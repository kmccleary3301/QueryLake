#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import multiprocessing as mp
import os
import re
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

os.environ.setdefault("VLLM_TARGET_DEVICE", "cuda")
try:
    mp.set_start_method("spawn", force=True)
except RuntimeError:
    pass

from QueryLake.files.object_store import LocalCASObjectStore
from QueryLake.files.service import FilesRuntimeService
from QueryLake.operation_classes.ray_chandra_class import ChandraDeployment, build_chandra_runtime_compatibility_snapshot
from scripts.chandra_quality_compare import _build_surface, _directory_sha256, _failure_fingerprint, _normalize_text
from scripts.chandra_benchmark_pdf import _resolve_runtime_class

PAGE_SPLIT_RE = re.compile(r"(?m)^## Page (\d+)\s*$")


class _DummyDB:
    def add(self, _row):
        return None

    def commit(self):
        return None


class _MethodProxy:
    def __init__(self, fn):
        self.remote = fn


class _LocalChandraHandle:
    def __init__(self, runtime: Any):
        self.transcribe = _MethodProxy(runtime.transcribe)
        self.transcribe_many = _MethodProxy(runtime.transcribe_many)


class _DummyUmbrella:
    def __init__(self, handle):
        self.chandra_handles = {"chandra": handle}


@dataclass
class _RunResult:
    full_text: str
    page_outputs: List[str]
    meta: Dict[str, Any]
    wall_seconds: float
    pages_dir: Path
    json_path: Path


def _split_pages(full_text: str, page_count: int) -> List[str]:
    text = (full_text or "").strip()
    if not text:
        return [""] * page_count
    matches = list(PAGE_SPLIT_RE.finditer(text))
    if not matches:
        return [text] + ([""] * max(0, page_count - 1))
    outputs = [""] * page_count
    for idx, match in enumerate(matches):
        page_num = int(match.group(1))
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if 1 <= page_num <= page_count:
            outputs[page_num - 1] = f"## Page {page_num}\n\n{body}".strip()
    return outputs


def _write_pages(outputs: List[str], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for idx, text in enumerate(outputs, start=1):
        (out_dir / f"page_{idx:04d}.md").write_text((text or "").strip() + "\n", encoding="utf-8")


def _compare_dirs(baseline_dir: Path, candidate_dir: Path) -> Dict[str, Any]:
    baseline_pages = {path.name: path.read_text(encoding="utf-8", errors="replace") for path in sorted(baseline_dir.glob("*.md"))}
    candidate_pages = {path.name: path.read_text(encoding="utf-8", errors="replace") for path in sorted(candidate_dir.glob("*.md"))}
    shared_pages = sorted(set(baseline_pages).intersection(candidate_pages))
    if not shared_pages:
        raise ValueError(f"No overlapping page files between {baseline_dir} and {candidate_dir}")
    raw_surface = _build_surface("raw", baseline_pages, candidate_pages, shared_pages)
    normalized_baseline = {}
    normalized_candidate = {}
    normalization_stats = {}
    for page in shared_pages:
        norm_base, base_stats = _normalize_text(baseline_pages[page])
        norm_cand, cand_stats = _normalize_text(candidate_pages[page])
        normalized_baseline[page] = norm_base
        normalized_candidate[page] = norm_cand
        normalization_stats[page] = {"baseline": base_stats.as_dict(), "candidate": cand_stats.as_dict()}
    normalized_surface = _build_surface("normalized", normalized_baseline, normalized_candidate, shared_pages)
    return {
        "baseline_dir": str(baseline_dir),
        "candidate_dir": str(candidate_dir),
        "shared_pages": len(shared_pages),
        "baseline_dir_sha256": _directory_sha256(baseline_dir),
        "candidate_dir_sha256": _directory_sha256(candidate_dir),
        "aggregate": raw_surface.aggregate,
        "recommendation": raw_surface.recommendation,
        "failure_fingerprint": _failure_fingerprint(raw_surface.results),
        "pages": [row.as_dict() for row in raw_surface.results],
        "normalized_aggregate": normalized_surface.aggregate,
        "normalized_recommendation": normalized_surface.recommendation,
        "normalized_failure_fingerprint": _failure_fingerprint(normalized_surface.results),
        "normalization": {"per_page_stats": normalization_stats},
    }


async def _run_single(
    *,
    data: bytes,
    bytes_cas: str,
    runtime: Any,
    profile: str,
    dpi: int,
    concurrency: int,
    out_root: Path,
    slug: str,
    run_name: str,
    text_layer_mode: str,
    min_chars_per_page: int,
    min_coverage: float,
) -> _RunResult:
    store = LocalCASObjectStore()
    service = FilesRuntimeService(_DummyDB(), object_store=store, umbrella=_DummyUmbrella(_LocalChandraHandle(runtime)))
    service._pdf_text_layer_mode = text_layer_mode
    service._pdf_text_min_chars_per_page = int(min_chars_per_page)
    service._pdf_text_min_coverage = float(min_coverage)

    page_overrides: Optional[Dict[int, str]] = None
    routing_meta: Optional[Dict[str, Any]] = None
    if text_layer_mode == "mixed":
        page_texts, parsed_meta = service._extract_pdf_text_layer_pages(data)
        if page_texts is not None:
            routing = service._evaluate_pdf_text_layer_page_overrides(page_texts)
            indices = list(routing.get("selected_page_indices", []))
            if indices:
                page_overrides = {int(idx): page_texts[int(idx)] for idx in indices}
            routing_meta = {
                **parsed_meta,
                "routing": {key: value for key, value in routing.items() if key != "selected_page_indices"},
                "selected_page_indices": indices,
            }

    start = asyncio.get_running_loop().time()
    if hasattr(service, "_process_pdf_with_chandra_pages"):
        page_outputs, meta = await service._process_pdf_with_chandra_pages(
            data,
            bytes_cas,
            profile=profile,
            dpi=dpi,
            concurrency=concurrency,
            page_text_overrides=page_overrides,
        )
        full_text = "\n\n".join(page_outputs)
    else:
        full_text, meta = await service._process_pdf_with_chandra(
            data,
            bytes_cas,
            profile=profile,
            dpi=dpi,
            concurrency=concurrency,
            page_text_overrides=page_overrides,
        )
        page_outputs = _split_pages(full_text, int(meta.get("pages", 1) or 1))
    wall_seconds = asyncio.get_running_loop().time() - start
    if routing_meta is not None:
        meta = {**meta, "text_layer_routing": routing_meta}
    pages_dir = out_root / f"{slug}_{run_name}_pages"
    _write_pages(page_outputs, pages_dir)
    result = {
        "pdf": slug,
        "run_name": run_name,
        "wall_seconds": round(wall_seconds, 4),
        "pages": int(meta.get("pages", 1) or 1),
        "pages_per_second": round((int(meta.get("pages", 1) or 1) / wall_seconds), 4) if wall_seconds > 0 else 0.0,
        "meta": meta,
    }
    json_path = out_root / f"{slug}_{run_name}.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return _RunResult(full_text=full_text, page_outputs=page_outputs, meta=meta, wall_seconds=wall_seconds, pages_dir=pages_dir, json_path=json_path)


async def _amain(args: argparse.Namespace) -> Dict[str, Any]:
    scan = json.loads(Path(args.scan_json).read_text(encoding="utf-8"))
    scan_rows = list(scan.get("all_results", []) or scan.get("rows", []) or [])
    top_rows = list(scan.get("top_candidates", []) or [])
    pdf_paths = [Path(row["pdf"]) for row in scan_rows]
    if args.only_top_candidates and top_rows:
        pdf_paths = [Path(row["pdf"]) for row in top_rows]
    if args.limit:
        pdf_paths = pdf_paths[: args.limit]

    out_root = Path(args.out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    runtime_class = _resolve_runtime_class()
    runtime = runtime_class(
        model_path=args.model,
        prompt=args.prompt,
        max_batch_size=args.max_batch_size,
        max_batch_wait_ms=args.max_batch_wait_ms,
        max_new_tokens=args.max_new_tokens,
        max_image_pixels=args.max_image_pixels,
        cache_enabled=not args.disable_cache,
        torch_dtype=args.torch_dtype,
        runtime_backend=args.runtime_backend,
        vllm_trust_remote_code=args.vllm_trust_remote_code,
        vllm_tensor_parallel_size=args.vllm_tensor_parallel_size,
        vllm_data_parallel_size=args.vllm_data_parallel_size,
        vllm_gpu_memory_utilization=args.vllm_gpu_memory_utilization,
        vllm_max_model_len=args.vllm_max_model_len,
        vllm_max_num_seqs=args.vllm_max_num_seqs,
        vllm_dtype=args.vllm_dtype,
        vllm_enforce_eager=args.vllm_enforce_eager,
        vllm_disable_log_stats=args.vllm_disable_log_stats,
        vllm_async_scheduling=args.vllm_async_scheduling,
        vllm_server_base_url=args.vllm_server_base_url,
        vllm_server_base_urls=args.vllm_server_base_urls,
        vllm_server_model=args.vllm_server_model,
        vllm_server_api_key=args.vllm_server_api_key,
        vllm_server_timeout_seconds=args.vllm_server_timeout_seconds,
        vllm_server_max_retries=args.vllm_server_max_retries,
        vllm_server_retry_backoff_seconds=args.vllm_server_retry_backoff_seconds,
        vllm_server_parallel_requests=args.vllm_server_parallel_requests,
        vllm_server_probe_on_init=args.vllm_server_probe_on_init,
        vllm_server_fallback_to_hf_on_error=args.vllm_server_fallback_to_hf_on_error,
        vllm_server_circuit_breaker_threshold=args.vllm_server_circuit_breaker_threshold,
        vllm_server_allowed_local_media_path=args.vllm_server_allowed_local_media_path,
    )
    runtime_snapshot = runtime.runtime_compatibility_snapshot() if hasattr(runtime, "runtime_compatibility_snapshot") else build_chandra_runtime_compatibility_snapshot(runtime)
    effective_backend = str(runtime_snapshot.get("effective_runtime_backend") or "").strip().lower()
    if args.require_effective_runtime_backend and effective_backend != args.require_effective_runtime_backend:
        raise RuntimeError(f"Expected effective backend {args.require_effective_runtime_backend}, got {effective_backend or 'unknown'}")

    rows: List[Dict[str, Any]] = []
    try:
        for pdf_path in pdf_paths:
            data = pdf_path.read_bytes()
            slug = pdf_path.stem.replace('.', '_')
            bytes_cas = hashlib_sha256_bytes(data)
            baseline = await _run_single(
                data=data,
                bytes_cas=bytes_cas,
                runtime=runtime,
                profile=args.profile,
                dpi=args.dpi,
                concurrency=args.concurrency,
                out_root=out_root,
                slug=slug,
                run_name="ocr_only",
                text_layer_mode="off",
                min_chars_per_page=args.text_layer_min_chars_per_page,
                min_coverage=args.text_layer_min_coverage,
            )
            mixed = await _run_single(
                data=data,
                bytes_cas=bytes_cas,
                runtime=runtime,
                profile=args.profile,
                dpi=args.dpi,
                concurrency=args.concurrency,
                out_root=out_root,
                slug=slug,
                run_name="mixed_textlayer",
                text_layer_mode="mixed",
                min_chars_per_page=args.text_layer_min_chars_per_page,
                min_coverage=args.text_layer_min_coverage,
            )
            quality = _compare_dirs(baseline.pages_dir, mixed.pages_dir)
            quality_path = out_root / f"{slug}_ocr_only_vs_mixed_quality.json"
            quality_path.write_text(json.dumps(quality, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            base_pages = int(baseline.meta.get("pages", 1) or 1)
            mixed_ocr_pages = int(mixed.meta.get("ocr_pages", 0) or 0)
            text_pages = int(mixed.meta.get("text_layer_pages", 0) or 0)
            rows.append({
                "pdf": str(pdf_path),
                "baseline_wall_seconds": round(baseline.wall_seconds, 4),
                "mixed_wall_seconds": round(mixed.wall_seconds, 4),
                "baseline_pages_per_second": round(base_pages / baseline.wall_seconds, 4) if baseline.wall_seconds > 0 else 0.0,
                "mixed_pages_per_second": round(base_pages / mixed.wall_seconds, 4) if mixed.wall_seconds > 0 else 0.0,
                "wall_seconds_delta_pct": round(((mixed.wall_seconds / baseline.wall_seconds) - 1.0) * 100.0, 3) if baseline.wall_seconds > 0 else 0.0,
                "pages_per_second_delta_pct": round((((base_pages / mixed.wall_seconds) / (base_pages / baseline.wall_seconds)) - 1.0) * 100.0, 3) if baseline.wall_seconds > 0 and mixed.wall_seconds > 0 else 0.0,
                "baseline_ocr_pages": int(baseline.meta.get("ocr_pages", 0) or 0),
                "mixed_ocr_pages": mixed_ocr_pages,
                "mixed_text_layer_pages": text_pages,
                "mixed_ocr_page_reduction": int((baseline.meta.get("ocr_pages", 0) or 0) - mixed_ocr_pages),
                "mixed_selected_coverage": round((text_pages / base_pages), 4) if base_pages > 0 else 0.0,
                "quality_recommendation": quality["recommendation"],
                "normalized_quality_recommendation": quality["normalized_recommendation"],
                "artifacts": {
                    "baseline_json": str(baseline.json_path),
                    "mixed_json": str(mixed.json_path),
                    "baseline_pages_dir": str(baseline.pages_dir),
                    "mixed_pages_dir": str(mixed.pages_dir),
                    "quality_compare_json": str(quality_path),
                },
            })
    finally:
        if getattr(runtime, "_batcher", None) is not None:
            await runtime._batcher.shutdown()

    pps_deltas = [row["pages_per_second_delta_pct"] for row in rows]
    wall_deltas = [row["wall_seconds_delta_pct"] for row in rows]
    selected_coverages = [row["mixed_selected_coverage"] for row in rows]
    summary = {
        "scan_json": args.scan_json,
        "out_root": str(out_root),
        "pdfs_evaluated": len(rows),
        "runtime": {
            "model": args.model,
            "profile": args.profile,
            "runtime_backend": args.runtime_backend,
            "effective_runtime_backend": effective_backend,
            "compatibility_snapshot": runtime_snapshot,
        },
        "text_layer_policy": {
            "mode": "mixed",
            "min_chars_per_page": args.text_layer_min_chars_per_page,
            "min_coverage": args.text_layer_min_coverage,
        },
        "aggregate": {
            "pages_per_second_delta_mean_pct": round(statistics.mean(pps_deltas), 3) if pps_deltas else 0.0,
            "pages_per_second_delta_median_pct": round(statistics.median(pps_deltas), 3) if pps_deltas else 0.0,
            "wall_seconds_delta_mean_pct": round(statistics.mean(wall_deltas), 3) if wall_deltas else 0.0,
            "wall_seconds_delta_median_pct": round(statistics.median(wall_deltas), 3) if wall_deltas else 0.0,
            "selected_coverage_mean": round(statistics.mean(selected_coverages), 4) if selected_coverages else 0.0,
            "docs_with_any_text_layer_pages": sum(1 for row in rows if row["mixed_text_layer_pages"] > 0),
            "docs_with_quality_pass": sum(1 for row in rows if row["quality_recommendation"]["verdict"] == "pass"),
            "docs_with_normalized_quality_pass": sum(1 for row in rows if row["normalized_quality_recommendation"]["verdict"] == "pass"),
        },
        "rows": rows,
    }
    return summary


def hashlib_sha256_bytes(data: bytes) -> str:
    import hashlib
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Chandra-1 OCR-only vs mixed text-layer routing.")
    parser.add_argument("--scan-json", required=True)
    parser.add_argument("--out-root", required=True)
    parser.add_argument("--only-top-candidates", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--model", required=True)
    parser.add_argument("--prompt", default="Convert this page into clean Markdown.")
    parser.add_argument("--dpi", type=int, default=144)
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument("--max-batch-size", type=int, default=24)
    parser.add_argument("--max-batch-wait-ms", type=int, default=15)
    parser.add_argument("--max-new-tokens", type=int, default=768)
    parser.add_argument("--max-image-pixels", type=int, default=2097152)
    parser.add_argument("--torch-dtype", default="auto")
    parser.add_argument("--runtime-backend", default="vllm", choices=["hf", "vllm", "vllm_server"])
    parser.add_argument("--require-effective-runtime-backend", default="vllm")
    parser.add_argument("--vllm-trust-remote-code", action="store_true")
    parser.add_argument("--vllm-tensor-parallel-size", type=int, default=1)
    parser.add_argument("--vllm-data-parallel-size", type=int, default=1)
    parser.add_argument("--vllm-gpu-memory-utilization", type=float, default=0.95)
    parser.add_argument("--vllm-max-model-len", type=int, default=131072)
    parser.add_argument("--vllm-max-num-seqs", type=int, default=8)
    parser.add_argument("--vllm-dtype", default="auto")
    parser.add_argument("--vllm-enforce-eager", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--vllm-disable-log-stats", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--vllm-async-scheduling", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--vllm-server-base-url", default="http://127.0.0.1:8022/v1")
    parser.add_argument(
        "--vllm-server-base-urls",
        default="",
        help="Optional comma-separated vLLM server /v1 base URLs for striped dispatch.",
    )
    parser.add_argument("--vllm-server-model", default=None)
    parser.add_argument("--vllm-server-api-key", default="")
    parser.add_argument("--vllm-server-timeout-seconds", type=float, default=120.0)
    parser.add_argument("--vllm-server-max-retries", type=int, default=2)
    parser.add_argument("--vllm-server-retry-backoff-seconds", type=float, default=0.5)
    parser.add_argument("--vllm-server-parallel-requests", type=int, default=24)
    parser.add_argument("--vllm-server-probe-on-init", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--vllm-server-fallback-to-hf-on-error", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--vllm-server-circuit-breaker-threshold", type=int, default=3)
    parser.add_argument(
        "--vllm-server-allowed-local-media-path",
        default=str((Path(__file__).resolve().parent.parent / "object_store")),
    )
    parser.add_argument("--profile", default="speed")
    parser.add_argument("--disable-cache", action="store_true", default=True)
    parser.add_argument("--text-layer-min-chars-per-page", type=int, default=120)
    parser.add_argument("--text-layer-min-coverage", type=float, default=0.8)
    parser.add_argument("--out-json", required=True)
    args = parser.parse_args()
    result = asyncio.run(_amain(args))
    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    out_path = Path(args.out_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

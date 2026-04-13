#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
from pathlib import Path
from typing import Any, Dict, List, Optional

os.environ.setdefault("VLLM_TARGET_DEVICE", "cuda")

from scripts.chandra_benchmark_pdf import (  # type: ignore
    BENCHMARK_SCHEMA_VERSION,
    REQUEST_SHAPE_VERSION,
    RUNTIME_SEMANTICS_VERSION,
    PassStats,
    _render_pdf_pages,
    _resolve_runtime_class,
    _run_document_shape_pass,
    _run_pass,
    _summarize_page_complexities,
)
from scripts.chandra_quality_compare import (  # type: ignore
    _build_surface,
    _directory_sha256,
    _failure_fingerprint,
    _normalize_text,
)
from QueryLake.operation_classes.ray_chandra_class import build_chandra_runtime_compatibility_snapshot


def _write_pages(outputs: List[str], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for idx, text in enumerate(outputs, start=1):
        (out_dir / f"page_{idx:04d}.md").write_text(text.strip() + "\n", encoding="utf-8")


def _compare_dirs(baseline_dir: Path, candidate_dir: Path) -> Dict[str, Any]:
    baseline_pages = {
        path.name: path.read_text(encoding="utf-8", errors="replace")
        for path in sorted(baseline_dir.glob("*.md"))
    }
    candidate_pages = {
        path.name: path.read_text(encoding="utf-8", errors="replace")
        for path in sorted(candidate_dir.glob("*.md"))
    }
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
        normalization_stats[page] = {
            "baseline": base_stats.as_dict(),
            "candidate": cand_stats.as_dict(),
        }
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
        "normalization": {
            "strategy": {
                "markdown_images": "replace with [IMAGE] placeholder",
                "html_images": "replace with [IMAGE] placeholder",
                "bullet_runs": "collapse repeated list markers to '- '",
                "blank_lines": "collapse 3+ blank lines to 2",
                "line_endings": "normalize to LF and trim trailing spaces",
            },
            "per_page_stats": normalization_stats,
        },
    }


def _benchmark_compare(baseline: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, Any]:
    base = baseline["passes"][0]
    cand = candidate["passes"][0]
    base_pps = float(base["pages_per_second"])
    cand_pps = float(cand["pages_per_second"])
    base_wall = float(base["wall_seconds"])
    cand_wall = float(cand["wall_seconds"])
    pps_delta_pct = ((cand_pps / base_pps) - 1.0) * 100.0 if base_pps else 0.0
    wall_delta_pct = ((cand_wall / base_wall) - 1.0) * 100.0 if base_wall else 0.0
    if pps_delta_pct >= 10.0 and wall_delta_pct <= -8.0:
        verdict = "improves"
    elif pps_delta_pct <= -5.0 or wall_delta_pct >= 5.0:
        verdict = "regress"
    else:
        verdict = "flat"
    return {
        "baseline": {
            "wall_seconds": round(base_wall, 4),
            "pages_per_second": round(base_pps, 4),
        },
        "candidate": {
            "wall_seconds": round(cand_wall, 4),
            "pages_per_second": round(cand_pps, 4),
        },
        "delta": {
            "pages_per_second_pct": round(pps_delta_pct, 3),
            "wall_seconds_pct": round(wall_delta_pct, 3),
        },
        "recommendation": {"verdict": verdict},
    }


async def _run_doc(
    runtime: Any,
    runtime_snapshot: Dict[str, Any],
    pdf_path: Path,
    args: argparse.Namespace,
    out_root: Path,
) -> Dict[str, Any]:
    render_start = asyncio.get_running_loop().time()
    images = _render_pdf_pages(str(pdf_path), dpi=args.dpi, max_pages=args.max_pages, render_cache_dir=args.render_cache_dir)
    render_seconds = asyncio.get_running_loop().time() - render_start
    page_complexity = _summarize_page_complexities(images)
    resolved_max_new_tokens = None if args.use_profile_defaults else args.max_new_tokens
    resolved_max_image_pixels = None if args.use_profile_defaults else args.max_image_pixels

    slug = pdf_path.stem.replace('.', '_')
    baseline_pages_dir = out_root / f"{slug}_baseline_pages"
    docshape_pages_dir = out_root / f"{slug}_docshape_pages"
    baseline_json = out_root / f"{slug}_baseline.json"
    docshape_json = out_root / f"{slug}_docshape.json"
    benchmark_compare_json = out_root / f"{slug}_baseline_vs_docshape_benchmark.json"
    quality_compare_json = out_root / f"{slug}_baseline_vs_docshape_quality.json"

    baseline_pass = await _run_pass(
        runtime=runtime,
        images=images,
        prompt=args.prompt,
        max_new_tokens=resolved_max_new_tokens,
        max_image_pixels=resolved_max_image_pixels,
        blocked_phrases=args.bad_word,
        concurrency=args.concurrency,
        name="cold",
        profile=args.profile,
        use_transcribe_many=args.transport_mode == "batch",
    )
    docshape_pass = await _run_document_shape_pass(
        runtime=runtime,
        images=images,
        page_complexity=page_complexity,
        prompt=args.prompt,
        max_new_tokens=resolved_max_new_tokens,
        default_max_image_pixels=resolved_max_image_pixels,
        lowered_max_image_pixels=args.document_shape_first_pass_max_image_pixels,
        blocked_phrases=args.bad_word,
        concurrency=args.concurrency,
        name="cold",
        near_white_threshold=args.sparse_near_white_threshold,
        ink_threshold=args.sparse_ink_threshold,
        edge_threshold=args.sparse_edge_threshold,
        variance_threshold=args.sparse_variance_threshold,
        min_sparse_ratio=args.document_shape_min_sparse_ratio,
        rerun_suspect_pages=bool(args.document_shape_rerun_suspect_pages),
        rerun_min_chars=args.document_shape_rerun_min_chars,
        profile=args.profile,
        use_transcribe_many=args.transport_mode == "batch",
    )

    _write_pages(baseline_pass.outputs, baseline_pages_dir)
    _write_pages(docshape_pass.outputs, docshape_pages_dir)

    base_result = {
        "pdf": str(pdf_path),
        "benchmark_schema_version": BENCHMARK_SCHEMA_VERSION,
        "runtime_semantics_version": RUNTIME_SEMANTICS_VERSION,
        "request_shape_version": REQUEST_SHAPE_VERSION,
        "render": {
            "dpi": args.dpi,
            "pages": len(images),
            "seconds": round(render_seconds, 4),
            "cache_dir": args.render_cache_dir,
            "page_complexity": page_complexity,
        },
        "runtime": {
            "model": args.model,
            "profile": args.profile,
            "runtime_backend": args.runtime_backend,
            "transport_mode": args.transport_mode,
            "max_new_tokens": resolved_max_new_tokens,
            "max_image_pixels": resolved_max_image_pixels,
            "concurrency": args.concurrency,
            "use_profile_defaults": bool(args.use_profile_defaults),
            "compatibility_snapshot": runtime_snapshot,
        },
        "passes": [baseline_pass.as_dict()],
    }
    cand_result = {
        "pdf": str(pdf_path),
        "benchmark_schema_version": BENCHMARK_SCHEMA_VERSION,
        "runtime_semantics_version": RUNTIME_SEMANTICS_VERSION,
        "request_shape_version": REQUEST_SHAPE_VERSION,
        "render": {
            "dpi": args.dpi,
            "pages": len(images),
            "seconds": round(render_seconds, 4),
            "cache_dir": args.render_cache_dir,
            "page_complexity": page_complexity,
        },
        "runtime": {
            "model": args.model,
            "profile": args.profile,
            "runtime_backend": args.runtime_backend,
            "transport_mode": args.transport_mode,
            "max_new_tokens": resolved_max_new_tokens,
            "max_image_pixels": resolved_max_image_pixels,
            "concurrency": args.concurrency,
            "use_profile_defaults": bool(args.use_profile_defaults),
            "document_shape_first_pass_max_image_pixels": args.document_shape_first_pass_max_image_pixels,
            "document_shape_min_sparse_ratio": args.document_shape_min_sparse_ratio,
            "document_shape_rerun_suspect_pages": bool(args.document_shape_rerun_suspect_pages),
            "document_shape_rerun_min_chars": args.document_shape_rerun_min_chars,
            "compatibility_snapshot": runtime_snapshot,
        },
        "passes": [docshape_pass.as_dict()],
    }
    baseline_json.write_text(json.dumps(base_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    docshape_json.write_text(json.dumps(cand_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    benchmark_compare = _benchmark_compare(base_result, cand_result)
    benchmark_compare_json.write_text(json.dumps(benchmark_compare, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    quality_compare = _compare_dirs(baseline_pages_dir, docshape_pages_dir)
    quality_compare_json.write_text(json.dumps(quality_compare, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return {
        "pdf": str(pdf_path),
        "sampled_pages": len(images),
        "page_complexity_counts": page_complexity.get("counts", {}),
        "sparse_ratio": round(float(docshape_pass.metadata.get("document_sparse_ratio", 0.0)), 6),
        "document_lowered_first_pass": bool(docshape_pass.metadata.get("document_lowered_first_pass", False)),
        "rerun_page_count": int(docshape_pass.metadata.get("rerun_page_count", 0)),
        "baseline": base_result["passes"][0],
        "candidate": cand_result["passes"][0],
        "benchmark_compare": benchmark_compare,
        "quality_recommendation": quality_compare["recommendation"],
        "normalized_quality_recommendation": quality_compare["normalized_recommendation"],
        "artifacts": {
            "baseline_json": str(baseline_json),
            "docshape_json": str(docshape_json),
            "baseline_pages_dir": str(baseline_pages_dir),
            "docshape_pages_dir": str(docshape_pages_dir),
            "benchmark_compare_json": str(benchmark_compare_json),
            "quality_compare_json": str(quality_compare_json),
        },
    }


async def _amain(args: argparse.Namespace) -> Dict[str, Any]:
    scan = json.loads(Path(args.scan_json).read_text(encoding="utf-8"))
    pdf_rows = scan.get("all_results", [])
    pdf_paths = [Path(row["pdf"] if "pdf" in row else row["pdf_path"]) for row in pdf_rows]
    if args.only_top_candidates:
        top = scan.get("top_candidates", [])
        pdf_paths = [Path(row["pdf"]) for row in top]
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
    )
    runtime_snapshot = runtime.runtime_compatibility_snapshot() if hasattr(runtime, "runtime_compatibility_snapshot") else build_chandra_runtime_compatibility_snapshot(runtime)
    effective_backend = str(runtime_snapshot.get("effective_runtime_backend") or "").strip().lower()
    required_backend = str(args.require_effective_runtime_backend or "").strip().lower()
    if required_backend and effective_backend != required_backend:
        raise RuntimeError(
            f"Corpus eval requires effective runtime backend '{required_backend}', got '{effective_backend or 'unknown'}'."
        )

    rows = []
    try:
        for pdf_path in pdf_paths:
            rows.append(await _run_doc(runtime, runtime_snapshot, pdf_path, args, out_root))
    finally:
        if getattr(runtime, "_batcher", None) is not None:
            await runtime._batcher.shutdown()

    pps_deltas = [row["benchmark_compare"]["delta"]["pages_per_second_pct"] for row in rows]
    wall_deltas = [row["benchmark_compare"]["delta"]["wall_seconds_pct"] for row in rows]
    changed_rows = [row for row in rows if row["document_lowered_first_pass"]]
    unchanged_rows = [row for row in rows if not row["document_lowered_first_pass"]]
    summary = {
        "scan_json": args.scan_json,
        "out_root": str(out_root),
        "pdfs_evaluated": len(rows),
        "runtime": {
            "model": args.model,
            "profile": args.profile,
            "runtime_backend": args.runtime_backend,
            "effective_runtime_backend": effective_backend,
            "transport_mode": args.transport_mode,
            "compatibility_snapshot": runtime_snapshot,
        },
        "document_shape_policy": {
            "lowered_max_image_pixels": args.document_shape_first_pass_max_image_pixels,
            "min_sparse_ratio": args.document_shape_min_sparse_ratio,
            "rerun_suspect_pages": bool(args.document_shape_rerun_suspect_pages),
            "rerun_min_chars": args.document_shape_rerun_min_chars,
            "sparse_thresholds": {
                "near_white_fraction_min": args.sparse_near_white_threshold,
                "ink_fraction_max": args.sparse_ink_threshold,
                "edge_density_max": args.sparse_edge_threshold,
                "variance_max": args.sparse_variance_threshold,
            },
        },
        "aggregate": {
            "pages_per_second_delta_mean_pct": round(statistics.mean(pps_deltas), 3) if pps_deltas else 0.0,
            "pages_per_second_delta_median_pct": round(statistics.median(pps_deltas), 3) if pps_deltas else 0.0,
            "wall_seconds_delta_mean_pct": round(statistics.mean(wall_deltas), 3) if wall_deltas else 0.0,
            "wall_seconds_delta_median_pct": round(statistics.median(wall_deltas), 3) if wall_deltas else 0.0,
            "docs_with_lowered_first_pass": len(changed_rows),
            "docs_without_lowered_first_pass": len(unchanged_rows),
            "docs_with_quality_pass": sum(1 for row in rows if row["quality_recommendation"]["verdict"] == "pass"),
            "docs_with_normalized_quality_pass": sum(1 for row in rows if row["normalized_quality_recommendation"]["verdict"] == "pass"),
            "policy_changed_pages_per_second_delta_mean_pct": round(
                statistics.mean(row["benchmark_compare"]["delta"]["pages_per_second_pct"] for row in changed_rows),
                3,
            )
            if changed_rows
            else 0.0,
            "policy_changed_wall_seconds_delta_mean_pct": round(
                statistics.mean(row["benchmark_compare"]["delta"]["wall_seconds_pct"] for row in changed_rows),
                3,
            )
            if changed_rows
            else 0.0,
            "no_policy_change_pages_per_second_delta_mean_pct": round(
                statistics.mean(row["benchmark_compare"]["delta"]["pages_per_second_pct"] for row in unchanged_rows),
                3,
            )
            if unchanged_rows
            else 0.0,
            "no_policy_change_wall_seconds_delta_mean_pct": round(
                statistics.mean(row["benchmark_compare"]["delta"]["wall_seconds_pct"] for row in unchanged_rows),
                3,
            )
            if unchanged_rows
            else 0.0,
        },
        "rows": rows,
    }
    return summary


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Chandra-1 baseline vs document-shape corpus evaluation.")
    parser.add_argument("--scan-json", required=True)
    parser.add_argument("--out-root", required=True)
    parser.add_argument("--only-top-candidates", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--pdf", dest="pdf", default="")
    parser.add_argument("--model", required=True)
    parser.add_argument("--prompt", default="Convert this page into clean Markdown.")
    parser.add_argument("--dpi", type=int, default=144)
    parser.add_argument("--render-cache-dir", default=None)
    parser.add_argument("--max-pages", type=int, default=5)
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
    parser.add_argument("--vllm-server-base-urls", default="")
    parser.add_argument("--vllm-server-model", default=None)
    parser.add_argument("--vllm-server-api-key", default="")
    parser.add_argument("--vllm-server-timeout-seconds", type=float, default=120.0)
    parser.add_argument("--vllm-server-max-retries", type=int, default=2)
    parser.add_argument("--vllm-server-retry-backoff-seconds", type=float, default=0.5)
    parser.add_argument("--vllm-server-parallel-requests", type=int, default=24)
    parser.add_argument("--vllm-server-probe-on-init", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--vllm-server-fallback-to-hf-on-error", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--vllm-server-circuit-breaker-threshold", type=int, default=3)
    parser.add_argument("--profile", default="speed")
    parser.add_argument("--disable-cache", action="store_true")
    parser.add_argument("--use-profile-defaults", action="store_true", default=True)
    parser.add_argument("--transport-mode", default="page", choices=["page", "batch"])
    parser.add_argument("--document-shape-first-pass-max-image-pixels", type=int, default=393216)
    parser.add_argument("--document-shape-min-sparse-ratio", type=float, default=0.5)
    parser.add_argument("--document-shape-rerun-suspect-pages", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--document-shape-rerun-min-chars", type=int, default=450)
    parser.add_argument("--sparse-near-white-threshold", type=float, default=0.74)
    parser.add_argument("--sparse-ink-threshold", type=float, default=0.02)
    parser.add_argument("--sparse-edge-threshold", type=float, default=0.03)
    parser.add_argument("--sparse-variance-threshold", type=float, default=120.0)
    parser.add_argument("--bad-word", action="append", default=[])
    parser.add_argument("--out-json", required=True)
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    result = asyncio.run(_amain(args))
    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    out_path = Path(args.out_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

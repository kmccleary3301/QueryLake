#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import statistics
import tempfile
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pypdfium2 as pdfium
from PIL import Image

os.environ.setdefault("VLLM_TARGET_DEVICE", "cuda")

from QueryLake.operation_classes.ray_chandra_class import (
    ChandraDeployment,
    analyze_ocr_page_complexity,
    build_chandra_runtime_compatibility_snapshot,
)

BENCHMARK_SCHEMA_VERSION = 1
RUNTIME_SEMANTICS_VERSION = "chandra_runtime_v1"
REQUEST_SHAPE_VERSION = "page_request_v1"
REQUEST_SHAPE_BATCH_VERSION = "batch_request_v1"


@dataclass
class PassStats:
    name: str
    wall_seconds: float
    page_latencies: List[float]
    total_chars: int
    outputs: List[str]
    metadata: Optional[dict] = None

    def as_dict(self) -> dict:
        latencies_ms = [value * 1000.0 for value in self.page_latencies]
        pages = len(self.page_latencies)
        result = {
            "name": self.name,
            "pages": pages,
            "wall_seconds": round(self.wall_seconds, 4),
            "pages_per_second": round((pages / self.wall_seconds), 4) if self.wall_seconds > 0 else 0.0,
            "total_chars": self.total_chars,
            "latency_ms": {
                "mean": round(statistics.mean(latencies_ms), 2) if latencies_ms else 0.0,
                "median": round(statistics.median(latencies_ms), 2) if latencies_ms else 0.0,
                "p95": round(_percentile(latencies_ms, 95.0), 2) if latencies_ms else 0.0,
                "max": round(max(latencies_ms), 2) if latencies_ms else 0.0,
            },
        }
        if self.metadata:
            result["metadata"] = self.metadata
        return result


def _percentile(values: List[float], pct: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    idx = int((len(sorted_values) - 1) * (pct / 100.0))
    return sorted_values[max(0, min(idx, len(sorted_values) - 1))]


def _resolve_pdf_path(pdf_path: str) -> Tuple[str, Optional[str]]:
    if pdf_path.startswith("http://") or pdf_path.startswith("https://"):
        fd, tmp_path = tempfile.mkstemp(prefix="chandra_bench_", suffix=".pdf")
        os.close(fd)
        urllib.request.urlretrieve(pdf_path, tmp_path)
        return tmp_path, tmp_path
    return pdf_path, None


def _hash_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _render_pdf_pages(
    pdf_path: str,
    dpi: int,
    max_pages: Optional[int],
    render_cache_dir: Optional[str] = None,
) -> List[Any]:
    document = pdfium.PdfDocument(pdf_path)
    scale = float(dpi) / 72.0
    page_count = len(document)
    if max_pages is not None:
        page_count = min(page_count, max_pages)

    cache_run_dir: Optional[Path] = None
    if render_cache_dir:
        cache_root = Path(render_cache_dir)
        cache_key = f"{_hash_file(pdf_path)}_dpi{dpi}_pages{page_count}"
        cache_run_dir = cache_root / cache_key
        cache_run_dir.mkdir(parents=True, exist_ok=True)

    pages: List[Any] = []
    for index in range(page_count):
        cache_file = cache_run_dir / f"page_{index+1:04d}.png" if cache_run_dir else None
        if cache_file and cache_file.exists():
            pil_image = Image.open(cache_file).convert("RGB")
            pages.append(pil_image)
            continue

        page = document[index]
        pil_image = page.render(scale=scale).to_pil().convert("RGB")
        pages.append(pil_image)
        if cache_file:
            pil_image.save(cache_file, format="PNG")
        page.close()
    document.close()
    return pages


def _summarize_page_complexities(images: List[Any]) -> Dict[str, Any]:
    details: List[Dict[str, Any]] = []
    counts: Dict[str, int] = {"simple": 0, "mixed": 0, "complex": 0, "unavailable": 0}
    unavailable = 0
    for image in images:
        try:
            item = analyze_ocr_page_complexity(image)
        except Exception:
            item = {
                "class": "unavailable",
                "ink_fraction": None,
                "edge_density": None,
                "variance": None,
                "pixels": None,
            }
            unavailable += 1
        details.append(item)
    for item in details:
        counts[item["class"]] = counts.get(item["class"], 0) + 1
    if not details:
        return {"counts": counts, "pages": [], "unavailable_pages": 0}
    numeric_details = [item for item in details if item["class"] != "unavailable"]
    return {
        "counts": counts,
        "unavailable_pages": unavailable,
        "pages": [
            {
                "page_index": idx + 1,
                "class": item["class"],
                "near_white_fraction": item.get("near_white_fraction"),
                "ink_fraction": item["ink_fraction"],
                "edge_density": item["edge_density"],
                "variance": item["variance"],
                "pixels": item["pixels"],
            }
            for idx, item in enumerate(details)
        ],
        "mean_ink_fraction": round(statistics.mean(item["ink_fraction"] for item in numeric_details), 6) if numeric_details else None,
        "mean_edge_density": round(statistics.mean(item["edge_density"] for item in numeric_details), 6) if numeric_details else None,
        "mean_variance": round(statistics.mean(item["variance"] for item in numeric_details), 2) if numeric_details else None,
    }


def _normalize_triage_classes(raw_value: Optional[str]) -> List[str]:
    if not raw_value:
        return ["simple"]
    allowed = {"simple", "mixed", "complex"}
    classes = [item.strip().lower() for item in raw_value.split(",") if item.strip()]
    invalid = [item for item in classes if item not in allowed]
    if invalid:
        raise ValueError(f"Unsupported triage page classes: {', '.join(sorted(set(invalid)))}")
    deduped: List[str] = []
    for item in classes:
        if item not in deduped:
            deduped.append(item)
    return deduped or ["simple"]


def _identify_sparse_feature_indices(
    page_complexity: Dict[str, Any],
    *,
    near_white_threshold: float,
    ink_threshold: float,
    edge_threshold: float,
    variance_threshold: float,
) -> List[int]:
    sparse_indices: List[int] = []
    for item in page_complexity.get("pages", []):
        near_white = item.get("near_white_fraction")
        ink = item.get("ink_fraction")
        edge = item.get("edge_density")
        variance = item.get("variance")
        if None in (near_white, ink, edge, variance):
            continue
        if (
            float(near_white) >= float(near_white_threshold)
            and float(ink) <= float(ink_threshold)
            and float(edge) <= float(edge_threshold)
            and float(variance) <= float(variance_threshold)
        ):
            sparse_indices.append(int(item["page_index"]) - 1)
    return sparse_indices


def _resolve_tapered_page_max_image_pixels(
    page_complexity: Dict[str, Any],
    *,
    default_max_image_pixels: int,
    min_max_image_pixels: int,
    medium_max_image_pixels: Optional[int] = None,
    near_white_weight: float = 0.45,
    ink_weight: float = 0.25,
    edge_weight: float = 0.20,
    variance_weight: float = 0.10,
) -> Dict[int, int]:
    min_pixels = max(1, int(min_max_image_pixels))
    default_pixels = max(min_pixels, int(default_max_image_pixels))
    medium_pixels = (
        max(min_pixels, min(default_pixels, int(medium_max_image_pixels)))
        if medium_max_image_pixels is not None
        else None
    )
    total_weight = max(0.0001, near_white_weight + ink_weight + edge_weight + variance_weight)
    routed: Dict[int, int] = {}

    for item in page_complexity.get("pages", []):
        near_white = item.get("near_white_fraction")
        ink = item.get("ink_fraction")
        edge = item.get("edge_density")
        variance = item.get("variance")
        page_index = int(item.get("page_index", 0)) - 1
        if page_index < 0 or None in (near_white, ink, edge, variance):
            continue
        sparse_score = (
            near_white_weight * min(1.0, max(0.0, (float(near_white) - 0.68) / 0.22))
            + ink_weight * min(1.0, max(0.0, (0.08 - float(ink)) / 0.08))
            + edge_weight * min(1.0, max(0.0, (0.10 - float(edge)) / 0.10))
            + variance_weight * min(1.0, max(0.0, (300.0 - float(variance)) / 300.0))
        ) / total_weight
        sparse_score = max(0.0, min(1.0, sparse_score))
        tapered_pixels = int(round(default_pixels - sparse_score * (default_pixels - min_pixels)))

        if medium_pixels is not None:
            if sparse_score >= 0.68:
                resolved_pixels = min_pixels
            elif sparse_score >= 0.30:
                resolved_pixels = medium_pixels
            else:
                resolved_pixels = default_pixels
        else:
            resolved_pixels = max(min_pixels, min(default_pixels, tapered_pixels))
        routed[page_index] = int(resolved_pixels)

    return routed


def _resolve_runtime_class():
    runtime_class = getattr(ChandraDeployment, "func_or_class", None)
    return runtime_class or ChandraDeployment


async def _run_pass(
    runtime: Any,
    images: List[Any],
    prompt: str,
    max_new_tokens: Optional[int],
    max_image_pixels: Optional[int],
    blocked_phrases: Optional[List[str]],
    concurrency: int,
    name: str,
    profile: Optional[str] = None,
    use_transcribe_many: bool = False,
) -> PassStats:
    wall_start = time.perf_counter()
    if use_transcribe_many and len(images) > 1 and hasattr(runtime, "transcribe_many"):
        outputs = await runtime.transcribe_many(
            images=images,
            prompt=prompt,
            max_new_tokens=max_new_tokens,
            max_image_pixels=max_image_pixels,
            blocked_phrases=blocked_phrases,
            profile=profile,
        )
        if len(outputs) != len(images):
            raise RuntimeError(f"Batch transport output length mismatch ({len(outputs)} != {len(images)}).")
        wall_seconds = time.perf_counter() - wall_start
        page_latencies = [wall_seconds] * len(images)
        metadata = {
            "transport_mode": "batch",
            "latency_semantics": "collective_wall_for_entire_batch",
        }
    else:
        semaphore = asyncio.Semaphore(max(1, int(concurrency)))
        page_latencies = [0.0] * len(images)
        outputs: List[str] = [""] * len(images)
        metadata = None

        async def _worker(page_idx: int, image_obj: Any) -> None:
            start = time.perf_counter()
            async with semaphore:
                output = await runtime.transcribe(
                    image=image_obj,
                    prompt=prompt,
                    max_new_tokens=max_new_tokens,
                    max_image_pixels=max_image_pixels,
                    blocked_phrases=blocked_phrases,
                    profile=profile,
                )
            page_latencies[page_idx] = time.perf_counter() - start
            outputs[page_idx] = output

        await asyncio.gather(*[_worker(page_idx, image) for page_idx, image in enumerate(images)])
    wall_seconds = time.perf_counter() - wall_start
    return PassStats(
        name=name,
        wall_seconds=wall_seconds,
        page_latencies=page_latencies,
        total_chars=sum(len(text) for text in outputs),
        outputs=outputs,
        metadata=metadata,
    )


async def _run_triaged_pass(
    runtime: Any,
    images: List[Any],
    page_complexity: Dict[str, Any],
    prompt: str,
    max_new_tokens: Optional[int],
    default_max_image_pixels: Optional[int],
    lowered_max_image_pixels: int,
    blocked_phrases: Optional[List[str]],
    concurrency: int,
    name: str,
    profile: Optional[str] = None,
    use_transcribe_many: bool = False,
    lowered_page_classes: Optional[List[str]] = None,
) -> PassStats:
    page_latencies: List[float] = [0.0] * len(images)
    outputs: List[str] = [""] * len(images)
    total_wall = 0.0
    bucket_counts = {"lowered": 0, "default": 0}
    lowered_page_classes = lowered_page_classes or ["simple"]

    lowered_indices = [
        int(item["page_index"]) - 1
        for item in page_complexity.get("pages", [])
        if item.get("class") in set(lowered_page_classes)
    ]
    lowered_index_set = set(lowered_indices)
    default_indices = [idx for idx in range(len(images)) if idx not in lowered_index_set]

    async def _run_bucket(indices: List[int], resolved_pixels: Optional[int], bucket_name: str) -> None:
        nonlocal total_wall
        if not indices:
            return
        bucket_counts[bucket_name] += len(indices)
        wall_seconds, latencies, bucket_outputs = await _run_subset_pass(
            runtime=runtime,
            images=images,
            indices=indices,
            prompt=prompt,
            max_new_tokens=max_new_tokens,
            max_image_pixels=resolved_pixels,
            blocked_phrases=blocked_phrases,
            concurrency=concurrency,
            profile=profile,
            use_transcribe_many=use_transcribe_many,
        )
        total_wall += wall_seconds
        for idx in indices:
            page_latencies[idx] = latencies[idx]
            outputs[idx] = bucket_outputs[idx]

    if use_transcribe_many and hasattr(runtime, "transcribe_many"):
        await _run_bucket(default_indices, default_max_image_pixels, "default")
        await _run_bucket(lowered_indices, lowered_max_image_pixels, "lowered")
        latency_semantics = "summed_wall_across_triage_buckets"
        transport_mode = "batch"
    else:
        semaphore = asyncio.Semaphore(max(1, int(concurrency)))
        latency_semantics = "per_page_concurrent_requests_with_per_page_cap"
        transport_mode = "page"
        bucket_counts["default"] = len(default_indices)
        bucket_counts["lowered"] = len(lowered_indices)

        async def _worker(page_idx: int, resolved_pixels: Optional[int]) -> None:
            start = time.perf_counter()
            async with semaphore:
                output = await runtime.transcribe(
                    image=images[page_idx],
                    prompt=prompt,
                    max_new_tokens=max_new_tokens,
                    max_image_pixels=resolved_pixels,
                    blocked_phrases=blocked_phrases,
                    profile=profile,
                )
            page_latencies[page_idx] = time.perf_counter() - start
            outputs[page_idx] = output

        wall_start = time.perf_counter()
        tasks = [
            _worker(idx, default_max_image_pixels) for idx in default_indices
        ] + [
            _worker(idx, lowered_max_image_pixels) for idx in lowered_indices
        ]
        await asyncio.gather(*tasks)
        total_wall = time.perf_counter() - wall_start

    metadata = {
        "transport_mode": transport_mode,
        "latency_semantics": latency_semantics,
        "triage_mode": "page_class_lower_cap_v2",
        "lowered_page_classes": list(lowered_page_classes),
        "lowered_page_max_image_pixels": int(lowered_max_image_pixels),
        "default_max_image_pixels": int(default_max_image_pixels) if default_max_image_pixels else None,
        "lowered_page_count": len(lowered_indices),
        "bucket_counts": bucket_counts,
    }
    return PassStats(
        name=name,
        wall_seconds=total_wall,
        page_latencies=page_latencies,
        total_chars=sum(len(text) for text in outputs),
        outputs=outputs,
        metadata=metadata,
    )


async def _run_tapered_feature_pass(
    runtime: Any,
    images: List[Any],
    page_complexity: Dict[str, Any],
    prompt: str,
    max_new_tokens: Optional[int],
    default_max_image_pixels: int,
    min_max_image_pixels: int,
    blocked_phrases: Optional[List[str]],
    concurrency: int,
    name: str,
    *,
    medium_max_image_pixels: Optional[int] = None,
    near_white_weight: float = 0.45,
    ink_weight: float = 0.25,
    edge_weight: float = 0.20,
    variance_weight: float = 0.10,
    profile: Optional[str] = None,
) -> PassStats:
    per_page_pixels = _resolve_tapered_page_max_image_pixels(
        page_complexity,
        default_max_image_pixels=default_max_image_pixels,
        min_max_image_pixels=min_max_image_pixels,
        medium_max_image_pixels=medium_max_image_pixels,
        near_white_weight=near_white_weight,
        ink_weight=ink_weight,
        edge_weight=edge_weight,
        variance_weight=variance_weight,
    )
    page_latencies: List[float] = [0.0] * len(images)
    outputs: List[str] = [""] * len(images)
    semaphore = asyncio.Semaphore(max(1, int(concurrency)))

    async def _worker(page_idx: int, resolved_pixels: int) -> None:
        start = time.perf_counter()
        async with semaphore:
            output = await runtime.transcribe(
                image=images[page_idx],
                prompt=prompt,
                max_new_tokens=max_new_tokens,
                max_image_pixels=resolved_pixels,
                blocked_phrases=blocked_phrases,
                profile=profile,
            )
        page_latencies[page_idx] = time.perf_counter() - start
        outputs[page_idx] = output

    wall_start = time.perf_counter()
    await asyncio.gather(
        *[_worker(idx, per_page_pixels.get(idx, default_max_image_pixels)) for idx in range(len(images))]
    )
    total_wall = time.perf_counter() - wall_start

    bucket_counts: Dict[str, int] = {}
    for idx in range(len(images)):
        resolved = int(per_page_pixels.get(idx, default_max_image_pixels))
        bucket_counts[str(resolved)] = bucket_counts.get(str(resolved), 0) + 1

    metadata = {
        "transport_mode": "page",
        "latency_semantics": "per_page_concurrent_requests_with_per_page_cap",
        "triage_mode": "feature_tapered_cap_v1",
        "default_max_image_pixels": int(default_max_image_pixels),
        "min_max_image_pixels": int(min_max_image_pixels),
        "medium_max_image_pixels": int(medium_max_image_pixels) if medium_max_image_pixels is not None else None,
        "bucket_counts": bucket_counts,
        "resolved_page_max_image_pixels": {
            str(idx + 1): int(per_page_pixels.get(idx, default_max_image_pixels)) for idx in range(len(images))
        },
        "feature_weights": {
            "near_white": float(near_white_weight),
            "ink": float(ink_weight),
            "edge": float(edge_weight),
            "variance": float(variance_weight),
        },
    }
    return PassStats(
        name=name,
        wall_seconds=total_wall,
        page_latencies=page_latencies,
        total_chars=sum(len(text) for text in outputs),
        outputs=outputs,
        metadata=metadata,
    )


async def _run_sparse_feature_pass(
    runtime: Any,
    images: List[Any],
    page_complexity: Dict[str, Any],
    prompt: str,
    max_new_tokens: Optional[int],
    default_max_image_pixels: Optional[int],
    lowered_max_image_pixels: int,
    blocked_phrases: Optional[List[str]],
    concurrency: int,
    name: str,
    *,
    near_white_threshold: float,
    ink_threshold: float,
    edge_threshold: float,
    variance_threshold: float,
    rerun_suspect_pages: bool = False,
    rerun_min_chars: int = 450,
    profile: Optional[str] = None,
    use_transcribe_many: bool = False,
) -> PassStats:
    sparse_indices = _identify_sparse_feature_indices(
        page_complexity,
        near_white_threshold=near_white_threshold,
        ink_threshold=ink_threshold,
        edge_threshold=edge_threshold,
        variance_threshold=variance_threshold,
    )
    sparse_index_set = set(sparse_indices)
    synthetic_page_complexity = {
        "pages": [
            {
                "page_index": idx + 1,
                "class": "lowered" if idx in sparse_index_set else "default",
            }
            for idx in range(len(images))
        ]
    }
    first_pass = await _run_triaged_pass(
        runtime=runtime,
        images=images,
        page_complexity=synthetic_page_complexity,
        prompt=prompt,
        max_new_tokens=max_new_tokens,
        default_max_image_pixels=default_max_image_pixels,
        lowered_max_image_pixels=lowered_max_image_pixels,
        blocked_phrases=blocked_phrases,
        concurrency=concurrency,
        name=name,
        profile=profile,
        use_transcribe_many=use_transcribe_many,
        lowered_page_classes=["lowered"],
    )

    rerun_indices: List[int] = []
    if rerun_suspect_pages:
        rerun_indices = [
            idx for idx in sparse_indices if _needs_escalation(first_pass.outputs[idx], rerun_min_chars)
        ]

    if rerun_indices:
        rerun_wall, rerun_latencies, rerun_outputs = await _run_subset_pass(
            runtime=runtime,
            images=images,
            indices=rerun_indices,
            prompt=prompt,
            max_new_tokens=max_new_tokens,
            max_image_pixels=default_max_image_pixels,
            blocked_phrases=blocked_phrases,
            concurrency=concurrency,
            profile=profile,
            use_transcribe_many=use_transcribe_many,
        )
        for idx in rerun_indices:
            first_pass.page_latencies[idx] += rerun_latencies[idx]
            first_pass.outputs[idx] = rerun_outputs[idx]
        first_pass.wall_seconds += rerun_wall
        first_pass.total_chars = sum(len(text) for text in first_pass.outputs)

    metadata = dict(first_pass.metadata or {})
    metadata.update(
        {
            "triage_mode": "sparse_feature_lower_cap_v1",
            "sparse_page_count": len(sparse_indices),
            "sparse_page_indices": [idx + 1 for idx in sparse_indices],
            "sparse_feature_thresholds": {
                "near_white_fraction_min": float(near_white_threshold),
                "ink_fraction_max": float(ink_threshold),
                "edge_density_max": float(edge_threshold),
                "variance_max": float(variance_threshold),
            },
            "rerun_suspect_pages": bool(rerun_suspect_pages),
            "rerun_min_chars": int(rerun_min_chars),
            "rerun_page_count": len(rerun_indices),
            "rerun_page_indices": [idx + 1 for idx in rerun_indices],
        }
    )
    first_pass.metadata = metadata
    return first_pass


async def _run_document_shape_pass(
    runtime: Any,
    images: List[Any],
    page_complexity: Dict[str, Any],
    prompt: str,
    max_new_tokens: Optional[int],
    default_max_image_pixels: Optional[int],
    lowered_max_image_pixels: int,
    blocked_phrases: Optional[List[str]],
    concurrency: int,
    name: str,
    *,
    near_white_threshold: float,
    ink_threshold: float,
    edge_threshold: float,
    variance_threshold: float,
    min_sparse_ratio: float = 0.5,
    rerun_suspect_pages: bool = False,
    rerun_min_chars: int = 450,
    profile: Optional[str] = None,
    use_transcribe_many: bool = False,
) -> PassStats:
    sparse_indices = _identify_sparse_feature_indices(
        page_complexity,
        near_white_threshold=near_white_threshold,
        ink_threshold=ink_threshold,
        edge_threshold=edge_threshold,
        variance_threshold=variance_threshold,
    )
    sparse_ratio = float(len(sparse_indices)) / float(len(images) or 1)
    use_lowered_first_pass = sparse_ratio >= float(min_sparse_ratio)
    first_pass_pixels = lowered_max_image_pixels if use_lowered_first_pass else default_max_image_pixels

    first_pass = await _run_pass(
        runtime=runtime,
        images=images,
        prompt=prompt,
        max_new_tokens=max_new_tokens,
        max_image_pixels=first_pass_pixels,
        blocked_phrases=blocked_phrases,
        concurrency=concurrency,
        name=name,
        profile=profile,
        use_transcribe_many=use_transcribe_many,
    )

    rerun_indices: List[int] = []
    if use_lowered_first_pass and rerun_suspect_pages:
        rerun_indices = [idx for idx, output in enumerate(first_pass.outputs) if _needs_escalation(output, rerun_min_chars)]

    if rerun_indices:
        rerun_wall, rerun_latencies, rerun_outputs = await _run_subset_pass(
            runtime=runtime,
            images=images,
            indices=rerun_indices,
            prompt=prompt,
            max_new_tokens=max_new_tokens,
            max_image_pixels=default_max_image_pixels,
            blocked_phrases=blocked_phrases,
            concurrency=concurrency,
            profile=profile,
            use_transcribe_many=use_transcribe_many,
        )
        for idx in rerun_indices:
            first_pass.page_latencies[idx] += rerun_latencies[idx]
            first_pass.outputs[idx] = rerun_outputs[idx]
        first_pass.wall_seconds += rerun_wall
        first_pass.total_chars = sum(len(text) for text in first_pass.outputs)

    metadata = dict(first_pass.metadata or {})
    metadata.update(
        {
            "triage_mode": "document_shape_lower_cap_v1",
            "sparse_page_count": len(sparse_indices),
            "sparse_page_indices": [idx + 1 for idx in sparse_indices],
            "sparse_feature_thresholds": {
                "near_white_fraction_min": float(near_white_threshold),
                "ink_fraction_max": float(ink_threshold),
                "edge_density_max": float(edge_threshold),
                "variance_max": float(variance_threshold),
            },
            "document_sparse_ratio": sparse_ratio,
            "document_sparse_ratio_threshold": float(min_sparse_ratio),
            "document_lowered_first_pass": bool(use_lowered_first_pass),
            "lowered_first_pass_max_image_pixels": int(lowered_max_image_pixels),
            "default_max_image_pixels": int(default_max_image_pixels) if default_max_image_pixels else None,
            "rerun_suspect_pages": bool(rerun_suspect_pages),
            "rerun_min_chars": int(rerun_min_chars),
            "rerun_page_count": len(rerun_indices),
            "rerun_page_indices": [idx + 1 for idx in rerun_indices],
        }
    )
    first_pass.metadata = metadata
    return first_pass


async def _run_subset_pass(
    runtime: Any,
    images: List[Any],
    indices: List[int],
    prompt: str,
    max_new_tokens: Optional[int],
    max_image_pixels: Optional[int],
    blocked_phrases: Optional[List[str]],
    concurrency: int,
    profile: Optional[str] = None,
    use_transcribe_many: bool = False,
) -> Tuple[float, Dict[int, float], Dict[int, str]]:
    page_latencies: Dict[int, float] = {}
    page_outputs: Dict[int, str] = {}

    if use_transcribe_many and len(indices) > 1 and hasattr(runtime, "transcribe_many"):
        batch_images = [images[page_idx] for page_idx in indices]
        wall_start = time.perf_counter()
        outputs = await runtime.transcribe_many(
            images=batch_images,
            prompt=prompt,
            max_new_tokens=max_new_tokens,
            max_image_pixels=max_image_pixels,
            blocked_phrases=blocked_phrases,
            profile=profile,
        )
        wall_seconds = time.perf_counter() - wall_start
        if len(outputs) != len(indices):
            raise RuntimeError(f"Batch transport output length mismatch ({len(outputs)} != {len(indices)}).")
        for page_idx, output in zip(indices, outputs):
            page_latencies[page_idx] = wall_seconds
            page_outputs[page_idx] = output
        return wall_seconds, page_latencies, page_outputs

    semaphore = asyncio.Semaphore(max(1, int(concurrency)))

    async def _worker(page_idx: int) -> None:
        start = time.perf_counter()
        async with semaphore:
            output = await runtime.transcribe(
                image=images[page_idx],
                prompt=prompt,
                max_new_tokens=max_new_tokens,
                max_image_pixels=max_image_pixels,
                blocked_phrases=blocked_phrases,
                profile=profile,
            )
        page_latencies[page_idx] = time.perf_counter() - start
        page_outputs[page_idx] = output

    wall_start = time.perf_counter()
    await asyncio.gather(*[_worker(page_idx) for page_idx in indices])
    wall_seconds = time.perf_counter() - wall_start
    return wall_seconds, page_latencies, page_outputs


def _needs_escalation(text: str, min_chars: int) -> bool:
    stripped = text.strip()
    if len(stripped) < max(1, int(min_chars)):
        return True
    if stripped.count("```") % 2 == 1:
        return True
    if stripped.count("<table") > stripped.count("</table>"):
        return True
    if stripped.count("<div") > stripped.count("</div>"):
        return True
    if stripped.count("\\begin{") > stripped.count("\\end{"):
        return True
    suspect_tail = ("<table", "<tr", "<td", "<th", "<div", "<span", "\\begin{", "| --- |")
    if any(stripped.endswith(suffix) for suffix in suspect_tail):
        return True
    return False


async def _run_adaptive_pass(
    runtime: Any,
    images: List[Any],
    prompt: str,
    concurrency: int,
    low_tokens: int,
    high_tokens: int,
    low_pixels: Optional[int],
    high_pixels: Optional[int],
    blocked_phrases: Optional[List[str]],
    min_chars: int,
    name: str,
    profile: Optional[str] = None,
    use_transcribe_many: bool = False,
) -> PassStats:
    low_pass = await _run_pass(
        runtime=runtime,
        images=images,
        prompt=prompt,
        max_new_tokens=low_tokens,
        max_image_pixels=low_pixels,
        blocked_phrases=blocked_phrases,
        concurrency=concurrency,
        name=f"{name}_low",
        profile=profile,
        use_transcribe_many=use_transcribe_many,
    )
    flagged = [idx for idx, output in enumerate(low_pass.outputs) if _needs_escalation(output, min_chars=min_chars)]
    merged_outputs = list(low_pass.outputs)
    merged_latencies = list(low_pass.page_latencies)
    total_wall = low_pass.wall_seconds
    rerun_wall = 0.0

    if flagged:
        rerun_wall, rerun_latencies, rerun_outputs = await _run_subset_pass(
            runtime=runtime,
            images=images,
            indices=flagged,
            prompt=prompt,
            max_new_tokens=high_tokens,
            max_image_pixels=high_pixels,
            blocked_phrases=blocked_phrases,
            concurrency=concurrency,
            profile=profile,
            use_transcribe_many=use_transcribe_many,
        )
        total_wall += rerun_wall
        for idx in flagged:
            merged_outputs[idx] = rerun_outputs[idx]
            merged_latencies[idx] += rerun_latencies[idx]

    return PassStats(
        name=name,
        wall_seconds=total_wall,
        page_latencies=merged_latencies,
        total_chars=sum(len(text) for text in merged_outputs),
        outputs=merged_outputs,
        metadata={
            "adaptive": True,
            "transport_mode": "batch" if use_transcribe_many else "page",
            "latency_semantics": "collective_wall_for_entire_batch" if use_transcribe_many else "per_page_rpc_wall",
            "low_tokens": low_tokens,
            "high_tokens": high_tokens,
            "low_pixels": low_pixels,
            "high_pixels": high_pixels,
            "flagged_pages": len(flagged),
            "flagged_indices": flagged,
            "rerun_wall_seconds": round(rerun_wall, 4),
        },
    )


async def _run(args: argparse.Namespace) -> dict:
    resolved_pdf_path, temporary_download = _resolve_pdf_path(args.pdf)
    try:
        render_start = time.perf_counter()
        images = _render_pdf_pages(
            resolved_pdf_path,
            dpi=args.dpi,
            max_pages=args.max_pages,
            render_cache_dir=args.render_cache_dir,
        )
        render_seconds = time.perf_counter() - render_start
        page_complexity = _summarize_page_complexities(images)

        runtime_class = _resolve_runtime_class()
        load_start = time.perf_counter()
        runtime = runtime_class(
            model_path=args.model,
            prompt=args.prompt,
            max_batch_size=args.max_batch_size,
            max_batch_wait_ms=args.max_batch_wait_ms,
            max_new_tokens=args.max_new_tokens,
            max_image_pixels=args.max_image_pixels,
            profile_speed_repetition_penalty=args.profile_speed_repetition_penalty,
            profile_balanced_repetition_penalty=args.profile_balanced_repetition_penalty,
            profile_quality_repetition_penalty=args.profile_quality_repetition_penalty,
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
        model_load_seconds = time.perf_counter() - load_start
        runtime_compatibility_snapshot = (
            runtime.runtime_compatibility_snapshot()
            if hasattr(runtime, "runtime_compatibility_snapshot")
            else build_chandra_runtime_compatibility_snapshot(runtime)
        )
        required_effective_backend = str(getattr(args, "require_effective_runtime_backend", "") or "").strip().lower()
        effective_backend = str(runtime_compatibility_snapshot.get("effective_runtime_backend") or "").strip().lower()
        if required_effective_backend and effective_backend != required_effective_backend:
            raise RuntimeError(
                f"Benchmark requires effective runtime backend '{required_effective_backend}', "
                f"but runtime initialized as '{effective_backend or 'unknown'}'."
            )

        passes: List[PassStats] = []

        async def _execute_pass(pass_name: str) -> PassStats:
            resolved_max_new_tokens = None if args.use_profile_defaults else args.max_new_tokens
            resolved_max_image_pixels = None if args.use_profile_defaults else args.max_image_pixels
            if args.adaptive:
                return await _run_adaptive_pass(
                    runtime=runtime,
                    images=images,
                    prompt=args.prompt,
                    concurrency=args.concurrency,
                    low_tokens=args.adaptive_low_tokens,
                    high_tokens=args.adaptive_high_tokens,
                    low_pixels=args.adaptive_low_pixels,
                    high_pixels=args.adaptive_high_pixels,
                    blocked_phrases=args.bad_word,
                    min_chars=args.adaptive_min_chars,
                    name=pass_name,
                    profile=args.profile,
                    use_transcribe_many=args.transport_mode == "batch",
                )
            sparse_first_pass_max_image_pixels = getattr(args, "sparse_first_pass_max_image_pixels", None)
            if sparse_first_pass_max_image_pixels:
                return await _run_sparse_feature_pass(
                    runtime=runtime,
                    images=images,
                    page_complexity=page_complexity,
                    prompt=args.prompt,
                    max_new_tokens=resolved_max_new_tokens,
                    default_max_image_pixels=resolved_max_image_pixels,
                    lowered_max_image_pixels=sparse_first_pass_max_image_pixels,
                    blocked_phrases=args.bad_word,
                    concurrency=args.concurrency,
                    name=pass_name,
                    near_white_threshold=args.sparse_near_white_threshold,
                    ink_threshold=args.sparse_ink_threshold,
                    edge_threshold=args.sparse_edge_threshold,
                    variance_threshold=args.sparse_variance_threshold,
                    rerun_suspect_pages=bool(args.sparse_rerun_suspect_pages),
                    rerun_min_chars=args.sparse_rerun_min_chars,
                    profile=args.profile,
                    use_transcribe_many=args.transport_mode == "batch",
                )
            document_shape_first_pass_max_image_pixels = getattr(args, "document_shape_first_pass_max_image_pixels", None)
            if document_shape_first_pass_max_image_pixels:
                return await _run_document_shape_pass(
                    runtime=runtime,
                    images=images,
                    page_complexity=page_complexity,
                    prompt=args.prompt,
                    max_new_tokens=resolved_max_new_tokens,
                    default_max_image_pixels=resolved_max_image_pixels,
                    lowered_max_image_pixels=document_shape_first_pass_max_image_pixels,
                    blocked_phrases=args.bad_word,
                    concurrency=args.concurrency,
                    name=pass_name,
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
            tapered_min_max_image_pixels = getattr(args, "tapered_min_max_image_pixels", None)
            if tapered_min_max_image_pixels:
                return await _run_tapered_feature_pass(
                    runtime=runtime,
                    images=images,
                    page_complexity=page_complexity,
                    prompt=args.prompt,
                    max_new_tokens=resolved_max_new_tokens,
                    default_max_image_pixels=resolved_max_image_pixels or 589824,
                    min_max_image_pixels=tapered_min_max_image_pixels,
                    medium_max_image_pixels=getattr(args, "tapered_medium_max_image_pixels", None),
                    blocked_phrases=args.bad_word,
                    concurrency=args.concurrency,
                    name=pass_name,
                    near_white_weight=args.tapered_near_white_weight,
                    ink_weight=args.tapered_ink_weight,
                    edge_weight=args.tapered_edge_weight,
                    variance_weight=args.tapered_variance_weight,
                    profile=args.profile,
                )
            triage_simple_max_image_pixels = getattr(args, "triage_simple_max_image_pixels", None)
            if triage_simple_max_image_pixels:
                return await _run_triaged_pass(
                    runtime=runtime,
                    images=images,
                    page_complexity=page_complexity,
                    prompt=args.prompt,
                    max_new_tokens=resolved_max_new_tokens,
                    default_max_image_pixels=resolved_max_image_pixels,
                    lowered_max_image_pixels=triage_simple_max_image_pixels,
                    blocked_phrases=args.bad_word,
                    concurrency=args.concurrency,
                    name=pass_name,
                    profile=args.profile,
                    use_transcribe_many=args.transport_mode == "batch",
                    lowered_page_classes=_normalize_triage_classes(
                        getattr(args, "triage_lowered_page_classes", None)
                    ),
                )
            return await _run_pass(
                runtime=runtime,
                images=images,
                prompt=args.prompt,
                max_new_tokens=resolved_max_new_tokens,
                max_image_pixels=resolved_max_image_pixels,
                blocked_phrases=args.bad_word,
                concurrency=args.concurrency,
                name=pass_name,
                profile=args.profile,
                use_transcribe_many=args.transport_mode == "batch",
            )
        passes.append(await _execute_pass("cold"))

        for warm_idx in range(args.warm_runs):
            passes.append(await _execute_pass(f"warm_{warm_idx + 1}"))

        if getattr(runtime, "_batcher", None) is not None:
            await runtime._batcher.shutdown()

        if args.out_markdown:
            pass_name = args.markdown_pass
            selected_pass = passes[-1]
            if pass_name != "last":
                matched = next((item for item in passes if item.name == pass_name), None)
                if matched is None:
                    available = ", ".join(item.name for item in passes)
                    raise ValueError(f"Unknown --markdown-pass '{pass_name}'. Available: {available}")
                selected_pass = matched
            markdown_text = []
            for page_idx, page_text in enumerate(selected_pass.outputs, start=1):
                markdown_text.append(f"## Page {page_idx}\n\n{page_text.strip()}\n")
            out_md = Path(args.out_markdown)
            out_md.parent.mkdir(parents=True, exist_ok=True)
            out_md.write_text("\n---\n\n".join(markdown_text) + "\n", encoding="utf-8")

        if args.out_pages_dir:
            pages_dir = Path(args.out_pages_dir)
            pages_dir.mkdir(parents=True, exist_ok=True)
            for page_idx, page_text in enumerate(passes[-1].outputs, start=1):
                page_path = pages_dir / f"page_{page_idx:04d}.md"
                page_path.write_text(page_text.strip() + "\n", encoding="utf-8")

        results = {
            "pdf": args.pdf,
            "benchmark_schema_version": BENCHMARK_SCHEMA_VERSION,
            "runtime_semantics_version": RUNTIME_SEMANTICS_VERSION,
            "request_shape_version": REQUEST_SHAPE_BATCH_VERSION if args.transport_mode == "batch" else REQUEST_SHAPE_VERSION,
            "render": {
                "dpi": args.dpi,
                "pages": len(images),
                "seconds": round(render_seconds, 4),
                "cache_dir": args.render_cache_dir,
                "page_complexity": page_complexity,
            },
            "runtime": {
                "model": args.model,
                "torch_dtype": args.torch_dtype,
                "max_batch_size": args.max_batch_size,
                "max_batch_wait_ms": args.max_batch_wait_ms,
                "max_new_tokens": None if args.use_profile_defaults else args.max_new_tokens,
                "max_image_pixels": None if args.use_profile_defaults else args.max_image_pixels,
                "concurrency": args.concurrency,
                "model_load_seconds": round(model_load_seconds, 4),
                "profile": args.profile,
                "runtime_backend": args.runtime_backend,
                "transport_mode": args.transport_mode,
                "triage_simple_max_image_pixels": getattr(args, "triage_simple_max_image_pixels", None),
                "document_shape_first_pass_max_image_pixels": getattr(args, "document_shape_first_pass_max_image_pixels", None),
                "document_shape_min_sparse_ratio": getattr(args, "document_shape_min_sparse_ratio", 0.5),
                "document_shape_rerun_suspect_pages": bool(getattr(args, "document_shape_rerun_suspect_pages", False)),
                "document_shape_rerun_min_chars": getattr(args, "document_shape_rerun_min_chars", 450),
                "vllm_server_base_urls": args.vllm_server_base_urls,
                "use_profile_defaults": bool(args.use_profile_defaults),
                "cache_enabled": not args.disable_cache,
                "adaptive": bool(args.adaptive),
                "runtime_semantics_version": RUNTIME_SEMANTICS_VERSION,
                "request_shape_version": REQUEST_SHAPE_BATCH_VERSION if args.transport_mode == "batch" else REQUEST_SHAPE_VERSION,
                "adaptive_low_tokens": args.adaptive_low_tokens,
                "adaptive_high_tokens": args.adaptive_high_tokens,
                "adaptive_low_pixels": args.adaptive_low_pixels,
                "adaptive_high_pixels": args.adaptive_high_pixels,
                "adaptive_min_chars": args.adaptive_min_chars,
                "sparse_first_pass_max_image_pixels": getattr(args, "sparse_first_pass_max_image_pixels", None),
                "sparse_near_white_threshold": getattr(args, "sparse_near_white_threshold", 0.74),
                "sparse_ink_threshold": getattr(args, "sparse_ink_threshold", 0.02),
                "sparse_edge_threshold": getattr(args, "sparse_edge_threshold", 0.03),
                "sparse_variance_threshold": getattr(args, "sparse_variance_threshold", 120.0),
                "sparse_rerun_suspect_pages": bool(getattr(args, "sparse_rerun_suspect_pages", False)),
                "sparse_rerun_min_chars": getattr(args, "sparse_rerun_min_chars", 450),
                "tapered_min_max_image_pixels": getattr(args, "tapered_min_max_image_pixels", None),
                "tapered_medium_max_image_pixels": getattr(args, "tapered_medium_max_image_pixels", None),
                "tapered_near_white_weight": getattr(args, "tapered_near_white_weight", 0.45),
                "tapered_ink_weight": getattr(args, "tapered_ink_weight", 0.25),
                "tapered_edge_weight": getattr(args, "tapered_edge_weight", 0.20),
                "tapered_variance_weight": getattr(args, "tapered_variance_weight", 0.10),
                "blocked_phrases": list(args.bad_word or []),
                "compatibility_snapshot": runtime_compatibility_snapshot,
            },
            "passes": [item.as_dict() for item in passes],
        }
        return results
    finally:
        if temporary_download and os.path.exists(temporary_download):
            os.remove(temporary_download)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark Chandra OCR on a PDF.")
    parser.add_argument("--pdf", required=True, help="Local PDF path or http(s) URL.")
    parser.add_argument("--model", required=True, help="Model path (HF id or local path).")
    parser.add_argument("--prompt", default="Convert this page into clean Markdown.", help="OCR prompt.")
    parser.add_argument("--dpi", type=int, default=144, help="Render DPI for PDF pages.")
    parser.add_argument("--render-cache-dir", default=None, help="Optional on-disk cache directory for rendered pages.")
    parser.add_argument("--max-pages", type=int, default=None, help="Optional page cap.")
    parser.add_argument("--concurrency", type=int, default=24, help="Concurrent page requests.")
    parser.add_argument("--warm-runs", type=int, default=1, help="Number of warm passes after cold pass.")
    parser.add_argument("--max-batch-size", type=int, default=24)
    parser.add_argument("--max-batch-wait-ms", type=int, default=15)
    parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=768,
        help="Output token budget override. Used directly unless --use-profile-defaults is set.",
    )
    parser.add_argument("--max-image-pixels", type=int, default=2_097_152)
    parser.add_argument(
        "--triage-simple-max-image-pixels",
        type=int,
        default=None,
        help="Optional lower image cap applied only to pages classified as simple in benchmark mode.",
    )
    parser.add_argument(
        "--triage-lowered-page-classes",
        default="simple",
        help="Comma-separated benchmark-only page classes that should use the lower image cap. Default: simple",
    )
    parser.add_argument(
        "--sparse-first-pass-max-image-pixels",
        type=int,
        default=None,
        help="Benchmark-only lowered cap for pages matching sparse-feature thresholds.",
    )
    parser.add_argument(
        "--document-shape-first-pass-max-image-pixels",
        type=int,
        default=None,
        help="Benchmark-only lowered cap for the whole document when the sparse-page ratio clears a threshold.",
    )
    parser.add_argument("--document-shape-min-sparse-ratio", type=float, default=0.5)
    parser.add_argument(
        "--document-shape-rerun-suspect-pages",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Rerun structurally suspect pages at the default cap after a lowered-cap document first pass.",
    )
    parser.add_argument("--document-shape-rerun-min-chars", type=int, default=450)
    parser.add_argument("--sparse-near-white-threshold", type=float, default=0.74)
    parser.add_argument("--sparse-ink-threshold", type=float, default=0.02)
    parser.add_argument("--sparse-edge-threshold", type=float, default=0.03)
    parser.add_argument("--sparse-variance-threshold", type=float, default=120.0)
    parser.add_argument(
        "--sparse-rerun-suspect-pages",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Rerun sparse first-pass pages at the default cap if the output looks structurally suspect.",
    )
    parser.add_argument("--sparse-rerun-min-chars", type=int, default=450)
    parser.add_argument(
        "--tapered-min-max-image-pixels",
        type=int,
        default=None,
        help="Benchmark-only minimum image cap for per-page feature-tapered routing.",
    )
    parser.add_argument(
        "--tapered-medium-max-image-pixels",
        type=int,
        default=None,
        help="Optional intermediate image cap for feature-tapered routing.",
    )
    parser.add_argument("--tapered-near-white-weight", type=float, default=0.45)
    parser.add_argument("--tapered-ink-weight", type=float, default=0.25)
    parser.add_argument("--tapered-edge-weight", type=float, default=0.20)
    parser.add_argument("--tapered-variance-weight", type=float, default=0.10)
    parser.add_argument("--profile-speed-repetition-penalty", type=float, default=1.0)
    parser.add_argument("--profile-balanced-repetition-penalty", type=float, default=1.0)
    parser.add_argument("--profile-quality-repetition-penalty", type=float, default=1.0)
    parser.add_argument(
        "--bad-word",
        action="append",
        default=[],
        help="Optional blocked phrase passed through as a decode/output constraint. Repeat for multiple phrases.",
    )
    parser.add_argument("--torch-dtype", default="auto")
    parser.add_argument("--runtime-backend", default="hf", choices=["hf", "vllm", "vllm_server"])
    parser.add_argument(
        "--require-effective-runtime-backend",
        default="",
        help="Optional effective runtime backend that must actually initialize (e.g. vllm, vllm_server, hf).",
    )
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
    parser.add_argument("--profile", default=None, help="Optional runtime profile (speed|balanced|quality|adaptive).")
    parser.add_argument("--disable-cache", action="store_true", help="Disable runtime in-memory cache for benchmark run.")
    parser.add_argument(
        "--use-profile-defaults",
        action="store_true",
        help="Do not override tokens/pixels; let runtime profile/default choose them.",
    )
    parser.add_argument("--adaptive", action="store_true", help="Enable two-stage low/high rerun policy.")
    parser.add_argument(
        "--transport-mode",
        default="page",
        choices=["page", "batch"],
        help="Request transport shape: page-per-call or one batched actor call per pass.",
    )
    parser.add_argument(
        "--adaptive-low-tokens",
        type=int,
        default=512,
        help="Deprecated runtime knob; retained for benchmark script compatibility.",
    )
    parser.add_argument(
        "--adaptive-high-tokens",
        type=int,
        default=1024,
        help="Deprecated runtime knob; retained for benchmark script compatibility.",
    )
    parser.add_argument("--adaptive-low-pixels", type=int, default=1_048_576)
    parser.add_argument("--adaptive-high-pixels", type=int, default=2_097_152)
    parser.add_argument("--adaptive-min-chars", type=int, default=450)
    parser.add_argument("--out-json", default=None, help="Optional path to write JSON results.")
    parser.add_argument("--out-markdown", default=None, help="Optional path to write merged markdown.")
    parser.add_argument("--out-pages-dir", default=None, help="Optional directory for per-page markdown from last pass.")
    parser.add_argument(
        "--markdown-pass",
        default="last",
        help="Pass name to export for --out-markdown (default: last).",
    )
    return parser


def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()
    result = asyncio.run(_run(args))
    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.out_json:
        out_path = Path(args.out_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

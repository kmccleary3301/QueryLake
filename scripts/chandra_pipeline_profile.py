#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import io
import json
import statistics
import time
from pathlib import Path
from typing import Any, Dict, List

from PIL import Image
import pypdfium2 as pdfium

from QueryLake.operation_classes.ray_chandra_class import (
    resolve_pdf_render_scale,
    resolve_profile_max_image_pixels,
)

PROFILE_SCHEMA_VERSION = 1
SERIALIZATION_PATH_VERSION = "png_data_url_v1"
RENDER_POLICY_VERSION = "render_to_profile_cap_v1"


def _percentile(values: List[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = int((len(ordered) - 1) * (pct / 100.0))
    return ordered[max(0, min(idx, len(ordered) - 1))]


def _summarize_ms(values: List[float]) -> Dict[str, float]:
    if not values:
        return {"mean": 0.0, "median": 0.0, "p95": 0.0, "max": 0.0}
    ms = [value * 1000.0 for value in values]
    return {
        "mean": round(statistics.mean(ms), 2),
        "median": round(statistics.median(ms), 2),
        "p95": round(_percentile(ms, 95.0), 2),
        "max": round(max(ms), 2),
    }


def _profile_pdf(pdf_path: Path, dpi: int, max_pages: int, profile: str, max_image_pixels: int | None) -> Dict[str, Any]:
    base_scale = float(dpi) / 72.0
    document = pdfium.PdfDocument(str(pdf_path))
    page_count = min(len(document), max_pages)

    render_times: List[float] = []
    png_encode_times: List[float] = []
    png_decode_times: List[float] = []
    image_to_data_url_times: List[float] = []
    image_to_data_url_total_times: List[float] = []
    png_sizes: List[int] = []
    data_url_sizes: List[int] = []
    page_sizes: List[List[int]] = []
    render_scales: List[float] = []
    render_capped_pages = 0

    for index in range(page_count):
        page = document[index]
        page_width, page_height = page.get_size()
        render_scale = resolve_pdf_render_scale(
            page_width,
            page_height,
            dpi=dpi,
            max_image_pixels=max_image_pixels,
        )
        if render_scale < (base_scale - 1e-6):
            render_capped_pages += 1
        t0 = time.perf_counter()
        image = page.render(scale=render_scale).to_pil().convert("RGB")
        render_times.append(time.perf_counter() - t0)
        page.close()

        page_sizes.append([int(image.size[0]), int(image.size[1])])
        render_scales.append(round(render_scale, 6))

        t0 = time.perf_counter()
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        png_bytes = buffer.getvalue()
        png_encode_times.append(time.perf_counter() - t0)
        png_sizes.append(len(png_bytes))

        t0 = time.perf_counter()
        decoded = Image.open(io.BytesIO(png_bytes)).convert("RGB")
        _ = decoded.size
        png_decode_times.append(time.perf_counter() - t0)

        t0 = time.perf_counter()
        payload = "data:image/png;base64," + base64.b64encode(png_bytes).decode("utf-8")
        image_to_data_url_times.append(time.perf_counter() - t0)
        data_url_sizes.append(len(payload))

        t0 = time.perf_counter()
        total_buffer = io.BytesIO()
        image.save(total_buffer, format="PNG")
        total_payload = "data:image/png;base64," + base64.b64encode(total_buffer.getvalue()).decode("utf-8")
        _ = len(total_payload)
        image_to_data_url_total_times.append(time.perf_counter() - t0)

    document.close()

    return {
        "pdf": str(pdf_path),
        "profile_schema_version": PROFILE_SCHEMA_VERSION,
        "serialization_path_version": SERIALIZATION_PATH_VERSION,
        "render_policy_version": RENDER_POLICY_VERSION,
        "profile": str(profile),
        "dpi": int(dpi),
        "render_target_max_image_pixels": int(max_image_pixels) if max_image_pixels else None,
        "pages_profiled": int(page_count),
        "page_sizes": page_sizes,
        "render_scales": render_scales,
        "render_capped_pages": int(render_capped_pages),
        "render_ms": _summarize_ms(render_times),
        "png_encode_ms": _summarize_ms(png_encode_times),
        "png_decode_ms": _summarize_ms(png_decode_times),
        "image_to_data_url_ms": _summarize_ms(image_to_data_url_times),
        "image_to_data_url_total_ms": _summarize_ms(image_to_data_url_total_times),
        "png_size_bytes": {
            "mean": round(statistics.mean(png_sizes), 2) if png_sizes else 0.0,
            "median": round(statistics.median(png_sizes), 2) if png_sizes else 0.0,
            "max": max(png_sizes) if png_sizes else 0,
        },
        "data_url_size_bytes": {
            "mean": round(statistics.mean(data_url_sizes), 2) if data_url_sizes else 0.0,
            "median": round(statistics.median(data_url_sizes), 2) if data_url_sizes else 0.0,
            "max": max(data_url_sizes) if data_url_sizes else 0,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Profile PDF render and Chandra request-shaping overhead.")
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--dpi", type=int, default=144)
    parser.add_argument("--profile", default="speed")
    parser.add_argument("--max-image-pixels", type=int, default=None)
    parser.add_argument("--max-pages", type=int, default=20)
    parser.add_argument("--out-json", default=None)
    args = parser.parse_args()

    max_image_pixels = args.max_image_pixels
    if max_image_pixels is None:
        max_image_pixels = resolve_profile_max_image_pixels(args.profile)
    report = _profile_pdf(
        Path(args.pdf),
        dpi=args.dpi,
        max_pages=args.max_pages,
        profile=args.profile,
        max_image_pixels=max_image_pixels,
    )
    rendered = json.dumps(report, indent=2)
    print(rendered)
    if args.out_json:
        out_path = Path(args.out_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

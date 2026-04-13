#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any, Dict, List


def _p95(values: List[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = int((len(ordered) - 1) * 0.95)
    return ordered[idx]


def _load_json(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _lane_status_matches(observed: str, required: str) -> bool:
    required_norm = str(required).strip().lower()
    observed_norm = str(observed).strip().lower()
    if required_norm in {"", "any"}:
        return True
    return observed_norm == required_norm


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate frozen Chandra closure gates from artifacts.")
    parser.add_argument("--benchmark-json", required=True, help="Output JSON from chandra_benchmark_pdf.py.")
    parser.add_argument("--quality-json", required=True, help="Output JSON from chandra_quality_compare.py.")
    parser.add_argument(
        "--compatibility-json",
        default=None,
        help="Optional JSON from chandra_runtime_compatibility_report.py.",
    )
    parser.add_argument("--require-runtime-compatibility-snapshot", action="store_true")
    parser.add_argument("--require-baseline-dir", default=None)
    parser.add_argument("--require-benchmark-schema-version", type=int, default=1)
    parser.add_argument("--require-runtime-semantics-version", default="chandra_runtime_v1")
    parser.add_argument("--require-request-shape-version", default="page_request_v1")
    parser.add_argument("--require-current-lane-status", default="any")
    parser.add_argument("--require-target-lane-status", default="any")
    parser.add_argument("--require-runtime-backend-status", default="any")
    parser.add_argument("--warm-max-seconds", type=float, default=30.0)
    parser.add_argument("--warm-p95-max-seconds", type=float, default=33.0)
    parser.add_argument("--warm-min-pages-per-second", type=float, default=None)
    parser.add_argument("--require-quality-verdict", default="pass")
    parser.add_argument("--require-normalized-quality-verdict", default=None)
    parser.add_argument("--out-json", default=None)
    args = parser.parse_args()

    benchmark = _load_json(args.benchmark_json)
    quality = _load_json(args.quality_json)
    compatibility = _load_json(args.compatibility_json) if args.compatibility_json else None
    benchmark_schema_version = int(benchmark.get("benchmark_schema_version", 0) or 0)
    runtime_semantics_version = str(benchmark.get("runtime_semantics_version", "") or "").strip()
    request_shape_version = str(benchmark.get("request_shape_version", "") or "").strip()
    runtime_snapshot = ((benchmark.get("runtime") or {}).get("compatibility_snapshot") if isinstance(benchmark.get("runtime"), dict) else None)
    benchmark_quality_baseline_dir = str(quality.get("baseline_dir", "") or "").strip()

    passes = benchmark.get("passes", [])
    warm_runs = [float(item.get("wall_seconds", 0.0)) for item in passes if str(item.get("name", "")).startswith("warm_")]
    if not warm_runs:
        raise RuntimeError("Benchmark artifact does not contain warm_* passes.")

    warm_min = min(warm_runs)
    warm_max = max(warm_runs)
    warm_mean = statistics.mean(warm_runs)
    warm_median = statistics.median(warm_runs)
    warm_p95 = _p95(warm_runs)
    warm_pps = [
        float(item.get("pages_per_second", 0.0))
        for item in passes
        if str(item.get("name", "")).startswith("warm_")
    ]
    warm_pps_min = min(warm_pps) if warm_pps else 0.0

    quality_verdict = str((quality.get("recommendation") or {}).get("verdict", "")).strip().lower()
    normalized_quality_verdict = str(
        (quality.get("normalized_recommendation") or {}).get("verdict", "")
    ).strip().lower()
    gate_warm = warm_max <= float(args.warm_max_seconds)
    gate_p95 = warm_p95 <= float(args.warm_p95_max_seconds)
    gate_quality = quality_verdict == str(args.require_quality_verdict).strip().lower()
    gate_normalized_quality = (
        True
        if args.require_normalized_quality_verdict is None
        else normalized_quality_verdict == str(args.require_normalized_quality_verdict).strip().lower()
    )
    gate_warm_pps = (
        True
        if args.warm_min_pages_per_second is None
        else warm_pps_min >= float(args.warm_min_pages_per_second)
    )
    gate_benchmark_schema = benchmark_schema_version == int(args.require_benchmark_schema_version)
    gate_runtime_semantics = runtime_semantics_version == str(args.require_runtime_semantics_version).strip()
    gate_request_shape = request_shape_version == str(args.require_request_shape_version).strip()
    gate_runtime_snapshot = True if not args.require_runtime_compatibility_snapshot else isinstance(runtime_snapshot, dict)
    gate_baseline_dir = True if not args.require_baseline_dir else benchmark_quality_baseline_dir == str(args.require_baseline_dir).strip()
    current_lane_status = str(((compatibility or {}).get("current_lane") or {}).get("status") or "").strip().lower()
    target_lane_status = str(((compatibility or {}).get("target_lane") or {}).get("status") or "").strip().lower()
    runtime_backend_status = str(((compatibility or {}).get("runtime") or {}).get("status") or "").strip().lower()
    gate_current_lane = _lane_status_matches(current_lane_status, args.require_current_lane_status)
    gate_target_lane = _lane_status_matches(target_lane_status, args.require_target_lane_status)
    gate_runtime_backend = _lane_status_matches(runtime_backend_status, args.require_runtime_backend_status)

    result = {
        "benchmark_json": args.benchmark_json,
        "quality_json": args.quality_json,
        "compatibility_json": args.compatibility_json,
        "benchmark_schema_version": benchmark_schema_version,
        "runtime_semantics_version": runtime_semantics_version,
        "request_shape_version": request_shape_version,
        "warm_runs_seconds": warm_runs,
        "warm_summary": {
            "count": len(warm_runs),
            "min": round(warm_min, 4),
            "max": round(warm_max, 4),
            "mean": round(warm_mean, 4),
            "median": round(warm_median, 4),
            "p95": round(warm_p95, 4),
        },
        "quality_verdict": quality_verdict,
        "normalized_quality_verdict": normalized_quality_verdict or None,
        "gates": {
            "warm_leq_threshold": {
                "threshold_seconds": float(args.warm_max_seconds),
                "pass": bool(gate_warm),
            },
            "warm_p95_leq_threshold": {
                "threshold_seconds": float(args.warm_p95_max_seconds),
                "pass": bool(gate_p95),
            },
            "warm_pages_per_second_geq_threshold": {
                "threshold_pages_per_second": (
                    float(args.warm_min_pages_per_second)
                    if args.warm_min_pages_per_second is not None
                    else None
                ),
                "observed_min_pages_per_second": round(warm_pps_min, 4) if warm_pps else None,
                "pass": bool(gate_warm_pps),
            },
            "quality_verdict_match": {
                "required": str(args.require_quality_verdict).strip().lower(),
                "pass": bool(gate_quality),
            },
            "normalized_quality_verdict_match": {
                "required": (
                    str(args.require_normalized_quality_verdict).strip().lower()
                    if args.require_normalized_quality_verdict is not None
                    else None
                ),
                "observed": normalized_quality_verdict or None,
                "pass": bool(gate_normalized_quality),
            },
            "benchmark_schema_version_match": {
                "required": int(args.require_benchmark_schema_version),
                "pass": bool(gate_benchmark_schema),
            },
            "runtime_semantics_version_match": {
                "required": str(args.require_runtime_semantics_version).strip(),
                "pass": bool(gate_runtime_semantics),
            },
            "request_shape_version_match": {
                "required": str(args.require_request_shape_version).strip(),
                "pass": bool(gate_request_shape),
            },
            "runtime_compatibility_snapshot_present": {
                "required": bool(args.require_runtime_compatibility_snapshot),
                "pass": bool(gate_runtime_snapshot),
            },
            "baseline_dir_match": {
                "required": str(args.require_baseline_dir).strip() if args.require_baseline_dir else None,
                "observed": benchmark_quality_baseline_dir or None,
                "pass": bool(gate_baseline_dir),
            },
            "current_lane_status_match": {
                "required": str(args.require_current_lane_status).strip().lower(),
                "observed": current_lane_status or None,
                "pass": bool(gate_current_lane),
            },
            "target_lane_status_match": {
                "required": str(args.require_target_lane_status).strip().lower(),
                "observed": target_lane_status or None,
                "pass": bool(gate_target_lane),
            },
            "runtime_backend_status_match": {
                "required": str(args.require_runtime_backend_status).strip().lower(),
                "observed": runtime_backend_status or None,
                "pass": bool(gate_runtime_backend),
            },
        },
    }
    result["overall_pass"] = bool(
        gate_warm
        and gate_p95
        and gate_warm_pps
        and gate_quality
        and gate_normalized_quality
        and gate_benchmark_schema
        and gate_runtime_semantics
        and gate_request_shape
        and gate_runtime_snapshot
        and gate_baseline_dir
        and gate_current_lane
        and gate_target_lane
        and gate_runtime_backend
    )

    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.out_json:
        out_path = Path(args.out_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

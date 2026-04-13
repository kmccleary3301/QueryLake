#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _load_json(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _get_passes(benchmark: Dict[str, Any]) -> List[Dict[str, Any]]:
    passes = benchmark.get("passes", [])
    if not isinstance(passes, list):
        return []
    return [item for item in passes if isinstance(item, dict)]


def _primary_pass(benchmark: Dict[str, Any]) -> Dict[str, Any]:
    passes = _get_passes(benchmark)
    if not passes:
        raise ValueError("Benchmark artifact does not contain any passes.")
    warm_passes = [item for item in passes if str(item.get("name", "")).startswith("warm_")]
    return warm_passes[-1] if warm_passes else passes[-1]


def _pass_by_name(benchmark: Dict[str, Any], name: str) -> Optional[Dict[str, Any]]:
    for item in _get_passes(benchmark):
        if str(item.get("name", "")) == name:
            return item
    return None


def _pct_delta(base: float, cand: float) -> float:
    if base == 0:
        return 0.0
    return ((cand - base) / base) * 100.0


def _seconds(value: Any) -> float:
    return float(value or 0.0)


def _pass_summary(pass_data: Dict[str, Any]) -> Dict[str, Any]:
    latency = dict(pass_data.get("latency_ms") or {})
    return {
        "name": str(pass_data.get("name", "")),
        "pages": int(pass_data.get("pages") or 0),
        "wall_seconds": _seconds(pass_data.get("wall_seconds")),
        "pages_per_second": float(pass_data.get("pages_per_second") or 0.0),
        "total_chars": int(pass_data.get("total_chars") or 0),
        "latency_ms": {
            "mean": float(latency.get("mean") or 0.0),
            "median": float(latency.get("median") or 0.0),
            "p95": float(latency.get("p95") or 0.0),
            "max": float(latency.get("max") or 0.0),
        },
        "metadata": dict(pass_data.get("metadata") or {}),
    }


def _runtime_summary(benchmark: Dict[str, Any]) -> Dict[str, Any]:
    runtime = dict(benchmark.get("runtime") or {})
    render = dict(benchmark.get("render") or {})
    return {
        "benchmark_schema_version": benchmark.get("benchmark_schema_version"),
        "runtime_semantics_version": benchmark.get("runtime_semantics_version"),
        "request_shape_version": benchmark.get("request_shape_version"),
        "render": {
            "dpi": render.get("dpi"),
            "pages": render.get("pages"),
            "seconds": render.get("seconds"),
            "cache_dir": render.get("cache_dir"),
        },
        "runtime": {
            "backend": runtime.get("runtime_backend"),
            "profile": runtime.get("profile"),
            "transport_mode": runtime.get("transport_mode"),
            "use_profile_defaults": runtime.get("use_profile_defaults"),
            "max_batch_size": runtime.get("max_batch_size"),
            "max_batch_wait_ms": runtime.get("max_batch_wait_ms"),
            "max_new_tokens": runtime.get("max_new_tokens"),
            "max_image_pixels": runtime.get("max_image_pixels"),
            "concurrency": runtime.get("concurrency"),
            "vllm_server_base_urls": runtime.get("vllm_server_base_urls"),
        },
    }


def _compare_passes(baseline: Dict[str, Any], candidate: Dict[str, Any]) -> List[Dict[str, Any]]:
    baseline_passes = _get_passes(baseline)
    candidate_passes = _get_passes(candidate)
    baseline_names = [str(item.get("name", "")) for item in baseline_passes]
    candidate_names = [str(item.get("name", "")) for item in candidate_passes]
    shared_names = [name for name in baseline_names if name in candidate_names]
    rows: List[Dict[str, Any]] = []
    for name in shared_names:
        base_pass = _pass_by_name(baseline, name)
        cand_pass = _pass_by_name(candidate, name)
        if base_pass is None or cand_pass is None:
            continue
        base_summary = _pass_summary(base_pass)
        cand_summary = _pass_summary(cand_pass)
        rows.append(
            {
                "name": name,
                "baseline": base_summary,
                "candidate": cand_summary,
                "delta": {
                    "wall_seconds": round(cand_summary["wall_seconds"] - base_summary["wall_seconds"], 6),
                    "wall_seconds_pct": round(_pct_delta(base_summary["wall_seconds"], cand_summary["wall_seconds"]), 3),
                    "pages_per_second": round(cand_summary["pages_per_second"] - base_summary["pages_per_second"], 6),
                    "pages_per_second_pct": round(
                        _pct_delta(base_summary["pages_per_second"], cand_summary["pages_per_second"]), 3
                    ),
                    "total_chars": cand_summary["total_chars"] - base_summary["total_chars"],
                    "latency_ms_mean": round(
                        cand_summary["latency_ms"]["mean"] - base_summary["latency_ms"]["mean"], 3
                    ),
                    "latency_ms_p95": round(
                        cand_summary["latency_ms"]["p95"] - base_summary["latency_ms"]["p95"], 3
                    ),
                },
            }
        )
    return rows


def _recommendation(primary_delta: Dict[str, Any], transport_changed: bool) -> Dict[str, Any]:
    pps_pct = float(primary_delta.get("pages_per_second_pct") or 0.0)
    wall_pct = float(primary_delta.get("wall_seconds_pct") or 0.0)
    if pps_pct >= 10.0:
        verdict = "improve"
        note = "Candidate is materially faster on the primary pass."
    elif pps_pct <= -10.0:
        verdict = "regress"
        note = "Candidate is materially slower on the primary pass."
    else:
        verdict = "flat"
        note = "Primary throughput is broadly unchanged."
    if transport_changed:
        note += " Transport shape changed, so latency should be interpreted alongside request-mode metadata."
    return {
        "verdict": verdict,
        "note": note,
        "primary_pages_per_second_pct": round(pps_pct, 3),
        "primary_wall_seconds_pct": round(wall_pct, 3),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare two Chandra benchmark JSON artifacts.")
    parser.add_argument("--baseline-json", required=True)
    parser.add_argument("--candidate-json", required=True)
    parser.add_argument("--out-json", default=None)
    parser.add_argument("--out-md", default=None)
    args = parser.parse_args()

    baseline = _load_json(args.baseline_json)
    candidate = _load_json(args.candidate_json)

    baseline_primary = _pass_summary(_primary_pass(baseline))
    candidate_primary = _pass_summary(_primary_pass(candidate))
    primary_delta = {
        "wall_seconds": round(candidate_primary["wall_seconds"] - baseline_primary["wall_seconds"], 6),
        "wall_seconds_pct": round(_pct_delta(baseline_primary["wall_seconds"], candidate_primary["wall_seconds"]), 3),
        "pages_per_second": round(candidate_primary["pages_per_second"] - baseline_primary["pages_per_second"], 6),
        "pages_per_second_pct": round(
            _pct_delta(baseline_primary["pages_per_second"], candidate_primary["pages_per_second"]), 3
        ),
        "total_chars": candidate_primary["total_chars"] - baseline_primary["total_chars"],
        "latency_ms_mean": round(
            candidate_primary["latency_ms"]["mean"] - baseline_primary["latency_ms"]["mean"], 3
        ),
        "latency_ms_p95": round(candidate_primary["latency_ms"]["p95"] - baseline_primary["latency_ms"]["p95"], 3),
    }
    baseline_runtime = _runtime_summary(baseline)
    candidate_runtime = _runtime_summary(candidate)
    pass_rows = _compare_passes(baseline, candidate)
    transport_changed = (
        str(baseline_runtime["runtime"].get("transport_mode") or "") != str(candidate_runtime["runtime"].get("transport_mode") or "")
        or str(baseline_runtime["request_shape_version"] or "") != str(candidate_runtime["request_shape_version"] or "")
    )
    report = {
        "baseline_json": str(Path(args.baseline_json)),
        "candidate_json": str(Path(args.candidate_json)),
        "baseline": {
            "primary_pass": baseline_primary,
            "runtime": baseline_runtime,
        },
        "candidate": {
            "primary_pass": candidate_primary,
            "runtime": candidate_runtime,
        },
        "primary_delta": primary_delta,
        "transport_changed": transport_changed,
        "recommendation": _recommendation(primary_delta, transport_changed),
        "common_passes": pass_rows,
    }

    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)
    if args.out_json:
        out_path = Path(args.out_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered + "\n", encoding="utf-8")
    if args.out_md:
        lines = [
            "# Chandra Benchmark Comparison",
            "",
            f"- Baseline: `{args.baseline_json}`",
            f"- Candidate: `{args.candidate_json}`",
            f"- Primary pass delta pages/sec: `{primary_delta['pages_per_second']:+.4f}`",
            f"- Primary pass delta wall seconds: `{primary_delta['wall_seconds']:+.4f}`",
            f"- Recommendation: `{report['recommendation']['verdict']}`",
            f"- Note: {report['recommendation']['note']}",
        ]
        out_path = Path(args.out_md)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

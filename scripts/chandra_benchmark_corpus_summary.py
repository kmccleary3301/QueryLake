#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime
import json
import statistics
from pathlib import Path
from typing import Any, Dict, List, Optional


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _primary_pass(benchmark: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    passes = benchmark.get("passes", [])
    if not isinstance(passes, list) or not passes:
        return None
    warm_passes = [item for item in passes if isinstance(item, dict) and str(item.get("name", "")).startswith("warm_")]
    return warm_passes[-1] if warm_passes else next((item for item in reversed(passes) if isinstance(item, dict)), None)


def _benchmark_entry(path: Path, data: Dict[str, Any]) -> Dict[str, Any]:
    runtime = dict(data.get("runtime") or {})
    render = dict(data.get("render") or {})
    primary = _primary_pass(data) or {}
    return {
        "file": path.name,
        "backend": runtime.get("runtime_backend"),
        "profile": runtime.get("profile"),
        "pages": primary.get("pages"),
        "pps": primary.get("pages_per_second"),
        "wall_seconds": primary.get("wall_seconds"),
        "render_seconds": render.get("seconds"),
        "model_load_seconds": runtime.get("model_load_seconds"),
        "use_profile_defaults": runtime.get("use_profile_defaults"),
        "max_image_pixels": runtime.get("max_image_pixels"),
        "max_new_tokens": runtime.get("max_new_tokens"),
        "vllm_server_base_urls": runtime.get("vllm_server_base_urls"),
    }


def _top_entries(entries: List[Dict[str, Any]], *, limit: int) -> List[Dict[str, Any]]:
    sortable = [entry for entry in entries if isinstance(entry.get("pps"), (int, float))]
    sortable.sort(key=lambda row: float(row.get("pps") or 0.0), reverse=True)
    return sortable[:limit]


def _aggregate(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    pps_values = [float(entry["pps"]) for entry in entries if isinstance(entry.get("pps"), (int, float))]
    return {
        "count": len(entries),
        "with_pps": len(pps_values),
        "pps_mean": round(statistics.mean(pps_values), 6) if pps_values else None,
        "pps_median": round(statistics.median(pps_values), 6) if pps_values else None,
        "pps_max": round(max(pps_values), 6) if pps_values else None,
    }


def _group_top(entries: List[Dict[str, Any]], backend: str, limit: int) -> List[Dict[str, Any]]:
    filtered = [entry for entry in entries if str(entry.get("backend") or "") == backend]
    return _top_entries(filtered, limit=limit)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize Chandra benchmark JSON artifacts.")
    parser.add_argument("--benchmarks-dir", required=True)
    parser.add_argument("--out-json", default=None)
    parser.add_argument("--top-n", type=int, default=10)
    args = parser.parse_args()

    benchmark_dir = Path(args.benchmarks_dir)
    if not benchmark_dir.exists() or not benchmark_dir.is_dir():
        raise FileNotFoundError(f"Benchmark directory does not exist: {benchmark_dir}")

    entries: List[Dict[str, Any]] = []
    for path in sorted(benchmark_dir.glob("*.json")):
        data = _load_json(path)
        if "passes" not in data or not isinstance(data.get("passes"), list):
            continue
        entries.append(_benchmark_entry(path, data))

    summary = {
        "generated_on": datetime.date.today().isoformat(),
        "benchmark_file_count": len(entries),
        "benchmark_entries": entries,
        "top_overall": _top_entries(entries, limit=args.top_n),
        "top_hf": _group_top(entries, "hf", args.top_n),
        "top_vllm_server": _group_top(entries, "vllm_server", args.top_n),
        "top_vllm": _group_top(entries, "vllm", args.top_n),
        "aggregate": _aggregate(entries),
    }

    rendered = json.dumps(summary, indent=2, sort_keys=True)
    print(rendered)
    if args.out_json:
        out_path = Path(args.out_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

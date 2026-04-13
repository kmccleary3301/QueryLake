#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def _load_json(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_matrix(compatibility: Dict[str, Any], benchmark: Dict[str, Any] | None = None) -> Dict[str, Any]:
    package_versions = compatibility.get("package_versions") or {}
    probes = compatibility.get("probes") or {}
    benchmark_runtime = ((benchmark or {}).get("runtime") or {}).get("compatibility_snapshot") or {}
    compatibility_runtime = compatibility.get("runtime") or {}
    configured_backend = compatibility_runtime.get("configured_runtime_backend") or benchmark_runtime.get("configured_runtime_backend")
    effective_backend = compatibility_runtime.get("effective_runtime_backend") or benchmark_runtime.get("effective_runtime_backend")
    runtime_status = compatibility_runtime.get("status")
    if runtime_status in {None, "", "unknown"} and configured_backend and effective_backend:
        runtime_status = "ready" if configured_backend == effective_backend else "degraded"
    return {
        "artifact_type": "chandra_runtime_compatibility_matrix_v1",
        "generated_on": datetime.now(timezone.utc).isoformat(),
        "current_lane": {
            "model_path": compatibility.get("current_lane", {}).get("model_path"),
            "model_type": compatibility.get("current_lane", {}).get("observed", {}).get("model_type"),
            "architectures": compatibility.get("current_lane", {}).get("observed", {}).get("architectures") or [],
            "status": compatibility.get("current_lane", {}).get("status"),
            "probe_status": (probes.get("current") or {}).get("status"),
            "benchmarkable": bool(benchmark),
        },
        "target_lane": {
            "model_path": compatibility.get("target_lane", {}).get("model_path"),
            "model_type": compatibility.get("target_lane", {}).get("observed", {}).get("model_type"),
            "architectures": compatibility.get("target_lane", {}).get("observed", {}).get("architectures") or [],
            "status": compatibility.get("target_lane", {}).get("status"),
            "probe_status": (probes.get("target") or {}).get("status"),
            "benchmarkable": bool(benchmark),
        },
        "runtime": {
            "configured_backend": configured_backend,
            "effective_backend": effective_backend,
            "status": runtime_status,
            "fallback": bool(configured_backend and effective_backend and configured_backend != effective_backend),
        },
        "package_versions": {
            "torch": package_versions.get("torch"),
            "transformers": package_versions.get("transformers"),
            "vllm": package_versions.get("vllm"),
            "ray": package_versions.get("ray"),
            "pillow": package_versions.get("pillow"),
            "pypdfium2": package_versions.get("pypdfium2"),
        },
        "benchmark_runtime_snapshot_present": bool(benchmark_runtime),
        "benchmark_request_shape_version": (benchmark or {}).get("request_shape_version"),
        "benchmark_runtime_semantics_version": (benchmark or {}).get("runtime_semantics_version"),
    }


def _render_markdown(matrix: Dict[str, Any]) -> str:
    current = matrix["current_lane"]
    target = matrix["target_lane"]
    runtime = matrix["runtime"]
    packages = matrix["package_versions"]
    lines = [
        "# Chandra Runtime Compatibility Matrix",
        "",
        f"- Generated on: `{matrix['generated_on']}`",
        f"- Benchmark runtime snapshot present: `{matrix['benchmark_runtime_snapshot_present']}`",
        f"- Benchmark runtime semantics version: `{matrix['benchmark_runtime_semantics_version']}`",
        f"- Benchmark request shape version: `{matrix['benchmark_request_shape_version']}`",
        "",
        "## Current Lane",
        f"- Model path: `{current['model_path']}`",
        f"- Model type: `{current['model_type']}`",
        f"- Architectures: `{', '.join(current['architectures'])}`",
        f"- Lane status: `{current['status']}`",
        f"- Probe status: `{current['probe_status']}`",
        f"- Benchmarkable: `{current['benchmarkable']}`",
        "",
        "## Target Lane",
        f"- Model path: `{target['model_path']}`",
        f"- Model type: `{target['model_type']}`",
        f"- Architectures: `{', '.join(target['architectures'])}`",
        f"- Lane status: `{target['status']}`",
        f"- Probe status: `{target['probe_status']}`",
        f"- Benchmarkable: `{target['benchmarkable']}`",
        "",
        "## Runtime",
        f"- Configured backend: `{runtime['configured_backend']}`",
        f"- Effective backend: `{runtime['effective_backend']}`",
        f"- Status: `{runtime['status']}`",
        f"- Fallback active: `{runtime['fallback']}`",
        "",
        "## Package Versions",
    ]
    for key, value in packages.items():
        lines.append(f"- {key}: `{value}`")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a compact Chandra compatibility matrix artifact.")
    parser.add_argument("--compatibility-json", required=True)
    parser.add_argument("--benchmark-json", default=None)
    parser.add_argument("--out-json", default=None)
    parser.add_argument("--out-md", default=None)
    args = parser.parse_args()

    compatibility = _load_json(args.compatibility_json)
    benchmark = _load_json(args.benchmark_json) if args.benchmark_json else None
    matrix = build_matrix(compatibility, benchmark)
    rendered = json.dumps(matrix, indent=2, sort_keys=True)
    print(rendered)
    if args.out_json:
        out_json = Path(args.out_json)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(rendered + "\n", encoding="utf-8")
    if args.out_md:
        out_md = Path(args.out_md)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_md.write_text(_render_markdown(matrix), encoding="utf-8")


if __name__ == "__main__":
    main()

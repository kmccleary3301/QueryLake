#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def _load_json(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _require(value: bool, name: str, failures: List[str]) -> None:
    if not value:
        failures.append(name)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Chandra benchmark artifact schema and metadata.")
    parser.add_argument("--benchmark-json", required=True)
    parser.add_argument("--require-benchmark-schema-version", type=int, default=1)
    parser.add_argument("--require-runtime-semantics-version", default="chandra_runtime_v1")
    parser.add_argument("--require-request-shape-version", default=None)
    parser.add_argument("--require-runtime-compatibility-snapshot", action="store_true")
    parser.add_argument("--out-json", default=None)
    args = parser.parse_args()

    benchmark = _load_json(args.benchmark_json)
    failures: List[str] = []

    _require(
        int(benchmark.get("benchmark_schema_version", 0) or 0) == int(args.require_benchmark_schema_version),
        "benchmark_schema_version_mismatch",
        failures,
    )
    _require(
        str(benchmark.get("runtime_semantics_version", "") or "").strip()
        == str(args.require_runtime_semantics_version).strip(),
        "runtime_semantics_version_mismatch",
        failures,
    )
    if args.require_request_shape_version:
        _require(
            str(benchmark.get("request_shape_version", "") or "").strip()
            == str(args.require_request_shape_version).strip(),
            "request_shape_version_mismatch",
            failures,
        )
    if args.require_runtime_compatibility_snapshot:
        runtime = benchmark.get("runtime")
        snapshot = runtime.get("compatibility_snapshot") if isinstance(runtime, dict) else None
        _require(isinstance(snapshot, dict), "missing_runtime_compatibility_snapshot", failures)

    result = {
        "benchmark_json": args.benchmark_json,
        "failures": failures,
        "pass": not failures,
    }
    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.out_json:
        out_path = Path(args.out_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

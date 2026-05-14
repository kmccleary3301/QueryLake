#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.scanning.registry import build_default_scanner_registry, registry_report_rows


def _markdown_table(rows: List[Dict[str, Any]]) -> str:
    headers = [
        "backend_id",
        "backend_class",
        "support_tier",
        "status",
        "routing_eligibility",
        "deployment_model",
        "geometry_level",
        "cost_class",
        "privacy_class",
        "benchmark_status",
    ]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(header, "")) for header in headers) + " |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Print the default QueryLake scanner backend registry.")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    rows = registry_report_rows(build_default_scanner_registry())
    if args.format == "json":
        payload = json.dumps(rows, indent=2, sort_keys=True)
    else:
        payload = _markdown_table(rows)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

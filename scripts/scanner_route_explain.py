#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.scanning.contracts import ScanRequest
from QueryLake.scanning.registry import build_default_scanner_registry
from QueryLake.scanning.routing import explain_routing_plan, plan_scan_route, routing_plan_to_markdown


def _load_request(path: Path) -> ScanRequest:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return ScanRequest(**payload)


def main() -> int:
    parser = argparse.ArgumentParser(description="Explain scanner routing for a ScanRequest JSON payload.")
    parser.add_argument("request_json", type=Path, help="Path to a JSON object matching ScanRequest fields")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args()

    request = _load_request(args.request_json)
    plan = plan_scan_route(build_default_scanner_registry(), request)
    if args.format == "markdown":
        print(routing_plan_to_markdown(plan))
    else:
        print(json.dumps(explain_routing_plan(plan), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

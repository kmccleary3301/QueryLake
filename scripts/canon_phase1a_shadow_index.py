#!/usr/bin/env python
from __future__ import annotations

import argparse
import json

from QueryLake.canon.runtime import build_shadow_report_index, load_shadow_reports, persist_shadow_report_index


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a Canon++ Phase 1A shadow report index.")
    parser.add_argument("--report-dir", required=True, help="Directory containing canon_shadow_report_v1 artifacts.")
    parser.add_argument("--output", required=True, help="Output JSON file path.")
    args = parser.parse_args()

    reports = load_shadow_reports(args.report_dir)
    payload = build_shadow_report_index(reports)
    output_path = persist_shadow_report_index(index_payload=payload, output_path=args.output)
    print(json.dumps({"output_path": output_path, "report_count": payload["report_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

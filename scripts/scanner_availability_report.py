#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from QueryLake.scanning.availability import scanner_availability_rows, scanner_availability_to_markdown


def main() -> int:
    parser = argparse.ArgumentParser(description="Report scanner backend availability without loading heavy adapters eagerly.")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    args = parser.parse_args()

    rows = scanner_availability_rows()
    if args.format == "json":
        print(json.dumps({"rows": rows}, indent=2, sort_keys=True))
    else:
        print(scanner_availability_to_markdown(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

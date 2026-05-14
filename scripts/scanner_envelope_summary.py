#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.files.object_store import LocalCASObjectStore
from QueryLake.scanning.persistence import read_scanner_envelope_payload, summarize_scanner_envelope_payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a bounded summary for a persisted scanner envelope CAS object.")
    parser.add_argument("--store-dir", required=True, type=Path, help="Local CAS object store directory")
    parser.add_argument("--cas", required=True, help="Scanner envelope CAS ref")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    store = LocalCASObjectStore(args.store_dir)
    payload = read_scanner_envelope_payload(store, args.cas)
    summary = summarize_scanner_envelope_payload(payload)
    print(json.dumps(summary, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

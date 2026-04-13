#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.local_dense_sidecar import LOCAL_DENSE_SIDECAR_ADAPTER


DOC_PATH = ROOT / "docs/database/LOCAL_DENSE_SIDECAR_CONTRACT.md"
BLOCK_RE = re.compile(
    r"<!-- BEGIN_LOCAL_DENSE_SIDECAR_CONTRACT -->\s*```json\n(.*?)\n```\s*<!-- END_LOCAL_DENSE_SIDECAR_CONTRACT -->",
    re.DOTALL,
)


def _expected_contract_json() -> str:
    return json.dumps(LOCAL_DENSE_SIDECAR_ADAPTER.contract().payload(), indent=2, sort_keys=True)


def main() -> int:
    content = DOC_PATH.read_text(encoding="utf-8")
    match = BLOCK_RE.search(content)
    if match is None:
        print(f"Missing dense-sidecar contract block in {DOC_PATH}", file=sys.stderr)
        return 1

    observed = json.dumps(json.loads(match.group(1)), indent=2, sort_keys=True)
    expected = _expected_contract_json()
    if observed != expected:
        print("Local dense-sidecar contract drift detected.", file=sys.stderr)
        print(f"Docs file: {DOC_PATH}", file=sys.stderr)
        print("Expected:", file=sys.stderr)
        print(expected, file=sys.stderr)
        print("Observed:", file=sys.stderr)
        print(observed, file=sys.stderr)
        return 1

    print("Local dense-sidecar contract is in sync.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

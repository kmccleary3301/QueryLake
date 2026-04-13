#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.db_compat_v2_runtime_boundary_status import build_v2_runtime_boundary_payload


DOC_PATH = ROOT / "docs/database/V2_RUNTIME_BOUNDARY.md"
BLOCK_RE = re.compile(
    r"<!-- BEGIN_V2_RUNTIME_BOUNDARY_CONTRACT -->\s*```json\n(.*?)\n```\s*<!-- END_V2_RUNTIME_BOUNDARY_CONTRACT -->",
    re.DOTALL,
)


def main() -> int:
    content = DOC_PATH.read_text(encoding="utf-8")
    match = BLOCK_RE.search(content)
    if match is None:
        print(f"Missing V2 runtime-boundary contract block in {DOC_PATH}", file=sys.stderr)
        return 1

    observed = json.dumps(json.loads(match.group(1)), indent=2, sort_keys=True)
    expected = json.dumps(build_v2_runtime_boundary_payload(), indent=2, sort_keys=True)
    if observed != expected:
        print("V2 runtime-boundary contract drift detected.", file=sys.stderr)
        print(f"Docs file: {DOC_PATH}", file=sys.stderr)
        print("Expected:", file=sys.stderr)
        print(expected, file=sys.stderr)
        print("Observed:", file=sys.stderr)
        print(observed, file=sys.stderr)
        return 1

    print("V2 runtime-boundary contract is in sync.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

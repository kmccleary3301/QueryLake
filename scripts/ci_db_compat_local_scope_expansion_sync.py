#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.db_compat import DEPLOYMENT_PROFILES
from QueryLake.runtime.local_profile_v2 import (
    LOCAL_PROFILE_ID,
    build_local_profile_scope_expansion_contract_payload,
)


DOC_PATH = ROOT / "docs/database/LOCAL_PROFILE_SCOPE_EXPANSION_CRITERIA.md"
BLOCK_RE = re.compile(
    r"<!-- BEGIN_LOCAL_PROFILE_SCOPE_EXPANSION_CONTRACT -->\s*```json\n(.*?)\n```\s*<!-- END_LOCAL_PROFILE_SCOPE_EXPANSION_CONTRACT -->",
    re.DOTALL,
)


def _expected_contract_json() -> str:
    profile = DEPLOYMENT_PROFILES[LOCAL_PROFILE_ID]
    payload = build_local_profile_scope_expansion_contract_payload(profile=profile)
    return json.dumps(payload, indent=2, sort_keys=True)


def main() -> int:
    content = DOC_PATH.read_text(encoding="utf-8")
    match = BLOCK_RE.search(content)
    if match is None:
        print(f"Missing local profile scope expansion contract block in {DOC_PATH}", file=sys.stderr)
        return 1

    observed = json.dumps(json.loads(match.group(1)), indent=2, sort_keys=True)
    expected = _expected_contract_json()
    if observed != expected:
        print("Local profile scope expansion contract drift detected.", file=sys.stderr)
        print(f"Docs file: {DOC_PATH}", file=sys.stderr)
        print("Expected:", file=sys.stderr)
        print(expected, file=sys.stderr)
        print("Observed:", file=sys.stderr)
        print(observed, file=sys.stderr)
        return 1

    print("Local profile scope expansion contract is in sync.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

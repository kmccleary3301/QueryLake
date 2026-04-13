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
from QueryLake.runtime.local_profile_v2 import build_local_route_support_matrix_payload

DOC_PATH = ROOT / 'docs/database/LOCAL_PROFILE_SUPPORT_MATRIX.md'
JSON_BLOCK_RE = re.compile(r"```json\n(.*?)\n```", re.DOTALL)


def _normalize(value):
    return json.loads(json.dumps(value, sort_keys=True))


def main() -> int:
    text = DOC_PATH.read_text()
    match = JSON_BLOCK_RE.search(text)
    if match is None:
        raise SystemExit(f'No JSON code block found in {DOC_PATH}')
    documented = json.loads(match.group(1))
    runtime = build_local_route_support_matrix_payload(
        profile=DEPLOYMENT_PROFILES['sqlite_fts5_dense_sidecar_local_v1']
    )
    if _normalize(documented) != _normalize(runtime):
        print(json.dumps({'documented': documented, 'runtime': runtime}, indent=2, sort_keys=True))
        raise SystemExit('Local profile support matrix doc does not match code.')
    print(f'Local profile support matrix matches code ({len(runtime)} routes).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

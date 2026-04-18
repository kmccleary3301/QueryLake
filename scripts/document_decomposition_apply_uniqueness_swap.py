#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.database.create_db_session import initialize_database_engine
from QueryLake.runtime.document_decomposition import apply_segment_uniqueness_swap


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Apply the view-scoped document_segment uniqueness swap.')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    database, _ = initialize_database_engine(ensure_sparse_bootstrap=False)
    payload = apply_segment_uniqueness_swap(database, dry_run=bool(args.dry_run))
    if args.json:
        print(json.dumps(payload, indent=2))
        return 0 if payload['action'] in {'plan_swap', 'applied'} else 1
    print(f"action: {payload['action']}")
    print(f"ready_for_swap: {payload['audit']['ready_for_constraint_swap']}")
    return 0 if payload['action'] in {'plan_swap', 'applied'} else 1


if __name__ == '__main__':
    raise SystemExit(main())

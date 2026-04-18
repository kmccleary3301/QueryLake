#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.database.create_db_session import initialize_database_engine
from QueryLake.runtime.document_decomposition import fetch_document_chunk_authority_provenance


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Inspect canonical segment/unit provenance for compatibility chunk rows.')
    parser.add_argument('--document-id', required=True)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)

    database, _ = initialize_database_engine(ensure_sparse_bootstrap=False)
    payload = fetch_document_chunk_authority_provenance(database, document_id=args.document_id)
    if args.json:
        print(json.dumps(payload, indent=2))
        return 0
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

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

from sqlmodel import select

from QueryLake.database.create_db_session import initialize_database_engine
from QueryLake.database.sql_db_tables import document_raw
from QueryLake.runtime.document_decomposition import audit_segment_uniqueness_readiness


def _load_document_ids(database, *, document_ids: List[str], limit: int | None, offset: int = 0) -> List[str]:
    if document_ids:
        return [str(row) for row in document_ids]
    if limit is None:
        return []
    stmt = select(document_raw.id).order_by(document_raw.creation_timestamp.desc())
    if offset:
        stmt = stmt.offset(int(offset))
    stmt = stmt.limit(limit)
    return [str(row) for row in database.exec(stmt).all()]


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Audit readiness for document_segment uniqueness swap.')
    parser.add_argument('--document-id', action='append', default=[])
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--offset', type=int, default=0)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    database, _ = initialize_database_engine(ensure_sparse_bootstrap=False)
    scoped_document_ids = _load_document_ids(database, document_ids=list(args.document_id or []), limit=args.limit, offset=0 if args.document_id else int(args.offset))
    payload = audit_segment_uniqueness_readiness(database, document_ids=scoped_document_ids if args.document_id else None, scope_limit=None if args.document_id else args.limit, scope_offset=0 if args.document_id else int(args.offset))
    if args.json:
        print(json.dumps(payload, indent=2))
        return 0
    for key in [
        'scope_mode',
        'scope_document_count',
        'segment_count',
        'null_segment_view_count',
        'duplicate_key_count',
        'default_view_conflict_count',
        'chunk_authority_missing_count',
        'chunk_authority_orphan_count',
        'legacy_constraint_present',
        'proposed_constraint_present',
        'compatibility_normalized',
        'ready_for_constraint_swap',
        'ready_for_swap',
    ]:
        print(f'{key}: {payload[key]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

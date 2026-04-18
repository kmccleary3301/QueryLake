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
from QueryLake.runtime.document_decomposition import backfill_document_decomposition


def _load_documents(database, *, document_ids: List[str], limit: int | None, offset: int = 0) -> List[document_raw]:
    stmt = select(document_raw).order_by(document_raw.creation_timestamp.desc())
    if document_ids:
        stmt = select(document_raw).where(document_raw.id.in_(document_ids))
    else:
        if offset:
            stmt = stmt.offset(int(offset))
        if limit is not None:
            stmt = stmt.limit(limit)
    return list(database.exec(stmt).all())


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backfill decomposition authority state for historical documents.")
    parser.add_argument("--document-id", action="append", default=[])
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    database, _ = initialize_database_engine(ensure_sparse_bootstrap=False)
    docs = _load_documents(
        database,
        document_ids=list(args.document_id or []),
        limit=None if args.document_id else int(args.limit),
        offset=0 if args.document_id else int(args.offset),
    )

    results = []
    for row in docs:
        results.append(backfill_document_decomposition(database, document_row=row, dry_run=bool(args.dry_run)))

    payload = {
        "documents_considered": len(results),
        "backfilled_count": sum(1 for row in results if row.get("action") == "backfilled"),
        "relinked_count": sum(1 for row in results if row.get("action") == "relinked_chunk_authority"),
        "planned_count": sum(1 for row in results if row.get("action") == "plan_backfill"),
        "skipped_count": sum(1 for row in results if str(row.get("action", "")).startswith("skip_")),
        "results": results,
    }

    if args.json:
        print(json.dumps(payload, indent=2))
        return 0

    print(f"documents_considered: {payload['documents_considered']}")
    print(f"backfilled_count: {payload['backfilled_count']}")
    print(f"relinked_count: {payload['relinked_count']}")
    print(f"planned_count: {payload['planned_count']}")
    print(f"skipped_count: {payload['skipped_count']}")
    for row in results:
        print(f"  - {row['document_id']}: action={row['action']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

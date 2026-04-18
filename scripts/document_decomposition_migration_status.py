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
from QueryLake.runtime.document_decomposition import (
    aggregate_decomposition_status,
    backfill_document_decomposition,
    summarize_many_documents,
)


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
    parser = argparse.ArgumentParser(description="Combined migration-state and dry-run backfill surface for document decomposition.")
    parser.add_argument("--document-id", action="append", default=[])
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args(argv)

    database, _ = initialize_database_engine(ensure_sparse_bootstrap=False)
    docs = _load_documents(
        database,
        document_ids=list(args.document_id or []),
        limit=None if args.document_id else int(args.limit),
        offset=0 if args.document_id else int(args.offset),
    )
    doc_ids = [row.id for row in docs]
    summaries = summarize_many_documents(database, document_ids=doc_ids)
    aggregate = aggregate_decomposition_status(summaries)
    dry_run = [backfill_document_decomposition(database, document_row=row, dry_run=True) for row in docs]
    payload = {
        "aggregate": aggregate,
        "dry_run": {
            "documents_considered": len(dry_run),
            "planned_count": sum(1 for row in dry_run if row.get("action") == "plan_backfill"),
            "relinked_count": sum(1 for row in dry_run if row.get("action") == "relinked_chunk_authority"),
            "skipped_count": sum(1 for row in dry_run if str(row.get("action", "")).startswith("skip_")),
        },
    }
    if not args.summary_only:
        payload["documents"] = summaries
        payload["dry_run"]["results"] = dry_run
    if args.json:
        print(json.dumps(payload, indent=2))
        return 0
    print(f"documents_scanned: {aggregate['documents_scanned']}")
    print(f"empty_documents: {aggregate['empty_documents']}")
    print(f"canonical_documents: {aggregate['canonical_documents']}")
    print(f"backfilled_documents: {aggregate['backfilled_documents']}")
    print(f"legacy_only_documents: {aggregate['legacy_only_documents']}")
    print(f"partial_documents: {aggregate['partial_documents']}")
    print(f"chunks_missing_authority_links_documents: {aggregate['chunks_missing_authority_links_documents']}")
    print(f"segments_missing_default_view_documents: {aggregate['segments_missing_default_view_documents']}")
    print(f"unknown_documents: {aggregate['unknown_documents']}")
    print(f"dry_run_planned_count: {payload['dry_run']['planned_count']}")
    print(f"dry_run_relinked_count: {payload['dry_run']['relinked_count']}")
    print(f"dry_run_skipped_count: {payload['dry_run']['skipped_count']}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

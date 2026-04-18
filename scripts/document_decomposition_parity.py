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
    compute_chunk_segment_parity,
    fetch_document_decomposition_state,
)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check chunk-to-segment parity for decomposed documents.")
    parser.add_argument("--document-id", action="append", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    database, _ = initialize_database_engine(ensure_sparse_bootstrap=False)
    docs = list(database.exec(select(document_raw).where(document_raw.id.in_(list(args.document_id)))).all())
    doc_by_id = {row.id: row for row in docs}
    results = []
    for document_id in list(args.document_id):
        if document_id not in doc_by_id:
            results.append({"document_id": document_id, "verdict": "missing_document"})
            continue
        state = fetch_document_decomposition_state(database, document_id=document_id)
        results.append(
            {
                "document_id": document_id,
                **compute_chunk_segment_parity(
                    chunk_rows=state["chunks"],
                    segment_rows=state["segments"],
                ),
            }
        )

    payload = {
        "documents_checked": len(results),
        "pass_count": sum(1 for row in results if row.get("verdict") == "pass"),
        "warn_count": sum(1 for row in results if row.get("verdict") == "warn"),
        "fail_count": sum(1 for row in results if row.get("verdict") == "fail"),
        "results": results,
    }

    if args.json:
        print(json.dumps(payload, indent=2))
        return 0

    print(f"documents_checked: {payload['documents_checked']}")
    print(f"pass_count: {payload['pass_count']}")
    print(f"warn_count: {payload['warn_count']}")
    print(f"fail_count: {payload['fail_count']}")
    for row in results:
        print(
            "  - "
            f"{row['document_id']}: verdict={row['verdict']} "
            f"chunk_count={row.get('chunk_count', 0)} "
            f"authority_linked_chunk_count={row.get('authority_linked_chunk_count', 0)} "
            f"text_match_count={row.get('text_match_count', 0)} "
            f"missing_authority={len(list(row.get('missing_authority_chunk_ids') or []))}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import text as sql_text

from QueryLake.database.create_db_session import initialize_database_engine

STOP = {
    "the", "and", "for", "with", "that", "this", "from", "are", "was", "were", "has", "have", "not", "you", "your",
    "document", "chunk", "querylake",
}


def terms(text: str) -> List[str]:
    out = []
    for t in re.findall(r"[A-Za-z][A-Za-z0-9_]{3,}", text.lower()):
        if t not in STOP and len(t) >= 4:
            out.append(t)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Build local decomposition parity eval queries from authority-linked chunk rows.")
    parser.add_argument("--limit", type=int, default=24)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    database, _ = initialize_database_engine(ensure_sparse_bootstrap=False)
    rows = list(database.exec(sql_text(
        """
        SELECT c.id, c.text, c.document_id, c.document_chunk_number
        FROM documentchunk c
        WHERE c.authority_segment_id IS NOT NULL AND length(c.text) > 80
        ORDER BY c.creation_timestamp DESC, c.id ASC
        LIMIT :limit
        """
    ).bindparams(limit=int(args.limit))).all())
    queries = []
    seen = set()
    query_classes = ["natural", "quote_like", "technical", "metadata_like", "ocr_noisy"]
    for idx, row in enumerate(rows):
        text = str(row.text or "")
        ts = terms(text)
        if len(ts) < 2:
            continue
        cls = query_classes[len(queries) % len(query_classes)]
        if cls == "quote_like":
            words = re.findall(r"[A-Za-z][A-Za-z0-9_]+", text)
            q = " ".join(words[: min(6, len(words))]) if words else " ".join(ts[:3])
        elif cls == "ocr_noisy":
            q = " ".join(ts[:2])
        else:
            q = " ".join(ts[:3])
        q = q.strip()
        if len(q) < 4 or q in seen:
            continue
        seen.add(q)
        queries.append({
            "query": q,
            "query_class": cls,
            "source": "authority_linked_documentchunk_sample",
            "source_document_id": row.document_id,
            "source_chunk_id": row.id,
            "source_chunk_number": row.document_chunk_number,
        })
        if len(queries) >= int(args.limit):
            break
    payload = {
        "schema_version": "document_decomposition_eval_queries_v1",
        "selection": "latest authority-linked chunk rows with sufficient text",
        "query_count": len(queries),
        "queries": queries,
    }
    Path(args.output).write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({"query_count": len(queries), "output": args.output}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

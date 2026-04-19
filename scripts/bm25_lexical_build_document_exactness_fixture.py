#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from sqlalchemy import text

from QueryLake.database.create_db_session import initialize_database_engine


def _load_collection_documents(collection_id: str) -> List[Dict[str, Any]]:
    database = initialize_database_engine(
        ensure_sparse_bootstrap=False,
        ensure_decomposition_bootstrap=False,
    )[0]
    rows = database.execute(
        text(
            """
            SELECT id, file_name, integrity_sha256, COALESCE(website_url, '') AS website_url
            FROM document_raw
            WHERE document_collection_id = :collection_id
            ORDER BY file_name
            """
        ),
        {"collection_id": str(collection_id)},
    ).all()
    return [
        {
            "id": str(row.id),
            "file_name": str(row.file_name or ""),
            "integrity_sha256": str(row.integrity_sha256 or ""),
            "website_url": str(row.website_url or ""),
        }
        for row in rows
    ]


def build_document_exactness_fixture(collection_id: str) -> Dict[str, Any]:
    documents = _load_collection_documents(collection_id)
    query_rows: List[Dict[str, Any]] = []
    qrel_rows: List[Dict[str, Any]] = []
    query_counter = 1
    for document in documents:
        file_id = str(document["id"])
        file_name = str(document["file_name"])
        integrity_sha256 = str(document["integrity_sha256"])
        base_payload = {
            "collection_ids": [str(collection_id)],
            "corpus_slices": ["document", "document_exactness"],
            "profile_id": "paradedb_postgres_gold_v1",
            "route": "search_bm25.document",
            "source_fixture": "seeded_targeted_document_exactness_v1",
        }
        query_specs = [
            (
                file_name,
                ["document_exact_file_name", "identifier_exact"],
                f"Exact file-name query for {file_name}",
            ),
            (
                f"\"{file_name}\"",
                ["document_exact_file_name", "navigational_exact"],
                f"Quoted navigational file-name query for {file_name}",
            ),
            (
                integrity_sha256,
                ["document_integrity_hash", "identifier_exact"],
                f"Exact integrity hash query for {file_name}",
            ),
        ]
        for query_text, query_slices, notes in query_specs:
            query_id = f"target_doc_exact_v1_{query_counter:04d}"
            query_counter += 1
            query_rows.append(
                {
                    **base_payload,
                    "notes": notes,
                    "query_id": query_id,
                    "query_slices": list(query_slices),
                    "query_text": query_text,
                }
            )
            qrel_rows.append(
                {
                    "authority_id": "",
                    "judged_by": "seeded_targeted_document_exactness_v1",
                    "notes": notes,
                    "query_id": query_id,
                    "relevance": 2,
                    "result_id": file_id,
                }
            )
    slice_manifest = {
        "document": {
            "description": "Document-table lexical evaluation slice.",
            "query_count": len(query_rows),
        },
        "document_exactness": {
            "description": "Targeted document-table exactness tranche.",
            "query_count": len(query_rows),
        },
        "document_exact_file_name": {
            "description": "Exact file-name and title-sensitive document queries.",
            "query_count": sum(1 for row in query_rows if "document_exact_file_name" in row["query_slices"]),
        },
        "document_integrity_hash": {
            "description": "Exact integrity hash queries on the document table.",
            "query_count": sum(1 for row in query_rows if "document_integrity_hash" in row["query_slices"]),
        },
        "identifier_exact": {
            "description": "Identifier-heavy exactness queries.",
            "query_count": sum(1 for row in query_rows if "identifier_exact" in row["query_slices"]),
        },
        "navigational_exact": {
            "description": "Quoted navigational document queries.",
            "query_count": sum(1 for row in query_rows if "navigational_exact" in row["query_slices"]),
        },
    }
    return {
        "collection_id": str(collection_id),
        "documents": documents,
        "query_rows": query_rows,
        "qrel_rows": qrel_rows,
        "slice_manifest": slice_manifest,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a targeted document-table exactness fixture from a live collection.")
    parser.add_argument("--collection-id", required=True)
    parser.add_argument("--query-set-output", required=True)
    parser.add_argument("--qrels-output", required=True)
    parser.add_argument("--slice-manifest-output", required=True)
    args = parser.parse_args()

    payload = build_document_exactness_fixture(str(args.collection_id))
    query_rows = payload["query_rows"]
    qrel_rows = payload["qrel_rows"]
    slice_manifest = payload["slice_manifest"]

    query_set_path = Path(args.query_set_output)
    qrels_path = Path(args.qrels_output)
    slice_manifest_path = Path(args.slice_manifest_output)
    query_set_path.parent.mkdir(parents=True, exist_ok=True)
    qrels_path.parent.mkdir(parents=True, exist_ok=True)
    slice_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    query_set_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in query_rows),
        encoding="utf-8",
    )
    qrels_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in qrel_rows),
        encoding="utf-8",
    )
    slice_manifest_path.write_text(
        json.dumps(slice_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "collection_id": str(args.collection_id),
                "document_count": len(payload["documents"]),
                "query_count": len(query_rows),
                "qrel_count": len(qrel_rows),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

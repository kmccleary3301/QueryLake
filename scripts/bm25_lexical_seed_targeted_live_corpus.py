#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import time
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Tuple
from hashlib import sha256

from sqlmodel import select

from QueryLake.api.collections import create_document_collection
from QueryLake.database import encryption
from QueryLake.database.create_db_session import initialize_database_engine
from QueryLake.database.sql_db_tables import DocumentChunk, document_collection, document_raw, document_zip_blob
from QueryLake.misc_functions.paradedb_query_builder import classify_lexical_query
from QueryLake.runtime.ingestion_lineage import create_upload_lineage_rows
from QueryLake.vector_database.embeddings import chunk_documents

CORPUS_DOCS: List[Tuple[str, str]] = [
    (
        "doc1.md",
        """# Demineralizer Overview

A demineralizer removes dissolved mineral ions from water using ion-exchange resins. It is commonly used for high-purity water applications.

## Key Steps
- Pre-filtration to remove suspended solids
- Cation and anion exchange
- Regeneration with acid/base
""",
    ),
    (
        "doc2.md",
        """# Flue Gas Analysis Notes

Flue gas analysis measures O2, CO2, CO, NOx, and SO2 to evaluate combustion efficiency and emissions.

## Indicators
- High O2 suggests excess air
- Elevated CO indicates incomplete combustion
""",
    ),
    (
        "doc3.md",
        """# Mineral Insulating Oil

Mineral insulating oil is used in transformers for dielectric strength and cooling.

## Maintenance
- Monitor moisture content
- Assess dielectric breakdown voltage
- Check acidity and oxidation
""",
    ),
    (
        "doc4.md",
        """# E2E Upload Check

This file confirms upload flow after encryption fix.

- item: 1
- item: 2
""",
    ),
    (
        "ql_e2e_doc1.md",
        """# QueryLake E2E Doc 1

This is a test document for E2E verification.
It includes a unique token: E2E_DOC_1_ALPHA.

- bullet a
- bullet b
""",
    ),
    (
        "ql_e2e_doc2.md",
        """# QueryLake E2E Doc 2

Second test document with token: E2E_DOC_2_BRAVO.
""",
    ),
    (
        "basf_sample.md",
        Path("docs_tmp/basf_sample.md").read_text(encoding="utf-8"),
    ),
    (
        "querylake_capture_seed.txt",
        """QueryLake Retrieval Demo

QueryLake is a self-hosted AI control plane for teams that need one runtime for ingestion, retrieval, and orchestration.

The retrieval surface should make three layers legible:
1. ingestion and parsing
2. search across collection-ready chunks
3. runtime and workflow execution

This seed document exists so the archived studio can show a populated collection page with a document list and BM25 search results.

Useful search phrases:
- tri-lane retrieval
- ingestion and parsing
- runtime and workflow execution
- collection-ready chunks
""",
    ),
]


QUERY_SPECS: List[Tuple[str, str, List[str], List[str]]] = [
    ("target_live_v3_0001", "basf_sample.md", ["basf_sample.md"], ["enterprise_doc", "identifier_exact"]),
    ("target_live_v3_0002", "querylake_capture_seed.txt", ["querylake_capture_seed.txt"], ["technical_doc", "identifier_exact"]),
    ("target_live_v3_0003", "E2E_DOC_1_ALPHA", ["ql_e2e_doc1.md"], ["technical_doc", "identifier_exact"]),
    ("target_live_v3_0004", "E2E_DOC_2_BRAVO", ["ql_e2e_doc2.md"], ["technical_doc", "identifier_exact"]),
    ("target_live_v3_0005", "doc1.md", ["doc1.md"], ["enterprise_doc", "identifier_exact"]),
    ("target_live_v3_0006", "ql_e2e_doc2.md", ["ql_e2e_doc2.md"], ["technical_doc", "identifier_exact"]),
    ("target_live_v3_0007", "flue gas", ["doc2.md"], ["technical_doc", "short_query"]),
    ("target_live_v3_0008", "acid base", ["doc1.md"], ["technical_doc", "short_query"]),
    ("target_live_v3_0009", "pure water", ["doc1.md"], ["enterprise_doc", "short_query"]),
    ("target_live_v3_0010", "o2 co2", ["doc2.md"], ["technical_doc", "short_query"]),
    ("target_live_v3_0011", "resin beds", ["doc1.md", "basf_sample.md"], ["enterprise_doc", "short_query"]),
    ("target_live_v3_0012", "pumps rinse", ["basf_sample.md"], ["enterprise_doc", "short_query"]),
    ("target_live_v3_0013", "flue gas analysis notes indicators", ["doc2.md"], ["technical_doc", "phrase_sensitive"]),
    ("target_live_v3_0014", "mineral insulating oil maintenance acidity oxidation", ["doc3.md"], ["technical_doc", "phrase_sensitive"]),
    ("target_live_v3_0015", "boiler water treatment deaeration oxygen scavengers", ["basf_sample.md"], ["enterprise_doc", "phrase_sensitive"]),
    ("target_live_v3_0016", "demineralizer water ion exchange resins", ["doc1.md", "basf_sample.md"], ["enterprise_doc", "phrase_sensitive"]),
    ("target_live_v3_0017", "runtime workflow execution collection ready chunks", ["querylake_capture_seed.txt"], ["technical_doc", "phrase_sensitive"]),
    ("target_live_v3_0018", "transformer dielectric strength cooling maintenance", ["doc3.md"], ["technical_doc", "phrase_sensitive"]),
    ("target_live_v3_0019", "upload flow after encryption fix", ["doc4.md"], ["technical_doc", "phrase_sensitive"]),
    ("target_live_v3_0020", "combustion efficiency emissions excess air", ["doc2.md"], ["technical_doc", "phrase_sensitive"]),
    ("target_live_v3_0021", "cation anion exchange regeneration acid base", ["doc1.md"], ["enterprise_doc", "phrase_sensitive"]),
    ("target_live_v3_0022", '"flue gas notes"', ["doc2.md"], ["technical_doc", "navigational_exact"]),
    ("target_live_v3_0023", '"acid base"', ["doc1.md"], ["technical_doc", "navigational_exact"]),
]


SLICE_MANIFEST = {
    "document_chunk": {"description": "Chunk-level lexical retrieval surfaces.", "primary_metric": "nDCG@10"},
    "enterprise_doc": {"description": "Enterprise/process document lexical queries.", "primary_metric": "nDCG@10"},
    "technical_doc": {"description": "Technical/process and system-document lexical queries.", "primary_metric": "nDCG@10"},
    "phrase_sensitive": {"description": "Queries where ordered or tight lexical dependence matters.", "primary_metric": "nDCG@10"},
    "short_query": {"description": "Very short head queries where exactness and fielding matter.", "primary_metric": "Success@1"},
    "navigational_exact": {"description": "Quoted title-like lexical queries.", "primary_metric": "Success@1"},
    "identifier_exact": {"description": "Exact token or filename seeking lexical queries.", "primary_metric": "Success@1"},
}


def _collection_by_name(database, name: str):
    return database.exec(select(document_collection).where(document_collection.name == name)).first()


def _doc_by_name(database, collection_id: str, file_name: str):
    return database.exec(
        select(document_raw).where(
            document_raw.document_collection_id == collection_id,
            document_raw.file_name == file_name,
        )
    ).first()


def _chunk_id_for_doc(database, document_id: str) -> str:
    row = database.exec(
        select(DocumentChunk.id)
        .where(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.document_chunk_number)
    ).first()
    assert row is not None, f"No chunks found for document {document_id}"
    return str(row)


async def _ensure_collection(database, auth: dict, name: str, public: bool) -> str:
    existing = _collection_by_name(database, name)
    if existing is not None:
        return str(existing.id)
    created = create_document_collection(
        database,
        auth,
        name=name,
        description="Seeded BM25 lexical research live corpus",
        public=public,
    )
    return str(created["hash_id"])


async def _ensure_docs(database, auth: dict, collection_id: str) -> Dict[str, str]:
    collection = database.exec(select(document_collection).where(document_collection.id == collection_id)).first()
    assert collection is not None, f"Collection {collection_id} not found"
    file_to_doc: Dict[str, str] = {}
    for file_name, content in CORPUS_DOCS:
        existing = _doc_by_name(database, collection_id, file_name)
        if existing is not None:
            file_to_doc[file_name] = str(existing.id)
            continue

        file_bytes = content.encode("utf-8")
        blob = BytesIO(file_bytes)
        blob.name = file_name
        encrypted_bytes = encryption.aes_encrypt_zip_file(key="", file_data=blob)
        zip_blob = document_zip_blob(
            file_count=1,
            size_bytes=len(encrypted_bytes),
            file_data=encrypted_bytes,
            document_collection_id=collection_id,
        )
        database.add(zip_blob)
        database.commit()
        database.refresh(zip_blob)

        new_doc = document_raw(
            file_name=file_name,
            integrity_sha256=sha256(file_bytes).hexdigest(),
            size_bytes=len(file_bytes),
            creation_timestamp=time.time(),
            public=True,
            finished_processing=1,
            blob_id=zip_blob.id,
            blob_dir="file",
            md={
                "file_name": file_name,
                "integrity_sha256": sha256(file_bytes).hexdigest(),
                "size_bytes": len(file_bytes),
                "seeded_live_corpus": True,
            },
            document_collection_id=collection_id,
        )
        collection.document_count += 1
        database.add(new_doc)
        database.add(collection)
        database.commit()
        database.refresh(new_doc)
        create_upload_lineage_rows(
            database,
            document_id=new_doc.id,
            created_by=str(collection.author_user_name or "lexical_research_seed"),
            content_hash=str(new_doc.integrity_sha256),
            storage_ref=f"{zip_blob.id}:{new_doc.blob_dir}",
            metadata={"file_name": file_name, "collection_id": collection_id, "seeded_live_corpus": True},
        )
        await chunk_documents(
            lambda _name: None,
            database,
            auth,
            [new_doc.id],
            [file_name],
            document_bytes_list=[file_bytes],
            create_embeddings=False,
            create_sparse_embeddings=False,
        )
        file_to_doc[file_name] = str(new_doc.id)
    return file_to_doc


def _write_jsonl(path: Path, rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


async def main() -> int:
    parser = argparse.ArgumentParser(description="Seed a targeted live lexical corpus and emit matching query/qrel fixtures.")
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--collection-name", default="BM25 Lexical Research Targeted Live Corpus")
    parser.add_argument("--public", action="store_true", default=True)
    parser.add_argument("--query-set-output", required=True)
    parser.add_argument("--qrels-output", required=True)
    parser.add_argument("--slice-manifest-output", required=True)
    parser.add_argument("--metadata-output", required=True)
    args = parser.parse_args()

    auth = {"api_key": args.api_key}
    database, _engine = initialize_database_engine(ensure_sparse_bootstrap=False, ensure_decomposition_bootstrap=False)
    collection_id = await _ensure_collection(database, auth, args.collection_name, bool(args.public))
    file_to_doc = await _ensure_docs(database, auth, collection_id)
    file_to_chunk = {file_name: _chunk_id_for_doc(database, doc_id) for file_name, doc_id in file_to_doc.items()}

    query_rows = []
    qrel_rows = []
    profile = {}
    for query_id, query_text, gold_files, query_slices in QUERY_SPECS:
        query_class = classify_lexical_query(query_text)
        profile[query_class] = profile.get(query_class, 0) + 1
        query_rows.append(
            {
                "query_id": query_id,
                "route": "search_bm25.document_chunk",
                "profile_id": "paradedb_postgres_gold_v1",
                "query_text": query_text,
                "query_slices": query_slices,
                "corpus_slices": ["document_chunk", "enterprise_doc", "technical_doc"],
                "collection_ids": [collection_id],
                "notes": f"Seeded targeted live corpus query (class={query_class})",
                "source_fixture": "seeded_targeted_live_corpus_v1",
            }
        )
        for gold_file in gold_files:
            qrel_rows.append(
                {
                    "query_id": query_id,
                    "result_id": file_to_chunk[gold_file],
                    "relevance": 2,
                    "authority_id": "",
                    "judged_by": "seeded_targeted_live_corpus_v1",
                    "notes": f"Gold chunk from seeded live corpus file {gold_file}",
                }
            )

    _write_jsonl(Path(args.query_set_output), query_rows)
    _write_jsonl(Path(args.qrels_output), qrel_rows)
    Path(args.slice_manifest_output).write_text(json.dumps(SLICE_MANIFEST, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    Path(args.metadata_output).write_text(
        json.dumps(
            {
                "collection_id": collection_id,
                "collection_name": args.collection_name,
                "file_to_doc": file_to_doc,
                "file_to_chunk": file_to_chunk,
                "query_class_counts": profile,
                "query_count": len(query_rows),
                "qrel_count": len(qrel_rows),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "collection_id": collection_id,
                "collection_name": args.collection_name,
                "query_count": len(query_rows),
                "qrel_count": len(qrel_rows),
                "query_class_counts": profile,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

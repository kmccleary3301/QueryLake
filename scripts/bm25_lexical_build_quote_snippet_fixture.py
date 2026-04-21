#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

PROFILE_ID = "paradedb_postgres_gold_v1"
COLLECTION_ID = "AfJDl3rb1N8YZOpbHVmq9oXROHPby6jF"

FILE_TO_CHUNK_ID: Dict[str, str] = {
    "doc1.md": "U0YwvjBfCbdMCfR5sRnwj0RAB5oXhKcy",
    "doc2.md": "5yVfC8dFqs9PV07byjjoRleBwDTkaibj",
    "doc3.md": "TqFU2N0VpXh0DQOe8me0CwyOcJ8mXUDI",
    "doc4.md": "AQoRVjynFwiAOrOD5UkC7qLZ7UHcFUpd",
    "ql_e2e_doc1.md": "iFw0RAt8IfVyRNFSoaDnWUhdUNTADpjr",
    "ql_e2e_doc2.md": "NEuKRoKnAdz21pMZ9Loexoay09q1FqyF",
    "basf_sample.md": "WR8gL96y8Ha2BZBzsC5QSUf9iGfviMUc",
    "querylake_capture_seed.txt": "BNoePRB60UlU8vuKijDDDeECstFmQeDp",
}

QUERY_SPECS: List[Tuple[str, str, List[str], List[str], str]] = [
    ("quote_snip_v1_0001", '"Flue gas analysis measures O2, CO2, CO, NOx, and SO2"', ["doc2.md"], ["quoted_exact", "technical_doc", "quote_snippet"], "Exact quoted sentence from flue gas doc."),
    ("quote_snip_v1_0002", "flue gas analysis measures o2 co2 co nox so2", ["doc2.md"], ["phrase_sensitive_unquoted", "technical_doc", "quote_snippet"], "Unquoted recovery of exact sentence from flue gas doc."),
    ("quote_snip_v1_0003", '"High O2 suggests excess air"', ["doc2.md"], ["quoted_exact", "technical_doc", "quote_snippet"], "Exact quoted bullet from flue gas doc."),
    ("quote_snip_v1_0004", "high o2 suggests excess air", ["doc2.md"], ["snippet_memory", "technical_doc", "quote_snippet"], "Remembered bullet text without quotes."),
    ("quote_snip_v1_0005", '"Elevated CO indicates incomplete combustion"', ["doc2.md"], ["quoted_exact", "technical_doc", "quote_snippet"], "Exact quoted bullet from flue gas doc."),
    ("quote_snip_v1_0006", "elevated co indicates incomplete combustion", ["doc2.md"], ["snippet_memory", "technical_doc", "quote_snippet"], "Remembered bullet text without quotes."),
    ("quote_snip_v1_0007", '"runtime and workflow execution"', ["querylake_capture_seed.txt"], ["quoted_exact", "technical_doc", "quote_snippet"], "Quoted phrase from retrieval demo seed."),
    ("quote_snip_v1_0008", "runtime and workflow execution", ["querylake_capture_seed.txt"], ["snippet_memory", "technical_doc", "quote_snippet"], "Unquoted remembered phrase from retrieval demo seed."),
    ("quote_snip_v1_0009", '"collection-ready chunks"', ["querylake_capture_seed.txt"], ["quoted_exact", "tweet_like_short_phrase", "quote_snippet"], "Quoted short phrase from retrieval demo seed."),
    ("quote_snip_v1_0010", "collection ready chunks", ["querylake_capture_seed.txt"], ["partial_phrase_recovery", "tweet_like_short_phrase", "quote_snippet"], "Hyphen-stripped remembered short phrase."),
    ("quote_snip_v1_0011", '"ingestion and parsing"', ["querylake_capture_seed.txt"], ["quoted_exact", "technical_doc", "quote_snippet"], "Quoted phrase from retrieval demo seed."),
    ("quote_snip_v1_0012", '"Cation and anion exchange"', ["doc1.md"], ["quoted_exact", "enterprise_doc", "quote_snippet"], "Exact quoted section content from demineralizer doc."),
    ("quote_snip_v1_0013", "cation and anion exchange", ["doc1.md"], ["phrase_sensitive_unquoted", "enterprise_doc", "quote_snippet"], "Unquoted recovery for demineralizer section content."),
    ("quote_snip_v1_0014", '"Regeneration with acid/base"', ["doc1.md"], ["quoted_exact", "enterprise_doc", "quote_snippet"], "Quoted slash-bearing phrase from demineralizer doc."),
    ("quote_snip_v1_0015", "regeneration with acid base", ["doc1.md"], ["partial_phrase_recovery", "enterprise_doc", "quote_snippet"], "Punctuation-normalized recovery of slash-bearing phrase."),
    ("quote_snip_v1_0016", '"Assess dielectric breakdown voltage"', ["doc3.md"], ["quoted_exact", "technical_doc", "quote_snippet"], "Quoted maintenance bullet from insulating oil doc."),
    ("quote_snip_v1_0017", "assess dielectric breakdown voltage", ["doc3.md"], ["snippet_memory", "technical_doc", "quote_snippet"], "Unquoted remembered maintenance bullet."),
    ("quote_snip_v1_0018", '"Check acidity and oxidation"', ["doc3.md"], ["quoted_exact", "technical_doc", "quote_snippet"], "Quoted maintenance bullet from insulating oil doc."),
    ("quote_snip_v1_0019", "check acidity oxidation", ["doc3.md"], ["partial_phrase_recovery", "technical_doc", "quote_snippet"], "Compressed remembered maintenance bullet."),
    ("quote_snip_v1_0020", '"ion exchange resins"', ["doc1.md", "basf_sample.md"], ["quoted_exact", "multi_target_phrase", "enterprise_doc", "quote_snippet"], "Exact quoted phrase that exists in multiple seeded enterprise documents."),
    ("quote_snip_v1_0021", "ion exchange resins", ["doc1.md", "basf_sample.md"], ["phrase_sensitive_unquoted", "multi_target_phrase", "enterprise_doc", "quote_snippet"], "Unquoted recovery for multi-target enterprise phrase."),
    ("quote_snip_v1_0022", '"oxygen scavengers, pH control"', ["basf_sample.md"], ["quoted_exact", "enterprise_doc", "quote_snippet"], "Quoted phrase with punctuation from BASF sample."),
    ("quote_snip_v1_0023", "oxygen scavengers ph control", ["basf_sample.md"], ["partial_phrase_recovery", "enterprise_doc", "quote_snippet"], "Punctuation-normalized recovery for BASF phrase."),
    ("quote_snip_v1_0024", '"This file confirms upload flow after encryption fix."', ["doc4.md"], ["quoted_exact", "technical_doc", "quote_snippet"], "Exact quoted sentence from upload check doc."),
    ("quote_snip_v1_0025", "upload flow after encryption fix", ["doc4.md"], ["snippet_memory", "technical_doc", "quote_snippet"], "Remembered sentence fragment from upload check doc."),
    ("quote_snip_v1_0026", '"Second test document with token: E2E_DOC_2_BRAVO."', ["ql_e2e_doc2.md"], ["quoted_exact", "technical_doc", "quote_snippet"], "Quoted sentence from E2E doc 2."),
    ("quote_snip_v1_0027", "second test document with token e2e doc 2 bravo", ["ql_e2e_doc2.md"], ["snippet_memory", "technical_doc", "quote_snippet"], "Unquoted remembered sentence from E2E doc 2."),
]

SLICE_MANIFEST = {
    "document_chunk": {"description": "Chunk-level lexical quote/snippet retrieval surface.", "primary_metric": "nDCG@10"},
    "quote_snippet": {"description": "Remembered phrase and exact quote retrieval slice.", "primary_metric": "nDCG@10"},
    "quoted_exact": {"description": "Explicitly quoted phrase queries that should prefer exact in-text hits.", "primary_metric": "Success@1"},
    "phrase_sensitive_unquoted": {"description": "Unquoted phrase-like queries where exact or tight in-text dependence likely matters.", "primary_metric": "nDCG@10"},
    "snippet_memory": {"description": "Remembered sentence-fragment queries without explicit quotes.", "primary_metric": "MRR@10"},
    "tweet_like_short_phrase": {"description": "Very short phrase lookups where exact phrase presence should dominate.", "primary_metric": "Success@1"},
    "partial_phrase_recovery": {"description": "Snippet recovery with punctuation, casing, or formatting drift.", "primary_metric": "nDCG@10"},
    "multi_target_phrase": {"description": "Phrase queries where the phrase exists in multiple relevant locations.", "primary_metric": "Recall@10"},
    "enterprise_doc": {"description": "Enterprise or process-document quote/snippet queries.", "primary_metric": "nDCG@10"},
    "technical_doc": {"description": "Technical/procedural quote/snippet queries.", "primary_metric": "nDCG@10"},
}


def _write_jsonl(path: Path, rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def build_query_rows() -> List[dict]:
    rows: List[dict] = []
    for query_id, query_text, files, query_slices, notes in QUERY_SPECS:
        corpus_slices = ["document_chunk"]
        if any(slice_name == "enterprise_doc" for slice_name in query_slices):
            corpus_slices.append("enterprise_doc")
        if any(slice_name == "technical_doc" for slice_name in query_slices):
            corpus_slices.append("technical_doc")
        rows.append(
            {
                "collection_ids": [COLLECTION_ID],
                "corpus_slices": corpus_slices,
                "notes": notes,
                "profile_id": PROFILE_ID,
                "query_id": query_id,
                "query_slices": query_slices,
                "query_text": query_text,
                "route": "search_bm25.document_chunk",
                "source_fixture": "quote_snippet_live_v1",
            }
        )
    return rows


def build_qrel_rows() -> List[dict]:
    rows: List[dict] = []
    for query_id, _query_text, files, _query_slices, notes in QUERY_SPECS:
        for file_name in files:
            rows.append(
                {
                    "authority_id": "",
                    "judged_by": "quote_snippet_live_v1",
                    "notes": f"{notes} Expected quote/snippet hit in {file_name}",
                    "query_id": query_id,
                    "relevance": 2,
                    "result_id": FILE_TO_CHUNK_ID[file_name],
                }
            )
    return rows


def main() -> int:
    base = Path("tests/fixtures/lexical_research")
    query_path = base / "query_set_live_quote_snippet_v1.jsonl"
    qrel_path = base / "qrels_live_quote_snippet_v1.jsonl"
    slice_manifest_path = base / "slice_manifest_live_quote_snippet_v1.json"

    query_rows = build_query_rows()
    qrel_rows = build_qrel_rows()

    _write_jsonl(query_path, query_rows)
    _write_jsonl(qrel_path, qrel_rows)
    slice_manifest_path.write_text(json.dumps(SLICE_MANIFEST, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "query_set": str(query_path),
        "qrels": str(qrel_path),
        "slice_manifest": str(slice_manifest_path),
        "query_count": len(query_rows),
        "qrel_count": len(qrel_rows),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

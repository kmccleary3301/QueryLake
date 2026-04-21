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
    "basf_sample.md": "WR8gL96y8Ha2BZBzsC5QSUf9iGfviMUc",
    "querylake_capture_seed.txt": "BNoePRB60UlU8vuKijDDDeECstFmQeDp",
}

QUERY_SPECS: List[Tuple[str, str, List[str], List[str], str]] = [
    (
        "quote_snip_neg_v1_0001",
        '"Regeneration with acid and base"',
        ["doc1.md"],
        ["negative_phrase_absent", "quoted_absent_fallback", "enterprise_doc", "quote_snippet_negative"],
        "Quoted phrase absent due to slash variation; fallback should still find doc1.",
    ),
    (
        "quote_snip_neg_v1_0002",
        '"Typical systems include cation and anion beds and regeneration with acid and caustic and conductivity monitoring"',
        ["basf_sample.md"],
        ["negative_phrase_absent", "quoted_absent_fallback", "enterprise_doc", "quote_snippet_negative"],
        "Absent exact punctuation-rich BASF sentence with and/caustic normalization drift.",
    ),
    (
        "quote_snip_neg_v1_0003",
        '"Key steps include filtration and softening and demineralization and deaeration and chemical dosing"',
        ["basf_sample.md"],
        ["negative_phrase_absent", "quoted_absent_fallback", "enterprise_doc", "quote_snippet_negative"],
        "Absent exact BASF sentence with punctuation removed and conjunction drift.",
    ),
    (
        "quote_snip_neg_v1_0004",
        '"The retrieval surface should make four layers legible"',
        ["querylake_capture_seed.txt"],
        ["negative_phrase_absent", "quoted_absent_fallback", "technical_doc", "quote_snippet_negative"],
        "Absent exact clause with a single token changed.",
    ),
    (
        "quote_snip_neg_v1_0005",
        '"This seed document exists so the archived studio can show a collection page with a list of documents and bm25 results"',
        ["querylake_capture_seed.txt"],
        ["negative_phrase_absent", "quoted_absent_fallback", "technical_doc", "quote_snippet_negative"],
        "Absent exact long sentence with light wording drift.",
    ),
    (
        "quote_snip_neg_v1_0006",
        '"Flue gas analysis measures oxygen and carbon dioxide and carbon monoxide and sulfur dioxide"',
        ["doc2.md"],
        ["negative_phrase_absent", "quoted_absent_fallback", "technical_doc", "quote_snippet_negative"],
        "Absent exact technical sentence with expanded chemical names.",
    ),
    (
        "quote_snip_neg_v1_0007",
        '"High oxygen suggests too much air"',
        ["doc2.md"],
        ["negative_phrase_absent", "quoted_absent_fallback", "technical_doc", "quote_snippet_negative"],
        "Absent exact short quote with wording drift.",
    ),
    (
        "quote_snip_neg_v1_0008",
        '"Assess dielectric breakdown and oxidation stability"',
        ["doc3.md"],
        ["negative_phrase_absent", "quoted_absent_fallback", "technical_doc", "quote_snippet_negative"],
        "Absent exact insulating-oil phrase with extra descriptor.",
    ),
    (
        "quote_snip_neg_v1_0009",
        '"This file confirms the upload flow after the encryption fix"',
        ["doc4.md"],
        ["negative_phrase_absent", "quoted_absent_fallback", "technical_doc", "quote_snippet_negative"],
        "Absent exact short sentence with inserted stopwords.",
    ),
    (
        "quote_snip_neg_v1_0010",
        '"oxygen scavengers and ph control"',
        ["basf_sample.md"],
        ["negative_phrase_absent", "quoted_absent_fallback", "enterprise_doc", "quote_snippet_negative"],
        "Absent exact short enterprise phrase with conjunction inserted.",
    ),
]

SLICE_MANIFEST = {
    "document_chunk": {"description": "Chunk-level lexical negative quote/snippet fallback surface.", "primary_metric": "nDCG@10"},
    "quote_snippet_negative": {"description": "Quoted phrase-absent fallback cases where lexical retrieval should still find the intended chunk.", "primary_metric": "nDCG@10"},
    "negative_phrase_absent": {"description": "Quoted phrases that do not occur verbatim in the corpus and require lexical fallback rather than exact hit recovery.", "primary_metric": "nDCG@10"},
    "quoted_absent_fallback": {"description": "Quoted queries with wording or punctuation drift that should still retrieve the intended chunk via fallback behavior.", "primary_metric": "MRR@10"},
    "enterprise_doc": {"description": "Enterprise/process document negative fallback queries.", "primary_metric": "nDCG@10"},
    "technical_doc": {"description": "Technical/procedural negative fallback queries.", "primary_metric": "nDCG@10"},
}


def _write_jsonl(path: Path, rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def build_query_rows() -> List[dict]:
    rows: List[dict] = []
    for query_id, query_text, files, query_slices, notes in QUERY_SPECS:
        corpus_slices = ["document_chunk"]
        if "enterprise_doc" in query_slices:
            corpus_slices.append("enterprise_doc")
        if "technical_doc" in query_slices:
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
                "source_fixture": "quote_snippet_negative_v1",
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
                    "judged_by": "quote_snippet_negative_v1",
                    "notes": f"{notes} Expected fallback hit in {file_name}",
                    "query_id": query_id,
                    "relevance": 2,
                    "result_id": FILE_TO_CHUNK_ID[file_name],
                }
            )
    return rows


def main() -> int:
    base = Path("tests/fixtures/lexical_research")
    query_path = base / "query_set_live_quote_snippet_negative_v1.jsonl"
    qrel_path = base / "qrels_live_quote_snippet_negative_v1.jsonl"
    slice_manifest_path = base / "slice_manifest_live_quote_snippet_negative_v1.json"

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

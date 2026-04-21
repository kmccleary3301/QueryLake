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
        "quote_snip_chal_v1_0001",
        '"Regeneration with acid/base"',
        ["doc1.md"],
        ["quoted_exact", "punctuation_sensitive", "enterprise_doc", "quote_snippet_challenge"],
        "Known slash-sensitive exact phrase from doc1.",
    ),
    (
        "quote_snip_chal_v1_0002",
        '"Typical systems include cation and anion beds, regeneration with acid/caustic, and conductivity monitoring."',
        ["basf_sample.md"],
        ["quoted_exact", "punctuation_sensitive", "enterprise_doc", "quote_snippet_challenge"],
        "Long punctuation-heavy exact sentence from BASF sample.",
    ),
    (
        "quote_snip_chal_v1_0003",
        "typical systems include cation and anion beds regeneration with acid caustic and conductivity monitoring",
        ["basf_sample.md"],
        ["phrase_sensitive_unquoted", "punctuation_normalized", "enterprise_doc", "quote_snippet_challenge"],
        "Punctuation-normalized recovery of long BASF sentence.",
    ),
    (
        "quote_snip_chal_v1_0004",
        '"Key steps include filtration, softening, demineralization, deaeration, and chemical dosing (oxygen scavengers, pH control)."',
        ["basf_sample.md"],
        ["quoted_exact", "punctuation_sensitive", "enterprise_doc", "quote_snippet_challenge"],
        "Exact sentence with parentheses and comma punctuation.",
    ),
    (
        "quote_snip_chal_v1_0005",
        "key steps include filtration softening demineralization deaeration and chemical dosing oxygen scavengers ph control",
        ["basf_sample.md"],
        ["phrase_sensitive_unquoted", "punctuation_normalized", "enterprise_doc", "quote_snippet_challenge"],
        "Punctuation-normalized recovery of parenthesized BASF sentence.",
    ),
    (
        "quote_snip_chal_v1_0006",
        '"Demineralizers remove mineral ions (calcium, magnesium, sodium) from water using ion exchange resins."',
        ["basf_sample.md"],
        ["quoted_exact", "punctuation_sensitive", "enterprise_doc", "quote_snippet_challenge"],
        "Exact sentence with parenthesized list from BASF sample.",
    ),
    (
        "quote_snip_chal_v1_0007",
        '"The retrieval surface should make three layers legible:"',
        ["querylake_capture_seed.txt"],
        ["quoted_exact", "punctuation_sensitive", "technical_doc", "quote_snippet_challenge"],
        "Exact quoted clause ending with colon from retrieval seed.",
    ),
    (
        "quote_snip_chal_v1_0008",
        "the retrieval surface should make three layers legible",
        ["querylake_capture_seed.txt"],
        ["snippet_memory", "punctuation_normalized", "technical_doc", "quote_snippet_challenge"],
        "Colon-stripped remembered clause from retrieval seed.",
    ),
    (
        "quote_snip_chal_v1_0009",
        '"This seed document exists so the archived studio can show a populated collection page with a document list and BM25 search results."',
        ["querylake_capture_seed.txt"],
        ["quoted_exact", "technical_doc", "quote_snippet_challenge"],
        "Long exact sentence from retrieval demo seed.",
    ),
    (
        "quote_snip_chal_v1_0010",
        '"Flue gas analysis measures O2, CO2, CO, NOx, and SO2 to evaluate combustion efficiency and emissions."',
        ["doc2.md"],
        ["quoted_exact", "punctuation_sensitive", "technical_doc", "quote_snippet_challenge"],
        "Long exact sentence with punctuation from flue gas doc.",
    ),
    (
        "quote_snip_chal_v1_0011",
        '"Mineral insulating oil is used in transformers for dielectric strength and cooling."',
        ["doc3.md"],
        ["quoted_exact", "technical_doc", "quote_snippet_challenge"],
        "Long exact sentence from insulating oil doc.",
    ),
    (
        "quote_snip_chal_v1_0012",
        '"This file confirms upload flow after encryption fix."',
        ["doc4.md"],
        ["quoted_exact", "technical_doc", "quote_snippet_challenge"],
        "Exact sentence from upload check doc.",
    ),
]

SLICE_MANIFEST = {
    "document_chunk": {"description": "Chunk-level lexical quote/snippet challenge surface.", "primary_metric": "nDCG@10"},
    "quote_snippet_challenge": {"description": "Harder phrase-sensitive quote/snippet slice with punctuation and formatting stressors.", "primary_metric": "nDCG@10"},
    "quoted_exact": {"description": "Explicit quoted phrase queries that should prefer exact in-text hits.", "primary_metric": "Success@1"},
    "phrase_sensitive_unquoted": {"description": "Unquoted phrase-like queries where exact or tight in-text dependence likely matters.", "primary_metric": "nDCG@10"},
    "snippet_memory": {"description": "Remembered sentence-fragment queries without explicit quotes.", "primary_metric": "MRR@10"},
    "punctuation_sensitive": {"description": "Queries where punctuation, slashes, commas, colons, or parentheses may materially affect lexical behavior.", "primary_metric": "Success@1"},
    "punctuation_normalized": {"description": "Recovered phrase queries with punctuation stripped or normalized.", "primary_metric": "nDCG@10"},
    "enterprise_doc": {"description": "Enterprise/process document challenge queries.", "primary_metric": "nDCG@10"},
    "technical_doc": {"description": "Technical/procedural challenge queries.", "primary_metric": "nDCG@10"},
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
                "source_fixture": "quote_snippet_challenge_v1",
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
                    "judged_by": "quote_snippet_challenge_v1",
                    "notes": f"{notes} Expected challenge hit in {file_name}",
                    "query_id": query_id,
                    "relevance": 2,
                    "result_id": FILE_TO_CHUNK_ID[file_name],
                }
            )
    return rows


def main() -> int:
    base = Path("tests/fixtures/lexical_research")
    query_path = base / "query_set_live_quote_snippet_challenge_v1.jsonl"
    qrel_path = base / "qrels_live_quote_snippet_challenge_v1.jsonl"
    slice_manifest_path = base / "slice_manifest_live_quote_snippet_challenge_v1.json"

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

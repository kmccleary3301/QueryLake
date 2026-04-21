from __future__ import annotations

from scripts.bm25_lexical_build_quote_snippet_challenge_fixture import (
    QUERY_SPECS,
    SLICE_MANIFEST,
    build_qrel_rows,
    build_query_rows,
)


def test_quote_snippet_challenge_fixture_builder_counts_and_shape() -> None:
    query_rows = build_query_rows()
    qrel_rows = build_qrel_rows()

    assert len(query_rows) == len(QUERY_SPECS) == 12
    assert len(qrel_rows) == 12
    assert all(row["route"] == "search_bm25.document_chunk" for row in query_rows)
    assert all(row["source_fixture"] == "quote_snippet_challenge_v1" for row in query_rows)
    assert "quoted_exact" in SLICE_MANIFEST
    assert "punctuation_sensitive" in SLICE_MANIFEST
    assert "punctuation_normalized" in SLICE_MANIFEST
    assert "quote_snippet_challenge" in SLICE_MANIFEST


def test_quote_snippet_challenge_fixture_builder_includes_known_shared_miss_cases() -> None:
    query_rows = build_query_rows()
    qrel_rows = build_qrel_rows()

    slash_case = next(row for row in query_rows if row["query_id"] == "quote_snip_chal_v1_0001")
    long_case = next(row for row in query_rows if row["query_id"] == "quote_snip_chal_v1_0002")

    assert slash_case["query_text"] == '"Regeneration with acid/base"'
    assert long_case["query_text"].startswith('"Typical systems include cation and anion beds')

    slash_qrels = [row for row in qrel_rows if row["query_id"] == "quote_snip_chal_v1_0001"]
    long_qrels = [row for row in qrel_rows if row["query_id"] == "quote_snip_chal_v1_0002"]
    assert len(slash_qrels) == 1
    assert len(long_qrels) == 1

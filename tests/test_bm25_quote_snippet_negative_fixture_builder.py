from __future__ import annotations

from scripts.bm25_lexical_build_quote_snippet_negative_fixture import (
    QUERY_SPECS,
    SLICE_MANIFEST,
    build_qrel_rows,
    build_query_rows,
)


def test_quote_snippet_negative_fixture_builder_counts_and_shape() -> None:
    query_rows = build_query_rows()
    qrel_rows = build_qrel_rows()

    assert len(query_rows) == len(QUERY_SPECS) == 10
    assert len(qrel_rows) == 10
    assert all(row["route"] == "search_bm25.document_chunk" for row in query_rows)
    assert all(row["source_fixture"] == "quote_snippet_negative_v1" for row in query_rows)
    assert "negative_phrase_absent" in SLICE_MANIFEST
    assert "quoted_absent_fallback" in SLICE_MANIFEST


def test_quote_snippet_negative_fixture_builder_contains_absent_quote_cases() -> None:
    query_rows = build_query_rows()

    q1 = next(row for row in query_rows if row["query_id"] == "quote_snip_neg_v1_0001")
    q2 = next(row for row in query_rows if row["query_id"] == "quote_snip_neg_v1_0002")

    assert q1["query_text"] == '"Regeneration with acid and base"'
    assert q2["query_text"].startswith('"Typical systems include cation and anion beds and regeneration')
    assert "negative_phrase_absent" in q1["query_slices"]
    assert "quoted_absent_fallback" in q2["query_slices"]

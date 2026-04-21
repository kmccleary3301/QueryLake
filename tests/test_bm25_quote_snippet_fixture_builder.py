from __future__ import annotations

from scripts.bm25_lexical_build_quote_snippet_fixture import (
    QUERY_SPECS,
    SLICE_MANIFEST,
    build_qrel_rows,
    build_query_rows,
)


def test_quote_snippet_fixture_builder_counts_and_shape() -> None:
    query_rows = build_query_rows()
    qrel_rows = build_qrel_rows()

    assert len(query_rows) == len(QUERY_SPECS) == 27
    assert len(qrel_rows) == 29
    assert all(row["route"] == "search_bm25.document_chunk" for row in query_rows)
    assert all(row["source_fixture"] == "quote_snippet_live_v1" for row in query_rows)
    assert "quoted_exact" in SLICE_MANIFEST
    assert "snippet_memory" in SLICE_MANIFEST
    assert "partial_phrase_recovery" in SLICE_MANIFEST


def test_quote_snippet_fixture_builder_contains_multi_target_phrase_case() -> None:
    query_rows = build_query_rows()
    qrel_rows = build_qrel_rows()

    multi_target_query = next(row for row in query_rows if row["query_id"] == "quote_snip_v1_0020")
    assert "multi_target_phrase" in multi_target_query["query_slices"]

    multi_target_qrels = [row for row in qrel_rows if row["query_id"] == "quote_snip_v1_0020"]
    assert len(multi_target_qrels) == 2
    assert {row["result_id"] for row in multi_target_qrels}

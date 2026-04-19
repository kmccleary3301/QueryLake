from QueryLake.canon.runtime import build_shadow_diff_summary
from QueryLake.typing.retrieval_primitives import RetrievalCandidate


def _candidate(content_id: str) -> RetrievalCandidate:
    return RetrievalCandidate(content_id=content_id)


def test_shadow_diff_summary_detects_exact_match():
    payload = build_shadow_diff_summary(
        route_family="search_bm25.document_chunk",
        profile_id="paradedb_postgres_gold_v1",
        execution_mode="canon_shadow",
        legacy_candidates=[_candidate("a"), _candidate("b")],
        canon_candidates=[_candidate("a"), _candidate("b")],
        top_k_requested=2,
        legacy_plan_id="legacy-plan",
        canon_graph_id="graph-123",
    )

    assert payload["divergence_class"] == "exact_match"
    assert payload["overlap_at_k"] == 2
    assert payload["legacy_only_ids"] == []
    assert payload["canon_only_ids"] == []


def test_shadow_diff_summary_detects_candidate_set_delta():
    payload = build_shadow_diff_summary(
        route_family="search_hybrid.document_chunk",
        profile_id="paradedb_postgres_gold_v1",
        execution_mode="canon_shadow",
        legacy_candidates=[_candidate("a"), _candidate("b")],
        canon_candidates=[_candidate("a"), _candidate("c")],
        top_k_requested=2,
        legacy_plan_id="legacy-plan",
        canon_graph_id="graph-456",
        trace_summary_ref="trace-1",
    )

    assert payload["divergence_class"] == "candidate_set_delta"
    assert payload["overlap_at_k"] == 1
    assert payload["legacy_only_ids"] == ["b"]
    assert payload["canon_only_ids"] == ["c"]
    assert payload["trace_summary_ref"] == "trace-1"

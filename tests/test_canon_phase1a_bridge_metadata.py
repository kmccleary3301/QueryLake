from QueryLake.canon.runtime import build_canon_bridge_metadata
from QueryLake.runtime.retrieval_pipeline_runtime import default_pipeline_for_route


def test_canon_bridge_metadata_for_hybrid_route_contains_graph_and_trace_fields():
    pipeline = default_pipeline_for_route("search_hybrid")
    assert pipeline is not None

    payload = build_canon_bridge_metadata(
        route="search_hybrid.document_chunk",
        pipeline=pipeline,
        options={"explain_plan": True},
    )

    assert payload["available"] is True
    assert payload["graph_name"].startswith("canon.retrieval.search_hybrid.document_chunk")
    assert payload["node_count"] == 4
    assert payload["trace_summary"]["retention_class"] == "summary_plus_detail"
    assert payload["replay_summary"]["available"] is False
    assert payload["stage_nodes"][0]["primitive_id"] == "BM25RetrieverParadeDB"
    assert payload["profile_lowering"]["route_id"] == "search_hybrid.document_chunk"
    assert payload["profile_lowering"]["executor_id"]


def test_canon_bridge_metadata_can_request_debug_replay_summary():
    pipeline = default_pipeline_for_route("search_bm25.document_chunk")
    assert pipeline is not None

    payload = build_canon_bridge_metadata(
        route="search_bm25.document_chunk",
        pipeline=pipeline,
        options={"canon_debug_replay": True},
    )

    assert payload["replay_summary"]["available"] is True
    assert payload["replay_summary"]["retention_class"] == "debug_replay"
    assert payload["replay_summary"]["replay_guarantee_class"] == "analysis_only"
    assert payload["profile_lowering"]["representation_scope_id"] == "document_chunk"

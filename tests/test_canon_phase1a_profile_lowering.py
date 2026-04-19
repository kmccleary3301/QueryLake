from QueryLake.canon.compiler import build_profile_lowering_snapshot


def test_profile_lowering_snapshot_for_hybrid_route_contains_executor_and_scope():
    payload = build_profile_lowering_snapshot(route="search_hybrid.document_chunk")

    assert payload["route_id"] == "search_hybrid.document_chunk"
    assert payload["executor_id"]
    assert payload["support_state"] in {"supported", "degraded", "unsupported", "planned"}
    assert payload["representation_scope_id"] == "document_chunk"
    assert isinstance(payload["backend_stack"], dict)
    assert "authority" in payload["backend_stack"]


def test_profile_lowering_snapshot_for_file_chunks_route_contains_projection_descriptor():
    payload = build_profile_lowering_snapshot(route="search_file_chunks")

    assert payload["route_id"] == "search_file_chunks"
    assert "file_chunk_lexical_projection_v1" in payload["projection_descriptors"]
    assert payload["representation_scope_id"] == "file_chunk"

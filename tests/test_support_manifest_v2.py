from QueryLake.runtime.support_manifest_v2 import (
    build_representation_scope_registry_payload,
    build_route_support_manifest_entries_v2,
    get_representation_scope,
)


def test_route_representation_scope_registry_maps_current_routes():
    hybrid_scope = get_representation_scope("search_hybrid.document_chunk")
    file_scope = get_representation_scope("search_file_chunks")
    graph_scope = get_representation_scope("retrieval.graph.traversal")

    assert hybrid_scope.scope_id == "document_chunk"
    assert hybrid_scope.compatibility_projection is True
    assert file_scope.scope_id == "file_chunk"
    assert graph_scope.scope_id == "document_segment_graph"


def test_build_route_support_manifest_entries_v2_enriches_rows():
    payload = build_route_support_manifest_entries_v2(
        [
            {
                "route_id": "search_bm25.document_chunk",
                "declared_state": "degraded",
                "declared_executable": True,
                "declared_optional": False,
                "notes": "test note",
            }
        ]
    )
    assert len(payload) == 1
    row = payload[0]
    assert row["representation_scope"]["scope_id"] == "document_chunk"
    assert row["capability_dependencies"] == ["retrieval.lexical.bm25"]
    assert row["support_state"] == "degraded"
    assert row["notes"] == "test note"


def test_representation_scope_registry_payload_exposes_known_scopes():
    payload = build_representation_scope_registry_payload()
    assert set(payload) >= {"document_chunk", "file_chunk", "document_segment_graph"}
    assert payload["document_chunk"]["authority_model"] == "document_segment"

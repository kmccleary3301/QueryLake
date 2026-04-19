from __future__ import annotations

from QueryLake.canon.package import (
    build_route_graph_package_bundle,
    load_graph_package_bundle,
    persist_graph_package_bundle,
)


def test_route_graph_package_bundle_contains_graph_and_transition_bundle():
    import os
    os.environ["QUERYLAKE_SEARCH_INDEX_NAMESPACE"] = "ql"
    os.environ["QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS"] = "1024"
    payload = build_route_graph_package_bundle(
        route="search_bm25.document_chunk",
        package_revision="rev-1",
    )

    assert payload["schema_version"] == "canon_graph_package_bundle_v1"
    assert payload["route_id"] == "search_bm25.document_chunk"
    assert payload["graph"]["node_count"] >= 1
    assert payload["graph"]["graph_id"].startswith("graph-")
    assert payload["package_id"].startswith("canon-package-")
    assert payload["search_plane_a_transition"]["schema_version"] == "canon_phase1a_search_plane_a_transition_bundle_v1"


def test_graph_package_bundle_persists_and_loads(tmp_path):
    import os
    os.environ["QUERYLAKE_SEARCH_INDEX_NAMESPACE"] = "ql"
    os.environ["QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS"] = "1024"
    payload = build_route_graph_package_bundle(
        route="search_file_chunks",
        package_revision="rev-2",
        profile_targets=["aws_aurora_pg_opensearch_v1"],
    )
    persisted = persist_graph_package_bundle(bundle=payload, output_dir=tmp_path)
    loaded = load_graph_package_bundle(persisted["path"])

    assert loaded["package_id"] == payload["package_id"]
    assert loaded["graph"]["graph_id"] == payload["graph"]["graph_id"]
    assert loaded["profile_targets"] == ["aws_aurora_pg_opensearch_v1"]

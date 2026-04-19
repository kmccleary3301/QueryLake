from __future__ import annotations

from QueryLake.canon.control.pointer_registry import save_pointer_registry
from QueryLake.canon.package import build_phase1a_package_set_bundle, load_graph_package_registry
from QueryLake.canon.runtime.search_plane_a_matrix import build_search_plane_a_lowering_matrix


def test_search_plane_a_lowering_matrix_spans_source_and_target_profiles(tmp_path):
    import os

    os.environ["QUERYLAKE_SEARCH_INDEX_NAMESPACE"] = "ql"
    os.environ["QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS"] = "1024"

    registry_path = tmp_path / "package_registry.json"
    build_phase1a_package_set_bundle(
        routes=[
            "search_bm25.document_chunk",
            "search_hybrid.document_chunk",
            "search_file_chunks",
        ],
        package_revision="rev-matrix",
        output_dir=tmp_path / "packages",
        registry_path=registry_path,
        route_options={"search_hybrid.document_chunk": {"disable_sparse": True}},
    )
    package_registry = load_graph_package_registry(registry_path)
    bindings = {}
    for package in package_registry["packages"]:
        bindings[package["route_id"]] = {
            "package_id": package["package_id"],
            "package_revision": package["package_revision"],
            "graph_id": package["graph_id"],
        }
    bm25_pkg = next(pkg for pkg in package_registry["packages"] if pkg["route_id"] == "search_bm25.document_chunk")
    save_pointer_registry(
        {
            "schema_version": "canon_pointer_registry_v1",
            "generated_at": "2026-04-19T00:00:00+00:00",
            "shadow_pointer": {
                "pointer_id": "ptr-shadow",
                "graph_id": bm25_pkg["graph_id"],
                "package_revision": bm25_pkg["package_revision"],
                "profile_id": "aws_aurora_pg_opensearch_v1",
                "route_ids": list(bindings.keys()),
                "mode": "shadow",
                "metadata": {"package_bindings": bindings},
            },
            "candidate_primary_pointer": None,
            "primary_pointer": None,
            "history": [],
        },
        tmp_path / "pointer_registry.json",
    )

    payload = build_search_plane_a_lowering_matrix(
        routes=list(bindings.keys()),
        profile_ids=["aws_aurora_pg_opensearch_v1", "planetscale_opensearch_v1"],
        package_registry_path=registry_path,
        pointer_registry_path=tmp_path / "pointer_registry.json",
    )

    counts = payload["summary"]["execution_mode_counts"]
    assert payload["schema_version"] == "canon_phase1a_search_plane_a_lowering_matrix_v1"
    assert payload["summary"]["row_count"] == 6
    assert counts["legacy_route_executor_passthrough"] == 3
    assert counts["planned_profile_shadow_only"] == 3

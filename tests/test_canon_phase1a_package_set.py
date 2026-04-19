from __future__ import annotations

from QueryLake.canon.package import build_phase1a_package_set_bundle


def test_phase1a_package_set_bundle_builds_bounded_routes(tmp_path):
    import os

    os.environ["QUERYLAKE_SEARCH_INDEX_NAMESPACE"] = "ql"
    os.environ["QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS"] = "1024"

    payload = build_phase1a_package_set_bundle(
        routes=[
            "search_bm25.document_chunk",
            "search_hybrid.document_chunk",
            "search_file_chunks",
        ],
        package_revision="rev-set",
        output_dir=tmp_path / "packages",
        registry_path=tmp_path / "package_registry.json",
        route_options={"search_hybrid.document_chunk": {"disable_sparse": True}},
    )

    assert payload["schema_version"] == "canon_phase1a_package_set_bundle_v1"
    assert payload["registry_summary"]["package_count"] == 3
    assert payload["registry_summary"]["route_count"] == 3
    hybrid_row = next(row for row in payload["route_rows"] if row["route_id"] == "search_hybrid.document_chunk")
    assert hybrid_row["compile_options"]["disable_sparse"] is True

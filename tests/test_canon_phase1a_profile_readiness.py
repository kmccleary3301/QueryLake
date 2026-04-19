from __future__ import annotations

from QueryLake.canon.runtime import (
    build_phase1a_profile_readiness_bundle,
    build_phase1a_projection_writer_matrix,
    build_phase1a_search_plane_a_transition_bundle,
)
from QueryLake.runtime.db_compat import get_deployment_profile
from QueryLake.runtime.projection_refresh import mark_projection_build_ready


def test_phase1a_projection_writer_matrix_uses_real_writer_and_refresh_contracts(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")

    payload = build_phase1a_projection_writer_matrix(
        profile=get_deployment_profile("aws_aurora_pg_opensearch_v1"),
        projection_ids=[
            "document_chunk_lexical_projection_v1",
            "segment_dense_projection_v1",
        ],
        metadata_store_path=str(tmp_path / "projection_store.json"),
    )

    assert payload["schema_version"] == "canon_phase1a_projection_writer_matrix_v1"
    assert payload["summary"]["projection_count"] == 2
    assert payload["summary"]["writer_executable_count"] == 2
    assert payload["summary"]["refresh_rebuild_mode_count"] == 2
    assert "projection_writers_resolve_for_declared_targets" in payload["recommendations"]
    lexical_row = next(row for row in payload["rows"] if row["projection_id"] == "document_chunk_lexical_projection_v1")
    assert lexical_row["writer_resolution"]["backend"] == "opensearch"
    assert lexical_row["refresh_plan"]["mode"] == "rebuild"
    assert lexical_row["projection_target"]["authority_model"] == "document_chunk_compatibility"


def test_phase1a_profile_readiness_bundle_reflects_runtime_ready_split_stack(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")
    metadata_path = tmp_path / "projection_store.json"

    for projection_id, lane_family in [
        ("document_chunk_lexical_projection_v1", "lexical"),
        ("document_chunk_dense_projection_v1", "dense"),
        ("file_chunk_lexical_projection_v1", "lexical"),
    ]:
        mark_projection_build_ready(
            projection_id=projection_id,
            projection_version="v1",
            profile_id="aws_aurora_pg_opensearch_v1",
            lane_family=lane_family,
            target_backend="opensearch",
            build_revision=f"{projection_id}:ready",
            path=str(metadata_path),
        )

    payload = build_phase1a_profile_readiness_bundle(
        profile_id="aws_aurora_pg_opensearch_v1",
        routes=[
            "search_bm25.document_chunk",
            "search_file_chunks",
            "search_hybrid.document_chunk",
        ],
        metadata_store_path=str(metadata_path),
    )

    assert payload["schema_version"] == "canon_phase1a_profile_readiness_bundle_v1"
    assert payload["summary"]["route_count"] == 3
    assert payload["summary"]["compile_available_count"] == 3
    assert payload["summary"]["runtime_ready_count"] == 3
    assert payload["summary"]["declared_executable_routes_runtime_ready"] is True
    assert payload["summary"]["projection_writer_executable_count"] >= 3
    assert payload["bringup"]["summary"]["route_runtime_ready"] is True
    assert "profile_runtime_ready_for_declared_phase1a_routes" in payload["recommendations"]


def test_phase1a_search_plane_a_transition_bundle_surfaces_target_gaps(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")
    metadata_path = tmp_path / "projection_store.json"
    mark_projection_build_ready(
        projection_id="document_chunk_lexical_projection_v1",
        projection_version="v1",
        profile_id="aws_aurora_pg_opensearch_v1",
        lane_family="lexical",
        target_backend="opensearch",
        build_revision="doclex:ready",
        path=str(metadata_path),
    )

    payload = build_phase1a_search_plane_a_transition_bundle(
        routes=["search_bm25.document_chunk", "search_file_chunks"],
        source_metadata_store_path=str(metadata_path),
    )

    assert payload["schema_version"] == "canon_phase1a_search_plane_a_transition_bundle_v1"
    assert any(delta["target_support_state"] == "planned" for delta in payload["route_deltas"])
    assert "source_opensearch_stack_covers_bounded_phase1a_routes" in payload["recommendations"]
    assert "target_planetscale_opensearch_requires_runtime_lowering_before_cutover" in payload["recommendations"]
    assert "target_planetscale_opensearch_requires_projection_writer_implementation" in payload["recommendations"]

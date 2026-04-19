from __future__ import annotations

from QueryLake.canon.materialization import (
    build_phase1a_materialization_bundle,
    persist_phase1a_materialization_bundle,
)


def test_phase1a_materialization_bundle_builds_rebuild_plans(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")
    bundle = build_phase1a_materialization_bundle(
        profile_id="aws_aurora_pg_opensearch_v1",
        projection_ids=["document_chunk_lexical_projection_v1", "document_chunk_dense_projection_v1"],
        metadata_store_path=str(tmp_path / "projection_store.json"),
    )

    assert bundle["schema_version"] == "canon_phase1a_materialization_bundle_v1"
    assert bundle["summary"]["plan_count"] == 2
    assert bundle["summary"]["rebuild_plan_count"] == 2
    assert "materialization_bundle_ready_for_bootstrap_execution" in bundle["recommendations"]


def test_phase1a_materialization_bundle_persists(tmp_path):
    bundle = {
        "schema_version": "canon_phase1a_materialization_bundle_v1",
        "profile": {"id": "aws_aurora_pg_opensearch_v1"},
        "summary": {"plan_count": 1},
    }
    path = persist_phase1a_materialization_bundle(bundle=bundle, output_path=tmp_path / "bundle.json")
    assert str(path).endswith("bundle.json")

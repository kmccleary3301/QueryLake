from __future__ import annotations

from QueryLake.canon.control.pointer_registry import save_pointer_registry
from QueryLake.canon.control.authority_control_registry import apply_authority_control_bootstrap
from QueryLake.canon.control.target_profile_promotion import build_target_profile_promotion_bundle
from QueryLake.canon.package import build_phase1a_package_set_bundle, load_graph_package_registry
from QueryLake.canon.runtime.authority_control_bootstrap import build_authority_control_bootstrap_bundle
from QueryLake.canon.runtime import (
    build_shadow_execution_report,
    build_shadow_replay_bundle,
    build_shadow_trace_export,
    persist_shadow_execution_report,
    persist_shadow_replay_bundle,
    persist_shadow_trace_export,
)
from QueryLake.runtime.projection_refresh import mark_projection_build_ready
from QueryLake.typing.retrieval_primitives import (
    RetrievalCandidate,
    RetrievalExecutionResult,
    RetrievalPipelineSpec,
    RetrievalPipelineStage,
    RetrievalRequest,
)


def _persist_exact_match_report(tmp_path, *, route: str, report_id: str) -> None:
    request = RetrievalRequest(route=route, query_text="q", query_ir_v2={"route_id": route})
    pipeline = RetrievalPipelineSpec(
        pipeline_id=f"orchestrated.{route}",
        version="v1",
        stages=[RetrievalPipelineStage(stage_id="stage", primitive_id="SyntheticRetriever")],
    )
    legacy_result = RetrievalExecutionResult(
        pipeline_id="legacy",
        pipeline_version="v1",
        candidates=[RetrievalCandidate(content_id=f"{report_id}-a")],
    )
    canon_result = RetrievalExecutionResult(
        pipeline_id="canon",
        pipeline_version="v1",
        candidates=[RetrievalCandidate(content_id=f"{report_id}-a")],
        metadata={"canon_graph_id": f"graph-{report_id}", "canon_bridge": {"available": True}},
    )
    report = build_shadow_execution_report(
        report_id=report_id,
        request=request,
        pipeline=pipeline,
        profile_id="aws_aurora_pg_opensearch_v1",
        legacy_result=legacy_result,
        canon_result=canon_result,
        shadow_diff={"divergence_class": "exact_match"},
    )
    persist_shadow_execution_report(report=report, output_dir=tmp_path)
    persist_shadow_replay_bundle(
        bundle=build_shadow_replay_bundle(
            bundle_id=f"canon-shadow-bundle-{report_id}",
            request=request,
            pipeline=pipeline,
            legacy_result=legacy_result,
            canon_result=canon_result,
            shadow_diff={"divergence_class": "exact_match"},
        ),
        output_dir=tmp_path,
    )
    persist_shadow_trace_export(
        export=build_shadow_trace_export(
            export_id=f"canon-shadow-traces-{report_id}",
            request=request,
            pipeline=pipeline,
            canon_result=canon_result,
        ),
        output_dir=tmp_path,
    )


def _seed_target_packages_and_pointer(tmp_path, routes: list[str]) -> None:
    build_phase1a_package_set_bundle(
        routes=routes,
        package_revision="rev-promo",
        output_dir=tmp_path / "packages",
        registry_path=tmp_path / "package_registry.json",
        route_options={"search_hybrid.document_chunk": {"disable_sparse": True}},
    )
    package_registry = load_graph_package_registry(tmp_path / "package_registry.json")
    bindings = {}
    seed = None
    for package in package_registry["packages"]:
        bindings[package["route_id"]] = {
            "package_id": package["package_id"],
            "package_revision": package["package_revision"],
            "graph_id": package["graph_id"],
        }
        if package["route_id"] == "search_bm25.document_chunk":
            seed = package
    assert seed is not None
    save_pointer_registry(
        {
            "schema_version": "canon_pointer_registry_v1",
            "generated_at": "2026-04-19T00:00:00+00:00",
            "shadow_pointer": {
                "pointer_id": "ptr-shadow",
                "graph_id": seed["graph_id"],
                "package_revision": seed["package_revision"],
                "profile_id": "planetscale_opensearch_v1",
                "route_ids": routes,
                "mode": "shadow",
                "metadata": {"package_bindings": bindings},
            },
            "candidate_primary_pointer": None,
            "primary_pointer": None,
            "history": [],
        },
        tmp_path / "pointer_registry.json",
    )


def test_target_profile_promotion_bundle_candidate_ready_but_not_primary(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")
    monkeypatch.setenv("QUERYLAKE_SPARSE_INDEX_DIMENSIONS", "8192")
    monkeypatch.setenv("QUERYLAKE_PLANETSCALE_DSN", "mysql://planetscale.example.com")

    routes = [
        "search_bm25.document_chunk",
        "search_file_chunks",
        "search_hybrid.document_chunk",
    ]
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
            path=str(tmp_path / "projection_store.json"),
        )
    for route, report_id in [
        ("search_bm25.document_chunk", "report-bm25"),
        ("search_file_chunks", "report-file"),
        ("search_hybrid.document_chunk", "report-hybrid"),
    ]:
        _persist_exact_match_report(tmp_path, route=route, report_id=report_id)
    _seed_target_packages_and_pointer(tmp_path, routes)

    payload = build_target_profile_promotion_bundle(
        target_profile_id="planetscale_opensearch_v1",
        routes=routes,
        shadow_artifact_dir=str(tmp_path),
        package_registry_path=str(tmp_path / "package_registry.json"),
        pointer_registry_path=str(tmp_path / "pointer_registry.json"),
        metadata_store_path=str(tmp_path / "projection_store.json"),
    )

    assert payload["summary"]["candidate_primary_ready"] is True
    assert payload["summary"]["bootstrap_ready_to_apply"] is True
    assert payload["summary"]["bootstrap_applied"] is False
    assert payload["summary"]["primary_ready"] is False
    assert "authority_plane_migration_incomplete" in payload["blockers"]
    assert "control_plane_migration_incomplete" in payload["blockers"]
    assert "target_profile_can_enter_candidate_primary_after_review" in payload["recommendations"]


def test_target_profile_promotion_bundle_blocks_without_target_configuration(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")
    monkeypatch.setenv("QUERYLAKE_SPARSE_INDEX_DIMENSIONS", "8192")
    monkeypatch.delenv("QUERYLAKE_PLANETSCALE_DSN", raising=False)
    routes = ["search_bm25.document_chunk"]
    mark_projection_build_ready(
        projection_id="document_chunk_lexical_projection_v1",
        projection_version="v1",
        profile_id="aws_aurora_pg_opensearch_v1",
        lane_family="lexical",
        target_backend="opensearch",
        build_revision="doclex:ready",
        path=str(tmp_path / "projection_store.json"),
    )
    _persist_exact_match_report(tmp_path, route="search_bm25.document_chunk", report_id="report-bm25")
    _seed_target_packages_and_pointer(tmp_path, routes)

    payload = build_target_profile_promotion_bundle(
        target_profile_id="planetscale_opensearch_v1",
        routes=routes,
        shadow_artifact_dir=str(tmp_path),
        package_registry_path=str(tmp_path / "package_registry.json"),
        pointer_registry_path=str(tmp_path / "pointer_registry.json"),
        metadata_store_path=str(tmp_path / "projection_store.json"),
    )

    assert payload["summary"]["candidate_primary_ready"] is False
    assert "target_profile_configuration_not_ready" in payload["blockers"]


def test_target_profile_promotion_bundle_reports_bootstrap_applied(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")
    monkeypatch.setenv("QUERYLAKE_SPARSE_INDEX_DIMENSIONS", "8192")
    monkeypatch.setenv("QUERYLAKE_PLANETSCALE_DSN", "mysql://planetscale.example.com")
    routes = [
        "search_bm25.document_chunk",
        "search_file_chunks",
        "search_hybrid.document_chunk",
    ]
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
            path=str(tmp_path / "projection_store.json"),
        )
    for route, report_id in [
        ("search_bm25.document_chunk", "report-bm25"),
        ("search_file_chunks", "report-file"),
        ("search_hybrid.document_chunk", "report-hybrid"),
    ]:
        _persist_exact_match_report(tmp_path, route=route, report_id=report_id)
    _seed_target_packages_and_pointer(tmp_path, routes)
    bootstrap_bundle = build_authority_control_bootstrap_bundle(
        profile_id="planetscale_opensearch_v1",
        routes=routes,
        package_registry_path=str(tmp_path / "package_registry.json"),
        pointer_registry_path=str(tmp_path / "pointer_registry.json"),
        metadata_store_path=str(tmp_path / "projection_store.json"),
    )
    apply_authority_control_bootstrap(
        bundle=bootstrap_bundle,
        registry_path=tmp_path / "authority_control_registry.json",
    )

    payload = build_target_profile_promotion_bundle(
        target_profile_id="planetscale_opensearch_v1",
        routes=routes,
        shadow_artifact_dir=str(tmp_path),
        package_registry_path=str(tmp_path / "package_registry.json"),
        pointer_registry_path=str(tmp_path / "pointer_registry.json"),
        authority_control_registry_path=str(tmp_path / "authority_control_registry.json"),
        metadata_store_path=str(tmp_path / "projection_store.json"),
    )

    assert payload["summary"]["bootstrap_applied"] is True

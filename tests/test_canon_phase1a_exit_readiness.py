from __future__ import annotations

import json

from QueryLake.canon.control.pointer_registry import save_pointer_registry
from QueryLake.canon.package import build_phase1a_package_set_bundle, load_graph_package_registry
from QueryLake.canon.runtime import (
    build_phase1a_exit_readiness_bundle,
    build_shadow_replay_bundle,
    build_shadow_trace_export,
    build_shadow_execution_report,
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


def test_phase1a_exit_readiness_bundle_can_satisfy_gate(monkeypatch, tmp_path):
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

    for route, report_id in [
        ("search_bm25.document_chunk", "report-bm25"),
        ("search_file_chunks", "report-file"),
        ("search_hybrid.document_chunk", "report-hybrid"),
    ]:
        _persist_exact_match_report(tmp_path, route=route, report_id=report_id)

    payload = build_phase1a_exit_readiness_bundle(
        profile_id="aws_aurora_pg_opensearch_v1",
        shadow_artifact_dir=tmp_path,
        metadata_store_path=str(metadata_path),
        routes=[
            "search_bm25.document_chunk",
            "search_file_chunks",
            "search_hybrid.document_chunk",
        ],
    )

    assert payload["schema_version"] == "canon_phase1a_exit_readiness_bundle_v1"
    assert payload["summary"]["report_count"] == 3
    assert payload["summary"]["candidate_set_delta_count"] == 0
    assert payload["summary"]["ready_for_phase1b"] is True
    assert payload["gates"]["declared_routes_runtime_ready"] is True
    assert "phase1a_exit_gate_satisfied" in payload["recommendations"]


def test_phase1a_exit_readiness_bundle_flags_shadow_gaps(monkeypatch, tmp_path):
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

    # One report only, and with a candidate set delta.
    request = RetrievalRequest(
        route="search_bm25.document_chunk",
        query_text="q",
        query_ir_v2={"route_id": "search_bm25.document_chunk"},
    )
    pipeline = RetrievalPipelineSpec(
        pipeline_id="orchestrated.search_bm25.document_chunk",
        version="v1",
        stages=[RetrievalPipelineStage(stage_id="stage", primitive_id="SyntheticRetriever")],
    )
    report = build_shadow_execution_report(
        report_id="delta-report",
        request=request,
        pipeline=pipeline,
        profile_id="aws_aurora_pg_opensearch_v1",
        legacy_result=RetrievalExecutionResult(
            pipeline_id="legacy",
            pipeline_version="v1",
            candidates=[RetrievalCandidate(content_id="a")],
        ),
        canon_result=RetrievalExecutionResult(
            pipeline_id="canon",
            pipeline_version="v1",
            candidates=[RetrievalCandidate(content_id="b")],
            metadata={"canon_graph_id": "graph-delta", "canon_bridge": {"available": True}},
        ),
        shadow_diff={"divergence_class": "candidate_set_delta"},
    )
    persist_shadow_execution_report(report=report, output_dir=tmp_path)

    payload = build_phase1a_exit_readiness_bundle(
        profile_id="aws_aurora_pg_opensearch_v1",
        shadow_artifact_dir=tmp_path,
        metadata_store_path=str(metadata_path),
        routes=["search_bm25.document_chunk", "search_file_chunks"],
    )

    assert payload["summary"]["ready_for_phase1b"] is False
    assert payload["gates"]["shadow_reports_present"] is False
    assert payload["gates"]["no_candidate_set_deltas"] is False
    assert "capture_shadow_evidence_for_each_bounded_route" in payload["recommendations"]
    assert "resolve_shadow_candidate_set_deltas_before_broadening_scope" in payload["recommendations"]


def test_phase1a_exit_readiness_bundle_includes_package_selection_gates(monkeypatch, tmp_path):
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

    routes = [
        "search_bm25.document_chunk",
        "search_file_chunks",
        "search_hybrid.document_chunk",
    ]
    for route, report_id in [
        ("search_bm25.document_chunk", "report-bm25"),
        ("search_file_chunks", "report-file"),
        ("search_hybrid.document_chunk", "report-hybrid"),
    ]:
        _persist_exact_match_report(tmp_path, route=route, report_id=report_id)

    build_phase1a_package_set_bundle(
        routes=routes,
        package_revision="rev-exit",
        output_dir=tmp_path / "packages",
        registry_path=tmp_path / "package_registry.json",
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
                "profile_id": "aws_aurora_pg_opensearch_v1",
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

    payload = build_phase1a_exit_readiness_bundle(
        profile_id="aws_aurora_pg_opensearch_v1",
        shadow_artifact_dir=tmp_path,
        metadata_store_path=str(metadata_path),
        routes=routes,
        package_registry_path=str(tmp_path / "package_registry.json"),
        pointer_registry_path=str(tmp_path / "pointer_registry.json"),
    )

    assert payload["gates"]["selected_packages_resolved_for_bounded_routes"] is True
    assert payload["gates"]["no_blocked_search_plane_a_rows"] is False
    assert payload["summary"]["ready_for_phase1b"] is False
    assert payload["search_plane_a_lowering_matrix"]["summary"]["execution_mode_counts"]["blocked"] == 1
    assert "resolve_blocked_search_plane_a_rows_before_candidate_primary" in payload["recommendations"]


def test_phase1a_exit_readiness_bundle_surfaces_target_profile_shadow_execution(monkeypatch, tmp_path):
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

    routes = [
        "search_bm25.document_chunk",
        "search_file_chunks",
        "search_hybrid.document_chunk",
    ]
    for route, report_id in [
        ("search_bm25.document_chunk", "report-bm25"),
        ("search_file_chunks", "report-file"),
        ("search_hybrid.document_chunk", "report-hybrid"),
    ]:
        _persist_exact_match_report(tmp_path, route=route, report_id=report_id)

    build_phase1a_package_set_bundle(
        routes=routes,
        package_revision="rev-target-shadow",
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

    payload = build_phase1a_exit_readiness_bundle(
        profile_id="aws_aurora_pg_opensearch_v1",
        shadow_artifact_dir=tmp_path,
        metadata_store_path=str(metadata_path),
        routes=routes,
        package_registry_path=str(tmp_path / "package_registry.json"),
        pointer_registry_path=str(tmp_path / "pointer_registry.json"),
    )

    target_summary = payload["summary"]["target_profile_shadow_execution"]
    assert target_summary["row_count"] == 3
    assert target_summary["shadow_executable_count"] == 3
    assert target_summary["canon_target_profile_shadow_executor_count"] == 3
    assert payload["target_search_plane_a_lowering_matrix"]["summary"]["execution_mode_counts"][
        "canon_target_profile_shadow_executor"
    ] == 3
    assert "bounded_target_profile_search_plane_shadow_execution_is_available" in payload["recommendations"]

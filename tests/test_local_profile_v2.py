import tempfile

from QueryLake.runtime.db_compat import DEPLOYMENT_PROFILES
from QueryLake.runtime.local_profile_v2 import (
    build_local_profile_diagnostics_payload,
    build_local_projection_build_ir_v2,
    build_local_query_ir_v2,
    build_local_route_execution_plan_payload,
    build_local_route_materialization_targets,
    build_local_route_projection_ir_v2,
    build_local_route_runtime_context_v2,
    build_local_route_support_matrix_payload,
)
from QueryLake.runtime.projection_refresh import bootstrap_profile_projections
from QueryLake.runtime.retrieval_route_executors import resolve_search_hybrid_route_executor


def test_local_query_ir_v2_translation_is_stable_for_hybrid_route():
    ir = build_local_query_ir_v2(
        "search_hybrid.document_chunk",
        raw_query_text='"vapor recovery" site:boiler',
        use_dense=True,
        collection_ids=["col-1"],
        return_statement=True,
    )
    assert ir.route_id == "search_hybrid.document_chunk"
    assert ir.representation_scope_id == "document_chunk"
    assert ir.requested_lanes() == ["lexical", "dense"]
    assert ir.strictness_policy.value == "reject_if_not_exact"
    assert ir.filter_ir.collection_ids == ["col-1"]
    assert ir.planner_hints["return_statement"] is True
    assert ir.planner_hints["query_features"]["quoted_phrases"] is True
    assert ir.planner_hints["query_features"]["hard_constraints"] is True


def test_local_query_ir_v2_detects_boolean_operators_without_hard_constraints():
    ir = build_local_query_ir_v2(
        "search_bm25.document_chunk",
        raw_query_text="vapor AND recovery",
        use_dense=False,
        use_sparse=False,
    )
    assert ir.strictness_policy.value == "exact"
    assert ir.planner_hints["query_features"]["quoted_phrases"] is False
    assert ir.planner_hints["query_features"]["boolean_operators"] is True
    assert ir.planner_hints["query_features"]["hard_constraints"] is False


def test_local_route_projection_ir_v2_tracks_required_targets_and_buildability():
    profile = DEPLOYMENT_PROFILES["sqlite_fts5_dense_sidecar_local_v1"]
    ir = build_local_route_projection_ir_v2(
        "search_hybrid.document_chunk",
        profile=profile,
        support_state="supported",
        use_dense=True,
        runtime_ready=False,
        runtime_blockers=["projection_not_ready"],
    )
    assert ir.route_id == "search_hybrid.document_chunk"
    assert ir.representation_scope_id == "document_chunk"
    assert ir.buildability_class.value == "executable_requires_build"
    assert [target.target_id for target in ir.required_targets] == [
        "document_chunk_lexical_projection_v1",
        "document_chunk_dense_projection_v1",
    ]
    assert ir.recovery_hints == [
        "bootstrap_required_projections:search_hybrid.document_chunk",
    ]


def test_local_materialization_targets_use_typed_route_targets():
    profile = DEPLOYMENT_PROFILES["sqlite_fts5_dense_sidecar_local_v1"]
    targets = build_local_route_materialization_targets(
        "search_file_chunks",
        profile=profile,
    )
    assert len(targets) == 1
    target = targets[0]
    assert target["projection_id"] == "file_chunk_lexical_projection_v1"
    assert target["source_scope"] == "file_chunk"
    assert target["target_backend_name"] == "sqlite_fts5"
    assert target["metadata"]["runtime_family"] == "local_profile_v2"


def test_local_projection_build_ir_v2_reports_ready_dense_projection():
    profile = DEPLOYMENT_PROFILES["sqlite_fts5_dense_sidecar_local_v1"]
    plan = build_local_projection_build_ir_v2(
        "document_chunk_dense_projection_v1",
        profile=profile,
        support_state="supported",
        action_mode="local_materialize",
        build_status="ready",
    )
    assert plan["projection_id"] == "document_chunk_dense_projection_v1"
    assert plan["representation_scope_id"] == "document_chunk"
    assert plan["lane_family"] == "dense"
    assert plan["target_backend"] == "local_dense_sidecar"
    assert plan["buildability_class"] == "executable_ready"


def test_local_route_resolution_carries_v2_planning_payload():
    profile = DEPLOYMENT_PROFILES["sqlite_fts5_dense_sidecar_local_v1"]
    resolved = resolve_search_hybrid_route_executor(
        profile=profile,
        use_bm25=True,
        use_similarity=True,
        use_sparse=False,
    )
    assert resolved.resolution.planning_v2["query_ir_v2_template"]["route_id"] == "search_hybrid.document_chunk"
    assert resolved.resolution.planning_v2["projection_ir_v2"]["representation_scope_id"] == "document_chunk"


def test_local_bootstrap_items_include_projection_plan_v2():
    profile = DEPLOYMENT_PROFILES["sqlite_fts5_dense_sidecar_local_v1"]
    with tempfile.TemporaryDirectory() as tmpdir:
        report = bootstrap_profile_projections(
            profile=profile,
            projection_ids=["document_chunk_lexical_projection_v1"],
            metadata_store_path=f"{tmpdir}/projection_metadata.json",
        )
    assert len(report.projection_items) == 1
    item = report.projection_items[0]
    assert item.projection_plan_v2["projection_id"] == "document_chunk_lexical_projection_v1"
    assert item.projection_plan_v2["representation_scope_id"] == "document_chunk"


def test_local_route_support_matrix_payload_is_stable():
    profile = DEPLOYMENT_PROFILES["sqlite_fts5_dense_sidecar_local_v1"]
    payload = build_local_route_support_matrix_payload(profile=profile)
    by_route = {entry["route_id"]: entry for entry in payload}

    assert by_route["search_hybrid.document_chunk"]["declared_executable"] is True
    assert by_route["search_hybrid.document_chunk"]["representation_scope_id"] == "document_chunk"
    assert by_route["search_hybrid.document_chunk"]["required_projection_descriptors"] == [
        "document_chunk_lexical_projection_v1",
        "document_chunk_dense_projection_v1",
    ]
    assert by_route["search_hybrid.document_chunk"]["lexical_support_class"] == "degraded_supported"
    assert by_route["retrieval.sparse.vector"]["declared_executable"] is False
    assert by_route["retrieval.sparse.vector"]["lexical_support_class"] == "unsupported"


def test_local_route_execution_plan_payload_is_stable():
    profile = DEPLOYMENT_PROFILES["sqlite_fts5_dense_sidecar_local_v1"]
    payload = build_local_route_execution_plan_payload(
        "search_hybrid.document_chunk",
        profile=profile,
        raw_query_text="vapor recovery",
        support_state="supported",
        use_dense=True,
        collection_ids=["c1"],
        return_statement=True,
        runtime_ready=False,
        runtime_blockers=["projection_build_required"],
    )
    assert payload["route_id"] == "search_hybrid.document_chunk"
    assert payload["query_ir_v2_template"]["route_id"] == "search_hybrid.document_chunk"
    assert payload["projection_ir_v2"]["representation_scope_id"] == "document_chunk"
    assert [item["projection_id"] for item in payload["materialization_targets"]] == [
        "document_chunk_lexical_projection_v1",
        "document_chunk_dense_projection_v1",
    ]


def test_local_route_runtime_context_v2_is_stable_for_hybrid_route():
    profile = DEPLOYMENT_PROFILES["sqlite_fts5_dense_sidecar_local_v1"]
    context = build_local_route_runtime_context_v2(
        "search_hybrid.document_chunk",
        profile=profile,
        raw_query_text="vapor recovery",
        support_state="supported",
        use_dense=True,
        collection_ids=["c1"],
        runtime_ready=False,
        runtime_blockers=["projection_build_required"],
    )
    assert context.route_id == "search_hybrid.document_chunk"
    assert context.representation_scope_id == "document_chunk"
    assert context.capability_dependencies == [
        "retrieval.lexical.bm25",
        "retrieval.dense.vector",
    ]
    assert context.required_projection_ids == [
        "document_chunk_lexical_projection_v1",
        "document_chunk_dense_projection_v1",
    ]
    assert context.lexical_support_class == "degraded_supported"
    assert context.materialization_target("document_chunk_dense_projection_v1") is not None
    assert context.query_ir_v2_template["route_id"] == "search_hybrid.document_chunk"
    assert context.projection_ir_v2["representation_scope_id"] == "document_chunk"


def test_local_profile_diagnostics_payload_route_runtime_contracts_use_v2_context():
    profile = DEPLOYMENT_PROFILES["sqlite_fts5_dense_sidecar_local_v1"]
    payload = build_local_profile_diagnostics_payload(profile=profile)
    by_route = {entry["route_id"]: entry for entry in payload["route_runtime_contracts"]}

    hybrid = by_route["search_hybrid.document_chunk"]
    assert hybrid["representation_scope_id"] == "document_chunk"
    assert hybrid["capability_dependencies"] == [
        "retrieval.lexical.bm25",
        "retrieval.dense.vector",
    ]
    assert hybrid["required_projection_ids"] == [
        "document_chunk_lexical_projection_v1",
        "document_chunk_dense_projection_v1",
    ]
    assert hybrid["dense_sidecar_required"] is True
    assert hybrid["query_ir_v2_template"]["route_id"] == "search_hybrid.document_chunk"
    assert hybrid["projection_ir_v2"]["representation_scope_id"] == "document_chunk"

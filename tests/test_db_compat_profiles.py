import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.db_compat import (
    QueryLakeProfileConfigurationError,
    DEFAULT_DB_PROFILE,
    build_backend_connectivity_payload,
    build_profile_configuration_payload,
    build_profile_diagnostics_payload,
    build_profile_route_support_matrix,
    build_supported_profiles_manifest_payload,
    QueryLakeUnsupportedFeatureError,
    build_capabilities_payload,
    get_deployment_profile,
    require_capability,
    validate_profile_configuration_requirements,
    validate_current_db_profile,
)
from QueryLake.runtime.projection_refresh import (
    invalidate_projection_build_states,
    mark_projection_build_failed,
    mark_projection_build_ready,
    mark_projection_build_started,
)
from QueryLake.runtime.projection_refresh import (
    ProjectionRefreshRequest,
    build_projection_refresh_plan,
    execute_projection_refresh_plan,
)


def test_default_profile_is_gold(monkeypatch):
    monkeypatch.delenv("QUERYLAKE_DB_PROFILE", raising=False)
    profile = validate_current_db_profile()
    assert profile.id == DEFAULT_DB_PROFILE
    assert profile.implemented is True


def test_payload_contains_profile_and_capabilities(monkeypatch):
    monkeypatch.delenv("QUERYLAKE_DB_PROFILE", raising=False)
    payload = build_capabilities_payload()
    assert payload["profile"]["id"] == DEFAULT_DB_PROFILE
    ids = {entry["id"] for entry in payload["capabilities"]}
    assert "retrieval.lexical.bm25" in ids
    assert "retrieval.sparse.vector" in ids
    assert payload["representation_scopes"]["document_chunk"]["authority_model"] == "document_segment"
    route_support = {row["route_id"]: row for row in payload["route_support_v2"]}
    assert route_support["search_hybrid.document_chunk"]["representation_scope"]["scope_id"] == "document_chunk"
    assert route_support["search_hybrid.document_chunk"]["capability_dependencies"] == [
        "retrieval.lexical.bm25",
        "retrieval.dense.vector",
    ]


def test_profile_diagnostics_payload_exposes_v2_manifest_data(monkeypatch):
    monkeypatch.delenv("QUERYLAKE_DB_PROFILE", raising=False)
    payload = build_profile_diagnostics_payload()
    assert payload["representation_scopes"]["file_chunk"]["authority_model"] == "file_chunk"
    route_support = {row["route_id"]: row for row in payload["route_support_v2"]}
    assert route_support["search_file_chunks"]["representation_scope"]["scope_id"] == "file_chunk"
    assert route_support["search_file_chunks"]["capability_dependencies"] == ["retrieval.lexical.bm25"]


def test_require_capability_raises_structured_error_for_planned_profile(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "postgres_pgvector_light_v1")
    profile = get_deployment_profile()
    try:
        require_capability("retrieval.sparse.vector", profile=profile)
    except QueryLakeUnsupportedFeatureError as exc:
        payload = exc.to_payload()
        assert payload["type"] == "unsupported_feature"
        assert payload["capability"] == "retrieval.sparse.vector"
        assert payload["profile"] == "postgres_pgvector_light_v1"
        assert payload["docs_ref"] == "docs/database/DB_COMPAT_PROFILES.md#unsupported-feature-contract"
        assert payload["retryable"] is False
        return
    raise AssertionError("expected QueryLakeUnsupportedFeatureError")


def test_unknown_profile_raises_structured_configuration_error(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "not_a_real_profile")
    try:
        validate_current_db_profile()
    except QueryLakeProfileConfigurationError as exc:
        payload = exc.to_payload()
        assert payload["type"] == "profile_configuration_error"
        assert payload["code"] == "ql.db_profile_invalid"
        assert payload["profile"] == "not_a_real_profile"
        assert payload["docs_ref"] == "docs/database/PROFILE_DIAGNOSTICS.md#startup-validation-rules"
        assert payload["retryable"] is False
        return
    raise AssertionError("expected QueryLakeProfileConfigurationError")


def test_declared_but_unimplemented_profile_fails_fast(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")
    profile = validate_current_db_profile()
    assert profile.id == "aws_aurora_pg_opensearch_v1"
    assert profile.implemented is True


def test_pgvector_light_profile_now_validates_as_limited_executable(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "postgres_pgvector_light_v1")
    profile = validate_current_db_profile()
    assert profile.id == "postgres_pgvector_light_v1"
    assert profile.implemented is True


def test_sqlite_local_profile_now_validates_as_supported_embedded(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "sqlite_fts5_dense_sidecar_local_v1")
    profile = validate_current_db_profile()
    assert profile.id == "sqlite_fts5_dense_sidecar_local_v1"
    assert profile.implemented is True


def test_local_profile_lane_adapter_registry_is_declared(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "sqlite_fts5_dense_sidecar_local_v1")
    payload = build_profile_diagnostics_payload(profile=get_deployment_profile())
    lanes = {row["lane_family"]: row for row in payload["lane_diagnostics"]}

    assert lanes["lexical_bm25"]["backend"] == "sqlite_fts5"
    assert lanes["lexical_bm25"]["adapter_id"] == "sqlite_fts5_bm25_v1"
    assert lanes["dense_vector"]["backend"] == "local_dense_sidecar"
    assert lanes["dense_vector"]["adapter_id"] == "local_dense_sidecar_v1"
    assert lanes["graph_traversal"]["backend"] == "sqlite_relation_graph"
    assert payload["local_profile"]["maturity"] == "embedded_supported"
    assert payload["local_profile"]["docs_ref"] == "docs/database/LOCAL_PROFILE_V1.md"
    local_support = {row["route_id"]: row for row in payload["local_profile"]["support_matrix"]}
    assert local_support["search_hybrid.document_chunk"]["representation_scope_id"] == "document_chunk"
    assert local_support["search_hybrid.document_chunk"]["declared_executable"] is True
    assert local_support["search_hybrid.document_chunk"]["lexical_support_class"] == "degraded_supported"
    assert local_support["search_file_chunks"]["representation_scope_id"] == "file_chunk"
    route_support_v2 = {row["route_id"]: row for row in payload["route_support_v2"]}
    assert (
        route_support_v2["search_hybrid.document_chunk"]["representation_scope"]["scope_id"]
        == local_support["search_hybrid.document_chunk"]["representation_scope_id"]
    )


def test_profile_configuration_payload_reports_missing_split_stack_requirements(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    payload = build_profile_configuration_payload()
    assert payload["profile_id"] == "aws_aurora_pg_opensearch_v1"
    assert payload["ready"] is False
    assert any(row["env_var"] == "QUERYLAKE_SEARCH_BACKEND_URL" and row["valid"] is False for row in payload["requirements"])
    assert any(
        row["env_var"] == "QUERYLAKE_AUTHORITY_DATABASE_URL"
        and row["required_for_execution"] is False
        and row["valid"] is False
        for row in payload["requirements"]
    )


def test_profile_configuration_validation_rejects_malformed_split_stack_requirements(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "not-a-url")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "0")
    with pytest.raises(QueryLakeProfileConfigurationError) as exc_info:
        validate_profile_configuration_requirements()
    payload = exc_info.value.to_payload()
    assert payload["profile"] == "aws_aurora_pg_opensearch_v1"
    assert "QUERYLAKE_SEARCH_BACKEND_URL" in payload["message"]
    assert "QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS" in payload["message"]


def test_profile_diagnostics_payload_reports_configuration_invalid_kind(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "not-a-url")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "0")

    payload = build_profile_diagnostics_payload()
    validation = payload["startup_validation"]
    assert validation["boot_ready"] is False
    assert validation["configuration_ready"] is False
    assert validation["validation_error_kind"] == "configuration_invalid"
    assert "missing environment variables" in validation["validation_error_hint"] or "Populate the missing environment variables" in validation["validation_error_hint"]
    assert validation["validation_error_docs_ref"] == "docs/database/FIRST_SPLIT_STACK_DEPLOYMENT.md#configuration-checklist"


def test_profile_diagnostics_payload_includes_route_executors_and_target(monkeypatch):
    monkeypatch.delenv("QUERYLAKE_DB_PROFILE", raising=False)
    payload = build_profile_diagnostics_payload()
    assert payload["profile"]["id"] == DEFAULT_DB_PROFILE
    assert payload["startup_validation"]["boot_ready"] is True
    assert payload["route_summary"]["inspected_route_count"] == len(payload["route_executors"])
    assert payload["route_summary"]["runtime_ready_route_count"] == len(payload["route_executors"])
    assert payload["route_executors"]
    assert payload["execution_target"]["profile_id"] == DEFAULT_DB_PROFILE
    assert payload["backend_connectivity"]["authority"]["status"] == "assumed_local_sql_engine"
    assert payload["backend_connectivity"]["projection"]["status"] == "co_located_with_authority"
    assert payload["route_summary"]["compatibility_projection_route_count"] >= 1
    assert "search_hybrid.document_chunk" in payload["route_summary"]["compatibility_projection_route_ids"]
    hybrid = {entry["route_id"]: entry for entry in payload["route_executors"]}["search_hybrid.document_chunk"]
    assert hybrid["compatibility_projection_reliance"] is True
    assert "document_chunk_dense_projection_v1" in hybrid["compatibility_projection_target_ids"]


def test_profile_diagnostics_payload_marks_planned_profiles_not_boot_ready(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.delenv("QUERYLAKE_SEARCH_BACKEND_URL", raising=False)
    monkeypatch.delenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", raising=False)
    monkeypatch.delenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", raising=False)
    payload = build_profile_diagnostics_payload()
    assert payload["startup_validation"]["boot_ready"] is False
    assert payload["startup_validation"]["profile_implemented"] is True
    assert payload["execution_target"]["profile_id"] == "aws_aurora_pg_opensearch_v1"


def test_profile_diagnostics_payload_exposes_lane_placeholders_for_split_stack_profile(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")

    payload = build_profile_diagnostics_payload()
    lanes = {row["lane_family"]: row for row in payload["lane_diagnostics"]}

    assert lanes["lexical_bm25"]["support_state"] == "degraded"
    assert lanes["lexical_bm25"]["implemented"] is True
    assert lanes["lexical_file_bm25"]["support_state"] == "supported"
    assert lanes["lexical_file_bm25"]["implemented"] is True
    assert lanes["dense_vector"]["support_state"] == "supported"
    assert lanes["dense_vector"]["implemented"] is True

    assert lanes["sparse_vector"]["support_state"] == "unsupported"
    assert lanes["sparse_vector"]["implemented"] is False
    assert lanes["sparse_vector"]["route_surface_declared"] is False
    assert lanes["sparse_vector"]["execution_mode"] == "placeholder"
    assert lanes["sparse_vector"]["blocked_by_capability"] == "retrieval.sparse.vector"
    assert lanes["sparse_vector"]["placeholder_executor_id"] == "placeholder.sparse_vector.aws_aurora_pg_opensearch_v1"
    assert lanes["sparse_vector"]["recommended_profile_id"] == "paradedb_postgres_gold_v1"
    assert "Disable sparse retrieval" in lanes["sparse_vector"]["hint"]

    assert lanes["graph_traversal"]["support_state"] == "unsupported"
    assert lanes["graph_traversal"]["implemented"] is False
    assert lanes["graph_traversal"]["route_surface_declared"] is False
    assert lanes["graph_traversal"]["execution_mode"] == "placeholder"
    assert lanes["graph_traversal"]["blocked_by_capability"] == "retrieval.graph.traversal"
    assert lanes["graph_traversal"]["placeholder_executor_id"] == "placeholder.graph_traversal.aws_aurora_pg_opensearch_v1"
    assert "graph traversal" in lanes["graph_traversal"]["hint"].lower()


def test_profile_diagnostics_payload_marks_pgvector_light_dense_only_slice_boot_ready(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "postgres_pgvector_light_v1")

    payload = build_profile_diagnostics_payload()

    validation = payload["startup_validation"]
    assert validation["boot_ready"] is True
    assert validation["profile_implemented"] is True
    assert validation["route_execution_ready"] is True
    assert validation["route_runtime_ready"] is True
    assert validation["required_route_ids"] == ["search_hybrid.document_chunk"]
    assert validation["non_executable_required_routes"] == []
    assert validation["non_runtime_ready_required_routes"] == []
    assert sorted(validation["non_executable_optional_routes"]) == [
        "search_bm25.document_chunk",
        "search_file_chunks",
    ]
    routes = {entry["route_id"]: entry for entry in payload["route_executors"]}
    assert routes["search_hybrid.document_chunk"]["implemented"] is True
    assert routes["search_hybrid.document_chunk"]["runtime_ready"] is True
    assert routes["search_hybrid.document_chunk"]["projection_dependency_mode"] == "optional_compatibility"
    assert routes["search_hybrid.document_chunk"]["projection_descriptors"] == []
    assert routes["search_hybrid.document_chunk"]["compatibility_projection_reliance"] is False
    assert routes["search_bm25.document_chunk"]["implemented"] is False
    assert routes["search_file_chunks"]["implemented"] is False


def test_profile_diagnostics_payload_treats_optional_route_gaps_as_non_blocking(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")

    payload = build_profile_diagnostics_payload()

    validation = payload["startup_validation"]
    assert validation["boot_ready"] is False
    assert validation["validation_error_kind"] == "projection_missing"
    assert validation["validation_error_docs_ref"] == "docs/database/PROFILE_DIAGNOSTICS.md#route-runtime-readiness-vs-route-execution-readiness"
    assert validation["validation_error_command"] == "python scripts/db_compat_profile_bootstrap.py --profile aws_aurora_pg_opensearch_v1"
    assert "bootstrap command" in validation["validation_error_hint"]
    assert validation["validation_error_details"]["projection_blocker_routes"]["projection_not_ready"] == [
        "search_bm25.document_chunk",
        "search_file_chunks",
        "search_hybrid.document_chunk",
    ]
    assert validation["route_execution_ready"] is True
    assert validation["route_runtime_ready"] is False
    assert validation["full_route_coverage_ready"] is True
    assert validation["full_runtime_coverage_ready"] is False
    assert validation["required_route_ids"] == [
        "search_hybrid.document_chunk",
        "search_bm25.document_chunk",
        "search_file_chunks",
    ]
    assert validation["non_executable_required_routes"] == []
    assert sorted(validation["non_runtime_ready_required_routes"]) == [
        "search_bm25.document_chunk",
        "search_file_chunks",
        "search_hybrid.document_chunk",
    ]
    assert validation["non_executable_optional_routes"] == []
    assert validation["non_runtime_ready_optional_routes"] == []
    assert "not runtime-ready" in validation["validation_error"]
    route_summary = payload["route_summary"]
    assert route_summary["inspected_route_count"] == 3
    assert route_summary["executable_route_count"] == 3
    assert route_summary["runtime_ready_route_count"] == 0
    assert route_summary["projection_blocked_route_count"] == 3
    assert route_summary["runtime_blocked_route_count"] == 3
    assert route_summary["compatibility_projection_route_count"] == 3
    assert route_summary["canonical_projection_route_count"] == 0
    assert route_summary["support_state_counts"] == {"degraded": 2, "supported": 1}
    assert route_summary["blocker_kind_counts"] == {"projection_not_ready": 3}
    assert sorted(route_summary["projection_blocked_route_ids"]) == [
        "search_bm25.document_chunk",
        "search_file_chunks",
        "search_hybrid.document_chunk",
    ]
    assert payload["backend_connectivity"]["authority"]["status"] == "assumed_current_sql_engine"
    assert payload["backend_connectivity"]["authority"]["database_url_env"] == "QUERYLAKE_DATABASE_URL"
    assert payload["backend_connectivity"]["projection"]["status"] == "configured_unprobed"
    route_payloads = {row["route_id"]: row for row in payload["route_executors"]}
    hybrid = route_payloads["search_hybrid.document_chunk"]
    assert hybrid["projection_dependency_mode"] == "required_external_projection"
    assert hybrid["projection_ready"] is False
    assert hybrid["runtime_ready"] is False
    assert hybrid["compatibility_projection_reliance"] is True
    assert hybrid["canonical_projection_target_ids"] == []
    assert len(hybrid["runtime_blockers"]) == 1
    assert hybrid["runtime_blockers"][0]["kind"] == "projection_not_ready"
    assert hybrid["runtime_blockers"][0]["summary"] == "Required external projections are not ready on this deployment."
    assert sorted(hybrid["runtime_blockers"][0]["projection_ids"]) == [
        "document_chunk_dense_projection_v1",
        "document_chunk_lexical_projection_v1",
    ]
    assert sorted(hybrid["projection_missing_descriptors"]) == [
        "document_chunk_dense_projection_v1",
        "document_chunk_lexical_projection_v1",
    ]
    assert hybrid["projection_writer_gap_descriptors"] == []
    assert sorted(hybrid["projection_build_gap_descriptors"]) == [
        "document_chunk_dense_projection_v1",
        "document_chunk_lexical_projection_v1",
    ]
    assert hybrid["projection_readiness"]["document_chunk_lexical_projection_v1"]["build_status"] == "absent"
    assert hybrid["projection_readiness"]["document_chunk_lexical_projection_v1"]["action_mode"] == "rebuild"
    assert hybrid["projection_readiness"]["document_chunk_dense_projection_v1"]["action_mode"] == "rebuild"


def test_profile_diagnostics_payload_reports_ready_split_stack_route_projections(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")

    mark_projection_build_ready(
        projection_id="document_chunk_lexical_projection_v1",
        projection_version="v1",
        profile_id="aws_aurora_pg_opensearch_v1",
        lane_family="lexical",
        target_backend="opensearch",
        build_revision="rev:lex",
        path=str(tmp_path / "projection_meta.json"),
    )
    mark_projection_build_ready(
        projection_id="document_chunk_dense_projection_v1",
        projection_version="v1",
        profile_id="aws_aurora_pg_opensearch_v1",
        lane_family="dense",
        target_backend="opensearch",
        build_revision="rev:dense",
        path=str(tmp_path / "projection_meta.json"),
    )
    mark_projection_build_ready(
        projection_id="file_chunk_lexical_projection_v1",
        projection_version="v1",
        profile_id="aws_aurora_pg_opensearch_v1",
        lane_family="lexical",
        target_backend="opensearch",
        build_revision="rev:file",
        path=str(tmp_path / "projection_meta.json"),
    )

    payload = build_profile_diagnostics_payload(metadata_store_path=str(tmp_path / "projection_meta.json"))
    validation = payload["startup_validation"]
    assert validation["boot_ready"] is True
    assert validation["route_runtime_ready"] is True
    assert validation["declared_executable_routes_runtime_ready"] is True
    assert validation["non_runtime_ready_required_routes"] == []
    assert validation["full_runtime_coverage_ready"] is True
    route_summary = payload["route_summary"]
    declared_route_support_matrix = build_profile_route_support_matrix(get_deployment_profile())
    declared_route_ids = [
        route_id
        for route_id, row in declared_route_support_matrix.items()
        if row.get("declared_executable") and route_id in {"search_bm25.document_chunk", "search_hybrid.document_chunk", "search_file_chunks"}
    ]
    assert route_summary["inspected_route_count"] == 3
    assert route_summary["declared_route_count"] == len(declared_route_ids)
    assert route_summary["declared_executable_route_count"] == 3
    assert route_summary["declared_optional_route_count"] == 0
    assert route_summary["runtime_ready_route_count"] == 3
    assert route_summary["declared_executable_runtime_ready_count"] == 3
    assert route_summary["declared_executable_runtime_blocked_count"] == 0
    assert route_summary["projection_blocked_route_count"] == 0
    assert route_summary["runtime_blocked_route_count"] == 0
    assert route_summary["blocker_kind_counts"] == {}
    assert sorted(route_summary["declared_executable_runtime_ready_ids"]) == [
        "search_bm25.document_chunk",
        "search_file_chunks",
        "search_hybrid.document_chunk",
    ]
    expected_declared_route_support = {
        route["route_id"]: route["support_state"]
        for route in payload["route_executors"]
        if route["route_id"] in declared_route_ids
    }
    assert route_summary["declared_route_support"] == expected_declared_route_support
    assert declared_route_support_matrix["retrieval.sparse.vector"]["declared_optional"] is True
    assert declared_route_support_matrix["retrieval.graph.traversal"]["declared_optional"] is True
    route_payloads = {row["route_id"]: row for row in payload["route_executors"]}
    hybrid = route_payloads["search_hybrid.document_chunk"]
    file_chunks = route_payloads["search_file_chunks"]
    assert hybrid["projection_ready"] is True
    assert hybrid["runtime_ready"] is True
    assert hybrid["runtime_blockers"] == []
    assert hybrid["projection_missing_descriptors"] == []
    assert hybrid["lexical_semantics"]["support_class"] == "degraded_supported"
    assert hybrid["lexical_semantics"]["capability_states"]["retrieval.lexical.phrase_boost"] == "degraded"
    assert hybrid["lexical_semantics"]["unsupported_capabilities"] == [
        "retrieval.lexical.hard_constraints",
    ]
    assert hybrid["projection_readiness"]["document_chunk_lexical_projection_v1"]["build_status"] == "ready"
    assert hybrid["projection_readiness"]["document_chunk_dense_projection_v1"]["build_status"] == "ready"
    assert file_chunks["projection_ready"] is True
    assert file_chunks["runtime_ready"] is True
    assert file_chunks["lexical_semantics"]["support_class"] == "degraded_supported"
    assert file_chunks["projection_readiness"]["file_chunk_lexical_projection_v1"]["build_status"] == "ready"


def test_profile_diagnostics_payload_treats_gold_projection_dependency_as_optional(monkeypatch):
    monkeypatch.delenv("QUERYLAKE_DB_PROFILE", raising=False)
    payload = build_profile_diagnostics_payload()
    route_payloads = {row["route_id"]: row for row in payload["route_executors"]}
    hybrid = route_payloads["search_hybrid.document_chunk"]
    assert hybrid["projection_dependency_mode"] == "optional_compatibility"
    assert hybrid["projection_ready"] is True
    assert hybrid["runtime_ready"] is True
    assert hybrid["runtime_blockers"] == []
    assert hybrid["projection_missing_descriptors"] == []
    assert "document_chunk_lexical_projection_v1" in hybrid["projection_readiness"]


def test_profile_diagnostics_payload_partial_split_stack_readiness_after_lexical_builds(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")

    metadata_path = tmp_path / "projection_meta.json"
    mark_projection_build_ready(
        projection_id="document_chunk_lexical_projection_v1",
        projection_version="v1",
        profile_id="aws_aurora_pg_opensearch_v1",
        lane_family="lexical",
        target_backend="opensearch",
        build_revision="rev:doc-lex",
        path=str(metadata_path),
    )
    mark_projection_build_ready(
        projection_id="file_chunk_lexical_projection_v1",
        projection_version="v1",
        profile_id="aws_aurora_pg_opensearch_v1",
        lane_family="lexical",
        target_backend="opensearch",
        build_revision="rev:file-lex",
        path=str(metadata_path),
    )

    payload = build_profile_diagnostics_payload(metadata_store_path=str(metadata_path))
    validation = payload["startup_validation"]
    assert validation["boot_ready"] is False
    assert validation["route_execution_ready"] is True
    assert validation["route_runtime_ready"] is False
    assert validation["declared_executable_routes_runtime_ready"] is False
    assert validation["non_runtime_ready_required_routes"] == [
        "search_hybrid.document_chunk",
    ]
    assert sorted(validation["declared_executable_runtime_ready_ids"]) == [
        "search_bm25.document_chunk",
        "search_file_chunks",
    ]
    assert validation["declared_executable_runtime_blocked_ids"] == [
        "search_hybrid.document_chunk",
    ]

    route_payloads = {row["route_id"]: row for row in payload["route_executors"]}
    bm25 = route_payloads["search_bm25.document_chunk"]
    hybrid = route_payloads["search_hybrid.document_chunk"]
    file_chunks = route_payloads["search_file_chunks"]

    assert bm25["runtime_ready"] is True
    assert bm25["runtime_blockers"] == []
    assert file_chunks["runtime_ready"] is True
    assert file_chunks["runtime_blockers"] == []
    assert hybrid["runtime_ready"] is False
    assert hybrid["lexical_semantics"]["support_class"] == "degraded_supported"
    assert hybrid["projection_writer_gap_descriptors"] == []
    assert hybrid["projection_build_gap_descriptors"] == [
        "document_chunk_dense_projection_v1",
    ]


def test_profile_diagnostics_payload_becomes_boot_ready_after_real_split_stack_refresh_runs(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "3")
    metadata_path = tmp_path / "projection_meta.json"

    import QueryLake.runtime.opensearch_projection_writers as writers_mod

    monkeypatch.setattr(writers_mod, "_ensure_index", lambda index_name, payload=None: None)
    monkeypatch.setattr(writers_mod, "_clear_index", lambda index_name: {"deleted": 0})
    def _fake_fetch_projection_materialization_rows(database, target):
        projection_id = target.projection_id
        if projection_id == "file_chunk_lexical_projection_v1":
            return [("file-chunk-1", "hello file", {}, 1.0, "fv-1", "user-1", "col-1")]
        return [
            type(
                "DocRow",
                (),
                {
                    "id": "chunk-1",
                    "text": "hello world",
                    "document_id": "doc-1",
                    "document_name": "Doc One",
                    "website_url": None,
                    "collection_id": "col-1",
                    "creation_timestamp": 1.0,
                    "document_chunk_number": 0,
                    "md": {},
                    "document_md": {},
                    "embedding": [0.1, 0.2, 0.3],
                },
            )(),
        ]

    monkeypatch.setattr(writers_mod, "fetch_projection_materialization_rows", _fake_fetch_projection_materialization_rows)
    monkeypatch.setattr(
        writers_mod,
        "_perform_opensearch_bulk",
        lambda *, path, lines: {"errors": False, "items": [{"index": {"status": 201}} for _ in lines[::2]]},
    )

    for projection_id, lane_families in [
        ("document_chunk_lexical_projection_v1", ["lexical"]),
        ("document_chunk_dense_projection_v1", ["dense"]),
        ("file_chunk_lexical_projection_v1", ["lexical"]),
    ]:
        request = ProjectionRefreshRequest(
            projection_id=projection_id,
            lane_families=lane_families,
            collection_ids=["col-1"],
            metadata={"force_rebuild": True},
        )
        plan = build_projection_refresh_plan(request, metadata_store_path=str(metadata_path))
        report = execute_projection_refresh_plan(plan, database=object(), metadata_store_path=str(metadata_path))
        assert len(report.executed_actions) == 1

    payload = build_profile_diagnostics_payload(metadata_store_path=str(metadata_path))
    validation = payload["startup_validation"]
    assert validation["boot_ready"] is True
    assert validation["route_runtime_ready"] is True
    assert validation["non_runtime_ready_required_routes"] == []

    route_payloads = {row["route_id"]: row for row in payload["route_executors"]}
    hybrid = route_payloads["search_hybrid.document_chunk"]
    bm25 = route_payloads["search_bm25.document_chunk"]
    file_chunks = route_payloads["search_file_chunks"]

    assert hybrid["runtime_ready"] is True
    assert hybrid["runtime_blockers"] == []
    assert hybrid["projection_missing_descriptors"] == []
    assert bm25["runtime_ready"] is True
    assert file_chunks["runtime_ready"] is True


def test_backend_connectivity_projection_probe_reports_reachable(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")
    monkeypatch.setenv("QUERYLAKE_PROFILE_DIAGNOSTICS_PROBE", "1")

    class _Response:
        status_code = 200

    class _Client:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, url):
            assert url == "https://search.example.com"
            return _Response()

    monkeypatch.setattr("QueryLake.runtime.db_compat.httpx.Client", _Client)
    profile = get_deployment_profile()
    config = build_profile_configuration_payload(profile)
    payload = build_backend_connectivity_payload(profile, configuration=config)
    assert payload["projection"]["status"] == "reachable"
    assert payload["projection"]["checked"] is True
    assert payload["projection"]["status_code"] == 200


def test_backend_connectivity_projection_probe_reports_unreachable(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")
    monkeypatch.setenv("QUERYLAKE_PROFILE_DIAGNOSTICS_PROBE", "1")

    class _Client:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, url):
            raise RuntimeError("boom")

    monkeypatch.setattr("QueryLake.runtime.db_compat.httpx.Client", _Client)
    profile = get_deployment_profile()
    config = build_profile_configuration_payload(profile)
    payload = build_backend_connectivity_payload(profile, configuration=config)
    assert payload["projection"]["status"] == "unreachable"
    assert payload["projection"]["checked"] is True
    assert "boom" in payload["projection"]["detail"]


def test_profile_diagnostics_probe_unreachable_projection_blocks_boot_ready(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")
    monkeypatch.setenv("QUERYLAKE_PROFILE_DIAGNOSTICS_PROBE", "1")

    from tempfile import TemporaryDirectory

    class _Client:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, url):
            raise RuntimeError("opensearch down")

    monkeypatch.setattr("QueryLake.runtime.db_compat.httpx.Client", _Client)
    with TemporaryDirectory() as tmpdir:
        metadata_path = os.path.join(tmpdir, "projection_meta.json")
        mark_projection_build_ready(
            projection_id="document_chunk_lexical_projection_v1",
            projection_version="v1",
            profile_id="aws_aurora_pg_opensearch_v1",
            lane_family="lexical",
            target_backend="opensearch",
            build_revision="rev:lex",
            path=metadata_path,
        )
        mark_projection_build_ready(
            projection_id="document_chunk_dense_projection_v1",
            projection_version="v1",
            profile_id="aws_aurora_pg_opensearch_v1",
            lane_family="dense",
            target_backend="opensearch",
            build_revision="rev:dense",
            path=metadata_path,
        )
        mark_projection_build_ready(
            projection_id="file_chunk_lexical_projection_v1",
            projection_version="v1",
            profile_id="aws_aurora_pg_opensearch_v1",
            lane_family="lexical",
            target_backend="opensearch",
            build_revision="rev:file",
            path=metadata_path,
        )
        payload = build_profile_diagnostics_payload(metadata_store_path=metadata_path)
    validation = payload["startup_validation"]
    assert validation["backend_connectivity_ready"] is False
    assert validation["non_reachable_required_backends"] == ["projection"]
    assert validation["boot_ready"] is False
    assert validation["validation_error_kind"] == "backend_unreachable"
    assert "required planes: projection" in str(validation["validation_error"])


def test_profile_diagnostics_probe_unreachable_authority_blocks_boot_ready(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")
    monkeypatch.setenv("QUERYLAKE_PROFILE_DIAGNOSTICS_PROBE", "1")
    monkeypatch.setenv("QUERYLAKE_AUTHORITY_DATABASE_URL", "postgresql://aurora-user:pw@aurora.example.internal:5432/querylake")

    from tempfile import TemporaryDirectory

    class _Response:
        status_code = 200

    class _Client:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, url):
            return _Response()

    class _Engine:
        def connect(self):
            raise RuntimeError("aurora down")

        def dispose(self):
            return None

    monkeypatch.setattr("QueryLake.runtime.db_compat.httpx.Client", _Client)
    monkeypatch.setattr("QueryLake.runtime.db_compat.create_engine", lambda *args, **kwargs: _Engine())
    with TemporaryDirectory() as tmpdir:
        metadata_path = os.path.join(tmpdir, "projection_meta.json")
        mark_projection_build_ready(
            projection_id="document_chunk_lexical_projection_v1",
            projection_version="v1",
            profile_id="aws_aurora_pg_opensearch_v1",
            lane_family="lexical",
            target_backend="opensearch",
            build_revision="rev:lex",
            path=metadata_path,
        )
        mark_projection_build_ready(
            projection_id="document_chunk_dense_projection_v1",
            projection_version="v1",
            profile_id="aws_aurora_pg_opensearch_v1",
            lane_family="dense",
            target_backend="opensearch",
            build_revision="rev:dense",
            path=metadata_path,
        )
        mark_projection_build_ready(
            projection_id="file_chunk_lexical_projection_v1",
            projection_version="v1",
            profile_id="aws_aurora_pg_opensearch_v1",
            lane_family="lexical",
            target_backend="opensearch",
            build_revision="rev:file",
            path=metadata_path,
        )
        payload = build_profile_diagnostics_payload(metadata_store_path=metadata_path)
    validation = payload["startup_validation"]
    assert validation["backend_connectivity_ready"] is False
    assert validation["non_reachable_required_backends"] == ["authority"]
    assert validation["boot_ready"] is False
    assert validation["validation_error_kind"] == "backend_unreachable"
    assert "required planes: authority" in str(validation["validation_error"])


def test_backend_connectivity_authority_probe_reports_reachable(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_PROFILE_DIAGNOSTICS_PROBE", "1")

    class _Connection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, statement):
            class _Result:
                def scalar(self_inner):
                    return 1

            return _Result()

    class _Engine:
        def connect(self):
            return _Connection()

        def dispose(self):
            return None

    def _fake_create_engine(url, pool_pre_ping=True, connect_args=None):
        assert pool_pre_ping is True
        assert isinstance(connect_args, dict)
        return _Engine()

    monkeypatch.setattr("QueryLake.runtime.db_compat.create_engine", _fake_create_engine)
    profile = get_deployment_profile()
    config = build_profile_configuration_payload(profile)
    payload = build_backend_connectivity_payload(profile, configuration=config)
    assert payload["authority"]["status"] == "reachable"
    assert payload["authority"]["checked"] is True
    assert "SELECT 1" in payload["authority"]["detail"]


def test_backend_connectivity_authority_probe_prefers_explicit_authority_dsn(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")
    monkeypatch.setenv("QUERYLAKE_AUTHORITY_DATABASE_URL", "postgresql://aurora-user:pw@aurora.example.internal:5432/querylake")
    monkeypatch.setenv("QUERYLAKE_PROFILE_DIAGNOSTICS_PROBE", "1")

    observed = {}

    class _Connection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, statement):
            class _Result:
                def scalar(self_inner):
                    return 1

            return _Result()

    class _Engine:
        def connect(self):
            return _Connection()

        def dispose(self):
            return None

    def _fake_create_engine(url, pool_pre_ping=True, connect_args=None):
        observed["url"] = url
        observed["connect_args"] = connect_args
        return _Engine()

    monkeypatch.setattr("QueryLake.runtime.db_compat.create_engine", _fake_create_engine)
    profile = get_deployment_profile()
    config = build_profile_configuration_payload(profile)
    payload = build_backend_connectivity_payload(profile, configuration=config)
    assert observed["url"] == "postgresql://aurora-user:pw@aurora.example.internal:5432/querylake"
    assert payload["authority"]["status"] == "reachable"
    assert payload["authority"]["database_url_env"] == "QUERYLAKE_AUTHORITY_DATABASE_URL"
    assert payload["authority"]["checked"] is True


def test_backend_connectivity_authority_payload_surfaces_override_without_probe(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")
    monkeypatch.setenv("QUERYLAKE_AUTHORITY_DATABASE_URL", "postgresql://aurora-user:pw@aurora.example.internal:5432/querylake")

    payload = build_profile_diagnostics_payload()
    assert payload["backend_connectivity"]["authority"]["status"] == "configured_authority_target"
    assert payload["backend_connectivity"]["authority"]["database_url_env"] == "QUERYLAKE_AUTHORITY_DATABASE_URL"
    assert payload["backend_connectivity"]["authority"]["target"] == {
        "scheme": "postgresql",
        "host": "aurora.example.internal",
        "port": 5432,
        "database": "querylake",
    }


def test_backend_connectivity_projection_payload_surfaces_safe_target(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com:9443")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")
    payload = build_profile_diagnostics_payload()
    assert payload["backend_connectivity"]["projection"]["target"] == {
        "scheme": "https",
        "host": "search.example.com",
        "port": 9443,
        "index_namespace": "ql",
    }


def test_profile_diagnostics_distinguishes_projection_stale_validation_kind(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")
    metadata_path = str(tmp_path / "projection_meta.json")

    mark_projection_build_ready(
        projection_id="document_chunk_lexical_projection_v1",
        projection_version="v1",
        profile_id="aws_aurora_pg_opensearch_v1",
        lane_family="lexical",
        target_backend="opensearch",
        build_revision="r1",
        path=metadata_path,
    )
    mark_projection_build_ready(
        projection_id="document_chunk_dense_projection_v1",
        projection_version="v1",
        profile_id="aws_aurora_pg_opensearch_v1",
        lane_family="dense",
        target_backend="opensearch",
        build_revision="r2",
        path=metadata_path,
    )
    mark_projection_build_ready(
        projection_id="file_chunk_lexical_projection_v1",
        projection_version="v1",
        profile_id="aws_aurora_pg_opensearch_v1",
        lane_family="lexical",
        target_backend="opensearch",
        build_revision="r3",
        path=metadata_path,
    )
    invalidate_projection_build_states(
        projection_id="document_chunk_lexical_projection_v1",
        projection_version="v1",
        profile_id="aws_aurora_pg_opensearch_v1",
        lane_families=["lexical"],
        invalidated_by=["document_updated"],
        path=metadata_path,
    )

    payload = build_profile_diagnostics_payload(metadata_store_path=metadata_path)
    startup = payload["startup_validation"]

    assert startup["validation_error_kind"] == "projection_stale"
    assert "search_bm25.document_chunk" in startup["validation_error_details"]["route_ids"]
    assert startup["validation_error_details"]["projection_blocker_routes"]["projection_stale"] == [
        "search_bm25.document_chunk",
        "search_hybrid.document_chunk",
    ]
    assert startup["validation_error_details"]["projection_blocker_projection_ids"]["projection_stale"] == [
        "document_chunk_lexical_projection_v1",
    ]


def test_backend_connectivity_authority_probe_reports_unreachable(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_PROFILE_DIAGNOSTICS_PROBE", "1")

    class _Engine:
        def connect(self):
            raise RuntimeError("sql down")

        def dispose(self):
            return None

    monkeypatch.setattr("QueryLake.runtime.db_compat.create_engine", lambda *args, **kwargs: _Engine())
    profile = get_deployment_profile()
    config = build_profile_configuration_payload(profile)
    payload = build_backend_connectivity_payload(profile, configuration=config)
    assert payload["authority"]["status"] == "unreachable"
    assert payload["authority"]["checked"] is True
    assert "sql down" in payload["authority"]["detail"]


def test_profile_diagnostics_payload_reports_building_projection_blocker(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")
    metadata_path = str(tmp_path / "projection_meta.json")

    mark_projection_build_started(
        projection_id="document_chunk_lexical_projection_v1",
        projection_version="v1",
        profile_id="aws_aurora_pg_opensearch_v1",
        lane_family="lexical",
        target_backend="opensearch",
        build_revision="rev:lex",
        path=metadata_path,
    )
    mark_projection_build_ready(
        projection_id="document_chunk_dense_projection_v1",
        projection_version="v1",
        profile_id="aws_aurora_pg_opensearch_v1",
        lane_family="dense",
        target_backend="opensearch",
        build_revision="rev:dense",
        path=metadata_path,
    )
    mark_projection_build_ready(
        projection_id="file_chunk_lexical_projection_v1",
        projection_version="v1",
        profile_id="aws_aurora_pg_opensearch_v1",
        lane_family="lexical",
        target_backend="opensearch",
        build_revision="rev:file",
        path=metadata_path,
    )

    payload = build_profile_diagnostics_payload(metadata_store_path=metadata_path)
    hybrid = {row["route_id"]: row for row in payload["route_executors"]}["search_hybrid.document_chunk"]
    assert hybrid["runtime_ready"] is False
    assert hybrid["projection_building_gap_descriptors"] == ["document_chunk_lexical_projection_v1"]
    assert hybrid["projection_failed_gap_descriptors"] == []
    assert hybrid["projection_stale_gap_descriptors"] == []
    assert hybrid["projection_build_gap_descriptors"] == []
    assert hybrid["runtime_blockers"][0]["kind"] == "projection_building"


def test_profile_diagnostics_payload_reports_failed_projection_blocker(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")
    metadata_path = str(tmp_path / "projection_meta.json")

    mark_projection_build_failed(
        projection_id="document_chunk_lexical_projection_v1",
        projection_version="v1",
        profile_id="aws_aurora_pg_opensearch_v1",
        lane_family="lexical",
        target_backend="opensearch",
        build_revision="rev:lex",
        error_summary="writer failed",
        path=metadata_path,
    )
    mark_projection_build_ready(
        projection_id="document_chunk_dense_projection_v1",
        projection_version="v1",
        profile_id="aws_aurora_pg_opensearch_v1",
        lane_family="dense",
        target_backend="opensearch",
        build_revision="rev:dense",
        path=metadata_path,
    )
    mark_projection_build_ready(
        projection_id="file_chunk_lexical_projection_v1",
        projection_version="v1",
        profile_id="aws_aurora_pg_opensearch_v1",
        lane_family="lexical",
        target_backend="opensearch",
        build_revision="rev:file",
        path=metadata_path,
    )

    payload = build_profile_diagnostics_payload(metadata_store_path=metadata_path)
    hybrid = {row["route_id"]: row for row in payload["route_executors"]}["search_hybrid.document_chunk"]
    assert hybrid["runtime_ready"] is False
    assert hybrid["projection_building_gap_descriptors"] == []
    assert hybrid["projection_failed_gap_descriptors"] == ["document_chunk_lexical_projection_v1"]
    assert hybrid["projection_stale_gap_descriptors"] == []
    assert hybrid["projection_build_gap_descriptors"] == []
    assert hybrid["runtime_blockers"][0]["kind"] == "projection_failed"


def test_profile_diagnostics_payload_reports_stale_projection_blocker(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")
    metadata_path = str(tmp_path / "projection_meta.json")

    mark_projection_build_ready(
        projection_id="document_chunk_lexical_projection_v1",
        projection_version="v1",
        profile_id="aws_aurora_pg_opensearch_v1",
        lane_family="lexical",
        target_backend="opensearch",
        build_revision="rev:lex",
        path=metadata_path,
    )
    mark_projection_build_ready(
        projection_id="document_chunk_dense_projection_v1",
        projection_version="v1",
        profile_id="aws_aurora_pg_opensearch_v1",
        lane_family="dense",
        target_backend="opensearch",
        build_revision="rev:dense",
        path=metadata_path,
    )
    mark_projection_build_ready(
        projection_id="file_chunk_lexical_projection_v1",
        projection_version="v1",
        profile_id="aws_aurora_pg_opensearch_v1",
        lane_family="lexical",
        target_backend="opensearch",
        build_revision="rev:file",
        path=metadata_path,
    )
    invalidate_projection_build_states(
        projection_id="document_chunk_lexical_projection_v1",
        projection_version="v1",
        profile_id="aws_aurora_pg_opensearch_v1",
        lane_families=["lexical"],
        invalidated_by=["document_ingest_changed"],
        path=metadata_path,
    )

    payload = build_profile_diagnostics_payload(metadata_store_path=metadata_path)
    hybrid = {row["route_id"]: row for row in payload["route_executors"]}["search_hybrid.document_chunk"]
    assert hybrid["runtime_ready"] is False
    assert hybrid["projection_building_gap_descriptors"] == []
    assert hybrid["projection_failed_gap_descriptors"] == []
    assert hybrid["projection_stale_gap_descriptors"] == ["document_chunk_lexical_projection_v1"]
    assert hybrid["projection_build_gap_descriptors"] == []
    assert hybrid["runtime_blockers"][0]["kind"] == "projection_stale"


def test_supported_profiles_manifest_payload_reports_authoritative_profile_and_route_matrix():
    payload = build_supported_profiles_manifest_payload()
    profiles = {row["id"]: row for row in payload["profiles"]}

    assert set(profiles) >= {
        "paradedb_postgres_gold_v1",
        "postgres_pgvector_light_v1",
        "aws_aurora_pg_opensearch_v1",
        "sqlite_fts5_dense_sidecar_local_v1",
    }

    gold = profiles["paradedb_postgres_gold_v1"]
    assert gold["implemented"] is True
    assert gold["recommended"] is True
    assert gold["maturity"] == "gold"
    assert gold["capabilities"]["retrieval.lexical.bm25"] == "supported"
    assert gold["routes"]["search_hybrid.document_chunk"]["declared_state"] == "supported"
    assert gold["routes"]["retrieval.graph.traversal"]["declared_executable"] is True
    assert gold["routes"]["retrieval.graph.traversal"]["declared_optional"] is False
    assert gold["routes"]["search_hybrid.document_chunk"]["representation_scope_id"] == "document_chunk"
    assert gold["routes"]["search_hybrid.document_chunk"]["capability_dependencies"] == [
        "retrieval.lexical.bm25",
        "retrieval.dense.vector",
    ]
    assert gold["representation_scopes"]["document_chunk"]["compatibility_projection"] is True
    assert gold["routes_v2"][0]["representation_scope"]["scope_id"] in {
        "document_chunk",
        "document_segment_graph",
        "file_chunk",
    }

    light = profiles["postgres_pgvector_light_v1"]
    assert light["implemented"] is True
    assert light["maturity"] == "limited_executable"
    assert light["capabilities"]["retrieval.dense.vector"] == "supported"
    assert light["capabilities"]["retrieval.lexical.bm25"] == "unsupported"
    assert light["routes"]["search_hybrid.document_chunk"]["declared_executable"] is True
    assert light["routes"]["search_bm25.document_chunk"]["declared_optional"] is True

    aurora = profiles["aws_aurora_pg_opensearch_v1"]
    assert aurora["implemented"] is True
    assert aurora["maturity"] == "split_stack_executable"
    assert aurora["capabilities"]["retrieval.lexical.bm25"] == "supported"
    assert aurora["capabilities"]["retrieval.dense.vector"] == "supported"
    assert aurora["capabilities"]["retrieval.sparse.vector"] == "unsupported"
    assert aurora["routes"]["search_bm25.document_chunk"]["declared_state"] == "supported"
    assert aurora["routes"]["search_bm25.document_chunk"]["declared_executable"] is True
    assert aurora["routes"]["retrieval.sparse.vector"]["declared_optional"] is True

    local = profiles["sqlite_fts5_dense_sidecar_local_v1"]
    assert local["implemented"] is True
    assert local["maturity"] == "embedded_supported"
    assert local["capabilities"]["retrieval.dense.vector"] == "supported"
    assert local["capabilities"]["retrieval.lexical.bm25"] == "degraded"
    assert local["routes"]["search_hybrid.document_chunk"]["declared_executable"] is True
    assert local["routes"]["search_bm25.document_chunk"]["declared_state"] == "degraded"
    assert local["routes"]["retrieval.sparse.vector"]["declared_optional"] is True

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.db_compat import (
    DEPLOYMENT_PROFILES,
    build_capabilities_payload,
    build_profile_diagnostics_payload,
)
from QueryLake.runtime.profile_bringup import build_profile_bringup_payload
from QueryLake.runtime.projection_refresh import mark_projection_build_ready
from QueryLake.runtime.retrieval_route_executors import (
    resolve_search_bm25_route_executor,
    resolve_search_file_chunks_route_executor,
    resolve_search_hybrid_route_executor,
)
from server import build_readyz_payload


SDK_ROOT = Path(__file__).resolve().parents[1] / "sdk" / "python" / "src"
if str(SDK_ROOT) not in sys.path:
    sys.path.insert(0, str(SDK_ROOT))

from querylake_sdk.models import (
    parse_capabilities_summary,
    parse_profile_bringup_summary,
    parse_profile_diagnostics_summary,
)


def test_split_stack_support_state_is_consistent_across_capabilities_diagnostics_resolution_and_sdk(tmp_path, monkeypatch):
    profile = DEPLOYMENT_PROFILES["aws_aurora_pg_opensearch_v1"]
    metadata_path = tmp_path / "projection_meta.json"
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://example-opensearch.local")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "querylake")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")

    mark_projection_build_ready(
        projection_id="document_chunk_lexical_projection_v1",
        projection_version="v1",
        profile_id=profile.id,
        lane_family="lexical",
        target_backend="opensearch",
        build_revision="consistency:lexical",
        metadata={"source": "cross_surface_test"},
        path=str(metadata_path),
    )
    mark_projection_build_ready(
        projection_id="document_chunk_dense_projection_v1",
        projection_version="v1",
        profile_id=profile.id,
        lane_family="dense",
        target_backend="opensearch",
        build_revision="consistency:dense",
        metadata={"source": "cross_surface_test"},
        path=str(metadata_path),
    )
    mark_projection_build_ready(
        projection_id="file_chunk_lexical_projection_v1",
        projection_version="v1",
        profile_id=profile.id,
        lane_family="lexical",
        target_backend="opensearch",
        build_revision="consistency:file",
        metadata={"source": "cross_surface_test"},
        path=str(metadata_path),
    )

    capabilities_payload = build_capabilities_payload(profile)
    diagnostics_payload = build_profile_diagnostics_payload(profile=profile, metadata_store_path=str(metadata_path))
    bringup_payload = build_profile_bringup_payload(profile=profile, metadata_store_path=str(metadata_path))
    readyz_payload = build_readyz_payload(
        model_ids=["bge-m3", "reranker"],
        profile=profile,
        metadata_store_path=str(metadata_path),
    )

    capability_summary = parse_capabilities_summary(capabilities_payload)
    diagnostics_summary = parse_profile_diagnostics_summary(diagnostics_payload)
    bringup_summary = parse_profile_bringup_summary(bringup_payload)

    assert capabilities_payload["profile"]["maturity"] == "split_stack_executable"
    assert diagnostics_payload["profile"]["maturity"] == "split_stack_executable"
    assert bringup_payload["profile"]["maturity"] == "split_stack_executable"
    assert capability_summary.profile.maturity == "split_stack_executable"
    assert diagnostics_summary.profile.maturity == "split_stack_executable"
    assert bringup_summary.profile.maturity == "split_stack_executable"
    assert readyz_payload["db_profile"]["maturity"] == "split_stack_executable"
    assert readyz_payload["models"] == ["bge-m3", "reranker"]

    expected_capability_states = {
        row["id"]: row["support_state"]
        for row in capabilities_payload["capabilities"]
    }
    diagnostics_capability_states = {
        row["id"]: row["support_state"]
        for row in diagnostics_payload["capabilities"]
    }
    assert diagnostics_capability_states == expected_capability_states
    assert bringup_summary.profile.id == diagnostics_summary.profile.id == capability_summary.profile.id
    lane_diagnostics = {
        row["lane_family"]: row
        for row in diagnostics_payload["lane_diagnostics"]
    }
    assert lane_diagnostics["sparse_vector"]["support_state"] == expected_capability_states["retrieval.sparse.vector"]
    assert lane_diagnostics["graph_traversal"]["support_state"] == expected_capability_states["retrieval.graph.traversal"]
    assert lane_diagnostics["sparse_vector"]["route_surface_declared"] is False
    assert lane_diagnostics["graph_traversal"]["route_surface_declared"] is False
    assert lane_diagnostics["sparse_vector"]["execution_mode"] == "placeholder"
    assert lane_diagnostics["graph_traversal"]["execution_mode"] == "placeholder"
    assert lane_diagnostics["sparse_vector"]["recommended_profile_id"] == "paradedb_postgres_gold_v1"
    assert lane_diagnostics["graph_traversal"]["recommended_profile_id"] == "paradedb_postgres_gold_v1"
    assert lane_diagnostics["sparse_vector"]["blocked_by_capability"] == "retrieval.sparse.vector"
    assert lane_diagnostics["graph_traversal"]["blocked_by_capability"] == "retrieval.graph.traversal"

    resolved_bm25 = resolve_search_bm25_route_executor(table="document_chunk", profile=profile)
    resolved_hybrid = resolve_search_hybrid_route_executor(
        use_bm25=True,
        use_similarity=True,
        use_sparse=False,
        profile=profile,
    )
    resolved_file = resolve_search_file_chunks_route_executor(profile=profile)

    expected_routes = {
        "search_bm25.document_chunk": resolved_bm25,
        "search_hybrid.document_chunk": resolved_hybrid,
        "search_file_chunks": resolved_file,
    }
    expected_states = {
        route_id: resolver.resolution.support_state
        for route_id, resolver in expected_routes.items()
    }
    diagnostics_states = {
        route_id: diagnostics_summary.route_support_state(route_id)
        for route_id in expected_routes.keys()
    }
    assert diagnostics_states == expected_states
    expected_lexical_support_class = {
        "search_bm25.document_chunk": "degraded_supported",
        "search_hybrid.document_chunk": "degraded_supported",
        "search_file_chunks": "degraded_supported",
    }
    assert bringup_summary.summary.route_runtime_ready is True
    assert bringup_summary.summary.declared_executable_routes_runtime_ready is True
    assert sorted(bringup_summary.route_runtime_ready_ids) == sorted(expected_routes.keys())
    assert bringup_summary.route_runtime_blocked_ids == []
    assert bringup_summary.declared_route_support == {
        route_id: expected_states[route_id] for route_id in expected_routes.keys()
    }
    assert sorted(bringup_summary.declared_executable_route_ids) == sorted(expected_routes.keys())
    assert bringup_summary.declared_optional_route_ids == []
    assert sorted(bringup_summary.declared_executable_runtime_ready_ids) == sorted(expected_routes.keys())
    assert bringup_summary.declared_executable_runtime_blocked_ids == []
    assert bringup_summary.declared_routes_runtime_ready() is True
    assert sorted(bringup_summary.lexical_degraded_route_ids) == sorted(expected_routes.keys())
    assert sorted(bringup_summary.lexical_gold_recommended_route_ids) == sorted(expected_routes.keys())
    assert bringup_summary.summary.lexical_degraded_route_count == len(expected_routes)
    assert bringup_summary.summary.lexical_gold_recommended_route_count == len(expected_routes)
    assert bringup_summary.summary.compatibility_projection_route_count == len(expected_routes)
    assert bringup_summary.summary.canonical_projection_route_count == 0
    assert bringup_summary.summary.route_lexical_support_class_counts["degraded_supported"] == len(expected_routes)
    assert bringup_summary.summary.lexical_capability_blocker_counts["retrieval.lexical.hard_constraints"] == len(expected_routes)
    assert bringup_summary.exact_lexical_constraints_recommend_gold() is True
    assert bringup_summary.compatibility_projection_reliance() is True
    assert bringup_summary.canonical_projection_coverage() is False
    assert bringup_summary.projection_ids_needing_build == []
    assert bringup_summary.backend_unreachable_planes == []
    assert bringup_summary.summary.ready_projection_count == 3
    assert bringup_summary.summary.required_projection_count == 3
    assert bringup_summary.summary.required_projection_status_counts["ready"] == 3
    assert bringup_summary.projection_building_ids == []
    assert bringup_summary.projection_failed_ids == []
    assert bringup_summary.projection_stale_ids == []
    assert bringup_summary.projection_absent_ids == []
    assert bringup_summary.building_projections() == []
    assert bringup_summary.failed_projections() == []
    assert bringup_summary.stale_projections() == []
    assert bringup_summary.absent_projections() == []
    assert readyz_payload["db_profile_diagnostics"]["boot_ready"] is True
    assert readyz_payload["db_profile_bringup"]["summary"]["route_runtime_ready"] is True
    assert readyz_payload["db_profile_bringup"]["projection_ids_needing_build"] == []
    assert readyz_payload["db_profile_bringup"]["route_runtime_blocked_ids"] == []
    assert readyz_payload["db_profile_bringup"]["backend_unreachable_planes"] == []

    for route_id, resolver in expected_routes.items():
        sdk_route = diagnostics_summary.route_executor(route_id)
        assert sdk_route is not None
        assert sdk_route.executor_id == resolver.resolution.executor_id
        assert diagnostics_summary.route_adapter_ids(route_id) == {
            lane_id: str(adapter.get("adapter_id"))
            for lane_id, adapter in resolver.resolution.lane_adapters.items()
        }
        assert diagnostics_summary.route_lane_backends(route_id) == {
            lane_id: str(adapter.get("backend"))
            for lane_id, adapter in resolver.resolution.lane_adapters.items()
        }
        assert diagnostics_summary.route_projection_targets(route_id) == resolver.resolution.projection_targets
        assert diagnostics_summary.route_projection_target_backend_names(route_id) == {
            str(entry["projection_id"]): str(entry["target_backend_name"])
            for entry in resolver.resolution.projection_targets
        }
        assert sdk_route.compatibility_projection_reliance is True
        assert sorted(sdk_route.compatibility_projection_target_ids) == sorted(
            str(entry["projection_id"])
            for entry in resolver.resolution.projection_targets
            if str(entry.get("authority_model") or "").endswith("_compatibility")
        )
        for projection_id in resolver.resolution.projection_descriptors:
            projection_entry = bringup_summary.projection_diagnostics.projection(projection_id)
            assert projection_entry is not None
            route_target = diagnostics_summary.route_executor(route_id).projection_target_map()[projection_id]
            assert route_target["authority_model"] == projection_entry.materialization_target["authority_model"]
            assert route_target["record_schema"] == projection_entry.materialization_target["record_schema"]
            assert route_target["target_backend_name"] == projection_entry.materialization_target["target_backend_name"]
        assert diagnostics_summary.route_lexical_support_class(route_id) == expected_lexical_support_class[route_id]
        lexical_states = diagnostics_summary.route_lexical_capability_states(route_id)
        assert lexical_states["retrieval.lexical.advanced_operators"] == "degraded"
        assert lexical_states["retrieval.lexical.hard_constraints"] == "unsupported"
        assert "retrieval.lexical.proximity" in diagnostics_summary.route_lexical_degraded_capabilities(route_id)
        assert diagnostics_summary.route_lexical_unsupported_capabilities(route_id) == [
            "retrieval.lexical.hard_constraints"
        ]
        assert diagnostics_summary.route_gold_recommended_for_exact_constraints(route_id) is True
        assert diagnostics_summary.route_lexical_exact_constraint_degraded_capabilities(route_id) == [
            "retrieval.lexical.advanced_operators",
            "retrieval.lexical.phrase_boost",
            "retrieval.lexical.proximity",
        ]
        assert diagnostics_summary.route_lexical_exact_constraint_unsupported_capabilities(route_id) == [
            "retrieval.lexical.hard_constraints"
        ]
        recovery_entry = bringup_summary.route_recovery_entry(route_id)
        assert recovery_entry is not None
        assert recovery_entry.runtime_ready is True
        assert recovery_entry.projection_ready is True
        assert recovery_entry.lexical_support_class == "degraded_supported"
        assert recovery_entry.gold_recommended_for_exact_constraints is True
        assert recovery_entry.bootstrapable_blocking_projection_ids == []
        assert bringup_summary.route_prefers_gold_for_exact_constraints(route_id) is True
        assert bringup_summary.route_exact_constraint_degraded_capabilities(route_id) == [
            "retrieval.lexical.advanced_operators",
            "retrieval.lexical.phrase_boost",
            "retrieval.lexical.proximity",
        ]
        assert bringup_summary.route_exact_constraint_unsupported_capabilities(route_id) == [
            "retrieval.lexical.hard_constraints"
        ]
        if resolver.resolution.support_state == "degraded":
            assert diagnostics_summary.route_state(route_id) == "degraded_runtime_ready"
            assert diagnostics_summary.route_is_degraded(route_id) is True
        else:
            assert diagnostics_summary.route_state(route_id) == "runtime_ready"
            assert diagnostics_summary.route_is_degraded(route_id) is False
        assert diagnostics_summary.route_blocked_by_projection(route_id) is False
        assert diagnostics_summary.route_blocked_by_backend_connectivity(route_id) is False

    assert capability_summary.support_state("retrieval.lexical.advanced_operators") == "degraded"
    assert diagnostics_summary.support_state("retrieval.lexical.advanced_operators") == "degraded"
    assert capability_summary.support_state("retrieval.sparse.vector") == "unsupported"
    assert diagnostics_summary.support_state("retrieval.sparse.vector") == "unsupported"

import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.profile_bringup import build_profile_bringup_payload
from QueryLake.runtime.local_dense_sidecar import LOCAL_DENSE_SIDECAR_ADAPTER
from QueryLake.runtime.projection_contracts import DocumentChunkMaterializationRecord
from QueryLake.runtime.projection_refresh import (
    ProjectionRefreshRequest,
    build_projection_refresh_plan,
    execute_projection_refresh_plan,
    mark_projection_build_ready,
)


def test_profile_bringup_payload_aggregates_runtime_and_projection_state(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")
    metadata_store_path = tmp_path / "projection_store.json"

    mark_projection_build_ready(
        projection_id="file_chunk_lexical_projection_v1",
        projection_version="v1",
        profile_id="aws_aurora_pg_opensearch_v1",
        lane_family="lexical",
        target_backend="opensearch",
        build_revision="r1",
        path=str(metadata_store_path),
    )

    payload = build_profile_bringup_payload(metadata_store_path=str(metadata_store_path))

    assert payload["profile"]["id"] == "aws_aurora_pg_opensearch_v1"
    assert payload["representation_scopes"]["document_chunk"]["authority_model"] == "document_segment"
    route_support_v2 = {row["route_id"]: row for row in payload["route_support_v2"]}
    assert route_support_v2["search_hybrid.document_chunk"]["representation_scope"]["scope_id"] == "document_chunk"
    assert route_support_v2["search_hybrid.document_chunk"]["capability_dependencies"] == [
        "retrieval.lexical.bm25",
        "retrieval.dense.vector",
    ]
    assert payload["summary"]["configuration_ready"] is True
    assert payload["summary"]["required_projection_count"] >= 3
    assert payload["summary"]["ready_projection_count"] == 1
    assert payload["summary"]["projection_absent_count"] >= 2
    assert payload["summary"]["bootstrapable_required_projection_count"] >= 2
    assert payload["summary"]["nonbootstrapable_required_projection_count"] == 0
    assert payload["summary"]["recommended_projection_count"] >= 2
    assert payload["summary"]["recommended_ready_projection_count"] == 0
    assert payload["summary"]["recommended_projection_ids_needing_build_count"] >= 2
    assert payload["summary"]["bootstrapable_recommended_projection_count"] >= 2
    assert payload["summary"]["nonbootstrapable_recommended_projection_count"] == 0
    assert payload["summary"]["required_projection_status_counts"]["ready"] == 1
    assert "file_chunk_lexical_projection_v1" in payload["ready_projection_ids"]
    assert "document_chunk_lexical_projection_v1" in payload["projection_ids_needing_build"]
    assert "document_chunk_lexical_projection_v1" in payload["bootstrapable_required_projection_ids"]
    assert "document_chunk_lexical_projection_v1" in payload["projection_absent_ids"]
    assert "segment_lexical_projection_v1" in payload["recommended_projection_ids"]
    assert "segment_dense_projection_v1" in payload["recommended_projection_ids"]
    assert "segment_lexical_projection_v1" in payload["recommended_projection_ids_needing_build"]
    assert "segment_lexical_projection_v1" in payload["bootstrapable_recommended_projection_ids"]
    assert payload["recommended_ready_projection_ids"] == []
    assert payload["nonbootstrapable_required_projection_ids"] == []
    assert payload["nonbootstrapable_recommended_projection_ids"] == []
    assert payload["projection_building_ids"] == []
    assert payload["projection_failed_ids"] == []
    assert payload["projection_stale_ids"] == []
    assert "search_file_chunks" in payload["route_runtime_ready_ids"]
    assert "search_hybrid.document_chunk" in payload["route_runtime_blocked_ids"]
    assert payload["profile_diagnostics"]["profile"]["id"] == "aws_aurora_pg_opensearch_v1"
    assert payload["projection_diagnostics"]["profile_id"] == "aws_aurora_pg_opensearch_v1"
    projection_items = {
        item["projection_id"]: item
        for item in payload["projection_diagnostics"]["projection_items"]
    }
    assert projection_items["document_chunk_lexical_projection_v1"]["materialization_target"]["target_backend_name"] == "opensearch"
    assert projection_items["segment_lexical_projection_v1"]["materialization_target"]["authority_model"] == "document_segment"
    assert payload["summary"]["next_action_count"] >= 1
    assert any(item["kind"] == "bootstrap_projections" for item in payload["next_actions"])
    assert any(item["kind"] == "bootstrap_recommended_projections" for item in payload["next_actions"])
    assert any(item["plane"] == "projection" for item in payload["backend_targets"])
    assert payload["summary"]["projection_status_counts"]["ready"] == 1
    assert payload["summary"]["route_runtime_blocker_kind_counts"]["projection_not_ready"] >= 1
    assert payload["summary"]["lexical_degraded_route_count"] >= 1
    assert payload["summary"]["lexical_gold_recommended_route_count"] >= 1
    assert payload["summary"]["compatibility_projection_route_count"] >= 1
    assert payload["summary"]["compatibility_projection_target_count"] >= 1
    assert payload["summary"]["route_lexical_support_class_counts"]["degraded_supported"] >= 1
    assert payload["summary"]["lexical_capability_blocker_counts"]["retrieval.lexical.hard_constraints"] >= 1
    assert "search_hybrid.document_chunk" in payload["lexical_degraded_route_ids"]
    assert "search_hybrid.document_chunk" in payload["lexical_gold_recommended_route_ids"]
    assert "search_hybrid.document_chunk" in payload["compatibility_projection_route_ids"]
    assert "document_chunk_lexical_projection_v1" in payload["compatibility_projection_target_ids"]
    assert "segment_lexical_projection_v1" in payload["canonical_projection_target_ids"]
    assert any(item["kind"] == "prefer_gold_profile_for_exact_lexical_constraints" for item in payload["next_actions"])
    assert "document_chunk_lexical_projection_v1" in payload["route_blocked_projection_ids"]
    route_recovery = {
        item["route_id"]: item
        for item in payload["route_recovery"]
    }
    assert route_recovery["search_hybrid.document_chunk"]["runtime_ready"] is False
    assert route_recovery["search_hybrid.document_chunk"]["representation_scope_id"] == "document_chunk"
    assert route_recovery["search_hybrid.document_chunk"]["representation_scope"]["authority_model"] == "document_segment"
    assert route_recovery["search_hybrid.document_chunk"]["query_ir_v2"]["route_id"] == "search_hybrid.document_chunk"
    assert route_recovery["search_hybrid.document_chunk"]["projection_ir_v2"]["representation_scope_id"] == "document_chunk"
    assert route_recovery["search_hybrid.document_chunk"]["capability_dependencies"] == [
        "retrieval.lexical.bm25",
        "retrieval.dense.vector",
    ]
    assert "document_chunk_lexical_projection_v1" in route_recovery["search_hybrid.document_chunk"]["bootstrapable_blocking_projection_ids"]
    assert route_recovery["search_hybrid.document_chunk"]["bootstrap_command"] is not None
    assert route_recovery["search_hybrid.document_chunk"]["lexical_support_class"] == "degraded_supported"
    assert route_recovery["search_hybrid.document_chunk"]["gold_recommended_for_exact_constraints"] is True


def test_profile_bringup_adds_specific_projection_recovery_actions(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")
    metadata_store_path = tmp_path / "projection_store.json"

    mark_projection_build_ready(
        projection_id="document_chunk_lexical_projection_v1",
        projection_version="v1",
        profile_id="aws_aurora_pg_opensearch_v1",
        lane_family="lexical",
        target_backend="opensearch",
        build_revision="r1",
        path=str(metadata_store_path),
    )
    mark_projection_build_ready(
        projection_id="document_chunk_dense_projection_v1",
        projection_version="v1",
        profile_id="aws_aurora_pg_opensearch_v1",
        lane_family="dense",
        target_backend="opensearch",
        build_revision="r2",
        path=str(metadata_store_path),
    )
    mark_projection_build_ready(
        projection_id="file_chunk_lexical_projection_v1",
        projection_version="v1",
        profile_id="aws_aurora_pg_opensearch_v1",
        lane_family="lexical",
        target_backend="opensearch",
        build_revision="r3",
        path=str(metadata_store_path),
    )

    from QueryLake.runtime.projection_refresh import invalidate_projection_build_states

    invalidate_projection_build_states(
        projection_id="document_chunk_lexical_projection_v1",
        projection_version="v1",
        profile_id="aws_aurora_pg_opensearch_v1",
        lane_families=["lexical"],
        invalidated_by=["document_updated"],
        path=str(metadata_store_path),
    )

    payload = build_profile_bringup_payload(metadata_store_path=str(metadata_store_path))
    action_kinds = {item["kind"] for item in payload["next_actions"]}
    assert "rebuild_stale_projections" in action_kinds
    stale_action = next(item for item in payload["next_actions"] if item["kind"] == "rebuild_stale_projections")
    assert stale_action["projection_ids"] == ["document_chunk_lexical_projection_v1"]
    assert payload["projection_stale_ids"] == ["document_chunk_lexical_projection_v1"]
    assert payload["summary"]["projection_stale_count"] == 1


def test_profile_bringup_distinguishes_bootstrapable_and_nonbootstrapable_projections(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setattr(
        "QueryLake.runtime.profile_bringup.build_profile_diagnostics_payload",
        lambda *args, **kwargs: {
            "profile": {"id": "aws_aurora_pg_opensearch_v1"},
            "startup_validation": {
                "boot_ready": False,
                "configuration_ready": True,
                "route_execution_ready": False,
                "route_runtime_ready": False,
                "backend_connectivity_ready": True,
            },
            "route_summary": {
                "runtime_ready_route_ids": [],
                "runtime_blocked_route_ids": ["search_hybrid.document_chunk"],
            },
            "backend_connectivity": {},
            "route_executors": [
                {
                    "route_id": "search_hybrid.document_chunk",
                    "implemented": True,
                    "support_state": "supported",
                    "runtime_ready": False,
                    "projection_dependency_mode": "required_external_projection",
                    "projection_descriptors": ["document_chunk_lexical_projection_v1"],
                    "runtime_blockers": [
                        {
                            "kind": "projection_not_ready",
                            "projection_ids": ["document_chunk_lexical_projection_v1"],
                        }
                    ],
                }
            ],
        },
    )
    monkeypatch.setattr(
        "QueryLake.runtime.profile_bringup.build_projection_diagnostics_payload",
        lambda *args, **kwargs: {
            "projection_items": [
                {
                    "projection_id": "document_chunk_lexical_projection_v1",
                    "authority_model": "document_chunk_compatibility",
                    "support_state": "supported",
                    "executable": True,
                    "build_status": "absent",
                    "materialization_target": {"authority_model": "document_chunk_compatibility"},
                },
                {
                    "projection_id": "segment_lexical_projection_v1",
                    "authority_model": "document_segment",
                    "support_state": "supported",
                    "executable": False,
                    "build_status": "absent",
                    "materialization_target": {"authority_model": "document_segment"},
                },
            ],
            "metadata": {"build_status_counts": {"absent": 2}},
        },
    )

    payload = build_profile_bringup_payload()

    assert payload["bootstrapable_required_projection_ids"] == ["document_chunk_lexical_projection_v1"]
    assert payload["nonbootstrapable_required_projection_ids"] == []
    assert payload["bootstrapable_recommended_projection_ids"] == []
    assert payload["nonbootstrapable_recommended_projection_ids"] == ["segment_lexical_projection_v1"]
    assert payload["summary"]["bootstrapable_required_projection_count"] == 1
    assert payload["summary"]["nonbootstrapable_required_projection_count"] == 0
    assert payload["summary"]["bootstrapable_recommended_projection_count"] == 0
    assert payload["summary"]["nonbootstrapable_recommended_projection_count"] == 1
    assert any(action["kind"] == "bootstrap_projections" for action in payload["next_actions"])
    assert any(action["kind"] == "review_nonbootstrapable_recommended_projections" for action in payload["next_actions"])


def test_local_profile_bringup_exposes_v2_manifest_and_local_route_ids(monkeypatch):
    LOCAL_DENSE_SIDECAR_ADAPTER.reset()
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "sqlite_fts5_dense_sidecar_local_v1")
    payload = build_profile_bringup_payload()

    assert payload["profile"]["id"] == "sqlite_fts5_dense_sidecar_local_v1"
    assert payload["representation_scopes"]["document_chunk"]["authority_model"] == "document_segment"
    assert payload["local_profile"]["maturity"] == "embedded_supported"
    assert payload["local_profile"]["docs_ref"] == "docs/database/LOCAL_PROFILE_V1.md"
    assert payload["local_profile"]["promotion_docs_ref"] == "docs/database/LOCAL_PROFILE_PROMOTION_BAR.md"
    local_support = {row["route_id"]: row for row in payload["local_profile"]["support_matrix"]}
    assert local_support["search_hybrid.document_chunk"]["representation_scope_id"] == "document_chunk"
    assert local_support["search_hybrid.document_chunk"]["lexical_support_class"] == "degraded_supported"
    assert local_support["search_file_chunks"]["representation_scope_id"] == "file_chunk"
    promotion = payload["local_profile"]["promotion_status"]
    assert promotion["declared_scope_frozen"] is True
    assert promotion["route_execution_real"] is True
    assert promotion["projection_lifecycle_real"] is True
    assert promotion["planning_v2_surfaced"] is True
    assert promotion["query_ir_v2_complete"] is True
    assert promotion["projection_ir_v2_complete"] is True
    assert promotion["representation_scope_ids_present"] is True
    assert sorted(promotion["representation_scope_ids"]) == [
        "document_chunk",
        "document_segment_graph",
        "file_chunk",
    ]
    assert promotion["declared_executable_route_count"] == 3
    assert sorted(promotion["declared_executable_route_ids"]) == [
        "search_bm25.document_chunk",
        "search_file_chunks",
        "search_hybrid.document_chunk",
    ]
    assert promotion["declared_executable_runtime_ready_ids"] == []
    assert sorted(promotion["declared_executable_runtime_blocked_ids"]) == [
        "search_bm25.document_chunk",
        "search_file_chunks",
        "search_hybrid.document_chunk",
    ]
    assert promotion["required_projection_count"] == 3
    assert sorted(promotion["required_projection_ids"]) == [
        "document_chunk_dense_projection_v1",
        "document_chunk_lexical_projection_v1",
        "file_chunk_lexical_projection_v1",
    ]
    assert promotion["dense_sidecar_ready"] is False
    assert promotion["dense_sidecar_projection_id"] == "document_chunk_dense_projection_v1"
    assert sorted(promotion["lexical_degraded_route_ids"]) == [
        "search_bm25.document_chunk",
        "search_file_chunks",
        "search_hybrid.document_chunk",
    ]
    dense_sidecar = payload["local_profile"]["dense_sidecar"]
    assert dense_sidecar["adapter_id"] == "local_dense_sidecar_v1"
    assert dense_sidecar["execution_mode"] == "projection_backed_process_local"
    assert dense_sidecar["storage_mode"] == "metadata_backed_projection_records"
    assert dense_sidecar["runtime_contract_ready"] is False
    assert dense_sidecar["promotion_contract_ready"] is False
    assert "projection_not_ready" in list(dense_sidecar["runtime_blockers"])
    assert "projection_not_ready" in list(dense_sidecar["promotion_blockers"])
    assert dense_sidecar["ready_state_source"] == "not_ready"
    assert dense_sidecar["stats_source"] == "cache_cold"
    assert dense_sidecar["cache_lifecycle_state"] == "projection_not_ready"
    assert dense_sidecar["rebuildable_from_projection_records"] is False
    assert dense_sidecar["requires_process_warmup"] is False
    assert dense_sidecar["persisted_projection_state_available"] is False
    assert dense_sidecar["contract"]["storage_contract_version"] == "v1"
    assert dense_sidecar["contract"]["persistence_scope"] == "projection_build_state_plus_process_local_cache"
    assert dense_sidecar["contract"]["durability_level"] == "rebuildable_metadata_backed"
    assert dense_sidecar["contract"]["cache_scope"] == "process_local"
    assert dense_sidecar["contract"]["query_mode"] == "cosine_similarity_full_scan"
    assert dense_sidecar["cache_warmed"] is False
    assert dense_sidecar["record_count"] == 0
    assert dense_sidecar["embedding_dimension"] == 0
    assert dense_sidecar["projection_plan_v2"]["projection_id"] == "document_chunk_dense_projection_v1"
    route_runtime_contracts = {
        row["route_id"]: row for row in payload["local_profile"]["route_runtime_contracts"]
    }
    assert route_runtime_contracts["search_hybrid.document_chunk"]["dense_sidecar_required"] is True
    assert route_runtime_contracts["search_hybrid.document_chunk"]["dense_sidecar_ready"] is False
    assert route_runtime_contracts["search_hybrid.document_chunk"]["dense_sidecar_cache_warmed"] is False
    assert route_runtime_contracts["search_hybrid.document_chunk"]["dense_sidecar_indexed_record_count"] == 0
    assert route_runtime_contracts["search_hybrid.document_chunk"]["dense_sidecar_embedding_dimension"] == 0
    assert route_runtime_contracts["search_hybrid.document_chunk"]["dense_sidecar_ready_state_source"] == "not_ready"
    assert route_runtime_contracts["search_hybrid.document_chunk"]["dense_sidecar_stats_source"] == "cache_cold"
    assert route_runtime_contracts["search_hybrid.document_chunk"]["dense_sidecar_cache_lifecycle_state"] == "projection_not_ready"
    assert route_runtime_contracts["search_hybrid.document_chunk"]["dense_sidecar_rebuildable_from_projection_records"] is False
    assert route_runtime_contracts["search_hybrid.document_chunk"]["dense_sidecar_requires_process_warmup"] is False
    assert route_runtime_contracts["search_hybrid.document_chunk"]["dense_sidecar_persisted_projection_state_available"] is False
    assert route_runtime_contracts["search_hybrid.document_chunk"]["dense_sidecar_contract"]["adapter_id"] == "local_dense_sidecar_v1"
    assert route_runtime_contracts["search_hybrid.document_chunk"]["query_ir_v2_template"]["route_id"] == "search_hybrid.document_chunk"
    assert route_runtime_contracts["search_hybrid.document_chunk"]["projection_ir_v2"]["representation_scope_id"] == "document_chunk"
    assert route_runtime_contracts["search_bm25.document_chunk"]["dense_sidecar_required"] is False
    route_support_v2 = {row["route_id"]: row for row in payload["route_support_v2"]}
    assert route_support_v2["search_bm25.document_chunk"]["representation_scope"]["scope_id"] == "document_chunk"
    assert route_support_v2["search_file_chunks"]["representation_scope"]["scope_id"] == "file_chunk"

    route_recovery = {item["route_id"]: item for item in payload["route_recovery"]}
    assert route_recovery["search_hybrid.document_chunk"]["executor_id"] == "sqlite_local.search_hybrid.document_chunk.v1"
    assert route_recovery["search_hybrid.document_chunk"]["representation_scope_id"] == "document_chunk"
    assert route_recovery["search_hybrid.document_chunk"]["runtime_ready"] is False
    assert route_recovery["search_hybrid.document_chunk"]["planning_v2"]["query_ir_v2_template"]["route_id"] == "search_hybrid.document_chunk"
    assert route_recovery["search_hybrid.document_chunk"]["planning_v2"]["projection_ir_v2"]["representation_scope_id"] == "document_chunk"
    assert route_recovery["search_hybrid.document_chunk"]["capability_dependencies"] == [
        "retrieval.lexical.bm25",
        "retrieval.dense.vector",
    ]
    assert "document_chunk_lexical_projection_v1" in route_recovery["search_hybrid.document_chunk"]["bootstrapable_blocking_projection_ids"]
    assert route_recovery["search_file_chunks"]["executor_id"] == "sqlite_local.search_file_chunks.v1"
    assert route_recovery["search_file_chunks"]["representation_scope"]["authority_model"] == "file_chunk"
    assert route_recovery["search_file_chunks"]["runtime_ready"] is False
    assert "file_chunk_lexical_projection_v1" in route_recovery["search_file_chunks"]["bootstrapable_blocking_projection_ids"]


def test_local_profile_bringup_uses_persisted_dense_sidecar_stats_when_cache_is_cold(monkeypatch, tmp_path):
    LOCAL_DENSE_SIDECAR_ADAPTER.reset()
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "sqlite_fts5_dense_sidecar_local_v1")
    metadata_store_path = tmp_path / "local_profile_projection_store.json"
    monkeypatch.setattr(
        "QueryLake.runtime.local_dense_sidecar.fetch_projection_materialization_records",
        lambda database, target: [
            DocumentChunkMaterializationRecord(id="chunk_a", text="alpha", embedding=[1.0, 0.0, 0.0]),
            DocumentChunkMaterializationRecord(id="chunk_b", text="beta", embedding=[0.0, 1.0, 0.0]),
        ],
    )

    for projection_id in [
        "document_chunk_lexical_projection_v1",
        "file_chunk_lexical_projection_v1",
    ]:
        mark_projection_build_ready(
            projection_id=projection_id,
            projection_version="v1",
            profile_id="sqlite_fts5_dense_sidecar_local_v1",
            lane_family="lexical",
            target_backend="sqlite_fts5",
            build_revision=f"{projection_id}:ready",
            path=str(metadata_store_path),
        )

    dense_plan = build_projection_refresh_plan(
        ProjectionRefreshRequest(
            projection_id="document_chunk_dense_projection_v1",
            projection_version="v1",
            collection_ids=["c1"],
        ),
        profile=None,
        metadata_store_path=str(metadata_store_path),
    )
    execute_projection_refresh_plan(
        dense_plan,
        database=object(),
        metadata_store_path=str(metadata_store_path),
    )
    LOCAL_DENSE_SIDECAR_ADAPTER.reset()

    payload = build_profile_bringup_payload(metadata_store_path=str(metadata_store_path))
    dense_sidecar = payload["local_profile"]["dense_sidecar"]
    route_runtime_contracts = {
        row["route_id"]: row for row in payload["local_profile"]["route_runtime_contracts"]
    }

    assert dense_sidecar["ready"] is True
    assert dense_sidecar["runtime_contract_ready"] is True
    assert dense_sidecar["promotion_contract_ready"] is True
    assert dense_sidecar["runtime_blockers"] == []
    assert dense_sidecar["promotion_blockers"] == []
    assert dense_sidecar["cache_warmed"] is True
    assert dense_sidecar["record_count"] == 2
    assert dense_sidecar["embedding_dimension"] == 3
    assert dense_sidecar["ready_state_source"] == "persisted_projection_build_state"
    assert dense_sidecar["stats_source"] == "persisted_projection_build_state"
    assert dense_sidecar["cache_lifecycle_state"] == "cache_warmed_persisted_metadata"
    assert dense_sidecar["rebuildable_from_projection_records"] is True
    assert dense_sidecar["requires_process_warmup"] is False
    assert dense_sidecar["persisted_projection_state_available"] is True
    assert route_runtime_contracts["search_hybrid.document_chunk"]["dense_sidecar_ready"] is True
    assert route_runtime_contracts["search_hybrid.document_chunk"]["dense_sidecar_cache_warmed"] is True
    assert route_runtime_contracts["search_hybrid.document_chunk"]["dense_sidecar_indexed_record_count"] == 2
    assert route_runtime_contracts["search_hybrid.document_chunk"]["dense_sidecar_ready_state_source"] == "persisted_projection_build_state"
    assert route_runtime_contracts["search_hybrid.document_chunk"]["dense_sidecar_stats_source"] == "persisted_projection_build_state"
    assert route_runtime_contracts["search_hybrid.document_chunk"]["dense_sidecar_cache_lifecycle_state"] == "cache_warmed_persisted_metadata"
    assert route_runtime_contracts["search_hybrid.document_chunk"]["dense_sidecar_rebuildable_from_projection_records"] is True
    assert route_runtime_contracts["search_hybrid.document_chunk"]["dense_sidecar_requires_process_warmup"] is False
    assert route_runtime_contracts["search_hybrid.document_chunk"]["dense_sidecar_persisted_projection_state_available"] is True
    assert route_runtime_contracts["search_hybrid.document_chunk"]["runtime_ready"] is True

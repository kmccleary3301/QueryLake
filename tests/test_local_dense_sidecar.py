from QueryLake.runtime.local_dense_sidecar import LOCAL_DENSE_SIDECAR_ADAPTER
from QueryLake.runtime.projection_contracts import DocumentChunkMaterializationRecord, ProjectionMaterializationTarget, ProjectionAuthorityReference


def _target() -> ProjectionMaterializationTarget:
    return ProjectionMaterializationTarget(
        projection_id="document_chunk_dense_projection_v1",
        projection_version="v1",
        lane_family="dense",
        authority_model="document_chunk_compatibility",
        source_scope="document_chunk",
        record_schema="DenseProjectionRecord",
        target_backend_family="vector_index",
        target_backend_name="local_dense_sidecar",
        authority_reference=ProjectionAuthorityReference(authority_model="document_chunk_compatibility"),
        metadata={},
    )


def test_local_dense_sidecar_warms_and_reports_stats(monkeypatch):
    LOCAL_DENSE_SIDECAR_ADAPTER.reset()
    contract = LOCAL_DENSE_SIDECAR_ADAPTER.contract().payload()
    assert contract["adapter_id"] == "local_dense_sidecar_v1"
    assert contract["storage_contract_version"] == "v1"
    assert contract["storage_mode"] == "metadata_backed_projection_records"
    assert contract["persistence_scope"] == "projection_build_state_plus_process_local_cache"
    assert contract["durability_level"] == "rebuildable_metadata_backed"
    assert contract["cache_scope"] == "process_local"
    assert contract["shared_across_processes"] is False
    assert contract["rebuild_strategy"] == "projection_rescan_on_cache_cold_or_process_start"
    assert "projection_build_state.metadata.dense_sidecar" in list(contract["artifact_layout"])
    monkeypatch.setattr(
        'QueryLake.runtime.local_dense_sidecar.fetch_projection_materialization_records',
        lambda database, target: [
            DocumentChunkMaterializationRecord(id='a', text='x', embedding=[1.0, 0.0, 0.0]),
            DocumentChunkMaterializationRecord(id='b', text='y', embedding=[0.0, 1.0, 0.0]),
        ],
    )
    target = _target()
    stats_before = LOCAL_DENSE_SIDECAR_ADAPTER.inspect_target(target)
    assert stats_before['cache_warmed'] is False
    assert stats_before['stats_source'] == 'cache_cold'
    status_before = LOCAL_DENSE_SIDECAR_ADAPTER.status_payload(
        projection_id="document_chunk_dense_projection_v1",
        build_status="absent",
        executable=False,
        requiring_route_ids=["search_hybrid.document_chunk"],
        materialization_target=target.model_dump(),
    )
    assert status_before["runtime_contract_ready"] is False
    assert status_before["promotion_contract_ready"] is False
    assert status_before["lifecycle_state"] == "blocked_projection_not_ready"
    assert status_before["cache_lifecycle_state"] == "projection_not_ready"
    assert status_before["rebuildable_from_projection_records"] is False
    assert status_before["requires_process_warmup"] is False
    assert status_before["persisted_projection_state_available"] is False
    assert status_before["runtime_blockers"] == ["projection_not_ready", "adapter_not_executable"]
    assert status_before["promotion_blockers"] == ["projection_not_ready", "adapter_not_executable"]
    ranked = LOCAL_DENSE_SIDECAR_ADAPTER.search_projection(None, target=target, query_embedding=[1.0, 0.0, 0.0], limit=5)
    assert ranked[0][0].id == 'a'
    stats_after = LOCAL_DENSE_SIDECAR_ADAPTER.inspect_target(target)
    assert stats_after['cache_warmed'] is True
    assert stats_after['record_count'] == 2
    assert stats_after['embedding_dimension'] == 3
    assert stats_after['stats_source'] == 'process_local_cache'
    status_after = LOCAL_DENSE_SIDECAR_ADAPTER.status_payload(
        projection_id="document_chunk_dense_projection_v1",
        build_status="ready",
        executable=True,
        requiring_route_ids=["search_hybrid.document_chunk"],
        materialization_target=target.model_dump(),
    )
    assert status_after["runtime_contract_ready"] is True
    assert status_after["promotion_contract_ready"] is True
    assert status_after["lifecycle_state"] == "ready_cache_warmed"
    assert status_after["cache_lifecycle_state"] == "cache_warmed_process_local"
    assert status_after["rebuildable_from_projection_records"] is True
    assert status_after["requires_process_warmup"] is False
    assert status_after["persisted_projection_state_available"] is False
    assert status_after["runtime_blockers"] == []
    assert status_after["promotion_blockers"] == []


def test_local_dense_sidecar_uses_persisted_projection_build_state_when_cache_is_cold():
    LOCAL_DENSE_SIDECAR_ADAPTER.reset()
    target = _target()
    status = LOCAL_DENSE_SIDECAR_ADAPTER.status_payload(
        projection_id="document_chunk_dense_projection_v1",
        build_status="ready",
        executable=True,
        requiring_route_ids=["search_hybrid.document_chunk"],
        materialization_target=target.model_dump(),
        persisted_dense_sidecar={
            "cache_warmed": True,
            "record_count": 2,
            "embedding_dimension": 3,
            "cache_key": "persisted-key",
        },
    )
    assert status["ready"] is True
    assert status["runtime_contract_ready"] is True
    assert status["promotion_contract_ready"] is True
    assert status["cache_warmed"] is True
    assert status["record_count"] == 2
    assert status["embedding_dimension"] == 3
    assert status["cache_key"] == "persisted-key"
    assert status["stats_source"] == "persisted_projection_build_state"
    assert status["ready_state_source"] == "persisted_projection_build_state"
    assert status["lifecycle_state"] == "ready_cache_warmed"
    assert status["cache_lifecycle_state"] == "cache_warmed_persisted_metadata"
    assert status["rebuildable_from_projection_records"] is True
    assert status["requires_process_warmup"] is False
    assert status["persisted_projection_state_available"] is True
    assert status["runtime_blockers"] == []
    assert status["promotion_blockers"] == []

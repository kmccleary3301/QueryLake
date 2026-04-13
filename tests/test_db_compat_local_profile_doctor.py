from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.db_compat_local_profile_doctor import main
from QueryLake.runtime.local_dense_sidecar import LOCAL_DENSE_SIDECAR_ADAPTER


def test_local_profile_doctor_reports_blocked_state(capsys):
    LOCAL_DENSE_SIDECAR_ADAPTER.reset()
    assert main([]) == 0
    out = capsys.readouterr().out
    assert "profile: sqlite_fts5_dense_sidecar_local_v1" in out
    assert "dense_sidecar_ready: False" in out
    assert "dense_sidecar_cache_warmed: False" in out
    assert "dense_sidecar_record_count: 0" in out
    assert "dense_sidecar_ready_state_source: not_ready" in out
    assert "dense_sidecar_lifecycle_state: blocked_projection_not_ready" in out
    assert "dense_sidecar_cache_lifecycle_state: projection_not_ready" in out
    assert "dense_sidecar_stats_source: cache_cold" in out
    assert "dense_sidecar_rebuildable_from_projection_records: False" in out
    assert "dense_sidecar_requires_process_warmup: False" in out
    assert "dense_sidecar_persisted_projection_state_available: False" in out
    assert "dense_sidecar_runtime_contract_ready: False" in out
    assert "dense_sidecar_promotion_contract_ready: False" in out
    assert "dense_sidecar_runtime_blockers: projection_not_ready" in out
    assert "dense_sidecar_contract:" in out
    assert "storage_contract_version=v1" in out
    assert "lifecycle_contract_version=v1" in out
    assert "durability_level=rebuildable_metadata_backed" in out
    assert "cache_scope=process_local" in out
    assert "support_matrix:" in out
    assert "search_bm25.document_chunk: support_state=degraded" in out
    assert "declared_executable_route_ids:" in out
    assert "required_projection_ids:" in out
    assert "projection_plan_v2_registry:" in out
    assert "scope_expansion_status:" in out
    assert "scope_expansion_contract:" in out
    assert "dense_sidecar_contract_version=v1" in out
    assert "dense_sidecar_lifecycle_contract_version=v1" in out
    assert "dense_sidecar_lifecycle_state=blocked_projection_not_ready" in out
    assert "required_before_widening: define_next_embedded_route_slice" in out


def test_local_profile_doctor_reports_ready_state(capsys):
    LOCAL_DENSE_SIDECAR_ADAPTER.reset()
    assert main(["--enable-ready-profile-projections"]) == 0
    out = capsys.readouterr().out
    assert "dense_sidecar_ready: True" in out
    assert "dense_sidecar_embedding_dimension: 0" in out
    assert "dense_sidecar_ready_state_source: projection_build_status" in out
    assert "dense_sidecar_lifecycle_state: ready_projection_backed_cache_cold" in out
    assert "dense_sidecar_cache_lifecycle_state: cache_cold_rebuildable" in out
    assert "dense_sidecar_stats_source: cache_cold" in out
    assert "dense_sidecar_rebuildable_from_projection_records: True" in out
    assert "dense_sidecar_requires_process_warmup: True" in out
    assert "dense_sidecar_persisted_projection_state_available: False" in out
    assert "dense_sidecar_runtime_contract_ready: True" in out
    assert "dense_sidecar_promotion_contract_ready: True" in out
    assert "dense_sidecar_runtime_blockers:" in out
    assert "search_hybrid.document_chunk: support_state=supported" in out
    assert "search_hybrid.document_chunk: runtime_ready=True" in out
    assert "dense_sidecar_ready_source=projection_build_status" in out
    assert "dense_sidecar_cache_lifecycle_state=cache_cold_rebuildable" in out
    assert "dense_sidecar_requires_process_warmup=True" in out
    assert "dense_sidecar_persisted_projection_state_available=False" in out
    assert "document_chunk_dense_projection_v1: backend=local_dense_sidecar" in out
    assert "scope_expansion_status:" in out
    assert "scope_expansion_contract:" in out
    assert "lifecycle_contract_version=v1" in out
    assert "dense_sidecar_lifecycle_state=ready_projection_backed_cache_cold" in out
    assert "dense_sidecar_lifecycle_contract_version=v1" in out
    assert "dense_sidecar_cache_lifecycle_state=cache_cold_rebuildable" in out
    assert "dense_sidecar_rebuildable_from_projection_records=True" in out
    assert "dense_sidecar_requires_process_warmup=True" in out
    assert "dense_sidecar_persisted_projection_state_available=False" in out
    assert "required_before_widening: define_next_embedded_route_slice" in out

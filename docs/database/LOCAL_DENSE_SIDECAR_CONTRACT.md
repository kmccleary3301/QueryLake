# Local Dense-Sidecar Contract

This document is the authoritative durable reference for the embedded
`local_dense_sidecar` runtime/storage contract used by
`sqlite_fts5_dense_sidecar_local_v1`.

The current contract is intentionally narrow:

- process-local query execution against a warmed in-memory index
- projection-backed rebuildability from dense projection records
- persisted readiness metadata in projection build state
- explicit runtime and promotion blockers when the dense projection is absent

The runtime now treats the adapter as the single authority for lifecycle status:

- process-local warmed cache state is reported from the adapter registry
- persisted projection build metadata is used when the runtime cache is cold
- surrounding diagnostics, bring-up, promotion, and completion surfaces consume
  that authoritative adapter payload rather than patching lifecycle state
  independently

In addition to the coarse lifecycle state, the runtime now exposes a more exact
cache/storage lifecycle view:

- `cache_lifecycle_state`
  distinguishes whether the current state is blocked, cache-cold-but-rebuildable,
  or cache-warmed from either process-local memory or persisted build metadata
- `rebuildable_from_projection_records`
  indicates whether the sidecar can be reconstructed from ready dense projection
  materialization records
- `requires_process_warmup`
  indicates that the runtime contract is satisfied but a process-local warmup
  pass is still needed for fastest query execution
- `persisted_projection_state_available`
  indicates that ready/cached metadata is available from projection build state
  even if the process-local cache is cold

The current contract does not guarantee:

- cross-process shared index state
- durable ANN artifacts independent of projection rebuilds
- widened embedded-scope semantics beyond the current supported slice

Lifecycle states surfaced by diagnostics, bring-up, doctor output, promotion status,
and completion gates:

- `blocked_projection_not_ready`
  dense projection is not ready, so the sidecar is not runtime-usable
- `blocked_adapter_not_executable`
  dense projection is ready but the adapter is not executable for the active slice
- `ready_projection_backed_cache_cold`
  dense projection is ready, runtime contract is satisfied, and the sidecar can be
  rebuilt/warmed on demand, but the process-local cache is currently cold
- `ready_cache_warmed`
  dense projection is ready and the sidecar has a usable warmed state, sourced
  either from the process-local cache or persisted projection build metadata

Cache-lifecycle states:

- `projection_not_ready`
  dense projection is not yet ready, so the sidecar is not rebuildable
- `adapter_not_executable`
  dense projection is ready but the current embedded slice does not permit
  dense-sidecar execution
- `cache_cold_rebuildable`
  dense projection is ready and executable, but the process-local runtime cache
  is cold and should be warmed on demand
- `cache_warmed_process_local`
  the current process has already built a usable in-memory index
- `cache_warmed_persisted_metadata`
  persisted projection-build metadata reports a previously warmed/usable state
  even if the current process-local cache is cold

Machine-readable contract:

<!-- BEGIN_LOCAL_DENSE_SIDECAR_CONTRACT -->
```json
{
  "adapter_id": "local_dense_sidecar_v1",
  "artifact_layout": [
    "projection_materialization_records",
    "projection_build_state.metadata.dense_sidecar",
    "process_local_index_registry"
  ],
  "cache_lifecycle_states": [
    "projection_not_ready",
    "adapter_not_executable",
    "cache_cold_rebuildable",
    "cache_warmed_process_local",
    "cache_warmed_persisted_metadata"
  ],
  "cache_model": "process_local_index_registry",
  "cache_scope": "process_local",
  "docs_ref": "docs/database/LOCAL_DENSE_SIDECAR_CONTRACT.md",
  "durability_level": "rebuildable_metadata_backed",
  "execution_mode": "projection_backed_process_local",
  "lifecycle_contract_version": "v1",
  "lifecycle_recovery_modes": [
    "bootstrap_required_projection",
    "restore_runtime_adapter_executability",
    "warm_process_local_cache_from_projection_records",
    "none"
  ],
  "lifecycle_states": [
    "blocked_projection_not_ready",
    "blocked_adapter_not_executable",
    "ready_projection_backed_cache_cold",
    "ready_cache_warmed"
  ],
  "persistence_scope": "projection_build_state_plus_process_local_cache",
  "promotion_contract": "projection_ready_with_runtime_contract_and_build_metadata",
  "query_mode": "cosine_similarity_full_scan",
  "ready_state_sources": [
    "not_ready",
    "projection_build_status",
    "process_local_cache",
    "persisted_projection_build_state"
  ],
  "readiness_contract": "projection_ready_and_executable",
  "rebuild_strategy": "projection_rescan_on_cache_cold_or_process_start",
  "shared_across_processes": false,
  "stats_sources": [
    "cache_cold",
    "process_local_cache",
    "persisted_projection_build_state",
    "cache_error"
  ],
  "storage_contract_version": "v1",
  "storage_mode": "metadata_backed_projection_records",
  "warmup_mode": "projection_materialization_scan"
}
```
<!-- END_LOCAL_DENSE_SIDECAR_CONTRACT -->

Operational interpretation:

- `storage_contract_version=v1`
  The first embedded dense-sidecar contract. Future widening work should bump this
  only when runtime/storage guarantees materially change.
- `lifecycle_contract_version=v1`
  The first versioned lifecycle schema for cache/readiness interpretation. Future
  widening work should bump this only when lifecycle-state meanings or promotion
  expectations materially change.
- `execution_mode=projection_backed_process_local`
  The queryable index is derived from projection materialization records and
  warmed into a process-local registry.
- `storage_mode=metadata_backed_projection_records`
  Persistent truth lives in projection materialization/build metadata rather than
  a separate durable ANN artifact store.
- `durability_level=rebuildable_metadata_backed`
  The index is intentionally rebuildable instead of independently durable.
- `query_mode=cosine_similarity_full_scan`
  The current supported slice prefers simplicity and inspectability over ANN
  complexity.

Operational interpretation of the new lifecycle helpers:

- `rebuildable_from_projection_records=true`
  means the dense projection records are sufficient to reconstruct the sidecar
  without an external durable ANN artifact.
- `requires_process_warmup=true`
  means the profile is still runnable and promotion-contract-valid, but the
  process-local index should be rebuilt before the sidecar reports a warm cache.
- `persisted_projection_state_available=true`
  means projection build metadata can carry forward readiness/cache information
  across process resets even though query execution remains process-local.

The contract is also exercised directly by:

```bash
python scripts/db_compat_local_dense_sidecar_lifecycle_smoke.py --enable-ready-profile-projections
```

That smoke verifies the expected transition from:

- `ready_projection_backed_cache_cold`

to:

- `ready_cache_warmed`

See also:

- [`LOCAL_PROFILE_V1.md`](./LOCAL_PROFILE_V1.md)
- [`LOCAL_PROFILE_PROMOTION_BAR.md`](./LOCAL_PROFILE_PROMOTION_BAR.md)
- [`LOCAL_PROFILE_SCOPE_EXPANSION_CRITERIA.md`](./LOCAL_PROFILE_SCOPE_EXPANSION_CRITERIA.md)

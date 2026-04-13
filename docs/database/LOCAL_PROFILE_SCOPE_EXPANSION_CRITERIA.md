# Local Profile Scope Expansion Criteria

This document records the bar for widening `sqlite_fts5_dense_sidecar_local_v1` beyond its current supported embedded slice.

Use the current supported slice as the baseline contract. Scope expansion is a separate decision with separate checks.

## Current supported slice

The current supported embedded slice is frozen around:

- `search_bm25.document_chunk`
- `search_file_chunks`
- `search_hybrid.document_chunk`

With the current semantic contract:

- local lexical semantics are `degraded_supported`
- hard lexical constraints are `unsupported`
- sparse retrieval is `unsupported`
- graph traversal is `unsupported`

## Canonical status surface

The machine-readable status for widening the profile lives in:

- `profile_bringup.local_profile.scope_expansion_status`
- `QueryLake/runtime/local_profile_v2.py::build_local_profile_scope_expansion_contract_payload`

The helper script is:

```bash
python scripts/db_compat_local_profile_scope_expansion_status.py
python scripts/db_compat_local_profile_scope_expansion_status.py --enable-ready-profile-projections
```

The frozen contract block in this document is checked by:

```bash
python scripts/ci_db_compat_local_scope_expansion_sync.py
```

The canonical widening contract frozen from code is:

<!-- BEGIN_LOCAL_PROFILE_SCOPE_EXPANSION_CONTRACT -->
```json
{
  "current_supported_slice_frozen": true,
  "declared_executable_route_ids": [
    "search_bm25.document_chunk",
    "search_file_chunks",
    "search_hybrid.document_chunk"
  ],
  "dense_sidecar_contract_version": "v1",
  "dense_sidecar_lifecycle_contract_version": "v1",
  "dense_sidecar_docs_ref": "docs/database/LOCAL_DENSE_SIDECAR_CONTRACT.md",
  "docs_ref": "docs/database/LOCAL_PROFILE_SCOPE_EXPANSION_CRITERIA.md",
  "future_scope_candidates": [
    "local_sparse_vector_lane",
    "local_graph_traversal_lane",
    "broader_embedded_route_validation",
    "wider_embedded_parity_gate"
  ],
  "lexical_contract": {
    "graph_traversal": "unsupported",
    "hard_constraints": "unsupported",
    "operator_heavy_semantics": "degraded_supported",
    "phrase_semantics": "degraded_supported",
    "plain_lexical": "degraded_supported",
    "sparse_retrieval": "unsupported"
  },
  "maturity": "embedded_supported",
  "profile_id": "sqlite_fts5_dense_sidecar_local_v1",
  "promotion_docs_ref": "docs/database/LOCAL_PROFILE_PROMOTION_BAR.md",
  "required_before_widening": [
    "define_next_embedded_route_slice",
    "add_runtime_validation_and_completion_coverage_for_widened_slice",
    "add_parity_or_no_regression_expectations_for_widened_slice",
    "reassess_dense_sidecar_contract_for_wider_slice"
  ],
  "satisfied_now": [
    "declared_local_slice_supported",
    "declared_local_slice_runtime_ready_after_bootstrap",
    "query_ir_v2_surfaced_for_declared_slice",
    "projection_ir_v2_surfaced_for_declared_slice",
    "dense_sidecar_contract_explicit"
  ]
}
```
<!-- END_LOCAL_PROFILE_SCOPE_EXPANSION_CONTRACT -->

## What is already satisfied

- the current supported slice is frozen
- the declared executable routes are represented consistently across:
  - code
  - diagnostics
  - bring-up
  - promotion status
  - completion gates
  - docs
- the dense-sidecar contract is explicit and machine-readable:
  - storage contract version
  - lifecycle contract version
  - durability level
  - artifact layout
  - cache scope
  - rebuild strategy
  - promotion contract
- the dense-sidecar contract is surfaced in:
  - diagnostics
  - bring-up
  - doctor output
  - promotion status
  - completion gate
- Query IR V2 and Projection IR V2 are surfaced for the declared slice

## What remains before widening the slice

Scope expansion should not happen until the following are addressed for the next proposed route set:

1. Define the exact next embedded route slice.
2. Add runtime validation and completion-gate coverage for that widened slice.
3. Add parity or no-regression expectations appropriate to the widened slice.
4. Reassess whether the widened slice requires a stronger dense-sidecar storage/query contract than the current:
   - `projection_backed_process_local`
   - `metadata_backed_projection_records`
   - `cosine_similarity_full_scan`

## Retention rule

Do not widen `SUPPORTED_PROFILES.md` for the local profile until the widened route slice has:

- explicit route declarations
- required projection declarations
- V2 planning payloads
- runtime readiness logic
- smoke coverage
- completion-style validation
- docs synced to code

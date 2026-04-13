# V2 Runtime Boundary

This document describes the active V2 runtime boundary that is now live in QueryLake.

## Active path

For the supported slices, the runtime path is now:

1. route resolution
2. `QueryIRV2` construction
3. `ProjectionIRV2` construction
4. lexical/capability strictness enforcement
5. typed materialization-target resolution
6. retrieval explain
7. orchestrated execution metadata
8. route execution and bring-up recovery

The important operational point is that V2 is no longer draft-only metadata. It now participates in:

- local embedded runtime execution
- local bootstrap / bring-up / promotion
- shared search request handling
- shared lexical capability enforcement
- route explain payloads
- orchestrated retrieval metadata and stage traces
- route resolution for gold, split-stack, and local supported slices

## Canonical runtime surfaces

These are the code paths that now define the live V2 boundary:

- `QueryLake/runtime/query_ir_v2.py`
- `QueryLake/runtime/projection_ir_v2.py`
- `QueryLake/runtime/retrieval_route_executors.py`
- `QueryLake/runtime/retrieval_explain.py`
- `QueryLake/runtime/retrieval_orchestrator.py`
- `QueryLake/runtime/profile_bringup.py`
- `QueryLake/runtime/local_profile_v2.py`
- `QueryLake/api/search.py`

These surfaces should agree on:

- `route_id`
- `representation_scope_id`
- strictness policy
- lane intent
- projection dependency/buildability metadata
- planning surface

Machine-readable contract:

<!-- BEGIN_V2_RUNTIME_BOUNDARY_CONTRACT -->
```json
{
  "active_path": [
    "route_resolution",
    "query_ir_v2_construction",
    "projection_ir_v2_construction",
    "lexical_capability_enforcement",
    "typed_materialization_target_resolution",
    "retrieval_explain",
    "orchestrated_execution_metadata",
    "route_execution_and_bringup_recovery"
  ],
  "active_profiles": [
    {
      "maturity": "gold",
      "profile_id": "paradedb_postgres_gold_v1"
    },
    {
      "maturity": "split_stack_executable",
      "profile_id": "aws_aurora_pg_opensearch_v1"
    },
    {
      "maturity": "embedded_supported",
      "profile_id": "sqlite_fts5_dense_sidecar_local_v1"
    }
  ],
  "active_route_ids": [
    "search_bm25.document_chunk",
    "search_hybrid.document_chunk",
    "search_file_chunks"
  ],
  "canonical_planning_fields": [
    "route_id",
    "representation_scope_id",
    "strictness_policy",
    "lane_intent.use_dense",
    "lane_intent.use_sparse",
    "projection_ir_v2.required_targets",
    "projection_ir_v2.buildability_class",
    "capability_dependencies",
    "planning_surface"
  ],
  "canonical_runtime_surfaces": [
    "QueryLake/runtime/query_ir_v2.py",
    "QueryLake/runtime/projection_ir_v2.py",
    "QueryLake/runtime/route_planning_v2.py",
    "QueryLake/runtime/retrieval_route_executors.py",
    "QueryLake/runtime/retrieval_explain.py",
    "QueryLake/runtime/retrieval_orchestrator.py",
    "QueryLake/runtime/profile_bringup.py",
    "QueryLake/runtime/local_profile_v2.py",
    "QueryLake/runtime/local_route_execution.py",
    "QueryLake/runtime/local_dense_sidecar.py",
    "QueryLake/api/search.py"
  ],
  "contract_version": "v1",
  "docs_refs": [
    "docs/database/QUERY_IR_V2.md",
    "docs/database/PROJECTION_IR_V2.md",
    "docs/database/LOCAL_PROFILE_V1.md",
    "docs/database/LOCAL_DENSE_SIDECAR_CONTRACT.md",
    "docs/database/LOCAL_PROFILE_SCOPE_EXPANSION_CRITERIA.md",
    "docs/database/V2_RUNTIME_BOUNDARY.md"
  ],
  "transitional_areas": [
    "deeper_execution_and_refinement_paths_outside_current_supported_route_slices",
    "compatibility_era_storage_internals_behind_typed_materialization_helpers",
    "wider_embedded_slice_routes_and_semantics_not_yet_promoted"
  ],
  "validated_by": [
    "scripts/db_compat_v2_runtime_consistency.py",
    "scripts/ci_db_compat_v2_runtime_boundary_sync.py"
  ]
}
```
<!-- END_V2_RUNTIME_BOUNDARY_CONTRACT -->

## Boundary edge

The V2 boundary documented here is the completed program boundary.

The items listed in the machine-readable contract are not unfinished work inside this program. They are the explicit edge of the completed boundary:

- deeper execution/refinement paths outside the current supported route slices
- compatibility-era storage internals that still remain hidden behind typed helper seams
- wider embedded-slice routes and semantics not yet promoted into the supported local scope

The current engineering rule is:

- supported runtime work must consume typed V2 contracts first
- compatibility-era shapes must remain behind typed helper seams
- broader path widening belongs to future scope, not to the completed V2 closeout

## Related docs

- `docs/database/QUERY_IR_V2.md`
- `docs/database/PROJECTION_IR_V2.md`
- `docs/database/LOCAL_PROFILE_V1.md`
- `docs/database/LOCAL_DENSE_SIDECAR_CONTRACT.md`
- `docs/database/LOCAL_PROFILE_SCOPE_EXPANSION_CRITERIA.md`
- `docs/database/V2_PROGRAM_COMPLETION_GATE.md`
- `docs/database/V2_FUTURE_SCOPE.md`

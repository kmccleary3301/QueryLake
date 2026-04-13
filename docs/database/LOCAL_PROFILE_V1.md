# Local Profile V1

| Field | Value |
|---|---|
| Audience | engineers evaluating the next lightweight embedded QueryLake profile |
| Use this when | you need the current design and runtime status of `sqlite_fts5_dense_sidecar_local_v1` |
| Prerequisites | [`DB_COMPAT_PROFILES.md`](./DB_COMPAT_PROFILES.md), [`PROFILE_DIAGNOSTICS.md`](./PROFILE_DIAGNOSTICS.md), [`SDK_PROFILE_AWARE_CLIENTS.md`](./SDK_PROFILE_AWARE_CLIENTS.md) |
| Related docs | [`SUPPORTED_PROFILES.md`](./SUPPORTED_PROFILES.md), [`CHOOSING_A_PROFILE.md`](./CHOOSING_A_PROFILE.md), [`AUTHORITY_PROJECTION_MODEL.md`](./AUTHORITY_PROJECTION_MODEL.md), [`QUERY_IR_V2.md`](./QUERY_IR_V2.md), [`PROJECTION_IR_V2.md`](./PROJECTION_IR_V2.md), [`LOCAL_PROFILE_WORKFLOW.md`](./LOCAL_PROFILE_WORKFLOW.md), [`LOCAL_OPERATOR_WORKFLOW.md`](./LOCAL_OPERATOR_WORKFLOW.md), [`LOCAL_PROFILE_SCOPE_EXPANSION_CRITERIA.md`](./LOCAL_PROFILE_SCOPE_EXPANSION_CRITERIA.md), [`LOCAL_DENSE_SIDECAR_CONTRACT.md`](./LOCAL_DENSE_SIDECAR_CONTRACT.md), [`V2_RUNTIME_BOUNDARY.md`](./V2_RUNTIME_BOUNDARY.md) |
| Status | supported embedded/local profile for the declared narrow executable route slice |

This document describes the first supported embedded/local QueryLake profile: `sqlite_fts5_dense_sidecar_local_v1`.

## Intent

The profile is meant to provide a lighter-weight QueryLake slice for:

- local development
- notebooks and research prototypes
- low-friction demos
- small single-user corpora

It is not intended to provide gold-profile semantic parity.

## Stack shape

| Plane | Backend |
|---|---|
| Authority | `sqlite` |
| Lexical | `sqlite_fts5` |
| Dense | `local_dense_sidecar` |
| Sparse | `none` |
| Graph | `none` |

## Current declared route slice

| Route | Intended support class | Current runtime state |
|---|---|---|
| `search_hybrid.document_chunk` | local hybrid over SQLite FTS5 + dense sidecar with degraded lexical semantics vs gold | executable after local projection bootstrap |
| `search_bm25.document_chunk` | local lexical BM25-style search with degraded semantics vs gold | executable after local projection bootstrap |
| `search_file_chunks` | local file lexical retrieval with degraded semantics vs gold | executable after local projection bootstrap |
| `retrieval.sparse.vector` | unsupported | unsupported |
| `retrieval.graph.traversal` | unsupported | unsupported |

The profile maturity for this stage is best read as:

- `embedded_supported`
- executable for a narrow declared slice
- supported for the declared embedded/local slice

## Code-synced support manifest

The JSON block below is checked against the runtime local-profile contract in CI.

<!-- BEGIN_LOCAL_PROFILE_SUPPORT_MANIFEST -->
```json
{
  "authority_backend": "sqlite",
  "declared_executable_route_ids": [
    "search_bm25.document_chunk",
    "search_file_chunks",
    "search_hybrid.document_chunk"
  ],
  "dense_backend": "local_dense_sidecar",
  "dense_sidecar_projection_id": "document_chunk_dense_projection_v1",
  "docs_ref": "docs/database/LOCAL_PROFILE_V1.md",
  "lexical_backend": "sqlite_fts5",
  "maturity": "embedded_supported",
  "profile_id": "sqlite_fts5_dense_sidecar_local_v1",
  "routes": [
    {
      "capability_dependencies": [
        "retrieval.lexical.bm25",
        "retrieval.dense.vector"
      ],
      "declared_executable": true,
      "declared_optional": false,
      "lexical_support_class": "degraded_supported",
      "representation_scope_id": "document_chunk",
      "required_projection_descriptors": [
        "document_chunk_lexical_projection_v1",
        "document_chunk_dense_projection_v1"
      ],
      "route_id": "search_hybrid.document_chunk",
      "support_state": "supported"
    },
    {
      "capability_dependencies": [
        "retrieval.lexical.bm25"
      ],
      "declared_executable": true,
      "declared_optional": false,
      "lexical_support_class": "degraded_supported",
      "representation_scope_id": "document_chunk",
      "required_projection_descriptors": [
        "document_chunk_lexical_projection_v1"
      ],
      "route_id": "search_bm25.document_chunk",
      "support_state": "degraded"
    },
    {
      "capability_dependencies": [
        "retrieval.lexical.bm25"
      ],
      "declared_executable": true,
      "declared_optional": false,
      "lexical_support_class": "degraded_supported",
      "representation_scope_id": "file_chunk",
      "required_projection_descriptors": [
        "file_chunk_lexical_projection_v1"
      ],
      "route_id": "search_file_chunks",
      "support_state": "degraded"
    },
    {
      "capability_dependencies": [
        "retrieval.sparse.vector"
      ],
      "declared_executable": false,
      "declared_optional": true,
      "lexical_support_class": "unsupported",
      "representation_scope_id": "document_chunk",
      "required_projection_descriptors": [],
      "route_id": "retrieval.sparse.vector",
      "support_state": "unsupported"
    },
    {
      "capability_dependencies": [
        "retrieval.graph.traversal"
      ],
      "declared_executable": false,
      "declared_optional": true,
      "lexical_support_class": "unsupported",
      "representation_scope_id": "document_segment_graph",
      "required_projection_descriptors": [],
      "route_id": "retrieval.graph.traversal",
      "support_state": "unsupported"
    }
  ]
}
```
<!-- END_LOCAL_PROFILE_SUPPORT_MANIFEST -->

## Current scaffolding

The profile is now a first-class target in the DB-compat system. It has:

- declared lane adapters
- local-specific route executor ids
- local-specific route executor classes
- local-specific projection writer ids
- local-specific executable projection writer scaffolds
- V2 representation-scope and route-support manifest data in:
  - capabilities
  - diagnostics
  - bring-up payloads
  - SDK helper models

That means the profile is no longer just a name in the registry. It is a concrete declared execution target with honest runtime status.

## Route executor ids

Current local route executor ids:

```text
sqlite_local.search_hybrid.document_chunk.v1
sqlite_local.search_bm25.document_chunk.v1
sqlite_local.search_file_chunks.v1
```

These are local scaffold executors with a narrow real execution slice.

Today they support:

- executable local lexical retrieval over the current compatibility chunk/file models
- executable local lexical+dense hybrid retrieval over the current document-chunk compatibility model
- **plan-only** execution for `return_statement` flows

They still require the local projection/bootstrap path to mark the scoped lexical/dense projection descriptors ready before diagnostics and bring-up will classify the routes as `runtime_ready`.

They still do **not** claim:

- sparse retrieval
- graph traversal
- full gold lexical semantics
- a fully packaged standalone embedded deployment

## Projection writer ids

Current local projection-writer ids:

```text
sqlite_local.projection_writer.lexical.document_chunk_lexical_projection_v1.v1
sqlite_local.projection_writer.lexical.file_chunk_lexical_projection_v1.v1
sqlite_local.projection_writer.dense.document_chunk.v1
```

These writers exist so the local profile can participate honestly in:

- projection planning
- bootstrap reporting
- diagnostics
- future completion-gate work

Unlike the route executors, the local projection writers now perform a real local materialization/build action at the metadata-store layer. That means the local profile can already participate in:

- projection refresh planning
- projection bootstrap
- ready/stale/failed lifecycle transitions

for the currently declared embedded/local slice.

## Bring-up expectations

Today, `sqlite_fts5_dense_sidecar_local_v1` should be understood as:

- profile-aware
- manifest-aware
- diagnostics-aware
- bring-up-aware
- route-executable for the narrow scoped local slice
- a supported embedded/local profile for the declared slice

Expected current behavior:

- diagnostics will expose the local lane adapters and route executors
- bring-up will expose representation scopes and route-support metadata
- route execution will work for the narrow local lexical/dense slice once the scoped local projections are bootstrapped
- `return_statement` flows can emit local planning scaffolds
- projection writes can mark local projection build state ready through the metadata/materialization seam

The same generic profile bootstrap machinery used by the split-stack profile now applies to the local slice too. For the scoped local route surface, the relevant bootstrap targets are:

- `document_chunk_lexical_projection_v1`
- `document_chunk_dense_projection_v1`
- `file_chunk_lexical_projection_v1`

After those projections are marked `ready`, diagnostics and bring-up will classify the declared executable local routes as `runtime_ready=true`. The overall profile is now part of the supported-profile set for its declared slice. Broader embedded packaging and deeper parity remain future work, not blockers for the current supported slice.

For the dense slice specifically, the dense-sidecar is now warmed as part of the dense projection build path. A successful build of `document_chunk_dense_projection_v1` records dense-sidecar readiness metadata into projection build state, and diagnostics/bring-up can reuse that persisted metadata even after a process-local cache reset.

The embedded dense-sidecar lifecycle is surfaced more precisely than a simple
ready/not-ready boolean. In addition to the coarse lifecycle state, the local
profile now exposes:

- `cache_lifecycle_state`
  whether the sidecar is blocked, cache-cold-but-rebuildable, or already warmed
- `rebuildable_from_projection_records`
  whether the current dense projection records are sufficient to rebuild the
  process-local sidecar
- `requires_process_warmup`
  whether the profile is runnable but still benefits from an explicit warmup
- `persisted_projection_state_available`
  whether build-state metadata can carry readiness/cache information across
  process resets

Those fields are available through:

- `profile_bringup.local_profile.dense_sidecar`
- `profile_bringup.local_profile.route_runtime_contracts[*]`
- `profile_bringup.local_profile.scope_expansion_status`
- the local doctor surface
- the Python SDK helper methods documented below

Example smoke/bring-up flow:

```bash
python scripts/db_compat_profile_smoke.py \
  --profile sqlite_fts5_dense_sidecar_local_v1 \
  --enable-ready-profile-projections \
  --expect-boot-ready true \
  --expect-route-runtime-ready true \
  --expect-declared-executable-routes-runtime-ready true

python scripts/db_compat_profile_bringup_smoke.py \
  --profile sqlite_fts5_dense_sidecar_local_v1 \
  --enable-ready-profile-projections \
  --expect-boot-ready true \
  --expect-route-runtime-ready true \
  --expect-declared-executable-routes-runtime-ready true
```

There is also now a narrow completion-style gate for the local slice:

```bash
python scripts/db_compat_local_profile_completion_gate.py \
  --profile sqlite_fts5_dense_sidecar_local_v1 \
  --enable-ready-profile-projections \
  --expect-profile-implemented true \
  --expect-boot-ready true \
  --expect-route-runtime-ready true \
  --expect-declared-executable-routes-runtime-ready true
```

This is the current supported-slice state before implementing:

1. broader local authority/storage packaging depth
2. denser local retrieval fidelity and lexical nuance
3. a wider embedded-profile scope beyond the current declared slice

## Configuration

Current optional local profile root:

```bash
export QUERYLAKE_DB_PROFILE=sqlite_fts5_dense_sidecar_local_v1
export QUERYLAKE_LOCAL_PROFILE_ROOT=/path/to/local/querylake-profile
```

`QUERYLAKE_LOCAL_PROFILE_ROOT` is currently still a declared configuration surface. The runtime uses it for local-profile intent and future embedded bring-up work; it does not yet by itself enable a fully packaged local deployment.

## What “scaffold only” means

The local profile already participates in QueryLake’s compatibility/control plane. That includes:

- route resolution
- lane resolution
- representation-scope declaration
- route-support manifests
- diagnostics
- bring-up
- SDK/CLI/doc surfaces

What it does **not** yet provide is a fully packaged embedded deployment.

That boundary is intentional. It keeps the local profile honest while the authority/storage packaging work is still being threaded into the next program.

Diagnostics and bring-up now also expose a dedicated `local_profile` block with:

- `support_matrix`
- `projection_plan_v2_registry`
- `promotion_status`
- `maturity`

Those fields are the current machine-readable source of truth for local-profile promotion work.

The `promotion_status` payload now explicitly includes:

- declared executable route ids
- runtime-ready vs runtime-blocked route ids
- projection-plan V2 completeness
- representation scope ids
- dense-sidecar readiness
- required projection ids
- representation scope ids participating in the scoped local slice
- dense-sidecar readiness for the scoped hybrid route

The `dense_sidecar` payload now explicitly includes:

- `adapter_id`
- `lifecycle_state`
- `cache_lifecycle_state`
- `execution_mode`
- `storage_mode`
- `contract`
- `contract.storage_contract_version`
- `contract.lifecycle_contract_version`
- `ready_state_source`
- `stats_source`
- `runtime_contract_ready`
- `promotion_contract_ready`
- `runtime_blockers`
- `promotion_blockers`
- `ready`
- `requiring_route_ids`
- `cache_warmed`
- `record_count`
- `embedding_dimension`
- `cache_key`

The `route_runtime_contracts` payload now explicitly includes:

- `representation_scope_id`
- `required_projection_ids`
- `dense_sidecar_required`
- `dense_sidecar_ready`
- `dense_sidecar_cache_warmed`
- `dense_sidecar_indexed_record_count`
- `dense_sidecar_ready_state_source`
- `dense_sidecar_stats_source`
- `dense_sidecar_contract`
- `planning_v2`

Promotion from this narrow executable scaffold into a supported embedded profile is tracked in [`LOCAL_PROFILE_PROMOTION_BAR.md`](./LOCAL_PROFILE_PROMOTION_BAR.md).

Current scripted status surface:

```bash
python scripts/db_compat_local_profile_promotion_status.py
python scripts/db_compat_local_profile_promotion_status.py --enable-ready-profile-projections
python scripts/db_compat_local_query_smoke.py --enable-ready-profile-projections --json
```

## Lexical semantics

The local profile is intentionally honest about lexical nuance:

| Query shape | Local support class |
|---|---|
| plain lexical BM25-style query | `degraded_supported` |
| quoted phrase query | `degraded_supported` |
| boolean/operator-heavy query | `degraded_supported` |
| hard field constraints like `title:\"...\"` | `unsupported` |

Hard lexical constraints are rejected before local backend query assembly. The local route is still executable for its declared slice; it just does not claim exact gold-style constraint semantics.

The current local query smoke covers these semantic classes explicitly:

- plain lexical BM25-style search
- phrase-degraded lexical BM25-style search
- operator-degraded lexical BM25-style search
- local lexical+dense hybrid search
- file lexical retrieval
- unsupported hard lexical constraints

## Dense sidecar

The current dense-sidecar implementation is intentionally narrow:

- adapter id: `local_dense_sidecar_v1`
- storage contract version: `v1`
- execution mode: `projection_backed_process_local`
- storage mode: `metadata_backed_projection_records`
- persistence scope: `projection_build_state_plus_process_local_cache`
- durability level: `rebuildable_metadata_backed`
- artifact layout:
  - `projection_materialization_records`
  - `projection_build_state.metadata.dense_sidecar`
  - `process_local_index_registry`
- cache scope: `process_local`
- rebuild strategy: `projection_rescan_on_cache_cold_or_process_start`
- query mode: `cosine_similarity_full_scan`
- promotion contract: `projection_ready_with_runtime_contract_and_build_metadata`

This means the hybrid dense lane reads from typed dense materialization records and ranks them in-process for the current local executable slice. It is sufficient for the embedded/local MVP path, but it is not yet a packaged standalone persistent vector subsystem.

Dense-sidecar readiness is therefore established by dense projection build, not only by first query execution. The process-local cache may still be cold on a fresh process start, but bring-up and promotion surfaces can now report the persisted indexed-record statistics from the last successful dense projection build.

The runtime now distinguishes:

- `ready_state_source`
  - `not_ready`
  - `projection_build_status`
  - `persisted_projection_build_state`
- `stats_source`
  - `cache_cold`
  - `process_local_cache`
  - `persisted_projection_build_state`

That distinction matters because route runtime-readiness for the local hybrid slice is allowed to survive a process-local cache reset as long as the dense projection build state remains valid.

The dense-sidecar contract also now distinguishes:

- `runtime_blockers`
  - what prevents the local dense lane from being runnable right now
- `promotion_blockers`
  - what still blocks the dense lane from satisfying the embedded-profile promotion contract

For the current profile slice, the durable boundary is the projection build metadata and typed dense materialization records. A cold in-process cache is recoverable through the declared rebuild strategy rather than treated as loss of truth.

## Developer workflow

Use this sequence when iterating on the local profile:

```bash
export QUERYLAKE_DB_PROFILE=sqlite_fts5_dense_sidecar_local_v1

# Inspect declared scope and current blockers.
python scripts/db_compat_local_profile_promotion_status.py

# Simulate the scoped local projections being ready.
python scripts/db_compat_local_profile_promotion_status.py --enable-ready-profile-projections

# Re-run the generic profile smoke against the same local slice.
python scripts/db_compat_profile_smoke.py \
  --profile sqlite_fts5_dense_sidecar_local_v1 \
  --enable-ready-profile-projections \
  --expect-boot-ready true \
  --expect-route-runtime-ready true \
  --expect-declared-executable-routes-runtime-ready true
```

Treat the output as the current source of truth for:

- declared executable routes
- runtime-ready routes
- required projections
- V2 planning payload coverage
- lexical degradation and gold-recommendation hints


## Query smoke

```bash
python scripts/db_compat_local_query_smoke.py --enable-ready-profile-projections --json
```

The local query smoke now emits a structured payload with:

- `bringup_summary`
- `local_profile`
- per-case route execution results
- top ids for the happy-path lexical and hybrid queries
- explicit unsupported-feature payloads for hard lexical constraints
- dense-sidecar lifecycle transition before and after local hybrid execution

There is also a dedicated dense-sidecar lifecycle smoke:

```bash
python scripts/db_compat_local_dense_sidecar_lifecycle_smoke.py --enable-ready-profile-projections
```

That smoke asserts the canonical local embedded lifecycle transition:

- before query execution:
  - `lifecycle_state=ready_projection_backed_cache_cold`
  - `cache_lifecycle_state=cache_cold_rebuildable`
- after local hybrid execution:
  - `lifecycle_state=ready_cache_warmed`
  - `cache_lifecycle_state=cache_warmed_process_local`

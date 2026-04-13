# First Split-Stack Deployment Guide

[![Docs Checks](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml/badge.svg)](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml)
[![Retrieval Eval](https://github.com/kmccleary3301/QueryLake/actions/workflows/retrieval_eval.yml/badge.svg)](https://github.com/kmccleary3301/QueryLake/actions/workflows/retrieval_eval.yml)

This guide is the practical bring-up path for the first executable split-stack QueryLake profile.

| Field | Value |
|---|---|
| Audience | platform engineers, deployment operators, backend contributors |
| Use this when | staging or validating the first split-stack deployment profile end-to-end |
| Prerequisites | [`DB_COMPAT_PROFILES.md`](./DB_COMPAT_PROFILES.md), [`PROFILE_DIAGNOSTICS.md`](./PROFILE_DIAGNOSTICS.md), [`CHOOSING_A_PROFILE.md`](./CHOOSING_A_PROFILE.md) |
| Related docs | [`AUTHORITY_PROJECTION_MODEL.md`](./AUTHORITY_PROJECTION_MODEL.md), [`ADDING_A_BACKEND_PROFILE.md`](./ADDING_A_BACKEND_PROFILE.md), [`BACKEND_PROFILE_RELEASE_GATE.md`](./BACKEND_PROFILE_RELEASE_GATE.md) |
| Status | active, first split-stack target guide |

## Table of contents

- [Scope](#scope)
- [Current profile](#current-profile)
- [Environment contract](#environment-contract)
- [Minimal staging configuration](#minimal-staging-configuration)
- [Bring-up sequence](#bring-up-sequence)
- [What good diagnostics look like](#what-good-diagnostics-look-like)
- [What failure looks like](#what-failure-looks-like)
- [Current intentional limitations](#current-intentional-limitations)

## Scope

This document is intentionally narrow. It is about the current first executable split-stack profile only:

```text
aws_aurora_pg_opensearch_v1
```

It does **not** describe a generic “any backend combination” deployment process.

For a single deterministic acceptance check of the current split-stack MVP slice, use:

- [`FIRST_SPLIT_STACK_COMPLETION_GATE.md`](./FIRST_SPLIT_STACK_COMPLETION_GATE.md)

## Current profile

The current first split-stack profile means:

| Plane | Backend |
|---|---|
| Authority | Aurora PostgreSQL-compatible SQL plane |
| Lexical | OpenSearch |
| Dense | OpenSearch |
| Sparse | declared but intentionally unsupported in the first slice |
| Graph | authority-plane relations exist conceptually, but graph traversal is intentionally unsupported in the first slice |

Current executable route subset:

| Route | State | Notes |
|---|---|---|
| `search_bm25.document_chunk` | executable | degraded relative to gold lexical semantics |
| `search_hybrid.document_chunk` | executable | lexical+dense only in the first split-stack slice |
| `search_file_chunks` | executable | lexical retrieval over file-chunk projections |

## Environment contract

At minimum, the first split-stack profile requires:

| Environment variable | Meaning |
|---|---|
| `QUERYLAKE_DB_PROFILE` | active QueryLake deployment profile id |
| `QUERYLAKE_AUTHORITY_DATABASE_URL` | optional explicit Aurora/PostgreSQL authority DSN; preferred when the authority plane differs from the local default SQL engine |
| `QUERYLAKE_SEARCH_BACKEND_URL` | OpenSearch base URL |
| `QUERYLAKE_SEARCH_INDEX_NAMESPACE` | index namespace/prefix used for projection indexes |
| `QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS` | dense vector dimensions for OpenSearch k-NN mappings |
| `QUERYLAKE_DATABASE_URL` | fallback SQL authority DSN; used when `QUERYLAKE_AUTHORITY_DATABASE_URL` is unset |

Optional but useful:

| Environment variable | Meaning |
|---|---|
| `QUERYLAKE_PROFILE_DIAGNOSTICS_PROBE` | set to `1` to enable lightweight authority-plane and projection-plane reachability probing |
| `QUERYLAKE_PROFILE_DIAGNOSTICS_PROBE_TIMEOUT_SECONDS` | override the diagnostics probe timeout |

## Minimal staging configuration

```bash
export QUERYLAKE_DB_PROFILE=aws_aurora_pg_opensearch_v1
export QUERYLAKE_AUTHORITY_DATABASE_URL=postgresql://querylake_access:querylake_access_password@aurora.internal:5432/querylake_database
export QUERYLAKE_SEARCH_BACKEND_URL=https://opensearch.example.internal
export QUERYLAKE_SEARCH_INDEX_NAMESPACE=querylake
export QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS=1024
export QUERYLAKE_PROFILE_DIAGNOSTICS_PROBE=1
```

The point of this configuration is not “production-ready OpenSearch.” It is “the deployment is explicit enough that QueryLake can validate, explain, probe, and reject unsupported behavior honestly.”

## Bring-up sequence

Use this order:

1. Export the profile and OpenSearch-related configuration.
2. Start QueryLake.
3. Inspect capabilities:

```bash
curl -s http://127.0.0.1:8000/v1/capabilities | jq
```

4. Inspect profile diagnostics:

```bash
curl -s http://127.0.0.1:8000/v1/profile-diagnostics | jq
```

5. Inspect projection diagnostics:

```bash
curl -s http://127.0.0.1:8000/v1/projection-diagnostics | jq
```

6. Inspect the projection plan:

```bash
curl -s http://127.0.0.1:8000/v1/projection-plan/explain | jq
```

7. Rebuild the required split-stack compatibility projections:

```bash
curl -s http://127.0.0.1:8000/v1/projection-refresh/run \
  -H 'content-type: application/json' \
  -d '{"projection_id":"document_chunk_lexical_projection_v1","collection_ids":["c1"],"metadata":{"force_rebuild":true}}' | jq

curl -s http://127.0.0.1:8000/v1/projection-refresh/run \
  -H 'content-type: application/json' \
  -d '{"projection_id":"document_chunk_dense_projection_v1","collection_ids":["c1"],"metadata":{"force_rebuild":true}}' | jq

curl -s http://127.0.0.1:8000/v1/projection-refresh/run \
  -H 'content-type: application/json' \
  -d '{"projection_id":"file_chunk_lexical_projection_v1","collection_ids":["c1"],"metadata":{"force_rebuild":true}}' | jq
```

8. Re-check profile diagnostics and confirm required routes are runtime-ready:

```bash
curl -s http://127.0.0.1:8000/v1/profile-diagnostics | jq '.startup_validation'
```

Only after those diagnostics are coherent should you treat the split-stack deployment as a meaningful test environment.

### Bootstrap the required projections in one step

For the current split-stack slice, the fastest practical bootstrap path is the dedicated helper:

```bash
python scripts/db_compat_profile_bootstrap.py \
  --profile aws_aurora_pg_opensearch_v1 \
  --metadata-store-path .querylake_projection_metadata.json \
  --validate-runtime-ready
```

Use `--projection-id` one or more times to bootstrap a narrower subset:

```bash
python scripts/db_compat_profile_bootstrap.py \
  --profile aws_aurora_pg_opensearch_v1 \
  --projection-id document_chunk_lexical_projection_v1 \
  --projection-id document_chunk_dense_projection_v1
```

The bootstrap output includes:

| Field | Meaning |
|---|---|
| `bootstrap_report.projection_ids` | projections the command attempted to materialize |
| `bootstrap_report.projection_items[*].status_before` | per-projection status before the bootstrap run |
| `bootstrap_report.projection_items[*].status_after` | per-projection status after the bootstrap run |
| `bootstrap_report.projection_items[*].executed_action_count` | per-projection rebuild operations actually executed |
| `bootstrap_report.projection_items[*].skipped_action_count` | per-projection actions skipped because execution was unnecessary or unsupported |
| `bootstrap_report.projection_items[*].build_revision` | last applied build revision for that projection lane |
| `bootstrap_report.projection_items[*].runtime_executable` | whether the active profile can actually materialize that projection |
| `bootstrap_report.projection_items[*].support_state` | support contract for the projection lane on the active profile |
| `bootstrap_report.projection_items[*].lifecycle_outcome` | normalized operator-facing lifecycle classification such as `materialized_from_absent`, `refreshed_from_stale`, `unchanged_ready`, or `failed` |
| `bootstrap_report.projection_items[*].error_summary` | per-projection failure reason when a bootstrap attempt fails |
| `bootstrap_report.projection_items[*].materialization_target` | explicit authority/projection target for that bootstrap item, including authority model, source scope, and target backend |
| `bootstrap_report.metadata.lifecycle_outcome_counts` | aggregate counts of bootstrap lifecycle outcomes across all requested projection ids |
| `bootstrap_report.metadata.materialized_projection_ids` | projection ids successfully created from an `absent` state during this bootstrap run |
| `bootstrap_report.metadata.refreshed_projection_ids` | projection ids moved from `stale` to `ready` during this bootstrap run |
| `bootstrap_report.metadata.recovered_failed_projection_ids` | projection ids recovered from a prior failed state |
| `bootstrap_report.metadata.unchanged_ready_projection_ids` | projection ids that were already ready and did not require rebuild work |
| `profile_diagnostics_before` | bring-up snapshot captured before the bootstrap run when `--validate-runtime-ready` is enabled |
| `profile_diagnostics` | bring-up snapshot captured after the bootstrap run when `--validate-runtime-ready` is enabled |
| `bootstrap_delta` | before/after readiness delta showing recovered projections, recovered routes, and whether bootstrap improved runtime readiness |
| `bootstrap_report.executed_actions` | projections that actually rebuilt in this run |
| `bootstrap_report.skipped_actions` | projections that were already ready or otherwise did not execute |
| `bootstrap_report.ready_projection_ids` | projections confirmed `ready` after the run |
| `profile_diagnostics` | included when `--validate-runtime-ready` is supplied so operators can confirm the post-bootstrap route/runtime state immediately |

This helper is intentionally profile-aware. It only bootstraps the projections defined for the current profile slice.

When interpreting bring-up and bootstrap output, distinguish:

| Bucket | Meaning |
|---|---|
| `bootstrapable_required_projection_ids` | required projections you can build immediately on the active profile |
| `nonbootstrapable_required_projection_ids` | required projections that still block runtime but need profile/support changes rather than a bootstrap command |
| `bootstrapable_recommended_projection_ids` | optional next-step projections that are buildable now |
| `nonbootstrapable_recommended_projection_ids` | optional projections that remain declared but not buildable on the active profile |

For a single-command preflight after the bootstrap path is wired, use the make target:

```bash
make ci-db-compat-bringup
```

That target asserts the current Aurora/OpenSearch fixture slice is:

| Check | Expected state |
| --- | --- |
| `boot_ready` | `true` |
| `configuration_ready` | `true` |
| `route_runtime_ready` | `true` |
| required projections | `3 ready` |
| sparse projection | still `absent` / unsupported |
| lexical-degraded routes | surfaced explicitly |
| gold-recommended lexical routes | surfaced explicitly |

For a deterministic “build then verify” path, use the bootstrap gate:

```bash
make ci-db-compat-bootstrap
```

That target is intentionally **fixture-backed** for local/CI use. It validates the profile-aware bootstrap helper contract and then asserts the post-bootstrap bring-up surface over the current executable split-stack fixture state:

| Check | Expected state |
| --- | --- |
| `boot_ready` | `true` |
| `configuration_ready` | `true` |
| `route_runtime_ready` | `true` |
| required lexical/dense/file projections | `ready` |

For a real deployment, run `python scripts/db_compat_profile_bootstrap.py ...` directly against your configured authority/projection backends instead of relying on the fixture-backed make target.

## Fast contract smoke commands

These commands are the shortest useful operator checks for the current split-stack tranche.

### 0. Run the aggregated bring-up smoke

This is the highest-signal preflight check for the current split-stack slice because it validates the compact bring-up surface operators should actually use.

Before the required projections are ready:

```bash
python scripts/db_compat_profile_bringup_smoke.py \
  --profile aws_aurora_pg_opensearch_v1 \
  --env QUERYLAKE_SEARCH_BACKEND_URL=https://example-opensearch.local \
  --env QUERYLAKE_SEARCH_INDEX_NAMESPACE=querylake \
  --env QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS=1024 \
  --expect-boot-ready false \
  --expect-configuration-ready true \
  --expect-route-runtime-ready false \
  --expect-ready-projection-count 0 \
  --expect-projection-needing-build document_chunk_lexical_projection_v1 \
  --expect-route-runtime search_hybrid.document_chunk=false \
  --expect-route-blocker-kind search_hybrid.document_chunk=projection_not_ready
```

After the required projections are ready:

```bash
python scripts/db_compat_profile_bringup_smoke.py \
  --profile aws_aurora_pg_opensearch_v1 \
  --env QUERYLAKE_SEARCH_BACKEND_URL=https://example-opensearch.local \
  --env QUERYLAKE_SEARCH_INDEX_NAMESPACE=querylake \
  --env QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS=1024 \
  --enable-ready-split-stack-projections \
  --expect-boot-ready true \
  --expect-configuration-ready true \
  --expect-route-runtime-ready true \
  --expect-ready-projection-count 3 \
  --expect-route-runtime search_hybrid.document_chunk=true \
  --expect-route-runtime search_bm25.document_chunk=true \
  --expect-route-runtime search_file_chunks=true
```

The smoke harness now also supports explicit checks for:

| Flag family | Purpose |
| --- | --- |
| `--expect-projection-building/failed/stale/absent` | assert projection lifecycle buckets directly |
| `--expect-required-projection-status-count KEY=N` | assert summarized required-projection lifecycle counts |
| `--expect-lexical-degraded-route` | assert route ids with degraded lexical semantics |
| `--expect-lexical-gold-recommended-route` | assert route ids that should prefer the gold profile for exact lexical constraints |
| `--expect-route-lexical-support-class-count KEY=N` | assert support-class rollups such as `degraded_supported=3` |
| `--expect-lexical-capability-blocker-count KEY=N` | assert specific lexical capability blocker counts |

### 1. Confirm the blocked-but-executable state

This verifies that the profile is configured, routes are implemented, and the normal blocker is missing external projections.

```bash
python scripts/db_compat_profile_smoke.py \
  --profile aws_aurora_pg_opensearch_v1 \
  --env QUERYLAKE_SEARCH_BACKEND_URL=https://example-opensearch.local \
  --env QUERYLAKE_SEARCH_INDEX_NAMESPACE=querylake \
  --env QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS=1024 \
  --expect-boot-ready false \
  --expect-route-execution-ready true \
  --expect-route-runtime-ready false \
  --expect-route-blocker-kind search_hybrid.document_chunk=projection_not_ready \
  --expect-route-blocker-kind search_bm25.document_chunk=projection_not_ready \
  --expect-route-blocker-kind search_file_chunks=projection_not_ready
```

### 2. Confirm the runtime-ready state

This uses a synthetic projection metadata fixture to model the state after the required split-stack projections are ready.

```bash
python scripts/db_compat_profile_smoke.py \
  --profile aws_aurora_pg_opensearch_v1 \
  --env QUERYLAKE_SEARCH_BACKEND_URL=https://example-opensearch.local \
  --env QUERYLAKE_SEARCH_INDEX_NAMESPACE=querylake \
  --env QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS=1024 \
  --enable-ready-split-stack-projections \
  --expect-boot-ready true \
  --expect-route-execution-ready true \
  --expect-route-runtime-ready true \
  --expect-route-runtime search_hybrid.document_chunk=true \
  --expect-route-runtime search_bm25.document_chunk=true \
  --expect-route-runtime search_file_chunks=true
```

### 3. Run the parity harness in runtime-ready mode

This checks both the split-stack executable surface and the subset that becomes runtime-ready once required projections exist.

```bash
python scripts/db_compat_contract_parity.py \
  --cases-json tests/fixtures/db_compat_contract_parity_cases.json \
  --enable-ready-split-stack-projections \
  --min-split-executable-ratio 0.49 \
  --min-split-runtime-ready-ratio 0.49 \
  --min-runtime-ready-overlap-ratio 0.49
```

Interpret the two key ratios carefully:

| Metric | Meaning |
|---|---|
| `split_executable_ratio` | fraction of the representative route/capability surface that the split-stack profile can execute in principle |
| `split_runtime_ready_ratio` | fraction of that same surface that is actually runnable on the current deployment once required projections are accounted for |

The first tells you whether the profile slice is implemented. The second tells you whether this deployment is ready to carry that slice right now.

### 4. Run the retrieval parity gate

This is the fixture-backed retrieval quality gate for the current split-stack slice. It does **not** claim exact ranking parity. It enforces acceptance bands for:

- top-k overlap
- MRR drop versus gold
- latency expansion versus gold

```bash
python scripts/db_compat_retrieval_parity.py \
  --cases-json tests/fixtures/db_compat_retrieval_parity_cases.json \
  --gold-runs-json tests/fixtures/db_compat_retrieval_parity_gold_runs.json \
  --split-runs-json tests/fixtures/db_compat_retrieval_parity_split_runs.json \
  --gold-latency-json tests/fixtures/db_compat_retrieval_parity_gold_latency.json \
  --split-latency-json tests/fixtures/db_compat_retrieval_parity_split_latency.json \
  --k 2 \
  --min-overlap 0.80 \
  --max-mrr-drop 0.10 \
  --max-latency-ratio 1.35
```

Use this gate to answer:

- “Is the split-stack result set still recognizably close to gold?”
- “Did first-hit quality regress materially?”
- “Did latency expansion exceed the allowed band?”

For interpretation policy, see:

- [`RETRIEVAL_PARITY_GATES.md`](./RETRIEVAL_PARITY_GATES.md)

## What good diagnostics look like

You want the following properties:

| Field | Desired state |
|---|---|
| `profile.id` | `aws_aurora_pg_opensearch_v1` |
| `configuration.ready` | `true` |
| `backend_connectivity.authority.status` | `configured_unprobed` or `reachable` |
| `backend_connectivity.projection.status` | `configured_unprobed` or `reachable` |
| `route_executors[].executor_id` | OpenSearch-backed route executors, not placeholders |
| `route_executors[].projection_dependency_mode` | `required_external_projection` |
| `route_executors[].runtime_ready` | `true` after required external projections are ready |
| `startup_validation.boot_ready` | `true` after the required lexical+dense/file lexical compatibility projections are refreshed |

The important operational distinction is:

- `route_execution_ready = true` means QueryLake knows how to execute the route in principle
- `route_runtime_ready = true` means the deployment is actually ready to run it now

## Current projection surface

The first split-stack slice now has two classes of projections:

1. Compatibility projections used directly by current executable retrieval routes
   - `document_chunk_lexical_projection_v1`
   - `document_chunk_dense_projection_v1`
   - `file_chunk_lexical_projection_v1`
2. Canonical segment projections that are now materially executable, but not yet used by the public split-stack retrieval routes
   - `segment_lexical_projection_v1`
   - `segment_dense_projection_v1`

That distinction matters. QueryLake can now build canonical segment lexical/dense OpenSearch materializations from `document_segment` authority rows, even though the first public route slice still targets the compatibility document/file search surfaces.

## What failure looks like

The split-stack profile is allowed to fail in these explicit ways:

1. Missing config:
   - startup validation fails
   - diagnostics report malformed or absent requirements

2. Projection plane not yet built:
   - `route_execution_ready = true`
   - `route_runtime_ready = false`
   - lexical routes report `projection_not_ready` when the required OpenSearch lexical projection is buildable but not yet in `ready` state
   - hybrid routes now also report `projection_not_ready` when the dense compatibility projection is buildable but not yet in `ready` state

3. Unsupported retrieval semantics:
   - request returns structured `501`
   - payload explains:
     - capability
     - profile
     - support state
     - backend stack
     - hint

These are acceptable failure modes. Silent semantic drift is not.

## Current intentional limitations

These are not bugs in the first split-stack slice. They are declared scope boundaries:

- sparse-vector retrieval is intentionally unsupported
- graph traversal is intentionally unsupported
- segment-level retrieval is intentionally unsupported
- advanced lexical semantics are degraded relative to the gold stack
- hard lexical constraints are intentionally unsupported

If you need those capabilities, use:

```bash
export QUERYLAKE_DB_PROFILE=paradedb_postgres_gold_v1
```

# QueryLake Primitive/Representation V2: Final Implementation Report

This is the final implementation report for the V2 primitives + embedded local profile program.

| Field | Value |
|---|---|
| Audience | maintainers, reviewers, downstream integrators |
| Use this when | you need the concise engineering answer to “what did the V2 program actually deliver?” |
| Prerequisites | [`V2_RUNTIME_BOUNDARY.md`](./V2_RUNTIME_BOUNDARY.md), [`LOCAL_PROFILE_V1.md`](./LOCAL_PROFILE_V1.md) |
| Related docs | [`V2_FUTURE_SCOPE.md`](./V2_FUTURE_SCOPE.md), [`V2_PROGRAM_COMPLETION_GATE.md`](./V2_PROGRAM_COMPLETION_GATE.md) |
| Status | final report for the completed V2 program |

## Delivered architecture

The V2 program delivered four concrete outcomes:

1. **Representation/materialization runtime boundary**
   - explicit representation scopes
   - typed materialization targets
   - typed helper seams between compatibility-era storage internals and runtime consumers

2. **Planning contract V2**
   - active `QueryIRV2` subset
   - active `ProjectionIRV2` subset
   - route-support/representation-scope manifests
   - shared runtime consistency across route resolution, request handling, explain, and orchestrated execution metadata

3. **Supported embedded local profile**
   - `sqlite_fts5_dense_sidecar_local_v1`
   - supported narrow embedded slice
   - real lexical, dense, and hybrid execution for that declared slice
   - real bootstrap/readiness/promotion/completion gates

4. **Embedded runtime contract surfaces**
   - explicit dense-sidecar storage/runtime contract
   - scope-expansion contract
   - SDK/doctor/operator workflows for the supported local slice
   - docs-sync and contract-sync gates in CI

## Supported profile outcome of the V2 program

The V2 program does not replace the earlier DB-compat program. It extends it.

After the V2 program:

- `paradedb_postgres_gold_v1` remains the canonical gold profile
- `aws_aurora_pg_opensearch_v1` remains the first supported split-stack profile
- `sqlite_fts5_dense_sidecar_local_v1` is now a supported embedded/local profile for its declared narrow slice

## What changed for the runtime architecture

- V2 planning state is no longer passive metadata
- `QueryIRV2` and `ProjectionIRV2` now survive across:
  - route resolution
  - search request handling
  - retrieval explain
  - orchestrated execution metadata
- local route executors now consume shared V2 helpers for:
  - materialization-target resolution
  - payload shaping
  - projection dependency/buildability reporting
- the embedded dense-sidecar is now a versioned runtime/storage contract, not a hidden implementation detail

## What changed for operators and client authors

- the local embedded slice is explicitly supported and bounded
- clients can inspect:
  - representation scopes
  - route support manifests
  - promotion status
  - widening blockers
  - dense-sidecar readiness
- docs, SDK, doctor output, and CI now agree on the same machine-readable contracts

## Final judgment

The V2 program is complete when judged against its stated scope:

- the V2 runtime boundary is real for the supported route slices
- the local embedded profile is supported for its declared slice
- the dense-sidecar contract is explicit and enforced
- wider embedded scope is frozen as future work instead of being left ambiguous


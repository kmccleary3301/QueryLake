# QueryLake Projection Diagnostics

[![Docs Checks](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml/badge.svg)](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml)
[![SDK Checks](https://github.com/kmccleary3301/QueryLake/actions/workflows/sdk_checks.yml/badge.svg)](https://github.com/kmccleary3301/QueryLake/actions/workflows/sdk_checks.yml)

This document defines the operator-facing projection diagnostics surface for QueryLake DB compatibility profiles.

| Field | Value |
|---|---|
| Audience | deployment operators, backend contributors, retrieval/storage engineers |
| Use this when | checking which projection descriptors are relevant to a profile, whether a projection is executable, and what its current build state is |
| Prerequisites | [`DB_COMPAT_PROFILES.md`](./DB_COMPAT_PROFILES.md), [`AUTHORITY_PROJECTION_MODEL.md`](./AUTHORITY_PROJECTION_MODEL.md) |
| Related docs | [`PROFILE_DIAGNOSTICS.md`](./PROFILE_DIAGNOSTICS.md), [`SDK_PROFILE_AWARE_CLIENTS.md`](./SDK_PROFILE_AWARE_CLIENTS.md) |
| Status | active, first operator-facing projection inspection surface |

## Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /v1/projection-diagnostics` | public/operator projection diagnostics for the active profile |
| `GET /v2/kernel/projection-diagnostics` | kernel/runtime projection diagnostics for the active profile |
| `POST /v1/projection-plan/explain` | explain the build/refresh plan for a named projection request |
| `POST /v2/kernel/projection-plan/explain` | kernel/runtime projection-plan explain surface |
| `POST /v1/projection-refresh/run` | execute the currently supported portion of a projection refresh plan |
| `POST /v2/kernel/projection-refresh/run` | kernel/runtime projection refresh execution surface |

## What the payload answers

The projection diagnostics payload is meant to answer these questions directly:

1. Which projection descriptors exist for this profile?
2. Which ones are actually executable on this deployment?
3. What backend serves each projection lane?
4. What is the current build state for each projection?
5. If a projection is not ready, is that because it is unsupported, planned, or merely absent/stale?

## Payload structure

| Section | Meaning |
|---|---|
| `profile_id` | active deployment profile id |
| `projection_items` | per-descriptor projection diagnostics rows |
| `metadata` | summary counts across support and build states |

Each `projection_items[]` row contains:

| Field | Meaning |
|---|---|
| `projection_id` | named descriptor id |
| `projection_version` | current version being inspected |
| `lane_family` | lexical, dense, sparse, or graph |
| `authority_model` | authority source model the projection is derived from |
| `source_scope` | document, segment, or compatibility scope |
| `record_schema` | declared projection record schema |
| `target_backend_family` | lexical index, dense index, sparse index, or graph index family |
| `backend_name` | active backend serving that lane on this profile |
| `support_state` | `supported`, `degraded`, `unsupported`, or `planned` |
| `executable` | whether QueryLake can currently build/refresh this projection on the active profile |
| `build_status` | `absent`, `building`, `ready`, `stale`, or `failed` |
| `action_mode` | `rebuild`, `noop`, `planned`, or `external_writer_unavailable` for the current profile |
| `invalidated_by` | scope/revision signals that force a rebuild |
| `materialization_target` | explicit authority/projection target contract for this lane, including normalized `authority_reference`, `source_scope`, `record_schema`, and `target_backend_name` |
| `build_state` | persisted build-state snapshot when available |

## Current intent

Projection diagnostics is not yet a full projection orchestration API. It is an inspection surface.

At this phase, it is used to:

- make projection descriptors first-class and inspectable,
- expose build-state truth over the network,
- show whether a profile is only *declared* vs actually *executable*,
- and make split-stack projection gaps visible before route execution fails.

The paired `projection-plan/explain` endpoint adds the next layer:

- explain which projection actions would run,
- show whether each lane would rebuild, noop, or remain planned,
- and expose persisted status snapshots before any build action is attempted.

The paired `projection-refresh/run` endpoint is intentionally stricter:

- it executes only actions with a real writer implementation behind them,
- it skips planned or external-writer-unavailable actions without marking the projection ready,
- and it returns `executed_actions` and `skipped_actions` separately so operators can see whether a deployment needs more plumbing instead of more build attempts.

This distinction now feeds directly into route diagnostics:

- routes blocked by projections that could be built if refresh were run report `projection_not_ready`
- routes blocked because the active profile has no projection writer yet report `projection_writer_unavailable`

For the current first split-stack slice, document-chunk lexical and dense compatibility projections are now both rebuildable on `aws_aurora_pg_opensearch_v1`. That means the normal blocker for those lanes is now `projection_not_ready`, not `projection_writer_unavailable`.

## Example projection-plan explain request

```json
{
  "projection_id": "document_chunk_lexical_projection_v1",
  "collection_ids": ["c1"],
  "metadata": {
    "force_rebuild": true
  }
}
```

## Example things to inspect in the explain payload

| Field | Why it matters |
|---|---|
| `actions[].mode` | whether the profile would actually rebuild or just report a planned action |
| `actions[].support_state` | whether the lane is `supported`, `degraded`, `unsupported`, or `planned` |
| `status_snapshot[]` | persisted build-state truth before action execution |
| `metadata.authority_reference` | which authority model and source scopes the projection request touches |

## Example projection-refresh run request

```json
{
  "projection_id": "document_chunk_lexical_projection_v1",
  "collection_ids": ["c1"]
}
```

Representative split-stack response shape:

```json
{
  "profile_id": "aws_aurora_pg_opensearch_v1",
  "projection_id": "document_chunk_lexical_projection_v1",
  "executed_actions": [
    {
      "lane_family": "lexical",
      "mode": "rebuild",
      "writer_id": "opensearch.projection_writer.lexical.document_chunk_lexical_projection_v1.v1"
    }
  ],
  "skipped_actions": [],
  "metadata": {
    "projection_version": "v1"
  }
}
```

## Gold vs split-stack reading

### Gold profile

On `paradedb_postgres_gold_v1`, many projection descriptors should report:

- `support_state = supported`
- `executable = true`
- `action_mode = rebuild` or `noop`

That reflects the fact that the gold stack can colocate authority and projection execution.

### First split-stack profile

On `aws_aurora_pg_opensearch_v1`, projection diagnostics should show a mix:

- lexical document/file compatibility projections: executable and rebuildable into OpenSearch compatibility indexes
- dense document compatibility projection: executable and rebuildable into the shared OpenSearch document-chunk compatibility index
- sparse and graph projections: unsupported or planned
- canonical segment lexical and dense projections: executable and rebuildable from `document_segment` authority rows into the dedicated OpenSearch segment index
- canonical segment sparse and graph projections: unsupported or planned

That distinction is intentional. QueryLake should expose the full architectural surface without pretending every projection is available on every backend profile.

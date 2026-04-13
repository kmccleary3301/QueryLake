# Query IR V2

| Field | Value |
|---|---|
| Audience | engineers working on the V2 primitive/runtime migration |
| Use this when | you need the minimal active `QueryIRV2` subset currently driving the supported V2 runtime surfaces |
| Prerequisites | [`LOCAL_PROFILE_V1.md`](./LOCAL_PROFILE_V1.md), [`AUTHORITY_PROJECTION_MODEL.md`](./AUTHORITY_PROJECTION_MODEL.md) |
| Status | active runtime subset for the supported V2 route slices |

This document records the **minimal active** `QueryIRV2` subset currently driving the supported V2 route slices.

It is intentionally smaller than the draft in `docs_tmp/`. The goal here is to document the part that is already driving runtime behavior.

## Active fields

The active V2 runtime currently uses these `QueryIRV2` fields directly:

- `route_id`
- `representation_scope_id`
- `raw_query_text`
- `normalized_query_text`
- `lexical_query_text`
- `use_dense`
- `use_sparse`
- `filter_ir.collection_ids`
- `strictness_policy`
- `planner_hints.return_statement`
- `planner_hints.query_features`

The `query_features` object currently carries:

- `quoted_phrases`
- `boolean_operators`
- `hard_constraints`

## Current runtime meaning

`QueryIRV2` now drives:

- local lexical route planning
- local hybrid route planning
- plan-only route payloads
- early hard-constraint rejection
- degraded lexical semantics classification
- shared search request handling for:
  - `search_bm25`
  - `search_hybrid`
  - `search_file_chunks`
- route-resolution planning payloads for:
  - `paradedb_postgres_gold_v1`
  - `aws_aurora_pg_opensearch_v1`
  - `sqlite_fts5_dense_sidecar_local_v1`
- retrieval explain payload construction
- orchestrated retrieval execution metadata

The currently supported local routes are:

- `search_bm25.document_chunk`
- `search_file_chunks`
- `search_hybrid.document_chunk`

## Current strictness policy use

The local translator currently maps request shape into:

- `approximate`
  - plain lexical requests without quotes/boolean operators/hard constraints
- `exact`
  - quoted phrase requests
  - boolean/operator-heavy requests
- `reject_if_not_exact`
  - hard lexical constraint requests such as fielded constraints

That does **not** mean the local profile provides exact lexical parity with the gold profile. It means the planner can distinguish:

- what can run in degraded form
- what must be rejected before backend query assembly

## Current scope boundary

The active `QueryIRV2` subset is no longer local-only.

It is the live planning subset for the current supported search-route slices across:

- `paradedb_postgres_gold_v1`
- `aws_aurora_pg_opensearch_v1`
- `sqlite_fts5_dense_sidecar_local_v1`

It is still intentionally narrower than a universal QueryLake query-planning algebra.

Outside the completed V2 program boundary:

- deeper execution/refinement paths beyond the supported search-route slices
- wider embedded-route semantics not yet promoted into the supported local slice
- future profile families that do not yet participate in the current V2 runtime boundary

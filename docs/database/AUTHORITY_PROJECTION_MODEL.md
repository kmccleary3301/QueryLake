# QueryLake Authority and Projection Model

[![Docs Checks](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml/badge.svg)](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml)
[![Retrieval Eval](https://github.com/kmccleary3301/QueryLake/actions/workflows/retrieval_eval.yml/badge.svg)](https://github.com/kmccleary3301/QueryLake/actions/workflows/retrieval_eval.yml)

This document records the current authority/projection boundary for QueryLake retrieval storage so the DB compatibility extension can evolve without conflating transactional truth with search-oriented materialization.

| Field | Value |
|---|---|
| Audience | backend contributors, storage/retrieval engineers, platform architects |
| Use this when | designing alternate DB/search profiles, planning migrations, or reasoning about rebuildable indexes |
| Prerequisites | [`DB_COMPAT_PROFILES.md`](DB_COMPAT_PROFILES.md), familiarity with current SQL tables |
| Related docs | `docs_tmp/database/QL_DB_COMPAT_EXTENSION_V1_ASSUMPTION_INVENTORY_2026-03-10.md`, `docs_tmp/database/QL_DB_COMPAT_EXTENSION_V1_EXECUTION_PLAN_2026-03-10.md` |
| Status | active design baseline; implementation-groundwork phase |

## Table of contents

- [Core rule](#core-rule)
- [What is authority today](#what-is-authority-today)
- [What is projection today](#what-is-projection-today)
- [What is transitional](#what-is-transitional)
- [Canonical future direction](#canonical-future-direction)
- [Compatibility note on DocumentChunk](#compatibility-note-on-documentchunk)
- [Projection rebuild contract](#projection-rebuild-contract)
- [Projection descriptors and build state](#projection-descriptors-and-build-state)
- [Operational invalidation signals](#operational-invalidation-signals)

## Core rule

QueryLake should treat **authority** and **projection** as separate concerns:

- **authority** stores transactional truth and source-of-record relationships,
- **projection** stores rebuildable retrieval/index artifacts optimized for lexical, dense, sparse, or graph access patterns.

The DB compatibility extension depends on this separation.

## What is authority today

Today, authority is still primarily rooted in the SQL data model around:

| Table / concept | Role |
|---|---|
| `document_raw` | source document metadata and lifecycle anchor |
| `document_segment` | canonical segment-oriented body records |
| file / file_version / file_chunk lineage | file-owned ingest authority for user file search surfaces |
| collection membership / ACL-linked SQL tables | authority for access control and retrieval scoping |
| retrieval pipeline registry and runtime control tables | authority for retrieval execution policy |

These are the records that should remain the long-term source of truth even when search/index execution moves to external systems.

## What is projection today

Today, projection exists implicitly inside search-oriented SQL tables and indexed columns:

| Projection surface | Current role |
|---|---|
| BM25-ready indexed text bodies | lexical projection |
| dense vector columns | dense retrieval projection |
| sparse vector columns | sparse retrieval projection |
| segment adjacency / graph-ready lookup structures | traversal projection |

The gold stack happens to colocate authority and projection in the same database engine. That is an implementation detail, not a long-term invariant.

## What is transitional

The following are still transitional and should not be treated as final architecture:

| Surface | Why it is transitional |
|---|---|
| `DocumentChunk` as a primary retrieval substrate | it currently mixes authority-like semantics with search-optimized materialization |
| implicit projection metadata | version/rebuild lineage is not yet first-class |
| backend-specific retrieval assumptions inside search code | these are being extracted behind explicit lane/adaptor seams |

## Canonical future direction

The target model is:

1. **authority plane**
   - canonical documents
   - versions
   - segments
   - segment relationships
   - collection and ACL truth

2. **projection plane**
   - lexical projection records
   - dense projection records
   - sparse projection records
   - graph traversal projection records
   - projection version / rebuild metadata

3. **control plane**
   - deployment profile
   - capability registry
   - lane/adaptor resolution
   - structured unsupported-feature behavior

## Compatibility note on `DocumentChunk`

`DocumentChunk` should now be treated as a **compatibility projection**, not the final authority model.

That means:

- it remains valid and useful on the gold stack,
- existing retrieval quality and APIs can continue to depend on it during migration,
- but future split-stack profiles should not treat it as the architectural center of truth.

In other words:

> `DocumentChunk` is a migration bridge and gold-profile projection surface, not the permanent canonical storage abstraction for QueryLake retrieval.

## Projection rebuild contract

The first code-level rebuild contract now exists in the runtime layer as:

- `QueryLake/runtime/projection_contracts.py`
- `QueryLake/runtime/projection_refresh.py`

Current intent:

- define projection records without coupling them to a specific authority table layout,
- define rebuild planning independently from backend execution,
- and let future split-stack profiles describe rebuild actions before they execute them.

At this phase, rebuild planning is intentionally lightweight:

- gold profile lanes are marked executable,
- planned profiles surface planned rebuild actions,
- and no alternate backend rebuild executor is wired yet.

## Projection descriptors and build state

The projection layer now has explicit descriptor and build-state contracts in code:

- `QueryLake/runtime/projection_registry.py`
- `QueryLake/runtime/projection_contracts.py`
- `QueryLake/runtime/projection_refresh.py`

What this adds:

- named projection descriptors instead of ad hoc projection ids,
- explicit record-schema mapping per lane family,
- projection build states such as `absent`, `building`, `ready`, `stale`, and `failed`,
- and a semi-persistent metadata store for projection build snapshots.

Current canonical descriptors:

| Projection id | Lane | Record schema | Authority model |
|---|---|---|---|
| `file_chunk_lexical_projection_v1` | lexical | `LexicalProjectionRecord` | `file_chunk_compatibility` |
| `document_chunk_lexical_projection_v1` | lexical | `LexicalProjectionRecord` | `document_chunk_compatibility` |
| `document_chunk_dense_projection_v1` | dense | `DenseProjectionRecord` | `document_chunk_compatibility` |
| `document_chunk_sparse_projection_v1` | sparse | `SparseProjectionRecord` | `document_chunk_compatibility` |
| `segment_lexical_projection_v1` | lexical | `LexicalProjectionRecord` | `document_segment` |
| `segment_dense_projection_v1` | dense | `DenseProjectionRecord` | `document_segment` |
| `segment_sparse_projection_v1` | sparse | `SparseProjectionRecord` | `document_segment` |
| `segment_graph_projection_v1` | graph | `GraphProjectionRecord` | `document_segment` |

This is still not a full split-stack projection engine, but it is now concrete enough to support:

- projection-plan inspection,
- projection build-state serialization,
- and honest planning for profiles that are declared but not executable yet.

One concrete runtime adoption point now exists in the OpenSearch retrieval path:

- `QueryLake/runtime/opensearch_route_execution.py`
- `QueryLake/runtime/authority_projection_access.py`

Those routes now build an explicit `ProjectionHydrationTarget` and rehydrate OpenSearch hit ids through the authority/projection access layer instead of performing an implicit `projection_id -> compatibility table` jump inside the backend-specific route code. That is intentionally small, but it is the first real retrieval-adjacent path using declared projection metadata as code, not just documentation.

That same access layer now also owns **projection source fetching** for rebuild/materialization flows:

- `QueryLake/runtime/opensearch_projection_writers.py`
- `QueryLake/runtime/authority_projection_access.py`

The OpenSearch projection writers no longer query `DocumentChunk` or `file_chunk` tables directly. They now resolve a declared projection source target and fetch source rows through `authority_projection_access.py`, using explicit authority models such as `document_chunk_compatibility`, `file_chunk_compatibility`, and now canonical `document_segment`. This keeps rebuild/materialization logic on the same declared authority/projection seam as retrieval hydration, instead of leaving projection writers as a direct-table special case.

That seam is now explicit in code through a typed materialization contract:

- `ProjectionAuthorityReference`
- `ProjectionMaterializationTarget`
- normalized materialization records in `QueryLake/runtime/projection_contracts.py`
  - `DocumentChunkMaterializationRecord`
  - `FileChunkMaterializationRecord`
  - `SegmentMaterializationRecord`

Those contracts carry the declared:

- projection identity and version
- authority model
- source scope
- record schema
- target backend family/name
- filtered authority reference used for rebuild/materialization

This matters because split-stack projection writers no longer need to invent their own private notion of “what rows should I read from which table.” They receive a declared materialization target and route that through the shared authority/projection access layer.

That shared layer now also normalizes fetched source rows into typed materialization records before they reach OpenSearch projection writers. This is a small but important architectural step: split-stack writers are no longer written against raw `DocumentChunk` ORM objects or ad hoc tuple layouts. They consume declared projection materialization records, which gives QueryLake a cleaner seam for future non-gold backends and reduces accidental coupling to compatibility-table field shapes.

For the first split-stack slice, two canonical segment descriptors are now genuinely executable on `aws_aurora_pg_opensearch_v1`:

- `segment_lexical_projection_v1`
- `segment_dense_projection_v1`

Those writers still feed the OpenSearch split-stack path, not the gold ParadeDB route family, but they are no longer descriptor-only planning objects. They now materialize from `document_segment` authority records through the same declared source-fetch contract as the compatibility projections.

The `document_chunk_*` and `file_chunk_*` descriptors are intentionally explicit compatibility descriptors. They exist so the first executable split-stack retrieval paths can refer to declared projection identity and authority model (`document_chunk_compatibility` / `file_chunk_compatibility`) instead of reaching directly into legacy SQL tables as unnamed architectural special cases.

## Operational invalidation signals

Projection planning now recognizes explicit invalidation reasons rather than treating every refresh as an opaque rebuild.

Current invalidation inputs include:

- collection scope changes
- document scope changes
- segment scope changes
- authority revision changes
- embedding revision changes
- metadata/filter revision changes
- operator semantics changes
- forced rebuild requests

The current implementation uses these signals for planning metadata and build-state transitions. Later phases will use the same signals to drive real split-stack index refresh work.

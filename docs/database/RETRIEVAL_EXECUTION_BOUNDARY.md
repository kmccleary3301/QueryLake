# QueryLake Retrieval Execution Boundary

[![Docs Checks](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml/badge.svg)](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml)
[![SDK Checks](https://github.com/kmccleary3301/QueryLake/actions/workflows/sdk_checks.yml/badge.svg)](https://github.com/kmccleary3301/QueryLake/actions/workflows/sdk_checks.yml)

This document defines the current execution boundary for retrieval routes in QueryLake's database compatibility extension.

| Field | Value |
|---|---|
| Audience | backend contributors, retrieval/runtime engineers, platform engineers |
| Use this when | adding a backend profile, changing retrieval execution code, or deciding where profile-specific logic belongs |
| Prerequisites | [`DB_COMPAT_PROFILES.md`](./DB_COMPAT_PROFILES.md), [`AUTHORITY_PROJECTION_MODEL.md`](./AUTHORITY_PROJECTION_MODEL.md) |
| Related docs | [`../../docs_tmp/database/QL_DB_COMPAT_EXTENSION_V1_EXECUTION_PLAN_2026-03-10.md`](../../docs_tmp/database/QL_DB_COMPAT_EXTENSION_V1_EXECUTION_PLAN_2026-03-10.md) |
| Status | active, phase-2 execution boundary |

## Rule of the system

`QueryLake/api/search.py` owns route semantics and orchestration. Backend-specific execution belongs behind profile-aware route executors and lane executors.

That means:

- `search.py` may validate, normalize, authorize, orchestrate, log, and shape results.
- `search.py` should **not** assemble ParadeDB-specific SQL directly.
- route executors choose the executable route path for the active profile.
- lane executors own backend-specific execution details for lexical/dense/sparse retrieval.

## Current layers

| Layer | Current module | Responsibility |
|---|---|---|
| Profile and capability contract | `QueryLake/runtime/db_compat.py` | profile registry, capability registry, startup validation, unsupported-feature contract |
| Primitive-to-lane mapping | `QueryLake/runtime/retrieval_lanes.py` | primitive id -> lane family -> adapter metadata |
| Route-executor resolution | `QueryLake/runtime/retrieval_route_executors.py` | route -> executable route executor for the active profile |
| Gold lane execution | `QueryLake/runtime/retrieval_lane_executors.py` | ParadeDB/pgvector SQL planning and execution |
| Route orchestration | `QueryLake/api/search.py` | request validation, permissions, embeddings, reranking, response shaping, observability |

## Current retrieval routes covered

| Route | Resolver | Gold executor |
|---|---|---|
| `search_hybrid.document_chunk` | `resolve_search_hybrid_route_executor(...)` | `GoldSearchHybridRouteExecutor` / `OpenSearchDocumentChunkHybridRouteExecutor` |
| `search_bm25.<table>` | `resolve_search_bm25_route_executor(...)` | `GoldSearchBM25RouteExecutor` / `OpenSearchDocumentChunkBM25RouteExecutor` |
| `search_file_chunks` | `resolve_search_file_chunks_route_executor(...)` | `GoldSearchFileChunkRouteExecutor` |

## Executable vs planned behavior

For the gold profile:

- route resolvers return executable gold route executors
- route logs include route-executor metadata
- retrieval behavior should remain unchanged

For non-gold profiles:

- executable slices resolve concrete non-gold route executors only for explicitly supported routes
- unsupported or unimplemented routes still resolve placeholder route executors
- `require_executable()` fails before query assembly for unsupported routes
- the failure is surfaced as a structured unsupported-feature error
- the route does not drift into backend-specific runtime crashes

## What belongs where

### Allowed in `search.py`

- auth and permission checks
- request assertions
- capability gating for route-level feature families
- embedding and reranking orchestration
- observability and retrieval-run logging
- result shaping into API payloads

### Not allowed in `search.py`

- backend-specific SQL string assembly
- direct references to gold executor helpers like `execute_gold_*`
- profile-specific backend branching beyond route-executor resolution

### Allowed in route executors

- route-family execution selection for the active profile
- route-local plan metadata needed to preserve result shaping
- placeholder behavior for planned/non-executable profiles

### Allowed in lane executors

- backend-specific SQL / query generation
- backend-specific bind parameters
- backend-specific statement execution

## Logging and explain requirements

Direct retrieval routes should emit route-executor metadata in operator-visible artifacts.

Current minimum requirement:

- retrieval-run metadata includes `route_executor`
- explain payloads for direct hybrid execution include `route_executor`

This metadata must include at least:

- route id
- executor id
- profile id
- implemented flag
- support state
- lane adapter metadata

## Acceptance rule for new profiles

A profile is not considered executable for a route until all of the following are true:

1. the route resolver selects a concrete executor for that profile
2. the executor's required lane adapters are implemented
3. unsupported lanes fail before query assembly
4. route-level tests prove correct status-code/error behavior
5. at least one integration smoke test exists for the route/profile pair

## Immediate next boundary after this phase

The next implementation step is **not** more route logic in `search.py`.

The next step is:

1. projection-aware execution planning
2. first split-stack executable route executors
3. profile-specific lexical/dense query translation behind those executors

That preserves the boundary instead of collapsing it.

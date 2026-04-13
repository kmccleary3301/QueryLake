# QueryLake DB Compatibility Program Status

[![Docs Checks](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml/badge.svg)](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml)

This document records the current implementation status of the QueryLake DB compatibility extension program.

| Field | Value |
|---|---|
| Audience | maintainers, reviewers, platform engineers |
| Use this when | you need the shortest accurate answer to “what has been finished, and what is intentionally left?” |
| Prerequisites | [`SUPPORTED_PROFILES.md`](./SUPPORTED_PROFILES.md), [`DB_COMPAT_COMPLETION_GATE.md`](./DB_COMPAT_COMPLETION_GATE.md) |
| Related docs | [`DB_COMPAT_IMPLEMENTATION_REPORT.md`](./DB_COMPAT_IMPLEMENTATION_REPORT.md), [`DB_COMPAT_FUTURE_SCOPE.md`](./DB_COMPAT_FUTURE_SCOPE.md), [`../DEBT/DB_COMPAT_EXTENSION_NEXT_PROGRAM.md`](../DEBT/DB_COMPAT_EXTENSION_NEXT_PROGRAM.md), `docs_tmp/database/QL_DB_COMPAT_EXTENSION_V1_EXECUTION_PLAN_2026-03-10.md` |
| Status | current scoped program completed; future expansion explicitly deferred |

## Achieved in this program

- deployment-profile registry and capability registry
- structured unsupported-feature and degraded-feature network contract
- startup profile validation and diagnostics
- retrieval lane and route-executor indirection
- gold-stack execution preserved behind explicit seams
- supported non-gold profiles:
  - `postgres_pgvector_light_v1`
  - `aws_aurora_pg_opensearch_v1`
- projection registry, projection diagnostics, bootstrap lifecycle reporting, and completion gates
- cross-surface consistency across:
  - API
  - diagnostics
  - bring-up
  - SDK
  - CLI
  - docs
  - CI
- parity and contract harnesses for the first split-stack profile

## Current supported outcome

| Profile | Outcome |
|---|---|
| `paradedb_postgres_gold_v1` | preserved as the canonical full-semantics stack |
| `postgres_pgvector_light_v1` | intentionally narrow dense-only executable profile |
| `aws_aurora_pg_opensearch_v1` | first supported split-stack profile with explicit degraded lexical semantics and explicit unsupported sparse/graph behavior |

## Completion standard for this program

The program is considered complete when all of the following are true:

- the gold profile is still fully preserved
- the first split-stack profile is fully supported for its declared route slice
- the light pgvector profile is honestly limited
- diagnostics, bring-up, completion gates, SDK, CLI, docs, and CI all agree
- remaining backend expansion work is explicitly deferred to a future program rather than silently left ambiguous

## Remaining work inside this program

None. The current scoped program is complete.

Anything beyond the supported surfaces described here is intentionally deferred and tracked in:
- [`DB_COMPAT_FUTURE_SCOPE.md`](./DB_COMPAT_FUTURE_SCOPE.md)
- [`../DEBT/DB_COMPAT_EXTENSION_NEXT_PROGRAM.md`](../DEBT/DB_COMPAT_EXTENSION_NEXT_PROGRAM.md)

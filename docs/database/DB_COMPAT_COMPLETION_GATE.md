# QueryLake DB Compatibility Completion Gate

[![Docs Checks](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml/badge.svg)](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml)

This is the final completion gate for the current DB compatibility extension program.

| Field | Value |
|---|---|
| Audience | maintainers, reviewers, release owners |
| Use this when | deciding whether the current DB compatibility program is actually complete by scope |
| Prerequisites | [`SUPPORTED_PROFILES.md`](./SUPPORTED_PROFILES.md), [`FIRST_SPLIT_STACK_COMPLETION_GATE.md`](./FIRST_SPLIT_STACK_COMPLETION_GATE.md), [`DB_COMPAT_PROGRAM_STATUS.md`](./DB_COMPAT_PROGRAM_STATUS.md) |
| Related docs | [`DB_COMPAT_FUTURE_SCOPE.md`](./DB_COMPAT_FUTURE_SCOPE.md), [`BACKEND_PROFILE_RELEASE_GATE.md`](./BACKEND_PROFILE_RELEASE_GATE.md) |
| Status | authoritative closeout gate for the current program |

## What this gate checks

The program-completion gate is intentionally narrower than “all future backend work.” It checks that the current scoped program is complete.

It verifies:

1. the authoritative supported-profile manifest in code is internally coherent
2. the currently supported profiles are exactly the ones the program promises:
   - `paradedb_postgres_gold_v1`
   - `postgres_pgvector_light_v1`
   - `aws_aurora_pg_opensearch_v1`
3. the gold profile remains the canonical recommended full-semantics stack
4. the light pgvector profile remains honestly limited
5. the first split-stack profile passes the ready-state completion gate
6. future-scope work is explicitly documented rather than silently implied

## Recommended command

```bash
python scripts/db_compat_program_completion_gate.py \
  --output /tmp/querylake_db_compat_program_completion_gate.json
```

## Interpretation

- If this gate passes, the **current DB compatibility program** is complete by its stated scope.
- It does **not** mean future backend expansion is finished.
- It does **not** mean:
  - split-stack sparse retrieval is implemented,
  - split-stack graph traversal is implemented,
  - a second split-stack backend exists,
  - or compatibility-era tables are gone everywhere.

Those are tracked explicitly in:
- [`DB_COMPAT_FUTURE_SCOPE.md`](./DB_COMPAT_FUTURE_SCOPE.md)

## Exact completion standard

Treat the DB compatibility extension program as complete only when all of the following are true:

- `paradedb_postgres_gold_v1` is still fully preserved
- `postgres_pgvector_light_v1` is still honestly limited
- `aws_aurora_pg_opensearch_v1` is complete for its declared scope
- diagnostics, bring-up, completion gates, SDK, CLI, docs, and CI all agree
- future backend expansion is clearly outside the current program boundary

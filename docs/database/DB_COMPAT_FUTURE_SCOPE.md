# QueryLake DB Compatibility Future Scope

[![Docs Checks](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml/badge.svg)](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml)

This document defines what is intentionally **outside** the scope of the current QueryLake DB compatibility extension program.

| Field | Value |
|---|---|
| Audience | maintainers, reviewers, future contributors |
| Use this when | deciding whether a missing feature is unfinished current work or future-scope work |
| Prerequisites | [`DB_COMPAT_PROGRAM_STATUS.md`](./DB_COMPAT_PROGRAM_STATUS.md), [`SUPPORTED_PROFILES.md`](./SUPPORTED_PROFILES.md) |
| Related docs | [`ADDING_A_BACKEND_PROFILE.md`](./ADDING_A_BACKEND_PROFILE.md), [`BACKEND_PROFILE_RELEASE_GATE.md`](./BACKEND_PROFILE_RELEASE_GATE.md), [`../DEBT/DB_COMPAT_EXTENSION_NEXT_PROGRAM.md`](../DEBT/DB_COMPAT_EXTENSION_NEXT_PROGRAM.md) |
| Status | authoritative out-of-scope boundary for the current program |

## Out of scope for current program completion

The current program does **not** require:

- a second fully implemented split-stack backend
- full split-stack sparse retrieval execution
- split-stack graph traversal execution
- full segment-search portability outside the gold stack
- total elimination of compatibility-era tables and models everywhere
- identical lexical scoring semantics across all backend stacks

## Why these are out of scope

The current program is about making QueryLake:

- honest about backend/profile support,
- executable on the gold stack and at least one real split-stack profile,
- explicit about degraded and unsupported retrieval semantics,
- and operationally diagnosable across API, SDK, CLI, docs, and CI.

That is enough to complete the DB compatibility extension program cleanly.

The items above are **next-program** work. They belong to:

- broader backend expansion,
- deeper retrieval portability,
- or deeper compatibility-model retirement.

## Next-program candidates

- implement a second true split-stack backend (for example `mongo_opensearch_v1`)
- add supported split-stack sparse retrieval
- add supported split-stack graph traversal
- reduce compatibility-boundary translation further in retrieval-adjacent runtime paths
- add broader cross-backend quality/performance evaluation beyond the first split-stack profile

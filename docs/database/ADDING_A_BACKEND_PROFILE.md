# Adding a QueryLake Backend Profile Without Lying to Users

[![Docs Checks](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml/badge.svg)](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml)
[![Retrieval Eval](https://github.com/kmccleary3301/QueryLake/actions/workflows/retrieval_eval.yml/badge.svg)](https://github.com/kmccleary3301/QueryLake/actions/workflows/retrieval_eval.yml)

This document defines the minimum bar for adding a new QueryLake DB/search profile honestly.

| Field | Value |
|---|---|
| Audience | backend contributors, platform engineers, architecture reviewers |
| Use this when | introducing a new authority/search stack, extending a planned profile, or deciding whether a profile is ready to be marked executable |
| Prerequisites | [`DB_COMPAT_PROFILES.md`](./DB_COMPAT_PROFILES.md), [`PROFILE_DIAGNOSTICS.md`](./PROFILE_DIAGNOSTICS.md), [`RETRIEVAL_EXECUTION_BOUNDARY.md`](./RETRIEVAL_EXECUTION_BOUNDARY.md), [`AUTHORITY_PROJECTION_MODEL.md`](./AUTHORITY_PROJECTION_MODEL.md) |
| Related docs | [`CHOOSING_A_PROFILE.md`](./CHOOSING_A_PROFILE.md), [`SDK_PROFILE_AWARE_CLIENTS.md`](./SDK_PROFILE_AWARE_CLIENTS.md) |
| Status | active, engineering policy |

## Table of contents

- [Core rule](#core-rule)
- [What counts as a profile](#what-counts-as-a-profile)
- [What you must define before code lands](#what-you-must-define-before-code-lands)
- [What must exist before a profile is executable](#what-must-exist-before-a-profile-is-executable)
- [What must exist before a profile is recommended](#what-must-exist-before-a-profile-is-recommended)
- [Support-state discipline](#support-state-discipline)
- [Required engineering checklist](#required-engineering-checklist)
- [Release gate](#release-gate)

## Core rule

Adding a profile is not the same thing as adding a backend connector.

A QueryLake profile is a product contract that defines:

- authority backend,
- projection/index backend,
- retrieval lane behavior,
- capability support states,
- degraded/unsupported semantics,
- and the diagnostics surfaces that explain all of the above.

If any of that is missing, the profile is not done.

## What counts as a profile

A real profile must declare:

- profile id
- label
- implementation status
- recommendation status
- backend stack by plane
- capability map
- configuration requirements
- route-execution support targets

These declarations belong in code, not just docs.

## What you must define before code lands

Before merging a new profile id at all, you must define:

1. The backend stack by plane:
   - authority
   - lexical
   - dense
   - sparse
   - graph
2. Capability states for every capability already tracked in `db_compat.py`.
3. Configuration requirements for that profile.
4. The intended MVP route scope.
5. Whether the profile is:
   - `planned`
   - `implemented`
   - `recommended`

If you cannot answer those questions precisely, the profile is not ready to be introduced.

## What must exist before a profile is executable

To mark a profile executable, the following must be true:

1. Startup validation exists for the profile.
2. `/v1/capabilities` reports the profile honestly.
3. `/v1/profile-diagnostics` reports route executors, blockers, and backend state honestly.
4. Unsupported capabilities fail with structured network errors.
5. At least one route executor is implemented for the routes claimed in the MVP scope.
6. Projection dependencies are declared and reflected in diagnostics.
7. At least one integration or smoke path exists for the executable route subset.

If the profile cannot pass those gates, it may be declared, but it may not be marked executable.

## What must exist before a profile is recommended

To mark a profile recommended, the following must be true:

1. It is already executable.
2. The route subset required by the target workload is stable.
3. Capability states are not misleadingly optimistic.
4. Gold-stack behavior is still preserved on the canonical profile.
5. A client/operator path can detect degraded behavior before issuing unsupported requests.
6. Documentation tells operators exactly what is degraded or unsupported.

This is intentionally a higher bar than “it runs.”

## Support-state discipline

Use support states carefully:

| State | Meaning |
|---|---|
| `supported` | executable today, with semantics QueryLake is willing to stand behind for this profile |
| `degraded` | executable today, but semantics are intentionally weaker or approximate relative to the gold profile |
| `unsupported` | intentionally not executable; must fail clearly over the network |
| `planned` | declared for architecture/migration reasons, but not executable yet |

Do not mark a feature `supported` just because a backend has a vaguely similar primitive.

Examples:

- phrase boosts implemented approximately on a split-stack profile should likely be `degraded`, not `supported`
- hard lexical constraints that are not actually enforced should be `unsupported`, not `degraded`
- a sparse lane that does not exist yet should be `unsupported` or `planned`, not `supported`

## Required engineering checklist

Use this checklist literally when introducing a new profile:

1. Add the profile declaration in `QueryLake/runtime/db_compat.py`.
2. Add configuration requirements.
3. Add MVP route support targets.
4. Add capability states for every tracked capability id.
5. Add profile docs in `docs/database/DB_COMPAT_PROFILES.md`.
6. Ensure capability IDs remain in sync with docs.
7. Add route executor resolution for the routes you claim are executable.
8. Add honest placeholders for routes you are not executing yet.
9. Add profile diagnostics coverage.
10. Add at least one smoke or contract test for the executable subset.
11. Add at least one unsupported-feature test for the non-executable subset.
12. Add operator guidance describing when *not* to use the profile.

## Release gate

Before merging a profile as executable, verify all of the following:

- `make ci-docs`
- `make ci-db-compat`
- capability docs sync passes
- profile docs sync passes
- projection descriptor sync passes
- route-executor diagnostics are correct
- unsupported-feature responses are structurally correct

The standard is simple:

> If a profile is present in QueryLake, users must be able to discover exactly what it can do, what it cannot do, and why.

Anything less is a dishonest abstraction.

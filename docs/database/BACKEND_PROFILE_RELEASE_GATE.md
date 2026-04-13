# Backend Profile Release Gate

[![Docs Checks](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml/badge.svg)](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml)
[![Retrieval Eval](https://github.com/kmccleary3301/QueryLake/actions/workflows/retrieval_eval.yml/badge.svg)](https://github.com/kmccleary3301/QueryLake/actions/workflows/retrieval_eval.yml)

This document is the explicit release gate for adding or expanding a QueryLake backend profile.

| Field | Value |
|---|---|
| Audience | maintainers, backend contributors, architecture reviewers |
| Use this when | deciding whether a profile change is merge-ready or release-ready |
| Prerequisites | [`ADDING_A_BACKEND_PROFILE.md`](./ADDING_A_BACKEND_PROFILE.md), [`DB_COMPAT_PROFILES.md`](./DB_COMPAT_PROFILES.md), [`PROFILE_DIAGNOSTICS.md`](./PROFILE_DIAGNOSTICS.md) |
| Related docs | [`CHOOSING_A_PROFILE.md`](./CHOOSING_A_PROFILE.md), [`FIRST_SPLIT_STACK_DEPLOYMENT.md`](./FIRST_SPLIT_STACK_DEPLOYMENT.md) |
| Status | active, release policy |

## Release gate

Do not mark a profile as executable or recommended unless all relevant gates below pass.

## Documentation gates

1. `docs/database/DB_COMPAT_PROFILES.md` includes the profile id and support states.
2. Capability IDs documented in `DB_COMPAT_PROFILES.md` match code.
3. Operator-facing guidance exists for when to use and when not to use the profile.
4. The profile's degraded and unsupported semantics are documented explicitly.

## Code and contract gates

1. Profile declaration exists in `QueryLake/runtime/db_compat.py`.
2. Configuration requirements exist and are validated at startup.
3. `/v1/capabilities` reports the profile honestly.
4. `/v1/profile-diagnostics` reports route executors, blockers, and backend state honestly.
5. Unsupported capabilities return structured network errors.
6. Claimed executable routes resolve to real route executors, not placeholders.

## Projection and runtime gates

1. Required projection descriptors exist.
2. Projection readiness is represented in diagnostics.
3. `route_runtime_ready` is meaningful for the routes being claimed.
4. Required runtime blockers are exposed explicitly instead of hidden inside backend-specific exceptions.

## Validation gates

At minimum, all of the following must pass:

```bash
make ci-docs
make ci-db-compat
```

Additionally, at least one smoke or integration path must exist for the route subset being claimed executable.

## Recommendation gate

A profile may be marked executable before it is marked recommended.

To mark a profile recommended, maintainers should be able to say all of the following with a straight face:

- the supported route subset is stable,
- degraded semantics are acceptable for the intended workload,
- unsupported features fail explicitly,
- and operators have enough diagnostics to understand what is happening.

If that statement is not defensible, the profile is not ready to be recommended.

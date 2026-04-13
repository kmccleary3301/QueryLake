# Choosing a QueryLake Database/Search Profile

[![Docs Checks](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml/badge.svg)](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml)
[![Retrieval Eval](https://github.com/kmccleary3301/QueryLake/actions/workflows/retrieval_eval.yml/badge.svg)](https://github.com/kmccleary3301/QueryLake/actions/workflows/retrieval_eval.yml)

Use this document when you need to pick a QueryLake deployment profile deliberately instead of defaulting blindly.

| Field | Value |
|---|---|
| Audience | deployment operators, platform engineers, backend contributors, SDK integrators |
| Use this when | selecting a backend/search stack, evaluating degraded semantics, or deciding whether a profile is production-safe for a workload |
| Prerequisites | [`DB_COMPAT_PROFILES.md`](./DB_COMPAT_PROFILES.md), [`PROFILE_DIAGNOSTICS.md`](./PROFILE_DIAGNOSTICS.md), [`SDK_PROFILE_AWARE_CLIENTS.md`](./SDK_PROFILE_AWARE_CLIENTS.md) |
| Related docs | [`AUTHORITY_PROJECTION_MODEL.md`](./AUTHORITY_PROJECTION_MODEL.md), [`RETRIEVAL_EXECUTION_BOUNDARY.md`](./RETRIEVAL_EXECUTION_BOUNDARY.md), [`ADDING_A_BACKEND_PROFILE.md`](./ADDING_A_BACKEND_PROFILE.md) |
| Status | active, operator/deployment guidance |

## Table of contents

- [Default rule](#default-rule)
- [Decision criteria](#decision-criteria)
- [Profile recommendations](#profile-recommendations)
- [When to choose the gold profile](#when-to-choose-the-gold-profile)
- [When to use the first split-stack profile](#when-to-use-the-first-split-stack-profile)
- [When not to use a non-gold profile](#when-not-to-use-a-non-gold-profile)
- [Operational checks before rollout](#operational-checks-before-rollout)
- [Practical selection flow](#practical-selection-flow)

## Default rule

If you do not have a strong reason to do otherwise, use:

```bash
export QUERYLAKE_DB_PROFILE=paradedb_postgres_gold_v1
```

That remains the canonical QueryLake stack because it preserves:

- the strongest lexical semantics,
- the full retrieval lane set,
- graph/segment traversal behavior,
- and the highest semantic fidelity relative to the current platform design.

Non-gold profiles exist to expand compatibility, not to weaken the recommended path.

## Decision criteria

Choose a profile by evaluating these questions in order:

| Question | Why it matters |
|---|---|
| Do you need full BM25 + advanced lexical operators + hard lexical constraints? | If yes, the gold stack is the safe answer today. |
| Do you need sparse-vector retrieval as part of hybrid search? | The first split-stack slice does not support it yet. |
| Do you need graph traversal or segment-level retrieval? | These are not available on the first split-stack slice. |
| Are you optimizing for platform compatibility with an existing enterprise stack? | This is the main reason to consider a non-gold profile. |
| Can your client/operator layer branch on supported vs degraded vs unsupported capabilities? | If not, do not deploy a degraded profile yet. |
| Can you tolerate approximate lexical semantics for phrase/proximity behavior? | The first split-stack slice degrades these intentionally. |

## Profile recommendations

| Profile | Maturity | Use it when | Avoid it when |
|---|---|---|
| `paradedb_postgres_gold_v1` | `gold` | you need QueryLake's strongest semantics and current production behavior | you are specifically validating compatibility on a different stack |
| `aws_aurora_pg_opensearch_v1` | `split_stack_executable` | you need a realistic first split-stack profile with Aurora-compatible authority, explicit authority-plane DSN control, and OpenSearch-backed lexical+dense execution | you need sparse retrieval, hard lexical constraints, graph traversal, or strict lexical semantic parity |
| `postgres_pgvector_light_v1` | `limited_executable` | you need a minimal PostgreSQL + pgvector deployment and can accept dense-only document-chunk retrieval | you need BM25, file lexical search, sparse retrieval, or graph/segment retrieval |
| `sqlite_fts5_dense_sidecar_local_v1` | `embedded_supported` | you want the supported embedded/local QueryLake slice for low-friction SQLite + local lexical/dense retrieval with explicit degradation | you need broader local parity or a wider embedded scope than the current declared slice |
| `mongo_opensearch_v1` | `planned` | currently do not use in production; this is a declared/planned profile | you need executable deployment behavior today |
| `planetscale_opensearch_v1` | `planned` | currently do not use in production; this is a declared/planned profile | you need executable deployment behavior today |

## When to choose the gold profile

Choose the gold profile if any of the following are true:

- you are doing retrieval evaluation or RAG quality benchmarking,
- you need Google/Twitter-like advanced lexical operator behavior,
- you need hard lexical constraints to be enforced honestly,
- you need sparse-vector hybrid retrieval,
- you need graph traversal or segment-aware retrieval,
- you are debugging correctness rather than backend portability,
- or you want the profile that QueryLake recommends by default.

## When to use the first split-stack profile

The first split-stack profile is:

```text
aws_aurora_pg_opensearch_v1
```

Use it when all of the following are true:

1. You need an authority SQL plane that is Aurora/PostgreSQL-compatible.
2. You are willing to use OpenSearch as the lexical/dense projection plane.
3. Your workload fits inside the currently supported slice:
   - document-chunk BM25-like lexical retrieval
   - file-chunk lexical retrieval
   - lexical+dense hybrid retrieval
4. Your client can handle degraded lexical semantics for:
   - phrase boosts
   - proximity/slop-like behavior
5. Your client or operator path already checks capabilities before enabling unsupported features.

## When not to use a non-gold profile

Do **not** choose a non-gold profile yet if:

- your application assumes every retrieval primitive exists everywhere,
- you need exact lexical behavior parity rather than conceptual primitive parity,
- you cannot expose or react to structured unsupported-feature errors,
- you do not have projection readiness checks in deployment workflows,
- or you are evaluating retrieval quality and need the best current QueryLake behavior.

## Operational checks before rollout

Before treating any profile as acceptable for a deployment, check:

1. Capability surface:

```bash
curl -s http://127.0.0.1:8000/v1/capabilities | jq
```

2. Profile diagnostics:

```bash
curl -s http://127.0.0.1:8000/v1/profile-diagnostics | jq
```

3. Projection readiness:

```bash
curl -s http://127.0.0.1:8000/v1/projection-diagnostics | jq
```

4. Projection plan:

```bash
curl -s http://127.0.0.1:8000/v1/projection-plan/explain | jq
```

You should not treat a split-stack profile as healthy just because:

- startup succeeded, or
- the profile id is recognized.

The route executor diagnostics and projection readiness fields are the real operational gate.

## Practical selection flow

Use this flow literally:

1. Start with `paradedb_postgres_gold_v1`.
2. Move to `aws_aurora_pg_opensearch_v1` only if backend compatibility is a concrete requirement.
3. Inspect `/v1/capabilities` and `/v1/profile-diagnostics`.
4. Confirm route executors and projection readiness for the routes you actually need.
5. Confirm the client path handles:
   - `supported`
   - `degraded`
   - `unsupported`
6. Only then expose the non-gold profile to real workloads.

If you are deciding whether to create or extend a profile rather than choosing one, continue in:

- [`ADDING_A_BACKEND_PROFILE.md`](./ADDING_A_BACKEND_PROFILE.md)

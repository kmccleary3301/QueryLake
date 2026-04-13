# QueryLake Database Compatibility Profiles

[![Docs Checks](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml/badge.svg)](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml)
[![Retrieval Eval](https://github.com/kmccleary3301/QueryLake/actions/workflows/retrieval_eval.yml/badge.svg)](https://github.com/kmccleary3301/QueryLake/actions/workflows/retrieval_eval.yml)

This document defines the current QueryLake database compatibility contract: deployment profiles, capability discovery, and how unsupported retrieval features are reported over the network.

| Field | Value |
|---|---|
| Audience | backend contributors, platform engineers, SDK consumers, deployment operators |
| Use this when | deciding which DB/search stack to deploy, wiring feature flags, or handling degraded/unsupported retrieval behavior |
| Prerequisites | [`README.md`](../../README.md), [`docs/README.md`](../README.md), basic familiarity with QueryLake retrieval surfaces |
| Related docs | [`../sdk/API_REFERENCE.md`](../sdk/API_REFERENCE.md), [`../sdk/RAG_RESEARCH_PLAYBOOK.md`](../sdk/RAG_RESEARCH_PLAYBOOK.md), [`SDK_PROFILE_AWARE_CLIENTS.md`](./SDK_PROFILE_AWARE_CLIENTS.md), `docs_tmp/database/QL_DB_COMPAT_EXTENSION_V1_EXECUTION_PLAN_2026-03-10.md` |
| Status | active, phase-1/phase-2 implementation boundary |

## Table of contents

- [Why this exists](#why-this-exists)
- [Current rule of the system](#current-rule-of-the-system)
- [Profiles](#profiles)
- [Capability discovery](#capability-discovery)
- [Profile diagnostics](#profile-diagnostics)
- [Unsupported-feature contract](#unsupported-feature-contract)
- [Retrieval execution boundary](#retrieval-execution-boundary)
- [Choosing a profile](#choosing-a-profile)
- [Adding a backend profile](#adding-a-backend-profile)
- [Supported profiles](#supported-profiles)
- [First split-stack deployment](#first-split-stack-deployment)
- [Backend profile release gate](#backend-profile-release-gate)
- [Current implementation status](#current-implementation-status)
- [Operator guidance](#operator-guidance)
- [Client guidance](#client-guidance)

## Why this exists

QueryLake is being extended to support multiple authority/search stacks without lying about retrieval semantics.

The core rule is:

> QueryLake preserves its strongest retrieval primitives on the gold stack, and exposes profile-aware capability masking everywhere else.

That means:

- the **ParadeDB + PostgreSQL** profile remains the canonical implementation,
- planned profiles are allowed to exist before they execute,
- and unsupported retrieval requests fail **explicitly and structurally**, not implicitly through backend-specific crashes.

## Current rule of the system

There is exactly one **recommended** production profile today, plus two non-gold maturity levels:

- `gold`: canonical full-semantics profile
- `limited_executable`: deliberately narrow executable profile
- `split_stack_executable`: executable split-stack profile with explicit degraded/unsupported edges
- `planned`: declared profile id with capability semantics, but no executable route surface yet
- `embedded_supported`: supported embedded/local profile for a narrow declared executable slice

| Profile | Maturity | Executable | Recommended | Notes |
|---|---:|---:|---|
| `paradedb_postgres_gold_v1` | `gold` | 🟢 | 🟢 | canonical QueryLake stack; preserves current retrieval behavior |
| `postgres_pgvector_light_v1` | `limited_executable` | 🟡 | 🔴 | limited executable slice; dense-only document-chunk retrieval, no lexical or sparse lanes |
| `aws_aurora_pg_opensearch_v1` | `split_stack_executable` | 🟡 | 🔴 | first executable split-stack slice; document-chunk BM25, lexical+dense hybrid, file-chunk lexical search, canonical segment lexical/dense projection materialization, and explicit authority-plane DSN override support |
| `sqlite_fts5_dense_sidecar_local_v1` | `embedded_supported` | 🟡 | 🔴 | supported embedded/local profile for the declared SQLite FTS5 + dense-sidecar slice, with explicit lexical degradation versus gold |
| `mongo_opensearch_v1` | `planned` | 🔴 | 🔴 | planned document-authority + search-index profile |
| `planetscale_opensearch_v1` | `planned` | 🔴 | 🔴 | planned MySQL-compatible authority + external search profile |

The active profile is chosen with:

```bash
export QUERYLAKE_DB_PROFILE=paradedb_postgres_gold_v1
```

If a deployment declares a profile that QueryLake knows about but does not implement yet, startup fails fast with a structured configuration error.

## Profiles

### Gold profile

`paradedb_postgres_gold_v1`

Backend stack:

| Plane | Backend |
|---|---|
| Authority | `postgresql` |
| Lexical | `paradedb` |
| Dense | `pgvector_halfvec` |
| Sparse | `pgvector_sparsevec` |
| Graph | `postgresql_segment_relations` |

Supported retrieval capabilities:

| Capability | State |
|---|---|
| `authority.sql_transactions` | 🟢 supported |
| `projection.rebuildable_indexes` | 🟢 supported |
| `retrieval.lexical.bm25` | 🟢 supported |
| `retrieval.lexical.advanced_operators` | 🟢 supported |
| `retrieval.dense.vector` | 🟢 supported |
| `retrieval.sparse.vector` | 🟢 supported |
| `retrieval.graph.traversal` | 🟢 supported |
| `retrieval.segment_search` | 🟢 supported |
| `acl.pushdown` | 🟢 supported |
| `explain.retrieval_plan` | 🔵 planned |

### Planned and partially executable profiles

Planned profiles are not placeholders for marketing. They are declarations that:

- the profile id is reserved,
- capability states are known,
- and unsupported execution should fail *predictably*.

They do **not** imply the backend path exists yet. Some profiles may also be partially executable for a narrow route subset before they become generally recommended.

The next planned profile after the completed DB-compat program is:

- `sqlite_fts5_dense_sidecar_local_v1`

That profile is intentionally aimed at a different deployment shape:

- embedded/local development,
- single-user and small-scale research workflows,
- explicit lexical degradation rather than gold-profile parity,
- dense retrieval plus local lexical retrieval without introducing a full external authority/search stack.

See [`LOCAL_PROFILE_V1.md`](./LOCAL_PROFILE_V1.md) for the current local route/projection scaffolding and bring-up expectations.

## Capability discovery

QueryLake exposes the active profile and capability map over the network.

Endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /v1/capabilities` | public deployment capability summary |
| `GET /v2/kernel/capabilities` | kernel/runtime-facing capability summary |
| `GET /readyz` | includes the active `db_profile`, compact startup validation, and compact profile bring-up state |

Example:

```bash
curl -s http://127.0.0.1:8000/v1/capabilities | jq
```

Example response shape:

```json
{
  "profile": {
    "id": "paradedb_postgres_gold_v1",
    "label": "ParadeDB + PostgreSQL (gold)",
    "implemented": true,
    "recommended": true,
    "maturity": "gold",
    "backend_stack": {
      "authority": "postgresql",
      "lexical": "paradedb",
      "dense": "pgvector_halfvec",
      "sparse": "pgvector_sparsevec",
      "graph": "postgresql_segment_relations"
    },
    "notes": "Canonical QueryLake profile. Preserves current retrieval semantics."
  },
  "capabilities": [
    {
      "id": "retrieval.lexical.bm25",
      "support_state": "supported",
      "summary": "Native BM25 lexical retrieval."
    }
  ]
}
```

## Profile diagnostics

For operator-facing readiness and configuration inspection, QueryLake also exposes:

| Endpoint | Purpose |
|---|---|
| `GET /v1/profile-diagnostics` | profile metadata, config readiness, route executors, and MVP scope |
| `GET /v2/kernel/profile-diagnostics` | same diagnostics surface for kernel/runtime consumers |

See:

- [`PROFILE_DIAGNOSTICS.md`](./PROFILE_DIAGNOSTICS.md)
- [`SUPPORTED_PROFILES.md`](./SUPPORTED_PROFILES.md)

This is the preferred surface for answering:

- which config keys are still missing,
- whether the active profile is boot-ready,
- which retrieval routes are executable,
- and what the first split-stack target is intended to support.

QueryLake now also distinguishes fine-grained lexical semantics beneath the broad BM25 surface:

- `retrieval.lexical.advanced_operators`
- `retrieval.lexical.phrase_boost`
- `retrieval.lexical.proximity`
- `retrieval.lexical.hard_constraints`

That split exists so future non-gold profiles can report degraded phrase/proximity behavior without pretending hard lexical constraints are fully portable.

## Unsupported-feature contract

When a retrieval surface is not available on the active profile, QueryLake returns a structured unsupported-feature payload instead of a backend-specific failure.

Status code:

- `501 Not Implemented` for unsupported capability usage

Payload shape:

```json
{
  "detail": {
    "type": "unsupported_feature",
    "code": "ql.db_capability_unsupported",
    "message": "File-chunk lexical search requires BM25 lexical retrieval support on the active deployment profile.",
    "capability": "retrieval.lexical.bm25",
    "profile": "postgres_pgvector_light_v1",
    "support_state": "unsupported",
    "backend_stack": {
      "authority": "postgresql",
      "lexical": "none",
      "dense": "pgvector_halfvec",
      "sparse": "none",
      "graph": "postgresql_segment_relations"
    },
    "hint": "Use the ParadeDB/PostgreSQL gold profile, or disable file-chunk lexical search on this deployment.",
    "docs_ref": "docs/database/DB_COMPAT_PROFILES.md#unsupported-feature-contract",
    "retryable": false
  }
}
```

Contract notes:

| Field | Meaning |
|---|---|
| `docs_ref` | stable documentation pointer for the failing contract surface |
| `retryable` | whether retrying the same request without changing profile/config is expected to help |

This contract is intended to be stable across:

- direct HTTP routes,
- `/api/*` wrapped calls,
- and runtime event execution surfaces.

## Retrieval execution boundary

The retrieval route execution seam is documented separately in:

- [`RETRIEVAL_EXECUTION_BOUNDARY.md`](./RETRIEVAL_EXECUTION_BOUNDARY.md)

Use that document when deciding:

- whether logic belongs in `search.py`,
- whether a new backend path should be a route executor or a lane executor,
- and what has to be true before a non-gold profile can be considered executable for a route.

## Choosing a profile

For operator-facing deployment guidance, use:

- [`CHOOSING_A_PROFILE.md`](./CHOOSING_A_PROFILE.md)

That document is the practical answer to:

- which profile should I deploy,
- when is the split-stack profile appropriate,
- and when should I stay on the gold stack.

## Adding a backend profile

For engineering policy on introducing or extending a backend profile, use:

- [`ADDING_A_BACKEND_PROFILE.md`](./ADDING_A_BACKEND_PROFILE.md)

That document defines the minimum bar for:

- declaring a new profile,
- marking it executable,
- and marking it recommended without overstating support.

## Supported profiles

For the shortest authoritative current matrix, use:

- [`SUPPORTED_PROFILES.md`](./SUPPORTED_PROFILES.md)

## First split-stack deployment

For a concrete bring-up path for the current first executable split-stack slice, use:

- [`FIRST_SPLIT_STACK_DEPLOYMENT.md`](./FIRST_SPLIT_STACK_DEPLOYMENT.md)

That guide covers:

- required environment variables,
- what route/runtime readiness should look like,
- and what failure looks like when required external projections are still absent.

## Backend profile release gate

For the explicit merge/release gate when introducing or expanding a profile, use:

- [`BACKEND_PROFILE_RELEASE_GATE.md`](./BACKEND_PROFILE_RELEASE_GATE.md)

That is the maintainers' answer to:

- when can a profile be called executable,
- when can it be called recommended,
- and what has to be true before those claims are honest.

## Current implementation status

As of this phase:

- profile selection exists,
- startup validation exists,
- capability discovery exists,
- unsupported-feature errors are structured,
- retrieval primitive resolution is profile-aware,
- gold-stack lexical/dense/sparse execution seams have been extracted,
- and a narrow split-stack execution slice now exists for `aws_aurora_pg_opensearch_v1`.

What does **not** exist yet:

- full alternate lexical/dense/sparse adapter coverage,
- authority/projection split execution,
- or broad non-ParadeDB retrieval parity beyond the first document-chunk BM25 and lexical+dense hybrid slice.

## Operator guidance

Use the gold profile unless you are actively developing the compatibility extension.

Recommended practice:

1. Deploy with `QUERYLAKE_DB_PROFILE=paradedb_postgres_gold_v1`.
2. Expose `/v1/capabilities` in staging and operator diagnostics.
3. Treat non-gold profiles as development targets until they are marked executable.
4. Do not advertise unsupported retrieval surfaces as available just because a profile id exists.

## Client guidance

Client code should probe capabilities before enabling optional retrieval features, and profile diagnostics before assuming a route is executable.

The current split-stack slice also has a fixture-backed retrieval parity gate:

- [`RETRIEVAL_PARITY_GATES.md`](./RETRIEVAL_PARITY_GATES.md)
- [`DB_COMPAT_COMPLETION_GATE.md`](./DB_COMPAT_COMPLETION_GATE.md)
- [`DB_COMPAT_PROGRAM_STATUS.md`](./DB_COMPAT_PROGRAM_STATUS.md)
- [`DB_COMPAT_IMPLEMENTATION_REPORT.md`](./DB_COMPAT_IMPLEMENTATION_REPORT.md)
- [`DB_COMPAT_FUTURE_SCOPE.md`](./DB_COMPAT_FUTURE_SCOPE.md)

Python SDK example:

```python
from querylake_sdk import QueryLakeClient

client = QueryLakeClient(base_url="http://127.0.0.1:8000", oauth2="...")
caps = client.capabilities_summary()
diag = client.profile_diagnostics_summary()

if caps.is_available("retrieval.sparse.vector"):
    print("Sparse retrieval is available")
else:
    print("Disable sparse lane controls for this deployment")

if not diag.route_executable("search_file_chunks"):
    print("File-chunk lexical search is not executable on this profile")
```

Do not assume:

- sparse retrieval,
- advanced lexical operators,
- or graph traversal

are uniformly available across future profiles.

For the intended SDK branching pattern, see:

- [`SDK_PROFILE_AWARE_CLIENTS.md`](./SDK_PROFILE_AWARE_CLIENTS.md)

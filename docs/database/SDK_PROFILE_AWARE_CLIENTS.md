# QueryLake SDK: Profile-Aware Clients

[![Docs Checks](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml/badge.svg)](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml)
[![SDK Checks](https://github.com/kmccleary3301/QueryLake/actions/workflows/sdk_checks.yml/badge.svg)](https://github.com/kmccleary3301/QueryLake/actions/workflows/sdk_checks.yml)

Build client code that adapts to the active QueryLake database/search profile without guessing which retrieval surfaces are available.

| Field | Value |
|---|---|
| Audience | SDK users, application engineers, integration maintainers |
| Use this when | writing clients that need to branch on supported vs degraded vs unsupported retrieval semantics |
| Prerequisites | [`DB_COMPAT_PROFILES.md`](./DB_COMPAT_PROFILES.md), [`PROFILE_DIAGNOSTICS.md`](./PROFILE_DIAGNOSTICS.md), [`../sdk/API_REFERENCE.md`](../sdk/API_REFERENCE.md) |
| Related docs | [`RETRIEVAL_EXECUTION_BOUNDARY.md`](./RETRIEVAL_EXECUTION_BOUNDARY.md), [`../../sdk/python/README.md`](../../sdk/python/README.md) |
| Status | active, phase-3 SDK/operator guidance |

## Rule of thumb

Use the SDK in three layers:

1. `capabilities_summary()` for feature flags and retrieval-lane availability
2. `profile_diagnostics_summary()` when you need route-level executability, projection readiness, config readiness, or operator-facing explanations
3. thin client helpers when you want a direct yes/no answer for route execution on the active deployment
4. typed backend-connectivity and startup-validation helpers when you are writing deployment bring-up or readiness automation
5. `profile_bringup_summary()` when you want one typed preflight payload instead of manually correlating route diagnostics and projection state
6. `readyz_summary()` when you want the same high-signal readiness view that operators see from `/readyz`, but parsed into a typed compact payload

Do not hardcode assumptions like:

- “BM25 always exists”
- “sparse is always safe to enable”
- “document-chunk hybrid and file-chunk lexical are always equally available”

Those assumptions are only true on the gold profile.

## Minimal capability check

```python
from querylake_sdk import QueryLakeClient

client = QueryLakeClient(base_url="http://127.0.0.1:8000")
caps = client.capabilities_summary()

if caps.is_available("retrieval.sparse.vector"):
    sparse_weight = 0.2
    limit_sparse = 12
else:
    sparse_weight = 0.0
    limit_sparse = 0

route_scope = caps.route_representation_scope_id("search_hybrid.document_chunk")
route_caps = caps.route_capability_dependencies("search_hybrid.document_chunk")
route_declared_executable = client.route_declared_executable_from_capabilities("search_hybrid.document_chunk")
route_declared_optional = client.route_declared_optional_from_capabilities("retrieval.sparse.vector")
```

Important behavior:

- `is_supported(...)` means only `supported`
- `is_available(..., allow_degraded=True)` treats `degraded` as usable
- `is_available(..., allow_degraded=False)` requires full support

## Route-level executability check

Some capability checks are too coarse for execution decisions. For example:

- the active profile may support a dense lane,
- but lexical routes may still be unavailable,
- while `search_hybrid.document_chunk` is executable only in a dense-only subset.

Use profile diagnostics for this:

```python
from querylake_sdk import QueryLakeClient

client = QueryLakeClient(base_url="http://127.0.0.1:8000")
diag = client.profile_diagnostics_summary()

if diag.route_executable("search_hybrid.document_chunk"):
    print("Hybrid document-chunk retrieval is executable on this deployment.")

if not diag.route_executable("search_file_chunks"):
    print("This deployment does not expose file-chunk lexical retrieval.")
```

## Route-level projection readiness

On split-stack profiles, a route can be executable in principle but still blocked because its required external projections are not built yet.

Use projection-readiness helpers for that distinction:

```python
from querylake_sdk import QueryLakeClient

client = QueryLakeClient(base_url="http://127.0.0.1:8000")
diag = client.profile_diagnostics_summary()

route_id = "search_hybrid.document_chunk"

if diag.route_executable(route_id) and not diag.route_projection_ready(route_id):
    print("Route is supported by the active profile, but external projections are not ready.")
    print(diag.route_projection_missing_descriptors(route_id))

if diag.route_runtime_ready(route_id):
    print("This deployment can execute the route right now.")
```

Thin client wrappers are available too:

```python
if client.route_runtime_ready("search_hybrid.document_chunk"):
    ...
else:
    print(client.route_projection_missing_descriptors("search_hybrid.document_chunk"))
    print(client.route_blocker_kinds("search_hybrid.document_chunk"))

print(client.route_lane_backends("search_hybrid.document_chunk"))
print(client.route_adapter_ids("search_hybrid.document_chunk"))
print(client.route_projection_target_backend_names("search_hybrid.document_chunk"))
print(client.route_required_projection_descriptor_ids("search_hybrid.document_chunk"))
print(client.route_declared_executable("search_hybrid.document_chunk"))
print(client.route_declared_optional("retrieval.sparse.vector"))
print(client.route_lexical_support_class("search_hybrid.document_chunk"))
print(client.route_state("search_hybrid.document_chunk"))
print(client.route_summary())
print(client.runtime_blocker_summary())
```

For the experimental local embedded profile, the SDK also exposes local-profile-specific helpers:

```python
print(client.local_profile_maturity())
print(client.local_support_matrix())
print(client.local_route_support_entry("search_hybrid.document_chunk"))
print(client.local_route_representation_scope_id("search_hybrid.document_chunk"))
print(client.local_route_representation_scope("search_hybrid.document_chunk"))
print(client.local_route_capability_dependencies("search_hybrid.document_chunk"))
print(client.local_route_declared_executable("search_hybrid.document_chunk"))
print(client.local_route_lexical_support_class("search_hybrid.document_chunk"))
print(client.local_route_dense_sidecar_ready("search_hybrid.document_chunk"))
print(client.local_route_dense_sidecar_cache_warmed("search_hybrid.document_chunk"))
print(client.local_route_dense_sidecar_indexed_record_count("search_hybrid.document_chunk"))
print(client.profile_bringup_summary().local_dense_sidecar_contract())
print(client.profile_bringup_summary().local_dense_sidecar_contract_version())
print(client.profile_bringup_summary().local_dense_sidecar_lifecycle_contract_version())
print(client.profile_bringup_summary().local_dense_sidecar_ready_state_source())
print(client.profile_bringup_summary().local_dense_sidecar_stats_source())
print(client.profile_bringup_summary().local_dense_sidecar_cache_lifecycle_state())
print(client.profile_bringup_summary().local_dense_sidecar_rebuildable_from_projection_records())
print(client.profile_bringup_summary().local_dense_sidecar_requires_process_warmup())
print(client.profile_bringup_summary().local_dense_sidecar_persisted_projection_state_available())
print(client.profile_bringup_summary().local_route_dense_sidecar_contract("search_hybrid.document_chunk"))
print(client.profile_bringup_summary().local_route_dense_sidecar_ready_state_source("search_hybrid.document_chunk"))
print(client.profile_bringup_summary().local_route_dense_sidecar_stats_source("search_hybrid.document_chunk"))
print(client.profile_bringup_summary().local_route_dense_sidecar_cache_lifecycle_state("search_hybrid.document_chunk"))
print(client.profile_bringup_summary().local_route_dense_sidecar_rebuildable_from_projection_records("search_hybrid.document_chunk"))
print(client.profile_bringup_summary().local_route_dense_sidecar_requires_process_warmup("search_hybrid.document_chunk"))
print(client.profile_bringup_summary().local_route_dense_sidecar_persisted_projection_state_available("search_hybrid.document_chunk"))
print(client.local_promotion_status())
print(client.local_scope_expansion_status())
print(client.local_declared_executable_route_ids())
print(client.local_declared_runtime_ready_route_ids())
print(client.local_declared_runtime_blocked_route_ids())
print(client.local_required_projection_ids())
print(client.local_representation_scope_ids())
print(client.local_current_supported_slice_frozen())
print(client.local_scope_expansion_pending_for_wider_scope())
print(client.local_scope_expansion_required_now())
print(client.local_scope_expansion_satisfied_now())
print(client.local_scope_expansion_future_scope_candidates())
print(client.local_scope_expansion_docs_ref())
print(client.local_scope_expansion_contract())
print(client.local_scope_expansion_contract_version())
print(client.local_scope_expansion_lifecycle_contract_version())
print(client.local_scope_expansion_lifecycle_state())
print(client.local_scope_expansion_cache_lifecycle_state())
print(client.local_scope_expansion_dense_sidecar_promotion_contract_ready())
print(client.local_scope_expansion_rebuildable_from_projection_records())
print(client.local_scope_expansion_requires_process_warmup())
print(client.local_scope_expansion_persisted_projection_state_available())
print(client.local_scope_expansion_required_before_widening())
```

Route-state helpers return normalized client-facing states:

| State | Meaning |
|---|---|
| `runtime_ready` | fully runnable on the current deployment |
| `degraded_runtime_ready` | runnable, but with degraded semantics |
| `blocked_by_projection` | executable in principle, but blocked by projection readiness |
| `blocked_by_backend_connectivity` | executable in principle, but blocked by failed backend reachability |
| `blocked_runtime` | blocked for another runtime reason |
| `unsupported` | the active profile does not support the route |
| `degraded_requires_opt_in` | degraded route exists, but `allow_degraded=False` rejected it |
| `planned` | declared route without an implemented executor |
| `missing_route` | no such route is present in diagnostics |

## Startup validation and backend connectivity

For deployment bring-up, the typed diagnostics models now expose both the normalized startup failure kind and typed backend-plane entries:

```python
from querylake_sdk import QueryLakeClient

client = QueryLakeClient(base_url="http://127.0.0.1:8000")
diag = client.profile_diagnostics_summary()

if diag.startup_validation is not None:
    print(diag.startup_validation.validation_error_kind)
    print(diag.startup_validation.is_projection_runtime_blocked())

projection_plane = client.backend_connectivity_entry("projection")
if projection_plane is not None:
    print(projection_plane.backend)
    print(projection_plane.status)
    print(projection_plane.endpoint)
```

Useful helpers:

| Helper | Purpose |
|---|---|
| `client.kernel_profile_diagnostics_summary()` | typed kernel-surface diagnostics payload |
| `client.backend_connectivity_entry("projection")` | typed projection-plane connectivity record |
| `client.backend_connectivity_entries()` | typed connectivity map for all reported planes |
| `client.route_is_degraded(route_id)` | whether the route is executable but degraded |
| `client.route_blocked_by_projection(route_id)` | whether projection readiness is the blocking reason |
| `client.route_blocked_by_backend_connectivity(route_id)` | whether backend reachability is the blocking reason |
| `client.route_lexical_support_class(route_id)` | normalized lexical semantics class for the route |
| `client.route_lexical_capability_states(route_id)` | per-capability lexical support-state map for the route |
| `client.route_lexical_degraded_capabilities(route_id)` | degraded lexical features for the route |
| `client.route_lexical_unsupported_capabilities(route_id)` | lexical features that must fail fast on the route |
| `client.route_gold_recommended_for_exact_constraints(route_id)` | whether exact lexical workloads on the route should still prefer the gold profile |
| `client.route_exact_constraint_degraded_capabilities(route_id)` | exact-constraint-related capabilities that degrade on the route |
| `client.route_exact_constraint_unsupported_capabilities(route_id)` | exact-constraint-related capabilities that are fully unsupported on the route |
| `client.route_projection_targets(route_id)` | explicit route-level projection targets with authority model, source scope, and target backend |
| `client.route_projection_target_backend_names(route_id)` | compact `projection_id -> target_backend_name` map for route dependencies |
| `client.route_required_projection_descriptor_ids(route_id)` | required projection descriptor ids for the resolved route |
| `client.route_declared_executable(route_id)` | whether the current diagnostics manifest declares the route executable |
| `client.route_declared_optional(route_id)` | whether the current diagnostics manifest declares the route optional |
| `client.profile_diagnostics_summary().route_executor(route_id).compatibility_projection_reliance` | whether the route still depends on compatibility projections |

## Bring-up summary from the SDK

For deployment preflight or automation, use the aggregated bring-up helper:

```python
from querylake_sdk import QueryLakeClient

client = QueryLakeClient(base_url="http://127.0.0.1:8000")
bringup = client.profile_bringup_summary()

print(bringup.summary.boot_ready)
print(bringup.ready_projection_ids)
print(bringup.projection_ids_needing_build)
print(bringup.bootstrapable_required_projections())
print(bringup.nonbootstrapable_required_projections())
print(bringup.projection_building_ids)
print(bringup.projection_failed_ids)
print(bringup.projection_stale_ids)
print(bringup.projection_absent_ids)
print(bringup.recommended_projection_ids)
print(bringup.recommended_projection_ids_needing_build)
print(bringup.bootstrapable_recommended_projections())
print(bringup.nonbootstrapable_recommended_projections())
print(bringup.route_runtime_blocked_ids)
print(bringup.lexical_degraded_route_ids)
print(bringup.lexical_gold_recommended_route_ids)
print(bringup.compatibility_projection_route_ids)
print(bringup.canonical_projection_target_ids)
print(bringup.route_recovery_entry("search_bm25.document_chunk"))
print(bringup.route_declared_executable("search_bm25.document_chunk"))
print(bringup.route_required_projection_descriptor_ids("search_bm25.document_chunk"))
print(bringup.backend_unreachable_planes)
print(bringup.bootstrap_command())
print([action.summary for action in bringup.highest_priority_actions()])
```

The local promotion helpers are available on the same summary/client surfaces:

- `bringup.local_support_matrix()`
- `bringup.local_promotion_status()`
- `bringup.local_scope_expansion_status()`
- `bringup.local_declared_executable_route_ids()`
- `bringup.local_declared_runtime_ready_route_ids()`
- `bringup.local_declared_runtime_blocked_route_ids()`
- `bringup.local_required_projection_ids()`
- `bringup.local_representation_scope_ids()`
- `bringup.local_route_representation_scope(route_id)`
- `bringup.local_route_capability_dependencies(route_id)`
- `bringup.local_route_lexical_support_class(route_id)`
- `bringup.local_route_dense_sidecar_ready(route_id)`
- `bringup.local_route_dense_sidecar_cache_warmed(route_id)`
- `bringup.local_route_dense_sidecar_indexed_record_count(route_id)`
- `bringup.local_route_dense_sidecar_cache_lifecycle_state(route_id)`
- `bringup.local_route_dense_sidecar_rebuildable_from_projection_records(route_id)`
- `bringup.local_route_dense_sidecar_requires_process_warmup(route_id)`
- `bringup.local_route_dense_sidecar_persisted_projection_state_available(route_id)`

For the embedded-profile widening boundary, the SDK now exposes explicit helpers:

| Helper | Purpose |
|---|---|
| `client.local_scope_expansion_status()` | raw machine-readable widening status from `profile_bringup.local_profile.scope_expansion_status` |
| `client.local_current_supported_slice_frozen()` | whether the current supported embedded slice is intentionally frozen |
| `client.local_scope_expansion_pending_for_wider_scope()` | remaining blockers before widening the supported slice |
| `client.local_scope_expansion_required_now()` | widening criteria currently tracked |
| `client.local_scope_expansion_satisfied_now()` | widening criteria already satisfied |
| `client.local_scope_expansion_future_scope_candidates()` | future route/semantic candidates deferred beyond the current slice |
| `client.local_scope_expansion_docs_ref()` | authoritative docs reference for interpreting the widening criteria |
| `client.local_scope_expansion_contract()` | frozen machine-readable widening contract from `profile_bringup.local_profile.scope_expansion_contract` |
| `client.local_scope_expansion_contract_version()` | dense-sidecar contract version referenced by the widening contract |
| `client.local_scope_expansion_lifecycle_contract_version()` | dense-sidecar lifecycle contract version referenced by the widening contract |
| `client.local_scope_expansion_lifecycle_state()` | current dense-sidecar lifecycle state attached to widening status |
| `client.local_scope_expansion_cache_lifecycle_state()` | finer-grained cache/storage lifecycle state for the embedded dense-sidecar |
| `client.local_scope_expansion_dense_sidecar_promotion_contract_ready()` | whether the dense-sidecar promotion contract is satisfied right now |
| `client.local_scope_expansion_rebuildable_from_projection_records()` | whether the current embedded dense-sidecar can be reconstructed from ready projection records |
| `client.local_scope_expansion_requires_process_warmup()` | whether the embedded slice is runnable but still needs process-local sidecar warmup |
| `client.local_scope_expansion_persisted_projection_state_available()` | whether build-state metadata carries forward dense-sidecar readiness/cache state |
| `client.local_scope_expansion_required_before_widening()` | frozen criteria list that must be addressed before widening beyond the current embedded slice |

This is the fastest SDK surface for answering:

- is the active profile boot-ready?
- which projections still need to be built?
- which of those are buildable right now vs blocked by profile support?
- which routes are blocked right now?
- are backend connectivity failures part of the reason?
- which routes are still leaning on compatibility projections instead of canonical authority-backed targets?

Use `bringup_route_recovery()` when you need route-by-route operator guidance instead of only aggregate counters. This surface tells you whether a route is:

- fixable immediately via projection bootstrap,
- blocked by non-bootstrapable profile limitations, or
- runnable but degraded enough that exact lexical workloads should still prefer the gold ParadeDB profile.

Additional convenience helpers are available when you want automation-friendly preflight output directly from the client:

| Helper | Purpose |
|---|---|
| `client.bringup_bootstrap_command()` | return the current highest-priority projection bootstrap command, if any |
| `client.bringup_next_actions()` | return ordered remediation items with command and blocker metadata |
| `client.bringup_backend_targets()` | return compact authority/projection target summaries with endpoint/env and probe state |
| `client.bringup_recommended_projection_status_buckets()` | return `ready` / `needs_build` / `all` buckets for executable canonical projections that are not required for the current public route slice |
| `client.bringup_lexical_degraded_routes()` | return routes whose lexical semantics are degraded or partially unsupported |
| `client.bringup_lexical_gold_recommended_routes()` | return routes that should prefer the gold profile for exact lexical constraints |
| `client.bringup_declared_route_support()` | return the declared route support matrix emitted by the backend bring-up contract |
| `client.bringup_declared_executable_routes()` | return the backend-declared executable route ids |
| `client.bringup_declared_optional_routes()` | return the backend-declared optional route ids |
| `client.bringup_declared_runtime_ready_routes()` | return declared executable route ids that are runtime-ready right now |
| `client.bringup_declared_runtime_blocked_routes()` | return declared executable route ids that are still runtime-blocked |
| `client.bringup_declared_routes_runtime_ready()` | true when all declared executable routes are runtime-ready |
| `client.bringup_route_recovery()` | return per-route recovery summaries with runtime blockers, bootstrapable projection ids, and lexical caveat hints |
| `client.bringup_route_recovery_entry(route_id)` | return a targeted recovery summary for a single route |
| `client.bringup_projection_status_buckets()` | return ready/building/failed/stale/absent projection ids from the aggregated bring-up surface |
| `summary.projection(...).materialization_target` | inspect the explicit authority/projection target contract for a projection row, including `authority_model`, `source_scope`, and `target_backend_name` |

The CLI doctor command now exposes the same shape in one place:

```bash
querylake --profile local doctor | jq '.profile_bringup_summary'
querylake --profile local doctor | jq '.profile_diagnostics_summary'
```

Use it when you want:

- the active startup validation kind and details
- backend target summaries for the authority/projection planes
- prioritized remediation actions without writing SDK code
- a quick list of routes that are operational but still not equivalent to the gold profile for exact lexical workloads

### Query-level degradation and sparse gating

Use request-specific explain helpers when the active profile is degraded rather than fully supported.

Quoted phrase behavior on the first split-stack profile is degraded, not unsupported:

```python
plan = client.search_hybrid_plan_explain(
    query='"vapor recovery"',
    collection_ids=["col-1"],
)

print(plan.degraded_capabilities())
print(plan.unsupported_capabilities())
print(plan.route_id())
print(plan.representation_scope_id())
print(plan.planning_surface())
print(plan.projection_buildability_class())
```

Hard lexical constraints should still be treated as a hard stop when the request-level lexical plan says they are unsupported:

```python
plan = client.search_hybrid_plan_explain(
    query="title:boiler",
    collection_ids=["col-1"],
)

if "retrieval.lexical.hard_constraints" in plan.unsupported_capabilities():
    raise RuntimeError("This deployment cannot execute hard lexical constraints safely.")
```

The same request-level explain surface is now available for lexical-only routes:

```python
bm25_plan = client.search_bm25_plan_explain(
    query="boiler feedwater chemistry",
    collection_ids=["col-1"],
)
print(bm25_plan.route_id())
print(bm25_plan.representation_scope_id())

file_plan = client.search_file_chunks_plan_explain(query="boiler feedwater chemistry")
print(file_plan.route_id())
print(file_plan.representation_scope_id())
```

Sparse should be gated before you ever include it in a request:

```python
caps = client.capabilities_summary()
allow_sparse = caps.is_available("retrieval.sparse.vector")

rows = client.search_hybrid_chunks(
    query="boiler feedwater chemistry",
    collection_ids=["col-1"],
    use_sparse=allow_sparse,
    limit_sparse=12 if allow_sparse else 0,
    sparse_weight=0.15 if allow_sparse else 0.0,
)
```

That is the correct client strategy:
- degrade phrase/proximity-aware lexical behavior only when your product path tolerates it,
- fail fast on unsupported hard lexical constraints,
- and never send sparse-lane requests unless capability discovery says the lane is executable.

## Client strategy matrix

Use the following matrix instead of guessing from backend names:

| Situation | Recommended client behavior | Why |
|---|---|---|
| Capability is `supported` and route state is `runtime_ready` | execute normally | full profile support and current deployment readiness are both satisfied |
| Capability is `degraded` and route state is `degraded_runtime_ready` | execute only if the product path tolerates approximate semantics; surface a note to users or logs | the route is runnable, but semantics are weaker than the gold profile |
| Route state is `blocked_by_projection` | do not execute; surface deployment/operator guidance | the route is valid in principle but required external projections are not ready |
| Route state is `blocked_by_backend_connectivity` | do not execute; surface backend health guidance | the route cannot run until required planes are reachable |
| Capability is `unsupported` | fail fast and remove or disable the option in the UI/client path | QueryLake is explicitly telling you the active profile does not support this behavior |
| Capability/route is `planned` | treat it as unavailable | planned means architecturally declared, not executable |
| You need exact hard lexical constraints or strict phrase semantics | require the gold profile | split-stack lexical behavior is intentionally degraded or unsupported for these cases |
| You want sparse hybrid on the current split-stack profile | disable sparse explicitly | the first split-stack slice does not execute sparse retrieval today |

Practical rule:

- use `capabilities_summary()` to decide what features may be shown,
- use `profile_diagnostics_summary()` to decide what can actually run right now,
- and use request-specific explain helpers when you need adapter/lane provenance for a particular query.

## Typical branch pattern

```python
from querylake_sdk import QueryLakeClient

client = QueryLakeClient(base_url="http://127.0.0.1:8000")
caps = client.capabilities_summary()
diag = client.profile_diagnostics_summary()

allow_sparse = caps.is_available("retrieval.sparse.vector")
allow_hard_constraints = caps.is_supported("retrieval.lexical.hard_constraints")
allow_doc_hybrid = diag.route_executable("search_hybrid.document_chunk")

if not allow_doc_hybrid:
    raise RuntimeError(
        f"search_hybrid.document_chunk is not executable on profile {diag.profile.id}"
    )

query = '"boiler feedwater"'
if not allow_hard_constraints:
    # downgrade the query shape rather than pretending strict semantics still hold
    query = "boiler feedwater"

rows = client.search_hybrid_chunks(
    query=query,
    collection_ids=["<collection-id>"],
    limit_bm25=12,
    limit_similarity=12,
    limit_sparse=12 if allow_sparse else 0,
    bm25_weight=0.45,
    similarity_weight=0.55 if not allow_sparse else 0.4,
    sparse_weight=0.15 if allow_sparse else 0.0,
)
```

## Retrieval plan explain from the SDK

When you need to know not just whether a route is available, but **which adapters and lane families** were selected for a concrete hybrid retrieval request, use the plan-explain helper:

```python
from querylake_sdk import QueryLakeClient

client = QueryLakeClient(base_url="http://127.0.0.1:8000")

plan = client.search_hybrid_plan_explain(
    query="boiler feedwater chemistry",
    collection_ids=["<collection-id>"],
    limit_bm25=8,
    limit_similarity=8,
    explain_plan=True,  # optional; helper forces it anyway
)

print(plan.route)
print(plan.route_executor())
print(plan.adapter_ids())
print(plan.route_id())
print(plan.representation_scope_id())
print(plan.planning_surface())
print(plan.projection_buildability_class())
print(plan.degraded_capabilities())
print(plan.unsupported_capabilities())
```

Use this when:

- you want operator-facing explain output for the exact request shape being executed
- you want to log adapter selection for audits or benchmark artifacts
- you want to confirm that a degraded profile is using the lane/backend combination you expect

Practical distinction:

| Need | Helper |
|---|---|
| static deployment capability truth | `capabilities_summary()` |
| route executability and blocker state | `profile_diagnostics_summary()` |
| request-specific adapter/lane explain output | `search_hybrid_plan_explain(...)`, `search_bm25_plan_explain(...)`, `search_file_chunks_plan_explain(...)` |

## Helper methods

### Capability summary helpers

Available on `CapabilitiesSummary`:

| Method | Purpose |
|---|---|
| `capability(capability_id)` | return the `CapabilitySummary` object or `None` |
| `support_state(capability_id)` | return `supported`, `degraded`, `unsupported`, `planned`, or `None` |
| `is_supported(capability_id)` | true only for full support |
| `is_available(capability_id, allow_degraded=True)` | true for supported, and optionally degraded |
| `supported_capabilities()` | list supported capability rows |
| `degraded_capabilities()` | list degraded capability rows |
| `unavailable_capabilities()` | list unsupported/planned capability rows |

Thin client wrappers:

| Method | Equivalent |
|---|---|
| `client.support_state(capability_id)` | `client.capabilities_summary().support_state(...)` |
| `client.supports(capability_id, allow_degraded=True)` | `client.capabilities_summary().is_available(...)` |
| `client.representation_scopes()` | return the declared representation-scope registry from the capabilities contract |
| `client.route_support_manifest_v2()` | return the V2 route support manifest keyed by route id |
| `client.route_representation_scope_id_from_capabilities(route_id)` | get the route's declared representation scope id from the capabilities contract |
| `client.route_capability_dependencies_from_capabilities(route_id)` | get the route's declared capability dependencies from the capabilities contract |
| `client.diagnostics_representation_scopes()` | return the representation-scope registry attached to the current diagnostics payload |
| `client.diagnostics_route_support_manifest_v2()` | return the diagnostics V2 route support manifest keyed by route id |
| `client.bringup_representation_scopes()` | return the representation-scope registry attached to the current bring-up payload |
| `client.bringup_route_support_manifest_v2()` | return the bring-up V2 route support manifest keyed by route id |

### Profile diagnostics helpers

Available on `ProfileDiagnosticsSummary`:

| Method | Purpose |
|---|---|
| `route_executor(route_id)` | return the `RouteExecutorSummary` or `None` |
| `route_support_state(route_id)` | get the resolved support state for that route |
| `route_executable(route_id, allow_degraded=True)` | whether the route is executable under the current profile |
| `route_projection_ready(route_id)` | whether required external projections are ready on this deployment |
| `route_projection_missing_descriptors(route_id)` | missing projection descriptor ids blocking execution |
| `route_runtime_ready(route_id, allow_degraded=True)` | whether the route is actually runnable right now |
| `route_blocker_kinds(route_id)` | normalized runtime blocker categories for the route |
| `route_blocking_projection_ids(route_id)` | projection ids surfaced by runtime blockers |
| `route_lane_backends(route_id)` | lane-to-backend map for the resolved route executor |
| `route_adapter_ids(route_id)` | lane-to-adapter-id map for the resolved route executor |
| `route_representation_scope_id(route_id)` | representation scope id attached to the resolved route executor |
| `route_representation_scope(route_id)` | raw representation scope payload attached to the resolved route executor |
| `route_lexical_support_class(route_id)` | normalized lexical semantics summary for the route |
| `route_lexical_capability_states(route_id)` | route-level lexical capability state map |
| `route_lexical_degraded_capabilities(route_id)` | degraded lexical features for the route |
| `route_lexical_unsupported_capabilities(route_id)` | unsupported lexical features for the route |
| `route_summary_payload()` | aggregated counts and route-id lists for executable/runtime-ready/blocker states |
| `runtime_blocker_summary()` | blocker-kind count map across all inspected routes |
| `executable_routes()` | list executable route executors |
| `runtime_ready_routes()` | list route executors runnable on this deployment right now |
| `degraded_routes()` | list executable-but-degraded route executors |
| `missing_route_executors()` | list planned/non-implemented route executors |
| `projection_blocked_routes()` | list executable routes blocked only by missing projections |
| `runtime_blocked_routes()` | list routes blocked by runtime readiness, including support-state blockers |
| `backend_connectivity_status(plane)` | status string for `authority` / `projection` connectivity |

Configuration helpers:

| Method | Purpose |
|---|---|
| `missing_requirements()` | env/config requirements not present |
| `invalid_requirements()` | present but invalid requirements |
| `blocking_requirements()` | requirements blocking execution |

Thin client wrappers:

| Method | Equivalent |
|---|---|
| `client.route_support_state(route_id)` | `client.profile_diagnostics_summary().route_support_state(...)` |
| `client.route_executable(route_id, allow_degraded=True)` | `client.profile_diagnostics_summary().route_executable(...)` |
| `client.route_projection_ready(route_id)` | `client.profile_diagnostics_summary().route_projection_ready(...)` |
| `client.route_projection_missing_descriptors(route_id)` | `client.profile_diagnostics_summary().route_projection_missing_descriptors(...)` |
| `client.route_runtime_ready(route_id, allow_degraded=True)` | `client.profile_diagnostics_summary().route_runtime_ready(...)` |
| `client.route_blocker_kinds(route_id)` | normalized blocker kinds for the route |
| `client.route_blocking_projection_ids(route_id)` | projection ids carried by runtime blockers |
| `client.route_lane_backends(route_id)` | lane backend mapping for the route |
| `client.route_adapter_ids(route_id)` | lane adapter-id mapping for the route |
| `client.route_summary()` | aggregated route-state counts and route-id lists |
| `client.runtime_blocker_summary()` | blocker-kind count map for the active profile |
| `client.projection_blocked_routes(allow_degraded=True)` | route ids currently blocked by projection readiness |
| `client.runtime_blocked_routes(allow_degraded=True)` | route ids currently blocked by runtime readiness |
| `client.backend_connectivity_status(plane)` | plane-level connectivity status string |

### Retrieval plan explain helpers

Available on `RetrievalPlanExplainSummary`:

| Method | Purpose |
|---|---|
| `route_executor()` | effective route executor id or route-executor payload |
| `lexical_capability_plan()` | request-specific lexical capability planner payload |
| `lane_state()` | effective lane-state payload for the request |
| `adapter_ids()` | lane-family to adapter-id mapping extracted from pipeline stages |
| `query_ir_v2()` | effective `QueryIRV2` payload for the concrete request |
| `projection_ir_v2()` | effective `ProjectionIRV2` payload for the concrete request |
| `route_id()` | resolved route id from request-specific V2 planning |
| `representation_scope_id()` | resolved representation scope id from request-specific V2 planning |
| `planning_surface()` | planning surface used for the request-specific V2 payload |
| `projection_buildability_class()` | active projection-buildability class for the request |
| `degraded_capabilities()` | degraded lexical capabilities for this request |
| `unsupported_capabilities()` | unsupported lexical capabilities for this request |

Thin client wrappers:

| Method | Purpose |
|---|---|
| `client.search_hybrid_plan_explain(...)` | return parsed `RetrievalPlanExplainSummary` for a concrete hybrid request |
| `client.search_hybrid_plan_explain_with_options(...)` | same, but uses a typed `HybridSearchOptions` payload |
| `client.search_bm25_plan_explain(...)` | return parsed `RetrievalPlanExplainSummary` for a concrete BM25 request |
| `client.search_file_chunks_plan_explain(...)` | return parsed `RetrievalPlanExplainSummary` for a concrete file-chunk lexical request |

Each `RouteExecutorSummary` now also carries `runtime_blockers`, with helpers including:
- `blocker_kinds()`
- `blocking_projection_ids()`
- `writer_gap_projection_ids()`
- `build_gap_projection_ids()`
- `has_projection_writer_gap()`
- `lane_backends()`
- `adapter_ids()`

That lets SDK callers surface operator-facing reasons and backend selection without reparsing raw payloads.

## Recommended client policy

For research and application code:

1. Probe capability state before enabling optional lanes.
2. Probe route executability before assuming a surface exists.
3. Treat `degraded` as a deliberate product choice, not an invisible fallback.
4. Reject unsupported strict semantics rather than silently weakening them.

For operator tooling:

1. call `profile_diagnostics_summary()`
2. inspect `startup_validation`
3. inspect `blocking_requirements()`
4. inspect `missing_route_executors()`

When interpreting `startup_validation`:

- `boot_ready` means the profile can serve every route it declares as `supported` or `degraded` in its current target slice and that any required external projections are ready,
- `full_route_coverage_ready` means every inspected canonical route is executable,
- `full_runtime_coverage_ready` means every inspected canonical route is runnable on this deployment right now,
- `non_executable_optional_routes` are visible gaps outside the required MVP subset, if any remain.

## What not to do

Do not:

- assume non-gold profiles support all lexical operators
- infer route executability from capability IDs alone
- silently enable sparse because the backend “looks like” it should support vectors
- treat `planned` as executable

## Current practical split

Today:

- use the gold profile when you need full QueryLake retrieval semantics
- use the first split-stack profile only when you explicitly accept its narrower route surface

That split is now visible in the SDK. Client code should reflect it explicitly.


## Projection inspection

Use `projection_diagnostics()` when you need to inspect projection descriptor coverage and build-state truth for the active profile. This is especially useful on split-stack profiles, where route support may depend on compatibility projections being declared, executable, and ready.

Practical distinction:

| Question | Helper |
|---|---|
| “Does the profile support this route at all?” | `route_executable(...)` |
| “Are the required projections built?” | `route_projection_ready(...)` |
| “Can I actually call this route right now?” | `route_runtime_ready(...)` |
| “Why is the route blocked?” | `route_blocker_kinds(...)` / `route_blocking_projection_ids(...)` |
| “Which backend and adapter are serving the route?” | `route_lane_backends(...)` / `route_adapter_ids(...)` |
| “Will quoted phrases degrade or will hard lexical constraints fail?” | `route_lexical_support_class(...)` / `route_lexical_capability_states(...)` |

When you want actionable projection worklists instead of raw diagnostic payloads, use `projection_diagnostics_summary()`:

```python
from querylake_sdk import QueryLakeClient

client = QueryLakeClient(base_url="http://127.0.0.1:8000")
summary = client.projection_diagnostics_summary()

print(summary.projection_ids_needing_build())
print([row.projection_id for row in summary.ready_projections()])
print([row.projection_id for row in summary.blocked_projections()])
print([row.projection_id for row in summary.projections_for_backend("opensearch")])
print([row.projection_id for row in summary.projections_for_lane("dense_vector")])
```

Available helpers on `ProjectionDiagnosticsSummary`:

| Method | Purpose |
|---|---|
| `ready_projections()` | rows already built and ready |
| `actionable_projections(allow_degraded=True)` | projections that are declared/executable enough to work on next |
| `blocked_projections(allow_degraded=True)` | projections blocked by support/config/runtime state |
| `projection_ids_needing_build(allow_degraded=True)` | compact worklist of projection ids that should be built next |
| `projections_for_backend(backend_name)` | filter by target backend, e.g. `opensearch` |
| `projections_for_lane(lane_family)` | filter by lane family, e.g. `lexical_bm25` or `dense_vector` |

Each `ProjectionDiagnosticSummaryItem` also exposes:

| Method | Purpose |
|---|---|
| `is_ready()` | projection is built and ready |
| `is_available(allow_degraded=True)` | projection is usable on the active profile |
| `needs_build(allow_degraded=True)` | projection is actionable but not yet built |

Thin client wrapper:

| Method | Equivalent |
|---|---|
| `client.projection_ids_needing_build(allow_degraded=True)` | `client.projection_diagnostics_summary().projection_ids_needing_build(...)` |

When you need to test whether the current deployment can actually execute a refresh, use:

```python
report = client.projection_refresh_run_summary(
    {"projection_id": "document_chunk_lexical_projection_v1", "collection_ids": ["c1"]}
)

if report.has_writer_gap():
    print("Projection plumbing is still missing an external writer.")
    print(report.skipped_modes())
```

That is deliberately different from `projection_ids_needing_build()`: a projection can be relevant to the active profile but still not be buildable yet if the profile has no concrete writer implementation for that lane/backend.

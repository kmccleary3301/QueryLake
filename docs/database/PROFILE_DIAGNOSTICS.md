# QueryLake Profile Diagnostics

[![Docs Checks](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml/badge.svg)](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml)
[![SDK Checks](https://github.com/kmccleary3301/QueryLake/actions/workflows/sdk_checks.yml/badge.svg)](https://github.com/kmccleary3301/QueryLake/actions/workflows/sdk_checks.yml)

This document defines the operator-facing diagnostics surface for QueryLake database compatibility profiles.

| Field | Value |
|---|---|
| Audience | deployment operators, backend contributors, SDK consumers |
| Use this when | validating a profile before startup, checking whether a route is executable, or inspecting split-stack readiness |
| Prerequisites | [`DB_COMPAT_PROFILES.md`](./DB_COMPAT_PROFILES.md), [`RETRIEVAL_EXECUTION_BOUNDARY.md`](./RETRIEVAL_EXECUTION_BOUNDARY.md) |
| Related docs | [`AUTHORITY_PROJECTION_MODEL.md`](./AUTHORITY_PROJECTION_MODEL.md), [`../sdk/API_REFERENCE.md`](../sdk/API_REFERENCE.md), [`SDK_PROFILE_AWARE_CLIENTS.md`](./SDK_PROFILE_AWARE_CLIENTS.md) |
| Status | active, phase-2/phase-3 diagnostics contract |

## Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /v1/profile-diagnostics` | public/operator diagnostics for the active DB profile |
| `GET /v2/kernel/profile-diagnostics` | kernel/runtime diagnostics for the active DB profile |
| `GET /v1/profile-bringup` | aggregated bring-up view combining route readiness, backend connectivity, and projection readiness |
| `GET /v2/kernel/profile-bringup` | kernel/runtime bring-up view for the active DB profile |
| `GET /readyz` | compact startup-validation and bring-up summary embedded into readiness output |

## What diagnostics contain

The diagnostics payload is intended to answer four questions directly:

1. Which profile is active?
2. Is the profile boot-ready on this deployment?
3. Which retrieval routes are actually executable?
4. What is the intended MVP scope if this profile is still only a target?

Current payload sections:

| Section | Meaning |
|---|---|
| `profile` | active deployment profile metadata, including normalized `maturity` |
| `capabilities` | capability map and support states |
| `configuration` | required env/config keys and whether they are valid |
| `execution_target` | intended maturity and MVP surface for the profile |
| `startup_validation` | boot readiness summary |
| `route_summary` | operator-facing rollup of executable vs runtime-ready routes and blocker counts |
| `route_executors` | route-level executor metadata for the active profile, including lane adapters, declared projection descriptors, explicit route projection targets, route-level projection readiness, and lexical semantics summaries for lexical surfaces |
| `lane_diagnostics` | lane-family-level support and placeholder metadata, including sparse and graph lanes even when no direct route surface exists yet |
| `backend_connectivity` | backend reachability or configuration state for authority and projection planes |
| `backend_connectivity.*.target` | redacted target identity for the active plane, such as scheme/host/port/database or index namespace |

The same DB-compat contract layer now also standardizes structured error payload fields for profile/configuration failures and unsupported route requests.

| Field | Meaning |
|---|---|
| `docs_ref` | stable documentation pointer for the failing contract surface |
| `retryable` | whether a retry without changing profile/config is expected to help |

`GET /readyz` is intentionally compact, but it now mirrors the most operationally relevant bring-up fields as well:

| Field | Meaning |
|---|---|
| `db_profile` | active profile metadata from the capability surface |
| `db_profile_diagnostics` | compact startup validation rollup |
| `db_profile_bringup.summary` | compact bring-up rollup for projections, runtime-ready routes, and backend reachability |
| `db_profile_bringup.projection_ids_needing_build` | required projection ids still blocking runtime readiness |
| `db_profile_bringup.route_runtime_blocked_ids` | currently blocked route ids |
| `db_profile_bringup.backend_unreachable_planes` | required backend planes that are configured but not reachable |

## Startup-validation rules

`startup_validation.boot_ready` is only `true` when all of the following are true:

- the selected profile is implemented,
- required configuration is present and valid,
- and every route the profile declares as `supported` or `degraded` in its own MVP scope is executable.

Planned profiles are expected to report:

- `profile_implemented = false`
- `boot_ready = false`
- a concrete `validation_error`

That is intentional. Planned profiles should be visible and diagnosable without pretending they are executable.

For executable split-stack targets, diagnostics now distinguish:

| Field | Meaning |
|---|---|
| `route_execution_ready` | all required routes in the profile's declared MVP scope are executable |
| `route_runtime_ready` | all required routes are executable and have their required projections ready on this deployment |
| `backend_connectivity_ready` | all required backend planes passed active connectivity probes when probing is enabled |
| `inspected_route_ids` | the canonical route surface this diagnostics payload actually evaluated |
| `full_route_coverage_ready` | every inspected canonical route is executable |
| `full_runtime_coverage_ready` | every inspected canonical route is runtime-ready on this deployment |
| `declared_executable_routes_runtime_ready` | every route the active profile explicitly declares executable is runtime-ready right now |
| `required_route_ids` | routes that must work for the profile to be considered boot-ready |
| `optional_route_ids` | routes intentionally left as `planned` or `unsupported` in the current target slice |
| `declared_executable_route_ids` | canonical executable route ids from the active profile's declared support matrix |
| `declared_optional_route_ids` | canonical optional route ids from the active profile's declared support matrix |
| `non_executable_required_routes` | blockers that make `boot_ready = false` |
| `non_runtime_ready_required_routes` | required routes blocked by missing projections or other runtime-readiness gaps |
| `non_reachable_required_backends` | required backend planes that failed active connectivity probes |
| `non_executable_optional_routes` | visible gaps that do not block profile startup readiness |
| `non_runtime_ready_optional_routes` | optional routes blocked by runtime-readiness gaps |
| `validation_error_kind` | normalized operator-facing failure class for the current startup state |
| `validation_error_details` | structured blocker details including affected routes, projection ids, and backend planes where applicable |
| `validation_error_hint` | concise operator-facing remediation hint for the current blocker class |
| `validation_error_docs_ref` | docs anchor for the recommended remediation path |
| `validation_error_command` | bootstrap/repair command when QueryLake can suggest one deterministically |

The new `route_summary` section is the fastest way to answer “what is working right now?” without iterating every route row manually.

| Field | Meaning |
|---|---|
| `inspected_route_count` | number of canonical routes covered by the diagnostics payload |
| `executable_route_count` | count of routes executable under the active profile |
| `runtime_ready_route_count` | count of routes runnable right now on this deployment |
| `declared_route_count` | count of canonical routes in the active profile's declared support matrix |
| `declared_executable_route_count` | count of canonical executable routes declared by the active profile |
| `declared_optional_route_count` | count of canonical optional routes declared by the active profile |
| `declared_executable_runtime_ready_count` | count of declared executable routes currently runtime-ready |
| `declared_executable_runtime_blocked_count` | count of declared executable routes still runtime-blocked |
| `projection_blocked_route_count` | executable routes blocked only by missing external projections |
| `runtime_blocked_route_count` | routes not currently runnable for any reason |
| `declared_route_support` | canonical support matrix for the active profile's declared route slice |
| `support_state_counts` | aggregate route counts by `supported` / `degraded` / `planned` / `unsupported` |
| `blocker_kind_counts` | aggregate counts by normalized blocker kind |
| `projection_blocked_route_ids` | route ids blocked by projection readiness |
| `runtime_blocked_route_ids` | route ids not runnable right now |
| `declared_executable_runtime_ready_ids` | declared executable route ids currently runtime-ready |
| `declared_executable_runtime_blocked_ids` | declared executable route ids currently blocked |

## Profile bring-up aggregation

When operators need a single preflight surface instead of stitching together profile diagnostics and projection diagnostics manually, use `GET /v1/profile-bringup`.

That payload adds:

| Field | Meaning |
|---|---|
| `summary.boot_ready` | top-level deployment readiness signal |
| `summary.configuration_ready` | required config present and valid |
| `summary.route_execution_ready` | declared required routes have executable resolvers |
| `summary.route_runtime_ready` | required routes are runnable right now |
| `summary.backend_connectivity_ready` | required backend planes are reachable when probes are enabled |
| `summary.projection_status_counts` | compact counts of `ready` / `building` / `stale` / `failed` / `absent` projection states |
| `summary.route_runtime_blocker_kind_counts` | compact counts of runtime blocker kinds across inspected routes |
| `summary.lexical_degraded_route_count` | count of runtime-visible routes whose lexical semantics are degraded or partially unsupported |
| `summary.lexical_gold_recommended_route_count` | count of routes that should steer operators toward the gold profile for exact lexical constraints |
| `summary.route_lexical_support_class_counts` | aggregate counts of `native_supported` / `degraded_supported` / `unsupported` lexical route summaries |
| `summary.lexical_capability_blocker_counts` | aggregate counts of lexical capability blockers across inspected routes |
| `summary.route_recovery_count` | count of route-level recovery entries explaining how blocked or degraded routes can be remediated |
| `summary.bootstrapable_required_projection_count` | required projections that the active profile can build immediately |
| `summary.nonbootstrapable_required_projection_count` | required projections that still block runtime but are not buildable on the active profile |
| `summary.bootstrapable_recommended_projection_count` | recommended projections that the active profile can build immediately |
| `summary.nonbootstrapable_recommended_projection_count` | recommended projections that are declared but not buildable on the active profile |
| `required_projection_ids` | projections the active profile depends on for current executable routes |
| `ready_projection_ids` | required projections already built and ready |
| `projection_ids_needing_build` | required projections still missing or stale |
| `bootstrapable_required_projection_ids` | required projections that can be built immediately with the active profile/tooling |
| `nonbootstrapable_required_projection_ids` | required projections that remain runtime blockers but need profile/config/support changes rather than a bootstrap command |
| `recommended_projection_ids` | executable canonical projections that are not required for the current public route slice, but are recommended next bootstrap targets |
| `recommended_ready_projection_ids` | recommended canonical projections already built and ready |
| `recommended_projection_ids_needing_build` | recommended canonical projections that still need bootstrap/rebuild work |
| `bootstrapable_recommended_projection_ids` | recommended projections that can be built immediately |
| `nonbootstrapable_recommended_projection_ids` | recommended projections that are not buildable on the active profile |
| `projection_building_ids` | required projections currently building |
| `projection_failed_ids` | required projections currently failed |
| `projection_stale_ids` | required projections currently stale/invalidated |
| `projection_absent_ids` | required projections that do not yet have materialized state |
| `lexical_degraded_route_ids` | route ids whose lexical semantics are degraded or partially unsupported on the active profile |
| `lexical_gold_recommended_route_ids` | route ids that should prefer the gold profile when exact lexical constraints matter |
| `route_blocked_projection_ids` | unique projection ids currently blocking one or more runtime routes |
| `backend_targets` | compact authority/projection-plane target summaries, including endpoint/env source and probe status |
| `next_actions` | ordered remediation hints generated from configuration, backend connectivity, projection, and route-runtime blockers |
| `route_recovery` | per-route recovery summaries describing runtime state, blocking projection ids, bootstrapability, lexical support class, and profile-specific recovery hints |
| `route_runtime_ready_ids` | canonical routes runnable right now |
| `route_runtime_blocked_ids` | canonical routes still blocked |
| `backend_unreachable_planes` | backend planes currently preventing runtime readiness |
| `route_executors[*].projection_targets` | explicit route-level materialization targets for each declared projection dependency, including `authority_model`, `source_scope`, `record_schema`, and `target_backend_name` |
| `route_executors[*].compatibility_projection_target_ids` | route-level projection targets still backed by `*_compatibility` authority models |
| `route_executors[*].canonical_projection_target_ids` | route-level projection targets already backed by canonical authority models such as `document_segment` |
| `route_executors[*].compatibility_projection_reliance` | whether the route still depends on compatibility projections |

`profile_bringup` intentionally nests both `profile_diagnostics` and `projection_diagnostics` so operators can escalate from a compact summary into the full contract without issuing multiple extra requests.

Even when a split-stack profile is fully runtime-ready, bring-up can still surface lexical caveats. That is intentional. Runtime readiness means the declared slice is operational; it does **not** imply full gold-stack lexical semantics.

The `route_executors[*].projection_targets` rows are the route-facing counterpart to nested `projection_diagnostics.projection_items[*].materialization_target`:

- `projection_diagnostics` answers: “what does this projection descriptor mean globally on this profile?”
- `route_executors[*].projection_targets` answers: “what exact projection targets does this route currently depend on?”

Those two surfaces should now agree on:

- `projection_id`
- `authority_model`
- `source_scope`
- `record_schema`
- `target_backend_name`

The canonical operator signal is:

- `lexical_degraded_route_ids`: routes whose lexical behavior is degraded or partially unsupported
- `lexical_gold_recommended_route_ids`: routes that should steer exact lexical workloads back to the gold ParadeDB profile
- `next_actions[*].kind = prefer_gold_profile_for_exact_lexical_constraints`: remediation guidance for exact phrase/proximity/hard-constraint requirements
- `compatibility_projection_route_ids`: routes still leaning on compatibility projections instead of canonical authority-backed projection targets

The projection lifecycle is now surfaced directly at the bring-up layer as well:

- `projection_building_ids`
- `projection_failed_ids`
- `projection_stale_ids`
- `projection_absent_ids`
- `summary.required_projection_status_counts`

That lets operators answer “what kind of projection work is left?” without traversing the nested `projection_diagnostics.projection_items[]` list first.
These fields are intentionally scoped to the **required bring-up set**, not every descriptor in the profile-wide projection registry. Use nested `projection_diagnostics` when you need the full descriptor inventory, including planned or otherwise non-required projections.

The additional `recommended_*` projection fields answer the next question after a profile is runtime-ready:

- “Which canonical projections should I bootstrap next so this deployment relies less on compatibility projections over time?”

That distinction matters on the first Aurora/OpenSearch split-stack slice, because the currently supported public route surface still depends on compatibility projections while canonical segment lexical/dense projections are already executable.

The `route_recovery` list is the fastest way to answer:

- “Why is this route blocked right now?”
- “Can I fix it by bootstrapping projections, or is this a true profile limitation?”
- “Is the route technically runnable but still a bad fit for exact lexical workloads?”

Each row carries:

| Field | Meaning |
|---|---|
| `route_id` | canonical route identifier |
| `implemented` | whether the route has an executable resolver on the active profile |
| `support_state` | normalized support state for the route |
| `runtime_ready` | whether the route is runnable right now |
| `projection_ready` | whether projection readiness is satisfied |
| `blocker_kinds` | compact blocker classification list |
| `bootstrapable_blocking_projection_ids` | route blockers fixable immediately by running the profile bootstrap command |
| `nonbootstrapable_blocking_projection_ids` | route blockers that require profile/config/support changes rather than bootstrap |
| `bootstrap_command` | route-scoped bootstrap suggestion when applicable |
| `lexical_support_class` | `native_supported`, `degraded_supported`, or `unsupported` |
| `gold_recommended_for_exact_constraints` | whether operators should prefer the gold profile for exact phrase/proximity/hard-constraint workloads |
| `exact_constraint_degraded_capabilities` | lexical capabilities that degrade but still execute |
| `exact_constraint_unsupported_capabilities` | lexical capabilities that are not available on the active profile |

When split-stack projections are the blocker, the payload now includes a concrete bootstrap command in the highest-priority remediation item, for example:

```bash
python scripts/db_compat_profile_bootstrap.py --profile aws_aurora_pg_opensearch_v1
```

When that bootstrap command is run with `--validate-runtime-ready`, it now returns a full before/after bring-up delta:

| Field | Meaning |
|---|---|
| `profile_diagnostics_before` | bring-up snapshot before the bootstrap run |
| `profile_diagnostics` | bring-up snapshot after the bootstrap run |
| `bootstrap_delta.projection_ids_recovered` | projections that moved into `ready` during the run |
| `bootstrap_delta.route_ids_recovered` | routes that became runtime-ready after the run |
| `bootstrap_delta.bootstrap_improved_runtime_readiness` | whether the bootstrap run improved readiness materially |
| `bootstrap_report.metadata.lifecycle_outcome_counts` | aggregate lifecycle outcomes such as `materialized_from_absent`, `refreshed_from_stale`, or `unchanged_ready` |

For repeatable checks, the repository now includes two scriptable surfaces:

| Command | Purpose |
|---|---|
| `python scripts/db_compat_profile_smoke.py ...` | route-level diagnostics smoke over executability and runtime blockers |
| `python scripts/db_compat_profile_bringup_smoke.py ...` | compact bring-up preflight over configuration, projection readiness, backend connectivity, and runtime-ready routes |
| `make ci-db-compat-bringup` | opinionated Aurora/OpenSearch bring-up smoke using the current executable split-stack fixture |
| `make ci-db-compat-bootstrap` | fixture-backed Aurora/OpenSearch bootstrap-and-verify gate for local/CI contract validation |

Use the bring-up harness when you want a single deterministic go/no-go check for the current split-stack slice instead of manually correlating multiple payloads.

Connectivity payloads intentionally expose a **safe** parsed target summary when QueryLake can derive one without surfacing credentials:

| Plane | Example target fields |
|---|---|
| authority | `scheme`, `host`, `port`, `database` |
| projection | `scheme`, `host`, `port`, `index_namespace` |

Passwords, usernames, and query-string secrets are intentionally not emitted.

The bootstrap harness now also supports explicit idempotency/state assertions, for example:

```bash
python scripts/db_compat_profile_bootstrap.py \
  --profile aws_aurora_pg_opensearch_v1 \
  --expect-executed-action-count 0 \
  --expect-skipped-action-count 3 \
  --expect-projection-status document_chunk_lexical_projection_v1=ready
```

That is useful when validating that a rerun of projection bootstrap did not unnecessarily rebuild already-ready projections.

Current `validation_error_kind` values:

| Kind | Meaning |
|---|---|
| `profile_not_implemented` | the selected profile is declared but not executable in this build |
| `configuration_invalid` | required environment/config values are missing or malformed |
| `route_non_executable` | a required route in the profile slice has no executable resolver |
| `projection_runtime_blocked` | required routes are executable in principle but blocked by projection state |
| `projection_missing` | required external projections have not been built yet |
| `projection_building` | required external projections are currently building |
| `projection_failed` | required external projection builds failed and need repair |
| `projection_stale` | required external projections exist but are invalidated/stale |
| `route_not_runtime_ready` | required routes are runtime-blocked for non-projection reasons |
| `backend_unreachable` | required backend planes failed active connectivity probes |

Projection-specific kinds distinguish the remediation path. When one is active, `validation_error_details` includes:

- `route_ids`
- `projection_blocker_routes`
- `projection_blocker_projection_ids`
- `blocker_kind_counts`

## First split-stack target

The current first split-stack target is:

| Profile | Maturity | Intended MVP |
|---|---|---|
| `aws_aurora_pg_opensearch_v1` | `target` | authority in Aurora/PostgreSQL, lexical+dense retrieval in OpenSearch projections |

Current explicit MVP stance:

| Surface | State | Notes |
|---|---|---|
| `search_hybrid.document_chunk` | supported | first executable slice: lexical+dense hybrid on document-chunk projections |
| `search_bm25.document_chunk` | supported | first executable slice: BM25-like lexical retrieval on document-chunk projections |
| `search_file_chunks` | supported | file-chunk lexical retrieval now follows the same OpenSearch projection/index path |
| sparse lane | unsupported | intentionally disabled in the first executable slice |
| graph traversal | unsupported | out of scope for the first split-stack slice |

That means the split-stack profile can now report full canonical route coverage for its current inspected retrieval surface while still honestly declaring sparse and graph work out of scope.

## PostgreSQL + pgvector light profile

The current light-profile stance is intentionally narrower:

| Profile | Maturity | Intended MVP |
|---|---|---|
| `postgres_pgvector_light_v1` | `target` | co-located PostgreSQL authority plus dense-only document-chunk retrieval on pgvector |

Current explicit MVP stance:

| Surface | State | Notes |
|---|---|---|
| `search_hybrid.document_chunk` | supported | dense-only route; callers must disable BM25 and sparse lanes |
| `search_bm25.document_chunk` | unsupported | no lexical engine is present |
| `search_file_chunks` | unsupported | no lexical engine is present |
| sparse lane | unsupported | intentionally disabled |
| graph traversal | planned | outside the first light-profile slice |

## Route-level lexical semantics

For lexical routes and hybrid routes that include a lexical lane, diagnostics now include:

| Field | Meaning |
|---|---|
| `route_executors[*].lexical_semantics.support_class` | normalized summary such as `native_supported`, `degraded_supported`, or `unsupported` |
| `route_executors[*].lexical_semantics.capability_states` | per-capability support states for BM25, advanced operators, phrase boost, proximity, and hard constraints |
| `route_executors[*].lexical_semantics.degraded_capabilities` | lexical features that are allowed but degraded on the active profile |
| `route_executors[*].lexical_semantics.unsupported_capabilities` | lexical features that must fail fast on the active profile |

This is the operator-facing answer to:

- “Does this route support quoted phrases natively?”
- “Are phrase/proximity semantics degraded on this profile?”
- “Will hard lexical constraints fail before query execution?”

For the current first split-stack slice, the expected pattern is:

- BM25 itself: `supported`
- advanced operators: `degraded`
- phrase boost / proximity: degraded enough that exact lexical semantics should still prefer the gold profile
- hard constraints: `unsupported`, and therefore still a gold-profile concern when strict lexical filtering is required
- advanced operators / phrase boost / proximity: `degraded`
- hard lexical constraints: `unsupported`

The light profile therefore shows a narrower required-route set in diagnostics than the gold profile or the first split-stack OpenSearch profile.


Each `route_executors[]` row now also includes route-level projection readiness fields:

| Field | Meaning |
|---|---|
| `projection_descriptors` | named projection descriptors that the route depends on |
| `projection_dependency_mode` | `optional_compatibility` on the gold stack, `required_external_projection` on split-stack routes that need external indexes |
| `projection_ready` | whether the route's declared projection dependencies are currently built and ready for execution |
| `projection_missing_descriptors` | descriptors whose current build state is not `ready` |
| `projection_readiness` | per-descriptor readiness snapshot including `build_status`, `support_state`, `executable`, `action_mode`, and build-state metadata when present |
| `runtime_ready` | whether the route is runnable right now on this deployment |
| `runtime_blockers` | structured reasons the route is not currently runnable, such as missing external projections or missing writer implementations |

This is the bridge between route-level compatibility and the authority/projection model. A route can now be:

- executable in principle,
- supported by the active profile,
- but still not projection-ready on this deployment because required external indexes are either not built yet or do not yet have a writer implementation on the active profile.

That distinction is intentional. QueryLake should expose it directly instead of burying it inside backend-specific failure modes.

Current blocker semantics:

| Blocker kind | Meaning |
|---|---|
| `projection_not_ready` | the route depends on a projection that is buildable on this profile but currently not in `ready` state |
| `projection_building` | the route depends on a projection currently in `building` state |
| `projection_failed` | the route depends on a projection whose most recent build failed |
| `projection_stale` | the route depends on a projection that was previously ready but has since been invalidated |
| `projection_writer_unavailable` | the route depends on a projection in the profile slice, but QueryLake does not yet implement a writer for that backend/profile combination |

For the current first split-stack slice, `search_file_chunks` now follows the same runtime-readiness model as the document-chunk lexical and hybrid routes. In practice, that means its normal blocker on `aws_aurora_pg_opensearch_v1` is also `projection_not_ready` until `file_chunk_lexical_projection_v1` reaches `ready`.

SDK helpers built directly on top of these route fields now include:
- `route_blocker_kinds(route_id)`
- `route_blocking_projection_ids(route_id)`
- `route_lane_backends(route_id)`
- `route_adapter_ids(route_id)`
- `route_summary()`
- `runtime_blocker_summary()`
- `runtime_blocked_routes()`

## Lane diagnostics

`lane_diagnostics` exists because route-level diagnostics are not sufficient to describe every retrieval lane honestly.

In particular:

- `sparse_vector` may be intentionally unsupported on a profile even when hybrid retrieval exists in degraded form,
- `graph_traversal` may be declared at the capability layer before the compatibility layer exposes a concrete route surface,
- and operators still need an inspectable contract for those lanes.

Each `lane_diagnostics[]` row includes:

| Field | Meaning |
|---|---|
| `lane_family` | normalized lane id such as `lexical_bm25`, `dense_vector`, `sparse_vector`, or `graph_traversal` |
| `backend` | backend family currently assigned to that lane on the active profile |
| `adapter_id` | concrete or placeholder adapter id for that lane |
| `support_state` | `supported`, `degraded`, `unsupported`, or `planned` |
| `implemented` | whether QueryLake currently implements this lane on the active profile |
| `route_surface_declared` | whether the compatibility layer currently exposes a direct route surface for this lane |
| `capability_ids` | capability ids that define the lane contract |
| `execution_mode` | `native` for executable lane implementations; `placeholder` for intentionally non-executable contracts |
| `blocked_by_capability` | primary capability preventing execution when the lane is placeholder-backed |
| `placeholder_executor_id` | stable placeholder executor id used by diagnostics for unsupported sparse/graph lanes |
| `recommended_profile_id` | profile to prefer when exact semantics are required |
| `hint` | remediation hint for placeholder-backed lanes |
| `notes` | operator-facing caveats for placeholder or indirect lanes |

This is the stable place to inspect sparse and graph status on split-stack profiles.

As of the current split-stack tranche, `boot_ready` follows `route_runtime_ready`, not just `route_execution_ready`. That means a profile with declared route executors but missing required external projections is not considered startup-ready yet.

When `QUERYLAKE_PROFILE_DIAGNOSTICS_PROBE=1`, `boot_ready` also follows `backend_connectivity_ready`. In practice:

- if the authority probe fails, `non_reachable_required_backends` includes `authority`
- if the OpenSearch/projection probe fails for a required split-stack route surface, `non_reachable_required_backends` includes `projection`

That is intentional. Once probing is enabled, backend reachability failures are treated as startup blockers instead of passive informational warnings.

## Client guidance

SDK clients should use diagnostics when they need more than simple capability flags.

Use `capabilities` when you only need support-state checks.

Use `profile-diagnostics` when you need:

- configuration readiness,
- route-executor visibility,
- or deployment/operator-facing explanations.

For concrete SDK usage patterns, see:

- [`SDK_PROFILE_AWARE_CLIENTS.md`](./SDK_PROFILE_AWARE_CLIENTS.md)

The important distinction is:

| Question | Diagnostics interpretation |
|---|---|
| “Is this route part of the supported surface for the active profile?” | `route_executable(...)` |
| “Are this deployment's required external projections built?” | `route_projection_ready(...)` |
| “Will the route execute successfully right now?” | `route_runtime_ready(...)` |

## Backend connectivity semantics

`backend_connectivity` now reports structured plane-specific entries instead of bare placeholder strings.

Current statuses include:

| Status | Meaning |
|---|---|
| `assumed_local_sql_engine` | the current gold deployment relies on the co-located SQL authority engine |
| `assumed_current_sql_engine` | the active split-stack profile still resolves authority access through the current SQLAlchemy engine when active probing is disabled |
| `configured_authority_target` | the split-stack profile declares an explicit authority DSN override and diagnostics are reporting against that target even when active probing is disabled |
| `co_located_with_authority` | the projection backend is effectively part of the same gold SQL stack |
| `configured_unprobed` | required configuration exists, but active reachability probing is disabled |
| `reachable` | an optional lightweight probe succeeded |
| `unreachable` | an optional lightweight probe failed |
| `configuration_incomplete` | required configuration for that backend plane is missing or malformed |
| `not_probed` | the backend family is known, but explicit probing is not implemented yet |

For split-stack OpenSearch profiles, projection probing can be enabled with:

- `QUERYLAKE_PROFILE_DIAGNOSTICS_PROBE=1`
- optional timeout override: `QUERYLAKE_PROFILE_DIAGNOSTICS_PROBE_TIMEOUT_SECONDS`
- optional authority override: `QUERYLAKE_AUTHORITY_DATABASE_URL`

For SQL-backed authority planes, the same probe flag now enables a lightweight `SELECT 1` probe against the currently configured SQL authority DSN. That means both:

- `paradedb_postgres_gold_v1`
- `aws_aurora_pg_opensearch_v1`

can now report `reachable` or `unreachable` on the authority plane when probes are enabled. QueryLake still remains conservative for backend families that do not yet have a dedicated authority probe implementation.

If `QUERYLAKE_AUTHORITY_DATABASE_URL` is set on a split-stack SQL profile, diagnostics will also surface:

- `backend_connectivity.authority.database_url_env = "QUERYLAKE_AUTHORITY_DATABASE_URL"`
- `backend_connectivity.authority.status = "configured_authority_target"` when probes are disabled

If it is unset, the authority plane falls back to `QUERYLAKE_DATABASE_URL`, and diagnostics will report `database_url_env = "QUERYLAKE_DATABASE_URL"` instead.

# QueryLake SDK API Reference (Python)

[![Docs Checks](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml/badge.svg)](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml)
[![SDK Checks](https://github.com/kmccleary3301/QueryLake/actions/workflows/sdk_checks.yml/badge.svg)](https://github.com/kmccleary3301/QueryLake/actions/workflows/sdk_checks.yml)

Method-level reference for the Python SDK and CLI command surface.

| Field | Value |
|---|---|
| Audience | SDK users, maintainers, and developers writing integration code |
| Use this when | Use this when you already know the basic workflow and need method names, return-shape expectations, or CLI coverage details. |
| Prerequisites | Familiarity with the SDK quickstart and core QueryLake auth/search concepts. |
| Related docs | [`SDK_QUICKSTART.md`](SDK_QUICKSTART.md), [`BULK_INGEST_REFERENCE.md`](BULK_INGEST_REFERENCE.md), [`LOCAL_PROFILE_WORKFLOW.md`](LOCAL_PROFILE_WORKFLOW.md) |
| Status | 🟢 maintained reference |

## Client classes

| Class | Use case |
|---|---|
| `QueryLakeClient` | Synchronous scripts, notebooks, backend services |
| `AsyncQueryLakeClient` | Async services and task runners |

## Authentication model

SDK auth payloads map directly to QueryLake backend auth contracts:

- OAuth2 token: `{"oauth2": "<token>"}`
- API key: `{"api_key": "sk-..."}` (if enabled by backend policy)

Typical bootstrap:

1. `client.login(username=..., password=...)`
2. SDK stores returned OAuth2 token in-memory for subsequent calls

## QueryLakeClient methods

### Core connectivity

- `healthz() -> dict`
- `readyz() -> dict`
- `readyz_summary() -> ReadyzSummary`
- `capabilities() -> dict`
- `kernel_capabilities() -> dict`
- `capabilities_summary() -> CapabilitiesSummary`
- `representation_scopes() -> dict[str, dict[str, Any]]`
- `route_support_manifest_v2() -> dict[str, dict[str, Any]]`
- `route_representation_scope_id_from_capabilities(route_id) -> str | None`
- `route_capability_dependencies_from_capabilities(route_id) -> list[str]`
- `route_declared_executable_from_capabilities(route_id) -> bool`
- `route_declared_optional_from_capabilities(route_id) -> bool`
- `support_state(capability_id) -> str | None`
- `supports(capability_id, allow_degraded=True) -> bool`
- `profile_diagnostics() -> dict`
- `kernel_profile_diagnostics() -> dict`
- `profile_diagnostics_summary() -> ProfileDiagnosticsSummary`
- `kernel_profile_diagnostics_summary() -> ProfileDiagnosticsSummary`
- `diagnostics_representation_scopes() -> dict[str, dict[str, Any]]`
- `diagnostics_route_support_manifest_v2() -> dict[str, dict[str, Any]]`
- `profile_bringup() -> dict`
- `kernel_profile_bringup() -> dict`
- `profile_bringup_summary() -> ProfileBringupSummary`
- `kernel_profile_bringup_summary() -> ProfileBringupSummary`
- `bringup_representation_scopes() -> dict[str, dict[str, Any]]`
- `bringup_route_support_manifest_v2() -> dict[str, dict[str, Any]]`
- `bringup_bootstrap_command() -> str | None`
- `bringup_next_actions() -> list[dict]`
- `bringup_backend_targets() -> list[dict]`
- `bringup_lexical_degraded_routes() -> list[str]`
- `bringup_lexical_gold_recommended_routes() -> list[str]`
- `bringup_declared_route_support() -> dict[str, str]`
- `bringup_route_declared_executable(route_id) -> bool`
- `bringup_route_declared_optional(route_id) -> bool`
- `bringup_route_required_projection_descriptor_ids(route_id) -> list[str]`
- `bringup_declared_executable_routes() -> list[str]`
- `bringup_declared_optional_routes() -> list[str]`
- `bringup_declared_runtime_ready_routes() -> list[str]`
- `bringup_declared_runtime_blocked_routes() -> list[str]`
- `bringup_declared_routes_runtime_ready() -> bool`
- `bringup_route_recovery() -> list[dict]`
- `bringup_route_recovery_entry(route_id) -> dict | None`
- `bringup_projection_status_buckets() -> dict[str, list[str]]`
- `bringup_recommended_projection_status_buckets() -> dict[str, list[str]]`
- `local_profile_maturity() -> str | None`
- `local_support_matrix() -> list[dict]`
- `local_route_support_entry(route_id) -> dict`
- `local_route_representation_scope_id(route_id) -> str | None`
- `local_route_representation_scope(route_id) -> dict`
- `local_route_capability_dependencies(route_id) -> list[str]`
- `local_route_declared_executable(route_id) -> bool`
- `local_route_lexical_support_class(route_id) -> str | None`
- `local_route_dense_sidecar_ready(route_id) -> bool`
- `local_route_dense_sidecar_cache_warmed(route_id) -> bool`
- `local_route_dense_sidecar_indexed_record_count(route_id) -> int`
- `local_promotion_status() -> dict`
- `local_declared_executable_route_ids() -> list[str]`
- `local_declared_runtime_ready_route_ids() -> list[str]`
- `local_declared_runtime_blocked_route_ids() -> list[str]`
- `local_required_projection_ids() -> list[str]`
- `local_representation_scope_ids() -> list[str]`
- `projection_diagnostics_summary() -> ProjectionDiagnosticsSummary`
  - each `ProjectionDiagnosticSummaryItem` now includes `materialization_target` with the normalized authority/projection target contract
- `route_support_state(route_id) -> str | None`
- `route_declared_executable(route_id) -> bool`
- `route_declared_optional(route_id) -> bool`
- `route_required_projection_descriptor_ids(route_id) -> list[str]`
- `route_executable(route_id, allow_degraded=True) -> bool`
- `route_runtime_ready(route_id, allow_degraded=True) -> bool`
- `route_state(route_id, allow_degraded=True) -> str`
- `route_is_degraded(route_id) -> bool`
- `route_blocked_by_projection(route_id, allow_degraded=True) -> bool`
- `route_blocked_by_backend_connectivity(route_id, allow_degraded=True) -> bool`
- `route_gold_recommended_for_exact_constraints(route_id) -> bool`
- `route_exact_constraint_degraded_capabilities(route_id) -> list[str]`
- `route_exact_constraint_unsupported_capabilities(route_id) -> list[str]`
- `backend_connectivity_entry(plane) -> BackendConnectivitySummary | None`
- `backend_connectivity_entries() -> dict[str, BackendConnectivitySummary]`
- `ping() -> Any`
- `list_models() -> dict`
- `chat_completions(payload: dict) -> dict`
- `embeddings(payload: dict) -> dict`

### Auth/session

- `login(username, password) -> dict`
- `add_user(username, password) -> dict`
- `set_auth(auth=..., oauth2=..., api_key=...)`

### Collections + documents

- `create_collection(name, description=None, public=False, organization_id=None) -> dict`
- `list_collections(organization_id=None, global_collections=False) -> dict`
- `fetch_collection(collection_hash_id) -> dict`
- `modify_collection(collection_hash_id, title=None, description=None) -> Any`
- `list_collection_documents(collection_hash_id, limit=100, offset=0) -> list[dict]`
- `delete_document(document_hash_id) -> Any`
- `upload_document(file_path, collection_hash_id, idempotency_key=None, ...) -> dict`
- `upload_directory(collection_hash_id, directory=..., file_paths=..., checkpoint_file=..., resume=False, checkpoint_save_every=1, strict_checkpoint_match=True, dedupe_by_content_hash=False, dedupe_scope="run-local", idempotency_strategy="none", idempotency_prefix="qlsdk", ...) -> dict`
- `upload_directory_with_options(collection_hash_id, options=UploadDirectoryOptions(...)) -> dict`

### Retrieval

- `search_hybrid(query, collection_ids, ..., **kwargs) -> list[dict]`
- `search_hybrid_with_metrics(query, collection_ids, ..., **kwargs) -> dict`
- `search_hybrid_with_options(query, collection_ids, options=HybridSearchOptions(...), **kwargs) -> list[dict]`
- `search_hybrid_with_metrics_options(query, collection_ids, options=HybridSearchOptions(...), **kwargs) -> dict`
- `search_hybrid_chunks(...) -> list[SearchResultChunk]`
- `count_chunks(collection_ids=None) -> dict`
- `get_random_chunks(limit=5, collection_ids=None) -> list[dict]`

`search_hybrid_with_metrics` returns the orchestrated backend payload shape (`rows`, `duration`, optional plan/queue metadata) when available.

## PDF Output Contract Helper

If you are consuming PDF transcription results or stored document metadata, use:

- `querylake_sdk.parse_pdf_output_contract_summary(...)`

It returns `PdfOutputContractSummary`, which gives typed access to:
- `output_contract`
- `page_source_by_page`
- `page_source_counts`

Current contract values:
- `ocr_markdown`
- `text_layer_fastpath_markdown`
- `mixed_text_layer_fastpath_markdown`

Use this helper when downstream logic needs to branch between:
- OCR-derived markdown
- full text-layer fast path
- mixed per-page OCR/text-layer output

Minimal example:

```python
from querylake_sdk import parse_pdf_output_contract_summary

summary = parse_pdf_output_contract_summary(result)
if summary.is_ocr_markdown():
    ...
elif summary.is_text_layer_fastpath():
    ...
elif summary.is_mixed_text_layer_fastpath():
    page_sources = summary.page_source_by_page
```

Typed option models are available in `querylake_sdk`:

- `UploadDirectoryOptions`
- `HybridSearchOptions`
- builder helpers: `build_upload_directory_options(...)`, `build_hybrid_search_options(...)`

### Escape hatch for all backend functions

- `api(function_name, payload=None, method=\"POST\", auth=None) -> Any`

This keeps the SDK forward-compatible with new backend API functions without waiting for SDK helper wrappers.

## DB compatibility helpers

The SDK exposes parsed helpers for QueryLake's deployment-profile contract.

### `CapabilitiesSummary`

| Method | Meaning |
|---|---|
| `capability(capability_id)` | return a `CapabilitySummary` or `None` |
| `support_state(capability_id)` | support state for a capability |
| `is_supported(capability_id)` | true only for full support |
| `is_available(capability_id, allow_degraded=True)` | true for supported, and optionally degraded |
| `supported_capabilities()` | list supported capabilities |
| `degraded_capabilities()` | list degraded capabilities |
| `unavailable_capabilities()` | list unsupported/planned capabilities |

### `ProfileConfigurationSummary`

| Method | Meaning |
|---|---|
| `missing_requirements()` | config requirements not present |
| `invalid_requirements()` | requirements present but invalid |
| `blocking_requirements()` | requirements blocking execution |

### `ProfileDiagnosticsSummary`

| Method | Meaning |
|---|---|
| `route_executor(route_id)` | return a `RouteExecutorSummary` or `None` |
| `route_support_state(route_id)` | route-level support state |
| `route_representation_scope_id_from_capabilities(route_id)` | representation scope id declared for the route in the capability manifest |
| `route_capability_dependencies_from_capabilities(route_id)` | capability ids the route depends on in the capability manifest |
| `route_executable(route_id, allow_degraded=True)` | whether the route executes on the active profile |
| `route_runtime_ready(route_id, allow_degraded=True)` | whether the route is runnable right now on the deployment |
| `route_state(route_id, allow_degraded=True)` | normalized route state (`runtime_ready`, `blocked_by_projection`, etc.) |
| `route_is_degraded(route_id)` | whether the route is executable but degraded |
| `route_blocked_by_projection(route_id, allow_degraded=True)` | whether projection readiness is the blocking reason |
| `route_blocked_by_backend_connectivity(route_id, allow_degraded=True)` | whether backend reachability is the blocking reason |
| `route_lexical_support_class(route_id)` | normalized lexical semantics summary for the route |
| `route_lexical_capability_states(route_id)` | route-level lexical capability state map |
| `route_lexical_degraded_capabilities(route_id)` | degraded lexical semantics on the route |
| `route_lexical_unsupported_capabilities(route_id)` | unsupported lexical semantics on the route |
| `route_gold_recommended_for_exact_constraints(route_id)` | whether exact lexical workloads on the route should still prefer the gold profile |
| `route_exact_constraint_degraded_capabilities(route_id)` | exact-constraint-related lexical capabilities that degrade on the route |
| `route_exact_constraint_unsupported_capabilities(route_id)` | exact-constraint-related lexical capabilities that must fail fast on the route |
| `route_projection_targets(route_id)` | explicit route-level projection targets with authority model, source scope, record schema, and target backend |
| `route_projection_target_backend_names(route_id)` | compact `projection_id -> target_backend_name` map for route dependencies |
| `executable_routes()` | list executable route executors |
| `degraded_routes()` | list executable-but-degraded route executors |
| `missing_route_executors()` | list planned/non-implemented route executors |
| `backend_connectivity_entry(plane)` | typed connectivity entry for `authority` / `projection` |
| `backend_connectivity_entries()` | typed connectivity map |

### `StartupValidationSummary`

| Method | Meaning |
|---|---|
| `validation_error_kind` | normalized bring-up failure class |
| `validation_error_details` | structured blocker details for projection/backend/runtime bring-up failures |
| `is_configuration_invalid()` | configuration is present but invalid |
| `is_backend_unreachable()` | backend reachability blocks startup |
| `is_projection_runtime_blocked()` | projections block runtime readiness |
| `has_route_execution_gap()` | required routes are not executable |
| `has_route_runtime_gap()` | required routes are executable but not runtime-ready |

### `BackendConnectivitySummary`

| Method | Meaning |
|---|---|
| `is_ready()` | backend plane is ready |
| `is_unreachable()` | backend plane is unreachable |
| `is_not_probed()` | backend plane is configured but not actively probed |
| `blocks_execution()` | backend plane failure should block execution |

Recommended pattern:

1. call `capabilities_summary()` to gate optional lanes such as sparse
2. call `profile_diagnostics_summary()` to determine whether a route is executable
3. reject unsupported strict semantics explicitly instead of silently weakening them

### `ProfileBringupSummary`

Use this when you want one aggregated preflight payload instead of manually correlating route diagnostics, projection readiness, and backend connectivity.

Useful methods:

| Method | Meaning |
|---|---|
| `needs_projection_build()` | required projections are still missing or stale |
| `backend_connectivity_blocked()` | backend connectivity is currently blocking bring-up |
| `runtime_blocked()` | at least one required route is still runtime-blocked |
| `lexical_degraded()` | at least one route has degraded or partially unsupported lexical semantics |
| `exact_lexical_constraints_recommend_gold()` | the active profile should steer exact lexical workloads to the gold profile |
| `compatibility_projection_reliance()` | at least one route still depends on compatibility projections |
| `canonical_projection_coverage()` | at least one route already exposes canonical authority-backed projection targets |
| `building_projections()` | required projections currently building |
| `failed_projections()` | required projections currently failed |
| `stale_projections()` | required projections currently stale |
| `absent_projections()` | required projections still absent |
| `bootstrap_command()` | highest-priority profile-aware projection bootstrap command, if available |
| `highest_priority_actions()` | ordered remediation items for the active profile |
| `route_recovery_entry(route_id)` | route-scoped recovery summary including runtime blockers, bootstrapability, and lexical caveats |
| `declared_route_support_state(route_id)` | backend-declared support state for the route in the current profile contract |
| `route_declared_executable(route_id)` | whether the bring-up manifest declares the route executable |
| `route_declared_optional(route_id)` | whether the bring-up manifest declares the route optional |
| `route_required_projection_descriptor_ids(route_id)` | required projection descriptors for the route from the bring-up planning payload |
| `declared_routes_runtime_ready()` | whether all backend-declared executable routes are runtime-ready right now |
| `route_prefers_gold_for_exact_constraints(route_id)` | whether the bring-up contract recommends the gold profile for exact lexical workloads on the route |
| `route_exact_constraint_degraded_capabilities(route_id)` | exact-constraint lexical degradations from the route-recovery surface |
| `route_exact_constraint_unsupported_capabilities(route_id)` | exact-constraint lexical unsupported set from the route-recovery surface |
| `local_support_matrix()` | local-profile-specific route support rows from the dedicated `local_profile` payload block |
| `local_promotion_status()` | machine-readable local promotion/bar status payload |
| `local_scope_expansion_status()` | machine-readable widening-status payload for the embedded local profile |
| `local_declared_executable_route_ids()` | local declared executable route ids from the promotion-status payload |
| `local_declared_runtime_ready_route_ids()` | local executable route ids already runtime-ready |
| `local_declared_runtime_blocked_route_ids()` | local executable route ids still blocked |
| `local_required_projection_ids()` | required local projection ids for the current scoped slice |
| `local_representation_scope_ids()` | representation scopes currently participating in the local scoped slice |
| `local_current_supported_slice_frozen()` | whether the current local supported slice is intentionally frozen |
| `local_scope_expansion_pending_for_wider_scope()` | widening blockers still outstanding for the local profile |
| `local_scope_expansion_required_now()` | widening criteria currently tracked for the local profile |
| `local_scope_expansion_satisfied_now()` | widening criteria already satisfied |
| `local_scope_expansion_future_scope_candidates()` | wider local-profile candidates intentionally deferred beyond the current supported slice |
| `local_scope_expansion_docs_ref()` | canonical docs reference for the widening criteria |
| `local_scope_expansion_contract()` | frozen machine-readable widening contract for the supported embedded slice |
| `local_scope_expansion_contract_version()` | dense-sidecar contract version referenced by the widening contract |
| `local_scope_expansion_lifecycle_contract_version()` | dense-sidecar lifecycle contract version referenced by the widening contract |
| `local_scope_expansion_lifecycle_state()` | current dense-sidecar lifecycle state surfaced with widening status |
| `local_scope_expansion_cache_lifecycle_state()` | finer-grained cache/storage lifecycle state for the embedded dense-sidecar |
| `local_scope_expansion_dense_sidecar_promotion_contract_ready()` | whether the current dense-sidecar promotion contract is satisfied |
| `local_scope_expansion_rebuildable_from_projection_records()` | whether the dense-sidecar is rebuildable from ready projection records |
| `local_scope_expansion_requires_process_warmup()` | whether the embedded slice is runnable but still needs process-local dense-sidecar warmup |
| `local_scope_expansion_persisted_projection_state_available()` | whether persisted build-state metadata carries forward dense-sidecar readiness/cache state |
| `local_scope_expansion_required_before_widening()` | frozen criteria list that must be addressed before widening the local embedded slice |
| `local_route_representation_scope(route_id)` | full representation-scope payload for the local route |
| `local_route_capability_dependencies(route_id)` | capability dependencies for the local route |
| `local_route_lexical_support_class(route_id)` | normalized lexical support class for the local route |
| `local_route_dense_sidecar_ready(route_id)` | whether the local route currently has its dense-sidecar dependency satisfied |
| `local_route_dense_sidecar_cache_warmed(route_id)` | whether dense-sidecar cache warm-state is currently known for the route |
| `local_route_dense_sidecar_indexed_record_count(route_id)` | indexed record count reported for the route's dense-sidecar dependency |
| `local_route_dense_sidecar_cache_lifecycle_state(route_id)` | finer-grained cache/storage lifecycle state for the route's dense-sidecar dependency |
| `local_route_dense_sidecar_rebuildable_from_projection_records(route_id)` | whether the route's dense-sidecar dependency is rebuildable from ready projection records |
| `local_route_dense_sidecar_requires_process_warmup(route_id)` | whether the route is runnable but still needs process-local dense-sidecar warmup |
| `local_route_dense_sidecar_persisted_projection_state_available(route_id)` | whether persisted build-state metadata carries forward dense-sidecar readiness/cache state for the route |

### `RetrievalPlanExplainSummary`

Use this when you need request-specific explain output for supported retrieval routes rather than static deployment diagnostics.

Available client helpers:

- `search_hybrid_plan_explain(...) -> RetrievalPlanExplainSummary`
- `search_hybrid_plan_explain_with_options(...) -> RetrievalPlanExplainSummary`
- `search_bm25_plan_explain(...) -> RetrievalPlanExplainSummary`
- `search_file_chunks_plan_explain(...) -> RetrievalPlanExplainSummary`

Available methods on `RetrievalPlanExplainSummary`:

| Method | Meaning |
|---|---|
| `route_executor()` | effective route executor id or richer route-executor payload |
| `lexical_capability_plan()` | request-specific lexical capability planner payload |
| `lane_state()` | effective lane-state payload for the request |
| `adapter_ids()` | lane-family to adapter-id map extracted from resolved stages |
| `query_ir_v2()` | effective `QueryIRV2` payload for the concrete request |
| `projection_ir_v2()` | effective `ProjectionIRV2` payload for the concrete request |
| `route_id()` | resolved route id from request-specific V2 planning |
| `representation_scope_id()` | resolved representation scope id from request-specific V2 planning |
| `planning_surface()` | planning surface recorded for the request-specific V2 payload |
| `projection_buildability_class()` | active projection-buildability class for the request |
| `degraded_capabilities()` | degraded lexical capability ids for the request |
| `unsupported_capabilities()` | unsupported lexical capability ids for the request |

Practical use:

1. call `capabilities_summary()` for high-level lane gating
2. call `profile_diagnostics_summary()` for route/runtime readiness
3. call `search_hybrid_plan_explain(...)`, `search_bm25_plan_explain(...)`, or `search_file_chunks_plan_explain(...)` when you need the actual adapter/lane resolution for a concrete request payload

Example:

```python
plan = client.search_hybrid_plan_explain(
    query='"vapor recovery"~3',
    collection_ids=["col-1"],
)

print(plan.route_id())
print(plan.representation_scope_id())
print(plan.planning_surface())
print(plan.projection_buildability_class())
print(plan.degraded_capabilities())
print(plan.unsupported_capabilities())
```

Use capability discovery plus plan/explain together:
- `capabilities_summary()` to decide whether sparse is executable at all
- `search_hybrid_plan_explain(...)`, `search_bm25_plan_explain(...)`, or `search_file_chunks_plan_explain(...)` to inspect degraded or unsupported lexical operator semantics for the actual request

## CLI commands

- `querylake doctor`
  - now includes compact typed `readyz` / profile diagnostics / bring-up rollups in addition to raw health output
  - exposes:
    - `validation_error_kind`
    - `validation_error_details`
    - `degraded_runtime_ready_routes`
    - `backend_targets`
    - prioritized `next_actions`
- `querylake setup`
- `querylake login`
- `querylake models`
- `querylake profile list`
- `querylake profile show`
- `querylake profile set-default`
- `querylake profile set-url`
- `querylake profile delete`
- `querylake rag create-collection`
- `querylake rag list-collections`
- `querylake rag get-collection`
- `querylake rag update-collection`
- `querylake rag list-documents`
- `querylake rag count-chunks`
- `querylake rag random-chunks`
- `querylake rag delete-document`
- `querylake rag upload`
- `querylake rag upload-dir`
  - source selection: `--dir` (required unless `--from-selection` is provided)
  - bulk selection controls: `--pattern`, `--recursive`, `--max-files`
  - replay exact file sets: `--from-selection` (JSON artifact with `selected_files`)
  - filter controls: `--extensions`, `--exclude-glob` (repeatable)
  - planning mode: `--dry-run` + `--list-files` for selection preview without upload
  - artifact output: `--selection-output` (selected file list), `--report-file` (final payload JSON)
  - resumable mode: `--checkpoint-file`, `--resume`, `--checkpoint-save-every`, `--no-checkpoint-strict`
  - profile mode: `--ingest-profile`, `--ingest-profile-file`
  - sparse toggle controls: `--sparse-embeddings`, `--no-sparse-embeddings`
  - dedupe controls: `--dedupe-content-hash`, `--dedupe-scope {run-local,checkpoint-resume,all}`
  - dedupe override: `--no-dedupe-content-hash`
  - idempotency controls: `--idempotency-strategy {none,content-hash,path-hash}`, `--idempotency-prefix`
  - ingest controls: `--await-embedding`, `--no-scan`, `--no-embeddings`, `--sparse-embeddings`, `--sparse-dimensions`, `--fail-fast`
- `querylake rag search`
  - add `--with-metrics` in hybrid mode to include duration/profile fields
  - add `--preset` for common retrieval profiles (`balanced`, `tri-lane`, `lexical-heavy`, `semantic-heavy`, `sparse-heavy`)
  - optional gates: `--min-total-results`, `--fail-on-empty` (exit code `2` on gate failure)
- `querylake rag search-batch`
  - run newline-delimited query files with same mode/preset/metrics options as `rag search`
  - supports `--output-file` to persist full batch JSON report (includes `_meta` provenance block)
  - optional gates: `--min-total-results`, `--fail-on-empty` (exit code `2` on gate failure)

## Error model

| Exception | Meaning |
|---|---|
| `QueryLakeTransportError` | Network/transport-level failure |
| `QueryLakeHTTPStatusError` | Non-2xx HTTP status from backend |
| `QueryLakeAPIError` | `/api/*` response returned `success=false` |

## Design notes

- SDK is intentionally thin around query shaping and retrieval strategy so research teams can pass lane/fusion options directly.
- Helper methods standardize common workflows; low-level `api()` keeps full backend reach.
- `upload_document` passes parameters via query string JSON to mirror backend multipart contract exactly.

## SDK quality gate (contributors)

From repo root:

```bash
make sdk-precommit-install
make sdk-precommit-run
make sdk-lint
make sdk-type
make sdk-ci
```

Single-source quality script (used by Make, hooks, and CI):

```bash
bash scripts/dev/sdk_quality_gate.sh all
```

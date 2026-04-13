# Projection IR V2

| Field | Value |
|---|---|
| Audience | engineers working on the V2 projection/bootstrap migration |
| Use this when | you need the minimal active `Projection IR V2` subset currently driving supported bootstrap/build and route-dependency surfaces |
| Prerequisites | [`LOCAL_PROFILE_V1.md`](./LOCAL_PROFILE_V1.md), [`QUERY_IR_V2.md`](./QUERY_IR_V2.md), [`AUTHORITY_PROJECTION_MODEL.md`](./AUTHORITY_PROJECTION_MODEL.md) |
| Status | active runtime subset for the supported V2 route/build slices |

This document records the **minimal active** projection-planning subset already driving bootstrap/build reporting and route dependency surfaces for the supported V2 slices.

## Active route projection plan fields

For route recovery and diagnostics, the runtime now emits route-level projection planning with:

- `route_id`
- `representation_scope_id`
- `required_targets`
- `capability_dependencies`
- `runtime_blockers`
- `buildability_class`
- `recovery_hints`

Each required target currently carries:

- `target_id`
- `required`
- `target_backend_family`
- `support_state`
- `metadata.target_backend_name`
- `metadata.representation_scope_id`

## Active projection build-plan registry fields

For bootstrap and promotion status, the runtime now emits per-projection build-plan entries with:

- `profile_id`
- `projection_id`
- `representation_scope_id`
- `lane_family`
- `target_backend`
- `buildability_class`
- `action_mode`
- `support_state`
- `materialization_target`

## Current active projection set

The current local embedded profile V2 projection-plan registry covers:

- `document_chunk_lexical_projection_v1`
- `document_chunk_dense_projection_v1`
- `file_chunk_lexical_projection_v1`

These entries now participate in:

- diagnostics
- bring-up
- local doctor output
- local promotion status
- local completion/consistency gates

## Current scope boundary

This active Projection IR V2 subset is still intentionally narrower than a universal projection-planning contract for every future profile family.

It is currently the source of truth for:

- local bootstrap/build planning
- local projection dependency reporting
- local promotion/completion checks
- shared route-resolution projection dependency/buildability payloads for the current supported search-route slices
- retrieval explain and orchestrated execution metadata for those slices

Outside the completed V2 program boundary:

- wider embedded-slice routes and semantics not yet promoted
- deeper projection-planning usage in future execution/refinement paths
- future profile families outside the current supported route slices

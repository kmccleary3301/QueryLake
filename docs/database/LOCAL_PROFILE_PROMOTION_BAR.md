# Local Profile Promotion Bar

This document records the promotion bar for `sqlite_fts5_dense_sidecar_local_v1`.

The current local profile is now listed as a supported embedded profile for its declared slice in `SUPPORTED_PROFILES.md`. The conditions below describe the bar that had to be satisfied for that promotion and remain the contract for keeping the profile in the supported set.

The canonical machine-readable source of truth for this bar is:
- `profile_bringup.local_profile.promotion_status`

The promotion and completion scripts now consume that central payload rather than maintaining a separate ad hoc local-status model.

## Promotion target

Promote:
- `sqlite_fts5_dense_sidecar_local_v1`
- Current maturity: `embedded_supported`

From:
- narrow executable scaffold

To:
- supported embedded profile for the declared slice

## Required conditions

### 1. Declared scope is frozen

The profile must have one authoritative declared scope in code and docs for:
- `search_bm25.document_chunk`
- `search_file_chunks`
- `search_hybrid.document_chunk`

The scope must explicitly state:
- local lexical support is degraded relative to the gold profile
- sparse retrieval is unsupported
- hard lexical constraints are unsupported

### 2. Route execution is real

The declared-executable routes must have:
- local-specific executor ids
- local-specific execution paths
- no hidden fallback to non-local executor families

### 3. Projection lifecycle is real

The declared-executable routes must have:
- required projection descriptors
- buildable local projection writers
- bootstrap/build status transitions
- runtime-readiness reporting that depends on those projections

### 4. V2 planning is surfaced everywhere

For each declared-executable route, the following must be available through:
- capabilities
- diagnostics
- bring-up
- SDK helpers

Required V2 payloads:
- `query_ir_v2_template`
- `projection_ir_v2`
- `representation_scope`
- capability dependency list

### 5. Completion-style local gates are green

The local profile must have:
- profile smoke coverage
- bring-up smoke coverage
- local completion gate coverage

The local completion gate must verify:
- declared executable route ids
- route runtime readiness after local bootstrap
- required projection readiness
- dense-sidecar readiness for the hybrid slice
- route runtime contracts for the declared executable routes
- lexical degraded route ids
- lexical gold-recommended route ids
- V2 planning payload presence

### 6. Developer/operator guidance is sufficient

The docs must clearly show:
- what the local profile supports
- what degrades
- what is rejected
- how to bootstrap it
- how to inspect readiness

## Current status

Satisfied now:
- declared local route slice exists
- local route executors exist
- local projection writers/build paths exist
- local smoke / bring-up / completion gates exist
- local query smoke exists for the declared executable route slice
- V2 planning payloads are present in diagnostics and bring-up
- dense-sidecar readiness is surfaced in diagnostics, bring-up, promotion status, and the completion gate
- dense-sidecar runtime/promotion blocker fields are surfaced in diagnostics, bring-up, promotion status, and the completion gate
- dense-sidecar indexed-record stats survive process-local cache resets through persisted projection build metadata
- route runtime contracts are surfaced for the declared executable local routes

Still required before broader embedded-scope expansion:
- stronger local dense-sidecar execution story
- broader local route/runtime validation beyond the current narrow slice
- final parity/no-regression expectations for a wider embedded profile scope

## Operator checks

Use these scripts when evaluating the current bar:

```bash
python scripts/db_compat_local_profile_doctor.py
python scripts/db_compat_local_profile_consistency_check.py
python scripts/db_compat_local_profile_promotion_status.py
python scripts/db_compat_local_query_smoke.py --enable-ready-profile-projections
python scripts/db_compat_local_profile_completion_gate.py \
  --profile sqlite_fts5_dense_sidecar_local_v1
```

## Retention rule

Do not widen the local profile scope in `SUPPORTED_PROFILES.md` until the remaining items above are implemented and gated in CI.

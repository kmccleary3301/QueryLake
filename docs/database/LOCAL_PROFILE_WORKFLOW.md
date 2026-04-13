# Local Profile Workflow

| Field | Value |
|---|---|
| Audience | developers bringing up the first supported embedded/local profile |
| Use this when | you want the shortest end-to-end workflow for `sqlite_fts5_dense_sidecar_local_v1` |
| Prerequisites | [`LOCAL_PROFILE_V1.md`](./LOCAL_PROFILE_V1.md), [`LOCAL_PROFILE_PROMOTION_BAR.md`](./LOCAL_PROFILE_PROMOTION_BAR.md) |
| Status | active workflow for the current supported local slice |

## 1. Inspect capabilities

```bash
python scripts/db_compat_profile_smoke.py \
  --profile sqlite_fts5_dense_sidecar_local_v1
```

This confirms the local profile is selected and exposes the declared executable route slice.

## 2. Inspect bring-up status

```bash
python scripts/db_compat_local_profile_doctor.py
```

This prints:

- current local maturity
- whether declared executable routes are runtime-ready
- dense-sidecar readiness
- dense-sidecar indexed-record stats from the last successful dense projection build
- required projection ids
- projection-plan registry entries

## 3. Bootstrap the required local projections

```bash
python scripts/db_compat_profile_bringup_smoke.py \
  --profile sqlite_fts5_dense_sidecar_local_v1 \
  --enable-ready-profile-projections
```

For the current supported local slice, the required projections are:

- `document_chunk_lexical_projection_v1`
- `document_chunk_dense_projection_v1`
- `file_chunk_lexical_projection_v1`

## 4. Re-check runtime readiness

```bash
python scripts/db_compat_local_profile_doctor.py \
  --enable-ready-profile-projections
```

On the happy path, this should report:

- `declared_executable_routes_runtime_ready: True`
- `dense_sidecar_ready: True`
- `dense_sidecar.cache_warmed: True`

## 5. Run the local completion and consistency gates

```bash
python scripts/db_compat_local_profile_completion_gate.py \
  --profile sqlite_fts5_dense_sidecar_local_v1 \
  --enable-ready-profile-projections

python scripts/db_compat_local_profile_consistency_check.py \
  --profile sqlite_fts5_dense_sidecar_local_v1 \
  --enable-ready-profile-projections
```

## 6. Understand semantic limits

The current supported local slice is still semantically narrower than the gold profile.

- plain lexical search: degraded-supported
- phrase/operator-heavy lexical search: degraded-supported
- hard lexical constraints: unsupported
- sparse retrieval: unsupported
- graph traversal: unsupported

Use the gold profile when you need exact lexical constraints or richer retrieval semantics.

## Route execution smoke

```bash
python scripts/db_compat_local_query_smoke.py \
  --enable-ready-profile-projections \
  --json
```

This executes the declared local route slice against the fixture corpus and verifies:

- BM25 top hit
- phrase-degraded BM25 top hit
- operator-degraded BM25 top hit
- hybrid top hit
- file-chunk lexical top hit
- unsupported hard lexical constraints fail structurally
- the dense sidecar cache is warmed by real local hybrid execution
- the dense-sidecar indexed-record count is visible through the build/bring-up contract

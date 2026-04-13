# Local Operator Workflow

This is the recommended operator workflow for the supported embedded slice:

- profile: `sqlite_fts5_dense_sidecar_local_v1`
- declared executable routes:
  - `search_bm25.document_chunk`
  - `search_hybrid.document_chunk`
  - `search_file_chunks`

## 1. Inspect profile smoke

Confirm the profile and supported slice:

```bash
python scripts/db_compat_profile_smoke.py \
  --profile sqlite_fts5_dense_sidecar_local_v1
```

## 2. Inspect bring-up state

Check whether required projections or dense-sidecar readiness are still blocking runtime:

```bash
python scripts/db_compat_profile_bringup_smoke.py \
  --profile sqlite_fts5_dense_sidecar_local_v1
```

## 3. Bootstrap required projections

Build the local lexical and dense projections for the declared slice:

```bash
python scripts/db_compat_profile_bootstrap.py \
  --profile sqlite_fts5_dense_sidecar_local_v1 \
  --validate-runtime-ready
```

## 4. Re-check completion

Confirm that the declared executable slice is runtime-ready:

```bash
python scripts/db_compat_local_profile_completion_gate.py \
  --profile sqlite_fts5_dense_sidecar_local_v1 \
  --enable-ready-profile-projections
```

## 5. Inspect consistency and widening status

Confirm that the supported slice and widening criteria still match the runtime contract:

```bash
python scripts/db_compat_local_profile_consistency_check.py \
  --profile sqlite_fts5_dense_sidecar_local_v1 \
  --enable-ready-profile-projections

python scripts/db_compat_local_profile_scope_expansion_status.py \
  --enable-ready-profile-projections
```

## 6. Run the local query smoke

Confirm that the supported slice still behaves honestly:

```bash
python scripts/db_compat_local_query_smoke.py \
  --enable-ready-profile-projections
```

That smoke covers:

- plain lexical BM25-style search
- degraded phrase/operator lexical behavior
- lexical + dense hybrid
- file lexical retrieval
- unsupported hard lexical constraints

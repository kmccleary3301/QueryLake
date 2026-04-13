# First Split-Stack Completion Gate

Use this gate to decide whether `aws_aurora_pg_opensearch_v1` is behaving like a credible first split-stack profile instead of just a declared compatibility target.

| Field | Value |
| --- | --- |
| Audience | engineers operating or validating the first split-stack profile |
| Use this when | you want one deterministic acceptance check for Aurora/OpenSearch readiness |
| Prerequisites | `docs/database/PROFILE_DIAGNOSTICS.md`, `docs/database/FIRST_SPLIT_STACK_DEPLOYMENT.md` |
| Related docs | `docs/database/DB_COMPAT_PROFILES.md`, `docs/database/RETRIEVAL_PARITY_GATES.md`, [`DB_COMPAT_COMPLETION_GATE.md`](./DB_COMPAT_COMPLETION_GATE.md) |
| Status | active |

## What this gate checks

The completion gate intentionally focuses on the currently declared-executable split-stack slice:

- `search_bm25.document_chunk`
- `search_file_chunks`
- `search_hybrid.document_chunk`

It verifies:

1. the profile is configuration-ready
2. required backend planes are reachable
3. required projections exist and are ready
4. all declared executable routes are runtime-ready
5. lexical degradation is still reported honestly
6. the route ids exposed by diagnostics and bring-up agree with the declared support matrix

## Why this exists

The profile already has:

- capability discovery
- route diagnostics
- bootstrap lifecycle reporting
- parity gates

But operators still need a single acceptance surface that answers:

> "Is the first split-stack profile actually complete enough for its declared MVP?"

That is what this gate does.

## Recommended command

Missing required projections:

```bash
python scripts/db_compat_first_split_stack_completion_gate.py \
  --profile aws_aurora_pg_opensearch_v1 \
  --env QUERYLAKE_SEARCH_BACKEND_URL=https://example-opensearch.local \
  --env QUERYLAKE_SEARCH_INDEX_NAMESPACE=querylake \
  --env QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS=1024 \
  --expect-boot-ready false \
  --expect-configuration-ready true \
  --expect-route-runtime-ready false \
  --expect-declared-executable-routes-runtime-ready false \
  --expect-backend-connectivity-ready true \
  --expect-required-projection-count 3 \
  --expect-ready-projection-count 0 \
  --expect-declared-executable-route-ids search_bm25.document_chunk,search_file_chunks,search_hybrid.document_chunk \
  --expect-lexical-degraded-route-ids search_bm25.document_chunk,search_file_chunks,search_hybrid.document_chunk \
  --expect-lexical-gold-recommended-route-ids search_bm25.document_chunk,search_file_chunks,search_hybrid.document_chunk
```

Ready split-stack slice:

```bash
python scripts/db_compat_first_split_stack_completion_gate.py \
  --profile aws_aurora_pg_opensearch_v1 \
  --env QUERYLAKE_SEARCH_BACKEND_URL=https://example-opensearch.local \
  --env QUERYLAKE_SEARCH_INDEX_NAMESPACE=querylake \
  --env QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS=1024 \
  --enable-ready-split-stack-projections \
  --expect-boot-ready true \
  --expect-configuration-ready true \
  --expect-route-runtime-ready true \
  --expect-declared-executable-routes-runtime-ready true \
  --expect-backend-connectivity-ready true \
  --expect-required-projection-count 3 \
  --expect-ready-projection-count 3 \
  --expect-declared-executable-route-ids search_bm25.document_chunk,search_file_chunks,search_hybrid.document_chunk \
  --expect-lexical-degraded-route-ids search_bm25.document_chunk,search_file_chunks,search_hybrid.document_chunk \
  --expect-lexical-gold-recommended-route-ids search_bm25.document_chunk,search_file_chunks,search_hybrid.document_chunk
```

## Interpretation

- `boot_ready=false` with `configuration_ready=true` and `backend_connectivity_ready=true`
  usually means the declared executable routes are still blocked by projection readiness.
- `declared_executable_routes_runtime_ready=true`
  means the profile is operationally complete for its currently declared executable route slice.
- `lexical_degraded_route_ids` and `lexical_gold_recommended_route_ids`
  remaining non-empty is expected today. The first split-stack profile is runnable, but exact lexical semantics are still a gold-profile concern.
- the gate also checks internal contract consistency between:
  - `declared_route_support`
  - declared executable vs optional route ids
  - declared runtime-ready vs runtime-blocked route ids
  - route-recovery support-state payloads
  - lexical degraded / gold-recommended route flags

## Completion gate for the current MVP

Treat the first split-stack profile as complete for its current MVP only when all of the following are true:

- configuration is ready
- backend connectivity is ready
- required projection count is `3`
- ready projection count is `3`
- declared executable route ids are exactly:
  - `search_bm25.document_chunk`
  - `search_file_chunks`
  - `search_hybrid.document_chunk`
- all declared executable routes are runtime-ready
- lexical degradation is still reported honestly
- parity gates remain green

This gate is intentionally narrower than "full QueryLake backend portability." It only certifies the first split-stack MVP slice.

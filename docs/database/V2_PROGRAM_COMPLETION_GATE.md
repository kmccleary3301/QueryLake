# QueryLake Primitive/Representation V2 Program Completion Gate

This is the final completion gate for the V2 primitives + embedded local profile program.

| Field | Value |
|---|---|
| Audience | maintainers, reviewers, release owners |
| Use this when | deciding whether the V2 program is actually complete by scope |
| Prerequisites | [`V2_RUNTIME_BOUNDARY.md`](./V2_RUNTIME_BOUNDARY.md), [`LOCAL_PROFILE_V1.md`](./LOCAL_PROFILE_V1.md), [`LOCAL_PROFILE_SCOPE_EXPANSION_CRITERIA.md`](./LOCAL_PROFILE_SCOPE_EXPANSION_CRITERIA.md) |
| Related docs | [`V2_IMPLEMENTATION_REPORT.md`](./V2_IMPLEMENTATION_REPORT.md), [`V2_FUTURE_SCOPE.md`](./V2_FUTURE_SCOPE.md), [`LOCAL_DENSE_SIDECAR_CONTRACT.md`](./LOCAL_DENSE_SIDECAR_CONTRACT.md) |
| Status | authoritative closeout gate for the V2 program |

## What this gate checks

The V2 program-completion gate verifies that:

1. the prior scoped DB-compat program is still complete
2. the V2 runtime boundary is synced to the live runtime contract
3. the embedded local supported slice passes its own supported-slice gate
4. the embedded local widening contract is frozen and docs-synced
5. the dense-sidecar contract is explicit and docs-synced
6. shared V2 runtime consistency is still green across:
   - route resolution
   - search request handling
   - retrieval explain
   - orchestrated execution metadata
7. future wider embedded scope is explicitly separated instead of silently implied

## Recommended command

```bash
python scripts/db_compat_v2_program_completion_gate.py \
  --output /tmp/querylake_db_compat_v2_program_completion_gate.json
```

## Exact completion standard

Treat the V2 program as complete only when all of the following are true:

- `QueryIRV2` is part of the live runtime boundary for the current supported search-route slices
- `ProjectionIRV2` is part of the live build/dependency boundary for the current supported search-route slices
- `sqlite_fts5_dense_sidecar_local_v1` is supported for its declared embedded slice
- the dense-sidecar contract is explicit, versioned, and enforced
- local lexical degradation is honest across capabilities, diagnostics, bring-up, smoke, SDK, and docs
- the widening boundary beyond the current local slice is frozen and explicitly future scope

## Interpretation

- If this gate passes, the current V2 program is complete by its stated scope.
- It does not mean wider embedded-route support is complete.
- It does not mean additional profile families are implemented.
- It does not mean all compatibility-era storage internals are gone everywhere.

Those items are tracked explicitly in:

- [`V2_FUTURE_SCOPE.md`](./V2_FUTURE_SCOPE.md)


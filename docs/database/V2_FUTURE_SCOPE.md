# QueryLake Primitive/Representation V2 Future Scope

This document defines what is intentionally outside the scope of the completed V2 program.

| Field | Value |
|---|---|
| Audience | maintainers, reviewers, future contributors |
| Use this when | deciding whether a missing V2/local feature is incomplete current work or future-scope work |
| Prerequisites | [`V2_IMPLEMENTATION_REPORT.md`](./V2_IMPLEMENTATION_REPORT.md), [`V2_PROGRAM_COMPLETION_GATE.md`](./V2_PROGRAM_COMPLETION_GATE.md) |
| Related docs | [`LOCAL_PROFILE_SCOPE_EXPANSION_CRITERIA.md`](./LOCAL_PROFILE_SCOPE_EXPANSION_CRITERIA.md), [`DB_COMPAT_PROFILES.md`](./DB_COMPAT_PROFILES.md) |
| Status | authoritative out-of-scope boundary for the completed V2 program |

## Out of scope for V2 completion

The completed V2 program does **not** require:

- widening `sqlite_fts5_dense_sidecar_local_v1` beyond its current declared supported slice
- adding local sparse retrieval
- adding local graph traversal
- promoting a second embedded backend family
- making V2 the dominant runtime boundary for every future execution/refinement path
- fully retiring every compatibility-era storage shape everywhere

## Why these are out of scope

The V2 program is about making QueryLake:

- explicit about representation/materialization boundaries
- explicit about active V2 planning contracts
- capable of supporting one real embedded/local profile honestly
- explicit about widening blockers and future embedded-route ambitions

That is enough to complete the current program cleanly.

## Next-program candidates

- widen the embedded supported slice beyond the current route set
- add local sparse retrieval
- add local graph traversal
- add another embedded backend family
- push V2 deeper into broader execution/refinement paths outside the currently supported search-route slices


# Document Decomposition Tranche 1

| Status | Active |
|---|---|
| Scope | additive authority-layer substrate, compatibility normalization, migration tooling |
| Prerequisites | [`AUTHORITY_PROJECTION_MODEL.md`](./AUTHORITY_PROJECTION_MODEL.md), [`QUERY_IR_V2.md`](./QUERY_IR_V2.md), [`RETRIEVAL_EXECUTION_BOUNDARY.md`](./RETRIEVAL_EXECUTION_BOUNDARY.md) |

## Purpose

This document is the durable operator and contributor reference for tranche 1 of the document decomposition authority-layer migration.

Tranche 1 does **not** introduce frontier retrieval families or public multi-view query routing. It does three narrower things:

1. persists parser-derived units and view-scoped segments for new ingest,
2. keeps `DocumentChunk` alive as a compatibility projection,
3. provides controlled migration/backfill/audit tooling for historical data.

## Current milestone

As of `2026-04-15`, the last fully frozen audited boundary is the first `190,000` historical documents (`0-189999`). New ingests are canonical by default, and the historical normalization campaign continues in staged windows beyond that point. Global normalization is still incomplete.


## Foreground stop-point

The foreground normalization target for tranche 1 is `200,000` historical documents. That is the point where the normalized front is large enough to support tranche-2 substrate-aware runtime work without pretending the long historical tail is finished.

If the campaign remains healthy through that target, further rollout should continue as **background maintenance**, not as blocking foreground work for the next tranche.

## Concurrency guidance

Supported and routine:

- scoped doctor + migration-status + uniqueness-audit together for a checkpoint boundary
- one background rollout window running while code/docs work continues

Avoid unless you are deliberately testing the behavior:

- multiple rollout campaigns against the same manifest at once
- mixing unrelated schema bootstrap work into decomposition rollout jobs
- claiming a durable boundary from manifest state before the full scoped audit set completes

## What tranche 1 adds

New schema/runtime primitives:

- `document_unit_view`
- `document_unit`
- `document_segment_view`
- `document_segment_member`
- `document_segment.segment_view_id`
- `DocumentChunk.authority_segment_id`

New operational tools:

- `scripts/document_decomposition_doctor.py`
- `scripts/document_decomposition_parity.py`
- `scripts/backfill_document_decomposition.py`
- `scripts/document_decomposition_migration_status.py`
- `scripts/document_decomposition_uniqueness_audit.py`
- `scripts/document_decomposition_apply_uniqueness_swap.py`
- `scripts/repair_document_decomposition.py`
- `scripts/document_decomposition_campaign_status.py`

## Authority rule

For new ingests, canonical local-text authority is now:

1. `document_unit_view`
2. `document_unit`
3. `document_segment_view`
4. `document_segment`
5. `document_segment_member`

`DocumentChunk` is still materialized and still read by current public retrieval surfaces, but it should be treated as a compatibility projection derived from canonical segments.

## Migration states

The tranche-1 tooling uses these states:

- `canonical`
- `backfilled_compat`
- `legacy_only`
- `partial`
- `chunks_missing_authority_links`
- `segments_missing_default_view`
- `empty`

Interpretation:

- `canonical`: new-ingest authority state exists and `DocumentChunk` compatibility rows are linked
- `backfilled_compat`: historical docs were normalized from legacy chunks into degraded-but-authoritative decomposition state
- `legacy_only`: no decomposition rows exist yet
- `partial`: mixed or incomplete decomposition rows exist
- `chunks_missing_authority_links`: decomposition exists but `DocumentChunk.authority_segment_id` is incomplete
- `segments_missing_default_view`: segments exist without the current default local-text view

## Supported workflows

### Inspect current state

```bash
PYTHONPATH=. python scripts/document_decomposition_doctor.py --limit 25 --json
```

### Check current parity

```bash
PYTHONPATH=. python scripts/document_decomposition_parity.py --document-id <doc_id> --json
```

### Inspect chunk-to-segment provenance

```bash
PYTHONPATH=. python scripts/document_decomposition_provenance.py --document-id <doc_id> --json
```

This is the narrow internal inspection surface for tranche-2 starter work. It exposes canonical segment ids, segment views, and member unit spans for compatibility chunks without changing public retrieval APIs.

### Plan or execute backfill

```bash
PYTHONPATH=. python scripts/backfill_document_decomposition.py --limit 25 --dry-run --json
PYTHONPATH=. python scripts/backfill_document_decomposition.py --document-id <doc_id> --json
```

### Repair degraded mixed state

```bash
PYTHONPATH=. python scripts/repair_document_decomposition.py --document-id <doc_id> --dry-run --json
PYTHONPATH=. python scripts/repair_document_decomposition.py --document-id <doc_id> --json
```

### Audit or apply uniqueness normalization

```bash
PYTHONPATH=. python scripts/document_decomposition_uniqueness_audit.py --json
PYTHONPATH=. python scripts/document_decomposition_apply_uniqueness_swap.py --json
```

### Summarize campaign status

```bash
PYTHONPATH=. python scripts/document_decomposition_campaign_status.py --audited-limit 190000 --audit-date 2026-04-15 --json
```

This report is the machine-readable source of truth for:

- latest fully audited boundary
- latest merely committed boundary
- whether committed rollout is ahead of audited status
- cumulative campaign backfilled/skipped/parity totals

## Repair policy

Repair is intentionally conservative.

It is allowed to rebuild degraded historical state only when the document does **not** already have a non-backfill default local-text view. If a non-backfill default view exists, the repair tool returns `manual_review_required` rather than mutating potentially canonical state.

This is deliberate. Tranche 1 prefers explicit manual review over silent lineage loss.

## Constraint normalization

The old uniqueness shape:

- `(document_version_id, segment_type, segment_index)`

is replaced by the tranche-1 view-scoped shape:

- `(document_version_id, segment_view_id, segment_type, segment_index)`

The swap should only be applied after:

- no `document_segment.segment_view_id` nulls remain
- no duplicate proposed keys exist
- no duplicate current default views exist per document/version

## What tranche 1 does not do

- public multi-view retrieval routing
- representation generalization beyond current compatibility rows
- late chunking / multivector / page-visual / table-native retrieval
- retirement of `DocumentChunk`

See also: [`DOCUMENT_DECOMPOSITION_TRANCHE2_BOOTSTRAP.md`](DOCUMENT_DECOMPOSITION_TRANCHE2_BOOTSTRAP.md) for the immediate next-phase boundary once tranche 1 is stabilized.

## Success criteria

Tranche 1 is in good shape when:

1. new ingests dual-write canonical units/views/members,
2. historical docs can be backfilled without losing current retrieval compatibility,
3. parity checks pass on sampled normalized documents,
4. uniqueness is view-scoped,
5. current public retrieval behavior remains stable.
## Boundary interpretation

Operators should distinguish two different boundaries:

- **latest fully audited boundary**: the largest normalized range that has a complete scoped doctor, migration-status, and uniqueness-audit set
- **latest committed boundary**: the largest range implied by the campaign manifest's latest completed rollout window

These boundaries are sometimes equal and sometimes not. Durable status docs should only claim the fully audited boundary as stable.

## Known remaining debt

- Global historical normalization is still incomplete.
- The long historical tail still contains legacy-only compatibility rows outside the normalized front.
- Tranche 1 intentionally does not yet make public retrieval/query surfaces decomposition-aware.
- Further rollout can continue as background maintenance once the foreground stop-point is reached.


# Retrieval Parity Gates

[![Docs Checks](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml/badge.svg)](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml)
[![SDK Checks](https://github.com/kmccleary3301/QueryLake/actions/workflows/sdk_checks.yml/badge.svg)](https://github.com/kmccleary3301/QueryLake/actions/workflows/sdk_checks.yml)

Acceptance policy for gold-vs-split-stack retrieval comparison artifacts and CI gates.

| Field | Value |
|---|---|
| Audience | backend contributors, retrieval engineers, platform maintainers |
| Use this when | defining or reviewing cross-profile retrieval parity expectations |
| Prerequisites | [`DB_COMPAT_PROFILES.md`](./DB_COMPAT_PROFILES.md), [`FIRST_SPLIT_STACK_DEPLOYMENT.md`](./FIRST_SPLIT_STACK_DEPLOYMENT.md), [`RETRIEVAL_EXECUTION_BOUNDARY.md`](./RETRIEVAL_EXECUTION_BOUNDARY.md) |
| Related docs | [`PROFILE_DIAGNOSTICS.md`](./PROFILE_DIAGNOSTICS.md), [`SDK_PROFILE_AWARE_CLIENTS.md`](./SDK_PROFILE_AWARE_CLIENTS.md) |
| Status | active, first split-stack parity policy |

## Principle

QueryLake does **not** promise exact retrieval parity across backends.

It does promise:

- the same conceptual primitive surface,
- the same request and response envelopes,
- the same capability and error model,
- explicit degraded or unsupported semantics where backend behavior differs,
- measurable overlap and quality bands for the first split-stack slice.

For the current first split-stack profile, acceptance is based on:

1. top-k overlap
2. MRR drop relative to gold
3. latency expansion relative to gold

## Current CI gate

`make ci-db-compat` now runs:

```bash
python scripts/db_compat_retrieval_parity.py \
  --cases-json tests/fixtures/db_compat_retrieval_parity_cases.json \
  --route-thresholds-json tests/fixtures/db_compat_retrieval_parity_route_thresholds.json \
  --gold-runs-json tests/fixtures/db_compat_retrieval_parity_gold_runs.json \
  --split-runs-json tests/fixtures/db_compat_retrieval_parity_split_runs.json \
  --gold-latency-json tests/fixtures/db_compat_retrieval_parity_gold_latency.json \
  --split-latency-json tests/fixtures/db_compat_retrieval_parity_split_latency.json \
  --k 2 \
  --min-overlap 0.80 \
  --max-mrr-drop 0.10 \
  --max-latency-ratio 1.35
```

## Acceptance bands

| Metric | Meaning | Current CI threshold | Why |
|---|---|---:|---|
| `topk_overlap_mean` | average overlap between gold and split-stack top-k results | `>= 0.80` | split-stack should remain recognizably close without pretending exact rank identity |
| `mrr_delta` | split-stack MRR minus gold MRR | `>= -0.10` | split-stack can degrade, but should not collapse first-hit quality |
| `latency_ratio_mean` | split-stack mean latency divided by gold mean latency | `<= 1.35` | split-stack may be slower, but not unboundedly slower on the representative fixture set |

These are **acceptance bands**, not semantic parity claims.

## Route-specific aggregate gates

In addition to the global aggregate thresholds above, CI now enforces route-specific aggregate gates from:

- `tests/fixtures/db_compat_retrieval_parity_route_thresholds.json`

Current route gates:

| Route | `min_overlap` | `max_mrr_drop` | `max_latency_ratio` |
|---|---:|---:|---:|
| `search_bm25.document_chunk` | `0.85` | `0.05` | `1.35` |
| `search_hybrid.document_chunk` | `0.75` | `0.10` | `1.35` |
| `search_file_chunks` | `0.50` | `0.10` | `1.50` |

These route gates are evaluated against `metrics.route_metrics[...]`, not just the global averages.

## Fixture scope

The current retrieval parity fixture intentionally covers a small representative set:

| Case | Route | Purpose |
|---|---|---|
| `bm25_simple` | `search_bm25.document_chunk` | lexical baseline |
| `bm25_phrase` | `search_bm25.document_chunk` | phrase-like lexical behavior under degraded operator semantics |
| `hybrid_dense_lexical` | `search_hybrid.document_chunk` | first split-stack MVP hybrid route |
| `file_chunk_simple` | `search_file_chunks` | file lexical route |
| `hybrid_hard_constraint_unsupported` | `search_hybrid.document_chunk` | unsupported hard-constraint behavior must fail honestly on split-stack |

The fixture is not meant to be a benchmark corpus. It is a deterministic parity gate for:

- result overlap sanity,
- first-hit quality sanity,
- profile-to-profile regression detection.

Each case now carries explicit expectations for the split-stack profile:

- `supported`
- `degraded`
- `unsupported`

Unsupported cases are expected to remain outside the executable parity aggregate and are validated separately. By default, an unsupported case must not return split-stack results in the fixture harness.

## How to read the artifact

The parity harness emits:

- `metrics.topk_overlap_mean`
- `metrics.gold_mrr`
- `metrics.split_mrr`
- `metrics.mrr_delta`
- `metrics.latency_ratio_mean`
- `metrics.per_query[]`

Each per-query row includes:

- `gold_topk`
- `split_topk`
- `overlap_at_k`
- `gold_rr`
- `split_rr`
- `gold_latency_ms`
- `split_latency_ms`
- `latency_ratio`
- `split_expected_state`
- `failure_reasons`

Interpretation:

- low overlap with stable MRR may be acceptable if the split-stack still returns relevant first hits
- low overlap with large negative MRR is not acceptable
- acceptable overlap does not excuse unsupported lexical semantics; those must still be declared via capabilities and explain payloads
- unsupported cases are expected to fail structurally; they should not be silently folded into the executable overlap metrics

## What this does not mean

Passing the parity gate does **not** mean:

- exact ParadeDB BM25 parity
- exact phrase/proximity parity
- exact hard-constraint parity
- exact sparse/graph parity

Those remain explicit profile-level support questions.

## Next expansion path

As the split-stack profile matures, expand this gate in this order:

1. add more lexical edge cases
2. add dense-heavy semantic cases
3. add real benchmark-backed artifact generation
4. add environment-backed parity runs, not just fixture-backed runs

Do not tighten thresholds blindly. Tighten them only after:

- the route semantics are stable,
- the explain output is trustworthy,
- and the degraded/unsupported feature contract remains honest.

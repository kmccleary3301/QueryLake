# Chandra OCR Decision Closeout

This document closes the current OCR decision program.

It does not attempt to preserve every experiment. It freezes the final production recommendation,
the branches that were tested, and the branches that remain future work.

## Final Recommendation

- Default production OCR lane: `Chandra-1`
- Recommended serving mode: external `vllm_server`
- Default production contract: `ocr_markdown`
- `Chandra-2`: opt-in / experimental
- PDF text-layer fast path: opt-in / experimental under a separate contract
- Chandra-1 selective-cap OCR branches: benchmark-only

## What Was Decided

### 1. `Chandra-1` remains the default OCR lane

Reason:
- it remains the best production-quality OCR baseline on the measured corpora
- it stayed stronger than the tested Chandra-2 candidates under the current promotion criteria
- the current pipeline improvements already benefit this lane

### 2. `Chandra-2` is not promoted

Reason:
- runtime compatibility was solved
- benchmark governance was solved
- but the best Chandra-2 candidates did not clear the canonical quality gate

This is an explicit no-promotion decision, not an unresolved experiment.

### 3. Text-layer routing is real, but it is not OCR-equivalent

Reason:
- it has the largest remaining throughput upside
- but its output shape diverges materially from the OCR-markdown baseline
- it must be treated as a separate contract unless a stronger alignment layer exists

### 4. Selective-cap OCR branches remain benchmark-only

Reason:
- some gains were real on favorable document shapes
- they did not generalize broadly enough across the current scholarly corpus
- they do not justify current service-path complexity as defaults

## What Landed In The Stack

- `render-to-cap` PDF raster policy
- bytes-backed image payload reuse
- stronger benchmark and baseline governance
- runtime compatibility reporting for Chandra lanes
- durable OCR option-set docs
- durable output-contract integration docs
- SDK helper for typed PDF output-contract parsing
- CLI path for inspecting persisted document output contracts

## Closed Branches

These are closed for the current OCR decision set:

- Chandra-2 default promotion
- page-vs-batch transport as the main speed lever
- naive Chandra-1 concurrency sweeps
- current text-layer routing as a drop-in OCR replacement
- current selective-cap OCR branches as general production defaults

## Durable Contract Surface

For the maintained contract docs, use:

- [`CHANDRA_OCR_VLLM_SERVER.md`](CHANDRA_OCR_VLLM_SERVER.md)
- [`CHANDRA_OCR_OPTION_SET.md`](CHANDRA_OCR_OPTION_SET.md)
- [`CHANDRA_OUTPUT_CONTRACT_INTEGRATION.md`](CHANDRA_OUTPUT_CONTRACT_INTEGRATION.md)

Do not require downstream users to reconstruct the contract from `docs_tmp/` artifacts.

## Future Work

If more OCR work continues, the next valid branches are:

1. stronger text-layer contract alignment, or
2. explicit downstream features that intentionally support the text-layer contracts

Do not reopen broad Chandra-2 promotion work or generic OCR tuning without materially new evidence.

## Status

This OCR decision set is now frozen enough to justify:

- the production default
- the experimental lanes
- the benchmark-only branches
- the downstream contract boundary

That is the closeout condition for the current OCR option program.

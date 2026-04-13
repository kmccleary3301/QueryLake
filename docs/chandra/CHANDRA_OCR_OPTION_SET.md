# Chandra OCR Option Set

This document freezes the current OCR option set and the output contracts QueryLake exposes for PDF
transcription.

It is intentionally narrower than the experiment log in `docs_tmp/`. This is the durable operator
surface.

For downstream branching guidance, also read:
- [`CHANDRA_OUTPUT_CONTRACT_INTEGRATION.md`](CHANDRA_OUTPUT_CONTRACT_INTEGRATION.md)

For the final closeout summary of the current OCR decision program, also read:
- [`CHANDRA_OCR_DECISION_CLOSEOUT.md`](CHANDRA_OCR_DECISION_CLOSEOUT.md)

## Current Recommendation

- Default production OCR path: `Chandra-1` over external `vllm_server`
- Default output contract: `ocr_markdown`
- Experimental OCR path: `Chandra-2` over external `vllm_server`
- Experimental fast path: PDF text-layer extraction under a separate output contract
- Benchmark-only: Chandra-1 selective-cap OCR branches

## Why This Is The Current Shape

- `Chandra-1` remains the best production-quality OCR baseline on the measured promotion corpus.
- `Chandra-2` is integrated and benchmarkable, but it did not clear the current promotion bar.
- Text-layer routing has large speed upside, but it does not preserve OCR-markdown parity closely
  enough to be treated as a drop-in replacement.
- Selective-cap OCR branches do help on narrow document shapes, but they do not generalize enough to
  justify production-path complexity yet.

## Output Contracts

### `ocr_markdown`

OCR-derived markdown contract used by the current production Chandra path.

Properties:
- page content is produced from OCR rather than direct PDF text extraction
- current baseline contract for Chandra-1 comparisons
- contract expected by existing OCR-quality benchmark artifacts

### `text_layer_fastpath_markdown`

Direct PDF text-layer contract for pages served entirely from the PDF text layer.

Properties:
- significantly faster than OCR on eligible PDFs
- formatting and structural conventions can differ materially from the OCR-markdown baseline
- should be treated as a separate contract, not a transparent replacement for `ocr_markdown`

### `mixed_text_layer_fastpath_markdown`

Per-page mixed contract where some pages come from direct text-layer extraction and others from OCR.

Properties:
- intended for hybrid fast-path evaluation
- page-level source mix is explicit in service metadata
- not currently promoted as the default PDF contract

## Service Metadata

When the PDF pipeline uses a text-layer path, service metadata now makes that explicit.

Relevant fields:
- `output_contract`
- `page_source_by_page`
- `page_source_counts`

Expected values:
- fully OCR PDF: `output_contract = "ocr_markdown"`
- fully text-layer PDF: `output_contract = "text_layer_fastpath_markdown"`
- mixed PDF: `output_contract = "mixed_text_layer_fastpath_markdown"`

This exists so downstream consumers do not have to infer contract shape from the content alone.

## Current Status By Option

### `Chandra-1`

Status:
- default

Serving recommendation:
- external `vllm_server`

Contract:
- `ocr_markdown`

Notes:
- best current production-quality OCR baseline
- benefits from `render-to-cap` and bytes-backed image reuse already landed in the pipeline

### `Chandra-2`

Status:
- opt-in / experimental

Serving recommendation:
- external `vllm_server`

Contract:
- `ocr_markdown`

Notes:
- runtime-compatible and benchmarkable
- not promoted because current candidates did not clear the canonical quality gate

### Text-layer fast path

Status:
- opt-in / experimental

Serving recommendation:
- use only when consumers can tolerate or explicitly support the text-layer contract

Contract:
- `text_layer_fastpath_markdown` or `mixed_text_layer_fastpath_markdown`

Notes:
- strongest remaining throughput opportunity
- current normalization/alignment work is not yet strong enough to claim OCR-contract parity

### Selective-cap OCR branches

Status:
- benchmark-only

Notes:
- useful for measurement and specialized document shapes
- not yet justified for production-path complexity

## What Is Closed

These branches are closed for the current OCR decision set:

- Chandra-2 default promotion
- page-vs-batch transport as the primary speed lever
- naive Chandra-1 concurrency sweeps as the next main optimization path
- current text-layer routing as a drop-in OCR replacement
- current selective-cap OCR branches as general production defaults

## If Further Work Continues

The next valid branches are:

1. stronger text-layer contract alignment, or
2. explicit downstream support for the text-layer contracts

Do not reopen broad Chandra-2 promotion work or generic OCR tuning until one of those branches
produces materially new evidence.

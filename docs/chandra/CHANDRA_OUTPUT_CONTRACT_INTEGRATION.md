# Chandra Output Contract Integration

This document explains how downstream consumers should interpret PDF transcription results from the
current Chandra stack.

The critical rule is simple:

- do not assume all PDF transcription output is the same contract
- branch on `output_contract`

## Why This Exists

QueryLake now exposes multiple PDF transcription paths:

- OCR-derived markdown
- text-layer fast-path markdown
- mixed per-page text-layer/OCR markdown

These are all useful, but they are not interchangeable.

The OCR path is the current production-quality baseline. The text-layer paths are much faster on
eligible PDFs, but their formatting and structure can differ materially from the OCR baseline.

## Contract Field

When a PDF is processed, metadata can include:

- `output_contract`
- `page_source_by_page`
- `page_source_counts`

Current contract values:

- `ocr_markdown`
- `text_layer_fastpath_markdown`
- `mixed_text_layer_fastpath_markdown`

## Recommended Downstream Behavior

### If `output_contract == "ocr_markdown"`

Treat the content as the current OCR baseline contract.

This is the right path when downstream logic expects:
- OCR-style markdown structure
- current benchmark-compatible formatting
- the highest-confidence production path

### If `output_contract == "text_layer_fastpath_markdown"`

Treat the content as a separate fast-path contract.

Recommended assumptions:
- text is likely correct enough for many research and indexing tasks
- formatting may differ from OCR-markdown expectations
- if strict OCR-contract parity matters, do not treat this as equivalent

Good uses:
- fast ingestion
- search indexing
- text analytics that do not depend on OCR-style markdown formatting

Use caution for:
- strict markdown-structure comparisons
- OCR-benchmark-style regression checks
- downstream transforms tuned specifically for OCR output

### If `output_contract == "mixed_text_layer_fastpath_markdown"`

Treat the content as a hybrid per-page contract.

Recommended assumptions:
- some pages came from text-layer extraction
- some pages came from OCR
- formatting consistency can vary page to page

Use the accompanying metadata:
- `page_source_by_page`
- `page_source_counts`

This lets downstream consumers:
- detect which pages were OCR vs text-layer
- reroute or reprocess selected pages if needed
- avoid pretending the whole document came from one homogeneous path

## Minimal Integration Pattern

Use the contract to decide how strict downstream processing should be.

Example policy:

```python
meta = result.get("metadata") or {}
contract = str(meta.get("output_contract") or "ocr_markdown")

if contract == "ocr_markdown":
    handle_as_ocr_markdown(result)
elif contract == "text_layer_fastpath_markdown":
    handle_as_textlayer_fastpath(result)
elif contract == "mixed_text_layer_fastpath_markdown":
    handle_as_mixed_fastpath(result, meta.get("page_source_by_page") or {})
else:
    raise ValueError(f"Unknown PDF output contract: {contract}")
```

## Recommended Product Policy

Current safe policy is:

- default path: `ocr_markdown`
- opt-in fast path: `text_layer_fastpath_markdown`
- opt-in hybrid path: `mixed_text_layer_fastpath_markdown`

Do not silently replace OCR output with text-layer output in consumers that were built against the
OCR baseline.

## When To Normalize

If a downstream workflow wants to consume text-layer output while staying closer to OCR expectations,
normalization should be treated as an explicit step.

That normalization step should be:
- versioned
- measurable
- contract-aware

Do not hide that conversion behind undocumented heuristics.

## Current Production Recommendation

- Keep `Chandra-1` + `ocr_markdown` as the default production path.
- Keep `Chandra-2` under opt-in / experimental use.
- Keep text-layer fast paths opt-in / experimental unless downstream consumers explicitly support the
  separate text-layer contracts.

For the frozen OCR option set, see:
- [`CHANDRA_OCR_OPTION_SET.md`](CHANDRA_OCR_OPTION_SET.md)

For serving/runtime guidance, see:
- [`CHANDRA_OCR_VLLM_SERVER.md`](CHANDRA_OCR_VLLM_SERVER.md)

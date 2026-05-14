from __future__ import annotations

from typing import Iterable, List

from QueryLake.files.object_store import LocalCASObjectStore
from QueryLake.scanning.adapters import ScannerRunContext
from QueryLake.scanning.contracts import materialize_legacy_markdown_envelope
from QueryLake.scanning.docling import DoclingExtractionResult, DoclingLocalParserAdapter
from QueryLake.scanning.evaluation import ScannerEvalCase, ScannerEvalResult, evaluate_scanner_envelope_contract
from QueryLake.scanning.providers import GeminiDocumentFallbackMockAdapter, MistralOCRMockAdapter, ProviderMockResult, ProviderPolicy


def _context(case: ScannerEvalCase, backend_id: str) -> ScannerRunContext:
    return ScannerRunContext(
        run_id=f"eval_{case.case_id}_{backend_id}",
        backend_id=backend_id,
        backend_class="eval_mock",
        support_tier="experimental",
        file_id=f"file_{case.case_id}",
        file_version_id=f"fv_{case.case_id}",
        config_hash="scanner_eval_mock_v1",
        md={"case_id": case.case_id, "document_class": case.document_class},
    )


def _native_envelope(case: ScannerEvalCase):
    return materialize_legacy_markdown_envelope(
        run_id=f"eval_{case.case_id}_native",
        backend_id="pymupdf4llm_native",
        backend_class="native_digital_extraction",
        support_tier="first_class",
        legacy_output_contract="text_layer_fastpath_markdown",
        markdown=f"## Page 1\n\nNative baseline text for {case.case_id}.",
        meta={
            "engine": "pymupdf4llm",
            "pages": 1,
            "page_source_by_page": {"0001": "native_text"},
            "page_source_counts": {"native_text": 1, "ocr": 0},
        },
    )


def _ocr_envelope(case: ScannerEvalCase):
    return materialize_legacy_markdown_envelope(
        run_id=f"eval_{case.case_id}_ocr",
        backend_id="chandra_1",
        backend_class="incumbent_continuity",
        support_tier="first_class",
        legacy_output_contract="ocr_markdown",
        markdown=f"## Page 1\n\nOCR baseline text for {case.case_id}.",
        meta={
            "engine": "chandra",
            "pages": 1,
            "page_source_by_page": {"0001": "ocr"},
            "page_source_counts": {"ocr": 1, "native_text": 0},
        },
    )


def _mixed_envelope(case: ScannerEvalCase):
    return materialize_legacy_markdown_envelope(
        run_id=f"eval_{case.case_id}_mixed",
        backend_id="chandra_1",
        backend_class="incumbent_continuity",
        support_tier="first_class",
        legacy_output_contract="mixed_text_layer_fastpath_markdown",
        markdown=f"## Page 1\n\nNative baseline text.\n\n## Page 2\n\nOCR baseline text for {case.case_id}.",
        meta={
            "engine": "chandra",
            "pages": 2,
            "page_source_by_page": {"0001": "native_text", "0002": "ocr"},
            "page_source_counts": {"native_text": 1, "text_layer": 1, "ocr": 1},
        },
    )


def _docling_envelope(case: ScannerEvalCase):
    adapter = DoclingLocalParserAdapter(
        extractor=lambda _data: DoclingExtractionResult(
            markdown=f"# Table baseline\n\n| Field | Value |\n| --- | --- |\n| case | {case.case_id} |",
            raw_payload={"tables": [{"cells": 4}], "pages": [{"width": 612, "height": 792}]},
            page_count=1,
            pages=[{"width": 612, "height": 792}],
            objects=[{"object_type": "heading", "text": "Table baseline", "page_index": 1}],
            tables=[{"object_type": "table", "text": f"case {case.case_id}", "page_index": 1, "cells": 4}],
            backend_version="mock-docling",
        )
    )
    return adapter.scan_pdf_bytes(
        pdf_bytes=b"%PDF-1.4\n%EOF",
        context=_context(case, "docling_local"),
        store=LocalCASObjectStore(),
    )


def _provider_envelope(case: ScannerEvalCase):
    if case.capture_mode == "photo" or "vision_only" in case.expected_acquisition_modes:
        adapter = GeminiDocumentFallbackMockAdapter(
            mock_result=ProviderMockResult(
                markdown=f"## Page 1\n\nPremium fallback baseline for {case.case_id}.",
                raw_payload={"case_id": case.case_id, "vision": True},
                model_id="gemini-document-mock",
                estimated_cost_usd=1.0,
            )
        )
        return adapter.scan_with_policy(
            context=_context(case, "gemini_document_fallback"),
            policy=ProviderPolicy(allow_premium=True, estimated_cost_usd=1.0, max_cost_usd=2.0),
            store=LocalCASObjectStore(),
        )
    adapter = MistralOCRMockAdapter(
        mock_result=ProviderMockResult(
            markdown=f"## Page 1\n\nManaged parser baseline for {case.case_id}.",
            raw_payload={"case_id": case.case_id},
            model_id="mistral-ocr-mock",
            estimated_cost_usd=0.03,
        )
    )
    return adapter.scan_with_policy(
        context=_context(case, "mistral_ocr"),
        policy=ProviderPolicy(allow_managed=True, estimated_cost_usd=0.03, max_cost_usd=0.10),
        store=LocalCASObjectStore(),
    )


def mock_envelope_for_eval_case(case: ScannerEvalCase):
    if case.document_class in {"tables_heavy"}:
        return _docling_envelope(case)
    if case.document_class in {"form_like"}:
        return _provider_envelope(case)
    if case.capture_mode == "mixed" or "mixed" in case.expected_acquisition_modes and case.document_class == "mixed_pdf":
        return _mixed_envelope(case)
    if case.capture_mode == "born_digital" and case.document_class not in {"weak_text_layer_pdf"}:
        return _native_envelope(case)
    if case.document_class in {"image_document"}:
        return _provider_envelope(case)
    return _ocr_envelope(case)


def run_mock_eval(cases: Iterable[ScannerEvalCase]) -> List[ScannerEvalResult]:
    results: List[ScannerEvalResult] = []
    for case in cases:
        envelope = mock_envelope_for_eval_case(case)
        results.append(evaluate_scanner_envelope_contract(envelope, case))
    return results

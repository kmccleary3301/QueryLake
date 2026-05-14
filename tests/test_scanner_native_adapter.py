from __future__ import annotations

import json

import pytest

from QueryLake.files.object_store import LocalCASObjectStore
from QueryLake.scanning.adapters import ScannerRunContext
from QueryLake.scanning.native import (
    NativeExtractionResult,
    NativeTextQualityError,
    NativeTextQualityPolicy,
    PyMuPDF4LLMNativeAdapter,
    assess_native_text_quality,
    split_markdown_pages,
)


def test_pymupdf4llm_adapter_availability_is_lazy_and_optional():
    availability = PyMuPDF4LLMNativeAdapter().check_available()

    assert availability.backend_id == "pymupdf4llm_native"
    if availability.available:
        assert availability.reason == "available"
    else:
        assert availability.reason == "missing_optional_dependency:pymupdf4llm"
        assert availability.md["install_extra"] == "querylake-backend[scanners-native]"


def test_native_quality_accepts_strong_born_digital_text():
    assessment = assess_native_text_quality(
        [
            "Introduction\n" + ("A strong native text page with content. " * 8),
            "Methods\n" + ("Another strong native text page with content. " * 8),
        ],
        NativeTextQualityPolicy(min_total_chars=100, min_chars_per_page=80, min_qualified_page_coverage=1.0),
    )

    assert assessment.selected is True
    assert assessment.reason == "quality_pass"
    assert assessment.pages == 2
    assert assessment.qualified_pages == 2


def test_native_quality_rejects_sparse_or_repeated_text():
    sparse = assess_native_text_quality(["short", ""], NativeTextQualityPolicy(min_total_chars=100))
    repeated = assess_native_text_quality(
        ["same line\n" * 40],
        NativeTextQualityPolicy(
            min_total_chars=100,
            min_chars_per_page=10,
            min_qualified_page_coverage=1.0,
            max_repeated_line_ratio=0.20,
        ),
    )

    assert sparse.selected is False
    assert sparse.reason == "min_total_chars_miss"
    assert repeated.selected is False
    assert repeated.reason == "repeated_line_ratio_exceeded"


def test_split_markdown_pages_uses_page_headers_when_present():
    pages = split_markdown_pages("## Page 1\n\nAlpha\n\n## Page 2\n\nBeta")

    assert pages == ["Alpha", "Beta"]


def test_pymupdf4llm_adapter_maps_injected_extraction_to_native_envelope(tmp_path):
    def _extractor(_pdf_bytes: bytes) -> NativeExtractionResult:
        return NativeExtractionResult(
            markdown="## Page 1\n\n" + ("Native markdown paragraph. " * 10),
            page_markdown=["Native markdown paragraph. " * 10],
            raw_payload={"pages": [{"number": 1, "blocks": 1}]},
            backend_version="test-version",
        )

    adapter = PyMuPDF4LLMNativeAdapter(
        quality_policy=NativeTextQualityPolicy(min_total_chars=50, min_chars_per_page=50),
        extractor=_extractor,
    )
    store = LocalCASObjectStore(tmp_path / "cas")
    envelope = adapter.scan_pdf_bytes(
        pdf_bytes=b"%PDF-1.4\n%EOF",
        context=ScannerRunContext(
            run_id="native_run_1",
            backend_id="pymupdf4llm_native",
            backend_class="native_digital_extraction",
            support_tier="first_class",
            file_id="file_1",
            file_version_id="fv_1",
            config_hash="native-policy-v1",
            md={"source": "unit"},
        ),
        store=store,
    )

    assert envelope.scan_run.backend_id == "pymupdf4llm_native"
    assert envelope.scan_run.backend_version == "test-version"
    assert envelope.scan_run.config_hash == "native-policy-v1"
    assert envelope.contract.acquisition_mode == "native_text"
    assert envelope.contract.raw_backend_contract == "pymupdf4llm_markdown"
    assert envelope.contract.geometry_level == "block"
    assert envelope.pages[0].acquisition_mode == "native_text"
    assert envelope.legacy_projection().compatibility_contract == "text_layer_fastpath_markdown"
    assert envelope.quality["native_text_quality"]["selected"] is True

    raw_artifact = [
        artifact for artifact in envelope.artifacts if artifact.artifact_type == "scanner_raw_payload"
    ][0]
    raw_payload = json.loads(store.get_bytes(raw_artifact.storage_ref).decode("utf-8"))
    assert raw_payload["backend_id"] == "pymupdf4llm_native"
    assert raw_payload["raw_payload"]["pages"][0]["blocks"] == 1


def test_pymupdf4llm_adapter_rejects_weak_native_text():
    adapter = PyMuPDF4LLMNativeAdapter(
        quality_policy=NativeTextQualityPolicy(min_total_chars=1000),
        extractor=lambda _pdf_bytes: NativeExtractionResult(markdown="too short", page_markdown=["too short"]),
    )

    with pytest.raises(NativeTextQualityError) as exc:
        adapter.scan_pdf_bytes(
            pdf_bytes=b"%PDF-1.4\n%EOF",
            context=ScannerRunContext(
                run_id="native_run_weak",
                backend_id="pymupdf4llm_native",
                backend_class="native_digital_extraction",
                support_tier="first_class",
            ),
        )

    assert exc.value.assessment.reason == "min_total_chars_miss"

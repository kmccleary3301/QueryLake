from __future__ import annotations

from QueryLake.scanning.adapters import LegacyMarkdownScanResult, ScannerAdapter, ScannerRunContext
from QueryLake.scanning.chandra import ChandraCompatibilityAdapter, build_chandra_compatibility_envelope
from QueryLake.scanning.contracts import validate_scanner_envelope


def _context() -> ScannerRunContext:
    return ScannerRunContext(
        run_id="chandra_run_1",
        backend_id="chandra_1",
        backend_class="incumbent_continuity",
        support_tier="first_class",
        file_id="file_1",
        file_version_id="fv_1",
        document_version_id="dv_1",
        config_hash="profile-balanced-dpi-192",
        md={"source": "unit_fixture"},
    )


def _result() -> LegacyMarkdownScanResult:
    return LegacyMarkdownScanResult(
        markdown="## Page 1\n\nNative text\n\n## Page 2\n\nOCR text",
        page_markdown=["## Page 1\n\nNative text", "## Page 2\n\nOCR text"],
        ocr_info_cas="ocr-info-cas",
        page_image_cas_by_page={"0002": "page-2-image-cas"},
        page_ocr_json_cas_by_page={"0002": "page-2-ocr-json-cas"},
        meta={
            "engine": "chandra",
            "profile": "balanced",
            "pages": 2,
            "ocr_pages": 1,
            "text_layer_pages": 1,
            "output_contract": "mixed_text_layer_fastpath_markdown",
            "page_source_by_page": {"0001": "text_layer", "0002": "ocr"},
            "page_source_counts": {"text_layer": 1, "ocr": 1},
            "render_cache_hits": 3,
            "render_cache_misses": 1,
            "render_dpi": 192,
            "render_target_max_image_pixels": 14000000,
            "page_complexity_counts": {"simple": 1, "mixed": 1, "complex": 0},
            "page_complexity_by_page": {
                "0002": {"class": "mixed", "dark_pixel_ratio": 0.08},
            },
            "page_geometry_by_page": {
                "0001": {"width": 612, "height": 792, "rotation": 0},
                "0002": {"width": 612, "height": 792, "rotation": 0},
            },
        },
    )


def test_chandra_compatibility_adapter_satisfies_scanner_adapter_protocol():
    adapter = ChandraCompatibilityAdapter()

    assert isinstance(adapter, ScannerAdapter)
    availability = adapter.check_available()
    assert availability.available is True
    assert availability.reason == "mapping_only_adapter_available"
    assert availability.md["calls_runtime"] is False


def test_chandra_compatibility_wrapper_preserves_mixed_contract_and_page_refs():
    envelope = build_chandra_compatibility_envelope(context=_context(), result=_result())

    validate_scanner_envelope(envelope)
    assert envelope.scan_run.backend_id == "chandra_1"
    assert envelope.scan_run.config_hash == "profile-balanced-dpi-192"
    assert envelope.contract.legacy_output_contract == "mixed_text_layer_fastpath_markdown"
    assert envelope.contract.acquisition_mode == "mixed"
    assert [page.acquisition_mode for page in envelope.pages] == ["native_text", "ocr"]
    assert envelope.quality["page_source_counts"] == {"text_layer": 1, "ocr": 1}
    assert envelope.pages[1].quality == {"class": "mixed", "dark_pixel_ratio": 0.08}
    assert envelope.pages[1].width == 612
    assert envelope.pages[1].artifact_refs == [
        "chandra_run_1:page:0002:image",
        "chandra_run_1:page:0002:ocr_json",
    ]

    artifacts = {artifact.artifact_id: artifact for artifact in envelope.artifacts}
    assert artifacts["chandra_run_1:chandra_ocr_info"].storage_ref == "ocr-info-cas"
    assert artifacts["chandra_run_1:page:0002:image"].artifact_type == "scanner_page_image"
    assert artifacts["chandra_run_1:page:0002:image"].storage_ref == "page-2-image-cas"
    assert artifacts["chandra_run_1:page:0002:ocr_json"].artifact_type == "scanner_raw_payload"
    assert artifacts["chandra_run_1:page:0002:ocr_json"].storage_ref == "page-2-ocr-json-cas"


def test_chandra_adapter_maps_existing_output_without_runtime_call():
    adapter = ChandraCompatibilityAdapter()
    envelope = adapter.map_existing_output_to_envelope(_result(), _context())

    assert envelope.canonical_text() == "## Page 1\n\nNative text\n\n## Page 2\n\nOCR text"
    assert envelope.scan_run.md["adapter_context"] == {"source": "unit_fixture"}
    assert envelope.scan_run.md["render_cache_hits"] == 3
    assert envelope.pages[0].md["chandra_profile"] == "balanced"

from __future__ import annotations

from QueryLake.files.object_store import LocalCASObjectStore
from QueryLake.scanning.adapters import LegacyMarkdownScanResult, ScannerRunContext
from QueryLake.scanning.chandra import build_chandra_compatibility_envelope
from QueryLake.scanning.integration import (
    build_scanner_document_artifact_payload,
    build_scanner_enriched_ocr_done_payload,
    build_scanner_job_result_metadata,
)
from QueryLake.scanning.persistence import write_scanner_envelope


def _persisted(tmp_path):
    envelope = build_chandra_compatibility_envelope(
        context=ScannerRunContext(
            run_id="scan_job_1",
            backend_id="chandra_1",
            backend_class="incumbent_continuity",
            support_tier="first_class",
            file_id="file_1",
            file_version_id="fv_1",
        ),
        result=LegacyMarkdownScanResult(
            markdown="job metadata text",
            ocr_info_cas="ocr-info-cas",
            meta={
                "engine": "chandra",
                "profile": "balanced",
                "pages": 1,
                "ocr_pages": 1,
                "text_layer_pages": 0,
                "output_contract": "ocr_markdown",
                "page_source_by_page": {"0001": "ocr"},
                "page_source_counts": {"ocr": 1, "text_layer": 0},
                "render_cache_hits": 0,
                "render_cache_misses": 1,
            },
        ),
    )
    persisted = write_scanner_envelope(LocalCASObjectStore(tmp_path / "cas"), envelope)
    return envelope, persisted


def test_scanner_job_result_metadata_is_bounded_and_attachable(tmp_path):
    envelope, persisted = _persisted(tmp_path)

    metadata = build_scanner_job_result_metadata(envelope, persisted, route_explanation_ref="route-cas")
    scanner = metadata["scanner"]

    assert scanner["run_id"] == "scan_job_1"
    assert scanner["backend_id"] == "chandra_1"
    assert scanner["acquisition_mode"] == "ocr"
    assert scanner["legacy_output_contract"] == "ocr_markdown"
    assert scanner["scanner_envelope_cas"] == persisted.envelope_ref.storage_ref
    assert scanner["route_explanation_ref"] == "route-cas"
    assert scanner["summary"]["page_count"] == 1


def test_scanner_document_artifact_payload_matches_existing_artifact_shape(tmp_path):
    _envelope, persisted = _persisted(tmp_path)

    payload = build_scanner_document_artifact_payload(persisted)

    assert payload["artifact_type"] == "scanner_envelope"
    assert payload["modality"] == "document_scan"
    assert payload["storage_ref"] == persisted.envelope_ref.storage_ref
    assert payload["text"] is None
    assert payload["md"]["run_id"] == "scan_job_1"


def test_scanner_enriched_ocr_done_payload_preserves_existing_fields(tmp_path):
    envelope, persisted = _persisted(tmp_path)
    existing = {
        "pages": 1,
        "ocr_json_cas": "ocr-info-cas",
        "engine": "chandra",
        "profile": "balanced",
        "render_cache_hits": 0,
        "render_cache_misses": 1,
    }

    enriched = build_scanner_enriched_ocr_done_payload(existing, envelope, persisted)

    assert enriched["pages"] == 1
    assert enriched["ocr_json_cas"] == "ocr-info-cas"
    assert enriched["engine"] == "chandra"
    assert enriched["scanner"]["scanner_envelope_cas"] == persisted.envelope_ref.storage_ref
    assert enriched["scanner"]["raw_backend_contract"] == "chandra_ocr_markdown"

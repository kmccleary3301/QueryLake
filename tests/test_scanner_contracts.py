from __future__ import annotations

import pytest

from QueryLake.scanning.contracts import (
    ArtifactRef,
    PageRecord,
    Projection,
    RoutingDecision,
    ScanContract,
    ScanObject,
    ScanRun,
    ScannerEnvelope,
    normalize_legacy_output_contract,
    validate_scanner_envelope,
)


def _minimal_envelope() -> ScannerEnvelope:
    return ScannerEnvelope(
        schema_version="scanner_envelope_v1",
        scan_run=ScanRun(
            run_id="scan_1",
            backend_id="chandra_1",
            backend_class="incumbent_continuity",
            support_tier="first_class",
            status="succeeded",
            file_id="file_1",
            file_version_id="fv_1",
        ),
        contract=ScanContract(
            legacy_output_contract="ocr_markdown",
            raw_backend_contract="chandra_ocr_markdown",
            acquisition_mode="ocr",
            projection_kinds=["canonical_markdown", "canonical_text", "chunk_compat"],
            structure_level="block",
            geometry_level="page",
        ),
        artifacts=[ArtifactRef(artifact_id="art_raw", artifact_type="scanner_raw_payload", storage_ref="cas_123")],
        pages=[PageRecord(page_index=1, acquisition_mode="ocr", width=612, height=792)],
        objects=[
            ScanObject(
                object_id="obj_1",
                object_type="paragraph",
                page_index=1,
                reading_order=1,
                text="Hello world",
                confidence=None,
                confidence_available=False,
            )
        ],
        projections=[
            Projection(
                projection_id="proj_md",
                projection_kind="canonical_markdown",
                text="## Page 1\n\nHello world",
                compatibility_contract="ocr_markdown",
            ),
            Projection(
                projection_id="proj_text",
                projection_kind="canonical_text",
                text="Hello world",
            ),
        ],
        routing=[RoutingDecision(backend_id="chandra_1", action="selected", reason="continuity_default")],
    )


def test_scanner_envelope_serializes_and_validates():
    envelope = _minimal_envelope()

    validate_scanner_envelope(envelope)
    payload = envelope.to_payload()

    assert payload["schema_version"] == "scanner_envelope_v1"
    assert payload["scan_run"]["backend_id"] == "chandra_1"
    assert payload["contract"]["legacy_output_contract"] == "ocr_markdown"
    assert payload["artifacts"][0]["storage_ref"] == "cas_123"
    assert envelope.canonical_text() == "Hello world"
    assert envelope.legacy_projection().projection_id == "proj_md"


def test_legacy_output_contract_validation_preserves_current_values():
    assert normalize_legacy_output_contract("ocr_markdown") == "ocr_markdown"
    assert normalize_legacy_output_contract("text_layer_fastpath_markdown") == "text_layer_fastpath_markdown"
    assert normalize_legacy_output_contract("mixed_text_layer_fastpath_markdown") == "mixed_text_layer_fastpath_markdown"

    with pytest.raises(ValueError, match="Unknown legacy scanner output contract"):
        normalize_legacy_output_contract("opaque_new_contract")


def test_missing_confidence_is_not_low_confidence():
    envelope = _minimal_envelope()
    obj = envelope.objects[0]

    assert obj.confidence is None
    assert obj.confidence_available is False
    validate_scanner_envelope(envelope)


def test_native_ocr_mixed_and_vision_modes_are_distinct():
    modes = {"native_text", "ocr", "mixed", "vision_only"}
    envelopes = []
    for idx, mode in enumerate(sorted(modes), start=1):
        envelopes.append(
            ScannerEnvelope(
                schema_version="scanner_envelope_v1",
                scan_run=ScanRun(
                    run_id=f"scan_{idx}",
                    backend_id="backend",
                    backend_class="test",
                    support_tier="experimental",
                    status="succeeded",
                ),
                contract=ScanContract(
                    legacy_output_contract=None,
                    raw_backend_contract=f"raw_{mode}",
                    acquisition_mode=mode,  # type: ignore[arg-type]
                    projection_kinds=["canonical_text"],
                    structure_level="text_only",
                    geometry_level="none",
                ),
                pages=[PageRecord(page_index=1, acquisition_mode=mode)],  # type: ignore[arg-type]
                projections=[Projection(projection_id=f"proj_{idx}", projection_kind="canonical_text", text=mode)],
            )
        )

    for envelope in envelopes:
        validate_scanner_envelope(envelope)

    assert {envelope.contract.acquisition_mode for envelope in envelopes} == modes


def test_invalid_page_index_is_rejected():
    envelope = ScannerEnvelope(
        schema_version="scanner_envelope_v1",
        scan_run=ScanRun(
            run_id="scan_bad",
            backend_id="backend",
            backend_class="test",
            support_tier="experimental",
            status="succeeded",
        ),
        contract=ScanContract(
            legacy_output_contract=None,
            raw_backend_contract="raw",
            acquisition_mode="ocr",
            projection_kinds=["canonical_text"],
            structure_level="text_only",
            geometry_level="none",
        ),
        pages=[PageRecord(page_index=0, acquisition_mode="ocr")],
    )

    with pytest.raises(ValueError, match="page_index"):
        validate_scanner_envelope(envelope)

from QueryLake.scanning.contracts import materialize_legacy_markdown_envelope


def test_materialize_legacy_ocr_markdown_envelope():
    envelope = materialize_legacy_markdown_envelope(
        run_id="run_ocr",
        backend_id="chandra_1",
        backend_class="incumbent_continuity",
        support_tier="first_class",
        legacy_output_contract="ocr_markdown",
        markdown="page one\n\npage two",
        meta={
            "engine": "chandra",
            "pages": 2,
            "page_source_by_page": {"0001": "ocr", "0002": "ocr"},
            "page_source_counts": {"ocr": 2, "text_layer": 0},
        },
    )

    assert envelope.contract.acquisition_mode == "ocr"
    assert envelope.contract.raw_backend_contract == "chandra_ocr_markdown"
    assert [page.acquisition_mode for page in envelope.pages] == ["ocr", "ocr"]
    assert envelope.legacy_projection().text == "page one\n\npage two"
    assert envelope.quality["page_source_counts"] == {"ocr": 2, "text_layer": 0}
    validate_scanner_envelope(envelope)


def test_materialize_legacy_text_layer_envelope():
    envelope = materialize_legacy_markdown_envelope(
        run_id="run_native",
        backend_id="pymupdf4llm_native",
        backend_class="native_digital_extraction",
        support_tier="first_class",
        legacy_output_contract="text_layer_fastpath_markdown",
        markdown="native text",
        meta={
            "engine": "pdf_text_layer",
            "pages": 1,
            "page_source_by_page": {"0001": "text_layer"},
            "page_source_counts": {"ocr": 0, "text_layer": 1},
        },
    )

    assert envelope.contract.acquisition_mode == "native_text"
    assert envelope.contract.geometry_level == "none"
    assert envelope.pages[0].acquisition_mode == "native_text"
    assert envelope.legacy_projection().compatibility_contract == "text_layer_fastpath_markdown"
    validate_scanner_envelope(envelope)


def test_materialize_legacy_mixed_envelope_preserves_page_truth():
    envelope = materialize_legacy_markdown_envelope(
        run_id="run_mixed",
        backend_id="chandra_1",
        backend_class="incumbent_continuity",
        support_tier="first_class",
        legacy_output_contract="mixed_text_layer_fastpath_markdown",
        markdown="mixed text",
        meta={
            "engine": "chandra",
            "pages": 3,
            "page_source_by_page": {"0001": "text_layer", "0002": "ocr", "0003": "text_layer"},
            "page_source_counts": {"ocr": 1, "text_layer": 2},
        },
    )

    assert envelope.contract.acquisition_mode == "mixed"
    assert [page.acquisition_mode for page in envelope.pages] == ["native_text", "ocr", "native_text"]
    assert envelope.quality["page_source_counts"] == {"ocr": 1, "text_layer": 2}
    validate_scanner_envelope(envelope)

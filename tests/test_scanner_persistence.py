from __future__ import annotations

import json

import pytest

from QueryLake.files.object_store import LocalCASObjectStore
from QueryLake.scanning.contracts import materialize_legacy_markdown_envelope
from QueryLake.scanning.persistence import (
    SCANNER_ARTIFACT_TYPES,
    SCANNER_ENVELOPE_ARTIFACT_TYPE,
    read_scanner_envelope_payload,
    scanner_envelope_to_json_bytes,
    summarize_scanner_envelope_payload,
    write_scanner_envelope,
)


def _envelope():
    return materialize_legacy_markdown_envelope(
        run_id="persist_run",
        backend_id="chandra_1",
        backend_class="incumbent_continuity",
        support_tier="first_class",
        legacy_output_contract="ocr_markdown",
        markdown="## Page 1\n\nPersist me",
        meta={"engine": "chandra", "pages": 1, "page_source_by_page": {"0001": "ocr"}},
        file_id="file_1",
        file_version_id="fv_1",
        document_version_id="dv_1",
    )


def test_scanner_envelope_serialization_is_stable_json():
    envelope = _envelope()
    first = scanner_envelope_to_json_bytes(envelope)
    second = scanner_envelope_to_json_bytes(envelope)

    assert first == second
    payload = json.loads(first.decode("utf-8"))
    assert payload["schema_version"] == "scanner_envelope_v1"
    assert payload["scan_run"]["run_id"] == "persist_run"


def test_scanner_envelope_can_be_persisted_and_reloaded_from_cas(tmp_path):
    store = LocalCASObjectStore(tmp_path / "cas")
    envelope = _envelope()

    persisted = write_scanner_envelope(store, envelope)
    payload = read_scanner_envelope_payload(store, persisted.envelope_ref.storage_ref)

    assert persisted.envelope_ref.artifact_type == SCANNER_ENVELOPE_ARTIFACT_TYPE
    assert persisted.envelope_ref.mime_type == "application/vnd.querylake.scanner-envelope+json"
    assert persisted.envelope_ref.bytes_sha256 == persisted.envelope_ref.storage_ref
    assert payload["scan_run"]["run_id"] == "persist_run"
    assert payload["contract"]["legacy_output_contract"] == "ocr_markdown"
    assert payload["projections"][0]["text"] == "## Page 1\n\nPersist me"


def test_scanner_envelope_summary_is_bounded_and_interpretable(tmp_path):
    store = LocalCASObjectStore(tmp_path / "cas")
    persisted = write_scanner_envelope(store, _envelope())
    payload = read_scanner_envelope_payload(store, persisted.envelope_ref.storage_ref)

    summary = summarize_scanner_envelope_payload(payload)

    assert summary == {
        "schema_version": "scanner_envelope_v1",
        "run_id": "persist_run",
        "backend_id": "chandra_1",
        "backend_class": "incumbent_continuity",
        "support_tier": "first_class",
        "status": "succeeded",
        "legacy_output_contract": "ocr_markdown",
        "raw_backend_contract": "chandra_ocr_markdown",
        "acquisition_mode": "ocr",
        "page_count": 1,
        "projection_kinds": ["canonical_markdown", "canonical_text", "chunk_compat"],
        "routing_actions": ["selected"],
        "warning_count": 0,
        "error_count": 0,
    }


def test_missing_scanner_envelope_ref_is_explicit(tmp_path):
    store = LocalCASObjectStore(tmp_path / "cas")

    with pytest.raises(FileNotFoundError, match="scanner envelope CAS object not found"):
        read_scanner_envelope_payload(store, "missing")


def test_scanner_artifact_type_vocabulary_includes_first_wave_shapes():
    assert {
        "scanner_envelope",
        "scanner_raw_payload",
        "scanner_canonical_markdown",
        "scanner_canonical_text",
        "scanner_layout_graph",
        "scanner_structured_fields",
        "scanner_shadow_result",
    } <= SCANNER_ARTIFACT_TYPES

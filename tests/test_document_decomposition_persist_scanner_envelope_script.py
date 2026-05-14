from QueryLake.scanning.contracts import materialize_legacy_markdown_envelope
from scripts.document_decomposition_persist_scanner_envelope import scanner_envelope_from_payload


def test_scanner_envelope_from_payload_round_trips_legacy_envelope():
    envelope = materialize_legacy_markdown_envelope(
        run_id="run1",
        backend_id="chandra_1",
        backend_class="incumbent_continuity",
        support_tier="first_class",
        legacy_output_contract="ocr_markdown",
        markdown="hello",
        meta={"pages": 1},
        file_id="file1",
        file_version_id="fv1",
        document_version_id="dv1",
    )
    restored = scanner_envelope_from_payload(envelope.to_payload())
    assert restored.scan_run.run_id == "run1"
    assert restored.contract.raw_backend_contract == "legacy_ocr_markdown"
    assert restored.projections[0].text == "hello"


def test_persist_scanner_envelope_script_documents_mapping_requirement():
    source = __import__("pathlib").Path("scripts/document_decomposition_persist_scanner_envelope.py").read_text()
    assert "scanner envelope has no document_version_id" in source
    assert "persist_document_linked_scanner_decomposition" in source

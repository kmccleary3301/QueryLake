from __future__ import annotations

import json

from QueryLake.files.object_store import LocalCASObjectStore
from QueryLake.scanning.adapters import ScannerRunContext
from QueryLake.scanning.docling import DoclingExtractionResult, DoclingLocalParserAdapter


def test_docling_adapter_availability_is_lazy_and_optional():
    availability = DoclingLocalParserAdapter().check_available()

    assert availability.backend_id == "docling_local"
    if availability.available:
        assert availability.reason == "available"
    else:
        assert availability.reason == "missing_optional_dependency:docling"
        assert availability.md["install_extra"] == "querylake-backend[scanners-local]"


def test_docling_adapter_maps_tables_objects_and_raw_payload(tmp_path):
    def _extractor(_pdf_bytes: bytes) -> DoclingExtractionResult:
        return DoclingExtractionResult(
            markdown="# Report\n\n| A | B |\n| --- | --- |\n| 1 | 2 |",
            raw_payload={"pages": [{"width": 612, "height": 792}], "tables": [{"cells": 4}]},
            page_count=1,
            pages=[{"width": 612, "height": 792, "quality": {"source": "fixture"}}],
            objects=[{"object_type": "heading", "text": "Report", "page_index": 1, "bbox": [0, 0, 100, 20]}],
            tables=[{"object_type": "table", "text": "A B 1 2", "page_index": 1, "bbox": [0, 30, 200, 90], "cells": 4}],
            figures=[{"object_type": "figure", "text": "Chart", "page_index": 1}],
            backend_version="test-docling",
        )

    adapter = DoclingLocalParserAdapter(extractor=_extractor)
    store = LocalCASObjectStore(tmp_path / "cas")
    envelope = adapter.scan_pdf_bytes(
        pdf_bytes=b"%PDF-1.4\n%EOF",
        context=ScannerRunContext(
            run_id="docling_run_1",
            backend_id="docling_local",
            backend_class="general_local_parser",
            support_tier="first_class",
            file_id="file_1",
            file_version_id="fv_1",
            config_hash="docling-policy-v1",
            md={"source": "unit"},
        ),
        store=store,
    )

    assert envelope.scan_run.backend_id == "docling_local"
    assert envelope.scan_run.backend_version == "test-docling"
    assert envelope.contract.raw_backend_contract == "docling_document"
    assert envelope.contract.structure_level == "table_cell"
    assert envelope.contract.geometry_level == "table_cell"
    assert envelope.pages[0].width == 612
    assert {obj.object_type for obj in envelope.objects} == {"heading", "table", "figure"}
    assert any(projection.projection_kind == "structured_fields" for projection in envelope.projections)
    assert envelope.quality["table_count"] == 1

    raw_artifact = [artifact for artifact in envelope.artifacts if artifact.artifact_type == "scanner_raw_payload"][0]
    raw_payload = json.loads(store.get_bytes(raw_artifact.storage_ref).decode("utf-8"))
    assert raw_payload["raw_payload"]["tables"][0]["cells"] == 4

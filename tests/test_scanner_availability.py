from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from QueryLake.scanning.availability import scanner_availability_rows, scanner_availability_to_markdown
from QueryLake.scanning.docling import DoclingLocalParserAdapter


ROOT = Path(__file__).resolve().parents[1]


def test_docling_adapter_availability_is_lazy_and_optional():
    availability = DoclingLocalParserAdapter().check_available()

    assert availability.backend_id == "docling_local"
    if availability.available:
        assert availability.reason == "available"
    else:
        assert availability.reason == "missing_optional_dependency:docling"
        assert availability.md["integration_state"] == "mapping_adapter"


def test_scanner_availability_rows_include_known_and_unimplemented_backends():
    rows = scanner_availability_rows()
    by_backend = {row["backend_id"]: row for row in rows}

    assert by_backend["chandra_1"]["available"] is True
    assert by_backend["pymupdf4llm_native"]["reason"] in {
        "available",
        "missing_optional_dependency:pymupdf4llm",
    }
    assert by_backend["docling_local"]["reason"] in {
        "available",
        "missing_optional_dependency:docling",
    }
    assert by_backend["mistral_ocr"]["reason"] == "live_adapter_disabled"
    assert by_backend["gemini_document_fallback"]["reason"] == "live_adapter_disabled"


def test_scanner_availability_markdown_is_bounded():
    markdown = scanner_availability_to_markdown(scanner_availability_rows())

    assert "# Scanner Availability" in markdown
    assert "| backend_id | support_tier | routing_eligibility | available | reason |" in markdown
    assert "gemini_document_fallback" in markdown


def test_scanner_availability_report_script_outputs_json():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "scanner_availability_report.py"), "--format", "json"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert '"backend_id": "chandra_1"' in proc.stdout
    assert '"backend_id": "pymupdf4llm_native"' in proc.stdout

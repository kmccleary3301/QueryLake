from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from QueryLake.scanning.registry import (
    ScannerBackendSpec,
    build_default_scanner_registry,
    filter_registry_by_support_tier,
    get_backend_spec,
    registry_report_rows,
    validate_backend_spec,
    validate_scanner_registry,
)


def test_default_scanner_registry_validates_and_contains_first_wave_backends():
    registry = build_default_scanner_registry()

    validate_scanner_registry(registry)

    assert set(registry) >= {
        "chandra_1",
        "chandra_2",
        "pymupdf4llm_native",
        "docling_local",
        "mineru_shadow",
        "mistral_ocr",
        "gemini_document_fallback",
    }
    assert registry["chandra_1"].support_tier == "first_class"
    assert registry["chandra_2"].support_tier == "experimental"
    assert registry["mineru_shadow"].routing_eligibility == "shadow_only"
    assert registry["gemini_document_fallback"].support_tier == "premium_fallback"
    assert registry["gemini_document_fallback"].escalation_only is True


def test_registry_report_rows_are_stable_and_sorted():
    rows = registry_report_rows(build_default_scanner_registry())

    backend_ids = [row["backend_id"] for row in rows]
    assert backend_ids == sorted(backend_ids)
    assert {row["backend_id"] for row in rows} >= {"chandra_1", "docling_local", "mistral_ocr"}
    assert all("support_tier" in row for row in rows)
    assert all("routing_eligibility" in row for row in rows)


def test_filter_registry_by_support_tier():
    registry = build_default_scanner_registry()
    first_class = filter_registry_by_support_tier(registry, ["first_class"])

    assert "chandra_1" in first_class
    assert "pymupdf4llm_native" in first_class
    assert "docling_local" in first_class
    assert "mistral_ocr" in first_class
    assert "gemini_document_fallback" not in first_class
    assert "mineru_shadow" not in first_class


def test_premium_fallback_requires_escalation_and_budget_policy():
    good = get_backend_spec(build_default_scanner_registry(), "gemini_document_fallback")
    bad = ScannerBackendSpec(**{**good.to_payload(), "budget_policy": None})

    with pytest.raises(ValueError, match="budget_policy"):
        validate_backend_spec(bad)

    bad_route = ScannerBackendSpec(**{**good.to_payload(), "routing_eligibility": "default_eligible"})
    with pytest.raises(ValueError, match="premium fallback must not be default eligible"):
        validate_backend_spec(bad_route)


def test_first_class_backends_require_contract_tests():
    good = get_backend_spec(build_default_scanner_registry(), "docling_local")
    bad = ScannerBackendSpec(**{**good.to_payload(), "contract_test_suite": []})

    with pytest.raises(ValueError, match="first_class backends require contract_test_suite"):
        validate_backend_spec(bad)


def test_registry_report_script_outputs_markdown():
    root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, str(root / "scripts" / "scanner_registry_report.py"), "--format", "markdown"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "| backend_id |" in proc.stdout
    assert "chandra_1" in proc.stdout
    assert "gemini_document_fallback" in proc.stdout

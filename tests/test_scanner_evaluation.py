from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from QueryLake.scanning.contracts import materialize_legacy_markdown_envelope
from QueryLake.scanning.evaluation import (
    ScannerEvalCase,
    eval_results_to_markdown,
    evaluate_scanner_envelope_contract,
    load_eval_manifest,
    summarize_eval_results,
    validate_eval_cases,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tests" / "fixtures" / "scanning" / "eval_manifest_v1.json"


def test_eval_manifest_loads_document_class_inventory():
    cases = load_eval_manifest(MANIFEST)

    assert len(cases) >= 8
    assert {case.document_class for case in cases} >= {
        "born_digital_pdf",
        "scanned_pdf",
        "mixed_pdf",
        "tables_heavy",
        "form_like",
        "scientific_paper",
        "image_document",
    }


def test_eval_case_validation_rejects_duplicates():
    case = ScannerEvalCase(
        case_id="dup",
        document_class="born_digital_pdf",
        capture_mode="born_digital",
        source_ref="fixture://dup",
    )

    with pytest.raises(ValueError, match="duplicate eval case_id"):
        validate_eval_cases([case, case])


def test_evaluate_scanner_envelope_contract_passes_native_case():
    case = ScannerEvalCase(
        case_id="native_case",
        document_class="born_digital_pdf",
        capture_mode="born_digital",
        source_ref="fixture://native",
        expected_acquisition_modes=["native_text"],
        required_projection_kinds=["canonical_text", "canonical_markdown", "chunk_compat"],
    )
    envelope = materialize_legacy_markdown_envelope(
        run_id="native_run",
        backend_id="pymupdf4llm_native",
        backend_class="native_digital_extraction",
        support_tier="first_class",
        legacy_output_contract="text_layer_fastpath_markdown",
        markdown="native text",
        meta={
            "engine": "pymupdf4llm",
            "pages": 1,
            "page_source_by_page": {"0001": "native_text"},
            "page_source_counts": {"native_text": 1, "ocr": 0},
        },
    )

    result = evaluate_scanner_envelope_contract(envelope, case)

    assert result.passed is True
    assert result.checks["expected_acquisition_mode_present"] is True
    assert result.metrics["acquisition_modes"] == ["native_text"]


def test_evaluate_scanner_envelope_contract_surfaces_missing_projection():
    case = ScannerEvalCase(
        case_id="layout_case",
        document_class="tables_heavy",
        capture_mode="born_digital",
        source_ref="fixture://table",
        required_projection_kinds=["canonical_text", "structured_fields"],
    )
    envelope = materialize_legacy_markdown_envelope(
        run_id="native_run",
        backend_id="pymupdf4llm_native",
        backend_class="native_digital_extraction",
        support_tier="first_class",
        legacy_output_contract="text_layer_fastpath_markdown",
        markdown="native text",
        meta={"engine": "pymupdf4llm", "pages": 1},
    )

    result = evaluate_scanner_envelope_contract(envelope, case)

    assert result.passed is False
    assert result.checks["required_projection_kinds_present"] is False
    assert "required_projection_kinds_present" in eval_results_to_markdown([result])


def test_eval_summary_groups_by_backend():
    case = ScannerEvalCase(
        case_id="native_case",
        document_class="born_digital_pdf",
        capture_mode="born_digital",
        source_ref="fixture://native",
    )
    envelope = materialize_legacy_markdown_envelope(
        run_id="native_run",
        backend_id="pymupdf4llm_native",
        backend_class="native_digital_extraction",
        support_tier="first_class",
        legacy_output_contract="text_layer_fastpath_markdown",
        markdown="native text",
        meta={"engine": "pymupdf4llm", "pages": 1},
    )
    result = evaluate_scanner_envelope_contract(envelope, case)

    summary = summarize_eval_results([result])

    assert summary["total"] == 1
    assert summary["passed"] == 1
    assert summary["by_backend"]["pymupdf4llm_native"]["passed"] == 1


def test_scanner_eval_report_script_outputs_manifest_markdown():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "scanner_eval_report.py"), "--manifest", str(MANIFEST)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "# Scanner Eval Manifest" in proc.stdout
    assert "born_digital_clean_pdf" in proc.stdout
    assert "| case_id | document_class | capture_mode | expected_acquisition_modes |" in proc.stdout

from QueryLake.scanning.evaluation import (
    ScannerPromotionThresholds,
    decide_backend_promotion,
    promotion_decisions_to_markdown,
)


def test_promotion_decision_accepts_backend_when_thresholds_pass():
    case = ScannerEvalCase(
        case_id="native_case_promote",
        document_class="born_digital_pdf",
        capture_mode="born_digital",
        source_ref="fixture://native",
    )
    envelope = materialize_legacy_markdown_envelope(
        run_id="native_run_promote",
        backend_id="pymupdf4llm_native",
        backend_class="native_digital_extraction",
        support_tier="first_class",
        legacy_output_contract="text_layer_fastpath_markdown",
        markdown="native text",
        meta={"engine": "pymupdf4llm", "pages": 1},
    )
    result = evaluate_scanner_envelope_contract(envelope, case)

    decision = decide_backend_promotion(
        "pymupdf4llm_native",
        [result],
        ScannerPromotionThresholds(min_cases=1, min_contract_pass_rate=1.0),
    )

    assert decision.promotable is True
    assert decision.reason == "thresholds_met"
    assert "pymupdf4llm_native" in promotion_decisions_to_markdown([decision])


def test_promotion_decision_rejects_insufficient_cases():
    decision = decide_backend_promotion(
        "docling_local",
        [],
        ScannerPromotionThresholds(min_cases=2),
    )

    assert decision.promotable is False
    assert decision.reason == "insufficient_cases"

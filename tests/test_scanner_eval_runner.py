from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from QueryLake.scanning.eval_diff import diff_eval_results, eval_diff_to_markdown
from QueryLake.scanning.eval_runner import run_mock_eval
from QueryLake.scanning.evaluation import load_eval_manifest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tests" / "fixtures" / "scanning" / "eval_manifest_v1.json"


def test_mock_eval_runner_covers_manifest_cases():
    cases = load_eval_manifest(MANIFEST)
    results = run_mock_eval(cases)

    assert len(results) == len(cases)
    assert all(result.passed for result in results)
    assert {result.backend_id for result in results} >= {"pymupdf4llm_native", "chandra_1", "docling_local"}


def test_eval_diff_passes_matching_results_and_detects_regression():
    results = run_mock_eval(load_eval_manifest(MANIFEST))
    passing_diff = diff_eval_results(results, results)
    regressed = [result if idx else type(result)(**{**result.to_payload(), "passed": False, "checks": {**result.checks, "envelope_valid": False}}) for idx, result in enumerate(results)]
    failing_diff = diff_eval_results(results, regressed)

    assert passing_diff.passed is True
    assert failing_diff.passed is False
    assert any(item.startswith("case_regressed:") for item in failing_diff.regressions)
    assert "Scanner Eval Diff" in eval_diff_to_markdown(failing_diff)


def test_eval_baseline_and_diff_scripts(tmp_path):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "scanner_eval_baseline.py"),
            "--manifest",
            str(MANIFEST),
            "--json-out",
            str(baseline),
            "--format",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    candidate.write_text(baseline.read_text(encoding="utf-8"), encoding="utf-8")
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "scanner_eval_diff.py"),
            "--baseline",
            str(baseline),
            "--candidate",
            str(candidate),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(baseline.read_text(encoding="utf-8"))
    assert payload["summary"]["failed"] == 0
    assert "Passed: `true`" in proc.stdout

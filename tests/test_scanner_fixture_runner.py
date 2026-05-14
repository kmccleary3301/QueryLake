from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.scanner_compatibility_fixture_runner import run_manifest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "scanning" / "legacy_compat_manifest_v1.json"


def test_legacy_compat_fixture_manifest_runs_all_cases():
    summary = run_manifest(FIXTURE)

    assert summary["schema_version"] == "scanner_legacy_compat_summary_v1"
    assert summary["case_count"] == 3
    assert summary["passed_count"] == 3
    assert summary["failed_count"] == 0
    assert {result["summary"]["legacy_output_contract"] for result in summary["results"]} == {
        "ocr_markdown",
        "text_layer_fastpath_markdown",
        "mixed_text_layer_fastpath_markdown",
    }


def test_legacy_compat_fixture_runner_cli_writes_summary(tmp_path):
    output = tmp_path / "summary.json"
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "scanner_compatibility_fixture_runner.py"), str(FIXTURE), "--output", str(output)],
        check=True,
        capture_output=True,
        text=True,
    )

    stdout_summary = json.loads(proc.stdout)
    file_summary = json.loads(output.read_text(encoding="utf-8"))
    assert stdout_summary["passed_count"] == 3
    assert file_summary == stdout_summary

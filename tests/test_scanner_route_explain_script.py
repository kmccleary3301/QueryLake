from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_scanner_route_explain_script_outputs_json(tmp_path):
    request_path = tmp_path / "request.json"
    request_path.write_text(
        json.dumps(
            {
                "request_id": "req_route_script",
                "source_ref": "cas",
                "mime_type": "application/pdf",
                "logical_name": "scan.pdf",
                "route_hints": {"capture_mode": "scanned"},
            }
        ),
        encoding="utf-8",
    )

    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "scanner_route_explain.py"), str(request_path)],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(proc.stdout)
    assert payload["primary_backend_id"] == "chandra_1"
    assert payload["action_counts"]["selected"] == 1
    assert payload["blocked_reasons"]["premium_policy_denied"] == 1


def test_scanner_route_explain_script_outputs_markdown(tmp_path):
    request_path = tmp_path / "request.json"
    request_path.write_text(
        json.dumps(
            {
                "request_id": "req_route_script_native",
                "source_ref": "cas",
                "mime_type": "application/pdf",
                "logical_name": "native.pdf",
                "route_hints": {"capture_mode": "born_digital", "has_native_text": True},
            }
        ),
        encoding="utf-8",
    )

    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "scanner_route_explain.py"), str(request_path), "--format", "markdown"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "# Scanner Routing Plan" in proc.stdout
    assert "pymupdf4llm_native" in proc.stdout

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_local_embedded_supported_slice_gate(tmp_path: Path) -> None:
    output_path = tmp_path / "local_embedded_supported_slice_gate.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/db_compat_local_embedded_supported_slice_gate.py",
            "--enable-ready-profile-projections",
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["maturity"] == "embedded_supported"
    assert payload["declared_executable_routes_runtime_ready"] is True
    assert payload["dense_sidecar_lifecycle_contract_version"] == "v1"
    assert payload["gate_ok"] is True

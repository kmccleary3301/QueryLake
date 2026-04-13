from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_db_compat_v2_program_completion_gate_emits_complete_payload(tmp_path: Path) -> None:
    output_path = tmp_path / "db_compat_v2_program_completion_gate.json"
    result = subprocess.run(
        [
            "uv",
            "run",
            "--no-project",
            "python",
            "scripts/db_compat_v2_program_completion_gate.py",
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
    assert payload["program_complete"] is True
    assert payload["program_id"] == "querylake_primitives_representation_v2"
    assert "sqlite_fts5_dense_sidecar_local_v1" in payload["validated_profiles"]
    assert payload["notes"]["wider_embedded_scope_required_for_completion"] is False

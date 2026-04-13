from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.db_compat_local_profile_scope_expansion_status import main


def test_local_profile_scope_expansion_status_reports_blocked_state(tmp_path):
    output_path = tmp_path / "local_profile_scope_expansion_status_blocked.json"
    assert main(["--output", str(output_path)]) == 0
    payload = output_path.read_text(encoding="utf-8")
    assert '"scope_expansion_status"' in payload
    assert '"scope_expansion_contract"' in payload
    assert '"current_supported_slice_frozen": true' in payload
    assert '"dense_sidecar_contract_version": "v1"' in payload
    assert '"pending_for_wider_scope"' in payload


def test_local_profile_scope_expansion_status_reports_ready_state(tmp_path):
    output_path = tmp_path / "local_profile_scope_expansion_status_ready.json"
    assert main(["--enable-ready-profile-projections", "--output", str(output_path)]) == 0
    payload = output_path.read_text(encoding="utf-8")
    assert '"scope_expansion_status"' in payload
    assert '"scope_expansion_contract"' in payload
    assert '"current_supported_slice_frozen": true' in payload
    assert '"dense_sidecar_promotion_contract_ready": true' in payload
    assert '"declared_executable_runtime_ready": true' in payload

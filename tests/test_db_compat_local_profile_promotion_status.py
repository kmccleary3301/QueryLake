from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.db_compat_local_profile_promotion_status import main


def test_local_profile_promotion_status_reports_blocked_slice(tmp_path):
    output_path = tmp_path / "local_profile_promotion_status_blocked.json"
    assert main(["--output", str(output_path)]) == 0
    payload = output_path.read_text(encoding="utf-8")
    assert '"local_profile"' in payload
    assert '"profile_promoted": true' in payload
    assert '"planning_v2_surfaced": true' in payload
    assert '"declared_executable_runtime_ready": false' in payload
    assert '"runtime_ready_local_slice"' in payload
    assert '"representation_scope_ids"' in payload
    assert '"required_projection_ids"' in payload
    assert '"projection_plan_v2_registry"' in payload
    assert '"projection_plan_v2_complete": true' in payload
    assert '"dense_sidecar_ready": false' in payload
    assert '"dense_sidecar_runtime_contract_ready": false' in payload
    assert '"dense_sidecar_promotion_contract_ready": false' in payload
    assert '"dense_sidecar_lifecycle_state": "blocked_projection_not_ready"' in payload
    assert '"dense_sidecar_runtime_blockers"' in payload
    assert '"dense_sidecar_promotion_blockers"' in payload
    assert '"route_runtime_contracts"' in payload
    assert '"query_smoke"' in payload
    assert '"all_passed": true' in payload


def test_local_profile_promotion_status_reports_ready_slice(tmp_path):
    output_path = tmp_path / "local_profile_promotion_status_ready.json"
    assert main(
        [
            "--enable-ready-profile-projections",
            "--output",
            str(output_path),
        ]
    ) == 0
    payload = output_path.read_text(encoding="utf-8")
    assert '"local_profile"' in payload
    assert '"profile_promoted": true' in payload
    assert '"planning_v2_surfaced": true' in payload
    assert '"declared_executable_runtime_ready": true' in payload
    assert '"ready_projection_count": 3' in payload
    assert '"projection_plan_v2_registry"' in payload
    assert '"projection_plan_v2_complete": true' in payload
    assert '"dense_sidecar_ready": true' in payload
    assert '"dense_sidecar_runtime_contract_ready": true' in payload
    assert '"dense_sidecar_promotion_contract_ready": true' in payload
    assert '"dense_sidecar_lifecycle_state": "ready_projection_backed_cache_cold"' in payload
    assert '"remaining_blockers": []' in payload
    assert '"query_smoke"' in payload
    assert '"all_passed": true' in payload

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.db_compat_local_profile_consistency_check import main


def test_local_profile_consistency_check_reports_blocked_slice(tmp_path):
    output_path = tmp_path / "local_profile_consistency_blocked.json"
    assert main(["--output", str(output_path)]) == 0
    payload = output_path.read_text(encoding="utf-8")
    assert '"consistency_ok": true' in payload
    assert '"sdk_parse_consistency_ok": true' in payload
    assert '"checked_surfaces"' in payload
    assert '"required_projection_ids"' in payload
    assert '"scope_expansion_contract"' in payload
    assert '"scope_expansion_status"' in payload
    assert '"query_smoke_passed": true' in payload
    assert '"route_fact_summary"' in payload
    assert '"dense_sidecar_lifecycle_contract_version": "v1"' in payload


def test_local_profile_consistency_check_reports_ready_slice(tmp_path):
    output_path = tmp_path / "local_profile_consistency_ready.json"
    assert main(
        [
            "--enable-ready-profile-projections",
            "--output",
            str(output_path),
        ]
    ) == 0
    payload = output_path.read_text(encoding="utf-8")
    assert '"consistency_ok": true' in payload
    assert '"sdk_parse_consistency_ok": true' in payload
    assert '"dense_sidecar_ready": true' in payload
    assert '"dense_sidecar_contract_version": "v1"' in payload
    assert '"dense_sidecar_lifecycle_contract_version": "v1"' in payload
    assert '"query_smoke_passed": true' in payload
    assert '"bm25_phrase_degraded"' in payload

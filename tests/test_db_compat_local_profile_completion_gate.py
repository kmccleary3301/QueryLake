from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.db_compat_local_profile_completion_gate import main


def test_local_profile_completion_gate_reports_missing_projection_state(tmp_path):
    output_path = tmp_path / "local_profile_completion_gate_missing.json"
    args = [
        "--profile",
        "sqlite_fts5_dense_sidecar_local_v1",
        "--expect-profile-implemented",
        "true",
        "--expect-boot-ready",
        "false",
        "--expect-configuration-ready",
        "true",
        "--expect-route-runtime-ready",
        "false",
        "--expect-declared-executable-routes-runtime-ready",
        "false",
        "--expect-ready-projection-count",
        "0",
        "--expect-declared-executable-route-ids",
        "search_bm25.document_chunk,search_file_chunks,search_hybrid.document_chunk",
        "--expect-lexical-degraded-route-ids",
        "search_bm25.document_chunk,search_file_chunks,search_hybrid.document_chunk",
        "--expect-lexical-gold-recommended-route-ids",
        "search_bm25.document_chunk,search_file_chunks,search_hybrid.document_chunk",
        "--expect-query-smoke-passed",
        "true",
        "--output",
        str(output_path),
    ]
    assert main(args) == 0
    payload = output_path.read_text(encoding="utf-8")
    assert '"boot_ready": false' in payload
    assert '"declared_executable_routes_runtime_ready": false' in payload
    assert '"planning_v2"' in payload
    assert '"local_profile"' in payload
    assert '"promotion_status"' in payload
    assert '"projection_plan_v2_registry"' in payload
    assert '"dense_sidecar_ready": false' in payload
    assert '"dense_sidecar_runtime_contract_ready": false' in payload
    assert '"dense_sidecar_promotion_contract_ready": false' in payload
    assert '"query_smoke"' in payload


def test_local_profile_completion_gate_reports_ready_local_slice(tmp_path):
    output_path = tmp_path / "local_profile_completion_gate_ready.json"
    args = [
        "--profile",
        "sqlite_fts5_dense_sidecar_local_v1",
        "--enable-ready-profile-projections",
        "--expect-profile-implemented",
        "true",
        "--expect-boot-ready",
        "true",
        "--expect-configuration-ready",
        "true",
        "--expect-route-runtime-ready",
        "true",
        "--expect-declared-executable-routes-runtime-ready",
        "true",
        "--expect-ready-projection-count",
        "3",
        "--expect-declared-executable-route-ids",
        "search_bm25.document_chunk,search_file_chunks,search_hybrid.document_chunk",
        "--expect-lexical-degraded-route-ids",
        "search_bm25.document_chunk,search_file_chunks,search_hybrid.document_chunk",
        "--expect-lexical-gold-recommended-route-ids",
        "search_bm25.document_chunk,search_file_chunks,search_hybrid.document_chunk",
        "--expect-query-smoke-passed",
        "true",
        "--output",
        str(output_path),
    ]
    assert main(args) == 0
    payload = output_path.read_text(encoding="utf-8")
    assert '"route_runtime_ready": true' in payload
    assert '"declared_executable_routes_runtime_ready": true' in payload
    assert '"planning_v2"' in payload
    assert '"local_profile"' in payload
    assert '"promotion_status"' in payload
    assert '"projection_plan_v2_registry"' in payload
    assert '"dense_sidecar_ready": true' in payload
    assert '"dense_sidecar_runtime_contract_ready": true' in payload
    assert '"dense_sidecar_promotion_contract_ready": true' in payload
    assert '"query_smoke"' in payload

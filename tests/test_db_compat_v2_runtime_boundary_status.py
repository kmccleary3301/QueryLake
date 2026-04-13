from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.db_compat_v2_runtime_boundary_status import build_v2_runtime_boundary_payload


def test_v2_runtime_boundary_payload_tracks_active_profiles_and_routes():
    payload = build_v2_runtime_boundary_payload()

    assert payload["contract_version"] == "v1"
    assert [row["profile_id"] for row in payload["active_profiles"]] == [
        "paradedb_postgres_gold_v1",
        "aws_aurora_pg_opensearch_v1",
        "sqlite_fts5_dense_sidecar_local_v1",
    ]
    assert payload["active_route_ids"] == [
        "search_bm25.document_chunk",
        "search_hybrid.document_chunk",
        "search_file_chunks",
    ]
    assert "QueryLake/runtime/route_planning_v2.py" in payload["canonical_runtime_surfaces"]
    assert "representation_scope_id" in payload["canonical_planning_fields"]
    assert "compatibility_era_storage_internals_behind_typed_materialization_helpers" in payload["transitional_areas"]

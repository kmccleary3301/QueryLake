from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.db_compat_v2_runtime_consistency import build_v2_runtime_consistency_payload


def test_v2_runtime_consistency_payload_validates_all_supported_slices(tmp_path):
    payload = build_v2_runtime_consistency_payload(
        metadata_store_path=str(tmp_path / "db_compat_v2_runtime_consistency_meta.json"),
    )

    assert payload["validated_profile_count"] == 3
    assert sorted(payload["validated_routes"]) == [
        "search_bm25.document_chunk",
        "search_file_chunks",
        "search_hybrid.document_chunk",
    ]

    rows = {row["profile_id"]: row for row in payload["profiles"]}
    assert rows["paradedb_postgres_gold_v1"]["route_runtime_ready"] is True
    assert rows["aws_aurora_pg_opensearch_v1"]["declared_executable_routes_runtime_ready"] is True
    assert rows["sqlite_fts5_dense_sidecar_local_v1"]["declared_executable_routes_runtime_ready"] is True

    local_lexical = {
        row["route_id"]: row["lexical_support_class"]
        for row in rows["sqlite_fts5_dense_sidecar_local_v1"]["routes"]
    }
    assert local_lexical == {
        "search_bm25.document_chunk": "degraded_supported",
        "search_hybrid.document_chunk": "degraded_supported",
        "search_file_chunks": "degraded_supported",
    }
    for profile_row in rows.values():
        for route_row in profile_row["routes"]:
            assert route_row["planning_surface"] == "route_resolution"
            assert route_row["projection_buildability_class"] != ""
            assert route_row["strictness_policy"] != ""
            assert route_row["orchestrated_metadata_consistent"] is True
            assert route_row["orchestrated_trace_count"] >= 2

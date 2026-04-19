from QueryLake.canon.runtime import build_phase1a_route_profile_matrix


def test_phase1a_route_profile_matrix_covers_bounded_routes_and_profiles():
    payload = build_phase1a_route_profile_matrix(
        routes=["search_bm25.document_chunk", "search_file_chunks"],
        profile_ids=["paradedb_postgres_gold_v1", "planetscale_opensearch_v1"],
    )

    assert payload["schema_version"] == "canon_phase1a_route_profile_matrix_v1"
    assert len(payload["rows"]) == 4
    assert "planned_profiles_should_remain_shadow_only" in payload["recommendations"]
    assert all(row["compile"]["available"] is True for row in payload["rows"])
    assert any(
        row["profile_id"] == "planetscale_opensearch_v1" and row["lowering"]["support_state"] == "planned"
        for row in payload["rows"]
    )

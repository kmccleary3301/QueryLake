import json

from QueryLake.canon.runtime import build_shadow_report_index, load_shadow_reports, persist_shadow_report_index


def test_shadow_report_index_builds_recommendations():
    payload = build_shadow_report_index(
        [
            {
                "schema_version": "canon_shadow_report_v1",
                "report_id": "r1",
                "route": "search_bm25.document_chunk",
                "shadow_diff": {"divergence_class": "exact_match"},
            },
            {
                "schema_version": "canon_shadow_report_v1",
                "report_id": "r2",
                "route": "search_file_chunks",
                "shadow_diff": {"divergence_class": "ordering_delta_only"},
            },
        ]
    )

    assert payload["report_count"] == 2
    assert payload["divergence_counts"]["exact_match"] == 1
    assert "safe_to_expand_shadow_coverage" in payload["recommendations"]


def test_shadow_report_index_can_load_and_persist(tmp_path):
    report_path = tmp_path / "sample-report.json"
    report_path.write_text(
        json.dumps(
            {
                "schema_version": "canon_shadow_report_v1",
                "report_id": "r1",
                "route": "search_bm25.document_chunk",
                "shadow_diff": {"divergence_class": "exact_match"},
            }
        ),
        encoding="utf-8",
    )
    loaded = load_shadow_reports(tmp_path)
    output = persist_shadow_report_index(
        index_payload=build_shadow_report_index(loaded),
        output_path=tmp_path / "shadow-index.json",
    )

    assert len(loaded) == 1
    assert json.loads((tmp_path / "shadow-index.json").read_text(encoding="utf-8"))["report_count"] == 1
    assert output.endswith("shadow-index.json")

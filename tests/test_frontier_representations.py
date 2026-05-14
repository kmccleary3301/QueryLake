from QueryLake.runtime.frontier_representations import (
    build_late_chunk_trace,
    build_multivector_span_plan,
    build_semantic_segment_plan,
    build_table_native_plan,
    build_visual_region_plan,
    materialize_frontier_representation_rows,
)


def test_semantic_segment_plan_groups_source_segments_with_traceability():
    plan = build_semantic_segment_plan([
        {"id": "s1", "text": "Alpha boiler pressure."},
        {"id": "s2", "text": "Limits and safety valves."},
    ], max_chars=100)
    assert plan.lane == "semantic_segment_text"
    assert plan.segments[0]["source_segment_ids"] == ["s1", "s2"]


def test_late_chunk_trace_selects_query_relevant_segments():
    trace = build_late_chunk_trace([
        {"id": "s1", "text": "Alpha boiler pressure."},
        {"id": "s2", "text": "Unrelated."},
    ], query="boiler pressure")
    assert trace["lane"] == "late_chunk_query_embedding"
    assert trace["traceable"] is True
    assert trace["chunks"][0]["source_segment_id"] == "s1"


def test_multivector_span_plan_preserves_source_segment_ids():
    plan = build_multivector_span_plan([{"id": "s1", "text": "a" * 300}], span_chars=100)
    assert len(plan.segments) == 3
    assert all(row["source_segment_ids"] == ["s1"] for row in plan.segments)


def test_table_native_plan_extracts_markdown_rows():
    plan = build_table_native_plan("| A | B |\n| --- | --- |\n| 1 | 2 |")
    assert plan.lane == "table_cell_or_row_text"
    assert [row["cells"] for row in plan.segments] == [["A", "B"], ["1", "2"]]


def test_visual_region_plan_uses_scanner_unit_geometry():
    plan = build_visual_region_plan([
        {"unit_index": 0, "text": "Report", "anchor_payload": {"page": 1, "bbox": [0, 0, 100, 20]}},
        {"unit_index": 1, "text": "No box", "anchor_payload": {"page": 1}},
    ])
    assert plan.segments[0]["segment_type"] == "visual_region"
    assert plan.segments[0]["bbox"] == [0, 0, 100, 20]


def test_materialize_frontier_representation_rows_builds_view_segments_and_members():
    plan = build_semantic_segment_plan([{"id": "s1", "text": "Alpha"}])
    rows = materialize_frontier_representation_rows(document_version_id="dv1", artifact_id="art1", plan=plan)

    assert rows["unit_view"].unit_kind == "semantic_segment_text_unit"
    assert rows["segment_view"].view_alias == "semantic_text"
    assert rows["segments"][0].segment_type == "semantic"
    assert rows["segments"][0].md["source_segment_ids"] == ["s1"]
    assert rows["members"][0].segment_id == rows["segments"][0].id
    assert rows["members"][0].unit_id == rows["units"][0].id

from QueryLake.runtime.query_ir_v2 import (
    FilterIRV2,
    QueryIRV2,
    QueryStrictnessPolicy,
    instantiate_query_ir_v2,
)


def test_query_ir_v2_requested_lanes_honors_dense_sparse_and_text():
    ir = QueryIRV2(
        raw_query_text="vapor recovery",
        normalized_query_text="vapor recovery",
        lexical_query_text="vapor recovery",
        use_dense=True,
        use_sparse=False,
        representation_scope_id="document_segment",
        route_id="search_hybrid.segment",
    )
    assert ir.requested_lanes() == ["lexical", "dense"]


def test_query_ir_v2_can_represent_dense_only_request():
    ir = QueryIRV2(
        raw_query_text="",
        normalized_query_text="",
        lexical_query_text=None,
        use_dense=True,
        use_sparse=False,
        strictness_policy=QueryStrictnessPolicy.approximate,
        filter_ir=FilterIRV2(collection_ids=["c1"]),
        representation_scope_id="document_segment",
        route_id="search_hybrid.segment",
    )
    assert ir.requested_lanes() == ["dense"]
    assert ir.filter_ir.collection_ids == ["c1"]


def test_instantiate_query_ir_v2_merges_template_and_runtime_request_fields():
    template = QueryIRV2(
        raw_query_text="",
        normalized_query_text="",
        lexical_query_text="",
        use_dense=False,
        use_sparse=False,
        representation_scope_id="document_chunk",
        route_id="search_bm25.document_chunk",
        planner_hints={"planning_surface": "route_resolution"},
        metadata={"route_family": "search_bm25"},
    )

    ir = instantiate_query_ir_v2(
        template,
        raw_query_text='\"vapor recovery\"',
        lexical_query_text='\"vapor recovery\"',
        collection_ids=["c1", "c2"],
        planner_hints={"table": "document_chunk"},
        metadata={"table": "document_chunk"},
    )

    assert ir.route_id == "search_bm25.document_chunk"
    assert ir.representation_scope_id == "document_chunk"
    assert ir.raw_query_text == '"vapor recovery"'
    assert ir.normalized_query_text == '"vapor recovery"'
    assert ir.lexical_query_text == '"vapor recovery"'
    assert ir.filter_ir.collection_ids == ["c1", "c2"]
    assert ir.planner_hints["planning_surface"] == "route_resolution"
    assert ir.planner_hints["table"] == "document_chunk"
    assert ir.metadata["route_family"] == "search_bm25"
    assert ir.metadata["table"] == "document_chunk"

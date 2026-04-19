from QueryLake.canon.compiler import QueryLakeRouteCompileError, compile_querylake_route_to_graph


def test_compile_querylake_hybrid_route_uses_default_pipeline_mapping():
    graph = compile_querylake_route_to_graph(route="search_hybrid.document_chunk")

    assert graph.graph_name.startswith("canon.retrieval.search_hybrid.document_chunk")
    assert [node.node_id for node in graph.nodes] == [
        "stage.bm25",
        "stage.dense",
        "stage.sparse",
        "fusion",
    ]


def test_compile_querylake_bm25_route_uses_default_pipeline_mapping():
    graph = compile_querylake_route_to_graph(route="search_bm25.document_chunk")

    assert [node.node_id for node in graph.nodes] == ["stage.bm25"]
    assert graph.requested_outputs[0].key == "stage.bm25.candidates"


def test_compile_querylake_route_rejects_unknown_route_without_default_pipeline():
    try:
        compile_querylake_route_to_graph(route="search_graph.document_chunk")
        assert False, "expected unknown route compilation to fail"
    except QueryLakeRouteCompileError as exc:
        assert exc.route == "search_graph.document_chunk"
        assert "no default retrieval pipeline" in str(exc)

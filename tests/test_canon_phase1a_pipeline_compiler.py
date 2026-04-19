from QueryLake.canon.compiler import (
    RetrievalPipelineCompileError,
    compile_retrieval_pipeline_to_graph,
)
from QueryLake.canon.compiler.querylake_route_compiler import normalize_querylake_route_pipeline
from QueryLake.runtime.retrieval_pipeline_runtime import default_pipeline_for_route
from QueryLake.typing.retrieval_primitives import RetrievalPipelineSpec, RetrievalPipelineStage


def test_compile_bm25_default_pipeline_to_graph():
    pipeline = default_pipeline_for_route("search_bm25.document_chunk")
    assert pipeline is not None

    graph = compile_retrieval_pipeline_to_graph(
        route="search_bm25.document_chunk",
        pipeline=pipeline,
    )

    assert graph.graph_name.startswith("canon.retrieval.search_bm25.document_chunk")
    assert [node.node_id for node in graph.nodes] == ["stage.bm25"]
    assert graph.requested_outputs[0].key == "stage.bm25.candidates"
    assert graph.nodes[0].config["primitive_id"] == "BM25RetrieverParadeDB"


def test_compile_hybrid_default_pipeline_to_graph_includes_fusion():
    pipeline = default_pipeline_for_route("search_hybrid")
    assert pipeline is not None

    graph = compile_retrieval_pipeline_to_graph(
        route="search_hybrid.document_chunk",
        pipeline=pipeline,
    )

    assert [node.node_id for node in graph.nodes] == [
        "stage.bm25",
        "stage.dense",
        "stage.sparse",
        "fusion",
    ]
    assert graph.requested_outputs[0].key == "fusion.candidates"
    assert graph.nodes[-1].operation == "fusion_stage"


def test_compile_pipeline_can_add_rerank_stage_from_options():
    pipeline = default_pipeline_for_route("search_hybrid")
    assert pipeline is not None

    graph = compile_retrieval_pipeline_to_graph(
        route="search_hybrid.document_chunk",
        pipeline=pipeline,
        options={"rerank_enabled": True, "reranker_primitive": "CrossEncoderReranker"},
    )

    assert graph.nodes[-1].node_id == "rerank"
    assert graph.requested_outputs[0].key == "rerank.candidates"


def test_compile_hybrid_pipeline_can_disable_sparse_stage_from_options():
    pipeline = default_pipeline_for_route("search_hybrid")
    assert pipeline is not None

    graph = compile_retrieval_pipeline_to_graph(
        route="search_hybrid.document_chunk",
        pipeline=normalize_querylake_route_pipeline(
            route="search_hybrid.document_chunk",
            pipeline=pipeline,
            options={"disable_sparse": True},
        ),
    )

    assert [node.node_id for node in graph.nodes] == [
        "stage.bm25",
        "stage.dense",
        "fusion",
    ]


def test_compile_pipeline_rejects_empty_enabled_stage_set():
    pipeline = RetrievalPipelineSpec(
        pipeline_id="empty.pipeline",
        version="v1",
        stages=[RetrievalPipelineStage(stage_id="bm25", primitive_id="BM25RetrieverParadeDB", enabled=False)],
    )

    try:
        compile_retrieval_pipeline_to_graph(route="search_bm25.document_chunk", pipeline=pipeline)
        assert False, "expected empty-stage pipeline to fail"
    except RetrievalPipelineCompileError as exc:
        assert exc.route == "search_bm25.document_chunk"
        assert exc.pipeline_id == "empty.pipeline"

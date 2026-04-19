import asyncio

from QueryLake.canon.runtime import build_querylake_shadow_diff, execute_querylake_pipeline_in_canon_shadow
from QueryLake.runtime.retrieval_primitives_legacy import WeightedScoreFusion
from QueryLake.typing.retrieval_primitives import (
    RetrievalCandidate,
    RetrievalPipelineSpec,
    RetrievalPipelineStage,
    RetrievalRequest,
)


class _DummyRetriever:
    def __init__(self, primitive_id: str, rows):
        self.primitive_id = primitive_id
        self.version = "v1"
        self._rows = rows

    async def retrieve(self, request):
        return list(self._rows)


def test_execute_querylake_pipeline_in_canon_shadow_runs_hybrid_graph():
    pipeline = RetrievalPipelineSpec(
        pipeline_id="orchestrated.search_hybrid",
        version="v1",
        stages=[
            RetrievalPipelineStage(stage_id="bm25", primitive_id="BM25RetrieverParadeDB"),
            RetrievalPipelineStage(stage_id="dense", primitive_id="DenseRetrieverPGVector"),
        ],
        flags={"fusion_primitive": "WeightedScoreFusion"},
    )
    request = RetrievalRequest(
        route="search_hybrid.document_chunk",
        query_text="q",
        options={"limit": 10},
        query_ir_v2={"route_id": "search_hybrid.document_chunk"},
    )
    result = asyncio.run(
        execute_querylake_pipeline_in_canon_shadow(
            request=request,
            pipeline=pipeline,
            retrievers={
                "bm25": _DummyRetriever("BM25RetrieverParadeDB", [RetrievalCandidate(content_id="a")]),
                "dense": _DummyRetriever("DenseRetrieverPGVector", [RetrievalCandidate(content_id="b")]),
            },
            fusion=WeightedScoreFusion(),
            reranker=None,
        )
    )

    assert result.pipeline_id == "orchestrated.search_hybrid"
    assert "canon_bridge" in result.metadata
    assert result.metadata["canon_bridge"]["available"] is True
    assert any(trace.stage == "canon_shadow_execute" for trace in result.traces)
    assert len(result.candidates) == 2


def test_build_querylake_shadow_diff_detects_exact_match():
    request = RetrievalRequest(route="search_bm25.document_chunk", query_text="q", options={"limit": 2}, query_ir_v2={"route_id": "search_bm25.document_chunk"})
    pipeline = RetrievalPipelineSpec(
        pipeline_id="orchestrated.search_bm25.document_chunk",
        version="v1",
        stages=[RetrievalPipelineStage(stage_id="bm25", primitive_id="BM25RetrieverParadeDB")],
    )
    legacy = type("R", (), {"candidates": [RetrievalCandidate(content_id="a"), RetrievalCandidate(content_id="b")]})()
    canon = type("R", (), {"candidates": [RetrievalCandidate(content_id="a"), RetrievalCandidate(content_id="b")], "metadata": {"canon_graph_id": "graph-123"}})()

    payload = build_querylake_shadow_diff(
        request=request,
        pipeline=pipeline,
        profile_id="paradedb_postgres_gold_v1",
        legacy_result=legacy,
        canon_result=canon,
    )

    assert payload["divergence_class"] == "exact_match"
    assert payload["canon_graph_id"] == "graph-123"

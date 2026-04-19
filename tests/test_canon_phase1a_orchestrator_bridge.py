import asyncio

from QueryLake.runtime.retrieval_orchestrator import PipelineOrchestrator
from QueryLake.typing.retrieval_primitives import (
    RetrievalCandidate,
    RetrievalPipelineSpec,
    RetrievalPipelineStage,
    RetrievalRequest,
)


class _DummyRetriever:
    def __init__(self, rows):
        self.primitive_id = "BM25"
        self.version = "v1"
        self._rows = rows

    async def retrieve(self, request):
        return self._rows


def test_orchestrator_emits_canon_bridge_metadata_for_explain_runs():
    pipeline = RetrievalPipelineSpec(
        pipeline_id="orchestrated.search_bm25.document_chunk",
        version="v1",
        stages=[RetrievalPipelineStage(stage_id="bm25", primitive_id="BM25RetrieverParadeDB")],
    )
    request = RetrievalRequest(
        route="search_bm25.document_chunk",
        query_text="boiler pressure",
        options={"explain_plan": True, "limit": 5},
        query_ir_v2={"route_id": "search_bm25.document_chunk"},
    )

    result = asyncio.run(
        PipelineOrchestrator().run(
            request=request,
            pipeline=pipeline,
            retrievers={
                "bm25": _DummyRetriever(
                    [
                        RetrievalCandidate(
                            content_id="c1",
                            text="row",
                            metadata={"collection_id": "col1"},
                        )
                    ]
                )
            },
        )
    )

    assert "canon_bridge" in result.metadata
    assert result.metadata["canon_bridge"]["available"] is True
    assert result.metadata["canon_bridge"]["graph_name"].startswith("canon.retrieval.search_bm25.document_chunk")
    trace_map = {trace.stage: trace for trace in result.traces}
    assert "canon_bridge_compile" in trace_map
    assert trace_map["canon_bridge_compile"].details["graph_id"] == result.metadata["canon_bridge"]["graph_id"]

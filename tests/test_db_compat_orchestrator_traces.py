from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from QueryLake.runtime.retrieval_orchestrator import PipelineOrchestrator
from QueryLake.typing.retrieval_primitives import (
    RetrievalCandidate,
    RetrievalPipelineSpec,
    RetrievalPipelineStage,
    RetrievalRequest,
)


class DummyRetriever:
    primitive_id = "BM25RetrieverParadeDB"
    version = "v1"

    async def retrieve(self, request: RetrievalRequest):
        return [
            RetrievalCandidate(
                content_id="doc-1",
                text="hello",
                metadata={"collection_id": "c1"},
                stage_scores={"bm25_score": 1.0},
            )
        ]


@pytest.mark.asyncio
async def test_orchestrator_trace_includes_adapter_metadata(monkeypatch):
    monkeypatch.delenv("QUERYLAKE_DB_PROFILE", raising=False)
    pipeline = RetrievalPipelineSpec(
        pipeline_id="p",
        version="v1",
        stages=[RetrievalPipelineStage(stage_id="bm25", primitive_id="BM25RetrieverParadeDB")],
    )
    result = await PipelineOrchestrator().run(
        RetrievalRequest(
            route="search_bm25.document_chunk",
            query_text="hello",
            collection_ids=["c1"],
        ),
        pipeline,
        retrievers={"bm25": DummyRetriever()},
        fusion=None,
        reranker=None,
        packer=None,
    )
    trace = next(trace for trace in result.traces if trace.stage == "retrieve:bm25")
    assert trace.details["primitive_id"] == "BM25RetrieverParadeDB"
    assert trace.details["adapter"]["adapter_id"] == "paradedb_bm25_v1"
    assert trace.details["adapter"]["lane_family"] == "lexical_bm25"

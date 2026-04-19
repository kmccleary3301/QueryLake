import asyncio
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.retrieval_orchestrator import PipelineOrchestrator
from QueryLake.typing.retrieval_primitives import (
    RetrievalCandidate,
    RetrievalPipelineSpec,
    RetrievalPipelineStage,
    RetrievalRequest,
)
from QueryLake.runtime.retrieval_primitives_legacy import RRFusion


class _DummyRetriever:
    def __init__(self, primitive_id: str, rows):
        self.primitive_id = primitive_id
        self.version = "v1"
        self._rows = rows

    async def retrieve(self, request: RetrievalRequest):
        return self._rows


class _DummyReranker:
    primitive_id = "DummyReranker"
    version = "v1"

    async def rerank(self, request: RetrievalRequest, candidates):
        return sorted(candidates, key=lambda c: c.content_id, reverse=True)


class _CaptureReranker:
    primitive_id = "CaptureReranker"
    version = "v1"

    def __init__(self):
        self.seen_ids = []

    async def rerank(self, request: RetrievalRequest, candidates):
        self.seen_ids = [candidate.content_id for candidate in candidates]
        return candidates


def test_pipeline_orchestrator_runs_retrieve_fuse_rerank():
    req = RetrievalRequest(query_text="q", options={"limit": 3})
    pipeline = RetrievalPipelineSpec(
        pipeline_id="p1",
        version="v1",
        stages=[
            RetrievalPipelineStage(stage_id="bm25", primitive_id="BM25"),
            RetrievalPipelineStage(stage_id="dense", primitive_id="Dense"),
        ],
    )
    bm25_rows = [
        RetrievalCandidate(content_id="a", text="A", provenance=["bm25"], stage_ranks={"bm25": 1}),
        RetrievalCandidate(content_id="b", text="B", provenance=["bm25"], stage_ranks={"bm25": 2}),
    ]
    dense_rows = [
        RetrievalCandidate(content_id="b", text="B", provenance=["dense"], stage_ranks={"dense": 1}),
        RetrievalCandidate(content_id="c", text="C", provenance=["dense"], stage_ranks={"dense": 2}),
    ]

    orchestrator = PipelineOrchestrator()
    result = asyncio.run(
        orchestrator.run(
            request=req,
            pipeline=pipeline,
            retrievers={
                "bm25": _DummyRetriever("BM25", bm25_rows),
                "dense": _DummyRetriever("Dense", dense_rows),
            },
            fusion=RRFusion(),
            reranker=_DummyReranker(),
        )
    )

    assert result.pipeline_id == "p1"
    assert len(result.candidates) == 3
    assert len(result.traces) >= 3
    assert any(trace.stage.startswith("retrieve:") for trace in result.traces)


def test_pipeline_orchestrator_applies_acl_filter_before_rerank():
    req = RetrievalRequest(query_text="q", collection_ids=["allowed"], options={"limit": 10})
    pipeline = RetrievalPipelineSpec(
        pipeline_id="p_acl",
        version="v1",
        stages=[
            RetrievalPipelineStage(stage_id="bm25", primitive_id="BM25"),
            RetrievalPipelineStage(stage_id="dense", primitive_id="Dense"),
        ],
    )
    bm25_rows = [
        RetrievalCandidate(content_id="a", text="A", metadata={"collection_id": "allowed"}, provenance=["bm25"]),
        RetrievalCandidate(content_id="b", text="B", metadata={"collection_id": "denied"}, provenance=["bm25"]),
    ]
    dense_rows = [
        RetrievalCandidate(content_id="c", text="C", metadata={"collection_id": "denied"}, provenance=["dense"]),
    ]
    reranker = _CaptureReranker()

    orchestrator = PipelineOrchestrator()
    result = asyncio.run(
        orchestrator.run(
            request=req,
            pipeline=pipeline,
            retrievers={
                "bm25": _DummyRetriever("BM25", bm25_rows),
                "dense": _DummyRetriever("Dense", dense_rows),
            },
            fusion=RRFusion(),
            reranker=reranker,
        )
    )

    assert reranker.seen_ids == ["a"]
    assert [row.content_id for row in result.candidates] == ["a"]
    assert any(trace.stage.startswith("acl:") for trace in result.traces)


def test_pipeline_orchestrator_emits_policy_preflight_trace():
    req = RetrievalRequest(query_text="q", options={"limit": 2})
    pipeline = RetrievalPipelineSpec(
        pipeline_id="p_preflight",
        version="v1",
        stages=[RetrievalPipelineStage(stage_id="bm25", primitive_id="BM25")],
    )
    orchestrator = PipelineOrchestrator()
    result = asyncio.run(
        orchestrator.run(
            request=req,
            pipeline=pipeline,
            retrievers={"bm25": _DummyRetriever("BM25", [])},
            fusion=RRFusion(),
        )
    )
    preflight = [trace for trace in result.traces if trace.stage == "policy_preflight"]
    assert len(preflight) == 1
    assert preflight[0].details["valid"] is True


def test_pipeline_orchestrator_policy_preflight_can_fail_fast():
    req = RetrievalRequest(
        query_text="q",
        options={"limit": -1, "enforce_policy_validation": True},
    )
    pipeline = RetrievalPipelineSpec(
        pipeline_id="p_preflight_fail",
        version="v1",
        stages=[RetrievalPipelineStage(stage_id="bm25", primitive_id="BM25")],
    )
    orchestrator = PipelineOrchestrator()
    try:
        asyncio.run(
            orchestrator.run(
                request=req,
                pipeline=pipeline,
                retrievers={"bm25": _DummyRetriever("BM25", [])},
            )
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "limit_negative" in str(exc)


def test_pipeline_orchestrator_can_emit_canon_shadow_execution_metadata():
    req = RetrievalRequest(
        query_text="q",
        options={"limit": 3, "canon_shadow_execute": True},
        query_ir_v2={"route_id": "search_hybrid.document_chunk"},
    )
    pipeline = RetrievalPipelineSpec(
        pipeline_id="orchestrated.search_hybrid",
        version="v1",
        stages=[
            RetrievalPipelineStage(stage_id="bm25", primitive_id="BM25RetrieverParadeDB"),
            RetrievalPipelineStage(stage_id="dense", primitive_id="DenseRetrieverPGVector"),
        ],
        flags={"fusion_primitive": "WeightedScoreFusion"},
    )
    bm25_rows = [RetrievalCandidate(content_id="a", text="A", provenance=["bm25"], stage_ranks={"bm25": 1})]
    dense_rows = [RetrievalCandidate(content_id="b", text="B", provenance=["dense"], stage_ranks={"dense": 1})]

    orchestrator = PipelineOrchestrator()
    result = asyncio.run(
        orchestrator.run(
            request=req,
            pipeline=pipeline,
            retrievers={
                "bm25": _DummyRetriever("BM25RetrieverParadeDB", bm25_rows),
                "dense": _DummyRetriever("DenseRetrieverPGVector", dense_rows),
            },
            fusion=RRFusion(),
        )
    )

    assert "canon_shadow" in result.metadata
    assert result.metadata["canon_shadow"]["bridge"]["available"] is True
    assert result.metadata["canon_shadow"]["shadow_diff"]["divergence_class"] in {"exact_match", "ordering_delta_only", "candidate_set_delta"}
    assert any(trace.stage == "canon_shadow_execute" for trace in result.traces)


def test_pipeline_orchestrator_can_emit_file_chunk_shadow_metadata_and_persist_report(tmp_path):
    req = RetrievalRequest(
        route="search_file_chunks",
        query_text="q",
        options={
            "limit": 3,
            "canon_shadow_execute": True,
            "canon_shadow_report_dir": str(tmp_path),
            "canon_shadow_report_id": "file-chunk-shadow",
            "canon_shadow_bundle_dir": str(tmp_path),
            "canon_shadow_bundle_id": "file-chunk-shadow-bundle",
        },
        query_ir_v2={"route_id": "search_file_chunks"},
    )
    pipeline = RetrievalPipelineSpec(
        pipeline_id="orchestrated.search_file_chunks",
        version="v1",
        stages=[
            RetrievalPipelineStage(stage_id="file_bm25", primitive_id="BM25RetrieverParadeDB"),
        ],
    )
    rows = [RetrievalCandidate(content_id="chunk_d3", text="D3", provenance=["file_bm25"], stage_ranks={"file_bm25": 1})]

    orchestrator = PipelineOrchestrator()
    result = asyncio.run(
        orchestrator.run(
            request=req,
            pipeline=pipeline,
            retrievers={
                "file_bm25": _DummyRetriever("BM25RetrieverParadeDB", rows),
            },
        )
    )

    assert result.metadata["canon_shadow"]["bridge"]["available"] is True
    assert result.metadata["canon_shadow"]["shadow_diff"]["divergence_class"] == "exact_match"
    persisted = result.metadata["canon_shadow"]["report"]
    assert persisted["report_id"] == "file-chunk-shadow"
    assert (tmp_path / "file-chunk-shadow.json").exists() is True
    assert result.metadata["canon_shadow"]["replay_bundle"]["bundle_id"] == "file-chunk-shadow-bundle"
    assert (tmp_path / "file-chunk-shadow-bundle.json").exists() is True
    assert result.metadata["canon_shadow"]["trace_export"]["export_id"] == "file-chunk-shadow-bundle-traces"
    assert (tmp_path / "file-chunk-shadow-bundle-traces.json").exists() is True

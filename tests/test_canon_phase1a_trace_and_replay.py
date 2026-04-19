import json

from QueryLake.canon.runtime import (
    build_shadow_replay_bundle,
    build_shadow_trace_export,
    persist_shadow_replay_bundle,
    persist_shadow_trace_export,
)
from QueryLake.typing.retrieval_primitives import RetrievalCandidate, RetrievalExecutionResult, RetrievalPipelineSpec, RetrievalPipelineStage, RetrievalRequest, RetrievalStageTrace


def test_shadow_trace_export_contains_stage_payloads():
    request = RetrievalRequest(route="search_bm25.document_chunk", query_text="q", query_ir_v2={"route_id": "search_bm25.document_chunk"})
    pipeline = RetrievalPipelineSpec(
        pipeline_id="orchestrated.search_bm25.document_chunk",
        version="v1",
        stages=[RetrievalPipelineStage(stage_id="bm25", primitive_id="BM25RetrieverParadeDB")],
    )
    canon_result = RetrievalExecutionResult(
        pipeline_id="canon",
        pipeline_version="v1",
        candidates=[RetrievalCandidate(content_id="a")],
        traces=[RetrievalStageTrace(stage="canon:stage.bm25", duration_ms=1.5, output_count=1, details={"effect_class": "ExternalReadOnly"})],
        metadata={"canon_graph_id": "graph-123"},
    )

    payload = build_shadow_trace_export(
        export_id="trace-1",
        request=request,
        pipeline=pipeline,
        canon_result=canon_result,
    )

    assert payload["export_id"] == "trace-1"
    assert payload["graph_id"] == "graph-123"
    assert payload["trace_count"] == 1
    assert payload["spans"][0]["name"] == "canon:stage.bm25"


def test_shadow_replay_bundle_builds_and_persists(tmp_path):
    request = RetrievalRequest(route="search_file_chunks", query_text="flue gas", query_ir_v2={"route_id": "search_file_chunks"})
    pipeline = RetrievalPipelineSpec(
        pipeline_id="orchestrated.search_file_chunks",
        version="v1",
        stages=[RetrievalPipelineStage(stage_id="file_bm25", primitive_id="FileChunkBM25RetrieverSQL")],
    )
    legacy_result = RetrievalExecutionResult(
        pipeline_id="legacy",
        pipeline_version="v1",
        candidates=[RetrievalCandidate(content_id="chunk_d3")],
    )
    canon_result = RetrievalExecutionResult(
        pipeline_id="canon",
        pipeline_version="v1",
        candidates=[RetrievalCandidate(content_id="chunk_d3")],
        metadata={"canon_graph_id": "graph-999", "canon_bridge": {"available": True}},
    )

    bundle = build_shadow_replay_bundle(
        bundle_id="bundle-1",
        request=request,
        pipeline=pipeline,
        legacy_result=legacy_result,
        canon_result=canon_result,
        shadow_diff={"divergence_class": "exact_match"},
    )
    persisted = persist_shadow_replay_bundle(bundle=bundle, output_dir=tmp_path)
    bundle_path = tmp_path / "bundle-1.json"

    assert persisted["path"] == str(bundle_path)
    assert bundle_path.exists() is True
    assert json.loads(bundle_path.read_text(encoding="utf-8"))["graph_id"] == "graph-999"


def test_shadow_trace_export_persists_with_export_id(tmp_path):
    request = RetrievalRequest(route="search_bm25.document_chunk", query_text="q", query_ir_v2={"route_id": "search_bm25.document_chunk"})
    pipeline = RetrievalPipelineSpec(
        pipeline_id="orchestrated.search_bm25.document_chunk",
        version="v1",
        stages=[RetrievalPipelineStage(stage_id="bm25", primitive_id="BM25RetrieverParadeDB")],
    )
    canon_result = RetrievalExecutionResult(
        pipeline_id="canon",
        pipeline_version="v1",
        traces=[RetrievalStageTrace(stage="canon:stage.bm25", duration_ms=1.0)],
    )
    export = build_shadow_trace_export(
        export_id="trace-bundle-1",
        request=request,
        pipeline=pipeline,
        canon_result=canon_result,
    )
    persisted = persist_shadow_trace_export(export=export, output_dir=tmp_path)
    export_path = tmp_path / "trace-bundle-1.json"

    assert persisted["path"] == str(export_path)
    assert json.loads(export_path.read_text(encoding="utf-8"))["export_id"] == "trace-bundle-1"

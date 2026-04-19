import json

from QueryLake.canon.runtime import build_shadow_execution_report, persist_shadow_execution_report
from QueryLake.typing.retrieval_primitives import RetrievalCandidate, RetrievalExecutionResult, RetrievalPipelineSpec, RetrievalPipelineStage, RetrievalRequest


def test_shadow_execution_report_builds_expected_payload():
    request = RetrievalRequest(route="search_bm25.document_chunk", query_text="q", options={"limit": 2}, query_ir_v2={"route_id": "search_bm25.document_chunk"})
    pipeline = RetrievalPipelineSpec(
        pipeline_id="orchestrated.search_bm25.document_chunk",
        version="v1",
        stages=[RetrievalPipelineStage(stage_id="bm25", primitive_id="BM25RetrieverParadeDB")],
    )
    legacy_result = RetrievalExecutionResult(
        pipeline_id="legacy",
        pipeline_version="v1",
        candidates=[RetrievalCandidate(content_id="a"), RetrievalCandidate(content_id="b")],
    )
    canon_result = RetrievalExecutionResult(
        pipeline_id="canon",
        pipeline_version="v1",
        candidates=[RetrievalCandidate(content_id="a"), RetrievalCandidate(content_id="b")],
        metadata={
            "canon_graph_id": "graph-123",
            "canon_bridge": {
                "available": True,
                "graph_id": "graph-123",
                "trace_summary": {"retention_class": "summary_only"},
                "replay_summary": {"retention_class": "summary_only"},
            },
        },
    )
    report = build_shadow_execution_report(
        report_id="shadow-report-1",
        request=request,
        pipeline=pipeline,
        profile_id="gold",
        legacy_result=legacy_result,
        canon_result=canon_result,
        shadow_diff={"divergence_class": "exact_match"},
    )

    assert report["report_id"] == "shadow-report-1"
    assert report["route"] == "search_bm25.document_chunk"
    assert report["bridge"]["graph_id"] == "graph-123"
    assert report["legacy"]["candidate_ids_top_k"] == ["a", "b"]
    assert report["canon"]["candidate_ids_top_k"] == ["a", "b"]
    assert report["shadow_diff"]["divergence_class"] == "exact_match"


def test_shadow_execution_report_persists_to_json(tmp_path):
    payload = {"report_id": "persist-me", "schema_version": "canon_shadow_report_v1"}
    persisted = persist_shadow_execution_report(report=payload, output_dir=tmp_path)
    path = tmp_path / "persist-me.json"

    assert persisted["path"] == str(path)
    assert path.exists() is True
    assert json.loads(path.read_text(encoding="utf-8"))["report_id"] == "persist-me"

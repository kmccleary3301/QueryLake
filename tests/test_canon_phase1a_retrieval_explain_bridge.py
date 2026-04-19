from QueryLake.runtime.retrieval_explain import build_retrieval_plan_explain
from QueryLake.typing.retrieval_primitives import RetrievalPipelineSpec, RetrievalPipelineStage


def test_retrieval_plan_explain_includes_canon_bridge_metadata(monkeypatch):
    monkeypatch.delenv("QUERYLAKE_DB_PROFILE", raising=False)
    pipeline = RetrievalPipelineSpec(
        pipeline_id="orchestrated.search_hybrid",
        version="v1",
        stages=[
            RetrievalPipelineStage(stage_id="bm25", primitive_id="BM25RetrieverParadeDB"),
            RetrievalPipelineStage(stage_id="dense", primitive_id="DenseRetrieverPGVector"),
            RetrievalPipelineStage(stage_id="sparse", primitive_id="SparseRetrieverPGVector"),
        ],
        flags={"fusion_primitive": "WeightedScoreFusion"},
    )

    payload = build_retrieval_plan_explain(
        route="search_hybrid.document_chunk",
        pipeline=pipeline,
        options={"explain_plan": True},
    )

    canon_bridge = payload["effective"]["canon_bridge"]
    assert canon_bridge["available"] is True
    assert canon_bridge["graph_name"].startswith("canon.retrieval.search_hybrid.document_chunk")
    assert canon_bridge["trace_summary"]["retention_class"] == "summary_plus_detail"
    assert canon_bridge["stage_nodes"][1]["stage_id"] == "dense"

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.retrieval_explain import build_retrieval_plan_explain
from QueryLake.typing.retrieval_primitives import RetrievalPipelineSpec, RetrievalPipelineStage


def test_retrieval_plan_explain_contains_adapter_metadata(monkeypatch):
    monkeypatch.delenv("QUERYLAKE_DB_PROFILE", raising=False)
    pipeline = RetrievalPipelineSpec(
        pipeline_id="p",
        version="v1",
        stages=[
            RetrievalPipelineStage(stage_id="bm25", primitive_id="BM25RetrieverParadeDB"),
            RetrievalPipelineStage(stage_id="dense", primitive_id="DenseRetrieverPGVector"),
        ],
    )

    payload = build_retrieval_plan_explain(
        route="search_hybrid",
        pipeline=pipeline,
        options={"limit": 10},
    )

    assert payload["effective"]["profile"]["id"] == "paradedb_postgres_gold_v1"
    stage_map = {stage["stage_id"]: stage for stage in payload["pipeline"]["stages"]}
    assert stage_map["bm25"]["adapter"]["adapter_id"] == "paradedb_bm25_v1"
    assert stage_map["bm25"]["adapter"]["lane_family"] == "lexical_bm25"
    assert stage_map["dense"]["adapter"]["adapter_id"] == "pgvector_halfvec_v1"


def test_retrieval_plan_explain_can_surface_route_executor_and_lexical_plan(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    pipeline = RetrievalPipelineSpec(
        pipeline_id="p",
        version="v1",
        stages=[
            RetrievalPipelineStage(stage_id="bm25", primitive_id="BM25RetrieverParadeDB"),
        ],
    )

    payload = build_retrieval_plan_explain(
        route="search_hybrid",
        pipeline=pipeline,
        options={"limit": 10},
        route_executor={
            "route_id": "search_hybrid.document_chunk",
            "executor_id": "opensearch.search_hybrid.document_chunk.v1",
            "planning_v2": {
                "query_ir_v2_template": {
                    "route_id": "search_hybrid.document_chunk",
                    "representation_scope_id": "document_chunk",
                    "strictness_policy": "approximate",
                },
                "projection_ir_v2": {
                    "route_id": "search_hybrid.document_chunk",
                    "representation_scope_id": "document_chunk",
                    "buildability_class": "degraded_executable",
                },
            },
        },
        lexical_capability_plan={
            "query_features": ["phrase_boost"],
            "degraded_capabilities": ["retrieval.lexical.phrase_boost"],
            "unsupported_capabilities": [],
        },
    )

    assert payload["effective"]["route_executor"]["executor_id"] == "opensearch.search_hybrid.document_chunk.v1"
    assert payload["effective"]["query_ir_v2"]["route_id"] == "search_hybrid.document_chunk"
    assert payload["effective"]["query_ir_v2"]["representation_scope_id"] == "document_chunk"
    assert payload["effective"]["projection_ir_v2"]["buildability_class"] == "degraded_executable"
    assert payload["effective"]["lexical_capability_plan"]["degraded_capabilities"] == [
        "retrieval.lexical.phrase_boost"
    ]


def test_retrieval_plan_explain_instantiates_v2_payloads_from_templates(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "sqlite_fts5_dense_sidecar_local_v1")
    pipeline = RetrievalPipelineSpec(
        pipeline_id="p",
        version="v1",
        stages=[RetrievalPipelineStage(stage_id="bm25", primitive_id="BM25RetrieverParadeDB")],
    )

    payload = build_retrieval_plan_explain(
        route="search_bm25",
        pipeline=pipeline,
        route_executor={
            "route_id": "search_bm25.document_chunk",
            "executor_id": "sqlite_local.search_bm25.document_chunk.v1",
            "planning_v2": {
                "query_ir_v2_template": {
                    "raw_query_text": "",
                    "normalized_query_text": "",
                    "lexical_query_text": "",
                    "representation_scope_id": "document_chunk",
                    "strictness_policy": "approximate",
                    "use_dense": False,
                    "use_sparse": False,
                },
                "projection_ir_v2": {
                    "buildability_class": "degraded_executable",
                    "required_targets": [
                        {
                            "target_id": "document_chunk_lexical_projection_v1",
                            "required": True,
                            "target_backend_family": "lexical_index",
                            "support_state": "supported",
                            "metadata": {"target_backend_name": "sqlite_fts5"},
                        }
                    ],
                },
            },
        },
    )

    assert payload["effective"]["query_ir_v2"]["route_id"] == "search_bm25.document_chunk"
    assert payload["effective"]["query_ir_v2"]["representation_scope_id"] == "document_chunk"
    assert payload["effective"]["projection_ir_v2"]["route_id"] == "search_bm25.document_chunk"
    assert payload["effective"]["projection_ir_v2"]["representation_scope_id"] == "document_chunk"
    assert payload["effective"]["projection_ir_v2"]["buildability_class"] == "degraded_executable"

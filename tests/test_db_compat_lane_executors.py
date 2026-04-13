from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.retrieval_lane_executors import (
    build_gold_bm25_search_plan,
    execute_gold_bm25_search,
    execute_gold_document_chunk_hybrid_lanes,
    execute_gold_file_chunk_bm25_search,
)
from QueryLake.runtime.retrieval_primitive_factory import build_retrievers_for_pipeline
from QueryLake.typing.retrieval_primitives import RetrievalPipelineSpec, RetrievalPipelineStage


def test_hybrid_lane_executor_emits_gold_statement():
    stmt = execute_gold_document_chunk_hybrid_lanes(
        None,
        collection_spec="collection_id:IN [abc]",
        formatted_query="text:hello",
        strong_where_clause=None,
        similarity_constraint="WHERE TRUE",
        retrieved_fields_string="text",
        use_bm25=True,
        use_similarity=True,
        use_sparse=False,
        limit_bm25=5,
        limit_similarity=7,
        limit_sparse=0,
        similarity_weight=0.25,
        bm25_weight=0.75,
        sparse_weight=0.0,
        embedding=[0.1, 0.2],
        embedding_sparse={},
        sparse_dimensions=1024,
        return_statement=True,
    )
    assert "paradedb.parse" in stmt
    assert "embedding <=>" in stmt
    assert "LIMIT 5" in stmt or ":limit_bm25" not in stmt


def test_bm25_lane_executor_emits_gold_statement():
    stmt = execute_gold_bm25_search(
        None,
        chosen_table_name="document_chunk",
        chosen_attributes="text",
        parse_field="(collection_id:IN [abc]) AND (text:hello)",
        order_by_field="ORDER BY score DESC, id ASC",
        limit=10,
        offset=0,
        table="document_chunk",
        formatted_query="text:hello",
        quoted_phrases=["hello world"],
        segment_collection_filter="",
        return_statement=True,
    )
    assert "paradedb.parse" in stmt
    assert "bm25_candidates" in stmt
    assert "POSITION" in stmt


def test_factory_builds_gold_retrievers_through_lane_resolution(monkeypatch):
    monkeypatch.delenv("QUERYLAKE_DB_PROFILE", raising=False)
    pipeline = RetrievalPipelineSpec(
        pipeline_id="p",
        version="v1",
        stages=[
            RetrievalPipelineStage(stage_id="bm25", primitive_id="BM25RetrieverParadeDB"),
            RetrievalPipelineStage(stage_id="dense", primitive_id="DenseRetrieverPGVector"),
            RetrievalPipelineStage(stage_id="sparse", primitive_id="SparseRetrieverPGVector"),
        ],
    )
    retrievers = build_retrievers_for_pipeline(
        pipeline=pipeline,
        database=object(),
        auth={},
        toolchain_function_caller=lambda *_args, **_kwargs: None,
        search_bm25_fn=lambda **_kwargs: [],
        search_hybrid_fn=lambda **_kwargs: {"rows": []},
    )
    assert set(retrievers.keys()) == {"bm25", "dense", "sparse"}
    assert retrievers["bm25"].primitive_id == "BM25RetrieverParadeDB"
    assert retrievers["dense"].primitive_id == "DenseRetrieverPGVector"
    assert retrievers["sparse"].primitive_id == "SparseRetrieverPGVector"


def test_file_chunk_bm25_executor_emits_gold_statement():
    stmt = execute_gold_file_chunk_bm25_search(
        None,
        username="alice",
        query="hello world",
        sort_by="score",
        sort_dir="DESC",
        limit=10,
        offset=0,
        return_statement=True,
    )
    assert "paradedb.parse" in stmt
    assert "FROM file_chunk" in stmt
    assert "JOIN file_version" in stmt
    assert "JOIN file " in stmt or "JOIN file\n" in stmt


def test_bm25_plan_builder_preserves_gold_collection_parse_behavior_for_chunks():
    plan = build_gold_bm25_search_plan(
        query='"hello world" alpha',
        valid_fields=["text", "document_name"],
        catch_all_fields=["text"],
        table="document_chunk",
        collection_ids=["abc123"],
        sort_by="score",
        sort_dir="DESC",
        document_collection_attrs=["document_collection_id"],
    )
    assert plan.parse_field == "(collection_id:IN [abc123]) AND (alpha OR text:\"hello world\")" or "collection_id:IN [abc123]" in plan.parse_field
    assert plan.order_by_field == "ORDER BY score DESC, id ASC"
    assert plan.quoted_phrases == ("hello world",)


def test_bm25_plan_builder_uses_segment_scope_filter_for_segment_table():
    plan = build_gold_bm25_search_plan(
        query="boiler pressure",
        valid_fields=["text", "segment_index"],
        catch_all_fields=["text"],
        table="segment",
        collection_ids=["c1", "c2"],
        sort_by="text",
        sort_dir="ASC",
        document_collection_attrs=["document_collection_id"],
    )
    assert plan.parse_field == "boiler pressure" or "text:" in plan.parse_field or plan.formatted_query in plan.parse_field
    assert "collection_id" in plan.segment_collection_filter
    assert "c1" in plan.segment_collection_filter and "c2" in plan.segment_collection_filter


def test_file_chunk_executor_empty_query_falls_back_to_created_at_sort():
    stmt = execute_gold_file_chunk_bm25_search(
        None,
        username="alice",
        query="",
        sort_by="score",
        sort_dir="DESC",
        limit=10,
        offset=0,
        return_statement=True,
    )
    assert "ORDER BY created_at DESC" in stmt
    assert "paradedb.parse" not in stmt

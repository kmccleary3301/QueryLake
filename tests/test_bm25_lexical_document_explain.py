from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.api.search import search_bm25
from QueryLake.runtime.db_compat import BackendStack
from QueryLake.runtime.retrieval_route_executors import (
    BM25RouteExecution,
    ResolvedRouteExecutor,
    RouteExecutorResolution,
)


class DummyUserAuth:
    username = "alice"


class DummyDB:
    def rollback(self):
        return None


def test_search_bm25_document_direct_plan_explain_surfaces_lexical_variant(monkeypatch):
    monkeypatch.delenv("QUERYLAKE_DB_PROFILE", raising=False)
    monkeypatch.setattr("QueryLake.api.search.get_user", lambda *_args, **_kwargs: (None, DummyUserAuth()))
    monkeypatch.setattr("QueryLake.api.search.assert_collections_priviledge", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        "QueryLake.api.search._build_route_planning_context_v2",
        lambda *_, **__: {
            "query_ir_v2": {
                "route_id": "search_bm25.document",
                "representation_scope_id": "document",
                "raw_query_text": "basf_sample.md",
                "normalized_query_text": "basf_sample.md",
                "lexical_query_text": "basf_sample.md",
                "use_dense": False,
                "use_sparse": False,
                "filter_ir": {"collection_ids": ["c1"], "document_ids": [], "metadata_filters": []},
                "planner_hints": {},
                "metadata": {},
            },
            "projection_ir_v2": {
                "route_id": "search_bm25.document",
                "representation_scope_id": "document",
                "projection_id": "document_lexical_projection_v1",
                "storage_backend": "postgresql",
                "adapter_chain": [],
                "metadata": {},
            },
        },
    )

    class _FakeBm25Executor:
        def execute(self, *_args, **_kwargs):
            return BM25RouteExecution(
                rows_or_statement=[
                    (
                        "doc-1",
                        4.2,
                        "doc-1",
                        "basf_sample.md",
                        123.0,
                        "hash-1",
                        42,
                        None,
                        "c1",
                        None,
                        "blob-1",
                        "file",
                        3,
                        {"file_name": "basf_sample.md"},
                    ),
                ],
                formatted_query="basf_sample.md",
                quoted_phrases=(),
                plan=type("Plan", (), {"lexical_query_debug": {"field_weights": {"document_name": 3.0}}})(),
            )

    monkeypatch.setattr(
        "QueryLake.api.search.resolve_search_bm25_route_executor",
        lambda **_kwargs: ResolvedRouteExecutor(
            resolution=RouteExecutorResolution(
                route_id="search_bm25.document",
                executor_id="gold.search_bm25.document.v1",
                profile_id="paradedb_postgres_gold_v1",
                implemented=True,
                support_state="supported",
                backend_stack=BackendStack(
                    authority="postgresql",
                    lexical="paradedb",
                    dense="pgvector_halfvec",
                    sparse="pgvector_sparsevec",
                    graph="postgresql_segment_relations",
                ),
                lane_adapters={},
                projection_descriptors=["document_lexical_projection_v1"],
            ),
            executor=_FakeBm25Executor(),
        ),
    )

    payload = search_bm25(
        database=DummyDB(),
        auth={"oauth2": "tok"},
        query="basf_sample.md",
        collection_ids=["c1"],
        table="document",
        group_chunks=False,
        explain_plan=True,
        _direct_stage_call=True,
        _skip_observability=True,
        lexical_variant_id="QL-L4",
    )

    assert "plan_explain" in payload
    assert payload["plan_explain"]["effective"]["lexical_variant"]["variant_id"] == "QL-L4"
    assert payload["plan_explain"]["effective"]["query_ir_v2"]["route_id"] == "search_bm25.document"
    assert payload["plan_explain"]["effective"]["projection_ir_v2"]["representation_scope_id"] == "document"

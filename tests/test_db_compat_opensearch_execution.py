from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.opensearch_route_execution import (  # noqa: E402
    execute_opensearch_file_chunk_bm25_search,
    execute_opensearch_document_chunk_bm25_search,
    execute_opensearch_document_chunk_hybrid_search,
)


def test_opensearch_bm25_executor_hydrates_document_chunk_rows(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    hydration_calls = {}

    monkeypatch.setattr(
        "QueryLake.runtime.opensearch_route_execution._perform_opensearch_request",
        lambda **_kwargs: {
            "hits": {
                "hits": [
                    {"_id": "chunk-b", "_score": 8.0, "_source": {}},
                    {"_id": "chunk-a", "_score": 9.5, "_source": {}},
                ]
            }
        },
    )
    monkeypatch.setattr(
        "QueryLake.runtime.opensearch_route_execution.hydrate_projection_target",
        lambda _database, target: hydration_calls.update(
            {
                "projection_id": target.projection_id,
                "record_ids": tuple(target.record_ids),
                "authority_model": target.authority_model,
            }
        )
        or {
            "chunk-a": ("chunk-a", 1.0, None, "doc-a", 0, None, "c1", "Doc A", None, False, {}, {}, "alpha"),
            "chunk-b": ("chunk-b", 2.0, None, "doc-b", 1, None, "c1", "Doc B", None, False, {}, {}, "beta"),
        },
    )

    plan, rows = execute_opensearch_document_chunk_bm25_search(
        database=object(),
        projection_id="document_chunk_lexical_projection_v1",
        query="boiler feed water",
        collection_ids=["c1"],
        sort_by="score",
        sort_dir="DESC",
        limit=5,
        offset=0,
    )

    assert plan.formatted_query == "boiler feed water"
    assert [row[0] for row in rows] == ["chunk-b", "chunk-a"]
    assert [row[1] for row in rows] == [8.0, 9.5]
    assert rows[0][2] == "chunk-b"
    assert hydration_calls["projection_id"] == "document_chunk_lexical_projection_v1"
    assert hydration_calls["record_ids"] == ("chunk-b", "chunk-a")
    assert hydration_calls["authority_model"] == "document_chunk_compatibility"


def test_opensearch_bm25_return_statement_includes_projection_id(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    plan, statement = execute_opensearch_document_chunk_bm25_search(
        database=object(),
        projection_id="document_chunk_lexical_projection_v1",
        query="feed water",
        collection_ids=["c1"],
        sort_by="score",
        sort_dir="DESC",
        limit=5,
        offset=0,
        return_statement=True,
    )

    assert plan.formatted_query == "feed water"
    assert "\"projection_id\": \"document_chunk_lexical_projection_v1\"" in statement


def test_opensearch_hybrid_executor_combines_lexical_and_dense_rrf(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    hydration_calls = {}

    call_counter = {"count": 0}

    def _fake_search(**_kwargs):
        call_counter["count"] += 1
        if call_counter["count"] == 1:
            return {
                "hits": {
                    "hits": [
                        {"_id": "chunk-a", "_score": 11.0, "_source": {}},
                        {"_id": "chunk-b", "_score": 9.0, "_source": {}},
                    ]
                }
            }
        return {
            "hits": {
                "hits": [
                    {"_id": "chunk-b", "_score": 0.91, "_source": {}},
                    {"_id": "chunk-c", "_score": 0.88, "_source": {}},
                ]
            }
        }

    monkeypatch.setattr("QueryLake.runtime.opensearch_route_execution._perform_opensearch_request", _fake_search)
    monkeypatch.setattr(
        "QueryLake.runtime.opensearch_route_execution.hydrate_projection_target",
        lambda _database, target: hydration_calls.update(
            {
                "projection_id": target.projection_id,
                "record_ids": tuple(target.record_ids),
                "authority_model": target.authority_model,
            }
        )
        or {
            "chunk-a": ("chunk-a", 1.0, None, "doc-a", 0, None, "c1", "Doc A", None, False, {}, {}, "alpha"),
            "chunk-b": ("chunk-b", 2.0, None, "doc-b", 1, None, "c1", "Doc B", None, False, {}, {}, "beta"),
            "chunk-c": ("chunk-c", 3.0, None, "doc-c", 2, None, "c1", "Doc C", None, False, {}, {}, "gamma"),
        },
    )

    rows = execute_opensearch_document_chunk_hybrid_search(
        database=object(),
        projection_descriptors=[
            "document_chunk_lexical_projection_v1",
            "document_chunk_dense_projection_v1",
        ],
        raw_query_text="vapor recovery",
        collection_ids=["c1"],
        use_bm25=True,
        use_similarity=True,
        use_sparse=False,
        limit_bm25=5,
        limit_similarity=5,
        limit_sparse=0,
        similarity_weight=0.7,
        bm25_weight=0.3,
        sparse_weight=0.0,
        embedding=[0.1, 0.2, 0.3],
    )

    assert [row[0] for row in rows] == ["chunk-b", "chunk-c", "chunk-a"]
    assert rows[0][4] > rows[1][4] > rows[2][4]
    assert rows[0][5] == "chunk-b"
    assert hydration_calls["projection_id"] == "document_chunk_dense_projection_v1"
    assert hydration_calls["record_ids"] == ("chunk-a", "chunk-b", "chunk-c")
    assert hydration_calls["authority_model"] == "document_chunk_compatibility"


def test_opensearch_hybrid_return_statement_is_backend_request_summary(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    statement = execute_opensearch_document_chunk_hybrid_search(
        database=object(),
        projection_descriptors=[
            "document_chunk_lexical_projection_v1",
            "document_chunk_dense_projection_v1",
        ],
        raw_query_text="steam boiler",
        collection_ids=["c1"],
        use_bm25=True,
        use_similarity=True,
        use_sparse=False,
        limit_bm25=10,
        limit_similarity=10,
        limit_sparse=0,
        similarity_weight=0.5,
        bm25_weight=0.5,
        sparse_weight=0.0,
        embedding=[0.5, 0.4],
        return_statement=True,
    )
    assert "\"backend\": \"opensearch\"" in statement
    assert "\"route\": \"search_hybrid.document_chunk\"" in statement
    assert "\"projection_id\": \"document_chunk_dense_projection_v1\"" in statement


def test_opensearch_file_chunk_executor_hydrates_file_chunk_rows(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    hydration_calls = {}

    monkeypatch.setattr(
        "QueryLake.runtime.opensearch_route_execution._perform_opensearch_request",
        lambda **_kwargs: {
            "hits": {
                "hits": [
                    {"_id": "fc-b", "_score": 8.0, "_source": {}},
                    {"_id": "fc-a", "_score": 9.5, "_source": {}},
                ]
            }
        },
    )
    monkeypatch.setattr(
        "QueryLake.runtime.opensearch_route_execution.hydrate_projection_target",
        lambda _database, target: hydration_calls.update(
            {
                "projection_id": target.projection_id,
                "record_ids": tuple(target.record_ids),
                "authority_model": target.authority_model,
            }
        )
        or {
            "fc-a": ("fc-a", "alpha", {"page": 1}, 101.0, "fv-a"),
            "fc-b": ("fc-b", "beta", {"page": 2}, 102.0, "fv-b"),
        },
    )

    query_is_empty, rows = execute_opensearch_file_chunk_bm25_search(
        database=object(),
        projection_id="file_chunk_lexical_projection_v1",
        username="alice",
        query="boiler feed water",
        sort_by="score",
        sort_dir="DESC",
        limit=5,
        offset=0,
    )

    assert query_is_empty is False
    assert [row[0] for row in rows] == ["fc-b", "fc-a"]
    assert [row[1] for row in rows] == [8.0, 9.5]
    assert rows[0][2] == "fc-b"
    assert hydration_calls["projection_id"] == "file_chunk_lexical_projection_v1"
    assert hydration_calls["record_ids"] == ("fc-b", "fc-a")
    assert hydration_calls["authority_model"] == "file_chunk_compatibility"


def test_opensearch_file_chunk_return_statement_includes_projection_id(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    query_is_empty, statement = execute_opensearch_file_chunk_bm25_search(
        database=object(),
        projection_id="file_chunk_lexical_projection_v1",
        username="alice",
        query="",
        sort_by="score",
        sort_dir="DESC",
        limit=5,
        offset=0,
        return_statement=True,
    )

    assert query_is_empty is True
    assert "\"route\": \"search_file_chunks\"" in statement
    assert "\"projection_id\": \"file_chunk_lexical_projection_v1\"" in statement

from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.api.search import search_bm25, search_file_chunks, search_hybrid
from QueryLake.runtime.db_compat import BackendStack, QueryLakeUnsupportedFeatureError
from QueryLake.runtime.retrieval_route_executors import (
    BM25RouteExecution,
    FileChunkRouteExecution,
    ResolvedRouteExecutor,
    RouteExecutorResolution,
)


class DummyUserAuth:
    username = "alice"


class DummyDB:
    def rollback(self):
        return None


async def _unused_toolchain_function_caller(_name):
    raise AssertionError("toolchain_function_caller should not be used in this test")


def test_search_file_chunks_applies_capability_gate(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "postgres_pgvector_light_v1")
    monkeypatch.setattr("QueryLake.api.search.get_user", lambda *_args, **_kwargs: (None, DummyUserAuth()))

    with pytest.raises(QueryLakeUnsupportedFeatureError) as exc_info:
        search_file_chunks(
            database=object(),
            auth={"oauth2": "tok"},
            query="hello",
        )

    payload = exc_info.value.to_payload()
    assert payload["type"] == "unsupported_feature"
    assert payload["capability"] == "retrieval.lexical.bm25"
    assert payload["profile"] == "postgres_pgvector_light_v1"


def test_search_bm25_document_chunk_preserves_gold_result_ordering_and_scores(monkeypatch):
    monkeypatch.delenv("QUERYLAKE_DB_PROFILE", raising=False)
    monkeypatch.setattr("QueryLake.api.search.get_user", lambda *_args, **_kwargs: (None, DummyUserAuth()))
    monkeypatch.setattr("QueryLake.api.search.assert_collections_priviledge", lambda *_args, **_kwargs: None)

    class _FakeBm25Executor:
        def execute(self, *_args, **_kwargs):
            return BM25RouteExecution(
                rows_or_statement=[
                    (
                        "row-a", 0.2,
                        "row-a", 1.0, None, "doc-a", 0, None, "c1", "Doc A", None, False, {}, {}, "alpha"
                    ),
                    (
                        "row-b", 0.9,
                        "row-b", 2.0, None, "doc-b", 1, None, "c1", "Doc B", None, False, {}, {}, "beta"
                    ),
                ],
                formatted_query="hello OR world",
                quoted_phrases=(),
                plan=None,
            )

    monkeypatch.setattr(
        "QueryLake.api.search.resolve_search_bm25_route_executor",
        lambda **_kwargs: ResolvedRouteExecutor(
            resolution=RouteExecutorResolution(
                route_id="search_bm25.document_chunk",
                executor_id="test.executor",
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
                projection_descriptors=["document_chunk_lexical_projection_v1"],
            ),
            executor=_FakeBm25Executor(),
        ),
    )

    results = search_bm25(
        database=DummyDB(),
        auth={"oauth2": "tok"},
        query="hello world",
        collection_ids=["c1"],
        table="document_chunk",
        group_chunks=False,
        _direct_stage_call=True,
        _skip_observability=True,
    )

    assert [row.id for row in results] == ["row-b", "row-a"]
    assert [row.bm25_score for row in results] == [0.9, 0.2]


def test_search_file_chunks_shapes_gold_executor_rows_without_sql_regression(monkeypatch):
    monkeypatch.delenv("QUERYLAKE_DB_PROFILE", raising=False)
    monkeypatch.setattr("QueryLake.api.search.get_user", lambda *_args, **_kwargs: (None, DummyUserAuth()))

    class _FakeFileChunkExecutor:
        def execute(self, *_args, **_kwargs):
            return FileChunkRouteExecution(
                rows_or_statement=[
                    ("fc-1", 0.7, "fc-1", "chunk text", {"page": 1}, 123.0, "fv-1"),
                ],
                query_is_empty=False,
            )

    monkeypatch.setattr(
        "QueryLake.api.search.resolve_search_file_chunks_route_executor",
        lambda **_kwargs: ResolvedRouteExecutor(
            resolution=RouteExecutorResolution(
                route_id="search_file_chunks",
                executor_id="test.executor",
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
                projection_descriptors=["file_chunk_lexical_projection_v1"],
            ),
            executor=_FakeFileChunkExecutor(),
        ),
    )

    results = search_file_chunks(
        database=DummyDB(),
        auth={"oauth2": "tok"},
        query="boiler",
        _direct_stage_call=True,
        _skip_observability=True,
    )

    assert results == {
        "results": [
            {
                "id": "fc-1",
                "text": "chunk text",
                "md": {"page": 1},
                "created_at": 123.0,
                "file_version_id": "fv-1",
                "bm25_score": 0.7,
            }
        ]
    }


def test_search_file_chunks_surfaces_v2_plan_explain(monkeypatch):
    monkeypatch.delenv("QUERYLAKE_DB_PROFILE", raising=False)
    monkeypatch.setattr("QueryLake.api.search.get_user", lambda *_args, **_kwargs: (None, DummyUserAuth()))

    class _FakeFileChunkExecutor:
        def execute(self, *_args, **_kwargs):
            return FileChunkRouteExecution(
                rows_or_statement=[
                    ("fc-1", 0.7, "fc-1", "chunk text", {"page": 1}, 123.0, "fv-1"),
                ],
                query_is_empty=False,
            )

    monkeypatch.setattr(
        "QueryLake.api.search.resolve_search_file_chunks_route_executor",
        lambda **_kwargs: ResolvedRouteExecutor(
            resolution=RouteExecutorResolution(
                route_id="search_file_chunks",
                executor_id="gold.search_file_chunks.v1",
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
                projection_descriptors=["file_chunk_lexical_projection_v1"],
            ),
            executor=_FakeFileChunkExecutor(),
        ),
    )

    results = search_file_chunks(
        database=DummyDB(),
        auth={"oauth2": "tok"},
        query="boiler",
        explain_plan=True,
        _direct_stage_call=True,
        _skip_observability=True,
    )

    assert results["plan_explain"]["effective"]["query_ir_v2"]["route_id"] == "search_file_chunks"
    assert results["plan_explain"]["effective"]["query_ir_v2"]["representation_scope_id"] == "file_chunk"
    assert results["plan_explain"]["effective"]["projection_ir_v2"]["route_id"] == "search_file_chunks"
    assert results["plan_explain"]["effective"]["projection_ir_v2"]["representation_scope_id"] == "file_chunk"
    assert results["plan_explain"]["effective"]["lexical_capability_plan"]["degraded_capabilities"] == []


@pytest.mark.asyncio
async def test_search_hybrid_pgvector_light_supports_dense_only_document_chunk_route(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "postgres_pgvector_light_v1")
    monkeypatch.setattr("QueryLake.api.search.get_user", lambda *_args, **_kwargs: (None, DummyUserAuth()))
    monkeypatch.setattr("QueryLake.api.search.assert_collections_priviledge", lambda *_args, **_kwargs: None)

    class _FakeDenseOnlyHybridExecutor:
        def execute(self, *_args, **_kwargs):
            return [
                (
                    "row-dense", 0.81, 0.0, 0.0, 0.81,
                    "row-dense", 1.0, None, "doc-dense", 0, None, "c1", "Dense Doc", None, False, {}, {}, "dense text"
                )
            ]

    monkeypatch.setattr(
        "QueryLake.api.search.resolve_search_hybrid_route_executor",
        lambda **_kwargs: ResolvedRouteExecutor(
            resolution=RouteExecutorResolution(
                route_id="search_hybrid.document_chunk",
                executor_id="pgvector.search_hybrid.document_chunk.dense_only.v1",
                profile_id="postgres_pgvector_light_v1",
                implemented=True,
                support_state="supported",
                backend_stack=BackendStack(
                    authority="postgresql",
                    lexical="none",
                    dense="pgvector_halfvec",
                    sparse="none",
                    graph="postgresql_segment_relations",
                ),
                lane_adapters={},
                projection_descriptors=[],
            ),
            executor=_FakeDenseOnlyHybridExecutor(),
        ),
    )

    payload = await search_hybrid(
        database=DummyDB(),
        toolchain_function_caller=_unused_toolchain_function_caller,
        auth={"oauth2": "tok"},
        query={"embedding": "dense query", "bm25": ""},
        embedding=[0.1] * 1024,
        collection_ids=["c1"],
        use_bm25=False,
        use_similarity=True,
        use_sparse=False,
        limit_bm25=0,
        limit_similarity=8,
        limit_sparse=0,
        bm25_weight=0.0,
        similarity_weight=1.0,
        sparse_weight=0.0,
        group_chunks=False,
        _direct_stage_call=True,
        _skip_observability=True,
    )

    assert payload["rows"][0]["id"] == "row-dense"
    assert payload["rows"][0]["similarity_score"] == 0.81
    assert payload["rows"][0]["bm25_score"] == 0.0


@pytest.mark.asyncio
async def test_search_hybrid_split_stack_hard_constraints_fail_even_with_implicit_bm25(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setattr("QueryLake.api.search.get_user", lambda *_args, **_kwargs: (None, DummyUserAuth()))
    monkeypatch.setattr("QueryLake.api.search.assert_collections_priviledge", lambda *_args, **_kwargs: None)

    with pytest.raises(QueryLakeUnsupportedFeatureError) as exc_info:
        await search_hybrid(
            database=DummyDB(),
            toolchain_function_caller=_unused_toolchain_function_caller,
            auth={"oauth2": "tok"},
            query={"bm25": "title:boiler", "embedding": ""},
            collection_ids=["c1"],
            limit_bm25=10,
            limit_similarity=0,
            limit_sparse=0,
            bm25_weight=1.0,
            similarity_weight=0.0,
            sparse_weight=0.0,
            use_similarity=False,
            use_sparse=False,
            group_chunks=False,
            _direct_stage_call=True,
            _skip_observability=True,
        )

    payload = exc_info.value.to_payload()
    assert payload["capability"] == "retrieval.lexical.hard_constraints"
    assert payload["profile"] == "aws_aurora_pg_opensearch_v1"


@pytest.mark.asyncio
async def test_search_hybrid_split_stack_phrase_query_surfaces_degraded_lexical_plan(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setattr("QueryLake.api.search.get_user", lambda *_args, **_kwargs: (None, DummyUserAuth()))
    monkeypatch.setattr("QueryLake.api.search.assert_collections_priviledge", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("QueryLake.api.search.fetch_document_chunk_materialization_provenance", lambda database, records: [])
    monkeypatch.setattr("QueryLake.api.search.fetch_document_chunk_authority_materializations", lambda database, records: [])

    class _FakeLexicalHybridExecutor:
        def execute(self, *_args, **_kwargs):
            return [
                (
                    "row-phrase", 0.91, 0.91, 0.0, 0.91,
                    "row-phrase", 1.0, None, "doc-phrase", 0, None, "c1", "Phrase Doc", None, False, {}, {}, "phrase text"
                )
            ]

    monkeypatch.setattr(
        "QueryLake.api.search.resolve_search_hybrid_route_executor",
        lambda **_kwargs: ResolvedRouteExecutor(
            resolution=RouteExecutorResolution(
                route_id="search_hybrid.document_chunk",
                executor_id="opensearch.search_hybrid.document_chunk.lexical_dense.v1",
                profile_id="aws_aurora_pg_opensearch_v1",
                implemented=True,
                support_state="degraded",
                backend_stack=BackendStack(
                    authority="aurora_postgresql",
                    lexical="opensearch",
                    dense="opensearch",
                    sparse="opensearch",
                    graph="aurora_postgresql_segment_relations",
                ),
                lane_adapters={},
                projection_descriptors=["document_chunk_lexical_projection_v1"],
            ),
            executor=_FakeLexicalHybridExecutor(),
        ),
    )

    payload = await search_hybrid(
        database=DummyDB(),
        toolchain_function_caller=_unused_toolchain_function_caller,
        auth={"oauth2": "tok"},
        query={"bm25": "\"vapor recovery\"", "embedding": ""},
        collection_ids=["c1"],
        limit_bm25=10,
        limit_similarity=0,
        limit_sparse=0,
        bm25_weight=1.0,
        similarity_weight=0.0,
        sparse_weight=0.0,
        use_similarity=False,
        use_sparse=False,
        explain_plan=True,
        group_chunks=False,
        _direct_stage_call=True,
        _skip_observability=True,
    )

    lexical_plan = payload["plan_explain"]["effective"]["lexical_capability_plan"]
    assert payload["plan_explain"]["effective"]["query_ir_v2"]["route_id"] == "search_hybrid.document_chunk"
    assert payload["plan_explain"]["effective"]["query_ir_v2"]["representation_scope_id"] == "document_chunk"
    assert payload["plan_explain"]["effective"]["projection_ir_v2"]["route_id"] == "search_hybrid.document_chunk"
    assert lexical_plan["degraded_capabilities"] == [
        "retrieval.lexical.advanced_operators",
        "retrieval.lexical.phrase_boost",
    ]
    assert lexical_plan["unsupported_capabilities"] == []


@pytest.mark.asyncio
async def test_search_hybrid_split_stack_proximity_query_surfaces_degraded_lexical_plan(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setattr("QueryLake.api.search.get_user", lambda *_args, **_kwargs: (None, DummyUserAuth()))
    monkeypatch.setattr("QueryLake.api.search.assert_collections_priviledge", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("QueryLake.api.search.fetch_document_chunk_materialization_provenance", lambda database, records: [])
    monkeypatch.setattr("QueryLake.api.search.fetch_document_chunk_authority_materializations", lambda database, records: [])

    class _FakeLexicalHybridExecutor:
        def execute(self, *_args, **_kwargs):
            return [
                (
                    "row-prox", 0.73, 0.73, 0.0, 0.73,
                    "row-prox", 1.0, None, "doc-prox", 0, None, "c1", "Prox Doc", None, False, {}, {}, "prox text"
                )
            ]

    monkeypatch.setattr(
        "QueryLake.api.search.resolve_search_hybrid_route_executor",
        lambda **_kwargs: ResolvedRouteExecutor(
            resolution=RouteExecutorResolution(
                route_id="search_hybrid.document_chunk",
                executor_id="opensearch.search_hybrid.document_chunk.lexical_dense.v1",
                profile_id="aws_aurora_pg_opensearch_v1",
                implemented=True,
                support_state="degraded",
                backend_stack=BackendStack(
                    authority="aurora_postgresql",
                    lexical="opensearch",
                    dense="opensearch",
                    sparse="opensearch",
                    graph="aurora_postgresql_segment_relations",
                ),
                lane_adapters={},
                projection_descriptors=["document_chunk_lexical_projection_v1"],
            ),
            executor=_FakeLexicalHybridExecutor(),
        ),
    )

    payload = await search_hybrid(
        database=DummyDB(),
        toolchain_function_caller=_unused_toolchain_function_caller,
        auth={"oauth2": "tok"},
        query={"bm25": "\"vapor recovery\"~3", "embedding": ""},
        collection_ids=["c1"],
        limit_bm25=10,
        limit_similarity=0,
        limit_sparse=0,
        bm25_weight=1.0,
        similarity_weight=0.0,
        sparse_weight=0.0,
        use_similarity=False,
        use_sparse=False,
        explain_plan=True,
        group_chunks=False,
        _direct_stage_call=True,
        _skip_observability=True,
    )

    lexical_plan = payload["plan_explain"]["effective"]["lexical_capability_plan"]
    assert payload["plan_explain"]["effective"]["query_ir_v2"]["route_id"] == "search_hybrid.document_chunk"
    assert payload["plan_explain"]["effective"]["projection_ir_v2"]["representation_scope_id"] == "document_chunk"
    assert lexical_plan["degraded_capabilities"] == [
        "retrieval.lexical.advanced_operators",
        "retrieval.lexical.phrase_boost",
        "retrieval.lexical.proximity",
    ]
    assert lexical_plan["unsupported_capabilities"] == []


@pytest.mark.asyncio
async def test_search_hybrid_direct_plan_explain_surfaces_authority_materializations(monkeypatch):
    monkeypatch.delenv("QUERYLAKE_DB_PROFILE", raising=False)
    monkeypatch.setattr("QueryLake.api.search.get_user", lambda *_args, **_kwargs: (None, DummyUserAuth()))
    monkeypatch.setattr("QueryLake.api.search.assert_collections_priviledge", lambda *_args, **_kwargs: None)

    class _FakeHybridExecutor:
        def execute(self, *_args, **_kwargs):
            return [
                (
                    "row-direct", 0.88, 0.88, 0.0, 0.88,
                    "row-direct", 1.0, None, "doc-direct", 0, None, "c1", "Direct Doc", None, False, {}, {}, "direct text"
                )
            ]

    monkeypatch.setattr(
        "QueryLake.api.search.resolve_search_hybrid_route_executor",
        lambda **_kwargs: ResolvedRouteExecutor(
            resolution=RouteExecutorResolution(
                route_id="search_hybrid.document_chunk",
                executor_id="gold.search_hybrid.document_chunk.v1",
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
                projection_descriptors=["document_chunk_lexical_projection_v1"],
            ),
            executor=_FakeHybridExecutor(),
        ),
    )
    monkeypatch.setattr(
        "QueryLake.api.search.fetch_document_chunk_materialization_provenance",
        lambda database, records: [
            {
                "chunk_id": "row-direct",
                "canonical_authority_segment_id": "seg-direct",
                "authority_segment_consistent": True,
            }
        ],
    )
    monkeypatch.setattr(
        "QueryLake.api.search.fetch_document_chunk_authority_materializations",
        lambda database, records: [
            {
                "chunk_id": "row-direct",
                "materialized_authority_segment_id": "seg-direct",
                "authority_segment_resolved": True,
                "segment_materialization": {
                    "id": "seg-direct",
                    "segment_index": 3,
                    "document_id": "doc-direct",
                },
            }
        ],
    )

    logged = {"kwargs": None}
    monkeypatch.setattr("QueryLake.api.search.log_retrieval_run", lambda *args, **kwargs: logged.update({"kwargs": kwargs}))
    monkeypatch.setattr("QueryLake.api.search.metrics.record_retrieval", lambda **kwargs: None)

    payload = await search_hybrid(
        database=DummyDB(),
        toolchain_function_caller=_unused_toolchain_function_caller,
        auth={"oauth2": "tok"},
        query={"bm25": "boiler", "embedding": ""},
        collection_ids=["c1"],
        limit_bm25=10,
        limit_similarity=0,
        limit_sparse=0,
        bm25_weight=1.0,
        similarity_weight=0.0,
        sparse_weight=0.0,
        use_similarity=False,
        use_sparse=False,
        explain_plan=True,
        group_chunks=False,
        _direct_stage_call=True,
        _skip_observability=False,
    )

    assert payload["plan_explain"]["effective"]["compatibility_provenance"]["records"][0]["chunk_id"] == "row-direct"
    assert payload["plan_explain"]["effective"]["compatibility_materializations"]["records"][0]["segment_materialization"]["id"] == "seg-direct"
    assert logged["kwargs"]["md"]["compatibility_materialization_summary"]["resolved_record_count"] == 1
    assert logged["kwargs"]["md"]["compatibility_materialization_summary"]["unique_authority_segment_count"] == 1


def test_search_bm25_document_chunk_plan_explain_surfaces_authority_materializations(monkeypatch):
    monkeypatch.delenv("QUERYLAKE_DB_PROFILE", raising=False)
    monkeypatch.setattr("QueryLake.api.search.get_user", lambda *_args, **_kwargs: (None, DummyUserAuth()))
    monkeypatch.setattr("QueryLake.api.search.assert_collections_priviledge", lambda *_args, **_kwargs: None)

    class _FakeBm25Executor:
        def execute(self, *_args, **_kwargs):
            return BM25RouteExecution(
                rows_or_statement=[
                    (
                        "row-a", 0.9,
                        "row-a", 1.0, None, "doc-a", 0, None, "c1", "Doc A", None, False, {}, {}, "alpha"
                    ),
                ],
                formatted_query="boiler",
                quoted_phrases=(),
                plan=None,
            )

    monkeypatch.setattr(
        "QueryLake.api.search.resolve_search_bm25_route_executor",
        lambda **_kwargs: ResolvedRouteExecutor(
            resolution=RouteExecutorResolution(
                route_id="search_bm25.document_chunk",
                executor_id="gold.search_bm25.document_chunk.v1",
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
                projection_descriptors=["document_chunk_lexical_projection_v1"],
            ),
            executor=_FakeBm25Executor(),
        ),
    )
    monkeypatch.setattr(
        "QueryLake.api.search.fetch_document_chunk_materialization_provenance",
        lambda database, records: [{"chunk_id": "row-a", "canonical_authority_segment_id": "seg-a", "authority_segment_consistent": True}],
    )
    monkeypatch.setattr(
        "QueryLake.api.search.fetch_document_chunk_authority_materializations",
        lambda database, records: [{"chunk_id": "row-a", "materialized_authority_segment_id": "seg-a", "authority_segment_resolved": True, "segment_materialization": {"id": "seg-a", "segment_index": 1}}],
    )

    logged = {"kwargs": None}
    monkeypatch.setattr("QueryLake.api.search.log_retrieval_run", lambda *args, **kwargs: logged.update({"kwargs": kwargs}))
    monkeypatch.setattr("QueryLake.api.search.metrics.record_retrieval", lambda **kwargs: None)

    payload = search_bm25(
        database=DummyDB(),
        auth={"oauth2": "tok"},
        query="boiler",
        collection_ids=["c1"],
        table="document_chunk",
        group_chunks=False,
        explain_plan=True,
        _direct_stage_call=True,
        _skip_observability=False,
    )

    assert payload["plan_explain"]["effective"]["compatibility_provenance"]["records"][0]["chunk_id"] == "row-a"
    assert payload["plan_explain"]["effective"]["compatibility_materializations"]["records"][0]["segment_materialization"]["id"] == "seg-a"
    assert logged["kwargs"]["md"]["compatibility_materialization_summary"]["resolved_record_count"] == 1
    assert logged["kwargs"]["md"]["compatibility_materialization_summary"]["unique_authority_segment_count"] == 1

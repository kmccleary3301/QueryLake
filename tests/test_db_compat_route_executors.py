from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.db_compat import QueryLakeUnsupportedFeatureError, get_deployment_profile
from QueryLake.runtime.retrieval_route_executors import (
    GoldSearchBM25RouteExecutor,
    GoldSearchFileChunkRouteExecutor,
    GoldSearchHybridRouteExecutor,
    OpenSearchDocumentChunkBM25RouteExecutor,
    OpenSearchDocumentChunkHybridRouteExecutor,
    OpenSearchFileChunkRouteExecutor,
    PlaceholderSearchBM25RouteExecutor,
    PlaceholderSearchFileChunkRouteExecutor,
    PlaceholderSearchHybridRouteExecutor,
    resolve_search_bm25_route_executor,
    resolve_search_file_chunks_route_executor,
    resolve_search_hybrid_route_executor,
)
from QueryLake.runtime.local_route_execution import (
    SQLiteLocalSearchBM25RouteExecutor,
    SQLiteLocalSearchFileChunkRouteExecutor,
    SQLiteLocalSearchHybridRouteExecutor,
)
from QueryLake.database.sql_db_tables import DocumentChunk, file_chunk as FileChunkTable


def test_gold_profile_resolves_gold_route_executors(monkeypatch):
    monkeypatch.delenv("QUERYLAKE_DB_PROFILE", raising=False)
    profile = get_deployment_profile()

    bm25 = resolve_search_bm25_route_executor(table="document_chunk", profile=profile)
    hybrid = resolve_search_hybrid_route_executor(use_bm25=True, use_similarity=True, use_sparse=True, profile=profile)
    file_chunks = resolve_search_file_chunks_route_executor(profile=profile)

    assert bm25.resolution.implemented is True
    assert hybrid.resolution.implemented is True
    assert file_chunks.resolution.implemented is True
    assert bm25.resolution.representation_scope_id == "document_chunk"
    assert bm25.resolution.representation_scope["authority_model"] == "document_segment"
    assert bm25.resolution.projection_descriptors == ["document_chunk_lexical_projection_v1"]
    assert bm25.resolution.projection_targets[0]["projection_id"] == "document_chunk_lexical_projection_v1"
    assert bm25.resolution.projection_targets[0]["target_backend_name"] == "paradedb"
    assert bm25.resolution.planning_v2["query_ir_v2_template"]["route_id"] == "search_bm25.document_chunk"
    assert bm25.resolution.planning_v2["projection_ir_v2"]["representation_scope_id"] == "document_chunk"
    assert hybrid.resolution.projection_descriptors == [
        "document_chunk_lexical_projection_v1",
        "document_chunk_dense_projection_v1",
        "document_chunk_sparse_projection_v1",
    ]
    assert [entry["target_backend_name"] for entry in hybrid.resolution.projection_targets] == [
        "paradedb",
        "pgvector_halfvec",
        "pgvector_sparsevec",
    ]
    assert file_chunks.resolution.projection_descriptors == ["file_chunk_lexical_projection_v1"]
    assert file_chunks.resolution.projection_targets[0]["target_backend_name"] == "paradedb"
    assert isinstance(bm25.executor, GoldSearchBM25RouteExecutor)
    assert isinstance(hybrid.executor, GoldSearchHybridRouteExecutor)
    assert isinstance(file_chunks.executor, GoldSearchFileChunkRouteExecutor)
    assert hybrid.resolution.planning_v2["query_ir_v2_template"]["route_id"] == "search_hybrid.document_chunk"
    assert hybrid.resolution.planning_v2["query_ir_v2_template"]["use_dense"] is True
    assert hybrid.resolution.planning_v2["projection_ir_v2"]["representation_scope_id"] == "document_chunk"
    assert file_chunks.resolution.planning_v2["query_ir_v2_template"]["route_id"] == "search_file_chunks"
    assert file_chunks.resolution.planning_v2["projection_ir_v2"]["representation_scope_id"] == "file_chunk"


def test_split_stack_profile_resolves_concrete_supported_route_executors(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    profile = get_deployment_profile()

    bm25 = resolve_search_bm25_route_executor(table="document_chunk", profile=profile)
    hybrid = resolve_search_hybrid_route_executor(use_bm25=True, use_similarity=True, use_sparse=False, profile=profile)
    file_chunks = resolve_search_file_chunks_route_executor(profile=profile)

    assert bm25.resolution.implemented is True
    assert hybrid.resolution.implemented is True
    assert file_chunks.resolution.implemented is True
    assert bm25.resolution.profile_id == "aws_aurora_pg_opensearch_v1"
    assert hybrid.resolution.representation_scope_id == "document_chunk"
    assert file_chunks.resolution.representation_scope_id == "file_chunk"
    assert hybrid.resolution.projection_descriptors == [
        "document_chunk_lexical_projection_v1",
        "document_chunk_dense_projection_v1",
    ]
    assert [entry["target_backend_name"] for entry in hybrid.resolution.projection_targets] == [
        "opensearch",
        "opensearch",
    ]
    assert isinstance(bm25.executor, OpenSearchDocumentChunkBM25RouteExecutor)
    assert isinstance(hybrid.executor, OpenSearchDocumentChunkHybridRouteExecutor)
    assert isinstance(file_chunks.executor, OpenSearchFileChunkRouteExecutor)
    assert bm25.executor.projection_id == "document_chunk_lexical_projection_v1"
    assert hybrid.executor.projection_descriptors == (
        "document_chunk_lexical_projection_v1",
        "document_chunk_dense_projection_v1",
    )
    assert file_chunks.resolution.projection_targets[0]["authority_model"] == "file_chunk_compatibility"
    assert file_chunks.executor.projection_id == "file_chunk_lexical_projection_v1"
    assert bm25.resolution.planning_v2["query_ir_v2_template"]["strictness_policy"] == "approximate"
    assert bm25.resolution.planning_v2["projection_ir_v2"]["metadata"]["planning_surface"] == "route_resolution"
    assert hybrid.resolution.planning_v2["projection_ir_v2"]["buildability_class"] == "degraded_executable"
    assert file_chunks.resolution.planning_v2["projection_ir_v2"]["representation_scope_id"] == "file_chunk"


def test_split_stack_profile_keeps_sparse_hybrid_and_segment_bm25_non_executable(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    profile = get_deployment_profile()

    hybrid = resolve_search_hybrid_route_executor(use_bm25=True, use_similarity=True, use_sparse=True, profile=profile)
    segment_bm25 = resolve_search_bm25_route_executor(table="segment", profile=profile)

    assert hybrid.resolution.implemented is False
    assert isinstance(hybrid.executor, PlaceholderSearchHybridRouteExecutor)
    assert segment_bm25.resolution.implemented is False
    assert segment_bm25.resolution.support_state == "unsupported"
    assert isinstance(segment_bm25.executor, PlaceholderSearchBM25RouteExecutor)


def test_local_profile_route_resolution_exposes_local_scaffold_executor_ids(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "sqlite_fts5_dense_sidecar_local_v1")
    profile = get_deployment_profile()

    hybrid = resolve_search_hybrid_route_executor(use_bm25=True, use_similarity=True, use_sparse=False, profile=profile)
    bm25 = resolve_search_bm25_route_executor(table="document_chunk", profile=profile)
    file_chunks = resolve_search_file_chunks_route_executor(profile=profile)

    assert hybrid.resolution.executor_id == "sqlite_local.search_hybrid.document_chunk.v1"
    assert hybrid.resolution.implemented is True
    assert hybrid.resolution.support_state == "degraded"
    assert hybrid.resolution.representation_scope_id == "document_chunk"
    assert isinstance(hybrid.executor, SQLiteLocalSearchHybridRouteExecutor)

    assert bm25.resolution.executor_id == "sqlite_local.search_bm25.document_chunk.v1"
    assert bm25.resolution.implemented is True
    assert bm25.resolution.support_state == "degraded"
    assert bm25.resolution.representation_scope["authority_model"] == "document_segment"
    assert isinstance(bm25.executor, SQLiteLocalSearchBM25RouteExecutor)

    assert file_chunks.resolution.executor_id == "sqlite_local.search_file_chunks.v1"
    assert file_chunks.resolution.implemented is True
    assert file_chunks.resolution.support_state == "degraded"
    assert file_chunks.resolution.representation_scope_id == "file_chunk"
    assert isinstance(file_chunks.executor, SQLiteLocalSearchFileChunkRouteExecutor)


def test_local_profile_route_executors_support_plan_only(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "sqlite_fts5_dense_sidecar_local_v1")
    profile = get_deployment_profile()

    hybrid = resolve_search_hybrid_route_executor(use_bm25=True, use_similarity=True, use_sparse=False, profile=profile)
    hybrid.require_executable(allow_plan_only=True)
    hybrid_plan = hybrid.executor.execute(
        None,
        raw_query_text="vapor recovery",
        collection_ids=["c1"],
        use_bm25=True,
        use_similarity=True,
        use_sparse=False,
        return_statement=True,
    )
    assert "LOCAL_QUERYLAKE_SCAFFOLD_PLAN" in hybrid_plan
    assert "sqlite_fts5" in hybrid_plan
    assert "local_dense_sidecar" in hybrid_plan

    bm25 = resolve_search_bm25_route_executor(table="document_chunk", profile=profile)
    bm25.require_executable(allow_plan_only=True)
    bm25_plan = bm25.executor.execute(
        None,
        query="\"vapor recovery\"",
        table="document_chunk",
        sort_by="score",
        sort_dir="DESC",
        return_statement=True,
    )
    assert "LOCAL_QUERYLAKE_SCAFFOLD_PLAN" in bm25_plan.rows_or_statement
    assert bm25_plan.formatted_query == "\"vapor recovery\""

    file_chunks = resolve_search_file_chunks_route_executor(profile=profile)
    file_chunks.require_executable(allow_plan_only=True)
    file_plan = file_chunks.executor.execute(
        None,
        query="flue gas analysis",
        return_statement=True,
    )
    assert "LOCAL_QUERYLAKE_SCAFFOLD_PLAN" in file_plan.rows_or_statement
    assert file_plan.query_is_empty is False


class _FakeSession:
    def __init__(self, rows):
        self._rows = list(rows)

    def exec(self, statement):
        return list(self._rows)


def test_local_profile_bm25_executor_returns_ranked_rows(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "sqlite_fts5_dense_sidecar_local_v1")
    profile = get_deployment_profile()
    session = _FakeSession(
        [
            DocumentChunk(
                id="chunk_a",
                collection_id="c1",
                document_name="doc-a",
                text="vapor recovery system maintenance",
                md={},
                document_md={},
            ),
            DocumentChunk(
                id="chunk_b",
                collection_id="c1",
                document_name="doc-b",
                text="boiler feedwater chemistry",
                md={},
                document_md={},
            ),
        ]
    )

    bm25 = resolve_search_bm25_route_executor(table="document_chunk", profile=profile)
    bm25.require_executable()
    execution = bm25.executor.execute(
        session,
        query="vapor recovery",
        table="document_chunk",
        collection_ids=["c1"],
        sort_by="score",
        sort_dir="DESC",
        limit=5,
        offset=0,
    )
    rows = list(execution.rows_or_statement)
    assert rows[0][0] == "chunk_a"
    assert float(rows[0][1]) > 0.0


def test_local_profile_hybrid_executor_returns_fused_rows(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "sqlite_fts5_dense_sidecar_local_v1")
    profile = get_deployment_profile()
    session = _FakeSession(
        [
            DocumentChunk(
                id="chunk_a",
                collection_id="c1",
                document_name="doc-a",
                text="vapor recovery system maintenance",
                embedding=[1.0, 0.0, 0.0],
                md={},
                document_md={},
            ),
            DocumentChunk(
                id="chunk_b",
                collection_id="c1",
                document_name="doc-b",
                text="feedwater chemistry guide",
                embedding=[0.0, 1.0, 0.0],
                md={},
                document_md={},
            ),
        ]
    )

    hybrid = resolve_search_hybrid_route_executor(use_bm25=True, use_similarity=True, use_sparse=False, profile=profile)
    hybrid.require_executable()
    rows = hybrid.executor.execute(
        session,
        raw_query_text="vapor recovery",
        collection_ids=["c1"],
        use_bm25=True,
        use_similarity=True,
        use_sparse=False,
        limit_bm25=5,
        limit_similarity=5,
        bm25_weight=0.4,
        similarity_weight=0.6,
        sparse_weight=0.0,
        embedding=[1.0, 0.0, 0.0],
    )
    assert rows[0][0] == "chunk_a"
    assert float(rows[0][4]) > 0.0


def test_local_profile_hybrid_executor_rejects_hard_constraints_before_query_assembly(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "sqlite_fts5_dense_sidecar_local_v1")
    profile = get_deployment_profile()
    hybrid = resolve_search_hybrid_route_executor(use_bm25=True, use_similarity=True, use_sparse=False, profile=profile)
    hybrid.require_executable()

    with pytest.raises(QueryLakeUnsupportedFeatureError) as exc_info:
        hybrid.executor.execute(
            None,
            raw_query_text='title:"vapor recovery"',
            collection_ids=["c1"],
            use_bm25=True,
            use_similarity=True,
            use_sparse=False,
            embedding=[1.0, 0.0, 0.0],
        )

    assert exc_info.value.to_payload()["capability"] == "retrieval.lexical.hard_constraints"


def test_local_profile_file_chunk_executor_returns_ranked_rows(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "sqlite_fts5_dense_sidecar_local_v1")
    profile = get_deployment_profile()
    session = _FakeSession(
        [
            FileChunkTable(
                id="file_a",
                file_version_id="fv1",
                text="flue gas analysis procedure",
                md={},
            ),
            FileChunkTable(
                id="file_b",
                file_version_id="fv2",
                text="feedwater handbook",
                md={},
            ),
        ]
    )

    file_chunks = resolve_search_file_chunks_route_executor(profile=profile)
    file_chunks.require_executable()
    execution = file_chunks.executor.execute(
        session,
        query="flue gas analysis",
        sort_by="score",
        sort_dir="DESC",
        limit=5,
        offset=0,
    )
    rows = list(execution.rows_or_statement)
    assert rows[0][0] == "file_a"
    assert float(rows[0][1]) > 0.0


def test_local_profile_bm25_executor_rejects_hard_constraints_before_query_assembly(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "sqlite_fts5_dense_sidecar_local_v1")
    profile = get_deployment_profile()
    bm25 = resolve_search_bm25_route_executor(table="document_chunk", profile=profile)
    bm25.require_executable()

    with pytest.raises(QueryLakeUnsupportedFeatureError) as exc_info:
        bm25.executor.execute(
            None,
            query='title:"vapor recovery"',
            table="document_chunk",
            collection_ids=["c1"],
            sort_by="score",
            sort_dir="DESC",
            limit=5,
            offset=0,
        )

    assert exc_info.value.to_payload()["capability"] == "retrieval.lexical.hard_constraints"


def test_local_profile_file_chunk_executor_rejects_hard_constraints_before_query_assembly(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "sqlite_fts5_dense_sidecar_local_v1")
    profile = get_deployment_profile()
    file_chunks = resolve_search_file_chunks_route_executor(profile=profile)
    file_chunks.require_executable()

    with pytest.raises(QueryLakeUnsupportedFeatureError) as exc_info:
        file_chunks.executor.execute(
            None,
            query='path:"manual.pdf"',
            sort_by="score",
            sort_dir="DESC",
            limit=5,
            offset=0,
        )

    assert exc_info.value.to_payload()["capability"] == "retrieval.lexical.hard_constraints"


def test_route_executor_require_executable_fails_before_query_assembly(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "postgres_pgvector_light_v1")
    profile = get_deployment_profile()

    resolved = resolve_search_file_chunks_route_executor(profile=profile)
    with pytest.raises(QueryLakeUnsupportedFeatureError) as exc_info:
        resolved.require_executable()

    payload = exc_info.value.to_payload()
    assert payload["type"] == "unsupported_feature"
    assert payload["capability"] == "retrieval.lexical.bm25"
    assert payload["profile"] == "postgres_pgvector_light_v1"


def test_pgvector_light_profile_resolves_dense_only_hybrid_route(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "postgres_pgvector_light_v1")
    profile = get_deployment_profile()

    hybrid = resolve_search_hybrid_route_executor(
        use_bm25=False,
        use_similarity=True,
        use_sparse=False,
        profile=profile,
    )
    bm25 = resolve_search_bm25_route_executor(table="document_chunk", profile=profile)
    file_chunks = resolve_search_file_chunks_route_executor(profile=profile)

    assert hybrid.resolution.implemented is True
    assert hybrid.resolution.support_state == "supported"
    assert hybrid.resolution.executor_id == "pgvector.search_hybrid.document_chunk.dense_only.v1"
    assert hybrid.resolution.projection_descriptors == []
    assert hybrid.resolution.projection_targets == []
    assert isinstance(hybrid.executor, GoldSearchHybridRouteExecutor)

    assert bm25.resolution.implemented is False
    assert isinstance(bm25.executor, PlaceholderSearchBM25RouteExecutor)
    assert file_chunks.resolution.implemented is False
    assert isinstance(file_chunks.executor, PlaceholderSearchFileChunkRouteExecutor)


def test_search_module_uses_route_executor_boundary_only():
    source = Path(ROOT / "QueryLake" / "api" / "search.py").read_text()
    assert "execute_gold_bm25_search" not in source
    assert "execute_gold_document_chunk_hybrid_lanes" not in source
    assert "execute_gold_file_chunk_bm25_search" not in source
    assert "build_gold_bm25_search_plan" not in source
    assert "from ..runtime.retrieval_route_executors import" in source

from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.db_compat import QueryLakeUnsupportedFeatureError, get_deployment_profile
from QueryLake.runtime.retrieval_lanes import (
    get_retrieval_lane_binding,
    resolve_retrieval_adapter,
    resolve_retriever_builder,
)
from QueryLake.runtime.retrieval_primitives_legacy import (
    BM25RetrieverParadeDB,
    DenseRetrieverPGVector,
    FileChunkBM25RetrieverSQL,
    SparseRetrieverPGVector,
)


def test_gold_profile_resolves_expected_lane_builders(monkeypatch):
    monkeypatch.delenv("QUERYLAKE_DB_PROFILE", raising=False)
    profile = get_deployment_profile()

    assert resolve_retriever_builder("BM25RetrieverParadeDB", profile=profile) is get_retrieval_lane_binding("BM25RetrieverParadeDB").builder
    assert resolve_retriever_builder("DenseRetrieverPGVector", profile=profile) is get_retrieval_lane_binding("DenseRetrieverPGVector").builder
    assert resolve_retriever_builder("SparseRetrieverPGVector", profile=profile) is get_retrieval_lane_binding("SparseRetrieverPGVector").builder
    assert resolve_retriever_builder("FileChunkBM25RetrieverSQL", profile=profile) is get_retrieval_lane_binding("FileChunkBM25RetrieverSQL").builder


def test_gold_lane_builders_construct_current_implementations(monkeypatch):
    monkeypatch.delenv("QUERYLAKE_DB_PROFILE", raising=False)
    profile = get_deployment_profile()

    bm25 = resolve_retriever_builder("BM25RetrieverParadeDB", profile=profile)(database=object(), auth={})
    dense = resolve_retriever_builder("DenseRetrieverPGVector", profile=profile)(database=object(), auth={}, toolchain_function_caller=lambda *_args, **_kwargs: None)
    sparse = resolve_retriever_builder("SparseRetrieverPGVector", profile=profile)(database=object(), auth={}, toolchain_function_caller=lambda *_args, **_kwargs: None)
    file_bm25 = resolve_retriever_builder("FileChunkBM25RetrieverSQL", profile=profile)(database=object(), auth={})

    assert isinstance(bm25, BM25RetrieverParadeDB)
    assert isinstance(dense, DenseRetrieverPGVector)
    assert isinstance(sparse, SparseRetrieverPGVector)
    assert isinstance(file_bm25, FileChunkBM25RetrieverSQL)


def test_planned_profile_rejects_sparse_lane(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "postgres_pgvector_light_v1")
    profile = get_deployment_profile()

    with pytest.raises(QueryLakeUnsupportedFeatureError) as exc_info:
        resolve_retriever_builder("SparseRetrieverPGVector", profile=profile)

    payload = exc_info.value.to_payload()
    assert payload["type"] == "unsupported_feature"
    assert payload["capability"] == "retrieval.sparse.vector"
    assert payload["profile"] == "postgres_pgvector_light_v1"


def test_adapter_resolution_reports_profile_lane_and_backend(monkeypatch):
    monkeypatch.delenv("QUERYLAKE_DB_PROFILE", raising=False)
    profile = get_deployment_profile()
    resolution = resolve_retrieval_adapter("BM25RetrieverParadeDB", profile=profile)
    assert resolution.profile_id == "paradedb_postgres_gold_v1"
    assert resolution.lane_family == "lexical_bm25"
    assert resolution.adapter_id == "paradedb_bm25_v1"
    assert resolution.backend == "paradedb"
    assert resolution.support_state == "supported"

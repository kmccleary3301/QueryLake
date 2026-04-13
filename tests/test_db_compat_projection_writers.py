from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.db_compat import DEPLOYMENT_PROFILES
from QueryLake.runtime.projection_writers import (
    get_projection_writer_runtime,
    resolve_projection_writer,
)


def test_gold_projection_writer_runtime_executes_locally():
    resolution = resolve_projection_writer(
        "document_chunk_lexical_projection_v1",
        profile=DEPLOYMENT_PROFILES["paradedb_postgres_gold_v1"],
    )
    runtime = get_projection_writer_runtime(resolution)
    result = runtime.execute(
        database=None,
        projection_id="document_chunk_lexical_projection_v1",
        projection_version="v1",
        lane_family="lexical",
        adapter_backend="paradedb",
        authority_reference={},
        request_metadata={},
        invalidated_by=["force_rebuild_requested"],
    )
    assert result.implemented is True
    assert result.mode == "rebuild"
    assert result.build_revision == "v1:lexical"
    assert result.metadata["adapter_backend"] == "paradedb"


def test_split_stack_projection_writer_runtime_stays_placeholder():
    resolution = resolve_projection_writer(
        "segment_graph_projection_v1",
        profile=DEPLOYMENT_PROFILES["aws_aurora_pg_opensearch_v1"],
    )
    runtime = get_projection_writer_runtime(resolution)
    result = runtime.execute(
        database=None,
        projection_id="segment_graph_projection_v1",
        projection_version="v1",
        lane_family="graph",
        adapter_backend="opensearch",
        authority_reference={},
        request_metadata={},
        invalidated_by=[],
    )
    assert result.implemented is False
    assert result.mode == "planned"
    assert result.build_revision is None
    assert "not implemented" in str(result.notes or "").lower()


def test_projection_writer_resolution_respects_lane_override():
    resolution = resolve_projection_writer(
        "segment_lexical_projection_v1",
        profile=DEPLOYMENT_PROFILES["paradedb_postgres_gold_v1"],
        lane_family="dense",
    )
    assert resolution.lane_family == "dense"
    assert resolution.writer_id == "gold.projection_writer.dense.v1"
    assert resolution.backend == "pgvector_halfvec"


def test_split_stack_lexical_projection_writer_resolution_is_real(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    resolution = resolve_projection_writer(
        "document_chunk_lexical_projection_v1",
        profile=DEPLOYMENT_PROFILES["aws_aurora_pg_opensearch_v1"],
    )
    assert resolution.implemented is True
    assert resolution.mode == "rebuild"
    assert resolution.backend == "opensearch"
    runtime = get_projection_writer_runtime(resolution)
    assert runtime.implemented is True


def test_split_stack_file_chunk_lexical_projection_writer_resolution_is_real(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    resolution = resolve_projection_writer(
        "file_chunk_lexical_projection_v1",
        profile=DEPLOYMENT_PROFILES["aws_aurora_pg_opensearch_v1"],
    )
    assert resolution.implemented is True
    assert resolution.mode == "rebuild"
    assert resolution.backend == "opensearch"
    runtime = get_projection_writer_runtime(resolution)
    assert runtime.implemented is True


def test_split_stack_dense_projection_writer_resolution_is_real(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")
    resolution = resolve_projection_writer(
        "document_chunk_dense_projection_v1",
        profile=DEPLOYMENT_PROFILES["aws_aurora_pg_opensearch_v1"],
    )
    assert resolution.implemented is True
    assert resolution.mode == "rebuild"
    assert resolution.backend == "opensearch"
    runtime = get_projection_writer_runtime(resolution)
    assert runtime.implemented is True


def test_split_stack_segment_lexical_projection_writer_resolution_is_real(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    resolution = resolve_projection_writer(
        "segment_lexical_projection_v1",
        profile=DEPLOYMENT_PROFILES["aws_aurora_pg_opensearch_v1"],
    )
    assert resolution.implemented is True
    assert resolution.mode == "rebuild"
    assert resolution.backend == "opensearch"
    runtime = get_projection_writer_runtime(resolution)
    assert runtime.implemented is True


def test_split_stack_segment_dense_projection_writer_resolution_is_real(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")
    resolution = resolve_projection_writer(
        "segment_dense_projection_v1",
        profile=DEPLOYMENT_PROFILES["aws_aurora_pg_opensearch_v1"],
    )
    assert resolution.implemented is True
    assert resolution.mode == "rebuild"
    assert resolution.backend == "opensearch"
    runtime = get_projection_writer_runtime(resolution)
    assert runtime.implemented is True


def test_split_stack_segment_lexical_projection_writer_executes(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    runtime = get_projection_writer_runtime(
        resolve_projection_writer(
            "segment_lexical_projection_v1",
            profile=DEPLOYMENT_PROFILES["aws_aurora_pg_opensearch_v1"],
        )
    )
    bulk_calls = {}
    monkeypatch.setattr(
        "QueryLake.runtime.opensearch_projection_writers.fetch_projection_materialization_records",
        lambda database, target: [
            {
                "id": "seg-1",
                "text": "segment body",
                "md": {"kind": "segment"},
                "created_at": 123.0,
                "segment_type": "chunk",
                "segment_index": 7,
                "document_version_id": "dv-1",
                "parent_segment_id": None,
                "document_id": "doc-1",
                "document_name": "paper.pdf",
                "website_url": "https://example.test/paper",
                "collection_id": "col-1",
                "embedding": [0.1, 0.2],
                "embedding_sparse": {},
            }
        ],
    )
    monkeypatch.setattr(
        "QueryLake.runtime.opensearch_projection_writers._perform_opensearch_json_request",
        lambda **kwargs: {"ok": True},
    )
    def _capture_bulk(**kwargs):
        bulk_calls["payload"] = kwargs
        return {"errors": False, "items": []}
    monkeypatch.setattr(
        "QueryLake.runtime.opensearch_projection_writers._perform_opensearch_bulk",
        _capture_bulk,
    )
    result = runtime.execute(
        database=SimpleNamespace(),
        projection_id="segment_lexical_projection_v1",
        projection_version="v1",
        lane_family="lexical",
        adapter_backend="opensearch",
        authority_reference={"collection_ids": ["col-1"]},
        request_metadata={},
        invalidated_by=["force_rebuild_requested"],
    )
    assert result.implemented is True
    assert result.metadata["documents_indexed"] == 1
    assert result.metadata["materialization_target"]["projection_id"] == "segment_lexical_projection_v1"
    assert result.metadata["materialization_target"]["target_backend_name"] == "opensearch"
    bulk_docs = bulk_calls["payload"]["lines"]
    assert bulk_docs[1]["id"] == "seg-1"
    assert bulk_docs[1]["segment_type"] == "chunk"
    assert bulk_docs[1]["document_id"] == "doc-1"


def test_split_stack_segment_dense_projection_writer_executes(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "2")
    runtime = get_projection_writer_runtime(
        resolve_projection_writer(
            "segment_dense_projection_v1",
            profile=DEPLOYMENT_PROFILES["aws_aurora_pg_opensearch_v1"],
        )
    )
    bulk_calls = {}
    monkeypatch.setattr(
        "QueryLake.runtime.opensearch_projection_writers.fetch_projection_materialization_records",
        lambda database, target: [
            {
                "id": "seg-2",
                "text": "dense segment body",
                "md": {},
                "created_at": 456.0,
                "segment_type": "chunk",
                "segment_index": 8,
                "document_version_id": "dv-2",
                "parent_segment_id": None,
                "document_id": "doc-2",
                "document_name": "dense.pdf",
                "website_url": None,
                "collection_id": "col-2",
                "embedding": [0.25, 0.75],
                "embedding_sparse": {},
            }
        ],
    )
    monkeypatch.setattr(
        "QueryLake.runtime.opensearch_projection_writers._perform_opensearch_json_request",
        lambda **kwargs: {"ok": True},
    )
    def _capture_bulk(**kwargs):
        bulk_calls["payload"] = kwargs
        return {"errors": False, "items": []}
    monkeypatch.setattr(
        "QueryLake.runtime.opensearch_projection_writers._perform_opensearch_bulk",
        _capture_bulk,
    )
    result = runtime.execute(
        database=SimpleNamespace(),
        projection_id="segment_dense_projection_v1",
        projection_version="v1",
        lane_family="dense",
        adapter_backend="opensearch",
        authority_reference={"document_ids": ["doc-2"]},
        request_metadata={},
        invalidated_by=[],
    )
    assert result.implemented is True
    assert result.metadata["documents_with_dense_vectors"] == 1
    assert result.metadata["materialization_target"]["projection_id"] == "segment_dense_projection_v1"
    assert result.metadata["materialization_target"]["target_backend_name"] == "opensearch"
    bulk_docs = bulk_calls["payload"]["lines"]
    assert bulk_docs[1]["id"] == "seg-2"
    assert bulk_docs[1]["embedding"] == [0.25, 0.75]

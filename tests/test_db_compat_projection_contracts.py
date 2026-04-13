from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.projection_contracts import (
    DenseProjectionRecord,
    GraphProjectionRecord,
    LexicalProjectionRecord,
    ProjectionBuildState,
    ProjectionSnapshotMetadata,
    SparseProjectionRecord,
)


def _metadata() -> ProjectionSnapshotMetadata:
    return ProjectionSnapshotMetadata(
        projection_id="segment_projection",
        projection_version="v1",
        authority_backend="postgresql",
        projection_backend="paradedb",
        lane_family="lexical",
        build_id="build-123",
        source_document_id="doc-1",
        source_segment_id="seg-1",
        metadata={"tenant": "personal"},
    )


def test_projection_snapshot_metadata_round_trip():
    payload = _metadata().model_dump()
    restored = ProjectionSnapshotMetadata.model_validate(payload)
    assert restored.projection_id == "segment_projection"
    assert restored.metadata["tenant"] == "personal"


def test_lexical_projection_record_round_trip():
    record = LexicalProjectionRecord(
        projection=_metadata(),
        projection_record_id="lex-1",
        text="hello world",
        searchable_fields={"title": "hello"},
    )
    restored = LexicalProjectionRecord.model_validate(record.model_dump())
    assert restored.projection.lane_family == "lexical"
    assert restored.searchable_fields["title"] == "hello"


def test_dense_projection_record_round_trip():
    record = DenseProjectionRecord(
        projection=_metadata().model_copy(update={"lane_family": "dense", "projection_backend": "pgvector_halfvec"}),
        projection_record_id="dense-1",
        embedding_function="bge-m3",
        embedding_dimensions=1024,
        embedding_vector=[0.1, 0.2],
    )
    restored = DenseProjectionRecord.model_validate(record.model_dump())
    assert restored.embedding_dimensions == 1024
    assert restored.projection.projection_backend == "pgvector_halfvec"


def test_sparse_projection_record_round_trip():
    record = SparseProjectionRecord(
        projection=_metadata().model_copy(update={"lane_family": "sparse", "projection_backend": "pgvector_sparsevec"}),
        projection_record_id="sparse-1",
        embedding_function="bge-m3",
        sparse_dimensions=1024,
        sparse_vector={"indices": [1, 4], "values": [0.3, 0.8]},
    )
    restored = SparseProjectionRecord.model_validate(record.model_dump())
    assert restored.sparse_dimensions == 1024
    assert restored.sparse_vector["indices"] == [1, 4]


def test_graph_projection_record_round_trip():
    record = GraphProjectionRecord(
        projection=_metadata().model_copy(update={"lane_family": "graph", "projection_backend": "postgresql_segment_relations"}),
        projection_record_id="graph-1",
        source_segment_id="seg-1",
        target_segment_id="seg-2",
        edge_type="adjacent",
        weight=0.75,
        metadata={"window": 2},
    )
    restored = GraphProjectionRecord.model_validate(record.model_dump())
    assert restored.edge_type == "adjacent"
    assert restored.weight == 0.75
    assert restored.metadata["window"] == 2


def test_projection_build_state_round_trip():
    state = ProjectionBuildState(
        projection_id="segment_lexical_projection_v1",
        projection_version="v1",
        profile_id="paradedb_postgres_gold_v1",
        lane_family="lexical",
        target_backend="paradedb",
        status="ready",
        last_build_revision="rev-1",
        last_build_timestamp=123.0,
        metadata={"collection": "personal"},
    )
    restored = ProjectionBuildState.model_validate(state.model_dump())
    assert restored.status == "ready"
    assert restored.metadata["collection"] == "personal"

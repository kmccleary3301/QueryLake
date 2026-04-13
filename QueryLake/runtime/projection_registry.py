from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class ProjectionDescriptor:
    projection_id: str
    lane_family: str
    record_schema: str
    authority_model: str
    source_scope: str
    target_backend_family: str
    notes: str

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


PROJECTION_DESCRIPTORS: Dict[str, ProjectionDescriptor] = {
    "file_chunk_lexical_projection_v1": ProjectionDescriptor(
        projection_id="file_chunk_lexical_projection_v1",
        lane_family="lexical",
        record_schema="LexicalProjectionRecord",
        authority_model="file_chunk_compatibility",
        source_scope="file_chunk",
        target_backend_family="lexical_index",
        notes="Compatibility lexical projection over legacy/gold file_chunk retrieval records.",
    ),
    "document_chunk_lexical_projection_v1": ProjectionDescriptor(
        projection_id="document_chunk_lexical_projection_v1",
        lane_family="lexical",
        record_schema="LexicalProjectionRecord",
        authority_model="document_chunk_compatibility",
        source_scope="document_chunk",
        target_backend_family="lexical_index",
        notes="Compatibility lexical projection over legacy/gold document_chunk retrieval records.",
    ),
    "document_chunk_dense_projection_v1": ProjectionDescriptor(
        projection_id="document_chunk_dense_projection_v1",
        lane_family="dense",
        record_schema="DenseProjectionRecord",
        authority_model="document_chunk_compatibility",
        source_scope="document_chunk",
        target_backend_family="dense_index",
        notes="Compatibility dense projection over legacy/gold document_chunk retrieval records.",
    ),
    "document_chunk_sparse_projection_v1": ProjectionDescriptor(
        projection_id="document_chunk_sparse_projection_v1",
        lane_family="sparse",
        record_schema="SparseProjectionRecord",
        authority_model="document_chunk_compatibility",
        source_scope="document_chunk",
        target_backend_family="sparse_index",
        notes="Compatibility sparse projection over legacy/gold document_chunk retrieval records.",
    ),
    "segment_lexical_projection_v1": ProjectionDescriptor(
        projection_id="segment_lexical_projection_v1",
        lane_family="lexical",
        record_schema="LexicalProjectionRecord",
        authority_model="document_segment",
        source_scope="segment",
        target_backend_family="lexical_index",
        notes="Canonical lexical projection for segment/document text retrieval.",
    ),
    "segment_dense_projection_v1": ProjectionDescriptor(
        projection_id="segment_dense_projection_v1",
        lane_family="dense",
        record_schema="DenseProjectionRecord",
        authority_model="document_segment",
        source_scope="segment",
        target_backend_family="dense_index",
        notes="Canonical dense vector projection for segment retrieval.",
    ),
    "segment_sparse_projection_v1": ProjectionDescriptor(
        projection_id="segment_sparse_projection_v1",
        lane_family="sparse",
        record_schema="SparseProjectionRecord",
        authority_model="document_segment",
        source_scope="segment",
        target_backend_family="sparse_index",
        notes="Canonical sparse vector projection for segment retrieval.",
    ),
    "segment_graph_projection_v1": ProjectionDescriptor(
        projection_id="segment_graph_projection_v1",
        lane_family="graph",
        record_schema="GraphProjectionRecord",
        authority_model="document_segment",
        source_scope="segment",
        target_backend_family="graph_index",
        notes="Canonical graph/segment-edge projection for traversal and expansion.",
    ),
}


def list_projection_descriptors() -> Dict[str, ProjectionDescriptor]:
    return dict(PROJECTION_DESCRIPTORS)


def get_projection_descriptor(projection_id: str) -> ProjectionDescriptor:
    descriptor = PROJECTION_DESCRIPTORS.get(str(projection_id))
    if descriptor is None:
        available = ", ".join(sorted(PROJECTION_DESCRIPTORS.keys()))
        raise ValueError(f"Unknown projection_id={projection_id}; available={available}")
    return descriptor

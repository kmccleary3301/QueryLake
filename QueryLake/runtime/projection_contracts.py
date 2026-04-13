from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


class ProjectionSnapshotMetadata(BaseModel):
    projection_id: str
    projection_version: str
    authority_backend: str
    projection_backend: str
    lane_family: str
    schema_version: int = 1
    build_id: Optional[str] = None
    source_document_id: Optional[str] = None
    source_segment_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


ProjectionStatus = Literal["absent", "building", "ready", "stale", "failed"]


class ProjectionBuildState(BaseModel):
    projection_id: str
    projection_version: str
    profile_id: str
    lane_family: str
    target_backend: str
    status: ProjectionStatus = "absent"
    last_build_revision: Optional[str] = None
    last_build_timestamp: Optional[float] = None
    error_summary: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProjectionAuthorityReference(BaseModel):
    authority_model: str
    document_ids: list[str] = Field(default_factory=list)
    segment_ids: list[str] = Field(default_factory=list)
    collection_ids: list[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProjectionMaterializationTarget(BaseModel):
    projection_id: str
    projection_version: str
    lane_family: str
    authority_model: str
    source_scope: str
    record_schema: str
    target_backend_family: str
    target_backend_name: str
    authority_reference: ProjectionAuthorityReference
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentChunkMaterializationRecord(BaseModel):
    id: str
    creation_timestamp: float = 0.0
    collection_type: str = ""
    document_id: str = ""
    document_chunk_number: int = 0
    document_integrity: str = ""
    collection_id: str = ""
    document_name: str = ""
    website_url: str = ""
    private: bool = False
    md: Dict[str, Any] = Field(default_factory=dict)
    document_md: Dict[str, Any] = Field(default_factory=dict)
    text: str = ""
    embedding: Optional[list[float]] = None
    embedding_sparse: Dict[str, Any] = Field(default_factory=dict)


class FileChunkMaterializationRecord(BaseModel):
    id: str
    text: str = ""
    md: Dict[str, Any] = Field(default_factory=dict)
    created_at: float = 0.0
    file_version_id: str = ""
    created_by: str = ""
    collection_id: str = ""


class SegmentMaterializationRecord(BaseModel):
    id: str
    text: str = ""
    md: Dict[str, Any] = Field(default_factory=dict)
    created_at: float = 0.0
    segment_type: str = ""
    segment_index: int = 0
    document_version_id: str = ""
    parent_segment_id: Optional[str] = None
    document_id: str = ""
    document_name: str = ""
    website_url: Optional[str] = None
    collection_id: str = ""
    embedding: Optional[list[float]] = None
    embedding_sparse: Dict[str, Any] = Field(default_factory=dict)


class LexicalProjectionRecord(BaseModel):
    projection: ProjectionSnapshotMetadata
    projection_record_id: str
    text: str
    searchable_fields: Dict[str, Any] = Field(default_factory=dict)


class DenseProjectionRecord(BaseModel):
    projection: ProjectionSnapshotMetadata
    projection_record_id: str
    embedding_function: str
    embedding_dimensions: int
    embedding_vector: Optional[list[float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SparseProjectionRecord(BaseModel):
    projection: ProjectionSnapshotMetadata
    projection_record_id: str
    embedding_function: str
    sparse_dimensions: int
    sparse_vector: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphProjectionRecord(BaseModel):
    projection: ProjectionSnapshotMetadata
    projection_record_id: str
    source_segment_id: str
    target_segment_id: str
    edge_type: str
    weight: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

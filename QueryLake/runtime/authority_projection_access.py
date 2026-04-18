from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Protocol, Sequence, runtime_checkable

from sqlmodel import Session, select

from QueryLake.database.sql_db_tables import (
    DocumentChunk,
    document_raw as DocumentRaw,
    document_segment as DocumentSegment,
    document_version as DocumentVersion,
    file as FileTable,
    file_chunk as FileChunkTable,
    file_version as FileVersionTable,
)
from QueryLake.runtime.projection_contracts import (
    DocumentChunkMaterializationRecord,
    FileChunkMaterializationRecord,
    ProjectionAuthorityReference,
    ProjectionMaterializationTarget,
    SegmentMaterializationRecord,
)
from QueryLake.runtime.projection_registry import ProjectionDescriptor, get_projection_descriptor
from QueryLake.runtime.document_decomposition import (
    DOCUMENT_CHUNK_COMPATIBILITY_CONTRACT,
    fetch_document_chunk_authority_provenance,
)


FILE_CHUNK_COMPAT_LEXICAL_PROJECTION_ID = "file_chunk_lexical_projection_v1"
DOCUMENT_CHUNK_COMPAT_LEXICAL_PROJECTION_ID = "document_chunk_lexical_projection_v1"
DOCUMENT_CHUNK_COMPAT_DENSE_PROJECTION_ID = "document_chunk_dense_projection_v1"
DOCUMENT_CHUNK_COMPAT_SPARSE_PROJECTION_ID = "document_chunk_sparse_projection_v1"
SEGMENT_LEXICAL_PROJECTION_ID = "segment_lexical_projection_v1"
SEGMENT_DENSE_PROJECTION_ID = "segment_dense_projection_v1"
SEGMENT_SPARSE_PROJECTION_ID = "segment_sparse_projection_v1"
SEGMENT_GRAPH_PROJECTION_ID = "segment_graph_projection_v1"

DOCUMENT_CHUNK_TUPLE_FIELDS = (
    "id",
    "creation_timestamp",
    "collection_type",
    "document_id",
    "document_chunk_number",
    "document_integrity",
    "collection_id",
    "document_name",
    "website_url",
    "private",
    "authority_segment_id",
    "md",
    "document_md",
    "text",
)

FILE_CHUNK_TUPLE_FIELDS = (
    "id",
    "text",
    "md",
    "created_at",
    "file_version_id",
)

SEGMENT_TUPLE_FIELDS = (
    "id",
    "text",
    "md",
    "created_at",
    "segment_type",
    "segment_index",
    "document_version_id",
    "parent_segment_id",
    "document_id",
    "document_name",
    "website_url",
    "collection_id",
    "embedding",
    "embedding_sparse",
)


@dataclass(frozen=True)
class ProjectionHydrationTarget:
    projection_id: str
    authority_model: str
    source_scope: str
    record_ids: tuple[str, ...]
    descriptor_notes: str

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProjectionSourceFetchTarget:
    projection_id: str
    authority_model: str
    source_scope: str
    collection_ids: tuple[str, ...]
    document_ids: tuple[str, ...]
    segment_ids: tuple[str, ...]
    metadata: Dict[str, Any]
    descriptor_notes: str

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


@runtime_checkable
class ProjectionHydratorProtocol(Protocol):
    def hydrate(self, database: Session, record_ids: Sequence[str]) -> Dict[str, tuple[Any, ...]]: ...


@runtime_checkable
class ProjectionSourceFetcherProtocol(Protocol):
    def fetch(self, database: Session, target: ProjectionSourceFetchTarget) -> List[Any]: ...


class DocumentChunkCompatibilityHydrator:
    def hydrate(self, database: Session, record_ids: Sequence[str]) -> Dict[str, tuple[Any, ...]]:
        if len(record_ids) == 0:
            return {}
        rows = list(database.exec(select(DocumentChunk).where(DocumentChunk.id.in_(list(record_ids)))))
        return {
            str(row.id): tuple(getattr(row, field_name) for field_name in DOCUMENT_CHUNK_TUPLE_FIELDS)
            for row in rows
        }


class FileChunkCompatibilityHydrator:
    def hydrate(self, database: Session, record_ids: Sequence[str]) -> Dict[str, tuple[Any, ...]]:
        if len(record_ids) == 0:
            return {}
        rows = list(database.exec(select(FileChunkTable).where(FileChunkTable.id.in_(list(record_ids)))))
        return {
            str(row.id): tuple(getattr(row, field_name) for field_name in FILE_CHUNK_TUPLE_FIELDS)
            for row in rows
        }


class DocumentSegmentAuthorityHydrator:
    def hydrate(self, database: Session, record_ids: Sequence[str]) -> Dict[str, tuple[Any, ...]]:
        if len(record_ids) == 0:
            return {}
        statement = (
            select(
                DocumentSegment.id,
                DocumentSegment.text,
                DocumentSegment.md,
                DocumentSegment.created_at,
                DocumentSegment.segment_type,
                DocumentSegment.segment_index,
                DocumentSegment.document_version_id,
                DocumentSegment.parent_segment_id,
                DocumentVersion.document_id,
                DocumentRaw.file_name,
                DocumentRaw.website_url,
                DocumentRaw.document_collection_id,
                DocumentSegment.embedding,
                DocumentSegment.embedding_sparse,
            )
            .join(DocumentVersion, DocumentVersion.id == DocumentSegment.document_version_id)
            .join(DocumentRaw, DocumentRaw.id == DocumentVersion.document_id)
            .where(DocumentSegment.id.in_(list(record_ids)))
        )
        rows = list(database.exec(statement))
        return {
            str(row[0]): tuple(row[index] for index in range(len(SEGMENT_TUPLE_FIELDS)))
            for row in rows
        }


class DocumentChunkCompatibilitySourceFetcher:
    def fetch(self, database: Session, target: ProjectionSourceFetchTarget) -> List[Any]:
        statement = select(DocumentChunk)
        if len(target.collection_ids) > 0:
            statement = statement.where(DocumentChunk.collection_id.in_(list(target.collection_ids)))
        if len(target.document_ids) > 0:
            statement = statement.where(DocumentChunk.document_id.in_(list(target.document_ids)))
        return list(database.exec(statement))


class FileChunkCompatibilitySourceFetcher:
    def fetch(self, database: Session, target: ProjectionSourceFetchTarget) -> List[Any]:
        statement = (
            select(
                FileChunkTable.id,
                FileChunkTable.text,
                FileChunkTable.md,
                FileChunkTable.created_at,
                FileChunkTable.file_version_id,
                FileTable.created_by,
                FileTable.collection_id,
            )
            .join(FileVersionTable, FileVersionTable.id == FileChunkTable.file_version_id)
            .join(FileTable, FileTable.id == FileVersionTable.file_id)
        )
        if len(target.collection_ids) > 0:
            statement = statement.where(FileTable.collection_id.in_(list(target.collection_ids)))
        return list(database.exec(statement))


class DocumentSegmentAuthoritySourceFetcher:
    def fetch(self, database: Session, target: ProjectionSourceFetchTarget) -> List[Any]:
        statement = (
            select(
                DocumentSegment.id,
                DocumentSegment.text,
                DocumentSegment.md,
                DocumentSegment.created_at,
                DocumentSegment.segment_type,
                DocumentSegment.segment_index,
                DocumentSegment.document_version_id,
                DocumentSegment.parent_segment_id,
                DocumentVersion.document_id,
                DocumentRaw.file_name,
                DocumentRaw.website_url,
                DocumentRaw.document_collection_id,
                DocumentSegment.embedding,
                DocumentSegment.embedding_sparse,
            )
            .join(DocumentVersion, DocumentVersion.id == DocumentSegment.document_version_id)
            .join(DocumentRaw, DocumentRaw.id == DocumentVersion.document_id)
        )
        if len(target.collection_ids) > 0:
            statement = statement.where(DocumentRaw.document_collection_id.in_(list(target.collection_ids)))
        if len(target.document_ids) > 0:
            statement = statement.where(DocumentVersion.document_id.in_(list(target.document_ids)))
        if len(target.segment_ids) > 0:
            statement = statement.where(DocumentSegment.id.in_(list(target.segment_ids)))
        return list(database.exec(statement))


def build_projection_hydration_target(
    *,
    projection_id: str,
    record_ids: Sequence[str],
    descriptor: Optional[ProjectionDescriptor] = None,
) -> ProjectionHydrationTarget:
    effective_descriptor = descriptor or get_projection_descriptor(projection_id)
    return ProjectionHydrationTarget(
        projection_id=effective_descriptor.projection_id,
        authority_model=effective_descriptor.authority_model,
        source_scope=effective_descriptor.source_scope,
        record_ids=tuple(str(record_id) for record_id in record_ids),
        descriptor_notes=effective_descriptor.notes,
    )


def build_projection_source_fetch_target(
    *,
    projection_id: str,
    authority_reference: Optional[Dict[str, Any]] = None,
    descriptor: Optional[ProjectionDescriptor] = None,
) -> ProjectionSourceFetchTarget:
    effective_descriptor = descriptor or get_projection_descriptor(projection_id)
    authority_reference = dict(authority_reference or {})
    return ProjectionSourceFetchTarget(
        projection_id=effective_descriptor.projection_id,
        authority_model=effective_descriptor.authority_model,
        source_scope=effective_descriptor.source_scope,
        collection_ids=tuple(str(value) for value in list(authority_reference.get("collection_ids") or [])),
        document_ids=tuple(str(value) for value in list(authority_reference.get("document_ids") or [])),
        segment_ids=tuple(str(value) for value in list(authority_reference.get("segment_ids") or [])),
        metadata=dict(authority_reference.get("metadata") or {}),
        descriptor_notes=effective_descriptor.notes,
    )


def build_projection_materialization_target(
    *,
    projection_id: str,
    projection_version: str = "v1",
    authority_reference: Optional[Dict[str, Any] | ProjectionAuthorityReference] = None,
    target_backend_name: str = "unknown",
    metadata: Optional[Dict[str, Any]] = None,
    descriptor: Optional[ProjectionDescriptor] = None,
) -> ProjectionMaterializationTarget:
    effective_descriptor = descriptor or get_projection_descriptor(projection_id)
    if isinstance(authority_reference, ProjectionAuthorityReference):
        effective_authority_reference = authority_reference
    else:
        normalized_authority_reference = {
            "authority_model": effective_descriptor.authority_model,
            "document_ids": [],
            "segment_ids": [],
            "collection_ids": [],
            "metadata": {},
        }
        if authority_reference:
            normalized_authority_reference.update(dict(authority_reference))
        effective_authority_reference = ProjectionAuthorityReference.model_validate(
            normalized_authority_reference
        )
    return ProjectionMaterializationTarget(
        projection_id=effective_descriptor.projection_id,
        projection_version=str(projection_version),
        lane_family=effective_descriptor.lane_family,
        authority_model=effective_descriptor.authority_model,
        source_scope=effective_descriptor.source_scope,
        record_schema=effective_descriptor.record_schema,
        target_backend_family=effective_descriptor.target_backend_family,
        target_backend_name=str(target_backend_name or "unknown"),
        authority_reference=effective_authority_reference,
        metadata=dict(metadata or {}),
    )


def resolve_projection_hydrator(
    projection_id: str,
    *,
    descriptor: Optional[ProjectionDescriptor] = None,
) -> ProjectionHydratorProtocol:
    effective_descriptor = descriptor or get_projection_descriptor(projection_id)
    if effective_descriptor.authority_model == "document_chunk_compatibility":
        return DocumentChunkCompatibilityHydrator()
    if effective_descriptor.authority_model == "file_chunk_compatibility":
        return FileChunkCompatibilityHydrator()
    if effective_descriptor.authority_model == "document_segment":
        return DocumentSegmentAuthorityHydrator()
    raise ValueError(
        "No projection hydrator is registered for "
        f"projection_id={effective_descriptor.projection_id} authority_model={effective_descriptor.authority_model}"
    )


def resolve_projection_source_fetcher(
    projection_id: str,
    *,
    descriptor: Optional[ProjectionDescriptor] = None,
) -> ProjectionSourceFetcherProtocol:
    effective_descriptor = descriptor or get_projection_descriptor(projection_id)
    if effective_descriptor.authority_model == "document_chunk_compatibility":
        return DocumentChunkCompatibilitySourceFetcher()
    if effective_descriptor.authority_model == "file_chunk_compatibility":
        return FileChunkCompatibilitySourceFetcher()
    if effective_descriptor.authority_model == "document_segment":
        return DocumentSegmentAuthoritySourceFetcher()
    raise ValueError(
        "No projection source fetcher is registered for "
        f"projection_id={effective_descriptor.projection_id} authority_model={effective_descriptor.authority_model}"
    )


def hydrate_projection_rows(
    database: Session,
    *,
    projection_id: str,
    record_ids: Sequence[str],
) -> Dict[str, tuple[Any, ...]]:
    target = build_projection_hydration_target(
        projection_id=projection_id,
        record_ids=record_ids,
    )
    return hydrate_projection_target(database, target=target)


def fetch_projection_source_rows(
    database: Session,
    *,
    projection_id: str,
    authority_reference: Optional[Dict[str, Any]] = None,
) -> List[Any]:
    target = build_projection_source_fetch_target(
        projection_id=projection_id,
        authority_reference=authority_reference,
    )
    return fetch_projection_source_target(database, target=target)


def fetch_projection_materialization_rows(
    database: Session,
    *,
    target: ProjectionMaterializationTarget,
) -> List[Any]:
    source_target = build_projection_source_fetch_target(
        projection_id=target.projection_id,
        authority_reference=target.authority_reference.model_dump(),
    )
    return fetch_projection_source_target(database, target=source_target)


def _normalize_document_chunk_materialization_record(row: Any) -> DocumentChunkMaterializationRecord:
    if isinstance(row, DocumentChunkMaterializationRecord):
        return row
    if isinstance(row, DocumentChunk):
        return DocumentChunkMaterializationRecord(
            id=str(row.id or ""),
            creation_timestamp=float(row.creation_timestamp or 0.0),
            collection_type=str(row.collection_type or ""),
            document_id=str(row.document_id or ""),
            document_chunk_number=int(row.document_chunk_number or 0),
            document_integrity=str(row.document_integrity or ""),
            collection_id=str(row.collection_id or ""),
            document_name=str(row.document_name or ""),
            website_url=str(row.website_url or ""),
            private=bool(row.private),
            authority_segment_id=None if getattr(row, "authority_segment_id", None) is None else str(getattr(row, "authority_segment_id")),
            compatibility_contract=DOCUMENT_CHUNK_COMPATIBILITY_CONTRACT,
            md=dict(row.md or {}),
            document_md=dict(row.document_md or {}),
            text=str(row.text or ""),
            embedding=list(getattr(row, "embedding", None) or []) or None,
            embedding_sparse=dict(getattr(row, "embedding_sparse", None) or {}),
        )
    if isinstance(row, dict):
        raw = dict(row)
        raw.setdefault("compatibility_contract", DOCUMENT_CHUNK_COMPATIBILITY_CONTRACT)
        return DocumentChunkMaterializationRecord.model_validate(raw)
    if isinstance(row, tuple):
        raw = dict(zip(DOCUMENT_CHUNK_TUPLE_FIELDS, row))
        raw.setdefault("compatibility_contract", DOCUMENT_CHUNK_COMPATIBILITY_CONTRACT)
        return DocumentChunkMaterializationRecord.model_validate(raw)
    raise TypeError(f"Unsupported document_chunk materialization row type: {type(row)!r}")


def _normalize_file_chunk_materialization_record(row: Any) -> FileChunkMaterializationRecord:
    if isinstance(row, FileChunkMaterializationRecord):
        return row
    if isinstance(row, FileChunkTable):
        return FileChunkMaterializationRecord(
            id=str(row.id or ""),
            text=str(row.text or ""),
            md=dict(row.md or {}),
            created_at=float(row.created_at or 0.0),
            file_version_id=str(row.file_version_id or ""),
            created_by=str(getattr(row, "created_by", "") or ""),
            collection_id=str(getattr(row, "collection_id", "") or ""),
        )
    if isinstance(row, dict):
        return FileChunkMaterializationRecord.model_validate(row)
    if isinstance(row, tuple):
        (
            row_id,
            text_value,
            md_value,
            created_at,
            file_version_id,
            created_by,
            collection_id,
        ) = row
        return FileChunkMaterializationRecord(
            id=str(row_id or ""),
            text=str(text_value or ""),
            md=dict(md_value or {}),
            created_at=float(created_at or 0.0),
            file_version_id=str(file_version_id or ""),
            created_by=str(created_by or ""),
            collection_id=str(collection_id or ""),
        )
    raise TypeError(f"Unsupported file_chunk materialization row type: {type(row)!r}")


def _normalize_segment_materialization_record(row: Any) -> SegmentMaterializationRecord:
    if isinstance(row, SegmentMaterializationRecord):
        return row
    if isinstance(row, dict):
        return SegmentMaterializationRecord.model_validate(row)
    if isinstance(row, tuple):
        raw = dict(zip(SEGMENT_TUPLE_FIELDS, row))
        return SegmentMaterializationRecord.model_validate(raw)
    raise TypeError(f"Unsupported segment materialization row type: {type(row)!r}")


def fetch_projection_materialization_records(
    database: Session,
    *,
    target: ProjectionMaterializationTarget,
) -> List[
    DocumentChunkMaterializationRecord
    | FileChunkMaterializationRecord
    | SegmentMaterializationRecord
]:
    rows = fetch_projection_materialization_rows(database, target=target)
    if target.source_scope == "document_chunk":
        return [_normalize_document_chunk_materialization_record(row) for row in rows]
    if target.source_scope == "file_chunk":
        return [_normalize_file_chunk_materialization_record(row) for row in rows]
    if target.source_scope == "segment":
        return [_normalize_segment_materialization_record(row) for row in rows]
    raise AssertionError(f"Unsupported projection materialization source_scope='{target.source_scope}'.")


def fetch_document_chunk_materialization_provenance(
    database: Session,
    *,
    records: Sequence[DocumentChunkMaterializationRecord | dict | tuple | DocumentChunk],
) -> List[Dict[str, Any]]:
    normalized_records = [_normalize_document_chunk_materialization_record(row) for row in records]
    requested_chunk_ids = {record.id for record in normalized_records}
    requested_document_ids = []
    seen_document_ids = set()
    for record in normalized_records:
        if not record.document_id:
            continue
        if record.document_id in seen_document_ids:
            continue
        seen_document_ids.add(record.document_id)
        requested_document_ids.append(record.document_id)

    provenance_by_chunk_id: Dict[str, Dict[str, Any]] = {}
    for document_id in requested_document_ids:
        payload = fetch_document_chunk_authority_provenance(database, document_id=document_id)
        for row in payload.get("records", []):
            chunk_id = str(row.get("chunk_id") or "")
            if chunk_id and chunk_id in requested_chunk_ids:
                provenance_by_chunk_id[chunk_id] = dict(row)

    records_with_provenance: List[Dict[str, Any]] = []
    for record in normalized_records:
        canonical_row = dict(provenance_by_chunk_id.get(record.id) or {})
        canonical_authority_segment_id = canonical_row.get("authority_segment_id")
        records_with_provenance.append({
            "chunk_id": record.id,
            "document_id": record.document_id,
            "document_chunk_number": int(record.document_chunk_number or 0),
            "compatibility_contract": record.compatibility_contract,
            "materialized_authority_segment_id": record.authority_segment_id,
            "canonical_authority_segment_id": canonical_authority_segment_id,
            "authority_segment_consistent": canonical_authority_segment_id == record.authority_segment_id,
            "segment_view_id": canonical_row.get("segment_view_id"),
            "segment_view_alias": canonical_row.get("segment_view_alias"),
            "segment_type": canonical_row.get("segment_type"),
            "segment_index": canonical_row.get("segment_index"),
            "member_count": canonical_row.get("member_count", 0),
            "members": list(canonical_row.get("members", [])),
        })
    return records_with_provenance


def fetch_document_chunk_authority_materializations(
    database: Session,
    *,
    records: Sequence[DocumentChunkMaterializationRecord | dict | tuple | DocumentChunk],
) -> List[Dict[str, Any]]:
    normalized_records = [_normalize_document_chunk_materialization_record(row) for row in records]
    authority_segment_ids: List[str] = []
    seen_segment_ids = set()
    for record in normalized_records:
        authority_segment_id = record.authority_segment_id
        if not authority_segment_id:
            continue
        if authority_segment_id in seen_segment_ids:
            continue
        seen_segment_ids.add(authority_segment_id)
        authority_segment_ids.append(authority_segment_id)

    hydrated_segments = hydrate_projection_rows(
        database,
        projection_id=SEGMENT_DENSE_PROJECTION_ID,
        record_ids=authority_segment_ids,
    ) if authority_segment_ids else {}
    normalized_segments = {
        str(segment_id): _normalize_segment_materialization_record(row)
        for segment_id, row in hydrated_segments.items()
    }

    payload: List[Dict[str, Any]] = []
    for record in normalized_records:
        segment = normalized_segments.get(str(record.authority_segment_id)) if record.authority_segment_id else None
        payload.append({
            "chunk_id": record.id,
            "document_id": record.document_id,
            "document_chunk_number": int(record.document_chunk_number or 0),
            "compatibility_contract": record.compatibility_contract,
            "materialized_authority_segment_id": record.authority_segment_id,
            "authority_segment_resolved": segment is not None,
            "segment_materialization": None if segment is None else segment.model_dump(),
        })
    return payload



def hydrate_projection_target(
    database: Session,
    *,
    target: ProjectionHydrationTarget,
) -> Dict[str, tuple[Any, ...]]:
    descriptor = get_projection_descriptor(target.projection_id)
    hydrator = resolve_projection_hydrator(target.projection_id, descriptor=descriptor)
    return hydrator.hydrate(database, target.record_ids)


def fetch_projection_source_target(
    database: Session,
    *,
    target: ProjectionSourceFetchTarget,
) -> List[Any]:
    descriptor = get_projection_descriptor(target.projection_id)
    fetcher = resolve_projection_source_fetcher(target.projection_id, descriptor=descriptor)
    return fetcher.fetch(database, target)

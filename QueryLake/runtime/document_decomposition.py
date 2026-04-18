from __future__ import annotations

from dataclasses import dataclass
from time import time
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from sqlmodel import Session, select

from QueryLake.database.sql_db_tables import (
    DocumentChunk,
    document_artifact as DocumentArtifact,
    document_raw,
    document_segment as DocumentSegment,
    document_segment_member as DocumentSegmentMember,
    document_segment_view as DocumentSegmentView,
    document_unit as DocumentUnit,
    document_unit_view as DocumentUnitView,
    document_version as DocumentVersion,
)
from QueryLake.runtime.content_fingerprint import content_fingerprint

DEFAULT_LOCAL_TEXT_VIEW_ALIAS = "default_local_text"
LEGACY_CHUNK_BACKFILL_UNIT_RECIPE_ID = "legacy_chunk_backfill_units_v1"
LEGACY_CHUNK_BACKFILL_SEGMENT_RECIPE_ID = "legacy_chunk_backfill_segments_v1"
LEGACY_CHUNK_BACKFILL_ARTIFACT_TYPE = "legacy_chunk_backfill"
DOCUMENT_CHUNK_COMPATIBILITY_CONTRACT = "canonical_segment_compat_projection_v1"

DECOMPOSITION_STATUS_EMPTY = "empty"
DECOMPOSITION_STATUS_CANONICAL = "canonical"
DECOMPOSITION_STATUS_BACKFILLED_COMPAT = "backfilled_compat"
DECOMPOSITION_STATUS_LEGACY_ONLY = "legacy_only"
DECOMPOSITION_STATUS_PARTIAL = "partial"
DECOMPOSITION_STATUS_CHUNKS_MISSING_AUTHORITY_LINKS = "chunks_missing_authority_links"
DECOMPOSITION_STATUS_SEGMENTS_MISSING_DEFAULT_VIEW = "segments_missing_default_view"
DECOMPOSITION_STATUS_UNKNOWN = "unknown"

DECOMPOSITION_STATUS_ORDER = [
    DECOMPOSITION_STATUS_EMPTY,
    DECOMPOSITION_STATUS_CANONICAL,
    DECOMPOSITION_STATUS_BACKFILLED_COMPAT,
    DECOMPOSITION_STATUS_LEGACY_ONLY,
    DECOMPOSITION_STATUS_PARTIAL,
    DECOMPOSITION_STATUS_CHUNKS_MISSING_AUTHORITY_LINKS,
    DECOMPOSITION_STATUS_SEGMENTS_MISSING_DEFAULT_VIEW,
    DECOMPOSITION_STATUS_UNKNOWN,
]


@dataclass
class DocumentDecompositionBackfillPayload:
    unit_view: DocumentUnitView
    units: List[DocumentUnit]
    segment_view: DocumentSegmentView
    segments: List[DocumentSegment]
    members: List[DocumentSegmentMember]
    chunk_links: List[Tuple[str, str]]


def _config_hash(payload: Dict[str, Any], *, salt: str) -> str:
    return content_fingerprint(text="", md=payload, salt=salt)


def infer_anchor_from_md(md: Dict[str, Any] | None) -> Tuple[Optional[str], Dict[str, Any]]:
    payload = dict(md or {})
    if "page" in payload:
        anchor = {
            "page": payload.get("page"),
        }
        if payload.get("location_link_firefox") is not None:
            anchor["location_link_firefox"] = payload.get("location_link_firefox")
        if payload.get("location_link_chrome") is not None:
            anchor["location_link_chrome"] = payload.get("location_link_chrome")
        return "page_ref", anchor
    if "line" in payload:
        return "line_ref", {"line": payload.get("line")}
    return None, {}


def _normalize_chunk_rows(chunk_rows: Sequence[Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for row in chunk_rows:
        if isinstance(row, dict):
            item = dict(row)
        else:
            item = {
                "id": getattr(row, "id"),
                "document_chunk_number": getattr(row, "document_chunk_number", 0),
                "text": getattr(row, "text", "") or "",
                "md": dict(getattr(row, "md", {}) or {}),
                "authority_segment_id": getattr(row, "authority_segment_id", None),
            }
        item["document_chunk_number"] = int(item.get("document_chunk_number", 0) or 0)
        item["text"] = str(item.get("text", "") or "")
        item["md"] = dict(item.get("md", {}) or {})
        rows.append(item)
    rows.sort(key=lambda row: (int(row.get("document_chunk_number", 0)), str(row.get("id") or "")))
    return rows


def build_chunk_backfill_payload(
    *,
    document_version_id: str,
    artifact_id: str,
    chunk_rows: Sequence[Any],
) -> DocumentDecompositionBackfillPayload:
    normalized = _normalize_chunk_rows(chunk_rows)
    unit_view_config = {
        "source": "document_chunk",
        "unit_kind": "legacy_document_chunk",
    }
    unit_view = DocumentUnitView(
        document_version_id=document_version_id,
        artifact_id=artifact_id,
        unit_kind="legacy_document_chunk",
        recipe_id=LEGACY_CHUNK_BACKFILL_UNIT_RECIPE_ID,
        recipe_version="v1",
        config_hash=_config_hash(unit_view_config, salt="document_unit_view"),
        status="ready",
        config=unit_view_config,
        stats={"unit_count": len(normalized)},
    )

    units: List[DocumentUnit] = []
    segments: List[DocumentSegment] = []
    members: List[DocumentSegmentMember] = []
    chunk_links: List[Tuple[str, str]] = []

    for idx, chunk in enumerate(normalized):
        anchor_type, anchor_payload = infer_anchor_from_md(chunk.get("md") or {})
        unit = DocumentUnit(
            unit_view_id=unit_view.id,
            unit_index=idx,
            text=chunk["text"],
            md={
                **dict(chunk.get("md") or {}),
                "legacy_chunk_id": chunk.get("id"),
                "legacy_chunk_number": int(chunk.get("document_chunk_number", idx)),
            },
            anchor_type=anchor_type,
            anchor_payload=anchor_payload,
        )
        units.append(unit)

    segment_view_config = {
        "source": "document_chunk_compat",
        "view_alias": DEFAULT_LOCAL_TEXT_VIEW_ALIAS,
        "unit_kind": unit_view.unit_kind,
    }
    segment_view = DocumentSegmentView(
        document_version_id=document_version_id,
        source_unit_view_id=unit_view.id,
        view_alias=DEFAULT_LOCAL_TEXT_VIEW_ALIAS,
        recipe_id=LEGACY_CHUNK_BACKFILL_SEGMENT_RECIPE_ID,
        recipe_version="v1",
        config_hash=_config_hash(segment_view_config, salt="document_segment_view"),
        segment_type_default="chunk",
        status="ready",
        is_current=True,
        config=segment_view_config,
        stats={"unit_count": len(units), "segment_count": len(normalized), "degraded_lineage": True},
    )

    for idx, (chunk, unit) in enumerate(zip(normalized, units)):
        chunk_md = dict(chunk.get("md") or {})
        derived_md = {
            **chunk_md,
            "source_unit_start_index": idx,
            "source_unit_end_index": idx,
            "source_unit_count": 1,
            "content_fingerprint": content_fingerprint(text=chunk["text"], md={"source": "legacy_chunk_backfill"}),
            "degraded_lineage": True,
            "legacy_chunk_id": chunk.get("id"),
        }
        segment = DocumentSegment(
            document_version_id=document_version_id,
            artifact_id=artifact_id,
            segment_view_id=segment_view.id,
            segment_type="chunk",
            segment_index=int(chunk.get("document_chunk_number", idx)),
            text=chunk["text"],
            md=derived_md,
        )
        member = DocumentSegmentMember(
            segment_id=segment.id,
            unit_id=unit.id,
            member_index=0,
            role="main",
            unit_start_char=0,
            unit_end_char=len(unit.text),
            md={"legacy_chunk_id": chunk.get("id")},
        )
        segments.append(segment)
        members.append(member)
        chunk_links.append((str(chunk.get("id")), segment.id))

    return DocumentDecompositionBackfillPayload(
        unit_view=unit_view,
        units=units,
        segment_view=segment_view,
        segments=segments,
        members=members,
        chunk_links=chunk_links,
    )


def compute_chunk_segment_parity(
    *,
    chunk_rows: Sequence[Any],
    segment_rows: Sequence[Any],
) -> Dict[str, Any]:
    chunks = _normalize_chunk_rows(chunk_rows)
    segments_by_id: Dict[str, Dict[str, Any]] = {}
    for row in segment_rows:
        if isinstance(row, dict):
            item = dict(row)
        else:
            item = {
                "id": getattr(row, "id"),
                "segment_index": getattr(row, "segment_index", 0),
                "text": getattr(row, "text", "") or "",
            }
        segments_by_id[str(item["id"])] = item

    missing_authority_chunk_ids: List[str] = []
    text_mismatch_chunk_ids: List[str] = []
    index_mismatch_chunk_ids: List[str] = []
    authority_segment_ids: List[str] = []
    text_match_count = 0
    index_match_count = 0

    for chunk in chunks:
        authority_segment_id = chunk.get("authority_segment_id")
        if authority_segment_id is None or str(authority_segment_id) not in segments_by_id:
            missing_authority_chunk_ids.append(str(chunk.get("id")))
            continue
        authority_segment_ids.append(str(authority_segment_id))
        segment = segments_by_id[str(authority_segment_id)]
        if str(segment.get("text") or "") == chunk["text"]:
            text_match_count += 1
        else:
            text_mismatch_chunk_ids.append(str(chunk.get("id")))
        if int(segment.get("segment_index", -1)) == int(chunk.get("document_chunk_number", -1)):
            index_match_count += 1
        else:
            index_mismatch_chunk_ids.append(str(chunk.get("id")))

    orphan_segment_ids = sorted(set(segments_by_id.keys()) - set(authority_segment_ids))
    verdict = "pass"
    if missing_authority_chunk_ids or text_mismatch_chunk_ids:
        verdict = "fail"
    elif index_mismatch_chunk_ids or orphan_segment_ids:
        verdict = "warn"

    return {
        "chunk_count": len(chunks),
        "segment_count": len(segments_by_id),
        "authority_linked_chunk_count": len(authority_segment_ids),
        "text_match_count": text_match_count,
        "index_match_count": index_match_count,
        "missing_authority_chunk_ids": missing_authority_chunk_ids,
        "text_mismatch_chunk_ids": text_mismatch_chunk_ids,
        "index_mismatch_chunk_ids": index_mismatch_chunk_ids,
        "orphan_segment_ids": orphan_segment_ids,
        "all_text_match": len(text_mismatch_chunk_ids) == 0 and len(missing_authority_chunk_ids) == 0,
        "verdict": verdict,
    }


def summarize_document_decomposition_rows(
    *,
    document_id: str,
    versions: Sequence[Any],
    unit_views: Sequence[Any],
    units: Sequence[Any],
    segment_views: Sequence[Any],
    segments: Sequence[Any],
    members: Sequence[Any],
    chunks: Sequence[Any],
) -> Dict[str, Any]:
    normalized_chunks = _normalize_chunk_rows(chunks)
    authority_linked_chunk_count = sum(1 for row in normalized_chunks if row.get("authority_segment_id"))
    default_views = [row for row in segment_views if getattr(row, "view_alias", None) == DEFAULT_LOCAL_TEXT_VIEW_ALIAS and bool(getattr(row, "is_current", True))]
    backfilled_views = [row for row in default_views if getattr(row, "recipe_id", None) == LEGACY_CHUNK_BACKFILL_SEGMENT_RECIPE_ID]

    status = DECOMPOSITION_STATUS_LEGACY_ONLY
    if len(normalized_chunks) == 0 and len(segments) == 0:
        status = DECOMPOSITION_STATUS_EMPTY
    elif len(default_views) > 0 and authority_linked_chunk_count == len(normalized_chunks) and len(normalized_chunks) > 0:
        status = DECOMPOSITION_STATUS_BACKFILLED_COMPAT if len(backfilled_views) > 0 else DECOMPOSITION_STATUS_CANONICAL
    elif len(default_views) > 0 and authority_linked_chunk_count < len(normalized_chunks):
        status = DECOMPOSITION_STATUS_CHUNKS_MISSING_AUTHORITY_LINKS
    elif len(segments) > 0 and len(default_views) == 0:
        status = DECOMPOSITION_STATUS_SEGMENTS_MISSING_DEFAULT_VIEW
    elif len(versions) > 0 or len(unit_views) > 0 or len(segment_views) > 0:
        status = DECOMPOSITION_STATUS_PARTIAL

    return {
        "document_id": document_id,
        "version_count": len(list(versions)),
        "unit_view_count": len(list(unit_views)),
        "unit_count": len(list(units)),
        "segment_view_count": len(list(segment_views)),
        "default_segment_view_count": len(default_views),
        "segment_count": len(list(segments)),
        "segment_member_count": len(list(members)),
        "chunk_count": len(normalized_chunks),
        "authority_linked_chunk_count": authority_linked_chunk_count,
        "compatibility_contract": DOCUMENT_CHUNK_COMPATIBILITY_CONTRACT,
        "status": status,
        "backfilled_compat": len(backfilled_views) > 0,
    }


def evaluate_document_chunk_compatibility_contract(
    *,
    chunk_rows: Sequence[Any],
    segment_rows: Sequence[Any],
) -> Dict[str, Any]:
    parity = compute_chunk_segment_parity(chunk_rows=chunk_rows, segment_rows=segment_rows)
    compatibility_normalized = (
        len(parity["missing_authority_chunk_ids"]) == 0
        and len(parity["orphan_segment_ids"]) == 0
    )
    return {
        "compatibility_contract": DOCUMENT_CHUNK_COMPATIBILITY_CONTRACT,
        "compatibility_normalized": compatibility_normalized,
        **parity,
    }


def ensure_document_version(database: Session, *, document_row: document_raw) -> DocumentVersion:
    version = database.exec(
        select(DocumentVersion)
        .where(DocumentVersion.document_id == document_row.id)
        .order_by(DocumentVersion.version_no.desc())
        .limit(1)
    ).first()
    if version is not None:
        return version
    version = DocumentVersion(
        document_id=document_row.id,
        version_no=1,
        content_hash=document_row.integrity_sha256,
        status="ready",
        created_at=time(),
        md={"source": "document_decomposition_backfill"},
    )
    database.add(version)
    database.commit()
    database.refresh(version)
    return version


def ensure_backfill_artifact(
    database: Session,
    *,
    document_row: document_raw,
    version: DocumentVersion,
) -> DocumentArtifact:
    artifact = database.exec(
        select(DocumentArtifact)
        .where(
            DocumentArtifact.document_version_id == version.id,
            DocumentArtifact.artifact_type == LEGACY_CHUNK_BACKFILL_ARTIFACT_TYPE,
        )
        .order_by(DocumentArtifact.created_at.desc())
        .limit(1)
    ).first()
    if artifact is not None:
        return artifact
    storage_ref = None
    if getattr(document_row, "blob_id", None) and getattr(document_row, "blob_dir", None):
        storage_ref = f"{document_row.blob_id}:{document_row.blob_dir}"
    artifact = DocumentArtifact(
        document_version_id=version.id,
        artifact_type=LEGACY_CHUNK_BACKFILL_ARTIFACT_TYPE,
        modality="text",
        storage_ref=storage_ref,
        md={"source": "document_decomposition_backfill", "degraded_lineage": True},
    )
    database.add(artifact)
    database.commit()
    database.refresh(artifact)
    return artifact


def summarize_many_documents(database: Session, *, document_ids: Sequence[str]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for document_id in document_ids:
        state = fetch_document_decomposition_state(database, document_id=document_id)
        rows.append(summarize_document_decomposition_rows(document_id=document_id, **state))
    return rows


def aggregate_decomposition_status(summaries: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    items = list(summaries)
    aggregate = {
        "documents_scanned": len(items),
        "empty_documents": sum(1 for row in items if row["status"] == DECOMPOSITION_STATUS_EMPTY),
        "canonical_documents": sum(1 for row in items if row["status"] == DECOMPOSITION_STATUS_CANONICAL),
        "backfilled_documents": sum(1 for row in items if row["status"] == DECOMPOSITION_STATUS_BACKFILLED_COMPAT),
        "legacy_only_documents": sum(1 for row in items if row["status"] == DECOMPOSITION_STATUS_LEGACY_ONLY),
        "partial_documents": sum(1 for row in items if row["status"] == DECOMPOSITION_STATUS_PARTIAL),
        "chunks_missing_authority_links_documents": sum(1 for row in items if row["status"] == DECOMPOSITION_STATUS_CHUNKS_MISSING_AUTHORITY_LINKS),
        "segments_missing_default_view_documents": sum(1 for row in items if row["status"] == DECOMPOSITION_STATUS_SEGMENTS_MISSING_DEFAULT_VIEW),
    }
    aggregate["unknown_documents"] = max(
        0,
        aggregate["documents_scanned"]
        - aggregate["empty_documents"]
        - aggregate["canonical_documents"]
        - aggregate["backfilled_documents"]
        - aggregate["legacy_only_documents"]
        - aggregate["partial_documents"]
        - aggregate["chunks_missing_authority_links_documents"]
        - aggregate["segments_missing_default_view_documents"],
    )
    aggregate["status_order"] = list(DECOMPOSITION_STATUS_ORDER)
    return aggregate


PROPOSED_SEGMENT_UNIQUENESS_CONSTRAINT = "uq_document_segment_view_type_index"
LEGACY_SEGMENT_UNIQUENESS_CONSTRAINT = "uq_document_segment_version_type_index"


def audit_segment_uniqueness_readiness(
    database: Session,
    *,
    document_ids: Sequence[str] | None = None,
    scope_limit: int | None = None,
    scope_offset: int = 0,
) -> Dict[str, Any]:
    from sqlalchemy import text as sql_text

    scoped_document_ids = [str(row) for row in (document_ids or []) if row is not None]

    def _quoted_ids(ids: Sequence[str]) -> str:
        return ", ".join(f"'{str(row).replace("'", "''")}'" for row in ids)

    if scoped_document_ids:
        document_ids_sql = _quoted_ids(scoped_document_ids)
        scope_document_count = len(scoped_document_ids)
        scoped_cte = f"""
            WITH scoped_documents AS (
                SELECT id
                FROM {document_raw.__tablename__}
                WHERE id IN ({document_ids_sql})
            ),
            scoped_versions AS (
                SELECT id, document_id
                FROM {DocumentVersion.__tablename__}
                WHERE document_id IN (SELECT id FROM scoped_documents)
            )
        """
    elif scope_limit is not None:
        scope_document_count = int(database.exec(sql_text(
            f"""
            SELECT COUNT(*)
            FROM (
                SELECT id
                FROM {document_raw.__tablename__}
                ORDER BY creation_timestamp DESC
                OFFSET :scope_offset
                LIMIT :scope_limit
            ) scoped_documents
            """
        ).bindparams(scope_offset=int(scope_offset), scope_limit=int(scope_limit))).one()[0])
        scoped_cte = f"""
            WITH scoped_documents AS (
                SELECT id
                FROM {document_raw.__tablename__}
                ORDER BY creation_timestamp DESC
                OFFSET :scope_offset
                LIMIT :scope_limit
            ),
            scoped_versions AS (
                SELECT id, document_id
                FROM {DocumentVersion.__tablename__}
                WHERE document_id IN (SELECT id FROM scoped_documents)
            )
        """
    else:
        scope_document_count = 0
        scoped_cte = None

    if scoped_cte is not None:
        bind_stmt = lambda query: sql_text(scoped_cte + query).bindparams(
            scope_offset=int(scope_offset),
            scope_limit=int(scope_limit) if scope_limit is not None else 0,
        ) if scope_limit is not None and not scoped_document_ids else sql_text(scoped_cte + query)
        null_segment_view_count = int(database.exec(bind_stmt(
            f"SELECT COUNT(*) FROM {DocumentSegment.__tablename__} WHERE document_version_id IN (SELECT id FROM scoped_versions) AND segment_view_id IS NULL"
        )).one()[0])
        duplicate_rows = list(database.exec(bind_stmt(
            f"""
            SELECT document_version_id, segment_view_id, segment_type, segment_index, COUNT(*) AS c
            FROM {DocumentSegment.__tablename__}
            WHERE document_version_id IN (SELECT id FROM scoped_versions)
            GROUP BY document_version_id, segment_view_id, segment_type, segment_index
            HAVING COUNT(*) > 1
            ORDER BY c DESC, document_version_id ASC
            """
        )))
        default_view_conflicts = list(database.exec(bind_stmt(
            f"""
            SELECT document_version_id, view_alias, COUNT(*) AS c
            FROM {DocumentSegmentView.__tablename__}
            WHERE document_version_id IN (SELECT id FROM scoped_versions) AND is_current = TRUE AND view_alias IS NOT NULL
            GROUP BY document_version_id, view_alias
            HAVING COUNT(*) > 1
            ORDER BY c DESC, document_version_id ASC
            """
        )))
        chunk_authority_missing = int(database.exec(bind_stmt(
            f"""
            SELECT COUNT(*)
            FROM {DocumentChunk.__tablename__}
            WHERE document_id IN (SELECT id FROM scoped_documents) AND authority_segment_id IS NULL
            """
        )).one()[0])
        chunk_authority_orphans = int(database.exec(bind_stmt(
            f"""
            SELECT COUNT(*)
            FROM {DocumentChunk.__tablename__} c
            LEFT JOIN {DocumentSegment.__tablename__} s ON s.id = c.authority_segment_id
            WHERE c.document_id IN (SELECT id FROM scoped_documents) AND c.authority_segment_id IS NOT NULL AND s.id IS NULL
            """
        )).one()[0])
        segment_count = int(database.exec(bind_stmt(
            f"SELECT COUNT(*) FROM {DocumentSegment.__tablename__} WHERE document_version_id IN (SELECT id FROM scoped_versions)"
        )).one()[0])
    else:
        null_segment_view_count = int(database.exec(sql_text(
            f"SELECT COUNT(*) FROM {DocumentSegment.__tablename__} WHERE segment_view_id IS NULL"
        )).one()[0])
        duplicate_rows = list(database.exec(sql_text(
            f"""
            SELECT document_version_id, segment_view_id, segment_type, segment_index, COUNT(*) AS c
            FROM {DocumentSegment.__tablename__}
            GROUP BY document_version_id, segment_view_id, segment_type, segment_index
            HAVING COUNT(*) > 1
            ORDER BY c DESC, document_version_id ASC
            """
        )))
        default_view_conflicts = list(database.exec(sql_text(
            f"""
            SELECT document_version_id, view_alias, COUNT(*) AS c
            FROM {DocumentSegmentView.__tablename__}
            WHERE is_current = TRUE AND view_alias IS NOT NULL
            GROUP BY document_version_id, view_alias
            HAVING COUNT(*) > 1
            ORDER BY c DESC, document_version_id ASC
            """
        )))
        chunk_authority_missing = int(database.exec(sql_text(
            f"SELECT COUNT(*) FROM {DocumentChunk.__tablename__} WHERE document_id IS NOT NULL AND authority_segment_id IS NULL"
        )).one()[0])
        chunk_authority_orphans = int(database.exec(sql_text(
            f"""
            SELECT COUNT(*)
            FROM {DocumentChunk.__tablename__} c
            LEFT JOIN {DocumentSegment.__tablename__} s ON s.id = c.authority_segment_id
            WHERE c.document_id IS NOT NULL AND c.authority_segment_id IS NOT NULL AND s.id IS NULL
            """
        )).one()[0])
        segment_count = int(database.exec(sql_text(f"SELECT COUNT(*) FROM {DocumentSegment.__tablename__}")).one()[0])
    constraint_rows = list(database.exec(sql_text(
        f"""
        SELECT conname
        FROM pg_constraint
        WHERE conrelid = '{DocumentSegment.__tablename__}'::regclass
          AND contype = 'u'
        ORDER BY conname ASC
        """
    )))
    existing_constraints = [str(row[0]) for row in constraint_rows]
    ready_for_constraint_swap = (
        null_segment_view_count == 0
        and len(duplicate_rows) == 0
        and len(default_view_conflicts) == 0
    )
    compatibility_normalized = (
        chunk_authority_missing == 0
        and chunk_authority_orphans == 0
    )
    return {
        "scope_mode": "documents" if (scoped_document_ids or scoped_cte is not None) else "global",
        "scope_document_count": scope_document_count,
        "segment_count": segment_count,
        "null_segment_view_count": null_segment_view_count,
        "duplicate_key_count": len(duplicate_rows),
        "duplicate_keys": [
            {
                "document_version_id": str(row[0]),
                "segment_view_id": str(row[1]) if row[1] is not None else None,
                "segment_type": str(row[2]),
                "segment_index": int(row[3]),
                "count": int(row[4]),
            }
            for row in duplicate_rows[:25]
        ],
        "default_view_conflict_count": len(default_view_conflicts),
        "default_view_conflicts": [
            {
                "document_version_id": str(row[0]),
                "view_alias": str(row[1]) if row[1] is not None else None,
                "count": int(row[2]),
            }
            for row in default_view_conflicts[:25]
        ],
        "chunk_authority_missing_count": chunk_authority_missing,
        "chunk_authority_orphan_count": chunk_authority_orphans,
        "existing_unique_constraints": existing_constraints,
        "legacy_constraint_present": LEGACY_SEGMENT_UNIQUENESS_CONSTRAINT in existing_constraints,
        "proposed_constraint_present": PROPOSED_SEGMENT_UNIQUENESS_CONSTRAINT in existing_constraints,
        "compatibility_normalized": compatibility_normalized,
        "ready_for_constraint_swap": ready_for_constraint_swap,
        "ready_for_swap": ready_for_constraint_swap,
    }


def apply_segment_uniqueness_swap(database: Session, *, dry_run: bool = False) -> Dict[str, Any]:
    from sqlalchemy import text as sql_text

    audit = audit_segment_uniqueness_readiness(database)
    if not audit["ready_for_constraint_swap"]:
        return {"action": "blocked", "audit": audit}
    statements = [
        f"ALTER TABLE {DocumentSegment.__tablename__} DROP CONSTRAINT IF EXISTS {LEGACY_SEGMENT_UNIQUENESS_CONSTRAINT}",
        f"ALTER TABLE {DocumentSegment.__tablename__} DROP CONSTRAINT IF EXISTS {PROPOSED_SEGMENT_UNIQUENESS_CONSTRAINT}",
        f"ALTER TABLE {DocumentSegment.__tablename__} ADD CONSTRAINT {PROPOSED_SEGMENT_UNIQUENESS_CONSTRAINT} UNIQUE (document_version_id, segment_view_id, segment_type, segment_index)",
    ]
    if dry_run:
        return {"action": "plan_swap", "audit": audit, "sql": statements}
    for stmt in statements:
        database.exec(sql_text(stmt))
    database.commit()
    return {"action": "applied", "audit": audit, "post_audit": audit_segment_uniqueness_readiness(database)}


def fetch_document_decomposition_state(database: Session, *, document_id: str) -> Dict[str, Any]:
    versions = database.exec(select(DocumentVersion).where(DocumentVersion.document_id == document_id)).all()
    version_ids = [row.id for row in versions]
    unit_views: List[DocumentUnitView] = []
    units: List[DocumentUnit] = []
    segment_views: List[DocumentSegmentView] = []
    segments: List[DocumentSegment] = []
    members: List[DocumentSegmentMember] = []
    if version_ids:
        unit_views = database.exec(select(DocumentUnitView).where(DocumentUnitView.document_version_id.in_(version_ids))).all()
        unit_view_ids = [row.id for row in unit_views]
        if unit_view_ids:
            units = database.exec(select(DocumentUnit).where(DocumentUnit.unit_view_id.in_(unit_view_ids))).all()
            segment_views = database.exec(select(DocumentSegmentView).where(DocumentSegmentView.document_version_id.in_(version_ids))).all()
            segment_view_ids = [row.id for row in segment_views]
            if segment_view_ids:
                segments = database.exec(select(DocumentSegment).where(DocumentSegment.segment_view_id.in_(segment_view_ids))).all()
                segment_ids = [row.id for row in segments]
                if segment_ids:
                    members = database.exec(select(DocumentSegmentMember).where(DocumentSegmentMember.segment_id.in_(segment_ids))).all()
    chunks = database.exec(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.document_chunk_number.asc())
    ).all()
    return {
        "versions": versions,
        "unit_views": unit_views,
        "units": units,
        "segment_views": segment_views,
        "segments": segments,
        "members": members,
        "chunks": chunks,
    }




def build_chunk_authority_provenance(
    *,
    chunks: Sequence[Any],
    segments: Sequence[Any],
    segment_views: Sequence[Any],
    members: Sequence[Any],
    units: Sequence[Any],
) -> List[Dict[str, Any]]:
    def _value(row: Any, key: str, default: Any = None) -> Any:
        if isinstance(row, dict):
            return row.get(key, default)
        return getattr(row, key, default)

    normalized_chunks = _normalize_chunk_rows(chunks)
    segments_by_id = {str(_value(row, "id")): row for row in segments}
    segment_views_by_id = {str(_value(row, "id")): row for row in segment_views}
    units_by_id = {str(_value(row, "id")): row for row in units}
    members_by_segment: Dict[str, List[Any]] = {}
    for row in members:
        segment_id = str(_value(row, "segment_id"))
        members_by_segment.setdefault(segment_id, []).append(row)
    for segment_member_rows in members_by_segment.values():
        segment_member_rows.sort(key=lambda row: int(_value(row, "member_index", 0) or 0))

    records: List[Dict[str, Any]] = []
    for chunk in normalized_chunks:
        authority_segment_id = chunk.get("authority_segment_id")
        segment = segments_by_id.get(str(authority_segment_id)) if authority_segment_id is not None else None
        segment_view_id = _value(segment, "segment_view_id", None) if segment is not None else None
        segment_view = segment_views_by_id.get(str(segment_view_id)) if segment_view_id is not None else None
        member_rows = members_by_segment.get(str(authority_segment_id), []) if authority_segment_id is not None else []
        member_payload = []
        for member in member_rows:
            unit_id = str(_value(member, "unit_id", None) or "")
            unit = units_by_id.get(unit_id)
            member_payload.append({
                "member_index": int(_value(member, "member_index", 0) or 0),
                "role": _value(member, "role", None),
                "unit_id": unit_id or None,
                "unit_index": None if unit is None else int(_value(unit, "unit_index", 0) or 0),
                "unit_start_char": _value(member, "unit_start_char", None),
                "unit_end_char": _value(member, "unit_end_char", None),
            })
        records.append({
            "chunk_id": chunk.get("id"),
            "document_chunk_number": int(chunk.get("document_chunk_number", 0) or 0),
            "authority_segment_id": authority_segment_id,
            "segment_view_id": None if segment is None else segment_view_id,
            "segment_view_alias": None if segment_view is None else _value(segment_view, "view_alias", None),
            "segment_type": None if segment is None else _value(segment, "segment_type", None),
            "segment_index": None if segment is None else int(_value(segment, "segment_index", 0) or 0),
            "member_count": len(member_payload),
            "members": member_payload,
        })
    return records


def fetch_document_chunk_authority_provenance(database: Session, *, document_id: str) -> Dict[str, Any]:
    state = fetch_document_decomposition_state(database, document_id=document_id)
    records = build_chunk_authority_provenance(
        chunks=state["chunks"],
        segments=state["segments"],
        segment_views=state["segment_views"],
        members=state["members"],
        units=state["units"],
    )
    return {
        "document_id": document_id,
        "record_count": len(records),
        "records": records,
    }

def clear_backfill_decomposition_state(
    database: Session,
    *,
    document_id: str,
    dry_run: bool = False,
) -> Dict[str, Any]:
    state = fetch_document_decomposition_state(database, document_id=document_id)
    versions = list(state["versions"])
    chunks = list(state["chunks"])
    if not versions:
        return {
            "document_id": document_id,
            "action": "skip_no_versions",
            "deleted": {"unit_views": 0, "units": 0, "segment_views": 0, "segments": 0, "members": 0, "chunk_links_cleared": 0},
        }

    version_ids = [str(row.id) for row in versions]
    backfill_unit_views = [
        row for row in state["unit_views"]
        if getattr(row, "recipe_id", None) == LEGACY_CHUNK_BACKFILL_UNIT_RECIPE_ID
    ]
    backfill_segment_views = [
        row for row in state["segment_views"]
        if getattr(row, "recipe_id", None) == LEGACY_CHUNK_BACKFILL_SEGMENT_RECIPE_ID
    ]
    backfill_unit_view_ids = [str(row.id) for row in backfill_unit_views]
    backfill_segment_view_ids = [str(row.id) for row in backfill_segment_views]
    backfill_segment_ids = [str(row.id) for row in state["segments"] if str(getattr(row, "segment_view_id", "") or "") in backfill_segment_view_ids]

    deleted = {
        "unit_views": len(backfill_unit_view_ids),
        "units": sum(1 for row in state["units"] if str(getattr(row, "unit_view_id", "") or "") in backfill_unit_view_ids),
        "segment_views": len(backfill_segment_view_ids),
        "segments": len(backfill_segment_ids),
        "members": sum(1 for row in state["members"] if str(getattr(row, "segment_id", "") or "") in backfill_segment_ids),
        "chunk_links_cleared": sum(1 for row in chunks if getattr(row, "authority_segment_id", None) and str(getattr(row, "authority_segment_id", "")) in backfill_segment_ids),
    }

    if dry_run:
        return {"document_id": document_id, "action": "plan_clear_backfill_state", "deleted": deleted}

    if deleted["chunk_links_cleared"]:
        for chunk in chunks:
            authority_segment_id = getattr(chunk, "authority_segment_id", None)
            if authority_segment_id and str(authority_segment_id) in backfill_segment_ids:
                chunk.authority_segment_id = None
                database.add(chunk)
        database.commit()

    if backfill_segment_ids:
        from sqlalchemy import delete as sa_delete
        database.exec(sa_delete(DocumentSegmentMember).where(DocumentSegmentMember.segment_id.in_(backfill_segment_ids)))
        database.commit()
        database.exec(sa_delete(DocumentSegment).where(DocumentSegment.id.in_(backfill_segment_ids)))
        database.commit()

    if backfill_segment_view_ids:
        from sqlalchemy import delete as sa_delete
        database.exec(sa_delete(DocumentSegmentView).where(DocumentSegmentView.id.in_(backfill_segment_view_ids)))
        database.commit()

    if backfill_unit_view_ids:
        from sqlalchemy import delete as sa_delete
        database.exec(sa_delete(DocumentUnit).where(DocumentUnit.unit_view_id.in_(backfill_unit_view_ids)))
        database.commit()
        database.exec(sa_delete(DocumentUnitView).where(DocumentUnitView.id.in_(backfill_unit_view_ids)))
        database.commit()

    backfill_artifact_ids = [
        str(row.id)
        for row in database.exec(
            select(DocumentArtifact.id).where(
                DocumentArtifact.document_version_id.in_(version_ids),
                DocumentArtifact.artifact_type == LEGACY_CHUNK_BACKFILL_ARTIFACT_TYPE,
            )
        ).all()
    ]
    if backfill_artifact_ids:
        from sqlalchemy import delete as sa_delete
        database.exec(sa_delete(DocumentArtifact).where(DocumentArtifact.id.in_(backfill_artifact_ids)))
        database.commit()

    return {"document_id": document_id, "action": "cleared_backfill_state", "deleted": deleted}


def repair_document_decomposition(
    database: Session,
    *,
    document_row: document_raw,
    dry_run: bool = False,
) -> Dict[str, Any]:
    state = fetch_document_decomposition_state(database, document_id=document_row.id)
    summary_before = summarize_document_decomposition_rows(document_id=document_row.id, **state)
    status = str(summary_before["status"])
    default_views = [row for row in state["segment_views"] if getattr(row, "view_alias", None) == DEFAULT_LOCAL_TEXT_VIEW_ALIAS and bool(getattr(row, "is_current", True))]
    non_backfill_default_views = [row for row in default_views if getattr(row, "recipe_id", None) != LEGACY_CHUNK_BACKFILL_SEGMENT_RECIPE_ID]

    if status in {DECOMPOSITION_STATUS_EMPTY, DECOMPOSITION_STATUS_CANONICAL}:
        return {"document_id": document_row.id, "action": f"skip_{status}", "summary_before": summary_before}

    if status == DECOMPOSITION_STATUS_BACKFILLED_COMPAT:
        parity = compute_chunk_segment_parity(chunk_rows=state["chunks"], segment_rows=state["segments"])
        if parity["verdict"] == "pass":
            return {
                "document_id": document_row.id,
                "action": "skip_backfilled_compat_healthy",
                "summary_before": summary_before,
                "parity": parity,
            }

    if non_backfill_default_views:
        return {
            "document_id": document_row.id,
            "action": "manual_review_required",
            "summary_before": summary_before,
            "reason": "non_backfill_default_view_present",
            "default_view_ids": [str(row.id) for row in non_backfill_default_views],
        }

    if status == DECOMPOSITION_STATUS_CHUNKS_MISSING_AUTHORITY_LINKS and default_views:
        conservative = backfill_document_decomposition(database, document_row=document_row, dry_run=dry_run)
        if conservative.get("action") in {"relinked_chunk_authority", "plan_backfill", "skip_existing_default_view_conflict"}:
            return {
                "document_id": document_row.id,
                "action": conservative.get("action"),
                "summary_before": summary_before,
                **{k: v for k, v in conservative.items() if k not in {"document_id", "action", "summary_before"}},
            }

    clear_result = clear_backfill_decomposition_state(database, document_id=document_row.id, dry_run=dry_run)
    if dry_run:
        planned = backfill_document_decomposition(database, document_row=document_row, dry_run=True)
        return {
            "document_id": document_row.id,
            "action": "plan_repair",
            "summary_before": summary_before,
            "clear": clear_result,
            "rebuild": planned,
        }

    rebuilt = backfill_document_decomposition(database, document_row=document_row, dry_run=False)
    return {
        "document_id": document_row.id,
        "action": "repaired" if rebuilt.get("action") == "backfilled" else rebuilt.get("action", "repair_noop"),
        "summary_before": summary_before,
        "clear": clear_result,
        "rebuild": rebuilt,
    }


def backfill_document_decomposition(
    database: Session,
    *,
    document_row: document_raw,
    dry_run: bool = False,
) -> Dict[str, Any]:
    state = fetch_document_decomposition_state(database, document_id=document_row.id)
    summary_before = summarize_document_decomposition_rows(document_id=document_row.id, **state)
    if summary_before["chunk_count"] == 0:
        return {"document_id": document_row.id, "action": "skip_no_chunks", "summary_before": summary_before}

    default_views = [row for row in state["segment_views"] if getattr(row, "view_alias", None) == DEFAULT_LOCAL_TEXT_VIEW_ALIAS and bool(getattr(row, "is_current", True))]
    if default_views:
        parity = compute_chunk_segment_parity(chunk_rows=state["chunks"], segment_rows=state["segments"])
        if parity["verdict"] == "pass":
            return {
                "document_id": document_row.id,
                "action": "skip_already_canonical",
                "summary_before": summary_before,
                "parity": parity,
            }
        # repair missing chunk authority links by index/text against existing segments
        segment_by_index = {int(row.segment_index): row for row in state["segments"]}
        repaired = 0
        for chunk in state["chunks"]:
            if getattr(chunk, "authority_segment_id", None):
                continue
            segment = segment_by_index.get(int(chunk.document_chunk_number or 0))
            if segment is None:
                continue
            if str(segment.text or "") != str(chunk.text or ""):
                continue
            if not dry_run:
                chunk.authority_segment_id = segment.id
                database.add(chunk)
            repaired += 1
        if repaired > 0 and not dry_run:
            database.commit()
            state = fetch_document_decomposition_state(database, document_id=document_row.id)
            summary_after = summarize_document_decomposition_rows(document_id=document_row.id, **state)
            parity_after = compute_chunk_segment_parity(chunk_rows=state["chunks"], segment_rows=state["segments"])
            return {
                "document_id": document_row.id,
                "action": "relinked_chunk_authority",
                "relinked_count": repaired,
                "summary_before": summary_before,
                "summary_after": summary_after,
                "parity": parity_after,
            }
        return {
            "document_id": document_row.id,
            "action": "skip_existing_default_view_conflict",
            "summary_before": summary_before,
            "parity": parity,
        }

    version = ensure_document_version(database, document_row=document_row)
    artifact = ensure_backfill_artifact(database, document_row=document_row, version=version)
    payload = build_chunk_backfill_payload(
        document_version_id=version.id,
        artifact_id=artifact.id,
        chunk_rows=state["chunks"],
    )
    if dry_run:
        return {
            "document_id": document_row.id,
            "action": "plan_backfill",
            "summary_before": summary_before,
            "planned": {
                "unit_count": len(payload.units),
                "segment_count": len(payload.segments),
                "member_count": len(payload.members),
            },
        }

    database.add(payload.unit_view)
    database.commit()

    database.add_all(payload.units)
    database.commit()

    database.add(payload.segment_view)
    database.commit()

    database.add_all(payload.segments)
    database.commit()

    database.add_all(payload.members)
    segment_id_by_chunk_id = {chunk_id: segment_id for chunk_id, segment_id in payload.chunk_links}
    for chunk in state["chunks"]:
        segment_id = segment_id_by_chunk_id.get(str(chunk.id))
        if segment_id is not None:
            chunk.authority_segment_id = segment_id
            database.add(chunk)
    database.commit()

    state_after = fetch_document_decomposition_state(database, document_id=document_row.id)
    summary_after = summarize_document_decomposition_rows(document_id=document_row.id, **state_after)
    parity_after = compute_chunk_segment_parity(chunk_rows=state_after["chunks"], segment_rows=state_after["segments"])
    return {
        "document_id": document_row.id,
        "action": "backfilled",
        "summary_before": summary_before,
        "summary_after": summary_after,
        "parity": parity_after,
    }

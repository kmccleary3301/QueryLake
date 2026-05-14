from __future__ import annotations

from dataclasses import asdict, dataclass, field
import os
from typing import Any, Dict, List

from QueryLake.database.sql_db_tables import (
    document_artifact as DocumentArtifact,
    document_segment as DocumentSegment,
    document_segment_member as DocumentSegmentMember,
    document_segment_view as DocumentSegmentView,
    document_unit as DocumentUnit,
    document_unit_view as DocumentUnitView,
)
from QueryLake.runtime.content_fingerprint import content_fingerprint
from QueryLake.scanning.contracts import ScannerEnvelope, ScanObject


def scanner_decomposition_persistence_enabled() -> bool:
    return str(os.environ.get("QUERYLAKE_SCANNER_DECOMPOSITION_PERSIST", "")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


@dataclass(frozen=True)
class ScannerDecompositionUnitPlan:
    unit_index: int
    unit_kind: str
    text: str
    anchor_type: str | None = None
    anchor_payload: Dict[str, Any] = field(default_factory=dict)
    md: Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScannerDecompositionSegmentPlan:
    segment_index: int
    segment_type: str
    text: str
    source_unit_indices: List[int]
    view_alias: str
    md: Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScannerDecompositionPlan:
    backend_id: str
    raw_backend_contract: str
    unit_view_alias: str
    segment_view_alias: str
    units: List[ScannerDecompositionUnitPlan]
    segments: List[ScannerDecompositionSegmentPlan]
    warnings: List[str] = field(default_factory=list)

    def to_payload(self) -> Dict[str, Any]:
        return {
            "backend_id": self.backend_id,
            "raw_backend_contract": self.raw_backend_contract,
            "unit_view_alias": self.unit_view_alias,
            "segment_view_alias": self.segment_view_alias,
            "unit_count": len(self.units),
            "segment_count": len(self.segments),
            "units": [row.to_payload() for row in self.units],
            "segments": [row.to_payload() for row in self.segments],
            "warnings": list(self.warnings),
        }


def scanner_object_unit_kind(obj: ScanObject) -> str:
    normalized = str(obj.object_type or "").strip().lower()
    if normalized in {"table", "table_cell", "table_row"}:
        return "scanner_table"
    if normalized in {"line", "text_line"}:
        return "scanner_line"
    if normalized in {"figure", "image"}:
        return "scanner_figure"
    if normalized in {"heading", "title", "paragraph", "block", "text"}:
        return "scanner_text_block"
    return f"scanner_{normalized or 'object'}"


def scanner_object_segment_type(obj: ScanObject) -> str:
    unit_kind = scanner_object_unit_kind(obj)
    if unit_kind == "scanner_table":
        return "table"
    if unit_kind == "scanner_figure":
        return "figure"
    if unit_kind == "scanner_line":
        return "line"
    return "block"


def _object_anchor_payload(obj: ScanObject) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "page": int(obj.page_index),
        "object_id": obj.object_id,
        "reading_order": int(obj.reading_order),
    }
    if obj.bbox is not None:
        payload["bbox"] = list(obj.bbox)
    if obj.polygon is not None:
        payload["polygon"] = [list(point) for point in obj.polygon]
    return payload


def build_scanner_decomposition_plan(
    envelope: ScannerEnvelope,
    *,
    unit_view_alias: str = "scanner_objects",
    segment_view_alias: str = "layout_region",
) -> ScannerDecompositionPlan:
    units: List[ScannerDecompositionUnitPlan] = []
    segments: List[ScannerDecompositionSegmentPlan] = []
    warnings: List[str] = []

    text_objects = [obj for obj in envelope.objects if obj.text is not None and str(obj.text).strip()]
    text_objects.sort(key=lambda obj: (int(obj.page_index), int(obj.reading_order), str(obj.object_id)))

    if not text_objects:
        canonical_text = envelope.canonical_text().strip()
        if canonical_text:
            warnings.append("scanner_objects_missing; used canonical_text fallback unit")
            units.append(
                ScannerDecompositionUnitPlan(
                    unit_index=0,
                    unit_kind="scanner_canonical_text",
                    text=canonical_text,
                    anchor_type=None,
                    anchor_payload={},
                    md={"projection_fallback": True},
                )
            )
            segments.append(
                ScannerDecompositionSegmentPlan(
                    segment_index=0,
                    segment_type="block",
                    text=canonical_text,
                    source_unit_indices=[0],
                    view_alias=segment_view_alias,
                    md={"projection_fallback": True},
                )
            )
        else:
            warnings.append("scanner_envelope_has_no_text_units")
    else:
        for idx, obj in enumerate(text_objects):
            unit_kind = scanner_object_unit_kind(obj)
            anchor_payload = _object_anchor_payload(obj)
            unit = ScannerDecompositionUnitPlan(
                unit_index=idx,
                unit_kind=unit_kind,
                text=str(obj.text or ""),
                anchor_type="page_region" if obj.bbox or obj.polygon else "page_ref",
                anchor_payload=anchor_payload,
                md={
                    "scanner_object_id": obj.object_id,
                    "scanner_object_type": obj.object_type,
                    "confidence": obj.confidence,
                    "confidence_available": obj.confidence_available,
                    "source_artifact_ref": obj.source_artifact_ref,
                    **dict(obj.md or {}),
                },
            )
            units.append(unit)
            segments.append(
                ScannerDecompositionSegmentPlan(
                    segment_index=idx,
                    segment_type=scanner_object_segment_type(obj),
                    text=unit.text,
                    source_unit_indices=[idx],
                    view_alias=segment_view_alias,
                    md={
                        "scanner_object_id": obj.object_id,
                        "scanner_object_type": obj.object_type,
                        "page": obj.page_index,
                        "bbox": obj.bbox,
                        "polygon": obj.polygon,
                    },
                )
            )

    return ScannerDecompositionPlan(
        backend_id=envelope.scan_run.backend_id,
        raw_backend_contract=envelope.contract.raw_backend_contract,
        unit_view_alias=unit_view_alias,
        segment_view_alias=segment_view_alias,
        units=units,
        segments=segments,
        warnings=warnings,
    )


def materialize_scanner_decomposition_rows(
    *,
    document_version_id: str,
    artifact_id: str,
    plan: ScannerDecompositionPlan,
) -> Dict[str, Any]:
    unit_view_config = {
        "source": "scanner_envelope",
        "backend_id": plan.backend_id,
        "raw_backend_contract": plan.raw_backend_contract,
        "unit_view_alias": plan.unit_view_alias,
    }
    unit_view = DocumentUnitView(
        document_version_id=document_version_id,
        artifact_id=artifact_id,
        unit_kind=plan.unit_view_alias,
        recipe_id="scanner_envelope_units_v1",
        recipe_version="v1",
        config_hash=content_fingerprint(text="", md=unit_view_config, salt="scanner_unit_view"),
        status="ready",
        config=unit_view_config,
        stats={"unit_count": len(plan.units)},
    )
    unit_rows: List[DocumentUnit] = []
    for unit in plan.units:
        unit_rows.append(
            DocumentUnit(
                unit_view_id=unit_view.id,
                unit_index=int(unit.unit_index),
                text=unit.text,
                md={**dict(unit.md or {}), "scanner_backend_id": plan.backend_id},
                anchor_type=unit.anchor_type,
                anchor_payload=dict(unit.anchor_payload or {}),
            )
        )

    segment_view_config = {
        "source": "scanner_envelope",
        "backend_id": plan.backend_id,
        "raw_backend_contract": plan.raw_backend_contract,
        "segment_view_alias": plan.segment_view_alias,
        "unit_view_alias": plan.unit_view_alias,
    }
    segment_view = DocumentSegmentView(
        document_version_id=document_version_id,
        source_unit_view_id=unit_view.id,
        view_alias=plan.segment_view_alias,
        recipe_id="scanner_envelope_segments_v1",
        recipe_version="v1",
        config_hash=content_fingerprint(text="", md=segment_view_config, salt="scanner_segment_view"),
        segment_type_default="block",
        status="ready",
        is_current=True,
        config=segment_view_config,
        stats={"unit_count": len(unit_rows), "segment_count": len(plan.segments)},
    )
    unit_by_index = {unit.unit_index: row for unit, row in zip(plan.units, unit_rows)}
    segment_rows: List[DocumentSegment] = []
    member_rows: List[DocumentSegmentMember] = []
    for segment in plan.segments:
        segment_row = DocumentSegment(
            document_version_id=document_version_id,
            artifact_id=artifact_id,
            segment_view_id=segment_view.id,
            segment_type=segment.segment_type,
            segment_index=int(segment.segment_index),
            text=segment.text,
            md={**dict(segment.md or {}), "scanner_backend_id": plan.backend_id, "source_unit_indices": list(segment.source_unit_indices)},
        )
        segment_rows.append(segment_row)
        for member_index, unit_index in enumerate(segment.source_unit_indices):
            unit_row = unit_by_index.get(int(unit_index))
            if unit_row is None:
                continue
            member_rows.append(
                DocumentSegmentMember(
                    segment_id=segment_row.id,
                    unit_id=unit_row.id,
                    member_index=member_index,
                    role="main",
                    unit_start_char=0,
                    unit_end_char=len(unit_row.text or ""),
                    md={"scanner_backend_id": plan.backend_id},
                )
            )

    return {
        "unit_view": unit_view,
        "units": unit_rows,
        "segment_view": segment_view,
        "segments": segment_rows,
        "members": member_rows,
    }


def persist_scanner_decomposition_rows(
    database,
    *,
    document_version_id: str,
    artifact_id: str,
    envelope: ScannerEnvelope,
    enabled: bool | None = None,
    commit: bool = True,
) -> Dict[str, Any]:
    if enabled is None:
        enabled = scanner_decomposition_persistence_enabled()
    if not enabled:
        return {
            "status": "disabled",
            "persisted": False,
            "unit_count": 0,
            "segment_count": 0,
            "member_count": 0,
        }

    plan = build_scanner_decomposition_plan(envelope)
    rows = materialize_scanner_decomposition_rows(
        document_version_id=document_version_id,
        artifact_id=artifact_id,
        plan=plan,
    )
    ordered_rows = [
        rows["unit_view"],
        *rows["units"],
        rows["segment_view"],
        *rows["segments"],
        *rows["members"],
    ]
    try:
        for row in ordered_rows:
            database.add(row)
        if commit:
            database.commit()
        elif hasattr(database, "flush"):
            database.flush()
    except Exception:
        if hasattr(database, "rollback"):
            database.rollback()
        raise

    return {
        "status": "persisted",
        "persisted": True,
        "unit_view_id": rows["unit_view"].id,
        "segment_view_id": rows["segment_view"].id,
        "unit_count": len(rows["units"]),
        "segment_count": len(rows["segments"]),
        "member_count": len(rows["members"]),
        "warnings": list(plan.warnings),
    }


def persist_document_linked_scanner_decomposition(
    database,
    *,
    envelope: ScannerEnvelope,
    storage_ref: str | None = None,
    enabled: bool | None = None,
    commit: bool = True,
) -> Dict[str, Any]:
    document_version_id = getattr(envelope.scan_run, "document_version_id", None)
    if not document_version_id:
        return {
            "status": "mapping_unavailable",
            "persisted": False,
            "reason": "scanner_envelope_missing_document_version_id",
            "file_id": getattr(envelope.scan_run, "file_id", None),
            "file_version_id": getattr(envelope.scan_run, "file_version_id", None),
        }

    artifact = DocumentArtifact(
        document_version_id=str(document_version_id),
        artifact_type="scanner_envelope",
        modality="layout",
        storage_ref=storage_ref,
        md={
            "source": "scanner_envelope",
            "run_id": envelope.scan_run.run_id,
            "backend_id": envelope.scan_run.backend_id,
            "file_id": envelope.scan_run.file_id,
            "file_version_id": envelope.scan_run.file_version_id,
        },
    )
    try:
        database.add(artifact)
        if hasattr(database, "flush"):
            database.flush()
        result = persist_scanner_decomposition_rows(
            database,
            document_version_id=str(document_version_id),
            artifact_id=str(artifact.id),
            envelope=envelope,
            enabled=enabled,
            commit=commit,
        )
        return {
            **result,
            "document_version_id": str(document_version_id),
            "artifact_id": str(artifact.id),
            "mapping": "scanner_envelope_document_version_id",
        }
    except Exception:
        if hasattr(database, "rollback"):
            database.rollback()
        raise

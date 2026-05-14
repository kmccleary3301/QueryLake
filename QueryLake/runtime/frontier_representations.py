from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Sequence

from QueryLake.database.sql_db_tables import (
    document_segment as DocumentSegment,
    document_segment_member as DocumentSegmentMember,
    document_segment_view as DocumentSegmentView,
    document_unit as DocumentUnit,
    document_unit_view as DocumentUnitView,
)
from QueryLake.runtime.content_fingerprint import content_fingerprint


@dataclass(frozen=True)
class FrontierRepresentationPlan:
    lane: str
    source_view_alias: str
    target_view_alias: str
    segments: List[Dict[str, Any]]
    warnings: List[str] = field(default_factory=list)

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def build_semantic_segment_plan(
    source_segments: Sequence[Dict[str, Any]],
    *,
    target_view_alias: str = "semantic_text",
    max_chars: int = 1200,
) -> FrontierRepresentationPlan:
    out: List[Dict[str, Any]] = []
    current_text: List[str] = []
    current_ids: List[str] = []
    for row in source_segments:
        text = _clean_text(str(row.get("text") or ""))
        if not text:
            continue
        would_len = len(" ".join(current_text + [text]))
        if current_text and would_len > max_chars:
            out.append({
                "segment_index": len(out),
                "segment_type": "semantic",
                "text": " ".join(current_text),
                "source_segment_ids": list(current_ids),
            })
            current_text = []
            current_ids = []
        current_text.append(text)
        current_ids.append(str(row.get("id") or row.get("segment_id") or ""))
    if current_text:
        out.append({
            "segment_index": len(out),
            "segment_type": "semantic",
            "text": " ".join(current_text),
            "source_segment_ids": list(current_ids),
        })
    return FrontierRepresentationPlan(
        lane="semantic_segment_text",
        source_view_alias="default_local_text",
        target_view_alias=target_view_alias,
        segments=out,
    )


def build_late_chunk_trace(
    source_segments: Sequence[Dict[str, Any]],
    *,
    query: str,
    max_chars: int = 1600,
) -> Dict[str, Any]:
    query_terms = {term.lower() for term in re.findall(r"[A-Za-z0-9_]+", query)}
    scored = []
    for row in source_segments:
        text = _clean_text(str(row.get("text") or ""))
        terms = {term.lower() for term in re.findall(r"[A-Za-z0-9_]+", text)}
        score = len(query_terms & terms)
        if score > 0:
            scored.append((score, row, text))
    scored.sort(key=lambda item: (-item[0], str(item[1].get("id") or item[1].get("segment_id") or "")))
    chunks: List[Dict[str, Any]] = []
    budget = 0
    for score, row, text in scored:
        if chunks and budget + len(text) > max_chars:
            break
        chunks.append({
            "source_segment_id": str(row.get("id") or row.get("segment_id") or ""),
            "score": score,
            "text": text,
        })
        budget += len(text)
    return {
        "lane": "late_chunk_query_embedding",
        "query": query,
        "source_view_alias": "default_local_text",
        "chunk_count": len(chunks),
        "chunks": chunks,
        "traceable": all(bool(row["source_segment_id"]) for row in chunks),
    }


def build_multivector_span_plan(
    source_segments: Sequence[Dict[str, Any]],
    *,
    span_chars: int = 240,
) -> FrontierRepresentationPlan:
    spans: List[Dict[str, Any]] = []
    for row in source_segments:
        text = _clean_text(str(row.get("text") or ""))
        if not text:
            continue
        source_id = str(row.get("id") or row.get("segment_id") or "")
        for start in range(0, len(text), span_chars):
            span = text[start:start + span_chars].strip()
            if not span:
                continue
            spans.append({
                "segment_index": len(spans),
                "segment_type": "multivector_span",
                "text": span,
                "source_segment_ids": [source_id],
                "span_start_char": start,
                "span_end_char": start + len(span),
            })
    return FrontierRepresentationPlan(
        lane="multivector_token_or_span",
        source_view_alias="default_local_text",
        target_view_alias="multivector_spans",
        segments=spans,
    )


def build_table_native_plan(markdown_text: str, *, target_view_alias: str = "table_native") -> FrontierRepresentationPlan:
    rows: List[Dict[str, Any]] = []
    for line in str(markdown_text or "").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "|" not in stripped[1:]:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if cells and all(set(cell) <= {"-", ":", " "} for cell in cells):
            continue
        rows.append({
            "segment_index": len(rows),
            "segment_type": "table",
            "text": " | ".join(cells),
            "cells": cells,
        })
    return FrontierRepresentationPlan(
        lane="table_cell_or_row_text",
        source_view_alias="scanner_objects",
        target_view_alias=target_view_alias,
        segments=rows,
        warnings=[] if rows else ["no_markdown_table_rows_detected"],
    )


def build_visual_region_plan(scanner_units: Sequence[Dict[str, Any]], *, target_view_alias: str = "visual_page_region") -> FrontierRepresentationPlan:
    regions: List[Dict[str, Any]] = []
    for unit in scanner_units:
        anchor = dict(unit.get("anchor_payload") or {})
        if not (anchor.get("bbox") or anchor.get("polygon")):
            continue
        regions.append({
            "segment_index": len(regions),
            "segment_type": "visual_region",
            "text": str(unit.get("text") or ""),
            "source_unit_indices": [int(unit.get("unit_index", len(regions)) or 0)],
            "page": anchor.get("page"),
            "bbox": anchor.get("bbox"),
            "polygon": anchor.get("polygon"),
        })
    return FrontierRepresentationPlan(
        lane="visual_page_region",
        source_view_alias="scanner_objects",
        target_view_alias=target_view_alias,
        segments=regions,
        warnings=[] if regions else ["no_visual_regions_detected"],
    )


def materialize_frontier_representation_rows(
    *,
    document_version_id: str,
    artifact_id: str,
    plan: FrontierRepresentationPlan,
) -> Dict[str, Any]:
    unit_view_config = {
        "source": "frontier_representation_plan",
        "lane": plan.lane,
        "source_view_alias": plan.source_view_alias,
        "target_view_alias": plan.target_view_alias,
    }
    unit_view = DocumentUnitView(
        document_version_id=document_version_id,
        artifact_id=artifact_id,
        unit_kind=f"{plan.lane}_unit",
        recipe_id=f"{plan.lane}_units_v1",
        recipe_version="v1",
        config_hash=content_fingerprint(text="", md=unit_view_config, salt="frontier_unit_view"),
        status="ready",
        config=unit_view_config,
        stats={"unit_count": len(plan.segments)},
    )
    unit_rows: List[DocumentUnit] = []
    segment_rows: List[DocumentSegment] = []
    member_rows: List[DocumentSegmentMember] = []
    segment_view_config = {
        "source": "frontier_representation_plan",
        "lane": plan.lane,
        "source_view_alias": plan.source_view_alias,
        "target_view_alias": plan.target_view_alias,
    }
    segment_view = DocumentSegmentView(
        document_version_id=document_version_id,
        source_unit_view_id=unit_view.id,
        view_alias=plan.target_view_alias,
        recipe_id=f"{plan.lane}_segments_v1",
        recipe_version="v1",
        config_hash=content_fingerprint(text="", md=segment_view_config, salt="frontier_segment_view"),
        segment_type_default=str(plan.segments[0].get("segment_type", "frontier")) if plan.segments else "frontier",
        status="ready",
        is_current=True,
        config=segment_view_config,
        stats={"unit_count": len(plan.segments), "segment_count": len(plan.segments)},
    )
    for idx, segment in enumerate(plan.segments):
        text = str(segment.get("text") or "")
        unit = DocumentUnit(
            unit_view_id=unit_view.id,
            unit_index=idx,
            text=text,
            md={
                "frontier_lane": plan.lane,
                "source_segment_ids": list(segment.get("source_segment_ids") or []),
                "source_unit_indices": list(segment.get("source_unit_indices") or []),
                **{k: v for k, v in dict(segment).items() if k not in {"text"}},
            },
        )
        unit_rows.append(unit)
        segment_row = DocumentSegment(
            document_version_id=document_version_id,
            artifact_id=artifact_id,
            segment_view_id=segment_view.id,
            segment_type=str(segment.get("segment_type") or "frontier"),
            segment_index=int(segment.get("segment_index", idx) or 0),
            text=text,
            md={
                "frontier_lane": plan.lane,
                "source_view_alias": plan.source_view_alias,
                **{k: v for k, v in dict(segment).items() if k not in {"text"}},
            },
        )
        segment_rows.append(segment_row)
        member_rows.append(
            DocumentSegmentMember(
                segment_id=segment_row.id,
                unit_id=unit.id,
                member_index=0,
                role="main",
                unit_start_char=0,
                unit_end_char=len(text),
                md={"frontier_lane": plan.lane},
            )
        )
    return {
        "unit_view": unit_view,
        "units": unit_rows,
        "segment_view": segment_view,
        "segments": segment_rows,
        "members": member_rows,
    }

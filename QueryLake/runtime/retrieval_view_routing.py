from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

from QueryLake.runtime.representation_materialization_v2 import (
    MaterializationState,
    RepresentationEvaluationMode,
    RepresentationType,
    evaluate_representation_availability,
)


@dataclass(frozen=True)
class RetrievalViewRoute:
    requested_view: str
    effective_view: str
    table: str
    representation_type: str
    fallback_used: bool
    fallback_reason: Optional[str]
    blockers: tuple[str, ...]
    segment_view_alias: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


PUBLIC_VIEW_TO_REPRESENTATION: Dict[str, RepresentationType] = {
    "compat_chunk": RepresentationType.compat_chunk_text,
    "canonical_segment": RepresentationType.canonical_segment_text,
    "semantic_segment": RepresentationType.semantic_segment_text,
    "page_block": RepresentationType.page_block_text,
    "table": RepresentationType.table_cell_or_row_text,
    "layout_region": RepresentationType.layout_region_text,
    "late_chunk": RepresentationType.late_chunk_query_embedding,
    "multivector": RepresentationType.multivector_token_or_span,
    "visual_page_region": RepresentationType.visual_page_region,
}

REPRESENTATION_TO_TABLE: Dict[RepresentationType, str] = {
    RepresentationType.compat_chunk_text: "document_chunk",
    RepresentationType.canonical_segment_text: "segment",
    RepresentationType.semantic_segment_text: "segment",
    RepresentationType.page_block_text: "segment",
    RepresentationType.table_cell_or_row_text: "segment",
    RepresentationType.layout_region_text: "segment",
    RepresentationType.late_chunk_query_embedding: "segment",
    RepresentationType.multivector_token_or_span: "segment",
    RepresentationType.visual_page_region: "segment",
}

REPRESENTATION_TO_SEGMENT_VIEW_ALIAS: Dict[RepresentationType, Optional[str]] = {
    RepresentationType.compat_chunk_text: None,
    RepresentationType.canonical_segment_text: "default_local_text",
    RepresentationType.semantic_segment_text: "semantic_text",
    RepresentationType.page_block_text: "page_block",
    RepresentationType.table_cell_or_row_text: "table_native",
    RepresentationType.layout_region_text: "layout_region",
    RepresentationType.late_chunk_query_embedding: "late_chunk",
    RepresentationType.multivector_token_or_span: "multivector_spans",
    RepresentationType.visual_page_region: "visual_page_region",
}


def _env_flag(name: str, default: bool = False) -> bool:
    raw = (os.getenv(name, "1" if default else "0") or "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def current_retrieval_view_feature_flags() -> Dict[str, bool]:
    names = {
        "QUERYLAKE_RETRIEVAL_SEGMENT_ENABLED",
        "QUERYLAKE_RETRIEVAL_MULTI_VIEW_ENABLED",
        "QUERYLAKE_RETRIEVAL_LAYOUT_VIEW_ENABLED",
        "QUERYLAKE_RETRIEVAL_TABLE_VIEW_ENABLED",
        "QUERYLAKE_RETRIEVAL_LATE_CHUNKING_ENABLED",
        "QUERYLAKE_RETRIEVAL_MULTIVECTOR_ENABLED",
        "QUERYLAKE_RETRIEVAL_VISUAL_REGION_ENABLED",
    }
    return {name: _env_flag(name, False) for name in sorted(names)}


def resolve_retrieval_view_route(
    *,
    requested_view: Optional[str],
    current_table: str = "document_chunk",
    materialization_status: MaterializationState | str = MaterializationState.ready,
    prerequisites: Optional[Dict[str, bool]] = None,
    feature_flags: Optional[Dict[str, bool]] = None,
    mode: RepresentationEvaluationMode | str = RepresentationEvaluationMode.fallback_allowed,
) -> RetrievalViewRoute:
    if requested_view is None or str(requested_view).strip() == "":
        representation = RepresentationType.canonical_segment_text if current_table == "segment" else RepresentationType.compat_chunk_text
        return RetrievalViewRoute(
            requested_view="default",
            effective_view="canonical_segment" if current_table == "segment" else "compat_chunk",
            table=current_table,
            representation_type=representation.value,
            fallback_used=False,
            fallback_reason=None,
            blockers=(),
            segment_view_alias=REPRESENTATION_TO_SEGMENT_VIEW_ALIAS[representation],
        )

    requested = str(requested_view).strip()
    if requested not in PUBLIC_VIEW_TO_REPRESENTATION:
        available = ", ".join(sorted(PUBLIC_VIEW_TO_REPRESENTATION))
        raise ValueError(f"Unknown retrieval_view={requested}; available={available}")

    representation = PUBLIC_VIEW_TO_REPRESENTATION[requested]
    availability = evaluate_representation_availability(
        representation_type=representation,
        status=materialization_status,
        prerequisites=prerequisites or {},
        feature_flags=feature_flags if feature_flags is not None else current_retrieval_view_feature_flags(),
        mode=mode,
    )
    effective_representation = availability.fallback_representation_type if availability.fallback_allowed else representation
    assert effective_representation is not None
    effective_view = next(
        name for name, candidate in PUBLIC_VIEW_TO_REPRESENTATION.items()
        if candidate == effective_representation
    )
    return RetrievalViewRoute(
        requested_view=requested,
        effective_view=effective_view,
        table=REPRESENTATION_TO_TABLE[effective_representation],
        representation_type=effective_representation.value,
        fallback_used=bool(availability.fallback_allowed),
        fallback_reason=availability.fallback_reason,
        blockers=tuple(availability.blockers),
        segment_view_alias=REPRESENTATION_TO_SEGMENT_VIEW_ALIAS[effective_representation],
    )

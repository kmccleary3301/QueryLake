from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from QueryLake.runtime.projection_contracts import ProjectionAuthorityReference


class MaterializationState(str, Enum):
    absent = "absent"
    building = "building"
    ready = "ready"
    stale = "stale"
    failed = "failed"


class InvalidationReason(str, Enum):
    authority_content_changed = "authority_content_changed"
    authority_metadata_changed = "authority_metadata_changed"
    representation_recipe_changed = "representation_recipe_changed"
    embedding_model_changed = "embedding_model_changed"
    index_schema_changed = "index_schema_changed"
    capability_profile_changed = "capability_profile_changed"
    manual_rebuild_requested = "manual_rebuild_requested"


class RepresentationType(str, Enum):
    compat_chunk_text = "compat_chunk_text"
    canonical_segment_text = "canonical_segment_text"
    semantic_segment_text = "semantic_segment_text"
    page_block_text = "page_block_text"
    table_cell_or_row_text = "table_cell_or_row_text"
    layout_region_text = "layout_region_text"
    late_chunk_query_embedding = "late_chunk_query_embedding"
    multivector_token_or_span = "multivector_token_or_span"
    visual_page_region = "visual_page_region"


class RepresentationEvaluationMode(str, Enum):
    fallback_allowed = "fallback_allowed"
    strict = "strict"
    promotion = "promotion"


class RepresentationScopeRef(BaseModel):
    scope_id: str
    authority_model: str
    compatibility_projection: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class RepresentationDescriptorV2(BaseModel):
    representation_type: RepresentationType
    authority_model: str
    source_view_alias: str | None = None
    eager_mode: str = "eager"
    public_state: str = "internal"
    projection_ids: list[str] = Field(default_factory=list)
    required_feature_flags: list[str] = Field(default_factory=list)
    fallback_representation_type: RepresentationType | None = None
    notes: str = ""


class MaterializationTargetV2(BaseModel):
    target_id: str
    profile_id: str
    representation_scope: RepresentationScopeRef
    record_schema: str
    target_backend_family: str
    target_backend_name: str
    authority_reference: ProjectionAuthorityReference
    metadata: dict[str, Any] = Field(default_factory=dict)


class MaterializationStatusV2(BaseModel):
    target_id: str
    state: MaterializationState
    invalidated_by: list[InvalidationReason] = Field(default_factory=list)
    last_build_revision: str | None = None
    last_build_timestamp: str | None = None
    error_summary: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RepresentationAvailability(BaseModel):
    representation_type: RepresentationType
    available: bool
    strict_available: bool
    status: MaterializationState
    blockers: list[str] = Field(default_factory=list)
    fallback_representation_type: RepresentationType | None = None
    fallback_allowed: bool = False
    fallback_reason: str | None = None
    descriptor: RepresentationDescriptorV2


REPRESENTATION_DESCRIPTORS_V2: dict[RepresentationType, RepresentationDescriptorV2] = {
    RepresentationType.compat_chunk_text: RepresentationDescriptorV2(
        representation_type=RepresentationType.compat_chunk_text,
        authority_model="document_chunk_compatibility",
        source_view_alias=None,
        eager_mode="eager",
        public_state="default_compatibility",
        projection_ids=[
            "document_chunk_lexical_projection_v1",
            "document_chunk_dense_projection_v1",
            "document_chunk_sparse_projection_v1",
        ],
        notes="Legacy-compatible DocumentChunk text representation. Public default until segment lanes are promoted.",
    ),
    RepresentationType.canonical_segment_text: RepresentationDescriptorV2(
        representation_type=RepresentationType.canonical_segment_text,
        authority_model="document_segment",
        source_view_alias="default_local_text",
        eager_mode="eager",
        public_state="internal_candidate",
        projection_ids=[
            "segment_lexical_projection_v1",
            "segment_dense_projection_v1",
            "segment_sparse_projection_v1",
        ],
        required_feature_flags=["QUERYLAKE_RETRIEVAL_SEGMENT_ENABLED"],
        fallback_representation_type=RepresentationType.compat_chunk_text,
        notes="Canonical segment text lane for default local-text segment views.",
    ),
    RepresentationType.semantic_segment_text: RepresentationDescriptorV2(
        representation_type=RepresentationType.semantic_segment_text,
        authority_model="document_segment",
        source_view_alias="semantic_text",
        eager_mode="eager",
        public_state="experimental",
        projection_ids=["segment_lexical_projection_v1", "segment_dense_projection_v1"],
        required_feature_flags=["QUERYLAKE_RETRIEVAL_MULTI_VIEW_ENABLED"],
        fallback_representation_type=RepresentationType.compat_chunk_text,
        notes="Semantic segment pilot view. Not default.",
    ),
    RepresentationType.page_block_text: RepresentationDescriptorV2(
        representation_type=RepresentationType.page_block_text,
        authority_model="document_segment",
        source_view_alias="page_block",
        eager_mode="eager",
        public_state="experimental",
        projection_ids=["segment_lexical_projection_v1", "segment_dense_projection_v1"],
        required_feature_flags=["QUERYLAKE_RETRIEVAL_LAYOUT_VIEW_ENABLED"],
        fallback_representation_type=RepresentationType.compat_chunk_text,
        notes="Scanner/OCR page block text lane.",
    ),
    RepresentationType.table_cell_or_row_text: RepresentationDescriptorV2(
        representation_type=RepresentationType.table_cell_or_row_text,
        authority_model="document_segment",
        source_view_alias="table_native",
        eager_mode="eager",
        public_state="experimental",
        projection_ids=["segment_lexical_projection_v1"],
        required_feature_flags=["QUERYLAKE_RETRIEVAL_TABLE_VIEW_ENABLED"],
        fallback_representation_type=RepresentationType.compat_chunk_text,
        notes="Table-native row/cell text lane with structured table anchors.",
    ),
    RepresentationType.layout_region_text: RepresentationDescriptorV2(
        representation_type=RepresentationType.layout_region_text,
        authority_model="document_segment",
        source_view_alias="layout_region",
        eager_mode="eager",
        public_state="experimental",
        projection_ids=["segment_lexical_projection_v1"],
        required_feature_flags=["QUERYLAKE_RETRIEVAL_LAYOUT_VIEW_ENABLED"],
        fallback_representation_type=RepresentationType.compat_chunk_text,
        notes="Layout region text lane from scanner envelopes.",
    ),
    RepresentationType.late_chunk_query_embedding: RepresentationDescriptorV2(
        representation_type=RepresentationType.late_chunk_query_embedding,
        authority_model="document_segment",
        source_view_alias="default_local_text",
        eager_mode="query_time",
        public_state="experimental",
        projection_ids=["segment_dense_projection_v1"],
        required_feature_flags=["QUERYLAKE_RETRIEVAL_LATE_CHUNKING_ENABLED"],
        fallback_representation_type=RepresentationType.compat_chunk_text,
        notes="Late chunking pilot. Query-time representation; must preserve traceability to authority segments.",
    ),
    RepresentationType.multivector_token_or_span: RepresentationDescriptorV2(
        representation_type=RepresentationType.multivector_token_or_span,
        authority_model="document_segment",
        source_view_alias="default_local_text",
        eager_mode="eager",
        public_state="experimental",
        projection_ids=["segment_dense_projection_v1"],
        required_feature_flags=["QUERYLAKE_RETRIEVAL_MULTIVECTOR_ENABLED"],
        fallback_representation_type=RepresentationType.compat_chunk_text,
        notes="Multivector token/span pilot bound back to authority segment members.",
    ),
    RepresentationType.visual_page_region: RepresentationDescriptorV2(
        representation_type=RepresentationType.visual_page_region,
        authority_model="document_segment",
        source_view_alias="visual_page_region",
        eager_mode="eager",
        public_state="experimental",
        projection_ids=[],
        required_feature_flags=["QUERYLAKE_RETRIEVAL_VISUAL_REGION_ENABLED"],
        fallback_representation_type=RepresentationType.page_block_text,
        notes="Visual page/region pilot. Requires scanner layout/page artifacts.",
    ),
}


def list_representation_descriptors() -> dict[RepresentationType, RepresentationDescriptorV2]:
    return dict(REPRESENTATION_DESCRIPTORS_V2)


def get_representation_descriptor(representation_type: RepresentationType | str) -> RepresentationDescriptorV2:
    key = representation_type if isinstance(representation_type, RepresentationType) else RepresentationType(str(representation_type))
    return REPRESENTATION_DESCRIPTORS_V2[key]


def compute_invalidation_reasons(
    *,
    authority_revision_changed: bool = False,
    authority_metadata_changed: bool = False,
    representation_recipe_changed: bool = False,
    embedding_model_changed: bool = False,
    index_schema_changed: bool = False,
    capability_profile_changed: bool = False,
    manual_rebuild_requested: bool = False,
) -> list[InvalidationReason]:
    reasons: list[InvalidationReason] = []
    if authority_revision_changed:
        reasons.append(InvalidationReason.authority_content_changed)
    if authority_metadata_changed:
        reasons.append(InvalidationReason.authority_metadata_changed)
    if representation_recipe_changed:
        reasons.append(InvalidationReason.representation_recipe_changed)
    if embedding_model_changed:
        reasons.append(InvalidationReason.embedding_model_changed)
    if index_schema_changed:
        reasons.append(InvalidationReason.index_schema_changed)
    if capability_profile_changed:
        reasons.append(InvalidationReason.capability_profile_changed)
    if manual_rebuild_requested:
        reasons.append(InvalidationReason.manual_rebuild_requested)
    return reasons


def evaluate_representation_availability(
    *,
    representation_type: RepresentationType | str,
    status: MaterializationState | str,
    prerequisites: dict[str, bool] | None = None,
    feature_flags: dict[str, bool] | None = None,
    mode: RepresentationEvaluationMode | str = RepresentationEvaluationMode.fallback_allowed,
) -> RepresentationAvailability:
    descriptor = get_representation_descriptor(representation_type)
    resolved_status = status if isinstance(status, MaterializationState) else MaterializationState(str(status))
    resolved_mode = mode if isinstance(mode, RepresentationEvaluationMode) else RepresentationEvaluationMode(str(mode))
    prerequisites = dict(prerequisites or {})
    feature_flags = dict(feature_flags or {})

    blockers: list[str] = []
    for name, ok in sorted(prerequisites.items()):
        if not ok:
            blockers.append(f"missing_prerequisite:{name}")
    for flag_name in descriptor.required_feature_flags:
        if not bool(feature_flags.get(flag_name, False)):
            blockers.append(f"feature_flag_disabled:{flag_name}")
    if resolved_status != MaterializationState.ready:
        blockers.append(f"materialization_status:{resolved_status.value}")

    strict_available = len(blockers) == 0
    fallback_allowed = (
        not strict_available
        and descriptor.fallback_representation_type is not None
        and resolved_mode == RepresentationEvaluationMode.fallback_allowed
    )
    return RepresentationAvailability(
        representation_type=descriptor.representation_type,
        available=strict_available or fallback_allowed,
        strict_available=strict_available,
        status=resolved_status,
        blockers=blockers,
        fallback_representation_type=descriptor.fallback_representation_type,
        fallback_allowed=fallback_allowed,
        fallback_reason=None if not fallback_allowed else ";".join(blockers),
        descriptor=descriptor,
    )

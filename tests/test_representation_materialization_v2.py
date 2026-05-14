from QueryLake.runtime.representation_materialization_v2 import (
    InvalidationReason,
    MaterializationState,
    MaterializationStatusV2,
    MaterializationTargetV2,
    RepresentationEvaluationMode,
    RepresentationScopeRef,
    RepresentationType,
    compute_invalidation_reasons,
    evaluate_representation_availability,
    get_representation_descriptor,
    list_representation_descriptors,
)
from QueryLake.runtime.projection_contracts import ProjectionAuthorityReference


def test_materialization_target_v2_roundtrip():
    target = MaterializationTargetV2(
        target_id="segment_lexical_projection_v2",
        profile_id="sqlite_fts5_dense_sidecar_local_v1",
        representation_scope=RepresentationScopeRef(
            scope_id="document_segment",
            authority_model="document_segment",
        ),
        record_schema="LexicalProjectionRecord",
        target_backend_family="lexical_index",
        target_backend_name="sqlite_fts5",
        authority_reference=ProjectionAuthorityReference(authority_model="document_segment"),
    )
    payload = target.model_dump()
    rebuilt = MaterializationTargetV2.model_validate(payload)
    assert rebuilt.target_backend_name == "sqlite_fts5"
    assert rebuilt.representation_scope.scope_id == "document_segment"


def test_materialization_status_v2_tracks_state_and_invalidations():
    status = MaterializationStatusV2(
        target_id="segment_lexical_projection_v2",
        state=MaterializationState.stale,
        invalidated_by=[InvalidationReason.authority_content_changed],
        last_build_revision="r1",
    )
    assert status.state == MaterializationState.stale
    assert status.invalidated_by == [InvalidationReason.authority_content_changed]
    assert status.last_build_revision == "r1"


def test_representation_taxonomy_includes_north_star_lanes():
    descriptors = list_representation_descriptors()
    assert RepresentationType.compat_chunk_text in descriptors
    assert RepresentationType.canonical_segment_text in descriptors
    assert RepresentationType.semantic_segment_text in descriptors
    assert RepresentationType.page_block_text in descriptors
    assert RepresentationType.table_cell_or_row_text in descriptors
    assert RepresentationType.late_chunk_query_embedding in descriptors
    assert RepresentationType.multivector_token_or_span in descriptors
    assert RepresentationType.visual_page_region in descriptors


def test_canonical_segment_descriptor_declares_segment_authority_and_fallback():
    descriptor = get_representation_descriptor(RepresentationType.canonical_segment_text)
    assert descriptor.authority_model == "document_segment"
    assert descriptor.source_view_alias == "default_local_text"
    assert "segment_lexical_projection_v1" in descriptor.projection_ids
    assert descriptor.fallback_representation_type == RepresentationType.compat_chunk_text
    assert "QUERYLAKE_RETRIEVAL_SEGMENT_ENABLED" in descriptor.required_feature_flags


def test_representation_availability_strict_success_requires_ready_and_flags():
    availability = evaluate_representation_availability(
        representation_type=RepresentationType.canonical_segment_text,
        status=MaterializationState.ready,
        prerequisites={"segment_view": True, "projection_descriptor": True},
        feature_flags={"QUERYLAKE_RETRIEVAL_SEGMENT_ENABLED": True},
        mode=RepresentationEvaluationMode.strict,
    )
    assert availability.available is True
    assert availability.strict_available is True
    assert availability.blockers == []
    assert availability.fallback_allowed is False


def test_representation_availability_reports_fallback_when_allowed():
    availability = evaluate_representation_availability(
        representation_type=RepresentationType.canonical_segment_text,
        status=MaterializationState.absent,
        prerequisites={"segment_view": False},
        feature_flags={"QUERYLAKE_RETRIEVAL_SEGMENT_ENABLED": False},
        mode=RepresentationEvaluationMode.fallback_allowed,
    )
    assert availability.available is True
    assert availability.strict_available is False
    assert availability.fallback_allowed is True
    assert availability.fallback_representation_type == RepresentationType.compat_chunk_text
    assert "missing_prerequisite:segment_view" in availability.blockers
    assert "feature_flag_disabled:QUERYLAKE_RETRIEVAL_SEGMENT_ENABLED" in availability.blockers
    assert "materialization_status:absent" in availability.blockers


def test_representation_availability_promotion_mode_does_not_silent_fallback():
    availability = evaluate_representation_availability(
        representation_type=RepresentationType.canonical_segment_text,
        status=MaterializationState.stale,
        prerequisites={"segment_view": True},
        feature_flags={"QUERYLAKE_RETRIEVAL_SEGMENT_ENABLED": True},
        mode=RepresentationEvaluationMode.promotion,
    )
    assert availability.available is False
    assert availability.strict_available is False
    assert availability.fallback_allowed is False
    assert availability.blockers == ["materialization_status:stale"]


def test_compute_invalidation_reasons_is_explicit_and_ordered():
    reasons = compute_invalidation_reasons(
        authority_revision_changed=True,
        embedding_model_changed=True,
        manual_rebuild_requested=True,
    )
    assert reasons == [
        InvalidationReason.authority_content_changed,
        InvalidationReason.embedding_model_changed,
        InvalidationReason.manual_rebuild_requested,
    ]

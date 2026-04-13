from QueryLake.runtime.projection_contracts import ProjectionAuthorityReference
from QueryLake.runtime.representation_materialization_v2 import (
    InvalidationReason,
    MaterializationState,
    MaterializationStatusV2,
    MaterializationTargetV2,
    RepresentationScopeRef,
)


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

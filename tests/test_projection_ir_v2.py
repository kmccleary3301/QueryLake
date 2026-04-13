from QueryLake.runtime.projection_ir_v2 import (
    ProjectionBuildabilityClass,
    ProjectionDependencyRef,
    RouteProjectionIRV2,
    instantiate_projection_ir_v2,
)


def test_route_projection_ir_v2_preserves_required_and_optional_targets():
    ir = RouteProjectionIRV2(
        profile_id="sqlite_fts5_dense_sidecar_local_v1",
        route_id="search_bm25.segment",
        representation_scope_id="document_segment",
        required_targets=[
            ProjectionDependencyRef(
                target_id="segment_lexical_projection_v2",
                target_backend_family="lexical_index",
                support_state="supported",
            )
        ],
        optional_targets=[
            ProjectionDependencyRef(
                target_id="segment_dense_projection_v2",
                required=False,
                target_backend_family="dense_index",
                support_state="planned",
            )
        ],
        capability_dependencies=["retrieval.lexical.bm25"],
        buildability_class=ProjectionBuildabilityClass.executable_requires_build,
        recovery_hints=["bootstrap lexical projection"],
    )
    assert ir.required_targets[0].target_id == "segment_lexical_projection_v2"
    assert ir.optional_targets[0].required is False
    assert ir.buildability_class == ProjectionBuildabilityClass.executable_requires_build


def test_instantiate_projection_ir_v2_normalizes_sparse_fallback_payload():
    ir = instantiate_projection_ir_v2(
        None,
        profile_id="aws_aurora_pg_opensearch_v1",
        route_id="search_hybrid.document_chunk",
        representation_scope_id="document_chunk",
        required_targets=[
            {
                "target_id": "document_chunk_lexical_projection_v1",
                "required": True,
                "target_backend_family": "projection_index",
                "support_state": "degraded",
                "metadata": {"lane_family": "lexical"},
            }
        ],
        capability_dependencies=["retrieval.lexical.bm25"],
        runtime_blockers=["projection_build_required"],
        buildability_class="degraded_executable",
        recovery_hints=["bootstrap_required_projections"],
        metadata={"fallback_projection_ir_v2": True},
    )
    payload = ir.model_dump()
    assert payload["route_id"] == "search_hybrid.document_chunk"
    assert payload["representation_scope_id"] == "document_chunk"
    assert payload["buildability_class"] == "degraded_executable"
    assert payload["required_targets"][0]["target_id"] == "document_chunk_lexical_projection_v1"
    assert payload["metadata"]["fallback_projection_ir_v2"] is True

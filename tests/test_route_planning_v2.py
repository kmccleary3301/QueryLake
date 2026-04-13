from QueryLake.runtime.route_planning_v2 import (
    instantiate_route_planning_v2,
    instantiate_route_projection_ir_v2,
    instantiate_route_query_ir_v2,
)


def test_instantiate_route_query_ir_v2_uses_route_payload_defaults():
    payload = {
        "route_id": "search_bm25.document_chunk",
        "representation_scope_id": "document_chunk",
        "planning_v2": {
            "query_ir_v2_template": {
                "route_id": "search_bm25.document_chunk",
                "representation_scope_id": "document_chunk",
                "strictness_policy": "approximate",
                "use_dense": False,
                "use_sparse": False,
            },
        },
    }

    query_ir = instantiate_route_query_ir_v2(
        payload,
        raw_query_text="vapor recovery",
        lexical_query_text="vapor recovery",
        collection_ids=["c1"],
        planner_hints={"table": "document_chunk"},
    )

    assert query_ir["route_id"] == "search_bm25.document_chunk"
    assert query_ir["representation_scope_id"] == "document_chunk"
    assert query_ir["raw_query_text"] == "vapor recovery"
    assert query_ir["filter_ir"]["collection_ids"] == ["c1"]
    assert query_ir["planner_hints"]["table"] == "document_chunk"


def test_instantiate_route_projection_ir_v2_uses_payload_identity():
    payload = {
        "route_id": "search_hybrid.document_chunk",
        "representation_scope_id": "document_chunk",
        "profile_id": "aws_aurora_pg_opensearch_v1",
        "planning_v2": {
            "projection_ir_v2": {
                "buildability_class": "degraded_executable",
                "required_targets": [
                    {
                        "target_id": "document_chunk_lexical_projection_v1",
                        "required": True,
                        "target_backend_family": "lexical_index",
                        "support_state": "degraded",
                        "metadata": {"target_backend_name": "opensearch"},
                    }
                ],
                "capability_dependencies": ["retrieval.lexical.bm25", "retrieval.dense.vector"],
            }
        },
    }

    projection_ir = instantiate_route_projection_ir_v2(
        payload,
        metadata={"planning_surface": "route_recovery"},
    )

    assert projection_ir["route_id"] == "search_hybrid.document_chunk"
    assert projection_ir["representation_scope_id"] == "document_chunk"
    assert projection_ir["buildability_class"] == "degraded_executable"
    assert projection_ir["metadata"]["planning_surface"] == "route_recovery"


def test_instantiate_route_planning_v2_returns_canonical_payload():
    payload = {
        "route_id": "search_file_chunks",
        "representation_scope_id": "file_chunk",
        "profile_id": "sqlite_fts5_dense_sidecar_local_v1",
        "planning_v2": {
            "planning_surface": "route_resolution",
            "query_ir_v2_template": {
                "route_id": "search_file_chunks",
                "representation_scope_id": "file_chunk",
                "strictness_policy": "approximate",
                "use_dense": False,
                "use_sparse": False,
            },
            "projection_ir_v2": {
                "buildability_class": "degraded_executable",
                "required_targets": [
                    {
                        "target_id": "file_chunk_lexical_projection_v1",
                        "required": True,
                        "target_backend_family": "lexical_index",
                        "support_state": "degraded",
                        "metadata": {"target_backend_name": "sqlite_fts5"},
                    }
                ],
            },
        },
    }

    planning = instantiate_route_planning_v2(
        payload,
        raw_query_text="flue gas analysis",
        lexical_query_text="flue gas analysis",
        projection_metadata={"recovery_surface": "bringup"},
    )

    assert planning["planning_surface"] == "route_resolution"
    assert planning["query_ir_v2_template"]["route_id"] == "search_file_chunks"
    assert planning["query_ir_v2_template"]["raw_query_text"] == "flue gas analysis"
    assert planning["projection_ir_v2"]["route_id"] == "search_file_chunks"
    assert planning["projection_ir_v2"]["representation_scope_id"] == "file_chunk"
    assert planning["projection_ir_v2"]["metadata"]["recovery_surface"] == "bringup"


def test_instantiate_route_planning_v2_synthesizes_query_ir_when_planning_payload_absent():
    payload = {
        "route_id": "search_hybrid.document_chunk",
        "representation_scope_id": "document_chunk",
    }

    planning = instantiate_route_planning_v2(
        payload,
        raw_query_text="vapor recovery",
        lexical_query_text="vapor recovery",
        use_dense=True,
        use_sparse=False,
        collection_ids=["c1"],
    )

    assert planning["planning_surface"] == "route_resolution"
    assert planning["query_ir_v2_template"]["route_id"] == "search_hybrid.document_chunk"
    assert planning["query_ir_v2_template"]["representation_scope_id"] == "document_chunk"
    assert planning["query_ir_v2_template"]["use_dense"] is True
    assert planning["query_ir_v2_template"]["filter_ir"]["collection_ids"] == ["c1"]
    assert "projection_ir_v2" not in planning


def test_instantiate_route_projection_ir_v2_synthesizes_fallback_projection_plan():
    payload = {
        "route_id": "search_hybrid.document_chunk",
        "profile_id": "aws_aurora_pg_opensearch_v1",
        "backend_stack": {
            "authority": "aurora_postgresql",
            "lexical": "opensearch",
            "dense": "opensearch",
            "sparse": "opensearch",
            "graph": "aurora_postgresql_segment_relations",
        },
        "projection_descriptors": ["document_chunk_lexical_projection_v1"],
        "support_state": "degraded",
    }

    projection_ir = instantiate_route_projection_ir_v2(payload)

    assert projection_ir["route_id"] == "search_hybrid.document_chunk"
    assert projection_ir["representation_scope_id"] == "document_chunk"
    assert projection_ir["buildability_class"] == "degraded_executable"
    assert projection_ir["capability_dependencies"] == [
        "retrieval.lexical.bm25",
        "retrieval.dense.vector",
    ]
    assert projection_ir["required_targets"] == [
        {
            "target_id": "document_chunk_lexical_projection_v1",
            "required": True,
            "target_backend_family": "lexical_index",
            "support_state": "degraded",
            "metadata": {
                "target_backend_name": "opensearch",
                "lane_family": "lexical",
            },
        }
    ]
    assert projection_ir["runtime_blockers"] == ["projection_build_required"]
    assert projection_ir["recovery_hints"] == ["bootstrap_required_projections"]
    assert projection_ir["metadata"]["planning_surface"] == "route_resolution"

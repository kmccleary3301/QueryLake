from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from querylake_sdk import (
    HybridSearchOptions,
    QueryLakeAPIError,
    QueryLakeClient,
    UploadDirectoryOptions,
)


def _mock_client(handler):
    transport = httpx.MockTransport(handler)
    return httpx.Client(base_url="http://testserver", transport=transport)


def test_api_unwraps_success_result():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/fetch_all_collections"
        payload = json.loads(request.content.decode("utf-8"))
        assert payload["auth"]["oauth2"] == "tok_123"
        return httpx.Response(200, json={"success": True, "result": {"collections": []}})

    client = QueryLakeClient(base_url="http://testserver", oauth2="tok_123")
    client._client.close()
    client._client = _mock_client(handler)
    try:
        result = client.api("fetch_all_collections")
        assert result == {"collections": []}
    finally:
        client.close()


def test_capabilities_helpers():
    payload = {
        "profile": {
            "id": "aws_aurora_pg_opensearch_v1",
            "label": "Aurora PostgreSQL + OpenSearch",
            "implemented": True,
            "recommended": False,
            "maturity": "split_stack_executable",
            "backend_stack": {
                "authority": "aurora_postgresql",
                "lexical": "opensearch",
                "dense": "opensearch",
                "sparse": "opensearch",
                "graph": "aurora_postgresql_segment_relations",
            },
        },
        "capabilities": [
            {
                "id": "retrieval.lexical.bm25",
                "support_state": "supported",
                "summary": "BM25 lexical retrieval delegated to OpenSearch projections.",
            },
            {
                "id": "retrieval.sparse.vector",
                "support_state": "unsupported",
                "summary": "Sparse vector retrieval is not in the first executable split-stack slice.",
            },
            {
                "id": "retrieval.lexical.proximity",
                "support_state": "degraded",
                "summary": "Proximity semantics are profile-specific on the split-stack path.",
            },
        ],
        "representation_scopes": {
            "document_chunk": {
                "scope_id": "document_chunk",
                "authority_model": "document_segment",
                "compatibility_projection": True,
                "metadata": {"representation_kind": "chunk_compatibility_projection"},
            },
            "file_chunk": {
                "scope_id": "file_chunk",
                "authority_model": "file_chunk",
                "compatibility_projection": False,
                "metadata": {"representation_kind": "file_chunk_projection"},
            },
        },
        "route_support_v2": [
            {
                "route_id": "search_hybrid.document_chunk",
                "support_state": "supported",
                "implemented": True,
                "declared_executable": True,
                "declared_optional": False,
                "representation_scope": {
                    "scope_id": "document_chunk",
                    "authority_model": "document_segment",
                    "compatibility_projection": True,
                    "metadata": {"representation_kind": "chunk_compatibility_projection"},
                },
                "capability_dependencies": [
                    "retrieval.lexical.bm25",
                    "retrieval.dense.vector",
                ],
            },
            {
                "route_id": "search_file_chunks",
                "support_state": "degraded",
                "implemented": True,
                "declared_executable": True,
                "declared_optional": False,
                "representation_scope": {
                    "scope_id": "file_chunk",
                    "authority_model": "file_chunk",
                    "compatibility_projection": False,
                    "metadata": {"representation_kind": "file_chunk_projection"},
                },
                "capability_dependencies": ["retrieval.lexical.bm25"],
            },
        ],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/capabilities":
            return httpx.Response(200, json=payload)
        if request.url.path == "/v2/kernel/capabilities":
            return httpx.Response(200, json=payload)
        raise AssertionError(f"unexpected path: {request.url.path}")

    client = QueryLakeClient(base_url="http://testserver", oauth2="tok")
    client._client.close()
    client._client = _mock_client(handler)
    try:
        assert client.capabilities()["profile"]["id"] == "aws_aurora_pg_opensearch_v1"
        assert client.kernel_capabilities()["profile"]["id"] == "aws_aurora_pg_opensearch_v1"
        summary = client.capabilities_summary()
        assert summary.profile.maturity == "split_stack_executable"
        assert summary.profile.recommended is False
        assert summary.capability_map()["retrieval.lexical.bm25"].support_state == "supported"
        assert summary.support_state("retrieval.lexical.proximity") == "degraded"
        assert summary.is_supported("retrieval.lexical.bm25") is True
        assert summary.is_available("retrieval.lexical.proximity") is True
        assert summary.is_available("retrieval.lexical.proximity", allow_degraded=False) is False
        assert summary.is_available("retrieval.sparse.vector") is False
        assert [entry.id for entry in summary.degraded_capabilities()] == ["retrieval.lexical.proximity"]
        assert {entry.id for entry in summary.unavailable_capabilities()} == {"retrieval.sparse.vector"}
        assert summary.representation_scope("document_chunk").authority_model == "document_segment"
        assert summary.route_representation_scope_id("search_hybrid.document_chunk") == "document_chunk"
        assert summary.route_capability_dependencies("search_hybrid.document_chunk") == [
            "retrieval.lexical.bm25",
            "retrieval.dense.vector",
        ]
        assert client.route_representation_scope_id_from_capabilities("search_file_chunks") == "file_chunk"
        assert client.route_capability_dependencies_from_capabilities("search_file_chunks") == [
            "retrieval.lexical.bm25"
        ]
        assert client.representation_scopes()["document_chunk"]["compatibility_projection"] is True
        assert client.route_support_manifest_v2()["search_file_chunks"]["support_state"] == "degraded"
        assert client.support_state("retrieval.lexical.proximity") == "degraded"
        assert client.supports("retrieval.lexical.proximity") is True
        assert client.supports("retrieval.lexical.proximity", allow_degraded=False) is False
    finally:
        client.close()


def test_profile_diagnostics_helpers():
    payload = {
        "profile": {
            "id": "aws_aurora_pg_opensearch_v1",
            "label": "Aurora PostgreSQL + OpenSearch",
            "implemented": True,
            "recommended": False,
            "maturity": "split_stack_executable",
            "backend_stack": {
                "authority": "aurora_postgresql",
                "lexical": "opensearch",
                "dense": "opensearch",
                "sparse": "opensearch",
                "graph": "aurora_postgresql_segment_relations",
            },
        },
        "capabilities": [
            {
                "id": "retrieval.lexical.bm25",
                "support_state": "supported",
                "summary": "Lexical retrieval delegated to a projection/index plane.",
            },
            {
                "id": "retrieval.lexical.hard_constraints",
                "support_state": "unsupported",
                "summary": "Hard lexical constraints are not portable on this profile.",
            }
        ],
        "representation_scopes": {
            "document_chunk": {
                "scope_id": "document_chunk",
                "authority_model": "document_segment",
                "compatibility_projection": True,
                "metadata": {},
            }
        },
        "route_support_v2": [
            {
                "route_id": "search_hybrid.document_chunk",
                "support_state": "degraded",
                "implemented": True,
                "declared_executable": True,
                "declared_optional": False,
                "representation_scope": {
                    "scope_id": "document_chunk",
                    "authority_model": "document_segment",
                    "compatibility_projection": True,
                    "metadata": {},
                },
                "capability_dependencies": [
                    "retrieval.lexical.bm25",
                    "retrieval.dense.vector",
                ],
            }
        ],
        "configuration": {
            "profile_id": "aws_aurora_pg_opensearch_v1",
            "ready": True,
            "requirements": [
                {
                    "env_var": "QUERYLAKE_SEARCH_BACKEND_URL",
                    "kind": "url",
                    "summary": "Projection-plane OpenSearch endpoint.",
                    "required_for_execution": True,
                    "present": True,
                    "valid": True,
                },
                {
                    "env_var": "QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS",
                    "kind": "integer",
                    "summary": "Dense vector dimensions for OpenSearch mappings.",
                    "required_for_execution": False,
                    "present": False,
                    "valid": False,
                    "error": "missing",
                }
            ],
        },
        "execution_target": {
            "profile_id": "aws_aurora_pg_opensearch_v1",
            "maturity": "limited",
            "primary_recommendation": "First split-stack executable slice.",
            "mvp_scope": [
                {
                    "route_id": "search_hybrid.document_chunk",
                    "state": "supported",
                    "summary": "MVP target: lexical+dense hybrid on projection indexes.",
                },
                {
                    "route_id": "search_file_chunks",
                    "state": "supported",
                    "summary": "File-chunk lexical retrieval via OpenSearch projection indexes.",
                },
            ],
        },
        "startup_validation": {
            "boot_ready": False,
            "profile_implemented": True,
            "configuration_ready": True,
            "route_execution_ready": True,
            "route_runtime_ready": False,
            "inspected_route_ids": ["search_hybrid.document_chunk", "search_file_chunks"],
            "required_route_ids": ["search_hybrid.document_chunk", "search_file_chunks"],
            "optional_route_ids": [],
            "non_executable_required_routes": [],
            "non_executable_optional_routes": [],
            "full_route_coverage_ready": True,
            "non_runtime_ready_required_routes": ["search_hybrid.document_chunk"],
            "non_runtime_ready_optional_routes": [],
            "full_runtime_coverage_ready": False,
            "validation_error": "Deployment profile 'aws_aurora_pg_opensearch_v1' is configured, but these required retrieval routes are not runtime-ready on this deployment: search_hybrid.document_chunk.",
            "validation_error_kind": "projection_runtime_blocked",
            "validation_error_hint": "Build the missing required projections or switch to the gold profile if exact lexical constraints are required.",
            "validation_error_docs_ref": "docs/database/PROFILE_DIAGNOSTICS.md",
            "validation_error_command": "python scripts/db_compat_profile_bootstrap.py --profile aws_aurora_pg_opensearch_v1",
        },
        "route_executors": [
            {
                "route_id": "search_hybrid.document_chunk",
                "executor_id": "opensearch.search_hybrid.document_chunk.aws_aurora_pg_opensearch_v1",
                "profile_id": "aws_aurora_pg_opensearch_v1",
                "implemented": True,
                "support_state": "degraded",
                "backend_stack": {"authority": "aurora_postgresql", "lexical": "opensearch", "dense": "opensearch"},
                "lane_adapters": {},
                "planning_v2": {
                    "query_ir_v2_template": {
                        "route_id": "search_hybrid.document_chunk",
                        "representation_scope_id": "document_chunk",
                        "lane_intent": {"lexical": True, "dense": True, "sparse": False},
                    },
                    "projection_ir_v2": {
                        "route_id": "search_hybrid.document_chunk",
                        "representation_scope_id": "document_chunk",
                    },
                },
                "projection_descriptors": ["document_chunk_lexical_projection_v1", "document_chunk_dense_projection_v1"],
                "projection_targets": [
                    {
                        "projection_id": "document_chunk_lexical_projection_v1",
                        "projection_version": "v1",
                        "lane_family": "lexical",
                        "authority_model": "document_chunk_compatibility",
                        "source_scope": "document_chunk",
                        "record_schema": "document_chunk_lexical_record_v1",
                        "target_backend_family": "lexical_index",
                        "target_backend_name": "opensearch",
                        "authority_reference": {"authority_model": "document_chunk_compatibility"},
                    },
                    {
                        "projection_id": "document_chunk_dense_projection_v1",
                        "projection_version": "v1",
                        "lane_family": "dense",
                        "authority_model": "document_chunk_compatibility",
                        "source_scope": "document_chunk",
                        "record_schema": "document_chunk_dense_record_v1",
                        "target_backend_family": "dense_index",
                        "target_backend_name": "opensearch",
                        "authority_reference": {"authority_model": "document_chunk_compatibility"},
                    },
                ],
                "projection_dependency_mode": "required_external_projection",
                "projection_ready": False,
                "runtime_ready": False,
                "runtime_blockers": [
                    {
                        "kind": "projection_writer_unavailable",
                        "summary": "Required external projections depend on writer implementations that are not available on this deployment.",
                        "projection_ids": [
                            "document_chunk_lexical_projection_v1",
                            "document_chunk_dense_projection_v1",
                        ],
                    }
                ],
                "projection_missing_descriptors": ["document_chunk_lexical_projection_v1", "document_chunk_dense_projection_v1"],
                "projection_writer_gap_descriptors": ["document_chunk_lexical_projection_v1", "document_chunk_dense_projection_v1"],
                "projection_build_gap_descriptors": [],
                "projection_readiness": {
                    "document_chunk_lexical_projection_v1": {
                        "projection_id": "document_chunk_lexical_projection_v1",
                        "build_status": "absent",
                        "support_state": "supported",
                        "executable": False,
                        "action_mode": "external_writer_unavailable",
                    },
                    "document_chunk_dense_projection_v1": {
                        "projection_id": "document_chunk_dense_projection_v1",
                        "build_status": "absent",
                        "support_state": "supported",
                        "executable": False,
                        "action_mode": "external_writer_unavailable",
                    },
                },
                "representation_scope_id": "document_chunk",
                "representation_scope": {
                    "scope_id": "document_chunk",
                    "authority_model": "document_segment",
                    "compatibility_projection": True,
                    "metadata": {"representation_kind": "chunk_compatibility_projection"},
                },
                "lexical_semantics": {
                    "support_class": "degraded_supported",
                    "capability_states": {
                        "retrieval.lexical.bm25": "supported",
                        "retrieval.lexical.advanced_operators": "degraded",
                        "retrieval.lexical.phrase_boost": "degraded",
                        "retrieval.lexical.proximity": "degraded",
                        "retrieval.lexical.hard_constraints": "unsupported",
                    },
                    "degraded_capabilities": [
                        "retrieval.lexical.advanced_operators",
                        "retrieval.lexical.phrase_boost",
                        "retrieval.lexical.proximity",
                    ],
                    "unsupported_capabilities": [
                        "retrieval.lexical.hard_constraints",
                    ],
                },
            },
            {
                "route_id": "search_file_chunks",
                "executor_id": "opensearch.search_file_chunks.v1",
                "profile_id": "aws_aurora_pg_opensearch_v1",
                "implemented": True,
                "support_state": "supported",
                "backend_stack": {"authority": "aurora_postgresql", "lexical": "opensearch"},
                "lane_adapters": {},
                "projection_descriptors": ["file_chunk_lexical_projection_v1"],
                "projection_targets": [
                    {
                        "projection_id": "file_chunk_lexical_projection_v1",
                        "projection_version": "v1",
                        "lane_family": "lexical",
                        "authority_model": "file_chunk_compatibility",
                        "source_scope": "file_chunk",
                        "record_schema": "file_chunk_lexical_record_v1",
                        "target_backend_family": "lexical_index",
                        "target_backend_name": "opensearch",
                        "authority_reference": {"authority_model": "file_chunk_compatibility"},
                    }
                ],
                "projection_dependency_mode": "required_external_projection",
                "projection_ready": True,
                "runtime_ready": True,
                "runtime_blockers": [],
                "projection_missing_descriptors": [],
                "projection_readiness": {
                    "file_chunk_lexical_projection_v1": {
                        "projection_id": "file_chunk_lexical_projection_v1",
                        "build_status": "ready",
                        "support_state": "supported",
                        "executable": True,
                        "action_mode": "rebuild",
                    }
                },
                "lexical_semantics": {
                    "support_class": "degraded_supported",
                    "capability_states": {
                        "retrieval.lexical.bm25": "supported",
                        "retrieval.lexical.advanced_operators": "degraded",
                        "retrieval.lexical.phrase_boost": "degraded",
                        "retrieval.lexical.proximity": "degraded",
                        "retrieval.lexical.hard_constraints": "unsupported",
                    },
                    "degraded_capabilities": [
                        "retrieval.lexical.advanced_operators",
                        "retrieval.lexical.phrase_boost",
                        "retrieval.lexical.proximity",
                    ],
                    "unsupported_capabilities": [
                        "retrieval.lexical.hard_constraints",
                    ],
                },
                "representation_scope_id": "file_chunk",
                "representation_scope": {
                    "scope_id": "file_chunk",
                    "authority_model": "file_chunk",
                    "compatibility_projection": False,
                    "metadata": {"representation_kind": "file_chunk_projection"},
                },
            }
        ],
        "backend_connectivity": {
            "authority": {
                "backend": "aurora_postgresql",
                "status": "not_probed",
                "checked": False,
                "detail": "Authority backend reachability probing is not yet implemented for this backend family.",
            },
            "projection": {
                "backend": "opensearch",
                "status": "configured_unprobed",
                "checked": False,
                "endpoint": "https://search.example.com",
                "detail": "Projection backend is configured. Enable QUERYLAKE_PROFILE_DIAGNOSTICS_PROBE=1 to probe reachability.",
            },
        },
        "lane_diagnostics": [
            {
                "lane_family": "sparse_vector",
                "backend": "opensearch",
                "adapter_id": "placeholder.sparse_vector.aws_aurora_pg_opensearch_v1",
                "support_state": "unsupported",
                "implemented": False,
                "route_surface_declared": True,
                "capability_ids": ["retrieval.sparse.vector"],
                "execution_mode": "placeholder",
                "blocked_by_capability": "retrieval.sparse.vector",
                "placeholder_executor_id": "placeholder.sparse_vector.aws_aurora_pg_opensearch_v1",
                "recommended_profile_id": "paradedb_postgres_gold_v1",
                "hint": "Sparse retrieval is not executable on this profile. Use the gold profile for full sparse support.",
                "notes": "Reserved lane surface for future split-stack sparse execution.",
            },
            {
                "lane_family": "graph_traversal",
                "backend": "aurora_postgresql_segment_relations",
                "adapter_id": "placeholder.graph_traversal.aws_aurora_pg_opensearch_v1",
                "support_state": "unsupported",
                "implemented": False,
                "route_surface_declared": True,
                "capability_ids": ["retrieval.graph.traversal"],
                "execution_mode": "placeholder",
                "blocked_by_capability": "retrieval.graph.traversal",
                "placeholder_executor_id": "placeholder.graph_traversal.aws_aurora_pg_opensearch_v1",
                "recommended_profile_id": "paradedb_postgres_gold_v1",
                "hint": "Graph traversal is not executable on this profile. Use the gold profile for graph-aware retrieval.",
                "notes": "Reserved lane surface for future graph execution support.",
            },
        ],
    }

    projection_payload = {
        "profile_id": "aws_aurora_pg_opensearch_v1",
        "projection_items": [
            {
                "projection_id": "document_chunk_lexical_projection_v1",
                "projection_version": "v1",
                "lane_family": "lexical",
                "authority_model": "document_chunk_compatibility",
                "source_scope": "document_chunk",
                "record_schema": "LexicalProjectionRecord",
                "target_backend_family": "lexical_index",
                "backend_name": "opensearch",
                "support_state": "supported",
                "executable": False,
                "build_status": "absent",
                "action_mode": "external_writer_unavailable",
                "invalidated_by": [],
                "notes": "Compatibility lexical projection over legacy/gold document_chunk retrieval records.",
                "materialization_target": {
                    "projection_id": "document_chunk_lexical_projection_v1",
                    "projection_version": "v1",
                    "lane_family": "lexical",
                    "authority_model": "document_chunk_compatibility",
                    "source_scope": "document_chunk",
                    "record_schema": "LexicalProjectionRecord",
                    "target_backend_family": "lexical_index",
                    "target_backend_name": "opensearch",
                    "authority_reference": {
                        "authority_model": "document_chunk_compatibility",
                        "document_ids": [],
                        "segment_ids": [],
                        "collection_ids": [],
                        "metadata": {
                            "profile_id": "aws_aurora_pg_opensearch_v1",
                        },
                    },
                    "metadata": {
                        "profile_id": "aws_aurora_pg_opensearch_v1",
                    },
                },
                "build_state": {},
            }
        ],
        "metadata": {
            "projection_count": 1,
            "executable_count": 0,
            "planned_or_unavailable_count": 1,
            "support_state_counts": {"supported": 1},
            "build_status_counts": {"absent": 1},
        },
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/profile-diagnostics":
            return httpx.Response(200, json=payload)
        if request.url.path == "/v2/kernel/profile-diagnostics":
            return httpx.Response(200, json=payload)
        if request.url.path == "/v1/projection-diagnostics":
            return httpx.Response(200, json=projection_payload)
        if request.url.path == "/v2/kernel/projection-diagnostics":
            return httpx.Response(200, json=projection_payload)
        if request.url.path == "/v1/projection-plan/explain":
            return httpx.Response(
                200,
                json={
                    "profile_id": "aws_aurora_pg_opensearch_v1",
                    "projection_id": "document_chunk_lexical_projection_v1",
                    "projection_version": "v1",
                    "descriptor": {"projection_id": "document_chunk_lexical_projection_v1"},
                    "actions": [{"lane_family": "lexical", "mode": "rebuild"}],
                    "status_snapshot": [
                        {
                            "projection_id": "document_chunk_lexical_projection_v1",
                            "projection_version": "v1",
                            "profile_id": "aws_aurora_pg_opensearch_v1",
                            "lane_family": "lexical",
                            "target_backend": "opensearch",
                            "status": "stale",
                            "last_build_revision": "v1:lexical",
                            "last_build_timestamp": 123.0,
                            "error_summary": None,
                            "metadata": {"invalidated_by": ["document_scope_changed"]},
                        }
                    ],
                    "metadata": {"collection_ids": ["c1"]},
                },
            )
        if request.url.path == "/v1/projection-refresh/run":
            return httpx.Response(
                200,
                json={
                    "profile_id": "aws_aurora_pg_opensearch_v1",
                    "projection_id": "document_chunk_lexical_projection_v1",
                    "executed_actions": [],
                    "skipped_actions": [
                        {
                            "projection_descriptor_id": "document_chunk_lexical_projection_v1",
                            "lane_family": "lexical",
                            "record_schema": "LexicalProjectionRecord",
                            "adapter_backend": "opensearch",
                            "writer_id": "placeholder.projection_writer.lexical.aws_aurora_pg_opensearch_v1",
                            "writer_implemented": False,
                            "implemented": True,
                            "support_state": "supported",
                            "mode": "external_writer_unavailable",
                            "current_status": "absent",
                            "invalidated_by": [],
                            "notes": "Split-stack projection writers are not implemented yet for this profile.",
                        }
                    ],
                    "metadata": {"projection_version": "v1"},
                },
            )
        raise AssertionError(f"unexpected path: {request.url.path}")

    client = QueryLakeClient(base_url="http://testserver", oauth2="tok")
    client._client.close()
    client._client = _mock_client(handler)
    try:
        assert client.profile_diagnostics()["profile"]["id"] == "aws_aurora_pg_opensearch_v1"
        assert client.kernel_profile_diagnostics()["profile"]["id"] == "aws_aurora_pg_opensearch_v1"
        summary = client.profile_diagnostics_summary()
        kernel_summary = client.kernel_profile_diagnostics_summary()
        assert kernel_summary.profile.id == "aws_aurora_pg_opensearch_v1"
        assert kernel_summary.profile.maturity == "split_stack_executable"
        assert summary.configuration is not None
        assert summary.configuration.ready is True
        assert [entry.env_var for entry in summary.configuration.missing_requirements()] == ["QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS"]
        assert summary.configuration.blocking_requirements() == []
        assert summary.execution_target is not None
        assert summary.execution_target.maturity == "limited"
        assert summary.startup_validation is not None
        assert summary.startup_validation.boot_ready is False
        assert summary.startup_validation.route_execution_ready is True
        assert summary.startup_validation.route_runtime_ready is False
        assert summary.startup_validation.inspected_route_ids == ["search_hybrid.document_chunk", "search_file_chunks"]
        assert summary.startup_validation.full_route_coverage_ready is True
        assert summary.startup_validation.full_runtime_coverage_ready is False
        assert summary.startup_validation.non_executable_optional_routes == []
        assert summary.startup_validation.non_runtime_ready_required_routes == ["search_hybrid.document_chunk"]
        assert summary.startup_validation.validation_error_kind == "projection_runtime_blocked"
        assert summary.startup_validation.is_projection_runtime_blocked() is True
        assert summary.startup_validation.is_backend_unreachable() is False
        assert (
            summary.startup_validation.validation_error_hint
            == "Build the missing required projections or switch to the gold profile if exact lexical constraints are required."
        )
        assert summary.startup_validation.validation_error_docs_ref == "docs/database/PROFILE_DIAGNOSTICS.md"
        assert (
            summary.startup_validation.validation_error_command
            == "python scripts/db_compat_profile_bootstrap.py --profile aws_aurora_pg_opensearch_v1"
        )
        assert summary.route_executors[0].implemented is True
        assert summary.route_executors[0].projection_descriptors == ["document_chunk_lexical_projection_v1", "document_chunk_dense_projection_v1"]
        assert summary.route_executors[0].projection_dependency_mode == "required_external_projection"
        assert summary.route_executors[0].projection_ready is False
        assert summary.route_executors[0].runtime_ready() is False
        assert summary.route_executors[0].blocker_kinds() == ["projection_writer_unavailable"]
        assert summary.route_executors[0].is_projection_ready() is False
        assert summary.route_executors[0].requires_external_projection() is True
        assert summary.route_executors[0].has_projection_writer_gap() is True
        assert summary.route_executors[0].writer_gap_projection_ids() == [
            "document_chunk_lexical_projection_v1",
            "document_chunk_dense_projection_v1",
        ]
        assert summary.route_executors[0].build_gap_projection_ids() == []
        assert summary.route_executors[0].missing_required_projections() == [
            "document_chunk_lexical_projection_v1",
            "document_chunk_dense_projection_v1",
        ]
        assert summary.route_executors[0].projection_missing_descriptors == [
            "document_chunk_lexical_projection_v1",
            "document_chunk_dense_projection_v1",
        ]
        assert summary.route_executors[0].projection_readiness["document_chunk_lexical_projection_v1"]["build_status"] == "absent"
        assert summary.route_support_state("search_hybrid.document_chunk") == "degraded"
        assert summary.route_representation_scope_id("search_hybrid.document_chunk") == "document_chunk"
        assert summary.route_representation_scope("search_hybrid.document_chunk")["authority_model"] == "document_segment"
        assert summary.representation_scope("document_chunk").compatibility_projection is True
        assert summary.route_support_manifest_v2_entry("search_hybrid.document_chunk") is not None
        assert summary.route_capability_dependencies("search_hybrid.document_chunk") == [
            "retrieval.lexical.bm25",
            "retrieval.dense.vector",
        ]
        assert summary.route_declared_executable("search_hybrid.document_chunk") is True
        assert summary.route_declared_optional("search_hybrid.document_chunk") is False
        assert summary.route_executors[0].query_ir_v2_template()["route_id"] == "search_hybrid.document_chunk"
        assert summary.route_executors[0].projection_ir_v2()["representation_scope_id"] == "document_chunk"
        assert client.diagnostics_representation_scopes()["document_chunk"]["authority_model"] == "document_segment"
        assert (
            client.diagnostics_route_support_manifest_v2()["search_hybrid.document_chunk"]["representation_scope"][
                "scope_id"
            ]
            == "document_chunk"
        )
        assert client.route_query_ir_v2_template("search_hybrid.document_chunk")["route_id"] == "search_hybrid.document_chunk"
        assert client.route_projection_ir_v2("search_hybrid.document_chunk")["representation_scope_id"] == "document_chunk"
        assert client.route_declared_executable("search_hybrid.document_chunk") is True
        assert client.route_declared_optional("search_hybrid.document_chunk") is False
        assert summary.route_executable("search_hybrid.document_chunk") is True
        assert summary.route_executable("search_hybrid.document_chunk", allow_degraded=False) is False
        assert summary.route_projection_ready("search_hybrid.document_chunk") is False
        assert summary.route_projection_missing_descriptors("search_hybrid.document_chunk") == [
            "document_chunk_lexical_projection_v1",
            "document_chunk_dense_projection_v1",
        ]
        assert summary.route_runtime_ready("search_hybrid.document_chunk") is False
        assert summary.route_runtime_ready("search_hybrid.document_chunk", allow_degraded=False) is False
        assert summary.route_state("search_hybrid.document_chunk") == "blocked_by_projection"
        assert summary.route_is_degraded("search_hybrid.document_chunk") is True
        assert summary.route_blocked_by_projection("search_hybrid.document_chunk") is True
        assert summary.route_blocked_by_backend_connectivity("search_hybrid.document_chunk") is False
        assert summary.route_blocker_kinds("search_hybrid.document_chunk") == ["projection_writer_unavailable"]
        assert summary.route_blocking_projection_ids("search_hybrid.document_chunk") == [
            "document_chunk_lexical_projection_v1",
            "document_chunk_dense_projection_v1",
        ]
        assert summary.route_lexical_support_class("search_hybrid.document_chunk") == "degraded_supported"
        assert summary.route_lexical_capability_states("search_hybrid.document_chunk") == {
            "retrieval.lexical.bm25": "supported",
            "retrieval.lexical.advanced_operators": "degraded",
            "retrieval.lexical.phrase_boost": "degraded",
            "retrieval.lexical.proximity": "degraded",
            "retrieval.lexical.hard_constraints": "unsupported",
        }
        assert summary.route_lexical_degraded_capabilities("search_hybrid.document_chunk") == [
            "retrieval.lexical.advanced_operators",
            "retrieval.lexical.phrase_boost",
            "retrieval.lexical.proximity",
        ]
        assert summary.route_lexical_unsupported_capabilities("search_hybrid.document_chunk") == [
            "retrieval.lexical.hard_constraints",
        ]
        assert summary.route_lane_backends("search_hybrid.document_chunk") == {
            "bm25": "opensearch",
            "dense": "opensearch",
        }
        assert summary.route_adapter_ids("search_hybrid.document_chunk") == {
            "bm25": "opensearch_bm25_v1",
            "dense": "opensearch_dense_knn_v1",
        }
        route_summary = summary.route_summary_payload()
        assert route_summary.inspected_route_count == 2
        assert route_summary.executable_route_count == 2
        assert route_summary.runtime_ready_route_count == 1
        assert route_summary.projection_blocked_route_count == 1
        assert route_summary.runtime_blocked_route_count == 1
        assert route_summary.support_state_counts == {"degraded": 1, "supported": 1}
        assert route_summary.blocker_kind_counts == {"projection_writer_unavailable": 1}
        assert route_summary.runtime_blocked_route_ids == ["search_hybrid.document_chunk"]
        assert summary.runtime_blocker_summary() == {"projection_writer_unavailable": 1}
        assert summary.route_support_state("search_file_chunks") == "supported"
        assert summary.route_executable("search_file_chunks") is True
        assert summary.route_projection_ready("search_file_chunks") is True
        assert summary.route_projection_missing_descriptors("search_file_chunks") == []
        assert summary.route_runtime_ready("search_file_chunks") is True
        assert client.route_lexical_support_class("search_file_chunks") == "degraded_supported"
        assert client.route_lexical_unsupported_capabilities("search_file_chunks") == [
            "retrieval.lexical.hard_constraints",
        ]
        assert [entry.route_id for entry in summary.executable_routes()] == ["search_hybrid.document_chunk", "search_file_chunks"]
        assert [entry.route_id for entry in summary.runtime_ready_routes()] == ["search_file_chunks"]
        assert [entry.route_id for entry in summary.degraded_routes()] == ["search_hybrid.document_chunk"]
        assert [entry.route_id for entry in summary.missing_route_executors()] == []
        assert [entry.route_id for entry in summary.projection_blocked_routes()] == ["search_hybrid.document_chunk"]
        assert [entry.route_id for entry in summary.runtime_blocked_routes()] == ["search_hybrid.document_chunk"]
        assert summary.backend_connectivity_status("projection") == "configured_unprobed"
        projection_connectivity = summary.backend_connectivity_entry("projection")
        assert projection_connectivity is not None
        assert projection_connectivity.backend == "opensearch"
        assert projection_connectivity.is_not_probed() is True
        assert projection_connectivity.blocks_execution() is False
        assert summary.backend_connectivity["projection"]["status"] == "configured_unprobed"
        sparse_lane = summary.lane_diagnostic("sparse_vector")
        assert sparse_lane is not None
        assert sparse_lane.execution_mode == "placeholder"
        assert sparse_lane.blocked_by_capability == "retrieval.sparse.vector"
        assert sparse_lane.placeholder_executor_id == "placeholder.sparse_vector.aws_aurora_pg_opensearch_v1"
        assert sparse_lane.recommended_profile_id == "paradedb_postgres_gold_v1"
        assert sparse_lane.is_placeholder() is True
        graph_lane = summary.lane_diagnostic("graph_traversal")
        assert graph_lane is not None
        assert graph_lane.execution_mode == "placeholder"
        assert graph_lane.blocked_by_capability == "retrieval.graph.traversal"
        assert graph_lane.placeholder_executor_id == "placeholder.graph_traversal.aws_aurora_pg_opensearch_v1"
        assert graph_lane.recommended_profile_id == "paradedb_postgres_gold_v1"
        assert graph_lane.is_placeholder() is True
        assert client.route_support_state("search_hybrid.document_chunk") == "degraded"
        assert client.route_executable("search_hybrid.document_chunk") is True
        assert client.route_executable("search_hybrid.document_chunk", allow_degraded=False) is False
        assert client.route_projection_ready("search_hybrid.document_chunk") is False
        assert client.route_projection_missing_descriptors("search_hybrid.document_chunk") == [
            "document_chunk_lexical_projection_v1",
            "document_chunk_dense_projection_v1",
        ]
        assert client.route_runtime_ready("search_hybrid.document_chunk") is False
        assert client.route_state("search_hybrid.document_chunk") == "blocked_by_projection"
        assert client.route_is_degraded("search_hybrid.document_chunk") is True
        assert client.route_blocked_by_projection("search_hybrid.document_chunk") is True
        assert client.route_blocked_by_backend_connectivity("search_hybrid.document_chunk") is False
        assert client.route_blocker_kinds("search_hybrid.document_chunk") == ["projection_writer_unavailable"]
        assert client.route_blocking_projection_ids("search_hybrid.document_chunk") == [
            "document_chunk_lexical_projection_v1",
            "document_chunk_dense_projection_v1",
        ]
        assert client.route_lane_backends("search_hybrid.document_chunk") == {
            "bm25": "opensearch",
            "dense": "opensearch",
        }
        assert client.route_adapter_ids("search_hybrid.document_chunk") == {
            "bm25": "opensearch_bm25_v1",
            "dense": "opensearch_dense_knn_v1",
        }
        assert client.route_projection_target_backend_names("search_hybrid.document_chunk") == {
            "document_chunk_lexical_projection_v1": "opensearch",
            "document_chunk_dense_projection_v1": "opensearch",
        }
        assert client.route_required_projection_descriptor_ids("search_hybrid.document_chunk") == [
            "document_chunk_lexical_projection_v1",
            "document_chunk_dense_projection_v1",
        ]
        assert client.route_projection_targets("search_hybrid.document_chunk")[0]["authority_model"] == (
            "document_chunk_compatibility"
        )
        assert client.route_summary() == {
            "inspected_route_count": 2,
            "executable_route_count": 2,
            "runtime_ready_route_count": 1,
            "projection_blocked_route_count": 1,
            "runtime_blocked_route_count": 1,
            "compatibility_projection_route_count": 2,
            "canonical_projection_route_count": 0,
            "support_state_counts": {"degraded": 1, "supported": 1},
            "blocker_kind_counts": {"projection_writer_unavailable": 1},
            "executable_route_ids": ["search_hybrid.document_chunk", "search_file_chunks"],
            "runtime_ready_route_ids": ["search_file_chunks"],
            "projection_blocked_route_ids": ["search_hybrid.document_chunk"],
            "runtime_blocked_route_ids": ["search_hybrid.document_chunk"],
            "compatibility_projection_route_ids": ["search_hybrid.document_chunk", "search_file_chunks"],
            "canonical_projection_route_ids": [],
        }
        assert client.runtime_blocker_summary() == {"projection_writer_unavailable": 1}
        assert client.projection_blocked_routes() == ["search_hybrid.document_chunk"]
        assert client.runtime_blocked_routes() == ["search_hybrid.document_chunk"]
        assert client.backend_connectivity_status("projection") == "configured_unprobed"
        client_projection_connectivity = client.backend_connectivity_entry("projection")
        assert client_projection_connectivity is not None
        assert client_projection_connectivity.backend == "opensearch"
        assert client_projection_connectivity.endpoint == "https://search.example.com"
        assert client.backend_connectivity_entries()["projection"].status == "configured_unprobed"
        assert client.projection_diagnostics()["profile_id"] == "aws_aurora_pg_opensearch_v1"
        assert client.kernel_projection_diagnostics()["metadata"]["projection_count"] == 1
        projection_summary = client.projection_diagnostics_summary()
        assert projection_summary.profile_id == "aws_aurora_pg_opensearch_v1"
        projection_item = projection_summary.projection("document_chunk_lexical_projection_v1")
        assert projection_item is not None
        assert projection_item.build_status == "absent"
        assert projection_item.materialization_target["target_backend_name"] == "opensearch"
        assert projection_item.materialization_target["authority_model"] == "document_chunk_compatibility"
        assert projection_item.is_ready() is False
        assert projection_item.is_available() is False
        assert projection_item.needs_build() is False
        assert projection_item.build_state is None
        assert projection_summary.projection_ids_needing_build() == []
        assert [item.projection_id for item in projection_summary.blocked_projections()] == []
        assert [item.projection_id for item in projection_summary.actionable_projections()] == []
        assert [item.projection_id for item in projection_summary.projections_for_backend("opensearch")] == [
            "document_chunk_lexical_projection_v1"
        ]
        assert [item.projection_id for item in projection_summary.projections_for_lane("lexical")] == [
            "document_chunk_lexical_projection_v1"
        ]
        assert client.projection_ids_needing_build() == []
        explain_summary = client.projection_plan_explain_summary(
            {"projection_id": "document_chunk_lexical_projection_v1", "collection_ids": ["c1"]}
        )
        assert explain_summary.projection_id == "document_chunk_lexical_projection_v1"
        assert explain_summary.actions[0]["mode"] == "rebuild"
        assert explain_summary.status_snapshot[0].status == "stale"
        refresh_summary = client.projection_refresh_run_summary(
            {"projection_id": "document_chunk_lexical_projection_v1", "collection_ids": ["c1"]}
        )
        assert refresh_summary.profile_id == "aws_aurora_pg_opensearch_v1"
        assert refresh_summary.executed_projection_ids() == []
        assert refresh_summary.skipped_modes() == ["external_writer_unavailable"]
        assert refresh_summary.has_writer_gap() is True
    finally:
        client.close()


def test_profile_bringup_manifest_helpers():
    from querylake_sdk.models import parse_profile_bringup_summary

    payload = {
        "profile": {
            "id": "aws_aurora_pg_opensearch_v1",
            "label": "Aurora PostgreSQL + OpenSearch",
            "implemented": True,
            "recommended": False,
            "maturity": "split_stack_executable",
            "backend_stack": {},
        },
        "representation_scopes": {
            "document_chunk": {
                "scope_id": "document_chunk",
                "authority_model": "document_segment",
                "compatibility_projection": True,
                "metadata": {},
            }
        },
        "route_support_v2": [
            {
                "route_id": "search_hybrid.document_chunk",
                "support_state": "supported",
                "implemented": True,
                "declared_executable": True,
                "declared_optional": False,
                "representation_scope": {
                    "scope_id": "document_chunk",
                    "authority_model": "document_segment",
                    "compatibility_projection": True,
                    "metadata": {},
                },
                "capability_dependencies": [
                    "retrieval.lexical.bm25",
                    "retrieval.dense.vector",
                ],
            }
        ],
        "summary": {
            "boot_ready": True,
            "configuration_ready": True,
            "route_execution_ready": True,
            "route_runtime_ready": True,
            "backend_connectivity_ready": True,
        },
        "route_recovery": [
            {
                "route_id": "search_hybrid.document_chunk",
                "implemented": True,
                "support_state": "supported",
                "planning_v2": {
                    "query_ir_v2_template": {
                        "route_id": "search_hybrid.document_chunk",
                        "representation_scope_id": "document_chunk",
                    },
                    "projection_ir_v2": {
                        "route_id": "search_hybrid.document_chunk",
                        "representation_scope_id": "document_chunk",
                    },
                },
                "representation_scope_id": "document_chunk",
                "representation_scope": {
                    "scope_id": "document_chunk",
                    "authority_model": "document_segment",
                    "compatibility_projection": True,
                    "metadata": {},
                },
                "capability_dependencies": [
                    "retrieval.lexical.bm25",
                    "retrieval.dense.vector",
                ],
                "runtime_ready": True,
                "projection_ready": True,
            }
        ],
    }

    summary = parse_profile_bringup_summary(payload)
    assert summary.representation_scope("document_chunk").authority_model == "document_segment"
    assert summary.route_support_manifest_v2_entry("search_hybrid.document_chunk") is not None
    assert summary.route_capability_dependencies("search_hybrid.document_chunk") == [
        "retrieval.lexical.bm25",
        "retrieval.dense.vector",
    ]
    recovery = summary.route_recovery_entry("search_hybrid.document_chunk")
    assert recovery is not None
    assert recovery.representation_scope_id == "document_chunk"
    assert recovery.representation_scope_authority_model() == "document_segment"
    assert recovery.query_ir_v2_template()["route_id"] == "search_hybrid.document_chunk"
    assert recovery.projection_ir_v2()["representation_scope_id"] == "document_chunk"


def test_profile_bringup_client_manifest_helpers():
    payload = {
        "profile": {
            "id": "aws_aurora_pg_opensearch_v1",
            "label": "Aurora PostgreSQL + OpenSearch",
            "implemented": True,
            "recommended": False,
            "maturity": "split_stack_executable",
            "backend_stack": {},
        },
        "representation_scopes": {
            "document_chunk": {
                "scope_id": "document_chunk",
                "authority_model": "document_segment",
                "compatibility_projection": True,
                "metadata": {},
            }
        },
        "route_support_v2": [
            {
                "route_id": "search_hybrid.document_chunk",
                "support_state": "supported",
                "implemented": True,
                "declared_executable": True,
                "declared_optional": False,
                "representation_scope": {
                    "scope_id": "document_chunk",
                    "authority_model": "document_segment",
                    "compatibility_projection": True,
                    "metadata": {},
                },
                "capability_dependencies": [
                    "retrieval.lexical.bm25",
                    "retrieval.dense.vector",
                ],
            }
        ],
        "summary": {
            "boot_ready": True,
            "configuration_ready": True,
            "route_execution_ready": True,
            "route_runtime_ready": True,
            "backend_connectivity_ready": True,
        },
        "local_profile": {
            "support_matrix": [
                {
                    "route_id": "search_hybrid.document_chunk",
                    "representation_scope_id": "document_chunk",
                    "lexical_support_class": "degraded_supported",
                    "declared_executable": True,
                }
            ],
            "route_runtime_contracts": [
                {
                    "route_id": "search_hybrid.document_chunk",
                    "representation_scope_id": "document_chunk",
                    "runtime_ready": True,
                    "required_projection_ids": [
                        "document_chunk_lexical_projection_v1",
                        "document_chunk_dense_projection_v1",
                    ],
                    "capability_dependencies": [
                        "retrieval.lexical.bm25",
                        "retrieval.dense.vector",
                    ],
                    "representation_scope": {
                        "scope_id": "document_chunk",
                        "authority_model": "document_segment",
                        "compatibility_projection": True,
                        "metadata": {},
                    },
                    "lexical_support_class": "degraded_supported",
                    "dense_sidecar_required": True,
                    "dense_sidecar_ready": True,
                    "dense_sidecar_cache_warmed": True,
                    "dense_sidecar_indexed_record_count": 2,
                    "dense_sidecar_ready_state_source": "process_local_cache",
                    "dense_sidecar_stats_source": "process_local_cache",
                    "dense_sidecar_cache_lifecycle_state": "cache_warmed_process_local",
                    "dense_sidecar_rebuildable_from_projection_records": True,
                    "dense_sidecar_requires_process_warmup": False,
                    "dense_sidecar_persisted_projection_state_available": False,
                    "dense_sidecar_contract": {
                        "adapter_id": "local_dense_sidecar_v1",
                        "execution_mode": "projection_backed_process_local",
                        "storage_mode": "metadata_backed_projection_records",
                        "persistence_scope": "projection_build_state_plus_process_local_cache",
                        "cache_model": "process_local_index_registry",
                        "warmup_mode": "projection_materialization_scan",
                        "query_mode": "cosine_similarity_full_scan",
                        "readiness_contract": "projection_ready_and_executable",
                    },
                }
            ],
            "projection_plan_v2_registry": [
                {
                    "projection_id": "document_chunk_lexical_projection_v1",
                    "representation_scope_id": "document_chunk",
                    "target_backend": "sqlite_fts5",
                }
            ],
            "dense_sidecar": {
                "ready": True,
                "cache_warmed": True,
                "record_count": 2,
                "projection_id": "document_chunk_dense_projection_v1",
                "adapter_id": "local_dense_sidecar_v1",
                "execution_mode": "projection_backed_process_local",
                "storage_mode": "metadata_backed_projection_records",
                "ready_state_source": "process_local_cache",
                "stats_source": "process_local_cache",
                "cache_lifecycle_state": "cache_warmed_process_local",
                "rebuildable_from_projection_records": True,
                "requires_process_warmup": False,
                "persisted_projection_state_available": False,
                "contract": {
                    "adapter_id": "local_dense_sidecar_v1",
                    "execution_mode": "projection_backed_process_local",
                    "storage_mode": "metadata_backed_projection_records",
                    "persistence_scope": "projection_build_state_plus_process_local_cache",
                    "cache_model": "process_local_index_registry",
                    "warmup_mode": "projection_materialization_scan",
                    "query_mode": "cosine_similarity_full_scan",
                    "readiness_contract": "projection_ready_and_executable",
                },
            },
            "promotion_status": {
                "declared_scope_frozen": True,
                "route_execution_real": True,
                "declared_executable_route_ids": ["search_hybrid.document_chunk"],
                "declared_executable_runtime_ready_ids": ["search_hybrid.document_chunk"],
                "declared_executable_runtime_blocked_ids": [],
                "required_projection_ids": ["document_chunk_lexical_projection_v1"],
                "representation_scope_ids": ["document_chunk"],
            },
            "scope_expansion_status": {
                "current_supported_slice_frozen": True,
                "dense_sidecar_contract_version": "v1",
                "dense_sidecar_promotion_contract_ready": True,
                "dense_sidecar_lifecycle_state": "ready_projection_backed_cache_cold",
                "dense_sidecar_cache_lifecycle_state": "cache_cold_rebuildable",
                "dense_sidecar_rebuildable_from_projection_records": True,
                "dense_sidecar_requires_process_warmup": True,
                "dense_sidecar_persisted_projection_state_available": False,
                "required_for_scope_expansion": [
                    "local_dense_sidecar_contract_hardened",
                    "local_scope_sync_and_completion_gates"
                ],
                "satisfied_now": [
                    "declared_executable_routes_runtime_ready",
                    "projection_plan_v2_complete"
                ],
                "pending_for_wider_scope": [
                    "broaden_route_slice_beyond_current_supported_manifest"
                ],
                "future_scope_candidates": [
                    "broader_local_file_semantics",
                    "additional_local_hybrid_composition_modes"
                ],
                "docs_ref": "docs/database/LOCAL_PROFILE_SCOPE_EXPANSION_CRITERIA.md",
            },
            "scope_expansion_contract": {
                "profile_id": "sqlite_fts5_dense_sidecar_local_v1",
                "maturity": "embedded_supported",
                "current_supported_slice_frozen": True,
                "declared_executable_route_ids": ["search_hybrid.document_chunk"],
                "lexical_contract": {
                    "plain_lexical": "degraded_supported",
                    "phrase_semantics": "degraded_supported",
                    "operator_heavy_semantics": "degraded_supported",
                    "hard_constraints": "unsupported",
                    "sparse_retrieval": "unsupported",
                    "graph_traversal": "unsupported",
                },
                "satisfied_now": [
                    "declared_executable_routes_runtime_ready",
                    "projection_plan_v2_complete"
                ],
                "required_before_widening": [
                    "define_next_embedded_route_slice"
                ],
                "future_scope_candidates": [
                    "broader_local_file_semantics",
                    "additional_local_hybrid_composition_modes"
                ],
                "dense_sidecar_contract_version": "v1",
                "docs_ref": "docs/database/LOCAL_PROFILE_SCOPE_EXPANSION_CRITERIA.md",
                "promotion_docs_ref": "docs/database/LOCAL_PROFILE_PROMOTION_BAR.md",
                "dense_sidecar_docs_ref": "docs/database/LOCAL_DENSE_SIDECAR_CONTRACT.md",
            },
            "scope_expansion_docs_ref": "docs/database/LOCAL_PROFILE_SCOPE_EXPANSION_CRITERIA.md",
            "maturity": "embedded_supported",
        },
        "route_recovery": [
            {
                "route_id": "search_hybrid.document_chunk",
                "implemented": True,
                "support_state": "supported",
                "planning_v2": {
                    "query_ir_v2_template": {
                        "route_id": "search_hybrid.document_chunk",
                        "representation_scope_id": "document_chunk",
                    },
                    "projection_ir_v2": {
                        "route_id": "search_hybrid.document_chunk",
                        "representation_scope_id": "document_chunk",
                    },
                },
                "representation_scope_id": "document_chunk",
                "representation_scope": {
                    "scope_id": "document_chunk",
                    "authority_model": "document_segment",
                    "compatibility_projection": True,
                    "metadata": {},
                },
                "capability_dependencies": [
                    "retrieval.lexical.bm25",
                    "retrieval.dense.vector",
                ],
                "runtime_ready": True,
                "projection_ready": True,
            }
        ],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/profile-bringup":
            return httpx.Response(200, json=payload)
        if request.url.path == "/v1/profile-diagnostics":
            return httpx.Response(200, json=payload)
        raise AssertionError(f"unexpected path: {request.url.path}")

    client = QueryLakeClient(base_url="http://testserver", oauth2="tok")
    client._client.close()
    client._client = _mock_client(handler)
    try:
        assert client.bringup_representation_scopes()["document_chunk"]["authority_model"] == "document_segment"
        assert (
            client.bringup_route_support_manifest_v2()["search_hybrid.document_chunk"]["representation_scope"][
                "scope_id"
            ]
            == "document_chunk"
        )
        summary = client.profile_bringup_summary()
        assert summary.representation_scope("document_chunk").compatibility_projection is True
        assert summary.route_support_manifest_v2_entry("search_hybrid.document_chunk") is not None
        assert summary.route_capability_dependencies("search_hybrid.document_chunk") == [
            "retrieval.lexical.bm25",
            "retrieval.dense.vector",
        ]
        assert summary.local_profile_maturity() == "embedded_supported"
        assert summary.local_support_matrix()[0]["route_id"] == "search_hybrid.document_chunk"
        assert summary.local_promotion_status()["declared_scope_frozen"] is True
        assert summary.local_scope_expansion_status()["current_supported_slice_frozen"] is True
        assert summary.local_route_representation_scope_id("search_hybrid.document_chunk") == "document_chunk"
        assert summary.local_route_declared_executable("search_hybrid.document_chunk") is True
        assert summary.route_declared_executable("search_hybrid.document_chunk") is True
        assert summary.route_declared_optional("search_hybrid.document_chunk") is False
        assert client.bringup_route_query_ir_v2_template("search_hybrid.document_chunk")["route_id"] == "search_hybrid.document_chunk"
        assert client.bringup_route_projection_ir_v2("search_hybrid.document_chunk")["representation_scope_id"] == "document_chunk"
        assert client.bringup_route_recovery_entry("search_hybrid.document_chunk")["query_ir_v2"]["route_id"] == "search_hybrid.document_chunk"
        assert client.bringup_route_recovery_entry("search_hybrid.document_chunk")["projection_ir_v2"]["representation_scope_id"] == "document_chunk"
        assert client.local_profile_maturity() == "embedded_supported"
        assert client.local_support_matrix()[0]["representation_scope_id"] == "document_chunk"
        assert client.local_promotion_status()["route_execution_real"] is True
        assert client.local_scope_expansion_status()["docs_ref"] == "docs/database/LOCAL_PROFILE_SCOPE_EXPANSION_CRITERIA.md"
        assert client.local_route_representation_scope_id("search_hybrid.document_chunk") == "document_chunk"
        assert client.local_route_declared_executable("search_hybrid.document_chunk") is True
        assert client.local_declared_executable_route_ids() == ["search_hybrid.document_chunk"]
        assert client.local_declared_runtime_ready_route_ids() == ["search_hybrid.document_chunk"]
        assert client.local_declared_runtime_blocked_route_ids() == []
        assert client.local_required_projection_ids() == ["document_chunk_lexical_projection_v1"]
        assert client.local_representation_scope_ids() == ["document_chunk"]
        assert summary.local_current_supported_slice_frozen() is True
        assert summary.local_scope_expansion_pending_for_wider_scope() == [
            "broaden_route_slice_beyond_current_supported_manifest"
        ]
        assert summary.local_scope_expansion_required_now() == [
            "local_dense_sidecar_contract_hardened",
            "local_scope_sync_and_completion_gates",
        ]
        assert summary.local_scope_expansion_satisfied_now() == [
            "declared_executable_routes_runtime_ready",
            "projection_plan_v2_complete",
        ]
        assert summary.local_scope_expansion_future_scope_candidates() == [
            "broader_local_file_semantics",
            "additional_local_hybrid_composition_modes",
        ]
        assert summary.local_scope_expansion_docs_ref() == "docs/database/LOCAL_PROFILE_SCOPE_EXPANSION_CRITERIA.md"
        assert summary.local_scope_expansion_contract()["profile_id"] == "sqlite_fts5_dense_sidecar_local_v1"
        assert summary.local_scope_expansion_contract_docs_ref() == "docs/database/LOCAL_PROFILE_SCOPE_EXPANSION_CRITERIA.md"
        assert summary.local_scope_expansion_contract_version() == "v1"
        assert summary.local_scope_expansion_lifecycle_contract_version() == "v1"
        assert summary.local_scope_expansion_lifecycle_state() == "ready_projection_backed_cache_cold"
        assert summary.local_scope_expansion_cache_lifecycle_state() == "cache_cold_rebuildable"
        assert summary.local_scope_expansion_dense_sidecar_promotion_contract_ready() is True
        assert summary.local_scope_expansion_rebuildable_from_projection_records() is True
        assert summary.local_scope_expansion_requires_process_warmup() is True
        assert summary.local_scope_expansion_persisted_projection_state_available() is False
        assert summary.local_scope_expansion_required_before_widening() == [
            "define_next_embedded_route_slice"
        ]
        assert summary.local_dense_sidecar_cache_lifecycle_state() == "cache_warmed_process_local"
        assert summary.local_dense_sidecar_rebuildable_from_projection_records() is True
        assert summary.local_dense_sidecar_requires_process_warmup() is False
        assert summary.local_dense_sidecar_persisted_projection_state_available() is False
        assert summary.local_route_dense_sidecar_cache_lifecycle_state("search_hybrid.document_chunk") == "cache_warmed_process_local"
        assert summary.local_route_dense_sidecar_rebuildable_from_projection_records("search_hybrid.document_chunk") is True
        assert summary.local_route_dense_sidecar_requires_process_warmup("search_hybrid.document_chunk") is False
        assert summary.local_route_dense_sidecar_persisted_projection_state_available("search_hybrid.document_chunk") is False
        assert client.local_current_supported_slice_frozen() is True
        assert client.local_scope_expansion_pending_for_wider_scope() == [
            "broaden_route_slice_beyond_current_supported_manifest"
        ]
        assert client.local_scope_expansion_required_now() == [
            "local_dense_sidecar_contract_hardened",
            "local_scope_sync_and_completion_gates",
        ]
        assert client.local_scope_expansion_satisfied_now() == [
            "declared_executable_routes_runtime_ready",
            "projection_plan_v2_complete",
        ]
        assert client.local_scope_expansion_future_scope_candidates() == [
            "broader_local_file_semantics",
            "additional_local_hybrid_composition_modes",
        ]
        assert client.local_scope_expansion_docs_ref() == "docs/database/LOCAL_PROFILE_SCOPE_EXPANSION_CRITERIA.md"
        assert client.local_scope_expansion_contract()["profile_id"] == "sqlite_fts5_dense_sidecar_local_v1"
        assert client.local_dense_sidecar_cache_lifecycle_state() == "cache_warmed_process_local"
        assert client.local_dense_sidecar_rebuildable_from_projection_records() is True
        assert client.local_dense_sidecar_requires_process_warmup() is False
        assert client.local_dense_sidecar_persisted_projection_state_available() is False
        assert client.local_route_dense_sidecar_cache_lifecycle_state("search_hybrid.document_chunk") == "cache_warmed_process_local"
        assert client.local_route_dense_sidecar_rebuildable_from_projection_records("search_hybrid.document_chunk") is True
        assert client.local_route_dense_sidecar_requires_process_warmup("search_hybrid.document_chunk") is False
        assert client.local_route_dense_sidecar_persisted_projection_state_available("search_hybrid.document_chunk") is False
        assert client.local_scope_expansion_cache_lifecycle_state() == "cache_cold_rebuildable"
        assert client.local_scope_expansion_rebuildable_from_projection_records() is True
        assert client.local_scope_expansion_requires_process_warmup() is True
        assert client.local_scope_expansion_persisted_projection_state_available() is False
        assert client.local_scope_expansion_contract_docs_ref() == "docs/database/LOCAL_PROFILE_SCOPE_EXPANSION_CRITERIA.md"
        assert client.local_scope_expansion_contract_version() == "v1"
        assert client.local_scope_expansion_lifecycle_contract_version() == "v1"
        assert client.local_scope_expansion_lifecycle_state() == "ready_projection_backed_cache_cold"
        assert client.local_scope_expansion_dense_sidecar_promotion_contract_ready() is True
        assert client.local_scope_expansion_required_before_widening() == [
            "define_next_embedded_route_slice"
        ]
        assert summary.local_dense_sidecar_ready() is True
        assert summary.local_dense_sidecar_ready_state_source() == "process_local_cache"
        assert summary.local_dense_sidecar_stats_source() == "process_local_cache"
        assert summary.local_dense_sidecar_contract_version() == "v1"
        assert summary.local_dense_sidecar_lifecycle_contract_version() == "v1"
        assert summary.local_dense_sidecar_contract()["query_mode"] == "cosine_similarity_full_scan"
        assert summary.local_projection_plan_v2_registry()[0]["projection_id"] == "document_chunk_lexical_projection_v1"
        assert summary.local_projection_plan_v2("document_chunk_lexical_projection_v1")["representation_scope_id"] == "document_chunk"
        assert client.local_projection_plan_v2_registry()[0]["projection_id"] == "document_chunk_lexical_projection_v1"
        assert client.local_projection_plan_v2("document_chunk_lexical_projection_v1")["target_backend"] == "sqlite_fts5"
        assert summary.local_route_requires_dense_sidecar("search_hybrid.document_chunk") is True
        assert summary.local_route_capability_dependencies("search_hybrid.document_chunk") == [
            "retrieval.lexical.bm25",
            "retrieval.dense.vector",
        ]
        assert summary.local_route_representation_scope("search_hybrid.document_chunk")["scope_id"] == "document_chunk"
        assert summary.local_route_lexical_support_class("search_hybrid.document_chunk") == "degraded_supported"
        assert summary.local_route_dense_sidecar_ready("search_hybrid.document_chunk") is True
        assert summary.local_route_dense_sidecar_cache_warmed("search_hybrid.document_chunk") is True
        assert summary.local_route_dense_sidecar_indexed_record_count("search_hybrid.document_chunk") == 2
        assert summary.local_route_dense_sidecar_ready_state_source("search_hybrid.document_chunk") == "process_local_cache"
        assert summary.local_route_dense_sidecar_stats_source("search_hybrid.document_chunk") == "process_local_cache"
        assert summary.local_route_dense_sidecar_contract("search_hybrid.document_chunk")["persistence_scope"] == "projection_build_state_plus_process_local_cache"
        assert summary.local_route_required_projection_ids("search_hybrid.document_chunk") == [
            "document_chunk_lexical_projection_v1",
            "document_chunk_dense_projection_v1",
        ]
        assert client.local_route_capability_dependencies("search_hybrid.document_chunk") == [
            "retrieval.lexical.bm25",
            "retrieval.dense.vector",
        ]
        assert client.local_route_representation_scope("search_hybrid.document_chunk")["scope_id"] == "document_chunk"
        assert client.local_route_lexical_support_class("search_hybrid.document_chunk") == "degraded_supported"
        assert client.local_route_dense_sidecar_ready("search_hybrid.document_chunk") is True
        assert client.local_route_dense_sidecar_cache_warmed("search_hybrid.document_chunk") is True
        assert client.local_route_dense_sidecar_indexed_record_count("search_hybrid.document_chunk") == 2
        assert client.local_dense_sidecar_contract()["cache_model"] == "process_local_index_registry"
        assert client.local_dense_sidecar_contract_version() == "v1"
        assert client.local_dense_sidecar_lifecycle_contract_version() == "v1"
        assert client.local_dense_sidecar_ready_state_source() == "process_local_cache"
        assert client.local_dense_sidecar_stats_source() == "process_local_cache"
        assert client.local_route_dense_sidecar_ready_state_source("search_hybrid.document_chunk") == "process_local_cache"
        assert client.local_route_dense_sidecar_stats_source("search_hybrid.document_chunk") == "process_local_cache"
        assert client.profile_bringup_summary().local_route_dense_sidecar_contract("search_hybrid.document_chunk")["adapter_id"] == "local_dense_sidecar_v1"
    finally:
        client.close()


def test_profile_bringup_helpers():
    payload = {
        "profile": {
            "id": "aws_aurora_pg_opensearch_v1",
            "label": "Aurora PostgreSQL + OpenSearch",
            "implemented": True,
            "recommended": False,
            "maturity": "split_stack_executable",
            "backend_stack": {
                "authority": "aurora_postgresql",
                "lexical": "opensearch",
                "dense": "opensearch",
                "sparse": "opensearch",
                "graph": "aurora_postgresql_segment_relations",
            },
        },
        "summary": {
            "boot_ready": False,
            "configuration_ready": True,
            "route_execution_ready": True,
            "route_runtime_ready": False,
            "declared_executable_routes_runtime_ready": False,
            "backend_connectivity_ready": True,
            "required_projection_count": 3,
            "ready_projection_count": 1,
            "projection_ids_needing_build_count": 2,
            "bootstrapable_required_projection_count": 2,
            "nonbootstrapable_required_projection_count": 0,
            "recommended_projection_count": 2,
            "recommended_ready_projection_count": 0,
            "recommended_projection_ids_needing_build_count": 2,
            "bootstrapable_recommended_projection_count": 2,
            "nonbootstrapable_recommended_projection_count": 0,
            "projection_building_count": 0,
            "projection_failed_count": 0,
            "projection_stale_count": 0,
            "projection_absent_count": 2,
            "required_projection_status_counts": {"ready": 1, "absent": 2},
            "runtime_ready_route_count": 1,
            "runtime_blocked_route_count": 1,
            "declared_route_count": 1,
            "declared_executable_route_count": 1,
            "declared_optional_route_count": 0,
            "declared_executable_runtime_ready_count": 0,
            "declared_executable_runtime_blocked_count": 1,
            "backend_unreachable_plane_count": 0,
            "lexical_degraded_route_count": 1,
            "lexical_gold_recommended_route_count": 1,
            "route_lexical_support_class_counts": {"degraded_supported": 1},
            "lexical_capability_blocker_counts": {"retrieval.lexical.hard_constraints": 1},
            "compatibility_projection_route_count": 1,
            "canonical_projection_route_count": 0,
            "compatibility_projection_target_count": 2,
            "canonical_projection_target_count": 0,
            "next_action_count": 4,
            "route_recovery_count": 1,
        },
        "required_projection_ids": [
            "document_chunk_lexical_projection_v1",
            "document_chunk_dense_projection_v1",
            "file_chunk_lexical_projection_v1",
        ],
        "ready_projection_ids": ["file_chunk_lexical_projection_v1"],
        "projection_ids_needing_build": [
            "document_chunk_lexical_projection_v1",
            "document_chunk_dense_projection_v1",
        ],
        "bootstrapable_required_projection_ids": [
            "document_chunk_lexical_projection_v1",
            "document_chunk_dense_projection_v1",
        ],
        "nonbootstrapable_required_projection_ids": [],
        "recommended_projection_ids": [
            "segment_lexical_projection_v1",
            "segment_dense_projection_v1",
        ],
        "recommended_ready_projection_ids": [],
        "recommended_projection_ids_needing_build": [
            "segment_lexical_projection_v1",
            "segment_dense_projection_v1",
        ],
        "bootstrapable_recommended_projection_ids": [
            "segment_lexical_projection_v1",
            "segment_dense_projection_v1",
        ],
        "nonbootstrapable_recommended_projection_ids": [],
        "projection_building_ids": [],
        "projection_failed_ids": [],
        "projection_stale_ids": [],
        "projection_absent_ids": [
            "document_chunk_lexical_projection_v1",
            "document_chunk_dense_projection_v1",
        ],
        "route_runtime_ready_ids": ["search_file_chunks"],
        "route_runtime_blocked_ids": ["search_hybrid.document_chunk"],
        "declared_route_support": {"search_hybrid.document_chunk": "degraded"},
        "declared_executable_route_ids": ["search_hybrid.document_chunk"],
        "declared_optional_route_ids": [],
        "declared_executable_runtime_ready_ids": [],
        "declared_executable_runtime_blocked_ids": ["search_hybrid.document_chunk"],
        "lexical_degraded_route_ids": ["search_hybrid.document_chunk"],
        "lexical_gold_recommended_route_ids": ["search_hybrid.document_chunk"],
        "compatibility_projection_route_ids": ["search_hybrid.document_chunk"],
        "canonical_projection_route_ids": [],
        "compatibility_projection_target_ids": [
            "document_chunk_dense_projection_v1",
            "document_chunk_lexical_projection_v1",
        ],
        "canonical_projection_target_ids": [],
        "backend_unreachable_planes": [],
        "route_recovery": [
            {
                "route_id": "search_hybrid.document_chunk",
                "implemented": True,
                "support_state": "degraded",
                "runtime_ready": False,
                "projection_ready": False,
                "blocker_kinds": ["projection_not_ready"],
                "bootstrapable_blocking_projection_ids": [
                    "document_chunk_lexical_projection_v1",
                    "document_chunk_dense_projection_v1",
                ],
                "nonbootstrapable_blocking_projection_ids": [],
                "bootstrap_command": "python scripts/db_compat_profile_bootstrap.py --profile aws_aurora_pg_opensearch_v1 --projection-id document_chunk_lexical_projection_v1 --projection-id document_chunk_dense_projection_v1",
                "lexical_support_class": "degraded_supported",
                "gold_recommended_for_exact_constraints": True,
                "exact_constraint_degraded_capabilities": [
                    "retrieval.lexical.advanced_operators",
                    "retrieval.lexical.phrase_boost",
                    "retrieval.lexical.proximity",
                ],
                "exact_constraint_unsupported_capabilities": [
                    "retrieval.lexical.hard_constraints",
                ],
            }
        ],
        "backend_targets": [
            {
                "plane": "projection",
                "backend": "opensearch",
                "status": "configured_unprobed",
                "checked": False,
                "checked_at": None,
                "required": True,
                "endpoint": "https://search.example.com",
                "detail": "Projection backend is configured.",
                "target": {
                    "scheme": "https",
                    "host": "search.example.com",
                    "index_namespace": "ql",
                },
            }
        ],
        "next_actions": [
            {
                "kind": "bootstrap_projections",
                "priority": "high",
                "summary": "Build required projections.",
                "command": "python scripts/db_compat_profile_bootstrap.py --profile aws_aurora_pg_opensearch_v1",
                "projection_ids": [
                    "document_chunk_lexical_projection_v1",
                    "document_chunk_dense_projection_v1",
                ],
            },
            {
                "kind": "route_runtime_blocker",
                "priority": "medium",
                "summary": "Resolve runtime blockers for search_hybrid.document_chunk.",
                "route_id": "search_hybrid.document_chunk",
                "blocker_kinds": ["projection_not_ready"],
            },
            {
                "kind": "bootstrap_recommended_projections",
                "priority": "low",
                "summary": "Bootstrap recommended canonical projections after the required split-stack route surface is runtime-ready.",
                "projection_ids": [
                    "segment_lexical_projection_v1",
                    "segment_dense_projection_v1",
                ],
                "command": "python scripts/db_compat_profile_bootstrap.py --profile aws_aurora_pg_opensearch_v1 --projection-id segment_lexical_projection_v1 --projection-id segment_dense_projection_v1",
            },
            {
                "kind": "prefer_gold_profile_for_exact_lexical_constraints",
                "priority": "medium",
                "summary": "Use the gold ParadeDB profile when exact lexical constraints or full lexical operator semantics are required.",
                "route_ids": ["search_hybrid.document_chunk"],
                "capability_ids": [
                    "retrieval.lexical.advanced_operators",
                    "retrieval.lexical.phrase_boost",
                    "retrieval.lexical.proximity",
                    "retrieval.lexical.hard_constraints",
                ],
            },
        ],
        "profile_diagnostics": {
            "profile": {
                "id": "aws_aurora_pg_opensearch_v1",
                "label": "Aurora PostgreSQL + OpenSearch",
                "implemented": True,
                "recommended": False,
                "maturity": "split_stack_executable",
                "backend_stack": {
                    "authority": "aurora_postgresql",
                    "lexical": "opensearch",
                    "dense": "opensearch",
                    "sparse": "opensearch",
                    "graph": "aurora_postgresql_segment_relations",
                },
            },
            "capabilities": [],
            "route_executors": [],
            "backend_connectivity": {
                "projection": {
                    "backend": "opensearch",
                    "status": "configured_unprobed",
                    "checked": False,
                    "checked_at": None,
                    "endpoint": "https://search.example.com",
                }
            },
        },
        "projection_diagnostics": {
            "profile_id": "aws_aurora_pg_opensearch_v1",
            "projection_items": [
                {
                    "projection_id": "document_chunk_lexical_projection_v1",
                    "projection_version": "v1",
                    "lane_family": "lexical",
                    "authority_model": "document_chunk_compatibility",
                    "source_scope": "document_chunk",
                    "record_schema": "LexicalProjectionRecord",
                    "target_backend_family": "lexical_index",
                    "backend_name": "opensearch",
                    "support_state": "supported",
                    "executable": True,
                    "build_status": "absent",
                    "action_mode": "rebuild",
                    "invalidated_by": [],
                    "materialization_target": {
                        "projection_id": "document_chunk_lexical_projection_v1",
                        "projection_version": "v1",
                        "lane_family": "lexical",
                        "authority_model": "document_chunk_compatibility",
                        "source_scope": "document_chunk",
                        "record_schema": "LexicalProjectionRecord",
                        "target_backend_family": "lexical_index",
                        "target_backend_name": "opensearch",
                        "authority_reference": {
                            "authority_model": "document_chunk_compatibility",
                            "document_ids": [],
                            "segment_ids": [],
                            "collection_ids": [],
                            "metadata": {
                                "profile_id": "aws_aurora_pg_opensearch_v1",
                            },
                        },
                        "metadata": {
                            "profile_id": "aws_aurora_pg_opensearch_v1",
                        },
                    },
                    "build_state": {},
                }
            ],
            "metadata": {"projection_count": 3},
        },
        "metadata": {"projection_count": 3},
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/profile-bringup":
            return httpx.Response(200, json=payload)
        if request.url.path == "/v2/kernel/profile-bringup":
            return httpx.Response(200, json=payload)
        raise AssertionError(f"unexpected path: {request.url.path}")

    client = QueryLakeClient(base_url="http://testserver", oauth2="tok")
    client._client.close()
    client._client = _mock_client(handler)
    try:
        summary = client.profile_bringup_summary()
        kernel_summary = client.kernel_profile_bringup_summary()
        assert summary.profile.id == "aws_aurora_pg_opensearch_v1"
        assert summary.summary.required_projection_count == 3
        assert summary.needs_projection_build() is True
        assert summary.summary.bootstrapable_required_projection_count == 2
        assert summary.summary.nonbootstrapable_required_projection_count == 0
        assert summary.summary.recommended_projection_count == 2
        assert summary.summary.recommended_ready_projection_count == 0
        assert summary.summary.recommended_projection_ids_needing_build_count == 2
        assert summary.summary.bootstrapable_recommended_projection_count == 2
        assert summary.summary.nonbootstrapable_recommended_projection_count == 0
        assert summary.backend_connectivity_blocked() is False
        assert summary.runtime_blocked() is True
        assert summary.lexical_degraded() is True
        assert summary.exact_lexical_constraints_recommend_gold() is True
        assert summary.compatibility_projection_reliance() is True
        assert summary.canonical_projection_coverage() is False
        assert "search_hybrid.document_chunk" in summary.route_runtime_blocked_ids
        assert summary.summary.lexical_degraded_route_count == 1
        assert summary.summary.lexical_gold_recommended_route_count == 1
        assert summary.summary.route_lexical_support_class_counts["degraded_supported"] == 1
        assert summary.summary.lexical_capability_blocker_counts["retrieval.lexical.hard_constraints"] == 1
        assert summary.summary.compatibility_projection_route_count == 1
        assert summary.summary.compatibility_projection_target_count == 2
        assert summary.summary.required_projection_status_counts["ready"] == 1
        assert summary.declared_route_support_state("search_hybrid.document_chunk") == "degraded"
        assert summary.declared_executable_route_ids == ["search_hybrid.document_chunk"]
        assert summary.declared_optional_route_ids == []
        assert summary.declared_executable_runtime_ready_ids == []
        assert summary.declared_executable_runtime_blocked_ids == ["search_hybrid.document_chunk"]
        assert summary.declared_routes_runtime_ready() is False
        assert summary.lexical_degraded_route_ids == ["search_hybrid.document_chunk"]
        assert summary.lexical_gold_recommended_route_ids == ["search_hybrid.document_chunk"]
        assert summary.route_prefers_gold_for_exact_constraints("search_hybrid.document_chunk") is True
        assert summary.route_exact_constraint_degraded_capabilities("search_hybrid.document_chunk") == [
            "retrieval.lexical.advanced_operators",
            "retrieval.lexical.phrase_boost",
            "retrieval.lexical.proximity",
        ]
        assert summary.route_exact_constraint_unsupported_capabilities("search_hybrid.document_chunk") == [
            "retrieval.lexical.hard_constraints"
        ]
        assert summary.compatibility_projection_route_ids == ["search_hybrid.document_chunk"]
        assert summary.compatibility_projection_target_ids == [
            "document_chunk_dense_projection_v1",
            "document_chunk_lexical_projection_v1",
        ]
        assert summary.projection_building_ids == []
        assert summary.projection_failed_ids == []
        assert summary.projection_stale_ids == []
        assert summary.projection_absent_ids == [
            "document_chunk_lexical_projection_v1",
            "document_chunk_dense_projection_v1",
        ]
        assert summary.recommended_projection_ids == [
            "segment_lexical_projection_v1",
            "segment_dense_projection_v1",
        ]
        assert summary.recommended_ready_projection_ids == []
        assert summary.recommended_projection_ids_needing_build == [
            "segment_lexical_projection_v1",
            "segment_dense_projection_v1",
        ]
        assert summary.bootstrapable_required_projections() == [
            "document_chunk_lexical_projection_v1",
            "document_chunk_dense_projection_v1",
        ]
        assert summary.nonbootstrapable_required_projections() == []
        assert summary.recommended_projections() == [
            "segment_lexical_projection_v1",
            "segment_dense_projection_v1",
        ]
        assert summary.recommended_projections_needing_build() == [
            "segment_lexical_projection_v1",
            "segment_dense_projection_v1",
        ]
        assert summary.bootstrapable_recommended_projections() == [
            "segment_lexical_projection_v1",
            "segment_dense_projection_v1",
        ]
        assert summary.nonbootstrapable_recommended_projections() == []
        assert summary.bootstrapable_required_projection_ids == [
            "document_chunk_lexical_projection_v1",
            "document_chunk_dense_projection_v1",
        ]
        assert summary.bootstrapable_recommended_projection_ids == [
            "segment_lexical_projection_v1",
            "segment_dense_projection_v1",
        ]
        assert summary.absent_projections() == [
            "document_chunk_lexical_projection_v1",
            "document_chunk_dense_projection_v1",
        ]
        assert summary.summary.next_action_count == 4
        assert summary.summary.route_recovery_count == 1
        assert summary.bootstrap_command() == "python scripts/db_compat_profile_bootstrap.py --profile aws_aurora_pg_opensearch_v1"
        assert summary.backend_targets[0].plane == "projection"
        assert summary.backend_targets[0].target["host"] == "search.example.com"
        assert summary.highest_priority_actions()[0].kind == "bootstrap_projections"
        gold_action = next(
            action
            for action in summary.highest_priority_actions()
            if action.kind == "prefer_gold_profile_for_exact_lexical_constraints"
        )
        assert gold_action.route_ids == ["search_hybrid.document_chunk"]
        assert "retrieval.lexical.hard_constraints" in gold_action.capability_ids
        assert client.bringup_bootstrap_command() == "python scripts/db_compat_profile_bootstrap.py --profile aws_aurora_pg_opensearch_v1"
        assert client.bringup_next_actions()[0]["kind"] == "bootstrap_projections"
        assert client.bringup_backend_targets()[0]["plane"] == "projection"
        assert client.bringup_lexical_degraded_routes() == ["search_hybrid.document_chunk"]
        assert client.bringup_lexical_gold_recommended_routes() == ["search_hybrid.document_chunk"]
        assert client.bringup_declared_route_support() == {"search_hybrid.document_chunk": "degraded"}
        assert client.bringup_declared_executable_routes() == ["search_hybrid.document_chunk"]
        assert client.bringup_declared_optional_routes() == []
        assert client.bringup_route_declared_executable("search_hybrid.document_chunk") is True
        assert client.bringup_route_declared_optional("search_hybrid.document_chunk") is False
        assert client.bringup_declared_runtime_ready_routes() == []
        assert client.bringup_declared_runtime_blocked_routes() == ["search_hybrid.document_chunk"]
        assert client.bringup_declared_routes_runtime_ready() is False
        assert client.bringup_route_recovery()[0]["route_id"] == "search_hybrid.document_chunk"
        assert client.bringup_route_recovery_entry("search_hybrid.document_chunk")["lexical_support_class"] == "degraded_supported"
        assert client.bringup_route_recovery_entry("search_hybrid.document_chunk")["query_ir_v2"]["route_id"] == "search_hybrid.document_chunk"
        assert client.bringup_route_recovery_entry("search_hybrid.document_chunk")["projection_ir_v2"]["representation_scope_id"] == "document_chunk"
        assert client.bringup_route_recovery_entry("missing") is None
        assert client.route_prefers_gold_for_exact_constraints("search_hybrid.document_chunk") is True
        assert client.route_exact_constraint_degraded_capabilities("search_hybrid.document_chunk") == [
            "retrieval.lexical.advanced_operators",
            "retrieval.lexical.phrase_boost",
            "retrieval.lexical.proximity",
        ]
        assert client.route_exact_constraint_unsupported_capabilities("search_hybrid.document_chunk") == [
            "retrieval.lexical.hard_constraints"
        ]
        assert client.bringup_projection_status_buckets()["absent"] == [
            "document_chunk_lexical_projection_v1",
            "document_chunk_dense_projection_v1",
        ]
        assert client.bringup_route_required_projection_descriptor_ids("search_hybrid.document_chunk") == [
            "document_chunk_lexical_projection_v1",
            "document_chunk_dense_projection_v1",
        ]
        assert client.bringup_recommended_projection_status_buckets() == {
            "ready": [],
            "needs_build": ["segment_lexical_projection_v1", "segment_dense_projection_v1"],
            "all": ["segment_lexical_projection_v1", "segment_dense_projection_v1"],
        }
        assert summary.profile_diagnostics is not None
        assert summary.projection_diagnostics is not None
        projection_item = summary.projection_diagnostics.projection("document_chunk_lexical_projection_v1")
        assert projection_item is not None
        assert projection_item.materialization_target["source_scope"] == "document_chunk"
        assert projection_item.materialization_target["target_backend_name"] == "opensearch"
        assert kernel_summary.summary.ready_projection_count == 1
    finally:
        client.close()


def test_api_raises_on_success_false():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"success": False, "error": "bad auth", "trace": "stack..."},
        )

    client = QueryLakeClient(base_url="http://testserver")
    client._client.close()
    client._client = _mock_client(handler)
    try:
        with pytest.raises(QueryLakeAPIError) as exc:
            client.api("search_hybrid", {"query": "hello"})
        assert "bad auth" in str(exc.value)
        assert exc.value.trace == "stack..."
    finally:
        client.close()


def test_readyz_summary_helpers():
    payload = {
        "ok": True,
        "db": "ok",
        "models": ["bge-m3", "reranker"],
        "db_profile": {
            "id": "aws_aurora_pg_opensearch_v1",
            "label": "Aurora PostgreSQL + OpenSearch",
            "implemented": True,
            "recommended": False,
            "maturity": "split_stack_executable",
            "backend_stack": {
                "authority": "aurora_postgresql",
                "lexical": "opensearch",
                "dense": "opensearch",
            },
        },
        "db_profile_diagnostics": {
            "boot_ready": False,
            "configuration_ready": True,
            "route_runtime_ready": False,
        },
        "db_profile_bringup": {
            "summary": {
                "boot_ready": False,
                "configuration_ready": True,
                "route_execution_ready": True,
                "route_runtime_ready": False,
                "backend_connectivity_ready": True,
                "required_projection_count": 3,
                "ready_projection_count": 1,
                "projection_ids_needing_build_count": 2,
                "runtime_ready_route_count": 1,
                "runtime_blocked_route_count": 2,
                "backend_unreachable_plane_count": 0,
                "next_action_count": 1,
            },
            "projection_ids_needing_build": [
                "document_chunk_lexical_projection_v1",
                "document_chunk_dense_projection_v1",
            ],
            "route_runtime_blocked_ids": [
                "search_hybrid.document_chunk",
                "search_bm25.document_chunk",
            ],
            "backend_unreachable_planes": [],
        },
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/readyz"
        return httpx.Response(200, json=payload)

    client = QueryLakeClient(base_url="http://testserver", oauth2="tok")
    client._client.close()
    client._client = _mock_client(handler)
    try:
        summary = client.readyz_summary()
        assert summary.ok is True
        assert summary.profile is not None
        assert summary.profile.id == "aws_aurora_pg_opensearch_v1"
        assert summary.models == ["bge-m3", "reranker"]
        assert summary.boot_ready() is False
        assert summary.configuration_ready() is True
        assert summary.route_runtime_ready() is False
        assert summary.bringup is not None
        assert summary.bringup.projection_blocked() is True
        assert summary.bringup.backend_blocked() is False
        assert summary.bringup.route_runtime_blocked_ids == [
            "search_hybrid.document_chunk",
            "search_bm25.document_chunk",
        ]
    finally:
        client.close()


def test_upload_document_round_trip(tmp_path):
    sample = tmp_path / "sample.txt"
    sample.write_text("hello world", encoding="utf-8")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/upload_document"
        params = dict(request.url.params)
        assert "parameters" in params
        decoded = json.loads(params["parameters"])
        assert decoded["collection_hash_id"] == "abc123"
        assert decoded["create_embeddings"] is True
        assert decoded["auth"]["oauth2"] == "token"
        body = request.content
        assert b"sample.txt" in body
        return httpx.Response(200, json={"success": True, "result": {"hash_id": "doc1"}})

    client = QueryLakeClient(base_url="http://testserver", oauth2="token")
    client._client.close()
    client._client = _mock_client(handler)
    try:
        result = client.upload_document(file_path=sample, collection_hash_id="abc123")
        assert result["hash_id"] == "doc1"
    finally:
        client.close()


def test_upload_document_injects_idempotency_key(tmp_path):
    sample = tmp_path / "sample2.txt"
    sample.write_text("hello world", encoding="utf-8")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/upload_document"
        params = dict(request.url.params)
        decoded = json.loads(params["parameters"])
        metadata = decoded.get("document_metadata")
        assert isinstance(metadata, dict)
        assert metadata.get("existing") == "value"
        ingest_meta = metadata.get("_querylake_ingest")
        assert isinstance(ingest_meta, dict)
        assert ingest_meta.get("idempotency_key") == "idem_123"
        return httpx.Response(200, json={"success": True, "result": {"hash_id": "doc2"}})

    client = QueryLakeClient(base_url="http://testserver", oauth2="token")
    client._client.close()
    client._client = _mock_client(handler)
    try:
        result = client.upload_document(
            file_path=sample,
            collection_hash_id="abc123",
            document_metadata={"existing": "value"},
            idempotency_key="idem_123",
        )
        assert result["hash_id"] == "doc2"
    finally:
        client.close()


def test_fetch_document_uses_document_id_payload():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["payload"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(200, json={"success": True, "result": {"hash_id": "doc_123", "md": {}}})

    client = QueryLakeClient(base_url="http://testserver", oauth2="token")
    client._client.close()
    client._client = _mock_client(handler)
    try:
        result = client.fetch_document(document_hash_id="doc_123", get_chunk_count=True)
        assert result["hash_id"] == "doc_123"
        assert captured["path"] == "/api/fetch_document"
        assert captured["payload"]["document_id"] == "doc_123"
        assert captured["payload"]["get_chunk_count"] is True
    finally:
        client.close()


def test_upload_directory_dry_run_with_filters(tmp_path):
    root = tmp_path / "bulk"
    root.mkdir(parents=True, exist_ok=True)
    (root / "a.txt").write_text("a", encoding="utf-8")
    (root / "b.md").write_text("b", encoding="utf-8")
    sub = root / "sub"
    sub.mkdir(parents=True, exist_ok=True)
    (sub / "c.txt").write_text("c", encoding="utf-8")

    client = QueryLakeClient(base_url="http://testserver", oauth2="token")
    try:
        payload = client.upload_directory(
            collection_hash_id="abc123",
            directory=root,
            pattern="*",
            recursive=True,
            include_extensions=[".txt"],
            exclude_globs=["sub/*"],
            dry_run=True,
        )
        assert payload["dry_run"] is True
        assert payload["requested_files"] == 1
        assert payload["uploaded"] == 0
        assert payload["failed"] == 0
        assert len(payload["selected_files"]) == 1
        assert payload["selected_files"][0].endswith("a.txt")
    finally:
        client.close()


def test_upload_directory_explicit_file_list_and_errors(tmp_path, monkeypatch):
    root = tmp_path / "bulk2"
    root.mkdir(parents=True, exist_ok=True)
    good = root / "good.txt"
    good.write_text("good", encoding="utf-8")
    bad = root / "bad.txt"
    bad.write_text("bad", encoding="utf-8")

    calls = []

    def _fake_upload_document(**kwargs):
        file_path = str(kwargs["file_path"])
        calls.append(file_path)
        if file_path.endswith("bad.txt"):
            raise RuntimeError("simulated failure")
        return {"hash_id": "doc_ok"}

    client = QueryLakeClient(base_url="http://testserver", oauth2="token")
    monkeypatch.setattr(client, "upload_document", _fake_upload_document)
    try:
        payload = client.upload_directory(
            collection_hash_id="abc123",
            file_paths=[good, bad],
            fail_fast=False,
        )
        assert payload["selection_mode"] == "explicit-file-list"
        assert payload["requested_files"] == 2
        assert payload["uploaded"] == 1
        assert payload["failed"] == 1
        assert len(payload["errors"]) == 1
        assert "bad.txt" in payload["errors"][0]["file"]
        assert len(calls) == 2
    finally:
        client.close()


def test_upload_directory_dedupe_content_hash_run_local(tmp_path, monkeypatch):
    root = tmp_path / "bulk_hash"
    root.mkdir(parents=True, exist_ok=True)
    one = root / "a.txt"
    one.write_text("same", encoding="utf-8")
    two = root / "b.txt"
    two.write_text("same", encoding="utf-8")
    three = root / "c.txt"
    three.write_text("different", encoding="utf-8")

    calls = []

    def _fake_upload_document(**kwargs):
        calls.append(str(kwargs["file_path"]))
        return {"hash_id": "doc_ok"}

    client = QueryLakeClient(base_url="http://testserver", oauth2="token")
    monkeypatch.setattr(client, "upload_document", _fake_upload_document)
    try:
        payload = client.upload_directory(
            collection_hash_id="abc123",
            file_paths=[one, two, three],
            dedupe_by_content_hash=True,
            dedupe_scope="run-local",
        )
        assert payload["uploaded"] == 2
        assert payload["failed"] == 0
        assert payload["dedupe_by_content_hash"] is True
        assert payload["dedupe_scope"] == "run-local"
        assert payload["dedupe_skipped"] == 1
        assert len(payload["dedupe_skipped_files"]) == 1
        assert payload["dedupe_skipped_files"][0]["reason"] == "run-local-duplicate"
        assert calls == [str(one), str(three)]
    finally:
        client.close()


def test_upload_directory_dedupe_checkpoint_resume(tmp_path, monkeypatch):
    root = tmp_path / "bulk_hash_checkpoint"
    root.mkdir(parents=True, exist_ok=True)
    one = root / "one.txt"
    one.write_text("same", encoding="utf-8")
    one_hash = hashlib.sha256(one.read_bytes()).hexdigest()
    checkpoint_file = tmp_path / "checkpoint_hash.json"
    checkpoint_file.write_text(
        json.dumps(
            {
                "version": 1,
                "selection_sha256": "mismatch-ok",
                "uploaded_files": [],
                "uploaded_content_hashes": [one_hash],
            }
        ),
        encoding="utf-8",
    )

    calls = []

    def _fake_upload_document(**kwargs):
        calls.append(str(kwargs["file_path"]))
        return {"hash_id": "doc_ok"}

    client = QueryLakeClient(base_url="http://testserver", oauth2="token")
    monkeypatch.setattr(client, "upload_document", _fake_upload_document)
    try:
        payload = client.upload_directory(
            collection_hash_id="abc123",
            file_paths=[one],
            checkpoint_file=checkpoint_file,
            resume=True,
            strict_checkpoint_match=False,
            dedupe_by_content_hash=True,
            dedupe_scope="checkpoint-resume",
        )
        assert payload["dedupe_skipped"] == 1
        assert payload["uploaded"] == 0
        assert payload["failed"] == 0
        assert payload["status"] == "already_complete"
        assert payload["dedupe_skipped_files"][0]["reason"] == "checkpoint-resume-duplicate"
        assert calls == []
    finally:
        client.close()


def test_upload_directory_content_hash_idempotency_strategy(tmp_path, monkeypatch):
    root = tmp_path / "bulk_idem"
    root.mkdir(parents=True, exist_ok=True)
    one = root / "one.txt"
    one.write_text("one", encoding="utf-8")
    one_hash = hashlib.sha256(one.read_bytes()).hexdigest()

    keys = []

    def _fake_upload_document(**kwargs):
        keys.append(kwargs.get("idempotency_key"))
        return {"hash_id": "doc_ok"}

    client = QueryLakeClient(base_url="http://testserver", oauth2="token")
    monkeypatch.setattr(client, "upload_document", _fake_upload_document)
    try:
        payload = client.upload_directory(
            collection_hash_id="abc123",
            file_paths=[one],
            idempotency_strategy="content-hash",
            idempotency_prefix="test-prefix",
        )
        assert payload["uploaded"] == 1
        assert keys == [f"test-prefix:abc123:{one_hash}"]
    finally:
        client.close()


def test_upload_directory_checkpoint_resume(tmp_path, monkeypatch):
    root = tmp_path / "bulk3"
    root.mkdir(parents=True, exist_ok=True)
    one = root / "one.txt"
    one.write_text("one", encoding="utf-8")
    two = root / "two.txt"
    two.write_text("two", encoding="utf-8")
    checkpoint_file = tmp_path / "checkpoint.json"

    first_pass_calls = []

    def _first_pass_upload(**kwargs):
        file_path = str(kwargs["file_path"])
        first_pass_calls.append(file_path)
        if file_path.endswith("two.txt"):
            raise RuntimeError("transient failure")
        return {"hash_id": "doc_ok"}

    second_pass_calls = []

    def _second_pass_upload(**kwargs):
        file_path = str(kwargs["file_path"])
        second_pass_calls.append(file_path)
        return {"hash_id": "doc_ok"}

    client = QueryLakeClient(base_url="http://testserver", oauth2="token")
    monkeypatch.setattr(client, "upload_document", _first_pass_upload)
    try:
        first = client.upload_directory(
            collection_hash_id="abc123",
            file_paths=[one, two],
            fail_fast=True,
            checkpoint_file=checkpoint_file,
            checkpoint_save_every=1,
        )
        assert first["uploaded"] == 1
        assert first["failed"] == 1
        assert checkpoint_file.exists()

        monkeypatch.setattr(client, "upload_document", _second_pass_upload)
        second = client.upload_directory(
            collection_hash_id="abc123",
            file_paths=[one, two],
            checkpoint_file=checkpoint_file,
            resume=True,
        )
        assert second["resumed_from_checkpoint"] is True
        assert second["skipped_already_uploaded"] == 1
        assert second["uploaded"] == 1
        assert second["failed"] == 0
        assert first_pass_calls == [str(one), str(two)]
        assert second_pass_calls == [str(two)]
    finally:
        client.close()


def test_upload_directory_rejects_invalid_dedupe_or_idempotency(tmp_path):
    root = tmp_path / "bulk5"
    root.mkdir(parents=True, exist_ok=True)
    one = root / "one.txt"
    one.write_text("one", encoding="utf-8")

    client = QueryLakeClient(base_url="http://testserver", oauth2="token")
    try:
        with pytest.raises(ValueError, match="Unsupported dedupe_scope"):
            client.upload_directory(
                collection_hash_id="abc123",
                file_paths=[one],
                dedupe_by_content_hash=True,
                dedupe_scope="bad-scope",
            )
        with pytest.raises(ValueError, match="Unsupported idempotency_strategy"):
            client.upload_directory(
                collection_hash_id="abc123",
                file_paths=[one],
                idempotency_strategy="bad-strategy",
            )
    finally:
        client.close()


def test_upload_directory_options_validation():
    with pytest.raises(ValueError, match="checkpoint_save_every"):
        UploadDirectoryOptions(file_paths=["/tmp/a.txt"], checkpoint_save_every=0)
    with pytest.raises(ValueError, match="dedupe_scope"):
        UploadDirectoryOptions(file_paths=["/tmp/a.txt"], dedupe_scope="invalid")
    with pytest.raises(ValueError, match="idempotency_strategy"):
        UploadDirectoryOptions(file_paths=["/tmp/a.txt"], idempotency_strategy="invalid")
    with pytest.raises(ValueError, match="resume=True requires checkpoint_file"):
        UploadDirectoryOptions(file_paths=["/tmp/a.txt"], resume=True)


def test_upload_directory_with_options(tmp_path, monkeypatch):
    root = tmp_path / "bulk_options"
    root.mkdir(parents=True, exist_ok=True)
    one = root / "one.txt"
    one.write_text("one", encoding="utf-8")

    calls = []

    def _fake_upload_document(**kwargs):
        calls.append(str(kwargs["file_path"]))
        return {"hash_id": "doc_ok"}

    client = QueryLakeClient(base_url="http://testserver", oauth2="token")
    monkeypatch.setattr(client, "upload_document", _fake_upload_document)
    try:
        options = UploadDirectoryOptions(
            file_paths=[one],
            dedupe_by_content_hash=True,
            idempotency_strategy="content-hash",
            idempotency_prefix="typed",
        )
        payload = client.upload_directory_with_options(
            collection_hash_id="abc123",
            options=options,
        )
        assert payload["uploaded"] == 1
        assert payload["failed"] == 0
        assert payload["dedupe_by_content_hash"] is True
        assert calls == [str(one)]
    finally:
        client.close()


def test_upload_directory_checkpoint_hash_mismatch(tmp_path, monkeypatch):
    root = tmp_path / "bulk4"
    root.mkdir(parents=True, exist_ok=True)
    one = root / "one.txt"
    one.write_text("one", encoding="utf-8")
    checkpoint_file = tmp_path / "checkpoint_mismatch.json"
    checkpoint_file.write_text(
        json.dumps(
            {
                "version": 1,
                "selection_sha256": "mismatch",
                "uploaded_files": [],
            }
        ),
        encoding="utf-8",
    )

    client = QueryLakeClient(base_url="http://testserver", oauth2="token")
    monkeypatch.setattr(client, "upload_document", lambda **kwargs: {"hash_id": "doc_ok"})
    try:
        with pytest.raises(ValueError, match="selection hash mismatch"):
            client.upload_directory(
                collection_hash_id="abc123",
                file_paths=[one],
                checkpoint_file=checkpoint_file,
                resume=True,
            )
    finally:
        client.close()


def test_search_hybrid_with_option_models(monkeypatch):
    captured: list[dict] = []

    def _fake_api(function_name, payload, **kwargs):
        assert function_name == "search_hybrid"
        captured.append(dict(payload))
        return {"rows": [{"id": "row1", "text": "hello"}], "duration": {"total_ms": 1.0}}

    client = QueryLakeClient(base_url="http://testserver", oauth2="token")
    monkeypatch.setattr(client, "api", _fake_api)
    try:
        options = HybridSearchOptions(
            limit_bm25=5,
            limit_similarity=7,
            limit_sparse=9,
            bm25_weight=0.3,
            similarity_weight=0.4,
            sparse_weight=0.3,
        )
        rows = client.search_hybrid_with_options(
            query="hello",
            collection_ids=["c1"],
            options=options,
        )
        metrics = client.search_hybrid_with_metrics_options(
            query="hello",
            collection_ids=["c1"],
            options=options,
        )
        assert len(rows) == 1
        assert metrics["duration"]["total_ms"] == 1.0
        assert captured[0]["limit_bm25"] == 5
        assert captured[0]["limit_similarity"] == 7
        assert captured[0]["limit_sparse"] == 9
        assert captured[0]["bm25_weight"] == 0.3
        assert captured[0]["similarity_weight"] == 0.4
        assert captured[0]["sparse_weight"] == 0.3
    finally:
        client.close()


def test_search_hybrid_plan_explain_helpers(monkeypatch):
    captured: list[dict] = []

    def _fake_api(function_name, payload, **kwargs):
        assert function_name == "search_hybrid"
        captured.append(dict(payload))
        return {
            "rows": [{"id": "row1", "text": "hello"}],
            "plan_explain": {
                "route": "search_hybrid",
                "pipeline": {
                    "pipeline_id": "document_chunk_hybrid_v1",
                    "pipeline_version": "v1",
                    "source": "profile_aware_route",
                    "resolution": {"profile_id": "aws_aurora_pg_opensearch_v1"},
                    "flags": {"degraded": True},
                    "budgets": {"limit_bm25": 5, "limit_similarity": 7},
                    "stages": [
                        {
                            "stage_id": "lexical",
                            "primitive_id": "bm25_chunk_search",
                            "enabled": True,
                            "config": {"limit": 5},
                            "adapter": {
                                "lane_family": "lexical_bm25",
                                "adapter_id": "opensearch.lexical.aws_aurora_pg_opensearch_v1",
                                "support_state": "supported",
                            },
                        },
                        {
                            "stage_id": "dense",
                            "primitive_id": "dense_chunk_search",
                            "enabled": True,
                            "config": {"limit": 7},
                            "adapter": {
                                "lane_family": "dense_vector",
                                "adapter_id": "opensearch.dense.aws_aurora_pg_opensearch_v1",
                                "support_state": "supported",
                            },
                        },
                    ],
                },
                "effective": {
                    "route_executor": "opensearch.search_hybrid.document_chunk.aws_aurora_pg_opensearch_v1",
                    "lane_state": {
                        "lexical_bm25": {
                            "adapter_id": "opensearch.lexical.aws_aurora_pg_opensearch_v1",
                            "support_state": "supported",
                        },
                        "dense_vector": {
                            "adapter_id": "opensearch.dense.aws_aurora_pg_opensearch_v1",
                            "support_state": "supported",
                        },
                    },
                    "lexical_capability_plan": {
                        "degraded_capabilities": ["retrieval.lexical.proximity"],
                        "unsupported_capabilities": [],
                    },
                },
            },
        }

    client = QueryLakeClient(base_url="http://testserver", oauth2="token")
    monkeypatch.setattr(client, "api", _fake_api)
    try:
        summary = client.search_hybrid_plan_explain(query="hello", collection_ids=["c1"])
        assert summary.route == "search_hybrid"
        assert summary.pipeline.pipeline_id == "document_chunk_hybrid_v1"
        assert summary.route_executor() == "opensearch.search_hybrid.document_chunk.aws_aurora_pg_opensearch_v1"
        assert summary.adapter_ids() == {
            "lexical_bm25": "opensearch.lexical.aws_aurora_pg_opensearch_v1",
            "dense_vector": "opensearch.dense.aws_aurora_pg_opensearch_v1",
        }
        assert summary.degraded_capabilities() == ["retrieval.lexical.proximity"]
        assert summary.unsupported_capabilities() == []
        assert captured[0]["explain_plan"] is True
    finally:
        client.close()


def test_search_hybrid_plan_explain_with_options(monkeypatch):
    captured: list[dict] = []

    def _fake_api(function_name, payload, **kwargs):
        assert function_name == "search_hybrid"
        captured.append(dict(payload))
        return {"rows": [], "plan_explain": {"route": "search_hybrid", "pipeline": {"stages": []}, "effective": {}}}

    client = QueryLakeClient(base_url="http://testserver", oauth2="token")
    monkeypatch.setattr(client, "api", _fake_api)
    try:
        options = HybridSearchOptions(
            limit_bm25=3,
            limit_similarity=4,
            limit_sparse=0,
            bm25_weight=0.6,
            similarity_weight=0.4,
            sparse_weight=0.0,
        )
        summary = client.search_hybrid_plan_explain_with_options(
            query="hello",
            collection_ids=["c1"],
            options=options,
        )
        assert summary.route == "search_hybrid"
        assert captured[0]["limit_bm25"] == 3
        assert captured[0]["limit_similarity"] == 4
        assert captured[0]["bm25_weight"] == 0.6
        assert captured[0]["similarity_weight"] == 0.4
        assert captured[0]["explain_plan"] is True
    finally:
        client.close()


def test_search_bm25_plan_explain_helpers(monkeypatch):
    captured: list[dict] = []

    def _fake_api(function_name, payload, **kwargs):
        assert function_name == "search_bm25"
        captured.append(dict(payload))
        return {
            "rows": [{"id": "row1", "text": "hello"}],
            "plan_explain": {
                "route": "search_bm25",
                "pipeline": {
                    "pipeline_id": "document_chunk_bm25_v1",
                    "pipeline_version": "v1",
                    "source": "profile_aware_route",
                    "resolution": {"profile_id": "paradedb_postgres_gold_v1"},
                    "flags": {},
                    "budgets": {"limit": 10},
                    "stages": [
                        {
                            "stage_id": "lexical",
                            "primitive_id": "bm25_chunk_search",
                            "enabled": True,
                            "config": {"limit": 10},
                            "adapter": {
                                "lane_family": "lexical_bm25",
                                "adapter_id": "paradedb_bm25_v1",
                                "support_state": "supported",
                            },
                        }
                    ],
                },
                "effective": {
                    "route_executor": {
                        "executor_id": "paradedb.search_bm25.document_chunk.v1",
                        "planning_v2": {"planning_surface": "route_resolution"},
                    },
                    "query_ir_v2": {
                        "route_id": "search_bm25.document_chunk",
                        "representation_scope_id": "document_chunk",
                    },
                    "projection_ir_v2": {
                        "route_id": "search_bm25.document_chunk",
                        "representation_scope_id": "document_chunk",
                        "buildability_class": "executable_requires_build",
                        "metadata": {"planning_surface": "route_resolution"},
                    },
                    "lexical_capability_plan": {
                        "degraded_capabilities": [],
                        "unsupported_capabilities": [],
                    },
                },
            },
        }

    client = QueryLakeClient(base_url="http://testserver", oauth2="token")
    monkeypatch.setattr(client, "api", _fake_api)
    try:
        summary = client.search_bm25_plan_explain(query="hello", collection_ids=["c1"])
        assert summary.route == "search_bm25"
        assert summary.route_id() == "search_bm25.document_chunk"
        assert summary.representation_scope_id() == "document_chunk"
        assert summary.planning_surface() == "route_resolution"
        assert summary.projection_buildability_class() == "executable_requires_build"
        assert captured[0]["explain_plan"] is True
    finally:
        client.close()


def test_search_file_chunks_plan_explain_helpers(monkeypatch):
    captured: list[dict] = []

    def _fake_api(function_name, payload, **kwargs):
        assert function_name == "search_file_chunks"
        captured.append(dict(payload))
        return {
            "results": [{"id": "fc-1", "text": "hello"}],
            "plan_explain": {
                "route": "search_file_chunks",
                "pipeline": {
                    "pipeline_id": "file_chunk_bm25_v1",
                    "pipeline_version": "v1",
                    "source": "profile_aware_route",
                    "resolution": {"profile_id": "paradedb_postgres_gold_v1"},
                    "flags": {},
                    "budgets": {"limit": 20},
                    "stages": [
                        {
                            "stage_id": "lexical",
                            "primitive_id": "bm25_file_chunk_search",
                            "enabled": True,
                            "config": {"limit": 20},
                            "adapter": {
                                "lane_family": "lexical_bm25",
                                "adapter_id": "paradedb_bm25_v1",
                                "support_state": "supported",
                            },
                        }
                    ],
                },
                "effective": {
                    "route_executor": {
                        "executor_id": "paradedb.search_file_chunks.v1",
                        "planning_v2": {"planning_surface": "route_resolution"},
                    },
                    "query_ir_v2": {
                        "route_id": "search_file_chunks",
                        "representation_scope_id": "file_chunk",
                    },
                    "projection_ir_v2": {
                        "route_id": "search_file_chunks",
                        "representation_scope_id": "file_chunk",
                        "buildability_class": "executable_requires_build",
                        "metadata": {"planning_surface": "route_resolution"},
                    },
                    "lexical_capability_plan": {
                        "degraded_capabilities": [],
                        "unsupported_capabilities": [],
                    },
                },
            },
        }

    client = QueryLakeClient(base_url="http://testserver", oauth2="token")
    monkeypatch.setattr(client, "api", _fake_api)
    try:
        summary = client.search_file_chunks_plan_explain(query="hello")
        assert summary.route == "search_file_chunks"
        assert summary.route_id() == "search_file_chunks"
        assert summary.representation_scope_id() == "file_chunk"
        assert summary.planning_surface() == "route_resolution"
        assert summary.projection_buildability_class() == "executable_requires_build"
        assert captured[0]["explain_plan"] is True
    finally:
        client.close()


def test_search_hybrid_accepts_orchestrated_dict_payload():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/search_hybrid"
        return httpx.Response(
            200,
            json={
                "success": True,
                "result": {
                    "rows": [{"id": "row1", "text": "hello world"}],
                    "duration": {"total": 0.01},
                },
            },
        )

    client = QueryLakeClient(base_url="http://testserver", oauth2="token")
    client._client.close()
    client._client = _mock_client(handler)
    try:
        rows = client.search_hybrid(query="hello", collection_ids=["c1"])
        assert len(rows) == 1
        assert rows[0]["id"] == "row1"
        payload = client.search_hybrid_with_metrics(query="hello", collection_ids=["c1"])
        assert isinstance(payload.get("rows"), list)
        assert payload.get("duration", {}).get("total") == 0.01
    finally:
        client.close()


def test_delete_document_uses_hash_id_payload():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/delete_document"
        payload = json.loads(request.content.decode("utf-8"))
        assert payload["hash_id"] == "doc_123"
        return httpx.Response(200, json={"success": True, "result": True})

    client = QueryLakeClient(base_url="http://testserver", oauth2="token")
    client._client.close()
    client._client = _mock_client(handler)
    try:
        result = client.delete_document(document_hash_id="doc_123")
        assert result is True
    finally:
        client.close()


def test_modify_collection_payload():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/modify_document_collection"
        payload = json.loads(request.content.decode("utf-8"))
        assert payload["collection_hash_id"] == "col_12"
        assert payload["title"] == "new title"
        assert payload["description"] == "new desc"
        return httpx.Response(200, json={"success": True, "result": True})

    client = QueryLakeClient(base_url="http://testserver", oauth2="token")
    client._client.close()
    client._client = _mock_client(handler)
    try:
        result = client.modify_collection(
            collection_hash_id="col_12",
            title="new title",
            description="new desc",
        )
        assert result is True
    finally:
        client.close()

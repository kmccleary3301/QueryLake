from __future__ import annotations

from QueryLake.canon.control import (
    CanonPublishPointer,
    CanonPublishRequest,
    CanonPublishReview,
    apply_publish_plan,
    apply_revert_plan,
    build_publish_plan,
    load_pointer_registry,
)
from QueryLake.canon.control.authority_control_registry import load_authority_control_registry
from QueryLake.canon.control.route_serving_registry import build_route_slice_state, load_route_serving_registry


def _ready_exit() -> dict:
    return {
        "gates": {
            "all_bounded_routes_compile": True,
            "shadow_reports_present": True,
            "no_candidate_set_deltas": True,
            "declared_routes_runtime_ready": True,
        },
        "summary": {"ready_for_phase1b": True},
    }


def test_pointer_registry_apply_and_revert(tmp_path):
    registry_path = tmp_path / "registry.json"
    current_pointer = CanonPublishPointer(
        pointer_id="ptr-shadow-1",
        graph_id="graph-1",
        package_revision="rev-1",
        profile_id="aws_aurora_pg_opensearch_v1",
        route_ids=["search_bm25.document_chunk"],
        mode="shadow",
    )
    plan = build_publish_plan(
        CanonPublishRequest(
            target=CanonPublishPointer(
                pointer_id="ptr-primary-2",
                graph_id="graph-2",
                package_revision="rev-2",
                profile_id="aws_aurora_pg_opensearch_v1",
                route_ids=["search_bm25.document_chunk", "search_file_chunks"],
                mode="primary",
                metadata={
                    "package_bindings": {
                        "search_bm25.document_chunk": {
                            "package_id": "pkg-bm25",
                            "package_revision": "rev-2",
                            "graph_id": "graph-2",
                        },
                        "search_file_chunks": {
                            "package_id": "pkg-file",
                            "package_revision": "rev-2",
                            "graph_id": "graph-2b",
                        },
                    }
                },
            ),
            current=current_pointer,
            review=CanonPublishReview(
                branch_name="canonpp-phase1a",
                reviewed=True,
                ci_green=True,
                shadow_evidence_present=True,
            ),
            exit_readiness=_ready_exit(),
        )
    )

    registry = apply_publish_plan(plan=plan, registry_path=registry_path)
    assert registry["shadow_pointer"]["pointer_id"] == "ptr-primary-2"
    assert registry["candidate_primary_pointer"]["pointer_id"] == "ptr-primary-2"
    assert registry["primary_pointer"]["pointer_id"] == "ptr-primary-2"

    reverted = apply_revert_plan(
        revert_plan=plan["revert_plan"],
        pointer=current_pointer.model_dump(),
        registry_path=registry_path,
    )
    assert reverted["shadow_pointer"]["pointer_id"] == "ptr-shadow-1"
    loaded = load_pointer_registry(registry_path)
    assert len(loaded["history"]) == 2


def test_pointer_registry_rejects_blocked_plan(tmp_path):
    registry_path = tmp_path / "registry.json"
    plan = build_publish_plan(
        CanonPublishRequest(
            target=CanonPublishPointer(
                pointer_id="ptr-primary-3",
                graph_id="graph-3",
                package_revision="rev-3",
                profile_id="aws_aurora_pg_opensearch_v1",
                route_ids=["search_bm25.document_chunk"],
                mode="primary",
            ),
            review=CanonPublishReview(
                branch_name="canonpp-phase1a",
                reviewed=True,
                ci_green=True,
                shadow_evidence_present=True,
            ),
            exit_readiness={"gates": {}, "summary": {"ready_for_phase1b": False}},
        )
    )

    try:
        apply_publish_plan(plan=plan, registry_path=registry_path)
    except ValueError as exc:
        assert "blocked" in str(exc).lower()
    else:  # pragma: no cover
        raise AssertionError("blocked publish plan should not be applied")


def test_pointer_registry_rejects_multiroute_pointer_without_route_bindings(tmp_path):
    registry_path = tmp_path / "registry.json"
    plan = {
        "allowed": True,
        "target": {
            "pointer_id": "ptr-primary-4",
            "graph_id": "graph-4",
            "package_revision": "rev-4",
            "profile_id": "aws_aurora_pg_opensearch_v1",
            "route_ids": ["search_bm25.document_chunk", "search_file_chunks"],
            "mode": "candidate_primary",
            "metadata": {},
        },
        "steps": [
            {"step_id": "update_shadow_pointer"},
            {"step_id": "promote_candidate_pointer"},
        ],
        "blockers": [],
    }

    try:
        apply_publish_plan(plan=plan, registry_path=registry_path)
    except ValueError as exc:
        assert "route-level package bindings" in str(exc).lower()
    else:  # pragma: no cover
        raise AssertionError("multi-route pointer without bindings should be rejected")


def test_pointer_registry_applies_authority_control_bootstrap_step(tmp_path):
    registry_path = tmp_path / "registry.json"
    authority_control_registry_path = tmp_path / "authority_control_registry.json"
    plan = {
        "allowed": True,
        "target": {
            "pointer_id": "ptr-target-candidate",
            "graph_id": "graph-target",
            "package_revision": "rev-target",
            "profile_id": "planetscale_opensearch_v1",
            "route_ids": ["search_bm25.document_chunk"],
            "mode": "candidate_primary",
            "metadata": {
                "package_bindings": {
                    "search_bm25.document_chunk": {
                        "package_id": "pkg-bm25",
                        "package_revision": "rev-target",
                        "graph_id": "graph-target",
                    }
                }
            },
        },
        "steps": [
            {
                "step_id": "apply_authority_control_bootstrap",
                "metadata": {
                    "bootstrap_bundle": {
                        "schema_version": "canon_authority_control_bootstrap_bundle_v1",
                        "profile": {"id": "planetscale_opensearch_v1"},
                        "mode": "shadow",
                        "routes": ["search_bm25.document_chunk"],
                        "route_bindings": {
                            "search_bm25.document_chunk": {
                                "package_id": "pkg-bm25",
                                "package_revision": "rev-target",
                                "graph_id": "graph-target",
                            }
                        },
                        "phase1a_bootstrap_bundle": {
                            "execute": False,
                            "summary": {"declared_executable_routes_runtime_ready_after": True},
                        },
                        "summary": {
                            "candidate_primary_bootstrap_ready": True,
                            "primary_bootstrap_ready": False,
                            "configuration_ready": True,
                            "selected_package_resolved_count": 1,
                            "shadow_executable_count": 1,
                        },
                        "recommendations": [],
                    }
                },
            },
            {"step_id": "update_shadow_pointer"},
            {"step_id": "promote_candidate_pointer"},
        ],
        "blockers": [],
    }

    registry = apply_publish_plan(
        plan=plan,
        registry_path=registry_path,
        authority_control_registry_path=authority_control_registry_path,
    )

    assert registry["candidate_primary_pointer"]["pointer_id"] == "ptr-target-candidate"
    authority_control_registry = load_authority_control_registry(authority_control_registry_path)
    assert len(dict(authority_control_registry.get("entries") or {})) == 1


def test_pointer_registry_applies_route_serving_state_for_tranche2a_target_slice(tmp_path):
    registry_path = tmp_path / "registry.json"
    route_serving_registry_path = tmp_path / "route_serving_registry.json"
    plan = {
        "allowed": True,
        "target": {
            "pointer_id": "ptr-target-primary",
            "graph_id": "graph-target",
            "package_revision": "rev-target",
            "profile_id": "planetscale_opensearch_v1",
            "route_ids": ["search_bm25.document_chunk"],
            "mode": "primary",
            "metadata": {
                "package_bindings": {
                    "search_bm25.document_chunk": {
                        "package_id": "pkg-bm25",
                        "package_revision": "rev-target",
                        "graph_id": "graph-target",
                    }
                }
            },
        },
        "steps": [
            {"step_id": "update_shadow_pointer"},
            {"step_id": "promote_candidate_pointer"},
            {"step_id": "cutover_primary_pointer"},
            {"step_id": "apply_route_serving_state", "metadata": {"mode": "primary"}},
        ],
        "blockers": [],
    }

    apply_publish_plan(
        plan=plan,
        registry_path=registry_path,
        route_serving_registry_path=route_serving_registry_path,
    )

    route_serving_registry = load_route_serving_registry(route_serving_registry_path)
    activation = route_serving_registry["activations"][
        "planetscale_opensearch_v1:search_bm25.document_chunk:activation:primary"
    ]
    assert activation["package_ref"] == "pkg-bm25@rev-target"
    apply_state = route_serving_registry["apply_states"][
        "planetscale_opensearch_v1:search_bm25.document_chunk:apply:pkg-bm25@rev-target"
    ]
    assert apply_state["projection_descriptors"] == ["document_chunk_lexical_projection_v1"]
    certification = route_serving_registry["certifications"][
        "planetscale_opensearch_v1:search_bm25.document_chunk:cert:pkg-bm25@rev-target"
    ]
    assert certification["package_revision"] == "rev-target"


def test_pointer_registry_revert_updates_route_serving_state_for_tranche2a_target_slice(tmp_path):
    registry_path = tmp_path / "registry.json"
    route_serving_registry_path = tmp_path / "route_serving_registry.json"
    authority_control_registry_path = tmp_path / "authority_control_registry.json"
    current_pointer = CanonPublishPointer(
        pointer_id="ptr-target-shadow",
        graph_id="graph-shadow",
        package_revision="rev-shadow",
        profile_id="planetscale_opensearch_v1",
        route_ids=["search_bm25.document_chunk"],
        mode="shadow",
        metadata={
            "package_bindings": {
                "search_bm25.document_chunk": {
                    "package_id": "pkg-shadow",
                    "package_revision": "rev-shadow",
                    "graph_id": "graph-shadow",
                }
            }
        },
    )
    plan = build_publish_plan(
        CanonPublishRequest(
            target=CanonPublishPointer(
                pointer_id="ptr-target-candidate",
                graph_id="graph-target",
                package_revision="rev-target",
                profile_id="planetscale_opensearch_v1",
                route_ids=["search_bm25.document_chunk"],
                mode="candidate_primary",
                metadata={
                    "package_bindings": {
                        "search_bm25.document_chunk": {
                            "package_id": "pkg-target",
                            "package_revision": "rev-target",
                            "graph_id": "graph-target",
                        }
                    }
                },
            ),
            current=current_pointer,
            review=CanonPublishReview(
                branch_name="canonpp-tranche2a",
                reviewed=True,
                ci_green=True,
                shadow_evidence_present=True,
            ),
            exit_readiness={
                "gates": {
                    "all_bounded_routes_compile": True,
                    "shadow_reports_present": True,
                    "no_candidate_set_deltas": True,
                    "selected_packages_resolved_for_bounded_routes": True,
                    "no_blocked_search_plane_a_rows": True,
                },
                "target_profile_promotion": {
                    "summary": {
                        "candidate_primary_ready": True,
                        "primary_ready": False,
                    },
                    "authority_control_readiness": {
                        "summary": {
                            "bootstrap_applied": True,
                        },
                        "authority_control_bootstrap": {
                            "schema_version": "canon_authority_control_bootstrap_bundle_v1",
                            "summary": {
                                "candidate_primary_bootstrap_ready": True,
                                "primary_bootstrap_ready": False,
                            },
                            "profile": {"id": "planetscale_opensearch_v1"},
                            "mode": "shadow",
                            "routes": ["search_bm25.document_chunk"],
                        },
                    },
                },
                "summary": {"ready_for_phase1b": False},
            },
        )
    )

    apply_publish_plan(
        plan=plan,
        registry_path=registry_path,
        authority_control_registry_path=authority_control_registry_path,
        route_serving_registry_path=route_serving_registry_path,
    )
    candidate_state = build_route_slice_state(
        registry=load_route_serving_registry(route_serving_registry_path),
        profile_id="planetscale_opensearch_v1",
        route_id="search_bm25.document_chunk",
    )
    assert candidate_state["state"] == "candidate_primary_active"
    assert candidate_state["rollback_ready"] is True

    reverted = apply_revert_plan(
        revert_plan=plan["revert_plan"],
        pointer=current_pointer.model_dump(),
        registry_path=registry_path,
        route_serving_registry_path=route_serving_registry_path,
    )
    assert reverted["shadow_pointer"]["pointer_id"] == "ptr-target-shadow"

    reverted_state = build_route_slice_state(
        registry=load_route_serving_registry(route_serving_registry_path),
        profile_id="planetscale_opensearch_v1",
        route_id="search_bm25.document_chunk",
    )
    assert reverted_state["state"] == "shadow"


def test_pointer_registry_primary_cutover_reverts_route_serving_state_to_candidate(tmp_path):
    registry_path = tmp_path / "registry.json"
    route_serving_registry_path = tmp_path / "route_serving_registry.json"
    authority_control_registry_path = tmp_path / "authority_control_registry.json"
    shadow_pointer = CanonPublishPointer(
        pointer_id="ptr-target-shadow",
        graph_id="graph-shadow",
        package_revision="rev-shadow",
        profile_id="planetscale_opensearch_v1",
        route_ids=["search_bm25.document_chunk"],
        mode="shadow",
        metadata={
            "package_bindings": {
                "search_bm25.document_chunk": {
                    "package_id": "pkg-shadow",
                    "package_revision": "rev-shadow",
                    "graph_id": "graph-shadow",
                }
            }
        },
    )
    candidate_pointer = CanonPublishPointer(
        pointer_id="ptr-target-candidate",
        graph_id="graph-target",
        package_revision="rev-target",
        profile_id="planetscale_opensearch_v1",
        route_ids=["search_bm25.document_chunk"],
        mode="candidate_primary",
        metadata={
            "package_bindings": {
                "search_bm25.document_chunk": {
                    "package_id": "pkg-target",
                    "package_revision": "rev-target",
                    "graph_id": "graph-target",
                }
            }
        },
    )
    primary_pointer = CanonPublishPointer(
        pointer_id="ptr-target-primary",
        graph_id="graph-target",
        package_revision="rev-target",
        profile_id="planetscale_opensearch_v1",
        route_ids=["search_bm25.document_chunk"],
        mode="primary",
        metadata={
            "package_bindings": {
                "search_bm25.document_chunk": {
                    "package_id": "pkg-target",
                    "package_revision": "rev-target",
                    "graph_id": "graph-target",
                }
            }
        },
    )
    exit_readiness = {
        "gates": {
            "all_bounded_routes_compile": True,
            "shadow_reports_present": True,
            "no_candidate_set_deltas": True,
            "selected_packages_resolved_for_bounded_routes": True,
            "no_blocked_search_plane_a_rows": True,
        },
        "target_profile_promotion": {
            "summary": {
                "candidate_primary_ready": True,
                "primary_ready": True,
            },
            "authority_control_readiness": {
                "summary": {
                    "bootstrap_applied": True,
                },
                "authority_control_bootstrap": {
                    "schema_version": "canon_authority_control_bootstrap_bundle_v1",
                    "summary": {
                        "candidate_primary_bootstrap_ready": True,
                        "primary_bootstrap_ready": True,
                    },
                    "profile": {"id": "planetscale_opensearch_v1"},
                    "mode": "shadow",
                    "routes": ["search_bm25.document_chunk"],
                },
            },
        },
        "summary": {"ready_for_phase1b": True},
    }

    candidate_plan = build_publish_plan(
        CanonPublishRequest(
            target=candidate_pointer,
            current=shadow_pointer,
            review=CanonPublishReview(
                branch_name="canonpp-tranche2a",
                reviewed=True,
                ci_green=True,
                shadow_evidence_present=True,
            ),
            exit_readiness=exit_readiness,
        )
    )
    apply_publish_plan(
        plan=candidate_plan,
        registry_path=registry_path,
        authority_control_registry_path=authority_control_registry_path,
        route_serving_registry_path=route_serving_registry_path,
    )

    primary_plan = build_publish_plan(
        CanonPublishRequest(
            target=primary_pointer,
            current=candidate_pointer,
            review=CanonPublishReview(
                branch_name="canonpp-tranche2a",
                reviewed=True,
                ci_green=True,
                shadow_evidence_present=True,
            ),
            exit_readiness=exit_readiness,
        )
    )
    apply_publish_plan(
        plan=primary_plan,
        registry_path=registry_path,
        authority_control_registry_path=authority_control_registry_path,
        route_serving_registry_path=route_serving_registry_path,
    )
    primary_state = build_route_slice_state(
        registry=load_route_serving_registry(route_serving_registry_path),
        profile_id="planetscale_opensearch_v1",
        route_id="search_bm25.document_chunk",
    )
    assert primary_state["state"] == "primary_active"
    assert primary_state["rollback_ready"] is True
    assert primary_state["activation"]["rollback_target_pointer_id"] == "ptr-target-candidate"

    reverted = apply_revert_plan(
        revert_plan=primary_plan["revert_plan"],
        pointer=candidate_pointer.model_dump(),
        registry_path=registry_path,
        route_serving_registry_path=route_serving_registry_path,
    )
    assert reverted["candidate_primary_pointer"]["pointer_id"] == "ptr-target-candidate"

    reverted_state = build_route_slice_state(
        registry=load_route_serving_registry(route_serving_registry_path),
        profile_id="planetscale_opensearch_v1",
        route_id="search_bm25.document_chunk",
    )
    assert reverted_state["state"] == "candidate_primary_active"
    assert reverted_state["activation"]["predecessor_pointer_id"] == "ptr-target-primary"

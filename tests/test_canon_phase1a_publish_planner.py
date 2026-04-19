from __future__ import annotations

from QueryLake.canon.control import (
    CanonPublishPointer,
    CanonPublishRequest,
    CanonPublishReview,
    build_publish_plan,
)


def _exit_readiness(*, ready_for_phase1b: bool, candidate_ready: bool = True) -> dict:
    return {
        "gates": {
            "all_bounded_routes_compile": True,
            "shadow_reports_present": True,
            "no_candidate_set_deltas": candidate_ready,
            "declared_routes_runtime_ready": ready_for_phase1b,
        },
        "summary": {
            "ready_for_phase1b": ready_for_phase1b,
        },
    }


def test_publish_plan_allows_shadow_publish_without_primary_gate():
    payload = build_publish_plan(
        CanonPublishRequest(
            target=CanonPublishPointer(
                pointer_id="ptr-shadow-2",
                graph_id="graph-2",
                package_revision="r2",
                profile_id="aws_aurora_pg_opensearch_v1",
                route_ids=["search_bm25.document_chunk"],
                mode="shadow",
            ),
            current=CanonPublishPointer(
                pointer_id="ptr-shadow-1",
                graph_id="graph-1",
                package_revision="r1",
                profile_id="aws_aurora_pg_opensearch_v1",
                route_ids=["search_bm25.document_chunk"],
                mode="shadow",
            ),
            review=CanonPublishReview(
                branch_name="canonpp-phase1a",
                reviewed=True,
                ci_green=True,
                shadow_evidence_present=True,
            ),
            exit_readiness=_exit_readiness(ready_for_phase1b=False, candidate_ready=False),
        )
    )

    assert payload["allowed"] is True
    assert payload["mode_transition"] == "shadow->shadow"
    assert payload["revert_plan"]["available"] is True


def test_publish_plan_blocks_candidate_primary_without_candidate_gate():
    payload = build_publish_plan(
        CanonPublishRequest(
            target=CanonPublishPointer(
                pointer_id="ptr-candidate-1",
                graph_id="graph-2",
                package_revision="r2",
                profile_id="aws_aurora_pg_opensearch_v1",
                route_ids=["search_bm25.document_chunk"],
                mode="candidate_primary",
            ),
            review=CanonPublishReview(
                branch_name="canonpp-phase1a",
                reviewed=True,
                ci_green=True,
                shadow_evidence_present=True,
            ),
            exit_readiness=_exit_readiness(ready_for_phase1b=False, candidate_ready=False),
        )
    )

    assert payload["allowed"] is False
    assert "candidate_primary_gate_not_satisfied" in payload["blockers"]


def test_publish_plan_blocks_candidate_primary_when_search_plane_a_rows_are_blocked():
    payload = build_publish_plan(
        CanonPublishRequest(
            target=CanonPublishPointer(
                pointer_id="ptr-candidate-2",
                graph_id="graph-2",
                package_revision="r2",
                profile_id="aws_aurora_pg_opensearch_v1",
                route_ids=["search_bm25.document_chunk", "search_hybrid.document_chunk"],
                mode="candidate_primary",
            ),
            review=CanonPublishReview(
                branch_name="canonpp-phase1a",
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
                    "no_blocked_search_plane_a_rows": False,
                },
                "summary": {"ready_for_phase1b": False},
            },
        )
    )

    assert payload["allowed"] is False
    assert "candidate_primary_gate_not_satisfied" in payload["blockers"]


def test_publish_plan_blocks_candidate_primary_when_target_profile_promotion_gate_is_not_ready():
    payload = build_publish_plan(
        CanonPublishRequest(
            target=CanonPublishPointer(
                pointer_id="ptr-candidate-3",
                graph_id="graph-2",
                package_revision="r2",
                profile_id="planetscale_opensearch_v1",
                route_ids=["search_bm25.document_chunk", "search_hybrid.document_chunk"],
                mode="candidate_primary",
            ),
            review=CanonPublishReview(
                branch_name="canonpp-phase1a",
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
                        "candidate_primary_ready": False,
                        "primary_ready": False,
                    }
                },
                "summary": {"ready_for_phase1b": False},
            },
        )
    )

    assert payload["allowed"] is False
    assert "candidate_primary_gate_not_satisfied" in payload["blockers"]


def test_publish_plan_blocks_primary_without_exit_gate():
    payload = build_publish_plan(
        CanonPublishRequest(
            target=CanonPublishPointer(
                pointer_id="ptr-primary-1",
                graph_id="graph-3",
                package_revision="r3",
                profile_id="aws_aurora_pg_opensearch_v1",
                route_ids=["search_bm25.document_chunk", "search_file_chunks"],
                mode="primary",
            ),
            current=CanonPublishPointer(
                pointer_id="ptr-candidate-1",
                graph_id="graph-2",
                package_revision="r2",
                profile_id="aws_aurora_pg_opensearch_v1",
                route_ids=["search_bm25.document_chunk", "search_file_chunks"],
                mode="candidate_primary",
            ),
            review=CanonPublishReview(
                branch_name="canonpp-phase1a",
                reviewed=True,
                ci_green=True,
                shadow_evidence_present=True,
            ),
            exit_readiness=_exit_readiness(ready_for_phase1b=False, candidate_ready=True),
        )
    )

    assert payload["allowed"] is False
    assert "primary_gate_not_satisfied" in payload["blockers"]
    assert payload["revert_plan"]["revert_to_pointer_id"] == "ptr-candidate-1"


def test_publish_plan_allows_primary_when_exit_gate_satisfied():
    payload = build_publish_plan(
        CanonPublishRequest(
            target=CanonPublishPointer(
                pointer_id="ptr-primary-2",
                graph_id="graph-4",
                package_revision="r4",
                profile_id="aws_aurora_pg_opensearch_v1",
                route_ids=["search_bm25.document_chunk", "search_file_chunks", "search_hybrid.document_chunk"],
                mode="primary",
                metadata={
                    "package_bindings": {
                        "search_bm25.document_chunk": {
                            "package_id": "pkg-bm25",
                            "package_revision": "r4",
                            "graph_id": "graph-4a",
                        },
                        "search_file_chunks": {
                            "package_id": "pkg-file",
                            "package_revision": "r4",
                            "graph_id": "graph-4b",
                        },
                        "search_hybrid.document_chunk": {
                            "package_id": "pkg-hybrid",
                            "package_revision": "r4",
                            "graph_id": "graph-4c",
                        },
                    }
                },
            ),
            current=CanonPublishPointer(
                pointer_id="ptr-shadow-1",
                graph_id="graph-1",
                package_revision="r1",
                profile_id="aws_aurora_pg_opensearch_v1",
                route_ids=["search_bm25.document_chunk"],
                mode="shadow",
            ),
            review=CanonPublishReview(
                branch_name="canonpp-phase1a",
                reviewed=True,
                ci_green=True,
                shadow_evidence_present=True,
            ),
            exit_readiness=_exit_readiness(ready_for_phase1b=True, candidate_ready=True),
        )
    )

    assert payload["allowed"] is True
    assert payload["mode_transition"] == "shadow->primary"
    assert any(step["step_id"] == "cutover_primary_pointer" for step in payload["steps"])
    assert "forward_mode_transition" in payload["recommendations"]


def test_publish_plan_blocks_multiroute_promotion_without_route_bindings():
    payload = build_publish_plan(
        CanonPublishRequest(
            target=CanonPublishPointer(
                pointer_id="ptr-primary-3",
                graph_id="graph-5",
                package_revision="r5",
                profile_id="aws_aurora_pg_opensearch_v1",
                route_ids=["search_bm25.document_chunk", "search_file_chunks"],
                mode="candidate_primary",
            ),
            review=CanonPublishReview(
                branch_name="canonpp-phase1a",
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
                "summary": {"ready_for_phase1b": False},
            },
        )
    )

    assert payload["allowed"] is False
    assert "multiroute_package_bindings_incomplete" in payload["blockers"]

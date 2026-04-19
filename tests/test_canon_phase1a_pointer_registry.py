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

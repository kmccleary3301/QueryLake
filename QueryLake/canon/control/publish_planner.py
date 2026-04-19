from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from QueryLake.canon.control.models import (
    CanonPublishPointer,
    CanonPublishRequest,
    CanonPublishRevertPlan,
    CanonPublishStep,
)


_MODE_RANK = {
    "shadow": 0,
    "candidate_primary": 1,
    "primary": 2,
}


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _readiness_gates(exit_readiness: dict[str, Any]) -> dict[str, bool]:
    return {
        str(key): bool(value)
        for key, value in dict(exit_readiness.get("gates") or {}).items()
    }


def _candidate_primary_ready(exit_readiness: dict[str, Any]) -> bool:
    gates = _readiness_gates(exit_readiness)
    return bool(
        gates.get("all_bounded_routes_compile")
        and gates.get("shadow_reports_present")
        and gates.get("no_candidate_set_deltas")
    )


def _primary_ready(exit_readiness: dict[str, Any]) -> bool:
    return bool(dict(exit_readiness.get("summary") or {}).get("ready_for_phase1b"))


def _build_revert_plan(current: CanonPublishPointer | None) -> CanonPublishRevertPlan:
    if current is None:
        return CanonPublishRevertPlan(
            available=False,
            notes=["No existing pointer to revert to."],
        )
    return CanonPublishRevertPlan(
        available=True,
        revert_to_pointer_id=current.pointer_id,
        revert_mode=current.mode,
        steps=[
            CanonPublishStep(
                step_id="repoint_active_pointer",
                action="update_active_pointer",
                metadata={
                    "pointer_id": current.pointer_id,
                    "mode": current.mode,
                },
            )
        ],
        notes=["Prefer pointer reversal before emergency code changes."],
    )


def build_publish_plan(request: CanonPublishRequest) -> dict[str, Any]:
    target = request.target
    current = request.current
    review = request.review
    blockers: list[str] = []
    recommendations: list[str] = []
    steps: list[CanonPublishStep] = []

    if not review.reviewed:
        blockers.append("branch_review_missing")
    if not review.ci_green:
        blockers.append("ci_not_green")
    if not review.shadow_evidence_present:
        blockers.append("shadow_evidence_missing")

    target_rank = _MODE_RANK[target.mode]
    current_rank = _MODE_RANK[current.mode] if current is not None else -1
    mode_transition = f"{current.mode if current is not None else 'none'}->{target.mode}"

    if target.mode == "candidate_primary" and not _candidate_primary_ready(request.exit_readiness):
        blockers.append("candidate_primary_gate_not_satisfied")
    if target.mode == "primary" and not _primary_ready(request.exit_readiness):
        blockers.append("primary_gate_not_satisfied")

    if current is not None and current.pointer_id == target.pointer_id and current.mode == target.mode:
        recommendations.append("target_pointer_already_active")

    steps.append(
        CanonPublishStep(
            step_id="publish_graph_package",
            action="publish_graph_package",
            metadata={
                "graph_id": target.graph_id,
                "package_revision": target.package_revision,
            },
        )
    )
    if target.mode == "shadow":
        steps.append(
            CanonPublishStep(
                step_id="update_shadow_pointer",
                action="update_shadow_pointer",
                metadata={
                    "pointer_id": target.pointer_id,
                    "profile_id": target.profile_id,
                    "route_ids": list(target.route_ids),
                },
            )
        )
    elif target.mode == "candidate_primary":
        steps.extend(
            [
                CanonPublishStep(
                    step_id="update_shadow_pointer",
                    action="update_shadow_pointer",
                    metadata={"pointer_id": target.pointer_id},
                ),
                CanonPublishStep(
                    step_id="promote_candidate_pointer",
                    action="update_candidate_primary_pointer",
                    metadata={"pointer_id": target.pointer_id},
                ),
            ]
        )
    else:
        steps.extend(
            [
                CanonPublishStep(
                    step_id="update_shadow_pointer",
                    action="update_shadow_pointer",
                    metadata={"pointer_id": target.pointer_id},
                ),
                CanonPublishStep(
                    step_id="promote_candidate_pointer",
                    action="update_candidate_primary_pointer",
                    metadata={"pointer_id": target.pointer_id},
                ),
                CanonPublishStep(
                    step_id="cutover_primary_pointer",
                    action="update_primary_pointer",
                    metadata={"pointer_id": target.pointer_id},
                ),
            ]
        )

    if target_rank > current_rank:
        recommendations.append("forward_mode_transition")
    if current is not None and target.profile_id != current.profile_id:
        recommendations.append("profile_cutover_requires_heightened_review")

    allowed = len(blockers) == 0
    return {
        "schema_version": "canon_publish_plan_v1",
        "generated_at": _utc_now(),
        "target": target.model_dump(),
        "current": current.model_dump() if current is not None else None,
        "review": review.model_dump(),
        "mode_transition": mode_transition,
        "allowed": allowed,
        "blockers": blockers,
        "recommendations": recommendations,
        "steps": [step.model_dump() for step in steps],
        "revert_plan": _build_revert_plan(current).model_dump(),
    }

from __future__ import annotations

from typing import Any

from QueryLake.canon.control.route_serving_registry import (
    build_route_slice_state,
    load_route_serving_registry,
)
from QueryLake.canon.runtime.search_plane_a_execution import build_search_plane_a_execution_contract
from QueryLake.runtime.db_compat import get_deployment_profile


def _route_slice_support_state(*, route_state: str, authoritative: bool, primary_ready: bool) -> str:
    if route_state == "primary_active" and authoritative and primary_ready:
        return "route_slice_supported"
    if route_state == "candidate_primary_active" and authoritative:
        return "route_slice_candidate"
    if route_state == "primary_eligible":
        return "route_slice_primary_eligible"
    if route_state == "candidate_primary_eligible":
        return "route_slice_candidate_eligible"
    return "route_slice_shadow"


def build_route_slice_support_alignment(
    *,
    route_id: str,
    profile_id: str,
    package_registry_path: str,
    pointer_registry_path: str,
    route_serving_registry_path: str,
    mode: str = "primary",
) -> dict[str, Any]:
    profile = get_deployment_profile(profile_id)
    route_serving_registry = load_route_serving_registry(route_serving_registry_path)
    route_state = build_route_slice_state(
        registry=route_serving_registry,
        profile_id=profile.id,
        route_id=route_id,
    )
    execution_contract = build_search_plane_a_execution_contract(
        route_id=route_id,
        profile_id=profile.id,
        package_registry_path=package_registry_path,
        pointer_registry_path=pointer_registry_path,
        route_serving_registry_path=route_serving_registry_path,
        mode=mode,
    )
    runtime_support_state = _route_slice_support_state(
        route_state=str(route_state.get("state") or ""),
        authoritative=bool(execution_contract.get("authoritative")),
        primary_ready=bool(execution_contract.get("primary_ready")),
    )
    blockers: list[str] = []
    if runtime_support_state != "route_slice_supported":
        blockers.append("route_slice_not_primary_supported")
    if str(profile.maturity) == "planned":
        blockers.append("profile_global_support_state_remains_planned")
    return {
        "schema_version": "canon_route_slice_support_alignment_v1",
        "route_id": route_id,
        "profile_id": profile.id,
        "profile_global_maturity": profile.maturity,
        "route_state": route_state,
        "execution_contract": execution_contract,
        "runtime_support_state": runtime_support_state,
        "route_slice_supported": runtime_support_state == "route_slice_supported",
        "global_profile_supported": False,
        "support_claim_scope": "route_slice_only",
        "blockers": blockers,
        "notes": [
            "This payload aligns Tranche 2A support wording to a single route slice.",
            "It must not be interpreted as full-profile support for planetscale_opensearch_v1.",
        ],
    }

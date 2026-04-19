from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Iterable

from QueryLake.canon.package.registry import load_graph_package_registry, resolve_selected_graph_package
from QueryLake.canon.control.pointer_registry import load_pointer_registry
from QueryLake.canon.runtime.search_plane_a_execution import build_search_plane_a_execution_contract
from QueryLake.runtime.db_compat import (
    build_profile_configuration_payload,
    build_profile_execution_target_payload,
    build_profile_route_support_matrix,
    get_deployment_profile,
)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def build_authority_control_readiness_bundle(
    *,
    profile_id: str,
    routes: Iterable[str],
    package_registry_path: str,
    pointer_registry_path: str,
    mode: str = "shadow",
) -> dict[str, Any]:
    effective_profile = get_deployment_profile(profile_id)
    route_list = [str(route) for route in routes]
    config = build_profile_configuration_payload(effective_profile)
    route_support = build_profile_route_support_matrix(effective_profile)
    package_registry = load_graph_package_registry(package_registry_path)
    pointer_registry = load_pointer_registry(pointer_registry_path)

    route_rows: list[dict[str, Any]] = []
    unresolved_packages = 0
    shadow_executable = 0
    authority_blocked = 0
    control_blocked = 0

    for route_id in route_list:
        selected_package = resolve_selected_graph_package(
            registry=package_registry,
            pointer_registry=pointer_registry,
            route_id=route_id,
            profile_id=effective_profile.id,
            mode=mode,
        )
        execution_contract = build_search_plane_a_execution_contract(
            route_id=route_id,
            profile_id=effective_profile.id,
            package_registry_path=package_registry_path,
            pointer_registry_path=pointer_registry_path,
            mode=mode,
        )
        authority_blockers = list(execution_contract.get("authority_blockers") or [])
        search_plane_blockers = list(execution_contract.get("search_plane_blockers") or [])
        route_row = {
            "route_id": route_id,
            "declared_route_support": dict(route_support.get(route_id) or {}),
            "selected_package_resolved": bool(selected_package.get("resolved")),
            "shadow_executable": bool(execution_contract.get("shadow_executable")),
            "primary_ready": bool(execution_contract.get("primary_ready")),
            "authority_blockers": authority_blockers,
            "search_plane_blockers": search_plane_blockers,
            "execution_mode": str(execution_contract.get("execution_mode") or ""),
            "executor_id": str(execution_contract.get("executor_id") or ""),
        }
        route_rows.append(route_row)
        if not route_row["selected_package_resolved"]:
            unresolved_packages += 1
        if route_row["shadow_executable"]:
            shadow_executable += 1
        if "authority_plane_not_migrated" in authority_blockers:
            authority_blocked += 1
        if "control_plane_not_migrated" in authority_blockers:
            control_blocked += 1

    recommendations: list[str] = []
    if not bool(config.get("ready")):
        recommendations.append("complete_required_target_profile_configuration")
    if unresolved_packages > 0:
        recommendations.append("resolve_target_profile_package_bindings_for_all_bounded_routes")
    if shadow_executable == len(route_rows) and route_rows:
        recommendations.append("target_profile_search_plane_shadow_execution_covers_bounded_routes")
    if authority_blocked > 0:
        recommendations.append("authority_plane_migration_remains_blocking")
    if control_blocked > 0:
        recommendations.append("control_plane_migration_remains_blocking")

    candidate_primary_ready = bool(config.get("ready")) and unresolved_packages == 0 and shadow_executable == len(route_rows)
    primary_ready = candidate_primary_ready and authority_blocked == 0 and control_blocked == 0 and bool(
        effective_profile.implemented
    )

    return {
        "schema_version": "canon_authority_control_readiness_bundle_v1",
        "generated_at": _utc_now(),
        "profile": {
            "id": effective_profile.id,
            "label": effective_profile.label,
            "implemented": bool(effective_profile.implemented),
        },
        "profile_execution_target": build_profile_execution_target_payload(effective_profile),
        "configuration": config,
        "mode": str(mode),
        "routes": route_list,
        "route_rows": route_rows,
        "summary": {
            "route_count": len(route_rows),
            "selected_package_resolved_count": len(route_rows) - unresolved_packages,
            "shadow_executable_count": shadow_executable,
            "authority_blocked_count": authority_blocked,
            "control_blocked_count": control_blocked,
            "candidate_primary_ready": candidate_primary_ready,
            "primary_ready": primary_ready,
        },
        "recommendations": recommendations,
    }

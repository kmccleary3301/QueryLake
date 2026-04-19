from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Iterable, Optional

from QueryLake.canon.control.pointer_registry import load_pointer_registry
from QueryLake.canon.package.registry import load_graph_package_registry, resolve_selected_graph_package
from QueryLake.canon.runtime.bootstrap_bundle import build_phase1a_bootstrap_bundle
from QueryLake.canon.runtime.search_plane_a_execution import build_search_plane_a_execution_contract
from QueryLake.runtime.db_compat import build_profile_configuration_payload, get_deployment_profile


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def build_authority_control_bootstrap_bundle(
    *,
    profile_id: str,
    routes: Iterable[str],
    package_registry_path: str,
    pointer_registry_path: str,
    metadata_store_path: Optional[str] = None,
    mode: str = "shadow",
    execute_bootstrap: bool = False,
    database: Any = None,
    request_metadata: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    effective_profile = get_deployment_profile(profile_id)
    route_list = [str(route_id) for route_id in routes if str(route_id or "")]
    package_registry = load_graph_package_registry(package_registry_path)
    pointer_registry = load_pointer_registry(pointer_registry_path)
    profile_configuration = build_profile_configuration_payload(effective_profile)
    route_rows: list[dict[str, Any]] = []
    unresolved_packages = 0
    shadow_executable_count = 0
    route_bindings: dict[str, Any] = {}

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
        selected_package_resolved = bool(selected_package.get("resolved"))
        if not selected_package_resolved:
            unresolved_packages += 1
        if bool(execution_contract.get("shadow_executable")):
            shadow_executable_count += 1
        package_payload = dict(selected_package.get("package") or {})
        route_bindings[route_id] = {
            "package_id": str(package_payload.get("package_id") or ""),
            "package_revision": str(package_payload.get("package_revision") or ""),
            "graph_id": str(package_payload.get("graph_id") or ""),
        }
        route_rows.append(
            {
                "route_id": route_id,
                "selected_package_resolved": selected_package_resolved,
                "shadow_executable": bool(execution_contract.get("shadow_executable")),
                "execution_mode": str(execution_contract.get("execution_mode") or ""),
                "executor_id": str(execution_contract.get("executor_id") or ""),
                "search_plane_blockers": list(execution_contract.get("search_plane_blockers") or []),
                "authority_blockers": list(execution_contract.get("authority_blockers") or []),
            }
        )

    phase1a_bootstrap_bundle = build_phase1a_bootstrap_bundle(
        profile_id=effective_profile.id,
        metadata_store_path=metadata_store_path,
        execute=execute_bootstrap,
        database=database,
        request_metadata={
            "canon_phase": "phase1a",
            "target_profile": effective_profile.id,
            **dict(request_metadata or {}),
        },
    )
    bootstrap_summary = dict(phase1a_bootstrap_bundle.get("summary") or {})
    configuration_ready = bool(profile_configuration.get("ready"))
    runtime_ready_after_bootstrap = bool(
        bootstrap_summary.get("declared_executable_routes_runtime_ready_after")
    )
    candidate_primary_bootstrap_ready = bool(
        configuration_ready
        and unresolved_packages == 0
        and shadow_executable_count == len(route_rows)
        and runtime_ready_after_bootstrap
    )
    blockers: list[str] = []
    if not configuration_ready:
        blockers.append("target_profile_configuration_not_ready")
    if unresolved_packages > 0:
        blockers.append("bounded_route_packages_unresolved")
    if shadow_executable_count != len(route_rows):
        blockers.append("bounded_routes_not_shadow_executable")
    if not runtime_ready_after_bootstrap:
        blockers.append("target_profile_runtime_not_ready_after_bootstrap")

    recommendations: list[str] = []
    if candidate_primary_bootstrap_ready:
        recommendations.append("authority_control_bootstrap_ready_for_candidate_primary_apply")
    else:
        if not configuration_ready:
            recommendations.append("complete_target_profile_configuration_before_bootstrap_apply")
        if unresolved_packages > 0:
            recommendations.append("resolve_route_level_package_bindings_before_bootstrap_apply")
        if shadow_executable_count != len(route_rows):
            recommendations.append("restore_target_profile_shadow_execution_before_bootstrap_apply")
        if not runtime_ready_after_bootstrap:
            recommendations.append("complete_projection_bootstrap_or_runtime_recovery_before_bootstrap_apply")

    return {
        "schema_version": "canon_authority_control_bootstrap_bundle_v1",
        "generated_at": _utc_now(),
        "profile": {
            "id": effective_profile.id,
            "label": effective_profile.label,
            "implemented": bool(effective_profile.implemented),
        },
        "mode": str(mode),
        "routes": route_list,
        "profile_configuration": profile_configuration,
        "route_rows": route_rows,
        "route_bindings": route_bindings,
        "phase1a_bootstrap_bundle": phase1a_bootstrap_bundle,
        "summary": {
            "route_count": len(route_rows),
            "configuration_ready": configuration_ready,
            "selected_package_resolved_count": len(route_rows) - unresolved_packages,
            "shadow_executable_count": shadow_executable_count,
            "runtime_ready_after_bootstrap": runtime_ready_after_bootstrap,
            "candidate_primary_bootstrap_ready": candidate_primary_bootstrap_ready,
            "primary_bootstrap_ready": False,
        },
        "blockers": blockers,
        "recommendations": recommendations,
    }

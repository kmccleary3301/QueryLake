from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional

from QueryLake.canon.compiler.profile_lowering import build_profile_lowering_snapshot
from QueryLake.canon.runtime.profile_readiness import build_phase1a_search_plane_a_transition_bundle
from QueryLake.runtime.db_compat import (
    build_profile_execution_target_payload,
    build_profile_route_support_matrix,
    get_deployment_profile,
)
from QueryLake.runtime.retrieval_pipeline_runtime import default_pipeline_for_route


_ROUTE_TO_DEFAULT_PIPELINE_ROUTE = {
    "search_hybrid.document_chunk": "search_hybrid",
    "search_bm25.document_chunk": "search_bm25.document_chunk",
    "search_file_chunks": "search_file_chunks",
}


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _normalize_route(route_id: str) -> str:
    return _ROUTE_TO_DEFAULT_PIPELINE_ROUTE.get(str(route_id), str(route_id))


def _execution_mode(
    *,
    package_resolved: bool,
    lowering: dict[str, Any],
    declared_route: dict[str, Any],
    profile_implemented: bool,
) -> tuple[str, list[str], list[str]]:
    blockers: list[str] = []
    recommendations: list[str] = []

    if not package_resolved:
        blockers.append("selected_package_missing")
        recommendations.append("register_and_select_graph_package_before_publish")
    if not bool(declared_route.get("declared_executable", False)):
        blockers.append("route_not_declared_executable_for_profile")
    if not bool(lowering.get("implemented", False)):
        blockers.append("route_executor_not_implemented")
    if not bool(lowering.get("runtime_ready", False)):
        blockers.extend(str(value) for value in list(lowering.get("runtime_blockers") or []))
    if not profile_implemented:
        blockers.append("profile_not_implemented")
        recommendations.append("planned_profiles_remain_shadow_only")

    if blockers:
        if not profile_implemented:
            return "planned_profile_shadow_only", blockers, recommendations
        return "blocked", blockers, recommendations

    recommendations.append("selected_package_can_execute_via_current_profile_route_executor")
    return "legacy_route_executor_passthrough", blockers, recommendations


def build_search_plane_a_lowering_bundle(
    *,
    route_id: str,
    profile_id: str,
    package_registry_path: str | Path,
    pointer_registry_path: str | Path,
    mode: str = "shadow",
) -> dict[str, Any]:
    effective_profile = get_deployment_profile(profile_id)
    from QueryLake.canon.package.registry import load_graph_package_registry, resolve_selected_graph_package
    from QueryLake.canon.control.pointer_registry import load_pointer_registry

    package_registry = load_graph_package_registry(package_registry_path)
    pointer_registry = load_pointer_registry(pointer_registry_path)
    selected_package = resolve_selected_graph_package(
        registry=package_registry,
        pointer_registry=pointer_registry,
        route_id=route_id,
        profile_id=effective_profile.id,
        mode=mode,
    )

    pipeline = default_pipeline_for_route(_normalize_route(route_id))
    package_compile_options = dict(selected_package.get("package", {}).get("compile_options") or {})
    lowering = build_profile_lowering_snapshot(
        route=route_id,
        pipeline=pipeline,
        profile=effective_profile,
        options=package_compile_options,
    )
    declared_route = dict(build_profile_route_support_matrix(effective_profile).get(route_id) or {})
    execution_mode, blockers, recommendations = _execution_mode(
        package_resolved=bool(selected_package.get("resolved")),
        lowering=lowering,
        declared_route=declared_route,
        profile_implemented=bool(effective_profile.implemented),
    )

    payload = {
        "schema_version": "canon_phase1a_search_plane_a_lowering_bundle_v1",
        "generated_at": _utc_now(),
        "route_id": route_id,
        "mode": str(mode),
        "profile": {
            "id": effective_profile.id,
            "label": effective_profile.label,
            "implemented": bool(effective_profile.implemented),
            "maturity": effective_profile.maturity,
        },
        "profile_execution_target": build_profile_execution_target_payload(effective_profile),
        "declared_route_support": declared_route,
        "selected_package": selected_package,
        "lowering": lowering,
        "execution_mode": execution_mode,
        "blockers": blockers,
        "recommendations": recommendations,
    }
    if effective_profile.id == "planetscale_opensearch_v1":
        payload["search_plane_a_transition"] = build_phase1a_search_plane_a_transition_bundle(
            source_profile_id="aws_aurora_pg_opensearch_v1",
            target_profile_id=effective_profile.id,
            routes=[route_id],
        )
    return payload

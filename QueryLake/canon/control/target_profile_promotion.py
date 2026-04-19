from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Iterable, Optional

from QueryLake.canon.runtime.authority_control_readiness import build_authority_control_readiness_bundle
from QueryLake.canon.runtime.exit_readiness import build_phase1a_exit_readiness_bundle


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def build_target_profile_promotion_bundle(
    *,
    target_profile_id: str,
    routes: Iterable[str],
    shadow_artifact_dir: str,
    package_registry_path: str,
    pointer_registry_path: str,
    authority_control_registry_path: str | None = None,
    metadata_store_path: Optional[str] = None,
    package_selection_mode: str = "shadow",
) -> dict[str, Any]:
    route_list = [str(route) for route in routes]
    source_exit = build_phase1a_exit_readiness_bundle(
        profile_id="aws_aurora_pg_opensearch_v1",
        shadow_artifact_dir=shadow_artifact_dir,
        metadata_store_path=metadata_store_path,
        routes=route_list,
        include_target_profile_promotion=False,
        package_registry_path=package_registry_path,
        pointer_registry_path=pointer_registry_path,
        package_selection_mode=package_selection_mode,
    )
    authority_control = build_authority_control_readiness_bundle(
        profile_id=target_profile_id,
        routes=route_list,
        package_registry_path=package_registry_path,
        pointer_registry_path=pointer_registry_path,
        authority_control_registry_path=authority_control_registry_path,
        metadata_store_path=metadata_store_path,
        mode=package_selection_mode,
    )

    source_gates = dict(source_exit.get("gates") or {})
    authority_summary = dict(authority_control.get("summary") or {})
    candidate_primary_ready = bool(
        source_gates.get("all_bounded_routes_compile")
        and source_gates.get("shadow_reports_present")
        and source_gates.get("no_candidate_set_deltas")
        and source_gates.get("selected_packages_resolved_for_bounded_routes", True)
        and bool(authority_summary.get("candidate_primary_ready"))
    )
    primary_ready = bool(
        candidate_primary_ready
        and source_gates.get("declared_routes_runtime_ready")
        and bool(authority_summary.get("primary_ready"))
    )

    blockers: list[str] = []
    if not source_gates.get("shadow_reports_present"):
        blockers.append("source_shadow_reports_missing")
    if not source_gates.get("no_candidate_set_deltas"):
        blockers.append("source_shadow_candidate_set_deltas_present")
    if not source_gates.get("selected_packages_resolved_for_bounded_routes", True):
        blockers.append("bounded_route_packages_unresolved")
    if not bool(authority_summary.get("candidate_primary_ready")):
        blockers.append("target_profile_candidate_gate_not_satisfied")
    if not bool(authority_control.get("configuration", {}).get("ready")):
        blockers.append("target_profile_configuration_not_ready")
    if int(authority_summary.get("authority_blocked_count", 0)) > 0:
        blockers.append("authority_plane_migration_incomplete")
    if int(authority_summary.get("control_blocked_count", 0)) > 0:
        blockers.append("control_plane_migration_incomplete")

    recommendations: list[str] = []
    if candidate_primary_ready:
        recommendations.append("target_profile_can_enter_candidate_primary_after_review")
    else:
        recommendations.extend(list(authority_control.get("recommendations") or []))
        if not source_gates.get("shadow_reports_present"):
            recommendations.append("capture_shadow_reports_for_bounded_routes_before_promotion")
        if not source_gates.get("no_candidate_set_deltas"):
            recommendations.append("resolve_candidate_set_deltas_before_target_profile_promotion")
    if primary_ready:
        recommendations.append("target_profile_primary_gate_satisfied")
    else:
        recommendations.append("target_profile_primary_requires_authority_and_control_migration")

    return {
        "schema_version": "canon_target_profile_promotion_bundle_v1",
        "generated_at": _utc_now(),
        "target_profile_id": str(target_profile_id),
        "routes": route_list,
        "source_exit_readiness": source_exit,
        "authority_control_readiness": authority_control,
        "summary": {
            "bootstrap_ready_to_apply": bool(authority_summary.get("bootstrap_ready_to_apply")),
            "bootstrap_applied": bool(authority_summary.get("bootstrap_applied")),
            "candidate_primary_ready": candidate_primary_ready,
            "primary_ready": primary_ready,
            "blocker_count": len(blockers),
        },
        "blockers": blockers,
        "recommendations": recommendations,
    }

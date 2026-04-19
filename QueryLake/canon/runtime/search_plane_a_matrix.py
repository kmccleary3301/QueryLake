from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Iterable

from QueryLake.canon.runtime.search_plane_a_lowering import build_search_plane_a_lowering_bundle


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def build_search_plane_a_lowering_matrix(
    *,
    routes: Iterable[str],
    profile_ids: Iterable[str],
    package_registry_path: str,
    pointer_registry_path: str,
    mode: str = "shadow",
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    execution_counts: dict[str, int] = {}

    for profile_id in [str(value) for value in profile_ids]:
        for route_id in [str(value) for value in routes]:
            lowering = build_search_plane_a_lowering_bundle(
                route_id=route_id,
                profile_id=profile_id,
                package_registry_path=package_registry_path,
                pointer_registry_path=pointer_registry_path,
                mode=mode,
            )
            execution_mode = str(lowering.get("execution_mode") or "unknown")
            execution_counts[execution_mode] = execution_counts.get(execution_mode, 0) + 1
            rows.append(
                {
                    "route_id": route_id,
                    "profile_id": profile_id,
                    "execution_mode": execution_mode,
                    "selected_package_resolved": bool(lowering.get("selected_package", {}).get("resolved")),
                    "runtime_ready": bool(lowering.get("lowering", {}).get("runtime_ready")),
                    "implemented": bool(lowering.get("lowering", {}).get("implemented")),
                    "blockers": list(lowering.get("blockers") or []),
                }
            )

    recommendations: list[str] = []
    if execution_counts.get("legacy_route_executor_passthrough", 0) > 0:
        recommendations.append("bounded_routes_have_selected_package_backed_execution_on_current_profiles")
    if execution_counts.get("planned_profile_shadow_only", 0) > 0:
        recommendations.append("planned_profiles_remain_shadow_only_until_real_execution_targets_exist")
    if execution_counts.get("blocked", 0) > 0:
        recommendations.append("resolve_blocked_selected_package_or_runtime_paths_before_publish")

    return {
        "schema_version": "canon_phase1a_search_plane_a_lowering_matrix_v1",
        "generated_at": _utc_now(),
        "mode": str(mode),
        "routes": [str(value) for value in routes],
        "profile_ids": [str(value) for value in profile_ids],
        "rows": rows,
        "summary": {
            "row_count": len(rows),
            "execution_mode_counts": execution_counts,
        },
        "recommendations": recommendations,
    }

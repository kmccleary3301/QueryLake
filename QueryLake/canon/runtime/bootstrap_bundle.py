from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Iterable, Optional

from QueryLake.runtime.db_compat import DeploymentProfile, get_deployment_profile
from QueryLake.runtime.profile_bringup import build_profile_bringup_payload
from QueryLake.runtime.projection_refresh import (
    ProjectionRefreshRequest,
    bootstrap_profile_projections,
    default_bootstrap_projection_ids,
    explain_projection_refresh_plan,
)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def build_phase1a_bootstrap_bundle(
    *,
    profile_id: Optional[str] = None,
    projection_ids: Iterable[str] | None = None,
    metadata_store_path: Optional[str] = None,
    execute: bool = False,
    database: Any = None,
    request_metadata: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    effective_profile: DeploymentProfile = get_deployment_profile(profile_id) if profile_id else get_deployment_profile()
    effective_projection_ids = list(
        str(value)
        for value in (
            projection_ids
            if projection_ids is not None
            else default_bootstrap_projection_ids(profile=effective_profile)
        )
    )

    before = build_profile_bringup_payload(
        profile=effective_profile,
        metadata_store_path=metadata_store_path,
    )
    planned_projection_refreshes = [
        explain_projection_refresh_plan(
            ProjectionRefreshRequest(
                projection_id=projection_id,
                projection_version="v1",
                metadata={
                    "canon_phase": "phase1a",
                    **dict(request_metadata or {}),
                },
            ),
            profile=effective_profile,
            metadata_store_path=metadata_store_path,
        ).model_dump()
        for projection_id in effective_projection_ids
    ]

    bootstrap_report = None
    if execute:
        bootstrap_report = bootstrap_profile_projections(
            database=database,
            profile=effective_profile,
            projection_ids=effective_projection_ids,
            metadata_store_path=metadata_store_path,
            request_metadata={
                "canon_phase": "phase1a",
                **dict(request_metadata or {}),
            },
        ).model_dump()

    after = build_profile_bringup_payload(
        profile=effective_profile,
        metadata_store_path=metadata_store_path,
    )

    before_summary = dict(before.get("summary") or {})
    after_summary = dict(after.get("summary") or {})
    recommendations: list[str] = []
    if not execute:
        recommendations.append("bootstrap_bundle_plans_refresh_without_mutation")
    elif bool(after_summary.get("ready_projection_count", 0) > before_summary.get("ready_projection_count", 0)):
        recommendations.append("bootstrap_bundle_increased_ready_projection_count")
    if bool(after_summary.get("declared_executable_routes_runtime_ready")):
        recommendations.append("profile_runtime_ready_after_bootstrap")
    elif execute:
        recommendations.append("additional_projection_bootstrap_or_runtime_work_required")

    return {
        "schema_version": "canon_phase1a_bootstrap_bundle_v1",
        "generated_at": _utc_now(),
        "profile": {
            "id": effective_profile.id,
            "label": effective_profile.label,
            "implemented": bool(effective_profile.implemented),
        },
        "projection_ids": effective_projection_ids,
        "execute": bool(execute),
        "before": before,
        "planned_projection_refreshes": planned_projection_refreshes,
        "bootstrap_report": bootstrap_report,
        "after": after,
        "summary": {
            "planned_projection_count": len(planned_projection_refreshes),
            "ready_projection_count_before": int(before_summary.get("ready_projection_count", 0)),
            "ready_projection_count_after": int(after_summary.get("ready_projection_count", 0)),
            "declared_executable_routes_runtime_ready_before": bool(
                before_summary.get("declared_executable_routes_runtime_ready")
            ),
            "declared_executable_routes_runtime_ready_after": bool(
                after_summary.get("declared_executable_routes_runtime_ready")
            ),
        },
        "recommendations": recommendations,
    }

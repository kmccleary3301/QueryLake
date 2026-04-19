from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any, Iterable, Optional

from QueryLake.runtime.db_compat import get_deployment_profile
from QueryLake.runtime.projection_refresh import (
    ProjectionRefreshRequest,
    default_bootstrap_projection_ids,
    explain_projection_refresh_plan,
)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def build_phase1a_materialization_bundle(
    *,
    profile_id: str = "aws_aurora_pg_opensearch_v1",
    projection_ids: Iterable[str] | None = None,
    metadata_store_path: Optional[str] = None,
) -> dict[str, Any]:
    profile = get_deployment_profile(profile_id)
    effective_projection_ids = list(
        str(value)
        for value in (
            projection_ids if projection_ids is not None else default_bootstrap_projection_ids(profile=profile)
        )
    )
    plans = [
        explain_projection_refresh_plan(
            ProjectionRefreshRequest(
                projection_id=projection_id,
                projection_version="v1",
                metadata={"canon_phase": "phase1a", "execution_mode": "materialization_bundle"},
            ),
            profile=profile,
            metadata_store_path=metadata_store_path,
        ).model_dump()
        for projection_id in effective_projection_ids
    ]
    rebuild_count = sum(
        1
        for plan in plans
        if any(str(action.get("mode") or "") == "rebuild" for action in list(plan.get("actions") or []))
    )
    planned_count = sum(
        1
        for plan in plans
        if any(str(action.get("mode") or "") == "planned" for action in list(plan.get("actions") or []))
    )
    return {
        "schema_version": "canon_phase1a_materialization_bundle_v1",
        "generated_at": _utc_now(),
        "profile": {
            "id": profile.id,
            "label": profile.label,
        },
        "projection_ids": effective_projection_ids,
        "plans": plans,
        "summary": {
            "plan_count": len(plans),
            "rebuild_plan_count": rebuild_count,
            "planned_only_count": planned_count,
        },
        "recommendations": (
            ["materialization_bundle_ready_for_bootstrap_execution"]
            if rebuild_count > 0
            else ["materialization_bundle_has_no_rebuildable_targets"]
        ),
    }


def persist_phase1a_materialization_bundle(
    *,
    bundle: dict[str, Any],
    output_path: str | Path,
) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(path)

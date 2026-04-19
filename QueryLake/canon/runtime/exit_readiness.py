from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Optional

from QueryLake.canon.runtime.profile_readiness import (
    build_phase1a_profile_readiness_bundle,
    build_phase1a_search_plane_a_transition_bundle,
)
from QueryLake.canon.runtime.shadow_catalog import build_shadow_artifact_catalog, load_shadow_artifacts
from QueryLake.canon.runtime.shadow_index import build_shadow_report_index, load_shadow_reports


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def build_phase1a_exit_readiness_bundle(
    *,
    profile_id: str = "aws_aurora_pg_opensearch_v1",
    shadow_artifact_dir: str | Path,
    metadata_store_path: Optional[str] = None,
    routes: Iterable[str] | None = None,
    include_search_plane_transition: bool = True,
) -> dict[str, Any]:
    artifact_dir = Path(shadow_artifact_dir)
    profile_bundle = build_phase1a_profile_readiness_bundle(
        profile_id=profile_id,
        routes=routes,
        metadata_store_path=metadata_store_path,
    )
    reports = load_shadow_reports(artifact_dir)
    report_index = build_shadow_report_index(reports)
    artifacts = load_shadow_artifacts(artifact_dir)
    artifact_catalog = build_shadow_artifact_catalog(artifacts)

    route_count = int(profile_bundle.get("summary", {}).get("route_count", 0))
    compile_available_count = int(profile_bundle.get("summary", {}).get("compile_available_count", 0))
    runtime_ready = bool(profile_bundle.get("summary", {}).get("declared_executable_routes_runtime_ready"))
    report_count = int(report_index.get("report_count", 0))
    candidate_set_deltas = int(report_index.get("divergence_counts", {}).get("candidate_set_delta", 0))
    analysis_incomplete = int(report_index.get("divergence_counts", {}).get("analysis_incomplete", 0))
    orphan_count = len(list(artifact_catalog.get("orphan_correlation_keys") or []))

    gates = {
        "all_bounded_routes_compile": route_count > 0 and compile_available_count == route_count,
        "declared_routes_runtime_ready": runtime_ready,
        "shadow_reports_present": report_count >= route_count if route_count > 0 else False,
        "no_candidate_set_deltas": candidate_set_deltas == 0,
        "no_analysis_incomplete_reports": analysis_incomplete == 0,
        "shadow_artifacts_correlated": orphan_count == 0,
    }
    ready_for_phase1b = all(gates.values())

    recommendations: list[str] = []
    if ready_for_phase1b:
        recommendations.append("phase1a_exit_gate_satisfied")
    else:
        if not gates["declared_routes_runtime_ready"]:
            recommendations.append("complete_profile_runtime_readiness_before_canon_primary")
        if not gates["shadow_reports_present"]:
            recommendations.append("capture_shadow_evidence_for_each_bounded_route")
        if not gates["no_candidate_set_deltas"]:
            recommendations.append("resolve_shadow_candidate_set_deltas_before_broadening_scope")
        if not gates["shadow_artifacts_correlated"]:
            recommendations.append("repair_missing_shadow_artifacts_before_exit")
        if not gates["all_bounded_routes_compile"]:
            recommendations.append("finish_route_compile_coverage_before_exit")

    payload = {
        "schema_version": "canon_phase1a_exit_readiness_bundle_v1",
        "generated_at": _utc_now(),
        "profile_id": profile_id,
        "shadow_artifact_dir": str(artifact_dir),
        "profile_readiness": profile_bundle,
        "shadow_report_index": report_index,
        "shadow_artifact_catalog": artifact_catalog,
        "gates": gates,
        "summary": {
            "route_count": route_count,
            "report_count": report_count,
            "candidate_set_delta_count": candidate_set_deltas,
            "analysis_incomplete_count": analysis_incomplete,
            "orphan_artifact_count": orphan_count,
            "ready_for_phase1b": ready_for_phase1b,
        },
        "recommendations": recommendations,
    }
    if include_search_plane_transition:
        payload["search_plane_a_transition"] = build_phase1a_search_plane_a_transition_bundle(
            source_profile_id=profile_id,
            target_profile_id="planetscale_opensearch_v1",
            routes=routes,
            source_metadata_store_path=metadata_store_path,
        )
    return payload

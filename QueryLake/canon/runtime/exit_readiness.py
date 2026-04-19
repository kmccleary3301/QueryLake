from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Optional

from QueryLake.canon.runtime.profile_readiness import (
    build_phase1a_profile_readiness_bundle,
    build_phase1a_search_plane_a_transition_bundle,
)
from QueryLake.canon.runtime.search_plane_a_matrix import build_search_plane_a_lowering_matrix
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
    include_target_profile_promotion: bool = True,
    package_registry_path: str | None = None,
    pointer_registry_path: str | None = None,
    authority_control_registry_path: str | None = None,
    package_selection_mode: str = "shadow",
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
    lowering_matrix = None
    target_lowering_matrix = None
    target_profile_promotion = None
    if package_registry_path and pointer_registry_path:
        lowering_matrix = build_search_plane_a_lowering_matrix(
            routes=profile_bundle.get("routes") or [],
            profile_ids=[profile_id],
            package_registry_path=package_registry_path,
            pointer_registry_path=pointer_registry_path,
            mode=package_selection_mode,
        )
        rows = list(lowering_matrix.get("rows") or [])
        gates["selected_packages_resolved_for_bounded_routes"] = all(
            bool(row.get("selected_package_resolved")) for row in rows
        )
        gates["no_blocked_search_plane_a_rows"] = not any(
            str(row.get("execution_mode") or "") == "blocked"
            for row in rows
        )
        if profile_id == "aws_aurora_pg_opensearch_v1":
            from QueryLake.canon.control.target_profile_promotion import build_target_profile_promotion_bundle

            target_lowering_matrix = build_search_plane_a_lowering_matrix(
                routes=profile_bundle.get("routes") or [],
                profile_ids=["planetscale_opensearch_v1"],
                package_registry_path=package_registry_path,
                pointer_registry_path=pointer_registry_path,
                mode=package_selection_mode,
            )
            if include_target_profile_promotion:
                target_profile_promotion = build_target_profile_promotion_bundle(
                    target_profile_id="planetscale_opensearch_v1",
                    routes=profile_bundle.get("routes") or [],
                    shadow_artifact_dir=str(artifact_dir),
                    package_registry_path=package_registry_path,
                    pointer_registry_path=pointer_registry_path,
                    authority_control_registry_path=authority_control_registry_path,
                    metadata_store_path=metadata_store_path,
                    package_selection_mode=package_selection_mode,
                )
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
        if "selected_packages_resolved_for_bounded_routes" in gates and not gates["selected_packages_resolved_for_bounded_routes"]:
            recommendations.append("register_and_select_graph_packages_for_each_bounded_route_before_exit")
        if "no_blocked_search_plane_a_rows" in gates and not gates["no_blocked_search_plane_a_rows"]:
            recommendations.append("resolve_blocked_search_plane_a_rows_before_candidate_primary")
    if target_lowering_matrix is not None:
        target_rows = list(target_lowering_matrix.get("rows") or [])
        target_shadow_executable_count = sum(1 for row in target_rows if bool(row.get("shadow_executable")))
        payload_target_summary = {
            "row_count": len(target_rows),
            "shadow_executable_count": target_shadow_executable_count,
            "canon_target_profile_shadow_executor_count": int(
                target_lowering_matrix.get("summary", {}).get("execution_mode_counts", {}).get(
                    "canon_target_profile_shadow_executor",
                    0,
                )
            ),
        }
    else:
        payload_target_summary = None

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
            "target_profile_shadow_execution": payload_target_summary,
            "target_profile_candidate_primary_ready": bool(
                dict(target_profile_promotion.get("summary") or {}).get("candidate_primary_ready")
            )
            if target_profile_promotion is not None
            else None,
        },
        "recommendations": recommendations,
    }
    if lowering_matrix is not None:
        payload["search_plane_a_lowering_matrix"] = lowering_matrix
    if target_lowering_matrix is not None:
        payload["target_search_plane_a_lowering_matrix"] = target_lowering_matrix
        if payload_target_summary and int(payload_target_summary["canon_target_profile_shadow_executor_count"]) > 0:
            payload["recommendations"].append(
                "bounded_target_profile_search_plane_shadow_execution_is_available"
            )
    if target_profile_promotion is not None:
        payload["target_profile_promotion"] = target_profile_promotion
    if include_search_plane_transition:
        payload["search_plane_a_transition"] = build_phase1a_search_plane_a_transition_bundle(
            source_profile_id=profile_id,
            target_profile_id="planetscale_opensearch_v1",
            routes=routes,
            source_metadata_store_path=metadata_store_path,
        )
    return payload

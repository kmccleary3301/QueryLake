from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Iterable, Optional

from QueryLake.canon.compiler.profile_lowering import build_profile_lowering_snapshot
from QueryLake.canon.runtime.shadow_matrix import _default_routes
from QueryLake.runtime.db_compat import DeploymentProfile, get_deployment_profile
from QueryLake.runtime.profile_bringup import build_profile_bringup_payload
from QueryLake.runtime.projection_refresh import (
    ProjectionRefreshRequest,
    explain_projection_refresh_plan,
)
from QueryLake.runtime.projection_registry import get_projection_descriptor
from QueryLake.runtime.projection_writers import get_projection_writer_runtime, resolve_projection_writer
from QueryLake.runtime.retrieval_pipeline_runtime import default_pipeline_for_route


_ROUTE_TO_DEFAULT_PIPELINE_ROUTE = {
    "search_hybrid.document_chunk": "search_hybrid",
    "search_bm25.document_chunk": "search_bm25.document_chunk",
    "search_file_chunks": "search_file_chunks",
}


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _normalize_routes(routes: Iterable[str] | None) -> list[str]:
    if routes is None:
        return list(_default_routes())
    return [str(route) for route in routes]


def _route_pipeline(route: str):
    return default_pipeline_for_route(_ROUTE_TO_DEFAULT_PIPELINE_ROUTE.get(route, route))


def _projection_ids_from_bringup(payload: dict[str, Any]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for group_key in (
        "ready_projection_ids",
        "projection_ids_needing_build",
        "recommended_projection_ids",
        "bootstrapable_required_projection_ids",
        "bootstrapable_recommended_projection_ids",
        "nonbootstrapable_required_projection_ids",
        "nonbootstrapable_recommended_projection_ids",
    ):
        for value in list(payload.get(group_key) or []):
            projection_id = str(value or "")
            if projection_id and projection_id not in seen:
                ordered.append(projection_id)
                seen.add(projection_id)
    return ordered


def _runtime_payload(writer_runtime: Any) -> dict[str, Any]:
    if hasattr(writer_runtime, "to_payload"):
        return dict(writer_runtime.to_payload())
    return {
        "writer_id": str(getattr(writer_runtime, "writer_id", "") or ""),
        "implemented": bool(getattr(writer_runtime, "implemented", False)),
        "support_state": str(getattr(writer_runtime, "support_state", "") or ""),
        "mode": str(getattr(writer_runtime, "mode", "") or ""),
        "notes": getattr(writer_runtime, "notes", None),
    }


def build_phase1a_projection_writer_matrix(
    *,
    profile: Optional[DeploymentProfile] = None,
    projection_ids: Iterable[str],
    metadata_store_path: Optional[str] = None,
) -> dict[str, Any]:
    effective_profile = profile or get_deployment_profile()
    rows: list[dict[str, Any]] = []
    executable_count = 0
    rebuild_mode_count = 0
    planned_count = 0
    absent_status_count = 0

    for projection_id in [str(value) for value in projection_ids]:
        descriptor = get_projection_descriptor(projection_id)
        writer_resolution = resolve_projection_writer(
            projection_id,
            projection_version="v1",
            profile=effective_profile,
            descriptor=descriptor,
            lane_family=descriptor.lane_family,
        )
        writer_runtime = get_projection_writer_runtime(writer_resolution)
        plan = explain_projection_refresh_plan(
            ProjectionRefreshRequest(
                projection_id=projection_id,
                projection_version="v1",
                lane_families=[descriptor.lane_family],
                metadata={"canon_phase": "phase1a"},
            ),
            profile=effective_profile,
            metadata_store_path=metadata_store_path,
        )
        action = dict((plan.actions or [{}])[0] or {})
        status_snapshot = dict((plan.status_snapshot or [{}])[0] or {})
        row = {
            "projection_id": projection_id,
            "lane_family": descriptor.lane_family,
            "authority_model": descriptor.authority_model,
            "source_scope": descriptor.source_scope,
            "record_schema": descriptor.record_schema,
            "target_backend_family": descriptor.target_backend_family,
            "writer_resolution": writer_resolution.to_payload(),
            "writer_runtime": _runtime_payload(writer_runtime),
            "refresh_plan": {
                "mode": action.get("mode"),
                "implemented": bool(action.get("implemented", False)),
                "writer_implemented": bool(action.get("writer_implemented", False)),
                "support_state": str(action.get("support_state") or ""),
                "invalidated_by": list(action.get("invalidated_by") or []),
            },
            "build_state": status_snapshot,
            "projection_target": dict(plan.metadata.get("projection_target") or {}),
        }
        rows.append(row)
        if bool(writer_resolution.implemented):
            executable_count += 1
        if str(action.get("mode") or "") == "rebuild":
            rebuild_mode_count += 1
        if str(action.get("mode") or "") == "planned":
            planned_count += 1
        if str(status_snapshot.get("status") or "absent") == "absent":
            absent_status_count += 1

    recommendations: list[str] = []
    if rows and executable_count == len(rows):
        recommendations.append("projection_writers_resolve_for_declared_targets")
    if rebuild_mode_count > 0:
        recommendations.append("bootstrap_or_refresh_projection_targets")
    if planned_count > 0:
        recommendations.append("planned_projection_writers_require_future_profile_work")

    return {
        "schema_version": "canon_phase1a_projection_writer_matrix_v1",
        "generated_at": _utc_now(),
        "profile_id": effective_profile.id,
        "projection_ids": [row["projection_id"] for row in rows],
        "rows": rows,
        "summary": {
            "projection_count": len(rows),
            "writer_executable_count": executable_count,
            "writer_planned_count": planned_count,
            "refresh_rebuild_mode_count": rebuild_mode_count,
            "build_state_absent_count": absent_status_count,
        },
        "recommendations": recommendations,
    }


def build_phase1a_profile_readiness_bundle(
    *,
    profile_id: Optional[str] = None,
    routes: Iterable[str] | None = None,
    metadata_store_path: Optional[str] = None,
) -> dict[str, Any]:
    effective_profile = get_deployment_profile(profile_id) if profile_id else get_deployment_profile()
    bringup = build_profile_bringup_payload(
        profile=effective_profile,
        metadata_store_path=metadata_store_path,
    )
    route_recovery = {
        str(row.get("route_id") or ""): dict(row)
        for row in list(bringup.get("route_recovery") or [])
        if isinstance(row, dict)
    }
    effective_routes = _normalize_routes(routes or list(bringup.get("declared_executable_route_ids") or []) or None)
    route_rows: list[dict[str, Any]] = []
    compile_available_count = 0
    runtime_ready_count = 0

    for route in effective_routes:
        pipeline = _route_pipeline(route)
        lowering = build_profile_lowering_snapshot(route=route, pipeline=pipeline, profile=effective_profile)
        recovery = route_recovery.get(route, {})
        effective_runtime_ready = bool(recovery.get("runtime_ready", lowering.get("runtime_ready")))
        row = {
            "route": route,
            "pipeline_id": getattr(pipeline, "pipeline_id", None),
            "lowering": lowering,
            "route_recovery": recovery,
            "effective_runtime_ready": effective_runtime_ready,
        }
        route_rows.append(row)
        if pipeline is not None:
            compile_available_count += 1
        if effective_runtime_ready:
            runtime_ready_count += 1

    projection_ids = _projection_ids_from_bringup(bringup)
    writer_matrix = build_phase1a_projection_writer_matrix(
        profile=effective_profile,
        projection_ids=projection_ids,
        metadata_store_path=metadata_store_path,
    )

    lexical_gold_recommended = list(bringup.get("lexical_gold_recommended_route_ids") or [])
    recommendations: list[str] = list(writer_matrix.get("recommendations") or [])
    if bool(bringup.get("summary", {}).get("declared_executable_routes_runtime_ready")):
        recommendations.append("profile_runtime_ready_for_declared_phase1a_routes")
    else:
        recommendations.append("resolve_route_runtime_blockers_before_canon_primary")
    if lexical_gold_recommended:
        recommendations.append("retain_gold_profile_for_exact_lexical_constraints")

    return {
        "schema_version": "canon_phase1a_profile_readiness_bundle_v1",
        "generated_at": _utc_now(),
        "profile": {
            "id": effective_profile.id,
            "label": effective_profile.label,
            "implemented": bool(effective_profile.implemented),
        },
        "routes": effective_routes,
        "route_rows": route_rows,
        "bringup": bringup,
        "projection_writer_matrix": writer_matrix,
        "summary": {
            "route_count": len(effective_routes),
            "compile_available_count": compile_available_count,
            "runtime_ready_count": runtime_ready_count,
            "declared_executable_routes_runtime_ready": bool(
                bringup.get("summary", {}).get("declared_executable_routes_runtime_ready")
            ),
            "projection_count": int(writer_matrix.get("summary", {}).get("projection_count", 0)),
            "projection_writer_executable_count": int(
                writer_matrix.get("summary", {}).get("writer_executable_count", 0)
            ),
            "projection_writer_planned_count": int(
                writer_matrix.get("summary", {}).get("writer_planned_count", 0)
            ),
            "bootstrapable_required_projection_count": int(
                bringup.get("summary", {}).get("bootstrapable_required_projection_count", 0)
            ),
            "bootstrapable_recommended_projection_count": int(
                bringup.get("summary", {}).get("bootstrapable_recommended_projection_count", 0)
            ),
        },
        "recommendations": recommendations,
    }


def build_phase1a_search_plane_a_transition_bundle(
    *,
    source_profile_id: str = "aws_aurora_pg_opensearch_v1",
    target_profile_id: str = "planetscale_opensearch_v1",
    routes: Iterable[str] | None = None,
    source_metadata_store_path: Optional[str] = None,
    target_metadata_store_path: Optional[str] = None,
) -> dict[str, Any]:
    source_bundle = build_phase1a_profile_readiness_bundle(
        profile_id=source_profile_id,
        routes=routes,
        metadata_store_path=source_metadata_store_path,
    )
    target_bundle = build_phase1a_profile_readiness_bundle(
        profile_id=target_profile_id,
        routes=routes,
        metadata_store_path=target_metadata_store_path,
    )

    source_routes = {row["route"]: row for row in source_bundle["route_rows"]}
    target_routes = {row["route"]: row for row in target_bundle["route_rows"]}
    route_deltas: list[dict[str, Any]] = []
    for route in sorted(set(source_routes.keys()) | set(target_routes.keys())):
        source_row = source_routes.get(route, {})
        target_row = target_routes.get(route, {})
        route_deltas.append(
            {
                "route": route,
                "source_compile_available": bool(source_row.get("pipeline_id")),
                "target_compile_available": bool(target_row.get("pipeline_id")),
                "source_runtime_ready": bool(source_row.get("lowering", {}).get("runtime_ready")),
                "target_runtime_ready": bool(target_row.get("lowering", {}).get("runtime_ready")),
                "source_support_state": str(source_row.get("lowering", {}).get("support_state") or ""),
                "target_support_state": str(target_row.get("lowering", {}).get("support_state") or ""),
            }
        )

    source_projections = {
        row["projection_id"]: row for row in source_bundle["projection_writer_matrix"]["rows"]
    }
    target_projections = {
        row["projection_id"]: row for row in target_bundle["projection_writer_matrix"]["rows"]
    }
    projection_deltas: list[dict[str, Any]] = []
    for projection_id in sorted(set(source_projections.keys()) | set(target_projections.keys())):
        source_row = source_projections.get(projection_id, {})
        target_row = target_projections.get(projection_id, {})
        projection_deltas.append(
            {
                "projection_id": projection_id,
                "source_writer_implemented": bool(source_row.get("writer_resolution", {}).get("implemented")),
                "target_writer_implemented": bool(target_row.get("writer_resolution", {}).get("implemented")),
                "source_mode": str(source_row.get("refresh_plan", {}).get("mode") or ""),
                "target_mode": str(target_row.get("refresh_plan", {}).get("mode") or ""),
                "source_support_state": str(source_row.get("refresh_plan", {}).get("support_state") or ""),
                "target_support_state": str(target_row.get("refresh_plan", {}).get("support_state") or ""),
            }
        )

    recommendations: list[str] = []
    if route_deltas and all(delta["source_compile_available"] for delta in route_deltas):
        recommendations.append("source_opensearch_stack_covers_bounded_phase1a_routes")
    if any(not delta["target_runtime_ready"] for delta in route_deltas):
        recommendations.append("target_planetscale_opensearch_requires_runtime_lowering_before_cutover")
    if any(not delta["target_writer_implemented"] for delta in projection_deltas):
        recommendations.append("target_planetscale_opensearch_requires_projection_writer_implementation")

    return {
        "schema_version": "canon_phase1a_search_plane_a_transition_bundle_v1",
        "generated_at": _utc_now(),
        "source_profile_id": source_profile_id,
        "target_profile_id": target_profile_id,
        "source": source_bundle,
        "target": target_bundle,
        "route_deltas": route_deltas,
        "projection_deltas": projection_deltas,
        "recommendations": recommendations,
    }

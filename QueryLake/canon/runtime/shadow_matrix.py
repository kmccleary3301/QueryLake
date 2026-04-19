from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Iterable

from QueryLake.canon.compiler.profile_lowering import build_profile_lowering_snapshot
from QueryLake.canon.compiler.querylake_route_compiler import compile_querylake_route_to_graph
from QueryLake.runtime.db_compat import DEPLOYMENT_PROFILES, get_deployment_profile
from QueryLake.runtime.retrieval_pipeline_runtime import default_pipeline_for_route


_ROUTE_TO_DEFAULT_PIPELINE_ROUTE = {
    "search_hybrid.document_chunk": "search_hybrid",
    "search_bm25.document_chunk": "search_bm25.document_chunk",
    "search_file_chunks": "search_file_chunks",
}


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _default_routes() -> list[str]:
    return [
        "search_hybrid.document_chunk",
        "search_bm25.document_chunk",
        "search_file_chunks",
    ]


def build_phase1a_route_profile_matrix(
    *,
    routes: Iterable[str] | None = None,
    profile_ids: Iterable[str] | None = None,
) -> dict[str, Any]:
    effective_routes = [str(route) for route in (routes or _default_routes())]
    effective_profile_ids = [str(profile_id) for profile_id in (profile_ids or sorted(DEPLOYMENT_PROFILES.keys()))]
    rows: list[dict[str, Any]] = []

    for profile_id in effective_profile_ids:
        profile = get_deployment_profile(profile_id)
        for route in effective_routes:
            pipeline = default_pipeline_for_route(_ROUTE_TO_DEFAULT_PIPELINE_ROUTE.get(route, route))
            compile_payload: dict[str, Any]
            try:
                graph = compile_querylake_route_to_graph(route=route, pipeline=pipeline, options={})
                compile_payload = {
                    "available": True,
                    "graph_id": graph.graph_id,
                    "graph_name": graph.graph_name,
                    "node_count": len(graph.nodes),
                    "requested_outputs": [output.key for output in graph.requested_outputs],
                }
            except Exception as exc:
                compile_payload = {
                    "available": False,
                    "error": str(exc),
                }

            lowering = build_profile_lowering_snapshot(route=route, pipeline=pipeline, profile=profile)
            rows.append(
                {
                    "route": route,
                    "profile_id": profile.id,
                    "profile_label": profile.label,
                    "profile_implemented": bool(profile.implemented),
                    "compile": compile_payload,
                    "lowering": lowering,
                }
            )

    recommendations: list[str] = []
    if rows and all(row["compile"]["available"] for row in rows):
        recommendations.append("phase1a_routes_compile_across_declared_profiles")
    if any(not row["lowering"]["runtime_ready"] for row in rows):
        recommendations.append("investigate_profile_runtime_blockers")
    if any(not row["profile_implemented"] for row in rows):
        recommendations.append("planned_profiles_should_remain_shadow_only")

    return {
        "schema_version": "canon_phase1a_route_profile_matrix_v1",
        "generated_at": _utc_now(),
        "routes": effective_routes,
        "profile_ids": effective_profile_ids,
        "rows": rows,
        "recommendations": recommendations,
    }

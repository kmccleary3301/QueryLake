from __future__ import annotations

from typing import Any, Optional

from QueryLake.runtime.db_compat import DeploymentProfile, get_deployment_profile
from QueryLake.runtime.retrieval_route_executors import (
    ResolvedRouteExecutor,
    resolve_search_bm25_route_executor,
    resolve_search_file_chunks_route_executor,
    resolve_search_hybrid_route_executor,
)
from QueryLake.canon.compiler.querylake_route_compiler import normalize_querylake_route_pipeline
from QueryLake.typing.retrieval_primitives import RetrievalPipelineSpec


def _normalize_route(route: str) -> str:
    route_value = str(route or "")
    if route_value == "search_hybrid":
        return "search_hybrid.document_chunk"
    if route_value == "search_bm25":
        return "search_bm25.document_chunk"
    return route_value


def _infer_hybrid_lane_flags(pipeline: Optional[RetrievalPipelineSpec]) -> tuple[bool, bool, bool]:
    if pipeline is None:
        return True, True, False
    stage_ids = {str(stage.stage_id) for stage in pipeline.stages if stage.enabled}
    primitive_ids = {str(stage.primitive_id) for stage in pipeline.stages if stage.enabled}
    use_bm25 = "bm25" in stage_ids or any("BM25" in primitive for primitive in primitive_ids)
    use_similarity = "dense" in stage_ids or any("Dense" in primitive for primitive in primitive_ids)
    use_sparse = "sparse" in stage_ids or any("Sparse" in primitive for primitive in primitive_ids)
    return use_bm25, use_similarity, use_sparse


def _resolve_route_executor(
    route: str,
    *,
    pipeline: Optional[RetrievalPipelineSpec] = None,
    profile: Optional[DeploymentProfile] = None,
) -> ResolvedRouteExecutor:
    effective_profile = profile or get_deployment_profile()
    route_value = _normalize_route(route)
    if route_value == "search_hybrid.document_chunk":
        use_bm25, use_similarity, use_sparse = _infer_hybrid_lane_flags(pipeline)
        return resolve_search_hybrid_route_executor(
            use_bm25=use_bm25,
            use_similarity=use_similarity,
            use_sparse=use_sparse,
            profile=effective_profile,
        )
    if route_value == "search_bm25.document_chunk":
        return resolve_search_bm25_route_executor(table="document_chunk", profile=effective_profile)
    if route_value == "search_file_chunks":
        return resolve_search_file_chunks_route_executor(profile=effective_profile)
    raise ValueError(f"Unsupported Phase 1A route for profile lowering: {route_value}")


def build_profile_lowering_snapshot(
    *,
    route: str,
    pipeline: Optional[RetrievalPipelineSpec] = None,
    profile: Optional[DeploymentProfile] = None,
    options: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    route_value = _normalize_route(route)
    normalized_pipeline = (
        normalize_querylake_route_pipeline(route=route_value, pipeline=pipeline, options=options)
        if pipeline is not None
        else None
    )
    resolved = _resolve_route_executor(route_value, pipeline=normalized_pipeline, profile=profile)
    payload = resolved.to_payload()
    planning_v2 = dict(payload.get("planning_v2") or {})
    return {
        "profile_id": payload["profile_id"],
        "route_id": payload["route_id"],
        "route_alias": str(route),
        "options": dict(options or {}),
        "executor_id": payload["executor_id"],
        "implemented": bool(payload.get("implemented", False)),
        "support_state": str(payload.get("support_state") or ""),
        "representation_scope_id": str(payload.get("representation_scope_id") or ""),
        "backend_stack": dict(payload.get("backend_stack") or {}),
        "projection_descriptors": list(payload.get("projection_descriptors") or []),
        "lane_adapters": dict(payload.get("lane_adapters") or {}),
        "runtime_ready": bool(planning_v2.get("runtime_ready", payload.get("implemented", False))),
        "runtime_blockers": list(planning_v2.get("runtime_blockers") or []),
        "blocking_capability": resolved.blocking_capability,
    }

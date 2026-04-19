from __future__ import annotations

from typing import Any, Mapping

from QueryLake.canon.runtime.querylake_shadow import build_querylake_shadow_diff, execute_querylake_pipeline_in_canon_shadow
from QueryLake.canon.runtime.replay_bundle import build_shadow_replay_bundle, persist_shadow_replay_bundle
from QueryLake.canon.runtime.shadow_reports import build_shadow_execution_report, persist_shadow_execution_report
from QueryLake.canon.runtime.trace_export import build_shadow_trace_export, persist_shadow_trace_export
from QueryLake.runtime.retrieval_pipeline_runtime import default_pipeline_for_route
from QueryLake.typing.retrieval_primitives import (
    FusionPrimitive,
    RetrievalExecutionResult,
    RetrievalRequest,
    RetrieverPrimitive,
    RerankerPrimitive,
)


def build_request_from_shadow_case(case: Mapping[str, Any], *, limit: int = 10) -> RetrievalRequest:
    route = str(case.get("route") or "")
    query = str(case.get("query") or "")
    return RetrievalRequest(
        route=route,
        query_text=query,
        options={"limit": int(limit)},
        query_ir_v2={"route_id": route},
    )


def _default_pipeline_route(route: str) -> str:
    route_value = str(route or "")
    if route_value == "search_hybrid.document_chunk":
        return "search_hybrid"
    return route_value


async def execute_shadow_case(
    *,
    case: Mapping[str, Any],
    profile_id: str,
    retrievers: Mapping[str, RetrieverPrimitive],
    legacy_result: RetrievalExecutionResult,
    fusion: FusionPrimitive | None = None,
    reranker: RerankerPrimitive | None = None,
    output_dir: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    request = build_request_from_shadow_case(case, limit=limit)
    pipeline = default_pipeline_for_route(_default_pipeline_route(request.route))
    if pipeline is None:
        raise ValueError(f"No default pipeline for route '{request.route}'")

    canon_result = await execute_querylake_pipeline_in_canon_shadow(
        request=request,
        pipeline=pipeline,
        retrievers=retrievers,
        fusion=fusion,
        reranker=reranker,
    )
    shadow_diff = build_querylake_shadow_diff(
        request=request,
        pipeline=pipeline,
        profile_id=profile_id,
        legacy_result=legacy_result,
        canon_result=canon_result,
    )
    report = build_shadow_execution_report(
        report_id=f"canon-shadow-{case.get('case_id', 'case')}",
        request=request,
        pipeline=pipeline,
        profile_id=profile_id,
        legacy_result=legacy_result,
        canon_result=canon_result,
        shadow_diff=shadow_diff,
        top_k_snapshot=min(int(limit), 10),
    )
    persisted = None
    replay_bundle = None
    trace_export = None
    if output_dir:
        persisted = persist_shadow_execution_report(report=report, output_dir=output_dir)
        replay_bundle = persist_shadow_replay_bundle(
            bundle=build_shadow_replay_bundle(
                bundle_id=f"canon-shadow-bundle-{case.get('case_id', 'case')}",
                request=request,
                pipeline=pipeline,
                legacy_result=legacy_result,
                canon_result=canon_result,
                shadow_diff=shadow_diff,
            ),
            output_dir=output_dir,
        )
        trace_export = persist_shadow_trace_export(
            export=build_shadow_trace_export(
                export_id=f"canon-shadow-traces-{case.get('case_id', 'case')}",
                request=request,
                pipeline=pipeline,
                canon_result=canon_result,
            ),
            output_dir=output_dir,
        )

    return {
        "case_id": case.get("case_id"),
        "route": request.route,
        "pipeline_id": pipeline.pipeline_id,
        "shadow_diff": shadow_diff,
        "report": report,
        "persisted": persisted,
        "replay_bundle": replay_bundle,
        "trace_export": trace_export,
    }

from __future__ import annotations

import time
from typing import Any, Mapping

from QueryLake.canon import CanonExecutor, ExecutionContext, ExecutionMode
from QueryLake.canon.compiler import compile_querylake_route_to_graph
from QueryLake.canon.runtime.bridge_metadata import build_canon_bridge_metadata
from QueryLake.canon.runtime.shadow_diff import build_shadow_diff_summary
from QueryLake.typing.retrieval_primitives import (
    FusionPrimitive,
    RetrievalExecutionResult,
    RetrievalRequest,
    RetrievalStageTrace,
    RetrieverPrimitive,
    RerankerPrimitive,
)


def _source_from_dependency_key(key: str) -> str:
    parts = str(key or "").split(".")
    if len(parts) >= 3 and parts[0] == "stage":
        return parts[1]
    return str(key or "unknown")


async def execute_querylake_pipeline_in_canon_shadow(
    *,
    request: RetrievalRequest,
    pipeline,
    retrievers: Mapping[str, RetrieverPrimitive],
    fusion: FusionPrimitive | None,
    reranker: RerankerPrimitive | None,
) -> RetrievalExecutionResult:
    route_value = str(request.query_ir_v2.get("route_id") or request.route or "")
    graph = compile_querylake_route_to_graph(
        route=route_value,
        pipeline=pipeline,
        options=request.options,
    )

    async def retrieval_stage_handler(node, _inputs, context):
        stage_id = str(node.config.get("stage_id") or "")
        primitive = retrievers.get(stage_id)
        if primitive is None:
            raise RuntimeError(f"No retriever registered for stage '{stage_id}'")
        stage_request = request.model_copy(deep=True)
        stage_request.options = {**request.options, **dict(node.config.get("stage_config") or {})}
        candidates = await primitive.retrieve(stage_request)
        return {"candidates": candidates}

    async def fusion_stage_handler(_node, inputs, _context):
        grouped = {
            _source_from_dependency_key(key): value
            for key, value in inputs.items()
        }
        if fusion is None:
            ordered = []
            for value in grouped.values():
                ordered.extend(value)
            return {"candidates": ordered}
        return {"candidates": fusion.fuse(request, grouped)}

    async def reranker_stage_handler(_node, inputs, _context):
        candidates = next(iter(inputs.values()), [])
        if reranker is None:
            return {"candidates": candidates}
        reranked = await reranker.rerank(request, list(candidates))
        return {"candidates": reranked}

    executor = CanonExecutor()
    t_1 = time.time()
    execution = await executor.execute_async(
        graph,
        handlers={
            "retrieval_stage": retrieval_stage_handler,
            "fusion_stage": fusion_stage_handler,
            "reranker_stage": reranker_stage_handler,
        },
        context=ExecutionContext(mode=ExecutionMode.CANON_SHADOW),
    )
    t_2 = time.time()

    requested_key = graph.requested_outputs[0].key
    candidates = list(execution.outputs.get(requested_key, []))
    traces = [
        RetrievalStageTrace(
            stage=f"canon:{node_result.node_id}",
            duration_ms=0.0,
            input_count=None,
            output_count=None,
            details={
                "operation": node_result.operation,
                "status": node_result.status,
                "effect_class": node_result.effect_class.value,
            },
        )
        for node_result in execution.summary.node_results
    ]
    traces.append(
        RetrievalStageTrace(
            stage="canon_shadow_execute",
            duration_ms=(t_2 - t_1) * 1000.0,
            input_count=None,
            output_count=len(candidates),
            details={
                "graph_id": execution.graph_id,
                "requested_output_keys": list(execution.summary.requested_output_keys),
                "executed_node_ids": list(execution.summary.executed_node_ids),
            },
        )
    )

    bridge_metadata = build_canon_bridge_metadata(
        route=route_value,
        pipeline=pipeline,
        options={**request.options, "canon_debug_replay": bool(request.options.get("canon_debug_replay", False))},
    )
    return RetrievalExecutionResult(
        pipeline_id=pipeline.pipeline_id,
        pipeline_version=pipeline.version,
        candidates=candidates,
        traces=traces,
        metadata={
            "canon_bridge": bridge_metadata,
            "canon_graph_id": execution.graph_id,
        },
    )


def build_querylake_shadow_diff(
    *,
    request: RetrievalRequest,
    pipeline,
    profile_id: str,
    legacy_result: RetrievalExecutionResult,
    canon_result: RetrievalExecutionResult,
) -> dict[str, Any]:
    route_value = str(request.query_ir_v2.get("route_id") or request.route or "")
    return build_shadow_diff_summary(
        route_family=route_value,
        profile_id=profile_id,
        execution_mode="canon_shadow",
        legacy_candidates=legacy_result.candidates,
        canon_candidates=canon_result.candidates,
        top_k_requested=int(request.options.get("limit", len(legacy_result.candidates) or len(canon_result.candidates) or 0)),
        legacy_plan_id=f"legacy::{pipeline.pipeline_id}:{pipeline.version}",
        canon_graph_id=str(canon_result.metadata.get("canon_graph_id") or ""),
        trace_summary_ref=str(canon_result.metadata.get("canon_graph_id") or ""),
        replay_bundle_ref=None,
    )

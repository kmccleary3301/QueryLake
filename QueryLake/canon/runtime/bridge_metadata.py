from __future__ import annotations

from typing import Any, Mapping

from QueryLake.canon.compiler import (
    QueryLakeRouteCompileError,
    RetrievalPipelineCompileError,
    compile_querylake_route_to_graph,
    compile_retrieval_pipeline_to_graph,
)
from QueryLake.canon.runtime.summaries import build_replay_summary, build_trace_summary
from QueryLake.typing.retrieval_primitives import RetrievalPipelineSpec


def _retention_class(*, options: Mapping[str, Any]) -> str:
    if bool(options.get("canon_debug_replay", False)):
        return "debug_replay"
    if bool(options.get("explain_plan", False)):
        return "summary_plus_detail"
    return "summary_only"


def _replay_guarantee_class(*, graph_node_count: int) -> str:
    # Phase 1A bridge compilation is diagnostic only. No execution replay is guaranteed yet.
    return "analysis_only" if graph_node_count > 0 else "best_effort_external"


def build_canon_bridge_metadata(
    *,
    route: str,
    pipeline: RetrievalPipelineSpec,
    options: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    opts = dict(options or {})
    try:
        graph = compile_querylake_route_to_graph(route=route, pipeline=pipeline, options=opts)
    except QueryLakeRouteCompileError:
        graph = compile_retrieval_pipeline_to_graph(route=route, pipeline=pipeline, options=opts)
    except RetrievalPipelineCompileError as exc:
        return {
            "available": False,
            "route": str(route),
            "pipeline_id": pipeline.pipeline_id,
            "pipeline_version": pipeline.version,
            "compile_error": str(exc),
        }

    stage_nodes = [node for node in graph.nodes if node.node_id.startswith("stage.")]
    retention_class = _retention_class(options=opts)
    return {
        "available": True,
        "route": str(route),
        "pipeline_id": pipeline.pipeline_id,
        "pipeline_version": pipeline.version,
        "graph_id": graph.graph_id,
        "graph_name": graph.graph_name,
        "node_count": len(graph.nodes),
        "node_ids": [node.node_id for node in graph.nodes],
        "requested_output_keys": [ref.key for ref in graph.requested_outputs],
        "stage_count": len(stage_nodes),
        "stage_nodes": [
            {
                "node_id": node.node_id,
                "primitive_id": node.config.get("primitive_id"),
                "stage_id": node.config.get("stage_id"),
                "effect_class": node.effect_class.value,
            }
            for node in stage_nodes
        ],
        "compiler": {
            "mode": "querylake_route_compiler",
            "deterministic_graph_identity": True,
        },
        "trace_summary": build_trace_summary(
            retention_class=retention_class,
            execution_mode="canon_shadow",
        ).to_payload(),
        "replay_summary": build_replay_summary(
            retention_class=retention_class,
            replay_guarantee_class=_replay_guarantee_class(graph_node_count=len(graph.nodes)),
        ).to_payload(),
    }

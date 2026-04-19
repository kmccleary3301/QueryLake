from __future__ import annotations

from typing import Any, Mapping

from QueryLake.canon.effects import EffectClass
from QueryLake.canon.models import GraphSpec, NodeSpec, OutputRef
from QueryLake.typing.retrieval_primitives import RetrievalPipelineSpec, RetrievalPipelineStage


class RetrievalPipelineCompileError(ValueError):
    def __init__(self, message: str, route: str, pipeline_id: str):
        super().__init__(message)
        self.route = route
        self.pipeline_id = pipeline_id

    def __str__(self) -> str:
        return f"route={self.route} pipeline={self.pipeline_id}: {super().__str__()}"


_STAGE_OUTPUT_NAME = "candidates"
_FUSION_OUTPUT_NAME = "candidates"
_RERANK_OUTPUT_NAME = "candidates"


def _node_id_for_stage(stage: RetrievalPipelineStage) -> str:
    return f"stage.{stage.stage_id}"


def _is_fusion_enabled(flags: Mapping[str, Any]) -> bool:
    if "fusion_primitive" not in flags:
        return False
    primitive = str(flags.get("fusion_primitive", "") or "").strip().lower()
    return primitive not in {"", "none", "off", "disabled"}


def _is_reranker_enabled(flags: Mapping[str, Any], options: Mapping[str, Any]) -> bool:
    enabled = bool(options.get("rerank_enabled", flags.get("rerank_enabled", False)))
    primitive = str(options.get("reranker_primitive", flags.get("reranker_primitive", "CrossEncoderReranker")) or "CrossEncoderReranker").strip().lower()
    return enabled and primitive not in {"", "none", "off", "disabled"}


def _build_stage_node(stage: RetrievalPipelineStage, *, route: str, pipeline: RetrievalPipelineSpec) -> NodeSpec:
    return NodeSpec(
        node_id=_node_id_for_stage(stage),
        operation="retrieval_stage",
        effect_class=EffectClass.EXTERNAL_READ_ONLY,
        output_names=(_STAGE_OUTPUT_NAME,),
        config={
            "route": route,
            "pipeline_id": pipeline.pipeline_id,
            "pipeline_version": pipeline.version,
            "stage_id": stage.stage_id,
            "primitive_id": stage.primitive_id,
            "stage_config": dict(stage.config or {}),
        },
    )


def compile_retrieval_pipeline_to_graph(
    *,
    route: str,
    pipeline: RetrievalPipelineSpec,
    options: Mapping[str, Any] | None = None,
) -> GraphSpec:
    effective_route = str(route or "").strip()
    if not effective_route:
        raise RetrievalPipelineCompileError("route must be non-empty", route="", pipeline_id=pipeline.pipeline_id)

    enabled_stages = [stage for stage in pipeline.stages if bool(stage.enabled)]
    if not enabled_stages:
        raise RetrievalPipelineCompileError(
            "pipeline has no enabled stages",
            route=effective_route,
            pipeline_id=pipeline.pipeline_id,
        )

    opts = dict(options or {})
    flags = dict(pipeline.flags or {})
    nodes: list[NodeSpec] = []
    stage_refs: list[OutputRef] = []

    for stage in enabled_stages:
        stage_node = _build_stage_node(stage, route=effective_route, pipeline=pipeline)
        nodes.append(stage_node)
        stage_refs.append(OutputRef(stage_node.node_id, _STAGE_OUTPUT_NAME))

    requested_output = stage_refs[0]

    if len(stage_refs) > 1 or _is_fusion_enabled(flags):
        fusion_primitive = str(flags.get("fusion_primitive", "WeightedScoreFusion") or "WeightedScoreFusion").strip()
        fusion_node = NodeSpec(
            node_id="fusion",
            operation="fusion_stage",
            effect_class=EffectClass.PURE_DETERMINISTIC,
            dependencies=tuple(stage_refs),
            output_names=(_FUSION_OUTPUT_NAME,),
            config={
                "route": effective_route,
                "pipeline_id": pipeline.pipeline_id,
                "pipeline_version": pipeline.version,
                "fusion_primitive": fusion_primitive,
                "flags": flags,
            },
        )
        nodes.append(fusion_node)
        requested_output = OutputRef(fusion_node.node_id, _FUSION_OUTPUT_NAME)

    if _is_reranker_enabled(flags, opts):
        reranker_primitive = str(
            opts.get("reranker_primitive", flags.get("reranker_primitive", "CrossEncoderReranker"))
            or "CrossEncoderReranker"
        ).strip()
        rerank_node = NodeSpec(
            node_id="rerank",
            operation="reranker_stage",
            effect_class=EffectClass.EXTERNAL_READ_ONLY,
            dependencies=(requested_output,),
            output_names=(_RERANK_OUTPUT_NAME,),
            config={
                "route": effective_route,
                "pipeline_id": pipeline.pipeline_id,
                "pipeline_version": pipeline.version,
                "reranker_primitive": reranker_primitive,
                "query_text": opts.get("rerank_query_text"),
            },
        )
        nodes.append(rerank_node)
        requested_output = OutputRef(rerank_node.node_id, _RERANK_OUTPUT_NAME)

    graph_name = f"canon.retrieval.{effective_route}.{pipeline.pipeline_id}.{pipeline.version}"
    return GraphSpec(nodes=tuple(nodes), requested_outputs=(requested_output,), graph_name=graph_name)

from __future__ import annotations

from typing import Any, Dict, Optional

from QueryLake.runtime.db_compat import get_deployment_profile
from QueryLake.runtime.route_planning_v2 import instantiate_route_planning_v2
from QueryLake.runtime.retrieval_lanes import resolve_retrieval_adapter
from QueryLake.typing.retrieval_primitives import RetrievalPipelineSpec


def _effective_fusion(
    *,
    options: Dict[str, Any],
    flags: Dict[str, Any],
) -> Dict[str, Any]:
    primitive_raw = options.get("fusion_primitive", flags.get("fusion_primitive", "WeightedScoreFusion"))
    primitive = str(primitive_raw or "WeightedScoreFusion").strip()
    primitive_lower = primitive.lower()

    if primitive_lower in {"none", "off", "disabled"}:
        return {
            "enabled": False,
            "primitive": "none",
        }
    if primitive_lower in {"rrf", "rrfusion"}:
        return {
            "enabled": True,
            "primitive": "RRFusion",
            "rrf_k": int(options.get("rrf_k", flags.get("rrf_k", 60))),
        }
    return {
        "enabled": True,
        "primitive": "WeightedScoreFusion",
        "normalization": str(options.get("fusion_normalization", flags.get("fusion_normalization", "minmax"))),
        "weights": options.get("fusion_weights"),
        "score_keys": options.get("fusion_score_keys"),
    }


def _effective_reranker(
    *,
    options: Dict[str, Any],
    flags: Dict[str, Any],
) -> Dict[str, Any]:
    rerank_enabled = bool(options.get("rerank_enabled", flags.get("rerank_enabled", False)))
    reranker_primitive = str(options.get("reranker_primitive", flags.get("reranker_primitive", "CrossEncoderReranker")))
    return {
        "enabled": rerank_enabled and reranker_primitive.lower().strip() not in {"none", "off", "disabled"},
        "primitive": reranker_primitive,
        "query_text": options.get("rerank_query_text"),
    }


def build_retrieval_plan_explain(
    *,
    route: str,
    pipeline: RetrievalPipelineSpec,
    options: Optional[Dict[str, Any]] = None,
    pipeline_resolution: Optional[Dict[str, Any]] = None,
    lane_state: Optional[Dict[str, Any]] = None,
    route_executor: Optional[Dict[str, Any]] = None,
    lexical_capability_plan: Optional[Dict[str, Any]] = None,
    lexical_variant: Optional[Dict[str, Any]] = None,
    lexical_query_debug: Optional[Dict[str, Any]] = None,
    query_ir_v2: Optional[Dict[str, Any]] = None,
    projection_ir_v2: Optional[Dict[str, Any]] = None,
    compatibility_provenance: Optional[Dict[str, Any]] = None,
    compatibility_materializations: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    opts = dict(options or {})
    flags = dict(pipeline.flags or {})
    profile = get_deployment_profile()
    route_executor_payload = dict(route_executor or {})
    if query_ir_v2 is not None or projection_ir_v2 is not None:
        route_executor_payload = dict(route_executor_payload)
        route_executor_payload["planning_v2"] = {
            "query_ir_v2_template": dict(query_ir_v2 or route_executor_payload.get("planning_v2", {}).get("query_ir_v2_template") or {}),
            "projection_ir_v2": dict(projection_ir_v2 or route_executor_payload.get("planning_v2", {}).get("projection_ir_v2") or {}),
            **{
                key: value
                for key, value in dict(route_executor_payload.get("planning_v2") or {}).items()
                if key not in {"query_ir_v2_template", "projection_ir_v2"}
            },
        }
    effective_planning_v2 = instantiate_route_planning_v2(route_executor_payload)
    effective_query_ir_v2: Dict[str, Any] = dict(effective_planning_v2.get("query_ir_v2_template") or {})
    effective_projection_ir_v2: Dict[str, Any] = dict(effective_planning_v2.get("projection_ir_v2") or {})

    return {
        "route": str(route),
        "pipeline": {
            "pipeline_id": pipeline.pipeline_id,
            "pipeline_version": pipeline.version,
            "source": (pipeline_resolution or {}).get("source"),
            "resolution": dict(pipeline_resolution or {}),
            "flags": flags,
            "budgets": dict(pipeline.budgets or {}),
            "stages": [
                {
                    "stage_id": stage.stage_id,
                    "primitive_id": stage.primitive_id,
                    "enabled": bool(stage.enabled),
                    "config": dict(stage.config or {}),
                    "adapter": resolve_retrieval_adapter(stage.primitive_id, profile=profile).to_payload(),
                }
                for stage in pipeline.stages
            ],
        },
        "effective": {
            "fusion": _effective_fusion(options=opts, flags=flags),
            "reranker": _effective_reranker(options=opts, flags=flags),
            "limit": int(opts.get("limit", 0)),
            "limits": {
                "limit_bm25": opts.get("limit_bm25"),
                "limit_similarity": opts.get("limit_similarity"),
                "limit_sparse": opts.get("limit_sparse"),
            },
            "lane_state": dict(lane_state or {}),
            "profile": {
                "id": profile.id,
                "backend_stack": {
                    "authority": profile.backend_stack.authority,
                    "lexical": profile.backend_stack.lexical,
                    "dense": profile.backend_stack.dense,
                    "sparse": profile.backend_stack.sparse,
                    "graph": profile.backend_stack.graph,
                },
            },
            **({"route_executor": route_executor_payload} if route_executor is not None else {}),
            **({"query_ir_v2": effective_query_ir_v2} if effective_query_ir_v2 else {}),
            **({"projection_ir_v2": effective_projection_ir_v2} if effective_projection_ir_v2 else {}),
            **(
                {"lexical_capability_plan": dict(lexical_capability_plan)}
                if lexical_capability_plan is not None
                else {}
            ),
            **(
                {"lexical_variant": dict(lexical_variant)}
                if lexical_variant is not None
                else {}
            ),
            **(
                {"lexical_query_debug": dict(lexical_query_debug)}
                if lexical_query_debug is not None
                else {}
            ),
            **(
                {"compatibility_provenance": dict(compatibility_provenance)}
                if compatibility_provenance is not None
                else {}
            ),
            **(
                {"compatibility_materializations": dict(compatibility_materializations)}
                if compatibility_materializations is not None
                else {}
            ),
        },
    }

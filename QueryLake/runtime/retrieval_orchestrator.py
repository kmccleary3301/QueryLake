from __future__ import annotations

import time
from typing import Dict, List, Optional

from QueryLake.canon.runtime import (
    build_canon_bridge_metadata,
    build_shadow_replay_bundle,
    build_shadow_trace_export,
    build_shadow_execution_report,
    build_querylake_shadow_diff,
    execute_querylake_pipeline_in_canon_shadow,
    persist_shadow_execution_report,
    persist_shadow_replay_bundle,
    persist_shadow_trace_export,
)
from QueryLake.runtime.db_compat import get_deployment_profile
from QueryLake.runtime.retrieval_lanes import resolve_retrieval_adapter
from QueryLake.typing.retrieval_primitives import (
    ContextPackingPrimitive,
    FusionPrimitive,
    RetrievalExecutionResult,
    RetrievalPipelineSpec,
    RetrievalRequest,
    RetrievalStageTrace,
    RetrieverPrimitive,
    RerankerPrimitive,
)


class PipelineOrchestrator:
    def __init__(self) -> None:
        pass

    @staticmethod
    def _acl_filter(
        request: RetrievalRequest,
        candidates: List,
        *,
        stage: str,
        traces: List[RetrievalStageTrace],
    ) -> List:
        if len(request.collection_ids) == 0:
            return candidates
        allowed_collections = {str(v) for v in request.collection_ids if isinstance(v, str) and len(v) > 0}
        if len(allowed_collections) == 0:
            return candidates
        allow_unscoped = bool(request.options.get("allow_unscoped_candidates", False))
        t_1 = time.time()
        filtered = []
        for candidate in candidates:
            md = candidate.metadata if isinstance(candidate.metadata, dict) else {}
            collection_id = md.get("collection_id")
            if isinstance(collection_id, str) and collection_id in allowed_collections:
                filtered.append(candidate)
                continue
            if collection_id is None and allow_unscoped:
                filtered.append(candidate)
        t_2 = time.time()
        traces.append(
            RetrievalStageTrace(
                stage=f"acl:{stage}",
                duration_ms=(t_2 - t_1) * 1000.0,
                input_count=len(candidates),
                output_count=len(filtered),
                details={
                    "allowed_collections": sorted(allowed_collections),
                    "dropped_count": max(0, len(candidates) - len(filtered)),
                },
            )
        )
        return filtered

    @staticmethod
    def _preflight_validate(
        request: RetrievalRequest,
        pipeline: RetrievalPipelineSpec,
        *,
        traces: List[RetrievalStageTrace],
    ) -> None:
        t_1 = time.time()
        errors: List[str] = []
        warnings: List[str] = []

        if len(request.query_text.strip()) == 0:
            errors.append("query_text_empty")
        if len(request.collection_ids) > 0 and any(
            not isinstance(v, str) or len(v.strip()) == 0 for v in request.collection_ids
        ):
            errors.append("collection_ids_invalid")

        limit = request.options.get("limit", None)
        if limit is not None:
            try:
                if int(limit) < 0:
                    errors.append("limit_negative")
            except Exception:
                errors.append("limit_not_int")
        offset = request.options.get("offset", None)
        if offset is not None:
            try:
                if int(offset) < 0:
                    errors.append("offset_negative")
            except Exception:
                errors.append("offset_not_int")

        for key, value in request.budgets.items():
            if not isinstance(value, (int, float)):
                warnings.append(f"budget_non_numeric:{key}")
            elif float(value) < 0:
                errors.append(f"budget_negative:{key}")

        stage_ids = [stage.stage_id for stage in pipeline.stages]
        if len(stage_ids) != len(set(stage_ids)):
            errors.append("duplicate_stage_id")

        t_2 = time.time()
        traces.append(
            RetrievalStageTrace(
                stage="policy_preflight",
                duration_ms=(t_2 - t_1) * 1000.0,
                input_count=None,
                output_count=None,
                details={
                    "valid": len(errors) == 0,
                    "errors": errors,
                    "warnings": warnings,
                    "pipeline_id": pipeline.pipeline_id,
                    "pipeline_version": pipeline.version,
                    "route_id": str(request.query_ir_v2.get("route_id") or request.route or ""),
                    "representation_scope_id": str(
                        request.query_ir_v2.get("representation_scope_id")
                        or request.projection_ir_v2.get("representation_scope_id")
                        or ""
                    ),
                    "planning_surface": str(
                        request.projection_ir_v2.get("metadata", {}).get("planning_surface")
                        or request.query_ir_v2.get("metadata", {}).get("planning_surface")
                        or "route_resolution"
                    ),
                },
            )
        )
        if len(errors) > 0 and bool(request.options.get("enforce_policy_validation", False)):
            raise ValueError(f"Retrieval policy preflight failed: {', '.join(errors)}")

    async def run(
        self,
        request: RetrievalRequest,
        pipeline: RetrievalPipelineSpec,
        *,
        retrievers: Dict[str, RetrieverPrimitive],
        fusion: Optional[FusionPrimitive] = None,
        reranker: Optional[RerankerPrimitive] = None,
        packer: Optional[ContextPackingPrimitive] = None,
    ) -> RetrievalExecutionResult:
        traces: List[RetrievalStageTrace] = []
        candidates_by_source = {}
        self._preflight_validate(request, pipeline, traces=traces)

        canon_bridge = None
        if bool(request.options.get("canon_shadow_compile", False) or request.options.get("explain_plan", False)):
            t_bridge_1 = time.time()
            route_value = str(request.query_ir_v2.get("route_id") or request.route or "")
            canon_bridge = build_canon_bridge_metadata(
                route=route_value,
                pipeline=pipeline,
                options=request.options,
            )
            t_bridge_2 = time.time()
            traces.append(
                RetrievalStageTrace(
                    stage="canon_bridge_compile",
                    duration_ms=(t_bridge_2 - t_bridge_1) * 1000.0,
                    input_count=len(pipeline.stages),
                    output_count=int(canon_bridge.get("node_count", 0)) if isinstance(canon_bridge, dict) else None,
                    details={
                        "available": bool((canon_bridge or {}).get("available", False)),
                        "graph_id": (canon_bridge or {}).get("graph_id"),
                        "node_count": (canon_bridge or {}).get("node_count"),
                        "pipeline_id": pipeline.pipeline_id,
                    },
                )
            )

        for stage in pipeline.stages:
            if not stage.enabled:
                continue
            primitive = retrievers.get(stage.stage_id)
            if primitive is None:
                continue
            try:
                adapter_resolution = resolve_retrieval_adapter(
                    stage.primitive_id,
                    profile=get_deployment_profile(),
                ).to_payload()
            except Exception:
                adapter_resolution = {
                    "adapter_id": None,
                    "backend": None,
                    "implemented": False,
                    "lane_family": "unresolved",
                    "primitive_id": str(stage.primitive_id),
                }
            stage_request = request.model_copy(deep=True)
            stage_request.options = {**request.options, **stage.config}
            t_1 = time.time()
            candidates = await primitive.retrieve(stage_request)
            candidates = self._acl_filter(
                request,
                candidates,
                stage=f"retrieve:{stage.stage_id}",
                traces=traces,
            )
            t_2 = time.time()
            candidates_by_source[stage.stage_id] = candidates
            traces.append(
                RetrievalStageTrace(
                    stage=f"retrieve:{stage.stage_id}",
                    duration_ms=(t_2 - t_1) * 1000.0,
                    input_count=0,
                    output_count=len(candidates),
                    details={
                        "primitive_id": stage.primitive_id,
                        "adapter": adapter_resolution,
                        "route_id": str(request.query_ir_v2.get("route_id") or request.route or ""),
                        "representation_scope_id": str(
                            request.query_ir_v2.get("representation_scope_id")
                            or request.projection_ir_v2.get("representation_scope_id")
                            or ""
                        ),
                        "planning_surface": str(
                            request.projection_ir_v2.get("metadata", {}).get("planning_surface")
                            or request.query_ir_v2.get("metadata", {}).get("planning_surface")
                            or "route_resolution"
                        ),
                        "projection_buildability_class": str(
                            request.projection_ir_v2.get("buildability_class") or ""
                        ),
                    },
                )
            )

        # Fusion (or fallback concat in deterministic stage order)
        if fusion is not None:
            t_1 = time.time()
            fused = fusion.fuse(request, candidates_by_source)
            t_2 = time.time()
            traces.append(
                RetrievalStageTrace(
                    stage="fusion",
                    duration_ms=(t_2 - t_1) * 1000.0,
                    input_count=sum(len(v) for v in candidates_by_source.values()),
                    output_count=len(fused),
                    details={"primitive_id": fusion.primitive_id},
                )
            )
        else:
            fused = []
            for stage in pipeline.stages:
                if stage.stage_id in candidates_by_source:
                    fused.extend(candidates_by_source[stage.stage_id])

        # Optional rerank stage
        if reranker is not None:
            fused = self._acl_filter(
                request,
                fused,
                stage="pre_rerank",
                traces=traces,
            )
            t_1 = time.time()
            fused = await reranker.rerank(request, fused)
            t_2 = time.time()
            traces.append(
                RetrievalStageTrace(
                    stage="rerank",
                    duration_ms=(t_2 - t_1) * 1000.0,
                    input_count=len(fused),
                    output_count=len(fused),
                    details={"primitive_id": reranker.primitive_id},
                )
            )

        # Optional pack stage
        if packer is not None:
            t_1 = time.time()
            packed = packer.pack(request, fused)
            t_2 = time.time()
            traces.append(
                RetrievalStageTrace(
                    stage="pack",
                    duration_ms=(t_2 - t_1) * 1000.0,
                    input_count=len(fused),
                    output_count=len(packed),
                    details={"primitive_id": packer.primitive_id},
                )
            )
            fused = packed

        limit = int(request.options.get("limit", 0))
        if limit > 0:
            fused = fused[:limit]

        metadata = {
            "candidate_sources": list(candidates_by_source.keys()),
            "query_ir_v2": dict(request.query_ir_v2 or {}),
            "projection_ir_v2": dict(request.projection_ir_v2 or {}),
            **({"canon_bridge": dict(canon_bridge)} if isinstance(canon_bridge, dict) else {}),
        }

        result = RetrievalExecutionResult(
            pipeline_id=pipeline.pipeline_id,
            pipeline_version=pipeline.version,
            candidates=fused,
            traces=traces,
            metadata=metadata,
        )

        if bool(request.options.get("canon_shadow_execute", False)):
            canon_shadow_result = await execute_querylake_pipeline_in_canon_shadow(
                request=request,
                pipeline=pipeline,
                retrievers=retrievers,
                fusion=fusion,
                reranker=reranker,
            )
            shadow_diff = build_querylake_shadow_diff(
                request=request,
                pipeline=pipeline,
                profile_id=get_deployment_profile().id,
                legacy_result=result,
                canon_result=canon_shadow_result,
            )
            canon_shadow_payload = {
                "graph_id": canon_shadow_result.metadata.get("canon_graph_id"),
                "bridge": canon_shadow_result.metadata.get("canon_bridge"),
                "shadow_diff": shadow_diff,
            }
            report_dir = request.options.get("canon_shadow_report_dir")
            if isinstance(report_dir, str) and len(report_dir.strip()) > 0:
                report = build_shadow_execution_report(
                    report_id=str(request.options.get("canon_shadow_report_id") or f"canon-shadow-{pipeline.pipeline_id}"),
                    request=request,
                    pipeline=pipeline,
                    profile_id=get_deployment_profile().id,
                    legacy_result=result,
                    canon_result=canon_shadow_result,
                    shadow_diff=shadow_diff,
                    top_k_snapshot=int(request.options.get("limit", 10) or 10),
                )
                canon_shadow_payload["report"] = persist_shadow_execution_report(
                    report=report,
                    output_dir=report_dir,
                )
            bundle_dir = request.options.get("canon_shadow_bundle_dir")
            if isinstance(bundle_dir, str) and len(bundle_dir.strip()) > 0:
                bundle_id = str(request.options.get("canon_shadow_bundle_id") or f"canon-shadow-bundle-{pipeline.pipeline_id}")
                replay_bundle = build_shadow_replay_bundle(
                    bundle_id=bundle_id,
                    request=request,
                    pipeline=pipeline,
                    legacy_result=result,
                    canon_result=canon_shadow_result,
                    shadow_diff=shadow_diff,
                )
                trace_export = build_shadow_trace_export(
                    export_id=f"{bundle_id}-traces",
                    request=request,
                    pipeline=pipeline,
                    canon_result=canon_shadow_result,
                )
                canon_shadow_payload["replay_bundle"] = persist_shadow_replay_bundle(
                    bundle=replay_bundle,
                    output_dir=bundle_dir,
                )
                canon_shadow_payload["trace_export"] = persist_shadow_trace_export(
                    export=trace_export,
                    output_dir=bundle_dir,
                )
            result.metadata["canon_shadow"] = canon_shadow_payload
            result.traces.extend(canon_shadow_result.traces)

        return result

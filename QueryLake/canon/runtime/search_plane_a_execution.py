from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from QueryLake.canon.compiler.querylake_route_compiler import normalize_querylake_route_pipeline
from QueryLake.canon.control.route_serving_registry import (
    load_route_serving_registry,
    resolve_route_serving_state,
)
from QueryLake.canon.package.registry import load_graph_package_registry, resolve_selected_graph_package
from QueryLake.canon.control.pointer_registry import load_pointer_registry
from QueryLake.runtime.db_compat import build_profile_execution_target_payload, get_deployment_profile
from QueryLake.runtime.retrieval_pipeline_runtime import default_pipeline_for_route
from QueryLake.runtime.retrieval_route_executors import (
    OpenSearchDocumentChunkBM25RouteExecutor,
    OpenSearchDocumentChunkHybridRouteExecutor,
    OpenSearchFileChunkRouteExecutor,
    ResolvedRouteExecutor,
    resolve_search_bm25_route_executor,
    resolve_search_file_chunks_route_executor,
    resolve_search_hybrid_route_executor,
)
from QueryLake.typing.retrieval_primitives import RetrievalPipelineSpec


_ROUTE_TO_DEFAULT_PIPELINE_ROUTE = {
    "search_hybrid.document_chunk": "search_hybrid",
    "search_bm25.document_chunk": "search_bm25.document_chunk",
    "search_file_chunks": "search_file_chunks",
}
_SOURCE_SEARCH_PLANE_PROFILE_ID = "aws_aurora_pg_opensearch_v1"
_AUTHORITATIVE_TARGET_ROUTES = {
    "search_bm25.document_chunk",
    "search_file_chunks",
    "search_hybrid.document_chunk",
}


def _normalize_route(route_id: str) -> str:
    return _ROUTE_TO_DEFAULT_PIPELINE_ROUTE.get(str(route_id), str(route_id))


def _infer_hybrid_lane_flags(pipeline: Optional[RetrievalPipelineSpec]) -> tuple[bool, bool, bool]:
    if pipeline is None:
        return True, True, False
    stage_ids = {str(stage.stage_id) for stage in pipeline.stages if stage.enabled}
    primitive_ids = {str(stage.primitive_id) for stage in pipeline.stages if stage.enabled}
    use_bm25 = "bm25" in stage_ids or any("BM25" in primitive for primitive in primitive_ids)
    use_similarity = "dense" in stage_ids or any("Dense" in primitive for primitive in primitive_ids)
    use_sparse = "sparse" in stage_ids or any("Sparse" in primitive for primitive in primitive_ids)
    return use_bm25, use_similarity, use_sparse


def _resolve_source_search_plane_executor(
    *,
    route_id: str,
    compile_options: Optional[dict[str, Any]] = None,
) -> ResolvedRouteExecutor:
    normalized_route = str(route_id)
    pipeline = default_pipeline_for_route(_normalize_route(normalized_route))
    if pipeline is not None:
        pipeline = normalize_querylake_route_pipeline(
            route=normalized_route,
            pipeline=pipeline,
            options=dict(compile_options or {}),
        )
    source_profile = get_deployment_profile(_SOURCE_SEARCH_PLANE_PROFILE_ID)
    if normalized_route == "search_hybrid.document_chunk":
        use_bm25, use_similarity, use_sparse = _infer_hybrid_lane_flags(pipeline)
        return resolve_search_hybrid_route_executor(
            use_bm25=use_bm25,
            use_similarity=use_similarity,
            use_sparse=use_sparse,
            profile=source_profile,
        )
    if normalized_route == "search_bm25.document_chunk":
        return resolve_search_bm25_route_executor(
            table="document_chunk",
            profile=source_profile,
        )
    if normalized_route == "search_file_chunks":
        return resolve_search_file_chunks_route_executor(profile=source_profile)
    raise ValueError(f"Unsupported Phase 1A route for Search Plane A execution: {normalized_route}")


@dataclass(frozen=True)
class SearchPlaneAExecutionResolution:
    route_id: str
    profile_id: str
    source_search_profile_id: str
    execution_mode: str
    selected_package_resolved: bool
    shadow_executable: bool
    primary_ready: bool
    executor_id: str
    authoritative: bool = False
    migration_consulted: bool = False
    compile_options: dict[str, Any] = field(default_factory=dict)
    projection_descriptors: list[str] = field(default_factory=list)
    search_plane_blockers: list[str] = field(default_factory=list)
    authority_blockers: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    profile_execution_target: dict[str, Any] = field(default_factory=dict)
    selected_package: dict[str, Any] = field(default_factory=dict)
    source_resolution: dict[str, Any] = field(default_factory=dict)
    route_serving_state: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResolvedSearchPlaneAExecutionContract:
    resolution: SearchPlaneAExecutionResolution
    executor: Any

    def to_payload(self) -> dict[str, Any]:
        return self.resolution.to_payload()

    def execute(self, database: Any, **kwargs: Any) -> Any:
        if not self.resolution.shadow_executable:
            raise RuntimeError(
                f"Search Plane A execution contract for route '{self.resolution.route_id}' on profile "
                f"'{self.resolution.profile_id}' is not shadow-executable."
            )
        return self.executor.execute(database, **kwargs)


def resolve_search_plane_a_execution_contract(
    *,
    route_id: str,
    profile_id: str,
    package_registry_path: str,
    pointer_registry_path: str,
    route_serving_registry_path: str | None = None,
    mode: str = "shadow",
) -> ResolvedSearchPlaneAExecutionContract:
    effective_profile = get_deployment_profile(profile_id)
    package_registry = load_graph_package_registry(package_registry_path)
    pointer_registry = load_pointer_registry(pointer_registry_path)
    selected_package = resolve_selected_graph_package(
        registry=package_registry,
        pointer_registry=pointer_registry,
        route_id=route_id,
        profile_id=effective_profile.id,
        mode=mode,
    )
    compile_options = dict(selected_package.get("package", {}).get("compile_options") or {})
    recommendations: list[str] = []
    search_plane_blockers: list[str] = []
    authority_blockers: list[str] = []
    executor: Any = None
    source_resolution_payload: dict[str, Any] = {}
    executor_id = ""
    projection_descriptors: list[str] = []
    shadow_executable = False
    primary_ready = False
    authoritative = False
    migration_consulted = False
    route_serving_state: dict[str, Any] = {}

    if not bool(selected_package.get("resolved")):
        search_plane_blockers.append("selected_package_missing")
        recommendations.append("register_and_select_graph_package_before_execution")
    else:
        source_resolved = _resolve_source_search_plane_executor(
            route_id=route_id,
            compile_options=compile_options,
        )
        source_resolution_payload = source_resolved.to_payload()
        executor = source_resolved.executor
        executor_id = str(source_resolution_payload.get("executor_id") or getattr(executor, "executor_id", ""))
        projection_descriptors = list(source_resolution_payload.get("projection_descriptors") or [])
        if not bool(source_resolution_payload.get("implemented", False)):
            search_plane_blockers.append("route_executor_not_implemented_on_search_plane_source_profile")
        planning_v2 = dict(source_resolution_payload.get("planning_v2") or {})
        if not bool(planning_v2.get("runtime_ready", source_resolution_payload.get("implemented", False))):
            blockers = list(planning_v2.get("runtime_blockers") or [])
            if blockers:
                search_plane_blockers.extend(str(value) for value in blockers)
            else:
                search_plane_blockers.append("search_plane_runtime_not_ready")
        if len(search_plane_blockers) == 0:
            shadow_executable = True
            recommendations.append("reuse_current_opensearch_search_plane_via_canon_shadow_executor")

    execution_mode = "blocked"
    if shadow_executable:
        if effective_profile.id == _SOURCE_SEARCH_PLANE_PROFILE_ID:
            execution_mode = "legacy_route_executor_passthrough"
        elif effective_profile.id == "planetscale_opensearch_v1":
            if route_serving_registry_path and mode in {"candidate_primary", "primary"} and str(route_id) in _AUTHORITATIVE_TARGET_ROUTES:
                route_serving_registry = load_route_serving_registry(route_serving_registry_path)
                route_serving_state = resolve_route_serving_state(
                    registry=route_serving_registry,
                    profile_id=effective_profile.id,
                    route_id=str(route_id),
                    mode=str(mode),
                )
                migration_consulted = True
                if bool(route_serving_state.get("resolved")):
                    apply_state = dict(route_serving_state.get("apply_state") or {})
                    projections = [str(value) for value in list(apply_state.get("projection_descriptors") or []) if str(value or "")]
                    if len(projections) == 0:
                        authority_blockers.append("route_apply_state_projection_missing")
                    else:
                        if str(route_id) == "search_hybrid.document_chunk":
                            if not bool(compile_options.get("disable_sparse")):
                                authority_blockers.append("hybrid_authoritative_target_requires_sparse_disabled_package")
                                recommendations.append("recompile_hybrid_package_with_disable_sparse_true")
                            elif "document_chunk_sparse_projection_v1" in set(projections):
                                authority_blockers.append("hybrid_authoritative_target_sparse_projection_not_allowed")
                                recommendations.append("remove_sparse_projection_from_hybrid_target_apply_state")
                            else:
                                executor = OpenSearchDocumentChunkHybridRouteExecutor(
                                    projection_descriptors=tuple(projections),
                                )
                        elif str(route_id) == "search_file_chunks":
                            executor = OpenSearchFileChunkRouteExecutor(projection_id=projections[0])
                        else:
                            executor = OpenSearchDocumentChunkBM25RouteExecutor(projection_id=projections[0])
                        if executor is not None and len(authority_blockers) == 0:
                            executor_id = executor.executor_id
                            projection_descriptors = projections
                            source_resolution_payload = {}
                            search_plane_blockers = []
                            authority_blockers = []
                            execution_mode = "canon_target_profile_authoritative_executor"
                            authoritative = True
                            primary_ready = str(mode) == "primary"
                            recommendations.append("authoritative_target_execution_uses_route_scoped_serving_truth")
                else:
                    authority_blockers.extend(str(value) for value in list(route_serving_state.get("blockers") or []))
                    recommendations.append("complete_route_scoped_migrated_truth_before_authoritative_target_serving")
            if execution_mode == "blocked":
                execution_mode = "canon_target_profile_shadow_executor"
                authority_blockers.extend(
                    [
                        "authority_plane_not_migrated",
                        "control_plane_not_migrated",
                    ]
                )
                recommendations.append("target_profile_search_plane_is_shadow_executable_but_not_primary_ready")
        else:
            execution_mode = "canon_search_plane_shadow_executor"

    resolution = SearchPlaneAExecutionResolution(
        route_id=str(route_id),
        profile_id=effective_profile.id,
        source_search_profile_id=_SOURCE_SEARCH_PLANE_PROFILE_ID,
        execution_mode=execution_mode,
        selected_package_resolved=bool(selected_package.get("resolved")),
        shadow_executable=shadow_executable,
        primary_ready=primary_ready,
        authoritative=authoritative,
        migration_consulted=migration_consulted,
        executor_id=executor_id,
        compile_options=compile_options,
        projection_descriptors=projection_descriptors,
        search_plane_blockers=search_plane_blockers,
        authority_blockers=authority_blockers,
        recommendations=recommendations,
        profile_execution_target=build_profile_execution_target_payload(effective_profile),
        selected_package=selected_package,
        source_resolution=source_resolution_payload,
        route_serving_state=route_serving_state,
    )
    return ResolvedSearchPlaneAExecutionContract(resolution=resolution, executor=executor)


def build_search_plane_a_execution_contract(
    *,
    route_id: str,
    profile_id: str,
    package_registry_path: str,
    pointer_registry_path: str,
    route_serving_registry_path: str | None = None,
    mode: str = "shadow",
) -> dict[str, Any]:
    return resolve_search_plane_a_execution_contract(
        route_id=route_id,
        profile_id=profile_id,
        package_registry_path=package_registry_path,
        pointer_registry_path=pointer_registry_path,
        route_serving_registry_path=route_serving_registry_path,
        mode=mode,
    ).to_payload()

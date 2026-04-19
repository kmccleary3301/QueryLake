from __future__ import annotations

from QueryLake.canon.compiler.retrieval_pipeline_graph import (
    RetrievalPipelineCompileError,
    compile_retrieval_pipeline_to_graph,
)
from QueryLake.runtime.retrieval_pipeline_runtime import default_pipeline_for_route
from QueryLake.typing.retrieval_primitives import RetrievalPipelineSpec


_ROUTE_TO_DEFAULT_PIPELINE_ROUTE = {
    "search_hybrid.document_chunk": "search_hybrid",
    "search_bm25.document_chunk": "search_bm25.document_chunk",
    "search_file_chunks": "search_file_chunks",
}


def normalize_querylake_route_pipeline(
    *,
    route: str,
    pipeline: RetrievalPipelineSpec,
    options: dict | None = None,
) -> RetrievalPipelineSpec:
    effective_route = str(route or "").strip()
    opts = dict(options or {})
    if effective_route != "search_hybrid.document_chunk":
        return pipeline
    if not bool(opts.get("disable_sparse", False)):
        return pipeline
    cloned = pipeline.model_copy(deep=True)
    cloned.stages = [
        stage.model_copy(update={"enabled": False}) if str(stage.stage_id) == "sparse" else stage.model_copy(deep=True)
        for stage in cloned.stages
    ]
    metadata = dict(cloned.flags or {})
    metadata["disable_sparse"] = True
    cloned.flags = metadata
    return cloned


class QueryLakeRouteCompileError(ValueError):
    def __init__(self, message: str, route: str):
        super().__init__(message)
        self.route = route

    def __str__(self) -> str:
        return f"route={self.route}: {super().__str__()}"


def compile_querylake_route_to_graph(
    *,
    route: str,
    pipeline: RetrievalPipelineSpec | None = None,
    options: dict | None = None,
):
    effective_route = str(route or "").strip()
    if not effective_route:
        raise QueryLakeRouteCompileError("route must be non-empty", route="")

    pipeline_source_route = _ROUTE_TO_DEFAULT_PIPELINE_ROUTE.get(effective_route, effective_route)
    effective_pipeline = pipeline or default_pipeline_for_route(pipeline_source_route)
    if effective_pipeline is None:
        raise QueryLakeRouteCompileError(
            "no default retrieval pipeline is registered for this route",
            route=effective_route,
        )
    normalized_pipeline = normalize_querylake_route_pipeline(
        route=effective_route,
        pipeline=effective_pipeline,
        options=options,
    )

    try:
        return compile_retrieval_pipeline_to_graph(
            route=effective_route,
            pipeline=normalized_pipeline,
            options=options,
        )
    except RetrievalPipelineCompileError as exc:
        raise QueryLakeRouteCompileError(str(exc), route=effective_route) from exc

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any, Iterable, Optional

from QueryLake.canon.compiler.querylake_route_compiler import compile_querylake_route_to_graph
from QueryLake.canon.models import GraphSpec
from QueryLake.canon.runtime.profile_readiness import build_phase1a_search_plane_a_transition_bundle
from QueryLake.runtime.retrieval_pipeline_runtime import default_pipeline_for_route
from QueryLake.typing.retrieval_primitives import RetrievalPipelineSpec


_ROUTE_TO_DEFAULT_PIPELINE_ROUTE = {
    "search_hybrid.document_chunk": "search_hybrid",
    "search_bm25.document_chunk": "search_bm25.document_chunk",
    "search_file_chunks": "search_file_chunks",
}


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _effect_summary(graph: GraphSpec) -> dict[str, int]:
    counts: dict[str, int] = {}
    for node in graph.nodes:
        effect_name = str(node.effect_class.value)
        counts[effect_name] = counts.get(effect_name, 0) + 1
    return counts


def build_graph_package_bundle(
    *,
    graph: GraphSpec,
    route_id: str,
    pipeline: RetrievalPipelineSpec,
    package_revision: str,
    profile_targets: Iterable[str] | None = None,
    metadata: Optional[dict[str, Any]] = None,
    include_search_plane_transition: bool = True,
) -> dict[str, Any]:
    profile_target_list = [str(value) for value in (profile_targets or ["aws_aurora_pg_opensearch_v1", "planetscale_opensearch_v1"])]
    payload = {
        "schema_version": "canon_graph_package_bundle_v1",
        "generated_at": _utc_now(),
        "package_id": f"canon-package-{graph.graph_id}",
        "package_revision": package_revision,
        "route_id": route_id,
        "pipeline": {
            "pipeline_id": pipeline.pipeline_id,
            "version": pipeline.version,
            "stage_ids": [stage.stage_id for stage in pipeline.stages],
            "primitive_ids": [stage.primitive_id for stage in pipeline.stages],
        },
        "graph": {
            "graph_id": graph.graph_id,
            "graph_name": graph.graph_name,
            "node_count": len(graph.nodes),
            "requested_outputs": [output.key for output in graph.requested_outputs],
            "nodes": [node.to_canonical_dict() for node in graph.nodes],
            "effect_summary": _effect_summary(graph),
        },
        "profile_targets": profile_target_list,
        "metadata": dict(metadata or {}),
    }
    if include_search_plane_transition:
        payload["search_plane_a_transition"] = build_phase1a_search_plane_a_transition_bundle(
            source_profile_id="aws_aurora_pg_opensearch_v1",
            target_profile_id="planetscale_opensearch_v1",
            routes=[route_id],
        )
    return payload


def build_route_graph_package_bundle(
    *,
    route: str,
    package_revision: str,
    pipeline: RetrievalPipelineSpec | None = None,
    options: Optional[dict[str, Any]] = None,
    profile_targets: Iterable[str] | None = None,
    metadata: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    effective_pipeline = pipeline or default_pipeline_for_route(_ROUTE_TO_DEFAULT_PIPELINE_ROUTE.get(route, route))
    if effective_pipeline is None:
        raise ValueError(f"No default pipeline for route '{route}'")
    graph = compile_querylake_route_to_graph(route=route, pipeline=effective_pipeline, options=options or {})
    return build_graph_package_bundle(
        graph=graph,
        route_id=route,
        pipeline=effective_pipeline,
        package_revision=package_revision,
        profile_targets=profile_targets,
        metadata=metadata,
    )


def persist_graph_package_bundle(
    *,
    bundle: dict[str, Any],
    output_dir: str | Path,
) -> dict[str, str]:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    package_id = str(bundle.get("package_id") or "canon-package")
    path = target_dir / f"{package_id}.json"
    path.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "package_id": package_id,
        "path": str(path),
    }


def load_graph_package_bundle(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if str(payload.get("schema_version") or "") != "canon_graph_package_bundle_v1":
        raise ValueError(f"Unsupported graph package schema: {payload.get('schema_version')}")
    return payload

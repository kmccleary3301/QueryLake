#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.db_compat import DEPLOYMENT_PROFILES, build_capabilities_payload, build_profile_diagnostics_payload
from QueryLake.runtime.profile_bringup import build_profile_bringup_payload
from QueryLake.runtime.projection_refresh import mark_projection_build_ready
from QueryLake.runtime.retrieval_explain import build_retrieval_plan_explain
from QueryLake.runtime.retrieval_orchestrator import PipelineOrchestrator
from QueryLake.runtime.retrieval_route_executors import (
    resolve_search_bm25_route_executor,
    resolve_search_file_chunks_route_executor,
    resolve_search_hybrid_route_executor,
)
from QueryLake.typing.retrieval_primitives import (
    RetrievalCandidate,
    RetrievalPipelineSpec,
    RetrievalPipelineStage,
    RetrievalRequest,
)


ROUTES = (
    "search_bm25.document_chunk",
    "search_hybrid.document_chunk",
    "search_file_chunks",
)


@contextmanager
def _temporary_env(values: Dict[str, str]) -> Iterator[None]:
    previous: Dict[str, str | None] = {}
    try:
        for key, value in values.items():
            previous[key] = os.environ.get(key)
            os.environ[key] = value
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _seed_ready_projections(profile_id: str, metadata_store_path: str) -> None:
    if profile_id == "aws_aurora_pg_opensearch_v1":
        lexical_backend = "opensearch"
        dense_backend = "opensearch"
    elif profile_id == "sqlite_fts5_dense_sidecar_local_v1":
        lexical_backend = "sqlite_fts5"
        dense_backend = "local_dense_sidecar"
    else:
        return
    for projection_id, lane_family, target_backend in (
        ("document_chunk_lexical_projection_v1", "lexical", lexical_backend),
        ("document_chunk_dense_projection_v1", "dense", dense_backend),
        ("file_chunk_lexical_projection_v1", "lexical", lexical_backend),
    ):
        mark_projection_build_ready(
            projection_id=projection_id,
            projection_version="v1",
            profile_id=profile_id,
            lane_family=lane_family,
            target_backend=target_backend,
            build_revision=f"db_compat_v2_runtime_consistency:{profile_id}:{projection_id}",
            metadata={"source": "db_compat_v2_runtime_consistency"},
            path=metadata_store_path,
        )


def _resolve_route(route_id: str, profile):
    if route_id == "search_bm25.document_chunk":
        return resolve_search_bm25_route_executor(table="document_chunk", profile=profile)
    if route_id == "search_hybrid.document_chunk":
        return resolve_search_hybrid_route_executor(
            use_bm25=True,
            use_similarity=True,
            use_sparse=False,
            profile=profile,
        )
    if route_id == "search_file_chunks":
        return resolve_search_file_chunks_route_executor(profile=profile)
    raise KeyError(route_id)


def _pipeline_for_route(route_id: str) -> RetrievalPipelineSpec:
    if route_id == "search_hybrid.document_chunk":
        stages = [
            RetrievalPipelineStage(stage_id="bm25", primitive_id="BM25RetrieverParadeDB"),
            RetrievalPipelineStage(stage_id="dense", primitive_id="DenseRetrieverPGVector"),
        ]
    else:
        stages = [RetrievalPipelineStage(stage_id="bm25", primitive_id="BM25RetrieverParadeDB")]
    return RetrievalPipelineSpec(pipeline_id=f"{route_id}.v2", version="v2", stages=stages)


def _route_row_by_id(rows: List[dict], route_id: str) -> Dict[str, Any]:
    for row in rows:
        if str(row.get("route_id") or "") == route_id:
            return dict(row)
    raise KeyError(route_id)


class _FakeRetriever:
    primitive_id = "FakeRetriever"
    version = "v1"

    async def retrieve(self, request: RetrievalRequest) -> List[RetrievalCandidate]:
        return [
            RetrievalCandidate(
                content_id=f"{request.route}:candidate",
                text="stub",
                metadata={"collection_id": "col1"},
                provenance=[request.route],
            )
        ]


async def _run_orchestrated_snapshot(
    *,
    route_id: str,
    query_ir_v2: Dict[str, Any],
    projection_ir_v2: Dict[str, Any],
) -> Dict[str, Any]:
    pipeline = _pipeline_for_route(route_id)
    retrievers = {
        stage.stage_id: _FakeRetriever()
        for stage in pipeline.stages
    }
    request = RetrievalRequest(
        route=route_id,
        query_text="vapor recovery",
        collection_ids=["col1"],
        options={"limit": 5},
        query_ir_v2=dict(query_ir_v2),
        projection_ir_v2=dict(projection_ir_v2),
    )
    result = await PipelineOrchestrator().run(
        request=request,
        pipeline=pipeline,
        retrievers=retrievers,
        fusion=None,
        reranker=None,
        packer=None,
    )
    return {
        "metadata": dict(result.metadata or {}),
        "traces": [trace.model_dump() for trace in result.traces],
    }


def _route_snapshot(*, route_id: str, profile, diagnostics_payload: Dict[str, Any], bringup_payload: Dict[str, Any]) -> Dict[str, Any]:
    resolved = _resolve_route(route_id, profile)
    planning_v2 = dict(resolved.resolution.planning_v2 or {})
    query_ir_v2 = dict(planning_v2.get("query_ir_v2_template") or {})
    projection_ir_v2 = dict(planning_v2.get("projection_ir_v2") or {})

    diagnostics_executor = _route_row_by_id(list(diagnostics_payload.get("route_executors") or []), route_id)
    diagnostics_support = _route_row_by_id(list(diagnostics_payload.get("route_support_v2") or []), route_id)
    bringup_recovery = _route_row_by_id(list(bringup_payload.get("route_recovery") or []), route_id)

    explain_payload = build_retrieval_plan_explain(
        route=route_id,
        pipeline=_pipeline_for_route(route_id),
        options={"limit": 5},
        route_executor={
            "route_id": route_id,
            "executor_id": resolved.resolution.executor_id,
            "planning_v2": planning_v2,
        },
        query_ir_v2=query_ir_v2,
        projection_ir_v2=projection_ir_v2,
    )
    explain_effective = dict(explain_payload.get("effective") or {})
    explain_query_ir_v2 = dict(explain_effective.get("query_ir_v2") or {})
    explain_projection_ir_v2 = dict(explain_effective.get("projection_ir_v2") or {})
    orchestrated = asyncio.run(
        _run_orchestrated_snapshot(
            route_id=route_id,
            query_ir_v2=query_ir_v2,
            projection_ir_v2=projection_ir_v2,
        )
    )
    orchestrated_metadata = dict(orchestrated.get("metadata") or {})
    orchestrated_query_ir_v2 = dict(orchestrated_metadata.get("query_ir_v2") or {})
    orchestrated_projection_ir_v2 = dict(orchestrated_metadata.get("projection_ir_v2") or {})
    traces = list(orchestrated.get("traces") or [])
    preflight_trace = next(
        (trace for trace in traces if str(trace.get("stage") or "") == "policy_preflight"),
        {},
    )
    retrieve_traces = [
        trace for trace in traces if str(trace.get("stage") or "").startswith("retrieve:")
    ]
    preflight_details = dict(preflight_trace.get("details") or {})

    scope_ids = {
        "query": str(query_ir_v2.get("representation_scope_id") or ""),
        "projection": str(projection_ir_v2.get("representation_scope_id") or ""),
        "diagnostics_executor": str(diagnostics_executor.get("representation_scope_id") or ""),
        "diagnostics_support": str(diagnostics_support.get("representation_scope_id") or ""),
        "bringup": str(bringup_recovery.get("representation_scope_id") or ""),
        "explain_query": str(explain_query_ir_v2.get("representation_scope_id") or ""),
        "explain_projection": str(explain_projection_ir_v2.get("representation_scope_id") or ""),
        "orchestrated_query": str(orchestrated_query_ir_v2.get("representation_scope_id") or ""),
        "orchestrated_projection": str(orchestrated_projection_ir_v2.get("representation_scope_id") or ""),
        "orchestrated_preflight": str(preflight_details.get("representation_scope_id") or ""),
    }
    unique_scope_ids = {value for value in scope_ids.values() if value}
    if len(unique_scope_ids) != 1:
        raise AssertionError(f"{profile.id}:{route_id} scope mismatch: {scope_ids}")

    if str(query_ir_v2.get("route_id") or "") != route_id:
        raise AssertionError(f"{profile.id}:{route_id} query_ir_v2 route mismatch")
    if str(projection_ir_v2.get("route_id") or "") != route_id:
        raise AssertionError(f"{profile.id}:{route_id} projection_ir_v2 route mismatch")
    if str(explain_query_ir_v2.get("route_id") or "") != route_id:
        raise AssertionError(f"{profile.id}:{route_id} explain query_ir_v2 route mismatch")
    if str(explain_projection_ir_v2.get("route_id") or "") != route_id:
        raise AssertionError(f"{profile.id}:{route_id} explain projection_ir_v2 route mismatch")
    if str(orchestrated_query_ir_v2.get("route_id") or "") != route_id:
        raise AssertionError(f"{profile.id}:{route_id} orchestrated query_ir_v2 route mismatch")
    if str(orchestrated_projection_ir_v2.get("route_id") or "") != route_id:
        raise AssertionError(f"{profile.id}:{route_id} orchestrated projection_ir_v2 route mismatch")
    if str(preflight_details.get("route_id") or "") != route_id:
        raise AssertionError(f"{profile.id}:{route_id} preflight route_id mismatch")
    planning_surface = str(planning_v2.get("planning_surface") or "route_resolution")
    if planning_surface != "route_resolution":
        raise AssertionError(f"{profile.id}:{route_id} planning_surface mismatch: {planning_surface!r}")
    if str(preflight_details.get("planning_surface") or "route_resolution") != planning_surface:
        raise AssertionError(f"{profile.id}:{route_id} preflight planning_surface mismatch")
    for retrieve_trace in retrieve_traces:
        details = dict(retrieve_trace.get("details") or {})
        if str(details.get("route_id") or "") != route_id:
            raise AssertionError(f"{profile.id}:{route_id} retrieve trace route_id mismatch")
        if str(details.get("representation_scope_id") or "") != next(iter(unique_scope_ids)):
            raise AssertionError(f"{profile.id}:{route_id} retrieve trace scope mismatch")
        if str(details.get("planning_surface") or "route_resolution") != planning_surface:
            raise AssertionError(f"{profile.id}:{route_id} retrieve trace planning_surface mismatch")
    buildability_class = str(projection_ir_v2.get("buildability_class") or "")
    if not buildability_class:
        raise AssertionError(f"{profile.id}:{route_id} missing projection buildability_class")
    if str(orchestrated_projection_ir_v2.get("buildability_class") or "") != buildability_class:
        raise AssertionError(f"{profile.id}:{route_id} orchestrated projection buildability mismatch")
    strictness_policy = str(query_ir_v2.get("strictness_policy") or "")
    if not strictness_policy:
        raise AssertionError(f"{profile.id}:{route_id} missing strictness_policy")
    if str(orchestrated_query_ir_v2.get("strictness_policy") or "") != strictness_policy:
        raise AssertionError(f"{profile.id}:{route_id} orchestrated strictness mismatch")

    return {
        "route_id": route_id,
        "executor_id": resolved.resolution.executor_id,
        "support_state": resolved.resolution.support_state,
        "representation_scope_id": next(iter(unique_scope_ids)),
        "strictness_policy": strictness_policy,
        "planning_surface": planning_surface,
        "projection_buildability_class": buildability_class,
        "orchestrated_metadata_consistent": True,
        "orchestrated_trace_count": len(traces),
        "lane_intent": {
            "use_dense": bool(query_ir_v2.get("use_dense")),
            "use_sparse": bool(query_ir_v2.get("use_sparse")),
        },
        "capability_dependencies": list(diagnostics_support.get("capability_dependencies") or []),
        "lexical_support_class": str(
            bringup_recovery.get("lexical_support_class")
            or diagnostics_executor.get("lexical_support_class")
            or ""
        ),
        "runtime_ready": bool(bringup_recovery.get("runtime_ready")),
    }


def build_v2_runtime_consistency_payload(*, metadata_store_path: str) -> Dict[str, Any]:
    profile_rows: List[Dict[str, Any]] = []
    for profile_id in (
        "paradedb_postgres_gold_v1",
        "aws_aurora_pg_opensearch_v1",
        "sqlite_fts5_dense_sidecar_local_v1",
    ):
        profile = DEPLOYMENT_PROFILES[profile_id]
        env: Dict[str, str] = {}
        if profile_id == "aws_aurora_pg_opensearch_v1":
            env = {
                "QUERYLAKE_SEARCH_BACKEND_URL": "https://example-opensearch.local",
                "QUERYLAKE_SEARCH_INDEX_NAMESPACE": "querylake",
                "QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS": "1024",
            }
        with _temporary_env(env):
            _seed_ready_projections(profile_id, metadata_store_path)
            capabilities_payload = build_capabilities_payload(profile)
            diagnostics_payload = build_profile_diagnostics_payload(profile=profile, metadata_store_path=metadata_store_path)
            bringup_payload = build_profile_bringup_payload(profile=profile, metadata_store_path=metadata_store_path)
            routes = [
                _route_snapshot(
                    route_id=route_id,
                    profile=profile,
                    diagnostics_payload=diagnostics_payload,
                    bringup_payload=bringup_payload,
                )
                for route_id in ROUTES
            ]
            profile_rows.append(
                {
                    "profile_id": profile_id,
                    "maturity": profile.maturity,
                    "capabilities_profile_id": str(capabilities_payload.get("profile", {}).get("id") or ""),
                    "representation_scope_count": len(dict(diagnostics_payload.get("representation_scopes") or {})),
                    "route_runtime_ready": bool(bringup_payload.get("summary", {}).get("route_runtime_ready")),
                    "declared_executable_routes_runtime_ready": bool(
                        bringup_payload.get("summary", {}).get("declared_executable_routes_runtime_ready")
                    ),
                    "routes": routes,
                }
            )
    return {
        "validated_profile_count": len(profile_rows),
        "validated_routes": list(ROUTES),
        "profiles": profile_rows,
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate shared V2 runtime consistency across supported slices.")
    parser.add_argument("--output", default="/tmp/querylake_db_compat_v2_runtime_consistency.json")
    parser.add_argument(
        "--metadata-store-path",
        default="/tmp/querylake_db_compat_v2_runtime_consistency_meta.json",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    payload = build_v2_runtime_consistency_payload(metadata_store_path=args.metadata_store_path)
    Path(args.output).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(
        f"Validated V2 runtime consistency for {payload['validated_profile_count']} profiles "
        f"across {len(payload['validated_routes'])} routes."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

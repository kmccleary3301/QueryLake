from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple
import re

from pydantic import BaseModel, Field

from QueryLake.runtime.authority_projection_access import build_projection_materialization_target
from QueryLake.runtime.db_compat import DeploymentProfile, build_profile_route_support_matrix
from QueryLake.runtime.local_dense_sidecar import LOCAL_DENSE_SIDECAR_ADAPTER
from QueryLake.runtime.projection_ir_v2 import (
    ProjectionBuildabilityClass,
    ProjectionDependencyRef,
    RouteProjectionIRV2,
)
from QueryLake.runtime.projection_contracts import (
    DocumentChunkMaterializationRecord,
    FileChunkMaterializationRecord,
    ProjectionMaterializationTarget,
)
from QueryLake.runtime.query_ir_v2 import FilterIRV2, QueryIRV2, QueryStrictnessPolicy
from QueryLake.runtime.support_manifest_v2 import ROUTE_CAPABILITY_DEPENDENCIES, get_representation_scope


_FIELD_CONSTRAINT_RE = re.compile(r"(^|\s)([+\-])\w+|(\b\w+:(?:\"[^\"]+\"|\S+))", re.IGNORECASE)
_BOOLEAN_OPERATOR_RE = re.compile(r"\b(and|or|not)\b", re.IGNORECASE)
_QUOTE_RE = re.compile(r'"([^"\\]*(?:\\.[^"\\]*)*)"')


LOCAL_ROUTE_REQUIRED_PROJECTION_DESCRIPTORS: Dict[str, List[str]] = {
    "search_bm25.document_chunk": ["document_chunk_lexical_projection_v1"],
    "search_file_chunks": ["file_chunk_lexical_projection_v1"],
}

LOCAL_PROFILE_ID = "sqlite_fts5_dense_sidecar_local_v1"
LOCAL_DENSE_SIDECAR_PROJECTION_ID = "document_chunk_dense_projection_v1"

LOCAL_ROUTE_LEXICAL_SUPPORT_CLASS: Dict[str, str] = {
    "search_hybrid.document_chunk": "degraded_supported",
    "search_bm25.document_chunk": "degraded_supported",
    "search_file_chunks": "degraded_supported",
    "retrieval.sparse.vector": "unsupported",
    "retrieval.graph.traversal": "unsupported",
}

LOCAL_PROFILE_PROJECTION_IDS: List[str] = [
    "document_chunk_lexical_projection_v1",
    "document_chunk_dense_projection_v1",
    "file_chunk_lexical_projection_v1",
]


class LocalRouteRuntimeContextV2(BaseModel):
    route_id: str
    profile_id: str
    support_state: str
    representation_scope_id: str
    representation_scope: Dict[str, Any] = Field(default_factory=dict)
    capability_dependencies: List[str] = Field(default_factory=list)
    required_projection_ids: List[str] = Field(default_factory=list)
    materialization_targets: List[Dict[str, Any]] = Field(default_factory=list)
    lexical_support_class: str = "unsupported"
    query_ir_v2_template: Dict[str, Any] = Field(default_factory=dict)
    projection_ir_v2: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def dense_sidecar_required(self) -> bool:
        return LOCAL_DENSE_SIDECAR_PROJECTION_ID in set(self.required_projection_ids)

    def materialization_target(self, projection_id: str) -> Optional[Dict[str, Any]]:
        projection_key = str(projection_id)
        for target in self.materialization_targets:
            if str(target.get("projection_id") or "") == projection_key:
                return dict(target)
        return None


def resolve_local_route_materialization_target(
    context: LocalRouteRuntimeContextV2,
    projection_id: str,
) -> ProjectionMaterializationTarget:
    payload = context.materialization_target(projection_id)
    if payload is None:
        raise ValueError(
            "Missing local materialization target for "
            f"route_id={context.route_id} projection_id={projection_id}"
        )
    return ProjectionMaterializationTarget.model_validate(payload)


def _sort_materialization_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, dict):
        return str(sorted(value.items()))
    return value


def sort_document_chunk_materialization_record(
    chunk: DocumentChunkMaterializationRecord,
    sort_by: str,
) -> Any:
    if sort_by == "score":
        return 0.0
    return _sort_materialization_value(getattr(chunk, sort_by, None))


def sort_file_chunk_materialization_record(
    chunk: FileChunkMaterializationRecord,
    sort_by: str,
) -> Any:
    if sort_by == "score":
        return 0.0
    return _sort_materialization_value(getattr(chunk, sort_by, None))


def build_document_chunk_materialization_payload(
    chunk: DocumentChunkMaterializationRecord,
) -> Tuple[Any, ...]:
    return (
        chunk.id,
        float(chunk.creation_timestamp or 0.0),
        chunk.collection_type,
        chunk.document_id,
        int(chunk.document_chunk_number or 0),
        chunk.document_integrity,
        chunk.collection_id,
        chunk.document_name,
        chunk.website_url,
        bool(chunk.private),
        dict(chunk.md or {}),
        dict(chunk.document_md or {}),
        chunk.text,
    )


def build_file_chunk_materialization_payload(
    chunk: FileChunkMaterializationRecord,
) -> Tuple[Any, ...]:
    return (
        chunk.id,
        chunk.text,
        dict(chunk.md or {}),
        float(chunk.created_at or 0.0),
        chunk.file_version_id,
    )


def build_document_chunk_lexical_rows(
    paged: Sequence[Tuple[DocumentChunkMaterializationRecord, float]],
    *,
    query_is_empty: bool,
) -> List[Tuple[Any, ...]]:
    if query_is_empty:
        return [
            (chunk.id, *build_document_chunk_materialization_payload(chunk))
            for chunk, _ in paged
        ]
    return [
        (chunk.id, float(score), *build_document_chunk_materialization_payload(chunk))
        for chunk, score in paged
    ]


def build_file_chunk_lexical_rows(
    paged: Sequence[Tuple[FileChunkMaterializationRecord, float]],
    *,
    query_is_empty: bool,
) -> List[Tuple[Any, ...]]:
    if query_is_empty:
        return [
            (chunk.id, *build_file_chunk_materialization_payload(chunk))
            for chunk, _ in paged
        ]
    return [
        (chunk.id, float(score), *build_file_chunk_materialization_payload(chunk))
        for chunk, score in paged
    ]


def build_document_chunk_hybrid_rows(
    lexical_ranked: Sequence[Tuple[DocumentChunkMaterializationRecord, float]],
    dense_ranked: Sequence[Tuple[DocumentChunkMaterializationRecord, float]],
    *,
    bm25_weight: float,
    similarity_weight: float,
) -> List[Tuple[Any, ...]]:
    lexical_rank_map = {str(chunk.id): idx + 1 for idx, (chunk, _) in enumerate(lexical_ranked)}
    dense_rank_map = {str(chunk.id): idx + 1 for idx, (chunk, _) in enumerate(dense_ranked)}
    chunk_map = {str(chunk.id): chunk for chunk, _ in list(lexical_ranked) + list(dense_ranked) if chunk.id is not None}
    candidate_ids = sorted(set(list(lexical_rank_map.keys()) + list(dense_rank_map.keys())))
    results: List[Tuple[Any, ...]] = []
    for chunk_id in candidate_ids:
        chunk = chunk_map.get(chunk_id)
        if chunk is None:
            continue
        similarity_score = (
            (1.0 / (60.0 + float(dense_rank_map[chunk_id]))) if chunk_id in dense_rank_map else 0.0
        )
        bm25_score = (
            (1.0 / (60.0 + float(lexical_rank_map[chunk_id]))) if chunk_id in lexical_rank_map else 0.0
        )
        sparse_score = 0.0
        hybrid_score = (similarity_score * similarity_weight) + (bm25_score * bm25_weight)
        results.append(
            (
                chunk.id,
                similarity_score,
                bm25_score,
                sparse_score,
                hybrid_score,
                *build_document_chunk_materialization_payload(chunk),
            )
        )
    results.sort(key=lambda row: (-float(row[4]), str(row[0] or "")))
    return results


def is_local_profile_v2(profile: DeploymentProfile) -> bool:
    return str(profile.id) == LOCAL_PROFILE_ID


def local_route_required_projection_descriptors(
    route_id: str,
    *,
    use_dense: bool = False,
    use_sparse: bool = False,
) -> List[str]:
    if route_id == "search_hybrid.document_chunk":
        descriptors = ["document_chunk_lexical_projection_v1"]
        if use_dense:
            descriptors.append("document_chunk_dense_projection_v1")
        if use_sparse:
            descriptors.append("document_chunk_sparse_projection_v1")
        return descriptors
    return list(LOCAL_ROUTE_REQUIRED_PROJECTION_DESCRIPTORS.get(route_id, []))


def build_local_route_materialization_targets(
    route_id: str,
    *,
    profile: DeploymentProfile,
    use_dense: bool = False,
    use_sparse: bool = False,
) -> List[Dict[str, Any]]:
    targets: List[Dict[str, Any]] = []
    for projection_id in local_route_required_projection_descriptors(
        route_id,
        use_dense=use_dense,
        use_sparse=use_sparse,
    ):
        if projection_id in {"document_chunk_lexical_projection_v1", "file_chunk_lexical_projection_v1"}:
            backend_name = "sqlite_fts5"
        elif projection_id == "document_chunk_dense_projection_v1":
            backend_name = "local_dense_sidecar"
        else:
            backend_name = "none"
        target = build_projection_materialization_target(
            projection_id=projection_id,
            target_backend_name=backend_name,
            metadata={
                "profile_id": profile.id,
                "route_projection": True,
                "runtime_family": "local_profile_v2",
                "route_id": route_id,
            },
        )
        targets.append(target.model_dump())
    return targets


def build_local_query_ir_v2(
    route_id: str,
    *,
    raw_query_text: str,
    use_dense: bool = False,
    use_sparse: bool = False,
    collection_ids: Optional[Sequence[str]] = None,
    return_statement: bool = False,
) -> QueryIRV2:
    query = str(raw_query_text or "")
    normalized = " ".join(query.strip().split())
    has_quotes = bool(_QUOTE_RE.search(query))
    has_boolean_operators = bool(_BOOLEAN_OPERATOR_RE.search(query))
    has_hard_constraints = bool(_FIELD_CONSTRAINT_RE.search(query))
    if has_hard_constraints:
        strictness = QueryStrictnessPolicy.reject_if_not_exact
    elif has_quotes or has_boolean_operators:
        strictness = QueryStrictnessPolicy.exact
    else:
        strictness = QueryStrictnessPolicy.approximate
    scope = get_representation_scope(route_id)
    return QueryIRV2(
        raw_query_text=query,
        normalized_query_text=normalized,
        lexical_query_text=normalized or None,
        use_dense=bool(use_dense),
        use_sparse=bool(use_sparse),
        filter_ir=FilterIRV2(
            collection_ids=[str(item) for item in list(collection_ids or []) if str(item)]
        ),
        strictness_policy=strictness,
        representation_scope_id=scope.scope_id,
        route_id=route_id,
        planner_hints={
            "return_statement": bool(return_statement),
            "profile_runtime_family": "local_profile_v2",
            "query_features": {
                "quoted_phrases": has_quotes,
                "boolean_operators": has_boolean_operators,
                "hard_constraints": has_hard_constraints,
            },
        },
        metadata={
            "route_id": route_id,
            "representation_kind": str(scope.metadata.get("representation_kind") or ""),
        },
    )


def build_local_route_projection_ir_v2(
    route_id: str,
    *,
    profile: DeploymentProfile,
    support_state: str,
    use_dense: bool = False,
    use_sparse: bool = False,
    runtime_ready: bool = False,
    runtime_blockers: Optional[Sequence[str]] = None,
) -> RouteProjectionIRV2:
    scope = get_representation_scope(route_id)
    required_targets = [
        ProjectionDependencyRef(
            target_id=str(item["projection_id"]),
            required=True,
            target_backend_family=str(item["target_backend_family"]),
            support_state=support_state,
            metadata={
                "target_backend_name": str(item["target_backend_name"]),
                "representation_scope_id": scope.scope_id,
            },
        )
        for item in build_local_route_materialization_targets(
            route_id,
            profile=profile,
            use_dense=use_dense,
            use_sparse=use_sparse,
        )
    ]
    if support_state == "unsupported":
        buildability = ProjectionBuildabilityClass.unsupported
    elif runtime_ready:
        buildability = (
            ProjectionBuildabilityClass.degraded_executable
            if support_state == "degraded"
            else ProjectionBuildabilityClass.executable_ready
        )
    else:
        buildability = ProjectionBuildabilityClass.executable_requires_build
    blockers = [str(item) for item in list(runtime_blockers or []) if str(item)]
    hints: List[str] = []
    if len(required_targets) > 0 and not runtime_ready:
        hints.append(f"bootstrap_required_projections:{route_id}")
    if support_state == "degraded":
        hints.append("expect_degraded_lexical_semantics")
    return RouteProjectionIRV2(
        profile_id=profile.id,
        route_id=route_id,
        representation_scope_id=scope.scope_id,
        required_targets=required_targets,
        optional_targets=[],
        capability_dependencies=list(ROUTE_CAPABILITY_DEPENDENCIES.get(route_id, [])),
        runtime_blockers=blockers,
        buildability_class=buildability,
        recovery_hints=hints,
        metadata={
            "runtime_family": "local_profile_v2",
            "representation_kind": str(scope.metadata.get("representation_kind") or ""),
        },
    )


def build_local_route_execution_plan_payload(
    route_id: str,
    *,
    profile: DeploymentProfile,
    raw_query_text: str,
    support_state: str,
    use_dense: bool = False,
    use_sparse: bool = False,
    collection_ids: Optional[Sequence[str]] = None,
    return_statement: bool = False,
    runtime_ready: bool = False,
    runtime_blockers: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    query_ir_v2 = build_local_query_ir_v2(
        route_id,
        raw_query_text=raw_query_text,
        use_dense=use_dense,
        use_sparse=use_sparse,
        collection_ids=collection_ids,
        return_statement=return_statement,
    )
    projection_ir_v2 = build_local_route_projection_ir_v2(
        route_id,
        profile=profile,
        support_state=support_state,
        use_dense=use_dense,
        use_sparse=use_sparse,
        runtime_ready=runtime_ready,
        runtime_blockers=runtime_blockers,
    )
    materialization_targets = build_local_route_materialization_targets(
        route_id,
        profile=profile,
        use_dense=use_dense,
        use_sparse=use_sparse,
    )
    return {
        "route_id": route_id,
        "query_ir_v2_template": query_ir_v2.model_dump(),
        "projection_ir_v2": projection_ir_v2.model_dump(),
        "materialization_targets": [dict(item) for item in materialization_targets],
    }


def build_local_route_runtime_context_v2(
    route_id: str,
    *,
    profile: DeploymentProfile,
    support_state: str,
    raw_query_text: str = "",
    use_dense: bool = False,
    use_sparse: bool = False,
    collection_ids: Optional[Sequence[str]] = None,
    return_statement: bool = False,
    runtime_ready: bool = False,
    runtime_blockers: Optional[Sequence[str]] = None,
) -> LocalRouteRuntimeContextV2:
    scope = get_representation_scope(route_id)
    planning_payload = build_local_route_execution_plan_payload(
        route_id,
        profile=profile,
        raw_query_text=raw_query_text,
        support_state=support_state,
        use_dense=use_dense,
        use_sparse=use_sparse,
        collection_ids=collection_ids,
        return_statement=return_statement,
        runtime_ready=runtime_ready,
        runtime_blockers=runtime_blockers,
    )
    required_projection_ids = local_route_required_projection_descriptors(
        route_id,
        use_dense=use_dense,
        use_sparse=use_sparse,
    )
    return LocalRouteRuntimeContextV2(
        route_id=route_id,
        profile_id=str(profile.id),
        support_state=str(support_state),
        representation_scope_id=scope.scope_id,
        representation_scope={
            "scope_id": scope.scope_id,
            "authority_model": scope.authority_model,
            "compatibility_projection": bool(scope.compatibility_projection),
            "metadata": dict(scope.metadata),
        },
        capability_dependencies=list(ROUTE_CAPABILITY_DEPENDENCIES.get(route_id, [])),
        required_projection_ids=list(required_projection_ids),
        materialization_targets=[dict(item) for item in planning_payload["materialization_targets"]],
        lexical_support_class=LOCAL_ROUTE_LEXICAL_SUPPORT_CLASS.get(route_id, "unsupported"),
        query_ir_v2_template=dict(planning_payload["query_ir_v2_template"]),
        projection_ir_v2=dict(planning_payload["projection_ir_v2"]),
        metadata={
            "runtime_family": "local_profile_v2",
            "representation_kind": str(scope.metadata.get("representation_kind") or ""),
        },
    )


def build_local_projection_build_ir_v2(
    projection_id: str,
    *,
    profile: DeploymentProfile,
    support_state: str,
    action_mode: str,
    build_status: str,
) -> Dict[str, Any]:
    target = build_projection_materialization_target(
        projection_id=projection_id,
        target_backend_name=(
            "sqlite_fts5"
            if "lexical" in projection_id
            else "local_dense_sidecar"
            if "dense" in projection_id
            else "none"
        ),
        metadata={
            "profile_id": profile.id,
            "runtime_family": "local_profile_v2",
        },
    )
    if support_state == "unsupported":
        buildability = ProjectionBuildabilityClass.unsupported
    elif build_status == "ready":
        buildability = (
            ProjectionBuildabilityClass.degraded_executable
            if support_state == "degraded"
            else ProjectionBuildabilityClass.executable_ready
        )
    else:
        buildability = ProjectionBuildabilityClass.executable_requires_build
    return {
        "profile_id": profile.id,
        "projection_id": projection_id,
        "representation_scope_id": target.source_scope,
        "lane_family": target.lane_family,
        "target_backend": target.target_backend_name,
        "buildability_class": str(buildability.value),
        "action_mode": str(action_mode),
        "support_state": str(support_state),
        "materialization_target": target.model_dump(),
    }


def build_local_route_support_matrix_payload(
    *,
    profile: DeploymentProfile,
) -> List[Dict[str, Any]]:
    payload: List[Dict[str, Any]] = []
    for route_id, support in build_profile_route_support_matrix(profile).items():
        scope = get_representation_scope(route_id)
        use_dense = route_id == "search_hybrid.document_chunk"
        use_sparse = route_id == "retrieval.sparse.vector"
        payload.append(
            {
                "route_id": route_id,
                "support_state": str(support.get("declared_state") or "unsupported"),
                "declared_executable": bool(support.get("declared_executable")),
                "declared_optional": bool(support.get("declared_optional")),
                "representation_scope_id": scope.scope_id,
                "representation_scope": {
                    "scope_id": scope.scope_id,
                    "authority_model": scope.authority_model,
                    "compatibility_projection": bool(scope.compatibility_projection),
                    "metadata": dict(scope.metadata),
                },
                "capability_dependencies": list(ROUTE_CAPABILITY_DEPENDENCIES.get(route_id, [])),
                "required_projection_descriptors": local_route_required_projection_descriptors(
                    route_id,
                    use_dense=use_dense,
                    use_sparse=use_sparse,
                ),
                "lexical_support_class": LOCAL_ROUTE_LEXICAL_SUPPORT_CLASS.get(route_id, "unsupported"),
            }
        )
    return payload


def build_local_profile_support_manifest_payload(
    *,
    profile: DeploymentProfile,
) -> Dict[str, Any]:
    support_matrix = build_local_route_support_matrix_payload(profile=profile)
    return {
        "profile_id": profile.id,
        "maturity": profile.maturity,
        "authority_backend": "sqlite",
        "lexical_backend": "sqlite_fts5",
        "dense_backend": "local_dense_sidecar",
        "dense_sidecar_projection_id": LOCAL_DENSE_SIDECAR_PROJECTION_ID,
        "declared_executable_route_ids": sorted(
            str(row.get("route_id") or "")
            for row in support_matrix
            if bool(row.get("declared_executable"))
        ),
        "routes": [
            {
                "route_id": str(row.get("route_id") or ""),
                "support_state": str(row.get("support_state") or "unsupported"),
                "declared_executable": bool(row.get("declared_executable")),
                "declared_optional": bool(row.get("declared_optional")),
                "representation_scope_id": str(row.get("representation_scope_id") or ""),
                "required_projection_descriptors": list(row.get("required_projection_descriptors") or []),
                "capability_dependencies": list(row.get("capability_dependencies") or []),
                "lexical_support_class": str(row.get("lexical_support_class") or "unsupported"),
            }
            for row in support_matrix
        ],
        "docs_ref": "docs/database/LOCAL_PROFILE_V1.md",
    }


def build_local_projection_plan_registry_payload(
    *,
    profile: DeploymentProfile,
    projection_diagnostics: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    projection_items = {
        str(item.get("projection_id") or ""): dict(item)
        for item in list((projection_diagnostics or {}).get("projection_items") or [])
        if isinstance(item, dict) and item.get("projection_id") is not None
    }
    support_state_map: Dict[str, str] = {
        "document_chunk_lexical_projection_v1": "degraded",
        "document_chunk_dense_projection_v1": "supported",
        "file_chunk_lexical_projection_v1": "degraded",
    }
    payload: List[Dict[str, Any]] = []
    for projection_id in LOCAL_PROFILE_PROJECTION_IDS:
        item = projection_items.get(projection_id) or {}
        payload.append(
            build_local_projection_build_ir_v2(
                projection_id,
                profile=profile,
                support_state=str(item.get("support_state") or support_state_map.get(projection_id, "supported")),
                action_mode=str(item.get("action_mode") or "rebuild"),
                build_status=str(item.get("build_status") or "absent"),
            )
        )
    return payload


def build_local_dense_sidecar_status_payload(
    *,
    profile: DeploymentProfile,
    projection_diagnostics: Optional[Dict[str, Any]] = None,
    support_matrix: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    effective_support_matrix = support_matrix or build_local_route_support_matrix_payload(profile=profile)
    projection_items = {
        str(item.get("projection_id") or ""): dict(item)
        for item in list((projection_diagnostics or {}).get("projection_items") or [])
        if isinstance(item, dict) and item.get("projection_id") is not None
    }
    dense_projection = dict(projection_items.get(LOCAL_DENSE_SIDECAR_PROJECTION_ID) or {})
    requiring_routes = sorted(
        str(row.get("route_id") or "")
        for row in effective_support_matrix
        if LOCAL_DENSE_SIDECAR_PROJECTION_ID in list(row.get("required_projection_descriptors") or [])
    )
    build_status = str(dense_projection.get("build_status") or "absent")
    executable = bool(dense_projection.get("executable"))
    persisted_dense_sidecar = dict(
        dict(dense_projection.get("build_state") or {}).get("metadata", {}).get("dense_sidecar") or {}
    )
    payload = LOCAL_DENSE_SIDECAR_ADAPTER.status_payload(
        projection_id=LOCAL_DENSE_SIDECAR_PROJECTION_ID,
        build_status=build_status,
        executable=executable,
        requiring_route_ids=requiring_routes,
        materialization_target=dict(dense_projection.get("materialization_target") or {}),
        persisted_dense_sidecar=persisted_dense_sidecar,
    )
    payload["support_state"] = str(dense_projection.get("support_state") or "supported")
    payload["docs_ref"] = "docs/database/LOCAL_PROFILE_V1.md#dense-sidecar"
    payload["metadata"] = dict(dense_projection.get("materialization_target") or {})
    payload["projection_plan_v2"] = next((dict(item) for item in build_local_projection_plan_registry_payload(profile=profile, projection_diagnostics=projection_diagnostics) if str(item.get("projection_id") or "") == LOCAL_DENSE_SIDECAR_PROJECTION_ID), {})
    return payload


def build_local_route_runtime_contracts_payload(
    *,
    profile: DeploymentProfile,
    support_matrix: Optional[List[Dict[str, Any]]] = None,
    route_payloads: Optional[Sequence[Dict[str, Any]]] = None,
    projection_diagnostics: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    effective_support_matrix = support_matrix or build_local_route_support_matrix_payload(profile=profile)
    route_payload_map = {
        str(row.get("route_id") or ""): dict(row)
        for row in list(route_payloads or [])
        if isinstance(row, dict) and row.get("route_id") is not None
    }
    dense_status = build_local_dense_sidecar_status_payload(
        profile=profile,
        projection_diagnostics=projection_diagnostics,
        support_matrix=effective_support_matrix,
    )
    contracts: List[Dict[str, Any]] = []
    for row in effective_support_matrix:
        route_id = str(row.get("route_id") or "")
        runtime_row = route_payload_map.get(route_id) or {}
        lexical_semantics = dict(runtime_row.get("lexical_semantics") or {})
        runtime_blockers = [
            dict(entry)
            for entry in list(runtime_row.get("runtime_blockers") or [])
            if isinstance(entry, dict)
        ]
        support_state = str(runtime_row.get("support_state") or row.get("support_state") or "unsupported")
        blocker_kinds = [
            str(blocker.get("kind") or "")
            for blocker in runtime_blockers
            if str(blocker.get("kind") or "")
        ]
        context = build_local_route_runtime_context_v2(
            route_id,
            profile=profile,
            support_state=support_state,
            use_dense=route_id == "search_hybrid.document_chunk",
            use_sparse=route_id == "retrieval.sparse.vector",
            runtime_ready=bool(runtime_row.get("runtime_ready", False)),
            runtime_blockers=blocker_kinds,
        )
        planning_v2 = dict(runtime_row.get("planning_v2") or {})
        planning_v2["query_ir_v2_template"] = dict(context.query_ir_v2_template)
        planning_v2["projection_ir_v2"] = dict(context.projection_ir_v2)
        query_ir_v2_template = dict(planning_v2.get("query_ir_v2_template") or {})
        projection_ir_v2 = dict(planning_v2.get("projection_ir_v2") or {})
        required_projection_ids = list(context.required_projection_ids)
        contracts.append(
            {
                "route_id": route_id,
                "declared_state": str(row.get("support_state") or "unsupported"),
                "support_state": support_state,
                "declared_executable": bool(row.get("declared_executable")),
                "declared_optional": bool(row.get("declared_optional")),
                "implemented": bool(runtime_row.get("implemented", False)),
                "runtime_ready": bool(runtime_row.get("runtime_ready", False)),
                "projection_ready": bool(runtime_row.get("projection_ready", False)),
                "representation_scope_id": str(context.representation_scope_id),
                "representation_scope": dict(context.representation_scope),
                "capability_dependencies": list(context.capability_dependencies),
                "required_projection_ids": required_projection_ids,
                "missing_projection_ids": list(runtime_row.get("projection_missing_descriptors") or []),
                "projection_build_gap_ids": list(runtime_row.get("projection_build_gap_descriptors") or []),
                "blocking_projection_ids": sorted(
                    {
                        str(projection_id or "")
                        for blocker in runtime_blockers
                        for projection_id in list(blocker.get("projection_ids") or [])
                        if str(projection_id or "")
                    }
                ),
                "blocker_kinds": blocker_kinds,
                "dense_sidecar_required": context.dense_sidecar_required(),
                "dense_sidecar_ready": bool(dense_status.get("ready")) if LOCAL_DENSE_SIDECAR_PROJECTION_ID in required_projection_ids else False,
                "dense_sidecar_cache_warmed": bool(dense_status.get("cache_warmed")) if LOCAL_DENSE_SIDECAR_PROJECTION_ID in required_projection_ids else False,
                "dense_sidecar_indexed_record_count": int(dense_status.get("record_count") or 0) if LOCAL_DENSE_SIDECAR_PROJECTION_ID in required_projection_ids else 0,
                "dense_sidecar_embedding_dimension": int(dense_status.get("embedding_dimension") or 0) if LOCAL_DENSE_SIDECAR_PROJECTION_ID in required_projection_ids else 0,
                "dense_sidecar_ready_state_source": (
                    str(dense_status.get("ready_state_source") or "")
                    if LOCAL_DENSE_SIDECAR_PROJECTION_ID in required_projection_ids
                    else ""
                ),
                "dense_sidecar_stats_source": (
                    str(dense_status.get("stats_source") or "")
                    if LOCAL_DENSE_SIDECAR_PROJECTION_ID in required_projection_ids
                    else ""
                ),
                "dense_sidecar_contract": (
                    dict(dense_status.get("contract") or {})
                    if LOCAL_DENSE_SIDECAR_PROJECTION_ID in required_projection_ids
                    else {}
                ),
                "dense_sidecar_cache_lifecycle_state": (
                    str(dense_status.get("cache_lifecycle_state") or "")
                    if LOCAL_DENSE_SIDECAR_PROJECTION_ID in required_projection_ids
                    else ""
                ),
                "dense_sidecar_rebuildable_from_projection_records": (
                    bool(dense_status.get("rebuildable_from_projection_records"))
                    if LOCAL_DENSE_SIDECAR_PROJECTION_ID in required_projection_ids
                    else False
                ),
                "dense_sidecar_requires_process_warmup": (
                    bool(dense_status.get("requires_process_warmup"))
                    if LOCAL_DENSE_SIDECAR_PROJECTION_ID in required_projection_ids
                    else False
                ),
                "dense_sidecar_warmup_recommended": (
                    bool(dense_status.get("warmup_recommended"))
                    if LOCAL_DENSE_SIDECAR_PROJECTION_ID in required_projection_ids
                    else False
                ),
                "dense_sidecar_warmup_required_for_peak_performance": (
                    bool(dense_status.get("warmup_required_for_peak_performance"))
                    if LOCAL_DENSE_SIDECAR_PROJECTION_ID in required_projection_ids
                    else False
                ),
                "dense_sidecar_cold_start_recoverable": (
                    bool(dense_status.get("cold_start_recoverable"))
                    if LOCAL_DENSE_SIDECAR_PROJECTION_ID in required_projection_ids
                    else False
                ),
                "dense_sidecar_cache_persistence_mode": (
                    str(dense_status.get("cache_persistence_mode") or "")
                    if LOCAL_DENSE_SIDECAR_PROJECTION_ID in required_projection_ids
                    else ""
                ),
                "dense_sidecar_lifecycle_recovery_mode": (
                    str(dense_status.get("lifecycle_recovery_mode") or "")
                    if LOCAL_DENSE_SIDECAR_PROJECTION_ID in required_projection_ids
                    else ""
                ),
                "dense_sidecar_lifecycle_recovery_hints": (
                    list(dense_status.get("lifecycle_recovery_hints") or [])
                    if LOCAL_DENSE_SIDECAR_PROJECTION_ID in required_projection_ids
                    else []
                ),
                "dense_sidecar_warmup_target_route_ids": (
                    list(dense_status.get("warmup_target_route_ids") or [])
                    if LOCAL_DENSE_SIDECAR_PROJECTION_ID in required_projection_ids
                    else []
                ),
                "dense_sidecar_warmup_command_hint": (
                    dense_status.get("warmup_command_hint")
                    if LOCAL_DENSE_SIDECAR_PROJECTION_ID in required_projection_ids
                    else None
                ),
                "dense_sidecar_persisted_projection_state_available": (
                    bool(dense_status.get("persisted_projection_state_available"))
                    if LOCAL_DENSE_SIDECAR_PROJECTION_ID in required_projection_ids
                    else False
                ),
                "lexical_support_class": str(context.lexical_support_class),
                "gold_recommended_for_exact_constraints": bool(
                    lexical_semantics.get("gold_recommended_for_exact_constraints")
                ),
                "exact_constraint_degraded_capabilities": list(
                    lexical_semantics.get("degraded_capabilities") or []
                ),
                "exact_constraint_unsupported_capabilities": list(
                    lexical_semantics.get("unsupported_capabilities") or []
                ),
                "planning_v2": planning_v2,
                "query_ir_v2_template": query_ir_v2_template,
                "projection_ir_v2": projection_ir_v2,
            }
        )
    return contracts


def build_local_profile_promotion_status_payload(
    *,
    profile: DeploymentProfile,
    bringup_payload: Dict[str, Any],
    local_profile_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    route_recovery = {
        str(entry.get("route_id")): dict(entry)
        for entry in list(bringup_payload.get("route_recovery") or [])
        if isinstance(entry, dict) and entry.get("route_id") is not None
    }
    support_matrix = build_local_route_support_matrix_payload(profile=profile)
    dense_sidecar_ready = False
    effective_local_profile_payload = dict(local_profile_payload or bringup_payload.get("local_profile") or {})
    route_runtime_contracts = {
        str(entry.get("route_id") or ""): dict(entry)
        for entry in list(effective_local_profile_payload.get("route_runtime_contracts") or [])
        if isinstance(entry, dict) and entry.get("route_id") is not None
    }
    if effective_local_profile_payload:
        dense_sidecar_payload = dict(effective_local_profile_payload.get("dense_sidecar") or {})
        dense_sidecar_ready = bool(dense_sidecar_payload.get("ready"))
    else:
        dense_sidecar_payload = {}
    declared_executable_routes = [
        str(row.get("route_id") or "")
        for row in support_matrix
        if bool(row.get("declared_executable"))
    ]
    local_representation_scope_ids = sorted(
        {
            str(row.get("representation_scope_id") or "")
            for row in support_matrix
            if str(row.get("representation_scope_id") or "")
        }
    )
    projection_plan_v2_registry = list(
        (effective_local_profile_payload or {}).get("projection_plan_v2_registry") or []
    )
    runtime_ready_routes: List[str] = []
    blocked_routes: List[str] = []
    required_projection_ids: set[str] = set()
    planning_v2_ready = True
    query_ir_v2_complete = True
    projection_ir_v2_complete = True
    representation_scope_ids_present = True
    projection_plan_v2_complete = len(projection_plan_v2_registry) == len(LOCAL_PROFILE_PROJECTION_IDS)
    for route_id in declared_executable_routes:
        support_row = next(
            (row for row in support_matrix if str(row.get("route_id") or "") == route_id),
            {},
        )
        contract = route_runtime_contracts.get(route_id) or {}
        recovery = route_recovery.get(route_id) or {}
        planning_v2 = dict(contract.get("planning_v2") or recovery.get("planning_v2") or {})
        query_ir_v2_template = dict(
            contract.get("query_ir_v2_template")
            or planning_v2.get("query_ir_v2_template")
            or {}
        )
        projection_ir_v2 = dict(
            contract.get("projection_ir_v2")
            or planning_v2.get("projection_ir_v2")
            or {}
        )
        if not planning_v2:
            planning_v2_ready = False
        if str(query_ir_v2_template.get("route_id") or "") != route_id:
            query_ir_v2_complete = False
            planning_v2_ready = False
        if str(projection_ir_v2.get("representation_scope_id") or "") == "":
            projection_ir_v2_complete = False
            planning_v2_ready = False
        if str(contract.get("representation_scope_id") or recovery.get("representation_scope_id") or "") == "":
            representation_scope_ids_present = False
        required_projection_ids.update(
            str(value)
            for value in list(contract.get("required_projection_ids") or support_row.get("required_projection_descriptors") or [])
            if str(value or "")
        )
        required_projection_ids.update(
            str(value)
            for value in list(recovery.get("required_projection_descriptor_ids") or [])
            if str(value or "")
        )
        required_projection_ids.update(
            str(value)
            for value in list(recovery.get("bootstrapable_blocking_projection_ids") or [])
            if str(value or "")
        )
        required_projection_ids.update(
            str(value)
            for value in list(recovery.get("nonbootstrapable_blocking_projection_ids") or contract.get("blocking_projection_ids") or [])
            if str(value or "")
        )
        if bool(contract.get("runtime_ready", recovery.get("runtime_ready"))):
            runtime_ready_routes.append(route_id)
        else:
            blocked_routes.append(route_id)

    summary = dict(bringup_payload.get("summary") or {})
    profile_promoted = bool(profile.implemented)
    remaining_blockers: List[str] = []
    if not profile_promoted:
        remaining_blockers.append("local_supported_profile_manifest_promotion")
    if not bool(summary.get("declared_executable_routes_runtime_ready")):
        remaining_blockers.append("runtime_ready_local_slice")
    return {
        "profile_promoted": profile_promoted,
        "declared_scope_frozen": True,
        "route_execution_real": True,
        "projection_lifecycle_real": int(summary.get("required_projection_count") or 0) > 0,
        "planning_v2_surfaced": planning_v2_ready,
        "query_ir_v2_complete": query_ir_v2_complete,
        "projection_ir_v2_complete": projection_ir_v2_complete,
        "projection_plan_v2_complete": projection_plan_v2_complete,
        "representation_scope_ids_present": representation_scope_ids_present,
        "representation_scope_ids": local_representation_scope_ids,
        "declared_executable_route_count": len(declared_executable_routes),
        "declared_executable_route_ids": sorted(declared_executable_routes),
        "declared_executable_runtime_ready_count": len(runtime_ready_routes),
        "declared_executable_runtime_ready_ids": sorted(runtime_ready_routes),
        "declared_executable_runtime_blocked_count": len(blocked_routes),
        "declared_executable_runtime_blocked_ids": sorted(blocked_routes),
        "declared_executable_runtime_ready": bool(
            summary.get("declared_executable_routes_runtime_ready")
        ),
        "ready_projection_count": int(summary.get("ready_projection_count") or 0),
        "required_projection_count": int(summary.get("required_projection_count") or 0),
        "required_projection_ids": sorted(required_projection_ids),
        "dense_sidecar_ready": dense_sidecar_ready,
        "dense_sidecar_runtime_contract_ready": bool(
            dense_sidecar_payload.get("runtime_contract_ready")
        ),
        "dense_sidecar_promotion_contract_ready": bool(
            dense_sidecar_payload.get("promotion_contract_ready")
        ),
        "dense_sidecar_runtime_blockers": list(
            dense_sidecar_payload.get("runtime_blockers") or []
        ),
        "dense_sidecar_promotion_blockers": list(
            dense_sidecar_payload.get("promotion_blockers") or []
        ),
        "dense_sidecar_lifecycle_state": str(
            dense_sidecar_payload.get("lifecycle_state") or ""
        ),
        "dense_sidecar_cache_lifecycle_state": str(
            dense_sidecar_payload.get("cache_lifecycle_state") or ""
        ),
        "dense_sidecar_rebuildable_from_projection_records": bool(
            dense_sidecar_payload.get("rebuildable_from_projection_records")
        ),
        "dense_sidecar_requires_process_warmup": bool(
            dense_sidecar_payload.get("requires_process_warmup")
        ),
        "dense_sidecar_warmup_recommended": bool(
            dense_sidecar_payload.get("warmup_recommended")
        ),
        "dense_sidecar_warmup_required_for_peak_performance": bool(
            dense_sidecar_payload.get("warmup_required_for_peak_performance")
        ),
        "dense_sidecar_cold_start_recoverable": bool(
            dense_sidecar_payload.get("cold_start_recoverable")
        ),
        "dense_sidecar_cache_persistence_mode": str(
            dense_sidecar_payload.get("cache_persistence_mode") or ""
        ),
        "dense_sidecar_lifecycle_recovery_mode": str(
            dense_sidecar_payload.get("lifecycle_recovery_mode") or ""
        ),
        "dense_sidecar_lifecycle_recovery_hints": list(
            dense_sidecar_payload.get("lifecycle_recovery_hints") or []
        ),
        "dense_sidecar_warmup_target_route_ids": list(
            dense_sidecar_payload.get("warmup_target_route_ids") or []
        ),
        "dense_sidecar_warmup_command_hint": dense_sidecar_payload.get("warmup_command_hint"),
        "dense_sidecar_persisted_projection_state_available": bool(
            dense_sidecar_payload.get("persisted_projection_state_available")
        ),
        "dense_sidecar_projection_id": LOCAL_DENSE_SIDECAR_PROJECTION_ID,
        "lexical_degraded_route_ids": list(bringup_payload.get("lexical_degraded_route_ids") or []),
        "lexical_gold_recommended_route_ids": list(
            bringup_payload.get("lexical_gold_recommended_route_ids") or []
        ),
        "remaining_blockers": remaining_blockers,
    }


def build_local_profile_scope_expansion_status_payload(
    *,
    profile: DeploymentProfile,
    bringup_payload: Dict[str, Any],
    local_profile_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    promotion_status = build_local_profile_promotion_status_payload(
        profile=profile,
        bringup_payload=bringup_payload,
        local_profile_payload=local_profile_payload,
    )
    summary = dict(bringup_payload.get("summary") or {})
    effective_local_profile_payload = dict(local_profile_payload or bringup_payload.get("local_profile") or {})
    support_matrix = list(effective_local_profile_payload.get("support_matrix") or [])
    dense_sidecar = dict(effective_local_profile_payload.get("dense_sidecar") or {})
    route_runtime_contracts = {
        str(entry.get("route_id") or ""): dict(entry)
        for entry in list(effective_local_profile_payload.get("route_runtime_contracts") or [])
        if isinstance(entry, dict) and entry.get("route_id") is not None
    }

    required_for_scope_expansion: List[str] = []
    if not bool(promotion_status.get("declared_executable_runtime_ready")):
        required_for_scope_expansion.append("keep_declared_slice_runtime_ready")
    if not bool(promotion_status.get("planning_v2_surfaced")):
        required_for_scope_expansion.append("keep_planning_v2_surfaced")
    if not bool(promotion_status.get("projection_plan_v2_complete")):
        required_for_scope_expansion.append("keep_projection_plan_v2_complete")
    if not bool(dense_sidecar.get("promotion_contract_ready")):
        required_for_scope_expansion.append("keep_dense_sidecar_promotion_contract_ready")

    future_scope_candidates = [
        "local_sparse_vector_lane",
        "local_graph_traversal_lane",
        "broader_embedded_route_validation",
        "wider_embedded_parity_gate",
    ]
    satisfied_now = [
        "declared_local_slice_supported",
        "declared_local_slice_runtime_ready_after_bootstrap",
        "query_ir_v2_surfaced_for_declared_slice",
        "projection_ir_v2_surfaced_for_declared_slice",
        "dense_sidecar_contract_explicit",
    ]
    pending_for_wider_scope = [
        "define_next_embedded_route_slice",
        "add_validation_for_any_new_embedded_routes",
        "add parity/no_regression expectations for widened embedded slice",
        "decide whether widened slice requires a stronger dense-sidecar query/storage contract",
    ]
    if any(
        bool(contract.get("support_state") == "supported")
        and str(route_id) not in set(promotion_status.get("declared_executable_route_ids") or [])
        for route_id, contract in route_runtime_contracts.items()
    ):
        pending_for_wider_scope.append("audit undeclared supported runtime routes before widening")

    return {
        "profile_id": profile.id,
        "maturity": profile.maturity,
        "current_supported_slice_frozen": True,
        "declared_executable_route_ids": list(promotion_status.get("declared_executable_route_ids") or []),
        "declared_executable_runtime_ready": bool(
            promotion_status.get("declared_executable_runtime_ready")
        ),
        "required_for_scope_expansion": required_for_scope_expansion,
        "satisfied_now": satisfied_now,
        "pending_for_wider_scope": pending_for_wider_scope,
        "future_scope_candidates": future_scope_candidates,
        "representation_scope_ids": sorted(
            {
                str(entry.get("representation_scope_id") or "")
                for entry in support_matrix
                if isinstance(entry, dict) and str(entry.get("representation_scope_id") or "")
            }
        ),
        "dense_sidecar_contract_version": str(
            dict(dense_sidecar.get("contract") or {}).get("storage_contract_version") or ""
        ),
        "dense_sidecar_lifecycle_contract_version": str(
            dict(dense_sidecar.get("contract") or {}).get("lifecycle_contract_version") or ""
        ),
        "dense_sidecar_promotion_contract_ready": bool(
            dense_sidecar.get("promotion_contract_ready")
        ),
        "dense_sidecar_lifecycle_state": str(
            dense_sidecar.get("lifecycle_state") or ""
        ),
        "dense_sidecar_cache_lifecycle_state": str(
            dense_sidecar.get("cache_lifecycle_state") or ""
        ),
        "dense_sidecar_rebuildable_from_projection_records": bool(
            dense_sidecar.get("rebuildable_from_projection_records")
        ),
        "dense_sidecar_requires_process_warmup": bool(
            dense_sidecar.get("requires_process_warmup")
        ),
        "dense_sidecar_warmup_recommended": bool(
            dense_sidecar.get("warmup_recommended")
        ),
        "dense_sidecar_warmup_required_for_peak_performance": bool(
            dense_sidecar.get("warmup_required_for_peak_performance")
        ),
        "dense_sidecar_cold_start_recoverable": bool(
            dense_sidecar.get("cold_start_recoverable")
        ),
        "dense_sidecar_cache_persistence_mode": str(
            dense_sidecar.get("cache_persistence_mode") or ""
        ),
        "dense_sidecar_lifecycle_recovery_mode": str(
            dense_sidecar.get("lifecycle_recovery_mode") or ""
        ),
        "dense_sidecar_lifecycle_recovery_hints": list(
            dense_sidecar.get("lifecycle_recovery_hints") or []
        ),
        "dense_sidecar_warmup_target_route_ids": list(
            dense_sidecar.get("warmup_target_route_ids") or []
        ),
        "dense_sidecar_warmup_command_hint": dense_sidecar.get("warmup_command_hint"),
        "dense_sidecar_persisted_projection_state_available": bool(
            dense_sidecar.get("persisted_projection_state_available")
        ),
        "dense_sidecar_promotion_blockers": list(
            dense_sidecar.get("promotion_blockers") or []
        ),
        "ready_projection_count": int(summary.get("ready_projection_count") or 0),
        "required_projection_count": int(summary.get("required_projection_count") or 0),
        "docs_ref": "docs/database/LOCAL_PROFILE_SCOPE_EXPANSION_CRITERIA.md",
    }


def build_local_profile_scope_expansion_contract_payload(
    *,
    profile: DeploymentProfile,
) -> Dict[str, Any]:
    support_matrix = build_local_route_support_matrix_payload(profile=profile)
    declared_executable_route_ids = sorted(
        str(entry.get("route_id") or "")
        for entry in support_matrix
        if bool(entry.get("declared_executable")) and str(entry.get("route_id") or "")
    )
    lexical_contract = {
        "plain_lexical": "degraded_supported",
        "phrase_semantics": "degraded_supported",
        "operator_heavy_semantics": "degraded_supported",
        "hard_constraints": "unsupported",
        "sparse_retrieval": "unsupported",
        "graph_traversal": "unsupported",
    }
    satisfied_now = [
        "declared_local_slice_supported",
        "declared_local_slice_runtime_ready_after_bootstrap",
        "query_ir_v2_surfaced_for_declared_slice",
        "projection_ir_v2_surfaced_for_declared_slice",
        "dense_sidecar_contract_explicit",
    ]
    required_before_widening = [
        "define_next_embedded_route_slice",
        "add_runtime_validation_and_completion_coverage_for_widened_slice",
        "add_parity_or_no_regression_expectations_for_widened_slice",
        "reassess_dense_sidecar_contract_for_wider_slice",
    ]
    future_scope_candidates = [
        "local_sparse_vector_lane",
        "local_graph_traversal_lane",
        "broader_embedded_route_validation",
        "wider_embedded_parity_gate",
    ]
    return {
        "profile_id": profile.id,
        "maturity": profile.maturity,
        "current_supported_slice_frozen": True,
        "declared_executable_route_ids": declared_executable_route_ids,
        "lexical_contract": lexical_contract,
        "satisfied_now": satisfied_now,
        "required_before_widening": required_before_widening,
        "future_scope_candidates": future_scope_candidates,
        "dense_sidecar_contract_version": LOCAL_DENSE_SIDECAR_ADAPTER.storage_contract_version,
        "dense_sidecar_lifecycle_contract_version": LOCAL_DENSE_SIDECAR_ADAPTER.lifecycle_contract_version,
        "docs_ref": "docs/database/LOCAL_PROFILE_SCOPE_EXPANSION_CRITERIA.md",
        "promotion_docs_ref": "docs/database/LOCAL_PROFILE_PROMOTION_BAR.md",
        "dense_sidecar_docs_ref": "docs/database/LOCAL_DENSE_SIDECAR_CONTRACT.md",
    }


def build_local_profile_diagnostics_payload(
    *,
    profile: DeploymentProfile,
    route_payloads: Optional[Sequence[Dict[str, Any]]] = None,
    projection_diagnostics: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    support_matrix = build_local_route_support_matrix_payload(profile=profile)
    dense_sidecar = build_local_dense_sidecar_status_payload(
        profile=profile,
        projection_diagnostics=projection_diagnostics,
        support_matrix=support_matrix,
    )
    return {
        "support_matrix": support_matrix,
        "projection_plan_v2_registry": build_local_projection_plan_registry_payload(
            profile=profile,
            projection_diagnostics=projection_diagnostics,
        ),
        "route_runtime_contracts": build_local_route_runtime_contracts_payload(
            profile=profile,
            support_matrix=support_matrix,
            route_payloads=route_payloads,
            projection_diagnostics=projection_diagnostics,
        ),
        "dense_sidecar": dense_sidecar,
        "scope_expansion_contract": build_local_profile_scope_expansion_contract_payload(
            profile=profile,
        ),
        "maturity": profile.maturity,
        "docs_ref": "docs/database/LOCAL_PROFILE_V1.md",
    }


def build_local_profile_bringup_payload(
    *,
    profile: DeploymentProfile,
    bringup_payload: Dict[str, Any],
    diagnostics_payload: Optional[Dict[str, Any]] = None,
    projection_diagnostics: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    route_payloads = []
    if diagnostics_payload:
        route_payloads = [
            dict(row)
            for row in list(diagnostics_payload.get("route_executors") or [])
            if isinstance(row, dict)
        ]
    diagnostics_view = build_local_profile_diagnostics_payload(
        profile=profile,
        route_payloads=route_payloads,
        projection_diagnostics=projection_diagnostics,
    )
    return {
        **diagnostics_view,
        "promotion_status": build_local_profile_promotion_status_payload(
            profile=profile,
            bringup_payload=bringup_payload,
            local_profile_payload=diagnostics_view,
        ),
        "scope_expansion_status": build_local_profile_scope_expansion_status_payload(
            profile=profile,
            bringup_payload=bringup_payload,
            local_profile_payload=diagnostics_view,
        ),
        "scope_expansion_contract": build_local_profile_scope_expansion_contract_payload(
            profile=profile,
        ),
        "promotion_docs_ref": "docs/database/LOCAL_PROFILE_PROMOTION_BAR.md",
        "scope_expansion_docs_ref": "docs/database/LOCAL_PROFILE_SCOPE_EXPANSION_CRITERIA.md",
    }

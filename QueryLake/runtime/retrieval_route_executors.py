from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Protocol, Sequence, Union, runtime_checkable

from sqlmodel import Session

from QueryLake.database.sql_db_tables import FILE_CHUNK_INDEXED_COLUMNS as FILE_FIELDS
from QueryLake.misc_functions.paradedb_query_parser import parse_search
from QueryLake.runtime.authority_projection_access import build_projection_materialization_target
from QueryLake.runtime.db_compat import (
    BackendStack,
    DeploymentProfile,
    QueryLakeUnsupportedFeatureError,
    get_deployment_profile,
)
from QueryLake.runtime.retrieval_lane_executors import (
    GoldBM25SearchPlan,
    build_gold_bm25_search_plan,
    execute_gold_bm25_search,
    execute_gold_document_chunk_hybrid_lanes,
    execute_gold_file_chunk_bm25_search,
)
from QueryLake.runtime.opensearch_route_execution import (
    execute_opensearch_document_chunk_bm25_search,
    execute_opensearch_document_chunk_hybrid_search,
    execute_opensearch_file_chunk_bm25_search,
)
from QueryLake.runtime.local_route_execution import (
    SQLiteLocalSearchBM25RouteExecutor,
    SQLiteLocalSearchFileChunkRouteExecutor,
    SQLiteLocalSearchHybridRouteExecutor,
)
from QueryLake.runtime.local_profile_v2 import (
    build_local_query_ir_v2,
    build_local_route_execution_plan_payload,
    build_local_route_projection_ir_v2,
)
from QueryLake.runtime.projection_ir_v2 import (
    ProjectionBuildabilityClass,
    ProjectionDependencyRef,
    RouteProjectionIRV2,
    instantiate_projection_ir_v2,
)
from QueryLake.runtime.query_ir_v2 import FilterIRV2, QueryIRV2, QueryStrictnessPolicy
from QueryLake.runtime.support_manifest_v2 import ROUTE_CAPABILITY_DEPENDENCIES, get_representation_scope
from QueryLake.runtime.retrieval_lanes import RetrievalAdapterResolution, resolve_retrieval_adapter


@runtime_checkable
class SearchHybridRouteExecutorProtocol(Protocol):
    executor_id: str

    def execute(self, database: Session, **kwargs: Any) -> Union[str, List[Any]]: ...


@runtime_checkable
class SearchBM25RouteExecutorProtocol(Protocol):
    executor_id: str

    def execute(self, database: Session, **kwargs: Any) -> "BM25RouteExecution": ...


@runtime_checkable
class SearchFileChunkRouteExecutorProtocol(Protocol):
    executor_id: str

    def execute(self, database: Session, **kwargs: Any) -> "FileChunkRouteExecution": ...


@dataclass(frozen=True)
class RouteExecutorResolution:
    route_id: str
    executor_id: str
    profile_id: str
    implemented: bool
    support_state: str
    backend_stack: BackendStack
    lane_adapters: Dict[str, Dict[str, Any]]
    projection_descriptors: List[str]
    projection_targets: List[Dict[str, Any]] = field(default_factory=list)
    representation_scope_id: str = ""
    representation_scope: Dict[str, Any] = field(default_factory=dict)
    planning_v2: Dict[str, Any] = field(default_factory=dict)
    notes: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["backend_stack"] = asdict(self.backend_stack)
        return payload


@dataclass(frozen=True)
class ResolvedRouteExecutor:
    resolution: RouteExecutorResolution
    executor: Any
    blocking_capability: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        return self.resolution.to_payload()

    def require_executable(self, *, allow_plan_only: bool = False) -> None:
        if self.resolution.implemented:
            return
        if allow_plan_only and bool(getattr(self.executor, "supports_plan_only", False)):
            return
        capability = self.blocking_capability or "retrieval.execution"
        route_name = self.resolution.route_id
        hint = (
            f"Use the ParadeDB/PostgreSQL gold profile or disable the unsupported lane(s) for route '{route_name}'."
        )
        raise QueryLakeUnsupportedFeatureError(
            capability=capability,
            profile=self.resolution.profile_id,
            support_state=self.resolution.support_state,  # type: ignore[arg-type]
            backend_stack=self.resolution.backend_stack,
            hint=hint,
            message=(
                f"Route executor '{self.resolution.executor_id}' for route '{route_name}' is not executable on deployment "
                f"profile '{self.resolution.profile_id}'."
            ),
        )


@dataclass(frozen=True)
class BM25RouteExecution:
    rows_or_statement: Union[str, List[Any]]
    formatted_query: str
    quoted_phrases: Sequence[str]
    plan: GoldBM25SearchPlan


@dataclass(frozen=True)
class FileChunkRouteExecution:
    rows_or_statement: Union[str, List[Any]]
    query_is_empty: bool


@dataclass(frozen=True)
class GoldSearchHybridRouteExecutor:
    executor_id: str = "gold.search_hybrid.document_chunk.sql.v1"

    def execute(self, database: Session, **kwargs: Any) -> Union[str, List[Any]]:
        return execute_gold_document_chunk_hybrid_lanes(
            database,
            collection_spec=kwargs["collection_spec"],
            formatted_query=kwargs["formatted_query"],
            strong_where_clause=kwargs.get("strong_where_clause"),
            similarity_constraint=kwargs["similarity_constraint"],
            retrieved_fields_string=kwargs["retrieved_fields_string"],
            use_bm25=bool(kwargs["use_bm25"]),
            use_similarity=bool(kwargs["use_similarity"]),
            use_sparse=bool(kwargs["use_sparse"]),
            limit_bm25=int(kwargs["limit_bm25"]),
            limit_similarity=int(kwargs["limit_similarity"]),
            limit_sparse=int(kwargs["limit_sparse"]),
            similarity_weight=float(kwargs["similarity_weight"]),
            bm25_weight=float(kwargs["bm25_weight"]),
            sparse_weight=float(kwargs["sparse_weight"]),
            embedding=kwargs.get("embedding"),
            embedding_sparse=kwargs.get("embedding_sparse"),
            sparse_dimensions=int(kwargs["sparse_dimensions"]),
            return_statement=bool(kwargs.get("return_statement", False)),
        )


@dataclass(frozen=True)
class GoldSearchBM25RouteExecutor:
    executor_id: str = "gold.search_bm25.sql.v1"

    def execute(self, database: Session, **kwargs: Any) -> BM25RouteExecution:
        plan = build_gold_bm25_search_plan(
            query=kwargs["query"],
            valid_fields=kwargs["valid_fields"],
            catch_all_fields=kwargs["catch_all_fields"],
            table=kwargs["table"],
            collection_ids=kwargs["collection_ids"],
            sort_by=kwargs["sort_by"],
            sort_dir=kwargs["sort_dir"],
            document_collection_attrs=kwargs["document_collection_attrs"],
        )
        rows_or_statement = execute_gold_bm25_search(
            database,
            chosen_table_name=kwargs["chosen_table_name"],
            chosen_attributes=kwargs["chosen_attributes"],
            parse_field=plan.parse_field,
            order_by_field=plan.order_by_field,
            limit=int(kwargs["limit"]),
            offset=int(kwargs["offset"]),
            table=str(kwargs["table"]),
            formatted_query=plan.formatted_query,
            quoted_phrases=plan.quoted_phrases,
            segment_collection_filter=plan.segment_collection_filter,
            return_statement=bool(kwargs.get("return_statement", False)),
        )
        return BM25RouteExecution(
            rows_or_statement=rows_or_statement,
            formatted_query=plan.formatted_query,
            quoted_phrases=plan.quoted_phrases,
            plan=plan,
        )


@dataclass(frozen=True)
class GoldSearchFileChunkRouteExecutor:
    executor_id: str = "gold.search_file_chunks.sql.v1"

    def execute(self, database: Session, **kwargs: Any) -> FileChunkRouteExecution:
        rows_or_statement = execute_gold_file_chunk_bm25_search(
            database,
            username=kwargs["username"],
            query=kwargs["query"],
            sort_by=kwargs["sort_by"],
            sort_dir=kwargs["sort_dir"],
            limit=int(kwargs["limit"]),
            offset=int(kwargs["offset"]),
            return_statement=bool(kwargs.get("return_statement", False)),
        )
        formatted_query, _ = parse_search(str(kwargs["query"] or ""), FILE_FIELDS, catch_all_fields=["text"])
        query_is_empty = formatted_query == "()"
        return FileChunkRouteExecution(
            rows_or_statement=rows_or_statement,
            query_is_empty=query_is_empty,
        )


@dataclass(frozen=True)
class OpenSearchDocumentChunkHybridRouteExecutor:
    projection_descriptors: tuple[str, ...]
    executor_id: str = "opensearch.search_hybrid.document_chunk.v1"

    def execute(self, database: Session, **kwargs: Any) -> Union[str, List[Any]]:
        return execute_opensearch_document_chunk_hybrid_search(
            database,
            projection_descriptors=self.projection_descriptors,
            raw_query_text=str(kwargs.get("raw_query_text", "") or ""),
            collection_ids=list(kwargs.get("collection_ids", [])),
            use_bm25=bool(kwargs["use_bm25"]),
            use_similarity=bool(kwargs["use_similarity"]),
            use_sparse=bool(kwargs["use_sparse"]),
            limit_bm25=int(kwargs["limit_bm25"]),
            limit_similarity=int(kwargs["limit_similarity"]),
            limit_sparse=int(kwargs["limit_sparse"]),
            similarity_weight=float(kwargs["similarity_weight"]),
            bm25_weight=float(kwargs["bm25_weight"]),
            sparse_weight=float(kwargs["sparse_weight"]),
            embedding=kwargs.get("embedding") or [],
            return_statement=bool(kwargs.get("return_statement", False)),
        )


@dataclass(frozen=True)
class OpenSearchDocumentChunkBM25RouteExecutor:
    projection_id: str
    executor_id: str = "opensearch.search_bm25.document_chunk.v1"

    def execute(self, database: Session, **kwargs: Any) -> BM25RouteExecution:
        plan, rows_or_statement = execute_opensearch_document_chunk_bm25_search(
            database,
            projection_id=self.projection_id,
            query=str(kwargs["query"] or ""),
            collection_ids=list(kwargs["collection_ids"]),
            sort_by=str(kwargs["sort_by"]),
            sort_dir=str(kwargs["sort_dir"]),
            limit=int(kwargs["limit"]),
            offset=int(kwargs["offset"]),
            return_statement=bool(kwargs.get("return_statement", False)),
        )
        return BM25RouteExecution(
            rows_or_statement=rows_or_statement,
            formatted_query=plan.formatted_query,
            quoted_phrases=plan.quoted_phrases,
            plan=plan,
        )


@dataclass(frozen=True)
class OpenSearchFileChunkRouteExecutor:
    projection_id: str
    executor_id: str = "opensearch.search_file_chunks.v1"

    def execute(self, database: Session, **kwargs: Any) -> FileChunkRouteExecution:
        query_is_empty, rows_or_statement = execute_opensearch_file_chunk_bm25_search(
            database,
            projection_id=self.projection_id,
            username=str(kwargs["username"]),
            query=str(kwargs["query"] or ""),
            sort_by=str(kwargs["sort_by"]),
            sort_dir=str(kwargs["sort_dir"]),
            limit=int(kwargs["limit"]),
            offset=int(kwargs["offset"]),
            return_statement=bool(kwargs.get("return_statement", False)),
        )
        return FileChunkRouteExecution(
            rows_or_statement=rows_or_statement,
            query_is_empty=query_is_empty,
        )


@dataclass(frozen=True)
class PlaceholderSearchHybridRouteExecutor:
    executor_id: str
    route_id: str
    profile_id: str
    support_state: str
    backend_stack: BackendStack
    capability: str

    def execute(self, database: Session, **kwargs: Any) -> Union[str, List[Any]]:
        raise QueryLakeUnsupportedFeatureError(
            capability=self.capability,
            profile=self.profile_id,
            support_state=self.support_state,  # type: ignore[arg-type]
            backend_stack=self.backend_stack,
            hint=f"Use the ParadeDB/PostgreSQL gold profile or disable unsupported hybrid lanes on route '{self.route_id}'.",
            message=(
                f"Route executor '{self.executor_id}' for route '{self.route_id}' is not executable on deployment profile "
                f"'{self.profile_id}'."
            ),
        )


@dataclass(frozen=True)
class PlaceholderSearchBM25RouteExecutor:
    executor_id: str
    route_id: str
    profile_id: str
    support_state: str
    backend_stack: BackendStack
    capability: str

    def execute(self, database: Session, **kwargs: Any) -> BM25RouteExecution:
        raise QueryLakeUnsupportedFeatureError(
            capability=self.capability,
            profile=self.profile_id,
            support_state=self.support_state,  # type: ignore[arg-type]
            backend_stack=self.backend_stack,
            hint=f"Use the ParadeDB/PostgreSQL gold profile or disable unsupported BM25 routes on '{self.route_id}'.",
            message=(
                f"Route executor '{self.executor_id}' for route '{self.route_id}' is not executable on deployment profile "
                f"'{self.profile_id}'."
            ),
        )


@dataclass(frozen=True)
class PlaceholderSearchFileChunkRouteExecutor:
    executor_id: str
    route_id: str
    profile_id: str
    support_state: str
    backend_stack: BackendStack
    capability: str

    def execute(self, database: Session, **kwargs: Any) -> FileChunkRouteExecution:
        raise QueryLakeUnsupportedFeatureError(
            capability=self.capability,
            profile=self.profile_id,
            support_state=self.support_state,  # type: ignore[arg-type]
            backend_stack=self.backend_stack,
            hint=f"Use the ParadeDB/PostgreSQL gold profile or disable unsupported file-chunk lexical search on '{self.route_id}'.",
            message=(
                f"Route executor '{self.executor_id}' for route '{self.route_id}' is not executable on deployment profile "
                f"'{self.profile_id}'."
            ),
        )


def _summarize_route_support(
    lane_adapters: Dict[str, RetrievalAdapterResolution],
) -> tuple[bool, str, Optional[str]]:
    degraded_capability: Optional[str] = None
    for adapter in lane_adapters.values():
        if not adapter.implemented:
            capability = adapter.required_capabilities[0] if len(adapter.required_capabilities) > 0 else None
            return False, "planned", capability
        if adapter.support_state == "unsupported":
            capability = adapter.required_capabilities[0] if len(adapter.required_capabilities) > 0 else None
            return False, "unsupported", capability
        if adapter.support_state == "planned":
            capability = adapter.required_capabilities[0] if len(adapter.required_capabilities) > 0 else None
            return False, "planned", capability
        if adapter.support_state == "degraded" and degraded_capability is None:
            degraded_capability = adapter.required_capabilities[0] if len(adapter.required_capabilities) > 0 else None
    if degraded_capability is not None:
        return True, "degraded", None
    return True, "supported", None


def _build_route_resolution(
    *,
    route_id: str,
    executor_id: str,
    profile: DeploymentProfile,
    lane_adapters: Dict[str, RetrievalAdapterResolution],
    projection_descriptors: List[str],
    notes: Optional[str] = None,
    planning_v2: Optional[Dict[str, Any]] = None,
) -> tuple[RouteExecutorResolution, Optional[str]]:
    implemented, support_state, blocking_capability = _summarize_route_support(lane_adapters)
    projection_targets = _build_route_projection_targets(
        profile=profile,
        lane_adapters=lane_adapters,
        projection_descriptors=projection_descriptors,
    )
    representation_scope = get_representation_scope(route_id)
    effective_planning_v2 = dict(planning_v2 or {})
    if not effective_planning_v2:
        effective_planning_v2 = _build_route_planning_v2(
            profile=profile,
            route_id=route_id,
            support_state=support_state,
            projection_targets=projection_targets,
            use_dense=("dense" in lane_adapters),
            use_sparse=("sparse" in lane_adapters),
        )
    resolution = RouteExecutorResolution(
        route_id=route_id,
        executor_id=executor_id,
        profile_id=profile.id,
        implemented=implemented,
        support_state=support_state,
        representation_scope_id=representation_scope.scope_id,
        representation_scope=representation_scope.model_dump(),
        backend_stack=profile.backend_stack,
        lane_adapters={name: adapter.to_payload() for name, adapter in lane_adapters.items()},
        projection_descriptors=list(projection_descriptors),
        projection_targets=projection_targets,
        planning_v2=effective_planning_v2,
        notes=notes,
    )
    return resolution, blocking_capability


def _fallback_backend_name_for_lane(*, lane_family: str, profile: DeploymentProfile) -> str:
    if lane_family == "lexical":
        return profile.backend_stack.lexical
    if lane_family == "dense":
        return profile.backend_stack.dense
    if lane_family == "sparse":
        return profile.backend_stack.sparse
    if lane_family == "graph":
        return profile.backend_stack.graph
    return profile.backend_stack.authority


def _build_route_projection_targets(
    *,
    profile: DeploymentProfile,
    lane_adapters: Dict[str, RetrievalAdapterResolution],
    projection_descriptors: Sequence[str],
) -> List[Dict[str, Any]]:
    lane_backend_overrides: Dict[str, str] = {}
    for adapter in lane_adapters.values():
        lane_backend = str(adapter.backend or "")
        if lane_backend:
            lane_backend_overrides[str(adapter.lane_family)] = lane_backend
    targets: List[Dict[str, Any]] = []
    for projection_id in projection_descriptors:
        materialization_target = build_projection_materialization_target(
            projection_id=projection_id,
            target_backend_name="unknown",
        )
        lane_family = materialization_target.lane_family
        target_backend_name = lane_backend_overrides.get(
            lane_family,
            _fallback_backend_name_for_lane(lane_family=lane_family, profile=profile),
        )
        materialization_target = build_projection_materialization_target(
            projection_id=projection_id,
            target_backend_name=target_backend_name,
            metadata={
                "profile_id": profile.id,
                "route_projection": True,
            },
        )
        targets.append(materialization_target.model_dump())
    return targets


def _generic_query_ir_v2_template(
    *,
    route_id: str,
    raw_query_text: str,
    use_dense: bool,
    use_sparse: bool,
    collection_ids: Sequence[str],
    support_state: str,
) -> Dict[str, Any]:
    scope = get_representation_scope(route_id)
    strictness = (
        QueryStrictnessPolicy.approximate
        if support_state == "degraded"
        else QueryStrictnessPolicy.exact
    )
    lexical_query_text = raw_query_text if route_id != "search_hybrid.document_chunk" or raw_query_text.strip() else ""
    query_ir = QueryIRV2(
        raw_query_text=raw_query_text,
        normalized_query_text=raw_query_text.strip(),
        lexical_query_text=lexical_query_text,
        use_dense=bool(use_dense),
        use_sparse=bool(use_sparse),
        filter_ir=FilterIRV2(collection_ids=list(collection_ids)),
        strictness_policy=strictness,
        representation_scope_id=scope.scope_id,
        route_id=route_id,
        planner_hints={
            "planning_surface": "route_resolution",
            "query_features": {},
        },
        metadata={
            "route_family": route_id.split('.')[0],
        },
    )
    return query_ir.model_dump()


def _generic_route_projection_ir_v2(
    *,
    profile: DeploymentProfile,
    route_id: str,
    projection_targets: Sequence[Dict[str, Any]],
    support_state: str,
) -> Dict[str, Any]:
    scope = get_representation_scope(route_id)
    if support_state == "supported":
        buildability = ProjectionBuildabilityClass.executable_requires_build
    elif support_state == "degraded":
        buildability = ProjectionBuildabilityClass.degraded_executable
    elif support_state == "planned":
        buildability = ProjectionBuildabilityClass.planned
    else:
        buildability = ProjectionBuildabilityClass.unsupported
    required_targets = [
        ProjectionDependencyRef(
            target_id=str(target.get("projection_id") or ""),
            required=True,
            target_backend_family=str(target.get("target_backend_family") or "unknown"),
            support_state=support_state,
            metadata={
                "target_backend_name": str(target.get("target_backend_name") or ""),
                "lane_family": str(target.get("lane_family") or ""),
            },
        )
        for target in projection_targets
        if str(target.get("projection_id") or "")
    ]
    projection_ir = instantiate_projection_ir_v2(
        None,
        profile_id=profile.id,
        route_id=route_id,
        representation_scope_id=scope.scope_id,
        required_targets=[item.model_dump() for item in required_targets],
        optional_targets=[],
        capability_dependencies=list(ROUTE_CAPABILITY_DEPENDENCIES.get(route_id, [])),
        runtime_blockers=(
            ["projection_build_required"] if len(required_targets) > 0 and support_state in {"supported", "degraded"} else []
        ),
        buildability_class=buildability,
        recovery_hints=(
            ["bootstrap_required_projections"] if len(required_targets) > 0 and support_state in {"supported", "degraded"} else []
        ),
        metadata={
            "planning_surface": "route_resolution",
            "backend_stack": profile.backend_stack.__dict__,
        },
    )
    return projection_ir.model_dump()


def _build_route_planning_v2(
    *,
    profile: DeploymentProfile,
    route_id: str,
    support_state: str,
    projection_targets: Sequence[Dict[str, Any]],
    raw_query_text: str = "",
    use_dense: bool = False,
    use_sparse: bool = False,
    collection_ids: Sequence[str] = (),
    return_statement: bool = False,
) -> Dict[str, Any]:
    return {
        "query_ir_v2_template": _generic_query_ir_v2_template(
            route_id=route_id,
            raw_query_text=raw_query_text,
            use_dense=use_dense,
            use_sparse=use_sparse,
            collection_ids=collection_ids,
            support_state=support_state,
        ),
        "projection_ir_v2": _generic_route_projection_ir_v2(
            profile=profile,
            route_id=route_id,
            projection_targets=projection_targets,
            support_state=support_state,
        ),
        "return_statement_default": bool(return_statement),
        "planning_surface": "route_resolution",
    }


def _document_chunk_projection_descriptors(*, use_similarity: bool, use_sparse: bool) -> List[str]:
    descriptors = ["document_chunk_lexical_projection_v1"]
    if use_similarity:
        descriptors.append("document_chunk_dense_projection_v1")
    if use_sparse:
        descriptors.append("document_chunk_sparse_projection_v1")
    return descriptors


def resolve_search_hybrid_route_executor(
    *,
    use_bm25: bool,
    use_similarity: bool,
    use_sparse: bool,
    profile: Optional[DeploymentProfile] = None,
) -> ResolvedRouteExecutor:
    effective_profile = profile or get_deployment_profile()
    lane_adapters: Dict[str, RetrievalAdapterResolution] = {}
    if use_bm25:
        lane_adapters["bm25"] = resolve_retrieval_adapter("BM25RetrieverParadeDB", profile=effective_profile)
    if use_similarity:
        lane_adapters["dense"] = resolve_retrieval_adapter("DenseRetrieverPGVector", profile=effective_profile)
    if use_sparse:
        lane_adapters["sparse"] = resolve_retrieval_adapter("SparseRetrieverPGVector", profile=effective_profile)

    projection_descriptors = (
        []
        if effective_profile.id == "postgres_pgvector_light_v1"
        else _document_chunk_projection_descriptors(
            use_similarity=bool(use_similarity),
            use_sparse=bool(use_sparse),
        )
    )

    resolution, blocking_capability = _build_route_resolution(
        route_id="search_hybrid.document_chunk",
        executor_id=(
            "gold.search_hybrid.document_chunk.sql.v1"
            if effective_profile.id == "paradedb_postgres_gold_v1"
            else "pgvector.search_hybrid.document_chunk.dense_only.v1"
            if effective_profile.id == "postgres_pgvector_light_v1"
            and not use_bm25
            and use_similarity
            and not use_sparse
            else "sqlite_local.search_hybrid.document_chunk.v1"
            if effective_profile.id == "sqlite_fts5_dense_sidecar_local_v1"
            else "opensearch.search_hybrid.document_chunk.v1"
            if effective_profile.id == "aws_aurora_pg_opensearch_v1" and not use_sparse
            else f"placeholder.search_hybrid.document_chunk.{effective_profile.id}"
        ),
        profile=effective_profile,
        lane_adapters=lane_adapters,
        projection_descriptors=projection_descriptors,
        planning_v2=(
            build_local_route_execution_plan_payload(
                "search_hybrid.document_chunk",
                profile=effective_profile,
                raw_query_text="",
                support_state="supported",
                use_dense=bool(use_similarity),
                use_sparse=bool(use_sparse),
                collection_ids=[],
                return_statement=False,
                runtime_ready=False,
                runtime_blockers=["projection_build_required"],
            )
            if effective_profile.id == "sqlite_fts5_dense_sidecar_local_v1"
            else {}
        ),
        notes="Hybrid route executor over lexical/dense/sparse lane adapters.",
    )
    executor: SearchHybridRouteExecutorProtocol
    if resolution.implemented and effective_profile.id in {"paradedb_postgres_gold_v1", "postgres_pgvector_light_v1"}:
        executor = GoldSearchHybridRouteExecutor()
    elif resolution.implemented and effective_profile.id == "aws_aurora_pg_opensearch_v1" and not use_sparse:
        executor = OpenSearchDocumentChunkHybridRouteExecutor(
            projection_descriptors=tuple(resolution.projection_descriptors),
        )
    elif effective_profile.id == "sqlite_fts5_dense_sidecar_local_v1":
        executor = SQLiteLocalSearchHybridRouteExecutor(
            executor_id=resolution.executor_id,
            route_id=resolution.route_id,
            profile_id=effective_profile.id,
            support_state=resolution.support_state,
            backend_stack=effective_profile.backend_stack,
            capability=blocking_capability or "retrieval.execution",
        )
    else:
        executor = PlaceholderSearchHybridRouteExecutor(
            executor_id=resolution.executor_id,
            route_id=resolution.route_id,
            profile_id=effective_profile.id,
            support_state=resolution.support_state,
            backend_stack=effective_profile.backend_stack,
            capability=blocking_capability or "retrieval.execution",
        )
    return ResolvedRouteExecutor(resolution=resolution, executor=executor, blocking_capability=blocking_capability)


def resolve_search_bm25_route_executor(
    *,
    table: str,
    profile: Optional[DeploymentProfile] = None,
) -> ResolvedRouteExecutor:
    effective_profile = profile or get_deployment_profile()
    lane_adapters = {"bm25": resolve_retrieval_adapter("BM25RetrieverParadeDB", profile=effective_profile)}
    resolution, blocking_capability = _build_route_resolution(
        route_id=f"search_bm25.{table}",
        executor_id=(
            "gold.search_bm25.sql.v1"
            if effective_profile.id == "paradedb_postgres_gold_v1"
            else "sqlite_local.search_bm25.document_chunk.v1"
            if effective_profile.id == "sqlite_fts5_dense_sidecar_local_v1" and table == "document_chunk"
            else "opensearch.search_bm25.document_chunk.v1"
            if effective_profile.id == "aws_aurora_pg_opensearch_v1" and table == "document_chunk"
            else f"placeholder.search_bm25.{table}.{effective_profile.id}"
        ),
        profile=effective_profile,
        lane_adapters=lane_adapters,
        projection_descriptors=[
            "document_chunk_lexical_projection_v1" if table == "document_chunk" else "segment_lexical_projection_v1"
        ],
        planning_v2=(
            build_local_route_execution_plan_payload(
                f"search_bm25.{table}",
                profile=effective_profile,
                raw_query_text="",
                support_state="degraded",
                use_dense=False,
                use_sparse=False,
                collection_ids=[],
                return_statement=False,
                runtime_ready=False,
                runtime_blockers=["projection_build_required"],
            )
            if effective_profile.id == "sqlite_fts5_dense_sidecar_local_v1" and table == "document_chunk"
            else {}
        ),
        notes="BM25 route executor over the lexical lane adapter.",
    )
    if effective_profile.id == "aws_aurora_pg_opensearch_v1" and table != "document_chunk":
        resolution = RouteExecutorResolution(
            route_id=resolution.route_id,
            executor_id=resolution.executor_id,
            profile_id=resolution.profile_id,
            implemented=False,
            support_state="unsupported",
            backend_stack=resolution.backend_stack,
            lane_adapters=resolution.lane_adapters,
            projection_descriptors=resolution.projection_descriptors,
            notes="Only document_chunk BM25 is executable on the first OpenSearch split-stack slice.",
        )
        blocking_capability = "retrieval.segment_search" if table == "segment" else "retrieval.lexical.bm25"
    executor: SearchBM25RouteExecutorProtocol
    if resolution.implemented and effective_profile.id == "paradedb_postgres_gold_v1":
        executor = GoldSearchBM25RouteExecutor()
    elif resolution.implemented and effective_profile.id == "aws_aurora_pg_opensearch_v1" and table == "document_chunk":
        executor = OpenSearchDocumentChunkBM25RouteExecutor(
            projection_id=resolution.projection_descriptors[0],
        )
    elif effective_profile.id == "sqlite_fts5_dense_sidecar_local_v1" and table == "document_chunk":
        executor = SQLiteLocalSearchBM25RouteExecutor(
            executor_id=resolution.executor_id,
            route_id=resolution.route_id,
            profile_id=effective_profile.id,
            support_state=resolution.support_state,
            backend_stack=effective_profile.backend_stack,
            capability=blocking_capability or "retrieval.lexical.bm25",
        )
    else:
        executor = PlaceholderSearchBM25RouteExecutor(
            executor_id=resolution.executor_id,
            route_id=resolution.route_id,
            profile_id=effective_profile.id,
            support_state=resolution.support_state,
            backend_stack=effective_profile.backend_stack,
            capability=blocking_capability or "retrieval.lexical.bm25",
        )
    return ResolvedRouteExecutor(resolution=resolution, executor=executor, blocking_capability=blocking_capability)


def resolve_search_file_chunks_route_executor(
    *,
    profile: Optional[DeploymentProfile] = None,
) -> ResolvedRouteExecutor:
    effective_profile = profile or get_deployment_profile()
    lane_adapters = {"bm25": resolve_retrieval_adapter("FileChunkBM25RetrieverSQL", profile=effective_profile)}
    resolution, blocking_capability = _build_route_resolution(
        route_id="search_file_chunks",
        executor_id=(
            "gold.search_file_chunks.sql.v1"
            if effective_profile.id == "paradedb_postgres_gold_v1"
            else "sqlite_local.search_file_chunks.v1"
            if effective_profile.id == "sqlite_fts5_dense_sidecar_local_v1"
            else "opensearch.search_file_chunks.v1"
            if effective_profile.id == "aws_aurora_pg_opensearch_v1"
            else f"placeholder.search_file_chunks.{effective_profile.id}"
        ),
        profile=effective_profile,
        lane_adapters=lane_adapters,
        projection_descriptors=["file_chunk_lexical_projection_v1"],
        planning_v2=(
            build_local_route_execution_plan_payload(
                "search_file_chunks",
                profile=effective_profile,
                raw_query_text="",
                support_state="degraded",
                use_dense=False,
                use_sparse=False,
                collection_ids=[],
                return_statement=False,
                runtime_ready=False,
                runtime_blockers=["projection_build_required"],
            )
            if effective_profile.id == "sqlite_fts5_dense_sidecar_local_v1"
            else {}
        ),
        notes="File-chunk lexical BM25 route executor over the file lexical lane adapter.",
    )
    executor: SearchFileChunkRouteExecutorProtocol
    if resolution.implemented and effective_profile.id == "paradedb_postgres_gold_v1":
        executor = GoldSearchFileChunkRouteExecutor()
    elif resolution.implemented and effective_profile.id == "aws_aurora_pg_opensearch_v1":
        executor = OpenSearchFileChunkRouteExecutor(
            projection_id=resolution.projection_descriptors[0],
        )
    elif effective_profile.id == "sqlite_fts5_dense_sidecar_local_v1":
        executor = SQLiteLocalSearchFileChunkRouteExecutor(
            executor_id=resolution.executor_id,
            route_id=resolution.route_id,
            profile_id=effective_profile.id,
            support_state=resolution.support_state,
            backend_stack=effective_profile.backend_stack,
            capability=blocking_capability or "retrieval.lexical.bm25",
        )
    else:
        executor = PlaceholderSearchFileChunkRouteExecutor(
            executor_id=resolution.executor_id,
            route_id=resolution.route_id,
            profile_id=effective_profile.id,
            support_state=resolution.support_state,
            backend_stack=effective_profile.backend_stack,
            capability=blocking_capability or "retrieval.lexical.bm25",
        )
    return ResolvedRouteExecutor(resolution=resolution, executor=executor, blocking_capability=blocking_capability)

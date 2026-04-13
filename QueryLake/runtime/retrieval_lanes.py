from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Awaitable, Callable, Dict, Optional, Union

from QueryLake.runtime.db_compat import (
    CapabilityDescriptor,
    DeploymentProfile,
    QueryLakeUnsupportedFeatureError,
    get_deployment_profile,
    require_capability,
)
from QueryLake.runtime.retrieval_primitives_legacy import (
    BM25RetrieverParadeDB,
    DenseRetrieverPGVector,
    FileChunkBM25RetrieverSQL,
    SparseRetrieverPGVector,
)

RetrieverBuilder = Callable[..., Any]


@dataclass(frozen=True)
class RetrievalLaneBinding:
    primitive_id: str
    lane_family: str
    required_capabilities: tuple[str, ...]
    builder: RetrieverBuilder
    notes: Optional[str] = None


@dataclass(frozen=True)
class RetrievalAdapterResolution:
    primitive_id: str
    lane_family: str
    adapter_id: str
    profile_id: str
    backend: str
    support_state: str
    implemented: bool
    required_capabilities: tuple[str, ...]

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RetrievalLaneContract:
    lane_family: str
    capability_ids: tuple[str, ...]
    summary: str
    route_surface_declared: bool = True
    notes: Optional[str] = None


@dataclass(frozen=True)
class RetrievalLaneDiagnostic:
    lane_family: str
    backend: str
    adapter_id: str
    support_state: str
    implemented: bool
    route_surface_declared: bool
    capability_ids: tuple[str, ...]
    execution_mode: str = "native"
    blocked_by_capability: Optional[str] = None
    placeholder_executor_id: Optional[str] = None
    recommended_profile_id: Optional[str] = None
    hint: Optional[str] = None
    notes: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


GOLD_RETRIEVAL_LANE_BINDINGS: Dict[str, RetrievalLaneBinding] = {
    "BM25RetrieverParadeDB": RetrievalLaneBinding(
        primitive_id="BM25RetrieverParadeDB",
        lane_family="lexical_bm25",
        required_capabilities=("retrieval.lexical.bm25", "retrieval.lexical.advanced_operators"),
        builder=lambda **kwargs: BM25RetrieverParadeDB(
            database=kwargs["database"],
            auth=kwargs["auth"],
            search_bm25_fn=kwargs.get("search_bm25_fn"),
        ),
        notes="Canonical lexical BM25 lane on ParadeDB/Postgres.",
    ),
    "DenseRetrieverPGVector": RetrievalLaneBinding(
        primitive_id="DenseRetrieverPGVector",
        lane_family="dense_vector",
        required_capabilities=("retrieval.dense.vector",),
        builder=lambda **kwargs: DenseRetrieverPGVector(
            database=kwargs["database"],
            auth=kwargs["auth"],
            toolchain_function_caller=kwargs["toolchain_function_caller"],
            search_hybrid_fn=kwargs.get("search_hybrid_fn"),
        ),
        notes="Canonical dense vector lane on pgvector.",
    ),
    "SparseRetrieverPGVector": RetrievalLaneBinding(
        primitive_id="SparseRetrieverPGVector",
        lane_family="sparse_vector",
        required_capabilities=("retrieval.sparse.vector",),
        builder=lambda **kwargs: SparseRetrieverPGVector(
            database=kwargs["database"],
            auth=kwargs["auth"],
            toolchain_function_caller=kwargs["toolchain_function_caller"],
            search_hybrid_fn=kwargs.get("search_hybrid_fn"),
        ),
        notes="Canonical sparse vector lane on pgvector sparsevec.",
    ),
    "FileChunkBM25RetrieverSQL": RetrievalLaneBinding(
        primitive_id="FileChunkBM25RetrieverSQL",
        lane_family="lexical_file_bm25",
        required_capabilities=("retrieval.lexical.bm25",),
        builder=lambda **kwargs: FileChunkBM25RetrieverSQL(
            database=kwargs["database"],
            auth=kwargs["auth"],
            search_file_chunks_fn=kwargs.get("search_file_chunks_fn"),
        ),
        notes="Lexical file-chunk retrieval lane backed by SQL search path.",
    ),
}


RETRIEVAL_LANE_CONTRACTS: Dict[str, RetrievalLaneContract] = {
    "lexical_bm25": RetrievalLaneContract(
        lane_family="lexical_bm25",
        capability_ids=("retrieval.lexical.bm25", "retrieval.lexical.advanced_operators"),
        summary="Lexical BM25 lane for document-chunk retrieval.",
        route_surface_declared=True,
    ),
    "lexical_file_bm25": RetrievalLaneContract(
        lane_family="lexical_file_bm25",
        capability_ids=("retrieval.lexical.bm25",),
        summary="Lexical BM25 lane for file-chunk retrieval.",
        route_surface_declared=True,
    ),
    "dense_vector": RetrievalLaneContract(
        lane_family="dense_vector",
        capability_ids=("retrieval.dense.vector",),
        summary="Dense vector lane for document-chunk retrieval.",
        route_surface_declared=True,
    ),
    "sparse_vector": RetrievalLaneContract(
        lane_family="sparse_vector",
        capability_ids=("retrieval.sparse.vector",),
        summary="Sparse vector lane for hybrid retrieval where the profile supports it.",
        route_surface_declared=False,
        notes="The compatibility layer does not expose a standalone sparse route surface yet; this lane currently appears only inside hybrid retrieval.",
    ),
    "graph_traversal": RetrievalLaneContract(
        lane_family="graph_traversal",
        capability_ids=("retrieval.graph.traversal",),
        summary="Graph / segment-adjacency lane reserved for traversal-capable profiles.",
        route_surface_declared=False,
        notes="The compatibility layer reserves this lane contract even where no executable graph route surface exists yet.",
    ),
}


PROFILE_LANE_ADAPTERS: Dict[str, Dict[str, Dict[str, Any]]] = {
    "paradedb_postgres_gold_v1": {
        "lexical_bm25": {"adapter_id": "paradedb_bm25_v1", "backend": "paradedb", "implemented": True},
        "lexical_file_bm25": {"adapter_id": "paradedb_file_chunk_bm25_v1", "backend": "paradedb", "implemented": True},
        "dense_vector": {"adapter_id": "pgvector_halfvec_v1", "backend": "pgvector_halfvec", "implemented": True},
        "sparse_vector": {"adapter_id": "pgvector_sparsevec_v1", "backend": "pgvector_sparsevec", "implemented": True},
        "graph_traversal": {"adapter_id": "postgresql_segment_relations_v1", "backend": "postgresql_segment_relations", "implemented": False},
    },
    "postgres_pgvector_light_v1": {
        "lexical_bm25": {"adapter_id": "none", "backend": "none", "implemented": False},
        "lexical_file_bm25": {"adapter_id": "none", "backend": "none", "implemented": False},
        "dense_vector": {"adapter_id": "pgvector_halfvec_v1", "backend": "pgvector_halfvec", "implemented": True},
        "sparse_vector": {"adapter_id": "none", "backend": "none", "implemented": False},
        "graph_traversal": {"adapter_id": "postgresql_segment_relations_v1", "backend": "postgresql_segment_relations", "implemented": False},
    },
    "aws_aurora_pg_opensearch_v1": {
        "lexical_bm25": {"adapter_id": "opensearch_bm25_v1", "backend": "opensearch", "implemented": True},
        "lexical_file_bm25": {"adapter_id": "opensearch_file_bm25_v1", "backend": "opensearch", "implemented": True},
        "dense_vector": {"adapter_id": "opensearch_dense_knn_v1", "backend": "opensearch", "implemented": True},
        "sparse_vector": {"adapter_id": "opensearch_sparse_knn_v1", "backend": "opensearch", "implemented": False},
        "graph_traversal": {"adapter_id": "aurora_segment_relations_v1", "backend": "aurora_postgresql_segment_relations", "implemented": False},
    },
    "sqlite_fts5_dense_sidecar_local_v1": {
        "lexical_bm25": {"adapter_id": "sqlite_fts5_bm25_v1", "backend": "sqlite_fts5", "implemented": True},
        "lexical_file_bm25": {"adapter_id": "sqlite_fts5_file_chunk_bm25_v1", "backend": "sqlite_fts5", "implemented": True},
        "dense_vector": {"adapter_id": "local_dense_sidecar_v1", "backend": "local_dense_sidecar", "implemented": True},
        "sparse_vector": {"adapter_id": "local_sparse_sidecar_v1", "backend": "local_sparse_sidecar", "implemented": False},
        "graph_traversal": {"adapter_id": "sqlite_relation_graph_v1", "backend": "sqlite_relation_graph", "implemented": False},
    },
    "mongo_opensearch_v1": {
        "lexical_bm25": {"adapter_id": "opensearch_bm25_v1", "backend": "opensearch", "implemented": False},
        "lexical_file_bm25": {"adapter_id": "opensearch_file_bm25_v1", "backend": "opensearch", "implemented": False},
        "dense_vector": {"adapter_id": "opensearch_dense_knn_v1", "backend": "opensearch", "implemented": False},
        "sparse_vector": {"adapter_id": "opensearch_sparse_knn_v1", "backend": "opensearch", "implemented": False},
        "graph_traversal": {"adapter_id": "projection_graph_v1", "backend": "projection_only", "implemented": False},
    },
    "planetscale_opensearch_v1": {
        "lexical_bm25": {"adapter_id": "opensearch_bm25_v1", "backend": "opensearch", "implemented": False},
        "lexical_file_bm25": {"adapter_id": "opensearch_file_bm25_v1", "backend": "opensearch", "implemented": False},
        "dense_vector": {"adapter_id": "opensearch_dense_knn_v1", "backend": "opensearch", "implemented": False},
        "sparse_vector": {"adapter_id": "opensearch_sparse_knn_v1", "backend": "opensearch", "implemented": False},
        "graph_traversal": {"adapter_id": "projection_graph_v1", "backend": "projection_only", "implemented": False},
    },
}


def list_retrieval_lane_bindings() -> Dict[str, RetrievalLaneBinding]:
    return dict(GOLD_RETRIEVAL_LANE_BINDINGS)


def list_retrieval_lane_contracts() -> Dict[str, RetrievalLaneContract]:
    return dict(RETRIEVAL_LANE_CONTRACTS)


def get_retrieval_lane_binding(primitive_id: str) -> RetrievalLaneBinding:
    binding = GOLD_RETRIEVAL_LANE_BINDINGS.get(str(primitive_id))
    if binding is None:
        available = ", ".join(sorted(GOLD_RETRIEVAL_LANE_BINDINGS.keys()))
        raise ValueError(f"Unsupported retriever primitive_id={primitive_id}; available={available}")
    return binding


def resolve_retrieval_adapter(
    primitive_id: str,
    *,
    profile: Optional[DeploymentProfile] = None,
) -> RetrievalAdapterResolution:
    effective_profile = profile or get_deployment_profile()
    binding = get_retrieval_lane_binding(primitive_id)
    profile_adapters = PROFILE_LANE_ADAPTERS.get(effective_profile.id, {})
    adapter = profile_adapters.get(binding.lane_family)
    if adapter is None:
        raise ValueError(
            f"No adapter mapping registered for profile={effective_profile.id} lane_family={binding.lane_family}"
        )

    capability_map = effective_profile.capability_map()
    support_state = "supported"
    for capability_id in binding.required_capabilities:
        descriptor = capability_map.get(capability_id)
        if descriptor is None:
            support_state = "unsupported"
            break
        if descriptor.support_state != "supported":
            support_state = descriptor.support_state
            break

    return RetrievalAdapterResolution(
        primitive_id=binding.primitive_id,
        lane_family=binding.lane_family,
        adapter_id=str(adapter.get("adapter_id")),
        profile_id=effective_profile.id,
        backend=str(adapter.get("backend")),
        support_state=str(support_state),
        implemented=bool(adapter.get("implemented")),
        required_capabilities=binding.required_capabilities,
    )


def build_profile_lane_diagnostics(
    profile: Optional[DeploymentProfile] = None,
) -> List[Dict[str, Any]]:
    effective_profile = profile or get_deployment_profile()
    capability_map: Dict[str, CapabilityDescriptor] = effective_profile.capability_map()
    profile_adapters = PROFILE_LANE_ADAPTERS.get(effective_profile.id, {})
    diagnostics: List[Dict[str, Any]] = []
    for lane_family, contract in RETRIEVAL_LANE_CONTRACTS.items():
        adapter = profile_adapters.get(lane_family, {})
        support_state = "unsupported"
        for capability_id in contract.capability_ids:
            descriptor = capability_map.get(capability_id)
            if descriptor is None:
                support_state = "unsupported"
                break
            support_state = descriptor.support_state
            if descriptor.support_state != "supported":
                break
        blocked_by_capability = None
        if support_state in {"unsupported", "planned", "degraded"} and len(contract.capability_ids) > 0:
            blocked_by_capability = contract.capability_ids[0]
        placeholder_executor_id = None
        execution_mode = "native" if bool(adapter.get("implemented", False)) else "placeholder"
        hint = None
        if execution_mode == "placeholder":
            placeholder_executor_id = f"placeholder.{lane_family}.{effective_profile.id}"
            if lane_family == "sparse_vector":
                hint = (
                    f"Lane '{lane_family}' is not executable on profile '{effective_profile.id}'. "
                    f"Disable sparse retrieval or use '{'paradedb_postgres_gold_v1'}'."
                )
            elif lane_family == "graph_traversal":
                hint = (
                    f"Lane '{lane_family}' is reserved but not executable on profile '{effective_profile.id}'. "
                    f"Use '{'paradedb_postgres_gold_v1'}' for graph traversal semantics."
                )
            else:
                hint = (
                    f"Lane '{lane_family}' is not executable on profile '{effective_profile.id}'. "
                    f"Use '{'paradedb_postgres_gold_v1'}' or choose a compatible route surface."
                )
        diagnostic = RetrievalLaneDiagnostic(
            lane_family=lane_family,
            backend=str(adapter.get("backend", "none")),
            adapter_id=str(adapter.get("adapter_id", "none")),
            support_state=str(support_state),
            implemented=bool(adapter.get("implemented", False)),
            route_surface_declared=contract.route_surface_declared,
            capability_ids=contract.capability_ids,
            execution_mode=execution_mode,
            blocked_by_capability=blocked_by_capability,
            placeholder_executor_id=placeholder_executor_id,
            recommended_profile_id="paradedb_postgres_gold_v1" if execution_mode == "placeholder" else None,
            hint=hint,
            notes=contract.notes,
        )
        diagnostics.append(diagnostic.to_payload())
    return diagnostics


def resolve_retriever_builder(
    primitive_id: str,
    *,
    profile: Optional[DeploymentProfile] = None,
) -> RetrieverBuilder:
    effective_profile = profile or get_deployment_profile()
    binding = get_retrieval_lane_binding(primitive_id)
    _ = resolve_retrieval_adapter(primitive_id, profile=effective_profile)

    for capability_id in binding.required_capabilities:
        hint = (
            f"Primitive '{binding.primitive_id}' requires capability '{capability_id}'. "
            f"Deploy the ParadeDB/Postgres gold profile or choose a compatible pipeline primitive."
        )
        try:
            require_capability(
                capability_id,
                profile=effective_profile,
                hint=hint,
                message=(
                    f"Retriever primitive '{binding.primitive_id}' is unavailable on deployment profile "
                    f"'{effective_profile.id}' because capability '{capability_id}' is not supported."
                ),
            )
        except QueryLakeUnsupportedFeatureError as exc:
            raise exc

    return binding.builder

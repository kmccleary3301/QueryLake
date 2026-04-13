from __future__ import annotations

from dataclasses import asdict, dataclass, field
import httpx
import os
import time
from sqlalchemy import create_engine, text
from typing import Any, Dict, List, Literal, Optional
from urllib.parse import urlparse

from QueryLake.runtime.support_manifest_v2 import (
    build_representation_scope_registry_payload,
    build_route_support_manifest_entries_v2,
    get_representation_scope,
    ROUTE_CAPABILITY_DEPENDENCIES,
)

SupportState = Literal["supported", "degraded", "unsupported", "planned"]


@dataclass(frozen=True)
class BackendStack:
    authority: str
    lexical: str
    dense: str
    sparse: str
    graph: str


@dataclass(frozen=True)
class CapabilityDescriptor:
    id: str
    support_state: SupportState
    summary: str
    notes: Optional[str] = None


@dataclass(frozen=True)
class DeploymentProfile:
    id: str
    label: str
    implemented: bool
    recommended: bool
    maturity: Literal["gold", "limited_executable", "split_stack_executable", "planned"]
    backend_stack: BackendStack
    capabilities: List[CapabilityDescriptor] = field(default_factory=list)
    notes: Optional[str] = None

    def capability_map(self) -> Dict[str, CapabilityDescriptor]:
        return {cap.id: cap for cap in self.capabilities}


@dataclass(frozen=True)
class ProfileConfigRequirement:
    env_var: str
    kind: Literal["str", "int", "url"]
    summary: str
    required_for_execution: bool = True
    notes: Optional[str] = None


@dataclass(frozen=True)
class ProfileRouteSupport:
    route_id: str
    state: SupportState
    summary: str
    notes: Optional[str] = None


@dataclass(frozen=True)
class ProfileExecutionTarget:
    profile_id: str
    maturity: Literal["gold", "planned", "target"]
    primary_recommendation: str
    mvp_scope: List[ProfileRouteSupport] = field(default_factory=list)
    notes: Optional[str] = None


CAPABILITIES_GOLD: List[CapabilityDescriptor] = [
    CapabilityDescriptor("authority.sql_transactions", "supported", "Authoritative transactional SQL semantics."),
    CapabilityDescriptor("projection.rebuildable_indexes", "supported", "Search indexes are projection artifacts that can be rebuilt."),
    CapabilityDescriptor("retrieval.lexical.bm25", "supported", "Native BM25 lexical retrieval."),
    CapabilityDescriptor("retrieval.lexical.advanced_operators", "supported", "Advanced lexical operators and hard lexical constraints."),
    CapabilityDescriptor("retrieval.lexical.phrase_boost", "supported", "Quoted phrases and exact-phrase boosts contribute directly to lexical ranking."),
    CapabilityDescriptor("retrieval.lexical.proximity", "supported", "Lexical phrase slop / proximity behavior is available."),
    CapabilityDescriptor("retrieval.lexical.hard_constraints", "supported", "Fielded and boolean hard lexical constraints are available."),
    CapabilityDescriptor("retrieval.dense.vector", "supported", "Dense vector retrieval."),
    CapabilityDescriptor("retrieval.sparse.vector", "supported", "Sparse vector retrieval."),
    CapabilityDescriptor("retrieval.graph.traversal", "supported", "Graph and segment traversal primitives."),
    CapabilityDescriptor("retrieval.segment_search", "supported", "Segment-level retrieval on canonical segment records."),
    CapabilityDescriptor("acl.pushdown", "supported", "ACL filtering can be pushed into retrieval execution."),
    CapabilityDescriptor("explain.retrieval_plan", "planned", "Retrieval plan/capability introspection output.", notes="Reserved for a later phase."),
]


CAPABILITIES_POSTGRES_LIGHT: List[CapabilityDescriptor] = [
    CapabilityDescriptor("authority.sql_transactions", "supported", "Authoritative transactional SQL semantics on PostgreSQL."),
    CapabilityDescriptor("projection.rebuildable_indexes", "planned", "Projection/index rebuild workflows remain planned for the light profile."),
    CapabilityDescriptor("retrieval.lexical.bm25", "unsupported", "Native BM25 lexical retrieval is unavailable without a lexical engine."),
    CapabilityDescriptor("retrieval.lexical.advanced_operators", "unsupported", "Advanced lexical operators are unavailable without a lexical engine."),
    CapabilityDescriptor("retrieval.lexical.phrase_boost", "unsupported", "Quoted-phrase lexical boosts are unavailable without a lexical engine."),
    CapabilityDescriptor("retrieval.lexical.proximity", "unsupported", "Phrase slop / proximity semantics are unavailable without a lexical engine."),
    CapabilityDescriptor("retrieval.lexical.hard_constraints", "unsupported", "Fielded and boolean hard lexical constraints are unavailable without a lexical engine."),
    CapabilityDescriptor("retrieval.dense.vector", "supported", "Dense vector retrieval on the co-located pgvector lane."),
    CapabilityDescriptor("retrieval.sparse.vector", "unsupported", "Sparse retrieval is not available in the light profile."),
    CapabilityDescriptor("retrieval.graph.traversal", "planned", "Graph and segment traversal primitives remain outside the first light-profile slice."),
    CapabilityDescriptor("retrieval.segment_search", "planned", "Segment-level retrieval on canonical segment records remains outside the first light-profile slice."),
    CapabilityDescriptor("acl.pushdown", "supported", "Collection/ACL filtering can still be pushed into SQL retrieval execution."),
    CapabilityDescriptor("explain.retrieval_plan", "planned", "Retrieval plan/capability introspection output."),
]


CAPABILITIES_SPLIT_STACK: List[CapabilityDescriptor] = [
    CapabilityDescriptor("authority.sql_transactions", "supported", "Authoritative transactional SQL semantics on the authority SQL plane."),
    CapabilityDescriptor("projection.rebuildable_indexes", "planned", "Search indexes are projection artifacts that can be rebuilt."),
    CapabilityDescriptor("retrieval.lexical.bm25", "supported", "Lexical retrieval delegated to a projection/index plane."),
    CapabilityDescriptor("retrieval.lexical.advanced_operators", "degraded", "Advanced lexical operators are profile-dependent and may be approximate on split-stack profiles."),
    CapabilityDescriptor("retrieval.lexical.phrase_boost", "degraded", "Quoted phrases may be approximated rather than scored exactly like the gold stack."),
    CapabilityDescriptor("retrieval.lexical.proximity", "degraded", "Phrase slop / proximity behavior may be approximate on split-stack profiles."),
    CapabilityDescriptor("retrieval.lexical.hard_constraints", "unsupported", "Fielded/boolean hard lexical constraints are not yet executable on the first split-stack slice."),
    CapabilityDescriptor("retrieval.dense.vector", "supported", "Dense vector retrieval delegated to a search/index plane."),
    CapabilityDescriptor("retrieval.sparse.vector", "unsupported", "Sparse retrieval is intentionally disabled on the first split-stack slice."),
    CapabilityDescriptor("retrieval.graph.traversal", "unsupported", "Graph and segment traversal primitives are out of scope for the first split-stack slice."),
    CapabilityDescriptor("retrieval.segment_search", "unsupported", "Segment-level retrieval is not yet executable on the first split-stack slice."),
    CapabilityDescriptor("acl.pushdown", "supported", "Collection/ACL filtering can be applied as backend filters on the split-stack retrieval plane."),
    CapabilityDescriptor("explain.retrieval_plan", "planned", "Retrieval plan/capability introspection output."),
]


CAPABILITIES_SQLITE_LOCAL_LIGHT: List[CapabilityDescriptor] = [
    CapabilityDescriptor("authority.sql_transactions", "supported", "Single-node transactional semantics on SQLite."),
    CapabilityDescriptor("projection.rebuildable_indexes", "supported", "Local lexical/vector indexes are rebuildable projection artifacts."),
    CapabilityDescriptor("retrieval.lexical.bm25", "degraded", "SQLite FTS5 lexical retrieval approximates the gold BM25 semantics."),
    CapabilityDescriptor("retrieval.lexical.advanced_operators", "degraded", "Advanced lexical operators are intentionally narrowed on the first local profile."),
    CapabilityDescriptor("retrieval.lexical.phrase_boost", "degraded", "Quoted-phrase behavior is available but not expected to match the gold profile exactly."),
    CapabilityDescriptor("retrieval.lexical.proximity", "degraded", "Phrase proximity semantics are available only in a reduced local form."),
    CapabilityDescriptor("retrieval.lexical.hard_constraints", "unsupported", "Hard lexical constraints remain out of scope for the first local profile."),
    CapabilityDescriptor("retrieval.dense.vector", "supported", "Dense vector retrieval through a local sidecar index."),
    CapabilityDescriptor("retrieval.sparse.vector", "unsupported", "Sparse retrieval is intentionally deferred for the first local profile."),
    CapabilityDescriptor("retrieval.graph.traversal", "unsupported", "Graph traversal is intentionally deferred for the first local profile."),
    CapabilityDescriptor("retrieval.segment_search", "planned", "Canonical segment-level retrieval remains a later local-profile phase."),
    CapabilityDescriptor("acl.pushdown", "supported", "Collection and metadata filters remain available locally."),
    CapabilityDescriptor("explain.retrieval_plan", "planned", "Retrieval plan/capability introspection output."),
]


DEPLOYMENT_PROFILES: Dict[str, DeploymentProfile] = {
    "paradedb_postgres_gold_v1": DeploymentProfile(
        id="paradedb_postgres_gold_v1",
        label="ParadeDB + PostgreSQL (gold)",
        implemented=True,
        recommended=True,
        maturity="gold",
        backend_stack=BackendStack(
            authority="postgresql",
            lexical="paradedb",
            dense="pgvector_halfvec",
            sparse="pgvector_sparsevec",
            graph="postgresql_segment_relations",
        ),
        capabilities=CAPABILITIES_GOLD,
        notes="Canonical QueryLake profile. Preserves current retrieval semantics.",
    ),
    "postgres_pgvector_light_v1": DeploymentProfile(
        id="postgres_pgvector_light_v1",
        label="PostgreSQL + pgvector (light)",
        implemented=True,
        recommended=False,
        maturity="limited_executable",
        backend_stack=BackendStack(
            authority="postgresql",
            lexical="none",
            dense="pgvector_halfvec",
            sparse="none",
            graph="postgresql_segment_relations",
        ),
        capabilities=CAPABILITIES_POSTGRES_LIGHT,
        notes="Limited executable profile. Dense-only document-chunk retrieval is available; lexical and sparse routes remain unsupported.",
    ),
    "aws_aurora_pg_opensearch_v1": DeploymentProfile(
        id="aws_aurora_pg_opensearch_v1",
        label="Aurora PostgreSQL + OpenSearch",
        implemented=True,
        recommended=False,
        maturity="split_stack_executable",
        backend_stack=BackendStack(
            authority="aurora_postgresql",
            lexical="opensearch",
            dense="opensearch",
            sparse="opensearch",
            graph="aurora_postgresql_segment_relations",
        ),
        capabilities=CAPABILITIES_SPLIT_STACK,
        notes="First planned split-stack profile.",
    ),
    "sqlite_fts5_dense_sidecar_local_v1": DeploymentProfile(
        id="sqlite_fts5_dense_sidecar_local_v1",
        label="SQLite FTS5 + dense sidecar (local)",
        implemented=True,
        recommended=False,
        maturity="embedded_supported",
        backend_stack=BackendStack(
            authority="sqlite",
            lexical="sqlite_fts5",
            dense="local_dense_sidecar",
            sparse="none",
            graph="none",
        ),
        capabilities=CAPABILITIES_SQLITE_LOCAL_LIGHT,
        notes="Supported embedded/local profile for low-friction developer and research workflows within its declared lexical+dense route slice.",
    ),
    "mongo_opensearch_v1": DeploymentProfile(
        id="mongo_opensearch_v1",
        label="MongoDB + OpenSearch",
        implemented=False,
        recommended=False,
        maturity="planned",
        backend_stack=BackendStack(
            authority="mongodb",
            lexical="opensearch",
            dense="opensearch",
            sparse="opensearch",
            graph="projection_only",
        ),
        capabilities=CAPABILITIES_SPLIT_STACK,
        notes="Planned document-authority + search-index profile.",
    ),
    "planetscale_opensearch_v1": DeploymentProfile(
        id="planetscale_opensearch_v1",
        label="PlanetScale + OpenSearch",
        implemented=False,
        recommended=False,
        maturity="planned",
        backend_stack=BackendStack(
            authority="planetscale",
            lexical="opensearch",
            dense="opensearch",
            sparse="opensearch",
            graph="projection_only",
        ),
        capabilities=CAPABILITIES_SPLIT_STACK,
        notes="Planned MySQL-compatible authority with external search plane.",
    ),
}

DEFAULT_DB_PROFILE = "paradedb_postgres_gold_v1"
DB_PROFILE_ENV = "QUERYLAKE_DB_PROFILE"
PROFILE_DIAGNOSTICS_PROBE_ENV = "QUERYLAKE_PROFILE_DIAGNOSTICS_PROBE"
PROFILE_DIAGNOSTICS_PROBE_TIMEOUT_ENV = "QUERYLAKE_PROFILE_DIAGNOSTICS_PROBE_TIMEOUT_SECONDS"
PROFILE_CONFIG_REQUIREMENTS: Dict[str, List[ProfileConfigRequirement]] = {
    "paradedb_postgres_gold_v1": [],
    "postgres_pgvector_light_v1": [],
    "aws_aurora_pg_opensearch_v1": [
        ProfileConfigRequirement(
            "QUERYLAKE_AUTHORITY_DATABASE_URL",
            "url",
            "Optional Aurora/PostgreSQL authority DSN override used for split-stack diagnostics and authority-engine targeting.",
            required_for_execution=False,
            notes="If unset, QueryLake falls back to QUERYLAKE_DATABASE_URL for the authority plane.",
        ),
        ProfileConfigRequirement("QUERYLAKE_SEARCH_BACKEND_URL", "url", "OpenSearch base URL."),
        ProfileConfigRequirement("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "str", "Index namespace/prefix used for projections."),
        ProfileConfigRequirement("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "int", "Dense vector dimensions for OpenSearch k-NN mappings."),
    ],
    "sqlite_fts5_dense_sidecar_local_v1": [
        ProfileConfigRequirement(
            "QUERYLAKE_LOCAL_PROFILE_ROOT",
            "str",
            "Filesystem root for local SQLite and sidecar index artifacts.",
            required_for_execution=False,
            notes="Reserved for the first local profile implementation phase.",
        ),
    ],
    "mongo_opensearch_v1": [
        ProfileConfigRequirement("QUERYLAKE_MONGO_URI", "url", "MongoDB authority-plane URI."),
        ProfileConfigRequirement("QUERYLAKE_SEARCH_BACKEND_URL", "url", "OpenSearch base URL."),
        ProfileConfigRequirement("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "str", "Index namespace/prefix used for projections."),
        ProfileConfigRequirement("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "int", "Dense vector dimensions for OpenSearch k-NN mappings."),
        ProfileConfigRequirement("QUERYLAKE_SPARSE_INDEX_DIMENSIONS", "int", "Sparse vector dimensions expected by the search/index plane."),
    ],
    "planetscale_opensearch_v1": [
        ProfileConfigRequirement("QUERYLAKE_PLANETSCALE_DSN", "url", "PlanetScale authority-plane DSN."),
        ProfileConfigRequirement("QUERYLAKE_SEARCH_BACKEND_URL", "url", "OpenSearch base URL."),
        ProfileConfigRequirement("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "str", "Index namespace/prefix used for projections."),
        ProfileConfigRequirement("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "int", "Dense vector dimensions for OpenSearch k-NN mappings."),
        ProfileConfigRequirement("QUERYLAKE_SPARSE_INDEX_DIMENSIONS", "int", "Sparse vector dimensions expected by the search/index plane."),
    ],
}

PROFILE_EXECUTION_TARGETS: Dict[str, ProfileExecutionTarget] = {
    "paradedb_postgres_gold_v1": ProfileExecutionTarget(
        profile_id="paradedb_postgres_gold_v1",
        maturity="gold",
        primary_recommendation="Use this profile for full QueryLake retrieval semantics and current production behavior.",
        mvp_scope=[
            ProfileRouteSupport("search_hybrid.document_chunk", "supported", "Three-lane hybrid retrieval on the gold stack."),
            ProfileRouteSupport("search_bm25.document_chunk", "supported", "BM25 lexical retrieval on document chunks."),
            ProfileRouteSupport("search_file_chunks", "supported", "BM25 lexical retrieval on ingested file chunks."),
            ProfileRouteSupport("retrieval.graph.traversal", "supported", "Graph-aware traversal and segment relations."),
        ],
        notes="Canonical profile. All compatibility work preserves this stack first.",
    ),
    "postgres_pgvector_light_v1": ProfileExecutionTarget(
        profile_id="postgres_pgvector_light_v1",
        maturity="target",
        primary_recommendation="Use this only when you need a minimal PostgreSQL + pgvector deployment and can accept dense-only document-chunk retrieval.",
        mvp_scope=[
            ProfileRouteSupport(
                "search_hybrid.document_chunk",
                "supported",
                "Dense-only document-chunk retrieval through the co-located pgvector lane.",
                notes="Requires use_bm25=false and use_sparse=false in the request shape.",
            ),
            ProfileRouteSupport(
                "search_bm25.document_chunk",
                "unsupported",
                "Lexical BM25 retrieval is intentionally unavailable without a lexical engine.",
            ),
            ProfileRouteSupport(
                "search_file_chunks",
                "unsupported",
                "File-chunk lexical retrieval is intentionally unavailable without a lexical engine.",
            ),
            ProfileRouteSupport(
                "retrieval.sparse.vector",
                "unsupported",
                "Sparse retrieval remains out of scope for the first light-profile slice.",
            ),
        ],
        notes="This profile is intentionally narrow: one dense-only executable route and explicit lexical/sparse exclusions.",
    ),
    "aws_aurora_pg_opensearch_v1": ProfileExecutionTarget(
        profile_id="aws_aurora_pg_opensearch_v1",
        maturity="target",
        primary_recommendation="First split-stack target. Authority remains SQL, lexical+dense retrieval move to OpenSearch projections.",
        mvp_scope=[
            ProfileRouteSupport("search_hybrid.document_chunk", "supported", "First executable slice: lexical+dense hybrid on document-chunk projection indexes."),
            ProfileRouteSupport("search_bm25.document_chunk", "supported", "First executable slice: lexical BM25-like retrieval on document-chunk projection indexes."),
            ProfileRouteSupport("search_file_chunks", "supported", "File-chunk lexical retrieval via OpenSearch projection indexes."),
            ProfileRouteSupport("retrieval.sparse.vector", "unsupported", "Sparse lane is intentionally disabled for the first executable slice."),
            ProfileRouteSupport("retrieval.graph.traversal", "unsupported", "Graph traversal is explicitly out of scope for the first split-stack slice."),
        ],
        notes="This is the first profile intended to become executable after the gold stack remains stable behind the adapter boundary.",
    ),
    "sqlite_fts5_dense_sidecar_local_v1": ProfileExecutionTarget(
        profile_id="sqlite_fts5_dense_sidecar_local_v1",
        maturity="embedded_supported",
        primary_recommendation="Use this when you need a supported embedded QueryLake profile with low-friction local lexical+dense retrieval and explicit lexical degradation versus gold.",
        mvp_scope=[
            ProfileRouteSupport(
                "search_hybrid.document_chunk",
                "supported",
                "Local lexical+dense hybrid retrieval on SQLite FTS5 plus a dense sidecar index.",
                notes="The first local slice is intended to preserve hybrid composition while staying honest about lexical differences from the gold profile.",
            ),
            ProfileRouteSupport(
                "search_bm25.document_chunk",
                "degraded",
                "Local lexical retrieval on SQLite FTS5 with intentionally degraded lexical semantics versus the gold profile.",
            ),
            ProfileRouteSupport(
                "search_file_chunks",
                "degraded",
                "Local file-chunk lexical retrieval on SQLite FTS5 with the same lexical limitations as the document-chunk lexical route.",
            ),
            ProfileRouteSupport(
                "retrieval.sparse.vector",
                "unsupported",
                "Sparse retrieval is intentionally deferred from the first local profile.",
            ),
            ProfileRouteSupport(
                "retrieval.graph.traversal",
                "unsupported",
                "Graph traversal is intentionally deferred from the first local profile.",
            ),
        ],
        notes="This profile is intentionally scoped as a supported embedded/local target for the declared lexical+dense route slice only.",
    ),
}


class QueryLakeUnsupportedFeatureError(RuntimeError):
    def __init__(
        self,
        *,
        capability: str,
        profile: str,
        message: Optional[str] = None,
        hint: Optional[str] = None,
        support_state: SupportState = "unsupported",
        backend_stack: Optional[BackendStack] = None,
    ) -> None:
        self.capability = capability
        self.profile = profile
        self.support_state = support_state
        self.backend_stack = backend_stack
        self.hint = hint or "Use a compatible deployment profile or disable the requested feature."
        self.message = message or f"Capability '{capability}' is not supported by deployment profile '{profile}'."
        super().__init__(self.message)

    def to_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "type": "unsupported_feature",
            "code": "ql.db_capability_unsupported",
            "message": self.message,
            "capability": self.capability,
            "profile": self.profile,
            "support_state": self.support_state,
            "hint": self.hint,
            "docs_ref": "docs/database/DB_COMPAT_PROFILES.md#unsupported-feature-contract",
            "retryable": False,
        }
        if self.backend_stack is not None:
            payload["backend_stack"] = asdict(self.backend_stack)
        return payload


class QueryLakeProfileConfigurationError(RuntimeError):
    def __init__(self, profile: str, message: str) -> None:
        self.profile = profile
        self.message = message
        super().__init__(message)

    def to_payload(self) -> Dict[str, Any]:
        return {
            "type": "profile_configuration_error",
            "code": "ql.db_profile_invalid",
            "message": self.message,
            "profile": self.profile,
            "docs_ref": "docs/database/PROFILE_DIAGNOSTICS.md#startup-validation-rules",
            "retryable": False,
        }


def get_current_db_profile_id() -> str:
    return os.getenv(DB_PROFILE_ENV, DEFAULT_DB_PROFILE).strip() or DEFAULT_DB_PROFILE


def get_deployment_profile(profile_id: Optional[str] = None) -> DeploymentProfile:
    effective_id = profile_id or get_current_db_profile_id()
    profile = DEPLOYMENT_PROFILES.get(effective_id)
    if profile is None:
        known = ", ".join(sorted(DEPLOYMENT_PROFILES.keys()))
        raise QueryLakeProfileConfigurationError(
            effective_id,
            f"Unknown QueryLake DB profile '{effective_id}'. Known profiles: {known}.",
        )
    return profile


def validate_current_db_profile() -> DeploymentProfile:
    profile = get_deployment_profile()
    if not profile.implemented:
        raise QueryLakeProfileConfigurationError(
            profile.id,
            f"QueryLake DB profile '{profile.id}' is declared but not implemented on this deployment. Use '{DEFAULT_DB_PROFILE}' for the current executable stack.",
        )
    return profile


def is_capability_supported(capability_id: str, profile: Optional[DeploymentProfile] = None) -> bool:
    effective_profile = profile or get_deployment_profile()
    descriptor = effective_profile.capability_map().get(capability_id)
    return descriptor is not None and descriptor.support_state == "supported"


def get_capability_descriptor(capability_id: str, profile: Optional[DeploymentProfile] = None) -> Optional[CapabilityDescriptor]:
    effective_profile = profile or get_deployment_profile()
    return effective_profile.capability_map().get(capability_id)


def get_capability_support_state(capability_id: str, profile: Optional[DeploymentProfile] = None) -> SupportState:
    descriptor = get_capability_descriptor(capability_id, profile=profile)
    return descriptor.support_state if descriptor is not None else "unsupported"


def require_capability(
    capability_id: str,
    *,
    profile: Optional[DeploymentProfile] = None,
    hint: Optional[str] = None,
    message: Optional[str] = None,
) -> None:
    effective_profile = profile or get_deployment_profile()
    descriptor = effective_profile.capability_map().get(capability_id)
    if descriptor is None or descriptor.support_state != "supported":
        support_state: SupportState = descriptor.support_state if descriptor is not None else "unsupported"
        fallback_message = message or (
            f"Capability '{capability_id}' is not supported by deployment profile '{effective_profile.id}'."
        )
        raise QueryLakeUnsupportedFeatureError(
            capability=capability_id,
            profile=effective_profile.id,
            message=fallback_message,
            hint=hint,
            support_state=support_state,
            backend_stack=effective_profile.backend_stack,
        )


def build_capabilities_payload(profile: Optional[DeploymentProfile] = None) -> Dict[str, Any]:
    effective_profile = profile or get_deployment_profile()
    route_support = build_profile_route_support_matrix(effective_profile)
    return {
        "profile": {
            "id": effective_profile.id,
            "label": effective_profile.label,
            "implemented": effective_profile.implemented,
            "recommended": effective_profile.recommended,
            "maturity": effective_profile.maturity,
            "notes": effective_profile.notes,
            "backend_stack": asdict(effective_profile.backend_stack),
        },
        "representation_scopes": build_representation_scope_registry_payload(),
        "capabilities": [
            {
                "id": cap.id,
                "support_state": cap.support_state,
                "summary": cap.summary,
                "notes": cap.notes,
            }
            for cap in effective_profile.capabilities
        ],
        "known_profiles": [
            {
                "id": profile.id,
                "label": profile.label,
                "implemented": profile.implemented,
                "recommended": profile.recommended,
                "maturity": profile.maturity,
            }
            for profile in DEPLOYMENT_PROFILES.values()
        ],
        "route_support_v2": build_route_support_manifest_entries_v2(route_support.values()),
    }


def build_supported_profiles_manifest_payload() -> Dict[str, Any]:
    profiles: List[Dict[str, Any]] = []
    for profile in DEPLOYMENT_PROFILES.values():
        route_support = build_profile_route_support_matrix(profile)
        profiles.append(
            {
                "id": profile.id,
                "label": profile.label,
                "implemented": profile.implemented,
                "recommended": profile.recommended,
                "maturity": profile.maturity,
                "backend_stack": asdict(profile.backend_stack),
                "capabilities": {
                    capability.id: capability.support_state
                    for capability in profile.capabilities
                },
                "representation_scopes": build_representation_scope_registry_payload(),
                "routes": {
                    route_id: {
                        "declared_state": row["declared_state"],
                        "declared_executable": row["declared_executable"],
                        "declared_optional": row["declared_optional"],
                        "representation_scope_id": row["representation_scope_id"],
                        "capability_dependencies": row["capability_dependencies"],
                    }
                    for route_id, row in route_support.items()
                },
                "routes_v2": build_route_support_manifest_entries_v2(route_support.values()),
            }
        )
    return {"profiles": profiles}


def get_profile_execution_target(profile: Optional[DeploymentProfile] = None) -> Optional[ProfileExecutionTarget]:
    effective_profile = profile or get_deployment_profile()
    return PROFILE_EXECUTION_TARGETS.get(effective_profile.id)


def build_profile_execution_target_payload(profile: Optional[DeploymentProfile] = None) -> Optional[Dict[str, Any]]:
    target = get_profile_execution_target(profile)
    if target is None:
        return None
    return {
        "profile_id": target.profile_id,
        "maturity": target.maturity,
        "primary_recommendation": target.primary_recommendation,
        "notes": target.notes,
        "mvp_scope": [
            {
                "route_id": route.route_id,
                "state": route.state,
                "summary": route.summary,
                "notes": route.notes,
            }
            for route in target.mvp_scope
        ],
    }


def build_profile_route_support_matrix(profile: Optional[DeploymentProfile] = None) -> Dict[str, Dict[str, Any]]:
    effective_profile = profile or get_deployment_profile()
    target = get_profile_execution_target(effective_profile)
    if target is None:
        return {}
    return {
        route.route_id: {
            "route_id": route.route_id,
            "declared_state": route.state,
            "summary": route.summary,
            "notes": route.notes,
            "declared_executable": route.state in {"supported", "degraded"},
            "declared_optional": route.state in {"planned", "unsupported"},
            "representation_scope_id": get_representation_scope(route.route_id).scope_id,
            "capability_dependencies": list(ROUTE_CAPABILITY_DEPENDENCIES.get(route.route_id, [])),
        }
        for route in target.mvp_scope
    }


def get_declared_executable_route_ids(profile: Optional[DeploymentProfile] = None) -> List[str]:
    matrix = build_profile_route_support_matrix(profile)
    return [
        route_id
        for route_id, payload in matrix.items()
        if bool(payload.get("declared_executable"))
    ]


def get_declared_optional_route_ids(profile: Optional[DeploymentProfile] = None) -> List[str]:
    matrix = build_profile_route_support_matrix(profile)
    return [
        route_id
        for route_id, payload in matrix.items()
        if bool(payload.get("declared_optional"))
    ]


def get_profile_config_requirements(profile: Optional[DeploymentProfile] = None) -> List[ProfileConfigRequirement]:
    effective_profile = profile or get_deployment_profile()
    return list(PROFILE_CONFIG_REQUIREMENTS.get(effective_profile.id, []))


def _validate_requirement_value(requirement: ProfileConfigRequirement, raw_value: Optional[str]) -> tuple[bool, Optional[str]]:
    if raw_value is None or str(raw_value).strip() == "":
        return False, "missing"
    value = str(raw_value).strip()
    if requirement.kind == "str":
        return True, None
    if requirement.kind == "int":
        try:
            parsed = int(value)
        except ValueError:
            return False, "must be an integer"
        if parsed <= 0:
            return False, "must be greater than zero"
        return True, None
    if requirement.kind == "url":
        if "://" not in value:
            return False, "must be a URL-like value containing '://'"
        return True, None
    return False, f"unsupported requirement kind '{requirement.kind}'"


def build_profile_configuration_payload(profile: Optional[DeploymentProfile] = None) -> Dict[str, Any]:
    effective_profile = profile or get_deployment_profile()
    requirements = get_profile_config_requirements(effective_profile)
    evaluated: List[Dict[str, Any]] = []
    ready = True
    for requirement in requirements:
        raw_value = os.getenv(requirement.env_var)
        valid, error = _validate_requirement_value(requirement, raw_value)
        if requirement.required_for_execution and not valid:
            ready = False
        evaluated.append(
            {
                "env_var": requirement.env_var,
                "kind": requirement.kind,
                "summary": requirement.summary,
                "required_for_execution": requirement.required_for_execution,
                "present": raw_value is not None and str(raw_value).strip() != "",
                "valid": valid,
                "error": error,
                "notes": requirement.notes,
            }
        )
    return {
        "profile_id": effective_profile.id,
        "ready": ready,
        "requirements": evaluated,
    }


def validate_profile_configuration_requirements(profile: Optional[DeploymentProfile] = None) -> Dict[str, Any]:
    effective_profile = profile or get_deployment_profile()
    payload = build_profile_configuration_payload(effective_profile)
    if payload["ready"]:
        return payload
    failing = [item["env_var"] for item in payload["requirements"] if item["required_for_execution"] and not item["valid"]]
    raise QueryLakeProfileConfigurationError(
        effective_profile.id,
        f"Deployment profile '{effective_profile.id}' is missing or has malformed required configuration: {', '.join(failing)}.",
    )


def build_profile_diagnostics_payload(
    profile: Optional[DeploymentProfile] = None,
    *,
    metadata_store_path: Optional[str] = None,
) -> Dict[str, Any]:
    effective_profile = profile or get_deployment_profile()
    config = build_profile_configuration_payload(effective_profile)
    execution_target = build_profile_execution_target_payload(effective_profile)
    capabilities_payload = build_capabilities_payload(effective_profile)

    from QueryLake.runtime.retrieval_route_executors import (
        resolve_search_bm25_route_executor,
        resolve_search_file_chunks_route_executor,
        resolve_search_hybrid_route_executor,
    )
    from QueryLake.runtime.lexical_capability_planner import build_route_lexical_semantics_summary
    from QueryLake.runtime.local_profile_v2 import (
        build_local_profile_diagnostics_payload,
        is_local_profile_v2,
    )
    from QueryLake.runtime.projection_refresh import build_projection_diagnostics_payload
    from QueryLake.runtime.retrieval_lanes import build_profile_lane_diagnostics

    hybrid_supports_bm25 = get_capability_support_state(
        "retrieval.lexical.bm25",
        profile=effective_profile,
    ) == "supported"
    hybrid_supports_dense = get_capability_support_state(
        "retrieval.dense.vector",
        profile=effective_profile,
    ) == "supported"
    hybrid_supports_sparse = get_capability_support_state(
        "retrieval.sparse.vector",
        profile=effective_profile,
    ) == "supported"
    route_resolutions = [
        resolve_search_hybrid_route_executor(
            use_bm25=hybrid_supports_bm25,
            use_similarity=hybrid_supports_dense,
            use_sparse=hybrid_supports_sparse,
            profile=effective_profile,
        ),
        resolve_search_bm25_route_executor(table="document_chunk", profile=effective_profile),
        resolve_search_file_chunks_route_executor(profile=effective_profile),
    ]
    projection_diagnostics = build_projection_diagnostics_payload(
        profile=effective_profile,
        metadata_store_path=metadata_store_path,
    )
    lane_diagnostics = build_profile_lane_diagnostics(effective_profile)
    projection_item_map = {
        item["projection_id"]: item
        for item in projection_diagnostics.get("projection_items", [])
        if isinstance(item, dict)
    }

    def _is_compatibility_authority_model(authority_model: Any) -> bool:
        return str(authority_model or "").endswith("_compatibility")

    route_payloads = []
    split_stack_projection_required = effective_profile.id != DEFAULT_DB_PROFILE
    for resolved in route_resolutions:
        payload = resolved.to_payload()
        descriptor_ids = list(payload.get("projection_descriptors") or [])
        projection_targets = [
            dict(entry)
            for entry in list(payload.get("projection_targets") or [])
            if isinstance(entry, dict)
        ]
        projection_target_map = {
            str(entry.get("projection_id")): dict(entry)
            for entry in projection_targets
            if entry.get("projection_id")
        }
        compatibility_projection_target_ids = sorted(
            str(entry.get("projection_id") or "")
            for entry in projection_targets
            if entry.get("projection_id") and _is_compatibility_authority_model(entry.get("authority_model"))
        )
        canonical_projection_target_ids = sorted(
            str(entry.get("projection_id") or "")
            for entry in projection_targets
            if entry.get("projection_id") and not _is_compatibility_authority_model(entry.get("authority_model"))
        )
        readiness_map: Dict[str, Any] = {}
        missing_descriptors: List[str] = []
        for projection_id in descriptor_ids:
            item = projection_item_map.get(projection_id)
            if item is None:
                readiness_map[projection_id] = {
                    "projection_id": projection_id,
                    "build_status": "absent",
                    "support_state": "unsupported",
                    "executable": False,
                    "action_mode": "unknown",
                    "materialization_target": projection_target_map.get(projection_id, {}),
                }
                missing_descriptors.append(projection_id)
                continue
            readiness_map[projection_id] = {
                "projection_id": projection_id,
                "build_status": item.get("build_status", "absent"),
                "support_state": item.get("support_state", "unsupported"),
                "executable": bool(item.get("executable", False)),
                "action_mode": item.get("action_mode", "unknown"),
                "build_state": dict(item.get("build_state") or {}),
                "invalidated_by": list(item.get("invalidated_by") or []),
                "backend_name": item.get("backend_name"),
                "materialization_target": dict(
                    item.get("materialization_target") or projection_target_map.get(projection_id) or {}
                ),
            }
            if item.get("build_status") != "ready":
                missing_descriptors.append(projection_id)

        projection_dependency_mode = (
            "required_external_projection"
            if split_stack_projection_required and len(descriptor_ids) > 0
            else "optional_compatibility"
        )
        projection_ready = (
            len(missing_descriptors) == 0
            if projection_dependency_mode == "required_external_projection"
            else True
        )
        if projection_dependency_mode != "required_external_projection":
            missing_descriptors = []
        runtime_blockers: List[Dict[str, Any]] = []
        if not bool(payload.get("implemented", False)):
            runtime_blockers.append(
                {
                    "kind": "executor_unimplemented",
                    "summary": "No executable route executor is implemented for this profile.",
                }
            )
        if payload.get("support_state") not in {"supported", "degraded"}:
            runtime_blockers.append(
                {
                    "kind": "unsupported_route_support_state",
                    "summary": f"Route support state is '{payload.get('support_state')}'.",
                }
            )
        writer_gap_descriptors: List[str] = []
        build_gap_descriptors: List[str] = []
        stale_gap_descriptors: List[str] = []
        failed_gap_descriptors: List[str] = []
        building_gap_descriptors: List[str] = []
        for projection_id in missing_descriptors:
            readiness = readiness_map.get(projection_id) or {}
            action_mode = readiness.get("action_mode")
            build_status = str(readiness.get("build_status") or "absent")
            if action_mode == "external_writer_unavailable":
                writer_gap_descriptors.append(projection_id)
            elif build_status == "stale":
                stale_gap_descriptors.append(projection_id)
            elif build_status == "failed":
                failed_gap_descriptors.append(projection_id)
            elif build_status == "building":
                building_gap_descriptors.append(projection_id)
            else:
                build_gap_descriptors.append(projection_id)

        if projection_dependency_mode == "required_external_projection" and len(writer_gap_descriptors) > 0:
            runtime_blockers.append(
                {
                    "kind": "projection_writer_unavailable",
                    "summary": "Required external projections depend on writer implementations that are not available on this deployment.",
                    "projection_ids": list(writer_gap_descriptors),
                }
            )
        if projection_dependency_mode == "required_external_projection" and len(building_gap_descriptors) > 0:
            runtime_blockers.append(
                {
                    "kind": "projection_building",
                    "summary": "Required external projections are currently building on this deployment.",
                    "projection_ids": list(building_gap_descriptors),
                }
            )
        if projection_dependency_mode == "required_external_projection" and len(failed_gap_descriptors) > 0:
            runtime_blockers.append(
                {
                    "kind": "projection_failed",
                    "summary": "Required external projections have failed builds on this deployment.",
                    "projection_ids": list(failed_gap_descriptors),
                }
            )
        if projection_dependency_mode == "required_external_projection" and len(stale_gap_descriptors) > 0:
            runtime_blockers.append(
                {
                    "kind": "projection_stale",
                    "summary": "Required external projections are stale and must be rebuilt on this deployment.",
                    "projection_ids": list(stale_gap_descriptors),
                }
            )
        if projection_dependency_mode == "required_external_projection" and len(build_gap_descriptors) > 0:
            runtime_blockers.append(
                {
                    "kind": "projection_not_ready",
                    "summary": "Required external projections are not ready on this deployment.",
                    "projection_ids": list(build_gap_descriptors),
                }
            )
        payload["projection_dependency_mode"] = projection_dependency_mode
        payload["projection_ready"] = projection_ready
        payload["projection_missing_descriptors"] = missing_descriptors
        payload["projection_writer_gap_descriptors"] = list(writer_gap_descriptors)
        payload["projection_building_gap_descriptors"] = list(building_gap_descriptors)
        payload["projection_failed_gap_descriptors"] = list(failed_gap_descriptors)
        payload["projection_stale_gap_descriptors"] = list(stale_gap_descriptors)
        payload["projection_build_gap_descriptors"] = list(build_gap_descriptors)
        payload["projection_readiness"] = readiness_map
        payload["compatibility_projection_target_ids"] = list(compatibility_projection_target_ids)
        payload["canonical_projection_target_ids"] = list(canonical_projection_target_ids)
        payload["compatibility_projection_reliance"] = len(compatibility_projection_target_ids) > 0
        if str(payload.get("route_id") or "").startswith(("search_bm25", "search_file_chunks", "search_hybrid")):
            payload["lexical_semantics"] = build_route_lexical_semantics_summary(
                route_id=str(payload.get("route_id") or ""),
                profile=effective_profile,
            )
        payload["runtime_ready"] = (
            bool(payload.get("implemented", False))
            and payload.get("support_state") in {"supported", "degraded"}
            and projection_ready
        )
        payload["runtime_blockers"] = runtime_blockers
        route_payloads.append(payload)

    inspected_route_ids = [payload["route_id"] for payload in route_payloads]
    declared_route_support_matrix = build_profile_route_support_matrix(effective_profile)
    required_route_ids = [
        route_id
        for route_id in get_declared_executable_route_ids(effective_profile)
        if route_id in inspected_route_ids
    ]
    optional_route_ids = [
        route_id
        for route_id in get_declared_optional_route_ids(effective_profile)
        if route_id in inspected_route_ids
    ]
    declared_route_ids = list(required_route_ids) + [
        route_id for route_id in optional_route_ids if route_id not in required_route_ids
    ]
    route_payload_map = {payload["route_id"]: payload for payload in route_payloads}
    declared_route_support = {
        route_id: str(route_payload_map.get(route_id, {}).get("support_state") or "")
        for route_id in declared_route_ids
        if route_id in route_payload_map
    }
    non_executable_required_routes = [
        route_id
        for route_id in required_route_ids
        if not route_payload_map.get(route_id, {}).get("implemented", False)
    ]
    non_executable_optional_routes = [
        route_id
        for route_id in optional_route_ids
        if route_id in route_payload_map and not route_payload_map[route_id]["implemented"]
    ]
    non_runtime_ready_required_routes = [
        route_id
        for route_id in required_route_ids
        if not route_payload_map.get(route_id, {}).get("runtime_ready", False)
    ]
    non_runtime_ready_optional_routes = [
        route_id
        for route_id in optional_route_ids
        if route_id in route_payload_map and not route_payload_map[route_id].get("runtime_ready", False)
    ]
    executable_route_ids = [
        payload["route_id"]
        for payload in route_payloads
        if payload["implemented"] and payload["support_state"] in {"supported", "degraded"}
    ]
    runtime_ready_route_ids = [
        payload["route_id"]
        for payload in route_payloads
        if payload.get("runtime_ready", False)
    ]
    declared_executable_runtime_ready_ids = [
        route_id
        for route_id in required_route_ids
        if route_id in runtime_ready_route_ids
    ]
    declared_executable_runtime_blocked_ids = [
        route_id
        for route_id in required_route_ids
        if route_id not in declared_executable_runtime_ready_ids
    ]
    projection_blocked_route_ids = [
        payload["route_id"]
        for payload in route_payloads
        if payload["route_id"] in executable_route_ids
        and not payload.get("runtime_ready", False)
        and any(
            isinstance(entry, dict) and str(entry.get("kind")) in {
                "projection_not_ready",
                "projection_building",
                "projection_failed",
                "projection_stale",
            }
            for entry in payload.get("runtime_blockers") or []
        )
    ]
    runtime_blocked_route_ids = [
        payload["route_id"]
        for payload in route_payloads
        if payload["route_id"] not in runtime_ready_route_ids
    ]
    compatibility_projection_route_ids = [
        payload["route_id"]
        for payload in route_payloads
        if bool(payload.get("compatibility_projection_reliance"))
    ]
    canonical_projection_route_ids = [
        payload["route_id"]
        for payload in route_payloads
        if len(list(payload.get("canonical_projection_target_ids") or [])) > 0
    ]
    support_state_counts: Dict[str, int] = {}
    blocker_kind_counts: Dict[str, int] = {}
    for payload in route_payloads:
        support_state = str(payload.get("support_state") or "")
        if support_state:
            support_state_counts[support_state] = support_state_counts.get(support_state, 0) + 1
        for blocker in payload.get("runtime_blockers") or []:
            if not isinstance(blocker, dict):
                continue
            kind = str(blocker.get("kind") or "")
            if not kind:
                continue
            blocker_kind_counts[kind] = blocker_kind_counts.get(kind, 0) + 1
    full_route_coverage_ready = all(payload["implemented"] for payload in route_payloads)
    full_runtime_coverage_ready = all(payload.get("runtime_ready", False) for payload in route_payloads)
    route_execution_ready = len(non_executable_required_routes) == 0
    route_runtime_ready = len(non_runtime_ready_required_routes) == 0
    declared_executable_routes_runtime_ready = len(declared_executable_runtime_blocked_ids) == 0

    backend_connectivity = build_backend_connectivity_payload(effective_profile, configuration=config)
    required_backend_planes = {"authority"}
    if any(
        payload.get("projection_dependency_mode") == "required_external_projection"
        for payload in route_payloads
        if payload["route_id"] in required_route_ids
    ):
        required_backend_planes.add("projection")
    non_reachable_required_backends = [
        plane
        for plane in sorted(required_backend_planes)
        if str((backend_connectivity.get(plane) or {}).get("status") or "") == "unreachable"
    ]
    backend_connectivity_ready = len(non_reachable_required_backends) == 0

    projection_blocker_route_map: Dict[str, List[str]] = {
        "projection_not_ready": [],
        "projection_building": [],
        "projection_failed": [],
        "projection_stale": [],
    }
    projection_blocker_projection_ids: Dict[str, List[str]] = {
        "projection_not_ready": [],
        "projection_building": [],
        "projection_failed": [],
        "projection_stale": [],
    }
    for payload in route_payloads:
        route_id = str(payload.get("route_id") or "")
        if route_id not in non_runtime_ready_required_routes:
            continue
        for blocker in payload.get("runtime_blockers") or []:
            if not isinstance(blocker, dict):
                continue
            kind = str(blocker.get("kind") or "")
            if kind not in projection_blocker_route_map:
                continue
            projection_blocker_route_map[kind].append(route_id)
            for projection_id in list(blocker.get("projection_ids") or []):
                projection_id = str(projection_id or "")
                if projection_id:
                    projection_blocker_projection_ids[kind].append(projection_id)
    projection_blocker_route_map = {
        kind: sorted(set(route_ids))
        for kind, route_ids in projection_blocker_route_map.items()
        if route_ids
    }
    projection_blocker_projection_ids = {
        kind: sorted(set(projection_ids))
        for kind, projection_ids in projection_blocker_projection_ids.items()
        if projection_ids
    }

    boot_ready = effective_profile.implemented and config["ready"] and route_runtime_ready and backend_connectivity_ready
    validation_error = None
    validation_error_kind = None
    validation_error_details: Dict[str, Any] = {}
    validation_error_hint: Optional[str] = None
    validation_error_docs_ref: Optional[str] = None
    validation_error_command: Optional[str] = None
    if not effective_profile.implemented:
        boot_ready = False
        validation_error_kind = "profile_not_implemented"
        validation_error = (
            f"QueryLake DB profile '{effective_profile.id}' is declared but not implemented on this deployment. "
            f"Use '{DEFAULT_DB_PROFILE}' for the current executable stack."
        )
        validation_error_hint = (
            f"Switch back to '{DEFAULT_DB_PROFILE}' or continue implementing the declared profile before enabling it."
        )
        validation_error_docs_ref = "docs/database/DB_COMPAT_PROFILES.md#profile-maturity-levels"
        validation_error_details = {
            "profile_id": effective_profile.id,
            "recommended_profile_id": DEFAULT_DB_PROFILE,
        }
    elif not config["ready"]:
        validation_error_kind = "configuration_invalid"
        failing = [
            item["env_var"]
            for item in config["requirements"]
            if item["required_for_execution"] and not item["valid"]
        ]
        validation_error = (
            f"Deployment profile '{effective_profile.id}' is missing or has malformed required configuration: "
            f"{', '.join(failing)}."
        )
        validation_error_hint = "Populate the missing environment variables or correct malformed values, then rerun profile diagnostics."
        validation_error_docs_ref = "docs/database/FIRST_SPLIT_STACK_DEPLOYMENT.md#configuration-checklist"
        validation_error_details = {
            "profile_id": effective_profile.id,
            "missing_or_invalid_env_vars": failing,
        }
    elif not route_execution_ready:
        validation_error_kind = "route_non_executable"
        validation_error = (
            f"Deployment profile '{effective_profile.id}' is configured, but these required retrieval routes remain non-executable: "
            f"{', '.join(non_executable_required_routes)}."
        )
        validation_error_hint = (
            "This profile is enabled, but one or more required route executors are still placeholders. "
            "Either restrict the claimed executable surface or finish the corresponding route executor implementation."
        )
        validation_error_docs_ref = "docs/database/BACKEND_PROFILE_RELEASE_GATE.md#profile-promotion-checklist"
        validation_error_details = {
            "profile_id": effective_profile.id,
            "route_ids": list(non_executable_required_routes),
        }
    elif not route_runtime_ready:
        if "projection_failed" in projection_blocker_route_map:
            validation_error_kind = "projection_failed"
        elif "projection_building" in projection_blocker_route_map:
            validation_error_kind = "projection_building"
        elif "projection_stale" in projection_blocker_route_map:
            validation_error_kind = "projection_stale"
        elif "projection_not_ready" in projection_blocker_route_map:
            validation_error_kind = "projection_missing"
        elif projection_blocker_route_map:
            validation_error_kind = "projection_runtime_blocked"
        else:
            validation_error_kind = "route_not_runtime_ready"
        validation_error = (
            f"Deployment profile '{effective_profile.id}' is configured, but these required retrieval routes are not runtime-ready on this deployment: "
            f"{', '.join(non_runtime_ready_required_routes)}."
        )
        validation_error_docs_ref = "docs/database/PROFILE_DIAGNOSTICS.md#route-runtime-readiness-vs-route-execution-readiness"
        validation_error_command = (
            f"python scripts/db_compat_profile_bootstrap.py --profile {effective_profile.id}"
        )
        if validation_error_kind == "projection_failed":
            validation_error_hint = (
                "One or more required projections are marked failed. Inspect the projection diagnostics, repair the writer or source data issue, and rerun the bootstrap command."
            )
        elif validation_error_kind == "projection_building":
            validation_error_hint = (
                "Required projections are still building. Wait for completion or rerun diagnostics after the build finishes."
            )
        elif validation_error_kind == "projection_stale":
            validation_error_hint = (
                "Required projections are stale. Rebuild them before treating this deployment as runtime-ready."
            )
        elif validation_error_kind == "projection_missing":
            validation_error_hint = (
                "Required projections have not been materialized yet. Run the profile bootstrap command to create them."
            )
        else:
            validation_error_hint = (
                "Inspect route runtime blockers and projection diagnostics before enabling traffic on this profile."
            )
        validation_error_details = {
            "profile_id": effective_profile.id,
            "route_ids": list(non_runtime_ready_required_routes),
            "projection_blocker_routes": projection_blocker_route_map,
            "projection_blocker_projection_ids": projection_blocker_projection_ids,
            "blocker_kind_counts": {
                kind: len(route_ids) for kind, route_ids in projection_blocker_route_map.items()
            },
        }
    elif not backend_connectivity_ready:
        validation_error_kind = "backend_unreachable"
        validation_error = (
            f"Deployment profile '{effective_profile.id}' failed active backend connectivity probes for required planes: "
            f"{', '.join(non_reachable_required_backends)}."
        )
        validation_error_hint = (
            "Fix the unreachable backend plane, then rerun profile diagnostics with probing enabled."
        )
        validation_error_docs_ref = "docs/database/PROFILE_DIAGNOSTICS.md#what-diagnostics-contain"
        validation_error_details = {
            "profile_id": effective_profile.id,
            "backend_planes": list(non_reachable_required_backends),
        }

    payload = {
        "profile": capabilities_payload["profile"],
        "capabilities": capabilities_payload["capabilities"],
        "representation_scopes": capabilities_payload.get("representation_scopes") or {},
        "route_support_v2": list(capabilities_payload.get("route_support_v2") or []),
        "configuration": config,
        "execution_target": execution_target,
        "startup_validation": {
            "boot_ready": boot_ready,
            "profile_implemented": effective_profile.implemented,
            "configuration_ready": config["ready"],
            "route_execution_ready": route_execution_ready,
            "route_runtime_ready": route_runtime_ready,
            "declared_executable_routes_runtime_ready": declared_executable_routes_runtime_ready,
            "backend_connectivity_ready": backend_connectivity_ready,
            "inspected_route_ids": inspected_route_ids,
            "required_route_ids": required_route_ids,
            "optional_route_ids": optional_route_ids,
            "declared_route_support": declared_route_support,
            "declared_executable_route_ids": required_route_ids,
            "declared_optional_route_ids": optional_route_ids,
            "non_executable_required_routes": non_executable_required_routes,
            "non_executable_optional_routes": non_executable_optional_routes,
            "full_route_coverage_ready": full_route_coverage_ready,
            "non_runtime_ready_required_routes": non_runtime_ready_required_routes,
            "non_runtime_ready_optional_routes": non_runtime_ready_optional_routes,
            "declared_executable_runtime_ready_ids": declared_executable_runtime_ready_ids,
            "declared_executable_runtime_blocked_ids": declared_executable_runtime_blocked_ids,
            "non_reachable_required_backends": non_reachable_required_backends,
            "full_runtime_coverage_ready": full_runtime_coverage_ready,
            "validation_error_kind": validation_error_kind,
            "validation_error": validation_error,
            "validation_error_details": validation_error_details,
            "validation_error_hint": validation_error_hint,
            "validation_error_docs_ref": validation_error_docs_ref,
            "validation_error_command": validation_error_command,
        },
        "route_summary": {
            "inspected_route_count": len(route_payloads),
            "declared_route_count": len(declared_route_support),
            "declared_executable_route_count": len(required_route_ids),
            "declared_optional_route_count": len(optional_route_ids),
            "executable_route_count": len(executable_route_ids),
            "runtime_ready_route_count": len(runtime_ready_route_ids),
            "declared_executable_runtime_ready_count": len(declared_executable_runtime_ready_ids),
            "declared_executable_runtime_blocked_count": len(declared_executable_runtime_blocked_ids),
            "projection_blocked_route_count": len(projection_blocked_route_ids),
            "runtime_blocked_route_count": len(runtime_blocked_route_ids),
            "compatibility_projection_route_count": len(compatibility_projection_route_ids),
            "canonical_projection_route_count": len(canonical_projection_route_ids),
            "support_state_counts": support_state_counts,
            "blocker_kind_counts": blocker_kind_counts,
            "declared_route_support": declared_route_support,
            "declared_executable_route_ids": required_route_ids,
            "declared_optional_route_ids": optional_route_ids,
            "executable_route_ids": executable_route_ids,
            "runtime_ready_route_ids": runtime_ready_route_ids,
            "declared_executable_runtime_ready_ids": declared_executable_runtime_ready_ids,
            "declared_executable_runtime_blocked_ids": declared_executable_runtime_blocked_ids,
            "projection_blocked_route_ids": projection_blocked_route_ids,
            "runtime_blocked_route_ids": runtime_blocked_route_ids,
            "compatibility_projection_route_ids": compatibility_projection_route_ids,
            "canonical_projection_route_ids": canonical_projection_route_ids,
        },
        "route_executors": route_payloads,
        "lane_diagnostics": lane_diagnostics,
        "backend_connectivity": backend_connectivity,
    }
    if is_local_profile_v2(effective_profile):
        payload["local_profile"] = build_local_profile_diagnostics_payload(
            profile=effective_profile,
            route_payloads=route_payloads,
            projection_diagnostics=projection_diagnostics,
        )
    return payload


def _diagnostic_probes_enabled() -> bool:
    value = str(os.getenv(PROFILE_DIAGNOSTICS_PROBE_ENV, "0")).strip().lower()
    return value in {"1", "true", "yes", "on"}


def _diagnostic_probe_timeout_seconds() -> float:
    try:
        value = float(os.getenv(PROFILE_DIAGNOSTICS_PROBE_TIMEOUT_ENV, "1.5"))
    except ValueError:
        return 1.5
    if value <= 0:
        return 1.5
    return value


def _probe_sql_authority_connectivity(*, database_url: str, timeout_seconds: float) -> Dict[str, Any]:
    connect_timeout = max(1, int(timeout_seconds))
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": connect_timeout},
    )
    try:
        with engine.connect() as connection:
            scalar = connection.execute(text("SELECT 1")).scalar()
        return {
            "status": "reachable" if int(scalar or 0) == 1 else "unreachable",
            "checked": True,
            "detail": "Authority SQL probe completed with SELECT 1.",
        }
    except Exception as exc:
        return {
            "status": "unreachable",
            "checked": True,
            "detail": str(exc),
        }
    finally:
        engine.dispose()


def _build_authority_connectivity_payload(profile: DeploymentProfile, configuration: Dict[str, Any]) -> Dict[str, Any]:
    def _safe_target(url: Optional[str]) -> Optional[Dict[str, Any]]:
        if not url:
            return None
        try:
            parsed = urlparse(str(url))
        except Exception:
            return None
        target: Dict[str, Any] = {}
        if parsed.scheme:
            target["scheme"] = parsed.scheme
        if parsed.hostname:
            target["host"] = parsed.hostname
        if parsed.port is not None:
            target["port"] = int(parsed.port)
        path = str(parsed.path or "").strip("/")
        if path:
            target["database"] = path.split("/")[-1]
        return target or None

    backend = profile.backend_stack.authority
    if backend == "postgresql":
        if _diagnostic_probes_enabled():
            from QueryLake.database.create_db_session import (
                configured_database_connect_timeout,
                configured_database_url,
            )

            payload = {
                "backend": backend,
                "checked": False,
                "checked_at": None,
            }
            payload.update(
                _probe_sql_authority_connectivity(
                    database_url=configured_database_url(),
                    timeout_seconds=float(configured_database_connect_timeout()),
                )
            )
            return payload
        return {
            "backend": backend,
            "status": "assumed_local_sql_engine",
            "checked": False,
            "checked_at": None,
            "detail": "Current gold deployment uses the co-located SQL authority engine.",
        }
    if backend == "aurora_postgresql":
        from QueryLake.database.create_db_session import (
            configured_authority_database_url,
            configured_database_connect_timeout,
        )

        authority_url = configured_authority_database_url()
        authority_override_present = any(
            item["env_var"] == "QUERYLAKE_AUTHORITY_DATABASE_URL" and item["valid"]
            for item in configuration.get("requirements", [])
        )
        source_env = "QUERYLAKE_AUTHORITY_DATABASE_URL" if authority_override_present else "QUERYLAKE_DATABASE_URL"
        if _diagnostic_probes_enabled():
            payload = {
                "backend": backend,
                "checked": False,
                "checked_at": None,
                "database_url_env": source_env,
            }
            safe_target = _safe_target(authority_url)
            if safe_target is not None:
                payload["target"] = safe_target
            payload.update(
                _probe_sql_authority_connectivity(
                    database_url=authority_url,
                    timeout_seconds=float(configured_database_connect_timeout()),
                )
            )
            return payload
        return {
            "backend": backend,
            "status": "configured_authority_target" if authority_override_present else "assumed_current_sql_engine",
            "checked": False,
            "checked_at": None,
            "database_url_env": source_env,
            **({"target": _safe_target(authority_url)} if _safe_target(authority_url) is not None else {}),
            "detail": (
                "Split-stack authority plane is configured explicitly via QUERYLAKE_AUTHORITY_DATABASE_URL."
                if authority_override_present
                else "Current split-stack authority access still resolves through the active SQLAlchemy engine. Set QUERYLAKE_AUTHORITY_DATABASE_URL to declare an explicit authority target for diagnostics and future cutover."
            ),
        }

    authority_envs = {
        "mongodb": "QUERYLAKE_MONGO_URI",
        "planetscale": "QUERYLAKE_PLANETSCALE_DSN",
    }
    env_var = authority_envs.get(backend)
    if env_var is not None:
        present = any(item["env_var"] == env_var and item["valid"] for item in configuration.get("requirements", []))
        return {
            "backend": backend,
            "status": "configured_unprobed" if present else "configuration_incomplete",
            "checked": False,
            "checked_at": None,
            "env_var": env_var,
            "detail": "Authority backend reachability probing is not yet implemented for this backend family.",
        }

    return {
        "backend": backend,
        "status": "not_probed",
        "checked": False,
        "checked_at": None,
        "detail": "Authority backend reachability probing is not yet implemented for this backend family.",
    }


def _build_projection_connectivity_payload(profile: DeploymentProfile, configuration: Dict[str, Any]) -> Dict[str, Any]:
    projection_backend = profile.backend_stack.lexical
    if projection_backend in {"paradedb", "none"}:
        return {
            "backend": projection_backend,
            "status": "co_located_with_authority" if projection_backend == "paradedb" else "not_applicable",
            "checked": False,
            "checked_at": None,
            "detail": "Projection execution is co-located with the authority SQL engine." if projection_backend == "paradedb" else "This profile does not declare an external projection backend.",
        }

    if projection_backend == "opensearch":
        endpoint = os.getenv("QUERYLAKE_SEARCH_BACKEND_URL")
        namespace = os.getenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE")
        configured = any(
            item["env_var"] == "QUERYLAKE_SEARCH_BACKEND_URL" and item["valid"]
            for item in configuration.get("requirements", [])
        )
        target: Dict[str, Any] = {}
        if endpoint:
            try:
                parsed = urlparse(str(endpoint))
                if parsed.scheme:
                    target["scheme"] = parsed.scheme
                if parsed.hostname:
                    target["host"] = parsed.hostname
                if parsed.port is not None:
                    target["port"] = int(parsed.port)
            except Exception:
                target = {}
        if namespace:
            target["index_namespace"] = namespace
        payload: Dict[str, Any] = {
            "backend": projection_backend,
            "checked": False,
            "checked_at": None,
            "endpoint": endpoint,
        }
        if target:
            payload["target"] = target
        if not configured or not endpoint:
            payload.update(
                {
                    "status": "configuration_incomplete",
                    "detail": "QUERYLAKE_SEARCH_BACKEND_URL is missing or malformed.",
                }
            )
            return payload
        if not _diagnostic_probes_enabled():
            payload.update(
                {
                    "status": "configured_unprobed",
                    "detail": "Projection backend is configured. Enable QUERYLAKE_PROFILE_DIAGNOSTICS_PROBE=1 to probe reachability.",
                }
            )
            return payload
        timeout = _diagnostic_probe_timeout_seconds()
        try:
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                response = client.get(endpoint.rstrip("/"))
            payload.update(
                {
                    "status": "reachable" if response.status_code < 500 else "unreachable",
                    "checked": True,
                    "checked_at": time.time(),
                    "status_code": response.status_code,
                    "detail": f"OpenSearch probe returned HTTP {response.status_code}.",
                }
            )
            return payload
        except Exception as exc:
            payload.update(
                {
                    "status": "unreachable",
                    "checked": True,
                    "checked_at": time.time(),
                    "detail": str(exc),
                }
            )
            return payload

    return {
        "backend": projection_backend,
        "status": "not_probed",
        "checked": False,
        "checked_at": None,
        "detail": "Projection backend reachability probing is not yet implemented for this backend family.",
    }


def build_backend_connectivity_payload(
    profile: Optional[DeploymentProfile] = None,
    *,
    configuration: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    effective_profile = profile or get_deployment_profile()
    effective_configuration = configuration or build_profile_configuration_payload(effective_profile)
    return {
        "authority": _build_authority_connectivity_payload(effective_profile, effective_configuration),
        "projection": _build_projection_connectivity_payload(effective_profile, effective_configuration),
    }

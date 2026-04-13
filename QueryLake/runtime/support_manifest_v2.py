from __future__ import annotations

from typing import Any, Dict, Iterable, List

from pydantic import BaseModel, Field

from QueryLake.runtime.representation_materialization_v2 import RepresentationScopeRef


REPRESENTATION_SCOPE_REGISTRY: Dict[str, RepresentationScopeRef] = {
    "document_chunk": RepresentationScopeRef(
        scope_id="document_chunk",
        authority_model="document_segment",
        compatibility_projection=True,
        metadata={
            "representation_kind": "chunk_compatibility_projection",
            "intended_routes": [
                "search_hybrid.document_chunk",
                "search_bm25.document_chunk",
                "retrieval.sparse.vector",
            ],
        },
    ),
    "file_chunk": RepresentationScopeRef(
        scope_id="file_chunk",
        authority_model="file_chunk",
        compatibility_projection=False,
        metadata={
            "representation_kind": "file_chunk_projection",
            "intended_routes": ["search_file_chunks"],
        },
    ),
    "document_segment_graph": RepresentationScopeRef(
        scope_id="document_segment_graph",
        authority_model="document_segment",
        compatibility_projection=False,
        metadata={
            "representation_kind": "graph_relation_view",
            "intended_routes": ["retrieval.graph.traversal"],
        },
    ),
}


ROUTE_REPRESENTATION_SCOPE_IDS: Dict[str, str] = {
    "search_hybrid.document_chunk": "document_chunk",
    "search_bm25.document_chunk": "document_chunk",
    "search_file_chunks": "file_chunk",
    "retrieval.sparse.vector": "document_chunk",
    "retrieval.graph.traversal": "document_segment_graph",
}


ROUTE_CAPABILITY_DEPENDENCIES: Dict[str, List[str]] = {
    "search_hybrid.document_chunk": [
        "retrieval.lexical.bm25",
        "retrieval.dense.vector",
    ],
    "search_bm25.document_chunk": ["retrieval.lexical.bm25"],
    "search_file_chunks": ["retrieval.lexical.bm25"],
    "retrieval.sparse.vector": ["retrieval.sparse.vector"],
    "retrieval.graph.traversal": ["retrieval.graph.traversal"],
}


class RouteSupportManifestEntryV2(BaseModel):
    route_id: str
    support_state: str
    declared_executable: bool
    declared_optional: bool
    representation_scope: RepresentationScopeRef
    capability_dependencies: List[str] = Field(default_factory=list)
    notes: str | None = None


class ProfileSupportManifestV2(BaseModel):
    profile_id: str
    routes: List[RouteSupportManifestEntryV2] = Field(default_factory=list)


def get_representation_scope(route_id: str) -> RepresentationScopeRef:
    scope_id = ROUTE_REPRESENTATION_SCOPE_IDS.get(route_id, "document_chunk")
    return REPRESENTATION_SCOPE_REGISTRY[scope_id]


def build_route_support_manifest_entries_v2(
    route_support_rows: Iterable[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    for row in route_support_rows:
        route_id = str(row.get("route_id") or "")
        if not route_id:
            continue
        scope = get_representation_scope(route_id)
        entry = RouteSupportManifestEntryV2(
            route_id=route_id,
            support_state=str(row.get("declared_state") or "unsupported"),
            declared_executable=bool(row.get("declared_executable")),
            declared_optional=bool(row.get("declared_optional")),
            representation_scope=scope,
            capability_dependencies=list(ROUTE_CAPABILITY_DEPENDENCIES.get(route_id, [])),
            notes=(str(row.get("notes")) if row.get("notes") is not None else None),
        )
        entries.append(entry.model_dump())
    return entries


def build_representation_scope_registry_payload() -> Dict[str, Dict[str, Any]]:
    return {
        scope_id: scope.model_dump()
        for scope_id, scope in REPRESENTATION_SCOPE_REGISTRY.items()
    }

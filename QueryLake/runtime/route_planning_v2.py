from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from QueryLake.runtime.projection_ir_v2 import instantiate_projection_ir_v2
from QueryLake.runtime.query_ir_v2 import instantiate_query_ir_v2


def _payload_dict(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if hasattr(value, "model_dump"):
        return dict(value.model_dump())
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _route_id_from_payload(route_executor_payload: Mapping[str, Any], template: Mapping[str, Any]) -> str:
    return str(
        route_executor_payload.get("route_id")
        or template.get("route_id")
        or ""
    )


def _fallback_representation_scope_id(route_id: str) -> str:
    route_id = str(route_id or "")
    if route_id in {"search_bm25.document_chunk", "search_hybrid.document_chunk"}:
        return "document_chunk"
    if route_id == "search_file_chunks":
        return "file_chunk"
    return ""


def _representation_scope_id_from_payload(
    route_executor_payload: Mapping[str, Any],
    query_template: Mapping[str, Any],
    projection_template: Mapping[str, Any],
) -> str:
    route_id = _route_id_from_payload(route_executor_payload, query_template)
    return str(
        route_executor_payload.get("representation_scope_id")
        or query_template.get("representation_scope_id")
        or projection_template.get("representation_scope_id")
        or _fallback_representation_scope_id(route_id)
        or ""
    )


def _lane_family_from_projection_descriptor(descriptor_id: str) -> str:
    descriptor_id = str(descriptor_id or "")
    if "dense" in descriptor_id:
        return "dense"
    return "lexical"


def _target_backend_family_from_lane_family(lane_family: str) -> str:
    if lane_family == "dense":
        return "vector_index"
    return "lexical_index"


def _target_backend_name_from_lane_family(
    route_executor_payload: Mapping[str, Any],
    lane_family: str,
) -> str:
    backend_stack = _payload_dict(route_executor_payload.get("backend_stack"))
    if lane_family == "dense":
        return str(backend_stack.get("dense") or "")
    return str(backend_stack.get("lexical") or "")


def _capability_dependencies_for_route(route_id: str) -> list[str]:
    route_id = str(route_id or "")
    if route_id == "search_hybrid.document_chunk":
        return ["retrieval.lexical.bm25", "retrieval.dense.vector"]
    if route_id in {"search_bm25.document_chunk", "search_file_chunks"}:
        return ["retrieval.lexical.bm25"]
    return []


def _fallback_projection_required_targets(
    route_executor_payload: Mapping[str, Any],
) -> list[dict[str, Any]]:
    support_state = str(route_executor_payload.get("support_state") or "planned")
    required_targets: list[dict[str, Any]] = []
    for descriptor_id in list(route_executor_payload.get("projection_descriptors") or []):
        lane_family = _lane_family_from_projection_descriptor(str(descriptor_id))
        required_targets.append(
            {
                "target_id": str(descriptor_id),
                "required": True,
                "target_backend_family": _target_backend_family_from_lane_family(lane_family),
                "support_state": support_state,
                "metadata": {
                    "target_backend_name": _target_backend_name_from_lane_family(route_executor_payload, lane_family),
                    "lane_family": lane_family,
                },
            }
        )
    return required_targets


def _fallback_projection_buildability_class(route_executor_payload: Mapping[str, Any]) -> str:
    support_state = str(route_executor_payload.get("support_state") or "planned")
    if support_state == "supported":
        return "executable_requires_build"
    if support_state == "degraded":
        return "degraded_executable"
    return "planned"


def instantiate_route_query_ir_v2(
    route_executor_payload: Mapping[str, Any],
    *,
    raw_query_text: str | None = None,
    lexical_query_text: str | None = None,
    normalized_query_text: str | None = None,
    use_dense: Optional[bool] = None,
    use_sparse: Optional[bool] = None,
    collection_ids: Optional[list[str]] = None,
    document_ids: Optional[list[str]] = None,
    metadata_filters: Optional[list[dict[str, Any]]] = None,
    planner_hints: Optional[dict[str, Any]] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> Dict[str, Any]:
    planning_v2 = _payload_dict(route_executor_payload.get("planning_v2"))
    query_template = _payload_dict(planning_v2.get("query_ir_v2_template"))
    projection_template = _payload_dict(planning_v2.get("projection_ir_v2"))

    route_id = _route_id_from_payload(route_executor_payload, query_template)
    representation_scope_id = _representation_scope_id_from_payload(
        route_executor_payload,
        query_template,
        projection_template,
    )
    template_raw_query = str(query_template.get("raw_query_text") or "")

    payload = instantiate_query_ir_v2(
        query_template or None,
        raw_query_text=template_raw_query if raw_query_text is None else str(raw_query_text),
        route_id=route_id or None,
        representation_scope_id=representation_scope_id or None,
        lexical_query_text=lexical_query_text,
        normalized_query_text=normalized_query_text,
        use_dense=use_dense,
        use_sparse=use_sparse,
        collection_ids=collection_ids,
        document_ids=document_ids,
        metadata_filters=metadata_filters,
        planner_hints=planner_hints,
        metadata=metadata,
    )
    return payload.model_dump()


def instantiate_route_projection_ir_v2(
    route_executor_payload: Mapping[str, Any],
    *,
    metadata: Optional[dict[str, Any]] = None,
) -> Dict[str, Any]:
    planning_v2 = _payload_dict(route_executor_payload.get("planning_v2"))
    query_template = _payload_dict(planning_v2.get("query_ir_v2_template"))
    projection_template = _payload_dict(planning_v2.get("projection_ir_v2"))

    route_id = _route_id_from_payload(route_executor_payload, query_template)
    representation_scope_id = _representation_scope_id_from_payload(
        route_executor_payload,
        query_template,
        projection_template,
    )
    if not projection_template:
        if not route_id or not representation_scope_id:
            return {}
        required_targets = _fallback_projection_required_targets(route_executor_payload)
        if not required_targets:
            return {}
        projection_template = {
            "required_targets": required_targets,
            "optional_targets": [],
            "capability_dependencies": _capability_dependencies_for_route(route_id),
            "runtime_blockers": ["projection_build_required"],
            "buildability_class": _fallback_projection_buildability_class(route_executor_payload),
            "recovery_hints": ["bootstrap_required_projections"],
            "metadata": {
                "planning_surface": "route_resolution",
                "backend_stack": _payload_dict(route_executor_payload.get("backend_stack")),
            },
        }
    payload = instantiate_projection_ir_v2(
        projection_template,
        profile_id=str(
            projection_template.get("profile_id")
            or route_executor_payload.get("profile_id")
            or ""
        ),
        route_id=route_id,
        representation_scope_id=representation_scope_id,
        required_targets=list(projection_template.get("required_targets") or []),
        optional_targets=list(projection_template.get("optional_targets") or []),
        capability_dependencies=list(projection_template.get("capability_dependencies") or []),
        runtime_blockers=list(projection_template.get("runtime_blockers") or []),
        buildability_class=projection_template.get("buildability_class") or "planned",
        recovery_hints=list(projection_template.get("recovery_hints") or []),
        metadata=dict(metadata or {}),
    )
    return payload.model_dump()


def instantiate_route_planning_v2(
    route_executor_payload: Mapping[str, Any],
    *,
    raw_query_text: str | None = None,
    lexical_query_text: str | None = None,
    normalized_query_text: str | None = None,
    use_dense: Optional[bool] = None,
    use_sparse: Optional[bool] = None,
    collection_ids: Optional[list[str]] = None,
    document_ids: Optional[list[str]] = None,
    metadata_filters: Optional[list[dict[str, Any]]] = None,
    planner_hints: Optional[dict[str, Any]] = None,
    query_metadata: Optional[dict[str, Any]] = None,
    projection_metadata: Optional[dict[str, Any]] = None,
) -> Dict[str, Any]:
    planning_v2 = _payload_dict(route_executor_payload.get("planning_v2"))
    query_template = _payload_dict(planning_v2.get("query_ir_v2_template"))
    projection_template = _payload_dict(planning_v2.get("projection_ir_v2"))
    route_id = _route_id_from_payload(route_executor_payload, query_template)
    representation_scope_id = _representation_scope_id_from_payload(
        route_executor_payload,
        query_template,
        projection_template,
    )
    if not route_id and not representation_scope_id and not planning_v2:
        return {}
    query_ir_v2 = instantiate_route_query_ir_v2(
        route_executor_payload,
        raw_query_text=raw_query_text,
        lexical_query_text=lexical_query_text,
        normalized_query_text=normalized_query_text,
        use_dense=use_dense,
        use_sparse=use_sparse,
        collection_ids=collection_ids,
        document_ids=document_ids,
        metadata_filters=metadata_filters,
        planner_hints=planner_hints,
        metadata=query_metadata,
    )
    projection_ir_v2 = instantiate_route_projection_ir_v2(
        route_executor_payload,
        metadata=projection_metadata,
    )
    payload = dict(planning_v2)
    payload.setdefault("planning_surface", "route_resolution")
    payload["query_ir_v2_template"] = dict(query_ir_v2)
    if projection_ir_v2:
        payload["projection_ir_v2"] = dict(projection_ir_v2)
    return payload

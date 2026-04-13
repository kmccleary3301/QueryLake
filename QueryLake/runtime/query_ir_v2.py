from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class QueryStrictnessPolicy(str, Enum):
    exact = "exact"
    approximate = "approximate"
    reject_if_not_exact = "reject_if_not_exact"


class SupportClassification(str, Enum):
    native_supported = "native_supported"
    degraded_supported = "degraded_supported"
    unsupported = "unsupported"


class FilterIRV2(BaseModel):
    collection_ids: list[str] = Field(default_factory=list)
    document_ids: list[str] = Field(default_factory=list)
    metadata_filters: list[dict[str, Any]] = Field(default_factory=list)


class QueryIRV2(BaseModel):
    raw_query_text: str
    normalized_query_text: str
    lexical_query_text: str | None = None
    use_dense: bool = True
    use_sparse: bool = False
    filter_ir: FilterIRV2 = Field(default_factory=FilterIRV2)
    strictness_policy: QueryStrictnessPolicy = QueryStrictnessPolicy.approximate
    representation_scope_id: str
    route_id: str
    planner_hints: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def requested_lanes(self) -> list[str]:
        lanes: list[str] = []
        if (self.lexical_query_text or self.normalized_query_text).strip():
            lanes.append("lexical")
        if self.use_dense:
            lanes.append("dense")
        if self.use_sparse:
            lanes.append("sparse")
        return lanes


def instantiate_query_ir_v2(
    template: QueryIRV2 | dict[str, Any] | None,
    *,
    raw_query_text: str,
    route_id: str | None = None,
    representation_scope_id: str | None = None,
    lexical_query_text: str | None = None,
    normalized_query_text: str | None = None,
    use_dense: bool | None = None,
    use_sparse: bool | None = None,
    collection_ids: list[str] | None = None,
    document_ids: list[str] | None = None,
    metadata_filters: list[dict[str, Any]] | None = None,
    planner_hints: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> QueryIRV2:
    base: dict[str, Any]
    if isinstance(template, QueryIRV2):
        base = template.model_dump()
    elif isinstance(template, dict):
        base = dict(template)
    else:
        base = {}

    base["raw_query_text"] = str(raw_query_text or "")
    if normalized_query_text is not None:
        base["normalized_query_text"] = str(normalized_query_text)
    else:
        base["normalized_query_text"] = str(raw_query_text or "").strip()
    if lexical_query_text is not None:
        base["lexical_query_text"] = str(lexical_query_text)
    else:
        base["lexical_query_text"] = str(raw_query_text or "")
    if use_dense is not None:
        base["use_dense"] = bool(use_dense)
    if use_sparse is not None:
        base["use_sparse"] = bool(use_sparse)
    if route_id is not None:
        base["route_id"] = str(route_id)
    if representation_scope_id is not None:
        base["representation_scope_id"] = str(representation_scope_id)

    filter_ir = dict(base.get("filter_ir") or {})
    if collection_ids is not None:
        filter_ir["collection_ids"] = [str(value) for value in list(collection_ids or []) if str(value)]
    if document_ids is not None:
        filter_ir["document_ids"] = [str(value) for value in list(document_ids or []) if str(value)]
    if metadata_filters is not None:
        filter_ir["metadata_filters"] = list(metadata_filters or [])
    base["filter_ir"] = filter_ir

    if planner_hints:
        merged_hints = dict(base.get("planner_hints") or {})
        merged_hints.update(dict(planner_hints))
        base["planner_hints"] = merged_hints
    if metadata:
        merged_metadata = dict(base.get("metadata") or {})
        merged_metadata.update(dict(metadata))
        base["metadata"] = merged_metadata

    return QueryIRV2.model_validate(base)

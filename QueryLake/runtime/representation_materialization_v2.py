from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from QueryLake.runtime.projection_contracts import ProjectionAuthorityReference


class MaterializationState(str, Enum):
    absent = "absent"
    building = "building"
    ready = "ready"
    stale = "stale"
    failed = "failed"


class InvalidationReason(str, Enum):
    authority_content_changed = "authority_content_changed"
    authority_metadata_changed = "authority_metadata_changed"
    representation_recipe_changed = "representation_recipe_changed"
    embedding_model_changed = "embedding_model_changed"
    index_schema_changed = "index_schema_changed"
    capability_profile_changed = "capability_profile_changed"
    manual_rebuild_requested = "manual_rebuild_requested"


class RepresentationScopeRef(BaseModel):
    scope_id: str
    authority_model: str
    compatibility_projection: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class MaterializationTargetV2(BaseModel):
    target_id: str
    profile_id: str
    representation_scope: RepresentationScopeRef
    record_schema: str
    target_backend_family: str
    target_backend_name: str
    authority_reference: ProjectionAuthorityReference
    metadata: dict[str, Any] = Field(default_factory=dict)


class MaterializationStatusV2(BaseModel):
    target_id: str
    state: MaterializationState
    invalidated_by: list[InvalidationReason] = Field(default_factory=list)
    last_build_revision: str | None = None
    last_build_timestamp: str | None = None
    error_summary: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

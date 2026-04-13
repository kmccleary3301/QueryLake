from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ProjectionBuildabilityClass(str, Enum):
    executable_ready = "executable_ready"
    executable_requires_build = "executable_requires_build"
    executable_requires_backend = "executable_requires_backend"
    degraded_executable = "degraded_executable"
    unsupported = "unsupported"
    planned = "planned"


class ProjectionDependencyRef(BaseModel):
    target_id: str
    required: bool = True
    target_backend_family: str
    support_state: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RouteProjectionIRV2(BaseModel):
    profile_id: str
    route_id: str
    representation_scope_id: str
    required_targets: list[ProjectionDependencyRef] = Field(default_factory=list)
    optional_targets: list[ProjectionDependencyRef] = Field(default_factory=list)
    capability_dependencies: list[str] = Field(default_factory=list)
    runtime_blockers: list[str] = Field(default_factory=list)
    buildability_class: ProjectionBuildabilityClass
    recovery_hints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


def instantiate_projection_ir_v2(
    template: dict[str, Any] | None,
    *,
    profile_id: str,
    route_id: str,
    representation_scope_id: str,
    required_targets: list[dict[str, Any]] | None = None,
    optional_targets: list[dict[str, Any]] | None = None,
    capability_dependencies: list[str] | None = None,
    runtime_blockers: list[str] | None = None,
    buildability_class: str | ProjectionBuildabilityClass | None = None,
    recovery_hints: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> RouteProjectionIRV2:
    base = dict(template or {})
    base["profile_id"] = str(profile_id)
    base["route_id"] = str(route_id)
    base["representation_scope_id"] = str(representation_scope_id)
    if required_targets is not None:
        base["required_targets"] = list(required_targets)
    if optional_targets is not None:
        base["optional_targets"] = list(optional_targets)
    if capability_dependencies is not None:
        base["capability_dependencies"] = list(capability_dependencies)
    if runtime_blockers is not None:
        base["runtime_blockers"] = list(runtime_blockers)
    if buildability_class is not None:
        base["buildability_class"] = (
            buildability_class.value
            if isinstance(buildability_class, ProjectionBuildabilityClass)
            else str(buildability_class)
        )
    if recovery_hints is not None:
        base["recovery_hints"] = list(recovery_hints)
    if metadata:
        merged_metadata = dict(base.get("metadata") or {})
        merged_metadata.update(dict(metadata))
        base["metadata"] = merged_metadata
    return RouteProjectionIRV2.model_validate(base)

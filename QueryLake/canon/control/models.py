from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


PublishMode = Literal["shadow", "candidate_primary", "primary"]


class CanonPublishPointer(BaseModel):
    pointer_id: str
    graph_id: str
    package_revision: str
    profile_id: str
    route_ids: list[str] = Field(default_factory=list)
    mode: PublishMode
    metadata: dict[str, Any] = Field(default_factory=dict)


class CanonPublishReview(BaseModel):
    branch_name: str
    reviewed: bool = False
    ci_green: bool = False
    shadow_evidence_present: bool = False
    notes: list[str] = Field(default_factory=list)


class CanonPublishRequest(BaseModel):
    target: CanonPublishPointer
    current: Optional[CanonPublishPointer] = None
    review: CanonPublishReview
    exit_readiness: dict[str, Any] = Field(default_factory=dict)


class CanonPublishStep(BaseModel):
    step_id: str
    action: str
    required: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class CanonPublishRevertPlan(BaseModel):
    available: bool
    revert_to_pointer_id: Optional[str] = None
    revert_mode: Optional[PublishMode] = None
    steps: list[CanonPublishStep] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

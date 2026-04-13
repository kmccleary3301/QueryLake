from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pydantic import BaseModel, Field

from QueryLake.runtime.authority_projection_access import build_projection_materialization_target
from QueryLake.runtime.db_compat import DEPLOYMENT_PROFILES, DeploymentProfile, get_deployment_profile
from QueryLake.runtime.local_profile_v2 import build_local_projection_build_ir_v2
from QueryLake.runtime.projection_contracts import ProjectionAuthorityReference, ProjectionBuildState
from QueryLake.runtime.projection_registry import (
    ProjectionDescriptor,
    get_projection_descriptor,
    list_projection_descriptors,
)
from QueryLake.runtime.projection_writers import (
    get_projection_writer_runtime,
    resolve_projection_writer,
)

if TYPE_CHECKING:
    from sqlmodel import Session


class ProjectionReference(BaseModel):
    projection_record_id: str
    projection_id: str
    projection_version: str
    lane_family: str
    projection_backend: str
    source_document_id: Optional[str] = None
    source_segment_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProjectionRefreshRequest(BaseModel):
    projection_id: str
    projection_version: str = "v1"
    lane_families: List[str] = Field(default_factory=list)
    collection_ids: List[str] = Field(default_factory=list)
    document_ids: List[str] = Field(default_factory=list)
    segment_ids: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProjectionRefreshAction(BaseModel):
    projection_descriptor_id: str
    lane_family: str
    record_schema: str
    adapter_backend: str
    writer_id: Optional[str] = None
    writer_implemented: bool = False
    implemented: bool
    support_state: str
    mode: str
    current_status: str = "absent"
    invalidated_by: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class ProjectionRefreshPlan(BaseModel):
    profile_id: str
    projection_id: str
    projection_version: str
    projection_descriptor: Dict[str, Any]
    actions: List[ProjectionRefreshAction] = Field(default_factory=list)
    status_snapshot: List[ProjectionBuildState] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


LANE_TO_BACKEND_ATTR = {
    "lexical": "lexical",
    "dense": "dense",
    "sparse": "sparse",
    "graph": "graph",
}

PROJECTION_METADATA_STORE_ENV = "QUERYLAKE_PROJECTION_METADATA_PATH"
_DEFAULT_PROJECTION_METADATA_STORE = ".querylake_projection_metadata.json"
PROFILE_BOOTSTRAP_PROJECTION_IDS: Dict[str, List[str]] = {
    "aws_aurora_pg_opensearch_v1": [
        "document_chunk_lexical_projection_v1",
        "document_chunk_dense_projection_v1",
        "file_chunk_lexical_projection_v1",
    ],
    "sqlite_fts5_dense_sidecar_local_v1": [
        "document_chunk_lexical_projection_v1",
        "document_chunk_dense_projection_v1",
        "file_chunk_lexical_projection_v1",
    ],
}


class ProjectionMetadataStore(BaseModel):
    records: Dict[str, ProjectionBuildState] = Field(default_factory=dict)


class ProjectionRefreshExecutionReport(BaseModel):
    profile_id: str
    projection_id: str
    executed_actions: List[ProjectionRefreshAction] = Field(default_factory=list)
    skipped_actions: List[ProjectionRefreshAction] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProjectionBootstrapItem(BaseModel):
    projection_id: str
    projection_version: str
    lane_family: str
    target_backend: str
    status_before: str = "absent"
    status_after: str = "absent"
    executed_action_count: int = 0
    skipped_action_count: int = 0
    build_revision: Optional[str] = None
    runtime_executable: bool = False
    support_state: str = "unsupported"
    lifecycle_outcome: str = "unknown"
    error_summary: Optional[str] = None
    materialization_target: Dict[str, Any] = Field(default_factory=dict)
    projection_plan_v2: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProjectionBootstrapReport(BaseModel):
    profile_id: str
    projection_ids: List[str] = Field(default_factory=list)
    projection_items: List[ProjectionBootstrapItem] = Field(default_factory=list)
    executed_actions: List[Dict[str, Any]] = Field(default_factory=list)
    skipped_actions: List[Dict[str, Any]] = Field(default_factory=list)
    ready_projection_ids: List[str] = Field(default_factory=list)
    building_projection_ids: List[str] = Field(default_factory=list)
    stale_projection_ids: List[str] = Field(default_factory=list)
    failed_projection_ids: List[str] = Field(default_factory=list)
    absent_projection_ids: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


def _classify_bootstrap_lifecycle_outcome(
    *,
    status_before: str,
    status_after: str,
    runtime_executable: bool,
    executed_action_count: int,
    error_summary: Optional[str],
) -> str:
    if error_summary is not None or status_after == "failed":
        return "failed"
    if status_before == "absent" and status_after == "ready":
        return "materialized_from_absent"
    if status_before == "stale" and status_after == "ready":
        return "refreshed_from_stale"
    if status_before == "failed" and status_after == "ready":
        return "recovered_from_failed"
    if status_before == "ready" and status_after == "ready":
        return "rebuilt_ready" if executed_action_count > 0 else "unchanged_ready"
    if status_after == "building":
        return "building"
    if status_after == "stale":
        return "stale"
    if status_after == "absent":
        return "not_buildable" if not runtime_executable else "still_absent"
    if status_before != status_after:
        return f"state_changed:{status_before}->{status_after}"
    return status_after or "unknown"


class ProjectionPlanExplain(BaseModel):
    profile_id: str
    projection_id: str
    projection_version: str
    descriptor: Dict[str, Any]
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    status_snapshot: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProjectionDiagnosticItem(BaseModel):
    projection_id: str
    projection_version: str
    lane_family: str
    authority_model: str
    source_scope: str
    record_schema: str
    target_backend_family: str
    backend_name: str
    support_state: str
    executable: bool
    build_status: str
    action_mode: str
    invalidated_by: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    materialization_target: Dict[str, Any] = Field(default_factory=dict)
    build_state: Dict[str, Any] = Field(default_factory=dict)


class ProjectionDiagnosticsSummary(BaseModel):
    profile_id: str
    projection_items: List[ProjectionDiagnosticItem] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


def _projection_build_state(
    *,
    projection_id: str,
    projection_version: str,
    profile_id: str,
    lane_family: str,
    target_backend: str,
    status: str,
    last_build_revision: Optional[str] = None,
    last_build_timestamp: Optional[float] = None,
    error_summary: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> ProjectionBuildState:
    return ProjectionBuildState(
        projection_id=projection_id,
        projection_version=projection_version,
        profile_id=profile_id,
        lane_family=lane_family,
        target_backend=target_backend,
        status=status,
        last_build_revision=last_build_revision,
        last_build_timestamp=last_build_timestamp,
        error_summary=error_summary,
        metadata=dict(metadata or {}),
    )


def _metadata_store_path(path: Optional[str] = None) -> Path:
    configured = path or os.getenv(PROJECTION_METADATA_STORE_ENV, _DEFAULT_PROJECTION_METADATA_STORE)
    return Path(configured).expanduser().resolve()


def load_projection_metadata_store(path: Optional[str] = None) -> ProjectionMetadataStore:
    store_path = _metadata_store_path(path)
    if not store_path.exists():
        return ProjectionMetadataStore()
    payload = json.loads(store_path.read_text())
    return ProjectionMetadataStore.model_validate(payload)


def save_projection_metadata_store(store: ProjectionMetadataStore, path: Optional[str] = None) -> Path:
    store_path = _metadata_store_path(path)
    store_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=str(store_path.parent), prefix="projection_meta_", suffix=".json") as tmp:
        tmp.write(store.model_dump_json(indent=2))
        tmp_path = Path(tmp.name)
    tmp_path.replace(store_path)
    return store_path


def _build_state_key(projection_id: str, projection_version: str, profile_id: str, lane_family: str) -> str:
    return f"{profile_id}:{projection_id}:{projection_version}:{lane_family}"


def get_projection_build_state(
    *,
    projection_id: str,
    projection_version: str,
    lane_family: str,
    profile_id: Optional[str] = None,
    path: Optional[str] = None,
) -> Optional[ProjectionBuildState]:
    effective_profile_id = profile_id or get_deployment_profile().id
    store = load_projection_metadata_store(path)
    return store.records.get(_build_state_key(projection_id, projection_version, effective_profile_id, lane_family))


def set_projection_build_state(
    state: ProjectionBuildState,
    *,
    path: Optional[str] = None,
) -> ProjectionBuildState:
    store = load_projection_metadata_store(path)
    key = _build_state_key(state.projection_id, state.projection_version, state.profile_id, state.lane_family)
    store.records[key] = state
    save_projection_metadata_store(store, path)
    return state


def list_projection_build_states(
    *,
    projection_id: Optional[str] = None,
    profile_id: Optional[str] = None,
    path: Optional[str] = None,
) -> List[ProjectionBuildState]:
    store = load_projection_metadata_store(path)
    values = list(store.records.values())
    if projection_id is not None:
        values = [state for state in values if state.projection_id == projection_id]
    if profile_id is not None:
        values = [state for state in values if state.profile_id == profile_id]
    return values


def mark_projection_build_started(
    *,
    projection_id: str,
    projection_version: str,
    profile_id: str,
    lane_family: str,
    target_backend: str,
    build_revision: str,
    metadata: Optional[Dict[str, Any]] = None,
    path: Optional[str] = None,
) -> ProjectionBuildState:
    state = _projection_build_state(
        projection_id=projection_id,
        projection_version=projection_version,
        profile_id=profile_id,
        lane_family=lane_family,
        target_backend=target_backend,
        status="building",
        last_build_revision=build_revision,
        last_build_timestamp=time.time(),
        metadata=metadata,
    )
    return set_projection_build_state(state, path=path)


def mark_projection_build_ready(
    *,
    projection_id: str,
    projection_version: str,
    profile_id: str,
    lane_family: str,
    target_backend: str,
    build_revision: str,
    metadata: Optional[Dict[str, Any]] = None,
    path: Optional[str] = None,
) -> ProjectionBuildState:
    state = _projection_build_state(
        projection_id=projection_id,
        projection_version=projection_version,
        profile_id=profile_id,
        lane_family=lane_family,
        target_backend=target_backend,
        status="ready",
        last_build_revision=build_revision,
        last_build_timestamp=time.time(),
        metadata=metadata,
    )
    return set_projection_build_state(state, path=path)


def mark_projection_build_failed(
    *,
    projection_id: str,
    projection_version: str,
    profile_id: str,
    lane_family: str,
    target_backend: str,
    error_summary: str,
    build_revision: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    path: Optional[str] = None,
) -> ProjectionBuildState:
    existing = get_projection_build_state(
        projection_id=projection_id,
        projection_version=projection_version,
        lane_family=lane_family,
        profile_id=profile_id,
        path=path,
    )
    state = _projection_build_state(
        projection_id=projection_id,
        projection_version=projection_version,
        profile_id=profile_id,
        lane_family=lane_family,
        target_backend=target_backend,
        status="failed",
        last_build_revision=build_revision or (existing.last_build_revision if existing is not None else None),
        last_build_timestamp=time.time(),
        error_summary=error_summary,
        metadata=metadata or (existing.metadata if existing is not None else {}),
    )
    return set_projection_build_state(state, path=path)


def invalidate_projection_build_states(
    *,
    projection_id: str,
    projection_version: str,
    profile_id: str,
    lane_families: List[str],
    invalidated_by: List[str],
    path: Optional[str] = None,
) -> List[ProjectionBuildState]:
    invalidated: List[ProjectionBuildState] = []
    for lane_family in lane_families:
        existing = get_projection_build_state(
            projection_id=projection_id,
            projection_version=projection_version,
            lane_family=lane_family,
            profile_id=profile_id,
            path=path,
        )
        if existing is None:
            continue
        state = existing.model_copy(
            update={
                "status": "stale",
                "metadata": {
                    **dict(existing.metadata or {}),
                    "invalidated_by": list(invalidated_by),
                },
            }
        )
        invalidated.append(set_projection_build_state(state, path=path))
    return invalidated


def build_projection_reference(
    *,
    projection_record_id: str,
    projection_id: str,
    projection_version: str,
    lane_family: str,
    projection_backend: str,
    source_document_id: Optional[str] = None,
    source_segment_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> ProjectionReference:
    return ProjectionReference(
        projection_record_id=projection_record_id,
        projection_id=projection_id,
        projection_version=projection_version,
        lane_family=lane_family,
        projection_backend=projection_backend,
        source_document_id=source_document_id,
        source_segment_id=source_segment_id,
        metadata=dict(metadata or {}),
    )


def build_authority_reference(request: ProjectionRefreshRequest, *, descriptor: Optional[ProjectionDescriptor] = None) -> ProjectionAuthorityReference:
    effective_descriptor = descriptor or get_projection_descriptor(request.projection_id)
    return ProjectionAuthorityReference(
        authority_model=effective_descriptor.authority_model,
        document_ids=list(request.document_ids),
        segment_ids=list(request.segment_ids),
        collection_ids=list(request.collection_ids),
        metadata={
            "projection_id": request.projection_id,
            "projection_version": request.projection_version,
            **dict(request.metadata or {}),
        },
    )


def compute_projection_invalidation_reasons(request: ProjectionRefreshRequest) -> List[str]:
    reasons: List[str] = []
    if len(request.collection_ids) > 0:
        reasons.append("collection_scope_changed")
    if len(request.document_ids) > 0:
        reasons.append("document_scope_changed")
    if len(request.segment_ids) > 0:
        reasons.append("segment_scope_changed")

    metadata = dict(request.metadata or {})
    for metadata_key, reason in [
        ("authority_revision", "authority_revision_changed"),
        ("embedding_revision", "embedding_revision_changed"),
        ("metadata_revision", "metadata_filter_scope_changed"),
        ("operator_revision", "operator_semantics_changed"),
        ("force_rebuild", "force_rebuild_requested"),
    ]:
        if metadata.get(metadata_key):
            reasons.append(reason)
    return reasons


def build_projection_refresh_plan(
    request: ProjectionRefreshRequest,
    *,
    profile: Optional[DeploymentProfile] = None,
    metadata_store_path: Optional[str] = None,
) -> ProjectionRefreshPlan:
    effective_profile = profile or get_deployment_profile()
    descriptor = get_projection_descriptor(request.projection_id)
    requested_lanes = request.lane_families or [descriptor.lane_family]
    actions: List[ProjectionRefreshAction] = []
    capability_map = effective_profile.capability_map()
    invalidated_by = compute_projection_invalidation_reasons(request)
    status_snapshot: List[ProjectionBuildState] = []

    for lane_family in requested_lanes:
        capability_id = {
            "lexical": "retrieval.lexical.bm25",
            "dense": "retrieval.dense.vector",
            "sparse": "retrieval.sparse.vector",
            "graph": "retrieval.graph.traversal",
        }.get(lane_family, "")
        descriptor_capability = capability_map.get(capability_id) if capability_id else None
        support_state = descriptor_capability.support_state if descriptor_capability is not None else "unsupported"
        backend_attr = LANE_TO_BACKEND_ATTR.get(lane_family)
        backend_name = getattr(effective_profile.backend_stack, backend_attr, "unknown") if backend_attr else "unknown"
        writer = resolve_projection_writer(
            request.projection_id,
            projection_version=request.projection_version,
            profile=effective_profile,
            descriptor=descriptor,
            lane_family=lane_family,
        )
        current_state = get_projection_build_state(
            projection_id=request.projection_id,
            projection_version=request.projection_version,
            lane_family=lane_family,
            profile_id=effective_profile.id,
            path=metadata_store_path,
        )
        if current_state is None:
            current_state = ProjectionBuildState(
                projection_id=request.projection_id,
                projection_version=request.projection_version,
                profile_id=effective_profile.id,
                lane_family=lane_family,
                target_backend=backend_name,
                status="absent",
            )
        status_snapshot.append(current_state)
        current_status = current_state.status

        profile_build_enabled = bool(effective_profile.implemented or effective_profile.id == "sqlite_fts5_dense_sidecar_local_v1")
        if support_state in {"supported", "degraded"} and profile_build_enabled and writer.implemented:
            mode = "rebuild" if current_status in {"absent", "failed", "stale"} or len(invalidated_by) > 0 else "noop"
            notes = "Projection build path is implemented on the current deployment profile."
        elif support_state in {"supported", "degraded"} and profile_build_enabled and not writer.implemented:
            mode = writer.mode
            notes = writer.notes or "Projection writer is not yet implemented for this profile."
        else:
            mode = "planned"
            notes = "Declared contract only; execution path is not yet implemented for this lane/profile."

        actions.append(
            ProjectionRefreshAction(
                projection_descriptor_id=descriptor.projection_id,
                lane_family=lane_family,
                record_schema={
                    "lexical": "LexicalProjectionRecord",
                    "dense": "DenseProjectionRecord",
                    "sparse": "SparseProjectionRecord",
                    "graph": "GraphProjectionRecord",
                }.get(lane_family, descriptor.record_schema),
                adapter_backend=backend_name,
                writer_id=writer.writer_id,
                writer_implemented=writer.implemented,
                implemented=bool(profile_build_enabled and support_state in {"supported", "degraded"}),
                support_state=support_state,
                mode=mode,
                current_status=current_status,
                invalidated_by=list(invalidated_by),
                notes=notes,
            )
        )

    return ProjectionRefreshPlan(
        profile_id=effective_profile.id,
        projection_id=request.projection_id,
        projection_version=request.projection_version,
        projection_descriptor=descriptor.to_payload(),
        actions=actions,
        status_snapshot=status_snapshot,
        metadata={
            "authority_reference": build_authority_reference(request, descriptor=descriptor).model_dump(),
            "projection_target": build_projection_materialization_target(
                projection_id=request.projection_id,
                projection_version=request.projection_version,
                authority_reference=build_authority_reference(request, descriptor=descriptor),
                target_backend_name=next(
                    (
                        action.adapter_backend
                        for action in actions
                        if action.lane_family == descriptor.lane_family
                    ),
                    "unknown",
                ),
                metadata={"profile_id": effective_profile.id},
                descriptor=descriptor,
            ).model_dump(),
            "collection_ids": list(request.collection_ids),
            "document_ids": list(request.document_ids),
            "segment_ids": list(request.segment_ids),
            "request_metadata": dict(request.metadata or {}),
        },
    )


def explain_projection_refresh_plan(
    request: ProjectionRefreshRequest,
    *,
    profile: Optional[DeploymentProfile] = None,
    metadata_store_path: Optional[str] = None,
) -> ProjectionPlanExplain:
    plan = build_projection_refresh_plan(request, profile=profile, metadata_store_path=metadata_store_path)
    return ProjectionPlanExplain(
        profile_id=plan.profile_id,
        projection_id=plan.projection_id,
        projection_version=plan.projection_version,
        descriptor=dict(plan.projection_descriptor),
        actions=[action.model_dump() for action in plan.actions],
        status_snapshot=[state.model_dump() for state in plan.status_snapshot],
        metadata=dict(plan.metadata),
    )


def default_bootstrap_projection_ids(
    *,
    profile: Optional[DeploymentProfile] = None,
) -> List[str]:
    effective_profile = profile or get_deployment_profile()
    return list(PROFILE_BOOTSTRAP_PROJECTION_IDS.get(effective_profile.id, []))


def execute_projection_refresh_plan(
    plan: ProjectionRefreshPlan,
    *,
    database: Optional["Session"] = None,
    metadata_store_path: Optional[str] = None,
) -> ProjectionRefreshExecutionReport:
    executed_actions: List[ProjectionRefreshAction] = []
    skipped_actions: List[ProjectionRefreshAction] = []
    now_ts = time.time()

    for action in plan.actions:
        if action.mode == "rebuild" and action.implemented and action.writer_implemented:
            writer_runtime = get_projection_writer_runtime(
                resolve_projection_writer(
                    plan.projection_id,
                    projection_version=plan.projection_version,
                    profile=DEPLOYMENT_PROFILES[plan.profile_id],
                    descriptor=get_projection_descriptor(plan.projection_id),
                    lane_family=action.lane_family,
                )
            )
            writer_execution = writer_runtime.execute(
                database=database,
                projection_id=plan.projection_id,
                projection_version=plan.projection_version,
                lane_family=action.lane_family,
                adapter_backend=action.adapter_backend,
                authority_reference=dict(plan.metadata.get("authority_reference") or {}),
                request_metadata=dict(plan.metadata.get("request_metadata") or {}),
                invalidated_by=list(action.invalidated_by),
            )
            build_revision = writer_execution.build_revision or f"{plan.projection_version}:{action.lane_family}"
            common_metadata = {
                "projection_descriptor_id": action.projection_descriptor_id,
                **dict(writer_execution.metadata or {}),
            }
            try:
                mark_projection_build_started(
                    projection_id=plan.projection_id,
                    projection_version=plan.projection_version,
                    profile_id=plan.profile_id,
                    lane_family=action.lane_family,
                    target_backend=action.adapter_backend,
                    build_revision=build_revision,
                    metadata=common_metadata,
                    path=metadata_store_path,
                )
                mark_projection_build_ready(
                    projection_id=plan.projection_id,
                    projection_version=plan.projection_version,
                    profile_id=plan.profile_id,
                    lane_family=action.lane_family,
                    target_backend=action.adapter_backend,
                    build_revision=build_revision,
                    metadata=common_metadata,
                    path=metadata_store_path,
                )
                executed_actions.append(action)
            except Exception as exc:  # pragma: no cover - defensive
                mark_projection_build_failed(
                    projection_id=plan.projection_id,
                    projection_version=plan.projection_version,
                    profile_id=plan.profile_id,
                    lane_family=action.lane_family,
                    target_backend=action.adapter_backend,
                    build_revision=build_revision,
                    error_summary=str(exc),
                    metadata=common_metadata,
                    path=metadata_store_path,
                )
                raise
        else:
            skipped_actions.append(action)

    return ProjectionRefreshExecutionReport(
        profile_id=plan.profile_id,
        projection_id=plan.projection_id,
        executed_actions=executed_actions,
        skipped_actions=skipped_actions,
        metadata={"projection_version": plan.projection_version},
    )


def bootstrap_profile_projections(
    *,
    database: Optional["Session"] = None,
    profile: Optional[DeploymentProfile] = None,
    projection_ids: Optional[List[str]] = None,
    metadata_store_path: Optional[str] = None,
    request_metadata: Optional[Dict[str, Any]] = None,
) -> ProjectionBootstrapReport:
    effective_profile = profile or get_deployment_profile()
    effective_projection_ids = list(projection_ids or default_bootstrap_projection_ids(profile=effective_profile))
    executed_actions: List[Dict[str, Any]] = []
    skipped_actions: List[Dict[str, Any]] = []
    projection_items: List[ProjectionBootstrapItem] = []
    lifecycle_outcome_counts: Dict[str, int] = {}
    materialized_projection_ids: List[str] = []
    refreshed_projection_ids: List[str] = []
    recovered_failed_projection_ids: List[str] = []
    unchanged_ready_projection_ids: List[str] = []
    not_buildable_projection_ids: List[str] = []

    for projection_id in effective_projection_ids:
        descriptor = get_projection_descriptor(projection_id)
        materialization_target = build_projection_materialization_target(
            projection_id=projection_id,
            projection_version="v1",
            authority_reference=ProjectionAuthorityReference(
                authority_model=descriptor.authority_model,
                metadata={
                    "bootstrap_profile": effective_profile.id,
                    **dict(request_metadata or {}),
                },
            ),
            target_backend_name=getattr(
                effective_profile.backend_stack,
                LANE_TO_BACKEND_ATTR.get(descriptor.lane_family, ""),
                "unknown",
            ),
            metadata={"profile_id": effective_profile.id},
            descriptor=descriptor,
        )
        status_before_state = get_projection_build_state(
            projection_id=projection_id,
            projection_version="v1",
            lane_family=descriptor.lane_family,
            profile_id=effective_profile.id,
            path=metadata_store_path,
        )
        status_before = status_before_state.status if status_before_state is not None else "absent"
        plan = build_projection_refresh_plan(
            ProjectionRefreshRequest(
                projection_id=projection_id,
                projection_version="v1",
                lane_families=[descriptor.lane_family],
                metadata={
                    "bootstrap_profile": effective_profile.id,
                    **dict(request_metadata or {}),
                },
            ),
            profile=effective_profile,
            metadata_store_path=metadata_store_path,
        )
        action = plan.actions[0] if len(plan.actions) > 0 else None
        item_error_summary: Optional[str] = None
        item_executed_actions: List[Dict[str, Any]] = []
        item_skipped_actions: List[Dict[str, Any]] = []
        try:
            report = execute_projection_refresh_plan(
                plan,
                database=database,
                metadata_store_path=metadata_store_path,
            )
            item_executed_actions = [entry.model_dump() for entry in report.executed_actions]
            item_skipped_actions = [entry.model_dump() for entry in report.skipped_actions]
            executed_actions.extend(item_executed_actions)
            skipped_actions.extend(item_skipped_actions)
        except Exception as exc:
            item_error_summary = str(exc)
        state = get_projection_build_state(
            projection_id=projection_id,
            projection_version="v1",
            lane_family=descriptor.lane_family,
            profile_id=effective_profile.id,
            path=metadata_store_path,
        )
        if state is None and item_error_summary is not None and action is not None:
            state = mark_projection_build_failed(
                projection_id=projection_id,
                projection_version="v1",
                profile_id=effective_profile.id,
                lane_family=descriptor.lane_family,
                target_backend=action.adapter_backend,
                build_revision=f"v1:{descriptor.lane_family}",
                error_summary=item_error_summary,
                metadata={
                    "projection_descriptor_id": descriptor.projection_id,
                    "bootstrap_profile": effective_profile.id,
                    **dict(request_metadata or {}),
                },
                path=metadata_store_path,
            )
        runtime_executable = bool(action is not None and action.implemented and action.writer_implemented)
        status_after = state.status if state is not None else "absent"
        lifecycle_outcome = _classify_bootstrap_lifecycle_outcome(
            status_before=status_before,
            status_after=status_after,
            runtime_executable=runtime_executable,
            executed_action_count=len(item_executed_actions),
            error_summary=(item_error_summary or (state.error_summary if state is not None else None)),
        )
        lifecycle_outcome_counts[lifecycle_outcome] = lifecycle_outcome_counts.get(lifecycle_outcome, 0) + 1
        if lifecycle_outcome == "materialized_from_absent":
            materialized_projection_ids.append(projection_id)
        elif lifecycle_outcome == "refreshed_from_stale":
            refreshed_projection_ids.append(projection_id)
        elif lifecycle_outcome == "recovered_from_failed":
            recovered_failed_projection_ids.append(projection_id)
        elif lifecycle_outcome == "unchanged_ready":
            unchanged_ready_projection_ids.append(projection_id)
        elif lifecycle_outcome == "not_buildable":
            not_buildable_projection_ids.append(projection_id)

        projection_items.append(
            ProjectionBootstrapItem(
                projection_id=projection_id,
                projection_version="v1",
                lane_family=descriptor.lane_family,
                target_backend=(action.adapter_backend if action is not None else getattr(effective_profile.backend_stack, LANE_TO_BACKEND_ATTR.get(descriptor.lane_family, ''), 'unknown')),
                status_before=status_before,
                status_after=status_after,
                executed_action_count=len(item_executed_actions),
                skipped_action_count=len(item_skipped_actions),
                build_revision=(state.last_build_revision if state is not None else None),
                runtime_executable=runtime_executable,
                support_state=(action.support_state if action is not None else "unsupported"),
                lifecycle_outcome=lifecycle_outcome,
                error_summary=(item_error_summary or (state.error_summary if state is not None else None)),
                materialization_target=materialization_target.model_dump(),
                projection_plan_v2=(
                    build_local_projection_build_ir_v2(
                        projection_id,
                        profile=effective_profile,
                        support_state=(action.support_state if action is not None else "unsupported"),
                        action_mode=(action.mode if action is not None else "noop"),
                        build_status=status_after,
                    )
                    if effective_profile.id == "sqlite_fts5_dense_sidecar_local_v1"
                    else {}
                ),
                metadata={
                    "projection_descriptor_id": descriptor.projection_id,
                    "authority_model": descriptor.authority_model,
                    "record_schema": descriptor.record_schema,
                    "source_scope": descriptor.source_scope,
                    "target_backend_family": descriptor.target_backend_family,
                },
            )
        )

    ready_projection_ids: List[str] = []
    building_projection_ids: List[str] = []
    stale_projection_ids: List[str] = []
    failed_projection_ids: List[str] = []
    absent_projection_ids: List[str] = []
    for item in projection_items:
        if item.status_after == "ready":
            ready_projection_ids.append(item.projection_id)
        elif item.status_after == "building":
            building_projection_ids.append(item.projection_id)
        elif item.status_after == "stale":
            stale_projection_ids.append(item.projection_id)
        elif item.status_after == "failed":
            failed_projection_ids.append(item.projection_id)
        else:
            absent_projection_ids.append(item.projection_id)

    return ProjectionBootstrapReport(
        profile_id=effective_profile.id,
        projection_ids=effective_projection_ids,
        projection_items=projection_items,
        executed_actions=executed_actions,
        skipped_actions=skipped_actions,
        ready_projection_ids=ready_projection_ids,
        building_projection_ids=building_projection_ids,
        stale_projection_ids=stale_projection_ids,
        failed_projection_ids=failed_projection_ids,
        absent_projection_ids=absent_projection_ids,
        metadata={
            "projection_count": len(effective_projection_ids),
            "ready_count": len(ready_projection_ids),
            "building_count": len(building_projection_ids),
            "stale_count": len(stale_projection_ids),
            "failed_count": len(failed_projection_ids),
            "absent_count": len(absent_projection_ids),
            "executed_action_count": len(executed_actions),
            "skipped_action_count": len(skipped_actions),
            "lifecycle_outcome_counts": lifecycle_outcome_counts,
            "materialized_projection_ids": materialized_projection_ids,
            "refreshed_projection_ids": refreshed_projection_ids,
            "recovered_failed_projection_ids": recovered_failed_projection_ids,
            "unchanged_ready_projection_ids": unchanged_ready_projection_ids,
            "not_buildable_projection_ids": not_buildable_projection_ids,
            "metadata_store_path": str(_metadata_store_path(metadata_store_path)),
        },
    )


def build_projection_diagnostics_payload(
    *,
    profile: Optional[DeploymentProfile] = None,
    metadata_store_path: Optional[str] = None,
) -> Dict[str, Any]:
    effective_profile = profile or get_deployment_profile()
    capability_map = effective_profile.capability_map()
    items: List[ProjectionDiagnosticItem] = []

    lane_capability_ids = {
        "lexical": "retrieval.lexical.bm25",
        "dense": "retrieval.dense.vector",
        "sparse": "retrieval.sparse.vector",
        "graph": "retrieval.graph.traversal",
    }

    for descriptor in list_projection_descriptors().values():
        lane_family = descriptor.lane_family
        capability_id = lane_capability_ids.get(lane_family)
        capability = capability_map.get(capability_id) if capability_id else None
        support_state = capability.support_state if capability is not None else "unsupported"
        backend_attr = LANE_TO_BACKEND_ATTR.get(lane_family)
        backend_name = getattr(effective_profile.backend_stack, backend_attr, "unknown") if backend_attr else "unknown"

        request = ProjectionRefreshRequest(
            projection_id=descriptor.projection_id,
            projection_version="v1",
            lane_families=[lane_family],
        )
        plan = build_projection_refresh_plan(
            request,
            profile=effective_profile,
            metadata_store_path=metadata_store_path,
        )
        action = plan.actions[0]
        build_state = get_projection_build_state(
            projection_id=descriptor.projection_id,
            projection_version="v1",
            lane_family=lane_family,
            profile_id=effective_profile.id,
            path=metadata_store_path,
        )
        materialization_target = build_projection_materialization_target(
            projection_id=descriptor.projection_id,
            projection_version="v1",
            authority_reference=ProjectionAuthorityReference(
                authority_model=descriptor.authority_model,
                metadata={"profile_id": effective_profile.id},
            ),
            target_backend_name=backend_name,
            metadata={"profile_id": effective_profile.id},
            descriptor=descriptor,
        )
        items.append(
            ProjectionDiagnosticItem(
                projection_id=descriptor.projection_id,
                projection_version="v1",
                lane_family=lane_family,
                authority_model=descriptor.authority_model,
                source_scope=descriptor.source_scope,
                record_schema=descriptor.record_schema,
                target_backend_family=descriptor.target_backend_family,
                backend_name=backend_name,
                support_state=support_state,
                executable=bool(action.implemented and action.writer_implemented),
                build_status=build_state.status if build_state is not None else "absent",
                action_mode=action.mode,
                invalidated_by=list(action.invalidated_by),
                notes=descriptor.notes,
                materialization_target=materialization_target.model_dump(),
                build_state=build_state.model_dump() if build_state is not None else {},
            )
        )

    executable_count = sum(1 for item in items if item.executable)
    support_counts: Dict[str, int] = {}
    build_counts: Dict[str, int] = {}
    for item in items:
        support_counts[item.support_state] = support_counts.get(item.support_state, 0) + 1
        build_counts[item.build_status] = build_counts.get(item.build_status, 0) + 1

    return ProjectionDiagnosticsSummary(
        profile_id=effective_profile.id,
        projection_items=items,
        metadata={
            "projection_count": len(items),
            "executable_count": executable_count,
            "planned_or_unavailable_count": len(items) - executable_count,
            "support_state_counts": support_counts,
            "build_status_counts": build_counts,
        },
    ).model_dump()

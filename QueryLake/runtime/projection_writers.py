from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, Optional, Protocol, runtime_checkable

if TYPE_CHECKING:
    from sqlmodel import Session

from QueryLake.runtime.db_compat import DeploymentProfile, get_deployment_profile
from QueryLake.runtime.projection_registry import ProjectionDescriptor, get_projection_descriptor


@dataclass(frozen=True)
class ProjectionWriterResolution:
    projection_id: str
    projection_version: str
    profile_id: str
    lane_family: str
    writer_id: str
    backend: str
    implemented: bool
    support_state: str
    mode: str
    notes: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        return {
            "projection_id": self.projection_id,
            "projection_version": self.projection_version,
            "profile_id": self.profile_id,
            "lane_family": self.lane_family,
            "writer_id": self.writer_id,
            "backend": self.backend,
            "implemented": self.implemented,
            "support_state": self.support_state,
            "mode": self.mode,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class ProjectionWriterExecution:
    writer_id: str
    implemented: bool
    mode: str
    build_revision: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    notes: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        return {
            "writer_id": self.writer_id,
            "implemented": self.implemented,
            "mode": self.mode,
            "build_revision": self.build_revision,
            "metadata": dict(self.metadata or {}),
            "notes": self.notes,
        }


@runtime_checkable
class ProjectionWriterRuntime(Protocol):
    writer_id: str
    implemented: bool
    support_state: str
    mode: str

    def execute(
        self,
        *,
        database: Optional["Session"],
        projection_id: str,
        projection_version: str,
        lane_family: str,
        adapter_backend: str,
        authority_reference: Dict[str, Any],
        request_metadata: Dict[str, Any],
        invalidated_by: list[str],
    ) -> ProjectionWriterExecution: ...


@dataclass(frozen=True)
class GoldProjectionWriter:
    writer_id: str
    support_state: str
    mode: str = "rebuild"
    implemented: bool = True

    def execute(
        self,
        *,
        database: Optional["Session"],
        projection_id: str,
        projection_version: str,
        lane_family: str,
        adapter_backend: str,
        authority_reference: Dict[str, Any],
        request_metadata: Dict[str, Any],
        invalidated_by: list[str],
    ) -> ProjectionWriterExecution:
        build_revision = f"{projection_version}:{lane_family}"
        return ProjectionWriterExecution(
            writer_id=self.writer_id,
            implemented=True,
            mode=self.mode,
            build_revision=build_revision,
            metadata={
                "projection_id": projection_id,
                "projection_version": projection_version,
                "lane_family": lane_family,
                "adapter_backend": adapter_backend,
                "authority_reference": dict(authority_reference or {}),
                "request_metadata": dict(request_metadata or {}),
                "invalidated_by": list(invalidated_by),
            },
            notes="Gold profile projection writer executed locally.",
        )


@dataclass(frozen=True)
class PlaceholderProjectionWriter:
    writer_id: str
    support_state: str
    mode: str
    implemented: bool = False
    notes: Optional[str] = None

    def execute(
        self,
        *,
        database: Optional["Session"],
        projection_id: str,
        projection_version: str,
        lane_family: str,
        adapter_backend: str,
        authority_reference: Dict[str, Any],
        request_metadata: Dict[str, Any],
        invalidated_by: list[str],
    ) -> ProjectionWriterExecution:
        return ProjectionWriterExecution(
            writer_id=self.writer_id,
            implemented=False,
            mode=self.mode,
            build_revision=None,
            metadata={
                "projection_id": projection_id,
                "projection_version": projection_version,
                "lane_family": lane_family,
                "adapter_backend": adapter_backend,
                "authority_reference": dict(authority_reference or {}),
                "request_metadata": dict(request_metadata or {}),
                "invalidated_by": list(invalidated_by),
            },
            notes=self.notes,
        )


def _lane_capability_id(lane_family: str) -> str:
    return {
        "lexical": "retrieval.lexical.bm25",
        "dense": "retrieval.dense.vector",
        "sparse": "retrieval.sparse.vector",
        "graph": "retrieval.graph.traversal",
    }.get(lane_family, "")


def _lane_backend_name(profile: DeploymentProfile, lane_family: str) -> str:
    attr = {
        "lexical": "lexical",
        "dense": "dense",
        "sparse": "sparse",
        "graph": "graph",
    }.get(lane_family)
    if attr is None:
        return "unknown"
    return getattr(profile.backend_stack, attr, "unknown")


def resolve_projection_writer(
    projection_id: str,
    *,
    projection_version: str = "v1",
    profile: Optional[DeploymentProfile] = None,
    descriptor: Optional[ProjectionDescriptor] = None,
    lane_family: Optional[str] = None,
) -> ProjectionWriterResolution:
    effective_profile = profile or get_deployment_profile()
    effective_descriptor = descriptor or get_projection_descriptor(projection_id)
    effective_lane_family = lane_family or effective_descriptor.lane_family
    backend_name = _lane_backend_name(effective_profile, effective_lane_family)
    capability_id = _lane_capability_id(effective_lane_family)
    capability = effective_profile.capability_map().get(capability_id)
    support_state = capability.support_state if capability is not None else "unsupported"

    if effective_profile.id == "sqlite_fts5_dense_sidecar_local_v1":
        if projection_id in {
            "document_chunk_lexical_projection_v1",
            "file_chunk_lexical_projection_v1",
        } and effective_lane_family == "lexical":
            return ProjectionWriterResolution(
                projection_id=projection_id,
                projection_version=projection_version,
                profile_id=effective_profile.id,
                lane_family=effective_lane_family,
                writer_id=f"sqlite_local.projection_writer.lexical.{projection_id}.v1",
                backend=backend_name,
                implemented=support_state in {"supported", "degraded"},
                support_state=support_state,
                mode="local_materialize" if support_state in {"supported", "degraded"} else "planned_scaffold",
                notes="Local SQLite FTS5 lexical projection materialization is available as a local build scaffold.",
            )
        if projection_id == "document_chunk_dense_projection_v1" and effective_lane_family == "dense":
            return ProjectionWriterResolution(
                projection_id=projection_id,
                projection_version=projection_version,
                profile_id=effective_profile.id,
                lane_family=effective_lane_family,
                writer_id="sqlite_local.projection_writer.dense.document_chunk.v1",
                backend=backend_name,
                implemented=support_state in {"supported", "degraded"},
                support_state=support_state,
                mode="local_materialize" if support_state in {"supported", "degraded"} else "planned_scaffold",
                notes="Local dense-sidecar projection materialization is available as a local build scaffold.",
            )
        return ProjectionWriterResolution(
            projection_id=projection_id,
            projection_version=projection_version,
            profile_id=effective_profile.id,
            lane_family=effective_lane_family,
            writer_id=f"sqlite_local.projection_writer.{effective_lane_family}.{projection_id}.v1",
            backend=backend_name,
            implemented=False,
            support_state=support_state,
            mode="planned_scaffold",
            notes="No executable local projection writer is implemented for this projection yet.",
        )

    if not effective_profile.implemented:
        return ProjectionWriterResolution(
            projection_id=projection_id,
            projection_version=projection_version,
            profile_id=effective_profile.id,
            lane_family=effective_lane_family,
            writer_id=f"placeholder.projection_writer.{projection_id}.{effective_profile.id}",
            backend=backend_name,
            implemented=False,
            support_state=support_state,
            mode="planned",
            notes="Profile is declared but not implemented.",
        )

    if effective_profile.id == "paradedb_postgres_gold_v1":
        return ProjectionWriterResolution(
            projection_id=projection_id,
            projection_version=projection_version,
            profile_id=effective_profile.id,
            lane_family=effective_lane_family,
            writer_id=f"gold.projection_writer.{effective_lane_family}.v1",
            backend=backend_name,
            implemented=support_state == "supported",
            support_state=support_state,
            mode="rebuild" if support_state == "supported" else "planned",
            notes="Gold profile uses the co-located SQL/projection stack.",
        )

    if effective_profile.id == "aws_aurora_pg_opensearch_v1":
        if projection_id in {
            "document_chunk_lexical_projection_v1",
            "file_chunk_lexical_projection_v1",
            "segment_lexical_projection_v1",
        } and effective_lane_family == "lexical":
            return ProjectionWriterResolution(
                projection_id=projection_id,
                projection_version=projection_version,
                profile_id=effective_profile.id,
                lane_family=effective_lane_family,
                writer_id=f"opensearch.projection_writer.lexical.{projection_id}.v1",
                backend=backend_name,
                implemented=support_state == "supported",
                support_state=support_state,
                mode="rebuild" if support_state == "supported" else "planned",
                notes="Split-stack lexical compatibility projection writer is implemented for OpenSearch.",
            )
        if projection_id == "document_chunk_dense_projection_v1" and effective_lane_family == "dense":
            return ProjectionWriterResolution(
                projection_id=projection_id,
                projection_version=projection_version,
                profile_id=effective_profile.id,
                lane_family=effective_lane_family,
                writer_id="opensearch.projection_writer.dense.document_chunk.v1",
                backend=backend_name,
                implemented=support_state == "supported",
                support_state=support_state,
                mode="rebuild" if support_state == "supported" else "planned",
                notes="Split-stack dense compatibility projection writer is implemented for OpenSearch document-chunk projections.",
            )
        if projection_id == "segment_dense_projection_v1" and effective_lane_family == "dense":
            return ProjectionWriterResolution(
                projection_id=projection_id,
                projection_version=projection_version,
                profile_id=effective_profile.id,
                lane_family=effective_lane_family,
                writer_id="opensearch.projection_writer.dense.segment.v1",
                backend=backend_name,
                implemented=support_state == "supported",
                support_state=support_state,
                mode="rebuild" if support_state == "supported" else "planned",
                notes="Canonical dense segment projection writer is implemented for the first OpenSearch split-stack slice.",
            )
        return ProjectionWriterResolution(
            projection_id=projection_id,
            projection_version=projection_version,
            profile_id=effective_profile.id,
            lane_family=effective_lane_family,
            writer_id=f"placeholder.projection_writer.{effective_lane_family}.aws_aurora_pg_opensearch_v1",
            backend=backend_name,
            implemented=False,
            support_state=support_state,
            mode="external_writer_unavailable" if support_state in {"supported", "degraded"} else "planned",
            notes="Split-stack projection writers are not implemented yet for this profile.",
        )

    return ProjectionWriterResolution(
        projection_id=projection_id,
        projection_version=projection_version,
        profile_id=effective_profile.id,
        lane_family=effective_lane_family,
        writer_id=f"placeholder.projection_writer.{effective_lane_family}.{effective_profile.id}",
        backend=backend_name,
        implemented=False,
        support_state=support_state,
        mode="planned",
        notes="No projection writer is implemented for this profile.",
    )


def get_projection_writer_runtime(
    resolution: ProjectionWriterResolution,
) -> ProjectionWriterRuntime:
    if resolution.profile_id == "sqlite_fts5_dense_sidecar_local_v1":
        from QueryLake.runtime.local_projection_writers import get_sqlite_local_projection_writer

        return get_sqlite_local_projection_writer(
            projection_id=resolution.projection_id,
            lane_family=resolution.lane_family,
        )
    if (
        resolution.profile_id == "aws_aurora_pg_opensearch_v1"
        and resolution.implemented
        and resolution.mode == "rebuild"
        and resolution.lane_family in {"lexical", "dense"}
        and resolution.projection_id in {
            "document_chunk_lexical_projection_v1",
            "file_chunk_lexical_projection_v1",
            "segment_lexical_projection_v1",
            "document_chunk_dense_projection_v1",
            "segment_dense_projection_v1",
        }
    ):
        from QueryLake.runtime.opensearch_projection_writers import (
            get_opensearch_dense_projection_writer,
            get_opensearch_lexical_projection_writer,
        )
        if resolution.lane_family == "dense":
            return get_opensearch_dense_projection_writer(
                projection_id=resolution.projection_id,
            )
        return get_opensearch_lexical_projection_writer(
            projection_id=resolution.projection_id,
        )
    if resolution.implemented and resolution.mode == "rebuild":
        return GoldProjectionWriter(
            writer_id=resolution.writer_id,
            support_state=resolution.support_state,
            mode=resolution.mode,
        )
    return PlaceholderProjectionWriter(
        writer_id=resolution.writer_id,
        support_state=resolution.support_state,
        mode=resolution.mode,
        notes=resolution.notes,
    )

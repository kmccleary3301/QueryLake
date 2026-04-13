from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from QueryLake.runtime.authority_projection_access import build_projection_materialization_target
from QueryLake.runtime.local_dense_sidecar import LOCAL_DENSE_SIDECAR_ADAPTER
from QueryLake.runtime.projection_writers import ProjectionWriterExecution


@dataclass(frozen=True)
class SQLiteLocalProjectionWriter:
    writer_id: str
    support_state: str
    mode: str = "local_materialize"
    implemented: bool = True
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
        metadata = {
            "projection_id": projection_id,
            "projection_version": projection_version,
            "lane_family": lane_family,
            "adapter_backend": adapter_backend,
            "authority_reference": dict(authority_reference or {}),
            "request_metadata": dict(request_metadata or {}),
            "invalidated_by": list(invalidated_by),
        }
        if lane_family == "dense" and adapter_backend == "local_dense_sidecar" and database is not None:
            target = build_projection_materialization_target(
                projection_id=projection_id,
                projection_version=projection_version,
                authority_reference=dict(authority_reference or {}),
                target_backend_name=adapter_backend,
                metadata={
                    "profile_id": str(request_metadata.get("profile_id") or ""),
                    "runtime_family": "local_profile_v2",
                    "writer_id": self.writer_id,
                },
            )
            index = LOCAL_DENSE_SIDECAR_ADAPTER.warm_projection(database, target=target)
            metadata["dense_sidecar"] = {
                "cache_warmed": True,
                "cache_key": index.cache_key,
                "record_count": int(index.record_count),
                "embedding_dimension": int(index.embedding_dimension),
            }
        return ProjectionWriterExecution(
            writer_id=self.writer_id,
            implemented=True,
            mode=self.mode,
            build_revision=f"{projection_version}:{lane_family}:local",
            metadata=metadata,
            notes=self.notes
            or "Local SQLite profile projection writer scaffold is declared but not implemented yet.",
        )


def get_sqlite_local_projection_writer(*, projection_id: str, lane_family: str) -> SQLiteLocalProjectionWriter:
    return SQLiteLocalProjectionWriter(
        writer_id=f"sqlite_local.projection_writer.{lane_family}.{projection_id}.v1",
        support_state="degraded" if lane_family == "lexical" else "supported",
        mode="local_materialize",
        notes=(
            "Local SQLite FTS5 + dense-sidecar projection materialization is implemented as a local metadata/build scaffold. "
            "This marks projection state and provides the target seam for future executable local retrieval."
        ),
    )

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Sequence
import math

from sqlmodel import Session

from QueryLake.runtime.authority_projection_access import fetch_projection_materialization_records
from QueryLake.runtime.projection_contracts import DocumentChunkMaterializationRecord, ProjectionMaterializationTarget


@dataclass(frozen=True)
class LocalDenseSidecarContract:
    adapter_id: str
    storage_contract_version: str
    lifecycle_contract_version: str
    execution_mode: str
    storage_mode: str
    persistence_scope: str
    durability_level: str
    artifact_layout: tuple[str, ...]
    cache_model: str
    cache_scope: str
    shared_across_processes: bool
    warmup_mode: str
    rebuild_strategy: str
    query_mode: str
    readiness_contract: str
    promotion_contract: str
    lifecycle_states: tuple[str, ...]
    cache_lifecycle_states: tuple[str, ...]
    ready_state_sources: tuple[str, ...]
    stats_sources: tuple[str, ...]
    lifecycle_recovery_modes: tuple[str, ...]
    docs_ref: str = "docs/database/LOCAL_DENSE_SIDECAR_CONTRACT.md"

    def payload(self) -> Dict[str, Any]:
        return {
            "adapter_id": self.adapter_id,
            "storage_contract_version": self.storage_contract_version,
            "lifecycle_contract_version": self.lifecycle_contract_version,
            "execution_mode": self.execution_mode,
            "storage_mode": self.storage_mode,
            "persistence_scope": self.persistence_scope,
            "durability_level": self.durability_level,
            "artifact_layout": list(self.artifact_layout),
            "cache_model": self.cache_model,
            "cache_scope": self.cache_scope,
            "shared_across_processes": bool(self.shared_across_processes),
            "warmup_mode": self.warmup_mode,
            "rebuild_strategy": self.rebuild_strategy,
            "query_mode": self.query_mode,
            "readiness_contract": self.readiness_contract,
            "promotion_contract": self.promotion_contract,
            "lifecycle_states": list(self.lifecycle_states),
            "cache_lifecycle_states": list(self.cache_lifecycle_states),
            "ready_state_sources": list(self.ready_state_sources),
            "stats_sources": list(self.stats_sources),
            "lifecycle_recovery_modes": list(self.lifecycle_recovery_modes),
            "docs_ref": self.docs_ref,
        }


def normalize_dense_query_embedding(value: Sequence[float] | None) -> list[float]:
    if value is None:
        return []
    try:
        return [float(item) for item in value]
    except Exception:
        return []


def cosine_similarity(
    query_embedding: Sequence[float],
    candidate_embedding: Sequence[float],
) -> float:
    if not query_embedding or not candidate_embedding:
        return 0.0
    limit = min(len(query_embedding), len(candidate_embedding))
    if limit <= 0:
        return 0.0
    q = [float(query_embedding[i]) for i in range(limit)]
    c = [float(candidate_embedding[i]) for i in range(limit)]
    dot = sum(qv * cv for qv, cv in zip(q, c))
    q_norm = math.sqrt(sum(qv * qv for qv in q))
    c_norm = math.sqrt(sum(cv * cv for cv in c))
    if q_norm == 0.0 or c_norm == 0.0:
        return 0.0
    return dot / (q_norm * c_norm)


def rank_dense_records(
    records: Sequence[DocumentChunkMaterializationRecord],
    *,
    query_embedding: Sequence[float] | None,
    limit: int,
) -> list[tuple[DocumentChunkMaterializationRecord, float]]:
    normalized_query = normalize_dense_query_embedding(query_embedding)
    if not normalized_query:
        return []
    ranked = [
        (
            record,
            cosine_similarity(normalized_query, list(record.embedding or [])),
        )
        for record in records
    ]
    ranked = [item for item in ranked if item[1] > 0.0]
    ranked.sort(key=lambda item: (-item[1], str(item[0].id or "")))
    return ranked[: max(int(limit or 0), 0)]


@dataclass(frozen=True)
class LocalDenseSidecarIndex:
    cache_key: str
    projection_id: str
    record_count: int
    embedding_dimension: int
    records: tuple[DocumentChunkMaterializationRecord, ...]

    def stats_payload(self) -> Dict[str, Any]:
        return {
            "cache_key": self.cache_key,
            "projection_id": self.projection_id,
            "record_count": int(self.record_count),
            "embedding_dimension": int(self.embedding_dimension),
            "cache_warmed": True,
        }


def _target_cache_key(target: ProjectionMaterializationTarget) -> str:
    authority_reference = target.authority_reference
    collection_ids = ",".join(sorted(str(item) for item in list(authority_reference.collection_ids or []) if str(item)))
    document_ids = ",".join(sorted(str(item) for item in list(authority_reference.document_ids or []) if str(item)))
    segment_ids = ",".join(sorted(str(item) for item in list(authority_reference.segment_ids or []) if str(item)))
    return "|".join(
        [
            str(target.projection_id),
            str(target.source_scope),
            str(target.target_backend_name),
            collection_ids,
            document_ids,
            segment_ids,
        ]
    )


def _persisted_dense_sidecar_payload(value: Dict[str, Any] | None) -> Dict[str, Any]:
    payload = dict(value or {})
    return {
        "cache_warmed": bool(payload.get("cache_warmed")),
        "record_count": int(payload.get("record_count") or 0),
        "embedding_dimension": int(payload.get("embedding_dimension") or 0),
        "cache_key": str(payload.get("cache_key") or ""),
    }


@dataclass
class LocalDenseSidecarAdapter:
    adapter_id: str = "local_dense_sidecar_v1"
    storage_contract_version: str = "v1"
    lifecycle_contract_version: str = "v1"
    execution_mode: str = "projection_backed_process_local"
    storage_mode: str = "metadata_backed_projection_records"
    persistence_scope: str = "projection_build_state_plus_process_local_cache"
    durability_level: str = "rebuildable_metadata_backed"
    artifact_layout: tuple[str, ...] = (
        "projection_materialization_records",
        "projection_build_state.metadata.dense_sidecar",
        "process_local_index_registry",
    )
    cache_model: str = "process_local_index_registry"
    cache_scope: str = "process_local"
    shared_across_processes: bool = False
    warmup_mode: str = "projection_materialization_scan"
    rebuild_strategy: str = "projection_rescan_on_cache_cold_or_process_start"
    query_mode: str = "cosine_similarity_full_scan"
    readiness_contract: str = "projection_ready_and_executable"
    promotion_contract: str = "projection_ready_with_runtime_contract_and_build_metadata"
    lifecycle_states: tuple[str, ...] = (
        "blocked_projection_not_ready",
        "blocked_adapter_not_executable",
        "ready_projection_backed_cache_cold",
        "ready_cache_warmed",
    )
    cache_lifecycle_states: tuple[str, ...] = (
        "projection_not_ready",
        "adapter_not_executable",
        "cache_cold_rebuildable",
        "cache_warmed_process_local",
        "cache_warmed_persisted_metadata",
    )
    ready_state_sources: tuple[str, ...] = (
        "not_ready",
        "projection_build_status",
        "process_local_cache",
        "persisted_projection_build_state",
    )
    stats_sources: tuple[str, ...] = (
        "cache_cold",
        "process_local_cache",
        "persisted_projection_build_state",
        "cache_error",
    )
    lifecycle_recovery_modes: tuple[str, ...] = (
        "bootstrap_required_projection",
        "restore_runtime_adapter_executability",
        "warm_process_local_cache_from_projection_records",
        "none",
    )
    _index_registry: Dict[str, LocalDenseSidecarIndex] | None = None

    def __post_init__(self) -> None:
        if self._index_registry is None:
            self._index_registry = {}

    def reset(self) -> None:
        self._index_registry = {}

    def contract(self) -> LocalDenseSidecarContract:
        return LocalDenseSidecarContract(
            adapter_id=self.adapter_id,
            storage_contract_version=self.storage_contract_version,
            lifecycle_contract_version=self.lifecycle_contract_version,
            execution_mode=self.execution_mode,
            storage_mode=self.storage_mode,
            persistence_scope=self.persistence_scope,
            durability_level=self.durability_level,
            artifact_layout=self.artifact_layout,
            cache_model=self.cache_model,
            cache_scope=self.cache_scope,
            shared_across_processes=self.shared_across_processes,
            warmup_mode=self.warmup_mode,
            rebuild_strategy=self.rebuild_strategy,
            query_mode=self.query_mode,
            readiness_contract=self.readiness_contract,
            promotion_contract=self.promotion_contract,
            lifecycle_states=self.lifecycle_states,
            cache_lifecycle_states=self.cache_lifecycle_states,
            ready_state_sources=self.ready_state_sources,
            stats_sources=self.stats_sources,
            lifecycle_recovery_modes=self.lifecycle_recovery_modes,
        )

    def lifecycle_recovery_payload(
        self,
        *,
        projection_id: str,
        build_status: str,
        executable: bool,
        requiring_route_ids: Sequence[str],
        cache_warmed: bool,
        persisted_projection_state_available: bool,
    ) -> Dict[str, Any]:
        route_ids = [str(item) for item in list(requiring_route_ids or []) if str(item)]
        if str(build_status) != "ready":
            return {
                "recovery_mode": "bootstrap_required_projection",
                "warmup_recommended": False,
                "warmup_required_for_peak_performance": False,
                "cold_start_recoverable": False,
                "cache_persistence_mode": self.persistence_scope,
                "warmup_target_route_ids": [],
                "warmup_command_hint": None,
                "recovery_hints": [f"bootstrap_projection:{projection_id}"],
            }
        if not bool(executable):
            return {
                "recovery_mode": "restore_runtime_adapter_executability",
                "warmup_recommended": False,
                "warmup_required_for_peak_performance": False,
                "cold_start_recoverable": False,
                "cache_persistence_mode": self.persistence_scope,
                "warmup_target_route_ids": [],
                "warmup_command_hint": None,
                "recovery_hints": ["restore_dense_sidecar_adapter_executability"],
            }
        if not bool(cache_warmed):
            return {
                "recovery_mode": "warm_process_local_cache_from_projection_records",
                "warmup_recommended": True,
                "warmup_required_for_peak_performance": True,
                "cold_start_recoverable": True,
                "cache_persistence_mode": self.persistence_scope,
                "warmup_target_route_ids": route_ids,
                "warmup_command_hint": (
                    "Run a local hybrid query or "
                    "scripts/db_compat_local_dense_sidecar_lifecycle_smoke.py "
                    "--enable-ready-profile-projections"
                ),
                "recovery_hints": (
                    [
                        "warm_process_local_dense_sidecar_cache",
                        (
                            "persisted_projection_state_available"
                            if persisted_projection_state_available
                            else "projection_records_rebuildable"
                        ),
                    ]
                ),
            }
        return {
            "recovery_mode": "none",
            "warmup_recommended": False,
            "warmup_required_for_peak_performance": False,
            "cold_start_recoverable": True,
            "cache_persistence_mode": self.persistence_scope,
            "warmup_target_route_ids": route_ids,
            "warmup_command_hint": None,
            "recovery_hints": [],
        }

    def runtime_blockers(
        self,
        *,
        build_status: str,
        executable: bool,
    ) -> list[str]:
        blockers: list[str] = []
        if str(build_status) != "ready":
            blockers.append("projection_not_ready")
        if not bool(executable):
            blockers.append("adapter_not_executable")
        return blockers

    def promotion_blockers(
        self,
        *,
        build_status: str,
        executable: bool,
        cache_warmed: bool,
    ) -> list[str]:
        _ = cache_warmed
        return list(self.runtime_blockers(build_status=build_status, executable=executable))

    def inspect_target_with_persisted_state(
        self,
        target: ProjectionMaterializationTarget,
        *,
        persisted_dense_sidecar: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        runtime_stats = self.inspect_target(target)
        if bool(runtime_stats.get("cache_warmed")):
            return {
                **runtime_stats,
                "ready_state_source": "process_local_cache",
            }
        persisted_stats = _persisted_dense_sidecar_payload(persisted_dense_sidecar)
        if persisted_stats["cache_warmed"] or persisted_stats["record_count"] > 0 or persisted_stats["embedding_dimension"] > 0:
            return {
                **persisted_stats,
                "cache_key": persisted_stats["cache_key"] or str(runtime_stats.get("cache_key") or ""),
                "stats_source": "persisted_projection_build_state",
                "ready_state_source": "persisted_projection_build_state",
            }
        return {
            **runtime_stats,
            "ready_state_source": "cache_cold",
        }

    def status_payload(
        self,
        *,
        projection_id: str,
        build_status: str,
        executable: bool,
        requiring_route_ids: Sequence[str],
        materialization_target: Dict[str, Any] | None = None,
        persisted_dense_sidecar: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        ready = str(build_status) == "ready" and bool(executable)
        stats: Dict[str, Any] = {
            "cache_warmed": False,
            "record_count": 0,
            "embedding_dimension": 0,
            "cache_key": "",
            "stats_source": "cache_cold",
            "ready_state_source": "cache_cold",
        }
        try:
            if materialization_target:
                target = ProjectionMaterializationTarget.model_validate(materialization_target)
                stats = self.inspect_target_with_persisted_state(
                    target,
                    persisted_dense_sidecar=persisted_dense_sidecar,
                )
        except Exception:
            stats = {
                "cache_warmed": False,
                "record_count": 0,
                "embedding_dimension": 0,
                "cache_key": "",
                "stats_source": "cache_error",
                "ready_state_source": "cache_error",
            }
        runtime_blockers = self.runtime_blockers(
            build_status=str(build_status),
            executable=bool(executable),
        )
        promotion_blockers = self.promotion_blockers(
            build_status=str(build_status),
            executable=bool(executable),
            cache_warmed=bool(stats.get("cache_warmed")),
        )
        lifecycle_state = "blocked_projection_not_ready"
        if str(build_status) == "ready" and bool(executable):
            lifecycle_state = (
                "ready_cache_warmed"
                if bool(stats.get("cache_warmed"))
                else "ready_projection_backed_cache_cold"
            )
        elif str(build_status) == "ready" and not bool(executable):
            lifecycle_state = "blocked_adapter_not_executable"
        cache_lifecycle_state = "projection_not_ready"
        if str(build_status) == "ready" and not bool(executable):
            cache_lifecycle_state = "adapter_not_executable"
        elif ready:
            stats_source = str(stats.get("stats_source") or "")
            if bool(stats.get("cache_warmed")) and stats_source == "process_local_cache":
                cache_lifecycle_state = "cache_warmed_process_local"
            elif bool(stats.get("cache_warmed")) and stats_source == "persisted_projection_build_state":
                cache_lifecycle_state = "cache_warmed_persisted_metadata"
            else:
                cache_lifecycle_state = "cache_cold_rebuildable"
        rebuildable_from_projection_records = bool(str(build_status) == "ready" and bool(executable))
        requires_process_warmup = bool(rebuildable_from_projection_records and not bool(stats.get("cache_warmed")))
        persisted_projection_state_available = bool(
            str(stats.get("stats_source") or "") == "persisted_projection_build_state"
        )
        lifecycle_recovery = self.lifecycle_recovery_payload(
            projection_id=projection_id,
            build_status=str(build_status),
            executable=bool(executable),
            requiring_route_ids=requiring_route_ids,
            cache_warmed=bool(stats.get("cache_warmed")),
            persisted_projection_state_available=persisted_projection_state_available,
        )
        ready_state_source = str(stats.get("ready_state_source") or "")
        if ready:
            if ready_state_source not in {
                "process_local_cache",
                "persisted_projection_build_state",
            }:
                ready_state_source = "projection_build_status"
        else:
            ready_state_source = "not_ready"
        return {
            "adapter_id": self.adapter_id,
            "projection_id": projection_id,
            "backend_name": "local_dense_sidecar",
            "execution_mode": self.execution_mode,
            "storage_mode": self.storage_mode,
            "build_status": str(build_status),
            "executable": bool(executable),
            "ready": ready,
            "runtime_contract_ready": ready,
            "promotion_contract_ready": ready,
            "ready_state_source": ready_state_source,
            "lifecycle_state": lifecycle_state,
            "cache_lifecycle_state": cache_lifecycle_state,
            "rebuildable_from_projection_records": rebuildable_from_projection_records,
            "requires_process_warmup": requires_process_warmup,
            "persisted_projection_state_available": persisted_projection_state_available,
            "cache_persistence_mode": str(lifecycle_recovery.get("cache_persistence_mode") or self.persistence_scope),
            "cold_start_recoverable": bool(lifecycle_recovery.get("cold_start_recoverable")),
            "warmup_recommended": bool(lifecycle_recovery.get("warmup_recommended")),
            "warmup_required_for_peak_performance": bool(
                lifecycle_recovery.get("warmup_required_for_peak_performance")
            ),
            "warmup_target_route_ids": list(lifecycle_recovery.get("warmup_target_route_ids") or []),
            "warmup_command_hint": lifecycle_recovery.get("warmup_command_hint"),
            "lifecycle_recovery_mode": str(lifecycle_recovery.get("recovery_mode") or "none"),
            "lifecycle_recovery_hints": list(lifecycle_recovery.get("recovery_hints") or []),
            "runtime_blockers": runtime_blockers,
            "promotion_blockers": promotion_blockers,
            "requiring_route_ids": [str(item) for item in list(requiring_route_ids or []) if str(item)],
            "materialization_target": dict(materialization_target or {}),
            "contract": self.contract().payload(),
            **{key: value for key, value in stats.items() if key != "ready_state_source"},
        }

    def inspect_target(self, target: ProjectionMaterializationTarget) -> Dict[str, Any]:
        cache_key = _target_cache_key(target)
        index = dict(self._index_registry or {}).get(cache_key)
        if index is None:
            return {
                "cache_warmed": False,
                "record_count": 0,
                "embedding_dimension": 0,
                "cache_key": cache_key,
                "stats_source": "cache_cold",
            }
        payload = index.stats_payload()
        payload["stats_source"] = "process_local_cache"
        return payload

    def warm_projection(
        self,
        database: Session,
        *,
        target: ProjectionMaterializationTarget,
    ) -> LocalDenseSidecarIndex:
        records = list(fetch_projection_materialization_records(database, target=target))
        embedding_dimension = 0
        for record in records:
            values = list(record.embedding or [])
            if values:
                embedding_dimension = len(values)
                break
        index = LocalDenseSidecarIndex(
            cache_key=_target_cache_key(target),
            projection_id=str(target.projection_id),
            record_count=len(records),
            embedding_dimension=embedding_dimension,
            records=tuple(records),
        )
        assert self._index_registry is not None
        self._index_registry[index.cache_key] = index
        return index

    def search(
        self,
        records: Sequence[DocumentChunkMaterializationRecord],
        *,
        query_embedding: Sequence[float] | None,
        limit: int,
    ) -> list[tuple[DocumentChunkMaterializationRecord, float]]:
        return rank_dense_records(records, query_embedding=query_embedding, limit=limit)

    def search_projection(
        self,
        database: Session,
        *,
        target: ProjectionMaterializationTarget,
        query_embedding: Sequence[float] | None,
        limit: int,
    ) -> list[tuple[DocumentChunkMaterializationRecord, float]]:
        cache_key = _target_cache_key(target)
        index = dict(self._index_registry or {}).get(cache_key)
        if index is None:
            index = self.warm_projection(database, target=target)
        return self.search(index.records, query_embedding=query_embedding, limit=limit)


LOCAL_DENSE_SIDECAR_ADAPTER = LocalDenseSidecarAdapter()

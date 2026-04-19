from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class CanonTraceSummary:
    available: bool
    retention_class: str
    execution_mode: str
    span_model: str

    def to_payload(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CanonReplaySummary:
    available: bool
    retention_class: str
    replay_guarantee_class: str
    bundle_version: str

    def to_payload(self) -> dict[str, object]:
        return asdict(self)


def build_trace_summary(*, retention_class: str, execution_mode: str) -> CanonTraceSummary:
    return CanonTraceSummary(
        available=True,
        retention_class=retention_class,
        execution_mode=execution_mode,
        span_model="phase1a_bridge_compile_only",
    )


def build_replay_summary(*, retention_class: str, replay_guarantee_class: str) -> CanonReplaySummary:
    return CanonReplaySummary(
        available=retention_class in {"debug_replay", "incident_replay"},
        retention_class=retention_class,
        replay_guarantee_class=replay_guarantee_class,
        bundle_version="phase1a.bridge.v1",
    )

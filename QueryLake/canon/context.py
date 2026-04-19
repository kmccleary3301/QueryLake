from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import time
import uuid


class ExecutionMode(str, Enum):
    LEGACY_PIPELINE = "legacy_pipeline"
    CANON_SHADOW = "canon_shadow"
    CANON_PRIMARY = "canon_primary"


class TracePolicy(str, Enum):
    DISABLED = "disabled"
    SUMMARY = "summary"
    DETAIL = "detail"


@dataclass(slots=True)
class CancellationToken:
    cancelled: bool = False
    reason: str | None = None

    def cancel(self, reason: str | None = None) -> None:
        self.cancelled = True
        self.reason = reason


@dataclass(slots=True)
class ExecutionContext:
    request_id: str = field(default_factory=lambda: f"canon-{uuid.uuid4().hex}")
    mode: ExecutionMode = ExecutionMode.CANON_SHADOW
    deadline_unix_ms: int | None = None
    cancellation: CancellationToken = field(default_factory=CancellationToken)
    trace_policy: TracePolicy = TracePolicy.SUMMARY
    created_unix_ms: int = field(default_factory=lambda: int(time.time() * 1000))

    def check_open(self) -> None:
        if self.cancellation.cancelled:
            raise RuntimeError(self.cancellation.reason or "Execution cancelled")
        if self.deadline_unix_ms is not None and int(time.time() * 1000) > self.deadline_unix_ms:
            raise TimeoutError("Execution deadline exceeded")

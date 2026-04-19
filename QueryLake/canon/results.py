from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .context import ExecutionMode
from .effects import EffectClass


@dataclass(slots=True)
class NodeExecutionResult:
    node_id: str
    operation: str
    effect_class: EffectClass
    status: str
    dependency_node_ids: tuple[str, ...] = field(default_factory=tuple)
    input_keys: tuple[str, ...] = field(default_factory=tuple)
    output_names: tuple[str, ...] = field(default_factory=tuple)
    output_count: int = 0
    duration_ms: float = 0.0
    error: str | None = None
    failure_classification: str | None = None
    memoized: bool = False


@dataclass(slots=True)
class ExecutionSummary:
    graph_id: str
    execution_mode: ExecutionMode
    requested_output_keys: tuple[str, ...]
    total_nodes_defined: int
    executed_node_ids: tuple[str, ...]
    node_results: tuple[NodeExecutionResult, ...]
    total_duration_ms: float = 0.0
    memoized_reads: int = 0
    failed_node_id: str | None = None
    failure_classification: str | None = None


@dataclass(slots=True)
class ExecutionResult:
    graph_id: str
    outputs: dict[str, Any]
    summary: ExecutionSummary

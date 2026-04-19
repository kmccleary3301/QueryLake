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
    output_names: tuple[str, ...] = field(default_factory=tuple)
    error: str | None = None
    memoized: bool = False


@dataclass(slots=True)
class ExecutionSummary:
    graph_id: str
    execution_mode: ExecutionMode
    requested_output_keys: tuple[str, ...]
    total_nodes_defined: int
    executed_node_ids: tuple[str, ...]
    node_results: tuple[NodeExecutionResult, ...]


@dataclass(slots=True)
class ExecutionResult:
    graph_id: str
    outputs: dict[str, Any]
    summary: ExecutionSummary

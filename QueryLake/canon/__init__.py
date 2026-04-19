"""Canon++ Phase 1A minimal execution scaffold."""

from .context import CancellationToken, ExecutionCancelledError, ExecutionContext, ExecutionMode, TracePolicy
from .effects import EffectClass
from .executor import CanonExecutionError, CanonExecutor
from .models import GraphSpec, NodeSpec, OutputRef
from .results import ExecutionResult, ExecutionSummary, NodeExecutionResult

__all__ = [
    "CancellationToken",
    "CanonExecutionError",
    "CanonExecutor",
    "EffectClass",
    "ExecutionCancelledError",
    "ExecutionContext",
    "ExecutionMode",
    "ExecutionResult",
    "ExecutionSummary",
    "GraphSpec",
    "NodeExecutionResult",
    "NodeSpec",
    "OutputRef",
    "TracePolicy",
]

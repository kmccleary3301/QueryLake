"""Phase 1A runtime-facing Canon++ types and executor."""

from QueryLake.canon.context import CancellationToken, ExecutionContext, ExecutionMode, TracePolicy
from QueryLake.canon.executor import CanonExecutionError, CanonExecutor
from QueryLake.canon.results import ExecutionResult, ExecutionSummary, NodeExecutionResult
from .bridge_metadata import build_canon_bridge_metadata
from .replay_bundle import build_shadow_replay_bundle, persist_shadow_replay_bundle
from .shadow_harness import build_request_from_shadow_case, execute_shadow_case
from .shadow_index import build_shadow_report_index, load_shadow_reports, persist_shadow_report_index
from .shadow_reports import build_shadow_execution_report, persist_shadow_execution_report
from .trace_export import build_shadow_trace_export, persist_shadow_trace_export
from .querylake_shadow import build_querylake_shadow_diff, execute_querylake_pipeline_in_canon_shadow
from .summaries import CanonReplaySummary, CanonTraceSummary, build_replay_summary, build_trace_summary
from .shadow_diff import build_shadow_diff_summary

__all__ = [
    "build_request_from_shadow_case",
    "build_shadow_replay_bundle",
    "build_shadow_trace_export",
    "build_shadow_execution_report",
    "build_shadow_report_index",
    "build_querylake_shadow_diff",
    "build_replay_summary",
    "build_shadow_diff_summary",
    "execute_querylake_pipeline_in_canon_shadow",
    "execute_shadow_case",
    "build_trace_summary",
    "CancellationToken",
    "build_canon_bridge_metadata",
    "CanonExecutionError",
    "CanonReplaySummary",
    "CanonTraceSummary",
    "CanonExecutor",
    "ExecutionContext",
    "ExecutionMode",
    "ExecutionResult",
    "ExecutionSummary",
    "load_shadow_reports",
    "NodeExecutionResult",
    "persist_shadow_execution_report",
    "persist_shadow_report_index",
    "persist_shadow_replay_bundle",
    "persist_shadow_trace_export",
    "TracePolicy",
]

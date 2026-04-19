"""Phase 1A runtime-facing Canon++ types and executor."""

from QueryLake.canon.context import (
    CancellationToken,
    ExecutionCancelledError,
    ExecutionContext,
    ExecutionMode,
    TracePolicy,
)
from QueryLake.canon.executor import CanonExecutionError, CanonExecutor
from QueryLake.canon.results import ExecutionResult, ExecutionSummary, NodeExecutionResult
from .bridge_metadata import build_canon_bridge_metadata
from .bootstrap_bundle import build_phase1a_bootstrap_bundle
from .replay_bundle import build_shadow_replay_bundle, persist_shadow_replay_bundle
from .exit_readiness import build_phase1a_exit_readiness_bundle
from .profile_readiness import (
    build_phase1a_profile_readiness_bundle,
    build_phase1a_projection_writer_matrix,
    build_phase1a_search_plane_a_transition_bundle,
)
from .shadow_catalog import (
    apply_shadow_retention_plan,
    build_shadow_artifact_catalog,
    build_shadow_retention_plan,
    load_shadow_artifacts,
    persist_shadow_artifact_catalog,
    persist_shadow_retention_plan,
)
from .shadow_harness import build_request_from_shadow_case, execute_shadow_case, persist_shadow_harness_catalog
from .shadow_index import build_shadow_report_index, load_shadow_reports, persist_shadow_report_index
from .search_plane_a_execution import (
    build_search_plane_a_execution_contract,
    resolve_search_plane_a_execution_contract,
)
from .shadow_matrix import build_phase1a_route_profile_matrix
from .shadow_reports import build_shadow_execution_report, persist_shadow_execution_report
from .trace_export import build_shadow_trace_export, persist_shadow_trace_export
from .querylake_shadow import build_querylake_shadow_diff, execute_querylake_pipeline_in_canon_shadow
from .summaries import CanonReplaySummary, CanonTraceSummary, build_replay_summary, build_trace_summary
from .shadow_diff import build_shadow_diff_summary

__all__ = [
    "build_request_from_shadow_case",
    "build_phase1a_route_profile_matrix",
    "build_phase1a_exit_readiness_bundle",
    "build_phase1a_profile_readiness_bundle",
    "build_phase1a_projection_writer_matrix",
    "build_phase1a_search_plane_a_transition_bundle",
    "build_search_plane_a_execution_contract",
    "build_shadow_replay_bundle",
    "build_shadow_artifact_catalog",
    "build_shadow_trace_export",
    "build_shadow_execution_report",
    "build_shadow_report_index",
    "build_shadow_retention_plan",
    "build_querylake_shadow_diff",
    "build_replay_summary",
    "build_shadow_diff_summary",
    "execute_querylake_pipeline_in_canon_shadow",
    "execute_shadow_case",
    "build_trace_summary",
    "CancellationToken",
    "build_canon_bridge_metadata",
    "build_phase1a_bootstrap_bundle",
    "CanonExecutionError",
    "CanonReplaySummary",
    "CanonTraceSummary",
    "CanonExecutor",
    "ExecutionContext",
    "ExecutionCancelledError",
    "ExecutionMode",
    "ExecutionResult",
    "ExecutionSummary",
    "load_shadow_artifacts",
    "load_shadow_reports",
    "NodeExecutionResult",
    "resolve_search_plane_a_execution_contract",
    "apply_shadow_retention_plan",
    "persist_shadow_artifact_catalog",
    "persist_shadow_harness_catalog",
    "persist_shadow_execution_report",
    "persist_shadow_report_index",
    "persist_shadow_retention_plan",
    "persist_shadow_replay_bundle",
    "persist_shadow_trace_export",
    "TracePolicy",
]

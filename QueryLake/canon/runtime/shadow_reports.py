from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from QueryLake.typing.retrieval_primitives import RetrievalCandidate, RetrievalExecutionResult, RetrievalPipelineSpec, RetrievalRequest


def _candidate_ids(candidates: Sequence[RetrievalCandidate], *, limit: int | None = None) -> list[str]:
    rows = candidates if limit is None else candidates[:limit]
    return [str(candidate.content_id) for candidate in rows]


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def build_shadow_execution_report(
    *,
    report_id: str,
    request: RetrievalRequest,
    pipeline: RetrievalPipelineSpec,
    profile_id: str,
    legacy_result: RetrievalExecutionResult,
    canon_result: RetrievalExecutionResult,
    shadow_diff: Mapping[str, Any],
    top_k_snapshot: int = 10,
) -> dict[str, Any]:
    bridge = dict(canon_result.metadata.get("canon_bridge") or {})
    graph_id = str(canon_result.metadata.get("canon_graph_id") or bridge.get("graph_id") or "")

    return {
        "schema_version": "canon_shadow_report_v1",
        "report_id": str(report_id),
        "generated_at": _utc_now(),
        "route": str(request.query_ir_v2.get("route_id") or request.route or ""),
        "query_text": request.query_text,
        "profile_id": str(profile_id),
        "pipeline": {
            "pipeline_id": pipeline.pipeline_id,
            "pipeline_version": pipeline.version,
            "stage_ids": [stage.stage_id for stage in pipeline.stages if stage.enabled],
        },
        "bridge": bridge,
        "shadow_diff": dict(shadow_diff),
        "legacy": {
            "candidate_count": len(legacy_result.candidates),
            "candidate_ids_top_k": _candidate_ids(legacy_result.candidates, limit=top_k_snapshot),
            "trace_count": len(legacy_result.traces),
        },
        "canon": {
            "candidate_count": len(canon_result.candidates),
            "candidate_ids_top_k": _candidate_ids(canon_result.candidates, limit=top_k_snapshot),
            "trace_count": len(canon_result.traces),
            "graph_id": graph_id,
        },
        "trace_summary": bridge.get("trace_summary"),
        "replay_summary": bridge.get("replay_summary"),
    }


def persist_shadow_execution_report(
    *,
    report: Mapping[str, Any],
    output_dir: str | Path,
) -> dict[str, Any]:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    report_id = str(report.get("report_id") or "canon-shadow-report")
    path = target_dir / f"{report_id}.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "report_id": report_id,
        "path": str(path),
    }

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from QueryLake.typing.retrieval_primitives import RetrievalExecutionResult, RetrievalPipelineSpec, RetrievalRequest


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def build_shadow_trace_export(
    *,
    export_id: str,
    request: RetrievalRequest,
    pipeline: RetrievalPipelineSpec,
    canon_result: RetrievalExecutionResult,
) -> dict[str, Any]:
    graph_id = str(canon_result.metadata.get("canon_graph_id") or "")
    return {
        "schema_version": "canon_shadow_trace_export_v1",
        "export_id": str(export_id),
        "generated_at": _utc_now(),
        "route": str(request.query_ir_v2.get("route_id") or request.route or ""),
        "pipeline_id": pipeline.pipeline_id,
        "pipeline_version": pipeline.version,
        "graph_id": graph_id,
        "trace_count": len(canon_result.traces),
        "spans": [
            {
                "name": trace.stage,
                "duration_ms": trace.duration_ms,
                "input_count": trace.input_count,
                "output_count": trace.output_count,
                "attributes": dict(trace.details or {}),
            }
            for trace in canon_result.traces
        ],
    }


def persist_shadow_trace_export(
    *,
    export: dict[str, Any],
    output_dir: str | Path,
) -> dict[str, Any]:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    export_id = str(export.get("export_id") or "canon-shadow-trace-export")
    path = target_dir / f"{export_id}.json"
    path.write_text(json.dumps(export, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "export_id": export_id,
        "path": str(path),
    }

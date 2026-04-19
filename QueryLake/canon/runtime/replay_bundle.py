from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from QueryLake.typing.retrieval_primitives import RetrievalExecutionResult, RetrievalPipelineSpec, RetrievalRequest


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def build_shadow_replay_bundle(
    *,
    bundle_id: str,
    request: RetrievalRequest,
    pipeline: RetrievalPipelineSpec,
    legacy_result: RetrievalExecutionResult,
    canon_result: RetrievalExecutionResult,
    shadow_diff: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "canon_shadow_replay_bundle_v1",
        "bundle_id": str(bundle_id),
        "generated_at": _utc_now(),
        "route": str(request.query_ir_v2.get("route_id") or request.route or ""),
        "query_text": request.query_text,
        "pipeline_id": pipeline.pipeline_id,
        "pipeline_version": pipeline.version,
        "graph_id": str(canon_result.metadata.get("canon_graph_id") or ""),
        "legacy_candidate_ids": [str(candidate.content_id) for candidate in legacy_result.candidates],
        "canon_candidate_ids": [str(candidate.content_id) for candidate in canon_result.candidates],
        "shadow_diff": dict(shadow_diff),
        "bridge": dict(canon_result.metadata.get("canon_bridge") or {}),
    }


def persist_shadow_replay_bundle(
    *,
    bundle: Mapping[str, Any],
    output_dir: str | Path,
) -> dict[str, Any]:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    bundle_id = str(bundle.get("bundle_id") or "canon-shadow-replay-bundle")
    path = target_dir / f"{bundle_id}.json"
    path.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "bundle_id": bundle_id,
        "path": str(path),
    }

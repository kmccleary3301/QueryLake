from __future__ import annotations

import json
from pathlib import Path
from typing import Awaitable, Callable, Dict, Optional

from sqlmodel import Session

from QueryLake.runtime.retrieval_experiments import log_experiment_run
from QueryLake.typing.retrieval_primitives import RetrievalExecutionResult


def summarize_execution(result: RetrievalExecutionResult) -> Dict[str, float]:
    total_latency_seconds = sum((trace.duration_ms or 0.0) for trace in result.traces) / 1000.0
    return {
        "results_count": float(len(result.candidates)),
        "latency_seconds": float(total_latency_seconds),
        "trace_count": float(len(result.traces)),
    }


def _candidate_ids(result: RetrievalExecutionResult, *, top_k: int = 10) -> list[str]:
    return [str(candidate.content_id) for candidate in result.candidates[:top_k]]


def build_shadow_comparison_summary(
    baseline: RetrievalExecutionResult,
    candidate: RetrievalExecutionResult,
    *,
    top_k: int = 10,
) -> Dict[str, object]:
    baseline_ids = _candidate_ids(baseline, top_k=top_k)
    candidate_ids = _candidate_ids(candidate, top_k=top_k)
    baseline_set = set(baseline_ids)
    candidate_set = set(candidate_ids)
    if baseline_ids == candidate_ids:
        divergence_class = "exact_match"
    elif baseline_set == candidate_set:
        divergence_class = "ordering_delta_only"
    else:
        divergence_class = "candidate_set_delta"
    return {
        "schema_version": "retrieval_shadow_comparison_summary_v1",
        "divergence_class": divergence_class,
        "top_k": int(top_k),
        "baseline_candidate_ids": baseline_ids,
        "candidate_candidate_ids": candidate_ids,
        "baseline_only_ids": sorted(baseline_set - candidate_set),
        "candidate_only_ids": sorted(candidate_set - baseline_set),
    }


def persist_shadow_comparison_summary(
    *,
    summary: Dict[str, object],
    output_dir: str | Path,
    comparison_id: str,
) -> Dict[str, str]:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"{comparison_id}.json"
    path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "comparison_id": comparison_id,
        "path": str(path),
    }


async def run_shadow_mode(
    *,
    baseline_executor: Callable[[], Awaitable[RetrievalExecutionResult]],
    candidate_executor: Callable[[], Awaitable[RetrievalExecutionResult]],
    publish_result: str = "baseline",
    database: Optional[Session] = None,
    experiment_id: Optional[str] = None,
    query_text: str = "",
    query_hash: Optional[str] = None,
    baseline_run_id: Optional[str] = None,
    candidate_run_id: Optional[str] = None,
    comparison_output_dir: Optional[str] = None,
    comparison_id: Optional[str] = None,
    comparison_top_k: int = 10,
) -> Dict[str, object]:
    assert publish_result in {"baseline", "candidate"}, "publish_result must be baseline or candidate"
    baseline = await baseline_executor()
    candidate = await candidate_executor()

    baseline_metrics = summarize_execution(baseline)
    candidate_metrics = summarize_execution(candidate)
    comparison_summary = build_shadow_comparison_summary(
        baseline,
        candidate,
        top_k=comparison_top_k,
    )
    comparison_ref = None

    if database is not None and experiment_id is not None:
        published_pipeline_id = baseline.pipeline_id if publish_result == "baseline" else candidate.pipeline_id
        published_pipeline_version = baseline.pipeline_version if publish_result == "baseline" else candidate.pipeline_version
        log_experiment_run(
            database,
            experiment_id=experiment_id,
            query_text=query_text,
            query_hash=query_hash,
            baseline_run_id=baseline_run_id,
            candidate_run_id=candidate_run_id,
            baseline_metrics=baseline_metrics,
            candidate_metrics=candidate_metrics,
            publish_mode=publish_result,
            published_pipeline_id=published_pipeline_id,
            published_pipeline_version=published_pipeline_version,
        )

    if comparison_output_dir is not None:
        comparison_ref = persist_shadow_comparison_summary(
            summary=comparison_summary,
            output_dir=comparison_output_dir,
            comparison_id=comparison_id or f"retrieval-shadow-{publish_result}",
        )

    published = baseline if publish_result == "baseline" else candidate
    return {
        "published": published,
        "baseline": baseline,
        "candidate": candidate,
        "baseline_metrics": baseline_metrics,
        "candidate_metrics": candidate_metrics,
        "comparison_summary": comparison_summary,
        "comparison_ref": comparison_ref,
    }

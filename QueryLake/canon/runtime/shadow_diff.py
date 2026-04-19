from __future__ import annotations

from typing import Any, Iterable, Sequence

from QueryLake.typing.retrieval_primitives import RetrievalCandidate


def _candidate_ids(candidates: Iterable[RetrievalCandidate]) -> list[str]:
    return [str(candidate.content_id) for candidate in candidates]


def build_shadow_diff_summary(
    *,
    route_family: str,
    profile_id: str,
    execution_mode: str,
    legacy_candidates: Sequence[RetrievalCandidate],
    canon_candidates: Sequence[RetrievalCandidate],
    top_k_requested: int,
    legacy_plan_id: str,
    canon_graph_id: str,
    trace_summary_ref: str | None = None,
    replay_bundle_ref: str | None = None,
) -> dict[str, Any]:
    legacy_ids = _candidate_ids(legacy_candidates[:top_k_requested])
    canon_ids = _candidate_ids(canon_candidates[:top_k_requested])
    overlap = [candidate_id for candidate_id in legacy_ids if candidate_id in canon_ids]
    legacy_only = [candidate_id for candidate_id in legacy_ids if candidate_id not in canon_ids]
    canon_only = [candidate_id for candidate_id in canon_ids if candidate_id not in legacy_ids]

    if legacy_ids == canon_ids:
        divergence_class = "exact_match"
    elif set(legacy_ids) == set(canon_ids):
        divergence_class = "ordering_delta_only"
    elif legacy_only or canon_only:
        divergence_class = "candidate_set_delta"
    else:
        divergence_class = "analysis_incomplete"

    return {
        "route_family": route_family,
        "profile_id": profile_id,
        "execution_mode": execution_mode,
        "legacy_plan_id": legacy_plan_id,
        "canon_graph_id": canon_graph_id,
        "legacy_result_count": len(legacy_candidates),
        "canon_result_count": len(canon_candidates),
        "top_k_requested": int(top_k_requested),
        "overlap_at_k": len(overlap),
        "legacy_only_ids": legacy_only,
        "canon_only_ids": canon_only,
        "score_comparison_mode": "candidate_identity_only",
        "divergence_class": divergence_class,
        "trace_summary_ref": trace_summary_ref,
        "replay_bundle_ref": replay_bundle_ref,
    }

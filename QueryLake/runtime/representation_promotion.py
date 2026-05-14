from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class RepresentationPromotionThresholds:
    min_recall_against_baseline_at_k: float = 0.95
    max_latency_regression_ratio: float = 1.25
    max_fallback_rate: float = 0.05
    min_provenance_coverage: float = 0.98
    min_query_count: int = 10

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RepresentationPromotionDecision:
    representation_type: str
    promote: bool
    blockers: list[str]
    metrics: Dict[str, Any]
    thresholds: RepresentationPromotionThresholds

    def to_payload(self) -> Dict[str, Any]:
        return {
            "representation_type": self.representation_type,
            "promote": self.promote,
            "blockers": list(self.blockers),
            "metrics": dict(self.metrics),
            "thresholds": self.thresholds.to_payload(),
        }


def decide_representation_promotion(
    *,
    representation_type: str,
    metrics: Dict[str, Any],
    thresholds: RepresentationPromotionThresholds | None = None,
) -> RepresentationPromotionDecision:
    thresholds = thresholds or RepresentationPromotionThresholds()
    blockers: list[str] = []
    query_count = int(metrics.get("query_count", 0) or 0)
    recall_against_baseline_at_k = float(
        metrics.get("mean_recall_against_baseline_at_k", metrics.get("mean_overlap_at_k", 0.0)) or 0.0
    )
    overlap_at_k = float(metrics.get("mean_overlap_at_k", recall_against_baseline_at_k) or 0.0)
    latency_ratio = float(metrics.get("candidate_over_baseline_latency_ratio", 1.0) or 1.0)
    fallback_rate = float(metrics.get("fallback_rate", 0.0) or 0.0)
    provenance_coverage = float(metrics.get("provenance_coverage", 0.0) or 0.0)

    if query_count < thresholds.min_query_count:
        blockers.append("insufficient_query_count")
    if recall_against_baseline_at_k < thresholds.min_recall_against_baseline_at_k:
        blockers.append("recall_against_baseline_below_threshold")
    if latency_ratio > thresholds.max_latency_regression_ratio:
        blockers.append("latency_regression_above_threshold")
    if fallback_rate > thresholds.max_fallback_rate:
        blockers.append("fallback_rate_above_threshold")
    if provenance_coverage < thresholds.min_provenance_coverage:
        blockers.append("provenance_coverage_below_threshold")

    return RepresentationPromotionDecision(
        representation_type=str(representation_type),
        promote=len(blockers) == 0,
        blockers=blockers,
        metrics={
            "query_count": query_count,
            "mean_overlap_at_k": overlap_at_k,
            "mean_recall_against_baseline_at_k": recall_against_baseline_at_k,
            "candidate_over_baseline_latency_ratio": latency_ratio,
            "fallback_rate": fallback_rate,
            "provenance_coverage": provenance_coverage,
        },
        thresholds=thresholds,
    )

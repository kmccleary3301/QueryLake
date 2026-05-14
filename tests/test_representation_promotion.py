from QueryLake.runtime.representation_promotion import RepresentationPromotionThresholds, decide_representation_promotion


def test_representation_promotion_passes_when_thresholds_met():
    decision = decide_representation_promotion(
        representation_type="canonical_segment_text",
        metrics={
            "query_count": 20,
            "mean_overlap_at_k": 0.7,
            "mean_recall_against_baseline_at_k": 0.99,
            "candidate_over_baseline_latency_ratio": 1.05,
            "fallback_rate": 0.01,
            "provenance_coverage": 1.0,
        },
    )
    assert decision.promote is True
    assert decision.blockers == []


def test_representation_promotion_reports_all_blockers():
    decision = decide_representation_promotion(
        representation_type="canonical_segment_text",
        metrics={
            "query_count": 2,
            "mean_overlap_at_k": 0.2,
            "mean_recall_against_baseline_at_k": 0.2,
            "candidate_over_baseline_latency_ratio": 2.0,
            "fallback_rate": 0.5,
            "provenance_coverage": 0.5,
        },
        thresholds=RepresentationPromotionThresholds(min_query_count=10),
    )
    assert decision.promote is False
    assert decision.blockers == [
        "insufficient_query_count",
        "recall_against_baseline_below_threshold",
        "latency_regression_above_threshold",
        "fallback_rate_above_threshold",
        "provenance_coverage_below_threshold",
    ]

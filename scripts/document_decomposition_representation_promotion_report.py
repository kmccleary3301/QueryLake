#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.representation_promotion import RepresentationPromotionThresholds, decide_representation_promotion


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate representation-lane promotion thresholds from metric JSON.")
    parser.add_argument("--metrics", required=True)
    parser.add_argument("--representation-type", default="canonical_segment_text")
    parser.add_argument("--min-recall-against-baseline-at-k", type=float, default=0.95)
    parser.add_argument("--max-latency-regression-ratio", type=float, default=1.25)
    parser.add_argument("--max-fallback-rate", type=float, default=0.05)
    parser.add_argument("--min-provenance-coverage", type=float, default=0.98)
    parser.add_argument("--min-query-count", type=int, default=10)
    args = parser.parse_args()

    payload = json.loads(Path(args.metrics).read_text())
    metrics = payload.get("metrics", payload)
    thresholds = RepresentationPromotionThresholds(
        min_recall_against_baseline_at_k=args.min_recall_against_baseline_at_k,
        max_latency_regression_ratio=args.max_latency_regression_ratio,
        max_fallback_rate=args.max_fallback_rate,
        min_provenance_coverage=args.min_provenance_coverage,
        min_query_count=args.min_query_count,
    )
    decision = decide_representation_promotion(
        representation_type=args.representation_type,
        metrics=metrics,
        thresholds=thresholds,
    )
    print(json.dumps(decision.to_payload(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

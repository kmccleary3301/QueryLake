#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from QueryLake.scanning.evaluation import (
    ScannerEvalResult,
    ScannerPromotionThresholds,
    decide_backend_promotion,
    promotion_decisions_to_markdown,
)


def _load_results(path: Path):
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_results = payload.get("results", payload if isinstance(payload, list) else [])
    if not isinstance(raw_results, list):
        raise ValueError("promotion input must be a results list or an object with a 'results' list")
    return [ScannerEvalResult(**item) for item in raw_results]


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate scanner backend promotion thresholds from eval results JSON.")
    parser.add_argument("--results", required=True, help="JSON file containing ScannerEvalResult payloads.")
    parser.add_argument("--backend-id", action="append", default=[], help="Backend to evaluate. May be repeated.")
    parser.add_argument("--min-contract-pass-rate", type=float, default=1.0)
    parser.add_argument("--min-cases", type=int, default=1)
    parser.add_argument("--max-failure-count", type=int, default=0)
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    args = parser.parse_args()

    results = _load_results(Path(args.results))
    backend_ids = args.backend_id or sorted({result.backend_id for result in results})
    thresholds = ScannerPromotionThresholds(
        min_contract_pass_rate=args.min_contract_pass_rate,
        min_cases=args.min_cases,
        max_failure_count=args.max_failure_count,
    )
    decisions = [decide_backend_promotion(backend_id, results, thresholds) for backend_id in backend_ids]
    if args.format == "json":
        print(json.dumps({"decisions": [decision.to_payload() for decision in decisions]}, indent=2, sort_keys=True))
    else:
        print(promotion_decisions_to_markdown(decisions))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

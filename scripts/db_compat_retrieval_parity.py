#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List, Mapping


def topk_overlap_ratio(a: List[str], b: List[str], k: int) -> float:
    if k <= 0:
        return 0.0
    sa = set(a[:k])
    sb = set(b[:k])
    denom = max(1, len(sa))
    return len(sa & sb) / float(denom)


def reciprocal_rank(result_ids: List[str], expected_ids: Iterable[str]) -> float:
    expected = {str(v) for v in expected_ids}
    if not expected:
        return 0.0
    for idx, result_id in enumerate(result_ids):
        if str(result_id) in expected:
            return 1.0 / float(idx + 1)
    return 0.0


def _normalize_runs_payload(payload: object) -> Dict[str, List[str]]:
    if isinstance(payload, dict):
        normalized: Dict[str, List[str]] = {}
        for key, value in payload.items():
            if isinstance(value, list):
                normalized[str(key)] = [str(v) for v in value]
        return normalized
    if isinstance(payload, list):
        normalized = {}
        for entry in payload:
            if not isinstance(entry, dict):
                continue
            query = entry.get("query")
            retrieved_ids = entry.get("retrieved_ids")
            if isinstance(query, str) and isinstance(retrieved_ids, list):
                normalized[query] = [str(v) for v in retrieved_ids]
        return normalized
    return {}


def _normalize_latency_payload(payload: object) -> Dict[str, float]:
    if not isinstance(payload, dict):
        return {}
    out: Dict[str, float] = {}
    for key, value in payload.items():
        try:
            out[str(key)] = float(value)
        except Exception:
            continue
    return out


def load_cases(path: Path) -> List[Dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("cases-json must contain a JSON list")
    return [entry for entry in payload if isinstance(entry, dict)]


def load_route_thresholds(path: Path) -> Dict[str, Dict[str, float]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("route-thresholds-json must contain a JSON object")
    normalized: Dict[str, Dict[str, float]] = {}
    for route, value in payload.items():
        if not isinstance(route, str) or not isinstance(value, dict):
            continue
        normalized[route] = {
            "min_overlap": float(value.get("min_overlap", 0.0) or 0.0),
            "max_mrr_drop": float(value.get("max_mrr_drop", 1.0) or 1.0),
            "max_latency_ratio": float(value.get("max_latency_ratio", 9999.0) or 9999.0),
        }
    return normalized


def parity_metrics_from_cases(
    *,
    cases: List[Dict[str, Any]],
    gold_runs: Mapping[str, List[str]],
    split_runs: Mapping[str, List[str]],
    gold_latency_ms: Mapping[str, float],
    split_latency_ms: Mapping[str, float],
    k: int,
) -> Dict[str, Any]:
    per_query: List[Dict[str, Any]] = []
    route_metrics: Dict[str, Dict[str, float]] = {}
    overlap_scores: List[float] = []
    gold_rr_values: List[float] = []
    split_rr_values: List[float] = []
    latency_ratios: List[float] = []
    degraded_case_count = 0
    unsupported_case_count = 0

    for case in cases:
        query = str(case.get("query", "") or "")
        route = str(case.get("route", "") or "")
        case_id = str(case.get("case_id", "") or query)
        expected_ids = case.get("expected_ids", [])
        split_expected_state = str(case.get("split_expected_state", "supported") or "supported")
        min_overlap = float(case.get("min_overlap", 0.0) or 0.0)
        max_mrr_drop = float(case.get("max_mrr_drop", 1.0) or 1.0)
        max_latency_ratio = float(case.get("max_latency_ratio", 9999.0) or 9999.0)
        unsupported_expect_empty = bool(case.get("unsupported_expect_empty", True))
        if not isinstance(expected_ids, list):
            expected_ids = []
        if split_expected_state == "degraded":
            degraded_case_count += 1
        elif split_expected_state == "unsupported":
            unsupported_case_count += 1

        gold_results = list(gold_runs.get(query, []))
        split_results = list(split_runs.get(query, []))
        overlap_at_k = topk_overlap_ratio(gold_results, split_results, k)
        gold_rr = reciprocal_rank(gold_results, expected_ids)
        split_rr = reciprocal_rank(split_results, expected_ids)
        gold_latency = float(gold_latency_ms.get(query, 0.0) or 0.0)
        split_latency = float(split_latency_ms.get(query, 0.0) or 0.0)
        latency_ratio = 1.0 if gold_latency <= 0 else split_latency / float(gold_latency)

        if split_expected_state != "unsupported":
            overlap_scores.append(overlap_at_k)
            gold_rr_values.append(gold_rr)
            split_rr_values.append(split_rr)
            latency_ratios.append(latency_ratio)

        route_bucket = route_metrics.setdefault(
            route,
            {
                "case_count": 0.0,
                "degraded_case_count": 0.0,
                "unsupported_case_count": 0.0,
                "overlap_sum": 0.0,
                "gold_rr_sum": 0.0,
                "split_rr_sum": 0.0,
                "latency_ratio_sum": 0.0,
            },
        )
        route_bucket["case_count"] += 1.0
        if split_expected_state == "degraded":
            route_bucket["degraded_case_count"] += 1.0
        if split_expected_state == "unsupported":
            route_bucket["unsupported_case_count"] += 1.0
        else:
            route_bucket["overlap_sum"] += overlap_at_k
            route_bucket["gold_rr_sum"] += gold_rr
            route_bucket["split_rr_sum"] += split_rr
            route_bucket["latency_ratio_sum"] += latency_ratio
        failure_reasons: List[str] = []
        if split_expected_state == "unsupported":
            if unsupported_expect_empty and bool(split_results[:k]):
                failure_reasons.append("unsupported_case_returned_split_results")
        else:
            if overlap_at_k < min_overlap:
                failure_reasons.append("overlap_below_case_threshold")
            if (split_rr - gold_rr) < -max_mrr_drop:
                failure_reasons.append("mrr_drop_exceeds_case_threshold")
            if latency_ratio > max_latency_ratio:
                failure_reasons.append("latency_ratio_exceeds_case_threshold")

        per_query.append(
            {
                "case_id": case_id,
                "route": route,
                "query": query,
                "split_expected_state": split_expected_state,
                "thresholds": {
                    "min_overlap": min_overlap,
                    "max_mrr_drop": max_mrr_drop,
                    "max_latency_ratio": max_latency_ratio,
                },
                "expected_ids": [str(v) for v in expected_ids],
                "gold_topk": gold_results[:k],
                "split_topk": split_results[:k],
                "overlap_at_k": overlap_at_k,
                "gold_rr": gold_rr,
                "split_rr": split_rr,
                "gold_latency_ms": gold_latency,
                "split_latency_ms": split_latency,
                "latency_ratio": latency_ratio,
                "unsupported_expect_empty": unsupported_expect_empty,
                "passes_thresholds": len(failure_reasons) == 0,
                "failure_reasons": failure_reasons,
            }
        )

    gold_mrr = mean(gold_rr_values) if gold_rr_values else 0.0
    split_mrr = mean(split_rr_values) if split_rr_values else 0.0
    mean_overlap = mean(overlap_scores) if overlap_scores else 0.0
    mean_latency_ratio = mean(latency_ratios) if latency_ratios else 1.0

    route_metric_payload = {}
    for route, payload in route_metrics.items():
        executable_case_count = max(0.0, payload["case_count"] - payload["unsupported_case_count"])
        route_metric_payload[route] = {
            "case_count": int(payload["case_count"]),
            "degraded_case_count": int(payload["degraded_case_count"]),
            "unsupported_case_count": int(payload["unsupported_case_count"]),
            "topk_overlap_mean": (payload["overlap_sum"] / executable_case_count) if executable_case_count else 0.0,
            "gold_mrr": (payload["gold_rr_sum"] / executable_case_count) if executable_case_count else 0.0,
            "split_mrr": (payload["split_rr_sum"] / executable_case_count) if executable_case_count else 0.0,
            "mrr_delta": ((payload["split_rr_sum"] - payload["gold_rr_sum"]) / executable_case_count)
            if executable_case_count
            else 0.0,
            "latency_ratio_mean": (payload["latency_ratio_sum"] / executable_case_count)
            if executable_case_count
            else 1.0,
        }

    return {
        "query_count": len(cases),
        "k": int(k),
        "topk_overlap_mean": mean_overlap,
        "gold_mrr": gold_mrr,
        "split_mrr": split_mrr,
        "mrr_delta": split_mrr - gold_mrr,
        "latency_ratio_mean": mean_latency_ratio,
        "degraded_case_count": degraded_case_count,
        "unsupported_case_count": unsupported_case_count,
        "route_metrics": route_metric_payload,
        "per_query": per_query,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Fixture-driven gold-vs-split-stack retrieval parity harness.")
    parser.add_argument("--cases-json", required=True)
    parser.add_argument("--gold-runs-json", required=True)
    parser.add_argument("--split-runs-json", required=True)
    parser.add_argument("--gold-latency-json", default=None)
    parser.add_argument("--split-latency-json", default=None)
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--route-thresholds-json", default=None)
    parser.add_argument("--min-overlap", type=float, default=0.0)
    parser.add_argument("--max-mrr-drop", type=float, default=1.0)
    parser.add_argument("--max-latency-ratio", type=float, default=9999.0)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    cases = load_cases(Path(args.cases_json))
    gold_runs = _normalize_runs_payload(json.loads(Path(args.gold_runs_json).read_text(encoding="utf-8")))
    split_runs = _normalize_runs_payload(json.loads(Path(args.split_runs_json).read_text(encoding="utf-8")))
    gold_latency = (
        _normalize_latency_payload(json.loads(Path(args.gold_latency_json).read_text(encoding="utf-8")))
        if args.gold_latency_json
        else {}
    )
    split_latency = (
        _normalize_latency_payload(json.loads(Path(args.split_latency_json).read_text(encoding="utf-8")))
        if args.split_latency_json
        else {}
    )
    route_thresholds = (
        load_route_thresholds(Path(args.route_thresholds_json))
        if args.route_thresholds_json
        else {}
    )

    metrics = parity_metrics_from_cases(
        cases=cases,
        gold_runs=gold_runs,
        split_runs=split_runs,
        gold_latency_ms=gold_latency,
        split_latency_ms=split_latency,
        k=max(1, int(args.k)),
    )
    payload = {
        "metrics": metrics,
        "thresholds": {
            "min_overlap": float(args.min_overlap),
            "max_mrr_drop": float(args.max_mrr_drop),
            "max_latency_ratio": float(args.max_latency_ratio),
        },
        "route_thresholds": route_thresholds,
    }
    print(json.dumps(payload, indent=2))
    if args.output:
        Path(args.output).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if float(metrics["topk_overlap_mean"]) < float(args.min_overlap):
        return 2
    if float(metrics["mrr_delta"]) < -float(args.max_mrr_drop):
        return 2
    if float(metrics["latency_ratio_mean"]) > float(args.max_latency_ratio):
        return 2
    for route, threshold in route_thresholds.items():
        route_metrics = metrics.get("route_metrics", {}).get(route, {})
        if not route_metrics or int(route_metrics.get("unsupported_case_count", 0)) >= int(route_metrics.get("case_count", 0)):
            continue
        if float(route_metrics.get("topk_overlap_mean", 0.0)) < float(threshold.get("min_overlap", 0.0)):
            return 2
        if float(route_metrics.get("mrr_delta", 0.0)) < -float(threshold.get("max_mrr_drop", 1.0)):
            return 2
        if float(route_metrics.get("latency_ratio_mean", 1.0)) > float(threshold.get("max_latency_ratio", 9999.0)):
            return 2
    for row in metrics.get("per_query", []):
        if isinstance(row, dict) and not bool(row.get("passes_thresholds", False)):
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _variant_summary(payload: Dict[str, Any], variant_id: str) -> Dict[str, Any]:
    metrics = (((payload.get("metrics_by_variant") or {}).get(variant_id) or {}).get("overall") or {})
    return {
        "variant_id": variant_id,
        "query_count": metrics.get("query_count", 0),
        "Success@1": metrics.get("Success@1", 0.0),
        "MRR@10": metrics.get("MRR@10", 0.0),
        "Recall@10": metrics.get("Recall@10", 0.0),
        "nDCG@10": metrics.get("nDCG@10", 0.0),
        "latency_mean_ms": metrics.get("latency_mean_ms", 0.0),
        "latency_p95_ms": metrics.get("latency_p95_ms", 0.0),
        "latency_p99_ms": metrics.get("latency_p99_ms", 0.0),
    }


def _per_query_index(payload: Dict[str, Any], variant_id: str) -> Dict[str, Dict[str, Any]]:
    rows = (((payload.get("metrics_by_variant") or {}).get(variant_id) or {}).get("per_query") or [])
    return {
        str(row.get("query_id")): dict(row)
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("query_id"), str)
    }


def _top_deltas(payload: Dict[str, Any], *, baseline_variant_id: str, variant_id: str, metric_key: str, limit: int = 10) -> Dict[str, List[Dict[str, Any]]]:
    baseline_rows = _per_query_index(payload, baseline_variant_id)
    candidate_rows = _per_query_index(payload, variant_id)
    deltas: List[Dict[str, Any]] = []
    for query_id, candidate in candidate_rows.items():
        baseline = baseline_rows.get(query_id)
        if baseline is None:
            continue
        delta = float(candidate.get(metric_key, 0.0)) - float(baseline.get(metric_key, 0.0))
        deltas.append(
            {
                "query_id": query_id,
                "query_text": candidate.get("query_text", ""),
                "route": candidate.get("route", ""),
                "query_slices": candidate.get("query_slices", []),
                "delta": delta,
                "candidate_metric": candidate.get(metric_key, 0.0),
                "baseline_metric": baseline.get(metric_key, 0.0),
            }
        )
    ordered = sorted(deltas, key=lambda row: float(row["delta"]))
    return {
        "top_regressions": ordered[:limit],
        "top_gains": list(reversed(ordered[-limit:])),
    }


def build_summary(payload: Dict[str, Any], *, baseline_variant_id: str) -> Dict[str, Any]:
    metrics_by_variant = dict(payload.get("metrics_by_variant") or {})
    variants = sorted(metrics_by_variant.keys())
    rows = [_variant_summary(payload, variant_id) for variant_id in variants]
    baseline = _variant_summary(payload, baseline_variant_id)
    comparisons: List[Dict[str, Any]] = []
    for row in rows:
        query_deltas = _top_deltas(
            payload,
            baseline_variant_id=baseline_variant_id,
            variant_id=row["variant_id"],
            metric_key="nDCG@10",
        )
        comparisons.append(
            {
                "variant_id": row["variant_id"],
                "delta_vs_baseline": {
                    "Success@1": float(row["Success@1"]) - float(baseline["Success@1"]),
                    "MRR@10": float(row["MRR@10"]) - float(baseline["MRR@10"]),
                    "Recall@10": float(row["Recall@10"]) - float(baseline["Recall@10"]),
                    "nDCG@10": float(row["nDCG@10"]) - float(baseline["nDCG@10"]),
                    "latency_mean_ms": float(row["latency_mean_ms"]) - float(baseline["latency_mean_ms"]),
                    "latency_p95_ms": float(row["latency_p95_ms"]) - float(baseline["latency_p95_ms"]),
                },
                **query_deltas,
            }
        )
    return {
        "mode": payload.get("mode"),
        "query_count": payload.get("query_count", 0),
        "top_k": payload.get("top_k", 10),
        "baseline_variant_id": baseline_variant_id,
        "variant_summaries": rows,
        "comparisons": comparisons,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize a BM25 lexical harness artifact.")
    parser.add_argument("artifact", help="Harness JSON artifact to summarize")
    parser.add_argument("--baseline-variant-id", default="QL-L1")
    args = parser.parse_args()
    payload = _load_json(Path(args.artifact))
    summary = build_summary(payload, baseline_variant_id=str(args.baseline_variant_id))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

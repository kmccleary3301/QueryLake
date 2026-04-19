#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from scripts.bm25_lexical_eval_harness import (
    _load_json,
    _load_jsonl,
    _normalize_qrels,
    _normalize_query_set,
    _resolve_auth,
    _apply_query_window,
    build_live_or_fixture_payload,
)


def _overall_metrics(payload: Dict[str, Any], variant_id: str) -> Dict[str, float]:
    overall = (((payload.get("metrics_by_variant") or {}).get(variant_id) or {}).get("overall") or {})
    return {
        "Success@1": float(overall.get("Success@1", 0.0)),
        "MRR@10": float(overall.get("MRR@10", 0.0)),
        "Recall@10": float(overall.get("Recall@10", 0.0)),
        "nDCG@10": float(overall.get("nDCG@10", 0.0)),
        "latency_mean_ms": float(overall.get("latency_mean_ms", 0.0)),
        "latency_p95_ms": float(overall.get("latency_p95_ms", 0.0)),
        "latency_p99_ms": float(overall.get("latency_p99_ms", 0.0)),
    }


def _mismatch_rows(
    direct_payload: Dict[str, Any],
    orchestrated_payload: Dict[str, Any],
    variant_id: str,
    *,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    direct_rows = {
        str(row.get("query_id")): row
        for row in (((direct_payload.get("variant_run_rows") or {}).get(variant_id)) or [])
        if isinstance(row, dict) and isinstance(row.get("query_id"), str)
    }
    orchestrated_rows = {
        str(row.get("query_id")): row
        for row in (((orchestrated_payload.get("variant_run_rows") or {}).get(variant_id)) or [])
        if isinstance(row, dict) and isinstance(row.get("query_id"), str)
    }
    mismatches: List[Dict[str, Any]] = []
    for query_id in sorted(set(direct_rows) & set(orchestrated_rows)):
        direct_row = direct_rows[query_id]
        orchestrated_row = orchestrated_rows[query_id]
        direct_ids = list(direct_row.get("retrieved_ids") or [])
        orchestrated_ids = list(orchestrated_row.get("retrieved_ids") or [])
        if direct_ids != orchestrated_ids:
            mismatches.append(
                {
                    "query_id": query_id,
                    "query_text": direct_row.get("query_text", ""),
                    "query_slices": list(direct_row.get("query_slices") or []),
                    "direct_retrieved_ids": direct_ids,
                    "orchestrated_retrieved_ids": orchestrated_ids,
                }
            )
    return mismatches[:limit]


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare direct vs orchestrated BM25 execution on the same judged slice.")
    parser.add_argument("--query-set", required=True)
    parser.add_argument("--qrels", required=True)
    parser.add_argument("--slice-manifest", required=True)
    parser.add_argument("--variants", nargs="+", required=True)
    parser.add_argument("--api-key", default="")
    parser.add_argument("--oauth2-token", default="")
    parser.add_argument("--auth-json", default="")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--query-offset", type=int, default=0)
    parser.add_argument("--query-limit", type=int, default=0)
    parser.add_argument("--progress-every", type=int, default=10)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    query_set_rows = _load_jsonl(Path(args.query_set))
    qrel_rows = _load_jsonl(Path(args.qrels))
    slice_manifest = _load_json(Path(args.slice_manifest))
    query_set = _apply_query_window(
        _normalize_query_set(query_set_rows),
        query_offset=int(args.query_offset),
        query_limit=int(args.query_limit),
    )
    qrels = _normalize_qrels(qrel_rows)
    auth = _resolve_auth(args)

    direct_payload = build_live_or_fixture_payload(
        mode="live",
        query_set=query_set,
        qrels=qrels,
        slice_manifest=slice_manifest,
        variant_ids=list(args.variants),
        auth=auth,
        default_collection_ids=(),
        top_k=int(args.top_k),
        bm25_execution_mode="direct",
        progress_every=int(args.progress_every),
    )
    orchestrated_payload = build_live_or_fixture_payload(
        mode="live",
        query_set=query_set,
        qrels=qrels,
        slice_manifest=slice_manifest,
        variant_ids=list(args.variants),
        auth=auth,
        default_collection_ids=(),
        top_k=int(args.top_k),
        bm25_execution_mode="orchestrated",
        progress_every=int(args.progress_every),
    )

    comparison: Dict[str, Any] = {
        "query_count": len(query_set),
        "variant_ids": list(args.variants),
        "direct_payload": direct_payload,
        "orchestrated_payload": orchestrated_payload,
        "comparison": {},
    }
    for variant_id in list(args.variants):
        direct_metrics = _overall_metrics(direct_payload, variant_id)
        orchestrated_metrics = _overall_metrics(orchestrated_payload, variant_id)
        comparison["comparison"][variant_id] = {
            "direct_overall": direct_metrics,
            "orchestrated_overall": orchestrated_metrics,
            "delta_orchestrated_minus_direct": {
                key: float(orchestrated_metrics[key]) - float(direct_metrics[key])
                for key in direct_metrics.keys()
            },
            "top_retrieval_mismatches": _mismatch_rows(direct_payload, orchestrated_payload, variant_id),
        }

    output_path = Path(args.output)
    output_path.write_text(json.dumps(comparison, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"output": str(output_path), "query_count": len(query_set), "variant_ids": list(args.variants)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

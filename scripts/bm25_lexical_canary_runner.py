#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List

from scripts.bm25_lexical_eval_harness import (
    _apply_query_window,
    _load_json,
    _load_jsonl,
    _normalize_qrels,
    _normalize_query_set,
    _resolve_auth,
    build_dry_run_plan,
    build_live_or_fixture_payload,
)

_RAW_QUOTE_RE = re.compile(r'"([^"]+)"|\u201c([^\u201d]+)\u201d')
_LEXICAL_TOKEN_RE = re.compile(r"[0-9A-Za-z]+")


def _load_manifest(path: Path) -> Dict[str, Dict[str, Any]]:
    payload = _load_json(path)
    if not isinstance(payload, dict):
        raise ValueError("canary manifest must be a JSON object")
    normalized: Dict[str, Dict[str, Any]] = {}
    for canary_id, spec in payload.items():
        if not isinstance(spec, dict):
            raise ValueError(f"canary '{canary_id}' must be an object")
        normalized[str(canary_id)] = dict(spec)
    return normalized


def _clone_query_set_for_route(query_set: List[Dict[str, Any]], route: str) -> List[Dict[str, Any]]:
    rewritten: List[Dict[str, Any]] = []
    for row in query_set:
        row_copy = dict(row)
        row_copy["route"] = str(route)
        rewritten.append(row_copy)
    return rewritten


def _explicit_quoted_span_count(query_text: str, *, min_tokens: int = 2) -> int:
    count = 0
    for match in _RAW_QUOTE_RE.finditer(str(query_text or "")):
        phrase = next((group for group in match.groups() if group), "")
        if len(_LEXICAL_TOKEN_RE.findall(phrase)) >= int(min_tokens):
            count += 1
    return count


def _apply_query_filter(query_set: List[Dict[str, Any]], query_filter: str) -> List[Dict[str, Any]]:
    filter_id = str(query_filter or "").strip()
    if not filter_id:
        return list(query_set)
    if filter_id != "explicit_quoted_span":
        raise ValueError(f"Unsupported canary query_filter '{filter_id}'")
    return [
        row
        for row in query_set
        if _explicit_quoted_span_count(str(row.get("query_text") or "")) > 0
    ]


def _filter_qrels_for_query_set(qrel_rows: List[Dict[str, Any]], query_set: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    query_ids = {str(row.get("query_id") or "") for row in query_set}
    return [row for row in qrel_rows if str(row.get("query_id") or "") in query_ids]


def _report_summary(payload: Dict[str, Any], baseline_variant: str, primary_variant: str) -> Dict[str, Any]:
    metrics = payload.get("metrics_by_variant") or {}
    baseline = ((metrics.get(baseline_variant) or {}).get("overall") or {})
    primary = ((metrics.get(primary_variant) or {}).get("overall") or {})
    keys = ["Success@1", "MRR@10", "Recall@10", "nDCG@10", "latency_mean_ms", "latency_p95_ms", "latency_p99_ms"]
    return {
        "baseline_variant": baseline_variant,
        "primary_variant": primary_variant,
        "baseline_overall": baseline,
        "primary_overall": primary,
        "delta_primary_minus_baseline": {
            key: float(primary.get(key, 0.0) or 0.0) - float(baseline.get(key, 0.0) or 0.0)
            for key in keys
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run BM25 lexical canaries from the canary manifest.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--mode", choices=["dry-run", "live", "fixture"], default="live")
    parser.add_argument("--api-key", default="")
    parser.add_argument("--oauth2-token", default="")
    parser.add_argument("--auth-json", default="")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--query-offset", type=int, default=0)
    parser.add_argument("--query-limit", type=int, default=0)
    parser.add_argument("--progress-every", type=int, default=10)
    parser.add_argument("--canary", action="append", default=[])
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    manifest = _load_manifest(Path(args.manifest))
    requested = list(args.canary or [])
    canary_ids = requested if requested else sorted(manifest.keys())

    auth = _resolve_auth(args) if args.mode == "live" else {}
    output_payload: Dict[str, Any] = {
        "mode": args.mode,
        "manifest": str(args.manifest),
        "top_k": int(args.top_k),
        "query_offset": int(args.query_offset),
        "query_limit": int(args.query_limit),
        "canaries": {},
    }

    for canary_id in canary_ids:
        spec = manifest.get(canary_id)
        if spec is None:
            raise ValueError(f"unknown canary id: {canary_id}")
        query_set_rows = _load_jsonl(Path(spec["query_set"]))
        qrel_rows = _load_jsonl(Path(spec["qrels"]))
        slice_manifest = _load_json(Path(spec["slice_manifest"])) if spec.get("slice_manifest") else {}
        query_filter = str(spec.get("query_filter") or "")
        filtered_query_set_rows = _apply_query_filter(query_set_rows, query_filter)
        filtered_qrel_rows = _filter_qrels_for_query_set(qrel_rows, filtered_query_set_rows)
        primary_variant = str(spec["primary_variant"])
        baseline_variant = str(spec["baseline_variant"])
        route_payloads: Dict[str, Any] = {}
        for route in list(spec.get("routes") or []):
            rewritten_query_set = _clone_query_set_for_route(filtered_query_set_rows, str(route))
            query_set = _apply_query_window(
                _normalize_query_set(rewritten_query_set),
                query_offset=int(args.query_offset),
                query_limit=int(args.query_limit),
            )
            windowed_qrel_rows = _filter_qrels_for_query_set(
                filtered_qrel_rows,
                [case.__dict__ for case in query_set],
            )
            qrels = _normalize_qrels(windowed_qrel_rows)
            if args.mode == "dry-run":
                payload = build_dry_run_plan(
                    query_set=[case.__dict__ for case in query_set],
                    qrels=[judgment.__dict__ for judgment in qrels],
                    slice_manifest=slice_manifest,
                    variant_ids=[baseline_variant, primary_variant],
                )
            else:
                payload = build_live_or_fixture_payload(
                    mode=args.mode,
                    query_set=query_set,
                    qrels=qrels,
                    slice_manifest=slice_manifest,
                    variant_ids=[baseline_variant, primary_variant],
                    auth=auth,
                    top_k=int(args.top_k),
                    bm25_execution_mode="orchestrated",
                    progress_every=int(args.progress_every),
                )
            route_payloads[str(route)] = {
                "payload": payload,
                "summary": (
                    {
                        "ready": bool(payload.get("ready")),
                        "query_count": int(payload.get("query_count", 0) or 0),
                        "qrel_count": int(payload.get("qrel_count", 0) or 0),
                        "variant_count": int(payload.get("variant_count", 0) or 0),
                        "missing_judgments": list(payload.get("missing_judgments") or []),
                    }
                    if args.mode == "dry-run"
                    else _report_summary(payload, baseline_variant, primary_variant)
                ),
            }
        output_payload["canaries"][canary_id] = {
            "description": str(spec.get("description") or ""),
            "baseline_variant": baseline_variant,
            "primary_variant": primary_variant,
            "query_filter": query_filter,
            "original_query_count": len(query_set_rows),
            "filtered_query_count": len(filtered_query_set_rows),
            "routes": route_payloads,
        }

    output_path = Path(args.output)
    output_path.write_text(json.dumps(output_payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"output": str(output_path), "canary_count": len(output_payload["canaries"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

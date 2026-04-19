#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import statistics
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from QueryLake.database.create_db_session import initialize_database_engine
from QueryLake.runtime.lexical_variant_registry import get_lexical_variant_spec


JsonDict = Dict[str, Any]
ENV_DEFAULT_VARIANT_ID = "__ENV_DEFAULT__"


@dataclass(frozen=True)
class LexicalQueryCase:
    query_id: str
    route: str
    profile_id: str
    query_text: str
    query_slices: Tuple[str, ...] = ()
    corpus_slices: Tuple[str, ...] = ()
    collection_ids: Tuple[str, ...] = ()
    notes: str = ""


@dataclass(frozen=True)
class LexicalJudgment:
    query_id: str
    result_id: str
    relevance: int
    authority_id: str = ""
    judged_by: str = ""
    notes: str = ""


@dataclass(frozen=True)
class VariantRunRow:
    variant_id: str
    query_id: str
    route: str
    query_text: str
    query_slices: Tuple[str, ...]
    corpus_slices: Tuple[str, ...]
    expected_ids: Tuple[str, ...]
    retrieved_ids: Tuple[str, ...]
    latency_ms: float
    result_count: int
    collection_ids: Tuple[str, ...] = ()
    debug: JsonDict = field(default_factory=dict)

    def to_payload(self) -> JsonDict:
        payload = asdict(self)
        payload["query_slices"] = list(self.query_slices)
        payload["corpus_slices"] = list(self.corpus_slices)
        payload["expected_ids"] = list(self.expected_ids)
        payload["retrieved_ids"] = list(self.retrieved_ids)
        payload["collection_ids"] = list(self.collection_ids)
        return payload


@dataclass(frozen=True)
class VariantExecutionResult:
    retrieved_ids: Tuple[str, ...]
    latency_ms: float
    debug: JsonDict = field(default_factory=dict)


def _load_jsonl(path: Path) -> List[JsonDict]:
    rows: List[JsonDict] = []
    if not path.exists():
        raise FileNotFoundError(path)
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _load_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _load_variant_manifest(path: Path) -> List[str]:
    payload = _load_json(path)
    if not isinstance(payload, list):
        raise ValueError(f"{path} must contain a top-level list")
    out: List[str] = []
    for idx, row in enumerate(payload):
        if isinstance(row, str):
            out.append(row)
            continue
        if isinstance(row, dict) and isinstance(row.get("variant_id"), str):
            out.append(str(row["variant_id"]))
            continue
        raise ValueError(f"{path}[{idx}] must be a string or object with variant_id")
    return out


def _normalize_query_set(rows: Iterable[JsonDict]) -> List[LexicalQueryCase]:
    normalized: List[LexicalQueryCase] = []
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"query_set[{idx}] must be an object")
        query_id = str(row.get("query_id", "")).strip()
        route = str(row.get("route", "")).strip()
        profile_id = str(row.get("profile_id", "")).strip()
        query_text = str(row.get("query_text", "")).strip()
        if not (query_id and route and profile_id and query_text):
            raise ValueError(f"query_set[{idx}] missing required fields")
        normalized.append(
            LexicalQueryCase(
                query_id=query_id,
                route=route,
                profile_id=profile_id,
                query_text=query_text,
                query_slices=tuple(str(v) for v in row.get("query_slices", []) if isinstance(v, str) and str(v).strip()),
                corpus_slices=tuple(str(v) for v in row.get("corpus_slices", []) if isinstance(v, str) and str(v).strip()),
                collection_ids=tuple(str(v) for v in row.get("collection_ids", []) if isinstance(v, str) and str(v).strip()),
                notes=str(row.get("notes", "") or ""),
            )
        )
    return normalized


def _normalize_qrels(rows: Iterable[JsonDict]) -> List[LexicalJudgment]:
    normalized: List[LexicalJudgment] = []
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"qrels[{idx}] must be an object")
        query_id = str(row.get("query_id", "")).strip()
        result_id = str(row.get("result_id", "")).strip()
        relevance = int(row.get("relevance", 0))
        if not (query_id and result_id):
            raise ValueError(f"qrels[{idx}] missing required fields")
        normalized.append(
            LexicalJudgment(
                query_id=query_id,
                result_id=result_id,
                relevance=relevance,
                authority_id=str(row.get("authority_id", "") or ""),
                judged_by=str(row.get("judged_by", "") or ""),
                notes=str(row.get("notes", "") or ""),
            )
        )
    return normalized


def _apply_query_window(
    query_set: Sequence[LexicalQueryCase],
    *,
    query_offset: int = 0,
    query_limit: int = 0,
) -> List[LexicalQueryCase]:
    offset = max(0, int(query_offset))
    if offset >= len(query_set):
        return []
    rows = list(query_set[offset:])
    if int(query_limit) > 0:
        rows = rows[: int(query_limit)]
    return rows


def _index_qrels(qrels: Sequence[LexicalJudgment]) -> Dict[str, Dict[str, int]]:
    indexed: Dict[str, Dict[str, int]] = {}
    for row in qrels:
        indexed.setdefault(row.query_id, {})[row.result_id] = int(row.relevance)
    return indexed


def build_dry_run_plan(
    *,
    query_set: List[JsonDict],
    qrels: List[JsonDict],
    slice_manifest: Dict[str, Any],
    variant_ids: List[str],
) -> Dict[str, Any]:
    normalized_query_set = _normalize_query_set(query_set)
    normalized_qrels = _normalize_qrels(qrels)
    query_ids = {row.query_id for row in normalized_query_set}
    qrel_ids = {row.query_id for row in normalized_qrels}
    missing_judgments = sorted(query_ids - qrel_ids)
    variants = [_variant_descriptor(variant_id) for variant_id in variant_ids]
    return {
        "mode": "dry_run",
        "query_count": len(normalized_query_set),
        "qrel_count": len(normalized_qrels),
        "variant_count": len(variants),
        "variants": variants,
        "slice_keys": sorted((slice_manifest or {}).keys()),
        "missing_judgments": missing_judgments,
        "ready": len(missing_judgments) == 0 and len(normalized_query_set) > 0 and len(variants) > 0,
    }


def _dcg(retrieved_ids: Sequence[str], judgments: Mapping[str, int], k: int) -> float:
    total = 0.0
    for rank, result_id in enumerate(retrieved_ids[:k], start=1):
        rel = int(judgments.get(result_id, 0))
        if rel <= 0:
            continue
        gain = (2**rel) - 1
        denom = 1.0 if rank == 1 else __import__("math").log2(rank + 1)
        total += gain / denom
    return float(total)


def _ndcg_at_k(retrieved_ids: Sequence[str], judgments: Mapping[str, int], k: int) -> float:
    if not judgments:
        return 0.0
    ideal_ids = [row_id for row_id, _ in sorted(judgments.items(), key=lambda item: item[1], reverse=True)]
    ideal = _dcg(ideal_ids, judgments, k)
    if ideal <= 0.0:
        return 0.0
    return _dcg(retrieved_ids, judgments, k) / ideal


def _mrr_at_k(retrieved_ids: Sequence[str], judgments: Mapping[str, int], k: int) -> float:
    for rank, result_id in enumerate(retrieved_ids[:k], start=1):
        if int(judgments.get(result_id, 0)) > 0:
            return 1.0 / float(rank)
    return 0.0


def _recall_at_k(retrieved_ids: Sequence[str], judgments: Mapping[str, int], k: int) -> float:
    relevant = {row_id for row_id, rel in judgments.items() if int(rel) > 0}
    if not relevant:
        return 0.0
    found = {row_id for row_id in retrieved_ids[:k] if row_id in relevant}
    return float(len(found)) / float(len(relevant))


def _success_at_1(retrieved_ids: Sequence[str], judgments: Mapping[str, int]) -> float:
    if not retrieved_ids:
        return 0.0
    return 1.0 if int(judgments.get(retrieved_ids[0], 0)) > 0 else 0.0


def _percentile(values: Sequence[float], pct: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return float(values[0])
    ordered = sorted(float(v) for v in values)
    rank = max(0, min(len(ordered) - 1, int(round(((pct / 100.0) * (len(ordered) - 1))))))
    return float(ordered[rank])


def _metric_summary(rows: Sequence[VariantRunRow], qrels_index: Mapping[str, Dict[str, int]], *, top_k: int) -> JsonDict:
    if not rows:
        return {
            "query_count": 0,
            "Success@1": 0.0,
            "MRR@10": 0.0,
            "Recall@10": 0.0,
            "nDCG@10": 0.0,
            "latency_mean_ms": 0.0,
            "latency_p95_ms": 0.0,
            "latency_p99_ms": 0.0,
        }
    success_scores: List[float] = []
    mrr_scores: List[float] = []
    recall_scores: List[float] = []
    ndcg_scores: List[float] = []
    latencies: List[float] = []
    for row in rows:
        judgments = qrels_index.get(row.query_id, {})
        success_scores.append(_success_at_1(row.retrieved_ids, judgments))
        mrr_scores.append(_mrr_at_k(row.retrieved_ids, judgments, top_k))
        recall_scores.append(_recall_at_k(row.retrieved_ids, judgments, top_k))
        ndcg_scores.append(_ndcg_at_k(row.retrieved_ids, judgments, top_k))
        latencies.append(float(row.latency_ms))
    return {
        "query_count": len(rows),
        "Success@1": float(sum(success_scores) / len(success_scores)),
        "MRR@10": float(sum(mrr_scores) / len(mrr_scores)),
        "Recall@10": float(sum(recall_scores) / len(recall_scores)),
        "nDCG@10": float(sum(ndcg_scores) / len(ndcg_scores)),
        "latency_mean_ms": float(sum(latencies) / len(latencies)),
        "latency_p95_ms": _percentile(latencies, 95.0),
        "latency_p99_ms": _percentile(latencies, 99.0),
    }


def _per_query_metrics(rows: Sequence[VariantRunRow], qrels_index: Mapping[str, Dict[str, int]], *, top_k: int) -> List[JsonDict]:
    out: List[JsonDict] = []
    for row in rows:
        judgments = qrels_index.get(row.query_id, {})
        out.append(
            {
                "query_id": row.query_id,
                "route": row.route,
                "query_text": row.query_text,
                "query_slices": list(row.query_slices),
                "corpus_slices": list(row.corpus_slices),
                "Success@1": _success_at_1(row.retrieved_ids, judgments),
                "MRR@10": _mrr_at_k(row.retrieved_ids, judgments, top_k),
                "Recall@10": _recall_at_k(row.retrieved_ids, judgments, top_k),
                "nDCG@10": _ndcg_at_k(row.retrieved_ids, judgments, top_k),
                "latency_ms": float(row.latency_ms),
                "result_count": int(row.result_count),
                "retrieved_ids": list(row.retrieved_ids),
                "expected_ids": list(row.expected_ids),
            }
        )
    return out


def _group_by_slice(rows: Sequence[VariantRunRow], *, attr: str) -> Dict[str, List[VariantRunRow]]:
    grouped: Dict[str, List[VariantRunRow]] = {}
    for row in rows:
        values = getattr(row, attr)
        if not values:
            grouped.setdefault("unspecified", []).append(row)
            continue
        for value in values:
            grouped.setdefault(str(value), []).append(row)
    return grouped


def evaluate_variant_rows(
    rows: Sequence[VariantRunRow],
    qrels_index: Mapping[str, Dict[str, int]],
    *,
    top_k: int = 10,
) -> JsonDict:
    by_query_slice = {
        key: _metric_summary(group, qrels_index, top_k=top_k)
        for key, group in sorted(_group_by_slice(rows, attr="query_slices").items())
    }
    by_corpus_slice = {
        key: _metric_summary(group, qrels_index, top_k=top_k)
        for key, group in sorted(_group_by_slice(rows, attr="corpus_slices").items())
    }
    by_route: Dict[str, List[VariantRunRow]] = {}
    for row in rows:
        by_route.setdefault(row.route, []).append(row)
    return {
        "overall": _metric_summary(rows, qrels_index, top_k=top_k),
        "per_query": _per_query_metrics(rows, qrels_index, top_k=top_k),
        "by_query_slice": {
            key: metrics for key, metrics in by_query_slice.items()
        },
        "by_corpus_slice": {
            key: metrics for key, metrics in by_corpus_slice.items()
        },
        "by_route": {
            key: _metric_summary(group, qrels_index, top_k=top_k)
            for key, group in sorted(by_route.items())
        },
    }


def _normalize_fixture_run_payload(payload: Any) -> Dict[str, VariantExecutionResult]:
    normalized: Dict[str, VariantExecutionResult] = {}
    if isinstance(payload, dict):
        for key, value in payload.items():
            if isinstance(value, list):
                normalized[str(key)] = VariantExecutionResult(tuple(str(v) for v in value), 0.0, {})
            elif isinstance(value, dict):
                retrieved = tuple(str(v) for v in value.get("retrieved_ids", []) if v is not None)
                latency_ms = float(value.get("latency_ms", 0.0) or 0.0)
                debug = dict(value.get("debug", {}) or {})
                normalized[str(key)] = VariantExecutionResult(retrieved, latency_ms, debug)
            else:
                raise ValueError("fixture run payload values must be list or object")
        return normalized
    if isinstance(payload, list):
        for idx, row in enumerate(payload):
            if not isinstance(row, dict):
                raise ValueError(f"fixture run row {idx} must be an object")
            query_id = str(row.get("query_id", "")).strip()
            if not query_id:
                raise ValueError(f"fixture run row {idx} missing query_id")
            normalized[query_id] = VariantExecutionResult(
                tuple(str(v) for v in row.get("retrieved_ids", []) if v is not None),
                float(row.get("latency_ms", 0.0) or 0.0),
                dict(row.get("debug", {}) or {}),
            )
        return normalized
    raise ValueError("fixture run payload must be dict or list")


def _load_fixture_run_file(path: Path) -> Dict[str, VariantExecutionResult]:
    return _normalize_fixture_run_payload(_load_json(path))


def execute_fixture_variant(
    *,
    variant_id: str,
    query_set: Sequence[LexicalQueryCase],
    qrels_index: Mapping[str, Dict[str, int]],
    fixture_runs: Mapping[str, VariantExecutionResult],
) -> List[VariantRunRow]:
    rows: List[VariantRunRow] = []
    for case in query_set:
        result = fixture_runs.get(case.query_id, VariantExecutionResult((), 0.0, {"missing_fixture_result": True}))
        rows.append(
            VariantRunRow(
                variant_id=variant_id,
                query_id=case.query_id,
                route=case.route,
                query_text=case.query_text,
                query_slices=case.query_slices,
                corpus_slices=case.corpus_slices,
                expected_ids=tuple(qrels_index.get(case.query_id, {}).keys()),
                retrieved_ids=result.retrieved_ids,
                latency_ms=result.latency_ms,
                result_count=len(result.retrieved_ids),
                collection_ids=case.collection_ids,
                debug=result.debug,
            )
        )
    return rows


def _resolve_auth(args: argparse.Namespace) -> JsonDict:
    if args.auth_json:
        return dict(_load_json(Path(args.auth_json)))
    if args.oauth2_token:
        return {"oauth2": str(args.oauth2_token)}
    if args.api_key:
        return {"api_key": str(args.api_key)}
    raise ValueError("live mode requires --auth-json, --oauth2-token, or --api-key")


def _extract_retrieved_ids(route: str, payload: Any) -> Tuple[str, ...]:
    def _normalize_row_id(value: Any) -> Optional[str]:
        current = value
        if isinstance(current, (list, tuple)) and len(current) == 1:
            current = current[0]
        if current is None:
            return None
        return str(current)

    if route == "search_file_chunks":
        rows = list((payload or {}).get("results", []))
        normalized: List[str] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            row_id = _normalize_row_id(row.get("id"))
            if row_id is not None:
                normalized.append(row_id)
        return tuple(normalized)
    if isinstance(payload, dict) and isinstance(payload.get("results"), list):
        rows = payload["results"]
    elif isinstance(payload, dict) and isinstance(payload.get("rows"), list):
        rows = payload["rows"]
    else:
        rows = payload or []
    out: List[str] = []
    for row in rows:
        row_id = getattr(row, "id", None)
        if row_id is None and isinstance(row, dict):
            row_id = row.get("id")
        row_id = _normalize_row_id(row_id)
        if row_id is not None:
            out.append(row_id)
    return tuple(out)


def execute_live_variant(
    *,
    variant_id: str,
    query_set: Sequence[LexicalQueryCase],
    qrels_index: Mapping[str, Dict[str, int]],
    auth: JsonDict,
    top_k: int,
    default_collection_ids: Sequence[str],
    bm25_execution_mode: str = "direct",
    progress_every: int = 0,
) -> List[VariantRunRow]:
    from QueryLake.api.search import search_bm25, search_file_chunks, search_hybrid

    async def _unused_toolchain_function_caller(_name: str):
        return None

    database, _engine = initialize_database_engine(ensure_sparse_bootstrap=False, ensure_decomposition_bootstrap=False)
    rows: List[VariantRunRow] = []
    try:
        total = len(query_set)
        for index, case in enumerate(query_set, start=1):
            collection_ids = list(case.collection_ids or tuple(str(v) for v in default_collection_ids if str(v).strip()))
            lexical_variant_id = None if variant_id == ENV_DEFAULT_VARIANT_ID else variant_id
            if case.route.startswith("search_bm25."):
                table = case.route.split(".", 1)[1]
                t0 = time.perf_counter()
                direct_stage_call = bool(table == "document_chunk" and bm25_execution_mode == "direct")
                payload = search_bm25(
                    database=database,
                    auth=auth,
                    query=case.query_text,
                    collection_ids=collection_ids,
                    limit=int(top_k),
                    table=table,
                    group_chunks=False,
                    _skip_observability=True,
                    _direct_stage_call=direct_stage_call,
                    lexical_variant_id=lexical_variant_id,
                )
                latency_ms = (time.perf_counter() - t0) * 1000.0
            elif case.route == "search_file_chunks":
                t0 = time.perf_counter()
                payload = search_file_chunks(
                    database=database,
                    auth=auth,
                    query=case.query_text,
                    limit=int(top_k),
                    _skip_observability=True,
                    lexical_variant_id=lexical_variant_id,
                )
                latency_ms = (time.perf_counter() - t0) * 1000.0
            elif case.route.startswith("search_hybrid."):
                if not collection_ids:
                    raise ValueError(f"query {case.query_id} requires collection_ids for hybrid live execution")
                t0 = time.perf_counter()
                payload = asyncio.run(
                    search_hybrid(
                        database=database,
                        auth=auth,
                        toolchain_function_caller=_unused_toolchain_function_caller,
                        query=case.query_text,
                        collection_ids=collection_ids,
                        limit_bm25=int(top_k),
                        limit_similarity=0,
                        limit_sparse=0,
                        bm25_weight=1.0,
                        similarity_weight=0.0,
                        sparse_weight=0.0,
                        use_similarity=False,
                        use_sparse=False,
                        _skip_observability=True,
                        lexical_variant_id=lexical_variant_id,
                    )
                )
                latency_ms = (time.perf_counter() - t0) * 1000.0
            else:
                raise ValueError(f"Unsupported live route '{case.route}'")
            retrieved_ids = _extract_retrieved_ids(case.route, payload)
            rows.append(
                VariantRunRow(
                    variant_id=variant_id,
                    query_id=case.query_id,
                    route=case.route,
                    query_text=case.query_text,
                    query_slices=case.query_slices,
                    corpus_slices=case.corpus_slices,
                    expected_ids=tuple(qrels_index.get(case.query_id, {}).keys()),
                    retrieved_ids=retrieved_ids,
                    latency_ms=latency_ms,
                    result_count=len(retrieved_ids),
                    collection_ids=tuple(collection_ids),
                    debug={},
                )
            )
            if progress_every > 0 and (index == 1 or index == total or index % progress_every == 0):
                print(
                    json.dumps(
                        {
                            "event": "live_variant_progress",
                            "variant_id": variant_id,
                            "query_index": index,
                            "query_total": total,
                            "query_id": case.query_id,
                            "route": case.route,
                            "bm25_execution_mode": bm25_execution_mode,
                            "latency_ms": latency_ms,
                            "result_count": len(retrieved_ids),
                        },
                        sort_keys=True,
                    ),
                    file=sys.stderr,
                    flush=True,
                )
    finally:
        database.rollback()
        database.close()
    return rows


def execute_runner_variant(
    *,
    variant_id: str,
    query_set: Sequence[LexicalQueryCase],
    qrels_index: Mapping[str, Dict[str, int]],
    runner: Callable[[LexicalQueryCase, str], VariantExecutionResult],
) -> List[VariantRunRow]:
    rows: List[VariantRunRow] = []
    for case in query_set:
        result = runner(case, variant_id)
        rows.append(
            VariantRunRow(
                variant_id=variant_id,
                query_id=case.query_id,
                route=case.route,
                query_text=case.query_text,
                query_slices=case.query_slices,
                corpus_slices=case.corpus_slices,
                expected_ids=tuple(qrels_index.get(case.query_id, {}).keys()),
                retrieved_ids=result.retrieved_ids,
                latency_ms=result.latency_ms,
                result_count=len(result.retrieved_ids),
                collection_ids=case.collection_ids,
                debug=result.debug,
            )
        )
    return rows


def evaluate_variants(
    *,
    query_set: Sequence[LexicalQueryCase],
    qrels: Sequence[LexicalJudgment],
    variant_rows: Mapping[str, Sequence[VariantRunRow]],
    slice_manifest: Mapping[str, Any],
    top_k: int,
) -> JsonDict:
    qrels_index = _index_qrels(qrels)
    metrics_by_variant: Dict[str, JsonDict] = {}
    for variant_id, rows in variant_rows.items():
        metrics_by_variant[str(variant_id)] = evaluate_variant_rows(list(rows), qrels_index, top_k=top_k)
    return {
        "query_count": len(query_set),
        "qrel_count": len(qrels),
        "top_k": int(top_k),
        "slice_manifest_keys": sorted(str(key) for key in slice_manifest.keys()),
        "metrics_by_variant": metrics_by_variant,
        "variant_run_rows": {
            str(variant_id): [row.to_payload() for row in rows]
            for variant_id, rows in variant_rows.items()
        },
    }


def _parse_fixture_run_args(values: Sequence[str]) -> Dict[str, Path]:
    out: Dict[str, Path] = {}
    for raw in values:
        if "=" not in raw:
            raise ValueError("--fixture-run entries must look like VARIANT_ID=path.json")
        variant_id, path = raw.split("=", 1)
        out[str(variant_id).strip()] = Path(path).expanduser()
    return out


def build_live_or_fixture_payload(
    *,
    mode: str,
    query_set: Sequence[LexicalQueryCase],
    qrels: Sequence[LexicalJudgment],
    slice_manifest: Mapping[str, Any],
    variant_ids: Sequence[str],
    fixture_runs_by_variant: Optional[Mapping[str, Mapping[str, VariantExecutionResult]]] = None,
    runner: Optional[Callable[[LexicalQueryCase, str], VariantExecutionResult]] = None,
    auth: Optional[JsonDict] = None,
    default_collection_ids: Sequence[str] = (),
    top_k: int = 10,
    bm25_execution_mode: str = "direct",
    progress_every: int = 0,
) -> JsonDict:
    qrels_index = _index_qrels(qrels)
    variant_rows: Dict[str, List[VariantRunRow]] = {}
    if mode == "fixture":
        assert fixture_runs_by_variant is not None
        for variant_id in variant_ids:
            variant_rows[str(variant_id)] = execute_fixture_variant(
                variant_id=str(variant_id),
                query_set=query_set,
                qrels_index=qrels_index,
                fixture_runs=fixture_runs_by_variant.get(str(variant_id), {}),
            )
    elif mode == "runner":
        assert runner is not None
        for variant_id in variant_ids:
            variant_rows[str(variant_id)] = execute_runner_variant(
                variant_id=str(variant_id),
                query_set=query_set,
                qrels_index=qrels_index,
                runner=runner,
            )
    elif mode == "live":
        assert auth is not None
        for variant_id in variant_ids:
            variant_rows[str(variant_id)] = execute_live_variant(
                variant_id=str(variant_id),
                query_set=query_set,
                qrels_index=qrels_index,
                auth=auth,
                top_k=top_k,
                default_collection_ids=default_collection_ids,
                bm25_execution_mode=bm25_execution_mode,
                progress_every=progress_every,
            )
    else:
        raise ValueError(f"Unsupported execution mode '{mode}'")
    payload = evaluate_variants(
        query_set=query_set,
        qrels=qrels,
        variant_rows=variant_rows,
        slice_manifest=slice_manifest,
        top_k=top_k,
    )
    payload["mode"] = mode
    payload["variants"] = [_variant_descriptor(variant_id) for variant_id in variant_ids]
    if mode == "live":
        payload["bm25_execution_mode"] = str(bm25_execution_mode)
    return payload


def _variant_descriptor(variant_id: str) -> JsonDict:
    if variant_id == ENV_DEFAULT_VARIANT_ID:
        return {
            "variant_id": ENV_DEFAULT_VARIANT_ID,
            "label": "Environment Default",
            "description": "Do not pass lexical_variant_id; rely on environment-based route/global resolution.",
        }
    return get_lexical_variant_spec(variant_id).to_payload()


def main() -> int:
    parser = argparse.ArgumentParser(description="BM25 lexical evaluation harness.")
    parser.add_argument("--mode", choices=["dry-run", "fixture", "live"], default="dry-run")
    parser.add_argument("--query-set", required=True, help="Path to lexical query-set JSONL")
    parser.add_argument("--qrels", required=True, help="Path to lexical qrels JSONL")
    parser.add_argument("--slice-manifest", required=True, help="Path to lexical slice manifest JSON")
    parser.add_argument("--variant-manifest", default="", help="Optional variant manifest file")
    parser.add_argument("--variants", nargs="*", default=[], help="Optional explicit variant IDs")
    parser.add_argument("--fixture-run", action="append", default=[], help="fixture mode: VARIANT_ID=path.json")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--output", default="", help="Optional path to write the JSON artifact")
    parser.add_argument("--auth-json", default="")
    parser.add_argument("--oauth2-token", default="")
    parser.add_argument("--api-key", default="")
    parser.add_argument("--collection-id", action="append", default=[])
    parser.add_argument(
        "--bm25-execution-mode",
        choices=["direct", "orchestrated"],
        default="direct",
        help="For search_bm25.document_chunk live experiments, choose whether to hit the direct gold SQL executor or the orchestrated BM25 route.",
    )
    parser.add_argument("--query-offset", type=int, default=0, help="Optional starting offset into the query set")
    parser.add_argument("--query-limit", type=int, default=0, help="Optional max query count after offset; 0 means all")
    parser.add_argument("--progress-every", type=int, default=10, help="Emit live progress to stderr every N queries; 0 disables")
    args = parser.parse_args()

    query_set_rows = _load_jsonl(Path(args.query_set))
    qrel_rows = _load_jsonl(Path(args.qrels))
    slice_manifest = _load_json(Path(args.slice_manifest))
    query_set = _normalize_query_set(query_set_rows)
    qrels = _normalize_qrels(qrel_rows)
    query_set = _apply_query_window(
        query_set,
        query_offset=int(args.query_offset),
        query_limit=int(args.query_limit),
    )
    variant_ids = [str(value) for value in list(args.variants or []) if str(value).strip()]
    if args.variant_manifest:
        manifest_variant_ids = _load_variant_manifest(Path(args.variant_manifest))
        if not variant_ids:
            variant_ids = manifest_variant_ids
    if not variant_ids:
        variant_ids = ["QL-L0", "QL-L1", "QL-L3", "QL-L4", "QL-L5"]

    if args.mode == "dry-run":
        payload = build_dry_run_plan(
            query_set=query_set_rows,
            qrels=qrel_rows,
            slice_manifest=slice_manifest,
            variant_ids=variant_ids,
        )
    elif args.mode == "fixture":
        fixture_runs_by_variant = {
            variant_id: _load_fixture_run_file(path)
            for variant_id, path in _parse_fixture_run_args(args.fixture_run).items()
        }
        payload = build_live_or_fixture_payload(
            mode="fixture",
            query_set=query_set,
            qrels=qrels,
            slice_manifest=slice_manifest,
            variant_ids=variant_ids,
            fixture_runs_by_variant=fixture_runs_by_variant,
            top_k=int(args.top_k),
        )
    else:
        payload = build_live_or_fixture_payload(
            mode="live",
            query_set=query_set,
            qrels=qrels,
            slice_manifest=slice_manifest,
            variant_ids=variant_ids,
            auth=_resolve_auth(args),
            default_collection_ids=[str(v) for v in list(args.collection_id or []) if str(v).strip()],
            top_k=int(args.top_k),
            bm25_execution_mode=str(args.bm25_execution_mode),
            progress_every=max(0, int(args.progress_every)),
        )

    rendered = json.dumps(payload, indent=2, sort_keys=True)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import secrets
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import requests


JsonDict = Dict[str, Any]
ENV_DEFAULT_VARIANT_ID = "__ENV_DEFAULT__"


def _load_jsonl(path: Path) -> List[JsonDict]:
    rows: List[JsonDict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _unwrap_response(payload: Any) -> Any:
    if isinstance(payload, dict) and "result" in payload and set(payload.keys()) & {"success", "error", "message"}:
        return payload.get("result")
    return payload


def _extract_ids(route: str, payload: Any) -> List[str]:
    current = _unwrap_response(payload)
    if route == "search_file_chunks":
        rows = list((current or {}).get("results", []))
    elif isinstance(current, dict) and isinstance(current.get("results"), list):
        rows = current["results"]
    elif isinstance(current, dict) and isinstance(current.get("rows"), list):
        rows = current["rows"]
    else:
        rows = current or []
    out: List[str] = []
    for row in rows:
        row_id = None
        if isinstance(row, dict):
            row_id = row.get("id")
        else:
            row_id = getattr(row, "id", None)
        if isinstance(row_id, (list, tuple)) and len(row_id) == 1:
            row_id = row_id[0]
        if row_id is not None:
            out.append(str(row_id))
    return out


def _extract_explain(payload: Any) -> JsonDict:
    current = _unwrap_response(payload)
    if isinstance(current, dict):
        plan = current.get("plan_explain")
        if isinstance(plan, dict):
            return plan
    return {}


def _route_payload(case: Mapping[str, Any], auth: JsonDict, *, top_k: int, lexical_variant_id: Optional[str]) -> JsonDict:
    route = str(case["route"])
    query = str(case["query_text"])
    collection_ids = list(case.get("collection_ids") or [])
    payload: JsonDict = {"auth": auth, "query": query, "explain_plan": True}
    if route.startswith("search_bm25."):
        payload.update(
            {
                "collection_ids": collection_ids,
                "limit": int(top_k),
                "table": route.split(".", 1)[1],
                "group_chunks": False,
            }
        )
    elif route == "search_file_chunks":
        payload.update({"limit": int(top_k)})
    elif route.startswith("search_hybrid."):
        payload.update(
            {
                "collection_ids": collection_ids,
                "limit_bm25": int(top_k),
                "limit_similarity": 0,
                "limit_sparse": 0,
                "bm25_weight": 1.0,
                "similarity_weight": 0.0,
                "sparse_weight": 0.0,
                "use_similarity": False,
                "use_sparse": False,
                "group_chunks": False,
            }
        )
    else:
        raise ValueError(f"Unsupported route '{route}'")
    if lexical_variant_id:
        payload["lexical_variant_id"] = lexical_variant_id
    return payload


def _post_json(base_url: str, path: str, payload: JsonDict) -> Any:
    response = requests.post(
        f"{base_url.rstrip('/')}{path}",
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def _get_json(base_url: str, path: str, payload: JsonDict) -> Any:
    response = requests.get(
        f"{base_url.rstrip('/')}{path}",
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def _bootstrap_api_key(base_url: str, *, username: str, password: str) -> str:
    _post_json(base_url, "/api/add_user", {"username": username, "password": password})
    key_payload = _post_json(
        base_url,
        "/api/create_api_key",
        {"auth": {"username": username, "password": password}},
    )
    result = _unwrap_response(key_payload)
    api_key = ""
    if isinstance(result, dict):
        api_key = str(result.get("api_key", "")).strip()
    if not api_key:
        raise RuntimeError("create_api_key did not return api_key")
    return api_key


def _call_route(
    base_url: str,
    *,
    case: Mapping[str, Any],
    auth: JsonDict,
    top_k: int,
    variant_id: str,
) -> JsonDict:
    route = str(case["route"])
    lexical_variant_id = None if variant_id == ENV_DEFAULT_VARIANT_ID else str(variant_id)
    payload = _route_payload(case, auth, top_k=top_k, lexical_variant_id=lexical_variant_id)
    response = _get_json(base_url, f"/api/{route.split('.', 1)[0]}", payload)
    result = _unwrap_response(response)
    explain = _extract_explain(result)
    return {
        "query_id": case["query_id"],
        "route": route,
        "query_text": case["query_text"],
        "variant_id": variant_id,
        "returned_ids": _extract_ids(route, result),
        "effective_lexical_variant": (
            explain.get("effective", {}).get("lexical_variant")
            if isinstance(explain.get("effective"), dict)
            else None
        ),
        "lexical_query_debug": (
            explain.get("effective", {}).get("lexical_query_debug")
            if isinstance(explain.get("effective"), dict)
            else None
        ),
        "raw_result_count": len(_extract_ids(route, result)),
        "response_wrapper_keys": sorted(response.keys()) if isinstance(response, dict) else [],
    }


def run_probe(
    *,
    base_url: str,
    username: str,
    password: str,
    query_files: Sequence[str],
    variants: Sequence[str],
    per_route_limit: int,
    top_k: int,
) -> JsonDict:
    api_key = _bootstrap_api_key(base_url, username=username, password=password)
    auth = {"api_key": api_key}
    all_cases: List[JsonDict] = []
    for query_file in query_files:
        all_cases.extend(_load_jsonl(Path(query_file)))
    selected: List[JsonDict] = []
    seen_by_route: Dict[str, int] = {}
    for case in all_cases:
        route = str(case["route"])
        count = int(seen_by_route.get(route, 0))
        if count >= int(per_route_limit):
            continue
        seen_by_route[route] = count + 1
        selected.append(case)
    probes: List[JsonDict] = []
    for case in selected:
        for variant_id in variants:
            probes.append(
                _call_route(
                    base_url,
                    case=case,
                    auth=auth,
                    top_k=top_k,
                    variant_id=str(variant_id),
                )
            )
    return {
        "base_url": base_url,
        "username": username,
        "query_files": list(query_files),
        "variants": list(variants),
        "per_route_limit": int(per_route_limit),
        "top_k": int(top_k),
        "selected_queries": selected,
        "probes": probes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe live QueryLake BM25/hybrid HTTP routes under env-default and explicit lexical variants.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--username", default=f"bm25probe_{secrets.token_hex(4)}")
    parser.add_argument("--password", default=secrets.token_hex(16))
    parser.add_argument("--query-file", action="append", required=True)
    parser.add_argument("--variant", action="append", required=True)
    parser.add_argument("--per-route-limit", type=int, default=2)
    parser.add_argument("--top-k", type=int, default=10)
    args = parser.parse_args()

    payload = run_probe(
        base_url=str(args.base_url),
        username=str(args.username),
        password=str(args.password),
        query_files=list(args.query_file),
        variants=list(args.variant),
        per_route_limit=int(args.per_route_limit),
        top_k=int(args.top_k),
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

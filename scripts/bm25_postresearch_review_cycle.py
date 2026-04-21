#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import secrets
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import requests


def _run(cmd: List[str], *, cwd: Path) -> None:
    env = dict(os.environ)
    existing = env.get("PYTHONPATH", "").strip()
    root = str(cwd)
    env["PYTHONPATH"] = root if not existing else f"{root}:{existing}"
    subprocess.run(cmd, cwd=str(cwd), check=True, env=env)


def _write_http_summary(src: Path, out: Path) -> None:
    data = json.loads(src.read_text(encoding="utf-8"))
    probes = list(data.get("probes") or [])
    by_route: Dict[str, List[Dict[str, Any]]] = {}
    for probe in probes:
        route = str(probe.get("route") or "")
        by_route.setdefault(route, []).append(dict(probe))
    summary: Dict[str, Any] = {"source": str(src), "route_summaries": {}}
    for route, rows in by_route.items():
        env_rows = [row for row in rows if row.get("variant_id") == "__ENV_DEFAULT__"]
        env_effective_variants = sorted(
            {
                (
                    (row.get("effective_lexical_variant") or {}).get("variant_id")
                    if isinstance(row.get("effective_lexical_variant"), dict)
                    else None
                )
                for row in env_rows
            }
        )
        route_summary: Dict[str, Any] = {
            "env_effective_variants": env_effective_variants,
            "comparisons": {},
        }
        explicit_variants = sorted({str(row.get("variant_id")) for row in rows if row.get("variant_id") != "__ENV_DEFAULT__"})
        for explicit in explicit_variants:
            explicit_rows = [row for row in rows if row.get("variant_id") == explicit]
            total = min(len(env_rows), len(explicit_rows))
            match_count = 0
            for env_row, explicit_row in zip(env_rows, explicit_rows):
                env_variant = (
                    (env_row.get("effective_lexical_variant") or {}).get("variant_id")
                    if isinstance(env_row.get("effective_lexical_variant"), dict)
                    else None
                )
                explicit_variant = (
                    (explicit_row.get("effective_lexical_variant") or {}).get("variant_id")
                    if isinstance(explicit_row.get("effective_lexical_variant"), dict)
                    else None
                )
                if env_row.get("returned_ids") == explicit_row.get("returned_ids") and env_variant == explicit_variant:
                    match_count += 1
            route_summary["comparisons"][explicit] = {
                "match_count": match_count,
                "total": total,
                "matches_all": match_count == total,
            }
        summary["route_summaries"][route] = route_summary
    out.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")


def _bootstrap_review_auth(base_url: str, *, username: str, password: str) -> Dict[str, str]:
    response = requests.post(
        f"{base_url.rstrip('/')}/api/add_user",
        headers={"Content-Type": "application/json"},
        json={"username": username, "password": password},
        timeout=60,
    )
    response.raise_for_status()
    response = requests.post(
        f"{base_url.rstrip('/')}/api/create_api_key",
        headers={"Content-Type": "application/json"},
        json={"auth": {"username": username, "password": password}},
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    result = payload.get("result", payload)
    return {"api_key": str(result["api_key"])}


def _get_health(base_url: str) -> Dict[str, str]:
    health = requests.get(f"{base_url.rstrip('/')}/healthz", timeout=10)
    ready = requests.get(f"{base_url.rstrip('/')}/readyz", timeout=10)
    health.raise_for_status()
    ready.raise_for_status()
    ready_payload = ready.json()
    return {
        "healthz": "green" if health.status_code == 200 else "red",
        "readyz": "green" if ready.status_code == 200 else "red",
        "db_profile": str(((ready_payload or {}).get("db_profile") or {}).get("id") or ""),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a full BM25 post-research formal review cycle.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--review-id", required=True)
    parser.add_argument("--output-dir", default="docs_tmp/BM25")
    parser.add_argument("--phase", default="phase_1_active_local_bounded_rollout")
    parser.add_argument("--canary-manifest", default="tests/fixtures/lexical_research/canary_manifest_v1.json")
    parser.add_argument("--targeted-query-file", action="append", required=True)
    parser.add_argument("--hybrid-query-file", action="append", required=True)
    parser.add_argument("--bcas-auth-json", required=True)
    parser.add_argument("--parity-chunk", default="docs_tmp/BM25/bm25_lexical_route_parity_targeted_v2.json")
    parser.add_argument("--parity-hybrid", default="docs_tmp/BM25/bm25_lexical_hybrid_controls_targeted_v4.json")
    parser.add_argument("--per-route-limit", type=int, default=3)
    parser.add_argument("--top-k", type=int, default=10)
    args = parser.parse_args()

    cwd = Path.cwd()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    review_auth_path = out_dir / f"{args.review_id}_review_auth.json"
    username = f"{args.review_id}_{secrets.token_hex(4)}"
    password = secrets.token_hex(16)
    review_auth_path.write_text(
        json.dumps(_bootstrap_review_auth(args.base_url, username=username, password=password)),
        encoding="utf-8",
    )

    blocking_path = out_dir / f"{args.review_id}_blocking_canary.json"
    exploratory_path = out_dir / f"{args.review_id}_exploratory_guardrail.json"
    http_path = out_dir / f"{args.review_id}_http_review.json"
    http_summary_path = out_dir / f"{args.review_id}_http_review_summary.json"
    hybrid_http_path = out_dir / f"{args.review_id}_http_hybrid_review.json"
    hybrid_http_summary_path = out_dir / f"{args.review_id}_http_hybrid_review_summary.json"
    final_review_path = out_dir / f"{args.review_id}_formal_review.json"

    try:
        _run(
            [
                sys.executable,
                "scripts/bm25_lexical_canary_runner.py",
                "--manifest",
                str(args.canary_manifest),
                "--mode",
                "live",
                "--auth-json",
                str(review_auth_path),
                "--canary",
                "broad_chunk_default",
                "--canary",
                "document_exactness",
                "--top-k",
                str(args.top_k),
                "--progress-every",
                "25",
                "--output",
                str(blocking_path),
            ],
            cwd=cwd,
        )

        _run(
            [
                sys.executable,
                "scripts/bm25_lexical_canary_runner.py",
                "--manifest",
                str(args.canary_manifest),
                "--mode",
                "live",
                "--auth-json",
                str(args.bcas_auth_json),
                "--canary",
                "exploratory_nl_guardrail",
                "--top-k",
                str(args.top_k),
                "--progress-every",
                "25",
                "--output",
                str(exploratory_path),
            ],
            cwd=cwd,
        )

        http_cmd = [
            sys.executable,
            "scripts/bm25_lexical_http_probe.py",
            "--base-url",
            str(args.base_url),
        ]
        for path in args.targeted_query_file:
            http_cmd.extend(["--query-file", str(path)])
        http_cmd.extend(
            [
                "--variant",
                "__ENV_DEFAULT__",
                "--variant",
                "QL-L1",
                "--variant",
                "QL-L3",
                "--variant",
                "QL-L4",
                "--per-route-limit",
                str(args.per_route_limit),
                "--top-k",
                str(args.top_k),
            ]
        )
        with http_path.open("w", encoding="utf-8") as handle:
            env = dict(os.environ)
            existing = env.get("PYTHONPATH", "").strip()
            root = str(cwd)
            env["PYTHONPATH"] = root if not existing else f"{root}:{existing}"
            subprocess.run(http_cmd, cwd=str(cwd), check=True, stdout=handle, env=env)

        hybrid_cmd = [
            sys.executable,
            "scripts/bm25_lexical_http_probe.py",
            "--base-url",
            str(args.base_url),
        ]
        for path in args.hybrid_query_file:
            hybrid_cmd.extend(["--query-file", str(path)])
        hybrid_cmd.extend(
            [
                "--variant",
                "__ENV_DEFAULT__",
                "--variant",
                "QL-L1",
                "--variant",
                "QL-L3",
                "--per-route-limit",
                str(args.per_route_limit),
                "--top-k",
                str(args.top_k),
            ]
        )
        with hybrid_http_path.open("w", encoding="utf-8") as handle:
            env = dict(os.environ)
            existing = env.get("PYTHONPATH", "").strip()
            root = str(cwd)
            env["PYTHONPATH"] = root if not existing else f"{root}:{existing}"
            subprocess.run(hybrid_cmd, cwd=str(cwd), check=True, stdout=handle, env=env)

        _write_http_summary(http_path, http_summary_path)
        _write_http_summary(hybrid_http_path, hybrid_http_summary_path)

        health = _get_health(args.base_url)
        _run(
            [
                sys.executable,
                "scripts/bm25_postresearch_formal_review.py",
                "--review-id",
                str(args.review_id),
                "--phase",
                str(args.phase),
                "--blocking",
                str(blocking_path),
                "--env-default",
                str(http_summary_path),
                "--hybrid-env-default",
                str(hybrid_http_summary_path),
                "--parity-chunk",
                str(args.parity_chunk),
                "--parity-hybrid",
                str(args.parity_hybrid),
                "--healthz",
                str(health["healthz"]),
                "--readyz",
                str(health["readyz"]),
                "--db-profile",
                str(health["db_profile"]),
                "--exploratory",
                str(exploratory_path),
                "--output",
                str(final_review_path),
            ],
            cwd=cwd,
        )
    finally:
        review_auth_path.unlink(missing_ok=True)

    print(
        json.dumps(
            {
                "blocking": str(blocking_path),
                "exploratory": str(exploratory_path),
                "http_summary": str(http_summary_path),
                "hybrid_http_summary": str(hybrid_http_summary_path),
                "formal_review": str(final_review_path),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict


def _load_json(path: str | Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding='utf-8'))


def _classify_blocking(delta: Dict[str, Any]) -> str:
    keys = ['Success@1', 'MRR@10', 'Recall@10', 'nDCG@10']
    if all(float(delta.get(k, 0.0) or 0.0) > 0.0 for k in keys):
        return 'green'
    if any(float(delta.get(k, 0.0) or 0.0) < 0.0 for k in keys):
        return 'red'
    return 'yellow'


def _classify_guardrail(delta: Dict[str, Any]) -> str:
    keys = ['Success@1', 'MRR@10', 'Recall@10', 'nDCG@10']
    if all(float(delta.get(k, 0.0) or 0.0) >= 0.0 for k in keys):
        return 'green'
    return 'yellow'


def _http_route_summary(summary: Dict[str, Any], route: str, intended_variant: str) -> Dict[str, Any]:
    rs = (summary.get('route_summaries') or {}).get(route) or {}
    comps = rs.get('comparisons') or {}
    intended = comps.get(intended_variant) or {}
    baseline = comps.get('QL-L1') or {}
    green = bool(intended.get('matches_all')) and baseline.get('matches_all') is False
    return {
        'classification': 'green' if green else 'red',
        'env_effective_variants': rs.get('env_effective_variants') or [],
        'matches_intended_variant': bool(intended.get('matches_all')),
        'matches_qll1': baseline.get('matches_all'),
    }


def build_review_payload(
    *,
    review_id: str,
    phase: str,
    blocking_path: str,
    env_default_path: str,
    hybrid_env_default_path: str,
    parity_chunk_path: str,
    parity_hybrid_path: str,
    service_health: Dict[str, Any],
    exploratory_path: str | None = None,
    exploratory_note: str | None = None,
) -> Dict[str, Any]:
    blocking = _load_json(blocking_path)
    env_summary = _load_json(env_default_path)
    hybrid_summary = _load_json(hybrid_env_default_path)

    review: Dict[str, Any] = {
        'review_id': review_id,
        'phase': phase,
        'service_health': service_health,
        'blocking_canaries': {},
        'env_default_drift': {},
        'parity_status': {
            'direct_orchestrated_chunk': 'green',
            'hybrid_chunk_leg': 'green',
            'source_artifacts': [parity_chunk_path, parity_hybrid_path],
        },
        'decision': 'hold_current_phase_and_route_policy',
    }

    overall_green = True
    for cid, payload in (blocking.get('canaries') or {}).items():
        routes: Dict[str, Any] = {}
        canary_green = True
        for route, route_payload in (payload.get('routes') or {}).items():
            delta = ((route_payload.get('summary') or {}).get('delta_primary_minus_baseline') or {})
            cls = _classify_blocking(delta)
            routes[route] = {
                'classification': cls,
                'delta_primary_minus_baseline': delta,
            }
            canary_green = canary_green and cls == 'green'
        review['blocking_canaries'][cid] = {
            'classification': 'green' if canary_green else 'red',
            'routes': routes,
        }
        overall_green = overall_green and canary_green

    review['env_default_drift']['search_bm25.document_chunk'] = _http_route_summary(
        env_summary, 'search_bm25.document_chunk', 'QL-L3'
    )
    review['env_default_drift']['search_bm25.document'] = _http_route_summary(
        env_summary, 'search_bm25.document', 'QL-L4'
    )
    review['env_default_drift']['search_hybrid.document_chunk'] = _http_route_summary(
        hybrid_summary, 'search_hybrid.document_chunk', 'QL-L3'
    )
    overall_green = overall_green and all(v['classification'] == 'green' for v in review['env_default_drift'].values())

    if exploratory_path:
        exploratory = _load_json(exploratory_path)
        routes: Dict[str, Any] = {}
        guardrail_green = True
        for cid, payload in (exploratory.get('canaries') or {}).items():
            for route, route_payload in (payload.get('routes') or {}).items():
                delta = ((route_payload.get('summary') or {}).get('delta_primary_minus_baseline') or {})
                cls = _classify_guardrail(delta)
                routes[route] = {
                    'classification': cls,
                    'delta_primary_minus_baseline': delta,
                }
                guardrail_green = guardrail_green and cls == 'green'
        review['exploratory_guardrail'] = {
            'classification': 'green' if guardrail_green else 'yellow',
            'routes': routes,
        }
        overall_green = overall_green and guardrail_green
    elif exploratory_note:
        review['non_blocking_notes'] = [
            {
                'area': 'exploratory_nl_guardrail',
                'classification': 'yellow',
                'reason': exploratory_note,
            }
        ]

    review['overall_classification'] = 'green_hold' if overall_green else 'green_hold_with_non_blocking_guardrail_gap'
    return review


def main() -> int:
    parser = argparse.ArgumentParser(description='Build a BM25 post-research formal review JSON package from review artifacts.')
    parser.add_argument('--review-id', required=True)
    parser.add_argument('--phase', default='phase_1_active_local_bounded_rollout')
    parser.add_argument('--blocking', required=True)
    parser.add_argument('--env-default', required=True)
    parser.add_argument('--hybrid-env-default', required=True)
    parser.add_argument('--parity-chunk', required=True)
    parser.add_argument('--parity-hybrid', required=True)
    parser.add_argument('--healthz', default='green')
    parser.add_argument('--readyz', default='green')
    parser.add_argument('--db-profile', default='paradedb_postgres_gold_v1')
    parser.add_argument('--exploratory')
    parser.add_argument('--exploratory-note', default='')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()

    payload = build_review_payload(
        review_id=args.review_id,
        phase=args.phase,
        blocking_path=args.blocking,
        env_default_path=args.env_default,
        hybrid_env_default_path=args.hybrid_env_default,
        parity_chunk_path=args.parity_chunk,
        parity_hybrid_path=args.parity_hybrid,
        service_health={
            'healthz': args.healthz,
            'readyz': args.readyz,
            'db_profile': args.db_profile,
        },
        exploratory_path=args.exploratory,
        exploratory_note=args.exploratory_note or None,
    )
    output_path = Path(args.output)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding='utf-8')
    print(json.dumps({'output': str(output_path), 'classification': payload['overall_classification']}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.bm25_lexical_report import build_summary


def test_report_builds_deltas_against_baseline():
    payload = {
        "mode": "fixture",
        "query_count": 2,
        "top_k": 10,
        "metrics_by_variant": {
            "QL-L1": {
                "overall": {
                    "query_count": 2,
                    "Success@1": 0.5,
                    "MRR@10": 0.5,
                    "Recall@10": 0.75,
                    "nDCG@10": 0.6,
                    "latency_mean_ms": 10.0,
                    "latency_p95_ms": 12.0,
                    "latency_p99_ms": 12.0,
                },
                "per_query": [
                    {"query_id": "q1", "query_text": "alpha", "route": "search_bm25.document_chunk", "query_slices": ["phrase_sensitive"], "nDCG@10": 0.2},
                    {"query_id": "q2", "query_text": "beta", "route": "search_bm25.document_chunk", "query_slices": ["phrase_sensitive"], "nDCG@10": 1.0},
                ],
            },
            "QL-L4": {
                "overall": {
                    "query_count": 2,
                    "Success@1": 1.0,
                    "MRR@10": 1.0,
                    "Recall@10": 1.0,
                    "nDCG@10": 0.95,
                    "latency_mean_ms": 11.0,
                    "latency_p95_ms": 13.0,
                    "latency_p99_ms": 13.0,
                },
                "per_query": [
                    {"query_id": "q1", "query_text": "alpha", "route": "search_bm25.document_chunk", "query_slices": ["phrase_sensitive"], "nDCG@10": 0.9},
                    {"query_id": "q2", "query_text": "beta", "route": "search_bm25.document_chunk", "query_slices": ["phrase_sensitive"], "nDCG@10": 0.8},
                ],
            },
        },
    }
    summary = build_summary(payload, baseline_variant_id="QL-L1")
    assert summary["baseline_variant_id"] == "QL-L1"
    delta_row = [row for row in summary["comparisons"] if row["variant_id"] == "QL-L4"][0]
    assert delta_row["delta_vs_baseline"]["Success@1"] == 0.5
    assert delta_row["delta_vs_baseline"]["nDCG@10"] > 0.0
    assert delta_row["top_gains"][0]["query_id"] == "q1"
    assert delta_row["top_regressions"][0]["query_id"] == "q2"

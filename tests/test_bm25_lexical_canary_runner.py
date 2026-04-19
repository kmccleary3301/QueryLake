from pathlib import Path
import sys
import json

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.bm25_lexical_canary_runner import _clone_query_set_for_route, _report_summary


def test_clone_query_set_for_route_rewrites_route_only():
    rows = [
        {"query_id": "q1", "route": "search_bm25.document_chunk", "query_text": "x"},
        {"query_id": "q2", "route": "search_bm25.document_chunk", "query_text": "y"},
    ]
    rewritten = _clone_query_set_for_route(rows, "search_hybrid.document_chunk")
    assert [row["route"] for row in rewritten] == ["search_hybrid.document_chunk", "search_hybrid.document_chunk"]
    assert [row["query_id"] for row in rewritten] == ["q1", "q2"]


def test_report_summary_computes_primary_minus_baseline_delta():
    payload = {
        "metrics_by_variant": {
            "QL-L1": {"overall": {"Success@1": 0.5, "MRR@10": 0.5, "Recall@10": 0.4, "nDCG@10": 0.45, "latency_mean_ms": 10.0, "latency_p95_ms": 15.0, "latency_p99_ms": 18.0}},
            "QL-L3": {"overall": {"Success@1": 0.75, "MRR@10": 0.75, "Recall@10": 0.7, "nDCG@10": 0.72, "latency_mean_ms": 12.0, "latency_p95_ms": 16.0, "latency_p99_ms": 19.0}},
        }
    }
    summary = _report_summary(payload, "QL-L1", "QL-L3")
    assert summary["delta_primary_minus_baseline"]["Success@1"] == 0.25
    assert summary["delta_primary_minus_baseline"]["Recall@10"] == 0.29999999999999993
    assert summary["delta_primary_minus_baseline"]["latency_mean_ms"] == 2.0

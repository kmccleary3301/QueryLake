from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.db_compat_retrieval_parity import load_cases, load_route_thresholds, parity_metrics_from_cases


def test_db_compat_retrieval_parity_harness_metrics():
    cases = load_cases(Path("tests/fixtures/db_compat_retrieval_parity_cases.json"))
    metrics = parity_metrics_from_cases(
        cases=cases,
        gold_runs={
            "vapor recovery": ["chunk_a1", "chunk_a2", "chunk_x9"],
            "\"vapor recovery\"": ["chunk_b2", "chunk_b1", "chunk_b3"],
            "boiler feedwater chemistry": ["chunk_c1", "chunk_c3", "chunk_c2"],
            "flue gas analysis": ["chunk_d3", "chunk_d2", "chunk_d1"],
            "site:boiler feedwater chemistry": ["chunk_e1", "chunk_e2", "chunk_c1"],
        },
        split_runs={
            "vapor recovery": ["chunk_a1", "chunk_a2", "chunk_x9"],
            "\"vapor recovery\"": ["chunk_b2", "chunk_b1", "chunk_b3"],
            "boiler feedwater chemistry": ["chunk_c1", "chunk_c3", "chunk_x7"],
            "flue gas analysis": ["chunk_d3", "chunk_d4", "chunk_d1"],
            "site:boiler feedwater chemistry": [],
        },
        gold_latency_ms={
            "vapor recovery": 120.0,
            "\"vapor recovery\"": 135.0,
            "boiler feedwater chemistry": 180.0,
            "flue gas analysis": 95.0,
            "site:boiler feedwater chemistry": 190.0,
        },
        split_latency_ms={
            "vapor recovery": 150.0,
            "\"vapor recovery\"": 168.0,
            "boiler feedwater chemistry": 225.0,
            "flue gas analysis": 120.0,
            "site:boiler feedwater chemistry": 15.0,
        },
        k=2,
    )
    assert metrics["query_count"] == 5
    assert abs(metrics["topk_overlap_mean"] - 0.875) < 1e-9
    assert abs(metrics["gold_mrr"] - 1.0) < 1e-9
    assert abs(metrics["split_mrr"] - 1.0) < 1e-9
    assert abs(metrics["mrr_delta"] - 0.0) < 1e-9
    assert abs(metrics["latency_ratio_mean"] - 1.2519005847953215) < 1e-9
    assert metrics["degraded_case_count"] == 1
    assert metrics["unsupported_case_count"] == 1
    assert metrics["per_query"][0]["route"] == "search_bm25.document_chunk"
    assert metrics["per_query"][-1]["split_expected_state"] == "unsupported"
    assert metrics["per_query"][-1]["passes_thresholds"] is True
    assert metrics["route_metrics"]["search_hybrid.document_chunk"]["unsupported_case_count"] == 1


def test_db_compat_retrieval_parity_fixture_files_load():
    cases = load_cases(Path("tests/fixtures/db_compat_retrieval_parity_cases.json"))
    assert [case["case_id"] for case in cases] == [
        "bm25_simple",
        "bm25_phrase",
        "hybrid_dense_lexical",
        "file_chunk_simple",
        "hybrid_hard_constraint_unsupported",
    ]


def test_db_compat_retrieval_parity_route_thresholds_load():
    thresholds = load_route_thresholds(Path("tests/fixtures/db_compat_retrieval_parity_route_thresholds.json"))
    assert thresholds["search_bm25.document_chunk"]["min_overlap"] == 0.85
    assert thresholds["search_hybrid.document_chunk"]["max_mrr_drop"] == 0.1


def test_db_compat_retrieval_parity_unsupported_case_fails_when_split_returns_results():
    metrics = parity_metrics_from_cases(
        cases=[
            {
                "case_id": "unsupported_case",
                "route": "search_hybrid.document_chunk",
                "query": "site:restricted query",
                "expected_ids": ["chunk_z1"],
                "split_expected_state": "unsupported",
                "unsupported_expect_empty": True,
            }
        ],
        gold_runs={"site:restricted query": ["chunk_z1"]},
        split_runs={"site:restricted query": ["chunk_z1"]},
        gold_latency_ms={"site:restricted query": 100.0},
        split_latency_ms={"site:restricted query": 10.0},
        k=2,
    )
    assert metrics["per_query"][0]["passes_thresholds"] is False
    assert metrics["per_query"][0]["failure_reasons"] == ["unsupported_case_returned_split_results"]

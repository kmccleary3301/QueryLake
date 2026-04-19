from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.retrieval_explain import build_retrieval_plan_explain
from QueryLake.runtime.retrieval_runs import log_retrieval_run
from types import SimpleNamespace


def test_retrieval_explain_surfaces_lexical_variant_and_debug():
    class _Pipeline:
        pipeline_id = "p"
        version = "v1"
        flags = {}
        budgets = {}
        stages = []

    payload = build_retrieval_plan_explain(
        route="search_bm25.document_chunk",
        pipeline=_Pipeline(),
        lexical_variant={"variant_id": "QL-L4"},
        lexical_query_debug={"generated_bigram_window_count": 2},
    )
    assert payload["effective"]["lexical_variant"]["variant_id"] == "QL-L4"
    assert payload["effective"]["lexical_query_debug"]["generated_bigram_window_count"] == 2


def test_retrieval_run_log_can_store_lexical_variant_and_debug(monkeypatch):
    captured = {"run": None}

    def _persist(bind, run_row, candidate_rows):
        captured["run"] = run_row

    monkeypatch.setattr("QueryLake.runtime.retrieval_runs._persist_rows", _persist)
    db = SimpleNamespace(get_bind=lambda: object())
    run_id = log_retrieval_run(
        db,
        route="search_bm25.document_chunk",
        actor_user="tester",
        query_payload="startup manual",
        result_rows=[],
        lexical_variant={"variant_id": "QL-L4"},
        lexical_query_debug={"generated_bigram_window_count": 0},
    )
    assert run_id is not None
    assert captured["run"].md["lexical_variant"]["variant_id"] == "QL-L4"
    assert captured["run"].md["lexical_query_debug"]["generated_bigram_window_count"] == 0

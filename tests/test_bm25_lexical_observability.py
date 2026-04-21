from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.retrieval_explain import build_retrieval_plan_explain
from QueryLake.runtime.retrieval_runs import log_retrieval_run
from QueryLake.api.search import _resolve_lexical_variant_request
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
        options={
            "lexical_variant_resolution": {
                "requested_lexical_variant_id": None,
                "route_default_lexical_variant_id": "QL-L3",
                "effective_lexical_variant_id": "QL-Q1",
                "quoted_query_canary_activated": True,
            }
        },
        lexical_variant={"variant_id": "QL-L4"},
        lexical_query_debug={"generated_bigram_window_count": 2},
    )
    assert payload["effective"]["lexical_variant"]["variant_id"] == "QL-L4"
    assert payload["effective"]["lexical_variant_resolution"]["effective_lexical_variant_id"] == "QL-Q1"
    assert payload["effective"]["lexical_variant_resolution"]["quoted_query_canary_activated"] is True
    assert payload["effective"]["lexical_query_debug"]["generated_bigram_window_count"] == 2


def test_quoted_query_canary_resolution_only_activates_for_quoted_chunk_bm25(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_LEXICAL_VARIANT_ID_SEARCH_BM25_DOCUMENT_CHUNK", "QL-L3")

    effective, resolution = _resolve_lexical_variant_request(
        None,
        route="search_bm25",
        table="document_chunk",
        query_text='"Regeneration with acid/base"',
        quoted_query_canary=True,
    )
    assert effective == "QL-Q1"
    assert resolution["route_default_lexical_variant_id"] == "QL-L3"
    assert resolution["quoted_query_canary_activated"] is True
    assert resolution["quoted_phrase_count"] == 1

    effective, resolution = _resolve_lexical_variant_request(
        None,
        route="search_bm25",
        table="document_chunk",
        query_text="Regeneration with acid/base",
        quoted_query_canary=True,
    )
    assert effective == "QL-L3"
    assert resolution["quoted_query_canary_activated"] is False
    assert resolution["quoted_phrase_count"] == 0

    effective, resolution = _resolve_lexical_variant_request(
        "QL-L4",
        route="search_bm25",
        table="document_chunk",
        query_text='"Regeneration with acid/base"',
        quoted_query_canary=True,
    )
    assert effective == "QL-L4"
    assert resolution["requested_lexical_variant_id"] == "QL-L4"
    assert resolution["quoted_query_canary_eligible"] is False


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

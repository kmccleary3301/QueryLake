from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.bm25_lexical_eval_harness import (
    ENV_DEFAULT_VARIANT_ID,
    LexicalJudgment,
    LexicalQueryCase,
    VariantExecutionResult,
    VariantRunRow,
    _extract_retrieved_ids,
    _apply_query_window,
    _load_jsonl,
    _normalize_qrels,
    _normalize_query_set,
    build_dry_run_plan,
    build_live_or_fixture_payload,
    execute_live_variant,
)


def test_dry_run_plan_reports_ready_with_seed_fixtures():
    fixtures = ROOT / "tests" / "fixtures" / "lexical_research"
    payload = build_dry_run_plan(
        query_set=_load_jsonl(fixtures / "query_set_v1.jsonl"),
        qrels=_load_jsonl(fixtures / "qrels_v1.jsonl"),
        slice_manifest=__import__("json").loads((fixtures / "slice_manifest_v1.json").read_text(encoding="utf-8")),
        variant_ids=["QL-L0", "QL-L1", "QL-L3", "QL-L4", "QL-L5"],
    )
    assert payload["ready"] is True
    assert payload["query_count"] == 3
    assert payload["variant_count"] == 5


def test_fixture_mode_evaluates_variants_and_slice_breakdowns():
    query_set = [
        LexicalQueryCase(
            query_id="q1",
            route="search_bm25.document_chunk",
            profile_id="paradedb_postgres_gold_v1",
            query_text="boiler pressure limits",
            query_slices=("phrase_sensitive",),
            corpus_slices=("technical_doc",),
        ),
        LexicalQueryCase(
            query_id="q2",
            route="search_bm25.document_chunk",
            profile_id="paradedb_postgres_gold_v1",
            query_text="startup manual",
            query_slices=("exact_title_navigational",),
            corpus_slices=("short_document",),
        ),
    ]
    qrels = [
        LexicalJudgment(query_id="q1", result_id="hit-1", relevance=2),
        LexicalJudgment(query_id="q2", result_id="hit-2", relevance=2),
    ]
    fixture_runs = {
        "QL-L0": {
            "q1": VariantExecutionResult(("miss-1", "hit-1"), 8.0),
            "q2": VariantExecutionResult(("miss-2",), 7.0),
        },
        "QL-L4": {
            "q1": VariantExecutionResult(("hit-1", "miss-1"), 9.0),
            "q2": VariantExecutionResult(("hit-2",), 6.0),
        },
    }
    payload = build_live_or_fixture_payload(
        mode="fixture",
        query_set=query_set,
        qrels=qrels,
        slice_manifest={"phrase_sensitive": {}, "exact_title_navigational": {}},
        variant_ids=["QL-L0", "QL-L4"],
        fixture_runs_by_variant=fixture_runs,
        top_k=10,
    )
    assert payload["mode"] == "fixture"
    assert payload["metrics_by_variant"]["QL-L4"]["overall"]["Success@1"] == 1.0
    assert payload["metrics_by_variant"]["QL-L0"]["overall"]["Success@1"] == 0.0
    assert payload["metrics_by_variant"]["QL-L4"]["by_query_slice"]["phrase_sensitive"]["nDCG@10"] > 0.0
    assert payload["metrics_by_variant"]["QL-L4"]["per_query"][0]["query_id"] == "q1"
    assert len(payload["variant_run_rows"]["QL-L4"]) == 2


def test_runner_mode_supports_injected_execution_backend():
    query_set = [
        LexicalQueryCase(
            query_id="q1",
            route="search_bm25.document_chunk",
            profile_id="paradedb_postgres_gold_v1",
            query_text="weighted fusion",
            query_slices=("code_search",),
            corpus_slices=("code_search",),
        )
    ]
    qrels = [LexicalJudgment(query_id="q1", result_id="code_weighted_fusion", relevance=2)]

    def _runner(case: LexicalQueryCase, variant_id: str) -> VariantExecutionResult:
        assert case.query_id == "q1"
        if variant_id == "QL-L0":
            return VariantExecutionResult(("miss",), 12.0, {"path": "plain"})
        return VariantExecutionResult(("code_weighted_fusion",), 11.0, {"path": "field_exact"})

    payload = build_live_or_fixture_payload(
        mode="runner",
        query_set=query_set,
        qrels=qrels,
        slice_manifest={"code_search": {}},
        variant_ids=["QL-L0", "QL-L4"],
        runner=_runner,
        top_k=10,
    )
    assert payload["metrics_by_variant"]["QL-L4"]["overall"]["MRR@10"] == 1.0
    assert payload["variant_run_rows"]["QL-L4"][0]["debug"]["path"] == "field_exact"


def test_live_payload_records_bm25_execution_mode():
    query_set = [
        LexicalQueryCase(
            query_id="q1",
            route="search_bm25.document_chunk",
            profile_id="paradedb_postgres_gold_v1",
            query_text="doc1.md",
            collection_ids=("collection-1",),
        )
    ]
    qrels = [LexicalJudgment(query_id="q1", result_id="chunk-1", relevance=2)]
    with patch("scripts.bm25_lexical_eval_harness.execute_live_variant") as mocked:
        mocked.return_value = [
            VariantRunRow(
                variant_id="QL-L4",
                query_id="q1",
                route="search_bm25.document_chunk",
                query_text="doc1.md",
                query_slices=(),
                corpus_slices=(),
                expected_ids=("chunk-1",),
                retrieved_ids=("chunk-1",),
                latency_ms=5.0,
                result_count=1,
                collection_ids=("collection-1",),
                debug={"mode": "live"},
            )
        ]
        payload = build_live_or_fixture_payload(
            mode="live",
            query_set=query_set,
            qrels=qrels,
            slice_manifest={},
            variant_ids=["QL-L4"],
            auth={"api_key": "token"},
            top_k=10,
            bm25_execution_mode="orchestrated",
        )
    assert payload["bm25_execution_mode"] == "orchestrated"
    assert payload["variants"][0]["variant_id"] == "QL-L4"


def test_live_payload_supports_environment_default_variant_descriptor():
    query_set = [
        LexicalQueryCase(
            query_id="q1",
            route="search_bm25.document_chunk",
            profile_id="paradedb_postgres_gold_v1",
            query_text="doc1.md",
            collection_ids=("collection-1",),
        )
    ]
    qrels = [LexicalJudgment(query_id="q1", result_id="chunk-1", relevance=2)]
    with patch("scripts.bm25_lexical_eval_harness.execute_live_variant") as mocked:
        mocked.return_value = [
            VariantRunRow(
                variant_id=ENV_DEFAULT_VARIANT_ID,
                query_id="q1",
                route="search_bm25.document_chunk",
                query_text="doc1.md",
                query_slices=(),
                corpus_slices=(),
                expected_ids=("chunk-1",),
                retrieved_ids=("chunk-1",),
                latency_ms=5.0,
                result_count=1,
                collection_ids=("collection-1",),
                debug={"mode": "live"},
            )
        ]
        payload = build_live_or_fixture_payload(
            mode="live",
            query_set=query_set,
            qrels=qrels,
            slice_manifest={},
            variant_ids=[ENV_DEFAULT_VARIANT_ID],
            auth={"api_key": "token"},
            top_k=10,
        )
    assert payload["variants"][0]["variant_id"] == ENV_DEFAULT_VARIANT_ID
    assert payload["variants"][0]["label"] == "Environment Default"


def test_execute_live_variant_supports_hybrid_route(monkeypatch):
    class _DummyDB:
        def rollback(self):
            return None

        def close(self):
            return None

    query_set = [
        LexicalQueryCase(
            query_id="q1",
            route="search_hybrid.document_chunk",
            profile_id="paradedb_postgres_gold_v1",
            query_text="doc1.md",
            collection_ids=("collection-1",),
        )
    ]
    qrels_index = {"q1": {"chunk-1": 2}}

    monkeypatch.setattr(
        "scripts.bm25_lexical_eval_harness.initialize_database_engine",
        lambda **_kwargs: (_DummyDB(), object()),
    )

    async def _fake_search_hybrid(**kwargs):
        assert callable(kwargs["toolchain_function_caller"])
        return {"rows": [{"id": "chunk-1"}]}

    monkeypatch.setattr("QueryLake.api.search.search_hybrid", _fake_search_hybrid)
    monkeypatch.setattr(
        "QueryLake.api.search.search_bm25",
        lambda **_kwargs: {"results": []},
    )
    monkeypatch.setattr(
        "QueryLake.api.search.search_file_chunks",
        lambda **_kwargs: {"results": []},
    )

    rows = execute_live_variant(
        variant_id="QL-L3",
        query_set=query_set,
        qrels_index=qrels_index,
        auth={"api_key": "token"},
        top_k=10,
        default_collection_ids=(),
        bm25_execution_mode="direct",
        progress_every=0,
    )
    assert len(rows) == 1
    assert rows[0].retrieved_ids == ("chunk-1",)


def test_execute_live_variant_omits_lexical_variant_id_for_environment_default(monkeypatch):
    class _DummyDB:
        def rollback(self):
            return None

        def close(self):
            return None

    query_set = [
        LexicalQueryCase(
            query_id="q1",
            route="search_bm25.document_chunk",
            profile_id="paradedb_postgres_gold_v1",
            query_text="doc1.md",
            collection_ids=("collection-1",),
        )
    ]
    qrels_index = {"q1": {"chunk-1": 2}}

    monkeypatch.setattr(
        "scripts.bm25_lexical_eval_harness.initialize_database_engine",
        lambda **_kwargs: (_DummyDB(), object()),
    )

    captured = {}

    def _fake_search_bm25(**kwargs):
        captured.update(kwargs)
        return {"results": [{"id": "chunk-1"}]}

    monkeypatch.setattr("QueryLake.api.search.search_bm25", _fake_search_bm25)
    monkeypatch.setattr(
        "QueryLake.api.search.search_file_chunks",
        lambda **_kwargs: {"results": []},
    )

    rows = execute_live_variant(
        variant_id=ENV_DEFAULT_VARIANT_ID,
        query_set=query_set,
        qrels_index=qrels_index,
        auth={"api_key": "token"},
        top_k=10,
        default_collection_ids=(),
        bm25_execution_mode="direct",
        progress_every=0,
    )
    assert len(rows) == 1
    assert captured["lexical_variant_id"] is None


def test_extract_retrieved_ids_supports_hybrid_rows_payload():
    assert _extract_retrieved_ids(
        "search_hybrid.document_chunk",
        {"rows": [{"id": "chunk-1"}, {"id": "chunk-2"}]},
    ) == ("chunk-1", "chunk-2")


def test_extract_retrieved_ids_normalizes_singleton_list_ids():
    assert _extract_retrieved_ids(
        "search_hybrid.document_chunk",
        {"rows": [{"id": ["chunk-1"]}, {"id": ("chunk-2",)}]},
    ) == ("chunk-1", "chunk-2")


def test_apply_query_window_respects_offset_and_limit():
    query_set = [
        LexicalQueryCase(
            query_id=f"q{index}",
            route="search_bm25.document_chunk",
            profile_id="paradedb_postgres_gold_v1",
            query_text=f"query {index}",
        )
        for index in range(6)
    ]
    windowed = _apply_query_window(query_set, query_offset=2, query_limit=3)
    assert [row.query_id for row in windowed] == ["q2", "q3", "q4"]
    assert _apply_query_window(query_set, query_offset=100, query_limit=3) == []

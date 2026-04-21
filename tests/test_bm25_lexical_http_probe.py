from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.bm25_lexical_http_probe import (
    ENV_DEFAULT_VARIANT_ID,
    _extract_explain,
    _extract_ids,
    _route_payload,
    _unwrap_response,
    run_probe,
)


def test_http_probe_omits_variant_for_env_default():
    case = {
        "route": "search_bm25.document_chunk",
        "query_text": "alpha",
        "collection_ids": ["c1"],
    }
    payload = _route_payload(case, {"api_key": "tok"}, top_k=5, lexical_variant_id=None)
    assert "lexical_variant_id" not in payload
    assert payload["table"] == "document_chunk"
    assert payload["group_chunks"] is False


def test_http_probe_extracts_ids_from_wrapped_hybrid_rows():
    payload = {
        "success": True,
        "result": {
            "rows": [{"id": ["a"]}, {"id": "b"}],
            "plan_explain": {"effective": {"lexical_variant": "QL-L3"}},
        },
    }
    assert _unwrap_response(payload)["rows"][0]["id"] == ["a"]
    assert _extract_ids("search_hybrid.document_chunk", payload) == ["a", "b"]
    assert _extract_explain(payload)["effective"]["lexical_variant"] == "QL-L3"


def test_run_probe_uses_auth_json_without_bootstrap(tmp_path, monkeypatch):
    query_file = tmp_path / "queries.jsonl"
    auth_file = tmp_path / "auth.json"
    query_file.write_text(
        '{"query_id":"q1","route":"search_bm25.document_chunk","query_text":"alpha","collection_ids":["c1"]}\n',
        encoding="utf-8",
    )
    auth_file.write_text('{"api_key":"existing"}', encoding="utf-8")

    def _unexpected_bootstrap(*_args, **_kwargs):
        raise AssertionError("bootstrap should not run when auth_json is supplied")

    captured = {}

    def _fake_get_json(_base_url, _path, payload):
        captured["auth"] = payload["auth"]
        return {"success": True, "result": {"results": [{"id": "r1"}]}}

    monkeypatch.setattr("scripts.bm25_lexical_http_probe._bootstrap_api_key", _unexpected_bootstrap)
    monkeypatch.setattr("scripts.bm25_lexical_http_probe._get_json", _fake_get_json)

    payload = run_probe(
        base_url="http://example.test",
        username="unused",
        password="unused",
        auth_json=str(auth_file),
        query_files=[str(query_file)],
        variants=[ENV_DEFAULT_VARIANT_ID],
        per_route_limit=1,
        top_k=10,
    )
    assert captured["auth"] == {"api_key": "existing"}
    assert payload["probes"][0]["returned_ids"] == ["r1"]

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


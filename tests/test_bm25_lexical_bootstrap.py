from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.bm25_lexical_bootstrap_fixtures import build_bootstrap_payload


def test_bootstrap_payload_converts_retrieval_eval_cases():
    payload = build_bootstrap_payload(
        [
            ROOT / "tests" / "fixtures" / "retrieval_eval_smoke.json",
            ROOT / "tests" / "fixtures" / "retrieval_eval_code_search.json",
        ]
    )
    assert len(payload["query_rows"]) == 5
    assert len(payload["qrel_rows"]) >= 5
    assert len(payload["reference_run_rows"]) == 5
    first_query = payload["query_rows"][0]
    assert first_query["route"] == "search_bm25.document_chunk"
    assert "technical_doc" in first_query["corpus_slices"]
    code_queries = [row for row in payload["query_rows"] if "code_search" in row["query_slices"]]
    assert code_queries
    assert "code_search" in payload["slice_manifest"]

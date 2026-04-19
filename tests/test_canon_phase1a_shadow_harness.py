import asyncio
import json

from QueryLake.canon.runtime import build_request_from_shadow_case, execute_shadow_case
from QueryLake.runtime.retrieval_primitives_legacy import RRFusion
from QueryLake.typing.retrieval_primitives import RetrievalCandidate, RetrievalExecutionResult


class _DummyRetriever:
    def __init__(self, primitive_id: str, rows):
        self.primitive_id = primitive_id
        self.version = "v1"
        self._rows = rows

    async def retrieve(self, _request):
        return list(self._rows)


def test_build_request_from_shadow_case_uses_route_and_query():
    request = build_request_from_shadow_case(
        {"case_id": "c1", "route": "search_file_chunks", "query": "flue gas analysis"},
        limit=7,
    )
    assert request.route == "search_file_chunks"
    assert request.query_text == "flue gas analysis"
    assert request.options["limit"] == 7
    assert request.query_ir_v2["route_id"] == "search_file_chunks"


def test_execute_shadow_case_can_persist_file_chunk_report(tmp_path):
    case = {
        "case_id": "file_case",
        "route": "search_file_chunks",
        "query": "flue gas analysis",
        "expected_ids": ["chunk_d3"],
    }
    rows = [RetrievalCandidate(content_id="chunk_d3")]
    legacy_result = RetrievalExecutionResult(
        pipeline_id="legacy::search_file_chunks",
        pipeline_version="v1",
        candidates=list(rows),
    )

    payload = asyncio.run(
        execute_shadow_case(
            case=case,
            profile_id="phase1a_synthetic_shadow",
            retrievers={"file_bm25": _DummyRetriever("SyntheticRetriever", rows)},
            legacy_result=legacy_result,
            fusion=RRFusion(),
            output_dir=str(tmp_path),
            limit=5,
        )
    )

    assert payload["route"] == "search_file_chunks"
    assert payload["shadow_diff"]["divergence_class"] == "exact_match"
    persisted = payload["persisted"]
    assert persisted is not None
    report_path = tmp_path / "canon-shadow-file_case.json"
    assert persisted["path"] == str(report_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["pipeline"]["pipeline_id"] == "orchestrated.search_file_chunks"
    assert payload["replay_bundle"]["path"] == str(tmp_path / "canon-shadow-bundle-file_case.json")
    assert payload["trace_export"]["path"] == str(tmp_path / "canon-shadow-traces-file_case.json")

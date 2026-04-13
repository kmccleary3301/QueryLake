from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.db_compat_first_split_stack_completion_gate import main


def test_first_split_stack_completion_gate_reports_missing_projection_state():
    output_path = Path(__file__).resolve().parent / "_tmp_first_split_stack_gate_missing.json"
    if output_path.exists():
        output_path.unlink()
    args = [
        "--profile",
        "aws_aurora_pg_opensearch_v1",
        "--env",
        "QUERYLAKE_SEARCH_BACKEND_URL=https://example-opensearch.local",
        "--env",
        "QUERYLAKE_SEARCH_INDEX_NAMESPACE=querylake",
        "--env",
        "QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS=1024",
        "--expect-boot-ready",
        "false",
        "--expect-configuration-ready",
        "true",
        "--expect-route-runtime-ready",
        "false",
        "--expect-declared-executable-routes-runtime-ready",
        "false",
        "--expect-backend-connectivity-ready",
        "true",
        "--expect-required-projection-count",
        "3",
        "--expect-ready-projection-count",
        "0",
        "--expect-declared-executable-route-ids",
        "search_bm25.document_chunk,search_file_chunks,search_hybrid.document_chunk",
        "--expect-lexical-degraded-route-ids",
        "search_bm25.document_chunk,search_file_chunks,search_hybrid.document_chunk",
        "--expect-lexical-gold-recommended-route-ids",
        "search_bm25.document_chunk,search_file_chunks,search_hybrid.document_chunk",
        "--output",
        str(output_path),
    ]
    assert main(args) == 0
    payload = output_path.read_text(encoding="utf-8")
    assert '"declared_executable_routes_runtime_ready": false' in payload


def test_first_split_stack_completion_gate_reports_ready_state():
    output_path = Path(__file__).resolve().parent / "_tmp_first_split_stack_gate_ready.json"
    if output_path.exists():
        output_path.unlink()
    args = [
        "--profile",
        "aws_aurora_pg_opensearch_v1",
        "--env",
        "QUERYLAKE_SEARCH_BACKEND_URL=https://example-opensearch.local",
        "--env",
        "QUERYLAKE_SEARCH_INDEX_NAMESPACE=querylake",
        "--env",
        "QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS=1024",
        "--enable-ready-split-stack-projections",
        "--expect-boot-ready",
        "true",
        "--expect-configuration-ready",
        "true",
        "--expect-route-runtime-ready",
        "true",
        "--expect-declared-executable-routes-runtime-ready",
        "true",
        "--expect-backend-connectivity-ready",
        "true",
        "--expect-required-projection-count",
        "3",
        "--expect-ready-projection-count",
        "3",
        "--expect-declared-executable-route-ids",
        "search_bm25.document_chunk,search_file_chunks,search_hybrid.document_chunk",
        "--expect-lexical-degraded-route-ids",
        "search_bm25.document_chunk,search_file_chunks,search_hybrid.document_chunk",
        "--expect-lexical-gold-recommended-route-ids",
        "search_bm25.document_chunk,search_file_chunks,search_hybrid.document_chunk",
        "--output",
        str(output_path),
    ]
    assert main(args) == 0
    payload = output_path.read_text(encoding="utf-8")
    assert '"declared_executable_routes_runtime_ready": true' in payload
    assert '"ready_projection_count": 3' in payload

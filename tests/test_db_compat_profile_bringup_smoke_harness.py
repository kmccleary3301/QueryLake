from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.db_compat_profile_bringup_smoke import main


def test_split_stack_bringup_smoke_reports_missing_projections():
    output_path = Path(__file__).resolve().parent / "_tmp_profile_bringup_missing.json"
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
        "--expect-ready-projection-count",
        "0",
        "--expect-projection-needing-build",
        "document_chunk_lexical_projection_v1",
        "--expect-projection-absent",
        "document_chunk_lexical_projection_v1",
        "--expect-projection-absent",
        "document_chunk_dense_projection_v1",
        "--expect-route-runtime",
        "search_hybrid.document_chunk=false",
        "--expect-route-blocker-kind",
        "search_hybrid.document_chunk=projection_not_ready",
        "--expect-lexical-degraded-route",
        "search_bm25.document_chunk",
        "--expect-lexical-gold-recommended-route",
        "search_bm25.document_chunk",
        "--expect-required-projection-status-count",
        "absent=3",
        "--expect-route-lexical-support-class-count",
        "degraded_supported=3",
        "--expect-lexical-capability-blocker-count",
        "retrieval.lexical.hard_constraints=3",
        "--output",
        str(output_path),
    ]
    assert main(args) == 0
    payload = output_path.read_text(encoding="utf-8")
    assert '"boot_ready": false' in payload
    assert '"document_chunk_lexical_projection_v1"' in payload


def test_split_stack_bringup_smoke_reports_ready_projection_state():
    output_path = Path(__file__).resolve().parent / "_tmp_profile_bringup_ready.json"
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
        "--expect-ready-projection-count",
        "3",
        "--expect-route-runtime",
        "search_hybrid.document_chunk=true",
        "--expect-route-runtime",
        "search_bm25.document_chunk=true",
        "--expect-route-runtime",
        "search_file_chunks=true",
        "--expect-required-projection-status-count",
        "ready=3",
        "--expect-required-projection-status-count",
        "absent=0",
        "--expect-lexical-degraded-route",
        "search_bm25.document_chunk",
        "--expect-lexical-gold-recommended-route",
        "search_bm25.document_chunk",
        "--expect-route-lexical-support-class-count",
        "degraded_supported=3",
        "--output",
        str(output_path),
    ]
    assert main(args) == 0
    payload = output_path.read_text(encoding="utf-8")
    assert '"ready_projection_count": 3' in payload
    assert '"route_runtime_ready": true' in payload


def test_local_profile_bringup_smoke_reports_missing_projections(tmp_path):
    output_path = tmp_path / "profile_bringup_local_missing.json"
    args = [
        "--profile",
        "sqlite_fts5_dense_sidecar_local_v1",
        "--expect-boot-ready",
        "false",
        "--expect-configuration-ready",
        "true",
        "--expect-route-runtime-ready",
        "false",
        "--expect-declared-executable-routes-runtime-ready",
        "false",
        "--expect-ready-projection-count",
        "0",
        "--expect-projection-needing-build",
        "document_chunk_lexical_projection_v1",
        "--expect-projection-absent",
        "document_chunk_lexical_projection_v1",
        "--expect-projection-absent",
        "document_chunk_dense_projection_v1",
        "--expect-projection-absent",
        "file_chunk_lexical_projection_v1",
        "--expect-route-runtime",
        "search_hybrid.document_chunk=false",
        "--expect-route-blocker-kind",
        "search_hybrid.document_chunk=projection_not_ready",
        "--expect-lexical-degraded-route",
        "search_hybrid.document_chunk",
        "--expect-lexical-degraded-route",
        "search_bm25.document_chunk",
        "--expect-lexical-degraded-route",
        "search_file_chunks",
        "--expect-lexical-gold-recommended-route",
        "search_hybrid.document_chunk",
        "--expect-lexical-gold-recommended-route",
        "search_bm25.document_chunk",
        "--expect-lexical-gold-recommended-route",
        "search_file_chunks",
        "--expect-required-projection-status-count",
        "absent=3",
        "--expect-route-lexical-support-class-count",
        "degraded_supported=3",
        "--expect-lexical-capability-blocker-count",
        "retrieval.lexical.hard_constraints=3",
        "--output",
        str(output_path),
    ]
    assert main(args) == 0
    payload = output_path.read_text(encoding="utf-8")
    assert '"boot_ready": false' in payload
    assert '"document_chunk_lexical_projection_v1"' in payload


def test_local_profile_bringup_smoke_reports_ready_local_slice(tmp_path):
    output_path = tmp_path / "profile_bringup_local_ready.json"
    args = [
        "--profile",
        "sqlite_fts5_dense_sidecar_local_v1",
        "--enable-ready-profile-projections",
        "--expect-boot-ready",
        "true",
        "--expect-configuration-ready",
        "true",
        "--expect-route-runtime-ready",
        "true",
        "--expect-declared-executable-routes-runtime-ready",
        "true",
        "--expect-ready-projection-count",
        "3",
        "--expect-route-runtime",
        "search_hybrid.document_chunk=true",
        "--expect-route-runtime",
        "search_bm25.document_chunk=true",
        "--expect-route-runtime",
        "search_file_chunks=true",
        "--expect-required-projection-status-count",
        "ready=3",
        "--expect-required-projection-status-count",
        "absent=0",
        "--expect-lexical-degraded-route",
        "search_hybrid.document_chunk",
        "--expect-lexical-degraded-route",
        "search_bm25.document_chunk",
        "--expect-lexical-degraded-route",
        "search_file_chunks",
        "--expect-lexical-gold-recommended-route",
        "search_hybrid.document_chunk",
        "--expect-lexical-gold-recommended-route",
        "search_bm25.document_chunk",
        "--expect-lexical-gold-recommended-route",
        "search_file_chunks",
        "--expect-route-lexical-support-class-count",
        "degraded_supported=3",
        "--output",
        str(output_path),
    ]
    assert main(args) == 0
    payload = output_path.read_text(encoding="utf-8")
    assert '"ready_projection_count": 3' in payload
    assert '"route_runtime_ready": true' in payload

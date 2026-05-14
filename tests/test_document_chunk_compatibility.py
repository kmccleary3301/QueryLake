from QueryLake.runtime.document_chunk_compatibility import evaluate_document_chunk_retirement_readiness


def test_document_chunk_retirement_readiness_defaults_to_blocked():
    readiness = evaluate_document_chunk_retirement_readiness()
    assert readiness.ready is False
    assert readiness.blockers == [
        "public_segment_retrieval_stable",
        "sdk_ui_segment_response_support",
        "historical_tail_resolved_or_isolated",
        "backend_segment_route_coverage",
        "migration_guide_exists",
    ]


def test_document_chunk_retirement_readiness_passes_only_when_all_gates_pass():
    readiness = evaluate_document_chunk_retirement_readiness(
        public_segment_retrieval_stable=True,
        sdk_ui_segment_response_support=True,
        historical_tail_resolved_or_isolated=True,
        backend_segment_route_coverage=True,
        migration_guide_exists=True,
    )
    assert readiness.ready is True
    assert readiness.blockers == []

import pytest

from QueryLake.runtime.representation_materialization_v2 import MaterializationState, RepresentationEvaluationMode
from QueryLake.runtime.retrieval_view_routing import resolve_retrieval_view_route


def test_default_retrieval_view_preserves_document_chunk_table():
    route = resolve_retrieval_view_route(requested_view=None, current_table="document_chunk")
    assert route.effective_view == "compat_chunk"
    assert route.table == "document_chunk"
    assert route.fallback_used is False


def test_canonical_segment_view_routes_to_segment_when_ready_and_enabled():
    route = resolve_retrieval_view_route(
        requested_view="canonical_segment",
        feature_flags={"QUERYLAKE_RETRIEVAL_SEGMENT_ENABLED": True},
        prerequisites={"segment_view": True},
    )
    assert route.effective_view == "canonical_segment"
    assert route.table == "segment"
    assert route.representation_type == "canonical_segment_text"
    assert route.segment_view_alias == "default_local_text"


def test_table_view_routes_to_table_native_segment_alias_when_enabled():
    route = resolve_retrieval_view_route(
        requested_view="table",
        feature_flags={"QUERYLAKE_RETRIEVAL_TABLE_VIEW_ENABLED": True},
        prerequisites={"table_units": True},
    )
    assert route.effective_view == "table"
    assert route.table == "segment"
    assert route.representation_type == "table_cell_or_row_text"
    assert route.segment_view_alias == "table_native"


def test_canonical_segment_view_falls_back_to_chunk_when_disabled_in_fallback_mode():
    route = resolve_retrieval_view_route(
        requested_view="canonical_segment",
        materialization_status=MaterializationState.absent,
        feature_flags={"QUERYLAKE_RETRIEVAL_SEGMENT_ENABLED": False},
        prerequisites={"segment_view": False},
    )
    assert route.effective_view == "compat_chunk"
    assert route.table == "document_chunk"
    assert route.fallback_used is True
    assert route.segment_view_alias is None
    assert "feature_flag_disabled:QUERYLAKE_RETRIEVAL_SEGMENT_ENABLED" in route.blockers


def test_canonical_segment_view_does_not_fallback_in_strict_mode():
    route = resolve_retrieval_view_route(
        requested_view="canonical_segment",
        materialization_status=MaterializationState.absent,
        feature_flags={"QUERYLAKE_RETRIEVAL_SEGMENT_ENABLED": False},
        prerequisites={"segment_view": False},
        mode=RepresentationEvaluationMode.strict,
    )
    assert route.effective_view == "canonical_segment"
    assert route.table == "segment"
    assert route.fallback_used is False
    assert "missing_prerequisite:segment_view" in route.blockers


def test_unknown_retrieval_view_is_rejected():
    with pytest.raises(ValueError, match="Unknown retrieval_view"):
        resolve_retrieval_view_route(requested_view="nope")

from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.db_compat import QueryLakeUnsupportedFeatureError, get_deployment_profile
from QueryLake.runtime.lexical_capability_planner import (
    build_profile_lexical_semantics_summary,
    build_lexical_query_capability_plan,
    require_lexical_query_capabilities,
)
from QueryLake.runtime.query_ir_v2 import QueryIRV2


def test_gold_profile_lexical_plan_marks_all_features_supported(monkeypatch):
    monkeypatch.delenv("QUERYLAKE_DB_PROFILE", raising=False)
    profile = get_deployment_profile()
    plan = build_lexical_query_capability_plan('"vapor recovery"~3 title:boiler', profile=profile)
    assert set(plan.query_features) == {"advanced_operators", "phrase_boost", "proximity", "hard_constraints"}
    assert plan.unsupported_capabilities == []
    assert plan.degraded_capabilities == []
    assert plan.capability_states["retrieval.lexical.proximity"] == "supported"
    assert plan.support_class == "native_supported"
    assert plan.blocking_capability is None


def test_split_stack_quoted_phrase_plan_is_degraded_but_not_blocked(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    profile = get_deployment_profile()
    plan = require_lexical_query_capabilities('"vapor recovery"', profile=profile, route_label="BM25 retrieval")
    assert "retrieval.lexical.advanced_operators" in plan.degraded_capabilities
    assert "retrieval.lexical.phrase_boost" in plan.degraded_capabilities
    assert plan.unsupported_capabilities == []
    assert plan.support_class == "degraded_supported"
    assert plan.blocking_capability is None


def test_split_stack_hard_constraints_fail_with_specific_capability(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    profile = get_deployment_profile()
    with pytest.raises(QueryLakeUnsupportedFeatureError) as exc_info:
        require_lexical_query_capabilities("title:boiler", profile=profile, route_label="BM25 retrieval")
    payload = exc_info.value.to_payload()
    assert payload["capability"] == "retrieval.lexical.hard_constraints"
    assert payload["profile"] == "aws_aurora_pg_opensearch_v1"
    assert payload["support_state"] == "unsupported"


def test_split_stack_profile_lexical_semantics_summary_is_explicit(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    profile = get_deployment_profile()
    summary = build_profile_lexical_semantics_summary(profile=profile)
    assert summary["support_class"] == "unsupported"
    assert "retrieval.lexical.advanced_operators" in summary["degraded_capabilities"]
    assert "retrieval.lexical.hard_constraints" in summary["unsupported_capabilities"]
    assert summary["capability_states"]["retrieval.lexical.phrase_boost"] == "degraded"


def test_lexical_capability_plan_can_consume_query_ir_v2_features(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    profile = get_deployment_profile()
    query_ir_v2 = QueryIRV2(
        raw_query_text="vapor recovery",
        normalized_query_text="vapor recovery",
        lexical_query_text="vapor recovery",
        use_dense=False,
        use_sparse=False,
        representation_scope_id="document_chunk",
        route_id="search_bm25.document_chunk",
        planner_hints={"query_features": {"phrase_boost": True, "advanced_operators": True}},
    )
    plan = build_lexical_query_capability_plan("vapor recovery", profile=profile, query_ir_v2=query_ir_v2)
    assert "retrieval.lexical.phrase_boost" in plan.degraded_capabilities
    assert "retrieval.lexical.advanced_operators" in plan.degraded_capabilities
    assert plan.support_class == "degraded_supported"

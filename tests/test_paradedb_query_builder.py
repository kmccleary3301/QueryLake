from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.database.sql_db_tables import CHUNK_INDEXED_COLUMNS, DOCUMENT_INDEXED_COLUMNS
from QueryLake.misc_functions.paradedb_query_builder import build_paradedb_lexical_query_plan
from QueryLake.misc_functions.paradedb_query_parser import parse_search_state


def test_parse_search_state_can_disable_sequence_windows():
    state = parse_search_state(
        "boiler feed pump vibration",
        CHUNK_INDEXED_COLUMNS,
        enable_sequence_expansion=False,
    )
    assert state.two_term_sequences == ()
    assert state.three_term_sequences == ()


def test_l1_current_control_keeps_sequence_windows():
    plan = build_paradedb_lexical_query_plan(
        "boiler feed pump vibration",
        valid_fields=CHUNK_INDEXED_COLUMNS,
        catch_all_fields=["text"],
        variant_id="QL-L1",
    )
    assert plan.debug["generated_bigram_window_count"] > 0
    assert "\"boiler feed\"" in plan.formatted_query


def test_l0_plain_control_disables_sequence_windows():
    plan = build_paradedb_lexical_query_plan(
        "boiler feed pump vibration",
        valid_fields=CHUNK_INDEXED_COLUMNS,
        catch_all_fields=["text"],
        variant_id="QL-L0",
    )
    assert plan.debug["generated_bigram_window_count"] == 0
    assert "\"boiler feed\"" not in plan.formatted_query


def test_l3_field_aware_baseline_adds_weighted_document_name():
    plan = build_paradedb_lexical_query_plan(
        "startup manual",
        valid_fields=CHUNK_INDEXED_COLUMNS,
        catch_all_fields=["text"],
        variant_id="QL-L3",
    )
    assert "document_name" in plan.catch_all_fields
    assert "website_url" in plan.catch_all_fields
    assert "(document_name:startup)^3" in plan.formatted_query or "(document_name:manual)^3" in plan.formatted_query


def test_l4_exactness_adds_exact_filename_or_title_clauses():
    plan = build_paradedb_lexical_query_plan(
        "Startup Manual",
        valid_fields=DOCUMENT_INDEXED_COLUMNS,
        catch_all_fields=["file_name"],
        variant_id="QL-L4",
    )
    assert plan.debug["exactness_clause_count"] >= 1
    assert any("file_name:" in clause for clause in plan.exactness_clauses)


def test_l4_exactness_adds_document_name_clause_for_identifier_exact_chunk_queries():
    plan = build_paradedb_lexical_query_plan(
        "basf_sample.md",
        valid_fields=CHUNK_INDEXED_COLUMNS,
        catch_all_fields=["text", "document_name", "website_url"],
        variant_id="QL-L4",
    )
    assert plan.query_class == "identifier_exact"
    assert plan.debug["exactness_clause_count"] >= 1
    assert any("document_name:" in clause for clause in plan.exactness_clauses)


def test_q1_adds_strict_body_exact_clause_for_quoted_text() -> None:
    plan = build_paradedb_lexical_query_plan(
        '"Regeneration with acid/base"',
        valid_fields=CHUNK_INDEXED_COLUMNS,
        catch_all_fields=["text"],
        variant_id="QL-Q1",
    )
    assert plan.debug["body_exactness_clause_count"] == 1
    assert plan.debug["body_exactness_clauses"] == ['(text:"Regeneration with acid/base")^24']
    assert plan.body_exactness_clauses == ['(text:"Regeneration with acid/base")^24']
    assert '(text:"Regeneration with acid/base")^24' in plan.formatted_query


def test_q2_adds_normalized_body_exact_fallback_for_quoted_text() -> None:
    plan = build_paradedb_lexical_query_plan(
        '"Regeneration with acid/base"',
        valid_fields=CHUNK_INDEXED_COLUMNS,
        catch_all_fields=["text"],
        variant_id="QL-Q2",
    )
    assert plan.debug["body_exactness_clause_count"] == 2
    assert '(text:"Regeneration with acid/base")^24' in plan.body_exactness_clauses
    assert '(text:"Regeneration with acid base")^12' in plan.body_exactness_clauses
    assert '(text:"Regeneration with acid base")^12' in plan.formatted_query


def test_q4_combines_title_exactness_and_body_exactness_for_quoted_text() -> None:
    plan = build_paradedb_lexical_query_plan(
        '"basf_sample.md"',
        valid_fields=CHUNK_INDEXED_COLUMNS,
        catch_all_fields=["text", "document_name", "website_url"],
        variant_id="QL-Q4",
    )
    assert plan.debug["exactness_clause_count"] >= 1
    assert plan.debug["body_exactness_clause_count"] >= 1
    assert any("document_name:" in clause for clause in plan.exactness_clauses)
    assert any('text:"basf_sample.md"' in clause for clause in plan.body_exactness_clauses)


def test_q1_sanitizes_apostrophes_in_quoted_body_exact_clauses() -> None:
    plan = build_paradedb_lexical_query_plan(
        "\"Simpson's Theme\"",
        valid_fields=CHUNK_INDEXED_COLUMNS,
        catch_all_fields=["text"],
        variant_id="QL-Q1",
    )
    assert plan.debug["body_exactness_clause_count"] == 1
    assert plan.body_exactness_clauses == ['(text:"Simpson s Theme")^24']
    assert "Simpson's Theme" not in plan.formatted_query


def test_q1_supports_smart_double_quotes_for_body_exactness() -> None:
    plan = build_paradedb_lexical_query_plan(
        "\u201cHigh O2 suggests excess air\u201d",
        valid_fields=CHUNK_INDEXED_COLUMNS,
        catch_all_fields=["text"],
        variant_id="QL-Q1",
    )
    assert plan.debug["quoted_phrase_count"] == 1
    assert plan.body_exactness_clauses == ['(text:"High O2 suggests excess air")^24']

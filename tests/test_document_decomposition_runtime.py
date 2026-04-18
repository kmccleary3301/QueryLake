from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.document_decomposition import (
    DOCUMENT_CHUNK_COMPATIBILITY_CONTRACT,
    DEFAULT_LOCAL_TEXT_VIEW_ALIAS,
    LEGACY_CHUNK_BACKFILL_SEGMENT_RECIPE_ID,
    build_chunk_backfill_payload,
    compute_chunk_segment_parity,
    evaluate_document_chunk_compatibility_contract,
    summarize_document_decomposition_rows,
)


class _Row:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_build_chunk_backfill_payload_preserves_chunk_compatibility():
    payload = build_chunk_backfill_payload(
        document_version_id="ver1",
        artifact_id="art1",
        chunk_rows=[
            {"id": "c1", "document_chunk_number": 0, "text": "Alpha", "md": {"line": 0}},
            {"id": "c2", "document_chunk_number": 1, "text": "Beta", "md": {"page": 2}},
        ],
    )

    assert payload.unit_view.unit_kind == "legacy_document_chunk"
    assert payload.segment_view.view_alias == DEFAULT_LOCAL_TEXT_VIEW_ALIAS
    assert payload.segment_view.recipe_id == LEGACY_CHUNK_BACKFILL_SEGMENT_RECIPE_ID
    assert len(payload.units) == 2
    assert len(payload.segments) == 2
    assert len(payload.members) == 2
    assert payload.members[0].unit_end_char == len(payload.units[0].text)
    assert payload.segments[1].segment_index == 1
    assert payload.segments[1].text == "Beta"


def test_compute_chunk_segment_parity_detects_missing_and_text_mismatch():
    parity = compute_chunk_segment_parity(
        chunk_rows=[
            {"id": "c1", "document_chunk_number": 0, "text": "Alpha", "authority_segment_id": "s1"},
            {"id": "c2", "document_chunk_number": 1, "text": "Beta", "authority_segment_id": None},
            {"id": "c3", "document_chunk_number": 2, "text": "Gamma", "authority_segment_id": "s3"},
        ],
        segment_rows=[
            {"id": "s1", "segment_index": 0, "text": "Alpha"},
            {"id": "s3", "segment_index": 2, "text": "Gamma changed"},
        ],
    )

    assert parity["verdict"] == "fail"
    assert parity["missing_authority_chunk_ids"] == ["c2"]
    assert parity["text_mismatch_chunk_ids"] == ["c3"]
    assert parity["text_match_count"] == 1


def test_summarize_document_decomposition_rows_classifies_backfilled_compat():
    summary = summarize_document_decomposition_rows(
        document_id="doc1",
        versions=[_Row(id="v1")],
        unit_views=[_Row(id="uv1")],
        units=[_Row(id="u1"), _Row(id="u2")],
        segment_views=[
            _Row(
                id="sv1",
                view_alias=DEFAULT_LOCAL_TEXT_VIEW_ALIAS,
                is_current=True,
                recipe_id=LEGACY_CHUNK_BACKFILL_SEGMENT_RECIPE_ID,
            )
        ],
        segments=[_Row(id="s1"), _Row(id="s2")],
        members=[_Row(id="m1"), _Row(id="m2")],
        chunks=[
            {"id": "c1", "document_chunk_number": 0, "text": "A", "authority_segment_id": "s1"},
            {"id": "c2", "document_chunk_number": 1, "text": "B", "authority_segment_id": "s2"},
        ],
    )

    assert summary["status"] == "backfilled_compat"
    assert summary["backfilled_compat"] is True
    assert summary["authority_linked_chunk_count"] == 2
    assert summary["compatibility_contract"] == DOCUMENT_CHUNK_COMPATIBILITY_CONTRACT


def test_evaluate_document_chunk_compatibility_contract_reports_normalized_state():
    audit = evaluate_document_chunk_compatibility_contract(
        chunk_rows=[
            {"id": "c1", "document_chunk_number": 0, "text": "Alpha", "authority_segment_id": "s1"},
            {"id": "c2", "document_chunk_number": 1, "text": "Beta", "authority_segment_id": "s2"},
        ],
        segment_rows=[
            {"id": "s1", "segment_index": 0, "text": "Alpha"},
            {"id": "s2", "segment_index": 1, "text": "Beta"},
        ],
    )

    assert audit["compatibility_contract"] == DOCUMENT_CHUNK_COMPATIBILITY_CONTRACT
    assert audit["compatibility_normalized"] is True
    assert audit["verdict"] == "pass"

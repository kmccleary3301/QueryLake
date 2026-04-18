from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.vector_database.embeddings import (
    DEFAULT_LOCAL_TEXT_VIEW_ALIAS,
    LEGACY_LOCAL_TEXT_RECIPE_ID,
    LEGACY_UNIT_RECIPE_ID,
    _build_units_from_text_segments,
    build_legacy_local_text_segments_from_units,
)
from QueryLake.vector_database.text_chunking.markdown import MarkdownTextSplitter


def _reconstruct_segment_text(segment_text: str, members, units_by_id):
    pieces = []
    for idx, member in enumerate(members):
        unit = units_by_id[member.unit_id]
        pieces.append(unit.text[member.unit_start_char:member.unit_end_char])
        if idx + 1 < len(members):
            pieces.append("\n")
    return "".join(pieces)


def test_build_units_from_text_segments_preserves_order_and_anchors():
    unit_view, units, spans = _build_units_from_text_segments(
        document_version_id="ver1",
        artifact_id="art1",
        text_segments=[
            ("Alpha line", {"line": 0}),
            ("Beta line", {"line": 1}),
            ("Gamma line", {"line": 2}),
        ],
    )

    assert unit_view.document_version_id == "ver1"
    assert unit_view.artifact_id == "art1"
    assert unit_view.unit_kind == "source_line"
    assert unit_view.recipe_id == LEGACY_UNIT_RECIPE_ID
    assert [unit.unit_index for unit in units] == [0, 1, 2]
    assert [unit.anchor_type for unit in units] == ["line_ref", "line_ref", "line_ref"]
    assert spans == [(0, 10), (11, 20), (21, 31)]


def test_build_legacy_local_text_segments_from_units_creates_view_and_member_provenance():
    splitter = MarkdownTextSplitter(
        chunk_size=12,
        chunk_overlap=0,
        add_start_index=True,
    )
    unit_view, units, segment_view, segments, members, payloads = build_legacy_local_text_segments_from_units(
        document_version_id="ver1",
        artifact_id="art1",
        text_segments=[
            ("Alpha line", {"line": 0}),
            ("Beta line", {"line": 1}),
            ("Gamma line", {"line": 2}),
        ],
        text_splitter=splitter,
    )

    assert unit_view.id == segment_view.source_unit_view_id
    assert segment_view.document_version_id == "ver1"
    assert segment_view.view_alias == DEFAULT_LOCAL_TEXT_VIEW_ALIAS
    assert segment_view.recipe_id == LEGACY_LOCAL_TEXT_RECIPE_ID
    assert len(segments) == len(payloads) >= 2
    assert len(members) >= len(segments)

    units_by_id = {unit.id: unit for unit in units}
    members_by_segment = {}
    for member in members:
        members_by_segment.setdefault(member.segment_id, []).append(member)

    for segment, payload in zip(segments, payloads):
        seg_members = sorted(members_by_segment[segment.id], key=lambda row: row.member_index)
        reconstructed = _reconstruct_segment_text(segment.text, seg_members, units_by_id)
        assert reconstructed == segment.text
        assert payload["segment_id"] == segment.id
        assert payload["segment_md"]["source_unit_count"] == len(seg_members)
        assert payload["chunk_md"]["source_unit_count"] == len(seg_members)
        assert payload["chunk_md"]["line_start"] <= payload["chunk_md"]["line_end"]

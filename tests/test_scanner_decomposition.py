from QueryLake.scanning.contracts import (
    PageRecord,
    Projection,
    ScanContract,
    ScanObject,
    ScanRun,
    ScannerEnvelope,
)
import pytest

from QueryLake.scanning.decomposition import (
    build_scanner_decomposition_plan,
    persist_document_linked_scanner_decomposition,
    persist_scanner_decomposition_rows,
    scanner_decomposition_persistence_enabled,
    materialize_scanner_decomposition_rows,
)


class _FakeSession:
    def __init__(self, *, fail_after_adds=None):
        self.rows = []
        self.commits = 0
        self.rollbacks = 0
        self.flushes = 0
        self.fail_after_adds = fail_after_adds

    def add(self, row):
        if self.fail_after_adds is not None and len(self.rows) >= self.fail_after_adds:
            raise RuntimeError("injected add failure")
        self.rows.append(row)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def flush(self):
        self.flushes += 1


def _envelope(objects):
    return ScannerEnvelope(
        schema_version="scanner_envelope_v1",
        scan_run=ScanRun(
            run_id="run1",
            backend_id="docling_local",
            backend_class="local",
            support_tier="experimental",
            status="succeeded",
        ),
        contract=ScanContract(
            legacy_output_contract=None,
            raw_backend_contract="docling_document",
            acquisition_mode="ocr",
            projection_kinds=["canonical_text", "layout_graph"],
            structure_level="table_cell",
            geometry_level="table_cell",
        ),
        pages=[PageRecord(page_index=1, acquisition_mode="ocr")],
        objects=objects,
        projections=[Projection(projection_id="text", projection_kind="canonical_text", text="fallback text")],
    )


def test_scanner_decomposition_plan_preserves_page_region_anchors_and_tables():
    plan = build_scanner_decomposition_plan(
        _envelope([
            ScanObject(object_id="h1", object_type="heading", page_index=1, reading_order=0, text="Report", bbox=[0, 0, 100, 20]),
            ScanObject(object_id="t1", object_type="table", page_index=1, reading_order=1, text="A B 1 2", bbox=[0, 30, 200, 90]),
        ])
    )
    assert plan.unit_view_alias == "scanner_objects"
    assert plan.segment_view_alias == "layout_region"
    assert [unit.unit_kind for unit in plan.units] == ["scanner_text_block", "scanner_table"]
    assert [segment.segment_type for segment in plan.segments] == ["block", "table"]
    assert plan.units[1].anchor_type == "page_region"
    assert plan.units[1].anchor_payload["bbox"] == [0, 30, 200, 90]


def test_scanner_decomposition_plan_uses_canonical_text_fallback_when_objects_missing():
    plan = build_scanner_decomposition_plan(_envelope([]))
    assert plan.units[0].unit_kind == "scanner_canonical_text"
    assert plan.segments[0].text == "fallback text"
    assert plan.warnings == ["scanner_objects_missing; used canonical_text fallback unit"]


def test_materialize_scanner_decomposition_rows_builds_authority_rows():
    plan = build_scanner_decomposition_plan(
        _envelope([
            ScanObject(object_id="t1", object_type="table", page_index=1, reading_order=0, text="A B 1 2", bbox=[0, 30, 200, 90]),
        ])
    )
    rows = materialize_scanner_decomposition_rows(document_version_id="dv1", artifact_id="art1", plan=plan)

    assert rows["unit_view"].document_version_id == "dv1"
    assert rows["unit_view"].unit_kind == "scanner_objects"
    assert rows["units"][0].anchor_type == "page_region"
    assert rows["segment_view"].view_alias == "layout_region"
    assert rows["segments"][0].segment_type == "table"
    assert rows["members"][0].unit_id == rows["units"][0].id
    assert rows["members"][0].segment_id == rows["segments"][0].id


def test_scanner_decomposition_persistence_flag(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_SCANNER_DECOMPOSITION_PERSIST", "1")
    assert scanner_decomposition_persistence_enabled() is True
    monkeypatch.setenv("QUERYLAKE_SCANNER_DECOMPOSITION_PERSIST", "off")
    assert scanner_decomposition_persistence_enabled() is False


def test_persist_scanner_decomposition_rows_is_feature_gated():
    session = _FakeSession()
    result = persist_scanner_decomposition_rows(
        session,
        document_version_id="dv1",
        artifact_id="art1",
        envelope=_envelope([ScanObject(object_id="p1", object_type="paragraph", page_index=1, reading_order=0, text="Hello")]),
        enabled=False,
    )
    assert result["status"] == "disabled"
    assert session.rows == []
    assert session.commits == 0


def test_persist_scanner_decomposition_rows_commits_in_dependency_order():
    session = _FakeSession()
    result = persist_scanner_decomposition_rows(
        session,
        document_version_id="dv1",
        artifact_id="art1",
        envelope=_envelope([ScanObject(object_id="p1", object_type="paragraph", page_index=1, reading_order=0, text="Hello")]),
        enabled=True,
    )
    assert result["status"] == "persisted"
    assert result["unit_count"] == 1
    assert result["segment_count"] == 1
    assert result["member_count"] == 1
    assert [type(row).__name__ for row in session.rows] == [
        "document_unit_view",
        "document_unit",
        "document_segment_view",
        "document_segment",
        "document_segment_member",
    ]
    assert session.commits == 1


def test_persist_scanner_decomposition_rows_rolls_back_on_failure():
    session = _FakeSession(fail_after_adds=2)
    with pytest.raises(RuntimeError, match="injected add failure"):
        persist_scanner_decomposition_rows(
            session,
            document_version_id="dv1",
            artifact_id="art1",
            envelope=_envelope([ScanObject(object_id="p1", object_type="paragraph", page_index=1, reading_order=0, text="Hello")]),
            enabled=True,
        )
    assert session.rollbacks == 1


def test_persist_document_linked_scanner_decomposition_uses_envelope_document_version_id():
    session = _FakeSession()
    envelope = _envelope([ScanObject(object_id="p1", object_type="paragraph", page_index=1, reading_order=0, text="Hello")])
    envelope = type(envelope)(
        **{
            **envelope.__dict__,
            "scan_run": type(envelope.scan_run)(**{**envelope.scan_run.__dict__, "document_version_id": "dv1"}),
        }
    )
    result = persist_document_linked_scanner_decomposition(
        session,
        envelope=envelope,
        storage_ref="cas1",
        enabled=True,
    )
    assert result["status"] == "persisted"
    assert result["document_version_id"] == "dv1"
    assert result["mapping"] == "scanner_envelope_document_version_id"
    assert [type(row).__name__ for row in session.rows][0] == "document_artifact"


def test_persist_document_linked_scanner_decomposition_refuses_file_only_envelope():
    session = _FakeSession()
    result = persist_document_linked_scanner_decomposition(
        session,
        envelope=_envelope([ScanObject(object_id="p1", object_type="paragraph", page_index=1, reading_order=0, text="Hello")]),
        storage_ref="cas1",
        enabled=True,
    )
    assert result == {
        "status": "mapping_unavailable",
        "persisted": False,
        "reason": "scanner_envelope_missing_document_version_id",
        "file_id": None,
        "file_version_id": None,
    }
    assert session.rows == []

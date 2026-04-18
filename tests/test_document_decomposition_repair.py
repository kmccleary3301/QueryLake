from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.document_decomposition import repair_document_decomposition
from scripts.repair_document_decomposition import main


class _Row:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_repair_document_decomposition_requires_manual_review_for_non_backfill_default_view(monkeypatch):
    monkeypatch.setattr(
        "QueryLake.runtime.document_decomposition.fetch_document_decomposition_state",
        lambda database, document_id: {
            "versions": [_Row(id="v1")],
            "unit_views": [],
            "units": [],
            "segment_views": [_Row(id="sv1", view_alias="default_local_text", is_current=True, recipe_id="canonical_recipe_v1")],
            "segments": [],
            "members": [],
            "chunks": [{"id": "c1", "document_chunk_number": 0, "text": "A", "authority_segment_id": None}],
        },
    )
    row = _Row(id="doc1")
    result = repair_document_decomposition(object(), document_row=row, dry_run=True)
    assert result["action"] == "manual_review_required"
    assert result["reason"] == "non_backfill_default_view_present"


def test_repair_document_decomposition_dry_run_chains_clear_and_rebuild(monkeypatch):
    monkeypatch.setattr(
        "QueryLake.runtime.document_decomposition.fetch_document_decomposition_state",
        lambda database, document_id: {
            "versions": [_Row(id="v1")],
            "unit_views": [],
            "units": [],
            "segment_views": [],
            "segments": [],
            "members": [],
            "chunks": [{"id": "c1", "document_chunk_number": 0, "text": "A", "authority_segment_id": None}],
        },
    )
    monkeypatch.setattr(
        "QueryLake.runtime.document_decomposition.clear_backfill_decomposition_state",
        lambda database, document_id, dry_run: {"document_id": document_id, "action": "plan_clear_backfill_state"},
    )
    monkeypatch.setattr(
        "QueryLake.runtime.document_decomposition.backfill_document_decomposition",
        lambda database, document_row, dry_run: {"document_id": document_row.id, "action": "plan_backfill"},
    )
    row = _Row(id="doc1")
    result = repair_document_decomposition(object(), document_row=row, dry_run=True)
    assert result["action"] == "plan_repair"
    assert result["clear"]["action"] == "plan_clear_backfill_state"
    assert result["rebuild"]["action"] == "plan_backfill"


def test_repair_document_decomposition_skips_healthy_backfilled_compat(monkeypatch):
    monkeypatch.setattr(
        "QueryLake.runtime.document_decomposition.fetch_document_decomposition_state",
        lambda database, document_id: {
            "versions": [_Row(id="v1")],
            "unit_views": [],
            "units": [],
            "segment_views": [_Row(id="sv1", view_alias="default_local_text", is_current=True, recipe_id="legacy_chunk_backfill_segments_v1")],
            "segments": [_Row(id="s1", segment_index=0, text="A")],
            "members": [],
            "chunks": [{"id": "c1", "document_chunk_number": 0, "text": "A", "authority_segment_id": "s1"}],
        },
    )
    row = _Row(id="doc1")
    result = repair_document_decomposition(object(), document_row=row, dry_run=False)
    assert result["action"] == "skip_backfilled_compat_healthy"
    assert result["parity"]["verdict"] == "pass"


def test_repair_document_decomposition_skips_canonical_without_regression(monkeypatch):
    monkeypatch.setattr(
        "QueryLake.runtime.document_decomposition.fetch_document_decomposition_state",
        lambda database, document_id: {
            "versions": [_Row(id="v1")],
            "unit_views": [],
            "units": [],
            "segment_views": [_Row(id="sv1", view_alias="default_local_text", is_current=True, recipe_id="canonical_recipe_v1")],
            "segments": [_Row(id="s1", segment_index=0, text="A")],
            "members": [],
            "chunks": [{"id": "c1", "document_chunk_number": 0, "text": "A", "authority_segment_id": "s1"}],
        },
    )
    row = _Row(id="doc1")
    result = repair_document_decomposition(object(), document_row=row, dry_run=False)
    assert result["action"] == "skip_canonical"
    assert result["summary_before"]["status"] == "canonical"


def test_repair_document_decomposition_relinks_missing_authority_conservatively(monkeypatch):
    class _DB:
        def __init__(self):
            self.added = []
            self.committed = 0

        def add(self, row):
            self.added.append(row)

        def commit(self):
            self.committed += 1

    db = _DB()
    chunk = _Row(id="c1", document_chunk_number=0, text="A", authority_segment_id=None)
    states = [
        {
            "versions": [_Row(id="v1")],
            "unit_views": [],
            "units": [],
            "segment_views": [_Row(id="sv1", view_alias="default_local_text", is_current=True, recipe_id="legacy_chunk_backfill_segments_v1")],
            "segments": [_Row(id="s1", segment_index=0, text="A")],
            "members": [],
            "chunks": [chunk],
        },
        {
            "versions": [_Row(id="v1")],
            "unit_views": [],
            "units": [],
            "segment_views": [_Row(id="sv1", view_alias="default_local_text", is_current=True, recipe_id="legacy_chunk_backfill_segments_v1")],
            "segments": [_Row(id="s1", segment_index=0, text="A")],
            "members": [],
            "chunks": [chunk],
        },
    ]
    def _next_state(database, document_id):
        if len(states) > 1:
            return states.pop(0)
        return states[0]

    monkeypatch.setattr(
        "QueryLake.runtime.document_decomposition.fetch_document_decomposition_state",
        _next_state,
    )
    row = _Row(id="doc1")
    result = repair_document_decomposition(db, document_row=row, dry_run=False)
    assert result["action"] == "relinked_chunk_authority"
    assert result["relinked_count"] == 1
    assert chunk.authority_segment_id == "s1"
    assert db.committed == 1


def test_repair_document_decomposition_script_json(monkeypatch, capsys):
    monkeypatch.setattr(
        "scripts.repair_document_decomposition.initialize_database_engine",
        lambda **kwargs: (object(), None),
    )
    monkeypatch.setattr(
        "scripts.repair_document_decomposition._load_documents",
        lambda database, document_ids, limit, offset=0: [_Row(id="doc1"), _Row(id="doc2")],
    )
    monkeypatch.setattr(
        "scripts.repair_document_decomposition.repair_document_decomposition",
        lambda database, document_row, dry_run: {"document_id": document_row.id, "action": "plan_repair"},
    )
    assert main(["--json"]) == 0
    payload = capsys.readouterr().out
    assert '"documents_considered": 2' in payload
    assert '"planned_count": 2' in payload

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.document_decomposition_doctor import main


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return list(self._rows)


class _Doc:
    def __init__(self, doc_id: str, creation_timestamp: float):
        self.id = doc_id
        self.creation_timestamp = creation_timestamp


class _Session:
    def exec(self, stmt):
        text = str(stmt)
        if "FROM document_raw" in text:
            return _Result([_Doc("doc1", 1.0), _Doc("doc2", 2.0)])
        raise AssertionError(f"Unexpected statement: {text}")


def test_document_decomposition_doctor_json(monkeypatch, capsys):
    monkeypatch.setattr(
        "scripts.document_decomposition_doctor.initialize_database_engine",
        lambda **kwargs: (_Session(), None),
    )
    monkeypatch.setattr(
        "scripts.document_decomposition_doctor.fetch_document_decomposition_state",
        lambda db, document_id: {
            "versions": [object()] if document_id == "doc1" else [],
            "unit_views": [object()] if document_id == "doc1" else [],
            "units": [object()],
            "segment_views": [],
            "segments": [],
            "members": [],
            "chunks": [{"id": "c1", "document_chunk_number": 0, "text": "x", "authority_segment_id": None}],
        },
    )
    monkeypatch.setattr(
        "scripts.document_decomposition_doctor.summarize_document_decomposition_rows",
        lambda document_id, **state: {
            "document_id": document_id,
            "status": "legacy_only" if document_id == "doc2" else "partial",
            "chunk_count": 1,
            "authority_linked_chunk_count": 0,
            "segment_count": 0,
            "default_segment_view_count": 0,
        },
    )

    assert main(["--json"]) == 0
    out = capsys.readouterr().out
    assert '"documents_scanned": 2' in out
    assert '"empty_documents": 0' in out
    assert '"legacy_only_documents": 1' in out


def test_document_decomposition_doctor_summary_only_omits_documents(monkeypatch, capsys):
    monkeypatch.setattr(
        "scripts.document_decomposition_doctor.initialize_database_engine",
        lambda **kwargs: (_Session(), None),
    )
    monkeypatch.setattr(
        "scripts.document_decomposition_doctor.fetch_document_decomposition_state",
        lambda db, document_id: {
            "versions": [], "unit_views": [], "units": [], "segment_views": [], "segments": [], "members": [],
            "chunks": [],
        },
    )
    monkeypatch.setattr(
        "scripts.document_decomposition_doctor.summarize_document_decomposition_rows",
        lambda document_id, **state: {"document_id": document_id, "status": "empty", "chunk_count": 0, "authority_linked_chunk_count": 0, "segment_count": 0, "default_segment_view_count": 0},
    )

    assert main(["--json", "--summary-only"]) == 0
    out = capsys.readouterr().out
    assert '"aggregate"' in out
    assert '"documents"' not in out

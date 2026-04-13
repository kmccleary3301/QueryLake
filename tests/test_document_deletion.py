from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.api.document_deletion import delete_collection_documents, delete_document_dependents


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return list(self._rows)


class _DummySession:
    def __init__(self):
        self.version_ids = ["ver1"]
        self.segment_ids = ["seg1", "seg2"]
        self.calls = []
        self.deleted = []

    def exec(self, stmt):
        text = str(stmt)
        self.calls.append(text)
        if "SELECT document_version.id" in text:
            return _Result(self.version_ids)
        if "SELECT document_segment.id" in text:
            return _Result(self.segment_ids)
        return _Result([])

    def delete(self, row):
        self.deleted.append(row.id)


class _Doc:
    def __init__(self, doc_id, blob_id=None):
        self.id = doc_id
        self.blob_id = blob_id


def test_delete_document_dependents_runs_fk_safe_order():
    db = _DummySession()
    delete_document_dependents(db, "doc1")
    rendered = "\n".join(db.calls)
    assert "SELECT document_version.id" in rendered
    assert "SELECT document_segment.id" in rendered
    assert "DELETE FROM embedding_record" in rendered
    assert "DELETE FROM segment_edge" in rendered
    assert "DELETE FROM document_segment" in rendered
    assert "DELETE FROM document_artifact" in rendered
    assert "DELETE FROM segmentation_run" in rendered
    assert "DELETE FROM document_version" in rendered
    assert "DELETE FROM documentchunk" in rendered


def test_delete_collection_documents_deletes_each_document(monkeypatch):
    db = _DummySession()
    blob_deleted = []
    monkeypatch.setattr(
        "QueryLake.api.document_deletion.encryption.aes_delete_file_from_zip_blob",
        lambda database, document_id, commit=True: blob_deleted.append((document_id, commit)),
    )
    docs = [_Doc("doc1", blob_id=None), _Doc("doc2", blob_id="blob2")]
    delete_collection_documents(db, docs)
    assert db.deleted == ["doc1", "doc2"]
    assert blob_deleted == [("doc2", False)]

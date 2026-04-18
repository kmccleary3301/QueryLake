from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.document_decomposition_migration_status import main


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
    def __init__(self):
        self.seen = []

    def exec(self, stmt):
        text = str(stmt)
        self.seen.append(text)
        if 'FROM document_raw' in text:
            return _Result([_Doc('doc1', 1.0), _Doc('doc2', 2.0)])
        raise AssertionError(text)


def test_document_decomposition_migration_status_json(monkeypatch, capsys):
    session = _Session()
    monkeypatch.setattr(
        'scripts.document_decomposition_migration_status.initialize_database_engine',
        lambda **kwargs: (session, None),
    )
    monkeypatch.setattr(
        'scripts.document_decomposition_migration_status.summarize_many_documents',
        lambda db, document_ids: [
            {'document_id': 'doc1', 'status': 'partial'},
            {'document_id': 'doc2', 'status': 'legacy_only'},
        ],
    )
    monkeypatch.setattr(
        'scripts.document_decomposition_migration_status.aggregate_decomposition_status',
        lambda summaries: {
            'documents_scanned': 2,
            'empty_documents': 0,
            'canonical_documents': 0,
            'backfilled_documents': 0,
            'legacy_only_documents': 1,
            'partial_documents': 1,
            'chunks_missing_authority_links_documents': 0,
            'segments_missing_default_view_documents': 0,
            'unknown_documents': 0,
            'status_order': [],
        },
    )
    monkeypatch.setattr(
        'scripts.document_decomposition_migration_status.backfill_document_decomposition',
        lambda db, document_row, dry_run: {'document_id': document_row.id, 'action': 'plan_backfill' if document_row.id == 'doc1' else 'skip_already_canonical'},
    )
    assert main(['--json']) == 0
    out = capsys.readouterr().out
    assert '"documents_scanned": 2' in out
    assert '"empty_documents": 0' in out
    assert '"planned_count": 1' in out


def test_document_decomposition_migration_status_applies_offset(monkeypatch):
    session = _Session()
    seen = {}
    monkeypatch.setattr(
        'scripts.document_decomposition_migration_status.initialize_database_engine',
        lambda **kwargs: (session, None),
    )
    monkeypatch.setattr(
        'scripts.document_decomposition_migration_status._load_documents',
        lambda database, document_ids, limit, offset=0: seen.update({
            'document_ids': document_ids,
            'limit': limit,
            'offset': offset,
        }) or [_Doc('doc1', 1.0), _Doc('doc2', 2.0)],
    )
    monkeypatch.setattr(
        'scripts.document_decomposition_migration_status.summarize_many_documents',
        lambda db, document_ids: [],
    )
    monkeypatch.setattr(
        'scripts.document_decomposition_migration_status.aggregate_decomposition_status',
        lambda summaries: {
            'documents_scanned': 0,
            'empty_documents': 0,
            'canonical_documents': 0,
            'backfilled_documents': 0,
            'legacy_only_documents': 0,
            'partial_documents': 0,
            'chunks_missing_authority_links_documents': 0,
            'segments_missing_default_view_documents': 0,
            'unknown_documents': 0,
            'status_order': [],
        },
    )
    monkeypatch.setattr(
        'scripts.document_decomposition_migration_status.backfill_document_decomposition',
        lambda db, document_row, dry_run: {'document_id': document_row.id, 'action': 'skip_noop'},
    )

    assert main(['--json', '--limit', '10', '--offset', '7']) == 0
    assert seen == {'document_ids': [], 'limit': 10, 'offset': 7}


def test_document_decomposition_migration_status_summary_only_omits_details(monkeypatch, capsys):
    session = _Session()
    monkeypatch.setattr(
        'scripts.document_decomposition_migration_status.initialize_database_engine',
        lambda **kwargs: (session, None),
    )
    monkeypatch.setattr(
        'scripts.document_decomposition_migration_status.summarize_many_documents',
        lambda db, document_ids: [],
    )
    monkeypatch.setattr(
        'scripts.document_decomposition_migration_status.aggregate_decomposition_status',
        lambda summaries: {
            'documents_scanned': 0,
            'empty_documents': 0,
            'canonical_documents': 0,
            'backfilled_documents': 0,
            'legacy_only_documents': 0,
            'partial_documents': 0,
            'chunks_missing_authority_links_documents': 0,
            'segments_missing_default_view_documents': 0,
            'unknown_documents': 0,
            'status_order': [],
        },
    )
    monkeypatch.setattr(
        'scripts.document_decomposition_migration_status.backfill_document_decomposition',
        lambda db, document_row, dry_run: {'document_id': document_row.id, 'action': 'skip_noop'},
    )

    assert main(['--json', '--summary-only']) == 0
    out = capsys.readouterr().out
    assert '"aggregate"' in out
    assert '"documents"' not in out
    assert '"results"' not in out

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.document_decomposition_uniqueness_audit import main


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _Session:
    def exec(self, stmt):
        return _Result(["doc1", "doc2"])


def test_uniqueness_audit_script_passes_scoped_document_ids(monkeypatch, capsys):
    monkeypatch.setattr(
        'scripts.document_decomposition_uniqueness_audit.initialize_database_engine',
        lambda **kwargs: (_Session(), None),
    )
    monkeypatch.setattr(
        'scripts.document_decomposition_uniqueness_audit.audit_segment_uniqueness_readiness',
        lambda database, document_ids=None, scope_limit=None, scope_offset=0: {
            'scope_mode': 'documents',
            'scope_document_count': len(document_ids),
            'segment_count': 5,
            'null_segment_view_count': 0,
            'duplicate_key_count': 0,
            'default_view_conflict_count': 0,
            'chunk_authority_missing_count': 0,
            'chunk_authority_orphan_count': 0,
            'legacy_constraint_present': False,
            'proposed_constraint_present': True,
            'compatibility_normalized': True,
            'ready_for_constraint_swap': True,
            'ready_for_swap': True,
        },
    )
    assert main(['--document-id', 'doc1', '--document-id', 'doc2', '--json']) == 0
    out = capsys.readouterr().out
    assert '"scope_mode": "documents"' in out
    assert '"scope_document_count": 2' in out



def test_uniqueness_audit_script_passes_scope_limit_and_offset(monkeypatch, capsys):
    monkeypatch.setattr(
        'scripts.document_decomposition_uniqueness_audit.initialize_database_engine',
        lambda **kwargs: (_Session(), None),
    )
    captured = {}

    def _audit(database, document_ids=None, scope_limit=None, scope_offset=0):
        captured['document_ids'] = document_ids
        captured['scope_limit'] = scope_limit
        captured['scope_offset'] = scope_offset
        return {
            'scope_mode': 'documents',
            'scope_document_count': 2,
            'segment_count': 5,
            'null_segment_view_count': 0,
            'duplicate_key_count': 0,
            'default_view_conflict_count': 0,
            'chunk_authority_missing_count': 0,
            'chunk_authority_orphan_count': 0,
            'legacy_constraint_present': False,
            'proposed_constraint_present': True,
            'compatibility_normalized': True,
            'ready_for_constraint_swap': True,
            'ready_for_swap': True,
        }

    monkeypatch.setattr(
        'scripts.document_decomposition_uniqueness_audit.audit_segment_uniqueness_readiness',
        _audit,
    )
    assert main(['--limit', '2', '--offset', '10', '--json']) == 0
    out = capsys.readouterr().out
    assert '"scope_mode": "documents"' in out
    assert captured == {'document_ids': None, 'scope_limit': 2, 'scope_offset': 10}

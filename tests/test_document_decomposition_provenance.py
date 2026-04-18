from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.document_decomposition_provenance import main
from QueryLake.runtime.document_decomposition import build_chunk_authority_provenance


class _Row:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class _Session:
    pass


def test_build_chunk_authority_provenance_maps_chunk_to_segment_and_members():
    chunks = [
        {'id': 'c1', 'document_chunk_number': 0, 'text': 'hello', 'md': {}, 'authority_segment_id': 's1'}
    ]
    segments = [_Row(id='s1', segment_view_id='sv1', segment_type='chunk', segment_index=0)]
    segment_views = [_Row(id='sv1', view_alias='default_local_text')]
    members = [_Row(segment_id='s1', unit_id='u1', member_index=0, role='main', unit_start_char=0, unit_end_char=5)]
    units = [_Row(id='u1', unit_index=0)]
    payload = build_chunk_authority_provenance(chunks=chunks, segments=segments, segment_views=segment_views, members=members, units=units)
    assert payload[0]['chunk_id'] == 'c1'
    assert payload[0]['authority_segment_id'] == 's1'
    assert payload[0]['segment_view_alias'] == 'default_local_text'
    assert payload[0]['member_count'] == 1
    assert payload[0]['members'][0]['unit_id'] == 'u1'
    assert payload[0]['members'][0]['unit_index'] == 0


def test_provenance_script_uses_runtime_helper(monkeypatch, capsys):
    monkeypatch.setattr('scripts.document_decomposition_provenance.initialize_database_engine', lambda **kwargs: (_Session(), None))
    monkeypatch.setattr(
        'scripts.document_decomposition_provenance.fetch_document_chunk_authority_provenance',
        lambda database, document_id: {'document_id': document_id, 'record_count': 1, 'records': [{'chunk_id': 'c1'}]},
    )
    assert main(['--document-id', 'doc1', '--json']) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload['document_id'] == 'doc1'
    assert payload['record_count'] == 1
    assert payload['records'][0]['chunk_id'] == 'c1'

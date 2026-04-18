from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.document_decomposition_rollout_campaign import main


class _Database:
    pass


def test_rollout_campaign_writes_manifest_and_window_artifacts(monkeypatch, tmp_path):
    monkeypatch.setattr(
        'scripts.document_decomposition_rollout_campaign.initialize_database_engine',
        lambda **kwargs: (_Database(), None),
    )

    def fake_run_rollout_window(database, *, limit, offset, batch_size, parity_sample_size):
        before = {'documents_scanned': limit, 'canonical_documents': 0, 'backfilled_documents': 0, 'legacy_only_documents': limit, 'partial_documents': 0, 'chunks_missing_authority_links_documents': 0}
        after = {'documents_scanned': limit, 'canonical_documents': 0, 'backfilled_documents': limit, 'legacy_only_documents': 0, 'partial_documents': 0, 'chunks_missing_authority_links_documents': 0}
        return {
            'limit': limit,
            'offset': offset,
            'batch_size': batch_size,
            'parity_sample_size': parity_sample_size,
            'before': before,
            'aggregate_before': before,
            'after': after,
            'aggregate_after': after,
            'legacy_ids_initial_count': limit,
            'batch_count': 1,
            'batch_backfilled_total': limit,
            'batch_skipped_total': 0,
            'parity_summary': {'pass_count': 1, 'warn_count': 0, 'fail_count': 0},
            'batches': [
                {
                    'batch_index': 0,
                    'documents_considered': limit,
                    'backfilled_count': limit,
                    'relinked_count': 0,
                    'skipped_count': 0,
                    'document_ids': ['d1'],
                    'parity_sample': [{'document_id': 'd1', 'verdict': 'pass'}],
                }
            ],
        }

    monkeypatch.setattr(
        'scripts.document_decomposition_rollout_campaign.run_rollout_window',
        fake_run_rollout_window,
    )

    manifest_path = tmp_path / 'manifest.json'
    output_dir = tmp_path / 'windows'
    assert main([
        '--start-offset', '100',
        '--window-size', '10',
        '--window-count', '2',
        '--output-dir', str(output_dir),
        '--manifest-path', str(manifest_path),
        '--json',
    ]) == 0

    manifest = json.loads(manifest_path.read_text())
    assert manifest['total_windows_completed'] == 2
    assert manifest['last_offset_completed'] == 110
    window_files = list(output_dir.glob('document_decomposition_rollout_window_offset*_limit10.json'))
    assert len(window_files) == 2

    payload = json.loads(window_files[0].read_text())
    assert payload['before']['legacy_only_documents'] == 10
    assert payload['after']['backfilled_documents'] == 10
    assert payload['batch_backfilled_total'] == 10
    assert payload['batch_skipped_total'] == 0
    assert payload['parity_summary']['pass_count'] == 1
    assert payload['parity_summary']['warn_count'] == 0
    assert payload['parity_summary']['fail_count'] == 0

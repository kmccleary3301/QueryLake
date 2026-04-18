from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.document_decomposition_campaign_status import main


def test_campaign_status_reports_audited_and_committed_boundaries(tmp_path, capsys):
    manifest = {
        'total_windows_completed': 2,
        'last_offset_completed': 140000,
        'windows': [
            {'offset': 115000, 'limit': 25000, 'batch_backfilled_total': 25000, 'batch_skipped_total': 0, 'parity_pass_count': 500, 'parity_warn_count': 0, 'parity_fail_count': 0},
            {'offset': 140000, 'limit': 25000, 'batch_backfilled_total': 25000, 'batch_skipped_total': 0, 'parity_pass_count': 500, 'parity_warn_count': 0, 'parity_fail_count': 0},
        ],
    }
    doctor = {'aggregate': {'documents_scanned': 165000, 'backfilled_documents': 165000, 'legacy_only_documents': 0, 'partial_documents': 0, 'chunks_missing_authority_links_documents': 0}}
    migration = {'dry_run': {'documents_considered': 165000, 'planned_count': 0, 'relinked_count': 0, 'skipped_count': 165000}}
    scoped = {'compatibility_normalized': True, 'duplicate_key_count': 0, 'null_segment_view_count': 0, 'chunk_authority_missing_count': 0}
    global_audit = {'compatibility_normalized': False, 'chunk_authority_missing_count': 123}

    manifest_path = tmp_path / 'manifest.json'
    doctor_path = tmp_path / 'doctor.json'
    migration_path = tmp_path / 'migration.json'
    scoped_path = tmp_path / 'scoped.json'
    global_path = tmp_path / 'global.json'
    manifest_path.write_text(json.dumps(manifest))
    doctor_path.write_text(json.dumps(doctor))
    migration_path.write_text(json.dumps(migration))
    scoped_path.write_text(json.dumps(scoped))
    global_path.write_text(json.dumps(global_audit))

    assert main([
        '--audited-limit', '165000',
        '--audit-date', '2026-04-15',
        '--manifest-path', str(manifest_path),
        '--doctor-path', str(doctor_path),
        '--migration-status-path', str(migration_path),
        '--scoped-audit-path', str(scoped_path),
        '--global-audit-path', str(global_path),
        '--json',
    ]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload['latest_fully_audited_boundary'] == '0-164999'
    assert payload['latest_committed_boundary'] == '0-164999'
    assert payload['committed_ahead_of_audited_documents'] == 0
    assert payload['campaign_backfilled_total'] == 50000
    assert payload['scoped_backfilled_documents'] == 165000
    assert payload['scoped_legacy_only_documents'] == 0
    assert payload['scoped_chunks_missing_authority_links_documents'] == 0
    assert payload['campaign_parity_pass_total'] == 1000
    assert payload['global_chunk_authority_missing_count'] == 123

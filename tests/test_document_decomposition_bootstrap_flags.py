from pathlib import Path


DECOMPOSITION_SCRIPTS = [
    'scripts/document_decomposition_doctor.py',
    'scripts/document_decomposition_migration_status.py',
    'scripts/document_decomposition_uniqueness_audit.py',
    'scripts/rollout_document_decomposition_backfill.py',
    'scripts/document_decomposition_rollout_campaign.py',
    'scripts/backfill_document_decomposition.py',
    'scripts/repair_document_decomposition.py',
    'scripts/document_decomposition_parity.py',
    'scripts/document_decomposition_apply_uniqueness_swap.py',
    'scripts/document_decomposition_provenance.py',
]


def test_decomposition_scripts_disable_unrelated_sparse_bootstrap():
    missing = []
    for rel_path in DECOMPOSITION_SCRIPTS:
        text = Path(rel_path).read_text(encoding='utf-8')
        if 'ensure_sparse_bootstrap=False' not in text:
            missing.append(rel_path)
    assert missing == []

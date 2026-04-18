#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open() as f:
        return json.load(f)


def _default_audited_path(prefix: str, audited_limit: int, audit_date: str) -> Path:
    return Path(f"docs_tmp/RAG/CHUNKING/{prefix}_{audited_limit}_{audit_date}.json")


def _compute_boundaries(manifest: Dict[str, Any], audited_limit: int) -> Dict[str, Any]:
    windows = manifest.get('windows', [])
    last_window = windows[-1] if windows else None
    if last_window is not None:
        committed_offset = int(last_window['offset'])
        committed_limit = int(last_window['limit'])
        latest_committed_boundary_end = committed_offset + committed_limit - 1
    else:
        committed_offset = None
        committed_limit = None
        latest_committed_boundary_end = None
    latest_audited_boundary_end = int(audited_limit) - 1
    committed_ahead = None
    if latest_committed_boundary_end is not None:
        committed_ahead = max(0, latest_committed_boundary_end - latest_audited_boundary_end)
    return {
        'latest_fully_audited_boundary': f"0-{latest_audited_boundary_end}",
        'latest_fully_audited_document_count': int(audited_limit),
        'latest_committed_boundary': None if latest_committed_boundary_end is None else f"0-{latest_committed_boundary_end}",
        'latest_committed_offset': committed_offset,
        'latest_committed_limit': committed_limit,
        'committed_ahead_of_audited_documents': committed_ahead,
    }


def _compute_campaign_totals(manifest: Dict[str, Any]) -> Dict[str, Any]:
    windows = manifest.get('windows', [])
    return {
        'manifest_completed_windows': int(manifest.get('total_windows_completed', len(windows))),
        'manifest_last_offset_completed': manifest.get('last_offset_completed'),
        'campaign_backfilled_total': sum(int(w.get('batch_backfilled_total', 0) or 0) for w in windows),
        'campaign_skipped_total': sum(int(w.get('batch_skipped_total', 0) or 0) for w in windows),
        'campaign_parity_pass_total': sum(int(w.get('parity_pass_count', 0) or 0) for w in windows),
        'campaign_parity_warn_total': sum(int(w.get('parity_warn_count', 0) or 0) for w in windows),
        'campaign_parity_fail_total': sum(int(w.get('parity_fail_count', 0) or 0) for w in windows),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Summarize document decomposition rollout status from manifest and audited checkpoint artifacts.')
    parser.add_argument('--audited-limit', type=int, required=True)
    parser.add_argument('--audit-date', required=True)
    parser.add_argument('--manifest-path', default='docs_tmp/RAG/CHUNKING/DOCUMENT_DECOMPOSITION_TRANCHE1_ROLLOUT_CAMPAIGN_2026-04-13.json')
    parser.add_argument('--doctor-path')
    parser.add_argument('--migration-status-path')
    parser.add_argument('--scoped-audit-path')
    parser.add_argument('--global-audit-path')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)

    doctor_path = Path(args.doctor_path) if args.doctor_path else _default_audited_path('DOCUMENT_DECOMPOSITION_TRANCHE1_DOCTOR', args.audited_limit, args.audit_date)
    migration_path = Path(args.migration_status_path) if args.migration_status_path else _default_audited_path('DOCUMENT_DECOMPOSITION_TRANCHE1_MIGRATION_STATUS', args.audited_limit, args.audit_date)
    scoped_path = Path(args.scoped_audit_path) if args.scoped_audit_path else _default_audited_path('DOCUMENT_DECOMPOSITION_TRANCHE1_UNIQUENESS_AUDIT_SCOPED', args.audited_limit, args.audit_date)
    global_path = Path(args.global_audit_path) if args.global_audit_path else Path(f"docs_tmp/RAG/CHUNKING/DOCUMENT_DECOMPOSITION_TRANCHE1_UNIQUENESS_AUDIT_GLOBAL_{args.audit_date}.json")

    manifest = _load_json(Path(args.manifest_path))
    doctor = _load_json(doctor_path)
    migration = _load_json(migration_path)
    scoped = _load_json(scoped_path)
    global_audit = _load_json(global_path)

    doctor_aggregate = doctor.get('aggregate', {})
    payload = {
        **_compute_boundaries(manifest, args.audited_limit),
        **_compute_campaign_totals(manifest),
        'audited_limit': int(args.audited_limit),
        'audit_date': args.audit_date,
        'scoped_compatibility_normalized': scoped.get('compatibility_normalized'),
        'scoped_duplicate_key_count': scoped.get('duplicate_key_count'),
        'scoped_null_segment_view_count': scoped.get('null_segment_view_count'),
        'scoped_chunk_authority_missing_count': scoped.get('chunk_authority_missing_count'),
        'scoped_backfilled_documents': doctor_aggregate.get('backfilled_documents'),
        'scoped_legacy_only_documents': doctor_aggregate.get('legacy_only_documents'),
        'scoped_partial_documents': doctor_aggregate.get('partial_documents'),
        'scoped_chunks_missing_authority_links_documents': doctor_aggregate.get('chunks_missing_authority_links_documents'),
        'global_compatibility_normalized': global_audit.get('compatibility_normalized'),
        'global_chunk_authority_missing_count': global_audit.get('chunk_authority_missing_count'),
        'doctor_aggregate': doctor_aggregate,
        'migration_dry_run': {
            'documents_considered': migration.get('dry_run', {}).get('documents_considered'),
            'planned_count': migration.get('dry_run', {}).get('planned_count'),
            'relinked_count': migration.get('dry_run', {}).get('relinked_count'),
            'skipped_count': migration.get('dry_run', {}).get('skipped_count'),
        },
    }

    if args.json:
        print(json.dumps(payload, indent=2))
        return 0

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

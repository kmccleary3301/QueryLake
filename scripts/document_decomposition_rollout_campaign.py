#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.database.create_db_session import initialize_database_engine
from scripts.rollout_document_decomposition_backfill import run_rollout_window


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _default_window_artifact_path(output_dir: Path, *, offset: int, limit: int) -> Path:
    return output_dir / f'document_decomposition_rollout_window_offset{offset}_limit{limit}.json'


def _summarize_window(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'offset': int(payload['offset']),
        'limit': int(payload['limit']),
        'aggregate_before': payload['aggregate_before'],
        'aggregate_after': payload['aggregate_after'],
        'legacy_ids_initial_count': int(payload['legacy_ids_initial_count']),
        'batch_count': int(payload['batch_count']),
        'batch_backfilled_total': sum(int(b['backfilled_count']) for b in payload['batches']),
        'batch_skipped_total': sum(int(b['skipped_count']) for b in payload['batches']),
        'parity_fail_count': sum(1 for b in payload['batches'] for r in b['parity_sample'] if r.get('verdict') == 'fail'),
        'parity_warn_count': sum(1 for b in payload['batches'] for r in b['parity_sample'] if r.get('verdict') == 'warn'),
        'parity_pass_count': sum(1 for b in payload['batches'] for r in b['parity_sample'] if r.get('verdict') == 'pass'),
    }


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Checkpointed campaign runner for document decomposition historical rollout.')
    parser.add_argument('--start-offset', type=int, default=0)
    parser.add_argument('--window-size', type=int, default=5000)
    parser.add_argument('--window-count', type=int, default=1)
    parser.add_argument('--batch-size', type=int, default=250)
    parser.add_argument('--parity-sample-size', type=int, default=5)
    parser.add_argument('--output-dir', default='docs_tmp/RAG/CHUNKING')
    parser.add_argument('--manifest-path', default='docs_tmp/RAG/CHUNKING/DOCUMENT_DECOMPOSITION_TRANCHE1_ROLLOUT_CAMPAIGN_2026-04-13.json')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = Path(args.manifest_path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    if manifest_path.exists() and manifest_path.stat().st_size:
        manifest = json.loads(manifest_path.read_text())
    else:
        manifest = {
            'created_at': _utc_now(),
            'windows': [],
        }

    database, _ = initialize_database_engine(ensure_sparse_bootstrap=False)
    windows_out = []
    for i in range(int(args.window_count)):
        offset = int(args.start_offset) + i * int(args.window_size)
        payload = run_rollout_window(
            database,
            limit=int(args.window_size),
            offset=offset,
            batch_size=int(args.batch_size),
            parity_sample_size=int(args.parity_sample_size),
        )
        artifact_path = _default_window_artifact_path(output_dir, offset=offset, limit=int(args.window_size))
        artifact_path.write_text(json.dumps(payload, indent=2))
        window_summary = {
            **_summarize_window(payload),
            'artifact_path': str(artifact_path),
            'completed_at': _utc_now(),
        }
        manifest['windows'].append(window_summary)
        manifest['updated_at'] = _utc_now()
        manifest['last_offset_completed'] = offset
        manifest['total_windows_completed'] = len(manifest['windows'])
        manifest_path.write_text(json.dumps(manifest, indent=2))
        windows_out.append(window_summary)

    result = {
        'manifest_path': str(manifest_path),
        'windows_completed_now': windows_out,
        'total_windows_completed': len(manifest['windows']),
    }
    if args.json:
        print(json.dumps(result, indent=2))
        return 0
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

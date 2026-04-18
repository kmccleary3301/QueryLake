#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlmodel import select

from QueryLake.database.create_db_session import initialize_database_engine
from QueryLake.database.sql_db_tables import document_raw
from QueryLake.runtime.document_decomposition import (
    aggregate_decomposition_status,
    backfill_document_decomposition,
    compute_chunk_segment_parity,
    fetch_document_decomposition_state,
    summarize_many_documents,
)


def _load_documents(database, *, limit: int, offset: int = 0) -> List[document_raw]:
    stmt = select(document_raw).order_by(document_raw.creation_timestamp.desc())
    if offset:
        stmt = stmt.offset(int(offset))
    stmt = stmt.limit(limit)
    return list(database.exec(stmt).all())


def _sample_ids(doc_ids: List[str], sample_size: int) -> List[str]:
    if sample_size <= 0 or not doc_ids:
        return []
    if len(doc_ids) <= sample_size:
        return list(doc_ids)
    step = max(1, len(doc_ids) // sample_size)
    sample = [doc_ids[i] for i in range(0, len(doc_ids), step)]
    return sample[:sample_size]


def run_rollout_window(
    database,
    *,
    limit: int,
    offset: int = 0,
    batch_size: int = 250,
    parity_sample_size: int = 5,
) -> dict:
    docs = _load_documents(database, limit=int(limit), offset=int(offset))
    doc_ids = [str(row.id) for row in docs]
    summaries_before = summarize_many_documents(database, document_ids=doc_ids)
    aggregate_before = aggregate_decomposition_status(summaries_before)
    legacy_ids = [row['document_id'] for row in summaries_before if row['status'] == 'legacy_only']

    batches = [legacy_ids[i:i + int(batch_size)] for i in range(0, len(legacy_ids), int(batch_size))]
    batch_results = []
    for batch_index, batch_ids in enumerate(batches):
        batch_id_set = set(batch_ids)
        batch_docs = [row for row in docs if str(row.id) in batch_id_set]
        results = [backfill_document_decomposition(database, document_row=row, dry_run=False) for row in batch_docs]
        parity_ids = _sample_ids(batch_ids, int(parity_sample_size))
        parity = []
        for document_id in parity_ids:
            state = fetch_document_decomposition_state(database, document_id=document_id)
            parity.append({
                'document_id': document_id,
                **compute_chunk_segment_parity(chunk_rows=state['chunks'], segment_rows=state['segments']),
            })
        batch_results.append({
            'batch_index': batch_index,
            'documents_considered': len(results),
            'backfilled_count': sum(1 for row in results if row.get('action') == 'backfilled'),
            'relinked_count': sum(1 for row in results if row.get('action') == 'relinked_chunk_authority'),
            'skipped_count': sum(1 for row in results if str(row.get('action', '')).startswith('skip_')),
            'document_ids': batch_ids,
            'parity_sample': parity,
        })

    summaries_after = summarize_many_documents(database, document_ids=doc_ids)
    aggregate_after = aggregate_decomposition_status(summaries_after)
    parity_pass_count = sum(1 for batch in batch_results for row in batch['parity_sample'] if row.get('verdict') == 'pass')
    parity_warn_count = sum(1 for batch in batch_results for row in batch['parity_sample'] if row.get('verdict') == 'warn')
    parity_fail_count = sum(1 for batch in batch_results for row in batch['parity_sample'] if row.get('verdict') == 'fail')
    batch_backfilled_total = sum(int(batch['backfilled_count']) for batch in batch_results)
    batch_skipped_total = sum(int(batch['skipped_count']) for batch in batch_results)
    return {
        'limit': int(limit),
        'offset': int(offset),
        'batch_size': int(batch_size),
        'parity_sample_size': int(parity_sample_size),
        'before': aggregate_before,
        'aggregate_before': aggregate_before,
        'after': aggregate_after,
        'aggregate_after': aggregate_after,
        'legacy_ids_initial_count': len(legacy_ids),
        'batch_count': len(batch_results),
        'batch_backfilled_total': batch_backfilled_total,
        'batch_skipped_total': batch_skipped_total,
        'parity_summary': {
            'pass_count': parity_pass_count,
            'warn_count': parity_warn_count,
            'fail_count': parity_fail_count,
        },
        'batches': batch_results,
    }


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Batch rollout for historical document decomposition backfill.')
    parser.add_argument('--limit', type=int, default=5000)
    parser.add_argument('--batch-size', type=int, default=250)
    parser.add_argument('--offset', type=int, default=0)
    parser.add_argument('--parity-sample-size', type=int, default=5)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)

    database, _ = initialize_database_engine(ensure_sparse_bootstrap=False)
    payload = run_rollout_window(
        database,
        limit=int(args.limit),
        offset=int(args.offset),
        batch_size=int(args.batch_size),
        parity_sample_size=int(args.parity_sample_size),
    )

    if args.json:
        print(json.dumps(payload, indent=2))
        return 0

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

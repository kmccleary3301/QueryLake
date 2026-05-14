#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.database.create_db_session import initialize_database_engine
from QueryLake.runtime.document_decomposition import (
    DEFAULT_LOCAL_TEXT_VIEW_ALIAS,
    build_operator_provenance_payload,
    fetch_document_operator_provenance,
    resolve_document_chunk_authority,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit operator-facing document decomposition provenance without SQL.")
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--document-id")
    target.add_argument("--chunk-id")
    parser.add_argument("--view-alias", default=DEFAULT_LOCAL_TEXT_VIEW_ALIAS)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    database, _ = initialize_database_engine(ensure_sparse_bootstrap=False)
    if args.document_id:
        payload = fetch_document_operator_provenance(
            database,
            document_id=args.document_id,
            view_alias=args.view_alias,
        )
    else:
        resolution = resolve_document_chunk_authority(database, chunk_id=args.chunk_id)
        records = [] if resolution.segment is None else [resolution.segment]
        payload = build_operator_provenance_payload(
            representation_type="canonical_segment_text",
            document_id=resolution.document_id,
            records=records,
            source="document_chunk_authority",
        )
        payload["chunk_id"] = resolution.chunk_id
        payload["resolution_status"] = resolution.status
        payload["notes"] = list(resolution.notes)

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"schema={payload['schema_version']} document_id={payload.get('document_id')} records={payload['record_count']} anchors={payload['anchor_count']}")
        for record in payload.get("records", [])[:20]:
            print(f"segment={record.get('segment_id')} view={record.get('segment_view_alias')} type={record.get('segment_type')} index={record.get('segment_index')} members={record.get('member_count')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

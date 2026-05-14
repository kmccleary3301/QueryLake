#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Type

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.database.create_db_session import initialize_database_engine
from QueryLake.scanning.contracts import (
    ArtifactRef,
    PageRecord,
    Projection,
    RoutingDecision,
    ScanContract,
    ScanObject,
    ScanRun,
    ScannerEnvelope,
    validate_scanner_envelope,
)
from QueryLake.scanning.decomposition import persist_scanner_decomposition_rows
from QueryLake.scanning.decomposition import persist_document_linked_scanner_decomposition


def _dataclass_from_payload(cls: Type[Any], payload: Dict[str, Any]) -> Any:
    allowed = set(getattr(cls, "__dataclass_fields__", {}).keys())
    return cls(**{key: value for key, value in dict(payload or {}).items() if key in allowed})


def scanner_envelope_from_payload(payload: Dict[str, Any]) -> ScannerEnvelope:
    envelope = ScannerEnvelope(
        schema_version=str(payload.get("schema_version") or "scanner_envelope_v1"),
        scan_run=_dataclass_from_payload(ScanRun, payload.get("scan_run") or {}),
        contract=_dataclass_from_payload(ScanContract, payload.get("contract") or {}),
        artifacts=[_dataclass_from_payload(ArtifactRef, row) for row in payload.get("artifacts") or []],
        pages=[_dataclass_from_payload(PageRecord, row) for row in payload.get("pages") or []],
        objects=[_dataclass_from_payload(ScanObject, row) for row in payload.get("objects") or []],
        projections=[_dataclass_from_payload(Projection, row) for row in payload.get("projections") or []],
        routing=[_dataclass_from_payload(RoutingDecision, row) for row in payload.get("routing") or []],
        quality=dict(payload.get("quality") or {}),
        warnings=list(payload.get("warnings") or []),
        errors=list(payload.get("errors") or []),
    )
    validate_scanner_envelope(envelope)
    return envelope


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Persist scanner envelope decomposition rows when the document authority mapping is explicitly known."
    )
    parser.add_argument("--envelope-json", required=True)
    parser.add_argument("--document-version-id")
    parser.add_argument("--artifact-id")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    payload = json.loads(Path(args.envelope_json).read_text())
    if not isinstance(payload, dict):
        raise ValueError("scanner envelope JSON must be an object")
    envelope = scanner_envelope_from_payload(payload)
    database, _ = initialize_database_engine(ensure_sparse_bootstrap=False)
    if args.document_version_id and args.artifact_id:
        result = persist_scanner_decomposition_rows(
            database,
            document_version_id=args.document_version_id,
            artifact_id=args.artifact_id,
            envelope=envelope,
            enabled=True,
            commit=not bool(args.dry_run),
        )
    elif getattr(envelope.scan_run, "document_version_id", None):
        result = persist_document_linked_scanner_decomposition(
            database,
            envelope=envelope,
            enabled=True,
            commit=not bool(args.dry_run),
        )
    else:
        raise SystemExit(
            "scanner envelope has no document_version_id; pass --document-version-id and --artifact-id explicitly"
        )
    if args.dry_run:
        database.rollback()
        result = {**result, "dry_run": True, "persisted": False}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

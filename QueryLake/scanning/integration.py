from __future__ import annotations

from typing import Any, Dict, Optional

from QueryLake.scanning.contracts import ScannerEnvelope
from QueryLake.scanning.persistence import PersistedScannerEnvelope, summarize_scanner_envelope_payload


def build_scanner_job_result_metadata(
    envelope: ScannerEnvelope,
    persisted: PersistedScannerEnvelope,
    *,
    route_explanation_ref: Optional[str] = None,
) -> Dict[str, Any]:
    payload = persisted.payload
    summary = summarize_scanner_envelope_payload(payload)
    return {
        "scanner": {
            "schema_version": envelope.schema_version,
            "run_id": envelope.scan_run.run_id,
            "backend_id": envelope.scan_run.backend_id,
            "backend_class": envelope.scan_run.backend_class,
            "support_tier": envelope.scan_run.support_tier,
            "status": envelope.scan_run.status,
            "acquisition_mode": envelope.contract.acquisition_mode,
            "legacy_output_contract": envelope.contract.legacy_output_contract,
            "raw_backend_contract": envelope.contract.raw_backend_contract,
            "scanner_envelope_artifact_id": persisted.envelope_ref.artifact_id,
            "scanner_envelope_cas": persisted.envelope_ref.storage_ref,
            "route_explanation_ref": route_explanation_ref,
            "summary": summary,
        }
    }


def build_scanner_document_artifact_payload(persisted: PersistedScannerEnvelope) -> Dict[str, Any]:
    ref = persisted.envelope_ref
    return {
        "artifact_type": ref.artifact_type,
        "modality": "document_scan",
        "storage_ref": ref.storage_ref,
        "text": None,
        "md": ref.md,
    }


def build_scanner_enriched_ocr_done_payload(
    existing_payload: Dict[str, Any],
    envelope: ScannerEnvelope,
    persisted: PersistedScannerEnvelope,
) -> Dict[str, Any]:
    enriched = dict(existing_payload or {})
    enriched["scanner"] = build_scanner_job_result_metadata(envelope, persisted)["scanner"]
    return enriched

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol

from QueryLake.scanning.contracts import ArtifactRef, ScannerEnvelope, validate_scanner_envelope


SCANNER_ENVELOPE_ARTIFACT_TYPE = "scanner_envelope"
SCANNER_RAW_PAYLOAD_ARTIFACT_TYPE = "scanner_raw_payload"
SCANNER_CANONICAL_MARKDOWN_ARTIFACT_TYPE = "scanner_canonical_markdown"
SCANNER_CANONICAL_TEXT_ARTIFACT_TYPE = "scanner_canonical_text"
SCANNER_LAYOUT_GRAPH_ARTIFACT_TYPE = "scanner_layout_graph"
SCANNER_STRUCTURED_FIELDS_ARTIFACT_TYPE = "scanner_structured_fields"
SCANNER_SHADOW_RESULT_ARTIFACT_TYPE = "scanner_shadow_result"

SCANNER_ARTIFACT_TYPES = {
    SCANNER_ENVELOPE_ARTIFACT_TYPE,
    SCANNER_RAW_PAYLOAD_ARTIFACT_TYPE,
    SCANNER_CANONICAL_MARKDOWN_ARTIFACT_TYPE,
    SCANNER_CANONICAL_TEXT_ARTIFACT_TYPE,
    SCANNER_LAYOUT_GRAPH_ARTIFACT_TYPE,
    SCANNER_STRUCTURED_FIELDS_ARTIFACT_TYPE,
    SCANNER_SHADOW_RESULT_ARTIFACT_TYPE,
}


class ScannerObjectStore(Protocol):
    def put_bytes(self, data: bytes) -> str:
        ...

    def get_bytes(self, cas: str) -> Optional[bytes]:
        ...


@dataclass(frozen=True)
class PersistedScannerEnvelope:
    envelope_ref: ArtifactRef
    payload: Dict[str, Any]

    def to_payload(self) -> Dict[str, Any]:
        return {"envelope_ref": self.envelope_ref.to_payload(), "payload": self.payload}


def scanner_envelope_to_json_bytes(envelope: ScannerEnvelope) -> bytes:
    """Serialize a validated scanner envelope to stable UTF-8 JSON bytes."""

    validate_scanner_envelope(envelope)
    return json.dumps(envelope.to_payload(), sort_keys=True, separators=(",", ":")).encode("utf-8")


def scanner_payload_sha256(payload_bytes: bytes) -> str:
    return hashlib.sha256(payload_bytes).hexdigest()


def scanner_envelope_artifact_ref(
    *,
    envelope: ScannerEnvelope,
    storage_ref: str,
    payload_bytes: bytes,
    artifact_id: Optional[str] = None,
) -> ArtifactRef:
    return ArtifactRef(
        artifact_id=artifact_id or f"{envelope.scan_run.run_id}:scanner_envelope",
        artifact_type=SCANNER_ENVELOPE_ARTIFACT_TYPE,
        storage_ref=storage_ref,
        mime_type="application/vnd.querylake.scanner-envelope+json",
        bytes_sha256=scanner_payload_sha256(payload_bytes),
        md={
            "schema_version": envelope.schema_version,
            "run_id": envelope.scan_run.run_id,
            "backend_id": envelope.scan_run.backend_id,
            "backend_class": envelope.scan_run.backend_class,
            "support_tier": envelope.scan_run.support_tier,
            "status": envelope.scan_run.status,
            "legacy_output_contract": envelope.contract.legacy_output_contract,
            "raw_backend_contract": envelope.contract.raw_backend_contract,
            "acquisition_mode": envelope.contract.acquisition_mode,
            "projection_kinds": list(envelope.contract.projection_kinds),
        },
    )


def write_scanner_envelope(
    store: ScannerObjectStore,
    envelope: ScannerEnvelope,
    *,
    artifact_id: Optional[str] = None,
) -> PersistedScannerEnvelope:
    """Persist a canonical scanner envelope in a CAS-like object store.

    The return value is deliberately artifact-shaped so it can be attached to the
    existing file/document artifact path before any scanner-specific tables exist.
    """

    payload_bytes = scanner_envelope_to_json_bytes(envelope)
    cas = store.put_bytes(payload_bytes)
    ref = scanner_envelope_artifact_ref(
        envelope=envelope,
        storage_ref=cas,
        payload_bytes=payload_bytes,
        artifact_id=artifact_id,
    )
    return PersistedScannerEnvelope(envelope_ref=ref, payload=envelope.to_payload())


def read_scanner_envelope_payload(store: ScannerObjectStore, storage_ref: str) -> Dict[str, Any]:
    raw = store.get_bytes(storage_ref)
    if raw is None:
        raise FileNotFoundError(f"scanner envelope CAS object not found: {storage_ref}")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"scanner envelope CAS object is not valid JSON: {storage_ref}") from exc
    if not isinstance(payload, dict):
        raise ValueError("scanner envelope payload must be a JSON object")
    return payload


def summarize_scanner_envelope_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    scan_run = payload.get("scan_run") or {}
    contract = payload.get("contract") or {}
    projections = payload.get("projections") or []
    pages = payload.get("pages") or []
    routing = payload.get("routing") or []
    return {
        "schema_version": payload.get("schema_version"),
        "run_id": scan_run.get("run_id"),
        "backend_id": scan_run.get("backend_id"),
        "backend_class": scan_run.get("backend_class"),
        "support_tier": scan_run.get("support_tier"),
        "status": scan_run.get("status"),
        "legacy_output_contract": contract.get("legacy_output_contract"),
        "raw_backend_contract": contract.get("raw_backend_contract"),
        "acquisition_mode": contract.get("acquisition_mode"),
        "page_count": len(pages),
        "projection_kinds": [projection.get("projection_kind") for projection in projections],
        "routing_actions": [decision.get("action") for decision in routing],
        "warning_count": len(payload.get("warnings") or []),
        "error_count": len(payload.get("errors") or []),
    }

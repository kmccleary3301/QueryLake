from __future__ import annotations

from typing import Any, Dict, List, Optional

from QueryLake.scanning.adapters import AdapterAvailability
from QueryLake.scanning.chandra import ChandraCompatibilityAdapter
from QueryLake.scanning.docling import DoclingLocalParserAdapter
from QueryLake.scanning.native import PyMuPDF4LLMNativeAdapter
from QueryLake.scanning.providers import GeminiDocumentFallbackMockAdapter, MistralOCRMockAdapter
from QueryLake.scanning.registry import ScannerBackendSpec, build_default_scanner_registry
from QueryLake.scanning.shadow import MinerUShadowAdapter


def _availability_by_backend() -> Dict[str, AdapterAvailability]:
    adapters = [
        ChandraCompatibilityAdapter(),
        PyMuPDF4LLMNativeAdapter(),
        DoclingLocalParserAdapter(),
        MistralOCRMockAdapter(),
        GeminiDocumentFallbackMockAdapter(),
        MinerUShadowAdapter(),
    ]
    return {adapter.backend_id: adapter.check_available() for adapter in adapters}


def scanner_availability_rows(
    registry: Optional[Dict[str, ScannerBackendSpec]] = None,
) -> List[Dict[str, Any]]:
    registry = registry or build_default_scanner_registry()
    availability = _availability_by_backend()
    rows: List[Dict[str, Any]] = []
    for backend_id in sorted(registry):
        spec = registry[backend_id]
        item = availability.get(backend_id)
        if item is None:
            item = AdapterAvailability(
                backend_id=backend_id,
                available=False,
                reason="adapter_not_implemented",
            )
        rows.append(
            {
                "backend_id": backend_id,
                "display_name": spec.display_name,
                "support_tier": spec.support_tier,
                "status": spec.status,
                "routing_eligibility": spec.routing_eligibility,
                "available": item.available,
                "reason": item.reason,
                "version": item.version,
                "md": item.md,
            }
        )
    return rows


def scanner_availability_to_markdown(rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# Scanner Availability",
        "",
        "| backend_id | support_tier | routing_eligibility | available | reason |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['backend_id']} | {row['support_tier']} | {row['routing_eligibility']} | {str(row['available']).lower()} | {row['reason']} |"
        )
    return "\n".join(lines)

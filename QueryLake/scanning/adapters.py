from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from QueryLake.scanning.contracts import ScannerEnvelope


@dataclass(frozen=True)
class ScannerRunContext:
    run_id: str
    backend_id: str
    backend_class: str
    support_tier: str
    file_id: Optional[str] = None
    file_version_id: Optional[str] = None
    document_version_id: Optional[str] = None
    config_hash: Optional[str] = None
    md: Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AdapterAvailability:
    backend_id: str
    available: bool
    reason: str = "available"
    version: Optional[str] = None
    md: Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LegacyMarkdownScanResult:
    markdown: str
    meta: Dict[str, Any]
    page_markdown: List[str] = field(default_factory=list)
    ocr_info_cas: Optional[str] = None
    page_image_cas_by_page: Dict[str, str] = field(default_factory=dict)
    page_ocr_json_cas_by_page: Dict[str, str] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


@runtime_checkable
class ScannerAdapter(Protocol):
    backend_id: str

    def check_available(self) -> AdapterAvailability:
        ...

    def map_existing_output_to_envelope(
        self,
        result: LegacyMarkdownScanResult,
        context: ScannerRunContext,
    ) -> ScannerEnvelope:
        ...

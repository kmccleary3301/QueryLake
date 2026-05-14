from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Literal, Optional

SupportTier = Literal["first_class", "experimental", "shadow", "premium_fallback", "deferred", "watchlist", "low_ev"]
AcquisitionMode = Literal["native_text", "ocr", "mixed", "vision_only"]
ProjectionKind = Literal[
    "canonical_markdown",
    "canonical_text",
    "layout_graph",
    "structured_fields",
    "scientific_tei",
    "chunk_compat",
]
StructureLevel = Literal["text_only", "block", "line", "token", "table_cell", "figure", "field_schema", "page_visual"]
GeometryLevel = Literal["none", "page", "block", "line", "token", "polygon", "table_cell"]
ScanStatus = Literal["pending", "running", "succeeded", "failed", "partial", "skipped"]

LEGACY_OUTPUT_CONTRACTS = {
    "ocr_markdown",
    "text_layer_fastpath_markdown",
    "mixed_text_layer_fastpath_markdown",
}


@dataclass(frozen=True)
class ArtifactRef:
    artifact_id: str
    artifact_type: str
    storage_ref: Optional[str] = None
    text: Optional[str] = None
    mime_type: Optional[str] = None
    bytes_sha256: Optional[str] = None
    md: Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScanRun:
    run_id: str
    backend_id: str
    backend_class: str
    support_tier: SupportTier
    status: ScanStatus
    file_id: Optional[str] = None
    file_version_id: Optional[str] = None
    document_version_id: Optional[str] = None
    config_hash: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    backend_version: Optional[str] = None
    model_id: Optional[str] = None
    processor_version: Optional[str] = None
    md: Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScanContract:
    legacy_output_contract: Optional[str]
    raw_backend_contract: str
    acquisition_mode: AcquisitionMode
    projection_kinds: List[ProjectionKind]
    structure_level: StructureLevel
    geometry_level: GeometryLevel
    md: Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PageRecord:
    page_index: int
    acquisition_mode: AcquisitionMode
    width: Optional[float] = None
    height: Optional[float] = None
    rotation: Optional[float] = None
    language: Optional[str] = None
    script: Optional[str] = None
    quality: Dict[str, Any] = field(default_factory=dict)
    artifact_refs: List[str] = field(default_factory=list)
    md: Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScanObject:
    object_id: str
    object_type: str
    page_index: int
    reading_order: int
    text: Optional[str] = None
    text_span_ref: Optional[str] = None
    bbox: Optional[List[float]] = None
    polygon: Optional[List[List[float]]] = None
    parent_object_id: Optional[str] = None
    child_object_ids: List[str] = field(default_factory=list)
    confidence: Optional[float] = None
    confidence_available: bool = False
    source_artifact_ref: Optional[str] = None
    md: Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Projection:
    projection_id: str
    projection_kind: ProjectionKind
    text: Optional[str] = None
    storage_ref: Optional[str] = None
    source_page_indices: List[int] = field(default_factory=list)
    source_object_ids: List[str] = field(default_factory=list)
    compatibility_contract: Optional[str] = None
    md: Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RoutingDecision:
    backend_id: str
    action: Literal["selected", "skipped", "shadowed", "fallback", "blocked", "escalated"]
    reason: str
    page_indices: List[int] = field(default_factory=list)
    policy_status: Optional[str] = None
    fallback_from: Optional[str] = None
    md: Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScanRequest:
    request_id: str
    source_ref: str
    mime_type: Optional[str] = None
    file_id: Optional[str] = None
    file_version_id: Optional[str] = None
    document_version_id: Optional[str] = None
    logical_name: Optional[str] = None
    policy: Dict[str, Any] = field(default_factory=dict)
    route_hints: Dict[str, Any] = field(default_factory=dict)
    md: Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScannerEnvelope:
    schema_version: str
    scan_run: ScanRun
    contract: ScanContract
    artifacts: List[ArtifactRef] = field(default_factory=list)
    pages: List[PageRecord] = field(default_factory=list)
    objects: List[ScanObject] = field(default_factory=list)
    projections: List[Projection] = field(default_factory=list)
    routing: List[RoutingDecision] = field(default_factory=list)
    quality: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)

    def canonical_text(self) -> str:
        for projection in self.projections:
            if projection.projection_kind == "canonical_text" and projection.text is not None:
                return projection.text
        for projection in self.projections:
            if projection.projection_kind in {"canonical_markdown", "chunk_compat"} and projection.text is not None:
                return projection.text
        return ""

    def legacy_projection(self) -> Optional[Projection]:
        for projection in self.projections:
            if projection.compatibility_contract == self.contract.legacy_output_contract:
                return projection
        return None


def normalize_legacy_output_contract(contract: Optional[str]) -> Optional[str]:
    if contract is None:
        return None
    normalized = str(contract).strip()
    if normalized not in LEGACY_OUTPUT_CONTRACTS:
        raise ValueError(f"Unknown legacy scanner output contract: {contract}")
    return normalized


def validate_scanner_envelope(envelope: ScannerEnvelope) -> None:
    if envelope.schema_version != "scanner_envelope_v1":
        raise ValueError(f"Unsupported scanner envelope schema version: {envelope.schema_version}")
    if not envelope.scan_run.run_id:
        raise ValueError("scan_run.run_id is required")
    if not envelope.scan_run.backend_id:
        raise ValueError("scan_run.backend_id is required")
    if envelope.contract.legacy_output_contract is not None:
        normalize_legacy_output_contract(envelope.contract.legacy_output_contract)
    if not envelope.contract.raw_backend_contract:
        raise ValueError("contract.raw_backend_contract is required")
    if not envelope.contract.projection_kinds:
        raise ValueError("contract.projection_kinds must not be empty")
    for page in envelope.pages:
        if page.page_index < 1:
            raise ValueError("page_index is one-based and must be >= 1")
    for obj in envelope.objects:
        if obj.page_index < 1:
            raise ValueError("object.page_index is one-based and must be >= 1")
        if obj.confidence is not None and not (0.0 <= float(obj.confidence) <= 1.0):
            raise ValueError("object.confidence must be in [0, 1] when present")


def _page_source_acquisition(source: str) -> AcquisitionMode:
    normalized = str(source or "").strip().lower()
    if normalized in {"text_layer", "native_text", "pdf_text_layer"}:
        return "native_text"
    if normalized in {"vision", "vision_only"}:
        return "vision_only"
    return "ocr"


def _contract_acquisition_mode(contract: str) -> AcquisitionMode:
    normalized = normalize_legacy_output_contract(contract)
    if normalized == "text_layer_fastpath_markdown":
        return "native_text"
    if normalized == "mixed_text_layer_fastpath_markdown":
        return "mixed"
    return "ocr"


def _raw_contract_for_legacy(contract: str, engine: Optional[str]) -> str:
    normalized = normalize_legacy_output_contract(contract)
    engine_name = str(engine or "legacy").strip().lower() or "legacy"
    if normalized == "ocr_markdown" and engine_name == "chandra":
        return "chandra_ocr_markdown"
    if normalized == "text_layer_fastpath_markdown" and engine_name == "pymupdf4llm":
        return "pymupdf4llm_markdown"
    if normalized == "text_layer_fastpath_markdown":
        return "pdf_text_layer_fastpath_markdown"
    if normalized == "mixed_text_layer_fastpath_markdown":
        return f"{engine_name}_mixed_text_layer_fastpath_markdown"
    return f"{engine_name}_{normalized}"


def materialize_legacy_markdown_envelope(
    *,
    run_id: str,
    backend_id: str,
    backend_class: str,
    support_tier: SupportTier,
    legacy_output_contract: str,
    markdown: str,
    meta: Optional[Dict[str, Any]] = None,
    file_id: Optional[str] = None,
    file_version_id: Optional[str] = None,
    document_version_id: Optional[str] = None,
) -> ScannerEnvelope:
    """Wrap current files-service markdown outputs in scanner_envelope_v1.

    This is a compatibility materializer. It does not call scanner backends and it
    does not change runtime ingestion behavior.
    """

    normalized_contract = normalize_legacy_output_contract(legacy_output_contract)
    metadata = dict(meta or {})
    page_count = int(metadata.get("pages", 0) or 0)
    if page_count <= 0:
        page_source_by_page = metadata.get("page_source_by_page") or {}
        page_count = len(page_source_by_page) if isinstance(page_source_by_page, dict) else 1
    page_count = max(1, page_count)

    page_source_by_page = metadata.get("page_source_by_page") or {}
    if not isinstance(page_source_by_page, dict):
        page_source_by_page = {}

    contract_acquisition = _contract_acquisition_mode(normalized_contract)
    pages: List[PageRecord] = []
    for page_index in range(1, page_count + 1):
        source = page_source_by_page.get(f"{page_index:04d}") or page_source_by_page.get(str(page_index)) or "ocr"
        page_mode = _page_source_acquisition(str(source))
        if contract_acquisition != "mixed":
            page_mode = contract_acquisition
        pages.append(
            PageRecord(
                page_index=page_index,
                acquisition_mode=page_mode,
                quality=metadata.get("page_complexity_by_page", {}).get(f"{page_index:04d}", {})
                if isinstance(metadata.get("page_complexity_by_page"), dict)
                else {},
                md={"source": source},
            )
        )

    raw_backend_contract = _raw_contract_for_legacy(normalized_contract, metadata.get("engine"))
    projection_kinds: List[ProjectionKind] = ["canonical_markdown", "canonical_text", "chunk_compat"]
    envelope = ScannerEnvelope(
        schema_version="scanner_envelope_v1",
        scan_run=ScanRun(
            run_id=run_id,
            backend_id=backend_id,
            backend_class=backend_class,
            support_tier=support_tier,
            status="succeeded",
            file_id=file_id,
            file_version_id=file_version_id,
            document_version_id=document_version_id,
            backend_version=str(metadata.get("backend_version")) if metadata.get("backend_version") else None,
            model_id=str(metadata.get("model_id")) if metadata.get("model_id") else None,
            processor_version=str(metadata.get("processor_version")) if metadata.get("processor_version") else None,
            md={"legacy_meta": metadata},
        ),
        contract=ScanContract(
            legacy_output_contract=normalized_contract,
            raw_backend_contract=raw_backend_contract,
            acquisition_mode=contract_acquisition,
            projection_kinds=projection_kinds,
            structure_level="block" if normalized_contract != "text_layer_fastpath_markdown" else "text_only",
            geometry_level="page" if normalized_contract != "text_layer_fastpath_markdown" else "none",
        ),
        artifacts=[
            ArtifactRef(
                artifact_id=f"{run_id}:legacy_meta",
                artifact_type="legacy_scanner_metadata",
                storage_ref=metadata.get("ocr_info_cas"),
                md=metadata,
            )
        ],
        pages=pages,
        projections=[
            Projection(
                projection_id=f"{run_id}:canonical_markdown",
                projection_kind="canonical_markdown",
                text=markdown,
                source_page_indices=list(range(1, page_count + 1)),
                compatibility_contract=normalized_contract,
            ),
            Projection(
                projection_id=f"{run_id}:canonical_text",
                projection_kind="canonical_text",
                text=markdown,
                source_page_indices=list(range(1, page_count + 1)),
            ),
            Projection(
                projection_id=f"{run_id}:chunk_compat",
                projection_kind="chunk_compat",
                text=markdown,
                source_page_indices=list(range(1, page_count + 1)),
                compatibility_contract=normalized_contract,
            ),
        ],
        routing=[
            RoutingDecision(
                backend_id=backend_id,
                action="selected",
                reason="legacy_compatibility_materialization",
                page_indices=list(range(1, page_count + 1)),
                md={"legacy_output_contract": normalized_contract},
            )
        ],
        quality={
            "page_source_counts": metadata.get("page_source_counts", {}),
            "page_complexity_counts": metadata.get("page_complexity_counts", {}),
        },
    )
    validate_scanner_envelope(envelope)
    return envelope

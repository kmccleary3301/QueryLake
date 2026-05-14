from __future__ import annotations

import importlib
import importlib.util
import json
import re
import tempfile
import time
from dataclasses import asdict, dataclass, field
from importlib import metadata
from typing import Any, Callable, Dict, List, Optional

from QueryLake.scanning.adapters import AdapterAvailability, ScannerRunContext
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
from QueryLake.scanning.persistence import SCANNER_RAW_PAYLOAD_ARTIFACT_TYPE, ScannerObjectStore


def _safe_version(package_name: str) -> Optional[str]:
    try:
        return metadata.version(package_name)
    except Exception:
        return None


def _markdown_to_text(markdown: str) -> str:
    text = str(markdown or "")
    text = re.sub(r"`{3}.*?`{3}", " ", text, flags=re.DOTALL)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"^[#>*\-\s]+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


@dataclass(frozen=True)
class DoclingExtractionResult:
    markdown: str
    raw_payload: Dict[str, Any] = field(default_factory=dict)
    page_count: int = 1
    pages: List[Dict[str, Any]] = field(default_factory=list)
    objects: List[Dict[str, Any]] = field(default_factory=list)
    tables: List[Dict[str, Any]] = field(default_factory=list)
    figures: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    backend_version: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


class DoclingLocalParserAdapter:
    backend_id = "docling_local"

    def __init__(
        self,
        *,
        extractor: Optional[Callable[[bytes], DoclingExtractionResult]] = None,
    ) -> None:
        self._extractor = extractor

    def check_available(self) -> AdapterAvailability:
        if self._extractor is not None:
            return AdapterAvailability(
                backend_id=self.backend_id,
                available=True,
                reason="injected_extractor_available",
                version="injected",
                md={"integration_state": "mapping_adapter"},
            )
        spec = importlib.util.find_spec("docling")
        if spec is None:
            return AdapterAvailability(
                backend_id=self.backend_id,
                available=False,
                reason="missing_optional_dependency:docling",
                md={
                    "install_extra": "querylake-backend[scanners-local]",
                    "package": "docling",
                    "integration_state": "mapping_adapter",
                },
            )
        return AdapterAvailability(
            backend_id=self.backend_id,
            available=True,
            reason="available",
            version=_safe_version("docling"),
            md={"integration_state": "mapping_adapter"},
        )

    def extract_pdf_bytes(self, pdf_bytes: bytes) -> DoclingExtractionResult:
        if self._extractor is not None:
            return self._extractor(pdf_bytes)

        availability = self.check_available()
        if not availability.available:
            raise RuntimeError(availability.reason)

        converter_mod = importlib.import_module("docling.document_converter")
        converter = converter_mod.DocumentConverter()
        with tempfile.NamedTemporaryFile(prefix="querylake_docling_", suffix=".pdf") as tmp:
            tmp.write(pdf_bytes)
            tmp.flush()
            result = converter.convert(tmp.name)

        document = result.document
        markdown = document.export_to_markdown()
        raw_payload: Dict[str, Any]
        if hasattr(document, "export_to_dict"):
            raw_payload = document.export_to_dict()
        elif hasattr(document, "model_dump"):
            raw_payload = document.model_dump()
        elif hasattr(document, "to_dict"):
            raw_payload = document.to_dict()
        else:
            raw_payload = {"markdown": markdown}

        pages = raw_payload.get("pages") if isinstance(raw_payload, dict) else None
        page_count = len(pages) if isinstance(pages, list) and pages else int(raw_payload.get("page_count", 1) or 1)
        return DoclingExtractionResult(
            markdown=str(markdown or ""),
            raw_payload=raw_payload if isinstance(raw_payload, dict) else {"raw": raw_payload},
            page_count=max(1, page_count),
            pages=pages if isinstance(pages, list) else [],
            objects=raw_payload.get("objects", []) if isinstance(raw_payload.get("objects"), list) else [],
            tables=raw_payload.get("tables", []) if isinstance(raw_payload.get("tables"), list) else [],
            figures=raw_payload.get("figures", []) if isinstance(raw_payload.get("figures"), list) else [],
            backend_version=_safe_version("docling"),
        )

    def scan_pdf_bytes(
        self,
        *,
        pdf_bytes: bytes,
        context: ScannerRunContext,
        store: Optional[ScannerObjectStore] = None,
    ) -> ScannerEnvelope:
        started_at = time.time()
        extraction = self.extract_pdf_bytes(pdf_bytes)
        page_count = max(1, int(extraction.page_count or len(extraction.pages) or 1))
        raw_payload_cas: Optional[str] = None
        if store is not None:
            raw_payload_cas = store.put_bytes(
                json.dumps(extraction.to_payload(), sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
            )

        artifacts: List[ArtifactRef] = []
        if raw_payload_cas is not None:
            artifacts.append(
                ArtifactRef(
                    artifact_id=f"{context.run_id}:docling_raw_payload",
                    artifact_type=SCANNER_RAW_PAYLOAD_ARTIFACT_TYPE,
                    storage_ref=raw_payload_cas,
                    mime_type="application/json",
                    md={"backend_id": self.backend_id, "backend_version": extraction.backend_version},
                )
            )

        pages: List[PageRecord] = []
        for page_index in range(1, page_count + 1):
            raw_page = extraction.pages[page_index - 1] if page_index - 1 < len(extraction.pages) else {}
            pages.append(
                PageRecord(
                    page_index=page_index,
                    acquisition_mode="mixed",
                    width=raw_page.get("width") if isinstance(raw_page, dict) else None,
                    height=raw_page.get("height") if isinstance(raw_page, dict) else None,
                    rotation=raw_page.get("rotation") if isinstance(raw_page, dict) else None,
                    quality=raw_page.get("quality", {}) if isinstance(raw_page, dict) else {},
                    md={"source": "docling"},
                )
            )

        objects: List[ScanObject] = []
        raw_objects = list(extraction.objects)
        raw_objects.extend({**table, "object_type": table.get("object_type", "table")} for table in extraction.tables)
        raw_objects.extend({**figure, "object_type": figure.get("object_type", "figure")} for figure in extraction.figures)
        for idx, raw_obj in enumerate(raw_objects, start=1):
            if not isinstance(raw_obj, dict):
                continue
            object_type = str(raw_obj.get("object_type") or raw_obj.get("type") or "block")
            objects.append(
                ScanObject(
                    object_id=str(raw_obj.get("object_id") or f"{context.run_id}:object:{idx:04d}"),
                    object_type=object_type,
                    page_index=max(1, int(raw_obj.get("page_index") or raw_obj.get("page") or 1)),
                    reading_order=int(raw_obj.get("reading_order") or idx),
                    text=raw_obj.get("text"),
                    bbox=raw_obj.get("bbox") if isinstance(raw_obj.get("bbox"), list) else None,
                    polygon=raw_obj.get("polygon") if isinstance(raw_obj.get("polygon"), list) else None,
                    confidence=raw_obj.get("confidence") if raw_obj.get("confidence") is not None else None,
                    confidence_available=raw_obj.get("confidence") is not None,
                    source_artifact_ref=f"{context.run_id}:docling_raw_payload" if raw_payload_cas else None,
                    md={key: value for key, value in raw_obj.items() if key not in {"text", "bbox", "polygon", "confidence"}},
                )
            )

        projection_kinds = ["canonical_markdown", "canonical_text", "chunk_compat"]
        structured_text = None
        if extraction.tables:
            projection_kinds.append("structured_fields")
            structured_text = json.dumps({"tables": extraction.tables}, sort_keys=True, default=str)

        projections = [
            Projection(
                projection_id=f"{context.run_id}:canonical_markdown",
                projection_kind="canonical_markdown",
                text=extraction.markdown,
                source_page_indices=list(range(1, page_count + 1)),
            ),
            Projection(
                projection_id=f"{context.run_id}:canonical_text",
                projection_kind="canonical_text",
                text=_markdown_to_text(extraction.markdown),
                source_page_indices=list(range(1, page_count + 1)),
            ),
            Projection(
                projection_id=f"{context.run_id}:chunk_compat",
                projection_kind="chunk_compat",
                text=extraction.markdown,
                source_page_indices=list(range(1, page_count + 1)),
            ),
        ]
        if structured_text is not None:
            projections.append(
                Projection(
                    projection_id=f"{context.run_id}:structured_fields",
                    projection_kind="structured_fields",
                    text=structured_text,
                    source_page_indices=list(range(1, page_count + 1)),
                    source_object_ids=[obj.object_id for obj in objects if obj.object_type == "table"],
                )
            )

        envelope = ScannerEnvelope(
            schema_version="scanner_envelope_v1",
            scan_run=ScanRun(
                run_id=context.run_id,
                backend_id=self.backend_id,
                backend_class="general_local_parser",
                support_tier="first_class",
                status="succeeded",
                file_id=context.file_id,
                file_version_id=context.file_version_id,
                document_version_id=context.document_version_id,
                config_hash=context.config_hash,
                started_at=started_at,
                completed_at=time.time(),
                backend_version=extraction.backend_version,
                md={"adapter_context": context.md, "raw_payload_cas": raw_payload_cas},
            ),
            contract=ScanContract(
                legacy_output_contract=None,
                raw_backend_contract="docling_document",
                acquisition_mode="mixed",
                projection_kinds=projection_kinds,
                structure_level="table_cell" if extraction.tables else "block",
                geometry_level="table_cell" if extraction.tables else "block",
                md={"table_count": len(extraction.tables), "figure_count": len(extraction.figures)},
            ),
            artifacts=artifacts,
            pages=pages,
            objects=objects,
            projections=projections,
            routing=[
                RoutingDecision(
                    backend_id=self.backend_id,
                    action="selected",
                    reason="local_parser_mapping",
                    page_indices=list(range(1, page_count + 1)),
                )
            ],
            quality={
                "table_count": len(extraction.tables),
                "figure_count": len(extraction.figures),
                "object_count": len(objects),
            },
            warnings=list(extraction.warnings),
        )
        validate_scanner_envelope(envelope)
        return envelope

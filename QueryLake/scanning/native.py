from __future__ import annotations

import importlib
import importlib.util
import json
import re
import tempfile
import time
from dataclasses import asdict, dataclass, field, replace
from importlib import metadata
from typing import Any, Callable, Dict, List, Optional

from QueryLake.scanning.adapters import AdapterAvailability, ScannerRunContext
from QueryLake.scanning.contracts import ArtifactRef, ScannerEnvelope, materialize_legacy_markdown_envelope, validate_scanner_envelope
from QueryLake.scanning.persistence import SCANNER_RAW_PAYLOAD_ARTIFACT_TYPE, ScannerObjectStore


@dataclass(frozen=True)
class NativeTextQualityPolicy:
    min_total_chars: int = 120
    min_chars_per_page: int = 80
    min_qualified_page_coverage: float = 0.80
    max_repeated_line_ratio: float = 0.35
    max_empty_page_coverage: float = 0.20

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NativeTextQualityAssessment:
    selected: bool
    reason: str
    pages: int
    total_chars: int
    avg_chars_per_page: float
    qualified_pages: int
    qualified_page_coverage: float
    empty_pages: int
    empty_page_coverage: float
    repeated_line_ratio: float
    policy: NativeTextQualityPolicy

    def to_payload(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["avg_chars_per_page"] = round(float(self.avg_chars_per_page), 2)
        payload["qualified_page_coverage"] = round(float(self.qualified_page_coverage), 4)
        payload["empty_page_coverage"] = round(float(self.empty_page_coverage), 4)
        payload["repeated_line_ratio"] = round(float(self.repeated_line_ratio), 4)
        return payload


@dataclass(frozen=True)
class NativeExtractionResult:
    markdown: str
    page_markdown: List[str] = field(default_factory=list)
    raw_payload: Dict[str, Any] = field(default_factory=dict)
    backend_version: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


class NativeTextQualityError(RuntimeError):
    def __init__(self, assessment: NativeTextQualityAssessment):
        super().__init__(f"native text quality rejected: {assessment.reason}")
        self.assessment = assessment


def normalize_native_page_markdown(text: Optional[str]) -> str:
    if not text:
        return ""
    normalized = str(text).replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in normalized.split("\n")).strip()


def split_markdown_pages(markdown: str) -> List[str]:
    text = normalize_native_page_markdown(markdown)
    if not text:
        return []
    parts = re.split(r"(?m)^##\s+Page\s+\d+\s*$", text)
    pages = [normalize_native_page_markdown(part) for part in parts if normalize_native_page_markdown(part)]
    return pages or [text]


def assess_native_text_quality(
    page_markdown: List[str],
    policy: Optional[NativeTextQualityPolicy] = None,
) -> NativeTextQualityAssessment:
    policy = policy or NativeTextQualityPolicy()
    pages = list(page_markdown or [])
    page_count = len(pages)
    page_chars = [len(normalize_native_page_markdown(page)) for page in pages]
    total_chars = int(sum(page_chars))
    qualified_pages = sum(1 for count in page_chars if count >= policy.min_chars_per_page)
    empty_pages = sum(1 for count in page_chars if count <= 0)
    avg_chars = (float(total_chars) / float(page_count)) if page_count else 0.0
    qualified_coverage = (float(qualified_pages) / float(page_count)) if page_count else 0.0
    empty_coverage = (float(empty_pages) / float(page_count)) if page_count else 1.0

    normalized_lines: List[str] = []
    for page in pages:
        normalized_lines.extend(
            line.strip()
            for line in normalize_native_page_markdown(page).split("\n")
            if line.strip()
        )
    if normalized_lines:
        counts: Dict[str, int] = {}
        for line in normalized_lines:
            counts[line] = counts.get(line, 0) + 1
        repeated_lines = sum(count for count in counts.values() if count > 1)
        repeated_ratio = float(repeated_lines) / float(len(normalized_lines))
    else:
        repeated_ratio = 0.0

    selected = True
    reason = "quality_pass"
    if page_count <= 0:
        selected = False
        reason = "no_pages"
    elif total_chars < policy.min_total_chars:
        selected = False
        reason = "min_total_chars_miss"
    elif qualified_coverage < policy.min_qualified_page_coverage:
        selected = False
        reason = "qualified_page_coverage_miss"
    elif empty_coverage > policy.max_empty_page_coverage:
        selected = False
        reason = "empty_page_coverage_exceeded"
    elif repeated_ratio > policy.max_repeated_line_ratio:
        selected = False
        reason = "repeated_line_ratio_exceeded"

    return NativeTextQualityAssessment(
        selected=selected,
        reason=reason,
        pages=page_count,
        total_chars=total_chars,
        avg_chars_per_page=avg_chars,
        qualified_pages=qualified_pages,
        qualified_page_coverage=qualified_coverage,
        empty_pages=empty_pages,
        empty_page_coverage=empty_coverage,
        repeated_line_ratio=repeated_ratio,
        policy=policy,
    )


def _safe_version(package_name: str) -> Optional[str]:
    try:
        return metadata.version(package_name)
    except Exception:
        return None


class PyMuPDF4LLMNativeAdapter:
    backend_id = "pymupdf4llm_native"

    def __init__(
        self,
        *,
        quality_policy: Optional[NativeTextQualityPolicy] = None,
        extractor: Optional[Callable[[bytes], NativeExtractionResult]] = None,
    ) -> None:
        self.quality_policy = quality_policy or NativeTextQualityPolicy()
        self._extractor = extractor

    def check_available(self) -> AdapterAvailability:
        if self._extractor is not None:
            return AdapterAvailability(
                backend_id=self.backend_id,
                available=True,
                reason="injected_extractor_available",
                version="injected",
            )
        spec = importlib.util.find_spec("pymupdf4llm")
        if spec is None:
            return AdapterAvailability(
                backend_id=self.backend_id,
                available=False,
                reason="missing_optional_dependency:pymupdf4llm",
                md={
                    "install_extra": "querylake-backend[scanners-native]",
                    "package": "pymupdf4llm",
                },
            )
        return AdapterAvailability(
            backend_id=self.backend_id,
            available=True,
            reason="available",
            version=_safe_version("pymupdf4llm"),
        )

    def extract_pdf_bytes(self, pdf_bytes: bytes) -> NativeExtractionResult:
        if self._extractor is not None:
            return self._extractor(pdf_bytes)

        availability = self.check_available()
        if not availability.available:
            raise RuntimeError(availability.reason)

        module = importlib.import_module("pymupdf4llm")
        with tempfile.NamedTemporaryFile(prefix="querylake_pymupdf4llm_", suffix=".pdf") as tmp:
            tmp.write(pdf_bytes)
            tmp.flush()
            markdown = module.to_markdown(tmp.name)

        markdown = normalize_native_page_markdown(markdown)
        page_markdown = split_markdown_pages(markdown)
        return NativeExtractionResult(
            markdown=markdown,
            page_markdown=page_markdown,
            raw_payload={
                "markdown": markdown,
                "page_count": len(page_markdown),
            },
            backend_version=_safe_version("pymupdf4llm"),
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
        page_markdown = extraction.page_markdown or split_markdown_pages(extraction.markdown)
        assessment = assess_native_text_quality(page_markdown, self.quality_policy)
        if not assessment.selected:
            raise NativeTextQualityError(assessment)

        page_count = max(1, assessment.pages)
        raw_payload = {
            "backend_id": self.backend_id,
            "backend_version": extraction.backend_version,
            "quality": assessment.to_payload(),
            "raw_payload": extraction.raw_payload,
        }
        raw_payload_cas: Optional[str] = None
        if store is not None:
            raw_payload_cas = store.put_bytes(
                json.dumps(raw_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
            )

        meta = {
            "engine": "pymupdf4llm",
            "backend_version": extraction.backend_version,
            "pages": page_count,
            "output_contract": "text_layer_fastpath_markdown",
            "page_source_by_page": {
                f"{page_idx:04d}": "native_text"
                for page_idx in range(1, page_count + 1)
            },
            "page_source_counts": {
                "native_text": page_count,
                "text_layer": page_count,
                "ocr": 0,
            },
            "native_quality": assessment.to_payload(),
            "raw_payload_cas": raw_payload_cas,
        }
        envelope = materialize_legacy_markdown_envelope(
            run_id=context.run_id,
            backend_id=self.backend_id,
            backend_class="native_digital_extraction",
            support_tier="first_class",
            legacy_output_contract="text_layer_fastpath_markdown",
            markdown=extraction.markdown,
            meta=meta,
            file_id=context.file_id,
            file_version_id=context.file_version_id,
            document_version_id=context.document_version_id,
        )

        artifacts = list(envelope.artifacts)
        if raw_payload_cas is not None:
            artifacts.append(
                ArtifactRef(
                    artifact_id=f"{context.run_id}:pymupdf4llm_raw_payload",
                    artifact_type=SCANNER_RAW_PAYLOAD_ARTIFACT_TYPE,
                    storage_ref=raw_payload_cas,
                    mime_type="application/json",
                    md={
                        "backend_id": self.backend_id,
                        "backend_version": extraction.backend_version,
                    },
                )
            )

        envelope = replace(
            envelope,
            scan_run=replace(
                envelope.scan_run,
                started_at=started_at,
                completed_at=time.time(),
                backend_version=extraction.backend_version,
                config_hash=context.config_hash,
                md={
                    **envelope.scan_run.md,
                    "adapter_context": context.md,
                    "native_quality": assessment.to_payload(),
                },
            ),
            contract=replace(
                envelope.contract,
                raw_backend_contract="pymupdf4llm_markdown",
                structure_level="block",
                geometry_level="block",
                md={"quality_policy": self.quality_policy.to_payload()},
            ),
            artifacts=artifacts,
            quality={
                **envelope.quality,
                "native_text_quality": assessment.to_payload(),
            },
        )
        validate_scanner_envelope(envelope)
        return envelope

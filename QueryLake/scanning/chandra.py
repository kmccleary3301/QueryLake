from __future__ import annotations

from dataclasses import replace
from typing import Any, Dict, List, Optional

from QueryLake.scanning.adapters import AdapterAvailability, LegacyMarkdownScanResult, ScannerAdapter, ScannerRunContext
from QueryLake.scanning.contracts import ArtifactRef, PageRecord, ScannerEnvelope, materialize_legacy_markdown_envelope, validate_scanner_envelope
from QueryLake.scanning.persistence import SCANNER_RAW_PAYLOAD_ARTIFACT_TYPE


def _page_key(page_index: int) -> str:
    return f"{page_index:04d}"


def _normalize_page_ref_map(raw: Optional[Dict[Any, Any]]) -> Dict[str, str]:
    refs: Dict[str, str] = {}
    for key, value in dict(raw or {}).items():
        if value is None:
            continue
        if isinstance(key, int):
            normalized_key = _page_key(key)
        else:
            key_text = str(key)
            normalized_key = _page_key(int(key_text)) if key_text.isdigit() else key_text
        refs[normalized_key] = str(value)
    return refs


def _page_geometry(meta: Dict[str, Any], page_key: str) -> Dict[str, Optional[float]]:
    geometry = meta.get("page_geometry_by_page") or meta.get("page_dimensions_by_page") or {}
    if not isinstance(geometry, dict):
        return {"width": None, "height": None, "rotation": None}
    item = geometry.get(page_key) or geometry.get(str(int(page_key))) if page_key.isdigit() else geometry.get(page_key)
    if not isinstance(item, dict):
        return {"width": None, "height": None, "rotation": None}
    return {
        "width": item.get("width") or item.get("width_px"),
        "height": item.get("height") or item.get("height_px"),
        "rotation": item.get("rotation"),
    }


def build_chandra_compatibility_envelope(
    *,
    context: ScannerRunContext,
    result: LegacyMarkdownScanResult,
) -> ScannerEnvelope:
    """Map existing Chandra/files-service output shapes into scanner_envelope_v1.

    This function does not render PDFs, call Chandra, or mutate files runtime state.
    It only preserves the current output contract in the canonical scanner envelope.
    """

    meta = dict(result.meta or {})
    legacy_output_contract = meta.get("output_contract") or "ocr_markdown"
    markdown = result.markdown
    if not markdown and result.page_markdown:
        markdown = "\n\n".join(result.page_markdown)

    envelope = materialize_legacy_markdown_envelope(
        run_id=context.run_id,
        backend_id=context.backend_id,
        backend_class=context.backend_class,
        support_tier=context.support_tier,  # type: ignore[arg-type]
        legacy_output_contract=legacy_output_contract,
        markdown=markdown,
        meta=meta,
        file_id=context.file_id,
        file_version_id=context.file_version_id,
        document_version_id=context.document_version_id,
    )

    artifacts: List[ArtifactRef] = list(envelope.artifacts)
    if result.ocr_info_cas:
        artifacts.append(
            ArtifactRef(
                artifact_id=f"{context.run_id}:chandra_ocr_info",
                artifact_type=SCANNER_RAW_PAYLOAD_ARTIFACT_TYPE,
                storage_ref=result.ocr_info_cas,
                mime_type="application/json",
                md={"role": "chandra_ocr_info", "source": "files_service_ocr_info_cas"},
            )
        )

    page_image_refs = _normalize_page_ref_map(result.page_image_cas_by_page or meta.get("page_image_cas_by_page"))
    page_ocr_refs = _normalize_page_ref_map(result.page_ocr_json_cas_by_page or meta.get("page_ocr_json_cas_by_page"))
    pages: List[PageRecord] = []
    for page in envelope.pages:
        key = _page_key(page.page_index)
        page_artifact_ids = list(page.artifact_refs)
        if key in page_image_refs:
            artifact_id = f"{context.run_id}:page:{key}:image"
            artifacts.append(
                ArtifactRef(
                    artifact_id=artifact_id,
                    artifact_type="scanner_page_image",
                    storage_ref=page_image_refs[key],
                    mime_type="image/png",
                    md={"page_index": page.page_index, "role": "rendered_page_image"},
                )
            )
            page_artifact_ids.append(artifact_id)
        if key in page_ocr_refs:
            artifact_id = f"{context.run_id}:page:{key}:ocr_json"
            artifacts.append(
                ArtifactRef(
                    artifact_id=artifact_id,
                    artifact_type=SCANNER_RAW_PAYLOAD_ARTIFACT_TYPE,
                    storage_ref=page_ocr_refs[key],
                    mime_type="application/json",
                    md={"page_index": page.page_index, "role": "page_ocr_json"},
                )
            )
            page_artifact_ids.append(artifact_id)
        geometry = _page_geometry(meta, key)
        pages.append(
            replace(
                page,
                width=geometry["width"],
                height=geometry["height"],
                rotation=geometry["rotation"],
                artifact_refs=page_artifact_ids,
                md={
                    **page.md,
                    "chandra_profile": meta.get("profile"),
                    "render_dpi": meta.get("render_dpi"),
                    "render_target_max_image_pixels": meta.get("render_target_max_image_pixels"),
                    "render_cache": {
                        "hits": meta.get("render_cache_hits"),
                        "misses": meta.get("render_cache_misses"),
                    },
                },
            )
        )

    envelope = replace(
        envelope,
        artifacts=artifacts,
        pages=pages,
        scan_run=replace(
            envelope.scan_run,
            config_hash=context.config_hash,
            md={
                **envelope.scan_run.md,
                "adapter_context": context.md,
                "chandra_profile": meta.get("profile"),
                "render_dpi": meta.get("render_dpi"),
                "render_cache_hits": meta.get("render_cache_hits"),
                "render_cache_misses": meta.get("render_cache_misses"),
            },
        ),
    )
    validate_scanner_envelope(envelope)
    return envelope


class ChandraCompatibilityAdapter(ScannerAdapter):
    backend_id = "chandra_1"

    def check_available(self) -> AdapterAvailability:
        return AdapterAvailability(
            backend_id=self.backend_id,
            available=True,
            reason="mapping_only_adapter_available",
            md={"calls_runtime": False},
        )

    def map_existing_output_to_envelope(
        self,
        result: LegacyMarkdownScanResult,
        context: ScannerRunContext,
    ) -> ScannerEnvelope:
        return build_chandra_compatibility_envelope(context=context, result=result)

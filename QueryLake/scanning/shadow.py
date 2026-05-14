from __future__ import annotations

import importlib.util
import json
import time
from dataclasses import dataclass, field
from importlib import metadata
from typing import Any, Dict, List, Optional

from QueryLake.scanning.adapters import AdapterAvailability, ScannerRunContext
from QueryLake.scanning.contracts import (
    ArtifactRef,
    PageRecord,
    Projection,
    RoutingDecision,
    ScanContract,
    ScanRun,
    ScannerEnvelope,
    validate_scanner_envelope,
)
from QueryLake.scanning.persistence import SCANNER_RAW_PAYLOAD_ARTIFACT_TYPE, SCANNER_SHADOW_RESULT_ARTIFACT_TYPE, ScannerObjectStore


def _safe_version(package_name: str) -> Optional[str]:
    try:
        return metadata.version(package_name)
    except Exception:
        return None


@dataclass(frozen=True)
class ShadowParserResult:
    markdown: str
    raw_payload: Dict[str, Any] = field(default_factory=dict)
    page_count: int = 1
    backend_version: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


class MinerUShadowAdapter:
    backend_id = "mineru_shadow"

    def __init__(self, *, result: Optional[ShadowParserResult] = None) -> None:
        self._result = result

    def check_available(self) -> AdapterAvailability:
        if self._result is not None:
            return AdapterAvailability(
                backend_id=self.backend_id,
                available=True,
                reason="injected_shadow_result_available",
                version="injected",
                md={"shadow_only": True},
            )
        spec = importlib.util.find_spec("mineru")
        if spec is None:
            return AdapterAvailability(
                backend_id=self.backend_id,
                available=False,
                reason="missing_optional_dependency:mineru",
                md={"shadow_only": True, "package": "mineru", "install_extra": "not_declared_yet"},
            )
        return AdapterAvailability(
            backend_id=self.backend_id,
            available=True,
            reason="available",
            version=_safe_version("mineru"),
            md={"shadow_only": True},
        )

    def scan_shadow_result(
        self,
        *,
        context: ScannerRunContext,
        store: Optional[ScannerObjectStore] = None,
    ) -> ScannerEnvelope:
        availability = self.check_available()
        if self._result is None:
            raise RuntimeError(availability.reason)
        result = self._result
        started_at = time.time()
        raw_payload_cas: Optional[str] = None
        if store is not None:
            raw_payload_cas = store.put_bytes(
                json.dumps(result.raw_payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
            )

        artifacts: List[ArtifactRef] = [
            ArtifactRef(
                artifact_id=f"{context.run_id}:shadow_markdown",
                artifact_type=SCANNER_SHADOW_RESULT_ARTIFACT_TYPE,
                text=result.markdown,
                mime_type="text/markdown",
                md={"backend_id": self.backend_id, "shadow_only": True},
            )
        ]
        if raw_payload_cas is not None:
            artifacts.append(
                ArtifactRef(
                    artifact_id=f"{context.run_id}:mineru_raw_payload",
                    artifact_type=SCANNER_RAW_PAYLOAD_ARTIFACT_TYPE,
                    storage_ref=raw_payload_cas,
                    mime_type="application/json",
                    md={"backend_id": self.backend_id, "shadow_only": True},
                )
            )

        page_count = max(1, int(result.page_count or 1))
        envelope = ScannerEnvelope(
            schema_version="scanner_envelope_v1",
            scan_run=ScanRun(
                run_id=context.run_id,
                backend_id=self.backend_id,
                backend_class="general_local_parser",
                support_tier="shadow",
                status="succeeded",
                file_id=context.file_id,
                file_version_id=context.file_version_id,
                document_version_id=context.document_version_id,
                config_hash=context.config_hash,
                started_at=started_at,
                completed_at=time.time(),
                backend_version=result.backend_version,
                md={"adapter_context": context.md, "shadow_only": True, "raw_payload_cas": raw_payload_cas},
            ),
            contract=ScanContract(
                legacy_output_contract=None,
                raw_backend_contract="mineru_shadow_payload",
                acquisition_mode="mixed",
                projection_kinds=["canonical_markdown", "canonical_text"],
                structure_level="block",
                geometry_level="block",
                md={"shadow_only": True, "user_facing": False},
            ),
            artifacts=artifacts,
            pages=[PageRecord(page_index=idx, acquisition_mode="mixed", md={"shadow_only": True}) for idx in range(1, page_count + 1)],
            projections=[
                Projection(
                    projection_id=f"{context.run_id}:shadow_markdown_projection",
                    projection_kind="canonical_markdown",
                    text=result.markdown,
                    source_page_indices=list(range(1, page_count + 1)),
                    md={"shadow_only": True},
                ),
                Projection(
                    projection_id=f"{context.run_id}:shadow_text_projection",
                    projection_kind="canonical_text",
                    text=result.markdown,
                    source_page_indices=list(range(1, page_count + 1)),
                    md={"shadow_only": True},
                ),
            ],
            routing=[
                RoutingDecision(
                    backend_id=self.backend_id,
                    action="shadowed",
                    reason="shadow_policy_allowed",
                    page_indices=list(range(1, page_count + 1)),
                    md={"user_facing": False},
                )
            ],
            quality={"shadow_only": True},
            warnings=list(result.warnings),
        )
        validate_scanner_envelope(envelope)
        return envelope

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
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
from QueryLake.scanning.persistence import SCANNER_RAW_PAYLOAD_ARTIFACT_TYPE, ScannerObjectStore


@dataclass(frozen=True)
class ProviderPolicy:
    allow_managed: bool = False
    allow_premium: bool = False
    max_cost_usd: Optional[float] = None
    estimated_cost_usd: float = 0.0

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProviderMockResult:
    markdown: str
    raw_payload: Dict[str, Any] = field(default_factory=dict)
    page_count: int = 1
    model_id: Optional[str] = None
    estimated_cost_usd: float = 0.0
    latency_seconds: Optional[float] = None
    warnings: List[str] = field(default_factory=list)

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


class ProviderPolicyError(RuntimeError):
    pass


def _markdown_to_text(markdown: str) -> str:
    return "\n".join(line.strip("#* `\t ") for line in str(markdown or "").splitlines()).strip()


class _ProviderBase:
    backend_id: str
    backend_class: str
    support_tier: str
    raw_backend_contract: str
    acquisition_mode: str
    env_key: str
    default_model_id: str

    def __init__(self, *, mock_result: Optional[ProviderMockResult] = None, live_enabled: bool = False) -> None:
        self._mock_result = mock_result
        self.live_enabled = live_enabled

    def check_available(self) -> AdapterAvailability:
        if self._mock_result is not None:
            return AdapterAvailability(
                backend_id=self.backend_id,
                available=True,
                reason="mock_result_available",
                version="mock",
                md={"live_enabled": False},
            )
        if not self.live_enabled:
            return AdapterAvailability(
                backend_id=self.backend_id,
                available=False,
                reason="live_adapter_disabled",
                md={"requires_explicit_live_enable": True},
            )
        if not os.getenv(self.env_key):
            return AdapterAvailability(
                backend_id=self.backend_id,
                available=False,
                reason=f"missing_credential:{self.env_key}",
                md={"credential_env": self.env_key, "credential_present": False},
            )
        return AdapterAvailability(
            backend_id=self.backend_id,
            available=False,
            reason="live_adapter_not_implemented",
            md={"credential_env": self.env_key, "credential_present": True},
        )

    def _enforce_policy(self, policy: ProviderPolicy) -> None:
        if self.support_tier == "premium_fallback" and not policy.allow_premium:
            raise ProviderPolicyError("premium_policy_denied")
        if self.support_tier != "premium_fallback" and not policy.allow_managed:
            raise ProviderPolicyError("managed_policy_denied")
        if policy.max_cost_usd is not None and policy.estimated_cost_usd > policy.max_cost_usd:
            raise ProviderPolicyError("budget_policy_denied")

    def scan_with_policy(
        self,
        *,
        context: ScannerRunContext,
        policy: ProviderPolicy,
        store: Optional[ScannerObjectStore] = None,
    ) -> ScannerEnvelope:
        self._enforce_policy(policy)
        if self._mock_result is None:
            availability = self.check_available()
            raise RuntimeError(availability.reason)
        return self._map_result(context=context, result=self._mock_result, policy=policy, store=store)

    def _map_result(
        self,
        *,
        context: ScannerRunContext,
        result: ProviderMockResult,
        policy: ProviderPolicy,
        store: Optional[ScannerObjectStore],
    ) -> ScannerEnvelope:
        started_at = time.time()
        raw_payload_cas: Optional[str] = None
        raw_payload = {
            "backend_id": self.backend_id,
            "model_id": result.model_id or self.default_model_id,
            "estimated_cost_usd": result.estimated_cost_usd,
            "raw_payload": result.raw_payload,
        }
        if store is not None:
            raw_payload_cas = store.put_bytes(
                json.dumps(raw_payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
            )

        artifacts: List[ArtifactRef] = []
        if raw_payload_cas is not None:
            artifacts.append(
                ArtifactRef(
                    artifact_id=f"{context.run_id}:{self.backend_id}_raw_payload",
                    artifact_type=SCANNER_RAW_PAYLOAD_ARTIFACT_TYPE,
                    storage_ref=raw_payload_cas,
                    mime_type="application/json",
                    md={"backend_id": self.backend_id, "model_id": result.model_id or self.default_model_id},
                )
            )

        page_count = max(1, int(result.page_count or 1))
        envelope = ScannerEnvelope(
            schema_version="scanner_envelope_v1",
            scan_run=ScanRun(
                run_id=context.run_id,
                backend_id=self.backend_id,
                backend_class=self.backend_class,
                support_tier=self.support_tier,  # type: ignore[arg-type]
                status="succeeded",
                file_id=context.file_id,
                file_version_id=context.file_version_id,
                document_version_id=context.document_version_id,
                config_hash=context.config_hash,
                started_at=started_at,
                completed_at=time.time(),
                model_id=result.model_id or self.default_model_id,
                md={
                    "adapter_context": context.md,
                    "policy": policy.to_payload(),
                    "estimated_cost": result.estimated_cost_usd,
                    "raw_payload_cas": raw_payload_cas,
                },
            ),
            contract=ScanContract(
                legacy_output_contract=None,
                raw_backend_contract=self.raw_backend_contract,
                acquisition_mode=self.acquisition_mode,  # type: ignore[arg-type]
                projection_kinds=["canonical_markdown", "canonical_text", "chunk_compat"],
                structure_level="block",
                geometry_level="block",
                md={"policy_gated": True},
            ),
            artifacts=artifacts,
            pages=[PageRecord(page_index=idx, acquisition_mode=self.acquisition_mode) for idx in range(1, page_count + 1)],  # type: ignore[arg-type]
            projections=[
                Projection(
                    projection_id=f"{context.run_id}:canonical_markdown",
                    projection_kind="canonical_markdown",
                    text=result.markdown,
                    source_page_indices=list(range(1, page_count + 1)),
                ),
                Projection(
                    projection_id=f"{context.run_id}:canonical_text",
                    projection_kind="canonical_text",
                    text=_markdown_to_text(result.markdown),
                    source_page_indices=list(range(1, page_count + 1)),
                ),
                Projection(
                    projection_id=f"{context.run_id}:chunk_compat",
                    projection_kind="chunk_compat",
                    text=result.markdown,
                    source_page_indices=list(range(1, page_count + 1)),
                ),
            ],
            routing=[
                RoutingDecision(
                    backend_id=self.backend_id,
                    action="escalated" if self.support_tier == "premium_fallback" else "selected",
                    reason="policy_allowed_mock_provider",
                    page_indices=list(range(1, page_count + 1)),
                    md={"policy": policy.to_payload()},
                )
            ],
            quality={"estimated_cost_usd": result.estimated_cost_usd},
            warnings=list(result.warnings),
        )
        validate_scanner_envelope(envelope)
        return envelope


class MistralOCRMockAdapter(_ProviderBase):
    backend_id = "mistral_ocr"
    backend_class = "managed_general_parser"
    support_tier = "first_class"
    raw_backend_contract = "mistral_ocr_mock"
    acquisition_mode = "ocr"
    env_key = "MISTRAL_API_KEY"
    default_model_id = "mistral-ocr"


class GeminiDocumentFallbackMockAdapter(_ProviderBase):
    backend_id = "gemini_document_fallback"
    backend_class = "premium_hard_document_escalator"
    support_tier = "premium_fallback"
    raw_backend_contract = "gemini_document_mock"
    acquisition_mode = "vision_only"
    env_key = "GEMINI_API_KEY"
    default_model_id = "gemini-premium-document"

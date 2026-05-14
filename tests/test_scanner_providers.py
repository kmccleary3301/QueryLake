from __future__ import annotations

import json

import pytest

from QueryLake.files.object_store import LocalCASObjectStore
from QueryLake.scanning.adapters import ScannerRunContext
from QueryLake.scanning.providers import (
    GeminiDocumentFallbackMockAdapter,
    MistralOCRMockAdapter,
    ProviderMockResult,
    ProviderPolicy,
    ProviderPolicyError,
)


def _context(backend_id: str) -> ScannerRunContext:
    return ScannerRunContext(
        run_id=f"{backend_id}_run",
        backend_id=backend_id,
        backend_class="managed_general_parser",
        support_tier="first_class",
        file_id="file_1",
        file_version_id="fv_1",
        config_hash="provider-policy-v1",
    )


def test_mistral_mock_adapter_requires_managed_policy(tmp_path):
    adapter = MistralOCRMockAdapter(
        mock_result=ProviderMockResult(
            markdown="## Page 1\n\nManaged OCR text",
            raw_payload={"pages": [{"index": 1}]},
            page_count=1,
            model_id="mistral-test",
            estimated_cost_usd=0.02,
        )
    )

    with pytest.raises(ProviderPolicyError, match="managed_policy_denied"):
        adapter.scan_with_policy(context=_context("mistral_ocr"), policy=ProviderPolicy())

    store = LocalCASObjectStore(tmp_path / "cas")
    envelope = adapter.scan_with_policy(
        context=_context("mistral_ocr"),
        policy=ProviderPolicy(allow_managed=True, estimated_cost_usd=0.02, max_cost_usd=0.10),
        store=store,
    )

    assert envelope.scan_run.backend_id == "mistral_ocr"
    assert envelope.contract.acquisition_mode == "ocr"
    assert envelope.scan_run.md["estimated_cost"] == 0.02
    raw_ref = envelope.artifacts[0].storage_ref
    assert json.loads(store.get_bytes(raw_ref).decode("utf-8"))["model_id"] == "mistral-test"


def test_gemini_premium_mock_adapter_requires_premium_and_budget(tmp_path):
    adapter = GeminiDocumentFallbackMockAdapter(
        mock_result=ProviderMockResult(
            markdown="## Page 1\n\nPremium visual extraction",
            raw_payload={"vision": True},
            page_count=1,
            model_id="gemini-test",
            estimated_cost_usd=4.0,
        )
    )

    with pytest.raises(ProviderPolicyError, match="premium_policy_denied"):
        adapter.scan_with_policy(context=_context("gemini_document_fallback"), policy=ProviderPolicy(allow_managed=True))

    with pytest.raises(ProviderPolicyError, match="budget_policy_denied"):
        adapter.scan_with_policy(
            context=_context("gemini_document_fallback"),
            policy=ProviderPolicy(allow_premium=True, estimated_cost_usd=4.0, max_cost_usd=1.0),
        )

    envelope = adapter.scan_with_policy(
        context=_context("gemini_document_fallback"),
        policy=ProviderPolicy(allow_premium=True, estimated_cost_usd=4.0, max_cost_usd=5.0),
        store=LocalCASObjectStore(tmp_path / "cas"),
    )

    assert envelope.scan_run.backend_id == "gemini_document_fallback"
    assert envelope.scan_run.support_tier == "premium_fallback"
    assert envelope.contract.acquisition_mode == "vision_only"
    assert envelope.routing[0].action == "escalated"


def test_provider_live_availability_does_not_expose_secret_values(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "super-secret")
    availability = MistralOCRMockAdapter(live_enabled=True).check_available()

    assert availability.reason == "live_adapter_not_implemented"
    assert availability.md["credential_present"] is True
    assert "super-secret" not in str(availability.to_payload())

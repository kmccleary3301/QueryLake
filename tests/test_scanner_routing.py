from __future__ import annotations

from QueryLake.scanning.contracts import ScanRequest
from QueryLake.scanning.registry import build_default_scanner_registry
from QueryLake.scanning.routing import (
    RoutingPolicy,
    explain_routing_plan,
    plan_scan_route,
    policy_from_request,
    routing_plan_to_markdown,
)


def _registry():
    return build_default_scanner_registry()


def test_policy_from_request_defaults_to_local_safe_behavior():
    request = ScanRequest(request_id="req", source_ref="cas", mime_type="application/pdf")
    policy = policy_from_request(request)

    assert policy.allow_managed is False
    assert policy.allow_premium is False
    assert policy.allow_shadow is False
    assert policy.prefer_native_text is True
    assert policy.privacy_class == "local"


def test_born_digital_pdf_prefers_native_text_lane():
    request = ScanRequest(
        request_id="req_native",
        source_ref="cas",
        mime_type="application/pdf",
        logical_name="paper.pdf",
        route_hints={"has_native_text": True, "capture_mode": "born_digital"},
    )

    plan = plan_scan_route(_registry(), request)

    assert plan.primary_backend_id == "pymupdf4llm_native"
    assert plan.decisions[0].backend_id == "pymupdf4llm_native"
    assert plan.decisions[0].action == "selected"


def test_weak_native_text_routes_away_from_native_lane():
    request = ScanRequest(
        request_id="req_weak_native",
        source_ref="cas",
        mime_type="application/pdf",
        logical_name="weak.pdf",
        route_hints={
            "has_native_text": True,
            "capture_mode": "born_digital",
            "native_text_quality": "weak",
        },
    )

    plan = plan_scan_route(_registry(), request)

    assert plan.primary_backend_id == "chandra_1"
    assert plan.decisions[0].backend_id == "pymupdf4llm_native"
    assert plan.decisions[0].action == "blocked"
    assert plan.decisions[0].reason == "native_text_quality_rejected"


def test_scanned_pdf_uses_local_continuity_and_blocks_managed_and_premium_by_default():
    request = ScanRequest(
        request_id="req_scan",
        source_ref="cas",
        mime_type="application/pdf",
        logical_name="scan.pdf",
        route_hints={"capture_mode": "scanned"},
    )

    plan = plan_scan_route(_registry(), request)

    assert plan.primary_backend_id == "chandra_1"
    denied = {(decision.backend_id, decision.reason) for decision in plan.decisions if decision.action == "blocked"}
    assert ("mistral_ocr", "managed_policy_denied") in denied or ("mistral_ocr", "privacy_policy_denied") in denied
    assert ("gemini_document_fallback", "premium_policy_denied") in denied


def test_managed_route_can_be_allowed_without_premium():
    request = ScanRequest(
        request_id="req_managed",
        source_ref="cas",
        mime_type="application/pdf",
        logical_name="scan.pdf",
        route_hints={"capture_mode": "scanned"},
    )
    policy = RoutingPolicy(allow_managed=True, allow_premium=False, privacy_class="managed")

    plan = plan_scan_route(_registry(), request, policy)

    mistral = [decision for decision in plan.decisions if decision.backend_id == "mistral_ocr"][0]
    gemini = [decision for decision in plan.decisions if decision.backend_id == "gemini_document_fallback"][0]
    assert mistral.action in {"skipped", "selected"}
    assert mistral.policy_status == "allowed"
    assert gemini.action == "blocked"
    assert gemini.reason == "premium_policy_denied"


def test_premium_fallback_is_allowed_only_when_policy_allows_it():
    request = ScanRequest(
        request_id="req_premium",
        source_ref="cas",
        mime_type="image/png",
        logical_name="hard.png",
        route_hints={"capture_mode": "photo"},
    )
    policy = RoutingPolicy(allow_managed=True, allow_premium=True, privacy_class="managed")

    plan = plan_scan_route(_registry(), request, policy)

    gemini = [decision for decision in plan.decisions if decision.backend_id == "gemini_document_fallback"][0]
    assert gemini.action in {"skipped", "selected"}
    assert gemini.policy_status in {"allowed", None}


def test_shadow_backend_never_becomes_primary():
    request = ScanRequest(
        request_id="req_shadow",
        source_ref="cas",
        mime_type="application/pdf",
        logical_name="scan.pdf",
        route_hints={"capture_mode": "scanned"},
    )
    policy = RoutingPolicy(allow_shadow=True, shadow_backend_ids=["mineru_shadow"])

    plan = plan_scan_route(_registry(), request, policy)

    assert plan.primary_backend_id == "chandra_1"
    assert plan.shadow_backend_ids == ["mineru_shadow"]
    assert any(decision.backend_id == "mineru_shadow" and decision.action == "shadowed" for decision in plan.decisions)


def test_force_backend_can_select_explicit_only_backend():
    request = ScanRequest(request_id="req_force", source_ref="cas", mime_type="application/pdf")
    policy = RoutingPolicy(force_backend_id="docling_local")

    plan = plan_scan_route(_registry(), request, policy)

    assert plan.primary_backend_id == "docling_local"
    assert plan.decisions[0].reason == "forced_backend"


def test_routing_plan_explanation_is_bounded_and_auditable():
    request = ScanRequest(
        request_id="req_explain",
        source_ref="cas",
        mime_type="application/pdf",
        logical_name="scan.pdf",
        route_hints={"capture_mode": "scanned"},
    )

    plan = plan_scan_route(_registry(), request)
    explanation = explain_routing_plan(plan)
    markdown = routing_plan_to_markdown(plan)

    assert explanation["primary_backend_id"] == "chandra_1"
    assert explanation["action_counts"]["selected"] == 1
    assert explanation["blocked_reasons"]["premium_policy_denied"] == 1
    assert any(decision["backend_id"] == "mistral_ocr" for decision in explanation["decisions"])
    assert "| backend_id | action | reason | policy_status |" in markdown
    assert "premium_policy_denied" in markdown

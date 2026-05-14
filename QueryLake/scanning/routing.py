from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from QueryLake.scanning.contracts import RoutingDecision, ScanRequest
from QueryLake.scanning.registry import ScannerBackendSpec, get_backend_spec


@dataclass(frozen=True)
class RoutingPolicy:
    allow_managed: bool = False
    allow_premium: bool = False
    allow_shadow: bool = False
    prefer_native_text: bool = True
    max_cost_class: Optional[str] = None
    privacy_class: str = "local"
    force_backend_id: Optional[str] = None
    shadow_backend_ids: List[str] = field(default_factory=list)

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RoutingPlan:
    primary_backend_id: Optional[str]
    decisions: List[RoutingDecision]
    shadow_backend_ids: List[str] = field(default_factory=list)

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


def explain_routing_plan(plan: RoutingPlan) -> Dict[str, Any]:
    """Return a bounded, serializable explanation for debugging route choices."""

    action_counts: Dict[str, int] = {}
    blocked_reasons: Dict[str, int] = {}
    selected_reasons: List[str] = []
    for decision in plan.decisions:
        action_counts[decision.action] = action_counts.get(decision.action, 0) + 1
        if decision.action == "blocked":
            blocked_reasons[decision.reason] = blocked_reasons.get(decision.reason, 0) + 1
        if decision.action == "selected":
            selected_reasons.append(decision.reason)

    return {
        "primary_backend_id": plan.primary_backend_id,
        "shadow_backend_ids": list(plan.shadow_backend_ids),
        "decision_count": len(plan.decisions),
        "action_counts": action_counts,
        "blocked_reasons": blocked_reasons,
        "selected_reasons": selected_reasons,
        "decisions": [
            {
                "backend_id": decision.backend_id,
                "action": decision.action,
                "reason": decision.reason,
                "policy_status": decision.policy_status,
                "fallback_from": decision.fallback_from,
                "page_indices": list(decision.page_indices),
            }
            for decision in plan.decisions
        ],
    }


def routing_plan_to_markdown(plan: RoutingPlan) -> str:
    explanation = explain_routing_plan(plan)
    lines = [
        "# Scanner Routing Plan",
        "",
        f"- Primary backend: `{explanation['primary_backend_id'] or 'none'}`",
        f"- Shadow backends: `{', '.join(explanation['shadow_backend_ids']) or 'none'}`",
        f"- Decision count: `{explanation['decision_count']}`",
        "",
        "| backend_id | action | reason | policy_status |",
        "| --- | --- | --- | --- |",
    ]
    for decision in explanation["decisions"]:
        lines.append(
            f"| {decision['backend_id']} | {decision['action']} | {decision['reason']} | {decision['policy_status'] or ''} |"
        )
    return "\n".join(lines)


def policy_from_request(request: ScanRequest) -> RoutingPolicy:
    raw = dict(request.policy or {})
    return RoutingPolicy(
        allow_managed=bool(raw.get("allow_managed", False)),
        allow_premium=bool(raw.get("allow_premium", False)),
        allow_shadow=bool(raw.get("allow_shadow", False)),
        prefer_native_text=bool(raw.get("prefer_native_text", True)),
        max_cost_class=raw.get("max_cost_class"),
        privacy_class=str(raw.get("privacy_class", "local") or "local"),
        force_backend_id=raw.get("force_backend_id"),
        shadow_backend_ids=list(raw.get("shadow_backend_ids", []) or []),
    )


def _is_pdf(request: ScanRequest) -> bool:
    mime = str(request.mime_type or "").lower()
    name = str(request.logical_name or "").lower()
    return mime == "application/pdf" or name.endswith(".pdf")


def _capture_mode(request: ScanRequest) -> str:
    hint = request.route_hints.get("capture_mode") if request.route_hints else None
    if hint:
        return str(hint)
    if request.route_hints.get("has_native_text") is True:
        return "born_digital"
    return "unknown"


def _managed_allowed(spec: ScannerBackendSpec, policy: RoutingPolicy) -> bool:
    if spec.deployment_model != "managed":
        return True
    if spec.support_tier == "premium_fallback":
        return policy.allow_premium
    return policy.allow_managed


def _privacy_allowed(spec: ScannerBackendSpec, policy: RoutingPolicy) -> bool:
    if policy.privacy_class == "local" and spec.deployment_model == "managed":
        return False
    return True


def _candidate_allowed(spec: ScannerBackendSpec, policy: RoutingPolicy) -> tuple[bool, str]:
    if spec.routing_eligibility in {"deferred", "never"}:
        return False, "routing_not_eligible"
    if spec.routing_eligibility == "shadow_only":
        return False, "shadow_only_not_primary"
    if spec.support_tier == "premium_fallback" and not policy.allow_premium:
        return False, "premium_policy_denied"
    if spec.deployment_model == "managed" and spec.support_tier != "premium_fallback" and not policy.allow_managed:
        return False, "managed_policy_denied"
    if not _privacy_allowed(spec, policy):
        return False, "privacy_policy_denied"
    if not _managed_allowed(spec, policy):
        return False, "provider_policy_denied"
    return True, "eligible"


def plan_scan_route(registry: Dict[str, ScannerBackendSpec], request: ScanRequest, policy: Optional[RoutingPolicy] = None) -> RoutingPlan:
    policy = policy or policy_from_request(request)
    decisions: List[RoutingDecision] = []

    if policy.force_backend_id:
        spec = get_backend_spec(registry, policy.force_backend_id)
        allowed, reason = _candidate_allowed(spec, policy)
        if allowed or spec.routing_eligibility == "explicit_only":
            decisions.append(RoutingDecision(backend_id=spec.backend_id, action="selected", reason="forced_backend"))
            return RoutingPlan(primary_backend_id=spec.backend_id, decisions=decisions)
        decisions.append(RoutingDecision(backend_id=spec.backend_id, action="blocked", reason=reason, policy_status="denied"))
        return RoutingPlan(primary_backend_id=None, decisions=decisions)

    capture_mode = _capture_mode(request)
    has_native_text = bool(request.route_hints.get("has_native_text", False))
    native_text_quality = str(request.route_hints.get("native_text_quality", "") or "").strip().lower()
    native_quality_rejected = native_text_quality in {"weak", "failed", "rejected", "low_quality"}

    ordered_candidates: List[str] = []
    if (
        _is_pdf(request)
        and policy.prefer_native_text
        and (capture_mode == "born_digital" or has_native_text)
        and not native_quality_rejected
    ):
        ordered_candidates.append("pymupdf4llm_native")
    if _is_pdf(request):
        ordered_candidates.extend(["chandra_1", "docling_local", "mistral_ocr", "gemini_document_fallback"])
    else:
        ordered_candidates.extend(["docling_local", "chandra_1", "mistral_ocr", "gemini_document_fallback"])

    seen = set()
    primary: Optional[str] = None
    if _is_pdf(request) and policy.prefer_native_text and native_quality_rejected and "pymupdf4llm_native" in registry:
        decisions.append(
            RoutingDecision(
                backend_id="pymupdf4llm_native",
                action="blocked",
                reason="native_text_quality_rejected",
                policy_status="denied",
                md={"native_text_quality": native_text_quality},
            )
        )
        seen.add("pymupdf4llm_native")
    for backend_id in ordered_candidates:
        if backend_id in seen or backend_id not in registry:
            continue
        seen.add(backend_id)
        spec = registry[backend_id]
        allowed, reason = _candidate_allowed(spec, policy)
        if allowed and primary is None:
            primary = backend_id
            decisions.append(RoutingDecision(backend_id=backend_id, action="selected", reason="first_eligible_candidate"))
        else:
            action = "skipped" if allowed else "blocked"
            decisions.append(
                RoutingDecision(
                    backend_id=backend_id,
                    action=action,
                    reason="lower_priority_candidate" if allowed else reason,
                    policy_status="allowed" if allowed else "denied",
                )
            )

    shadow_backend_ids: List[str] = []
    if policy.allow_shadow:
        for backend_id in policy.shadow_backend_ids:
            if backend_id not in registry:
                decisions.append(RoutingDecision(backend_id=backend_id, action="blocked", reason="unknown_shadow_backend"))
                continue
            spec = registry[backend_id]
            if spec.routing_eligibility != "shadow_only":
                decisions.append(RoutingDecision(backend_id=backend_id, action="blocked", reason="not_shadow_backend"))
                continue
            shadow_backend_ids.append(backend_id)
            decisions.append(RoutingDecision(backend_id=backend_id, action="shadowed", reason="shadow_policy_allowed"))

    return RoutingPlan(primary_backend_id=primary, decisions=decisions, shadow_backend_ids=shadow_backend_ids)

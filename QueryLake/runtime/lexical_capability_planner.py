from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Dict, List, Optional

from QueryLake.runtime.db_compat import (
    CapabilityDescriptor,
    DeploymentProfile,
    QueryLakeUnsupportedFeatureError,
    get_capability_descriptor,
    get_deployment_profile,
)
from QueryLake.runtime.query_ir_v2 import QueryIRV2


_FIELD_OR_BOOLEAN_RE = re.compile(r"(^|\s)([+\-])\w+|(\w+:\w+)|\b(and|or|not)\b", re.IGNORECASE)
_QUOTE_RE = re.compile(r'"([^"\\]*(?:\\.[^"\\]*)*)"')
_PROXIMITY_RE = re.compile(r'"([^"\\]*(?:\\.[^"\\]*)*)"\~\d+')


def _coerce_query_ir_v2(query_ir_v2: Optional[Any]) -> Optional[QueryIRV2]:
    if query_ir_v2 is None:
        return None
    if isinstance(query_ir_v2, QueryIRV2):
        return query_ir_v2
    if isinstance(query_ir_v2, dict):
        if not str(query_ir_v2.get("route_id") or ""):
            return None
        if not str(query_ir_v2.get("representation_scope_id") or ""):
            return None
        return QueryIRV2.model_validate(query_ir_v2)
    return QueryIRV2.model_validate(query_ir_v2)


def _extract_query_features(query_text: str, *, query_ir_v2: Optional[QueryIRV2] = None) -> List[str]:
    features: List[str] = []
    hinted_features = ((query_ir_v2.planner_hints.get("query_features") if query_ir_v2 else {}) or {})
    for feature in hinted_features.keys():
        feature_name = str(feature or "")
        if feature_name and feature_name not in features:
            features.append(feature_name)
    query = str(query_text or "")
    has_quotes = bool(_QUOTE_RE.search(query))
    has_proximity = bool(_PROXIMITY_RE.search(query))
    has_hard_constraints = bool(_FIELD_OR_BOOLEAN_RE.search(query))
    if (has_quotes or has_proximity or has_hard_constraints) and "advanced_operators" not in features:
        features.append("advanced_operators")
    if has_quotes and "phrase_boost" not in features:
        features.append("phrase_boost")
    if has_proximity and "proximity" not in features:
        features.append("proximity")
    if has_hard_constraints and "hard_constraints" not in features:
        features.append("hard_constraints")
    return features


@dataclass(frozen=True)
class LexicalQueryCapabilityPlan:
    query_text: str
    query_features: List[str]
    required_capabilities: List[str]
    degraded_capabilities: List[str]
    unsupported_capabilities: List[str]
    capability_states: Dict[str, str]
    support_class: str = "native_supported"
    blocking_capability: Optional[str] = None

    def to_payload(self) -> Dict[str, object]:
        return {
            "query_features": list(self.query_features),
            "required_capabilities": list(self.required_capabilities),
            "degraded_capabilities": list(self.degraded_capabilities),
            "unsupported_capabilities": list(self.unsupported_capabilities),
            "capability_states": dict(self.capability_states),
            "support_class": str(self.support_class),
            "blocking_capability": self.blocking_capability,
        }


def _descriptor_support_state(descriptor: Optional[CapabilityDescriptor]) -> str:
    return descriptor.support_state if descriptor is not None else "unsupported"


def build_lexical_query_capability_plan(
    query_text: str,
    *,
    profile: Optional[DeploymentProfile] = None,
    query_ir_v2: Optional[Any] = None,
) -> LexicalQueryCapabilityPlan:
    effective_profile = profile or get_deployment_profile()
    query = str(query_text or "")
    coerced_query_ir_v2 = _coerce_query_ir_v2(query_ir_v2)
    features: List[str] = []
    required: List[str] = []
    degraded: List[str] = []
    unsupported: List[str] = []
    states: Dict[str, str] = {}

    def register(capability_id: str, feature_name: str) -> None:
        if feature_name not in features:
            features.append(feature_name)
        descriptor = get_capability_descriptor(capability_id, profile=effective_profile)
        state = _descriptor_support_state(descriptor)
        states[capability_id] = state
        if capability_id not in required:
            required.append(capability_id)
        if state == "degraded" and capability_id not in degraded:
            degraded.append(capability_id)
        elif state in {"unsupported", "planned"} and capability_id not in unsupported:
            unsupported.append(capability_id)

    features = _extract_query_features(query, query_ir_v2=coerced_query_ir_v2)
    if "advanced_operators" in features:
        register("retrieval.lexical.advanced_operators", "advanced_operators")
    if "phrase_boost" in features:
        register("retrieval.lexical.phrase_boost", "phrase_boost")
    if "proximity" in features:
        register("retrieval.lexical.proximity", "proximity")
    if "hard_constraints" in features:
        register("retrieval.lexical.hard_constraints", "hard_constraints")

    support_class = "native_supported"
    blocking_capability = None
    if len(unsupported) > 0:
        support_class = "unsupported"
        blocking_capability = unsupported[0]
    elif len(degraded) > 0:
        support_class = "degraded_supported"

    return LexicalQueryCapabilityPlan(
        query_text=query,
        query_features=features,
        required_capabilities=required,
        degraded_capabilities=degraded,
        unsupported_capabilities=unsupported,
        capability_states=states,
        support_class=support_class,
        blocking_capability=blocking_capability,
    )


def build_profile_lexical_semantics_summary(
    *,
    profile: Optional[DeploymentProfile] = None,
) -> Dict[str, object]:
    effective_profile = profile or get_deployment_profile()
    capability_ids = [
        "retrieval.lexical.bm25",
        "retrieval.lexical.advanced_operators",
        "retrieval.lexical.phrase_boost",
        "retrieval.lexical.proximity",
        "retrieval.lexical.hard_constraints",
    ]
    capability_states: Dict[str, str] = {
        capability_id: _descriptor_support_state(
            get_capability_descriptor(capability_id, profile=effective_profile)
        )
        for capability_id in capability_ids
    }
    degraded_capabilities = [
        capability_id for capability_id, state in capability_states.items() if state == "degraded"
    ]
    unsupported_capabilities = [
        capability_id for capability_id, state in capability_states.items() if state in {"unsupported", "planned"}
    ]
    support_class = "native_supported"
    if unsupported_capabilities:
        support_class = "unsupported"
    elif degraded_capabilities:
        support_class = "degraded_supported"
    return {
        "support_class": support_class,
        "capability_states": capability_states,
        "degraded_capabilities": degraded_capabilities,
        "unsupported_capabilities": unsupported_capabilities,
    }


def build_route_lexical_semantics_summary(
    *,
    route_id: str,
    profile: Optional[DeploymentProfile] = None,
) -> Dict[str, object]:
    effective_profile = profile or get_deployment_profile()
    base = build_profile_lexical_semantics_summary(profile=effective_profile)
    capability_states = dict(base.get("capability_states") or {})
    degraded_capabilities = [
        capability_id
        for capability_id in list(base.get("degraded_capabilities") or [])
        if str(capability_id or "")
    ]
    unsupported_capabilities = [
        capability_id
        for capability_id in list(base.get("unsupported_capabilities") or [])
        if str(capability_id or "")
    ]

    route_id_value = str(route_id or "")
    if not route_id_value.startswith(("search_bm25", "search_file_chunks", "search_hybrid")):
        return base

    bm25_state = str(capability_states.get("retrieval.lexical.bm25") or "unsupported")
    exact_constraint_capability_ids = [
        "retrieval.lexical.advanced_operators",
        "retrieval.lexical.phrase_boost",
        "retrieval.lexical.proximity",
        "retrieval.lexical.hard_constraints",
    ]
    exact_constraint_degraded_capabilities = [
        capability_id
        for capability_id in exact_constraint_capability_ids
        if capability_states.get(capability_id) == "degraded"
    ]
    exact_constraint_unsupported_capabilities = [
        capability_id
        for capability_id in exact_constraint_capability_ids
        if capability_states.get(capability_id) in {"unsupported", "planned"}
    ]

    if bm25_state in {"unsupported", "planned"}:
        support_class = "unsupported"
    elif bm25_state == "degraded":
        support_class = "degraded_supported"
    elif exact_constraint_degraded_capabilities or exact_constraint_unsupported_capabilities:
        support_class = "degraded_supported"
    else:
        support_class = "native_supported"

    return {
        "support_class": support_class,
        "capability_states": capability_states,
        "degraded_capabilities": degraded_capabilities,
        "unsupported_capabilities": unsupported_capabilities,
        "gold_recommended_for_exact_constraints": bool(
            exact_constraint_degraded_capabilities or exact_constraint_unsupported_capabilities
        ),
        "exact_constraint_degraded_capabilities": exact_constraint_degraded_capabilities,
        "exact_constraint_unsupported_capabilities": exact_constraint_unsupported_capabilities,
    }


def require_lexical_query_capabilities(
    query_text: str,
    *,
    profile: Optional[DeploymentProfile] = None,
    route_label: str = "lexical retrieval",
    query_ir_v2: Optional[Any] = None,
) -> LexicalQueryCapabilityPlan:
    effective_profile = profile or get_deployment_profile()
    plan = build_lexical_query_capability_plan(query_text, profile=effective_profile, query_ir_v2=query_ir_v2)
    if len(plan.unsupported_capabilities) == 0:
        return plan

    blocking_capability = plan.unsupported_capabilities[0]
    if blocking_capability == "retrieval.lexical.hard_constraints":
        message = (
            f"{route_label} requires hard lexical constraint support on deployment profile '{effective_profile.id}'."
        )
        hint = "Use the gold profile or remove fielded/boolean hard constraints from the query."
    elif blocking_capability == "retrieval.lexical.proximity":
        message = (
            f"{route_label} requires lexical proximity support on deployment profile '{effective_profile.id}'."
        )
        hint = "Use the gold profile or remove phrase slop/proximity operators from the query."
    elif blocking_capability == "retrieval.lexical.phrase_boost":
        message = (
            f"{route_label} requires quoted-phrase lexical boost support on deployment profile '{effective_profile.id}'."
        )
        hint = "Use the gold profile or remove quoted-phrase lexical constraints from the query."
    else:
        message = (
            f"{route_label} requires advanced lexical operator support on deployment profile '{effective_profile.id}'."
        )
        hint = "Use the gold profile or issue a simpler lexical query."

    raise QueryLakeUnsupportedFeatureError(
        capability=blocking_capability,
        profile=effective_profile.id,
        support_state=plan.capability_states.get(blocking_capability, "unsupported"),  # type: ignore[arg-type]
        backend_stack=effective_profile.backend_stack,
        message=message,
        hint=hint,
    )

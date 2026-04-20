from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any


_CERT_STATE_RANK = {
    "draft": 0,
    "shadow_certified": 1,
    "candidate_eligible": 2,
    "primary_eligible": 3,
    "revoked": -1,
}

_MODE_MIN_CERT_STATE = {
    "shadow": "shadow_certified",
    "candidate_primary": "candidate_eligible",
    "primary": "primary_eligible",
}


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _fingerprint(payload: dict[str, Any] | None) -> str:
    canonical = json.dumps(payload or {}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _package_ref(package_id: str, package_revision: str) -> str:
    return f"{package_id}@{package_revision}"


def _cert_key(*, profile_id: str, route_id: str, package_ref: str) -> str:
    return f"{profile_id}:{route_id}:cert:{package_ref}"


def _apply_key(*, profile_id: str, route_id: str, package_ref: str) -> str:
    return f"{profile_id}:{route_id}:apply:{package_ref}"


def _activation_key(*, profile_id: str, route_id: str, mode: str) -> str:
    return f"{profile_id}:{route_id}:activation:{mode}"


def load_route_serving_registry(path: str | Path) -> dict[str, Any]:
    registry_path = Path(path)
    if not registry_path.exists():
        return {
            "schema_version": "canon_route_serving_registry_v1",
            "generated_at": _utc_now(),
            "certifications": {},
            "apply_states": {},
            "activations": {},
            "history": [],
        }
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    if str(payload.get("schema_version") or "") != "canon_route_serving_registry_v1":
        raise ValueError(f"Unsupported route serving registry schema: {payload.get('schema_version')}")
    payload.setdefault("certifications", {})
    payload.setdefault("apply_states", {})
    payload.setdefault("activations", {})
    payload.setdefault("history", [])
    return payload


def save_route_serving_registry(payload: dict[str, Any], path: str | Path) -> str:
    registry_path = Path(path)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(registry_path)


def record_route_package_certification(
    *,
    registry_path: str | Path,
    profile_id: str,
    route_id: str,
    package_id: str,
    package_revision: str,
    graph_id: str,
    certification_state: str,
    evidence_ref: str,
    target_executor_id: str,
    compile_options: dict[str, Any] | None = None,
    source_shadow_baseline_ref: str | None = None,
) -> dict[str, Any]:
    package_ref = _package_ref(package_id, package_revision)
    registry = load_route_serving_registry(registry_path)
    entry = {
        "schema_version": "canon_route_package_certification_v1",
        "profile_id": profile_id,
        "route_id": route_id,
        "package_id": package_id,
        "package_revision": package_revision,
        "package_ref": package_ref,
        "graph_id": graph_id,
        "certification_state": certification_state,
        "certification_evidence_ref": evidence_ref,
        "target_executor_id": target_executor_id,
        "compile_options_fingerprint": _fingerprint(compile_options),
        "compile_options": dict(compile_options or {}),
        "source_shadow_baseline_ref": source_shadow_baseline_ref,
        "certified_at": _utc_now(),
        "revoked_at": None,
    }
    key = _cert_key(profile_id=profile_id, route_id=route_id, package_ref=package_ref)
    registry["certifications"][key] = entry
    registry["generated_at"] = _utc_now()
    registry["history"].append(
        {
            "recorded_at": _utc_now(),
            "kind": "package_certification",
            "profile_id": profile_id,
            "route_id": route_id,
            "package_ref": package_ref,
            "certification_state": certification_state,
        }
    )
    save_route_serving_registry(registry, registry_path)
    return entry


def record_route_apply_state(
    *,
    registry_path: str | Path,
    profile_id: str,
    route_id: str,
    package_id: str,
    package_revision: str,
    graph_id: str,
    projection_descriptors: list[str],
    config_payload: dict[str, Any] | None = None,
    dependency_payload: dict[str, Any] | None = None,
    healthy: bool = True,
) -> dict[str, Any]:
    package_ref = _package_ref(package_id, package_revision)
    registry = load_route_serving_registry(registry_path)
    key = _apply_key(profile_id=profile_id, route_id=route_id, package_ref=package_ref)
    entry = {
        "schema_version": "canon_route_apply_state_v1",
        "apply_state_ref": key,
        "profile_id": profile_id,
        "route_id": route_id,
        "package_id": package_id,
        "package_revision": package_revision,
        "package_ref": package_ref,
        "graph_id": graph_id,
        "projection_descriptors": list(projection_descriptors),
        "config_checksum": _fingerprint(config_payload),
        "dependency_checksum": _fingerprint(dependency_payload),
        "healthy": bool(healthy),
        "applied_at": _utc_now(),
    }
    registry["apply_states"][key] = entry
    registry["generated_at"] = _utc_now()
    registry["history"].append(
        {
            "recorded_at": _utc_now(),
            "kind": "route_apply_state",
            "profile_id": profile_id,
            "route_id": route_id,
            "package_ref": package_ref,
            "apply_state_ref": key,
        }
    )
    save_route_serving_registry(registry, registry_path)
    return entry


def record_route_activation(
    *,
    registry_path: str | Path,
    profile_id: str,
    route_id: str,
    mode: str,
    pointer_id: str,
    package_id: str,
    package_revision: str,
    apply_state_ref: str,
    approval_ref: str,
    predecessor_pointer_id: str | None = None,
    rollback_target_pointer_id: str | None = None,
    candidate_scope: dict[str, Any] | None = None,
) -> dict[str, Any]:
    package_ref = _package_ref(package_id, package_revision)
    registry = load_route_serving_registry(registry_path)
    key = _activation_key(profile_id=profile_id, route_id=route_id, mode=mode)
    entry = {
        "schema_version": "canon_route_activation_v1",
        "activation_ref": key,
        "profile_id": profile_id,
        "route_id": route_id,
        "mode": mode,
        "active": True,
        "pointer_id": pointer_id,
        "package_ref": package_ref,
        "apply_state_ref": apply_state_ref,
        "approval_ref": approval_ref,
        "predecessor_pointer_id": predecessor_pointer_id,
        "rollback_target_pointer_id": rollback_target_pointer_id,
        "candidate_scope": dict(candidate_scope or {}),
        "activated_at": _utc_now(),
        "deactivated_at": None,
        "deactivation_reason": None,
    }
    registry["activations"][key] = entry
    registry["generated_at"] = _utc_now()
    registry["history"].append(
        {
            "recorded_at": _utc_now(),
            "kind": "route_activation",
            "profile_id": profile_id,
            "route_id": route_id,
            "mode": mode,
            "pointer_id": pointer_id,
            "package_ref": package_ref,
        }
    )
    save_route_serving_registry(registry, registry_path)
    return entry


def deactivate_route_activation(
    *,
    registry_path: str | Path,
    profile_id: str,
    route_id: str,
    mode: str,
    reason: str,
) -> dict[str, Any] | None:
    registry = load_route_serving_registry(registry_path)
    key = _activation_key(profile_id=profile_id, route_id=route_id, mode=mode)
    entry = dict(dict(registry.get("activations") or {}).get(key) or {}) or None
    if entry is None:
        return None
    entry["active"] = False
    entry["deactivated_at"] = _utc_now()
    entry["deactivation_reason"] = str(reason)
    registry["activations"][key] = entry
    registry["generated_at"] = _utc_now()
    registry["history"].append(
        {
            "recorded_at": _utc_now(),
            "kind": "route_activation_deactivated",
            "profile_id": profile_id,
            "route_id": route_id,
            "mode": mode,
            "reason": str(reason),
        }
    )
    save_route_serving_registry(registry, registry_path)
    return entry


def get_route_package_certification(
    *,
    registry: dict[str, Any],
    profile_id: str,
    route_id: str,
    package_ref: str,
) -> dict[str, Any] | None:
    return dict(dict(registry.get("certifications") or {}).get(_cert_key(profile_id=profile_id, route_id=route_id, package_ref=package_ref)) or {}) or None


def get_route_apply_state(
    *,
    registry: dict[str, Any],
    profile_id: str,
    route_id: str,
    package_ref: str,
) -> dict[str, Any] | None:
    return dict(dict(registry.get("apply_states") or {}).get(_apply_key(profile_id=profile_id, route_id=route_id, package_ref=package_ref)) or {}) or None


def get_route_activation(
    *,
    registry: dict[str, Any],
    profile_id: str,
    route_id: str,
    mode: str,
) -> dict[str, Any] | None:
    return dict(dict(registry.get("activations") or {}).get(_activation_key(profile_id=profile_id, route_id=route_id, mode=mode)) or {}) or None


def _best_certification_for_route(
    *,
    registry: dict[str, Any],
    profile_id: str,
    route_id: str,
) -> dict[str, Any] | None:
    candidates = [
        dict(entry)
        for entry in list(dict(registry.get("certifications") or {}).values())
        if str(entry.get("profile_id") or "") == str(profile_id)
        and str(entry.get("route_id") or "") == str(route_id)
        and str(entry.get("certification_state") or "") != "revoked"
    ]
    if not candidates:
        return None
    candidates.sort(
        key=lambda entry: (
            _CERT_STATE_RANK.get(str(entry.get("certification_state") or ""), -1),
            str(entry.get("certified_at") or ""),
        ),
        reverse=True,
    )
    return candidates[0]


def build_route_slice_state(
    *,
    registry: dict[str, Any],
    profile_id: str,
    route_id: str,
) -> dict[str, Any]:
    primary_state = resolve_route_serving_state(
        registry=registry,
        profile_id=profile_id,
        route_id=route_id,
        mode="primary",
    )
    if bool(primary_state.get("resolved")):
        activation = dict(primary_state.get("activation") or {})
        return {
            "schema_version": "canon_route_slice_state_v1",
            "profile_id": profile_id,
            "route_id": route_id,
            "state": "primary_active",
            "rollback_ready": bool(activation.get("rollback_target_pointer_id")),
            "activation": activation,
            "certification": dict(primary_state.get("certification") or {}),
            "apply_state": dict(primary_state.get("apply_state") or {}),
            "blockers": [],
        }

    candidate_state = resolve_route_serving_state(
        registry=registry,
        profile_id=profile_id,
        route_id=route_id,
        mode="candidate_primary",
    )
    if bool(candidate_state.get("resolved")):
        activation = dict(candidate_state.get("activation") or {})
        return {
            "schema_version": "canon_route_slice_state_v1",
            "profile_id": profile_id,
            "route_id": route_id,
            "state": "candidate_primary_active",
            "rollback_ready": bool(activation.get("rollback_target_pointer_id")),
            "activation": activation,
            "certification": dict(candidate_state.get("certification") or {}),
            "apply_state": dict(candidate_state.get("apply_state") or {}),
            "blockers": [],
        }

    shadow_state = resolve_route_serving_state(
        registry=registry,
        profile_id=profile_id,
        route_id=route_id,
        mode="shadow",
    )
    if bool(shadow_state.get("resolved")):
        return {
            "schema_version": "canon_route_slice_state_v1",
            "profile_id": profile_id,
            "route_id": route_id,
            "state": "shadow",
            "rollback_ready": False,
            "activation": dict(shadow_state.get("activation") or {}),
            "certification": dict(shadow_state.get("certification") or {}),
            "apply_state": dict(shadow_state.get("apply_state") or {}),
            "blockers": [],
        }

    certification = _best_certification_for_route(
        registry=registry,
        profile_id=profile_id,
        route_id=route_id,
    )
    if certification is None:
        return {
            "schema_version": "canon_route_slice_state_v1",
            "profile_id": profile_id,
            "route_id": route_id,
            "state": "shadow",
            "rollback_ready": False,
            "activation": None,
            "certification": None,
            "apply_state": None,
            "blockers": [],
        }

    package_ref = str(certification.get("package_ref") or "")
    apply_state = get_route_apply_state(
        registry=registry,
        profile_id=profile_id,
        route_id=route_id,
        package_ref=package_ref,
    )
    blockers: list[str] = []
    if apply_state is None:
        blockers.append("route_apply_state_missing")
    elif not bool(apply_state.get("healthy")):
        blockers.append("route_apply_state_unhealthy")

    cert_state = str(certification.get("certification_state") or "")
    derived_state = "shadow"
    if _CERT_STATE_RANK.get(cert_state, -1) >= _CERT_STATE_RANK["candidate_eligible"]:
        derived_state = "candidate_primary_eligible"
    if _CERT_STATE_RANK.get(cert_state, -1) >= _CERT_STATE_RANK["primary_eligible"]:
        derived_state = "primary_eligible"

    return {
        "schema_version": "canon_route_slice_state_v1",
        "profile_id": profile_id,
        "route_id": route_id,
        "state": derived_state,
        "rollback_ready": False,
        "activation": None,
        "certification": certification,
        "apply_state": apply_state,
        "blockers": blockers,
    }


def build_candidate_canary_evidence_packet(
    *,
    registry: dict[str, Any],
    profile_id: str,
    route_id: str,
) -> dict[str, Any]:
    route_state = build_route_slice_state(
        registry=registry,
        profile_id=profile_id,
        route_id=route_id,
    )
    activation = dict(route_state.get("activation") or {})
    candidate_scope = dict(activation.get("candidate_scope") or {})
    return {
        "schema_version": "canon_candidate_canary_evidence_packet_v1",
        "profile_id": profile_id,
        "route_id": route_id,
        "state": str(route_state.get("state") or "shadow"),
        "candidate_primary_active": str(route_state.get("state") or "") == "candidate_primary_active",
        "rollback_ready": bool(route_state.get("rollback_ready")),
        "candidate_scope": candidate_scope,
        "activation": activation or None,
        "certification": route_state.get("certification"),
        "apply_state": route_state.get("apply_state"),
        "blockers": list(route_state.get("blockers") or []),
        "summary": {
            "pointer_id": activation.get("pointer_id"),
            "rollback_target_pointer_id": activation.get("rollback_target_pointer_id"),
            "package_ref": activation.get("package_ref") or dict(route_state.get("certification") or {}).get("package_ref"),
        },
    }


def resolve_route_serving_state(
    *,
    registry: dict[str, Any],
    profile_id: str,
    route_id: str,
    mode: str,
) -> dict[str, Any]:
    activation = get_route_activation(
        registry=registry,
        profile_id=profile_id,
        route_id=route_id,
        mode=mode,
    )
    blockers: list[str] = []
    if activation is None:
        blockers.append("route_activation_missing")
        return {
            "resolved": False,
            "blockers": blockers,
            "activation": None,
            "certification": None,
            "apply_state": None,
        }
    if not bool(activation.get("active", True)):
        blockers.append("route_activation_inactive")
        return {
            "resolved": False,
            "blockers": blockers,
            "activation": activation,
            "certification": None,
            "apply_state": None,
        }
    package_ref = str(activation.get("package_ref") or "")
    certification = get_route_package_certification(
        registry=registry,
        profile_id=profile_id,
        route_id=route_id,
        package_ref=package_ref,
    )
    if certification is None:
        blockers.append("route_package_certification_missing")
    else:
        required_state = _MODE_MIN_CERT_STATE.get(str(mode), "shadow_certified")
        observed_state = str(certification.get("certification_state") or "")
        if _CERT_STATE_RANK.get(observed_state, -1) < _CERT_STATE_RANK[required_state]:
            blockers.append("route_package_not_certified_for_activation_mode")
        if observed_state == "revoked":
            blockers.append("route_package_certification_revoked")
    apply_state_ref = str(activation.get("apply_state_ref") or "")
    apply_state = dict(dict(registry.get("apply_states") or {}).get(apply_state_ref) or {}) or None
    if apply_state is None:
        blockers.append("route_apply_state_missing")
    else:
        if not bool(apply_state.get("healthy")):
            blockers.append("route_apply_state_unhealthy")
        if str(apply_state.get("package_ref") or "") != package_ref:
            blockers.append("route_apply_state_package_mismatch")
    return {
        "resolved": len(blockers) == 0,
        "blockers": blockers,
        "activation": activation,
        "certification": certification,
        "apply_state": apply_state,
    }

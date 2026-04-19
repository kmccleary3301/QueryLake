from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from .authority_control_registry import apply_authority_control_bootstrap


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def load_pointer_registry(path: str | Path) -> dict[str, Any]:
    registry_path = Path(path)
    if not registry_path.exists():
        return {
            "schema_version": "canon_pointer_registry_v1",
            "generated_at": _utc_now(),
            "shadow_pointer": None,
            "candidate_primary_pointer": None,
            "primary_pointer": None,
            "history": [],
        }
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    if str(payload.get("schema_version") or "") != "canon_pointer_registry_v1":
        raise ValueError(f"Unsupported pointer registry schema: {payload.get('schema_version')}")
    return payload


def save_pointer_registry(payload: dict[str, Any], path: str | Path) -> str:
    registry_path = Path(path)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(registry_path)


def _validate_pointer_payload(pointer: dict[str, Any]) -> None:
    required_scalar_fields = ("pointer_id", "graph_id", "package_revision", "profile_id", "mode")
    for field_name in required_scalar_fields:
        if not str(pointer.get(field_name) or ""):
            raise ValueError(f"Pointer payload missing required field '{field_name}'.")
    route_ids = [str(route_id) for route_id in list(pointer.get("route_ids") or []) if str(route_id or "")]
    if not route_ids:
        raise ValueError("Pointer payload must include at least one route id.")
    package_bindings = dict(dict(pointer.get("metadata") or {}).get("package_bindings") or {})
    if len(route_ids) > 1:
        if not package_bindings:
            raise ValueError("Multi-route pointer payload requires route-level package bindings.")
        for route_id in route_ids:
            binding = dict(package_bindings.get(route_id) or {})
            if not binding:
                raise ValueError(f"Multi-route pointer payload missing package binding for route '{route_id}'.")
            for key in ("package_id", "package_revision", "graph_id"):
                if not str(binding.get(key) or ""):
                    raise ValueError(
                        f"Multi-route pointer payload has incomplete package binding for route '{route_id}'."
                    )


def apply_publish_plan(
    *,
    plan: dict[str, Any],
    registry_path: str | Path,
    authority_control_registry_path: str | Path | None = None,
) -> dict[str, Any]:
    if not bool(plan.get("allowed")):
        raise ValueError(f"Publish plan blocked: {', '.join(plan.get('blockers') or [])}")
    registry = load_pointer_registry(registry_path)
    target = dict(plan.get("target") or {})
    _validate_pointer_payload(target)
    for step in list(plan.get("steps") or []):
        step_id = str(step.get("step_id") or "")
        if step_id == "apply_authority_control_bootstrap":
            if authority_control_registry_path is None:
                raise ValueError("Authority/control registry path is required to apply authority/control bootstrap.")
            bundle = dict(dict(step.get("metadata") or {}).get("bootstrap_bundle") or {})
            apply_authority_control_bootstrap(
                bundle=bundle,
                registry_path=authority_control_registry_path,
            )
        elif step_id == "update_shadow_pointer":
            registry["shadow_pointer"] = dict(target)
        elif step_id == "promote_candidate_pointer":
            registry["candidate_primary_pointer"] = dict(target)
        elif step_id == "cutover_primary_pointer":
            registry["primary_pointer"] = dict(target)

    registry["generated_at"] = _utc_now()
    registry.setdefault("history", []).append(
        {
            "applied_at": _utc_now(),
            "mode_transition": plan.get("mode_transition"),
            "target_pointer_id": target.get("pointer_id"),
        }
    )
    save_pointer_registry(registry, registry_path)
    return registry


def apply_revert_plan(*, revert_plan: dict[str, Any], pointer: dict[str, Any], registry_path: str | Path) -> dict[str, Any]:
    if not bool(revert_plan.get("available")):
        raise ValueError("Revert plan is not available.")
    registry = load_pointer_registry(registry_path)
    revert_mode = str(revert_plan.get("revert_mode") or "")
    if revert_mode == "shadow":
        registry["shadow_pointer"] = dict(pointer)
    elif revert_mode == "candidate_primary":
        registry["candidate_primary_pointer"] = dict(pointer)
    elif revert_mode == "primary":
        registry["primary_pointer"] = dict(pointer)
    else:
        raise ValueError(f"Unsupported revert mode: {revert_mode}")
    registry["generated_at"] = _utc_now()
    registry.setdefault("history", []).append(
        {
            "reverted_at": _utc_now(),
            "revert_to_pointer_id": revert_plan.get("revert_to_pointer_id"),
            "revert_mode": revert_mode,
        }
    )
    save_pointer_registry(registry, registry_path)
    return registry

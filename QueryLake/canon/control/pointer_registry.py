from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any


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


def apply_publish_plan(*, plan: dict[str, Any], registry_path: str | Path) -> dict[str, Any]:
    if not bool(plan.get("allowed")):
        raise ValueError(f"Publish plan blocked: {', '.join(plan.get('blockers') or [])}")
    registry = load_pointer_registry(registry_path)
    target = dict(plan.get("target") or {})
    for step in list(plan.get("steps") or []):
        step_id = str(step.get("step_id") or "")
        if step_id == "update_shadow_pointer":
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

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any, Iterable


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _scope_key(*, profile_id: str, mode: str, routes: Iterable[str]) -> str:
    route_list = sorted({str(route_id) for route_id in routes if str(route_id or "")})
    return f"{profile_id}:{mode}:{'|'.join(route_list)}"


def load_authority_control_registry(path: str | Path) -> dict[str, Any]:
    registry_path = Path(path)
    if not registry_path.exists():
        return {
            "schema_version": "canon_authority_control_registry_v1",
            "generated_at": _utc_now(),
            "entries": {},
            "history": [],
        }
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    if str(payload.get("schema_version") or "") != "canon_authority_control_registry_v1":
        raise ValueError(
            f"Unsupported authority/control registry schema: {payload.get('schema_version')}"
        )
    payload.setdefault("entries", {})
    payload.setdefault("history", [])
    return payload


def save_authority_control_registry(payload: dict[str, Any], path: str | Path) -> str:
    registry_path = Path(path)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(registry_path)


def get_authority_control_bootstrap_entry(
    *,
    registry: dict[str, Any],
    profile_id: str,
    mode: str,
    routes: Iterable[str],
) -> dict[str, Any] | None:
    return dict(
        dict(registry.get("entries") or {}).get(
            _scope_key(profile_id=profile_id, mode=mode, routes=routes)
        )
        or {}
    ) or None


def apply_authority_control_bootstrap(
    *,
    bundle: dict[str, Any],
    registry_path: str | Path,
) -> dict[str, Any]:
    if str(bundle.get("schema_version") or "") != "canon_authority_control_bootstrap_bundle_v1":
        raise ValueError(
            f"Unsupported authority/control bootstrap bundle schema: {bundle.get('schema_version')}"
        )
    summary = dict(bundle.get("summary") or {})
    if not bool(summary.get("candidate_primary_bootstrap_ready")):
        raise ValueError("Authority/control bootstrap bundle is not ready for candidate-primary bootstrap.")

    profile_id = str(dict(bundle.get("profile") or {}).get("id") or "")
    mode = str(bundle.get("mode") or "shadow")
    routes = [str(route_id) for route_id in list(bundle.get("routes") or []) if str(route_id or "")]
    if not profile_id or not routes:
        raise ValueError("Authority/control bootstrap bundle is missing profile or route scope.")

    registry = load_authority_control_registry(registry_path)
    scope_key = _scope_key(profile_id=profile_id, mode=mode, routes=routes)
    entry = {
        "schema_version": "canon_authority_control_bootstrap_entry_v1",
        "scope_key": scope_key,
        "profile_id": profile_id,
        "mode": mode,
        "route_ids": routes,
        "applied_at": _utc_now(),
        "configuration_ready": bool(summary.get("configuration_ready")),
        "selected_package_resolved_count": int(summary.get("selected_package_resolved_count", 0)),
        "shadow_executable_count": int(summary.get("shadow_executable_count", 0)),
        "candidate_primary_bootstrap_ready": bool(summary.get("candidate_primary_bootstrap_ready")),
        "primary_bootstrap_ready": bool(summary.get("primary_bootstrap_ready")),
        "phase1a_bootstrap_executed": bool(
            dict(bundle.get("phase1a_bootstrap_bundle") or {}).get("execute")
        ),
        "phase1a_bootstrap_runtime_ready_after": bool(
            dict(dict(bundle.get("phase1a_bootstrap_bundle") or {}).get("summary") or {}).get(
                "declared_executable_routes_runtime_ready_after"
            )
        ),
        "route_bindings": dict(bundle.get("route_bindings") or {}),
        "recommendations": list(bundle.get("recommendations") or []),
        "bundle": bundle,
    }
    registry.setdefault("entries", {})[scope_key] = entry
    registry["generated_at"] = _utc_now()
    registry.setdefault("history", []).append(
        {
            "applied_at": _utc_now(),
            "scope_key": scope_key,
            "profile_id": profile_id,
            "mode": mode,
            "route_count": len(routes),
        }
    )
    save_authority_control_registry(registry, registry_path)
    return registry

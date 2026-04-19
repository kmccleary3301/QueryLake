from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any, Iterable, Optional


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _package_ref(package_id: str, package_revision: str) -> str:
    return f"{package_id}@{package_revision}"


def load_graph_package_registry(path: str | Path) -> dict[str, Any]:
    registry_path = Path(path)
    if not registry_path.exists():
        return {
            "schema_version": "canon_graph_package_registry_v1",
            "generated_at": _utc_now(),
            "packages": [],
            "route_index": {},
            "history": [],
        }
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    if str(payload.get("schema_version") or "") != "canon_graph_package_registry_v1":
        raise ValueError(f"Unsupported package registry schema: {payload.get('schema_version')}")
    return payload


def save_graph_package_registry(payload: dict[str, Any], path: str | Path) -> str:
    registry_path = Path(path)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(registry_path)


def _registry_record(
    *,
    bundle: dict[str, Any],
    artifact_path: str | None = None,
) -> dict[str, Any]:
    package_id = str(bundle.get("package_id") or "")
    package_revision = str(bundle.get("package_revision") or "")
    route_id = str(bundle.get("route_id") or "")
    graph = dict(bundle.get("graph") or {})
    pipeline = dict(bundle.get("pipeline") or {})
    return {
        "package_ref": _package_ref(package_id, package_revision),
        "package_id": package_id,
        "package_revision": package_revision,
        "route_id": route_id,
        "graph_id": str(graph.get("graph_id") or ""),
        "graph_name": str(graph.get("graph_name") or ""),
        "node_count": int(graph.get("node_count") or 0),
        "requested_outputs": list(graph.get("requested_outputs") or []),
        "enabled_stage_ids": [str(value) for value in list(pipeline.get("enabled_stage_ids") or [])],
        "compile_options": dict(pipeline.get("compile_options") or {}),
        "profile_targets": [str(value) for value in list(bundle.get("profile_targets") or [])],
        "artifact_path": artifact_path,
        "generated_at": str(bundle.get("generated_at") or _utc_now()),
        "metadata": dict(bundle.get("metadata") or {}),
    }


def register_graph_package_bundle(
    *,
    bundle: dict[str, Any],
    registry_path: str | Path,
    artifact_path: str | None = None,
) -> dict[str, Any]:
    registry = load_graph_package_registry(registry_path)
    record = _registry_record(bundle=bundle, artifact_path=artifact_path)
    package_ref = str(record["package_ref"])
    existing_packages = [
        pkg for pkg in list(registry.get("packages") or [])
        if str(pkg.get("package_ref") or "") != package_ref
    ]
    existing_packages.append(record)
    existing_packages.sort(key=lambda pkg: (str(pkg.get("route_id") or ""), str(pkg.get("package_ref") or "")))
    route_index: dict[str, list[str]] = {}
    for pkg in existing_packages:
        route_id = str(pkg.get("route_id") or "")
        if route_id:
            route_index.setdefault(route_id, []).append(str(pkg.get("package_ref") or ""))
    registry["packages"] = existing_packages
    registry["route_index"] = route_index
    registry["generated_at"] = _utc_now()
    registry.setdefault("history", []).append(
        {
            "registered_at": _utc_now(),
            "package_ref": package_ref,
            "route_id": record["route_id"],
        }
    )
    save_graph_package_registry(registry, registry_path)
    return registry


def list_graph_packages(
    registry: dict[str, Any],
    *,
    route_id: str | None = None,
    profile_id: str | None = None,
) -> list[dict[str, Any]]:
    packages = [dict(pkg) for pkg in list(registry.get("packages") or [])]
    if route_id is not None:
        packages = [pkg for pkg in packages if str(pkg.get("route_id") or "") == str(route_id)]
    if profile_id is not None:
        packages = [
            pkg for pkg in packages
            if str(profile_id) in {str(value) for value in list(pkg.get("profile_targets") or [])}
        ]
    return packages


def _resolve_pointer_binding(
    *,
    pointer: dict[str, Any],
    route_id: str,
) -> dict[str, Any]:
    metadata = dict(pointer.get("metadata") or {})
    package_bindings = dict(metadata.get("package_bindings") or {})
    binding = dict(package_bindings.get(route_id) or {})
    if binding:
        return binding
    return {
        "graph_id": pointer.get("graph_id"),
        "package_revision": pointer.get("package_revision"),
        "package_id": metadata.get("package_id"),
        "route_id": route_id,
    }


def resolve_graph_package_from_pointer(
    *,
    registry: dict[str, Any],
    pointer: dict[str, Any],
    route_id: str,
    profile_id: str,
) -> Optional[dict[str, Any]]:
    if route_id not in {str(value) for value in list(pointer.get("route_ids") or [])}:
        return None
    binding = _resolve_pointer_binding(pointer=pointer, route_id=route_id)
    candidates = list_graph_packages(registry, route_id=route_id, profile_id=profile_id)
    package_id = str(binding.get("package_id") or "")
    package_revision = str(binding.get("package_revision") or "")
    graph_id = str(binding.get("graph_id") or "")
    for package in candidates:
        if package_id and str(package.get("package_id") or "") != package_id:
            continue
        if package_revision and str(package.get("package_revision") or "") != package_revision:
            continue
        if graph_id and str(package.get("graph_id") or "") != graph_id:
            continue
        return package
    return None


def resolve_selected_graph_package(
    *,
    registry: dict[str, Any],
    pointer_registry: dict[str, Any],
    route_id: str,
    profile_id: str,
    mode: str = "shadow",
) -> dict[str, Any]:
    pointer_order = {
        "shadow": ["shadow_pointer"],
        "candidate_primary": ["candidate_primary_pointer", "shadow_pointer"],
        "primary": ["primary_pointer", "candidate_primary_pointer", "shadow_pointer"],
    }.get(str(mode), ["shadow_pointer"])

    evaluated: list[dict[str, Any]] = []
    for pointer_key in pointer_order:
        pointer = pointer_registry.get(pointer_key)
        if not isinstance(pointer, dict):
            continue
        package = resolve_graph_package_from_pointer(
            registry=registry,
            pointer=pointer,
            route_id=route_id,
            profile_id=profile_id,
        )
        evaluated.append(
            {
                "pointer_slot": pointer_key,
                "pointer_id": pointer.get("pointer_id"),
                "matched": package is not None,
                "route_id": route_id,
                "profile_id": profile_id,
            }
        )
        if package is not None:
            return {
                "schema_version": "canon_selected_graph_package_v1",
                "resolved": True,
                "mode": str(mode),
                "route_id": route_id,
                "profile_id": profile_id,
                "pointer_slot": pointer_key,
                "pointer": dict(pointer),
                "package": package,
                "evaluated_pointers": evaluated,
            }

    return {
        "schema_version": "canon_selected_graph_package_v1",
        "resolved": False,
        "mode": str(mode),
        "route_id": route_id,
        "profile_id": profile_id,
        "pointer_slot": None,
        "pointer": None,
        "package": None,
        "evaluated_pointers": evaluated,
    }


def register_graph_package_bundles(
    *,
    bundles: Iterable[dict[str, Any]],
    registry_path: str | Path,
    artifact_paths: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    registry = load_graph_package_registry(registry_path)
    for bundle in bundles:
        artifact_path = None
        if artifact_paths is not None:
            artifact_path = artifact_paths.get(str(bundle.get("package_id") or ""))
        registry = register_graph_package_bundle(
            bundle=bundle,
            registry_path=registry_path,
            artifact_path=artifact_path,
        )
    return registry

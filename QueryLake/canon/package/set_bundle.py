from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Optional

from QueryLake.canon.package.bundle import build_route_graph_package_bundle, persist_graph_package_bundle
from QueryLake.canon.package.registry import load_graph_package_registry, register_graph_package_bundle


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def build_phase1a_package_set_bundle(
    *,
    routes: Iterable[str],
    package_revision: str,
    output_dir: str | Path,
    registry_path: str | Path,
    profile_targets: Optional[Iterable[str]] = None,
    route_options: Optional[dict[str, dict[str, Any]]] = None,
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    route_rows: list[dict[str, Any]] = []
    for route in [str(value) for value in routes]:
        bundle = build_route_graph_package_bundle(
            route=route,
            package_revision=package_revision,
            profile_targets=profile_targets,
            options=dict((route_options or {}).get(route) or {}),
        )
        persisted = persist_graph_package_bundle(bundle=bundle, output_dir=output_path)
        register_graph_package_bundle(
            bundle=bundle,
            registry_path=registry_path,
            artifact_path=persisted["path"],
        )
        route_rows.append(
            {
                "route_id": route,
                "package_id": bundle["package_id"],
                "package_revision": bundle["package_revision"],
                "graph_id": bundle["graph"]["graph_id"],
                "artifact_path": persisted["path"],
                "profile_targets": list(bundle.get("profile_targets") or []),
                "compile_options": dict(bundle.get("pipeline", {}).get("compile_options") or {}),
            }
        )

    registry = load_graph_package_registry(registry_path)
    return {
        "schema_version": "canon_phase1a_package_set_bundle_v1",
        "generated_at": _utc_now(),
        "package_revision": package_revision,
        "routes": [row["route_id"] for row in route_rows],
        "route_rows": route_rows,
        "registry_path": str(registry_path),
        "registry_summary": {
            "package_count": len(list(registry.get("packages") or [])),
            "route_count": len(dict(registry.get("route_index") or {})),
        },
    }

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from .authority_control_registry import apply_authority_control_bootstrap
from .route_serving_registry import (
    record_route_activation,
    record_route_apply_state,
    record_route_package_certification,
)
from QueryLake.runtime.db_compat import get_deployment_profile
from QueryLake.runtime.retrieval_route_executors import resolve_search_bm25_route_executor


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


def _route_binding(pointer: dict[str, Any], route_id: str) -> dict[str, Any]:
    metadata = dict(pointer.get("metadata") or {})
    package_bindings = dict(metadata.get("package_bindings") or {})
    binding = dict(package_bindings.get(route_id) or {})
    if binding:
        return binding
    return {
        "package_id": str(pointer.get("graph_id") or ""),
        "package_revision": str(pointer.get("package_revision") or ""),
        "graph_id": str(pointer.get("graph_id") or ""),
    }


def _projection_descriptors_for_route(*, route_id: str) -> list[str]:
    if str(route_id) == "search_bm25.document_chunk":
        source_profile = get_deployment_profile("aws_aurora_pg_opensearch_v1")
        resolution = resolve_search_bm25_route_executor(table="document_chunk", profile=source_profile)
        return [str(value) for value in list(resolution.to_payload().get("projection_descriptors") or []) if str(value or "")]
    return []


def _record_tranche2a_route_serving_state(
    *,
    target: dict[str, Any],
    route_serving_registry_path: str | Path,
    mode: str,
) -> None:
    if str(target.get("profile_id") or "") != "planetscale_opensearch_v1":
        return
    route_ids = [str(route_id) for route_id in list(target.get("route_ids") or []) if str(route_id or "")]
    if route_ids != ["search_bm25.document_chunk"]:
        return

    route_id = route_ids[0]
    binding = _route_binding(target, route_id)
    package_ref = {
        "package_id": str(binding.get("package_id") or ""),
        "package_revision": str(binding.get("package_revision") or ""),
        "graph_id": str(binding.get("graph_id") or ""),
    }
    if not all(package_ref.values()):
        raise ValueError("Route-scoped serving state requires complete package binding metadata for the Tranche 2A route.")

    metadata = dict(target.get("metadata") or {})
    route_metadata = dict(dict(metadata.get("route_metadata") or {}).get(route_id) or {})
    projection_descriptors = [
        str(value)
        for value in list(route_metadata.get("projection_descriptors") or _projection_descriptors_for_route(route_id=route_id))
        if str(value or "")
    ]
    if len(projection_descriptors) == 0:
        raise ValueError("Route-scoped serving state requires projection descriptors for the Tranche 2A route.")

    certification_state = "candidate_eligible" if str(mode) == "candidate_primary" else "primary_eligible"
    record_route_package_certification(
        registry_path=route_serving_registry_path,
        profile_id=str(target.get("profile_id") or ""),
        route_id=route_id,
        package_id=package_ref["package_id"],
        package_revision=package_ref["package_revision"],
        graph_id=package_ref["graph_id"],
        certification_state=certification_state,
        evidence_ref=f"publish-plan:{target.get('pointer_id')}",
        target_executor_id="opensearch.search_bm25.document_chunk.v1",
        compile_options=route_metadata.get("compile_options"),
        source_shadow_baseline_ref=f"shadow:{route_id}",
    )
    apply_entry = record_route_apply_state(
        registry_path=route_serving_registry_path,
        profile_id=str(target.get("profile_id") or ""),
        route_id=route_id,
        package_id=package_ref["package_id"],
        package_revision=package_ref["package_revision"],
        graph_id=package_ref["graph_id"],
        projection_descriptors=projection_descriptors,
        config_payload=route_metadata.get("config_payload"),
        dependency_payload=route_metadata.get("dependency_payload"),
        healthy=True,
    )
    record_route_activation(
        registry_path=route_serving_registry_path,
        profile_id=str(target.get("profile_id") or ""),
        route_id=route_id,
        mode=str(mode),
        pointer_id=str(target.get("pointer_id") or ""),
        package_id=package_ref["package_id"],
        package_revision=package_ref["package_revision"],
        apply_state_ref=str(apply_entry.get("apply_state_ref") or ""),
        approval_ref=f"publish-plan:{target.get('pointer_id')}",
        predecessor_pointer_id=None,
        rollback_target_pointer_id=None,
        candidate_scope={"route_ids": route_ids},
    )


def apply_publish_plan(
    *,
    plan: dict[str, Any],
    registry_path: str | Path,
    authority_control_registry_path: str | Path | None = None,
    route_serving_registry_path: str | Path | None = None,
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
        elif step_id == "apply_route_serving_state":
            if route_serving_registry_path is None:
                raise ValueError("Route serving registry path is required to apply route-scoped serving state.")
            _record_tranche2a_route_serving_state(
                target=target,
                route_serving_registry_path=route_serving_registry_path,
                mode=str(dict(step.get("metadata") or {}).get("mode") or target.get("mode") or ""),
            )

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

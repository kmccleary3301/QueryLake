from __future__ import annotations

from typing import Any, Dict, List, Optional

from QueryLake.runtime.db_compat import DeploymentProfile, build_profile_diagnostics_payload, get_deployment_profile
from QueryLake.runtime.local_profile_v2 import (
    build_local_profile_bringup_payload,
    is_local_profile_v2,
)
from QueryLake.runtime.projection_refresh import build_projection_diagnostics_payload
from QueryLake.runtime.route_planning_v2 import instantiate_route_planning_v2


def _backend_target_summary(plane: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    target = {
        "plane": str(plane),
        "backend": str(payload.get("backend") or ""),
        "status": str(payload.get("status") or ""),
        "checked": bool(payload.get("checked")),
        "checked_at": payload.get("checked_at"),
        "required": plane in {"authority", "projection"},
    }
    for key in ("database_url_env", "env_var", "endpoint", "status_code", "detail"):
        if payload.get(key) is not None:
            target[key] = payload.get(key)
    return target


def _projection_bootstrap_command(profile_id: str, metadata_store_path: Optional[str]) -> str:
    command_parts = [
        "python scripts/db_compat_profile_bootstrap.py",
        f"--profile {profile_id}",
    ]
    if metadata_store_path:
        command_parts.append(f"--projection-metadata-path {metadata_store_path}")
    return " ".join(command_parts)


def _build_next_actions(
    *,
    profile_id: str,
    startup_validation: Dict[str, Any],
    backend_connectivity: Dict[str, Any],
    projection_ids_needing_build: List[str],
    bootstrapable_required_projection_ids: List[str],
    nonbootstrapable_required_projection_ids: List[str],
    recommended_projection_ids_needing_build: List[str],
    bootstrapable_recommended_projection_ids: List[str],
    nonbootstrapable_recommended_projection_ids: List[str],
    metadata_store_path: Optional[str],
    route_payloads: List[Dict[str, Any]],
    lexical_gold_recommended_route_ids: List[str],
    lexical_degraded_route_ids: List[str],
) -> List[Dict[str, Any]]:
    next_actions: List[Dict[str, Any]] = []
    route_projection_ids_by_kind: Dict[str, set[str]] = {
        "projection_not_ready": set(),
        "projection_building": set(),
        "projection_failed": set(),
        "projection_stale": set(),
    }

    if not bool(startup_validation.get("configuration_ready")):
        next_actions.append(
            {
                "kind": "fix_configuration",
                "priority": "high",
                "summary": "Complete the required profile configuration before attempting split-stack bring-up.",
                "details": str(startup_validation.get("validation_error") or ""),
                "docs_ref": "docs/database/FIRST_SPLIT_STACK_DEPLOYMENT.md#configuration-checklist",
            }
        )

    for plane, payload in backend_connectivity.items():
        if not isinstance(payload, dict):
            continue
        status = str(payload.get("status") or "")
        if status in {"configuration_incomplete", "unreachable", "backend_unreachable", "connection_failed"}:
            next_actions.append(
                {
                    "kind": "fix_backend_connectivity",
                    "priority": "high",
                    "plane": str(plane),
                    "summary": f"Restore {plane} backend readiness for the active profile.",
                    "details": str(payload.get("detail") or ""),
                    "backend": str(payload.get("backend") or ""),
                    "docs_ref": "docs/database/PROFILE_DIAGNOSTICS.md#what-diagnostics-contain",
                }
            )

    if bootstrapable_required_projection_ids:
        next_actions.append(
            {
                "kind": "bootstrap_projections",
                "priority": "high",
                "summary": "Build the required external projections before treating the split-stack profile as runtime-ready.",
                "projection_ids": list(bootstrapable_required_projection_ids),
                "command": _projection_bootstrap_command(profile_id, metadata_store_path),
                "docs_ref": "docs/database/FIRST_SPLIT_STACK_DEPLOYMENT.md#what-good-diagnostics-look-like",
            }
        )
    if nonbootstrapable_required_projection_ids:
        next_actions.append(
            {
                "kind": "investigate_nonbootstrapable_required_projections",
                "priority": "high",
                "summary": "Some required projections are not buildable on the active profile and will keep routes runtime-blocked until support or configuration changes.",
                "projection_ids": list(nonbootstrapable_required_projection_ids),
                "docs_ref": "docs/database/FIRST_SPLIT_STACK_DEPLOYMENT.md#current-intentional-limitations",
            }
        )
    if bootstrapable_recommended_projection_ids:
        next_actions.append(
            {
                "kind": "bootstrap_recommended_projections",
                "priority": "low",
                "summary": "Bootstrap recommended canonical projections after the required split-stack route surface is runtime-ready.",
                "projection_ids": list(bootstrapable_recommended_projection_ids),
                "command": (
                    f"{_projection_bootstrap_command(profile_id, metadata_store_path)} --projection-id "
                    + " --projection-id ".join(bootstrapable_recommended_projection_ids)
                ),
                "docs_ref": "docs/database/AUTHORITY_PROJECTION_MODEL.md#canonical-projection-targets",
            }
        )
    if nonbootstrapable_recommended_projection_ids:
        next_actions.append(
            {
                "kind": "review_nonbootstrapable_recommended_projections",
                "priority": "low",
                "summary": "Some recommended projections are not buildable on the active profile; they remain optional until that support exists.",
                "projection_ids": list(nonbootstrapable_recommended_projection_ids),
                "docs_ref": "docs/database/AUTHORITY_PROJECTION_MODEL.md#canonical-projection-targets",
            }
        )

    for row in route_payloads:
        route_id = str(row.get("route_id") or "")
        if not route_id or bool(row.get("runtime_ready")):
            continue
        blocker_kinds = [
            str(entry.get("kind"))
            for entry in list(row.get("runtime_blockers") or [])
            if isinstance(entry, dict) and entry.get("kind") is not None
        ]
        if not blocker_kinds:
            continue
        for blocker in list(row.get("runtime_blockers") or []):
            if not isinstance(blocker, dict):
                continue
            kind = str(blocker.get("kind") or "")
            if kind not in route_projection_ids_by_kind:
                continue
            for projection_id in list(blocker.get("projection_ids") or []):
                projection_id = str(projection_id or "")
                if projection_id:
                    route_projection_ids_by_kind[kind].add(projection_id)
        next_actions.append(
            {
                "kind": "route_runtime_blocker",
                "priority": "medium",
                "route_id": route_id,
                "summary": f"Resolve runtime blockers for {route_id}.",
                "blocker_kinds": blocker_kinds,
                "projection_ids": list(row.get("projection_build_gap_descriptors") or []),
                "docs_ref": "docs/database/PROFILE_DIAGNOSTICS.md#route-runtime-readiness-vs-route-execution-readiness",
            }
        )
    blocker_action_specs = [
        (
            "projection_failed",
            "investigate_failed_projections",
            "high",
            "Investigate and repair failed projection builds before treating the split-stack profile as runtime-ready.",
        ),
        (
            "projection_stale",
            "rebuild_stale_projections",
            "high",
            "Rebuild stale projections so split-stack routes stop serving out-of-date data.",
        ),
        (
            "projection_building",
            "wait_for_projection_build",
            "medium",
            "Wait for in-flight projection builds to complete before declaring the profile runtime-ready.",
        ),
    ]
    for blocker_kind, action_kind, priority, summary in blocker_action_specs:
        projection_ids = sorted(route_projection_ids_by_kind.get(blocker_kind) or [])
        if not projection_ids:
            continue
        next_actions.append(
            {
                "kind": action_kind,
                "priority": priority,
                "summary": summary,
                "projection_ids": projection_ids,
                "docs_ref": "docs/database/PROFILE_DIAGNOSTICS.md#startup-validation-and-error-kinds",
            }
        )
    if lexical_gold_recommended_route_ids:
        next_actions.append(
            {
                "kind": "prefer_gold_profile_for_exact_lexical_constraints",
                "priority": "medium",
                "summary": (
                    "Use the gold ParadeDB profile when exact lexical constraints or full lexical operator "
                    "semantics are required."
                ),
                "details": (
                    "The active profile is runtime-ready for its declared slice, but some lexical route surfaces "
                    "still degrade phrase/proximity behavior or reject hard lexical constraints."
                ),
                "docs_ref": "docs/database/PROFILE_DIAGNOSTICS.md#route-level-lexical-semantics",
                "route_ids": list(lexical_gold_recommended_route_ids),
                "capability_ids": [
                    "retrieval.lexical.advanced_operators",
                    "retrieval.lexical.phrase_boost",
                    "retrieval.lexical.proximity",
                    "retrieval.lexical.hard_constraints",
                ],
            }
        )
    elif lexical_degraded_route_ids:
        next_actions.append(
            {
                "kind": "review_degraded_lexical_semantics",
                "priority": "low",
                "summary": "Review degraded lexical semantics before treating this profile as equivalent to the gold stack.",
                "docs_ref": "docs/database/PROFILE_DIAGNOSTICS.md#route-level-lexical-semantics",
                "route_ids": list(lexical_degraded_route_ids),
                "capability_ids": [
                    "retrieval.lexical.advanced_operators",
                    "retrieval.lexical.phrase_boost",
                    "retrieval.lexical.proximity",
                ],
            }
        )
    return next_actions


def _build_route_recovery_payloads(
    *,
    profile_id: str,
    metadata_store_path: Optional[str],
    route_payloads: List[Dict[str, Any]],
    route_support_v2: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    route_support_map: Dict[str, Dict[str, Any]] = {}
    for row in route_support_v2:
        if not isinstance(row, dict):
            continue
        route_id = str(row.get("route_id") or "")
        if route_id:
            route_support_map[route_id] = row
    payloads: List[Dict[str, Any]] = []
    for row in route_payloads:
        if not isinstance(row, dict):
            continue
        route_id = str(row.get("route_id") or "")
        if not route_id:
            continue
        support_row = route_support_map.get(route_id) or {}
        planning_v2 = instantiate_route_planning_v2(dict(row))
        query_ir_v2 = dict(planning_v2.get("query_ir_v2_template") or {})
        projection_ir_v2 = dict(planning_v2.get("projection_ir_v2") or {})
        bootstrapable_projection_ids: List[str] = []
        nonbootstrapable_projection_ids: List[str] = []
        for blocker in list(row.get("runtime_blockers") or []):
            if not isinstance(blocker, dict):
                continue
            kind = str(blocker.get("kind") or "")
            projection_ids = [
                str(projection_id or "")
                for projection_id in list(blocker.get("projection_ids") or [])
                if str(projection_id or "")
            ]
            if kind in {"projection_not_ready", "projection_building", "projection_failed", "projection_stale"}:
                bootstrapable_projection_ids.extend(projection_ids)
            elif kind == "projection_writer_unavailable":
                nonbootstrapable_projection_ids.extend(projection_ids)
        bootstrapable_projection_ids = sorted(set(bootstrapable_projection_ids))
        nonbootstrapable_projection_ids = sorted(set(nonbootstrapable_projection_ids))
        lexical_semantics = dict(row.get("lexical_semantics") or {})
        lexical_support_class = str(lexical_semantics.get("support_class") or "")
        gold_recommended_for_exact_constraints = bool(
            lexical_semantics.get("gold_recommended_for_exact_constraints")
        )
        payloads.append(
            {
                "route_id": route_id,
                "executor_id": row.get("executor_id"),
                "implemented": bool(row.get("implemented")),
                "support_state": str(row.get("support_state") or ""),
                "planning_v2": planning_v2,
                "query_ir_v2": query_ir_v2,
                "projection_ir_v2": projection_ir_v2,
                "representation_scope_id": (
                    row.get("representation_scope_id")
                    if row.get("representation_scope_id") is not None
                    else support_row.get("representation_scope_id")
                ),
                "representation_scope": dict(
                    row.get("representation_scope")
                    or support_row.get("representation_scope")
                    or {}
                ),
                "capability_dependencies": list(
                    row.get("capability_dependencies")
                    or support_row.get("capability_dependencies")
                    or []
                ),
                "runtime_ready": bool(row.get("runtime_ready")),
                "projection_ready": bool(row.get("projection_ready", True)),
                "blocker_kinds": [
                    str(entry.get("kind"))
                    for entry in list(row.get("runtime_blockers") or [])
                    if isinstance(entry, dict) and entry.get("kind")
                ],
                "bootstrapable_blocking_projection_ids": bootstrapable_projection_ids,
                "nonbootstrapable_blocking_projection_ids": nonbootstrapable_projection_ids,
                "bootstrap_command": (
                    f"{_projection_bootstrap_command(profile_id, metadata_store_path)} --projection-id "
                    + " --projection-id ".join(bootstrapable_projection_ids)
                ) if bootstrapable_projection_ids else None,
                "lexical_support_class": lexical_support_class,
                "gold_recommended_for_exact_constraints": gold_recommended_for_exact_constraints,
                "exact_constraint_degraded_capabilities": list(
                    lexical_semantics.get("exact_constraint_degraded_capabilities") or []
                ),
                "exact_constraint_unsupported_capabilities": list(
                    lexical_semantics.get("exact_constraint_unsupported_capabilities") or []
                ),
            }
        )
    return payloads


def build_profile_bringup_payload(
    *,
    profile: Optional[DeploymentProfile] = None,
    metadata_store_path: Optional[str] = None,
) -> Dict[str, Any]:
    effective_profile = profile or get_deployment_profile()
    profile_diagnostics = build_profile_diagnostics_payload(
        effective_profile,
        metadata_store_path=metadata_store_path,
    )
    projection_diagnostics = build_projection_diagnostics_payload(
        profile=effective_profile,
        metadata_store_path=metadata_store_path,
    )

    startup_validation = dict(profile_diagnostics.get("startup_validation") or {})
    route_summary = dict(profile_diagnostics.get("route_summary") or {})
    backend_connectivity = dict(profile_diagnostics.get("backend_connectivity") or {})
    projection_metadata = dict(projection_diagnostics.get("metadata") or {})

    route_runtime_ready_ids = list(route_summary.get("runtime_ready_route_ids") or [])
    route_runtime_blocked_ids = list(route_summary.get("runtime_blocked_route_ids") or [])
    route_payloads = [
        dict(row)
        for row in list(profile_diagnostics.get("route_executors") or [])
        if isinstance(row, dict)
    ]
    lexical_degraded_route_ids: List[str] = []
    lexical_gold_recommended_route_ids: List[str] = []
    compatibility_projection_route_ids: List[str] = []
    canonical_projection_route_ids: List[str] = []
    compatibility_projection_target_ids: List[str] = []
    canonical_projection_target_ids: List[str] = []
    route_lexical_support_class_counts: Dict[str, int] = {}
    lexical_capability_blocker_counts: Dict[str, int] = {}
    for row in route_payloads:
        route_id = str(row.get("route_id") or "")
        compatibility_target_ids = [
            str(projection_id or "")
            for projection_id in list(row.get("compatibility_projection_target_ids") or [])
            if str(projection_id or "")
        ]
        canonical_target_ids = [
            str(projection_id or "")
            for projection_id in list(row.get("canonical_projection_target_ids") or [])
            if str(projection_id or "")
        ]
        if route_id and compatibility_target_ids:
            compatibility_projection_route_ids.append(route_id)
            compatibility_projection_target_ids.extend(compatibility_target_ids)
        if route_id and canonical_target_ids:
            canonical_projection_route_ids.append(route_id)
            canonical_projection_target_ids.extend(canonical_target_ids)
        lexical_semantics = dict(row.get("lexical_semantics") or {})
        if not route_id or not lexical_semantics:
            continue
        support_class = str(lexical_semantics.get("support_class") or "")
        if support_class:
            route_lexical_support_class_counts[support_class] = (
                route_lexical_support_class_counts.get(support_class, 0) + 1
            )
        degraded_capabilities = [
            str(capability_id or "")
            for capability_id in list(lexical_semantics.get("degraded_capabilities") or [])
            if str(capability_id or "")
        ]
        unsupported_capabilities = [
            str(capability_id or "")
            for capability_id in list(lexical_semantics.get("unsupported_capabilities") or [])
            if str(capability_id or "")
        ]
        if degraded_capabilities or unsupported_capabilities:
            lexical_degraded_route_ids.append(route_id)
        if (
            "retrieval.lexical.hard_constraints" in unsupported_capabilities
            or "retrieval.lexical.proximity" in degraded_capabilities
            or "retrieval.lexical.phrase_boost" in degraded_capabilities
        ):
            lexical_gold_recommended_route_ids.append(route_id)
        for capability_id in unsupported_capabilities + degraded_capabilities:
            lexical_capability_blocker_counts[capability_id] = (
                lexical_capability_blocker_counts.get(capability_id, 0) + 1
            )

    required_projection_ids: list[str] = []
    ready_projection_ids: list[str] = []
    projection_ids_needing_build: list[str] = []
    bootstrapable_required_projection_ids: list[str] = []
    nonbootstrapable_required_projection_ids: list[str] = []
    projection_building_ids: list[str] = []
    projection_failed_ids: list[str] = []
    projection_stale_ids: list[str] = []
    projection_absent_ids: list[str] = []
    recommended_projection_ids: list[str] = []
    recommended_ready_projection_ids: list[str] = []
    recommended_projection_ids_needing_build: list[str] = []
    bootstrapable_recommended_projection_ids: list[str] = []
    nonbootstrapable_recommended_projection_ids: list[str] = []
    required_projection_id_set: set[str] = set()
    for row in profile_diagnostics.get("route_executors") or []:
        if not isinstance(row, dict):
            continue
        if not bool(row.get("implemented")):
            continue
        if str(row.get("support_state") or "") not in {"supported", "degraded"}:
            continue
        if str(row.get("projection_dependency_mode") or "") != "required_external_projection":
            continue
        for projection_id in list(row.get("projection_descriptors") or []):
            projection_id = str(projection_id or "")
            if projection_id:
                required_projection_id_set.add(projection_id)

    for row in projection_diagnostics.get("projection_items") or []:
        if not isinstance(row, dict):
            continue
        projection_id = str(row.get("projection_id") or "")
        if not projection_id:
            continue
        materialization_target = dict(row.get("materialization_target") or {})
        authority_model = str(
            materialization_target.get("authority_model")
            or row.get("authority_model")
            or ""
        )
        if projection_id:
            if authority_model.endswith("_compatibility"):
                compatibility_projection_target_ids.append(projection_id)
            elif authority_model:
                canonical_projection_target_ids.append(projection_id)
        if projection_id not in required_projection_id_set:
            if bool(row.get("executable")):
                recommended_projection_ids.append(projection_id)
                build_status = str(row.get("build_status") or "")
                if build_status == "ready":
                    recommended_ready_projection_ids.append(projection_id)
                else:
                    recommended_projection_ids_needing_build.append(projection_id)
                    bootstrapable_recommended_projection_ids.append(projection_id)
            elif str(row.get("support_state") or "") in {"supported", "degraded"}:
                recommended_projection_ids_needing_build.append(projection_id)
                nonbootstrapable_recommended_projection_ids.append(projection_id)
            continue
        build_status = str(row.get("build_status") or "")
        required_projection_ids.append(projection_id)
        if build_status == "ready":
            ready_projection_ids.append(projection_id)
        else:
            projection_ids_needing_build.append(projection_id)
            if bool(row.get("executable")):
                bootstrapable_required_projection_ids.append(projection_id)
            else:
                nonbootstrapable_required_projection_ids.append(projection_id)
            if build_status == "building":
                projection_building_ids.append(projection_id)
            elif build_status == "failed":
                projection_failed_ids.append(projection_id)
            elif build_status == "stale":
                projection_stale_ids.append(projection_id)
            else:
                projection_absent_ids.append(projection_id)

    backend_unreachable_planes: list[str] = []
    for plane, payload in backend_connectivity.items():
        if not isinstance(payload, dict):
            continue
        if str(payload.get("status") or "") in {"unreachable", "backend_unreachable", "connection_failed"}:
            backend_unreachable_planes.append(str(plane))

    backend_targets = [
        _backend_target_summary(plane, payload)
        for plane, payload in backend_connectivity.items()
        if isinstance(payload, dict)
    ]
    route_runtime_blocker_kind_counts: Dict[str, int] = {}
    route_blocked_projection_ids: List[str] = []
    for row in route_payloads:
        if not isinstance(row, dict):
            continue
        for blocker in list(row.get("runtime_blockers") or []):
            if not isinstance(blocker, dict):
                continue
            kind = str(blocker.get("kind") or "")
            if kind:
                route_runtime_blocker_kind_counts[kind] = route_runtime_blocker_kind_counts.get(kind, 0) + 1
            for projection_id in list(blocker.get("projection_ids") or []):
                projection_id = str(projection_id or "")
                if projection_id:
                    route_blocked_projection_ids.append(projection_id)

    projection_status_counts = dict(projection_metadata.get("build_status_counts") or {})
    route_recovery = _build_route_recovery_payloads(
        profile_id=effective_profile.id,
        metadata_store_path=metadata_store_path,
        route_payloads=route_payloads,
        route_support_v2=[
            dict(row)
            for row in list(profile_diagnostics.get("route_support_v2") or [])
            if isinstance(row, dict)
        ],
    )
    next_actions = _build_next_actions(
        profile_id=effective_profile.id,
        startup_validation=startup_validation,
        backend_connectivity=backend_connectivity,
        projection_ids_needing_build=projection_ids_needing_build,
        bootstrapable_required_projection_ids=bootstrapable_required_projection_ids,
        nonbootstrapable_required_projection_ids=nonbootstrapable_required_projection_ids,
        recommended_projection_ids_needing_build=recommended_projection_ids_needing_build,
        bootstrapable_recommended_projection_ids=bootstrapable_recommended_projection_ids,
        nonbootstrapable_recommended_projection_ids=nonbootstrapable_recommended_projection_ids,
        metadata_store_path=metadata_store_path,
        route_payloads=route_payloads,
        lexical_gold_recommended_route_ids=lexical_gold_recommended_route_ids,
        lexical_degraded_route_ids=lexical_degraded_route_ids,
    )

    payload = {
        "profile": dict(profile_diagnostics.get("profile") or {}),
        "representation_scopes": dict(profile_diagnostics.get("representation_scopes") or {}),
        "route_support_v2": list(profile_diagnostics.get("route_support_v2") or []),
        "summary": {
            "boot_ready": bool(startup_validation.get("boot_ready")),
            "configuration_ready": bool(startup_validation.get("configuration_ready")),
            "route_execution_ready": bool(startup_validation.get("route_execution_ready")),
            "route_runtime_ready": bool(startup_validation.get("route_runtime_ready")),
            "declared_executable_routes_runtime_ready": bool(
                startup_validation.get("declared_executable_routes_runtime_ready")
            ),
            "backend_connectivity_ready": bool(startup_validation.get("backend_connectivity_ready")),
            "required_projection_count": len(required_projection_ids),
            "ready_projection_count": len(ready_projection_ids),
            "projection_ids_needing_build_count": len(projection_ids_needing_build),
            "bootstrapable_required_projection_count": len(bootstrapable_required_projection_ids),
            "nonbootstrapable_required_projection_count": len(nonbootstrapable_required_projection_ids),
            "recommended_projection_count": len(recommended_projection_ids),
            "recommended_ready_projection_count": len(recommended_ready_projection_ids),
            "recommended_projection_ids_needing_build_count": len(recommended_projection_ids_needing_build),
            "bootstrapable_recommended_projection_count": len(bootstrapable_recommended_projection_ids),
            "nonbootstrapable_recommended_projection_count": len(nonbootstrapable_recommended_projection_ids),
            "projection_building_count": len(projection_building_ids),
            "projection_failed_count": len(projection_failed_ids),
            "projection_stale_count": len(projection_stale_ids),
            "projection_absent_count": len(projection_absent_ids),
            "compatibility_projection_route_count": len(sorted(set(compatibility_projection_route_ids))),
            "canonical_projection_route_count": len(sorted(set(canonical_projection_route_ids))),
            "compatibility_projection_target_count": len(sorted(set(compatibility_projection_target_ids))),
            "canonical_projection_target_count": len(sorted(set(canonical_projection_target_ids))),
            "required_projection_status_counts": {
                "ready": len(ready_projection_ids),
                "building": len(projection_building_ids),
                "failed": len(projection_failed_ids),
                "stale": len(projection_stale_ids),
                "absent": len(projection_absent_ids),
            },
            "runtime_ready_route_count": len(route_runtime_ready_ids),
            "runtime_blocked_route_count": len(route_runtime_blocked_ids),
            "declared_route_count": int(route_summary.get("declared_route_count") or 0),
            "declared_executable_route_count": int(route_summary.get("declared_executable_route_count") or 0),
            "declared_optional_route_count": int(route_summary.get("declared_optional_route_count") or 0),
            "declared_executable_runtime_ready_count": int(
                route_summary.get("declared_executable_runtime_ready_count") or 0
            ),
            "declared_executable_runtime_blocked_count": int(
                route_summary.get("declared_executable_runtime_blocked_count") or 0
            ),
            "backend_unreachable_plane_count": len(backend_unreachable_planes),
            "route_runtime_blocker_kind_counts": route_runtime_blocker_kind_counts,
            "projection_status_counts": projection_status_counts,
            "lexical_degraded_route_count": len(lexical_degraded_route_ids),
            "lexical_gold_recommended_route_count": len(lexical_gold_recommended_route_ids),
            "route_lexical_support_class_counts": route_lexical_support_class_counts,
            "lexical_capability_blocker_counts": lexical_capability_blocker_counts,
            "next_action_count": len(next_actions),
            "route_recovery_count": len(route_recovery),
        },
        "required_projection_ids": required_projection_ids,
        "ready_projection_ids": ready_projection_ids,
        "projection_ids_needing_build": projection_ids_needing_build,
        "bootstrapable_required_projection_ids": bootstrapable_required_projection_ids,
        "nonbootstrapable_required_projection_ids": nonbootstrapable_required_projection_ids,
        "recommended_projection_ids": recommended_projection_ids,
        "recommended_ready_projection_ids": recommended_ready_projection_ids,
        "recommended_projection_ids_needing_build": recommended_projection_ids_needing_build,
        "bootstrapable_recommended_projection_ids": bootstrapable_recommended_projection_ids,
        "nonbootstrapable_recommended_projection_ids": nonbootstrapable_recommended_projection_ids,
        "projection_building_ids": projection_building_ids,
        "projection_failed_ids": projection_failed_ids,
        "projection_stale_ids": projection_stale_ids,
        "projection_absent_ids": projection_absent_ids,
        "compatibility_projection_route_ids": sorted(set(compatibility_projection_route_ids)),
        "canonical_projection_route_ids": sorted(set(canonical_projection_route_ids)),
        "compatibility_projection_target_ids": sorted(set(compatibility_projection_target_ids)),
        "canonical_projection_target_ids": sorted(set(canonical_projection_target_ids)),
        "route_runtime_ready_ids": route_runtime_ready_ids,
        "route_runtime_blocked_ids": route_runtime_blocked_ids,
        "declared_route_support": dict(route_summary.get("declared_route_support") or {}),
        "declared_executable_route_ids": list(route_summary.get("declared_executable_route_ids") or []),
        "declared_optional_route_ids": list(route_summary.get("declared_optional_route_ids") or []),
        "declared_executable_runtime_ready_ids": list(
            route_summary.get("declared_executable_runtime_ready_ids") or []
        ),
        "declared_executable_runtime_blocked_ids": list(
            route_summary.get("declared_executable_runtime_blocked_ids") or []
        ),
        "lexical_degraded_route_ids": sorted(set(lexical_degraded_route_ids)),
        "lexical_gold_recommended_route_ids": sorted(set(lexical_gold_recommended_route_ids)),
        "route_blocked_projection_ids": sorted(set(route_blocked_projection_ids)),
        "backend_unreachable_planes": backend_unreachable_planes,
        "backend_targets": backend_targets,
        "route_recovery": route_recovery,
        "next_actions": next_actions,
        "profile_diagnostics": profile_diagnostics,
        "projection_diagnostics": projection_diagnostics,
        "metadata": {
            "projection_count": int(projection_metadata.get("projection_count") or 0),
            "executable_projection_count": int(projection_metadata.get("executable_count") or 0),
            "planned_or_unavailable_projection_count": int(projection_metadata.get("planned_or_unavailable_count") or 0),
            "projection_status_counts": projection_status_counts,
            "route_runtime_blocker_kind_counts": route_runtime_blocker_kind_counts,
            "route_lexical_support_class_counts": route_lexical_support_class_counts,
            "lexical_capability_blocker_counts": lexical_capability_blocker_counts,
            "bootstrapable_required_projection_count": len(bootstrapable_required_projection_ids),
            "nonbootstrapable_required_projection_count": len(nonbootstrapable_required_projection_ids),
            "bootstrapable_recommended_projection_count": len(bootstrapable_recommended_projection_ids),
            "nonbootstrapable_recommended_projection_count": len(nonbootstrapable_recommended_projection_ids),
            "compatibility_projection_route_count": len(sorted(set(compatibility_projection_route_ids))),
            "canonical_projection_route_count": len(sorted(set(canonical_projection_route_ids))),
            "compatibility_projection_target_count": len(sorted(set(compatibility_projection_target_ids))),
            "canonical_projection_target_count": len(sorted(set(canonical_projection_target_ids))),
        },
    }
    if is_local_profile_v2(effective_profile):
        payload["local_profile"] = build_local_profile_bringup_payload(
            profile=effective_profile,
            bringup_payload=payload,
            diagnostics_payload=profile_diagnostics,
            projection_diagnostics=projection_diagnostics,
        )
    return payload

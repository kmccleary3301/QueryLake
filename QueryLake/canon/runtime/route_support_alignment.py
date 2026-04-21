from __future__ import annotations

from typing import Any

from QueryLake.canon.control.route_serving_registry import (
    build_route_slice_state,
    load_route_serving_registry,
)
from QueryLake.canon.runtime.search_plane_a_execution import build_search_plane_a_execution_contract
from QueryLake.runtime.db_compat import get_deployment_profile


_SUPPORTED_V5_ROUTE_VARIANTS = (
    {
        "route_id": "search_bm25.document_chunk",
        "variant_label": "default",
        "expected_supported": True,
    },
    {
        "route_id": "search_file_chunks",
        "variant_label": "default",
        "expected_supported": True,
    },
    {
        "route_id": "search_hybrid.document_chunk",
        "variant_label": "hybrid_sparse_disabled",
        "expected_supported": True,
    },
    {
        "route_id": "search_hybrid.document_chunk",
        "variant_label": "hybrid_sparse_enabled",
        "expected_supported": False,
        "deferred_ref": "CANON_PP_EXTENSIONS_SEARCH_PLANE_A_VARIANTS_CHARTER.md",
    },
)


def _route_slice_support_state(*, route_state: str, authoritative: bool, primary_ready: bool) -> str:
    if route_state == "primary_active" and authoritative and primary_ready:
        return "route_slice_supported"
    if route_state == "candidate_primary_active" and authoritative:
        return "route_slice_candidate"
    if route_state == "primary_eligible":
        return "route_slice_primary_eligible"
    if route_state == "candidate_primary_eligible":
        return "route_slice_candidate_eligible"
    return "route_slice_shadow"


def _variant_label_for_alignment(route_id: str, execution_contract: dict[str, Any]) -> str:
    if str(route_id) != "search_hybrid.document_chunk":
        return "default"
    compile_options = dict(execution_contract.get("compile_options") or {})
    if bool(compile_options.get("disable_sparse")):
        return "hybrid_sparse_disabled"
    return "hybrid_sparse_enabled"


def build_route_slice_support_alignment(
    *,
    route_id: str,
    profile_id: str,
    package_registry_path: str,
    pointer_registry_path: str,
    route_serving_registry_path: str,
    mode: str = "primary",
) -> dict[str, Any]:
    profile = get_deployment_profile(profile_id)
    route_serving_registry = load_route_serving_registry(route_serving_registry_path)
    route_state = build_route_slice_state(
        registry=route_serving_registry,
        profile_id=profile.id,
        route_id=route_id,
    )
    execution_contract = build_search_plane_a_execution_contract(
        route_id=route_id,
        profile_id=profile.id,
        package_registry_path=package_registry_path,
        pointer_registry_path=pointer_registry_path,
        route_serving_registry_path=route_serving_registry_path,
        mode=mode,
    )
    runtime_support_state = _route_slice_support_state(
        route_state=str(route_state.get("state") or ""),
        authoritative=bool(execution_contract.get("authoritative")),
        primary_ready=bool(execution_contract.get("primary_ready")),
    )
    blockers: list[str] = []
    if runtime_support_state != "route_slice_supported":
        blockers.append("route_slice_not_primary_supported")
    if str(profile.maturity) == "planned":
        blockers.append("profile_global_support_state_remains_planned")
    return {
        "schema_version": "canon_route_slice_support_alignment_v1",
        "route_id": route_id,
        "variant_label": _variant_label_for_alignment(route_id, execution_contract),
        "profile_id": profile.id,
        "profile_global_maturity": profile.maturity,
        "route_state": route_state,
        "execution_contract": execution_contract,
        "runtime_support_state": runtime_support_state,
        "route_slice_supported": runtime_support_state == "route_slice_supported",
        "global_profile_supported": False,
        "support_claim_scope": "route_slice_only",
        "blockers": blockers,
        "notes": [
            "This payload aligns support wording to a single route slice or route variant.",
            "It must not be interpreted as full-profile support for planetscale_opensearch_v1.",
        ],
    }


def build_route_scoped_support_matrix(
    *,
    profile_id: str,
    package_registry_path: str,
    pointer_registry_path: str,
    route_serving_registry_path: str,
    mode: str = "primary",
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for variant in _SUPPORTED_V5_ROUTE_VARIANTS:
        route_id = str(variant["route_id"])
        variant_label = str(variant["variant_label"])
        if not bool(variant.get("expected_supported")):
            rows.append(
                {
                    "route_id": route_id,
                    "variant_label": variant_label,
                    "profile_id": profile_id,
                    "runtime_support_state": "route_variant_deferred",
                    "route_slice_supported": False,
                    "global_profile_supported": False,
                    "support_claim_scope": "not_claimed",
                    "deferred": True,
                    "deferred_ref": str(variant.get("deferred_ref") or ""),
                    "blockers": ["route_variant_deferred_to_future_phase"],
                    "evidence": {},
                }
            )
            continue
        alignment = build_route_slice_support_alignment(
            route_id=route_id,
            profile_id=profile_id,
            package_registry_path=package_registry_path,
            pointer_registry_path=pointer_registry_path,
            route_serving_registry_path=route_serving_registry_path,
            mode=mode,
        )
        rows.append(
            {
                "route_id": route_id,
                "variant_label": variant_label,
                "profile_id": str(alignment.get("profile_id") or profile_id),
                "runtime_support_state": str(alignment.get("runtime_support_state") or ""),
                "route_slice_supported": bool(alignment.get("route_slice_supported")),
                "global_profile_supported": bool(alignment.get("global_profile_supported")),
                "support_claim_scope": str(alignment.get("support_claim_scope") or ""),
                "deferred": False,
                "deferred_ref": None,
                "blockers": list(alignment.get("blockers") or []),
                "evidence": {
                    "route_state": str(dict(alignment.get("route_state") or {}).get("state") or ""),
                    "executor_id": str(dict(alignment.get("execution_contract") or {}).get("executor_id") or ""),
                    "authoritative": bool(dict(alignment.get("execution_contract") or {}).get("authoritative")),
                    "primary_ready": bool(dict(alignment.get("execution_contract") or {}).get("primary_ready")),
                    "projection_descriptors": list(
                        dict(alignment.get("execution_contract") or {}).get("projection_descriptors") or []
                    ),
                    "compile_options": dict(dict(alignment.get("execution_contract") or {}).get("compile_options") or {}),
                },
            }
        )
    supported_rows = [row for row in rows if bool(row.get("route_slice_supported"))]
    deferred_rows = [row for row in rows if bool(row.get("deferred"))]
    return {
        "schema_version": "canon_route_scoped_support_matrix_v1",
        "profile_id": profile_id,
        "mode": mode,
        "global_profile_supported": False,
        "support_claim_scope": "route_slice_only",
        "supported_route_claim_count": len(supported_rows),
        "deferred_route_variant_count": len(deferred_rows),
        "rows": rows,
        "summary": {
            "supported_route_variants": [
                f"{row['route_id']}:{row['variant_label']}" for row in supported_rows
            ],
            "deferred_route_variants": [
                f"{row['route_id']}:{row['variant_label']}" for row in deferred_rows
            ],
            "closure_claim": (
                "Bounded route-scoped support for certified Search Plane A target-serving slices only; "
                "global profile support, sparse-enabled hybrid, Search Plane B, and offline runtime are not claimed."
            ),
        },
    }

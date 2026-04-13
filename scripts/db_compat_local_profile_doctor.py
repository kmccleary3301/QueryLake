#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.db_compat import DEPLOYMENT_PROFILES
from QueryLake.runtime.profile_bringup import build_profile_bringup_payload
from QueryLake.runtime.local_profile_v2 import build_local_profile_support_manifest_payload
from scripts.db_compat_profile_smoke import (
    _parse_env_pairs,
    _prepare_ready_profile_projection_metadata,
    temporary_env,
)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Human-readable doctor surface for the local embedded profile."
    )
    parser.add_argument("--profile", default="sqlite_fts5_dense_sidecar_local_v1")
    parser.add_argument("--env", action="append", default=[])
    parser.add_argument("--projection-metadata-path", default=None)
    parser.add_argument("--enable-ready-profile-projections", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.profile not in DEPLOYMENT_PROFILES:
        raise ValueError(f"Unknown profile id: {args.profile}")
    if args.enable_ready_profile_projections and args.projection_metadata_path:
        raise ValueError(
            "--enable-ready-profile-projections cannot be combined with --projection-metadata-path."
        )

    metadata_store_path = args.projection_metadata_path
    if args.enable_ready_profile_projections:
        metadata_store_path = _prepare_ready_profile_projection_metadata(args.profile)

    env_map = {"QUERYLAKE_DB_PROFILE": args.profile, **_parse_env_pairs(list(args.env or []))}
    with temporary_env(env_map):
        payload = build_profile_bringup_payload(
            profile=DEPLOYMENT_PROFILES[args.profile],
            metadata_store_path=metadata_store_path,
        )

    if args.json:
        print(json.dumps(payload, indent=2))
        return 0

    summary = dict(payload.get("summary") or {})
    local_profile = dict(payload.get("local_profile") or {})
    dense_sidecar = dict(local_profile.get("dense_sidecar") or {})
    promotion = dict(local_profile.get("promotion_status") or {})
    scope_expansion = dict(local_profile.get("scope_expansion_status") or {})
    scope_expansion_contract = dict(local_profile.get("scope_expansion_contract") or {})
    route_contracts = {
        str(entry.get("route_id") or ""): dict(entry)
        for entry in list(local_profile.get("route_runtime_contracts") or [])
        if isinstance(entry, dict) and entry.get("route_id") is not None
    }
    support_manifest = build_local_profile_support_manifest_payload(profile=DEPLOYMENT_PROFILES[args.profile])
    projection_registry = {
        str(entry.get("projection_id") or ""): dict(entry)
        for entry in list(local_profile.get("projection_plan_v2_registry") or [])
        if isinstance(entry, dict) and entry.get("projection_id") is not None
    }

    print(f"profile: {payload['profile']['id']}")
    print(f"maturity: {local_profile.get('maturity', 'unknown')}")
    print(f"configuration_ready: {bool(summary.get('configuration_ready'))}")
    print(f"declared_executable_routes_runtime_ready: {bool(summary.get('declared_executable_routes_runtime_ready'))}")
    print(f"dense_sidecar_ready: {bool(dense_sidecar.get('ready'))}")
    print(f"dense_sidecar_cache_warmed: {bool(dense_sidecar.get('cache_warmed'))}")
    print(f"dense_sidecar_record_count: {int(dense_sidecar.get('record_count') or 0)}")
    print(f"dense_sidecar_embedding_dimension: {int(dense_sidecar.get('embedding_dimension') or 0)}")
    print(f"dense_sidecar_ready_state_source: {str(dense_sidecar.get('ready_state_source') or '')}")
    print(f"dense_sidecar_lifecycle_state: {str(dense_sidecar.get('lifecycle_state') or '')}")
    print(f"dense_sidecar_cache_lifecycle_state: {str(dense_sidecar.get('cache_lifecycle_state') or '')}")
    print(f"dense_sidecar_stats_source: {str(dense_sidecar.get('stats_source') or '')}")
    print(
        "dense_sidecar_rebuildable_from_projection_records: "
        f"{bool(dense_sidecar.get('rebuildable_from_projection_records'))}"
    )
    print(
        "dense_sidecar_requires_process_warmup: "
        f"{bool(dense_sidecar.get('requires_process_warmup'))}"
    )
    print(
        "dense_sidecar_warmup_recommended: "
        f"{bool(dense_sidecar.get('warmup_recommended'))}"
    )
    print(
        "dense_sidecar_warmup_required_for_peak_performance: "
        f"{bool(dense_sidecar.get('warmup_required_for_peak_performance'))}"
    )
    print(
        "dense_sidecar_cold_start_recoverable: "
        f"{bool(dense_sidecar.get('cold_start_recoverable'))}"
    )
    print(
        "dense_sidecar_cache_persistence_mode: "
        f"{str(dense_sidecar.get('cache_persistence_mode') or '')}"
    )
    print(
        "dense_sidecar_lifecycle_recovery_mode: "
        f"{str(dense_sidecar.get('lifecycle_recovery_mode') or '')}"
    )
    print(
        "dense_sidecar_lifecycle_recovery_hints: "
        f"{','.join(list(dense_sidecar.get('lifecycle_recovery_hints') or []))}"
    )
    print(
        "dense_sidecar_warmup_target_route_ids: "
        f"{','.join(list(dense_sidecar.get('warmup_target_route_ids') or []))}"
    )
    print(
        "dense_sidecar_warmup_command_hint: "
        f"{str(dense_sidecar.get('warmup_command_hint') or '')}"
    )
    print(
        "dense_sidecar_persisted_projection_state_available: "
        f"{bool(dense_sidecar.get('persisted_projection_state_available'))}"
    )
    print(f"dense_sidecar_runtime_contract_ready: {bool(dense_sidecar.get('runtime_contract_ready'))}")
    print(f"dense_sidecar_promotion_contract_ready: {bool(dense_sidecar.get('promotion_contract_ready'))}")
    print(
        "dense_sidecar_runtime_blockers: "
        f"{','.join(list(dense_sidecar.get('runtime_blockers') or []))}"
    )
    print(
        "dense_sidecar_promotion_blockers: "
        f"{','.join(list(dense_sidecar.get('promotion_blockers') or []))}"
    )
    dense_contract = dict(dense_sidecar.get("contract") or {})
    if dense_contract:
        print("dense_sidecar_contract:")
        print(
            "  - "
            f"adapter_id={dense_contract.get('adapter_id', '')} "
            f"storage_contract_version={dense_contract.get('storage_contract_version', '')} "
            f"lifecycle_contract_version={dense_contract.get('lifecycle_contract_version', '')} "
            f"execution_mode={dense_contract.get('execution_mode', '')} "
            f"storage_mode={dense_contract.get('storage_mode', '')} "
            f"persistence_scope={dense_contract.get('persistence_scope', '')} "
            f"durability_level={dense_contract.get('durability_level', '')} "
            f"cache_scope={dense_contract.get('cache_scope', '')} "
            f"query_mode={dense_contract.get('query_mode', '')}"
        )
    print("support_matrix:")
    for row in list(support_manifest.get("routes") or []):
        projections = ",".join(list(row.get("required_projection_descriptors") or []))
        capabilities = ",".join(list(row.get("capability_dependencies") or []))
        print(
            "  - "
            f"{row.get('route_id')}: "
            f"support_state={row.get('support_state')} "
            f"declared_executable={bool(row.get('declared_executable'))} "
            f"scope={row.get('representation_scope_id')} "
            f"lexical_support_class={row.get('lexical_support_class')} "
            f"required_projections=[{projections}] "
            f"capabilities=[{capabilities}]"
        )
    print("declared_executable_route_ids:")
    for route_id in list(promotion.get("declared_executable_route_ids") or []):
        contract = route_contracts.get(str(route_id), {})
        print(
            "  - "
            f"{route_id}: runtime_ready={bool(contract.get('runtime_ready'))} "
            f"representation_scope={contract.get('representation_scope_id', '')} "
            f"dense_sidecar_required={bool(contract.get('dense_sidecar_required'))} "
            f"dense_sidecar_ready_source={contract.get('dense_sidecar_ready_state_source', '')} "
            f"dense_sidecar_cache_lifecycle_state={contract.get('dense_sidecar_cache_lifecycle_state', '')} "
            f"dense_sidecar_requires_process_warmup={bool(contract.get('dense_sidecar_requires_process_warmup'))} "
            f"dense_sidecar_warmup_recommended={bool(contract.get('dense_sidecar_warmup_recommended'))} "
            f"dense_sidecar_warmup_required_for_peak_performance={bool(contract.get('dense_sidecar_warmup_required_for_peak_performance'))} "
            f"dense_sidecar_lifecycle_recovery_mode={contract.get('dense_sidecar_lifecycle_recovery_mode', '')} "
            f"dense_sidecar_persisted_projection_state_available={bool(contract.get('dense_sidecar_persisted_projection_state_available'))}"
        )
    print("required_projection_ids:")
    for projection_id in list(promotion.get("required_projection_ids") or []):
        print(f"  - {projection_id}")
    print("projection_plan_v2_registry:")
    for projection_id in list(promotion.get("required_projection_ids") or []):
        item = projection_registry.get(str(projection_id), {})
        print(
            "  - "
            f"{projection_id}: backend={item.get('target_backend', '')} "
            f"buildability={item.get('buildability_class', '')} "
            f"scope={item.get('representation_scope_id', '')}"
        )
    print("lexical_degraded_route_ids:")
    for route_id in list(promotion.get("lexical_degraded_route_ids") or []):
        print(f"  - {route_id}")
    print("scope_expansion_status:")
    print(
        "  - "
        f"current_supported_slice_frozen={bool(scope_expansion.get('current_supported_slice_frozen'))} "
        f"dense_sidecar_contract_version={scope_expansion.get('dense_sidecar_contract_version', '')} "
        f"dense_sidecar_promotion_contract_ready={bool(scope_expansion.get('dense_sidecar_promotion_contract_ready'))} "
        f"dense_sidecar_lifecycle_state={scope_expansion.get('dense_sidecar_lifecycle_state', '')} "
        f"dense_sidecar_cache_lifecycle_state={scope_expansion.get('dense_sidecar_cache_lifecycle_state', '')} "
        f"dense_sidecar_rebuildable_from_projection_records={bool(scope_expansion.get('dense_sidecar_rebuildable_from_projection_records'))} "
        f"dense_sidecar_requires_process_warmup={bool(scope_expansion.get('dense_sidecar_requires_process_warmup'))} "
        f"dense_sidecar_warmup_recommended={bool(scope_expansion.get('dense_sidecar_warmup_recommended'))} "
        f"dense_sidecar_warmup_required_for_peak_performance={bool(scope_expansion.get('dense_sidecar_warmup_required_for_peak_performance'))} "
        f"dense_sidecar_lifecycle_recovery_mode={scope_expansion.get('dense_sidecar_lifecycle_recovery_mode', '')} "
        f"dense_sidecar_persisted_projection_state_available={bool(scope_expansion.get('dense_sidecar_persisted_projection_state_available'))}"
    )
    if scope_expansion_contract:
        print("scope_expansion_contract:")
        print(
            "  - "
            f"docs_ref={scope_expansion_contract.get('docs_ref', '')} "
            f"dense_sidecar_contract_version={scope_expansion_contract.get('dense_sidecar_contract_version', '')} "
            f"dense_sidecar_lifecycle_contract_version={scope_expansion_contract.get('dense_sidecar_lifecycle_contract_version', '')}"
        )
        for item in list(scope_expansion_contract.get("required_before_widening") or []):
            print(f"    required_before_widening: {item}")
    for item in list(scope_expansion.get("pending_for_wider_scope") or []):
        print(f"    pending: {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

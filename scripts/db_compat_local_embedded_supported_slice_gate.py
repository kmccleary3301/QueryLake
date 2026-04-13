#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.db_compat import DEPLOYMENT_PROFILES
from QueryLake.runtime.local_dense_sidecar import LOCAL_DENSE_SIDECAR_ADAPTER
from QueryLake.runtime.profile_bringup import build_profile_bringup_payload
from scripts.db_compat_local_query_smoke import build_local_query_smoke_payload
from scripts.db_compat_profile_smoke import (
    _parse_env_pairs,
    _prepare_ready_profile_projection_metadata,
    temporary_env,
)


def _sorted_strings(values: List[Any]) -> List[str]:
    return sorted(str(value) for value in values if str(value or ""))


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the frozen supported embedded/local profile slice."
    )
    parser.add_argument("--profile", default="sqlite_fts5_dense_sidecar_local_v1")
    parser.add_argument("--env", action="append", default=[])
    parser.add_argument("--projection-metadata-path", default=None)
    parser.add_argument("--enable-ready-profile-projections", action="store_true")
    parser.add_argument("--output", default=None)
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
        bringup = build_profile_bringup_payload(
            profile=DEPLOYMENT_PROFILES[args.profile],
            metadata_store_path=metadata_store_path,
        )
        query_smoke = build_local_query_smoke_payload(
            profile_id=args.profile,
            enable_ready_profile_projections=bool(args.enable_ready_profile_projections),
            metadata_store_path=metadata_store_path,
        )

    summary = dict(bringup.get("summary") or {})
    local_profile = dict(bringup.get("local_profile") or {})
    promotion_status = dict(local_profile.get("promotion_status") or {})
    scope_contract = dict(local_profile.get("scope_expansion_contract") or {})
    dense_sidecar = dict(local_profile.get("dense_sidecar") or {})
    support_matrix = list(local_profile.get("support_matrix") or [])

    declared_executable_route_ids = _sorted_strings(
        list(promotion_status.get("declared_executable_route_ids") or [])
    )
    required_projection_ids = _sorted_strings(
        list(promotion_status.get("required_projection_ids") or [])
    )
    representation_scope_ids = _sorted_strings(
        list(promotion_status.get("representation_scope_ids") or [])
    )

    gate_ok = True
    gate_ok = gate_ok and str(local_profile.get("maturity") or "") == "embedded_supported"
    gate_ok = gate_ok and bool(summary.get("declared_executable_routes_runtime_ready"))
    gate_ok = gate_ok and bool(scope_contract.get("current_supported_slice_frozen"))
    gate_ok = gate_ok and bool(dense_sidecar.get("runtime_contract_ready"))
    gate_ok = gate_ok and bool(dense_sidecar.get("promotion_contract_ready"))
    gate_ok = gate_ok and bool(dict(query_smoke.get("summary") or {}).get("all_passed"))
    gate_ok = gate_ok and declared_executable_route_ids == _sorted_strings(
        list(scope_contract.get("declared_executable_route_ids") or [])
    )
    gate_ok = gate_ok and str(dense_sidecar.get("contract", {}).get("storage_contract_version") or "") == str(
        LOCAL_DENSE_SIDECAR_ADAPTER.storage_contract_version
    )
    gate_ok = gate_ok and str(dense_sidecar.get("contract", {}).get("lifecycle_contract_version") or "") == str(
        LOCAL_DENSE_SIDECAR_ADAPTER.lifecycle_contract_version
    )
    gate_ok = gate_ok and str(scope_contract.get("dense_sidecar_contract_version") or "") == str(
        LOCAL_DENSE_SIDECAR_ADAPTER.storage_contract_version
    )
    gate_ok = gate_ok and str(scope_contract.get("dense_sidecar_lifecycle_contract_version") or "") == str(
        LOCAL_DENSE_SIDECAR_ADAPTER.lifecycle_contract_version
    )

    payload: Dict[str, Any] = {
        "profile_id": args.profile,
        "maturity": str(local_profile.get("maturity") or ""),
        "declared_executable_routes_runtime_ready": bool(
            summary.get("declared_executable_routes_runtime_ready")
        ),
        "declared_executable_route_ids": declared_executable_route_ids,
        "required_projection_ids": required_projection_ids,
        "representation_scope_ids": representation_scope_ids,
        "dense_sidecar_contract_version": str(
            dict(dense_sidecar.get("contract") or {}).get("storage_contract_version") or ""
        ),
        "dense_sidecar_lifecycle_contract_version": str(
            dict(dense_sidecar.get("contract") or {}).get("lifecycle_contract_version") or ""
        ),
        "dense_sidecar_lifecycle_state": str(dense_sidecar.get("lifecycle_state") or ""),
        "dense_sidecar_cache_lifecycle_state": str(
            dense_sidecar.get("cache_lifecycle_state") or ""
        ),
        "scope_expansion_required_before_widening": list(
            scope_contract.get("required_before_widening") or []
        ),
        "support_matrix_route_ids": _sorted_strings(
            [dict(entry).get("route_id") for entry in support_matrix if isinstance(entry, dict)]
        ),
        "query_smoke_passed": bool(dict(query_smoke.get("summary") or {}).get("all_passed")),
        "gate_ok": bool(gate_ok),
    }

    rendered = json.dumps(payload, indent=2)
    print(rendered)
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")

    return 0 if gate_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())

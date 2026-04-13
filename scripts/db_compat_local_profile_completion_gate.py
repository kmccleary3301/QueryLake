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
from QueryLake.runtime.profile_bringup import build_profile_bringup_payload
from scripts.db_compat_local_query_smoke import build_local_query_smoke_payload
from scripts.db_compat_profile_smoke import (
    _parse_env_pairs,
    _prepare_ready_profile_projection_metadata,
    temporary_env,
)


def _parse_csv(raw: str | None) -> List[str]:
    if raw is None or not raw.strip():
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


def _sorted_string_list(values: List[Any]) -> List[str]:
    return sorted(str(value) for value in values if str(value or ""))


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Completion gate for the narrow executable local profile slice."
    )
    parser.add_argument("--profile", required=True)
    parser.add_argument("--env", action="append", default=[])
    parser.add_argument("--projection-metadata-path", default=None)
    parser.add_argument("--enable-ready-profile-projections", action="store_true")
    parser.add_argument("--expect-profile-implemented", choices=["true", "false"], default=None)
    parser.add_argument("--expect-boot-ready", choices=["true", "false"], default=None)
    parser.add_argument("--expect-configuration-ready", choices=["true", "false"], default=None)
    parser.add_argument("--expect-route-runtime-ready", choices=["true", "false"], default=None)
    parser.add_argument(
        "--expect-declared-executable-routes-runtime-ready",
        choices=["true", "false"],
        default=None,
    )
    parser.add_argument("--expect-ready-projection-count", type=int, default=None)
    parser.add_argument("--expect-declared-executable-route-ids", default=None)
    parser.add_argument("--expect-lexical-degraded-route-ids", default=None)
    parser.add_argument("--expect-lexical-gold-recommended-route-ids", default=None)
    parser.add_argument("--expect-query-smoke-passed", choices=["true", "false"], default=None)
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
        payload = build_profile_bringup_payload(
            profile=DEPLOYMENT_PROFILES[args.profile],
            metadata_store_path=metadata_store_path,
        )
        payload["query_smoke"] = build_local_query_smoke_payload(
            profile_id=args.profile,
            enable_ready_profile_projections=bool(args.enable_ready_profile_projections),
            metadata_store_path=metadata_store_path,
        )

    rendered = json.dumps(payload, indent=2)
    print(rendered)
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")

    summary = dict(payload.get("summary") or {})
    local_profile = dict(payload.get("local_profile") or {})
    promotion_status = dict(local_profile.get("promotion_status") or {})
    dense_sidecar = dict(local_profile.get("dense_sidecar") or {})
    route_runtime_contracts = {
        str(entry.get("route_id") or ""): dict(entry)
        for entry in list(local_profile.get("route_runtime_contracts") or [])
        if isinstance(entry, dict) and entry.get("route_id") is not None
    }
    projection_registry = {
        str(entry.get("projection_id") or ""): dict(entry)
        for entry in list(local_profile.get("projection_plan_v2_registry") or [])
        if isinstance(entry, dict) and entry.get("projection_id") is not None
    }
    route_recovery = {
        str(entry.get("route_id")): dict(entry)
        for entry in list(payload.get("route_recovery") or [])
        if isinstance(entry, dict) and entry.get("route_id") is not None
    }
    startup_validation = dict((payload.get("profile_diagnostics") or {}).get("startup_validation") or {})
    query_smoke = dict(payload.get("query_smoke") or {})
    query_smoke_summary = dict(query_smoke.get("summary") or {})

    def _expect_bool(raw: str | None, actual: bool) -> None:
        if raw is None:
            return
        expected = raw == "true"
        if actual != expected:
            raise SystemExit(2)

    _expect_bool(args.expect_profile_implemented, bool(startup_validation.get("profile_implemented")))
    _expect_bool(args.expect_boot_ready, bool(summary.get("boot_ready")))
    _expect_bool(args.expect_configuration_ready, bool(summary.get("configuration_ready")))
    _expect_bool(args.expect_route_runtime_ready, bool(summary.get("route_runtime_ready")))
    _expect_bool(
        args.expect_declared_executable_routes_runtime_ready,
        bool(summary.get("declared_executable_routes_runtime_ready")),
    )

    if args.expect_ready_projection_count is not None:
        if int(summary.get("ready_projection_count") or 0) != int(args.expect_ready_projection_count):
            raise SystemExit(2)
    _expect_bool(args.expect_query_smoke_passed, bool(query_smoke_summary.get("all_passed")))

    declared_executable_route_ids = _sorted_string_list(list(payload.get("declared_executable_route_ids") or []))
    declared_runtime_ready_route_ids = _sorted_string_list(
        list(payload.get("declared_executable_runtime_ready_ids") or [])
    )
    expected_declared_route_ids = _parse_csv(args.expect_declared_executable_route_ids)
    if expected_declared_route_ids and declared_executable_route_ids != sorted(expected_declared_route_ids):
        raise SystemExit(2)

    if promotion_status:
        if declared_executable_route_ids != _sorted_string_list(
            list(promotion_status.get("declared_executable_route_ids") or [])
        ):
            raise SystemExit(2)
        if declared_runtime_ready_route_ids != _sorted_string_list(
            list(promotion_status.get("declared_executable_runtime_ready_ids") or [])
        ):
            raise SystemExit(2)
        if int(summary.get("ready_projection_count") or 0) != int(
            promotion_status.get("ready_projection_count") or 0
        ):
            raise SystemExit(2)
        if int(summary.get("required_projection_count") or 0) != int(
            promotion_status.get("required_projection_count") or 0
        ):
            raise SystemExit(2)
        if bool(summary.get("declared_executable_routes_runtime_ready")) != bool(
            promotion_status.get("declared_executable_runtime_ready")
        ):
            raise SystemExit(2)

    if bool(summary.get("declared_executable_routes_runtime_ready")) and (
        declared_runtime_ready_route_ids != declared_executable_route_ids
    ):
        raise SystemExit(2)

    expected_degraded_routes = _parse_csv(args.expect_lexical_degraded_route_ids)
    actual_degraded_routes = _sorted_string_list(list(payload.get("lexical_degraded_route_ids") or []))
    if expected_degraded_routes and actual_degraded_routes != sorted(expected_degraded_routes):
        raise SystemExit(2)

    expected_gold_recommended_routes = _parse_csv(args.expect_lexical_gold_recommended_route_ids)
    actual_gold_recommended_routes = _sorted_string_list(
        list(payload.get("lexical_gold_recommended_route_ids") or [])
    )
    if expected_gold_recommended_routes and actual_gold_recommended_routes != sorted(expected_gold_recommended_routes):
        raise SystemExit(2)
    if promotion_status:
        if actual_degraded_routes != _sorted_string_list(
            list(promotion_status.get("lexical_degraded_route_ids") or [])
        ):
            raise SystemExit(2)
        if actual_gold_recommended_routes != _sorted_string_list(
            list(promotion_status.get("lexical_gold_recommended_route_ids") or [])
        ):
            raise SystemExit(2)

    for route_id in declared_executable_route_ids:
        recovery = route_recovery.get(route_id)
        if recovery is None:
            raise SystemExit(2)
        if not bool(recovery.get("runtime_ready")) and bool(summary.get("declared_executable_routes_runtime_ready")):
            raise SystemExit(2)
        if str(recovery.get("representation_scope_id") or "") == "":
            raise SystemExit(2)
        planning_v2 = dict(recovery.get("planning_v2") or {})
        query_ir_v2_template = dict(planning_v2.get("query_ir_v2_template") or {})
        projection_ir_v2 = dict(planning_v2.get("projection_ir_v2") or {})
        if not planning_v2:
            raise SystemExit(2)
        if str(query_ir_v2_template.get("route_id") or "") != route_id:
            raise SystemExit(2)
        if str(projection_ir_v2.get("representation_scope_id") or "") == "":
            raise SystemExit(2)

    if promotion_status:
        if _sorted_string_list(list(promotion_status.get("required_projection_ids") or [])) != _sorted_string_list(
            list(payload.get("required_projection_ids") or [])
        ):
            raise SystemExit(2)
        support_matrix_scope_ids = sorted(
            {
                str(entry.get("representation_scope_id") or "")
                for entry in list(local_profile.get("support_matrix") or [])
                if isinstance(entry, dict) and str(entry.get("representation_scope_id") or "")
            }
        )
        if _sorted_string_list(list(promotion_status.get("representation_scope_ids") or [])) != support_matrix_scope_ids:
            raise SystemExit(2)
        if bool(promotion_status.get("dense_sidecar_ready")) != bool(dense_sidecar.get("ready")):
            raise SystemExit(2)
        if bool(promotion_status.get("dense_sidecar_runtime_contract_ready")) != bool(
            dense_sidecar.get("runtime_contract_ready")
        ):
            raise SystemExit(2)
        if bool(promotion_status.get("dense_sidecar_promotion_contract_ready")) != bool(
            dense_sidecar.get("promotion_contract_ready")
        ):
            raise SystemExit(2)
        if str(promotion_status.get("dense_sidecar_lifecycle_state") or "") != str(
            dense_sidecar.get("lifecycle_state") or ""
        ):
            raise SystemExit(2)
        if _sorted_string_list(list(promotion_status.get("dense_sidecar_runtime_blockers") or [])) != _sorted_string_list(
            list(dense_sidecar.get("runtime_blockers") or [])
        ):
            raise SystemExit(2)
        if _sorted_string_list(list(promotion_status.get("dense_sidecar_promotion_blockers") or [])) != _sorted_string_list(
            list(dense_sidecar.get("promotion_blockers") or [])
        ):
            raise SystemExit(2)
        if not bool(promotion_status.get("projection_plan_v2_complete")):
            raise SystemExit(2)

    if _sorted_string_list(list(promotion_status.get("required_projection_ids") or [])) != sorted(projection_registry.keys()):
        raise SystemExit(2)

    if bool(summary.get("declared_executable_routes_runtime_ready")) and not bool(dense_sidecar.get("ready")):
        raise SystemExit(2)
    if bool(summary.get("declared_executable_routes_runtime_ready")) and _sorted_string_list(
        list(dense_sidecar.get("runtime_blockers") or [])
    ):
        raise SystemExit(2)
    if bool(summary.get("declared_executable_routes_runtime_ready")) and not bool(query_smoke_summary.get("all_passed")):
        raise SystemExit(2)

    for route_id in declared_executable_route_ids:
        contract = route_runtime_contracts.get(route_id)
        if contract is None:
            raise SystemExit(2)
        if str(contract.get("representation_scope_id") or "") == "":
            raise SystemExit(2)
        if not dict(contract.get("planning_v2") or {}):
            raise SystemExit(2)
        if bool(contract.get("dense_sidecar_required")) and not bool(dense_sidecar.get("ready")) and bool(contract.get("runtime_ready")):
            raise SystemExit(2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

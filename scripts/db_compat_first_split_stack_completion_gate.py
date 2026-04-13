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
from scripts.db_compat_profile_smoke import (
    _parse_env_pairs,
    _prepare_ready_split_stack_projection_metadata,
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
        description="Completion gate for the first executable split-stack profile."
    )
    parser.add_argument("--profile", required=True)
    parser.add_argument("--env", action="append", default=[])
    parser.add_argument("--projection-metadata-path", default=None)
    parser.add_argument("--enable-ready-split-stack-projections", action="store_true")
    parser.add_argument("--expect-boot-ready", choices=["true", "false"], default=None)
    parser.add_argument("--expect-configuration-ready", choices=["true", "false"], default=None)
    parser.add_argument("--expect-route-runtime-ready", choices=["true", "false"], default=None)
    parser.add_argument(
        "--expect-declared-executable-routes-runtime-ready",
        choices=["true", "false"],
        default=None,
    )
    parser.add_argument("--expect-backend-connectivity-ready", choices=["true", "false"], default=None)
    parser.add_argument("--expect-required-projection-count", type=int, default=None)
    parser.add_argument("--expect-ready-projection-count", type=int, default=None)
    parser.add_argument("--expect-declared-executable-route-ids", default=None)
    parser.add_argument("--expect-lexical-degraded-route-ids", default=None)
    parser.add_argument("--expect-lexical-gold-recommended-route-ids", default=None)
    parser.add_argument("--output", default=None)
    args = parser.parse_args(argv)

    if args.profile not in DEPLOYMENT_PROFILES:
        raise ValueError(f"Unknown profile id: {args.profile}")
    if args.enable_ready_split_stack_projections and args.projection_metadata_path:
        raise ValueError(
            "--enable-ready-split-stack-projections cannot be combined with --projection-metadata-path."
        )

    metadata_store_path = args.projection_metadata_path
    if args.enable_ready_split_stack_projections:
        metadata_store_path = _prepare_ready_split_stack_projection_metadata(args.profile)

    env_map = {"QUERYLAKE_DB_PROFILE": args.profile, **_parse_env_pairs(list(args.env or []))}
    with temporary_env(env_map):
        payload = build_profile_bringup_payload(
            profile=DEPLOYMENT_PROFILES[args.profile],
            metadata_store_path=metadata_store_path,
        )

    rendered = json.dumps(payload, indent=2)
    print(rendered)
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")

    summary = dict(payload.get("summary") or {})
    route_recovery = {
        str(entry.get("route_id")): dict(entry)
        for entry in list(payload.get("route_recovery") or [])
        if isinstance(entry, dict) and entry.get("route_id") is not None
    }

    def _expect_bool(raw: str | None, key: str) -> None:
        if raw is None:
            return
        expected = raw == "true"
        actual = bool(summary.get(key))
        if actual != expected:
            raise SystemExit(2)

    _expect_bool(args.expect_boot_ready, "boot_ready")
    _expect_bool(args.expect_configuration_ready, "configuration_ready")
    _expect_bool(args.expect_route_runtime_ready, "route_runtime_ready")
    _expect_bool(
        args.expect_declared_executable_routes_runtime_ready,
        "declared_executable_routes_runtime_ready",
    )
    _expect_bool(args.expect_backend_connectivity_ready, "backend_connectivity_ready")

    if args.expect_required_projection_count is not None:
        if int(summary.get("required_projection_count") or 0) != int(args.expect_required_projection_count):
            raise SystemExit(2)
    if args.expect_ready_projection_count is not None:
        if int(summary.get("ready_projection_count") or 0) != int(args.expect_ready_projection_count):
            raise SystemExit(2)

    declared_route_support = {
        str(key): str(value)
        for key, value in dict(payload.get("declared_route_support") or {}).items()
    }
    declared_executable_route_ids = _sorted_string_list(list(payload.get("declared_executable_route_ids") or []))
    declared_optional_route_ids = _sorted_string_list(list(payload.get("declared_optional_route_ids") or []))
    declared_runtime_ready_route_ids = _sorted_string_list(
        list(payload.get("declared_executable_runtime_ready_ids") or [])
    )
    declared_runtime_blocked_route_ids = _sorted_string_list(
        list(payload.get("declared_executable_runtime_blocked_ids") or [])
    )

    if int(summary.get("declared_route_count") or 0) != len(declared_route_support):
        raise SystemExit(2)
    if int(summary.get("declared_executable_route_count") or 0) != len(declared_executable_route_ids):
        raise SystemExit(2)
    if int(summary.get("declared_optional_route_count") or 0) != len(declared_optional_route_ids):
        raise SystemExit(2)
    if int(summary.get("declared_executable_runtime_ready_count") or 0) != len(declared_runtime_ready_route_ids):
        raise SystemExit(2)
    if int(summary.get("declared_executable_runtime_blocked_count") or 0) != len(declared_runtime_blocked_route_ids):
        raise SystemExit(2)
    if sorted(declared_route_support.keys()) != sorted(declared_executable_route_ids + declared_optional_route_ids):
        raise SystemExit(2)
    if sorted(declared_runtime_ready_route_ids + declared_runtime_blocked_route_ids) != declared_executable_route_ids:
        raise SystemExit(2)

    expected_declared_route_ids = _parse_csv(args.expect_declared_executable_route_ids)
    if expected_declared_route_ids:
        actual_declared_route_ids = declared_executable_route_ids
        if actual_declared_route_ids != sorted(expected_declared_route_ids):
            raise SystemExit(2)
        actual_ready_route_ids = declared_runtime_ready_route_ids
        if bool(summary.get("declared_executable_routes_runtime_ready")) and (
            actual_ready_route_ids != actual_declared_route_ids
        ):
            raise SystemExit(2)
        for route_id in actual_declared_route_ids:
            recovery = route_recovery.get(route_id)
            if recovery is None:
                raise SystemExit(2)
            if declared_route_support.get(route_id) != str(recovery.get("support_state") or ""):
                raise SystemExit(2)
            if bool(summary.get("declared_executable_routes_runtime_ready")) and not bool(
                recovery.get("runtime_ready")
            ):
                raise SystemExit(2)

    expected_degraded_routes = _parse_csv(args.expect_lexical_degraded_route_ids)
    if expected_degraded_routes:
        actual_degraded_routes = _sorted_string_list(list(payload.get("lexical_degraded_route_ids") or []))
        if actual_degraded_routes != sorted(expected_degraded_routes):
            raise SystemExit(2)

    expected_gold_recommended_routes = _parse_csv(args.expect_lexical_gold_recommended_route_ids)
    if expected_gold_recommended_routes:
        actual_gold_recommended_routes = _sorted_string_list(
            list(payload.get("lexical_gold_recommended_route_ids") or [])
        )
        if actual_gold_recommended_routes != sorted(expected_gold_recommended_routes):
            raise SystemExit(2)

    actual_degraded_route_set = set(_sorted_string_list(list(payload.get("lexical_degraded_route_ids") or [])))
    actual_gold_route_set = set(_sorted_string_list(list(payload.get("lexical_gold_recommended_route_ids") or [])))
    for route_id in declared_executable_route_ids:
        recovery = route_recovery.get(route_id)
        if recovery is None:
            raise SystemExit(2)
        if bool(recovery.get("gold_recommended_for_exact_constraints")) != (route_id in actual_gold_route_set):
            raise SystemExit(2)
        lexical_support_class = str(recovery.get("lexical_support_class") or "")
        if route_id in actual_degraded_route_set and not lexical_support_class.startswith("degraded"):
            raise SystemExit(2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

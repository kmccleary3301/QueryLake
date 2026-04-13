#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from typing import List

from QueryLake.runtime.db_compat import DEPLOYMENT_PROFILES
from QueryLake.runtime.profile_bringup import build_profile_bringup_payload
from scripts.db_compat_profile_smoke import (
    _parse_env_pairs,
    _prepare_ready_profile_projection_metadata,
    _prepare_ready_split_stack_projection_metadata,
    temporary_env,
)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DB compatibility profile bring-up smoke harness.")
    parser.add_argument("--profile", required=True)
    parser.add_argument("--env", action="append", default=[])
    parser.add_argument("--projection-metadata-path", default=None)
    parser.add_argument("--enable-ready-profile-projections", action="store_true")
    parser.add_argument("--enable-ready-split-stack-projections", action="store_true")
    parser.add_argument("--expect-boot-ready", choices=["true", "false"], default=None)
    parser.add_argument("--expect-configuration-ready", choices=["true", "false"], default=None)
    parser.add_argument("--expect-route-runtime-ready", choices=["true", "false"], default=None)
    parser.add_argument("--expect-declared-executable-routes-runtime-ready", choices=["true", "false"], default=None)
    parser.add_argument("--expect-backend-connectivity-ready", choices=["true", "false"], default=None)
    parser.add_argument("--expect-ready-projection-count", type=int, default=None)
    parser.add_argument("--expect-projection-needing-build", action="append", default=[])
    parser.add_argument("--expect-projection-building", action="append", default=[])
    parser.add_argument("--expect-projection-failed", action="append", default=[])
    parser.add_argument("--expect-projection-stale", action="append", default=[])
    parser.add_argument("--expect-projection-absent", action="append", default=[])
    parser.add_argument("--expect-route-runtime", action="append", default=[])
    parser.add_argument("--expect-route-blocker-kind", action="append", default=[])
    parser.add_argument("--expect-lexical-degraded-route", action="append", default=[])
    parser.add_argument("--expect-lexical-gold-recommended-route", action="append", default=[])
    parser.add_argument("--expect-required-projection-status-count", action="append", default=[])
    parser.add_argument("--expect-route-lexical-support-class-count", action="append", default=[])
    parser.add_argument("--expect-lexical-capability-blocker-count", action="append", default=[])
    parser.add_argument("--output", default=None)
    args = parser.parse_args(argv)

    if args.profile not in DEPLOYMENT_PROFILES:
        raise ValueError(f"Unknown profile id: {args.profile}")
    if args.enable_ready_profile_projections and args.enable_ready_split_stack_projections:
        raise ValueError(
            "--enable-ready-profile-projections cannot be combined with --enable-ready-split-stack-projections."
        )
    if (args.enable_ready_profile_projections or args.enable_ready_split_stack_projections) and args.projection_metadata_path:
        raise ValueError(
            "--enable-ready-profile-projections/--enable-ready-split-stack-projections cannot be combined with --projection-metadata-path."
        )

    metadata_store_path = args.projection_metadata_path
    if args.enable_ready_profile_projections:
        metadata_store_path = _prepare_ready_profile_projection_metadata(args.profile)
    elif args.enable_ready_split_stack_projections:
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
    routes = {
        str(entry.get("route_id")): dict(entry)
        for entry in list(((payload.get("profile_diagnostics") or {}).get("route_executors") or []))
        if isinstance(entry, dict) and isinstance(entry.get("route_id"), str)
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

    if args.expect_ready_projection_count is not None:
        if int(summary.get("ready_projection_count") or 0) != int(args.expect_ready_projection_count):
            raise SystemExit(2)

    needing_build = set(str(value) for value in list(payload.get("projection_ids_needing_build") or []))
    for projection_id in list(args.expect_projection_needing_build or []):
        if str(projection_id) not in needing_build:
            raise SystemExit(2)

    projection_status_lists = {
        "building": set(str(value) for value in list(payload.get("projection_building_ids") or [])),
        "failed": set(str(value) for value in list(payload.get("projection_failed_ids") or [])),
        "stale": set(str(value) for value in list(payload.get("projection_stale_ids") or [])),
        "absent": set(str(value) for value in list(payload.get("projection_absent_ids") or [])),
    }
    for projection_id in list(args.expect_projection_building or []):
        if str(projection_id) not in projection_status_lists["building"]:
            raise SystemExit(2)
    for projection_id in list(args.expect_projection_failed or []):
        if str(projection_id) not in projection_status_lists["failed"]:
            raise SystemExit(2)
    for projection_id in list(args.expect_projection_stale or []):
        if str(projection_id) not in projection_status_lists["stale"]:
            raise SystemExit(2)
    for projection_id in list(args.expect_projection_absent or []):
        if str(projection_id) not in projection_status_lists["absent"]:
            raise SystemExit(2)

    for raw in list(args.expect_route_runtime or []):
        if "=" not in raw:
            raise ValueError(f"Invalid --expect-route-runtime value '{raw}'. Expected ROUTE_ID=true|false.")
        route_id, expected_raw = raw.split("=", 1)
        expected = expected_raw.strip().lower() == "true"
        actual = bool(routes.get(route_id.strip(), {}).get("runtime_ready"))
        if actual != expected:
            raise SystemExit(2)

    for raw in list(args.expect_route_blocker_kind or []):
        if "=" not in raw:
            raise ValueError(
                f"Invalid --expect-route-blocker-kind value '{raw}'. Expected ROUTE_ID=blocker_kind."
            )
        route_id, blocker_kind = raw.split("=", 1)
        actual_kinds = [
            str(entry.get("kind"))
            for entry in list(routes.get(route_id.strip(), {}).get("runtime_blockers") or [])
            if isinstance(entry, dict) and entry.get("kind") is not None
        ]
        if blocker_kind.strip() not in actual_kinds:
            raise SystemExit(2)

    lexical_degraded_routes = set(str(value) for value in list(payload.get("lexical_degraded_route_ids") or []))
    lexical_gold_routes = set(str(value) for value in list(payload.get("lexical_gold_recommended_route_ids") or []))
    for route_id in list(args.expect_lexical_degraded_route or []):
        if str(route_id) not in lexical_degraded_routes:
            raise SystemExit(2)
    for route_id in list(args.expect_lexical_gold_recommended_route or []):
        if str(route_id) not in lexical_gold_routes:
            raise SystemExit(2)

    def _expect_count_pairs(raw_values: List[str], actual: Dict[str, Any]) -> None:
        for raw in raw_values:
            if "=" not in raw:
                raise ValueError(f"Invalid expectation value '{raw}'. Expected KEY=count.")
            key, expected_raw = raw.split("=", 1)
            expected = int(expected_raw.strip())
            if int(actual.get(key.strip()) or 0) != expected:
                raise SystemExit(2)

    _expect_count_pairs(
        list(args.expect_required_projection_status_count or []),
        dict(summary.get("required_projection_status_counts") or {}),
    )
    _expect_count_pairs(
        list(args.expect_route_lexical_support_class_count or []),
        dict(summary.get("route_lexical_support_class_counts") or {}),
    )
    _expect_count_pairs(
        list(args.expect_lexical_capability_blocker_count or []),
        dict(summary.get("lexical_capability_blocker_counts") or {}),
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

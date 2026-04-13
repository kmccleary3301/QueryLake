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

from QueryLake.database.create_db_session import initialize_database_engine
from QueryLake.runtime.db_compat import DEPLOYMENT_PROFILES
from QueryLake.runtime.profile_bringup import build_profile_bringup_payload
from QueryLake.runtime.projection_refresh import bootstrap_profile_projections
from scripts.db_compat_profile_smoke import _parse_env_pairs, temporary_env


def _build_bootstrap_delta(*, before: dict, after: dict, bootstrap_report: dict) -> dict:
    before_summary = dict(before.get("summary") or {})
    after_summary = dict(after.get("summary") or {})
    before_ready_projection_ids = set(str(value) for value in list(before.get("ready_projection_ids") or []))
    after_ready_projection_ids = set(str(value) for value in list(after.get("ready_projection_ids") or []))
    before_runtime_ready_route_ids = set(str(value) for value in list(before.get("route_runtime_ready_ids") or []))
    after_runtime_ready_route_ids = set(str(value) for value in list(after.get("route_runtime_ready_ids") or []))
    before_backend_unreachable_planes = set(str(value) for value in list(before.get("backend_unreachable_planes") or []))
    after_backend_unreachable_planes = set(str(value) for value in list(after.get("backend_unreachable_planes") or []))
    bootstrap_metadata = dict(bootstrap_report.get("metadata") or {})
    return {
        "boot_ready_before": bool(before_summary.get("boot_ready")),
        "boot_ready_after": bool(after_summary.get("boot_ready")),
        "route_runtime_ready_before": bool(before_summary.get("route_runtime_ready")),
        "route_runtime_ready_after": bool(after_summary.get("route_runtime_ready")),
        "backend_connectivity_ready_before": bool(before_summary.get("backend_connectivity_ready")),
        "backend_connectivity_ready_after": bool(after_summary.get("backend_connectivity_ready")),
        "ready_projection_count_before": int(before_summary.get("ready_projection_count") or 0),
        "ready_projection_count_after": int(after_summary.get("ready_projection_count") or 0),
        "runtime_ready_route_count_before": int(before_summary.get("runtime_ready_route_count") or 0),
        "runtime_ready_route_count_after": int(after_summary.get("runtime_ready_route_count") or 0),
        "projection_ids_recovered": sorted(after_ready_projection_ids - before_ready_projection_ids),
        "route_ids_recovered": sorted(after_runtime_ready_route_ids - before_runtime_ready_route_ids),
        "backend_planes_recovered": sorted(before_backend_unreachable_planes - after_backend_unreachable_planes),
        "projection_ids_still_needing_build": list(after.get("projection_ids_needing_build") or []),
        "route_ids_still_runtime_blocked": list(after.get("route_runtime_blocked_ids") or []),
        "bootstrap_improved_runtime_readiness": (
            bool(after_summary.get("boot_ready"))
            or int(after_summary.get("runtime_ready_route_count") or 0) > int(before_summary.get("runtime_ready_route_count") or 0)
            or int(after_summary.get("ready_projection_count") or 0) > int(before_summary.get("ready_projection_count") or 0)
        ),
        "lifecycle_outcome_counts": dict(bootstrap_metadata.get("lifecycle_outcome_counts") or {}),
    }


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bootstrap required DB-compat projections for a profile.")
    parser.add_argument("--profile", required=True)
    parser.add_argument("--projection-id", action="append", default=[])
    parser.add_argument("--projection-metadata-path", "--metadata-store-path", dest="projection_metadata_path", default=None)
    parser.add_argument("--env", action="append", default=[])
    parser.add_argument("--validate-runtime-ready", action="store_true")
    parser.add_argument("--expect-boot-ready", choices=["true", "false"], default=None)
    parser.add_argument("--expect-configuration-ready", choices=["true", "false"], default=None)
    parser.add_argument("--expect-route-runtime-ready", choices=["true", "false"], default=None)
    parser.add_argument("--expect-backend-connectivity-ready", choices=["true", "false"], default=None)
    parser.add_argument("--expect-executed-action-count", type=int, default=None)
    parser.add_argument("--expect-skipped-action-count", type=int, default=None)
    parser.add_argument("--expect-projection-status", action="append", default=[])
    parser.add_argument("--output", default=None)
    args = parser.parse_args(argv)

    if args.profile not in DEPLOYMENT_PROFILES:
        raise ValueError(f"Unknown profile id: {args.profile}")

    env_map = {"QUERYLAKE_DB_PROFILE": args.profile, **_parse_env_pairs(list(args.env or []))}
    with temporary_env(env_map):
        database_result = initialize_database_engine()
        if isinstance(database_result, tuple):
            database, _engine = database_result
        else:
            database, _engine = database_result, None
        try:
            profile_diagnostics_before = (
                build_profile_bringup_payload(
                    profile=DEPLOYMENT_PROFILES[args.profile],
                    metadata_store_path=args.projection_metadata_path,
                )
                if args.validate_runtime_ready
                else None
            )
            bootstrap_report = bootstrap_profile_projections(
                database=database,
                profile=DEPLOYMENT_PROFILES[args.profile],
                projection_ids=list(args.projection_id or []),
                metadata_store_path=args.projection_metadata_path,
            )
            profile_diagnostics_after = (
                build_profile_bringup_payload(
                    profile=DEPLOYMENT_PROFILES[args.profile],
                    metadata_store_path=args.projection_metadata_path,
                )
                if args.validate_runtime_ready
                else None
            )
        finally:
            database.close()
            if _engine is not None:
                _engine.dispose()

    payload = {"bootstrap_report": bootstrap_report.model_dump()}
    if profile_diagnostics_after is not None:
        payload["profile_diagnostics_before"] = profile_diagnostics_before
        payload["profile_diagnostics"] = profile_diagnostics_after
        payload["bootstrap_delta"] = _build_bootstrap_delta(
            before=profile_diagnostics_before or {},
            after=profile_diagnostics_after,
            bootstrap_report=payload["bootstrap_report"],
        )

    rendered = json.dumps(payload, indent=2)
    print(rendered)
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")

    bootstrap_payload = dict(payload.get("bootstrap_report") or {})
    bootstrap_metadata = dict(bootstrap_payload.get("metadata") or {})
    if args.expect_executed_action_count is not None:
        if int(bootstrap_metadata.get("executed_action_count") or 0) != int(args.expect_executed_action_count):
            raise SystemExit(2)
    if args.expect_skipped_action_count is not None:
        if int(bootstrap_metadata.get("skipped_action_count") or 0) != int(args.expect_skipped_action_count):
            raise SystemExit(2)
    if profile_diagnostics_after is not None:
        bringup_summary = dict(profile_diagnostics_after.get("summary") or {})

        def _expect_bool(raw: str | None, key: str) -> None:
            if raw is None:
                return
            expected = raw == "true"
            actual = bool(bringup_summary.get(key))
            if actual != expected:
                raise SystemExit(2)

        _expect_bool(args.expect_boot_ready, "boot_ready")
        _expect_bool(args.expect_configuration_ready, "configuration_ready")
        _expect_bool(args.expect_route_runtime_ready, "route_runtime_ready")
        _expect_bool(args.expect_backend_connectivity_ready, "backend_connectivity_ready")
    for raw in list(args.expect_projection_status or []):
        if "=" not in raw:
            raise ValueError(
                f"Invalid --expect-projection-status value '{raw}'. Expected PROJECTION_ID=status."
            )
        projection_id, expected_status = raw.split("=", 1)
        status_lists = {
            "ready": list(bootstrap_payload.get("ready_projection_ids") or []),
            "building": list(bootstrap_payload.get("building_projection_ids") or []),
            "stale": list(bootstrap_payload.get("stale_projection_ids") or []),
            "failed": list(bootstrap_payload.get("failed_projection_ids") or []),
            "absent": list(bootstrap_payload.get("absent_projection_ids") or []),
        }
        actual_status = None
        for status, projection_ids in status_lists.items():
            if projection_id.strip() in {str(value) for value in projection_ids}:
                actual_status = status
                break
        if actual_status != expected_status.strip():
            raise SystemExit(2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

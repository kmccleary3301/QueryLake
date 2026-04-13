#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import os
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from typing import Dict, Iterator, List

from QueryLake.runtime.db_compat import DEPLOYMENT_PROFILES, build_profile_diagnostics_payload
from QueryLake.runtime.projection_refresh import mark_projection_build_ready


@contextmanager
def temporary_env(mapping: Dict[str, str]) -> Iterator[None]:
    previous = {key: os.environ.get(key) for key in mapping}
    try:
        for key, value in mapping.items():
            os.environ[key] = value
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _parse_env_pairs(values: List[str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for raw in values:
        if "=" not in raw:
            raise ValueError(f"Invalid --env value '{raw}'. Expected KEY=VALUE.")
        key, value = raw.split("=", 1)
        out[key.strip()] = value
    return out


def _prepare_ready_profile_projection_metadata(profile_id: str) -> str:
    temp_path = Path(tempfile.gettempdir()) / f"querylake_db_compat_smoke_{profile_id}_{int(time.time() * 1000)}.json"
    temp_path.write_text("{}", encoding="utf-8")
    if profile_id == "aws_aurora_pg_opensearch_v1":
        ready_items = [
            ("document_chunk_lexical_projection_v1", "lexical", "opensearch", "smoke:lexical"),
            ("document_chunk_dense_projection_v1", "dense", "opensearch", "smoke:dense"),
            ("file_chunk_lexical_projection_v1", "lexical", "opensearch", "smoke:file"),
        ]
    elif profile_id == "sqlite_fts5_dense_sidecar_local_v1":
        ready_items = [
            ("document_chunk_lexical_projection_v1", "lexical", "sqlite_fts5", "smoke:local-lexical"),
            ("document_chunk_dense_projection_v1", "dense", "local_dense_sidecar", "smoke:local-dense"),
            ("file_chunk_lexical_projection_v1", "lexical", "sqlite_fts5", "smoke:local-file"),
        ]
    else:
        raise ValueError(
            "--enable-ready-profile-projections is only supported for "
            "aws_aurora_pg_opensearch_v1 and sqlite_fts5_dense_sidecar_local_v1 in the current smoke harness."
        )

    for projection_id, lane_family, target_backend, revision in ready_items:
        mark_projection_build_ready(
            projection_id=projection_id,
            projection_version="v1",
            profile_id=profile_id,
            lane_family=lane_family,
            target_backend=target_backend,
            build_revision=revision,
            metadata={"source": "db_compat_profile_smoke"},
            path=str(temp_path),
        )
    return str(temp_path)


def _prepare_ready_split_stack_projection_metadata(profile_id: str) -> str:
    if profile_id != "aws_aurora_pg_opensearch_v1":
        raise ValueError(
            "--enable-ready-split-stack-projections is only supported for "
            "aws_aurora_pg_opensearch_v1 in the current smoke harness."
        )
    return _prepare_ready_profile_projection_metadata(profile_id)


def main() -> int:
    parser = argparse.ArgumentParser(description="DB compatibility profile smoke harness.")
    parser.add_argument("--profile", required=True)
    parser.add_argument("--env", action="append", default=[])
    parser.add_argument("--projection-metadata-path", default=None)
    parser.add_argument("--enable-ready-profile-projections", action="store_true")
    parser.add_argument("--enable-ready-split-stack-projections", action="store_true")
    parser.add_argument("--expect-boot-ready", choices=["true", "false"], default=None)
    parser.add_argument("--expect-route-execution-ready", choices=["true", "false"], default=None)
    parser.add_argument("--expect-route-runtime-ready", choices=["true", "false"], default=None)
    parser.add_argument("--expect-declared-executable-routes-runtime-ready", choices=["true", "false"], default=None)
    parser.add_argument("--expect-route-implemented", action="append", default=[])
    parser.add_argument("--expect-route-runtime", action="append", default=[])
    parser.add_argument("--expect-route-blocker-kind", action="append", default=[])
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

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
        payload = build_profile_diagnostics_payload(
            profile=DEPLOYMENT_PROFILES[args.profile],
            metadata_store_path=metadata_store_path,
        )

    print(json.dumps(payload, indent=2))
    if args.output:
        Path(args.output).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if args.expect_boot_ready is not None:
        expected = args.expect_boot_ready == "true"
        boot_ready = bool(((payload.get("startup_validation") or {}).get("boot_ready")))
        if boot_ready != expected:
            return 2
    if args.expect_route_execution_ready is not None:
        expected = args.expect_route_execution_ready == "true"
        route_execution_ready = bool(((payload.get("startup_validation") or {}).get("route_execution_ready")))
        if route_execution_ready != expected:
            return 2
    if args.expect_route_runtime_ready is not None:
        expected = args.expect_route_runtime_ready == "true"
        route_runtime_ready = bool(((payload.get("startup_validation") or {}).get("route_runtime_ready")))
        if route_runtime_ready != expected:
            return 2
    if args.expect_declared_executable_routes_runtime_ready is not None:
        expected = args.expect_declared_executable_routes_runtime_ready == "true"
        declared_runtime_ready = bool(
            ((payload.get("startup_validation") or {}).get("declared_executable_routes_runtime_ready"))
        )
        if declared_runtime_ready != expected:
            return 2

    routes = {
        str(entry.get("route_id")): dict(entry)
        for entry in list(payload.get("route_executors") or [])
        if isinstance(entry, dict) and isinstance(entry.get("route_id"), str)
    }

    for raw in list(args.expect_route_implemented or []):
        if "=" not in raw:
            raise ValueError(f"Invalid --expect-route-implemented value '{raw}'. Expected ROUTE_ID=true|false.")
        route_id, expected_raw = raw.split("=", 1)
        expected = expected_raw.strip().lower() == "true"
        actual = bool(routes.get(route_id.strip(), {}).get("implemented"))
        if actual != expected:
            return 2

    for raw in list(args.expect_route_runtime or []):
        if "=" not in raw:
            raise ValueError(f"Invalid --expect-route-runtime value '{raw}'. Expected ROUTE_ID=true|false.")
        route_id, expected_raw = raw.split("=", 1)
        expected = expected_raw.strip().lower() == "true"
        actual = bool(routes.get(route_id.strip(), {}).get("runtime_ready"))
        if actual != expected:
            return 2

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
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

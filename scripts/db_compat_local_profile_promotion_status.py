#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import asdict
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


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report current promotion status for the local embedded profile."
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

    profile = DEPLOYMENT_PROFILES[args.profile]
    metadata_store_path = args.projection_metadata_path
    if args.enable_ready_profile_projections:
        metadata_store_path = _prepare_ready_profile_projection_metadata(args.profile)

    env_map = {"QUERYLAKE_DB_PROFILE": args.profile, **_parse_env_pairs(list(args.env or []))}
    with temporary_env(env_map):
        bringup = build_profile_bringup_payload(
            profile=profile,
            metadata_store_path=metadata_store_path,
        )

    local_profile = dict(bringup.get("local_profile") or {})
    query_smoke = build_local_query_smoke_payload(
        profile_id=args.profile,
        enable_ready_profile_projections=bool(args.enable_ready_profile_projections),
        metadata_store_path=metadata_store_path,
    )
    payload: Dict[str, Any] = {
        "profile": {
            "id": profile.id,
            "label": profile.label,
            "implemented": bool(profile.implemented),
            "maturity": profile.maturity,
            "backend_stack": asdict(profile.backend_stack),
        },
        "local_profile": local_profile,
        "support_matrix": list(local_profile.get("support_matrix") or []),
        "route_runtime_contracts": list(local_profile.get("route_runtime_contracts") or []),
        "projection_plan_v2_registry": list(local_profile.get("projection_plan_v2_registry") or []),
        "dense_sidecar": dict(local_profile.get("dense_sidecar") or {}),
        "promotion_status": dict(local_profile.get("promotion_status") or {}),
        "query_smoke": query_smoke,
        "docs_ref": "docs/database/LOCAL_PROFILE_PROMOTION_BAR.md",
    }

    rendered = json.dumps(payload, indent=2)
    print(rendered)
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

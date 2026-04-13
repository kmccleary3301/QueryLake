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
    _prepare_ready_profile_projection_metadata,
    temporary_env,
)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report scope-expansion readiness for the supported local embedded profile."
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

    local_profile = dict(bringup.get("local_profile") or {})
    payload: Dict[str, Any] = {
        "profile": dict(bringup.get("profile") or {}),
        "summary": dict(bringup.get("summary") or {}),
        "scope_expansion_status": dict(local_profile.get("scope_expansion_status") or {}),
        "scope_expansion_contract": dict(local_profile.get("scope_expansion_contract") or {}),
        "promotion_status": dict(local_profile.get("promotion_status") or {}),
        "docs_ref": "docs/database/LOCAL_PROFILE_SCOPE_EXPANSION_CRITERIA.md",
    }
    rendered = json.dumps(payload, indent=2)
    print(rendered)
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

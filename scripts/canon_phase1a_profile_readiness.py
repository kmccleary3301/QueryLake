#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from QueryLake.canon.runtime import (
    build_phase1a_profile_readiness_bundle,
    build_phase1a_search_plane_a_transition_bundle,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Canon++ Phase 1A profile readiness bundle.")
    parser.add_argument("--profile-id", default="aws_aurora_pg_opensearch_v1")
    parser.add_argument("--route", action="append", dest="routes", default=None)
    parser.add_argument("--metadata-store-path", default=None)
    parser.add_argument("--include-transition-bundle", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    payload = build_phase1a_profile_readiness_bundle(
        profile_id=args.profile_id,
        routes=args.routes,
        metadata_store_path=args.metadata_store_path,
    )
    if args.include_transition_bundle:
        payload["search_plane_a_transition"] = build_phase1a_search_plane_a_transition_bundle(
            source_profile_id=args.profile_id,
            target_profile_id="planetscale_opensearch_v1",
            routes=args.routes,
            source_metadata_store_path=args.metadata_store_path,
        )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(output),
                "profile_id": payload["profile"]["id"],
                "route_count": payload["summary"]["route_count"],
                "runtime_ready_count": payload["summary"]["runtime_ready_count"],
                "projection_count": payload["summary"]["projection_count"],
                "recommendations": list(payload.get("recommendations") or []),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

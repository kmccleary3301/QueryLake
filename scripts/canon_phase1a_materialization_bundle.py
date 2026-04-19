#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from QueryLake.canon.materialization import (
    build_phase1a_materialization_bundle,
    persist_phase1a_materialization_bundle,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Canon++ Phase 1A materialization bundle.")
    parser.add_argument("--profile-id", default="aws_aurora_pg_opensearch_v1")
    parser.add_argument("--projection-id", action="append", dest="projection_ids", default=None)
    parser.add_argument("--metadata-store-path", default=None)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    bundle = build_phase1a_materialization_bundle(
        profile_id=args.profile_id,
        projection_ids=args.projection_ids,
        metadata_store_path=args.metadata_store_path,
    )
    persist_phase1a_materialization_bundle(bundle=bundle, output_path=args.output)
    print(
        json.dumps(
            {
                "output": args.output,
                "profile_id": bundle["profile"]["id"],
                "plan_count": bundle["summary"]["plan_count"],
                "rebuild_plan_count": bundle["summary"]["rebuild_plan_count"],
                "recommendations": list(bundle.get("recommendations") or []),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

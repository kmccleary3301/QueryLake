#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from QueryLake.canon.runtime import build_phase1a_bootstrap_bundle


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Canon++ Phase 1A split-stack bootstrap bundle.")
    parser.add_argument("--profile-id", default="aws_aurora_pg_opensearch_v1")
    parser.add_argument("--projection-id", action="append", dest="projection_ids", default=None)
    parser.add_argument("--metadata-store-path", default=None)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    payload = build_phase1a_bootstrap_bundle(
        profile_id=args.profile_id,
        projection_ids=args.projection_ids,
        metadata_store_path=args.metadata_store_path,
        execute=bool(args.execute),
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(output),
                "profile_id": payload["profile"]["id"],
                "execute": bool(payload["execute"]),
                "ready_projection_count_before": payload["summary"]["ready_projection_count_before"],
                "ready_projection_count_after": payload["summary"]["ready_projection_count_after"],
                "recommendations": list(payload.get("recommendations") or []),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

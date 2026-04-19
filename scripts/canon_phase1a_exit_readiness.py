#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from QueryLake.canon.runtime import build_phase1a_exit_readiness_bundle


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Canon++ Phase 1A exit-readiness bundle.")
    parser.add_argument("--profile-id", default="aws_aurora_pg_opensearch_v1")
    parser.add_argument("--shadow-artifact-dir", required=True)
    parser.add_argument("--metadata-store-path", default=None)
    parser.add_argument("--route", action="append", dest="routes", default=None)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    payload = build_phase1a_exit_readiness_bundle(
        profile_id=args.profile_id,
        shadow_artifact_dir=args.shadow_artifact_dir,
        metadata_store_path=args.metadata_store_path,
        routes=args.routes,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(output),
                "profile_id": payload["profile_id"],
                "ready_for_phase1b": bool(payload["summary"]["ready_for_phase1b"]),
                "report_count": int(payload["summary"]["report_count"]),
                "candidate_set_delta_count": int(payload["summary"]["candidate_set_delta_count"]),
                "recommendations": list(payload.get("recommendations") or []),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

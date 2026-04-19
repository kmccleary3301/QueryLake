#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from QueryLake.canon.runtime import (
    apply_shadow_retention_plan,
    build_shadow_artifact_catalog,
    build_shadow_retention_plan,
    load_shadow_artifacts,
    persist_shadow_artifact_catalog,
    persist_shadow_retention_plan,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Canon++ Phase 1A shadow artifact catalog and retention plan.")
    parser.add_argument("--artifact-dir", required=True, help="Directory containing shadow reports/bundles/traces.")
    parser.add_argument(
        "--catalog-output",
        default=None,
        help="Optional explicit output path for the artifact catalog JSON.",
    )
    parser.add_argument(
        "--retention-output",
        default=None,
        help="Optional explicit output path for the retention plan JSON.",
    )
    parser.add_argument(
        "--keep-latest-per-route",
        type=int,
        default=10,
        help="Number of newest report generations to keep per route in the retention plan.",
    )
    parser.add_argument(
        "--apply-retention",
        action="store_true",
        help="Apply the retention plan instead of only emitting it.",
    )
    args = parser.parse_args()

    artifact_dir = Path(args.artifact_dir)
    artifacts = load_shadow_artifacts(artifact_dir)
    catalog = build_shadow_artifact_catalog(artifacts)
    plan = build_shadow_retention_plan(
        artifacts,
        keep_latest_per_route=args.keep_latest_per_route,
    )

    catalog_output = args.catalog_output or str(artifact_dir / "canon_phase1a_shadow_artifact_catalog.json")
    retention_output = args.retention_output or str(artifact_dir / "canon_phase1a_shadow_retention_plan.json")
    persist_shadow_artifact_catalog(catalog=catalog, output_path=catalog_output)
    persist_shadow_retention_plan(plan=plan, output_path=retention_output)
    apply_result = apply_shadow_retention_plan(plan, dry_run=not args.apply_retention)

    print(
        json.dumps(
            {
                "catalog_output": catalog_output,
                "retention_output": retention_output,
                "artifact_count": int(catalog.get("artifact_count", 0)),
                "recommendations": list(catalog.get("recommendations") or []),
                "apply_result": apply_result,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from QueryLake.canon.package import build_route_graph_package_bundle, persist_graph_package_bundle


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and persist a Canon++ Phase 1A graph package bundle.")
    parser.add_argument("--route", required=True)
    parser.add_argument("--package-revision", required=True)
    parser.add_argument("--profile-target", action="append", dest="profile_targets", default=None)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    bundle = build_route_graph_package_bundle(
        route=args.route,
        package_revision=args.package_revision,
        profile_targets=args.profile_targets,
    )
    persisted = persist_graph_package_bundle(bundle=bundle, output_dir=args.output_dir)
    print(
        json.dumps(
            {
                "package_id": persisted["package_id"],
                "path": persisted["path"],
                "graph_id": bundle["graph"]["graph_id"],
                "node_count": bundle["graph"]["node_count"],
                "profile_targets": bundle["profile_targets"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

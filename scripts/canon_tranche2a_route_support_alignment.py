#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from QueryLake.canon.runtime.route_support_alignment import (
    build_route_scoped_support_matrix,
    build_route_slice_support_alignment,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Canon++ Tranche 2A route-slice support alignment payload.")
    parser.add_argument("--route", default="search_bm25.document_chunk")
    parser.add_argument("--profile", default="planetscale_opensearch_v1")
    parser.add_argument("--package-registry", required=True)
    parser.add_argument("--pointer-registry", required=True)
    parser.add_argument("--route-serving-registry", required=True)
    parser.add_argument("--mode", choices=["shadow", "candidate_primary", "primary"], default="primary")
    parser.add_argument("--matrix", action="store_true", help="Build the V5 route-scoped support matrix.")
    parser.add_argument("--output")
    args = parser.parse_args()

    if args.matrix:
        payload = build_route_scoped_support_matrix(
            profile_id=args.profile,
            package_registry_path=args.package_registry,
            pointer_registry_path=args.pointer_registry,
            route_serving_registry_path=args.route_serving_registry,
            mode=args.mode,
        )
    else:
        payload = build_route_slice_support_alignment(
            route_id=args.route,
            profile_id=args.profile,
            package_registry_path=args.package_registry,
            pointer_registry_path=args.pointer_registry,
            route_serving_registry_path=args.route_serving_registry,
            mode=args.mode,
        )
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

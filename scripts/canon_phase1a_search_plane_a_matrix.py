from __future__ import annotations

import argparse
import json

from QueryLake.canon.runtime.search_plane_a_matrix import build_search_plane_a_lowering_matrix


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the bounded Phase 1A Search Plane A lowering matrix.")
    parser.add_argument("--route", action="append", dest="routes", help="Route to include. Repeat for multiple.")
    parser.add_argument("--profile-id", action="append", dest="profile_ids", help="Profile to include. Repeat for multiple.")
    parser.add_argument("--package-registry-path", required=True, help="Path to the graph package registry JSON.")
    parser.add_argument("--pointer-registry-path", required=True, help="Path to the pointer registry JSON.")
    parser.add_argument("--mode", default="shadow", help="Pointer mode to resolve.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_search_plane_a_lowering_matrix(
        routes=args.routes or [
            "search_bm25.document_chunk",
            "search_hybrid.document_chunk",
            "search_file_chunks",
        ],
        profile_ids=args.profile_ids or [
            "aws_aurora_pg_opensearch_v1",
            "planetscale_opensearch_v1",
        ],
        package_registry_path=args.package_registry_path,
        pointer_registry_path=args.pointer_registry_path,
        mode=args.mode,
    )
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            f"{payload['summary']['row_count']} lowering rows; "
            f"modes={payload['summary']['execution_mode_counts']}"
        )


if __name__ == "__main__":
    main()

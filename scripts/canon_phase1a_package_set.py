from __future__ import annotations

import argparse
import json

from QueryLake.canon.package import build_phase1a_package_set_bundle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build and register the bounded Phase 1A package set.")
    parser.add_argument("--route", action="append", dest="routes", help="Route to include. Repeat for multiple.")
    parser.add_argument("--package-revision", required=True, help="Package revision identifier.")
    parser.add_argument("--output-dir", required=True, help="Directory for package artifacts.")
    parser.add_argument("--registry-path", required=True, help="Path to the package registry JSON.")
    parser.add_argument("--disable-hybrid-sparse", action="store_true", help="Compile the bounded hybrid route with sparse disabled.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_phase1a_package_set_bundle(
        routes=args.routes or [
            "search_bm25.document_chunk",
            "search_hybrid.document_chunk",
            "search_file_chunks",
        ],
        package_revision=args.package_revision,
        output_dir=args.output_dir,
        registry_path=args.registry_path,
        route_options=(
            {"search_hybrid.document_chunk": {"disable_sparse": True}}
            if args.disable_hybrid_sparse
            else None
        ),
    )
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            f"Built {len(payload['route_rows'])} packages at revision {payload['package_revision']} "
            f"into {payload['registry_path']}"
        )


if __name__ == "__main__":
    main()

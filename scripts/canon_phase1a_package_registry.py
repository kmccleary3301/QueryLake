from __future__ import annotations

import argparse
import json
from pathlib import Path

from QueryLake.canon.package import (
    build_route_graph_package_bundle,
    load_graph_package_registry,
    persist_graph_package_bundle,
    register_graph_package_bundle,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build and register bounded Phase 1A graph packages.")
    parser.add_argument("--route", action="append", dest="routes", help="Route to package. Repeat for multiple.")
    parser.add_argument("--package-revision", required=True, help="Package revision identifier.")
    parser.add_argument("--output-dir", required=True, help="Directory for persisted package artifacts.")
    parser.add_argument("--registry-path", required=True, help="Path to the package registry JSON.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    routes = args.routes or [
        "search_bm25.document_chunk",
        "search_hybrid.document_chunk",
        "search_file_chunks",
    ]
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for route in routes:
        bundle = build_route_graph_package_bundle(
            route=route,
            package_revision=args.package_revision,
        )
        persisted = persist_graph_package_bundle(bundle=bundle, output_dir=output_dir)
        register_graph_package_bundle(
            bundle=bundle,
            registry_path=args.registry_path,
            artifact_path=persisted["path"],
        )

    payload = load_graph_package_registry(args.registry_path)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Registered {len(payload.get('packages') or [])} packages in {args.registry_path}")


if __name__ == "__main__":
    main()

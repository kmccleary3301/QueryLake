from __future__ import annotations

import argparse
import json

from QueryLake.canon.runtime.search_plane_a_lowering import build_search_plane_a_lowering_bundle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a Phase 1A Search Plane A lowering bundle.")
    parser.add_argument("--route", required=True, help="Route id to lower.")
    parser.add_argument("--profile-id", required=True, help="Target deployment profile id.")
    parser.add_argument("--package-registry-path", required=True, help="Path to graph package registry JSON.")
    parser.add_argument("--pointer-registry-path", required=True, help="Path to pointer registry JSON.")
    parser.add_argument("--mode", default="shadow", help="Pointer mode to resolve against.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_search_plane_a_lowering_bundle(
        route_id=args.route,
        profile_id=args.profile_id,
        package_registry_path=args.package_registry_path,
        pointer_registry_path=args.pointer_registry_path,
        mode=args.mode,
    )
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            f"{payload['route_id']} on {payload['profile']['id']}: "
            f"{payload['execution_mode']} "
            f"(selected_package={payload['selected_package']['resolved']})"
        )


if __name__ == "__main__":
    main()

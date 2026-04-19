from __future__ import annotations

import argparse
import json

from QueryLake.canon.runtime import build_search_plane_a_execution_contract


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Canon++ Search Plane A execution contract.")
    parser.add_argument("--route", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--package-registry", required=True)
    parser.add_argument("--pointer-registry", required=True)
    parser.add_argument("--mode", default="shadow")
    parser.add_argument("--output")
    args = parser.parse_args()

    payload = build_search_plane_a_execution_contract(
        route_id=args.route,
        profile_id=args.profile,
        package_registry_path=args.package_registry,
        pointer_registry_path=args.pointer_registry,
        mode=args.mode,
    )
    rendered = json.dumps(payload, indent=2, sort_keys=True)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(rendered + "\n")
    print(rendered)


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json

from QueryLake.canon.runtime import build_authority_control_readiness_bundle


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Canon++ authority/control readiness bundle.")
    parser.add_argument("--profile", required=True)
    parser.add_argument("--route", action="append", dest="routes", required=True)
    parser.add_argument("--package-registry", required=True)
    parser.add_argument("--pointer-registry", required=True)
    parser.add_argument("--mode", default="shadow")
    parser.add_argument("--output")
    args = parser.parse_args()

    payload = build_authority_control_readiness_bundle(
        profile_id=args.profile,
        routes=args.routes,
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

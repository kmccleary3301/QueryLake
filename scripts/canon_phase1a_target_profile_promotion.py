from __future__ import annotations

import argparse
import json

from QueryLake.canon.control.target_profile_promotion import build_target_profile_promotion_bundle


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Canon++ target-profile promotion bundle.")
    parser.add_argument("--target-profile", required=True)
    parser.add_argument("--shadow-artifact-dir", required=True)
    parser.add_argument("--package-registry", required=True)
    parser.add_argument("--pointer-registry", required=True)
    parser.add_argument("--metadata-store-path")
    parser.add_argument("--route", action="append", dest="routes", required=True)
    parser.add_argument("--mode", default="shadow")
    parser.add_argument("--output")
    args = parser.parse_args()

    payload = build_target_profile_promotion_bundle(
        target_profile_id=args.target_profile,
        routes=args.routes,
        shadow_artifact_dir=args.shadow_artifact_dir,
        package_registry_path=args.package_registry,
        pointer_registry_path=args.pointer_registry,
        metadata_store_path=args.metadata_store_path,
        package_selection_mode=args.mode,
    )
    rendered = json.dumps(payload, indent=2, sort_keys=True)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(rendered + "\n")
    print(rendered)


if __name__ == "__main__":
    main()

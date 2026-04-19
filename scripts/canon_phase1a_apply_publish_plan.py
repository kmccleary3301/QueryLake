#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from QueryLake.canon.control import apply_publish_plan


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply a Canon++ publish plan to a local pointer registry.")
    parser.add_argument("--publish-plan", required=True)
    parser.add_argument("--registry-path", required=True)
    parser.add_argument("--authority-control-registry")
    args = parser.parse_args()

    plan = json.loads(Path(args.publish_plan).read_text(encoding="utf-8"))
    registry = apply_publish_plan(
        plan=plan,
        registry_path=args.registry_path,
        authority_control_registry_path=args.authority_control_registry,
    )
    print(
        json.dumps(
            {
                "registry_path": args.registry_path,
                "shadow_pointer": registry.get("shadow_pointer", {}).get("pointer_id") if registry.get("shadow_pointer") else None,
                "candidate_primary_pointer": registry.get("candidate_primary_pointer", {}).get("pointer_id")
                if registry.get("candidate_primary_pointer")
                else None,
                "primary_pointer": registry.get("primary_pointer", {}).get("pointer_id") if registry.get("primary_pointer") else None,
                "history_count": len(registry.get("history") or []),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

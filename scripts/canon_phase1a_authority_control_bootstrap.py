#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from QueryLake.canon.control import apply_authority_control_bootstrap
from QueryLake.canon.runtime import build_authority_control_bootstrap_bundle


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build and optionally apply a bounded Canon++ authority/control bootstrap."
    )
    parser.add_argument("--profile", required=True)
    parser.add_argument("--route", action="append", dest="routes", required=True)
    parser.add_argument("--package-registry", required=True)
    parser.add_argument("--pointer-registry", required=True)
    parser.add_argument("--authority-control-registry")
    parser.add_argument("--metadata-store-path", default=None)
    parser.add_argument("--mode", default="shadow")
    parser.add_argument("--execute-bootstrap", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    payload = build_authority_control_bootstrap_bundle(
        profile_id=args.profile,
        routes=args.routes,
        package_registry_path=args.package_registry,
        pointer_registry_path=args.pointer_registry,
        metadata_store_path=args.metadata_store_path,
        mode=args.mode,
        execute_bootstrap=bool(args.execute_bootstrap),
    )
    if args.apply:
        if not args.authority_control_registry:
            raise SystemExit("--authority-control-registry is required with --apply")
        registry = apply_authority_control_bootstrap(
            bundle=payload,
            registry_path=args.authority_control_registry,
        )
        payload["applied_registry_summary"] = {
            "entry_count": len(dict(registry.get("entries") or {})),
            "history_count": len(list(registry.get("history") or [])),
        }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(output),
                "candidate_primary_bootstrap_ready": bool(
                    dict(payload.get("summary") or {}).get("candidate_primary_bootstrap_ready")
                ),
                "applied": bool(args.apply),
                "recommendations": list(payload.get("recommendations") or []),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

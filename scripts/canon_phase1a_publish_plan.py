#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from QueryLake.canon.control import (
    CanonPublishPointer,
    CanonPublishRequest,
    CanonPublishReview,
    build_publish_plan,
)


def _load_json(path: str | None):
    if not path:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a bounded Canon++ publish/cutover plan.")
    parser.add_argument("--exit-readiness-bundle", required=True)
    parser.add_argument("--target-pointer-id", required=True)
    parser.add_argument("--graph-id", required=True)
    parser.add_argument("--package-revision", required=True)
    parser.add_argument("--profile-id", required=True)
    parser.add_argument("--route-id", action="append", dest="route_ids", default=[])
    parser.add_argument("--mode", choices=["shadow", "candidate_primary", "primary"], required=True)
    parser.add_argument("--current-pointer-json", default=None)
    parser.add_argument("--branch-name", required=True)
    parser.add_argument("--reviewed", action="store_true")
    parser.add_argument("--ci-green", action="store_true")
    parser.add_argument("--shadow-evidence-present", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    current = _load_json(args.current_pointer_json)
    request = CanonPublishRequest(
        target=CanonPublishPointer(
            pointer_id=args.target_pointer_id,
            graph_id=args.graph_id,
            package_revision=args.package_revision,
            profile_id=args.profile_id,
            route_ids=list(args.route_ids or []),
            mode=args.mode,
        ),
        current=CanonPublishPointer.model_validate(current) if current is not None else None,
        review=CanonPublishReview(
            branch_name=args.branch_name,
            reviewed=bool(args.reviewed),
            ci_green=bool(args.ci_green),
            shadow_evidence_present=bool(args.shadow_evidence_present),
        ),
        exit_readiness=_load_json(args.exit_readiness_bundle) or {},
    )
    payload = build_publish_plan(request)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(output),
                "allowed": bool(payload["allowed"]),
                "mode_transition": payload["mode_transition"],
                "blocker_count": len(payload["blockers"]),
                "recommendations": list(payload["recommendations"] or []),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from QueryLake.canon.runtime import build_phase1a_route_profile_matrix


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Canon++ Phase 1A route/profile shadow matrix.")
    parser.add_argument(
        "--route",
        action="append",
        dest="routes",
        default=None,
        help="Route to include. May be repeated. Defaults to all bounded Phase 1A routes.",
    )
    parser.add_argument(
        "--profile-id",
        action="append",
        dest="profile_ids",
        default=None,
        help="Profile id to include. May be repeated. Defaults to all declared profiles.",
    )
    parser.add_argument("--output", required=True, help="Output JSON path.")
    args = parser.parse_args()

    payload = build_phase1a_route_profile_matrix(
        routes=args.routes,
        profile_ids=args.profile_ids,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(output),
                "row_count": len(payload.get("rows") or []),
                "recommendations": list(payload.get("recommendations") or []),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

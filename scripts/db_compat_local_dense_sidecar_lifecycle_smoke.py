#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.db_compat_local_query_smoke import build_local_query_smoke_payload


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the local dense-sidecar lifecycle transition from cache-cold to process-warmed."
    )
    parser.add_argument("--profile", default="sqlite_fts5_dense_sidecar_local_v1")
    parser.add_argument("--enable-ready-profile-projections", action="store_true")
    parser.add_argument("--projection-metadata-path", default=None)
    parser.add_argument("--output", default=None)
    args = parser.parse_args(argv)

    payload = build_local_query_smoke_payload(
        profile_id=args.profile,
        enable_ready_profile_projections=bool(args.enable_ready_profile_projections),
        metadata_store_path=args.projection_metadata_path,
    )
    lifecycle = dict(payload.get("dense_sidecar_lifecycle_transition") or {})
    before = dict(lifecycle.get("before") or {})
    after = dict(lifecycle.get("after") or {})

    gate_ok = bool(lifecycle.get("cache_warmup_transition_ok"))
    gate_ok = gate_ok and str(before.get("lifecycle_state") or "") == "ready_projection_backed_cache_cold"
    gate_ok = gate_ok and str(before.get("cache_lifecycle_state") or "") == "cache_cold_rebuildable"
    gate_ok = gate_ok and str(after.get("lifecycle_state") or "") == "ready_cache_warmed"
    gate_ok = gate_ok and str(after.get("cache_lifecycle_state") or "") == "cache_warmed_process_local"
    gate_ok = gate_ok and str(after.get("ready_state_source") or "") == "process_local_cache"

    result: Dict[str, Any] = {
        "profile": str(payload.get("profile") or ""),
        "metadata_store_path": payload.get("metadata_store_path"),
        "dense_sidecar_lifecycle_transition": lifecycle,
        "gate_ok": bool(gate_ok),
    }
    rendered = json.dumps(result, indent=2)
    print(rendered)
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    return 0 if gate_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())

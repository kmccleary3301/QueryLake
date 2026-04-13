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

from QueryLake.runtime.db_compat import DEPLOYMENT_PROFILES
from QueryLake.runtime.local_profile_v2 import build_local_profile_scope_expansion_contract_payload
from scripts.db_compat_local_embedded_supported_slice_gate import main as local_embedded_supported_slice_main
from scripts.db_compat_program_completion_gate import main as db_compat_program_completion_main
from scripts.db_compat_v2_runtime_boundary_status import build_v2_runtime_boundary_payload
from scripts.db_compat_v2_runtime_consistency import main as v2_runtime_consistency_main


def _run_gate(fn, argv: List[str]) -> None:
    if fn(argv) != 0:
        raise SystemExit(2)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Final completion gate for the QueryLake Primitive/Representation V2 program."
    )
    parser.add_argument("--output", default=None)
    args = parser.parse_args(argv)

    _run_gate(
        db_compat_program_completion_main,
        ["--output", "/tmp/querylake_db_compat_program_completion_gate_for_v2.json"],
    )
    _run_gate(
        local_embedded_supported_slice_main,
        [
            "--enable-ready-profile-projections",
            "--output",
            "/tmp/querylake_db_compat_local_embedded_supported_slice_gate_for_v2.json",
        ],
    )
    _run_gate(
        v2_runtime_consistency_main,
        ["--output", "/tmp/querylake_db_compat_v2_runtime_consistency_for_v2_gate.json"],
    )

    runtime_boundary = build_v2_runtime_boundary_payload()
    scope_expansion_contract = build_local_profile_scope_expansion_contract_payload(
        profile=DEPLOYMENT_PROFILES["sqlite_fts5_dense_sidecar_local_v1"]
    )

    payload: Dict[str, Any] = {
        "program_complete": True,
        "program_id": "querylake_primitives_representation_v2",
        "runtime_boundary": runtime_boundary,
        "embedded_scope_contract": scope_expansion_contract,
        "validated_profiles": [
            "paradedb_postgres_gold_v1",
            "aws_aurora_pg_opensearch_v1",
            "sqlite_fts5_dense_sidecar_local_v1",
        ],
        "notes": {
            "embedded_supported_slice_complete": True,
            "wider_embedded_scope_required_for_completion": False,
            "future_scope_docs_ref": "docs/database/V2_FUTURE_SCOPE.md",
            "completion_gate_docs_ref": "docs/database/V2_PROGRAM_COMPLETION_GATE.md",
            "implementation_report_docs_ref": "docs/database/V2_IMPLEMENTATION_REPORT.md",
        },
    }
    rendered = json.dumps(payload, indent=2)
    print(rendered)
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

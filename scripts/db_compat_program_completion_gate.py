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

from QueryLake.runtime.db_compat import build_supported_profiles_manifest_payload
from scripts.db_compat_first_split_stack_completion_gate import main as first_split_stack_main


def _profiles_by_id(payload: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        str(entry["id"]): dict(entry)
        for entry in list(payload.get("profiles") or [])
        if isinstance(entry, dict) and entry.get("id") is not None
    }


def _assert_supported_profile_contract(payload: Dict[str, Any]) -> None:
    profiles = _profiles_by_id(payload)
    required_profiles = {
        "paradedb_postgres_gold_v1",
        "postgres_pgvector_light_v1",
        "aws_aurora_pg_opensearch_v1",
    }
    if not required_profiles.issubset(set(profiles)):
        raise SystemExit(2)

    gold = profiles["paradedb_postgres_gold_v1"]
    if not (gold.get("implemented") is True and gold.get("recommended") is True and gold.get("maturity") == "gold"):
        raise SystemExit(2)
    if gold["routes"]["search_bm25.document_chunk"]["declared_state"] != "supported":
        raise SystemExit(2)
    if gold["routes"]["search_file_chunks"]["declared_state"] != "supported":
        raise SystemExit(2)
    if gold["routes"]["search_hybrid.document_chunk"]["declared_state"] != "supported":
        raise SystemExit(2)

    light = profiles["postgres_pgvector_light_v1"]
    if not (light.get("implemented") is True and light.get("maturity") == "limited_executable"):
        raise SystemExit(2)
    if light["routes"]["search_hybrid.document_chunk"]["declared_state"] != "supported":
        raise SystemExit(2)
    if light["routes"]["search_bm25.document_chunk"]["declared_optional"] is not True:
        raise SystemExit(2)
    if light["routes"]["search_file_chunks"]["declared_optional"] is not True:
        raise SystemExit(2)

    aurora = profiles["aws_aurora_pg_opensearch_v1"]
    if not (aurora.get("implemented") is True and aurora.get("maturity") == "split_stack_executable"):
        raise SystemExit(2)
    if aurora["routes"]["search_bm25.document_chunk"]["declared_executable"] is not True:
        raise SystemExit(2)
    if aurora["routes"]["search_file_chunks"]["declared_executable"] is not True:
        raise SystemExit(2)
    if aurora["routes"]["search_hybrid.document_chunk"]["declared_executable"] is not True:
        raise SystemExit(2)
    if aurora["routes"]["retrieval.sparse.vector"]["declared_optional"] is not True:
        raise SystemExit(2)
    if aurora["routes"]["retrieval.graph.traversal"]["declared_optional"] is not True:
        raise SystemExit(2)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Final completion gate for the QueryLake DB compatibility extension program."
    )
    parser.add_argument("--output", default=None)
    args = parser.parse_args(argv)

    manifest = build_supported_profiles_manifest_payload()
    _assert_supported_profile_contract(manifest)

    split_stack_args = [
        "--profile",
        "aws_aurora_pg_opensearch_v1",
        "--env",
        "QUERYLAKE_SEARCH_BACKEND_URL=https://example-opensearch.local",
        "--env",
        "QUERYLAKE_SEARCH_INDEX_NAMESPACE=querylake",
        "--env",
        "QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS=1024",
        "--enable-ready-split-stack-projections",
        "--expect-boot-ready",
        "true",
        "--expect-configuration-ready",
        "true",
        "--expect-route-runtime-ready",
        "true",
        "--expect-declared-executable-routes-runtime-ready",
        "true",
        "--expect-backend-connectivity-ready",
        "true",
        "--expect-required-projection-count",
        "3",
        "--expect-ready-projection-count",
        "3",
        "--expect-declared-executable-route-ids",
        "search_bm25.document_chunk,search_file_chunks,search_hybrid.document_chunk",
        "--expect-lexical-degraded-route-ids",
        "search_bm25.document_chunk,search_file_chunks,search_hybrid.document_chunk",
        "--expect-lexical-gold-recommended-route-ids",
        "search_bm25.document_chunk,search_file_chunks,search_hybrid.document_chunk",
    ]
    if first_split_stack_main(split_stack_args) != 0:
        raise SystemExit(2)

    payload = {
        "program_complete": True,
        "supported_profiles_manifest": manifest,
        "validated_profiles": [
            "paradedb_postgres_gold_v1",
            "postgres_pgvector_light_v1",
            "aws_aurora_pg_opensearch_v1",
        ],
        "notes": {
            "current_program_scope_complete": True,
            "future_scope_required_for_completion": False,
            "future_scope_docs_ref": "docs/database/DB_COMPAT_FUTURE_SCOPE.md",
            "completion_gate_docs_ref": "docs/database/DB_COMPAT_COMPLETION_GATE.md",
        },
    }
    rendered = json.dumps(payload, indent=2)
    print(rendered)
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

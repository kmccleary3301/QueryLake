#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.db_compat import DEPLOYMENT_PROFILES


ACTIVE_ROUTE_IDS: tuple[str, ...] = (
    "search_bm25.document_chunk",
    "search_hybrid.document_chunk",
    "search_file_chunks",
)

ACTIVE_PATH: tuple[str, ...] = (
    "route_resolution",
    "query_ir_v2_construction",
    "projection_ir_v2_construction",
    "lexical_capability_enforcement",
    "typed_materialization_target_resolution",
    "retrieval_explain",
    "orchestrated_execution_metadata",
    "route_execution_and_bringup_recovery",
)

CANONICAL_RUNTIME_SURFACES: tuple[str, ...] = (
    "QueryLake/runtime/query_ir_v2.py",
    "QueryLake/runtime/projection_ir_v2.py",
    "QueryLake/runtime/route_planning_v2.py",
    "QueryLake/runtime/retrieval_route_executors.py",
    "QueryLake/runtime/retrieval_explain.py",
    "QueryLake/runtime/retrieval_orchestrator.py",
    "QueryLake/runtime/profile_bringup.py",
    "QueryLake/runtime/local_profile_v2.py",
    "QueryLake/runtime/local_route_execution.py",
    "QueryLake/runtime/local_dense_sidecar.py",
    "QueryLake/api/search.py",
)

CANONICAL_PLANNING_FIELDS: tuple[str, ...] = (
    "route_id",
    "representation_scope_id",
    "strictness_policy",
    "lane_intent.use_dense",
    "lane_intent.use_sparse",
    "projection_ir_v2.required_targets",
    "projection_ir_v2.buildability_class",
    "capability_dependencies",
    "planning_surface",
)

TRANSITIONAL_AREAS: tuple[str, ...] = (
    "deeper_execution_and_refinement_paths_outside_current_supported_route_slices",
    "compatibility_era_storage_internals_behind_typed_materialization_helpers",
    "wider_embedded_slice_routes_and_semantics_not_yet_promoted",
)

DOCS_REFS: tuple[str, ...] = (
    "docs/database/QUERY_IR_V2.md",
    "docs/database/PROJECTION_IR_V2.md",
    "docs/database/LOCAL_PROFILE_V1.md",
    "docs/database/LOCAL_DENSE_SIDECAR_CONTRACT.md",
    "docs/database/LOCAL_PROFILE_SCOPE_EXPANSION_CRITERIA.md",
    "docs/database/V2_RUNTIME_BOUNDARY.md",
)


def build_v2_runtime_boundary_payload() -> Dict[str, Any]:
    active_profile_ids = (
        "paradedb_postgres_gold_v1",
        "aws_aurora_pg_opensearch_v1",
        "sqlite_fts5_dense_sidecar_local_v1",
    )
    active_profiles: List[Dict[str, str]] = []
    for profile_id in active_profile_ids:
        profile = DEPLOYMENT_PROFILES[profile_id]
        active_profiles.append(
            {
                "profile_id": profile.id,
                "maturity": profile.maturity,
            }
        )
    return {
        "contract_version": "v1",
        "active_profiles": active_profiles,
        "active_route_ids": list(ACTIVE_ROUTE_IDS),
        "active_path": list(ACTIVE_PATH),
        "canonical_runtime_surfaces": list(CANONICAL_RUNTIME_SURFACES),
        "canonical_planning_fields": list(CANONICAL_PLANNING_FIELDS),
        "transitional_areas": list(TRANSITIONAL_AREAS),
        "validated_by": [
            "scripts/db_compat_v2_runtime_consistency.py",
            "scripts/ci_db_compat_v2_runtime_boundary_sync.py",
        ],
        "docs_refs": list(DOCS_REFS),
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render the canonical V2 runtime-boundary payload.")
    parser.add_argument("--output", default=None)
    args = parser.parse_args(list(argv) if argv is not None else None)

    payload = build_v2_runtime_boundary_payload()
    rendered = json.dumps(payload, indent=2, sort_keys=True)
    print(rendered)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

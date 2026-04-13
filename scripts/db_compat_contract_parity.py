#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from typing import Any, Dict, List, Mapping, Optional

from QueryLake.runtime.db_compat import DEPLOYMENT_PROFILES, DeploymentProfile, build_profile_diagnostics_payload
from QueryLake.runtime.lexical_capability_planner import build_lexical_query_capability_plan
from QueryLake.runtime.projection_refresh import mark_projection_build_ready
from QueryLake.runtime.retrieval_route_executors import (
    resolve_search_bm25_route_executor,
    resolve_search_file_chunks_route_executor,
    resolve_search_hybrid_route_executor,
)


def load_cases(path: Path) -> List[Dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("cases-json must be a JSON list")
    return [entry for entry in payload if isinstance(entry, dict)]


def _route_resolution(case: Mapping[str, Any], *, profile: DeploymentProfile) -> Dict[str, Any]:
    route = str(case.get("route", "")).strip()
    if route == "search_bm25":
        table = str(case.get("table", "document_chunk") or "document_chunk")
        return resolve_search_bm25_route_executor(table=table, profile=profile).to_payload()
    if route == "search_hybrid":
        return resolve_search_hybrid_route_executor(
            use_bm25=bool(case.get("use_bm25", True)),
            use_similarity=bool(case.get("use_similarity", True)),
            use_sparse=bool(case.get("use_sparse", False)),
            profile=profile,
        ).to_payload()
    if route == "search_file_chunks":
        return resolve_search_file_chunks_route_executor(profile=profile).to_payload()
    raise ValueError(f"Unsupported route in parity case: {route}")


def _lexical_plan(case: Mapping[str, Any], *, profile: DeploymentProfile) -> Dict[str, Any]:
    query = str(case.get("query", "") or "")
    if len(query) == 0:
        return {
            "query_features": [],
            "capability_states": {},
            "degraded_capabilities": [],
            "unsupported_capabilities": [],
        }
    plan = build_lexical_query_capability_plan(query, profile=profile)
    return {
        "query_features": list(plan.query_features),
        "capability_states": dict(plan.capability_states),
        "degraded_capabilities": list(plan.degraded_capabilities),
        "unsupported_capabilities": list(plan.unsupported_capabilities),
    }


def _route_diagnostics(
    *,
    profile: DeploymentProfile,
    metadata_store_path: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    payload = build_profile_diagnostics_payload(profile=profile, metadata_store_path=metadata_store_path)
    return {
        str(entry.get("route_id")): dict(entry)
        for entry in list(payload.get("route_executors") or [])
        if isinstance(entry, dict) and isinstance(entry.get("route_id"), str)
    }


def _projection_metadata_fixture_path(
    *,
    profiles: List[DeploymentProfile],
    enable_ready_split_stack: bool,
) -> Optional[str]:
    if not enable_ready_split_stack:
        return None
    if not any(profile.id == "aws_aurora_pg_opensearch_v1" for profile in profiles):
        return None

    tmp = tempfile.NamedTemporaryFile(
        prefix="querylake_db_compat_parity_projection_meta_",
        suffix=".json",
        delete=False,
    )
    tmp.close()
    metadata_path = tmp.name
    Path(metadata_path).write_text("{}", encoding="utf-8")
    for projection_id, lane_family, revision in [
        ("document_chunk_lexical_projection_v1", "lexical", "parity:lexical"),
        ("document_chunk_dense_projection_v1", "dense", "parity:dense"),
        ("file_chunk_lexical_projection_v1", "lexical", "parity:file"),
    ]:
        mark_projection_build_ready(
            projection_id=projection_id,
            projection_version="v1",
            profile_id="aws_aurora_pg_opensearch_v1",
            lane_family=lane_family,
            target_backend="opensearch",
            build_revision=revision,
            path=metadata_path,
        )
    return metadata_path


def evaluate_cases(
    *,
    cases: List[Dict[str, Any]],
    profiles: List[DeploymentProfile],
    metadata_store_path: Optional[str] = None,
) -> Dict[str, Any]:
    per_case: List[Dict[str, Any]] = []
    gold_executable = 0
    split_executable = 0
    gold_runtime_ready = 0
    split_runtime_ready = 0
    executable_overlap = 0
    runtime_ready_overlap = 0
    degraded_case_count = 0
    unsupported_case_count = 0
    profile_route_diagnostics = {
        profile.id: _route_diagnostics(profile=profile, metadata_store_path=metadata_store_path)
        for profile in profiles
    }

    for case in cases:
        case_result: Dict[str, Any] = {
            "case_id": str(case.get("case_id", "")),
            "route": str(case.get("route", "")),
            "query": str(case.get("query", "") or ""),
            "profiles": {},
        }
        executable_profiles: List[str] = []
        any_degraded = False
        any_unsupported = False
        for profile in profiles:
            route_resolution = _route_resolution(case, profile=profile)
            lexical_plan = _lexical_plan(case, profile=profile)
            route_diag = dict(
                profile_route_diagnostics.get(profile.id, {}).get(route_resolution.get("route_id", ""), {})
            )
            case_result["profiles"][profile.id] = {
                "route_resolution": route_resolution,
                "lexical_plan": lexical_plan,
                "route_diagnostics": route_diag,
            }
            route_supported_for_case = bool(route_resolution.get("implemented", False)) and len(
                list(lexical_plan.get("unsupported_capabilities") or [])
            ) == 0
            if bool(route_resolution.get("implemented", False)):
                executable_profiles.append(profile.id)
            if bool(route_diag.get("runtime_ready", False)) and route_supported_for_case:
                case_result.setdefault("_runtime_ready_profiles", []).append(profile.id)
            if route_resolution.get("support_state") == "degraded" or len(lexical_plan["degraded_capabilities"]) > 0:
                any_degraded = True
            if route_resolution.get("support_state") == "unsupported" or len(lexical_plan["unsupported_capabilities"]) > 0:
                any_unsupported = True

        gold_ok = "paradedb_postgres_gold_v1" in executable_profiles
        split_ok = "aws_aurora_pg_opensearch_v1" in executable_profiles
        runtime_ready_profiles = list(case_result.pop("_runtime_ready_profiles", []))
        gold_runtime_ok = "paradedb_postgres_gold_v1" in runtime_ready_profiles
        split_runtime_ok = "aws_aurora_pg_opensearch_v1" in runtime_ready_profiles
        gold_executable += int(gold_ok)
        split_executable += int(split_ok)
        gold_runtime_ready += int(gold_runtime_ok)
        split_runtime_ready += int(split_runtime_ok)
        executable_overlap += int(gold_ok and split_ok)
        runtime_ready_overlap += int(gold_runtime_ok and split_runtime_ok)
        degraded_case_count += int(any_degraded)
        unsupported_case_count += int(any_unsupported)
        case_result["summary"] = {
            "executable_profiles": executable_profiles,
            "runtime_ready_profiles": runtime_ready_profiles,
            "gold_executable": gold_ok,
            "split_executable": split_ok,
            "gold_runtime_ready": gold_runtime_ok,
            "split_runtime_ready": split_runtime_ok,
            "support_delta": {
                "gold": case_result["profiles"].get("paradedb_postgres_gold_v1", {}).get("route_resolution", {}).get("support_state"),
                "split": case_result["profiles"].get("aws_aurora_pg_opensearch_v1", {}).get("route_resolution", {}).get("support_state"),
            },
        }
        per_case.append(case_result)

    case_count = len(cases)
    return {
        "profiles": [profile.id for profile in profiles],
        "metrics": {
            "case_count": case_count,
            "gold_executable_count": gold_executable,
            "split_executable_count": split_executable,
            "gold_runtime_ready_count": gold_runtime_ready,
            "split_runtime_ready_count": split_runtime_ready,
            "executable_overlap_count": executable_overlap,
            "runtime_ready_overlap_count": runtime_ready_overlap,
            "split_executable_ratio": 0.0 if case_count == 0 else split_executable / float(case_count),
            "split_runtime_ready_ratio": 0.0 if case_count == 0 else split_runtime_ready / float(case_count),
            "executable_overlap_ratio": 0.0 if case_count == 0 else executable_overlap / float(case_count),
            "runtime_ready_overlap_ratio": 0.0 if case_count == 0 else runtime_ready_overlap / float(case_count),
            "degraded_case_count": degraded_case_count,
            "unsupported_case_count": unsupported_case_count,
        },
        "cases": per_case,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Fixture-driven DB compatibility contract parity harness.")
    parser.add_argument("--cases-json", required=True)
    parser.add_argument("--profiles", nargs="+", default=["paradedb_postgres_gold_v1", "aws_aurora_pg_opensearch_v1"])
    parser.add_argument("--output", default=None)
    parser.add_argument("--min-split-executable-ratio", type=float, default=0.0)
    parser.add_argument("--min-split-runtime-ready-ratio", type=float, default=0.0)
    parser.add_argument("--min-overlap-ratio", type=float, default=0.0)
    parser.add_argument("--min-runtime-ready-overlap-ratio", type=float, default=0.0)
    parser.add_argument("--enable-ready-split-stack-projections", action="store_true")
    args = parser.parse_args()

    profiles: List[DeploymentProfile] = []
    for profile_id in args.profiles:
        if profile_id not in DEPLOYMENT_PROFILES:
            raise ValueError(f"Unknown profile id: {profile_id}")
        profiles.append(DEPLOYMENT_PROFILES[profile_id])

    metadata_store_path = _projection_metadata_fixture_path(
        profiles=profiles,
        enable_ready_split_stack=bool(args.enable_ready_split_stack_projections),
    )
    payload = evaluate_cases(
        cases=load_cases(Path(args.cases_json)),
        profiles=profiles,
        metadata_store_path=metadata_store_path,
    )
    payload["metadata"] = {
        "projection_metadata_path": metadata_store_path,
        "ready_split_stack_projections": bool(args.enable_ready_split_stack_projections),
    }
    print(json.dumps(payload, indent=2))
    if args.output:
        Path(args.output).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    metrics = payload["metrics"]
    if float(metrics["split_executable_ratio"]) < float(args.min_split_executable_ratio):
        return 2
    if float(metrics["split_runtime_ready_ratio"]) < float(args.min_split_runtime_ready_ratio):
        return 2
    if float(metrics["executable_overlap_ratio"]) < float(args.min_overlap_ratio):
        return 2
    if float(metrics["runtime_ready_overlap_ratio"]) < float(args.min_runtime_ready_overlap_ratio):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

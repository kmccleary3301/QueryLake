#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SDK_SRC = ROOT / "sdk/python/src"
if str(SDK_SRC) not in sys.path:
    sys.path.insert(0, str(SDK_SRC))

from QueryLake.runtime.db_compat import DEPLOYMENT_PROFILES, build_profile_diagnostics_payload
from QueryLake.runtime.profile_bringup import build_profile_bringup_payload
from querylake_sdk.models import parse_profile_bringup_summary, parse_profile_diagnostics_summary
from scripts.db_compat_local_query_smoke import build_local_query_smoke_payload
from scripts.db_compat_profile_smoke import (
    _parse_env_pairs,
    _prepare_ready_profile_projection_metadata,
    temporary_env,
)


def _index_by(rows: List[dict], key: str) -> Dict[str, dict]:
    return {
        str(row.get(key) or ""): dict(row)
        for row in rows
        if isinstance(row, dict) and str(row.get(key) or "")
    }


def _scope_id(row: dict) -> str:
    if not isinstance(row, dict):
        return ""
    direct = str(row.get("representation_scope_id") or "")
    if direct:
        return direct
    nested = dict(row.get("representation_scope") or {})
    return str(nested.get("scope_id") or "")


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Assert that the local profile surfaces agree on the declared V2 route/projection contract."
    )
    parser.add_argument("--profile", default="sqlite_fts5_dense_sidecar_local_v1")
    parser.add_argument("--env", action="append", default=[])
    parser.add_argument("--projection-metadata-path", default=None)
    parser.add_argument("--enable-ready-profile-projections", action="store_true")
    parser.add_argument("--output", default=None)
    args = parser.parse_args(argv)

    if args.profile not in DEPLOYMENT_PROFILES:
        raise ValueError(f"Unknown profile id: {args.profile}")
    if args.enable_ready_profile_projections and args.projection_metadata_path:
        raise ValueError(
            "--enable-ready-profile-projections cannot be combined with --projection-metadata-path."
        )

    metadata_store_path = args.projection_metadata_path
    if args.enable_ready_profile_projections:
        metadata_store_path = _prepare_ready_profile_projection_metadata(args.profile)

    env_map = {"QUERYLAKE_DB_PROFILE": args.profile, **_parse_env_pairs(list(args.env or []))}
    with temporary_env(env_map):
        diagnostics = build_profile_diagnostics_payload(
            profile=DEPLOYMENT_PROFILES[args.profile],
            metadata_store_path=metadata_store_path,
        )
        bringup = build_profile_bringup_payload(
            profile=DEPLOYMENT_PROFILES[args.profile],
            metadata_store_path=metadata_store_path,
        )
        query_smoke = build_local_query_smoke_payload(
            profile_id=args.profile,
            metadata_store_path=metadata_store_path,
        )

    local = dict(bringup.get("local_profile") or {})
    promotion = dict(local.get("promotion_status") or {})
    scope_expansion_contract = dict(local.get("scope_expansion_contract") or {})
    scope_expansion_status = dict(local.get("scope_expansion_status") or {})
    dense_sidecar = dict(local.get("dense_sidecar") or {})
    support_matrix = _index_by(list(local.get("support_matrix") or []), "route_id")
    route_contracts = _index_by(list(local.get("route_runtime_contracts") or []), "route_id")
    route_recovery = _index_by(list(bringup.get("route_recovery") or []), "route_id")
    route_support_v2_diagnostics = _index_by(list(diagnostics.get("route_support_v2") or []), "route_id")
    route_support_v2 = _index_by(list(bringup.get("route_support_v2") or []), "route_id")
    projection_registry = _index_by(list(local.get("projection_plan_v2_registry") or []), "projection_id")
    query_smoke_cases = _index_by(list(query_smoke.get("cases") or []), "case_id")
    query_smoke_summary = dict(query_smoke.get("summary") or {})
    diagnostics_summary = parse_profile_diagnostics_summary(diagnostics)
    bringup_summary = parse_profile_bringup_summary(bringup)

    declared_executable_route_ids = sorted(
        route_id for route_id, row in support_matrix.items() if bool(row.get("declared_executable"))
    )
    if declared_executable_route_ids != sorted(list(promotion.get("declared_executable_route_ids") or [])):
        raise SystemExit(2)
    if declared_executable_route_ids != sorted(bringup_summary.local_declared_executable_route_ids()):
        raise SystemExit(2)
    if bool(dense_sidecar.get("ready")) != bool(diagnostics_summary.local_dense_sidecar_ready()):
        raise SystemExit(2)
    if bool(dense_sidecar.get("ready")) != bool(bringup_summary.local_dense_sidecar_ready()):
        raise SystemExit(2)
    if bool(scope_expansion_status.get("dense_sidecar_warmup_recommended")) != bool(
        dense_sidecar.get("warmup_recommended")
    ):
        raise SystemExit(2)
    if bool(scope_expansion_status.get("dense_sidecar_warmup_required_for_peak_performance")) != bool(
        dense_sidecar.get("warmup_required_for_peak_performance")
    ):
        raise SystemExit(2)
    if str(scope_expansion_status.get("dense_sidecar_lifecycle_recovery_mode") or "") != str(
        dense_sidecar.get("lifecycle_recovery_mode") or ""
    ):
        raise SystemExit(2)
    if list(scope_expansion_status.get("dense_sidecar_lifecycle_recovery_hints") or []) != list(
        dense_sidecar.get("lifecycle_recovery_hints") or []
    ):
        raise SystemExit(2)

    for route_id in declared_executable_route_ids:
        support_row = support_matrix.get(route_id) or {}
        contract = route_contracts.get(route_id)
        recovery = route_recovery.get(route_id)
        manifest = route_support_v2.get(route_id)
        manifest_diagnostics = route_support_v2_diagnostics.get(route_id)
        if contract is None or recovery is None or manifest is None or manifest_diagnostics is None:
            raise SystemExit(2)
        if _scope_id(manifest_diagnostics) != _scope_id(manifest):
            raise SystemExit(2)
        if _scope_id(support_row) != _scope_id(manifest):
            raise SystemExit(2)
        if _scope_id(support_row) != _scope_id(contract):
            raise SystemExit(2)
        if _scope_id(contract) != _scope_id(recovery):
            raise SystemExit(2)
        if bool(support_row.get("declared_executable")) != bool(manifest.get("declared_executable")):
            raise SystemExit(2)
        if bool(support_row.get("declared_executable")) != bool(manifest_diagnostics.get("declared_executable")):
            raise SystemExit(2)
        if list(manifest_diagnostics.get("capability_dependencies") or []) != list(
            manifest.get("capability_dependencies") or []
        ):
            raise SystemExit(2)
        if list(support_row.get("capability_dependencies") or []) != list(manifest.get("capability_dependencies") or []):
            raise SystemExit(2)
        if list(contract.get("capability_dependencies") or []) != list(manifest.get("capability_dependencies") or []):
            raise SystemExit(2)
        planning_v2 = dict(recovery.get("planning_v2") or {})
        query_ir_v2_template = dict(planning_v2.get("query_ir_v2_template") or {})
        projection_ir_v2 = dict(planning_v2.get("projection_ir_v2") or {})
        if str(query_ir_v2_template.get("route_id") or "") != route_id:
            raise SystemExit(2)
        if str(query_ir_v2_template.get("representation_scope_id") or "") != _scope_id(contract):
            raise SystemExit(2)
        if str(projection_ir_v2.get("representation_scope_id") or "") != _scope_id(contract):
            raise SystemExit(2)
        if _index_by(list(projection_ir_v2.get("required_targets") or []), "target_id").keys() != set(
            str(value) for value in list(contract.get("required_projection_ids") or [])
        ):
            raise SystemExit(2)
        if diagnostics_summary.local_route_representation_scope_id(route_id) != _scope_id(contract):
            raise SystemExit(2)
        if bringup_summary.local_route_representation_scope_id(route_id) != _scope_id(contract):
            raise SystemExit(2)
        if diagnostics_summary.local_route_capability_dependencies(route_id) != list(
            contract.get("capability_dependencies") or []
        ):
            raise SystemExit(2)
        if bringup_summary.local_route_capability_dependencies(route_id) != list(
            contract.get("capability_dependencies") or []
        ):
            raise SystemExit(2)
        if diagnostics_summary.local_route_required_projection_ids(route_id) != list(
            contract.get("required_projection_ids") or []
        ):
            raise SystemExit(2)
        if bringup_summary.local_route_required_projection_ids(route_id) != list(
            contract.get("required_projection_ids") or []
        ):
            raise SystemExit(2)
        if diagnostics_summary.local_route_lexical_support_class(route_id) != str(
            contract.get("lexical_support_class") or ""
        ):
            raise SystemExit(2)
        if bringup_summary.local_route_lexical_support_class(route_id) != str(
            contract.get("lexical_support_class") or ""
        ):
            raise SystemExit(2)
        smoke_case_id = {
            "search_bm25.document_chunk": "bm25_simple",
            "search_hybrid.document_chunk": "hybrid_dense_lexical",
            "search_file_chunks": "file_chunk_simple",
        }.get(route_id)
        if smoke_case_id:
            smoke_case = query_smoke_cases.get(smoke_case_id) or {}
            if str(smoke_case.get("lexical_support_class") or "") != str(contract.get("lexical_support_class") or ""):
                raise SystemExit(2)
        if diagnostics_summary.local_route_declared_executable(route_id) is not True:
            raise SystemExit(2)
        if bringup_summary.local_route_declared_executable(route_id) is not True:
            raise SystemExit(2)
        if diagnostics_summary.local_route_runtime_ready(route_id) != bool(contract.get("runtime_ready")):
            raise SystemExit(2)
        if bringup_summary.local_route_runtime_ready(route_id) != bool(contract.get("runtime_ready")):
            raise SystemExit(2)
        if diagnostics_summary.local_route_requires_dense_sidecar(route_id) != bool(
            contract.get("dense_sidecar_required")
        ):
            raise SystemExit(2)
        if bringup_summary.local_route_requires_dense_sidecar(route_id) != bool(
            contract.get("dense_sidecar_required")
        ):
            raise SystemExit(2)
        if diagnostics_summary.local_route_dense_sidecar_ready(route_id) != bool(contract.get("dense_sidecar_ready")):
            raise SystemExit(2)
        if bringup_summary.local_route_dense_sidecar_ready(route_id) != bool(contract.get("dense_sidecar_ready")):
            raise SystemExit(2)
        if diagnostics_summary.local_route_dense_sidecar_cache_warmed(route_id) != bool(
            contract.get("dense_sidecar_cache_warmed")
        ):
            raise SystemExit(2)
        if bringup_summary.local_route_dense_sidecar_cache_warmed(route_id) != bool(
            contract.get("dense_sidecar_cache_warmed")
        ):
            raise SystemExit(2)
        if diagnostics_summary.local_route_dense_sidecar_indexed_record_count(route_id) != int(
            contract.get("dense_sidecar_indexed_record_count") or 0
        ):
            raise SystemExit(2)
        if bringup_summary.local_route_dense_sidecar_indexed_record_count(route_id) != int(
            contract.get("dense_sidecar_indexed_record_count") or 0
        ):
            raise SystemExit(2)
        if bool(contract.get("dense_sidecar_warmup_recommended")) != bool(
            dense_sidecar.get("warmup_recommended")
        ) and bool(contract.get("dense_sidecar_required")):
            raise SystemExit(2)
        if bool(contract.get("dense_sidecar_warmup_required_for_peak_performance")) != bool(
            dense_sidecar.get("warmup_required_for_peak_performance")
        ) and bool(contract.get("dense_sidecar_required")):
            raise SystemExit(2)
        if str(contract.get("dense_sidecar_lifecycle_recovery_mode") or "") != str(
            dense_sidecar.get("lifecycle_recovery_mode") or ""
        ) and bool(contract.get("dense_sidecar_required")):
            raise SystemExit(2)

    required_projection_ids = sorted(list(promotion.get("required_projection_ids") or []))
    if required_projection_ids != sorted(projection_registry.keys()):
        raise SystemExit(2)
    if required_projection_ids != sorted(bringup_summary.local_required_projection_ids()):
        raise SystemExit(2)
    if sorted(list(promotion.get("representation_scope_ids") or [])) != sorted(
        bringup_summary.local_representation_scope_ids()
    ):
        raise SystemExit(2)

    if bool(promotion.get("dense_sidecar_ready")) != bool(dense_sidecar.get("ready")):
        raise SystemExit(2)
    if str(scope_expansion_contract.get("profile_id") or "") != args.profile:
        raise SystemExit(2)
    if str(scope_expansion_contract.get("docs_ref") or "") != "docs/database/LOCAL_PROFILE_SCOPE_EXPANSION_CRITERIA.md":
        raise SystemExit(2)
    if str(scope_expansion_contract.get("dense_sidecar_contract_version") or "") != str(
        dict(dense_sidecar.get("contract") or {}).get("storage_contract_version") or ""
    ):
        raise SystemExit(2)
    if str(scope_expansion_contract.get("dense_sidecar_lifecycle_contract_version") or "") != str(
        dict(dense_sidecar.get("contract") or {}).get("lifecycle_contract_version") or ""
    ):
        raise SystemExit(2)
    if sorted(list(scope_expansion_contract.get("declared_executable_route_ids") or [])) != declared_executable_route_ids:
        raise SystemExit(2)
    if bool(scope_expansion_status.get("current_supported_slice_frozen")) != bool(
        scope_expansion_contract.get("current_supported_slice_frozen")
    ):
        raise SystemExit(2)
    if str(bringup_summary.local_scope_expansion_contract_version() or "") != str(
        scope_expansion_contract.get("dense_sidecar_contract_version") or ""
    ):
        raise SystemExit(2)
    if str(bringup_summary.local_scope_expansion_lifecycle_contract_version() or "") != str(
        scope_expansion_contract.get("dense_sidecar_lifecycle_contract_version") or ""
    ):
        raise SystemExit(2)
    if str(bringup_summary.local_scope_expansion_lifecycle_state() or "") != str(
        scope_expansion_status.get("dense_sidecar_lifecycle_state") or ""
    ):
        raise SystemExit(2)
    if list(bringup_summary.local_scope_expansion_required_before_widening()) != list(
        scope_expansion_contract.get("required_before_widening") or []
    ):
        raise SystemExit(2)
    if bool(bringup_summary.local_scope_expansion_dense_sidecar_promotion_contract_ready()) != bool(
        scope_expansion_status.get("dense_sidecar_promotion_contract_ready")
    ):
        raise SystemExit(2)
    if not bool(query_smoke_summary.get("all_passed")):
        raise SystemExit(2)

    expected_smoke_routes = {
        "bm25_simple": "search_bm25.document_chunk",
        "bm25_phrase_degraded": "search_bm25.document_chunk",
        "bm25_operator_degraded": "search_bm25.document_chunk",
        "hybrid_dense_lexical": "search_hybrid.document_chunk",
        "file_chunk_simple": "search_file_chunks",
        "bm25_hard_constraint_unsupported": "search_bm25.document_chunk",
    }
    for case_id, route_id in expected_smoke_routes.items():
        case = query_smoke_cases.get(case_id)
        if case is None:
            raise SystemExit(2)
        if str(case.get("route_id") or "") != route_id:
            raise SystemExit(2)
        if route_id not in declared_executable_route_ids:
            raise SystemExit(2)
        contract = route_contracts.get(route_id) or {}
        if str(case.get("representation_scope_id") or "") != _scope_id(contract):
            raise SystemExit(2)
        if bool(case.get("dense_sidecar_required")) != bool(contract.get("dense_sidecar_required")):
            raise SystemExit(2)
        if str(case.get("lexical_support_class") or "") != str(contract.get("lexical_support_class") or ""):
            raise SystemExit(2)
        if case_id == "hybrid_dense_lexical" and bool(case.get("dense_sidecar_ready")) != bool(
            contract.get("dense_sidecar_ready")
        ):
            raise SystemExit(2)

    rendered_payload = {
        "profile_id": args.profile,
        "declared_executable_route_ids": declared_executable_route_ids,
        "required_projection_ids": required_projection_ids,
        "dense_sidecar_ready": bool(dense_sidecar.get("ready")),
        "scope_expansion_contract": scope_expansion_contract,
        "scope_expansion_status": scope_expansion_status,
        "query_smoke_passed": bool(query_smoke_summary.get("all_passed")),
        "query_smoke_case_ids": sorted(query_smoke_cases.keys()),
        "representation_scope_ids": sorted(list(promotion.get("representation_scope_ids") or [])),
        "sdk_parse_consistency_ok": True,
        "route_fact_summary": {
            route_id: {
                "representation_scope_id": _scope_id(route_contracts.get(route_id) or {}),
                "required_projection_ids": list((route_contracts.get(route_id) or {}).get("required_projection_ids") or []),
                "capability_dependencies": list((route_contracts.get(route_id) or {}).get("capability_dependencies") or []),
                "lexical_support_class": str((route_contracts.get(route_id) or {}).get("lexical_support_class") or ""),
                "dense_sidecar_required": bool((route_contracts.get(route_id) or {}).get("dense_sidecar_required")),
                "dense_sidecar_ready": bool((route_contracts.get(route_id) or {}).get("dense_sidecar_ready")),
            }
            for route_id in declared_executable_route_ids
        },
        "checked_surfaces": [
            "capabilities.route_support_v2",
            "profile_diagnostics",
            "profile_diagnostics.route_support_v2",
            "profile_diagnostics.sdk_summary",
            "profile_bringup",
            "profile_bringup.route_support_v2",
            "profile_bringup.sdk_summary",
            "local_profile.support_matrix",
            "local_profile.route_runtime_contracts",
            "local_profile.projection_plan_v2_registry",
            "local_profile.promotion_status",
            "local_profile.scope_expansion_contract",
            "local_profile.scope_expansion_status",
            "local_profile.query_smoke",
        ],
        "consistency_ok": True,
    }
    rendered = json.dumps(rendered_payload, indent=2)
    print(rendered)
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

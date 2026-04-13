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

from QueryLake.database.sql_db_tables import DocumentChunk, file_chunk as FileChunkTable
from QueryLake.runtime.db_compat import DEPLOYMENT_PROFILES, QueryLakeUnsupportedFeatureError
from QueryLake.runtime.local_dense_sidecar import LOCAL_DENSE_SIDECAR_ADAPTER
from QueryLake.runtime.profile_bringup import build_profile_bringup_payload
from QueryLake.runtime.retrieval_route_executors import (
    resolve_search_bm25_route_executor,
    resolve_search_file_chunks_route_executor,
    resolve_search_hybrid_route_executor,
)
from scripts.db_compat_profile_smoke import (
    _prepare_ready_profile_projection_metadata,
    temporary_env,
)


LOCAL_PROFILE_ID = "sqlite_fts5_dense_sidecar_local_v1"


class _FixtureSession:
    def __init__(self, rows: Iterable[Any]):
        self._rows = list(rows)

    def exec(self, statement):
        return list(self._rows)


def _document_rows() -> List[DocumentChunk]:
    return [
        DocumentChunk(
            id="chunk_a",
            collection_id="c1",
            document_name="doc-a",
            text="vapor recovery system maintenance",
            embedding=[1.0, 0.0, 0.0],
            md={},
            document_md={},
        ),
        DocumentChunk(
            id="chunk_b",
            collection_id="c1",
            document_name="doc-b",
            text="feedwater chemistry guide",
            embedding=[0.0, 1.0, 0.0],
            md={},
            document_md={},
        ),
    ]


def _file_rows() -> List[FileChunkTable]:
    return [
        FileChunkTable(
            id="file_a",
            file_version_id="fv1",
            text="flue gas analysis procedure",
            md={},
        ),
        FileChunkTable(
            id="file_b",
            file_version_id="fv2",
            text="feedwater handbook",
            md={},
        ),
    ]


def _route_contract_map(bringup_payload: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    local_profile = dict(bringup_payload.get("local_profile") or {})
    return {
        str(entry.get("route_id") or ""): dict(entry)
        for entry in list(local_profile.get("route_runtime_contracts") or [])
        if isinstance(entry, dict) and entry.get("route_id") is not None
    }


def _build_case_payload(
    *,
    case_id: str,
    route_id: str,
    contract: Dict[str, Any],
    top_ids: List[str] | None = None,
    error_payload: Dict[str, Any] | None = None,
    expected_top_id: str | None = None,
    expected_top_ids_contains: List[str] | None = None,
    expected_error_capability: str | None = None,
) -> Dict[str, Any]:
    passed = True
    if expected_top_id is not None:
        passed = bool(top_ids and top_ids[0] == expected_top_id)
    if expected_top_ids_contains is not None:
        observed = set(top_ids or [])
        passed = all(candidate in observed for candidate in expected_top_ids_contains)
    if expected_error_capability is not None:
        passed = str((error_payload or {}).get("capability") or "") == expected_error_capability
    return {
        "case_id": case_id,
        "route_id": route_id,
        "support_state": str(contract.get("support_state") or ""),
        "runtime_ready": bool(contract.get("runtime_ready")),
        "representation_scope_id": str(contract.get("representation_scope_id") or ""),
        "required_projection_ids": list(contract.get("required_projection_ids") or []),
        "dense_sidecar_required": bool(contract.get("dense_sidecar_required")),
        "dense_sidecar_ready": bool(contract.get("dense_sidecar_ready")),
        "lexical_support_class": str(contract.get("lexical_support_class") or ""),
        "query_ir_v2_template": dict(contract.get("query_ir_v2_template") or {}),
        "projection_ir_v2": dict(contract.get("projection_ir_v2") or {}),
        "top_ids": list(top_ids or []),
        "error": dict(error_payload or {}),
        "passed": bool(passed),
    }


def build_local_query_smoke_payload(
    *,
    profile_id: str = LOCAL_PROFILE_ID,
    enable_ready_profile_projections: bool = False,
    metadata_store_path: str | None = None,
) -> Dict[str, Any]:
    if profile_id != LOCAL_PROFILE_ID:
        raise ValueError(f"This smoke harness is only defined for {LOCAL_PROFILE_ID}.")
    if profile_id not in DEPLOYMENT_PROFILES:
        raise ValueError(f"Unknown profile id: {profile_id}")

    effective_metadata_store_path = metadata_store_path
    if enable_ready_profile_projections and effective_metadata_store_path is None:
        effective_metadata_store_path = _prepare_ready_profile_projection_metadata(profile_id)

    LOCAL_DENSE_SIDECAR_ADAPTER.reset()
    with temporary_env({"QUERYLAKE_DB_PROFILE": profile_id}):
        profile = DEPLOYMENT_PROFILES[profile_id]
        bringup_payload = build_profile_bringup_payload(
            profile=profile,
            metadata_store_path=effective_metadata_store_path,
        )
        dense_sidecar_before = dict(
            dict(bringup_payload.get("local_profile") or {}).get("dense_sidecar") or {}
        )
        route_contracts = _route_contract_map(bringup_payload)

        bm25 = resolve_search_bm25_route_executor(table="document_chunk", profile=profile)
        hybrid = resolve_search_hybrid_route_executor(
            use_bm25=True,
            use_similarity=True,
            use_sparse=False,
            profile=profile,
        )
        file_chunks = resolve_search_file_chunks_route_executor(profile=profile)
        bm25.require_executable()
        hybrid.require_executable()
        file_chunks.require_executable()

        cases: List[Dict[str, Any]] = []

        bm25_rows = bm25.executor.execute(
            _FixtureSession(_document_rows()),
            query="vapor recovery",
            table="document_chunk",
            collection_ids=["c1"],
            sort_by="score",
            sort_dir="DESC",
            limit=5,
            offset=0,
        ).rows_or_statement
        cases.append(
            _build_case_payload(
                case_id="bm25_simple",
                route_id="search_bm25.document_chunk",
                contract=route_contracts["search_bm25.document_chunk"],
                top_ids=[str(row[0]) for row in list(bm25_rows or [])],
                expected_top_id="chunk_a",
            )
        )
        bm25_phrase_rows = bm25.executor.execute(
            _FixtureSession(_document_rows()),
            query='"vapor recovery"',
            table="document_chunk",
            collection_ids=["c1"],
            sort_by="score",
            sort_dir="DESC",
            limit=5,
            offset=0,
        ).rows_or_statement
        cases.append(
            _build_case_payload(
                case_id="bm25_phrase_degraded",
                route_id="search_bm25.document_chunk",
                contract=route_contracts["search_bm25.document_chunk"],
                top_ids=[str(row[0]) for row in list(bm25_phrase_rows or [])],
                expected_top_id="chunk_a",
            )
        )
        bm25_operator_rows = bm25.executor.execute(
            _FixtureSession(_document_rows()),
            query="vapor OR chemistry",
            table="document_chunk",
            collection_ids=["c1"],
            sort_by="score",
            sort_dir="DESC",
            limit=5,
            offset=0,
        ).rows_or_statement
        cases.append(
            _build_case_payload(
                case_id="bm25_operator_degraded",
                route_id="search_bm25.document_chunk",
                contract=route_contracts["search_bm25.document_chunk"],
                top_ids=[str(row[0]) for row in list(bm25_operator_rows or [])],
                expected_top_ids_contains=["chunk_a", "chunk_b"],
            )
        )

        hybrid_rows = hybrid.executor.execute(
            _FixtureSession(_document_rows()),
            raw_query_text="vapor recovery",
            collection_ids=["c1"],
            use_bm25=True,
            use_similarity=True,
            use_sparse=False,
            embedding=[1.0, 0.0, 0.0],
            limit_bm25=5,
            limit_similarity=5,
            bm25_weight=0.5,
            similarity_weight=0.5,
            return_statement=False,
        )
        cases.append(
            _build_case_payload(
                case_id="hybrid_dense_lexical",
                route_id="search_hybrid.document_chunk",
                contract=route_contracts["search_hybrid.document_chunk"],
                top_ids=[str(row[0]) for row in list(hybrid_rows or [])],
                expected_top_id="chunk_a",
            )
        )

        file_rows = file_chunks.executor.execute(
            _FixtureSession(_file_rows()),
            query="flue gas analysis",
            sort_by="score",
            sort_dir="DESC",
            limit=5,
            offset=0,
        ).rows_or_statement
        cases.append(
            _build_case_payload(
                case_id="file_chunk_simple",
                route_id="search_file_chunks",
                contract=route_contracts["search_file_chunks"],
                top_ids=[str(row[0]) for row in list(file_rows or [])],
                expected_top_id="file_a",
            )
        )

        try:
            bm25.executor.execute(
                _FixtureSession(_document_rows()),
                query='title:"vapor recovery"',
                table="document_chunk",
                collection_ids=["c1"],
                sort_by="score",
                sort_dir="DESC",
                limit=5,
                offset=0,
            )
            hard_error_payload: Dict[str, Any] = {}
        except QueryLakeUnsupportedFeatureError as exc:
            hard_error_payload = exc.to_payload()
        cases.append(
            _build_case_payload(
                case_id="bm25_hard_constraint_unsupported",
                route_id="search_bm25.document_chunk",
                contract=route_contracts["search_bm25.document_chunk"],
                error_payload=hard_error_payload,
                expected_error_capability="retrieval.lexical.hard_constraints",
            )
        )
        bringup_after = build_profile_bringup_payload(
            profile=profile,
            metadata_store_path=effective_metadata_store_path,
        )
        dense_sidecar_after = dict(
            dict(bringup_after.get("local_profile") or {}).get("dense_sidecar") or {}
        )

    passed_case_ids = sorted(str(case["case_id"]) for case in cases if bool(case.get("passed")))
    failed_case_ids = sorted(str(case["case_id"]) for case in cases if not bool(case.get("passed")))
    lifecycle_transition = {
        "before": {
            "ready": bool(dense_sidecar_before.get("ready")),
            "lifecycle_state": str(dense_sidecar_before.get("lifecycle_state") or ""),
            "cache_lifecycle_state": str(
                dense_sidecar_before.get("cache_lifecycle_state") or ""
            ),
            "cache_warmed": bool(dense_sidecar_before.get("cache_warmed")),
            "ready_state_source": str(dense_sidecar_before.get("ready_state_source") or ""),
            "stats_source": str(dense_sidecar_before.get("stats_source") or ""),
        },
        "after": {
            "ready": bool(dense_sidecar_after.get("ready")),
            "lifecycle_state": str(dense_sidecar_after.get("lifecycle_state") or ""),
            "cache_lifecycle_state": str(
                dense_sidecar_after.get("cache_lifecycle_state") or ""
            ),
            "cache_warmed": bool(dense_sidecar_after.get("cache_warmed")),
            "ready_state_source": str(dense_sidecar_after.get("ready_state_source") or ""),
            "stats_source": str(dense_sidecar_after.get("stats_source") or ""),
        },
    }
    lifecycle_transition["cache_warmup_transition_ok"] = bool(
        lifecycle_transition["before"]["ready"]
        and lifecycle_transition["after"]["ready"]
        and not lifecycle_transition["before"]["cache_warmed"]
        and lifecycle_transition["after"]["cache_warmed"]
        and lifecycle_transition["after"]["cache_lifecycle_state"]
        == "cache_warmed_process_local"
    )
    payload: Dict[str, Any] = {
        "profile": profile_id,
        "metadata_store_path": effective_metadata_store_path,
        "bringup_summary": dict(bringup_payload.get("summary") or {}),
        "local_profile": dict(bringup_payload.get("local_profile") or {}),
        "dense_sidecar_lifecycle_transition": lifecycle_transition,
        "cases": cases,
        "summary": {
            "case_count": len(cases),
            "passed_case_count": len(passed_case_ids),
            "failed_case_count": len(failed_case_ids),
            "passed_case_ids": passed_case_ids,
            "failed_case_ids": failed_case_ids,
            "all_passed": len(failed_case_ids) == 0,
            "dense_sidecar_cache_warmed": bool(LOCAL_DENSE_SIDECAR_ADAPTER._index_registry),
            "dense_sidecar_cache_keys": sorted(list((LOCAL_DENSE_SIDECAR_ADAPTER._index_registry or {}).keys())),
            "dense_sidecar_cache_warmup_transition_ok": bool(
                lifecycle_transition["cache_warmup_transition_ok"]
            ),
        },
    }
    return payload


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute the local embedded profile's declared route slice.")
    parser.add_argument("--profile", default=LOCAL_PROFILE_ID)
    parser.add_argument("--enable-ready-profile-projections", action="store_true")
    parser.add_argument("--projection-metadata-path", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    payload = build_local_query_smoke_payload(
        profile_id=args.profile,
        enable_ready_profile_projections=bool(args.enable_ready_profile_projections),
        metadata_store_path=args.projection_metadata_path,
    )
    rendered = json.dumps(payload, indent=2)
    print(rendered)
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    return 0 if bool(dict(payload.get("summary") or {}).get("all_passed")) else 2


if __name__ == "__main__":
    raise SystemExit(main())

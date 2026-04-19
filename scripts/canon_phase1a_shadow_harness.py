#!/usr/bin/env python
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from QueryLake.canon.runtime import execute_shadow_case
from QueryLake.runtime.retrieval_primitives_legacy import RRFusion
from QueryLake.typing.retrieval_primitives import RetrievalCandidate, RetrievalExecutionResult


class _SyntheticRetriever:
    def __init__(self, primitive_id: str, rows: list[RetrievalCandidate]):
        self.primitive_id = primitive_id
        self.version = "v1"
        self._rows = rows

    async def retrieve(self, _request):
        return list(self._rows)


def _load_cases(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_rows(case: dict[str, Any]) -> list[RetrievalCandidate]:
    expected_ids = [str(value) for value in case.get("expected_ids", [])]
    if not expected_ids:
        expected_ids = [f"{case['case_id']}_candidate_1"]
    return [
        RetrievalCandidate(
            content_id=candidate_id,
            text=f"synthetic:{candidate_id}",
            provenance=["synthetic_shadow_harness"],
        )
        for candidate_id in expected_ids
    ]


async def _run(args) -> int:
    cases = _load_cases(Path(args.fixture))
    if args.limit_cases is not None:
        cases = cases[: args.limit_cases]

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "schema_version": "canon_phase1a_shadow_harness_summary_v1",
        "fixture": str(Path(args.fixture)),
        "profile_id": args.profile_id,
        "case_count": len(cases),
        "report_paths": [],
    }

    for case in cases:
        rows = _build_rows(case)
        route = str(case.get("route") or "")
        if route == "search_file_chunks":
            retrievers = {"file_bm25": _SyntheticRetriever("SyntheticRetriever", rows)}
        elif route == "search_hybrid.document_chunk":
            retrievers = {
                "bm25": _SyntheticRetriever("SyntheticRetrieverBM25", rows),
                "dense": _SyntheticRetriever("SyntheticRetrieverDense", rows),
                "sparse": _SyntheticRetriever("SyntheticRetrieverSparse", rows),
            }
        else:
            retrievers = {"bm25": _SyntheticRetriever("SyntheticRetriever", rows)}
        legacy_result = RetrievalExecutionResult(
            pipeline_id=f"legacy::{route}",
            pipeline_version="v1",
            candidates=list(rows),
        )
        result = await execute_shadow_case(
            case=case,
            profile_id=args.profile_id,
            retrievers=retrievers,
            legacy_result=legacy_result,
            fusion=RRFusion(),
            output_dir=str(output_dir),
            limit=args.limit,
        )
        if result.get("persisted"):
            summary["report_paths"].append(result["persisted"]["path"])

    summary_path = output_dir / "canon_phase1a_shadow_harness_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"summary_path": str(summary_path), "report_count": len(summary["report_paths"])}, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run bounded Canon++ Phase 1A synthetic shadow harness.")
    parser.add_argument(
        "--fixture",
        default="tests/fixtures/db_compat_retrieval_parity_cases.json",
        help="Path to parity/shadow cases JSON fixture.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory to write shadow reports into.",
    )
    parser.add_argument(
        "--profile-id",
        default="phase1a_synthetic_shadow",
        help="Profile id to stamp into reports.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Requested retrieval limit.",
    )
    parser.add_argument(
        "--limit-cases",
        type=int,
        default=None,
        help="Optional cap on number of cases from the fixture.",
    )
    args = parser.parse_args()
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())

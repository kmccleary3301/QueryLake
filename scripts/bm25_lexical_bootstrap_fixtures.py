#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence


DEFAULT_CASE_FILES = [
    "tests/fixtures/retrieval_eval_smoke.json",
    "tests/fixtures/retrieval_eval_code_search.json",
    "tests/fixtures/retrieval_eval_enterprise_docs.json",
    "tests/fixtures/retrieval_eval_multihop.json",
    "tests/fixtures/retrieval_eval_agentic_depth.json",
]


SLICE_MANIFEST_ADDITIONS: Dict[str, Dict[str, str]] = {
    "technical_doc": {
        "primary_metric": "nDCG@10",
        "description": "Technical documentation and operations-style lexical queries.",
    },
    "enterprise_doc": {
        "primary_metric": "nDCG@10",
        "description": "Enterprise documentation and policy-like corpora.",
    },
    "code_search": {
        "primary_metric": "Success@1",
        "description": "Code-search and known-function retrieval queries.",
    },
    "multi_hop": {
        "primary_metric": "Recall@10",
        "description": "Queries whose gold set spans multiple supporting passages.",
    },
    "exploratory_nl": {
        "primary_metric": "MRR@10",
        "description": "Open natural-language search prompts with lexical ambiguity.",
    },
    "short_query": {
        "primary_metric": "Success@1",
        "description": "Very short head queries where exactness and fielding matter.",
    },
    "phrase_sensitive": {
        "primary_metric": "nDCG@10",
        "description": "Queries where term dependence or ordered proximity matters.",
    },
    "technical_code_symbol": {
        "primary_metric": "Success@1",
        "description": "Identifier- or API-symbol-heavy code and implementation queries.",
    },
    "document_chunk": {
        "primary_metric": "nDCG@10",
        "description": "Chunk-level lexical retrieval surfaces.",
    },
}


DATASET_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "retrieval_eval_smoke": {
        "route": "search_bm25.document_chunk",
        "query_slices": ["phrase_sensitive", "technical_doc"],
        "corpus_slices": ["document_chunk", "technical_doc"],
    },
    "retrieval_eval_code_search": {
        "route": "search_bm25.document_chunk",
        "query_slices": ["code_search", "technical_code_symbol"],
        "corpus_slices": ["document_chunk", "code_search"],
    },
    "retrieval_eval_enterprise_docs": {
        "route": "search_bm25.document_chunk",
        "query_slices": ["phrase_sensitive", "enterprise_doc"],
        "corpus_slices": ["document_chunk", "enterprise_doc"],
    },
    "retrieval_eval_multihop": {
        "route": "search_bm25.document_chunk",
        "query_slices": ["exploratory_nl", "multi_hop"],
        "corpus_slices": ["document_chunk", "multi_hop"],
    },
    "retrieval_eval_agentic_depth": {
        "route": "search_bm25.document_chunk",
        "query_slices": ["exploratory_nl"],
        "corpus_slices": ["document_chunk"],
    },
    "BCAS_PHASE2_LIVE_EVAL_CASES_dense_heavy_augtrivia_2026-02-24": {
        "route": "search_bm25.document_chunk",
        "query_slices": ["exploratory_nl"],
        "corpus_slices": ["document_chunk"],
    },
}


def _load_case_rows(path: Path) -> List[Dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"{path} must contain a top-level list")
    return [row for row in payload if isinstance(row, dict)]


def _query_slices_for_row(dataset_key: str, row: Dict[str, Any]) -> List[str]:
    defaults = list(DATASET_DEFAULTS.get(dataset_key, {}).get("query_slices", []))
    scenario = str(row.get("scenario", "") or "").strip()
    if scenario:
        defaults.append(scenario)
    query = str(row.get("query", "") or "").strip()
    if len(query.split()) <= 3:
        defaults.append("short_query")
    return sorted({str(value) for value in defaults if str(value).strip()})


def _corpus_slices_for_row(dataset_key: str, row: Dict[str, Any]) -> List[str]:
    defaults = list(DATASET_DEFAULTS.get(dataset_key, {}).get("corpus_slices", []))
    dataset_value = str(row.get("dataset", "") or "").strip()
    if dataset_value:
        defaults.append(dataset_value)
    return sorted({str(value) for value in defaults if str(value).strip()})


def build_bootstrap_payload(case_files: Sequence[Path]) -> Dict[str, Any]:
    query_rows: List[Dict[str, Any]] = []
    qrel_rows: List[Dict[str, Any]] = []
    reference_run_rows: List[Dict[str, Any]] = []
    merged_slice_manifest = dict(SLICE_MANIFEST_ADDITIONS)
    query_counter = 0
    for path in case_files:
        dataset_key = path.stem
        defaults = DATASET_DEFAULTS.get(dataset_key, {})
        route = str(defaults.get("route", "search_bm25.document_chunk"))
        rows = _load_case_rows(path)
        for row in rows:
            query_counter += 1
            query_id = f"bootstrap_q_{query_counter:05d}"
            query_rows.append(
                {
                    "query_id": query_id,
                    "route": route,
                    "profile_id": "paradedb_postgres_gold_v1",
                    "query_text": str(row.get("query", "") or ""),
                    "query_slices": _query_slices_for_row(dataset_key, row),
                    "corpus_slices": _corpus_slices_for_row(dataset_key, row),
                    "collection_ids": [str(v) for v in row.get("allowed_collection_ids", []) if isinstance(v, str) and str(v).strip()],
                    "notes": f"Bootstrapped from {path.name}",
                    "source_fixture": str(path),
                }
            )
            expected_ids = [str(v) for v in row.get("expected_ids", []) if v is not None]
            reference_run_rows.append(
                {
                    "query_id": query_id,
                    "retrieved_ids": [str(v) for v in row.get("retrieved_ids", []) if v is not None],
                    "latency_ms": float(row.get("response_ms", 0.0) or 0.0),
                    "debug": {"source_fixture": str(path)},
                }
            )
            for result_id in expected_ids:
                qrel_rows.append(
                    {
                        "query_id": query_id,
                        "result_id": result_id,
                        "relevance": 2,
                        "authority_id": "",
                        "judged_by": "bootstrap_fixture",
                        "notes": f"Bootstrapped expected id from {path.name}",
                    }
                )
    return {
        "query_rows": query_rows,
        "qrel_rows": qrel_rows,
        "reference_run_rows": reference_run_rows,
        "slice_manifest": merged_slice_manifest,
    }


def _write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap lexical query/qrel fixtures from existing retrieval-eval case files.")
    parser.add_argument("--case-file", action="append", default=[], help="Additional retrieval-eval case file(s) to include")
    parser.add_argument("--include-bcas", action="store_true", help="Include docs_tmp/RAG/BCAS phase-2 live eval cases in the bootstrap set")
    parser.add_argument("--query-set-output", required=True)
    parser.add_argument("--qrels-output", required=True)
    parser.add_argument("--slice-manifest-output", required=True)
    parser.add_argument("--reference-run-output", default="")
    args = parser.parse_args()

    case_files = [Path(value) for value in DEFAULT_CASE_FILES]
    case_files.extend(Path(value) for value in list(args.case_file or []))
    if args.include_bcas:
        case_files.append(Path("docs_tmp/RAG/BCAS_PHASE2_LIVE_EVAL_CASES_dense_heavy_augtrivia_2026-02-24.json"))

    payload = build_bootstrap_payload(case_files)
    _write_jsonl(Path(args.query_set_output), payload["query_rows"])
    _write_jsonl(Path(args.qrels_output), payload["qrel_rows"])
    slice_manifest_path = Path(args.slice_manifest_output)
    slice_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    slice_manifest_path.write_text(json.dumps(payload["slice_manifest"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.reference_run_output:
        reference_run_path = Path(args.reference_run_output)
        reference_run_path.parent.mkdir(parents=True, exist_ok=True)
        reference_run_path.write_text(json.dumps(payload["reference_run_rows"], indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "query_count": len(payload["query_rows"]),
                "qrel_count": len(payload["qrel_rows"]),
                "reference_run_count": len(payload["reference_run_rows"]),
                "case_file_count": len(case_files),
                "query_set_output": args.query_set_output,
                "qrels_output": args.qrels_output,
                "slice_manifest_output": args.slice_manifest_output,
                "reference_run_output": args.reference_run_output,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

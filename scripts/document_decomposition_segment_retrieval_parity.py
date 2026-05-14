#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import text as sql_text

from QueryLake.database.create_db_session import initialize_database_engine
from QueryLake.database.sql_db_tables import DocumentChunk, document_raw, document_segment, document_segment_view, document_version
from QueryLake.runtime.document_decomposition import DEFAULT_LOCAL_TEXT_VIEW_ALIAS

DEFAULT_QUERIES = [
    "querylake retrieval",
    "document chunk",
    "canonical segment",
    "metadata search",
    "table markdown",
]


def compare_ranked_ids(*, baseline_ids: Sequence[str], candidate_ids: Sequence[str], k: int) -> Dict[str, Any]:
    baseline_top = [str(row) for row in baseline_ids[:k] if row]
    candidate_top = [str(row) for row in candidate_ids[:k] if row]
    baseline_set = set(baseline_top)
    candidate_set = set(candidate_top)
    overlap = baseline_set & candidate_set
    missing_from_candidate = [row for row in baseline_top if row not in candidate_set]
    candidate_only = [row for row in candidate_top if row not in baseline_set]
    return {
        "k": int(k),
        "baseline_count": len(baseline_top),
        "candidate_count": len(candidate_top),
        "overlap_count": len(overlap),
        "overlap_at_k": 0.0 if k <= 0 else len(overlap) / float(k),
        "recall_against_baseline_at_k": 1.0 if not baseline_top else len(overlap) / float(len(baseline_top)),
        "missing_from_candidate": missing_from_candidate,
        "candidate_only": candidate_only,
    }


def _collection_filter_sql(alias: str, collection_ids: Sequence[str]) -> str:
    if not collection_ids:
        return ""
    field = "collection_id" if alias == "c" else "document_collection_id"
    return f" AND {alias}.{field} = ANY(:collection_ids)"


def run_query_pair(database, *, query: str, limit: int, collection_ids: Sequence[str]) -> Dict[str, Any]:
    chunk_sql = sql_text(
        f"""
        WITH q AS (SELECT plainto_tsquery('english', :query) AS query)
        SELECT
            c.id AS chunk_id,
            c.authority_segment_id AS authority_segment_id,
            c.document_id AS document_id,
            c.document_chunk_number AS ordinal,
            ts_rank_cd(c.ts_content, q.query) AS score
        FROM {DocumentChunk.__tablename__} c, q
        WHERE c.ts_content @@ q.query
        {_collection_filter_sql('c', collection_ids)}
        ORDER BY score DESC, c.document_id ASC, c.document_chunk_number ASC, c.id ASC
        LIMIT :limit
        """
    )
    segment_sql = sql_text(
        f"""
        WITH q AS (SELECT plainto_tsquery('english', :query) AS query)
        SELECT
            s.id AS segment_id,
            v.document_id AS document_id,
            s.segment_index AS ordinal,
            ts_rank_cd(s.ts_content, q.query) AS score
        FROM {document_segment.__tablename__} s
        JOIN {document_segment_view.__tablename__} sv ON sv.id = s.segment_view_id
        JOIN {document_version.__tablename__} v ON v.id = s.document_version_id
        JOIN {document_raw.__tablename__} d ON d.id = v.document_id,
        q
        WHERE s.ts_content @@ q.query
          AND sv.view_alias = :view_alias
          AND sv.is_current = TRUE
        {_collection_filter_sql('d', collection_ids)}
        ORDER BY score DESC, v.document_id ASC, s.segment_index ASC, s.id ASC
        LIMIT :limit
        """
    )
    common_params = {
        "query": str(query),
        "limit": int(limit),
    }
    if collection_ids:
        common_params["collection_ids"] = list(collection_ids)
    chunk_started_at = time.perf_counter()
    chunk_rows = [dict(row._mapping) for row in database.exec(chunk_sql.bindparams(**common_params)).all()]
    chunk_elapsed_ms = (time.perf_counter() - chunk_started_at) * 1000.0
    segment_started_at = time.perf_counter()
    segment_rows = [dict(row._mapping) for row in database.exec(
        segment_sql.bindparams(**common_params, view_alias=DEFAULT_LOCAL_TEXT_VIEW_ALIAS)
    ).all()]
    segment_elapsed_ms = (time.perf_counter() - segment_started_at) * 1000.0
    chunk_authority_ids = [str(row.get("authority_segment_id") or "") for row in chunk_rows if row.get("authority_segment_id")]
    segment_ids = [str(row.get("segment_id") or "") for row in segment_rows if row.get("segment_id")]
    comparison = compare_ranked_ids(baseline_ids=chunk_authority_ids, candidate_ids=segment_ids, k=int(limit))
    return {
        "query": str(query),
        "limit": int(limit),
        "chunk_result_count": len(chunk_rows),
        "segment_result_count": len(segment_rows),
        "chunk_missing_authority_count": sum(1 for row in chunk_rows if not row.get("authority_segment_id")),
        "timings_ms": {
            "chunk_query": chunk_elapsed_ms,
            "segment_query": segment_elapsed_ms,
            "candidate_over_baseline_ratio": (
                None
                if chunk_elapsed_ms <= 0
                else segment_elapsed_ms / chunk_elapsed_ms
            ),
        },
        "comparison": comparison,
        "chunk_results": chunk_rows,
        "segment_results": segment_rows,
    }


def _load_queries(args: argparse.Namespace) -> List[str]:
    queries = list(args.query or [])
    if args.queries_json:
        payload = json.loads(Path(args.queries_json).read_text())
        if isinstance(payload, list):
            queries.extend(str(row.get("query") if isinstance(row, dict) else row) for row in payload)
        elif isinstance(payload, dict):
            queries.extend(
                str(row.get("query") if isinstance(row, dict) else row)
                for row in payload.get("queries", [])
            )
    return queries or list(DEFAULT_QUERIES)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare DocumentChunk BM25 authority hits against direct document_segment text hits.")
    parser.add_argument("--query", action="append", default=[])
    parser.add_argument("--queries-json")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--collection-id", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    database, _ = initialize_database_engine(ensure_sparse_bootstrap=False)
    query_reports = [
        run_query_pair(
            database,
            query=query,
            limit=int(args.limit),
            collection_ids=list(args.collection_id or []),
        )
        for query in _load_queries(args)
    ]
    non_empty = [row for row in query_reports if row["chunk_result_count"] or row["segment_result_count"]]
    chunk_result_total = sum(row["chunk_result_count"] for row in query_reports)
    chunk_missing_authority_total = sum(row["chunk_missing_authority_count"] for row in query_reports)
    provenance_coverage = (
        1.0
        if chunk_result_total <= 0
        else max(0.0, 1.0 - (float(chunk_missing_authority_total) / float(chunk_result_total)))
    )
    latency_ratios = [
        float(row["timings_ms"]["candidate_over_baseline_ratio"])
        for row in query_reports
        if row.get("timings_ms", {}).get("candidate_over_baseline_ratio") is not None
    ]
    payload = {
        "schema_version": "document_decomposition_segment_retrieval_parity_v1",
        "view_alias": DEFAULT_LOCAL_TEXT_VIEW_ALIAS,
        "query_count": len(query_reports),
        "non_empty_query_count": len(non_empty),
        "mean_overlap_at_k": 0.0 if not non_empty else sum(row["comparison"]["overlap_at_k"] for row in non_empty) / len(non_empty),
        "mean_recall_against_baseline_at_k": (
            0.0
            if not non_empty
            else sum(row["comparison"]["recall_against_baseline_at_k"] for row in non_empty) / len(non_empty)
        ),
        "candidate_over_baseline_latency_ratio": (
            1.0
            if not latency_ratios
            else sum(latency_ratios) / float(len(latency_ratios))
        ),
        "fallback_rate": 0.0,
        "provenance_coverage": provenance_coverage,
        "chunk_result_total": chunk_result_total,
        "chunk_missing_authority_total": chunk_missing_authority_total,
        "queries": query_reports,
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

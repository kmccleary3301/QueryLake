from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, List, Sequence, Tuple
import re

from sqlmodel import Session

from QueryLake.runtime.db_compat import BackendStack, QueryLakeUnsupportedFeatureError
from QueryLake.runtime.local_dense_sidecar import LOCAL_DENSE_SIDECAR_ADAPTER
from QueryLake.runtime.local_lexical_adapter import LOCAL_LEXICAL_ADAPTER
from QueryLake.runtime.local_profile_v2 import (
    LOCAL_DENSE_SIDECAR_PROJECTION_ID,
    build_document_chunk_hybrid_rows,
    build_document_chunk_lexical_rows,
    build_file_chunk_lexical_rows,
    build_local_route_runtime_context_v2,
    resolve_local_route_materialization_target,
)
from QueryLake.runtime.query_ir_v2 import QueryIRV2
from QueryLake.runtime.projection_contracts import (
    DocumentChunkMaterializationRecord,
    FileChunkMaterializationRecord,
)
from QueryLake.runtime.retrieval_lane_executors import GoldBM25SearchPlan


@dataclass(frozen=True)
class LocalBM25ScaffoldExecution:
    rows_or_statement: Any
    formatted_query: str
    quoted_phrases: Tuple[str, ...]
    plan: GoldBM25SearchPlan


@dataclass(frozen=True)
class LocalFileChunkScaffoldExecution:
    rows_or_statement: Any
    query_is_empty: bool


@dataclass(frozen=True)
class SQLiteLocalSearchHybridRouteExecutor:
    executor_id: str
    route_id: str
    profile_id: str
    support_state: str
    backend_stack: BackendStack
    capability: str = "retrieval.execution"
    supports_plan_only: bool = True

    def execute(self, database: Session, **kwargs: Any) -> Any:
        context = build_local_route_runtime_context_v2(
            self.route_id,
            profile=SimpleNamespace(id=self.profile_id),
            raw_query_text=str(kwargs.get("raw_query_text") or ""),
            support_state=self.support_state,
            use_dense=bool(kwargs.get("use_similarity")),
            use_sparse=bool(kwargs.get("use_sparse")),
            collection_ids=list(kwargs.get("collection_ids") or []),
            return_statement=bool(kwargs.get("return_statement")),
        )
        query_ir_v2 = QueryIRV2.model_validate(context.query_ir_v2_template)
        query_features = dict(query_ir_v2.planner_hints.get("query_features") or {})
        if bool(query_ir_v2.use_sparse):
            raise QueryLakeUnsupportedFeatureError(
                capability="retrieval.sparse.vector",
                message="Local profile does not support sparse retrieval for hybrid execution.",
                profile=self.profile_id,
                support_state="unsupported",
                backend_stack=self.backend_stack,
                hint="Disable sparse retrieval or use a profile with sparse support.",
            )
        if bool(query_features.get("hard_constraints")):
            raise QueryLakeUnsupportedFeatureError(
                capability="retrieval.lexical.hard_constraints",
                message="Local profile rejects exact hard lexical constraints for hybrid execution.",
                profile=self.profile_id,
                support_state="unsupported",
                backend_stack=self.backend_stack,
                hint="Remove fielded or hard lexical constraints, or use the gold profile.",
            )
        if bool(kwargs.get("return_statement")):
            lanes = []
            if bool(kwargs.get("use_bm25")):
                lanes.append("sqlite_fts5")
            if bool(kwargs.get("use_similarity")):
                lanes.append("local_dense_sidecar")
            if bool(kwargs.get("use_sparse")):
                lanes.append("unsupported_sparse")
            lane_summary = ", ".join(lanes) if len(lanes) > 0 else "none"
            return (
                "LOCAL_QUERYLAKE_SCAFFOLD_PLAN\n"
                f"profile={self.profile_id}\n"
                f"route={self.route_id}\n"
                f"query={str(kwargs.get('raw_query_text') or '')}\n"
                f"collection_ids={list(kwargs.get('collection_ids') or [])}\n"
                f"lanes={lane_summary}\n"
                f"query_ir_v2={query_ir_v2.model_dump_json()}\n"
                "note=This is a local planning view for the executable local route slice."
            )
        raw_query_text = str(query_ir_v2.raw_query_text or "")
        use_bm25 = bool(kwargs.get("use_bm25"))
        use_similarity = bool(kwargs.get("use_similarity"))
        limit_bm25 = int(kwargs.get("limit_bm25") or 0)
        limit_similarity = int(kwargs.get("limit_similarity") or 0)
        bm25_weight = float(kwargs.get("bm25_weight") or 0.0)
        similarity_weight = float(kwargs.get("similarity_weight") or 0.0)
        lexical_query = str(query_ir_v2.lexical_query_text or query_ir_v2.normalized_query_text or "")

        lexical_ranked: List[Tuple[DocumentChunkMaterializationRecord, float]] = []
        if use_bm25 and lexical_query.strip():
            lexical_target = resolve_local_route_materialization_target(
                context,
                "document_chunk_lexical_projection_v1",
            )
            lexical_ranked, _ = LOCAL_LEXICAL_ADAPTER.search_document_chunks(
                database,
                target=lexical_target,
                query_ir_v2=query_ir_v2,
                sort_by="score",
                sort_dir="DESC",
                limit=limit_bm25,
                offset=0,
            )
        dense_ranked: List[Tuple[DocumentChunkMaterializationRecord, float]] = []
        if use_similarity:
            dense_target = resolve_local_route_materialization_target(
                context,
                LOCAL_DENSE_SIDECAR_PROJECTION_ID,
            )
            dense_ranked = LOCAL_DENSE_SIDECAR_ADAPTER.search_projection(
                database,
                target=dense_target,
                query_embedding=kwargs.get("embedding"),
                limit=limit_similarity,
            )

        return build_document_chunk_hybrid_rows(
            lexical_ranked,
            dense_ranked,
            bm25_weight=bm25_weight,
            similarity_weight=similarity_weight,
        )


@dataclass(frozen=True)
class SQLiteLocalSearchBM25RouteExecutor:
    executor_id: str
    route_id: str
    profile_id: str
    support_state: str
    backend_stack: BackendStack
    capability: str = "retrieval.lexical.bm25"
    supports_plan_only: bool = True

    def execute(self, database: Session, **kwargs: Any) -> Any:
        query = str(kwargs.get("query") or "")
        plan = GoldBM25SearchPlan(
            parse_field=query if query else "()",
            formatted_query=query if query else "()",
            order_by_field=f"ORDER BY {str(kwargs.get('sort_by') or 'score')} {str(kwargs.get('sort_dir') or 'DESC')}",
            quoted_phrases=(),
            segment_collection_filter="",
        )
        context = build_local_route_runtime_context_v2(
            self.route_id,
            profile=SimpleNamespace(id=self.profile_id),
            raw_query_text=query,
            support_state=self.support_state,
            use_dense=False,
            use_sparse=False,
            collection_ids=list(kwargs.get("collection_ids") or []),
            return_statement=bool(kwargs.get("return_statement")),
        )
        query_ir_v2 = QueryIRV2.model_validate(context.query_ir_v2_template)
        query_features = dict(query_ir_v2.planner_hints.get("query_features") or {})
        if bool(query_features.get("hard_constraints")):
            raise QueryLakeUnsupportedFeatureError(
                capability="retrieval.lexical.hard_constraints",
                message="Local profile rejects exact hard lexical constraints for lexical BM25 execution.",
                profile=self.profile_id,
                support_state="unsupported",
                backend_stack=self.backend_stack,
                hint="Remove fielded or hard lexical constraints, or use the gold profile.",
            )
        if bool(kwargs.get("return_statement")):
            statement = (
                "LOCAL_QUERYLAKE_SCAFFOLD_PLAN\n"
                f"profile={self.profile_id}\n"
                f"route={self.route_id}\n"
                f"query={query}\n"
                f"table={str(kwargs.get('table') or 'document_chunk')}\n"
                "lexical_backend=sqlite_fts5\n"
                f"query_ir_v2={query_ir_v2.model_dump_json()}\n"
                "note=This is a local lexical planning view for the executable local route slice."
            )
            return LocalBM25ScaffoldExecution(
                rows_or_statement=statement,
                formatted_query=plan.formatted_query,
                quoted_phrases=plan.quoted_phrases,
                plan=plan,
            )
        collection_ids = {str(item) for item in list(kwargs.get("collection_ids") or []) if str(item)}
        sort_by = str(kwargs.get("sort_by") or "score")
        sort_dir = str(kwargs.get("sort_dir") or "DESC").upper()
        limit = int(kwargs.get("limit") or 10)
        offset = int(kwargs.get("offset") or 0)
        plan = GoldBM25SearchPlan(
            parse_field=query if query else "()",
            formatted_query=query if query else "()",
            order_by_field=f"ORDER BY {sort_by} {sort_dir}",
            quoted_phrases=tuple(),
            segment_collection_filter="",
        )
        lexical_target = resolve_local_route_materialization_target(
            context,
            "document_chunk_lexical_projection_v1",
        )
        paged, query_is_empty = LOCAL_LEXICAL_ADAPTER.search_document_chunks(
            database,
            target=lexical_target,
            query_ir_v2=query_ir_v2,
            sort_by=sort_by,
            sort_dir=sort_dir,
            limit=limit,
            offset=offset,
        )
        rows = build_document_chunk_lexical_rows(paged, query_is_empty=query_is_empty)
        return LocalBM25ScaffoldExecution(
            rows_or_statement=rows,
            formatted_query=plan.formatted_query,
            quoted_phrases=plan.quoted_phrases,
            plan=plan,
        )


@dataclass(frozen=True)
class SQLiteLocalSearchFileChunkRouteExecutor:
    executor_id: str
    route_id: str
    profile_id: str
    support_state: str
    backend_stack: BackendStack
    capability: str = "retrieval.lexical.bm25"
    supports_plan_only: bool = True

    def execute(self, database: Session, **kwargs: Any) -> Any:
        query = str(kwargs.get("query") or "")
        context = build_local_route_runtime_context_v2(
            self.route_id,
            profile=SimpleNamespace(id=self.profile_id),
            raw_query_text=query,
            support_state=self.support_state,
            use_dense=False,
            use_sparse=False,
            collection_ids=list(kwargs.get("collection_ids") or []),
            return_statement=bool(kwargs.get("return_statement")),
        )
        query_ir_v2 = QueryIRV2.model_validate(context.query_ir_v2_template)
        query_features = dict(query_ir_v2.planner_hints.get("query_features") or {})
        if bool(query_features.get("hard_constraints")):
            raise QueryLakeUnsupportedFeatureError(
                capability="retrieval.lexical.hard_constraints",
                message="Local profile rejects exact hard lexical constraints for file-chunk lexical execution.",
                profile=self.profile_id,
                support_state="unsupported",
                backend_stack=self.backend_stack,
                hint="Remove fielded or hard lexical constraints, or use the gold profile.",
            )
        if bool(kwargs.get("return_statement")):
            return LocalFileChunkScaffoldExecution(
                rows_or_statement=(
                    "LOCAL_QUERYLAKE_SCAFFOLD_PLAN\n"
                    f"profile={self.profile_id}\n"
                    f"route={self.route_id}\n"
                    f"query={query}\n"
                    "lexical_backend=sqlite_fts5\n"
                    f"query_ir_v2={query_ir_v2.model_dump_json()}\n"
                    "note=This is a local file lexical planning view for the executable local route slice."
                ),
                query_is_empty=query.strip() == "",
            )
        sort_by = str(kwargs.get("sort_by") or "score")
        sort_dir = str(kwargs.get("sort_dir") or "DESC").upper()
        limit = int(kwargs.get("limit") or 10)
        offset = int(kwargs.get("offset") or 0)
        lexical_target = resolve_local_route_materialization_target(
            context,
            "file_chunk_lexical_projection_v1",
        )
        paged, query_is_empty = LOCAL_LEXICAL_ADAPTER.search_file_chunks(
            database,
            target=lexical_target,
            query_ir_v2=query_ir_v2,
            sort_by=sort_by,
            sort_dir=sort_dir,
            limit=limit,
            offset=offset,
        )
        rows = build_file_chunk_lexical_rows(paged, query_is_empty=query_is_empty)
        return LocalFileChunkScaffoldExecution(
            rows_or_statement=rows,
            query_is_empty=query_is_empty,
        )

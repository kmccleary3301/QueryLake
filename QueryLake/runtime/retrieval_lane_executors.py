from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from sqlalchemy import text
from sqlmodel import Session

from QueryLake.database.sql_db_tables import DocumentChunk
from QueryLake.database.sql_db_tables import (
    FILE_CHUNK_INDEXED_COLUMNS as FILE_FIELDS,
    file as FileTable,
    file_chunk as FileChunkTable,
    file_version as FileVersionTable,
)
from QueryLake.misc_functions.paradedb_query_builder import build_paradedb_lexical_query_plan


@dataclass(frozen=True)
class GoldBM25SearchPlan:
    parse_field: str
    formatted_query: str
    order_by_field: str
    quoted_phrases: Tuple[str, ...]
    segment_collection_filter: str = ""
    lexical_variant_id: str = "QL-L1"
    lexical_query_debug: Dict[str, Any] | None = None


def build_gold_bm25_search_plan(
    *,
    query: str,
    valid_fields: Sequence[str],
    catch_all_fields: Sequence[str],
    table: str,
    collection_ids: Sequence[str],
    sort_by: str,
    sort_dir: str,
    document_collection_attrs: Sequence[str],
    lexical_variant_id: Optional[str] = None,
) -> GoldBM25SearchPlan:
    lexical_plan = build_paradedb_lexical_query_plan(
        str(query or ""),
        valid_fields=list(valid_fields),
        catch_all_fields=list(catch_all_fields),
        variant_id=lexical_variant_id,
    )
    formatted_query = lexical_plan.formatted_query
    strong_where_clause = lexical_plan.strong_where_clause

    if table == "segment":
        assert sort_by != "md", "sort_by='md' is not supported for table='segment'"
        segment_collection_filter = ""
        if len(collection_ids) > 0:
            clean_collection_ids = ",".join([f"'{c}'" for c in collection_ids])
            segment_collection_filter = f" AND COALESCE(document_segment.md->>'collection_id', '') IN ({clean_collection_ids})"
        parse_field = formatted_query
    else:
        collection_spec = (
            f"""collection_id:IN {str(list(collection_ids)).replace("'", "")}"""
            if table == "document_chunk"
            else " OR ".join([
                f"""({collection_attr}:IN {str(list(collection_ids)).replace("'", "")})"""
                for collection_attr in document_collection_attrs
            ])
        )

        if formatted_query.startswith("() NOT "):
            formatted_query = formatted_query[3:]
            parse_field = f"({collection_spec}) {formatted_query}"
        else:
            parse_field = (
                f"({collection_spec}) AND ({formatted_query})"
                if formatted_query != "()"
                else f"{collection_spec}"
            )
        segment_collection_filter = ""

    score_allowed = formatted_query != "()"
    assert not (sort_by == "score" and not score_allowed), "Cannot sort by score if no query is specified"
    order_by_field = f"ORDER BY {sort_by} {sort_dir}" + (", id ASC" if sort_by != "id" else "")
    quoted_phrases = tuple(re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"', query)[:4])

    return GoldBM25SearchPlan(
        parse_field=parse_field,
        formatted_query=formatted_query,
        order_by_field=order_by_field,
        quoted_phrases=quoted_phrases,
        segment_collection_filter=segment_collection_filter,
        lexical_variant_id=lexical_plan.variant_id,
        lexical_query_debug=dict(lexical_plan.debug),
    )


def execute_gold_document_chunk_hybrid_lanes(
    database: Session,
    *,
    collection_spec: str,
    formatted_query: str,
    strong_where_clause: Optional[str],
    similarity_constraint: str,
    retrieved_fields_string: str,
    use_bm25: bool,
    use_similarity: bool,
    use_sparse: bool,
    limit_bm25: int,
    limit_similarity: int,
    limit_sparse: int,
    similarity_weight: float,
    bm25_weight: float,
    sparse_weight: float,
    embedding: Any,
    embedding_sparse: Any,
    sparse_dimensions: int,
    return_statement: bool = False,
) -> Union[str, List[Any]]:
    bm25_filter_expr = f"({collection_spec}) AND ({formatted_query})"
    if strong_where_clause is not None:
        bm25_filter_expr = f"({collection_spec}) AND ({strong_where_clause}) AND ({formatted_query})"

    bm25_ranked_cte = f"""
    bm25_candidates AS (
        SELECT id
        FROM {DocumentChunk.__tablename__}
        WHERE id @@@ paradedb.parse('{bm25_filter_expr}')
        ORDER BY paradedb.score(id) DESC
        LIMIT :limit_bm25
    ),
    bm25_ranked AS (
        SELECT id, RANK() OVER (ORDER BY paradedb.score(id) DESC) AS rank
        FROM bm25_candidates
    )
    """ if use_bm25 else """
    bm25_ranked AS (
        SELECT NULL::text AS id, NULL::bigint AS rank WHERE FALSE
    )
    """

    semantic_search_cte = f"""
    semantic_search AS (
        SELECT id, RANK() OVER (ORDER BY embedding <=> :embedding_in) AS rank
        FROM {DocumentChunk.__tablename__}
        {similarity_constraint} AND embedding IS NOT NULL
        ORDER BY embedding <=> :embedding_in
        LIMIT :limit_similarity
    )
    """ if use_similarity else """
    semantic_search AS (
        SELECT NULL::text AS id, NULL::bigint AS rank WHERE FALSE
    )
    """

    sparse_search_cte = f"""
    sparse_search AS (
        SELECT id, RANK() OVER (
            ORDER BY (embedding_sparse::sparsevec({int(sparse_dimensions)})) <=> CAST(:sparse_embedding_in AS sparsevec({int(sparse_dimensions)}))
        ) AS rank
        FROM {DocumentChunk.__tablename__}
        {similarity_constraint} AND embedding_sparse IS NOT NULL
        ORDER BY (embedding_sparse::sparsevec({int(sparse_dimensions)})) <=> CAST(:sparse_embedding_in AS sparsevec({int(sparse_dimensions)}))
        LIMIT :limit_sparse
    )
    """ if use_sparse else """
    sparse_search AS (
        SELECT NULL::text AS id, NULL::bigint AS rank WHERE FALSE
    )
    """

    total_limit = int(limit_bm25 + limit_similarity + limit_sparse)
    assert total_limit > 0, "At least one lane must have a positive limit"

    stmt_text = text(f"""
        WITH
        {bm25_ranked_cte},
        {semantic_search_cte},
        {sparse_search_cte},
        candidate_ids AS (
            SELECT id FROM bm25_ranked
            UNION
            SELECT id FROM semantic_search
            UNION
            SELECT id FROM sparse_search
        )
        SELECT
            candidate_ids.id AS id,
            COALESCE(1.0 / (60 + semantic_search.rank), 0.0) AS semantic_score,
            COALESCE(1.0 / (60 + bm25_ranked.rank), 0.0) AS bm25_score,
            COALESCE(1.0 / (60 + sparse_search.rank), 0.0) AS sparse_score,
            (
                COALESCE(1.0 / (60 + semantic_search.rank), 0.0) * :similarity_weight +
                COALESCE(1.0 / (60 + bm25_ranked.rank), 0.0) * :bm25_weight +
                COALESCE(1.0 / (60 + sparse_search.rank), 0.0) * :sparse_weight
            ) AS score,
            {retrieved_fields_string}
        FROM candidate_ids
        LEFT JOIN semantic_search ON candidate_ids.id = semantic_search.id
        LEFT JOIN bm25_ranked ON candidate_ids.id = bm25_ranked.id
        LEFT JOIN sparse_search ON candidate_ids.id = sparse_search.id
        JOIN {DocumentChunk.__tablename__} ON {DocumentChunk.__tablename__}.id = candidate_ids.id
        ORDER BY score DESC, text
        LIMIT :sum;
    """)
    bind_values = {
        "similarity_weight": float(similarity_weight),
        "bm25_weight": float(bm25_weight),
        "sparse_weight": float(sparse_weight),
        "sum": total_limit,
    }
    if use_bm25:
        bind_values["limit_bm25"] = limit_bm25
    if use_similarity:
        bind_values["limit_similarity"] = limit_similarity
        bind_values["embedding_in"] = str(embedding)
    if use_sparse:
        bind_values["limit_sparse"] = limit_sparse
        bind_values["sparse_embedding_in"] = (
            embedding_sparse.to_text()
            if hasattr(embedding_sparse, "to_text")
            else str(embedding_sparse)
        )
    stmt = stmt_text.bindparams(**bind_values)

    if return_statement:
        return str(stmt.compile(compile_kwargs={"literal_binds": True}))

    return list(database.exec(stmt))


def execute_gold_bm25_search(
    database: Session,
    *,
    chosen_table_name: str,
    chosen_attributes: str,
    parse_field: str,
    order_by_field: str,
    limit: int,
    offset: int,
    table: str,
    formatted_query: str,
    quoted_phrases: Sequence[str],
    segment_collection_filter: str = "",
    return_statement: bool = False,
) -> Union[str, List[Any]]:
    score_field = "paradedb.score(id) AS score, " if formatted_query != "()" else ""
    phrase_rerank_enabled = (
        formatted_query != "()"
        and order_by_field == "ORDER BY score DESC, id ASC"
        and table in {"document_chunk", "segment"}
        and len(list(quoted_phrases)) > 0
    )

    if phrase_rerank_enabled:
        score_bind_params: Dict[str, Any] = {}
        phrase_boost_terms: List[str] = []
        for i, phrase in enumerate(list(quoted_phrases)[:4]):
            key = f"phrase_boost_{i}"
            score_bind_params[key] = phrase
            phrase_boost_terms.append(
                f"CASE WHEN POSITION(LOWER(:{key}) IN LOWER({chosen_table_name}.text)) > 0 THEN 1000 ELSE 0 END"
            )
        phrase_boost_expr = " + ".join(phrase_boost_terms)
        candidate_limit = min(400, max(int(limit) * 8, int(offset) + int(limit) * 4, 80))
        segment_filter_clause = segment_collection_filter if table == "segment" else ""
        stmt = text(f"""
        WITH bm25_candidates AS (
            SELECT id, paradedb.score(id) AS base_score
            FROM {chosen_table_name}
            WHERE id @@@ paradedb.parse('{parse_field}')
            {segment_filter_clause}
            ORDER BY paradedb.score(id) DESC
            LIMIT :candidate_limit
        )
        SELECT
            {chosen_table_name}.id AS id,
            (bm25_candidates.base_score + {phrase_boost_expr}) AS score,
            {chosen_attributes}
        FROM bm25_candidates
        JOIN {chosen_table_name} ON {chosen_table_name}.id = bm25_candidates.id
        ORDER BY score DESC, {chosen_table_name}.id ASC
        LIMIT :limit
        OFFSET :offset;
        """).bindparams(
            limit=limit,
            offset=offset,
            candidate_limit=candidate_limit,
            **score_bind_params,
        )
    elif table == "segment":
        stmt = text(f"""
        SELECT id, {score_field}{chosen_attributes}
        FROM {chosen_table_name}
        WHERE id @@@ paradedb.parse('{parse_field}')
        {segment_collection_filter}
        {order_by_field}
        LIMIT :limit
        OFFSET :offset;
        """).bindparams(
            limit=limit,
            offset=offset,
        )
    else:
        stmt = text(f"""
        SELECT id, {score_field}{chosen_attributes}
        FROM {chosen_table_name}
        WHERE id @@@ paradedb.parse('{parse_field}')
        {order_by_field}
        LIMIT :limit
        OFFSET :offset;
        """).bindparams(
            limit=limit,
            offset=offset,
        )

    if return_statement:
        return str(stmt.compile(compile_kwargs={"literal_binds": True}))

    return list(database.exec(stmt))


def execute_gold_file_chunk_bm25_search(
    database: Session,
    *,
    username: str,
    query: str,
    sort_by: str,
    sort_dir: str,
    limit: int,
    offset: int,
    return_statement: bool = False,
    lexical_variant_id: Optional[str] = None,
) -> Union[str, List[Any]]:
    lexical_plan = build_paradedb_lexical_query_plan(
        str(query or ""),
        valid_fields=FILE_FIELDS,
        catch_all_fields=["text"],
        variant_id=lexical_variant_id,
    )
    formatted_query = lexical_plan.formatted_query
    query_is_empty = formatted_query == "()"

    effective_sort_by = sort_by
    if query_is_empty and effective_sort_by == "score":
        effective_sort_by = "created_at"

    assert effective_sort_by in FILE_FIELDS or effective_sort_by == "score", (
        f"sort_by must be one of {FILE_FIELDS} or 'score'"
    )
    assert sort_dir in ["DESC", "ASC"], "sort_dir must be 'DESC' or 'ASC'"

    score_field = "paradedb.score(fc.id) AS score, " if not query_is_empty else ""

    if effective_sort_by == "score":
        order_by_field = "ORDER BY score DESC, fc.id ASC"
    else:
        order_by_field = (
            f"ORDER BY {effective_sort_by} {sort_dir}" + (", fc.id ASC" if effective_sort_by != "id" else "")
        )

    where_clause = "f.created_by = :username"
    if not query_is_empty:
        where_clause = f"{where_clause} AND fc.id @@@ paradedb.parse('{formatted_query}')"

    stmt = text(
        f"""
    SELECT fc.id, {score_field}fc.id, fc.text, fc.md, fc.created_at, fc.file_version_id
    FROM {FileChunkTable.__tablename__} fc
    JOIN {FileVersionTable.__tablename__} fv ON fc.file_version_id = fv.id
    JOIN {FileTable.__tablename__} f ON fv.file_id = f.id
    WHERE {where_clause}
    {order_by_field}
    LIMIT :limit
    OFFSET :offset;
    """
    ).bindparams(username=username, limit=limit, offset=offset)

    if return_statement:
        return str(stmt.compile(compile_kwargs={"literal_binds": True}))

    return list(database.exec(stmt))

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import httpx
from sqlmodel import Session

from QueryLake.runtime.authority_projection_access import (
    build_projection_hydration_target,
    hydrate_projection_target,
)
from QueryLake.runtime.projection_registry import get_projection_descriptor
from QueryLake.runtime.retrieval_lane_executors import GoldBM25SearchPlan


OPENSEARCH_TIMEOUT_ENV = "QUERYLAKE_SEARCH_BACKEND_TIMEOUT_SECONDS"
OPENSEARCH_VERIFY_TLS_ENV = "QUERYLAKE_SEARCH_BACKEND_VERIFY_TLS"
OPENSEARCH_URL_ENV = "QUERYLAKE_SEARCH_BACKEND_URL"
OPENSEARCH_INDEX_NAMESPACE_ENV = "QUERYLAKE_SEARCH_INDEX_NAMESPACE"
OPENSEARCH_API_KEY_ENV = "QUERYLAKE_SEARCH_BACKEND_API_KEY"
OPENSEARCH_USERNAME_ENV = "QUERYLAKE_SEARCH_BACKEND_USERNAME"
OPENSEARCH_PASSWORD_ENV = "QUERYLAKE_SEARCH_BACKEND_PASSWORD"
OPENSEARCH_DOCUMENT_CHUNK_INDEX_ENV = "QUERYLAKE_SEARCH_DOCUMENT_CHUNK_INDEX"
OPENSEARCH_FILE_CHUNK_INDEX_ENV = "QUERYLAKE_SEARCH_FILE_CHUNK_INDEX"
OPENSEARCH_SEGMENT_INDEX_ENV = "QUERYLAKE_SEARCH_SEGMENT_INDEX"


def _select_projection_descriptor(
    *,
    projection_descriptors: Sequence[str],
    lane_family: str,
) -> str:
    for projection_id in projection_descriptors:
        descriptor = get_projection_descriptor(str(projection_id))
        if descriptor.lane_family == lane_family:
            return descriptor.projection_id
    available = ", ".join(str(item) for item in projection_descriptors)
    raise AssertionError(
        f"No projection descriptor with lane_family='{lane_family}' was provided. available=[{available}]"
    )

@dataclass(frozen=True)
class OpenSearchHit:
    id: str
    score: float
    source: Dict[str, Any]


def _env_bool(name: str, default: bool) -> bool:
    raw = str(os.getenv(name, str(default))).strip().lower()
    return raw not in {"0", "false", "no", "off"}


def _search_backend_base_url() -> str:
    return str(os.getenv(OPENSEARCH_URL_ENV, "")).rstrip("/")


def _search_backend_index_namespace() -> str:
    return str(os.getenv(OPENSEARCH_INDEX_NAMESPACE_ENV, "")).strip()


def _search_backend_timeout_seconds() -> float:
    raw = str(os.getenv(OPENSEARCH_TIMEOUT_ENV, "10")).strip()
    try:
        return max(1.0, float(raw))
    except Exception:
        return 10.0


def _search_backend_auth_headers() -> Dict[str, str]:
    api_key = str(os.getenv(OPENSEARCH_API_KEY_ENV, "")).strip()
    if len(api_key) > 0:
        return {"Authorization": f"ApiKey {api_key}"}
    return {}


def _search_backend_auth_tuple() -> Optional[Tuple[str, str]]:
    username = str(os.getenv(OPENSEARCH_USERNAME_ENV, "")).strip()
    password = str(os.getenv(OPENSEARCH_PASSWORD_ENV, "")).strip()
    if len(username) > 0 and len(password) > 0:
        return (username, password)
    return None


def build_document_chunk_index_name() -> str:
    explicit = str(os.getenv(OPENSEARCH_DOCUMENT_CHUNK_INDEX_ENV, "")).strip()
    if len(explicit) > 0:
        return explicit
    namespace = _search_backend_index_namespace()
    if len(namespace) == 0:
        raise AssertionError(
            "QUERYLAKE_SEARCH_INDEX_NAMESPACE must be configured for split-stack OpenSearch retrieval."
        )
    return f"{namespace}__document_chunk"


def build_file_chunk_index_name() -> str:
    explicit = str(os.getenv(OPENSEARCH_FILE_CHUNK_INDEX_ENV, "")).strip()
    if len(explicit) > 0:
        return explicit
    namespace = _search_backend_index_namespace()
    if len(namespace) == 0:
        raise AssertionError(
            "QUERYLAKE_SEARCH_INDEX_NAMESPACE must be configured for split-stack OpenSearch retrieval."
        )
    return f"{namespace}__file_chunk"


def build_segment_index_name() -> str:
    explicit = str(os.getenv(OPENSEARCH_SEGMENT_INDEX_ENV, "")).strip()
    if len(explicit) > 0:
        return explicit
    namespace = _search_backend_index_namespace()
    if len(namespace) == 0:
        raise AssertionError(
            "QUERYLAKE_SEARCH_INDEX_NAMESPACE must be configured for split-stack OpenSearch retrieval."
        )
    return f"{namespace}__segment"


def _perform_opensearch_request(
    *,
    index_name: str,
    payload: Dict[str, Any],
    path_suffix: str = "_search",
) -> Dict[str, Any]:
    base_url = _search_backend_base_url()
    assert len(base_url) > 0, "QUERYLAKE_SEARCH_BACKEND_URL must be configured for split-stack OpenSearch retrieval."
    url = f"{base_url}/{index_name}/{path_suffix.lstrip('/')}"
    response = httpx.post(
        url,
        json=payload,
        headers={
            "Content-Type": "application/json",
            **_search_backend_auth_headers(),
        },
        auth=_search_backend_auth_tuple(),
        timeout=_search_backend_timeout_seconds(),
        verify=_env_bool(OPENSEARCH_VERIFY_TLS_ENV, True),
    )
    response.raise_for_status()
    return response.json()


def _extract_hits(payload: Dict[str, Any]) -> List[OpenSearchHit]:
    hits_payload = (((payload or {}).get("hits") or {}).get("hits")) or []
    results: List[OpenSearchHit] = []
    for hit in hits_payload:
        hit_id = str(hit.get("_id") or "")
        if len(hit_id) == 0:
            continue
        results.append(
            OpenSearchHit(
                id=hit_id,
                score=float(hit.get("_score") or 0.0),
                source=dict(hit.get("_source") or {}),
            )
        )
    return results


def _collection_filter(collection_ids: Sequence[str]) -> List[Dict[str, Any]]:
    clean_ids = [str(v) for v in collection_ids if isinstance(v, str) and len(str(v).strip()) > 0]
    if len(clean_ids) == 0:
        return []
    return [{"terms": {"collection_id": clean_ids}}]


def _keyword_sort_field(sort_by: str) -> str:
    if sort_by in {"document_name", "document_id", "collection_id", "website_url", "id"}:
        return f"{sort_by}.keyword" if sort_by != "id" else "id.keyword"
    return sort_by


def build_opensearch_document_chunk_bm25_request(
    *,
    query: str,
    collection_ids: Sequence[str],
    sort_by: str,
    sort_dir: str,
    limit: int,
    offset: int,
) -> Dict[str, Any]:
    clean_query = str(query or "").strip()
    query_is_empty = len(clean_query) == 0 or clean_query == "*"
    if query_is_empty:
        assert sort_by != "score", "Cannot sort by score if no query is specified"
        return {
            "from": int(offset),
            "size": int(limit),
            "_source": False,
            "track_total_hits": False,
            "query": {
                "bool": {
                    "filter": _collection_filter(collection_ids),
                }
            },
            "sort": [
                {_keyword_sort_field(sort_by): {"order": str(sort_dir).lower()}},
                {"id.keyword": {"order": "asc"}},
            ],
        }

    lexical_query = {
        "bool": {
            "filter": _collection_filter(collection_ids),
            "must": [
                {
                    "simple_query_string": {
                        "query": clean_query,
                        "fields": [
                            "text^5",
                            "document_name^2",
                            "document_id",
                            "website_url",
                        ],
                        "default_operator": "and",
                    }
                }
            ],
        }
    }
    payload: Dict[str, Any] = {
        "from": int(offset),
        "size": int(limit),
        "_source": False,
        "track_total_hits": False,
        "query": lexical_query,
    }
    if sort_by == "score":
        payload["sort"] = [{"_score": {"order": str(sort_dir).lower()}}, {"id.keyword": {"order": "asc"}}]
    else:
        payload["sort"] = [
            {_keyword_sort_field(sort_by): {"order": str(sort_dir).lower()}},
            {"id.keyword": {"order": "asc"}},
        ]
    return payload


def build_opensearch_document_chunk_dense_request(
    *,
    embedding: Sequence[float],
    collection_ids: Sequence[str],
    limit: int,
) -> Dict[str, Any]:
    return {
        "size": int(limit),
        "_source": False,
        "track_total_hits": False,
        "query": {
            "bool": {
                "filter": _collection_filter(collection_ids),
                "must": [
                    {
                        "knn": {
                            "embedding": {
                                "vector": list(embedding),
                                "k": int(limit),
                            }
                        }
                    }
                ],
            }
        },
    }


def build_opensearch_file_chunk_bm25_request(
    *,
    username: str,
    query: str,
    sort_by: str,
    sort_dir: str,
    limit: int,
    offset: int,
) -> Tuple[Dict[str, Any], bool]:
    clean_query = str(query or "").strip()
    query_is_empty = len(clean_query) == 0 or clean_query == "*"
    effective_sort_by = "created_at" if query_is_empty and sort_by == "score" else sort_by

    if query_is_empty:
        return (
            {
                "from": int(offset),
                "size": int(limit),
                "_source": False,
                "track_total_hits": False,
                "query": {
                    "bool": {
                        "filter": [{"term": {"created_by.keyword": str(username)}}],
                    }
                },
                "sort": [
                    {_keyword_sort_field(effective_sort_by): {"order": str(sort_dir).lower()}},
                    {"id.keyword": {"order": "asc"}},
                ],
            },
            True,
        )

    payload: Dict[str, Any] = {
        "from": int(offset),
        "size": int(limit),
        "_source": False,
        "track_total_hits": False,
        "query": {
            "bool": {
                "filter": [{"term": {"created_by.keyword": str(username)}}],
                "must": [
                    {
                        "simple_query_string": {
                            "query": clean_query,
                            "fields": ["text^5"],
                            "default_operator": "and",
                        }
                    }
                ],
            }
        },
    }
    if sort_by == "score":
        payload["sort"] = [{"_score": {"order": str(sort_dir).lower()}}, {"id.keyword": {"order": "asc"}}]
    else:
        payload["sort"] = [
            {_keyword_sort_field(effective_sort_by): {"order": str(sort_dir).lower()}},
            {"id.keyword": {"order": "asc"}},
        ]
    return payload, False


def _render_debug_statement(summary: Dict[str, Any]) -> str:
    return json.dumps(summary, indent=2, sort_keys=True)


def execute_opensearch_document_chunk_bm25_search(
    database: Session,
    *,
    projection_id: str,
    query: str,
    collection_ids: Sequence[str],
    sort_by: str,
    sort_dir: str,
    limit: int,
    offset: int,
    return_statement: bool = False,
) -> Tuple[GoldBM25SearchPlan, Union[str, List[Any]]]:
    request_payload = build_opensearch_document_chunk_bm25_request(
        query=query,
        collection_ids=collection_ids,
        sort_by=sort_by,
        sort_dir=sort_dir,
        limit=limit,
        offset=offset,
    )
    index_name = build_document_chunk_index_name()
    if return_statement:
        plan = GoldBM25SearchPlan(
            parse_field=str(query or "").strip() or "()",
            formatted_query=str(query or "").strip() or "()",
            order_by_field=json.dumps(request_payload.get("sort", [])),
            quoted_phrases=tuple(),
        )
        return plan, _render_debug_statement(
            {
                "backend": "opensearch",
                "route": "search_bm25.document_chunk",
                "index": index_name,
                "projection_id": projection_id,
                "request": request_payload,
            }
        )

    response_payload = _perform_opensearch_request(index_name=index_name, payload=request_payload)
    hits = _extract_hits(response_payload)
    hydration_target = build_projection_hydration_target(
        projection_id=projection_id,
        record_ids=[hit.id for hit in hits],
    )
    hydrated = hydrate_projection_target(
        database,
        target=hydration_target,
    )

    rows: List[Any] = []
    for hit in hits:
        hydrated_row = hydrated.get(hit.id)
        if hydrated_row is None:
            continue
        rows.append((hit.id, float(hit.score), *hydrated_row))

    plan = GoldBM25SearchPlan(
        parse_field=str(query or "").strip() or "()",
        formatted_query=str(query or "").strip() or "()",
        order_by_field=json.dumps(request_payload.get("sort", [])),
        quoted_phrases=tuple(),
    )
    return plan, rows


def execute_opensearch_file_chunk_bm25_search(
    database: Session,
    *,
    projection_id: str,
    username: str,
    query: str,
    sort_by: str,
    sort_dir: str,
    limit: int,
    offset: int,
    return_statement: bool = False,
) -> Tuple[bool, Union[str, List[Any]]]:
    request_payload, query_is_empty = build_opensearch_file_chunk_bm25_request(
        username=username,
        query=query,
        sort_by=sort_by,
        sort_dir=sort_dir,
        limit=limit,
        offset=offset,
    )
    index_name = build_file_chunk_index_name()
    if return_statement:
        return query_is_empty, _render_debug_statement(
            {
                "backend": "opensearch",
                "route": "search_file_chunks",
                "index": index_name,
                "projection_id": projection_id,
                "query_is_empty": query_is_empty,
                "request": request_payload,
            }
        )

    response_payload = _perform_opensearch_request(index_name=index_name, payload=request_payload)
    hits = _extract_hits(response_payload)
    hydration_target = build_projection_hydration_target(
        projection_id=projection_id,
        record_ids=[hit.id for hit in hits],
    )
    hydrated = hydrate_projection_target(
        database,
        target=hydration_target,
    )

    rows: List[Any] = []
    for hit in hits:
        hydrated_row = hydrated.get(hit.id)
        if hydrated_row is None:
            continue
        if query_is_empty:
            rows.append((hit.id, *hydrated_row))
        else:
            rows.append((hit.id, float(hit.score), *hydrated_row))
    return query_is_empty, rows


def execute_opensearch_document_chunk_hybrid_search(
    database: Session,
    *,
    projection_descriptors: Sequence[str],
    raw_query_text: str,
    collection_ids: Sequence[str],
    use_bm25: bool,
    use_similarity: bool,
    use_sparse: bool,
    limit_bm25: int,
    limit_similarity: int,
    limit_sparse: int,
    similarity_weight: float,
    bm25_weight: float,
    sparse_weight: float,
    embedding: Sequence[float],
    return_statement: bool = False,
) -> Union[str, List[Any]]:
    assert not use_sparse, "Sparse retrieval is not implemented for the OpenSearch split-stack profile."
    projection_id = _select_projection_descriptor(
        projection_descriptors=projection_descriptors,
        lane_family="dense" if use_similarity else "lexical",
    )
    index_name = build_document_chunk_index_name()
    lexical_payload = None
    dense_payload = None
    lexical_hits: List[OpenSearchHit] = []
    dense_hits: List[OpenSearchHit] = []

    if use_bm25:
        lexical_payload = build_opensearch_document_chunk_bm25_request(
            query=raw_query_text,
            collection_ids=collection_ids,
            sort_by="score",
            sort_dir="DESC",
            limit=int(limit_bm25),
            offset=0,
        )
    if use_similarity:
        dense_payload = build_opensearch_document_chunk_dense_request(
            embedding=embedding,
            collection_ids=collection_ids,
            limit=int(limit_similarity),
        )

    if return_statement:
        return _render_debug_statement(
            {
                "backend": "opensearch",
                "route": "search_hybrid.document_chunk",
                "index": index_name,
                "projection_id": projection_id,
                "lexical_request": lexical_payload,
                "dense_request": dense_payload,
                "fusion": {
                    "bm25_weight": float(bm25_weight),
                    "similarity_weight": float(similarity_weight),
                    "sparse_weight": float(sparse_weight),
                    "rrf_k": 60,
                },
            }
        )

    if lexical_payload is not None:
        lexical_hits = _extract_hits(_perform_opensearch_request(index_name=index_name, payload=lexical_payload))
    if dense_payload is not None:
        dense_hits = _extract_hits(_perform_opensearch_request(index_name=index_name, payload=dense_payload))

    lexical_rank = {hit.id: idx + 1 for idx, hit in enumerate(lexical_hits)}
    dense_rank = {hit.id: idx + 1 for idx, hit in enumerate(dense_hits)}
    ordered_ids: List[str] = []
    seen = set()
    for hit in list(lexical_hits) + list(dense_hits):
        if hit.id in seen:
            continue
        seen.add(hit.id)
        ordered_ids.append(hit.id)
    hydration_target = build_projection_hydration_target(
        projection_id=projection_id,
        record_ids=ordered_ids,
    )
    hydrated = hydrate_projection_target(
        database,
        target=hydration_target,
    )

    scored_rows: List[Tuple[str, float, float, float, float, Tuple[Any, ...]]] = []
    for candidate_id in ordered_ids:
        hydrated_row = hydrated.get(candidate_id)
        if hydrated_row is None:
            continue
        bm25_score = (1.0 / (60.0 + lexical_rank[candidate_id])) if candidate_id in lexical_rank else 0.0
        semantic_score = (1.0 / (60.0 + dense_rank[candidate_id])) if candidate_id in dense_rank else 0.0
        sparse_score_value = 0.0
        total_score = (
            semantic_score * float(similarity_weight)
            + bm25_score * float(bm25_weight)
            + sparse_score_value * float(sparse_weight)
        )
        scored_rows.append(
            (
                candidate_id,
                semantic_score,
                bm25_score,
                sparse_score_value,
                total_score,
                hydrated_row,
            )
        )
    scored_rows = sorted(scored_rows, key=lambda item: (-item[4], str(item[5][-1])))
    return [
        (
            candidate_id,
            semantic_score,
            bm25_score,
            sparse_score_value,
            total_score,
            *hydrated_row,
        )
        for candidate_id, semantic_score, bm25_score, sparse_score_value, total_score, hydrated_row in scored_rows
    ]

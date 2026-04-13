from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

import httpx
from sqlmodel import Session

from QueryLake.runtime.authority_projection_access import (
    DOCUMENT_CHUNK_TUPLE_FIELDS,
    FILE_CHUNK_TUPLE_FIELDS,
    SEGMENT_TUPLE_FIELDS,
    build_projection_materialization_target,
    fetch_projection_materialization_records,
)
from QueryLake.runtime.opensearch_route_execution import (
    _env_bool,
    _search_backend_auth_headers,
    _search_backend_auth_tuple,
    _search_backend_base_url,
    _search_backend_timeout_seconds,
    OPENSEARCH_VERIFY_TLS_ENV,
    build_document_chunk_index_name,
    build_file_chunk_index_name,
    build_segment_index_name,
)
from QueryLake.runtime.projection_writers import ProjectionWriterExecution

OPENSEARCH_DENSE_VECTOR_DIMENSIONS_ENV = "QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS"

# Compatibility wrapper retained because refresh/profile tests and older call sites
# still monkeypatch the writer-local fetch symbol directly. The default implementation
# returns normalized materialization records while still honoring monkeypatches on
# `fetch_projection_materialization_records`.
def fetch_projection_materialization_rows(database, *, target):
    return fetch_projection_materialization_records(database, target=target)


def _row_value(row: Any, key: str, default: Any = None) -> Any:
    if isinstance(row, dict):
        return row.get(key, default)
    return getattr(row, key, default)


def _coerce_row_mapping(row: Any, field_names: Sequence[str]) -> Any:
    if isinstance(row, tuple):
        return dict(zip(field_names, row))
    return row


def _ensure_session(database: Optional[Session]) -> Session:
    assert database is not None, "A SQL authority session is required for OpenSearch projection writing."
    return database


def _perform_opensearch_json_request(
    *,
    method: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    base_url = _search_backend_base_url()
    assert len(base_url) > 0, "QUERYLAKE_SEARCH_BACKEND_URL must be configured for split-stack OpenSearch projection writes."
    url = f"{base_url}/{path.lstrip('/')}"
    response = httpx.request(
        method=str(method).upper(),
        url=url,
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
    if len(response.content or b"") == 0:
        return {}
    return response.json()


def _perform_opensearch_bulk(
    *,
    path: str,
    lines: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    base_url = _search_backend_base_url()
    assert len(base_url) > 0, "QUERYLAKE_SEARCH_BACKEND_URL must be configured for split-stack OpenSearch projection writes."
    url = f"{base_url}/{path.lstrip('/')}"
    bulk_body = "\n".join(json.dumps(line, separators=(",", ":"), sort_keys=True) for line in lines) + "\n"
    response = httpx.post(
        url,
        content=bulk_body.encode("utf-8"),
        headers={
            "Content-Type": "application/x-ndjson",
            **_search_backend_auth_headers(),
        },
        auth=_search_backend_auth_tuple(),
        timeout=_search_backend_timeout_seconds(),
        verify=_env_bool(OPENSEARCH_VERIFY_TLS_ENV, True),
    )
    response.raise_for_status()
    if len(response.content or b"") == 0:
        return {}
    return response.json()


def _dense_vector_dimensions() -> int:
    raw = str(os.getenv(OPENSEARCH_DENSE_VECTOR_DIMENSIONS_ENV, "0")).strip()
    try:
        return max(0, int(raw))
    except Exception:
        return 0


def _document_chunk_index_payload() -> Dict[str, Any]:
    dimensions = _dense_vector_dimensions()
    properties: Dict[str, Any] = {
        "id": {"type": "keyword"},
        "text": {"type": "text"},
        "document_id": {"type": "keyword"},
        "document_name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
        "website_url": {"type": "keyword"},
        "collection_id": {"type": "keyword"},
        "creation_timestamp": {"type": "double"},
        "document_chunk_number": {"type": "integer"},
        "md": {"type": "object", "enabled": False},
        "document_md": {"type": "object", "enabled": False},
    }
    if dimensions > 0:
        properties["embedding"] = {
            "type": "knn_vector",
            "dimension": dimensions,
        }
    return {
        "settings": {
            "index": {
                "knn": True,
            }
        },
        "mappings": {
            "dynamic": False,
            "properties": properties,
        },
    }


def _file_chunk_index_payload() -> Dict[str, Any]:
    return {
        "mappings": {
            "dynamic": False,
            "properties": {
                "id": {"type": "keyword"},
                "text": {"type": "text"},
                "created_by": {"type": "keyword"},
                "collection_id": {"type": "keyword"},
                "file_version_id": {"type": "keyword"},
                "created_at": {"type": "double"},
                "md": {"type": "object", "enabled": False},
            },
        },
    }


def _segment_index_payload() -> Dict[str, Any]:
    dimensions = _dense_vector_dimensions()
    properties: Dict[str, Any] = {
        "id": {"type": "keyword"},
        "text": {"type": "text"},
        "document_id": {"type": "keyword"},
        "document_name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
        "website_url": {"type": "keyword"},
        "collection_id": {"type": "keyword"},
        "created_at": {"type": "double"},
        "segment_type": {"type": "keyword"},
        "segment_index": {"type": "integer"},
        "parent_segment_id": {"type": "keyword"},
        "document_version_id": {"type": "keyword"},
        "md": {"type": "object", "enabled": False},
    }
    if dimensions > 0:
        properties["embedding"] = {
            "type": "knn_vector",
            "dimension": dimensions,
        }
    return {
        "settings": {
            "index": {
                "knn": True,
            }
        },
        "mappings": {
            "dynamic": False,
            "properties": properties,
        },
    }


def _ensure_index(index_name: str, *, payload: Optional[Dict[str, Any]] = None) -> None:
    try:
        _perform_opensearch_json_request(
            method="PUT",
            path=index_name,
            payload=dict(payload or {}),
        )
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code if exc.response is not None else None
        if status_code != 400:
            raise
        try:
            payload = exc.response.json()
        except Exception:
            raise
        error_type = (((payload or {}).get("error") or {}).get("type")) or ""
        if error_type != "resource_already_exists_exception":
            raise


def _clear_index(index_name: str) -> Dict[str, Any]:
    return _perform_opensearch_json_request(
        method="POST",
        path=f"{index_name}/_delete_by_query",
        payload={"query": {"match_all": {}}},
    )
def _document_chunk_to_lexical_doc(row: Any) -> Dict[str, Any]:
    row = _coerce_row_mapping(row, DOCUMENT_CHUNK_TUPLE_FIELDS)
    payload = {
        "id": str(_row_value(row, "id", "") or ""),
        "text": str(_row_value(row, "text", "") or ""),
        "document_id": str(_row_value(row, "document_id", "") or ""),
        "document_name": str(_row_value(row, "document_name", "") or ""),
        "website_url": str(_row_value(row, "website_url", "") or ""),
        "collection_id": str(_row_value(row, "collection_id", "") or ""),
        "creation_timestamp": float(_row_value(row, "creation_timestamp", 0.0) or 0.0),
        "document_chunk_number": int(_row_value(row, "document_chunk_number", 0) or 0),
        "md": dict(_row_value(row, "md", {}) or {}),
        "document_md": dict(_row_value(row, "document_md", {}) or {}),
    }
    row_embedding = _row_value(row, "embedding", None)
    embedding_value = list(row_embedding or []) if row_embedding is not None else []
    dimensions = _dense_vector_dimensions()
    if dimensions > 0 and len(embedding_value) == dimensions:
        payload["embedding"] = embedding_value
    return payload


def _file_chunk_to_lexical_doc(row: Any) -> Dict[str, Any]:
    row = _coerce_row_mapping(row, FILE_CHUNK_TUPLE_FIELDS + ("created_by", "collection_id"))
    return {
        "id": str(_row_value(row, "id", "") or ""),
        "text": str(_row_value(row, "text", "") or ""),
        "md": dict(_row_value(row, "md", {}) or {}),
        "created_at": float(_row_value(row, "created_at", 0.0) or 0.0),
        "file_version_id": str(_row_value(row, "file_version_id", "") or ""),
        "created_by": str(_row_value(row, "created_by", "") or ""),
        "collection_id": str(_row_value(row, "collection_id", "") or ""),
    }


def _segment_to_doc(row: Any) -> Dict[str, Any]:
    row = _coerce_row_mapping(row, SEGMENT_TUPLE_FIELDS)
    payload = {
        "id": str(_row_value(row, "id", "") or ""),
        "text": str(_row_value(row, "text", "") or ""),
        "md": dict(_row_value(row, "md", {}) or {}),
        "created_at": float(_row_value(row, "created_at", 0.0) or 0.0),
        "segment_type": str(_row_value(row, "segment_type", "") or ""),
        "segment_index": int(_row_value(row, "segment_index", 0) or 0),
        "document_version_id": str(_row_value(row, "document_version_id", "") or ""),
        "parent_segment_id": str(_row_value(row, "parent_segment_id", "") or ""),
        "document_id": str(_row_value(row, "document_id", "") or ""),
        "document_name": str(_row_value(row, "document_name", "") or ""),
        "website_url": str(_row_value(row, "website_url", "") or ""),
        "collection_id": str(_row_value(row, "collection_id", "") or ""),
    }
    dense_value = _row_value(row, "embedding", None)
    dense = list(dense_value or []) if dense_value is not None else []
    dimensions = _dense_vector_dimensions()
    if dimensions > 0 and len(dense) == dimensions:
        payload["embedding"] = dense
    return payload


def _bulk_lines_for_index(
    *,
    index_name: str,
    docs: Sequence[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    lines: List[Dict[str, Any]] = []
    for doc in docs:
        document_id = str(doc.get("id") or "")
        if len(document_id) == 0:
            continue
        lines.append({"index": {"_index": index_name, "_id": document_id}})
        lines.append(doc)
    return lines


@dataclass(frozen=True)
class OpenSearchLexicalProjectionWriter:
    writer_id: str
    index_name: str
    source_scope: str
    support_state: str = "supported"
    mode: str = "rebuild"
    implemented: bool = True

    def execute(
        self,
        *,
        database: Optional[Session],
        projection_id: str,
        projection_version: str,
        lane_family: str,
        adapter_backend: str,
        authority_reference: Dict[str, Any],
        request_metadata: Dict[str, Any],
        invalidated_by: list[str],
    ) -> ProjectionWriterExecution:
        db = _ensure_session(database)
        materialization_target = build_projection_materialization_target(
            projection_id=projection_id,
            projection_version=projection_version,
            authority_reference=authority_reference,
            target_backend_name=adapter_backend,
            metadata=dict(request_metadata or {}),
        )
        rows = fetch_projection_materialization_rows(db, target=materialization_target)

        if self.source_scope == "document_chunk":
            docs = [_document_chunk_to_lexical_doc(row) for row in rows]
            index_payload = _document_chunk_index_payload()
        elif self.source_scope == "file_chunk":
            docs = [_file_chunk_to_lexical_doc(row) for row in rows]
            index_payload = _file_chunk_index_payload()
        elif self.source_scope == "segment":
            docs = [_segment_to_doc(row) for row in rows]
            index_payload = _segment_index_payload()
        else:  # pragma: no cover - defensive
            raise AssertionError(f"Unsupported lexical projection source_scope='{self.source_scope}'.")

        _ensure_index(self.index_name, payload=index_payload)
        clear_result = _clear_index(self.index_name)
        bulk_result: Dict[str, Any] = {"errors": False, "items": []}
        lines = _bulk_lines_for_index(index_name=self.index_name, docs=docs)
        if len(lines) > 0:
            bulk_result = _perform_opensearch_bulk(
                path="_bulk",
                lines=lines,
            )
            if bool(bulk_result.get("errors")):
                raise AssertionError(
                    f"OpenSearch bulk indexing reported errors for projection '{projection_id}'."
                )

        build_revision = f"{projection_version}:{lane_family}:{len(docs)}"
        return ProjectionWriterExecution(
            writer_id=self.writer_id,
            implemented=True,
            mode=self.mode,
            build_revision=build_revision,
            metadata={
                "projection_id": projection_id,
                "projection_version": projection_version,
                "lane_family": lane_family,
                "adapter_backend": adapter_backend,
                "authority_reference": dict(authority_reference or {}),
                "materialization_target": materialization_target.model_dump(),
                "request_metadata": dict(request_metadata or {}),
                "invalidated_by": list(invalidated_by),
                "index_name": self.index_name,
                "documents_indexed": len(docs),
                "clear_result": clear_result,
                "bulk_errors": bool(bulk_result.get("errors", False)),
            },
            notes="OpenSearch lexical compatibility projection rebuilt successfully.",
        )


@dataclass(frozen=True)
class OpenSearchDenseProjectionWriter:
    writer_id: str
    index_name: str
    support_state: str = "supported"
    mode: str = "rebuild"
    implemented: bool = True

    def execute(
        self,
        *,
        database: Optional[Session],
        projection_id: str,
        projection_version: str,
        lane_family: str,
        adapter_backend: str,
        authority_reference: Dict[str, Any],
        request_metadata: Dict[str, Any],
        invalidated_by: list[str],
    ) -> ProjectionWriterExecution:
        db = _ensure_session(database)
        materialization_target = build_projection_materialization_target(
            projection_id=projection_id,
            projection_version=projection_version,
            authority_reference=authority_reference,
            target_backend_name=adapter_backend,
            metadata=dict(request_metadata or {}),
        )
        rows = fetch_projection_materialization_rows(db, target=materialization_target)
        docs = [_segment_to_doc(row) if projection_id == "segment_dense_projection_v1" else _document_chunk_to_lexical_doc(row) for row in rows]
        documents_with_dense = sum(1 for doc in docs if "embedding" in doc)
        skipped_missing_dense = len(docs) - documents_with_dense

        index_payload = _segment_index_payload() if projection_id == "segment_dense_projection_v1" else _document_chunk_index_payload()
        _ensure_index(self.index_name, payload=index_payload)
        clear_result = _clear_index(self.index_name)
        bulk_result: Dict[str, Any] = {"errors": False, "items": []}
        lines = _bulk_lines_for_index(index_name=self.index_name, docs=docs)
        if len(lines) > 0:
            bulk_result = _perform_opensearch_bulk(
                path="_bulk",
                lines=lines,
            )
            if bool(bulk_result.get("errors")):
                raise AssertionError(
                    f"OpenSearch bulk indexing reported errors for projection '{projection_id}'."
                )

        build_revision = f"{projection_version}:{lane_family}:{len(docs)}"
        return ProjectionWriterExecution(
            writer_id=self.writer_id,
            implemented=True,
            mode=self.mode,
            build_revision=build_revision,
            metadata={
                "projection_id": projection_id,
                "projection_version": projection_version,
                "lane_family": lane_family,
                "adapter_backend": adapter_backend,
                "authority_reference": dict(authority_reference or {}),
                "materialization_target": materialization_target.model_dump(),
                "request_metadata": dict(request_metadata or {}),
                "invalidated_by": list(invalidated_by),
                "index_name": self.index_name,
                "documents_indexed": len(docs),
                "documents_with_dense_vectors": documents_with_dense,
                "documents_missing_dense_vectors": skipped_missing_dense,
                "clear_result": clear_result,
                "bulk_errors": bool(bulk_result.get("errors", False)),
            },
            notes="OpenSearch dense compatibility projection rebuilt successfully.",
        )


def get_opensearch_lexical_projection_writer(
    *,
    projection_id: str,
) -> OpenSearchLexicalProjectionWriter:
    if projection_id == "document_chunk_lexical_projection_v1":
        return OpenSearchLexicalProjectionWriter(
            writer_id="opensearch.projection_writer.lexical.document_chunk.v1",
            index_name=build_document_chunk_index_name(),
            source_scope="document_chunk",
        )
    if projection_id == "file_chunk_lexical_projection_v1":
        return OpenSearchLexicalProjectionWriter(
            writer_id="opensearch.projection_writer.lexical.file_chunk.v1",
            index_name=build_file_chunk_index_name(),
            source_scope="file_chunk",
        )
    if projection_id == "segment_lexical_projection_v1":
        return OpenSearchLexicalProjectionWriter(
            writer_id="opensearch.projection_writer.lexical.segment.v1",
            index_name=build_segment_index_name(),
            source_scope="segment",
        )
    raise AssertionError(f"No OpenSearch lexical projection writer is registered for projection_id='{projection_id}'.")


def get_opensearch_dense_projection_writer(
    *,
    projection_id: str,
) -> OpenSearchDenseProjectionWriter:
    if projection_id == "document_chunk_dense_projection_v1":
        return OpenSearchDenseProjectionWriter(
            writer_id="opensearch.projection_writer.dense.document_chunk.v1",
            index_name=build_document_chunk_index_name(),
        )
    if projection_id == "segment_dense_projection_v1":
        return OpenSearchDenseProjectionWriter(
            writer_id="opensearch.projection_writer.dense.segment.v1",
            index_name=build_segment_index_name(),
        )
    raise AssertionError(f"No OpenSearch dense projection writer is registered for projection_id='{projection_id}'.")

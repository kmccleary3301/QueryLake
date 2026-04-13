from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence
import re

from sqlmodel import Session

from QueryLake.runtime.authority_projection_access import fetch_projection_materialization_records
from QueryLake.runtime.projection_contracts import (
    DocumentChunkMaterializationRecord,
    FileChunkMaterializationRecord,
    ProjectionMaterializationTarget,
)
from QueryLake.runtime.query_ir_v2 import QueryIRV2


def extract_terms(query: str) -> list[str]:
    lowered = query.lower()
    lowered = re.sub(r'"([^"\\]*(?:\\.[^"\\]*)*)"', " ", lowered)
    return [token for token in re.findall(r"[a-z0-9_]+", lowered) if token not in {"and", "or", "not"}]


def extract_phrases(query: str) -> tuple[str, ...]:
    return tuple(re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"', query)[:4])


def lexical_score(text: str, *, query: str, terms: Sequence[str], phrases: Sequence[str]) -> float:
    lowered = str(text or "").lower()
    if len(lowered.strip()) == 0:
        return 0.0
    score = 0.0
    for phrase in phrases:
        phrase_lower = phrase.lower().strip()
        if phrase_lower and phrase_lower in lowered:
            score += 4.0
    for token in terms:
        if not token:
            continue
        score += float(lowered.count(token))
    if not terms and not phrases and query.strip():
        score += 1.0 if query.lower().strip() in lowered else 0.0
    return score


def _sort_value(value):
    if value is None:
        return ""
    if isinstance(value, dict):
        return str(sorted(value.items()))
    return value


@dataclass(frozen=True)
class LocalLexicalAdapter:
    adapter_id: str = "sqlite_fts5_projection_backed_v1"
    backend_name: str = "sqlite_fts5"
    execution_mode: str = "projection_backed_process_local"

    def search_document_chunks(
        self,
        database: Session,
        *,
        target: ProjectionMaterializationTarget,
        query_ir_v2: QueryIRV2,
        sort_by: str,
        sort_dir: str,
        limit: int,
        offset: int,
    ) -> tuple[list[tuple[DocumentChunkMaterializationRecord, float]], bool]:
        lexical_query = str(query_ir_v2.lexical_query_text or query_ir_v2.normalized_query_text or "")
        query_is_empty = lexical_query.strip() == ""
        terms = extract_terms(lexical_query)
        phrases = extract_phrases(lexical_query)
        chunks = list(fetch_projection_materialization_records(database, target=target))
        scored = [
            (chunk, lexical_score(chunk.text, query=lexical_query, terms=terms, phrases=phrases))
            for chunk in chunks
        ]
        if not query_is_empty:
            scored = [item for item in scored if item[1] > 0.0]
        reverse = str(sort_dir or "DESC").upper() != "ASC"
        if sort_by == "score" and not query_is_empty:
            scored.sort(key=lambda item: (float(item[1]), str(item[0].id or "")), reverse=reverse)
        else:
            scored.sort(
                key=lambda item: (_sort_value(getattr(item[0], sort_by, None)), str(item[0].id or "")),
                reverse=reverse,
            )
        return scored[offset : offset + limit], query_is_empty

    def search_file_chunks(
        self,
        database: Session,
        *,
        target: ProjectionMaterializationTarget,
        query_ir_v2: QueryIRV2,
        sort_by: str,
        sort_dir: str,
        limit: int,
        offset: int,
    ) -> tuple[list[tuple[FileChunkMaterializationRecord, float]], bool]:
        lexical_query = str(query_ir_v2.lexical_query_text or query_ir_v2.normalized_query_text or "")
        query_is_empty = lexical_query.strip() == ""
        terms = extract_terms(lexical_query)
        phrases = extract_phrases(lexical_query)
        chunks = list(fetch_projection_materialization_records(database, target=target))
        scored = [
            (chunk, lexical_score(chunk.text, query=lexical_query, terms=terms, phrases=phrases))
            for chunk in chunks
        ]
        if not query_is_empty:
            scored = [item for item in scored if item[1] > 0.0]
        reverse = str(sort_dir or "DESC").upper() != "ASC"
        if sort_by == "score" and not query_is_empty:
            scored.sort(key=lambda item: (float(item[1]), str(item[0].id or "")), reverse=reverse)
        else:
            scored.sort(
                key=lambda item: (_sort_value(getattr(item[0], sort_by, None)), str(item[0].id or "")),
                reverse=reverse,
            )
        return scored[offset : offset + limit], query_is_empty


LOCAL_LEXICAL_ADAPTER = LocalLexicalAdapter()

# from sentence_transformers import SentenceTransformer
# from sentence_transformers import CrossEncoder
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain.docstore.document import Document
from .text_chunking.character import RecursiveCharacterTextSplitter
from .text_chunking.markdown import MarkdownTextSplitter
from .text_chunking.document_class import Document
# from chromadb.api import ClientAPI
from ..database.sql_db_tables import (
    document_raw,
    DocumentChunk,
    DocumentEmbeddingDictionary,
    document_collection,
    document_version as DocumentVersion,
    document_artifact as DocumentArtifact,
    document_unit_view as DocumentUnitView,
    document_unit as DocumentUnit,
    document_segment_view as DocumentSegmentView,
    document_segment as DocumentSegment,
    document_segment_member as DocumentSegmentMember,
)
from ..api.hashing import random_hash, hash_function
from ..api.single_user_auth import get_user
from typing import List, Callable, Any, Union, Awaitable, Tuple, Literal, Optional, Dict
from numpy import ndarray
import numpy as np
from re import sub, split
from .document_parsing import parse_PDFs
from sqlmodel import Session, select, SQLModel, create_engine, and_, or_, func, not_, update
from ..typing.config import AuthType
import pgvector # Not sure exactly how the import works here, but it's necessary for sqlmodel queries.
from time import time
from io import BytesIO
import re
from itertools import chain
import json
import bisect
from ..database.create_db_session import initialize_database_engine
from ..database.create_db_session import configured_sparse_index_dimensions
from .sparse_projection import (
    SparseDimensionMismatchError,
    project_sparse_mapping,
    project_sparse_vector,
)
from ..typing.api_inputs import TextChunks
import logging
from ..observability import metrics
from ..runtime.ingestion_dual_write import dual_write_segments_enabled
from ..runtime.content_fingerprint import content_fingerprint
from ..runtime.embedding_records import (
    embedding_record_enabled,
    embedding_record_model_id,
    get_or_create_embedding_async,
)

logger = logging.getLogger(__name__)

DEFAULT_LOCAL_TEXT_VIEW_ALIAS = "default_local_text"
LEGACY_LOCAL_TEXT_RECIPE_ID = "legacy_local_text_v1"
LEGACY_UNIT_RECIPE_ID = "legacy_parser_units_v1"


def binary_search(sorted_list, target):
	index = bisect.bisect_right(sorted_list, target)
	index = min(max(0, index), len(sorted_list)-1)
	value = sorted_list[index]
	while value > target and index > 0:
		if value > target:
			index = max(0, index-1)
		value = sorted_list[index]
	return index
# from sqlmodel import Session, SQLModel, create_engine, select


# model = SentenceTransformer('BAAI/bge-large-en-v1.5')
# reranker_ce = CrossEncoder('BAAI/bge-reranker-base')
# model_collection_name = "bge-large-en-v1-5"

def split_list(input_list : list, n : int) -> List[list]:
    """
    Evenly split a list into `n` sublists of approximately equal length.
    """
    if n <= 0:
        return [input_list]
    k, m = divmod(len(input_list), n)
    return [input_list[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)]


def _extract_dense_embedding(payload: Any) -> Optional[List[float]]:
    value = payload
    if isinstance(value, dict):
        for key in ["embedding", "dense", "dense_embedding", "dense_vec", "dense_vecs"]:
            if key in value:
                value = value[key]
                break
    if value is None:
        return None
    if isinstance(value, ndarray):
        value = value.tolist()
    if isinstance(value, tuple):
        value = list(value)
    if isinstance(value, list):
        try:
            return [float(x) for x in value]
        except Exception:
            return None
    return None


def _extract_sparse_embedding(
    payload: Any,
    dimensions: int = 1024,
    *,
    strict_dimensions: bool = False,
    source_label: str = "sparse_embedding",
):
    value = payload
    if isinstance(value, dict):
        sparse_key_found = False
        for key in [
            "sparse",
            "sparse_embedding",
            "sparse_vec",
            "sparse_vecs",
            "lexical_weights",
            "weights",
            "sparse_weights",
        ]:
            if key in value:
                value = value[key]
                sparse_key_found = True
                break
        if not sparse_key_found:
            dense_fallback = _extract_dense_embedding(value)
            if dense_fallback is not None:
                value = dense_fallback
    if value is None:
        return None

    try:
        if isinstance(value, pgvector.SparseVector):
            return project_sparse_vector(
                value,
                dimensions,
                strict_dimensions=strict_dimensions,
                source_label=source_label,
            )

        # Allow callers to pass pgvector literal directly.
        if isinstance(value, str):
            parsed = pgvector.SparseVector.from_text(value)
            return project_sparse_vector(
                parsed,
                dimensions,
                strict_dimensions=strict_dimensions,
                source_label=source_label,
            )

        if isinstance(value, ndarray):
            value = value.tolist()

        # Common schema: {"indices":[...], "values":[...], "dimensions":N}
        if isinstance(value, dict) and "indices" in value and "values" in value:
            idxs = value.get("indices") or []
            vals = value.get("values") or []
            dim = int(value.get("dimensions", dimensions))
            if strict_dimensions and dim != dimensions:
                raise SparseDimensionMismatchError(
                    f"Sparse dimension mismatch for {source_label}: expected {dimensions}, observed {dim}"
                )
            mapping = {}
            for idx, val in zip(idxs, vals):
                if val is None:
                    continue
                mapping[int(idx)] = float(val)
            projected = project_sparse_mapping(
                mapping,
                dimensions,
                strict_dimensions=False,
                source_label=source_label,
            )
            return pgvector.SparseVector(projected, dimensions)

        if isinstance(value, dict):
            mapping = project_sparse_mapping(
                value,
                dimensions,
                strict_dimensions=False,
                source_label=source_label,
            )
            return pgvector.SparseVector(mapping, dimensions)

        # Dense vector input fallback; compress non-zero entries.
        if isinstance(value, list):
            if strict_dimensions and len(value) > 0 and len(value) != dimensions:
                raise SparseDimensionMismatchError(
                    f"Sparse dimension mismatch for {source_label}: expected {dimensions}, observed {len(value)}"
                )
            mapping = {}
            for idx, weight in enumerate(value):
                try:
                    val = float(weight)
                except Exception:
                    continue
                if val != 0.0:
                    mapping[idx] = val
            projected = project_sparse_mapping(
                mapping,
                dimensions,
                strict_dimensions=False,
                source_label=source_label,
            )
            return pgvector.SparseVector(projected, dimensions)
    except SparseDimensionMismatchError:
        raise
    except Exception:
        return None

    return None


def _config_hash(payload: Dict[str, Any], *, salt: str) -> str:
    return content_fingerprint(text="", md=payload, salt=salt)


def _infer_unit_contract(metadata: Optional[Dict[str, Any]]) -> Tuple[str, Optional[str], Dict[str, Any]]:
    md = metadata if isinstance(metadata, dict) else {}
    if "page" in md:
        payload = {"page": md.get("page")}
        for key in ("location_link_firefox", "location_link_chrome"):
            if key in md:
                payload[key] = md.get(key)
        return "pdf_text_fragment", "page_ref", payload
    if "line" in md:
        return "source_line", "line_ref", {"line": md.get("line")}
    return "provided_text_chunk", None, {}


def _infer_collection_unit_kind(text_segments: List[Tuple[str, dict]]) -> str:
    kinds = {
        _infer_unit_contract(metadata if isinstance(metadata, dict) else {})[0]
        for _, metadata in text_segments
    }
    if len(kinds) == 1:
        return list(kinds)[0]
    return "provided_text_chunk"


def _build_units_from_text_segments(
    *,
    document_version_id: str,
    artifact_id: str,
    text_segments: List[Tuple[str, dict]],
) -> Tuple[DocumentUnitView, List[DocumentUnit], List[Tuple[int, int]]]:
    unit_kind = _infer_collection_unit_kind(text_segments)
    view_config = {"unit_kind": unit_kind, "unit_count": len(text_segments)}
    unit_view = DocumentUnitView(
        document_version_id=document_version_id,
        artifact_id=artifact_id,
        unit_kind=unit_kind,
        recipe_id=LEGACY_UNIT_RECIPE_ID,
        recipe_version="v1",
        config_hash=_config_hash(view_config, salt="document_unit_view"),
        status="ready",
        config=view_config,
        stats={"unit_count": len(text_segments)},
    )

    units: List[DocumentUnit] = []
    spans: List[Tuple[int, int]] = []
    cursor = 0
    for idx, (text_value, metadata) in enumerate(text_segments):
        md = metadata if isinstance(metadata, dict) else {}
        _, anchor_type, anchor_payload = _infer_unit_contract(md)
        unit_text = str(text_value or "")
        units.append(
            DocumentUnit(
                unit_view_id=unit_view.id,
                unit_index=idx,
                text=unit_text,
                md=dict(md),
                anchor_type=anchor_type,
                anchor_payload=anchor_payload,
            )
        )
        start = cursor
        end = start + len(unit_text)
        spans.append((start, end))
        cursor = end + 1  # synthetic newline join
    return unit_view, units, spans


def _derive_segment_member_records(
    *,
    split_text: str,
    split_md: Dict[str, Any],
    units: List[DocumentUnit],
    unit_spans: List[Tuple[int, int]],
    segment_id: str,
) -> Tuple[List[DocumentSegmentMember], Dict[str, Any], Dict[str, Any]]:
    start_index = int(split_md.get("start_index", 0) or 0)
    end_index = start_index + len(split_text)
    members: List[DocumentSegmentMember] = []
    first_idx = None
    last_idx = None
    pages: List[int] = []
    lines: List[int] = []

    for unit, (unit_start, unit_end) in zip(units, unit_spans):
        if unit_end <= start_index:
            continue
        if unit_start >= end_index:
            break
        overlap_start = max(start_index, unit_start)
        overlap_end = min(end_index, unit_end)
        if overlap_end <= overlap_start:
            continue
        members.append(
            DocumentSegmentMember(
                segment_id=segment_id,
                unit_id=unit.id,
                member_index=len(members),
                role="main",
                unit_start_char=overlap_start - unit_start,
                unit_end_char=overlap_end - unit_start,
            )
        )
        first_idx = unit.unit_index if first_idx is None else first_idx
        last_idx = unit.unit_index
        unit_md = unit.md if isinstance(unit.md, dict) else {}
        if "page" in unit_md:
            try:
                pages.append(int(unit_md["page"]))
            except Exception:
                pass
        if "line" in unit_md:
            try:
                lines.append(int(unit_md["line"]))
            except Exception:
                pass

    derived_md: Dict[str, Any] = {
        "source_unit_start_index": int(first_idx or 0),
        "source_unit_end_index": int(last_idx or 0),
        "source_unit_count": len(members),
        "content_fingerprint": content_fingerprint(text=split_text, md={"member_count": len(members)}),
    }
    if pages:
        derived_md["page"] = int(pages[0])
        derived_md["page_start"] = int(min(pages))
        derived_md["page_end"] = int(max(pages))
    if lines:
        derived_md["line"] = int(lines[0])
        derived_md["line_start"] = int(min(lines))
        derived_md["line_end"] = int(max(lines))

    first_unit_md = dict(units[first_idx].md) if first_idx is not None and isinstance(units[first_idx].md, dict) else {}
    chunk_md = {**first_unit_md, **derived_md}
    return members, derived_md, chunk_md


def build_legacy_local_text_segments_from_units(
    *,
    document_version_id: str,
    artifact_id: str,
    text_segments: List[Tuple[str, dict]],
    text_splitter: MarkdownTextSplitter,
) -> Tuple[DocumentUnitView, List[DocumentUnit], DocumentSegmentView, List[DocumentSegment], List[DocumentSegmentMember], List[Dict[str, Any]]]:
    unit_view, units, unit_spans = _build_units_from_text_segments(
        document_version_id=document_version_id,
        artifact_id=artifact_id,
        text_segments=text_segments,
    )
    created_document = "\n".join([unit.text for unit in units])
    split_docs = text_splitter.split_documents([Document(page_content=created_document, metadata={})])
    view_config = {
        "chunk_size": int(text_splitter._chunk_size),
        "chunk_overlap": int(text_splitter._chunk_overlap),
        "unit_kind": unit_view.unit_kind,
    }
    segment_view = DocumentSegmentView(
        document_version_id=document_version_id,
        source_unit_view_id=unit_view.id,
        view_alias=DEFAULT_LOCAL_TEXT_VIEW_ALIAS,
        recipe_id=LEGACY_LOCAL_TEXT_RECIPE_ID,
        recipe_version="v1",
        config_hash=_config_hash(view_config, salt="document_segment_view"),
        segment_type_default="chunk",
        status="ready",
        is_current=True,
        config=view_config,
        stats={"unit_count": len(units), "segment_count": len(split_docs)},
    )
    segments: List[DocumentSegment] = []
    members_all: List[DocumentSegmentMember] = []
    chunk_payloads: List[Dict[str, Any]] = []

    for idx, split_doc in enumerate(split_docs):
        split_md = dict(split_doc.metadata if isinstance(split_doc.metadata, dict) else {})
        segment_row = DocumentSegment(
            document_version_id=document_version_id,
            artifact_id=artifact_id,
            segment_view_id=segment_view.id,
            segment_type="chunk",
            segment_index=idx,
            text=split_doc.page_content,
            md={},
        )
        members, segment_md, chunk_md = _derive_segment_member_records(
            split_text=split_doc.page_content,
            split_md=split_md,
            units=units,
            unit_spans=unit_spans,
            segment_id=segment_row.id,
        )
        segment_row.md = segment_md
        segments.append(segment_row)
        members_all.extend(members)
        chunk_payloads.append(
            {
                "segment_id": segment_row.id,
                "segment_index": idx,
                "text": split_doc.page_content,
                "segment_md": segment_md,
                "chunk_md": chunk_md,
            }
        )
    return unit_view, units, segment_view, segments, members_all, chunk_payloads

async def chunk_documents(toolchain_function_caller: Callable[[Any], Union[Callable, Awaitable[Callable]]],
                          database : Session,
                          auth : AuthType,
                          document_db_entries: List[Union[str, document_raw]],
                          document_names : List[str],
                          document_bytes_list : List[bytes] = None, 
                          document_texts : List[Union[str, List[TextChunks]]] = None,
                          document_metadata : List[Union[dict, Literal[None]]] = None,
                          create_embeddings : bool = True,
                          create_sparse_embeddings: bool = False,
                          sparse_embedding_function: str = "embedding_sparse",
                          sparse_embedding_dimensions: int = 1024,
                          enforce_sparse_dimension_match: bool = True):
    """
    Add document batch to postgres vector database using embeddings.
    
    Returns: A dictionary breaking down time spent on different tasks.
    
    Named keys:
        - "chunking"
        - "embedding"
        - "database_add"
        - "total"
    """
    start_time = time()
    
    assert not document_bytes_list is None or not document_texts is None, "Either document_bytes_list or document_texts must be provided."
    
    if not document_bytes_list is None:
        assert len(document_db_entries) == len(document_bytes_list) and len(document_db_entries) == len(document_names),\
            "Length of document_bytes_list, document_db_entries, and document_names must be the same."
    else:
        assert len(document_db_entries) == len(document_texts) and len(document_db_entries) == len(document_names),\
            "Length of document_texts, document_db_entries, and document_names must be the same."

    text_segment_collections = []
    real_db_entries = []
    
    # db_2, engine_2 = initialize_database_engine()
    
    for i in range(len(document_db_entries)):
        
        document_db_entry = document_db_entries[i]
        document_name = document_names[i]
        
        if isinstance(document_db_entry, str):
            document_db_entry : document_raw = database.exec(select(document_raw).where(document_raw.id == document_db_entry)).first()
            assert not document_db_entry is None, "Document not found in database."
        
        assert isinstance(document_db_entry, document_raw), "Document returned is not type `document_raw`."
        real_db_entries.append(document_db_entry)
        
        file_extension = document_name.split(".")[-1].lower()
        
        if document_texts is None:
            document_bytes = document_bytes_list[i]
            assert isinstance(document_bytes, bytes), "Document bytes must be a bytes object."
            
            if file_extension in ["pdf"]:
                text_chunks = parse_PDFs(document_bytes)
            elif file_extension in ["txt", "md", "json"]:
                text = document_bytes.decode("utf-8").split("\n")
                text_chunks = list(map(lambda i: (text[i], {"line": i}), list(range(len(text)))))
            else:
                raise ValueError(f"File extension `{file_extension}` not supported for scanning, only [pdf, txt, md, json] are supported at this time.")
        else:
            if isinstance(document_texts[i], str):
                text = document_texts[i].split("\n")
                text_chunks : List[Tuple[str, dict]] = list(map(lambda i: (
                    text[i], {"line": i}
                ), list(range(len(text)))))
            elif isinstance(document_texts[i], list) and all([isinstance(e, TextChunks) for e in document_texts[i]]):
                text_chunks : List[Tuple[str, dict]] = list(map(lambda x: (
                    x.text, x.metadata if not x.metadata is None else {}
                ), document_texts[i]))
            else:
                raise ValueError(f"Document text must be a string or a list of TextChunks.")

        text_segment_collections.append(text_chunks)
    
    if document_metadata is None:
        document_metadata = [None]*len(document_db_entries)
    # try:
    time_dict = await create_text_chunks(database, auth, toolchain_function_caller, text_segment_collections, 
                            real_db_entries, document_names, document_metadata=document_metadata,
                            create_embeddings=create_embeddings,
                            create_sparse_embeddings=create_sparse_embeddings,
                            sparse_embedding_function=sparse_embedding_function,
                            sparse_embedding_dimensions=sparse_embedding_dimensions,
                            enforce_sparse_dimension_match=enforce_sparse_dimension_match)
    
    time_dict["total"] = time() - start_time
    
    return time_dict


async def create_text_chunks(database : Session,
                             auth : AuthType,
                             toolchain_function_caller: Callable[[Any], Union[Callable, Awaitable[Callable]]],
                             text_segment_collections : List[List[Tuple[str, dict]]],
                             document_sql_entries : List[document_raw], 
                             document_names: List[str],
                             document_metadata : List[Union[dict, Literal[None]]],
                             create_embeddings : bool = True,
                             create_sparse_embeddings: bool = False,
                             sparse_embedding_function: str = "embedding_sparse",
                             sparse_embedding_dimensions: int = 1024,
                             enforce_sparse_dimension_match: bool = True):
    """
    Given a set of text chunks, possibly pairs with metadata, create embeddings for the
    entries. Craft an entry in the vector db, using the collection relevant to the
    model used. Each entry into the vector db will have the following metadata:

    collection_type - whether the parent collection is an org, user, or global collection.
    public - bool for if this is public or not.
    parent_collection_id - sql db hash id for the parent collection
    document_id - sql db hash id for the parent document.
    page - what page of the original document the chunk is from.
    document_name - name of the original document.
    
    Returns: A dictionary breaking down time spent on different tasks.
    
    Named keys:
        - "chunking"
        - "embedding"
        - "database_add"
        - "total"
    """

    time_dict = {
        "chunking": 0,
        "embedding": 0,
        "embedding_sparse": 0,
        "database_add": 0,
        "misc": 0
    }
    start_time = time()
    
    assert len(text_segment_collections) == len(document_sql_entries) and len(text_segment_collections) == len(document_names),\
        "Length of text_segment_collections, document_sql_entries, and document_names must be the same."
    assert isinstance(sparse_embedding_dimensions, int) and sparse_embedding_dimensions > 0, \
        "sparse_embedding_dimensions must be a positive integer"
    configured_sparse_dims = configured_sparse_index_dimensions()
    if create_sparse_embeddings and enforce_sparse_dimension_match and int(sparse_embedding_dimensions) != int(configured_sparse_dims):
        raise SparseDimensionMismatchError(
            "Sparse embedding dimensions do not match configured sparse index dimensions: "
            f"expected={configured_sparse_dims} (QUERYLAKE_SPARSE_INDEX_DIMENSIONS), "
            f"requested={int(sparse_embedding_dimensions)}, function={sparse_embedding_function}"
        )

    chunk_size = 1200
    chunk_overlap = 100
    text_splitter = MarkdownTextSplitter( # Same implemetation as LangChain
        chunk_size=chunk_size, 
        chunk_overlap=chunk_overlap,
        add_start_index=True
    )
    
    embedding_call : Awaitable[Callable] = toolchain_function_caller("embedding")
    sparse_embedding_call = None
    if create_sparse_embeddings:
        try:
            sparse_embedding_call = toolchain_function_caller(sparse_embedding_function)
        except Exception:
            if sparse_embedding_function != "embedding":
                try:
                    sparse_embedding_call = toolchain_function_caller("embedding")
                    logger.warning(
                        "Sparse embedding function '%s' unavailable; using dense embedding function for sparse extraction.",
                        sparse_embedding_function,
                    )
                except Exception:
                    sparse_embedding_call = None
            if sparse_embedding_call is None:
                logger.warning(
                    "Sparse embedding disabled because no sparse embedding function was resolved (%s).",
                    sparse_embedding_function,
                )
                create_sparse_embeddings = False
    use_embedding_records = bool(create_embeddings and embedding_record_enabled())
    use_dual_write_segments = bool(dual_write_segments_enabled() or use_embedding_records)
    embedding_model_id = embedding_record_model_id()
    
    collection = database.exec(select(document_collection).where(document_collection.id == document_sql_entries[0].document_collection_id)).first()
    assert not collection is None, "Collection not found."
    collection_type = collection.collection_type
    parent_collection_id = collection.id
    
    split_collections = []
    
    chunking_start_time = time()
    
    for i in range(len(text_segment_collections)):
        document_sql_entry = document_sql_entries[i]
        text_segments = text_segment_collections[i]
        document_name = document_names[i]
        
        # We are assuming an input of tuples with text and metadata.
        # We do this to keep track of location/ordering metadata such as page number.
        # This code concatenates the text and allows us to recover the minimum location index
        # After splitting for embedding.
        
        created_document = "\n".join([chunk[0] for chunk in text_segments])
        
        m_1 = time()
        doc_markers, current_sum = [], 0
        for i in range(len(text_segments)):
            doc_markers.append(current_sum)
            current_sum += len(text_segments[i][0]) + 1
        
        splits = text_splitter.split_documents([Document(page_content=created_document, metadata={})])
        splits = list(map(lambda x: Document(
            page_content=x.page_content,
            metadata={**text_segments[binary_search(doc_markers, x.metadata["start_index"])][1]}
        ), splits))
        m_2 = time() - m_1
        if m_2 > 1:
            logger.debug(
                "Chunked %s segments into embeddings in %.2fs",
                len(text_segments),
                m_2,
            )
        split_collections.append(splits)
    
    
    embeddings_all, embeddings_iterable = None, 0
    sparse_embeddings_iterable = 0
    sparse_embeddings_all = None
    embedding_record_hits, embedding_record_misses = 0, 0
    
    flattened_splits = list([e.page_content for e in chain.from_iterable(split_collections)])
    
    time_dict["chunking"] = time() - chunking_start_time
    embedding_start_time = time()
    
    if create_embeddings and not use_embedding_records:
        try:
            embeddings_all_raw = await embedding_call(auth, flattened_splits)
            embeddings_all = [_extract_dense_embedding(item) for item in embeddings_all_raw]
        except Exception:
            logger.exception("Embedding call failed; continuing without embeddings.")
            create_embeddings = False
            embeddings_all = None
    
    time_dict["embedding"] = time() - embedding_start_time

    sparse_embedding_start_time = time()
    if create_sparse_embeddings and sparse_embedding_call is not None:
        try:
            sparse_embeddings_raw = await sparse_embedding_call(auth, flattened_splits)
            sparse_embeddings_all = [
                _extract_sparse_embedding(
                    item,
                    sparse_embedding_dimensions,
                    strict_dimensions=bool(enforce_sparse_dimension_match),
                    source_label=f"{sparse_embedding_function}[{i}]",
                )
                for i, item in enumerate(sparse_embeddings_raw)
            ]
        except SparseDimensionMismatchError:
            raise
        except Exception:
            logger.exception("Sparse embedding call failed; continuing without sparse embeddings.")
            create_sparse_embeddings = False
            sparse_embeddings_all = None
    time_dict["embedding_sparse"] = time() - sparse_embedding_start_time
    
    db_additions, segment_additions, document_md_lookup = [], [], {}
    unit_view_additions: List[DocumentUnitView] = []
    unit_additions: List[DocumentUnit] = []
    segment_view_additions: List[DocumentSegmentView] = []
    segment_member_additions: List[DocumentSegmentMember] = []
    
    db_add_start_time = time()
    
    for i, doc in enumerate(document_sql_entries):
        document_md_lookup[doc.id] = document_metadata[i]
    
    db_additions = []
    segment_additions = []
    docs_to_finish_3, docs_to_finish_4 = [], []

    async def _embed_single(text_value: str) -> List[float]:
        result = await embedding_call(auth, [text_value])
        dense = _extract_dense_embedding(result[0]) if len(result) > 0 else None
        assert dense is not None, "Dense embedding function did not return a valid embedding payload"
        return dense

    def _ensure_version_and_artifact(document_sql_entry: document_raw):
        version = database.exec(
            select(DocumentVersion)
            .where(DocumentVersion.document_id == document_sql_entry.id)
            .order_by(DocumentVersion.version_no.desc())
            .limit(1)
        ).first()
        if version is None:
            version = DocumentVersion(
                document_id=document_sql_entry.id,
                version_no=1,
                content_hash=document_sql_entry.integrity_sha256,
                status="ready",
                md={"source": "chunk_documents"},
            )
            database.add(version)
            database.commit()
            database.refresh(version)

        artifact = database.exec(
            select(DocumentArtifact)
            .where(DocumentArtifact.document_version_id == version.id)
            .order_by(DocumentArtifact.created_at.desc())
            .limit(1)
        ).first()
        if artifact is None:
            artifact = DocumentArtifact(
                document_version_id=version.id,
                artifact_type="source_blob",
                storage_ref=f"{document_sql_entry.blob_id}:{document_sql_entry.blob_dir}",
                md={"source": "chunk_documents"},
            )
            database.add(artifact)
            database.commit()
            database.refresh(artifact)
        return version.id, artifact.id

    for seg_i in range(len(text_segment_collections)):
        document_sql_entry = document_sql_entries[seg_i]
        text_segments = text_segment_collections[seg_i]
        document_name = document_names[seg_i]
        splits : List[Document] = split_collections[seg_i]
        current_split_size = len(splits)
        document_metadata = document_md_lookup[document_sql_entry.id]
        version_id, artifact_id = (None, None)
        canonical_chunk_payloads: Optional[List[Dict[str, Any]]] = None
        canonical_segment_rows: Dict[str, DocumentSegment] = {}
        if use_dual_write_segments:
            version_id, artifact_id = _ensure_version_and_artifact(document_sql_entry)
            (
                unit_view_row,
                unit_rows,
                segment_view_row,
                canonical_segment_rows_list,
                segment_member_rows,
                canonical_chunk_payloads,
            ) = build_legacy_local_text_segments_from_units(
                document_version_id=version_id,
                artifact_id=artifact_id,
                text_segments=text_segments,
                text_splitter=text_splitter,
            )
            assert len(canonical_chunk_payloads) == current_split_size, (
                "Canonical segment build diverged from legacy split count. "
                f"expected={current_split_size}, actual={len(canonical_chunk_payloads)}"
            )
            canonical_segment_rows = {row.id: row for row in canonical_segment_rows_list}
            if use_embedding_records:
                database.add(unit_view_row)
                database.add_all(unit_rows)
                database.add(segment_view_row)
                database.add_all(canonical_segment_rows_list)
                database.add_all(segment_member_rows)
                database.commit()
            else:
                unit_view_additions.append(unit_view_row)
                unit_additions.extend(unit_rows)
                segment_view_additions.append(segment_view_row)
                segment_additions.extend(canonical_segment_rows_list)
                segment_member_additions.extend(segment_member_rows)
        
        embeddings = None
        if create_embeddings and not use_embedding_records:
            embeddings = embeddings_all[embeddings_iterable:embeddings_iterable+current_split_size]
        sparse_embeddings = None
        if create_sparse_embeddings and sparse_embeddings_all is not None:
            sparse_embeddings = sparse_embeddings_all[sparse_embeddings_iterable:sparse_embeddings_iterable+current_split_size]
        
        had_embeddings = False
        for i, chunk in enumerate(splits):
            chunk_md = dict(chunk.metadata if isinstance(chunk.metadata, dict) else {})
            assert isinstance(chunk_md, dict), "Metadata must be a dictionary."
            parent_doc_md = document_sql_entry.md
            assert isinstance(parent_doc_md, dict), "Parent document metadata must be a dictionary."
            document_md_make = {
                **(document_metadata if not document_metadata is None else {}),
                **parent_doc_md,
            }
            segment_md = {
                "collection_id": parent_collection_id,
                "document_name": document_name,
                **chunk_md,
            }
            segment_id_for_chunk = DocumentSegment().id
            segment_row = None
            if use_dual_write_segments and canonical_chunk_payloads is not None:
                canonical_payload = canonical_chunk_payloads[i]
                segment_id_for_chunk = str(canonical_payload["segment_id"])
                segment_md = {
                    "collection_id": parent_collection_id,
                    "document_name": document_name,
                    **dict(canonical_payload.get("segment_md") or {}),
                }
                chunk_md = dict(canonical_payload.get("chunk_md") or {})
                segment_row = canonical_segment_rows.get(segment_id_for_chunk)

            embedding_value = None
            if create_embeddings:
                if use_embedding_records:
                    embedding_record = await get_or_create_embedding_async(
                        database,
                        segment_id=segment_id_for_chunk,
                        text=chunk.page_content,
                        model_id=embedding_model_id,
                        embedding_fn=_embed_single,
                        md={"source": "create_text_chunks"},
                    )
                    embedding_value = embedding_record["embedding"]
                    if embedding_record["cache_hit"]:
                        embedding_record_hits += 1
                        metrics.record_retrieval_cache("embedding_record", "hit")
                    else:
                        embedding_record_misses += 1
                        metrics.record_retrieval_cache("embedding_record", "miss")
                    if segment_row is not None:
                        segment_row.embedding = embedding_value
                        database.add(segment_row)
                        database.commit()
                else:
                    embedding_value = embeddings[i] if embeddings is not None else None

            sparse_embedding_value = None
            if create_sparse_embeddings and sparse_embeddings is not None:
                sparse_embedding_value = sparse_embeddings[i]
                if segment_row is not None and sparse_embedding_value is not None:
                    segment_row.embedding_sparse = sparse_embedding_value

            had_embeddings = had_embeddings or (embedding_value is not None) or (sparse_embedding_value is not None)
            
            embedding_db_entry = DocumentChunk(
                # collection_type=collection_type,
                document_id=document_sql_entry.id,
                authority_segment_id=segment_id_for_chunk if use_dual_write_segments else None,
                document_chunk_number=i,
                collection_id=parent_collection_id,
                collection_type=collection_type,
                document_name=document_name,
                document_integrity=document_sql_entry.integrity_sha256,
                md=chunk_md,
                document_md=document_md_make,
                text=chunk.page_content,
                **({"website_url": document_sql_entry.website_url} if not document_sql_entry.website_url is None else {}),
                **({"embedding": embedding_value} if not embedding_value is None else {}),
                **({"embedding_sparse": sparse_embedding_value} if not sparse_embedding_value is None else {}),
            )
            db_additions.append(embedding_db_entry)
            if use_dual_write_segments and not use_embedding_records and segment_row is not None:
                if embedding_value is not None:
                    segment_row.embedding = embedding_value
                if sparse_embedding_value is not None:
                    segment_row.embedding_sparse = sparse_embedding_value
        
        if not had_embeddings:
            docs_to_finish_3.append(document_sql_entry.id)
        else:
            docs_to_finish_4.append(document_sql_entry.id)
        if not use_embedding_records:
            embeddings_iterable += current_split_size
        if create_sparse_embeddings:
            sparse_embeddings_iterable += current_split_size
    
    if len(unit_view_additions) > 0:
        database.add_all(unit_view_additions)
        database.commit()
    if len(unit_additions) > 0:
        database.add_all(unit_additions)
        database.commit()
    if len(segment_view_additions) > 0:
        database.add_all(segment_view_additions)
        database.commit()
    if len(segment_additions) > 0:
        database.add_all(segment_additions)
        database.commit()
    if len(segment_member_additions) > 0:
        database.add_all(segment_member_additions)
    if len(db_additions) > 0:
        database.add_all(db_additions)

    if len(docs_to_finish_3) > 0:
        stmt = update(document_raw).where(document_raw.id.in_(docs_to_finish_3)).values(finished_processing=3)
        database.exec(stmt)
    
    if len(docs_to_finish_4) > 0:
        stmt = update(document_raw).where(document_raw.id.in_(docs_to_finish_4)).values(finished_processing=4)
        database.exec(stmt)
    
    database.commit()

    if use_embedding_records:
        total_record_events = embedding_record_hits + embedding_record_misses
        time_dict["embedding_record"] = {
            "enabled": True,
            "model_id": embedding_model_id,
            "hits": embedding_record_hits,
            "misses": embedding_record_misses,
            "hit_rate": (float(embedding_record_hits) / float(total_record_events) if total_record_events > 0 else 0.0),
        }
    
    time_dict["database_add"] = time() - db_add_start_time
    time_dict["total"] = time() - start_time
    
    return time_dict

async def create_website_embeddings(database : Session, 
                                    auth : AuthType,
                                    toolchain_function_caller: Callable[[Any], Union[Callable, Awaitable[Callable]]],
                                    url_content_pairs : list):
    """
    Given a set of text chunks, possibly pairs with metadata, create embeddings for the
    entries. Craft an entry in the chroma db, using the collection relevant to the
    model used. Each entry into the chroma db will have the following metadata:

    collection_type - whether the parent collection is an org, user, or global collection.
    public - bool for if this is public or not.
    parent_collection_id - sql db hash id for the parent collection
    document_id - sql db hash id for the parent document.
    page - what page of the original document the chunk is from.
    document_name - name of the original document.
    """

    chunk_size = 600
    chunk_overlap = 120
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )

    
    # Split
    urls_shortened = [sub(r"^www\.", "", sub(r"https\:\/\/|http\:\/\/", "", url)).split("/")[0] for (url, _) in url_content_pairs]
    

    splits = text_splitter.split_documents([Document(page_content=url_content, metadata={"type": "website", "url": url, "website_short": urls_shortened[i]}) for i, (url, url_content) in enumerate(url_content_pairs)])

    splits_text = [doc.page_content for doc in splits]
    splits_metadata = [doc.metadata for doc in splits]
    
    embedding_call : Awaitable[Callable] = toolchain_function_caller("embedding")
    
    embeddings = await embedding_call(auth, splits_text)

    documents = [random_hash() for _ in splits]

    for i in range(len(embeddings)):
        
        document_db_entry = DocumentChunk(
            document_name=splits_metadata[i]["website_short"],
            website_url=splits_metadata[i]["url"],
            embedding=embeddings[i],
            text=splits_text[i],
        )
        database.add(document_db_entry)

    database.commit()
    
    pass

async def keyword_query(database : Session ,
                        auth : AuthType,
                        query : str, 
                        collection_hash_ids : List[str], 
                        k : int = 10):
    (_, _) = get_user(database, auth)
    
    if len(collection_hash_ids) > 1:
        lookup_sql_condition = or_(
            *(DocumentChunk.collection_id == collection_hash_id for collection_hash_id in collection_hash_ids)
        )
    else:
        
        lookup_sql_condition = (DocumentChunk.collection_id == collection_hash_ids[0])
    
    selection = select(DocumentChunk).where(lookup_sql_condition).limit(k)
    
    first_pass_results : List[DocumentChunk] = database.exec(selection)
    
    new_docs_dict = {} # Remove duplicates
    for i, doc in enumerate(first_pass_results):
        # print(doc)
        content_hash = hash_function(hash_function(doc.text)+hash_function(doc.document_integrity))
        new_docs_dict[content_hash] = {
            key : v for key, v in doc.__dict__.items() if key not in ["_sa_instance_state", "embedding"]
        }
    
    new_documents = list(new_docs_dict.values())
    
    return new_documents[:min(len(new_documents), k)]

def concat_without_overlap(strings):
    result = strings[0]
    for s in strings[1:]:
        overlap = min(len(result), len(s))
        while overlap > 0 and result[-overlap:] != s[:overlap]:
            overlap -= 1
        result += s[overlap:]
    return result

def expand_source(database : Session,
                  auth : AuthType,
                  chunk_id : str,
                  range : Tuple[int, int]):
    """
    Given the id of an embedding chunk from the vector database, get the surrounding chunks to provide context.
    """
    (_, _) = get_user(database, auth)
    
    assert isinstance(range, tuple) and len(range) == 2, "Range must be a tuple of two integers."
    assert range[0] < 0, "Range start must be less than 0."
    assert range[1] > 0, "Range end must be greater than 0."
    
    main_chunk = database.exec(select(DocumentChunk).where(DocumentChunk.id == chunk_id)).first()
    
    assert not main_chunk is None, "Chunk not found"
    main_chunk_index = main_chunk.document_chunk_number
    
    chunk_range : List[DocumentChunk] = database.exec(select(DocumentChunk).where(and_(
        DocumentChunk.document_id == main_chunk.document_id,
        DocumentChunk.document_chunk_number >= main_chunk_index + range[0],
        DocumentChunk.document_chunk_number <= main_chunk_index + range[1],
    ))).all()
    
    chunk_range : List[DocumentChunk] = sorted(chunk_range, key=lambda x: x.document_chunk_number)
    
    chunks_of_text = [chunk.text for chunk in chunk_range]
    
    # return concat_without_overlap(chunks_of_text)
    
    return DocumentEmbeddingDictionary(
        id=chunk_range[0].id,
        creation_timestamp=chunk_range[0].creation_timestamp,
        document_id=chunk_range[0].document_id,
        document_chunk_number=chunk_range[0].document_chunk_number,
        document_integrity=chunk_range[0].document_integrity,
        collection_id=chunk_range[0].collection_id,
        document_name=chunk_range[0].document_name,
        website_url=chunk_range[0].website_url,
        private=chunk_range[0].private,
        text=concat_without_overlap(chunks_of_text),
    ).model_dump()

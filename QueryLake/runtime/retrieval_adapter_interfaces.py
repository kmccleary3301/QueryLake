from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Protocol, Union, runtime_checkable

from sqlmodel import Session

from QueryLake.runtime.retrieval_lane_executors import (
    execute_gold_bm25_search,
    execute_gold_document_chunk_hybrid_lanes,
    execute_gold_file_chunk_bm25_search,
)


@runtime_checkable
class LexicalRetrievalAdapterProtocol(Protocol):
    adapter_id: str
    backend: str

    def execute_bm25(self, database: Session, **kwargs: Any) -> Union[str, List[Any]]: ...

    def execute_file_chunk_bm25(self, database: Session, **kwargs: Any) -> Union[str, List[Any]]: ...


@runtime_checkable
class DenseRetrievalAdapterProtocol(Protocol):
    adapter_id: str
    backend: str

    def execute_document_chunk_dense(self, database: Session, **kwargs: Any) -> Union[str, List[Any]]: ...


@runtime_checkable
class SparseRetrievalAdapterProtocol(Protocol):
    adapter_id: str
    backend: str

    def execute_document_chunk_sparse(self, database: Session, **kwargs: Any) -> Union[str, List[Any]]: ...


@runtime_checkable
class GraphTraversalAdapterProtocol(Protocol):
    adapter_id: str
    backend: str

    def expand_segments(self, database: Session, **kwargs: Any) -> Any: ...


@dataclass(frozen=True)
class GoldLexicalRetrievalAdapter:
    adapter_id: str = "paradedb_bm25_v1"
    backend: str = "paradedb"

    def execute_bm25(self, database: Session, **kwargs: Any) -> Union[str, List[Any]]:
        return execute_gold_bm25_search(database, **kwargs)

    def execute_file_chunk_bm25(self, database: Session, **kwargs: Any) -> Union[str, List[Any]]:
        return execute_gold_file_chunk_bm25_search(database, **kwargs)


@dataclass(frozen=True)
class GoldDenseRetrievalAdapter:
    adapter_id: str = "pgvector_halfvec_v1"
    backend: str = "pgvector_halfvec"

    def execute_document_chunk_dense(self, database: Session, **kwargs: Any) -> Union[str, List[Any]]:
        params = dict(kwargs)
        params.update(
            {
                "database": database,
                "use_bm25": False,
                "use_similarity": True,
                "use_sparse": False,
                "limit_bm25": 0,
                "limit_sparse": 0,
                "bm25_weight": 0.0,
                "similarity_weight": 1.0,
                "sparse_weight": 0.0,
            }
        )
        return execute_gold_document_chunk_hybrid_lanes(**params)


@dataclass(frozen=True)
class GoldSparseRetrievalAdapter:
    adapter_id: str = "pgvector_sparsevec_v1"
    backend: str = "pgvector_sparsevec"

    def execute_document_chunk_sparse(self, database: Session, **kwargs: Any) -> Union[str, List[Any]]:
        params = dict(kwargs)
        params.update(
            {
                "database": database,
                "use_bm25": False,
                "use_similarity": False,
                "use_sparse": True,
                "limit_bm25": 0,
                "limit_similarity": 0,
                "bm25_weight": 0.0,
                "similarity_weight": 0.0,
                "sparse_weight": 1.0,
            }
        )
        return execute_gold_document_chunk_hybrid_lanes(**params)


@dataclass(frozen=True)
class PlaceholderGraphTraversalAdapter:
    adapter_id: str
    backend: str

    def expand_segments(self, database: Session, **kwargs: Any) -> Any:
        raise NotImplementedError(
            f"Graph traversal adapter '{self.adapter_id}' on backend '{self.backend}' is not implemented yet."
        )


def get_gold_adapter_bundle() -> Dict[str, Any]:
    return {
        "lexical": GoldLexicalRetrievalAdapter(),
        "dense": GoldDenseRetrievalAdapter(),
        "sparse": GoldSparseRetrievalAdapter(),
        "graph": PlaceholderGraphTraversalAdapter(
            adapter_id="postgresql_segment_relations_v1",
            backend="postgresql_segment_relations",
        ),
    }

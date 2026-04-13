from pathlib import Path
import sys

import pgvector

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.api.search import _normalize_collection_ids_for_bound_query, _normalize_sparse_query_value
from QueryLake.vector_database.embeddings import _extract_sparse_embedding
from QueryLake.vector_database.sparse_projection import (
    project_sparse_mapping,
    project_sparse_vector,
    sparse_vector_to_mapping,
)


def test_project_sparse_mapping_mods_large_lexical_ids():
    projected = project_sparse_mapping({0: 1.0, 2050: 0.5}, 1024)
    assert projected[0] == 1.0
    assert projected[2] == 0.5


def test_project_sparse_vector_non_strict_coerces_dimensions():
    value = pgvector.SparseVector({0: 1.0, 7: 0.2}, 16)
    projected = project_sparse_vector(value, 8, strict_dimensions=False, source_label="unit")
    assert int(projected.dimensions()) == 8


def test_extract_sparse_embedding_projects_large_sparse_indices():
    parsed = _extract_sparse_embedding({2050: 0.5, 4: 0.2}, dimensions=1024, strict_dimensions=False)
    assert parsed is not None
    mapping = sparse_vector_to_mapping(parsed)
    assert mapping[2] == 0.5
    assert mapping[4] == 0.2


def test_normalize_sparse_query_projects_large_sparse_indices():
    parsed = _normalize_sparse_query_value({2050: 0.5, 4: 0.2}, dimensions=1024, strict_dimensions=False)
    assert parsed is not None
    mapping = sparse_vector_to_mapping(parsed)
    assert mapping[2] == 0.5
    assert mapping[4] == 0.2


def test_normalize_collection_ids_preserves_uuid_hyphens():
    out = _normalize_collection_ids_for_bound_query(["abc-123_def", "oops!", "short"])
    assert out == ["abc-123_def", "short"]

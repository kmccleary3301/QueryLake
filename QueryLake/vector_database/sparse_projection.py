from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping, MutableMapping, Tuple

import pgvector


class SparseDimensionMismatchError(ValueError):
    pass


def project_sparse_index(index: int, dimensions: int) -> int:
    if dimensions <= 0:
        raise ValueError("dimensions must be a positive integer")
    return int(index) % int(dimensions)


def project_sparse_mapping(
    mapping: Any,
    dimensions: int,
    *,
    strict_dimensions: bool = False,
    source_label: str = "sparse_mapping",
) -> Dict[int, float]:
    if dimensions <= 0:
        raise ValueError("dimensions must be a positive integer")

    projected: Dict[int, float] = {}
    items: Iterable[Tuple[Any, Any]]
    if isinstance(mapping, Mapping):
        items = mapping.items()
    else:
        raise TypeError(f"Unsupported sparse mapping input for {source_label}: {type(mapping)!r}")

    for raw_key, raw_value in items:
        if raw_value is None:
            continue
        try:
            index = int(raw_key)
            value = float(raw_value)
        except Exception:
            continue
        if value == 0.0:
            continue
        target_index = project_sparse_index(index, dimensions)
        projected[target_index] = projected.get(target_index, 0.0) + value

    return projected


def sparse_vector_to_mapping(vector_value: pgvector.SparseVector) -> Dict[int, float]:
    return {
        int(index): float(value)
        for index, value in zip(vector_value.indices(), vector_value.values())
        if float(value) != 0.0
    }


def project_sparse_vector(
    value: pgvector.SparseVector,
    dimensions: int,
    *,
    strict_dimensions: bool = False,
    source_label: str = "sparse_vector",
) -> pgvector.SparseVector:
    current_dimensions = int(value.dimensions())
    if current_dimensions == int(dimensions):
        return value
    if strict_dimensions:
        raise SparseDimensionMismatchError(
            f"Sparse dimension mismatch for {source_label}: expected {dimensions}, observed {current_dimensions}"
        )
    return pgvector.SparseVector(
        project_sparse_mapping(sparse_vector_to_mapping(value), dimensions, source_label=source_label),
        dimensions,
    )

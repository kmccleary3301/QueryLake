# Local Profile Support Matrix

This document is the canonical machine-readable route support matrix snapshot for `sqlite_fts5_dense_sidecar_local_v1`.

| Use this when | you need the exact local route support matrix reflected by the runtime contract |
| --- | --- |
| Canonical runtime source | `QueryLake/runtime/local_profile_v2.py::build_local_route_support_matrix_payload` |
| Drift gate | `python scripts/ci_local_profile_support_sync.py` |

## Machine-readable snapshot

```json
[
  {
    "capability_dependencies": [
      "retrieval.lexical.bm25",
      "retrieval.dense.vector"
    ],
    "declared_executable": true,
    "declared_optional": false,
    "lexical_support_class": "degraded_supported",
    "representation_scope": {
      "authority_model": "document_segment",
      "compatibility_projection": true,
      "metadata": {
        "intended_routes": [
          "search_hybrid.document_chunk",
          "search_bm25.document_chunk",
          "retrieval.sparse.vector"
        ],
        "representation_kind": "chunk_compatibility_projection"
      },
      "scope_id": "document_chunk"
    },
    "representation_scope_id": "document_chunk",
    "required_projection_descriptors": [
      "document_chunk_lexical_projection_v1",
      "document_chunk_dense_projection_v1"
    ],
    "route_id": "search_hybrid.document_chunk",
    "support_state": "supported"
  },
  {
    "capability_dependencies": [
      "retrieval.lexical.bm25"
    ],
    "declared_executable": true,
    "declared_optional": false,
    "lexical_support_class": "degraded_supported",
    "representation_scope": {
      "authority_model": "document_segment",
      "compatibility_projection": true,
      "metadata": {
        "intended_routes": [
          "search_hybrid.document_chunk",
          "search_bm25.document_chunk",
          "retrieval.sparse.vector"
        ],
        "representation_kind": "chunk_compatibility_projection"
      },
      "scope_id": "document_chunk"
    },
    "representation_scope_id": "document_chunk",
    "required_projection_descriptors": [
      "document_chunk_lexical_projection_v1"
    ],
    "route_id": "search_bm25.document_chunk",
    "support_state": "degraded"
  },
  {
    "capability_dependencies": [
      "retrieval.lexical.bm25"
    ],
    "declared_executable": true,
    "declared_optional": false,
    "lexical_support_class": "degraded_supported",
    "representation_scope": {
      "authority_model": "file_chunk",
      "compatibility_projection": false,
      "metadata": {
        "intended_routes": [
          "search_file_chunks"
        ],
        "representation_kind": "file_chunk_projection"
      },
      "scope_id": "file_chunk"
    },
    "representation_scope_id": "file_chunk",
    "required_projection_descriptors": [
      "file_chunk_lexical_projection_v1"
    ],
    "route_id": "search_file_chunks",
    "support_state": "degraded"
  },
  {
    "capability_dependencies": [
      "retrieval.sparse.vector"
    ],
    "declared_executable": false,
    "declared_optional": true,
    "lexical_support_class": "unsupported",
    "representation_scope": {
      "authority_model": "document_segment",
      "compatibility_projection": true,
      "metadata": {
        "intended_routes": [
          "search_hybrid.document_chunk",
          "search_bm25.document_chunk",
          "retrieval.sparse.vector"
        ],
        "representation_kind": "chunk_compatibility_projection"
      },
      "scope_id": "document_chunk"
    },
    "representation_scope_id": "document_chunk",
    "required_projection_descriptors": [],
    "route_id": "retrieval.sparse.vector",
    "support_state": "unsupported"
  },
  {
    "capability_dependencies": [
      "retrieval.graph.traversal"
    ],
    "declared_executable": false,
    "declared_optional": true,
    "lexical_support_class": "unsupported",
    "representation_scope": {
      "authority_model": "document_segment",
      "compatibility_projection": false,
      "metadata": {
        "intended_routes": [
          "retrieval.graph.traversal"
        ],
        "representation_kind": "graph_relation_view"
      },
      "scope_id": "document_segment_graph"
    },
    "representation_scope_id": "document_segment_graph",
    "required_projection_descriptors": [],
    "route_id": "retrieval.graph.traversal",
    "support_state": "unsupported"
  }
]
```

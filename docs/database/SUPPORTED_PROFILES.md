# QueryLake Supported Profiles

[![Docs Checks](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml/badge.svg)](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml)
[![SDK Checks](https://github.com/kmccleary3301/QueryLake/actions/workflows/sdk_checks.yml/badge.svg)](https://github.com/kmccleary3301/QueryLake/actions/workflows/sdk_checks.yml)

This is the concise, authoritative supported-profile surface for QueryLake's current DB compatibility program.

| Field | Value |
|---|---|
| Audience | deployment operators, backend contributors, SDK users |
| Use this when | you need the shortest trustworthy answer to “what profiles are real, and what do they support?” |
| Prerequisites | [`DB_COMPAT_PROFILES.md`](./DB_COMPAT_PROFILES.md), [`PROFILE_DIAGNOSTICS.md`](./PROFILE_DIAGNOSTICS.md) |
| Related docs | [`FIRST_SPLIT_STACK_DEPLOYMENT.md`](./FIRST_SPLIT_STACK_DEPLOYMENT.md), [`FIRST_SPLIT_STACK_COMPLETION_GATE.md`](./FIRST_SPLIT_STACK_COMPLETION_GATE.md), [`DB_COMPAT_COMPLETION_GATE.md`](./DB_COMPAT_COMPLETION_GATE.md), [`DB_COMPAT_IMPLEMENTATION_REPORT.md`](./DB_COMPAT_IMPLEMENTATION_REPORT.md), [`DB_COMPAT_PROGRAM_STATUS.md`](./DB_COMPAT_PROGRAM_STATUS.md), [`DB_COMPAT_FUTURE_SCOPE.md`](./DB_COMPAT_FUTURE_SCOPE.md) |
| Status | authoritative for current program scope |

## Current profiles

| Profile | Maturity | Executable | Recommended | Intended role |
|---|---|---:|---:|---|
| `paradedb_postgres_gold_v1` | `gold` | 🟢 | 🟢 | canonical full-semantics QueryLake stack |
| `postgres_pgvector_light_v1` | `limited_executable` | 🟡 | 🔴 | narrow dense-only fallback profile |
| `aws_aurora_pg_opensearch_v1` | `split_stack_executable` | 🟡 | 🔴 | first supported split-stack profile |
| `sqlite_fts5_dense_sidecar_local_v1` | `embedded_supported` | 🟡 | 🔴 | supported embedded/local profile for the declared SQLite FTS5 + dense-sidecar slice |
| `mongo_opensearch_v1` | `planned` | 🔴 | 🔴 | future authority/search split-stack profile |
| `planetscale_opensearch_v1` | `planned` | 🔴 | 🔴 | future MySQL-compatible split-stack profile |

## Program boundary

The current DB compatibility program is considered complete when:

- the gold profile remains fully preserved,
- `aws_aurora_pg_opensearch_v1` is fully supported for its declared scope,
- `postgres_pgvector_light_v1` remains honestly limited,
- all diagnostics, bring-up, completion gates, SDK, CLI, docs, and CI surfaces agree,
- and anything beyond that is explicitly deferred into future scope.

The current program does **not** require:

- a second fully implemented split-stack backend,
- full split-stack sparse retrieval,
- full graph-lane implementation outside the gold profile,
- or total elimination of compatibility projections everywhere in the codebase.

## Code-synced manifest

The JSON block below is checked in CI against `QueryLake/runtime/db_compat.py`.

<!-- BEGIN_SUPPORTED_PROFILES_MANIFEST -->
```json
{
  "profiles": [
    {
      "backend_stack": {
        "authority": "postgresql",
        "dense": "pgvector_halfvec",
        "graph": "postgresql_segment_relations",
        "lexical": "paradedb",
        "sparse": "pgvector_sparsevec"
      },
      "capabilities": {
        "acl.pushdown": "supported",
        "authority.sql_transactions": "supported",
        "explain.retrieval_plan": "planned",
        "projection.rebuildable_indexes": "supported",
        "retrieval.dense.vector": "supported",
        "retrieval.graph.traversal": "supported",
        "retrieval.lexical.advanced_operators": "supported",
        "retrieval.lexical.bm25": "supported",
        "retrieval.lexical.hard_constraints": "supported",
        "retrieval.lexical.phrase_boost": "supported",
        "retrieval.lexical.proximity": "supported",
        "retrieval.segment_search": "supported",
        "retrieval.sparse.vector": "supported"
      },
      "id": "paradedb_postgres_gold_v1",
      "implemented": true,
      "label": "ParadeDB + PostgreSQL (gold)",
      "maturity": "gold",
      "recommended": true,
      "representation_scopes": {
        "document_chunk": {
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
        "document_segment_graph": {
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
        "file_chunk": {
          "authority_model": "file_chunk",
          "compatibility_projection": false,
          "metadata": {
            "intended_routes": [
              "search_file_chunks"
            ],
            "representation_kind": "file_chunk_projection"
          },
          "scope_id": "file_chunk"
        }
      },
      "routes": {
        "retrieval.graph.traversal": {
          "capability_dependencies": [
            "retrieval.graph.traversal"
          ],
          "declared_executable": true,
          "declared_optional": false,
          "declared_state": "supported",
          "representation_scope_id": "document_segment_graph"
        },
        "search_bm25.document_chunk": {
          "capability_dependencies": [
            "retrieval.lexical.bm25"
          ],
          "declared_executable": true,
          "declared_optional": false,
          "declared_state": "supported",
          "representation_scope_id": "document_chunk"
        },
        "search_file_chunks": {
          "capability_dependencies": [
            "retrieval.lexical.bm25"
          ],
          "declared_executable": true,
          "declared_optional": false,
          "declared_state": "supported",
          "representation_scope_id": "file_chunk"
        },
        "search_hybrid.document_chunk": {
          "capability_dependencies": [
            "retrieval.lexical.bm25",
            "retrieval.dense.vector"
          ],
          "declared_executable": true,
          "declared_optional": false,
          "declared_state": "supported",
          "representation_scope_id": "document_chunk"
        }
      },
      "routes_v2": [
        {
          "capability_dependencies": [
            "retrieval.lexical.bm25",
            "retrieval.dense.vector"
          ],
          "declared_executable": true,
          "declared_optional": false,
          "notes": null,
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
          "route_id": "search_hybrid.document_chunk",
          "support_state": "supported"
        },
        {
          "capability_dependencies": [
            "retrieval.lexical.bm25"
          ],
          "declared_executable": true,
          "declared_optional": false,
          "notes": null,
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
          "route_id": "search_bm25.document_chunk",
          "support_state": "supported"
        },
        {
          "capability_dependencies": [
            "retrieval.lexical.bm25"
          ],
          "declared_executable": true,
          "declared_optional": false,
          "notes": null,
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
          "route_id": "search_file_chunks",
          "support_state": "supported"
        },
        {
          "capability_dependencies": [
            "retrieval.graph.traversal"
          ],
          "declared_executable": true,
          "declared_optional": false,
          "notes": null,
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
          "route_id": "retrieval.graph.traversal",
          "support_state": "supported"
        }
      ]
    },
    {
      "backend_stack": {
        "authority": "postgresql",
        "dense": "pgvector_halfvec",
        "graph": "postgresql_segment_relations",
        "lexical": "none",
        "sparse": "none"
      },
      "capabilities": {
        "acl.pushdown": "supported",
        "authority.sql_transactions": "supported",
        "explain.retrieval_plan": "planned",
        "projection.rebuildable_indexes": "planned",
        "retrieval.dense.vector": "supported",
        "retrieval.graph.traversal": "planned",
        "retrieval.lexical.advanced_operators": "unsupported",
        "retrieval.lexical.bm25": "unsupported",
        "retrieval.lexical.hard_constraints": "unsupported",
        "retrieval.lexical.phrase_boost": "unsupported",
        "retrieval.lexical.proximity": "unsupported",
        "retrieval.segment_search": "planned",
        "retrieval.sparse.vector": "unsupported"
      },
      "id": "postgres_pgvector_light_v1",
      "implemented": true,
      "label": "PostgreSQL + pgvector (light)",
      "maturity": "limited_executable",
      "recommended": false,
      "representation_scopes": {
        "document_chunk": {
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
        "document_segment_graph": {
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
        "file_chunk": {
          "authority_model": "file_chunk",
          "compatibility_projection": false,
          "metadata": {
            "intended_routes": [
              "search_file_chunks"
            ],
            "representation_kind": "file_chunk_projection"
          },
          "scope_id": "file_chunk"
        }
      },
      "routes": {
        "retrieval.sparse.vector": {
          "capability_dependencies": [
            "retrieval.sparse.vector"
          ],
          "declared_executable": false,
          "declared_optional": true,
          "declared_state": "unsupported",
          "representation_scope_id": "document_chunk"
        },
        "search_bm25.document_chunk": {
          "capability_dependencies": [
            "retrieval.lexical.bm25"
          ],
          "declared_executable": false,
          "declared_optional": true,
          "declared_state": "unsupported",
          "representation_scope_id": "document_chunk"
        },
        "search_file_chunks": {
          "capability_dependencies": [
            "retrieval.lexical.bm25"
          ],
          "declared_executable": false,
          "declared_optional": true,
          "declared_state": "unsupported",
          "representation_scope_id": "file_chunk"
        },
        "search_hybrid.document_chunk": {
          "capability_dependencies": [
            "retrieval.lexical.bm25",
            "retrieval.dense.vector"
          ],
          "declared_executable": true,
          "declared_optional": false,
          "declared_state": "supported",
          "representation_scope_id": "document_chunk"
        }
      },
      "routes_v2": [
        {
          "capability_dependencies": [
            "retrieval.lexical.bm25",
            "retrieval.dense.vector"
          ],
          "declared_executable": true,
          "declared_optional": false,
          "notes": "Requires use_bm25=false and use_sparse=false in the request shape.",
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
          "route_id": "search_hybrid.document_chunk",
          "support_state": "supported"
        },
        {
          "capability_dependencies": [
            "retrieval.lexical.bm25"
          ],
          "declared_executable": false,
          "declared_optional": true,
          "notes": null,
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
          "route_id": "search_bm25.document_chunk",
          "support_state": "unsupported"
        },
        {
          "capability_dependencies": [
            "retrieval.lexical.bm25"
          ],
          "declared_executable": false,
          "declared_optional": true,
          "notes": null,
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
          "route_id": "search_file_chunks",
          "support_state": "unsupported"
        },
        {
          "capability_dependencies": [
            "retrieval.sparse.vector"
          ],
          "declared_executable": false,
          "declared_optional": true,
          "notes": null,
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
          "route_id": "retrieval.sparse.vector",
          "support_state": "unsupported"
        }
      ]
    },
    {
      "backend_stack": {
        "authority": "aurora_postgresql",
        "dense": "opensearch",
        "graph": "aurora_postgresql_segment_relations",
        "lexical": "opensearch",
        "sparse": "opensearch"
      },
      "capabilities": {
        "acl.pushdown": "supported",
        "authority.sql_transactions": "supported",
        "explain.retrieval_plan": "planned",
        "projection.rebuildable_indexes": "planned",
        "retrieval.dense.vector": "supported",
        "retrieval.graph.traversal": "unsupported",
        "retrieval.lexical.advanced_operators": "degraded",
        "retrieval.lexical.bm25": "supported",
        "retrieval.lexical.hard_constraints": "unsupported",
        "retrieval.lexical.phrase_boost": "degraded",
        "retrieval.lexical.proximity": "degraded",
        "retrieval.segment_search": "unsupported",
        "retrieval.sparse.vector": "unsupported"
      },
      "id": "aws_aurora_pg_opensearch_v1",
      "implemented": true,
      "label": "Aurora PostgreSQL + OpenSearch",
      "maturity": "split_stack_executable",
      "recommended": false,
      "representation_scopes": {
        "document_chunk": {
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
        "document_segment_graph": {
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
        "file_chunk": {
          "authority_model": "file_chunk",
          "compatibility_projection": false,
          "metadata": {
            "intended_routes": [
              "search_file_chunks"
            ],
            "representation_kind": "file_chunk_projection"
          },
          "scope_id": "file_chunk"
        }
      },
      "routes": {
        "retrieval.graph.traversal": {
          "capability_dependencies": [
            "retrieval.graph.traversal"
          ],
          "declared_executable": false,
          "declared_optional": true,
          "declared_state": "unsupported",
          "representation_scope_id": "document_segment_graph"
        },
        "retrieval.sparse.vector": {
          "capability_dependencies": [
            "retrieval.sparse.vector"
          ],
          "declared_executable": false,
          "declared_optional": true,
          "declared_state": "unsupported",
          "representation_scope_id": "document_chunk"
        },
        "search_bm25.document_chunk": {
          "capability_dependencies": [
            "retrieval.lexical.bm25"
          ],
          "declared_executable": true,
          "declared_optional": false,
          "declared_state": "supported",
          "representation_scope_id": "document_chunk"
        },
        "search_file_chunks": {
          "capability_dependencies": [
            "retrieval.lexical.bm25"
          ],
          "declared_executable": true,
          "declared_optional": false,
          "declared_state": "supported",
          "representation_scope_id": "file_chunk"
        },
        "search_hybrid.document_chunk": {
          "capability_dependencies": [
            "retrieval.lexical.bm25",
            "retrieval.dense.vector"
          ],
          "declared_executable": true,
          "declared_optional": false,
          "declared_state": "supported",
          "representation_scope_id": "document_chunk"
        }
      },
      "routes_v2": [
        {
          "capability_dependencies": [
            "retrieval.lexical.bm25",
            "retrieval.dense.vector"
          ],
          "declared_executable": true,
          "declared_optional": false,
          "notes": null,
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
          "route_id": "search_hybrid.document_chunk",
          "support_state": "supported"
        },
        {
          "capability_dependencies": [
            "retrieval.lexical.bm25"
          ],
          "declared_executable": true,
          "declared_optional": false,
          "notes": null,
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
          "route_id": "search_bm25.document_chunk",
          "support_state": "supported"
        },
        {
          "capability_dependencies": [
            "retrieval.lexical.bm25"
          ],
          "declared_executable": true,
          "declared_optional": false,
          "notes": null,
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
          "route_id": "search_file_chunks",
          "support_state": "supported"
        },
        {
          "capability_dependencies": [
            "retrieval.sparse.vector"
          ],
          "declared_executable": false,
          "declared_optional": true,
          "notes": null,
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
          "route_id": "retrieval.sparse.vector",
          "support_state": "unsupported"
        },
        {
          "capability_dependencies": [
            "retrieval.graph.traversal"
          ],
          "declared_executable": false,
          "declared_optional": true,
          "notes": null,
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
          "route_id": "retrieval.graph.traversal",
          "support_state": "unsupported"
        }
      ]
    },
    {
      "backend_stack": {
        "authority": "sqlite",
        "dense": "local_dense_sidecar",
        "graph": "none",
        "lexical": "sqlite_fts5",
        "sparse": "none"
      },
      "capabilities": {
        "acl.pushdown": "supported",
        "authority.sql_transactions": "supported",
        "explain.retrieval_plan": "planned",
        "projection.rebuildable_indexes": "supported",
        "retrieval.dense.vector": "supported",
        "retrieval.graph.traversal": "unsupported",
        "retrieval.lexical.advanced_operators": "degraded",
        "retrieval.lexical.bm25": "degraded",
        "retrieval.lexical.hard_constraints": "unsupported",
        "retrieval.lexical.phrase_boost": "degraded",
        "retrieval.lexical.proximity": "degraded",
        "retrieval.segment_search": "planned",
        "retrieval.sparse.vector": "unsupported"
      },
      "id": "sqlite_fts5_dense_sidecar_local_v1",
      "implemented": true,
      "label": "SQLite FTS5 + dense sidecar (local)",
      "maturity": "embedded_supported",
      "recommended": false,
      "representation_scopes": {
        "document_chunk": {
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
        "document_segment_graph": {
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
        "file_chunk": {
          "authority_model": "file_chunk",
          "compatibility_projection": false,
          "metadata": {
            "intended_routes": [
              "search_file_chunks"
            ],
            "representation_kind": "file_chunk_projection"
          },
          "scope_id": "file_chunk"
        }
      },
      "routes": {
        "retrieval.graph.traversal": {
          "capability_dependencies": [
            "retrieval.graph.traversal"
          ],
          "declared_executable": false,
          "declared_optional": true,
          "declared_state": "unsupported",
          "representation_scope_id": "document_segment_graph"
        },
        "retrieval.sparse.vector": {
          "capability_dependencies": [
            "retrieval.sparse.vector"
          ],
          "declared_executable": false,
          "declared_optional": true,
          "declared_state": "unsupported",
          "representation_scope_id": "document_chunk"
        },
        "search_bm25.document_chunk": {
          "capability_dependencies": [
            "retrieval.lexical.bm25"
          ],
          "declared_executable": true,
          "declared_optional": false,
          "declared_state": "degraded",
          "representation_scope_id": "document_chunk"
        },
        "search_file_chunks": {
          "capability_dependencies": [
            "retrieval.lexical.bm25"
          ],
          "declared_executable": true,
          "declared_optional": false,
          "declared_state": "degraded",
          "representation_scope_id": "file_chunk"
        },
        "search_hybrid.document_chunk": {
          "capability_dependencies": [
            "retrieval.lexical.bm25",
            "retrieval.dense.vector"
          ],
          "declared_executable": true,
          "declared_optional": false,
          "declared_state": "supported",
          "representation_scope_id": "document_chunk"
        }
      },
      "routes_v2": [
        {
          "capability_dependencies": [
            "retrieval.lexical.bm25",
            "retrieval.dense.vector"
          ],
          "declared_executable": true,
          "declared_optional": false,
          "notes": "The first local slice is intended to preserve hybrid composition while staying honest about lexical differences from the gold profile.",
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
          "route_id": "search_hybrid.document_chunk",
          "support_state": "supported"
        },
        {
          "capability_dependencies": [
            "retrieval.lexical.bm25"
          ],
          "declared_executable": true,
          "declared_optional": false,
          "notes": null,
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
          "route_id": "search_bm25.document_chunk",
          "support_state": "degraded"
        },
        {
          "capability_dependencies": [
            "retrieval.lexical.bm25"
          ],
          "declared_executable": true,
          "declared_optional": false,
          "notes": null,
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
          "route_id": "search_file_chunks",
          "support_state": "degraded"
        },
        {
          "capability_dependencies": [
            "retrieval.sparse.vector"
          ],
          "declared_executable": false,
          "declared_optional": true,
          "notes": null,
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
          "route_id": "retrieval.sparse.vector",
          "support_state": "unsupported"
        },
        {
          "capability_dependencies": [
            "retrieval.graph.traversal"
          ],
          "declared_executable": false,
          "declared_optional": true,
          "notes": null,
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
          "route_id": "retrieval.graph.traversal",
          "support_state": "unsupported"
        }
      ]
    },
    {
      "backend_stack": {
        "authority": "mongodb",
        "dense": "opensearch",
        "graph": "projection_only",
        "lexical": "opensearch",
        "sparse": "opensearch"
      },
      "capabilities": {
        "acl.pushdown": "supported",
        "authority.sql_transactions": "supported",
        "explain.retrieval_plan": "planned",
        "projection.rebuildable_indexes": "planned",
        "retrieval.dense.vector": "supported",
        "retrieval.graph.traversal": "unsupported",
        "retrieval.lexical.advanced_operators": "degraded",
        "retrieval.lexical.bm25": "supported",
        "retrieval.lexical.hard_constraints": "unsupported",
        "retrieval.lexical.phrase_boost": "degraded",
        "retrieval.lexical.proximity": "degraded",
        "retrieval.segment_search": "unsupported",
        "retrieval.sparse.vector": "unsupported"
      },
      "id": "mongo_opensearch_v1",
      "implemented": false,
      "label": "MongoDB + OpenSearch",
      "maturity": "planned",
      "recommended": false,
      "representation_scopes": {
        "document_chunk": {
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
        "document_segment_graph": {
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
        "file_chunk": {
          "authority_model": "file_chunk",
          "compatibility_projection": false,
          "metadata": {
            "intended_routes": [
              "search_file_chunks"
            ],
            "representation_kind": "file_chunk_projection"
          },
          "scope_id": "file_chunk"
        }
      },
      "routes": {},
      "routes_v2": []
    },
    {
      "backend_stack": {
        "authority": "planetscale",
        "dense": "opensearch",
        "graph": "projection_only",
        "lexical": "opensearch",
        "sparse": "opensearch"
      },
      "capabilities": {
        "acl.pushdown": "supported",
        "authority.sql_transactions": "supported",
        "explain.retrieval_plan": "planned",
        "projection.rebuildable_indexes": "planned",
        "retrieval.dense.vector": "supported",
        "retrieval.graph.traversal": "unsupported",
        "retrieval.lexical.advanced_operators": "degraded",
        "retrieval.lexical.bm25": "supported",
        "retrieval.lexical.hard_constraints": "unsupported",
        "retrieval.lexical.phrase_boost": "degraded",
        "retrieval.lexical.proximity": "degraded",
        "retrieval.segment_search": "unsupported",
        "retrieval.sparse.vector": "unsupported"
      },
      "id": "planetscale_opensearch_v1",
      "implemented": false,
      "label": "PlanetScale + OpenSearch",
      "maturity": "planned",
      "recommended": false,
      "representation_scopes": {
        "document_chunk": {
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
        "document_segment_graph": {
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
        "file_chunk": {
          "authority_model": "file_chunk",
          "compatibility_projection": false,
          "metadata": {
            "intended_routes": [
              "search_file_chunks"
            ],
            "representation_kind": "file_chunk_projection"
          },
          "scope_id": "file_chunk"
        }
      },
      "routes": {},
      "routes_v2": []
    }
  ]
}
```
<!-- END_SUPPORTED_PROFILES_MANIFEST -->

## Interpretation

- `gold` means full current QueryLake retrieval semantics are preserved.
- `split_stack_executable` means the profile is real and executable for its declared route slice, with explicit degraded or unsupported semantics where needed.
- `limited_executable` means the profile intentionally exposes a narrow route subset.
- `planned` means the profile id and capability story are reserved, but execution is not in scope yet.

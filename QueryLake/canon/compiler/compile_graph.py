from __future__ import annotations

from QueryLake.canon.models import GraphSpec


def compile_graph(graph: GraphSpec) -> GraphSpec:
    """Minimal Phase 1A compiler entry point.

    Milestone 2A only needs a deterministic compiler shell that accepts a
    validated graph and returns a compiled-ready graph object without yet
    introducing route-family lowering semantics.
    """

    if not isinstance(graph, GraphSpec):
        raise TypeError("compile_graph expects a GraphSpec instance")
    return graph

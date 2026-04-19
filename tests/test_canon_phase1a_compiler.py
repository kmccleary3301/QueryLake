from QueryLake.canon import EffectClass, GraphSpec, NodeSpec, OutputRef
from QueryLake.canon.compiler import compile_graph


def test_compile_graph_accepts_minimal_graph_spec():
    graph = GraphSpec(
        nodes=(
            NodeSpec("a", "const", EffectClass.PURE_DETERMINISTIC, config={"value": 1}),
        ),
        requested_outputs=(OutputRef("a"),),
    )

    compiled = compile_graph(graph)

    assert compiled is graph
    assert compiled.graph_id == graph.graph_id

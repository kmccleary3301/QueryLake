from QueryLake.canon import EffectClass, GraphSpec, NodeSpec, OutputRef


def test_graph_spec_rejects_duplicate_node_ids():
    node_a = NodeSpec(node_id="dup", operation="const", effect_class=EffectClass.PURE_DETERMINISTIC)
    node_b = NodeSpec(node_id="dup", operation="const", effect_class=EffectClass.PURE_DETERMINISTIC)
    try:
        GraphSpec(nodes=(node_a, node_b), requested_outputs=(OutputRef("dup"),))
        assert False, "expected duplicate node id validation to fail"
    except ValueError as exc:
        assert "unique" in str(exc)


def test_graph_spec_rejects_unknown_dependency_output():
    node_a = NodeSpec(node_id="a", operation="const", effect_class=EffectClass.PURE_DETERMINISTIC)
    node_b = NodeSpec(
        node_id="b",
        operation="combine",
        effect_class=EffectClass.PURE_DETERMINISTIC,
        dependencies=(OutputRef("a", "missing"),),
    )
    try:
        GraphSpec(nodes=(node_a, node_b), requested_outputs=(OutputRef("b"),))
        assert False, "expected dependency validation to fail"
    except ValueError as exc:
        assert "unknown output" in str(exc)


def test_graph_id_is_deterministic_for_identical_graphs():
    node_a = NodeSpec(
        node_id="a",
        operation="const",
        effect_class=EffectClass.PURE_DETERMINISTIC,
        config={"value": 1},
    )
    node_b = NodeSpec(
        node_id="b",
        operation="combine",
        effect_class=EffectClass.PURE_DETERMINISTIC,
        dependencies=(OutputRef("a"),),
        config={"offset": 2},
    )
    graph_one = GraphSpec(nodes=(node_a, node_b), requested_outputs=(OutputRef("b"),))
    graph_two = GraphSpec(nodes=(node_a, node_b), requested_outputs=(OutputRef("b"),))
    assert graph_one.graph_id == graph_two.graph_id


def test_node_spec_requires_phase_1a_effect_enum():
    try:
        NodeSpec(node_id="a", operation="const", effect_class="NotAllowed")
        assert False, "expected effect validation to fail"
    except ValueError:
        pass

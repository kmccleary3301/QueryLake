from QueryLake.canon import (
    CanonExecutionError,
    CanonExecutor,
    EffectClass,
    ExecutionContext,
    GraphSpec,
    NodeSpec,
    OutputRef,
)


def test_executor_runs_only_demanded_subgraph():
    executed = []

    def const_handler(node, _inputs, _context):
        executed.append(node.node_id)
        return {"result": node.config["value"]}

    def sum_handler(node, inputs, _context):
        executed.append(node.node_id)
        return {"result": sum(inputs.values()) + node.config.get("offset", 0)}

    graph = GraphSpec(
        nodes=(
            NodeSpec("a", "const", EffectClass.PURE_DETERMINISTIC, config={"value": 2}),
            NodeSpec("b", "const", EffectClass.PURE_DETERMINISTIC, config={"value": 3}),
            NodeSpec(
                "sum",
                "sum",
                EffectClass.PURE_DETERMINISTIC,
                dependencies=(OutputRef("a"), OutputRef("b")),
                config={"offset": 1},
            ),
            NodeSpec("unused", "const", EffectClass.PURE_DETERMINISTIC, config={"value": 99}),
        ),
        requested_outputs=(OutputRef("sum"),),
    )

    result = CanonExecutor().execute(
        graph,
        handlers={"const": const_handler, "sum": sum_handler},
        context=ExecutionContext(),
    )

    assert result.outputs == {"sum.result": 6}
    assert executed == ["a", "b", "sum"]
    assert result.summary.executed_node_ids == ("a", "b", "sum")
    assert result.summary.total_nodes_defined == 4
    assert result.summary.requested_output_keys == ("sum.result",)


def test_executor_returns_structured_summary_envelope():
    def const_handler(node, _inputs, _context):
        return {"result": node.config["value"]}

    graph = GraphSpec(
        nodes=(
            NodeSpec("a", "const", EffectClass.PURE_DETERMINISTIC, config={"value": 7}),
        ),
        requested_outputs=(OutputRef("a"),),
    )

    result = CanonExecutor().execute(graph, handlers={"const": const_handler})

    assert result.graph_id == graph.graph_id
    assert result.summary.graph_id == graph.graph_id
    assert result.summary.executed_node_ids == ("a",)
    assert result.summary.node_results[0].status == "success"
    assert result.summary.node_results[0].effect_class == EffectClass.PURE_DETERMINISTIC
    assert result.summary.node_results[0].duration_ms >= 0.0
    assert result.summary.node_results[0].output_count == 1
    assert result.summary.total_duration_ms >= 0.0
    assert result.summary.memoized_reads == 0


def test_executor_records_memoized_reads_for_repeat_requests():
    def const_handler(node, _inputs, _context):
        return {"result": node.config["value"]}

    graph = GraphSpec(
        nodes=(NodeSpec("a", "const", EffectClass.PURE_DETERMINISTIC, config={"value": 7}),),
        requested_outputs=(OutputRef("a"), OutputRef("a")),
    )

    result = CanonExecutor().execute(graph, handlers={"const": const_handler})

    assert result.outputs["a.result"] == 7
    assert result.summary.executed_node_ids == ("a",)
    assert result.summary.memoized_reads == 1


def test_executor_fails_cleanly_when_handler_is_missing():
    graph = GraphSpec(
        nodes=(
            NodeSpec("a", "missing", EffectClass.PURE_DETERMINISTIC),
        ),
        requested_outputs=(OutputRef("a"),),
    )

    try:
        CanonExecutor().execute(graph, handlers={})
        assert False, "expected missing handler to fail"
    except CanonExecutionError as exc:
        assert exc.classification == "invariant_violation"
        assert exc.node_id == "a"


def test_executor_translates_cancelled_context_to_structured_error():
    graph = GraphSpec(
        nodes=(NodeSpec("a", "const", EffectClass.PURE_DETERMINISTIC),),
        requested_outputs=(OutputRef("a"),),
    )
    context = ExecutionContext()
    context.cancellation.cancel("stop now")

    try:
        CanonExecutor().execute(graph, handlers={"const": lambda *_: {"result": 1}}, context=context)
        assert False, "expected cancelled execution to fail"
    except CanonExecutionError as exc:
        assert exc.classification == "cancelled"
        assert exc.node_id is None


def test_executor_translates_expired_deadline_to_timeout_error():
    graph = GraphSpec(
        nodes=(NodeSpec("a", "const", EffectClass.PURE_DETERMINISTIC),),
        requested_outputs=(OutputRef("a"),),
    )
    context = ExecutionContext(deadline_unix_ms=0)

    try:
        CanonExecutor().execute(graph, handlers={"const": lambda *_: {"result": 1}}, context=context)
        assert False, "expected expired deadline to fail"
    except CanonExecutionError as exc:
        assert exc.classification == "timeout"
        assert exc.node_id is None

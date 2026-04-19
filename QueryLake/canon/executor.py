from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from .context import ExecutionContext
from .models import GraphSpec, NodeSpec, OutputRef
from .results import ExecutionResult, ExecutionSummary, NodeExecutionResult


class CanonExecutionError(RuntimeError):
    def __init__(self, message: str, classification: str, node_id: str | None = None):
        super().__init__(message)
        self.classification = classification
        self.node_id = node_id

    def __str__(self) -> str:
        if self.node_id:
            return f"{self.classification}: {self.node_id}: {super().__str__()}"
        return f"{self.classification}: {super().__str__()}"


NodeHandler = Callable[[NodeSpec, Mapping[str, Any], ExecutionContext], Mapping[str, Any]]


class CanonExecutor:
    """Minimal demand-driven executor for Phase 1A Milestone 2A.

    This intentionally proves only bounded structural semantics:
    graph acceptance, dependency traversal, per-run memoization, and
    structured result envelopes. It is not the full Canon++ kernel.
    """

    def execute(
        self,
        graph: GraphSpec,
        handlers: Mapping[str, NodeHandler],
        context: ExecutionContext | None = None,
        requested_outputs: tuple[OutputRef, ...] | None = None,
    ) -> ExecutionResult:
        execution_context = context or ExecutionContext()
        desired_outputs = requested_outputs or graph.requested_outputs
        node_map = graph.node_map
        executed: dict[str, dict[str, Any]] = {}
        node_results: list[NodeExecutionResult] = []

        def run_node(node_id: str) -> dict[str, Any]:
            execution_context.check_open()
            if node_id in executed:
                return executed[node_id]

            node = node_map[node_id]
            resolved_inputs: dict[str, Any] = {}
            for dependency in node.dependencies:
                parent_outputs = run_node(dependency.node_id)
                resolved_inputs[dependency.key] = parent_outputs[dependency.output_name]

            handler = handlers.get(node.operation)
            if handler is None:
                raise CanonExecutionError(
                    f"No handler registered for operation '{node.operation}'",
                    classification="invariant_violation",
                    node_id=node.node_id,
                )

            try:
                raw_outputs = dict(handler(node, resolved_inputs, execution_context))
            except TimeoutError as exc:
                raise CanonExecutionError(
                    str(exc), classification="timeout", node_id=node.node_id
                ) from exc
            except RuntimeError as exc:
                raise CanonExecutionError(
                    str(exc), classification="internal_error", node_id=node.node_id
                ) from exc

            missing_outputs = [name for name in node.output_names if name not in raw_outputs]
            if missing_outputs:
                raise CanonExecutionError(
                    f"Handler '{node.operation}' did not return required outputs {missing_outputs}",
                    classification="invariant_violation",
                    node_id=node.node_id,
                )

            executed[node_id] = raw_outputs
            node_results.append(
                NodeExecutionResult(
                    node_id=node.node_id,
                    operation=node.operation,
                    effect_class=node.effect_class,
                    status="success",
                    output_names=tuple(sorted(raw_outputs.keys())),
                )
            )
            return raw_outputs

        outputs: dict[str, Any] = {}
        for output_ref in desired_outputs:
            node_outputs = run_node(output_ref.node_id)
            outputs[output_ref.key] = node_outputs[output_ref.output_name]

        summary = ExecutionSummary(
            graph_id=graph.graph_id,
            execution_mode=execution_context.mode,
            requested_output_keys=tuple(ref.key for ref in desired_outputs),
            total_nodes_defined=len(graph.nodes),
            executed_node_ids=tuple(result.node_id for result in node_results),
            node_results=tuple(node_results),
        )
        return ExecutionResult(graph_id=graph.graph_id, outputs=outputs, summary=summary)

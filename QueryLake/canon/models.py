from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Mapping

from .effects import EffectClass


@dataclass(frozen=True, slots=True)
class OutputRef:
    node_id: str
    output_name: str = "result"

    def __post_init__(self) -> None:
        if not self.node_id or not self.node_id.strip():
            raise ValueError("OutputRef.node_id must be non-empty")
        if not self.output_name or not self.output_name.strip():
            raise ValueError("OutputRef.output_name must be non-empty")

    @property
    def key(self) -> str:
        return f"{self.node_id}.{self.output_name}"


@dataclass(frozen=True, slots=True)
class NodeSpec:
    node_id: str
    operation: str
    effect_class: EffectClass
    dependencies: tuple[OutputRef, ...] = field(default_factory=tuple)
    output_names: tuple[str, ...] = ("result",)
    config: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.node_id or not self.node_id.strip():
            raise ValueError("NodeSpec.node_id must be non-empty")
        if not self.operation or not self.operation.strip():
            raise ValueError("NodeSpec.operation must be non-empty")
        if not isinstance(self.effect_class, EffectClass):
            object.__setattr__(self, "effect_class", EffectClass(self.effect_class))
        deps = tuple(self.dependencies)
        outputs = tuple(self.output_names)
        if not outputs:
            raise ValueError("NodeSpec.output_names must not be empty")
        if len(set(outputs)) != len(outputs):
            raise ValueError("NodeSpec.output_names must be unique")
        if any(not name or not name.strip() for name in outputs):
            raise ValueError("NodeSpec.output_names must contain non-empty names")
        object.__setattr__(self, "dependencies", deps)
        object.__setattr__(self, "output_names", outputs)
        object.__setattr__(self, "config", dict(self.config))

    def validate_references(self, known_outputs: Mapping[str, set[str]]) -> None:
        for dependency in self.dependencies:
            if dependency.node_id not in known_outputs:
                raise ValueError(
                    f"NodeSpec '{self.node_id}' depends on unknown node '{dependency.node_id}'"
                )
            if dependency.output_name not in known_outputs[dependency.node_id]:
                raise ValueError(
                    f"NodeSpec '{self.node_id}' depends on unknown output "
                    f"'{dependency.output_name}' from node '{dependency.node_id}'"
                )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "operation": self.operation,
            "effect_class": self.effect_class.value,
            "dependencies": [
                {"node_id": ref.node_id, "output_name": ref.output_name}
                for ref in self.dependencies
            ],
            "output_names": list(self.output_names),
            "config": dict(sorted(self.config.items())),
        }


@dataclass(frozen=True, slots=True)
class GraphSpec:
    nodes: tuple[NodeSpec, ...]
    requested_outputs: tuple[OutputRef, ...]
    graph_name: str = "canon_graph_v1"

    def __post_init__(self) -> None:
        nodes = tuple(self.nodes)
        requested_outputs = tuple(self.requested_outputs)
        if not nodes:
            raise ValueError("GraphSpec.nodes must not be empty")
        if not requested_outputs:
            raise ValueError("GraphSpec.requested_outputs must not be empty")
        ids = [node.node_id for node in nodes]
        if len(set(ids)) != len(ids):
            raise ValueError("GraphSpec node ids must be unique")
        known_outputs = {node.node_id: set(node.output_names) for node in nodes}
        for node in nodes:
            node.validate_references(known_outputs)
        for output_ref in requested_outputs:
            if output_ref.node_id not in known_outputs:
                raise ValueError(
                    f"GraphSpec requested output references unknown node '{output_ref.node_id}'"
                )
            if output_ref.output_name not in known_outputs[output_ref.node_id]:
                raise ValueError(
                    f"GraphSpec requested output references unknown output '{output_ref.output_name}' "
                    f"from node '{output_ref.node_id}'"
                )
        object.__setattr__(self, "nodes", nodes)
        object.__setattr__(self, "requested_outputs", requested_outputs)

    @property
    def node_map(self) -> dict[str, NodeSpec]:
        return {node.node_id: node for node in self.nodes}

    @property
    def graph_id(self) -> str:
        payload = {
            "graph_name": self.graph_name,
            "nodes": [node.to_canonical_dict() for node in self.nodes],
            "requested_outputs": [
                {"node_id": ref.node_id, "output_name": ref.output_name}
                for ref in self.requested_outputs
            ],
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        digest = hashlib.sha256(raw).hexdigest()[:16]
        return f"graph-{digest}"

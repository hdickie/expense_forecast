from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any

from .models import ChangeSet, DirtyRange, EvaluationResult, GraphExecutionDiagnostics, VariableKey, stable_fingerprint


@dataclass
class GraphContext:
    values: dict[VariableKey, Any] = field(default_factory=dict)
    fingerprints: dict[VariableKey, str] = field(default_factory=dict)
    checkpoints: dict[str, dict] = field(default_factory=dict)
    diagnostics: GraphExecutionDiagnostics = field(default_factory=GraphExecutionDiagnostics)

    def write(self, key, value):
        fingerprint = stable_fingerprint(value)
        changed = self.fingerprints.get(key) != fingerprint
        self.values[key] = value
        self.fingerprints[key] = fingerprint
        return changed


class GraphNode(ABC):
    def __init__(self, node_id, inputs=(), outputs=()):
        self.node_id = str(node_id)
        self.inputs = frozenset(inputs)
        self.outputs = frozenset(outputs)

    def invalidate(self, change: ChangeSet):
        return change.dirty_range if self.inputs & change.variables else None

    @abstractmethod
    def evaluate(self, context: GraphContext, dirty_range: DirtyRange):
        raise NotImplementedError


class FixedPointNode(GraphNode):
    """Scaffold for cyclic components; financial solvers arrive in later slices."""

    def __init__(self, *args, convergence_tolerance=None, max_iterations=100, **kwargs):
        super().__init__(*args, **kwargs)
        self.convergence_tolerance = convergence_tolerance
        self.max_iterations = max_iterations


class ComputationGraph:
    def __init__(self, nodes, fixed_point_evaluators=None):
        nodes = list(nodes)
        self.nodes = {node.node_id: node for node in nodes}
        if len(self.nodes) != len(nodes):
            raise ValueError("Duplicate graph node id")
        self.fixed_point_evaluators = dict(fixed_point_evaluators or {})
        self.producer = {}
        for node in self.nodes.values():
            for output in node.outputs:
                if output in self.producer:
                    raise ValueError(
                        f"Multiple writers for {output}: {self.producer[output]} and {node.node_id}"
                    )
                self.producer[output] = node.node_id
        self.downstream = defaultdict(set)
        self.upstream = defaultdict(set)
        for node in self.nodes.values():
            for input_key in node.inputs:
                producer = self.producer.get(input_key)
                if producer is not None:
                    self.downstream[producer].add(node.node_id)
                    self.upstream[node.node_id].add(producer)
        self.order = self._topological_order()

    def _topological_order(self):
        indegree = {node_id: len(self.upstream[node_id]) for node_id in self.nodes}
        queue = deque(sorted(node_id for node_id, degree in indegree.items() if degree == 0))
        order = []
        while queue:
            node_id = queue.popleft()
            order.append(node_id)
            for child in sorted(self.downstream[node_id]):
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)
        if len(order) != len(self.nodes):
            cyclic = sorted(node_id for node_id, degree in indegree.items() if degree > 0)
            if not all(node_id in self.fixed_point_evaluators for node_id in cyclic):
                raise ValueError(
                    "Cyclic graph component requires a fixed-point evaluator: "
                    + ", ".join(cyclic)
                )
            order.extend(cyclic)
        return order

    def evaluate(self, context, change):
        dirty = {}
        for node_id in self.order:
            node = self.nodes[node_id]
            invalidated = node.invalidate(change)
            upstream_ranges = [dirty[parent] for parent in self.upstream[node_id] if parent in dirty]
            for upstream_range in upstream_ranges:
                invalidated = upstream_range if invalidated is None else invalidated.merge(upstream_range)
            if invalidated is None:
                context.diagnostics.nodes_skipped.append(node_id)
                continue
            result = node.evaluate(context, invalidated)
            context.diagnostics.nodes_evaluated.append(node_id)
            context.diagnostics.dirty_ranges[node_id] = invalidated
            context.diagnostics.events_recomputed += result.events_recomputed
            context.diagnostics.checkpoints_reused += result.checkpoints_reused
            if result.stable_from is not None:
                context.diagnostics.reconvergence_points.append(result.stable_from)
            if result.changed_outputs:
                dirty[node_id] = result.changed_range or invalidated
        return context

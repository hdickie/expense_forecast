from datetime import date

import pytest

from expense_forecast.graph_engine.graph import ComputationGraph, GraphContext, GraphNode
from expense_forecast.graph_engine.models import ChangeSet, DirtyRange, EvaluationResult, EventKey, VariableKey


class CopyNode(GraphNode):
    def evaluate(self, context, dirty_range):
        value = sum(context.values.get(key, 0) for key in self.inputs)
        changed = False
        for output in self.outputs:
            changed |= context.write(output, value)
        return EvaluationResult(set(self.outputs) if changed else set(), dirty_range, events_recomputed=1)


def test_dirty_ranges_merge_and_preserve_open_ended_suffix():
    first = DirtyRange(EventKey(date(2026, 2, 1), "a"), EventKey(date(2026, 2, 5), "b"))
    second = DirtyRange(EventKey(date(2026, 1, 1), "c"))

    merged = first.merge(second)

    assert merged.start.date == date(2026, 1, 1)
    assert merged.end is None


def test_graph_rejects_multiple_output_writers():
    output = VariableKey("state", "cash")
    with pytest.raises(ValueError, match="Multiple writers"):
        ComputationGraph([
            CopyNode("one", outputs=[output]),
            CopyNode("two", outputs=[output]),
        ])


def test_graph_rejects_cycle_without_fixed_point_evaluator():
    left, right = VariableKey("state", "left"), VariableKey("state", "right")
    with pytest.raises(ValueError, match="fixed-point"):
        ComputationGraph([
            CopyNode("left", inputs=[right], outputs=[left]),
            CopyNode("right", inputs=[left], outputs=[right]),
        ])


def test_scheduler_propagates_only_from_changed_outputs():
    source = VariableKey("input", "source")
    middle = VariableKey("state", "middle")
    final = VariableKey("state", "final")
    graph = ComputationGraph([
        CopyNode("middle", inputs=[source], outputs=[middle]),
        CopyNode("final", inputs=[middle], outputs=[final]),
    ])
    context = GraphContext(values={source: 5})
    context.fingerprints[source] = "input"
    event = EventKey(date(2026, 1, 1), "start")
    change = ChangeSet.create([source], DirtyRange(event), "test")

    graph.evaluate(context, change)

    assert context.values[final] == 5
    assert context.diagnostics.nodes_evaluated == ["middle", "final"]

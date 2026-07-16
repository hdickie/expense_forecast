from __future__ import annotations

import datetime
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Iterable


@dataclass(frozen=True, order=True)
class VariableKey:
    namespace: str
    name: str

    def __str__(self):
        return f"{self.namespace}.{self.name}"


@dataclass(frozen=True, order=True)
class EventKey:
    date: datetime.date
    occurrence_id: str
    sequence: int = 0


@dataclass(frozen=True)
class DirtyRange:
    start: EventKey
    end: EventKey | None = None

    def merge(self, other: "DirtyRange") -> "DirtyRange":
        start = min(self.start, other.start)
        if self.end is None or other.end is None:
            end = None
        else:
            end = max(self.end, other.end)
        return DirtyRange(start, end)

    def contains(self, event_key: EventKey) -> bool:
        return event_key >= self.start and (self.end is None or event_key <= self.end)


@dataclass(frozen=True)
class ChangeSet:
    variables: frozenset[VariableKey]
    dirty_range: DirtyRange
    cause: str
    provenance: tuple[str, ...] = ()

    @classmethod
    def create(cls, variables: Iterable[VariableKey], dirty_range, cause, provenance=()):
        return cls(frozenset(variables), dirty_range, cause, tuple(provenance))


@dataclass
class EvaluationResult:
    changed_outputs: set[VariableKey] = field(default_factory=set)
    changed_range: DirtyRange | None = None
    stable_from: EventKey | None = None
    events_recomputed: int = 0
    checkpoints_reused: int = 0
    provenance: list[str] = field(default_factory=list)


@dataclass
class GraphExecutionDiagnostics:
    engine: str = "graph"
    nodes_evaluated: list[str] = field(default_factory=list)
    nodes_skipped: list[str] = field(default_factory=list)
    dirty_ranges: dict[str, DirtyRange] = field(default_factory=dict)
    checkpoints_reused: int = 0
    events_recomputed: int = 0
    reconvergence_points: list[EventKey] = field(default_factory=list)
    wall_seconds: float = 0.0
    legacy_shadow_seconds: float | None = None
    cache_hits: int = 0
    billing_cycles_recomputed: int = 0
    investment_spans_recomputed: int = 0
    policy_iterations: int = 0
    converged_components: list[str] = field(default_factory=list)


def stable_fingerprint(value: Any) -> str:
    def normalize(item):
        if isinstance(item, (datetime.date, datetime.datetime)):
            return item.isoformat()
        if hasattr(item, "to_dict"):
            return normalize(item.to_dict())
        if isinstance(item, dict):
            return {str(key): normalize(val) for key, val in sorted(item.items(), key=lambda pair: str(pair[0]))}
        if isinstance(item, (list, tuple)):
            return [normalize(val) for val in item]
        return str(item)

    payload = json.dumps(normalize(value), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

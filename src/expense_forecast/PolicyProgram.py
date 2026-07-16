"""Time-varying forecast policy configuration and compiled regime records."""

from __future__ import annotations

import copy
import datetime
from dataclasses import dataclass, field

from expense_forecast.ForecastPolicy import ForecastPolicy
from expense_forecast.ForecastPolicySet import ForecastPolicySet


@dataclass
class DatedPolicyChange:
    """Atomically add, replace, and remove policies at the start of a date."""

    effective_date: datetime.date
    add: list[ForecastPolicy] = field(default_factory=list)
    replace: list[ForecastPolicy] = field(default_factory=list)
    remove: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not isinstance(self.effective_date, datetime.date):
            raise TypeError("effective_date must be a datetime.date")
        self.add = list(self.add or [])
        self.replace = list(self.replace or [])
        self.remove = list(self.remove or [])
        for policy in self.add + self.replace:
            if not isinstance(policy, ForecastPolicy):
                raise TypeError("add and replace accept ForecastPolicy instances")
        if any(not isinstance(key, str) or not key.strip() for key in self.remove):
            raise ValueError("remove accepts non-empty policy keys")
        keys = [policy.policy_key for policy in self.add + self.replace] + self.remove
        if len(keys) != len(set(keys)):
            raise ValueError("A dated policy change may modify each policy key once")

    @classmethod
    def bounded(cls, start_date, end_date, *, add=None, replace=None, remove=None):
        """Return start/end changes for a half-open ``[start, end)`` override."""
        if not isinstance(end_date, datetime.date) or end_date <= start_date:
            raise ValueError("end_date must be after start_date")
        additions = list(add or [])
        replacements = list(replace or [])
        removals = list(remove or [])
        start = cls(start_date, additions, replacements, removals)
        # Restoration is resolved by PolicyProgram because it needs the policy
        # state immediately before the bounded change.
        start._bounded_end_date = end_date
        return start


@dataclass
class PolicyRegime:
    regime_id: str
    start_date: datetime.date
    end_date: datetime.date
    active_policy_keys: list[str]
    source: str = "configured"
    changes: list[str] = field(default_factory=list)
    derived_transformations: list[str] = field(default_factory=list)
    proofs: list[str] = field(default_factory=list)
    invalidation_reason: str | None = None
    analytical_decisions: int = 0
    recursive_decisions: int = 0
    execution_seconds: float = 0.0
    recomputed_nodes: int = 0
    suffix_forecasts_avoided: int = 0


class PolicyProgram:
    """A base policy set plus persistent, date-effective modifications."""

    def __init__(self, base_policy_set=None, dated_changes=None):
        base_policy_set = base_policy_set or ForecastPolicySet()
        if not isinstance(base_policy_set, ForecastPolicySet):
            raise TypeError("base_policy_set must be a ForecastPolicySet")
        self.base_policy_set = copy.deepcopy(base_policy_set)
        self.dated_changes = sorted(
            copy.deepcopy(list(dated_changes or [])),
            key=lambda change: change.effective_date,
        )
        if any(not isinstance(change, DatedPolicyChange) for change in self.dated_changes):
            raise TypeError("dated_changes must contain DatedPolicyChange instances")
        dates = [change.effective_date for change in self.dated_changes]
        if len(dates) != len(set(dates)):
            raise ValueError("Only one DatedPolicyChange is allowed per effective date")
        self._expand_bounded_changes()
        self._validate_sequence()

    @property
    def policies(self):
        """Compatibility view of policies active before the first dated change."""
        return self.base_policy_set.policies

    def __bool__(self):
        return bool(self.base_policy_set) or bool(self.dated_changes)

    def _apply(self, policy_set, change):
        active = {policy.policy_key: copy.deepcopy(policy) for policy in policy_set.policies}
        for key in change.remove:
            if key not in active:
                raise ValueError(f"Cannot remove inactive policy key: {key}")
            active.pop(key)
        for policy in change.replace:
            if policy.policy_key not in active:
                raise ValueError(f"Cannot replace inactive policy key: {policy.policy_key}")
            active[policy.policy_key] = copy.deepcopy(policy)
        for policy in change.add:
            if policy.policy_key in active:
                raise ValueError(f"Cannot add active policy key: {policy.policy_key}")
            active[policy.policy_key] = copy.deepcopy(policy)
        return ForecastPolicySet(list(active.values()))

    def _expand_bounded_changes(self):
        expanded = []
        current = copy.deepcopy(self.base_policy_set)
        for change in self.dated_changes:
            before = copy.deepcopy(current)
            current = self._apply(current, change)
            expanded.append(change)
            end_date = getattr(change, "_bounded_end_date", None)
            if end_date is not None:
                before_by_key = {policy.policy_key: policy for policy in before.policies}
                after_by_key = {policy.policy_key: policy for policy in current.policies}
                restore_remove = [key for key in after_by_key if key not in before_by_key]
                restore_add = [policy for key, policy in before_by_key.items() if key not in after_by_key]
                restore_replace = [
                    policy for key, policy in before_by_key.items()
                    if key in after_by_key
                ]
                expanded.append(DatedPolicyChange(
                    end_date,
                    add=restore_add,
                    replace=restore_replace,
                    remove=restore_remove,
                ))
                current = before
        self.dated_changes = sorted(expanded, key=lambda item: item.effective_date)

    def _validate_sequence(self):
        current = copy.deepcopy(self.base_policy_set)
        for change in self.dated_changes:
            current = self._apply(current, change)

    def resolve(self, on_date):
        if not isinstance(on_date, datetime.date):
            raise TypeError("on_date must be a datetime.date")
        current = copy.deepcopy(self.base_policy_set)
        for change in self.dated_changes:
            if change.effective_date > on_date:
                break
            current = self._apply(current, change)
        return current

    def phase_boundaries(self, start_date, end_date):
        return [start_date] + [
            change.effective_date for change in self.dated_changes
            if start_date < change.effective_date <= end_date
        ]


__all__ = ["DatedPolicyChange", "PolicyProgram", "PolicyRegime"]

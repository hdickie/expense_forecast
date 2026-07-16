"""Lightweight dependency graph used by analytical policy constraints."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class PolicyEventNode:
    node_id: str
    date: object
    priority: int
    amount: Decimal
    memo: str
    account_from: str | None
    account_to: str | None
    dependencies: tuple[str, ...] = field(default_factory=tuple)


class PolicyEventGraph:
    """Index scheduled cash-flow nodes by account, date, and priority."""

    def __init__(self, nodes=None):
        self.nodes = list(nodes or [])

    @classmethod
    def from_schedule(cls, schedule, memo_rule_set):
        nodes = []
        previous_by_account = {}
        for index, row in schedule.sort_values(["Date", "Priority"]).iterrows():
            rule = memo_rule_set.findMatchingMemoRule(row["Memo"], row["Priority"])
            accounts = [
                value for value in (rule.account_from, rule.account_to)
                if value not in (None, "", "None")
            ]
            dependencies = tuple(
                previous_by_account[account]
                for account in accounts
                if account in previous_by_account
            )
            node_id = f"event-{index}-{row['Date']}-{row['Priority']}"
            node = PolicyEventNode(
                node_id=node_id,
                date=row["Date"],
                priority=int(row["Priority"]),
                amount=Decimal(str(row["Amount"])),
                memo=str(row["Memo"]),
                account_from=rule.account_from,
                account_to=rule.account_to,
                dependencies=dependencies,
            )
            nodes.append(node)
            for account in accounts:
                previous_by_account[account] = node_id
        return cls(nodes)

    def reserve_requirement(self, account_name, after_date, policy_priority):
        running = Decimal("0")
        maximum = Decimal("0")
        binding_date = None
        affected = []
        for node in self.nodes:
            if node.date <= after_date or node.priority >= int(policy_priority):
                continue
            if node.account_from == account_name:
                running += node.amount
                affected.append(node.node_id)
            if node.account_to == account_name:
                running -= node.amount
                affected.append(node.node_id)
            if running > maximum:
                maximum = running
                binding_date = node.date
        return maximum, binding_date, affected

    def has_reachable_outflow(self, account_name, after_date=None):
        return any(
            node.account_from == account_name
            and (after_date is None or node.date >= after_date)
            for node in self.nodes
        )

    def future_incoming(self, account_names, after_date, policy_priority):
        names = set(account_names)
        return sum(
            (
                node.amount for node in self.nodes
                if node.date > after_date
                and node.priority < int(policy_priority)
                and node.account_to in names
            ),
            Decimal("0"),
        )


__all__ = ["PolicyEventGraph", "PolicyEventNode"]

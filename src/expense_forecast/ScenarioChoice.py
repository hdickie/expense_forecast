"""Structured configuration contributed by one scenario choice."""

import copy
import json
import jsonpickle

from expense_forecast.AccountSet import AccountSet
from expense_forecast.ConditionalScenarioTransitionSet import (
    ConditionalScenarioTransitionSet,
)
from expense_forecast.ForecastPolicySet import ForecastPolicySet
from expense_forecast.LineItemSet import LineItemSet
from expense_forecast.MemoRuleSet import MemoRuleSet


def overlay_account_sets(base, addition):
    """Add accounts without permitting an existing definition to change."""
    if not isinstance(base, AccountSet) or not isinstance(addition, AccountSet):
        raise TypeError("account overlays require AccountSet instances")
    result = copy.deepcopy(base)
    existing = {
        row["Name"]: row
        for row in result.to_dict()["accounts"]
    }
    addition_rows = {
        row["Name"]: row
        for row in addition.to_dict()["accounts"]
    }
    for account in addition.accounts:
        row = addition_rows[account.name]
        if account.name in existing:
            if existing[account.name] != row:
                raise ValueError(
                    f"Conflicting account definition for {account.name!r}"
                )
            continue
        if getattr(account, "primary_checking_ind", False):
            raise ValueError(
                "ScenarioChoice cannot add or replace the primary checking "
                f"account {account.name!r}"
            )
        result.accounts.append(copy.deepcopy(account))
        existing[account.name] = row
    AccountSet._validate_unique_names(result.getAccounts())
    return result


def extend_account_schema(state, schema):
    """Add accounts missing from a live balance state without resetting it."""
    if not isinstance(state, AccountSet) or not isinstance(schema, AccountSet):
        raise TypeError("account schema extension requires AccountSet instances")
    result = copy.deepcopy(state)
    existing_names = {account.name for account in result.accounts}
    for account in schema.accounts:
        if account.name not in existing_names:
            result.accounts.append(copy.deepcopy(account))
            existing_names.add(account.name)
    AccountSet._validate_unique_names(result.getAccounts())
    return result


def overlay_memo_rule_sets(base, overlay):
    """Overlay memo rules using regex and priority as the semantic key."""
    if not isinstance(base, MemoRuleSet) or not isinstance(overlay, MemoRuleSet):
        raise TypeError("memo-rule overlays require MemoRuleSet instances")
    rules = copy.deepcopy(base.memo_rules)
    positions = {
        (rule.memo_regex, rule.transaction_priority): index
        for index, rule in enumerate(rules)
    }
    for rule in overlay.memo_rules:
        key = (rule.memo_regex, rule.transaction_priority)
        candidate = copy.deepcopy(rule)
        if key in positions:
            rules[positions[key]] = candidate
        else:
            positions[key] = len(rules)
            rules.append(candidate)
    result = MemoRuleSet(rules)
    result.memoized_rule_matches = {}
    return result


def overlay_policy_sets(base, overlay):
    """Overlay policies by policy key while retaining declaration position."""
    if not isinstance(base, ForecastPolicySet) or not isinstance(
        overlay, ForecastPolicySet
    ):
        raise TypeError("policy overlays require ForecastPolicySet instances")
    policies = copy.deepcopy(base.policies)
    positions = {
        policy.policy_key: index
        for index, policy in enumerate(policies)
    }
    for policy in overlay.policies:
        candidate = copy.deepcopy(policy)
        if policy.policy_key in positions:
            policies[positions[policy.policy_key]] = candidate
        else:
            positions[policy.policy_key] = len(policies)
            policies.append(candidate)
    return ForecastPolicySet(*policies)


def overlay_transition_sets(base, overlay):
    """Append activated transitions while enforcing global uniqueness."""
    if not isinstance(base, ConditionalScenarioTransitionSet) or not isinstance(
        overlay, ConditionalScenarioTransitionSet
    ):
        raise TypeError(
            "transition overlays require ConditionalScenarioTransitionSet instances"
        )
    return ConditionalScenarioTransitionSet(
        *copy.deepcopy(base.transitions),
        *copy.deepcopy(overlay.transitions),
    )


class ScenarioChoice:
    """Bundle the transactions, policies, and transitions for one choice."""

    def __init__(
        self,
        line_item_set=None,
        account_set=None,
        memo_rule_set=None,
        policy_set=None,
        transition_set=None,
    ):
        line_items = line_item_set or LineItemSet()
        accounts = account_set or AccountSet()
        memo_rules = memo_rule_set or MemoRuleSet()
        policies = policy_set or ForecastPolicySet()
        transitions = transition_set or ConditionalScenarioTransitionSet()
        if not isinstance(line_items, LineItemSet):
            raise TypeError("line_item_set must be a LineItemSet")
        if not isinstance(accounts, AccountSet):
            raise TypeError("account_set must be an AccountSet")
        if not isinstance(memo_rules, MemoRuleSet):
            raise TypeError("memo_rule_set must be a MemoRuleSet")
        if not isinstance(policies, ForecastPolicySet):
            raise TypeError("policy_set must be a ForecastPolicySet")
        if not isinstance(transitions, ConditionalScenarioTransitionSet):
            raise TypeError(
                "transition_set must be a ConditionalScenarioTransitionSet"
            )
        if line_items.scenario_selections:
            raise ValueError(
                "ScenarioChoice line_item_set cannot contain scenario selections"
            )
        self.line_item_set = copy.deepcopy(line_items)
        self.account_set = copy.deepcopy(accounts)
        self.memo_rule_set = copy.deepcopy(memo_rules)
        self.policy_set = copy.deepcopy(policies)
        self.transition_set = copy.deepcopy(transitions)

    @property
    def line_items(self):
        """Expose the familiar choice-template line items for inspection."""
        return self.line_item_set.line_items

    def to_dict(self):
        return {
            "line_item_set": self.line_item_set.to_dict(),
            "account_set": self.account_set.to_dict(),
            "memo_rule_set": self.memo_rule_set.to_dict(),
            "policy_set": json.loads(jsonpickle.encode(self.policy_set)),
            "transition_set": json.loads(
                jsonpickle.encode(self.transition_set)
            ),
        }

    @classmethod
    def from_dict(cls, data):
        """Read structured choices and legacy line-item-only payloads."""
        if "line_item_set" not in data:
            return cls(line_item_set=LineItemSet.from_dict(data))
        return cls(
            line_item_set=LineItemSet.from_dict(data["line_item_set"]),
            account_set=AccountSet.from_dict(
                data.get("account_set", {"accounts": []})
            ),
            memo_rule_set=MemoRuleSet.from_dict(
                data.get("memo_rule_set", {"memo_rules": []})
            ),
            policy_set=copy.deepcopy(
                jsonpickle.decode(json.dumps(data["policy_set"]))
                if data.get("policy_set") else ForecastPolicySet()
            ),
            transition_set=copy.deepcopy(
                jsonpickle.decode(json.dumps(data["transition_set"]))
                if data.get("transition_set")
                else ConditionalScenarioTransitionSet()
            ),
        )

    @classmethod
    def normalize(cls, value):
        """Preserve the convenient legacy shorthand of supplying line items."""
        if isinstance(value, cls):
            return copy.deepcopy(value)
        if isinstance(value, LineItemSet):
            return cls(line_item_set=value)
        raise TypeError(
            "ScenarioDimension choices must be ScenarioChoice or LineItemSet "
            "instances"
        )

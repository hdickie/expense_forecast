"""
Summary
-------

Description
-----------

Contract
--------

@interface-report: show
"""


#Scenario.py

# Scenario:
#     label: "Nursing school + Weekend CNA"
#     choices: {
#         "School": "Nursing school",
#         "Work": "Weekend CNA"
#     }
#     line_item_set: BudgetSet(...)


import copy

from expense_forecast.ForecastPolicySet import ForecastPolicySet
from expense_forecast.LineItemSet import LineItemSet
from expense_forecast.ConditionalScenarioTransitionSet import (
    ConditionalScenarioTransitionSet,
)
from expense_forecast.AccountSet import AccountSet
from expense_forecast.MemoRuleSet import MemoRuleSet
from expense_forecast.ScenarioChoice import (
    overlay_account_sets,
    overlay_memo_rule_sets,
)


#TODO DEFER manual review of Scenario docstring
class Scenario:

    """
    Summary
    -------

    Description
    -----------

    Contract
    --------

    @interface-report: show
    """
    #TODO DEFER manual review of Scenario.__init__ docstring
    def __init__(
        self, label, choices, line_item_set, policy_set=None,
        transition_set=None, account_set=None, memo_rule_set=None,
    ):
        """
        #TODO DEFER one-line description of Scenario.__init__.

        #TODO DEFER multi-line description of Scenario.__init__.
        #TODO DEFER explain how Scenario.__init__ participates in this module.
        #TODO DEFER document important state, validation, or serialization behavior.

        Parameters
        ----------
        label : str
            #TODO DEFER one-line description of Scenario.__init__.label.

        choices : object
            #TODO DEFER one-line description of Scenario.__init__.choices.

        line_item_set : object
            #TODO DEFER one-line description of Scenario.__init__.line_item_set.

        Returns
        -------
        None

        Contract
        --------
        - #TODO DEFER contract lines for Scenario.__init__.
        - #TODO DEFER document exceptions, mutations, and precision assumptions for Scenario.__init__.

        @interface-report: show
        """
        if not isinstance(label, str):
            raise TypeError("label must be a string")
        if not isinstance(choices, dict):
            raise TypeError("choices must be a mapping")
        if not isinstance(line_item_set, LineItemSet):
            raise TypeError("line_item_set must be a LineItemSet")
        configured = policy_set or ForecastPolicySet()
        configured_transitions = (
            transition_set or ConditionalScenarioTransitionSet()
        )
        configured_accounts = account_set or AccountSet()
        configured_memo_rules = memo_rule_set or MemoRuleSet()
        if not isinstance(configured, ForecastPolicySet):
            raise TypeError("policy_set must be a ForecastPolicySet")
        if not isinstance(
            configured_transitions, ConditionalScenarioTransitionSet
        ):
            raise TypeError(
                "transition_set must be a ConditionalScenarioTransitionSet"
            )
        if not isinstance(configured_accounts, AccountSet):
            raise TypeError("account_set must be an AccountSet")
        if not isinstance(configured_memo_rules, MemoRuleSet):
            raise TypeError("memo_rule_set must be a MemoRuleSet")
        self.label = label
        self.choices = dict(choices)
        self.line_item_set = copy.deepcopy(line_item_set)
        self.policy_set = copy.deepcopy(configured)
        self.transition_set = copy.deepcopy(configured_transitions)
        self.account_set = copy.deepcopy(configured_accounts)
        self.memo_rule_set = copy.deepcopy(configured_memo_rules)

    @property
    def line_items(self):
        return self.line_item_set.line_items

    def with_policy_set(self, policy_set):
        """Return an independent copy of this scenario with new policies.

        ScenarioSpace may reuse its generated Scenario objects across several
        forecasts.  Returning a copy keeps fluent configuration from changing
        either the space or another forecast built from the same selection.
        """
        if not isinstance(policy_set, ForecastPolicySet):
            raise TypeError("policy_set must be a ForecastPolicySet")
        return Scenario(
            label=self.label,
            choices=self.choices,
            line_item_set=self.line_item_set,
            policy_set=policy_set,
            transition_set=self.transition_set,
            account_set=self.account_set,
            memo_rule_set=self.memo_rule_set,
        )

    def to_initial_conditions(
        self, start_date, end_date, account_set, memo_rule_set, **kwargs
    ):
        from expense_forecast.ExpenseForecastInitialConditions import (
            ExpenseForecastInitialConditions,
        )

        supplied_transition_set = kwargs.pop("transition_set", None)
        if supplied_transition_set is not None and not isinstance(
            supplied_transition_set, ConditionalScenarioTransitionSet
        ):
            raise TypeError(
                "transition_set must be a ConditionalScenarioTransitionSet"
            )
        transitions = ConditionalScenarioTransitionSet(
            *self.transition_set.transitions,
            *(
                supplied_transition_set.transitions
                if supplied_transition_set is not None else []
            ),
        )
        resolved_accounts = overlay_account_sets(
            account_set, self.account_set
        )
        resolved_memo_rules = overlay_memo_rule_sets(
            memo_rule_set, self.memo_rule_set
        )
        return ExpenseForecastInitialConditions(
            start_date=start_date,
            end_date=end_date,
            account_set=resolved_accounts,
            line_item_set=copy.deepcopy(self.line_item_set),
            memo_rule_set=resolved_memo_rules,
            policy_set=copy.deepcopy(self.policy_set),
            transition_set=copy.deepcopy(transitions),
            **kwargs,
        )

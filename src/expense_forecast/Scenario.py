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
from expense_forecast.PolicyProgram import PolicyProgram


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
        self, label, choices, line_item_set, policy_set=None, policy_program=None
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
        if policy_set is not None and policy_program is not None:
            raise ValueError("Specify policy_set or policy_program, not both")
        configured = policy_program or policy_set or ForecastPolicySet()
        if not isinstance(configured, (ForecastPolicySet, PolicyProgram)):
            raise TypeError("policy configuration must be ForecastPolicySet or PolicyProgram")
        self.label = label
        self.choices = dict(choices)
        self.line_item_set = copy.deepcopy(line_item_set)
        self.policy_program = copy.deepcopy(
            configured if isinstance(configured, PolicyProgram) else PolicyProgram(configured)
        )
        self.policy_set = copy.deepcopy(self.policy_program.base_policy_set)

    @property
    def line_items(self):
        return self.line_item_set.line_items

    def to_initial_conditions(
        self, start_date, end_date, account_set, memo_rule_set, **kwargs
    ):
        from expense_forecast.ExpenseForecastInitialConditions import (
            ExpenseForecastInitialConditions,
        )

        return ExpenseForecastInitialConditions(
            start_date=start_date,
            end_date=end_date,
            account_set=copy.deepcopy(account_set),
            line_item_set=copy.deepcopy(self.line_item_set),
            memo_rule_set=copy.deepcopy(memo_rule_set),
            policy_program=copy.deepcopy(self.policy_program),
            **kwargs,
        )

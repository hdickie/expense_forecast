"""
Summary
-------

Description
-----------

Contract
--------

@interface-report: show
"""


#ScenarioSpace.py
from expense_forecast.MemoRuleSet import MemoRuleSet
from expense_forecast.ScenarioDimension import ScenarioDimension
from expense_forecast.LineItemSet import LineItemSet
import pandas as pd

#TODO manual review of ScenarioSpace docstring
class ScenarioSpace:

    """
    Summary
    -------

    Description
    -----------

    Contract
    --------

    @interface-report: show
    """
    #TODO manual review of ScenarioSpace._validate_memo_rule_set_and_scenario_dimensions_are_compatible docstring
    def _validate_memo_rule_set_and_scenario_dimensions_are_compatible(self,
                                                                        invariant_transactions:LineItemSet,
                                                                        scenario_dimensions: dict[str, ScenarioDimension],
                                                                        memo_rule_set: MemoRuleSet
                                                                  ):

        """
        TODO one-line description of ScenarioSpace._validate_memo_rule_set_and_scenario_dimensions_are_compatible.

        TODO multi-line description of ScenarioSpace._validate_memo_rule_set_and_scenario_dimensions_are_compatible.
        TODO explain how ScenarioSpace._validate_memo_rule_set_and_scenario_dimensions_are_compatible participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        invariant_transactions : object
            TODO one-line description of ScenarioSpace._validate_memo_rule_set_and_scenario_dimensions_are_compatible.invariant_transactions.

        scenario_dimensions : object
            TODO one-line description of ScenarioSpace._validate_memo_rule_set_and_scenario_dimensions_are_compatible.scenario_dimensions.

        memo_rule_set : object
            TODO one-line description of ScenarioSpace._validate_memo_rule_set_and_scenario_dimensions_are_compatible.memo_rule_set.

        Returns
        -------
        None
            TODO one-line description of return value of ScenarioSpace._validate_memo_rule_set_and_scenario_dimensions_are_compatible.

        Contract
        --------
        - #TODO contract lines for ScenarioSpace._validate_memo_rule_set_and_scenario_dimensions_are_compatible.
        - #TODO document exceptions, mutations, and precision assumptions for ScenarioSpace._validate_memo_rule_set_and_scenario_dimensions_are_compatible.

        @interface-report: show
        """
        raise NotImplementedError

    #TODO manual review of ScenarioSpace.addDimension docstring
    def addDimension(self, dimension_name, scenario_dimension: ScenarioDimension):
        """
        TODO one-line description of ScenarioSpace.addDimension.

        TODO multi-line description of ScenarioSpace.addDimension.
        TODO explain how ScenarioSpace.addDimension participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        dimension_name : object
            TODO one-line description of ScenarioSpace.addDimension.dimension_name.

        scenario_dimension : object
            TODO one-line description of ScenarioSpace.addDimension.scenario_dimension.

        Returns
        -------
        object
            TODO one-line description of return value of ScenarioSpace.addDimension.

        Contract
        --------
        - #TODO contract lines for ScenarioSpace.addDimension.
        - #TODO document exceptions, mutations, and precision assumptions for ScenarioSpace.addDimension.

        @interface-report: show
        """
        partial_scenario_to_delete_afterward_keys = []

        # I'm not actually sure I need this but it seems like a good thing to have
        self.scenario_dimensions[dimension_name] = scenario_dimension


        for existing_scenario_name, existing_scenario_budget_set in self.scenarios.items():
            for choice_name, choice_budget_set in scenario_dimension.choices.items():

                if self.dimension_count > 0:
                    new_scenario_name = existing_scenario_name+" | "+choice_name
                else:
                    new_scenario_name = choice_name

                new_scenario = existing_scenario_budget_set.union(choice_budget_set)
                self.scenarios[new_scenario_name] = new_scenario
                partial_scenario_to_delete_afterward_keys.append(existing_scenario_name)
        for key in partial_scenario_to_delete_afterward_keys:
            self.scenarios.pop(key)

        self.dimension_indices[dimension_name] = self.dimension_count
        self.dimension_names.append(dimension_name)
        self.dimension_count += 1

    # TODO I will need some version of these eventually
    # def dropScenarioByLabel(self, scenario_label):
    #     pass

    # def dropScenario(self, scenario_name, choice_name):
    #     pass

    # def dropScenarios(self, dimension_choice_list_map: dict[str,list[str]]):
    #     # not required to include all dimensions
    #     pass




    # TODO I think I want to move away from data frame operations?
    #TODO manual review of ScenarioSpace.getScenariosDF docstring
    def getScenariosDF(self):
        """
        TODO one-line description of ScenarioSpace.getScenariosDF.

        TODO multi-line description of ScenarioSpace.getScenariosDF.
        TODO explain how ScenarioSpace.getScenariosDF participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that ScenarioSpace.getScenariosDF takes no parameters beyond self/cls.

        Returns
        -------
        object
            TODO one-line description of return value of ScenarioSpace.getScenariosDF.

        Contract
        --------
        - #TODO contract lines for ScenarioSpace.getScenariosDF.
        - #TODO document exceptions, mutations, and precision assumptions for ScenarioSpace.getScenariosDF.

        @interface-report: show
        """
        scenarios_df = pd.DataFrame()
        for dimension_name in self.dimension_names:
            scenarios_df[dimension_name] = ""

        scenario_index = 0
        for choice_list_str in self.scenarios.keys():
            choices = [ choice.strip() for choice in choice_list_str.split('|') ]

            choice_index = 0
            for choice_value in choices:
                scenarios_df.iloc[scenario_index, choice_index] = choice_value
                choice_index += 1

            scenario_index += 1

        return scenarios_df

    #TODO a methos to add exceptions- like, only keep these combinations of labels or drop this specific one

    #TODO manual review of ScenarioSpace.__init__ docstring
    def __init__(self,
                 invariant_transactions: LineItemSet,
                 scenario_dimensions: dict[str, ScenarioDimension],
                 memo_rule_set: MemoRuleSet):

        """
        TODO one-line description of ScenarioSpace.__init__.

        TODO multi-line description of ScenarioSpace.__init__.
        TODO explain how ScenarioSpace.__init__ participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        invariant_transactions : object
            TODO one-line description of ScenarioSpace.__init__.invariant_transactions.

        scenario_dimensions : object
            TODO one-line description of ScenarioSpace.__init__.scenario_dimensions.

        memo_rule_set : object
            TODO one-line description of ScenarioSpace.__init__.memo_rule_set.

        Returns
        -------
        None
            TODO one-line description of return value of ScenarioSpace.__init__.

        Contract
        --------
        - #TODO contract lines for ScenarioSpace.__init__.
        - #TODO document exceptions, mutations, and precision assumptions for ScenarioSpace.__init__.

        @interface-report: show
        """
        self.scenario_dimensions = {}
        self.dimension_indices = {} #input is dict, in choice string we need to know order and have it be stable
        self.dimension_names = [] #inverse of above
        self.scenarios = {} # str -> LineItemSet (concat choice labels -> union budgetset)

        self._validate_memo_rule_set_and_scenario_dimensions_are_compatible(invariant_transactions, scenario_dimensions, memo_rule_set)
        self.invariant_transactions = invariant_transactions
        self.memo_rule_set = memo_rule_set

        self.dimension_count = 0
        self.scenarios[''] = self.invariant_transactions

        for dimension_name, dimension_budget_set in scenario_dimensions.items():
            self.addDimension(dimension_name, dimension_budget_set)






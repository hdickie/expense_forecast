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
from expense_forecast.ForecastPolicySet import ForecastPolicySet
from expense_forecast.Scenario import Scenario
from expense_forecast.ConditionalScenarioTransitionSet import (
    ConditionalScenarioTransitionSet,
)
from expense_forecast.AccountSet import AccountSet
from expense_forecast.ScenarioChoice import (
    overlay_account_sets,
    overlay_memo_rule_sets,
    overlay_policy_sets,
)
import copy
import pandas as pd

#TODO DOC manual review of ScenarioSpace docstring
class ScenarioSpace:

    @staticmethod
    def _merge_policy_sets(*policy_sets):
        result = ForecastPolicySet()
        for policy_set in policy_sets:
            result = overlay_policy_sets(result, policy_set)
        return result

    @staticmethod
    def _merge_transition_sets(*transition_sets):
        transitions = [
            copy.deepcopy(transition)
            for transition_set in transition_sets
            for transition in transition_set.transitions
        ]
        return ConditionalScenarioTransitionSet(*transitions)

    """
    Summary
    -------

    Description
    -----------

    Contract
    --------

    @interface-report: show
    """
    #TODO DOC manual review of ScenarioSpace._validate_memo_rule_set_and_scenario_dimensions_are_compatible docstring
    def _validate_memo_rule_set_and_scenario_dimensions_are_compatible(self,
                                                                        invariant_transactions:LineItemSet,
                                                                        scenario_dimensions: dict[str, ScenarioDimension],
                                                                        memo_rule_set: MemoRuleSet
                                                                  ):

        """
        #TODO DOC one-line description of ScenarioSpace._validate_memo_rule_set_and_scenario_dimensions_are_compatible.

        #TODO DOC multi-line description of ScenarioSpace._validate_memo_rule_set_and_scenario_dimensions_are_compatible.
        #TODO DOC explain how ScenarioSpace._validate_memo_rule_set_and_scenario_dimensions_are_compatible participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        invariant_transactions : object
            #TODO DOC one-line description of ScenarioSpace._validate_memo_rule_set_and_scenario_dimensions_are_compatible.invariant_transactions.

        scenario_dimensions : object
            #TODO DOC one-line description of ScenarioSpace._validate_memo_rule_set_and_scenario_dimensions_are_compatible.scenario_dimensions.

        memo_rule_set : object
            #TODO DOC one-line description of ScenarioSpace._validate_memo_rule_set_and_scenario_dimensions_are_compatible.memo_rule_set.

        Returns
        -------
        None
            #TODO DOC one-line description of return value of ScenarioSpace._validate_memo_rule_set_and_scenario_dimensions_are_compatible.

        Contract
        --------
        - #TODO DOC contract lines for ScenarioSpace._validate_memo_rule_set_and_scenario_dimensions_are_compatible.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ScenarioSpace._validate_memo_rule_set_and_scenario_dimensions_are_compatible.

        @interface-report: show
        """
        if not isinstance(invariant_transactions, LineItemSet):
            raise TypeError("invariant_transactions must be a LineItemSet")
        if not isinstance(memo_rule_set, MemoRuleSet):
            raise TypeError("memo_rule_set must be a MemoRuleSet")
        if not isinstance(scenario_dimensions, dict):
            raise TypeError("scenario_dimensions must be a mapping")
        for dimension_name, dimension in scenario_dimensions.items():
            if not isinstance(dimension, ScenarioDimension):
                raise TypeError(
                    f"Scenario dimension {dimension_name!r} is not a ScenarioDimension"
                )
            if dimension_name != dimension.name:
                raise ValueError(
                    f"Scenario dimension key {dimension_name!r} does not match "
                    f"its name {dimension.name!r}"
                )

    #TODO DOC manual review of ScenarioSpace.addDimension docstring
    def addDimension(self, dimension_name, scenario_dimension: ScenarioDimension):
        """
        #TODO DOC one-line description of ScenarioSpace.addDimension.

        #TODO DOC multi-line description of ScenarioSpace.addDimension.
        #TODO DOC explain how ScenarioSpace.addDimension participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        dimension_name : object
            #TODO DOC one-line description of ScenarioSpace.addDimension.dimension_name.

        scenario_dimension : object
            #TODO DOC one-line description of ScenarioSpace.addDimension.scenario_dimension.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ScenarioSpace.addDimension.

        Contract
        --------
        - #TODO DOC contract lines for ScenarioSpace.addDimension.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ScenarioSpace.addDimension.

        @interface-report: show
        """
        self.scenario_dimensions[dimension_name] = scenario_dimension
        existing_scenarios = list(self.scenarios.items())
        new_scenarios = {}
        for existing_scenario_name, existing_scenario_line_item_set in existing_scenarios:
            for choice_name, choice in scenario_dimension.choices.items():

                if self.dimension_count > 0:
                    new_scenario_name = existing_scenario_name+" | "+choice_name
                else:
                    new_scenario_name = choice_name

                existing_set = (
                    existing_scenario_line_item_set.line_item_set
                    if isinstance(existing_scenario_line_item_set, Scenario)
                    else existing_scenario_line_item_set
                )
                line_item_set = existing_set + scenario_dimension.select(choice_name)
                choices = dict(
                    existing_scenario_line_item_set.choices
                    if isinstance(existing_scenario_line_item_set, Scenario) else {}
                )
                choices[dimension_name] = choice_name
                choice_policy_set = self._merge_policy_sets(
                    existing_scenario_line_item_set.policy_set,
                    choice.policy_set,
                )
                choice_transition_set = self._merge_transition_sets(
                    existing_scenario_line_item_set.transition_set,
                    choice.transition_set,
                )
                choice_account_set = overlay_account_sets(
                    existing_scenario_line_item_set.account_set,
                    choice.account_set,
                )
                choice_memo_rule_set = overlay_memo_rule_sets(
                    existing_scenario_line_item_set.memo_rule_set,
                    choice.memo_rule_set,
                )
                new_scenarios[new_scenario_name] = Scenario(
                    new_scenario_name,
                    choices,
                    line_item_set,
                    (
                        self._policy_set_for_choices(choices)
                        if any(
                            override_choices == choices
                            for override_choices, _ in self.policy_overrides
                        )
                        else choice_policy_set
                    ),
                    choice_transition_set,
                    choice_account_set,
                    choice_memo_rule_set,
                )
        self.scenarios = new_scenarios

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
    #TODO DOC manual review of ScenarioSpace.getScenariosDF docstring
    def getScenariosDF(self):
        """
        #TODO DOC one-line description of ScenarioSpace.getScenariosDF.

        #TODO DOC multi-line description of ScenarioSpace.getScenariosDF.
        #TODO DOC explain how ScenarioSpace.getScenariosDF participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ScenarioSpace.getScenariosDF takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ScenarioSpace.getScenariosDF.

        Contract
        --------
        - #TODO DOC contract lines for ScenarioSpace.getScenariosDF.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ScenarioSpace.getScenariosDF.

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

    #TODO DOC manual review of ScenarioSpace.__init__ docstring
    def __init__(self,
                 invariant_transactions: LineItemSet,
                 scenario_dimensions: dict[str, ScenarioDimension],
                 memo_rule_set: MemoRuleSet,
                 default_policy_set: ForecastPolicySet = None,
                 policy_overrides=None):

        """
        #TODO DOC one-line description of ScenarioSpace.__init__.

        #TODO DOC multi-line description of ScenarioSpace.__init__.
        #TODO DOC explain how ScenarioSpace.__init__ participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        invariant_transactions : object
            #TODO DOC one-line description of ScenarioSpace.__init__.invariant_transactions.

        scenario_dimensions : object
            #TODO DOC one-line description of ScenarioSpace.__init__.scenario_dimensions.

        memo_rule_set : object
            #TODO DOC one-line description of ScenarioSpace.__init__.memo_rule_set.

        Returns
        -------
        None
            #TODO DOC one-line description of return value of ScenarioSpace.__init__.

        Contract
        --------
        - #TODO DOC contract lines for ScenarioSpace.__init__.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ScenarioSpace.__init__.

        @interface-report: show
        """
        self.scenario_dimensions = {}
        self.dimension_indices = {} #input is dict, in choice string we need to know order and have it be stable
        self.dimension_names = [] #inverse of above
        self.scenarios = {} # str -> LineItemSet (concat choice labels -> union budgetset)
        self.default_policy_set = copy.deepcopy(
            default_policy_set or ForecastPolicySet()
        )
        if not isinstance(self.default_policy_set, ForecastPolicySet):
            raise TypeError("default_policy_set must be a ForecastPolicySet")
        self.policy_overrides = []
        for choice_map, policy_set in (policy_overrides or []):
            if not isinstance(choice_map, dict):
                raise TypeError("policy override choices must be a mapping")
            if not isinstance(policy_set, ForecastPolicySet):
                raise TypeError("policy override value must be a ForecastPolicySet")
            self.policy_overrides.append((dict(choice_map), copy.deepcopy(policy_set)))

        self._validate_memo_rule_set_and_scenario_dimensions_are_compatible(invariant_transactions, scenario_dimensions, memo_rule_set)
        self.invariant_transactions = invariant_transactions
        self.memo_rule_set = memo_rule_set

        self.dimension_count = 0
        self.scenarios[''] = Scenario(
            '', {}, self.invariant_transactions, self.default_policy_set,
            account_set=AccountSet(),
        )

        for dimension_name, dimension_line_item_set in scenario_dimensions.items():
            self.addDimension(dimension_name, dimension_line_item_set)

    def _policy_set_for_choices(self, choices):
        matching = [
            policy_set for choice_map, policy_set in self.policy_overrides
            if choice_map == choices
        ]
        if len(matching) > 1:
            raise ValueError(f"Duplicate policy override for choices {choices!r}")
        return copy.deepcopy(matching[0] if matching else self.default_policy_set)

    def from_choice_keys(self, choice_keys={}):
        """Build one Scenario from a human-readable dimension/choice mapping.

        The mapping may select any subset of this space's dimensions.  An
        empty mapping therefore represents the invariant transactions alone.
        Unlike ``self.scenarios``, this method does not search the precomputed
        Cartesian product; it composes exactly the choices the caller names.
        """
        if not isinstance(choice_keys, dict):
            raise TypeError("choice_keys must be a mapping")

        unknown_dimensions = [
            name for name in choice_keys if name not in self.scenario_dimensions
        ]
        if unknown_dimensions:
            known = ", ".join(repr(name) for name in self.dimension_names) or "none"
            unknown = ", ".join(repr(name) for name in unknown_dimensions)
            raise ValueError(
                f"Unknown scenario dimension(s): {unknown}. Known dimensions: {known}"
            )

        # Start with a copy so the returned Scenario never shares mutable line
        # item or metadata state with the ScenarioSpace.
        selected_line_items = copy.deepcopy(self.invariant_transactions)
        selected_choices = {}
        selected_policy_sets = [copy.deepcopy(self.default_policy_set)]
        selected_transition_sets = []
        selected_account_set = AccountSet()
        selected_memo_rule_set = MemoRuleSet()
        label_parts = []

        # Space declaration order makes labels stable even when the caller's
        # dictionary was constructed in a different order.
        for dimension_name in self.dimension_names:
            if dimension_name not in choice_keys:
                continue
            choice_name = choice_keys[dimension_name]
            dimension = self.scenario_dimensions[dimension_name]
            if choice_name not in dimension.choices:
                known = ", ".join(repr(name) for name in dimension.choices)
                raise ValueError(
                    f"Unknown choice {choice_name!r} for ScenarioDimension "
                    f"{dimension_name!r}. Known choices: {known}"
                )

            selected_line_items = selected_line_items + dimension.select(choice_name)
            selected_policy_sets.append(
                copy.deepcopy(dimension.choices[choice_name].policy_set)
            )
            selected_transition_sets.append(
                copy.deepcopy(dimension.choices[choice_name].transition_set)
            )
            selected_account_set = overlay_account_sets(
                selected_account_set,
                dimension.choices[choice_name].account_set,
            )
            selected_memo_rule_set = overlay_memo_rule_sets(
                selected_memo_rule_set,
                dimension.choices[choice_name].memo_rule_set,
            )
            selected_choices[dimension_name] = choice_name
            label_parts.append(f"{dimension_name}: {choice_name}")

        exact_override = any(
            override_choices == selected_choices
            for override_choices, _ in self.policy_overrides
        )
        return Scenario(
            label=" | ".join(label_parts) if label_parts else "Invariant",
            choices=selected_choices,
            line_item_set=selected_line_items,
            policy_set=(
                self._policy_set_for_choices(selected_choices)
                if exact_override
                else self._merge_policy_sets(*selected_policy_sets)
            ),
            transition_set=self._merge_transition_sets(
                *selected_transition_sets
            ),
            account_set=selected_account_set,
            memo_rule_set=selected_memo_rule_set,
        )

    def materialize_from_keys(self, choice_key_maps):
        """Build an ordered list of scenarios from readable choice mappings.

        This is deliberately a thin plural counterpart to
        :meth:`from_choice_keys`.  Keeping all composition and validation in
        that method ensures a scenario behaves identically whether selected
        alone or as part of a forecast set.
        """
        if isinstance(choice_key_maps, (str, bytes, dict)):
            raise TypeError("choice_key_maps must be an iterable of mappings")

        try:
            choice_key_maps = list(choice_key_maps)
        except TypeError as error:
            raise TypeError(
                "choice_key_maps must be an iterable of mappings"
            ) from error

        return [
            self.from_choice_keys(choice_keys)
            for choice_keys in choice_key_maps
        ]

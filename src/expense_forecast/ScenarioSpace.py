#ScenarioSpace.py
from expense_forecast.MemoRuleSet import MemoRuleSet
from expense_forecast.ScenarioDimension import ScenarioDimension
from expense_forecast.BudgetSet import BudgetSet
import pandas as pd 

class ScenarioSpace:

    def _validate_memo_rule_set_and_scenario_dimensions_are_compatible(self, 
                                                                        invariant_transactions:BudgetSet,
                                                                        scenario_dimensions: dict[str, ScenarioDimension],
                                                                        memo_rule_set: MemoRuleSet
                                                                  ):
        
        raise NotImplementedError

    def addDimension(self, dimension_name, scenario_dimension: ScenarioDimension):
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
        
        



    def getScenariosDF(self):
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

    def __init__(self, 
                 invariant_transactions: BudgetSet,
                 scenario_dimensions: dict[str, ScenarioDimension],
                 memo_rule_set: MemoRuleSet):
        
        self.scenario_dimensions = {}
        self.dimension_indices = {} #input is dict, in choice string we need to know order and have it be stable
        self.dimension_names = [] #inverse of above
        self.scenarios = {} # str -> BudgetSet (concat choice labels -> union budgetset)
        
        self._validate_memo_rule_set_and_scenario_dimensions_are_compatible(invariant_transactions, scenario_dimensions, memo_rule_set)
        self.invariant_transactions = invariant_transactions
        self.memo_rule_set = memo_rule_set

        self.dimension_count = 0
        self.scenarios[''] = self.invariant_transactions

        for dimension_name, dimension_budget_set in scenario_dimensions.items():
            self.addDimension(dimension_name, dimension_budget_set)

        

        
        
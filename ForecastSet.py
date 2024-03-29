import pandas as pd
import re
import copy
import BudgetItem
import BudgetSet
import jsonpickle
import logging
from log_methods import log_in_color
from log_methods import setup_logger
logger = setup_logger('ForecastSet', './log/ForecastSet.log', level=logging.WARNING)

class ForecastSet:

    def __init__(self, core_budget_set, option_budget_set):

        intersection = pd.merge(core_budget_set.getBudgetItems(), option_budget_set.getBudgetItems(), how ='inner')
        if not intersection.empty:
            raise ValueError('overlap detected in Core and Option Budgetsets')

        self.core_budget_set = core_budget_set
        self.option_budget_set = option_budget_set

        self.scenarios = {}

    def initialize_forecast_set_from_json(self,path):
        raise NotImplementedError

    def initialize_forecast_set_from_excel(self,path):
        raise NotImplementedError

    def to_json(self, path):
        raise NotImplementedError

    def to_excel(self, path):
        raise NotImplementedError

    def addScenario(self,name_of_scenario,lists_of_memo_regexes):
        new_option_budget_set = copy.deepcopy(self.core_budget_set)
        for bi in self.option_budget_set.budget_items:
            for memo_regex in lists_of_memo_regexes:
                match_result = re.search(memo_regex,bi.memo)
                try:
                    match_result.group(0)
                    new_option_budget_set = BudgetSet.BudgetSet(new_option_budget_set.budget_items + [bi])
                except:
                    pass

        self.scenarios[name_of_scenario] = new_option_budget_set

    def addChoiceToAllScenarios(self, list_of_choice_names, list_of_lists_of_memo_regexes):
        log_in_color(logger, 'white', 'debug', 'ENTER addChoiceToAllScenarios')
        if len(self.scenarios) == 0:
            self.scenarios['Core'] = self.core_budget_set

        new_list_of_scenarios = {}
        choice_index = 0
        for list_of_memo_regexes in list_of_lists_of_memo_regexes:
            choice_name = list_of_choice_names[choice_index]
            log_in_color(logger, 'white', 'debug', 'choice_index ' + str(choice_index))
            log_in_color(logger, 'white', 'debug', 'choice_name ' + str(choice_name))
            for s_key, s_value in self.scenarios.items():
                log_in_color(logger, 'white', 'debug', 's_key ' + str(s_key))
                new_option_budget_set = copy.deepcopy(s_value)

                new_option_budget_set_list = new_option_budget_set.budget_items
                for bi in self.option_budget_set.budget_items:
                    log_in_color(logger, 'white', 'debug', 'bi ' + str(bi))
                    for memo_regex in list_of_memo_regexes:
                        match_result = re.search(memo_regex, bi.memo)
                        try:
                            match_result.group(0)
                            new_option_budget_set_list.append(bi)
                        except:
                            pass
                new_option_budget_set = BudgetSet.BudgetSet(new_option_budget_set_list)
                new_list_of_scenarios[s_key+' | '+ choice_name] = new_option_budget_set
            choice_index += 1

        self.scenarios = new_list_of_scenarios
        log_in_color(logger, 'white', 'debug', 'EXIT addChoiceToAllScenarios')

    def __str__(self):
        return_string = "------------------------------------------------------------------------------------------------\n"
        return_string += "Core Set:\n"
        return_string += self.core_budget_set.getBudgetItems().to_string() + "\n"
        return_string += "------------------------------------------------------------------------------------------------\n"
        return_string += "Optional Set:\n"
        return_string += self.option_budget_set.getBudgetItems().to_string() + "\n"
        for key, value in self.scenarios.items():
            return_string += "------------------------------------------------------------------------------------------------\n"
            return_string += str(key) + " \n"
            return_string += value.getBudgetItems().to_string() + "\n"


        return return_string

    def to_json(self):
        return jsonpickle.encode(self, indent=4)

    def addCustomLabelToScenario(self, old_label, new_label):
        try:
            self.scenarios[new_label] = self.scenarios[old_label]
            del self.scenarios[old_label]
        except KeyError as e:
            raise ValueError("Scenario label not found")

    # Scenario_Name	Choose_One_Set_Id	Option_Name	Option_Id	Memo_Regex_List
    def getScenarioSetExcelPage(self):
        pass

    #does not load core and option budget sets
    # Scenario_Name	All_Choice_Option_Names	Option_Name	Option_Id	Memo_Regex_List
    def load_scenario_definitions_from_excel(self):
        pass


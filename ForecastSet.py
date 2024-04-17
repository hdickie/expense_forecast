import pandas as pd
import re
import copy
import BudgetItem
import BudgetSet
import jsonpickle
import logging
import json
import ExpenseForecast
from log_methods import log_in_color
from log_methods import setup_logger
import os
#logger = setup_logger('ForecastSet', './log/ForecastSet.log', level=logging.WARNING)
# logger = logging.getLogger(__name__)
import random
import math
thread_id = str(math.floor(random.random() * 1000))
try:
    logger = setup_logger(__name__, os.environ['EF_LOG_DIR'] + __name__ + '_'+ thread_id+'.log', level=logging.INFO)
except KeyError:
    logger = setup_logger(__name__, __name__ + '_'+ thread_id+'.log', level=logging.INFO)

def from_json_string(json_string):
    data = json.loads(json_string)
    #print(data.keys())

    #print(data['py/object']) #ForecastSet.ForecastSet
    # print('--------------------')
    print(data['base_forecast']) #todo this needs to be decoded
    print('--------------------')
    print(data['core_budget_set']) #todo decode
    print('--------------------')
    print(data['option_budget_set']) #todo decode
    print('--------------------')
    print(data['forecast_set_name']) #Test Forecast Name
    print('--------------------')
    print(data['forecast_name_to_budget_item_set__dict']) #todo decode values
    print('--------------------')
    print(data['initialized_forecasts']) #todo decode values
    print('--------------------')
    print(data['id_to_name']) #good as is


def from_json(path_to_json):
    with open(path_to_json) as json_data:
        data = json.load(json_data)

    print(data)
    raise NotImplementedError
    #return S

class ForecastSet:

    def __init__(self, base_forecast, option_budget_set, forecast_set_name=''):
        self.base_forecast = base_forecast

        self.core_budget_set = base_forecast.initial_budget_set
        self.option_budget_set = option_budget_set

        intersection = pd.merge(self.core_budget_set.getBudgetItems(), option_budget_set.getBudgetItems(), how ='inner')
        if not intersection.empty:
            raise ValueError('overlap detected in Core and Option Budgetsets')

        self.option_budget_set = option_budget_set
        self.forecast_set_name = forecast_set_name

        #keys are forecast_name
        self.forecast_name_to_budget_item_set__dict = {}
        self.initialized_forecasts = {}
        self.id_to_name = {}
        self.id_to_name['Core'] = base_forecast.unique_id
        self.initialized_forecasts[base_forecast.unique_id] = base_forecast

    def initialize_forecast_set_from_database(self):
        raise NotImplementedError

    def initialize_forecast_set_from_json(self,path):
        raise NotImplementedError

    def initialize_forecast_set_from_excel(self,path):
        raise NotImplementedError

    def to_excel(self):
        raise NotImplementedError

    def to_json(self):
        if len(self.forecast_name_to_budget_item_set__dict) != self.initialized_forecasts:
            self.initialize_forecasts()
        return jsonpickle.encode(self, indent=4, unpicklable=False)



    # def addScenario(self,name_of_scenario,lists_of_memo_regexes):
    #     new_option_budget_set = copy.deepcopy(self.core_budget_set)
    #     for bi in self.option_budget_set.budget_items:
    #         for memo_regex in lists_of_memo_regexes:
    #             match_result = re.search(memo_regex,bi.memo)
    #             try:
    #                 match_result.group(0)
    #                 new_option_budget_set = BudgetSet.BudgetSet(new_option_budget_set.budget_items + [bi])
    #             except:
    #                 pass
    #
    #     self.scenarios[name_of_scenario] = new_option_budget_set

    def initialize_forecasts(self):
        for forecast_name, budget_set in self.forecast_name_to_budget_item_set__dict.items():
            new_E = ExpenseForecast.ExpenseForecast(account_set=self.base_forecast.initial_account_set,
                                                    budget_set=budget_set,
                                                    memo_rule_set=self.base_forecast.initial_memo_rule_set,
                                                    start_date_YYYYMMDD=self.base_forecast.start_date_YYYYMMDD,
                                                    end_date_YYYYMMDD=self.base_forecast.end_date_YYYYMMDD,
                                                    milestone_set=self.base_forecast.milestone_set,
                                                    forecast_set_name=self.forecast_set_name,
                                                    forecast_name=forecast_name
                                                    )
            self.id_to_name[new_E.unique_id] = forecast_name
            self.initialized_forecasts[new_E.unique_id] = new_E

    def get_id_to_forecast_name_map(self):
        return self.id_to_name

    def get_id_to_forecast_map(self):
        return self.initialized_forecasts

    def get_forecast_name_to_forecast_map(self):
        name_to_forecast_map = {}
        for id, forecast_name in self.id_to_name.items():
            name_to_forecast_map[forecast_name] = self.initialized_forecasts[id]
        return name_to_forecast_map


    def addChoiceToAllForecasts(self, list_of_choice_names, list_of_lists_of_memo_regexes):
        log_in_color(logger, 'white', 'debug', 'ENTER addChoiceToAllScenarios')
        if len(self.forecast_name_to_budget_item_set__dict) == 0:
            self.forecast_name_to_budget_item_set__dict['Core'] = self.core_budget_set

        new_dict_of_scenarios = {}
        choice_index = 0
        for list_of_memo_regexes in list_of_lists_of_memo_regexes:
            choice_name = list_of_choice_names[choice_index]
            log_in_color(logger, 'white', 'debug', 'choice_index ' + str(choice_index))
            log_in_color(logger, 'white', 'debug', 'choice_name ' + str(choice_name))
            for s_key, s_value in self.forecast_name_to_budget_item_set__dict.items():
                log_in_color(logger, 'white', 'debug', 's_key ' + str(s_key))
                new_option_budget_set = copy.deepcopy(s_value)

                new_option_budget_set_list = new_option_budget_set.budget_items
                for bi in self.option_budget_set.budget_items:
                    log_in_color(logger, 'white', 'debug', 'bi ' + str(bi))
                    for memo_regex in list_of_memo_regexes:
                        print((memo_regex, bi.memo))
                        match_result = re.search(memo_regex, bi.memo)
                        try:
                            match_result.group(0)
                            new_option_budget_set_list.append(bi)
                        except:
                            pass
                new_option_budget_set = BudgetSet.BudgetSet(new_option_budget_set_list)
                new_dict_of_scenarios[s_key+' | '+ choice_name] = new_option_budget_set
            choice_index += 1

        self.forecast_name_to_budget_item_set__dict = new_dict_of_scenarios
        log_in_color(logger, 'white', 'debug', 'EXIT addChoiceToAllScenarios')

    def __str__(self):
        return_string = "------------------------------------------------------------------------------------------------\n"
        return_string += "Core Set:\n"
        return_string += self.core_budget_set.getBudgetItems().to_string() + "\n"
        return_string += "------------------------------------------------------------------------------------------------\n"
        return_string += "Optional Set:\n"
        return_string += self.option_budget_set.getBudgetItems().to_string() + "\n"
        for key, value in self.forecast_name_to_budget_item_set__dict.items():
            return_string += "------------------------------------------------------------------------------------------------\n"
            return_string += str(key) + " \n"
            return_string += value.getBudgetItems().to_string() + "\n"


        return return_string

    def renameForecast(self, old_label, new_label):
        try:
            self.forecast_name_to_budget_item_set__dict[new_label] = self.forecast_name_to_budget_item_set__dict[old_label]
            del self.forecast_name_to_budget_item_set__dict[old_label]
        except KeyError as e:
            raise ValueError("Forecast Name not found")



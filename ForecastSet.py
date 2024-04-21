import pandas as pd
import re
import copy
import BudgetItem
import BudgetSet
import jsonpickle
import logging
import json
import ExpenseForecast
import ForecastRunner
from log_methods import log_in_color
from log_methods import setup_logger
import os
#logger = setup_logger('ForecastSet', './log/ForecastSet.log', level=logging.WARNING)
# logger = logging.getLogger(__name__)
import random
import math

import hashlib


thread_id = str(math.floor(random.random() * 1000))
try:
    logger = setup_logger(__name__, os.environ['EF_LOG_DIR'] + __name__ + '_'+ thread_id+'.log', level=logging.INFO)
except KeyError:
    logger = setup_logger(__name__, __name__ + '_'+ thread_id+'.log', level=logging.INFO)


def initialize_from_json_string(json_string):
    data = json.loads(json_string)

    return initialize_from_dict(data)

def initialize_from_dict(data):

    #print(data['py/object']) #ForecastSet.ForecastSet
    #print('--------------------')
    base_forecast = ExpenseForecast.initialize_from_dict(data['base_forecast'])

    #print('--------------------')
    #print(data['core_budget_set'])

    core_budget_set = BudgetSet.BudgetSet([])
    for BudgetItem__dict in data['core_budget_set']['budget_items']:
        #BudgetItem__dict = BudgetItem__dict[0]
        sd_YYYYMMDD = BudgetItem__dict['start_date_YYYYMMDD']
        ed_YYYYMMDD = BudgetItem__dict['end_date_YYYYMMDD']

        core_budget_set.addBudgetItem(start_date_YYYYMMDD=sd_YYYYMMDD,
                 end_date_YYYYMMDD=ed_YYYYMMDD,
                 priority=BudgetItem__dict['priority'],
                 cadence=BudgetItem__dict['cadence'],
                 amount=BudgetItem__dict['amount'],
                 memo=BudgetItem__dict['memo'],
                 deferrable=BudgetItem__dict['deferrable'],
                 partial_payment_allowed=BudgetItem__dict['partial_payment_allowed'])


    #print('--------------------')
    #print(data['option_budget_set'])
    option_budget_set = BudgetSet.BudgetSet([])
    for BudgetItem__dict in data['option_budget_set']['budget_items']:
        # BudgetItem__dict = BudgetItem__dict[0]
        sd_YYYYMMDD = BudgetItem__dict['start_date_YYYYMMDD']
        ed_YYYYMMDD = BudgetItem__dict['end_date_YYYYMMDD']

        option_budget_set.addBudgetItem(start_date_YYYYMMDD=sd_YYYYMMDD,
                                      end_date_YYYYMMDD=ed_YYYYMMDD,
                                      priority=BudgetItem__dict['priority'],
                                      cadence=BudgetItem__dict['cadence'],
                                      amount=BudgetItem__dict['amount'],
                                      memo=BudgetItem__dict['memo'],
                                      deferrable=BudgetItem__dict['deferrable'],
                                      partial_payment_allowed=BudgetItem__dict['partial_payment_allowed'])
    #print('--------------------')
    #print(data['forecast_set_name']) #Test Forecast Name
    forecast_set_name = data['forecast_set_name']
    #print('--------------------')
    #print(data['forecast_name_to_budget_item_set__dict'])
    forecast_name_to_budget_item_set__dict = {}
    for forecast_name, budget_item_set_dict in data['forecast_name_to_budget_item_set__dict'].items():

        #print(forecast_name)
        B = BudgetSet.BudgetSet([])
        for BudgetItem__dict in budget_item_set_dict['budget_items']:
            # BudgetItem__dict = BudgetItem__dict[0]
            sd_YYYYMMDD = BudgetItem__dict['start_date_YYYYMMDD']
            ed_YYYYMMDD = BudgetItem__dict['end_date_YYYYMMDD']

            B.addBudgetItem(start_date_YYYYMMDD=sd_YYYYMMDD,
                                          end_date_YYYYMMDD=ed_YYYYMMDD,
                                          priority=BudgetItem__dict['priority'],
                                          cadence=BudgetItem__dict['cadence'],
                                          amount=BudgetItem__dict['amount'],
                                          memo=BudgetItem__dict['memo'],
                                          deferrable=BudgetItem__dict['deferrable'],
                                          partial_payment_allowed=BudgetItem__dict['partial_payment_allowed'])
        forecast_name_to_budget_item_set__dict[forecast_name] = B

    #print('--------------------')
    #print(data['initialized_forecasts'])
    initialized_forecasts = {}
    for k, v in data['initialized_forecasts'].items():
        #print(v)
        initialized_forecasts[k] = ExpenseForecast.initialize_from_dict(v)

    id_to_name = data['id_to_name']
    # print('--------------------')
    # print(data['id_to_name']) #good as is

    S = ForecastSet(base_forecast,option_budget_set,forecast_set_name)
    S.forecast_name_to_budget_item_set__dict = forecast_name_to_budget_item_set__dict
    S.initialized_forecasts = initialized_forecasts
    S.id_to_name = id_to_name

    return S

def initialize_from_json_file(path_to_json):
    with open(path_to_json) as json_data:
        data = json.load(json_data)

    return initialize_from_dict(data)

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
        self.id_to_name[base_forecast.unique_id] = 'Core'
        self.initialized_forecasts[base_forecast.unique_id] = base_forecast

        self.unique_id = 'S'+base_forecast.unique_id

    def initialize_forecast_set_from_database(self):
        raise NotImplementedError

    def initialize_forecast_set_from_json(self,path):
        raise NotImplementedError

    def initialize_forecast_set_from_excel(self,path):
        raise NotImplementedError

    def to_excel(self):
        raise NotImplementedError

    def to_json(self):
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
        new_id_to_name = {}
        new_initialized_forecasts = {}
        for forecast_name, budget_set in self.forecast_name_to_budget_item_set__dict.items():
            #print('Initializing '+forecast_name)
            new_E = ExpenseForecast.ExpenseForecast(account_set=self.base_forecast.initial_account_set,
                                                    budget_set=budget_set,
                                                    memo_rule_set=self.base_forecast.initial_memo_rule_set,
                                                    start_date_YYYYMMDD=self.base_forecast.start_date_YYYYMMDD,
                                                    end_date_YYYYMMDD=self.base_forecast.end_date_YYYYMMDD,
                                                    milestone_set=self.base_forecast.milestone_set,
                                                    forecast_set_name=self.forecast_set_name,
                                                    forecast_name=forecast_name
                                                    )
            new_id_to_name[new_E.unique_id] = forecast_name
            new_initialized_forecasts[new_E.unique_id] = new_E
        self.id_to_name = new_id_to_name
        self.initialized_forecasts = new_initialized_forecasts
        self.unique_id = 'S' + str(int(hashlib.sha1(str(self.initialized_forecasts.keys()).encode("utf-8")).hexdigest(),16) % 100000).rjust(6, '0')

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
                        #print((memo_regex, bi.memo))
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

        self.initialize_forecasts()
        log_in_color(logger, 'white', 'debug', 'EXIT addChoiceToAllScenarios')

    def __str__(self):
        return_string = "------------------------------------------------------------------------------------------------\n"
        return_string += "Core Set " + self.base_forecast.unique_id + ":\n"
        return_string += self.core_budget_set.getBudgetItems().to_string() + "\n"
        return_string += "------------------------------------------------------------------------------------------------\n"
        return_string += "Optional Set:\n"
        return_string += self.option_budget_set.getBudgetItems().to_string() + "\n"
        for key, value in self.forecast_name_to_budget_item_set__dict.items():
            return_string += "------------------------------------------------------------------------------------------------\n"
            return_string += str(key) + " \n"
            return_string += value.getBudgetItems().to_string() + "\n"
        return_string += "------------------------------------------------------------------------------------------------\n"
        return_string += "Initialized Forecasts:\n"
        return_string += "id     sd       ed       Complete:\n"
        for k, v in self.initialized_forecasts.items():
            completed_flag = v.forecast_df is not None
            return_string += str(k) + " " + v.start_date_YYYYMMDD + " " + v.end_date_YYYYMMDD + " " + str(completed_flag) + " \n"
        return_string += "------------------------------------------------------------------------------------------------\n"


        return return_string

    def renameForecast(self, old_label, new_label):
        try:
            self.forecast_name_to_budget_item_set__dict[new_label] = self.forecast_name_to_budget_item_set__dict[old_label]
            del self.forecast_name_to_budget_item_set__dict[old_label]
        except KeyError as e:
            raise ValueError("Forecast Name not found")

    def update_date_range(self,start_date_YYYYMMDD,end_date_YYYYMMDD):

        #this updates the unique_id of the base_forecast
        self.base_forecast.update_date_range(start_date_YYYYMMDD, end_date_YYYYMMDD)

        #can't call update date range unless the ExpenseForecast already exists
        self.initialize_forecasts()
        new_initialized_forecasts = self.initialized_forecasts.copy()
        for E_key, E in self.initialized_forecasts.copy().items():
            del new_initialized_forecasts[E_key]
            old_id = E.unique_id
            E.update_date_range(start_date_YYYYMMDD,end_date_YYYYMMDD)
            new_id = E.unique_id
            new_initialized_forecasts[new_id] = E
        self.initialized_forecasts = new_initialized_forecasts
        self.unique_id = 'S' + str(int(hashlib.sha1(str(self.initialized_forecasts.keys()).encode("utf-8")).hexdigest(),16) % 100000).rjust(6, '0')

    def writeToJSONFile(self, output_dir='./'):
        log_in_color(logger,'green', 'info', 'Writing to '+str(output_dir)+'ForecastSet_' + self.unique_id + '.json')
        with open(str(output_dir)+'ForecastSet_' + self.unique_id + '.json','w') as f:
            f.write(self.to_json())

    def runAllForecasts(self,log_level='WARNING'):
        # print('runAllForecasts')
        R = ForecastRunner.ForecastRunner(lock_directory='./lock/')
        for unique_id, E in self.initialized_forecasts.items():
            R.start_forecast(E,log_level)
        R.waitAll()
        self.initialized_forecasts = R.forecasts

    def runAllForecastsApproximate(self):
        R = ForecastRunner.ForecastRunner(lock_directory='.')
        for unique_id, E in self.initialized_forecasts.items():
            R.start_forecast_approximate(E)
        R.waitAll()
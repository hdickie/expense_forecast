import copy

import ExpenseForecast, datetime

from log_methods import log_in_color
import BudgetSet

import json

import pandas as pd

from multiprocessing import Pool

class ForecastHandler:

    def __init__(self):
        pass

    def outputHTMLreport(self,E):
        pass
        raise NotImplementedError


    # I think it better to have manual review instead of guessing and checking. this would spend a lot of compute when a human could look and savea lot of time
    # def satisfice(self,AccountSet,BudgetSet, MemoRuleSet, start_date_YYYYMMDD, end_date_YYYYMMDD, InvokeOnErrorMemoRuleSet):
    #
    #     #given the input parameters, run the forecast. if it reaches the end, return the forecast.
    #     #if not, add a budget item to move funds from checking to credit,
    #     # (and in the future) from savings to checking, or from savings to credit
    #     # these new budget items would need to have a corresponding memo rule, so an input memoruleset that is only invoked in case of error is necessary
    #
    #     E = ExpenseForecast.ExpenseForecast(AccountSet,
    #                                         BudgetSet,
    #                                         MemoRuleSet,
    #                                         start_date_YYYYMMDD,
    #                                         end_date_YYYYMMDD)
    #
    #     if max(E.forecast_df.Date) == E.end_date:
    #         return E
    #     else:
    #         # we need to be able to guarantee that the transaction we add will come before the problem day, so we decrement by 1
    #         latest_successfully_simulated_day = max(E.forecast_df.Date) - datetime.timedelta(days=1)
    #
    #         problematic_transaction = E.skipped_df.head(1) #this SHOULD be the transaction that caused the problem
    #         problematic_memo_rule = MemoRuleSet.findMatchingMemoRule(problematic_transaction)
    #
    #         account_that_needs_more_funds = problematic_memo_rule.Account_From
    #
    #         #run the simulation adain with only the transactions that
    #
    #
    #     raise NotImplementedError

    # def calculateImpactOfAddingItemSet(self,AccountSet,Core_BudgetSet, Additional_BudgetSet, MemoRuleSet, start_date_YYYYMMDD, end_date_YYYYMMDD):
    #     raise NotImplementedError

    def getRuntimeEstimate(self,AccountSet,BudgetSet, MemoRuleSet, start_date_YYYYMMDD, end_date_YYYYMMDD):
        log_in_color('green','debug','getRuntimeEstimate(start_date_YYYYMMDD='+str(start_date_YYYYMMDD)+',end_date_YYYYMMDD='+str(end_date_YYYYMMDD)+')')
        log_in_color('green', 'debug', 'Length of forecast:')
        log_in_color('green', 'debug', 'Non-deferrable, partial-payment not allowed:')
        log_in_color('green', 'debug', 'Partial-payment allowed:')
        log_in_color('green', 'debug', 'Deferrable:')
        #number of days * 7.5 seconds
        # for each non-deferrable, partial-payment-not-allowed proposed item, add (end_date - date) * 7.5 seconds
        # for each partial payment allowed item, add [ (end_date - date) * 7.5 seconds, (end_date - date) * 7.5 seconds * 2 ] to get an range time estimate
        # for each deferrable payment, add [ (end_date - date) * 7.5 seconds, ( 1 + FLOOR( (end_date - date) / 14) )^2 / 2 * 7.5 seconds ]

        raise NotImplementedError


    def calculateMultipleChooseOne(self,AccountSet,Core_BudgetSet, MemoRuleSet, start_date_YYYYMMDD, end_date_YYYYMMDD, list_of_lists_of_budget_sets):

        #the number of returned forecasts will be equal to the product of the lengths of the lists in list_of_lists_of_budget_sets
        length_of_lists = [ len(x) for x in list_of_lists_of_budget_sets]
        number_of_returned_forecasts = 1
        for l in length_of_lists:
            number_of_returned_forecasts = number_of_returned_forecasts * l

        #at this point, our return variable is the correct size, and has an empty list for each budget set
        master_list = [Core_BudgetSet.budget_items] #this is a list of lists of budget items
        for list_of_budget_sets in list_of_lists_of_budget_sets:
            current_list = []

            for budget_set in list_of_budget_sets:
                for master_budget_item_list in master_list:
                    current_list.append(budget_set.budget_items + master_budget_item_list)

            master_list = current_list

        program_start = datetime.datetime.now()
        scenario_index = 0
        for budget_set in master_list:
            loop_start = datetime.datetime.now()
            B = BudgetSet.BudgetSet(budget_set)
            # print('B:')
            # print(B.getBudgetItems().to_string())
            print('Starting simulation scenario '+str(scenario_index))
            try:
                E = ExpenseForecast.ExpenseForecast(account_set=copy.deepcopy(AccountSet),
                                                        budget_set=B,
                                                        memo_rule_set=MemoRuleSet,
                                                        start_date_YYYYMMDD=start_date_YYYYMMDD,
                                                        end_date_YYYYMMDD=end_date_YYYYMMDD)
            except:
                print('Simulation scenario '+str(scenario_index)+' failed')

            loop_finish = datetime.datetime.now()

            loop_delta = loop_finish - loop_start
            time_since_started = loop_finish - program_start

            average_time_per_loop = time_since_started.seconds / (scenario_index + 1)
            loops_remaining = number_of_returned_forecasts - (scenario_index + 1)
            ETC = loop_finish + datetime.timedelta(seconds=average_time_per_loop*loops_remaining)
            progress_string = 'Finished in '+str(loop_delta.seconds)+' seconds. ETC: '+str(ETC.strftime('%Y-%m-%d %H:%M:%S'))

            print(progress_string)

            scenario_index += 1


    def json_file_to_ExpenseForecast(self,path_to_json):

        with open(path_to_json) as json_data:
            data = json.load(json_data)


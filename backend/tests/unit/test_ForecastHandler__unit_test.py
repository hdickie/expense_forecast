# import pytest
# import AccountSet
# import AccountMilestone
# import CompositeMilestone
# import ExpenseForecast
# import ForecastHandler, AccountSet, BudgetSet, MemoRuleSet
# import pandas as pd, numpy as np
# import datetime, logging
# import ForecastSet
# import MemoMilestone
# import MilestoneSet
#
# pd.options.mode.chained_assignment = None #apparently this warning can throw false positives???
#
# from log_methods import log_in_color
# from log_methods import setup_logger
# logger = setup_logger('test_ForecastHandler', './log/test_ForecastHandler.log', level=logging.DEBUG)
#
# import copy
#
# class TestForecastHandlerMethods:
#
#     def test_ForecastHandler_Constructor(self):
#         F = ForecastHandler.ForecastHandler()
#
#     def test_run_forecast_set(self):
#
#         start_date_YYYYMMDD = '20240101'
#         end_date_YYYYMMDD = '20240105'
#
#         A = AccountSet.AccountSet([])
#         A.createAccount('Checking',10_000,0,99999,'checking')
#
#         core_budget_set = BudgetSet.BudgetSet([])
#         option_budget_set = BudgetSet.BudgetSet([])
#
#         core_budget_set.addBudgetItem(start_date_YYYYMMDD,end_date_YYYYMMDD,1,'daily',11,'food',False,False)
#         option_budget_set.addBudgetItem(start_date_YYYYMMDD,end_date_YYYYMMDD,1,'daily',10,'txn 1A',False,False)
#         option_budget_set.addBudgetItem(start_date_YYYYMMDD, end_date_YYYYMMDD, 1, 'daily', 20, 'txn 1B', False, False)
#         option_budget_set.addBudgetItem(start_date_YYYYMMDD, end_date_YYYYMMDD, 1, 'daily', 50, 'txn 1C', False, False)
#         option_budget_set.addBudgetItem(start_date_YYYYMMDD, end_date_YYYYMMDD, 1, 'daily', 100, 'txn 2A', False, False)
#         option_budget_set.addBudgetItem(start_date_YYYYMMDD, end_date_YYYYMMDD, 1, 'daily', 200, 'txn 2B', False, False)
#         option_budget_set.addBudgetItem(start_date_YYYYMMDD, end_date_YYYYMMDD, 1, 'daily', 500, 'txn 2C', False, False)
#
#         M = MemoRuleSet.MemoRuleSet([])
#         M.addMemoRule('.*','Checking',None,1)
#
#
#         MS = MilestoneSet.MilestoneSet([AccountMilestone.AccountMilestone('Checking below 9500','Checking',0,9500),
#                                         AccountMilestone.AccountMilestone('Checking below 8000', 'Checking', 0, 8000)
#                                         ],[],[])
#
#         S = ForecastSet.ForecastSet(core_budget_set, option_budget_set)
#
#         scenario_A = ['.*A.*']
#         scenario_B = ['.*B.*']
#         scenario_C = ['.*C.*']
#         scenario_D = ['.*D.*']
#         S.addChoiceToAllScenarios(['A', 'B'], [scenario_A, scenario_B])
#         S.addChoiceToAllScenarios(['C', 'D'], [scenario_C, scenario_D])
#
#         F = ForecastHandler.ForecastHandler()
#
#         #EF() :: account_set, budget_set, memo_rule_set, start_date_YYYYMMDD, end_date_YYYYMMDD,milestone_set,
#
#         E__dict = F.initialize_forecasts_with_scenario_set(A, S, M, start_date_YYYYMMDD,end_date_YYYYMMDD, MS)
#
#
#         for key, value in E__dict.items():
#             value.runForecast()
#             value.appendSummaryLines()
#             value.writeToJSONFile('./')
#             F.generateHTMLReport(value)
#
#
#         F.generateScenarioSetHTMLReport(E__dict)
#
#         raise NotImplementedError
#
#

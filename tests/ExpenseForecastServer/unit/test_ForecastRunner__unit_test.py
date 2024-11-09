# import pytest
# import subprocess
# import ForecastRunner
# import AccountSet
# import BudgetSet
# import MemoRuleSet
# import MilestoneSet
# import ExpenseForecast
# import ForecastHandler
# import os
# import concurrent.futures
# import datetime
# from time import sleep
#
# class TestForecastRunnerMethods:
#
#
#     @pytest.mark.parametrize('param1,param2',
#                              [('param1','param2'),
#                               ])
#     def test_start_forecast(self, param1,param2):
#         start_date = datetime.datetime.now().strftime('%Y%m%d')
#         end_date = '20240430'
#         start_date2 = datetime.datetime.now().strftime('%Y%m%d')
#         end_date2 = '20240501'
#         start_date3 = datetime.datetime.now().strftime('%Y%m%d')
#         end_date3 = '20240502'
#         start_date4 = datetime.datetime.now().strftime('%Y%m%d')
#         end_date4 = '20240503'
#         start_date5 = datetime.datetime.now().strftime('%Y%m%d')
#         end_date5 = '20240504'
#
#         A = AccountSet.AccountSet([])
#         B = BudgetSet.BudgetSet([])
#         M = MemoRuleSet.MemoRuleSet([])
#
#         A.createCheckingAccount('Checking', 5000, 0, 99999)
#         B.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'food', False, False)
#         M.addMemoRule('.*', 'Checking', 'None', 1)
#
#         MS = MilestoneSet.MilestoneSet([], [], [])
#         E1 = ExpenseForecast.ExpenseForecast(A, B, M, start_date, end_date, MS)
#         E2 = ExpenseForecast.ExpenseForecast(A, B, M, start_date2, end_date2, MS)
#         E3 = ExpenseForecast.ExpenseForecast(A, B, M, start_date3, end_date3, MS)
#         E4 = ExpenseForecast.ExpenseForecast(A, B, M, start_date4, end_date4, MS)
#         E5 = ExpenseForecast.ExpenseForecast(A, B, M, start_date5, end_date5, MS)
#
#         R = ForecastRunner.ForecastRunner('/Users/hume/Github/expense_forecast/lock/')
#         R.start_forecast(E1)
#         R.start_forecast(E2)
#         R.start_forecast(E3)
#         R.start_forecast(E4)
#         R.start_forecast(E5)
#
#         R.ps()
#         sleep(5)
#         R.cancel('049833')
#         R.ps()

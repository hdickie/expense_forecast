import ExpenseForecast
import ForecastHandler
import BudgetSet
import AccountSet
import MemoRuleSet
import MilestoneSet
import ForecastSet
import AccountMilestone
import pandas as pd
import concurrent.futures
from time import sleep
import ForecastRunner
import datetime
pd.options.mode.chained_assignment = None #apparently this warning can throw false positives???

def task(n_seconds):
    sleep(n_seconds)
    return 'Done!'

import subprocess

if __name__ == '__main__':
    cmd = "python -m ef_cli parameterize forecastset --filename S.json --start_date 20000301 --end_date 20001231 --username hume"
    cmd_arg_list = cmd.split(" ")
    completed_process = subprocess.run(cmd_arg_list, capture_output=True, check=True)


    og_S = ForecastSet.initialize_from_json_file('./S.json')
    print(og_S.unique_id)
    print('------------------------------------------')
    for unique_id, E in og_S.initialized_forecasts.items():
        print(E.start_date_YYYYMMDD,E.end_date_YYYYMMDD)

    og_S.update_date_range('20000301', '20001231')

    print('------------------------------------------')
    for unique_id, E in og_S.initialized_forecasts.items():
        print(E.start_date_YYYYMMDD, E.end_date_YYYYMMDD)
    print(og_S.unique_id)

    og_S.writeToJSONFile(('./out/'))

    # print('------------------------------------------')
    # S = ForecastSet.initialize_from_json_file('./out/ForecastSet_S087228.json')
    # S.update_date_range('20000301','20001231')

    # for unique_id, E in S.initialized_forecasts.items():
    #     assert E.start_date_YYYYMMDD == '20000301'
    #     assert E.end_date_YYYYMMDD == '20001231'
    # print('------------------------------------------')

    # start_date = datetime.datetime.now().strftime('%Y%m%d')
    # end_date = '20240430'
    #
    # A = AccountSet.AccountSet([])
    # B1 = BudgetSet.BudgetSet([])
    # # B2 = BudgetSet.BudgetSet([])
    # # B3 = BudgetSet.BudgetSet([])
    # # B4 = BudgetSet.BudgetSet([])
    # # B5 = BudgetSet.BudgetSet([])
    # M = MemoRuleSet.MemoRuleSet([])
    #
    # B_optional = BudgetSet.BudgetSet([])
    # B_optional.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'Choice 1 Option A',False,False)
    # B_optional.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'Choice 1 Option B',False,False)
    # B_optional.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'Choice 2 Option C',False,False)
    # B_optional.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'Choice 2 Option D',False,False)
    #
    # A.createCheckingAccount('Checking', 5000, 0, 99999)
    # B1.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'food 1', False, False)
    # # B2.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'food 2', False, False)
    # # B3.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'food 3', False, False)
    # # B4.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'food 4', False, False)
    # # B5.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'food 5', False, False)
    # M.addMemoRule('.*', 'Checking', 'None', 1)
    #
    # MS = MilestoneSet.MilestoneSet([], [], [])
    # E1 = ExpenseForecast.ExpenseForecast(A, B1, M, start_date, end_date, MS)
    #
    # S = ForecastSet.ForecastSet(E1,B_optional,forecast_set_name='Test Forecast Name')
    # S.addChoiceToAllForecasts(['Option A','Option B'],[['.*Option A.*'],['.*Option B.*']])
    # S.addChoiceToAllForecasts(['Option C', 'Option D'], [['.*Option C.*'], ['.*Option D.*']])
    #
    # json_string = S.to_json()
    # S2 = ForecastSet.from_json_string(json_string)

    #print(S2)

    # E2 = ExpenseForecast.ExpenseForecast(A, B2, M, start_date, end_date, MS)
    # E3 = ExpenseForecast.ExpenseForecast(A, B3, M, start_date, end_date, MS)
    # E4 = ExpenseForecast.ExpenseForecast(A, B4, M, start_date, end_date, MS)
    # E5 = ExpenseForecast.ExpenseForecast(A, B5, M, start_date, end_date, MS)

    # E1.writeToJSONFile('./out/') #031987
    # E2.writeToJSONFile('./out/') #093122
    # E3.writeToJSONFile('./out/') #051928
    # E4.writeToJSONFile('./out/') #064210
    # E5.writeToJSONFile('./out/') #052438

    # print(E1.unique_id)
    # print(E2.unique_id)
    # print(E3.unique_id)
    # print(E4.unique_id)
    # print(E5.unique_id)
    # start_date = datetime.datetime.now().strftime('%Y%m%d')
    # end_date = '20240430'
    # start_date2 = datetime.datetime.now().strftime('%Y%m%d')
    # end_date2 = '20240501'
    # start_date3 = datetime.datetime.now().strftime('%Y%m%d')
    # end_date3 = '20240502'
    # start_date4 = datetime.datetime.now().strftime('%Y%m%d')
    # end_date4 = '20240503'
    # start_date5 = datetime.datetime.now().strftime('%Y%m%d')
    # end_date5 = '20240504'
    #
    # A = AccountSet.AccountSet([])
    # B = BudgetSet.BudgetSet([])
    # M = MemoRuleSet.MemoRuleSet([])
    #
    # A.createCheckingAccount('Checking', 5000, 0, 99999)
    # B.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'food', False, False)
    # M.addMemoRule('.*', 'Checking', 'None', 1)
    #
    # MS = MilestoneSet.MilestoneSet([], [], [])
    # E1 = ExpenseForecast.ExpenseForecast(A, B, M, start_date, end_date, MS)
    # E2 = ExpenseForecast.ExpenseForecast(A, B, M, start_date2, end_date2, MS)
    # E3 = ExpenseForecast.ExpenseForecast(A, B, M, start_date3, end_date3, MS)
    # E4 = ExpenseForecast.ExpenseForecast(A, B, M, start_date4, end_date4, MS)
    # E5 = ExpenseForecast.ExpenseForecast(A, B, M, start_date5, end_date5, MS)
    #
    # print(E1.unique_id)
    # print(E2.unique_id)
    # print(E3.unique_id)
    # print(E4.unique_id)
    # print(E5.unique_id)
    #
    # R = ForecastRunner.ForecastRunner('/Users/hume/Github/expense_forecast/lock/')
    # R.start_forecast(E1)
    # R.start_forecast(E2)
    # R.start_forecast(E3)
    # R.start_forecast(E4)
    # R.start_forecast(E5)
    #
    # # R.print_results_as_they_come()
    #
    # R.ps()
    # sleep(11)
    # R.cancel('049833')
    # R.ps()
    # sleep(11)
    # R.ps()
    # sleep(11)
    # R.ps()
    # sleep(11)
    # R.ps()





    # executor = concurrent.futures.ProcessPoolExecutor()
    #
    # futures = {}
    # for i in range(1,11):
    #     keys = (5*i)
    #     futures[keys] = executor.submit(task,keys)
    #
    # for i in range(0,60):
    #     for k, v in futures.items():
    #         print(str(k)+' '+str(v.done()))
    #     print('--------------')
    #     sleep(1)


    # Future class methods
    # future.cancel()
    # future.cancelled()
    # future.running()
    # future.done()
    # future.exception() ?
    # future.add_done_callback()

    # concurrent.futures module methods
    # concurrent.futures.wait(fs) return_when=['FIRST_COMPLETED','FIRST_EXCEPTION','ALL_COMPLETED']
    # concurrent.futures.as_completed(fs)



    #print(future.result())
    #executor.shutdown()


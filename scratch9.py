import ExpenseForecast
# import ForecastHandler
import BudgetSet
import AccountSet
import MemoRuleSet
import MilestoneSet
# import ForecastSet
# import AccountMilestone
import pandas as pd
# import concurrent.futures
# from time import sleep
# import ForecastRunner
# import datetime

pd.options.mode.chained_assignment = None #apparently this warning can throw false positives???


# import subprocess
# import pebble

# def task(n_seconds):
#     sleep(n_seconds)
#     return 'Done!'

# from generate_date_sequence import generate_date_sequence

if __name__ == '__main__':
    start_date_YYYYMMDD = '20240522'
    end_date_YYYYMMDD = '20250101' #we want 9/1

    A = AccountSet.AccountSet([])
    A.createCheckingAccount('Checking', 1000, 0, 999999999, True)
    A.createCreditCardAccount('Credit', 0, 7500, 0, 25000, '20240107', 0.2899, 40)

    B = BudgetSet.BudgetSet([])
    B.addBudgetItem(start_date_YYYYMMDD, '22001231', 1, 'daily', 40, 'food', deferrable=False,
                    partial_payment_allowed=False)
    B.addBudgetItem('20240505', '22001231', 2, 'monthly', 7000, 'pay cc', deferrable=False,
                    partial_payment_allowed=True)
    B.addBudgetItem('20240105', '22001231', 1, 'semiweekly', 1600, 'EMT income', deferrable=False,
                    partial_payment_allowed=False)
    B.addBudgetItem('20240531', '20240628', 1, 'semiweekly', 600, 'repay mom', deferrable=False,
                    partial_payment_allowed=False)
    B.addBudgetItem('20240701', '20260401', 1, 'monthly', 800, 'repay dad', deferrable=False,
                    partial_payment_allowed=False)
    # B.addBudgetItem('20240103', '20240303', 2, 'monthly', 460, 'pay cc', False, False)

    M = MemoRuleSet.MemoRuleSet([])
    M.addMemoRule('food', 'Credit', 'None', 1)
    M.addMemoRule('pay cc', 'Checking', 'Credit', 2)
    M.addMemoRule('.*income.*', 'None', 'Checking', 1)
    M.addMemoRule('.*repay.*', 'Checking', 'None', 1)

    MS = MilestoneSet.MilestoneSet([], [], [])

    E = ExpenseForecast.ExpenseForecast(A, B, M, start_date_YYYYMMDD, end_date_YYYYMMDD, MS)



    E.runForecastApproximate(log_level='DEBUG')
    E.forecast_df.to_csv('test_IRL_case_2__short.csv')
    # print(E.initial_account_set.getAccounts().to_string())
    # print('-----------------')
    print(E)

#
#     # sw1_sd = '20240501'
#     # sw2_sd = '20240502'
#     # sw3_sd = '20240503'
#     # sw4_sd = '20240504'
#     # sw5_sd = '20240505'
#     # sw6_sd = '20240506'
#     # sw7_sd = '20240507'
#     # sw8_sd = '20240508'
#     # sw9_sd = '20240509'
#     # sw10_sd = '20240510'
#     # sw11_sd = '20240511'
#     # sw12_sd = '20240512'
#     # sw13_sd = '20240513'
#     # sw14_sd = '20240514'
#     #
#     # sw1 = generate_date_sequence(sw1_sd,15,'semiweekly')
#     # sw2 = generate_date_sequence(sw2_sd,15,'semiweekly')
#     # sw3 = generate_date_sequence(sw3_sd,15,'semiweekly')
#     # sw4 = generate_date_sequence(sw4_sd,15,'semiweekly')
#     # sw5 = generate_date_sequence(sw5_sd,15,'semiweekly')
#     # sw6 = generate_date_sequence(sw6_sd,15,'semiweekly')
#     # sw7 = generate_date_sequence(sw7_sd,15,'semiweekly')
#     # sw8 = generate_date_sequence(sw8_sd,15,'semiweekly')
#     # sw9 = generate_date_sequence(sw9_sd,15,'semiweekly')
#     # sw10 = generate_date_sequence(sw10_sd,15,'semiweekly')
#     # sw11 = generate_date_sequence(sw11_sd,15,'semiweekly')
#     # sw12 = generate_date_sequence(sw12_sd,15,'semiweekly')
#     # sw13 = generate_date_sequence(sw13_sd,15,'semiweekly')
#     # sw14 = generate_date_sequence(sw14_sd,15,'semiweekly')
#     #
#     # print('sw1:'+sw1_sd+' '+str(sw1))
#     # print('sw2:'+sw2_sd+' '+str(sw2))
#     # print('sw3:'+sw3_sd+' '+str(sw3))
#     # print('sw4:'+sw4_sd+' '+str(sw4))
#     # print('sw5:'+sw5_sd+' '+str(sw5))
#     # print('sw6:'+sw6_sd+' '+str(sw6))
#     # print('sw7:'+sw7_sd+' '+str(sw7))
#     # print('sw8:'+sw8_sd+' '+str(sw8))
#     # print('sw9:'+sw9_sd+' '+str(sw9))
#     # print('sw10:'+sw10_sd+' '+str(sw10))
#     # print('sw11:'+sw11_sd+' '+str(sw11))
#     # print('sw12:'+sw12_sd+' '+str(sw12))
#     # print('sw13:'+sw13_sd+' '+str(sw13))
#     # print('sw14:'+sw14_sd+' '+str(sw14))
#     #
#     # assert sw1 == ['20240501','20240515']
#     # assert sw2 == ['20240502','20240516']
#     # assert sw3 == ['20240503','20240517']
#     # assert sw4 == ['20240504','20240518']
#     # assert sw5 == ['20240505','20240519']
#     # assert sw6 == ['20240506','20240520']
#     # assert sw7 == ['20240507','20240521']
#     # assert sw8 == ['20240508','20240522']
#     # assert sw9 == ['20240509','20240523']
#     # assert sw10 == ['20240510','20240524']
#     # assert sw11 == ['20240511','20240525']
#     # assert sw12 == ['20240512','20240526']
#     # assert sw13 == ['20240513','20240527']
#     # assert sw14 == ['20240514','20240528']
#
#     # S = ForecastSet.initialize_from_json_file('ForecastSet_S084000.json')  # let this throw an exception if needed
#     # S.initialize_forecasts()
#     #
#     # R = ForecastRunner.ForecastRunner(lock_directory='.')
#     # for unique_id, E in S.initialized_forecasts.items():
#     #     R.start_forecast(E)
#     # R.waitAll()
#     #
#     # # S.runAllForecasts()
#     # # S.writeToJSONFile()
#     # F = ForecastHandler.ForecastHandler()
#     # for unique_id, E in S.initialized_forecasts.items():
#     #     print(unique_id)
#     #     F.generateHTMLReport(E)
#
#     # income_start_date = '20240503'
#     # begin_repay_cc_date = '20240601'
#     # end_repay_cc_date = '20250601'
#
#     start_date_YYYYMMDD = '20240101'
#     #end_date_YYYYMMDD = '20240606' #07 does not have "more cc payment", but 06 does
#     end_date_YYYYMMDD = '20240205'  # 07 does not have "more cc payment", but 06 does
#     #maybe should have been 2200 failed -> 921 success
#
#     A = AccountSet.AccountSet([])
#     A.createCheckingAccount('Checking', 1000, 0, 9999999, True)
#     A.createCreditCardAccount('Credit',500,1000,0,25000,'20240104',0.1,40)
#     #A.createLoanAccount('Approximate Loan',15858.49,0,0,25000,'20241203',0.0476,250)
#
#
#     # print(A.getAccounts().to_string())
#     #                                   Name   Balance  Min_Balance  Max_Balance       Account_Type Billing_Start_Date Interest_Type     APR Interest_Cadence Minimum_Payment  Primary_Checking_Ind
#     # 0                             Checking    500.00          0.0    9999999.0           checking               None          None    None             None            None                  True
#     # 1                Credit: Curr Stmt Bal      0.00          0.0      25000.0      curr stmt bal               None          None    None             None            None                 False
#     # 2                Credit: Prev Stmt Bal   9000.00          0.0      25000.0      prev stmt bal           20240507          None  0.2899          monthly            40.0                 False
#     # 3  Approximate Loan: Principal Balance  15858.49          0.0      25000.0  principal balance           20241203        simple  0.0476            daily           250.0                 False
#     # 4           Approximate Loan: Interest      0.00          0.0      25000.0           interest               None          None    None             None            None                 False
#
#
#     B = BudgetSet.BudgetSet([])
#     B.addBudgetItem(start_date_YYYYMMDD, end_date_YYYYMMDD, 1, 'daily', 25, 'food', False, False)
#     B.addBudgetItem('20240103', '20240303', 2, 'monthly', 2000, 'pay down cc', False, True)
#     # B.addBudgetItem('20240518', end_date_YYYYMMDD, 1, 'monthly', 25, 'storage unit', False, False)
#     # B.addBudgetItem('20240518', '20240628', 1, 'semiweekly', 600, 'repay mom', False, False)
#     # B.addBudgetItem('20240701', '20270401', 1, 'monthly', 800, 'repay dad', False, False)
#     # B.addBudgetItem('20240420', end_date_YYYYMMDD, 1, 'monthly', 90, 'car insurance', False, False)
#     # B.addBudgetItem(income_start_date, end_date_YYYYMMDD, 1, 'semiweekly', 1600, 'EMT income', False, False)
#     # B.addBudgetItem('20240531', end_date_YYYYMMDD, 1, 'monthly', 900, 'pay down cc', False, False)
#     # B.addBudgetItem('20240531', end_date_YYYYMMDD, 2, 'monthly', 2200, 'more cc payment', False, True)
#
#
#     optional_B = BudgetSet.BudgetSet([])
#     # optional_B.addBudgetItem(begin_repay_cc_date, end_repay_cc_date, 1, 'monthly', 0, 'repay cc 0', False, False)
#     # optional_B.addBudgetItem(begin_repay_cc_date, end_repay_cc_date, 1, 'monthly', 500, 'repay cc 500', False, False)
#     # optional_B.addBudgetItem(begin_repay_cc_date, end_repay_cc_date, 1, 'monthly', 500, 'repay cc 750', False, False)
#     # optional_B.addBudgetItem(begin_repay_cc_date, end_repay_cc_date, 1, 'monthly', 500, 'repay cc 150', False, False)
#
#     M = MemoRuleSet.MemoRuleSet([])
#     # M.addMemoRule('repay.*', 'Checking', 'None', 1)
#     # M.addMemoRule('car insurance', 'Credit', 'None', 1)
#     M.addMemoRule('food', 'Credit', 'None', 1)
#     # M.addMemoRule('storage unit', 'Credit', 'None', 1)
#     # M.addMemoRule('.*income.*','None','Checking',1)
#     M.addMemoRule('pay down cc', 'Checking', 'Credit', 2)
#     # M.addMemoRule('more cc payment', 'Checking', 'Credit', 2)
#
#
#     MS = MilestoneSet.MilestoneSet([],[],[])
#     E = ExpenseForecast.ExpenseForecast(A,B,M,start_date_YYYYMMDD,end_date_YYYYMMDD,MS)
#     E.runForecast()
#     print(E.forecast_df.to_string())
#     # E.writeToJSONFile()
#
#     # F = ForecastHandler.ForecastHandler()
#     # # F.generateHTMLReport(E)
#     #
#     # S = ForecastSet.ForecastSet(E,option_budget_set=optional_B)
#     # S.addChoiceToAllForecasts(['repay cc 0','repay cc 500','repay cc 750','repay cc 100'],
#     #                           [['repay cc 0'],
#     #                            ['repay cc 500'],
#     #                            ['repay cc 750'],
#     #                            ['repay cc 1000']
#     #                            ])
#     # S.runAllForecasts()
#     # S.writeToJSONFile()
#     # for unique_id, E in S.initialized_forecasts.items():
#     #     F.generateHTMLReport(E)
#
#     # cmd = "python -m ef_cli parameterize forecastset --filename S.json --start_date 20000601 --end_date 20001231 --username hume"
#     # cmd_arg_list = cmd.split(" ")
#     # completed_process = subprocess.run(cmd_arg_list, capture_output=True, check=True)
#     # for l in completed_process.stdout.splitlines():
#     #     print(l)
#
#     # S = ForecastSet.initialize_from_json_file('S.json')
#     # S.runAllForecastsApproximate()
#     #
#     # for E in S.initialized_forecasts.values():
#         #E.runForecastApproximate()
#
#     # E = ExpenseForecast.initialize_from_json_file('./out/test.json')  # let this throw an exception if needed
#     # print('Running forecast')
#     # E.runForecast()
#     # E.appendSummaryLines()
#     # print('Writing forecast')
#     # E.writeToJSONFile('./out/')
#
#     # cmd = "python -m ef_cli parameterize forecastset --filename S.json --start_date 20000301 --end_date 20001231 --username hume"
#     # cmd_arg_list = cmd.split(" ")
#     # completed_process = subprocess.run(cmd_arg_list, capture_output=True, check=True)
#     #
#     #
#     # og_S = ForecastSet.initialize_from_json_file('./out/ForecastSet_S015661.json')
#     # print(og_S.initialized_forecasts)
#     # # print(og_S.unique_id)
#     # # print('------------------------------------------')
#     # # for unique_id, E in og_S.initialized_forecasts.items():
#     # #     print(E.start_date_YYYYMMDD,E.end_date_YYYYMMDD)
#     #
#     # og_S.update_date_range('20000301', '20001231')
#     #
#     # # print('------------------------------------------')
#     # # for unique_id, E in og_S.initialized_forecasts.items():
#     # #     print(E.start_date_YYYYMMDD, E.end_date_YYYYMMDD)
#     # # print(og_S.unique_id)
#     #
#     # og_S.writeToJSONFile('./out/')
#     # print(og_S.initialized_forecasts)
#     #
#     # for k, v in og_S.initialized_forecasts.items():
#     #     print(k)
#     #     v.writeToJSONFile('./out/')
#
#     # print('------------------------------------------')
#     # S = ForecastSet.initialize_from_json_file('./out/ForecastSet_S087228.json')
#     # S.update_date_range('20000301','20001231')
#
#     # for unique_id, E in S.initialized_forecasts.items():
#     #     assert E.start_date_YYYYMMDD == '20000301'
#     #     assert E.end_date_YYYYMMDD == '20001231'
#     # print('------------------------------------------')
#
#     # start_date = datetime.datetime.now().strftime('%Y%m%d')
#     # end_date = '20240430'
#     #
#     # A = AccountSet.AccountSet([])
#     # B1 = BudgetSet.BudgetSet([])
#     # # B2 = BudgetSet.BudgetSet([])
#     # # B3 = BudgetSet.BudgetSet([])
#     # # B4 = BudgetSet.BudgetSet([])
#     # # B5 = BudgetSet.BudgetSet([])
#     # M = MemoRuleSet.MemoRuleSet([])
#     #
#     # B_optional = BudgetSet.BudgetSet([])
#     # B_optional.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'Choice 1 Option A',False,False)
#     # B_optional.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'Choice 1 Option B',False,False)
#     # B_optional.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'Choice 2 Option C',False,False)
#     # B_optional.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'Choice 2 Option D',False,False)
#     #
#     # A.createCheckingAccount('Checking', 5000, 0, 99999)
#     # B1.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'food 1', False, False)
#     # # B2.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'food 2', False, False)
#     # # B3.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'food 3', False, False)
#     # # B4.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'food 4', False, False)
#     # # B5.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'food 5', False, False)
#     # M.addMemoRule('.*', 'Checking', 'None', 1)
#     #
#     # MS = MilestoneSet.MilestoneSet([], [], [])
#     # E1 = ExpenseForecast.ExpenseForecast(A, B1, M, start_date, end_date, MS)
#     #
#     # S = ForecastSet.ForecastSet(E1,B_optional,forecast_set_name='Test Forecast Name')
#     # S.addChoiceToAllForecasts(['Option A','Option B'],[['.*Option A.*'],['.*Option B.*']])
#     # S.addChoiceToAllForecasts(['Option C', 'Option D'], [['.*Option C.*'], ['.*Option D.*']])
#     #
#     # for k, v in S.initialized_forecasts.items():
#     #     v.writeToJSONFile('./out/')
#
#     # json_string = S.to_json()
#     # S2 = ForecastSet.from_json_string(json_string)
#
#     #print(S2)
#
#     # E2 = ExpenseForecast.ExpenseForecast(A, B2, M, start_date, end_date, MS)
#     # E3 = ExpenseForecast.ExpenseForecast(A, B3, M, start_date, end_date, MS)
#     # E4 = ExpenseForecast.ExpenseForecast(A, B4, M, start_date, end_date, MS)
#     # E5 = ExpenseForecast.ExpenseForecast(A, B5, M, start_date, end_date, MS)
#
#     # E1.writeToJSONFile('./out/') #031987
#     # E2.writeToJSONFile('./out/') #093122
#     # E3.writeToJSONFile('./out/') #051928
#     # E4.writeToJSONFile('./out/') #064210
#     # E5.writeToJSONFile('./out/') #052438
#
#     # print(E1.unique_id)
#     # print(E2.unique_id)
#     # print(E3.unique_id)
#     # print(E4.unique_id)
#     # print(E5.unique_id)
#     # start_date = datetime.datetime.now().strftime('%Y%m%d')
#     # end_date = '20240430'
#     # start_date2 = datetime.datetime.now().strftime('%Y%m%d')
#     # end_date2 = '20240501'
#     # start_date3 = datetime.datetime.now().strftime('%Y%m%d')
#     # end_date3 = '20240502'
#     # start_date4 = datetime.datetime.now().strftime('%Y%m%d')
#     # end_date4 = '20240503'
#     # start_date5 = datetime.datetime.now().strftime('%Y%m%d')
#     # end_date5 = '20240504'
#     #
#     # A = AccountSet.AccountSet([])
#     # B = BudgetSet.BudgetSet([])
#     # M = MemoRuleSet.MemoRuleSet([])
#     #
#     # A.createCheckingAccount('Checking', 5000, 0, 99999)
#     # B.addBudgetItem(start_date, end_date, 1, 'daily', 10, 'food', False, False)
#     # M.addMemoRule('.*', 'Checking', 'None', 1)
#     #
#     # MS = MilestoneSet.MilestoneSet([], [], [])
#     # E1 = ExpenseForecast.ExpenseForecast(A, B, M, start_date, end_date, MS)
#     # E2 = ExpenseForecast.ExpenseForecast(A, B, M, start_date2, end_date2, MS)
#     # E3 = ExpenseForecast.ExpenseForecast(A, B, M, start_date3, end_date3, MS)
#     # E4 = ExpenseForecast.ExpenseForecast(A, B, M, start_date4, end_date4, MS)
#     # E5 = ExpenseForecast.ExpenseForecast(A, B, M, start_date5, end_date5, MS)
#     #
#     # print(E1.unique_id)
#     # print(E2.unique_id)
#     # print(E3.unique_id)
#     # print(E4.unique_id)
#     # print(E5.unique_id)
#     #
#     # R = ForecastRunner.ForecastRunner('/Users/hume/Github/expense_forecast/lock/')
#     # R.start_forecast(E1)
#     # R.start_forecast(E2)
#     # R.start_forecast(E3)
#     # R.start_forecast(E4)
#     # R.start_forecast(E5)
#     #
#     # # R.print_results_as_they_come()
#     #
#     # R.ps()
#     # sleep(11)
#     # R.cancel('049833')
#     # R.ps()
#     # sleep(11)
#     # R.ps()
#     # sleep(11)
#     # R.ps()
#     # sleep(11)
#     # R.ps()
#
#
#
#
#
#     # executor = concurrent.futures.ProcessPoolExecutor()
#     #
#     # futures = {}
#     # for i in range(1,11):
#     #     keys = (5*i)
#     #     futures[keys] = executor.submit(task,keys)
#     #
#     # for i in range(0,60):
#     #     for k, v in futures.items():
#     #         print(str(k)+' '+str(v.done()))
#     #     print('--------------')
#     #     sleep(1)
#
#
#     # Future class methods
#     # future.cancel()
#     # future.cancelled()
#     # future.running()
#     # future.done()
#     # future.exception() ?
#     # future.add_done_callback()
#
#     # concurrent.futures module methods
#     # concurrent.futures.wait(fs) return_when=['FIRST_COMPLETED','FIRST_EXCEPTION','ALL_COMPLETED']
#     # concurrent.futures.as_completed(fs)
#
#
#
#     #print(future.result())
#     #executor.shutdown()
#
# ### 2024-05-03 08:37
# # FAILED test_ExpenseForecast.py::TestExpenseForecastMethods::test_initialize_forecast_from_excel_not_yet_run - AttributeError: 'NoneType' object has ...
# # FAILED test_ExpenseForecast.py::TestExpenseForecastMethods::test_initialize_forecast_from_excel_already_run - TypeError: 'ExpenseForecast' object is...
# # FAILED test_ExpenseForecast.py::TestExpenseForecastMethods::test_initialize_forecast_from_json_not_yet_run - TypeError: strptime() argument 1 must b...
# # FAILED test_ExpenseForecast.py::TestExpenseForecastMethods::test_initialize_forecast_from_json_already_run - TypeError: strptime() argument 1 must b...
# # FAILED test_ExpenseForecast.py::TestExpenseForecastMethods::test_run_forecast_from_json_at_path - TypeError: strptime() argument 1 must be str, not int
# # FAILED test_ExpenseForecast.py::TestExpenseForecastMethods::test_run_forecast_from_excel_at_path - AttributeError: 'NoneType' object has no attribut...
# # FAILED test_ExpenseForecast.py::TestExpenseForecastMethods::test_interest_types_and_cadences_at_most_monthly - NotImplementedError
# # FAILED test_ExpenseForecast.py::TestExpenseForecastMethods::test_quarter_and_year_long_interest_cadences - NotImplementedError
# # FAILED test_ForecastHandler.py::TestForecastHandlerMethods::test_run_forecast_set - AttributeError: 'BudgetSet' object has no attribute 'initial_bud...
# # FAILED test_ForecastRunner.py::TestForecastRunnerMethods::test_start_forecast[param1-param2] - ValueError: End date of budget item must be greater t...
# # FAILED test_ForecastSet.py::TestForecastSet::test_ForecastSet_writeToDatabase_empty_notRun - psycopg2.OperationalError: could not translate host nam...
# # FAILED test_ForecastSet.py::TestForecastSet::test_ForecastSet_writeToDatabase_empty_Run - psycopg2.OperationalError: could not translate host name "...
# # FAILED test_ForecastSet.py::TestForecastSet::test_ForecastSet_writeToDatabase_zeroChoices_NotRun - psycopg2.OperationalError: could not translate ho...
# # FAILED test_ForecastSet.py::TestForecastSet::test_ForecastSet_writeToDatabase_zeroChoices_Run - psycopg2.OperationalError: could not translate host ...
# # FAILED test_ForecastSet.py::TestForecastSet::test_ForecastSet_writeToDatabase_oneChoice_Run - psycopg2.OperationalError: could not translate host na...
# # FAILED test_ForecastSet.py::TestForecastSet::test_ForecastSet_writeToDatabase_oneChoice_NotRun - psycopg2.OperationalError: could not translate host...
# # FAILED test_ForecastSet.py::TestForecastSet::test_ForecastSet_writeToDatabase_twoChoices_NotRun - psycopg2.OperationalError: could not translate hos...
# # FAILED test_ForecastSet.py::TestForecastSet::test_ForecastSet_writeToDatabase_twoChoices_Run - psycopg2.OperationalError: could not translate host n...
# # FAILED test_ef_cli.py::TestEFCLIMethods::test_help[cmd_string] - subprocess.CalledProcessError: Command '['python', '-m', 'ef_cli', 'cmd_string']' r...
# # FAILED test_ef_cli.py::TestEFCLIMethods::test_parameterize_file_forecast_no_label[parameterize forecast --id 031987 --source file --start_date 20240101 --end_date 20241231 --username hume --log_directory ./out/]
# # FAILED test_ef_cli.py::TestEFCLIMethods::test_parameterize_file_forecast_with_label[parameterize forecast --id 031987 --source file --start_date 20240101 --end_date 20241231 --username hume --log_directory ./out/ --label FORECAST_LABEL]
# # FAILED test_ef_cli.py::TestEFCLIMethods::test_parameterize_file_forecastset_no_label[parameterize forecastset --source file --id S --username hume --output_directory ./out/ --start_date 20240120 --end_date 20240601]
# # FAILED test_ef_cli.py::TestEFCLIMethods::test_parameterize_file_forecastset_no_label[parameterize forecastset --source file --id S --username hume --output_directory ./out/ --start_date 20000120 --end_date 20000601]
# # FAILED test_ef_cli.py::TestEFCLIMethods::test_parameterize_file_forecastset_no_label[parameterize forecastset --source file --id S --username hume --output_directory ./out/ --start_date 20240420 --end_date 20240601]
# # FAILED test_ef_cli.py::TestEFCLIMethods::test_parameterize_file_forecastset_with_label[parameterize forecastset --filename S.json --start_date 20000601 --end_date 20001231 --username hume --label NEW_FORECAST_SET_NAME]
# # FAILED test_ef_cli.py::TestEFCLIMethods::test_run_forecast[run forecast --id 062822 --source file --username hume --working_directory ./out/] - subp...
# # FAILED test_ef_cli.py::TestEFCLIMethods::test_run_forecast[run forecast --id 062822 --source file --username hume --working_directory ./out/ --approximate]
# # FAILED test_ef_cli.py::TestEFCLIMethods::test_run_forecast[run forecast --id 062822 --source file --username hume --working_directory ./out/ --overwrite]
# # FAILED test_ef_cli.py::TestEFCLIMethods::test_run_forecast[run forecast --id 062822 --source file --username hume --working_directory ./out/ --approximate --overwrite]
# # FAILED test_ef_cli.py::TestEFCLIMethods::test_run_forecastset[run forecastset --source file --id S033683 --username hume --working_directory ./out/]
# # FAILED test_ef_cli.py::TestEFCLIMethods::test_run_forecastset[run forecastset --source file --id S033683 --username hume --working_directory ./out/ --approximate]
# # FAILED test_ef_cli.py::TestEFCLIMethods::test_run_forecastset[run forecastset --source file --id S033683 --username hume --working_directory ./out/ --overwrite]
# # FAILED test_ef_cli.py::TestEFCLIMethods::test_run_forecastset[run forecastset --source file --id S033683 --username hume --working_directory ./out/ --approximate --overwrite]
# # FAILED test_ef_cli.py::TestEFCLIMethods::test_list[list] - subprocess.CalledProcessError: Command '['python', '-m', 'ef_cli', 'list']' returned non-...

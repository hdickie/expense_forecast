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
import datetime
import math

pd.options.mode.chained_assignment = None #apparently this warning can throw false positives???


# import subprocess
# import pebble

# def task(n_seconds):
#     sleep(n_seconds)
#     return 'Done!'

# from generate_date_sequence import generate_date_sequence

if __name__ == '__main__':


    start_date_YYYYMMDD = datetime.datetime.now().strftime('%Y%m%d')
    end_date_YYYYMMDD = '20260101'

    A = AccountSet.AccountSet([])
    A.createCheckingAccount('Checking', 3325.36 + 88.42 + 45.39, 0, 999999999, True)
    A.createCreditCardAccount('Credit', 0, 14286.00, 0, 25000, '20240107', 0.2899, 40, billing_cycle_payment_balance=0, end_of_previous_cycle_balance=14286.00)
    A.createLoanAccount('Dad Loan',(15000 + 1400) - 500*2,0,0,20000,'20240101',0,500, billing_cycle_payment_balance=0, end_of_previous_cycle_balance=(15000 + 1400) - 500*2)
    A.createLoanAccount('Student Loans', 15000, 100, 0, 16000, '20241003', 0.06, 223.19, billing_cycle_payment_balance=0, end_of_previous_cycle_balance=15000)

    B = BudgetSet.BudgetSet([])
    B.addBudgetItem('20240105', end_date_YYYYMMDD, 1, 'semiweekly', 1600, 'EMT income')
    B.addBudgetItem(start_date_YYYYMMDD, end_date_YYYYMMDD, 1, 'daily', 20, 'food')
    B.addBudgetItem('20240702', end_date_YYYYMMDD, 1, 'monthly', 20, 'hulu')
    B.addBudgetItem('20240702', end_date_YYYYMMDD, 1, 'monthly', 20, 'ai daddy')
    B.addBudgetItem('20240702', end_date_YYYYMMDD, 1, 'monthly', 50, 'parking')
    B.addBudgetItem('20240702', end_date_YYYYMMDD, 1, 'semiweekly', 80, 'gas')
    B.addBudgetItem('20240420', end_date_YYYYMMDD, 1, 'monthly', 95, 'car insurance')
    B.addBudgetItem('20240401', end_date_YYYYMMDD, 1, 'monthly', 100, 'storage unit rent')
    B.addBudgetItem('20240818', end_date_YYYYMMDD, 1, 'monthly', 250, 'phone')
    B.addBudgetItem('20240903', '20240903', 1, 'once', 500, 'sjcc fall tuition')
    B.addBudgetItem('20250203', '20250203', 1, 'once', 400, 'sjcc spring 2025 tuition')
    B.addBudgetItem('20250603', '20250603', 1, 'once', 400, 'sjcc summer 2025 tuition')
    B.addBudgetItem('20250803', '20250803', 1, 'once', 400, 'sjcc fall 2025 tuition')
    # B.addBudgetItem('20260929', '20260929', 1, 'once', 1250, 'evergreen tuition fall 2026')
    # B.addBudgetItem('20270112', '20270112', 1, 'once', 1250, 'evergreen tuition winter 2026')
    # B.addBudgetItem('20270405', '20270405', 1, 'once', 1250, 'evergreen tuition spring 2027')
    # B.addBudgetItem('20270628', '20270628', 1, 'once', 1250, 'evergreen tuition summer 2027')

    B2 = BudgetSet.BudgetSet(B.budget_items)

    # start date 10/18
    #B2.addBudgetItem('20240505', end_date_YYYYMMDD, 2, 'monthly', 7000, 'pay cc', deferrable=False,partial_payment_allowed=True)
    B2.addBudgetItem('20241105', '20241105', 1, 'once', 3235.98, 'pay cc 11/5')
    B2.addBudgetItem('20241205', '20241205', 1, 'once', 2476.81, 'pay cc 12/5')
    B2.addBudgetItem('20250105', '20250105', 1, 'once', 4076.81, 'pay cc 1/5/25')
    B2.addBudgetItem('20250205', '20250205', 1, 'once', 2076.81, 'pay cc 2/5/25')
    B2.addBudgetItem('20250305', '20250305', 1, 'once', 2476.81, 'pay cc 3/5/25')
    B2.addBudgetItem('20250405', '20250405', 1, 'once', 2476.81, 'pay cc 4/5/25')
    B2.addBudgetItem('20250505', '20250505', 1, 'once', 2476.81, 'pay cc 5/5/25')
    B2.addBudgetItem('20250605', '20250605', 1, 'once', 2076.81, 'pay cc 6/5/25')
    B2.addBudgetItem('20250705', '20250705', 1, 'once', 4076.81, 'pay cc 7/5/25')

    B2.addBudgetItem('20250805', '20250805', 1, 'once', 539.84, 'pay cc 8/5/25')
    B2.addBudgetItem('20250905', '20250905', 1, 'once', 1275, 'pay cc 9/5/25')
    B2.addBudgetItem('20251005', '20251005', 1, 'once', 1255, 'pay cc 10/5/25')
    B2.addBudgetItem('20251105', '20251105', 1, 'once', 1275, 'pay cc 11/5/25')
    B2.addBudgetItem('20251205', '20251205', 1, 'once', 1255.00, 'pay cc 12/5/25')

    B2.addBudgetItem('20250905', end_date_YYYYMMDD, 2, 'monthly', 7000, 'pay cc', deferrable=False,partial_payment_allowed=True)



    # cycle_amount = 1500
    # asymptote_surplus_amount = 500
    # B.addBudgetItem(start_date_YYYYMMDD, end_date_YYYYMMDD, 1, 'monthly', cycle_amount + asymptote_surplus_amount, 'pay cc cycle + extra')


    M = MemoRuleSet.MemoRuleSet([])
    M.addMemoRule('food', 'Credit', 'None', 1)
    M.addMemoRule('parking', 'Credit', 'None', 1)
    M.addMemoRule('hulu', 'Credit', 'None', 1)
    M.addMemoRule('ai daddy', 'Credit', 'None', 1)
    M.addMemoRule('car insurance', 'Credit', 'None', 1)
    M.addMemoRule('storage unit', 'Credit', 'None', 1)
    M.addMemoRule('phone', 'Credit', 'None', 1)
    M.addMemoRule('gas', 'Credit', 'None', 1)
    M.addMemoRule('pay cc', 'Checking', 'Credit', 2)
    M.addMemoRule('.*pay cc.*', 'Checking', 'Credit', 1)
    M.addMemoRule('.*income.*', 'None', 'Checking', 1)
    M.addMemoRule('.*repay.*', 'Checking', 'None', 1)
    M.addMemoRule('.*tuition.*', 'Checking', 'None', 1)
    M.addMemoRule('.*fake loan payment.*', 'Checking', 'None', 1)

    MS = MilestoneSet.MilestoneSet([], [], [])

    # E_p1 = ExpenseForecast.ExpenseForecast(A, B, M, start_date_YYYYMMDD, end_date_YYYYMMDD, MS)
    E_p2 = ExpenseForecast.ExpenseForecast(A, B2, M, start_date_YYYYMMDD, end_date_YYYYMMDD, MS)
    #
    # E_p1.runForecast(log_level='DEBUG')
    # E_p1.forecast_df.to_csv('E_p1.csv')

    E_p2.runForecast(log_level='DEBUG')
    E_p2.forecast_df.to_csv('E_p2.csv')
    print(E_p2)

    # for index, row in E_p1.forecast_df.iterrows():
    #     try:
    #         assert E_p1.forecast_df.loc[index,'Checking'] == E_p2.forecast_df.loc[index,'Checking']
    #         assert E_p1.forecast_df.loc[index, 'Credit: Curr Stmt Bal'] == E_p2.forecast_df.loc[index, 'Credit: Curr Stmt Bal']
    #         assert E_p1.forecast_df.loc[index, 'Credit: Prev Stmt Bal'] == E_p2.forecast_df.loc[index, 'Credit: Prev Stmt Bal']
    #     except Exception as e:
    #         print(e.args)
    #         print('Mismatch at index = '+str(index))
    #         print(E_p1.forecast_df.loc[index])
    #         print(E_p2.forecast_df.loc[index])
    #         raise e
    # print('Forecasts Matched :)')

# 0       Date Checking Credit: Curr Stmt Bal Credit: Prev Stmt Bal  Marginal Interest  Net Gain  Net Loss Net Worth Loan Total CC Debt Total Liquid Total                                                                                                                                                                                                                 Memo Directives                                                                                                                                                                                                                                              Memo
# 0   20241012  2479.42                   0.0              12609.79               0.00      0.00       0.0 -10130.37        0.0      12609.79      2479.42
# 1   20241112  4748.69                     0              13513.69             304.63   1365.37       0.0   -8765.0        0.0      13513.69      4748.69                                                                                               CC INTEREST (Credit: Prev Stmt Bal +$304.63); CC MIN PAYMENT (Credit: Prev Stmt Bal -$430.73); CC MIN PAYMENT (Checking -$430.73)                                         EMT income x2 (Checking +$3200.00); food x32 (Credit -$640.00); repay dad (Checking -$500.00); phone (Credit -$250.00); car insurance (Credit -$100.00); hulu (Credit -$20.00); ai daddy (Credit -$20.00)
# 2   20241212      0.0                     0               7631.47             326.47   1133.53       0.0  -7631.47        0.0       7631.47          0.0    CC INTEREST (Credit: Prev Stmt Bal +$326.47); CC MIN PAYMENT (Credit: Prev Stmt Bal -$461.61); CC MIN PAYMENT (Checking -$461.61); ADDTL CC PAYMENT (Checking -$6737.08); ADDTL CC PAYMENT (Credit: Prev Stmt Bal -$6737.08)  EMT income x2 (Checking +$3200.00); food x30 (Credit -$600.00); repay dad (Checking -$500.00); phone (Credit -$250.00); fake loan payment (Checking -$250.00); car insurance (Credit -$100.00); ai daddy (Credit -$20.00); hulu (Credit -$20.00)
# 3   20250112  1959.19                     0               8497.78             347.12   1092.88       0.0  -6538.59        0.0       8497.78      1959.19                                                                                               CC INTEREST (Credit: Prev Stmt Bal +$347.12); CC MIN PAYMENT (Checking -$490.81); CC MIN PAYMENT (Credit: Prev Stmt Bal -$490.81)  EMT income x2 (Checking +$3200.00); food x31 (Credit -$620.00); repay dad (Checking -$500.00); phone (Credit -$250.00); fake loan payment (Checking -$250.00); car insurance (Credit -$100.00); ai daddy (Credit -$20.00); hulu (Credit -$20.00)
# 4   20250212      0.0                     0               5671.93             205.29   1234.71       0.0  -5671.93        0.0       5671.93          0.0  CC INTEREST (Credit: Prev Stmt Bal +$205.29); CC MIN PAYMENT (Credit: Prev Stmt Bal -$290.270); CC MIN PAYMENT (Checking -$290.270); ADDTL CC PAYMENT (Checking -$4179.06); ADDTL CC PAYMENT (Credit: Prev Stmt Bal -$4179.06)  EMT income x2 (Checking +$3200.00); food x31 (Credit -$620.00); repay dad (Checking -$500.00); phone (Credit -$250.00); fake loan payment (Checking -$250.00); car insurance (Credit -$100.00); hulu (Credit -$20.00); ai daddy (Credit -$20.00)
# 5   20250312  2236.79                     0               7035.47             237.98   1262.02       0.0  -4798.68        0.0       7035.47      2236.79                                                                                             CC INTEREST (Credit: Prev Stmt Bal +$237.98); CC MIN PAYMENT (Checking -$336.490); CC MIN PAYMENT (Credit: Prev Stmt Bal -$336.490)  EMT income x2 (Checking +$3200.00); food x28 (Credit -$560.00); repay dad (Checking -$500.00); phone (Credit -$250.00); fake loan payment (Checking -$250.00); car insurance (Credit -$100.00); hulu (Credit -$20.00); ai daddy (Credit -$20.00)
# 6   20250412      0.0                     0                2607.4             169.97   2870.03       0.0   -2607.4        0.0        2607.4          0.0    CC INTEREST (Credit: Prev Stmt Bal +$169.97); CC MIN PAYMENT (Credit: Prev Stmt Bal -$240.32); CC MIN PAYMENT (Checking -$240.32); ADDTL CC PAYMENT (Checking -$6333.53); ADDTL CC PAYMENT (Credit: Prev Stmt Bal -$6333.53)  EMT income x3 (Checking +$4800.00); food x31 (Credit -$620.00); repay dad (Checking -$500.00); phone (Credit -$250.00); fake loan payment (Checking -$250.00); car insurance (Credit -$100.00); hulu (Credit -$20.00); ai daddy (Credit -$20.00)
# 7   20250512      0.0                     0                2098.6             216.00   1244.00       0.0   -2098.6        0.0        2098.6          0.0     CC INTEREST (Credit: Prev Stmt Bal +$216.0); CC MIN PAYMENT (Checking -$305.41); CC MIN PAYMENT (Credit: Prev Stmt Bal -$305.41); ADDTL CC PAYMENT (Checking -$2584.18); ADDTL CC PAYMENT (Credit: Prev Stmt Bal -$2584.18)  EMT income x2 (Checking +$3200.00); food x30 (Credit -$600.00); repay dad (Checking -$500.00); phone (Credit -$250.00); fake loan payment (Checking -$250.00); car insurance (Credit -$100.00); ai daddy (Credit -$20.00); hulu (Credit -$20.00)
# 8   20250612      0.0                     0               1830.25             113.13   1326.87       0.0  -1830.25        0.0       1830.25          0.0    CC INTEREST (Credit: Prev Stmt Bal +$113.13); CC MIN PAYMENT (Checking -$159.96); CC MIN PAYMENT (Credit: Prev Stmt Bal -$159.96); ADDTL CC PAYMENT (Checking -$2840.34); ADDTL CC PAYMENT (Credit: Prev Stmt Bal -$2840.34)  EMT income x2 (Checking +$3200.00); food x31 (Credit -$620.00); repay dad (Checking -$500.00); phone (Credit -$250.00); fake loan payment (Checking -$250.00); car insurance (Credit -$100.00); hulu (Credit -$20.00); ai daddy (Credit -$20.00)
# 9   20250712      0.0                     0               1832.32             112.83   1347.17       0.0  -1832.32        0.0       1832.32          0.0    CC INTEREST (Credit: Prev Stmt Bal +$112.83); CC MIN PAYMENT (Checking -$159.54); CC MIN PAYMENT (Credit: Prev Stmt Bal -$159.54); ADDTL CC PAYMENT (Checking -$3194.66); ADDTL CC PAYMENT (Credit: Prev Stmt Bal -$3194.66)  EMT income x2 (Checking +$3200.00); food x30 (Credit -$600.00); repay dad (Checking -$500.00); phone (Credit -$250.00); fake loan payment (Checking -$250.00); car insurance (Credit -$100.00); ai daddy (Credit -$20.00); hulu (Credit -$20.00)
# 10  20250812      0.0                     0               2245.05             121.44   1318.56       0.0  -2245.05        0.0       2245.05          0.0    CC INTEREST (Credit: Prev Stmt Bal +$121.44); CC MIN PAYMENT (Checking -$171.71); CC MIN PAYMENT (Credit: Prev Stmt Bal -$171.71); ADDTL CC PAYMENT (Checking -$3692.60); ADDTL CC PAYMENT (Credit: Prev Stmt Bal -$3692.60)  EMT income x2 (Checking +$3200.00); food x31 (Credit -$620.00); repay dad (Checking -$500.00); phone (Credit -$250.00); fake loan payment (Checking -$250.00); car insurance (Credit -$100.00); ai daddy (Credit -$20.00); hulu (Credit -$20.00)
# 11  20250912      0.0                     0                1604.1             143.44   2896.56       0.0   -1604.1        0.0        1604.1          0.0    CC INTEREST (Credit: Prev Stmt Bal +$143.44); CC MIN PAYMENT (Checking -$202.82); CC MIN PAYMENT (Credit: Prev Stmt Bal -$202.82); ADDTL CC PAYMENT (Checking -$6009.85); ADDTL CC PAYMENT (Credit: Prev Stmt Bal -$6009.85)  EMT income x3 (Checking +$4800.00); food x31 (Credit -$620.00); repay dad (Checking -$500.00); phone (Credit -$250.00); fake loan payment (Checking -$250.00); car insurance (Credit -$100.00); hulu (Credit -$20.00); ai daddy (Credit -$20.00)
# 12  20251012      0.0                     0                3317.7             183.94   1276.06       0.0   -3317.7        0.0        3317.7          0.0    CC INTEREST (Credit: Prev Stmt Bal +$183.94); CC MIN PAYMENT (Checking -$260.08); CC MIN PAYMENT (Credit: Prev Stmt Bal -$260.08); ADDTL CC PAYMENT (Checking -$5450.35); ADDTL CC PAYMENT (Credit: Prev Stmt Bal -$5450.35)  EMT income x2 (Checking +$3200.00); food x30 (Credit -$600.00); repay dad (Checking -$500.00); phone (Credit -$250.00); fake loan payment (Checking -$250.00); car insurance (Credit -$100.00); ai daddy (Credit -$20.00); hulu (Credit -$20.00)



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

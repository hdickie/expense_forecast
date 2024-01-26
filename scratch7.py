
import pandas as pd

pd.options.mode.chained_assignment = None #apparently this warning can throw false positives???

from log_methods import log_in_color

import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
import numpy as np

import ForecastHandler
import BudgetSet
import AccountSet
import MemoRuleSet
import MilestoneSet
import ForecastSet
import AccountMilestone
import datetime

if __name__ == '__main__':
    start_date_YYYYMMDD = '20240123'
    end_date_YYYYMMDD = '20290101'

    # start_date_YYYYMMDD = '20240101'
    # end_date_YYYYMMDD = '20240201'

    first_rent_date = '20240401'

    start_driving_for_work_date = '20240301'
    first_gym_date = '20240601'

    first_rn_paycheck_date = '20280201'
    last_rn_paycheck_date = end_date_YYYYMMDD
    er_tech_first_paycheck_dates = ['20240901', '20241001', '20241101', '20241201', '20250101', '20250201', '20250301']
    er_tech_last_paycheck_date = (
                datetime.datetime.strptime(first_rn_paycheck_date, '%Y%m%d') - datetime.timedelta(days=14)).strftime(
        '%Y%m%d')

    first_emt_paycheck_date = '20240301'
    last_emt_paycheck_dates = [
        (datetime.datetime.strptime(d, '%Y%m%d') - datetime.timedelta(days=14)).strftime('%Y%m%d') for d in
        er_tech_first_paycheck_dates]

    first_cheap_food_day = start_date_YYYYMMDD
    # last_cheap_food_day = (datetime.datetime.strptime(first_er_tech_paycheck_date,'%Y%m%d') - datetime.timedelta(days=1)).strftime('%Y%m%d')
    last_cheap_food_day = end_date_YYYYMMDD
    first_nice_food_day = end_date_YYYYMMDD
    last_nice_food_day = end_date_YYYYMMDD

    additional_cc_payment__er_tech____first_date = er_tech_first_paycheck_dates
    # additional_cc_payment__er_tech____first_date = '20260101'
    additional_cc_payment__er_tech____last_date = er_tech_last_paycheck_date
    additional_cc_payment__er_tech___amount = 400

    additional_cc_payment__RN___first_date = first_rn_paycheck_date
    # additional_cc_payment__RN___first_date = first_er_tech_paycheck_date
    additional_cc_payment__RN___last_date = end_date_YYYYMMDD
    additional_cc_payment__RN___amount = 0

    end_of_recaptialization_date = '20240601'
    car_insurance_amount = 89.0
    daily_cheap_food_amount = 10
    daily_nice_food_amount = 20
    monthly_gas_amount = 160 / 2  # doin this as semiweekly bc closer to irl
    semiweekly_emt_income_amount = 15 * 80
    semiweekly_er_tech_income_amount = 21.25 * 80
    semiweekly_rn_amount = 33 * 80
    rent_amount = 1200
    gym_monthly_amount = 50

    loan_A_pbal = 15000
    loan_A_interest = 100
    loan_A_APR = 0.06
    loan_A_min_payment = 113

    A = AccountSet.AccountSet([])
    A.createAccount('Checking', 4000, 0, 99999, 'checking')
    A.createAccount('Credit', 0, 0, 25000, 'credit', '20240107', 'compound', 0.24, 'monthly', 40, 23751.93)

    A.createAccount('Loan A', loan_A_pbal + loan_A_interest, 0, 25000, 'loan', end_of_recaptialization_date, 'simple',
                    loan_A_APR, 'daily', loan_A_min_payment, None, loan_A_pbal, loan_A_interest)
    # # A.createAccount('Loan A', loan_B_pbal + loan_B_interest, 0, 25000, 'loan', '20240103', 'simple', loan_B_APR, 'daily', loan_B_min_payment, None, loan_B_pbal, loan_B_interest)
    # # A.createAccount('Loan A', loan_C_pbal + loan_C_interest, 0, 25000, 'loan', '20240103', 'simple', loan_C_APR, 'daily', loan_C_min_payment, None, loan_C_pbal, loan_C_interest)
    # # A.createAccount('Loan A', loan_D_pbal + loan_D_interest, 0, 25000, 'loan', '20240103', 'simple', loan_D_APR, 'daily', loan_D_min_payment, None, loan_D_pbal, loan_D_interest)
    # # A.createAccount('Loan A', loan_E_pbal + loan_E_interest, 0, 25000, 'loan', '20240103', 'simple', loan_E_APR, 'daily', loan_E_min_payment, None, loan_E_pbal, loan_E_interest)

    core_budget_set = BudgetSet.BudgetSet([])
    option_budget_set = BudgetSet.BudgetSet([])

    core_budget_set.addBudgetItem(first_cheap_food_day, last_cheap_food_day, 1, 'daily', daily_cheap_food_amount,
                                  'cheap food', False, False)
    core_budget_set.addBudgetItem(first_gym_date, end_date_YYYYMMDD, 1, 'semiweekly', gym_monthly_amount, 'gym', False,
                                  False)
    core_budget_set.addBudgetItem('20240602', '20240602', 1, 'once', 1245.97, 'tax debt', False, False)
    core_budget_set.addBudgetItem('20240118', end_date_YYYYMMDD, 1, 'monthly', car_insurance_amount, 'car insurance',
                                  False, False)
    core_budget_set.addBudgetItem(first_rent_date, end_date_YYYYMMDD, 1, 'monthly', rent_amount, 'rent', False, False)
    core_budget_set.addBudgetItem(start_driving_for_work_date, end_date_YYYYMMDD, 1, 'semiweekly', monthly_gas_amount,
                                  'gas', False, False)

    core_budget_set.addBudgetItem(first_nice_food_day, last_nice_food_day, 1, 'daily', daily_nice_food_amount,
                                  'nice food', False, False)

    # er_tech_last_paycheck_date

    for i in range(0, len(er_tech_first_paycheck_dates)):
        last_emt_paycheck_date = last_emt_paycheck_dates[i]
        er_tech_first_paycheck_date = er_tech_first_paycheck_dates[i]

        memo_suffix = ' er tech first day ' + str(er_tech_first_paycheck_date)
        option_budget_set.addBudgetItem(first_emt_paycheck_date, last_emt_paycheck_date, 1, 'semiweekly',
                                        semiweekly_emt_income_amount, 'emt income' + memo_suffix, False, False)

        option_budget_set.addBudgetItem(er_tech_first_paycheck_date, er_tech_last_paycheck_date, 1, 'semiweekly',
                                        semiweekly_er_tech_income_amount, 'er tech income' + memo_suffix, False, False)
        option_budget_set.addBudgetItem(er_tech_first_paycheck_date, last_emt_paycheck_date, 1, 'semiweekly',
                                        additional_cc_payment__er_tech___amount,
                                        'additional cc payment' + memo_suffix, False, False)

    additional_cc_payment__RN___amounts = [400, 600, 700, 800]
    for amt in additional_cc_payment__RN___amounts:
        memo_suffix = ' rn first day ' + str(first_rn_paycheck_date) + ' ' + str(amt)
        option_budget_set.addBudgetItem(first_rn_paycheck_date, last_rn_paycheck_date, 1, 'semiweekly',
                                        amt,
                                        'additional cc payment' + memo_suffix, False, False)

    core_budget_set.addBudgetItem(first_rn_paycheck_date, last_rn_paycheck_date, 1, 'semiweekly', semiweekly_rn_amount,
                                  'rn income', False, False)

    # core_budget_set.addBudgetItem('20241201', '20241201', 1, 'once', 1200, 'tax debt 2', False, False) # just an assumption

    # 2,346.21 left in sf mra

    # option_budget_set.addBudgetItem(start_date_YYYYMMDD, end_date_YYYYMMDD, 1, 'daily', 10, 'txn 1A', False, False)

    M = MemoRuleSet.MemoRuleSet([])
    M.addMemoRule('car insurance', 'Checking', None, 1)
    M.addMemoRule('gas', 'Checking', None, 1)
    M.addMemoRule('food', 'Checking', None, 1)
    M.addMemoRule('rent', 'Checking', None, 1)
    M.addMemoRule('gym', 'Checking', None, 1)
    M.addMemoRule('tax debt', 'Checking', None, 1)
    M.addMemoRule('.*additional cc payment.*', 'Checking', 'Credit', 1)
    M.addMemoRule('.*income.*', None, 'Checking', 1)

    MS = MilestoneSet.MilestoneSet([AccountMilestone.AccountMilestone('Credit below 5k', 'Credit', 0, 5000),
                                    AccountMilestone.AccountMilestone('No credit card debt', 'Credit', 0, 8000),
                                    AccountMilestone.AccountMilestone('Loan 5k', 'Loan A', 0, 5000),
                                    AccountMilestone.AccountMilestone('Loans paid off', 'Credit', 0, 0),
                                    ], [], [])

    # S = ForecastSet.ForecastSet(core_budget_set, option_budget_set)
    #
    # scenario_A = ['.*A.*']
    # scenario_B = ['.*B.*']
    # scenario_C = ['.*C.*']
    # scenario_D = ['.*D.*']
    # S.addChoiceToAllScenarios(['A', 'B'], [scenario_A, scenario_B])
    # S.addChoiceToAllScenarios(['C', 'D'], [scenario_C, scenario_D])

    F = ForecastHandler.ForecastHandler()

    S = ForecastSet.ForecastSet(core_budget_set, option_budget_set)

    # todo
    # er_tech_first_paycheck_dates = ['20240901', '20241001', '20241101', '20241201', '20250101', '20250201','20250301']
    # [400, 600, 700, 800]
    first_day_choice = ['er tech first day 20240901', 'er tech first day 20241001', 'er tech first day 20241101',
                        'er tech first day 20241201', 'er tech first day 20250101', 'er tech first day 20250201',
                        'er tech first day 20250301']
    first_day_choice_lol = [[d] for d in first_day_choice]
    cc_amt_amount_choice = ['additional cc payment rn first day 20280201 400',
                            'additional cc payment rn first day 20280201 600',
                            'additional cc payment rn first day 20280201 700',
                            'additional cc payment rn first day 20280201 800']
    cc_amt_amount_choice_lol = [[a] for a in cc_amt_amount_choice]
    S.addChoiceToAllScenarios(
        ['start er tech 9/1/24', 'start er tech 10/1/24', 'start er tech 11/1/24', 'start er tech 12/1/24',
         'start er tech 1/1/25', 'start er tech 2/1/25', 'start er tech 3/1/25', ], first_day_choice_lol)
    S.addChoiceToAllScenarios(['pay cc extra 400', 'pay cc extra 600', 'pay cc extra 700', 'pay cc extra 800'],
                              cc_amt_amount_choice_lol)

    print(S)
    E__dict = F.initialize_forecasts_with_scenario_set(A, S, M, start_date_YYYYMMDD, end_date_YYYYMMDD, MS)
    for key, value in E__dict.items():
        print(value.unique_id)
import BudgetSet
import ExpenseForecast
import AccountSet
import pandas as pd
import MemoRuleSet
import copy
import ForecastHandler
import MilestoneSet
import MemoRule
import AccountMilestone
import BudgetItem
import ForecastSet

pd.options.mode.chained_assignment = None #apparently this warning can throw false positives???

from log_methods import log_in_color

if __name__ == '__main__':

    start_date_YYYYMMDD = '20240101'
    end_date_YYYYMMDD = '20240110'
    #end_date_YYYYMMDD = '20260101'

    first_emt_paycheck_date = '20240301'
    first_rent_date = '20240401'
    last_emt_paycheck_date = '20250101'
    first_er_tech_paycheck_date = last_emt_paycheck_date
    start_driving_for_work_date = '20240214'
    first_gym_date = '20240601'
    nice_food_day = end_date_YYYYMMDD
    additional_loan_payment_date = first_er_tech_paycheck_date

    end_of_recaptialization_date = '20240601'
    car_insurance_amount = 89.0
    daily_cheap_food_amount = 10
    daily_nice_food_amount = 20
    monthly_gas_amount = 160 / 2 #doin this as semiweekly bc closer to irl
    semiweekly_emt_income_amount = 1200
    semiweekly_er_tech_income_amount = 1700
    rent_amount = 1200
    gym_monthly_amount = 50

    loan_A_pbal = 15000
    loan_A_interest = 100
    loan_A_APR = 0.06
    loan_A_min_payment = 113

    A = AccountSet.AccountSet([])
    A.createAccount('Checking', 4000, 0, 99999, 'checking')
    A.createAccount('Credit', 0, 0, 25000, 'credit','20240107','compound',0.24,'monthly',40,23751.93)

    A.createAccount('Loan A', loan_A_pbal + loan_A_interest, 0, 25000, 'loan', end_of_recaptialization_date, 'simple', loan_A_APR, 'daily', loan_A_min_payment, None, loan_A_pbal, loan_A_interest)
    # A.createAccount('Loan A', loan_B_pbal + loan_B_interest, 0, 25000, 'loan', '20240103', 'simple', loan_B_APR, 'daily', loan_B_min_payment, None, loan_B_pbal, loan_B_interest)
    # A.createAccount('Loan A', loan_C_pbal + loan_C_interest, 0, 25000, 'loan', '20240103', 'simple', loan_C_APR, 'daily', loan_C_min_payment, None, loan_C_pbal, loan_C_interest)
    # A.createAccount('Loan A', loan_D_pbal + loan_D_interest, 0, 25000, 'loan', '20240103', 'simple', loan_D_APR, 'daily', loan_D_min_payment, None, loan_D_pbal, loan_D_interest)
    # A.createAccount('Loan A', loan_E_pbal + loan_E_interest, 0, 25000, 'loan', '20240103', 'simple', loan_E_APR, 'daily', loan_E_min_payment, None, loan_E_pbal, loan_E_interest)

    core_budget_set = BudgetSet.BudgetSet([])
    option_budget_set = BudgetSet.BudgetSet([])

    core_budget_set.addBudgetItem(start_date_YYYYMMDD, nice_food_day, 1, 'daily', daily_cheap_food_amount, 'cheap food',False, False)
    core_budget_set.addBudgetItem('20240105', '20240105', 2, 'once', 10, 'test txn',False, False)

    # core_budget_set.addBudgetItem(nice_food_day, end_date_YYYYMMDD, 1, 'daily', daily_nice_food_amount, 'nice food', False, False)
    # core_budget_set.addBudgetItem('20240118', end_date_YYYYMMDD, 1, 'monthly', car_insurance_amount, 'car insurance', False, False)
    # core_budget_set.addBudgetItem(first_rent_date, end_date_YYYYMMDD, 1, 'monthly', rent_amount, 'rent', False, False)
    # core_budget_set.addBudgetItem(start_driving_for_work_date, end_date_YYYYMMDD, 1, 'semiweekly', monthly_gas_amount, 'gas',False, False)
    # core_budget_set.addBudgetItem(first_emt_paycheck_date, last_emt_paycheck_date, 1, 'semiweekly', semiweekly_emt_income_amount, 'emt income',False, False)
    # core_budget_set.addBudgetItem(first_er_tech_paycheck_date, end_date_YYYYMMDD, 1, 'semiweekly',semiweekly_er_tech_income_amount, 'er tech income', False, False)
    # core_budget_set.addBudgetItem(first_gym_date, end_date_YYYYMMDD, 1, 'semiweekly', gym_monthly_amount, 'gym', False, False)
    # core_budget_set.addBudgetItem('20240602', '20240602', 1, 'once', 1245.97, 'tax debt', False, False)
    #core_budget_set.addBudgetItem(additional_loan_payment_date, end_date_YYYYMMDD, 2, 'monthly', 800, 'additional cc payment', False, True)

    #2,346.21 left in sf mra


    #option_budget_set.addBudgetItem(start_date_YYYYMMDD, end_date_YYYYMMDD, 1, 'daily', 10, 'txn 1A', False, False)

    M = MemoRuleSet.MemoRuleSet([])
    M.addMemoRule('car insurance', 'Checking', None, 1)
    M.addMemoRule('test txn', 'Checking', None, 2)
    M.addMemoRule('gas', 'Checking', None, 1)
    M.addMemoRule('food', 'Checking', None, 1)
    M.addMemoRule('rent', 'Checking', None, 1)
    M.addMemoRule('gym', 'Checking', None, 1)
    M.addMemoRule('tax debt', 'Checking', None, 1)
    M.addMemoRule('additional cc payment', 'Checking', 'Credit', 2)
    M.addMemoRule('.*income.*', None, 'Checking', 1)

    MS = MilestoneSet.MilestoneSet([#AccountMilestone.AccountMilestone('Checking below 9500', 'Checking', 0, 9500),
                                    #AccountMilestone.AccountMilestone('Checking below 8000', 'Checking', 0, 8000)
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

    E = ExpenseForecast.ExpenseForecast(A,core_budget_set,M,start_date_YYYYMMDD,end_date_YYYYMMDD,MS)
    E.runForecast()
    E.appendSummaryLines()
    F.generateHTMLReport(E)

    # EF() :: account_set, budget_set, memo_rule_set, start_date_YYYYMMDD, end_date_YYYYMMDD,milestone_set,

    #E__dict = F.initialize_forecasts_with_scenario_set(A, S, M, start_date_YYYYMMDD, end_date_YYYYMMDD, MS)

    # for key, value in E__dict.items():
    #     value.runForecast()
    #     value.appendSummaryLines()
    #     value.writeToJSONFile('./')
    #     F.generateHTMLReport(value)
    #
    # F.generateScenarioSetHTMLReport(E__dict)
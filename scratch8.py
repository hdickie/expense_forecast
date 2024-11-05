import ForecastHandler
import BudgetSet
import AccountSet
import MemoRuleSet
import MilestoneSet
import ForecastSet
import AccountMilestone
import pandas as pd

pd.options.mode.chained_assignment = None #apparently this warning can throw false positives???

if __name__ == '__main__':
    start_date_YYYYMMDD = '20240201'
    end_date_YYYYMMDD = '20240301'

    daily_cheap_food_amount = 10

    loan_A_pbal = 15000
    loan_A_interest = 100
    loan_A_APR = 0.06
    loan_A_min_payment = 113

    A = AccountSet.AccountSet([])
    A.createAccount('Checking', 4000, 0, 99999, 'checking')
    A.createAccount('Credit', 0, 0, 25000, 'credit', '20240107', 'compound', 0.24, 'monthly', 40, 23751.93)
    A.createAccount('Loan A', loan_A_pbal + loan_A_interest, 0, 25000, 'loan', start_date_YYYYMMDD, 'simple',
                    loan_A_APR, 'daily', loan_A_min_payment, None, loan_A_pbal, loan_A_interest)

    core_budget_set = BudgetSet.BudgetSet([])
    option_budget_set = BudgetSet.BudgetSet([])

    core_budget_set.addBudgetItem(start_date_YYYYMMDD, end_date_YYYYMMDD, 1, 'daily', daily_cheap_food_amount,'cheap food', False, False)

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

    F = ForecastHandler.ForecastHandler()

    S = ForecastSet.ForecastSet(core_budget_set, option_budget_set)


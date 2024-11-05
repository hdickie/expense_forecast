import unittest, pytest

import AccountMilestone
import AccountSet,BudgetSet,MemoRuleSet,ExpenseForecast
import pandas as pd, numpy as np
import datetime, logging
import tempfile
import BudgetItem
import CompositeMilestone
import ForecastHandler
import MemoMilestone
import MemoRule

pd.options.mode.chained_assignment = None #apparently this warning can throw false positives???
import MilestoneSet
from log_methods import log_in_color
import Account, BudgetSet, MemoRuleSet
import copy

from generate_date_sequence import generate_date_sequence


def match_p1_test_txn_checking_memo_rule_list():
    return [MemoRule.MemoRule('test txn', 'Checking', None, 1)]

def income_rule_list():
    return [MemoRule.MemoRule('.*income.*', None, 'Checking', 1)]


def non_trivial_loan(name,pbal,interest,apr):
    A = AccountSet.AccountSet([])
    A.createAccount(name=name,
                    balance=pbal + interest,
                    min_balance=0,
                    max_balance=9999,
                    account_type='loan',
                    billing_start_date_YYYYMMDD='20000102',
                    interest_type='simple',
                    apr=apr,
                    interest_cadence='daily',
                    minimum_payment=50,
                    previous_statement_balance=None,
                    current_statement_balance=None,
                    principal_balance=pbal,
                    interest_balance=interest,
                    billing_cycle_payment_balance=0,
                    end_of_previous_cycle_balance=pbal)

    return A.accounts

def credit_acct_list(curr_balance,prev_balance,apr):
    A = AccountSet.AccountSet([])
    A.createAccount(name='Credit',
                    balance=curr_balance+prev_balance,
                    min_balance=0,
                    max_balance=20000,
                    account_type='credit',
                    billing_start_date_YYYYMMDD='20000102',
                    interest_type=None,
                    apr=apr,
                    interest_cadence='monthly',
                    minimum_payment=40,
                      previous_statement_balance=prev_balance,
                    current_statement_balance=curr_balance,
                      principal_balance=None,
                      interest_balance=None,
                    billing_cycle_payment_balance=0,
                    end_of_previous_cycle_balance=prev_balance,
                      print_debug_messages=True,
                      raise_exceptions=True)
    return A.accounts


def credit_bsd12_acct_list(prev_balance,curr_balance,apr):
    A = AccountSet.AccountSet([])
    A.createAccount(name='Credit',
                    balance=curr_balance + prev_balance,
                    min_balance=0,
                    max_balance=20000,
                    account_type='credit',
                    billing_start_date_YYYYMMDD='19990112',
                    interest_type=None,
                    apr=apr,
                    interest_cadence='monthly',
                    minimum_payment=40,
                    previous_statement_balance=prev_balance,
                    current_statement_balance=curr_balance,
                    principal_balance=None,
                    interest_balance=None,
                    billing_cycle_payment_balance=0,
                    end_of_previous_cycle_balance=prev_balance,
                    print_debug_messages=True,
                    raise_exceptions=True)
    return A.accounts


def checking_acct_list(balance):
    return [Account.Account('Checking',balance,0,100000,'checking',primary_checking_ind=True)]


def txn_budget_item_once_list(amount,priority,memo,deferrable,partial_payment_allowed):
    return [BudgetItem.BudgetItem('20000102','20000102',priority,'once',amount,memo,deferrable,partial_payment_allowed)]

def credit_bsd12_w_eopc_acct_list(prev_balance,curr_balance,apr,end_of_prev_cycle_balance):
    A = AccountSet.AccountSet([])
    A.createAccount(name='Credit',
                    balance=curr_balance + prev_balance,
                    min_balance=0,
                    max_balance=20000,
                    account_type='credit',
                    billing_start_date_YYYYMMDD='19990112',
                    apr=apr,
                    interest_cadence='monthly',
                    minimum_payment=40,
                    previous_statement_balance=prev_balance,
                    current_statement_balance=curr_balance,
                    billing_cycle_payment_balance=end_of_prev_cycle_balance - prev_balance,
                    end_of_previous_cycle_balance=end_of_prev_cycle_balance,
                    print_debug_messages=True,
                    raise_exceptions=True)
    return A.accounts

if __name__ == '__main__':
    pass
    # test_name, advance_payment_amount, interest_accrued_this_cycle, prev_prev_stmt_bal, total_balance, min_payment, expected_result = ('Z_42010_1110', 200, 300, 100, 300, 0, -1)
    # print('test_name, advance_payment_amount, interest_accrued_this_cycle, prev_prev_stmt_bal, total_balance, min_payment, expected_result')
    # print(test_name, advance_payment_amount, interest_accrued_this_cycle, prev_prev_stmt_bal, total_balance, min_payment, expected_result)
    # res =  ExpenseForecast.determineMinPaymentAmount(float(advance_payment_amount),
    #                                                                            float(interest_accrued_this_cycle),
    #                                                                            float(prev_prev_stmt_bal),
    #                                                                            float(total_balance), float(min_payment))
    # print(res)





    test_description,account_set,budget_set,memo_rule_set,start_date_YYYYMMDD,end_date_YYYYMMDD,milestone_set,expected_result_df = ('test_p7__additional_loan_payment__amt_560',
         AccountSet.AccountSet(
             checking_acct_list(5000) + non_trivial_loan('Loan A', 1000, 100, 0.1) + non_trivial_loan('Loan B', 1000,
                                                                                                      100,
                                                                                                      0.05) + non_trivial_loan(
                 'Loan C', 1000, 100, 0.01)),
         BudgetSet.BudgetSet(
             [BudgetItem.BudgetItem('20000102', '20000102', 7, 'once', 560, 'additional_loan_payment')]),
         MemoRuleSet.MemoRuleSet([
             MemoRule.MemoRule('.*', 'Checking', None, 1),
             MemoRule.MemoRule('additional_loan_payment', 'Checking', 'ALL_LOANS', 7)
         ]),
         '20000101',
         '20000103',
         MilestoneSet.MilestoneSet( [], [], []),
         pd.DataFrame({
             'Date': ['20000101', '20000102', '20000103'],
             'Checking': [5000, 5000 - 150 - 560, 5000 - 150 - 560],
             'Loan A: Principal Balance': [1000, 496.89 , 496.89 ],
             'Loan A: Interest': [100, 0, 0.14],
             'Loan A: Loan Billing Cycle Payment Bal': [0, 503.11 + 50.27, 503.11 + 50.27],
             'Loan A: Loan End of Prev Cycle Bal': [1000, 1000, 1000],
             'Loan B: Principal Balance': [1000, 1000, 1000],
             'Loan B: Interest': [100, 43.52, 43.66],
             'Loan B: Loan Billing Cycle Payment Bal': [0, 6.62, 6.62],
             'Loan B: Loan End of Prev Cycle Bal': [1000, 1000, 1000],
             'Loan C: Principal Balance': [1000, 1000, 1000],
             'Loan C: Interest': [ 100, 50.03, 50.06 ],
             'Loan C: Loan Billing Cycle Payment Bal': [0, 0, 0],
             'Loan C: Loan End of Prev Cycle Bal': [1000, 1000, 1000],
             'Marginal Interest': [0, 0.44, 0.31],
             'Net Gain': [0, 0, 0],
             'Net Loss': [0, 0.44, 0.31],
             'Net Worth': [1700, 1699.56, 1699.25],
             'Loan Total': [3300, 2590.44, 2590.75],
             'CC Debt Total': [0, 0, 0],
             'Liquid Total': [5000, 5000 - 150 - 560, 5000 - 150 - 560],
             'Next Income Date': ['', '', ''],
                                  'Memo Directives': ['', 'LOAN MIN PAYMENT (Loan A: Interest -$50.00); LOAN MIN PAYMENT (Checking -$50.00); LOAN MIN PAYMENT (Loan B: Interest -$50.00); LOAN MIN PAYMENT (Checking -$50.00); LOAN MIN PAYMENT (Loan C: Interest -$50.00); LOAN MIN PAYMENT (Checking -$50.00); ADDTL LOAN PAYMENT (Checking -$503.11); ADDTL LOAN PAYMENT (Loan A: Principal Balance -$503.11); ADDTL LOAN PAYMENT (Checking -$50.27); ADDTL LOAN PAYMENT (Loan A: Interest -$50.27); ADDTL LOAN PAYMENT (Checking -$6.62); ADDTL LOAN PAYMENT (Loan B: Interest -$6.62)', ''],
             'Memo': ['', '', '']
         })
         )

    E = ExpenseForecast.ExpenseForecast(account_set, budget_set,
                                        memo_rule_set,
                                        start_date_YYYYMMDD,
                                        end_date_YYYYMMDD,
                                        milestone_set,
                                        raise_exceptions=False)

    E.runForecast(log_level='DEBUG')
    #print(E.forecast_df.to_string())
    #
    # # def sync_account_set_w_forecast_day(account_set, forecast_df, date_YYYYMMDD):
    # #
    # #     Accounts_df = account_set.getAccounts()
    # #
    # #     relevant_forecast_day = forecast_df[forecast_df.Date == date_YYYYMMDD]
    # #     # print('relevant_forecast_day:')
    # #     # print(relevant_forecast_day)
    # #
    # #     row_sel_vec = (forecast_df.Date == date_YYYYMMDD)
    # #     try:
    # #         assert sum(row_sel_vec) > 0
    # #     except Exception as e:
    # #         error_msg = "error in sync_account_set_w_forecast_day\n"
    # #         error_msg += "date_YYYYMMDD: " + date_YYYYMMDD + "\n"
    # #         error_msg += "min date of forecast:" + min(forecast_df.Date) + "\n"
    # #         error_msg += "max date of forecast:" + max(forecast_df.Date) + "\n"
    # #         raise AssertionError(error_msg)
    # #
    # #     # print('Accounts_df.shape:' + str(Accounts_df.shape))
    # #
    # #     for account_index in range(1, (1 + Accounts_df.shape[0])):
    # #         account_index = int(account_index)
    # #         # print('account_index: ' + str(account_index))
    # #         relevant_balance = relevant_forecast_day.iat[0, account_index]
    # #         # print('relevant_balance: ' + str(relevant_balance))
    # #         account_set.accounts[account_index - 1].balance = round(relevant_balance, 2)
    # #
    # #     return account_set
    # #
    # #
    # # forecast_w_check_only_A = pd.DataFrame(
    # #     {'Date': ['20000101', '20000102'], 'test checking': [0, 0], 'Memo': ['', ''], 'Memo Directives': ['', '']})
    # # forecast_w_check_and_credit_B = pd.DataFrame(
    # #     {'Date': ['20000101', '20000102'], 'test checking': [0, 0], 'test credit: Prev Stmt Bal': [0, 0], 'test credit: Curr Stmt Bal': [0, 0], 'test credit: Credit Billing Cycle Payment Bal': [0, 0], 'test credit: Credit End of Prev Cycle Bal': [0, 0], 'Memo': ['', ''], 'Memo Directives': ['', '']})
    # # forecast_w_check_and_loan_C = pd.DataFrame(
    # #     {'Date': ['20000101', '20000102'], 'test checking': [0, 0], 'test loan: Principal Balance': [0, 0], 'test loan: Interest': [0, 0], 'test credit: Loan Billing Cycle Payment Bal': [0, 0], 'test credit: Loan End of Prev Cycle Bal': [0, 0], 'Memo': ['', ''], 'Memo Directives': ['', '']})
    # #
    # # A1 = AccountSet.AccountSet([])
    # # A2 = AccountSet.AccountSet([])
    # # B1 = AccountSet.AccountSet([])
    # # B2 = AccountSet.AccountSet([])
    # # C1 = AccountSet.AccountSet([])
    # # C2 = AccountSet.AccountSet([])
    # #
    # # A1.createAccount(name="test checking",
    # #                  balance=1000.0,
    # #                  min_balance=0.0,
    # #                  max_balance=float('inf'),
    # #                  account_type='checking',
    # #                  billing_start_date_YYYYMMDD=None,
    # #                  interest_type=None,
    # #                  apr=None,
    # #                  interest_cadence=None,
    # #                  minimum_payment=None,
    # #                  previous_statement_balance=None,
    # #                  principal_balance=None,
    # #                  interest_balance=None,
    # #                  billing_cycle_payment_balance=0,
    # #                  print_debug_messages=False)
    # #
    # # A2.createAccount(name="test checking",
    # #                  balance=999.0,
    # #                  min_balance=0.0,
    # #                  max_balance=float('inf'),
    # #                  account_type='checking',
    # #                  billing_start_date_YYYYMMDD=None,
    # #                  interest_type=None,
    # #                  apr=None,
    # #                  interest_cadence=None,
    # #                  minimum_payment=None,
    # #                  previous_statement_balance=None,
    # #                  principal_balance=None,
    # #                  interest_balance=None,
    # #                  billing_cycle_payment_balance=0,
    # #                  print_debug_messages=False)
    # #
    # # B1.createAccount(name="test checking",
    # #                  balance=1000.0,
    # #                  min_balance=0.0,
    # #                  max_balance=float('inf'),
    # #                  account_type='checking',
    # #                  billing_start_date_YYYYMMDD=None,
    # #                  interest_type=None,
    # #                  apr=None,
    # #                  interest_cadence=None,
    # #                  minimum_payment=None,
    # #                  previous_statement_balance=None,
    # #                  principal_balance=None,
    # #                  interest_balance=None,
    # #                  billing_cycle_payment_balance=0,
    # #                  print_debug_messages=False)
    # #
    # # B2.createAccount(name="test checking",
    # #                  balance=999.0,
    # #                  min_balance=0.0,
    # #                  max_balance=float('inf'),
    # #                  account_type='checking',
    # #                  billing_start_date_YYYYMMDD=None,
    # #                  interest_type=None,
    # #                  apr=None,
    # #                  interest_cadence=None,
    # #                  minimum_payment=None,
    # #                  previous_statement_balance=None,
    # #                  principal_balance=None,
    # #                  interest_balance=None,
    # #                  billing_cycle_payment_balance=0,
    # #                  print_debug_messages=False)
    # #
    # # B1.createAccount(name="test credit",
    # #                  balance=1500.0,
    # #                  min_balance=0.0,
    # #                  max_balance=20000.0,
    # #                  account_type='credit',
    # #                  billing_start_date_YYYYMMDD='20000107',
    # #                  interest_type=None,
    # #                  apr=0.2479,
    # #                  interest_cadence='monthly',
    # #                  minimum_payment=20.0,
    # #                  previous_statement_balance=500.0,
    # #                  current_statement_balance=1000.0,
    # #                  principal_balance=None,
    # #                  interest_balance=None,
    # #                  billing_cycle_payment_balance=0,
    # #                  end_of_previous_cycle_balance=500.0,
    # #                  print_debug_messages=False)
    # #
    # # B2.createAccount(name="test credit",
    # #                  balance=1000.0,
    # #                  min_balance=0.0,
    # #                  max_balance=20000.0,
    # #                  account_type='credit',
    # #                  billing_start_date_YYYYMMDD='20000107',
    # #                  interest_type=None,
    # #                  apr=0.2479,
    # #                  interest_cadence='monthly',
    # #                  minimum_payment=20.0,
    # #                  previous_statement_balance=250.0,
    # #                  current_statement_balance=750.0,
    # #                  principal_balance=None,
    # #                  interest_balance=None,
    # #                  billing_cycle_payment_balance=0,
    # #                  end_of_previous_cycle_balance=500.0,
    # #                  print_debug_messages=False)
    # #
    # # C1.createAccount(name="test checking",
    # #                  balance=1000.0,
    # #                  min_balance=0.0,
    # #                  max_balance=float('inf'),
    # #                  account_type='checking',
    # #                  billing_start_date_YYYYMMDD=None,
    # #                  interest_type=None,
    # #                  apr=None,
    # #                  interest_cadence=None,
    # #                  minimum_payment=None,
    # #                  previous_statement_balance=None,
    # #                  principal_balance=None,
    # #                  interest_balance=None,
    # #                  billing_cycle_payment_balance=0,
    # #                  print_debug_messages=False)
    # #
    # # C2.createAccount(name="test checking",
    # #                  balance=999.0,
    # #                  min_balance=0.0,
    # #                  max_balance=float('inf'),
    # #                  account_type='checking',
    # #                  billing_start_date_YYYYMMDD=None,
    # #                  interest_type=None,
    # #                  apr=None,
    # #                  interest_cadence=None,
    # #                  minimum_payment=None,
    # #                  previous_statement_balance=None,
    # #                  principal_balance=None,
    # #                  interest_balance=None,
    # #                  billing_cycle_payment_balance=0,
    # #                  print_debug_messages=False)
    # #
    # # C1.createAccount(name="test loan",
    # #                  balance=1500.0,
    # #                  min_balance=0,
    # #                  max_balance=26000.0,
    # #                  account_type='loan',
    # #                  billing_start_date_YYYYMMDD='20230303',
    # #                  interest_type='simple',
    # #                  apr=0.067,
    # #                  interest_cadence='daily',
    # #                  minimum_payment='223.19',
    # #                  previous_statement_balance=None,
    # #                  principal_balance=1100.0,
    # #                  interest_balance=400.0,
    # #                  billing_cycle_payment_balance=0,
    # #                  end_of_previous_cycle_balance=900,
    # #                  print_debug_messages=False)
    # #
    # # C2.createAccount(name="test loan",
    # #                  balance=1000.0,
    # #                  min_balance=0,
    # #                  max_balance=26000.0,
    # #                  account_type='loan',
    # #                  billing_start_date_YYYYMMDD='20230303',
    # #                  interest_type='simple',
    # #                  apr=0.067,
    # #                  interest_cadence='daily',
    # #                  minimum_payment='223.19',
    # #                  previous_statement_balance=None,
    # #                  principal_balance=850.0,
    # #                  interest_balance=150.0,
    # #                  billing_cycle_payment_balance=0,
    # #                  end_of_previous_cycle_balance=900,
    # #                  print_debug_messages=False)
    # #
    # # # sync_account_set_w_forecast_day(account_set, forecast_df, date_YYYYMMDD)
    # # print('A1:')
    # # print(A1.getAccounts().to_string())
    # # result_A_1 = sync_account_set_w_forecast_day(A1, forecast_w_check_only_A, '20000101')
    # # print('result_A_1:')
    # # print(result_A_1.getAccounts().to_string())
    # # print('##############################')
    # # print('B1:')
    # # print(B1.getAccounts().to_string())
    # # result_B_1 = sync_account_set_w_forecast_day(B1, forecast_w_check_and_credit_B, '20000101')
    # # print('result_B_1:')
    # # print(result_B_1.getAccounts().to_string())
    # # print('##############################')
    # # print('C1:')
    # # print(C1.getAccounts().to_string())
    # # result_C_1 = sync_account_set_w_forecast_day(C1, forecast_w_check_and_loan_C, '20000101')
    # # print('result_C_1:')
    # # print(result_C_1.getAccounts().to_string())

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
    test_name, advance_payment_amount, interest_accrued_this_cycle, prev_prev_stmt_bal, total_balance, min_payment, expected_result = ('21100_0111', '300', '100', '100', '200', '400', '-1')
    print('test_name, advance_payment_amount, interest_accrued_this_cycle, prev_prev_stmt_bal, total_balance, min_payment, expected_result')
    print(test_name, advance_payment_amount, interest_accrued_this_cycle, prev_prev_stmt_bal, total_balance, min_payment, expected_result)
    assert float(expected_result) == ExpenseForecast.determineMinPaymentAmount(float(advance_payment_amount),
                                                                               float(interest_accrued_this_cycle),
                                                                               float(prev_prev_stmt_bal),
                                                                               float(total_balance), float(min_payment))

    # Ok, new plan for test_determineMinPaymentAmount
    # The number of possible cases for this 6!, but even more since some of them can be equal
    # I guess we could multiply those separately actually
    # There are 5 spots where < or <= could go, so 2^5
    # So there are 6!*2^5 or 23040 possible cases here
    # So, to generate unique test cases, I could represent them with 2 strings:
    # One for the order, with the max choice for each decending by one. e.g. 543210 or 000000
    # the first is the reverse of the input list, and the second is input list returned unchanged
    # the second string is a binary string of 5 used for the choice of <= or <
    #
    # Randomly generating numbers for the test cases!!!

    # import math
    # import random
    #
    # num_unique_test_cases_desired = 30
    # num_of_monotonic_orderings = 5*4*3*2
    # num_of_possible_relationships = 2**4
    # test_definition_tuples = []
    # for i in range(0,num_unique_test_cases_desired):
    #     o = math.floor(random.random() * num_of_monotonic_orderings)
    #     r = math.floor(random.random() * num_of_possible_relationships)
    #
    #     og_o = o
    #     og_r = r
    #     #
    #     # first_element = o % 6
    #     # o = math.floor(o / 6)
    #
    #     second_element = o % 5
    #     o = math.floor(o / 5)
    #
    #     third_element = o % 4
    #     o = math.floor(o / 4)
    #
    #     fourth_element = o % 3
    #     o = math.floor(o / 3)
    #
    #     fifth_element = o % 2
    #     o = math.floor(o / 2)
    #
    #     sixth_element = o
    #     element_order = str(second_element) + str(third_element) + str(fourth_element) + str(fifth_element) + str(sixth_element)
    #     assert sixth_element == 0
    #
    #     # first_relationship = r % 2
    #     # r = math.floor(r / 2)
    #
    #     second_relationship = r % 2
    #     r = math.floor(r / 2)
    #
    #     third_relationship = r % 2
    #     r = math.floor(r / 2)
    #
    #     fourth_relationship = r % 2
    #     r = math.floor(r / 2)
    #
    #     fifth_relationship = r % 2
    #     r = math.floor(r / 2)
    #     assert r == 0 or r == 1
    #
    #     relationships = str(second_relationship)+str(third_relationship)+str(fourth_relationship)+str(fifth_relationship)
    #
    #     #print(element_order,relationships)
    #     test_definition_tuples.append((element_order,relationships))
    #
    # #
    # og_param_list = ['advance_payment_amount','interest_accrued_this_cycle','og_principal_due_this_cycle','total_balance','min_payment']
    # test_name_and_def = {}
    # for test_tuple in test_definition_tuples:
    #     test_value_dict = {}
    #     param_list = og_param_list.copy()
    #     amount = 100
    #     for i in range(0,5):
    #         c = int(test_tuple[0][i])
    #         current_param_name = param_list.pop(int(c))
    #         test_value_dict[current_param_name] = amount
    #         if i == 4:
    #             pass
    #         elif int(test_tuple[1][i]) == 1:
    #             amount += 100
    #
    #     test_name_and_def[test_tuple] = test_value_dict
    #
    # # ['advance_payment_amount','interest_accrued_this_cycle','og_principal_due_this_cycle','prev_stmt_bal','curr_stmt_bal','min_payment']
    # for k, v in test_name_and_def.items():
    #     pass
    #     print("('"+k[0]+'_'+k[1]+"','"+str(v['advance_payment_amount'])+"','"+str(v['interest_accrued_this_cycle'])+"','"+str(v['og_principal_due_this_cycle'])+"','"+str(v['total_balance'])+"','"+str(v['min_payment'])+"','RESULT INT'),")
    #     #print(k[0]+'_'+k[1],v['advance_payment_amount'],v['interest_accrued_this_cycle'],v['og_principal_due_this_cycle'],v['prev_stmt_bal'],v['curr_stmt_bal'],v['min_payment'])

    # test_description,account_set,budget_set,memo_rule_set,start_date_YYYYMMDD,end_date_YYYYMMDD,milestone_set,expected_result_df = ('test_cc_interest_accrued_reaches_0',
    #      AccountSet.AccountSet(checking_acct_list(500) + credit_bsd12_w_eopc_acct_list(0, 0, 0.05, 35)),  # todo implement
    #      #BudgetSet.BudgetSet([BudgetItem.BudgetItem('20000112', '20000112', 2, 'once', 600, 'pay cc interest accrued on due date', False, False)]),
    #      BudgetSet.BudgetSet(),
    #      MemoRuleSet.MemoRuleSet([
    #          MemoRule.MemoRule('.*', 'Checking', None, 1),
    #          MemoRule.MemoRule('.*', 'Checking', 'Credit', 2)
    #      ]),
    #      '20000110',
    #      '20000214',
    #      MilestoneSet.MilestoneSet([], [], []),
    #      pd.DataFrame({
    #          'Date': generate_date_sequence('20000110', 35, 'daily'),
    #          'Checking': [0] * 36,
    #          'Credit: Curr Stmt Bal': [0] * 36,
    #          'Credit: Prev Stmt Bal': [0] * 36,
    #          'Credit: Credit Billing Cycle Payment Bal': [0] * 36,
    #          'Credit: Credit End of Prev Cycle Bal': [0] * 36,
    #          'Marginal Interest': [0] * 36,
    #          'Net Gain': [0] * 36,
    #          'Net Loss': [0] * 36,
    #          'Net Worth': [0] * 36,
    #          'Loan Total': [0] * 36,
    #          'CC Debt Total': [0] * 36,
    #          'Liquid Total': [0] * 36,
    #          'Next Income Date': [''] * 36,
    #          'Memo Directives': ['NOT IMPLEMENTED'] * 36,
    #          'Memo': [''] * 36
    #      })
    #      )
    #
    # E = ExpenseForecast.ExpenseForecast(account_set, budget_set,
    #                                     memo_rule_set,
    #                                     start_date_YYYYMMDD,
    #                                     end_date_YYYYMMDD,
    #                                     milestone_set,
    #                                     raise_exceptions=False)
    #
    # E.runForecast(log_level='DEBUG')
    # #print(E.forecast_df.to_string())
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

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
                    billing_cycle_payment_balance=0)

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
                    print_debug_messages=True,
                    raise_exceptions=True)
    return A.accounts


def checking_acct_list(balance):
    return [Account.Account('Checking',balance,0,100000,'checking',primary_checking_ind=True)]


def txn_budget_item_once_list(amount,priority,memo,deferrable,partial_payment_allowed):
    return [BudgetItem.BudgetItem('20000102','20000102',priority,'once',amount,memo,deferrable,partial_payment_allowed)]


if __name__ == '__main__':
    test_description,account_set,budget_set,memo_rule_set,start_date_YYYYMMDD,end_date_YYYYMMDD,milestone_set,expected_result_df = ('test_cc_single_additional_payment_day_before',
         AccountSet.AccountSet(checking_acct_list(5000) + credit_bsd12_acct_list(500, 500, 0.05)),
         BudgetSet.BudgetSet([BudgetItem.BudgetItem('20000111', '20000111', 2, 'once', 600,
                                                    'single additional payment day before due date', False, False)]),
         MemoRuleSet.MemoRuleSet([
             MemoRule.MemoRule('.*', 'Checking', None, 1),
             MemoRule.MemoRule('.*', 'Checking', 'Credit', 2)
         ]),
         '20000110',
         '20000112',
         MilestoneSet.MilestoneSet([], [], []),
         pd.DataFrame({
             'Date': ['20000110', '20000111', '20000112'],
             'Checking': [5000, 5000, 4400],
             'Credit: Curr Stmt Bal': [500, 0, 0],
             'Credit: Prev Stmt Bal': [500, 400, 402.08],
             'Credit: Credit Billing Cycle Payment Bal': [0, 600, 0],
             'Marginal Interest': [0, 0, 2.08],
             'Net Gain': [0, 0, 0],
             'Net Loss': [0, 0, 2.08],
             'Net Worth': [4000, 4000, 3997.92],
             'Loan Total': [0, 0, 0],
             'CC Debt Total': [1000, 400, 402.08],
             'Liquid Total': [5000, 4400.0, 4400.0],
             'Memo Directives': ['',
                                 'ADDTL CC PAYMENT (Checking -$600.00); ADDTL CC PAYMENT (Credit: Prev Stmt Bal -$600.00)',
                                 'CC MIN PAYMENT ALREADY MADE (Checking -$0.00); CC MIN PAYMENT ALREADY MADE (Credit: Prev Stmt Bal -$0.00); CC INTEREST (Credit: Prev Stmt Bal +$2.08)'],
             'Memo': ['', 'single additional payment day before due date (Checking -$600.00)', '']
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
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
                    interest_balance=interest)

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
                    billing_start_date_YYYYMMDD='20000112',
                    interest_type=None,
                    apr=apr,
                    interest_cadence='monthly',
                    minimum_payment=40,
                    previous_statement_balance=prev_balance,
                    current_statement_balance=curr_balance,
                    principal_balance=None,
                    interest_balance=None,
                    print_debug_messages=True,
                    raise_exceptions=True)
    return A.accounts


def checking_acct_list(balance):
    return [Account.Account('Checking',balance,0,100000,'checking',primary_checking_ind=True)]


def txn_budget_item_once_list(amount,priority,memo,deferrable,partial_payment_allowed):
    return [BudgetItem.BudgetItem('20000102','20000102',priority,'once',amount,memo,deferrable,partial_payment_allowed)]


if __name__ == '__main__':
    test_description,account_set,budget_set,memo_rule_set,start_date_YYYYMMDD,end_date_YYYYMMDD,milestone_set,expected_result_df = ( 'test_p7__additional_loan_payment__amt_10',
                AccountSet.AccountSet(checking_acct_list(5000) + non_trivial_loan('Loan A',1000,100,0.1) + non_trivial_loan('Loan B',1000,100,0.05) + non_trivial_loan('Loan C',1000,100,0.01)),
                BudgetSet.BudgetSet([BudgetItem.BudgetItem('20000102','20000102',7,'once',10,'additional_loan_payment')]),
                MemoRuleSet.MemoRuleSet([
                    MemoRule.MemoRule('.*','Checking',None,1),
                    MemoRule.MemoRule('additional_loan_payment','Checking','ALL_LOANS',7)
                ]),
                '20000101',
                '20000103',
                MilestoneSet.MilestoneSet( [], [], []),
                pd.DataFrame({
                    'Date': ['20000101', '20000102', '20000103'],
                    'Checking': [5000, 4840, 4840],
                    'Loan A: Principal Balance': [1000, 1000, 1000],
                    'Loan A: Interest': [100, 40.27, 40.54],
                    'Loan B: Principal Balance': [1000, 1000, 1000],
                    'Loan B: Interest': [100, 50.14, 50.28],
                    'Loan C: Principal Balance': [1000, 1000, 1000],
                    'Loan C: Interest': [100, 50.03, 50.06],
                    'Marginal Interest': [0, 0.44, 0.44],
                    'Net Gain': [0, 0, 0],
                    'Net Loss': [0, 0, 0],
                    'Net Worth': [1700, 1699.56, 1699.12],
                    'Loan Total': [3300, 3140.44, 3140.88],
                    'CC Debt Total': [0, 0, 0],
                    'Liquid Total': [5000, 4840, 4840],
                                  'Memo Directives': ['', 'LOAN MIN PAYMENT (Loan A: Interest -$50.00); LOAN MIN PAYMENT (Checking -$50.00); LOAN MIN PAYMENT (Loan B: Interest -$50.00); LOAN MIN PAYMENT (Checking -$50.00); LOAN MIN PAYMENT (Loan C: Interest -$50.00); LOAN MIN PAYMENT (Checking -$50.00); ADDTL LOAN PAYMENT (Checking -$10.00); ADDTL LOAN PAYMENT (Loan A: Interest -$10.00)', ''],
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
    print(E.forecast_df.to_string())
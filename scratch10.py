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


if __name__ == '__main__':
    test_description,account_set,budget_set,memo_rule_set,start_date_YYYYMMDD,end_date_YYYYMMDD,milestone_set,expected_result_df = (
                'test_p2_and_3__p3_item_skipped_bc_p2',
                AccountSet.AccountSet(checking_acct_list(100)),
                BudgetSet.BudgetSet(txn_budget_item_once_list(100, 2, 'this should be executed', False, False) + txn_budget_item_once_list(100, 3, 'this should be skipped', False, False)),
                MemoRuleSet.MemoRuleSet([MemoRule.MemoRule(memo_regex='.*', account_from='Checking', account_to=None,
                                                           transaction_priority=1),
                                         MemoRule.MemoRule(memo_regex='.*', account_from='Checking', account_to=None,
                                                           transaction_priority=2),
                                         MemoRule.MemoRule(memo_regex='.*', account_from='Checking', account_to=None,
                                                           transaction_priority=3)
                                         ]),
                '20000101',
                '20000103',
                MilestoneSet.MilestoneSet( [], [], []),
                pd.DataFrame({
                    'Date': ['20000101', '20000102', '20000103'],
                    'Checking': [100, 0, 0],
                    'Marginal Interest': [0, 0, 0],
                    'Net Gain': [0, 0, 0],
                    'Net Loss': [0, 100, 0],
                    'Net Worth': [100, 0, 0],
                    'Loan Total': [0, 0, 0],
                    'CC Debt Total': [0, 0, 0],
                    'Liquid Total': [100, 0, 0],
                                  'Memo Directives': ['', '', ''],
                    'Memo': ['', 'this should be executed (Checking -$100.00)', '']
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
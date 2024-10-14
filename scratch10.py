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
    test_description,account_set,budget_set,memo_rule_set,start_date_YYYYMMDD,end_date_YYYYMMDD,milestone_set,expected_result_df = (
                'test_execute_defer_after_receiving_income_2_days_later',
                AccountSet.AccountSet(checking_acct_list(500)),
                BudgetSet.BudgetSet([
                                     BudgetItem.BudgetItem('20000102','20000102',1,'once',100,'SPEND daily p1 txn', False,False), #EOD 400

                                     BudgetItem.BudgetItem('20000103', '20000103', 1, 'once', 100, 'SPEND daily p1 txn 2',False, False), #EOD 300
                                     BudgetItem.BudgetItem('20000103', '20000103', 3, 'once', 400,'SPEND p3 txn on 1/3 that is skipped bc later lower priority_index txn', False, False),

                                     BudgetItem.BudgetItem('20000104', '20000104', 1, 'once', 200, '200 income on 1/4',False, False), #500
                                     BudgetItem.BudgetItem('20000104', '20000104', 1, 'once', 100, 'SPEND daily p1 txn 3',False, False), #400
                                     BudgetItem.BudgetItem('20000102', '20000102', 2, 'once', 400, 'SPEND p2 txn deferred from 1/2 to 1/4', True, False) #EOD 0

                                     ]
                                    ),
                MemoRuleSet.MemoRuleSet([MemoRule.MemoRule(memo_regex='SPEND.*',
                                                           account_from='Checking',
                                                           account_to=None,
                                                           transaction_priority=1),
                                         MemoRule.MemoRule(memo_regex='.*income.*',
                                                           account_from=None,
                                                           account_to='Checking',
                                                           transaction_priority=1),
                                         MemoRule.MemoRule(memo_regex='SPEND.*',
                                                           account_from='Checking',
                                                           account_to=None,
                                                           transaction_priority=2),
                                         MemoRule.MemoRule(memo_regex='SPEND.*',
                                                           account_from='Checking',
                                                           account_to=None,
                                                           transaction_priority=3)
                                         ]),
                '20000101',
                '20000104', #note that this is later than the test defined above
                MilestoneSet.MilestoneSet( [], [], []),
                pd.DataFrame({
                    'Date': ['20000101', '20000102', '20000103', '20000104'],
                    'Checking': [500, 400, 300, 0],
                    'Marginal Interest': [0, 0, 0, 0],
                    'Net Gain': [0, 0, 0, 0],
                    'Net Loss': [0, 100, 100, 300],
                    'Net Worth': [500, 400, 300, 0],
                    'Loan Total': [0, 0, 0, 0],
                    'CC Debt Total': [0, 0, 0, 0],
                    'Liquid Total': [500, 400, 300, 0],
                                  'Memo Directives': ['', '', '',''],
                    'Memo': ['', 'SPEND daily p1 txn (Checking -$100.00)',
                             'SPEND daily p1 txn 2 (Checking -$100.00)',
                             '200 income on 1/4 (Checking +$200.00); SPEND daily p1 txn 3 (Checking -$100.00); SPEND p2 txn deferred from 1/2 to 1/4 (Checking -$400.00)']
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
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
                                'test_cc_payment__satisfice__curr_bal_25__expect_0',
                                AccountSet.AccountSet(checking_acct_list(2000) + credit_acct_list(25, 0, 0.05)),
                                BudgetSet.BudgetSet([]),
                                MemoRuleSet.MemoRuleSet([MemoRule.MemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=1)]),
                                '20000101',
                                '20000103',
                                MilestoneSet.MilestoneSet( [], [], []),
                                pd.DataFrame({
                                    'Date': ['20000101', '20000102', '20000103'],
                                    'Checking': [2000, 2000, 2000],
                                    'Credit: Curr Stmt Bal': [25, 0, 0],
                                    'Credit: Prev Stmt Bal': [0, 25, 25],
                                    'Marginal Interest': [0, 0, 0],
                                    'Net Gain': [0, 0, 0],
                                    'Net Loss': [0, 0, 0],
                                    'Net Worth': [1975, 1975, 1975],
                                    'Loan Total': [0, 0, 0],
                                    'CC Debt Total': [25, 25, 25],
                                    'Liquid Total': [2000, 2000, 2000],
                                  'Memo Directives': ['', '', ''],
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
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
from log_methods import setup_logger
logger = setup_logger('test_ExpenseForecast', './log/test_ExpenseForecast.log', level=logging.DEBUG)

from log_methods import display_test_result

def checking_acct_list(balance):
    return [Account.Account('Checking',balance,0,100000,'checking',primary_checking_ind=True)]

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

def txn_budget_item_once_list(amount,priority,memo,deferrable,partial_payment_allowed):
    return [BudgetItem.BudgetItem('20000102','20000102',priority,'once',amount,memo,deferrable,partial_payment_allowed)]

def match_all_p1_checking_memo_rule_list():
    return [MemoRule.MemoRule('.*','Checking',None,1)]

def match_p1_test_txn_checking_memo_rule_list():
    return [MemoRule.MemoRule('test txn', 'Checking', None, 1)]

def match_p1_test_txn_credit_memo_rule_list():
    return [MemoRule.MemoRule('test txn', 'Credit', None, 1)]

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
                    interest_balance=interest)

    return A.accounts

class TestExpenseForecastMethods:

    @pytest.mark.parametrize('account_set,budget_set,memo_rule_set,start_date_YYYYMMDD,end_date_YYYYMMDD,milestone_set',

                             [(AccountSet.AccountSet(checking_acct_list(10)),
                              BudgetSet.BudgetSet(txn_budget_item_once_list(10,1,'test txn',False,False)),
                              MemoRuleSet.MemoRuleSet(match_p1_test_txn_checking_memo_rule_list()),
                              '19991231',
                              '20000101',
                              MilestoneSet.MilestoneSet(
                                  [],
                                  [],
                                  []),
                              )

                             # (AccountSet.AccountSet([]),
                             #  BudgetSet.BudgetSet([]),
                             #  MemoRuleSet.MemoRuleSet([]),
                             #  start_date_YYYYMMDD,
                             #  end_date_YYYYMMDD,
                             #  MilestoneSet.MilestoneSet([])
                             #  ),

                             ])
    def test_ExpenseForecast_Constructor__valid_inputs(self,account_set,budget_set,memo_rule_set,start_date_YYYYMMDD,end_date_YYYYMMDD,milestone_set):
        ExpenseForecast.ExpenseForecast(account_set,
                                        budget_set,
                                        memo_rule_set,
                                        start_date_YYYYMMDD,
                                        end_date_YYYYMMDD,
                                        milestone_set,
                                        print_debug_messages=False)

    @pytest.mark.parametrize('account_set,budget_set,memo_rule_set,start_date_YYYYMMDD,end_date_YYYYMMDD,milestone_set,expected_exception',

                             [
                                 (AccountSet.AccountSet([]),
                                  BudgetSet.BudgetSet([]),
                                  MemoRuleSet.MemoRuleSet([]),
                                  'incorrect date format',
                                  '20000103',
                                  MilestoneSet.MilestoneSet(
                                      [],
                                      [],
                                      []),
                                  ValueError
                                  ),  # malformed start date

                                 (AccountSet.AccountSet([]),
                                  BudgetSet.BudgetSet([]),
                                  MemoRuleSet.MemoRuleSet([]),
                                  '20000101',
                                  'incorrect date format',
                                  MilestoneSet.MilestoneSet(
                                      [],
                                      [],
                                      []),
                                  ValueError
                                  ),  # malformed end date

                                 (AccountSet.AccountSet([]),
                              BudgetSet.BudgetSet([]),
                              MemoRuleSet.MemoRuleSet([]),
                              '20000101',
                              '19991231',
                              MilestoneSet.MilestoneSet(
                                [],
                                [],
                              []),
                              ValueError
                              ),  #end date before start date

                              (AccountSet.AccountSet([]),
                               BudgetSet.BudgetSet([]),
                               MemoRuleSet.MemoRuleSet([]),
                               '19991231',
                               '20000101',
                               MilestoneSet.MilestoneSet(
                                   [],
                                   [],
                                   []),
                               ValueError
                               ),  # empty account_set

                              (AccountSet.AccountSet(checking_acct_list(10)),
                               BudgetSet.BudgetSet(txn_budget_item_once_list(10,1,'test txn',False,False)),
                               MemoRuleSet.MemoRuleSet([]),
                               '19991231',
                               '20000101',
                               MilestoneSet.MilestoneSet(
                                   [],
                                   [],
                                   []),
                               ValueError
                               ), # A budget memo x priority element does not have a matching regex in memo rule set

                              (AccountSet.AccountSet(checking_acct_list(10)),
                               BudgetSet.BudgetSet(txn_budget_item_once_list(10,1,'test txn',False,False)),
                               MemoRuleSet.MemoRuleSet(match_p1_test_txn_credit_memo_rule_list()),
                               '19991231',
                               '20000101',
                               MilestoneSet.MilestoneSet(
                                   [],
                                   [],
                                   []),
                               ValueError
                               ),  #A memo rule has an account that does not exist in AccountSet

                              # (AccountSet.AccountSet([]),
                              #  BudgetSet.BudgetSet([]),
                              #  MemoRuleSet.MemoRuleSet([]),
                              #  'start_date_YYYYMMDD',
                              #  'end_date_YYYYMMDD',
                              #  MilestoneSet.MilestoneSet(
                              #      [],
                              #      [],
                              #      []),
                              #  ValueError
                              #  ),

                              ])
    def test_ExpenseForecast_Constructor__invalid_inputs(self,account_set,budget_set,memo_rule_set,
                                                         start_date_YYYYMMDD,end_date_YYYYMMDD,milestone_set,expected_exception):
        with pytest.raises(expected_exception):
            ExpenseForecast.ExpenseForecast(account_set,
                                        budget_set,
                                        memo_rule_set,
                                        start_date_YYYYMMDD,
                                        end_date_YYYYMMDD,
                                        milestone_set,
                                        print_debug_messages=False)


    def compute_forecast_and_actual_vs_expected(self,
                                                account_set,
                                                budget_set,
                                                memo_rule_set,
                                                start_date_YYYYMMDD,
                                                end_date_YYYYMMDD,
                                                milestone_set,
                                                expected_result_df,
                                                test_description):

        E = ExpenseForecast.ExpenseForecast(account_set, budget_set,
                                            memo_rule_set,
                                            start_date_YYYYMMDD,
                                            end_date_YYYYMMDD,
                                            milestone_set,
                                            raise_exceptions=False)

        E.runForecast()

        d = E.compute_forecast_difference(copy.deepcopy(E.forecast_df),copy.deepcopy(expected_result_df),
                                          label=test_description,
                                          make_plots=False,
                                          diffs_only=True,
                                          require_matching_columns=True,
                                          require_matching_date_range=True,
                                          append_expected_values=False,
                                          return_type='dataframe')

        f = E.compute_forecast_difference(copy.deepcopy(E.forecast_df),copy.deepcopy(expected_result_df),
                                          label=test_description,
                                          make_plots=False,
                                          diffs_only=False,
                                          require_matching_columns=True,
                                          require_matching_date_range=True,
                                          append_expected_values=True,
                                          return_type='dataframe')

        print(f.T.to_string())

        try:
            log_in_color(logger, 'white', 'debug', '###################################')
            log_in_color(logger, 'white', 'debug', f.to_string())
            log_in_color(logger, 'white', 'debug','###################################')
            log_in_color(logger,'white','debug',f.T.to_string())
            log_in_color(logger, 'white', 'debug', '###################################')
            display_test_result(logger,test_description, d)
        except Exception as e:
            raise e

        try:
            sel_vec = (d.columns != 'Date') & (d.columns != 'Memo')

            #non_boilerplate_values__M = np.matrix(d.iloc[:, sel_vec])
            non_boilerplate_values__M = np.array(d.iloc[:, sel_vec])
            non_boilerplate_values__M = non_boilerplate_values__M[:,None]

            error_ind = round(float(sum(sum(np.square(
                non_boilerplate_values__M)).T)),2)  # this very much DOES NOT SCALE. this is intended for small tests
            assert error_ind == 0

            try:
                for i in range(0,expected_result_df.shape[0]):
                    assert expected_result_df.loc[i,'Memo'].strip() == E.forecast_df.loc[i,'Memo'].strip()
            except Exception as e:
                log_in_color(logger,'red','error','Forecasts matched but the memo did not')
                date_memo1_memo2_df = pd.DataFrame()
                date_memo1_memo2_df['Date'] = expected_result_df.Date
                date_memo1_memo2_df['Expected_Memo'] = expected_result_df.Memo
                date_memo1_memo2_df['Actual_Memo'] = E.forecast_df.Memo
                log_in_color(logger,'red', 'error', date_memo1_memo2_df.to_string())
                raise e


        except Exception as e:
            # print(test_description) #todo use log methods
            # print(f.T.to_string())
            raise e

        return E

    @pytest.mark.parametrize('test_description,account_set,budget_set,memo_rule_set,start_date_YYYYMMDD,end_date_YYYYMMDD,milestone_set,expected_result_df',[
                             (
                              'test_p1_only_no_budget_items',
                              AccountSet.AccountSet(checking_acct_list(0) + credit_acct_list(0,0,0.05)),
                              BudgetSet.BudgetSet([]),
                              MemoRuleSet.MemoRuleSet(match_p1_test_txn_checking_memo_rule_list()),
                              '20000101',
                              '20000103',
                              MilestoneSet.MilestoneSet([],[],[]),
                              pd.DataFrame({
                                  'Date': ['20000101', '20000102', '20000103'],
                                  'Checking': [0, 0, 0],
                                  'Credit: Curr Stmt Bal': [0, 0, 0],
                                  'Credit: Prev Stmt Bal': [0, 0, 0],
                                  'Marginal Interest': [0, 0, 0],
                                  'Net Gain': [0, 0, 0],
                                  'Net Loss': [0, 0, 0],
                                  'Net Worth': [0, 0, 0],
                                  'Loan Total': [0, 0, 0],
                                  'CC Debt Total': [0, 0, 0],
                                  'Liquid Total': [0, 0, 0],
                                  'Memo': ['', '', '']
                              })
                              ),

                                (
                                'test_p1_only__income_and_payment_on_same_day',
                                AccountSet.AccountSet(checking_acct_list(0) + credit_acct_list(0, 0, 0.05)),
                                BudgetSet.BudgetSet(txn_budget_item_once_list(100,1, 'income',False,False) + txn_budget_item_once_list(100,1, 'test txn',False,False)),
                                MemoRuleSet.MemoRuleSet(match_p1_test_txn_checking_memo_rule_list() + income_rule_list()),
                                '20000101',
                                '20000103',
                                MilestoneSet.MilestoneSet( [], [], []),
                                pd.DataFrame({
                                'Date': ['20000101', '20000102', '20000103'],
                                'Checking': [0, 0, 0],
                                'Credit: Curr Stmt Bal': [0, 0, 0],
                                'Credit: Prev Stmt Bal': [0, 0, 0],
                                    'Marginal Interest': [0, 0, 0],
                                    'Net Gain': [0, 0, 0],
                                    'Net Loss': [0, 0, 0],
                                    'Net Worth': [0, 0, 0],
                                    'Loan Total': [0, 0, 0],
                                    'CC Debt Total': [0, 0, 0],
                                    'Liquid Total': [0, 0, 0],
                                'Memo': ['', 'income (Checking +$100.0); test txn (Checking -$100.0);', '']
                                })
                                ),

                                (
                                'test_cc_payment__satisfice__curr_bal_25__expect_25',
                                AccountSet.AccountSet(checking_acct_list(2000) + credit_acct_list(25, 0, 0.05)),
                                BudgetSet.BudgetSet([]),
                                MemoRuleSet.MemoRuleSet([MemoRule.MemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=1)]),
                                '20000101',
                                '20000103',
                                MilestoneSet.MilestoneSet( [], [], []),
                                pd.DataFrame({
                                    'Date': ['20000101', '20000102', '20000103'],
                                    'Checking': [2000, 1975, 1975],
                                    'Credit: Curr Stmt Bal': [25, 0, 0],
                                    'Credit: Prev Stmt Bal': [0, 0, 0],
                                    'Marginal Interest': [0, 0, 0],
                                    'Net Gain': [0, 0, 0],
                                    'Net Loss': [0, 0, 0],
                                    'Net Worth': [1975, 1975, 1975],
                                    'Loan Total': [0, 0, 0],
                                    'CC Debt Total': [25, 0, 0],
                                    'Liquid Total': [2000, 1975, 1975],
                                    'Memo': ['', 'cc min payment (Credit: Curr Stmt Bal -$25.0);', '']
                                })
                                ),

                                (
                                'test_cc_payment__satisfice__prev_bal_1000__expect_40',
                                AccountSet.AccountSet(checking_acct_list(2000) + credit_acct_list(0, 1000, 0.05)),
                                BudgetSet.BudgetSet([]),
                                MemoRuleSet.MemoRuleSet([MemoRule.MemoRule(memo_regex='.*', account_from='Credit', account_to=None,
                                                                       transaction_priority=1)]),
                                '20000101',
                                '20000103',
                                MilestoneSet.MilestoneSet( [], [], []),
                                pd.DataFrame({
                                    'Date': ['20000101', '20000102', '20000103'],
                                    'Checking': [2000, 1960, 1960],
                                    'Credit: Curr Stmt Bal': [0, 0, 0],
                                    'Credit: Prev Stmt Bal': [1000, 964.17, 964.17],
                                    'Marginal Interest': [0, 4.17, 0],
                                    'Net Gain': [0, 0, 0],
                                    'Net Loss': [0, 4.17, 0],
                                    'Net Worth': [1000, 995.83, 995.83],
                                    'Loan Total': [0, 0, 0],
                                    'CC Debt Total': [1000, 964.17, 964.17],
                                    'Liquid Total': [2000, 1960, 1960],
                                    'Memo': ['', 'cc interest (Checking -$4.17); cc min payment (Credit: Prev Stmt Bal -$35.83);', '']
                                })
                                ),

                                (
                                'test_cc_payment__satisfice__prev_bal_3000__expect_60',
                                AccountSet.AccountSet(checking_acct_list(2000) + credit_acct_list(0, 3000, 0.12)),
                                BudgetSet.BudgetSet([]),
                                MemoRuleSet.MemoRuleSet([MemoRule.MemoRule(memo_regex='.*', account_from='Credit', account_to=None,transaction_priority=1)]),
                                '20000101',
                                '20000103',
                                MilestoneSet.MilestoneSet( [], [], []),
                                pd.DataFrame({
                                    'Date': ['20000101', '20000102', '20000103'],
                                    'Checking': [2000, 1940, 1940],
                                    'Credit: Curr Stmt Bal': [0, 0, 0],
                                    'Credit: Prev Stmt Bal': [3000, 2970, 2970],
                                    'Marginal Interest': [0, 30, 0],
                                    'Net Gain': [0, 0, 0],
                                    'Net Loss': [0, 30, 0],
                                    'Net Worth': [-1000, -1030, -1030],
                                    'Loan Total': [0, 0, 0],
                                    'CC Debt Total': [3000, 2970, 2970],
                                    'Liquid Total': [2000, 1940, 1940],
                                    'Memo': ['', 'cc interest (Checking -$30.0); cc min payment (Credit: Prev Stmt Bal -$30.0);', '']
                                })
                                ),

                            (
                            'test_p2_and_3__expect_skip',
                            AccountSet.AccountSet(checking_acct_list(0) + credit_acct_list(0, 0, 0.05)),
                            BudgetSet.BudgetSet(txn_budget_item_once_list(10,2, 'this should be skipped',False,False)),
                            MemoRuleSet.MemoRuleSet([MemoRule.MemoRule(memo_regex='.*', account_from='Checking', account_to=None,transaction_priority=1),
                                                     MemoRule.MemoRule(memo_regex='.*', account_from='Checking', account_to=None,transaction_priority=2)]),
                            '20000101',
                            '20000103',
                            MilestoneSet.MilestoneSet( [], [], []),
                            pd.DataFrame({
                            'Date': ['20000101', '20000102', '20000103'],
                            'Checking': [0, 0, 0],
                            'Credit: Curr Stmt Bal': [0, 0, 0],
                            'Credit: Prev Stmt Bal': [0, 0, 0],
                                'Marginal Interest': [0, 0, 0],
                                'Net Gain': [0, 0, 0],
                                'Net Loss': [0, 0, 0],
                                'Net Worth': [0, 0, 0],
                                'Loan Total': [0, 0, 0],
                                'CC Debt Total': [0, 0, 0],
                                'Liquid Total': [0, 0, 0],
                            'Memo': ['', '', '']
                            })
                            ),

        (
                'test_p2_and_3__expect_defer',
                AccountSet.AccountSet(checking_acct_list(0) + credit_acct_list(0, 0, 0.05)),
                BudgetSet.BudgetSet(txn_budget_item_once_list(10, 2, 'this should be deferred',True,False)),
                MemoRuleSet.MemoRuleSet([MemoRule.MemoRule(memo_regex='.*', account_from='Checking', account_to=None,
                                                           transaction_priority=1),
                                         MemoRule.MemoRule(memo_regex='.*', account_from='Checking', account_to=None,
                                                           transaction_priority=2),
                                         MemoRule.MemoRule(memo_regex='.*', account_from='Checking', account_to=None,
                                                           transaction_priority=3)]),
                '20000101',
                '20000103',
                MilestoneSet.MilestoneSet( [], [], []),
                pd.DataFrame({
                    'Date': ['20000101', '20000102', '20000103'],
                    'Checking': [0, 0, 0],
                    'Credit: Curr Stmt Bal': [0, 0, 0],
                    'Credit: Prev Stmt Bal': [0, 0, 0],
                    'Marginal Interest': [0, 0, 0],
                    'Net Gain': [0, 0, 0],
                    'Net Loss': [0, 0, 0],
                    'Net Worth': [0, 0, 0],
                    'Loan Total': [0, 0, 0],
                    'CC Debt Total': [0, 0, 0],
                    'Liquid Total': [0, 0, 0],
                    'Memo': ['', '', '']
                })
        ),

        (
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
                    'Memo': ['', 'this should be executed (Checking -$100.0);', '']
                })
        ),

        (
                'test_p2_and_3__p3_item_deferred_bc_p2',
                AccountSet.AccountSet(checking_acct_list(100)),
                BudgetSet.BudgetSet(txn_budget_item_once_list(100, 2, 'this should be executed', False,
                                                              False) + txn_budget_item_once_list(100, 3,
                                                                                                 'this should be deferred',
                                                                                                 True, False)),
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
                    'Memo': ['', 'this should be executed (Checking -$100.0);', '']
                })
        ),

        (
                'test_p4__cc_payment__no_prev_balance__pay_100__no_funds__expect_skip',
                AccountSet.AccountSet(checking_acct_list(0) + credit_acct_list(0,0,0.05)),
                BudgetSet.BudgetSet(txn_budget_item_once_list(100, 4, 'additional credit card payment', False,
                                                              False)),
                MemoRuleSet.MemoRuleSet([MemoRule.MemoRule(memo_regex='.*', account_from='Checking', account_to=None,
                                                           transaction_priority=1),
                                         MemoRule.MemoRule(memo_regex='.*', account_from='Checking', account_to=None,
                                                           transaction_priority=4)
                                         ]),
                '20000101',
                '20000103',
                MilestoneSet.MilestoneSet( [], [], []),
                pd.DataFrame({
                    'Date': ['20000101', '20000102', '20000103'],
                    'Checking': [0, 0, 0],
                    'Credit: Curr Stmt Bal': [0, 0, 0],
                    'Credit: Prev Stmt Bal': [0, 0, 0],
                    'Marginal Interest': [0, 0, 0],
                    'Net Gain': [0, 0, 0],
                    'Net Loss': [0, 0, 0],
                    'Net Worth': [0, 0, 0],
                    'Loan Total': [0, 0, 0],
                    'CC Debt Total': [0, 0, 0],
                    'Liquid Total': [0, 0, 0],
                    'Memo': ['', '', '']
                })
        ),

        (
                'test_p4__cc_payment__no_prev_balance__pay_100__expect_skip',
                AccountSet.AccountSet(checking_acct_list(2000) + credit_acct_list(0, 0, 0.05)),
                BudgetSet.BudgetSet(txn_budget_item_once_list(100, 4, 'this should be skipped', False,
                                                              False)),
                MemoRuleSet.MemoRuleSet([MemoRule.MemoRule(memo_regex='.*', account_from='Credit', account_to=None,
                                                           transaction_priority=1),
                                         MemoRule.MemoRule(memo_regex='.*', account_from='Checking', account_to='Credit',
                                                           transaction_priority=4)
                                         ]),
                '20000101',
                '20000103',
                MilestoneSet.MilestoneSet( [], [], []),
                pd.DataFrame({
                    'Date': ['20000101', '20000102', '20000103'],
                    'Checking': [2000, 2000, 2000],
                    'Credit: Curr Stmt Bal': [0, 0, 0],
                    'Credit: Prev Stmt Bal': [0, 0, 0],
                    'Marginal Interest': [0, 0, 0],
                    'Net Gain': [0, 0, 0],
                    'Net Loss': [0, 0, 0],
                    'Net Worth': [2000, 2000, 2000],
                    'Loan Total': [0, 0, 0],
                    'CC Debt Total': [0, 0, 0],
                    'Liquid Total': [2000, 2000, 2000],
                    'Memo': ['', '', '']
                })
        ),

        (
                'test_p4__cc_payment__pay_all_of_prev_part_of_curr__expect_800',
                AccountSet.AccountSet(checking_acct_list(2000) + credit_bsd12_acct_list(500, 500, 0.05)),
                BudgetSet.BudgetSet(txn_budget_item_once_list(800, 4, 'test pay all prev part of curr', False,
                                                              False)),
                MemoRuleSet.MemoRuleSet([MemoRule.MemoRule(memo_regex='.*', account_from='Credit', account_to=None,
                                                           transaction_priority=1),
                                         MemoRule.MemoRule(memo_regex='.*', account_from='Checking',
                                                           account_to='Credit',
                                                           transaction_priority=4)
                                         ]),
                '20000101',
                '20000103',
                MilestoneSet.MilestoneSet( [], [], []),
                pd.DataFrame({
                    'Date': ['20000101', '20000102', '20000103'],
                    'Checking': [2000, 1200, 1200],
                    'Credit: Curr Stmt Bal': [500, 200, 200],
                    'Credit: Prev Stmt Bal': [500, 0, 0],
                    'Marginal Interest': [0, 0, 0],
                    'Net Gain': [0, 0, 0],
                    'Net Loss': [0, 800, 0],
                    'Net Worth': [1000, 1000, 1000],
                    'Loan Total': [0, 0, 0],
                    'CC Debt Total': [1000, 200, 200],
                    'Liquid Total': [2000, 1200, 1200],
                    'Memo': ['', 'test pay all prev part of curr (Checking -$800.0);  additional cc payment (Credit: Curr Stmt Bal $300.0);  additional cc payment (Credit: Prev Stmt Bal $500.0);', '']
                })
        ),

        (
                'test_p4__cc_payment__pay_part_of_prev_balance__expect_200',
                AccountSet.AccountSet(checking_acct_list(200) + credit_bsd12_acct_list(500, 500, 0.05)),
                BudgetSet.BudgetSet(txn_budget_item_once_list(200, 4, 'additional cc payment test', False,
                                                              False)),
                MemoRuleSet.MemoRuleSet([MemoRule.MemoRule(memo_regex='.*', account_from='Credit', account_to=None,
                                                           transaction_priority=1),
                                         MemoRule.MemoRule(memo_regex='.*additional cc payment.*', account_from='Checking',
                                                           account_to='Credit',
                                                           transaction_priority=4)
                                         ]),
                '20000101',
                '20000103',
                MilestoneSet.MilestoneSet( [], [], []),
                pd.DataFrame({
                    'Date': ['20000101', '20000102', '20000103'],
                    'Checking': [200, 0, 0],
                    'Credit: Curr Stmt Bal': [500, 500, 500],
                    'Credit: Prev Stmt Bal': [500, 300, 300],
                    'Marginal Interest': [0, 0, 0],
                    'Net Gain': [0, 0, 0],
                    'Net Loss': [0, 0, 0],
                    'Net Worth': [-800, -800, -800],
                    'Loan Total': [0, 0, 0],
                    'CC Debt Total': [1000, 800, 800],
                    'Liquid Total': [200, 0, 0],
                    'Memo': ['', 'additional cc payment test (Checking -$200.0);  additional cc payment (Credit: Prev Stmt Bal $200.0);', '']
                })
        ),

        (
                'test_p4__cc_payment__non_0_prev_balance_but_no_funds__expect_0',
                AccountSet.AccountSet(checking_acct_list(40) + credit_acct_list(500, 500, 0.05)),
                BudgetSet.BudgetSet(txn_budget_item_once_list(100, 4, 'additional cc payment test', False,
                                                              False)),
                MemoRuleSet.MemoRuleSet([MemoRule.MemoRule(memo_regex='.*', account_from='Credit', account_to=None,
                                                           transaction_priority=1),
                                         MemoRule.MemoRule(memo_regex='.*additional cc payment.*',
                                                           account_from='Checking',
                                                           account_to='Credit',
                                                           transaction_priority=4)
                                         ]),
                '20000101',
                '20000103',
                MilestoneSet.MilestoneSet( [], [], []),
                pd.DataFrame({
                    'Date': ['20000101', '20000102', '20000103'],
                    'Checking': [40, 0, 0],
                    'Credit: Curr Stmt Bal': [500, 0, 0],
                    'Credit: Prev Stmt Bal': [500, 962.08, 962.08],
                    'Marginal Interest': [0, 2.08, 0],
                    'Net Gain': [0, 0, 0],
                    'Net Loss': [0, 2.08, 0],
                    'Net Worth': [-960, -962.08, -962.08],
                    'Loan Total': [0, 0, 0],
                    'CC Debt Total': [1000, 962.08, 962.08],
                    'Liquid Total': [40, 0, 0],
                    'Memo': ['', 'cc interest (Checking -$2.08); cc min payment (Credit: Prev Stmt Bal -$37.92);', '']
                })
        ),

        (
                'test_p4__cc_payment__partial_of_indicated_amount',
                AccountSet.AccountSet(checking_acct_list(1000) + credit_bsd12_acct_list(500, 1500, 0.05)),
                BudgetSet.BudgetSet(txn_budget_item_once_list(20000, 4, 'partial cc payment', False,
                                                              True)),
                MemoRuleSet.MemoRuleSet([MemoRule.MemoRule(memo_regex='.*', account_from='Credit', account_to=None,
                                                           transaction_priority=1),
                                         MemoRule.MemoRule(memo_regex='.*',
                                                           account_from='Checking',
                                                           account_to='Credit',
                                                           transaction_priority=4)
                                         ]),
                '20000101',
                '20000103',
                MilestoneSet.MilestoneSet( [], [], []),
                pd.DataFrame({
                    'Date': ['20000101', '20000102', '20000103'],
                    'Checking': [1000, 0, 0],
                    'Credit: Curr Stmt Bal': [1500, 1000, 1000],
                    'Credit: Prev Stmt Bal': [500, 0, 0],
                    'Marginal Interest': [0, 0, 0],
                    'Net Gain': [0, 0, 0],
                    'Net Loss': [0, 1000, 0],
                    'Net Worth': [-1000, -1000, -1000],
                    'Loan Total': [0, 0, 0],
                    'CC Debt Total': [2000, 1000, 1000],
                    'Liquid Total': [1000, 0, 0],
                    'Memo': ['', 'partial cc payment (Checking -$1000.0);  additional cc payment (Credit: Curr Stmt Bal $500.0);  additional cc payment (Credit: Prev Stmt Bal $500.0);', '']
                })
        ), # 12/21 4AM this is coded correctly and the test fail is bc of algo

        (
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
                    'Memo': ['', 'SPEND daily p1 txn (Checking -$100.0);',
                             'SPEND daily p1 txn 2 (Checking -$100.0);',
                             '200 income on 1/4 (Checking +$200.0); SPEND daily p1 txn 3 (Checking -$100.0); SPEND p2 txn deferred from 1/2 to 1/4 (Checking -$400.0);']
                })
        ),

        (
                'test_execute_at_reduced_amount_bc_later_higher_priority_txn',
                AccountSet.AccountSet(checking_acct_list(400)),
                BudgetSet.BudgetSet(
                    [BudgetItem.BudgetItem('20000104', '20000104', 2, 'once', 200, 'pay 200 after reduced amt txn', False, False),
                     BudgetItem.BudgetItem('20000103', '20000103', 3, 'once', 400, 'pay reduced amount', False, True)]
                    #+
                    #txn_budget_item_once_list(200, 2, 'pay 200 after reduced amt txn', False, False) +
                    #txn_budget_item_once_list(400, 3,'pay reduced amount',False, True)
                    ),
                MemoRuleSet.MemoRuleSet([MemoRule.MemoRule(memo_regex='.*',
                                                           account_from='Checking',
                                                           account_to=None,
                                                           transaction_priority=1),
                                         MemoRule.MemoRule(memo_regex='.*',
                                                           account_from='Checking',
                                                           account_to=None,
                                                           transaction_priority=2),
                                         MemoRule.MemoRule(memo_regex='.*',
                                                           account_from='Checking',
                                                           account_to=None,
                                                           transaction_priority=3)
                                         ]),
                '20000101',
                '20000105',  # note that this is later than the test defined above
                MilestoneSet.MilestoneSet( [], [], []),
                pd.DataFrame({
                    'Date': ['20000101', '20000102', '20000103', '20000104', '20000105'],
                    'Checking': [400, 400, 200, 0, 0],
                    'Marginal Interest': [0, 0, 0, 0, 0],
                    'Net Gain': [0, 0, 0, 0, 0],
                    'Net Loss': [0, 0, 200, 200, 0],
                    'Net Worth': [400, 400, 200, 0, 0],
                    'Loan Total': [0, 0, 0, 0, 0],
                    'CC Debt Total': [0, 0, 0, 0, 0],
                    'Liquid Total': [400, 400, 200, 0, 0],
                    'Memo': ['', '', 'pay reduced amount (Checking -$200.0);', 'pay 200 after reduced amt txn (Checking -$200.0);', '']
                })
        ),  #this test cas coded correctly. the fail is bc of algo. 12/12 5:21AM

        (
                'test_transactions_executed_at_p1_and_p2',
                AccountSet.AccountSet(checking_acct_list(2000)),
                BudgetSet.BudgetSet(
                    [BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 100, 'p1 daily txn 1',False, False),
                     BudgetItem.BudgetItem('20000103', '20000103', 1, 'once', 100, 'p1 daily txn 2',False, False),
                     BudgetItem.BudgetItem('20000104', '20000104', 1, 'once', 100, 'p1 daily txn 3',False, False),
                     BudgetItem.BudgetItem('20000105', '20000105', 1, 'once', 100, 'p1 daily txn 4', False, False),

                     BudgetItem.BudgetItem('20000102', '20000102', 2, 'once', 100, 'p2 daily txn 1/2/00', False, False),
                     BudgetItem.BudgetItem('20000103', '20000103', 2, 'once', 100, 'p2 daily txn 1/3/00', False, False),
                     BudgetItem.BudgetItem('20000104', '20000104', 2, 'once', 100, 'p2 daily txn 1/4/00', False, False),
                     BudgetItem.BudgetItem('20000105', '20000105', 2, 'once', 100, 'p2 daily txn 1/5/00', False, False)
                     ]

                ),
                MemoRuleSet.MemoRuleSet([MemoRule.MemoRule(memo_regex='.*',
                                                           account_from='Checking',
                                                           account_to=None,
                                                           transaction_priority=1),
                                         MemoRule.MemoRule(memo_regex='.*',
                                                           account_from='Checking',
                                                           account_to=None,
                                                           transaction_priority=2)
                                         ]),
                '20000101',
                '20000106',  # note that this is later than the test defined above
                MilestoneSet.MilestoneSet( [], [], []),
                pd.DataFrame({
                    'Date': ['20000101', '20000102', '20000103', '20000104', '20000105', '20000106'],
                    'Checking': [2000, 1800, 1600, 1400, 1200, 1200],
                    'Marginal Interest': [0, 0, 0, 0, 0, 0],
                    'Net Gain': [0, 0, 0, 0, 0, 0],
                    'Net Loss': [0, 200, 200, 200, 200, 0],
                    'Net Worth': [2000, 1800, 1600, 1400, 1200, 1200],
                    'Loan Total': [0, 0, 0, 0, 0, 0],
                    'CC Debt Total': [0, 0, 0, 0, 0, 0],
                    'Liquid Total': [2000, 1800, 1600, 1400, 1200, 1200],
                    'Memo': ['',
                             'p1 daily txn 1 (Checking -$100.0); p2 daily txn 1/2/00 (Checking -$100.0);',
                             'p1 daily txn 2 (Checking -$100.0); p2 daily txn 1/3/00 (Checking -$100.0);',
                             'p1 daily txn 3 (Checking -$100.0); p2 daily txn 1/4/00 (Checking -$100.0);',
                             'p1 daily txn 4 (Checking -$100.0); p2 daily txn 1/5/00 (Checking -$100.0);',
                             '']
                })
        ),

            (
            'test_transactions_executed_at_p1_and_p2_and_p3',
            AccountSet.AccountSet(checking_acct_list(2000)),
            BudgetSet.BudgetSet(
                [BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 100, 'p1 daily txn 1/2/00', False, False),
                 BudgetItem.BudgetItem('20000103', '20000103', 1, 'once', 100, 'p1 daily txn 1/3/00', False, False),
                 BudgetItem.BudgetItem('20000104', '20000104', 1, 'once', 100, 'p1 daily txn 1/4/00', False, False),
                 BudgetItem.BudgetItem('20000105', '20000105', 1, 'once', 100, 'p1 daily txn 1/5/00', False, False),

                 BudgetItem.BudgetItem('20000102', '20000102', 2, 'once', 100, 'p2 daily txn 1/2/00', False, False),
                 BudgetItem.BudgetItem('20000103', '20000103', 2, 'once', 100, 'p2 daily txn 1/3/00', False, False),
                 BudgetItem.BudgetItem('20000104', '20000104', 2, 'once', 100, 'p2 daily txn 1/4/00', False, False),
                 BudgetItem.BudgetItem('20000105', '20000105', 2, 'once', 100, 'p2 daily txn 1/5/00', False, False),

                 BudgetItem.BudgetItem('20000102', '20000102', 3, 'once', 100, 'p3 daily txn 1/2/00', False, False),
                 BudgetItem.BudgetItem('20000103', '20000103', 3, 'once', 100, 'p3 daily txn 1/3/00', False, False),
                 BudgetItem.BudgetItem('20000104', '20000104', 3, 'once', 100, 'p3 daily txn 1/4/00', False, False),
                 BudgetItem.BudgetItem('20000105', '20000105', 3, 'once', 100, 'p3 daily txn 1/5/00', False, False)
                 ]

            ),
            MemoRuleSet.MemoRuleSet([MemoRule.MemoRule(memo_regex='.*',
                                                       account_from='Checking',
                                                       account_to=None,
                                                       transaction_priority=1),
                                     MemoRule.MemoRule(memo_regex='.*',
                                                       account_from='Checking',
                                                       account_to=None,
                                                       transaction_priority=2),
                                     MemoRule.MemoRule(memo_regex='.*',
                                                       account_from='Checking',
                                                       account_to=None,
                                                       transaction_priority=3)
                                     ]),
            '20000101',
            '20000106',  # note that this is later than the test defined above
            MilestoneSet.MilestoneSet( [], [], []),
            pd.DataFrame({
                'Date': ['20000101', '20000102', '20000103', '20000104', '20000105', '20000106'],
                'Checking': [2000, 1700, 1400, 1100, 800, 800],
                'Marginal Interest': [0, 0, 0, 0, 0, 0],
                    'Net Gain': [0, 0, 0, 0, 0, 0],
                    'Net Loss': [0, 300, 300, 300, 300, 0],
                    'Net Worth': [2000, 1700, 1400, 1100, 800, 800],
                    'Loan Total': [0, 0, 0, 0, 0, 0],
                    'CC Debt Total': [0, 0, 0, 0, 0, 0],
                    'Liquid Total': [2000, 1700, 1400, 1100, 800, 800],
                'Memo': ['',
                         'p1 daily txn 1/2/00 (Checking -$100.0); p2 daily txn 1/2/00 (Checking -$100.0); p3 daily txn 1/2/00 (Checking -$100.0);',
                         'p1 daily txn 1/3/00 (Checking -$100.0); p2 daily txn 1/3/00 (Checking -$100.0); p3 daily txn 1/3/00 (Checking -$100.0);',
                         'p1 daily txn 1/4/00 (Checking -$100.0); p2 daily txn 1/4/00 (Checking -$100.0); p3 daily txn 1/4/00 (Checking -$100.0);',
                         'p1 daily txn 1/5/00 (Checking -$100.0); p2 daily txn 1/5/00 (Checking -$100.0); p3 daily txn 1/5/00 (Checking -$100.0);',
                         '']
            })
        ),

        # (
        #         'test_transactions_executed_at_p1_and_p2_and_p3',
        #         AccountSet.AccountSet(checking_acct_list(2000)),
        #         BudgetSet.BudgetSet(
        #             [BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 100, 'p1 daily txn 1/2/00', False, False),
        #              BudgetItem.BudgetItem('20000103', '20000103', 1, 'once', 100, 'p1 daily txn 1/3/00', False, False),
        #              BudgetItem.BudgetItem('20000104', '20000104', 1, 'once', 100, 'p1 daily txn 1/4/00', False, False),
        #              BudgetItem.BudgetItem('20000105', '20000105', 1, 'once', 100, 'p1 daily txn 1/5/00', False, False),
        #
        #              BudgetItem.BudgetItem('20000102', '20000102', 2, 'once', 100, 'p2 daily txn 1/2/00', False, False),
        #              BudgetItem.BudgetItem('20000103', '20000103', 2, 'once', 100, 'p2 daily txn 1/3/00', False, False),
        #              BudgetItem.BudgetItem('20000104', '20000104', 2, 'once', 100, 'p2 daily txn 1/4/00', False, False),
        #              BudgetItem.BudgetItem('20000105', '20000105', 2, 'once', 100, 'p2 daily txn 1/5/00', False, False),
        #
        #              BudgetItem.BudgetItem('20000102', '20000102', 3, 'once', 100, 'p3 daily txn 1/2/00', False, False),
        #              BudgetItem.BudgetItem('20000103', '20000103', 3, 'once', 100, 'p3 daily txn 1/3/00', False, False),
        #              BudgetItem.BudgetItem('20000104', '20000104', 3, 'once', 100, 'p3 daily txn 1/4/00', False, False),
        #              BudgetItem.BudgetItem('20000105', '20000105', 3, 'once', 100, 'p3 daily txn 1/5/00', False, False)
        #              ]
        #
        #         ),
        #         MemoRuleSet.MemoRuleSet([MemoRule.MemoRule(memo_regex='.*',
        #                                                    account_from='Checking',
        #                                                    account_to=None,
        #                                                    transaction_priority=1),
        #                                  MemoRule.MemoRule(memo_regex='.*',
        #                                                    account_from='Checking',
        #                                                    account_to=None,
        #                                                    transaction_priority=2),
        #                                  MemoRule.MemoRule(memo_regex='.*',
        #                                                    account_from='Checking',
        #                                                    account_to=None,
        #                                                    transaction_priority=3)
        #                                  ]),
        #         '20000101',
        #         '20000106',  # note that this is later than the test defined above
        #         MilestoneSet.MilestoneSet( [], [], []),
        #         pd.DataFrame({
        #             'Date': ['20000101', '20000102', '20000103', '20000104', '20000105', '20000106'],
        #             'Checking': [2000, 1700, 1400, 1100, 800, 800],
        #             'Memo': ['', '', '', '', '', '']
        #         })
        # ),


        ( 'test_p7__additional_loan_payment__amt_10',
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
                    'Memo': ['', 'loan min payment (Loan A: Interest -$50.0);  loan min payment (Loan B: Interest -$50.0);  loan min payment (Loan C: Interest -$50.0);  additional loan payment (Loan A: Interest -$10.0);', '']
                })
        ),

        ('test_p7__additional_loan_payment__amt_110',
         AccountSet.AccountSet(
             checking_acct_list(5000) + non_trivial_loan('Loan A', 1000, 100, 0.1) + non_trivial_loan('Loan B', 1000,
                                                                                                      100,
                                                                                                      0.05) + non_trivial_loan(
                 'Loan C', 1000, 100, 0.01)),
         BudgetSet.BudgetSet([BudgetItem.BudgetItem('20000102', '20000102', 7, 'once', 110, 'additional_loan_payment')]),
         MemoRuleSet.MemoRuleSet([
             MemoRule.MemoRule('.*', 'Checking', None, 1),
             MemoRule.MemoRule('additional_loan_payment', 'Checking', 'ALL_LOANS', 7)
         ]),
         '20000101',
         '20000103',
         MilestoneSet.MilestoneSet( [], [], []),
         pd.DataFrame({
             'Date': ['20000101', '20000102', '20000103'],
             'Checking': [5000, 4740, 4740],
             'Loan A: Principal Balance': [1000, 940.27, 940.27],
             'Loan A: Interest': [100, 0.0, 0.26],
             'Loan B: Principal Balance': [1000, 1000, 1000],
             'Loan B: Interest': [100, 50.14, 50.28],
             'Loan C: Principal Balance': [1000, 1000, 1000],
             'Loan C: Interest': [100, 50.03, 50.06],
             'Marginal Interest': [0, 0.44, 0.43],
             'Net Gain': [0, 0, 0],
             'Net Loss': [0, 0, 0],
             'Net Worth': [1700, 1699.56, 1699.13],
             'Loan Total': [3300, 3040.44, 3040.87],
             'CC Debt Total': [0, 0, 0],
             'Liquid Total': [5000, 4740, 4740],
             'Memo': ['', 'loan min payment (Loan A: Interest -$50.0);  loan min payment (Loan B: Interest -$50.0);  loan min payment (Loan C: Interest -$50.0);  additional loan payment (Loan A: Principal Balance -$59.73);  additional loan payment (Loan A: Interest -$50.27);', '']
         })
         ),

        ('test_p7__additional_loan_payment__amt_560',
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
             'Loan B: Principal Balance': [1000, 1000, 1000],
             'Loan B: Interest': [100, 43.52, 43.66],
             'Loan C: Principal Balance': [1000, 1000, 1000],
             'Loan C: Interest': [ 100, 50.03, 50.06 ],
             'Marginal Interest': [0, 0.44, 0.31],
             'Net Gain': [0, 0, 0],
             'Net Loss': [0, 0, 0],
             'Net Worth': [1700, 1699.56, 1699.25],
             'Loan Total': [3300, 2590.44, 2590.75],
             'CC Debt Total': [0, 0, 0],
             'Liquid Total': [5000, 5000 - 150 - 560, 5000 - 150 - 560],
             'Memo': ['', 'loan min payment (Loan A: Interest -$50.0);  loan min payment (Loan B: Interest -$50.0);  loan min payment (Loan C: Interest -$50.0);  additional loan payment (Loan A: Principal Balance -$503.11);  additional loan payment (Loan A: Interest -$50.27);  additional loan payment (Loan B: Interest -$6.62);', '']
         })
         ), #todo double check this math

        ('test_p7__additional_loan_payment__amt_610',
         AccountSet.AccountSet(
             checking_acct_list(5000) + non_trivial_loan('Loan A', 1000, 100, 0.1) + non_trivial_loan('Loan B', 1000,
                                                                                                      100,
                                                                                                      0.05) + non_trivial_loan(
                 'Loan C', 1000, 100, 0.01)),
         BudgetSet.BudgetSet(
             [BudgetItem.BudgetItem('20000102', '20000102', 7, 'once', 610, 'additional_loan_payment')]),
         MemoRuleSet.MemoRuleSet([
             MemoRule.MemoRule('.*', 'Checking', None, 1),
             MemoRule.MemoRule('additional_loan_payment', 'Checking', 'ALL_LOANS', 7)
         ]),
         '20000101',
         '20000103',
         MilestoneSet.MilestoneSet( [], [], []),
         pd.DataFrame({
             'Date': ['20000101', '20000102', '20000103'],
             'Checking': [5000, 5000 - 150 - 610, 5000 - 150 - 610],
             'Loan A: Principal Balance': [1000, 480.89, 480.89],
             'Loan A: Interest': [100, 0, 0.13],
             'Loan B: Principal Balance': [1000, 1000, 1000],
             'Loan B: Interest': [100, 9.52, 9.66],
             'Loan C: Principal Balance': [1000, 1000, 1000],
             'Loan C: Interest': [100, 50.03,50.06],
             'Marginal Interest': [0, 0.44, 0.3],
             'Net Gain': [0, 0, 0],
             'Net Loss': [0, 0, 0],
             'Net Worth': [1700, 1699.56, 1699.26],
             'Loan Total': [3300, 2540.44, 2540.74],
             'CC Debt Total': [0, 0, 0],
             'Liquid Total': [5000, 5000 - 150 - 610, 5000 - 150 - 610],
             'Memo': ['', 'loan min payment (Loan A: Interest -$50.0);  loan min payment (Loan B: Interest -$50.0);  loan min payment (Loan C: Interest -$50.0);  additional loan payment (Loan A: Principal Balance -$519.11);  additional loan payment (Loan A: Interest -$50.27);  additional loan payment (Loan B: Interest -$40.62);', '']
         })
         ),  # todo check this math


        ('test_p7__additional_loan_payment__amt_1900',
         AccountSet.AccountSet(
             checking_acct_list(5000) + non_trivial_loan('Loan A', 1000, 100, 0.1) + non_trivial_loan('Loan B', 1000,
                                                                                                      100,
                                                                                                      0.05) + non_trivial_loan(
                 'Loan C', 1000, 100, 0.01)),
         BudgetSet.BudgetSet(
             [BudgetItem.BudgetItem('20000102', '20000102', 7, 'once', 1900, 'additional_loan_payment')]),
         MemoRuleSet.MemoRuleSet([
             MemoRule.MemoRule('.*', 'Checking', None, 1),
             MemoRule.MemoRule('additional_loan_payment', 'Checking', 'ALL_LOANS', 7)
         ]),
         '20000101',
         '20000103',
         MilestoneSet.MilestoneSet( [], [], []),
         pd.DataFrame({
             'Date': ['20000101', '20000102', '20000103'],
             'Checking': [5000, 5000 - 150 - 1900, 5000 - 150 - 1900],
             'Loan A: Principal Balance': [1000, 92.62, 92.62],
             'Loan A: Interest': [100, 0, 0.03],
             'Loan B: Principal Balance': [1000, 185.25, 185.25],
             'Loan B: Interest': [100, 0, 0.03],
             'Loan C: Principal Balance': [1000, 972.57, 972.57],
             'Loan C: Interest': [100, 0, 0.03],
             'Marginal Interest': [0, 0.44, 0.09],
             'Net Gain': [0, 0, 0],
             'Net Loss': [0, 0, 0],
             'Net Worth': [1700, 1699.56, 1699.47],
             'Loan Total': [3300, 1250.44, 1250.53],
             'CC Debt Total': [0, 0, 0],
             'Liquid Total': [5000, 5000 - 150 - 1900, 5000 - 150 - 1900],
             'Memo': ['', 'loan min payment (Loan A: Interest -$50.0);  loan min payment (Loan B: Interest -$50.0);  loan min payment (Loan C: Interest -$50.0);  additional loan payment (Loan A: Principal Balance -$907.38);  additional loan payment (Loan A: Interest -$50.27);  additional loan payment (Loan B: Principal Balance -$814.75);  additional loan payment (Loan B: Interest -$50.14);  additional loan payment (Loan C: Principal Balance -$27.43);  additional loan payment (Loan C: Interest -$50.03);', '']
         })
         ),

        ('test_p7__additional_loan_payment__amt_overpay',
         AccountSet.AccountSet(
             checking_acct_list(5000) + non_trivial_loan('Loan A', 1000, 100, 0.1) + non_trivial_loan('Loan B', 1000,
                                                                                                      100,
                                                                                                      0.05) + non_trivial_loan(
                 'Loan C', 1000, 100, 0.01)),
         BudgetSet.BudgetSet(
             [BudgetItem.BudgetItem('20000102', '20000102', 7, 'once', 3500, 'additional_loan_payment')]),
         MemoRuleSet.MemoRuleSet([
             MemoRule.MemoRule('.*', 'Checking', None, 1),
             MemoRule.MemoRule('additional_loan_payment', 'Checking', 'ALL_LOANS', 7)
         ]),
         '20000101',
         '20000103',
         MilestoneSet.MilestoneSet( [], [], []),
         pd.DataFrame({
             'Date': ['20000101', '20000102', '20000103'],
             'Checking': [5000, 1699.56, 1699.56],
             'Loan A: Principal Balance': [1000, 0, 0],
             'Loan A: Interest': [100, 0, 0],
             'Loan B: Principal Balance': [1000, 0, 0],
             'Loan B: Interest': [100, 0, 0],
             'Loan C: Principal Balance': [1000, 0, 0],
             'Loan C: Interest': [100, 0, 0],
             'Marginal Interest': [0, 0.44, 0],
             'Net Gain': [0, 0, 0],
             'Net Loss': [0, 0, 0],
             'Net Worth': [1700, 1699.56, 1699.56],
             'Loan Total': [3300, 0, 0],
             'CC Debt Total': [0, 0, 0],
             'Liquid Total': [5000, 1699.56, 1699.56],
             'Memo': ['', 'loan min payment (Loan A: Interest -$50.0);  loan min payment (Loan B: Interest -$50.0);  loan min payment (Loan C: Interest -$50.0);  additional loan payment (Loan A: Principal Balance -$1000.0);  additional loan payment (Loan A: Interest -$50.27);  additional loan payment (Loan B: Principal Balance -$1000.0);  additional loan payment (Loan B: Interest -$50.14);  additional loan payment (Loan C: Principal Balance -$1000.0);  additional loan payment (Loan C: Interest -$50.03);', '']
         })
         ),

                                # (
                                #         'test_p1_only_no_budget_items',
                                #         AccountSet.AccountSet(checking_acct_list(0) + credit_acct_list(0, 0, 0.05)),
                                #         BudgetSet.BudgetSet([]),
                                #         MemoRuleSet.MemoRuleSet(match_p1_test_txn_checking_memo_rule_list()),
                                #         '20000101',
                                #         '20000103',
                                #         MilestoneSet.MilestoneSet( [], [], []),
                                #         pd.DataFrame({
                                #             'Date': ['20000101', '20000102', '20000103'],
                                #             'Checking': [0, 0, 0],
                                #             'Credit: Curr Stmt Bal': [0, 0, 0],
                                #             'Credit: Prev Stmt Bal': [0, 0, 0],
                                #             'Memo': ['', '', '']
                                #         })
                                # ),

                             ])
    def test_business_case(self,test_description,account_set,budget_set,memo_rule_set,start_date_YYYYMMDD,end_date_YYYYMMDD,milestone_set,expected_result_df):

        expected_result_df.Date = [datetime.datetime.strptime(x, '%Y%m%d') for x in
                                   expected_result_df.Date]

        E = self.compute_forecast_and_actual_vs_expected(account_set,
                                                     budget_set,
                                                     memo_rule_set,
                                                     start_date_YYYYMMDD,
                                                     end_date_YYYYMMDD,
                                                     milestone_set,
                                                     expected_result_df,
                                                     test_description)

    @pytest.mark.parametrize('test_description,account_set,budget_set,memo_rule_set,start_date_YYYYMMDD,end_date_YYYYMMDD,milestone_set,expected_result_df,expected_memo_of_deferred_txn,expected_deferred_date',[
    (
            'test_p5_and_6__expect_defer',
            AccountSet.AccountSet(checking_acct_list(1000)),
            BudgetSet.BudgetSet([BudgetItem.BudgetItem('20000102', '20000102', 5, 'once', 100, 'p5 txn 1/2/00', False, False),
                                 BudgetItem.BudgetItem('20000102', '20000102', 6, 'once', 1000, 'p6 deferrable txn 1/2/00', True, False),
                                 ]),
            MemoRuleSet.MemoRuleSet( [
                MemoRule.MemoRule('.*','Checking',None,5),
                MemoRule.MemoRule('.*', 'Checking', None, 6)
            ] ),
            '20000101',
            '20000103',
            MilestoneSet.MilestoneSet( [], [], []),
            pd.DataFrame({
                'Date': ['20000101', '20000102', '20000103'],
                'Checking': [1000, 900, 900],
                'Marginal Interest': [0, 0, 0],
                'Net Gain': [0, 0, 0],
                'Net Loss': [0, 100, 0],
                'Net Worth': [1000, 900, 900],
                'Loan Total': [0, 0, 0],
                'CC Debt Total': [0, 0, 0],
                'Liquid Total': [1000, 900, 900],
                'Memo': ['', 'p5 txn 1/2/00 (Checking -$100.0);', '']
            }),
            'p6 deferrable txn 1/2/00',
            None #deferred but never executed
    ),

        (
                'test_p5_and_6__expect_defer__daily',
                AccountSet.AccountSet(checking_acct_list(1000)),
                BudgetSet.BudgetSet(
                    [BudgetItem.BudgetItem('20000102', '20000102', 5, 'once', 100, 'p5 txn 1/2/00', False, False),
                     BudgetItem.BudgetItem('20000103', '20000103', 1, 'once', 100, 'income 1/3/00', False, False),
                     BudgetItem.BudgetItem('20000102', '20000102', 6, 'once', 1000, 'p6 deferrable txn 1/2/00', True, False),
                     ]),
                MemoRuleSet.MemoRuleSet([
                    MemoRule.MemoRule('.*', None, 'Checking', 1),
                    MemoRule.MemoRule('.*', 'Checking', None, 5),
                    MemoRule.MemoRule('.*', 'Checking', None, 6)
                ]),
                '20000101',
                '20000103',
                MilestoneSet.MilestoneSet( [], [], []),
                pd.DataFrame({
                    'Date': ['20000101', '20000102', '20000103'],
                    'Checking': [1000, 900, 0],
                    'Marginal Interest': [0, 0, 0],
                    'Net Gain': [0, 0, 0],
                    'Net Loss': [0, 100, 900],
                    'Net Worth': [1000, 900, 0],
                    'Loan Total': [0, 0, 0],
                    'CC Debt Total': [0, 0, 0],
                    'Liquid Total': [1000, 900, 0],
                    'Memo': ['', 'p5 txn 1/2/00 (Checking -$100.0); ', 'income 1/3/00 (Checking +$100.0); p6 deferrable txn 1/2/00 (Checking -$1000.0);']
                }),
                'p6 deferrable txn 1/2/00 (Checking -$1000.0)',
                '20000103'
        ),

        (
                'test_expect_defer_past_end_of_forecast',
                AccountSet.AccountSet(checking_acct_list(1000)),
                BudgetSet.BudgetSet(
                    [BudgetItem.BudgetItem('20000102', '20000102', 2, 'once', 2000, 'deferred past end', True, False)
                     ]),
                MemoRuleSet.MemoRuleSet([
                    MemoRule.MemoRule('.*', None, 'Checking', 1),
                    MemoRule.MemoRule('.*', 'Checking', None, 2)
                ]),
                '20000101',
                '20000103',
                MilestoneSet.MilestoneSet( [], [], []),
                pd.DataFrame({
                    'Date': ['20000101', '20000102', '20000103'],
                    'Checking': [1000, 1000, 1000],
                    'Marginal Interest': [0,0,0],
                    'Net Gain': [0,0,0],
                    'Net Loss': [0,0,0],
                    'Net Worth': [1000,1000,1000],
                    'Loan Total': [0,0,0],
                    'CC Debt Total': [0,0,0],
                    'Liquid Total': [1000,1000,1000],
                    'Memo': ['', '', '']
                }),
                'deferred past end',
                None
        ),

    ])
    def test_deferrals(self, test_description, account_set, budget_set, memo_rule_set, start_date_YYYYMMDD,
                           end_date_YYYYMMDD, milestone_set, expected_result_df, expected_memo_of_deferred_txn,
                       expected_deferred_date):

        expected_result_df.Date = [datetime.datetime.strptime(x, '%Y%m%d') for x in
                                   expected_result_df.Date]

        E = self.compute_forecast_and_actual_vs_expected(account_set,
                                                         budget_set,
                                                         memo_rule_set,
                                                         start_date_YYYYMMDD,
                                                         end_date_YYYYMMDD,
                                                         milestone_set,
                                                         expected_result_df,
                                                         test_description)

        if expected_deferred_date is not None:
            row_sel_vec = [ datetime.datetime.strptime(d,'%Y%m%d') == datetime.datetime.strptime(expected_deferred_date,'%Y%m%d') for d in E.forecast_df.Date ]
            assert sum(row_sel_vec) == 1 #if 0, then deferred date was not found
            assert expected_memo_of_deferred_txn in E.forecast_df.loc[ row_sel_vec , 'Memo'].iat[0]
        else:
            print('E.deferred_df')
            print(E.deferred_df.to_string())
            assert E.deferred_df.shape[0] == 1
            assert E.deferred_df.loc[0, 'Memo'] == expected_memo_of_deferred_txn


    def test_multiple_matching_memo_rule_regex(self):

        start_date_YYYYMMDD = '20000101'
        end_date_YYYYMMDD = '20000103'

        account_set = AccountSet.AccountSet([])
        budget_set = BudgetSet.BudgetSet([])
        memo_rule_set = MemoRuleSet.MemoRuleSet([])

        account_set.createAccount(name='Checking',
                                  balance=1000,
                                  min_balance=0,
                                  max_balance=float('Inf'),
                                  account_type="checking",
                                  primary_checking_ind=True)

        account_set.createAccount(name='Credit',
                                  balance=0,
                                  min_balance=0,
                                  max_balance=20000,
                                  account_type="credit",
                                  billing_start_date_YYYYMMDD='20000102',
                                  interest_type=None,
                                  apr=0.05,
                                  interest_cadence='Monthly',
                                  minimum_payment=40,
                                  previous_statement_balance=0,
                                  current_statement_balance=0,
                                  principal_balance=None,
                                  interest_balance=None
                                  )

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000102', end_date_YYYYMMDD='20000102', priority=2,
                                 cadence='once', amount=0, memo='test memo',
                                 deferrable=False,
                                 partial_payment_allowed=False)

        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=1)
        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=2)
        memo_rule_set.addMemoRule(memo_regex='test memo', account_from='Credit', account_to=None, transaction_priority=2)

        milestone_set = MilestoneSet.MilestoneSet([], [], [])

        with pytest.raises(ValueError):
            ExpenseForecast.ExpenseForecast(account_set,budget_set,memo_rule_set,start_date_YYYYMMDD,end_date_YYYYMMDD,milestone_set)

        # expected_result_df = pd.DataFrame({
        #     'Date': ['20000101', '20000102', '20000103'],
        #     'Checking': [1000, 1000, 1000],
        #     'Credit: Curr Stmt Bal': [0, 0, 0],
        #     'Credit: Prev Stmt Bal': [0, 0, 0],
        #     'Memo': ['', '', '']
        # })
        # expected_result_df.Date = [datetime.datetime.strptime(x, '%Y%m%d') for x in
        #                            expected_result_df.Date]
        #
        # E = self.compute_forecast_and_actual_vs_expected(account_set,
        #                                                  budget_set,
        #                                                  memo_rule_set,
        #                                                  start_date_YYYYMMDD,
        #                                                  end_date_YYYYMMDD,
        #                                                  expected_result_df,
        #                                                  test_description)



    # def test_get_available_balances(self):
    #
    #     start_date_YYYYMMDD = '20230325'
    #     end_date_YYYYMMDD = '20231231'
    #
    #     current_checking_balance = 5000
    #     current_credit_previous_statement_balance = 0
    #     current_credit_current_statement_balance = 0
    #
    #     account_set = copy.deepcopy(self.account_set)
    #     budget_set = copy.deepcopy(self.budget_set)
    #     memo_rule_set = copy.deepcopy(self.memo_rule_set)
    #     milestone_set = copy.deepcopy(self.milestone_set)
    #
    #     account_set.createAccount(name='Checking',
    #                               balance=current_checking_balance,
    #                               min_balance=0,
    #                               max_balance=float('Inf'),
    #                               account_type="checking")
    #
    #     account_set.createAccount(name='Credit',
    #                               balance=current_credit_current_statement_balance,
    #                               min_balance=0,
    #                               max_balance=20000,
    #                               account_type="credit",
    #                               billing_start_date_YYYYMMDD='20230103',
    #                               interest_type='Compound',
    #                               apr=0.2824,
    #                               interest_cadence='Monthly',
    #                               minimum_payment=40,
    #                               previous_statement_balance=current_credit_previous_statement_balance,
    #                               principal_balance=None,
    #                               interest_balance=None
    #                               )
    #
    #     account_set.createAccount(name='Loan A',
    #                               balance=4746.18,
    #                               min_balance=0,
    #                               max_balance=float("inf"),
    #                               account_type="loan",
    #                               billing_start_date_YYYYMMDD='20230903',
    #                               interest_type='simple',
    #                               apr=0.0466,
    #                               interest_cadence='daily',
    #                               minimum_payment=50,
    #                               previous_statement_balance=None,
    #                               principal_balance=4746.18,
    #                               interest_balance=0
    #                               )
    #
    #     account_set.createAccount(name='Loan B',
    #                               balance=1919.55,
    #                               min_balance=0,
    #                               max_balance=float("inf"),
    #                               account_type="loan",
    #                               billing_start_date_YYYYMMDD='20230903',
    #                               interest_type='simple',
    #                               apr=0.0429,
    #                               interest_cadence='daily',
    #                               minimum_payment=50,
    #                               previous_statement_balance=None,
    #                               principal_balance=1919.55,
    #                               interest_balance=0
    #                               )
    #
    #     account_set.createAccount(name='Loan C',
    #                               balance=4726.68,
    #                               min_balance=0,
    #                               max_balance=float("inf"),
    #                               account_type="loan",
    #                               billing_start_date_YYYYMMDD='20230903',
    #                               interest_type='simple',
    #                               apr=0.0429,
    #                               interest_cadence='daily',
    #                               minimum_payment=50,
    #                               previous_statement_balance=None,
    #                               principal_balance=4726.68,
    #                               interest_balance=0
    #                               )
    #
    #     account_set.createAccount(name='Loan D',
    #                               balance=1823.31,
    #                               min_balance=0,
    #                               max_balance=float("inf"),
    #                               account_type="loan",
    #                               billing_start_date_YYYYMMDD='20230903',
    #                               interest_type='simple',
    #                               apr=0.0376,
    #                               interest_cadence='daily',
    #                               minimum_payment=50,
    #                               previous_statement_balance=None,
    #                               principal_balance=1823.31,
    #                               interest_balance=0
    #                               )
    #
    #     account_set.createAccount(name='Loan E',
    #                               balance=3359.17,
    #                               min_balance=0,
    #                               max_balance=float("inf"),
    #                               account_type="loan",
    #                               billing_start_date_YYYYMMDD='20230903',
    #                               interest_type='simple',
    #                               apr=0.0376,
    #                               interest_cadence='daily',
    #                               minimum_payment=50,
    #                               previous_statement_balance=None,
    #                               principal_balance=3359.17,
    #                               interest_balance=0
    #                               )
    #   print(account_set.getAvailableBalances()) #pass by manual inspection


    def test_str(self):
        start_date_YYYYMMDD = '20000101'
        end_date_YYYYMMDD = '20000103'

        account_set = AccountSet.AccountSet([])
        budget_set = BudgetSet.BudgetSet([])
        memo_rule_set = MemoRuleSet.MemoRuleSet([])

        account_set.createAccount(name='Checking',
                                  balance=1000,
                                  min_balance=0,
                                  max_balance=float('Inf'),
                                  account_type="checking",
                                  primary_checking_ind=True)

        account_set.createAccount(name='Credit',
                                  balance=0,
                                  min_balance=0,
                                  max_balance=20000,
                                  account_type="credit",
                                  billing_start_date_YYYYMMDD='20000102',
                                  interest_type=None,
                                  apr=0.05,
                                  interest_cadence='Monthly',
                                  minimum_payment=40,
                                  previous_statement_balance=0,
                                  current_statement_balance=0,
                                  principal_balance=None,
                                  interest_balance=None
                                  )

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000101', end_date_YYYYMMDD='20000103', priority=1,
                                 cadence='daily', amount=0, memo='dummy memo',
                                 deferrable=False,
                                 partial_payment_allowed=False)

        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=1)

        expected_result_df = pd.DataFrame({
            'Date': ['20000101', '20000102', '20000103'],
            'Checking': [1000, 0, 0],
            'Credit: Curr Stmt Bal': [0, 0, 0],
            'Credit: Prev Stmt Bal': [0, 0, 0],
            'Memo': ['', '', '']
        })
        expected_result_df.Date = [datetime.datetime.strptime(x, '%Y%m%d') for x in
                                   expected_result_df.Date]

        milestone_set = MilestoneSet.MilestoneSet([], [], [])

        E = ExpenseForecast.ExpenseForecast(account_set, budget_set, memo_rule_set, start_date_YYYYMMDD,
                                            end_date_YYYYMMDD, milestone_set)

        str(E)

        E.runForecast()

        str(E)

    def test_initialize_forecast_from_excel_not_yet_run(self):
        start_date_YYYYMMDD = '20000101'
        end_date_YYYYMMDD = '20000105'

        A = AccountSet.AccountSet(
            checking_acct_list(2000) + credit_acct_list(100, 100, 0.01) + non_trivial_loan('test loan', 100, 0, 0.01))

        B = BudgetSet.BudgetSet(
            [BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 100, 'p1 daily txn 1/2/00', False, False),
             BudgetItem.BudgetItem('20000103', '20000103', 2, 'once', 100, 'p2 daily txn 1/3/00', False, False),
             BudgetItem.BudgetItem('20000104', '20000104', 3, 'once', 100, 'p3 daily txn 1/4/00', False, False),
             BudgetItem.BudgetItem('20010101', '20010101', 3, 'once', 100, 'specific regex 2', False, False)
             ]
        )
        M = MemoRuleSet.MemoRuleSet([MemoRule.MemoRule(memo_regex='.*',
                                                       account_from='Checking',
                                                       account_to=None,
                                                       transaction_priority=1),
                                     MemoRule.MemoRule(memo_regex='.*',
                                                       account_from='Checking',
                                                       account_to=None,
                                                       transaction_priority=2),
                                     MemoRule.MemoRule(memo_regex='.*',
                                                       account_from='Checking',
                                                       account_to=None,
                                                       transaction_priority=3)
                                     ])

        MS = MilestoneSet.MilestoneSet( [], [], [])
        MS.addAccountMilestone('test account milestone 1', 'Credit', 160, 160)  # doesnt happen
        MS.addAccountMilestone('test account milestone 2', 'Checking', 0, 100)  # does happen

        MS.addMemoMilestone('test memo milestone 1', 'p2 daily txn 1/3/00')  # does happen
        MS.addMemoMilestone('test memo milestone 2', 'specific regex 2')  # doesnt happen

        AM1 = AccountMilestone.AccountMilestone('test account milestone 1', 'Credit', 160, 160)  # does happen
        AM2 = AccountMilestone.AccountMilestone('test account milestone 2', 'Checking', 0, 100)  # doesnt happen

        MM1 = MemoMilestone.MemoMilestone('test memo milestone 1', 'p2 daily txn 1/3/00')  # does happen
        MM2 = MemoMilestone.MemoMilestone('test memo milestone 2', 'specific regex 2')  # doesnt happen

        MS.addCompositeMilestone('test composite milestone 1', [AM1], [MM1])  # does happen
        MS.addCompositeMilestone('test composite milestone 2', [AM2], [MM2])  # doesnt happen

        E1 = ExpenseForecast.ExpenseForecast(A, B, M, start_date_YYYYMMDD, end_date_YYYYMMDD, MS)

        # E1.runForecast()  # Forecast_028363.html
        # E1.appendSummaryLines()
        E1.to_excel('./out/')  # ./out/Forecast_059039.xlsx

        E2_list = ExpenseForecast.initialize_from_excel_file('./out/Forecast_'+str(E1.unique_id)+'.xlsx')
        E2 = E2_list[0]

        print('############################################')
        print(E1.milestone_set.to_json())
        print('############################################')
        print(E2.milestone_set.to_json())
        print('############################################')

        # before runForecast
        assert E1.unique_id == E2.unique_id
        # assert E1.start_ts == E2.start_ts
        # assert E1.end_ts == E2.end_ts
        assert E1.start_date_YYYYMMDD == E2.start_date_YYYYMMDD
        assert E1.end_date_YYYYMMDD == E2.end_date_YYYYMMDD
        assert E1.initial_account_set.getAccounts().to_string() == E2.initial_account_set.getAccounts().to_string()
        assert E1.initial_budget_set.getBudgetItems().to_string() == E2.initial_budget_set.getBudgetItems().to_string()
        assert E1.initial_memo_rule_set.getMemoRules().to_string() == E2.initial_memo_rule_set.getMemoRules().to_string()
        assert E1.milestone_set.to_json() == E2.milestone_set.to_json()
    #
    # def test_initialize_from_excel_already_run__no_append(self):
    #     start_date_YYYYMMDD = '20000101'
    #     end_date_YYYYMMDD = '20000105'
    #
    #     A = AccountSet.AccountSet(
    #         checking_acct_list(2000) + credit_acct_list(100, 100, 0.01) + non_trivial_loan('test loan', 100, 0, 0.01))
    #
    #     B = BudgetSet.BudgetSet(
    #         [BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 100, 'p1 daily txn 1/2/00', False, False),
    #          BudgetItem.BudgetItem('20000103', '20000103', 2, 'once', 100, 'p2 daily txn 1/3/00', False, False),
    #          BudgetItem.BudgetItem('20000104', '20000104', 3, 'once', 100, 'p3 daily txn 1/4/00', False, False),
    #          BudgetItem.BudgetItem('20010101', '20010101', 3, 'once', 100, 'specific regex 2', False, False)
    #          ]
    #     )
    #     M = MemoRuleSet.MemoRuleSet([MemoRule.MemoRule(memo_regex='.*',
    #                                                    account_from='Checking',
    #                                                    account_to=None,
    #                                                    transaction_priority=1),
    #                                  MemoRule.MemoRule(memo_regex='.*',
    #                                                    account_from='Checking',
    #                                                    account_to=None,
    #                                                    transaction_priority=2),
    #                                  MemoRule.MemoRule(memo_regex='.*',
    #                                                    account_from='Checking',
    #                                                    account_to=None,
    #                                                    transaction_priority=3)
    #                                  ])
    #
    #     MS = MilestoneSet.MilestoneSet( [], [], [])
    #     MS.addAccountMilestone('test account milestone 1', 'Credit', 160, 160)  # doesnt happen
    #     MS.addAccountMilestone('test account milestone 2', 'Checking', 0, 100)  # does happen
    #
    #     MS.addMemoMilestone('test memo milestone 1', 'p2 daily txn 1/3/00')  # does happen
    #     MS.addMemoMilestone('test memo milestone 2', 'specific regex 2')  # doesnt happen
    #
    #     AM1 = AccountMilestone.AccountMilestone('test account milestone 1', 'Credit', 160, 160)  # does happen
    #     AM2 = AccountMilestone.AccountMilestone('test account milestone 2', 'Checking', 0, 100)  # doesnt happen
    #
    #     MM1 = MemoMilestone.MemoMilestone('test memo milestone 1', 'p2 daily txn 1/3/00')  # does happen
    #     MM2 = MemoMilestone.MemoMilestone('test memo milestone 2', 'specific regex 2')  # doesnt happen
    #
    #     MS.addCompositeMilestone('test composite milestone 1', [AM1], [MM1])  # does happen
    #     MS.addCompositeMilestone('test composite milestone 2', [AM2], [MM2])  # doesnt happen
    #
    #     E1 = ExpenseForecast.ExpenseForecast(A, B, M, start_date_YYYYMMDD, end_date_YYYYMMDD, MS)
    #
    #     E1.runForecast()  # Forecast_028363.html
    #     E1.to_excel('./out')  # ./out/Forecast_028363.xlsx
    #
    #     E2_list = ExpenseForecast.initialize_from_excel_file('./out/Forecast_059039.xlsx')
    #     E2 = E2_list[0]
    #
    #     # before runForecast
    #     assert E1.unique_id == E2.unique_id
    #     assert E1.start_ts == E2.start_ts
    #     assert E1.end_ts == E2.end_ts
    #     assert E1.start_date_YYYYMMDD == E2.start_date_YYYYMMDD
    #     assert E1.end_date_YYYYMMDD == E2.end_date_YYYYMMDD
    #     assert E1.initial_account_set.getAccounts().to_string() == E2.initial_account_set.getAccounts().to_string()
    #     assert E1.initial_budget_set.getBudgetItems().to_string() == E2.initial_budget_set.getBudgetItems().to_string()
    #     assert E1.initial_memo_rule_set.getMemoRules().to_string() == E2.initial_memo_rule_set.getMemoRules().to_string()
    #     assert E1.milestone_set.to_json() == E2.milestone_set.to_json()
    #
    #     # after runForecast
    #     assert str(E1.account_milestone_results) == str(E2.account_milestone_results)
    #     assert str(E1.memo_milestone_results) == str(E2.memo_milestone_results)
    #     assert str(E1.composite_milestone_results) == str(E2.composite_milestone_results)
    #
    #     for index, row in E1.skipped_df.iterrows():
    #         for c_index in range(0, E1.skipped_df.shape[1]):
    #             assert E1.skipped_df.iloc[index, c_index] == E2.skipped_df.iloc[index, c_index]
    #
    #     for index, row in E1.deferred_df.iterrows():
    #         for c_index in range(0, E1.deferred_df.shape[1]):
    #             assert E1.deferred_df.iloc[index, c_index] == E2.deferred_df.iloc[index, c_index]
    #
    #     for index, row in E1.confirmed_df.iterrows():
    #         for c_index in range(0, E1.confirmed_df.shape[1]):
    #             assert E1.confirmed_df.iloc[index, c_index] == E2.confirmed_df.iloc[index, c_index]
    #
    #     for index, row in E1.forecast_df.iterrows():
    #         for c_index in range(0, E1.forecast_df.shape[1]):
    #             if c_index != 0 and c_index != E1.forecast_df.columns.tolist().index('Memo'):
    #                 assert round(E1.forecast_df.iloc[index, c_index], 2) == round(E2.forecast_df.iloc[index, c_index],2)
    #             else:
    #                 try:
    #                     assert E1.forecast_df.iloc[index, c_index] == E2.forecast_df.iloc[index, c_index]
    #                 except Exception as e:
    #                     print(index,c_index)
    #                     print(e.args)
    #                     raise e

    def test_initialize_forecast_from_excel_already_run(self):
        start_date_YYYYMMDD = '20000101'
        end_date_YYYYMMDD = '20000105'

        A = AccountSet.AccountSet(
            checking_acct_list(2000) + credit_acct_list(100, 100, 0.01) + non_trivial_loan('test loan', 100, 0, 0.01))

        B = BudgetSet.BudgetSet(
            [BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 100, 'p1 daily txn 1/2/00', False, False),
             BudgetItem.BudgetItem('20000103', '20000103', 2, 'once', 100, 'p2 daily txn 1/3/00', False, False),
             BudgetItem.BudgetItem('20000104', '20000104', 3, 'once', 100, 'p3 daily txn 1/4/00', False, False),
             BudgetItem.BudgetItem('20010101', '20010101', 3, 'once', 100, 'specific regex 2', False, False)
             ]
        )
        M = MemoRuleSet.MemoRuleSet([MemoRule.MemoRule(memo_regex='.*',
                                                       account_from='Checking',
                                                       account_to=None,
                                                       transaction_priority=1),
                                     MemoRule.MemoRule(memo_regex='.*',
                                                       account_from='Checking',
                                                       account_to=None,
                                                       transaction_priority=2),
                                     MemoRule.MemoRule(memo_regex='.*',
                                                       account_from='Checking',
                                                       account_to=None,
                                                       transaction_priority=3)
                                     ])

        MS = MilestoneSet.MilestoneSet( [], [], [])
        MS.addAccountMilestone('test account milestone 1', 'Credit', 160, 160)  # doesnt happen
        MS.addAccountMilestone('test account milestone 2', 'Checking', 0, 100)  # does happen

        MS.addMemoMilestone('test memo milestone 1', 'p2 daily txn 1/3/00')  # does happen
        MS.addMemoMilestone('test memo milestone 2', 'specific regex 2')  # doesnt happen

        AM1 = AccountMilestone.AccountMilestone('test account milestone 1', 'Credit', 160, 160)  # does happen
        AM2 = AccountMilestone.AccountMilestone('test account milestone 2', 'Checking', 0, 100)  # doesnt happen

        MM1 = MemoMilestone.MemoMilestone('test memo milestone 1', 'p2 daily txn 1/3/00')  # does happen
        MM2 = MemoMilestone.MemoMilestone('test memo milestone 2', 'specific regex 2')  # doesnt happen

        MS.addCompositeMilestone('test composite milestone 1', [AM1], [MM1])  # does happen
        MS.addCompositeMilestone('test composite milestone 2', [AM2], [MM2])  # doesnt happen

        E1 = ExpenseForecast.ExpenseForecast(A, B, M, start_date_YYYYMMDD, end_date_YYYYMMDD, MS)

        E1.runForecast()  # Forecast_028363.html
        E1.to_excel('./out')  # ./out/Forecast_028363.xlsx

        E2_list = ExpenseForecast.initialize_from_excel_file('./out/Forecast_'+str(E1.unique_id)+'.xlsx')
        E2 = E2_list[0]

        # before runForecast
        assert E1.unique_id == E2.unique_id
        assert E1.start_ts == E2.start_ts
        assert E1.end_ts == E2.end_ts
        assert E1.start_date_YYYYMMDD == E2.start_date_YYYYMMDD
        assert E1.end_date_YYYYMMDD == E2.end_date_YYYYMMDD
        assert E1.initial_account_set.getAccounts().to_string() == E2.initial_account_set.getAccounts().to_string()
        assert E1.initial_budget_set.getBudgetItems().to_string() == E2.initial_budget_set.getBudgetItems().to_string()
        assert E1.initial_memo_rule_set.getMemoRules().to_string() == E2.initial_memo_rule_set.getMemoRules().to_string()
        assert E1.milestone_set.to_json() == E2.milestone_set.to_json()

        # after runForecast
        assert str(E1.account_milestone_results) == str(E2.account_milestone_results)
        assert str(E1.memo_milestone_results) == str(E2.memo_milestone_results)
        assert str(E1.composite_milestone_results) == str(E2.composite_milestone_results)

        for index, row in E1.skipped_df.iterrows():
            for c_index in range(0, E1.skipped_df.shape[1]):
                assert E1.skipped_df.iloc[index, c_index] == E2.skipped_df.iloc[index, c_index]

        for index, row in E1.deferred_df.iterrows():
            for c_index in range(0, E1.deferred_df.shape[1]):
                assert E1.deferred_df.iloc[index, c_index] == E2.deferred_df.iloc[index, c_index]

        for index, row in E1.confirmed_df.iterrows():
            for c_index in range(0, E1.confirmed_df.shape[1]):
                assert E1.confirmed_df.iloc[index, c_index] == E2.confirmed_df.iloc[index, c_index]

        # after appendSummaryLines
        # e.g. "Marginal Interest":0.0,"Net Gain":0,"Net Loss":0,"Net Worth":1700.0,"Loan Total":100.0,"CC Debt Total":200.0,"Liquid Total":2000.0,
        for index, row in E1.forecast_df.iterrows():
            for c_index in range(0, E1.forecast_df.shape[1]):
                if c_index != 0 and c_index != E1.forecast_df.columns.tolist().index('Memo'):
                    assert round(E1.forecast_df.iloc[index, c_index], 2) == round(E2.forecast_df.iloc[index, c_index],
                                                                                  2)
                else:
                    assert E1.forecast_df.iloc[index, c_index] == E2.forecast_df.iloc[index, c_index]

    def test_initialize_forecast_from_json_not_yet_run(self):
        start_date_YYYYMMDD = '20000101'
        end_date_YYYYMMDD = '20000105'

        A = AccountSet.AccountSet(
            checking_acct_list(2000) + credit_acct_list(100, 100, 0.01) + non_trivial_loan('test loan', 100, 0, 0.01))

        B = BudgetSet.BudgetSet(
            [BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 100, 'p1 daily txn 1/2/00', False, False),
             BudgetItem.BudgetItem('20000103', '20000103', 2, 'once', 100, 'p2 daily txn 1/3/00', False, False),
             BudgetItem.BudgetItem('20000104', '20000104', 3, 'once', 100, 'p3 daily txn 1/4/00', False, False)
             ]
        )
        M = MemoRuleSet.MemoRuleSet([MemoRule.MemoRule(memo_regex='.*',
                                                       account_from='Checking',
                                                       account_to=None,
                                                       transaction_priority=1),
                                     MemoRule.MemoRule(memo_regex='.*',
                                                       account_from='Checking',
                                                       account_to=None,
                                                       transaction_priority=2),
                                     MemoRule.MemoRule(memo_regex='.*',
                                                       account_from='Checking',
                                                       account_to=None,
                                                       transaction_priority=3)
                                     ])

        MS = MilestoneSet.MilestoneSet( [], [], [])
        MS.addAccountMilestone('test account milestone 1', 'Credit', 160, 160)  # doesnt happen
        MS.addAccountMilestone('test account milestone 2', 'Checking', 0, 100)  # does happen

        MS.addMemoMilestone('test memo milestone 1', 'p2 daily txn 1/3/00')  # does happen
        MS.addMemoMilestone('test memo milestone 2', 'specific regex 2')  # doesnt happen

        AM1 = AccountMilestone.AccountMilestone('test account milestone 1', 'Credit', 160, 160)  # does happen
        AM2 = AccountMilestone.AccountMilestone('test account milestone 2', 'Checking', 0, 100)  # doesnt happen

        MM1 = MemoMilestone.MemoMilestone('test memo milestone 1', 'p2 daily txn 1/3/00')  # does happen
        MM2 = MemoMilestone.MemoMilestone('test memo milestone 2', 'specific regex 2')  # doesnt happen

        MS.addCompositeMilestone('test composite milestone 1', [AM1], [MM1])  # does happen
        MS.addCompositeMilestone('test composite milestone 2', [AM2], [MM2])  # doesnt happen

        E1 = ExpenseForecast.ExpenseForecast(A, B, M, start_date_YYYYMMDD, end_date_YYYYMMDD, MS,
                                             forecast_set_name='Forecast Set Name',
                                             forecast_name='Forecast Name'
                                             )

        #E1.runForecast()  # Forecast_028363.html
        E1.writeToJSONFile('./out/')  # ./out/ForecastResult_010783.json
        # print(E1.to_json())

        E2  = ExpenseForecast.initialize_from_json_file('./out/ForecastResult_'+str(E1.unique_id)+'.json')

        # before runForecast
        assert E1.unique_id == E2.unique_id
        # assert E1.start_ts == E2.start_tsx
        # assert E1.end_ts == E2.end_ts
        assert E1.start_date_YYYYMMDD == E2.start_date_YYYYMMDD
        assert E1.end_date_YYYYMMDD == E2.end_date_YYYYMMDD
        assert E1.initial_account_set.getAccounts().to_string() == E2.initial_account_set.getAccounts().to_string()
        assert E1.initial_budget_set.getBudgetItems().to_string() == E2.initial_budget_set.getBudgetItems().to_string()
        assert E1.initial_memo_rule_set.getMemoRules().to_string() == E2.initial_memo_rule_set.getMemoRules().to_string()
        assert E1.milestone_set.to_json() == E2.milestone_set.to_json()

        # after runForecast
        # assert str(E1.account_milestone_results) == str(E2.account_milestone_results)
        # assert str(E1.memo_milestone_results) == str(E2.memo_milestone_results)
        # assert str(E1.composite_milestone_results) == str(E2.composite_milestone_results)
        #
        # for index, row in E1.skipped_df.iterrows():
        #     for c_index in range(0, E1.skipped_df.shape[1]):
        #         assert E1.skipped_df.iloc[index, c_index] == E2.skipped_df.iloc[index, c_index]
        #
        # for index, row in E1.deferred_df.iterrows():
        #     for c_index in range(0, E1.deferred_df.shape[1]):
        #         assert E1.deferred_df.iloc[index, c_index] == E2.deferred_df.iloc[index, c_index]
        #
        # for index, row in E1.confirmed_df.iterrows():
        #     for c_index in range(0, E1.confirmed_df.shape[1]):
        #         assert E1.confirmed_df.iloc[index, c_index] == E2.confirmed_df.iloc[index, c_index]
        #
        # # after appendSummaryLines
        # # e.g. "Marginal Interest":0.0,"Net Gain":0,"Net Loss":0,"Net Worth":1700.0,"Loan Total":100.0,"CC Debt Total":200.0,"Liquid Total":2000.0,
        # for index, row in E1.forecast_df.iterrows():
        #     for c_index in range(0, E1.forecast_df.shape[1]):
        #         if c_index != 0 and c_index != E1.forecast_df.columns.tolist().index('Memo'):
        #             assert round(E1.forecast_df.iloc[index, c_index], 2) == round(E2.forecast_df.iloc[index, c_index],
        #                                                                           2)
        #         else:
        #             assert E1.forecast_df.iloc[index, c_index] == E2.forecast_df.iloc[index, c_index]
    #
    # def test_initialize_from_json_already_run__no_append(self):
    #     start_date_YYYYMMDD = '20000101'
    #     end_date_YYYYMMDD = '20000105'
    #
    #     A = AccountSet.AccountSet(
    #         checking_acct_list(2000) + credit_acct_list(100, 100, 0.01) + non_trivial_loan('test loan', 100, 0, 0.01))
    #
    #     B = BudgetSet.BudgetSet(
    #         [BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 100, 'p1 daily txn 1/2/00', False, False),
    #          BudgetItem.BudgetItem('20000103', '20000103', 2, 'once', 100, 'p2 daily txn 1/3/00', False, False),
    #          BudgetItem.BudgetItem('20000104', '20000104', 3, 'once', 100, 'p3 daily txn 1/4/00', False, False)
    #          ]
    #     )
    #     M = MemoRuleSet.MemoRuleSet([MemoRule.MemoRule(memo_regex='.*',
    #                                                    account_from='Checking',
    #                                                    account_to=None,
    #                                                    transaction_priority=1),
    #                                  MemoRule.MemoRule(memo_regex='.*',
    #                                                    account_from='Checking',
    #                                                    account_to=None,
    #                                                    transaction_priority=2),
    #                                  MemoRule.MemoRule(memo_regex='.*',
    #                                                    account_from='Checking',
    #                                                    account_to=None,
    #                                                    transaction_priority=3)
    #                                  ])
    #
    #     MS = MilestoneSet.MilestoneSet( [], [], [])
    #     MS.addAccountMilestone('test account milestone 1', 'Credit', 160, 160)  # doesnt happen
    #     MS.addAccountMilestone('test account milestone 2', 'Checking', 0, 100)  # does happen
    #
    #     MS.addMemoMilestone('test memo milestone 1', 'p2 daily txn 1/3/00')  # does happen
    #     MS.addMemoMilestone('test memo milestone 2', 'specific regex 2')  # doesnt happen
    #
    #     AM1 = AccountMilestone.AccountMilestone('test account milestone 1', 'Credit', 160, 160)  # does happen
    #     AM2 = AccountMilestone.AccountMilestone('test account milestone 2', 'Checking', 0, 100)  # doesnt happen
    #
    #     MM1 = MemoMilestone.MemoMilestone('test memo milestone 1', 'p2 daily txn 1/3/00')  # does happen
    #     MM2 = MemoMilestone.MemoMilestone('test memo milestone 2', 'specific regex 2')  # doesnt happen
    #
    #     MS.addCompositeMilestone('test composite milestone 1', [AM1], [MM1])  # does happen
    #     MS.addCompositeMilestone('test composite milestone 2', [AM2], [MM2])  # doesnt happen
    #
    #     E1 = ExpenseForecast.ExpenseForecast(A, B, M, start_date_YYYYMMDD, end_date_YYYYMMDD, MS)
    #
    #     E1.runForecast()  # Forecast_028363.html
    #     E1.writeToJSONFile('./out') # ./out/Forecast_028363.json
    #
    #     E2_list = ExpenseForecast.initialize_from_json_file('./out/Forecast_028363.json')
    #     E2 = E2_list[0]
    #
    #     #before runForecast
    #     assert E1.unique_id == E2.unique_id
    #     assert E1.start_ts == E2.start_ts
    #     assert E1.end_ts == E2.end_ts
    #     assert E1.start_date_YYYYMMDD == E2.start_date_YYYYMMDD
    #     assert E1.end_date_YYYYMMDD == E2.end_date_YYYYMMDD
    #     assert E1.initial_account_set.getAccounts().to_string() == E2.initial_account_set.getAccounts().to_string()
    #     assert E1.initial_budget_set.getBudgetItems().to_string() == E2.initial_budget_set.getBudgetItems().to_string()
    #     assert E1.initial_memo_rule_set.getMemoRules().to_string() == E2.initial_memo_rule_set.getMemoRules().to_string()
    #     assert E1.milestone_set.to_json() == E2.milestone_set.to_json()
    #
    #     #after runForecast
    #     assert str(E1.account_milestone_results) == str(E2.account_milestone_results)
    #     assert str(E1.memo_milestone_results) == str(E2.memo_milestone_results)
    #     assert str(E1.composite_milestone_results) == str(E2.composite_milestone_results)
    #
    #     for index, row in E1.skipped_df.iterrows():
    #         for c_index in range(0,E1.skipped_df.shape[1]):
    #             assert E1.skipped_df.iloc[index,c_index] == E2.skipped_df.iloc[index,c_index]
    #
    #     for index, row in E1.deferred_df.iterrows():
    #         for c_index in range(0, E1.deferred_df.shape[1]):
    #             assert E1.deferred_df.iloc[index,c_index] == E2.deferred_df.iloc[index,c_index]
    #
    #     for index, row in E1.confirmed_df.iterrows():
    #         for c_index in range(0, E1.confirmed_df.shape[1]):
    #             assert E1.confirmed_df.iloc[index,c_index] == E2.confirmed_df.iloc[index,c_index]
    #
    #     for index, row in E1.forecast_df.iterrows():
    #         for c_index in range(0, E1.forecast_df.shape[1]):
    #             if c_index != 0 and c_index != (E1.forecast_df.shape[1] - 1):
    #                 assert round(E1.forecast_df.iloc[index,c_index],2) == round(E2.forecast_df.iloc[index,c_index],2)
    #             else:
    #                 assert E1.forecast_df.iloc[index, c_index] == E2.forecast_df.iloc[index, c_index]
    #

    def test_initialize_forecast_from_json_already_run(self):
        start_date_YYYYMMDD = '20000101'
        end_date_YYYYMMDD = '20000105'

        A = AccountSet.AccountSet(
            checking_acct_list(2000) + credit_acct_list(100, 100, 0.01) + non_trivial_loan('test loan', 100, 0, 0.01))

        B = BudgetSet.BudgetSet(
            [BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 100, 'p1 daily txn 1/2/00', False, False),
             BudgetItem.BudgetItem('20000103', '20000103', 2, 'once', 100, 'p2 daily txn 1/3/00', False, False),
             BudgetItem.BudgetItem('20000104', '20000104', 3, 'once', 100, 'p3 daily txn 1/4/00', False, False)
             ]
        )
        M = MemoRuleSet.MemoRuleSet([MemoRule.MemoRule(memo_regex='.*',
                                                       account_from='Checking',
                                                       account_to=None,
                                                       transaction_priority=1),
                                     MemoRule.MemoRule(memo_regex='.*',
                                                       account_from='Checking',
                                                       account_to=None,
                                                       transaction_priority=2),
                                     MemoRule.MemoRule(memo_regex='.*',
                                                       account_from='Checking',
                                                       account_to=None,
                                                       transaction_priority=3)
                                     ])

        MS = MilestoneSet.MilestoneSet( [], [], [])
        MS.addAccountMilestone('test account milestone 1', 'Credit', 160, 160)  # doesnt happen
        MS.addAccountMilestone('test account milestone 2', 'Checking', 0, 100)  # does happen

        MS.addMemoMilestone('test memo milestone 1', 'p2 daily txn 1/3/00')  # does happen
        MS.addMemoMilestone('test memo milestone 2', 'specific regex 2')  # doesnt happen

        AM1 = AccountMilestone.AccountMilestone('test account milestone 1', 'Credit', 160, 160)  # does happen
        AM2 = AccountMilestone.AccountMilestone('test account milestone 2', 'Checking', 0, 100)  # doesnt happen

        MM1 = MemoMilestone.MemoMilestone('test memo milestone 1', 'p2 daily txn 1/3/00')  # does happen
        MM2 = MemoMilestone.MemoMilestone('test memo milestone 2', 'specific regex 2')  # doesnt happen

        MS.addCompositeMilestone('test composite milestone 1', [AM1], [MM1])  # does happen
        MS.addCompositeMilestone('test composite milestone 2', [AM2], [MM2])  # doesnt happen

        E1 = ExpenseForecast.ExpenseForecast(A, B, M, start_date_YYYYMMDD, end_date_YYYYMMDD, MS)

        E1.runForecast()  # Forecast_028363.html
        E1.writeToJSONFile('./out/')  # ./out/Forecast_028363.json

        E2 = ExpenseForecast.initialize_from_json_file('./out/ForecastResult_'+str(E1.unique_id)+'.json')


        # before runForecast
        assert E1.unique_id == E2.unique_id
        assert E1.start_ts == E2.start_ts
        assert E1.end_ts == E2.end_ts
        assert E1.start_date_YYYYMMDD == E2.start_date_YYYYMMDD
        assert E1.end_date_YYYYMMDD == E2.end_date_YYYYMMDD
        assert E1.initial_account_set.getAccounts().to_string() == E2.initial_account_set.getAccounts().to_string()
        assert E1.initial_budget_set.getBudgetItems().to_string() == E2.initial_budget_set.getBudgetItems().to_string()
        assert E1.initial_memo_rule_set.getMemoRules().to_string() == E2.initial_memo_rule_set.getMemoRules().to_string()
        assert E1.milestone_set.to_json() == E2.milestone_set.to_json()

        # after runForecast
        assert str(E1.account_milestone_results) == str(E2.account_milestone_results)
        assert str(E1.memo_milestone_results) == str(E2.memo_milestone_results)
        assert str(E1.composite_milestone_results) == str(E2.composite_milestone_results)

        for index, row in E1.skipped_df.iterrows():
            for c_index in range(0, E1.skipped_df.shape[1]):
                assert E1.skipped_df.iloc[index, c_index] == E2.skipped_df.iloc[index, c_index]

        for index, row in E1.deferred_df.iterrows():
            for c_index in range(0, E1.deferred_df.shape[1]):
                assert E1.deferred_df.iloc[index, c_index] == E2.deferred_df.iloc[index, c_index]

        for index, row in E1.confirmed_df.iterrows():
            for c_index in range(0, E1.confirmed_df.shape[1]):
                assert E1.confirmed_df.iloc[index, c_index] == E2.confirmed_df.iloc[index, c_index]

        # after appendSummaryLines
        # e.g. "Marginal Interest":0.0,"Net Gain":0,"Net Loss":0,"Net Worth":1700.0,"Loan Total":100.0,"CC Debt Total":200.0,"Liquid Total":2000.0,
        for index, row in E1.forecast_df.iterrows():
            for c_index in range(0, E1.forecast_df.shape[1]):
                if c_index != 0 and c_index != E1.forecast_df.columns.tolist().index('Memo'):
                    assert round(E1.forecast_df.iloc[index, c_index], 2) == round(E2.forecast_df.iloc[index, c_index],2)
                else:
                    assert E1.forecast_df.iloc[index, c_index] == E2.forecast_df.iloc[index, c_index]



    def test_run_forecast_from_json_at_path(self):

        sd = '20000101'
        ed = '20000103'

        A = AccountSet.AccountSet(checking_acct_list(2000) + credit_acct_list(100,100,0.01) + non_trivial_loan('test loan',100,0,0.01))
        B = BudgetSet.BudgetSet(
            [BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 100, 'p1 daily txn 1/2/00', False, False),
             BudgetItem.BudgetItem('20000102', '20000102', 2, 'once', 100, 'p2 daily txn 1/2/00', False, False),
             BudgetItem.BudgetItem('20000104', '20000104', 3, 'once', 100, 'p3 daily txn 1/4/00', False, False)
             ]
        )
        M = MemoRuleSet.MemoRuleSet([MemoRule.MemoRule(memo_regex='.*',
                                                   account_from='Checking',
                                                   account_to=None,
                                                   transaction_priority=1),
                                 MemoRule.MemoRule(memo_regex='.*',
                                                   account_from='Checking',
                                                   account_to=None,
                                                   transaction_priority=2),
                                 MemoRule.MemoRule(memo_regex='.*',
                                                   account_from='Checking',
                                                   account_to=None,
                                                   transaction_priority=3)
                                 ])
        MS = MilestoneSet.MilestoneSet( [], [], [])
        MS.addAccountMilestone('test account milestone','Checking',0,100)
        MS.addMemoMilestone('test memo milestone','specific regex')
        MS.addAccountMilestone('test account milestone 2', 'Checking', 0, 200)
        MS.addMemoMilestone('test memo milestone 2', 'specific regex 2')

        AM = AccountMilestone.AccountMilestone('test account milestone 2','Checking',0,100)
        MM = MemoMilestone.MemoMilestone('test memo milestone 2','other specific regex')

        MS.addCompositeMilestone('test composite milestone',[AM],[MM])
        MS.addCompositeMilestone('test composite milestone 1', [AM], [MM])

        E1 = ExpenseForecast.ExpenseForecast(A,B,M,sd,ed,MS)
        E1.runForecast()
        with open ('./out/tmp_json_abc123_zzzzz.json','w') as f:
            J = E1.to_json()
            print(J)
            f.write(J)

        E2 = ExpenseForecast.initialize_from_json_file('./out/tmp_json_abc123_zzzzz.json')
        E2.runForecast()

        E1_str_lines = str(E1).split('\n')
        E2_str_lines = str(E2).split('\n')

        comparable_E1_str_lines = []
        for l in E1_str_lines:
            if 'Start timestamp' not in l and 'End timestamp' not in l and 'Forecast__' not in l:
                comparable_E1_str_lines.append(l)

        comparable_E2_str_lines = []
        for l in E2_str_lines:
            if 'Start timestamp' not in l and 'End timestamp' not in l and 'Forecast__' not in l:
                comparable_E2_str_lines.append(l)

        # print('------------------------------------------------------------------------------------')
        # for l in comparable_E1_str_lines:
        #     print(l)
        # print('------------------------------------------------------------------------------------')
        # for l in comparable_E2_str_lines:
        #     print(l)
        # print('------------------------------------------------------------------------------------')

        assert comparable_E1_str_lines == comparable_E2_str_lines

    def test_run_forecast_from_excel_at_path(self):

        sd = '20000101'
        ed = '20000103'

        A = AccountSet.AccountSet(checking_acct_list(2000) + credit_acct_list(100,100,0.01) + non_trivial_loan('test loan',100,0,0.01))
        B = BudgetSet.BudgetSet(
            [BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 100, 'specific regex', False, False),
             BudgetItem.BudgetItem('20000102', '20000102', 2, 'once', 100, 'specific regex 2', False, False),
             BudgetItem.BudgetItem('20000104', '20000104', 3, 'once', 100, 'p3 daily txn 1/4/00', False, False)
             ]
        )
        M = MemoRuleSet.MemoRuleSet([MemoRule.MemoRule(memo_regex='.*',
                                                   account_from='Checking',
                                                   account_to=None,
                                                   transaction_priority=1),
                                 MemoRule.MemoRule(memo_regex='.*',
                                                   account_from='Checking',
                                                   account_to=None,
                                                   transaction_priority=2),
                                 MemoRule.MemoRule(memo_regex='.*',
                                                   account_from='Checking',
                                                   account_to=None,
                                                   transaction_priority=3)
                                 ])
        MS = MilestoneSet.MilestoneSet( [], [], [])
        MS.addAccountMilestone('test account milestone', 'Checking', 0, 100)
        MS.addMemoMilestone('test memo milestone', 'specific regex')
        MS.addAccountMilestone('test account milestone 2', 'Checking', 0, 200)
        MS.addMemoMilestone('test memo milestone 2', 'specific regex 2')

        AM = AccountMilestone.AccountMilestone('test account milestone 2', 'Checking', 0, 100)
        MM = MemoMilestone.MemoMilestone('test memo milestone 2', 'other specific regex')

        MS.addCompositeMilestone('test composite milestone', [AM], [MM])
        MS.addCompositeMilestone('test composite milestone 1', [AM], [MM])

        E1 = ExpenseForecast.ExpenseForecast(A,B,M,sd,ed,MS)

        out_dir = './out/'
        E1.to_excel(out_dir)
        E2 = ExpenseForecast.initialize_from_excel_file(out_dir+'Forecast_'+str(E1.unique_id)+'.xlsx')[0]

        E1.runForecast()
        E2.runForecast()

        E1_str_lines = str(E1).split('\n')
        E2_str_lines = str(E2).split('\n')

        comparable_E1_str_lines = []
        for l in E1_str_lines:
            if 'Start timestamp' not in l and 'End timestamp' not in l and 'Forecast__' not in l:
                comparable_E1_str_lines.append(l)

        comparable_E2_str_lines = []
        for l in E2_str_lines:
            if 'Start timestamp' not in l and 'End timestamp' not in l and 'Forecast__' not in l:
                comparable_E2_str_lines.append(l)

        assert comparable_E1_str_lines == comparable_E2_str_lines
        #
        # #initialize w account rows in reverse order for coverage
        # account_set_df = pd.read_excel(fname, sheet_name='AccountSet')
        # account_set_df = account_set_df.iloc[::-1] #reverse order of rows
        # budget_set_df = pd.read_excel(fname, sheet_name='BudgetSet')
        # memo_rule_set_df = pd.read_excel(fname, sheet_name='MemoRuleSet')
        # choose_one_set_df = pd.read_excel(fname, sheet_name='ChooseOneSet')
        # account_milestones_df = pd.read_excel(fname, sheet_name='AccountMilestones')
        # memo_milestones_df = pd.read_excel(fname, sheet_name='MemoMilestones')
        # composite_account_milestones_df = pd.read_excel(fname, sheet_name='CompositeAccountMilestones')
        # composite_memo_milestones_df = pd.read_excel(fname, sheet_name='CompositeMemoMilestones')
        # config_df = pd.read_excel(fname, sheet_name='config')
        #
        # with pd.ExcelWriter(fname, engine='openpyxl') as writer:
        #     account_set_df.to_excel(writer, sheet_name='AccountSet',index=False)
        #     budget_set_df.to_excel(writer, sheet_name='BudgetSet',index=False)
        #     memo_rule_set_df.to_excel(writer, sheet_name='MemoRuleSet',index=False)
        #     choose_one_set_df.to_excel(writer, sheet_name='ChooseOneSet',index=False)
        #     account_milestones_df.to_excel(writer, sheet_name='AccountMilestones',index=False)
        #     memo_milestones_df.to_excel(writer, sheet_name='MemoMilestones',index=False)
        #     composite_account_milestones_df.to_excel(writer, sheet_name='CompositeAccountMilestones',index=False)
        #     composite_memo_milestones_df.to_excel(writer, sheet_name='CompositeMemoMilestones', index=False)
        #     config_df.to_excel(writer, sheet_name='config',index=False)
        #
        # #E1_reverse = ExpenseForecast.initialize_from_excel_file(fname)

    def test_forecast_longer_than_satisfice(self):
        #if satisfice fails on the second day of the forecast, there is weirdness

        start_date_YYYYMMDD = '20000101'
        end_date_YYYYMMDD = '20000104'

        account_set = AccountSet.AccountSet([])
        budget_set = BudgetSet.BudgetSet([])
        memo_rule_set = MemoRuleSet.MemoRuleSet([])

        account_set.createAccount(name='Checking',
                                  balance=100,
                                  min_balance=0,
                                  max_balance=float('Inf'),
                                  account_type="checking")


        budget_set.addBudgetItem(start_date_YYYYMMDD='20000101', end_date_YYYYMMDD='20000104', priority=1,
                                 cadence='daily', amount=50, memo='dummy memo',
                                 deferrable=False,
                                 partial_payment_allowed=False)

        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=1)

        milestone_set = MilestoneSet.MilestoneSet([],[],[])

        # expected_result_df = pd.DataFrame({
        #     'Date': ['20000101', '20000102', '20000103'],
        #     'Checking': [0, 0, 0],
        #     'Credit: Curr Stmt Bal': [0, 0, 0],
        #     'Credit: Prev Stmt Bal': [0, 0, 0],
        #     'Memo': ['', '', '']
        # })
        # expected_result_df.Date = [datetime.datetime.strptime(x, '%Y%m%d') for x in
        #                            expected_result_df.Date]
        #
        # E = self.compute_forecast_and_actual_vs_expected(account_set,
        #                                                  budget_set,
        #                                                  memo_rule_set,
        #                                                  start_date_YYYYMMDD,
        #                                                  end_date_YYYYMMDD,
        #                                                  expected_result_df,
        #                                                  test_description)

        E = ExpenseForecast.ExpenseForecast(account_set,
                                            budget_set,
                                            memo_rule_set,
                                            start_date_YYYYMMDD,
                                            end_date_YYYYMMDD, milestone_set)

        #todo what should we do here?

        # with pytest.raises(ValueError):
        #     E.runForecast()

        # log_in_color(logger,'white', 'debug', 'Confirmed:')
        # log_in_color(logger,'white', 'debug', E.confirmed_df.to_string())
        # log_in_color(logger,'white', 'debug', 'Deferred:')
        # log_in_color(logger,'white', 'debug', E.deferred_df.to_string())
        # log_in_color(logger,'white', 'debug', 'Skipped:')
        # log_in_color(logger,'white', 'debug', E.skipped_df.to_string())
        # log_in_color(logger,'white', 'debug', 'Forecast:')
        # log_in_color(logger,'white', 'debug', E.forecast_df.to_string())

    ### I'm p sure min loan payments wor kcorrectly and coding this in a way that makes sense is annoying me
    # def test_minimum_loan_payments(self):
    #     test_description = 'test_minimum_loan_payments'
    #
    #     start_date_YYYYMMDD = '20000101'
    #     end_date_YYYYMMDD = '20000103'
    #
    #     account_set = AccountSet.AccountSet([])
    #     budget_set = BudgetSet.BudgetSet([])
    #     memo_rule_set = MemoRuleSet.MemoRuleSet([])
    #
    #     account_set.createAccount(name='Checking',
    #                               balance=2000,
    #                               min_balance=0,
    #                               max_balance=float('Inf'),
    #                               account_type="checking")
    #
    #     account_set.createAccount(name='Loan A',
    #                               balance=5000,
    #                               min_balance=0,
    #                               max_balance=float("inf"),
    #                               account_type="loan",
    #                               billing_start_date_YYYYMMDD='20000102',
    #                               interest_type='simple',
    #                               apr=0.05,
    #                               interest_cadence='daily',
    #                               minimum_payment=50,
    #                               previous_statement_balance=None,
    #                               principal_balance=5000,
    #                               interest_balance=0
    #                               )
    #
    #     account_set.createAccount(name='Loan B',
    #                               balance=5025,
    #                               min_balance=0,
    #                               max_balance=float("inf"),
    #                               account_type="loan",
    #                               billing_start_date_YYYYMMDD='20000102',
    #                               interest_type='simple',
    #                               apr=0.05,
    #                               interest_cadence='daily',
    #                               minimum_payment=50,
    #                               previous_statement_balance=None,
    #                               principal_balance=5000,
    #                               interest_balance=25
    #                               )
    #
    #     account_set.createAccount(name='Loan C',
    #                               balance=5075,
    #                               min_balance=0,
    #                               max_balance=float("inf"),
    #                               account_type="loan",
    #                               billing_start_date_YYYYMMDD='20000102',
    #                               interest_type='simple',
    #                               apr=0.05,
    #                               interest_cadence='daily',
    #                               minimum_payment=50,
    #                               previous_statement_balance=None,
    #                               principal_balance=5000,
    #                               interest_balance=75
    #                               )
    #
    #     account_set.createAccount(name='Loan D',
    #                               balance=50,
    #                               min_balance=0,
    #                               max_balance=float("inf"),
    #                               account_type="loan",
    #                               billing_start_date_YYYYMMDD='20000102',
    #                               interest_type='simple',
    #                               apr=0.12,
    #                               interest_cadence='daily',
    #                               minimum_payment=50,
    #                               previous_statement_balance=None,
    #                               principal_balance=50,
    #                               interest_balance=0
    #                               )
    #
    #     account_set.createAccount(name='Loan E',
    #                               balance=25,
    #                               min_balance=0,
    #                               max_balance=float("inf"),
    #                               account_type="loan",
    #                               billing_start_date_YYYYMMDD='20000102',
    #                               interest_type='simple',
    #                               apr=0.12,
    #                               interest_cadence='daily',
    #                               minimum_payment=50,
    #                               previous_statement_balance=None,
    #                               principal_balance=25,
    #                               interest_balance=0
    #                               )
    #
    #
    #     memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=1)
    #
    #     expected_result_df = pd.DataFrame({
    #         'Date': ['20000101', '20000102', '20000103'],
    #         'Checking': [2000, 1775, 1775],
    #         'Loan A: Principal Balance': [5000,4950 ,4950 ],
    #         'Loan A: Interest': [0, 0.68, 1.36 ],
    #         'Loan B: Principal Balance': [5000,4975 ,4975 ],
    #         'Loan B: Interest': [25, 0.68, 1.36],
    #         'Loan C: Principal Balance': [5000,5000 ,5000 ],
    #         'Loan C: Interest': [75, 25.68, 26.36],
    #         'Loan D: Principal Balance': [50, 0, 0],
    #         'Loan D: Interest': [0, 0, 0],
    #         'Loan E: Principal Balance': [25, 0, 0],
    #         'Loan E: Interest': [0, 0, 0],
    #         'Memo': ['', 'loan min payment (Loan A: Interest -$0.68); loan min payment (Loan A: Principal Balance -$49.32); loan min payment (Loan B: Interest -$25.68);  loan min payment (Loan B: Principal Balance -$24.32); loan min payment (Loan C: Interest -$50.0); loan min payment (Loan D: Interest -$0.02); loan min payment (Loan D: Principal Balance -$49.98); loan min payment (Loan E: Interest -$0.01); loan min payment (Loan E: Principal Balance -$25.0);', '']
    #     })
    #     expected_result_df.Date = [datetime.datetime.strptime(x, '%Y%m%d') for x in
    #                                expected_result_df.Date]
    #
    #     milestone_set = MilestoneSet.MilestoneSet(account_set, budget_set, [], [], [])
    #
    #     E = self.compute_forecast_and_actual_vs_expected(account_set,
    #                                                      budget_set,
    #                                                      memo_rule_set,
    #                                                      start_date_YYYYMMDD,
    #                                                      end_date_YYYYMMDD,
    #                                                      milestone_set,
    #                                                      expected_result_df,
    #                                                      test_description)




    # Interest accruals are calculated before any payments for that day
    #
    # scenarios:
    # 1. daily accrual simple ( 0 APR )
    # 2. daily accrual simple
    # 3. monthly accrual simple
    # 4. daily accrual compound
    # 5. monthly accrual compound
    # 6. daily accrual simple (make a payment)
    # 7. monthly accrual compound (make a payment)
    #
    # each test case can have success defined by a 3 x n matrix

    #

    # scenarios: min payments only
    # 1. minimum payments only
    #
    # scenarios: hard coded payments in excess of minimum
    # 2. extra payment: 1 loan, less than total balance
    # 3. extra payment: 1 loan, more than total balance
    # 4. extra payment: 1 loan, less than total balance when insufficient funds
    # 5. extra payment: 1 loan, more than total balance when insufficient funds

    # 6. extra payment: 2 loans, same interest rate diff balances, less than total balance
    # 7. extra payment: 2 loans, same interest rate diff balances, more than total balance
    # 8. extra payment: 2 loans, same interest rate diff balances, less than total balance when insufficient funds
    # 9. extra payment: 2 loans, same interest rate diff balances, more than total balance when insufficient funds

    # 10. extra payment: 2 loans, diff interest rate diff balances, less than total balance
    # 11. extra payment: 2 loans, diff interest rate diff balances, more than total balance
    # 12. extra payment: 2 loans, diff interest rate diff balances, less than total balance when insufficient funds
    # 13. extra payment: 2 loans, diff interest rate diff balances, more than total balance when insufficient funds

    # 14. extra payment: 5 loans, diff interest rate diff balances, less than total balance
    # 15. extra payment: 5 loans, diff interest rate diff balances, more than total balance
    # 16. extra payment: 5 loans, diff interest rate diff balances, less than total balance when insufficient funds
    # 17. extra payment: 5 loans, diff interest rate diff balances, more than total balance when insufficient funds
    #
    # scenarios: amount = "*"
    # 18. extra payment: 5 loans, diff interest rate diff balances,
    # def test_loan_payments(self):
    #     test_descriptions = [
    #         'Test 1 : ',
    #         'Test 2 : '
    #     ]
    #
    #     account_sets = []
    #     budget_sets = []
    #     memo_rule_sets = []
    #
    #     expected_results = []
    #
    #     start_date_YYYYMMDD = self.start_date_YYYYMMDD
    #     end_date_YYYYMMDD = self.end_date_YYYYMMDD
    #
    #     for i in range(0, len(test_descriptions)):
    #         account_sets.append(copy.deepcopy(self.account_set))
    #         budget_sets.append(copy.deepcopy(self.budget_set))
    #         memo_rule_sets.append(copy.deepcopy(self.memo_rule_set))
    #
    #     ### BEGIN Test Case 1
    #     account_sets[0].addAccount(name='Checking',
    #                                balance=0,
    #                                min_balance=0,
    #                                max_balance=float('Inf'),
    #                                account_type="checking")
    #
    #     account_sets[0].addAccount(name='Loan',
    #                                balance=1000,
    #                                min_balance=0,
    #                                max_balance=float('Inf'),
    #                                account_type="loan",
    #                                billing_start_date_YYYYMMDD='20000102',
    #                                interest_type='Simple',
    #                                apr=0.05,
    #                                interest_cadence='Daily',
    #                                minimum_payment=0,
    #                                previous_statement_balance=None,
    #                                principal_balance=1000,
    #                                interest_balance=0
    #                                )
    #
    #     budget_sets[0].addBudgetItem(start_date_YYYYMMDD='20000101', end_date_YYYYMMDD='20000103', priority=1,
    #                                  cadence='daily', amount=0, memo='dummy memo',
    #                                  deferrable=False)
    #
    #     memo_rule_sets[0].addMemoRule(memo_regex='.*', account_from='Checking', account_to='Loan',
    #                                   transaction_priority=1)
    #
    #     expected_result_0_df = pd.DataFrame({
    #         'Date': ['20000101', '20000102', '20000103'],
    #         'Checking': [0, 0, 0],
    #         'Loan: Principal Balance': [0, 0, 0],
    #         'Loan: Interest': [0, 0, 0],
    #         'Memo': ['', '', '']
    #     })
    #     expected_result_0_df.Date = [datetime.datetime.strptime(x, '%Y%m%d').strftime('%Y-%m-%d') for x in
    #                                  expected_result_0_df.Date]
    #     expected_results.append(expected_result_0_df)
    #     ### END
    #
    #     ### BEGIN Test Case 2
    #     account_sets[1].addAccount(name='Checking',
    #                                balance=0,
    #                                min_balance=0,
    #                                max_balance=float('Inf'),
    #                                account_type="checking")
    #
    #     account_sets[1].addAccount(name='Credit',
    #                                balance=1000,
    #                                min_balance=0,
    #                                max_balance=float('Inf'),
    #                                account_type="credit",
    #                                billing_start_date_YYYYMMDD='20000102',
    #                                interest_type='Compound',
    #                                apr=0.05,
    #                                interest_cadence='Monthly',
    #                                minimum_payment=0,
    #                                previous_statement_balance=0,
    #                                principal_balance=None,
    #                                interest_balance=None
    #                                )
    #
    #     budget_sets[1].addBudgetItem(start_date_YYYYMMDD='20000101', end_date_YYYYMMDD='20000103', priority=1,
    #                                  cadence='daily', amount=0, memo='dummy memo',
    #                                  deferrable=False)
    #
    #     memo_rule_sets[1].addMemoRule(memo_regex='.*', account_from='Checking', account_to='Credit',
    #                                   transaction_priority=1)
    #
    #     expected_result_1_df = pd.DataFrame({
    #         'Date': ['20000101', '20000102', '20000103'],
    #         'Checking': [0, 0, 0],
    #         'Credit: Curr Stmt Bal': [0, 0, 0],
    #         'Credit: Prev Stmt Bal': [0, 0, 0],
    #         'Memo': ['', '', '']
    #     })
    #     expected_result_1_df.Date = [datetime.datetime.strptime(x, '%Y%m%d').strftime('%Y-%m-%d') for x in
    #                                  expected_result_1_df.Date]
    #     expected_results.append(expected_result_1_df)
    #     ### END
    #
    #     # Run the Forecasts
    #     expense_forecasts = []
    #     for i in range(0, len(test_descriptions)):
    #         # print('Running Forecast #'+str(i))
    #
    #         try:
    #             expense_forecasts.append(ExpenseForecast.ExpenseForecast(account_sets[i],
    #                                                                      budget_sets[i],
    #                                                                      memo_rule_sets[i],
    #                                                                      start_date_YYYYMMDD,
    #                                                                      end_date_YYYYMMDD, raise_exceptions=False))
    #
    #             # print(expense_forecasts[i].forecast_df.to_string())
    #         except Exception as e:
    #             print(e)
    #             print(budget_sets[i])
    #             raise e
    #
    #     # Compute Differences
    #     differences = []
    #     for i in range(0, len(test_descriptions)):
    #         try:
    #
    #             print(expense_forecasts[i].forecast_df.columns)
    #             print(expected_results[i].columns)
    #
    #             d = expense_forecasts[i].compute_forecast_difference(expected_results[i],
    #                                                                  label=test_descriptions[i],
    #                                                                  make_plots=True,
    #                                                                  diffs_only=False,
    #                                                                  require_matching_columns=True,
    #                                                                  require_matching_date_range=True,
    #                                                                  append_expected_values=True,
    #                                                                  return_type='dataframe')
    #             d = d.reindex(sorted(d.columns), axis=1)
    #             differences.append(d)
    #
    #         except Exception as e:
    #             print(e)
    #
    #     # Display Results
    #     for i in range(0, len(test_descriptions)):
    #         try:
    #             display_test_result(logger,test_descriptions[i], differences[i])
    #         except Exception as e:
    #             print(e)
    #
    #     # Check Results
    #     for i in range(0, len(test_descriptions)):
    #         self.assertTrue(differences[i].shape[0] == 0)

    def test_interest_types_and_cadences_at_most_monthly(self):
        raise NotImplementedError #i would waste a lot of time every time I ran tests if i implemented it before optimization
        sd = '20000101'
        ed = '20000103'

        A = AccountSet.AccountSet([])

        # compound semiweekly interest
        # compound weekly
        # compound daily

        # simple monthly
        # simple semiweekly
        # simple weekly
        A.createAccount('')


        B = BudgetSet.BudgetSet(
            [
            ])
        M = MemoRuleSet.MemoRuleSet([MemoRule.MemoRule(memo_regex='.*',
                                                       account_from='Checking',
                                                       account_to=None,
                                                       transaction_priority=1)
                                     ])
        MS = MilestoneSet.MilestoneSet( [], [], [])

        E = ExpenseForecast.ExpenseForecast(A, B, M, sd, ed, MS)

    #this test will compute a forecast a year long, so it will take a long time
    #this should be implemented after optimization
    def test_quarter_and_year_long_interest_cadences(self):
        raise NotImplementedError
        sd = '20000101'
        ed = '20000103'

        A = AccountSet.AccountSet(
            checking_acct_list(2000) )
        B = BudgetSet.BudgetSet(
            [
             ]
        )
        M = MemoRuleSet.MemoRuleSet([MemoRule.MemoRule(memo_regex='.*',
                                                       account_from='Checking',
                                                       account_to=None,
                                                       transaction_priority=1)
                                     ])
        MS = MilestoneSet.MilestoneSet( [], [], [])

        E = ExpenseForecast.ExpenseForecast(A, B, M, sd, ed, MS)
    #
    # def test_summary_lines(self):
    #
    #     test_description = 'test_summary_lines'
    #
    #     start_date_YYYYMMDD = '20000101'
    #     end_date_YYYYMMDD = '20000103'
    #
    #     account_set = AccountSet.AccountSet([])
    #     budget_set = BudgetSet.BudgetSet([])
    #     memo_rule_set = MemoRuleSet.MemoRuleSet([])
    #
    #     account_set.createAccount(name='Checking',
    #                               balance=2000,
    #                               min_balance=0,
    #                               max_balance=float('Inf'),
    #                               account_type="checking")
    #
    #     account_set.createAccount('Credit',500,0,10000,'credit','20000102','compound',0.25,'monthly',50,250,None,None)
    #
    #     account_set.createAccount(name='Loan A',
    #                               balance=5000,
    #                               min_balance=0,
    #                               max_balance=float("inf"),
    #                               account_type="loan",
    #                               billing_start_date_YYYYMMDD='20000102',
    #                               interest_type='simple',
    #                               apr=0.05,
    #                               interest_cadence='daily',
    #                               minimum_payment=50,
    #                               previous_statement_balance=None,
    #                               principal_balance=5000,
    #                               interest_balance=0
    #                               )
    #
    #     account_set.createAccount(name='Loan B',
    #                               balance=5025,
    #                               min_balance=0,
    #                               max_balance=float("inf"),
    #                               account_type="loan",
    #                               billing_start_date_YYYYMMDD='20000102',
    #                               interest_type='simple',
    #                               apr=0.05,
    #                               interest_cadence='daily',
    #                               minimum_payment=50,
    #                               previous_statement_balance=None,
    #                               principal_balance=5000,
    #                               interest_balance=25
    #                               )
    #
    #     account_set.createAccount(name='Loan C',
    #                               balance=5075,
    #                               min_balance=0,
    #                               max_balance=float("inf"),
    #                               account_type="loan",
    #                               billing_start_date_YYYYMMDD='20000102',
    #                               interest_type='simple',
    #                               apr=0.05,
    #                               interest_cadence='daily',
    #                               minimum_payment=50,
    #                               previous_statement_balance=None,
    #                               principal_balance=5000,
    #                               interest_balance=75
    #                               )
    #
    #     memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=1)
    #
    #     expected_result_df = pd.DataFrame({
    #         'Date': ['20000101', '20000102', '20000103'],
    #         'Checking': [2000, 1810, 1810],
    #         'Credit: Curr Stmt Bal': [500, 0, 0],
    #         'Credit: Prev Stmt Bal': [250, 714.38, 714.38],
    #         'Loan A: Principal Balance': [5000, 4950, 4950],
    #         'Loan A: Interest': [0, 0.68, 1.36],
    #         'Loan B: Principal Balance': [5000, 4975, 4975],
    #         'Loan B: Interest': [25, 0.68, 1.36],
    #         'Loan C: Principal Balance': [5000, 5000, 5000],
    #         'Loan C: Interest': [75, 25.68, 26.36],
    #         'Memo': ['', '', ''],
    #         'NetWorth': [-13850, -13856.42, -13858.46],
    #         'CCDebtTotal': [750, 714.38, 714.38],
    #         'LiquidTotal': [2000, 1810, 1810],
    #         'LoanTotal': [15100, 14952.04, 14954.08]
    #     })
    #     expected_result_df.Date = [datetime.datetime.strptime(x, '%Y%m%d') for x in
    #                                expected_result_df.Date]
    #
    #     milestone_set = MilestoneSet.MilestoneSet(account_set, budget_set, [], [], [])
    #
    #
    #     E = ExpenseForecast.ExpenseForecast(account_set, budget_set,
    #                                         memo_rule_set,
    #                                         start_date_YYYYMMDD,
    #                                         end_date_YYYYMMDD,
    #                                         milestone_set,
    #                                         raise_exceptions=False)
    #
    #     E.runForecast()
    #     E.appendSummaryLines()
    #
    #     d = E.compute_forecast_difference(copy.deepcopy(E.forecast_df), copy.deepcopy(expected_result_df),
    #                                       label=test_description,
    #                                       make_plots=False,
    #                                       diffs_only=True,
    #                                       require_matching_columns=True,
    #                                       require_matching_date_range=True,
    #                                       append_expected_values=False,
    #                                       return_type='dataframe')
    #
    #     f = E.compute_forecast_difference(copy.deepcopy(E.forecast_df), copy.deepcopy(expected_result_df),
    #                                       label=test_description,
    #                                       make_plots=False,
    #                                       diffs_only=False,
    #                                       require_matching_columns=True,
    #                                       require_matching_date_range=True,
    #                                       append_expected_values=True,
    #                                       return_type='dataframe')
    #
    #     print(f.T.to_string())
    #
    #     try:
    #         display_test_result(logger,test_description, d)
    #     except Exception as e:
    #         raise e
    #
    #     try:
    #         sel_vec = (d.columns != 'Date') & (d.columns != 'Memo')
    #         #on_boilerplate_values__M = np.matrix(d.iloc[:, sel_vec])
    #         non_boilerplate_values__M = np.ndarray(d.iloc[:, sel_vec])
    #
    #         error_ind = round(float(sum(sum(np.square(
    #             non_boilerplate_values__M)).T)), 2)  # this very much DOES NOT SCALE. this is intended for small tests
    #         assert error_ind == 0
    #     except Exception as e:
    #         # print(test_description) #todo use log methods
    #         # print(f.T.to_string())
    #         raise e

    @pytest.mark.parametrize(
        'test_description,account_set,budget_set,memo_rule_set,start_date_YYYYMMDD,end_date_YYYYMMDD,milestone_set,account_milestone_names,expected_milestone_dates',
        [
            (
                    'test_account_milestone',
                    AccountSet.AccountSet(checking_acct_list(10) + credit_acct_list(0, 0, 0.05)),
                    BudgetSet.BudgetSet([BudgetItem.BudgetItem('20000102','20000102',1,'once',10,'test txn')]),
                    MemoRuleSet.MemoRuleSet([MemoRule.MemoRule('.*','Checking',None,1)]),
                    '20000101',
                    '20000103',
                    MilestoneSet.MilestoneSet(
                    [AccountMilestone.AccountMilestone('test account milestone','Checking',0,0)], [], []),
                    ['test account milestone'],
                    ['20000102']
            ),
        ])
    def test_evaluate_account_milestone(self,test_description,account_set,budget_set,memo_rule_set,start_date_YYYYMMDD,end_date_YYYYMMDD,milestone_set,account_milestone_names,expected_milestone_dates):
        E = ExpenseForecast.ExpenseForecast(account_set,budget_set,memo_rule_set,start_date_YYYYMMDD,end_date_YYYYMMDD,milestone_set)
        E.runForecast()
        assert len(account_milestone_names) == len(expected_milestone_dates)

        for i in range(0,len(account_milestone_names)):
            try:
                am_name = account_milestone_names[i]
                assert E.account_milestone_results[am_name] == expected_milestone_dates[i]
            except Exception as e:
                print(str(account_milestone_names[i]) + ' did not match expected milestone date')
                print('Received: '+ str(E.account_milestone_results[am_name]))
                print('Expected: ' + str(expected_milestone_dates[i]))
                raise e

    @pytest.mark.parametrize(
        'test_description,account_set,budget_set,memo_rule_set,start_date_YYYYMMDD,end_date_YYYYMMDD,milestone_set,memo_milestone_names,expected_milestone_dates',
        [
            (
                    'test_memo_milestone',
                    AccountSet.AccountSet(checking_acct_list(10) + credit_acct_list(0, 0, 0.05)),
                    BudgetSet.BudgetSet([BudgetItem.BudgetItem('20000102','20000102',1,'once',10,'memo milestone')]),
                    MemoRuleSet.MemoRuleSet([MemoRule.MemoRule('.*','Checking',None,1)]),
                    '20000101',
                    '20000103',
                    MilestoneSet.MilestoneSet(
                    [], [MemoMilestone.MemoMilestone('test memo milestone','memo milestone')], []),
                    ['test memo milestone'],
                    ['20000102']
            ),
        ])
    def test_evaluate_memo_milestone(self,test_description,account_set,budget_set,memo_rule_set,start_date_YYYYMMDD,end_date_YYYYMMDD,milestone_set,memo_milestone_names,expected_milestone_dates):
        E = ExpenseForecast.ExpenseForecast(account_set,budget_set,memo_rule_set,start_date_YYYYMMDD,end_date_YYYYMMDD,milestone_set)
        E.runForecast()

        assert len(memo_milestone_names) == len(expected_milestone_dates)

        for i in range(0,len(memo_milestone_names)):
            try:
                mm_name = memo_milestone_names[i]
                assert E.memo_milestone_results[mm_name] == expected_milestone_dates[i]
            except Exception as e:
                print(str(memo_milestone_names[i]) + ' did not match expected milestone date')
                print('Received: '+ str(E.memo_milestone_results[mm_name]))
                print('Expected: ' + str(expected_milestone_dates[i]))
                raise e

    @pytest.mark.parametrize(
        'test_description,account_set,budget_set,memo_rule_set,start_date_YYYYMMDD,end_date_YYYYMMDD,milestone_set,composite_milestone_names,expected_milestone_dates',
        [
            (
                    'test composite milestone',
                    AccountSet.AccountSet(checking_acct_list(10) + credit_acct_list(0, 0, 0.05)),
                    BudgetSet.BudgetSet([BudgetItem.BudgetItem('20000102','20000102',1,'once',10,'memo milestone')]),
                    MemoRuleSet.MemoRuleSet([MemoRule.MemoRule('.*','Checking',None,1)]),
                    '20000101',
                    '20000103',
                    MilestoneSet.MilestoneSet(
                        [AccountMilestone.AccountMilestone('test account milestone','Checking',0,0)],
                        [MemoMilestone.MemoMilestone('test memo milestone', 'memo milestone')],
                        [CompositeMilestone.CompositeMilestone('test composite milestone',
                                                               [AccountMilestone.AccountMilestone('test account milestone','Checking',0,0)],
                                                               [MemoMilestone.MemoMilestone('test memo milestone', 'memo milestone')])]),
                    ['test composite milestone'],
                    ['20000102']
            ),
        ])
    def test_evaluate_composite_milestone(self,test_description,account_set,budget_set,memo_rule_set,start_date_YYYYMMDD,end_date_YYYYMMDD,milestone_set,composite_milestone_names,expected_milestone_dates):

        E = ExpenseForecast.ExpenseForecast(account_set, budget_set, memo_rule_set, start_date_YYYYMMDD, end_date_YYYYMMDD,
                                            milestone_set)
        E.runForecast()
        assert len(composite_milestone_names) == len(expected_milestone_dates)

        for i in range(0, len(composite_milestone_names)):
            try:
                cm_name = composite_milestone_names[i]
                assert E.composite_milestone_results[cm_name] == expected_milestone_dates[i]
            except Exception as e:
                print(str(composite_milestone_names[i]) + ' did not match expected milestone date')
                print('Received: ' + str(E.composite_milestone_results[cm_name]))
                print('Expected: ' + str(expected_milestone_dates[i]))
                raise e

    def test_multiple_additional_loan_payments__expect_eliminate_future_min_payments(self):
        start_date_YYYYMMDD = '20240101'
        end_date_YYYYMMDD = '20240205'

        A = AccountSet.AccountSet([])
        A.createCheckingAccount('Checking',5000,0,999999)
        A.createLoanAccount('Loan A',3500,100,0,99999,'20230103',0.4,50)

        B = BudgetSet.BudgetSet([])
        B.addBudgetItem(start_date_YYYYMMDD, end_date_YYYYMMDD, 1, 'semiweekly', 1500, 'income', False, False)
        B.addBudgetItem('20240103', end_date_YYYYMMDD, 7, 'semiweekly', 2000, 'additional loan payment', False, True)

        M = MemoRuleSet.MemoRuleSet([])
        M.addMemoRule('.*income.*', None, 'Checking', 1)
        M.addMemoRule('additional loan payment', 'Checking', 'ALL_LOANS', 7)

        MS = MilestoneSet.MilestoneSet([], [], [])

        E = ExpenseForecast.ExpenseForecast(A,
                                             B,
                                             M,
                                             start_date_YYYYMMDD,
                                             end_date_YYYYMMDD,
                                             MS)
        E.runForecast()

        # this is just for me to review
        F = ForecastHandler.ForecastHandler()
        F.generateHTMLReport(E) #.html

        final_state_df = E.forecast_df.tail(1)
        assert final_state_df.iloc[0,:].Memo.strip() == ''  # loan should already have been paid off. If fail, there will be an additional payment here

    def test_multiple_additional_loan_payments_on_consecutive_days(self):
        start_date_YYYYMMDD = '20240101'
        end_date_YYYYMMDD = '20240205'

        A = AccountSet.AccountSet([])
        A.createCheckingAccount('Checking',5000,0,999999)
        A.createLoanAccount('Loan A', 3500, 100, 0, 99999, '20230103', 0.4, 50)

        B = BudgetSet.BudgetSet([])
        B.addBudgetItem(start_date_YYYYMMDD, end_date_YYYYMMDD, 1, 'semiweekly', 1500, 'income', False, False)
        B.addBudgetItem('20240110', '20240110', 7, 'once', 1000, 'additional loan payment 1', False, True)
        B.addBudgetItem('20240111', '20240111', 7, 'once', 1000, 'additional loan payment 2', False, True)
        B.addBudgetItem('20240112', '20240112', 7, 'once', 1000, 'additional loan payment 3', False, True)
        B.addBudgetItem('20240113', '20240113', 7, 'once', 1000, 'additional loan payment 4', False, True)

        M = MemoRuleSet.MemoRuleSet([])
        M.addMemoRule('.*income.*', None, 'Checking', 1)
        M.addMemoRule('additional loan payment', 'Checking', 'ALL_LOANS', 7)

        MS = MilestoneSet.MilestoneSet([], [], [])

        E = ExpenseForecast.ExpenseForecast(A,
                                            B,
                                            M,
                                            start_date_YYYYMMDD,
                                            end_date_YYYYMMDD,
                                            MS)
        E.runForecast()

        # this is just for me to review
        F = ForecastHandler.ForecastHandler()
        F.generateHTMLReport(E)  # .html

        final_state_df = E.forecast_df.tail(1)

        #I'm not sure what the check should be here but this looks correct
        #assert final_state_df.iloc[0,:].Memo.strip() == ''  #./Forecast_091547.html


    def test_additional_loan_payments_overpayment(self):
        start_date_YYYYMMDD = '20240101'
        end_date_YYYYMMDD = '20240205'

        A = AccountSet.AccountSet([])
        A.createCheckingAccount('Checking', 5000, 0, 999999)
        A.createLoanAccount('Loan A', 3500, 100, 0, 99999, '20230103', 0.4, 50)

        B = BudgetSet.BudgetSet([])
        B.addBudgetItem(start_date_YYYYMMDD, end_date_YYYYMMDD, 1, 'semiweekly', 1500, 'income', False, False)
        B.addBudgetItem('20240110', '20240110', 7, 'once', 10000, 'additional loan payment 1', False, True)

        M = MemoRuleSet.MemoRuleSet([])
        M.addMemoRule('.*income.*', None, 'Checking', 1)
        M.addMemoRule('additional loan payment', 'Checking', 'ALL_LOANS', 7)

        MS = MilestoneSet.MilestoneSet([], [], [])

        E = ExpenseForecast.ExpenseForecast(A,
                                            B,
                                            M,
                                            start_date_YYYYMMDD,
                                            end_date_YYYYMMDD,
                                            MS)
        E.runForecast()

        # this is just for me to review
        F = ForecastHandler.ForecastHandler()
        F.generateHTMLReport(E)  # .html

        final_state_df = E.forecast_df.tail(1)
        assert final_state_df.iloc[0,2] == 0 #pbal
        assert final_state_df.iloc[0, 2] == 0 #interest


    # passed by observation
    # def test_additional_cc_payments_overpayment(self):
    #     start_date_YYYYMMDD = '20240101'
    #     end_date_YYYYMMDD = '20240205'
    #
    #     A = AccountSet.AccountSet([])
    #     A.createAccount('Checking', 5000, 0, 999999, 'checking')
    #     A.createAccount('Credit', 1800, 0, 999999, 'credit', '20230103', 'compound', 0.4, 'monthly', 50, 1800, None, None)
    #
    #     B = BudgetSet.BudgetSet([])
    #     B.addBudgetItem(start_date_YYYYMMDD, end_date_YYYYMMDD, 1, 'semiweekly', 1500, 'income', False, False)
    #     B.addBudgetItem('20240109', '20240109', 2, 'once', 111, 'test txn', False, False)
    #     B.addBudgetItem('20240110', '20240110', 3, 'once', 10000, 'additional cc payment', False, True)
    #
    #     M = MemoRuleSet.MemoRuleSet([])
    #     M.addMemoRule('.*income.*', None, 'Checking', 1)
    #     M.addMemoRule('.*test txn.*', 'Credit', None , 2)
    #     M.addMemoRule('additional cc payment', 'Checking', 'Credit', 3)
    #
    #     MS = MilestoneSet.MilestoneSet(A, B, [], [], [])
    #
    #     E = ExpenseForecast.ExpenseForecast(A,
    #                                         B,
    #                                         M,
    #                                         start_date_YYYYMMDD,
    #                                         end_date_YYYYMMDD,
    #                                         MS)
    #     E.runForecast()
    #     E.appendSummaryLines()
    #
    #     # this is just for me to review
    #     F = ForecastHandler.ForecastHandler()
    #     F.generateHTMLReport(E)  # .html
    #
    #     final_state_df = E.forecast_df.tail(1)
    #     raise NotImplementedError

    ## passed by observation
    # def test_additional_cc_payments_expect_eliminate_future_min_payments(self):
    #     start_date_YYYYMMDD = '20240101'
    #     end_date_YYYYMMDD = '20240205'
    #
    #     A = AccountSet.AccountSet([])
    #     A.createAccount('Checking', 5000, 0, 999999, 'checking')
    #     A.createAccount('Loan A', 3600, 0, 999999, 'loan', '20230103', 'simple', 0.4, 'daily', 50, None, 3500, 100)
    #
    #     B = BudgetSet.BudgetSet([])
    #     B.addBudgetItem(start_date_YYYYMMDD, end_date_YYYYMMDD, 1, 'semiweekly', 1500, 'income', False, False)
    #     B.addBudgetItem('20240110', '20240110', 7, 'once', 10000, 'additional loan payment 1', False, True)
    #
    #     M = MemoRuleSet.MemoRuleSet([])
    #     M.addMemoRule('.*income.*', None, 'Checking', 1)
    #     M.addMemoRule('additional loan payment', 'Checking', 'ALL_LOANS', 7)
    #
    #     MS = MilestoneSet.MilestoneSet(A, B, [], [], [])
    #
    #     E = ExpenseForecast.ExpenseForecast(A,
    #                                         B,
    #                                         M,
    #                                         start_date_YYYYMMDD,
    #                                         end_date_YYYYMMDD,
    #                                         MS)
    #     E.runForecast()
    #     E.appendSummaryLines()
    #
    #     # this is just for me to review
    #     F = ForecastHandler.ForecastHandler()
    #     F.generateHTMLReport(E)  # .html
    #
    #     final_state_df = E.forecast_df.tail(1)
    #     raise NotImplementedError

    #
    #
    # def test_multiple_additional_cc_payments(self):
    #     start_date_YYYYMMDD = '20240101'
    #     end_date_YYYYMMDD = '20240205'
    #
    #     A = AccountSet.AccountSet([])
    #     A.createAccount('Checking', 5000, 0, 999999, 'checking')
    #     A.createAccount('Credit', 5000, 0, 999999, 'credit','20240103','compound',0.24,'monthly',40,5000)
    #
    #     # name, balance, min_balance, max_balance, account_type, billing_start_date_YYYYMMDD, interest_type, apr,
    #     # interest_cadence, minimum_payment, previous_statement_balance, principal_balance, interest_balance = None,
    #
    #     B = BudgetSet.BudgetSet([])
    #     B.addBudgetItem(start_date_YYYYMMDD, end_date_YYYYMMDD, 1, 'daily', 30, 'SPEND food', False, False)
    #     B.addBudgetItem(start_date_YYYYMMDD, end_date_YYYYMMDD, 1, 'semiweekly', 1500, 'income', False, False)
    #     B.addBudgetItem('20240103', end_date_YYYYMMDD, 2, 'semiweekly', 1500, 'additional cc payment', False, True)
    #
    #     M = MemoRuleSet.MemoRuleSet([])
    #     M.addMemoRule('.*income.*', None, 'Checking', 1)
    #     M.addMemoRule('SPEND.*', 'Checking', None, 1)
    #     M.addMemoRule('additional cc payment', 'Checking', 'Credit', 2)
    #     #
    #     # A1 = AccountMilestone.AccountMilestone('Loan A 0', 'Loan A', 0, 0)
    #     # A2 = AccountMilestone.AccountMilestone('Loan A 1000', 'Loan A', 1000, 1000)
    #     # A3 = AccountMilestone.AccountMilestone('Loan B 0', 'Loan B', 0, 0)
    #     # A4 = AccountMilestone.AccountMilestone('Loan B 1000', 'Loan B', 1000, 1000)
    #     # A5 = AccountMilestone.AccountMilestone('Loan C 0', 'Loan C', 0, 0)
    #     # A6 = AccountMilestone.AccountMilestone('Loan C 1000', 'Loan C', 1000, 1000)
    #     #
    #     # CM1 = CompositeMilestone.CompositeMilestone('All 1k', [A2, A4, A6], [])
    #
    #     MS = MilestoneSet.MilestoneSet(A, B, [], [], [])
    #
    #     E = ExpenseForecast.ExpenseForecast(A,
    #                                          B,
    #                                          M,
    #                                          start_date_YYYYMMDD,
    #                                          end_date_YYYYMMDD,
    #                                          MS)
    #     E.runForecast()
    #     E.appendSummaryLines()
    #
    #     # this is just for me to review
    #     F = ForecastHandler.ForecastHandler()
    #     F.generateHTMLReport(E) #Forecast_008797.html
    #
    #     #todo assert E attributes for test
    #     raise NotImplementedError



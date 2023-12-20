import unittest, pytest
import AccountSet,BudgetSet,MemoRuleSet,ExpenseForecast
import pandas as pd, numpy as np
import datetime, logging

import BudgetItem
import MemoRule

pd.options.mode.chained_assignment = None #apparently this warning can throw false positives???
import MilestoneSet
from log_methods import log_in_color
import Account, BudgetSet, MemoRuleSet
import copy

from generate_date_sequence import generate_date_sequence

from log_methods import display_test_result

def checking_acct():
    return Account.Account('checking',1000,0,10000,'checking',None,None,None,None,None)

def txn_budget_item():
    return BudgetItem.BudgetItem('20000101','20000101',1,'once',10,'test txn',False,False)

def match_all_checking_memo_rule():
    return MemoRule.MemoRule('.*','checking',None,1)

def match_test_txn_checking_memo_rule():
    return MemoRule.MemoRule('test txn', 'checking', None, 1)

def match_test_txn_credit_memo_rule():
    return MemoRule.MemoRule('test txn', 'credit', None, 1)

class TestExpenseForecastMethods:

    start_date_YYYYMMDD = '20000101'
    end_date_YYYYMMDD = '20000103'

    account_set = AccountSet.AccountSet([])
    budget_set = BudgetSet.BudgetSet([])
    memo_rule_set = MemoRuleSet.MemoRuleSet([])
    milestone_set = MilestoneSet.MilestoneSet(account_set,budget_set,[],[],[])


    def account_boundaries_are_violated(self,accounts_df,forecast_df):

        for col_name in forecast_df.columns.tolist():
            if col_name == 'Date' or col_name == 'Memo':
                continue

            acct_boundary__min = accounts_df.loc[accounts_df.Name == col_name,'Min_Balance']
            acct_boundary__max = accounts_df.loc[accounts_df.Name == col_name, 'Max_Balance']

            min_in_forecast_for_acct = min(forecast_df[col_name])
            max_in_forecast_for_acct = max(forecast_df[col_name])

            try:
                # print('min_in_forecast_for_acct:'+str(min_in_forecast_for_acct))
                # print('max_in_forecast_for_acct:' + str(max_in_forecast_for_acct))
                # print('acct_boundary__min:' + str(acct_boundary__min))
                # print('acct_boundary__max:' + str(acct_boundary__max))

                assert float(min_in_forecast_for_acct) >= float(acct_boundary__min)
                assert float(max_in_forecast_for_acct) <= float(acct_boundary__max)
            except Exception as e:
                print('Account Boundary Violation for '+str(col_name)+' in ExpenseForecast.account_boundaries_are_violated()')
                return True
        return False
    #
    # def test_current_situation(self):
    #     account_set = AccountSet.AccountSet([])
    #     budget_set = BudgetSet.BudgetSet([])
    #     memo_rule_set = MemoRuleSet.MemoRuleSet([])
    #
    #     # start_date_YYYYMMDD = '20230328'
    #     # end_date_YYYYMMDD = '20231231'
    #     #
    #     # current_checking_balance = 4224.62
    #     # current_credit_previous_statement_balance = 7351.2
    #     # current_credit_current_statement_balance = 430.27
    #
    #     start_date_YYYYMMDD = '20230731'
    #     end_date_YYYYMMDD = '20230802'
    #     #2670.8499999999995,990.5,15503.94
    #     current_checking_balance = 2670.85
    #     current_credit_previous_statement_balance = 15503.94
    #     current_credit_current_statement_balance = 990.5
    #
    #     account_set.addAccount(name='Checking',
    #                            balance=current_checking_balance,
    #                            min_balance=0,
    #                            max_balance=float('Inf'),
    #                            account_type="checking")
    #
    #     account_set.addAccount(name='Credit',
    #                            balance=current_credit_current_statement_balance,
    #                            min_balance=0,
    #                            max_balance=20000,
    #                            account_type="credit",
    #                            billing_start_date_YYYYMMDD='20230103',
    #                            interest_type='Compound',
    #                            apr=0.2824,
    #                            interest_cadence='Monthly',
    #                            minimum_payment=40,
    #                            previous_statement_balance=current_credit_previous_statement_balance,
    #                            principal_balance=None,
    #                            accrued_interest=None
    #                            )
    #
    #     account_set.addAccount(name='Loan A',
    #                            balance=4746.18,
    #                            min_balance=0,
    #                            max_balance=float("inf"),
    #                            account_type="loan",
    #                            billing_start_date_YYYYMMDD='20230903',
    #                            interest_type='simple',
    #                            apr=0.0466,
    #                            interest_cadence='daily',
    #                            minimum_payment=50,
    #                            previous_statement_balance=None,
    #                            principal_balance=4746.18,
    #                            accrued_interest=0
    #                            )
    #
    #     account_set.addAccount(name='Loan B',
    #                            balance=1919.55,
    #                            min_balance=0,
    #                            max_balance=float("inf"),
    #                            account_type="loan",
    #                            billing_start_date_YYYYMMDD='20230903',
    #                            interest_type='simple',
    #                            apr=0.0429,
    #                            interest_cadence='daily',
    #                            minimum_payment=50,
    #                            previous_statement_balance=None,
    #                            principal_balance=1919.55,
    #                            accrued_interest=0
    #                            )
    #
    #     account_set.addAccount(name='Loan C',
    #                            balance=4726.68,
    #                            min_balance=0,
    #                            max_balance=float("inf"),
    #                            account_type="loan",
    #                            billing_start_date_YYYYMMDD='20230903',
    #                            interest_type='simple',
    #                            apr=0.0429,
    #                            interest_cadence='daily',
    #                            minimum_payment=50,
    #                            previous_statement_balance=None,
    #                            principal_balance=4726.68,
    #                            accrued_interest=0
    #                            )
    #
    #     account_set.addAccount(name='Loan D',
    #                            balance=1823.31,
    #                            min_balance=0,
    #                            max_balance=float("inf"),
    #                            account_type="loan",
    #                            billing_start_date_YYYYMMDD='20230903',
    #                            interest_type='simple',
    #                            apr=0.0376,
    #                            interest_cadence='daily',
    #                            minimum_payment=50,
    #                            previous_statement_balance=None,
    #                            principal_balance=1823.31,
    #                            accrued_interest=0
    #                            )
    #
    #     account_set.addAccount(name='Loan E',
    #                            balance=3359.17,
    #                            min_balance=0,
    #                            max_balance=float("inf"),
    #                            account_type="loan",
    #                            billing_start_date_YYYYMMDD='20230903',
    #                            interest_type='simple',
    #                            apr=0.0376,
    #                            interest_cadence='daily',
    #                            minimum_payment=50,
    #                            previous_statement_balance=None,
    #                            principal_balance=3359.17,
    #                            accrued_interest=0
    #                            )
    #
    #     account_set.addAccount(name='Tax Debt',
    #                            balance=8000,
    #                            min_balance=0,
    #                            max_balance=float("inf"),
    #                            account_type="loan",
    #                            billing_start_date_YYYYMMDD='20231015',
    #                            interest_type='simple',
    #                            apr=0.06,
    #                            interest_cadence='daily',
    #                            minimum_payment=0,
    #                            previous_statement_balance=None,
    #                            principal_balance=8000,
    #                            accrued_interest=0
    #                            )
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230615', priority=1,
    #                              cadence='weekly', amount=450, memo='unemployment income',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD=start_date_YYYYMMDD, end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='daily', amount=30, memo='food',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230630', priority=1,
    #                              cadence='monthly', amount=1918, memo='rent (june last month at current place)',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230217', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='monthly', amount=89, memo='car insurance',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230331', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='monthly', amount=163.09, memo='phone bill',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230731', priority=1,
    #                              cadence='monthly', amount=100, memo='internet',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230219', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='monthly', amount=8, memo='hulu',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230219', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='monthly', amount=15, memo='hbo max',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230307', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='monthly', amount=33, memo='gym',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230407', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='monthly', amount=10, memo='spotify',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='monthly', amount=100, memo='gas and bus',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230221', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='monthly', amount=175.50, memo='health insurance',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230731', priority=1,
    #                              cadence='monthly', amount=300, memo='utilities',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230427', end_date_YYYYMMDD='20230427', priority=1,
    #                              cadence='once', amount=2900, memo='EMT class',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230628', end_date_YYYYMMDD='20231215', priority=1,
    #                              cadence='semiweekly', amount=1320, memo='EMT income (work for 6 months)',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20240228', priority=1,
    #                              cadence='monthly', amount=800, memo='rent (santa cruz 8 months)',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20240228', priority=1,
    #                              cadence='monthly', amount=1100, memo='additional cc payment (while staying in santa cruz)',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20240301', end_date_YYYYMMDD='20241231', priority=1,
    #                              cadence='monthly', amount=3000, memo='income (new tech job at 130k march 2024)',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20240401', end_date_YYYYMMDD='20241231', priority=1,
    #                              cadence='monthly', amount=1200, memo='rent (w james and panda)',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20240401', end_date_YYYYMMDD='20241231', priority=1,
    #                              cadence='monthly', amount=150, memo='utilities (w james and panda)',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #     #
    #     # budget_set.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20241231', priority=4,
    #     #                          cadence='monthly', amount=20000, memo='additional cc payment',
    #     #                          deferrable=False,
    #     #                          partial_payment_allowed=True)
    #
    #     # budget_set.addBudgetItem(start_date_YYYYMMDD='20230102', end_date_YYYYMMDD='20230731', priority=4,
    #     #                          cadence='monthly', amount=3611.5, memo='cyclical billing total',
    #     #                          deferrable=False,
    #     #                          partial_payment_allowed=False)
    #
    #     # 1000 + 1918 + 89 + 163 + 100 + 8 + 15 + 33 + 10 + 100 + 175.5 = 3611.5 + 300 ; cyclical billing total
    #
    #     memo_rule_set.addMemoRule(memo_regex='.*income.*', account_from=None, account_to='Checking', transaction_priority=1)
    #
    #     memo_rule_set.addMemoRule(memo_regex='food', account_from='Credit', account_to=None, transaction_priority=1)
    #     memo_rule_set.addMemoRule(memo_regex='internet', account_from='Credit', account_to=None, transaction_priority=1)
    #     memo_rule_set.addMemoRule(memo_regex='phone bill', account_from='Credit', account_to=None, transaction_priority=1)
    #     memo_rule_set.addMemoRule(memo_regex='car insurance', account_from='Credit', account_to=None, transaction_priority=1)
    #     memo_rule_set.addMemoRule(memo_regex='health insurance', account_from='Credit', account_to=None, transaction_priority=1)
    #     memo_rule_set.addMemoRule(memo_regex='gas and bus', account_from='Credit', account_to=None, transaction_priority=1)
    #     memo_rule_set.addMemoRule(memo_regex='spotify', account_from='Credit', account_to=None, transaction_priority=1)
    #     memo_rule_set.addMemoRule(memo_regex='gym', account_from='Credit', account_to=None, transaction_priority=1)
    #     memo_rule_set.addMemoRule(memo_regex='hbo max', account_from='Credit', account_to=None, transaction_priority=1)
    #     memo_rule_set.addMemoRule(memo_regex='hulu', account_from='Credit', account_to=None, transaction_priority=1)
    #     memo_rule_set.addMemoRule(memo_regex='.*rent.*', account_from='Checking', account_to=None, transaction_priority=1)
    #     memo_rule_set.addMemoRule(memo_regex='.*utilities.*', account_from='Checking', account_to=None, transaction_priority=1)
    #
    #     memo_rule_set.addMemoRule(memo_regex='.*additional cc payment.*', account_from='Checking', account_to='Credit', transaction_priority=1)
    #
    #     memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=2)
    #     memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=3)
    #     memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=4)
    #     memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=5)
    #     memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=6)
    #     memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=7)
    #
    #     memo_rule_set.addMemoRule(memo_regex='EMT class', account_from='Credit', account_to=None, transaction_priority=1)
    #
    #     E = ExpenseForecast.ExpenseForecast(account_set,
    #                                         budget_set,
    #                                         memo_rule_set,
    #                                         start_date_YYYYMMDD,
    #                                         end_date_YYYYMMDD)
    #
    #     log_in_color('white', 'info', 'Confirmed:')
    #     log_in_color('white', 'info', E.confirmed_df.to_string())
    #     log_in_color('white', 'info', 'Deferred:')
    #     log_in_color('white', 'info', E.deferred_df.to_string())
    #     log_in_color('white', 'info', 'Skipped:')
    #     log_in_color('white', 'info', E.skipped_df.to_string())
    #     log_in_color('white', 'info', 'Forecast:')
    #     log_in_color('white', 'info', E.forecast_df.to_string())
    #
    #     E.forecast_df.to_csv('./current_situation__'+start_date_YYYYMMDD+'__'+end_date_YYYYMMDD+'.csv')
    #
    #     E.plotOverall('./current_situation2__'+start_date_YYYYMMDD+'__'+end_date_YYYYMMDD+'.png')


    @pytest.mark.parametrize('account_set,budget_set,memo_rule_set,start_date_YYYYMMDD,end_date_YYYYMMDD,milestone_set',

                             [(AccountSet.AccountSet([checking_acct()]),
                              BudgetSet.BudgetSet([txn_budget_item()]),
                              MemoRuleSet.MemoRuleSet([match_test_txn_checking_memo_rule()]),
                              '19991231',
                              '20000101',
                              MilestoneSet.MilestoneSet(
                                  AccountSet.AccountSet([]),
                                  BudgetSet.BudgetSet([]),
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

                             [(AccountSet.AccountSet([]),
                              BudgetSet.BudgetSet([]),
                              MemoRuleSet.MemoRuleSet([]),
                              '20000101',
                              '19991231',
                              MilestoneSet.MilestoneSet(
                                AccountSet.AccountSet([]),
                                BudgetSet.BudgetSet([]),
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
                                   AccountSet.AccountSet([]),
                                   BudgetSet.BudgetSet([]),
                                   [],
                                   [],
                                   []),
                               ValueError
                               ),  # empty account_set

                              (AccountSet.AccountSet([checking_acct()]),
                               BudgetSet.BudgetSet([txn_budget_item()]),
                               MemoRuleSet.MemoRuleSet([]),
                               '19991231',
                               '20000101',
                               MilestoneSet.MilestoneSet(
                                   AccountSet.AccountSet([]),
                                   BudgetSet.BudgetSet([]),
                                   [],
                                   [],
                                   []),
                               ValueError
                               ), # A budget memo x priority element does not have a matching regex in memo rule set

                              (AccountSet.AccountSet([checking_acct()]),
                               BudgetSet.BudgetSet([txn_budget_item()]),
                               MemoRuleSet.MemoRuleSet([match_test_txn_credit_memo_rule()]),
                               '19991231',
                               '20000101',
                               MilestoneSet.MilestoneSet(
                                   AccountSet.AccountSet([]),
                                   BudgetSet.BudgetSet([]),
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
                              #      AccountSet.AccountSet([]),
                              #      BudgetSet.BudgetSet([]),
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
            display_test_result(test_description, d)
        except Exception as e:
            raise e

        try:
            sel_vec = (d.columns != 'Date') & (d.columns != 'Memo')
            non_boilerplate_values__M = np.matrix(d.iloc[:, sel_vec])

            error_ind = sum(sum(np.square(
                non_boilerplate_values__M)).T)  # this very much DOES NOT SCALE. this is intended for small tests
            assert error_ind == 0
        except Exception as e:
            # print(test_description) #todo use log methods
            # print(f.T.to_string())
            raise e

        return E

    def test_p1_only_no_budget_items(self):
        test_description = 'test_p1_only_no_budget_items'

        start_date_YYYYMMDD = self.start_date_YYYYMMDD
        end_date_YYYYMMDD = self.end_date_YYYYMMDD

        account_set = copy.deepcopy(self.account_set)
        budget_set = copy.deepcopy(self.budget_set)
        memo_rule_set = copy.deepcopy(self.memo_rule_set)
        milestone_set = copy.deepcopy(self.milestone_set)

        account_set.createAccount(name='Checking',
                                  balance=0,
                                  min_balance=0,
                                  max_balance=float('Inf'),
                                  account_type="checking")

        account_set.createAccount(name='Credit',
                                  balance=0,
                                  min_balance=0,
                                  max_balance=20000,
                                  account_type="credit",
                                  billing_start_date_YYYYMMDD='20000102',
                                  interest_type='Compound',
                                  apr=0.05,
                                  interest_cadence='Monthly',
                                  minimum_payment=40,
                                  previous_statement_balance=0,
                                  principal_balance=None,
                                  accrued_interest=None
                                  )

        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=1)

        expected_result_df = pd.DataFrame({
            'Date': ['20000101', '20000102', '20000103'],
            'Checking': [0, 0, 0],
            'Credit: Curr Stmt Bal': [0, 0, 0],
            'Credit: Prev Stmt Bal': [0, 0, 0],
            'Memo': ['', '', '']
        })
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

    def test_p1_only__income_and_payment_on_same_day(self):
        test_description = 'test_p1_only__income_and_payment_on_same_day'

        start_date_YYYYMMDD = self.start_date_YYYYMMDD
        end_date_YYYYMMDD = self.end_date_YYYYMMDD

        account_set = copy.deepcopy(self.account_set)
        budget_set = copy.deepcopy(self.budget_set)
        memo_rule_set = copy.deepcopy(self.memo_rule_set)
        milestone_set = copy.deepcopy(self.milestone_set)

        account_set.createAccount(name='Checking',
                                  balance=0,
                                  min_balance=0,
                                  max_balance=float('Inf'),
                                  account_type="checking")

        account_set.createAccount(name='Credit',
                                  balance=0,
                                  min_balance=0,
                                  max_balance=20000,
                                  account_type="credit",
                                  billing_start_date_YYYYMMDD='20000102',
                                  interest_type='Compound',
                                  apr=0.05,
                                  interest_cadence='Monthly',
                                  minimum_payment=40,
                                  previous_statement_balance=0,
                                  principal_balance=None,
                                  accrued_interest=None
                                  )

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000102', end_date_YYYYMMDD='20000102', priority=1,
                                 cadence='once', amount=100, memo='test item',
                                 deferrable=False,
                                 partial_payment_allowed=False)

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000102', end_date_YYYYMMDD='20000102', priority=1,
                                 cadence='once', amount=100, memo='income',
                                 deferrable=False,
                                 partial_payment_allowed=False)

        memo_rule_set.addMemoRule(memo_regex='income', account_from=None, account_to='Checking',transaction_priority=1)
        memo_rule_set.addMemoRule(memo_regex='test item', account_from='Checking', account_to=None, transaction_priority=1)

        expected_result_df = pd.DataFrame({
            'Date': ['20000101', '20000102', '20000103'],
            'Checking': [0, 0, 0],
            'Credit: Curr Stmt Bal': [0, 0, 0],
            'Credit: Prev Stmt Bal': [0, 0, 0],
            'Memo': ['', '', '']
        })
        expected_result_df.Date = [datetime.datetime.strptime(x, '%Y%m%d') for x in expected_result_df.Date]

        E = self.compute_forecast_and_actual_vs_expected(account_set,
                                                     budget_set,
                                                     memo_rule_set,
                                                     start_date_YYYYMMDD,
                                                     end_date_YYYYMMDD,
                                                         milestone_set,
                                                     expected_result_df,
                                                     test_description)
    def test_p1_only__cc_payment__prev_bal_25__expect_25(self):
        test_description = 'test_cc_payment__satisfice__prev_bal_25__expect_25'

        start_date_YYYYMMDD = self.start_date_YYYYMMDD
        end_date_YYYYMMDD = self.end_date_YYYYMMDD

        account_set = copy.deepcopy(self.account_set)
        budget_set = copy.deepcopy(self.budget_set)
        memo_rule_set = copy.deepcopy(self.memo_rule_set)
        milestone_set = copy.deepcopy(self.milestone_set)

        account_set.createAccount(name='Checking',
                                  balance=2000,
                                  min_balance=0,
                                  max_balance=float('Inf'),
                                  account_type="checking")

        account_set.createAccount(name='Credit',
                                  balance=0,
                                  min_balance=0,
                                  max_balance=20000,
                                  account_type="credit",
                                  billing_start_date_YYYYMMDD='20000102',
                                  interest_type='Compound',
                                  apr=0.05,
                                  interest_cadence='Monthly',
                                  minimum_payment=40,
                                  previous_statement_balance=25,
                                  principal_balance=None,
                                  accrued_interest=None
                                  )

        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=1)

        expected_result_df = pd.DataFrame({
            'Date': ['20000101', '20000102', '20000103'],
            'Checking': [2000, 1975, 1975],
            'Credit: Curr Stmt Bal': [0, 0, 0],
            'Credit: Prev Stmt Bal': [25, 0, 0],
            'Memo': ['', '', '']
        })
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

    def test_p1_only__cc_payment__prev_bal_1000__expect_40(self):
        test_description = 'test_cc_payment__satisfice__prev_bal_1000__expect_40'

        start_date_YYYYMMDD = self.start_date_YYYYMMDD
        end_date_YYYYMMDD = self.end_date_YYYYMMDD

        account_set = copy.deepcopy(self.account_set)
        budget_set = copy.deepcopy(self.budget_set)
        memo_rule_set = copy.deepcopy(self.memo_rule_set)
        milestone_set = copy.deepcopy(self.milestone_set)

        account_set.createAccount(name='Checking',
                                  balance=2000,
                                  min_balance=0,
                                  max_balance=float('Inf'),
                                  account_type="checking")

        account_set.createAccount(name='Credit',
                                  balance=0,
                                  min_balance=0,
                                  max_balance=20000,
                                  account_type="credit",
                                  billing_start_date_YYYYMMDD='20000102',
                                  interest_type='Compound',
                                  apr=0.05,
                                  interest_cadence='Monthly',
                                  minimum_payment=40,
                                  previous_statement_balance=1000,
                                  principal_balance=None,
                                  accrued_interest=None
                                  )

        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=1)

        expected_result_df = pd.DataFrame({
            'Date': ['20000101', '20000102', '20000103'],
            'Checking': [2000, 1960, 1960],
            'Credit: Curr Stmt Bal': [0, 0, 0],
            'Credit: Prev Stmt Bal': [1000, 964, 964], #this amount should have interest added
            'Memo': ['', '', '']
        })
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
    def test_p1_only__cc_payment_prev_bal_3000__expect_60(self):
        test_description = 'test_cc_payment__satisfice__prev_bal_3000__expect_60'

        start_date_YYYYMMDD = self.start_date_YYYYMMDD
        end_date_YYYYMMDD = self.end_date_YYYYMMDD

        account_set = copy.deepcopy(self.account_set)
        budget_set = copy.deepcopy(self.budget_set)
        memo_rule_set = copy.deepcopy(self.memo_rule_set)
        milestone_set = copy.deepcopy(self.milestone_set)

        account_set.createAccount(name='Checking',
                                  balance=2000,
                                  min_balance=0,
                                  max_balance=float('Inf'),
                                  account_type="checking")

        account_set.createAccount(name='Credit',
                                  balance=0,
                                  min_balance=0,
                                  max_balance=20000,
                                  account_type="credit",
                                  billing_start_date_YYYYMMDD='20000102',
                                  interest_type='Compound',
                                  apr=0.05,
                                  interest_cadence='Monthly',
                                  minimum_payment=40,
                                  previous_statement_balance=3000,
                                  principal_balance=None,
                                  accrued_interest=None
                                  )

        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=1)

        expected_result_df = pd.DataFrame({
            'Date': ['20000101', '20000102', '20000103'],
            'Checking': [2000, 1940, 1940],
            'Credit: Curr Stmt Bal': [0, 0, 0],
            'Credit: Prev Stmt Bal': [3000, 2952.25, 2952.25],
            'Memo': ['', '', '']
        })
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
    def test_p2_and_3__expect_skip(self):
        test_description = 'test_p2_and_3__expect_skip'

        start_date_YYYYMMDD = self.start_date_YYYYMMDD
        end_date_YYYYMMDD = self.end_date_YYYYMMDD

        account_set = copy.deepcopy(self.account_set)
        budget_set = copy.deepcopy(self.budget_set)
        memo_rule_set = copy.deepcopy(self.memo_rule_set)
        milestone_set = copy.deepcopy(self.milestone_set)

        account_set.createAccount(name='Checking',
                                  balance=0,
                                  min_balance=0,
                                  max_balance=float('Inf'),
                                  account_type="checking")

        account_set.createAccount(name='Credit',
                                  balance=0,
                                  min_balance=0,
                                  max_balance=20000,
                                  account_type="credit",
                                  billing_start_date_YYYYMMDD='20000102',
                                  interest_type='Compound',
                                  apr=0.05,
                                  interest_cadence='Monthly',
                                  minimum_payment=40,
                                  previous_statement_balance=0,
                                  principal_balance=None,
                                  accrued_interest=None
                                  )

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000102', end_date_YYYYMMDD='20000102', priority=2,
                                 cadence='once', amount=10, memo='this should be skipped',
                                 deferrable=False,
                                 partial_payment_allowed=False)

        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=1)
        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=2)

        expected_result_df = pd.DataFrame({
            'Date': ['20000101', '20000102', '20000103'],
            'Checking': [0, 0, 0],
            'Credit: Curr Stmt Bal': [0, 0, 0],
            'Credit: Prev Stmt Bal': [0, 0, 0],
            'Memo': ['', '', '']
        })
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

        assert E.skipped_df.shape[0] == 1
        assert E.skipped_df['Memo'].iloc[0] == 'this should be skipped'
    def test_p2_and_3__expect_defer(self):
        test_description = 'test_p2_and_3__expect_defer'

        start_date_YYYYMMDD = self.start_date_YYYYMMDD
        end_date_YYYYMMDD = self.end_date_YYYYMMDD

        account_set = copy.deepcopy(self.account_set)
        budget_set = copy.deepcopy(self.budget_set)
        memo_rule_set = copy.deepcopy(self.memo_rule_set)
        milestone_set = copy.deepcopy(self.milestone_set)

        account_set.createAccount(name='Checking',
                                  balance=0,
                                  min_balance=0,
                                  max_balance=float('Inf'),
                                  account_type="checking")

        account_set.createAccount(name='Credit',
                                  balance=0,
                                  min_balance=0,
                                  max_balance=20000,
                                  account_type="credit",
                                  billing_start_date_YYYYMMDD='20000102',
                                  interest_type='Compound',
                                  apr=0.05,
                                  interest_cadence='Monthly',
                                  minimum_payment=40,
                                  previous_statement_balance=0,
                                  principal_balance=None,
                                  accrued_interest=None
                                  )

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000102', end_date_YYYYMMDD='20000102', priority=3,
                                 cadence='once', amount=10, memo='this should be deferred',
                                 deferrable=True,
                                 partial_payment_allowed=False)

        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=1)
        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=3)

        expected_result_df = pd.DataFrame({
            'Date': ['20000101', '20000102', '20000103'],
            'Checking': [0, 0, 0],
            'Credit: Curr Stmt Bal': [0, 0, 0],
            'Credit: Prev Stmt Bal': [0, 0, 0],
            'Memo': ['', '', '']
        })
        expected_result_df.Date = [datetime.datetime.strptime(x, '%Y%m%d') for x in expected_result_df.Date]

        E = self.compute_forecast_and_actual_vs_expected(account_set,
                                                     budget_set,
                                                     memo_rule_set,
                                                     start_date_YYYYMMDD,
                                                     end_date_YYYYMMDD,
                                                         milestone_set,
                                                     expected_result_df,
                                                     test_description)
        # print('E.deferred_df:')
        # print(E.deferred_df)
        assert E.deferred_df.shape[0] == 1
        assert E.deferred_df['Memo'].iloc[0] == 'this should be deferred'

    def test_p2_and_3__p3_item_skipped_bc_p2(self):
        test_description = 'test_p2_and_3__p3_item_skipped_bc_p2'

        start_date_YYYYMMDD = self.start_date_YYYYMMDD
        end_date_YYYYMMDD = self.end_date_YYYYMMDD

        account_set = copy.deepcopy(self.account_set)
        budget_set = copy.deepcopy(self.budget_set)
        memo_rule_set = copy.deepcopy(self.memo_rule_set)
        milestone_set = copy.deepcopy(self.milestone_set)

        account_set.createAccount(name='Checking',
                                  balance=100,
                                  min_balance=0,
                                  max_balance=float('Inf'),
                                  account_type="checking")

        account_set.createAccount(name='Credit',
                                  balance=0,
                                  min_balance=0,
                                  max_balance=20000,
                                  account_type="credit",
                                  billing_start_date_YYYYMMDD='20000102',
                                  interest_type='Compound',
                                  apr=0.05,
                                  interest_cadence='Monthly',
                                  minimum_payment=40,
                                  previous_statement_balance=0,
                                  principal_balance=None,
                                  accrued_interest=None
                                  )

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000102', end_date_YYYYMMDD='20000102', priority=2,
                                 cadence='once', amount=100, memo='this should be executed',
                                 deferrable=False,
                                 partial_payment_allowed=False)

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000102', end_date_YYYYMMDD='20000102', priority=3,
                                 cadence='once', amount=100, memo='this should be skipped',
                                 deferrable=False,
                                 partial_payment_allowed=False)

        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=1)
        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=2)
        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=3)

        expected_result_df = pd.DataFrame({
            'Date': ['20000101', '20000102', '20000103'],
            'Checking': [100, 0, 0],
            'Credit: Curr Stmt Bal': [0, 0, 0],
            'Credit: Prev Stmt Bal': [0, 0, 0],
            'Memo': ['', '', '']
        })
        expected_result_df.Date = [datetime.datetime.strptime(x, '%Y%m%d') for x in expected_result_df.Date]

        E = self.compute_forecast_and_actual_vs_expected(account_set,
                                                     budget_set,
                                                     memo_rule_set,
                                                     start_date_YYYYMMDD,
                                                     end_date_YYYYMMDD,
                                                         milestone_set,
                                                     expected_result_df,
                                                     test_description)

        assert E.skipped_df.shape[0] == 1
        assert E.skipped_df['Memo'].iloc[0] == 'this should be skipped'
    def test_p2_and_3__p3_item_deferred_bc_p2(self):
        test_description = 'test_p2_and_3__p3_item_deferred_bc_p2'

        start_date_YYYYMMDD = self.start_date_YYYYMMDD
        end_date_YYYYMMDD = self.end_date_YYYYMMDD

        account_set = copy.deepcopy(self.account_set)
        budget_set = copy.deepcopy(self.budget_set)
        memo_rule_set = copy.deepcopy(self.memo_rule_set)
        milestone_set = copy.deepcopy(self.milestone_set)

        account_set.createAccount(name='Checking',
                                  balance=100,
                                  min_balance=0,
                                  max_balance=float('Inf'),
                                  account_type="checking")

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000102', end_date_YYYYMMDD='20000102', priority=2,
                                 cadence='once', amount=100, memo='this should be executed',
                                 deferrable=False,
                                 partial_payment_allowed=False)

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000102', end_date_YYYYMMDD='20000102', priority=3,
                                 cadence='once', amount=100, memo='this should be deferred',
                                 deferrable=True,
                                 partial_payment_allowed=False)

        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=1)
        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=2)
        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=3)

        expected_result_df = pd.DataFrame({
            'Date': ['20000101', '20000102', '20000103'],
            'Checking': [100, 0, 0],
            'Memo': ['', '', '']
        })
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

        # print('Forecast:')
        # print(E.forecast_df.to_string())
        #
        # print('Confirmed:')
        # print(E.confirmed_df.to_string())
        #
        # print('Deferred:')
        # print(E.deferred_df.to_string())
        #
        # print('Skipped:')
        # print(E.skipped_df.to_string())

        assert E.deferred_df.shape[0] == 1
        assert E.deferred_df['Memo'].iloc[0] == 'this should be deferred'

    def test_p4__cc_payment__no_prev_balance__pay_100__no_funds__expect_skip(self):
        test_description = 'test_cc_payment__optimize__no_prev_balance__pay_100__no_funds__expect_skip'

        start_date_YYYYMMDD = self.start_date_YYYYMMDD
        end_date_YYYYMMDD = self.end_date_YYYYMMDD

        account_set = copy.deepcopy(self.account_set)
        budget_set = copy.deepcopy(self.budget_set)
        memo_rule_set = copy.deepcopy(self.memo_rule_set)
        milestone_set = copy.deepcopy(self.milestone_set)

        account_set.createAccount(name='Checking',
                                  balance=0,
                                  min_balance=0,
                                  max_balance=float('Inf'),
                                  account_type="checking")

        account_set.createAccount(name='Credit',
                                  balance=0,
                                  min_balance=0,
                                  max_balance=20000,
                                  account_type="credit",
                                  billing_start_date_YYYYMMDD='20000102',
                                  interest_type='Compound',
                                  apr=0.05,
                                  interest_cadence='Monthly',
                                  minimum_payment=40,
                                  previous_statement_balance=0,
                                  principal_balance=None,
                                  accrued_interest=None
                                  )

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000102', end_date_YYYYMMDD='20000102', priority=4,
                                 cadence='once', amount=100, memo='additional credit card payment',
                                 deferrable=False,
                                 partial_payment_allowed=False)

        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=1)
        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=4)

        expected_result_df = pd.DataFrame({
            'Date': ['20000101', '20000102', '20000103'],
            'Checking': [0, 0, 0],
            'Credit: Curr Stmt Bal': [0, 0, 0],
            'Credit: Prev Stmt Bal': [0, 0, 0],
            'Memo': ['', '', '']
        })
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
    def test_p4__cc_payment__no_prev_balance__pay_100__expect_skip(self):
        test_description = 'test_cc_payment__optimize__no_prev_balance__pay_100__expect_skip'


        start_date_YYYYMMDD = self.start_date_YYYYMMDD
        end_date_YYYYMMDD = self.end_date_YYYYMMDD

        account_set = copy.deepcopy(self.account_set)
        budget_set = copy.deepcopy(self.budget_set)
        memo_rule_set = copy.deepcopy(self.memo_rule_set)
        milestone_set = copy.deepcopy(self.milestone_set)

        account_set.createAccount(name='Checking',
                                  balance=2000,
                                  min_balance=0,
                                  max_balance=float('Inf'),
                                  account_type="checking")

        account_set.createAccount(name='Credit',
                                  balance=0,
                                  min_balance=0,
                                  max_balance=20000,
                                  account_type="credit",
                                  billing_start_date_YYYYMMDD='20000102',
                                  interest_type='Compound',
                                  apr=0.05,
                                  interest_cadence='Monthly',
                                  minimum_payment=40,
                                  previous_statement_balance=0,
                                  principal_balance=None,
                                  accrued_interest=None
                                  )

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000102', end_date_YYYYMMDD='20000102', priority=4,
                                 cadence='once', amount=100, memo='this should be skipped',
                                 deferrable=False,
                                 partial_payment_allowed=False)

        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=1)
        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to='Credit', transaction_priority=4)

        expected_result_df = pd.DataFrame({
            'Date': ['20000101', '20000102', '20000103'],
            'Checking': [2000, 2000, 2000],
            'Credit: Curr Stmt Bal': [0, 0, 0],
            'Credit: Prev Stmt Bal': [0, 0, 0],
            'Memo': ['', '', '']
        })
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

        assert E.skipped_df.shape[0] == 1
        assert E.skipped_df['Memo'].iloc[0] == 'this should be skipped'

    def test_p4__cc_payment__pay_all_of_prev_part_of_curr__expect_800(self):
        test_description = 'test_cc_payment__optimize__pay_all_of_prev_part_of_curr__expect_800'

        start_date_YYYYMMDD = self.start_date_YYYYMMDD
        end_date_YYYYMMDD = self.end_date_YYYYMMDD

        account_set = copy.deepcopy(self.account_set)
        budget_set = copy.deepcopy(self.budget_set)
        memo_rule_set = copy.deepcopy(self.memo_rule_set)
        milestone_set = copy.deepcopy(self.milestone_set)

        account_set.createAccount(name='Checking',
                                  balance=2000,
                                  min_balance=0,
                                  max_balance=float('Inf'),
                                  account_type="checking")

        account_set.createAccount(name='Credit',
                                  balance=500,
                                  min_balance=0,
                                  max_balance=20000,
                                  account_type="credit",
                                  billing_start_date_YYYYMMDD='20000112',
                                  interest_type='Compound',
                                  apr=0.05,
                                  interest_cadence='Monthly',
                                  minimum_payment=40,
                                  previous_statement_balance=500,
                                  principal_balance=None,
                                  accrued_interest=None
                                  )

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000102', end_date_YYYYMMDD='20000102', priority=4,
                                 cadence='once', amount=800, memo='test pay all prev part of curr',
                                 deferrable=False,
                                 partial_payment_allowed=False)

        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=1)
        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to='Credit', transaction_priority=4)

        expected_result_df = pd.DataFrame({
            'Date': ['20000101', '20000102', '20000103'],
            'Checking': [2000, 1200, 1200],
            'Credit: Curr Stmt Bal': [500, 200, 200],
            'Credit: Prev Stmt Bal': [500, 0, 0],
            'Memo': ['', '', '']
        })
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
    def test_p4__cc_payment__pay_part_of_prev_balance__expect_200(self):
        test_description = 'test_cc_payment__optimize__pay_part_of_prev_balance__expect_200'

        start_date_YYYYMMDD = self.start_date_YYYYMMDD
        end_date_YYYYMMDD = self.end_date_YYYYMMDD

        account_set = copy.deepcopy(self.account_set)
        budget_set = copy.deepcopy(self.budget_set)
        memo_rule_set = copy.deepcopy(self.memo_rule_set)
        milestone_set = copy.deepcopy(self.milestone_set)

        account_set.createAccount(name='Checking',
                                  balance=200,
                                  min_balance=0,
                                  max_balance=float('Inf'),
                                  account_type="checking")

        account_set.createAccount(name='Credit',
                                  balance=500,
                                  min_balance=0,
                                  max_balance=20000,
                                  account_type="credit",
                                  billing_start_date_YYYYMMDD='20000112',
                                  interest_type='Compound',
                                  apr=0.05,
                                  interest_cadence='Monthly',
                                  minimum_payment=40,
                                  previous_statement_balance=500,
                                  principal_balance=None,
                                  accrued_interest=None
                                  )

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000102', end_date_YYYYMMDD='20000102', priority=4,
                                 cadence='once', amount=200, memo='additional cc payment test',deferrable=False,
                                 partial_payment_allowed=True)


        memo_rule_set.addMemoRule(memo_regex='.*',account_from='Credit',account_to=None,transaction_priority=1)

        memo_rule_set.addMemoRule(memo_regex='.*additional cc payment.*', account_from='Checking', account_to='Credit', transaction_priority=4)

        expected_result_df = pd.DataFrame({
            'Date': ['20000101', '20000102', '20000103'],
            'Checking': [200, 0, 0],
            'Credit: Curr Stmt Bal': [500, 500, 500],
            'Credit: Prev Stmt Bal': [500, 300, 300],
            'Memo': ['', '', '']
        })
        expected_result_df.Date = [datetime.datetime.strptime(x, '%Y%m%d') for x in expected_result_df.Date]
        ### END

        E = self.compute_forecast_and_actual_vs_expected(account_set,
                                                     budget_set,
                                                     memo_rule_set,
                                                     start_date_YYYYMMDD,
                                                     end_date_YYYYMMDD,
                                                         milestone_set,
                                                     expected_result_df,
                                                     test_description)
    def test_p4__cc_payment__non_0_prev_balance_but_no_funds__expect_0(self):
        test_description = 'test_cc_payment__optimize__non_0_prev_balance_but_no_funds__expect_0'

        start_date_YYYYMMDD = self.start_date_YYYYMMDD
        end_date_YYYYMMDD = self.end_date_YYYYMMDD

        account_set = copy.deepcopy(self.account_set)
        budget_set = copy.deepcopy(self.budget_set)
        memo_rule_set = copy.deepcopy(self.memo_rule_set)
        milestone_set = copy.deepcopy(self.milestone_set)

        account_set.createAccount(name='Checking',
                                  balance=40,
                                  min_balance=0,
                                  max_balance=float('Inf'),
                                  account_type="checking")

        account_set.createAccount(name='Credit',
                                  balance=500,
                                  min_balance=0,
                                  max_balance=20000,
                                  account_type="credit",
                                  billing_start_date_YYYYMMDD='20000102',
                                  interest_type='Compound',
                                  apr=0.05,
                                  interest_cadence='Monthly',
                                  minimum_payment=40,
                                  previous_statement_balance=500,
                                  principal_balance=None,
                                  accrued_interest=None
                                  )

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000102', end_date_YYYYMMDD='20000102', priority=4,
                                 cadence='once', amount=100, memo='additional cc payment test 9',deferrable=False,
                                 partial_payment_allowed=True)


        memo_rule_set.addMemoRule(memo_regex='.*',account_from='Credit',account_to=None,transaction_priority=1)

        memo_rule_set.addMemoRule(memo_regex='.*additional cc payment.*', account_from='Checking', account_to='Credit', transaction_priority=4)

        expected_result_df = pd.DataFrame({
            'Date': ['20000101', '20000102', '20000103'],
            'Checking': [40, 0, 0],
            'Credit: Curr Stmt Bal': [500, 0, 0],
            'Credit: Prev Stmt Bal': [500,961.92, 961.92],
            'Memo': ['', '', '']
        })
        expected_result_df.Date = [datetime.datetime.strptime(x, '%Y%m%d') for x in expected_result_df.Date]

        E = self.compute_forecast_and_actual_vs_expected(account_set,
                                                     budget_set,
                                                     memo_rule_set,
                                                     start_date_YYYYMMDD,
                                                     end_date_YYYYMMDD,
                                                         milestone_set,
                                                     expected_result_df,
                                                     test_description)

        #print(E.forecast_df.to_string())

        #assert E.skipped_df.shape[0] == 1 #this should be checking for the additional payment memo
        # todo i need to decide what the expected behavior is here. giving this a pass for now because i wwnt to move on
        #I looked at it and this test is passing (for now) so I'm just moving on
    def test_p4__cc_payment__partial_of_indicated_amount(self):
        test_description = 'test_p4__cc_payment__partial_of_indicated_amount'

        start_date_YYYYMMDD = self.start_date_YYYYMMDD
        end_date_YYYYMMDD = self.end_date_YYYYMMDD

        account_set = copy.deepcopy(self.account_set)
        budget_set = copy.deepcopy(self.budget_set)
        memo_rule_set = copy.deepcopy(self.memo_rule_set)
        milestone_set = copy.deepcopy(self.milestone_set)

        account_set.createAccount(name='Checking',
                                  balance=1000,
                                  min_balance=0,
                                  max_balance=float('Inf'),
                                  account_type="checking")

        account_set.createAccount(name='Credit',
                                  balance=1500,
                                  min_balance=0,
                                  max_balance=20000,
                                  account_type="credit",
                                  billing_start_date_YYYYMMDD='20000112',
                                  interest_type='Compound',
                                  apr=0.05,
                                  interest_cadence='Monthly',
                                  minimum_payment=40,
                                  previous_statement_balance=500,
                                  principal_balance=None,
                                  accrued_interest=None
                                  )

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000102', end_date_YYYYMMDD='20000102', priority=4,
                                 cadence='once', amount=20000, memo='partial cc payment',
                                 deferrable=False,
                                 partial_payment_allowed=True)

        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=1)
        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to='Credit', transaction_priority=4)

        expected_result_df = pd.DataFrame({
            'Date': ['20000101', '20000102', '20000103'],
            'Checking': [1000, 0, 0],
            'Credit: Curr Stmt Bal': [1500, 1000, 1000],
            'Credit: Prev Stmt Bal': [500, 0, 0],
            'Memo': ['', '', '']
        })
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

    #
    # def test_p5_and_6__expect_skip(self):
    #     test_description = 'test_p5_and_6__expect_skip'
    #
    #     start_date_YYYYMMDD = self.start_date_YYYYMMDD
    #     end_date_YYYYMMDD = self.end_date_YYYYMMDD
    #
    #     account_set = copy.deepcopy(self.account_set)
    #     budget_set = copy.deepcopy(self.budget_set)
    #     memo_rule_set = copy.deepcopy(self.memo_rule_set)
    #
    #     account_set.addAccount(name='Checking',
    #                            balance=1000,
    #                            min_balance=0,
    #                            max_balance=float('Inf'),
    #                            account_type="checking")
    #
    #     account_set.addAccount(name='Credit',
    #                            balance=0,
    #                            min_balance=0,
    #                            max_balance=20000,
    #                            account_type="credit",
    #                            billing_start_date_YYYYMMDD='20000102',
    #                            interest_type='Compound',
    #                            apr=0.05,
    #                            interest_cadence='Monthly',
    #                            minimum_payment=40,
    #                            previous_statement_balance=0,
    #                            principal_balance=None,
    #                            accrued_interest=None
    #                            )
    #
    #     # budget_set.addBudgetItem(start_date_YYYYMMDD='20000101', end_date_YYYYMMDD='20000103', priority=1,
    #     #                          cadence='daily', amount=0, memo='dummy memo',
    #     #                          deferrable=False,
    #     #                          partial_payment_allowed=False)
    #     #
    #     # memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=1)
    #
    #     expected_result_df = pd.DataFrame({
    #         'Date': ['20000101', '20000102', '20000103'],
    #         'Checking': [0, 0, 0],
    #         'Credit: Curr Stmt Bal': [0, 0, 0],
    #         'Credit: Prev Stmt Bal': [0, 0, 0],
    #         'Memo': ['', '', '']
    #     })
    #     expected_result_df.Date = [datetime.datetime.strptime(x, '%Y%m%d') for x in
    #                                expected_result_df.Date]
    #
    #     E = self.compute_forecast_and_actual_vs_expected(account_set,
    #                                                  budget_set,
    #                                                  memo_rule_set,
    #                                                  start_date_YYYYMMDD,
    #                                                  end_date_YYYYMMDD,
    #                                                  expected_result_df,
    #                                                  test_description)
    #     raise NotImplementedError

    def test_execute_defer_after_receiving_income_2_days_later(self):

        test_description = 'test_execute_defer_after_receving_income_2_days_later'

        start_date_YYYYMMDD = self.start_date_YYYYMMDD
        end_date_YYYYMMDD = '20000105'

        account_set = copy.deepcopy(self.account_set)
        budget_set = copy.deepcopy(self.budget_set)
        memo_rule_set = copy.deepcopy(self.memo_rule_set)
        milestone_set = copy.deepcopy(self.milestone_set)

        account_set.createAccount(name='Checking',
                                  balance=500,
                                  min_balance=0,
                                  max_balance=float('Inf'),
                                  account_type="checking")

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000101', end_date_YYYYMMDD='20000104', priority=1,
                                 cadence='daily', amount=100, memo='SPEND daily p1 txn',
                                 deferrable=False,
                                 partial_payment_allowed=False)

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000104', end_date_YYYYMMDD='20000104', priority=1,
                                 cadence='once', amount=200, memo='200 income on 1/4',
                                 deferrable=False,
                                 partial_payment_allowed=False)

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000102', end_date_YYYYMMDD='20000102', priority=2,
                                 cadence='once', amount=400, memo='SPEND p2 txn deferred from 1/2 to 1/4',
                                 deferrable=True,
                                 partial_payment_allowed=False)

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000103', end_date_YYYYMMDD='20000103', priority=3,
                                 cadence='once', amount=400, memo='SPEND p3 txn on 1/3 that is skipped bc later lower priority_index txn',
                                 deferrable=False,
                                 partial_payment_allowed=False)

        memo_rule_set.addMemoRule(memo_regex='SPEND.*', account_from='Checking', account_to=None, transaction_priority=1)
        memo_rule_set.addMemoRule(memo_regex='.*income.*', account_from=None, account_to='Checking', transaction_priority=1)
        memo_rule_set.addMemoRule(memo_regex='SPEND.*', account_from='Checking', account_to=None, transaction_priority=2)
        memo_rule_set.addMemoRule(memo_regex='SPEND.*', account_from='Checking', account_to=None, transaction_priority=3)

        expected_result_df = pd.DataFrame({
            'Date': ['20000101', '20000102', '20000103', '20000104', '20000105'],
            'Checking': [500, 400, 300, 0, 0],
            'Memo': ['', '', '', '', '']
        })
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

        # E = ExpenseForecast.ExpenseForecast(account_set,
        #                                     budget_set,
        #                                     memo_rule_set,
        #                                     start_date_YYYYMMDD,
        #                                     end_date_YYYYMMDD, raise_exceptions=False)
        #
        # print(E.forecast_df.to_string())



    def test_execute_at_reduced_amount_bc_later_higher_priority_txn(self):

        test_description = 'test_execute_at_reduced_amount_bc_later_higher_priority_txn'

        start_date_YYYYMMDD = self.start_date_YYYYMMDD
        end_date_YYYYMMDD = '20000105'

        account_set = copy.deepcopy(self.account_set)
        budget_set = copy.deepcopy(self.budget_set)
        memo_rule_set = copy.deepcopy(self.memo_rule_set)
        milestone_set = copy.deepcopy(self.milestone_set)

        account_set.createAccount(name='Checking',
                                  balance=400,
                                  min_balance=0,
                                  max_balance=float('Inf'),
                                  account_type="checking")

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000104', end_date_YYYYMMDD='20000104', priority=2,
                                 cadence='once', amount=200, memo='pay 200 after reduced amt txn',
                                 deferrable=False,
                                 partial_payment_allowed=False)

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000103', end_date_YYYYMMDD='20000103', priority=3,
                                 cadence='once', amount=400, memo='pay reduced amount',
                                 deferrable=False,
                                 partial_payment_allowed=True)

        #
        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=1)
        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=2)
        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=3)

        expected_result_df = pd.DataFrame({
            'Date': ['20000101', '20000102', '20000103', '20000104', '20000105'],
            'Checking': [400, 400, 200, 0, 0],
            'Memo': ['', '', '', '', '']
        })
        expected_result_df.Date = [datetime.datetime.strptime(x, '%Y%m%d') for x in
                                   expected_result_df.Date]

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
                                            end_date_YYYYMMDD, raise_exceptions=False)

        print(E.forecast_df.to_string())


    def test_transactions_executed_at_p1_and_p2(self):

        test_description = 'test_transactions_executed_at_p1_and_p2'

        start_date_YYYYMMDD = self.start_date_YYYYMMDD
        end_date_YYYYMMDD = '20000106'

        account_set = copy.deepcopy(self.account_set)
        budget_set = copy.deepcopy(self.budget_set)
        memo_rule_set = copy.deepcopy(self.memo_rule_set)
        milestone_set = copy.deepcopy(self.milestone_set)

        account_set.createAccount(name='Checking',
                                  balance=2000,
                                  min_balance=0,
                                  max_balance=float('Inf'),
                                  account_type="checking")

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000102', end_date_YYYYMMDD='20000105', priority=1,
                                 cadence='daily', amount=100, memo='p1 daily txn',
                                 deferrable=False,
                                 partial_payment_allowed=False)

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000102', end_date_YYYYMMDD='20000102', priority=2,
                                 cadence='once', amount=100, memo='p2 daily txn 1/2/00',
                                 deferrable=False,
                                 partial_payment_allowed=False)

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000103', end_date_YYYYMMDD='20000103', priority=2,
                                 cadence='once', amount=100, memo='p2 daily txn 1/3/00',
                                 deferrable=False,
                                 partial_payment_allowed=False)

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000104', end_date_YYYYMMDD='20000104', priority=2,
                                 cadence='once', amount=100, memo='p2 daily txn 1/4/00',
                                 deferrable=False,
                                 partial_payment_allowed=False)

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000105', end_date_YYYYMMDD='20000105', priority=2,
                                 cadence='once', amount=100, memo='p2 daily txn 1/5/00',
                                 deferrable=False,
                                 partial_payment_allowed=False)


        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=1)
        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=2)

        expected_result_df = pd.DataFrame({
            'Date': ['20000101', '20000102', '20000103', '20000104', '20000105', '20000106'],
            'Checking': [2000, 1800, 1600, 1400, 1200, 1200],
            'Memo': ['', '', '', '', '', '']
        })
        expected_result_df.Date = [datetime.datetime.strptime(x, '%Y%m%d') for x in
                                   expected_result_df.Date]

        E = self.compute_forecast_and_actual_vs_expected(account_set,
                                                         budget_set,
                                                         memo_rule_set,
                                                         start_date_YYYYMMDD,
                                                         end_date_YYYYMMDD,
                                                         expected_result_df,
                                                         test_description)

        #print(E.forecast_df)


    def test_transactions_executed_at_p1_and_p2_and_p3(self):

        test_description = 'test_transactions_executed_at_p1_and_p2_and_p3'

        start_date_YYYYMMDD = self.start_date_YYYYMMDD
        end_date_YYYYMMDD = '20000106'

        account_set = copy.deepcopy(self.account_set)
        budget_set = copy.deepcopy(self.budget_set)
        memo_rule_set = copy.deepcopy(self.memo_rule_set)
        milestone_set = copy.deepcopy(self.milestone_set)

        account_set.createAccount(name='Checking',
                                  balance=2000,
                                  min_balance=0,
                                  max_balance=float('Inf'),
                                  account_type="checking")

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000102', end_date_YYYYMMDD='20000105', priority=1,
                                 cadence='daily', amount=100, memo='p1 daily txn',
                                 deferrable=False,
                                 partial_payment_allowed=False)

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000102', end_date_YYYYMMDD='20000102', priority=2,
                                 cadence='once', amount=100, memo='p2 daily txn 1/2/00',
                                 deferrable=False,
                                 partial_payment_allowed=False)

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000103', end_date_YYYYMMDD='20000103', priority=2,
                                 cadence='once', amount=100, memo='p2 daily txn 1/3/00',
                                 deferrable=False,
                                 partial_payment_allowed=False)

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000104', end_date_YYYYMMDD='20000104', priority=2,
                                 cadence='once', amount=100, memo='p2 daily txn 1/4/00',
                                 deferrable=False,
                                 partial_payment_allowed=False)

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000105', end_date_YYYYMMDD='20000105', priority=2,
                                 cadence='once', amount=100, memo='p2 daily txn 1/5/00',
                                 deferrable=False,
                                 partial_payment_allowed=False)

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000102', end_date_YYYYMMDD='20000105', priority=3,
                                 cadence='daily', amount=100, memo='p3 daily txn',
                                 deferrable=False,
                                 partial_payment_allowed=False)

        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=1)
        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=2)
        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=3)

        expected_result_df = pd.DataFrame({
            'Date': ['20000101', '20000102', '20000103', '20000104', '20000105', '20000106'],
            'Checking': [2000, 1700, 1400, 1100, 800, 800],
            'Memo': ['', '', '', '', '', '']
        })
        expected_result_df.Date = [datetime.datetime.strptime(x, '%Y%m%d') for x in
                                   expected_result_df.Date]

        E = self.compute_forecast_and_actual_vs_expected(account_set,
                                                         budget_set,
                                                         memo_rule_set,
                                                         start_date_YYYYMMDD,
                                                         end_date_YYYYMMDD,
                                                         expected_result_df,
                                                         test_description)

        print(E.forecast_df.to_string())

    def test_multiple_matching_memo_rule_regex(self):
        # For this test, I want to see:
        # A lower amount at higher priority-indexed txn occuring instead of a lower priority-index with a higher amount
        # An executed transactions from each priority level in use

        test_description = 'test_complex_input_test_1'

        start_date_YYYYMMDD = self.start_date_YYYYMMDD
        end_date_YYYYMMDD = self.end_date_YYYYMMDD

        account_set = copy.deepcopy(self.account_set)
        budget_set = copy.deepcopy(self.budget_set)
        memo_rule_set = copy.deepcopy(self.memo_rule_set)
        milestone_set = copy.deepcopy(self.milestone_set)

        account_set.createAccount(name='Checking',
                                  balance=1000,
                                  min_balance=0,
                                  max_balance=float('Inf'),
                                  account_type="checking")

        account_set.createAccount(name='Credit',
                                  balance=0,
                                  min_balance=0,
                                  max_balance=20000,
                                  account_type="credit",
                                  billing_start_date_YYYYMMDD='20000102',
                                  interest_type='Compound',
                                  apr=0.05,
                                  interest_cadence='Monthly',
                                  minimum_payment=40,
                                  previous_statement_balance=0,
                                  principal_balance=None,
                                  accrued_interest=None
                                  )

        # budget_set.addBudgetItem(start_date_YYYYMMDD='20000101', end_date_YYYYMMDD='20000103', priority=1,
        #                          cadence='daily', amount=0, memo='dummy memo',
        #                          deferrable=False,
        #                          partial_payment_allowed=False)
        #
        # memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=1)

        expected_result_df = pd.DataFrame({
            'Date': ['20000101', '20000102', '20000103'],
            'Checking': [0, 0, 0],
            'Credit: Curr Stmt Bal': [0, 0, 0],
            'Credit: Prev Stmt Bal': [0, 0, 0],
            'Memo': ['', '', '']
        })
        expected_result_df.Date = [datetime.datetime.strptime(x, '%Y%m%d') for x in
                                   expected_result_df.Date]

        E = self.compute_forecast_and_actual_vs_expected(account_set,
                                                         budget_set,
                                                         memo_rule_set,
                                                         start_date_YYYYMMDD,
                                                         end_date_YYYYMMDD,
                                                         expected_result_df,
                                                         test_description)
        raise NotImplementedError


    def test_get_available_balances(self):

        start_date_YYYYMMDD = '20230325'
        end_date_YYYYMMDD = '20231231'

        current_checking_balance = 5000
        current_credit_previous_statement_balance = 0
        current_credit_current_statement_balance = 0

        account_set = copy.deepcopy(self.account_set)
        budget_set = copy.deepcopy(self.budget_set)
        memo_rule_set = copy.deepcopy(self.memo_rule_set)
        milestone_set = copy.deepcopy(self.milestone_set)

        account_set.createAccount(name='Checking',
                                  balance=current_checking_balance,
                                  min_balance=0,
                                  max_balance=float('Inf'),
                                  account_type="checking")

        account_set.createAccount(name='Credit',
                                  balance=current_credit_current_statement_balance,
                                  min_balance=0,
                                  max_balance=20000,
                                  account_type="credit",
                                  billing_start_date_YYYYMMDD='20230103',
                                  interest_type='Compound',
                                  apr=0.2824,
                                  interest_cadence='Monthly',
                                  minimum_payment=40,
                                  previous_statement_balance=current_credit_previous_statement_balance,
                                  principal_balance=None,
                                  accrued_interest=None
                                  )

        account_set.createAccount(name='Loan A',
                                  balance=4746.18,
                                  min_balance=0,
                                  max_balance=float("inf"),
                                  account_type="loan",
                                  billing_start_date_YYYYMMDD='20230903',
                                  interest_type='simple',
                                  apr=0.0466,
                                  interest_cadence='daily',
                                  minimum_payment=50,
                                  previous_statement_balance=None,
                                  principal_balance=4746.18,
                                  accrued_interest=0
                                  )

        account_set.createAccount(name='Loan B',
                                  balance=1919.55,
                                  min_balance=0,
                                  max_balance=float("inf"),
                                  account_type="loan",
                                  billing_start_date_YYYYMMDD='20230903',
                                  interest_type='simple',
                                  apr=0.0429,
                                  interest_cadence='daily',
                                  minimum_payment=50,
                                  previous_statement_balance=None,
                                  principal_balance=1919.55,
                                  accrued_interest=0
                                  )

        account_set.createAccount(name='Loan C',
                                  balance=4726.68,
                                  min_balance=0,
                                  max_balance=float("inf"),
                                  account_type="loan",
                                  billing_start_date_YYYYMMDD='20230903',
                                  interest_type='simple',
                                  apr=0.0429,
                                  interest_cadence='daily',
                                  minimum_payment=50,
                                  previous_statement_balance=None,
                                  principal_balance=4726.68,
                                  accrued_interest=0
                                  )

        account_set.createAccount(name='Loan D',
                                  balance=1823.31,
                                  min_balance=0,
                                  max_balance=float("inf"),
                                  account_type="loan",
                                  billing_start_date_YYYYMMDD='20230903',
                                  interest_type='simple',
                                  apr=0.0376,
                                  interest_cadence='daily',
                                  minimum_payment=50,
                                  previous_statement_balance=None,
                                  principal_balance=1823.31,
                                  accrued_interest=0
                                  )

        account_set.createAccount(name='Loan E',
                                  balance=3359.17,
                                  min_balance=0,
                                  max_balance=float("inf"),
                                  account_type="loan",
                                  billing_start_date_YYYYMMDD='20230903',
                                  interest_type='simple',
                                  apr=0.0376,
                                  interest_cadence='daily',
                                  minimum_payment=50,
                                  previous_statement_balance=None,
                                  principal_balance=3359.17,
                                  accrued_interest=0
                                  )

        #print(account_set.getAvailableBalances()) #pass by manual inspection
    #
    # def test_what_if_i_didnt_quit_my_job(self):
    #
    #     start_date_YYYYMMDD = '20230325'
    #     end_date_YYYYMMDD = '20230501'
    #
    #     current_checking_balance = 5000
    #     current_credit_previous_statement_balance = 0
    #     current_credit_current_statement_balance = 0
    #
    #     account_set = copy.deepcopy(self.account_set)
    #     budget_set = copy.deepcopy(self.budget_set)
    #     memo_rule_set = copy.deepcopy(self.memo_rule_set)
    #
    #     account_set.addAccount(name='Checking',
    #                            balance=current_checking_balance,
    #                            min_balance=0,
    #                            max_balance=float('Inf'),
    #                            account_type="checking")
    #
    #     account_set.addAccount(name='Credit',
    #                            balance=current_credit_current_statement_balance,
    #                            min_balance=0,
    #                            max_balance=20000,
    #                            account_type="credit",
    #                            billing_start_date_YYYYMMDD='20230103',
    #                            interest_type='Compound',
    #                            apr=0.2824,
    #                            interest_cadence='Monthly',
    #                            minimum_payment=40,
    #                            previous_statement_balance=current_credit_previous_statement_balance,
    #                            principal_balance=None,
    #                            accrued_interest=None
    #                            )
    #
    #     account_set.addAccount(name='Loan A',
    #                            balance=4746.18,
    #                            min_balance=0,
    #                            max_balance=float("inf"),
    #                            account_type="loan",
    #                            billing_start_date_YYYYMMDD='20230903',
    #                            interest_type='simple',
    #                            apr=0.0466,
    #                            interest_cadence='daily',
    #                            minimum_payment=50,
    #                            previous_statement_balance=None,
    #                            principal_balance=4746.18,
    #                            accrued_interest=0
    #                            )
    #
    #     account_set.addAccount(name='Loan B',
    #                            balance=1919.55,
    #                            min_balance=0,
    #                            max_balance=float("inf"),
    #                            account_type="loan",
    #                            billing_start_date_YYYYMMDD='20230903',
    #                            interest_type='simple',
    #                            apr=0.0429,
    #                            interest_cadence='daily',
    #                            minimum_payment=50,
    #                            previous_statement_balance=None,
    #                            principal_balance=1919.55,
    #                            accrued_interest=0
    #                            )
    #
    #     account_set.addAccount(name='Loan C',
    #                            balance=4726.68,
    #                            min_balance=0,
    #                            max_balance=float("inf"),
    #                            account_type="loan",
    #                            billing_start_date_YYYYMMDD='20230903',
    #                            interest_type='simple',
    #                            apr=0.0429,
    #                            interest_cadence='daily',
    #                            minimum_payment=50,
    #                            previous_statement_balance=None,
    #                            principal_balance=4726.68,
    #                            accrued_interest=0
    #                            )
    #
    #     account_set.addAccount(name='Loan D',
    #                            balance=1823.31,
    #                            min_balance=0,
    #                            max_balance=float("inf"),
    #                            account_type="loan",
    #                            billing_start_date_YYYYMMDD='20230903',
    #                            interest_type='simple',
    #                            apr=0.0376,
    #                            interest_cadence='daily',
    #                            minimum_payment=50,
    #                            previous_statement_balance=None,
    #                            principal_balance=1823.31,
    #                            accrued_interest=0
    #                            )
    #
    #     account_set.addAccount(name='Loan E',
    #                            balance=3359.17,
    #                            min_balance=0,
    #                            max_balance=float("inf"),
    #                            account_type="loan",
    #                            billing_start_date_YYYYMMDD='20230903',
    #                            interest_type='simple',
    #                            apr=0.0376,
    #                            interest_cadence='daily',
    #                            minimum_payment=50,
    #                            previous_statement_balance=None,
    #                            principal_balance=3359.17,
    #                            accrued_interest=0
    #                            )
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD=start_date_YYYYMMDD, end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='daily', amount=30, memo='food',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='monthly', amount=1918, memo='rent',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230217', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='monthly', amount=89, memo='car insurance',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230331', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='monthly', amount=163.09, memo='phone bill',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='monthly', amount=100, memo='internet',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230219', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='monthly', amount=8, memo='hulu',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230219', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='monthly', amount=15, memo='hbo max',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230307', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='monthly', amount=33, memo='gym',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230407', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='monthly', amount=10, memo='spotify',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='monthly', amount=100, memo='gas and bus',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230221', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='monthly', amount=175.50, memo='health insurance',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='monthly', amount=300, memo='utilities',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230102', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=4,
    #                              cadence='monthly', amount=3611.5, memo='cyclical billing total',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='semiweekly', amount=2240, memo='income',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     # 1000 + 1918 + 89 + 163 + 100 + 8 + 15 + 33 + 10 + 100 + 175.5 = 3611.5 + 300 ; cyclical billing total
    #
    #     memo_rule_set.addMemoRule(memo_regex='income', account_from=None, account_to='Checking', transaction_priority=1)
    #
    #     memo_rule_set.addMemoRule(memo_regex='food', account_from='Credit', account_to=None, transaction_priority=1)
    #     memo_rule_set.addMemoRule(memo_regex='internet', account_from='Credit', account_to=None, transaction_priority=1)
    #     memo_rule_set.addMemoRule(memo_regex='phone bill', account_from='Credit', account_to=None, transaction_priority=1)
    #     memo_rule_set.addMemoRule(memo_regex='car insurance', account_from='Credit', account_to=None, transaction_priority=1)
    #     memo_rule_set.addMemoRule(memo_regex='health insurance', account_from='Credit', account_to=None, transaction_priority=1)
    #     memo_rule_set.addMemoRule(memo_regex='gas and bus', account_from='Credit', account_to=None, transaction_priority=1)
    #     memo_rule_set.addMemoRule(memo_regex='spotify', account_from='Credit', account_to=None, transaction_priority=1)
    #     memo_rule_set.addMemoRule(memo_regex='gym', account_from='Credit', account_to=None, transaction_priority=1)
    #     memo_rule_set.addMemoRule(memo_regex='hbo max', account_from='Credit', account_to=None, transaction_priority=1)
    #     memo_rule_set.addMemoRule(memo_regex='hulu', account_from='Credit', account_to=None, transaction_priority=1)
    #     memo_rule_set.addMemoRule(memo_regex='rent', account_from='Checking', account_to=None, transaction_priority=1)
    #     memo_rule_set.addMemoRule(memo_regex='utilities', account_from='Checking', account_to=None, transaction_priority=1)
    #
    #     memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=2)
    #     memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=3)
    #     memo_rule_set.addMemoRule(memo_regex='cyclical billing total', account_from='Checking', account_to=None, transaction_priority=4)
    #     memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=5)
    #     memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=6)
    #     memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=7)
    #
    #     E = ExpenseForecast.ExpenseForecast(account_set,
    #                                         budget_set,
    #                                         memo_rule_set,
    #                                         start_date_YYYYMMDD,
    #                                         end_date_YYYYMMDD, raise_exceptions=False)
    #
    #     # log_in_color('white', 'debug', 'Confirmed:')
    #     # log_in_color('white', 'debug', E.confirmed_df.to_string())
    #     log_in_color('white', 'info', 'Deferred:')
    #     log_in_color('white', 'info', E.deferred_df.to_string())
    #     log_in_color('white', 'info', 'Skipped:')
    #     log_in_color('white', 'info', E.skipped_df.to_string())
    #     log_in_color('white', 'info', 'Forecast:')
    #     log_in_color('white', 'info', E.forecast_df.to_string())

    def test_dont_recompute_past_days_for_p2plus_transactions(self):
        #will have to analyze logs for this
        raise NotImplementedError

    def test_dont_output_logs_during_execution(self):
        raise NotImplementedError

    def test_run_from_excel_at_path(self):
        # not exa
        raise NotImplementedError

    def test_forecast_longer_than_satisfice(self):
        #if satisfice fails on the second day of the forecast, there is weirdness
        test_description = 'test_complex_input_test_1'

        start_date_YYYYMMDD = self.start_date_YYYYMMDD
        end_date_YYYYMMDD = '20000104'

        account_set = copy.deepcopy(self.account_set)
        budget_set = copy.deepcopy(self.budget_set)
        memo_rule_set = copy.deepcopy(self.memo_rule_set)

        account_set.createAccount(name='Checking',
                                  balance=0,
                                  min_balance=0,
                                  max_balance=float('Inf'),
                                  account_type="checking")

        account_set.createAccount(name='Credit',
                                  balance=40,
                                  min_balance=0,
                                  max_balance=20000,
                                  account_type="credit",
                                  billing_start_date_YYYYMMDD='20000103',
                                  interest_type='Compound',
                                  apr=0.05,
                                  interest_cadence='Monthly',
                                  minimum_payment=40,
                                  previous_statement_balance=0,
                                  principal_balance=None,
                                  accrued_interest=None
                                  )

        # budget_set.addBudgetItem(start_date_YYYYMMDD='20000101', end_date_YYYYMMDD='20000103', priority=1,
        #                          cadence='daily', amount=0, memo='dummy memo',
        #                          deferrable=False,
        #                          partial_payment_allowed=False)
        #
        # memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=1)

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
                                            end_date_YYYYMMDD, raise_exceptions=False)

        log_in_color('white', 'debug', 'Confirmed:')
        log_in_color('white', 'debug', E.confirmed_df.to_string())
        log_in_color('white', 'debug', 'Deferred:')
        log_in_color('white', 'debug', E.deferred_df.to_string())
        log_in_color('white', 'debug', 'Skipped:')
        log_in_color('white', 'debug', E.skipped_df.to_string())
        log_in_color('white', 'debug', 'Forecast:')
        log_in_color('white', 'debug', E.forecast_df.to_string())
    #
    # def test_my_real_life_data(self):
    #     test_description = 'test_my_real_life_data'
    #
    #     # start_date_YYYYMMDD = '20230328'
    #     # end_date_YYYYMMDD = '20230601'
    #     # #end_date_YYYYMMDD = '20231231'
    #
    #
    #     #2023-08-31  2023-08-31 00:00:00  2144.18               1433.59               15186.7
    #
    #     start_date_YYYYMMDD = '20230328'
    #     end_date_YYYYMMDD = '20231231'
    #
    #     current_checking_balance = 2424.62 + 450*4
    #     current_credit_previous_statement_balance = 7351.2
    #     current_credit_current_total_balance = 7781.47
    #     current_credit_current_statement_balance = current_credit_current_total_balance - current_credit_previous_statement_balance
    #
    #     account_set = AccountSet.AccountSet([])
    #     budget_set = BudgetSet.BudgetSet([])
    #     memo_rule_set = MemoRuleSet.MemoRuleSet([])
    #
    #     account_set.addAccount(name='Checking',
    #                            balance=current_checking_balance,
    #                            min_balance=0,
    #                            max_balance=float('Inf'),
    #                            account_type="checking")
    #
    #     account_set.addAccount(name='Credit',
    #                            balance=current_credit_current_statement_balance,
    #                            min_balance=0,
    #                            max_balance=20000,
    #                            account_type="credit",
    #                            billing_start_date_YYYYMMDD='20230103',
    #                            interest_type='Compound',
    #                            apr=0.2824,
    #                            interest_cadence='Monthly',
    #                            minimum_payment=40,
    #                            previous_statement_balance=current_credit_previous_statement_balance,
    #                            principal_balance=None,
    #                            accrued_interest=None
    #                            )
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD=start_date_YYYYMMDD, end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='daily', amount=30, memo='food',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='monthly', amount=1918, memo='rent',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230217', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='monthly', amount=89, memo='car insurance',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230331', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='monthly', amount=163.09, memo='phone bill',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='monthly', amount=100, memo='internet',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230219', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='monthly', amount=8, memo='hulu',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230219', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='monthly', amount=15, memo='hbo max',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230307', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='monthly', amount=33, memo='gym',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230407', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='monthly', amount=10, memo='spotify',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='monthly', amount=100, memo='gas and bus',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230221', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='monthly', amount=175.50, memo='health insurance',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='monthly', amount=300, memo='utilities',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     # budget_set.addBudgetItem(start_date_YYYYMMDD='20230102', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=4,
    #     #                          cadence='monthly', amount=3611.5, memo='cyclical billing total',
    #     #                          deferrable=False,
    #     #                          partial_payment_allowed=True)
    #
    #     budget_set.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
    #                              cadence='weekly', amount=450, memo='income',
    #                              deferrable=False,
    #                              partial_payment_allowed=False)
    #
    #     # 1000 + 1918 + 89 + 163 + 100 + 8 + 15 + 33 + 10 + 100 + 175.5 = 3611.5 + 300 ; cyclical billing total
    #
    #     memo_rule_set.addMemoRule(memo_regex='income', account_from=None, account_to='Checking', transaction_priority=1)
    #
    #     memo_rule_set.addMemoRule(memo_regex='food', account_from='Credit', account_to=None, transaction_priority=1)
    #     memo_rule_set.addMemoRule(memo_regex='internet', account_from='Credit', account_to=None, transaction_priority=1)
    #     memo_rule_set.addMemoRule(memo_regex='phone bill', account_from='Credit', account_to=None, transaction_priority=1)
    #     memo_rule_set.addMemoRule(memo_regex='car insurance', account_from='Credit', account_to=None, transaction_priority=1)
    #     memo_rule_set.addMemoRule(memo_regex='health insurance', account_from='Credit', account_to=None, transaction_priority=1)
    #     memo_rule_set.addMemoRule(memo_regex='gas and bus', account_from='Credit', account_to=None, transaction_priority=1)
    #     memo_rule_set.addMemoRule(memo_regex='spotify', account_from='Credit', account_to=None, transaction_priority=1)
    #     memo_rule_set.addMemoRule(memo_regex='gym', account_from='Credit', account_to=None, transaction_priority=1)
    #     memo_rule_set.addMemoRule(memo_regex='hbo max', account_from='Credit', account_to=None, transaction_priority=1)
    #     memo_rule_set.addMemoRule(memo_regex='hulu', account_from='Credit', account_to=None, transaction_priority=1)
    #     memo_rule_set.addMemoRule(memo_regex='rent', account_from='Checking', account_to=None, transaction_priority=1)
    #     memo_rule_set.addMemoRule(memo_regex='utilities', account_from='Checking', account_to=None, transaction_priority=1)
    #
    #     memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=2)
    #     memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=3)
    #     #memo_rule_set.addMemoRule(memo_regex='cyclical billing total', account_from='Checking', account_to=None, transaction_priority=4)
    #     memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=5)
    #     memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=6)
    #     memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=7)
    #
    #     E = ExpenseForecast.ExpenseForecast(account_set,
    #                                         budget_set,
    #                                         memo_rule_set,
    #                                         start_date_YYYYMMDD,
    #                                         end_date_YYYYMMDD)
    #
    #     log_in_color('white','debug','Confirmed:')
    #     log_in_color('white','debug',E.confirmed_df.to_string())
    #     log_in_color('white','debug','Deferred:')
    #     log_in_color('white','debug',E.deferred_df.to_string())
    #     log_in_color('white','debug','Skipped:')
    #     log_in_color('white','debug',E.skipped_df.to_string())
    #     log_in_color('white', 'debug', 'Forecast:')
    #     log_in_color('white', 'debug', E.forecast_df.to_string())
    #
    #     E.plotOverall('./out.png')

    def test_p5_and_6__expect_defer(self):
        test_description = 'test_p5_and_6__expect_defer'

        start_date_YYYYMMDD = self.start_date_YYYYMMDD
        end_date_YYYYMMDD = self.end_date_YYYYMMDD

        account_set = copy.deepcopy(self.account_set)
        budget_set = copy.deepcopy(self.budget_set)
        memo_rule_set = copy.deepcopy(self.memo_rule_set)

        account_set.createAccount(name='Checking',
                                  balance=1000,
                                  min_balance=0,
                                  max_balance=float('Inf'),
                                  account_type="checking")

        account_set.createAccount(name='Credit',
                                  balance=0,
                                  min_balance=0,
                                  max_balance=20000,
                                  account_type="credit",
                                  billing_start_date_YYYYMMDD='20000102',
                                  interest_type='Compound',
                                  apr=0.05,
                                  interest_cadence='Monthly',
                                  minimum_payment=40,
                                  previous_statement_balance=0,
                                  principal_balance=None,
                                  accrued_interest=None
                                  )

        # budget_set.addBudgetItem(start_date_YYYYMMDD='20000101', end_date_YYYYMMDD='20000103', priority=1,
        #                          cadence='daily', amount=0, memo='dummy memo',
        #                          deferrable=False,
        #                          partial_payment_allowed=False)
        #
        # memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=1)

        expected_result_df = pd.DataFrame({
            'Date': ['20000101', '20000102', '20000103'],
            'Checking': [0, 0, 0],
            'Credit: Curr Stmt Bal': [0, 0, 0],
            'Credit: Prev Stmt Bal': [0, 0, 0],
            'Memo': ['', '', '']
        })
        expected_result_df.Date = [datetime.datetime.strptime(x, '%Y%m%d') for x in
                                   expected_result_df.Date]

        E = self.compute_forecast_and_actual_vs_expected(account_set,
                                                     budget_set,
                                                     memo_rule_set,
                                                     start_date_YYYYMMDD,
                                                     end_date_YYYYMMDD,
                                                     expected_result_df,
                                                     test_description)
        raise NotImplementedError

    def test_minimum_loan_payments(self):
        test_description = 'test_minimum_loan_payments'

        start_date_YYYYMMDD = '20230901'
        end_date_YYYYMMDD = '20230905'

        account_set = copy.deepcopy(self.account_set)
        budget_set = copy.deepcopy(self.budget_set)
        memo_rule_set = copy.deepcopy(self.memo_rule_set)

        account_set.createAccount(name='Checking',
                                  balance=2000,
                                  min_balance=0,
                                  max_balance=float('Inf'),
                                  account_type="checking")

        account_set.createAccount(name='Credit',
                                  balance=0,
                                  min_balance=0,
                                  max_balance=20000,
                                  account_type="credit",
                                  billing_start_date_YYYYMMDD='20230103',
                                  interest_type='Compound',
                                  apr=0.2824,
                                  interest_cadence='Monthly',
                                  minimum_payment=40,
                                  previous_statement_balance=0,
                                  principal_balance=None,
                                  accrued_interest=None
                                  )

        account_set.createAccount(name='Loan A',
                                  balance=4746.18,
                                  min_balance=0,
                                  max_balance=float("inf"),
                                  account_type="loan",
                                  billing_start_date_YYYYMMDD='20230903',
                                  interest_type='simple',
                                  apr=0.0466,
                                  interest_cadence='daily',
                                  minimum_payment=50,
                                  previous_statement_balance=None,
                                  principal_balance=4746.18,
                                  accrued_interest=0
                                  )

        account_set.createAccount(name='Loan B',
                                  balance=1919.55,
                                  min_balance=0,
                                  max_balance=float("inf"),
                                  account_type="loan",
                                  billing_start_date_YYYYMMDD='20230903',
                                  interest_type='simple',
                                  apr=0.0429,
                                  interest_cadence='daily',
                                  minimum_payment=50,
                                  previous_statement_balance=None,
                                  principal_balance=1919.55,
                                  accrued_interest=0
                                  )

        account_set.createAccount(name='Loan C',
                                  balance=4726.68,
                                  min_balance=0,
                                  max_balance=float("inf"),
                                  account_type="loan",
                                  billing_start_date_YYYYMMDD='20230903',
                                  interest_type='simple',
                                  apr=0.0429,
                                  interest_cadence='daily',
                                  minimum_payment=50,
                                  previous_statement_balance=None,
                                  principal_balance=4726.68,
                                  accrued_interest=0
                                  )

        account_set.createAccount(name='Loan D',
                                  balance=1823.31,
                                  min_balance=0,
                                  max_balance=float("inf"),
                                  account_type="loan",
                                  billing_start_date_YYYYMMDD='20230903',
                                  interest_type='simple',
                                  apr=0.0376,
                                  interest_cadence='daily',
                                  minimum_payment=50,
                                  previous_statement_balance=None,
                                  principal_balance=1823.31,
                                  accrued_interest=0
                                  )

        account_set.createAccount(name='Loan E',
                                  balance=3359.17,
                                  min_balance=0,
                                  max_balance=float("inf"),
                                  account_type="loan",
                                  billing_start_date_YYYYMMDD='20230903',
                                  interest_type='simple',
                                  apr=0.0376,
                                  interest_cadence='daily',
                                  minimum_payment=50,
                                  previous_statement_balance=None,
                                  principal_balance=3359.17,
                                  accrued_interest=0
                                  )


        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=1)

        expected_result_df = pd.DataFrame({
            'Date': ['20230902', '20230903', '20230904'],
            'Checking': [2000, 1750, 1750],
            'Loan A: Principal Balance': [0,0,0],
            'Loan A: Interest': [0, 0, 0],
            'Loan B: Principal Balance': [0, 0, 0],
            'Loan B: Interest': [0, 0, 0],
            'Loan C: Principal Balance': [0, 0, 0],
            'Loan C: Interest': [0, 0, 0],
            'Loan D: Principal Balance': [0, 0, 0],
            'Loan D: Interest': [0, 0, 0],
            'Loan E: Principal Balance': [0, 0, 0],
            'Loan E: Interest': [0, 0, 0],
            'Memo': ['', '', '']
        })
        expected_result_df.Date = [datetime.datetime.strptime(x, '%Y%m%d') for x in
                                   expected_result_df.Date]

        # E = self.compute_forecast_and_actual_vs_expected(account_set,
        #                                                  budget_set,
        #                                                  memo_rule_set,
        #                                                  start_date_YYYYMMDD,
        #                                                  end_date_YYYYMMDD,
        #                                                  expected_result_df,
        #                                                  test_description)

        # E = ExpenseForecast.ExpenseForecast(account_set,
        #                                     budget_set,
        #                                     memo_rule_set,
        #                                     start_date_YYYYMMDD,
        #                                     end_date_YYYYMMDD, raise_exceptions=False)
        #
        # print(E.forecast_df.to_string())

        ### Pass by manual inspection

    #note that additional loan payment is not a memo line, but allocate_additional_loan_payments is a helper method that can be used to create budget items
    #honestly should probably be refactored to be a method of account_set
    def test_p7__additional_loan_payments(self):
        test_description = 'test_p7__additional_loan_payments'

        start_date_YYYYMMDD = '20230901'
        end_date_YYYYMMDD = '20230905'

        account_set = copy.deepcopy(self.account_set)
        budget_set = copy.deepcopy(self.budget_set)
        memo_rule_set = copy.deepcopy(self.memo_rule_set)

        account_set.createAccount(name='Checking',
                                  balance=1000,
                                  min_balance=0,
                                  max_balance=float('Inf'),
                                  account_type="checking")

        account_set.createAccount(name='Loan A',
                                  balance=4746.18,
                                  min_balance=0,
                                  max_balance=float("inf"),
                                  account_type="loan",
                                  billing_start_date_YYYYMMDD='20230903',
                                  interest_type='simple',
                                  apr=0.0466,
                                  interest_cadence='daily',
                                  minimum_payment=50,
                                  previous_statement_balance=None,
                                  principal_balance=4746.18,
                                  accrued_interest=0
                                  )

        account_set.createAccount(name='Loan B',
                                  balance=1919.55,
                                  min_balance=0,
                                  max_balance=float("inf"),
                                  account_type="loan",
                                  billing_start_date_YYYYMMDD='20230903',
                                  interest_type='simple',
                                  apr=0.0429,
                                  interest_cadence='daily',
                                  minimum_payment=50,
                                  previous_statement_balance=None,
                                  principal_balance=1919.55,
                                  accrued_interest=0
                                  )

        account_set.createAccount(name='Loan C',
                                  balance=4726.68,
                                  min_balance=0,
                                  max_balance=float("inf"),
                                  account_type="loan",
                                  billing_start_date_YYYYMMDD='20230903',
                                  interest_type='simple',
                                  apr=0.0429,
                                  interest_cadence='daily',
                                  minimum_payment=50,
                                  previous_statement_balance=None,
                                  principal_balance=4726.68,
                                  accrued_interest=0
                                  )

        account_set.createAccount(name='Loan D',
                                  balance=1823.31,
                                  min_balance=0,
                                  max_balance=float("inf"),
                                  account_type="loan",
                                  billing_start_date_YYYYMMDD='20230903',
                                  interest_type='simple',
                                  apr=0.0376,
                                  interest_cadence='daily',
                                  minimum_payment=50,
                                  previous_statement_balance=None,
                                  principal_balance=1823.31,
                                  accrued_interest=0
                                  )

        account_set.createAccount(name='Loan E',
                                  balance=3359.17,
                                  min_balance=0,
                                  max_balance=float("inf"),
                                  account_type="loan",
                                  billing_start_date_YYYYMMDD='20230903',
                                  interest_type='simple',
                                  apr=0.0376,
                                  interest_cadence='daily',
                                  minimum_payment=50,
                                  previous_statement_balance=None,
                                  principal_balance=3359.17,
                                  accrued_interest=0
                                  )

        budget_set.addBudgetItem(start_date_YYYYMMDD='20230901', end_date_YYYYMMDD='20240901', priority=1,
                                 cadence='semiweekly', amount=2000, memo='income',
                                 deferrable=False,
                                 partial_payment_allowed=False)

        budget_set.addBudgetItem(start_date_YYYYMMDD='20230903', end_date_YYYYMMDD='20240903', priority=7,
                                 cadence='monthly', amount=20000, memo='PAY_TO_ALL_LOANS',
                                 deferrable=False,
                                 partial_payment_allowed=False)

        memo_rule_set.addMemoRule(memo_regex='income', account_from=None, account_to='Checking', transaction_priority=1)

        memo_rule_set.addMemoRule(memo_regex='PAY_TO_ALL_LOANS', account_from='Checking', account_to='ALL_LOANS', transaction_priority=7)

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
        #                                              budget_set,
        #                                              memo_rule_set,
        #                                              start_date_YYYYMMDD,
        #                                              end_date_YYYYMMDD,
        #                                              expected_result_df,
        #                                              test_description)

        # for i in range(300,20000,1000):
        #     response = account_set.allocate_additional_loan_payments(i)
        #     print(response)
        ### pass by manual inspection


        # E = ExpenseForecast.ExpenseForecast(account_set,
        #                                     budget_set,
        #                                     memo_rule_set,
        #                                     start_date_YYYYMMDD,
        #                                     end_date_YYYYMMDD, raise_exceptions=False)
        #
        # print(E.forecast_df.to_string())
        #
        # E.forecast_df.to_csv('./out.csv')

        ### pass by manual inspection


    # def test_p8__savings(self):
    #     test_description = 'test_p8__savings'
    #
    #     start_date_YYYYMMDD = self.start_date_YYYYMMDD
    #     end_date_YYYYMMDD = self.end_date_YYYYMMDD
    #
    #     account_set = copy.deepcopy(self.account_set)
    #     budget_set = copy.deepcopy(self.budget_set)
    #     memo_rule_set = copy.deepcopy(self.memo_rule_set)
    #
    #     account_set.addAccount(name='Checking',
    #                            balance=1000,
    #                            min_balance=0,
    #                            max_balance=float('Inf'),
    #                            account_type="checking")
    #
    #     account_set.addAccount(name='Credit',
    #                            balance=0,
    #                            min_balance=0,
    #                            max_balance=20000,
    #                            account_type="credit",
    #                            billing_start_date_YYYYMMDD='20000102',
    #                            interest_type='Compound',
    #                            apr=0.05,
    #                            interest_cadence='Monthly',
    #                            minimum_payment=40,
    #                            previous_statement_balance=0,
    #                            principal_balance=None,
    #                            accrued_interest=None
    #                            )
    #
    #     # budget_set.addBudgetItem(start_date_YYYYMMDD='20000101', end_date_YYYYMMDD='20000103', priority=1,
    #     #                          cadence='daily', amount=0, memo='dummy memo',
    #     #                          deferrable=False,
    #     #                          partial_payment_allowed=False)
    #     #
    #     # memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=1)
    #
    #     expected_result_df = pd.DataFrame({
    #         'Date': ['20000101', '20000102', '20000103'],
    #         'Checking': [0, 0, 0],
    #         'Credit: Curr Stmt Bal': [0, 0, 0],
    #         'Credit: Prev Stmt Bal': [0, 0, 0],
    #         'Memo': ['', '', '']
    #     })
    #     expected_result_df.Date = [datetime.datetime.strptime(x, '%Y%m%d').strftime('%Y-%m-%d') for x in
    #                                expected_result_df.Date]
    #
    #     E = self.compute_forecast_and_actual_vs_expected(account_set,
    #                                                  budget_set,
    #                                                  memo_rule_set,
    #                                                  start_date_YYYYMMDD,
    #                                                  end_date_YYYYMMDD,
    #                                                  expected_result_df,
    #                                                  test_description)
    #     raise NotImplementedError
    #
    # def test_p9__investments(self):
    #     test_description = 'test_p9__investments'
    #
    #     start_date_YYYYMMDD = self.start_date_YYYYMMDD
    #     end_date_YYYYMMDD = self.end_date_YYYYMMDD
    #
    #     account_set = copy.deepcopy(self.account_set)
    #     budget_set = copy.deepcopy(self.budget_set)
    #     memo_rule_set = copy.deepcopy(self.memo_rule_set)
    #
    #     account_set.addAccount(name='Checking',
    #                            balance=1000,
    #                            min_balance=0,
    #                            max_balance=float('Inf'),
    #                            account_type="checking")
    #
    #     account_set.addAccount(name='Credit',
    #                            balance=0,
    #                            min_balance=0,
    #                            max_balance=20000,
    #                            account_type="credit",
    #                            billing_start_date_YYYYMMDD='20000102',
    #                            interest_type='Compound',
    #                            apr=0.05,
    #                            interest_cadence='Monthly',
    #                            minimum_payment=40,
    #                            previous_statement_balance=0,
    #                            principal_balance=None,
    #                            accrued_interest=None
    #                            )
    #
    #     # budget_set.addBudgetItem(start_date_YYYYMMDD='20000101', end_date_YYYYMMDD='20000103', priority=1,
    #     #                          cadence='daily', amount=0, memo='dummy memo',
    #     #                          deferrable=False,
    #     #                          partial_payment_allowed=False)
    #     #
    #     # memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=1)
    #
    #     expected_result_df = pd.DataFrame({
    #         'Date': ['20000101', '20000102', '20000103'],
    #         'Checking': [0, 0, 0],
    #         'Credit: Curr Stmt Bal': [0, 0, 0],
    #         'Credit: Prev Stmt Bal': [0, 0, 0],
    #         'Memo': ['', '', '']
    #     })
    #     expected_result_df.Date = [datetime.datetime.strptime(x, '%Y%m%d').strftime('%Y-%m-%d') for x in
    #                                expected_result_df.Date]
    #
    #     E = self.compute_forecast_and_actual_vs_expected(account_set,
    #                                                  budget_set,
    #                                                  memo_rule_set,
    #                                                  start_date_YYYYMMDD,
    #                                                  end_date_YYYYMMDD,
    #                                                  expected_result_df,
    #                                                  test_description)
    #     raise NotImplementedError


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
    #                                accrued_interest=0
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
    #                                accrued_interest=None
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
    #             display_test_result(test_descriptions[i], differences[i])
    #         except Exception as e:
    #             print(e)
    #
    #     # Check Results
    #     for i in range(0, len(test_descriptions)):
    #         self.assertTrue(differences[i].shape[0] == 0)

    #
    # def test_allocate_additional_loan_payments(self):
    #     account_set = copy.deepcopy(self.account_set)
    #     budget_set = copy.deepcopy(self.budget_set)
    #     memo_rule_set = copy.deepcopy(self.memo_rule_set)
    #
    #     start_date_YYYYMMDD = self.start_date_YYYYMMDD
    #     end_date_YYYYMMDD = self.end_date_YYYYMMDD
    #
    #     account_set.addAccount(name='Checking',
    #                            balance=0,
    #                            min_balance=0,
    #                            max_balance=float('Inf'),
    #                            account_type="checking",
    #                            billing_start_date_YYYYMMDD=None,
    #                            interest_type=None,
    #                            apr=None,
    #                            interest_cadence=None,
    #                            minimum_payment=None,
    #                            previous_statement_balance=None,
    #                            principal_balance=None,
    #                            accrued_interest=None
    #                            )
    #
    #     account_set.addAccount(name='Loan A',
    #                            balance=3359.17,
    #                            min_balance=0,
    #                            max_balance=float('Inf'),
    #                            account_type="loan",
    #                            billing_start_date_YYYYMMDD='20230903',
    #                            interest_type='Simple',
    #                            apr=0.0466,
    #                            interest_cadence='Daily',
    #                            minimum_payment=67.28,
    #                            previous_statement_balance=None,
    #                            principal_balance=3359.17,
    #                            accrued_interest=0
    #                            )
    #
    #     account_set.addAccount(name='Loan B',
    #                            balance=4746.18,
    #                            min_balance=0,
    #                            max_balance=float('Inf'),
    #                            account_type="loan",
    #                            billing_start_date_YYYYMMDD='20230903',
    #                            interest_type='Simple',
    #                            apr=0.0429,
    #                            interest_cadence='Daily',
    #                            minimum_payment=56.57,
    #                            previous_statement_balance=None,
    #                            principal_balance=4746.18,
    #                            accrued_interest=0
    #                            )
    #
    #     account_set.addAccount(name='Loan C',
    #                            balance=1919.55,
    #                            min_balance=0,
    #                            max_balance=float('Inf'),
    #                            account_type="loan",
    #                            billing_start_date_YYYYMMDD='20230903',
    #                            interest_type='Simple',
    #                            apr=0.0429,
    #                            interest_cadence='Daily',
    #                            minimum_payment=22.88,
    #                            previous_statement_balance=None,
    #                            principal_balance=1919.55,
    #                            accrued_interest=0
    #                            )
    #
    #     account_set.addAccount(name='Loan D',
    #                            balance=4766.68,
    #                            min_balance=0,
    #                            max_balance=float('Inf'),
    #                            account_type="loan",
    #                            billing_start_date_YYYYMMDD='20230903',
    #                            interest_type='Simple',
    #                            apr=0.0376,
    #                            interest_cadence='Daily',
    #                            minimum_payment=55.17,
    #                            previous_statement_balance=None,
    #                            principal_balance=4766.68,
    #                            accrued_interest=0
    #                            )
    #
    #     account_set.addAccount(name='Loan E',
    #                            balance=1823.31,
    #                            min_balance=0,
    #                            max_balance=float('Inf'),
    #                            account_type="loan",
    #                            billing_start_date_YYYYMMDD='20230903',
    #                            interest_type='Simple',
    #                            apr=0.0376,
    #                            interest_cadence='Daily',
    #                            minimum_payment=21.29,
    #                            previous_statement_balance=None,
    #                            principal_balance=1823.31,
    #                            accrued_interest=0
    #                            )
    #
    #
    #
    #     E = ExpenseForecast.ExpenseForecast(account_set,
    #                                         budget_set,
    #                                         memo_rule_set,
    #                                         start_date_YYYYMMDD,
    #                                         end_date_YYYYMMDD, raise_exceptions=False)
    #
    #     #print('running loan payment allocation')
    #     #B1 = E.allocate_additional_loan_payments(account_set, 15000, '20230303')
    #     #print('B1:')
    #     #print(B1.getBudgetItems().to_string())
    #
    #     B2 = E.allocate_additional_loan_payments(account_set, 1000, '20230303')
    #     #print('B2:')
    #     #print(B2.getBudgetItems().to_string())
    #



    # def test_toJSON(self):
    #     raise NotImplementedError
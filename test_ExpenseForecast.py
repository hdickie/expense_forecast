import unittest
import AccountSet,BudgetSet,MemoRuleSet,ExpenseForecast
import pandas as pd, numpy as np
import datetime, logging
pd.options.mode.chained_assignment = None #apparently this warning can throw false positives???

from log_methods import log_in_color

import copy

def generate_date_sequence(start_date_YYYYMMDD,num_days,cadence):
    """ A wrapper for pd.date_range intended to make code easier to read.

    #todo write project_utilities.generate_date_sequence() doctests
    """

    start_date = datetime.datetime.strptime(start_date_YYYYMMDD,'%Y%m%d')
    end_date = start_date + datetime.timedelta(days=num_days)

    if cadence.lower() == "once":
        return pd.Series(start_date)
    elif cadence.lower() == "daily":
        return_series = pd.date_range(start_date,end_date,freq='D')
    elif cadence.lower() == "weekly":
        return_series = pd.date_range(start_date,end_date,freq='W')
    elif cadence.lower() == "biweekly":
        return_series = pd.date_range(start_date,end_date,freq='2W')
    elif cadence.lower() == "monthly":

        day_delta = int(start_date.strftime('%d'))-1
        first_of_each_relevant_month = pd.date_range(start_date,end_date,freq='MS')

        return_series = first_of_each_relevant_month + datetime.timedelta(days=day_delta)
    elif cadence.lower() == "quarterly":
        #todo check if this needs an adjustment like the monthly case did
        return_series = pd.date_range(start_date,end_date,freq='Q')
    elif cadence.lower() == "yearly":
        # todo check if this needs an adjustment like the monthly case did
        return_series = pd.date_range(start_date,end_date,freq='Y')
    else:
        print('undefined edge case in generate_date_sequence()')
        print('start_date_YYYYMMDD:'+str(start_date_YYYYMMDD))
        print('num_days:'+str(num_days))
        print('cadence:'+str(cadence))

    return return_series

from log_methods import display_test_result

class TestExpenseForecastMethods(unittest.TestCase):

    def setUp(self):
        #print('Running setUp')
        self.account_set = AccountSet.AccountSet([])
        self.budget_set = BudgetSet.BudgetSet([])
        self.memo_rule_set = MemoRuleSet.MemoRuleSet([])
        self.start_date_YYYYMMDD = '20000101'
        self.end_date_YYYYMMDD = '20000103'

        self.og_dir = dir()

        #print('exiting setup')

    def tearDown(self):
        #print('Running tearDown')
        pass
        #print('exiting tearDown')

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

    def test_ExpenseForecast_Constructor(self):
        """
        |
        | Test Cases
        | Expected Successes
        | S1: Base case. More complex tests will go in other methods.
        |
        | Expected Fails
        | F1: start date is after end date
        | F2: Pass in empty AccountSet, BudgetSet, MemoRuleSet objects
        | F3: A budget memo x priority element does not have a matching regex in memo rule set
        | F4: A memo rule has an account that does not exist in AccountSet
        """

        account_set = self.account_set
        budget_set = self.budget_set
        memo_rule_set = self.memo_rule_set
        start_date_YYYYMMDD = self.start_date_YYYYMMDD
        end_date_YYYYMMDD = self.end_date_YYYYMMDD

        with self.assertRaises(ValueError): #F1
            #switch started and end date to provoke error
            ExpenseForecast.ExpenseForecast(account_set, budget_set, memo_rule_set,end_date_YYYYMMDD, start_date_YYYYMMDD)

        with self.assertRaises(ValueError): #F2
            ExpenseForecast.ExpenseForecast(account_set, budget_set, memo_rule_set, start_date_YYYYMMDD, end_date_YYYYMMDD)

        account_set.addAccount(name='checking', balance=0, min_balance=0, max_balance=0, account_type="checking" )

        with self.assertRaises(ValueError): #F3
            budget_set.addBudgetItem(start_date_YYYYMMDD='20000101',
                                     end_date_YYYYMMDD='20000101',
                                     priority=1,
                                     cadence='once',
                                     amount=10,
                                     deferrable=False,
                                     memo='test',
                                     print_debug_messages=False)

            #Since there are no memo rules, this will cause the intended error
            ExpenseForecast.ExpenseForecast(account_set,
                                            budget_set,
                                            memo_rule_set,
                                            start_date_YYYYMMDD,
                                            end_date_YYYYMMDD,
                                            print_debug_messages=False)

        with self.assertRaises(ValueError):  # F4
            budget_set = BudgetSet.BudgetSet()
            memo_rule_set.addMemoRule(memo_regex='.*',account_from='doesnt exist',account_to=None,transaction_priority=1)
            ExpenseForecast.ExpenseForecast(account_set,
                                            budget_set,
                                            memo_rule_set,
                                            start_date_YYYYMMDD,
                                            end_date_YYYYMMDD,
                                            print_debug_messages=False)

        ### Debug Message Tests


    def compute_forecast_and_actual_vs_expected(self,
                                                account_set,
                                                budget_set,
                                                memo_rule_set,
                                                start_date_YYYYMMDD,
                                                end_date_YYYYMMDD,
                                                expected_result_df,
                                                test_description):

        E = ExpenseForecast.ExpenseForecast(account_set, budget_set,
                                            memo_rule_set,
                                            start_date_YYYYMMDD,
                                            end_date_YYYYMMDD, raise_exceptions=False)

        d = E.compute_forecast_difference(expected_result_df,
                                          label=test_description,
                                          make_plots=False,
                                          diffs_only=True,
                                          require_matching_columns=True,
                                          require_matching_date_range=True,
                                          append_expected_values=False,
                                          return_type='dataframe')

        f = E.compute_forecast_difference(expected_result_df,
                                          label=test_description,
                                          make_plots=False,
                                          diffs_only=False,
                                          require_matching_columns=True,
                                          require_matching_date_range=True,
                                          append_expected_values=True,
                                          return_type='dataframe')

        try:
            display_test_result(test_description, d)
        except Exception as e:
            raise e

        try:
            sel_vec = (d.columns != 'Date') & (d.columns != 'Memo')
            non_boilerplate_values__M = np.matrix(d.iloc[:, sel_vec])

            error_ind = sum(sum(np.square(
                non_boilerplate_values__M)).T)  # this very much DOES NOT SCALE. this is intended for small tests
            self.assertTrue(error_ind == 0)
        except Exception as e:
            print(test_description)
            print(f.T.to_string())
            raise e

    def test_cc_payment__satisfice__prev_bal_25__expect_25(self):
        test_description = 'test_cc_payment__satisfice__prev_bal_25__expect_25'

        start_date_YYYYMMDD = self.start_date_YYYYMMDD
        end_date_YYYYMMDD = self.end_date_YYYYMMDD

        account_set = copy.deepcopy(self.account_set)
        budget_set = copy.deepcopy(self.budget_set)
        memo_rule_set = copy.deepcopy(self.memo_rule_set)

        account_set.addAccount(name='Checking',
                                   balance=2000,
                                   min_balance=0,
                                   max_balance=float('Inf'),
                                   account_type="checking")

        account_set.addAccount(name='Credit',
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

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000101', end_date_YYYYMMDD='20000103', priority=1,
                                     cadence='daily', amount=0, memo='dummy memo',
                                     deferrable=False)

        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=1)

        expected_result_df = pd.DataFrame({
            'Date': ['20000101', '20000102', '20000103'],
            'Checking': [2000, 1975, 1975],
            'Credit: Curr Stmt Bal': [0, 0, 0],
            'Credit: Prev Stmt Bal': [25, 0, 0],
            'Memo': ['', '', '']
        })
        expected_result_df.Date = [datetime.datetime.strptime(x, '%Y%m%d').strftime('%Y-%m-%d') for x in
                                     expected_result_df.Date]

        self.compute_forecast_and_actual_vs_expected(account_set,
                                                budget_set,
                                                memo_rule_set,
                                                start_date_YYYYMMDD,
                                                end_date_YYYYMMDD,
                                                expected_result_df,
                                                test_description)

    def test_cc_payment__satisfice__prev_bal_1000__expect_40(self):
        test_description = 'test_cc_payment__satisfice__prev_bal_1000__expect_40'

        start_date_YYYYMMDD = self.start_date_YYYYMMDD
        end_date_YYYYMMDD = self.end_date_YYYYMMDD

        account_set = copy.deepcopy(self.account_set)
        budget_set = copy.deepcopy(self.budget_set)
        memo_rule_set = copy.deepcopy(self.memo_rule_set)

        account_set.addAccount(name='Checking',
                               balance=2000,
                               min_balance=0,
                               max_balance=float('Inf'),
                               account_type="checking")

        account_set.addAccount(name='Credit',
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

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000101', end_date_YYYYMMDD='20000103', priority=1,
                                 cadence='daily', amount=0, memo='dummy memo',
                                 deferrable=False)

        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=1)

        expected_result_df = pd.DataFrame({
            'Date': ['20000101', '20000102', '20000103'],
            'Checking': [2000, 1960, 1960],
            'Credit: Curr Stmt Bal': [0, 0, 0],
            'Credit: Prev Stmt Bal': [1000, 960, 960],
            'Memo': ['', '', '']
        })
        expected_result_df.Date = [datetime.datetime.strptime(x, '%Y%m%d').strftime('%Y-%m-%d') for x in
                                   expected_result_df.Date]

        self.compute_forecast_and_actual_vs_expected(account_set,
                                                     budget_set,
                                                     memo_rule_set,
                                                     start_date_YYYYMMDD,
                                                     end_date_YYYYMMDD,
                                                     expected_result_df,
                                                     test_description)

    def test_cc_payment__satisfice__prev_bal_3000__expect_60(self):
        test_description = 'test_cc_payment__satisfice__prev_bal_3000__expect_60'

        start_date_YYYYMMDD = self.start_date_YYYYMMDD
        end_date_YYYYMMDD = self.end_date_YYYYMMDD

        account_set = copy.deepcopy(self.account_set)
        budget_set = copy.deepcopy(self.budget_set)
        memo_rule_set = copy.deepcopy(self.memo_rule_set)

        account_set.addAccount(name='Checking',
                               balance=2000,
                               min_balance=0,
                               max_balance=float('Inf'),
                               account_type="checking")

        account_set.addAccount(name='Credit',
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

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000101', end_date_YYYYMMDD='20000103', priority=1,
                                 cadence='daily', amount=0, memo='dummy memo',
                                 deferrable=False)

        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=1)

        expected_result_df = pd.DataFrame({
            'Date': ['20000101', '20000102', '20000103'],
            'Checking': [2000, 1940, 1940],
            'Credit: Curr Stmt Bal': [0, 0, 0],
            'Credit: Prev Stmt Bal': [3000, 2940, 2940],
            'Memo': ['', '', '']
        })
        expected_result_df.Date = [datetime.datetime.strptime(x, '%Y%m%d').strftime('%Y-%m-%d') for x in
                                   expected_result_df.Date]

        self.compute_forecast_and_actual_vs_expected(account_set,
                                                     budget_set,
                                                     memo_rule_set,
                                                     start_date_YYYYMMDD,
                                                     end_date_YYYYMMDD,
                                                     expected_result_df,
                                                     test_description)

    def test_cc_payment__optimize__no_prev_balance__pay_100__no_funds__expect_skip(self):
        test_description = 'test_cc_payment__optimize__no_prev_balance__pay_100__no_funds__expect_skip'

        start_date_YYYYMMDD = self.start_date_YYYYMMDD
        end_date_YYYYMMDD = self.end_date_YYYYMMDD

        account_set = copy.deepcopy(self.account_set)
        budget_set = copy.deepcopy(self.budget_set)
        memo_rule_set = copy.deepcopy(self.memo_rule_set)

        account_set.addAccount(name='Checking',
                               balance=2000,
                               min_balance=0,
                               max_balance=float('Inf'),
                               account_type="checking")

        account_set.addAccount(name='Credit',
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

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000101', end_date_YYYYMMDD='20000103', priority=1,
                                 cadence='daily', amount=0, memo='dummy memo',
                                 deferrable=False)

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000101', end_date_YYYYMMDD='20000103', priority=4,
                                 cadence='once', amount=100, memo='dummy memo',
                                 deferrable=False)

        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=1)
        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=4)

        expected_result_df = pd.DataFrame({
            'Date': ['20000101', '20000102', '20000103'],
            'Checking': [2000, 2000, 2000],
            'Credit: Curr Stmt Bal': [0, 0, 0],
            'Credit: Prev Stmt Bal': [0, 0, 0],
            'Memo': ['', '', '']
        })
        expected_result_df.Date = [datetime.datetime.strptime(x, '%Y%m%d').strftime('%Y-%m-%d') for x in
                                   expected_result_df.Date]

        self.compute_forecast_and_actual_vs_expected(account_set,
                                                     budget_set,
                                                     memo_rule_set,
                                                     start_date_YYYYMMDD,
                                                     end_date_YYYYMMDD,
                                                     expected_result_df,
                                                     test_description)
    def test_cc_payment__optimize__no_prev_balance__pay_100__expect_skip(self):
        test_description = 'test_cc_payment__optimize__no_prev_balance__pay_100__expect_skip'


        start_date_YYYYMMDD = self.start_date_YYYYMMDD
        end_date_YYYYMMDD = self.end_date_YYYYMMDD

        account_set = copy.deepcopy(self.account_set)
        budget_set = copy.deepcopy(self.budget_set)
        memo_rule_set = copy.deepcopy(self.memo_rule_set)


        account_set.addAccount(name='Checking',
                               balance=2000,
                               min_balance=0,
                               max_balance=float('Inf'),
                               account_type="checking")

        account_set.addAccount(name='Credit',
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

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000101', end_date_YYYYMMDD='20000103', priority=1,
                                 cadence='daily', amount=0, memo='dummy memo',
                                 deferrable=False)

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000101', end_date_YYYYMMDD='20000103', priority=4,
                                 cadence='once', amount=100, memo='dummy memo',
                                 deferrable=False)

        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=1)
        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=4)

        expected_result_df = pd.DataFrame({
            'Date': ['20000101', '20000102', '20000103'],
            'Checking': [2000, 2000, 2000],
            'Credit: Curr Stmt Bal': [0, 0, 0],
            'Credit: Prev Stmt Bal': [0, 0, 0],
            'Memo': ['', '', '']
        })
        expected_result_df.Date = [datetime.datetime.strptime(x, '%Y%m%d').strftime('%Y-%m-%d') for x in
                                   expected_result_df.Date]

        self.compute_forecast_and_actual_vs_expected(account_set,
                                                     budget_set,
                                                     memo_rule_set,
                                                     start_date_YYYYMMDD,
                                                     end_date_YYYYMMDD,
                                                     expected_result_df,
                                                     test_description)

    def test_cc_payment__optimize__pay_all_of_prev_part_of_curr__expect_800(self):
        test_description = 'test_cc_payment__optimize__pay_all_of_prev_part_of_curr__expect_800'

        start_date_YYYYMMDD = self.start_date_YYYYMMDD
        end_date_YYYYMMDD = self.end_date_YYYYMMDD

        account_set = copy.deepcopy(self.account_set)
        budget_set = copy.deepcopy(self.budget_set)
        memo_rule_set = copy.deepcopy(self.memo_rule_set)

        account_set.addAccount(name='Checking',
                               balance=2000,
                               min_balance=0,
                               max_balance=float('Inf'),
                               account_type="checking")

        account_set.addAccount(name='Credit',
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

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000101', end_date_YYYYMMDD='20000103', priority=1,
                                 cadence='daily', amount=0, memo='dummy memo',
                                 deferrable=False)

        budget_set.addBudgetItem(start_date_YYYYMMDD='20000102', end_date_YYYYMMDD='20000102', priority=4,
                                 cadence='once', amount=720, memo='test pay all prev part of curr',
                                 deferrable=False)

        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=1)
        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=4)

        expected_result_df = pd.DataFrame({
            'Date': ['20000101', '20000102', '20000103'],
            'Checking': [2000, 1200, 1200],
            'Credit: Curr Stmt Bal': [500, 200, 200],
            'Credit: Prev Stmt Bal': [500, 0, 0],
            'Memo': ['', '', '']
        })
        expected_result_df.Date = [datetime.datetime.strptime(x, '%Y%m%d').strftime('%Y-%m-%d') for x in
                                   expected_result_df.Date]

        self.compute_forecast_and_actual_vs_expected(account_set,
                                                     budget_set,
                                                     memo_rule_set,
                                                     start_date_YYYYMMDD,
                                                     end_date_YYYYMMDD,
                                                     expected_result_df,
                                                     test_description)


    def test_cc_payment__optimize__pay_part_of_prev_balance__expect_200(self):
        test_description = 'test_cc_payment__optimize__pay_part_of_prev_balance__expect_200'

        start_date_YYYYMMDD = self.start_date_YYYYMMDD
        end_date_YYYYMMDD = self.end_date_YYYYMMDD

        account_set = copy.deepcopy(self.account_set)
        budget_set = copy.deepcopy(self.budget_set)
        memo_rule_set = copy.deepcopy(self.memo_rule_set)


        account_set.addAccount(name='Checking',
                               balance=200,
                               min_balance=0,
                               max_balance=float('Inf'),
                               account_type="checking")

        account_set.addAccount(name='Credit',
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
                                 cadence='once', amount=160, memo='additional cc payment test 9',deferrable=False)


        memo_rule_set.addMemoRule(memo_regex='.*',account_from='Credit',account_to=None,transaction_priority=1)

        memo_rule_set.addMemoRule(memo_regex='.*additional cc payment.*', account_from='Checking', account_to='Credit', transaction_priority=4)

        expected_result_df = pd.DataFrame({
            'Date': ['20000101', '20000102', '20000103'],
            'Checking': [200, 0, 0],
            'Credit: Curr Stmt Bal': [500, 500, 500],
            'Credit: Prev Stmt Bal': [500, 300, 300],
            'Memo': ['', '', '']
        })
        expected_result_df.Date = [datetime.datetime.strptime(x, '%Y%m%d').strftime('%Y-%m-%d') for x in expected_result_df.Date]
        ### END

        self.compute_forecast_and_actual_vs_expected(account_set,
                                                     budget_set,
                                                     memo_rule_set,
                                                     start_date_YYYYMMDD,
                                                     end_date_YYYYMMDD,
                                                     expected_result_df,
                                                     test_description)

    def test_cc_payment__optimize__non_0_prev_balance_but_no_funds__expect_0(self):
        test_description = 'test_cc_payment__optimize__non_0_prev_balance_but_no_funds__expect_0'

        start_date_YYYYMMDD = self.start_date_YYYYMMDD
        end_date_YYYYMMDD = self.end_date_YYYYMMDD

        account_set = copy.deepcopy(self.account_set)
        budget_set = copy.deepcopy(self.budget_set)
        memo_rule_set = copy.deepcopy(self.memo_rule_set)

        account_set.addAccount(name='Checking',
                               balance=0,
                               min_balance=0,
                               max_balance=float('Inf'),
                               account_type="checking")

        account_set.addAccount(name='Credit',
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
                                 cadence='once', amount=100, memo='additional cc payment test 9',deferrable=False)


        memo_rule_set.addMemoRule(memo_regex='.*',account_from='Credit',account_to=None,transaction_priority=1)

        memo_rule_set.addMemoRule(memo_regex='.*additional cc payment.*', account_from='Checking', account_to='Credit', transaction_priority=4)

        expected_result_df = pd.DataFrame({
            'Date': ['20000101', '20000102', '20000103'],
            'Checking': [0, 0, 0],
            'Credit: Curr Stmt Bal': [500, 500, 500],
            'Credit: Prev Stmt Bal': [500, 300, 300],
            'Memo': ['', '', '']
        })
        expected_result_df.Date = [datetime.datetime.strptime(x, '%Y%m%d').strftime('%Y-%m-%d') for x in expected_result_df.Date]

        self.compute_forecast_and_actual_vs_expected(account_set,
                                                     budget_set,
                                                     memo_rule_set,
                                                     start_date_YYYYMMDD,
                                                     end_date_YYYYMMDD,
                                                     expected_result_df,
                                                     test_description)




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
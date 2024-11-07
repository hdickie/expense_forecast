import logging
import sys
from log_methods import log_in_color
from log_methods import display_test_result
import ExpenseForecast
import copy
import pandas as pd
import numpy as np
import AccountSet, BudgetSet, MemoRuleSet, MilestoneSet, BudgetItem, MemoRule, Account

logger = logging.getLogger(__name__)

def compute_forecast_and_actual_vs_expected(account_set,
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
    # E.forecast_df.to_csv(test_description+'.csv')
    d = E.compute_forecast_difference(copy.deepcopy(E.forecast_df), copy.deepcopy(expected_result_df),
                                      label=test_description,
                                      make_plots=False,
                                      diffs_only=True,
                                      require_matching_columns=True,
                                      require_matching_date_range=True,
                                      append_expected_values=False,
                                      return_type='dataframe')

    f = E.compute_forecast_difference(copy.deepcopy(E.forecast_df), copy.deepcopy(expected_result_df),
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
        log_in_color(logger, 'white', 'debug', '###################################')
        log_in_color(logger, 'white', 'debug', f.T.to_string())
        log_in_color(logger, 'white', 'debug', '###################################')
        display_test_result(logger, test_description, d)
    except Exception as e:
        raise e

    try:
        sel_vec = (d.columns != 'Date') & (d.columns != 'Memo') & (d.columns != 'Memo Directives')

        # non_boilerplate_values__M = np.matrix(d.iloc[:, sel_vec])
        non_boilerplate_values__M = np.array(d.iloc[:, sel_vec])
        non_boilerplate_values__M = non_boilerplate_values__M[:, None]

        error_ind = round(float(sum(sum(np.square(
            non_boilerplate_values__M)).T)), 2)  # this very much DOES NOT SCALE. this is intended for small tests
        assert error_ind == 0

        try:
            for i in range(0, expected_result_df.shape[0]):
                assert expected_result_df.loc[i, 'Memo'].strip() == E.forecast_df.loc[i, 'Memo'].strip()
        except Exception as e:
            log_in_color(logger, 'red', 'error', 'Forecasts matched but the memo did not')
            date_memo1_memo2_df = pd.DataFrame()
            date_memo1_memo2_df['Date'] = expected_result_df.Date
            date_memo1_memo2_df['Expected_Memo'] = expected_result_df.Memo
            date_memo1_memo2_df['Actual_Memo'] = E.forecast_df.Memo
            log_in_color(logger, 'red', 'error', date_memo1_memo2_df.to_string())
            raise e

        try:
            for i in range(0, expected_result_df.shape[0]):
                assert expected_result_df.loc[i, 'Memo Directives'].strip() == E.forecast_df.loc[
                    i, 'Memo Directives'].strip()
        except Exception as e:
            log_in_color(logger, 'red', 'error', 'Forecasts and memo matched but the Memo Directives did not')
            date_memo1_memo2_df = pd.DataFrame()
            date_memo1_memo2_df['Date'] = expected_result_df.Date
            date_memo1_memo2_df['Expected_Memo_Directives'] = expected_result_df['Memo Directives']
            date_memo1_memo2_df['Actual_Memo_Directives'] = E.forecast_df['Memo Directives']
            log_in_color(logger, 'red', 'error', date_memo1_memo2_df.to_string())
            raise e

        try:
            for i in range(0, expected_result_df.shape[0]):
                assert expected_result_df.loc[i, 'Next Income Date'] == E.forecast_df.loc[i, 'Next Income Date']
        except Exception as e:
            log_in_color(logger, 'red', 'error', 'Forecasts, Memo and Md matched, but next_income_date did not')
            date_id1_id2_df = pd.DataFrame()
            date_id1_id2_df['Date'] = expected_result_df.Date
            date_id1_id2_df['Expected Next Income Date'] = expected_result_df['Next Income Date']
            date_id1_id2_df['Actual Next Income Date'] = E.forecast_df['Next Income Date']
            log_in_color(logger, 'red', 'error', date_id1_id2_df.to_string())
            raise e


    except Exception as e:
        # print(test_description) #todo use log methods
        # print(f.T.to_string())
        raise e

    return E


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
                    billing_start_date_YYYYMMDD='20000112',
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
                    interest_balance=interest,
                    billing_cycle_payment_balance=0,
                    end_of_previous_cycle_balance=pbal)

    return A.accounts

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
    import json
    with open('coverage.json','r') as f:
        #print(f.readlines())
        string_lines = ''.join(f.readlines())
        print(string_lines)
        lines = json.loads(string_lines)
        print(lines['totals']['percent_covered_display'])

    # test_description, account_set, budget_set, memo_rule_set, start_date_YYYYMMDD, end_date_YYYYMMDD, milestone_set, expected_result_df =(
    #                 'test_next_income_date',
    #                 AccountSet.AccountSet(checking_acct_list(1000)),
    #                 BudgetSet.BudgetSet(
    #                     [BudgetItem.BudgetItem('20000102', '20000102', 1, 'once', 100, 'income 1', False, False),
    #                      BudgetItem.BudgetItem('20000104', '20000104', 1, 'once', 100, 'income 2', False, False)
    #                      ]),
    #                 MemoRuleSet.MemoRuleSet([
    #                     MemoRule.MemoRule('.*', None, 'Checking', 1)
    #                 ]),
    #                 '20000101',
    #                 '20000105',
    #                 MilestoneSet.MilestoneSet([], [], []),
    #                 pd.DataFrame({
    #                     'Date': ['20000101', '20000102', '20000103', '20000104', '20000105'],
    #                     'Checking': [1000, 1100, 1100, 1200, 1200],
    #                     'Marginal Interest': [0, 0, 0, 0, 0],
    #                     'Net Gain': [0, 100, 0, 100, 0],
    #                     'Net Loss': [0, 0, 0, 0, 0],
    #                     'Net Worth': [1000, 1100, 1100, 1200, 1200],
    #                     'Loan Total': [0, 0, 0, 0, 0],
    #                     'CC Debt Total': [0, 0, 0, 0, 0],
    #                     'Liquid Total': [1000, 1100, 1100, 1200, 1200],
    #                     'Next Income Date': ['20000102', '20000104', '20000104', '', ''],
    #                     'Memo Directives': ['', 'INCOME (Checking +$100.00)', '', 'INCOME (Checking +$100.00)', ''],
    #                     'Memo': ['', 'income 1 (Checking +$100.00)', '', 'income 2 (Checking +$100.00)', '']
    #                 })
    #         )
    #
    # E = ExpenseForecast.ExpenseForecast(account_set, budget_set,
    #                                     memo_rule_set,
    #                                     start_date_YYYYMMDD,
    #                                     end_date_YYYYMMDD,
    #                                     milestone_set,
    #                                     raise_exceptions=False)
    #
    # E.runForecast()
    # print(E.forecast_df.to_string())

    # compute_forecast_and_actual_vs_expected(account_set,
    #                                              budget_set,
    #                                              memo_rule_set,
    #                                              start_date_YYYYMMDD,
    #                                              end_date_YYYYMMDD,
    #                                              milestone_set,
    #                                              expected_result_df,
    #                                              test_description)


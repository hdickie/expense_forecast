import logging

import BudgetSet, ExpenseForecast, AccountSet, datetime, pandas as pd, MemoRuleSet, copy
pd.options.mode.chained_assignment = None #apparently this warning can throw false positives???

from log_methods import log_in_color
from log_methods import display_test_result

logger = logging.getLogger()

if __name__ == '__main__':
    log_in_color('green', 'debug', 'START SCRATCH', 0)

    case_string = 'test'

    account_set = AccountSet.AccountSet([])
    budget_set = BudgetSet.BudgetSet([])
    memo_rule_set = MemoRuleSet.MemoRuleSet([])

    if case_string == 'test':
        pass
    elif case_string == 'reallife':

        start_date_YYYYMMDD = '20230313'
        end_date_YYYYMMDD = '20231231'

        current_checking_balance = 2434.18
        current_credit_previous_statement_balance = 7351.23
        current_credit_current_statement_balance = 7456.73 - current_credit_previous_statement_balance

        account_set.addAccount(name='Checking',
                                   balance=current_checking_balance,
                                   min_balance=0,
                                   max_balance=float('Inf'),
                                   account_type="checking")

        account_set.addAccount(name='Credit',
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

        budget_set.addBudgetItem(start_date_YYYYMMDD=start_date_YYYYMMDD, end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                                     cadence='daily', amount=30, memo='food',
                                     deferrable=False)

        budget_set.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                                 cadence='monthly', amount=1918, memo='rent',
                                 deferrable=False)

        budget_set.addBudgetItem(start_date_YYYYMMDD='20230217', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                                 cadence='monthly', amount=89, memo='car insurance',
                                 deferrable=False)

        budget_set.addBudgetItem(start_date_YYYYMMDD='20230331', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                                 cadence='monthly', amount=163.09, memo='phone bill',
                                 deferrable=False)

        budget_set.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                                 cadence='monthly', amount=100, memo='internet',
                                 deferrable=False)

        budget_set.addBudgetItem(start_date_YYYYMMDD='20230219', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                                 cadence='monthly', amount=8, memo='hulu',
                                 deferrable=False)

        budget_set.addBudgetItem(start_date_YYYYMMDD='20230219', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                                 cadence='monthly', amount=15, memo='hbo max',
                                 deferrable=False)

        budget_set.addBudgetItem(start_date_YYYYMMDD='20230307', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                                 cadence='monthly', amount=33, memo='gym',
                                 deferrable=False)

        budget_set.addBudgetItem(start_date_YYYYMMDD='20230407', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                                 cadence='monthly', amount=10, memo='spotify',
                                 deferrable=False)

        budget_set.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                                 cadence='monthly', amount=100, memo='gas and bus',
                                 deferrable=False)

        budget_set.addBudgetItem(start_date_YYYYMMDD='20230221', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                                 cadence='monthly', amount=175.50, memo='health insurance',
                                 deferrable=False)

        budget_set.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                                 cadence='monthly', amount=300, memo='utilities',
                                 deferrable=False)

        budget_set.addBudgetItem(start_date_YYYYMMDD='20230102', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=4,
                                 cadence='monthly', amount=3611.5, memo='cyclical billing total',
                                 deferrable=False)

        budget_set.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                                 cadence='weekly', amount=450, memo='income',
                                 deferrable=False)

        # 1000 + 1918 + 89 + 163 + 100 + 8 + 15 + 33 + 10 + 100 + 175.5 = 3611.5 + 300 ; cyclical billing total

        memo_rule_set.addMemoRule(memo_regex='income', account_from=None, account_to='Checking', transaction_priority=1)

        memo_rule_set.addMemoRule(memo_regex='food', account_from='Credit', account_to=None, transaction_priority=1)
        memo_rule_set.addMemoRule(memo_regex='internet', account_from='Credit', account_to=None, transaction_priority=1)
        memo_rule_set.addMemoRule(memo_regex='phone bill', account_from='Credit', account_to=None, transaction_priority=1)
        memo_rule_set.addMemoRule(memo_regex='car insurance', account_from='Credit', account_to=None, transaction_priority=1)
        memo_rule_set.addMemoRule(memo_regex='health insurance', account_from='Credit', account_to=None,transaction_priority=1)
        memo_rule_set.addMemoRule(memo_regex='gas and bus', account_from='Credit', account_to=None,transaction_priority=1)
        memo_rule_set.addMemoRule(memo_regex='spotify', account_from='Credit', account_to=None,transaction_priority=1)
        memo_rule_set.addMemoRule(memo_regex='gym', account_from='Credit', account_to=None,transaction_priority=1)
        memo_rule_set.addMemoRule(memo_regex='hbo max', account_from='Credit', account_to=None,transaction_priority=1)
        memo_rule_set.addMemoRule(memo_regex='hulu', account_from='Credit', account_to=None,transaction_priority=1)
        memo_rule_set.addMemoRule(memo_regex='rent', account_from='Checking', account_to=None,transaction_priority=1)
        memo_rule_set.addMemoRule(memo_regex='utilities', account_from='Checking', account_to=None, transaction_priority=1)

        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=2)
        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=3)
        memo_rule_set.addMemoRule(memo_regex='cyclical billing total', account_from='Checking', account_to=None, transaction_priority=4)
        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None,transaction_priority=5)
        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=6)
        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=7)

        E = ExpenseForecast.ExpenseForecast(account_set,
                                            budget_set,
                                            memo_rule_set,
                                            start_date_YYYYMMDD,
                                            end_date_YYYYMMDD)

        print(E.forecast_df.to_string())

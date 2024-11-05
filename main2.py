import logging
import ExpenseForecast
import AccountSet
import Account
import BudgetSet
import MemoRuleSet
import MilestoneSet
import ForecastHandler
import AccountMilestone
import datetime
from test_ExpenseForecast import TestExpenseForecastMethods
import pandas as pd
from test_MemoRuleSet import TestMemoRuleSetMethods

if __name__ == '__main__':
      start_date_YYYYMMDD = '20000101'
      end_date_YYYYMMDD = '20000103'

      account_set = AccountSet.AccountSet([])
      budget_set = BudgetSet.BudgetSet([])
      memo_rule_set = MemoRuleSet.MemoRuleSet([])
      milestone_set = MilestoneSet.MilestoneSet(account_set, budget_set, [], [], [])

      test_description = 'test_p2_and_3__expect_skip'

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

      H = TestExpenseForecastMethods()
      E = H.compute_forecast_and_actual_vs_expected(account_set,
                                                       budget_set,
                                                       memo_rule_set,
                                                       start_date_YYYYMMDD,
                                                       end_date_YYYYMMDD,
                                                       milestone_set,
                                                       expected_result_df,
                                                       test_description)

      assert E.skipped_df.shape[0] == 1
      assert E.skipped_df['Memo'].iloc[0] == 'this should be skipped'
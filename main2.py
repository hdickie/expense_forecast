import logging
import ExpenseForecast
import AccountSet
import Account
import BudgetSet
import MemoRuleSet
import MilestoneSet
import ForecastHandler

if __name__ == '__main__':
      test_budget_set = BudgetSet.BudgetSet([])
      test_budget_set.addBudgetItem(start_date_YYYYMMDD='20220101', end_date_YYYYMMDD='20220101', priority=1,
                                    cadence='daily', amount=10, deferrable=False, memo='test',
                                    partial_payment_allowed=False
                                    # ,throw_exceptions=False
                                    )
      test_budget_set.addBudgetItem(start_date_YYYYMMDD='20220101', end_date_YYYYMMDD='20220101', priority=1,
                                    cadence='daily', amount=10, deferrable=False, memo='test',
                                    partial_payment_allowed=False
                                    # ,throw_exceptions=False
                                    )
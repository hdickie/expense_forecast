import logging
import ExpenseForecast
import AccountSet
import Account
import BudgetSet
import MemoRuleSet
import MilestoneSet
import ForecastHandler
import AccountMilestone

from test_MemoRuleSet import TestMemoRuleSetMethods

if __name__ == '__main__':
      A = AccountMilestone.AccountMilestone('Milestone_Name','Account_Name',0,100)
      print(A)
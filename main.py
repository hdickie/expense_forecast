import logging
import ExpenseForecast
import AccountSet
import BudgetSet
import MemoRuleSet
import MilestoneSet
import ForecastHandler

if __name__ == '__main__':

    start_date_YYYYMMDD = '20231011'
    end_date_YYYYMMDD = '20240101'

    account_set = AccountSet.AccountSet([])
    budget_set = BudgetSet.BudgetSet([])
    memo_rule_set = MemoRuleSet.MemoRuleSet([])

    milestone_set = MilestoneSet.MilestoneSet(account_set,budget_set,[],[],[])

    account_set.createAccount(name='Checking',
                              balance=5000,
                              min_balance=0,
                              max_balance=float('Inf'),
                              account_type="checking")

    budget_set.addBudgetItem(start_date_YYYYMMDD=start_date_YYYYMMDD, end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                             cadence='daily', amount=20, memo='food',
                             deferrable=False,
                             partial_payment_allowed=False)

    budget_set.addBudgetItem(start_date_YYYYMMDD=start_date_YYYYMMDD, end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                             cadence='semiweekly', amount=450, memo='income',
                             deferrable=False,
                             partial_payment_allowed=False)

    memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=1)
    memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=2)

    E = ExpenseForecast.ExpenseForecast(account_set, budget_set,
                                        memo_rule_set,
                                        start_date_YYYYMMDD,
                                        end_date_YYYYMMDD,
                                        milestone_set, raise_exceptions=True)
    E.runForecast()
    E.appendSummaryLines()

    F = ForecastHandler.ForecastHandler()

    F.generateHTMLReport(E)
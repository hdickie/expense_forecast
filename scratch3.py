import BudgetSet, ExpenseForecast, AccountSet, pandas as pd, MemoRuleSet, copy, ForecastHandler
import MilestoneSet, MemoRule
import BudgetItem

pd.options.mode.chained_assignment = None #apparently this warning can throw false positives???

from log_methods import log_in_color

if __name__ == '__main__':

    start_date_YYYYMMDD = '20000101'
    end_date_YYYYMMDD = '20000105'

    account_set = AccountSet.AccountSet([])
    account_set.createAccount('Checking',2000,0,99999,'checking')

    # name, balance, min_balance, max_balance, account_type, billing_start_date_YYYYMMDD, interest_type, apr,
    # interest_cadence, minimum_payment, previous_statement_balance, principal_balance, accrued_interest = None,


    budget_set = BudgetSet.BudgetSet(
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

            )

    memo_rule_set = MemoRuleSet.MemoRuleSet([MemoRule.MemoRule(memo_regex='.*',
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

    milestone_set = MilestoneSet.MilestoneSet(account_set, budget_set, [], [], [])

    E = ExpenseForecast.ExpenseForecast(account_set, budget_set,
                                        memo_rule_set,
                                        start_date_YYYYMMDD,
                                        end_date_YYYYMMDD,
                                        milestone_set,
                                        raise_exceptions=False)

    E.runForecast()
    E.appendSummaryLines()

    F = ForecastHandler.ForecastHandler()
    F.generateHTMLReport(E, './out/')
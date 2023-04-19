
import ForecastHandler, ExpenseForecast
import BudgetSet, AccountSet, MemoRuleSet
import MilestoneSet

import CompositeMilestone

if __name__ == '__main__':
    pass

    account_set = AccountSet.AccountSet([])
    budget_set = BudgetSet.BudgetSet([])

    #memo_milestones_df
    #account_milestones_df
    #composite_milestones_df

    CompositeMilestone.CompositeMilestone('milestone name 1','a','b','c')
    CompositeMilestone.CompositeMilestone('milestone name 2', 'z')

    #MS = MilestoneSet.MilestoneSet(account_set,budget_set,memo_milestones_df,account_milestones_df,composite_milestones_df)

    # F = ForecastHandler.ForecastHandler()
    #
    # F.initialize_from_excel_file('expense_forecast__input.ods')
    #
    # print(F.read_results_from_disk())

    #F.run_forecasts()

    # E1 = ExpenseForecast.initialize_from_json_file(path_to_json='Forecast__2023_04_07__14_06_02__031534.json')
    # E1.appendSummaryLines()
    #
    # E2 = ExpenseForecast.initialize_from_json_file(path_to_json='Forecast__2023_04_07__13_27_36__020658.json')
    # E2.appendSummaryLines()

    #print(E1.evaulateMemoMilestone('EMT class'))

    #F.generateCompareTwoForecastsHTMLReport(E1,E2)

    # core_budget_set = [['1']]
    #
    # CoreBudgetSet = BudgetSet.BudgetSet([])
    # CoreBudgetSet.addBudgetItem('20000101','20000101',1,'once','1','Core',deferrable=False,partial_payment_allowed=False)
    #
    # BudgetSetA2 = BudgetSet.BudgetSet([])
    # BudgetSetA2.addBudgetItem('20000101', '20000101', 1, 'once', '1', 'A2', deferrable=False, partial_payment_allowed=False)
    #
    # BudgetSetB2 = BudgetSet.BudgetSet([])
    # BudgetSetB2.addBudgetItem('20000101', '20000101', 1, 'once', '1', 'B2', deferrable=False, partial_payment_allowed=False)
    #
    # BudgetSetC3 = BudgetSet.BudgetSet([])
    # BudgetSetC3.addBudgetItem('20000101', '20000101', 1, 'once', '1', 'C3', deferrable=False, partial_payment_allowed=False)
    #
    # BudgetSetD3 = BudgetSet.BudgetSet([])
    # BudgetSetD3.addBudgetItem('20000101', '20000101', 1, 'once', '1', 'D3', deferrable=False, partial_payment_allowed=False)
    #
    # BudgetSetE3 = BudgetSet.BudgetSet([])
    # BudgetSetE3.addBudgetItem('20000101', '20000101', 1, 'once', '1', 'E3', deferrable=False, partial_payment_allowed=False)
    #
    # BudgetSetF4 = BudgetSet.BudgetSet([])
    # BudgetSetF4.addBudgetItem('20000101', '20000101', 1, 'once', '1', 'F4', deferrable=False, partial_payment_allowed=False)
    #
    # list_of_lists_of_budget_sets = [
    #     [ BudgetSetA2, BudgetSetB2 ],
    #     [ BudgetSetC3, BudgetSetD3, BudgetSetE3 ],
    #     [ BudgetSetF4 ]
    # ]
    #
    # F = ForecastHandler.ForecastHandler()
    #
    # account_set = AccountSet.AccountSet([])
    # memo_rule_set = MemoRuleSet.MemoRuleSet([])
    #
    # account_set.addAccount(name='Checking',
    #                        balance=1000,
    #                        min_balance=0,
    #                        max_balance=float('Inf'),
    #                        account_type="checking")
    #
    # memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=1)
    #
    # F.calculateMultipleChooseOne(account_set, CoreBudgetSet , memo_rule_set, '20000101', '20000103', list_of_lists_of_budget_sets)
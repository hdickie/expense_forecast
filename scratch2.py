
import ForecastHandler
import BudgetSet, AccountSet, MemoRuleSet

if __name__ == '__main__':

    core_budget_set = [['1']]

    CoreBudgetSet = BudgetSet.BudgetSet([])
    CoreBudgetSet.addBudgetItem('20000101','20000101',1,'once','1','Core',deferrable=False,partial_payment_allowed=False)

    BudgetSetA2 = BudgetSet.BudgetSet([])
    BudgetSetA2.addBudgetItem('20000101', '20000101', 1, 'once', '1', 'A2', deferrable=False, partial_payment_allowed=False)

    BudgetSetB2 = BudgetSet.BudgetSet([])
    BudgetSetB2.addBudgetItem('20000101', '20000101', 1, 'once', '1', 'B2', deferrable=False, partial_payment_allowed=False)

    BudgetSetC3 = BudgetSet.BudgetSet([])
    BudgetSetC3.addBudgetItem('20000101', '20000101', 1, 'once', '1', 'C3', deferrable=False, partial_payment_allowed=False)

    BudgetSetD3 = BudgetSet.BudgetSet([])
    BudgetSetD3.addBudgetItem('20000101', '20000101', 1, 'once', '1', 'D3', deferrable=False, partial_payment_allowed=False)

    BudgetSetE3 = BudgetSet.BudgetSet([])
    BudgetSetE3.addBudgetItem('20000101', '20000101', 1, 'once', '1', 'E3', deferrable=False, partial_payment_allowed=False)

    BudgetSetF4 = BudgetSet.BudgetSet([])
    BudgetSetF4.addBudgetItem('20000101', '20000101', 1, 'once', '1', 'F4', deferrable=False, partial_payment_allowed=False)

    list_of_lists_of_budget_sets = [
        [ BudgetSetA2, BudgetSetB2 ],
        [ BudgetSetC3, BudgetSetD3, BudgetSetE3 ],
        [ BudgetSetF4 ]
    ]

    F = ForecastHandler.ForecastHandler()

    account_set = AccountSet.AccountSet([])
    memo_rule_set = MemoRuleSet.MemoRuleSet([])

    account_set.addAccount(name='Checking',
                           balance=1000,
                           min_balance=0,
                           max_balance=float('Inf'),
                           account_type="checking")

    memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=1)

    F.calculateMultipleChooseOne(account_set, CoreBudgetSet , memo_rule_set, '20000101', '20000103', list_of_lists_of_budget_sets)
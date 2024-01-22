import pytest
import BudgetItem, BudgetSet


def example_budget_item():
    return BudgetItem.BudgetItem(start_date_YYYYMMDD='20000101', end_date_YYYYMMDD='20000101', priority=1,
                                 cadence='once',
                                 amount=10, deferrable=False, memo='test')

class TestBudgetSetMethods:

    @pytest.mark.parametrize('budget_items__list',[
        ([example_budget_item()]),
    ])
    def test_BudgetSet_Constructor(self,budget_items__list):
        BudgetSet.BudgetSet(budget_items__list)

    @pytest.mark.parametrize('start_date_YYYYMMDD,end_date_YYYYMMDD,priority,cadence,amount,memo,deferrable,partial_payment_allowed', [
        (['20000101','20000101',1,'daily',10,'test memo',False,False]),
    ])
    def test_addBudgetItem(self,start_date_YYYYMMDD,end_date_YYYYMMDD,priority,cadence,amount,memo,deferrable,partial_payment_allowed):
        test_budget_set = BudgetSet.BudgetSet([])
        test_budget_set.addBudgetItem(start_date_YYYYMMDD='20000101',end_date_YYYYMMDD='20000101', priority=1, cadence='once',
                                      amount=10, deferrable=False, memo='test 2',partial_payment_allowed=False)

    def test_getBudgetItems(self):
        test_budget_set = BudgetSet.BudgetSet([])

        test_budget_set.addBudgetItem(start_date_YYYYMMDD='20000101',end_date_YYYYMMDD='20000101',priority=1,cadence='once',
            amount=10, deferrable=False, memo='test',partial_payment_allowed=False)
        test_df = test_budget_set.getBudgetItems()
        assert test_df is not None

    def test_getBudgetSchedule(self):
        test_budget_set = BudgetSet.BudgetSet([])
        test_budget_set.addBudgetItem(start_date_YYYYMMDD='20220101',end_date_YYYYMMDD='20230101',priority=1,cadence='daily',amount=0,deferrable=False,partial_payment_allowed=False,memo='test 0')
        test_budget_set.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230101', priority=1, cadence='once', amount=0,deferrable=False,partial_payment_allowed=False, memo='test 1')
        test_budget_set.addBudgetItem(start_date_YYYYMMDD='20220101', end_date_YYYYMMDD='20230101', priority=1, cadence='weekly',amount=0,deferrable=False,partial_payment_allowed=False, memo='test 2')
        test_budget_set.addBudgetItem(start_date_YYYYMMDD='20220101', end_date_YYYYMMDD='20230101', priority=1, cadence='semiweekly',amount=0,deferrable=False,partial_payment_allowed=False, memo='test 3')
        test_budget_set.addBudgetItem(start_date_YYYYMMDD='20220101', end_date_YYYYMMDD='20230101', priority=1, cadence='monthly',amount=0,deferrable=False,partial_payment_allowed=False, memo='test 4')
        test_budget_set.addBudgetItem(start_date_YYYYMMDD='20220101', end_date_YYYYMMDD='20230101', priority=1, cadence='quarterly',amount=0,deferrable=False,partial_payment_allowed=False, memo='test 5')
        test_budget_set.addBudgetItem(start_date_YYYYMMDD='20220101', end_date_YYYYMMDD='20230101', priority=1, cadence='yearly',amount=0,deferrable=False,partial_payment_allowed=False, memo='test 6')
        test_df = test_budget_set.getBudgetSchedule('20220101','20230101')


    def test_str(self):
        test_budget_set = BudgetSet.BudgetSet([])
        budgetset_str = str(test_budget_set)
        assert budgetset_str is not None

        test_budget_set.addBudgetItem(start_date_YYYYMMDD='20220101',end_date_YYYYMMDD='20220101', priority=1,cadence='daily',amount=0,deferrable=False,memo='test',
                                      partial_payment_allowed=False
                                      #,throw_exceptions=False
                                      )
        budgetset_str = str(test_budget_set)
        assert budgetset_str is not None

    def test_duplicate_budget_items_not_allowed(self):
        test_budget_set = BudgetSet.BudgetSet([])
        with pytest.raises(ValueError):
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

    #this test is here for coverage, bc input validation would have stopped this branch of logic first
    def test_illegal_cadence_in__generate_date_sequence__internal_method(self):
        with pytest.raises(ValueError):
            BudgetSet.generate_date_sequence('20000101', 10, 'shmaily')

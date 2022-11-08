import unittest
import BudgetItem, BudgetSet

class TestBudgetSetMethods(unittest.TestCase):

    def test_BudgetSet_Constructor(self):

        test_budget_set = BudgetSet.BudgetSet()
        self.assertEqual('<class \'BudgetSet.BudgetSet\'>',str( type( test_budget_set ) ) )

        # bc duck-typing, we dont check data types, but just make sure that the fields are usable the way we want

        # check constructor with list of budgetitems
        test_budget_item = BudgetItem.BudgetItem(start_date_YYYYMMDD='20000101',priority=1,cadence='once',
            amount=10, deferrable=False, memo='test')
        self.assertEqual('<class \'BudgetSet.BudgetSet\'>', str(type(BudgetSet.BudgetSet([test_budget_item]))))

    def test_addBudgetItem(self):
        test_budget_set = BudgetSet.BudgetSet()
        test_budget_set.addBudgetItem(start_date_YYYYMMDD='20000101', priority=1, cadence='once',
                                      amount=10, deferrable=False, memo='test 2')
        self.assertEqual('<class \'BudgetSet.BudgetSet\'>', str(type(test_budget_set)))

    def test_getBudgetItems(self):
        test_budget_set = BudgetSet.BudgetSet()
        test_df = test_budget_set.getBudgetItems()
        self.assertIsNotNone(test_df)

        test_budget_set.addBudgetItem(start_date_YYYYMMDD='20000101',priority=1,cadence='once',
            amount=10, deferrable=False, memo='test')
        test_df = test_budget_set.getBudgetItems()
        self.assertIsNotNone(test_df)

    def test_getBudgetSchedule(self):
        test_budget_set = BudgetSet.BudgetSet()
        test_budget_set.addBudgetItem(start_date_YYYYMMDD='20220101',priority=1,cadence='daily',amount=0,deferrable=False,memo='test'
                                      #,throw_exceptions=False
                                      )
        test_budget_set.addBudgetItem(start_date_YYYYMMDD='20220101', priority=1, cadence='weekly',amount=0,deferrable=False, memo='test 1')
        test_budget_set.addBudgetItem(start_date_YYYYMMDD='20220101', priority=1, cadence='biweekly',amount=0,deferrable=False, memo='test 2')
        test_budget_set.addBudgetItem(start_date_YYYYMMDD='20220101', priority=1, cadence='monthly',amount=0,deferrable=False, memo='test 3')
        test_budget_set.addBudgetItem(start_date_YYYYMMDD='20220101', priority=1, cadence='quarterly',amount=0,deferrable=False, memo='test 4')
        test_budget_set.addBudgetItem(start_date_YYYYMMDD='20220101', priority=1, cadence='yearly',amount=0,deferrable=False, memo='test 5')
        test_df = test_budget_set.getBudgetSchedule('20220101',365)
        self.assertIsNotNone(test_df)
        pass

    def test_str(self):
        test_budget_set = BudgetSet.BudgetSet()
        budgetset_str = str(test_budget_set)
        self.assertIsNotNone(budgetset_str)

        test_budget_set.addBudgetItem(start_date_YYYYMMDD='20220101',priority=1,cadence='daily',amount=0,deferrable=False,memo='test'
                                      #,throw_exceptions=False
                                      )
        budgetset_str = str(test_budget_set)
        self.assertIsNotNone(budgetset_str)

    def test_repr(self):
        self.assertIsNotNone(repr(BudgetSet.BudgetSet()))
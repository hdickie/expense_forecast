import unittest
import BudgetItem, BudgetSet

class TestBudgetSetMethods(unittest.TestCase):

    def test_BudgetSet_Constructor(self):

        test_budget_set = BudgetSet.BudgetSet()
        self.assertEqual('<class \'BudgetSet.BudgetSet\'>',str( type( test_budget_set ) ) )

        # bc duck-typing, we dont check data types, but just make sure that the fields are usable the way we want

        # check constructor with list of budgetitems
        test_budget_item = BudgetItem.BudgetItem()
        self.assertEqual('<class \'BudgetSet.BudgetSet\'>', str(type(BudgetSet.BudgetSet([test_budget_item]))))

        test_budget_set.addBudgetItem(memo = 'test')
        self.assertEqual('<class \'BudgetSet.BudgetSet\'>', str(type(test_budget_set)))

    def test_getBudgetItems(self):
        test_budget_set = BudgetSet.BudgetSet()
        test_df = test_budget_set.getBudgetItems()
        self.assertIsNotNone(test_df)

        test_budget_set.addBudgetItem(memo='test')
        test_df = test_budget_set.getBudgetItems()
        self.assertIsNotNone(test_df)

    def test_getBudgetSchedule(self):
        test_budget_set = BudgetSet.BudgetSet()
        test_budget_set.addBudgetItem(start_date='20220101',priority=1,cadence='daily',memo='test')
        test_budget_set.addBudgetItem(start_date='20220101', priority=1, cadence='weekly', memo='test')
        test_budget_set.addBudgetItem(start_date='20220101', priority=1, cadence='biweekly', memo='test')
        test_budget_set.addBudgetItem(start_date='20220101', priority=1, cadence='monthly', memo='test')
        test_budget_set.addBudgetItem(start_date='20220101', priority=1, cadence='quarterly', memo='test')
        test_budget_set.addBudgetItem(start_date='20220101', priority=1, cadence='yearly', memo='test')
        test_df = test_budget_set.getBudgetSchedule('20220101',365)
        self.assertIsNotNone(test_df)
        pass

    def test_str(self):
        test_budget_set = BudgetSet.BudgetSet()
        budgetset_str = str(test_budget_set)
        self.assertIsNotNone(budgetset_str)

        test_budget_set.addBudgetItem()
        budgetset_str = str(test_budget_set)
        self.assertIsNotNone(budgetset_str)

    def test_repr(self):
        self.assertIsNotNone(repr(BudgetSet.BudgetSet()))
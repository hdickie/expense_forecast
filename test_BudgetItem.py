import unittest
import BudgetItem

class TestBudgetItemMethods(unittest.TestCase):

    def test_BudgetItemSet_Constructor(self):

        test_budget_item = BudgetItem.BudgetItem(start_date_YYYYMMDD='20000101',priority=1,cadence='once',
            amount=10, deferrable=False, memo='test')
        self.assertEqual('<class \'BudgetItem.BudgetItem\'>',str( type( test_budget_item ) ) )

        # bc duck-typing, we dont check data types, but just make sure that the fields are usable the way we want

    def test_str(self):
        self.assertIsNotNone(str(BudgetItem.BudgetItem(
            start_date_YYYYMMDD='20000101',
            priority=1,
            cadence='once',
            amount=10,
            deferrable=False,
            memo='test'
        )))

    def test_repr(self):
        self.assertIsNotNone(repr(BudgetItem.BudgetItem(
            start_date_YYYYMMDD='20000101',
            priority=1,
            cadence='once',
            amount=10,
            deferrable=False,
            memo='test'
        )))


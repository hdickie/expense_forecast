import unittest
import BudgetItem

class TestBudgetItemMethods(unittest.TestCase):

    def test_BudgetItemSet_Constructor(self):

        #todo bool() is a way more generous cast than i initially thought. maybe watch that...

        test_budget_item = BudgetItem.BudgetItem(start_date_YYYYMMDD='20000101',priority=1,cadence='once',
            amount=10, deferrable=False, memo='test')
        self.assertEqual('<class \'BudgetItem.BudgetItem\'>',str( type( test_budget_item ) ) )

        # bc duck-typing, we dont check data types, but just make sure that the fields are usable the way we want
        with self.assertRaises(TypeError):
            BudgetItem.BudgetItem(start_date_YYYYMMDD='not a date string', priority=1, cadence='once',
                                  amount=10, deferrable=False, memo='test',print_debug_messages=False)

        with self.assertRaises(TypeError):
            BudgetItem.BudgetItem(start_date_YYYYMMDD='20000101', priority='not an integer', cadence='once',
                                  amount=10, deferrable=False, memo='test',print_debug_messages=False)

        with self.assertRaises(TypeError):
            BudgetItem.BudgetItem(start_date_YYYYMMDD='20000101', priority=1, cadence='once',
                                  amount='not a float', deferrable=False, memo='test',print_debug_messages=False)

        # with self.assertRaises(TypeError):
        #     #deferrable fails cast to bool
        #     BudgetItem.BudgetItem(start_date_YYYYMMDD='20000101', priority=1, cadence='once',
        #                           amount=10, deferrable=None, memo='test')

        with self.assertRaises(ValueError):
            #priority too low
            BudgetItem.BudgetItem(start_date_YYYYMMDD='20000101', priority=0, cadence='once',
                                  amount=10, deferrable=False, memo='test',print_debug_messages=False)

        with self.assertRaises(ValueError):
            #unacceptable value for cadence
            BudgetItem.BudgetItem(start_date_YYYYMMDD='20000101', priority=1, cadence='shmonce',
                                  amount=10, deferrable=False, memo='test',print_debug_messages=False)

        with self.assertRaises(ValueError):
            BudgetItem.BudgetItem(start_date_YYYYMMDD='20000101', priority=2, cadence='once',
                                  amount=10, deferrable=False, memo='Income', print_debug_messages=False)

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

    def test_toJSON(self):
        test_budget_item = BudgetItem.BudgetItem(start_date_YYYYMMDD='20000101',priority=1,cadence='once',
            amount=10, deferrable=False, memo='test')
        test_budget_item_JSON = test_budget_item.toJSON()

        test_expectation = """{\n"Start_Date":"2000-01-01 00:00:00",\n"Priority":"1",\n"Cadence":"once",\n"Amount":"10.0",\n"Deferrable":"False",\n"Memo":"test"\n}"""

        assert test_budget_item_JSON == test_expectation


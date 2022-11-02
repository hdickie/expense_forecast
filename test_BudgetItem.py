import unittest
import BudgetItem, BudgetSet

class TestBudgetItemSetMethods(unittest.TestCase):

    def test_BudgetItemSet_Constructor(self):

        #TODO change this to use isinstance
        self.assertEqual('<class \'BudgetSet.BudgetSet\'>',str( type( BudgetSet.BudgetSet() ) ) )

        # bc duck-typing, we dont check data types, but just make sure that the fields are usable the way we want


        pass


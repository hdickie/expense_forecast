import unittest
import MemoRuleSet

class TestMemoRuleSetMethods(unittest.TestCase):

    def test_MemoRuleSet_Constructor(self):

        #TODO change this to use isinstance
        self.assertEqual('<class \'MemoRuleSet.MemoRuleSet\'>',str( type( MemoRuleSet.MemoRuleSet() ) ) )

        # bc duck-typing, we dont check data types, but just make sure that the fields are usable the way we want

        pass
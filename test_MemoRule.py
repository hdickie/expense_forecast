import unittest
import MemoRule

class TestMemoRuleMethods(unittest.TestCase):

    def test_MemoRule_Constructor(self):

        #TODO change this to use isinstance
        self.assertEqual('<class \'MemoRule.MemoRuleSet\'>',str( type( MemoRule.MemoRule() ) ) )

        # bc duck-typing, we dont check data types, but just make sure that the fields are usable the way we want


        pass


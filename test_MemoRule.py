import unittest
import MemoRule

class TestMemoRuleMethods(unittest.TestCase):

    def test_MemoRule_Constructor(self):

        self.assertEqual('<class \'MemoRule.MemoRule\'>',str( type( MemoRule.MemoRule(memo_regex='.*',account_from='',account_to='',transaction_priority=1) ) ) )

        # bc duck-typing, we dont check data types, but just make sure that the fields are usable the way we want


    def test_str(self):
        self.assertIsNotNone(str(MemoRule.MemoRule(memo_regex='.*',account_from='',account_to='',transaction_priority=1)))

    def test_repr(self):
        self.assertIsNotNone(repr(MemoRule.MemoRule(memo_regex='.*',account_from='',account_to='',transaction_priority=1)))
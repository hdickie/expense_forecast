import unittest
import MemoRule

class TestMemoRuleMethods(unittest.TestCase):

    def test_MemoRule_Constructor(self):

        self.assertEqual('<class \'MemoRule.MemoRule\'>',str( type( MemoRule.MemoRule(memo_regex='.*',account_from='',account_to='',transaction_priority=1) ) ) )

        #provoking exceptions for test coverage
        with self.assertRaises(TypeError):
            MemoRule.MemoRule(memo_regex=None,account_from=None,account_to=None,transaction_priority=None,print_debug_messages=False)

        with self.assertRaises(ValueError):
            MemoRule.MemoRule(memo_regex="*",account_from='',account_to='',transaction_priority=1,print_debug_messages=False)

    def test_MemoRule_str(self):
        self.assertIsNotNone(str(MemoRule.MemoRule(memo_regex='.*',account_from='',account_to='',transaction_priority=1)))

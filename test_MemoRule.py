import unittest
import MemoRule

class TestMemoRuleMethods(unittest.TestCase):

    def test_MemoRule_Constructor(self):

        self.assertEqual('<class \'MemoRule.MemoRule\'>',str( type( MemoRule.MemoRule(memo_regex='.*',account_from='',account_to='',transaction_priority=1) ) ) )

        #provoking exceptions for test coverage
        with self.assertRaises(TypeError):
            MemoRule.MemoRule(memo_regex=None,account_from=None,account_to=None,transaction_priority=None)

        with self.assertRaises(ValueError):
            MemoRule.MemoRule(memo_regex="*",account_from='',account_to='',transaction_priority=1)

    def test_MemoRule_str(self):
        self.assertIsNotNone(str(MemoRule.MemoRule(memo_regex='.*',account_from='',account_to='',transaction_priority=1)))

    def test_MemoRule_repr(self):
        self.assertIsNotNone(repr(MemoRule.MemoRule(memo_regex='.*',account_from='',account_to='',transaction_priority=1)))

    def test_MemoRule_toJSON(self):

        test_memo_rule = MemoRule.MemoRule(memo_regex='.*',account_from='',account_to='',transaction_priority=1)
        test_memo_rule_JSON = test_memo_rule.toJSON()
        test_expectation = """{\n"Memo_Regex":".*",\n"Account_From":"",\n"Account_To":"",\n"Transaction_Priority":"1"\n}"""

        assert test_memo_rule_JSON == test_expectation
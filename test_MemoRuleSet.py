import unittest
import MemoRuleSet, MemoRule

class TestMemoRuleSetMethods(unittest.TestCase):

    def test_MemoRuleSet_Constructor(self):

        test_memo_rule_set = MemoRuleSet.MemoRuleSet()
        self.assertEqual('<class \'MemoRuleSet.MemoRuleSet\'>',str( type( test_memo_rule_set ) ) )

        test_memo_rule = MemoRule.MemoRule(memo_regex='.*',account_from='',account_to='',transaction_priority=1)
        test_memo_rule_set = MemoRuleSet.MemoRuleSet([test_memo_rule])
        self.assertEqual('<class \'MemoRuleSet.MemoRuleSet\'>', str(type(test_memo_rule_set)))

        # bc duck-typing, we dont check data types, but just make sure that the fields are usable the way we want

        pass

    def test_str(self):
        test_memo_rule_set = MemoRuleSet.MemoRuleSet()
        self.assertIsNotNone(str( test_memo_rule_set ))

        test_memo_rule_set.addMemoRule(memo_regex='.*',account_from='',account_to='',transaction_priority=1)
        self.assertIsNotNone(str( test_memo_rule_set ))

    def test_repr(self):
        test_memo_rule_set = MemoRuleSet.MemoRuleSet()
        self.assertIsNotNone(repr(test_memo_rule_set))

        test_memo_rule_set.addMemoRule(memo_regex='.*',account_from='',account_to='',transaction_priority=1)
        self.assertIsNotNone(repr(test_memo_rule_set))

    def test_getMemoRules(self):
        test_memorule_set = MemoRuleSet.MemoRuleSet()
        test_df = test_memorule_set.getMemoRules()
        self.assertIsNotNone(test_df)

        test_memorule_set.addMemoRule(memo_regex='.*',account_from='',account_to='',transaction_priority=1)
        test_df = test_memorule_set.getMemoRules()
        self.assertIsNotNone(test_df)
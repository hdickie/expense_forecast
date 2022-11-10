import unittest
import MemoRuleSet, MemoRule

class TestMemoRuleSetMethods(unittest.TestCase):

    def test_MemoRuleSet_Constructor(self):

        test_memo_rule_set = MemoRuleSet.MemoRuleSet()
        self.assertEqual('<class \'MemoRuleSet.MemoRuleSet\'>',str( type( test_memo_rule_set ) ) )

        test_memo_rule = MemoRule.MemoRule(memo_regex='.*',account_from='noodle 2',account_to='',transaction_priority=1)
        test_memo_rule_set = MemoRuleSet.MemoRuleSet([test_memo_rule])
        self.assertEqual('<class \'MemoRuleSet.MemoRuleSet\'>', str(type(test_memo_rule_set)))

        # bc duck-typing, we dont check data types, but just make sure that the fields are usable the way we want

        pass

    def test_str(self):
        test_memo_rule_set = MemoRuleSet.MemoRuleSet()
        self.assertIsNotNone(str( test_memo_rule_set ))

        test_memo_rule_set.addMemoRule(memo_regex='.*',account_from='noodle 3',account_to='',transaction_priority=1)
        self.assertIsNotNone(str( test_memo_rule_set ))

    def test_repr(self):
        test_memo_rule_set = MemoRuleSet.MemoRuleSet()
        self.assertIsNotNone(repr(test_memo_rule_set))

        test_memo_rule_set.addMemoRule(memo_regex='.*',account_from='noodle 4',account_to='',transaction_priority=1)
        self.assertIsNotNone(repr(test_memo_rule_set))

    def test_getMemoRules(self):
        test_memorule_set = MemoRuleSet.MemoRuleSet()
        test_df = test_memorule_set.getMemoRules()
        self.assertIsNotNone(test_df)

        test_memorule_set.addMemoRule(memo_regex='.*',account_from='noodle 5',account_to='',transaction_priority=1)
        test_df = test_memorule_set.getMemoRules()
        self.assertIsNotNone(test_df)

    def test_addMemoRule(self):

        raise NotImplementedError

    def test_toJSON(self):
        test_memo_rule_set = MemoRuleSet.MemoRuleSet([MemoRule.MemoRule(memo_regex='.*', account_from='noodle', account_to='',
                                           transaction_priority=1),
                                                      MemoRule.MemoRule(memo_regex='.*', account_from='poodle',
                                                                        account_to='',
                                                                        transaction_priority=2)
                                                      ])
        test_memo_rule_set_JSON = test_memo_rule_set.toJSON()
        test_expectation = """{\n{\n"Memo_Regex":".*",\n"Account_From":"noodle",\n"Account_To":"",\n"Transaction_Priority":"1"\n},\n{\n"Memo_Regex":".*",\n"Account_From":"poodle",\n"Account_To":"",\n"Transaction_Priority":"2"\n}\n}"""

        assert test_memo_rule_set_JSON == test_expectation
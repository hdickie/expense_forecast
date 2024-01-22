import pytest

import BudgetSet
import MemoRuleSet, MemoRule

def empty_memo_rule_set():
    return MemoRuleSet.MemoRuleSet([])

def memo_rule_set_income_only():
    M = MemoRuleSet.MemoRuleSet([])
    M.addMemoRule('income',  None, 'checking',1)
    return M

def match_all_memo_rule_set():
    M = MemoRuleSet.MemoRuleSet([])
    M.addMemoRule('.*', None, 'checking', 1)
    return M

def match_all_and_income_memo_rule_set():
    M = MemoRuleSet.MemoRuleSet([])
    M.addMemoRule('.*',None,'checking',1)
    M.addMemoRule('income',  None, 'checking',1)
    return M

def income_budget_item():
    B = BudgetSet.BudgetSet([])
    B.addBudgetItem('20000101','20000101',1,'once',10,'income',False,False)
    return B

def txn_budget_item():
    B = BudgetSet.BudgetSet([])
    B.addBudgetItem('20000101','20000101',1,'once',10,'txn',False,False)
    return B


class TestMemoRuleSetMethods:

    def test_MemoRuleSet_Constructor(self):
        test_memo_rule_set = MemoRuleSet.MemoRuleSet([])
        assert test_memo_rule_set is not None

        test_memo_rule = MemoRule.MemoRule(memo_regex='.*',account_from='noodle 2',account_to='',transaction_priority=1)
        test_memo_rule_set = MemoRuleSet.MemoRuleSet([test_memo_rule])
        assert test_memo_rule_set is not None


    def test_str(self):
        test_memo_rule_set = MemoRuleSet.MemoRuleSet([])
        assert test_memo_rule_set is not None

        test_memo_rule_set.addMemoRule(memo_regex='.*',account_from='noodle 3',account_to='',transaction_priority=1)
        assert str(test_memo_rule_set) is not None

    def test_getMemoRules(self):
        test_memorule_set = MemoRuleSet.MemoRuleSet([])
        test_df = test_memorule_set.getMemoRules()
        assert test_df is not None

        test_memorule_set.addMemoRule(memo_regex='.*',account_from='noodle 5',account_to='',transaction_priority=1)
        test_df = test_memorule_set.getMemoRules()
        assert test_df is not None

    def test_addMemoRule(self):
        with pytest.raises(ValueError): #duplicate memo rule
            memo_rule_set = MemoRuleSet.MemoRuleSet([])
            memo_rule_set.addMemoRule(memo_regex=".*", account_from='', account_to='', transaction_priority=1)
            memo_rule_set.addMemoRule(memo_regex=".*", account_from='', account_to='', transaction_priority=1)

        with pytest.raises(ValueError):  # ambiguous combination of memo rules
            memo_rule_set = MemoRuleSet.MemoRuleSet([])
            memo_rule_set.addMemoRule(memo_regex=".*", account_from='a', account_to='b', transaction_priority=1)
            memo_rule_set.addMemoRule(memo_regex=".*", account_from='a', account_to='c', transaction_priority=1)

    def test_find_matching_memo_rule(self):
        M_E = empty_memo_rule_set()
        M_A = match_all_memo_rule_set()
        M_AI = match_all_and_income_memo_rule_set()
        B_I = income_budget_item()
        M_I = memo_rule_set_income_only()
        B_T = txn_budget_item()

        with pytest.raises(ValueError):
            M_E.findMatchingMemoRule(B_I.budget_items[0].memo,1) #no match found

        with pytest.raises(ValueError):
            M_AI.findMatchingMemoRule(B_I.budget_items[0].memo,1) #multiple matches

        with pytest.raises(ValueError):
            M_I.findMatchingMemoRule(B_T.budget_items[0].memo,1) #non-trivial non-match

        M_A.findMatchingMemoRule(B_I.budget_items[0].memo,1)

import pytest

from backend.core import DecisionRule, LineItemSet
from backend.core import DecisionRuleSet

import logging
logger = logging.getLogger("test.unit.DecisionRuleSet")


def empty_decision_rule_set():
    return DecisionRuleSet.DecisionRuleSet([])


def decision_rule_set_income_only():
    M = DecisionRuleSet.DecisionRuleSet([])
    M.addDecisionRule("income", None, "checking", 1)
    return M


def match_all_decision_rule_set():
    M = DecisionRuleSet.DecisionRuleSet([])
    M.addDecisionRule(".*", None, "checking", 1)
    return M


def match_all_and_income_decision_rule_set():
    M = DecisionRuleSet.DecisionRuleSet([])
    M.addDecisionRule(".*", None, "checking", 1)
    M.addDecisionRule("income", None, "checking", 1)
    return M


def income_line_item():
    B = LineItemSet.DecisionRuleSet([])
    B.addDecisionRule("20000101", "20000101", 1, "once", 10, "income", False, False)
    return B


def txn_line_item():
    B = LineItemSet.DecisionRuleSet([])
    B.addDecisionRule("20000101", "20000101", 1, "once", 10, "txn", False, False)
    return B


class TestMemoRuleSetMethods:

    @pytest.mark.unit
    def test_DecisionRuleSet_Constructor(self):
        test_memo_rule_set = DecisionRuleSet.DecisionRuleSet([])
        assert test_memo_rule_set is not None

        test_memo_rule = DecisionRule.DecisionRule(
            memo_regex=".*",
            account_from="noodle 2",
            account_to="",
            transaction_priority=1,
        )
        test_memo_rule_set = DecisionRuleSet.DecisionRuleSet([test_memo_rule])
        assert test_memo_rule_set is not None

    @pytest.mark.unit
    def test_str(self):
        test_memo_rule_set = DecisionRuleSet.DecisionRuleSet([])
        assert test_memo_rule_set is not None

        test_memo_rule_set.addDecisionRule(
            memo_regex=".*",
            account_from="noodle 3",
            account_to="",
            transaction_priority=1,
        )
        assert str(test_memo_rule_set) is not None

    @pytest.mark.unit
    def test_getDecisionRules(self):
        test_memorule_set = DecisionRuleSet.DecisionRuleSet([])
        test_df = test_memorule_set.getDecisionRules()
        assert test_df is not None

        test_memorule_set.addDecisionRule(
            memo_regex=".*",
            account_from="noodle 5",
            account_to="",
            transaction_priority=1,
        )
        test_df = test_memorule_set.getDecisionRules()
        assert test_df is not None

    @pytest.mark.unit
    def test_addDecisionRule(self):
        with pytest.raises(ValueError):  # duplicate memo rule
            memo_rule_set = DecisionRuleSet.DecisionRuleSet([])
            memo_rule_set.addDecisionRule(
                memo_regex=".*", account_from="", account_to="", transaction_priority=1
            )
            memo_rule_set.addDecisionRule(
                memo_regex=".*", account_from="", account_to="", transaction_priority=1
            )

        with pytest.raises(ValueError):  # ambiguous combination of memo rules
            memo_rule_set = DecisionRuleSet.DecisionRuleSet([])
            memo_rule_set.addDecisionRule(
                memo_regex=".*",
                account_from="a",
                account_to="b",
                transaction_priority=1,
            )
            memo_rule_set.addDecisionRule(
                memo_regex=".*",
                account_from="a",
                account_to="c",
                transaction_priority=1,
            )

    @pytest.mark.unit
    def test_find_matching_memo_rule(self):
        M_E = empty_decision_rule_set()
        M_A = match_all_decision_rule_set()
        M_AI = match_all_and_income_decision_rule_set()
        B_I = income_line_item()
        M_I = decision_rule_set_income_only()
        B_T = txn_line_item()

        with pytest.raises(ValueError):
            M_E.findMatchingDecisionRule(B_I.budget_items[0].memo, 1)  # no match found

        with pytest.raises(ValueError):
            M_AI.findMatchingDecisionRule(B_I.budget_items[0].memo, 1)  # multiple matches

        with pytest.raises(ValueError):
            M_I.findMatchingDecisionRule(
                B_T.budget_items[0].memo, 1
            )  # non-trivial non-match

        M_A.findMatchingDecisionRule(B_I.budget_items[0].memo, 1)

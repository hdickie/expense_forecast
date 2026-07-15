import pytest
from datetime import date

from expense_forecast.LineItemSet import LineItemSet
from expense_forecast.MemoRuleSet import MemoRuleSet
from expense_forecast.MemoRule import MemoRule


def empty_memo_rule_set():
    return MemoRuleSet([])


def memo_rule_set_income_only():
    M = MemoRuleSet([])
    M.addMemoRule("income", None, "checking", 1)
    return M


def match_all_memo_rule_set():
    M = MemoRuleSet([])
    M.addMemoRule(".*", None, "checking", 1)
    return M


def match_all_and_income_memo_rule_set():
    M = MemoRuleSet([])
    M.addMemoRule(".*", None, "checking", 1)
    M.addMemoRule("income", None, "checking", 1)
    return M


def income_budget_item():
    B = LineItemSet([])
    B.addLineItem(
        date(2000, 1, 1),
        date(2000, 1, 1),
        1,
        "once",
        10,
        "income",
        deferrable=False,
        partial_payment_allowed=False,
    )
    return B


def txn_budget_item():
    B = LineItemSet([])
    B.addLineItem(
        date(2000, 1, 1),
        date(2000, 1, 1),
        1,
        "once",
        10,
        "txn",
        deferrable=False,
        partial_payment_allowed=False,
    )
    return B


class TestMemoRuleSetMethods:

    @pytest.mark.unit
    def test_MemoRuleSet_Constructor(self):
        test_memo_rule_set = MemoRuleSet([])
        assert test_memo_rule_set is not None

        test_memo_rule = MemoRule(
            memo_regex=".*",
            account_from="noodle 2",
            account_to=None,
            transaction_priority=1,
        )
        test_memo_rule_set = MemoRuleSet([test_memo_rule])
        assert test_memo_rule_set is not None

    @pytest.mark.unit
    def test_str(self):
        test_memo_rule_set = MemoRuleSet([])
        assert test_memo_rule_set is not None

        test_memo_rule_set.addMemoRule(
            memo_regex=".*",
            account_from="noodle 3",
            account_to=None,
            transaction_priority=1,
        )
        assert str(test_memo_rule_set) is not None

    @pytest.mark.unit
    def test_getMemoRules(self):
        test_memorule_set = MemoRuleSet([])
        test_df = test_memorule_set.getMemoRules()
        assert test_df is not None

        test_memorule_set.addMemoRule(
            memo_regex=".*",
            account_from="noodle 5",
            account_to=None,
            transaction_priority=1,
        )
        test_df = test_memorule_set.getMemoRules()
        assert test_df is not None

    @pytest.mark.unit
    def test_addMemoRule(self):
        with pytest.raises(ValueError):  # duplicate memo rule
            memo_rule_set = MemoRuleSet([])
            memo_rule_set.addMemoRule(
                memo_regex=".*", account_from="checking", account_to=None, transaction_priority=1
            )
            memo_rule_set.addMemoRule(
                memo_regex=".*", account_from="checking", account_to=None, transaction_priority=1
            )

        with pytest.raises(ValueError):  # ambiguous combination of memo rules
            memo_rule_set = MemoRuleSet([])
            memo_rule_set.addMemoRule(
                memo_regex=".*",
                account_from="a",
                account_to="b",
                transaction_priority=1,
            )
            memo_rule_set.addMemoRule(
                memo_regex=".*",
                account_from="a",
                account_to="c",
                transaction_priority=1,
            )

    @pytest.mark.unit
    def test_find_matching_memo_rule(self):
        M_E = empty_memo_rule_set()
        M_A = match_all_memo_rule_set()
        M_AI = match_all_and_income_memo_rule_set()
        B_I = income_budget_item()
        M_I = memo_rule_set_income_only()
        B_T = txn_budget_item()

        with pytest.raises(Exception):
            M_E.findMatchingMemoRule(B_I.line_items[0].memo, 1)  # no match found

        with pytest.raises(Exception):
            M_AI.findMatchingMemoRule(B_I.line_items[0].memo, 1)  # multiple matches

        with pytest.raises(Exception):
            M_I.findMatchingMemoRule(
                B_T.line_items[0].memo, 1
            )  # non-trivial non-match

        M_A.findMatchingMemoRule(B_I.line_items[0].memo, 1)

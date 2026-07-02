import unittest
import re

from expense_forecast.MemoRule import MemoRule
import pytest


class TestMemoRuleMethods(unittest.TestCase):

    @pytest.mark.unit
    def test_MemoRule_Constructor(self):

        self.assertIsInstance(
            MemoRule(
                memo_regex=".*",
                account_from="checking",
                account_to=None,
                transaction_priority=1,
            ),
            MemoRule,
        )

        # provoking exceptions for test coverage
        with self.assertRaises(TypeError):
            MemoRule(
                memo_regex=None,
                account_from=None,
                account_to=None,
                transaction_priority=None,
                print_debug_messages=False,
            )

        with self.assertRaises(re.PatternError):
            MemoRule(
                memo_regex="*",
                account_from="checking",
                account_to=None,
                transaction_priority=1,
            )

    @pytest.mark.unit
    def test_MemoRule_str(self):
        self.assertIsNotNone(
            str(
                MemoRule(
                    memo_regex=".*",
                    account_from="checking",
                    account_to=None,
                    transaction_priority=1,
                )
            )
        )

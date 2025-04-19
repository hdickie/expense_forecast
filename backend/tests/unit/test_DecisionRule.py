import unittest
from backend.core import DecisionRule
import pytest

import logging
logger = logging.getLogger("test.unit.MemoRule")

class TestMemoRuleMethods(unittest.TestCase):

    @pytest.mark.unit
    def test_MemoRule_Constructor(self):

        self.assertEqual(
            "<class 'MemoRule.MemoRule'>",
            str(
                type(
                    DecisionRule.MemoRule(
                        memo_regex=".*",
                        account_from="",
                        account_to="",
                        transaction_priority=1,
                    )
                )
            ),
        )

        # provoking exceptions for test coverage
        with self.assertRaises(TypeError):
            DecisionRule.MemoRule(
                memo_regex=None,
                account_from=None,
                account_to=None,
                transaction_priority=None,
                print_debug_messages=False,
            )

        with self.assertRaises(ValueError):
            DecisionRule.MemoRule(
                memo_regex="*",
                account_from="",
                account_to="",
                transaction_priority=1,
                print_debug_messages=False,
            )

    @pytest.mark.unit
    def test_MemoRule_str(self):
        self.assertIsNotNone(
            str(
                DecisionRule.MemoRule(
                    memo_regex=".*",
                    account_from="",
                    account_to="",
                    transaction_priority=1,
                )
            )
        )

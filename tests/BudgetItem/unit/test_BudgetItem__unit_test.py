import pytest
from datetime import date

from expense_forecast.BudgetItem import BudgetItem


class TestBudgetItemMethods:

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "start_date,end_date,priority,cadence,amount,memo,deferrable,partial_payment_allowed",
        # (start_date,
        # end_date,
        # priority,
        # cadence,
        # amount,
        # memo,
        # deferrable,
        # partial_payment_allowed),
        [
            (date(2000, 1, 1), date(2000, 1, 1), 1, "daily", 10, "test memo", False, False),
        ],
    )
    def test_BudgetItem_Constructor__valid_inputs(
        self,
        start_date,
        end_date,
        priority,
        cadence,
        amount,
        memo,
        deferrable,
        partial_payment_allowed,
    ):
        BudgetItem(
            start_date,
            end_date,
            priority,
            cadence,
            amount,
            memo,
            deferrable=deferrable,
            partial_payment_allowed=partial_payment_allowed,
        )

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "start_date,end_date,priority,cadence,amount,memo,deferrable,partial_payment_allowed,income_flag",
        # (start_date,
        # end_date,
        # priority,
        # cadence,
        # amount,
        # memo,
        # deferrable,
        # partial_payment_allowed),
        [
            (
                "X",
                date(2000, 1, 1),
                1,
                "daily",
                10,
                "test memo",
                False,
                False,
                False,
            ),  # malformed start date string
            (
                date(2000, 1, 1),
                "X",
                1,
                "daily",
                10,
                "test memo",
                False,
                False,
                False,
            ),  # malformed end date string
            (
                date(2000, 1, 1),
                date(2000, 1, 1),
                "X",
                "daily",
                10,
                "test memo",
                False,
                False,
                False,
            ),  # priority is not an int
            (
                date(2000, 1, 1),
                date(2000, 1, 1),
                1,
                "daily",
                "X",
                "test memo",
                False,
                False,
                False,
            ),  # amount is not a float
            (
                date(2000, 1, 1),
                date(2000, 1, 1),
                0,
                "daily",
                10,
                "test memo",
                False,
                False,
                False,
            ),  # priority is less than 1
            (
                date(2000, 1, 1),
                date(2000, 1, 1),
                1,
                "shmaily",
                10,
                "test memo",
                False,
                False,
                False,
            ),  # illegal cadence value
            (
                date(2000, 1, 1),
                date(2000, 1, 1),
                2,
                "daily",
                10,
                "income",
                False,
                False,
                True,
            ),  # priority not 1 for income
            (
                date(2000, 1, 1),
                date(2000, 1, 1),
                1,
                "daily",
                10,
                "test",
                True,
                False,
                False,
            ),  # deferrable must be false for p1
            (
                date(2000, 1, 1),
                date(2000, 1, 1),
                1,
                "daily",
                10,
                "test",
                False,
                True,
                False,
            ),  # partial_payment_allowed must be false for p1
        ],
    )
    def test_BudgetItem_Constructor__invalid_inputs(
        self,
        start_date,
        end_date,
        priority,
        cadence,
        amount,
        memo,
        deferrable,
        partial_payment_allowed,
        income_flag,
    ):
        with pytest.raises(Exception):
            BudgetItem(
                start_date,
                end_date,
                priority,
                cadence,
                amount,
                memo,
                deferrable=deferrable,
                partial_payment_allowed=partial_payment_allowed,
                income_flag=income_flag,
            )

    @pytest.mark.unit
    @pytest.mark.skip(reason="this test needs to be improved")
    def test_to_str(self):
        B = BudgetItem(
            date(2000, 1, 1),
            date(2000, 1, 1),
            1,
            "daily",
            10,
            "test",
            deferrable=False,
            partial_payment_allowed=False,
        )
        str(B)

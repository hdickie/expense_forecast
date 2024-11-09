import pytest
import BudgetItem


class TestBudgetItemMethods:

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "start_date_YYYYMMDD,end_date_YYYYMMDD,priority,cadence,amount,memo,deferrable,partial_payment_allowed",
        # (start_date_YYYYMMDD,
        # end_date_YYYYMMDD,
        # priority,
        # cadence,
        # amount,
        # memo,
        # deferrable,
        # partial_payment_allowed),
        [
            ("20000101", "20000101", 1, "daily", 10, "test memo", False, False),
        ],
    )
    def test_BudgetItem_Constructor__valid_inputs(
        self,
        start_date_YYYYMMDD,
        end_date_YYYYMMDD,
        priority,
        cadence,
        amount,
        memo,
        deferrable,
        partial_payment_allowed,
    ):
        BudgetItem.BudgetItem(
            start_date_YYYYMMDD,
            end_date_YYYYMMDD,
            priority,
            cadence,
            amount,
            memo,
            deferrable,
            partial_payment_allowed,
        )

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "start_date_YYYYMMDD,end_date_YYYYMMDD,priority,cadence,amount,memo,deferrable,partial_payment_allowed",
        # (start_date_YYYYMMDD,
        # end_date_YYYYMMDD,
        # priority,
        # cadence,
        # amount,
        # memo,
        # deferrable,
        # partial_payment_allowed),
        [
            (
                "X",
                "20000101",
                1,
                "daily",
                10,
                "test memo",
                False,
                False,
            ),  # malformed start date string
            (
                "20000101",
                "X",
                1,
                "daily",
                10,
                "test memo",
                False,
                False,
            ),  # malformed end date string
            (
                "20000101",
                "20000101",
                "X",
                "daily",
                10,
                "test memo",
                False,
                False,
            ),  # priority is not an int
            (
                "20000101",
                "20000101",
                1,
                "daily",
                "X",
                "test memo",
                False,
                False,
            ),  # amount is not a float
            (
                "20000101",
                "20000101",
                0,
                "daily",
                10,
                "test memo",
                False,
                False,
            ),  # priority is less than 1
            (
                "20000101",
                "20000101",
                1,
                "shmaily",
                10,
                "test memo",
                False,
                False,
            ),  # illegal cadence value
            (
                "20000101",
                "20000101",
                2,
                "daily",
                10,
                "income",
                False,
                False,
            ),  # priority not 1 for income
            (
                "20000101",
                "20000101",
                1,
                "daily",
                10,
                "test",
                True,
                False,
            ),  # deferrable must be false for p1
            (
                "20000101",
                "20000101",
                1,
                "daily",
                10,
                "test",
                False,
                True,
            ),  # partial_payment_allowed must be false for p1
        ],
    )
    def test_BudgetItem_Constructor__invalid_inputs(
        self,
        start_date_YYYYMMDD,
        end_date_YYYYMMDD,
        priority,
        cadence,
        amount,
        memo,
        deferrable,
        partial_payment_allowed,
    ):
        with pytest.raises(Exception):
            BudgetItem.BudgetItem(
                start_date_YYYYMMDD,
                end_date_YYYYMMDD,
                priority,
                cadence,
                amount,
                memo,
                deferrable,
                partial_payment_allowed,
            )

    @pytest.mark.unit
    @pytest.mark.skip(reason="this test needs to be improved")
    def test_to_str(self):
        B = BudgetItem.BudgetItem(
            "20000101", "20000101", 1, "daily", 10, "test", False, False
        )
        str(B)

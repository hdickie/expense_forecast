import pytest
from datetime import date

from expense_forecast.BudgetItem import BudgetItem
from expense_forecast.BudgetSet import BudgetSet
from expense_forecast.generate_date_sequence import generate_date_sequence

def example_budget_item():
    return BudgetItem(
        start_date=date(2000, 1, 1),
        end_date=date(2000, 1, 1),
        priority=1,
        cadence="once",
        amount=10,
        deferrable=False,
        memo="test",
    )


class TestBudgetSetMethods:

    @pytest.mark.parametrize(
        "budget_items__list",
        [
            ([example_budget_item()]),
        ],
    )
    def test_BudgetSet_Constructor(self, budget_items__list):
        BudgetSet(budget_items__list)

    @pytest.mark.parametrize(
        "start_date,end_date,priority,cadence,amount,memo,deferrable,partial_payment_allowed",
        [
            ([date(2000, 1, 1), date(2000, 1, 1), 1, "daily", 10, "test memo", False, False]),
        ],
    )
    def test_addBudgetItem(
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
        test_budget_set = BudgetSet([])
        test_budget_set.addBudgetItem(
            start_date=date(2000, 1, 1),
            end_date=date(2000, 1, 1),
            priority=1,
            cadence="once",
            amount=10,
            deferrable=False,
            memo="test 2",
            partial_payment_allowed=False,
        )

    def test_getBudgetItems(self):
        test_budget_set = BudgetSet([])

        test_budget_set.addBudgetItem(
            start_date=date(2000, 1, 1),
            end_date=date(2000, 1, 1),
            priority=1,
            cadence="once",
            amount=10,
            deferrable=False,
            memo="test",
            partial_payment_allowed=False,
        )
        test_df = test_budget_set.getBudgetItems()
        assert test_df is not None

    def test_getBudgetSchedule(self):
        test_budget_set = BudgetSet([])
        test_budget_set.addBudgetItem(
            start_date=date(2022, 1, 1),
            end_date=date(2023, 1, 1),
            priority=1,
            cadence="daily",
            amount=0,
            deferrable=False,
            partial_payment_allowed=False,
            memo="test 0",
        )
        test_budget_set.addBudgetItem(
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 1),
            priority=1,
            cadence="once",
            amount=0,
            deferrable=False,
            partial_payment_allowed=False,
            memo="test 1",
        )
        test_budget_set.addBudgetItem(
            start_date=date(2022, 1, 1),
            end_date=date(2023, 1, 1),
            priority=1,
            cadence="weekly",
            amount=0,
            deferrable=False,
            partial_payment_allowed=False,
            memo="test 2",
        )
        test_budget_set.addBudgetItem(
            start_date=date(2022, 1, 1),
            end_date=date(2023, 1, 1),
            priority=1,
            cadence="semiweekly",
            amount=0,
            deferrable=False,
            partial_payment_allowed=False,
            memo="test 3",
        )
        test_budget_set.addBudgetItem(
            start_date=date(2022, 1, 1),
            end_date=date(2023, 1, 1),
            priority=1,
            cadence="monthly",
            amount=0,
            deferrable=False,
            partial_payment_allowed=False,
            memo="test 4",
        )
        test_budget_set.addBudgetItem(
            start_date=date(2022, 1, 1),
            end_date=date(2023, 1, 1),
            priority=1,
            cadence="quarterly",
            amount=0,
            deferrable=False,
            partial_payment_allowed=False,
            memo="test 5",
        )
        test_budget_set.addBudgetItem(
            start_date=date(2022, 1, 1),
            end_date=date(2023, 1, 1),
            priority=1,
            cadence="anually",
            amount=0,
            deferrable=False,
            partial_payment_allowed=False,
            memo="test 6",
        )
        test_df = test_budget_set.getBudgetSchedule()

    def test_str(self):
        test_budget_set = BudgetSet([])
        budgetset_str = str(test_budget_set)
        assert budgetset_str is not None

        test_budget_set.addBudgetItem(
            start_date=date(2022, 1, 1),
            end_date=date(2022, 1, 1),
            priority=1,
            cadence="daily",
            amount=0,
            deferrable=False,
            memo="test",
            partial_payment_allowed=False,
            # ,throw_exceptions=False
        )
        budgetset_str = str(test_budget_set)
        assert budgetset_str is not None

    def test_duplicate_budget_items_not_allowed(self):
        test_budget_set = BudgetSet([])
        with pytest.raises(ValueError):
            test_budget_set.addBudgetItem(
                start_date=date(2022, 1, 1),
                end_date=date(2022, 1, 1),
                priority=1,
                cadence="daily",
                amount=10,
                deferrable=False,
                memo="test",
                partial_payment_allowed=False,
                # ,throw_exceptions=False
            )
            test_budget_set.addBudgetItem(
                start_date=date(2022, 1, 1),
                end_date=date(2022, 1, 1),
                priority=1,
                cadence="daily",
                amount=10,
                deferrable=False,
                memo="test",
                partial_payment_allowed=False,
                # ,throw_exceptions=False
            )

    # this test is here for coverage, bc input validation would have stopped this branch of logic first
    def test_illegal_cadence_in__generate_date_sequence__internal_method(self):
        with pytest.raises(ValueError):
            generate_date_sequence(date(2000, 1, 1), 10, "shmaily")

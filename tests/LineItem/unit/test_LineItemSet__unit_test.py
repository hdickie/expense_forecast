import pytest
from datetime import date

from expense_forecast.LineItem import LineItem
from expense_forecast.LineItemSet import LineItemSet
from expense_forecast.generate_date_sequence import generate_date_sequence
from expense_forecast.ScenarioDimension import ScenarioDimension

def example_line_item():
    return LineItem(
        start_date=date(2000, 1, 1),
        end_date=date(2000, 1, 1),
        priority=1,
        interval="once",
        amount=10,
        deferrable=False,
        memo="test",
    )


class TestLineItemSetMethods:

    def test_union_is_idempotent_and_preserves_scenario_selection(self):
        choice = LineItemSet([example_line_item()])
        food = ScenarioDimension("Food", {"Very Low": choice})

        selected = food.select("Very Low")
        result = selected + selected

        assert len(result.line_items) == 1
        assert result.scenario_selections == {"Food": "Very Low"}

    def test_union_rejects_conflicting_choices_for_same_dimension(self):
        low = LineItemSet([example_line_item()])
        average_item = LineItem(
            start_date=date(2000, 1, 2),
            end_date=date(2000, 1, 2),
            priority=1,
            interval="once",
            amount=20,
            deferrable=False,
            memo="average",
        )
        food = ScenarioDimension(
            "Food", {"Very Low": low, "Average": LineItemSet([average_item])}
        )

        with pytest.raises(ValueError, match="conflicting selections"):
            food.select("Very Low") + food.select("Average")

    def test_replace_scenario_choice_swaps_line_items_and_metadata(self):
        low = LineItemSet([example_line_item()])
        average_item = LineItem(
            start_date=date(2000, 1, 2),
            end_date=date(2000, 1, 2),
            priority=1,
            interval="once",
            amount=20,
            deferrable=False,
            memo="average",
        )
        food = ScenarioDimension(
            "Food", {"Very Low": low, "Average": LineItemSet([average_item])}
        )

        result = food.select("Very Low").replace_scenario_choice("Food", "Average")

        assert result.scenario_selections == {"Food": "Average"}
        assert [item.memo for item in result.line_items] == ["average"]

    @pytest.mark.parametrize(
        "line_items__list",
        [
            ([example_line_item()]),
        ],
    )
    def test_LineItemSet_Constructor(self, line_items__list):
        LineItemSet(line_items__list)

    @pytest.mark.parametrize(
        "start_date,end_date,priority,interval,amount,memo,deferrable,partial_payment_allowed",
        [
            ([date(2000, 1, 1), date(2000, 1, 1), 1, "daily", 10, "test memo", False, False]),
        ],
    )
    def test_addLineItem(
        self,
        start_date,
        end_date,
        priority,
        interval,
        amount,
        memo,
        deferrable,
        partial_payment_allowed,
    ):
        test_line_item_set = LineItemSet([])
        test_line_item_set.addLineItem(
            start_date=date(2000, 1, 1),
            end_date=date(2000, 1, 1),
            priority=1,
            interval="once",
            amount=10,
            deferrable=False,
            memo="test 2",
            partial_payment_allowed=False,
        )

    def test_getLineItems(self):
        test_line_item_set = LineItemSet([])

        test_line_item_set.addLineItem(
            start_date=date(2000, 1, 1),
            end_date=date(2000, 1, 1),
            priority=1,
            interval="once",
            amount=10,
            deferrable=False,
            memo="test",
            partial_payment_allowed=False,
        )
        test_df = test_line_item_set.getLineItems()
        assert test_df is not None

    def test_getLineItemSchedule(self):
        test_line_item_set = LineItemSet([])
        test_line_item_set.addLineItem(
            start_date=date(2022, 1, 1),
            end_date=date(2023, 1, 1),
            priority=1,
            interval="daily",
            amount=0,
            deferrable=False,
            partial_payment_allowed=False,
            memo="test 0",
        )
        test_line_item_set.addLineItem(
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 1),
            priority=1,
            interval="once",
            amount=0,
            deferrable=False,
            partial_payment_allowed=False,
            memo="test 1",
        )
        test_line_item_set.addLineItem(
            start_date=date(2022, 1, 1),
            end_date=date(2023, 1, 1),
            priority=1,
            interval="weekly",
            amount=0,
            deferrable=False,
            partial_payment_allowed=False,
            memo="test 2",
        )
        test_line_item_set.addLineItem(
            start_date=date(2022, 1, 1),
            end_date=date(2023, 1, 1),
            priority=1,
            interval="semiweekly",
            amount=0,
            deferrable=False,
            partial_payment_allowed=False,
            memo="test 3",
        )
        test_line_item_set.addLineItem(
            start_date=date(2022, 1, 1),
            end_date=date(2023, 1, 1),
            priority=1,
            interval="monthly",
            amount=0,
            deferrable=False,
            partial_payment_allowed=False,
            memo="test 4",
        )
        test_line_item_set.addLineItem(
            start_date=date(2022, 1, 1),
            end_date=date(2023, 1, 1),
            priority=1,
            interval="quarterly",
            amount=0,
            deferrable=False,
            partial_payment_allowed=False,
            memo="test 5",
        )
        test_line_item_set.addLineItem(
            start_date=date(2022, 1, 1),
            end_date=date(2023, 1, 1),
            priority=1,
            interval="anually",
            amount=0,
            deferrable=False,
            partial_payment_allowed=False,
            memo="test 6",
        )
        test_df = test_line_item_set.getLineItemSchedule()

    def test_str(self):
        test_line_item_set = LineItemSet([])
        line_item_set_str = str(test_line_item_set)
        assert line_item_set_str is not None

        test_line_item_set.addLineItem(
            start_date=date(2022, 1, 1),
            end_date=date(2022, 1, 1),
            priority=1,
            interval="daily",
            amount=0,
            deferrable=False,
            memo="test",
            partial_payment_allowed=False,
            # ,throw_exceptions=False
        )
        line_item_set_str = str(test_line_item_set)
        assert line_item_set_str is not None

    def test_duplicate_line_items_not_allowed(self):
        test_line_item_set = LineItemSet([])
        with pytest.raises(ValueError):
            test_line_item_set.addLineItem(
                start_date=date(2022, 1, 1),
                end_date=date(2022, 1, 1),
                priority=1,
                interval="daily",
                amount=10,
                deferrable=False,
                memo="test",
                partial_payment_allowed=False,
                # ,throw_exceptions=False
            )
            test_line_item_set.addLineItem(
                start_date=date(2022, 1, 1),
                end_date=date(2022, 1, 1),
                priority=1,
                interval="daily",
                amount=10,
                deferrable=False,
                memo="test",
                partial_payment_allowed=False,
                # ,throw_exceptions=False
            )

    # this test is here for coverage, bc input validation would have stopped this branch of logic first
    def test_illegal_interval_in__generate_date_sequence__internal_method(self):
        with pytest.raises(ValueError):
            generate_date_sequence(date(2000, 1, 1), 10, "shmaily")

from datetime import date

import pytest

from expense_forecast.LineItemSet import LineItemSet
from expense_forecast.ScenarioDimension import ScenarioDimension
from expense_forecast.ExpenseForecastInitialConditions import ExpenseForecastInitialConditions


def _line_items(*, start, end, interval="monthly", memo="income"):
    result = LineItemSet()
    result.addLineItem(
        start_date=start,
        end_date=end,
        priority=1,
        interval=interval,
        amount=100,
        memo=memo,
        income_flag=True,
    )
    return result


def test_choice_for_date_range_reschedules_recurring_items_without_mutating_choice():
    original_start = date(2020, 1, 1)
    original_end = date(2020, 12, 31)
    dimension = ScenarioDimension(
        "Income",
        {"RN Year 1": _line_items(start=original_start, end=original_end)},
    )

    result = dimension.choice_for_date_range(
        "RN Year 1", date(2026, 7, 1), date(2027, 6, 30)
    )

    assert result.line_items[0].start_date == date(2026, 7, 1)
    assert result.line_items[0].end_date == date(2027, 6, 30)
    assert dimension.choices["RN Year 1"].line_items[0].start_date == original_start
    assert dimension.choices["RN Year 1"].line_items[0].end_date == original_end
    assert result.scenario_selections == {}
    assert set(result.scenario_dimensions) == {"Income"}
    assert result.scenario_timelines["Income"][0]["choice"] == "RN Year 1"


def test_dated_choices_from_same_dimension_can_be_combined():
    template = _line_items(start=date(2020, 1, 1), end=date(2020, 12, 31))
    dimension = ScenarioDimension(
        "Income", {"RN Year 1": template, "RN Year 2": template}
    )

    result = dimension.choice_for_date_range(
        "RN Year 1", date(2026, 1, 1), date(2026, 12, 31)
    ) + dimension.choice_for_date_range(
        "RN Year 2", date(2027, 1, 1), date(2027, 12, 31)
    )

    assert len(result.line_items) == 2
    assert result.scenario_selections == {}


def test_dated_semiweekly_choices_preserve_cadence_across_shared_boundary():
    first = _line_items(
        start=date(2020, 1, 1), end=date(2020, 12, 31), interval="semiweekly",
        memo="paycheck",
    )
    second = _line_items(
        start=date(2020, 1, 1), end=date(2020, 12, 31), interval="semiweekly",
        memo="paycheck",
    )
    dimension = ScenarioDimension("Income", {"Year 1": first, "Year 2": second})
    transition = date(2026, 12, 31)

    result = dimension.choice_for_date_range(
        "Year 1", date(2026, 1, 1), transition
    ) + dimension.choice_for_date_range(
        "Year 2", transition, date(2027, 12, 31)
    )

    dates = result.getLineItemSchedule()["Date"].tolist()
    assert all((right - left).days == 14 for left, right in zip(dates, dates[1:]))
    assert result.scenario_timelines["Income"][0]["end_date"] == transition.replace(
        day=30
    )

    rebuilt = ExpenseForecastInitialConditions._line_item_set_from_dict(result.to_dict())
    assert rebuilt.scenario_timelines == result.scenario_timelines
    assert rebuilt.line_items[0].recurrence_anchor == date(2026, 1, 1)


def test_choice_for_date_range_keeps_in_range_one_time_item_at_original_date():
    event_date = date(2026, 8, 15)
    dimension = ScenarioDimension(
        "Trip",
        {"Long trip": _line_items(start=event_date, end=event_date, interval="once")},
    )

    result = dimension.choice_for_date_range(
        "Long trip", date(2026, 8, 1), date(2026, 8, 31)
    )

    assert len(result.line_items) == 1
    assert result.line_items[0].start_date == event_date
    assert result.line_items[0].end_date == event_date


def test_choice_for_date_range_drops_out_of_range_one_time_item(caplog):
    event_date = date(2026, 8, 15)
    dimension = ScenarioDimension(
        "Trip",
        {
            "Long trip": _line_items(
                start=event_date, end=event_date, interval="once", memo="event"
            )
        },
    )

    with caplog.at_level("WARNING"):
        result = dimension.choice_for_date_range(
            "Long trip", date(2026, 9, 1), date(2026, 9, 30)
        )

    assert result.line_items == []
    assert "Dropping one-time line item 'event'" in caplog.text
    assert "2026-09-01 to 2026-09-30" in caplog.text


def test_choice_for_date_range_supports_empty_choice():
    dimension = ScenarioDimension("Income", {"Unemployed": LineItemSet()})

    result = dimension.choice_for_date_range(
        "Unemployed", date(2026, 1, 1), date(2026, 12, 31)
    )

    assert result.line_items == []


def test_choice_for_date_range_rejects_unknown_choice():
    dimension = ScenarioDimension("Income", {"Unemployed": LineItemSet()})

    with pytest.raises(ValueError, match="Unknown choice"):
        dimension.choice_for_date_range(
            "Missing", date(2026, 1, 1), date(2026, 12, 31)
        )


@pytest.mark.parametrize(
    "start_date,end_date,expected_message",
    [
        ("2026-01-01", date(2026, 12, 31), "start_date"),
        (date(2026, 1, 1), "2026-12-31", "end_date"),
    ],
)
def test_choice_for_date_range_rejects_non_date_boundaries(
    start_date, end_date, expected_message
):
    dimension = ScenarioDimension("Income", {"Unemployed": LineItemSet()})

    with pytest.raises(TypeError, match=expected_message):
        dimension.choice_for_date_range("Unemployed", start_date, end_date)


def test_choice_for_date_range_rejects_reversed_range():
    dimension = ScenarioDimension("Income", {"Unemployed": LineItemSet()})

    with pytest.raises(ValueError, match="on or before"):
        dimension.choice_for_date_range(
            "Unemployed", date(2026, 12, 31), date(2026, 1, 1)
        )

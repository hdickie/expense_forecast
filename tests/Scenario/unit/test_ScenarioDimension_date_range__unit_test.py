from datetime import date

import pytest

from expense_forecast.LineItemSet import LineItemSet
from expense_forecast.ScenarioDimension import ScenarioDimension
from expense_forecast.ExpenseForecastInitialConditions import ExpenseForecastInitialConditions


def _line_items(
    *, start, end, interval="monthly", memo="income", recurrence_key=None
):
    result = LineItemSet()
    result.addLineItem(
        start_date=start,
        end_date=end,
        priority=1,
        interval=interval,
        amount=100,
        memo=memo,
        income_flag=True,
        recurrence_key=recurrence_key,
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


def test_stateful_timeline_materializes_new_choice_on_change_date():
    original_start = date(2020, 1, 1)
    original_end = date(2020, 12, 31)
    dimension = ScenarioDimension(
        "Income",
        {
            "Year 1": _line_items(
                start=original_start,
                end=original_end,
                interval="semiweekly",
                memo="Year 1 paycheck",
                recurrence_key="paycheck",
            ),
            "Year 2": _line_items(
                start=original_start,
                end=original_end,
                interval="semiweekly",
                memo="Year 2 paycheck",
                recurrence_key="paycheck",
            ),
        },
    )
    change_date = date(2026, 12, 31)

    returned = dimension.set_default(date(2026, 1, 1), "Year 1")
    assert returned is dimension
    assert dimension.change_choice_on_date(change_date, "Year 2") is dimension
    result = dimension.to_line_item_set(date(2027, 12, 31))

    assert dimension.scenario_timelines == [
        {
            "choice": "Year 1",
            "effective_date": date(2026, 1, 1),
            "end_date": date(2026, 12, 30),
        },
        {
            "choice": "Year 2",
            "effective_date": change_date,
            "end_date": None,
        },
    ]
    assert result.scenario_timelines["Income"][1]["effective_date"] == change_date
    schedule = result.getLineItemSchedule()
    assert schedule.loc[
        schedule["Date"] >= change_date, "Memo"
    ].iloc[0] == "Year 2 paycheck"
    dates = schedule["Date"].tolist()
    assert all(
        (right - left).days == 14
        for left, right in zip(dates, dates[1:])
    )

    # Authoring and materialization never alter the stored choice templates.
    for choice in dimension.choices.values():
        assert choice.line_items[0].start_date == original_start
        assert choice.line_items[0].end_date == original_end


def test_stateful_timeline_supports_multiple_changes_and_empty_choices():
    employed = _line_items(
        start=date(2020, 1, 1), end=date(2020, 12, 31)
    )
    dimension = ScenarioDimension(
        "Work", {"Employed": employed, "Unemployed": LineItemSet()}
    )
    dimension.set_default(date(2026, 1, 1), "Employed")
    dimension.change_choice_on_date(date(2026, 2, 1), "Unemployed")
    dimension.change_choice_on_date(date(2026, 3, 1), "Employed")

    result = dimension.to_line_item_set(date(2026, 3, 31))

    assert [entry["choice"] for entry in result.scenario_timelines["Work"]] == [
        "Employed", "Unemployed", "Employed"
    ]
    assert len(result.line_items) == 2


def test_stateful_timeline_keeps_only_in_range_one_time_items():
    event_date = date(2026, 2, 15)
    dimension = ScenarioDimension(
        "Trip",
        {
            "Home": LineItemSet(),
            "Travel": _line_items(
                start=event_date,
                end=event_date,
                interval="once",
                memo="trip",
            ),
        },
    )
    dimension.set_default(date(2026, 1, 1), "Home")
    dimension.change_choice_on_date(date(2026, 2, 1), "Travel")

    assert len(dimension.to_line_item_set(date(2026, 2, 28)).line_items) == 1
    assert len(dimension.to_line_item_set(date(2026, 2, 10)).line_items) == 0


def test_stateful_timeline_round_trips_materialized_metadata():
    dimension = ScenarioDimension(
        "Income",
        {
            "Year 1": _line_items(
                start=date(2020, 1, 1), end=date(2020, 12, 31)
            ),
            "Year 2": _line_items(
                start=date(2020, 1, 1), end=date(2020, 12, 31)
            ),
        },
    )
    dimension.set_default(date(2026, 1, 1), "Year 1")
    dimension.change_choice_on_date(date(2027, 1, 1), "Year 2")
    result = dimension.to_line_item_set(date(2027, 12, 31))

    rebuilt = ExpenseForecastInitialConditions._line_item_set_from_dict(
        result.to_dict()
    )
    assert rebuilt.scenario_timelines == result.scenario_timelines


def test_stateful_timeline_validates_authoring_order_and_ranges():
    dimension = ScenarioDimension(
        "Income",
        {"Year 1": LineItemSet(), "Year 2": LineItemSet()},
    )

    with pytest.raises(ValueError, match="set_default"):
        dimension.change_choice_on_date(date(2027, 1, 1), "Year 2")
    with pytest.raises(ValueError, match="set_default"):
        dimension.to_line_item_set(date(2027, 1, 1))
    with pytest.raises(ValueError, match="Unknown choice"):
        dimension.set_default(date(2026, 1, 1), "Missing")
    with pytest.raises(TypeError, match="effective_date"):
        dimension.set_default("2026-01-01", "Year 1")

    dimension.set_default(date(2026, 1, 1), "Year 1")
    with pytest.raises(ValueError, match="already has a default"):
        dimension.set_default(date(2026, 2, 1), "Year 2")
    with pytest.raises(ValueError, match="already active"):
        dimension.change_choice_on_date(date(2026, 2, 1), "Year 1")
    with pytest.raises(ValueError, match="strictly increasing"):
        dimension.change_choice_on_date(date(2026, 1, 1), "Year 2")
    with pytest.raises(ValueError, match="on or after"):
        dimension.to_line_item_set(date(2025, 12, 31))
    with pytest.raises(TypeError, match="end_date"):
        dimension.to_line_item_set("2026-12-31")

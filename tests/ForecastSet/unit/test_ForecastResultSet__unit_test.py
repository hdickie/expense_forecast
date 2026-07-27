from datetime import date

import pytest

from expense_forecast.AccountSet import AccountSet
from expense_forecast.ExpenseForecastInitialConditions import (
    ExpenseForecastInitialConditions,
)
from expense_forecast.ForecastHandler import ForecastHandler
from expense_forecast.ForecastResultSet import ForecastResultSet
from expense_forecast.LineItemSet import LineItemSet
from expense_forecast.MemoRuleSet import MemoRuleSet


def _result(end=date(2026, 1, 3), name="Forecast", balance=100):
    accounts = AccountSet()
    accounts.createCheckingAccount(
        "Checking", balance, 0, float("inf"), True
    )
    conditions = ExpenseForecastInitialConditions(
        date(2026, 1, 1),
        end,
        accounts,
        LineItemSet(),
        MemoRuleSet(),
        forecast_name=name,
    )
    return ForecastHandler.runForecast(conditions)


def test_forecast_result_set_preserves_order_and_has_stable_id():
    first = _result(name="First")
    second = _result(name="Second", balance=101)

    result_set = ForecastResultSet(first, second)
    rebuilt = ForecastResultSet([first, second])

    assert list(result_set) == [first, second]
    assert result_set.unique_id == rebuilt.unique_id
    assert result_set.start_date == date(2026, 1, 1)
    assert result_set.end_date == date(2026, 1, 3)


def test_forecast_result_set_validates_members_and_dates():
    with pytest.raises(ValueError, match="at least one"):
        ForecastResultSet()
    with pytest.raises(TypeError, match="ExpenseForecastResult"):
        ForecastResultSet(object())

    first = _result(name="First")
    with pytest.raises(ValueError, match="unique forecast IDs"):
        ForecastResultSet(first, first)
    with pytest.raises(ValueError, match="matching forecast row dates"):
        ForecastResultSet(
            first, _result(date(2026, 1, 4), "Longer", balance=101)
        )

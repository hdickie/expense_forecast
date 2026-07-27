
from datetime import date

import pandas as pd
import pytest

from expense_forecast.ExpenseForecastInitialConditions import (
    ExpenseForecastInitialConditions,
)
from expense_forecast.ExpenseForecastResult import ExpenseForecastResult
from expense_forecast.ForecastHandler import ForecastHandler
from expense_forecast.ForecastResultSet import ForecastResultSet


class TestForecastSetIntegration:

    @staticmethod
    def _result(unique_id):
        result = object.__new__(ExpenseForecastResult)
        result.unique_id = unique_id
        result.forecast_df = pd.DataFrame(
            {"Date": [date(2026, 1, 1), date(2026, 2, 1)]}
        )
        return result

    def test_approximate_set_runner_preserves_order_and_forwards_options(
        self, monkeypatch
    ):
        first = object.__new__(ExpenseForecastInitialConditions)
        second = object.__new__(ExpenseForecastInitialConditions)
        expected_results = {
            id(first): self._result("first"),
            id(second): self._result("second"),
        }
        calls = []

        def fake_run(
            initial_conditions,
            milestone_set=None,
            include_debug_columns=False,
            engine="legacy",
            graph_trace=False,
        ):
            calls.append(
                (
                    initial_conditions,
                    milestone_set,
                    include_debug_columns,
                    engine,
                    graph_trace,
                )
            )
            return expected_results[id(initial_conditions)]

        monkeypatch.setattr(
            ForecastHandler, "runForecastApproximate", fake_run
        )

        result_set = ForecastHandler.runForecastSetApproximate(
            [first, second],
            milestone_set="milestones",
            include_debug_columns=True,
            engine="shadow v2",
            graph_trace=True,
        )

        assert isinstance(result_set, ForecastResultSet)
        assert list(result_set) == [
            expected_results[id(first)],
            expected_results[id(second)],
        ]
        assert calls == [
            (first, "milestones", True, "shadow v2", True),
            (second, "milestones", True, "shadow v2", True),
        ]

    @pytest.mark.parametrize("value", [[], [object()]])
    def test_approximate_set_runner_validates_inputs(self, value):
        expected = ValueError if not value else TypeError
        with pytest.raises(expected):
            ForecastHandler.runForecastSetApproximate(value)

"""An ordered collection of completed forecasts for comparative reporting."""

from __future__ import annotations

import hashlib

import pandas as pd

from expense_forecast.ExpenseForecastResult import ExpenseForecastResult


class ForecastResultSet:
    """Store comparable forecast results in stable declaration order."""

    def __init__(self, *results):
        if len(results) == 1 and isinstance(results[0], (list, tuple)):
            results = tuple(results[0])
        if not results:
            raise ValueError("ForecastResultSet requires at least one result")
        if any(not isinstance(result, ExpenseForecastResult) for result in results):
            raise TypeError(
                "ForecastResultSet accepts only ExpenseForecastResult objects"
            )

        identifiers = [result.unique_id for result in results]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("ForecastResultSet requires unique forecast IDs")

        expected_dates = self._normalized_dates(results[0])
        for result in results[1:]:
            if self._normalized_dates(result) != expected_dates:
                raise ValueError(
                    "ForecastResultSet requires matching forecast row dates"
                )

        self.results = list(results)
        self.start_date = expected_dates[0]
        self.end_date = expected_dates[-1]
        digest = hashlib.sha256(
            "\x1f".join(identifiers).encode("utf-8")
        ).hexdigest()[:12]
        self.unique_id = digest

    @staticmethod
    def _normalized_dates(result):
        if "Date" not in result.forecast_df.columns:
            raise ValueError(
                f"Forecast {result.unique_id!r} has no Date column"
            )
        dates = [
            pd.Timestamp(value).date()
            for value in result.forecast_df["Date"]
        ]
        if not dates:
            raise ValueError(
                f"Forecast {result.unique_id!r} has no forecast rows"
            )
        return dates

    def __iter__(self):
        return iter(self.results)

    def __len__(self):
        return len(self.results)

    def __getitem__(self, index):
        return self.results[index]

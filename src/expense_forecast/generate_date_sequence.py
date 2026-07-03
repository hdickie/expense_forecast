import pandas as pd
import datetime


def generate_date_sequence(start_date, num_days, cadence):
    """A wrapper for pd.date_range intended to make code easier to read."""

    end_date = start_date + datetime.timedelta(days=num_days)

    if num_days == 0:
        return [start_date]

    if cadence.lower() == "once":
        return [start_date]

    elif cadence.lower() == "daily":
        return_series = pd.date_range(start_date, end_date, freq="D")

    elif cadence.lower() == "weekly":
        day_delta = start_date.weekday()
        start_date = start_date - datetime.timedelta(days=day_delta)
        end_date = end_date - datetime.timedelta(days=day_delta)
        relevant_weekly_schedule = pd.date_range(start_date, end_date, freq="W-MON")
        return_series = relevant_weekly_schedule + datetime.timedelta(days=day_delta)

    elif cadence.lower() == "semiweekly":
        day_delta = start_date.weekday()
        start_date = start_date - datetime.timedelta(days=day_delta)
        end_date = end_date - datetime.timedelta(days=day_delta)
        relevant_weekly_schedule = pd.date_range(start_date, end_date, freq="W-MON")
        result_sequence = relevant_weekly_schedule + datetime.timedelta(days=day_delta)
        return_series = result_sequence[0 : len(result_sequence) : 2]

    elif cadence.lower() == "monthly":
        day_delta = start_date.day - 1
        start_date = start_date - datetime.timedelta(days=day_delta)
        first_of_each_relevant_month = pd.date_range(start_date, end_date, freq="MS")
        return_series = first_of_each_relevant_month + datetime.timedelta(days=day_delta)

    elif cadence.lower() == "quarterly":
        day_delta = start_date.day
        start_date = start_date - datetime.timedelta(days=day_delta)
        first_of_each_relevant_quarter = pd.date_range(start_date, end_date, freq="Q")
        return_series = first_of_each_relevant_quarter + datetime.timedelta(days=day_delta)

    elif cadence.lower() == "yearly":
        day_delta = start_date.day - 1
        start_date = start_date - datetime.timedelta(days=day_delta)
        first_of_each_relevant_year = pd.date_range(start_date, end_date, freq="YS")
        return_series = first_of_each_relevant_year + datetime.timedelta(days=day_delta)

    else:
        raise ValueError(
            "Undefined cadence in generate_date_sequence: " + str(cadence)
        )

    return pd.Series(return_series.date)

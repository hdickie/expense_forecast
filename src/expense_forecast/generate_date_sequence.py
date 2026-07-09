"""
Summary
-------

Description
-----------

Contract
--------

@interface-report: show
"""


import pandas as pd
import datetime


#TODO manual review of generate_date_sequence.generate_date_sequence docstring
def generate_date_sequence(start_date, num_days, cadence):

    """
    TODO one-line description of generate_date_sequence.generate_date_sequence.

    TODO multi-line description of generate_date_sequence.generate_date_sequence.
    TODO explain how generate_date_sequence.generate_date_sequence participates in this module.
    TODO document important state, validation, or serialization behavior.

    Parameters
    ----------
    start_date : date
        TODO one-line description of generate_date_sequence.generate_date_sequence.start_date.

    num_days : int
        TODO one-line description of generate_date_sequence.generate_date_sequence.num_days.

    cadence : str
        TODO one-line description of generate_date_sequence.generate_date_sequence.cadence.

    Returns
    -------
    pd.Series | list[date]
        TODO one-line description of return value of generate_date_sequence.generate_date_sequence.

    Contract
    --------
    - #TODO contract lines for generate_date_sequence.generate_date_sequence.
    - #TODO document exceptions, mutations, and precision assumptions for generate_date_sequence.generate_date_sequence.

    @interface-report: show
    """
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
        first_of_each_relevant_quarter = pd.date_range(start_date, end_date, freq="QE")
        return_series = first_of_each_relevant_quarter + datetime.timedelta(days=day_delta)

    elif cadence.lower() == "anually":
        day_delta = start_date.day - 1
        start_date = start_date - datetime.timedelta(days=day_delta)
        first_of_each_relevant_year = pd.date_range(start_date, end_date, freq="YS")
        return_series = first_of_each_relevant_year + datetime.timedelta(days=day_delta)

    else:
        raise ValueError(
            "Undefined cadence in generate_date_sequence: " + str(cadence)
        )

    return pd.Series(return_series.date)

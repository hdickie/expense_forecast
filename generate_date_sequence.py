import pandas as pd
import datetime

def generate_date_sequence(start_date_YYYYMMDD, num_days, cadence):
    """ A wrapper for pd.date_range intended to make code easier to read.

    """

    start_date = datetime.datetime.strptime(start_date_YYYYMMDD, '%Y%m%d')
    end_date = start_date + datetime.timedelta(days=num_days)

    if cadence.lower() == "once":
        return pd.Series(start_date_YYYYMMDD)
    elif cadence.lower() == "daily":
        return_series = pd.date_range(start_date, end_date, freq='D')
    elif cadence.lower() == "weekly":
        return_series = pd.date_range(start_date, end_date, freq='W')
    elif cadence.lower() == "semiweekly":
        #return_series = pd.date_range(start_date, end_date, freq='2W')
        day_delta = int(start_date.strftime('%d')) - 2 #not sure why this is 2 when others needed 1 but testing says so
        start_date = start_date - datetime.timedelta(days=day_delta)
        relevant_semiweekly_schedule = pd.date_range(start_date, end_date, freq='2W')
        return_series = relevant_semiweekly_schedule + datetime.timedelta(days=day_delta)
    elif cadence.lower() == "monthly":
        day_delta = int(start_date.strftime('%d')) - 1
        start_date = start_date - datetime.timedelta(days=day_delta)
        first_of_each_relevant_month = pd.date_range(start_date, end_date, freq='MS')
        return_series = first_of_each_relevant_month + datetime.timedelta(days=day_delta)
    elif cadence.lower() == "quarterly":
        day_delta = int(start_date.strftime('%d'))
        start_date = start_date - datetime.timedelta(days=day_delta)
        first_of_each_relevant_quarter = pd.date_range(start_date, end_date,freq='Q')
        return_series = first_of_each_relevant_quarter + datetime.timedelta(days=day_delta)
    elif cadence.lower() == "yearly":
        day_delta = int(start_date.strftime('%d')) - 1
        start_date = start_date - datetime.timedelta(days=day_delta)

        # Y is year end, YS is year start. there is no just 'year' option
        first_of_each_relevant_year = pd.date_range(start_date, end_date, freq='YS')

        return_series = first_of_each_relevant_year + datetime.timedelta(days=day_delta)
    else:
        raise ValueError("Undefined cadence in generate_date_sequence: "+str(cadence))

    return_series = [ d.strftime('%Y%m%d') for d in return_series ]
    return return_series
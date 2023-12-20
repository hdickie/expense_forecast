import pandas as pd
import datetime

def generate_date_sequence(start_date_YYYYMMDD, num_days, cadence):
    """ A wrapper for pd.date_range intended to make code easier to read.

    #todo write project_utilities.generate_date_sequence() doctests
    """
    #log_in_color('green', 'debug', 'ENTER generate_date_sequence(start_date_YYYYMMDD=' + str(start_date_YYYYMMDD) + ',num_days=' + str(num_days) + ',=' + str(cadence) + '):', 0)
    # print('start_date_YYYYMMDD:'+str(start_date_YYYYMMDD))
    # print('num_days...........:'+str(num_days))
    # print('cadence............:'+str(cadence))

    start_date = datetime.datetime.strptime(start_date_YYYYMMDD, '%Y%m%d')
    end_date = start_date + datetime.timedelta(days=num_days)

    if cadence.lower() == "once":
        return pd.Series(start_date_YYYYMMDD)
    elif cadence.lower() == "daily":
        return_series = pd.date_range(start_date, end_date, freq='D')
    elif cadence.lower() == "weekly":
        return_series = pd.date_range(start_date, end_date, freq='W')
    elif cadence.lower() == "semiweekly":
        return_series = pd.date_range(start_date, end_date, freq='2W')
    elif cadence.lower() == "monthly":

        day_delta = int(start_date.strftime('%d')) - 1
        first_of_each_relevant_month = pd.date_range(start_date - datetime.timedelta(days=day_delta), end_date, freq='MS')

        return_series = first_of_each_relevant_month + datetime.timedelta(days=day_delta)
    elif cadence.lower() == "quarterly":
        # todo check if this needs an adjustment like the monthly case did
        return_series = pd.date_range(start_date, end_date, freq='Q')
    elif cadence.lower() == "yearly":
        # todo check if this needs an adjustment like the monthly case did
        return_series = pd.date_range(start_date, end_date, freq='Y')
    else:
        raise ValueError("Undefined cadence in generate_date_sequence: "+str(cadence))

    return_series = [ d.strftime('%Y%m%d') for d in return_series ]

    # log_in_color('green', 'debug', str(return_series), 0)
    # log_in_color('green', 'debug', 'EXIT generate_date_sequence()', 0)
    return return_series

import datetime

class Account:

    def __init__(self):
        self.name = ''
        self.balance = -1
        self.min_balance = -1
        self.max_balance = -1
        self.apr = 0
        self.interest_cadence = 'None' #None, Daily, Monthly
        self.interest_type = 'None'
        self.billing_start_date = datetime.datetime.strptime('2000-01-01','%Y-%m-%d')

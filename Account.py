
import datetime

class Account:

    def __init__(self,
                 name = '',
                 balance = -1,
                 min_balance = -1,
                 max_balance = -1,
                 apr = 0,
                 interest_cadence = 'None',
                 interest_type = 'None',
                 billing_start_date = '2000-01-01'
                 ):

        self.name = str(name)
        self.balance = balance
        self.min_balance = min_balance
        self.max_balance = max_balance
        self.apr = apr
        self.interest_cadence = interest_cadence  #None, Daily, Monthly
        self.interest_type = interest_type #None, Simple, Compound
        self.billing_start_date = billing_start_date

        #TODO there should be an account type field here.... for tracking interst for simple interest bearing accounts


        if self.billing_start_date != 'None':
            self.billing_start_date = datetime.datetime.strptime(billing_start_date,'%Y-%m-%d')

        #the exceptions these already throw are correct so no need to catch and re-raise
        assert isinstance(float(balance),float)
        assert isinstance(float(min_balance),float)
        assert isinstance(float(max_balance),float)
        assert isinstance(float(apr),float)

        if interest_cadence.lower() not in ['none','daily','monthly']:
            raise ValueError

        if interest_type.lower() not in ['none','simple','compound']:
            raise ValueError

        #used for input validation here

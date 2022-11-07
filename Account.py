"""
Single-line description for Account.py

Multiple line description

"""
import datetime

class Account:

    def __init__(self,
                 name = '',
                 balance = -1,
                 previous_statement_balance = -1,
                 min_balance = -1,
                 max_balance = -1,
                 apr = 0,
                 interest_cadence = 'None',
                 interest_type = 'None',
                 billing_start_date = '2000-01-01',
                 account_type = 'checking',
                 principal_balance = -1,
                 accrued_interest = -1,
                 minimum_payment = 0
                 ):
        """
        Creates an Account. Input validation is performed.

        Multiple-line description of Account constructor.

        >>> Account()
        |Name: |
        |Balance: -1|
        |Min Balance: -1|
        |Max Balance: -1|
        |APR: 0|
        |Interest Cadence: None|
        |Interest Type: None|
        |Billing Start Date: 2000-01-01 00:00:00|
        |Account Type: checking|
        |Principal Balance: -1|
        |Accrued Interest: -1|
        |Minimum Payment: 0|
        <BLANKLINE>

        :param name:
        :param balance:
        :param previous_statement_balance:
        :param min_balance:
        :param max_balance:
        :param apr:
        :param interest_cadence:
        :param interest_type:
        :param billing_start_date:
        :param account_type:
        :param principal_balance:
        :param accrued_interest:
        :param minimum_payment:
        """

        self.name = str(name)
        self.balance = balance
        self.previous_statement_balance = previous_statement_balance
        self.min_balance = min_balance
        self.max_balance = max_balance
        self.apr = apr
        self.interest_cadence = interest_cadence  #None, Daily, Monthly
        self.interest_type = interest_type #None, Simple, Compound
        self.billing_start_date = billing_start_date
        self.account_type = account_type
        self.principal_balance = principal_balance
        self.accrued_interest = accrued_interest
        self.minimum_payment = minimum_payment

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

        #todo assert principal + interest = balance

    def __repr__(self):
        return_string = ""
        return_string += "|Name: "+str(self.name)+"|\n"
        return_string += "|Balance: "+str(self.balance)+"|\n"
        return_string += "|Min Balance: "+str(self.min_balance)+"|\n"
        return_string += "|Max Balance: "+str(self.max_balance)+"|\n"
        return_string += "|APR: "+str(self.apr)+"|\n"
        return_string += "|Interest Cadence: "+str(self.interest_cadence)+"|\n"
        return_string += "|Interest Type: "+str(self.interest_type)+"|\n"
        return_string += "|Billing Start Date: "+str(self.billing_start_date)+"|\n"
        return_string += "|Account Type: "+str(self.account_type)+"|\n"
        return_string += "|Principal Balance: "+str(self.principal_balance)+"|\n"
        return_string += "|Accrued Interest: "+str(self.accrued_interest)+"|\n"
        return_string += "|Minimum Payment: " + str(self.minimum_payment) + "|\n"
        return return_string

    def __str__(self):
        #TODO return specific sets of fields based on account type
        return_string = ""
        return_string += "Name: " + str(self.name) + "\n"
        return_string += "Balance: " + str(self.balance) + "\n"
        return_string += "Min Balance: " + str(self.min_balance) + "\n"
        return_string += "Max Balance: " + str(self.max_balance) + "\n"
        return_string += "APR: " + str(self.apr) + "\n"
        return_string += "Interest Cadence: " + str(self.interest_cadence) + "\n"
        return_string += "Interest Type: " + str(self.interest_type) + "\n"
        return_string += "Billing Start Date: " + str(self.billing_start_date) + "\n"
        return_string += "Account Type: " + str(self.account_type) + "\n"
        return_string += "Principal Balance: " + str(self.principal_balance) + "\n"
        return_string += "Accrued Interest: " + str(self.accrued_interest) + "\n"
        return_string += "Minimum Payment: " + str(self.minimum_payment) + "\n"
        return return_string

if __name__ == "__main__":
    import doctest
    doctest.testmod()


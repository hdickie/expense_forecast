"""
Single-line description for Account.py

Multiple line description

"""
import datetime, pandas as pd

class Account:

    def __init__(self,
                 name, #no default because it is a required field
                 balance,
                 min_balance,
                 max_balance,
                 account_type, #checking, savings, credit, principal balance, interest
                 billing_start_date_YYYYMMDD=None,
                 interest_type=None,
                 apr=None,
                 interest_cadence=None,
                 minimum_payment=None,
                 previous_statement_balance=None,
                 principal_balance = None,
                 accrued_interest = None

                 ):
        """
        Creates an Account. Input validation is performed.

        The Account constructor does not check types, but numerical parameters will raise a ValueError if they cannot be
        cast to float. Legal combinations of parameters for each account type are:

        account_type = "checking"
        billing_start_date_YYYYMMDD = None
        interest_type = None
        apr = None
        interest_cadence = None
        previous_statement_balance = None
        minimum_payment = None
        principal_balance = None
        accrued_interest = None

        account_type = "savings"
        billing_start_date_YYYYMMDD = date of str matching format %Y%m%d
        interest_type = "compound"
        apr = float (not None)
        interest_cadence = "daily", "monthly", or "yearly"
        previous_statement_balance = None
        minimum_payment = None
        principal_balance = None
        accrued_interest = None

        account_type = "credit"
        billing_start_date_YYYYMMDD = date of str matching format %Y%m%d
        interest_type = "compound"
        apr = float (not None)
        interest_cadence = "daily", "monthly", or "yearly"
        previous_statement_balance = float (not None). Must obey account min and max.
        minimum_payment = Non-negative float (not None).
        principal_balance = None
        accrued_interest = None

        account_type = "loan"
        billing_start_date_YYYYMMDD = date of str matching format %Y%m%d
        interest_type = "simple"
        apr = float (not None)
        interest_cadence = "daily", "monthly", or "yearly"
        previous_statement_balance = None
        minimum_payment = Non-negative float (not None).
        principal_balance = Non-negative float (not None). Principal_Balance + Accrued_Interets must = Balance.
        accrued_interest = Non-negative float (not None). Principal_Balance + Accrued_Interets must = Balance.


        >>> Account()
        Traceback (most recent call last):
        ...
        TypeError: Account.__init__() missing 5 required positional arguments: 'name', 'balance', 'min_balance', 'max_balance', and 'account_type'

        >>> Account(name='balance boundary violation',balance = -1, min_balance=0, max_balance=0,account_type="checking")
        Traceback (most recent call last):
        ...
        xyz

        >>> Account(name='account type error',balance=0,min_balance=0,max_balance=0,account_type='shmecking')
        account_type was not one of: checking, credit, savings, loan
        Traceback (most recent call last):
        ...
        ValueError
        #idk why this test isn't working

        >>> Account(name='checking w non-None params that should be None',balance = 0, min_balance = 0, max_balance = 0,account_type='checking',
        ... billing_start_date_YYYYMMDD = '20000101',
        ... interest_type = 'simple',
        ... apr = 0,
        ... interest_cadence = 'weekly',
        ... previous_statement_balance = 0,
        ... minimum_payment = 0,
        ... principal_balance = 0,
        ... accrued_interest = 0)
        Traceback (most recent call last):
        ...
        ValueError

        :param str name: A name for the account. Used to label output columns.
        :param float balance: A dollar value for the balance of the account.
        :param float min_balance: The minimum legal value for account balance.
        :param float max_balance: The maximum legal value for account balance. May be float('Inf').
        :param str account_type:
        :param str billing_start_date_YYYYMMDD: A string that indicates the billing start date.
        :param str interest_type: One of: 'simple', 'compound'. Not case sensitive.
        :param float apr: A float value that indicates the percent increase per YEAR.
        :param str interest_cadence: One of: 'daily', 'monthly', 'yearly'
        :param float previous_statement_balance: Previous statement balance. Only meaningful for credit cards.
        :param float minimum_payment: Minimum payment. Only meaningful for loans and credit cards.
        :param float principal_balance: Principal Balance. Only meaningful for accounts w simple interest.
        :param float accrued_interest: Accrued Interest. Only meaningful for accounts w simple interest.
        :return Account object
        :rtype Account
        :raises ValueError: if the combination of input paramters is not valid.
        :raises TypeError: if numerical values can't be cast to float. If billing_start_date is not string format %Y%m%d.
        """

        exception_type_error_ind = False
        exception_type_error_message_string = ""

        exception_value_error_ind = False
        exception_value_error_message_string = ""

        if account_type.lower() not in ['checking','credit','savings','loan']:
            exception_value_error_ind += 'account_type was not one of: checking, credit, savings, loan\n'
            exception_value_error_ind = True

        #todo conditional validation based on account type
        #self.account_type = account_type

        try:
            self.name = str(name)
        except:
            exception_value_error_ind += 'failed cast self.name to str\n'
            exception_type_error_ind = True

        try:
            self.balance = float(balance)
        except:
            exception_value_error_ind += 'failed cast self.balance to float\n'
            exception_type_error_ind = True

        if account_type.lower() in ['credit']:
            try:
                self.previous_statement_balance = float(previous_statement_balance)
            except:
                exception_value_error_ind += 'failed cast self.previous_statement_balance to float\n'
                exception_type_error_ind = True
        else:
            if previous_statement_balance is not None:
                exception_value_error_message_string += "For types other than credit, previous_statement_balance should be None.\n"
                exception_value_error_ind = True


        try:
            self.min_balance = float(min_balance)
        except:
            exception_value_error_ind += 'failed cast self.min_balance to float\n'
            exception_type_error_ind = True

        try:
            self.max_balance = float(max_balance)
        except:
            exception_value_error_ind += 'failed cast self.max_balance to float\n'
            exception_type_error_ind = True

        if account_type.lower() in ['credit','loan','savings']:
            try:
                self.apr = float(apr)
            except:
                exception_value_error_ind += 'failed cast self.apr to float\n'
                exception_type_error_ind = True
        else:
            if apr is not None:
                exception_value_error_message_string += "For types other than credit, loan, or savings, apr should be None.\n"
                exception_value_error_ind = True

        if account_type.lower() in ['credit', 'loan', 'savings']:
            try:
                self.interest_cadence = str(interest_cadence) #None, Daily, Monthly
            except:
                exception_value_error_ind += 'failed cast self.interest_cadence to str\n'
                exception_type_error_ind = True
        else:
            if interest_cadence is not None:
                exception_value_error_message_string += "For types other than credit, loan, or savings, interest_cadence should be None.\n"
                exception_value_error_ind = True

                #todo left off here. continue below adding conditional validation based on account type

        try:
            self.interest_type = str(interest_type) #None, Simple, Compound
        except:
            exception_value_error_ind += 'failed cast self.interest_type to str\n'
            exception_type_error_ind = True

        try:
            self.billing_start_date = datetime.datetime.strptime(billing_start_date_YYYYMMDD,'%Y%m%d')
        except:
            exception_value_error_ind += 'failed cast self.billing_start_date_YYYYMMDD to datetime\n'
            exception_type_error_ind = True

        try:
            self.principal_balance = float(principal_balance)
        except:
            exception_value_error_ind += 'failed cast self.principal_balance to float\n'
            exception_type_error_ind = True

        try:
            self.accrued_interest = float(accrued_interest)
        except:
            exception_value_error_ind += 'failed cast self.accrued_interest to float\n'
            exception_type_error_ind = True

        try:
            self.minimum_payment = float(minimum_payment)
        except:
            exception_value_error_ind += 'failed cast self.minimum_payment to float\n'
            exception_type_error_ind = True



        if interest_cadence.lower() not in ['none','daily','monthly']:
            raise ValueError

        if interest_type.lower() not in ['none','simple','compound']:
            raise ValueError

        #todo assert principal + interest = balance

        if exception_type_error_ind:
            print(exception_type_error_message_string)
            raise TypeError

        if exception_value_error_ind:
            print(exception_value_error_message_string)
            raise ValueError

    def __repr__(self):
        return str(self)

    def __str__(self):

        single_account_df = pd.DataFrame({
            'Name':[self.name],
            'Balance': [self.balance],
            'Min Balance': [self.min_balance],
            'Max Balance': [self.max_balance],
            'APR': [self.apr],
            'Interest Cadence': [self.interest_cadence],
            'Interest Type': [self.interest_type],
            'Billing Start Date': [self.billing_start_date],
            'Account Type': [self.account_type],
            'Principal Balance': [self.principal_balance],
            'Accrued Interest': [self.accrued_interest],
            'Minimum Payment': [self.minimum_payment]
        })

        return single_account_df.to_string()



if __name__ == "__main__":
    import doctest
    doctest.testmod()


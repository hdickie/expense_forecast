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
                 accrued_interest = None,
                 print_debug_messages = True, #this is here because doctest can test expected output OR exceptions, but not both
                 throw_exceptions = True
                 ):
        """
        Creates an Account. Input validation is performed.

        The Account constructor does not check types, but numerical parameters will raise a ValueError if they cannot be
        cast to float. Legal combinations of parameters are described below.

        Note that this method is can't create previous statement balance or interest accounts and it is not intended to.
        Those accounts are created when a credit or loan account are added to an AccountSet with the addAccount method or
        in the AccountSet constructor.

        Just don't use Account() to directly create accounts. Create an AccountSet and add them wiht addAccount.

        :param str name: A name for the account. Used to label output columns.
        :param float balance: A dollar value for the balance of the account.
        :param float min_balance: The minimum legal value for account balance.
        :param float max_balance: The maximum legal value for account balance. May be float('Inf').
        :param str account_type:
        :param str billing_start_date_YYYYMMDD: A string that indicates the billing start date with format %Y%m%d.
        :param str interest_type: One of: 'simple', 'compound'. Not case sensitive.
        :param float apr: A float value that indicates the percent increase per YEAR.
        :param str interest_cadence: One of: 'daily', 'monthly', 'yearly'
        :param float previous_statement_balance: Previous statement balance. Only meaningful for credit cards.
        :param float minimum_payment: Minimum payment. Only meaningful for loans and credit cards.
        :param float principal_balance: Principal Balance. Only meaningful for accounts w simple interest.
        :param float accrued_interest: Accrued Interest. Only meaningful for accounts w simple interest.
        :param bool print_debug_messages: if true, prints debug messages
        :param bool throw_exceptions: if true, throws any exceptions that were raised
        :return Account object
        :rtype Account
        :raises ValueError: if the combination of input paramters is not valid.
        :raises TypeError: if numerical values can't be cast to float. If billing_start_date is not string format %Y%m%d.

         Legal combinations of parameters for each account type are:

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

        #
        # account_type = "credit"
        # billing_start_date_YYYYMMDD = date of str matching format %Y%m%d
        # interest_type = "compound"
        # apr = float (not None)
        # interest_cadence = "daily", "monthly", or "yearly"
        # previous_statement_balance = float (not None). Must obey account min and max.
        # minimum_payment = Non-negative float (not None).
        # principal_balance = None
        # accrued_interest = None
        #
        # account_type = "loan"
        # billing_start_date_YYYYMMDD = date of str matching format %Y%m%d
        # interest_type = "simple"
        # apr = float (not None)
        # interest_cadence = "daily", "monthly", or "yearly"
        # previous_statement_balance = None
        # minimum_payment = Non-negative float (not None).
        # principal_balance = Non-negative float (not None). Principal_Balance + Accrued_Interets must = Balance.
        # accrued_interest = Non-negative float (not None). Principal_Balance + Accrued_Interets must = Balance.


        >>> Account()
        Traceback (most recent call last):
        ...
        TypeError: Account.__init__() missing 5 required positional arguments: 'name', 'balance', 'min_balance', 'max_balance', and 'account_type'

        >>> print(Account(name='checking test',balance=0,min_balance=0,max_balance=0,account_type='checking').toJSON())
        {
        "Name":"checking test",
        "Balance":"0.0",
        "Min_Balance":"0.0",
        "Max_Balance":"0.0",
        "APR":"None",
        "Interest_Cadence":"None",
        "Interest_Type":"None",
        "Billing_Start_Date":"None",
        "Account_Type":"checking",
        "Principal_Balance":"None",
        "Accrued_Interest":"None",
        "Minimum_Payment":"None"
        }

        >>> print(Account(name='balance boundary violation',
        ... balance = -1,
        ... min_balance=0,
        ... max_balance=0,
        ... account_type="checking",
        ... throw_exceptions=False).toJSON())
        Account.balance was less than minimum balance
        <BLANKLINE>
        {
        "Name":"balance boundary violation",
        "Balance":"-1.0",
        "Min_Balance":"0.0",
        "Max_Balance":"0.0",
        "APR":"None",
        "Interest_Cadence":"None",
        "Interest_Type":"None",
        "Billing_Start_Date":"None",
        "Account_Type":"checking",
        "Principal_Balance":"None",
        "Accrued_Interest":"None",
        "Minimum_Payment":"None"
        }


        >>> print(Account(name='balance boundary violation',
        ... balance = -1,
        ... min_balance=0,
        ... max_balance=0,
        ... account_type="checking",
        ... print_debug_messages=False).toJSON())
        Traceback (most recent call last):
        ...
        ValueError

        >>> print(Account(name='account type error',
        ... balance=0,
        ... min_balance=0,
        ... max_balance=0,
        ... account_type='shmecking',
        ... throw_exceptions=False).toJSON())
        Account.account_type was not one of: checking, prev stmt bal, cur stmt bal, interest, savings, principal balance
        <BLANKLINE>
        {
        "Name":"account type error",
        "Balance":"0.0",
        "Min_Balance":"0.0",
        "Max_Balance":"0.0",
        "APR":"None",
        "Interest_Cadence":"None",
        "Interest_Type":"None",
        "Billing_Start_Date":"None",
        "Account_Type":"shmecking",
        "Principal_Balance":"None",
        "Accrued_Interest":"None",
        "Minimum_Payment":"None"
        }

        >>> print(Account(name='account type error',
        ... balance=0,
        ... min_balance=0,
        ... max_balance=0,
        ... account_type='shmecking',
        ... print_debug_messages=False).toJSON())
        Traceback (most recent call last):
        ...
        ValueError

        >>> print(Account(name='checking w non-None params that should be None',
        ... balance = 0,
        ... min_balance = 0,
        ... max_balance = 0,
        ... account_type='checking',
        ... billing_start_date_YYYYMMDD = '20000101',
        ... interest_type = 'simple',
        ... apr = 0,
        ... interest_cadence = 'weekly',
        ... previous_statement_balance = 0,
        ... minimum_payment = 0,
        ... principal_balance = 0,
        ... accrued_interest = 0,throw_exceptions=False).toJSON())
        For types other than credit, previous_statement_balance should be None.
        For types other than credit, loan, or savings, apr should be None.
        For types other than credit, loan, or savings, interest_cadence should be None.
        For types other than credit, loan, or savings, interest_type should be None.
        For types other than credit, loan, or savings, billing_start_date should be None.
        For types other than loan, principal_balance should be None.
        For types other than loan, accrued_interest should be None.
        For types other than credit or loan, minimum_payment should be None.
        <BLANKLINE>
        {
        "Name":"checking w non-None params that should be None",
        "Balance":"0.0",
        "Min_Balance":"0.0",
        "Max_Balance":"0.0",
        "APR":"0",
        "Interest_Cadence":"weekly",
        "Interest_Type":"simple",
        "Billing_Start_Date":"20000101",
        "Account_Type":"checking",
        "Principal_Balance":"0",
        "Accrued_Interest":"0",
        "Minimum_Payment":"0"
        }

        >>> print(Account(name='checking w non-None params that should be None',
        ... balance = 0,
        ... min_balance = 0,
        ... max_balance = 0,
        ... account_type='checking',
        ... billing_start_date_YYYYMMDD = '20000101',
        ... interest_type = 'simple',
        ... apr = 0,
        ... interest_cadence = 'weekly',
        ... previous_statement_balance = 0,
        ... minimum_payment = 0,
        ... principal_balance = 0,
        ... accrued_interest = 0,print_debug_messages=False).toJSON())
        Traceback (most recent call last):
        ...
        ValueError


        """
        self.name = name
        self.balance = balance
        self.min_balance = min_balance
        self.max_balance = max_balance
        self.account_type = account_type
        self.billing_start_date = billing_start_date_YYYYMMDD
        self.interest_type = interest_type
        self.apr = apr
        self.interest_cadence = interest_cadence
        self.minimum_payment = minimum_payment
        self.previous_statement_balance = previous_statement_balance
        self.principal_balance = principal_balance
        self.accrued_interest = accrued_interest

        exception_type_error_ind = False
        exception_type_error_message_string = ""

        exception_value_error_ind = False
        exception_value_error_message_string = ""

        if account_type.lower() in ['credit','loan']:
            exception_value_error_message_string += 'WARNING: Account.account_type was one of: credit, loan\n'
            exception_value_error_message_string += 'Note that these values are accepted by AccountSet.addAccount()\n'
            exception_value_error_message_string += 'but not by the class Account directly \n'
            exception_value_error_message_string += 'Value was:' + str(account_type.lower()) + "\n"
            exception_value_error_ind = True
            raise ValueError #honestly no need to continue if we hit this

        if account_type.lower() not in ['checking','prv stmt bal','curr stmt bal','savings','principal balance','interest']:
            exception_value_error_message_string += 'Account.account_type was not one of: checking, prv stmt bal, curr stmt bal, interest, savings, principal balance\n'
            exception_value_error_message_string += 'Value was:'+str(account_type.lower())+"\n"
            exception_value_error_ind = True
            raise ValueError

        self.name = str(name)
        # try:
        #     self.name = str(name)
        # except:
        #     exception_type_error_message_string += 'failed cast Account.name to str\n'
        #     exception_type_error_ind = True

        try:
            self.balance = float(balance)
        except:
            exception_type_error_message_string += 'failed cast Account.balance to float\n'
            exception_type_error_ind = True

        # if account_type.lower() in ['credit']:
        #     try:
        #         self.previous_statement_balance = float(previous_statement_balance)
        #     except:
        #         exception_type_error_message_string += 'failed cast Account.previous_statement_balance to float\n'
        #         exception_type_error_ind = True
        # else:
        #     if previous_statement_balance is not None:
        #         exception_value_error_message_string += "For types other than credit, Account.previous_statement_balance should be None.\n"
        #         exception_value_error_message_string += 'Value was:' + str(previous_statement_balance)+"\n"
        #         exception_value_error_ind = True


        try:
            self.min_balance = float(min_balance)
        except:
            exception_type_error_message_string += 'failed cast Account.min_balance to float\n'
            exception_type_error_ind = True

        try:
            assert self.min_balance <= self.balance
        except:
            exception_value_error_message_string += 'Account.balance was less than minimum balance\n'
            exception_value_error_ind = True

        try:
            self.max_balance = float(max_balance)
        except:
            exception_type_error_message_string += 'failed cast Account.max_balance to float\n'
            exception_type_error_ind = True

        try:
            assert self.max_balance >= self.balance
        except:
            exception_value_error_message_string += 'Account.balance was greater than Account.max_balance\n'
            exception_value_error_message_string += str(self.max_balance)+' >= '+str(self.balance)+' was not true\n'
            exception_value_error_ind = True

        try:
            assert self.max_balance >= self.min_balance
        except:
            exception_value_error_message_string += 'Account.max_balance was less than Account.min_balance\n'
            exception_value_error_ind = True

        if account_type.lower() in ['prv stmt bal','principal balance','savings']:
            try:
                self.apr = float(apr)
            except:
                exception_type_error_message_string += 'failed cast Account.apr to float\n'
                exception_type_error_ind = True
        else:
            if apr is not None:
                exception_value_error_message_string += "For types other than prv stmt bal, principal balance, or savings, Account.apr should be None.\n"
                exception_value_error_message_string += 'Value was:' + str(apr)+"\n"
                exception_value_error_ind = True

        self.interest_cadence = interest_cadence
        if account_type.lower() in ['prv stmt bal','principal balance','savings']:
            self.interest_cadence = str(interest_cadence)
            # try:
            #     self.interest_cadence = str(interest_cadence)
            # except:
            #     exception_type_error_message_string += 'failed cast Account.interest_cadence to str\n'
            #     exception_type_error_ind = True
        else:
            if interest_cadence is not None:
                exception_value_error_message_string += "For types other than prv stmt bal,principal balance,savings, Account.interest_cadence should be None.\n"
                exception_value_error_message_string += 'Value was:' + str(interest_cadence)+"\n"
                exception_value_error_ind = True

        if account_type.lower() in ['prv stmt bal','principal balance','savings']:
            self.interest_type = str(interest_type)
            # try:
            #     self.interest_type = str(interest_type) #None, Simple, Compound
            # except:
            #     exception_type_error_message_string += 'failed cast Account.interest_type to str\n'
            #     exception_type_error_ind = True
        else:
            if interest_type is not None:
                exception_value_error_message_string += "For types other than prv stmt bal,principal balance,savings, Account.interest_type should be None.\n"
                exception_value_error_message_string += 'Value was:' + str(interest_type)+"\n"
                exception_value_error_ind = True

        if account_type.lower() in ['prv stmt bal','principal balance','savings']:
            try:
                self.billing_start_date = datetime.datetime.strptime(billing_start_date_YYYYMMDD,'%Y%m%d')
            except:
                exception_type_error_message_string += 'failed cast Account.billing_start_date_YYYYMMDD to datetime\n'
                exception_type_error_ind = True
        else:
            if billing_start_date_YYYYMMDD is not None:
                exception_value_error_message_string += "For types other than prv stmt bal,principal balance,savings, Account.billing_start_date should be None.\n"
                exception_value_error_message_string += 'Value was:' + str(billing_start_date_YYYYMMDD)+"\n"
                exception_value_error_ind = True

        # if account_type.lower() in ['loan']:
        #     try:
        #         self.principal_balance = float(principal_balance)
        #     except:
        #         exception_type_error_message_string += 'failed cast Account.principal_balance to float\n'
        #         exception_type_error_ind = True
        # else:
        #     if principal_balance is not None:
        #         exception_value_error_message_string += "For types other than loan, Account.principal_balance should be None.\n"
        #         exception_value_error_message_string += 'Value was:' + str(principal_balance)+"\n"
        #         exception_value_error_ind = True

        # if account_type.lower() in ['principal balance']:
        #     try:
        #         self.accrued_interest = float(accrued_interest)
        #     except:
        #         exception_type_error_message_string += 'failed cast Account.accrued_interest to float\n'
        #         exception_value_error_message_string += 'Value was:' + str(accrued_interest) + "\n"
        #         exception_type_error_ind = True
        # else:
        #     if accrued_interest is not None:
        #         exception_value_error_message_string += "For types other than principal balance, Account.accrued_interest should be None.\n"
        #         exception_value_error_message_string += 'Value was:' + str(accrued_interest)+"\n"
        #         exception_value_error_ind = True

        if account_type.lower() in ['prv stmt bal','principal balance']:
            try:
                self.minimum_payment = float(minimum_payment)
            except:
                exception_type_error_message_string += 'failed cast Account.minimum_payment to float\n'
                exception_type_error_ind = True
        else:
            if minimum_payment is not None:
                exception_value_error_message_string += "For types other than prv stmt bal or principal balance, Account.minimum_payment should be None.\n"
                exception_value_error_message_string += 'Value was:' + str(minimum_payment)+"\n"
                exception_value_error_ind = True

        #Once procesing has reached this point, interest and principal have been separated into different accounts
        # if account_type.lower() in ['principal balance']:
        #     if principal_balance + accrued_interest != balance:
        #         exception_value_error_message_string += "Account.Principal_balance + Account.accrued_interest != Account.balance.\n"
        #         exception_value_error_ind = True

        if print_debug_messages:
            if exception_type_error_ind: print(exception_type_error_message_string)

            if exception_value_error_ind: print(exception_value_error_message_string)

        if throw_exceptions:
            if exception_type_error_ind:
                raise TypeError

            if exception_value_error_ind:
                raise ValueError



    def __repr__(self):
        return str(self)

    def __str__(self):

        single_account_df = pd.DataFrame({
            'Name':[self.name],
            'Balance': [self.balance],
            'Min Balance': [self.min_balance],
            'Max Balance': [self.max_balance],
            'Account Type': [self.account_type],
            'Billing Start Date': [self.billing_start_date],
            'Interest Type': [self.interest_type],
            'APR': [self.apr],
            'Interest Cadence': [self.interest_cadence],
            'Minimum Payment': [self.minimum_payment],
            'Previpus Statement Balance': [self.previous_statement_balance],
            'Principal Balance': [self.principal_balance],
            'Accrued Interest': [self.accrued_interest]
        })

        return single_account_df.to_string()

    def toJSON(self):
        """
        Get a JSON string representation of the Account object.
        """
        JSON_string = "{\n"
        JSON_string += "\"Name\":"+"\""+str(self.name)+"\",\n"
        JSON_string += "\"Balance\":" + "\"" + str(self.balance) + "\",\n"
        JSON_string += "\"Min_Balance\":" + "\"" + str(self.min_balance) + "\",\n"
        JSON_string += "\"Max_Balance\":" + "\"" + str(self.max_balance) + "\",\n"
        JSON_string += "\"Account_Type\":" + "\"" + str(self.account_type) + "\",\n"
        JSON_string += "\"Billing_Start_Date\":" + "\"" + str(self.billing_start_date) + "\",\n"
        JSON_string += "\"Interest_Type\":" + "\"" + str(self.interest_type) + "\",\n"
        JSON_string += "\"APR\":" + "\"" + str(self.apr) + "\",\n"
        JSON_string += "\"Interest_Cadence\":" + "\"" + str(self.interest_cadence) + "\",\n"
        JSON_string += "\"Minimum_Payment\":" + "\"" + str(self.minimum_payment) + "\"\n"
        JSON_string += "\"Previous_Statement_Balance\":" + "\"" + str(self.previous_statement_balance) + "\"\n"
        JSON_string += "\"Principal_Balance\":" + "\"" + str(self.principal_balance) + "\",\n"
        JSON_string += "\"Accrued_Interest\":" + "\"" + str(self.accrued_interest) + "\",\n"
        JSON_string += "}"
        return JSON_string

    # def fromJSON(self,JSON_string):
    #     #todo implement Account.fromJSON()
    #     pass


#written in one line so that test coverage can reach 100%
if __name__ == "__main__": import doctest ; doctest.testmod()


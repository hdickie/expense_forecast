
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
                 print_debug_messages=True, #this is here because doctest can test expected output OR exceptions, but not both
                 raise_exceptions=True
                 ):
        """
        Creates an Account object. Input validation is performed. Intended for use by internal methods.

        :param str name: A name for the account. Used to label output columns.
        :param float balance: A dollar value for the balance of the account.
        :param float min_balance: The minimum legal value for account balance. May be float('-Inf').
        :param float max_balance: The maximum legal value for account balance. May be float('Inf').
        :param str account_type: One of: prev stmt bal, curr stmt bal, principal balance, interest, checking. Not case sensitive.
        :param str billing_start_date_YYYYMMDD: A string that indicates the billing start date with format %Y%m%d.
        :param str interest_type: One of: 'simple', 'compound'. Not case sensitive.
        :param float apr: A float value that indicates the percent increase per YEAR.
        :param str interest_cadence: One of: 'daily', 'monthly', 'yearly'. Not case sensitive.
        :param float minimum_payment: Minimum payment. Only meaningful for loans and credit cards.
        :param bool print_debug_messages: if true, prints debug messages
        :param bool raise_exceptions: if true, throws any exceptions that were raised
        :raises ValueError: if the combination of input parameters is not valid.
        :raises  TypeError: if numerical values can't be cast to float. If billing_start_date is not string format %Y%m%d.
        :rtype: Account

        | Users should use AccountSet.addAcount(), since some complexity is handled by that method.
        | If you are initializing Accounts directly, you should know the following:

        | There are 5 required parameters in the method signature.
        | These are all parameters needed for Checking, Curr Stmt Bal and Interest account types.
        | Prev Stmt Bal and Principal Balance account types also require all the other parameters.
        | The Account constructor does not check types, but numerical parameters will raise a ValueError if they cannot be cast to float.

        | Account relationships are inferred based on name by splitting on ':'
        | e.g. an account called "credit" becomes "credit : curr stmt bal" and "credit : prev stmt bal". (whitespace is arbitrary)
        | Keep this in mind if you are initializing Accounts directly.

        | The logic of the way Accounts work is essentially this:
        | All accounts have either no interest, simple interest, or compound interest.
        | If no interest, great: we just need the 5 required parameters.
        | If simple interest, we need to track principal balance and interest separately.
        | If compound interest, we need to track previous and current statement balance.
        | The AccountSet.addAccount() method handles this. And allows "credit", "loan", and "savings" as account types.

        | Comments on negative amounts:
        | The absolute value of the amount is subtracted from the "From" account and added to the "To" account.
        | Therefore, the only effect the sign of the amount has is on the value inserted to the Memo line.

        | Example of the Account constructor:
        """
        self.name=name
        self.balance=balance
        self.min_balance=min_balance
        self.max_balance=max_balance
        self.account_type=account_type
        self.billing_start_date=billing_start_date_YYYYMMDD
        self.interest_type=interest_type
        self.apr=apr
        self.interest_cadence=interest_cadence
        self.minimum_payment=minimum_payment

        exception_type_error_ind=False
        exception_type_error_message_string=""

        exception_value_error_ind=False
        exception_value_error_message_string=""

        if account_type is None:
            account_type = 'None' \
                           ''
            self.account_type = "None" # to avoid exceptions when string methods are used

        if account_type.lower() in ['credit','loan']:
            exception_value_error_message_string += 'WARNING: Account.account_type was one of: credit, loan\n'
            exception_value_error_message_string += 'Note that these values are accepted by AccountSet.addAccount() but not by the class Account directly \n'
            exception_value_error_ind=True

        if account_type.lower() not in ['checking','prev stmt bal','curr stmt bal','savings','principal balance','interest']:
            exception_value_error_message_string += 'Account.account_type was not one of: checking, prev stmt bal, curr stmt bal, interest, savings, principal balance\n'
            exception_value_error_message_string += 'Value was:'+str(account_type.lower())+"\n"
            exception_value_error_ind=True

        self.name=str(name)
        if self.account_type.lower() in ['prev stmt bal', 'principal balance']:
            if ':' not in self.name:
                exception_value_error_message_string += 'Accounts of type prev stmt bal or principal balance require colon char in the account name.\n'
                exception_value_error_message_string += 'Value was:' + str(name) + "\n"
                exception_value_error_ind = True

                #raise ValueError #Accounts of type prev stmt bal or principal balance require colon char in the account name.

        try:
            self.balance=float(balance)
        except:
            exception_type_error_message_string += 'failed cast Account.balance to float\n'
            exception_type_error_message_string += 'Value was:' + str(balance) + "\n"
            exception_type_error_ind=True

        # if account_type.lower() in ['credit']:
        #     try:
        #         self.previous_statement_balance=float(previous_statement_balance)
        #     except:
        #         exception_type_error_message_string += 'failed cast Account.previous_statement_balance to float\n'
        #         exception_type_error_ind=True
        # else:
        #     if previous_statement_balance is not None:
        #         exception_value_error_message_string += "For types other than credit, Account.previous_statement_balance should be None.\n"
        #         exception_value_error_message_string += 'Value was:' + str(previous_statement_balance)+"\n"
        #         exception_value_error_ind=True


        try:
            self.min_balance=float(min_balance)
        except:
            exception_type_error_message_string += 'failed cast Account.min_balance to float\n'
            exception_type_error_message_string += 'Value was:' + str(min_balance) + "\n"
            exception_type_error_ind=True

        try:
            assert self.min_balance <= self.balance
        except:
            exception_value_error_message_string += 'Account.balance was less than minimum balance\n'
            exception_value_error_message_string += str(self.min_balance) + ' <= ' + str(self.balance) + ' was not true\n'
            exception_value_error_ind=True

        try:
            self.max_balance=float(max_balance)
        except:
            exception_type_error_message_string += 'failed cast Account.max_balance to float\n'
            exception_type_error_message_string += 'Value was:' + str(max_balance) + "\n"
            exception_type_error_ind=True

        try:
            assert self.max_balance >= self.balance
        except:
            exception_value_error_message_string += 'Account.balance was greater than Account.max_balance\n'
            exception_value_error_message_string += str(self.max_balance)+' >= '+str(self.balance)+' was not true\n'
            exception_value_error_ind=True

        try:
            assert self.max_balance >= self.min_balance
        except:
            exception_value_error_message_string += 'Account.max_balance was less than Account.min_balance\n'
            exception_value_error_ind=True

        if account_type.lower() in ['prev stmt bal','principal balance','savings']:
            try:
                self.apr=float(apr)
            except:
                exception_type_error_message_string += 'failed cast Account.apr to float\n'
                exception_type_error_message_string += 'Value was:' + str(apr) + "\n"
                exception_type_error_ind=True
        else:
            if apr is not None and apr != 'None':
                if float(apr) != 0:
                    exception_value_error_message_string += "For types other than prev stmt bal, principal balance, or savings, Account.apr should be None.\n"
                    exception_value_error_message_string += 'Value was:' + str(apr)+"\n"
                    exception_value_error_ind=True

        self.interest_cadence=interest_cadence

        if account_type.lower() in ['prev stmt bal','principal balance','savings']:
            if interest_cadence is not None:
                self.interest_cadence=str(interest_cadence)
            else:
                exception_value_error_message_string += "For account_type = prev stmt bal, principal balance, or savings, Account.interest_cadence should be one of: daily, monthly, quarterly, or yearly.\n"
                exception_value_error_message_string += "Value was:" + str(interest_cadence)+"\n"
                exception_value_error_ind = True

        else:
            if interest_cadence is not None and interest_cadence != 'None':
                exception_value_error_message_string += "For account_type other than prev stmt bal, principal balance, or savings, Account.interest_cadence should be None.\n"
                exception_value_error_message_string += 'Value was:' + str(interest_cadence)+"\n"
                exception_value_error_ind=True

        if account_type.lower() in ['prev stmt bal','principal balance','savings']:
            self.interest_type=str(interest_type)
        else:
            if interest_type is not None and interest_type != 'None':
                exception_value_error_message_string += "For types other than prev stmt bal, principal balance, or savings, Account.interest_type should be None.\n"
                exception_value_error_message_string += 'Value was:' + str(interest_type)+"\n"
                exception_value_error_ind=True

        if account_type.lower() in ['prev stmt bal','principal balance','savings']:
            try:
                try:
                    try:
                        self.billing_start_date = datetime.datetime.strptime(str(billing_start_date_YYYYMMDD),'%Y%m%d')
                    except:
                        self.billing_start_date = datetime.datetime.strptime(str(billing_start_date_YYYYMMDD), '%Y-%m-%d %H:%M:%S')
                except:
                    self.billing_start_date = datetime.datetime.strptime(str(billing_start_date_YYYYMMDD), '%Y-%m-%d')
            except Exception as e:
                exception_type_error_message_string += str(e)
                exception_type_error_message_string += 'failed cast Account.billing_start_date_YYYYMMDD to datetime\n'
                exception_type_error_message_string += 'Value was:' + str(billing_start_date_YYYYMMDD) + "\n"
                exception_type_error_ind=True
        else:
            if billing_start_date_YYYYMMDD != 'None':
                if billing_start_date_YYYYMMDD is not None:
                    exception_value_error_message_string += "For types other than prev stmt bal, principal balance, or savings, Account.billing_start_date should be None.\n"
                    exception_value_error_message_string += 'Value was:' + str(billing_start_date_YYYYMMDD)+"\n"
                    exception_value_error_ind=True

        # if account_type.lower() in ['loan']:
        #     try:
        #         self.principal_balance=float(principal_balance)
        #     except:
        #         exception_type_error_message_string += 'failed cast Account.principal_balance to float\n'
        #         exception_type_error_ind=True
        # else:
        #     if principal_balance is not None:
        #         exception_value_error_message_string += "For types other than loan, Account.principal_balance should be None.\n"
        #         exception_value_error_message_string += 'Value was:' + str(principal_balance)+"\n"
        #         exception_value_error_ind=True

        # if account_type.lower() in ['principal balance']:
        #     try:
        #         self.accrued_interest=float(accrued_interest)
        #     except:
        #         exception_type_error_message_string += 'failed cast Account.accrued_interest to float\n'
        #         exception_value_error_message_string += 'Value was:' + str(accrued_interest) + "\n"
        #         exception_type_error_ind=True
        # else:
        #     if accrued_interest is not None:
        #         exception_value_error_message_string += "For types other than principal balance, Account.accrued_interest should be None.\n"
        #         exception_value_error_message_string += 'Value was:' + str(accrued_interest)+"\n"
        #         exception_value_error_ind=True

        if account_type.lower() in ['prev stmt bal','principal balance']:
            try:
                self.minimum_payment=float(minimum_payment)
            except:
                exception_value_error_message_string += 'failed cast Account.minimum_payment to float\n'
                exception_value_error_message_string += 'Value was:' + str(minimum_payment) + "\n"
                exception_value_error_ind=True
        else:
            if minimum_payment != 'None':
                if minimum_payment is not None:
                    exception_value_error_message_string += "For types other than prev stmt bal or principal balance, Account.minimum_payment should be None.\n"
                    exception_value_error_message_string += 'Value was:' + str(minimum_payment)+"\n"
                    exception_value_error_ind=True

        if print_debug_messages:
            if exception_type_error_ind: print("TypeErrors:\n"+exception_type_error_message_string)

            if exception_value_error_ind: print("ValueErrors:\n"+exception_value_error_message_string)

        if raise_exceptions:
            if exception_type_error_ind:
                raise TypeError

            if exception_value_error_ind:
                raise ValueError



    def __repr__(self):
        return str(self)

    def __str__(self):

        single_account_df=pd.DataFrame({
            'Name':[self.name],
            'Balance': [self.balance],
            'Min Balance': [self.min_balance],
            'Max Balance': [self.max_balance],
            'Account Type': [self.account_type],
            'Billing Start Date': [self.billing_start_date],
            'Interest Type': [self.interest_type],
            'APR': [self.apr],
            'Interest Cadence': [self.interest_cadence],
            'Minimum Payment': [self.minimum_payment]
        })

        return single_account_df.to_string()

    def toJSON(self):
        """
        :rtype: string
        """
        JSON_string="{\n"
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
        JSON_string += "}"
        return JSON_string

    # def to_html(self):
    #     return pd.DataFrame({
    #         'Name': [self.name],
    #         'Balance': [self.balance],
    #         'Min Balance': [self.min_balance],
    #         'Max Balance': [self.max_balance],
    #         'Account Type': [self.account_type],
    #         'Billing Start Date': [self.billing_start_date],
    #         'Interest Type': [self.interest_type],
    #         'APR': [self.apr],
    #         'Interest Cadence': [self.interest_cadence],
    #         'Minimum Payment': [self.minimum_payment]
    #     }).to_html()

    # def fromJSON(self,JSON_string):
    #     pass


#written in one line so that test coverage can reach 100%
if __name__ == "__main__": import doctest ; doctest.testmod()


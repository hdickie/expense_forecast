
import datetime
import pandas as pd
import jsonpickle

class Account:

    def __init__(self,
                 name,  # no default because it is a required field
                 balance,
                 min_balance,
                 max_balance,
                 account_type,  # checking, credit, principal balance, interest, investment
                 billing_start_date_YYYYMMDD=None,
                 interest_type=None,
                 apr=None,
                 interest_cadence=None,
                 minimum_payment=None,
                 primary_checking_ind=False,
                 print_debug_messages=True,
                 # this is here because doctest can test expected output OR exceptions, but not both
                 raise_exceptions=True
                 ):
        """
        Creates an Account object. Input validation is performed. Intended for use by internal methods.

        :param str name: A name for the account. Used to label output columns.
        :param float balance: A dollar value for the balance of the account.
        :param float min_balance: The minimum legal value for account balance. May be float('-Inf').
        :param float max_balance: The maximum legal value for account balance. May be float('Inf').
        :param str account_type: One of: prev stmt bal, curr stmt bal, principal balance, interest, checking, billing cycle payment balance. Not case sensitive.
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
        | These are all parameters needed for Billing Cycle Payment Balance, Checking, Curr Stmt Bal and Interest account types.
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

        """

        self.name = str(name)
        self.account_type = str(account_type).lower()
        self.primary_checking_ind = bool(primary_checking_ind)

        try:
            self.balance = float(balance)
        except ValueError:
            raise TypeError(f'Account.balance must be a float. Value was: {balance}')

        try:
            self.min_balance = float(min_balance)
        except ValueError:
            raise TypeError(f'Account.min_balance must be a float. Value was: {min_balance}')

        try:
            self.max_balance = float(max_balance)
        except ValueError:
            raise TypeError(f'Account.max_balance must be a float. Value was: {max_balance}')

        if self.min_balance > self.balance:
            raise ValueError(f'Account.balance ({self.balance}) cannot be less than min_balance ({self.min_balance}).')

        if self.max_balance < self.balance:
            raise ValueError(
                f'Account.balance ({self.balance}) cannot be greater than max_balance ({self.max_balance}).')

        if self.max_balance < self.min_balance:
            raise ValueError(
                f'Account.max_balance ({self.max_balance}) cannot be less than min_balance ({self.min_balance}).')

        valid_account_types = ['checking', 'credit prev stmt bal', 'credit curr stmt bal', 'savings', 'principal balance', 'interest', 'credit billing cycle payment bal', 'loan billing cycle payment bal', 'loan end of prev cycle bal', 'credit end of prev cycle bal']
        if self.account_type not in valid_account_types:
            raise ValueError(f"Invalid account_type: {account_type}. Must be one of {', '.join(valid_account_types)}.")

        if self.account_type in ['credit curr stmt bal','credit prev stmt bal', 'principal balance', 'credit billing cycle payment bal', 'loan billing cycle payment bal', 'loan prev end of cycle balance', 'credit prev end of cycle balance']:
            if ':' not in self.name:
                raise ValueError(
                    'Accounts of type credit curr stmt bal, credit prev stmt bal, credit billing cycle payment bal, loan billing cycle payment bal, principal balance, loan prev end of cycle balance, credit prev end of cycle balance require colon char in the account name.')

        # Handle apr
        if self.account_type in ['credit prev stmt bal', 'principal balance', 'savings']:
            if apr is None:
                raise ValueError(f"Account.apr is required for account_type '{self.account_type}'.")
            try:
                self.apr = float(apr)
                if self.apr < 0:
                    raise ValueError('Account.apr must be non-negative.')
            except ValueError:
                raise TypeError(f'Account.apr must be a float. Value was: {apr}')
        else:
            if apr is not None and float(apr) != 0:
                raise ValueError(f"Account.apr should be None or 0 for account_type '{self.account_type}'.")

            self.apr = None

        # Handle interest_cadence
        if self.account_type in ['credit prev stmt bal', 'principal balance', 'savings']:
            if interest_cadence is None:
                raise ValueError(f"Account.interest_cadence is required for account_type '{self.account_type}'.")
            else:
                self.interest_cadence = str(interest_cadence).lower()
        else:
            if interest_cadence is not None:
                raise ValueError(f"Account.interest_cadence should be None for account_type '{self.account_type}'.")
            self.interest_cadence = None

        # Handle interest_type
        if self.account_type in ['principal balance', 'savings']:
            if interest_type is None:
                raise ValueError(f"Account.interest_type is required for account_type '{self.account_type}'.")
            self.interest_type = str(interest_type).lower()
            if self.interest_type not in ['simple', 'compound']:
                raise ValueError("Interest type must be 'simple' or 'compound'.")
        else:
            if interest_type is not None:
                raise ValueError(f"Account.interest_type should be None for account_type '{self.account_type}'.")
            self.interest_type = None

        # Handle billing_start_date_YYYYMMDD
        if self.account_type in ['credit billing cycle payment bal','loan billing cycle payment bal', 'credit prev stmt bal', 'principal balance', 'savings', 'loan end of prev cycle bal', 'credit end of prev cycle bal']:
            if billing_start_date_YYYYMMDD is None:
                raise ValueError(
                    f"Account.billing_start_date_YYYYMMDD is required for account_type '{self.account_type}'.")
            else:
                try:
                    if isinstance(billing_start_date_YYYYMMDD, str):
                        datetime.datetime.strptime(billing_start_date_YYYYMMDD, '%Y%m%d')
                    else:
                        raise TypeError
                    self.billing_start_date_YYYYMMDD = billing_start_date_YYYYMMDD
                except ValueError:
                    raise TypeError(
                        f'Account.billing_start_date_YYYYMMDD must be a string in %Y%m%d format. Value was: {billing_start_date_YYYYMMDD}')
        else:
            if billing_start_date_YYYYMMDD is not None:
                raise ValueError(
                    f"Account.billing_start_date_YYYYMMDD should be None for account_type '{self.account_type}'.")
            self.billing_start_date_YYYYMMDD = None

        # Handle minimum_payment
        if self.account_type in ['credit prev stmt bal', 'principal balance']:
            if minimum_payment is None:
                raise ValueError(f"Account.minimum_payment is required for account_type '{self.account_type}'.")
            try:
                self.minimum_payment = float(minimum_payment)
            except ValueError:
                raise TypeError(f'Account.minimum_payment must be a float. Value was: {minimum_payment}')

            if self.minimum_payment < 0:
                raise ValueError('Account.minimum_payment must be non-negative.')
        else:
            if minimum_payment is not None:
                raise ValueError(f"Account.minimum_payment should be None for account_type '{self.account_type}'.")
            self.minimum_payment = None

        # Handle primary_checking_ind
        if not isinstance(self.primary_checking_ind, bool):
            raise TypeError(f'primary_checking_ind must be a bool. Value was: {primary_checking_ind}')

        # If print_debug_messages is True, we can print messages if needed, but exceptions are raised immediately.

    def to_json(self):
        """
        :rtype: string
        """
        return jsonpickle.encode(self, indent=4)

    def __str__(self):
        return pd.DataFrame({
            'Name': [self.name],
            'Balance': [self.balance],
            'Min_Balance': [self.min_balance],
            'Max_Balance': [self.max_balance],
            'Account_Type': [self.account_type],
            'Billing_Start_Date': [self.billing_start_date_YYYYMMDD],
            'Interest_Type': [self.interest_type],
            'APR': [self.apr],
            'Interest_Cadence': [self.interest_cadence],
            'Minimum_Payment': [self.minimum_payment],
            'Primary_Checking_Ind': [self.primary_checking_ind]
        }).to_string()


#written in one line so that test coverage can reach 100%
if __name__ == "__main__": import doctest ; doctest.testmod()

# Before GPT
# 96 passed, 137 deselected in 17.85s

# After GPT
# 96 passed, 137 deselected in 18.76s
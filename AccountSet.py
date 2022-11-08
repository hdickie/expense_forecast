"""
Single-line AccountSet description

Multiple-line AccountSet description

"""
import Account, pandas as pd
class AccountSet:

    def __init__(self,accounts__list=[]):
        """
        Creates an AccountSet object. Previous Statement Balance and Loan Interest accounts are created automatically.

        :param accounts__list:

        >>> AccountSet()
        Empty DataFrame
        Columns: [Name, Balance, Previous_Statement_Balance, Min_Balance, Max_Balance, APR, Interest_Cadence, Interest_Type, Billing_Start_Dt, Account_Type, Principal_Balance, Accrued_Interest, Minimum_Payment]
        Index: []

        >>> print(AccountSet([Account.Account(name="test checking",
        ... balance = 0,
        ... min_balance = 0,
        ... max_balance = 0,
        ... account_type = 'checking'
        ... )]).toJSON())
        {
        {
        "Name":"test checking",
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
        }
        <BLANKLINE>

        >>> print(AccountSet([Account.Account(name="test loan",
        ... balance = 500,
        ... min_balance = 0,
        ... max_balance = float('Inf'),
        ... account_type = 'loan',
        ... billing_start_date_YYYYMMDD='20220103',
        ... interest_type = 'Simple',
        ... apr=0.0376,
        ... interest_cadence='daily',
        ... minimum_payment=55.17,
        ... previous_statement_balance=None,
        ... principal_balance = 400,
        ... accrued_interest = 100,
        ... print_debug_messages = True,
        ... throw_exceptions = False
        ... )]).toJSON())

        >>> print(AccountSet([Account.Account(name="test credit",
        ... balance = 1000,
        ... min_balance = 0,
        ... max_balance = 20000,
        ... account_type = 'credit',
        ... billing_start_date_YYYYMMDD='20220103',
        ... interest_type = 'Compound',
        ... apr=0.2674,
        ... interest_cadence='monthly',
        ... minimum_payment=40,
        ... previous_statement_balance=2000,
        ... print_debug_messages = True,
        ... throw_exceptions = False
        ... )]).toJSON())

        """

        # IMPORTANT NOTE: the previous statement balance and interest accounts should be the index after
        # im sure there is a fancier/smarter design but the logic I have implemented in ExpenseForecast assumes this

        self.accounts = []
        for account in accounts__list:
            if account.account_type == "credit":
                prev_stmt_bal_acct = Account.Account(name=account.name+": Prev Stmt Bal",
                balance=account.previous_statement_balance,
                min_balance=account.min_balance,
                max_balance=account.max_balance,
                account_type="Prev Stmt Bal",
                billing_start_date_YYYYMMDD = account.billing_start_date,
                interest_type = account.interest_type,
                apr = account.apr,
                interest_cadence = account.interest_cadence,
                minimum_payment = account.minimum_payment,
                throw_exceptions=False)

                account.name += ": Cur Stmt Bal"
                account.account_type = "Cur Stmt Bal"
                account.interest_type = None
                account.apr = None
                account.interest_cadence = None
                account.previous_statement_balance = None
                account.minimum_payment = None

                self.accounts.append(account)
                self.accounts.append(prev_stmt_bal_acct)
            elif account.account_type == "loan":
                # todo create interest account
                # todo also set appropriate values to None
                loan_interest_acct = Account.Account(name = str(account.name)+': Interest',  # no default because it is a required field
                balance = float(account.accrued_interest),
                min_balance = 0,
                max_balance = float('Inf'),
                account_type = 'interest',
                billing_start_date_YYYYMMDD = None,
                interest_type = None,
                apr = None,
                interest_cadence = None,
                minimum_payment = None,
                previous_statement_balance = None,
                principal_balance = None,
                accrued_interest = None,
                throw_exceptions=False
                )

                account.name += ': Principal Balance'
                account.account_type = 'Principal Balance'
                account.accrued_interest = None

                self.accounts.append(account)
                self.accounts.append(loan_interest_acct)
            else:
                self.accounts.append(account)

    def __str__(self):
        return self.getAccounts().to_string()

    def __repr__(self):
        return str(self)

    def addAccount(self,
                 name,
                 balance,
                 min_balance,
                 max_balance,
                 account_type,
                 billing_start_date_YYYYMMDD=None,
                 interest_type=None,
                 apr = None,
                 interest_cadence=None,
                 minimum_payment=None,
                 previous_statement_balance=None,
                 principal_balance = None,
                 accrued_interest = None,
                 print_debug_messages = True,
                 throw_exceptions = True
                 ):

        """ Add an Account to list AccountSet.accounts. For credit and loan type accounts, previous statement balance and interest accounts are created.

        """

        #TODO this should be based on interest type or interest AND account type
        if account_type.lower() == 'loan':
            account = Account.Account(name+': Principal Balance', balance, previous_statement_balance, min_balance, max_balance, apr, interest_cadence, interest_type,
                                      billing_start_date_YYYYMMDD, 'Principal Balance', principal_balance, None,minimum_payment,print_debug_messages,throw_exceptions)
            self.accounts.append(account)

            account = Account.Account(name+': Interest', balance, previous_statement_balance, min_balance, max_balance, apr, interest_cadence, interest_type,
                                      billing_start_date_YYYYMMDD, 'Interest', None, accrued_interest,minimum_payment,print_debug_messages,throw_exceptions)
            self.accounts.append(account)

        elif account_type.lower() == 'credit':
            account = Account.Account(name+': Current Statement Balance', balance, 0, min_balance, max_balance, apr, interest_cadence, interest_type,
                                      billing_start_date_YYYYMMDD, 'Current Statement Balance', principal_balance, None,minimum_payment,print_debug_messages,throw_exceptions)
            self.accounts.append(account)

            account = Account.Account(name+': Previous Statement Balance', previous_statement_balance, 0, min_balance, max_balance, apr, interest_cadence, interest_type,
                                      billing_start_date_YYYYMMDD, 'Previous Statement Balance', principal_balance, None,minimum_payment,print_debug_messages,throw_exceptions)
            self.accounts.append(account)
        else:
            account = Account.Account(name, balance, previous_statement_balance, min_balance, max_balance, apr, interest_cadence, interest_type,
                                      billing_start_date_YYYYMMDD, account_type, principal_balance, accrued_interest,minimum_payment,print_debug_messages,throw_exceptions)
            self.accounts.append(account)

    def getAccounts(self):
        """
        Get a DataFrame representing the AccountSet object.

        This test is failing even though this is indeed the result I get when I try this in the console.
        # >>> x = AccountSet().getAccounts()
        # Empty DataFrame
        # Columns: [Name, Balance, Previous_Statement_Balance, Min_Balance, Max_Balance, APR, Interest_Cadence, Interest_Type, Billing_Start_Dt, Account_Type, Principal_Balance, Accrued_Interest, Minimum_Payment]
        # Index: []

        >>> print(AccountSet([Account.Account(name='test',balance=0,min_balance=0,max_balance=0,account_type = "checking")]).toJSON())
        {
        {
        "Name":"test",
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
        }
        <BLANKLINE>
        """
        all_accounts_df = pd.DataFrame({'Name':[],'Balance':[],'Previous_Statement_Balance':[],'Min_Balance':[],'Max_Balance':[],
                                        'APR': [], 'Interest_Cadence': [], 'Interest_Type': [], 'Billing_Start_Dt': [],
                                        'Account_Type': [], 'Principal_Balance': [], 'Accrued_Interest': [], 'Minimum_Payment': []
                                        })

        for account in self.accounts:
            new_account_row_df = pd.DataFrame({'Name': [account.name],
                                               'Balance': [account.balance],
                                               'Previous_Statement_Balance': [account.previous_statement_balance],
                                               'Min_Balance': [account.min_balance],
                                               'Max_Balance': [account.max_balance],
                                               'APR': [account.apr],
                                               'Interest_Cadence': [account.interest_cadence],
                                               'Interest_Type': [account.interest_type],
                                               'Billing_Start_Dt': [account.billing_start_date],
                                               'Account_Type': [account.account_type],
                                               'Principal_Balance': [account.principal_balance],
                                               'Accrued_Interest': [account.accrued_interest],
                                               'Minimum_Payment': [account.minimum_payment]
                                            })

            all_accounts_df = pd.concat([all_accounts_df, new_account_row_df], axis=0)
            all_accounts_df.reset_index(drop=True,inplace=True)

        #if there are no accounts, I want to return a data frame with 0 rows

        return all_accounts_df

    def toJSON(self):
        """
        Get a JSON string representation of the AccountSet object.
        """

        JSON_string="{\n"
        for i in range(0,len(self.accounts)):
            account = self.accounts[i]
            JSON_string+=account.toJSON()
            if i+1 != len(self.accounts):
                JSON_string+=","
            JSON_string+='\n'
        JSON_string+='}\n'

        return JSON_string

    def fromJSON(self,JSON_string):
        #todo implement AccountSet.fromJSON()
        pass

if __name__ == "__main__":
    import doctest
    doctest.testmod()
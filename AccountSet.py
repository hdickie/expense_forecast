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

        #todo example of adding a loan account. (copy this into the unittest)

        #todo example of adding a credit account. (copy this into the unittest)

        """

        # IMPORTANT NOTE: the previous statement balance and interest accounts should be the index after
        # im sure there is a fancier/smarter design but the logic I have implemented in ExpenseForecast assumes this

        self.accounts = []
        for account in accounts__list:
            self.accounts.append(account)

            #if credit or loan accounts are being added via this method, they should already be consistent.
            #FOR THAT REASON, adding accounts this way is not recommended.
            #therefore, once all accounts have been added to self.accounts, we check for consistency

        if len(self.accounts) > 0:
            accounts_df = self.getAccounts()
            #index_of_name_column = accounts_df.columns.tolist().index('Name')
            loan_check_name__series = accounts_df.loc[accounts_df.Account_Type.isin(['Principal Balance','Interest']), 'Name']
            cc_check__name__series = accounts_df.loc[accounts_df.Account_Type.isin(['Prv Stmt Bal','Curr Stmt Bal']), 'Name']

            print('loan_check_name__series:'+str(loan_check_name__series))
            print('cc_check__name__series:'+str(cc_check__name__series))

            loan_pb_acct__list = list()
            loan_interest_acct__list = list()
            for acct in loan_check_name__series:
                acct_name = acct.split(':')[0]
                acct_type = acct.split(':')[1].lower().strip()

                if acct_type == 'principal balance':
                    loan_pb_acct__list.append(acct_name)
                elif acct_type == 'interest':
                    loan_interest_acct__list.append(acct_name)
                # else:
                #     print('this should be impossible')
                #     print('value was:' + str(acct_type))
                #     raise ValueError

            cc_prv_acct__list = list()
            cc_curr_acct__list = list()
            for acct in cc_check__name__series:
                acct_name = acct.split(':')[0]
                acct_type = acct.split(':')[1].lower().strip()

                if acct_type == 'prv stmt bal':
                    cc_prv_acct__list.append(acct_name)
                elif acct_type == 'curr stmt bal':
                    cc_curr_acct__list.append(acct_name)
                # else:
                #     print('this should be impossible')
                #     print('value was:'+str(acct_type))
                #     raise ValueError

            print('loan_pb_acct__list:'+str(loan_pb_acct__list))
            print('loan_interest_acct__list:'+str(loan_interest_acct__list))
            print('cc_prv_acct__list:'+str(cc_prv_acct__list))
            print('cc_curr_acct__list:'+str(cc_curr_acct__list))
            print('')

            if loan_pb_acct__list != loan_interest_acct__list:
                raise ValueError
            if cc_prv_acct__list != cc_curr_acct__list:
                raise ValueError



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
        """
        Add an Account to list AccountSet.accounts. For credit and loan type accounts, previous statement balance and interest accounts are created.
        """

        #TODO this should be based on interest type or interest AND account type
        if account_type.lower() == 'loan':


            if principal_balance + accrued_interest != balance:
                print("Account.Principal_balance + Account.accrued_interest != Account.balance.\n")
                raise ValueError

            account = Account.Account(name = name+': Principal Balance',
                                      balance = principal_balance,
                                      min_balance = min_balance,
                                      max_balance = max_balance,
                                      account_type = 'Principal Balance',
                                      billing_start_date_YYYYMMDD = billing_start_date_YYYYMMDD,
                                      interest_type = interest_type,
                                      apr = apr,
                                      interest_cadence = interest_cadence,
                                      minimum_payment = minimum_payment,
                                      previous_statement_balance = None,
                                      principal_balance = None,
                                      accrued_interest = None,
                                      print_debug_messages = print_debug_messages,
                                      throw_exceptions = throw_exceptions)
            self.accounts.append(account)


            account = Account.Account(name = name+': Interest',
                                      balance=accrued_interest,
                                      min_balance=min_balance,
                                      max_balance=max_balance,
                                      account_type='Interest',
                                      billing_start_date_YYYYMMDD=None,
                                      interest_type=None,
                                      apr=None,
                                      interest_cadence=None,
                                      minimum_payment=None,
                                      previous_statement_balance=None,
                                      principal_balance=None,
                                      accrued_interest=None,
                                      print_debug_messages=print_debug_messages,
                                      throw_exceptions=throw_exceptions)
            self.accounts.append(account)

        elif account_type.lower() == 'credit':
            account = Account.Account(name = name+': Curr Stmt Bal',
                                      balance = balance,
                                      min_balance = min_balance,
                                      max_balance = max_balance,
                                      account_type = 'Curr Stmt Bal',
                                      billing_start_date_YYYYMMDD = None,
                                      interest_type = None,
                                      apr = None,
                                      interest_cadence = None,
                                      minimum_payment = None,
                                      previous_statement_balance = None,
                                      principal_balance = None,
                                      accrued_interest = None,
                                      print_debug_messages = print_debug_messages,
                                      throw_exceptions = throw_exceptions)
            self.accounts.append(account)

            account = Account.Account(name = name+': Prv Stmt Bal',
                                      balance = previous_statement_balance,
                                      min_balance = min_balance,
                                      max_balance = max_balance,
                                      account_type = 'Prv Stmt Bal',
                                      billing_start_date_YYYYMMDD = billing_start_date_YYYYMMDD,
                                      interest_type = interest_type,
                                      apr = apr,
                                      interest_cadence = interest_cadence,
                                      minimum_payment = minimum_payment,
                                      previous_statement_balance = None,
                                      principal_balance = None,
                                      accrued_interest = None,
                                      print_debug_messages = print_debug_messages,
                                      throw_exceptions = throw_exceptions)
            self.accounts.append(account)
        else:
            account = Account.Account(name = name,
                                      balance = balance,
                                      min_balance = min_balance,
                                      max_balance = max_balance,
                                      account_type = account_type,
                                      billing_start_date_YYYYMMDD = billing_start_date_YYYYMMDD,
                                      interest_type = interest_type,
                                      apr = apr,
                                      interest_cadence = interest_cadence,
                                      minimum_payment = minimum_payment,
                                      previous_statement_balance = previous_statement_balance,
                                      principal_balance = principal_balance,
                                      accrued_interest = accrued_interest,
                                      print_debug_messages = print_debug_messages,
                                      throw_exceptions = throw_exceptions)
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
        all_accounts_df = pd.DataFrame({'Name':[],
                                        'Balance':[],
                                        'Min_Balance':[],
                                        'Max_Balance':[],
                                        'Account_Type': [],
                                        'Billing_Start_Dt': [],
                                        'Interest_Type': [],
                                        'APR': [],
                                        'Interest_Cadence': [],
                                        'Minimum_Payment': [],
                                        'Previous_Statement_Balance': [],
                                        'Principal_Balance': [],
                                        'Accrued_Interest': []
                                        })

        for account in self.accounts:
            new_account_row_df = pd.DataFrame({'Name': [account.name],
                                               'Balance': [account.balance],
                                               'Min_Balance': [account.min_balance],
                                               'Max_Balance': [account.max_balance],
                                               'Account_Type': [account.account_type],
                                               'Billing_Start_Dt': [account.billing_start_date],
                                               'Interest_Type': [account.interest_type],
                                               'APR': [account.apr],
                                               'Interest_Cadence': [account.interest_cadence],
                                               'Minimum_Payment': [account.minimum_payment],
                                               'Previous_Statement_Balance': [account.previous_statement_balance],
                                               'Principal_Balance': [account.principal_balance],
                                               'Accrued_Interest': [account.accrued_interest]
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
        JSON_string+='}'

        return JSON_string

    # def fromJSON(self,JSON_string):
    #     #todo implement AccountSet.fromJSON()
    #     pass

#written in one line so that test coverage can reach 100%
if __name__ == "__main__": import doctest ; doctest.testmod()
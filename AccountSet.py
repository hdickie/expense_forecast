import Account, pandas as pd


class AccountSet:

    def __init__(self,accounts__list=[]):
        self.accounts = []
        for account in accounts__list:
            self.accounts.append(account)

    def __str__(self):
        return_string = ""

        for account in self.accounts:
            return_string += str(account) + "\n"

        return return_string

    def __repr__(self):
        return str(self)

    def addAccount(self,
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


        #TODO this should be based on interest type or interest AND account type
        if account_type.lower() == 'loan':
            account = Account.Account(name+': Principal Balance', balance, previous_statement_balance, min_balance, max_balance, apr, interest_cadence, interest_type,
                                      billing_start_date, 'Principal Balance', principal_balance, None,minimum_payment)
            self.accounts.append(account)

            account = Account.Account(name+': Interest', balance, previous_statement_balance, min_balance, max_balance, apr, interest_cadence, interest_type,
                                      billing_start_date, 'Principal Balance', None, accrued_interest,minimum_payment)
            self.accounts.append(account)

        elif account_type.lower() == 'credit':
            account = Account.Account(name+': Current Statement Balance', balance, 0, min_balance, max_balance, apr, interest_cadence, interest_type,
                                      billing_start_date, 'Current Statement Balance', principal_balance, None,minimum_payment)
            self.accounts.append(account)

            account = Account.Account(name+': Previous Statement Balance', previous_statement_balance, 0, min_balance, max_balance, apr, interest_cadence, interest_type,
                                      billing_start_date, 'Previous Statement Balance', principal_balance, None,minimum_payment)
            self.accounts.append(account)
        else:
            account = Account.Account(name, balance, previous_statement_balance, min_balance, max_balance, apr, interest_cadence, interest_type,
                                      billing_start_date, account_type, principal_balance, accrued_interest,minimum_payment)
            self.accounts.append(account)

    def getAccounts(self):
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

        return all_accounts_df

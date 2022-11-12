import Account, pandas as pd


class AccountSet:

    def __init__(self, accounts__list=[], print_debug_messages=True, raise_exceptions=True):
        """
        Creates an AccountSet object. Possible Account Types are: Checking, Credit, Loan, Savings. Consistency is checked.

        :param list accounts__list: A list of Account objects. Empty list by default. Consistency is checked.
        :raises ValueError: if the combination of input parameters is not valid.
        :raises Other exception types: if members of input list do not have the methods and attributes of an Account object.
        :rtype: AccountSet

        | Reasons for ValueError exception:
        | Combined balance between prev and curr violate account boundaries.
        | Accounts that are related (as implied by name) have different parameters.
        | A principal balance account was input without an interest account, vice versa, and etc.

        | Creating an AccountSet without passing parameters is a valid thing to do.

        >>> AccountSet()
        Empty DataFrame
        Columns: [Name, Balance, Min_Balance, Max_Balance, Account_Type, Billing_Start_Dt, Interest_Type, APR, Interest_Cadence, Minimum_Payment]
        Index: []

        | If you want to pass a list of Accounts explicitly you can do that as well.

        >>> print(AccountSet([Account.Account(name="test checking",
        ... balance=0,
        ... min_balance=0,
        ... max_balance=0,
        ... account_type='checking'
        ... )]).toJSON())
        {
        {
        "Name":"test checking",
        "Balance":"0.0",
        "Min_Balance":"0.0",
        "Max_Balance":"0.0",
        "Account_Type":"checking",
        "Billing_Start_Date":"None",
        "Interest_Type":"None",
        "APR":"None",
        "Interest_Cadence":"None",
        "Minimum_Payment":"None"
        }
        }
        """

        value_error_text = ""
        value_error_ind = False

        type_error_text = ""
        type_error_ind = False

        # IMPORTANT NOTE: the previous statement balance and interest accounts should be the index after
        # im sure there is a fancier/smarter design but the logic I have implemented in ExpenseForecast assumes this

        self.accounts = []
        for account in accounts__list:
            self.accounts.append(account)

            # if credit or loan accounts are being added via this method, they should already be consistent.
            # FOR THAT REASON, adding accounts this way is not recommended.
            # therefore, once all accounts have been added to self.accounts, we check for consistency

        if len(self.accounts) > 0:

            # todo assert that the object has the attributes that an account should?
            required_attributes = ['name', 'balance', 'min_balance', 'max_balance', 'account_type',
                                   'billing_start_date',
                                   'interest_type', 'apr', 'interest_cadence', 'minimum_payment']

            for obj in self.accounts:
                try:
                    assert set(required_attributes) & set(dir(obj)) == set(required_attributes)
                except:
                    value_error_text += "An object in the input list did not have all the attributes an Account is expected to have.\n"
                    value_error_text += "Are all objects in the input list of type Account?\n"
                    value_error_ind = True

                    # in practice this output never makes it to the console but im including these lines for consistency
                    if print_debug_messages:
                        print(value_error_text)

                    # this is about to explode, so raising the exception here will be easier to debug
                    raise ValueError

                if obj.account_type.lower() in ['prev stmt bal','principal balance']:
                    try:
                        assert ':' in obj.name
                    except:
                        value_error_text += "Accounts of type prev stmt bal or principal balance require '\:'\ in the account name. '\n"
                        value_error_ind = True

                        if print_debug_messages:
                            print(value_error_text)

                        # this is about to explode, so raising the exception here will be easier to debug
                        raise ValueError


            accounts_df = self.getAccounts()

            # print('accounts_df:')
            # print(accounts_df.to_string())
            # print('accounts_df.Account_Type:')
            # print(accounts_df.Account_Type)
            # print('accounts_df.Account_Type.isin([Principal Balance, Interest]):')
            # print(accounts_df.Account_Type.isin(['Principal Balance', 'Interest']))
            # print('accounts_df.Account_Type.isin([Prev Stmt Bal, Curr Stmt Bal]):')
            # print(accounts_df.Account_Type.isin(['Prev Stmt Bal', 'Curr Stmt Bal']))

            # print('accounts_df.loc[accounts_df.Account_Type.isin([Principal Balance, Interest],:)]')
            # print(accounts_df.loc[
            #     accounts_df.Account_Type.isin(['Principal Balance', 'Interest']),:])

            # print('accounts_df.loc[accounts_df.Account_Type.isin([Principal Balance, Interest],:)]')
            # print(accounts_df.loc[
            #       accounts_df.Account_Type.isin(['Prev Stmt Bal', 'Curr Stmt Bal']), :])

            # index_of_name_column=accounts_df.columns.tolist().index('Name')
            loan_check_name__series = accounts_df.loc[
                accounts_df.Account_Type.isin(['Principal Balance', 'Interest']), 'Name']
            cc_check__name__series = accounts_df.loc[
                accounts_df.Account_Type.isin(['Prev Stmt Bal', 'Curr Stmt Bal']), 'Name']

            # print('loan_check_name__series:')
            # print(loan_check_name__series)

            # print('cc_check__name__series:')
            # print(cc_check__name__series)

            loan_pb_acct__list = list()
            loan_interest_acct__list = list()
            for acct in loan_check_name__series:
                acct_name = acct.split(':')[0]
                acct_type = acct.split(':')[1].lower().strip()

                # print('acct_name:' + str(acct_name))
                # print('acct_type:' + str(acct_type))

                if acct_type.lower() == 'principal balance':
                    loan_pb_acct__list.append(acct_name)
                elif acct_type.lower() == 'interest':
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

                # print('acct_name:'+str(acct_name))
                # print('acct_type:'+str(acct_type))

                if acct_type.lower() == 'prev stmt bal':
                    cc_prv_acct__list.append(acct_name)
                elif acct_type.lower() == 'curr stmt bal':
                    cc_curr_acct__list.append(acct_name)
                # else:
                #     print('this should be impossible')
                #     print('value was:'+str(acct_type))
                #     raise ValueError

            if set(loan_pb_acct__list) & set(loan_interest_acct__list) != set(loan_pb_acct__list) and \
                    set(loan_pb_acct__list) & set(loan_interest_acct__list) != set(loan_interest_acct__list):
                value_error_text += "The intersection of Principal Balance and Interest accounts was not equal to the union.\n"
                value_error_text += "loan_pb_acct__list:\n"
                value_error_text += str(loan_pb_acct__list) + "\n"
                value_error_text += 'loan_interest_acct__list:\n'
                value_error_text += str(loan_interest_acct__list) + "\n"
                value_error_ind = True

            if set(cc_prv_acct__list) & set(cc_curr_acct__list) != set(cc_prv_acct__list) and \
                set(cc_prv_acct__list) & set(cc_curr_acct__list) != set(cc_curr_acct__list):
                value_error_text += "The intersection of Prev Stmt Bal and Curr Stmt Bal accounts was not equal to the union.\n"
                value_error_text += "cc_prv_acct__list:\n"
                value_error_text += str(cc_prv_acct__list) + "\n"
                value_error_text += 'cc_curr_acct__list:\n'
                value_error_text += str(cc_curr_acct__list) + "\n"
                value_error_ind = True

            #at this point, all accounts have been added to self.accounts, been verified to have the necessary attributes
            #and confirmed that related accounts are present. Therefore, we can now check for consistent parameters
            #between related accounts, also check account boundaries against the combined balances

            accounts_df = self.getAccounts()
            for acct_name in cc_prv_acct__list:
                cc_prv_acct_row = accounts_df.iloc[accounts_df.Name.tolist().index(acct_name+": Prev Stmt Bal"),:]
                cc_curr_acct_row = accounts_df.iloc[accounts_df.Name.tolist().index(acct_name + ": Curr Stmt Bal"), :]

                try:
                    assert cc_prv_acct_row.Min_Balance == cc_curr_acct_row.Min_Balance
                    cc_combined_balance = cc_prv_acct_row.Balance + cc_curr_acct_row.Balance

                    try:
                        assert cc_combined_balance >= cc_prv_acct_row.Min_Balance
                    except:
                        value_error_text += 'Combined Prev and Curr Stmt bal was less than min_balance for account ' + str(acct_name) + "\n"
                        value_error_ind = True
                except:
                    value_error_text += 'Min_Balance did not match between Curr Stmt Bal and Prev Stmt Bal for account '+str(acct_name)+"\n"
                    value_error_ind = True

                try:
                    assert cc_prv_acct_row.Max_Balance == cc_curr_acct_row.Max_Balance
                    cc_combined_balance = cc_prv_acct_row.Balance + cc_curr_acct_row.Balance
                    try:
                        assert cc_combined_balance <= cc_prv_acct_row.Max_Balance
                    except:
                        value_error_text += 'Combined Prev and Curr Stmt bal was greater than max_balance for account ' + str(acct_name) + "\n"
                        value_error_ind = True
                except:
                    value_error_text += 'Max_Balance did not match between Curr Stmt Bal and Prev Stmt Bal for account '+str(acct_name)+"\n"
                    value_error_ind = True

            for acct_name in loan_pb_acct__list:
                loan_pb_acct_row = accounts_df.iloc[accounts_df.Name.tolist().index(acct_name + ": Principal Balance"),
                                  :]
                loan_interest_acct_row = accounts_df.iloc[accounts_df.Name.tolist().index(acct_name + ": Interest"),
                                   :]

                try:
                    assert loan_pb_acct_row.Min_Balance == loan_interest_acct_row.Min_Balance
                    cc_combined_balance = loan_pb_acct_row.Balance + loan_interest_acct_row.Balance
                    try:
                        assert cc_combined_balance >= loan_interest_acct_row.Min_Balance
                    except:
                        value_error_text += 'Combined Principal Balance and Interest bal was less than min_balance for account ' + str(acct_name) + "\n"
                        value_error_ind = True
                except:
                    value_error_text += 'Min_Balance did not match between Principal Balance and Interest for account ' + str(
                        acct_name) + "\n"
                    value_error_ind = True

                try:
                    assert loan_pb_acct_row.Max_Balance == loan_interest_acct_row.Max_Balance
                    cc_combined_balance = loan_pb_acct_row.Balance + loan_interest_acct_row.Balance
                    try:
                        assert cc_combined_balance <= loan_interest_acct_row.Max_Balance
                    except:
                        value_error_text += 'Combined Principal Balance and Interest bal was greater than max_balance for account ' + str(acct_name) + "\n"
                        value_error_ind = True
                except:
                    value_error_text += 'Max_Balance did not match between Principal Balance and Interest for account ' + str(
                        acct_name) + "\n"
                    value_error_ind = True




                # print('cc_prv_acct_row:')
                # print(cc_prv_acct_row)



            if print_debug_messages:
                if type_error_ind: print("TypeErrors:\n" + type_error_text)

                if value_error_ind: print("ValueErrors:\n" + value_error_text)

            if raise_exceptions:
                if type_error_ind:
                    raise TypeError

                if value_error_ind:
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
                   apr=None,
                   interest_cadence=None,
                   minimum_payment=None,
                   previous_statement_balance=None,
                   principal_balance=None,
                   accrued_interest=None,
                   print_debug_messages=True,
                   raise_exceptions=True
                   ):
        """
        Add an Account to list AccountSet.accounts. For credit and loan type accounts, previous statement balance and interest accounts are created.

        | Test Cases
        | Expected Successes
        | S1: add Checking #todo refactor AccountSet.addAccount() doctest S1 to use _S1 label
        | S2: add Savings #todo refactor AccountSet.addAccount() doctest S2 to use _S2 label
        | S3: add Credit #todo refactor AccountSet.addAccount() doctest S3 to use _S3 label
        | S4: add Loan #todo refactor AccountSet.addAccount() doctest S4 to use _S4 label
        |
        | Expected Fails
        | F1 add a second checking account  #todo refactor AccountSet.addAccount() doctest F1 to use _F1 label
        | F2 add an account with the same name as an existing account #todo refactor AccountSet.addAccount() doctest F2 to use _F2 label
        | F3: Savings - Prev Stmt Bal + Cur Stmt Bal violates account boundary #todo refactor AccountSet.addAccount() doctest F3 to use _F3 label
        | F4: Loan - Principal Balance + Interest != Balance #todo refactor AccountSet.addAccount() doctest F4 to use _F4 label
        |
        |
        """

        # TODO this should be based on interest type or interest AND account type
        if account_type.lower() == 'loan':

            if principal_balance is None:
                print('Prinicipal_Balance cannot be None for account_type=loan')
                raise ValueError

            if accrued_interest is None:
                print('Accrued_Interest cannot be None for account_type=loan')
                raise ValueError

            if principal_balance + accrued_interest != balance:
                print("Account.Principal_balance + Account.accrued_interest != Account.balance.\n")
                raise ValueError

            account = Account.Account(name=name + ': Principal Balance',
                                      balance=principal_balance,
                                      min_balance=min_balance,
                                      max_balance=max_balance,
                                      account_type='Principal Balance',
                                      billing_start_date_YYYYMMDD=billing_start_date_YYYYMMDD,
                                      interest_type=interest_type,
                                      apr=apr,
                                      interest_cadence=interest_cadence,
                                      minimum_payment=minimum_payment,
                                      previous_statement_balance=None,
                                      principal_balance=None,
                                      accrued_interest=None,
                                      print_debug_messages=print_debug_messages,
                                      raise_exceptions=raise_exceptions)
            self.accounts.append(account)

            account = Account.Account(name=name + ': Interest',
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
                                      raise_exceptions=raise_exceptions)
            self.accounts.append(account)

        elif account_type.lower() == 'credit':

            if previous_statement_balance is None:
                print('Previous_Statement_Balance cannot be None for account_type=loan')
                raise ValueError

            account = Account.Account(name=name + ': Curr Stmt Bal',
                                      balance=balance,
                                      min_balance=min_balance,
                                      max_balance=max_balance,
                                      account_type='Curr Stmt Bal',
                                      billing_start_date_YYYYMMDD=None,
                                      interest_type=None,
                                      apr=None,
                                      interest_cadence=None,
                                      minimum_payment=None,
                                      previous_statement_balance=None,
                                      principal_balance=None,
                                      accrued_interest=None,
                                      print_debug_messages=print_debug_messages,
                                      raise_exceptions=raise_exceptions)
            self.accounts.append(account)

            account = Account.Account(name=name + ': Prv Stmt Bal',
                                      balance=previous_statement_balance,
                                      min_balance=min_balance,
                                      max_balance=max_balance,
                                      account_type='Prv Stmt Bal',
                                      billing_start_date_YYYYMMDD=billing_start_date_YYYYMMDD,
                                      interest_type=interest_type,
                                      apr=apr,
                                      interest_cadence=interest_cadence,
                                      minimum_payment=minimum_payment,
                                      previous_statement_balance=None,
                                      principal_balance=None,
                                      accrued_interest=None,
                                      print_debug_messages=print_debug_messages,
                                      raise_exceptions=raise_exceptions)
            self.accounts.append(account)
        else:
            account = Account.Account(name=name,
                                      balance=balance,
                                      min_balance=min_balance,
                                      max_balance=max_balance,
                                      account_type=account_type,
                                      billing_start_date_YYYYMMDD=billing_start_date_YYYYMMDD,
                                      interest_type=interest_type,
                                      apr=apr,
                                      interest_cadence=interest_cadence,
                                      minimum_payment=minimum_payment,
                                      previous_statement_balance=previous_statement_balance,
                                      principal_balance=principal_balance,
                                      accrued_interest=accrued_interest,
                                      print_debug_messages=print_debug_messages,
                                      raise_exceptions=raise_exceptions)
            self.accounts.append(account)

    def getAccounts(self):
        """
        Get a DataFrame representing the AccountSet object.

        This test is failing even though this is indeed the result I get when I try this in the console.
        # >>> x=AccountSet().getAccounts()
        # Empty DataFrame
        # Columns: [Name, Balance, Previous_Statement_Balance, Min_Balance, Max_Balance, APR, Interest_Cadence, Interest_Type, Billing_Start_Dt, Account_Type, Principal_Balance, Accrued_Interest, Minimum_Payment]
        # Index: []

        >>> print(AccountSet([Account.Account(name='test',balance=0,min_balance=0,max_balance=0,account_type="checking")]).toJSON())
        {
        {
        "Name":"test",
        "Balance":"0.0",
        "Min_Balance":"0.0",
        "Max_Balance":"0.0",
        "Account_Type":"checking",
        "Billing_Start_Date":"None",
        "Interest_Type":"None",
        "APR":"None",
        "Interest_Cadence":"None",
        "Minimum_Payment":"None"
        }
        }
        """
        all_accounts_df = pd.DataFrame({'Name': [],
                                        'Balance': [],
                                        'Min_Balance': [],
                                        'Max_Balance': [],
                                        'Account_Type': [],
                                        'Billing_Start_Dt': [],
                                        'Interest_Type': [],
                                        'APR': [],
                                        'Interest_Cadence': [],
                                        'Minimum_Payment': []
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
                                               'Minimum_Payment': [account.minimum_payment]
                                               })

            all_accounts_df = pd.concat([all_accounts_df, new_account_row_df], axis=0)
            all_accounts_df.reset_index(drop=True, inplace=True)

        # if there are no accounts, I want to return a data frame with 0 rows

        return all_accounts_df

    def toJSON(self):
        """
        Get a JSON <string> representation of the <AccountSet> object.

        """

        JSON_string = "{\n"
        for i in range(0, len(self.accounts)):
            account = self.accounts[i]
            JSON_string += account.toJSON()
            if i + 1 != len(self.accounts):
                JSON_string += ","
            JSON_string += '\n'
        JSON_string += '}'

        return JSON_string

    # def fromJSON(self,JSON_string):
    #     pass


# written in one line so that test coverage can reach 100%
if __name__ == "__main__": import doctest; doctest.testmod()

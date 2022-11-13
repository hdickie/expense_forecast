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


        ######### Move these to another file when I can get it to count for test coverage ###########

        | Test Cases
        | Expected Successes
        |
        |
        | Expected Fails
        | [x] F1: Pass a list containing a non-Account object
        | [ ] F2: Missing related accounts
        | [ ] F3: Inconsistent account parameters: Min_Balance and Max_Balance
        | [ ] F4: Combined balance max account boundary violation
        | [ ] F5: Combined balance min account boundary violation

        Pass a list with an object that is not an Account object.
        This error never prints the error text even if you pass raise_exceptions = True
        The line that the exception is rasied from is close to the validation code that explains this so I am
        calling this good enough.
        >>> print(AccountSet([0]).toJSON()) #F1: Pass a list containing a non-Account object
        Traceback (most recent call last):
        ...
        ValueError


        >>> print(AccountSet([ #F2: Missing related accounts: credit
        ... Account.Account(name="Credit: Prev Stmt Bal",
        ... balance=75,
        ... min_balance=1,
        ... max_balance=101,
        ... apr=0.05,
        ... interest_cadence="Monthly",
        ... interest_type="Compound",
        ... billing_start_date_YYYYMMDD="20000101",
        ... account_type='Prev Stmt Bal',
        ... minimum_payment=40
        ... )],raise_exceptions=False).toJSON())
        Traceback (most recent call last):
        ...
        ValueError

        >>> print(AccountSet([ #F2: Missing related accounts: loan
        ... Account.Account(name="Loan: Interest",
        ... balance=75,
        ... min_balance=0,
        ... max_balance=100,
        ... apr=None,
        ... interest_cadence=None,
        ... interest_type=None,
        ... billing_start_date_YYYYMMDD=None,
        ... account_type='Interest',
        ... minimum_payment=None
        ... )],raise_exceptions=False).toJSON())
        Traceback (most recent call last):
        ...
        ValueError



        >>> print(AccountSet([ #F3: Inconsistent account parameters: Min_Balance and Max_Balance
        ... Account.Account(name="Credit: Curr Stmt Bal",
        ... balance=75,
        ... min_balance=0,
        ... max_balance=100,
        ... apr=None,
        ... interest_cadence=None,
        ... interest_type=None,
        ... billing_start_date_YYYYMMDD=None,
        ... account_type='Curr Stmt Bal',
        ... minimum_payment=None
        ... ),
        ... Account.Account(name="Credit: Prev Stmt Bal",
        ... balance=75,
        ... min_balance=1,
        ... max_balance=101,
        ... apr=0.05,
        ... interest_cadence="Monthly",
        ... interest_type="Compound",
        ... billing_start_date_YYYYMMDD="20000101",
        ... account_type='Prev Stmt Bal',
        ... minimum_payment=40
        ... ),Account.Account(name="Loan: Interest",
        ... balance=75,
        ... min_balance=0,
        ... max_balance=100,
        ... apr=None,
        ... interest_cadence=None,
        ... interest_type=None,
        ... billing_start_date_YYYYMMDD=None,
        ... account_type='Interest',
        ... minimum_payment=None
        ... ),
        ... Account.Account(name="Loan: Principal Balance",
        ... balance=75,
        ... min_balance=1,
        ... max_balance=101,
        ... apr=0.05,
        ... interest_cadence="Monthly",
        ... interest_type="Compound",
        ... billing_start_date_YYYYMMDD="20000101",
        ... account_type='Principal Balance',
        ... minimum_payment=40
        ... )],raise_exceptions=False).toJSON())
        ValueErrors:
        Min_Balance did not match between Curr Stmt Bal and Prev Stmt Bal for account Credit
        Max_Balance did not match between Curr Stmt Bal and Prev Stmt Bal for account Credit
        Min_Balance did not match between Principal Balance and Interest for account Loan
        Max_Balance did not match between Principal Balance and Interest for account Loan
        <BLANKLINE>
        {
        {
        "Name":"Credit: Curr Stmt Bal",
        "Balance":"75.0",
        "Min_Balance":"0.0",
        "Max_Balance":"100.0",
        "Account_Type":"Curr Stmt Bal",
        "Billing_Start_Date":"None",
        "Interest_Type":"None",
        "APR":"None",
        "Interest_Cadence":"None",
        "Minimum_Payment":"None"
        },
        {
        "Name":"Credit: Prev Stmt Bal",
        "Balance":"75.0",
        "Min_Balance":"1.0",
        "Max_Balance":"101.0",
        "Account_Type":"Prev Stmt Bal",
        "Billing_Start_Date":"2000-01-01 00:00:00",
        "Interest_Type":"Compound",
        "APR":"0.05",
        "Interest_Cadence":"Monthly",
        "Minimum_Payment":"40.0"
        },
        {
        "Name":"Loan: Interest",
        "Balance":"75.0",
        "Min_Balance":"0.0",
        "Max_Balance":"100.0",
        "Account_Type":"Interest",
        "Billing_Start_Date":"None",
        "Interest_Type":"None",
        "APR":"None",
        "Interest_Cadence":"None",
        "Minimum_Payment":"None"
        },
        {
        "Name":"Loan: Principal Balance",
        "Balance":"75.0",
        "Min_Balance":"1.0",
        "Max_Balance":"101.0",
        "Account_Type":"Principal Balance",
        "Billing_Start_Date":"2000-01-01 00:00:00",
        "Interest_Type":"Compound",
        "APR":"0.05",
        "Interest_Cadence":"Monthly",
        "Minimum_Payment":"40.0"
        }
        }


        >>> print(AccountSet( #F4: Combined balance max account boundary violation
        ... [Account.Account(name="Credit: Curr Stmt Bal",
        ... balance=75,
        ... min_balance=0,
        ... max_balance=100,
        ... apr=None,
        ... interest_cadence=None,
        ... interest_type=None,
        ... billing_start_date_YYYYMMDD=None,
        ... account_type='Curr Stmt Bal',
        ... minimum_payment=None
        ... ),
        ... Account.Account(name="Credit: Prev Stmt Bal",
        ... balance=75,
        ... min_balance=0,
        ... max_balance=100,
        ... apr=0.05,
        ... interest_cadence="Monthly",
        ... interest_type="Compound",
        ... billing_start_date_YYYYMMDD="20000101",
        ... account_type='Prev Stmt Bal',
        ... minimum_payment=40
        ... ),Account.Account(name="Loan: Interest",
        ... balance=75,
        ... min_balance=0,
        ... max_balance=100,
        ... apr=None,
        ... interest_cadence=None,
        ... interest_type=None,
        ... billing_start_date_YYYYMMDD=None,
        ... account_type='Interest',
        ... minimum_payment=None
        ... ),
        ... Account.Account(name="Loan: Principal Balance",
        ... balance=75,
        ... min_balance=0,
        ... max_balance=100,
        ... apr=0.05,
        ... interest_cadence="Monthly",
        ... interest_type="Compound",
        ... billing_start_date_YYYYMMDD="20000101",
        ... account_type='Principal Balance',
        ... minimum_payment=40
        ... )],raise_exceptions=False).toJSON())
        ValueErrors:
        Combined Prev and Curr Stmt bal was greater than max_balance for account Credit
        Combined Principal Balance and Interest bal was greater than max_balance for account Loan
        <BLANKLINE>
        {
        {
        "Name":"Credit: Curr Stmt Bal",
        "Balance":"75.0",
        "Min_Balance":"0.0",
        "Max_Balance":"100.0",
        "Account_Type":"Curr Stmt Bal",
        "Billing_Start_Date":"None",
        "Interest_Type":"None",
        "APR":"None",
        "Interest_Cadence":"None",
        "Minimum_Payment":"None"
        },
        {
        "Name":"Credit: Prev Stmt Bal",
        "Balance":"75.0",
        "Min_Balance":"0.0",
        "Max_Balance":"100.0",
        "Account_Type":"Prev Stmt Bal",
        "Billing_Start_Date":"2000-01-01 00:00:00",
        "Interest_Type":"Compound",
        "APR":"0.05",
        "Interest_Cadence":"Monthly",
        "Minimum_Payment":"40.0"
        },
        {
        "Name":"Loan: Interest",
        "Balance":"75.0",
        "Min_Balance":"0.0",
        "Max_Balance":"100.0",
        "Account_Type":"Interest",
        "Billing_Start_Date":"None",
        "Interest_Type":"None",
        "APR":"None",
        "Interest_Cadence":"None",
        "Minimum_Payment":"None"
        },
        {
        "Name":"Loan: Principal Balance",
        "Balance":"75.0",
        "Min_Balance":"0.0",
        "Max_Balance":"100.0",
        "Account_Type":"Principal Balance",
        "Billing_Start_Date":"2000-01-01 00:00:00",
        "Interest_Type":"Compound",
        "APR":"0.05",
        "Interest_Cadence":"Monthly",
        "Minimum_Payment":"40.0"
        }
        }


        >>> print(AccountSet( #F5: Combined balance min account boundary violation
        ... [Account.Account(name="Credit: Curr Stmt Bal",
        ... balance=-10,
        ... min_balance=-15,
        ... max_balance=100,
        ... apr=None,
        ... interest_cadence=None,
        ... interest_type=None,
        ... billing_start_date_YYYYMMDD=None,
        ... account_type='Curr Stmt Bal',
        ... minimum_payment=None
        ... ),
        ... Account.Account(name="Credit: Prev Stmt Bal",
        ... balance=-10,
        ... min_balance=-15,
        ... max_balance=100,
        ... apr=0.05,
        ... interest_cadence="Monthly",
        ... interest_type="Compound",
        ... billing_start_date_YYYYMMDD="20000101",
        ... account_type='Prev Stmt Bal',
        ... minimum_payment=40
        ... ),Account.Account(name="Loan: Interest",
        ... balance=-10,
        ... min_balance=-15,
        ... max_balance=100,
        ... apr=None,
        ... interest_cadence=None,
        ... interest_type=None,
        ... billing_start_date_YYYYMMDD=None,
        ... account_type='Interest',
        ... minimum_payment=None
        ... ),
        ... Account.Account(name="Loan: Principal Balance",
        ... balance=-10,
        ... min_balance=-15,
        ... max_balance=100,
        ... apr=0.05,
        ... interest_cadence="Monthly",
        ... interest_type="Compound",
        ... billing_start_date_YYYYMMDD="20000101",
        ... account_type='Principal Balance',
        ... minimum_payment=40
        ... )],raise_exceptions=False).toJSON())
        ValueErrors:
        Combined Prev and Curr Stmt bal was less than min_balance for account Credit
        Combined Principal Balance and Interest bal was less than min_balance for account Loan
        <BLANKLINE>
        {
        {
        "Name":"Credit: Curr Stmt Bal",
        "Balance":"-10.0",
        "Min_Balance":"-15.0",
        "Max_Balance":"100.0",
        "Account_Type":"Curr Stmt Bal",
        "Billing_Start_Date":"None",
        "Interest_Type":"None",
        "APR":"None",
        "Interest_Cadence":"None",
        "Minimum_Payment":"None"
        },
        {
        "Name":"Credit: Prev Stmt Bal",
        "Balance":"-10.0",
        "Min_Balance":"-15.0",
        "Max_Balance":"100.0",
        "Account_Type":"Prev Stmt Bal",
        "Billing_Start_Date":"2000-01-01 00:00:00",
        "Interest_Type":"Compound",
        "APR":"0.05",
        "Interest_Cadence":"Monthly",
        "Minimum_Payment":"40.0"
        },
        {
        "Name":"Loan: Interest",
        "Balance":"-10.0",
        "Min_Balance":"-15.0",
        "Max_Balance":"100.0",
        "Account_Type":"Interest",
        "Billing_Start_Date":"None",
        "Interest_Type":"None",
        "APR":"None",
        "Interest_Cadence":"None",
        "Minimum_Payment":"None"
        },
        {
        "Name":"Loan: Principal Balance",
        "Balance":"-10.0",
        "Min_Balance":"-15.0",
        "Max_Balance":"100.0",
        "Account_Type":"Principal Balance",
        "Billing_Start_Date":"2000-01-01 00:00:00",
        "Interest_Type":"Compound",
        "APR":"0.05",
        "Interest_Cadence":"Monthly",
        "Minimum_Payment":"40.0"
        }
        }

        ######################################
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

            required_attributes = ['name', 'balance', 'min_balance', 'max_balance', 'account_type',
                                   'billing_start_date',
                                   'interest_type', 'apr', 'interest_cadence', 'minimum_payment']

            for obj in self.accounts:
                if set(required_attributes) & set(dir(obj)) != set(required_attributes):
                    raise ValueError #An object in the input list did not have all the attributes an Account is expected to have.

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

            if (set(loan_pb_acct__list) & set(loan_interest_acct__list)) != set(loan_pb_acct__list) or \
                    (set(loan_pb_acct__list) & set(loan_interest_acct__list)) != set(loan_interest_acct__list):
                value_error_text += "The intersection of Principal Balance and Interest accounts was not equal to the union.\n"
                value_error_text += "loan_pb_acct__list:\n"
                value_error_text += str(loan_pb_acct__list) + "\n"
                value_error_text += 'loan_interest_acct__list:\n'
                value_error_text += str(loan_interest_acct__list) + "\n"
                value_error_ind = True
                raise ValueError #The intersection of Principal Balance and Interest accounts was not equal to the union.

            if set(cc_prv_acct__list) & set(cc_curr_acct__list) != set(cc_prv_acct__list) or \
                set(cc_prv_acct__list) & set(cc_curr_acct__list) != set(cc_curr_acct__list):
                value_error_text += "The intersection of Prev Stmt Bal and Curr Stmt Bal accounts was not equal to the union.\n"
                value_error_text += "cc_prv_acct__list:\n"
                value_error_text += str(cc_prv_acct__list) + "\n"
                value_error_text += 'cc_curr_acct__list:\n'
                value_error_text += str(cc_curr_acct__list) + "\n"
                value_error_ind = True
                raise ValueError #The intersection of Prev Stmt Bal and Curr Stmt Bal accounts was not equal to the union.

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
                if type_error_ind: raise TypeError

                if value_error_ind: raise ValueError

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
        | F1: add a second checking account  #todo refactor AccountSet.addAccount() doctest F1 to use _F1 label
        | F2: add an account with the same name as an existing account #todo refactor AccountSet.addAccount() doctest F2 to use _F2 label
        | F3: Savings - Prev Stmt Bal + Cur Stmt Bal violates account boundary #todo refactor AccountSet.addAccount() doctest F3 to use _F3 label
        | F4: Loan - Principal Balance + Interest != Balance #todo refactor AccountSet.addAccount() doctest F4 to use _F4 label
        |
        |
        """

        # TODO this should be based on interest type or interest AND account type
        if account_type.lower() == 'loan':

            if principal_balance is None:
                raise ValueError #Prinicipal_Balance cannot be None for account_type=loan

            if accrued_interest is None:
                raise ValueError #Accrued_Interest cannot be None for account_type=loan

            if principal_balance + accrued_interest != balance:
                raise ValueError #Account.Principal_balance + Account.accrued_interest != Account.balance

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
                                      print_debug_messages=print_debug_messages,
                                      raise_exceptions=raise_exceptions)
            self.accounts.append(account)

        elif account_type.lower() == 'credit':

            if previous_statement_balance is None:
                raise ValueError #Previous_Statement_Balance cannot be None for account_type=loan

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
                                      print_debug_messages=print_debug_messages,
                                      raise_exceptions=raise_exceptions)
            self.accounts.append(account)

            account = Account.Account(name=name + ': Prev Stmt Bal',
                                      balance=previous_statement_balance,
                                      min_balance=min_balance,
                                      max_balance=max_balance,
                                      account_type='Prev Stmt Bal',
                                      billing_start_date_YYYYMMDD=billing_start_date_YYYYMMDD,
                                      interest_type=interest_type,
                                      apr=apr,
                                      interest_cadence=interest_cadence,
                                      minimum_payment=minimum_payment,
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

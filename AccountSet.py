import Account, pandas as pd
import copy
from log_methods import log_in_color

class AccountSet:

    #TODO passing this without arguments caused accounts__list to get values from some older scope. Therefore, AccountSet() doesn't work as expected.
    # (I expected the default parameter defined below to be used!)
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
        #print('enter AccountSet()')

        value_error_text = ""
        value_error_ind = False

        type_error_text = ""
        type_error_ind = False

        # IMPORTANT NOTE: the previous statement balance and interest accounts should be the index after
        # im sure there is a fancier/smarter design but the logic I have implemented in ExpenseForecast assumes this

        #print('BEFORE accounts__list:' + str(accounts__list))
        self.accounts = accounts__list
        #print('AFTER  accounts__list:'+str(accounts__list))

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
                accounts_df.Account_Type.isin(['principal balance', 'interest']), 'Name']
            cc_check__name__series = accounts_df.loc[
                accounts_df.Account_Type.isin(['prev stmt bal', 'curr stmt bal']), 'Name']

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

            if print_debug_messages:
                if type_error_ind: print("TypeErrors:\n" + type_error_text)

                if value_error_ind: print("ValueErrors:\n" + value_error_text)

            if raise_exceptions:
                if type_error_ind: raise TypeError

                if value_error_ind: raise ValueError
        #print('exit AccountSet()')

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

        #todo implement test: for each account with interest_type == 'Simple', there should be principal balance and an interest acct
        # this check has been implemented by account_type, but not by interest_type
        # for each account with interest_type == 'Compound', there should be prev bal and curr bal accts
        # i am 100% not mad about redundancy here
        """

        log_string='addAccount(name='+str(name)+',balance='+str(balance)+',account_type='+str(account_type)
        if account_type == 'checking':
            pass
        elif account_type == 'credit':
            log_string+=',billing_start_date_YYYYMMDD='+str(billing_start_date_YYYYMMDD)+',apr='+str(apr)+',previous_statement_balance='+str(previous_statement_balance)
        elif account_type == 'loan':
            log_string+=',billing_start_date_YYYYMMDD='+str(billing_start_date_YYYYMMDD)+',apr='+str(apr)+',principal_balance='+str(principal_balance)+',accrued_interest='+str(accrued_interest)
        else:
            pass
        log_string+=')'
        log_in_color('green', 'debug',log_string, 0)

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
                                      account_type='principal balance',
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
                                      account_type='interest',
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
                raise ValueError #Previous_Statement_Balance cannot be None for account_type=credit

            account = Account.Account(name=name + ': Curr Stmt Bal',
                                      balance=balance,
                                      min_balance=min_balance,
                                      max_balance=max_balance,
                                      account_type='curr stmt bal',
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
                                      account_type='prev stmt bal',
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

    def getAvailableBalances(self):

        balances_dict = {}
        for i in range(0,len(self.accounts)):
            a = self.accounts[i]
            if a.account_type == 'checking':
                balances_dict[a.name] = a.balance
            elif a.account_type == 'prev stmt bal':
                prev_balance = a.balance
                curr_balance = self.accounts[i-1].balance

                remaining_prev_balance = a.max_balance - ( prev_balance + curr_balance )
                balances_dict[a.name.split(':')[0]] = remaining_prev_balance
            else:
                pass
                #raise NotImplementedError
        return balances_dict

    def executeTransaction(self, Account_From, Account_To, Amount,income_flag=False):

        if Amount == 0:
            return None

        boundary_error_ind = False
        equivalent_exchange_error_ind = False

        debug_print__AF=Account_From
        debug_print__AT=Account_To
        debug_print_Amount=str(Amount)

        if Account_From is None:
            debug_print__AF = 'None'

        if Account_To is None:
            debug_print__AT = 'None'
        log_in_color('green', 'debug','executeTransaction(Account_From='+debug_print__AF+', Account_To='+debug_print__AT+', Amount='+debug_print_Amount+')', 2)

        before_txn_total_available_funds = 0
        available_funds = self.getAvailableBalances()

        log_in_color('magenta', 'error', 'available_funds:'+str(available_funds),3)

        for a in available_funds.keys():
            before_txn_total_available_funds += available_funds[a]

        #determine account type. there will be 1 or 2 matches depending on account type. 1 => no interest , 2 => interest
        account_base_names = [ x.split(':')[0] for x in self.getAccounts().Name ]
        #print('self.getAccounts().Name:'+str(self.getAccounts().Name))
        #print('account_base_names:'+str(account_base_names))
        if Account_From is not None:
            if Account_From != '' and Account_From != 'None':
                AF_base_name_match_count = account_base_names.count(Account_From)
                account_from_index = account_base_names.index(Account_From)  # first match found. for credit, first will be current stmt bal, second will be prev
                if AF_base_name_match_count == 2:
                    if self.accounts[account_from_index].account_type == 'curr stmt bal':
                        AF_Account_Type = 'credit'
                    elif self.accounts[account_from_index].account_type == 'principal balance':
                        AF_Account_Type = 'loan'
                    elif self.accounts[account_from_index].account_type == 'checking':
                        AF_Account_Type = 'checking'
                elif AF_base_name_match_count == 1:
                    AF_Account_Type = self.accounts[account_from_index].account_type
                else:
                    raise ValueError #if this happens, then validation in ExpenseForecast constructor failed to catch something
                #AT_base_name_match_count = account_base_names.count(Account_To)

        if Account_To is not None:
            if Account_To != '' and Account_To != 'None':
                AT_base_name_match_count = account_base_names.count(Account_To)
                account_to_index = account_base_names.index(Account_To)  # first match found. for credit, first will be current stmt bal, second will be prev
                if AT_base_name_match_count == 2:
                    if self.accounts[account_to_index].account_type == 'curr stmt bal':
                        AT_Account_Type = 'credit'
                    elif self.accounts[account_to_index].account_type == 'principal balance':
                        AT_Account_Type = 'loan'
                    elif self.accounts[account_to_index].account_type == 'checking':
                        AT_Account_Type = 'checking'
                elif AT_base_name_match_count == 1:
                    AT_Account_Type = self.accounts[account_to_index].account_type
                else:
                    raise ValueError #if this happens, then validation in ExpenseForecast constructor failed to catch something

        if Account_From is not None:
            if Account_From != '' and Account_From != 'None':
                if AF_Account_Type == 'checking':

                    balance_after_proposed_transaction = self.accounts[account_from_index].balance - abs(Amount)
                    try:
                        assert self.accounts[account_from_index].min_balance <= balance_after_proposed_transaction and self.accounts[account_from_index].max_balance
                    except Exception as e:
                        log_in_color('red','error','transaction violated Account_From boundaries:')
                        log_in_color('red', 'error', str(e))
                        log_in_color('red', 'error', 'Account_From:\n'+str(self.accounts[account_from_index]))
                        log_in_color('red', 'error', 'Amount:'+str(Amount))
                        boundary_error_ind = True

                    self.accounts[account_from_index].balance -= abs(Amount)
                elif AF_Account_Type == 'credit' or AF_Account_Type == 'loan':

                    balance_after_proposed_transaction = self.accounts[account_from_index].balance + abs(Amount)
                    try:
                        assert self.accounts[account_from_index].min_balance <= balance_after_proposed_transaction and \
                               self.accounts[account_from_index].max_balance
                    except Exception as e:
                        log_in_color('red', 'error', 'transaction violated Account_From boundaries:')
                        log_in_color('red', 'error', str(e))
                        log_in_color('red', 'error', 'Account_From:\n' + str(self.accounts[account_from_index]))
                        log_in_color('red', 'error', 'Amount:' + str(Amount))
                        boundary_error_ind = True

                    self.accounts[account_from_index].balance += abs(Amount)
                else:
                    raise NotImplementedError #from types other than checking or credit not yet implemented
                log_in_color('magenta', 'debug', 'Paid ' + str(Amount) + ' from ' + Account_From, 3)



        if Account_To is not None:
            if Account_To != '' and Account_To != 'None':
                if AT_Account_Type == 'checking':

                    self.accounts[account_to_index].balance += abs(Amount)
                    log_in_color('magenta', 'debug', 'Paid ' + str(Amount) + ' to ' + Account_To, 3)
                elif AT_Account_Type == 'credit' or AT_Account_Type == 'loan':
                    #if the amount we are playing on credit card is more than the previous statement balance
                    if abs(Amount) >= self.accounts[account_to_index+1].balance:
                        remaining_to_pay = abs(Amount) - self.accounts[account_to_index + 1].balance
                        self.accounts[account_to_index + 1].balance = 0
                        log_in_color('magenta', 'debug','Paid ' + str(self.accounts[account_to_index + 1].balance) + ' to ' + str(self.accounts[account_to_index + 1].name), 3)


                        #this has the potential to overpay, but we consider that upstreams problem
                        self.accounts[account_to_index].balance -= remaining_to_pay
                        log_in_color('magenta', 'debug', 'Paid ' + str(remaining_to_pay) + ' to ' + self.accounts[account_to_index].name, 3)
                    else: #pay down the previous statement balance
                        log_in_color('magenta', 'debug', 'Paid ' + str(Amount) + ' to ' + str(self.accounts[account_to_index + 1].name), 3)
                        self.accounts[account_to_index + 1].balance -= Amount
                else:
                    raise NotImplementedError #from types other than checking or credit not yet implemented

        after_txn_total_available_funds = 0
        available_funds = self.getAvailableBalances()
        for a in available_funds.keys():
            after_txn_total_available_funds += available_funds[a]

        empirical_delta = before_txn_total_available_funds - after_txn_total_available_funds

        if income_flag:
            empirical_delta = empirical_delta * -1

        if round(empirical_delta,2) != round(Amount,2) and Account_From is not None and Account_To is not None:
            equivalent_exchange_error_ind = True

        if boundary_error_ind:
            raise ValueError #Account boundaries were violated

        if equivalent_exchange_error_ind:
            log_in_color('red', 'error', 'FUNDS NOT ACCOUNTED FOR POST-TRANSACTION',3)
            log_in_color('red', 'error', 'income_flag:'+str(income_flag), 3)
            available_funds = self.getAvailableBalances()
            log_in_color('red', 'error', 'available_funds:' + str(available_funds), 3)
            log_in_color('red', 'error', '( SUM(before txn balances) - SUM(after txn balances) ) != 0',3)
            log_in_color('red', 'error', str(before_txn_total_available_funds) + ' - ' + str(after_txn_total_available_funds) + ' = ' + str(empirical_delta) + ' !== ' + str(Amount) ,3)
            # log_in_color('red', 'error', 'before_txn_total_available_funds:'+str(before_txn_total_available_funds), 3)
            # log_in_color('red', 'error', 'after_txn_total_available_funds:'+str(after_txn_total_available_funds), 3)
            # log_in_color('red', 'error', 'empirical_delta:'+str(empirical_delta), 3)
            # log_in_color('red', 'error', 'Amount:'+str(Amount), 3)


            raise ValueError # ( SUM(before txn balances) - SUM(after txn balances) ) != Amount

    def transaction_would_violate_account_boundaries(self,account_from_name,account_to_name,amount,income_flag=False):

        if amount == 0:
            return False

        copy_of_this_account_set = copy.deepcopy(self)
        copy_of_this_account_set.executeTransaction(account_from_name,account_to_name,amount,income_flag)
        account_info = copy_of_this_account_set.getAccounts()
        illegal_state_rows = account_info[(account_info.Balance < account_info.Min_Balance) | (account_info.Balance > account_info.Max_Balance)]

        if illegal_state_rows.shape[0] > 0:
            print('illegal_state_rows:')
            print(illegal_state_rows.to_string())

        return illegal_state_rows.shape[0] > 0


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

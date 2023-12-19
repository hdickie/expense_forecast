import Account, pandas as pd
import copy
from log_methods import log_in_color
import logging
import numpy as np

import BudgetSet #this could be refactored out, and should be in terms of independent dependencies and clear organization, but it works
import BudgetItem

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

class AccountSet:

    #TODO passing this without arguments caused accounts__list to get values from some older scope. Therefore, AccountSet() doesn't work as expected.
    # (I expected the default parameter defined below to be used!)
    def __init__(self, accounts__list, print_debug_messages=True, raise_exceptions=True):
        """
        Creates an AccountSet object. Possible Account Types are: Checking, Credit, Loan, Savings. Consistency is checked.

        :param list accounts__list: A list of Account objects. Empty list by default. Consistency is checked.
        :raises ValueError: if the combination of input parameters is not valid.
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
        if accounts__list is None:
            accounts__list = []
            self.accounts = accounts__list
            return

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
                    #print(self.accounts)
                    raise ValueError("An object in the input list did not have all the attributes an Account is expected to have.") #An object in the input list did not have all the attributes an Account is expected to have.

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
                raise ValueError("The intersection of Principal Balance and Interest accounts was not equal to the union.") #The intersection of Principal Balance and Interest accounts was not equal to the union.

            if set(cc_prv_acct__list) & set(cc_curr_acct__list) != set(cc_prv_acct__list) or \
                set(cc_prv_acct__list) & set(cc_curr_acct__list) != set(cc_curr_acct__list):
                value_error_text += "The intersection of Prev Stmt Bal and Curr Stmt Bal accounts was not equal to the union.\n"
                value_error_text += "cc_prv_acct__list:\n"
                value_error_text += str(cc_prv_acct__list) + "\n"
                value_error_text += 'cc_curr_acct__list:\n'
                value_error_text += str(cc_curr_acct__list) + "\n"
                value_error_ind = True
                raise ValueError("The intersection of Prev Stmt Bal and Curr Stmt Bal accounts was not equal to the union.") #The intersection of Prev Stmt Bal and Curr Stmt Bal accounts was not equal to the union.

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
        return self.to_json()

    def __repr__(self):
        return self.to_json()

    def addAccount(self,list_of_accounts):
        #todo check a multiple is not being created
        #check that prev has a curr, and princ has an interest
        #check not receiving too many accounts
        #check not empty
        self.accounts += list_of_accounts

    def createAccount(self,
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

        #todo disallow adding a second checking account

        log_string='createAccount(name='+str(name)+',balance='+str(balance)+',account_type='+str(account_type)
        if account_type == 'checking':
            pass
        elif account_type == 'credit':
            log_string+=',billing_start_date_YYYYMMDD='+str(billing_start_date_YYYYMMDD)+',apr='+str(apr)+',previous_statement_balance='+str(previous_statement_balance)
        elif account_type == 'loan':
            log_string+=',billing_start_date_YYYYMMDD='+str(billing_start_date_YYYYMMDD)+',apr='+str(apr)+',principal_balance='+str(principal_balance)+',accrued_interest='+str(accrued_interest)

        log_string+=')'
        log_in_color('green', 'info',log_string, 0)

        if billing_start_date_YYYYMMDD is None:
            billing_start_date_YYYYMMDD = "None"

        if interest_type is None:
            interest_type = "None"

        if apr is None:
            apr = "None"

        if interest_cadence is None:
            interest_cadence = "None"

        if minimum_payment is None:
            minimum_payment = "None"

        if previous_statement_balance is None:
            previous_statement_balance = "None"

        if principal_balance is None:
            principal_balance = "None"

        if accrued_interest is None:
            accrued_interest = "None"

        # TODO this should be based on interest type or interest AND account type
        if account_type.lower() == 'loan':

            if principal_balance == 'None':
                raise ValueError #Prinicipal_Balance cannot be None for account_type=loan

            if accrued_interest == 'None':
                raise ValueError #Accrued_Interest cannot be None for account_type=loan

            if float(principal_balance) + float(accrued_interest) != float(balance):
                raise ValueError(name+": "+str(principal_balance)+" + "+str(accrued_interest)+" != "+str(balance)) #Account.Principal_balance + Account.accrued_interest != Account.balance

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

            if previous_statement_balance == 'None':
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

    def getBalances(self):
        #log_in_color('magenta','debug','ENTER getBalances()')
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

            elif a.account_type == 'principal balance':
                principal_balance = a.balance
                interest_balance = self.accounts[i+1].balance
                balances_dict[a.name.split(':')[0]] = ( principal_balance + interest_balance )
            else:
                #log_in_color('magenta', 'debug', 'Unexpected account type: '+str(a.account_type))
                pass
        #     print('balances_dict:')
        #     print(balances_dict)
        # log_in_color('magenta', 'debug', balances_dict)
        # log_in_color('magenta', 'debug', 'EXIT getBalances()')
        return balances_dict

    def executeTransaction(self, Account_From, Account_To, Amount,income_flag=False):

        Amount = round(Amount,2)

        if Amount == 0:
            return

        if Account_To == 'ALL_LOANS':
            loan_payment__list = self.allocate_additional_loan_payments(Amount)
            for i in range(0,len(loan_payment__list)):
                single_account_loan_payment = loan_payment__list[i]
                self.executeTransaction(single_account_loan_payment[0], #From
                                        single_account_loan_payment[1], #To
                                        single_account_loan_payment[2], #Amount
                                        income_flag=False)
            return

        boundary_error_ind = False
        equivalent_exchange_error_ind = False
        debug_print_Amount=str(Amount)
        debt_payment_ind = False

        if Account_From is None:
            Account_From = 'None'
            AF_Account_Type = 'None'

        if Account_To is None:
            Account_To = 'None'
            AT_Account_Type = 'None'

        #log_in_color('green', 'debug','executeTransaction(Account_From='+Account_From+', Account_To='+Account_To+', Amount='+debug_print_Amount+')')
        #print('executeTransaction(Account_From=' + str(Account_From) + ', Account_To=' + str(Account_To) + ', Amount=' + str(debug_print_Amount) + ')')

        before_txn_total_available_funds = 0
        available_funds = self.getBalances()
        starting_available_funds = copy.deepcopy(available_funds)

        log_in_color('magenta', 'debug', 'available_funds:'+str(available_funds))

        for a in available_funds.keys():
            before_txn_total_available_funds += available_funds[a]

        #determine account type. there will be 1 or 2 matches depending on account type. 1 => no interest , 2 => interest
        account_base_names = [ x.split(':')[0] for x in self.getAccounts().Name ]
        #print('self.getAccounts().Name:'+str(self.getAccounts().Name))
        #print('account_base_names:'+str(account_base_names))

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

        #at this point, we know account types but haven't changed any balances
        #if income, one account must be checking, and the other must be none
        if income_flag and AF_Account_Type == 'checking' and AT_Account_Type == 'None':
            pass #cool
        elif income_flag and AF_Account_Type == 'None' and AT_Account_Type == 'checking':
            pass #cool
        elif income_flag:
            #not cool
            raise ValueError("income_flag was True but did not refer to a checking account or referred to multiple accounts")


        if Account_From != '' and Account_From != 'None':
            if AF_Account_Type == 'checking':

                balance_after_proposed_transaction = self.accounts[account_from_index].balance - abs(Amount)
                try:
                    assert self.accounts[account_from_index].min_balance <= balance_after_proposed_transaction <= self.accounts[account_from_index].max_balance
                except Exception as e:
                    log_in_color('red', 'error', '')
                    log_in_color('red','error','transaction violated Account_From boundaries:')
                    log_in_color('red', 'error', str(e))
                    log_in_color('red', 'error', 'Account_From:\n'+str(self.accounts[account_from_index]))
                    log_in_color('red', 'error', 'Amount:'+str(Amount))
                    boundary_error_ind = True

                self.accounts[account_from_index].balance -= abs(Amount)
            elif AF_Account_Type == 'credit' or AF_Account_Type == 'loan':

                balance_after_proposed_transaction = self.getBalances()[self.accounts[account_from_index].name.split(':')[0]] - abs(Amount)
                #this check assumes that both prev and curr accounts for credit have the same bounds

                # log_in_color('magenta', 'debug', 'account min:' + str(self.accounts[account_from_index].min_balance), 3)
                # log_in_color('magenta', 'debug', 'account max:' + str(self.accounts[account_from_index].max_balance), 3)
                # log_in_color('magenta', 'debug', 'balance_after_proposed_transaction:' + str(balance_after_proposed_transaction), 3)

                try:
                    assert self.accounts[account_from_index].min_balance <= balance_after_proposed_transaction <= self.accounts[account_from_index].max_balance
                except Exception as e:
                    log_in_color('red', 'error', 'transaction violated Account_From boundaries:')
                    log_in_color('red', 'error', str(e))
                    log_in_color('red', 'error', 'Account_From:\n' + str(self.accounts[account_from_index]))
                    log_in_color('red', 'error', 'Amount:' + str(Amount))
                    boundary_error_ind = True

                self.accounts[account_from_index].balance += abs(Amount)
            else:
                raise NotImplementedError #from types other than checking or credit not yet implemented

            if not boundary_error_ind:
                log_in_color('magenta', 'debug', 'Paid ' + str(Amount) + ' from ' + Account_From, 0)



        if Account_To != '' and Account_To != 'None' and (not boundary_error_ind):
            if AT_Account_Type == 'checking':

                self.accounts[account_to_index].balance += abs(Amount)
                log_in_color('magenta', 'debug', 'Paid ' + str(Amount) + ' to ' + Account_To, 0)
            elif AT_Account_Type == 'credit' or AT_Account_Type == 'loan':

                debt_payment_ind = (AT_Account_Type.lower() == 'loan')

                AT_ANAME = self.accounts[account_to_index].name.split(':')[0]
                balance_after_proposed_transaction = self.getBalances()[AT_ANAME] - abs(Amount)

                try:
                    #print('assert '+str(self.accounts[account_to_index].min_balance)+' <= '+str(balance_after_proposed_transaction)+' <= '+str(self.accounts[account_to_index].max_balance))
                    assert self.accounts[account_to_index].min_balance <= balance_after_proposed_transaction <= self.accounts[account_to_index].max_balance
                except Exception as e:
                    log_in_color('red', 'error', '')
                    log_in_color('red','error','transaction violated Account_To boundaries:')
                    log_in_color('red', 'error', str(e))
                    log_in_color('red', 'error', 'Account_To:\n'+str(self.accounts[account_to_index]))
                    log_in_color('red', 'error', 'Amount:'+str(Amount))
                    boundary_error_ind = True

                # log_in_color('magenta', 'debug', 'account min:' + str(self.accounts[account_to_index].min_balance), 3)
                # log_in_color('magenta', 'debug', 'account max:' + str(self.accounts[account_to_index].max_balance), 3)
                # log_in_color('magenta', 'debug', 'balance_after_proposed_transaction:' + str(balance_after_proposed_transaction), 3)

                #if the amount we are playing on credit card is more than the previous statement balance
                if abs(Amount) >= self.accounts[account_to_index+1].balance:
                    remaining_to_pay = abs(Amount) - self.accounts[account_to_index + 1].balance
                    log_in_color('magenta', 'debug','Paid ' + str(self.accounts[account_to_index + 1].balance) + ' to ' + str(self.accounts[account_to_index + 1].name), 0)
                    self.accounts[account_to_index + 1].balance = 0

                    #this has the potential to overpay, but we consider that upstreams problem
                    self.accounts[account_to_index].balance -= remaining_to_pay
                    log_in_color('magenta', 'debug', 'Paid ' + str(remaining_to_pay) + ' to ' + self.accounts[account_to_index].name, 0)
                else: #pay down the previous statement balance
                    log_in_color('magenta', 'debug', 'Paid ' + str(Amount) + ' to ' + str(self.accounts[account_to_index + 1].name), 0)
                    self.accounts[account_to_index + 1].balance -= Amount
            else:
                raise NotImplementedError #from types other than checking or credit not yet implemented

        after_txn_total_available_funds = 0
        available_funds = self.getBalances()
        for a in available_funds.keys():
            after_txn_total_available_funds += available_funds[a]

        empirical_delta = round(after_txn_total_available_funds - before_txn_total_available_funds,2)

        if boundary_error_ind: raise ValueError("Account boundaries were violated")

        single_account_transaction_ind = ( Account_From == 'None' or Account_To == 'None' )


        if single_account_transaction_ind and income_flag:
            if empirical_delta != Amount: equivalent_exchange_error_ind = True
        elif not single_account_transaction_ind and debt_payment_ind:
            if empirical_delta != (Amount * -2): equivalent_exchange_error_ind = True
        elif single_account_transaction_ind and not income_flag:
            if empirical_delta != (Amount * -1): equivalent_exchange_error_ind = True
        elif not single_account_transaction_ind and not income_flag:
            if empirical_delta != 0: equivalent_exchange_error_ind = True
        else: equivalent_exchange_error_ind = True
            #raise ValueError("impossible error in  AccountSet::executeTransaction(). if 2 accounts were indicated, then the pre-post delta must be 0.") #this should not be possible.

        if equivalent_exchange_error_ind:
            log_in_color('red', 'error', '', 0)
            log_in_color('red', 'error', 'FUNDS NOT ACCOUNTED FOR POST-TRANSACTION', 0)
            log_in_color('red', 'error', 'single_account_transaction_ind:'+str(single_account_transaction_ind),0)
            log_in_color('red', 'error', 'income_flag:' + str(income_flag), 0)
            log_in_color('red', 'error', 'debt_payment_ind:' + str(debt_payment_ind), 0)
            log_in_color('red', 'error', 'starting_available_funds:' + str(starting_available_funds), 0)
            log_in_color('red', 'error', 'available_funds:' + str(self.getBalances()), 0)
            log_in_color('red', 'error', 'Amount:' + str(Amount), 0)
            log_in_color('red', 'error', 'empirical_delta:' + str(empirical_delta), 0)
            raise ValueError("Funds not accounted for in AccountSet::executeTransaction()") # Funds not accounted for


    def fromExcel(self):
        raise NotImplementedError

    def allocate_additional_loan_payments(self, amount):
        bal_string = ''
        for account_index, account_row in self.getAccounts().iterrows():
            bal_string += '$' + str(account_row.Balance) + ' '

        log_in_color('green','debug','ENTER allocate_additional_loan_payments(amount='+str(amount)+') '+bal_string)

        row_sel_vec = [ x for x in ( self.getAccounts().Account_Type == 'checking' ) ]
        checking_acct_name = self.getAccounts()[row_sel_vec].Name[0] #we use this waaay later during executeTransaction
        if self.getAccounts()[row_sel_vec].Balance.iat[0] < amount:
            log_in_color('green', 'debug', 'input amount is greater than available balance. Reducing amount.')
            amount = self.getAccounts().loc[row_sel_vec,:].Balance.iat[0]

        date_string_YYYYMMDD = '20000101' #this method needs to be refactored

        account_set = copy.deepcopy(self)

        A = account_set.getAccounts()
        principal_accts_df = A[A.Account_Type == 'principal balance']

        principal_accts_df['Marginal Interest Amount'] = principal_accts_df.Balance * principal_accts_df.APR
        principal_accts_df['Marginal Interest Rank'] = principal_accts_df['Marginal Interest Amount'].rank(method='dense', ascending=False)

        number_of_phase_space_regions = max(principal_accts_df['Marginal Interest Rank'])
        # log_in_color('yellow', 'debug','Explanation of the loan payment algorithm:')
        # log_in_color('yellow', 'debug', 'FACT 1: The optimal loan payment pays the loan with the highest marginal interest first.')
        # log_in_color('yellow', 'debug','FACT 2: If two loans have different balances and APRs, but will accrue the same amount of additional interest the next day, then it is at this point that we begin to split our next dollar between the two loans in proportion to the APR.')
        # log_in_color('yellow', 'debug','We would know that our allocation is optimal when the marginal interest for both loans stays the same.')
        # log_in_color('yellow', 'debug','Then we will reach a point where we are splitting our next dollar between two loans, then three... (assuming there are this many loans)')
        # log_in_color('yellow', 'debug','This algorithm finds these points to allocate payment.')
        # log_in_color('yellow', 'debug', 'If you plot this on a graph, the behavior changes when a new loan joins the group that is being paid proportionally. The space between these points is referred to as a phase space region.')
        # log_in_color('yellow', 'debug',
        #              'The following table shows the order in which loans will be paid. Marginal Interest Rank 1 will be paid until the Marginal Interest Amount is equal to the account with Marginal Interest Rank 2, etc.')
        # print(principal_accts_df.loc[:,('Name','Balance','Marginal Interest Amount','Marginal Interest Rank')].to_string())

        #log_in_color('yellow', 'debug', 'number_of_phase_space_regions:'+str(number_of_phase_space_regions))
        # print('number_of_phase_space_regions:'+str(number_of_phase_space_regions))

        all_account_names__1 = [x.split(':') for x in principal_accts_df.Name]
        all_account_names__2 = [name for sublist in all_account_names__1 for name in sublist]
        all_account_names = set(all_account_names__2) - set([' Principal Balance'])

        payment_amounts__BudgetSet = BudgetSet.BudgetSet([])

        for i in range(0, int(number_of_phase_space_regions)):

            if amount == 0:
                break

            log_in_color('yellow', 'debug','Phase space region index: '+str(i))
            A = account_set.getAccounts()
            #print('A:\n')
            #print(A.to_string())

            principal_accts_df = A[A.Account_Type == 'principal balance']
            interest_accts_df = A[A.Account_Type == 'interest']

            total_amount_per_loan = {}
            for acct_name in all_account_names:
                principal_amt = principal_accts_df.iloc[[acct_name in pa_element for pa_element in principal_accts_df.Name], :].Balance.iloc[0]
                interest_amt = interest_accts_df.iloc[[acct_name in pa_element for pa_element in interest_accts_df.Name], :].Balance.iloc[0]

                total_amount_per_loan[acct_name] = principal_amt + interest_amt

            # Let P0 be initial principal
            # Let M0 be initial marginal_interst
            # Let R be vector of APRs
            #then, P0 * R = M0

            #Assume the case where there are 2 loans
            #The principal balances at the beginning of the next phase space region corresponds to
            # P1 * R = M1
            #where both entries in M1 are the same, and correspond to the lower of the two marginal interest amounts
            #therefore, we calculate the maximum amount we are able to pay until the payment strategy must change as
            # P1 = M1 * R^-1
            # this is equivalent to taking the next desired state of marginal interest amounts and right multiplying by a vector of the reciprocal rates

            P = np.matrix(principal_accts_df.Balance)
            r = np.matrix(principal_accts_df.APR)
            P_dot_r = P.T.dot(r) #this represents marginal interest

            reciprocal_rates = []
            for i in range(0, P.shape[1]):
                reciprocal_rates.append(1 / r[0, i])
            reciprocal_rates = np.matrix(reciprocal_rates)
            # print('reciprocal_rates:')
            # print(reciprocal_rates.shape)
            # print(reciprocal_rates)

            #print('P_dot_r:')
            #print(np.matrix(P_dot_r))

            marginal_interest_amounts__list = []
            for i in range(0, P.shape[1]):
                marginal_interest_amounts__list.append(round(P_dot_r[i, i], 2))
            # print(marginal_interest_amounts__list)
            marginal_interest_amounts__matrix = np.matrix(marginal_interest_amounts__list)
            #print('marginal_interest_amounts__matrix:')
            #print(marginal_interest_amounts__matrix)
            marginal_interest_amounts_df = pd.DataFrame(marginal_interest_amounts__list)
            marginal_interest_amounts_df.columns = ['Marginal Interest Amount']
            marginal_interest_amounts_df['Marginal Interest Rank'] = marginal_interest_amounts_df['Marginal Interest Amount'].rank(method='dense', ascending=False)
            #print('marginal_interest_amounts_df:')
            #print(marginal_interest_amounts_df)

            try:
                next_lowest_marginal_interest_amount = marginal_interest_amounts_df[marginal_interest_amounts_df['Marginal Interest Rank'] == 2].iloc[0, 0]
            except Exception as e:
                next_lowest_marginal_interest_amount = 0
            #print('next_lowest_marginal_interest_amount:')
            #print(next_lowest_marginal_interest_amount)
            marginal_interest_amounts_df__c = copy.deepcopy(marginal_interest_amounts_df)

            # print('marginal_interest_amounts_df__c[marginal_interest_amounts_df__c[Marginal Interest Rank] == 1]')
            # print(marginal_interest_amounts_df__c['Marginal Interest Rank'] == 1)
            # print(marginal_interest_amounts_df__c[marginal_interest_amounts_df__c['Marginal Interest Rank'] == 1])
            # print(marginal_interest_amounts_df__c[marginal_interest_amounts_df__c['Marginal Interest Rank'] == 1]['Marginal Interest Amount'])

            marginal_interest_amounts_df__c.loc[
                marginal_interest_amounts_df__c['Marginal Interest Rank'] == 1, marginal_interest_amounts_df__c.columns == 'Marginal Interest Amount'] = next_lowest_marginal_interest_amount
            next_step_marginal_interest_vector = np.matrix(marginal_interest_amounts_df__c['Marginal Interest Amount']) #this corresponds to the M1 vector
            #print('next_step_marginal_interest_vector:\n')
            #print(next_step_marginal_interest_vector)

            #todo include interest in these amounts
            current_principal_balance_state = P
            #print('current_state:' + str(current_state))
            #print('total_amount_per_loan:'+str(total_amount_per_loan))

            A = account_set.getAccounts()

            #print('current_state:\n'+str(current_state))

            #print('next_step_marginal_interest_vector:')
            #print(next_step_marginal_interest_vector)

            next_principal_balance_state = next_step_marginal_interest_vector.T.dot(reciprocal_rates) #this corresponds to the P1 vector, and tells us how much we can pay before our strategy must change
            # print('next_state:\n' + str(next_state))

            principal_balance_delta = current_principal_balance_state - next_principal_balance_state
            # print('delta:')
            # print(delta)

            payment_amounts = []
            for i in range(0, principal_balance_delta.shape[0]):

                # if we pay at all, then we add the interest as well.
                current_loan_interest = interest_accts_df.iloc[i,:].Balance
                proposed_payment_on_principal = principal_balance_delta[i, i]

                #todo, currently, if the final payment includes interest, then the total gets distributed across multiple loans and does not go to interest first
                #to fix this, we need to add a interest_paid indicator, and then check for it around line 840 below (written 12/18/23)
                if proposed_payment_on_principal > 0:
                    loop__amount = round(proposed_payment_on_principal + current_loan_interest,2)
                else:
                    loop__amount = 0
                payment_amounts.append(loop__amount)

            total_interest_on_loans_w_non_0_payment = 0
            for i in range(0,len(payment_amounts)):
                if principal_balance_delta[i, i] > 0:
                    total_interest_on_loans_w_non_0_payment += interest_accts_df.iloc[i,:].Balance

            if amount <= sum(payment_amounts):
                payment_amounts = [round(a * (amount) / sum(payment_amounts),2) for a in payment_amounts]
            # print('payment_amounts:' + str(payment_amounts))
            # print('amount -> remaining_amount:')
            # print(str(amount) + ' -> ' + str(amount - sum(payment_amounts)))
            amount = round(amount - sum(payment_amounts),2)

            for i in range(0, principal_balance_delta.shape[0]):
                loop__to_name = principal_accts_df.Name.iloc[i].split(':')[0]
                loop__amount = round(payment_amounts[i], 2)

                # print( str( loop__amount ) + ' ' + loop__to_name )

                if loop__amount == 0:
                    continue

                account_set.executeTransaction(Account_From=checking_acct_name, Account_To=loop__to_name, Amount=round(loop__amount,2))
                payment_amounts__BudgetSet.addBudgetItem(date_string_YYYYMMDD, date_string_YYYYMMDD, 7, 'once', round(loop__amount,2), loop__to_name,False,partial_payment_allowed=False)

        # consolidate payments
        B = payment_amounts__BudgetSet.getBudgetItems()
        # print('B:')
        # print(B.to_string())
        payment_dict = {}
        for index, row in B.iterrows():
            # print('row:')
            # print(row)

            if row.Memo in payment_dict.keys():
                payment_dict[row.Memo] = payment_dict[row.Memo] + round(row.Amount,2)
            else:
                payment_dict[row.Memo] = round(row.Amount,2)

        final_txns = []
        for key in payment_dict.keys():
            final_txns.append(['Checking',key,payment_dict[key]])
            #final_budget_items.append(BudgetItem.BudgetItem(date_string_YYYYMMDD, date_string_YYYYMMDD, 7, 'once', payment_dict[key], False, key, ))


        # log_in_color('green', 'debug', 'final_budget_set:')
        # log_in_color('green', 'debug', final_budget_set)
        log_in_color('green', 'debug', 'EXIT allocate_additional_loan_payments(amount='+str(amount)+')')
        return final_txns


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

            #old line
            #all_accounts_df = pd.concat([all_accounts_df, new_account_row_df], axis=0)

            #new line
            if all_accounts_df.shape[0] == 0:
                all_accounts_df = new_account_row_df
            else:
                all_accounts_df = pd.concat([all_accounts_df, new_account_row_df.astype(all_accounts_df.dtypes)])

            all_accounts_df.reset_index(drop=True, inplace=True)

        # if there are no accounts, I want to return a data frame with 0 rows

        return all_accounts_df

    def to_json(self):
        """
        Get a JSON <string> representation of the <AccountSet> object.

        """
        JSON_string = "{\n"
        for i in range(0, len(self.accounts)):
            JSON_string += self.accounts[i].to_json()
            if i + 1 != len(self.accounts):
                JSON_string += ","
            JSON_string += '\n'
        JSON_string += '}'

        return JSON_string

    # def fromJSON(self,JSON_string):
    #     pass


# written in one line so that test coverage can reach 100%
if __name__ == "__main__": import doctest; doctest.testmod()

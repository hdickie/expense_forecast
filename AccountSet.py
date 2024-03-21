import Account, pandas as pd
import copy
from log_methods import log_in_color
import logging
import numpy as np
import BudgetSet #this could be refactored out, and should be in terms of independent dependencies and clear organization, but it works
import jsonpickle
from log_methods import setup_logger

logger = setup_logger('AccountSet','./log/AccountSet.log',logging.INFO)


def initialize_from_dataframe(accounts_df):
    #print('ENTER AccountSet initialize_from_dataframe')
    A = AccountSet([])
    try:
        for index, row in accounts_df.iterrows():
            row = pd.DataFrame(row).T

            accountname = row.account_name.iat[0]
            balance = row.balance.iat[0]
            min_balance = row.min_balance.iat[0]
            max_balance = row.max_balance.iat[0]
            primary_checking_ind = row.primary_checking_ind.iat[0]

            account_type = row.account_type.iat[0]

            current_statement_balance = row.current_statement_balance.iat[0]
            previous_statement_balance = row.previous_statement_balance.iat[0]
            billing_start_date_yyyymmdd = row.billing_start_date_yyyymmdd.iat[0]
            apr = row.apr.iat[0]
            minimum_payment = row.minimum_payment.iat[0]

            interest_balance = row.interest_balance.iat[0]
            principal_balance = row.principal_balance.iat[0]

            if account_type == 'Checking':
                A.createCheckingAccount(accountname,balance,min_balance,max_balance,primary_checking_ind)
            elif account_type == 'Credit':
                A.createCreditCardAccount(accountname,current_statement_balance,previous_statement_balance,min_balance,max_balance,billing_start_date_yyyymmdd,apr,minimum_payment)
            elif account_type == 'Loan':
                A.createLoanAccount(accountname,principal_balance,interest_balance,min_balance,max_balance,billing_start_date_yyyymmdd,apr,minimum_payment)
            elif account_type == 'Investment':
                A.createInvestmentAccount(accountname, row.balance, row.min_balance, row.max_balance, row.apr)
    except Exception as e:
        print(e.args)
        raise e
    #print(A.getAccounts().to_string())
    #print('EXIT AccountSet initialize_from_dataframe')
    return A

class AccountSet:

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

        value_error_text = ""
        value_error_ind = False

        type_error_text = ""
        type_error_ind = False

        self.accounts = accounts__list

        if len(self.accounts) > 0:
            required_attributes = ['name', 'balance', 'min_balance', 'max_balance', 'account_type',
                                   'billing_start_date_YYYYMMDD',
                                   'interest_type', 'apr', 'interest_cadence', 'minimum_payment']

            for obj in self.accounts:
                # An object in the input list did not have all the attributes an Account is expected to have.
                if set(required_attributes) & set(dir(obj)) != set(required_attributes): raise ValueError("An object in the input list did not have all the attributes an Account is expected to have.")

            # todo sort the accounts in account list so that pbal is before interest, and curr before prev

            # todo check a multiple is not being created

            accounts_df = self.getAccounts()

            loan_check_name__series = accounts_df.loc[
                accounts_df.Account_Type.isin(['principal balance', 'interest']), 'Name']
            cc_check__name__series = accounts_df.loc[
                accounts_df.Account_Type.isin(['prev stmt bal', 'curr stmt bal']), 'Name']

            loan_pb_acct__list = list()
            loan_interest_acct__list = list()
            for acct in loan_check_name__series:
                acct_name = acct.split(':')[0]
                acct_type = acct.split(':')[1].lower().strip()

                if acct_type.lower() == 'principal balance':
                    loan_pb_acct__list.append(acct_name)
                elif acct_type.lower() == 'interest':
                    loan_interest_acct__list.append(acct_name)

            cc_prv_acct__list = list()
            cc_curr_acct__list = list()
            for acct in cc_check__name__series:
                acct_name = acct.split(':')[0]
                acct_type = acct.split(':')[1].lower().strip()

                if acct_type.lower() == 'prev stmt bal':
                    cc_prv_acct__list.append(acct_name)
                elif acct_type.lower() == 'curr stmt bal':
                    cc_curr_acct__list.append(acct_name)

            if (set(loan_pb_acct__list) & set(loan_interest_acct__list)) != set(loan_pb_acct__list) or \
                    (set(loan_pb_acct__list) & set(loan_interest_acct__list)) != set(loan_interest_acct__list):
                value_error_text += "The intersection of Principal Balance and Interest accounts was not equal to the union.\n"
                value_error_text += "loan_pb_acct__list:\n"
                value_error_text += str(loan_pb_acct__list) + "\n"
                value_error_text += 'loan_interest_acct__list:\n'
                value_error_text += str(loan_interest_acct__list) + "\n"
                value_error_ind = True
                raise ValueError("The intersection of Principal Balance and Interest accounts was not equal to the union.")

            if set(cc_prv_acct__list) & set(cc_curr_acct__list) != set(cc_prv_acct__list) or \
                set(cc_prv_acct__list) & set(cc_curr_acct__list) != set(cc_curr_acct__list):
                value_error_text += "The intersection of Prev Stmt Bal and Curr Stmt Bal accounts was not equal to the union.\n"
                value_error_text += "cc_prv_acct__list:\n"
                value_error_text += str(cc_prv_acct__list) + "\n"
                value_error_text += 'cc_curr_acct__list:\n'
                value_error_text += str(cc_curr_acct__list) + "\n"
                value_error_ind = True
                raise ValueError("The intersection of Prev Stmt Bal and Curr Stmt Bal accounts was not equal to the union.")

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

    def __str__(self): return self.getAccounts().to_string()

    def getPrimaryCheckingAccountName(self):
        return self.getAccounts()[self.getAccounts().Primary_Checking_Ind].iloc[0,0]

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
                      current_statement_balance=None,
                      principal_balance=None,
                      interest_balance=None,
                      primary_checking_ind=False,
                      print_debug_messages=True,
                      raise_exceptions=True
                      ):
        """
        Add an Account to list AccountSet.accounts. For credit and loan type accounts, previous statement balance and interest accounts are created.


        """

        #todo disallow adding a second checking account (even better, refactor so that that is not necessary)

        log_string='createAccount(name='+str(name)+',balance='+str(balance)+',account_type='+str(account_type)
        if account_type == 'checking':
            pass
        elif account_type == 'credit':
            log_string+=',billing_start_date_YYYYMMDD='+str(billing_start_date_YYYYMMDD)+',apr='+str(apr)+',previous_statement_balance='+str(previous_statement_balance)
        elif account_type == 'loan':
            log_string+=',billing_start_date_YYYYMMDD='+str(billing_start_date_YYYYMMDD)+',apr='+str(apr)+',principal_balance='+str(principal_balance)+',interest_balance='+str(interest_balance)

        log_string+=')'
        log_in_color(logger,'green', 'debug',log_string, 0)

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
            
        if current_statement_balance is None:
            current_statement_balance = "None"

        if principal_balance is None:
            principal_balance = "None"

        if interest_balance is None:
            interest_balance = "None"

        if account_type.lower() != 'checking' and primary_checking_ind:
            raise ValueError("Primary_Checking_Ind was True when account_type was not checking")

        if account_type.lower() == 'loan':

            if principal_balance == 'None':
                raise ValueError("principal_balance was None for type loan, which is illegal")

            if interest_balance == 'None':
                raise ValueError("interest_balance was None for type loan, which is illegal")

            if float(principal_balance) + float(interest_balance) != float(balance):
                raise ValueError(name+": "+str(principal_balance)+" + "+str(interest_balance)+" != "+str(balance))

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
                                      balance=interest_balance,
                                      min_balance=min_balance,
                                      max_balance=max_balance,
                                      account_type='interest',
                                      # billing_start_date_YYYYMMDD=None,
                                      # interest_type=None,
                                      # apr=None,
                                      # interest_cadence=None,
                                      # minimum_payment=None,
                                      print_debug_messages=print_debug_messages,
                                      raise_exceptions=raise_exceptions)
            self.accounts.append(account)

        elif account_type.lower() == 'credit':

            if previous_statement_balance == 'None':
                raise ValueError("Previous_Statement_Balance cannot be None for account_type=credit")

            if current_statement_balance == 'None':
                raise ValueError("Current_Statement_Balance cannot be None for account_type=credit")

            assert balance == ( current_statement_balance + previous_statement_balance )

            account = Account.Account(name=name + ': Curr Stmt Bal',
                                      balance=current_statement_balance,
                                      min_balance=min_balance,
                                      max_balance=max_balance,
                                      account_type='curr stmt bal',
                                      # billing_start_date_YYYYMMDD=None,
                                      # interest_type=None,
                                      # apr=None,
                                      # interest_cadence=None,
                                      # minimum_payment=None,
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
        elif account_type.lower() == 'checking':
            account = Account.Account(name=name,
                                      balance=balance,
                                      min_balance=min_balance,
                                      max_balance=max_balance,
                                      account_type=account_type,
                                      # billing_start_date_YYYYMMDD=None,
                                      # interest_type=None,
                                      # apr=None,
                                      # interest_cadence=None,
                                      # minimum_payment=None,
                                      primary_checking_ind=primary_checking_ind,
                                      print_debug_messages=print_debug_messages,
                                      raise_exceptions=raise_exceptions)
            self.accounts.append(account)
        elif account_type.lower() == 'investment':
            account = Account.Account(name=name,
                                      balance=balance,
                                      min_balance=min_balance,
                                      max_balance=max_balance,
                                      account_type=account_type,
                                      apr=apr,
                                      print_debug_messages=print_debug_messages,
                                      raise_exceptions=raise_exceptions)

            self.accounts.append(account)
        else: raise NotImplementedError("Account type not recognized: "+str(account_type))



    def createCheckingAccount(self,name,balance,min_balance,max_balance,primary_checking_account_ind=True):
        self.createAccount(name=name,
                      balance=balance,
                      min_balance=min_balance,
                      max_balance=max_balance,
                      account_type='checking',
                      primary_checking_ind=primary_checking_account_ind)

    def createLoanAccount(self,name,principal_balance,interest_balance,min_balance,max_balance,billing_start_date_YYYYMMDD,apr,minimum_payment):
        self.createAccount(name=name,
                      balance=principal_balance + interest_balance,
                      min_balance=min_balance,
                      max_balance=max_balance,
                      account_type='loan',
                      billing_start_date_YYYYMMDD=billing_start_date_YYYYMMDD,
                      interest_type='simple',
                      apr=apr,
                      interest_cadence='daily',
                      minimum_payment=minimum_payment,
                      principal_balance=principal_balance,
                      interest_balance=interest_balance)

    def createCreditCardAccount(self,name,current_stmt_bal,prev_stmt_bal,min_balance,max_balance,billing_start_date_YYYYMMDD,apr,minimum_payment):
        self.createAccount(name=name,
                          balance=current_stmt_bal+prev_stmt_bal,
                          min_balance=min_balance,
                          max_balance=max_balance,
                          account_type='credit',
                          billing_start_date_YYYYMMDD=billing_start_date_YYYYMMDD,
                          interest_type=None,
                          apr=apr,
                          interest_cadence='monthly',
                          minimum_payment=minimum_payment,
                           previous_statement_balance=prev_stmt_bal,
                           current_statement_balance=current_stmt_bal)

    def createInvestmentAccount(self, name, balance, min_balance, max_balance, apr):
        self.createAccount(name=name,
                           balance=balance,
                           min_balance=min_balance,
                           max_balance=max_balance,
                           account_type='investment',
                           interest_type='compound',
                           apr=apr,
                           interest_cadence='monthly')

    def getBalances(self):
        #log_in_color(logger,'magenta','debug','ENTER getBalances()')
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
            elif a.account_type == 'curr stmt bal':
                pass #handled above
            elif a.account_type == 'principal balance':
                principal_balance = a.balance
                interest_balance = self.accounts[i+1].balance
                balances_dict[a.name.split(':')[0]] = ( principal_balance + interest_balance )
            elif a.account_type == 'interest':
                pass #this is handled in the principal balance case
            else: raise ValueError('Account Type not recognized: ' +str(a.account_type) )

        # log_in_color(logger,'magenta', 'debug', balances_dict)
        # log_in_color(logger,'magenta', 'debug', 'EXIT getBalances()')
        return balances_dict

    def executeTransaction(self, Account_From, Account_To, Amount, income_flag=False):
        log_in_color(logger,'white', 'debug','ENTER executeTransaction('+str(Account_From)+','+str(Account_To)+','+str(Amount)+')')
        Amount = round(Amount,2)

        if Amount == 0:
            return

        if Account_To == 'ALL_LOANS':
            loan_payment__list = self.allocate_additional_loan_payments(Amount)
            #print('loan_payment__list:')
            #print(loan_payment__list)
            for i in range(0,len(loan_payment__list)):
                single_account_loan_payment = loan_payment__list[i]
                self.executeTransaction(single_account_loan_payment[0], #From
                                        single_account_loan_payment[1], #To
                                        single_account_loan_payment[2], #Amount
                                        income_flag=False)
            return

        boundary_error_ind = False
        error_msg = ""
        equivalent_exchange_error_ind = False
        debug_print_Amount=str(Amount)
        debt_payment_ind = False

        if Account_From is None:
            Account_From = 'None'
            AF_Account_Type = 'None'

        if Account_To is None:
            Account_To = 'None'
            AT_Account_Type = 'None'

        #log_in_color(logger,'green', 'debug','executeTransaction(Account_From='+Account_From+', Account_To='+Account_To+', Amount='+debug_print_Amount+')')
        #print('executeTransaction(Account_From=' + str(Account_From) + ', Account_To=' + str(Account_To) + ', Amount=' + str(debug_print_Amount) + ')')

        before_txn_total_available_funds = 0
        available_funds = self.getBalances()
        starting_available_funds = copy.deepcopy(available_funds)

        log_in_color(logger,'magenta', 'debug', 'available_funds:'+str(available_funds))

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
                # elif self.accounts[account_from_index].account_type == 'principal balance':
                #     AF_Account_Type = 'loan'
                else: raise ValueError #this would happen if there were 2 accounts w same base name that are not cc accounts in the Account_From field
            elif AF_base_name_match_count == 1:
                AF_Account_Type = self.accounts[account_from_index].account_type
            else: raise ValueError #if this happens, then validation in ExpenseForecast constructor failed to catch something
            #AT_base_name_match_count = account_base_names.count(Account_To)
        else:
            AF_Account_Type = 'None'

        if Account_To is not None:
            if Account_To != '' and Account_To != 'None':
                AT_base_name_match_count = account_base_names.count(Account_To)
                account_to_index = account_base_names.index(Account_To)  # first match found. for credit, first will be current stmt bal, second will be prev
                if AT_base_name_match_count == 2:
                    if self.accounts[account_to_index].account_type == 'curr stmt bal':
                        AT_Account_Type = 'credit'
                    elif self.accounts[account_to_index].account_type == 'principal balance':
                        AT_Account_Type = 'loan'
                    else: raise ValueError #this would happen if there were 2 accts w same basename, not cc or loan, and in Account_From field
                elif AT_base_name_match_count == 1:
                    AT_Account_Type = self.accounts[account_to_index].account_type
                else: raise ValueError #if this happens, then validation in ExpenseForecast constructor failed to catch something
            else:
                AT_Account_Type = 'None'

        #at this point, we know account types but haven't changed any balances
        #if income, one account must be checking, and the other must be none
        if income_flag and AF_Account_Type == 'None' and AT_Account_Type == 'checking':
            pass #cool
        #not cool
        elif income_flag: raise ValueError("income_flag was True but did not refer to a checking account or referred to multiple accounts")


        #overdraft credit txn
        #overcredit credit txn
        if Account_From != '' and Account_From != 'None':
            if AF_Account_Type == 'checking':

                balance_after_proposed_transaction = self.accounts[account_from_index].balance - abs(Amount)

                if abs(balance_after_proposed_transaction) < 0.01:
                    balance_after_proposed_transaction = 0 #rounding errors are a bitch

                try:
                    assert self.accounts[account_from_index].min_balance <= balance_after_proposed_transaction <= self.accounts[account_from_index].max_balance
                except Exception as e:
                    log_in_color(logger,'red', 'debug', '')
                    log_in_color(logger,'red','debug','transaction violated Account_From boundaries:')
                    log_in_color(logger,'red', 'debug', str(e))
                    log_in_color(logger,'red', 'debug', 'Account_From:\n'+str(self.accounts[account_from_index]))
                    log_in_color(logger,'red', 'debug', 'Amount:'+str(Amount))
                    error_msg += 'transaction violated Account_From boundaries:\n'
                    error_msg += 'Account_From:\n'+str(self.accounts[account_from_index])+'\n'
                    error_msg += 'Amount:'+str(Amount)+'\n'
                    boundary_error_ind = True

                self.accounts[account_from_index].balance -= abs(Amount)
                self.accounts[account_from_index].balance = self.accounts[account_from_index].balance
            elif AF_Account_Type == 'credit' or AF_Account_Type == 'loan':

                balance_after_proposed_transaction = self.getBalances()[self.accounts[account_from_index].name.split(':')[0]] - abs(Amount)
                #this check assumes that both prev and curr accounts for credit have the same bounds

                # log_in_color(logger,'magenta', 'debug', 'account min:' + str(self.accounts[account_from_index].min_balance), 3)
                # log_in_color(logger,'magenta', 'debug', 'account max:' + str(self.accounts[account_from_index].max_balance), 3)
                # log_in_color(logger,'magenta', 'debug', 'balance_after_proposed_transaction:' + str(balance_after_proposed_transaction), 3)

                try:
                    assert self.accounts[account_from_index].min_balance <= balance_after_proposed_transaction <= self.accounts[account_from_index].max_balance
                except Exception as e:
                    log_in_color(logger,'red', 'debug', 'transaction violated Account_From boundaries:')
                    log_in_color(logger,'red', 'debug', str(e))
                    log_in_color(logger,'red', 'debug', 'Account_From:\n' + str(self.accounts[account_from_index]))
                    log_in_color(logger,'red', 'debug', 'Amount:' + str(Amount))
                    error_msg += 'transaction violated Account_From boundaries:\n'
                    error_msg += 'Account_From:\n' + str(self.accounts[account_from_index]) + '\n'
                    error_msg += 'Amount:' + str(Amount) + '\n'
                    boundary_error_ind = True

                self.accounts[account_from_index].balance += abs(Amount)
                self.accounts[account_from_index].balance = self.accounts[account_from_index].balance
            else: raise NotImplementedError("account type was: "+str(AF_Account_Type)) #from types other than checking or credit not yet implemented

            if not boundary_error_ind:
                log_in_color(logger,'magenta', 'debug', 'Paid ' + str(Amount) + ' from ' + Account_From, 0)



        if Account_To != '' and Account_To != 'None' and (not boundary_error_ind):
            if AT_Account_Type == 'checking':

                self.accounts[account_to_index].balance += abs(Amount)
                #self.accounts[account_to_index].balance = self.accounts[account_to_index].balance
                log_in_color(logger,'magenta', 'debug', 'Paid ' + str(Amount) + ' to ' + Account_To, 0)
            elif AT_Account_Type == 'credit' or AT_Account_Type == 'loan':

                debt_payment_ind = (AT_Account_Type.lower() == 'loan')

                #we can't use this here
                #AT_ANAME = self.accounts[account_to_index].name.split(':')[0]
                #balance_after_proposed_transaction = self.getBalances()[AT_ANAME] - abs(Amount)

                AT_basename = self.accounts[account_to_index].name.split(':')[0]
                row_sel_vec = [ AT_basename in aname for aname in self.getAccounts().Name ]
                relevant_rows_df = self.getAccounts().iloc[row_sel_vec,1] #col 1 is balance

                assert relevant_rows_df.shape[0] == 2

                balance_after_proposed_transaction = sum(relevant_rows_df) - abs(Amount)

                if abs(balance_after_proposed_transaction) < 0.01:
                    balance_after_proposed_transaction = 0

                try:
                    #print('assert '+str(self.accounts[account_to_index].min_balance)+' <= '+str(balance_after_proposed_transaction)+' <= '+str(self.accounts[account_to_index].max_balance))
                    assert self.accounts[account_to_index].min_balance <= balance_after_proposed_transaction <= self.accounts[account_to_index].max_balance
                except Exception as e:
                    log_in_color(logger,'red', 'debug', '')
                    log_in_color(logger,'red','debug','transaction violated Account_To boundaries:')
                    log_in_color(logger,'red', 'debug', str(e))
                    log_in_color(logger,'red', 'debug', 'Account_To:\n'+str(self.accounts[account_to_index]))
                    log_in_color(logger,'red', 'debug', 'Amount:'+str(Amount))
                    error_msg += 'transaction violated Account_To boundaries:\n'
                    error_msg += 'Account_From:\n' + str(self.accounts[account_to_index]) + '\n'
                    error_msg += 'Amount:' + str(Amount) + '\n'
                    boundary_error_ind = True

                # log_in_color(logger,'magenta', 'debug', 'account min:' + str(self.accounts[account_to_index].min_balance), 3)
                # log_in_color(logger,'magenta', 'debug', 'account max:' + str(self.accounts[account_to_index].max_balance), 3)
                # log_in_color(logger,'magenta', 'debug', 'balance_after_proposed_transaction:' + str(balance_after_proposed_transaction), 3)

                #if the amount we are playing on credit card is more than the previous statement balance
                #OR amt payed on interest is more than the total
                if abs(Amount) >= self.accounts[account_to_index+1].balance:
                    remaining_to_pay = abs(Amount) - self.accounts[account_to_index + 1].balance
                    log_in_color(logger,'magenta', 'debug','Paid ' + str(self.accounts[account_to_index + 1].balance) + ' to ' + str(self.accounts[account_to_index + 1].name), 0)
                    self.accounts[account_to_index + 1].balance = 0

                    #this has the potential to overpay, but we consider that upstreams problem
                    self.accounts[account_to_index].balance -= remaining_to_pay

                    if abs(self.accounts[account_to_index].balance) < 0.01:
                        self.accounts[account_to_index].balance = 0

                    #self.accounts[account_to_index].balance = self.accounts[account_to_index].balance
                    log_in_color(logger,'magenta', 'debug', 'Paid ' + str(remaining_to_pay) + ' to ' + self.accounts[account_to_index].name, 0)
                else: #pay down the previous statement balance
                    log_in_color(logger,'magenta', 'debug', 'Paid ' + str(Amount) + ' to ' + str(self.accounts[account_to_index + 1].name), 0)
                    self.accounts[account_to_index + 1].balance -= Amount
                    if abs(self.accounts[account_to_index + 1].balance) < 0.01:
                        self.accounts[account_to_index + 1].balance = 0
            else: raise NotImplementedError("account type was: "+str(AF_Account_Type)) #from types other than checking or credit not yet implemented



        after_txn_total_available_funds = 0
        available_funds = self.getBalances()
        for a in available_funds.keys():
            after_txn_total_available_funds += available_funds[a]

        empirical_delta = round(after_txn_total_available_funds - before_txn_total_available_funds,2)

        if boundary_error_ind: raise ValueError("Account boundaries were violated\n"+error_msg)

        single_account_transaction_ind = ( Account_From == 'None' or Account_To == 'None' )

        explanation_of_mismatch_string = ''
        if single_account_transaction_ind and income_flag:
            if empirical_delta != Amount: equivalent_exchange_error_ind = True
            explanation_of_mismatch_string += str(empirical_delta) + ' != ' + str(Amount)
        elif not single_account_transaction_ind and debt_payment_ind:
            if empirical_delta != (Amount * -2): equivalent_exchange_error_ind = True
            explanation_of_mismatch_string += str(empirical_delta) + ' != -2 * ' + str(Amount)
        elif single_account_transaction_ind and not income_flag:
            if empirical_delta != (Amount * -1): equivalent_exchange_error_ind = True
            explanation_of_mismatch_string += str(empirical_delta) + ' != -1 * ' + str(Amount)
        elif not single_account_transaction_ind and not income_flag:
            if empirical_delta != 0: equivalent_exchange_error_ind = True
            explanation_of_mismatch_string += str(empirical_delta) + ' != 0'
        else: equivalent_exchange_error_ind = True
            #raise ValueError("impossible error in  AccountSet::executeTransaction(). if 2 accounts were indicated, then the pre-post delta must be 0.") #this should not be possible.


        if equivalent_exchange_error_ind:
            # in contrast to the boundary violation error, this could should never run if this project has been designed correctly.
            equivalent_exchange_error_text = ''
            equivalent_exchange_error_text += 'FUNDS NOT ACCOUNTED FOR POST-TRANSACTION' + '\n'
            equivalent_exchange_error_text += 'single_account_transaction_ind:' + str(single_account_transaction_ind) + '\n'
            equivalent_exchange_error_text += 'income_flag:' + str(income_flag) + '\n'
            equivalent_exchange_error_text += 'debt_payment_ind:' + str(debt_payment_ind) + '\n'
            equivalent_exchange_error_text += 'starting_available_funds:' + str(starting_available_funds) + '\n'
            equivalent_exchange_error_text += 'available_funds:' + str(self.getBalances()) + '\n'
            equivalent_exchange_error_text += 'Amount:' + str(Amount) + '\n'
            equivalent_exchange_error_text += 'empirical_delta:' + str(empirical_delta) + '\n'
            equivalent_exchange_error_text += explanation_of_mismatch_string + '\n'
            log_in_color(logger,'red', 'error', equivalent_exchange_error_text, 0)
            raise ValueError("Funds not accounted for in AccountSet::executeTransaction()") # Funds not accounted for

    # def from_excel(self,path):
    #     self.accounts = []
    #     A_df = pd.read_excel(path)
    #
    #     # "Name": "test",
    #     # "Balance": "0.0",
    #     # "Min_Balance": "0.0",
    #     # "Max_Balance": "0.0",
    #     # "Account_Type": "checking",
    #     # "Billing_Start_Date": "None",
    #     # "Interest_Type": "None",
    #     # "APR": "None",
    #     # "Interest_Cadence": "None",
    #     # "Minimum_Payment": "None"
    #
    #     #info for paired accounts needs to be in one row, so we have to iterate over once
    #     expect_secondary_acct = False
    #     name = None
    #     balance = None
    #     min_balance = None
    #     max_balance = None
    #     billing_start_date_YYYYMMDD = None
    #     interest_type = None
    #     apr = None
    #     interest_cadence = None
    #     minimum_payment = None
    #     for index, row in A_df.iterrows():
    #         if expect_secondary_acct:
    #             assert min_balance == row.Min_Balance
    #             assert max_balance == row.Max_Balance
    #             assert name.split(':')[0] == row.Name.split(':')[0] #these are the only checks createAccount cant catch
    #         else:
    #             name = row.Name
    #             balance = row.Balance
    #             min_balance = row.Min_Balance
    #             max_balance = row.Max_Balance
    #
    #             billing_start_date_YYYYMMDD = row.Billing_Start_Dt
    #             interest_type = row.Interest_Type
    #             apr = row.APR
    #             interest_cadence = row.Interest_Cadence
    #             minimum_payment = row.Minimum_Payment
    #
    #         if row.Account_Type == 'checking':
    #             self.createAccount(name,
    #                   balance,
    #                   min_balance,
    #                   max_balance,
    #                   'checking')
    #         elif (row.Account_Type == 'curr stmt bal' or row.Account_Type == 'interest'
    #               or row.Account_Type == 'prev stmt bal' or row.Account_Type == 'principal balance') and not expect_secondary_acct: #we cant count on row order here
    #             expect_secondary_acct = True
    #             continue
    #         elif row.Account_Type == 'prev stmt bal' and expect_secondary_acct:
    #             expect_secondary_acct = False
    #             self.createAccount(name.split(':')[0],
    #                             balance,
    #                             min_balance,
    #                             max_balance,
    #                             'credit',
    #                             billing_start_date_YYYYMMDD=int(row.Billing_Start_Dt),
    #                             interest_type=row.Interest_Type,
    #                             apr=row.APR,
    #                             interest_cadence=row.Interest_Cadence,
    #                             minimum_payment=row.Minimum_Payment,
    #                             previous_statement_balance=row.Balance,
    #                             principal_balance=None,
    #                             interest_balance=None)
    #         elif row.Account_Type == 'curr stmt bal' and expect_secondary_acct:
    #             expect_secondary_acct = False
    #             self.createAccount(name.split(':')[0],
    #                             row.Balance,
    #                             min_balance,
    #                             max_balance,
    #                             'loan',
    #                            billing_start_date_YYYYMMDD=int(billing_start_date_YYYYMMDD),
    #                            interest_type=interest_type,
    #                            apr=apr,
    #                            interest_cadence=interest_cadence,
    #                            minimum_payment=minimum_payment,
    #                            previous_statement_balance=balance,
    #                            principal_balance=None,
    #                            interest_balance=None)
    #         elif row.Account_Type == 'principal balance' and expect_secondary_acct:
    #             expect_secondary_acct = False
    #             self.createAccount(name.split(':')[0],
    #                             balance + row.Balance,
    #                             min_balance,
    #                             max_balance,
    #                             'loan',
    #                             billing_start_date_YYYYMMDD=int(row.Billing_Start_Dt),
    #                             interest_type=row.Interest_Type,
    #                             apr=row.APR,
    #                             interest_cadence=row.Interest_Cadence,
    #                             minimum_payment=row.Minimum_Payment,
    #                             previous_statement_balance=None,
    #                             principal_balance=balance,
    #                             interest_balance=row.Balance)
    #         elif row.Account_Type == 'interest' and expect_secondary_acct:
    #             expect_secondary_acct = False
    #             self.createAccount(name.split(':')[0],
    #                             balance + row.Balance,
    #                             min_balance,
    #                             max_balance,
    #                             'loan',
    #                             billing_start_date_YYYYMMDD=int(billing_start_date_YYYYMMDD),
    #                             interest_type=interest_type,
    #                             apr=apr,
    #                             interest_cadence=interest_cadence,
    #                             minimum_payment=minimum_payment,
    #                             previous_statement_balance=None,
    #                             principal_balance=balance,
    #                             interest_balance=row.Balance)
    #         else: raise NotImplementedError #an unexpected account type was found, or expect_secondary_acct was set inappropriately
    #

    #
    # def to_excel(self,path):
    #     A = self.getAccounts()
    #     #A['Billing_Start_Dt'] = pd.to_datetime(A['Billing_Start_Dt'])
    #     #print(A.dtypes)
    #     A.to_excel(path)


    #this algorithm does not work because satisfice can be affected by optimizations
    #that is, p1 transactions will disappear if some p7 transactions occur before it
    #Here is the  case that made me realize this:
    #the algorithm receives the forecast with satisfice payments already made
    #however, then an additional payment is made that reduces the principal balance
    #consequently, the satisficed payment has now overpaid interest
    #...
    #...
    #...
    #definitely troublesome
    def allocate_additional_loan_payments(self, amount):
        #bal_string = ''
        #for account_index, account_row in self.getAccounts().iterrows():
        #    bal_string += '$' + str(account_row.Balance) + ' '

        #log_in_color(logger,'blue','debug','ENTER allocate_additional_loan_payments(amount='+str(amount)+') '+bal_string)

        row_sel_vec = [ x for x in ( self.getAccounts().Account_Type == 'checking' ) ]
        checking_acct_name = self.getAccounts()[row_sel_vec].Name[0] #we use this waaay later during executeTransaction
        if self.getAccounts()[row_sel_vec].Balance.iat[0] < amount:
            log_in_color(logger,'green', 'debug', 'input amount is greater than available balance. Reducing amount.')
            amount = self.getAccounts().loc[row_sel_vec,:].Balance.iat[0]

        date_string_YYYYMMDD = '20000101' #this method needs to be refactored

        account_set = copy.deepcopy(self)

        A = account_set.getAccounts()
        principal_accts_df = A[A.Account_Type == 'principal balance']

        principal_accts_df['Marginal Interest Amount'] = principal_accts_df.Balance * principal_accts_df.APR
        principal_accts_df['Marginal Interest Rank'] = principal_accts_df['Marginal Interest Amount'].rank(method='dense', ascending=False)

        number_of_phase_space_regions = max(principal_accts_df['Marginal Interest Rank'])
        # log_in_color(logger,'yellow', 'debug','Explanation of the loan payment algorithm:')
        # log_in_color(logger,'yellow', 'debug', 'FACT 1: The optimal loan payment pays the loan with the highest marginal interest first.')
        # log_in_color(logger,'yellow', 'debug','FACT 2: If two loans have different balances and APRs, but will accrue the same amount of additional interest the next day, then it is at this point that we begin to split our next dollar between the two loans in proportion to the APR.')
        # log_in_color(logger,'yellow', 'debug','We would know that our allocation is optimal when the marginal interest for both loans stays the same.')
        # log_in_color(logger,'yellow', 'debug','Then we will reach a point where we are splitting our next dollar between two loans, then three... (assuming there are this many loans)')
        # log_in_color(logger,'yellow', 'debug','This algorithm finds these points to allocate payment.')
        # log_in_color(logger,'yellow', 'debug', 'If you plot this on a graph, the behavior changes when a new loan joins the group that is being paid proportionally. The space between these points is referred to as a phase space region.')
        # log_in_color(logger,'yellow', 'debug',
        #              'The following table shows the order in which loans will be paid. Marginal Interest Rank 1 will be paid until the Marginal Interest Amount is equal to the account with Marginal Interest Rank 2, etc.')
        # print(principal_accts_df.loc[:,('Name','Balance','Marginal Interest Amount','Marginal Interest Rank')].to_string())

        #log_in_color(logger,'yellow', 'debug', 'number_of_phase_space_regions:'+str(number_of_phase_space_regions))
        # print('number_of_phase_space_regions:'+str(number_of_phase_space_regions))

        all_account_names__1 = [x.split(':') for x in principal_accts_df.Name]
        all_account_names__2 = [name for sublist in all_account_names__1 for name in sublist]
        all_account_names = set(all_account_names__2) - set([' Principal Balance'])

        payment_amounts__BudgetSet = BudgetSet.BudgetSet([])
        payment_amount_tuple_list = []

        for i in range(0, int(number_of_phase_space_regions)):

            if amount == 0:
                break

            log_in_color(logger,'yellow', 'debug','Phase space region index: '+str(i))
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

            #P = np.matrix(principal_accts_df.Balance)
            #todo learn more about numpy ndarray and improve this
            P = np.array(principal_accts_df.Balance)
            P = P[:,None]

            #r = np.matrix(principal_accts_df.APR)
            r = np.array(principal_accts_df.APR)
            r = r[:, None]

            #reciprocal_rates = []
            #for i in range(0, P.shape[1]):
            #    reciprocal_rates.append(1 / r[0, i])
            #reciprocal_rates = np.matrix(reciprocal_rates)\

            #print('P_dot_r:')
            #print(np.matrix(P_dot_r))

            marginal_interest_amounts = np.diag(P.dot(r.T))#this represents marginal interest
            #marginal_interest_amounts__list = []
            #for i in range(0, P.shape[1]):
            #    marginal_interest_amounts__list.append(round(P_dot_r[i, i], 2))
            # print(marginal_interest_amounts__list)
            #marginal_interest_amounts__matrix = np.matrix(marginal_interest_amounts__list)
            #print('marginal_interest_amounts__matrix:')
            #print(marginal_interest_amounts__matrix)

            marginal_interest_amounts_df = pd.DataFrame(marginal_interest_amounts)
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
            marginal_interest_amounts_df__c = pd.DataFrame(marginal_interest_amounts_df,copy=True)

            # print('marginal_interest_amounts_df__c[marginal_interest_amounts_df__c[Marginal Interest Rank] == 1]')
            # print(marginal_interest_amounts_df__c['Marginal Interest Rank'] == 1)
            # print(marginal_interest_amounts_df__c[marginal_interest_amounts_df__c['Marginal Interest Rank'] == 1])
            # print(marginal_interest_amounts_df__c[marginal_interest_amounts_df__c['Marginal Interest Rank'] == 1]['Marginal Interest Amount'])

            marginal_interest_amounts_df__c.loc[
                marginal_interest_amounts_df__c['Marginal Interest Rank'] == 1, marginal_interest_amounts_df__c.columns == 'Marginal Interest Amount'] = next_lowest_marginal_interest_amount
            next_step_marginal_interest_vector = np.array(marginal_interest_amounts_df__c['Marginal Interest Amount']) #this corresponds to the M1 vector
            next_step_marginal_interest_vector = next_step_marginal_interest_vector[:,None]
            #print('next_step_marginal_interest_vector:\n')
            #print(next_step_marginal_interest_vector)

            #todo include interest in these amounts
            current_principal_balance_state = P
            #print('current_state:' + str(current_state))
            #print('total_amount_per_loan:'+str(total_amount_per_loan))

            A = account_set.getAccounts()

            #print('current_state:\n'+str(current_state))

            #print('next_step_marginal_interest_vector:')
            #rint(next_step_marginal_interest_vector)

            reciprocal_rates = 1 / r

            #print('reciprocal_rates:')
            #print(reciprocal_rates)

            next_principal_balance_state = np.diag(next_step_marginal_interest_vector.dot(reciprocal_rates.T))  #this corresponds to the P1 vector, and tells us how much we can pay before our strategy must change

            #print('current_principal_balance_state:\n' + str(current_principal_balance_state))
            #print('next_principal_balance_state:\n' + str(next_principal_balance_state))

            principal_balance_delta = (current_principal_balance_state.T - next_principal_balance_state).T
            #print('principal_balance_delta:')
            #print(principal_balance_delta)

            # log_in_color(logger, 'blue', 'debug', 'principal_balance_delta:')
            # log_in_color(logger, 'blue', 'debug', str(principal_balance_delta))


            payment_amounts = []
            for i in range(0, principal_balance_delta.shape[0]):

                # if we pay at all, then we add the interest as well.
                current_loan_interest = np.array(interest_accts_df.iloc[i,:].Balance) #this is a 1 x 1 array

                proposed_payment_on_principal = principal_balance_delta

                #todo, currently, if the final payment includes interest, then the total gets distributed across multiple loans and does not go to interest first
                if proposed_payment_on_principal[i][0] > 0:
                    loop__amount = round(proposed_payment_on_principal[i][0] + current_loan_interest,2)
                else:
                    loop__amount = 0
                payment_amounts.append(loop__amount)

            total_interest_on_loans_w_non_0_payment = 0
            for i in range(0,len(payment_amounts)):
                if principal_balance_delta[i] > 0:
                    total_interest_on_loans_w_non_0_payment += interest_accts_df.iloc[i,:].Balance

            if amount <= sum(payment_amounts):
                payment_amounts = [a * (amount) / sum(payment_amounts) for a in payment_amounts]
            # print('payment_amounts:' + str(payment_amounts))
            # print('amount -> remaining_amount:')
            # print(str(amount) + ' -> ' + str(amount - sum(payment_amounts)))
            amount = amount - sum(payment_amounts)

            for i in range(0, principal_balance_delta.shape[0]):
                loop__to_name = principal_accts_df.Name.iloc[i].split(':')[0]
                loop__amount = payment_amounts[i]

                # print( str( loop__amount ) + ' ' + loop__to_name )

                if loop__amount == 0:
                    continue

                account_set.executeTransaction(Account_From=checking_acct_name, Account_To=loop__to_name, Amount=loop__amount)
                #payment_amounts__BudgetSet.addBudgetItem(date_string_YYYYMMDD, date_string_YYYYMMDD, 7, 'once', round(loop__amount,2), loop__to_name,False,partial_payment_allowed=False)
                payment_amount_tuple_list.append((loop__to_name,loop__amount))

        unique_payment_amount_tuple_dict = {}
        for tp in payment_amount_tuple_list:
            if tp[0] not in unique_payment_amount_tuple_dict:
                unique_payment_amount_tuple_dict[tp[0]] = tp[1]
            else:
                unique_payment_amount_tuple_dict[tp[0]] += tp[1]

        for key, value in unique_payment_amount_tuple_dict.items():
            payment_amounts__BudgetSet.addBudgetItem(date_string_YYYYMMDD, date_string_YYYYMMDD, 7, 'once',
                                                     value, key, False,
                                                     partial_payment_allowed=False)

        # consolidate payments
        B = payment_amounts__BudgetSet.getBudgetItems()
        # print('B:')
        # print(B.to_string())
        payment_dict = {}
        for index, row in B.iterrows():
            # print('row:')
            # print(row)

            if row.Memo in payment_dict.keys():
                payment_dict[row.Memo] = payment_dict[row.Memo] + row.Amount
            else:
                payment_dict[row.Memo] = row.Amount

        final_txns = []
        for key in payment_dict.keys():
            final_txns.append([checking_acct_name,key,payment_dict[key]])
            #final_budget_items.append(BudgetItem.BudgetItem(date_string_YYYYMMDD, date_string_YYYYMMDD, 7, 'once', payment_dict[key], False, key, ))


        #log_in_color(logger,'green', 'debug', 'final_txns:')
        #log_in_color(logger,'green', 'debug', final_txns)
        #log_in_color(logger,'blue', 'debug', 'EXIT allocate_additional_loan_payments(amount='+str(amount)+')')
        return final_txns

    def getAccounts(self):
        """
        Get a DataFrame representing the AccountSet object.

        This test is failing even though this is indeed the result I get when I try this in the console.
        # >>> x=AccountSet().getAccounts()
        # Empty DataFrame
        # Columns: [Name, Balance, Previous_Statement_Balance, Min_Balance, Max_Balance, APR, Interest_Cadence, Interest_Type, Billing_Start_Dt, Account_Type, Principal_Balance, interest_balance, Minimum_Payment]
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
                                        'Billing_Start_Date': [],
                                        'Interest_Type': [],
                                        'APR': [],
                                        'Interest_Cadence': [],
                                        'Minimum_Payment': [],
                                        'Primary_Checking_Ind': []
                                        })

        for account in self.accounts:
            new_account_row_df = pd.DataFrame({'Name': [account.name],
                                               'Balance': [account.balance],
                                               'Min_Balance': [account.min_balance],
                                               'Max_Balance': [account.max_balance],
                                               'Account_Type': [account.account_type],
                                               'Billing_Start_Date': [account.billing_start_date_YYYYMMDD],
                                               'Interest_Type': [account.interest_type],
                                               'APR': [account.apr],
                                               'Interest_Cadence': [account.interest_cadence],
                                               'Minimum_Payment': [account.minimum_payment],
                                               'Primary_Checking_Ind': [account.primary_checking_ind]
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
        return jsonpickle.encode(self,indent=4)


# written in one line so that test coverage can reach 100%
if __name__ == "__main__": import doctest; doctest.testmod()

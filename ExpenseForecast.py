
import pandas as pd, numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
import datetime
import re

import BudgetSet


def generate_date_sequence(start_date_YYYYMMDD,num_days,cadence):
    """ A wrapper for pd.date_range intended to make code easier to read.

    #todo write project_utilities.generate_date_sequence() doctests
    """

    start_date = datetime.datetime.strptime(start_date_YYYYMMDD,'%Y%m%d')
    end_date = start_date + datetime.timedelta(days=num_days)

    if cadence.lower() == "once":
        return pd.Series(start_date)
    elif cadence.lower() == "daily":
        return_series = pd.date_range(start_date,end_date,freq='D')
    elif cadence.lower() == "weekly":
        return_series = pd.date_range(start_date,end_date,freq='W')
    elif cadence.lower() == "biweekly":
        return_series = pd.date_range(start_date,end_date,freq='2W')
    elif cadence.lower() == "monthly":

        day_delta = int(start_date.strftime('%d'))-1
        first_of_each_relevant_month = pd.date_range(start_date,end_date,freq='MS')

        return_series = first_of_each_relevant_month + datetime.timedelta(days=day_delta)
    elif cadence.lower() == "quarterly":
        #todo check if this needs an adjustment like the monthly case did
        return_series = pd.date_range(start_date,end_date,freq='Q')
    elif cadence.lower() == "yearly":
        # todo check if this needs an adjustment like the monthly case did
        return_series = pd.date_range(start_date,end_date,freq='Y')

    return return_series

class ExpenseForecast:

    def __init__(self,
                 account_set,
                 budget_set,
                 memo_rule_set,
                 start_date_YYYYMMDD,
                 end_date_YYYYMMDD,
                 print_debug_messages=True,
                 raise_exceptions=True):
        """
        ExpenseForecast one-line description

        # todo ExpenseForecast doctests
        | Test Cases
        | Expected Successes
        | S1: ... #todo refactor ExpenseForecast.ExpenseForecast() doctest S1 to use _S1 label
        |
        | Expected Fails
        | F1 ... #todo refactor ExpenseForecast.ExpenseForecast() doctest F1 to use _F1 label

        :param account_set:
        :param budget_set:
        :param memo_rule_set:
        """
        #print('Starting Expense Forecast...\n')


        try:
            self.start_date = datetime.datetime.strptime(start_date_YYYYMMDD,'%Y%m%d')
        except:
            print('value was:'+str(start_date_YYYYMMDD)+'\n')
            raise ValueError #Failed to cast start_date_YYYYMMDD to datetime with format %Y%m%d

        try:
            self.end_date = datetime.datetime.strptime(end_date_YYYYMMDD,'%Y%m%d')
        except:
            raise ValueError #Failed to cast end_date_YYYYMMDD to datetime with format %Y%m%d

        if self.start_date >= self.end_date:
            raise ValueError #start_date must be before end_date

        accounts_df = account_set.getAccounts()
        if accounts_df.shape[0] == 0:
        #if len(account_set) == 0:
            raise ValueError #There needs to be at least 1 account for ExpenseForecast to do anything.
        #todo more strict checking

        budget_df = budget_set.getBudgetItems()
        memo_df = memo_rule_set.getMemoRules()

        error_text = ""
        error_ind = False

        # for each distinct account name in all memo rules to and from fields, there is a matching account
        # that is, for each memo rule that mentions an account, the mentioned account should exist
        # not that it is NOT a requirement that the converse is true
        # that is, there can be an account that has no corresponding memo rules

        # should be no duplicates and credit and loan acct splitting is already handled

        distinct_base_account_names__from_acct = pd.DataFrame(pd.DataFrame(accounts_df[['Name']]).apply(lambda x: x[0].split(':')[0],axis=1).drop_duplicates()).rename(columns={0:'Name'})
        account_names__from_memo = pd.concat([pd.DataFrame(memo_df[['Account_From']]).rename(columns={'Account_From':'Name'}),
                                              pd.DataFrame(memo_df[['Account_To']]).rename(columns={'Account_To':'Name'}) ])

        distinct_account_names__from_memo = pd.DataFrame(account_names__from_memo.loc[account_names__from_memo.Name != 'None', 'Name'].drop_duplicates().reset_index(drop=True))

        try:
            A = set(distinct_account_names__from_memo.Name).union(set(['']))
            B = set(distinct_account_names__from_memo.Name).intersection(set(distinct_base_account_names__from_acct.Name)).union(set(['']))
            assert A == B
        except:
            error_text += 'An account name was mentioned in a memo rule that did not exist in the account set\n'
            error_text += 'all accounts mentioned in memo rules:\n'
            error_text += distinct_account_names__from_memo.Name.to_string()+'\n'
            error_text += 'all defined accounts:\n'
            error_text += distinct_base_account_names__from_acct.Name.to_string()+'\n'
            error_text += 'intersection:\n'
            error_text += str(B)+'\n'
            error_text += 'Accounts from Memo:\n'
            error_text += str(A)+'\n'
            error_ind = True

        #for each budget item memo x priority combo, there is at least 1 memo_regex x priority that matches
        distinct_memo_priority_combinations__from_budget = budget_df[['Priority', 'Memo']].drop_duplicates()
        distinct_memo_priority_combinations__from_memo = memo_df[['Transaction_Priority', 'Memo_Regex']] #should be no duplicates

        any_matches_found_at_all = False
        for budget_index, budget_row in distinct_memo_priority_combinations__from_budget.iterrows():
            match_found = False
            for memo_index, memo_row in distinct_memo_priority_combinations__from_memo.iterrows():
                if budget_row.Priority == memo_row.Transaction_Priority:
                    m = re.search(memo_row.Memo_Regex, budget_row.Memo)
                    if m is not None:
                        match_found = True
                        any_matches_found_at_all = True
                        continue

            if match_found == False:
                error_text += "No regex match found for memo:\'"+str(budget_row.Memo)+"\'\n"

        if any_matches_found_at_all == False:
            error_ind = True

        smpl_sel_vec = accounts_df.Interest_Type.apply(lambda x: x.lower() if x is not None else None) == 'simple'
        cmpnd_sel_vec = accounts_df.Interest_Type.apply(lambda x: x.lower() if x is not None else None) == 'compound'

        if print_debug_messages:
            if error_ind: print(error_text)

        if raise_exceptions:
            if error_ind:
                raise ValueError

        self.initial_account_set = account_set
        self.initial_budget_set = budget_set
        self.initial_memo_rule_set = memo_rule_set

        self.forecast_df = pd.DataFrame({
            'Date':['20000101','20000102','20000103','20000104'],
            'Checking': [0,0,0,0],
            'Credit: Curr Stmt Bal': [0,0,0,0],
            'Credit: Prev Stmt Bal': [0,0,0,0],
            'Memo':['','','','']
        })

        #this method already has access to these: account_set, budget_set, memo_rule_set,start_date_YYYYMMDD,end_date_YYYYMMDD
        deffered_and_forecast__list = self.computeForecast()
        self.deferred_df = deffered_and_forecast__list[0]
        self.forecast_df = deffered_and_forecast__list[1]

        self.forecast_df.index = self.forecast_df['Date']

        #write all_data.csv
        self.forecast_df.iloc[:,0:(self.forecast_df.shape[1]-1)].to_csv('all_data.csv',index=False)

        self.forecast_df.to_csv('out.csv', index=False)

    def account_boundaries_are_violated(self,accounts_df,forecast_df):
        """
        account_boundaries_are_violated single-line description

        #todo ExpenseForecast.account_boundaries_are_violated() doctests
        | Test Cases
        | Expected Successes
        | S1: ... #todo refactor ExpenseForecast.account_boundaries_are_violated() doctest S1 to use _S1 label
        |
        | Expected Fails
        | F1 ... #todo refactor ExpenseForecast.account_boundaries_are_violated() doctest F1 to use _F1 label

        :param accounts_df:
        :param forecast_df:
        :return:
        """
        for col_name in forecast_df.columns.tolist():
            if col_name == 'Date' or col_name == 'Memo':
                continue

            current_column = forecast_df[col_name]

            acct_boundary__min = float(accounts_df.loc[accounts_df.Name == col_name,'Min_Balance'])
            acct_boundary__max = float(accounts_df.loc[accounts_df.Name == col_name, 'Max_Balance'])

            min_in_forecast_for_acct = min(current_column)
            max_in_forecast_for_acct = max(current_column)

            try:
                # print(current_column)
                # print('min_in_forecast_for_acct:'+str(min_in_forecast_for_acct))
                # print('max_in_forecast_for_acct:' + str(max_in_forecast_for_acct))
                # print('acct_boundary__min:' + str(acct_boundary__min))
                # print('acct_boundary__max:' + str(acct_boundary__max))
                # print('')
                # print('')

                assert float(min_in_forecast_for_acct) >= float(acct_boundary__min)
                assert float(max_in_forecast_for_acct) <= float(acct_boundary__max)

            except Exception as e:

                offending_rows__min = forecast_df[current_column < acct_boundary__min]
                offending_rows__max = forecast_df[current_column > acct_boundary__max]

                # print(e)
                # print('Account Boundary Violation for '+str(col_name)+' in ExpenseForecast.account_boundaries_are_violated()')
                # print('Offending Rows: Minimum')
                # print(offending_rows__min.to_string())
                # print('Offending Rows: Maximum')
                # print(offending_rows__max.to_string())
                return True
        return False

    def getInitialForecastRow(self):

        min_sched_date = self.start_date
        account_set_df = self.initial_account_set.getAccounts()

        date_only_df = pd.DataFrame(['Date', min_sched_date.strftime('%Y-%m-%d')]).T

        accounts_only_df = pd.DataFrame(account_set_df.iloc[:, 0:1]).T
        accounts_only_df.reset_index(inplace=True, drop=True)
        accounts_only_df.columns = accounts_only_df.iloc[0]

        starting_zero_balances_df = pd.DataFrame([0] * account_set_df.shape[0]).T
        starting_zero_balances_df.reset_index(inplace=True, drop=True)
        starting_zero_balances_df.columns = accounts_only_df.iloc[0]

        accounts_only_df = pd.concat([accounts_only_df, starting_zero_balances_df]).T
        accounts_only_df.reset_index(drop=True, inplace=True)
        accounts_only_df.columns = [0, 1]

        memo_only_df = pd.DataFrame(['Memo', '']).T

        initial_forecast_row_df = pd.concat([
            date_only_df,
            accounts_only_df,
            memo_only_df
        ])

        initial_forecast_row_df = initial_forecast_row_df.T
        initial_forecast_row_df.columns = initial_forecast_row_df.iloc[0, :]
        initial_forecast_row_df = initial_forecast_row_df[1:]
        initial_forecast_row_df.reset_index(drop=True, inplace=True)

        # print('initial forecast values pre assignment:')
        # print(forecast_df.to_string())

        # set initial values
        for i in range(0, account_set_df.shape[0]):
            row = account_set_df.iloc[i, :]
            # print('row:'+str(row))
            # print('Setting '+forecast_df.columns.tolist()[i+1]+' = '+str(row.Balance))

            initial_forecast_row_df.iloc[0, 1 + i] = row.Balance

        return initial_forecast_row_df

    def executeTransactionsForDay(self,budget_schedule_df,account_set,memo_set,current_forecast_row_df):

        #making minimum payments should be determined by memo rules instead of hard-coded as checking
        # try:
        #     print('budget_schedule_df:\n'+budget_schedule_df.to_string())
        # except Exception as e:
        #     pass
        # try:
        #     print('memo_rule_set:\n' + memo_rule_set.to_string())
        # except Exception as e:
        #     pass
        #
        # try:
        #     print('current_forecast_row_df:\n' + current_forecast_row_df.to_string())
        # except Exception as e:
        #     pass

        # This makes sure that Income is considered first
        budget_schedule_df.sort_values(by='Amount',inplace=True,ascending=False)

        deferred_transactions = []

        for index, row in budget_schedule_df.iterrows():

            found_matching_memo_rule = False
            for index2, row2 in memo_set.getMemoRules().iterrows():
                m = re.search(row2.Memo_Regex,row.Memo)
                try:
                    m.group(0)
                    found_matching_memo_rule = True
                except:
                    pass # no match

                if found_matching_memo_rule:

                    account_set.executeTransaction(row2.Account_From,row2.Account_To,row.Amount)

                    current_forecast_row_df.Memo += row.Memo + ' ; '
                    break #stop looking for matching memo rules
                else:
                    pass
                    #we checked for this case in the ExpenseForecast constructor so lets not do it here


        #at this point, memo has been updated, but balances are stale
        updated_balances = account_set.getAccounts().Balance
        for i in range(0,updated_balances.shape[0]):
            pass
            current_forecast_row_df.iloc[0,i+1] = updated_balances[i]

        #returns a single forecast row with updated memo
        return current_forecast_row_df

    def calculateInterestAccrualsForDay(self,account_set,current_forecast_row_df):

        #This method will transfer balances from current statement to previous statement for savings and credit accounts

        current_date = current_forecast_row_df.Date[0]

        #generate a date sequence at the specified cadence between billing_start_date and the current date
        #if the current date is in that sequence, then do accrual

        account_index = 0
        for index, row in account_set.getAccounts().iterrows():
            #print(row)
            if row.Interest_Cadence == 'None' or row.Interest_Cadence is None or row.Interest_Cadence == '': #ithink this may be refactored. i think this will explode if interest_cadence is None
                account_index += 1
                continue

            if row.Account_Type == 'savings':
                account_index += 1
                continue #todo

            num_days = (datetime.datetime.strptime(current_date,'%Y-%m-%d') - row.Billing_Start_Dt).days
            dseq = generate_date_sequence(start_date_YYYYMMDD=row.Billing_Start_Dt.strftime('%Y%m%d'),
                                          num_days=num_days,
                                          cadence=row.Interest_Cadence)

            if current_date in dseq:
                #do accruals
                if row.Account_Type == 'prev stmt bal' and row.Interest_Cadence == 'monthly':
                    #print('DOING INTEREST ACCRUAL')
                    #print('row:\n'+str(row.to_string()))
                    accrued_interest = row.APR * row.Balance / 12
                    account_set.accounts[account_index].balance += accrued_interest

                    #move curr stmt bal to previous
                    prev_stmt_balance = account_set.accounts[account_index - 1].balance

                    prev_acct_name = account_set.accounts[account_index - 1].name
                    curr_acct_name = account_set.accounts[account_index].name
                    #print('current account name:' + str(curr_acct_name))
                    #print('prev_acct_name:'+str(prev_acct_name))
                    #print('prev_stmt_balance:'+str(prev_stmt_balance))
                    account_set.accounts[account_index].balance += prev_stmt_balance
                    account_set.accounts[account_index - 1].balance = 0

                #todo loan interest case

            account_index += 1

        updated_balances = account_set.getAccounts().Balance
        for i in range(0, updated_balances.shape[0]):
            pass
            current_forecast_row_df.iloc[0, i + 1] = updated_balances[i]
        # returns a single forecast row (memo is updated externally)
        return current_forecast_row_df

    def computeForecast(self):
        """
        Computes output time-series that represents only non-negotiable spend.

        | Test Cases
        | Expected Successes
        | S1: ... #todo refactor ExpenseForecast.computeForecast() doctest S1 to use _S1 label
        |
        | Expected Fails
        | F1 ... #todo refactor ExpenseForecast.computeForecast() doctest F1 to use _F1 label

        :param budget_schedule_df:
        :param account_set_df:
        :param memo_rules_df:
        :return:
        """

        #this method will execute all budgetitems given to it. If account boudnaries are violated, it is because
        #the input provided was not properly vetted

        all_days = pd.date_range(self.start_date,self.end_date)
        initial_forecast_row_df = self.getInitialForecastRow()
        numdays = (self.end_date - self.start_date).days  # TODO assert upstream that end date is after start date, or include numdays as a obj var
        budget_schedule_df = self.initial_budget_set.getBudgetSchedule(self.start_date.strftime('%Y%m%d'), self.end_date.strftime('%Y%m%d'))


        memo_set = self.initial_memo_rule_set # this never changes
        account_set = self.initial_account_set

        #print('numdays:'+str(numdays))
        #print('initial_budget_set:'+str(self.initial_budget_set))
        #print('budget_schedule_df:'+budget_schedule_df.to_string()+'\n')
        for d in all_days:
          if d == self.start_date:
              forecast_df = initial_forecast_row_df
              previous_row_df = initial_forecast_row_df
              continue #because we consider the input values for the first day to be final
          current_row_df = previous_row_df.copy()
          current_row_df.Date = d.strftime('%Y-%m-%d')
          current_row_df.Memo = ''

          this_days_budget_schedule_df = budget_schedule_df.loc[budget_schedule_df.Date == d,:]

          #print('this_days_budget_schedule_df:'+str(this_days_budget_schedule_df))
          new_forecast_row_df = self.executeTransactionsForDay( this_days_budget_schedule_df, account_set, memo_set,current_row_df) #returns only a forecast row w updated memo
          new_forecast_row_df = self.calculateInterestAccrualsForDay( account_set,new_forecast_row_df ) #returns only a forecast row w updated memo

          forecast_df = pd.concat([forecast_df,new_forecast_row_df])
          previous_row_df = new_forecast_row_df

        deferred_past_end_date_budget_items_df = None

        # index_of_checking_column = forecast_df.columns.tolist().index('Checking')
        # index_of_memo_column = forecast_df.columns.tolist().index('Memo')
        # for d in all_days:
        #     if d == forecast_df.iloc[0,0]:
        #         previous_date = d
        #         continue #we consider the starting balances finalized
        #     new_row_df = forecast_df[forecast_df.Date == previous_date].copy()
        #     new_row_df.Date = d
        #     new_row_df.Memo = ''
        #
        #     relevant_budget_items_df = priority_1_budget_schedule_df.loc[ d == priority_1_budget_schedule_df.Date, : ]
        #     relevant_budget_items_df.sort_values(inplace=True, axis=0, by="Amount",ascending=False)
        #
        #     #here, interest is calculated and current statement balances are moved to previous
        #     for index, row in account_set_df.iterrows():
        #         if row['APR'] == 0:
        #             continue
        #
        #         if row['Account_Type'].lower() not in ['previous statement balance','interest']:
        #             continue
        #
        #         days_since_billing_start_date = (d - row['Billing_Start_Dt']).days
        #
        #         if row['Interest_Cadence'].lower() == 'daily':
        #             pass #we want to continue processing
        #         elif row['Interest_Cadence'].lower() == 'monthly':
        #             interest_accrual_days = generate_date_sequence(row['Billing_Start_Dt'].strftime('%Y%m%d'),
        #                                                            days_since_billing_start_date + 10, 'monthly')
        #             #print('checking if this is a day for monthly interest accrual')
        #             #print('? is '+str(d)+' in '+str(interest_accrual_days))
        #             if d not in interest_accrual_days:
        #                 continue
        #         elif row['Interest_Cadence'].lower() == 'yearly':
        #             interest_accrual_days = generate_date_sequence(row['Billing_Start_Dt'].strftime('%Y%m%d'),
        #                                                            days_since_billing_start_date + 10, 'yearly')
        #             if d not in interest_accrual_days:
        #                 continue
        #         else:
        #             print('Undefined case in computeForecast()')
        #
        #         #at this point, we know we are about to calculate interest. how we do that depends on cadence and account type
        #
        #         relevant_apr = row['APR']
        #         #print('row:'+str(row))
        #         if row['Account_Type'].lower() == 'previous statement balance' and row['Interest_Cadence'].lower() == 'monthly':
        #
        #             # total_debt = forecast_df.iloc[0, i] + forecast_df.iloc[0, i + 1] #i is current, i + 1 is previous
        #             available_funds = new_row_df.iloc[0, index_of_checking_column]
        #             # current_statement_balance = forecast_df.iloc[0, i]
        #             previous_statement_balance = new_row_df.iloc[0, index + 1] #plus 1 bc index is an iterative cursor for accounts_df not forecast_df
        #
        #             # scenarios
        #             # 1. make cc min payment only. bal is less than $40
        #             # 2. make cc min payment only. bal is more than $40 and less than $2k
        #             # 3. make cc min payment only. bal is more than $2k. min payment is 2%
        #             # 4. make cc min payment. combined current and prev statement balance less than $40, both non 0%
        #
        #             # scenarios: previous statement balance and payment in excess of minimum
        #
        #             # 5. make cc payment in excess of minimum. current statement more than $40, pay less than total balance.
        #             # 6. make cc payment in excess of minimum. current statement more than $40, pay less than total balance, when balance is greater than checking
        #             # 7. make cc payment in excess of minimum. current statement more than $2k, pay more than total balance.
        #             if new_row_df.iloc[0, index_of_memo_column] != "":
        #                 new_row_df.iloc[0, index_of_memo_column] += ' ; '
        #
        #             new_row_df.iloc[0, index_of_memo_column] += ' Min cc pmt , '
        #             if available_funds > previous_statement_balance and previous_statement_balance <= 40:
        #                 new_row_df.iloc[0, index_of_checking_column] -= previous_statement_balance
        #                 new_row_df.iloc[0, i + 1] = 0  # pay previous statement balance
        #                 new_row_df.iloc[0, index_of_memo_column] += ' Checking - '+str(previous_statement_balance)+' , '
        #                 new_row_df.iloc[0, index_of_memo_column] += ' Credit - ' + str(previous_statement_balance) + ' , '
        #             elif available_funds > previous_statement_balance and 40 < previous_statement_balance and previous_statement_balance <= 2000:
        #                 new_row_df.iloc[0, index_of_checking_column] -= 40
        #                 new_row_df.iloc[0, i + 1] -= 40  # pay previous statement balance
        #                 new_row_df.iloc[0, index_of_memo_column] += ' Checking - ' + str(40) + ' , '
        #                 new_row_df.iloc[0, index_of_memo_column] += ' Credit - ' + str(40) + ' , '
        #             elif available_funds > previous_statement_balance and 2000 <= previous_statement_balance:
        #                 min_payment_amt = previous_statement_balance * 0.02
        #                 new_row_df.iloc[0, index_of_checking_column] -= min_payment_amt
        #                 new_row_df.iloc[0, i + 1] -= min_payment_amt
        #                 new_row_df.iloc[0, index_of_memo_column] += ' Checking - ' + str(min_payment_amt) + ' , '
        #                 new_row_df.iloc[0, index_of_memo_column] += ' Credit - ' + str(min_payment_amt) + ' , '
        #
        #             #interest accrual and balance transfer
        #             index_of_previous_statement_balance = new_row_df.columns.tolist().index(row.Name)
        #             previous_statement_balance = new_row_df.iloc[0, index_of_previous_statement_balance]
        #
        #             index_of_current_statement_balance = index_of_previous_statement_balance - 1
        #             current_statement_balance = new_row_df.iloc[0, index_of_current_statement_balance]
        #
        #             #move current statement balance to previous and add interest
        #             new_interest_accrued = previous_statement_balance*relevant_apr/12
        #             new_row_df.iloc[0,index_of_previous_statement_balance] = current_statement_balance + previous_statement_balance + new_interest_accrued
        #             new_row_df.iloc[0, index_of_current_statement_balance] = 0
        #
        #             new_row_df.iloc[0, index_of_memo_column] += ' cc interest accrued ' + str(new_interest_accrued)
        #
        #         elif row['Account_Type'].lower() == 'interest' and row['Interest_Cadence'].lower() == 'daily':
        #             index_of_accrued_interest = new_row_df.columns.tolist().index(row.Name)
        #             index_of_principal_balance = index_of_accrued_interest - 1
        #
        #             new_row_df.iloc[0, index_of_accrued_interest] += new_row_df.iloc[0, index_of_principal_balance]*relevant_apr/365.25
        #
        #         elif row['Account_Type'].lower() == 'interest' and row['Interest_Cadence'].lower() == 'monthly':
        #             index_of_accrued_interest = new_row_df.columns.tolist().index(row.Name)
        #             index_of_principal_balance = index_of_accrued_interest - 1
        #
        #             new_row_df.iloc[0, index_of_accrued_interest] += new_row_df.iloc[
        #                                                                  0, index_of_principal_balance] * relevant_apr / 12
        #         elif row['Account_Type'].lower() == 'interest' and row['Interest_Cadence'].lower() == 'yearly':
        #             index_of_accrued_interest = new_row_df.columns.tolist().index(row.Name)
        #             index_of_principal_balance = index_of_accrued_interest - 1
        #
        #             new_row_df.iloc[0, index_of_accrued_interest] += new_row_df.iloc[
        #                                                                  0, index_of_principal_balance] * relevant_apr
        #         else:
        #             print('Undefined case in computeForecast()')
        #
        #     #other priority 1 transactions
        #     for index, budget_item in relevant_budget_items_df.iterrows():
        #         #if memo matches any regex in memo_rules_df
        #             #relevant_memo_rule = memo_rules_df[memo_rules_df.transaction_priority == 1 and memo_rules_df]
        #
        #         #use first regex match
        #         found_matching_regex = False
        #         for index2, row2 in memo_rules_df[memo_rules_df.transaction_priority == 1].iterrows():
        #             m = re.search(row2.memo_regex,budget_item.Memo)
        #
        #             if m is not None:
        #                 #do stuff
        #
        #                 if row2.account_from is not None:
        #                     index_of_account_from_column = list(new_row_df.columns).index(row2.account_from)
        #
        #                 if row2.account_to is not None:
        #                     index_of_account_to_column = list(new_row_df.columns).index(row2.account_to)
        #
        #                 if row2.account_from is not None and row2.account_to is None: #e.g. income
        #                     new_row_df.iloc[0, index_of_account_from_column] += budget_item.Amount
        #
        #                 if row2.account_to is not None and row2.account_from is None: #e.g. spend
        #                     new_row_df.iloc[0, index_of_account_to_column] += budget_item.Amount
        #
        #                 if row2.account_from is not None and row2.account_to is not None:  # e.g. xfer bw accts
        #                     new_row_df.iloc[0, index_of_account_to_column] += budget_item.Amount
        #                     new_row_df.iloc[0, index_of_account_from_column] -= budget_item.Amount
        #
        #                 found_matching_regex = True
        #                 break
        #
        #         if not found_matching_regex:
        #             print('We received a budget item that we do not have a case to handle. this is a show stopping error.')
        #             print('Exiting.')
        #         else: #update memo
        #             if new_row_df.loc[0,'Memo'] != '':
        #                 new_row_df.loc[0,'Memo'] = new_row_df.loc[0,'Memo'] + '; '
        #
        #             new_memo_text = budget_item.Memo + ' , '
        #             if row2.account_from is not None:
        #                 new_memo_text = new_memo_text + str(row2.account_from) + ' ' + str(-1*abs(budget_item.Amount)) + ' '
        #
        #             if row2.account_to is not None:
        #                 new_memo_text = new_memo_text + str(row2.account_to) + ' ' + str(budget_item.Amount) + ' '
        #
        #             new_row_df.loc[0, 'Memo'] = new_row_df.loc[0,'Memo'] + new_memo_text
        #
        #     previous_date = d
        #     if self.account_boundaries_are_violated(account_set_df,new_row_df):
        #         break
        #     else:
        #         forecast_df = pd.concat([forecast_df, new_row_df])



        # Fully don't need these lines but not deleting them yet just for completeness of the commented out section
        # updated_budget_schedule_df = budget_schedule_df.loc[budget_schedule_df.Priority != 1,:]
        # updated_budget_schedule_df.sort_values(inplace=True, axis=0, by="Date")
        # updated_budget_schedule_df.reset_index(inplace=True, drop=True)

        #account_set_df is returned unchanged. we depend on optimize logic to not violate boundaries by checking the forecast
        return [deferred_past_end_date_budget_items_df, forecast_df]

    def decide__defer_or_execute_or_skip(self,budget_schedule_item_df,account_set_df,forecast_df):
        """
        Returns an empty row (execute or skip), or an updated <DataFrame> of BudgetItems.

        This method accepts a single BudgetItem, along with the AccountSet and Forecast.

        This should print the reason for the decision to logs.

        :param budget_schedule_item_df:
        :param account_set_df:
        :param forecast_df:
        :return boolean:
        """

        #this needs to be able to accept "*", meaning "free balance"

        return True

    def evaluate_free_balance(self,account_set_df,forecast_df):
        #return values for each account

        pass

    def allocate_loan_payments(self, account_set, amount, date_string_YYYYMMDD, recursion_depth=0, partial_payment_budget_set=None):
        """
        First pass at this does not account for minimum payment amounts

        returns a budget item for each account implementing the payment
        """

        left_prefix = ' '.rjust(recursion_depth, '#')

        # The Algorithm:
        # if payment amount is larger than grand total, then pay and move on
        # Calculate the marginal interest amounts. Order them greatest to least.
        # All those accounts with rank 1 will for sure be part of this payment. there may be more but we start there.
        # If there is a next account, record that amount of marginal interest.
        # Compute what the balances for the currently considered loans must be in order to imply the corresponding amount of marginal interest.
        # If the total amount needed is greater than the amount, then allocate the current payment between the considered loans in proprotion to their current balances.
        # otherwise, implement a payment of the needed amounts, and recurse with new initial conditions

        A = account_set.getAccounts()
        principal_accts_df = A[A.Account_Type == 'principal balance']
        interest_accts_df = A[A.Account_Type == 'interest']

        all_account_names__1 = [ x.split(':') for x in principal_accts_df.Name ]
        all_account_names__2 = [name for sublist in all_account_names__1 for name in sublist]
        all_account_names = set(all_account_names__2) - set([' Principal Balance'])

        final_payment_amounts__BudgetSet = BudgetSet.BudgetSet([])

        grand_total_owed = sum(principal_accts_df.Balance) + sum(interest_accts_df.Balance)

        if amount > grand_total_owed:
            amount = grand_total_owed

        if partial_payment_budget_set is not None:
            #print('partial_payment_budget_set.getBudgetItems():')
            #print(partial_payment_budget_set.getBudgetItems().to_string())

            grand_total_allocated = sum(partial_payment_budget_set.getBudgetItems().Amount)

            if sum(partial_payment_budget_set.getBudgetItems().Amount) == amount:
                #algorithm complete!
                return partial_payment_budget_set
            elif sum(partial_payment_budget_set.getBudgetItems().Amount) > amount:
                print(left_prefix+'The allocate_loan_payments algorithm has somehow allocated more than the amount being paid')
                return None
            else:
                print(left_prefix+'Allocated amounts are less than total amount to pay')
                pass
                #continue the recursize algorithm
        else:
            grand_total_allocated = 0

        total_amount_per_loan = {}
        for acct_name in all_account_names:

            principal_amt = principal_accts_df.iloc[ [acct_name in pa_element for pa_element in principal_accts_df.Name] , : ].Balance.iloc[0]
            interest_amt = interest_accts_df.iloc[ [acct_name in pa_element for pa_element in principal_accts_df.Name], :].Balance.iloc[0]

            total_amount_per_loan[acct_name] = principal_amt + interest_amt

        if amount == grand_total_owed:
            print(left_prefix+'Case 1: The amount to pay is equal to the grand total owed')
            for acct_name in all_account_names:
                final_payment_amounts__BudgetSet.addBudgetItem(start_date_YYYYMMDD=date_string_YYYYMMDD,
                                                               end_date_YYYYMMDD=date_string_YYYYMMDD,
                                                               priority=7,
                                                                cadence='once',
                                                               amount=total_amount_per_loan[acct_name],
                                                               memo=acct_name+' additional payments',
                                                                deferrable=False)

            return final_payment_amounts__BudgetSet
        else:
            #the amount of the payment is less than the grand total
            principal_accts_df['Marginal Interest'] = [ round(x,2) for x in (principal_accts_df.Balance * principal_accts_df.APR) ]

            principal_accts_df.sort_values(by='Marginal Interest', inplace=True, ascending=False)
            principal_accts_df['Marginal Interest Rank'] = principal_accts_df['Marginal Interest'].rank(method='dense',ascending=False)
            #print(principal_accts_df.to_string())

            highest_marginal_interest_df = principal_accts_df[principal_accts_df['Marginal Interest Rank'] == 1]
            second_highest_marginal_interest_df = principal_accts_df[principal_accts_df['Marginal Interest Rank'] == 2]

            highest_marginal_interest_acct_name = highest_marginal_interest_df.Name.iloc[0].split(':')[0]
            second_highest_marginal_interest_acct_name = second_highest_marginal_interest_df.Name.iloc[0].split(':')[0]

            #print(highest_marginal_interest_df)
            #print(highest_marginal_interest_acct_name)

            #print(second_highest_marginal_interest_df)
            #print(second_highest_marginal_interest_acct_name)

            # if there is only 1 acct to pay first, and 0 accts in second place
            if highest_marginal_interest_df.shape[0] == 1 and second_highest_marginal_interest_df.shape[0] == 1:
                print(left_prefix+'Case 2: there is only 1 acct to pay first, and 0 accts in second place')
                amount_to_pay = min(total_amount_per_loan[highest_marginal_interest_acct_name],amount)

                final_payment_amounts__BudgetSet.addBudgetItem(start_date_YYYYMMDD=date_string_YYYYMMDD,
                                                               end_date_YYYYMMDD=date_string_YYYYMMDD,
                                                               priority=7,
                                                               cadence='once',
                                                               amount=amount_to_pay,
                                                               memo=acct_name + ' additional payments',
                                                               deferrable=False)

                account_set.executeTransaction(Account_From=None,Account_To=acct_name,Amount=amount_to_pay)
                amount = amount - amount_to_pay

                # LEFT OFF HERE

                recursion_depth = recursion_depth + 1
                final_payment_amounts__BudgetSet = self.allocate_loan_payments(account_set, amount, date_string_YYYYMMDD, recursion_depth, partial_payment_budget_set=final_payment_amounts__BudgetSet)
                return final_payment_amounts__BudgetSet

            # if there is only 1 acct to pay first, and at least 1 acct in second place
            elif highest_marginal_interest_df.shape[0] == 1 and second_highest_marginal_interest_df.shape[0] > 1:
                print(left_prefix + 'Case 3: there is only 1 acct to pay first, and at least 1 acct in second place')

                #the min in denominator is just to get a scalar from a vector. all vals are the same
                highest_loan_bifurcation_balance = highest_marginal_interest_df['Marginal Interest'].iloc[0] / min([ x for x in second_highest_marginal_interest_df.APR ])
                print(left_prefix+'highest_loan_bifurcation_balance:'+str(highest_loan_bifurcation_balance))

                return None

            # multiple accts to pay first, and no other accts to pay
            elif highest_marginal_interest_df.shape[0] == 1 and second_highest_marginal_interest_df.shape[0] == 0:
                print(left_prefix + 'Case 4: multiple accts to pay first, and no other accts to pay')

                return None

            # multiple accts to pay first, and at least 1 other acct to pay
            elif highest_marginal_interest_df.shape[0] == 1 and second_highest_marginal_interest_df.shape[0] == 0:
                print(left_prefix + 'Case 5: multiple accts to pay first, and at least 1 other acct to pay')

                return None

            else:
                print('UNDEFINED EDGE CASE IN ExpenseForecast::allocate_loan_payments()')
                return None




    def computeOptimalForecast(self,budget_set, account_set, memo_rule_set):
        """
        One-description.

        Multiple line dsecription.

        | Test Cases
        | Expected Successes
        | S1: ... #todo refactor ExpenseForecast.computeOptimalForecast() doctest S1 to use _S1 label
        |
        | Expected Fails
        | F1 ... #todo refactor ExpenseForecast.computeOptimalForecast() doctest F1 to use _F1 label

        :param budget_schedule_df:
        :param account_set_df:
        :param memo_rules_df:
        :return:
        """

        compute_forecast__list = self.computeForecast(budget_set, account_set, memo_rule_set)
        updated_budget_schedule_df = compute_forecast__list[0] #todo make sure this is sorted by amount descending
        account_set_df = compute_forecast__list[1]
        forecast_df = compute_forecast__list[2]

        memo_rules_df = self.initial_memo_rule_set.getMemoRules()

        print('ENTER computeOptimalForecast()')
        unique_priority_indices = updated_budget_schedule_df.Priority.unique()
        for priority_index in unique_priority_indices:

            for budget_item_index, budget_item_row in updated_budget_schedule_df.iterrows():
                print(budget_item_row)

                found_matching_regex = False
                transaction_was_executed = False
                relevant_memo_rules_rows_df = memo_rules_df[memo_rules_df.transaction_priority == priority_index]
                print(relevant_memo_rules_rows_df)
                for memo_rules_index, memo_rules_row in relevant_memo_rules_rows_df.iterrows():

                    memo_regex_match = re.search(memo_rules_row.memo_regex, budget_item_row.Memo)

                    if memo_regex_match is not None:
                        # do stuff

                        row_w_date_of_proposed_transaction = forecast_df[forecast_df.Date == budget_item_row.Date]
                        print(row_w_date_of_proposed_transaction)

                        # todo computeOptimalForecast():: the decision has to be made whether or not to execute the transaction

                        #` evaluate_free_balance

                        account_set.executeTransaction(memo_rules_row.Account_From, memo_rules_row.Account_To, budget_item_row.Amount)
                        transaction_was_executed = True

                        # if memo_rules_row.account_from is not None:
                        #     index_of_account_from_column = list(row_w_date_of_proposed_transaction.columns).index(memo_rules_row.account_from)
                        #
                        # if memo_rules_row.account_to is not None:
                        #     index_of_account_to_column = list(row_w_date_of_proposed_transaction.columns).index(memo_rules_row.account_to)






                        # if memo_rules_row.account_from is not None and memo_rules_row.account_to is None:  # e.g. income
                        #     row_w_date_of_proposed_transaction.iloc[0, index_of_account_from_column] += budget_item_row.Amount #execute transaction
                        #     transaction_was_executed = True
                        # elif memo_rules_row.account_to is not None and memo_rules_row.account_from is None:  # e.g. spend
                        #     row_w_date_of_proposed_transaction.iloc[0, index_of_account_to_column] += budget_item_row.Amount
                        #     transaction_was_executed = True
                        # elif memo_rules_row.account_from is not None and memo_rules_row.account_to is not None:  # e.g. xfer bw accts
                        #     row_w_date_of_proposed_transaction.iloc[0, index_of_account_to_column] += budget_item_row.Amount
                        #     row_w_date_of_proposed_transaction.iloc[0, index_of_account_from_column] -= budget_item_row.Amount
                        #     transaction_was_executed = True
                        # else:
                        #     transaction_was_executed = False #this is redundant, but included so code is readable

                        found_matching_regex = True
                        break

                    if not found_matching_regex:
                        print(
                            'We received a budget item that we do not have a case to handle. this is a show stopping error.')
                        print('Exiting.')
                    else:  # update memo
                        if row_w_date_of_proposed_transaction.loc[0, 'Memo'] != '':
                            row_w_date_of_proposed_transaction.loc[0, 'Memo'] = row_w_date_of_proposed_transaction.loc[0, 'Memo'] + '; '

                        new_memo_text = budget_item_row.Memo + ' , '
                        if memo_rules_row.account_from is not None:
                            new_memo_text = new_memo_text + str(memo_rules_row.account_from) + ' ' + str(
                                -1 * abs(budget_item_row.Amount)) + ' '

                        if memo_rules_row.account_to is not None:
                            new_memo_text = new_memo_text + str(memo_rules_row.account_to) + ' ' + str(budget_item_row.Amount) + ' '

                        row_w_date_of_proposed_transaction.loc[0, 'Memo'] = row_w_date_of_proposed_transaction.loc[0, 'Memo'] + new_memo_text

                if transaction_was_executed:
                    #todo computeOptimalForecast(): resatisficing must occur
                    #the row in question has been changed. we keep the row w the transaction and all previous rows.
                    #we submit all later rows for re-satsificing
                    #Note that computeForecast returns the first row the same as it was submitted, so we keep only
                    #those rows w less than date, and for the date = same as transaction and alter, we submit to computeForecast

                    date_of_transaction_df = row_w_date_of_proposed_transaction.iloc[0,0]
                    rows_to_keep_df = forecast_df[forecast_df.Date < date_of_transaction_df.Date]

                    #computeForecast iterates over budget schedule items to determine the date, so we filter the budget schedule items
                    only_future_budget_schedule_df = budget_schedule_df[budget_schedule_df.Date > date_of_transaction_df.Date]

                    #account initial balances must match the first row of the forecast that we submit

                    print(account_set_df)
                    print(row_w_date_of_proposed_transaction)

                    #memo rules are the same

                    recomputed_forecast_rows_df = self.computeForecast(only_future_budget_schedule_df, account_set_df, memo_rules_df)



















        return forecast_df
        #return self.computeForecast(budget_schedule_df, account_set_df, memo_rules_df)


    def plotOverall(self,forecast_df,output_path):
        """
        Writes to file a plot of all accounts.

        Multiple line description.


        :param forecast_df:
        :param output_path:
        :return:
        """
        figure(figsize=(14, 6), dpi=80)
        for i in range(1, forecast_df.shape[1] - 1):
            plt.plot(forecast_df['Date'], forecast_df.iloc[:, i], label=forecast_df.columns[i])

        ax = plt.subplot(111)
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.1,
                         box.width, box.height * 0.9])

        # Put a legend below current axis
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05),
                  fancybox=True, shadow=True, ncol=4)

        # TODO plotOverall():: a large number of accounts will require some adjustment here so that the legend is entirely visible

        min_date = min(forecast_df.Date).strftime('%Y-%m-%d')
        max_date = max(forecast_df.Date).strftime('%Y-%m-%d')
        plt.title('Forecast: ' + str(min_date) + ' -> ' + str(max_date))
        plt.savefig(output_path)

    def plotAccountTypeTotals(self,forecast_df,output_path):
        """
        Writes to file a plot by account type.

        | Test Cases
        | Expected Successes
        | S1: ... #todo refactor ExpenseForecast.plotAccountTypeTotals() doctest S1 to use _S1 label
        |
        | Expected Fails
        | F1 ... #todo refactor ExpenseForecast.plotAccountTypeTotals() doctest F1 to use _F1 label

        :param forecast_df:
        :param output_path:
        :return:
        """
        #aggregate by account type: Principal Balance + interest, checking, previous + current statement balance, savings
        checking_df = pd.DataFrame(forecast_df.Checking.copy())
        savings_df = pd.DataFrame(forecast_df.Savings.copy())
        date_df = pd.DataFrame(forecast_df.Date.copy())

        zero_df = pd.DataFrame(np.zeros((checking_df.shape[0], 1)))
        cc_df = pd.DataFrame(zero_df.copy())
        loan_df = pd.DataFrame(zero_df.copy())

        cc_colnames = [s for s in forecast_df.columns.tolist() if 'Statement Balance' in s]
        loan_colnames = [s for s in forecast_df.columns.tolist() if 'Interest' in s] + [s for s in forecast_df.columns.tolist() if 'Principal Balance' in s]

        cc_df = pd.DataFrame(forecast_df.loc[:,cc_colnames].sum(axis=1))

        loan_df = pd.DataFrame(forecast_df.loc[:,loan_colnames].sum(axis=1))

        date_df.reset_index(drop=True,inplace=True)
        checking_df.reset_index(drop=True,inplace=True)
        savings_df.reset_index(drop=True,inplace=True)
        cc_df.reset_index(drop=True,inplace=True)
        loan_df.reset_index(drop=True,inplace=True)

        loan_df = loan_df.rename(columns={0:"Loan"})
        cc_df = cc_df.rename(columns={0: "Credit"})

        agg_df = pd.concat([date_df,checking_df,savings_df,cc_df,loan_df],axis=1)

        figure(figsize=(14, 6), dpi=80)
        for i in range(1, agg_df.shape[1]):
            plt.plot(agg_df['Date'], agg_df.iloc[:, i], label=agg_df.columns[i])

        ax = plt.subplot(111)
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.1,
                         box.width, box.height * 0.9])

        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05),
                  fancybox=True, shadow=True, ncol=4)

        min_date = min(forecast_df.Date).strftime('%Y-%m-%d')
        max_date = max(forecast_df.Date).strftime('%Y-%m-%d')

        plt.title('Account Type Totals: ' + str(min_date) + ' -> ' + str(max_date))
        plt.savefig(output_path)

    def plotMarginalInterest(self,accounts_df,forecast_df,output_path):
        """
        Writes a plot of spend on interest from all sources.

        Multiple line description.

        | Test Cases
        | Expected Successes
        | S1: ... #todo refactor ExpenseForecast.plotMarginalInterest() doctest S1 to use _S1 label
        |
        | Expected Fails
        | F1 ... #todo refactor ExpenseForecast.plotMarginalInterest() doctest F1 to use _F1 label


        :param accounts_df:
        :param forecast_df:
        :param output_path:
        :return:
        """
        #todo plotMarginalInterest():: this will have to get the cc interest from the memo line
        raise NotImplementedError

    def toJSON(self):
        """
        Returns a JSON string representing the ExpenseForecast object.

        #todo ExpenseForecast.toJSON() say what the columns are

        :return:
        """
        raise NotImplementedError

    def to_html(self):
        return self.forecast_df.to_html()

    def compute_forecast_difference(self,forecast2_df,
                                    label='forecast_difference',
                                    make_plots=False,
                                    plot_directory='.',
                                    return_type='dataframe',
                                    require_matching_columns=False,
                                    require_matching_date_range=False,
                                    append_expected_values=False,
                                    diffs_only=False):

        self.forecast_df = self.forecast_df.reindex(sorted(self.forecast_df.columns), axis=1)
        forecast2_df = forecast2_df.reindex(sorted(forecast2_df.columns), axis=1)

        self.forecast_df.reset_index(inplace=True,drop=True)
        forecast2_df.reset_index(inplace=True,drop=True)

        # print('self.forecast_df:')
        # print(self.forecast_df)
        # print('')
        # print('forecast2_df:')
        # print(forecast2_df)

        #return_type in ['dataframe','html','both']
        #make
        #I want the html table to have a row with values all '...' for non-consecutive dates
        #Data frame will not return rows that match

        if require_matching_columns:
            try:
                assert self.forecast_df.shape[1] == forecast2_df.shape[1]
                assert set(self.forecast_df.columns) == set(forecast2_df.columns)
            except Exception as e:
                print('ERROR: ATTEMPTED TO TAKE DIFF OF FORECASTS WITH DIFFERENT COLUMNS')
                #print('# Check Number of Columns:')
                #print('self.forecast_df.shape[1]:'+str(self.forecast_df.shape[1]))
                #print('forecast2_df.shape[1]....:'+str(forecast2_df.shape[1]))
                #print('')
                #print('# Check Column Names:')
                #print('set(self.forecast_df.columns):'+str(set(self.forecast_df.columns) ))
                #print('set(forecast2_df.columns)....:'+str(set(forecast2_df.columns)))
                #print('')
                raise e

        if require_matching_date_range:
            try:
                assert min(self.forecast_df['Date']) == min(forecast2_df['Date'])
                assert max(self.forecast_df['Date']) == max(forecast2_df['Date'])
            except Exception as e:
                print('ERROR: ATTEMPTED TO TAKE DIFF OF FORECASTS WITH DIFFERENT DATE RANGE')
                print( 'LHS: ' +  str(min(self.forecast_df['Date'])) + ' - ' + str(max(self.forecast_df['Date'])) )
                print( 'RHS: ' + str(min(forecast2_df['Date'])) + ' - ' + str(max(forecast2_df['Date'])) )
                #print('# Check Min Date Range:')
                #print('min(self.forecast_df[\'Date\']):'+str())
                #print('min(forecast_df2[\'Date\']):'+str())
                #print('')
                #print('# Check Max Date Range:')
                #print('max(self.forecast_df[\'Date\']):'+str())
                #print('max(forecast_df2[\'Date\']):'+str())
                #print('')
                raise e

        if diffs_only == True:
            return_df = self.forecast_df[['Date','Memo']].copy()
        else:
            return_df = self.forecast_df.copy()
        return_df.reset_index(inplace=True,drop=True)

        #print(return_df.columns)
        #print('BEFORE return_df:\n' + return_df.to_string())

        # TODO align date range
        relevant_column_names__set = set(self.forecast_df.columns) - set(['Date','Memo'])
        #print('relevant_column_names__set:'+str(relevant_column_names__set))
        for c in relevant_column_names__set:
            new_column_name = c+' (Diff) '
            #print('new_column_name:'+str(new_column_name))
            res = pd.DataFrame( forecast2_df[c] - self.forecast_df[c] )
            #res = forecast2_df[c].sub(self.forecast_df[c])
            res.reset_index(inplace=True,drop=True)
            #print('res:'+str(res))
            return_df[new_column_name] = res

        if append_expected_values:
            for cname in forecast2_df.columns:
                if cname == 'Memo' or cname == 'Date':
                    continue
                return_df[cname+' (Expected)'] = forecast2_df[cname]

        return_df.index = return_df['Date']

        #print(return_df.columns)
        #print('AFTER return_df:\n' + return_df.to_string())

        # print('#########')
        # print('forecast2_df')
        # print(forecast2_df[c])
        #
        # print('#########')
        # print('self.forecast_df')
        # print(self.forecast_df[c])
        #
        # print('#########')
        # print('forecast2_df[c].sub(self.forecast_df[c])')
        # print(forecast2_df[c].sub(self.forecast_df[c]))
        #
        # print(return_df)

        if make_plots:
            pass
            #todo draw plots

        return return_df






#written in one line so that test coverage can reach 100%
#if __name__ == "__main__": import doctest ; doctest.testmod()
if __name__ == "__main__":
    pass

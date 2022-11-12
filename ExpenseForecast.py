
import pandas as pd, numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
import datetime
import re
from hd_util import *

class ExpenseForecast:

    def __init__(self,account_set,budget_set,memo_rule_set,start_date_YYYYMMDD,end_date_YYYYMMDD):
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

        #todo datetime validation in ExpenseForecast.ExpenseForecast()
        self.start_date = datetime.datetime.strptime(start_date_YYYYMMDD,'%Y%m%d')
        self.end_date = datetime.datetime.strptime(end_date_YYYYMMDD,'%Y%m%d')

        accounts_df = account_set.getAccounts()
        budget_df = budget_set.getBudgetItems()
        memo_df = memo_rule_set.getMemoRules()

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
            assert set(distinct_account_names__from_memo.Name).intersection(set(distinct_base_account_names__from_acct.Name)) == set(distinct_account_names__from_memo.Name)
        except:
            print('An account name was mentioned in a memo rule that did not exist in the account set')
            print('all accounts mentioned in memo rules:')
            print(distinct_account_names__from_memo)
            print('all defined accounts:')
            print(distinct_base_account_names__from_acct)
            error_ind = True

        #for each budget item memo x priority combo, there is at least 1 memo_regex x priority that matches
        distinct_memo_priority_combinations__from_budget = budget_df[['Priority', 'Memo']].drop_duplicates()
        distinct_memo_priority_combinations__from_memo = memo_df[['Transaction_Priority', 'Memo_Regex']] #should be no duplicates

        any_matches_found_at_all = False
        error_text=""
        for budget_index, budget_row in distinct_memo_priority_combinations__from_budget.iterrows():
            match_found = False
            for memo_index, memo_row in distinct_memo_priority_combinations__from_memo.iterrows():
                if budget_row.Priority == memo_row.Transaction_Priority:
                    m = re.search(memo_row.Memo_Regex, budget_row.Memo)
                    if m is not None:
                        match_found = True
                        continue

            if match_found == False:
                error_text += "No regex match found for memo:\'"+str(budget_row.Memo)+"\'\n"

        if error_text != "":
            print(error_text)
            error_ind = True

        smpl_sel_vec = accounts_df.Interest_Type.apply(lambda x: x.lower() if x is not None else None) == 'simple'
        cmpnd_sel_vec = accounts_df.Interest_Type.apply(lambda x: x.lower() if x is not None else None) == 'compound'


        # for each account with interest_type == 'Simple', there should be principal balance and an interest acct
        distinct_simple_interest_bearing_accounts = pd.DataFrame(accounts_df.loc[smpl_sel_vec,'Name'])
        #print(distinct_simple_interest_bearing_accounts.to_string())
        #todo implement test: for each account with interest_type == 'Simple', there should be principal balance and an interest acct

        #for each account with interest_type == 'Compound', there should be prev bal and curr bal accts
        distinct_compound_interest_bearing_accounts = pd.DataFrame(accounts_df.loc[cmpnd_sel_vec,'Name'])
        #print(distinct_compound_interest_bearing_accounts.to_string())
        #todo implement test: for each account with interest_type == 'Compound', there should be prev bal and curr bal accts

        error_text_string = ""
        error_ind = False

        if error_ind:
            print(error_text_string)
            raise ValueError

        self.initial_account_set = account_set
        self.initial_budget_set = budget_set
        self.initial_memo_rule_set = memo_rule_set

        self.forecast_df = self.computeForecast(account_set, budget_set, memo_rule_set)

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

        date_only_df = pd.DataFrame(['Date', min_sched_date]).T

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

    def executeTransactionsForDay(self,budget_schedule_df,memo_rule_set,current_forecast_row_df):

        #all transactions should be executed. This method does no error checking because that should happen upstream.
        #We could include account_df info here, but I don't think it is necessary

        #making minimum payments should be determined by memo rules instead of hard-coded as checking

        #returns a single forecast row with updated memo
        raise NotImplementedError

    def calculateInterestAccrualsForDay(self,account_df,current_forecast_row_df):

        # accounts that receive interest accruals should be selected by interest type, not by account type
        # Note that account balances are passed to this method, but they are irrelevant.
        # We refer to current_forecast_row_df for balances, and to account_df for interest accrual details

        #Note also that this method will transfer balances from current statement to previous statement for savings
        # and credit accounts

        # returns a single forecast row with updated memo
        raise NotImplementedError

    def computeForecast(self, budget_set, account_set, memo_rule_set):
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
        memo_df = self.initial_memo_rule_set.getMemoRules() #this never changes
        initial_forecast_row_df = self.getInitialForecastRow()
        account_set_df = self.initial_account_set.getAccounts()

        for d in all_days:
          if d == self.start_date:
              forecast_df = initial_forecast_row_df
              continue #because we consider the input values for the first day to be final

          this_days_budget_schedule_df = None

          new_forecast_row_df = self.executeTransactionsForDay(this_days_budget_schedule_df, memo_df,previous_row_df) #returns only a forecast row w updated memo
          new_forecast_row_df = self.calculateInterestAccrualsForDay( account_set_df,new_forecast_row_df ) #returns only a forecast row w updated memo

          forecast_df = pd.concat([forecast_df,new_forecast_row_df])
          previous_row_df = new_forecast_row_df



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

    def decide__defer_or_execute_or_skip(self,updated_budget_schedule_df,account_set_df,forecast_df):
        """
        Returns an empty row (execute or skip), or an updated <DataFrame> of BudgetItems.

        This method accepts a single BudgetItem, along with the AccountSet and Forecast.

        | Test Cases
        | Expected Successes
        | S1: ... #todo refactor ExpenseForecast.decide__defer_or_execute_or_skip() doctest S1 to use _S1 label
        |
        | Expected Fails
        | F1 ... #todo refactor ExpenseForecast.decide__defer_or_execute_or_skip() doctest F1 to use _F1 label

        :param updated_budget_schedule_df:
        :param account_set_df:
        :param forecast_df:
        :return:
        """
        updated_account_set_df = account_set_df
        updated_forecast_df = forecast_df

        #this needs to be able to accept "*", meaning "free balance"


        updated_budget_schedule_df.sort_values(inplace=True, axis=0, by="Date")
        updated_budget_schedule_df.reset_index(inplace=True, drop=True)

        return [updated_budget_schedule_df,account_set_df,forecast_df]



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

        computeForecastd_forecast__list = self.computeForecast(budget_set, account_set, memo_rule_set)
        updated_budget_schedule_df = computeForecastd_forecast__list[0]
        account_set_df = computeForecastd_forecast__list[1]
        forecast_df = computeForecastd_forecast__list[2]

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

                        if memo_rules_row.account_from is not None:
                            index_of_account_from_column = list(row_w_date_of_proposed_transaction.columns).index(memo_rules_row.account_from)

                        if memo_rules_row.account_to is not None:
                            index_of_account_to_column = list(row_w_date_of_proposed_transaction.columns).index(memo_rules_row.account_to)


                        #todo computeOptimalForecast():: the decision has to be made whether or not to execute the transaction
                        if memo_rules_row.account_from is not None and memo_rules_row.account_to is None:  # e.g. income
                            row_w_date_of_proposed_transaction.iloc[0, index_of_account_from_column] += budget_item_row.Amount
                            transaction_was_executed = True
                        elif memo_rules_row.account_to is not None and memo_rules_row.account_from is None:  # e.g. spend
                            row_w_date_of_proposed_transaction.iloc[0, index_of_account_to_column] += budget_item_row.Amount
                            transaction_was_executed = True
                        elif memo_rules_row.account_from is not None and memo_rules_row.account_to is not None:  # e.g. xfer bw accts
                            row_w_date_of_proposed_transaction.iloc[0, index_of_account_to_column] += budget_item_row.Amount
                            row_w_date_of_proposed_transaction.iloc[0, index_of_account_from_column] -= budget_item_row.Amount
                            transaction_was_executed = True
                        else:
                            transaction_was_executed = False #this is redundant, but included so code is readable

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

                    recomputeForecastd_rows_df = self.computeForecast(only_future_budget_schedule_df, account_set_df, memo_rules_df)



















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



#written in one line so that test coverage can reach 100%
if __name__ == "__main__": import doctest ; doctest.testmod()
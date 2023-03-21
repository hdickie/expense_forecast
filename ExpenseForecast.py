import pandas as pd, numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
import datetime
import re
import copy

import BudgetSet, BudgetItem

from log_methods import log_in_color


def generate_date_sequence(start_date_YYYYMMDD, num_days, cadence):
    """ A wrapper for pd.date_range intended to make code easier to read.

    #todo write project_utilities.generate_date_sequence() doctests
    """
    # print('generate_date_sequence():')
    # print('start_date_YYYYMMDD:'+str(start_date_YYYYMMDD))
    # print('num_days...........:'+str(num_days))
    # print('cadence............:'+str(cadence))

    start_date = datetime.datetime.strptime(start_date_YYYYMMDD, '%Y%m%d')
    end_date = start_date + datetime.timedelta(days=num_days)

    if cadence.lower() == "once":
        return pd.Series(start_date)
    elif cadence.lower() == "daily":
        return_series = pd.date_range(start_date, end_date, freq='D')
    elif cadence.lower() == "weekly":
        return_series = pd.date_range(start_date, end_date, freq='W')
    elif cadence.lower() == "biweekly":
        return_series = pd.date_range(start_date, end_date, freq='2W')
    elif cadence.lower() == "monthly":

        day_delta = int(start_date.strftime('%d')) - 1
        first_of_each_relevant_month = pd.date_range(start_date, end_date, freq='MS')

        return_series = first_of_each_relevant_month + datetime.timedelta(days=day_delta)
    elif cadence.lower() == "quarterly":
        # todo check if this needs an adjustment like the monthly case did
        return_series = pd.date_range(start_date, end_date, freq='Q')
    elif cadence.lower() == "yearly":
        # todo check if this needs an adjustment like the monthly case did
        return_series = pd.date_range(start_date, end_date, freq='Y')

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
        # print('Starting Expense Forecast...\n')

        try:
            self.start_date = datetime.datetime.strptime(start_date_YYYYMMDD, '%Y%m%d')
        except:
            print('value was:' + str(start_date_YYYYMMDD) + '\n')
            raise ValueError  # Failed to cast start_date_YYYYMMDD to datetime with format %Y%m%d

        try:
            self.end_date = datetime.datetime.strptime(end_date_YYYYMMDD, '%Y%m%d')
        except:
            raise ValueError  # Failed to cast end_date_YYYYMMDD to datetime with format %Y%m%d

        if self.start_date >= self.end_date:
            raise ValueError  # start_date must be before end_date

        accounts_df = account_set.getAccounts()
        if accounts_df.shape[0] == 0:
            # if len(account_set) == 0:
            raise ValueError  # There needs to be at least 1 account for ExpenseForecast to do anything.
        # todo more strict checking

        budget_df = budget_set.getBudgetItems()
        memo_df = memo_rule_set.getMemoRules()

        error_text = ""
        error_ind = False

        # for each distinct account name in all memo rules to and from fields, there is a matching account
        # that is, for each memo rule that mentions an account, the mentioned account should exist
        # not that it is NOT a requirement that the converse is true
        # that is, there can be an account that has no corresponding memo rules

        # should be no duplicates and credit and loan acct splitting is already handled

        distinct_base_account_names__from_acct = pd.DataFrame(
            pd.DataFrame(accounts_df[['Name']]).apply(lambda x: x[0].split(':')[0], axis=1).drop_duplicates()).rename(
            columns={0: 'Name'})
        account_names__from_memo = pd.concat(
            [pd.DataFrame(memo_df[['Account_From']]).rename(columns={'Account_From': 'Name'}),
             pd.DataFrame(memo_df[['Account_To']]).rename(columns={'Account_To': 'Name'})])

        distinct_account_names__from_memo = pd.DataFrame(
            account_names__from_memo.loc[account_names__from_memo.Name != 'None', 'Name'].drop_duplicates().reset_index(
                drop=True))

        try:
            A = set(distinct_account_names__from_memo.Name).union(set(['']))
            B = set(distinct_account_names__from_memo.Name).intersection(
                set(distinct_base_account_names__from_acct.Name)).union(set(['']))
            assert A == B
        except:
            error_text += 'An account name was mentioned in a memo rule that did not exist in the account set\n'
            error_text += 'all accounts mentioned in memo rules:\n'
            error_text += distinct_account_names__from_memo.Name.to_string() + '\n'
            error_text += 'all defined accounts:\n'
            error_text += distinct_base_account_names__from_acct.Name.to_string() + '\n'
            error_text += 'intersection:\n'
            error_text += str(B) + '\n'
            error_text += 'Accounts from Memo:\n'
            error_text += str(A) + '\n'
            error_ind = True

        # for each budget item memo x priority combo, there is at least 1 memo_regex x priority that matches
        distinct_memo_priority_combinations__from_budget = budget_df[['Priority', 'Memo']].drop_duplicates()
        distinct_memo_priority_combinations__from_memo = memo_df[
            ['Transaction_Priority', 'Memo_Regex']]  # should be no duplicates

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
                error_text += "No regex match found for memo:\'" + str(budget_row.Memo) + "\'\n"

        if any_matches_found_at_all == False:
            error_ind = True

        smpl_sel_vec = accounts_df.Interest_Type.apply(lambda x: x.lower() if x is not None else None) == 'simple'
        cmpnd_sel_vec = accounts_df.Interest_Type.apply(lambda x: x.lower() if x is not None else None) == 'compound'

        if print_debug_messages:
            if error_ind: print(error_text)

        if raise_exceptions:
            if error_ind:
                raise ValueError

        self.initial_account_set = copy.deepcopy(account_set)
        self.initial_budget_set = copy.deepcopy(budget_set)
        self.initial_memo_rule_set = copy.deepcopy(memo_rule_set)

        # forecast_df = self.getInitialForecastRow()
        #
        # deferred_df = pd.DataFrame(
        #     {'Date': [], 'Priority': [], 'Amount': [], 'Memo': [], 'Deferrable': [], 'Partial_Payment_Allowed': []})
        # skipped_df = pd.DataFrame(
        #     {'Date': [], 'Priority': [], 'Amount': [], 'Memo': [], 'Deferrable': [], 'Partial_Payment_Allowed': []})
        # confirmed_df = pd.DataFrame(
        #     {'Date': [], 'Priority': [], 'Amount': [], 'Memo': [], 'Deferrable': [], 'Partial_Payment_Allowed': []})

        self.log_stack_depth = 0

        proposed_df = budget_set.getBudgetSchedule(start_date_YYYYMMDD, end_date_YYYYMMDD)
        confirmed_df = copy.deepcopy(proposed_df.head(0))
        deferred_df = copy.deepcopy(proposed_df.head(0))
        skipped_df = copy.deepcopy(proposed_df.head(0))


        forecast_df, skipped_df, confirmed_df, deferred_df = self.computeOptimalForecast(start_date_YYYYMMDD=start_date_YYYYMMDD,
                                                                                         end_date_YYYYMMDD=end_date_YYYYMMDD,
                                                                                         confirmed_df=confirmed_df,
                                                                                         proposed_df=proposed_df,
                                                                                         deferred_df=deferred_df,
                                                                                         skipped_df=skipped_df,
                                                                                         account_set=account_set,
                                                                                         memo_rule_set=memo_rule_set)
        self.forecast_df = forecast_df
        self.skipped_df = skipped_df
        self.confirmed_df = confirmed_df
        self.deferred_df = deferred_df

        # print('self.forecast_df:')
        # print(self.forecast_df.to_string())

        try:
            assert (min(forecast_df.Date) == datetime.datetime.strptime(start_date_YYYYMMDD, '%Y%m%d'))
        except AssertionError as e:
            raise ValueError("""
                        ExpenseForecast() did not include the first day as specified.
                        start_date_YYYYMMDD=""" + str(start_date_YYYYMMDD) + """
                        min(forecast_df.Date)=""" + str(min(forecast_df.Date)) + """
                        """)

        try:
            assert (max(forecast_df.Date) == datetime.datetime.strptime(end_date_YYYYMMDD, '%Y%m%d'))
        except AssertionError as e:
            raise ValueError("""
                        ExpenseForecast() did not include the last day as specified.
                        end_date_YYYYMMDD=""" + str(end_date_YYYYMMDD) + """
                        max(forecast_df.Date)=""" + str(max(forecast_df.Date)) + """
                        """)

        self.forecast_df.index = self.forecast_df['Date']

        # write all_data.csv
        # self.forecast_df.iloc[:,0:(self.forecast_df.shape[1]-1)].to_csv('all_data.csv',index=False)

        # self.forecast_df.to_csv('out.csv', index=False)

    #
    # def account_boundaries_are_violated(self,accounts_df,forecast_df):
    #     """
    #     account_boundaries_are_violated single-line description
    #
    #     #todo ExpenseForecast.account_boundaries_are_violated() doctests
    #     | Test Cases
    #     | Expected Successes
    #     | S1: ... #todo refactor ExpenseForecast.account_boundaries_are_violated() doctest S1 to use _S1 label
    #     |
    #     | Expected Fails
    #     | F1 ... #todo refactor ExpenseForecast.account_boundaries_are_violated() doctest F1 to use _F1 label
    #
    #     :param accounts_df:
    #     :param forecast_df:
    #     :return:
    #     """
    #     for col_name in forecast_df.columns.tolist():
    #         if col_name == 'Date' or col_name == 'Memo':
    #             continue
    #
    #         current_column = forecast_df[col_name]
    #
    #         acct_boundary__min = float(accounts_df.loc[accounts_df.Name == col_name,'Min_Balance'])
    #         acct_boundary__max = float(accounts_df.loc[accounts_df.Name == col_name, 'Max_Balance'])
    #
    #         min_in_forecast_for_acct = min(current_column)
    #         max_in_forecast_for_acct = max(current_column)
    #
    #         try:
    #             # print(current_column)
    #             # print('min_in_forecast_for_acct:'+str(min_in_forecast_for_acct))
    #             # print('max_in_forecast_for_acct:' + str(max_in_forecast_for_acct))
    #             # print('acct_boundary__min:' + str(acct_boundary__min))
    #             # print('acct_boundary__max:' + str(acct_boundary__max))
    #             # print('')
    #             # print('')
    #
    #             assert float(min_in_forecast_for_acct) >= float(acct_boundary__min)
    #             assert float(max_in_forecast_for_acct) <= float(acct_boundary__max)
    #
    #         except Exception as e:
    #
    #             offending_rows__min = forecast_df[current_column < acct_boundary__min]
    #             offending_rows__max = forecast_df[current_column > acct_boundary__max]
    #
    #             # print(e)
    #             # print('Account Boundary Violation for '+str(col_name)+' in ExpenseForecast.account_boundaries_are_violated()')
    #             # print('Offending Rows: Minimum')
    #             # print(offending_rows__min.to_string())
    #             # print('Offending Rows: Maximum')
    #             # print(offending_rows__max.to_string())
    #             return True
    #     return False
    #
    #

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

    def executeTransactionsForDay(self, account_set,
                                  forecast_df,
                                  date_YYYYMMDD,
                                  memo_set,
                                  confirmed_df,
                                  proposed_df,
                                  deferred_df,
                                  skipped_df,
                                  priority_level,
                                  allow_partial_payments,
                                  allow_skip_and_defer):
        """

        I want this to be as generic as possible, with no memos or priority levels having dard coded behavior.
        At least a little of this hard-coding does make implementation simpler though.
        Therefore, let all income be priority level one, and be identified by the regex '.*income.*'


        """
        relevant_proposed_df = copy.deepcopy(proposed_df[(proposed_df.Priority <= priority_level) & (
                    proposed_df.Date == datetime.datetime.strptime(date_YYYYMMDD, '%Y%m%d'))])
        relevant_confirmed_df = copy.deepcopy(confirmed_df[(confirmed_df.Priority <= priority_level) & (
                    confirmed_df.Date == datetime.datetime.strptime(date_YYYYMMDD, '%Y%m%d'))])
        relevant_deferred_df = copy.deepcopy(deferred_df[(deferred_df.Priority <= priority_level) & (
                    deferred_df.Date == datetime.datetime.strptime(date_YYYYMMDD, '%Y%m%d'))])

        self.log_stack_depth += 1
        log_in_color('green', 'debug',
                     'BEGIN executeTransactionsForDay(priority_level=' + str(priority_level) + ',date=' + str(
                         date_YYYYMMDD) + ')', self.log_stack_depth)
        log_in_color('white', 'debug', '(start of day) available_balances: ' + str(account_set.getAvailableBalances()),
                     self.log_stack_depth)

        if priority_level == 1 and forecast_df.loc[
            forecast_df.Date == date_YYYYMMDD].empty and self.end_date != datetime.datetime.strptime(date_YYYYMMDD,
                                                                                                     '%Y%m%d'):
            # this is the only place where new days get added to a forecast
            previous_row_df = copy.deepcopy(forecast_df.tail(1))
            previous_row_df.Date = previous_row_df.Date + datetime.timedelta(days=1)
            forecast_df = pd.concat([forecast_df, previous_row_df])
            forecast_df.reset_index(drop=True, inplace=True)

        if (
                priority_level != 1 and relevant_proposed_df.empty and relevant_confirmed_df.empty and relevant_deferred_df.empty) | (
                priority_level == 1 and relevant_proposed_df.empty):
            log_in_color('white', 'debug',
                         '(end of day) available_balances: ' + str(account_set.getAvailableBalances()),
                         self.log_stack_depth)
            log_in_color('green', 'debug',
                         'END executeTransactionsForDay(priority_level=' + str(priority_level) + ',date=' + str(
                             date_YYYYMMDD) + ')', self.log_stack_depth)
            self.log_stack_depth -= 1
            return [forecast_df, skipped_df, confirmed_df,
                    deferred_df]  # this logic is here just to reduce useless logs

        memo_set_df = memo_set.getMemoRules()
        relevant_memo_set_df = memo_set_df[memo_set_df.Transaction_Priority == priority_level]

        if priority_level == 1:
            income_rows_sel_vec = [re.search('.*income.*', str(memo)) is not None for memo in proposed_df.Memo]
            income_rows_df = proposed_df[income_rows_sel_vec]
            non_income_rows_df = proposed_df[[not x for x in income_rows_sel_vec]]
            non_income_rows_df.sort_values(by='Amount', inplace=True, ascending=False)
            budget_schedule_df = pd.concat([income_rows_df, non_income_rows_df])

        if priority_level == 1 and confirmed_df.shape[0] > 0 and deferred_df.shape[0] > 0:
            raise ValueError("Design assumption violated.")

        if priority_level == 1 and (allow_skip_and_defer or allow_partial_payments):
            log_in_color('white', 'debug', 'Nonsense combination of parameters. Edit input and try again.',
                         self.log_stack_depth)
            log_in_color('white', 'debug',
                         '(if priority_level = 1, then allow_skip_and_defer and allow_partial_payments must both be false)',
                         self.log_stack_depth)
            raise ValueError(
                "Design assumption violated. executeTransactionsForDay() :: if priority_level = 1, then allow_skip_and_defer and allow_partial_payments must both be false")

        if priority_level > 1:
            # the account_set needs to be updated to reflect what the balances were for this day
            row_sel_vec = (forecast_df.Date == datetime.datetime.strptime(date_YYYYMMDD, '%Y%m%d'))
            for account_index, account_row in account_set.getAccounts().iterrows():
                account_set.accounts[account_index].Balance = forecast_df.loc[row_sel_vec, account_row.Name]

        # this may not be necessary, but it is at least clear that this method only operates on the local scope
        account_set = copy.deepcopy(account_set)
        forecast_df = copy.deepcopy(forecast_df)
        memo_set_df = copy.deepcopy(memo_set_df)

        log_in_color('yellow', 'debug', 'Relevant memo rules (priority ' + str(priority_level) + '):',
                     self.log_stack_depth)
        log_in_color('yellow', 'debug', relevant_memo_set_df.to_string(), self.log_stack_depth)

        for confirmed_index, confirmed_row in relevant_confirmed_df.iterrows():
            for memo_rule_index, memo_rule_row in relevant_memo_set_df.iterrows():
                m = re.search(memo_rule_row.Memo_Regex, confirmed_row.Memo)
                try:
                    m.group(0)
                    log_in_color('yellow', 'debug',
                                 'Found matching memo rule: ' + str(memo_rule_row.Account_From) + ' -> ' + str(
                                     memo_rule_row.Account_To), self.log_stack_depth)
                except Exception as e:
                    pass  # no match

                m_income = re.search('income', memo_rule_row.Memo_Regex)
                try:
                    m_income.group(0)
                    income_flag = True
                    log_in_color('yellow', 'debug', 'transaction flagged as income', 3)
                except Exception as e:
                    income_flag = False

                account_set.executeTransaction(Account_From=memo_rule_row.Account_From,
                                               Account_To=memo_rule_row.Account_To,
                                               Amount=confirmed_row.Amount,
                                               income_flag=income_flag)

        log_in_color('cyan', 'debug', 'Relevant proposed transactions for day (priority ' + str(priority_level) + '):',
                     self.log_stack_depth)
        log_in_color('cyan', 'debug', relevant_proposed_df.to_string(), self.log_stack_depth)

        proposed_and_deferred_df = pd.concat([relevant_proposed_df, relevant_deferred_df])
        for budget_item_index, budget_item_row in proposed_and_deferred_df.iterrows():
            amount_ammended = False

            for memo_rule_index, memo_rule_row in memo_set_df.iterrows():
                m = re.search(memo_rule_row.Memo_Regex, budget_item_row.Memo)
                try:
                    m.group(0)
                    log_in_color('yellow', 'debug',
                                 'Found matching memo rule: ' + str(memo_rule_row.Account_From) + ' -> ' + str(
                                     memo_rule_row.Account_To), self.log_stack_depth)
                except Exception as e:
                    pass  # no match

                m_income = re.search('income', memo_rule_row.Memo_Regex)
                try:
                    m_income.group(0)
                    income_flag = True
                    log_in_color('yellow', 'debug', 'transaction flagged as income', 3)
                except Exception as e:
                    income_flag = False

                # no need for error checking between memo rules and budget items because that happened upstream in the ExpenseForecast constructor

                available_balances = account_set.getAvailableBalances()
                log_in_color('white', 'debug', '(pre transaction) available_balances: ' + str(available_balances),
                             self.log_stack_depth)
                log_in_color('green', 'debug', 'Checking transaction to see if it violates account boundaries',
                             self.log_stack_depth)
                try:

                    # this line of code works for the satisfice case because there are no future conditions that could be violated.
                    # #copy.deepcopy(account_set).executeTransaction(Account_From=memo_rule_row.Account_From,
                    #                                               Account_To=memo_rule_row.Account_To,
                    #                                               Amount=budget_item_row.Amount,
                    #                                               income_flag=income_flag)

                    # todo roll_forward needs to be implemented. The problem is that interest accruals and minimum payments need to happen again also....
                    # ! a recursive trick could work here..... maybe.....................
                    # add the transaction to to confirmed_df and run it and then check for errors..........................

                    # this line works for the optimize case precisely because the executeTransactionsForDay method (this method) does no error checking
                    # if the transaction violates account boundaries, then that will be detected by AccountSet
                    # the key difference between this simulation-within-a-simulation and the main simulation is that the proposed transaction is treated as having priority 1
                    # if this works I am actually so extremely happy with the elegance
                    # also remove the original row tho
                    single_proposed_transaction_df = pd.DataFrame(copy.deepcopy(budget_item_row)).T
                    single_proposed_transaction_df.Priority = 1
                    self.log_stack_depth += 1
                    log_in_color('magenta', 'debug', 'BEGIN error-check computeOptimalForecast', self.log_stack_depth)
                    # start_date_YYYYMMDD, end_date_YYYYMMDD, confirmed_df, proposed_df, deferred_df, skipped_df, account_set, memo_rule_set

                    hypothetical_confirmed_df = pd.concat([copy.deepcopy(confirmed_df), single_proposed_transaction_df])


                    self.computeOptimalForecast(start_date_YYYYMMDD=self.start_date.strftime('%Y%m%d'),
                                                end_date_YYYYMMDD=self.end_date.strftime('%Y%m%d'),
                                                confirmed_df=hypothetical_confirmed_df,
                                                proposed_df=proposed_df,
                                                deferred_df=deferred_df,
                                                skipped_df=skipped_df,
                                                account_set=copy.deepcopy(account_set),
                                                memo_rule_set=copy.deepcopy(memo_set))
                    log_in_color('magenta', 'debug', 'END error-check computeOptimalForecast (SUCCESS)',self.log_stack_depth)
                    self.log_stack_depth -= 1
                    transaction_is_permitted = True
                except Exception as e:
                    print(e)
                    log_in_color('magenta', 'debug', 'END error-check computeOptimalForecast (FAIL)',self.log_stack_depth)
                    self.log_stack_depth -= 1
                    transaction_is_permitted = False

                log_in_color('green', 'debug', 'not transaction_is_permitted=' + str(
                    not transaction_is_permitted) + ',budget_item_row.Partial_Payment_Allowed=' + str(
                    budget_item_row.Partial_Payment_Allowed), self.log_stack_depth)
                if not transaction_is_permitted and allow_partial_payments and budget_item_row.Partial_Payment_Allowed:
                    budget_item_row.Amount = available_balances[memo_rule_row.Account_From]

                    try:
                        # copy.deepcopy(account_set).executeTransaction(Account_From=memo_rule_row.Account_From,
                        #                                               Account_To=memo_rule_row.Account_To,
                        #                                               Amount=budget_item_row.Amount,
                        #                                               income_flag=income_flag)

                        single_proposed_transaction_df = pd.DataFrame(copy.deepcopy(budget_item_row)).T
                        single_proposed_transaction_df.Priority = 1
                        self.log_stack_depth += 1
                        log_in_color('magenta', 'debug', 'BEGIN error-check computeOptimalForecast',self.log_stack_depth)
                        self.computeOptimalForecast(start_date_YYYYMMDD=self.start_date.strftime('%Y%m%d'),
                                                    end_date_YYYYMMDD=self.end_date.strftime('%Y%m%d'),
                                                    confirmed_df=pd.concat([copy.deepcopy(confirmed_df), single_proposed_transaction_df]),
                                                    proposed_df=proposed_df,
                                                    deferred_df=deferred_df,
                                                    skipped_df=skipped_df,
                                                    account_set=copy.deepcopy(account_set),
                                                    memo_rule_set=copy.deepcopy(memo_set))
                        log_in_color('magenta', 'debug', 'END error-check computeOptimalForecast (SUCCESS)',self.log_stack_depth)
                        self.log_stack_depth -= 1
                        transaction_is_permitted = True
                    except Exception as e:
                        print(e)
                        log_in_color('magenta', 'debug', 'END error-check computeOptimalForecast (FAIL)',
                                     self.log_stack_depth)
                        self.log_stack_depth -= 1
                        transaction_is_permitted = False  # I think this will never happen, because the "worst case" would be a 0, which is acceptable

                    if transaction_is_permitted:
                        log_in_color('green', 'debug',
                                     'Transaction was not permitted at indicated amount. The amount was approved at this amount: ' + str(
                                         budget_item_row.Amount), self.log_stack_depth)
                        amount_ammended = True

                # print('budget_item_row:'+str(budget_item_row))
                log_in_color('green', 'debug', 'not transaction_is_permitted=' + str(
                    not transaction_is_permitted) + ',budget_item_row.Deferrable=' + str(budget_item_row.Deferrable),
                             self.log_stack_depth)
                if not transaction_is_permitted and allow_skip_and_defer and budget_item_row.Deferrable:
                    log_in_color('green', 'debug', 'Appending transaction to deferred_df', self.log_stack_depth)
                    deferred_df = pd.concat([deferred_df, pd.DataFrame(budget_item_row).T])
                elif not transaction_is_permitted and allow_skip_and_defer and not budget_item_row.Deferrable:
                    log_in_color('green', 'debug', 'Appending transaction to skipped_df', self.log_stack_depth)
                    skipped_df = pd.concat([skipped_df, pd.DataFrame(budget_item_row).T])
                elif not transaction_is_permitted and not allow_skip_and_defer:
                    raise ValueError(
                        'Partial payment, skip and defer were not allowed (either by txn parameter or method call), and transaction failed to obtain approval.')

                elif transaction_is_permitted:
                    log_in_color('green', 'debug', 'Transaction is permitted. Proceeding.', self.log_stack_depth)
                    account_set.executeTransaction(Account_From=memo_rule_row.Account_From,
                                                   Account_To=memo_rule_row.Account_To, Amount=budget_item_row.Amount,
                                                   income_flag=income_flag)
                    confirmed_df = pd.concat([confirmed_df, budget_item_row])

                    ####
                    single_proposed_transaction_df = pd.DataFrame(copy.deepcopy(budget_item_row)).T
                    single_proposed_transaction_df.Priority = 1
                    self.log_stack_depth += 1
                    log_in_color('magenta', 'debug', 'BEGIN recalculating computeOptimalForecast', self.log_stack_depth)
                    forecast_with_accurately_updated_future_rows = self.computeOptimalForecast(self,
                                                                                               self.start_date.strftime(
                                                                                                   '%Y%m%d'),
                                                                                               self.end_date_YYYYMMDD.strftime(
                                                                                                   '%Y%m%d'), pd.concat(
                            [copy.deepcopy(confirmed_df), single_proposed_transaction_df]), copy.deepcopy(account_set),
                                                                                               copy.deepcopy(memo_set))
                    log_in_color('magenta', 'debug', 'END recalculating computeOptimalForecast', self.log_stack_depth)
                    self.log_stack_depth -= 1

                    forecast_rows_to_keep_df = forecast_df[
                        forecast_df < datetime.datetime.strptime(date_YYYYMMDD, '%Y%m%d')]
                    new_forecast_rows_df = forecast_with_accurately_updated_future_rows[
                        forecast_with_accurately_updated_future_rows.Date >= datetime.datetime.strptime(date_YYYYMMDD,
                                                                                                        '%Y%m%d')]

                    forecast_df = pd.concat([forecast_rows_to_keep_df, new_forecast_rows_df])
                    forecast_df.reset_index(drop=True, inplace=True)

                    row_sel_vec = [x for x in (forecast_df.Date == datetime.datetime.strptime(date_YYYYMMDD, '%Y%m%d'))]
                    col_sel_vec = (forecast_df.columns == "Memo")

                    if amount_ammended:
                        forecast_df.iloc[row_sel_vec, col_sel_vec] += budget_item_row.Memo + ' ($' + str(
                            budget_item_row.Amount) + ') ; '
                    else:
                        forecast_df.iloc[row_sel_vec, col_sel_vec] += budget_item_row.Memo + ' ; '
                    updated_balances = account_set.getAccounts().Balance
                    # print('forecast_df:')
                    # print(forecast_df.to_string())
                    # print( datetime.datetime.strptime(date_YYYYMMDD,'%Y%m%d'))
                    row_sel_vec = (forecast_df.Date == datetime.datetime.strptime(date_YYYYMMDD, '%Y%m%d'))
                    for account_index, account_row in account_set.getAccounts().iterrows():
                        if ( account_index + 1) == account_set.getAccount().shape[1]:
                            break
                        print('UPDATING ' + str(account_row.Name) + '. SET TO ' + str(updated_balances[account_index]))
                        relevant_balance = account_set.getAccounts().iloc[account_index,1]
                        forecast_df[forecast_df.Date == d].iloc[0, account_index + 1] = relevant_balance

                else:
                    raise ValueError("""This is an edge case that should not be possible
                    transaction_is_permitted...............:""" + str(transaction_is_permitted) + """
                    allow_skip_and_defer...................:""" + str(allow_skip_and_defer) + """
                    budget_item_row.Deferrable.............:""" + str(budget_item_row.Deferrable) + """
                    budget_item_row.Partial_Payment_Allowed:""" + str(budget_item_row.Partial_Payment_Allowed) + """
                    """)

        available_balances = account_set.getAvailableBalances()
        log_in_color('white', 'debug', '(end of day) available_balances: ' + str(available_balances),
                     self.log_stack_depth)
        log_in_color('green', 'debug',
                     'END executeTransactionsForDay(priority_level=' + str(priority_level) + ',date=' + str(
                         date_YYYYMMDD) + ')', self.log_stack_depth)
        self.log_stack_depth -= 1
        return [forecast_df, skipped_df, confirmed_df, deferred_df]

    # def executeEssentialTransactionsForDay(self, budget_schedule_df, account_set, memo_set, current_forecast_row_df):
    #     #print(BEGIN_GREEN + 'executeTransactionsForDay(date='+str(current_forecast_row_df.Date.iloc[0])+')' + RESET_COLOR)
    #     #print(BEGIN_GREEN + budget_schedule_df.to_string() + RESET_COLOR)
    #     self.log_stack_depth += 1
    #     log_in_color('green','debug','BEGIN executeEssentialTransactionsForDay(date='+str(current_forecast_row_df.Date.iloc[0])+')',self.log_stack_depth)
    #     available_balances = account_set.getAvailableBalances()
    #     log_in_color('white', 'debug', '(start of day) available_balances: ' + str(available_balances),self.log_stack_depth)
    #     #making minimum payments should be determined by memo rules instead of hard-coded as checking
    #     # try:
    #     #     print('budget_schedule_df:\n'+budget_schedule_df.to_string())
    #     # except Exception as e:
    #     #     pass
    #     # try:
    #     #     print('memo_rule_set:\n' + memo_rule_set.to_string())
    #     # except Exception as e:
    #     #     pass
    #     #
    #     # try:
    #     #     print('current_forecast_row_df:\n' + current_forecast_row_df.to_string())
    #     # except Exception as e:
    #     #     pass
    #
    #     income_rows_sel_vec = [ re.search('.*income.*',str(memo)) is not None for memo in budget_schedule_df.Memo]
    #     income_rows_df = budget_schedule_df[income_rows_sel_vec]
    #     non_income_rows_df = budget_schedule_df[[not x for x in income_rows_sel_vec]]
    #     non_income_rows_df.sort_values(by='Amount',inplace=True,ascending=False)
    #     budget_schedule_df = pd.concat([income_rows_df,non_income_rows_df])
    #
    #     log_in_color('cyan', 'debug', 'All proposed transactions for day:', self.log_stack_depth)
    #     for line in budget_schedule_df.to_string().split('\n'):
    #         log_in_color('cyan','debug',line,self.log_stack_depth)
    #
    #     for index, row in budget_schedule_df.iterrows():
    #         found_matching_memo_rule = False
    #
    #         if row.Amount == 0:
    #             continue
    #
    #         log_in_color('yellow', 'debug', 'All memo rules:' , self.log_stack_depth)
    #         for line in memo_set.getMemoRules().to_string().split('\n'):
    #             log_in_color('yellow', 'debug',line, self.log_stack_depth)
    #
    #         for index2, row2 in memo_set.getMemoRules().iterrows():
    #
    #             if row2.Transaction_Priority != row.Priority:
    #                 continue
    #
    #             m = re.search(row2.Memo_Regex,row.Memo)
    #             try:
    #                 m.group(0)
    #                 found_matching_memo_rule = True
    #                 log_in_color('yellow', 'debug','Found matching memo rule: '+str(row2.Account_From)+' -> '+str(row2.Account_To), self.log_stack_depth)
    #             except Exception as e:
    #                 pass # no match
    #                 #log_in_color('yellow', 'debug', 'found_matching_memo_rule = False', 3)
    #
    #             if found_matching_memo_rule:
    #                 m_cc = re.search('additional cc payment',row2.Memo_Regex)
    #                 try:
    #                     m_cc.group(0)
    #                     additional_cc_payment = True
    #                     #log_in_color('yellow', 'debug', 'transaction flagged as additional cc payment', 3)
    #                 except:
    #                     pass  # no match
    #
    #
    #                 m_loan = re.search('additional loan payment', row2.Memo_Regex)
    #                 try:
    #                     m_loan.group(0)
    #                     additional_loan_payment = True
    #                     #log_in_color('yellow', 'debug', 'transaction flagged as additional loan payment', 3)
    #                 except:
    #                     pass  # no match
    #
    #                 m_income = re.search('income', row2.Memo_Regex)
    #                 try:
    #                     m_income.group(0)
    #                     income_flag = True
    #                     #log_in_color('yellow', 'debug', 'transaction flagged as income', 3)
    #                 except Exception as e:
    #                     income_flag = False
    #
    #                 available_balances = account_set.getAvailableBalances()
    #                 if row2.Account_From is not None:
    #                     if row2.Account_From != 'None':
    #                         try:
    #                             assert row2.Account_From in available_balances.keys()
    #                         except AssertionError as e:
    #                             log_in_color('red', 'debug',row2.Account_From + ' not found in account set', self.log_stack_depth)
    #                             log_in_color('red', 'debug', 'available_balances.keys():'+str(available_balances.keys()), self.log_stack_depth)
    #                             raise e
    #
    #                 if row2.Account_To is not None:
    #                     if row2.Account_To != 'None':
    #                         try:
    #                             assert row2.Account_To in available_balances.keys()
    #                         except AssertionError as e:
    #                             log_in_color('red', 'debug',row2.Account_To + ' not found in account set', 3)
    #                             log_in_color('red', 'debug', 'available_balances.keys():'+str(available_balances.keys()), self.log_stack_depth)
    #                             raise e
    #
    #                 log_in_color('white', 'debug', '(pre transaction) available_balances: '+str(available_balances), self.log_stack_depth)
    #
    #                 #this check needs to more generally check for account boundary violations and doesnt explode w None values
    #                 #if row.Amount > available_balances[row2.Account_From]:
    #
    #                 not_OK_to_proceed = account_set.transaction_would_violate_current_state_account_boundaries(row2.Account_From, row2.Account_To, row.Amount, income_flag)
    #                 log_in_color('white', 'debug', 'not_OK_to_proceed:' + str(not_OK_to_proceed),self.log_stack_depth)
    #
    #                 if not_OK_to_proceed and row.Partial_Payment_Allowed:
    #                     previous_amount = row.Amount
    #                     row.Amount = available_balances[row2.Account_From]
    #                     log_in_color('white', 'debug', 'Partial Payment is allowed, so we reduce the amount of the payment', self.log_stack_depth)
    #                     log_in_color('white', 'debug',str(previous_amount)+' -> '+str(row.Amount), self.log_stack_depth)
    #
    #                 # if not_OK_to_proceed and allow_skip_and_defer:
    #                 #     log_in_color('white', 'debug', 'Insufficient funds on a deferrable transaction', self.log_stack_depth)
    #                 #     log_in_color('white', 'debug', 'row:\n' + str(row), self.log_stack_depth)
    #                 #     if row.Deferrable:
    #                 #         row.Date = row.Date + datetime.timedelta(days=1)
    #                 #         self.deferred_df = pd.concat([self.deferred_df, row])
    #                 #         log_in_color('white', 'debug', '\nself.deferred_df:', self.log_stack_depth)
    #                 #         log_in_color('white', 'debug', self.deferred_df, self.log_stack_depth)
    #                 #     else:
    #                 #         log_in_color('white', 'debug', 'Insufficient funds on a non-deferrable transaction\n', self.log_stack_depth)
    #                 #         self.skipped_df = pd.concat([self.skipped_df, row])
    #                 #         log_in_color('white', 'debug', '\nself.skipped_df:', self.log_stack_depth)
    #                 #         log_in_color('white', 'debug', self.skipped_df, self.log_stack_depth)
    #                 #
    #                 # else:
    #                 log_in_color('white', 'debug', 'Proceeding with transaction', self.log_stack_depth)
    #                 if income_flag:
    #                     log_in_color('white', 'debug', 'transaction flagged as income', self.log_stack_depth)
    #
    #                     account_set.executeTransaction(row2.Account_From,row2.Account_To,row.Amount,income_flag)
    #                     self.confirmed_df = pd.concat([self.confirmed_df,row])
    #
    #                 current_forecast_row_df.Memo += row.Memo + ' ; '
    #                 break #stop looking for matching memo rules
    #
    #         if not found_matching_memo_rule:
    #             #we checked for this case in the ExpenseForecast constructor so lets not do it here
    #             log_in_color('yellow', 'error', 'No matching memo rules found for transaction: '+str(row.Memo), self.log_stack_depth)
    #
    #
    #     #at this point, memo has been updated, but balances are stale
    #     updated_balances = account_set.getAccounts().Balance
    #     for i in range(0,updated_balances.shape[0]):
    #         current_forecast_row_df.iloc[0,i+1] = updated_balances[i]
    #
    #
    #     log_in_color('white', 'debug', '(end of day) available_balances: ' + str(account_set.getAvailableBalances()), self.log_stack_depth)
    #     log_in_color('green', 'debug',
    #                  'END   executeEssentialTransactionsForDay(date=' + str(current_forecast_row_df.Date.iloc[0]) + ')', self.log_stack_depth)
    #     self.log_stack_depth -= 1
    #     #returns a single forecast row with updated memo
    #     return current_forecast_row_df

    def calculateInterestAccrualsForDay(self, account_set, current_forecast_row_df):
        self.log_stack_depth += 1
        log_in_color('green', 'debug', 'BEGIN calculateInterestAccrualsForDay()', self.log_stack_depth)
        # This method will transfer balances from current statement to previous statement for savings and credit accounts

        current_date = current_forecast_row_df.Date.iloc[0]
        # generate a date sequence at the specified cadence between billing_start_date and the current date
        # if the current date is in that sequence, then do accrual
        for account_index, row in account_set.getAccounts().iterrows():
            if row.Interest_Cadence == 'None' or row.Interest_Cadence is None or row.Interest_Cadence == '':  # ithink this may be refactored. i think this will explode if interest_cadence is None
                continue
            num_days = (current_date - row.Billing_Start_Dt).days
            dseq = generate_date_sequence(start_date_YYYYMMDD=row.Billing_Start_Dt.strftime('%Y%m%d'),
                                          num_days=num_days,
                                          cadence=row.Interest_Cadence)

            if current_forecast_row_df.Date.iloc[0] == row.Billing_Start_Dt:
                dseq = set(current_forecast_row_df.Date).union(dseq)

            if current_date in dseq:
                log_in_color('green', 'debug', 'computing interest accruals for:' + str(row.Name), self.log_stack_depth)
                # print('interest accrual initial conditions:')
                # print(current_forecast_row_df.to_string())

                if row.Interest_Type.lower() == 'compound' and row.Interest_Cadence.lower() == 'yearly':
                    # print('CASE 1 : Compound, Monthly')

                    raise NotImplementedError

                elif row.Interest_Type.lower() == 'compound' and row.Interest_Cadence.lower() == 'quarterly':
                    # print('CASE 2 : Compound, Quarterly')

                    raise NotImplementedError

                elif row.Interest_Type.lower() == 'compound' and row.Interest_Cadence.lower() == 'monthly':
                    # print('CASE 3 : Compound, Monthly')

                    accrued_interest = row.APR * row.Balance / 12
                    account_set.accounts[account_index].balance += accrued_interest

                    # move curr stmt bal to previous
                    prev_stmt_balance = account_set.accounts[account_index - 1].balance

                    # prev_acct_name = account_set.accounts[account_index - 1].name
                    # curr_acct_name = account_set.accounts[account_index].name
                    # print('current account name:' + str(curr_acct_name))
                    # print('prev_acct_name:'+str(prev_acct_name))
                    # print('prev_stmt_balance:'+str(prev_stmt_balance))
                    account_set.accounts[account_index].balance += prev_stmt_balance
                    account_set.accounts[account_index].balance = round(account_set.accounts[account_index].balance, 2)
                    account_set.accounts[account_index - 1].balance = 0

                elif row.Interest_Type.lower() == 'compound' and row.Interest_Cadence.lower() == 'semiweekly':
                    # print('CASE 4 : Compound, Semiweekly')

                    raise NotImplementedError  # Compound, Semiweekly

                elif row.Interest_Type.lower() == 'compound' and row.Interest_Cadence.lower() == 'weekly':
                    # print('CASE 5 : Compound, Weekly')

                    raise NotImplementedError  # Compound, Weekly

                elif row.Interest_Type.lower() == 'compound' and row.Interest_Cadence.lower() == 'daily':
                    # print('CASE 6 : Compound, Daily')

                    raise NotImplementedError  # Compound, Daily

                elif row.Interest_Type.lower() == 'simple' and row.Interest_Cadence.lower() == 'yearly':
                    # print('CASE 7 : Simple, Monthly')

                    raise NotImplementedError  # Simple, Monthly

                elif row.Interest_Type.lower() == 'simple' and row.Interest_Cadence.lower() == 'quarterly':
                    # print('CASE 8 : Simple, Quarterly')

                    raise NotImplementedError  # Simple, Quarterly

                elif row.Interest_Type.lower() == 'simple' and row.Interest_Cadence.lower() == 'monthly':
                    # print('CASE 9 : Simple, Monthly')

                    raise NotImplementedError  # Simple, Monthly

                elif row.Interest_Type.lower() == 'simple' and row.Interest_Cadence.lower() == 'semiweekly':
                    # print('CASE 10 : Simple, Semiweekly')

                    raise NotImplementedError  # Simple, Semiweekly

                elif row.Interest_Type.lower() == 'simple' and row.Interest_Cadence.lower() == 'weekly':
                    # print('CASE 11 : Simple, Weekly')

                    raise NotImplementedError  # Simple, Weekly

                elif row.Interest_Type.lower() == 'simple' and row.Interest_Cadence.lower() == 'daily':
                    # print('CASE 12 : Simple, Daily')

                    accrued_interest = row.APR * row.Balance / 365.25
                    account_set.accounts[account_index + 1].balance += round(accrued_interest,
                                                                             2)  # this is the interest account

            else:
                # ('There were no interest bearing items for this day')
                # print(current_forecast_row_df.to_string())
                pass

            updated_balances = account_set.getAccounts().Balance
            for account_index, account_row in account_set.getAccounts().iterrows():
                if ( account_index + 1) == account_set.getAccount().shape[1]:
                    break
                relevant_balance = account_set.getAccounts().iloc[account_index,1]
                forecast_df[forecast_df.Date == d].iloc[0, account_index + 1] = relevant_balance

            # returns a single forecast row
            log_in_color('green', 'debug', 'EXIT calculateInterestAccrualsForDay', self.log_stack_depth)
            self.log_stack_depth -= 1
            return current_forecast_row_df

        log_in_color('green', 'debug', 'EXIT calculateInterestAccrualsForDay()', self.log_stack_depth)
        self.log_stack_depth -= 1
        return current_forecast_row_df  # this runs when there are no interest bearing accounts in the simulation at all

    def executeMinimumPayments(self, account_set, current_forecast_row_df):

        # the branch logic here assumes the sort order of accounts in account list
        A = account_set.getAccounts()

        for index, row in A.iterrows():
            if pd.isnull(row.Billing_Start_Dt):
                continue

            # print(BEGIN_GREEN + row.to_string() + RESET_COLOR)
            # print('current_forecast_row_df.Date - row.Billing_Start_Dt:')
            # print('current_forecast_row_df.Date:')
            # print(current_forecast_row_df.Date)
            # print('row.Billing_Start_Dt:')
            # print(row.Billing_Start_Dt)

            num_days = (current_forecast_row_df.Date.iloc[0] - row.Billing_Start_Dt).days
            billing_days = set(
                generate_date_sequence(row.Billing_Start_Dt.strftime('%Y%m%d'), num_days, row.Interest_Cadence))

            if current_forecast_row_df.Date.iloc[0] == row.Billing_Start_Dt:
                billing_days = set(current_forecast_row_df.Date).union(billing_days)

            if current_forecast_row_df.Date.iloc[0] in billing_days:
                self.log_stack_depth += 1
                log_in_color('green', 'debug',
                             'BEGIN executeMinimumPayments()',
                             self.log_stack_depth)
                # print(row)
                if row.Account_Type == 'prev stmt bal':  # cc min payment

                    minimum_payment_amount = max(40, row.Balance * 0.02)
                    current_forecast_row_df.Memo += row.Name.split(':')[0] + ' cc min payment ($' + str(
                        minimum_payment_amount) + ') ; '

                elif row.Account_Type == 'interest':  # loan min payment

                    minimum_payment_amount = A.loc[index - 1, :].Balance
                    current_forecast_row_df.Memo += row.Name.split(':')[0] + ' loan min payment ($' + str(
                        minimum_payment_amount) + '); '

                if row.Account_Type == 'prev stmt bal' or row.Account_Type == 'interest':

                    payment_toward_prev = min(minimum_payment_amount, row.Balance)
                    payment_toward_curr = min(A.loc[index - 1, :].Balance, minimum_payment_amount - payment_toward_prev)
                    surplus_payment = minimum_payment_amount - (payment_toward_prev + payment_toward_curr)

                    if (payment_toward_prev + payment_toward_curr) > 0:
                        account_set.executeTransaction(Account_From='Checking', Account_To=row.Name.split(':')[0],
                                                       # Note that the execute transaction method will split the amount paid between the 2 accounts
                                                       Amount=(payment_toward_prev + payment_toward_curr))

                updated_balances = account_set.getAccounts().Balance
                for account_index, account_row in account_set.getAccounts().iterrows():
                    if ( account_index + 1) == account_set.getAccount().shape[1]:
                        break
                    relevant_balance = account_set.getAccounts().iloc[account_index,1]
                    forecast_df[forecast_df.Date == d].iloc[0, account_index + 1] = relevant_balance

                log_in_color('green', 'debug',
                             'END  executeMinimumPayments()',
                             self.log_stack_depth)
                self.log_stack_depth -= 1

        return current_forecast_row_df

    def computeSatisficeForecast(self, start_date_YYYYMMDD, end_date_YYYYMMDD, budget_set, account_set, memo_rule_set):
        """
        Computes output time-series that represents only non-negotiable spend.

        :param budget_schedule_df:
        :param account_set_df:
        :param memo_rules_df:
        :return:
        """
        self.log_stack_depth += 1
        log_in_color('green', 'debug', 'BEGIN computeSatisficeForecast()', self.log_stack_depth)

        all_days = pd.date_range(datetime.datetime.strptime(start_date_YYYYMMDD, '%Y%m%d'),
                                 datetime.datetime.strptime(end_date_YYYYMMDD,
                                                            '%Y%m%d'))  # this needs to stay datetime datatype
        initial_forecast_row_df = self.getInitialForecastRow()
        budget_schedule_df = budget_set.getBudgetSchedule(start_date_YYYYMMDD, end_date_YYYYMMDD)

        forecast_df = copy.deepcopy(initial_forecast_row_df)
        previous_row_df = copy.deepcopy(initial_forecast_row_df)

        skipped_df = copy.deepcopy(budget_schedule_df.head(0))
        confirmed_df = copy.deepcopy(budget_schedule_df.head(0))
        deferred_df = copy.deepcopy(budget_schedule_df.head(0))

        try:
            for d in all_days:
                # log_in_color('green', 'debug', 'd:'+str(d),1)
                if d == datetime.datetime.strptime(start_date_YYYYMMDD, '%Y%m%d'):
                    continue  # because we consider the first day to be final

                current_row_df = previous_row_df.copy()
                current_row_df.Date = current_row_df.Date + datetime.timedelta(days=1)
                current_row_df.Memo = ''
                forecast_df = pd.concat([forecast_df, current_row_df])

                income_sel_vec = []
                for index, row in budget_schedule_df.iterrows():
                    try:
                        re.search('.*income.*', row.Memo).group(0)
                        income_sel_vec.append(True)
                    except:
                        income_sel_vec.append(False)
                not_income_sel_vec = [not x for x in income_sel_vec]

                forecast_df, skipped_df, confirmed_df, deferred_df = self.executeTransactionsForDay(
                    account_set, forecast_df=forecast_df,
                    date_YYYYMMDD=d,
                    memo_set=memo_rule_set,
                    confirmed_df=confirmed_df,
                    proposed_df=budget_schedule_df.loc[income_sel_vec],
                    deferred_df=deferred_df,
                    skipped_df=skipped_df,
                    priority_level=1,
                    allow_skip_and_defer=False,
                    allow_partial_payments=False)

                forecast_df[forecast_df.Date == d] = self.executeMinimumPayments(account_set, current_row_df)
                forecast_df[forecast_df.Date == d] = self.calculateInterestAccrualsForDay(account_set,
                                                                                          current_row_df)  # returns only a forecast row w updated memo

                # i assume that the above lines are all operating on the same data frame

                forecast_df, skipped_df, confirmed_df, deferred_df = self.executeTransactionsForDay(account_set,
                                                                                                    forecast_df=forecast_df,
                                                                                                    date_YYYYMMDD=d,
                                                                                                    memo_set=memo_rule_set,
                                                                                                    confirmed_df=confirmed_df,
                                                                                                    proposed_df=
                                                                                                    budget_schedule_df.loc[
                                                                                                        not_income_sel_vec],
                                                                                                    deferred_df=deferred_df,
                                                                                                    skipped_df=skipped_df,
                                                                                                    priority_level=1,
                                                                                                    allow_skip_and_defer=False,
                                                                                                    allow_partial_payments=False)

                previous_row_df = current_row_df

            forecast_df.reset_index(drop=True, inplace=True)
        except Exception as e:
            log_in_color('white', 'debug', repr(e), self.log_stack_depth)
            log_in_color('white', 'debug', '\nSATISFICE FINAL STATE BEFORE CRASH', self.log_stack_depth)
            log_in_color('white', 'debug', forecast_df.to_string(), self.log_stack_depth)

        if max(forecast_df.Date) != end_date_YYYYMMDD:
            s_date = (max(forecast_df.Date) + datetime.timedelta(days=1)).strftime('%Y%m%d')
            n_days = (datetime.datetime.strptime(end_date_YYYYMMDD, '%Y%m%d') - max(forecast_df.Date)).days - 1
            remaining_days = generate_date_sequence(s_date, n_days, 'daily')
            remaining_days_df = pd.DataFrame(remaining_days)
            remaining_days_df.rename(columns={0: 'Date'})

            empty_row = copy.deepcopy(forecast_df.head(1))
            for cname in empty_row.columns:
                if cname == 'Date':
                    continue
                elif cname == 'Memo':
                    empty_row[cname] = ''
                else:
                    empty_row[cname] = None

            empty_row = empty_row.rename(columns={"Date": "Old_Date__Delete_This"})
            remaining_rows_df = remaining_days_df.merge(empty_row, how="cross")
            remaining_rows_df = remaining_rows_df.drop(['Old_Date__Delete_This'], axis=1)
            remaining_rows_df = remaining_rows_df.rename(columns={0: "Date"})
            forecast_df = pd.concat([forecast_df, remaining_rows_df])
        forecast_df.reset_index(drop=True, inplace=True)
        log_in_color('white', 'debug', '', self.log_stack_depth)
        log_in_color('white', 'debug', 'SATISFICE FINAL STATE', self.log_stack_depth)
        log_in_color('white', 'debug', forecast_df.to_string(), self.log_stack_depth)

        # print('forecast_df:')
        # print(forecast_df.to_string())

        try:
            assert min(forecast_df.Date) == datetime.datetime.strptime(start_date_YYYYMMDD, '%Y%m%d')
        except Exception as e:
            raise ValueError("""
            computeSatisficeForecast() did not include the first day as specified.
            start_date_YYYYMMDD=""" + str(start_date_YYYYMMDD) + """
            min(forecast_df.Date)=""" + str(min(forecast_df.Date)) + """
            """)

        try:
            assert max(forecast_df.Date) == datetime.datetime.strptime(end_date_YYYYMMDD, '%Y%m%d')
        except Exception as e:
            raise ValueError("""
            computeSatisficeForecast() did not include the last day as specified.
            end_date_YYYYMMDD=""" + str(end_date_YYYYMMDD) + """
            max(forecast_df.Date)=""" + str(max(forecast_df.Date)) + """
            """)

        log_in_color('green', 'debug', 'END   computeSatisficeForecast()', self.log_stack_depth)
        self.log_stack_depth -= 1
        return [forecast_df, skipped_df, confirmed_df, deferred_df]

    def getMinimumFutureAvailableBalances(self, account_set, forecast_df, date_YYYYMMDD):
        self.log_stack_depth += 1
        log_in_color('green', 'debug', 'ENTER getMinimumFutureAvailableBalances(date=' + str(date_YYYYMMDD) + ')',
                     self.log_stack_depth)
        current_and_future_forecast_df = forecast_df[forecast_df.Date >= date_YYYYMMDD]

        # account set doesnt need to be in sync because we just using it for accoutn names
        A = account_set.getAccounts()
        future_available_balances = {}
        for account_index, account_row in A.iterrows():
            full_aname = account_row.Name
            aname = full_aname.split(':')[0]

            if account_row.Account_Type.lower() == 'checking':
                future_available_balances[aname] = min(current_and_future_forecast_df[aname])
            elif account_row.Account_Type.lower() == 'prev stmt bal':

                prev_name = full_aname
                curr_name = A.iloc[account_index - 1].Name

                available_credit = current_and_future_forecast_df[prev_name] + current_and_future_forecast_df[curr_name]
                future_available_balances[aname] = A[A.Name == prev_name].Max_Balance.iloc[0] - min(available_credit)

        log_in_color('magenta', 'debug', 'future_available_balances:' + str(future_available_balances),
                     self.log_stack_depth)
        log_in_color('green', 'debug', 'EXIT getMinimumFutureAvailableBalances(date=' + str(date_YYYYMMDD) + ')',
                     self.log_stack_depth)
        self.log_stack_depth -= 1
        return future_available_balances

    def updateForecastByPropogatingPostTransactionBalances(self, date_YYYYMMDD):
        self.log_stack_depth += 1
        log_in_color('green', 'debug', 'ENTER updateForecastByPropogatingPostTransactionBalances()',
                     self.log_stack_depth)
        # when this method called, there will be a mismatch between the balances in self.account_set, and the balances indicated on the forecast
        # there should be at most 2 differences, and if there are two, the changes would be between a prev and curr credit account, or a principal balance and interest account

        # for each account, check if the forecast agrees with the account set
        # assert that changes are always a reduction in net worth. (all income was priority 1, and this method is not called in priority 1)
        # set account_set balances equal to what is indicated by the forecast
        # re-satisfice using the balances and date from the previous step as initial conditions
        # assert that range of account balances do not violate account boundaries

        current_and_future_forecast_rows_df = self.forecast_df[self.forecast_df.Date >= date_YYYYMMDD]

        A = self.account_set.getAccounts()

        mismatched_balance_count = 0  # if this goes above 2 then there is an error
        account_index = 0
        for aname in self.account_set.getAccounts().Name:
            single_account_forecast_df = current_and_future_forecast_rows_df.iloc[:,
                                         current_and_future_forecast_rows_df.columns == aname]

            relevant_balance = A.loc[(A.Name == aname)].Balance.iloc[0]
            if single_account_forecast_df.iloc[0, 0] != relevant_balance:
                log_in_color('green', 'debug',
                             str(single_account_forecast_df.iloc[0, 0]) + ' != ' + str(relevant_balance),
                             self.log_stack_depth)
                self.account_set[account_index].balance = relevant_balance

            account_index += 1

        # at this point, account_set now reflects the forecast.
        # Now, we can use account_set and the current row of the forecast to update the future portion of the forecast
        # This logic could take advantage of code I have already written, but honestly the refactoring is too clever for me to figure out.
        # Instead, I will just reimplement it here, and we can refactor later once it works.

        log_in_color('green', 'debug', 'EXIT updateForecastByPropogatingPostTransactionBalances()',
                     self.log_stack_depth)
        self.log_stack_depth -= 1

    # def executeNonEssentialTransactionsForDay(self,current_budget_schedule_items_df,priority_level,date_YYYYMMDD):
    #     self.log_stack_depth += 1
    #     log_in_color('green', 'debug', 'ENTER executeNonEssentialTransactionsForDay(date=' + str(date_YYYYMMDD) + ')',self.log_stack_depth)
    #     assert min(current_budget_schedule_items_df.Priority) == max(current_budget_schedule_items_df.Priority)
    #     assert min(current_budget_schedule_items_df.Priority) == priority_level
    #
    #     log_in_color('cyan','debug','current_budget_schedule_items_df:',self.log_stack_depth)
    #     log_in_color('cyan', 'debug', current_budget_schedule_items_df,self.log_stack_depth)
    #
    #     #account_set needs to be set to the minimum balances for dates GREATER THAN OR EQUAL TO the day in question
    #     #however, this gets weird for credit, so lets make a method for it
    #
    #     minimum_future_available_balances = self.getMinimumFutureAvailableBalances(date_YYYYMMDD)
    #
    #     #todo set account_set balances equal to the values that the forecast has for this day
    #
    #     for index, row in current_budget_schedule_items_df.iterrows():
    #         found_matching_memo_rule = False
    #
    #         if row.Amount == 0:
    #             log_in_color('green', 'debug', 'Skipping transaction because the amount was 0', self.log_stack_depth)
    #             continue
    #
    #         log_in_color('yellow', 'debug', 'All memo rules:' , self.log_stack_depth)
    #         for line in self.initial_memo_rule_set.getMemoRules().to_string().split('\n'):
    #             log_in_color('yellow', 'debug',line, self.log_stack_depth)
    #
    #         for index2, row2 in self.initial_memo_rule_set.getMemoRules().iterrows():
    #
    #             if row2.Transaction_Priority != row.Priority:
    #                 continue
    #
    #             m = re.search(row2.Memo_Regex,row.Memo)
    #             try:
    #                 m.group(0)
    #                 found_matching_memo_rule = True
    #                 log_in_color('yellow', 'debug','Found matching memo rule: '+str(row2.Account_From)+' -> '+str(row2.Account_To), self.log_stack_depth)
    #             except Exception as e:
    #                 pass # no match
    #                 #log_in_color('yellow', 'debug', 'found_matching_memo_rule = False', 3)
    #
    #             if found_matching_memo_rule:
    #                 if row2.Account_From is not None:
    #                     if row2.Account_From != 'None':
    #                         try:
    #                             assert row2.Account_From in minimum_future_available_balances.keys()
    #                         except AssertionError as e:
    #                             log_in_color('red', 'debug', row2.Account_From + ' not found in account set', self.log_stack_depth)
    #                             log_in_color('red', 'debug',
    #                                          'available_balances.keys():' + str(minimum_future_available_balances.keys()), self.log_stack_depth)
    #                             raise e
    #
    #                 if row2.Account_To is not None:
    #                     if row2.Account_To != 'None':
    #                         try:
    #                             assert row2.Account_To in minimum_future_available_balances.keys()
    #                         except AssertionError as e:
    #                             log_in_color('red', 'debug', row2.Account_To + ' not found in account set', self.log_stack_depth)
    #                             log_in_color('red', 'debug',
    #                                          'available_balances.keys():' + str(minimum_future_available_balances.keys()), self.log_stack_depth)
    #                             raise e
    #
    #                 log_in_color('white', 'debug', '(pre transaction) available_balances: ' + str(minimum_future_available_balances),self.log_stack_depth)
    #
    #                 # this check needs to more generally check for account boundary violations and doesnt explode w None values
    #
    #                 not_OK_to_proceed = ( minimum_future_available_balances[row2.Account_From] < row.Amount )
    #                 log_in_color('white', 'debug', 'not_OK_to_proceed:' + str(not_OK_to_proceed), self.log_stack_depth)
    #
    #                 if not_OK_to_proceed:
    #                     if row.Partial_Payment_Allowed:
    #                         previous_amount = row.Amount
    #                         row.Amount = minimum_future_available_balances[row2.Account_From]
    #                         log_in_color('white', 'debug','Partial Payment is allowed, so we reduce the amount of the payment', self.log_stack_depth)
    #                         log_in_color('white', 'debug', str(previous_amount) + ' -> ' + str(row.Amount), self.log_stack_depth)
    #
    #                     elif row.Deferrable:
    #                         log_in_color('white', 'debug', 'Insufficient funds on a deferrable transaction', self.log_stack_depth)
    #                         log_in_color('white', 'debug', 'row:\n' + str(row), self.log_stack_depth)
    #
    #                         row.Date = row.Date + datetime.timedelta(days=1)
    #                         self.deferred_df = pd.concat([self.deferred_df, row])
    #                         log_in_color('white', 'debug', '\nself.deferred_df:', self.log_stack_depth)
    #                         log_in_color('white', 'debug', self.deferred_df, self.log_stack_depth)
    #                     else:
    #                         log_in_color('white', 'debug', 'Insufficient funds on a non-deferrable transaction\n',
    #                                      4)
    #                         self.skipped_df = pd.concat([self.skipped_df, row])
    #                         log_in_color('white', 'debug', '\nself.skipped_df:', self.log_stack_depth)
    #                         log_in_color('white', 'debug', self.skipped_df, self.log_stack_depth)
    #
    #                 else:
    #                     log_in_color('white', 'debug', 'Proceeding with transaction', self.log_stack_depth)
    #                     self.account_set.executeTransaction(row2.Account_From, row2.Account_To, row.Amount, income_flag=False)
    #                     self.confirmed_df = pd.concat([self.confirmed_df,row])
    #
    #                     self.forecast_df.loc[(self.forecast_df.Date == date_YYYYMMDD)].Memo += row.Memo + ' ; '
    #                     self.updateForecastByPropogatingPostTransactionBalances(date_YYYYMMDD)
    #
    #
    #                     break  # stop looking for matching memo rules
    #
    #                 if not found_matching_memo_rule:
    #                     # we checked for this case in the ExpenseForecast constructor so lets not do it here
    #                     log_in_color('yellow', 'error',
    #                                  'No matching memo rules found for transaction: ' + str(row.Memo), self.log_stack_depth)
    #
    #             # at this point, memo has been updated, but balances are stale
    #             updated_balances = account_set.getAccounts().Balance
    #             for i in range(0, updated_balances.shape[0]):
    #                 current_forecast_row_df.iloc[0, i + 1] = updated_balances[i]
    #
    #             log_in_color('white', 'debug',
    #                          '(end of day) available_balances: ' + str(account_set.getAvailableBalances()), self.log_stack_depth)
    #             log_in_color('green', 'debug',
    #                          'END   executeEssentialTransactionsForDay(date=' + str(
    #                              current_forecast_row_df.Date.iloc[0]) + ')', self.log_stack_depth)
    #             # returns a single forecast row with updated memo
    #             return current_forecast_row_df
    #
    #     self.log_stack_depth -= 1
    #     log_in_color('green', 'debug', 'EXIT executeNonEssentialTransactionsForDay(date=' + str(date_YYYYMMDD) + ')',self.log_stack_depth)

    def allocate_additional_loan_payments(self, account_set, amount, date_string_YYYYMMDD):

        account_set = copy.deepcopy(account_set)
        A = account_set.getAccounts()
        principal_accts_df = A[A.Account_Type == 'principal balance']

        principal_accts_df['Marginal Interest Amount'] = principal_accts_df.Balance * principal_accts_df.APR
        principal_accts_df['Marginal Interest Rank'] = principal_accts_df['Marginal Interest Amount'].rank(
            method='dense', ascending=False)

        number_of_phase_space_regions = max(principal_accts_df['Marginal Interest Rank'])
        # print('number_of_phase_space_regions:'+str(number_of_phase_space_regions))

        all_account_names__1 = [x.split(':') for x in principal_accts_df.Name]
        all_account_names__2 = [name for sublist in all_account_names__1 for name in sublist]
        all_account_names = set(all_account_names__2) - set([' Principal Balance'])

        payment_amounts__BudgetSet = BudgetSet.BudgetSet([])

        for i in range(0, int(number_of_phase_space_regions)):

            if amount == 0:
                break

            # print('i:'+str(i))
            A = account_set.getAccounts()
            # print('A:\n')
            # print(A.to_string())

            principal_accts_df = A[A.Account_Type == 'principal balance']
            interest_accts_df = A[A.Account_Type == 'interest']

            total_amount_per_loan = {}
            for acct_name in all_account_names:
                principal_amt = \
                    principal_accts_df.iloc[[acct_name in pa_element for pa_element in principal_accts_df.Name],
                    :].Balance.iloc[0]
                interest_amt = \
                    interest_accts_df.iloc[[acct_name in pa_element for pa_element in principal_accts_df.Name],
                    :].Balance.iloc[0]

                total_amount_per_loan[acct_name] = principal_amt + interest_amt

            P = np.matrix(principal_accts_df.Balance)
            r = np.matrix(principal_accts_df.APR)
            P_dot_r = P.T.dot(r)

            reciprocal_rates = []
            for i in range(0, P.shape[1]):
                reciprocal_rates.append(1 / r[0, i])
            reciprocal_rates = np.matrix(reciprocal_rates)
            # print('reciprocal_rates:')
            # print(reciprocal_rates.shape)
            # print(reciprocal_rates)

            # print('P_dot_r:')
            # print(P_dot_r.shape)
            # print(np.matrix(P_dot_r))

            marginal_interest_amounts__list = []
            for i in range(0, P.shape[1]):
                marginal_interest_amounts__list.append(round(P_dot_r[i, i], 2))
            # print(marginal_interest_amounts__list)
            marginal_interest_amounts__matrix = np.matrix(marginal_interest_amounts__list)
            # print('marginal_interest_amounts__matrix:')
            # print(marginal_interest_amounts__matrix)
            marginal_interest_amounts_df = pd.DataFrame(marginal_interest_amounts__list)
            marginal_interest_amounts_df.columns = ['Marginal Interest Amount']
            marginal_interest_amounts_df['Marginal Interest Rank'] = marginal_interest_amounts_df[
                'Marginal Interest Amount'].rank(method='dense', ascending=False)
            # print('marginal_interest_amounts_df:')
            # print(marginal_interest_amounts_df)

            try:
                next_lowest_marginal_interest_amount = \
                    marginal_interest_amounts_df[marginal_interest_amounts_df['Marginal Interest Rank'] == 2].iloc[0, 0]
            except Exception as e:
                next_lowest_marginal_interest_amount = 0
            # print('next_lowest_marginal_interest_amount:')
            # print(next_lowest_marginal_interest_amount)
            marginal_interest_amounts_df__c = copy.deepcopy(marginal_interest_amounts_df)

            # print('marginal_interest_amounts_df__c[marginal_interest_amounts_df__c[Marginal Interest Rank] == 1]')
            # print(marginal_interest_amounts_df__c['Marginal Interest Rank'] == 1)
            # print(marginal_interest_amounts_df__c[marginal_interest_amounts_df__c['Marginal Interest Rank'] == 1])
            # print(marginal_interest_amounts_df__c[marginal_interest_amounts_df__c['Marginal Interest Rank'] == 1]['Marginal Interest Amount'])

            marginal_interest_amounts_df__c.loc[marginal_interest_amounts_df__c[
                                                    'Marginal Interest Rank'] == 1, marginal_interest_amounts_df__c.columns == 'Marginal Interest Amount'] = next_lowest_marginal_interest_amount
            next_step_marginal_interest_vector = np.matrix(marginal_interest_amounts_df__c['Marginal Interest Amount'])
            # print('next_step_marginal_interest_vector:\n')
            # print(next_step_marginal_interest_vector)

            current_state = marginal_interest_amounts__matrix.T.dot(reciprocal_rates)
            # print('current_state:\n'+str(current_state))

            # print('next_step_marginal_interest_vector:')
            # print(next_step_marginal_interest_vector)

            next_state = next_step_marginal_interest_vector.T.dot(reciprocal_rates)
            # print('next_state:\n' + str(next_state))

            delta = current_state - next_state
            # print('delta:')
            # print(delta)

            payment_amounts = []
            for i in range(0, delta.shape[0]):
                loop__amount = delta[i, i]
                payment_amounts.append(loop__amount)

            if amount <= sum(payment_amounts):
                payment_amounts = [a * (amount) / sum(payment_amounts) for a in payment_amounts]
            # print('amount -> remaining_amount:')
            # print(str(amount) + ' -> ' + str(amount - sum(payment_amounts)))
            amount = amount - sum(payment_amounts)

            for i in range(0, delta.shape[0]):
                loop__to_name = principal_accts_df.Name.iloc[i].split(':')[0]
                loop__amount = round(payment_amounts[i], 2)

                # print( str( loop__amount ) + ' ' + loop__to_name )

                if loop__amount == 0:
                    continue

                account_set.executeTransaction(Account_From=None, Account_To=loop__to_name, Amount=loop__amount)
                payment_amounts__BudgetSet.addBudgetItem(date_string_YYYYMMDD, date_string_YYYYMMDD, 7, 'once',
                                                         loop__amount, False, loop__to_name + ' additional payment')

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

        final_budget_items = []
        for key in payment_dict.keys():
            final_budget_items.append(BudgetItem.BudgetItem(date_string_YYYYMMDD,
                                                            date_string_YYYYMMDD,
                                                            7,
                                                            'once',
                                                            payment_dict[key],
                                                            False,
                                                            key, ))
        # print('final_budget_items:')
        # print(final_budget_items)

        return BudgetSet.BudgetSet(final_budget_items)

    def computeOptimalForecast(self, start_date_YYYYMMDD, end_date_YYYYMMDD, confirmed_df, proposed_df, deferred_df, skipped_df, account_set, memo_rule_set):
        """
        One-description.

        Multiple line description.

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
        self.log_stack_depth += 1
        log_in_color('green', 'debug', 'ENTER computeOptimalForecast()', self.log_stack_depth)

        full_budget_schedule_df = pd.concat([confirmed_df, proposed_df, deferred_df, skipped_df])
        full_budget_schedule_df.reset_index(drop=True,inplace=True)
        try:
            assert full_budget_schedule_df.shape[0] == full_budget_schedule_df.drop_duplicates().shape[0]
        except Exception as e:
            log_in_color('red','debug','a duplicate memo was detected. This is filtered for in ExpenseForecast(), so we know that this was caused by internal logic.')
            raise e

        log_in_color('cyan', 'debug', 'Full budget schedule:', self.log_stack_depth)
        log_in_color('cyan', 'debug', full_budget_schedule_df.to_string(), self.log_stack_depth)


        if self.log_stack_depth > 10:
            raise ValueError("stack depth greater than 10. smells like infinite recursion to me. take a look buddy")

        all_days = pd.date_range(datetime.datetime.strptime(start_date_YYYYMMDD, '%Y%m%d'),
                                 datetime.datetime.strptime(end_date_YYYYMMDD, '%Y%m%d'))
        forecast_df = self.getInitialForecastRow()
        # print('initial_forecast_row:'+str(forecast_df))
        # budget_schedule_df = budget_set.getBudgetSchedule(start_date_YYYYMMDD, end_date_YYYYMMDD)

        for d in all_days:
            log_in_color('green', 'debug', 'SATISFICE d:' + str(d), self.log_stack_depth)

            # print('SATISFICE BEFORE TXN:'+str(forecast_df))
            forecast_df, new_skipped_df, new_confirmed_df, new_deferred_df = self.executeTransactionsForDay(account_set,
                                                                                                            forecast_df=forecast_df,
                                                                                                            date_YYYYMMDD=d.strftime(
                                                                                                                '%Y%m%d'),
                                                                                                            memo_set=memo_rule_set,
                                                                                                            confirmed_df=confirmed_df,
                                                                                                            proposed_df=proposed_df,
                                                                                                            deferred_df=deferred_df,
                                                                                                            skipped_df=skipped_df,
                                                                                                            priority_level=1,
                                                                                                            allow_skip_and_defer=False,
                                                                                                            allow_partial_payments=False)  # this is the implementation of satisfice
            # print('SATISFICE AFTER TXN:'+str(forecast_df))

            if new_skipped_df.shape[0] > 0:
                skipped_df = pd.concat([skipped_df, new_skipped_df])

            if new_confirmed_df.shape[0] > 0:
                confirmed_df = pd.concat([confirmed_df, new_confirmed_df])

            if new_deferred_df.shape[0] > 0:
                deferred_df = pd.concat([deferred_df, new_deferred_df])

            # these should probably come before executeTransactionsForDay, but I'm actually not sure so I'm OK leaving these here for now
            # print('BEFORE MIN PAYMENTS')
            # print(current_row_df.to_string())
            forecast_df[forecast_df.Date == d] = self.executeMinimumPayments(account_set,
                                                                             forecast_df[forecast_df.Date == d])
            # print('AFTER MIN PAYMENTS')
            # print(current_row_df.to_string())
            # print('BEFORE INTEREST ACCRUAL')
            # print(current_row_df.to_string())
            forecast_df[forecast_df.Date == d] = self.calculateInterestAccrualsForDay(account_set, forecast_df[
                forecast_df.Date == d])  # returns only a forecast row
            # print('AFTER INTEREST ACCRUAL')
            # print(current_row_df.to_string())

            #print('About to update account balances')
            for account_index, account_row in account_set.getAccounts().iterrows():
                if ( account_index + 1) == account_set.getAccounts().shape[1]:
                    break
                #print('UPDATING '+str(account_row.Name)+'. SET TO '+str(account_set.getAccounts()[account_index]))
                relevant_balance = account_set.getAccounts().iloc[account_index,1]
                forecast_df[forecast_df.Date == d].iloc[0, account_index + 1] = relevant_balance

        unique_priority_indices = full_budget_schedule_df.Priority.unique()
        for priority_index in unique_priority_indices:
            if priority_index == 1:
                continue

            for d in all_days:
                log_in_color('green', 'debug', 'OPTIMIZE ' + str(priority_index) + ' d:' + str(d), self.log_stack_depth)

                # print('OPTIMIZE BEFORE TXN forecast_df')
                # print(forecast_df[forecast_df.Date == d].to_string())
                forecast_df, new_skipped_df, new_confirmed_df, new_deferred_df = self.executeTransactionsForDay(
                    account_set,
                    forecast_df=forecast_df,
                    date_YYYYMMDD=d.strftime('%Y%m%d'),
                    memo_set=memo_rule_set,
                    confirmed_df=confirmed_df,
                    proposed_df=proposed_df,
                    deferred_df=deferred_df,
                    skipped_df=skipped_df,
                    priority_level=priority_index,
                    allow_skip_and_defer=True,
                    allow_partial_payments=True)
                # print('OPTIMIZE AFTER TXN forecast_df')
                # print(forecast_df[forecast_df.Date == d].to_string())

                if new_skipped_df.shape[0] > 0:
                    skipped_df = pd.concat([skipped_df, new_skipped_df])

                if new_confirmed_df.shape[0] > 0:
                    confirmed_df = pd.concat([confirmed_df, new_confirmed_df])

                if new_deferred_df.shape[0] > 0:
                    deferred_df = pd.concat([deferred_df, new_deferred_df])

                # print('About to update account balances')
                for account_index, account_row in account_set.getAccounts().iterrows():
                    if ( account_index + 1) == account_set.getAccounts().shape[1]:
                        break
                    # print('UPDATING '+str(account_row.Name)+'. SET TO '+str(updated_balances[account_index]))
                    relevant_balance = account_set.getAccounts().iloc[account_index,1]
                    forecast_df[forecast_df.Date == d].iloc[0, account_index + 1] = relevant_balance

        log_in_color('green', 'debug', 'EXIT computeOptimalForecast()', self.log_stack_depth)
        self.log_stack_depth -= 1
        return [forecast_df, skipped_df, confirmed_df, deferred_df]

    def plotOverall(self, forecast_df, output_path):
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

    def plotAccountTypeTotals(self, forecast_df, output_path):
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
        # aggregate by account type: Principal Balance + interest, checking, previous + current statement balance, savings
        checking_df = pd.DataFrame(forecast_df.Checking.copy())
        savings_df = pd.DataFrame(forecast_df.Savings.copy())
        date_df = pd.DataFrame(forecast_df.Date.copy())

        zero_df = pd.DataFrame(np.zeros((checking_df.shape[0], 1)))
        cc_df = pd.DataFrame(zero_df.copy())
        loan_df = pd.DataFrame(zero_df.copy())

        cc_colnames = [s for s in forecast_df.columns.tolist() if 'Statement Balance' in s]
        loan_colnames = [s for s in forecast_df.columns.tolist() if 'Interest' in s] + [s for s in
                                                                                        forecast_df.columns.tolist() if
                                                                                        'Principal Balance' in s]

        cc_df = pd.DataFrame(forecast_df.loc[:, cc_colnames].sum(axis=1))

        loan_df = pd.DataFrame(forecast_df.loc[:, loan_colnames].sum(axis=1))

        date_df.reset_index(drop=True, inplace=True)
        checking_df.reset_index(drop=True, inplace=True)
        savings_df.reset_index(drop=True, inplace=True)
        cc_df.reset_index(drop=True, inplace=True)
        loan_df.reset_index(drop=True, inplace=True)

        loan_df = loan_df.rename(columns={0: "Loan"})
        cc_df = cc_df.rename(columns={0: "Credit"})

        agg_df = pd.concat([date_df, checking_df, savings_df, cc_df, loan_df], axis=1)

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

    def plotMarginalInterest(self, accounts_df, forecast_df, output_path):
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
        # todo plotMarginalInterest():: this will have to get the cc interest from the memo line
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

    def compute_forecast_difference(self, forecast_df, forecast2_df,
                                    label='forecast_difference',
                                    make_plots=False,
                                    plot_directory='.',
                                    return_type='dataframe',
                                    require_matching_columns=False,
                                    require_matching_date_range=False,
                                    append_expected_values=False,
                                    diffs_only=False):

        forecast_df = self.forecast_df.reindex(sorted(forecast_df.columns), axis=1)
        forecast2_df = forecast2_df.reindex(sorted(forecast2_df.columns), axis=1)

        forecast_df.reset_index(inplace=True, drop=True)
        forecast2_df.reset_index(inplace=True, drop=True)

        # print('compute_forecast_difference()')
        # print('self.forecast_df:')
        # print(self.forecast_df.to_string())
        # print('forecast2_df:')
        # print(forecast2_df.to_string())

        # return_type in ['dataframe','html','both']
        # make
        # I want the html table to have a row with values all '...' for non-consecutive dates
        # Data frame will not return rows that match

        if require_matching_columns:
            try:
                assert forecast_df.shape[1] == forecast2_df.shape[1]
                assert set(forecast_df.columns) == set(forecast2_df.columns)
            except Exception as e:
                print('ERROR: ATTEMPTED TO TAKE DIFF OF FORECASTS WITH DIFFERENT COLUMNS')
                # print('# Check Number of Columns:')
                # print('self.forecast_df.shape[1]:'+str(self.forecast_df.shape[1]))
                # print('forecast2_df.shape[1]....:'+str(forecast2_df.shape[1]))
                # print('')
                # print('# Check Column Names:')
                # print('set(self.forecast_df.columns):'+str(set(self.forecast_df.columns) ))
                # print('set(forecast2_df.columns)....:'+str(set(forecast2_df.columns)))
                # print('')
                raise e

        if require_matching_date_range:
            try:
                assert min(forecast_df['Date']) == min(forecast2_df['Date'])
                assert max(forecast_df['Date']) == max(forecast2_df['Date'])
            except Exception as e:
                print('ERROR: ATTEMPTED TO TAKE DIFF OF FORECASTS WITH DIFFERENT DATE RANGE')
                print('LHS: ' + str(min(forecast_df['Date'])) + ' - ' + str(max(forecast_df['Date'])))
                print('RHS: ' + str(min(forecast2_df['Date'])) + ' - ' + str(max(forecast2_df['Date'])))
                # print('# Check Min Date Range:')
                # print('min(self.forecast_df[\'Date\']):'+str())
                # print('min(forecast_df2[\'Date\']):'+str())
                # print('')
                # print('# Check Max Date Range:')
                # print('max(self.forecast_df[\'Date\']):'+str())
                # print('max(forecast_df2[\'Date\']):'+str())
                # print('')
                raise e
        else:
            overlapping_date_range = set(forecast_df['Date']) & set(forecast2_df['Date'])
            LHS_only_dates = set(forecast_df['Date']) - set(forecast2_df['Date'])
            RHS_only_dates = set(forecast2_df['Date']) - set(forecast_df['Date'])
            if len(overlapping_date_range) == 0:
                raise ValueError  # the date ranges for the forecasts being compared are disjoint

            LHS_columns = forecast_df.columns
            LHS_example_row = pd.DataFrame(forecast_df.iloc[0, :]).copy().T
            LHS_example_row.columns = LHS_columns
            # print('LHS_example_row:')
            # print(LHS_example_row.to_string())
            # print('LHS_example_row.columns:')
            # print(LHS_example_row.columns)
            for cname in LHS_example_row.columns:
                if cname == 'Date':
                    continue
                elif cname == 'Memo':
                    LHS_example_row[cname] = ''
                else:
                    LHS_example_row[cname] = float("nan")

            for dt in RHS_only_dates:
                LHS_zero_row_to_add = LHS_example_row.copy()
                LHS_zero_row_to_add['Date'] = dt
                forecast_df = pd.concat([LHS_zero_row_to_add, forecast_df])
            forecast_df.sort_values(by='Date', inplace=True, ascending=True)

            RHS_example_row = pd.DataFrame(forecast2_df.iloc[0, :]).copy()
            for cname in RHS_example_row.columns:
                if cname == 'Date':
                    continue
                elif cname == 'Memo':
                    RHS_example_row[cname] = ''
                else:
                    RHS_example_row[cname] = float("nan")

            for dt in LHS_only_dates:
                RHS_zero_row_to_add = RHS_example_row.copy()
                RHS_zero_row_to_add['Date'] = dt
                forecast2_df = pd.concat([RHS_zero_row_to_add, self.forecast_df])
            forecast2_df.sort_values(by='Date', inplace=True, ascending=True)

        if diffs_only == True:
            return_df = forecast_df[['Date', 'Memo']].copy()
        else:
            return_df = forecast_df.copy()
        return_df.reset_index(inplace=True, drop=True)

        # print(return_df.columns)
        # print('BEFORE return_df:\n' + return_df.to_string())

        relevant_column_names__set = set(forecast_df.columns) - set(['Date', 'Memo'])
        # print('relevant_column_names__set:'+str(relevant_column_names__set))
        assert set(forecast_df.columns) == set(forecast2_df)
        for c in relevant_column_names__set:
            new_column_name = str(c) + ' (Diff) '
            # print('new_column_name:'+str(new_column_name))
            res = pd.DataFrame(forecast2_df[c] - forecast_df[c])
            # res = forecast2_df[c].sub(self.forecast_df[c])
            res.reset_index(inplace=True, drop=True)
            # print('res:'+str(res))
            return_df[new_column_name] = res

        if append_expected_values:
            for cname in forecast2_df.columns:
                if cname == 'Memo' or cname == 'Date':
                    continue
                return_df[cname + ' (Expected)'] = forecast2_df[cname]

        return_df.index = return_df['Date']

        # print(return_df.columns)
        # print('AFTER return_df:\n' + return_df.to_string())

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
            # todo draw plots

        return_df = return_df.reindex(sorted(return_df.columns), axis=1)

        return return_df


# written in one line so that test coverage can reach 100%
# if __name__ == "__main__": import doctest ; doctest.testmod()
if __name__ == "__main__":
    pass

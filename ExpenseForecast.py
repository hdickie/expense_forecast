import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
import datetime
import re
from hd_util import *

class ExpenseForecast:

    def __init__(self):

        #TODO assert consistency between accountset and budgetset

        #todo assert that satisfice memo rules have been defined

        pass

    def satisfice(self, budget_schedule_df, account_set_df, memo_rules_df):

        priority_1_budget_schedule_df = budget_schedule_df.loc[budget_schedule_df.Priority == 1, :]

        min_sched_date = min(budget_schedule_df.Date)
        max_sched_date = max(budget_schedule_df.Date)

        all_days = pd.date_range(min_sched_date, max_sched_date)

        date_only_df = pd.DataFrame(['Date',min_sched_date]).T

        accounts_only_df = pd.DataFrame( account_set_df.iloc[:,0:1] ).T
        accounts_only_df.reset_index(inplace=True,drop=True)
        accounts_only_df.columns = accounts_only_df.iloc[0]


        starting_zero_balances_df = pd.DataFrame([0]*account_set_df.shape[0]).T
        starting_zero_balances_df.reset_index(inplace=True,drop=True)
        starting_zero_balances_df.columns = accounts_only_df.iloc[0]

        accounts_only_df = pd.concat([accounts_only_df,starting_zero_balances_df]).T
        accounts_only_df.reset_index(drop=True,inplace=True)
        accounts_only_df.columns = [0,1]

        memo_only_df = pd.DataFrame(['Memo','']).T

        forecast_df = pd.concat([
            date_only_df,
            accounts_only_df,
            memo_only_df
            ])

        forecast_df = forecast_df.T
        forecast_df.columns = forecast_df.iloc[0,:]
        forecast_df = forecast_df[1:]
        forecast_df.reset_index(drop=True,inplace=True)

        #set initial values
        for i in range(0,account_set_df.shape[0]):
            row = account_set_df.iloc[i,:]
            forecast_df.iloc[0, 1 + i] = row.Balance


        for d in all_days:
            if d == forecast_df.iloc[0,0]:
                previous_date = d
                continue #we consider the starting balances finalized
            new_row_df = forecast_df[forecast_df.Date == previous_date].copy()
            new_row_df.Date = d
            new_row_df.Memo = ''

            relevant_budget_items_df = priority_1_budget_schedule_df.loc[ d == priority_1_budget_schedule_df.Date, : ]
            relevant_budget_items_df.sort_values(inplace=True, axis=0, by="Amount",ascending=False)

            # todo interest accruals. shouldnt happen every day as it does ats it is currently implemented
            for index, row in account_set_df.iterrows():
                index_of_relevant_column_balance = list(new_row_df.columns).index(row.Name)

                if row['APR'] == 0:
                    continue

                #todo if not an interest accrual day, continue

                days_since_billing_start_date = (d - row['Billing_Start_Dt']).days


                relevant_apr = row['APR']
                relevant_balance = new_row_df.iloc[0,index_of_relevant_column_balance]
                if row['Interest_Cadence'].lower() == 'daily':
                    new_balance = relevant_balance + ( relevant_balance * relevant_apr ) / 365.25
                elif row['Interest_Cadence'].lower() == 'monthly':

                    interest_accrual_days = generate_date_sequence(row['Billing_Start_Dt'].strftime('%Y%m%d'), days_since_billing_start_date + 10, 'monthly')
                    if d in interest_accrual_days:
                        print('doing a monthly interest accrual calculation '+str(d)+' '+str(row))
                        new_balance = relevant_balance + ( relevant_balance * relevant_apr) / 12
                    else:
                        new_balance = relevant_balance
                elif row['Interest_Cadence'].lower() == 'yearly':
                    interest_accrual_days = generate_date_sequence(row['Billing_Start_Dt'].strftime('%Y%m%d'),
                                                                   days_since_billing_start_date + 10, 'yearly')
                    if d in interest_accrual_days:
                        new_balance = relevant_balance + (relevant_balance * relevant_apr)
                    else:
                        new_balance = relevant_balance
                else:
                    print('Undefined case in satisfice()')

                #print(str(d)+' Updating balance '+str(row.Name)+' '+str(relevant_balance)+' -> '+str(new_balance))
                new_row_df.iloc[0, index_of_relevant_column_balance] = new_balance

            #todo execute non-neogtiable transactions
            for index, budget_item in relevant_budget_items_df.iterrows():
                #if memo matches any regex in memo_rules_df
                    #relevant_memo_rule = memo_rules_df[memo_rules_df.transaction_priority == 1 and memo_rules_df]

                #use first regex match
                found_matching_regex = False
                for index2, row2 in memo_rules_df[memo_rules_df.transaction_priority == 1].iterrows():
                    m = re.search(row2.memo_regex,budget_item.Memo)

                    if m is not None:
                        #do stuff

                        if row2.account_from is not None:
                            index_of_account_from_column = list(new_row_df.columns).index(row2.account_from)

                        if row2.account_to is not None:
                            index_of_account_to_column = list(new_row_df.columns).index(row2.account_to)

                        if row2.account_from is not None: #e.g. income
                            new_row_df.iloc[0, index_of_account_from_column] += budget_item.Amount

                        if row2.account_to is not None: #e.g. spend
                            new_row_df.iloc[0, index_of_account_to_column] += budget_item.Amount

                        if row2.account_from is not None and row2.account_to is not None:  # e.g. xfer bw accts
                            new_row_df.iloc[0, index_of_account_to_column] += budget_item.Amount
                            new_row_df.iloc[0, index_of_account_from_column] -= budget_item.Amount

                        found_matching_regex = True
                        break

                if not found_matching_regex:
                    print('We received a budget item that we do not have a case to handle. this is a show stopping error.')
                    print('Exiting.')
                else: #update memo
                    if new_row_df.loc[0,'Memo'] != '':
                        new_row_df.loc[0,'Memo'] = new_row_df.loc[0,'Memo'] + '; '

                    new_memo_text = ""
                    if row2.account_from is not None:
                        new_memo_text = new_memo_text + str(row2.account_from) + ' ' + str(-1*abs(budget_item.Amount)) + ' '

                    if row2.account_to is not None:
                        new_memo_text = new_memo_text + str(row2.account_to) + ' ' + str(budget_item.Amount) + ' '

                    new_row_df.loc[0, 'Memo'] = new_row_df.loc[0,'Memo'] + new_memo_text


            previous_date = d
            forecast_df = pd.concat([forecast_df,new_row_df])


        updated_budget_schedule_df = budget_schedule_df.loc[budget_schedule_df.Priority != 1,:]
        updated_budget_schedule_df.sort_values(inplace=True, axis=0, by="Date")
        updated_budget_schedule_df.reset_index(inplace=True, drop=True)

        #account_set_df is returned unchanged. we depend on optimize logic to not violate boundaries by checking the forecast
        return [updated_budget_schedule_df, account_set_df, forecast_df]

    def optimize_next_choice(self,updated_budget_schedule_df,account_set_df,forecast_df):

        updated_account_set_df = account_set_df
        updated_forecast_df = forecast_df




        updated_budget_schedule_df.sort_values(inplace=True, axis=0, by="Date")
        updated_budget_schedule_df.reset_index(inplace=True, drop=True)

        return [updated_budget_schedule_df,account_set_df,forecast_df]



    def computeForecast(self,budget_schedule_df, account_set_df, memo_rules_df):
        return self.satisfice(budget_schedule_df, account_set_df, memo_rules_df)


    def plotOutput(self,forecast_df,output_path):
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

        # TODO a large number of accounts will require some adjustment here so that the legend is entirely visible

        min_date = min(forecast_df.Date).strftime('%Y-%m-%d')
        max_date = max(forecast_df.Date).strftime('%Y-%m-%d')
        plt.title('Forecast: ' + str(min_date) + ' -> ' + str(max_date))
        plt.savefig(output_path)

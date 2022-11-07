import pandas as pd, numpy as np
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


        #print('initial forecast values pre assignment:')
        #print(forecast_df.to_string())

        #set initial values
        for i in range(0,account_set_df.shape[0]):
            row = account_set_df.iloc[i, :]
            #print('row:'+str(row))
            #print('Setting '+forecast_df.columns.tolist()[i+1]+' = '+str(row.Balance))

            if row.Account_Type.lower() == 'interest':
                forecast_df.iloc[0, 1 + i] = row.Accrued_Interest #the +1 is on the index here bc we are iterating over account_df not forecast_df
            else:
                forecast_df.iloc[0, 1 + i] = row.Balance

        #print('initial forecast values post assignment:')
        #print(forecast_df.to_string())

        #todo, we make minimum payments on loans and credit cards before interest for this day is calculated
        #in order for this to work, it is easiest if additional payments are made before the due date


        index_of_checking_column = forecast_df.columns.tolist().index('Checking')
        for d in all_days:
            if d == forecast_df.iloc[0,0]:
                previous_date = d
                continue #we consider the starting balances finalized
            new_row_df = forecast_df[forecast_df.Date == previous_date].copy()
            new_row_df.Date = d
            new_row_df.Memo = ''

            relevant_budget_items_df = priority_1_budget_schedule_df.loc[ d == priority_1_budget_schedule_df.Date, : ]
            relevant_budget_items_df.sort_values(inplace=True, axis=0, by="Amount",ascending=False)

            #here, interest is calculated and current statement balances are moved to previous
            for index, row in account_set_df.iterrows():
                if row['APR'] == 0:
                    continue

                if row['Account_Type'].lower() not in ['previous statement balance','interest']:
                    continue

                days_since_billing_start_date = (d - row['Billing_Start_Dt']).days

                if row['Interest_Cadence'].lower() == 'daily':
                    pass #we want to continue processing
                elif row['Interest_Cadence'].lower() == 'monthly':
                    interest_accrual_days = generate_date_sequence(row['Billing_Start_Dt'].strftime('%Y%m%d'),
                                                                   days_since_billing_start_date + 10, 'monthly')
                    #print('checking if this is a day for monthly interest accrual')
                    #print('? is '+str(d)+' in '+str(interest_accrual_days))
                    if d not in interest_accrual_days:
                        continue
                elif row['Interest_Cadence'].lower() == 'yearly':
                    interest_accrual_days = generate_date_sequence(row['Billing_Start_Dt'].strftime('%Y%m%d'),
                                                                   days_since_billing_start_date + 10, 'yearly')
                    if d not in interest_accrual_days:
                        continue
                else:
                    print('Undefined case in satisfice()')

                #at this point, we know we are about to calculate interest. how we do that depends on cadence and account type

                relevant_apr = row['APR']
                #print('row:'+str(row))
                if row['Account_Type'].lower() == 'previous statement balance' and row['Interest_Cadence'].lower() == 'monthly':

                    # total_debt = forecast_df.iloc[0, i] + forecast_df.iloc[0, i + 1] #i is current, i + 1 is previous
                    available_funds = new_row_df.iloc[0, index_of_checking_column]
                    # current_statement_balance = forecast_df.iloc[0, i]
                    previous_statement_balance = new_row_df.iloc[0, index + 1] #plus 1 bc index is an iterative cursor for accounts_df not forecast_df

                    # scenarios
                    # 1. make cc min payment only. bal is less than $40
                    # 2. make cc min payment only. bal is more than $40 and less than $2k
                    # 3. make cc min payment only. bal is more than $2k. min payment is 2%
                    # 4. make cc min payment. combined current and prev statement balance less than $40, both non 0%

                    # scenarios: previous statement balance and payment in excess of minimum

                    # 5. make cc payment in excess of minimum. current statement more than $40, pay less than total balance.
                    # 6. make cc payment in excess of minimum. current statement more than $40, pay less than total balance, when balance is greater than checking
                    # 7. make cc payment in excess of minimum. current statement more than $2k, pay more than total balance.

                    if available_funds > previous_statement_balance and previous_statement_balance <= 40:
                        new_row_df.iloc[0, index_of_checking_column] -= previous_statement_balance
                        new_row_df.iloc[0, i + 1] = 0  # pay previous statement balance
                        # todo update memo
                    elif available_funds > previous_statement_balance and 40 < previous_statement_balance and previous_statement_balance <= 2000:
                        new_row_df.iloc[0, index_of_checking_column] -= 40
                        new_row_df.iloc[0, i + 1] -= 40  # pay previous statement balance
                        # todo update memo
                    elif available_funds > previous_statement_balance and 2000 <= previous_statement_balance:
                        min_payment_amt = previous_statement_balance * 0.02
                        new_row_df.iloc[0, index_of_checking_column] -= min_payment_amt
                        new_row_df.iloc[0, i + 1] -= min_payment_amt  # pay previous statement balance
                        # todo update memo

                    #interest accrual and balance transfer
                    index_of_previous_statement_balance = new_row_df.columns.tolist().index(row.Name)
                    previous_statement_balance = new_row_df.iloc[0, index_of_previous_statement_balance]

                    index_of_current_statement_balance = index_of_previous_statement_balance - 1
                    current_statement_balance = new_row_df.iloc[0, index_of_current_statement_balance]

                    #move current statement balance to previous and add interest
                    new_row_df.iloc[0,index_of_previous_statement_balance] = current_statement_balance + previous_statement_balance + previous_statement_balance*relevant_apr/12
                    new_row_df.iloc[0, index_of_current_statement_balance] = 0

                elif row['Account_Type'].lower() == 'interest' and row['Interest_Cadence'].lower() == 'daily':
                    index_of_accrued_interest = new_row_df.columns.tolist().index(row.Name)
                    index_of_principal_balance = index_of_accrued_interest - 1

                    new_row_df.iloc[0, index_of_accrued_interest] += new_row_df.iloc[0, index_of_principal_balance]*relevant_apr/365.25

                elif row['Account_Type'].lower() == 'interest' and row['Interest_Cadence'].lower() == 'monthly':
                    index_of_accrued_interest = new_row_df.columns.tolist().index(row.Name)
                    index_of_principal_balance = index_of_accrued_interest - 1

                    new_row_df.iloc[0, index_of_accrued_interest] += new_row_df.iloc[
                                                                         0, index_of_principal_balance] * relevant_apr / 12
                elif row['Account_Type'].lower() == 'interest' and row['Interest_Cadence'].lower() == 'yearly':
                    index_of_accrued_interest = new_row_df.columns.tolist().index(row.Name)
                    index_of_principal_balance = index_of_accrued_interest - 1

                    new_row_df.iloc[0, index_of_accrued_interest] += new_row_df.iloc[
                                                                         0, index_of_principal_balance] * relevant_apr
                else:
                    print('Undefined case in satisfice()')

            #other priority 1 transactions
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

        #this needs to be able to accept "*", meaning "free balance"


        updated_budget_schedule_df.sort_values(inplace=True, axis=0, by="Date")
        updated_budget_schedule_df.reset_index(inplace=True, drop=True)

        return [updated_budget_schedule_df,account_set_df,forecast_df]



    def computeForecast(self,budget_schedule_df, account_set_df, memo_rules_df):
        return self.satisfice(budget_schedule_df, account_set_df, memo_rules_df)


    def plotOverall(self,forecast_df,output_path):
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

    def plotAccountTypeTotals(self,forecast_df,output_path):
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
        pass

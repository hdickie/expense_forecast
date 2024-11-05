
import pandas as pd
import re
import MemoMilestone
import CompositeMilestone
import AccountMilestone
import jsonpickle

def initialize_from_dataframe(account_milestones_df, memo_milestones_df, composite_milestones_df):

    am__list = []
    mm__list = []
    cm__list = []

    am__dict = {}
    mm__dict = {}

    for index, row in account_milestones_df.iterrows():
        new_AM = AccountMilestone.AccountMilestone(row.milestone_name,row.account_name,row.min_balance,row.max_balance)
        am__list += [ new_AM ]
        am__dict[row.milestone_name] = new_AM

    for index, row in memo_milestones_df.iterrows():
        new_MM = MemoMilestone.MemoMilestone(row.milestone_name,row.memo_regex)
        mm__list += [ new_MM ]
        mm__dict[row.milestone_name] = new_MM

    for index, row in composite_milestones_df.iterrows():
        AM_names = row.account_milestone_name_list.split(';')
        MM_names = row.memo_milestone_name_list.split(';')
        related_AM = []
        related_MM = []
        for AM_name in AM_names:
            related_AM.append(am__dict[AM_name])
        for MM_name in MM_names:
            related_MM.append(mm__dict[MM_name])
        cm__list += [ CompositeMilestone.CompositeMilestone(row.composite_milestone_name,related_AM,related_MM) ]

    return MilestoneSet(am__list,mm__list,cm__list)

class MilestoneSet:

    def __init__(self,account_milestones__list=None,memo_milestones__list=None,composite_milestones__list=None):

        # for account_milestone in account_milestones__list:
        #     all_account_names = set([ a.split(':')[0] for a in account_set.getAccounts().Name ])
        #     if not account_milestone.account_name in all_account_names:
        #         raise ValueError("Account Name for Milestone not found in accounts: "+str(account_milestone.account_name))

        if account_milestones__list is None:
            account_milestones__list = []

        if memo_milestones__list is None:
            memo_milestones__list = []

        if composite_milestones__list is None:
            composite_milestones__list = []

        self.account_milestones = account_milestones__list

        # for memo_milestone in memo_milestones__list:
        #     match_found = False
        #     for index2, row2 in budget_set.getBudgetItems().iterrows():
        #         if re.search(memo_milestone.memo_regex,row2.Memo) is not None:
        #             match_found = True
        #
        #     if not match_found:
        #         raise ValueError("Memo Milestone had no matches in budgetset, so no match during forecast calculation is possible.")

        self.memo_milestones = memo_milestones__list

        # for cm in composite_milestones__list:
        #     for account_milestone in cm.account_milestones:
        #         all_account_names = set([ a.split(':')[0] for a in account_set.getAccounts().Name ])
        #         if not account_milestone.account_name in all_account_names:
        #             raise ValueError("Account Name for Milestone in Composite Milestone not found in accounts: "+str(account_milestone.account_name))
        #
        #     for memo_milestone in memo_milestones__list:
        #         match_found = False
        #         for index2, row2 in budget_set.getBudgetItems().iterrows():
        #             if re.search(memo_milestone.memo_regex,row2.Memo) is not None:
        #                 match_found = True
        #
        #         if not match_found:
        #             raise ValueError("Memo Milestone in Composite Milestone had no matches in budgetset, so no match during forecast calculation is possible.")

        self.composite_milestones = composite_milestones__list

    def __str__(self):

        return_string = ""

        count_of_milestones = int(len(self.memo_milestones)) + int(len(self.account_milestones)) + int(len(self.composite_milestones))
        return_string += "Total # of Milestones: "+str(count_of_milestones)+"\n"

        return_string += "Memo Milestones:\n"
        for M in self.memo_milestones:
            return_string += str(M)+"\n"

        return_string += "Account Milestones:\n"
        for A in self.account_milestones:
            return_string += str(A) + "\n"

        return_string += "Composite Milestones:\n"
        for C in self.composite_milestones:
            return_string += str(C) + "\n"

        return return_string


    def addMemoMilestone(self,milestone_name,memo_regex_string):
        self.memo_milestones += [ MemoMilestone.MemoMilestone(milestone_name,memo_regex_string) ]

    def addAccountMilestone(self,milestone_name,account_name,min_balance,max_balance):
        self.account_milestones += [ AccountMilestone.AccountMilestone(milestone_name,account_name,min_balance,max_balance) ]

    def addCompositeMilestone(self,milestone_name,account_milestones__list, memo_milestones__list):
        #todo raise error if input milestones did not already exist #https://github.com/hdickie/expense_forecast/issues/22
        self.composite_milestones += [ CompositeMilestone.CompositeMilestone(milestone_name,account_milestones__list, memo_milestones__list) ]

    def to_json(self):
        return jsonpickle.encode(self, indent=4, unpicklable=False)

    def getAccountMilestonesDF(self):

        account_milestones_df = pd.DataFrame({'Milestone_Name': [],
                                        'Account_Name': [],
                                        'Min_Balance': [],
                                        'Max_Balance': []
                                        })

        for a in self.account_milestones:
            account_milestones_df = pd.concat([account_milestones_df,
                          pd.DataFrame({'Milestone_Name': [a.milestone_name],
                                        'Account_Name': [a.account_name],
                                        'Min_Balance': [a.min_balance],
                                        'Max_Balance': [a.max_balance]
                                        })])
        account_milestones_df.reset_index(drop=True, inplace=True)
        return account_milestones_df

    def getMemoMilestonesDF(self):
        memo_milestones_df = pd.DataFrame({'Milestone_Name': [],
                                        'Memo_Regex': []
                                        })

        for m in self.memo_milestones:
            memo_milestones_df = pd.concat([memo_milestones_df,
                          pd.DataFrame({'Milestone_Name': [m.milestone_name],
                                        'Memo_Regex': [m.memo_regex]
                                        })])
        memo_milestones_df.reset_index(drop=True,inplace=True)
        return memo_milestones_df

    def getCompositeMilestonesDF(self):
        composite_milestone_df = pd.DataFrame({'Composite_Milestone_Name': [],
                                               'Milestone_Type': [],
                                               'Milestone_Name': []
                                           })

        for cm in self.composite_milestones:
            for am in cm.account_milestones:
                composite_milestone_df = pd.concat([composite_milestone_df, pd.DataFrame({'Composite_Milestone_Name': [cm.milestone_name],
                                               'Milestone_Type': ['Account'],
                                               'Milestone_Name': [am.milestone_name]
                                           }) ])

            for mm in cm.memo_milestones:
                composite_milestone_df = pd.concat([composite_milestone_df,pd.DataFrame({'Composite_Milestone_Name': [cm.milestone_name],
                                               'Milestone_Type': ['Memo'],
                                               'Milestone_Name': [mm.milestone_name]
                                           })])
        composite_milestone_df.reset_index(drop=True, inplace=True)
        return composite_milestone_df

    def evaluateMilestones(self):

        account_milestone_results = {}
        for a_m in self.account_milestones:
            res = self.evaluateAccountMilestone(a_m.account_name, a_m.min_balance, a_m.max_balance)
            account_milestone_results[a_m.milestone_name] = res
        self.account_milestone_results = account_milestone_results

        memo_milestone_results = {}
        for m_m in self.memo_milestones:
            res = self.evaulateMemoMilestone(m_m.memo_regex)
            memo_milestone_results[m_m.milestone_name] = res
        self.memo_milestone_results = memo_milestone_results

        composite_milestone_results = {}
        for c_m in self.composite_milestones:
            res = self.evaluateCompositeMilestone(c_m.account_milestones,
                                                  c_m.memo_milestones)
            composite_milestone_results[c_m.milestone_name] = res
        self.composite_milestone_results = composite_milestone_results


    def evaluateAccountMilestone(self,account_name,min_balance,max_balance):
        log_in_color(logger,'yellow','debug','ENTER evaluateAccountMilestone('+str(account_name)+','+str(min_balance)+','+str(max_balance)+')',self.log_stack_depth)
        self.log_stack_depth += 1
        account_info = self.initial_account_set.getAccounts()
        account_base_names = [ a.split(':')[0] for a in account_info.Name ]
        row_sel_vec = [ a == account_name for a in account_base_names]

        relevant_account_info_rows_df = account_info[row_sel_vec]
        log_in_color(logger, 'yellow', 'debug', 'relevant_account_info_rows_df:')
        log_in_color(logger, 'yellow', 'debug',relevant_account_info_rows_df.to_string())

        #this df should be either 1 or 2 rows, but have same account type either way
        try:
            assert relevant_account_info_rows_df.Name.unique().shape[0] == 1
        except Exception as e:
            print(e)

        if relevant_account_info_rows_df.shape[0] == 1: #case for checking and savings
            col_sel_vec = self.forecast_df.columns == relevant_account_info_rows_df.head(1)['Name'].iat[0]
            col_sel_vec[0] = True
            relevant_time_series_df = self.forecast_df.iloc[:, col_sel_vec]

            # a valid success date stays valid until the end
            found_a_valid_success_date = False
            success_date = 'None'
            for index, row in relevant_time_series_df.iterrows():
                current_value = relevant_time_series_df.iloc[index, 1]
                if ((min_balance <= current_value) & (current_value <= max_balance)) and not found_a_valid_success_date:
                    found_a_valid_success_date = True
                    success_date = row.Date
                    log_in_color(logger, 'yellow', 'debug', 'success_date:'+str(success_date),self.log_stack_depth)
                elif ((min_balance > current_value) | (current_value > max_balance)):
                    found_a_valid_success_date = False
                    success_date = 'None'
                    log_in_color(logger, 'yellow', 'debug', 'success_date:None',self.log_stack_depth)

        elif relevant_account_info_rows_df.shape[0] == 2:  # case for credit and loan
            curr_stmt_bal_acct_name = relevant_account_info_rows_df.iloc[0,0]
            prev_stmt_bal_acct_name = relevant_account_info_rows_df.iloc[1, 0]

            # log_in_color(logger, 'yellow', 'debug', 'curr_stmt_bal_acct_name:')
            # log_in_color(logger, 'yellow', 'debug', curr_stmt_bal_acct_name)
            # log_in_color(logger, 'yellow', 'debug', 'prev_stmt_bal_acct_name:')
            # log_in_color(logger, 'yellow', 'debug', prev_stmt_bal_acct_name)

            col_sel_vec = self.forecast_df.columns == curr_stmt_bal_acct_name
            col_sel_vec = col_sel_vec | (self.forecast_df.columns == prev_stmt_bal_acct_name)
            col_sel_vec[0] = True #Date

            # log_in_color(logger, 'yellow', 'debug', 'col_sel_vec:')
            # log_in_color(logger, 'yellow', 'debug', col_sel_vec)

            relevant_time_series_df = self.forecast_df.iloc[:, col_sel_vec]

            #a valid success date stays valid until the end
            found_a_valid_success_date = False
            success_date = 'None'
            for index, row in relevant_time_series_df.iterrows():
                current_value = relevant_time_series_df.iloc[index,1] + relevant_time_series_df.iloc[index,2]
                if ((min_balance <= current_value) & (current_value <= max_balance)) and not found_a_valid_success_date:
                    found_a_valid_success_date = True
                    success_date = row.Date
                    log_in_color(logger, 'yellow', 'debug', 'success_date:' + str(success_date),self.log_stack_depth)
                elif ((min_balance > current_value) | (current_value > max_balance)):
                    found_a_valid_success_date = False
                    success_date = 'None'
                    log_in_color(logger, 'yellow', 'debug', 'success_date:None',self.log_stack_depth)

        # Summary lines
        elif account_name in ('Marginal Interest','Net Gain','Net Loss','Net Worth','Loan Total','CC Debt Total','Liquid Total'):
            col_sel_vec = self.forecast_df.columns == account_name
            col_sel_vec[0] = True
            relevant_time_series_df = self.forecast_df.iloc[:, col_sel_vec]

            # a valid success date stays valid until the end
            found_a_valid_success_date = False
            success_date = 'None'
            for index, row in relevant_time_series_df.iterrows():
                current_value = relevant_time_series_df.iloc[index, 1]
                if ((min_balance <= current_value) & (current_value <= max_balance)) and not found_a_valid_success_date:
                    found_a_valid_success_date = True
                    success_date = row.Date
                    log_in_color(logger, 'yellow', 'debug', 'success_date:' + str(success_date), self.log_stack_depth)
                elif ((min_balance > current_value) | (current_value > max_balance)):
                    found_a_valid_success_date = False
                    success_date = 'None'
                    log_in_color(logger, 'yellow', 'debug', 'success_date:None', self.log_stack_depth)
        else:
            raise ValueError("undefined edge case in ExpenseForecast::evaulateAccountMilestone""")

        # log_in_color(logger, 'yellow', 'debug', 'relevant_time_series_df:')
        # log_in_color(logger, 'yellow', 'debug', relevant_time_series_df.to_string())
        #
        # log_in_color(logger, 'yellow', 'debug', 'last_value:')
        # log_in_color(logger, 'yellow', 'debug', last_value)



        #
        # #if the last day of the forecast does not satisfy account bounds, then none of the days of the forecast qualify
        # if not (( min_balance <= last_value ) & ( last_value <= max_balance )):
        #     log_in_color(logger,'yellow', 'debug','EXIT evaluateAccountMilestone(' + str(account_name) + ',' + str(min_balance) + ',' + str(max_balance) + ') None')
        #     return None
        #
        # #if the code reaches this point, then the milestone was for sure reached.
        # #We can find the first day that qualifies my reverseing the sequence and returning the day before the first day that doesnt qualify
        # relevant_time_series_df = relevant_time_series_df.loc[::-1]
        # last_qualifying_date = relevant_time_series_df.head(1).Date.iat[0]
        # for index, row in relevant_time_series_df.iterrows():
        #     # print('row:')
        #     # print(row)
        #     # print(row.iloc[1])
        #     if (( min_balance <= row.iloc[1] ) & ( row.iloc[1] <= max_balance )):
        #         last_qualifying_date = row.Date.iat[0]
        #     else:
        #         break
        self.log_stack_depth -= 1
        log_in_color(logger,'yellow', 'debug','EXIT evaluateAccountMilestone(' + str(account_name) + ',' + str(min_balance) + ',' + str(max_balance) + ') '+str(success_date),self.log_stack_depth)
        return success_date

    def evaulateMemoMilestone(self,memo_regex):
        log_in_color(logger,'yellow', 'debug','ENTER evaluateMemoMilestone(' + str(memo_regex)+')',self.log_stack_depth)
        self.log_stack_depth += 1
        for forecast_index, forecast_row in self.forecast_df.iterrows():
            m = re.search(memo_regex,forecast_row.Memo)
            if m is not None:
                self.log_stack_depth -= 1
                log_in_color(logger,'yellow', 'debug', 'EXIT evaluateMemoMilestone(' + str(memo_regex) + ')',self.log_stack_depth)
                return forecast_row.Date

        self.log_stack_depth -= 1
        log_in_color(logger,'yellow', 'debug', 'EXIT evaluateMemoMilestone(' + str(memo_regex) + ')',self.log_stack_depth)
        return 'None'

    def evaluateCompositeMilestone(self,list_of_account_milestones,list_of_memo_milestones):
        log_in_color(logger, 'yellow', 'debug', 'ENTER evaluateCompositeMilestone()',self.log_stack_depth)
        self.log_stack_depth += 1
        #list_of_account_milestones is lists of 3-tuples that are (string,float,float) for parameters

        #todo composite milestones may contain some milestones that arent listed in the composite #https://github.com/hdickie/expense_forecast/issues/22

        num_of_acct_milestones = len(list_of_account_milestones)
        num_of_memo_milestones = len(list_of_memo_milestones)
        account_milestone_dates = []
        memo_milestone_dates = []

        for i in range(0,num_of_acct_milestones):
            account_milestone = list_of_account_milestones[i]
            am_result = self.evaluateAccountMilestone(account_milestone.account_name,account_milestone.min_balance,account_milestone.max_balance)
            if am_result is None: #disqualified immediately because success requires ALL
                self.log_stack_depth -= 1
                log_in_color(logger, 'yellow', 'debug', 'EXIT evaluateCompositeMilestone() None',self.log_stack_depth)
                return None
            account_milestone_dates.append(am_result)

        for i in range(0,num_of_memo_milestones):
            memo_milestone = list_of_memo_milestones[i]
            mm_result = self.evaulateMemoMilestone(memo_milestone.memo_regex)
            if mm_result is None:  # disqualified immediately because success requires ALL
                self.log_stack_depth -= 1
                log_in_color(logger, 'yellow', 'debug', 'EXIT evaluateCompositeMilestone() None',self.log_stack_depth)
                return None
            memo_milestone_dates.append(mm_result)

        result_date = max(account_milestone_dates + memo_milestone_dates)
        log_in_color(logger, 'yellow', 'debug', 'EXIT evaluateCompositeMilestone() '+str(result_date),self.log_stack_depth)
        self.log_stack_depth -= 1
        return result_date


    def getMilestoneResultsDF(self):
        if not hasattr(self,'forecast_df'):
            print('Forecast has not been run, so there are no results.')
            return

        milestone_results_df = pd.DataFrame({'Milestone_Name':[],
                                             'Milestone_Type': [],
                                             'Result_Date':[]})

        for key, value in self.account_milestone_results.items():
            milestone_results_df = pd.concat([milestone_results_df,
                                                  pd.DataFrame({'Milestone_Name': [ key ], 'Milestone_Type': [ 'Account' ], 'Result_Date': [ value ]}) ])

        for key, value in self.memo_milestone_results.items():
            milestone_results_df = pd.concat([milestone_results_df,
                                                  pd.DataFrame({'Milestone_Name': [ key ], 'Milestone_Type': [ 'Memo' ], 'Result_Date': [ value ]}) ])

        for key, value in self.composite_milestone_results.items():
            milestone_results_df = pd.concat([milestone_results_df,
                                                  pd.DataFrame({'Milestone_Name': [ key ], 'Milestone_Type': [ 'Composite' ], 'Result_Date': [ value ]}) ])



# def evaluateMilestones(self):
    #
    #     account_milestone_results = {}
    #     for a_m in self.milestone_set.account_milestones:
    #         res = self.evaluateAccountMilestone(a_m.account_name, a_m.min_balance, a_m.max_balance)
    #         account_milestone_results[a_m.milestone_name] = res
    #     self.account_milestone_results = account_milestone_results
    #
    #     memo_milestone_results = {}
    #     for m_m in self.milestone_set.memo_milestones:
    #         res = self.evaulateMemoMilestone(m_m.memo_regex)
    #         memo_milestone_results[m_m.milestone_name] = res
    #     self.memo_milestone_results = memo_milestone_results
    #
    #     composite_milestone_results = {}
    #     for c_m in self.milestone_set.composite_milestones:
    #         res = self.evaluateCompositeMilestone(c_m.account_milestones,
    #                                               c_m.memo_milestones)
    #         composite_milestone_results[c_m.milestone_name] = res
    #     self.composite_milestone_results = composite_milestone_results

    # def getAccountMilestoneResultsDF(self):
    #     return_df = pd.DataFrame({'Milestone_Name':[],'Date':[]})
    #     for key, value in self.account_milestone_results.items():
    #         try:
    #             value = datetime.datetime.strptime(value, '%Y%m%d')
    #         except:
    #             value = None
    #         return_df = pd.concat([return_df, pd.DataFrame({'Milestone_Name':[key],'Date':[ value ] })])
    #     return return_df

    # def getMemoMilestoneResultsDF(self):
    #     return_df = pd.DataFrame({'Milestone_Name': [], 'Date': []})
    #     for key, value in self.memo_milestone_results.items():
    #         try:
    #             value = datetime.datetime.strptime(value, '%Y%m%d')
    #         except:
    #             value = None
    #         return_df = pd.concat([return_df, pd.DataFrame({'Milestone_Name': [key], 'Date': [value]})])
    #     return return_df


    # def getCompositeMilestoneResultsDF(self):
    #     return_df = pd.DataFrame({'Milestone_Name': [], 'Date': []})
    #     for key, value in self.composite_milestone_results.items():
    #         try:
    #             value = datetime.datetime.strptime(value, '%Y%m%d')
    #         except:
    #             value = None
    #         return_df = pd.concat([return_df, pd.DataFrame({'Milestone_Name': [key], 'Date': [value]})])
    #     return return_df
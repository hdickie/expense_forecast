import copy
import os
import MilestoneSet
import ExpenseForecast, datetime
from log_methods import log_in_color
import BudgetSet
import json
import pandas as pd
import multiprocessing as mp
import AccountSet
import BudgetSet
import MemoRuleSet
import re
import hashlib
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
import AccountMilestone
import MemoMilestone
import CompositeMilestone
import matplotlib.dates
import matplotlib.patches as mpatches
import logging
import numpy as np
import matplotlib.cm as cm
import plotly.graph_objects as go

from log_methods import setup_logger
logger = setup_logger('ForecastHandler', './log/ForecastHandler.log', level=logging.DEBUG)

# e.g. custom_cycler = (cycler(color=['c', 'm', 'y', 'k']) + cycler(lw=[1, 2, 3, 4]))
# here, lw results in different types of dotted lines
default_color_cycle_list = ['blue','orange','green']
lw_cycle_list = [1, 2, 3, 4]

class ForecastHandler:

    def __init__(self):
        pass

    # def initialize_from_excel_file(self,path_to_excel_file):
    #     AccountSet_df = pd.read_excel(path_to_excel_file, sheet_name='AccountSet')
    #     BudgetSet_df = pd.read_excel(path_to_excel_file, sheet_name='BudgetSet')
    #     MemoRuleSet_df = pd.read_excel(path_to_excel_file, sheet_name='MemoRuleSet')
    #     ChooseOneSet_df = pd.read_excel(path_to_excel_file, sheet_name='ChooseOneSet')
    #
    #     AccountMilestones_df = pd.read_excel(path_to_excel_file, sheet_name='AccountMilestones')
    #     MemoMilestones_df = pd.read_excel(path_to_excel_file, sheet_name='MemoMilestones')
    #     CompositeMilestones_df = pd.read_excel(path_to_excel_file, sheet_name='CompositeMilestones')
    #
    #     config_df = pd.read_excel(path_to_excel_file, sheet_name='config')
    #     start_date_YYYYMMDD = config_df.Start_Date_YYYYMMDD.iat[0]
    #     end_date_YYYYMMDD = config_df.End_Date_YYYYMMDD.iat[0]
    #     output_directory = config_df.Output_Directory.iat[0]
    #
    #     A = AccountSet.AccountSet([])
    #     M = MemoRuleSet.MemoRuleSet([])
    #
    #     for account_index, account_row in AccountSet_df.iterrows():
    #         A.createAccount(account_row.Account_Name,
    #                         account_row.Balance,
    #                         account_row.Min_Balance,
    #                         account_row.Max_Balance,
    #                         account_row.Account_Type,
    #                         billing_start_date_YYYYMMDD=account_row.Billing_Start_Date_YYYYMMDD,
    #                         interest_type=account_row.Interest_Type,
    #                         apr=account_row.APR,
    #                         interest_cadence=account_row.Interest_Cadence,
    #                         minimum_payment=account_row.Minimum_Payment,
    #                         previous_statement_balance=account_row.Previous_Statement_Balance,
    #                         principal_balance=account_row.Principal_Balance,
    #                         accrued_interest=account_row.Accrued_Interest)
    #
    #     for memorule_index, memorule_row in MemoRuleSet_df.iterrows():
    #         M.addMemoRule(memorule_row.Memo_Regex,memorule_row.Account_From,memorule_row.Account_To,memorule_row.Transaction_Priority)
    #
    #     # number_of_combinations = 1
    #     self.choose_one_set_df = ChooseOneSet_df
    #     set_ids = ChooseOneSet_df.Choose_One_Set_Id.unique()
    #     set_ids.sort()
    #     # for set_id in set_ids:
    #     #     all_options_for_set = ChooseOneSet_df[ChooseOneSet_df.Choose_One_Set_Id == set_id,:]
    #     #     number_of_combinations = number_of_combinations * all_options_for_set.shape[0]
    #     master_list = ['']
    #     master_list_option_ids = ['']
    #     for set_id in set_ids:
    #         all_options_for_set = ChooseOneSet_df.loc[ChooseOneSet_df.Choose_One_Set_Id == set_id]
    #         current_list=[]
    #         current_list_option_ids = []
    #         for option_index, option_row in all_options_for_set.iterrows():
    #             for l in master_list:
    #                 current_list.append(l + ';' + option_row.Memo_Regex_List)
    #
    #             for l in master_list_option_ids:
    #                 current_list_option_ids.append(l+str(set_id)+'='+str(option_row.Option_Id)+' ')
    #
    #         master_list = current_list
    #         master_list_option_ids = current_list_option_ids
    #
    #
    #     budget_set_list = []
    #     for l in master_list:
    #         B = BudgetSet.BudgetSet([])
    #         for budget_item_index, budget_item_row in BudgetSet_df.iterrows():
    #             for memo_regex in l.split(';'):
    #                 if memo_regex == '':
    #                     continue
    #
    #                 if re.search(memo_regex,budget_item_row.Memo) is not None:
    #                     #print(memo_regex + ' ?= ' + str(budget_item_row.Memo)+" YES")
    #                     B.addBudgetItem(start_date_YYYYMMDD=budget_item_row.Start_Date,
    #                      end_date_YYYYMMDD=budget_item_row.End_Date,
    #                      priority=budget_item_row.Priority,
    #                      cadence=budget_item_row.Cadence,
    #                      amount=budget_item_row.Amount,
    #                      memo=budget_item_row.Memo,
    #                      deferrable=budget_item_row.Deferrable,
    #                      partial_payment_allowed=budget_item_row.Partial_Payment_Allowed
    #                                     )
    #
    #                     break
    #                 else:
    #                     pass
    #                     #print(memo_regex + ' ?= ' + str(budget_item_row.Memo)+" NO")
    #         budget_set_list.append(B)
    #
    #     account_milestones__list = []
    #     for index, row in AccountMilestones_df.iterrows():
    #         account_milestones__list.append(AccountMilestone.AccountMilestone(row.Milestone_Name,row.Account_Name,row.Min_Balance,row.Max_Balance))
    #
    #     memo_milestones__list = []
    #     for index, row in MemoMilestones_df.iterrows():
    #         memo_milestones__list.append(MemoMilestone.MemoMilestone(row.Milestone_Name,row.Memo_Regex))
    #
    #     composite_milestones__list = []
    #     for index, row in CompositeMilestones_df.iterrows():
    #         milestone_names__list = []
    #         for i in range(1,CompositeMilestones_df.shape[1]):
    #             milestone_names__list.append(row.iat[i])
    #
    #         composite_milestones__list.append(CompositeMilestone.CompositeMilestone(row.Milestone_Name,account_milestones__list, memo_milestones__list, milestone_names__list))
    #
    #     milestone_set = MilestoneSet.MilestoneSet(A,B,account_milestones__list,memo_milestones__list,composite_milestones__list)
    #     self.account_milestones__list = milestone_set.account_milestones__list
    #     self.memo_milestones__list = milestone_set.memo_milestones__list
    #     self.composite_milestones__list = milestone_set.composite_milestones__list
    #
    #     self.initial_account_set = copy.deepcopy(A)
    #     self.budget_set_list = budget_set_list
    #     self.initial_memo_rule_set = M
    #     self.start_date_YYYYMMDD = start_date_YYYYMMDD
    #     self.end_date_YYYYMMDD = end_date_YYYYMMDD
    #
    #     self.master_list_option_ids = master_list_option_ids
    #     self.output_directory = output_directory
    #
    #     self.config_df = config_df #todo store vars instead
    #
    #     budget_set_list = self.budget_set_list
    #     start_date_YYYYMMDD = self.start_date_YYYYMMDD
    #     end_date_YYYYMMDD = self.end_date_YYYYMMDD
    #     A = self.initial_account_set
    #     M = self.initial_memo_rule_set
    #
    #     # program_start = datetime.datetime.now()
    #     # scenario_index = 0
    #     number_of_returned_forecasts = len(budget_set_list)
    #     EF_pre_run = []
    #     for B in budget_set_list:
    #         try:
    #             E = ExpenseForecast.ExpenseForecast(account_set=copy.deepcopy(A),
    #                                                 budget_set=B,
    #                                                 memo_rule_set=M,
    #                                                 start_date_YYYYMMDD=start_date_YYYYMMDD,
    #                                                 end_date_YYYYMMDD=end_date_YYYYMMDD,
    #                                                 milestone_set=milestone_set)
    #             #print(E)
    #             # E.runForecast()
    #             EF_pre_run.append(E)
    #         except Exception as e:
    #
    #             print(e)
    #
    #     self.initialized_forecasts = EF_pre_run
    #
    # def read_results_from_disk(self):
    #
    #     E_objs = []
    #     forecast_ids = self.get_individual_forecast_ids()
    #     for forecast_id in forecast_ids:
    #         forecast_json_file_name_regex_pattern = 'Forecast__' + str(forecast_id) + '__[0-9]{4}_[0-9]{2}_[0-9]{2}__[0-9]{2}_[0-9]{2}_[0-9]{2}\.json'
    #         for f in os.listdir(self.output_directory):
    #             if re.search(forecast_json_file_name_regex_pattern,f) is not None:
    #                 E = ExpenseForecast.initialize_from_json_file(f)
    #                 E_objs.append(E)
    #
    #     #assert that all initial accounts sets matched, then set
    #     all_initial_account_set_hashes = [ hashlib.sha1(E.initial_account_set.getAccounts().to_string().encode("utf-8")).hexdigest() for E in E_objs ]
    #     logger.info('all_initial_account_set_hashes:')
    #     logger.info(all_initial_account_set_hashes)
    #     assert min(all_initial_account_set_hashes) == max(all_initial_account_set_hashes)
    #     assert len(all_initial_account_set_hashes) == len(E_objs)
    #     self.initial_account_set = E_objs[0].initial_account_set
    #
    #     #assert that all memo rules match, then set
    #     all_initial_memo_set_hashes = [ hash(E.initial_memo_rule_set.getMemoRules().to_string()) for E in E_objs ]
    #     assert min(all_initial_memo_set_hashes) == max(all_initial_memo_set_hashes)
    #     assert len(all_initial_memo_set_hashes) == len(E_objs)
    #     self.initial_memo_rule_set = E_objs[0].initial_memo_rule_set
    #
    #     all_start_dates = [E.start_date_YYYYMMDD for E in E_objs]
    #     assert min(all_start_dates) == max(all_start_dates)
    #     assert len(all_start_dates) == len(E_objs)
    #     self.start_date = E_objs[0].start_date_YYYYMMDD
    #
    #     all_end_dates = [E.end_date_YYYYMMDD for E in E_objs]
    #     assert min(all_end_dates) == max(all_end_dates)
    #     assert len(all_end_dates) == len(E_objs)
    #     self.end_date = E_objs[0].end_date_YYYYMMDD
    #
    #     #this is not an attribute of ExpenseForecast
    #     # all_output_directories = [ hash(E.output_directory) for E in E_objs]
    #     # assert min(all_output_directories) == max(all_output_directories)
    #     # assert len(all_output_directories) == len(E_objs)
    #     # self.output_directory = E_objs[0].output_directory
    #
    #     #we regenerate option ids because they depend on the ChooseOneSet, and not the individual forecast.
    #     #That is, Forecast #N could have the same settings, but different option ids based on what it is being compared to.
    #     #Even just moving around the rows in the input excel would change the option ids.  (this would change the unique id as well tho)
    #     number_of_combinations = 1
    #
    #     set_ids = self.choose_one_set_df.Choose_One_Set_Id.unique()
    #     set_ids.sort()
    #     for set_id in set_ids:
    #         all_options_for_set = self.choose_one_set_df.loc[self.choose_one_set_df.Choose_One_Set_Id == set_id,:]
    #         number_of_combinations = number_of_combinations * all_options_for_set.shape[0]
    #     master_list = ['']
    #     master_list_option_ids = ['']
    #     for set_id in set_ids:
    #         all_options_for_set = self.choose_one_set_df.loc[self.choose_one_set_df.Choose_One_Set_Id == set_id]
    #         current_list = []
    #         current_list_option_ids = []
    #         for option_index, option_row in all_options_for_set.iterrows():
    #             for l in master_list:
    #                 current_list.append(l + ';' + option_row.Memo_Regex_List)
    #
    #             for l in master_list_option_ids:
    #                 current_list_option_ids.append(l + str(set_id) + '=' + str(option_row.Option_Id) + ' ')
    #
    #         master_list = current_list
    #         master_list_option_ids = current_list_option_ids
    #
    #     assert len(master_list_option_ids) == len(E_objs)
    #     self.master_list_option_ids = master_list_option_ids
    #
    #     all_account_milestone_df_hashes = [ hash(E.account_milestones_df.to_string()) for E in E_objs ]
    #     assert min(all_account_milestone_df_hashes) == max(all_account_milestone_df_hashes) #error here means not all account milestones were the same
    #     assert len(all_account_milestone_df_hashes) == len(E_objs) #error here means one of the input forecasts did not have an account_milestone_df
    #     self.account_milestones_df = E_objs[0].account_milestones_df
    #
    #     all_memo_milestone_df_hashes = [ hash(E.memo_milestones_df.to_string()) for E in E_objs ]
    #     assert min(all_memo_milestone_df_hashes) == max(all_memo_milestone_df_hashes) #error here means not all memo milestones were the same
    #     assert len(all_memo_milestone_df_hashes) == len(E_objs) #error here means one of the input forecasts did not have a memo_milestone_df
    #     self.memo_milestones_df = E_objs[0].memo_milestones_df
    #
    #     all_composite_milestone_df_hashes = [ hash(E.composite_milestones_df.to_string()) for E in E_objs ]
    #     assert min(all_composite_milestone_df_hashes) == max(all_composite_milestone_df_hashes) #error here means not all the composite milestones were the same
    #     assert len(all_composite_milestone_df_hashes) == len(E_objs) #error here means one of the input forecasts did not have a composite_milestone_df
    #     self.composite_milestones_df = E_objs[0].composite_milestones_df
    #
    # def get_individual_forecast_ids(self):
    #     return [ E.unique_id for E in self.initialized_forecasts ]

    # def run_forecasts(self):
    #
    #     number_of_returned_forecasts = len(self.budget_set_list)
    #
    #     EF_pre_run = self.initialized_forecasts
    #
    #     program_start = datetime.datetime.now()
    #     scenario_index = 0
    #     for E in EF_pre_run:
    #         loop_start = datetime.datetime.now()
    #
    #         logger.info('Starting simulation scenario ' + str(scenario_index + 1) + ' / ' + str(number_of_returned_forecasts) + ' #' + E.unique_id)
    #         logger.info('Option ids: ' + self.master_list_option_ids[scenario_index])
    #         E.runForecast()
    #
    #         loop_finish = datetime.datetime.now()
    #
    #         loop_delta = loop_finish - loop_start
    #         time_since_started = loop_finish - program_start
    #
    #         average_time_per_loop = time_since_started.seconds / (scenario_index + 1)
    #         loops_remaining = number_of_returned_forecasts - (scenario_index + 1)
    #         ETC = loop_finish + datetime.timedelta(seconds=average_time_per_loop * loops_remaining)
    #         progress_string = 'Finished in ' + str(loop_delta.seconds) + ' seconds. ETC: ' + str(ETC.strftime('%Y-%m-%d %H:%M:%S'))
    #
    #         logger.info(progress_string)
    #
    #         scenario_index += 1




        # choose_one_sets__list = []
        # for i in set_ids:
        #     choose_one_sets__list.append([])

        # #Scenario_Name	Choose_One_Set_Id	Option_Name	Option_Id	Memo_Regex_List (semicolon delimited)
        # for chooseoneset_index, chooseoneset_row in ChooseOneSet_df.iterrows():
        #     pass
        #     #choose_one_sets__dict[chooseoneset_row.Choose_One_Set_Id].append(chooseoneset_row.Memo_Regex_List)

    def plotMilestoneComparison(self,E1,E2,output_path):
        assert hasattr(E1, 'forecast_df')
        assert hasattr(E2, 'forecast_df')

        AM_1 = E1.account_milestone_results
        MM_1 = E1.memo_milestone_results
        CM_1 = E1.composite_milestone_results
        AM_2 = E2.account_milestone_results
        MM_2 = E2.memo_milestone_results
        CM_2 = E2.composite_milestone_results

        data_x1 = []
        data_x2 = []
        data_y = []
        date_counter = 0

        am_keys_1 = []
        for am_key, am_value in AM_1.items():

            am_keys_1.append(am_key)
            data_x1.append(am_value)
            data_y.append(date_counter)
            date_counter += 1

        mm_keys_1 = []
        for mm_key, mm_value in MM_1.items():

            mm_keys_1.append(mm_key)
            data_x1.append(mm_value)
            data_y.append(date_counter)
            date_counter += 1

        cm_keys_1 = []
        for cm_key, cm_value in CM_1.items():

            cm_keys_1.append(cm_key)
            data_x1.append(cm_value)
            data_y.append(date_counter)
            date_counter += 1

        am_keys_2 = []
        for am_key, am_value in AM_2.items():
            # impute none as max
            if am_value is None:
                am_value = E2.end_date_YYYYMMDD
            if am_value == 'None':
                am_value = E2.end_date_YYYYMMDD
            data_x2.append(am_value)
            am_keys_2.append(am_key)

        mm_keys_2 = []
        for mm_key, mm_value in MM_2.items():
            # impute none as max
            if mm_value is None:
                mm_value = E2.end_date_YYYYMMDD
            if mm_value == 'None':
                mm_value = E2.end_date_YYYYMMDD
            data_x2.append(mm_value)
            mm_keys_2.append(mm_key)

        cm_keys_2 = []
        for cm_key, cm_value in CM_2.items():
            # impute none as max
            if cm_value is None:
                cm_value = E2.end_date_YYYYMMDD
            if cm_value == 'None':
                cm_value = E2.end_date_YYYYMMDD
            data_x2.append(cm_value)
            cm_keys_2.append(cm_key)

        figure(figsize=(14, 6), dpi=80)
        fig, ax = plt.subplots()
        fig.subplots_adjust(left=0.25)

        for i in range(0,len(data_x1)):
            x = data_x1[i]
            if x == 'None':
                data_x1[i] = None
            elif x is not None:
                data_x1[i] = datetime.datetime.strptime(x, '%Y%m%d')

        for i in range(0,len(data_x2)):
            x = data_x2[i]
            if x == 'None':
                data_x1[i] = None
            elif x is not None:
                data_x2[i] = datetime.datetime.strptime(x, '%Y%m%d')

        no_of_account_milestones = len(am_keys_1)
        am_sel_range = slice(0, (no_of_account_milestones + 1))

        no_of_memo_milestones = len(mm_keys_1)
        mm_sel_range = slice((no_of_account_milestones), (no_of_account_milestones + no_of_memo_milestones + 1))

        no_of_composite_milestones = len(cm_keys_1)
        cm_sel_range = slice((no_of_account_milestones + no_of_memo_milestones),
                             (no_of_account_milestones + no_of_memo_milestones + no_of_composite_milestones + 1))

        no_of_milestones = no_of_account_milestones + no_of_memo_milestones + no_of_composite_milestones


        if no_of_account_milestones > 0:
            #plt.scatter(data_x1[am_sel_range], data_y[am_sel_range], color="red", marker="o")
            #plt.scatter(data_x2[am_sel_range], data_y[am_sel_range], color="red", marker="*")
            for y in data_y[am_sel_range]:
                ax.barh(y+0.2,data_x1[am_sel_range],height=0.4, color="pink")
                ax.barh(y+0.6, data_x2[am_sel_range],height=0.4,color="red")

        if no_of_memo_milestones > 0:
            pass
            for y in data_y[mm_sel_range]:
                ax.barh(y+0.2,data_x1[mm_sel_range],height=0.4,color="#0abdc7")
                ax.barh(y+0.6, data_x2[mm_sel_range],height=0.4,color="#1800a3")
            #plt.scatter(data_x1[mm_sel_range], data_y[mm_sel_range], color="blue", marker="o")
            #plt.scatter(data_x2[mm_sel_range], data_y[mm_sel_range], color="blue", marker="*")

        if no_of_composite_milestones > 0:
            pass
            for y in data_y[cm_sel_range]:
                ax.barh(y+0.2,data_x1[cm_sel_range],height=0.4,color="#8021d9")
                ax.barh(y+0.6, data_x2[cm_sel_range],height=0.4,color="#5502a3")
            #plt.scatter(data_x1[cm_sel_range], data_y[cm_sel_range], color="purple", marker="o")
            #plt.scatter(data_x2[cm_sel_range], data_y[cm_sel_range], color="purple", marker="*")

        all_keys_1 = am_keys_1 + mm_keys_1 + cm_keys_1
        ax.set_yticks([ y + 0.5 for y in data_y])
        ax.set_yticklabels(all_keys_1, minor=False)
        #plt.yticks(rotation=75)


        all_keys_2 = am_keys_2 + mm_keys_2 + cm_keys_2

        # for i, txt in enumerate(all_keys_1):
        #     ax.annotate(txt, (data_x1[i], data_y[i]))
        #
        # for i, txt in enumerate(all_keys_2):
        #     ax.annotate(txt, (data_x2[i], data_y[i]))

        left_int_ts = matplotlib.dates.date2num(datetime.datetime.strptime(E1.start_date_YYYYMMDD, '%Y%m%d'))
        right_int_ts = matplotlib.dates.date2num(datetime.datetime.strptime(E1.end_date_YYYYMMDD, '%Y%m%d'))

        left = left_int_ts
        right = right_int_ts

        plt.xlim(left, right)

        plt.ylim(-0.25,no_of_milestones)

        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])

        #
        # red_patch = mpatches.Patch(color='red', label='account')
        # blue_patch = mpatches.Patch(color='blue', label='memo')
        # purple_patch = mpatches.Patch(color='purple', label='composite')
        #
        # #todo add a second legend for the shape of the point
        # # also, i dont like that labels get chopped off
        # # todo labels are highly likely to overlap on this plot so think about that
        # plt.legend(handles=[red_patch, blue_patch, purple_patch], bbox_to_anchor=(1.15, 1), loc='upper right')

        # TODO plotOverall():: a large number of accounts will require some adjustment here so that the legend is entirely visible
        date_as_datetime_type = [datetime.datetime.strptime(d, '%Y%m%d') for d in E1.forecast_df.Date]

        min_date = min(date_as_datetime_type).strftime('%Y-%m-%d')
        max_date = max(date_as_datetime_type).strftime('%Y-%m-%d')
        plt.suptitle('Forecast 1 #' + E1.unique_id + ' vs. Forecast 2 #' + E2.unique_id, horizontalalignment='center',x=0.58)
        plt.title(str(min_date) + ' -> ' + str(max_date), horizontalalignment='center')
        plt.xticks(rotation=90)
        plt.savefig(output_path)
        matplotlib.pyplot.close()

    def plotMilestoneDates(self,expense_forecast,output_path,plot_colors=['red','blue','purple']):
        assert hasattr(expense_forecast, 'forecast_df')

        assert len(plot_colors) >= 3

        AM = expense_forecast.account_milestone_results
        MM = expense_forecast.memo_milestone_results
        CM = expense_forecast.composite_milestone_results

        data_x = []
        data_y = []
        date_counter = 0

        am_keys = []
        for am_key, am_value in AM.items():
            #impute none as max
            if am_value is None:
                continue
            if am_value == 'None':
                continue
            am_keys.append(am_key)
            data_x.append(datetime.datetime.strptime(am_value,'%Y%m%d'))
            data_y.append(date_counter)
            date_counter += 1

        mm_keys = []
        for mm_key, mm_value in MM.items():
            #impute none as max
            if mm_value is None:
                continue
            if mm_value == 'None':
                continue
            mm_keys.append(mm_key)
            data_x.append(datetime.datetime.strptime(mm_value,'%Y%m%d'))
            data_y.append(date_counter)
            date_counter += 1

        cm_keys = []
        for cm_key, cm_value in CM.items():
            #impute none as max
            if cm_value is None:
                continue
            if cm_value == 'None':
                continue
            cm_keys.append(cm_key)
            data_x.append(datetime.datetime.strptime(cm_value,'%Y%m%d'))
            data_y.append(date_counter)
            date_counter += 1

        figure(figsize=(14, 6), dpi=80)

        fig, ax = plt.subplots()
        fig.subplots_adjust(left=0.25)
        if len(data_x) > 0:

            no_of_account_milestones = len(am_keys)
            am_sel_range = slice(0,(no_of_account_milestones+1))

            no_of_memo_milestones = len(mm_keys)
            mm_sel_range = slice((no_of_account_milestones),(no_of_account_milestones+no_of_memo_milestones+1))

            no_of_composite_milestones = len(cm_keys)
            cm_sel_range = slice((no_of_account_milestones+no_of_memo_milestones),(no_of_account_milestones+no_of_memo_milestones+no_of_composite_milestones+1))

            no_of_milestones = no_of_account_milestones + no_of_memo_milestones + no_of_composite_milestones

            if no_of_account_milestones > 0:
                #plt.scatter(data_x[am_sel_range], data_y[am_sel_range],color="red")
                for i in range(0,len(data_x[am_sel_range])):
                    ax.barh(data_y[am_sel_range][i],data_x[am_sel_range][i],color=plot_colors[0])

            if no_of_memo_milestones > 0:
                #plt.scatter(data_x[mm_sel_range], data_y[mm_sel_range],color="blue")
                for i in range(0, len(data_x[mm_sel_range])):
                    ax.barh(data_y[mm_sel_range][i], data_x[mm_sel_range][i], color=plot_colors[1])

            if no_of_composite_milestones > 0:
                #plt.scatter(data_x[cm_sel_range], data_y[cm_sel_range],color="purple")
                for i in range(0, len(data_x[cm_sel_range])):
                    ax.barh(data_y[cm_sel_range][i], data_x[cm_sel_range][i], color=plot_colors[2])

            all_keys = am_keys + mm_keys + cm_keys
            ax.set_yticks(data_y)
            ax.set_yticklabels(all_keys, minor=False)

            # left_int_ts = matplotlib.dates.date2num(datetime.datetime.strptime(expense_forecast.start_date_YYYYMMDD, '%Y%m%d'))
            # right_int_ts = matplotlib.dates.date2num(datetime.datetime.strptime(expense_forecast.end_date_YYYYMMDD, '%Y%m%d'))
            #
            # left = left_int_ts
            # right = right_int_ts
            #
            # plt.xlim(left, right)
            plt.xlim(datetime.datetime.strptime(expense_forecast.start_date_YYYYMMDD, '%Y%m%d'),datetime.datetime.strptime(expense_forecast.end_date_YYYYMMDD, '%Y%m%d'))

            plt.ylim(-0.5, no_of_milestones - 0.5)

            red_patch = mpatches.Patch(color='red', label='account')
            blue_patch = mpatches.Patch(color='blue', label='memo')
            purple_patch = mpatches.Patch(color='purple', label='composite')
            plt.legend(handles=[red_patch,blue_patch,purple_patch],bbox_to_anchor=(1.15, 1), loc='upper right')

            # TODO plotOverall():: a large number of accounts will require some adjustment here so that the legend is entirely visible
            date_as_datetime_type = [datetime.datetime.strptime(d, '%Y%m%d') for d in expense_forecast.forecast_df.Date]

            min_date = min(date_as_datetime_type).strftime('%Y-%m-%d')
            max_date = max(date_as_datetime_type).strftime('%Y-%m-%d')
            plt.xticks(rotation=90)
            plt.title('Forecast #' + expense_forecast.unique_id + ': ' + str(min_date) + ' -> ' + str(max_date))
        else:
            plt.axis('off')
            plt.text(0.5,0.5,s='There are no milestones to show.',horizontalalignment='center')



        plt.savefig(output_path)
        matplotlib.pyplot.close()

    def generateCompareTwoForecastsHTMLReport(self,E1, E2, output_dir='./',parent_report_path=None):

        #assert E1.start_date_YYYYMMDD == E2.start_date_YYYYMMDD
        assert E1.forecast_df.head(1).Date.iat[0] == E2.forecast_df.head(1).Date.iat[0]
        if E1.forecast_df.tail(1).Date.iat[0] != E2.forecast_df.tail(1).Date.iat[0]:

            E1_ed = datetime.datetime.strptime(E1.forecast_df.tail(1).Date.iat[0],'%Y%m%d')
            E2_ed = datetime.datetime.strptime(E2.forecast_df.tail(1).Date.iat[0], '%Y%m%d')
            earliest_end_date = min(E1_ed,E2_ed)

            E1_date_sel_vec = [ datetime.datetime.strptime(d,'%Y%m%d') <= earliest_end_date for d in E1.forecast_df.Date ]
            E2_date_sel_vec = [ datetime.datetime.strptime(d,'%Y%m%d') <= earliest_end_date for d in E2.forecast_df.Date ]
            E1.forecast_df = E1.forecast_df.iloc[ E1_date_sel_vec , : ]
            E2.forecast_df = E2.forecast_df.iloc[ E2_date_sel_vec, : ]

            E1.end_date_YYYYMMDD = earliest_end_date.strftime('%Y%m%d')
            E2.end_date_YYYYMMDD = earliest_end_date.strftime('%Y%m%d')


        # start_date = E1.start_date_YYYYMMDD.strftime('%Y-%m-%d')
        # end_date = E1.end_date_YYYYMMDD.strftime('%Y-%m-%d')

        report_1_id = E1.unique_id
        report_2_id = E2.unique_id

        report_file_name = 'compare_'+str(report_1_id)+'_'+str(report_2_id)

        report_1_start_ts__datetime = datetime.datetime.strptime(E1.start_ts, '%Y_%m_%d__%H_%M_%S')
        report_1_end_ts__datetime = datetime.datetime.strptime(E1.end_ts, '%Y_%m_%d__%H_%M_%S')
        report_2_start_ts__datetime = datetime.datetime.strptime(E2.start_ts, '%Y_%m_%d__%H_%M_%S')
        report_2_end_ts__datetime = datetime.datetime.strptime(E2.end_ts, '%Y_%m_%d__%H_%M_%S')
        report_1_simulation_time_elapsed = report_1_end_ts__datetime - report_1_start_ts__datetime
        report_2_simulation_time_elapsed = report_2_end_ts__datetime - report_2_start_ts__datetime

        if parent_report_path is not None:
            parent_report_text = """This report was generated alongside some others. See <a href=\"""" + parent_report_path + """\">this page</a> for information about related forecasts."""
        else:
            parent_report_text = ""

        # todo add a comment about whether the simulation was able to make it to the end or not.
        summary_text = """
                Forecast 1 #"""+str(E1.unique_id)+""" started at """ + str(report_1_start_ts__datetime) + """, took """ + str(report_1_simulation_time_elapsed) + """ to complete, and finished at """ + str(report_1_end_ts__datetime) + """.
                <br>
                Forecast 2 #"""+str(E2.unique_id)+""" started at """ + str(report_2_start_ts__datetime) + """, took """ + str(report_2_simulation_time_elapsed) + """ to complete, and finished at """ + str(report_2_end_ts__datetime) + """.
                """

        if E1.initial_account_set.getAccounts().to_string() == E2.initial_account_set.getAccounts().to_string():
            account_text = """
            The initial conditions and account boundaries are the same, and are:""" + E1.initial_account_set.getAccounts().to_html() + """
            """
        else:

            E1_acct_df = E1.initial_account_set.getAccounts()
            E2_acct_df = E2.initial_account_set.getAccounts()

            common_accounts_df = pd.merge(E1_acct_df,E2_acct_df,on=["Balance","Min_Balance","Max_Balance","Account_Type","Billing_Start_Dt","Interest_Type","APR","Interest_Cadence","Minimum_Payment"])

            E1_LJ_E2_df = pd.merge(E1_acct_df,E2_acct_df,on=["Balance","Min_Balance","Max_Balance","Account_Type","Billing_Start_Dt","Interest_Type","APR","Interest_Cadence","Minimum_Payment"],how="left",indicator=True)
            E2_LJ_E1_df = pd.merge(E2_acct_df, E1_acct_df,
                                   on=["Balance", "Min_Balance", "Max_Balance", "Account_Type", "Billing_Start_Dt", "Interest_Type", "APR", "Interest_Cadence", "Minimum_Payment"], how="left",
                                   indicator=True)

            accounts_forecast_1_only_df = E1_LJ_E2_df.loc[E1_LJ_E2_df._merge == 'left_only',["Balance", "Min_Balance", "Max_Balance", "Account_Type", "Billing_Start_Dt", "Interest_Type", "APR", "Interest_Cadence", "Minimum_Payment"]]
            accounts_forecast_2_only_df = E2_LJ_E1_df.loc[E2_LJ_E1_df._merge == 'left_only',["Balance", "Min_Balance", "Max_Balance", "Account_Type", "Billing_Start_Dt", "Interest_Type", "APR", "Interest_Cadence", "Minimum_Payment"]]

            account_text = """
            The initial conditions and account boundaries were different, and are:
            <h4>Shared Accounts:</h4>
            """ + common_accounts_df.to_html() + """
            <h4>Forecast 1 #"""+report_1_id+""" Only:</h4>
            """ + accounts_forecast_1_only_df.to_html() + """
            <h4>Forecast 2 #"""+report_2_id+""" Only:</h4>
            """ + accounts_forecast_2_only_df.to_html() + """
            """

        if E1.initial_budget_set.getBudgetItems().to_string() == E2.initial_budget_set.getBudgetItems().to_string():
            budget_set_text = """
            The transactions are the same, and are:""" + E1.initial_budget_set.getBudgetItems().to_html() + """
            """
        else:

            E1_budget_item_df = E1.initial_budget_set.getBudgetItems()
            E2_budget_item_df = E2.initial_budget_set.getBudgetItems()

            common_budget_items_df = pd.merge(E1_budget_item_df,E2_budget_item_df,on=["Start_Date","End_Date","Priority","Cadence","Amount","Memo","Deferrable","Partial_Payment_Allowed"])

            E1_LJ_E2_df = pd.merge(E1_budget_item_df,E2_budget_item_df,on=["Start_Date","End_Date","Priority","Cadence","Amount","Memo","Deferrable","Partial_Payment_Allowed"],indicator=True,how="left")

            E2_LJ_E1_df = pd.merge(E2_budget_item_df, E1_budget_item_df, on=["Start_Date", "End_Date", "Priority", "Cadence", "Amount", "Memo", "Deferrable", "Partial_Payment_Allowed"],
                                   indicator=True, how="left")

            budget_forecast_1_only_df = E1_LJ_E2_df.loc[E1_LJ_E2_df._merge == 'left_only',["Start_Date", "End_Date", "Priority", "Cadence", "Amount", "Memo", "Deferrable", "Partial_Payment_Allowed"]]
            budget_forecast_2_only_df = E2_LJ_E1_df.loc[E2_LJ_E1_df._merge == 'left_only',["Start_Date", "End_Date", "Priority", "Cadence", "Amount", "Memo", "Deferrable", "Partial_Payment_Allowed"]]

            budget_set_text = """
            The transactions considered for this analysis are different, and are:
            <h4>Shared Budget Items:</h4>
            """ + common_budget_items_df.to_html() + """
            <h4>Forecast 1 #"""+report_1_id+""" Only:</h4>
            """ + budget_forecast_1_only_df.to_html() + """
            <h4>Forecast 2 #"""+report_2_id+""" Only:</h4>
            """ + budget_forecast_2_only_df.to_html() + """
            """

        if E1.initial_memo_rule_set.getMemoRules().to_string() == E2.initial_memo_rule_set.getMemoRules().to_string():
            memo_rule_text = """
            These decision rules are the same and are:""" + E1.initial_memo_rule_set.getMemoRules().to_html() + """
            """
        else:

            E1_memo_rules_df = E1.initial_memo_rule_set.getMemoRules()
            E2_memo_rules_df = E2.initial_memo_rule_set.getMemoRules()

            common_memo_rules_df = pd.merge(E1_memo_rules_df, E2_memo_rules_df, on=["Memo_Regex", "Account_From", "Account_To", "Transaction_Priority"])

            E1_LJ_E2_df = pd.merge(E1_memo_rules_df, E2_memo_rules_df, on=["Memo_Regex", "Account_From", "Account_To", "Transaction_Priority"],
                                   indicator=True, how="left")

            E2_LJ_E1_df = pd.merge(E2_memo_rules_df, E1_memo_rules_df, on=["Memo_Regex", "Account_From", "Account_To", "Transaction_Priority"],
                                   indicator=True, how="left")

            memo_rule_forecast_1_only_df = E1_LJ_E2_df.loc[E1_LJ_E2_df._merge == 'left_only', ["Memo_Regex", "Account_From", "Account_To", "Transaction_Priority"]]
            memo_rule_forecast_2_only_df = E2_LJ_E1_df.loc[E2_LJ_E1_df._merge == 'left_only', ["Memo_Regex", "Account_From", "Account_To", "Transaction_Priority"]]

            memo_rule_text = """
            The decision rules used for this analysis are different, and are:
            <h4>Shared Memo Rules:</h4>
            """ + common_memo_rules_df.to_html() + """
            <h4>Forecast 1 #"""+report_1_id+""" Only:</h4>
            """ + memo_rule_forecast_1_only_df.to_html() + """
            <h4>Forecast 2 #"""+report_2_id+""" Only:</h4>
            """ + memo_rule_forecast_2_only_df.to_html() + """
            """

        assert E1.milestone_set.to_json() == E2.milestone_set.to_json()

        account_milestone_text = """
                These account milestones are defined:""" + E1.milestone_set.getAccountMilestonesDF().to_html() + """
                """

        memo_milestone_text = """
                These memo milestones are defined:""" + E1.milestone_set.getMemoMilestonesDF().to_html() + """
                """

        composite_milestone_text = """
                These composite milestones are defined:""" + E1.milestone_set.getCompositeMilestonesDF().to_html() + """
                """

        try:
            assert E1.forecast_df.shape[0] == E2.forecast_df.shape[0]
        except Exception as e:
            log_in_color(logger, 'red', 'error', 'E1.forecast_df.shape[0]:')
            log_in_color(logger, 'red', 'error', E1.forecast_df.shape[0])
            log_in_color(logger, 'red', 'error', 'E2.forecast_df.shape[0]:')
            log_in_color(logger, 'red', 'error', E2.forecast_df.shape[0])
            raise e
        num_days = E1.forecast_df.shape[0]

        report_1_initial_networth = E1.forecast_df.head(1)['Net Worth'].iat[0]
        report_1_final_networth = E1.forecast_df.tail(1)['Net Worth'].iat[0]
        report_1_networth_delta = report_1_final_networth - report_1_initial_networth
        report_1_avg_networth_change = round(report_1_networth_delta / float(E1.forecast_df.shape[0]), 2)

        if report_1_networth_delta >= 0:
            report_1_networth_rose_or_fell = "rose"
        else:
            report_1_networth_rose_or_fell = "fell"

        report_2_initial_networth = E2.forecast_df.head(1)['Net Worth'].iat[0]
        report_2_final_networth = E2.forecast_df.tail(1)['Net Worth'].iat[0]
        report_2_networth_delta = report_2_final_networth - report_2_initial_networth
        report_2_avg_networth_change = round(report_2_networth_delta / float(E1.forecast_df.shape[0]), 2)

        if report_2_networth_delta >= 0:
            report_2_networth_rose_or_fell = "rose"
        else:
            report_2_networth_rose_or_fell = "fell"

        #todo
        #Networth was higher in Forecast 1, with a final value $XX,XXX greater than the alternative.
        #The difference in average values for these trends is $XX.XX.

        networth_text = """
            For forecast 1 #"""+report_1_id+""", Net Worth began at """ + str(f"${float(report_1_initial_networth):,}") + """ and """ + report_1_networth_rose_or_fell + """ to """ + str(f"${float(report_1_final_networth):,}") + """ over """ + str(
        f"{float(num_days):,.0f}") + """ days, averaging """ + f"${float(report_1_avg_networth_change):,}" + """ per day.
        <br>
        For forecast 2 #"""+report_2_id+""", Net Worth began at """ + str(f"${float(report_2_initial_networth):,}") + """ and """ + report_2_networth_rose_or_fell + """ to """ + str(f"${float(report_2_final_networth):,}") + """ over """ + str(
        f"{float(num_days):,.0f}") + """ days, averaging """ + f"${float(report_2_avg_networth_change):,}" + """ per day.
        <br><br>
        """
        forecast_networth_delta = round(report_2_final_networth - report_1_final_networth,2)
        if report_1_final_networth >= report_2_final_networth:
            networth_text += """Forecast 1 #"""+report_1_id+""" ended with a Net Worth """+str(f"${float(forecast_networth_delta):,}")+""" greater than the alternative.  """
        else:
            networth_text += """Forecast 2 #"""+report_2_id+""" ended with a Net Worth """+str(f"${float(forecast_networth_delta):,}")+""" greater than the alternative.  """


        netgainloss_text = ""


        report_1_initial_loan_total = round(E1.forecast_df.head(1)['Loan Total'].iat[0], 2)
        report_1_final_loan_total = round(E1.forecast_df.tail(1)['Loan Total'].iat[0], 2)
        report_1_loan_delta = round(report_1_final_loan_total - report_1_initial_loan_total, 2)
        report_1_initial_cc_debt_total = round(E1.forecast_df.head(1)['CC Debt Total'].iat[0], 2)
        report_1_final_cc_debt_total = round(E1.forecast_df.tail(1)['CC Debt Total'].iat[0], 2)
        report_1_cc_debt_delta = round(report_1_final_cc_debt_total - report_1_initial_cc_debt_total, 2)
        report_1_initial_liquid_total = round(E1.forecast_df.head(1)['Liquid Total'].iat[0], 2)
        report_1_final_liquid_total = round(E1.forecast_df.tail(1)['Liquid Total'].iat[0], 2)
        report_1_liquid_delta = round(report_1_final_liquid_total - report_1_initial_liquid_total, 2)

        report_1_avg_loan_delta = round(report_1_loan_delta / num_days, 2)
        report_1_avg_cc_debt_delta = round(report_1_cc_debt_delta / num_days, 2)
        report_1_avg_liquid_delta = round(report_1_liquid_delta / num_days, 2)

        if report_1_avg_loan_delta >= 0:
            report_1_loan_rose_or_fell = "rose"
        else:
            report_1_loan_rose_or_fell = "fell"

        if report_1_avg_cc_debt_delta >= 0:
            report_1_cc_debt_rose_or_fell = "rose"
        else:
            report_1_cc_debt_rose_or_fell = "fell"

        if report_1_avg_liquid_delta >= 0:
            report_1_liquid_rose_or_fell = "rose"
        else:
            report_1_liquid_rose_or_fell = "fell"

        report_2_initial_loan_total = round(E2.forecast_df.head(1)['Loan Total'].iat[0], 2)
        report_2_final_loan_total = round(E2.forecast_df.tail(1)['Loan Total'].iat[0], 2)
        report_2_loan_delta = round(report_2_final_loan_total - report_2_initial_loan_total, 2)
        report_2_initial_cc_debt_total = round(E2.forecast_df.head(1)['CC Debt Total'].iat[0], 2)
        report_2_final_cc_debt_total = round(E2.forecast_df.tail(1)['CC Debt Total'].iat[0], 2)
        report_2_cc_debt_delta = round(report_2_final_cc_debt_total - report_2_initial_cc_debt_total, 2)
        report_2_initial_liquid_total = round(E2.forecast_df.head(1)['Liquid Total'].iat[0], 2)
        report_2_final_liquid_total = round(E2.forecast_df.tail(1)['Liquid Total'].iat[0], 2)
        report_2_liquid_delta = round(report_2_final_liquid_total - report_2_initial_liquid_total, 2)

        report_2_avg_loan_delta = round(report_2_loan_delta / num_days, 2)
        report_2_avg_cc_debt_delta = round(report_2_cc_debt_delta / num_days, 2)
        report_2_avg_liquid_delta = round(report_2_liquid_delta / num_days, 2)

        if report_2_avg_loan_delta >= 0:
            report_2_loan_rose_or_fell = "rose"
        else:
            report_2_loan_rose_or_fell = "fell"

        if report_2_avg_cc_debt_delta >= 0:
            report_2_cc_debt_rose_or_fell = "rose"
        else:
            report_2_cc_debt_rose_or_fell = "fell"

        if report_2_avg_liquid_delta >= 0:
            report_2_liquid_rose_or_fell = "rose"
        else:
            report_2_liquid_rose_or_fell = "fell"

        #todo
        # Less was owed in loans in Forecast 1, with a final value $XX,XXX less than the alternative.
        # The difference in average values for these trends is $XX.XX.

        # Less was owed on credit cards in Forecast 1, with a final value $XX,XXX less than the alternative.
        # The difference in average values for these trends is $XX.XX.

        # Liquid total was higher in Forecast 1, with a final value $XX,XXX greater than the alternative.
        # The difference in average values for these trends is $XX.XX.


        loan_debt_delta = round(report_2_final_loan_total - report_1_final_loan_total,2)
        cc_debt_delta = round(report_2_final_cc_debt_total - report_1_final_cc_debt_total,2)
        liquid_delta = round(report_2_final_liquid_total - report_1_final_liquid_total,2)

        if loan_debt_delta >= 0:
            loan_debt_delta_string = """Forecast 2 #"""+report_2_id+""" ended with loan debt """ + str(f"${float(abs(loan_debt_delta)):,}"+""" higher than the alternative.""")
        else:
            loan_debt_delta_string = """Forecast 1 #"""+report_1_id+""" ended with loan debt """ + str(f"${float(abs(loan_debt_delta)):,}"+""" higher than the alternative.""")

        if cc_debt_delta >= 0:
            cc_debt_delta_string = """Forecast 2 #"""+report_2_id+""" ended with credit card debt """ + str(f"${float(abs(cc_debt_delta)):,}"+""" higher than the alternative.""")
        else:
            cc_debt_delta_string = """Forecast 1 #"""+report_1_id+""" ended with credit card debt """ + str(f"${float(abs(cc_debt_delta)):,}"+""" higher than the alternative.""")

        if liquid_delta >= 0:
            liquid_debt_delta_string = """Forecast 2 #"""+report_2_id+""" ended with loan debt """ + str(f"${float(abs(liquid_delta)):,}"+""" higher than the alternative.""")
        else:
            liquid_debt_delta_string = """Forecast 1 #"""+report_1_id+""" ended with loan debt """ + str(f"${float(abs(liquid_delta)):,}"+""" higher than the alternative.""")

        account_type_text = """
                For Forecast 1 #"""+report_1_id+""", Loan debt began at """ + str(f"${float(report_1_initial_loan_total):,}") + """ and """ + report_1_loan_rose_or_fell + """ to """ + str(f"${float(report_1_final_loan_total):,}") + """ over """ + str(
            f"{float(num_days):,.0f}") + """ days, averaging """ + f"${float(report_1_avg_loan_delta):,}" + """ per day.
                <br>
                For forecast 2 #"""+report_2_id+""", Loan debt began at """ + str(f"${float(report_2_initial_loan_total):,}") + """ and """ + report_2_loan_rose_or_fell + """ to """ + str(f"${float(report_2_final_loan_total):,}") + """ over """ + str(
            f"{float(num_days):,.0f}") + """ days, averaging """ + f"${float(report_2_avg_loan_delta):,}" + """ per day.
                <br><br>
                """ + loan_debt_delta_string + """
                <br><br><br>
                For forecast 1 #"""+report_1_id+""", Credit card debt began at """ + str(f"${float(report_1_initial_cc_debt_total):,}") + """ and """ + report_1_cc_debt_rose_or_fell + """ to """ + str(
            f"${float(report_1_final_cc_debt_total):,}") + """ over """ + str(f"{float(num_days):,.0f}") + """ days, averaging """ + f"${float(report_1_avg_cc_debt_delta):,}" + """ per day.
                <br>
                For forecast 2 #"""+report_2_id+""", Credit card debt began at """ + str(f"${float(report_2_initial_cc_debt_total):,}") + """ and """ + report_2_cc_debt_rose_or_fell + """ to """ + str(
            f"${float(report_2_final_cc_debt_total):,}") + """ over """ + str(f"{float(num_days):,.0f}") + """ days, averaging """ + f"${float(report_2_avg_cc_debt_delta):,}" + """ per day.
                <br><br>
                """ + cc_debt_delta_string + """
                <br><br><br>
                For forecast 1 #"""+report_1_id+""", Liquid cash began at """ + str(f"${float(report_1_initial_liquid_total):,}") + """ and """ + report_1_liquid_rose_or_fell + """ to """ + str(f"${float(report_1_final_liquid_total):,}") + """ over """ + str(
            f"{float(num_days):,.0f}") + """ days, averaging """ + f"${float(report_1_avg_liquid_delta):,}" + """ per day.
                <br>
                For forecast 2 #"""+report_2_id+""", Liquid cash began at """ + str(f"${float(report_2_initial_liquid_total):,}") + """ and """ + report_2_liquid_rose_or_fell + """ to """ + str(f"${float(report_2_final_liquid_total):,}") + """ over """ + str(
            f"{float(num_days):,.0f}") + """ days, averaging """ + f"${float(report_2_avg_liquid_delta):,}" + """ per day.
                <br><br>
                """ + liquid_debt_delta_string + """
                """

        E1_account_info = E1.initial_account_set.getAccounts()
        E2_account_info = E2.initial_account_set.getAccounts()
        E1_account_base_names = set([a.split(':')[0] for a in E1_account_info.Name])
        E2_account_base_names = set([a.split(':')[0] for a in E2_account_info.Name])

        assert E1_account_base_names == E2_account_base_names
        E1_aggregated_df = copy.deepcopy(E1.forecast_df.loc[:, ['Date']])
        E2_aggregated_df = copy.deepcopy(E2.forecast_df.loc[:, ['Date']])

        for account_base_name in E1_account_base_names:
            E1_col_sel_vec = [account_base_name == a.split(':')[0] for a in E1.forecast_df.columns]
            E1_col_sel_vec[0] = True  # Date
            E1_relevant_df = E1.forecast_df.loc[:, E1_col_sel_vec]

            if E1_relevant_df.shape[1] == 2:  # checking and savings case
                E1_aggregated_df[account_base_name] = E1_relevant_df.iloc[:, 1]
            elif E1_relevant_df.shape[1] == 3:  # credit and loan
                E1_aggregated_df[account_base_name] = E1_relevant_df.iloc[:, 1] + E1_relevant_df.iloc[:, 2]

        for account_base_name in E2_account_base_names:
            E2_col_sel_vec = [account_base_name == a.split(':')[0] for a in E2.forecast_df.columns]
            E2_col_sel_vec[0] = True  # Date
            E2_relevant_df = E2.forecast_df.loc[:, E2_col_sel_vec]

            if E2_relevant_df.shape[1] == 2:  # checking and savings case
                E2_aggregated_df[account_base_name] = E2_relevant_df.iloc[:, 1]
            elif E2_relevant_df.shape[1] == 3:  # credit and loan
                E2_aggregated_df[account_base_name] = E2_relevant_df.iloc[:, 1] + E2_relevant_df.iloc[:, 2]

        #relevant_df = pd.merge(E1_aggregated_df, E2_aggregated_df, on=["Date"], suffixes=('_1', '_2'))

        interest_text = ""

        milestone_text = ""

        transaction_schedule_text = ""

        all_text=""
        E1_account_base_names = list(E1_account_base_names)
        E1_account_base_names.sort()
        for aname in E1_account_base_names:

            E1_initial_value = round(E1_aggregated_df.head(1)[aname].iat[0], 2)
            E1_final_value = round(E1_aggregated_df.tail(1)[aname].iat[0], 2)
            E1_delta = round(E1_final_value - E1_initial_value, 2)
            E1_daily_average = round(E1_delta/num_days,2)

            if E1_daily_average >= 0:
                E1_rose_or_fell="rose"
            else:
                E1_rose_or_fell = "fell"

            E2_initial_value = round(E2_aggregated_df.head(1)[aname].iat[0], 2)
            E2_final_value = round(E2_aggregated_df.tail(1)[aname].iat[0], 2)
            E2_delta = round(E2_final_value - E2_initial_value, 2)
            E2_daily_average = round(E2_delta / num_days, 2)

            if E2_daily_average >= 0:
                E2_rose_or_fell = "rose"
            else:
                E2_rose_or_fell = "fell"

            all_single_delta = round(E2_final_value - E1_final_value,2)
            if all_single_delta >= 0:
                delta_string = """Forecast 2 #""" + report_2_id + ", " +  aname + """ ended """ + str(f"${float(abs(all_single_delta)):,}" + """ higher than the alternative.""")
            else:
                delta_string = """Forecast 1 #""" + report_1_id + ", " + aname + """ ended """ + str(f"${float(abs(all_single_delta)):,}" + """ higher than the alternative.""")

            #str(f"${float(report_2_initial_liquid_total):,}")

            #todo dollar signs and comma formatting m
            line=""" For Forecast 1 #"""+str(E1.unique_id)+""", """+aname+""" began at """+str(f"${float(E1_initial_value):,}")+""" and  """+E1_rose_or_fell+""" to """+str(f"${float(E1_final_value):,}")+""" over  """+str(num_days)+""", averaging  """+str(f"${float(E1_daily_average):,}")+"""  per day. <br>
            For Forecast 2 #"""+str(E2.unique_id)+""", """+aname+""" began at """+str(f"${float(E2_initial_value):,}")+""" and  """+E2_rose_or_fell+""" to """+str(f"${float(E2_final_value):,}")+""" over  """+str(num_days)+""", averaging  """+str(f"${float(E2_daily_average):,}")+"""  per day. <br><br>   
            """ + delta_string + """ <br><br><br>
            """
            all_text+=line


        report_1_networth_line_plot_path = report_1_id + '_networth_line_plot.png'
        report_1_netgain_loss_plot_path = report_1_id + '_net_gain_loss_line_plot.png'
        report_1_accounttype_line_plot_path = report_1_id + '_accounttype_line_plot_plot.png'
        report_1_marginal_interest_plot_path = report_1_id + '_marginal_interest_line_plot.png'
        report_1_milestone_plot_path = report_1_id + '_milestone_bar_plot.png'
        report_1_all_line_plot_path = report_1_id + '_all_line_plot.png'


        report_2_networth_line_plot_path = report_2_id + '_networth_line_plot.png'
        report_2_netgain_loss_plot_path = report_2_id + '_net_gain_loss_line_plot.png'
        report_2_accounttype_line_plot_path = report_2_id + '_accounttype_line_plot_plot.png'
        report_2_marginal_interest_plot_path = report_2_id + '_marginal_interest_line_plot.png'
        report_2_milestone_plot_path = report_2_id + '_milestone_bar_plot.png'
        report_2_all_line_plot_path = report_2_id + '_all_line_plot.png'


        networth_comparison_plot_path = report_1_id + '_vs_' + report_2_id + '_networth_comparison_plot.png'
        netgain_loss_comparison_plot_path = report_1_id + '_vs_' + report_2_id + '_net_gain_loss_comparison_plot.png'
        account_type_comparison_plot_path = report_1_id + '_vs_' + report_2_id + '_account_type_comparison_plot.png'
        marginal_interest_comparison_plot_path = report_1_id + '_vs_' + report_2_id + '_marginal_interest_comparison_plot.png'
        milestone_comparison_plot_path = report_1_id + '_vs_' + report_2_id + '_milestone_comparison_plot.png'
        all_comparison_plot_path = report_1_id + '_vs_' + report_2_id + '_all_comparison_plot.png'

        self.plotNetWorth(E1, output_dir + report_1_networth_line_plot_path, line_color_cycle_list=['blue'],linestyle='solid')
        self.plotNetGainLoss(E1, output_dir + report_1_netgain_loss_plot_path, line_color_cycle_list=['green', 'red'],linestyle='solid')
        self.plotAccountTypeTotals(E1,output_dir + report_1_accounttype_line_plot_path)
        self.plotMarginalInterest(E1,output_dir + report_1_marginal_interest_plot_path,linestyle='solid')
        self.plotMilestoneDates(E1,output_dir + report_1_milestone_plot_path)
        self.plotAll(E1, output_dir + report_1_all_line_plot_path)

        self.plotNetWorth(E2, output_dir + report_2_networth_line_plot_path,line_color_cycle_list=['blue'],linestyle='dashed')
        self.plotNetGainLoss(E2, output_dir + report_2_netgain_loss_plot_path, line_color_cycle_list=['green', 'red'],linestyle='dashed')
        self.plotAccountTypeTotals(E2, output_dir + report_2_accounttype_line_plot_path,linestyle='dashed')
        self.plotMarginalInterest(E2,output_dir + report_2_marginal_interest_plot_path,linestyle='dashed')
        self.plotMilestoneDates(E2, output_dir + report_2_milestone_plot_path,plot_colors=["pink","#0abdc7","#8021d9"])
        self.plotAll(E2, output_dir + report_2_all_line_plot_path)

        self.plotNetWorthComparison(E1, E2, output_dir + networth_comparison_plot_path, line_color_cycle_list=['blue'])
        self.plotNetGainLossComparison(E1, E2, output_dir + netgain_loss_comparison_plot_path)
        self.plotAccountTypeComparison(E1,E2, output_dir + account_type_comparison_plot_path)
        self.plotMarginalInterestComparison(E1, E2, output_dir + marginal_interest_comparison_plot_path)
        self.plotMilestoneComparison(E1, E2, output_dir + milestone_comparison_plot_path)
        self.plotAllComparison(E1, E2, output_dir + all_comparison_plot_path)

        html_body = """
                <!DOCTYPE html>
                <html>
                <head>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <title>Expense Forecast Report #""" + str(report_1_id) + """ vs. #"""+str(report_2_id)+"""</title>
                <style>
                /* Style the tab */
                .tab {
                  overflow: hidden;
                  border: 1px solid #ccc;
                  background-color: #f1f1f1;
                }

                /* Style the buttons that are used to open the tab content */
                .tab button {
                  background-color: inherit;
                  float: left;
                  border: none;
                  outline: none;
                  cursor: pointer;
                  padding: 14px 16px;
                  transition: 0.3s;
                }

                /* Change background color of buttons on hover */
                .tab button:hover {
                  background-color: #ddd;
                }

                /* Create an active/current tablink class */
                .tab button.active {
                  background-color: #ccc;
                }

                /* Style the tab content */
                .tabcontent {
                  display: none;
                  padding: 6px 12px;
                  border: 1px solid #ccc;
                  border-top: none;
                }
                </style>


                </head>
                <body>
                <h1>Expense Forecast Report #""" + str(report_1_id) + """ vs. #"""+str(report_2_id)+"""</h1>
                <p>""" + datetime.datetime.strptime(E1.start_date_YYYYMMDD,'%Y%m%d').strftime('%Y-%m-%d') + """ to """ + datetime.datetime.strptime(E1.end_date_YYYYMMDD,'%Y%m%d').strftime('%Y-%m-%d') + " " + parent_report_text + """</p>

                <!-- Tab links -->
                <div class="tab">
                  <button class="tablinks active" onclick="openTab(event, 'ForecastParameters')">Forecast Parameters</button>
                  <button class="tablinks" onclick="openTab(event, 'NetWorth')">Net Worth</button>
                  <button class="tablinks" onclick="openTab(event, 'NetGainLoss')">Net Gain & Loss</button>
                  <button class="tablinks" onclick="openTab(event, 'AccountType')">Account Type</button>
                  <button class="tablinks" onclick="openTab(event, 'Interest')">Interest</button>
                  <button class="tablinks" onclick="openTab(event, 'Milestone')">Milestone</button>
                  <button class="tablinks" onclick="openTab(event, 'All')">All</button>
                  <button class="tablinks" onclick="openTab(event, 'TransactionSchedule')">Transaction Schedule</button>
                  <button class="tablinks" onclick="openTab(event, 'ForecastResults')">Forecast Results</button>
                </div>

                <!-- Tab content -->
                <div id="ForecastParameters" class="tabcontent">
                  <h3>Forecast Parameters</h3>
                  """ + summary_text + """
                  <h3>Accounts</h3>
                  <p>""" + account_text + """</p>
                  <h3>Budget Items</h3>
                  <p>""" + budget_set_text + """</p>
                  <h3>Memo Rules</h3>
                  <p>""" + memo_rule_text + """</p>
                  <h3>Account Milestones</h3>
                  <p>"""+account_milestone_text+"""</p>
                  <h3>Memo Milestones</h3>
                  <p>"""+memo_milestone_text+"""</p>
                  <h3>Composite Milestones</h3>
                  <p>"""+composite_milestone_text+"""</p>
                </div>

                <div id="NetWorth" class="tabcontent">
                  <h3>NetWorth</h3>
                  <p>""" + networth_text + """</p>
                  <img src=\"""" + networth_comparison_plot_path + """\">
                  <img src=\"""" + report_1_networth_line_plot_path + """\">
                  <img src=\"""" + report_2_networth_line_plot_path + """\">
                </div>

                <div id="NetGainLoss" class="tabcontent">
                  <h3>Net Gain & Loss</h3>
                  <p>"""+netgainloss_text+"""</p>
                   
                  <img src=\"""" + netgain_loss_comparison_plot_path + """\">
                  <img src=\"""" + report_1_netgain_loss_plot_path + """\">
                  <img src=\"""" + report_2_netgain_loss_plot_path + """\">
                </div>

                <div id="AccountType" class="tabcontent">
                  <h3>Account Type</h3>
                  <p>""" + account_type_text + """</p>
                  <img src=\"""" + account_type_comparison_plot_path + """\">
                  <img src=\"""" + report_1_accounttype_line_plot_path + """\">
                  <img src=\"""" + report_2_accounttype_line_plot_path + """\">
                </div>

                <div id="Interest" class="tabcontent">
                  <h3>Interest</h3>
                  <p>"""+interest_text+"""</p>
                  
                  <img src=\"""" + marginal_interest_comparison_plot_path + """\">
                  <img src=\"""" + report_1_marginal_interest_plot_path + """\">
                  <img src=\"""" + report_2_marginal_interest_plot_path + """\">
                  
                </div>

                <div id="Milestone" class="tabcontent">
                  <h3>Milestone</h3>
                  <p>"""+milestone_text+"""</p>
                  <img src=\"""" + milestone_comparison_plot_path + """\">
                  <br>
                  <img src=\"""" + report_1_milestone_plot_path + """\">
                  <br>
                  <img src=\"""" + report_2_milestone_plot_path + """\">
                  <h4>Account Milestones</h4>
                  """ + E1.getAccountMilestoneResultsDF().to_html() + """ <br>
                  """ + E2.getAccountMilestoneResultsDF().to_html() + """ <br>
                  <h4>Memo Milestones</h4>
                  """ + E1.getMemoMilestoneResultsDF().to_html() + """ <br>
                  """ + E2.getMemoMilestoneResultsDF().to_html() + """ <br>
                  <h4>Composite Milestones</h4>
                  """ + E1.getCompositeMilestoneResultsDF().to_html() + """ <br>
                  """ + E2.getCompositeMilestoneResultsDF().to_html() + """ <br>
                </div>

                <div id="All" class="tabcontent">
                  <h3>All</h3>
                  <p>"""+all_text+"""</p>
                  <img src=\"""" + all_comparison_plot_path + """\">
                  <img src=\"""" + report_1_all_line_plot_path + """\">
                  <img src=\"""" + report_2_all_line_plot_path + """\">
                </div>
                
                <div id="TransactionSchedule" class="tabcontent">
                  <h3>Transaction Schedule</h3>
                  """ + transaction_schedule_text + """
                </div>

                <div id="ForecastResults" class="tabcontent">
                  <h3>Forecast Results</h3>
                  <p>""" + summary_text + """</p>
                  <p>The visualized data are below:</p>
                  <h4>Forecast 1 #"""+str(E1.unique_id)+""":</h4>
                  """ + E1.forecast_df.to_html() + """
                  <h4>Forecast 2 #"""+str(E2.unique_id)+""":</h4>
                  """ + E2.forecast_df.to_html() + """
                </div>

                

                <script>
                function openTab(evt, tabName) {
                  // Declare all variables
                  var i, tabcontent, tablinks;

                  // Get all elements with class="tabcontent" and hide them
                  tabcontent = document.getElementsByClassName("tabcontent");
                  for (i = 0; i < tabcontent.length; i++) {
                    tabcontent[i].style.display = "none";
                  }

                  // Get all elements with class="tablinks" and remove the class "active"
                  tablinks = document.getElementsByClassName("tablinks");
                  for (i = 0; i < tablinks.length; i++) {
                    tablinks[i].className = tablinks[i].className.replace(" active", "");
                  }

                  // Show the current tab, and add an "active" class to the button that opened the tab
                  document.getElementById(tabName).style.display = "block";
                  evt.currentTarget.className += " active";
                }

                //having this here leaves the Summary tab open when the page first loads
                document.getElementById("ForecastParameters").style.display = "block";
                </script>

                </body>
                </html>
                """

        log_in_color(logger, 'green', 'info','Writing forecast comparison report to ' + output_dir + report_file_name + '.html')
        with open(output_dir+report_file_name+'.html', 'w') as f:
            f.write(html_body)

    def generateHTMLReport(self,E,output_dir='./',parent_report_path=None):

        start_date = datetime.datetime.strptime(E.start_date_YYYYMMDD,'%Y%m%d').strftime('%Y-%m-%d')
        end_date = datetime.datetime.strptime(E.end_date_YYYYMMDD,'%Y%m%d').strftime('%Y-%m-%d')

        forecast_failed = (E.forecast_df.tail(1).Date.iat[0] != E.end_date_YYYYMMDD)

        report_id = E.unique_id

        output_file_name = 'Forecast_'+str(report_id)

        start_ts__datetime = datetime.datetime.strptime(E.start_ts,'%Y_%m_%d__%H_%M_%S')
        end_ts__datetime = datetime.datetime.strptime(E.end_ts, '%Y_%m_%d__%H_%M_%S')
        simulation_time_elapsed = end_ts__datetime - start_ts__datetime

        if parent_report_path is not None:
            parent_report_text = """This report was generated alongside some others. See <a href=\"""" + parent_report_path + """\">this page</a> for information about related forecasts."""
        else:
            parent_report_text = ""

        #todo add a comment about whether the simulation was able to make it to the end or not.
        summary_text =  """
        This forecast started at """+str(start_ts__datetime)+""", took """ + str(simulation_time_elapsed) + """ to complete, and finished at """ + str(end_ts__datetime) + """.
        """

        account_text = """
        The initial conditions and account boundaries are defined as:"""+E.initial_account_set.getAccounts().to_html()+"""
        """

        budget_set_text = """
        These transactions are considered for analysis:"""+E.initial_budget_set.getBudgetItems().to_html()+"""
        """

        memo_rule_text = """
        These decision rules are used:"""+E.initial_memo_rule_set.getMemoRules().to_html()+"""
        """

        account_milestone_text = """
        These account milestones are defined:"""+E.milestone_set.getAccountMilestonesDF().to_html()+"""
        """

        memo_milestone_text = """
        These memo milestones are defined:"""+E.milestone_set.getMemoMilestonesDF().to_html()+"""
        """

        composite_milestone_text = """
        These composite milestones are defined:"""+E.milestone_set.getCompositeMilestonesDF().to_html()+"""
        """

        initial_networth=round(E.forecast_df.head(1)['Net Worth'].iat[0],2)
        final_networth=round(E.forecast_df.tail(1)['Net Worth'].iat[0],2)
        networth_delta=round(final_networth-initial_networth,2)
        num_days = E.forecast_df.shape[0]
        avg_networth_change=round(networth_delta/float(E.forecast_df.shape[0]),2)

        if networth_delta >= 0:
            rose_or_fell="rose"
        else:
            rose_or_fell="fell"

        networth_text = """
        Net Worth began at """+str(f"${float(initial_networth):,}")+""" and """+rose_or_fell+""" to """+str(f"${float(final_networth):,}")+""" over """+str(f"{float(num_days):,.0f}")+""" days, averaging """+f"${float(avg_networth_change):,}"+""" per day.
        """

        initial_loan_total = round(E.forecast_df.head(1)['Loan Total'].iat[0],2)
        final_loan_total = round(E.forecast_df.tail(1)['Loan Total'].iat[0],2)
        loan_delta = round(final_loan_total - initial_loan_total,2)
        initial_cc_debt_total = round(E.forecast_df.head(1)['CC Debt Total'].iat[0],2)
        final_cc_debt_total = round(E.forecast_df.tail(1)['CC Debt Total'].iat[0],2)
        cc_debt_delta = round(final_cc_debt_total - initial_cc_debt_total,2)
        initial_liquid_total = round(E.forecast_df.head(1)['Liquid Total'].iat[0],2)
        final_liquid_total = round(E.forecast_df.tail(1)['Liquid Total'].iat[0],2)
        liquid_delta = round(final_liquid_total - initial_liquid_total,2)

        avg_loan_delta = round(loan_delta / num_days,2)
        avg_cc_debt_delta = round(cc_debt_delta / num_days,2)
        avg_liquid_delta = round(liquid_delta / num_days,2)

        if avg_loan_delta >= 0:
            loan_rose_or_fell="rose"
        else:
            loan_rose_or_fell = "fell"

        if avg_cc_debt_delta >= 0:
            cc_debt_rose_or_fell="rose"
        else:
            cc_debt_rose_or_fell = "fell"

        if avg_liquid_delta >= 0:
            liquid_rose_or_fell="rose"
        else:
            liquid_rose_or_fell = "fell"

        account_type_text = """
        Loan debt began at """+str(f"${float(initial_loan_total):,}")+""" and """+loan_rose_or_fell+""" to """+str(f"${float(final_loan_total):,}")+""" over """+str(f"{float(num_days):,.0f}")+""" days, averaging """+f"${float(avg_loan_delta):,}"+""" per day.
        <br><br>
        Credit card debt began at """+str(f"${float(initial_cc_debt_total):,}")+""" and """+cc_debt_rose_or_fell+""" to """+str(f"${float(final_cc_debt_total):,}")+""" over """+str(f"{float(num_days):,.0f}")+""" days, averaging """+f"${float(avg_cc_debt_delta):,}"+""" per day.
        <br><br>
        Liquid cash began at """+str(f"${float(initial_liquid_total):,}")+""" and """+liquid_rose_or_fell+""" to """+str(f"${float(final_liquid_total):,}")+""" over """+str(f"{float(num_days):,.0f}")+""" days, averaging """+f"${float(avg_liquid_delta):,}"+""" per day.
        """

        total_gain = round(sum(E.forecast_df['Net Gain']),2)
        avg_daily_gain = round(total_gain / E.forecast_df.shape[0],2)

        total_loss = round(sum(E.forecast_df['Net Loss']), 2)
        avg_daily_loss = round(total_loss / E.forecast_df.shape[0], 2)

        net_gain_loss_text = "Total gain was "+str(f"${float(total_gain):,}")+" over "+str(E.forecast_df.shape[0])+" days, averaging "+str(f"${float(avg_daily_gain):,}")+" per day.<br><br>"
        net_gain_loss_text += "Total loss was "+str(f"-${float(total_loss):,}")+" over "+str(E.forecast_df.shape[0])+" days, averaging "+str(f"-${float(avg_daily_loss):,}")+" per day."

        total_interest_accrued = round(sum(E.forecast_df['Marginal Interest']), 2)
        avg_interest_accrued = round(total_interest_accrued / E.forecast_df.shape[0], 2)

        interest_text = "Total interest accrued was "+str(f"${float(total_interest_accrued):,}")+" over "+str(E.forecast_df.shape[0])+" days, averaging "+str(f"${float(avg_interest_accrued):,}")+" per day.<br>"
        interest_text += "This plot shows the new interest by day, not the total interest at a given time."


        cc_interest_sel_vec = [ 'cc interest' in m for m in E.forecast_df.Memo ]
        interest_rows_df = E.forecast_df.loc[cc_interest_sel_vec]
        interest_table_to_display_df = pd.DataFrame(interest_rows_df['Date'])
        interest_table_to_display_df['Total CC Interest'] = 0
        for index, row in interest_rows_df.iterrows():
            memo_line = row.Memo
            memo_line_items = memo_line.split(';')
            for memo_line_item in memo_line_items:
                memo_line_item = memo_line_item.strip()
                if 'cc interest' not in memo_line_item:
                    continue

                value_match = re.search('\(([A-Za-z0-9_ :]*) ([-+]?\$.*)\)$', memo_line_item)
                line_item_value_string = value_match.group(2)
                line_item_value_string = line_item_value_string.replace('(', '').replace(')', '').replace('$', '')
                line_item_value = float(line_item_value_string)

                interest_table_to_display_df.loc[index,'Total CC Interest'] += line_item_value
        interest_table_html = interest_table_to_display_df.to_html()


        am_result_df = E.getAccountMilestoneResultsDF()
        mm_result_df = E.getMemoMilestoneResultsDF()
        cm_result_df = E.getCompositeMilestoneResultsDF()

        achieved_am_count = am_result_df[am_result_df.Date < datetime.datetime.strptime(E.end_date_YYYYMMDD,'%Y%m%d')].shape[0]
        achieved_mm_count = mm_result_df[mm_result_df.Date < datetime.datetime.strptime(E.end_date_YYYYMMDD,'%Y%m%d')].shape[0]
        achieved_cm_count = cm_result_df[cm_result_df.Date < datetime.datetime.strptime(E.end_date_YYYYMMDD,'%Y%m%d')].shape[0]
        total_milestone_count = am_result_df.shape[0] + mm_result_df.shape[0] + cm_result_df.shape[0]
        achieved_milestone_count = achieved_am_count + achieved_mm_count + achieved_cm_count

        milestone_text = str(total_milestone_count)+" milestones were defined, and "+str(achieved_milestone_count)+" were achieved before the end of the forecast.<br>"
        milestone_text += "Note that unachieved milestones are displayed on the last day of the forecast."

        transaction_schedule_text = "Transactions are displayed below."

        p2_plus_txns_html_table = E.confirmed_df[ E.confirmed_df.Priority >= 2 ].to_html()

        cc_payments_df = pd.DataFrame({'Date':[],'Memo':[]})
        loan_payments_df = pd.DataFrame({'Date': [], 'Memo': []})
        for index, row in E.forecast_df.iterrows():
            memo_line_items = row.Memo.split(';')
            for memo_line_item in memo_line_items:
                if 'loan min payment' in memo_line_item or 'additional loan payment' in memo_line_item:
                    loan_payments_df = pd.concat([loan_payments_df,pd.DataFrame({'Date':[row.Date],'Memo':[memo_line_item]})])
                elif 'cc min payment' in memo_line_item or 'additional cc payment' in memo_line_item:
                    cc_payments_df = pd.concat([cc_payments_df,pd.DataFrame({'Date':[row.Date],'Memo':[memo_line_item]})])

        cc_payments_html_table = cc_payments_df.to_html()
        loan_payment_html_table = loan_payments_df.to_html()

        all_plot_page_text = ""

        sankey_text = ""

        #these plots will be output in the same directory as the final document, so output_dir path prefix is not needed
        networth_line_plot_path =  report_id + '_networth_line_plot.png'
        net_gain_loss_line_plot_path =  report_id + '_net_gain_loss_line_plot.png'
        accounttype_line_plot_path =  report_id + '_accounttype_line_plot.png'
        marginal_interest_line_plot_path =  report_id + '_marginal_interest_line_plot.png'
        milestone_scatter_plot_path =  report_id + '_milestone_scatter_plot.png'
        all_line_plot_path =  report_id + '_all_line_plot.png'
        sankey_path = report_id +'_sankey.jpg'


        #E.plotAll(all_line_plot_path)
        #E.plotNetWorth(networth_line_plot_path)
        #E.plotAccountTypeTotals(accounttype_line_plot_path)

        self.plotAll(E,output_dir + all_line_plot_path)
        self.plotNetWorth(E, output_dir + networth_line_plot_path)
        self.plotAccountTypeTotals(E, output_dir + accounttype_line_plot_path)
        self.plotMarginalInterest(E, output_dir + marginal_interest_line_plot_path)
        self.plotNetGainLoss(E, output_dir + net_gain_loss_line_plot_path)
        self.plotMilestoneDates(E,output_dir + milestone_scatter_plot_path)
        self.plotSankeyDiagram(E, output_dir + sankey_path)

        #print(E.forecast_df.to_string())

        left_fail_style_tag = ""
        right_fail_style_tag = ""
        fail_message = ""
        if forecast_failed:
            left_fail_style_tag = "<font color =\"red\">"
            right_fail_style_tag = "</font>"
            fail_message = "This forecast failed to reach the end. The results may not reflect the effect of non-essential transactions accurately."

        html_body = """
        <!DOCTYPE html>
        <html>
        <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Expense Forecast Report #""" + str(report_id) + """</title>
        <style>
        /* Style the tab */
        .tab {
          overflow: hidden;
          border: 1px solid #ccc;
          background-color: #f1f1f1;
        }

        /* Style the buttons that are used to open the tab content */
        .tab button {
          background-color: inherit;
          float: left;
          border: none;
          outline: none;
          cursor: pointer;
          padding: 14px 16px;
          transition: 0.3s;
        }

        /* Change background color of buttons on hover */
        .tab button:hover {
          background-color: #ddd;
        }

        /* Create an active/current tablink class */
        .tab button.active {
          background-color: #ccc;
        }

        /* Style the tab content */
        .tabcontent {
          display: none;
          padding: 6px 12px;
          border: 1px solid #ccc;
          border-top: none;
        }
        </style>


        </head>
        <body>
        <h1>""" + left_fail_style_tag + """Expense Forecast Report #""" + str(report_id) + right_fail_style_tag + """</h1>
        <p>"""+start_date+""" to """+end_date + " " + left_fail_style_tag + fail_message + right_fail_style_tag + " " + parent_report_text + """</p>

        <!-- Tab links -->
        <div class="tab">
          <button class="tablinks active" onclick="openTab(event, 'ForecastParameters')">Forecast Parameters</button>
          <button class="tablinks" onclick="openTab(event, 'NetWorth')">Net Worth</button>
          <button class="tablinks" onclick="openTab(event, 'NetGainLoss')">Net Gain & Loss</button>
          <button class="tablinks" onclick="openTab(event, 'AccountType')">Account Type</button>
          <button class="tablinks" onclick="openTab(event, 'Interest')">Interest</button>
          <button class="tablinks" onclick="openTab(event, 'Milestones')">Milestones</button>
          <button class="tablinks" onclick="openTab(event, 'All')">All</button>
          <button class="tablinks" onclick="openTab(event, 'TransactionSchedule')">Transaction Schedule</button>
          <button class="tablinks" onclick="openTab(event, 'Sankey')">Sankey</button>
          <button class="tablinks" onclick="openTab(event, 'Forecast Results')">Forecast Results</button>
        </div>

        <!-- Tab content -->
        <div id="ForecastParameters" class="tabcontent">
          <h3>Forecast Parameters</h3>
          <p>"""+summary_text+"""</p>
          <h3>Accounts</h3>
          <p>"""+account_text+"""</p>
          <h3>Budget Items</h3>
          <p>"""+budget_set_text+"""</p>
          <h3>Memo Rules</h3>
          <p>"""+memo_rule_text+"""</p>
          <h3>Account Milestones</h3>
          <p>"""+account_milestone_text+"""</p>
          <h3>Memo Milestones</h3>
          <p>"""+memo_milestone_text+"""</p>
          <h3>Composite Milestones</h3>
          <p>"""+composite_milestone_text+"""</p>
        </div>

        <div id="NetWorth" class="tabcontent">
          <h3>Net Worth</h3>
          <p>"""+networth_text+"""</p>
          <img src=\""""+networth_line_plot_path+"""\">
        </div>

        <div id="NetGainLoss" class="tabcontent">
          <h3>Net Gain & Loss</h3>
          <p>""" + net_gain_loss_text + """</p>
          <img src=\""""+net_gain_loss_line_plot_path+"""\">
        </div>

        <div id="AccountType" class="tabcontent">
          <h3>Account Type</h3>
          <p>"""+account_type_text+"""</p>
          <img src=\""""+accounttype_line_plot_path+"""\">
        </div>

        <div id="Interest" class="tabcontent">
          <h3>Interest</h3>
          <p>""" + interest_text + """</p>
          <img src=\""""+marginal_interest_line_plot_path+"""\">
          """ + interest_table_html + """
        </div>
        
        <div id="Milestones" class="tabcontent">
          <h3>Milestones</h3>
          <p>""" + milestone_text + """</p>
          
          <img src=\""""+milestone_scatter_plot_path+"""\">
          
          <h4>Account Milestones</h4>
          """ + E.getAccountMilestoneResultsDF().to_html() + """ <br>
          <h4>Memo Milestones</h4>
          """ + E.getMemoMilestoneResultsDF().to_html() + """ <br>
          <h4>Composite Milestones</h4>
          """ + E.getCompositeMilestoneResultsDF().to_html() + """ <br>
          
        </div>

        <div id="All" class="tabcontent">
          <h3>All</h3>
          <p>""" + all_plot_page_text + """</p>
          <img src=\""""+all_line_plot_path+"""\">
        </div>
        
        <div id="TransactionSchedule" class="tabcontent">
          <h3>Transaction Schedule</h3>
          <p>""" + transaction_schedule_text + """</p><br>
          Non-essential transactions: <br>
          <p>""" + p2_plus_txns_html_table + """</p><br><br>
          Credit Card Payments: <br>
          <p>""" + cc_payments_html_table + """</p><br><br>
          Loan Payments: <br>
          <p>""" + loan_payment_html_table + """</p><br><br>
          All Transactions: <br>
          """ + E.confirmed_df.to_html() + """
        </div>
        
        <div id="Sankey" class="tabcontent">
          <h3>Sankey</h3>
          <p>""" + sankey_text + """</p>
          <img src=\""""+sankey_path+"""\">
        </div>

        <div id="Forecast Results" class="tabcontent">
          <h3>Forecast Results</h3>
          <p>""" + summary_text + """</p>
          <p>The visualized data are below:</p>
          <h4>Forecast #"""+str(E.unique_id)+""":</h4>
          """ + E.forecast_df.to_html() + """
        </div>

        <br>

        <script>
        function openTab(evt, tabName) {
          // Declare all variables
          var i, tabcontent, tablinks;

          // Get all elements with class="tabcontent" and hide them
          tabcontent = document.getElementsByClassName("tabcontent");
          for (i = 0; i < tabcontent.length; i++) {
            tabcontent[i].style.display = "none";
          }

          // Get all elements with class="tablinks" and remove the class "active"
          tablinks = document.getElementsByClassName("tablinks");
          for (i = 0; i < tablinks.length; i++) {
            tablinks[i].className = tablinks[i].className.replace(" active", "");
          }

          // Show the current tab, and add an "active" class to the button that opened the tab
          document.getElementById(tabName).style.display = "block";
          evt.currentTarget.className += " active";
        }
        
        //having this here leaves the ForecastParameters tab open when the page first loads
        document.getElementById("ForecastParameters").style.display = "block";
        </script>

        </body>
        </html>

        """


        with open(output_dir+output_file_name+'.html','w') as f:
            f.write(html_body)
        log_in_color(logger,'green','info','Finished writing single forecast report to '+output_dir+output_file_name+'.html')

    # def getRuntimeEstimate(self,expense_forecast):
    #     E = expense_forecast
    #     log_in_color('green', 'debug','getRuntimeEstimate(start_date_YYYYMMDD='+str(E.start_date_YYYYMMDD)+',end_date_YYYYMMDD='+str(E.end_date_YYYYMMDD)+')')
    #
    #     budget_schedule_df = E.initial_budget_set.getBudgetSchedule(E.start_date_YYYYMMDD,E.end_date_YYYYMMDD)
    #
    #     #budget_schedule_df
    #
    #     # "Date" "Priority" "Amount" "Memo" "Deferrable" "Partial_Payment_Allowed"
    #
    #     # day length = 1.88 seconds on my mac
    #     # satisfice_time = number of days * day_length
    #     # for each non-deferrable, partial-payment-not-allowed proposed item, add (end_date - date) * day_length
    #     # for each partial payment allowed item, add [ (end_date - date) * 7.5 seconds, (end_date - date) * 7.5 seconds * 2 ] to get an range time estimate
    #     # for each deferrable payment, add [ (end_date - date) * day_length, ( 1 + FLOOR( (end_date - date) / 14) )^2 / 2 * day_length ]
    #
    #     raise NotImplementedError

    def initialize_forecasts_with_scenario_set(self,account_set,scenario_set,memo_rule_set,start_date_YYYYMMDD,end_date_YYYYMMDD,milestone_set):

        forecast_dict = {}
        for key__scenario_name, value__budget_set in scenario_set.scenarios.items():
            #account_set, budget_set, memo_rule_set, start_date_YYYYMMDD, end_date_YYYYMMDD,milestone_set,
            E = ExpenseForecast.ExpenseForecast(account_set=copy.deepcopy(account_set),
                                                                budget_set=copy.deepcopy(value__budget_set),
                                                                memo_rule_set=memo_rule_set,
                                                                start_date_YYYYMMDD=start_date_YYYYMMDD,
                                                                end_date_YYYYMMDD=end_date_YYYYMMDD,
                                                                milestone_set=milestone_set)
            forecast_dict[key__scenario_name] = E

        #return fict of ExpenseForecasts that have not been run
        return forecast_dict

    def initialize_forecasts_from_file(self, source_path, list_of_file_names):

        E_list = []
        for fname in list_of_file_names:
            E_list.append(ExpenseForecast.initialize_from_json_file(source_path+fname)[0])

        E__dict = {}
        for E in E_list:
            E__dict[E.scenario_name] = E

        return E__dict

    def run_forecast_set(self, E__dict):

        program_start = datetime.datetime.now()
        scenario_index = 0
        for scenario_name, E in E__dict.items():
            log_in_color(logger, 'white', 'info','Starting simulation scenario '+str(scenario_index)+' / '+str(len(E__dict))+': '+str(scenario_name))

            loop_start = datetime.datetime.now()

            try:
                E.runForecast()
                E.appendSummaryLines()
                E.scenario_name = scenario_name
                E.writeToJSONFile('./')
                self.generateHTMLReport(E)
            except Exception as e:
                log_in_color(logger,'red','error','simulation scenario '+str(scenario_index)+' / '+str(len(E__dict))+': '+str(scenario_name)+' FAILED')
                log_in_color(logger, 'red', 'error', e.args)

            loop_finish = datetime.datetime.now()

            loop_delta = loop_finish - loop_start
            time_since_started = loop_finish - program_start

            average_time_per_loop = time_since_started.seconds / (scenario_index + 1)
            loops_remaining = len(E__dict) - (scenario_index + 1)
            ETC = loop_finish + datetime.timedelta(seconds=average_time_per_loop*loops_remaining)
            progress_string = 'Finished in '+str(loop_delta.seconds)+' seconds. ETC: '+str(ETC.strftime('%Y-%m-%d %H:%M:%S'))

            log_in_color(logger, 'white', 'info',progress_string)

            scenario_index += 1
        return E__dict

    def run_forecast_set_parallel(self,E__dict):

        manager = mp.Manager()
        return_dict = manager.dict()

        process_list = []
        for scenario_name, scenario_E in E__dict.items():
            P = mp.Process(target = scenario_E.runSingleParallelForecast, args=(return_dict,) )
            P.start()
            process_list.append(P)

        for P in process_list:
            P.join()

        return return_dict

        # scenario_index = 0
        # for scenario_name, scenario_E in E__dict.items():
        #     log_in_color(logger, 'white', 'info','Starting simulation scenario '+str(scenario_index)+' / '+str(len(E__dict))+': '+str(scenario_name))
        #
        #     loop_start = datetime.datetime.now()
        #
        #     try:
        #         E__dict[scenario_name] = scenario_E.runForecast()
        #
        #         E__dict[scenario_name].appendSummaryLines()
        #         E__dict[scenario_name].writeToJSONFile('./')
        #         self.generateHTMLReport(E__dict[scenario_name])
        #     except Exception as e:
        #         log_in_color(logger,'red','error','simulation scenario '+str(scenario_index)+' / '+str(len(E__dict))+': '+str(scenario_name)+' FAILED')
        #
        #     loop_finish = datetime.datetime.now()
        #
        #     loop_delta = loop_finish - loop_start
        #     time_since_started = loop_finish - program_start
        #
        #     average_time_per_loop = time_since_started.seconds / (scenario_index + 1)
        #     loops_remaining = len(E__dict) - (scenario_index + 1)
        #     ETC = loop_finish + datetime.timedelta(seconds=average_time_per_loop*loops_remaining)
        #     progress_string = 'Finished in '+str(loop_delta.seconds)+' seconds. ETC: '+str(ETC.strftime('%Y-%m-%d %H:%M:%S'))
        #
        #     log_in_color(logger, 'white', 'info',progress_string)
        #
        #     scenario_index += 1
        return E__dict

    def plotAccountTypeComparison(self,E1,E2,output_path, line_color_cycle_list=['blue','orange','green'], lw_cycle=['1','3']):
        """
        Single-line description

        Multiple line description.


        :param E1:
        :param E2:
        :param output_path:
        :return:
        """
        figure(figsize=(14, 6), dpi=80)
        plt.gca().set_prop_cycle(plt.cycler(color=line_color_cycle_list))

        E1_relevant_columns_sel_vec = (E1.forecast_df.columns == 'Date') | (E1.forecast_df.columns == 'Loan Total') | (E1.forecast_df.columns == 'CC Debt Total') | (E1.forecast_df.columns == 'Liquid Total')
        E2_relevant_columns_sel_vec = (E2.forecast_df.columns == 'Date') | (E2.forecast_df.columns == 'Loan Total') | (E2.forecast_df.columns == 'CC Debt Total') | (E2.forecast_df.columns == 'Liquid Total')
        E1_relevant_df = E1.forecast_df.iloc[:, E1_relevant_columns_sel_vec]
        E2_relevant_df = E2.forecast_df.iloc[:, E2_relevant_columns_sel_vec]

        relevant_df = pd.merge(E1_relevant_df,E2_relevant_df,on=["Date"], suffixes=('_1','_2'))

        # this plot always has 6 lines, so we can make the plot more clear by using warm colors for Forecast 1 and cool colors for Forecast 2
        relevant_df = relevant_df[['Date','Loan Total_1','CC Debt Total_1','Liquid Total_1','Loan Total_2','CC Debt Total_2','Liquid Total_2']]
        color_array = ['orange','blue','green','orange','blue','green']

        x_values = [datetime.datetime.strptime(d, '%Y%m%d') for d in relevant_df['Date']]
        for i in range(1, relevant_df.shape[1]):
            if i > 3:
                ls = 'dashed'
            else:
                ls = 'solid'

            plt.plot(x_values, relevant_df.iloc[:, i], label=relevant_df.columns[i],color=color_array[i-1],linestyle=ls)

        bottom, top = plt.ylim()

        if 0 < bottom:
            plt.ylim(0, top)
        elif top < 0:
            plt.ylim(bottom, 0)

        ax = plt.subplot(111)
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])

        # Put a legend below current axis
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True, ncol=4)


        min_date = min([ datetime.datetime.strptime(d,'%Y%m%d') for d in E1.forecast_df.Date])
        max_date = max([ datetime.datetime.strptime(d,'%Y%m%d') for d in E1.forecast_df.Date])
        plt.title('Forecast 1 #' + E1.unique_id + ' vs. Forecast 2 #'+E2.unique_id+': ' + str(min_date) + ' -> ' + str(max_date))
        plt.xticks(rotation=90)
        plt.savefig(output_path)
        matplotlib.pyplot.close()

    def plotNetWorthComparison(self, E1, E2, output_path, line_color_cycle_list=['blue']):
        """
        Single-line description

        Multiple line description.


        :param E1:
        :param E2:
        :param output_path:
        :return:
        """
        figure(figsize=(14, 6), dpi=80)
        plt.gca().set_prop_cycle(plt.cycler(color=line_color_cycle_list))

        E1_relevant_columns_sel_vec = (E1.forecast_df.columns == 'Date') | (E1.forecast_df.columns == 'Net Worth')
        E2_relevant_columns_sel_vec = (E2.forecast_df.columns == 'Date') | (E2.forecast_df.columns == 'Net Worth')
        E1_relevant_df = E1.forecast_df.iloc[:, E1_relevant_columns_sel_vec]
        E2_relevant_df = E2.forecast_df.iloc[:, E2_relevant_columns_sel_vec]

        relevant_df = pd.merge(E1_relevant_df, E2_relevant_df, on=["Date"], suffixes=('_1', '_2'))

        # this plot always has 6 lines, so we can make the plot more clear by using warm colors for Forecast 1 and cool colors for Forecast 2
        relevant_df = relevant_df[['Date', 'Net Worth_1', 'Net Worth_2']]

        for i in range(1, relevant_df.shape[1]):
            if i == 1:
                ls = 'solid'
                label = 'Net Worth '+str(E1.unique_id)
            elif i == 2:
                ls = 'dashed'
                label = 'Net Worth ' + str(E2.unique_id)
            x_values = [datetime.datetime.strptime(d, '%Y%m%d') for d in relevant_df['Date']]
            plt.plot(x_values, relevant_df.iloc[:, i], label=label,linestyle=ls)

        bottom, top = plt.ylim()

        if 0 < bottom:
            plt.ylim(0, top)
        elif top < 0:
            plt.ylim(bottom, 0)

        ax = plt.subplot(111)
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])

        # Put a legend below current axis
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True, ncol=4)

        min_date = min([datetime.datetime.strptime(d, '%Y%m%d') for d in E1.forecast_df.Date])
        max_date = max([datetime.datetime.strptime(d, '%Y%m%d') for d in E1.forecast_df.Date])
        plt.title('Forecast 1 #' + E1.unique_id + ' vs. Forecast 2 #' + E2.unique_id + ': ' + str(min_date) + ' -> ' + str(max_date))
        plt.xticks(rotation=90)
        plt.savefig(output_path)
        matplotlib.pyplot.close()

    def plotMarginalInterestComparison(self, E1, E2, output_path):
        """
        Writes to file a plot of all accounts.

        Multiple line description.


        :param forecast_df:
        :param output_path:
        :return:
        """
        figure(figsize=(14, 6), dpi=80)

        E1_relevant_columns_sel_vec = (E1.forecast_df.columns == 'Date') | (E1.forecast_df.columns == 'Marginal Interest')
        E2_relevant_columns_sel_vec = (E2.forecast_df.columns == 'Date') | (E2.forecast_df.columns == 'Marginal Interest')
        E1_relevant_df = E1.forecast_df.iloc[:, E1_relevant_columns_sel_vec]
        E2_relevant_df = E2.forecast_df.iloc[:, E2_relevant_columns_sel_vec]

        relevant_df = pd.merge(E1_relevant_df, E2_relevant_df, on=["Date"], suffixes=('_1', '_2'))

        # this plot always has 6 lines, so we can make the plot more clear by using warm colors for Forecast 1 and cool colors for Forecast 2
        relevant_df = relevant_df[['Date', 'Marginal Interest_1', 'Marginal Interest_2']]

        for i in range(1, relevant_df.shape[1]):
            if i == 1:
                ls = 'solid'
                label = 'Marginal Interest ' + str(E1.unique_id)
            elif i == 2:
                ls = 'dashed'
                label = 'Marginal Interest ' + str(E2.unique_id)
            x_values = [datetime.datetime.strptime(d, '%Y%m%d') for d in relevant_df['Date']]
            plt.plot(x_values, relevant_df.iloc[:, i], color='blue', label=label, linestyle=ls)

        bottom, top = plt.ylim()

        if 0 < bottom:
            plt.ylim(0, top)
        elif top < 0:
            plt.ylim(bottom, 0)

        ax = plt.subplot(111)
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])

        # Put a legend below current axis
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True, ncol=4)

        min_date = min([datetime.datetime.strptime(d, '%Y%m%d') for d in E1.forecast_df.Date])
        max_date = max([datetime.datetime.strptime(d, '%Y%m%d') for d in E1.forecast_df.Date])
        plt.title(
            'Forecast 1 #' + E1.unique_id + ' vs. Forecast 2 #' + E2.unique_id + ': ' + str(min_date) + ' -> ' + str(
                max_date))
        plt.xticks(rotation=90)
        plt.savefig(output_path)
        matplotlib.pyplot.close()

    def plotNetGainLossComparison(self, E1, E2, output_path):
        """
        Writes to file a plot of all accounts.

        Multiple line description.


        :param forecast_df:
        :param output_path:
        :return:
        """

        figure(figsize=(14, 6), dpi=80)

        # lets combine curr and prev, principal and interest, and exclude summary lines
        E1_account_info = E1.initial_account_set.getAccounts()
        E2_account_info = E2.initial_account_set.getAccounts()
        E1_account_base_names = set([a.split(':')[0] for a in E1_account_info.Name])
        E2_account_base_names = set([a.split(':')[0] for a in E2_account_info.Name])

        assert E1_account_base_names == E2_account_base_names


        relevant_df = pd.merge(E1.forecast_df, E2.forecast_df, on=["Date"], suffixes=('_1', '_2'))

        x_values = [datetime.datetime.strptime(d, '%Y%m%d') for d in relevant_df['Date']]

        column_index = relevant_df.columns.tolist().index('Net Gain_1')
        plt.plot(x_values, relevant_df.iloc[:, column_index], color = 'green', label='Net Gain '+str(E1.unique_id), linestyle='solid')

        column_index = relevant_df.columns.tolist().index('Net Gain_2')
        plt.plot(x_values, relevant_df.iloc[:, column_index], color = 'green', label='Net Gain '+str(E2.unique_id), linestyle='dashed')

        column_index = relevant_df.columns.tolist().index('Net Loss_1')
        plt.plot(x_values, relevant_df.iloc[:, column_index], color = 'red', label='Net Loss '+str(E1.unique_id), linestyle='solid')

        column_index = relevant_df.columns.tolist().index('Net Loss_2')
        plt.plot(x_values, relevant_df.iloc[:, column_index], color = 'red', label='Net Loss '+str(E2.unique_id), linestyle='dashed')

        bottom, top = plt.ylim()
        if 0 < bottom:
            plt.ylim(0, top)
        elif top < 0:
            plt.ylim(bottom, 0)

        ax = plt.subplot(111)
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])

        # Put a legend below current axis
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True, ncol=4)

        # TODO plotOverall():: a large number of accounts will require some adjustment here so that the legend is entirely visible

        min_date = min([datetime.datetime.strptime(d, '%Y%m%d') for d in E1.forecast_df.Date])
        max_date = max([datetime.datetime.strptime(d, '%Y%m%d') for d in E1.forecast_df.Date])
        plt.title(
            'Forecast 1 #' + E1.unique_id + ' vs. Forecast 2 #' + E2.unique_id + ': ' + str(min_date) + ' -> ' + str(
                max_date))
        plt.xticks(rotation=90)
        plt.savefig(output_path)
        matplotlib.pyplot.close()

    def plotAllComparison(self, E1, E2, output_path, line_color_cycle_list=['blue'], lw_cycle=['1','3']):
        """
        Writes to file a plot of all accounts.

        Multiple line description.


        :param forecast_df:
        :param output_path:
        :return:
        """
        figure(figsize=(14, 6), dpi=80)
        plt.gca().set_prop_cycle(plt.cycler(color=line_color_cycle_list))

        #lets combine curr and prev, principal and interest, and exclude summary lines
        E1_account_info = E1.initial_account_set.getAccounts()
        E2_account_info = E2.initial_account_set.getAccounts()
        E1_account_base_names = set([ a.split(':')[0] for a in E1_account_info.Name])
        E2_account_base_names = set([a.split(':')[0] for a in E2_account_info.Name])

        assert E1_account_base_names == E2_account_base_names

        E1_aggregated_df = copy.deepcopy(E1.forecast_df.loc[:,['Date']])
        E2_aggregated_df = copy.deepcopy(E2.forecast_df.loc[:, ['Date']])

        for account_base_name in E1_account_base_names:
            E1_col_sel_vec = [ account_base_name == a.split(':')[0] for a in E1.forecast_df.columns]
            E1_col_sel_vec[0] = True #Date
            E1_relevant_df = E1.forecast_df.loc[:,E1_col_sel_vec]

            if E1_relevant_df.shape[1] == 2: #checking and savings case
                E1_aggregated_df[account_base_name] = E1_relevant_df.iloc[:,1]
            elif E1_relevant_df.shape[1] == 3:  #credit and loan
                E1_aggregated_df[account_base_name] = E1_relevant_df.iloc[:,1] + E1_relevant_df.iloc[:,2]

        for account_base_name in E2_account_base_names:
            E2_col_sel_vec = [ account_base_name == a.split(':')[0] for a in E2.forecast_df.columns]
            E2_col_sel_vec[0] = True #Date
            E2_relevant_df = E2.forecast_df.loc[:,E2_col_sel_vec]

            if E2_relevant_df.shape[1] == 2: #checking and savings case
                E2_aggregated_df[account_base_name] = E2_relevant_df.iloc[:,1]
            elif E2_relevant_df.shape[1] == 3:  #credit and loan
                E2_aggregated_df[account_base_name] = E2_relevant_df.iloc[:,1] + E2_relevant_df.iloc[:,2]


        relevant_df = pd.merge(E1_aggregated_df, E2_aggregated_df, on=["Date"], suffixes=('_1', '_2'))

        x_values = [datetime.datetime.strptime(d, '%Y%m%d') for d in relevant_df['Date']]
        for i in range(1, relevant_df.shape[1] - 1):
            plt.plot(x_values, relevant_df.iloc[:, i], label=relevant_df.columns[i])

        bottom, top = plt.ylim()
        if 0 < bottom:
            plt.ylim(0, top)
        elif top < 0:
            plt.ylim(bottom, 0)

        ax = plt.subplot(111)
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])

        # Put a legend below current axis
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True, ncol=4)

        # TODO plotOverall():: a large number of accounts will require some adjustment here so that the legend is entirely visible

        min_date = min([datetime.datetime.strptime(d, '%Y%m%d') for d in E1.forecast_df.Date])
        max_date = max([datetime.datetime.strptime(d, '%Y%m%d') for d in E1.forecast_df.Date])
        plt.title('Forecast 1 #'+E1.unique_id+' vs. Forecast 2 #'+E2.unique_id+': ' + str(min_date) + ' -> ' + str(max_date))
        plt.xticks(rotation=90)
        plt.savefig(output_path)
        matplotlib.pyplot.close()

    def plotAccountTypeTotals(self, expense_forecast, output_path, line_color_cycle_list=['blue','orange','green'], linestyle='solid'):
        """
        Writes to file a plot of all accounts.

        Multiple line description.


        :param forecast_df:
        :param output_path:
        :return:
        """

        assert hasattr(expense_forecast,'forecast_df')

        figure(figsize=(14, 6), dpi=80)
        plt.gca().set_prop_cycle(plt.cycler(color=line_color_cycle_list))

        relevant_columns_sel_vec = (expense_forecast.forecast_df.columns == 'Date') | (expense_forecast.forecast_df.columns == 'Loan Total') | (expense_forecast.forecast_df.columns == 'CC Debt Total') | (expense_forecast.forecast_df.columns == 'Liquid Total')
        relevant_df = expense_forecast.forecast_df.iloc[:,relevant_columns_sel_vec]

        x_values = [datetime.datetime.strptime(d, '%Y%m%d') for d in relevant_df['Date']]
        for i in range(1, relevant_df.shape[1]):
            if i == 1:
                label = 'CC Debt Total '+str(expense_forecast.unique_id)
            elif i == 2:
                label = 'Loan Total '+str(expense_forecast.unique_id)
            elif i == 3:
                label = 'Liquid Total '+str(expense_forecast.unique_id)
            plt.plot(x_values, relevant_df.iloc[:, i], label=label,linestyle=linestyle)

        bottom, top = plt.ylim()

        if 0 < bottom:
            plt.ylim(0,top)
        elif top < 0:
            plt.ylim(bottom, 0)

        ax = plt.subplot(111)
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])

        # Put a legend below current axis
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True, ncol=4)

        # TODO plotOverall():: a large number of accounts will require some adjustment here so that the legend is entirely visible
        date_as_datetime_type = [datetime.datetime.strptime(d, '%Y%m%d') for d in expense_forecast.forecast_df.Date]

        min_date = min(date_as_datetime_type).strftime('%Y-%m-%d')
        max_date = max(date_as_datetime_type).strftime('%Y-%m-%d')
        plt.title('Forecast #'+expense_forecast.unique_id+': ' + str(min_date) + ' -> ' + str(max_date))
        plt.xticks(rotation=90)
        plt.savefig(output_path)
        matplotlib.pyplot.close()

    def plotNetGainLoss(self, expense_forecast, output_path, line_color_cycle_list=['green','red'],linestyle='solid'):
        assert hasattr(expense_forecast, 'forecast_df')

        figure(figsize=(14, 6), dpi=80)
        plt.gca().set_prop_cycle(plt.cycler(color=line_color_cycle_list))

        x_values = [datetime.datetime.strptime(d, '%Y%m%d') for d in expense_forecast.forecast_df['Date']]

        # for i in range(1, self.forecast_df.shape[1] - 1):
        column_index = expense_forecast.forecast_df.columns.tolist().index('Net Gain')
        plt.plot(x_values, expense_forecast.forecast_df.iloc[:, column_index],
                 label='Net Gain '+str(expense_forecast.unique_id))

        column_index = expense_forecast.forecast_df.columns.tolist().index('Net Loss')
        plt.plot(x_values, expense_forecast.forecast_df.iloc[:, column_index],label='Net Loss '+str(expense_forecast.unique_id),linestyle=linestyle)

        bottom, top = plt.ylim()

        if 0 < bottom:
            plt.ylim(0, top)
        elif top < 0:
            plt.ylim(bottom, 0)

        ax = plt.subplot(111)
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])

        # Put a legend below current axis
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True, ncol=4)

        date_as_datetime_type = [datetime.datetime.strptime(d, '%Y%m%d') for d in expense_forecast.forecast_df.Date]

        min_date = min(date_as_datetime_type).strftime('%Y-%m-%d')
        max_date = max(date_as_datetime_type).strftime('%Y-%m-%d')
        plt.title('Forecast #' + expense_forecast.unique_id + ': ' + str(min_date) + ' -> ' + str(max_date))
        plt.xticks(rotation=90)
        plt.savefig(output_path)
        matplotlib.pyplot.close()

    def plotNetWorth(self, expense_forecast, output_path, line_color_cycle_list=['blue'], linestyle='solid'):
        """
        Writes to file a plot of all accounts.

        Multiple line description.


        :param forecast_df:
        :param output_path:
        :return:
        """

        assert hasattr(expense_forecast,'forecast_df')

        figure(figsize=(14, 6), dpi=80)
        plt.gca().set_prop_cycle(plt.cycler(color=line_color_cycle_list))

        column_index = expense_forecast.forecast_df.columns.tolist().index('Net Worth')
        x_values = [ datetime.datetime.strptime(d,'%Y%m%d') for d in expense_forecast.forecast_df['Date'] ]
        plt.plot( x_values, expense_forecast.forecast_df.iloc[:, column_index], label='Net Worth '+str(expense_forecast.unique_id),linestyle=linestyle)

        bottom, top = plt.ylim()
        top = top * 1.1 #otherwise doesnt show up if line is super flat

        if 0 < bottom:
            plt.ylim(0,top)
        elif top < 0:
            plt.ylim(bottom, 0)

        ax = plt.subplot(111)
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])

        # Put a legend below current axis
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True, ncol=4)

        # TODO plotOverall():: a large number of accounts will require some adjustment here so that the legend is entirely visible

        date_as_datetime_type = [datetime.datetime.strptime(d, '%Y%m%d') for d in expense_forecast.forecast_df.Date]

        min_date = min(date_as_datetime_type).strftime('%Y-%m-%d')
        max_date = max(date_as_datetime_type).strftime('%Y-%m-%d')
        plt.title('Forecast #'+expense_forecast.unique_id+': ' + str(min_date) + ' -> ' + str(max_date))
        plt.xticks(rotation=90)
        plt.savefig(output_path)
        matplotlib.pyplot.close()

    def plotAll(self, expense_forecast, output_path, line_color_cycle_list=default_color_cycle_list):
        """
        Writes to file a plot of all accounts.

        Multiple line description.


        :param forecast_df:
        :param output_path:
        :return:
        """

        assert hasattr(expense_forecast,'forecast_df')

        figure(figsize=(14, 6), dpi=80)
        plt.gca().set_prop_cycle(plt.cycler(color=line_color_cycle_list))

        #lets combine curr and prev, principal and interest, and exclude summary lines
        account_info = expense_forecast.initial_account_set.getAccounts()
        account_base_names = set([ a.split(':')[0] for a in account_info.Name])

        aggregated_df = copy.deepcopy(expense_forecast.forecast_df.loc[:,['Date']])

        for account_base_name in account_base_names:
            col_sel_vec = [ account_base_name == a.split(':')[0] for a in expense_forecast.forecast_df.columns ]
            col_sel_vec[0] = True #Date
            relevant_df = expense_forecast.forecast_df.loc[:,col_sel_vec]

            if relevant_df.shape[1] == 2: #checking and savings case
                aggregated_df[account_base_name] = relevant_df.iloc[:,1]
            elif relevant_df.shape[1] == 3:  #credit and loan
                aggregated_df[account_base_name] = relevant_df.iloc[:,1] + relevant_df.iloc[:,2]

            x_values = [datetime.datetime.strptime(d, '%Y%m%d') for d in aggregated_df['Date']]
            plt.plot(x_values, aggregated_df[account_base_name], label=account_base_name)

        #for i in range(1, aggregated_df.shape[1] - 1):
        #   pass

        bottom, top = plt.ylim()
        if 0 < bottom:
            plt.ylim(0, top)
        elif top < 0:
            plt.ylim(bottom, 0)

        ax = plt.subplot(111)
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])

        # Put a legend below current axis
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True, ncol=4)

        # TODO plotOverall():: a large number of accounts will require some adjustment here so that the legend is entirely visible

        date_as_datetime_type = [ datetime.datetime.strptime(d,'%Y%m%d') for d in expense_forecast.forecast_df.Date]

        min_date = min(date_as_datetime_type).strftime('%Y-%m-%d')
        max_date = max(date_as_datetime_type).strftime('%Y-%m-%d')
        plt.title('Forecast #'+expense_forecast.unique_id+': ' + str(min_date) + ' -> ' + str(max_date))
        plt.xticks(rotation=90)
        plt.savefig(output_path)
        matplotlib.pyplot.close()

    def plotMarginalInterest(self, expense_forecast, output_path, linestyle='solid'):
        """
        Writes a plot of spend on interest from all sources.

        Multiple line description.

        :param accounts_df:
        :param forecast_df:
        :param output_path:
        :return:
        """

        assert hasattr(expense_forecast,'forecast_df')
        figure(figsize=(14, 6), dpi=80)
        plt.gca().set_prop_cycle(plt.cycler(color=['blue']))

        column_index = expense_forecast.forecast_df.columns.tolist().index('Marginal Interest')
        x_values = [datetime.datetime.strptime(d, '%Y%m%d') for d in expense_forecast.forecast_df['Date']]
        plt.plot(x_values, expense_forecast.forecast_df.iloc[:, column_index],
                 label='Marginal Interest ' + str(expense_forecast.unique_id),linestyle=linestyle)

        bottom, top = plt.ylim()

        if 0 < bottom:
            plt.ylim(0, top)
        elif top < 0:
            plt.ylim(bottom, 0)

        ax = plt.subplot(111)
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])

        # Put a legend below current axis
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True, ncol=4)

        date_as_datetime_type = [datetime.datetime.strptime(d, '%Y%m%d') for d in expense_forecast.forecast_df.Date]

        min_date = min(date_as_datetime_type).strftime('%Y-%m-%d')
        max_date = max(date_as_datetime_type).strftime('%Y-%m-%d')
        plt.title('Forecast #' + expense_forecast.unique_id + ': ' + str(min_date) + ' -> ' + str(max_date))
        plt.xticks(rotation=90)
        plt.savefig(output_path)
        matplotlib.pyplot.close()

    def generateScenarioSetHTMLReport(self, expense_forecast__dict, output_dir='./'):

        report_id = '000000'
        output_report_path = output_dir + 'ForecastSummary.html'

        list_of_forecast_links_html = ""
        for E_key, E_value in expense_forecast__dict.items():
            E_value.writeToJSONFile('./')
            self.generateHTMLReport(E_value,output_dir,output_report_path) #todo undo this
            list_of_forecast_links_html += "<a href=\"Forecast_"+str(E_value.unique_id)+".html\">Forecast "+str(E_value.unique_id)+" "+str(E_key)+"</a><br>"

        milestone_difference_table_df = self.calculateMilestoneDifferenceTable(expense_forecast__dict)
        milestone_difference_table_html = milestone_difference_table_df.to_html()

        forecast_comparison_matrix_df = pd.DataFrame({})

        # forecast comparison matrix
        comparison_report_file_names = []
        single_report_scenario_names = []
        index_1 = 0
        for E_key_1, E_value_1 in expense_forecast__dict.items():
            index_2 = 0
            single_report_scenario_names.append(E_value_1.scenario_name)
            for E_key_2, E_value_2 in expense_forecast__dict.items():
                if E_key_1 == E_key_2:
                    report_href = "<a href=\"./" + 'Forecast_' + str(E_value_2.unique_id)+'.html' + "\">" + 'Forecast_' + str(E_value_2.unique_id)+'.html' + "</a>"
                    forecast_comparison_matrix_df.loc[index_1, index_2] = report_href
                    index_2 += 1
                    continue

                report_file_name = 'compare_' + str(E_value_1.unique_id) + '_' + str(E_value_2.unique_id)+'.html'
                comparison_report_file_names.append(report_file_name)
                self.generateCompareTwoForecastsHTMLReport(E_value_1,E_value_2,output_dir,output_report_path) #todo undo this

                report_href = "<a href=\"./" + report_file_name + "\">" + report_file_name + "</a>"
                forecast_comparison_matrix_df.loc[index_1, index_2] = report_href

                index_2 += 1
            index_1 += 1

        forecast_comparison_matrix_df.index = forecast_comparison_matrix_df.index.map(str)
        forecast_comparison_matrix_df.columns = forecast_comparison_matrix_df.columns.map(str)
        for row_index in range(0,len(single_report_scenario_names)):
            forecast_comparison_matrix_df = forecast_comparison_matrix_df.rename(index={str(row_index): single_report_scenario_names[row_index]})
            forecast_comparison_matrix_df = forecast_comparison_matrix_df.rename(columns={str(row_index): single_report_scenario_names[row_index]})
        forecast_comparison_matrix_html = forecast_comparison_matrix_df.to_html()

        #to_html sanitizes brackets, which we don't want
        forecast_comparison_matrix_html = forecast_comparison_matrix_html.replace('&lt;','<')
        forecast_comparison_matrix_html = forecast_comparison_matrix_html.replace('&gt;', '>')

        list_of_forecast_comparison_links_html = ""

        for comparison_report_file_name in comparison_report_file_names:
            list_of_forecast_comparison_links_html += "<a href=\"" + comparison_report_file_name + "\">"+comparison_report_file_name+"</a><br>"

        final_balance_plot_path = output_dir+'FinalBalancePlot.png'
        self.plotFinalBalancesOfForecastSet(expense_forecast__dict,final_balance_plot_path)

        milestone_plot_path = output_dir + 'ForecastSetMilestoneDates.png'
        self.plotMilestoneDatesForecastSet(expense_forecast__dict, milestone_plot_path)

        html_body = """
                <!DOCTYPE html>
                <html>
                <head>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <title>Expense ForecastSet Report #""" + str(report_id) + """</title>
                <style>
                /* Style the tab */
                .tab {
                  overflow: hidden;
                  border: 1px solid #ccc;
                  background-color: #f1f1f1;
                }

                /* Style the buttons that are used to open the tab content */
                .tab button {
                  background-color: inherit;
                  float: left;
                  border: none;
                  outline: none;
                  cursor: pointer;
                  padding: 14px 16px;
                  transition: 0.3s;
                }

                /* Change background color of buttons on hover */
                .tab button:hover {
                  background-color: #ddd;
                }

                /* Create an active/current tablink class */
                .tab button.active {
                  background-color: #ccc;
                }

                /* Style the tab content */
                .tabcontent {
                  display: none;
                  padding: 6px 12px;
                  border: 1px solid #ccc;
                  border-top: none;
                }
                </style>


                </head>
                <body>
                <h1>Expense Forecast Summary Report #""" + str(report_id) + """</h1>
                
                <!-- Tab links -->
                <div class="tab">
                  <button class="tablinks active" onclick="openTab(event, 'Summary')">Summary</button>
                </div>

                <!-- Tab content -->
                <div id="Summary" class="tabcontent">
                  <h3>Summary</h3>
                  """ + list_of_forecast_links_html + """ <br>
                  """ + list_of_forecast_comparison_links_html + """ <br>
                  """ + milestone_difference_table_html + """ <br>
                  """ + forecast_comparison_matrix_html + """ <br>
                  <img src=\"""" + final_balance_plot_path + """\"> <br>
                  <img src=\"""" + milestone_plot_path + """\"> <br>
                </div>

                <script>
                function openTab(evt, tabName) {
                  // Declare all variables
                  var i, tabcontent, tablinks;

                  // Get all elements with class="tabcontent" and hide them
                  tabcontent = document.getElementsByClassName("tabcontent");
                  for (i = 0; i < tabcontent.length; i++) {
                    tabcontent[i].style.display = "none";
                  }

                  // Get all elements with class="tablinks" and remove the class "active"
                  tablinks = document.getElementsByClassName("tablinks");
                  for (i = 0; i < tablinks.length; i++) {
                    tablinks[i].className = tablinks[i].className.replace(" active", "");
                  }

                  // Show the current tab, and add an "active" class to the button that opened the tab
                  document.getElementById(tabName).style.display = "block";
                  evt.currentTarget.className += " active";
                }

                //having this here leaves the ForecastParameters tab open when the page first loads
                document.getElementById("Summary").style.display = "block";
                </script>

                </body>
                </html>

                """

        with open(output_report_path,'w') as f:
            f.write(html_body)
        log_in_color(logger,'green','info','Finished writing scenario report to '+output_report_path)

    def calculateMilestoneDifferenceTable(self, expense_forecast__dict):

        final_table_df = pd.DataFrame() #todo this is for the case where there are no milestones. i did not think this through basically at all

        milestone_result_tables = []
        #all_table_df = pd.DataFrame({'Forecast_Id': [], 'Scenario_Id': [], 'Milestone_Type': [], 'Milestone_Name': [], 'Milestone_Date': []})
        for forecast_key, forecast_value in expense_forecast__dict.items():
            milestone_result_table_df = pd.DataFrame({'Forecast_Id': [], 'Scenario_Id': [], 'Milestone_Type': [], 'Milestone_Name': [], 'Milestone_Date': []})
            for milestone_name, milestone_value in forecast_value.account_milestone_results.items():
                new_row_df = pd.DataFrame({'Forecast_Id': [str(forecast_value.unique_id)], 'Scenario_Id': [forecast_key], 'Milestone_Type':['Account'],'Milestone_Name':[milestone_name],'Milestone_Date':[milestone_value]})
                milestone_result_table_df = pd.concat([milestone_result_table_df,new_row_df])
                #all_table_df = pd.concat([all_table_df,new_row_df])

            for milestone_name, milestone_value in forecast_value.memo_milestone_results.items():
                new_row_df = pd.DataFrame({'Forecast_Id': [str(forecast_value.unique_id)], 'Scenario_Id': [forecast_key], 'Milestone_Type':['Memo'],'Milestone_Name':[milestone_name],'Milestone_Date':[milestone_value]})
                milestone_result_table_df = pd.concat([milestone_result_table_df,new_row_df])
                #all_table_df = pd.concat([all_table_df, new_row_df])

            for milestone_name, milestone_value in forecast_value.composite_milestone_results.items():
                new_row_df = pd.DataFrame({'Forecast_Id': [str(forecast_value.unique_id)], 'Scenario_Id': [forecast_key], 'Milestone_Type':['Composite'],'Milestone_Name':[milestone_name],'Milestone_Date':[milestone_value]})
                milestone_result_table_df = pd.concat([milestone_result_table_df,new_row_df])
                #all_table_df = pd.concat([all_table_df, new_row_df])

            milestone_result_tables.append(milestone_result_table_df)

        if len(milestone_result_tables) > 0:
            all_table_df = pd.concat(milestone_result_tables)
            all_table_df.reset_index(drop=True,inplace=True)

            milestone_names = all_table_df.Milestone_Name.drop_duplicates()
            final_table_df = pd.DataFrame({})
            for milestone_name in milestone_names:
                row_sel_vec = (all_table_df.Milestone_Name == milestone_name)
                col_sel_vec = ( all_table_df.columns == 'Forecast_Id' ) | ( all_table_df.columns ==  'Milestone_Date' )
                relevant_results_df = all_table_df.loc[row_sel_vec, col_sel_vec]
                relevant_results_df.reset_index(drop=True, inplace=True)
                relevant_results_df = relevant_results_df.T

                for i in range(0,len(relevant_results_df.columns)):
                    relevant_results_df.rename(columns={i:relevant_results_df.iloc[0,i]},inplace=True)

                relevant_results_df = relevant_results_df.tail(1)
                relevant_results_df.reset_index(drop=True, inplace=True)
                relevant_results_df.index = relevant_results_df.index.map(str)
                relevant_results_df = relevant_results_df.rename(index={'0':milestone_name})

                if final_table_df.shape[0] == 0:
                    final_table_df = relevant_results_df
                else:
                    final_table_df = pd.concat([final_table_df,relevant_results_df])


            all_table_df.reset_index(drop=True,inplace=True)
        return final_table_df

    def plotScenarioSetMilestoneDifferences(self,expense_forecast__dict, line_color_cycle_list=['blue','red','purple']):
        #assert hasattr(expense_forecast, 'forecast_df')

        figure(figsize=(14, 6), dpi=80)
        fig, ax = plt.subplots()
        plt.gca().set_prop_cycle(plt.cycler(color=line_color_cycle_list)) #todo use this param

        #horizontal bar chart so y_values are same for each
        data_y = []
        all_keys = None
        for E_key, E_value in expense_forecast__dict.items():
            date_counter = 0

            AM = E_value.account_milestone_results
            MM = E_value.memo_milestone_results
            CM = E_value.composite_milestone_results

            am_keys = []
            for am_key, am_value in AM.items():
                # impute none as max
                if am_value is None:
                    am_value = E_value.end_date_YYYYMMDD
                if am_value == 'None':
                    am_value = E_value.end_date_YYYYMMDD
                am_keys.append(am_key)
                data_y.append(date_counter)
                date_counter += 1

            mm_keys = []
            for mm_key, mm_value in MM.items():
                # impute none as max
                if mm_value is None:
                    mm_value = E_value.end_date_YYYYMMDD
                if mm_value == 'None':
                    mm_value = E_value.end_date_YYYYMMDD
                mm_keys.append(mm_key)
                data_y.append(date_counter)
                date_counter += 1

            cm_keys = []
            for cm_key, cm_value in CM.items():
                # impute none as max
                if cm_value is None:
                    cm_value = E_value.end_date_YYYYMMDD
                if cm_value == 'None':
                    cm_value = E_value.end_date_YYYYMMDD
                cm_keys.append(cm_key)
                data_y.append(date_counter)
                date_counter += 1

            all_keys = am_keys + mm_keys + cm_keys
            break

        x_values_list = []
        for E_key, E_value in expense_forecast__dict.items():
            AM = E_value.account_milestone_results
            MM = E_value.memo_milestone_results
            CM = E_value.composite_milestone_results

            data_x = []
            date_counter = 0

            am_keys = []
            for am_key, am_value in AM.items():
                # impute none as max
                if am_value is None:
                    am_value = E_value.end_date_YYYYMMDD
                if am_value == 'None':
                    am_value = E_value.end_date_YYYYMMDD
                am_keys.append(am_key)
                data_x.append(am_value)
                date_counter += 1

            mm_keys = []
            for mm_key, mm_value in MM.items():
                # impute none as max
                if mm_value is None:
                    mm_value = E_value.end_date_YYYYMMDD
                if mm_value == 'None':
                    mm_value = E_value.end_date_YYYYMMDD
                mm_keys.append(mm_key)
                data_x.append(mm_value)
                date_counter += 1

            cm_keys = []
            for cm_key, cm_value in CM.items():
                # impute none as max
                if cm_value is None:
                    cm_value = E_value.end_date_YYYYMMDD
                if cm_value == 'None':
                    cm_value = E_value.end_date_YYYYMMDD
                cm_keys.append(cm_key)
                data_x.append(cm_value)
                date_counter += 1

            x_values_list.append(data_x)

        #transpose nested lists
        x_values_list = np.array(x_values_list).T.tolist()

        bottom, top = plt.ylim()
        if 0 < bottom:
            plt.ylim(0, top)
        elif top < 0:
            plt.ylim(bottom, 0)

        ax = plt.subplot(111)
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])

            # red_patch = mpatches.Patch(color='red', label='account')
            # blue_patch = mpatches.Patch(color='blue', label='memo')
            # purple_patch = mpatches.Patch(color='purple', label='composite')
            # plt.legend(handles=[red_patch, blue_patch, purple_patch], bbox_to_anchor=(1.15, 1), loc='upper right')

            # TODO plotOverall():: a large number of accounts will require some adjustment here so that the legend is entirely visible

        date_as_datetime_type = [datetime.datetime.strptime(d, '%Y%m%d') for d in E_value.forecast_df.Date]

        min_date = min(date_as_datetime_type).strftime('%Y-%m-%d')
        max_date = max(date_as_datetime_type).strftime('%Y-%m-%d')

        plt.title('Milestones' + ': ' + str(min_date) + ' -> ' + str(max_date))

        index = 0
        for x_values in x_values_list:
            plt.bar(x_values, index, 0.4, label=all_keys[index])
            index += 1

        plt.xticks(rotation=90)
        plt.savefig('ScenarioSetMilestoneDifferences.png')
        matplotlib.pyplot.close()

    def plotFinalBalancesOfForecastSet(self, dict_of_forecasts, output_path):

        figure()

        fig, ax = plt.subplots(figsize=(14, 6), dpi=80)


        #plt.gca().set_prop_cycle(plt.cycler(color=lin_colors))

        index = 0
        E_ids = []
        for E_key, E_value in dict_of_forecasts.items():
            assert hasattr(E_value, 'forecast_df')
            E_ids.append(E_value.unique_id)
            # df = pd.DataFrame(dict(graph=['Item one', 'Item two', 'Item three'],
            #                            n=[3, 5, 2], m=[6, 1, 3]))

            relevant_sel = E_value.forecast_df.columns != 'Net Gain'
            relevant_sel = relevant_sel & (E_value.forecast_df.columns != 'Net Loss')
            relevant_sel = relevant_sel & (E_value.forecast_df.columns != 'Marginal Interest')
            relevant_sel = relevant_sel & (E_value.forecast_df.columns !=  'Memo')

            relevant_df = E_value.forecast_df.loc[:,relevant_sel]

            #now group the related columns
            account_base_names = list(set([ n.split(':')[0] for n in relevant_df.columns ]))
            aggregated_df = pd.DataFrame(relevant_df['Date'])
            actual_account_base_names = []
            account_base_names.sort()
            for a in account_base_names:
                if a == 'Date' or a == 'Memo':
                    continue
                actual_account_base_names.append(a)
                # print('a:'+str(a))
                sel_vec = [ a in cname for cname in relevant_df.columns ]

                account_related_df = pd.DataFrame(relevant_df.loc[:, sel_vec])
                # print('account_related_df:')
                # print(account_related_df.to_string())

                if account_related_df.shape[1] == 1:
                    aggregated_df.insert(len(aggregated_df.columns), a, account_related_df.iloc[:,0], False)
                elif account_related_df.shape[1] == 2:
                    aggregated_df.insert(len(aggregated_df.columns), a, account_related_df.iloc[:,0] + account_related_df.iloc[:,1], False)



            # print('aggregated_df:')
            # print(aggregated_df.to_string())

            ind = np.arange(len(aggregated_df.columns)-1)
            width = 1 / (len(aggregated_df.columns)-2) #the denom here is 2 larger than number of bar groups

            #this working properly required all E have same columns, which is assumed but not enforced at this point
            lin_colors = cm.rainbow(np.linspace(0, 1, len(dict_of_forecasts)))

            color = lin_colors[index]
            for i in range(1,(len(aggregated_df.columns))):
                col_name = aggregated_df.columns[i]
                x_value = ind[(i-1)] + width * index
                plot_value = aggregated_df.iloc[:,i].tail(1).iat[0]
                ax.bar(x_value, plot_value, width, color = color) #color = , lebel =

            index += 1


            # #Marginal Interest	Net Gain	Net Loss	Net Worth	Loan Total	CC Debt Total	Liquid Tota
            # ax.barh(ind, E_value['Marginal Interest'], width, color='red', label='N')
            # ax.barh(ind, E_value['Net Gain'], width, color='red', label='N')
            # ax.barh(ind, E_value['Net Loss'], width, color='red', label='N')
            # ax.barh(ind, E_value['Loan Total'], width, color='red', label='N')
            # ax.barh(ind, E_value['CC Debt Total'], width, color='red', label='N')
            # ax.barh(ind, E_value['Liquid Total'], width, color='red', label='N')
            # ax.barh(ind + width, df.m, width, color='green', label='M')

        lin_colors = cm.rainbow(np.linspace(0, 1, len(dict_of_forecasts)))
        color_patches = []
        index = 0
        for c in lin_colors:
            color_patches.append( mpatches.Patch(color=c, label=E_ids[index]) )
            index += 1
        plt.legend(handles=color_patches, bbox_to_anchor=(1.15, 1), loc='best', prop={'size': 17})
        #ax.legend(fancybox=True, shadow=True)

        date_as_datetime_type = [datetime.datetime.strptime(d, '%Y%m%d') for d in E_value.forecast_df.Date]
        min_date = min(date_as_datetime_type).strftime('%Y-%m-%d')
        max_date = max(date_as_datetime_type).strftime('%Y-%m-%d')

        plt.title('Final Balances : ' + str(min_date) + ' -> ' + str(max_date))
        ax.set_xticks(ind, actual_account_base_names)
        plt.xticks(rotation=15)
        plt.savefig(output_path)
        matplotlib.pyplot.close()

    def plotMilestoneDatesForecastSet(self, dict_of_forecasts, output_path):

        figure() #todo idk if i need this
        fig, ax = plt.subplots(figsize=(14, 6), dpi=80)

        forecast_index = 0
        group_width = 1
        bar_width = 0.1
        E_ids = []
        milestone_names = []
        for E_key, E_value in dict_of_forecasts.items():
            assert hasattr(E_value, 'forecast_df')
            E_ids.append(E_value.unique_id)

            AMR = E_value.account_milestone_results
            MMR = E_value.memo_milestone_results
            CMR = E_value.composite_milestone_results

            no_of_milestones = len(AMR) + len(MMR) + len(CMR)
            lin_colors = cm.rainbow(np.linspace(0, 1, no_of_milestones ))
            plt.gca().set_prop_cycle(plt.cycler(color=lin_colors))
            milestone_index = 0
            if len(AMR) > 0:
                for key, value in AMR.items():
                    if value == 'None':
                        continue
                    x_value = forecast_index * group_width + milestone_index * bar_width
                    y_value = matplotlib.dates.date2num(datetime.datetime.strptime(value, '%Y%m%d'))
                    ax.bar(x_value, y_value, bar_width)
                    milestone_names.append(key)
                    milestone_index += 1

            if len(MMR) > 0:
                for key, value in MMR.items():
                    if value == 'None':
                        continue
                    x_value =  forecast_index * group_width + milestone_index * bar_width
                    y_value = matplotlib.dates.date2num(datetime.datetime.strptime(value, '%Y%m%d'))
                    ax.bar(x_value, y_value, bar_width)
                    milestone_names.append(key)
                    milestone_index += 1

            if len(CMR) > 0:
                for key, value in CMR.items():
                    if value == 'None':
                        continue
                    x_value =  forecast_index * group_width + milestone_index * bar_width
                    y_value = matplotlib.dates.date2num(datetime.datetime.strptime(value, '%Y%m%d'))
                    ax.bar(x_value, y_value, bar_width)
                    milestone_names.append(key)
                    milestone_index += 1

            forecast_index += 1
            # left_int_ts = matplotlib.dates.date2num(
            #     datetime.datetime.strptime(expense_forecast.start_date_YYYYMMDD, '%Y%m%d'))
            # right_int_ts = matplotlib.dates.date2num(
            #     datetime.datetime.strptime(expense_forecast.end_date_YYYYMMDD, '%Y%m%d'))
            #
            # all_keys = am_keys + mm_keys + cm_keys
            # for i, txt in enumerate(all_keys):
            #     ax.annotate(txt, (data_x[i], data_y[i]))
            #
            # left = left_int_ts
            # right = right_int_ts
            #
            # plt.xlim(left, right)

            bottom, top = plt.ylim()
            new_bottom = matplotlib.dates.date2num(datetime.datetime.strptime(E_value.start_date_YYYYMMDD, '%Y%m%d'))
            new_top = matplotlib.dates.date2num(datetime.datetime.strptime(E_value.end_date_YYYYMMDD, '%Y%m%d'))
            plt.ylim(new_bottom,new_top)

            # if 0 < bottom:
            #     plt.ylim(0, top)
            # elif top < 0:
            #     plt.ylim(bottom, 0)


            #
            # ax = plt.subplot(111)
            # box = ax.get_position()
            # ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])


        lin_colors = cm.rainbow(np.linspace(0, 1, no_of_milestones ))
        color_patches = []
        index = 0
        for c in lin_colors:
            color_patches.append( mpatches.Patch(color=c, label=milestone_names[index]) )
            index += 1
        plt.legend(handles=color_patches,
                    #bbox_to_anchor=(1.15, 1),
                   loc='center right', prop={'size': 11})
        #ax.legend(fancybox=True, shadow=True)

        date_as_datetime_type = [datetime.datetime.strptime(d, '%Y%m%d') for d in E_value.forecast_df.Date]
        min_date = min(date_as_datetime_type).strftime('%Y-%m-%d')
        max_date = max(date_as_datetime_type).strftime('%Y-%m-%d')

        x_tick_values = [ x + ( bar_width * len(dict_of_forecasts) / 2 ) for x in np.arange(len(dict_of_forecasts))]
        E_ids = [ '#'+str(E_id) for E_id in E_ids ] #to make it clear that the x axis labels are not numeric
        ax.set_xticks(x_tick_values, E_ids)
        ax.yaxis_date()
        plt.title('Milestone Dates : ' + str(min_date) + ' -> ' + str(max_date))
        plt.savefig(output_path)
        matplotlib.pyplot.close()

    def plotSankeyDiagram(self, expense_forecast, output_path):
        income_memos = []
        expense_memos = []
        for index, row in expense_forecast.initial_budget_set.getBudgetItems().iterrows():
            relevant_memo_rule = expense_forecast.initial_memo_rule_set.findMatchingMemoRule(row.Memo, row.Priority).memo_rules[0]
            if relevant_memo_rule.account_from == 'Checking' and relevant_memo_rule.account_to == 'None':
                expense_memos.append(row.Memo)
            elif relevant_memo_rule.account_from == 'Credit' and relevant_memo_rule.account_to == 'None':
                expense_memos.append(row.Memo)
            elif relevant_memo_rule.account_from == 'None' and relevant_memo_rule.account_to == 'Checking':
                income_memos.append(row.Memo)

        total_income = 0
        total_expense = 0
        total_interest = 0
        income_node_dict = {}
        expense_node_dict = {}
        for index, row in expense_forecast.forecast_df.iterrows():
            memo_line_items = row.Memo.split(';')
            for memo_line_item in memo_line_items:
                memo_line_item = memo_line_item.strip()
                if memo_line_item == '':
                    continue
                # account_name_match = re.search('\((.*)-\$(.*)\)', memo_line_item)
                # account_name = account_name_match.group(1)
                payment_amount_match = re.search('\(.*-?\$(.*)\)', memo_line_item)
                amount = float(payment_amount_match.group(1))
                for income_memo in income_memos:
                    if income_memo in memo_line_item:
                        total_income += amount

                        if income_memo not in income_node_dict.keys():
                            income_node_dict[income_memo] = amount
                        else:
                            income_node_dict[income_memo] += amount

                for expense_memo in expense_memos:
                    if expense_memo in memo_line_item:
                        total_expense += amount

                        if expense_memo not in expense_node_dict.keys():
                            expense_node_dict[expense_memo] = amount
                        else:
                            expense_node_dict[expense_memo] += amount

                if 'cc interest' in memo_line_item:
                    total_interest += amount

        total_expense += total_interest
        total_remaining = total_income - total_expense

        index = 0
        #print('total income:' + str(total_income))
        for key, value in income_node_dict.items():
            # print((key, value))
            index += 1

        total_income_index = index
        index += 1

        total_expense_index = index
        index += 1

        #print('total expense:' + str(total_expense))
        for key, value in expense_node_dict.items():
            # print((key, value))
            index += 1

        interest_index = index
        index += 1

        remaining_index = index
        index += 1  # dont need this bc no more nodes but whatever

        income_color = '#42f542'
        expense_color = '#ecf542'

        source = []
        target = []
        values = []
        labels = []
        colors = []
        index = 0
        for key, value in income_node_dict.items():
            labels.append(key)
            source.append(index)
            target.append(total_income_index)
            values.append(value)
            colors.append(income_color)
            index += 1

        source.append(total_income_index)
        target.append(total_expense_index)
        values.append(total_expense)
        labels.append('Total Income')
        colors.append(expense_color)
        index += 1

        source.append(total_income_index)
        target.append(remaining_index)
        values.append(total_remaining)
        labels.append('Total Expense')
        colors.append(income_color)
        index += 1

        for key, value in expense_node_dict.items():
            labels.append(key)
            source.append(total_expense_index)
            target.append(index)
            values.append(value)
            colors.append(expense_color)
            index += 1

        source.append(total_expense_index)
        target.append(interest_index)
        values.append(total_interest)
        labels.append('Total Interest')
        colors.append(expense_color)
        index += 1

        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=labels,
                color='grey'
            ),
            link=dict(
                source=source,  # indices correspond to labels, eg A1, A2, A1, B1, ...
                target=target,
                value=values,
                color=colors
            ))])

        fig.update_layout(title_text=expense_forecast.scenario_name, font_size=10)

        fig.write_image(output_path)
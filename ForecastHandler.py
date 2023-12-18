import copy
import os
import MilestoneSet
import ExpenseForecast, datetime
from log_methods import log_in_color
import BudgetSet
import json
import pandas as pd
from multiprocessing import Pool
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


import logging

log_format = '%(asctime)s - %(levelname)-8s - %(message)s'
l_formatter = logging.Formatter(log_format)

l_stream = logging.StreamHandler()
l_stream.setFormatter(l_formatter)
l_stream.setLevel(logging.INFO)

l_file = logging.FileHandler('ForecastHandler__'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.log')
l_file.setFormatter(l_formatter)
l_file.setLevel(logging.INFO)


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False
logger.handlers.clear()
logger.addHandler(l_stream)
logger.addHandler(l_file)



class ForecastHandler:

    def __init__(self):
        pass

    def initialize_from_excel_file(self,path_to_excel_file):
        AccountSet_df = pd.read_excel(path_to_excel_file, sheet_name='AccountSet')
        BudgetSet_df = pd.read_excel(path_to_excel_file, sheet_name='BudgetSet')
        MemoRuleSet_df = pd.read_excel(path_to_excel_file, sheet_name='MemoRuleSet')
        ChooseOneSet_df = pd.read_excel(path_to_excel_file, sheet_name='ChooseOneSet')

        AccountMilestones_df = pd.read_excel(path_to_excel_file, sheet_name='AccountMilestones')
        MemoMilestones_df = pd.read_excel(path_to_excel_file, sheet_name='MemoMilestones')
        CompositeMilestones_df = pd.read_excel(path_to_excel_file, sheet_name='CompositeMilestones')

        config_df = pd.read_excel(path_to_excel_file, sheet_name='config')
        start_date_YYYYMMDD = config_df.Start_Date_YYYYMMDD.iat[0]
        end_date_YYYYMMDD = config_df.End_Date_YYYYMMDD.iat[0]
        output_directory = config_df.Output_Directory.iat[0]

        A = AccountSet.AccountSet([])
        M = MemoRuleSet.MemoRuleSet([])

        for account_index, account_row in AccountSet_df.iterrows():
            A.createAccount(account_row.Account_Name,
                            account_row.Balance,
                            account_row.Min_Balance,
                            account_row.Max_Balance,
                            account_row.Account_Type,
                            billing_start_date_YYYYMMDD=account_row.Billing_Start_Date_YYYYMMDD,
                            interest_type=account_row.Interest_Type,
                            apr=account_row.APR,
                            interest_cadence=account_row.Interest_Cadence,
                            minimum_payment=account_row.Minimum_Payment,
                            previous_statement_balance=account_row.Previous_Statement_Balance,
                            principal_balance=account_row.Principal_Balance,
                            accrued_interest=account_row.Accrued_Interest)

        for memorule_index, memorule_row in MemoRuleSet_df.iterrows():
            M.addMemoRule(memorule_row.Memo_Regex,memorule_row.Account_From,memorule_row.Account_To,memorule_row.Transaction_Priority)

        # number_of_combinations = 1
        self.choose_one_set_df = ChooseOneSet_df
        set_ids = ChooseOneSet_df.Choose_One_Set_Id.unique()
        set_ids.sort()
        # for set_id in set_ids:
        #     all_options_for_set = ChooseOneSet_df[ChooseOneSet_df.Choose_One_Set_Id == set_id,:]
        #     number_of_combinations = number_of_combinations * all_options_for_set.shape[0]
        master_list = ['']
        master_list_option_ids = ['']
        for set_id in set_ids:
            all_options_for_set = ChooseOneSet_df.loc[ChooseOneSet_df.Choose_One_Set_Id == set_id]
            current_list=[]
            current_list_option_ids = []
            for option_index, option_row in all_options_for_set.iterrows():
                for l in master_list:
                    current_list.append(l + ';' + option_row.Memo_Regex_List)

                for l in master_list_option_ids:
                    current_list_option_ids.append(l+str(set_id)+'='+str(option_row.Option_Id)+' ')

            master_list = current_list
            master_list_option_ids = current_list_option_ids


        budget_set_list = []
        for l in master_list:
            B = BudgetSet.BudgetSet([])
            for budget_item_index, budget_item_row in BudgetSet_df.iterrows():
                for memo_regex in l.split(';'):
                    if memo_regex == '':
                        continue

                    if re.search(memo_regex,budget_item_row.Memo) is not None:
                        #print(memo_regex + ' ?= ' + str(budget_item_row.Memo)+" YES")
                        B.addBudgetItem(start_date_YYYYMMDD=budget_item_row.Start_Date,
                         end_date_YYYYMMDD=budget_item_row.End_Date,
                         priority=budget_item_row.Priority,
                         cadence=budget_item_row.Cadence,
                         amount=budget_item_row.Amount,
                         memo=budget_item_row.Memo,
                         deferrable=budget_item_row.Deferrable,
                         partial_payment_allowed=budget_item_row.Partial_Payment_Allowed
                                        )

                        break
                    else:
                        pass
                        #print(memo_regex + ' ?= ' + str(budget_item_row.Memo)+" NO")
            budget_set_list.append(B)

        account_milestones__list = []
        for index, row in AccountMilestones_df.iterrows():
            account_milestones__list.append(AccountMilestone.AccountMilestone(row.Milestone_Name,row.Account_Name,row.Min_Balance,row.Max_Balance))

        memo_milestones__list = []
        for index, row in MemoMilestones_df.iterrows():
            memo_milestones__list.append(MemoMilestone.MemoMilestone(row.Milestone_Name,row.Memo_Regex))

        composite_milestones__list = []
        for index, row in CompositeMilestones_df.iterrows():
            milestone_names__list = []
            for i in range(1,CompositeMilestones_df.shape[1]):
                milestone_names__list.append(row.iat[i])

            composite_milestones__list.append(CompositeMilestone.CompositeMilestone(row.Milestone_Name,account_milestones__list, memo_milestones__list, milestone_names__list))

        milestone_set = MilestoneSet.MilestoneSet(A,B,account_milestones__list,memo_milestones__list,composite_milestones__list)
        self.account_milestones__list = milestone_set.account_milestones__list
        self.memo_milestones__list = milestone_set.memo_milestones__list
        self.composite_milestones__list = milestone_set.composite_milestones__list

        self.initial_account_set = copy.deepcopy(A)
        self.budget_set_list = budget_set_list
        self.initial_memo_rule_set = M
        self.start_date_YYYYMMDD = start_date_YYYYMMDD
        self.end_date_YYYYMMDD = end_date_YYYYMMDD

        self.master_list_option_ids = master_list_option_ids
        self.output_directory = output_directory

        self.config_df = config_df #todo store vars instead

        budget_set_list = self.budget_set_list
        start_date_YYYYMMDD = self.start_date_YYYYMMDD
        end_date_YYYYMMDD = self.end_date_YYYYMMDD
        A = self.initial_account_set
        M = self.initial_memo_rule_set

        # program_start = datetime.datetime.now()
        # scenario_index = 0
        number_of_returned_forecasts = len(budget_set_list)
        EF_pre_run = []
        for B in budget_set_list:
            try:
                E = ExpenseForecast.ExpenseForecast(account_set=copy.deepcopy(A),
                                                    budget_set=B,
                                                    memo_rule_set=M,
                                                    start_date_YYYYMMDD=start_date_YYYYMMDD,
                                                    end_date_YYYYMMDD=end_date_YYYYMMDD,
                                                    milestone_set=milestone_set)
                #print(E)
                # E.runForecast()
                EF_pre_run.append(E)
            except Exception as e:

                print(e)

        self.initialized_forecasts = EF_pre_run

    def read_results_from_disk(self):

        E_objs = []
        forecast_ids = self.get_individual_forecast_ids()
        for forecast_id in forecast_ids:
            forecast_json_file_name_regex_pattern = 'Forecast__' + str(forecast_id) + '__[0-9]{4}_[0-9]{2}_[0-9]{2}__[0-9]{2}_[0-9]{2}_[0-9]{2}\.json'
            for f in os.listdir(self.output_directory):
                if re.search(forecast_json_file_name_regex_pattern,f) is not None:
                    E = ExpenseForecast.initialize_from_json_file(f)
                    E_objs.append(E)

        #assert that all initial accounts sets matched, then set
        all_initial_account_set_hashes = [ hashlib.sha1(E.initial_account_set.getAccounts().to_string().encode("utf-8")).hexdigest() for E in E_objs ]
        logger.info('all_initial_account_set_hashes:')
        logger.info(all_initial_account_set_hashes)
        assert min(all_initial_account_set_hashes) == max(all_initial_account_set_hashes)
        assert len(all_initial_account_set_hashes) == len(E_objs)
        self.initial_account_set = E_objs[0].initial_account_set

        #assert that all memo rules match, then set
        all_initial_memo_set_hashes = [ hash(E.initial_memo_rule_set.getMemoRules().to_string()) for E in E_objs ]
        assert min(all_initial_memo_set_hashes) == max(all_initial_memo_set_hashes)
        assert len(all_initial_memo_set_hashes) == len(E_objs)
        self.initial_memo_rule_set = E_objs[0].initial_memo_rule_set

        all_start_dates = [ E.start_date for E in E_objs ]
        assert min(all_start_dates) == max(all_start_dates)
        assert len(all_start_dates) == len(E_objs)
        self.start_date = E_objs[0].start_date

        all_end_dates = [E.end_date for E in E_objs]
        assert min(all_end_dates) == max(all_end_dates)
        assert len(all_end_dates) == len(E_objs)
        self.end_date = E_objs[0].end_date

        #this is not an attribute of ExpenseForecast
        # all_output_directories = [ hash(E.output_directory) for E in E_objs]
        # assert min(all_output_directories) == max(all_output_directories)
        # assert len(all_output_directories) == len(E_objs)
        # self.output_directory = E_objs[0].output_directory

        #we regenerate option ids because they depend on the ChooseOneSet, and not the individual forecast.
        #That is, Forecast #N could have the same settings, but different option ids based on what it is being compared to.
        #Even just moving around the rows in the input excel would change the option ids.  (this would change the unique id as well tho)
        number_of_combinations = 1

        set_ids = self.choose_one_set_df.Choose_One_Set_Id.unique()
        set_ids.sort()
        for set_id in set_ids:
            all_options_for_set = self.choose_one_set_df.loc[self.choose_one_set_df.Choose_One_Set_Id == set_id,:]
            number_of_combinations = number_of_combinations * all_options_for_set.shape[0]
        master_list = ['']
        master_list_option_ids = ['']
        for set_id in set_ids:
            all_options_for_set = self.choose_one_set_df.loc[self.choose_one_set_df.Choose_One_Set_Id == set_id]
            current_list = []
            current_list_option_ids = []
            for option_index, option_row in all_options_for_set.iterrows():
                for l in master_list:
                    current_list.append(l + ';' + option_row.Memo_Regex_List)

                for l in master_list_option_ids:
                    current_list_option_ids.append(l + str(set_id) + '=' + str(option_row.Option_Id) + ' ')

            master_list = current_list
            master_list_option_ids = current_list_option_ids

        assert len(master_list_option_ids) == len(E_objs)
        self.master_list_option_ids = master_list_option_ids

        all_account_milestone_df_hashes = [ hash(E.account_milestones_df.to_string()) for E in E_objs ]
        assert min(all_account_milestone_df_hashes) == max(all_account_milestone_df_hashes) #error here means not all account milestones were the same
        assert len(all_account_milestone_df_hashes) == len(E_objs) #error here means one of the input forecasts did not have an account_milestone_df
        self.account_milestones_df = E_objs[0].account_milestones_df

        all_memo_milestone_df_hashes = [ hash(E.memo_milestones_df.to_string()) for E in E_objs ]
        assert min(all_memo_milestone_df_hashes) == max(all_memo_milestone_df_hashes) #error here means not all memo milestones were the same
        assert len(all_memo_milestone_df_hashes) == len(E_objs) #error here means one of the input forecasts did not have a memo_milestone_df
        self.memo_milestones_df = E_objs[0].memo_milestones_df

        all_composite_milestone_df_hashes = [ hash(E.composite_milestones_df.to_string()) for E in E_objs ]
        assert min(all_composite_milestone_df_hashes) == max(all_composite_milestone_df_hashes) #error here means not all the composite milestones were the same
        assert len(all_composite_milestone_df_hashes) == len(E_objs) #error here means one of the input forecasts did not have a composite_milestone_df
        self.composite_milestones_df = E_objs[0].composite_milestones_df


    def get_individual_forecast_ids(self):
        return [ E.unique_id for E in self.initialized_forecasts ]

    def run_forecasts(self):

        number_of_returned_forecasts = len(self.budget_set_list)

        EF_pre_run = self.initialized_forecasts

        program_start = datetime.datetime.now()
        scenario_index = 0
        for E in EF_pre_run:
            loop_start = datetime.datetime.now()

            logger.info('Starting simulation scenario ' + str(scenario_index + 1) + ' / ' + str(number_of_returned_forecasts) + ' #' + E.unique_id)
            logger.info('Option ids: ' + self.master_list_option_ids[scenario_index])
            E.runForecast()

            loop_finish = datetime.datetime.now()

            loop_delta = loop_finish - loop_start
            time_since_started = loop_finish - program_start

            average_time_per_loop = time_since_started.seconds / (scenario_index + 1)
            loops_remaining = number_of_returned_forecasts - (scenario_index + 1)
            ETC = loop_finish + datetime.timedelta(seconds=average_time_per_loop * loops_remaining)
            progress_string = 'Finished in ' + str(loop_delta.seconds) + ' seconds. ETC: ' + str(ETC.strftime('%Y-%m-%d %H:%M:%S'))

            logger.info(progress_string)

            scenario_index += 1




        # choose_one_sets__list = []
        # for i in set_ids:
        #     choose_one_sets__list.append([])

        # #Scenario_Name	Choose_One_Set_Id	Option_Name	Option_Id	Memo_Regex_List (semicolon delimited)
        # for chooseoneset_index, chooseoneset_row in ChooseOneSet_df.iterrows():
        #     pass
        #     #choose_one_sets__dict[chooseoneset_row.Choose_One_Set_Id].append(chooseoneset_row.Memo_Regex_List)

    def generateCompareTwoForecastsHTMLReport(self,E1, E2, output_dir='./'):

        assert E1.start_date == E2.start_date
        assert E1.end_date == E2.end_date

        start_date = E1.start_date.strftime('%Y-%m-%d')
        end_date = E1.end_date.strftime('%Y-%m-%d')

        report_1_id = E1.unique_id
        report_2_id = E2.unique_id

        report_1_start_ts__datetime = datetime.datetime.strptime(E1.start_ts, '%Y_%m_%d__%H_%M_%S')
        report_1_end_ts__datetime = datetime.datetime.strptime(E1.end_ts, '%Y_%m_%d__%H_%M_%S')
        report_2_start_ts__datetime = datetime.datetime.strptime(E2.start_ts, '%Y_%m_%d__%H_%M_%S')
        report_2_end_ts__datetime = datetime.datetime.strptime(E2.end_ts, '%Y_%m_%d__%H_%M_%S')
        report_1_simulation_time_elapsed = report_1_end_ts__datetime - report_1_start_ts__datetime
        report_2_simulation_time_elapsed = report_2_end_ts__datetime - report_2_start_ts__datetime

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

        assert E1.forecast_df.shape[0] == E2.forecast_df.shape[0]
        num_days = E1.forecast_df.shape[0]

        report_1_initial_networth = E1.forecast_df.head(1)['NetWorth'].iat[0]
        report_1_final_networth = E1.forecast_df.tail(1)['NetWorth'].iat[0]
        report_1_networth_delta = report_1_final_networth - report_1_initial_networth
        report_1_avg_networth_change = round(report_1_networth_delta / float(E1.forecast_df.shape[0]), 2)

        if report_1_networth_delta >= 0:
            report_1_networth_rose_or_fell = "rose"
        else:
            report_1_networth_rose_or_fell = "fell"

        report_2_initial_networth = E2.forecast_df.head(1)['NetWorth'].iat[0]
        report_2_final_networth = E2.forecast_df.tail(1)['NetWorth'].iat[0]
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

        report_1_initial_loan_total = round(E1.forecast_df.head(1).LoanTotal.iat[0], 2)
        report_1_final_loan_total = round(E1.forecast_df.tail(1).LoanTotal.iat[0], 2)
        report_1_loan_delta = round(report_1_final_loan_total - report_1_initial_loan_total, 2)
        report_1_initial_cc_debt_total = round(E1.forecast_df.head(1).CCDebtTotal.iat[0], 2)
        report_1_final_cc_debt_total = round(E1.forecast_df.tail(1).CCDebtTotal.iat[0], 2)
        report_1_cc_debt_delta = round(report_1_final_cc_debt_total - report_1_initial_cc_debt_total, 2)
        report_1_initial_liquid_total = round(E1.forecast_df.head(1).LiquidTotal.iat[0], 2)
        report_1_final_liquid_total = round(E1.forecast_df.tail(1).LiquidTotal.iat[0], 2)
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

        report_2_initial_loan_total = round(E2.forecast_df.head(1).LoanTotal.iat[0], 2)
        report_2_final_loan_total = round(E2.forecast_df.tail(1).LoanTotal.iat[0], 2)
        report_2_loan_delta = round(report_2_final_loan_total - report_2_initial_loan_total, 2)
        report_2_initial_cc_debt_total = round(E2.forecast_df.head(1).CCDebtTotal.iat[0], 2)
        report_2_final_cc_debt_total = round(E2.forecast_df.tail(1).CCDebtTotal.iat[0], 2)
        report_2_cc_debt_delta = round(report_2_final_cc_debt_total - report_2_initial_cc_debt_total, 2)
        report_2_initial_liquid_total = round(E2.forecast_df.head(1).LiquidTotal.iat[0], 2)
        report_2_final_liquid_total = round(E2.forecast_df.tail(1).LiquidTotal.iat[0], 2)
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

            #todo dollar signs and comma formating m
            line=""" For Forecast 1 #"""+str(E1.unique_id)+""", """+aname+""" began at """+str(f"${float(E1_initial_value):,}")+""" and  """+E1_rose_or_fell+""" to """+str(f"${float(E1_final_value):,}")+""" over  """+str(num_days)+""", averaging  """+str(f"${float(E1_daily_average):,}")+"""  per day. <br>
            For Forecast 2 #"""+str(E2.unique_id)+""", """+aname+""" began at """+str(f"${float(E2_initial_value):,}")+""" and  """+E2_rose_or_fell+""" to """+str(f"${float(E2_final_value):,}")+""" over  """+str(num_days)+""", averaging  """+str(f"${float(E2_daily_average):,}")+"""  per day. <br><br>   
            """ + delta_string + """ <br><br><br>
            """
            all_text+=line





        report_1_networth_line_plot_path = output_dir + report_1_id + '_networth_line_plot.png'
        report_1_accounttype_line_plot_path = output_dir + report_1_id + '_accounttype_line_plot_plot.png'
        report_1_all_line_plot_path = output_dir + report_1_id + '_all_line_plot.png'

        report_2_networth_line_plot_path = output_dir + report_2_id + '_networth_line_plot.png'
        report_2_accounttype_line_plot_path = output_dir + report_2_id + '_accounttype_line_plot_plot.png'
        report_2_all_line_plot_path = output_dir + report_2_id + '_all_line_plot.png'

        account_type_comparison_plot_path = output_dir + report_1_id + '_vs_' + report_2_id + '_account_type_comparison_plot.png'
        networth_comparison_plot_path = output_dir + report_1_id + '_vs_' + report_2_id + '_networth_comparison_plot.png'
        all_comparison_plot_path = output_dir + report_1_id + '_vs_' + report_2_id + '_all_comparison_plot.png'

        E1.plotAll(report_1_all_line_plot_path)
        E1.plotNetWorth(report_1_networth_line_plot_path)
        E1.plotAccountTypeTotals(report_1_accounttype_line_plot_path)

        E2.plotAll(report_2_all_line_plot_path)
        E2.plotNetWorth(report_2_networth_line_plot_path)
        E2.plotAccountTypeTotals(report_2_accounttype_line_plot_path)

        self.plotAccountTypeComparison(E1,E2,account_type_comparison_plot_path)
        self.plotNetWorthComparison(E1, E2, networth_comparison_plot_path)
        self.plotAllComparison(E1, E2, all_comparison_plot_path)



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
                <p>""" + start_date + """ to """ + end_date + """</p>

                <!-- Tab links -->
                <div class="tab">
                  <button class="tablinks active" onclick="openTab(event, 'InputData')">Input Data</button>
                  <button class="tablinks" onclick="openTab(event, 'NetWorth')">Net Worth</button>
                  <button class="tablinks" onclick="openTab(event, 'NetGainLoss')">Net Gain/Loss</button>
                  <button class="tablinks" onclick="openTab(event, 'AccountType')">Account Type</button>
                  <button class="tablinks" onclick="openTab(event, 'Interest')">Interest</button>
                  <button class="tablinks" onclick="openTab(event, 'Milestone')">Milestone</button>
                  <button class="tablinks" onclick="openTab(event, 'All')">All</button>
                  <button class="tablinks" onclick="openTab(event, 'OutputData')">Output Data</button>
                </div>

                <!-- Tab content -->
                <div id="InputData" class="tabcontent">
                  <h3>Input Data</h3>
                  <h3>Accounts</h3>
                  <p>""" + account_text + """</p>
                  <h3>Budget Items</h3>
                  <p>""" + budget_set_text + """</p>
                  <h3>Memo Rules</h3>
                  <p>""" + memo_rule_text + """</p>
                </div>

                <div id="NetWorth" class="tabcontent">
                  <h3>NetWorth</h3>
                  <p>""" + networth_text + """</p>
                  <img src=\"""" + networth_comparison_plot_path + """\">
                  <img src=\"""" + report_1_networth_line_plot_path + """\">
                  <img src=\"""" + report_2_networth_line_plot_path + """\">
                </div>

                <div id="NetGainLoss" class="tabcontent">
                  <h3>NetGainLoss</h3>
                  <p>NetGainLoss text.</p>
                  <img src=\"""" + 'netgain_line_plot_path' + """\">
                </div>

                <div id="AccountType" class="tabcontent">
                  <h3>AccountType</h3>
                  <p>""" + account_type_text + """</p>
                  <img src=\"""" + account_type_comparison_plot_path + """\">
                  <img src=\"""" + report_1_accounttype_line_plot_path + """\">
                  <img src=\"""" + report_2_accounttype_line_plot_path + """\">
                </div>

                <div id="Interest" class="tabcontent">
                  <h3>Interest</h3>
                  <p>Interest text.</p>
                  <img src=\"""" + 'interest_line_plot_path' + """\">
                </div>

                <div id="Milestone" class="tabcontent">
                  <h3>Milestone</h3>
                  <p>Milestone text.</p>
                  <img src=\"""" + 'milestone_line_plot_path' + """\">
                </div>

                <div id="All" class="tabcontent">
                  <h3>All</h3>
                  <p>"""+all_text+"""</p>
                  <img src=\"""" + all_comparison_plot_path + """\">
                  <img src=\"""" + report_1_all_line_plot_path + """\">
                  <img src=\"""" + report_2_all_line_plot_path + """\">
                </div>
                
                <div id="OutputData" class="tabcontent">
                  <h3>Output Data</h3>
                  <p>""" + summary_text + """</p>
                  <p>The visualized data are below:</p>
                  <h4>Forecast 1 #"""+str(E1.unique_id)+""":</h4>
                  """ + E1.forecast_df.to_html() + """
                  <h4>Forecast 2 #"""+str(E2.unique_id)+""":</h4>
                  """ + E2.forecast_df.to_html() + """
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

                //having this here leaves the Summary tab open when the page first loads
                document.getElementById("InputData").style.display = "block";
                </script>

                </body>
                </html>

                """

        with open('out.html', 'w') as f:
            f.write(html_body)

    def generateHTMLReport(self,E,output_dir='./'):

        start_date = E.start_date.strftime('%Y-%m-%d')
        end_date = E.end_date.strftime('%Y-%m-%d')

        report_id = E.unique_id

        start_ts__datetime = datetime.datetime.strptime(E.start_ts,'%Y_%m_%d__%H_%M_%S')
        end_ts__datetime = datetime.datetime.strptime(E.end_ts, '%Y_%m_%d__%H_%M_%S')
        simulation_time_elapsed = end_ts__datetime - start_ts__datetime

        #todo add a comment about whether the simulation was able to make it to the end or not.
        summary_text = """
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

        initial_networth=E.forecast_df.head(1)['NetWorth'].iat[0]
        final_networth=E.forecast_df.tail(1)['NetWorth'].iat[0]
        networth_delta=final_networth-initial_networth
        num_days = E.forecast_df.shape[0]
        avg_networth_change=round(networth_delta/float(E.forecast_df.shape[0]),2)

        if networth_delta >= 0:
            rose_or_fell="rose"
        else:
            rose_or_fell="fell"

        networth_text = """
        Net Worth began at """+str(f"${float(initial_networth):,}")+""" and """+rose_or_fell+""" to """+str(f"${float(final_networth):,}")+""" over """+str(f"{float(num_days):,.0f}")+""" days, averaging """+f"${float(avg_networth_change):,}"+""" per day.
        """

        initial_loan_total = round(E.forecast_df.head(1).LoanTotal.iat[0],2)
        final_loan_total = round(E.forecast_df.tail(1).LoanTotal.iat[0],2)
        loan_delta = round(final_loan_total - initial_loan_total,2)
        initial_cc_debt_total = round(E.forecast_df.head(1).CCDebtTotal.iat[0],2)
        final_cc_debt_total = round(E.forecast_df.tail(1).CCDebtTotal.iat[0],2)
        cc_debt_delta = round(final_cc_debt_total - initial_cc_debt_total,2)
        initial_liquid_total = round(E.forecast_df.head(1).LiquidTotal.iat[0],2)
        final_liquid_total = round(E.forecast_df.tail(1).LiquidTotal.iat[0],2)
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

        networth_line_plot_path = output_dir + report_id + '_networth_line_plot.png'
        netgain_line_plot_path = output_dir + report_id + '_netgain_line_plot.png' #todo
        accounttype_line_plot_path = output_dir + report_id + '_accounttype_line_plot_plot.png'
        interest_line_plot_path = output_dir + report_id + '_interest_line_plot_plot.png' #todo
        milestone_line_plot_path = output_dir + report_id + '_milestone_line_plot.png' #todo
        all_line_plot_path = output_dir + report_id + '_all_line_plot.png'

        E.plotAll(all_line_plot_path)
        E.plotNetWorth(networth_line_plot_path)
        E.plotAccountTypeTotals(accounttype_line_plot_path)

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
        <h1>Expense Forecast Report #""" + str(report_id) + """</h1>
        <p>"""+start_date+""" to """+end_date+"""</p>

        <!-- Tab links -->
        <div class="tab">
          <button class="tablinks active" onclick="openTab(event, 'Summary')">Summary</button>
          <button class="tablinks" onclick="openTab(event, 'NetWorth')">Net Worth</button>
          <button class="tablinks" onclick="openTab(event, 'NetGainLoss')">Net Gain/Loss</button>
          <button class="tablinks" onclick="openTab(event, 'AccountType')">Account Type</button>
          <button class="tablinks" onclick="openTab(event, 'Interest')">Interest</button>
          <button class="tablinks" onclick="openTab(event, 'Milestone')">Milestone</button>
          <button class="tablinks" onclick="openTab(event, 'All')">All</button>
        </div>

        <!-- Tab content -->
        <div id="Summary" class="tabcontent">
          <h3>Summary</h3>
          <p>"""+summary_text+"""</p>
          <h3>Accounts</h3>
          <p>"""+account_text+"""</p>
          <h3>Budget Items</h3>
          <p>"""+budget_set_text+"""</p>
          <h3>Memo Rules</h3>
          <p>"""+memo_rule_text+"""</p>
        </div>

        <div id="NetWorth" class="tabcontent">
          <h3>NetWorth</h3>
          <p>"""+networth_text+"""</p>
          <img src=\""""+networth_line_plot_path+"""\">
        </div>

        <div id="NetGainLoss" class="tabcontent">
          <h3>NetGainLoss</h3>
          <p>NetGainLoss text.</p>
          <img src=\""""+netgain_line_plot_path+"""\">
        </div>

        <div id="AccountType" class="tabcontent">
          <h3>AccountType</h3>
          <p>"""+account_type_text+"""</p>
          <img src=\""""+accounttype_line_plot_path+"""\">
        </div>

        <div id="Interest" class="tabcontent">
          <h3>Interest</h3>
          <p>Interest text.</p>
          <img src=\""""+interest_line_plot_path+"""\">
        </div>
        
        <div id="Milestone" class="tabcontent">
          <h3>Milestone</h3>
          <p>Milestone text.</p>
          <img src=\""""+milestone_line_plot_path+"""\">
        </div>

        <div id="All" class="tabcontent">
          <h3>All</h3>
          <p>All text.</p>
          <img src=\""""+all_line_plot_path+"""\">
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
        
        //having this here leaves the Summary tab open when the page first loads
        document.getElementById("Summary").style.display = "block";
        </script>

        </body>
        </html>

        """

        with open('out.html','w') as f:
            f.write(html_body)

    def getRuntimeEstimate(self,AccountSet,BudgetSet, MemoRuleSet, start_date_YYYYMMDD, end_date_YYYYMMDD):
        log_in_color('green','debug','getRuntimeEstimate(start_date_YYYYMMDD='+str(start_date_YYYYMMDD)+',end_date_YYYYMMDD='+str(end_date_YYYYMMDD)+')')
        log_in_color('green', 'debug', 'Length of forecast:')
        log_in_color('green', 'debug', 'Non-deferrable, partial-payment not allowed:')
        log_in_color('green', 'debug', 'Partial-payment allowed:')
        log_in_color('green', 'debug', 'Deferrable:')
        #number of days * 7.5 seconds
        # for each non-deferrable, partial-payment-not-allowed proposed item, add (end_date - date) * 7.5 seconds
        # for each partial payment allowed item, add [ (end_date - date) * 7.5 seconds, (end_date - date) * 7.5 seconds * 2 ] to get an range time estimate
        # for each deferrable payment, add [ (end_date - date) * 7.5 seconds, ( 1 + FLOOR( (end_date - date) / 14) )^2 / 2 * 7.5 seconds ]

        raise NotImplementedError

    def calculateMultipleChooseOne(self,AccountSet,Core_BudgetSet, MemoRuleSet, start_date_YYYYMMDD, end_date_YYYYMMDD, list_of_lists_of_budget_sets):

        #the number of returned forecasts will be equal to the product of the lengths of the lists in list_of_lists_of_budget_sets
        length_of_lists = [ len(x) for x in list_of_lists_of_budget_sets]
        number_of_returned_forecasts = 1
        for l in length_of_lists:
            number_of_returned_forecasts = number_of_returned_forecasts * l

        #at this point, our return variable is the correct size, and has an empty list for each budget set
        master_list = [Core_BudgetSet.budget_items] #this is a list of lists of budget items
        for list_of_budget_sets in list_of_lists_of_budget_sets:
            current_list = []

            for budget_set in list_of_budget_sets:
                for master_budget_item_list in master_list:
                    current_list.append(budget_set.budget_items + master_budget_item_list)

            master_list = current_list

        program_start = datetime.datetime.now()
        scenario_index = 0
        for budget_set in master_list:
            loop_start = datetime.datetime.now()
            B = BudgetSet.BudgetSet(budget_set)
            # print('B:')
            # print(B.getBudgetItems().to_string())
            logger.info('Starting simulation scenario '+str(scenario_index))
            try:
                E = ExpenseForecast.ExpenseForecast(account_set=copy.deepcopy(AccountSet),
                                                        budget_set=B,
                                                        memo_rule_set=MemoRuleSet,
                                                        start_date_YYYYMMDD=start_date_YYYYMMDD,
                                                        end_date_YYYYMMDD=end_date_YYYYMMDD)
            except:
                logger.info('Simulation scenario '+str(scenario_index)+' failed')

            loop_finish = datetime.datetime.now()

            loop_delta = loop_finish - loop_start
            time_since_started = loop_finish - program_start

            average_time_per_loop = time_since_started.seconds / (scenario_index + 1)
            loops_remaining = number_of_returned_forecasts - (scenario_index + 1)
            ETC = loop_finish + datetime.timedelta(seconds=average_time_per_loop*loops_remaining)
            progress_string = 'Finished in '+str(loop_delta.seconds)+' seconds. ETC: '+str(ETC.strftime('%Y-%m-%d %H:%M:%S'))

            logger.info(progress_string)

            scenario_index += 1

    #
    # def run_forecast_from_excel_inputs(self,path_to_excel):
    #
    #     if not self.input_excel_values_are_valid(str(path_to_excel)):
    #         raise ValueError("There was a problem with the excel sheet at this path: "+str(path_to_excel))
    #
    #     raise NotImplementedError
    #
    # def input_excel_values_are_valid(self,path_to_excel):
    #     raise NotImplementedError


    def plotAccountTypeComparison(self,E1,E2,output_path):
        """
        Single-line description

        Multiple line description.


        :param E1:
        :param E2:
        :param output_path:
        :return:
        """
        figure(figsize=(14, 6), dpi=80)
        E1_relevant_columns_sel_vec = (E1.forecast_df.columns == 'Date') | (E1.forecast_df.columns == 'LoanTotal') | (E1.forecast_df.columns == 'CCDebtTotal') | (E1.forecast_df.columns == 'LiquidTotal')
        E2_relevant_columns_sel_vec = (E2.forecast_df.columns == 'Date') | (E2.forecast_df.columns == 'LoanTotal') | (E2.forecast_df.columns == 'CCDebtTotal') | (E2.forecast_df.columns == 'LiquidTotal')
        E1_relevant_df = E1.forecast_df.iloc[:, E1_relevant_columns_sel_vec]
        E2_relevant_df = E2.forecast_df.iloc[:, E2_relevant_columns_sel_vec]

        relevant_df = pd.merge(E1_relevant_df,E2_relevant_df,on=["Date"], suffixes=('_1','_2'))

        # this plot always has 6 lines, so we can make the plot more clear by using warm colors for Forecast 1 and cool colors for Forecast 2
        relevant_df = relevant_df[['Date','LoanTotal_1','CCDebtTotal_1','LiquidTotal_1','LoanTotal_2','CCDebtTotal_2','LiquidTotal_2']]
        color_array = ['crimson','orangered','fuchsia','chartreuse','darkgreen','olive']

        for i in range(1, relevant_df.shape[1]):
            plt.plot(relevant_df['Date'], relevant_df.iloc[:, i], label=relevant_df.columns[i],color=color_array[i-1])

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

        min_date = min(E1.forecast_df.Date).strftime('%Y-%m-%d')
        max_date = max(E1.forecast_df.Date).strftime('%Y-%m-%d')
        plt.title('Forecast 1 #' + E1.unique_id + ' vs. Forecast 2 #'+E2.unique_id+': ' + str(min_date) + ' -> ' + str(max_date))
        plt.savefig(output_path)

    def plotNetWorthComparison(self, E1, E2, output_path):
        """
        Single-line description

        Multiple line description.


        :param E1:
        :param E2:
        :param output_path:
        :return:
        """
        figure(figsize=(14, 6), dpi=80)
        E1_relevant_columns_sel_vec = (E1.forecast_df.columns == 'Date') | (E1.forecast_df.columns == 'NetWorth')
        E2_relevant_columns_sel_vec = (E2.forecast_df.columns == 'Date') | (E2.forecast_df.columns == 'NetWorth')
        E1_relevant_df = E1.forecast_df.iloc[:, E1_relevant_columns_sel_vec]
        E2_relevant_df = E2.forecast_df.iloc[:, E2_relevant_columns_sel_vec]

        relevant_df = pd.merge(E1_relevant_df, E2_relevant_df, on=["Date"], suffixes=('_1', '_2'))

        # this plot always has 6 lines, so we can make the plot more clear by using warm colors for Forecast 1 and cool colors for Forecast 2
        relevant_df = relevant_df[['Date', 'NetWorth_1', 'NetWorth_2']]
        color_array = ['fuchsia', 'olive']

        for i in range(1, relevant_df.shape[1]):
            plt.plot(relevant_df['Date'], relevant_df.iloc[:, i], label=relevant_df.columns[i], color=color_array[i - 1])

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

        min_date = min(E1.forecast_df.Date).strftime('%Y-%m-%d')
        max_date = max(E1.forecast_df.Date).strftime('%Y-%m-%d')
        plt.title('Forecast 1 #' + E1.unique_id + ' vs. Forecast 2 #' + E2.unique_id + ': ' + str(min_date) + ' -> ' + str(max_date))
        plt.savefig(output_path)

    def plotAllComparison(self, E1, E2, output_path):
        """
        Writes to file a plot of all accounts.

        Multiple line description.


        :param forecast_df:
        :param output_path:
        :return:
        """
        figure(figsize=(14, 6), dpi=80)

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

        for i in range(1, relevant_df.shape[1] - 1):
            plt.plot(relevant_df['Date'], relevant_df.iloc[:, i], label=relevant_df.columns[i])

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

        min_date = min(E1.forecast_df.Date).strftime('%Y-%m-%d')
        max_date = max(E1.forecast_df.Date).strftime('%Y-%m-%d')
        plt.title('Forecast 1 #'+E1.unique_id+' vs. Forecast 2 #'+E2.unique_id+': ' + str(min_date) + ' -> ' + str(max_date))
        plt.savefig(output_path)
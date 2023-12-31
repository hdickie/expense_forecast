import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
import datetime
import re
import copy
import json
import AccountMilestone
import CompositeMilestone
import MemoMilestone
import BudgetItem
import BudgetSet
import AccountSet
import MemoRuleSet
import hashlib
import MilestoneSet
from log_methods import log_in_color
from log_methods import setup_logger
import logging
from generate_date_sequence import generate_date_sequence

pd.options.mode.chained_assignment = None #apparently this warning can throw false positives???

logger = setup_logger('ExpenseForecast', 'ExpenseForecast.log', level=logging.DEBUG)

def initialize_from_excel_file(path_to_excel_file):

    account_set_df = pd.read_excel(path_to_excel_file,sheet_name='AccountSet')
    budget_set_df = pd.read_excel(path_to_excel_file, sheet_name='BudgetSet')
    memo_rule_set_df = pd.read_excel(path_to_excel_file, sheet_name='MemoRuleSet')
    choose_one_set_df = pd.read_excel(path_to_excel_file, sheet_name='ChooseOneSet')
    account_milestones_df = pd.read_excel(path_to_excel_file, sheet_name='AccountMilestones')
    memo_milestones_df = pd.read_excel(path_to_excel_file, sheet_name='MemoMilestones')
    composite_account_milestones_df = pd.read_excel(path_to_excel_file, sheet_name='CompositeAccountMilestones')
    composite_memo_milestones_df = pd.read_excel(path_to_excel_file, sheet_name='CompositeMemoMilestones')
    config_df = pd.read_excel(path_to_excel_file, sheet_name='config')

    try:
        run_info_df = pd.read_excel(path_to_excel_file,sheet_name='run_info')
        forecast_df = pd.read_excel(path_to_excel_file, sheet_name='Forecast')
        skipped_df = pd.read_excel(path_to_excel_file, sheet_name='Skipped')
        confirmed_df = pd.read_excel(path_to_excel_file, sheet_name='Confirmed')
        deferred_df = pd.read_excel(path_to_excel_file, sheet_name='Deferred')
        milestone_results_df = pd.read_excel(path_to_excel_file, sheet_name='MilestoneResults')
    except Exception as e:
        pass #if forecast was not run this will happen



    A = AccountSet.AccountSet([])
    expect_curr_bal_acct = False
    expect_prev_bal_acct = False
    expect_principal_bal_acct = False
    expect_interest_acct = False

    billing_start_date = None
    interest_type = None
    apr = None
    interest_cadence = None
    minimum_payment = None
    previous_statement_balance = None
    current_statement_balance = None
    principal_balance = None
    accrued_interest = None
    for index, row in account_set_df.iterrows():
        if row.Account_Type.lower() == 'checking':
            A.createAccount(row.Name,row.Balance,row.Min_Balance,row.Max_Balance,'checking',None,None,None,None,None,None,None,None)

        if row.Account_Type.lower() == 'curr stmt bal' and not expect_curr_bal_acct:
            current_statement_balance = row.Balance
            expect_prev_bal_acct = True
            continue

        if row.Account_Type.lower() == 'prev stmt bal' and not expect_prev_bal_acct:
            previous_statement_balance = row.Balance
            interest_cadence = row.Interest_Cadence
            minimum_payment = row.Minimum_Payment
            billing_start_date = str(int(row.Billing_Start_Dt))
            interest_type = row.Interest_Type
            apr = row.APR

            expect_curr_bal_acct = True
            continue

        if row.Account_Type.lower() == 'interest' and not expect_interest_acct:
            accrued_interest = row.Balance
            expect_principal_bal_acct = True
            continue

        if row.Account_Type.lower() == 'principal balance' and not expect_principal_bal_acct:
            principal_balance = row.Balance
            interest_cadence = row.Interest_Cadence
            minimum_payment = row.Minimum_Payment
            billing_start_date = str(int(row.Billing_Start_Dt))
            interest_type = row.Interest_Type
            apr = row.APR
            expect_interest_acct = True
            continue

        #todo i was tired when I wrote these likely worth a second look
        if row.Account_Type.lower() == 'curr stmt bal' and expect_curr_bal_acct:
            A.createAccount(row.Name.split(':')[0],row.Balance,row.Min_Balance,row.Max_Balance,'credit',billing_start_date,interest_type,apr,interest_cadence,minimum_payment,previous_statement_balance,None,None)
            expect_curr_bal_acct = False

        if row.Account_Type.lower() == 'prev stmt bal' and expect_prev_bal_acct:
            A.createAccount(row.Name.split(':')[0],current_statement_balance,row.Min_Balance,row.Max_Balance,'credit',str(int(row.Billing_Start_Dt)),row.Interest_Type,row.APR,row.Interest_Cadence,row.Minimum_Payment,row.Balance,None,None,None)
            expect_prev_bal_acct = False

        if row.Account_Type.lower() == 'interest' and expect_interest_acct:
            A.createAccount(row.Name.split(':')[0],row.Balance + principal_balance,row.Min_Balance,row.Max_Balance,'loan',billing_start_date,interest_type,apr,interest_cadence,minimum_payment,None,principal_balance,row.Balance)
            expect_interest_acct = False

        if row.Account_Type.lower() == 'principal balance' and expect_principal_bal_acct:
            A.createAccount(row.Name.split(':')[0],row.Balance + accrued_interest,row.Min_Balance,row.Max_Balance,'loan',str(int(row.Billing_Start_Dt)),row.Interest_Type,row.APR,row.Interest_Cadence,row.Minimum_Payment,None,row.Balance,accrued_interest)
            expect_principal_bal_acct = False

    B = BudgetSet.BudgetSet([])
    for index, row in budget_set_df.iterrows():
        B.addBudgetItem(row.Start_Date,row.End_Date,row.Priority,row.Cadence,row.Amount,row.Memo,row.Deferrable,row.Partial_Payment_Allowed)

    M = MemoRuleSet.MemoRuleSet([])
    for index, row in memo_rule_set_df.iterrows():
        M.addMemoRule(row.Memo_Regex,row.Account_From,row.Account_To,row.Transaction_Priority)

    # for index, row in choose_one_set_df.iterrows():
    #     pass

    am__list = []
    for index, row in account_milestones_df.iterrows():
        am__list.append(AccountMilestone.AccountMilestone(row.Milestone_Name,row.Account_Name,row.Min_Balance,row.Max_Balance))

    mm__list = []
    for index, row in memo_milestones_df.iterrows():
        mm__list.append(MemoMilestone.MemoMilestone(row.Milestone_Name,row.Memo_Regex))

    cm__list = []
    #todo
    #for index, row in composite_milestones_df.iterrows():
    #    cm__list.append(CompositeMilestone.CompositeMilestone(row.Milestone_Name,))

    MS = MilestoneSet.MilestoneSet(A,B,am__list,mm__list,cm__list)

    start_date_YYYYMMDD = config_df.Start_Date_YYYYMMDD[0]
    end_date_YYYYMMDD = config_df.End_Date_YYYYMMDD[0]

    E = ExpenseForecast(A,B,M,start_date_YYYYMMDD,end_date_YYYYMMDD,MS)

    try:
        E.start_ts = run_info_df.start_ts.iat[0]
        E.end_ts = run_info_df.end_ts.iat[0]

        E.forecast_df = forecast_df
        E.skipped_df = skipped_df
        E.confirmed_df = confirmed_df
        E.deferred_df = deferred_df
        E.milestone_results_df = milestone_results_df
    except Exception as e:
        pass #will happen if forecast was not run

    return E

def initialize_from_json_file(path_to_json):
    with open(path_to_json) as json_data:
        data = json.load(json_data)

    initial_account_set = data['initial_account_set']
    initial_budget_set = data['initial_budget_set']
    initial_memo_rule_set = data['initial_memo_rule_set']
    start_date_YYYYMMDD = data['start_date']
    end_date_YYYYMMDD = data['end_date']
    milestone_set = data['milestone_set']

    A = AccountSet.AccountSet([])
    B = BudgetSet.BudgetSet([])
    M = MemoRuleSet.MemoRuleSet([])
    MS = MilestoneSet.MilestoneSet(A,B,[],[],[])

    for Account__dict in initial_account_set:
        #print('Account__dict:')
        #print(Account__dict)
        #Account__dict = Account__dict[0] #the dict came in a list
        if Account__dict['Account_Type'].lower() == 'checking':
            A.createAccount(Account__dict['Name'],
                            Account__dict['Balance'],
                            Account__dict['Min_Balance'],
                            Account__dict['Max_Balance'],
                            Account__dict['Account_Type'],
                            Account__dict['Billing_Start_Date'],
                            Account__dict['Interest_Type'],
                            Account__dict['APR'],
                            Account__dict['Interest_Cadence'],
                            Account__dict['Minimum_Payment']
                            )

        elif Account__dict['Account_Type'].lower() == 'curr stmt bal':
            credit_acct_name = Account__dict['Name'].split(':')[0]
            credit_curr_bal = Account__dict['Balance']

        elif Account__dict['Account_Type'].lower() == 'prev stmt bal':

            #first curr then prev
            A.createAccount(name=credit_acct_name,
                            balance=credit_curr_bal,
                            min_balance=Account__dict['Min_Balance'],
                            max_balance=Account__dict['Max_Balance'],
                            account_type="credit",
                            billing_start_date_YYYYMMDD=Account__dict['Billing_Start_Date'],
                            interest_type=Account__dict['Interest_Type'],
                            apr=Account__dict['APR'],
                            interest_cadence=Account__dict['Interest_Cadence'],
                            minimum_payment=Account__dict['Minimum_Payment'],
                            previous_statement_balance=Account__dict['Balance']
                            )

            del credit_acct_name
            del credit_curr_bal

        elif Account__dict['Account_Type'].lower() == 'principal balance':

            loan_acct_name = Account__dict['Name'].split(':')[0]
            loan_balance = Account__dict['Balance']
            loan_apr = Account__dict['APR']
            loan_billing_start_date = Account__dict['Billing_Start_Date']
            loan_min_payment = Account__dict['Minimum_Payment']
            loan_interest_cadence = Account__dict['Interest_Cadence']
            loan_interest_type = Account__dict['Interest_Type']

        elif Account__dict['Account_Type'].lower() == 'interest':

            #principal balance then interest

            A.createAccount(name=loan_acct_name,
                            balance=float(loan_balance) + float(Account__dict['Balance']),
                            min_balance=Account__dict['Min_Balance'],
                            max_balance=Account__dict['Max_Balance'],
                            account_type="loan",
                            billing_start_date_YYYYMMDD=loan_billing_start_date,
                            interest_type=loan_interest_type,
                            apr=loan_apr,
                            interest_cadence=loan_interest_cadence,
                            minimum_payment=loan_min_payment,
                            principal_balance=loan_balance,
                            accrued_interest=Account__dict['Balance']
                            )

            del loan_acct_name
            del loan_balance

        else:
            raise ValueError('unrecognized account type in ExpenseForecast::initialize_from_json_file: '+str(Account__dict['Account_Type']))


    for BudgetItem__dict in initial_budget_set:
        BudgetItem__dict = BudgetItem__dict[0]
        sd_YYYYMMDD = BudgetItem__dict['Start_Date']
        ed_YYYYMMDD = BudgetItem__dict['End_Date']

        B.addBudgetItem(start_date_YYYYMMDD=sd_YYYYMMDD,
                 end_date_YYYYMMDD=ed_YYYYMMDD,
                 priority=BudgetItem__dict['Priority'],
                 cadence=BudgetItem__dict['Cadence'],
                 amount=BudgetItem__dict['Amount'],
                 memo=BudgetItem__dict['Memo'],
                 deferrable=BudgetItem__dict['Deferrable'],
                 partial_payment_allowed=BudgetItem__dict['Partial_Payment_Allowed'])

    for MemoRule__dict in initial_memo_rule_set:
        #MemoRule__dict = MemoRule__dict[0]
        M.addMemoRule(memo_regex=MemoRule__dict['Memo_Regex'],
                      account_from=MemoRule__dict['Account_From'],
                      account_to=MemoRule__dict['Account_To'],
                      transaction_priority=MemoRule__dict['Transaction_Priority'])

    #todo idk what the data structure is here i have to develop the test more
    for am in milestone_set["account_milestones"]:
        MS.addAccountMilestone(am['Milestone_Name'],am['Account_Name'],am['Min_Balance'],am['Max_Balance'])

    for mm in milestone_set["memo_milestones"]:
        MS.addMemoMilestone(mm['Milestone_Name'],mm['Memo_Regex'])

    #milestone_name,account_milestones__list, memo_milestones__list
    for cm in milestone_set["composite_milestones"]:

        account_milestones__list = []
        for acc_mil in cm['account_milestones']:
            account_milestones__list.append(AccountMilestone.AccountMilestone(acc_mil['Milestone_Name'],acc_mil['Account_Name'],acc_mil['Min_Balance'],acc_mil['Max_Balance']))

        memo_milestones__list = []
        for memo_mil in cm['memo_milestones']:
            memo_milestones__list.append(MemoMilestone.MemoMilestone(memo_mil['Milestone_Name'],memo_mil['Memo_Regex']))

        MS.addCompositeMilestone(cm['Milestone_Name'],account_milestones__list,memo_milestones__list)

    E = ExpenseForecast(A, B, M,start_date_YYYYMMDD, end_date_YYYYMMDD, MS, print_debug_messages=True)

    E.unique_id = data['unique_id']
    E.start_ts = data['start_ts']
    E.end_ts = data['end_ts']

    #it is so dumb that I have to do this
    f = open('forecast_df_' + str(E.unique_id)+'.json', 'w')
    f.write(json.dumps(data['forecast_df'],indent=4))
    f.close()

    f = open('skipped_df_' + str(E.unique_id) + '.json', 'w')
    f.write(json.dumps(data['skipped_df'],indent=4))
    f.close()

    f = open('confirmed_df_' + str(E.unique_id) + '.json', 'w')
    f.write(json.dumps(data['confirmed_df'],indent=4))
    f.close()

    f = open('deferred_df_' + str(E.unique_id) + '.json', 'w')
    f.write(json.dumps(data['deferred_df'],indent=4))
    f.close()

    E.forecast_df = pd.read_json('forecast_df_' + str(E.unique_id) + '.json')
    E.skipped_df = pd.read_json('skipped_df_' + str(E.unique_id) + '.json')
    E.confirmed_df = pd.read_json('confirmed_df_' + str(E.unique_id) + '.json')
    E.deferred_df = pd.read_json('deferred_df_' + str(E.unique_id) + '.json')

    #milestone results

    return E

class ExpenseForecast:

    def __str__(self):

        left_margin_width = 5

        return_string = ""

        if not hasattr(self,'forecast_df'):
            return_string += """ This forecast has not yet been run. Use runForecast() to compute this forecast. """
            json_file_name = "FILE NAME UNDEFINED"
        else:
            #(if skipped is empty or min skipped priority is greater than 1) AND ( max forecast date == end date ) #todo check this second clause

            return_string += (""" Start timestamp: """ + str(self.start_ts)).rjust(left_margin_width,' ') + "\n"
            return_string += (""" End timestamp: """ + str(self.end_ts)).rjust(left_margin_width,' ') + "\n"

            #whether or not this object has ever been written to disk, we know its file name
            json_file_name = "Forecast__"+str(self.unique_id)+"__"+self.start_ts+".json"


        return_string += """Forecast  #""" + str(self.unique_id) + """: """+ self.start_date_YYYYMMDD + """ -> """+ self.end_date_YYYYMMDD +"\n"
        return_string += " "+(str(self.initial_account_set.getAccounts().shape[0]) + """ accounts, """ + str(self.initial_budget_set.getBudgetItems().shape[0])  + """  budget items, """ + str(self.initial_memo_rule_set.getMemoRules().shape[0])  + """ memo rules.""").rjust(left_margin_width,' ')+"\n"
        return_string += " "+json_file_name+"\n"



        return_string += "\n Budget schedule items: \n"
        return_string += self.initial_budget_set.getBudgetItems().to_string() +"\n"

        return return_string

    def __init__(self, account_set, budget_set, memo_rule_set, start_date_YYYYMMDD, end_date_YYYYMMDD,
                 milestone_set,
                 print_debug_messages=True, raise_exceptions=True):
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
        log_in_color(logger,'green','info','ExpenseForecast(start_date_YYYYMMDD='+str(start_date_YYYYMMDD)+', end_date_YYYYMMDD='+str(end_date_YYYYMMDD)+')')

        try:
            datetime.datetime.strptime(str(start_date_YYYYMMDD), '%Y%m%d')
            self.start_date_YYYYMMDD = str(start_date_YYYYMMDD)
        except:
            print('value was:' + str(start_date_YYYYMMDD) + '\n')
            raise ValueError  # Failed to cast start_date_YYYYMMDD to datetime with format %Y%m%d

        try:
            datetime.datetime.strptime(str(end_date_YYYYMMDD), '%Y%m%d')
            self.end_date_YYYYMMDD = str(end_date_YYYYMMDD)
        except:
            raise ValueError  # Failed to cast end_date_YYYYMMDD to datetime with format %Y%m%d

        if datetime.datetime.strptime(str(start_date_YYYYMMDD), '%Y%m%d') >= datetime.datetime.strptime(str(end_date_YYYYMMDD), '%Y%m%d'):
            raise ValueError(str(self.start_date_YYYYMMDD)+" >= "+str(self.end_date_YYYYMMDD))  # start_date must be before end_date

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

        distinct_base_account_names__from_acct = pd.DataFrame(pd.DataFrame(accounts_df[['Name']]).apply(lambda x: x[0].split(':')[0], axis=1).drop_duplicates()).rename(columns={0: 'Name'})
        account_names__from_memo = pd.concat(
            [pd.DataFrame(memo_df[['Account_From']]).rename(columns={'Account_From': 'Name'}), pd.DataFrame(memo_df[['Account_To']]).rename(columns={'Account_To': 'Name'})])

        distinct_account_names__from_memo = pd.DataFrame(account_names__from_memo.loc[account_names__from_memo.Name != 'None', 'Name'].drop_duplicates().reset_index(drop=True))

        try:
            A = set(distinct_account_names__from_memo.Name).union(set(['']))
            A = A - set(['ALL_LOANS']) #if we have a memo rule for ALL_LOANS, we don't want that to be checked against the list of account names

            B = set(distinct_account_names__from_memo.Name).intersection(set(distinct_base_account_names__from_acct.Name)).union(set(['']))
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

        if budget_df.shape[0] > 0:
            # for each budget item memo x priority combo, there is at least 1 memo_regex x priority that matches
            distinct_memo_priority_combinations__from_budget = budget_df[['Priority', 'Memo']].drop_duplicates()
            distinct_memo_priority_combinations__from_memo = memo_df[['Transaction_Priority', 'Memo_Regex']]  # should be no duplicates

            #make sure no non matches
            any_matches_found_at_all = False
            budget_items_with_matches = [] #each budget item should get appended once
            for budget_index, budget_row in distinct_memo_priority_combinations__from_budget.iterrows():
                match_found = False
                for memo_index, memo_row in distinct_memo_priority_combinations__from_memo.iterrows():
                    if budget_row.Priority == memo_row.Transaction_Priority:
                        m = re.search(memo_row.Memo_Regex, budget_row.Memo)
                        if m is not None:
                            match_found = True
                            budget_items_with_matches.append((budget_row.Memo,budget_row.Priority))
                            any_matches_found_at_all = True
                            continue

                if match_found == False:
                    error_text += "No regex match found for memo:\'" + str(budget_row.Memo) + "\'\n"

            if any_matches_found_at_all == False:
                error_ind = True

            if len(budget_items_with_matches) != len(set(budget_items_with_matches)):
                error_text += "At least one budget item had multiple matches:\n"
                for i in range(0,len(budget_items_with_matches)-1):
                    if budget_items_with_matches[i] == budget_items_with_matches[i+1]:
                        error_text += str(budget_items_with_matches[i])+"\n"
                error_ind = True

        #smpl_sel_vec = accounts_df.Interest_Type.apply(lambda x: x.lower() if x is not None else None) == 'simple'
        #cmpnd_sel_vec = accounts_df.Interest_Type.apply(lambda x: x.lower() if x is not None else None) == 'compound'

        if print_debug_messages:
            if error_ind:
                print(error_text)

        if raise_exceptions:
            if error_ind:
                log_in_color(logger,'red', 'error', error_text)
                raise ValueError(error_text)

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

        #lb_sel_vec = (datetime.datetime.strptime(self.start_date_YYYYMMDD, '%Y%m%d') <= datetime.datetime.strptime(proposed_df.Date, '%Y%m%d'))
        lb_sel_vec = [ datetime.datetime.strptime(self.start_date_YYYYMMDD, '%Y%m%d') <= datetime.datetime.strptime(d, '%Y%m%d') for d in proposed_df.Date ]
        #rb_sel_vec = (datetime.datetime.strptime(proposed_df.Date, '%Y%m%d') <= datetime.datetime.strptime(str(end_date_YYYYMMDD), '%Y%m%d'))
        rb_sel_vec = [ datetime.datetime.strptime(d, '%Y%m%d') <= datetime.datetime.strptime(self.end_date_YYYYMMDD, '%Y%m%d') for d in proposed_df.Date ]

        proposed_df = proposed_df.iloc[lb_sel_vec and rb_sel_vec,:]
        proposed_df.reset_index(drop=True, inplace=True)

        # take priority 1 items and put them in confirmed
        confirmed_df = proposed_df[proposed_df.Priority == 1]
        confirmed_df.reset_index(drop=True, inplace=True)

        proposed_df = proposed_df[proposed_df.Priority != 1]
        proposed_df.reset_index(drop=True, inplace=True)

        deferred_df = copy.deepcopy(proposed_df.head(0))
        skipped_df = copy.deepcopy(proposed_df.head(0))



        account_hash = hashlib.sha1(account_set.getAccounts().to_string().encode("utf-8")).hexdigest()
        budget_hash = hashlib.sha1(budget_set.getBudgetItems().to_string().encode("utf-8")).hexdigest()
        memo_hash = hashlib.sha1(memo_rule_set.getMemoRules().to_string().encode("utf-8")).hexdigest()
        start_date_hash = int(start_date_YYYYMMDD)
        end_date_hash = int(end_date_YYYYMMDD)

        #
        # print('HASH CALCULATION:')
        # print('account hash:'+str(account_hash))
        # print('budget hash:'+str(budget_hash))
        # print('memo hash:'+str(memo_hash))
        # print('start_date hash:'+str(start_date_hash))
        # print('end_date hash:'+str(end_date_hash))


        self.unique_id = str(hash( int(account_hash,16) + int(budget_hash,16) + int(memo_hash,16) + start_date_hash + end_date_hash ) % 100000).rjust(6,'0')
        #
        # print("unique_id:"+str(self.unique_id))
        # print("")

        self.initial_proposed_df = proposed_df
        self.initial_deferred_df = deferred_df
        self.initial_skipped_df = skipped_df
        self.initial_confirmed_df = confirmed_df

        self.milestone_set = milestone_set

    def appendSummaryLines(self):
        #todo incorporate savings
        #add net gain/loss (requires looking at memo)
        #add cumulative interest paid (requires looking at memo)

        account_info = self.initial_account_set.getAccounts()

        loan_acct_sel_vec = (account_info.Account_Type == 'principal balance') | (account_info.Account_Type == 'interest')
        cc_acct_sel_vec = (account_info.Account_Type == 'prev stmt bal') | (account_info.Account_Type == 'curr stmt bal')

        loan_acct_info = account_info.loc[loan_acct_sel_vec,:]
        credit_acct_info = account_info.loc[cc_acct_sel_vec,:]
        #savings_acct_info = account_info[account_info.Account_Type.lower() == 'savings', :]

        NetWorth = self.forecast_df.Checking
        for loan_account_index, loan_account_row in loan_acct_info.iterrows():
            #loan_acct_col_sel_vec = (self.forecast_df.columns == loan_account_row.Name)
            #print('loan_acct_col_sel_vec')
            #print(loan_acct_col_sel_vec)
            NetWorth = NetWorth - self.forecast_df.loc[:,loan_account_row.Name]

        for credit_account_index, credit_account_row in credit_acct_info.iterrows():
            NetWorth = NetWorth - self.forecast_df.loc[:,credit_account_row.Name]

        # for savings_account_index, savings_account_row in savings_acct_info.iterrows():
        #     NetWorth += self.forecast_df[:,self.forecast_df.columns == savings_account_row.Name]

        LoanTotal = self.forecast_df.Checking - self.forecast_df.Checking
        for loan_account_index, loan_account_row in loan_acct_info.iterrows():
            LoanTotal = LoanTotal + self.forecast_df.loc[:,loan_account_row.Name]

        CCDebtTotal = self.forecast_df.Checking - self.forecast_df.Checking
        for credit_account_index, credit_account_row in credit_acct_info.iterrows():
            CCDebtTotal = CCDebtTotal + self.forecast_df.loc[:, credit_account_row.Name]

        LiquidTotal = self.forecast_df.Checking #todo savings would go here

        self.forecast_df['NetWorth'] = NetWorth
        self.forecast_df['LoanTotal'] = LoanTotal
        self.forecast_df['CCDebtTotal'] = CCDebtTotal
        self.forecast_df['LiquidTotal'] = LiquidTotal

        memo_column = copy.deepcopy(self.forecast_df['Memo'])
        self.forecast_df = self.forecast_df.drop(columns=['Memo'])
        self.forecast_df['Memo'] = memo_column

    def runForecast(self):
        self.start_ts = datetime.datetime.now().strftime('%Y_%m_%d__%H_%M_%S')

        forecast_df, skipped_df, confirmed_df, deferred_df = self.computeOptimalForecast(
            start_date_YYYYMMDD=self.start_date_YYYYMMDD,
            end_date_YYYYMMDD=self.end_date_YYYYMMDD,
            confirmed_df=pd.DataFrame(self.initial_confirmed_df, copy=True),
            proposed_df=pd.DataFrame(self.initial_proposed_df, copy=True),
            deferred_df=pd.DataFrame(self.initial_deferred_df, copy=True),
            skipped_df=pd.DataFrame(self.initial_skipped_df, copy=True),
            account_set=copy.deepcopy(self.initial_account_set),
            memo_rule_set=copy.deepcopy(self.initial_memo_rule_set),
            raise_satisfice_failed_exception=False)

        self.forecast_df = forecast_df
        self.skipped_df = skipped_df
        self.confirmed_df = confirmed_df
        self.deferred_df = deferred_df

        self.end_ts = datetime.datetime.now().strftime('%Y_%m_%d__%H_%M_%S')

        account_milestone_results__list = []
        for a_m in self.milestone_set.account_milestones__list:
            res = self.evaluateAccountMilestone(a_m.account_name, a_m.min_balance, a_m.max_balance)
            account_milestone_results__list.append((a_m.milestone_name, res))
        self.account_milestone_results__list = account_milestone_results__list

        memo_milestone_results__list = []
        for m_m in self.milestone_set.memo_milestones__list:
            res = self.evaulateMemoMilestone(m_m.memo_regex)
            memo_milestone_results__list.append((m_m.milestone_name, res))
        self.memo_milestone_results__list = memo_milestone_results__list

        composite_milestone_results__list = []
        for c_m in self.milestone_set.composite_milestones__list:
            res = self.evaluateCompositeMilestone(self.milestone_set.account_milestones__list,
                                                  self.milestone_set.memo_milestones__list)
            composite_milestone_results__list.append((c_m.milestone_name, res))
        self.composite_milestone_results__list = composite_milestone_results__list

        self.forecast_df.to_csv('./Forecast_' + self.unique_id + '.csv') #this is only the forecast not the whole ExpenseForecast object
        self.writeToJSONFile() #this is the whole ExpenseForecast object #todo this should accept a path parameter
    #
    # def runForecast_v0(self):
    #     self.start_ts = datetime.datetime.now().strftime('%Y_%m_%d__%H_%M_%S')
    #
    #     # C = self.initial_confirmed_df.shape[0]
    #     # P = self.initial_proposed_df.shape[0]
    #     # D = self.initial_deferred_df.shape[0]
    #     # S = self.initial_skipped_df.shape[0]
    #     # T = C + P + D + S
    #
    #     #log_in_color(logger,'green', 'debug', 'ENTER runForecast() C:'+str(C)+'  P:'+str(P)+'  D:'+str(D)+'  S:'+str(S)+'  T:'+str(T), self.log_stack_depth)
    #     #log_in_color(logger,'green', 'debug', str(self) , self.log_stack_depth)
    #
    #     self.final_account_set = copy.deepcopy(self.initial_account_set)
    #
    #     forecast_df, skipped_df, confirmed_df, deferred_df = self.computeOptimalForecast_v0(start_date_YYYYMMDD=self.start_date_YYYYMMDD,
    #                                                                                      end_date_YYYYMMDD=self.end_date_YYYYMMDD,
    #                                                                                      confirmed_df=self.initial_confirmed_df,
    #                                                                                      proposed_df=self.initial_proposed_df,
    #                                                                                      deferred_df=self.initial_deferred_df,
    #                                                                                      skipped_df=self.initial_skipped_df,
    #                                                                                      account_set=self.final_account_set,
    #                                                                                      memo_rule_set=self.initial_memo_rule_set,
    #                                                                                      raise_satisfice_failed_exception=False)
    #     self.forecast_df = forecast_df
    #
    #     log_in_color(logger,'white','info',forecast_df.to_string())
    #
    #     self.forecast_df.to_csv('./Forecast_'+self.unique_id+'.csv')
    #
    #     self.skipped_df = skipped_df
    #     self.confirmed_df = confirmed_df
    #     self.deferred_df = deferred_df
    #
    #     self.end_ts = datetime.datetime.now().strftime('%Y_%m_%d__%H_%M_%S')
    #
    #     account_milestone_results__list = []
    #     for a_m in self.milestone_set.account_milestones__list:
    #         res = self.evaluateAccountMilestone(a_m.account_name,a_m.min_balance,a_m.max_balance)
    #         account_milestone_results__list.append((a_m.milestone_name,res))
    #     self.account_milestone_results__list = account_milestone_results__list
    #
    #     memo_milestone_results__list = []
    #     for m_m in self.milestone_set.memo_milestones__list:
    #         res = self.evaulateMemoMilestone(m_m.memo_regex)
    #         memo_milestone_results__list.append((m_m.milestone_name,res))
    #     self.memo_milestone_results__list = memo_milestone_results__list
    #
    #     composite_milestone_results__list = []
    #     for c_m in self.milestone_set.composite_milestones__list:
    #         res = self.evaluateCompositeMilestone(self.milestone_set.account_milestones__list,self.milestone_set.memo_milestones__list)
    #         composite_milestone_results__list.append((c_m.milestone_name,res))
    #     self.composite_milestone_results__list = composite_milestone_results__list
    #
    #     self.writeToJSONFile()
    #
    #     ###todo I do want to include this code in the final version, but I need to figure out the log levels and streams in a formal way first
    #     # try:
    #     #     assert (min(forecast_df.Date) == self.start_date_YYYYMMDD)
    #     # except AssertionError as e:
    #     #     raise ValueError("""
    #     #                 ExpenseForecast() did not include the first day as specified.
    #     #                 start_date_YYYYMMDD=""" + str(self.start_date_YYYYMMDD) + """
    #     #                 min(forecast_df.Date)=""" + str(min(forecast_df.Date)) + """
    #     #                 """)
    #     #
    #     # try:
    #     #     assert (max(forecast_df.Date) == self.end_date_YYYYMMDD)
    #     # except AssertionError as e:
    #     #     raise ValueError("""
    #     #                 ExpenseForecast() did not include the last day as specified.
    #     #                 self.end_date=""" + str(self.end_date_YYYYMMDD) + """
    #     #                 max(forecast_df.Date)=""" + str(max(forecast_df.Date)) + """
    #     #                 """)

    def writeToJSONFile(self):

        # log_in_color(logger,'green','info','Writing to ./Forecast__'+run_ts+'.csv')
        # self.forecast_df.to_csv('./Forecast__'+run_ts+'.csv')
        log_in_color(logger,'green', 'info', 'Writing to ./Forecast__' + self.unique_id + '__' + self.start_ts + '.json')
        #self.forecast_df.to_csv('./Forecast__' + run_ts + '.json')

        #self.forecast_df.index = self.forecast_df['Date']

        f = open('Forecast__' + self.unique_id + '__' + self.start_ts + '.json','a')
        f.write(self.to_json())
        f.close()

        # write all_data.csv  # self.forecast_df.iloc[:,0:(self.forecast_df.shape[1]-1)].to_csv('all_data.csv',index=False)

        # self.forecast_df.to_csv('out.csv', index=False)

    def getInitialForecastRow(self):

        min_sched_date = self.start_date_YYYYMMDD
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

        initial_forecast_row_df = pd.concat([date_only_df, accounts_only_df, memo_only_df])

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

    def addANewDayToTheForecast(self, forecast_df, date_YYYYMMDD):
        dates_as_datetime_dtype = [datetime.datetime.strptime(d, '%Y%m%d') for d in forecast_df.Date]
        prev_date_as_datetime_dtype = (datetime.datetime.strptime(date_YYYYMMDD, '%Y%m%d') - datetime.timedelta(days=1))
        sel_vec = [d == prev_date_as_datetime_dtype for d in dates_as_datetime_dtype]
        new_row_df = copy.deepcopy(forecast_df.loc[sel_vec])
        new_row_df.Date = date_YYYYMMDD
        new_row_df.Memo = ''
        forecast_df = pd.concat([forecast_df, new_row_df])
        forecast_df.reset_index(drop=True, inplace=True)
        return forecast_df

    def sortTxnsToPutIncomeFirst(self,relevant_confirmed_df):
        income_rows_sel_vec = [re.search('.*income.*', str(memo)) is not None for memo in
                               relevant_confirmed_df.Memo]
        income_rows_df = relevant_confirmed_df[income_rows_sel_vec]
        non_income_rows_df = relevant_confirmed_df[[not x for x in income_rows_sel_vec]]
        non_income_rows_df.sort_values(by=['Amount'], inplace=True, ascending=False)
        relevant_confirmed_df = pd.concat([income_rows_df, non_income_rows_df])
        relevant_confirmed_df.reset_index(drop=True, inplace=True)
        return relevant_confirmed_df

    def checkIfTxnIsIncome(self, confirmed_row):
        m_income = re.search('income', confirmed_row.Memo)
        try:
            m_income.group(0)
            income_flag = True
            log_in_color(logger,'yellow', 'debug', 'transaction flagged as income: ' + str(m_income.group(0)), 3)
        except Exception as e:
            income_flag = False

        return income_flag

    def updateBalancesAndMemo(self, forecast_df, account_set, confirmed_row, memo_rule_row, date_YYYYMMDD):
        #log_in_color(logger, 'green', 'info', 'ENTER updateBalancesAndMemo()',self.log_stack_depth)

        row_sel_vec = (forecast_df.Date == date_YYYYMMDD)
        if memo_rule_row.Account_To != 'ALL_LOANS':
            forecast_df.loc[row_sel_vec, forecast_df.columns == 'Memo'] += confirmed_row.Memo + ' ($' + str(confirmed_row.Amount) + ') ; '
            log_in_color(logger, 'green', 'info', confirmed_row.Memo + ' ($' + str(confirmed_row.Amount) + ') ; ', self.log_stack_depth)

        for account_index, account_row in account_set.getAccounts().iterrows():
            if (account_index + 1) == account_set.getAccounts().shape[1]:
                break

            col_sel_vec = (forecast_df.columns == account_row.Name)

            current_balance = forecast_df.loc[row_sel_vec, col_sel_vec].iloc[0].iloc[0]
            relevant_balance = account_set.getAccounts().iloc[account_index, 1]

            if current_balance != relevant_balance:
                forecast_df.loc[row_sel_vec, col_sel_vec] = relevant_balance
                if memo_rule_row.Account_To == 'ALL_LOANS' and account_row.Name != memo_rule_row.Account_From:
                    forecast_df.loc[row_sel_vec, forecast_df.columns == 'Memo'] += str(account_row.Name) + ' additional loan payment ($' + str(round(current_balance - relevant_balance, 2)) + ') ; '
                    log_in_color(logger, 'green', 'info',str(account_row.Name) + ' additional loan payment ($' + str(round(current_balance - relevant_balance, 2)) + ') ; ', self.log_stack_depth)

        #log_in_color(logger, 'green', 'info', 'EXIT updateBalancesAndMemo()', self.log_stack_depth)
        return forecast_df

    def attemptTransaction(self, forecast_df, account_set, memo_set, confirmed_df, proposed_row_df):
        log_in_color(logger,'green','info','ENTER attemptTransaction( C:'+str(confirmed_df.shape[0])+' P:'+str(proposed_row_df.Memo)+')',self.log_stack_depth)
        self.log_stack_depth += 1
        try:
            single_proposed_transaction_df = pd.DataFrame(copy.deepcopy(proposed_row_df)).T
            not_yet_validated_confirmed_df = copy.deepcopy(pd.concat([confirmed_df, single_proposed_transaction_df]))
            empty_df = pd.DataFrame({'Date':[],'Priority':[],'Amount':[],'Memo':[],'Deferrable':[],'Partial_Payment_Allowed':[]})

            hypothetical_future_state_of_forecast = \
                self.computeOptimalForecast(start_date_YYYYMMDD=self.start_date_YYYYMMDD,
                                            end_date_YYYYMMDD=self.end_date_YYYYMMDD,
                                            confirmed_df=not_yet_validated_confirmed_df,
                                            proposed_df=empty_df,
                                            deferred_df=empty_df,
                                            skipped_df=empty_df,
                                            account_set=copy.deepcopy(
                                                self.sync_account_set_w_forecast_day(account_set, forecast_df,
                                                                                     self.start_date_YYYYMMDD)),
                                            memo_rule_set=memo_set)[0]

            self.log_stack_depth -= 1
            log_in_color(logger, 'green', 'info', 'EXIT attemptTransaction('+str(proposed_row_df.Memo)+')'+' (SUCCESS)',self.log_stack_depth)
            return hypothetical_future_state_of_forecast #transaction is peritted
        except ValueError as e:
            self.log_stack_depth -= 5  # several decrements were skipped over by the exception
            log_in_color(logger, 'red', 'info',
                         'EXIT attemptTransaction(' + str(proposed_row_df.Memo) + ')' + ' (FAIL)', self.log_stack_depth)
            if re.search('.*Account boundaries were violated.*',
                         str(e.args)) is None:  # this is the only exception where we don't want to stop immediately
                raise e

    def processConfirmedTransactions(self, forecast_df, relevant_confirmed_df, memo_set, account_set, date_YYYYMMDD):
        log_in_color(logger, 'green', 'info', 'ENTER processConfirmedTransactions( C:'+str(relevant_confirmed_df.shape[0])+' )', self.log_stack_depth)
        self.log_stack_depth += 1

        for confirmed_index, confirmed_row in relevant_confirmed_df.iterrows():
            relevant_memo_rule_set = memo_set.findMatchingMemoRule(confirmed_row.Memo, confirmed_row.Priority)
            memo_rule_row = relevant_memo_rule_set.getMemoRules().loc[0, :]

            income_flag = self.checkIfTxnIsIncome(confirmed_row)

            account_set.executeTransaction(Account_From=memo_rule_row.Account_From,
                                           Account_To=memo_rule_row.Account_To,
                                           Amount=confirmed_row.Amount,
                                           income_flag=income_flag)

            forecast_df = self.updateBalancesAndMemo(forecast_df, account_set, confirmed_row, memo_rule_row,
                                                     date_YYYYMMDD)

        self.log_stack_depth -= 1
        log_in_color(logger, 'green', 'info', 'EXIT processConfirmedTransactions()', self.log_stack_depth)
        return forecast_df

    def processProposedTransactions(self, account_set, forecast_df, date_YYYYMMDD, memo_set, confirmed_df, relevant_proposed_df, priority_level):
        log_in_color(logger, 'green', 'info', 'ENTER processProposedTransactions( P:'+str(relevant_proposed_df.shape[0])+' )', self.log_stack_depth)
        self.log_stack_depth += 1

        new_deferred_df = relevant_proposed_df.head(0) #to preserve schema
        new_skipped_df = relevant_proposed_df.head(0)
        new_confirmed_df = relevant_proposed_df.head(0)

        #new_deferred_df = pd.DataFrame({'Date': [], 'Priority': [], 'Amount': [], 'Memo': [], 'Deferrable': [], 'Partial_Payment_Allowed': []})
        #new_skipped_df = pd.DataFrame({'Date': [], 'Priority': [], 'Amount': [], 'Memo': [], 'Deferrable': [], 'Partial_Payment_Allowed': []})
        #new_confirmed_df = pd.DataFrame({'Date': [], 'Priority': [], 'Amount': [], 'Memo': [], 'Deferrable': [], 'Partial_Payment_Allowed': []})

        if relevant_proposed_df.shape[0] == 0:
            self.log_stack_depth -= 1
            log_in_color(logger, 'green', 'info', 'EXIT processProposedTransactions()', self.log_stack_depth)
            return forecast_df, new_confirmed_df, new_deferred_df, new_skipped_df

        for proposed_item_index, proposed_row_df in relevant_proposed_df.iterrows():

            relevant_memo_rule_set = memo_set.findMatchingMemoRule(proposed_row_df.Memo, proposed_row_df.Priority)
            memo_rule_row = relevant_memo_rule_set.getMemoRules().loc[0, :]

            # False if not permitted, updated forecast if it is permitted
            result_of_attempt = self.attemptTransaction(forecast_df, account_set, memo_set, confirmed_df,
                                                        proposed_row_df)

            transaction_is_permitted = isinstance(result_of_attempt, pd.DataFrame)
            if transaction_is_permitted:
                hypothetical_future_state_of_forecast = result_of_attempt
            else:
                hypothetical_future_state_of_forecast = None

            if not transaction_is_permitted and proposed_row_df.Partial_Payment_Allowed:
                proposed_row_df.Amount = account_set.getBalances()[memo_rule_row.Account_From]

                try:

                    min_fut_avl_bals = self.getMinimumFutureAvailableBalances(account_set, forecast_df, date_YYYYMMDD)

                    reduced_amt = min_fut_avl_bals[memo_rule_row.Account_From]
                    proposed_row_df.Amount = reduced_amt

                    not_yet_validated_confirmed_df = pd.concat([confirmed_df,pd.DataFrame(proposed_row_df).T])

                    empty_df = pd.DataFrame({'Date': [], 'Priority': [], 'Amount': [], 'Memo': [], 'Deferrable': [],
                                             'Partial_Payment_Allowed': []})

                    hypothetical_future_state_of_forecast = \
                        self.computeOptimalForecast(start_date_YYYYMMDD=self.start_date_YYYYMMDD,
                                                    end_date_YYYYMMDD=self.end_date_YYYYMMDD,
                                                    confirmed_df=not_yet_validated_confirmed_df,
                                                    proposed_df=empty_df,
                                                    deferred_df=empty_df,
                                                    skipped_df=empty_df,
                                                    account_set=copy.deepcopy(
                                                        self.sync_account_set_w_forecast_day(account_set, forecast_df,
                                                                                             self.start_date_YYYYMMDD)),
                                                    # since we resatisfice from the beginning, this should reflect the beginning as well
                                                    memo_rule_set=memo_set)[0]

                    transaction_is_permitted = True
                except ValueError as e:
                    if re.search('.*Account boundaries were violated.*',
                                 str(e.args)) is None:
                        raise e

                    transaction_is_permitted = False

                if transaction_is_permitted:
                    amount_ammended = True

            if not transaction_is_permitted and proposed_row_df.Deferrable:

                proposed_row_df.Date = (datetime.datetime.strptime(proposed_row_df.Date, '%Y%m%d') + datetime.timedelta(
                    days=1)).strftime('%Y%m%d')

                new_deferred_df = pd.concat([new_deferred_df, pd.DataFrame(proposed_row_df).T])

                remaining_unproposed_transactions_df = relevant_proposed_df[
                    ~relevant_proposed_df.index.isin(proposed_row_df.index)]
                proposed_df = remaining_unproposed_transactions_df

            elif not transaction_is_permitted and not proposed_row_df.Deferrable:
                skipped_df = pd.concat([new_skipped_df, pd.DataFrame(proposed_row_df).T])

                remaining_unproposed_transactions_df = relevant_proposed_df[
                    ~relevant_proposed_df.index.isin(proposed_row_df.index)]
                proposed_df = remaining_unproposed_transactions_df

            elif transaction_is_permitted:

                if priority_level > 1:
                    account_set = self.sync_account_set_w_forecast_day(account_set, forecast_df, date_YYYYMMDD)

                account_set.executeTransaction(Account_From=memo_rule_row.Account_From,
                                               Account_To=memo_rule_row.Account_To, Amount=proposed_row_df.Amount,
                                               income_flag=False)

                new_confirmed_df = pd.concat([new_confirmed_df,pd.DataFrame(proposed_row_df).T])

                remaining_unproposed_transactions_df = relevant_proposed_df[
                    ~relevant_proposed_df.index.isin(proposed_row_df.index)]
                relevant_proposed_df = remaining_unproposed_transactions_df

                # forecast_df, skipped_df, confirmed_df, deferred_df
                forecast_with_accurately_updated_future_rows = hypothetical_future_state_of_forecast

                forecast_rows_to_keep_df = forecast_df[
                    [datetime.datetime.strptime(d, '%Y%m%d') < datetime.datetime.strptime(date_YYYYMMDD, '%Y%m%d') for d
                     in forecast_df.Date]]

                new_forecast_rows_df = forecast_with_accurately_updated_future_rows[
                    [datetime.datetime.strptime(d, '%Y%m%d') >= datetime.datetime.strptime(date_YYYYMMDD, '%Y%m%d') for
                     d in forecast_with_accurately_updated_future_rows.Date]]
                forecast_df = pd.concat([forecast_rows_to_keep_df, new_forecast_rows_df])
                assert forecast_df.shape[0] == forecast_df.drop_duplicates().shape[0]
                forecast_df.reset_index(drop=True, inplace=True)

                row_sel_vec = [x for x in (forecast_df.Date == datetime.datetime.strptime(date_YYYYMMDD, '%Y%m%d'))]
                col_sel_vec = (forecast_df.columns == "Memo")

                for account_index, account_row in account_set.getAccounts().iterrows():
                    if (account_index + 1) == account_set.getAccounts().shape[1]:
                        break
                    relevant_balance = account_set.getAccounts().iloc[account_index, 1]

                    row_sel_vec = (forecast_df.Date == datetime.datetime.strptime(date_YYYYMMDD, '%Y%m%d'))
                    col_sel_vec = (forecast_df.columns == account_row.Name)
                    forecast_df.iloc[row_sel_vec, col_sel_vec] = relevant_balance

            else:
                raise ValueError("""This is an edge case that should not be possible
                        transaction_is_permitted...............:""" + str(transaction_is_permitted) + """
                        budget_item_row.Deferrable.............:""" + str(proposed_row_df.Deferrable) + """
                        budget_item_row.Partial_Payment_Allowed:""" + str(proposed_row_df.Partial_Payment_Allowed) + """
                        """)

        self.log_stack_depth -= 1
        log_in_color(logger, 'green', 'info', 'EXIT processProposedTransactions() C:'+str(new_confirmed_df.shape[0])+' D:'+str(new_deferred_df.shape[0])+' S:'+str(new_skipped_df.shape[0]), self.log_stack_depth)
        return forecast_df, new_confirmed_df, new_deferred_df, new_skipped_df

    # eTDF
    #account_set, forecast_df, date_YYYYMMDD, memo_set, confirmed_df, proposed_df, deferred_df, skipped_df, priority_level, allow_partial_payments, allow_skip_and_defer

    #account_set, forecast_df, date_YYYYMMDD, memo_set,              ,    relevant_deferred_df,             priority_level, allow_partial_payments, allow_skip_and_defer
    def processDeferredTransactions(self,account_set, forecast_df, date_YYYYMMDD, memo_set, relevant_deferred_df, priority_level, confirmed_df):
        log_in_color(logger, 'green', 'info','ENTER processDeferredTransactions( D:'+str(relevant_deferred_df.shape[0])+' )', self.log_stack_depth)
        self.log_stack_depth += 1

        #new_confirmed_df = pd.DataFrame(
        #    {'Date': [], 'Priority': [], 'Amount': [], 'Memo': [], 'Deferrable': [], 'Partial_Payment_Allowed': []})
        #new_deferred_df = pd.DataFrame(
        #    {'Date': [], 'Priority': [], 'Amount': [], 'Memo': [], 'Deferrable': [], 'Partial_Payment_Allowed': []})
        new_confirmed_df = confirmed_df.head(0) #to preserve schema
        new_deferred_df = relevant_deferred_df.head(0)  # to preserve schema. same as above line btw

        if relevant_deferred_df.shape[0] == 0:

            self.log_stack_depth -= 1
            log_in_color(logger, 'green', 'info', 'EXIT processDeferredTransactions()', self.log_stack_depth)
            return forecast_df, new_confirmed_df, new_deferred_df

        for deferred_item_index, deferred_row_df in relevant_deferred_df.iterrows():
            if datetime.datetime.strptime(deferred_row_df.Date, '%Y%m%d') > datetime.datetime.strptime(
                    self.end_date_YYYYMMDD, '%Y%m%d'):
                continue

            relevant_memo_rule_set = memo_set.findMatchingMemoRule(deferred_row_df.Memo, deferred_row_df.Priority)
            memo_rule_row = relevant_memo_rule_set.getMemoRules().loc[0, :]

            hypothetical_future_state_of_forecast = copy.deepcopy(forecast_df.head(0))

            try:

                not_yet_validated_confirmed_df = pd.concat([confirmed_df, pd.DataFrame(deferred_row_df).T])
                #not_yet_validated_confirmed_df = confirmed_df.append(deferred_row_df)

                empty_df = pd.DataFrame({'Date':[],'Priority':[],'Amount':[],'Memo':[],'Deferrable':[],'Partial_Payment_Allowed':[]})

                hypothetical_future_state_of_forecast = \
                self.computeOptimalForecast(start_date_YYYYMMDD=self.start_date_YYYYMMDD,
                                            end_date_YYYYMMDD=self.end_date_YYYYMMDD,
                                            confirmed_df=not_yet_validated_confirmed_df,
                                            proposed_df=empty_df,
                                            deferred_df=empty_df,
                                            skipped_df=empty_df,
                                            account_set=copy.deepcopy(
                                                self.sync_account_set_w_forecast_day(account_set, forecast_df,
                                                                                     self.start_date_YYYYMMDD)),
                                            memo_rule_set=memo_set)[0]

                transaction_is_permitted = True
            except ValueError as e:
                if re.search('.*Account boundaries were violated.*',
                             str(e.args)) is None:  # this is the only exception where we don't want to stop immediately
                    raise e

                transaction_is_permitted = False

            if not transaction_is_permitted and deferred_row_df.Deferrable:
                deferred_row_df.Date = (
                            datetime.datetime.strptime(deferred_row_df.Date,
                                                       '%Y%m%d') + datetime.timedelta(days=1)).strftime('%Y%m%d')
                #_deferred_df = relevant_deferred_df[    ~relevant_deferred_df.index.isin(deferred_row_df.index)]

                new_deferred_df = pd.concat([new_deferred_df,pd.DataFrame(deferred_row_df).T])

            elif transaction_is_permitted:

                if priority_level > 1:
                    account_set = self.sync_account_set_w_forecast_day(account_set, forecast_df, date_YYYYMMDD)

                account_set.executeTransaction(Account_From=memo_rule_row.Account_From,
                                               Account_To=memo_rule_row.Account_To, Amount=deferred_row_df.Amount,
                                               income_flag=False)


                new_confirmed_df = pd.concat([new_confirmed_df, pd.DataFrame(deferred_row_df).T])

                remaining_unproposed_deferred_transactions_df = relevant_deferred_df[
                    ~relevant_deferred_df.index.isin(deferred_row_df.index)]
                relevant_deferred_df = remaining_unproposed_deferred_transactions_df

                # forecast_df, skipped_df, confirmed_df, deferred_df
                forecast_with_accurately_updated_future_rows = hypothetical_future_state_of_forecast

                row_sel_vec = [
                    datetime.datetime.strptime(d, '%Y%m%d') < datetime.datetime.strptime(date_YYYYMMDD, '%Y%m%d') for d
                    in forecast_df.Date]
                forecast_rows_to_keep_df = forecast_df.loc[row_sel_vec, :]

                row_sel_vec = [
                    datetime.datetime.strptime(d, '%Y%m%d') >= datetime.datetime.strptime(date_YYYYMMDD, '%Y%m%d') for d
                    in forecast_with_accurately_updated_future_rows.Date]
                new_forecast_rows_df = forecast_with_accurately_updated_future_rows.loc[row_sel_vec, :]

                forecast_df = pd.concat([forecast_rows_to_keep_df, new_forecast_rows_df])
                assert forecast_df.shape[0] == forecast_df.drop_duplicates().shape[0]
                forecast_df.reset_index(drop=True, inplace=True)

                for account_index, account_row in account_set.getAccounts().iterrows():
                    if (account_index + 1) == account_set.getAccounts().shape[1]:
                        break
                    relevant_balance = account_set.getAccounts().iloc[account_index, 1]

                    row_sel_vec = (forecast_df.Date == date_YYYYMMDD)
                    col_sel_vec = (forecast_df.columns == account_row.Name)
                    forecast_df.iloc[row_sel_vec, col_sel_vec] = relevant_balance
            else:
                raise ValueError("""This is an edge case that should not be possible
                        transaction_is_permitted...............:""" + str(transaction_is_permitted) + """
                        budget_item_row.Deferrable.............:""" + str(deferred_row_df.Deferrable) + """
                        budget_item_row.Partial_Payment_Allowed:""" + str(deferred_row_df.Partial_Payment_Allowed) + """
                        """)

        self.log_stack_depth -= 1
        log_in_color(logger, 'green', 'info', 'EXIT processDeferredTransactions()', self.log_stack_depth)
        return forecast_df, new_confirmed_df, new_deferred_df


    def executeTransactionsForDay(self, account_set, forecast_df, date_YYYYMMDD, memo_set, confirmed_df, proposed_df, deferred_df, skipped_df, priority_level):
        """

                I want this to be as generic as possible, with no memos or priority levels having dard coded behavior.
                At least a little of this hard-coding does make implementation simpler though.
                Therefore, let all income be priority level one, and be identified by the regex '.*income.*'


                """

        C0 = confirmed_df.shape[0]
        P0 = proposed_df.shape[0]
        D0 = deferred_df.shape[0]
        S0 = skipped_df.shape[0]
        T0 = C0 + P0 + D0 + S0

        bal_string = '  '
        for account_index, account_row in account_set.getAccounts().iterrows():
            bal_string += '$' + str(round(account_row.Balance, 2)) + ' '

        row_count_string = ' C0:' + str(C0) + '  P0:' + str(P0) + '  D0:' + str(D0) + '  S0:' + str(S0) + '  T0:' + str(T0)
        log_in_color(logger, 'green', 'info','ENTER executeTransactionsForDay(priority_level=' + str(priority_level) + ',date=' + str(date_YYYYMMDD) + ') ' + str(row_count_string) + str(bal_string), self.log_stack_depth)

        self.log_stack_depth += 1
        isP1 = (priority_level == 1)

        relevant_proposed_df = copy.deepcopy(proposed_df[(proposed_df.Priority == priority_level) & (proposed_df.Date == date_YYYYMMDD)])
        relevant_confirmed_df = copy.deepcopy(confirmed_df[(confirmed_df.Priority == priority_level) & (confirmed_df.Date == date_YYYYMMDD)])
        relevant_deferred_df = copy.deepcopy(deferred_df[(deferred_df.Priority <= priority_level) & (deferred_df.Date == date_YYYYMMDD)])

        # F = 'F:' + str(forecast_df.shape[0])
        # C = 'C:' + str(relevant_confirmed_df.shape[0])
        # P = 'P:' + str(relevant_proposed_df.shape[0])
        # D = 'D:' + str(relevant_deferred_df.shape[0])
        # log_in_color(logger, 'magenta', 'info',
        #              'ENTER assessPotentialOptimizations( ' + F + ' ' + C + ' ' + P + ' ' + D + ' )',
        #              self.log_stack_depth)

        if isP1:
            assert relevant_proposed_df.empty

        thereArePendingConfirmedTransactions = not relevant_confirmed_df.empty

        date_sel_vec = [(d == date_YYYYMMDD) for d in forecast_df.Date]
        noMatchingDayInForecast = forecast_df.loc[date_sel_vec].empty
        notPastEndOfForecast = datetime.datetime.strptime(date_YYYYMMDD,'%Y%m%d') <= datetime.datetime.strptime(self.end_date_YYYYMMDD, '%Y%m%d')

        if isP1 and noMatchingDayInForecast and notPastEndOfForecast:
            forecast_df = self.addANewDayToTheForecast(forecast_df, date_YYYYMMDD)

        if isP1 and thereArePendingConfirmedTransactions:
            relevant_confirmed_df = self.sortTxnsToPutIncomeFirst(relevant_confirmed_df)

        if priority_level > 1:
            account_set = self.sync_account_set_w_forecast_day(account_set, forecast_df, date_YYYYMMDD)

        log_in_color(logger,'green','debug','eTFD :: before processConfirmed',self.log_stack_depth)
        forecast_df = self.processConfirmedTransactions(forecast_df, relevant_confirmed_df,memo_set,account_set,date_YYYYMMDD)
        log_in_color(logger, 'green', 'debug', 'eTFD :: after processConfirmed', self.log_stack_depth)

        log_in_color(logger, 'green', 'debug', 'eTFD :: before processProposed', self.log_stack_depth)
        forecast_df, new_confirmed_df, new_deferred_df, new_skipped_df = self.processProposedTransactions(account_set,
                                                                                                  forecast_df,
                                                                                                  date_YYYYMMDD,
                                                                                                  memo_set,
                                                                                                  confirmed_df,
                                                                                                  relevant_proposed_df,
                                                                                                  priority_level)
        log_in_color(logger, 'green', 'debug', 'eTFD :: after processProposed', self.log_stack_depth)

        log_in_color(logger, 'white', 'info', 'new_confirmed_df:', self.log_stack_depth)
        log_in_color(logger, 'white', 'info', new_confirmed_df.to_string(), self.log_stack_depth)

        log_in_color(logger, 'white', 'info', 'new_deferred_df:', self.log_stack_depth)
        log_in_color(logger, 'white', 'info', new_deferred_df.to_string(), self.log_stack_depth)

        log_in_color(logger, 'white', 'info', 'new_skipped_df:', self.log_stack_depth)
        log_in_color(logger, 'white', 'info', new_skipped_df.to_string(), self.log_stack_depth)

        confirmed_df = pd.concat([confirmed_df, new_confirmed_df])
        confirmed_df.reset_index(drop=True, inplace=True)

        deferred_df = pd.concat([deferred_df, new_deferred_df])
        deferred_df.reset_index(drop=True, inplace=True)

        skipped_df = pd.concat([skipped_df, new_skipped_df])
        skipped_df.reset_index(drop=True, inplace=True)

        log_in_color(logger, 'white', 'info','updated confirmed_df:',self.log_stack_depth)
        log_in_color(logger, 'white', 'info',confirmed_df.to_string(),self.log_stack_depth)

        log_in_color(logger, 'white', 'info','updated deferred_df:',self.log_stack_depth)
        log_in_color(logger, 'white', 'info',deferred_df.to_string(),self.log_stack_depth)

        log_in_color(logger, 'white', 'info','updated skipped_df:',self.log_stack_depth)
        log_in_color(logger, 'white', 'info',skipped_df.to_string(),self.log_stack_depth)

        relevant_deferred_before_processing = pd.DataFrame(relevant_deferred_df,copy=True) #we need this to remove old txns if they stay deferred

        log_in_color(logger, 'green', 'debug', 'eTFD :: before processDeferred', self.log_stack_depth)
        forecast_df, new_confirmed_df, new_deferred_df = self.processDeferredTransactions(account_set, forecast_df, date_YYYYMMDD, memo_set, pd.DataFrame(relevant_deferred_df,copy=True), priority_level, confirmed_df)
        log_in_color(logger, 'green', 'debug', 'eTFD :: after processDeferred', self.log_stack_depth)

        confirmed_df = pd.concat([confirmed_df, new_confirmed_df])
        confirmed_df.reset_index(drop=True, inplace=True)

        p_LJ_c = pd.merge(proposed_df, confirmed_df, on=['Date', 'Memo', 'Priority'])

        #deferred_df = deferred_df - relevant + new. index won't be the same as OG
        #this is the inverse of how we selected the relevant rows
        not_relevant_deferred_df = pd.DataFrame(deferred_df[(deferred_df.Priority > priority_level) | (deferred_df.Date != date_YYYYMMDD)],copy=True)

        deferred_df = pd.concat([not_relevant_deferred_df,new_deferred_df])
        #deferred_df = not_relevant_deferred_df.append(new_deferred_df)
        deferred_df.reset_index(drop=True, inplace=True)

        C1 = confirmed_df.shape[0]
        D1 = deferred_df.shape[0]
        S1 = skipped_df.shape[0]
        T1 = C1 + D1 + S1
        row_count_string = ' C1:' + str(C1) + '  D1:' + str(D1) + '  S1:' + str(S1) + '  T1:' + str(T1)

        bal_string = '  '
        for account_index, account_row in account_set.getAccounts().iterrows():
            bal_string += '$' + str(round(account_row.Balance, 2)) + ' '

        self.log_stack_depth -= 1
        log_in_color(logger, 'green', 'info','EXIT executeTransactionsForDay(priority_level=' + str(priority_level) + ',date=' + str(date_YYYYMMDD) + ') ' + str(row_count_string) + str(bal_string), self.log_stack_depth)
        return [forecast_df, confirmed_df, deferred_df, skipped_df]

    # we should be able to take skipped out of here
    # def executeTransactionsForDay_v0(self, account_set, forecast_df, date_YYYYMMDD, memo_set, confirmed_df, proposed_df, deferred_df, skipped_df, priority_level, allow_partial_payments,
    #                               allow_skip_and_defer):
    #     """
    #
    #     I want this to be as generic as possible, with no memos or priority levels having dard coded behavior.
    #     At least a little of this hard-coding does make implementation simpler though.
    #     Therefore, let all income be priority level one, and be identified by the regex '.*income.*'
    #
    #
    #     """
    #
    #
    #
    #     # note that for confirmed and deferred we take priority less than or equal to, but for proposed, we only take equal to
    #     relevant_proposed_df = copy.deepcopy(proposed_df[(proposed_df.Priority == priority_level) & (proposed_df.Date == date_YYYYMMDD)])
    #
    #     relevant_confirmed_df = copy.deepcopy(confirmed_df[(confirmed_df.Priority == priority_level) & (confirmed_df.Date == date_YYYYMMDD)])
    #     relevant_deferred_df = copy.deepcopy(deferred_df[(deferred_df.Priority <= priority_level) & (deferred_df.Date == date_YYYYMMDD)])
    #
    #     C0 = confirmed_df.shape[0]
    #     P0 = proposed_df.shape[0]
    #     D0 = deferred_df.shape[0]
    #     S0 = 0
    #     T0 = C0 + P0 + D0
    #
    #     bal_string = '  '
    #     for account_index, account_row in account_set.getAccounts().iterrows():
    #         bal_string += '$' + str(round(account_row.Balance,2)) + ' '
    #
    #     row_count_string = ' C0:' + str(C0) + '  P0:' + str(P0) + '  D0:' + str(D0) + '  S0:' + str(S0) + '  T0:' + str(T0)
    #
    #
    #     #logger.debug('self.log_stack_depth += 1')
    #     log_in_color(logger,'green', 'info', 'ENTER executeTransactionsForDay_v0(priority_level=' + str(priority_level) + ',date=' + str(date_YYYYMMDD) + ') ' + str(row_count_string) + str(bal_string),self.log_stack_depth)
    #     self.log_stack_depth += 1
    #     #log_in_color(logger,'white', 'debug', '(start of day) available_balances: ' + str(account_set.getAvailableBalances()), self.log_stack_depth)
    #
    #     # print('Initial state of forecast (eTFD):')
    #     # print(forecast_df.to_string())
    #
    #     # log_in_color(logger,'yellow', 'debug', 'Memo Rules:', self.log_stack_depth)
    #     # log_in_color(logger,'yellow', 'debug',memo_set.getMemoRules(), self.log_stack_depth)
    #
    #     # print('(proposed_df.Priority <= priority_level):')
    #     # print((proposed_df.Priority <= priority_level))
    #     # print('proposed_df.Priority:')
    #     # print(proposed_df.Priority)
    #     # print('priority_level:')
    #     # print(priority_level)
    #     # print('proposed_df.Date == date_YYYYMMDD')
    #     # print((proposed_df.Date == date_YYYYMMDD))
    #
    #     # if not confirmed_df.empty:
    #     #     log_in_color(logger,'cyan', 'debug', 'ALL Confirmed: ', self.log_stack_depth)
    #     #     log_in_color(logger,'cyan', 'debug', confirmed_df.to_string(), self.log_stack_depth)
    #     #
    #     # if not proposed_df.empty:
    #     #     log_in_color(logger,'cyan', 'debug', 'ALL Proposed: ', self.log_stack_depth)
    #     #     log_in_color(logger,'cyan', 'debug', proposed_df.to_string(), self.log_stack_depth)
    #     #
    #     # if not deferred_df.empty:
    #     #     log_in_color(logger,'cyan', 'debug', 'ALL Deferred: ', self.log_stack_depth)
    #     #     log_in_color(logger,'cyan', 'debug', deferred_df.to_string(), self.log_stack_depth)
    #
    #     if not relevant_confirmed_df.empty:
    #         log_in_color(logger,'cyan', 'debug', 'Relevant Confirmed: ', self.log_stack_depth)
    #         log_in_color(logger,'cyan', 'debug', relevant_confirmed_df.to_string(), self.log_stack_depth)
    #
    #     if not relevant_proposed_df.empty:
    #         log_in_color(logger,'cyan', 'debug', 'Relevant Proposed: ', self.log_stack_depth)
    #         log_in_color(logger,'cyan', 'debug', relevant_proposed_df.to_string(), self.log_stack_depth)
    #     if not relevant_deferred_df.empty:
    #         log_in_color(logger,'cyan', 'debug', 'Relevant Deferred: ', self.log_stack_depth)
    #         log_in_color(logger,'cyan', 'debug', relevant_deferred_df.to_string(), self.log_stack_depth)
    #
    #
    #     date_sel_vec = [(d == date_YYYYMMDD) for d in forecast_df.Date]
    #     if priority_level == 1 and forecast_df.loc[ date_sel_vec ].empty and datetime.datetime.strptime(date_YYYYMMDD, '%Y%m%d') <= datetime.datetime.strptime(self.end_date_YYYYMMDD, '%Y%m%d'):
    #         # this is the only place where new days get added to a forecast
    #
    #         dates_as_datetime_dtype = [datetime.datetime.strptime(d, '%Y%m%d') for d in forecast_df.Date]
    #         prev_date_as_datetime_dtype = (datetime.datetime.strptime(date_YYYYMMDD, '%Y%m%d') - datetime.timedelta(days=1))
    #         sel_vec = [ d == prev_date_as_datetime_dtype for d in dates_as_datetime_dtype]
    #         new_row_df = copy.deepcopy(forecast_df.loc[ sel_vec ])
    #         new_row_df.Date = date_YYYYMMDD
    #         new_row_df.Memo = ''
    #         #print('APPENDING NEW DAY: ' + date_YYYYMMDD)
    #         #print(previous_row_df.to_string())
    #         log_in_color(logger, 'green', 'info', 'eTDF :: adding new day to forecast', self.log_stack_depth)
    #         forecast_df = pd.concat([forecast_df, new_row_df])
    #         forecast_df.reset_index(drop=True, inplace=True)
    #
    #     if (priority_level != 1 and relevant_proposed_df.empty and relevant_confirmed_df.empty and relevant_deferred_df.empty) | (priority_level == 1 and relevant_confirmed_df.empty):
    #         log_in_color(logger,'white', 'debug', '(end of day ' + str(date_YYYYMMDD) + ') available_balances: ' + str(account_set.getBalances()), self.log_stack_depth)
    #         #log_in_color(logger,'white', 'debug', 'final row state: ' + str(forecast_df[forecast_df.Date == datetime.datetime.strptime(date_YYYYMMDD, '%Y%m%d')]), self.log_stack_depth)
    #
    #         C1 = confirmed_df.shape[0]
    #         P1 = proposed_df.shape[0]
    #         D1 = deferred_df.shape[0]
    #         S1 = skipped_df.shape[0]
    #         T1 = C1 + P1 + D1 + S1
    #         row_count_string = ' C1:' + str(C1) + '  P1:' + str(P1) + '  D1:' + str(D1) + '  S1:' + str(S1) + '  T1:' + str(T1)
    #
    #         bal_string = '  '
    #         for account_index, account_row in account_set.getAccounts().iterrows():
    #             bal_string += '$' + str(round(account_row.Balance,2)) + ' '
    #
    #         #logger.debug('self.log_stack_depth -= 1')
    #
    #         ### No, this is still necessary
    #
    #
    #         # if datetime.datetime.strptime(date_YYYYMMDD, '%Y%m%d') != self.start_date:
    #         #     log_in_color(logger,'green', 'debug', 'no items for ' + str(date_YYYYMMDD) + '. Setting this days balances equal to the previous.', self.log_stack_depth)
    #         #     for i in range(1, len(forecast_df.columns)):
    #         #         prev_row_sel_vec = (forecast_df.Date == (datetime.datetime.strptime(date_YYYYMMDD, '%Y%m%d') - datetime.timedelta(days=1)))
    #         #         curr_row_sel_vec = (forecast_df.Date == datetime.datetime.strptime(date_YYYYMMDD, '%Y%m%d'))
    #         #         col_sel_vec = (forecast_df.columns == forecast_df.columns[i])
    #         #
    #         #         if forecast_df.columns[i] == 'Memo':
    #         #             break
    #         #
    #         #         # print('prev_row_sel_vec:')
    #         #         # print(list(prev_row_sel_vec))
    #         #         # print('curr_row_sel_vec:')
    #         #         # print(list(curr_row_sel_vec))
    #         #         # print('col_sel_vec:')
    #         #         # print(col_sel_vec)
    #         #
    #         #         value_to_carry = forecast_df.loc[list(prev_row_sel_vec), col_sel_vec].iloc[0].iloc[0]
    #         #
    #         #         # print('value_to_carry:')
    #         #         # print(value_to_carry)
    #         #
    #         #         forecast_df.loc[list(curr_row_sel_vec), col_sel_vec] = value_to_carry
    #
    #         self.log_stack_depth -= 1
    #         log_in_color(logger, 'green', 'info','EXIT executeTransactionsForDay_v0(priority_level=' + str(priority_level) + ',date=' + str(date_YYYYMMDD) + ') ' + str(row_count_string) + str(bal_string), self.log_stack_depth)
    #
    #         return [forecast_df, skipped_df, confirmed_df, deferred_df]  # this logic is here just to reduce useless logs
    #
    #     memo_set_df = memo_set.getMemoRules()
    #     relevant_memo_set_df = memo_set_df[memo_set_df.Transaction_Priority == priority_level]
    #
    #
    #     ##this block never executed during testing, so lets enforce that
    #     #it makes sense that proposed_df should be empty if priority level is 1
    #     if priority_level == 1:
    #         assert relevant_proposed_df.empty
    #     # if (priority_level == 1) and not relevant_proposed_df.empty:
    #     #     # not sure if this sort needs to happen for both but it doesnt hurt anything
    #     #     # It's not SUPPOSED to be necessary, but bad user input could mean this is necessary, so let's keep it
    #     #     income_rows_sel_vec = [re.search('.*income.*', str(memo)) is not None for memo in relevant_proposed_df.Memo]
    #     #     income_rows_df = relevant_proposed_df[income_rows_sel_vec]
    #     #     non_income_rows_df = relevant_proposed_df[[not x for x in income_rows_sel_vec]]
    #     #     non_income_rows_df.sort_values(by=['Amount'], inplace=True, ascending=False)
    #     #     relevant_proposed_df = pd.concat([income_rows_df, non_income_rows_df])
    #     #     relevant_proposed_df.reset_index(drop=True, inplace=True)
    #
    #     if (priority_level == 1) and not relevant_confirmed_df.empty:
    #         income_rows_sel_vec = [re.search('.*income.*', str(memo)) is not None for memo in relevant_confirmed_df.Memo]
    #         income_rows_df = relevant_confirmed_df[income_rows_sel_vec]
    #         non_income_rows_df = relevant_confirmed_df[[not x for x in income_rows_sel_vec]]
    #         non_income_rows_df.sort_values(by=['Amount'], inplace=True, ascending=False)
    #         relevant_confirmed_df = pd.concat([income_rows_df, non_income_rows_df])
    #         relevant_confirmed_df.reset_index(drop=True,inplace=True)
    #
    #         log_in_color(logger, 'green', 'info', 'eTDF :: sorted confirmed to put income first', self.log_stack_depth)
    #
    #     if priority_level == 1 and confirmed_df.shape[0] > 0 and deferred_df.shape[0] > 0:
    #         raise ValueError("Design assumption violated.")
    #
    #     ### this was added to input validation for BudgetItem
    #     # if priority_level == 1 and (allow_skip_and_defer or allow_partial_payments):
    #     #     log_in_color(logger,'white', 'debug', 'Nonsense combination of parameters. Edit input and try again.', self.log_stack_depth)
    #     #     log_in_color(logger,'white', 'debug', '(if priority_level = 1, then allow_skip_and_defer and allow_partial_payments must both be false)', self.log_stack_depth)
    #     #     raise ValueError("Design assumption violated. executeTransactionsForDay() :: if priority_level = 1, then allow_skip_and_defer and allow_partial_payments must both be false")
    #
    #     if priority_level > 1:
    #         # the account_set needs to be updated to reflect what the balances were for this day
    #         account_set = self.sync_account_set_w_forecast_day(account_set,forecast_df,date_YYYYMMDD)
    #
    #     # this may not be necessary, but it is at least clear that this method only operates on the local scope
    #     account_set = copy.deepcopy(account_set)
    #     forecast_df = copy.deepcopy(forecast_df)
    #     memo_set_df = copy.deepcopy(memo_set_df)
    #
    #     # log_in_color(logger,'yellow', 'debug', 'Relevant memo rules (priority ' + str(priority_level) + '):', self.log_stack_depth)
    #     # log_in_color(logger,'yellow', 'debug', relevant_memo_set_df.to_string(), self.log_stack_depth)
    #
    #     self.log_stack_depth += 1
    #     #logger.debug('self.log_stack_depth += 1')
    #     #log_in_color(logger,'green', 'debug', 'BEGIN PROCESSING CONFIRMED TXNS', self.log_stack_depth)
    #     log_in_color(logger, 'green', 'info', 'eTDF :: BEGIN processing confirmed txns', self.log_stack_depth)
    #     for confirmed_index, confirmed_row in relevant_confirmed_df.iterrows():
    #         log_in_color(logger,'cyan', 'debug', 'processing confirmed transaction: ' + str(confirmed_row.Memo), self.log_stack_depth)
    #         relevant_memo_rule_set = memo_set.findMatchingMemoRule(confirmed_row.Memo,confirmed_row.Priority)
    #         memo_rule_row = relevant_memo_rule_set.getMemoRules().loc[0,:]
    #
    #         m_income = re.search('income', confirmed_row.Memo)
    #         try:
    #             m_income.group(0)
    #             income_flag = True
    #             log_in_color(logger,'yellow', 'debug', 'transaction flagged as income: ' + str(m_income.group(0)), 3)
    #         except Exception as e:
    #             income_flag = False
    #
    #         account_set.executeTransaction(Account_From=memo_rule_row.Account_From, Account_To=memo_rule_row.Account_To, Amount=confirmed_row.Amount, income_flag=income_flag)
    #
    #         # if confirmed_row.Priority == 1: #if priority is not 1, then it will go through proposed or deferred where it gets memo appended
    #         # print('Appending memo (CASE 1): ' + str(confirmed_row.Memo))
    #         # forecast_df.loc[row_sel_vec, forecast_df.columns == 'Memo'] += confirmed_row.Memo + ' ; '
    #         # print('Post-append memo: ' + str(forecast_df.loc[row_sel_vec, forecast_df.columns == 'Memo'].iat[0,0]))
    #
    #         row_sel_vec = (forecast_df.Date == date_YYYYMMDD)
    #
    #         #if confirmed_row.Memo == 'PAY_TO_ALL_LOANS':
    #         #    forecast_df.loc[row_sel_vec, forecast_df.columns == 'Memo'] += account_row.Name + ' payment ($' + str(current_balance - relevant_balance) + ') ; '
    #         #else:
    #
    #         if memo_rule_row.Account_To != 'ALL_LOANS':
    #             forecast_df.loc[row_sel_vec, forecast_df.columns == 'Memo'] += confirmed_row.Memo + ' ($' + str(confirmed_row.Amount) + ') ; '
    #
    #         #update forecast to reflect new balances
    #         for account_index, account_row in account_set.getAccounts().iterrows():
    #             # print('account_row:')
    #             # print(account_row.to_string())
    #             if (account_index + 1) == account_set.getAccounts().shape[1]:
    #                 break
    #
    #
    #             col_sel_vec = (forecast_df.columns == account_row.Name)
    #
    #             # print('d: '+date_YYYYMMDD)
    #             # print('row_sel_vec:'+str(row_sel_vec))
    #             # print('forecast_df.loc[row_sel_vec, col_sel_vec]:')
    #             # print(forecast_df.loc[row_sel_vec, col_sel_vec].to_string())
    #             # print('forecast_df.loc[row_sel_vec, col_sel_vec].iloc[0]:')
    #             # print(forecast_df.loc[row_sel_vec, col_sel_vec].iloc[0])
    #             # print('forecast_df.loc[row_sel_vec, col_sel_vec].iloc[0].iloc[0]:')
    #             # print(forecast_df.loc[row_sel_vec, col_sel_vec].iloc[0].iloc[0])
    #
    #             current_balance = forecast_df.loc[row_sel_vec, col_sel_vec].iloc[0].iloc[0]
    #             relevant_balance = account_set.getAccounts().iloc[account_index, 1]
    #
    #             # print('current_balance:'+str(current_balance))
    #             # print('relevant_balance:' + str(relevant_balance))
    #
    #             # print(str(current_balance)+' ?= '+str(relevant_balance))
    #             if current_balance != relevant_balance:  # if statement just here to reduce useless logs
    #                 # log_in_color(logger,'cyan', 'debug', 'updating forecast_row ', self.log_stack_depth)
    #                 # log_in_color(logger,'cyan', 'debug', 'CASE 4 Setting ' + account_row.Name + ' to ' + str(relevant_balance), self.log_stack_depth)
    #                 # log_in_color(logger,'cyan', 'debug', 'BEFORE', self.log_stack_depth)
    #                 # log_in_color(logger,'cyan', 'debug', forecast_df[row_sel_vec].to_string(), self.log_stack_depth)
    #
    #                 forecast_df.loc[row_sel_vec, col_sel_vec] = relevant_balance
    #                 if memo_rule_row.Account_To == 'ALL_LOANS' and account_row.Name != memo_rule_row.Account_From:
    #                     forecast_df.loc[row_sel_vec, forecast_df.columns == 'Memo'] += str(account_row.Name)+' additional loan payment ($' + str(round(current_balance - relevant_balance,2)) + ') ; '
    #
    #     log_in_color(logger, 'green', 'info', 'eTDF :: END processing confirmed txns', self.log_stack_depth)
    #
    #     #log_in_color(logger,'green', 'debug', 'END PROCESSING CONFIRMED TXNS', self.log_stack_depth)
    #     # log_in_color(logger,'cyan', 'debug', 'AFTER', self.log_stack_depth)
    #     # log_in_color(logger,'cyan', 'debug', forecast_df[row_sel_vec].to_string(), self.log_stack_depth)
    #
    #     # log_in_color(logger,'cyan', 'debug', 'Relevant proposed transactions for day (priority ' + str(priority_level) + '):', self.log_stack_depth)
    #     # log_in_color(logger,'cyan', 'debug', relevant_proposed_df.to_string(), self.log_stack_depth)
    #
    #     # assert proposed_and_deferred_df['Memo'].shape[0] == proposed_and_deferred_df['Memo'].drop_duplicates().shape[0]
    #
    #     new_deferred_df = copy.deepcopy(deferred_df.head(0))
    #
    #     log_in_color(logger, 'green', 'info', 'eTDF :: BEGIN processing proposed txns', self.log_stack_depth)
    #     #log_in_color(logger,'green', 'debug', 'BEGIN PROCESSING PROPOSED TXNS', self.log_stack_depth)
    #     for proposed_item_index, proposed_row_df in relevant_proposed_df.iterrows():
    #         amount_ammended = False
    #         log_in_color(logger,'cyan','debug','Processing proposed or deferred txn:',self.log_stack_depth)
    #         log_in_color(logger,'cyan','debug',pd.DataFrame(proposed_row_df).T.to_string(),self.log_stack_depth)
    #
    #         relevant_memo_rule_set = memo_set.findMatchingMemoRule(proposed_row_df.Memo,proposed_row_df.Priority)
    #         memo_rule_row = relevant_memo_rule_set.getMemoRules().loc[0,:]
    #
    #         hypothetical_future_state_of_forecast = copy.deepcopy(forecast_df.head(0))
    #
    #         # no need for error checking between memo rules and budget items because that happened upstream in the ExpenseForecast constructor
    #         log_in_color(logger,'white', 'debug', '(pre transaction) available_balances: ' + str(account_set.getBalances()), self.log_stack_depth)
    #         log_in_color(logger,'green', 'debug', 'Checking transaction to see if it violates account boundaries', self.log_stack_depth)
    #         self.log_stack_depth += 1
    #         #logger.debug('self.log_stack_depth += 1')
    #         try:
    #             log_in_color(logger,'magenta', 'debug', 'ENTER error-check computeOptimalForecast: '+str(proposed_row_df.Memo), self.log_stack_depth)
    #
    #             single_proposed_transaction_df = pd.DataFrame(copy.deepcopy(proposed_row_df)).T
    #
    #             not_yet_validated_confirmed_df = copy.deepcopy(pd.concat([confirmed_df, single_proposed_transaction_df]))
    #
    #             # furthermore, since we are not processing any more proposed transactions in this one-adjustment simulation, there is no need to pass any proposed transactions to this method call
    #             empty_df = copy.deepcopy(proposed_df).head(0)
    #
    #             # try:
    #             #     assert confirmed_df['Memo'].shape[0] == confirmed_df['Memo'].drop_duplicates().shape[0]
    #             # except Exception as e:
    #             #     print('duplicated memo in updated_confirmed in the proposed or deferred part of the logic')
    #             #     raise e
    #
    #             # date_to_sync = proposed_row_df.Date - datetime.timedelta(days=1)
    #             # date_to_sync_YYYYMMDD = date_to_sync.strftime('%Y%m%d')
    #             # past_days_that_do_not_need_to_be_recalculated_df = forecast_df[forecast_df.Date <= date_to_sync]
    #             #
    #             # account_set_for_error_check = copy.deepcopy(self.sync_account_set_w_forecast_day(account_set, forecast_df, date_to_sync ))
    #             #
    #             # recalculated_future_forecast_df = self.computeOptimalForecast(start_date_YYYYMMDD=date_to_sync_YYYYMMDD,
    #             #                                                                     end_date_YYYYMMDD=self.end_date.strftime('%Y%m%d'),
    #             #                                                                     confirmed_df=not_yet_validated_confirmed_df,
    #             #                                                                     proposed_df=empty_df,
    #             #                                                                     deferred_df=empty_df,
    #             #                                                                     skipped_df=empty_df,
    #             #                                                                     account_set=account_set_for_error_check,
    #             #                                                                     memo_rule_set=memo_set)[0]
    #             #
    #             # hypothetical_future_state_of_forecast = pd.concat([past_days_that_do_not_need_to_be_recalculated_df,recalculated_future_forecast_df])
    #             # hypothetical_future_state_of_forecast.reset_index(inplace=True,drop=True)
    #
    #             hypothetical_future_state_of_forecast = self.computeOptimalForecast(start_date_YYYYMMDD=self.start_date_YYYYMMDD,
    #                                                                                 end_date_YYYYMMDD=self.end_date_YYYYMMDD,
    #                                                                                 confirmed_df=not_yet_validated_confirmed_df,
    #                                                                                 proposed_df=empty_df,
    #                                                                                 deferred_df=empty_df,
    #                                                                                 skipped_df=empty_df,
    #                                                                                 account_set=copy.deepcopy(self.sync_account_set_w_forecast_day(account_set, forecast_df, self.start_date_YYYYMMDD)), #since we resatisfice from the beginning, this should reflect the beginning as well
    #                                                                                 #account_set=copy.deepcopy(account_set),
    #                                                                                 memo_rule_set=memo_set)[0]
    #
    #             log_in_color(logger,'magenta', 'debug', 'END error-check computeOptimalForecast: '+str(proposed_row_df.Memo)+' (SUCCESS)', self.log_stack_depth)
    #             self.log_stack_depth -= 1
    #             #logger.debug('self.log_stack_depth -= 1')
    #             transaction_is_permitted = True
    #         except ValueError as e:
    #             if re.search('.*Account boundaries were violated.*', str(e.args)) is None:  # this is the only exception where we don't want to stop immediately
    #                 raise e
    #
    #             log_in_color(logger,'magenta', 'debug', 'END error-check computeOptimalForecast: '+str(proposed_row_df.Memo)+' (FAIL)', self.log_stack_depth)
    #             self.log_stack_depth -= 1
    #             #logger.debug('self.log_stack_depth -= 1')
    #             transaction_is_permitted = False
    #
    #
    #         # log_in_color(logger,'green', 'debug','not transaction_is_permitted=' + str(not transaction_is_permitted) + ',budget_item_row.Partial_Payment_Allowed=' + str(budget_item_row.Partial_Payment_Allowed),self.log_stack_depth)
    #         if not transaction_is_permitted and allow_partial_payments and proposed_row_df.Partial_Payment_Allowed:
    #             log_in_color(logger,'green', 'debug', 'Transaction not permitted. Attempting to calculate partial payment.')
    #             proposed_row_df.Amount = account_set.getBalances()[memo_rule_row.Account_From]
    #
    #             single_proposed_transaction_df = pd.DataFrame(copy.deepcopy(proposed_row_df)).T
    #             self.log_stack_depth += 1
    #             #logger.debug('self.log_stack_depth += 1')
    #             try:
    #                 log_in_color(logger,'magenta', 'debug', 'BEGIN error-check computeOptimalForecast: '+str(proposed_row_df.Memo)+' (reduced payment)', self.log_stack_depth)
    #                 ##logger.debug(' '.ljust(self.log_stack_depth * 4, ' ') + ' BEGIN error-check computeOptimalForecast: '+str(proposed_row_df.Memo)+' (reduced payment)')
    #
    #                 # print('single_proposed_transaction_df before amount reduction:')
    #                 # print(single_proposed_transaction_df.to_string())
    #
    #                 min_fut_avl_bals = self.getMinimumFutureAvailableBalances(account_set, forecast_df, date_YYYYMMDD)
    #
    #                 # print('min_fut_avl_bals:')
    #                 # print(min_fut_avl_bals)
    #
    #                 reduced_amt = min_fut_avl_bals[memo_rule_row.Account_From]  # no need to add the OG amount to this because it was already rejected4
    #                 # print('reduced_amt:')
    #                 # print(reduced_amt)
    #
    #                 single_proposed_transaction_df.Amount = reduced_amt
    #
    #                 # print('single_proposed_transaction_df after amount reduction:')
    #                 # print(single_proposed_transaction_df.to_string())
    #
    #                 not_yet_validated_confirmed_df = copy.deepcopy(pd.concat([confirmed_df, single_proposed_transaction_df]))
    #
    #                 # furthermore, since we are not processing any more proposed transactions in this one-adjustment simulation, there is no need to pass any proposed transactions to this method call
    #                 empty_df = copy.deepcopy(proposed_df).head(0)
    #
    #                 # try:
    #                 #     assert confirmed_df['Memo'].shape[0] == confirmed_df['Memo'].drop_duplicates().shape[0]
    #                 # except Exception as e:
    #                 #     print('duplicated memo in updated_confirmed in the proposed or deferred part of the logic')
    #                 #     raise e
    #
    #                 # date_to_sync = proposed_row_df.Date - datetime.timedelta(days=1)
    #                 # date_to_sync_YYYYMMDD = date_to_sync.strftime('%Y%m%d')
    #                 # past_days_that_do_not_need_to_be_recalculated_df = forecast_df[forecast_df.Date <= date_to_sync]
    #                 #
    #                 # account_set_for_error_check = copy.deepcopy(self.sync_account_set_w_forecast_day(account_set, forecast_df, date_to_sync))
    #                 #
    #                 # recalculated_future_forecast_df = self.computeOptimalForecast(start_date_YYYYMMDD=date_to_sync_YYYYMMDD,
    #                 #                                                               end_date_YYYYMMDD=self.end_date.strftime('%Y%m%d'),
    #                 #                                                               confirmed_df=not_yet_validated_confirmed_df,
    #                 #                                                               proposed_df=empty_df,
    #                 #                                                               deferred_df=empty_df,
    #                 #                                                               skipped_df=empty_df,
    #                 #                                                               account_set=account_set_for_error_check,
    #                 #                                                               memo_rule_set=memo_set)[0]
    #                 #
    #                 # hypothetical_future_state_of_forecast = pd.concat([past_days_that_do_not_need_to_be_recalculated_df, recalculated_future_forecast_df])
    #                 # hypothetical_future_state_of_forecast.reset_index(inplace=True, drop=True)
    #
    #
    #                 hypothetical_future_state_of_forecast = self.computeOptimalForecast_v0(start_date_YYYYMMDD=self.start_date_YYYYMMDD,
    #                                                                                     end_date_YYYYMMDD=self.end_date_YYYYMMDD,
    #                                                                                     confirmed_df=not_yet_validated_confirmed_df,
    #                                                                                     proposed_df=empty_df,
    #                                                                                     deferred_df=empty_df,
    #                                                                                     skipped_df=empty_df,
    #                                                                                     account_set=copy.deepcopy(self.sync_account_set_w_forecast_day(account_set, forecast_df, self.start_date_YYYYMMDD)), #since we resatisfice from the beginning, this should reflect the beginning as well
    #                                                                                     memo_rule_set=memo_set)[0]
    #
    #                 log_in_color(logger,'magenta', 'debug', 'END error-check computeOptimalForecast: '+str(proposed_row_df.Memo)+' (SUCCESS)', self.log_stack_depth)
    #                 self.log_stack_depth -= 1
    #                 #logger.debug('self.log_stack_depth -= 1')
    #                 transaction_is_permitted = True
    #             except ValueError as e:
    #                 if re.search('.*Account boundaries were violated.*', str(e.args)) is None:  # this is the only exception where we don't want to stop immediately
    #                     raise e
    #
    #                 log_in_color(logger,'magenta', 'debug', 'END error-check computeOptimalForecast: '+str(proposed_row_df.Memo)+' (FAIL)', self.log_stack_depth)
    #                 self.log_stack_depth -= 1
    #                 #logger.debug('self.log_stack_depth -= 1')
    #                 transaction_is_permitted = False  # I think this will never happen, because the "worst case" would be a 0, which is acceptable
    #
    #             if transaction_is_permitted:
    #                 log_in_color(logger,'green', 'debug', 'Transaction was not permitted at indicated amount. The txn was approved at this amount: ' + str(proposed_row_df.Amount),
    #                              self.log_stack_depth)
    #                 amount_ammended = True
    #
    #         # print('budget_item_row:'+str(budget_item_row))
    #         # log_in_color(logger,'green', 'debug', 'not transaction_is_permitted=' + str(not transaction_is_permitted) + ',budget_item_row.Deferrable=' + str(budget_item_row.Deferrable),self.log_stack_depth)
    #         if not transaction_is_permitted and allow_skip_and_defer and proposed_row_df.Deferrable:
    #             log_in_color(logger,'green', 'debug', 'Appending transaction to deferred_df', self.log_stack_depth)
    #
    #             proposed_row_df.Date = (datetime.datetime.strptime(proposed_row_df.Date, '%Y%m%d') + datetime.timedelta(days = 1)).strftime('%Y%m%d')
    #
    #             # print('new_deferred_df before append (case 1)')
    #             # print(new_deferred_df.to_string())
    #
    #             new_deferred_df = pd.concat([new_deferred_df, pd.DataFrame(proposed_row_df).T])
    #
    #             # print('new_deferred_df after append')
    #             # print(new_deferred_df.to_string())
    #
    #
    #             # assert deferred_df['Memo'].shape[0] == deferred_df['Memo'].drop_duplicates().shape[0]
    #             #
    #             # print('proposed before moved to deferred:')
    #             # print(proposed_df.to_string())
    #
    #             #this is done only for QC, since we don't return proposed_df
    #             remaining_unproposed_transactions_df = proposed_df[~proposed_df.index.isin(single_proposed_transaction_df.index)]
    #             proposed_df = remaining_unproposed_transactions_df
    #             #
    #             # print('proposed after moved to deferred:')
    #             # print(proposed_df.to_string())
    #
    #         elif not transaction_is_permitted and allow_skip_and_defer and not proposed_row_df.Deferrable:
    #             log_in_color(logger,'green', 'debug', 'Appending transaction to skipped_df', self.log_stack_depth)
    #             skipped_df = pd.concat([skipped_df, pd.DataFrame(proposed_row_df).T])
    #             # assert skipped_df['Memo'].shape[0] == skipped_df['Memo'].drop_duplicates().shape[0]
    #
    #             # this is done only for QC, since we don't return proposed_df
    #             remaining_unproposed_transactions_df = proposed_df[~proposed_df.index.isin(single_proposed_transaction_df.index)]
    #             proposed_df = remaining_unproposed_transactions_df
    #
    #         elif not transaction_is_permitted and not allow_skip_and_defer:
    #             raise ValueError('Partial payment, skip and defer were not allowed (either by txn parameter or method call), and transaction failed to obtain approval.')
    #
    #         elif transaction_is_permitted:
    #             log_in_color(logger,'green', 'debug', 'Transaction is permitted. Proceeding.', self.log_stack_depth)
    #
    #             if priority_level > 1:
    #                 account_set = self.sync_account_set_w_forecast_day(account_set,forecast_df,date_YYYYMMDD)
    #
    #             account_set.executeTransaction(Account_From=memo_rule_row.Account_From, Account_To=memo_rule_row.Account_To, Amount=proposed_row_df.Amount, income_flag=False)
    #             log_in_color(logger,'white', 'debug', 'available_balances immediately after txn: ' + str(account_set.getBalances()), self.log_stack_depth)
    #
    #             # print('confirmed_df BEFORE append to official')
    #             # print(confirmed_df.to_string())
    #             confirmed_df = pd.concat([confirmed_df, pd.DataFrame(proposed_row_df).T])
    #             # assert confirmed_df['Memo'].shape[0] == confirmed_df['Memo'].drop_duplicates().shape[0]
    #             # print('confirmed_df AFTER append to official')
    #             # print(confirmed_df.to_string())
    #
    #             remaining_unproposed_transactions_df = proposed_df[~proposed_df.index.isin(single_proposed_transaction_df.index)]
    #             proposed_df = remaining_unproposed_transactions_df
    #
    #
    #             # forecast_df, skipped_df, confirmed_df, deferred_df
    #             forecast_with_accurately_updated_future_rows = hypothetical_future_state_of_forecast
    #
    #
    #             #log_in_color(logger,'white', 'debug', 'available_balances after recalculate future: ' + str(account_set.getBalances()), self.log_stack_depth)
    #
    #
    #             forecast_rows_to_keep_df = forecast_df[ [ datetime.datetime.strptime(d, '%Y%m%d') < datetime.datetime.strptime(date_YYYYMMDD, '%Y%m%d') for d in forecast_df.Date ] ]
    #             #forecast_rows_to_keep_df = forecast_df[forecast_df.Date < datetime.datetime.strptime(date_YYYYMMDD, '%Y%m%d')]
    #             # print('forecast_with_accurately_updated_future_rows:')
    #             # print(forecast_with_accurately_updated_future_rows)
    #
    #
    #             new_forecast_rows_df = forecast_with_accurately_updated_future_rows[[ datetime.datetime.strptime(d,'%Y%m%d') >= datetime.datetime.strptime(date_YYYYMMDD,'%Y%m%d') for d in forecast_with_accurately_updated_future_rows.Date]]
    #             #new_forecast_rows_df = forecast_with_accurately_updated_future_rows[forecast_with_accurately_updated_future_rows.Date >= datetime.datetime.strptime(date_YYYYMMDD, '%Y%m%d')]
    #
    #             forecast_df = pd.concat([forecast_rows_to_keep_df, new_forecast_rows_df])
    #             assert forecast_df.shape[0] == forecast_df.drop_duplicates().shape[0]
    #             forecast_df.reset_index(drop=True, inplace=True)
    #
    #             row_sel_vec = [x for x in (forecast_df.Date == datetime.datetime.strptime(date_YYYYMMDD, '%Y%m%d'))]
    #             col_sel_vec = (forecast_df.columns == "Memo")
    #
    #             # print('Appending memo (CASE 2): ' + str(proposed_row_df.Memo))
    #             # if amount_ammended:
    #             #     forecast_df.iloc[row_sel_vec, col_sel_vec] += proposed_row_df.Memo + ' ($' + str(proposed_row_df.Amount) + ') ; '
    #             # else:
    #             #     forecast_df.iloc[row_sel_vec, col_sel_vec] += proposed_row_df.Memo + ' ; '
    #             # print('Post-append memo: ' + str(forecast_df.loc[row_sel_vec, forecast_df.columns == 'Memo'].iat[0,0]))
    #
    #             # print('forecast_df:')
    #             # print(forecast_df.to_string())
    #             # print( datetime.datetime.strptime(date_YYYYMMDD,'%Y%m%d'))
    #             for account_index, account_row in account_set.getAccounts().iterrows():
    #                 if (account_index + 1) == account_set.getAccounts().shape[1]:
    #                     break
    #                 relevant_balance = account_set.getAccounts().iloc[account_index, 1]
    #
    #                 row_sel_vec = (forecast_df.Date == datetime.datetime.strptime(date_YYYYMMDD, '%Y%m%d'))
    #                 col_sel_vec = (forecast_df.columns == account_row.Name)
    #                 # log_in_color(logger,'cyan', 'debug', 'updating forecast_row ')
    #                 # log_in_color(logger,'cyan', 'debug', 'BEFORE')
    #                 # log_in_color(logger,'cyan', 'debug', forecast_df[row_sel_vec].to_string())
    #                 forecast_df.iloc[row_sel_vec, col_sel_vec] = relevant_balance
    #                 # log_in_color(logger,'cyan', 'debug', 'AFTER')
    #                 # log_in_color(logger,'cyan', 'debug', forecast_df[row_sel_vec].to_string())
    #
    #         else:
    #             raise ValueError("""This is an edge case that should not be possible
    #             transaction_is_permitted...............:""" + str(transaction_is_permitted) + """
    #             allow_skip_and_defer...................:""" + str(allow_skip_and_defer) + """
    #             budget_item_row.Deferrable.............:""" + str(proposed_row_df.Deferrable) + """
    #             budget_item_row.Partial_Payment_Allowed:""" + str(proposed_row_df.Partial_Payment_Allowed) + """
    #             """)
    #
    #     log_in_color(logger, 'green', 'info', 'eTDF :: END processing proposed txns', self.log_stack_depth)
    #
    #     #log_in_color(logger,'green', 'debug', 'BEGIN PROCESSING DEFERRED TXNS', self.log_stack_depth)
    #     log_in_color(logger, 'green', 'info', 'eTDF :: BEGIN processing deferred txns', self.log_stack_depth)
    #     for deferred_item_index, deferred_row_df in relevant_deferred_df.iterrows():
    #         amount_ammended = False
    #         # log_in_color(logger,'cyan','debug','Processing proposed or deferred txn:',self.log_stack_depth)
    #         # log_in_color(logger,'cyan','debug',pd.DataFrame(budget_item_row).T.to_string(),self.log_stack_depth)
    #
    #         if datetime.datetime.strptime(deferred_row_df.Date,'%Y%m%d') > datetime.datetime.strptime(self.end_date_YYYYMMDD,'%Y%m%d'):
    #             continue
    #
    #         relevant_memo_rule_set = memo_set.findMatchingMemoRule(deferred_row_df.Memo,deferred_row_df.Priority)
    #         memo_rule_row = relevant_memo_rule_set.getMemoRules().loc[0, :]
    #
    #         hypothetical_future_state_of_forecast = copy.deepcopy(forecast_df.head(0))
    #
    #         # no need for error checking between memo rules and budget items because that happened upstream in the ExpenseForecast constructor
    #         log_in_color(logger,'white', 'debug', '(pre transaction) available_balances: ' + str(account_set.getBalances()), self.log_stack_depth)
    #         log_in_color(logger,'green', 'debug', 'Checking transaction to see if it violates account boundaries', self.log_stack_depth)
    #         self.log_stack_depth += 1
    #         # logger.debug('self.log_stack_depth += 1')
    #         try:
    #             log_in_color(logger,'magenta', 'debug', 'BEGIN error-check computeOptimalForecast: ' + str(deferred_row_df.Memo), self.log_stack_depth)
    #             ##logger.debug(' '.ljust(self.log_stack_depth * 4, ' ') + ' BEGIN error-check computeOptimalForecast: ' + str(deferred_row_df.Memo))
    #
    #             single_proposed_deferred_transaction_df = pd.DataFrame(copy.deepcopy(deferred_row_df)).T
    #
    #             not_yet_validated_confirmed_df = copy.deepcopy(pd.concat([confirmed_df, single_proposed_deferred_transaction_df]))
    #
    #             # furthermore, since we are not processing any more proposed transactions in this one-adjustment simulation, there is no need to pass any proposed transactions to this method call
    #             empty_df = copy.deepcopy(proposed_df).head(0)
    #
    #             # try:
    #             #     assert confirmed_df['Memo'].shape[0] == confirmed_df['Memo'].drop_duplicates().shape[0]
    #             # except Exception as e:
    #             #     print('duplicated memo in updated_confirmed in the proposed or deferred part of the logic')
    #             #     raise e
    #
    #             # date_to_sync = deferred_row_df.Date - datetime.timedelta(days=1)
    #             # date_to_sync_YYYYMMDD = date_to_sync.strftime('%Y%m%d')
    #             # past_days_that_do_not_need_to_be_recalculated_df = forecast_df[forecast_df.Date <= date_to_sync]
    #             #
    #             # account_set_for_error_check = copy.deepcopy(self.sync_account_set_w_forecast_day(account_set, forecast_df, date_to_sync))
    #             #
    #             # recalculated_future_forecast_df = self.computeOptimalForecast(start_date_YYYYMMDD=date_to_sync_YYYYMMDD,
    #             #                                                               end_date_YYYYMMDD=self.end_date.strftime('%Y%m%d'),
    #             #                                                               confirmed_df=not_yet_validated_confirmed_df,
    #             #                                                               proposed_df=empty_df,
    #             #                                                               deferred_df=empty_df,
    #             #                                                               skipped_df=empty_df,
    #             #                                                               account_set=account_set_for_error_check,
    #             #                                                               memo_rule_set=memo_set)[0]
    #             #
    #             # hypothetical_future_state_of_forecast = pd.concat([past_days_that_do_not_need_to_be_recalculated_df, recalculated_future_forecast_df])
    #             # hypothetical_future_state_of_forecast.reset_index(inplace=True, drop=True)
    #
    #             hypothetical_future_state_of_forecast = self.computeOptimalForecast_v0(start_date_YYYYMMDD=self.start_date_YYYYMMDD,
    #                                                                                 end_date_YYYYMMDD=self.end_date_YYYYMMDD,
    #                                                                                 confirmed_df=not_yet_validated_confirmed_df,
    #                                                                                 proposed_df=empty_df,
    #                                                                                 deferred_df=empty_df,
    #                                                                                 skipped_df=empty_df,
    #                                                                                 account_set=copy.deepcopy(
    #                                                                                     self.sync_account_set_w_forecast_day(account_set, forecast_df, self.start_date_YYYYMMDD)),
    #                                                                                 memo_rule_set=memo_set)[0]
    #
    #             log_in_color(logger,'magenta', 'debug', 'END error-check computeOptimalForecast: ' + str(deferred_row_df.Memo) + ' (SUCCESS)', self.log_stack_depth)
    #             self.log_stack_depth -= 1
    #             # logger.debug('self.log_stack_depth -= 1')
    #             transaction_is_permitted = True
    #         except ValueError as e:
    #             if re.search('.*Account boundaries were violated.*', str(e.args)) is None:  # this is the only exception where we don't want to stop immediately
    #                 raise e
    #
    #             log_in_color(logger,'magenta', 'debug', 'END error-check computeOptimalForecast: ' + str(deferred_row_df.Memo) + ' (FAIL)', self.log_stack_depth)
    #             self.log_stack_depth -= 1
    #             # logger.debug('self.log_stack_depth -= 1')
    #             transaction_is_permitted = False
    #
    #         # log_in_color(logger,'green', 'debug','not transaction_is_permitted=' + str(not transaction_is_permitted) + ',budget_item_row.Partial_Payment_Allowed=' + str(budget_item_row.Partial_Payment_Allowed),self.log_stack_depth)
    #         if not transaction_is_permitted and allow_partial_payments and deferred_row_df.Partial_Payment_Allowed: #todo i think that this never gets executed bc deferred payments cannot be partial
    #             log_in_color(logger,'green', 'debug', 'Transaction not permitted. Attempting to calculate partial payment.')
    #             deferred_row_df.Amount = account_set.getBalances()[memo_rule_row.Account_From]
    #
    #             single_proposed_deferred_transaction_df = pd.DataFrame(copy.deepcopy(deferred_row_df)).T
    #             self.log_stack_depth += 1
    #             # logger.debug('self.log_stack_depth += 1')
    #             try:
    #                 log_in_color(logger,'magenta', 'debug', 'BEGIN error-check computeOptimalForecast: ' + str(deferred_row_df.Memo) + ' (reduced payment)', self.log_stack_depth)
    #                 # logger.debug(' '.ljust(self.log_stack_depth * 4, ' ') + ' BEGIN error-check computeOptimalForecast: ' + str(deferred_row_df.Memo) + ' (reduced payment)')
    #
    #                 min_fut_avl_bals = self.getMinimumFutureAvailableBalances(account_set,forecast_df,date_YYYYMMDD)
    #                 reduced_amt = min(min_fut_avl_bals[memo_rule_row.Account_From]) #no need to add the OG amount to this because it was already rejected
    #                 single_proposed_deferred_transaction_df.Amount = reduced_amt
    #
    #                 not_yet_validated_confirmed_df = copy.deepcopy(pd.concat([confirmed_df, single_proposed_deferred_transaction_df]))
    #
    #                 # furthermore, since we are not processing any more proposed transactions in this one-adjustment simulation, there is no need to pass any proposed transactions to this method call
    #                 empty_df = copy.deepcopy(proposed_df).head(0)
    #
    #                 # try:
    #                 #     assert confirmed_df['Memo'].shape[0] == confirmed_df['Memo'].drop_duplicates().shape[0]
    #                 # except Exception as e:
    #                 #     print('duplicated memo in updated_confirmed in the proposed or deferred part of the logic')
    #                 #     raise e
    #
    #                 # date_to_sync = deferred_row_df.Date - datetime.timedelta(days=1)
    #                 # date_to_sync_YYYYMMDD = date_to_sync.strftime('%Y%m%d')
    #                 # past_days_that_do_not_need_to_be_recalculated_df = forecast_df[forecast_df.Date <= date_to_sync]
    #                 #
    #                 # account_set_for_error_check = copy.deepcopy(self.sync_account_set_w_forecast_day(account_set, forecast_df, date_to_sync))
    #                 #
    #                 # recalculated_future_forecast_df = self.computeOptimalForecast(start_date_YYYYMMDD=date_to_sync_YYYYMMDD,
    #                 #                                                               end_date_YYYYMMDD=self.end_date.strftime('%Y%m%d'),
    #                 #                                                               confirmed_df=not_yet_validated_confirmed_df,
    #                 #                                                               proposed_df=empty_df,
    #                 #                                                               deferred_df=empty_df,
    #                 #                                                               skipped_df=empty_df,
    #                 #                                                               account_set=account_set_for_error_check,
    #                 #                                                               memo_rule_set=memo_set)[0]
    #                 #
    #                 # hypothetical_future_state_of_forecast = pd.concat([past_days_that_do_not_need_to_be_recalculated_df, recalculated_future_forecast_df])
    #                 # hypothetical_future_state_of_forecast.reset_index(inplace=True, drop=True)
    #
    #                 hypothetical_future_state_of_forecast = self.computeOptimalForecast_v0(start_date_YYYYMMDD=self.start_date_YYYYMMDD,
    #                                                                                     end_date_YYYYMMDD=self.end_date_YYYYMMDD,
    #                                                                                     confirmed_df=not_yet_validated_confirmed_df,
    #                                                                                     proposed_df=empty_df,
    #                                                                                     deferred_df=empty_df,
    #                                                                                     skipped_df=empty_df,
    #                                                                                     account_set=copy.deepcopy(account_set),
    #                                                                                     memo_rule_set=memo_set)[0]
    #
    #                 log_in_color(logger,'magenta', 'debug', 'END error-check computeOptimalForecast: ' + str(deferred_row_df.Memo) + ' (SUCCESS)', self.log_stack_depth)
    #                 self.log_stack_depth -= 1
    #                 # logger.debug('self.log_stack_depth -= 1')
    #                 transaction_is_permitted = True
    #             except ValueError as e:
    #                 if re.search('.*Account boundaries were violated.*', str(e.args)) is None:  # this is the only exception where we don't want to stop immediately
    #                     raise e
    #
    #                 log_in_color(logger,'magenta', 'debug', 'END error-check computeOptimalForecast: ' + str(deferred_row_df.Memo) + ' (FAIL)', self.log_stack_depth)
    #                 self.log_stack_depth -= 1
    #                 # logger.debug('self.log_stack_depth -= 1')
    #                 transaction_is_permitted = False  # I think this will never happen, because the "worst case" would be a 0, which is acceptable
    #
    #             if transaction_is_permitted:
    #                 log_in_color(logger,'green', 'debug', 'Transaction was not permitted at indicated amount. The txn was approved at this amount: ' + str(deferred_row_df.Amount),
    #                              self.log_stack_depth)
    #                 amount_ammended = True
    #
    #         # print('budget_item_row:'+str(budget_item_row))
    #         # log_in_color(logger,'green', 'debug', 'not transaction_is_permitted=' + str(not transaction_is_permitted) + ',budget_item_row.Deferrable=' + str(budget_item_row.Deferrable),self.log_stack_depth)
    #         if not transaction_is_permitted and allow_skip_and_defer and deferred_row_df.Deferrable:
    #             log_in_color(logger,'green', 'debug', 'Appending transaction to deferred_df', self.log_stack_depth)
    #
    #             # print('Failed to execute deferrable transaction while processing deferred txns. Incrementing date.')
    #             # print('Deferred_df before increment:')
    #             # print(pd.DataFrame(deferred_row_df).T.to_string())
    #
    #             # todo the number being 1 here means deferrable txns DRAMATICALLY slows down performance. 14 is recommended.
    #             # If all other attempts to optimize fail, then adjust this. I think there are faster ways to get this same result.
    #             single_proposed_deferred_transaction_df.Date = (datetime.datetime.strptime(single_proposed_deferred_transaction_df.Date.iat[0],'%Y%m%d') + datetime.timedelta(days=1)).strftime('%Y%m%d')
    #             remaining_deferred_df = deferred_df[~deferred_df.index.isin(single_proposed_deferred_transaction_df.index)]
    #
    #             # print('deferred_df before append (case 3)')
    #             # print(deferred_df.to_string())
    #             deferred_df = pd.concat([remaining_deferred_df, single_proposed_deferred_transaction_df])
    #             #log_in_color(logger,'green', 'debug', 'deferred_df after append')
    #             #log_in_color(logger,'green', 'debug', deferred_df.to_string())
    #
    #             # print('Deferred_df after increment:')
    #             # print(deferred_df.to_string())
    #
    #         elif not transaction_is_permitted and allow_skip_and_defer and not deferred_row_df.Deferrable:
    #             #     log_in_color(logger,'green', 'debug', 'Appending transaction to skipped_df', self.log_stack_depth)
    #             #     skipped_df = pd.concat([skipped_df, pd.DataFrame(deferred_row_df).T])
    #             #     # assert skipped_df['Memo'].shape[0] == skipped_df['Memo'].drop_duplicates().shape[0]
    #             #
    #             #     # this is done only for QC, since we don't return proposed_df
    #             #     remaining_unproposed_transactions_df = proposed_df[~proposed_df.index.isin(single_proposed_deferred_transaction_df.index)]
    #             #     proposed_df = remaining_unproposed_transactions_df
    #             raise ValueError #this should never happen. if we are processing deferred txns, they should all be deferrable
    #
    #
    #         elif not transaction_is_permitted and not allow_skip_and_defer:
    #             raise ValueError('Partial payment, skip and defer were not allowed (either by txn parameter or method call), and transaction failed to obtain approval.')
    #
    #         elif transaction_is_permitted:
    #             log_in_color(logger,'green', 'debug', 'Transaction is permitted. Proceeding.', self.log_stack_depth)
    #
    #             if priority_level > 1:
    #                 account_set = self.sync_account_set_w_forecast_day(account_set, forecast_df, date_YYYYMMDD)
    #
    #             account_set.executeTransaction(Account_From=memo_rule_row.Account_From, Account_To=memo_rule_row.Account_To, Amount=deferred_row_df.Amount, income_flag=False)
    #             log_in_color(logger,'white', 'debug', 'available_balances immediately after txn: ' + str(account_set.getBalances()), self.log_stack_depth)
    #
    #             # print('confirmed_df BEFORE append to official')
    #             # print(confirmed_df.to_string())
    #             confirmed_df = pd.concat([confirmed_df, pd.DataFrame(deferred_row_df).T])
    #             # assert confirmed_df['Memo'].shape[0] == confirmed_df['Memo'].drop_duplicates().shape[0]
    #             # print('confirmed_df AFTER append to official')
    #             # print(confirmed_df.to_string())
    #
    #             remaining_unproposed_deferred_transactions_df = deferred_df[~deferred_df.index.isin(single_proposed_deferred_transaction_df.index)]
    #             deferred_df = remaining_unproposed_deferred_transactions_df
    #
    #             # forecast_df, skipped_df, confirmed_df, deferred_df
    #             forecast_with_accurately_updated_future_rows = hypothetical_future_state_of_forecast
    #
    #             # log_in_color(logger,'white', 'debug', 'available_balances after recalculate future: ' + str(account_set.getBalances()), self.log_stack_depth)
    #
    #             row_sel_vec = [ datetime.datetime.strptime(d,'%Y%m%d') < datetime.datetime.strptime(date_YYYYMMDD, '%Y%m%d') for d in forecast_df.Date ]
    #             forecast_rows_to_keep_df = forecast_df.loc[ row_sel_vec, : ]
    #             #forecast_rows_to_keep_df = forecast_df[forecast_df.Date < datetime.datetime.strptime(date_YYYYMMDD, '%Y%m%d')]
    #             # print('forecast_with_accurately_updated_future_rows:')
    #             # print(forecast_with_accurately_updated_future_rows)
    #             row_sel_vec = [ datetime.datetime.strptime(d,'%Y%m%d') >= datetime.datetime.strptime(date_YYYYMMDD, '%Y%m%d') for d in forecast_with_accurately_updated_future_rows.Date ]
    #             new_forecast_rows_df = forecast_with_accurately_updated_future_rows.loc[row_sel_vec,:]
    #
    #             forecast_df = pd.concat([forecast_rows_to_keep_df, new_forecast_rows_df])
    #             assert forecast_df.shape[0] == forecast_df.drop_duplicates().shape[0]
    #             forecast_df.reset_index(drop=True, inplace=True)
    #
    #             #row_sel_vec = [x for x in (forecast_df.Date == datetime.datetime.strptime(date_YYYYMMDD, '%Y%m%d'))]
    #             #col_sel_vec = (forecast_df.columns == "Memo")
    #
    #             # print('Appending memo (CASE 2): ' + str(proposed_row_df.Memo))
    #             # if amount_ammended:
    #             #     forecast_df.iloc[row_sel_vec, col_sel_vec] += proposed_row_df.Memo + ' ($' + str(proposed_row_df.Amount) + ') ; '
    #             # else:
    #             #     forecast_df.iloc[row_sel_vec, col_sel_vec] += proposed_row_df.Memo + ' ; '
    #             # print('Post-append memo: ' + str(forecast_df.loc[row_sel_vec, forecast_df.columns == 'Memo'].iat[0,0]))
    #
    #             # print('forecast_df:')
    #             # print(forecast_df.to_string())
    #             # print( datetime.datetime.strptime(date_YYYYMMDD,'%Y%m%d'))
    #             for account_index, account_row in account_set.getAccounts().iterrows():
    #                 if (account_index + 1) == account_set.getAccounts().shape[1]:
    #                     break
    #                 relevant_balance = account_set.getAccounts().iloc[account_index, 1]
    #
    #                 row_sel_vec = (forecast_df.Date == date_YYYYMMDD)
    #                 col_sel_vec = (forecast_df.columns == account_row.Name)
    #                 # log_in_color(logger,'cyan', 'debug', 'updating forecast_row ')
    #                 # log_in_color(logger,'cyan', 'debug', 'BEFORE')
    #                 # log_in_color(logger,'cyan', 'debug', forecast_df[row_sel_vec].to_string())
    #                 forecast_df.iloc[row_sel_vec, col_sel_vec] = relevant_balance
    #                 # log_in_color(logger,'cyan', 'debug', 'AFTER')
    #                 # log_in_color(logger,'cyan', 'debug', forecast_df[row_sel_vec].to_string())
    #         else:
    #             raise ValueError("""This is an edge case that should not be possible
    #             transaction_is_permitted...............:""" + str(transaction_is_permitted) + """
    #             allow_skip_and_defer...................:""" + str(allow_skip_and_defer) + """
    #             budget_item_row.Deferrable.............:""" + str(deferred_row_df.Deferrable) + """
    #             budget_item_row.Partial_Payment_Allowed:""" + str(deferred_row_df.Partial_Payment_Allowed) + """
    #             """)
    #     log_in_color(logger, 'green', 'info', 'eTDF :: END processing deferred txns', self.log_stack_depth)
    #
    #     #log_in_color(logger,'green', 'debug', 'END PROCESSING DEFERRED TXNS', self.log_stack_depth)
    #     self.log_stack_depth -= 1
    #     #logger.debug('self.log_stack_depth -= 1')
    #
    #     # print('deferred_df before append (case 2)')
    #     # print(deferred_df.to_string())
    #     deferred_df = pd.concat([deferred_df, new_deferred_df])
    #     deferred_df.reset_index(drop=True, inplace=True)
    #     new_deferred_df = new_deferred_df.head(0)
    #     # print('deferred_df after append')
    #     # print(deferred_df.to_string())
    #
    #     # print('Final state of forecast (eTFD):')
    #     # print(forecast_df.to_string())
    #
    #
    #     # print('returning this forecast row:')
    #     # print(forecast_df[forecast_df.Date == datetime.datetime.strptime(date_YYYYMMDD,'%Y%m%d')])
    #     log_in_color(logger,'white', 'debug', '(end of day ' + str(date_YYYYMMDD) + ') available_balances: ' + str(account_set.getBalances()), self.log_stack_depth)
    #
    #     bal_string = '  '
    #     for account_index, account_row in account_set.getAccounts().iterrows():
    #         bal_string += '$' + str(round(account_row.Balance,2)) + ' '
    #
    #     C1 = confirmed_df.shape[0]
    #     P1 = proposed_df.shape[0]
    #     D1 = deferred_df.shape[0]
    #     S1 = skipped_df.shape[0]
    #     T1 = C1 + P1 + D1 + S1
    #     row_count_string = ' C1:' + str(C1) + '  P1:' + str(P1) + '  D1:' + str(D1) + '  S1:' + str(S1) + '  T1:' + str(T1)
    #     #log_in_color(logger,'white', 'debug', 'final forecast state: ' + str(forecast_df.to_string()), self.log_stack_depth)
    #     #self.log_stack_depth -= 1
    #
    #     log_in_color(logger,'green', 'debug', 'EXIT executeTransactionsForDay_v0(priority_level=' + str(priority_level) + ',date=' + str(date_YYYYMMDD) + ') ' + str(row_count_string) + str(bal_string),
    #                  self.log_stack_depth)
    #
    #     # txn count should be same at beginning and end
    #     #log_in_color(logger,'green','debug',str(T0)+' ?= '+str(T1),self.log_stack_depth)
    #     try:
    #         assert T0 == T1
    #
    #         # this method does not return proposed_df, so we can assert that it is empty
    #         #assert proposed_df.shape[0] == 0
    #     except Exception as e:
    #
    #         ### this was good during development but lowers coverage now that i dont need it so commenting it out
    #         # inital_txn_count_string = 'Before consideration: C0:' + str(C0) + '  P0:' + str(P0) + '  D0:' + str(D0) + '  S0:' + str(S0) + '  T0:' + str(T0)
    #         # final_txn_count_string = 'After consideration: C1:' + str(C1) + '  P1:' + str(P1) + '  D1:' + str(D1) + '  S1:' + str(S1) + '  T1:' + str(T1)
    #         #
    #         # log_in_color(logger,'cyan', 'debug', str(inital_txn_count_string))
    #         # log_in_color(logger,'cyan', 'debug', str(final_txn_count_string))
    #         #
    #         # if not confirmed_df.empty:
    #         #     log_in_color(logger,'cyan', 'debug', 'ALL Confirmed: ', self.log_stack_depth)
    #         #     log_in_color(logger,'cyan', 'debug', confirmed_df.to_string(), self.log_stack_depth + 1)
    #         #
    #         # if not proposed_df.empty:
    #         #     log_in_color(logger,'cyan', 'debug', 'ALL Proposed: ', self.log_stack_depth)
    #         #     log_in_color(logger,'cyan', 'debug', proposed_df.to_string(), self.log_stack_depth + 1)
    #         #
    #         # if not deferred_df.empty:
    #         #     log_in_color(logger,'cyan', 'debug', 'ALL Deferred: ', self.log_stack_depth)
    #         #     log_in_color(logger,'cyan', 'debug', deferred_df.to_string(), self.log_stack_depth + 1)
    #         #
    #         # if not relevant_confirmed_df.empty:
    #         #     log_in_color(logger,'cyan', 'debug', 'Relevant Confirmed: ', self.log_stack_depth)
    #         #     log_in_color(logger,'cyan', 'debug', relevant_confirmed_df.to_string(), self.log_stack_depth + 1)
    #         #
    #         # if not relevant_proposed_df.empty:
    #         #     log_in_color(logger,'cyan', 'debug', 'Relevant Proposed: ', self.log_stack_depth)
    #         #     log_in_color(logger,'cyan', 'debug', relevant_proposed_df.to_string(), self.log_stack_depth + 1)
    #         #
    #         # if not relevant_deferred_df.empty:
    #         #     log_in_color(logger,'cyan', 'debug', 'Relevant Deferred: ', self.log_stack_depth)
    #         #     log_in_color(logger,'cyan', 'debug', relevant_deferred_df.to_string(), self.log_stack_depth + 1)
    #
    #         raise e
    #
    #     self.log_stack_depth -= 1
    #     #logger.debug('self.log_stack_depth -= 1')
    #     return [forecast_df, skipped_df, confirmed_df, deferred_df]

    def calculateInterestAccrualsForDay(self, account_set, current_forecast_row_df):

        #logger.debug('self.log_stack_depth += 1')

        bal_string = ' '
        for account_index, account_row in account_set.getAccounts().iterrows():
            bal_string += '$' + str(round(account_row.Balance,2)) + ' '

        log_in_color(logger,'cyan', 'debug', 'ENTER calculateInterestAccrualsForDay() '+ current_forecast_row_df.Date.iat[0] + bal_string, self.log_stack_depth)
        self.log_stack_depth += 1
        # This method will transfer balances from current statement to previous statement for savings and credit accounts

        current_date = current_forecast_row_df.Date.iloc[0]
        # generate a date sequence at the specified cadence between billing_start_date and the current date
        # if the current date is in that sequence, then do accrual
        for account_index, account_row in account_set.getAccounts().iterrows():
            if account_row.Interest_Cadence == 'None' or account_row.Interest_Cadence is None or account_row.Interest_Cadence == '':  # ithink this may be refactored. i think this will explode if interest_cadence is None
                continue
            num_days = (datetime.datetime.strptime(current_date,'%Y%m%d') - datetime.datetime.strptime(account_row.Billing_Start_Dt,'%Y%m%d')).days
            dseq = generate_date_sequence(start_date_YYYYMMDD=account_row.Billing_Start_Dt, num_days=num_days, cadence=account_row.Interest_Cadence)

            if current_forecast_row_df.Date.iloc[0] == account_row.Billing_Start_Dt:
                dseq = set(current_forecast_row_df.Date).union(dseq)

            if current_date in dseq:
                #log_in_color(logger,'green', 'debug', 'computing interest accruals for:' + str(account_row.Name), self.log_stack_depth)
                # print('interest accrual initial conditions:')
                # print(current_forecast_row_df.to_string())

                if account_row.Interest_Type.lower() == 'compound' and account_row.Interest_Cadence.lower() == 'yearly':
                    # print('CASE 1 : Compound, Monthly')

                    raise NotImplementedError

                elif account_row.Interest_Type.lower() == 'compound' and account_row.Interest_Cadence.lower() == 'quarterly':
                    # print('CASE 2 : Compound, Quarterly')

                    raise NotImplementedError

                elif account_row.Interest_Type.lower() == 'compound' and account_row.Interest_Cadence.lower() == 'monthly':
                    # print('CASE 3 : Compound, Monthly')

                    accrued_interest = account_row.APR * account_row.Balance / 12
                    account_set.accounts[account_index].balance += accrued_interest
                    account_set.accounts[account_index].balance = round(account_set.accounts[account_index].balance,2)

                    # move curr stmt bal to previous
                    prev_stmt_balance = round(account_set.accounts[account_index - 1].balance,2)

                    # prev_acct_name = account_set.accounts[account_index - 1].name
                    # curr_acct_name = account_set.accounts[account_index].name
                    # print('current account name:' + str(curr_acct_name))
                    # print('prev_acct_name:'+str(prev_acct_name))
                    # print('prev_stmt_balance:'+str(prev_stmt_balance))
                    account_set.accounts[account_index].balance += prev_stmt_balance
                    account_set.accounts[account_index].balance = round(account_set.accounts[account_index].balance, 2)
                    account_set.accounts[account_index - 1].balance = 0

                elif account_row.Interest_Type.lower() == 'compound' and account_row.Interest_Cadence.lower() == 'semiweekly':
                    # print('CASE 4 : Compound, Semiweekly')

                    raise NotImplementedError  # Compound, Semiweekly

                elif account_row.Interest_Type.lower() == 'compound' and account_row.Interest_Cadence.lower() == 'weekly':
                    # print('CASE 5 : Compound, Weekly')

                    raise NotImplementedError  # Compound, Weekly

                elif account_row.Interest_Type.lower() == 'compound' and account_row.Interest_Cadence.lower() == 'daily':
                    # print('CASE 6 : Compound, Daily')

                    raise NotImplementedError  # Compound, Daily

                elif account_row.Interest_Type.lower() == 'simple' and account_row.Interest_Cadence.lower() == 'yearly':
                    # print('CASE 7 : Simple, Yearly')

                    raise NotImplementedError  # Simple, Yearly

                elif account_row.Interest_Type.lower() == 'simple' and account_row.Interest_Cadence.lower() == 'quarterly':
                    # print('CASE 8 : Simple, Quarterly')

                    raise NotImplementedError  # Simple, Quarterly

                elif account_row.Interest_Type.lower() == 'simple' and account_row.Interest_Cadence.lower() == 'monthly':
                    # print('CASE 9 : Simple, Monthly')

                    raise NotImplementedError  # Simple, Monthly

                elif account_row.Interest_Type.lower() == 'simple' and account_row.Interest_Cadence.lower() == 'semiweekly':
                    # print('CASE 10 : Simple, Semiweekly')

                    raise NotImplementedError  # Simple, Semiweekly

                elif account_row.Interest_Type.lower() == 'simple' and account_row.Interest_Cadence.lower() == 'weekly':
                    # print('CASE 11 : Simple, Weekly')

                    raise NotImplementedError  # Simple, Weekly

                elif account_row.Interest_Type.lower() == 'simple' and account_row.Interest_Cadence.lower() == 'daily':
                    # print('CASE 12 : Simple, Daily')

                    accrued_interest = account_row.APR * account_row.Balance / 365.25
                    account_set.accounts[account_index + 1].balance += accrued_interest  # this is the interest account
                    account_set.accounts[account_index + 1].balance = round(account_set.accounts[account_index + 1].balance,2)

            else:
                # ('There were no interest bearing items for this day')
                # print(current_forecast_row_df.to_string())
                pass

            updated_balances = account_set.getAccounts().Balance
            for account_index, account_row in account_set.getAccounts().iterrows():
                if (account_index + 1) == account_set.getAccounts().shape[1]:
                    break

                relevant_balance = account_set.getAccounts().iloc[account_index, 1]
                col_sel_vec = (current_forecast_row_df.columns == account_row.Name)
                current_forecast_row_df.iloc[0, col_sel_vec] = round(relevant_balance,2)

            bal_string = ''
            for account_index, account_row in account_set.getAccounts().iterrows():
                bal_string += '$' + str(round(account_row.Balance,2)) + ' '

            # # returns a single forecast row
            # log_in_color(logger,'green', 'debug', 'EXIT calculateInterestAccrualsForDay ' + bal_string, self.log_stack_depth)
            # self.log_stack_depth -= 1
            # return current_forecast_row_df

        bal_string = ' '
        for account_index, account_row in account_set.getAccounts().iterrows():
            bal_string += '$' + str(round(account_row.Balance,2)) + ' '

        self.log_stack_depth -= 1
        log_in_color(logger,'cyan', 'debug', 'EXIT  calculateInterestAccrualsForDay() '+ current_forecast_row_df.Date.iat[0] + bal_string, self.log_stack_depth)
        #logger.debug('self.log_stack_depth -= 1')
        return current_forecast_row_df  # this runs when there are no interest bearing accounts in the simulation at all

    def executeMinimumPayments(self, account_set, current_forecast_row_df):

        bal_string = ''
        for account_index2, account_row2 in account_set.getAccounts().iterrows():
            bal_string += '$' + str(round(account_row2.Balance,2)) + ' '


        #logger.debug('self.log_stack_depth += 1')
        log_in_color(logger,'cyan', 'debug', 'ENTER executeMinimumPayments() ' + bal_string, self.log_stack_depth)
        self.log_stack_depth += 1

        # the branch logic here assumes the sort order of accounts in account list
        for account_index, account_row in account_set.getAccounts().iterrows():

            #not sure why both of these checks are necessary
            if account_row.Billing_Start_Dt == 'None':
                continue

            if pd.isnull(account_row.Billing_Start_Dt):
                continue

            # print(BEGIN_GREEN + row.to_string() + RESET_COLOR)
            # print('current_forecast_row_df.Date - row.Billing_Start_Dt:')
            # print('current_forecast_row_df.Date:')
            # print(current_forecast_row_df.Date)
            # print('row.Billing_Start_Dt:')
            # print(row.Billing_Start_Dt)

            num_days = (datetime.datetime.strptime(current_forecast_row_df.Date.iloc[0],'%Y%m%d') - datetime.datetime.strptime(account_row.Billing_Start_Dt,'%Y%m%d')).days
            #billing_days = set(generate_date_sequence(account_row.Billing_Start_Dt.strftime('%Y%m%d'), num_days, account_row.Interest_Cadence))
            billing_days = set(generate_date_sequence(account_row.Billing_Start_Dt, num_days, 'monthly'))

            if current_forecast_row_df.Date.iloc[0] == account_row.Billing_Start_Dt:
                billing_days = set(current_forecast_row_df.Date).union(billing_days) #if the input date matches the start date, add it to the set (bc range where start = end == null set)

            if current_forecast_row_df.Date.iloc[0] in billing_days:
                # log_in_color(logger,'green', 'debug', 'Processing minimum payments', self.log_stack_depth)
                # log_in_color(logger,'green', 'debug', 'account_row:', self.log_stack_depth)
                # log_in_color(logger,'green', 'debug', account_row.to_string(), self.log_stack_depth)

                # print(row)
                if account_row.Account_Type == 'prev stmt bal':  # cc min payment

                    #minimum_payment_amount = max(40, account_row.Balance * 0.033) #this is an estimate
                    minimum_payment_amount = round(max(40, account_row.Balance * account_row.APR/12),2)
                    #todo it turns out that the way this really works is that Chase uses 1% PLUS the interest accrued to be charged immediately, not added to the principal
                    #very much not how I designed this but not earth-shatteringly different


                    payment_toward_prev = round(min(minimum_payment_amount, account_row.Balance),2)
                    payment_toward_curr = round(min(account_set.getAccounts().loc[account_index - 1, :].Balance, minimum_payment_amount - payment_toward_prev),2)
                    surplus_payment = round(minimum_payment_amount - (payment_toward_prev + payment_toward_curr),2)

                    if (payment_toward_prev + payment_toward_curr) > 0:
                        account_set.executeTransaction(Account_From='Checking', Account_To=account_row.Name.split(':')[0],
                                                       # Note that the execute transaction method will split the amount paid between the 2 accounts
                                                       Amount=(payment_toward_prev + payment_toward_curr))
                        current_forecast_row_df.Memo += account_row.Name.split(':')[0] + ' cc min payment ($' + str(minimum_payment_amount) + ') ; '

                elif account_row.Account_Type == 'principal balance':  # loan min payment

                    minimum_payment_amount = round(account_set.getAccounts().loc[account_index, :].Minimum_Payment,2)
                    current_debt_balance = round(account_set.getBalances()[account_row.Name.split(':')[0]],2)
                    loan_payment_amount = round(min(current_debt_balance,minimum_payment_amount),2)

                    if loan_payment_amount > 0:
                        account_set.executeTransaction(Account_From='Checking', Account_To=account_row.Name.split(':')[0],
                                                       # Note that the execute transaction method will split the amount paid between the 2 accounts
                                                       Amount=loan_payment_amount)
                        current_forecast_row_df.Memo += account_row.Name.split(':')[0] + ' loan min payment ($' + str(minimum_payment_amount) + '); '


                # if account_row.Account_Type == 'prev stmt bal' or account_row.Account_Type == 'interest':
                #
                #     payment_toward_prev = min(minimum_payment_amount, account_row.Balance)
                #     payment_toward_curr = min(account_set.getAccounts().loc[account_index - 1, :].Balance, minimum_payment_amount - payment_toward_prev)
                #     surplus_payment = minimum_payment_amount - (payment_toward_prev + payment_toward_curr)
                #
                #     if (payment_toward_prev + payment_toward_curr) > 0:
                #         account_set.executeTransaction(Account_From='Checking', Account_To=account_row.Name.split(':')[0],
                #                                        # Note that the execute transaction method will split the amount paid between the 2 accounts
                #                                        Amount=(payment_toward_prev + payment_toward_curr))

        # print('current_forecast_row_df pre-update')
        # print(current_forecast_row_df.to_string())
        for account_index, account_row in account_set.getAccounts().iterrows():
            relevant_balance = account_set.getAccounts().iloc[account_index, 1]
            col_sel_vec = (current_forecast_row_df.columns == account_row.Name)
            #print('Setting '+account_row.Name+' to '+str(relevant_balance))
            current_forecast_row_df.iloc[0, col_sel_vec] = round(relevant_balance,2)

        # print('current_forecast_row_df post-update')
        # print(current_forecast_row_df.to_string())

        bal_string = ''
        for account_index2, account_row2 in account_set.getAccounts().iterrows():
            bal_string += '$' + str(account_row2.Balance) + ' '

        # log_in_color(logger,'green', 'debug', 'return this row:', self.log_stack_depth)
        # log_in_color(logger,'green', 'debug', current_forecast_row_df.to_string(), self.log_stack_depth)
        self.log_stack_depth -= 1
        log_in_color(logger,'cyan', 'debug', 'EXIT  executeMinimumPayments() ' + bal_string, self.log_stack_depth)
        #logger.debug('self.log_stack_depth -= 1')

        return current_forecast_row_df

    def getMinimumFutureAvailableBalances(self, account_set, forecast_df, date_YYYYMMDD):
        self.log_stack_depth += 1
        #logger.debug('self.log_stack_depth += 1')
        log_in_color(logger,'green', 'debug', 'ENTER getMinimumFutureAvailableBalances(date=' + str(date_YYYYMMDD) + ')', self.log_stack_depth)


        current_and_future_forecast_df = forecast_df[ [datetime.datetime.strptime(d,'%Y%m%d') >= datetime.datetime.strptime(date_YYYYMMDD,'%Y%m%d') for d in forecast_df.Date] ]
        #current_and_future_forecast_df = forecast_df[forecast_df.Date >= datetime.datetime.strptime(date_YYYYMMDD,'%Y%m%d')]

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

        log_in_color(logger,'magenta', 'debug', 'future_available_balances:' + str(future_available_balances), self.log_stack_depth)
        log_in_color(logger,'green', 'debug', 'EXIT getMinimumFutureAvailableBalances(date=' + str(date_YYYYMMDD) + ')', self.log_stack_depth)
        self.log_stack_depth -= 1
        #logger.debug('self.log_stack_depth -= 1')
        return future_available_balances

    def sync_account_set_w_forecast_day(self, account_set, forecast_df, date_YYYYMMDD):
        bal_string = ' '
        for index, row in account_set.getAccounts().iterrows():
            bal_string += '$'+str(row.Balance) + ' '
        log_in_color(logger,'cyan','debug','ENTER sync_account_set_w_forecast_day(date_YYYYMMDD='+str(date_YYYYMMDD)+')'+bal_string,self.log_stack_depth)
        # log_in_color(logger,'green','debug','Initial account_set:',self.log_stack_depth)
        # log_in_color(logger,'green', 'debug', account_set.getAccounts().to_string(), self.log_stack_depth)

        relevant_forecast_day = forecast_df[forecast_df.Date == date_YYYYMMDD]

        # log_in_color(logger,'green', 'debug', 'relevant forecast row:', self.log_stack_depth)
        # log_in_color(logger,'green', 'debug', relevant_forecast_day.to_string(), self.log_stack_depth)

        for account_index, account_row in account_set.getAccounts().iterrows():
            if (account_index + 1) == account_set.getAccounts().shape[1]:
                break

            # print('forecast_df.Date:')
            # print(forecast_df.Date)
            # print('d:')
            # print(d)

            row_sel_vec = (forecast_df.Date == date_YYYYMMDD)
            # print('row_sel_vec:')
            # print(row_sel_vec)

            assert sum(row_sel_vec) > 0

            relevant_balance = relevant_forecast_day.iat[0, account_index + 1]
            # log_in_color(logger,'green','debug','CASE 1 Setting '+account_row.Name+' to '+str(relevant_balance),self.log_stack_depth)
            account_set.accounts[account_index].balance = relevant_balance

        bal_string = ' '
        for index, row in account_set.getAccounts().iterrows():
            bal_string += '$' + str(row.Balance) + ' '
        log_in_color(logger,'cyan','debug','EXIT sync_account_set_w_forecast_day(date_YYYYMMDD='+str(date_YYYYMMDD)+')'+bal_string,self.log_stack_depth)
        return account_set

    #propagate into the future and raise exception if account boundaries are violated
    def propagateTransactionsIntoTheFuture(self, account_set_before_p2_plus_txn, forecast_df, date_string_YYYYMMDD):

        #log_in_color(logger,'cyan','debug','propagateTransactionsIntoTheFuture('+str(date_string_YYYYMMDD)+')')
        #log_in_color(logger,'cyan','debug','account_set_before_p2_plus_txn:')
        #log_in_color(logger,'cyan','debug',account_set_before_p2_plus_txn.getAccounts().iloc[:,0:2].T.to_string())


        account_set_after_p2_plus_txn = self.sync_account_set_w_forecast_day(copy.deepcopy(account_set_before_p2_plus_txn), forecast_df, date_string_YYYYMMDD)
        #log_in_color(logger,'cyan','debug','account_set_after_p2_plus_txn:')
        #log_in_color(logger,'cyan', 'debug', account_set_after_p2_plus_txn.getAccounts().iloc[:,0:2].T.to_string())

        # we apply the delta to all future rows
        account_deltas = account_set_after_p2_plus_txn.getAccounts().Balance - account_set_before_p2_plus_txn.getAccounts().Balance
        #log_in_color(logger,'cyan','debug','account_deltas:')
        #log_in_color(logger,'cyan','debug',account_deltas)

        i = 0
        for account_index, account_row in account_set_after_p2_plus_txn.getAccounts().iterrows():
            if forecast_df[forecast_df.Date > date_string_YYYYMMDD].empty:
                break

            if account_deltas[i] == 0:
                i += 1
                continue

            row_sel_vec = (forecast_df.Date > date_string_YYYYMMDD) #only future rows
            col_sel_vec = (forecast_df.columns == account_row.Name)

            forecast_df.loc[row_sel_vec, col_sel_vec] = forecast_df.loc[row_sel_vec, col_sel_vec].add(
                account_deltas[i])
            #log_in_color(logger,'cyan','info','post propogation forecast_df:')
            #log_in_color(logger,'cyan','info',forecast_df.iloc[:,0:8].to_string())

            # check account boundaries
            min_future_acct_bal = min(forecast_df.loc[row_sel_vec, col_sel_vec].values)
            max_future_acct_bal = max(forecast_df.loc[row_sel_vec, col_sel_vec].values)

            try:
                assert account_row.Min_Balance <= min_future_acct_bal
                assert account_row.Max_Balance >= max_future_acct_bal
            except AssertionError:
                raise ValueError("Account boundaries were violated")

            i += 1
        return forecast_df

    def updateProposedTransactionsBasedOnOtherSets(self, confirmed_df, proposed_df, deferred_df, skipped_df):
        # update remaining_unproposed_transactions_df based on modifications to other sets made during the last loop
        C = 'C:'+str(confirmed_df.shape[0])
        P = 'P:'+str(proposed_df.shape[0])
        D = 'D:'+str(deferred_df.shape[0])
        S = 'S:'+str(skipped_df.shape[0])
        log_in_color(logger,'cyan','info','ENTER updateProposedTransactionsBasedOnOtherSets( '+C+' '+P+' '+D+' '+S+' )', self.log_stack_depth)

        log_in_color(logger, 'cyan', 'info', 'confirmed_df:', self.log_stack_depth)
        log_in_color(logger, 'cyan', 'info',confirmed_df.to_string(), self.log_stack_depth)

        log_in_color(logger, 'cyan', 'info', 'proposed_df:', self.log_stack_depth)
        log_in_color(logger, 'cyan', 'info', proposed_df.to_string(), self.log_stack_depth)

        log_in_color(logger, 'cyan', 'info', 'deferred_df:', self.log_stack_depth)
        log_in_color(logger, 'cyan', 'info', deferred_df.to_string(), self.log_stack_depth)

        log_in_color(logger, 'cyan', 'info', 'skipped_df:', self.log_stack_depth)
        log_in_color(logger, 'cyan', 'info', skipped_df.to_string(), self.log_stack_depth)

        self.log_stack_depth += 1
        # log_in_color(logger, 'cyan', 'info', 'confirmed_df: '+str(confirmed_df))
        # log_in_color(logger, 'cyan', 'info', 'proposed_df: '+str(proposed_df))
        # log_in_color(logger, 'cyan', 'info', 'deferred_df: '+str(deferred_df))
        # log_in_color(logger, 'cyan', 'info', 'skipped_df: '+str(skipped_df))
        #log_in_color(logger, 'cyan', 'info', 'confirmed_df cols: '+str(confirmed_df.columns))
        #log_in_color(logger, 'cyan', 'info', 'proposed_df cols: '+str(proposed_df.columns))
        #log_in_color(logger, 'cyan', 'info', 'deferred_df cols: '+str(deferred_df.columns))
        #log_in_color(logger, 'cyan', 'info', 'skipped_df cols: '+str(skipped_df.columns))

        p_LJ_c = pd.merge(proposed_df, confirmed_df, on=['Date', 'Memo', 'Priority'])
        p_LJ_d = pd.merge(proposed_df, deferred_df, on=['Date', 'Memo', 'Priority'])
        p_LJ_s = pd.merge(proposed_df, skipped_df, on=['Date', 'Memo', 'Priority'])

        not_confirmed_sel_vec = (~proposed_df.index.isin(p_LJ_c))
        not_deferred_sel_vec = (~proposed_df.index.isin(p_LJ_d))
        not_skipped_sel_vec = (~proposed_df.index.isin(p_LJ_s))
        remaining_unproposed_sel_vec = (not_confirmed_sel_vec & not_deferred_sel_vec & not_skipped_sel_vec)
        remaining_unproposed_transactions_df = proposed_df[remaining_unproposed_sel_vec]

        ### this code is equivalent. todo Which is more performant?
        # not_confirmed_sel_vec = (~proposed_df.index.isin(confirmed_df.index))
        # not_deferred_sel_vec = (~proposed_df.index.isin(deferred_df.index))
        # not_skipped_sel_vec = (~proposed_df.index.isin(skipped_df.index))
        # remaining_unproposed_sel_vec = (not_confirmed_sel_vec & not_deferred_sel_vec & not_skipped_sel_vec)
        # remaining_unproposed_transactions_df = proposed_df[remaining_unproposed_sel_vec]

        self.log_stack_depth -= 1
        log_in_color(logger, 'cyan', 'info', 'EXIT updateProposedTransactionsBasedOnOtherSets',self.log_stack_depth)
        return remaining_unproposed_transactions_df

    def overwriteOGSatisficeInterestWhenAdditionalLoanPayment(self, forecast_df, date_string_YYYYMMDD, account_set):
        bal_string = ' '
        for index, row in account_set.getAccounts().iterrows():
            bal_string += '$' + str(row.Balance) + ' '
        log_in_color(logger,'cyan','debug','ENTER overwriteOGSatisficeInterestWhenAdditionalLoanPayment()'+bal_string,self.log_stack_depth)

        # logic to update interest accruals if principal balance has been reduced
        yesterday_date_string = (datetime.datetime.strptime(date_string_YYYYMMDD, '%Y%m%d') - datetime.timedelta(days=1)).strftime('%Y%m%d')
        yesterdays_values = self.sync_account_set_w_forecast_day(account_set, forecast_df, yesterday_date_string)
        forecast_row_w_new_interest_values = self.calculateInterestAccrualsForDay(yesterdays_values, forecast_df[forecast_df.Date == yesterday_date_string])  # returns only a forecast row
        forecast_row_w_new_interest_values.Date = date_string_YYYYMMDD
        forecast_row_w_new_interest_values.Memo = ''
        for i in range(0, forecast_row_w_new_interest_values.shape[1]):
            if not ': Interest' in forecast_row_w_new_interest_values.columns[i]:
                continue

            if forecast_df.loc[forecast_df.Date == date_string_YYYYMMDD, forecast_row_w_new_interest_values.columns[i]].iat[0] < \
                    forecast_row_w_new_interest_values.iloc[0, i]:
                pass
            else:
                forecast_df.loc[forecast_df.Date == date_string_YYYYMMDD, forecast_row_w_new_interest_values.columns[i]] = \
                forecast_row_w_new_interest_values.iloc[0, i]
                log_in_color(logger, 'cyan', 'debug','OVERWRITING INTEREST VALUE' + bal_string,self.log_stack_depth)

        bal_string = ' '
        for index, row in account_set.getAccounts().iterrows():
            bal_string += '$' + str(row.Balance) + ' '
        log_in_color(logger, 'cyan', 'debug', 'EXIT overwriteOGSatisficeInterestWhenAdditionalLoanPayment()'+bal_string,self.log_stack_depth)
        return forecast_df

    def assessPotentialOptimizations(self, forecast_df, account_set, memo_rule_set, confirmed_df, proposed_df, deferred_df, skipped_df, raise_satisfice_failed_exception):
        F = 'F:'+str(forecast_df.shape[0])
        C = 'C:'+str(confirmed_df.shape[0])
        P = 'P:'+str(proposed_df.shape[0])
        D = 'D:'+str(deferred_df.shape[0])
        S = 'S:'+str(skipped_df.shape[0])
        log_in_color(logger,'magenta','info','ENTER assessPotentialOptimizations( '+F+' '+C+' '+P+' '+D+' '+S+' )',self.log_stack_depth)
        self.log_stack_depth += 1
        all_days = forecast_df.Date #todo havent tested this, but forecast_df has been satisficed so it has all the dates

        log_in_color(logger, 'magenta', 'info', 'confirmed_df:', self.log_stack_depth)
        log_in_color(logger, 'magenta', 'info', confirmed_df.to_string(), self.log_stack_depth)

        log_in_color(logger, 'magenta', 'info', 'proposed_df:', self.log_stack_depth)
        log_in_color(logger, 'magenta', 'info', proposed_df.to_string(), self.log_stack_depth)

        log_in_color(logger, 'magenta', 'info', 'deferred_df:', self.log_stack_depth)
        log_in_color(logger, 'magenta', 'info', deferred_df.to_string(), self.log_stack_depth)

        log_in_color(logger, 'magenta', 'info', 'skipped_df:', self.log_stack_depth)
        log_in_color(logger, 'magenta', 'info', skipped_df.to_string(), self.log_stack_depth)

        # Schema is: Date, Priority, Amount, Memo, Deferrable, Partial_Payment_Allowed
        full_budget_schedule_df = pd.concat([confirmed_df, proposed_df, deferred_df, skipped_df])
        full_budget_schedule_df.reset_index(drop=True, inplace=True)

        unique_priority_indices = full_budget_schedule_df.Priority.unique()
        unique_priority_indices.sort()

        for priority_index in unique_priority_indices:
            if priority_index == 1:
                continue #because this was handled by satisfice

            for date_string_YYYYMMDD in all_days:
                if date_string_YYYYMMDD == self.start_date_YYYYMMDD:
                    continue  # first day is considered final
                log_in_color(logger, 'magenta', 'info', 'p' + str(priority_index) + ' ' + str(date_string_YYYYMMDD),self.log_stack_depth)

                remaining_unproposed_transactions_df = self.updateProposedTransactionsBasedOnOtherSets(confirmed_df, proposed_df, deferred_df, skipped_df)

                #todo idk if this is necessary
                account_set = self.sync_account_set_w_forecast_day(account_set, forecast_df, date_string_YYYYMMDD)

                #todo maybe this could be moved down? not sure
                account_set_before_p2_plus_txn = copy.deepcopy(account_set)

                #todo not sure if this is necessary
                account_set = self.sync_account_set_w_forecast_day(account_set, forecast_df, date_string_YYYYMMDD)

                forecast_df = self.overwriteOGSatisficeInterestWhenAdditionalLoanPayment(forecast_df, date_string_YYYYMMDD, account_set)

                #log_in_color(logger, 'yellow', 'info','proposed_df before eTFD:')
                #log_in_color(logger, 'yellow', 'info', proposed_df.to_string())

                forecast_df, confirmed_df, deferred_df, skipped_df = self.executeTransactionsForDay(account_set=account_set,
                                                                                                    forecast_df=forecast_df,
                                                                                                    date_YYYYMMDD=date_string_YYYYMMDD,
                                                                                                    memo_set=memo_rule_set,
                                                                                                    confirmed_df=confirmed_df,
                                                                                                    proposed_df=remaining_unproposed_transactions_df,
                                                                                                    deferred_df=deferred_df,
                                                                                                    skipped_df=skipped_df,
                                                                                                    priority_level=priority_index)

                #log_in_color(logger, 'yellow', 'info', 'proposed after eTFD:')
                #log_in_color(logger, 'yellow', 'info', proposed_df.to_string())

                account_set = self.sync_account_set_w_forecast_day(account_set, forecast_df, date_string_YYYYMMDD)

                # this is necessary to make balance deltas propoagate only once
                if raise_satisfice_failed_exception:

                    #regarding why the input params are what they are here:
                    # since the budget schedule does not have Account_From and Account_To, we infer which accounts were
                    # affected by comparing the before and after, hence this method accepts the prior and current state
                    # to modify forecast_df
                    forecast_df = self.propagateTransactionsIntoTheFuture(account_set_before_p2_plus_txn, forecast_df, date_string_YYYYMMDD)

        self.log_stack_depth -= 1
        log_in_color(logger, 'magenta', 'info', 'EXIT assessPotentialOptimizations() C:'+str(confirmed_df.shape[0])+' D:'+str(deferred_df.shape[0])+' S:'+str(skipped_df.shape[0]),self.log_stack_depth)
        return forecast_df, skipped_df, confirmed_df, deferred_df

    def cleanUpAfterFailedSatisfice(self, confirmed_df, proposed_df, deferred_df, skipped_df):

        #this logic takes everything that was not executed and adds it to skipped_df
        not_confirmed_sel_vec = [ ( datetime.datetime.strptime(d,'%Y%m%d') > datetime.datetime.strptime(self.end_date_YYYYMMDD,'%Y%m%d') ) for d in confirmed_df.Date ] #this is using an end date that has been moved forward, so it is > not >=
        not_confirmed_df = confirmed_df.loc[ not_confirmed_sel_vec ]
        new_deferred_df = proposed_df.loc[[not x for x in proposed_df.Deferrable]]
        skipped_df = pd.concat([skipped_df, not_confirmed_df, new_deferred_df, deferred_df]) #todo I added deferred_df without testing if that was correct

        #if it was confirmed before the date of failure, it stays confirmed
        confirmed_sel_vec = [ ( datetime.datetime.strptime(d,'%Y%m%d') <= datetime.datetime.strptime(self.end_date_YYYYMMDD,'%Y%m%d') ) for d in confirmed_df.Date ]
        confirmed_df = confirmed_df.loc[ confirmed_sel_vec ]

        #todo if satisfice fails, should deferred transactions stay deferred?
        deferred_df = proposed_df.loc[proposed_df.Deferrable]

        skipped_df.reset_index(inplace=True, drop=True)
        confirmed_df.reset_index(inplace=True, drop=True)
        deferred_df.reset_index(inplace=True, drop=True)

        return confirmed_df, deferred_df, skipped_df

    def satisfice(self, list_of_date_strings, confirmed_df, account_set, memo_rule_set, forecast_df, raise_satisfice_failed_exception ):
        log_in_color(logger,'cyan','info','ENTER satisfice()',self.log_stack_depth)
        self.log_stack_depth += 1
        all_days = list_of_date_strings #just rename it so it's more clear for the context

        for d in all_days:
            if d == self.start_date_YYYYMMDD:
                continue  # first day is considered final
            #print('d:'+str(d))
            try:

                #todo begin reinspection from here

                # print('forecast before eTFD:')
                # print(forecast_df.to_string())
                forecast_df, confirmed_df, deferred_df, skipped_df = \
                    self.executeTransactionsForDay(account_set=account_set,
                                                    forecast_df=forecast_df,
                                                    date_YYYYMMDD=d,
                                                    memo_set=memo_rule_set,
                                                    confirmed_df=confirmed_df,
                                                    proposed_df=confirmed_df.head(0), #no proposed txns in satisfice
                                                    deferred_df=confirmed_df.head(0), #no deferred txns in satisfice
                                                    skipped_df=confirmed_df.head(0),  #no skipped txns in satisfice
                                                    priority_level=1)
                #print('forecast after eTFD:')
                #print(forecast_df.to_string())

                #pre_sync = pd.DataFrame(account_set.getAccounts(),copy=True)
                account_set = self.sync_account_set_w_forecast_day(account_set, forecast_df, d)
                #assert pre_sync.to_string() == account_set.getAccounts().to_string() #the program is not reaching a minimum payments day so this check isnt working yet

                post_min_payments_row = self.executeMinimumPayments(account_set, forecast_df[forecast_df.Date == d])

                forecast_df[forecast_df.Date == d] = post_min_payments_row
                account_set = self.sync_account_set_w_forecast_day(account_set, forecast_df, d)
                forecast_df[forecast_df.Date == d] = self.calculateInterestAccrualsForDay(account_set, forecast_df[forecast_df.Date == d])  # returns only a forecast row
                #account_set = self.sync_account_set_w_forecast_day(account_set, forecast_df, d) #I don't think this is necessary

                #print('about to go to next loop iteration')
            except ValueError as e:
                if (re.search('.*Account boundaries were violated.*', str(e.args)) is not None) and not raise_satisfice_failed_exception:
                    self.end_date = datetime.datetime.strptime(d, '%Y%m%d') - datetime.timedelta(days=1)

                    self.log_stack_depth -= 1
                    log_in_color(logger, 'cyan', 'info', 'EXIT satisfice()', self.log_stack_depth)
                    return False
                else:
                    raise e

        self.log_stack_depth -= 1
        log_in_color(logger, 'cyan', 'info', 'EXIT satisfice()',self.log_stack_depth)
        return forecast_df #this is the satisfice_success = true

    #todo deferral cadence parameter
    def computeOptimalForecast(self, start_date_YYYYMMDD, end_date_YYYYMMDD, confirmed_df, proposed_df, deferred_df, skipped_df, account_set, memo_rule_set, raise_satisfice_failed_exception=True):
        log_in_color(logger,'cyan','info','ENTER computeOptimalForecast()',self.log_stack_depth)
        self.log_stack_depth += 1

        log_in_color(logger, 'cyan', 'info', 'confirmed_df:', self.log_stack_depth)
        log_in_color(logger, 'cyan', 'info', confirmed_df.to_string(), self.log_stack_depth)

        log_in_color(logger, 'cyan', 'info', 'proposed_df:', self.log_stack_depth)
        log_in_color(logger, 'cyan', 'info', proposed_df.to_string(), self.log_stack_depth)

        log_in_color(logger, 'cyan', 'info', 'deferred_df:', self.log_stack_depth)
        log_in_color(logger, 'cyan', 'info', deferred_df.to_string(), self.log_stack_depth)

        log_in_color(logger, 'cyan', 'info', 'skipped_df:', self.log_stack_depth)
        log_in_color(logger, 'cyan', 'info', skipped_df.to_string(), self.log_stack_depth)

        #I have done it this way because I was having problems with datetime format YYYYMMDD HH:MM:SS popping up when I didn't want it and causing bugs
        #a better programmer would handle datetime objects properly
        all_days = pd.date_range(datetime.datetime.strptime(start_date_YYYYMMDD, '%Y%m%d'),datetime.datetime.strptime(end_date_YYYYMMDD, '%Y%m%d'))
        all_days = [d.strftime('%Y%m%d') for d in all_days]

        #Schema is: Date, <a column for each account>, Memo
        forecast_df = self.getInitialForecastRow()

        #the top of mind thing about this method call is the raise_satisfice_failed_exception parameter.
        #This parameter is used to prevent exceptions from stopping the program when testing if a transaction is permitted.
        #The cOF method is only called with this parameter False by the top level of execution.
        #the return value will be forecast_df if successful, and False if not successful and raise_satisfice_failed_exception = False
        #if return value would have been False, but raise_satisfice_failed_exception = True, then an exception will be raised
        #print('before satisfice')
        satisfice_success = self.satisfice(all_days, confirmed_df, account_set, memo_rule_set, forecast_df, raise_satisfice_failed_exception )
        #print('after satisfice')

        if satisfice_success is not None:
            forecast_df = satisfice_success

            #Here, note that confirmed_df, proposed_df, deferred_df, skipped_df are all in the same state as theey entered this method
            #but are modified when they come back
            forecast_df, skipped_df, confirmed_df, deferred_df = self.assessPotentialOptimizations(forecast_df, account_set, memo_rule_set, confirmed_df, proposed_df, deferred_df, skipped_df,raise_satisfice_failed_exception)
        else:
            confirmed_df, deferred_df, skipped_df = self.cleanUpAfterFailedSatisfice(confirmed_df, proposed_df, deferred_df, skipped_df)

        self.log_stack_depth -= 1
        log_in_color(logger, 'cyan', 'info', 'EXIT computeOptimalForecast() C:'+str(confirmed_df.shape[0])+' D:'+str(deferred_df.shape[0])+' S:'+str(skipped_df.shape[0]), self.log_stack_depth)
        return [forecast_df, skipped_df, confirmed_df, deferred_df]

    #
    # #todo add deferral cadence parameter
    # def computeOptimalForecast_v0(self, start_date_YYYYMMDD, end_date_YYYYMMDD, confirmed_df, proposed_df, deferred_df, skipped_df, account_set, memo_rule_set, raise_satisfice_failed_exception=True):
    #     """
    #     One-description.
    #
    #     Multiple line description.
    #
    #     :param start_date_YYYYMMDD:
    #     :param end_date_YYYYMMDD:
    #     :param confirmed_df:
    #     :param proposed_df:
    #     :param deferred_df:
    #     :param skipped_df:
    #     :param account_set:
    #     :param memo_rule_set:
    #     :param raise_satisfice_failed_exception:
    #     :return:
    #     """
    #
    #     C = confirmed_df.shape[0]
    #     P = proposed_df.shape[0]
    #     D = deferred_df.shape[0]
    #     S = skipped_df.shape[0]
    #     T = C + P + D + S
    #     row_count_string = ' C:' + str(C) + '  P:' + str(P) + '  D:' + str(D) + '  S:' + str(S) + '  T:' + str(T)
    #
    #     bal_string = '  '
    #     for account_index, account_row in account_set.getAccounts().iterrows():
    #         bal_string += '$' + str(account_row.Balance) + ' '
    #
    #     self.log_stack_depth += 1
    #     #logger.debug('self.log_stack_depth += 1')
    #     log_in_color(logger,'green', 'debug', 'ENTER computeOptimalForecast() ' + str(raise_satisfice_failed_exception) + ' ' + str(row_count_string) + str(bal_string), self.log_stack_depth)
    #
    #     full_budget_schedule_df = pd.concat([confirmed_df, proposed_df, deferred_df, skipped_df])
    #     full_budget_schedule_df.reset_index(drop=True, inplace=True)
    #     try:
    #         assert full_budget_schedule_df.shape[0] == full_budget_schedule_df.drop_duplicates().shape[0]
    #     except Exception as e:
    #         log_in_color(logger,'red', 'debug', 'a duplicate memo was detected. This is filtered for in ExpenseForecast(), so we know that this was caused by internal logic.')
    #         log_in_color(logger,'red', 'debug', full_budget_schedule_df.to_string())
    #         raise e
    #
    #     failed_to_satisfice_flag = False
    #
    #     # log_in_color(logger,'cyan', 'debug', 'Full budget schedule:', self.log_stack_depth)
    #     # log_in_color(logger,'cyan', 'debug', full_budget_schedule_df.to_string(), self.log_stack_depth)
    #     log_in_color(logger,'cyan', 'debug', 'computeOptimalForecast()', self.log_stack_depth)
    #     log_in_color(logger,'cyan', 'debug', 'Confirmed: ', self.log_stack_depth)
    #     log_in_color(logger,'cyan', 'debug', confirmed_df.to_string(), self.log_stack_depth)
    #     log_in_color(logger,'cyan', 'debug', 'Proposed: ', self.log_stack_depth)
    #     log_in_color(logger,'cyan', 'debug', proposed_df.to_string(), self.log_stack_depth)
    #     log_in_color(logger,'cyan', 'debug', 'Deferred: ', self.log_stack_depth)
    #     log_in_color(logger,'cyan', 'debug', deferred_df.to_string(), self.log_stack_depth)
    #
    #     if self.log_stack_depth > 20:
    #         raise ValueError("stack depth greater than 20. smells like infinite recursion to me. take a look buddy")
    #
    #     if self.log_stack_depth < 0:
    #         raise ValueError("uneven stack depth. It is likely there is as semantic error upstream. ")
    #
    #     all_days = pd.date_range(datetime.datetime.strptime(start_date_YYYYMMDD, '%Y%m%d'), datetime.datetime.strptime(end_date_YYYYMMDD, '%Y%m%d'))
    #     all_days = [ d.strftime('%Y%m%d') for d in all_days ]
    #     forecast_df = self.getInitialForecastRow()
    #     #budget_schedule_df = budget_set.getBudgetSchedule(start_date_YYYYMMDD, end_date_YYYYMMDD)
    #
    #     for d in all_days:
    #         if d == self.start_date_YYYYMMDD:
    #             continue  # first day is considered final
    #
    #         bal_string = ' '
    #         for account_index, account_row in account_set.getAccounts().iterrows():
    #             bal_string += '$' + str(account_row.Balance) + ' '
    #
    #         #log_in_color(logger,'green', 'info', 'BEGIN SATISFICE ' + str(d.strftime('%Y-%m-%d')) + bal_string, self.log_stack_depth)
    #
    #         if not raise_satisfice_failed_exception:  # to report progress
    #             try:
    #                 max_priority = max(full_budget_schedule_df.Priority.unique())
    #             except:
    #                 max_priority = 1
    #             log_in_color(logger,'white', 'info', 'p' + str(1) + ' / ' + str(max_priority) + ' ' + d)
    #
    #         # print('SATISFICE BEFORE TXN:'+str(forecast_df))
    #         try:
    #
    #             not_confirmed_sel_vec = ( ~proposed_df.index.isin(confirmed_df.index) )
    #             not_deferred_sel_vec = ( ~proposed_df.index.isin(deferred_df.index) )
    #             not_skipped_sel_vec = ( ~proposed_df.index.isin(skipped_df.index) )
    #             remaining_unproposed_sel_vec = ( not_confirmed_sel_vec & not_deferred_sel_vec & not_skipped_sel_vec )
    #             # print('!C: '+str(not_confirmed_sel_vec))
    #             # print('!D: '+str(not_deferred_sel_vec))
    #             # print('!S: '+str(not_skipped_sel_vec))
    #             # print(' P: '+str(remaining_unproposed_sel_vec))
    #             remaining_unproposed_transactions_df = proposed_df[ remaining_unproposed_sel_vec ]
    #
    #
    #
    #             forecast_df, skipped_df, confirmed_df, deferred_df = self.executeTransactionsForDay_v0(account_set, forecast_df=forecast_df, date_YYYYMMDD=d,
    #                                                                                                 memo_set=memo_rule_set, confirmed_df=confirmed_df, proposed_df=remaining_unproposed_transactions_df,
    #                                                                                                 deferred_df=deferred_df, skipped_df=skipped_df, priority_level=1,
    #                                                                                                 allow_skip_and_defer=False,
    #                                                                                                 allow_partial_payments=False)  # this is the implementation of satisfice
    #
    #             # print('SATISFICE AFTER TXN:'+str(forecast_df))
    #
    #             account_set = self.sync_account_set_w_forecast_day(account_set, forecast_df, d)
    #             post_min_payments_row = self.executeMinimumPayments(account_set, forecast_df[forecast_df.Date == d])
    #
    #             # print('post_min_payments_row:')
    #             # print(post_min_payments_row)
    #
    #             forecast_df[forecast_df.Date == d] = post_min_payments_row
    #             account_set = self.sync_account_set_w_forecast_day(account_set, forecast_df, d)
    #             forecast_df[forecast_df.Date == d] = self.calculateInterestAccrualsForDay(account_set, forecast_df[forecast_df.Date == d])  # returns only a forecast row
    #             account_set = self.sync_account_set_w_forecast_day(account_set, forecast_df, d)
    #
    #
    #         except ValueError as e:
    #
    #             # this method is allowed one account boundary exception. this is the case where satisfice doesn't make it to the end date
    #             # we move the end date closer to cope. the new row did not get appended
    #             if (re.search('.*Account boundaries were violated.*', str(e.args)) is not None) and not raise_satisfice_failed_exception:
    #                 self.end_date = datetime.datetime.strptime(d, '%Y%m%d') - datetime.timedelta(days=1)
    #                 failed_to_satisfice_flag = True
    #                 log_in_color(logger,'green', 'debug', 'FAILED TO SATISFICE. Not raising an exception per parameters.')
    #                 log_in_color(logger,'green', 'info', 'BEGIN SATISFICE ' + str(d) + bal_string, self.log_stack_depth)
    #                 break
    #             else:
    #                 raise e
    #
    #         #log_in_color(logger,'green', 'info', 'END SATISFICE ' + str(d.strftime('%Y-%m-%d')) + bal_string, self.log_stack_depth)
    #         #log_in_color(logger,'white','debug','########### SATISFICE ' + row_count_string + ' ###########################################################################################################',self.log_stack_depth)
    #         #log_in_color(logger,'white','debug',forecast_df.to_string(),self.log_stack_depth)
    #         #log_in_color(logger,'white','debug','##########################################################################################################################################################',self.log_stack_depth)
    #
    #     if not failed_to_satisfice_flag:
    #         unique_priority_indices = full_budget_schedule_df.Priority.unique()
    #         unique_priority_indices.sort()
    #
    #         for priority_index in unique_priority_indices:
    #             if priority_index == 1:
    #                 continue
    #
    #             for d in all_days:
    #                 if d == self.start_date_YYYYMMDD:
    #                     continue  # first day is considered final
    #
    #                 if not raise_satisfice_failed_exception: #to report progress
    #                     log_in_color(logger,'white','info','p' + str(priority_index) + ' / ' + str(max(unique_priority_indices)) + ' ' + str(d))
    #
    #                 C = confirmed_df.shape[0]
    #                 P = proposed_df.shape[0]
    #                 D = deferred_df.shape[0]
    #                 S = skipped_df.shape[0]
    #                 T = C + P + D + S
    #                 row_count_string = ' C:' + str(C) + '  P:' + str(P) + '  D:' + str(D) + '  S:' + str(S) + '  T:' + str(T)
    #
    #                 bal_string = '  '
    #                 for account_index, account_row in account_set.getAccounts().iterrows():
    #                     bal_string += '$' + str(account_row.Balance) + ' '
    #
    #                 #log_in_color(logger,'green', 'info', 'OPTIMIZE ' + str(priority_index) + ' d:' + str(d) + ' ' + str(row_count_string) + str(bal_string), self.log_stack_depth)
    #
    #                 account_set = self.sync_account_set_w_forecast_day(account_set, forecast_df, d)
    #
    #                 p_LJ_c = pd.merge(proposed_df, confirmed_df, on=['Date','Memo','Priority'])
    #                 p_LJ_d = pd.merge(proposed_df, deferred_df, on=['Date','Memo','Priority'])
    #                 p_LJ_s = pd.merge(proposed_df, skipped_df, on=['Date','Memo','Priority'])
    #
    #                 # print('p_LJ_c:')
    #                 # print(p_LJ_c.to_string())
    #                 # print('p_LJ_d:')
    #                 # print(p_LJ_d.to_string())
    #                 # print('p_LJ_s:')
    #                 # print(p_LJ_s.to_string())
    #
    #                 not_confirmed_sel_vec = (~proposed_df.index.isin( p_LJ_c ))
    #                 not_deferred_sel_vec = (~proposed_df.index.isin( p_LJ_d ))
    #                 not_skipped_sel_vec = (~proposed_df.index.isin( p_LJ_s ))
    #                 remaining_unproposed_sel_vec = (not_confirmed_sel_vec & not_deferred_sel_vec & not_skipped_sel_vec)
    #
    #                 # print('!C: '+str(not_confirmed_sel_vec))
    #                 # print('!D: '+str(not_deferred_sel_vec))
    #                 # print('!S: '+str(not_skipped_sel_vec))
    #                 # print(' P: '+str(remaining_unproposed_sel_vec))
    #                 remaining_unproposed_transactions_df = proposed_df[remaining_unproposed_sel_vec]
    #
    #                 # log_in_color(logger,'cyan', 'debug', 'Confirmed: ', self.log_stack_depth)
    #                 # log_in_color(logger,'cyan', 'debug', confirmed_df.to_string(), self.log_stack_depth + 1)
    #                 # log_in_color(logger,'cyan', 'debug', 'Proposed: ', self.log_stack_depth)
    #                 # log_in_color(logger,'cyan', 'debug', proposed_df.to_string(), self.log_stack_depth + 1)
    #                 # log_in_color(logger,'cyan', 'debug', 'Deferred: ', self.log_stack_depth)
    #                 # log_in_color(logger,'cyan', 'debug', deferred_df.to_string(), self.log_stack_depth + 1)
    #                 # log_in_color(logger,'cyan', 'debug', 'Skipped: ', self.log_stack_depth)
    #                 # log_in_color(logger,'cyan', 'debug', skipped_df.to_string(), self.log_stack_depth + 1)
    #                 # log_in_color(logger,'cyan', 'debug', 'Remaining unproposed: ', self.log_stack_depth)
    #                 # log_in_color(logger,'cyan', 'debug', remaining_unproposed_transactions_df.to_string(), self.log_stack_depth + 1)
    #
    #                 account_set_before_p2_plus_txn = copy.deepcopy(account_set)
    #
    #                 # print('pre-txn state of forecast (cOF):'+str(raise_satisfice_failed_exception))
    #                 # print(forecast_df.to_string())
    #
    #
    #
    #                 #only for interest accounts, we will overwrite todays value based on the values from yesterday
    #                 #this is needed because future days would have interest added based on the OG amount despite payment if we did not do this
    #                 yesterday_date_string = (datetime.datetime.strptime(d,'%Y%m%d') - datetime.timedelta(days = 1)).strftime('%Y%m%d')
    #                 yesterdays_values = self.sync_account_set_w_forecast_day( account_set, forecast_df, yesterday_date_string )
    #                 forecast_row_w_new_interest_values = self.calculateInterestAccrualsForDay(yesterdays_values, forecast_df[forecast_df.Date == yesterday_date_string])  # returns only a forecast row
    #                 forecast_row_w_new_interest_values.Date = d
    #                 forecast_row_w_new_interest_values.Memo = ''
    #                 #print('forecast_row_w_new_interest_values:')
    #                 #print(forecast_row_w_new_interest_values.to_string())
    #
    #                 #print('forecast_row_w_new_interest_values:')
    #                 #print(forecast_row_w_new_interest_values.to_string())
    #
    #                 for i in range(0,forecast_row_w_new_interest_values.shape[1]):
    #                     if not ': Interest' in forecast_row_w_new_interest_values.columns[i]:
    #                         continue
    #                     #print(str(i))
    #                     #print(str(forecast_df.loc[forecast_df.Date == d, i]) + ' -> ' + str(forecast_row_w_new_interest_values.iloc[0,i]))
    #
    #                     #if this payment is on the same day as a minimum payment, then we want to take that into account
    #                     #therefore, if todays value is lower than yesterdays value, keep it, else keep the new higher value
    #                     #this would not work if the incremental interest was greater than the minimum payment !!! #todo address this
    #
    #                     # print('forecast_df.loc[forecast_df.Date == d, forecast_row_w_new_interest_values.columns[i]].iat[0]:')
    #                     # print(forecast_df.loc[forecast_df.Date == d, forecast_row_w_new_interest_values.columns[i]].iat[0] )
    #                     # print('forecast_row_w_new_interest_values.iloc[0,i]')
    #                     # print(forecast_row_w_new_interest_values.iloc[0,i])
    #
    #                     if forecast_df.loc[forecast_df.Date == d, forecast_row_w_new_interest_values.columns[i]].iat[0] < forecast_row_w_new_interest_values.iloc[0,i]:
    #                         pass
    #                     else:
    #                         forecast_df.loc[forecast_df.Date == d, forecast_row_w_new_interest_values.columns[i]] = forecast_row_w_new_interest_values.iloc[0,i]
    #                 #print('forecast_df')
    #                 #print(forecast_df.to_string())
    #
    #                 forecast_df, skipped_df, confirmed_df, deferred_df = self.executeTransactionsForDay_v0(account_set,
    #                                                                                                     forecast_df=forecast_df,
    #                                                                                                     date_YYYYMMDD=d,
    #                                                                                                     memo_set=memo_rule_set,
    #                                                                                                     confirmed_df=confirmed_df,
    #                                                                                                     proposed_df=remaining_unproposed_transactions_df,
    #                                                                                                     deferred_df=deferred_df,
    #                                                                                                     skipped_df=skipped_df,
    #                                                                                                     priority_level=priority_index,
    #                                                                                                     allow_skip_and_defer=True,
    #                                                                                                     allow_partial_payments=True)
    #
    #
    #                 account_set = self.sync_account_set_w_forecast_day(account_set, forecast_df, d)
    #
    #
    #                 account_set_after_p2_plus_txn = copy.deepcopy(account_set)
    #
    #                 #this branch means that roll-forward only happens during the hypothetical. Otherwise it would happen twice
    #                 if raise_satisfice_failed_exception:
    #                     # print('post-txn (pre-roll-forward) state of forecast (cOF): '+str(raise_satisfice_failed_exception))
    #                     # print(forecast_df.to_string())
    #
    #                     #we apply the delta to all future rows
    #                     account_deltas = account_set_after_p2_plus_txn.getAccounts().Balance - account_set_before_p2_plus_txn.getAccounts().Balance
    #                     # print('account_deltas:')
    #                     # print(account_deltas)
    #
    #                     i = 0
    #                     for account_index, account_row in account_set.getAccounts().iterrows():
    #                         # print('i:'+str(i))
    #                         # print('account_row:'+str(account_row))
    #                         # print('forecast_df:')
    #                         # print(forecast_df.to_string())
    #                         if forecast_df[forecast_df.Date > d].empty:
    #                             break
    #
    #                         if account_deltas[i] == 0:
    #                             i += 1
    #                             continue
    #
    #                         # print('forecast_df before roll-forward:')
    #                         # print(forecast_df.to_string())
    #
    #                         row_sel_vec = ( forecast_df.Date > d )
    #                         col_sel_vec = ( forecast_df.columns == account_row.Name )
    #
    #                         forecast_df.loc[row_sel_vec, col_sel_vec] = forecast_df.loc[row_sel_vec, col_sel_vec].add(account_deltas[i])
    #
    #                         #check account boundaries
    #                         min_future_acct_bal = min(forecast_df.loc[row_sel_vec, col_sel_vec].values)
    #                         max_future_acct_bal = max(forecast_df.loc[row_sel_vec, col_sel_vec].values)
    #
    #                         try:
    #                             # print('forecast_df.loc[row_sel_vec, col_sel_vec].values:')
    #                             # print(forecast_df.loc[row_sel_vec, col_sel_vec].values)
    #                             # print('min_future_acct_bal:')
    #                             # print(min_future_acct_bal)
    #                             # print('max_future_acct_bal:')
    #                             # print(max_future_acct_bal)
    #                             assert account_row.Min_Balance <= min_future_acct_bal
    #                             assert account_row.Max_Balance >= max_future_acct_bal
    #                         except AssertionError:
    #                             raise ValueError("Account boundaries were violated")
    #
    #                         i += 1
    #
    #                     # print('post-roll-forward state of forecast (cOF):'+str(raise_satisfice_failed_exception))
    #                     # print(forecast_df.to_string())
    #
    #                 #log_in_color(logger,'white','debug','########### OPTIMIZE ' + str(priority_index) + ' ' + row_count_string + ' ###########################################################################################################',self.log_stack_depth)
    #                 #log_in_color(logger,'white','debug',forecast_df.to_string(),self.log_stack_depth)
    #                 #log_in_color(logger,'white','debug','##########################################################################################################################################################',self.log_stack_depth)
    #
    #     if failed_to_satisfice_flag:
    #         log_in_color(logger,'red', 'error', 'Forecast id: ' + str(self.unique_id))
    #         log_in_color(logger,'red','error','Last day successfully computed: '+str(d))
    #
    #         not_confirmed_sel_vec = [ ( datetime.datetime.strptime(d,'%Y%m%d') > datetime.datetime.strptime(self.end_date_YYYYMMDD,'%Y%m%d') ) for d in confirmed_df.Date ] #this is using an end date that has been moved forward, so it is > not >=
    #
    #         not_confirmed_df = confirmed_df.loc[ not_confirmed_sel_vec ]
    #         new_deferred_df = proposed_df.loc[[not x for x in proposed_df.Deferrable]]
    #         skipped_df = pd.concat([skipped_df, not_confirmed_df, new_deferred_df])
    #
    #         confirmed_sel_vec = [ ( datetime.datetime.strptime(d,'%Y%m%d') <= datetime.datetime.strptime(self.end_date_YYYYMMDD,'%Y%m%d') ) for d in confirmed_df.Date ]
    #         confirmed_df = confirmed_df.loc[ confirmed_sel_vec ]
    #
    #         deferred_df = proposed_df.loc[proposed_df.Deferrable]
    #
    #         skipped_df.reset_index(inplace=True, drop=True)
    #         confirmed_df.reset_index(inplace=True, drop=True)
    #         deferred_df.reset_index(inplace=True, drop=True)
    #
    #     # print('Final state of forecast (cOF):'+str(raise_satisfice_failed_exception))
    #     # print(forecast_df.to_string())
    #
    #     C = confirmed_df.shape[0]
    #     P = proposed_df.shape[0]
    #     D = deferred_df.shape[0]
    #     S = skipped_df.shape[0]
    #     T = C + P + D + S
    #     row_count_string = ' C:' + str(C) + '  P:' + str(P) + '  D:' + str(D) + '  S:' + str(S) + '  T:' + str(T)
    #
    #     bal_string = '  '
    #     for account_index, account_row in account_set.getAccounts().iterrows():
    #         bal_string += '$' + str(round(account_row.Balance,2)) + ' '
    #
    #     log_in_color(logger,'green', 'debug', 'EXIT computeOptimalForecast() ' + row_count_string + str(bal_string), self.log_stack_depth)
    #     self.log_stack_depth -= 1
    #     #logger.debug('self.log_stack_depth -= 1')
    #     return [forecast_df, skipped_df, confirmed_df, deferred_df]

    def evaluateAccountMilestone(self,account_name,min_balance,max_balance):
        log_in_color(logger,'yellow','debug','ENTER evaluateAccountMilestone('+str(account_name)+','+str(min_balance)+','+str(max_balance)+')')
        account_info = self.initial_account_set.getAccounts()
        account_base_names = [ a.split(':')[0] for a in account_info.Name ]
        row_sel_vec = [ a == account_name for a in account_base_names]

        relevant_account_info_rows_df = account_info[row_sel_vec]

        #this df should be either 1 or 2 rows, but have same account type either way
        try:
            assert relevant_account_info_rows_df.Name.unique().shape[0] == 1
        except Exception as e:
            print(e)

        if relevant_account_info_rows_df.shape[0] == 1: #case for checking and savings
            col_sel_vec = self.forecast_df.columns == relevant_account_info_rows_df.head(1)['Name'].iat[0]
            col_sel_vec[0] = True
            relevant_time_series_df = self.forecast_df.iloc[:, col_sel_vec]
        elif relevant_account_info_rows_df.shape[0] == 2:  # case for credit and loan
            col_sel_vec = self.forecast_df.columns == relevant_account_info_rows_df.head(1)['Name'].iat[0]
            col_sel_vec[0] = True

            relevant_time_series_df = self.forecast_df.iloc[:, col_sel_vec]
        else:
            raise ValueError("undefined edge case in ExpenseForecast::evaulateAccountMilestone""")

        last_value = relevant_time_series_df.tail(1).iat[0,1]
        #if the last day of the forecast does not satisfy account bounds, then none of the days of the forecast qualify
        if not (( min_balance <= last_value ) & ( last_value <= max_balance )):
            log_in_color(logger,'yellow', 'debug','EXIT evaluateAccountMilestone(' + str(account_name) + ',' + str(min_balance) + ',' + str(max_balance) + ')')
            return None

        #if the code reaches this point, then the milestone was for sure reached.
        #We can find the first day that qualifies my reverseing the sequence and returning the day before the first day that doesnt qualify
        relevant_time_series_df = relevant_time_series_df.loc[::-1]
        last_qualifying_date = relevant_time_series_df.head(1).Date
        for index, row in relevant_time_series_df.iterrows():
            # print('row:')
            # print(row)
            # print(row.iloc[1])
            if (( min_balance <= row.iloc[1] ) & ( row.iloc[1] <= max_balance )):
                last_qualifying_date = row.Date
            else:
                break
        log_in_color(logger,'yellow', 'debug','EXIT evaluateAccountMilestone(' + str(account_name) + ',' + str(min_balance) + ',' + str(max_balance) + ')')
        return last_qualifying_date

    def evaulateMemoMilestone(self,memo_regex):
        log_in_color(logger,'yellow', 'debug','ENTER evaluateMemoMilestone(' + str(memo_regex)+')')
        for forecast_index, forecast_row in self.forecast_df.iterrows():
            m = re.search(memo_regex,forecast_row.Memo)
            if m is not None:
                log_in_color(logger,'yellow', 'debug', 'EXIT evaluateMemoMilestone(' + str(memo_regex) + ')')
                return forecast_row.Date
        log_in_color(logger,'yellow', 'debug', 'EXIT evaluateMemoMilestone(' + str(memo_regex) + ')')
        return None

    def evaluateCompositeMilestone(self,list_of_account_milestones,list_of_memo_milestones):
        #list_of_account_milestones is lists of 3-tuples that are (string,float,float) for parameters

        #composite milestones may contain some milestones that arent listed in the composite #todo as of 2023-04-25

        num_of_acct_milestones = len(list_of_account_milestones)
        num_of_memo_milestones = len(list_of_memo_milestones)
        account_milestone_dates = []
        memo_milestone_dates = []

        for i in range(0,num_of_acct_milestones):
            account_milestone = list_of_account_milestones[i]
            am_result = self.evaluateAccountMilestone(account_milestone.account_name,account_milestone.min_balance,account_milestone.max_balance)
            if am_result is None: #disqualified immediately because success requires ALL
                return None
            account_milestone_dates.append(am_result)

        for i in range(0,num_of_memo_milestones):
            memo_milestone = list_of_memo_milestones[i]
            mm_result = self.evaulateMemoMilestone(memo_milestone.memo_regex)
            if mm_result is None:  # disqualified immediately because success requires ALL
                return None
            memo_milestone_dates.append(mm_result)

        return max(account_milestone_dates + memo_milestone_dates)

    def to_json(self):
        """
        Returns a JSON string representing the ExpenseForecast object.

        #todo ExpenseForecast.to_json() say what the columns are

        :return:
        """

        JSON_string = '{'

        unique_id_string = "\"unique_id\":\""+self.unique_id+"\",\n"
        start_ts_string = "\"start_ts\":\""+self.start_ts+"\",\n"
        end_ts_string = "\"end_ts\":\""+self.end_ts+"\",\n"

        start_date_string = "\"start_date\":"+self.start_date_YYYYMMDD+",\n"
        end_date_string = "\"end_date\":"+self.end_date_YYYYMMDD+",\n"

        memo_rule_set_string = "\"initial_memo_rule_set\":"+self.initial_memo_rule_set.to_json()+","
        initial_account_set_string = "\"initial_account_set\":"+self.initial_account_set.to_json()+","
        initial_budget_set_string = "\"initial_budget_set\":"+self.initial_budget_set.to_json()+","

        normalized_forecast_df_JSON_string = self.forecast_df.to_json(orient='records',date_format='iso')#.replace('\'','"')
        normalized_skipped_df_JSON_string = self.skipped_df.to_json(orient='records',date_format='iso')#.replace('\'','"')
        normalized_confirmed_df_JSON_string = self.confirmed_df.to_json(orient='records',date_format='iso')#.replace('\'','"')
        normalized_deferred_df_JSON_string = self.deferred_df.to_json(orient='records',date_format='iso')#.replace('\'','"')

        forecast_df_string = "\"forecast_df\":"+normalized_forecast_df_JSON_string+",\n"
        skipped_df_string = "\"skipped_df\":"+normalized_skipped_df_JSON_string+",\n"
        confirmed_df_string = "\"confirmed_df\":"+normalized_confirmed_df_JSON_string+",\n"
        deferred_df_string = "\"deferred_df\":"+normalized_deferred_df_JSON_string+",\n"

        JSON_string += unique_id_string
        JSON_string += start_ts_string
        JSON_string += end_ts_string
        JSON_string += start_date_string
        JSON_string += end_date_string
        JSON_string += memo_rule_set_string
        JSON_string += initial_account_set_string
        JSON_string += initial_budget_set_string
        JSON_string += forecast_df_string
        JSON_string += skipped_df_string
        JSON_string += confirmed_df_string
        JSON_string += deferred_df_string

        account_milestone_string = "{"
        for i in range(0,len(self.account_milestone_results__list)):
            a = self.account_milestone_results__list[i]
            account_milestone_string += '"'+str(a[0])+'":"'+str(a[1])+'"'
            if i != (len(self.account_milestone_results__list)-1):
                account_milestone_string+=","
        account_milestone_string+="}"

        memo_milestone_string = "{"
        for i in range(0, len(self.memo_milestone_results__list)):
            m = self.memo_milestone_results__list[i]
            memo_milestone_string += '"'+str(m[0])+'":"'+str(m[1])+'"'
            if i != (len(self.memo_milestone_results__list) - 1):
                memo_milestone_string += ","
        memo_milestone_string += "}"

        composite_milestone_string = "{"
        for i in range(0, len(self.composite_milestone_results__list)):
            c = self.composite_milestone_results__list[i]
            composite_milestone_string += '"'+str(c[0])+'":"'+str(a[1])+'"'
            if i != (len(self.composite_milestone_results__list) - 1):
                composite_milestone_string += ","
        composite_milestone_string += "}"

        JSON_string += "\"milestone_set\":"+self.milestone_set.to_json()+",\n"
        JSON_string += "\"account_milestone_results\":"+account_milestone_string+",\n"
        JSON_string += "\"memo_milestone_results\":"+memo_milestone_string+",\n"
        JSON_string += "\"composite_milestone_results\":"+composite_milestone_string

        JSON_string += '}'

        return JSON_string

    def to_html(self):
        return self.forecast_df.to_html()

    def compute_forecast_difference(self, forecast_df, forecast2_df, label='forecast_difference', make_plots=False, plot_directory='.', return_type='dataframe', require_matching_columns=False,
                                    require_matching_date_range=False, append_expected_values=False, diffs_only=False):

        forecast_df['Date'] = forecast_df.Date.apply(lambda x: datetime.datetime.strptime(x,'%Y%m%d'),0)

        forecast_df = forecast_df.reindex(sorted(forecast_df.columns), axis=1)
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
                print('# Check Number of Columns:')
                print('self.forecast_df.shape[1]:'+str(self.forecast_df.shape[1]))
                print('forecast2_df.shape[1]....:'+str(forecast2_df.shape[1]))
                print('')
                print('# Check Column Names:')
                print('set(self.forecast_df.columns):'+str(set(self.forecast_df.columns) ))
                print('set(forecast2_df.columns)....:'+str(set(forecast2_df.columns)))
                print('')
                raise e

        if require_matching_date_range:
            try:
                assert min(forecast_df['Date']) == min(forecast2_df['Date'])
                assert max(forecast_df['Date']) == max(forecast2_df['Date'])
            except Exception as e:
                print('ERROR: ATTEMPTED TO TAKE DIFF OF FORECASTS WITH DIFFERENT DATE RANGE')
                print('LHS: ' + str(min(forecast_df['Date'])) + ' - ' + str(max(forecast_df['Date'])))
                print('RHS: ' + str(min(forecast2_df['Date'])) + ' - ' + str(max(forecast2_df['Date'])))
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
            pass  # todo draw plots

        return_df = return_df.reindex(sorted(return_df.columns), axis=1)

        return return_df

    def getMilestoneResultsDF(self):
        if not hasattr(self,'forecast_df'):
            print('Forecast has not been run, so there are no results.')
            return

        milestone_results_df = pd.DataFrame({'Milestone_Name':[],
                                             'Result_Date':[]})

        for a in self.account_milestone_results__list:
            milestone_results_df = pd.concat([milestone_results_df,
                                              pd.DataFrame({'Milestone_Name': [a[0]],
                                                            'Result_Date': [a[1]]})
                                              ])

        for m in self.memo_milestone_results__list:
            milestone_results_df = pd.concat([milestone_results_df,
                                              pd.DataFrame({'Milestone_Name': [m[0]],
                                                            'Result_Date': [m[1]]})
                                              ])

        for c in self.composite_milestone_results__list:
            milestone_results_df = pd.concat([milestone_results_df,
                                              pd.DataFrame({'Milestone_Name': [c[0]],
                                                            'Result_Date': [c[1]]})
                                              ])

        return milestone_results_df

    def to_excel(self,path):

        #first page, run parameters
        account_set_df = self.initial_account_set.getAccounts()
        budget_set_df = self.initial_budget_set.getBudgetItems()
        memo_rule_set_df = self.initial_memo_rule_set.getMemoRules()
        choose_one_set_df = pd.DataFrame() #todo
        account_milestones_df = self.milestone_set.getAccountMilestonesDF()
        memo_milestones_df = self.milestone_set.getMemoMilestonesDF()
        composite_milestones__list = self.milestone_set.getCompositeMilestones_lists()
        composite_account_milestones_df = composite_milestones__list[0]
        composite_memo_milestones_df = composite_milestones__list[1]

        config_df = self.getConfigDF()
        run_info_df = self.getRunInfoDF()

        with pd.ExcelWriter(path, engine='openpyxl') as writer:
            account_set_df.to_excel(writer, sheet_name='AccountSet',index=False)
            budget_set_df.to_excel(writer, sheet_name='BudgetSet',index=False)
            memo_rule_set_df.to_excel(writer, sheet_name='MemoRuleSet',index=False)
            choose_one_set_df.to_excel(writer, sheet_name='ChooseOneSet',index=False)
            account_milestones_df.to_excel(writer, sheet_name='AccountMilestones',index=False)
            memo_milestones_df.to_excel(writer, sheet_name='MemoMilestones',index=False)
            composite_account_milestones_df.to_excel(writer, sheet_name='CompositeAccountMilestones',index=False)
            composite_memo_milestones_df.to_excel(writer, sheet_name='CompositeMemoMilestones', index=False)
            config_df.to_excel(writer, sheet_name='config',index=False)


            if hasattr(self,'forecast_df'):
                run_info_df.to_excel(writer, sheet_name='run_info', index=False)
                self.forecast_df.to_excel(writer, sheet_name='Forecast', index=False)
                self.skipped_df.to_excel(writer, sheet_name='Skipped', index=False)
                self.confirmed_df.to_excel(writer, sheet_name='Confirmed', index=False)
                self.deferred_df.to_excel(writer, sheet_name='Deferred', index=False)
                self.getMilestoneResultsDF().to_excel(writer, sheet_name='MilestoneResults', index=False)

    def getRunInfoDF(self):
        if hasattr(self, 'forecast_df'):
            return pd.DataFrame(
                {'start_ts': [self.start_ts],
                 'end_ts': [self.end_ts],
                 'unique_id': [self.unique_id]
                 })
        return pd.DataFrame(
            {'start_ts': [],
             'end_ts': [],
             'unique_id': []
             })

    def getConfigDF(self):
        return pd.DataFrame({'Start_Date_YYYYMMDD':[self.start_date_YYYYMMDD],'End_Date_YYYYMMDD':[self.end_date_YYYYMMDD]})


# written in one line so that test coverage can reach 100%
# if __name__ == "__main__": import doctest ; doctest.testmod()
if __name__ == "__main__":
    pass

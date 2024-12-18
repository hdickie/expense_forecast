import warnings
import pandas as pd
import datetime
import re
import copy
import json
import AccountMilestone
import MemoMilestone
import BudgetSet
import AccountSet
import MemoRuleSet
import hashlib
import MilestoneSet
from log_methods import log_in_color
from log_methods import setup_logger
import logging
from generate_date_sequence import generate_date_sequence
import numpy as np
import CompositeMilestone
import jsonpickle
import tqdm
import os
import random
import math
from sqlalchemy import create_engine
import psycopg2
warnings.simplefilter(action="ignore")

pd.options.mode.chained_assignment = (
    None  # apparently this warning can throw false positives???
)


# Show all decimal places in data frames
pd.set_option("display.precision", 100)
ROUNDING_ERROR_TOLERANCE = (
    0.0000000001  # 10 places? overkill but I want to see if it works
)

logger = setup_logger(__name__, "./" + __name__ + ".log", level=logging.DEBUG)


def initialize_from_database_with_select(
    start_date_YYYYMMDD,
    end_date_YYYYMMDD,
    account_set_select_q,
    budget_set_select_q,
    memo_rule_set_select_q,
    account_milestone_select_q,
    memo_milestone_select_q,
    composite_milestone_select_q,
    set_def_q,
    metadata_q,
    budget_item_post_run_category_select_q,
    forecast_select_q,
    database_hostname,
    database_name,
    database_username,
    database_password,
    database_port,
    log_directory,
    forecast_set_name,
    forecast_name,
):
    # print('ENTER ExpenseForecast::initialize_from_database_with_select')
    # print('metadata_q:')
    # print(metadata_q)
    start_date_YYYYMMDD = start_date_YYYYMMDD.replace("-", "")
    end_date_YYYYMMDD = end_date_YYYYMMDD.replace("-", "").replace("-", "")

    connect_string = (
        "postgresql://"
        + database_username
        + ":"
        + database_password
        + "@"
        + database_hostname
        + ":"
        + str(database_port)
        + "/"
        + database_name
    )
    engine = create_engine(connect_string)

    accounts_df = pd.read_sql_query(account_set_select_q, con=engine)
    # assert accounts_df.shape[0] > 0
    budget_items_df = pd.read_sql_query(budget_set_select_q, con=engine)
    # print(budget_set_select_q)
    # assert budget_items_df.shape[0] > 0 #not generically true but true in testing. remove this for prod
    memo_rules_df = pd.read_sql_query(memo_rule_set_select_q, con=engine)
    # assert memo_rules_df.shape[0] > 0 #not generically true but true in testing. remove this for prod
    account_milestones_df = pd.read_sql_query(account_milestone_select_q, con=engine)
    memo_milestones_df = pd.read_sql_query(memo_milestone_select_q, con=engine)
    composite_milestones_df = pd.read_sql_query(
        composite_milestone_select_q, con=engine
    )

    try:
        forecast_df = pd.read_sql_query(forecast_select_q, con=engine)
        forecast_df["Date"] = [str(int(d)) for d in forecast_df["Date"]]
    except Exception:
        forecast_df = None

    set_def_df = pd.read_sql_query(set_def_q, con=engine)

    # if forecast has not been run, this will be empty
    # forecast_set_id, forecast_id, forecast_title, forecast_subtitle
    # submit_ts, complete_ts, error_flag, _satisfice_failed_flag, insert_ts
    metadata_df = pd.read_sql_query(metadata_q, con=engine)
    start_ts = None
    end_ts = None
    forecast_name = ""

    forecast_name = set_def_df["forecast_name"].iat[0]

    if metadata_df.shape[0] > 0:
        start_ts = metadata_df["submit_ts"].iat[0].strftime("%Y-%m-%d %H:%M:%S")
        end_ts = metadata_df["complete_ts"].iat[0].strftime("%Y-%m-%d %H:%M:%S")

    budget_item_post_run_category_df = pd.read_sql_query(
        budget_item_post_run_category_select_q, con=engine
    )
    budget_item_post_run_category_df.rename(
        columns={
            "category": "Category",
            "forecast_id": "Forecast_Id",
            "date": "Date",
            "priority": "Priority",
            "amount": "Amount",
            "memo": "Memo",
            "deferrable": "Deferrable",
            "partial_payment_allowed": "Partial_Payment_Allowed",
        },
        inplace=True,
    )
    budget_item_post_run_category_df.Date = [
        d.strftime("%Y%m%d") for d in budget_item_post_run_category_df.Date
    ]
    # print('budget_item_post_run_category_df:')
    # print(budget_item_post_run_category_df.to_string())

    account_set = AccountSet.initialize_from_dataframe(accounts_df)
    budget_set = BudgetSet.initialize_from_dataframe(budget_items_df)
    memo_rule_set = MemoRuleSet.initialize_from_dataframe(memo_rules_df)
    milestone_set = MilestoneSet.initialize_from_dataframe(
        account_milestones_df, memo_milestones_df, composite_milestones_df
    )

    E = ExpenseForecast(
        account_set=account_set,
        budget_set=budget_set,
        memo_rule_set=memo_rule_set,
        start_date_YYYYMMDD=start_date_YYYYMMDD,
        end_date_YYYYMMDD=end_date_YYYYMMDD,
        milestone_set=milestone_set,
        log_directory=log_directory,
        forecast_set_name=forecast_set_name,
        forecast_name=forecast_name,
    )

    relevant_cols = [
        "Date",
        "Priority",
        "Amount",
        "Memo",
        "Deferrable",
        "Partial_Payment_Allowed",
    ]
    confirmed_df = budget_item_post_run_category_df.loc[
        budget_item_post_run_category_df.Category == "Confirmed", relevant_cols
    ]
    deferred_df = budget_item_post_run_category_df.loc[
        budget_item_post_run_category_df.Category == "Deferred", relevant_cols
    ]
    skipped_df = budget_item_post_run_category_df.loc[
        budget_item_post_run_category_df.Category == "Skipped", relevant_cols
    ]

    # print('confirmed_df:')
    # print(confirmed_df.to_string())
    # print('deferred_df:')
    # print(deferred_df.to_string())
    # print('skipped_df:')
    # print(skipped_df.to_string())

    E.confirmed_df = confirmed_df
    E.skipped_df = skipped_df
    E.deferred_df = deferred_df
    E.start_ts = start_ts
    E.end_ts = end_ts
    E.forecast_df = forecast_df

    # todo this needs to be handled upstream
    # E.forecast_df.Date = [ d.strftime('%Y%m%d') for d in E.forecast_df.Date ]
    # E.forecast_df = E.forecast_df.astype({"Date": int})
    # E.forecast_df = E.forecast_df.astype({"Date": str})

    # todo validation of confirmed, skipped, deferred, start_ts, end_ts

    return E


def initialize_from_database_with_id(
    username,
    forecast_set_id,
    forecast_id,
    database_hostname="localhost",
    database_name="postgres",
    database_username="postgres",
    database_password="postgres",
    database_port="5432",
):  # todo may need a few more parameters
    # print('ENTER ExpenseForecast::initialize_from_database_with_id forecast_id='+str(forecast_id))
    connect_string = (
        "postgresql://"
        + database_username
        + ":"
        + database_password
        + "@"
        + database_hostname
        + ":"
        + str(database_port)
        + "/"
        + database_name
    )
    engine = create_engine(connect_string)
    # engine = create_engine('postgresql://bsdegjmy_humedick@localhost:5432/bsdegjmy_sandbox')

    get_date_ranges_q = (
        "select distinct start_date, end_date from prod."
        + username
        + "_forecast_set_definitions where forecast_id = '"
        + str(forecast_id)
        + "' and forecast_set_id = '"
        + str(forecast_set_id)
        + "'"
    )
    # print('get_date_ranges_q:')
    # print(get_date_ranges_q)
    date_range_df = pd.read_sql_query(get_date_ranges_q, con=engine)
    assert date_range_df.shape[0] == 1

    start_date_YYYYMMDD = date_range_df.iloc[0, 0].strftime("%Y%m%d")
    end_date_YYYYMMDD = date_range_df.iloc[0, 1].strftime("%Y%m%d")

    account_set_select_q = (
        "select * from prod.ef_account_set_"
        + username
        + " where forecast_id = '"
        + forecast_id
        + "'"
    )
    # print('forecast_set_id:'+forecast_set_id)
    # print('forecast_id:'+forecast_id)
    # print('account_set_select_q:')
    # print(account_set_select_q)

    budget_set_select_q = (
        "select * from prod.ef_budget_item_set_"
        + username
        + " where forecast_id = '"
        + forecast_id
        + "'"
    )
    memo_rule_set_select_q = (
        "select * from prod.ef_memo_rule_set_"
        + username
        + " where forecast_id = '"
        + forecast_id
        + "'"
    )
    account_milestone_select_q = (
        "select * from prod.ef_account_milestones_"
        + username
        + " where forecast_id = '"
        + forecast_id
        + "'"
    )
    memo_milestone_select_q = (
        "select * from prod.ef_memo_milestones_"
        + username
        + " where forecast_id = '"
        + forecast_id
        + "'"
    )
    composite_milestone_select_q = (
        "select * from prod.ef_composite_milestones_"
        + username
        + " where forecast_id = '"
        + forecast_id
        + "'"
    )
    set_def_q = (
        """
    select *
    from prod."""
        + username
        + """_forecast_set_definitions
    where forecast_set_id = '"""
        + forecast_set_id
        + """' and forecast_id = '"""
        + forecast_id
        + """'
    """
    )
    # it has to be forecast_set bc if forecast hasnt been run yet we still need that info
    metadata_q = (
        """
    select forecast_set_id, forecast_id, forecast_title, forecast_subtitle,
    submit_ts, complete_ts, error_flag, _satisfice_failed_flag
    from (
    select *, row_number() over(partition by forecast_id order by insert_ts desc) as rn
    from prod."""
        + username
        + """_forecast_run_metadata
    where forecast_id = '"""
        + forecast_id
        + """'
    order by forecast_id
    ) where rn = 1 and forecast_id = '"""
        + forecast_id
        + """'
    """
    )
    budget_item_post_run_category_select_q = (
        "select * from prod."
        + username
        + "_budget_item_post_run_category where forecast_id = '"
        + forecast_id
        + "'"
    )

    forecast_select_q = "select * from prod." + username + "_forecast_" + forecast_id

    E = initialize_from_database_with_select(
        start_date_YYYYMMDD=start_date_YYYYMMDD,
        end_date_YYYYMMDD=end_date_YYYYMMDD,
        account_set_select_q=account_set_select_q,
        budget_set_select_q=budget_set_select_q,
        memo_rule_set_select_q=memo_rule_set_select_q,
        account_milestone_select_q=account_milestone_select_q,
        memo_milestone_select_q=memo_milestone_select_q,
        composite_milestone_select_q=composite_milestone_select_q,
        set_def_q=set_def_q,
        metadata_q=metadata_q,
        budget_item_post_run_category_select_q=budget_item_post_run_category_select_q,
        forecast_select_q=forecast_select_q,
        database_hostname=database_hostname,
        database_name=database_name,
        database_username=database_username,
        database_password=database_password,
        database_port=database_port,
        log_directory=".",
        forecast_set_name="",
        forecast_name="",
    )

    return E


# whether or not the expense forecast has been run will be determined at runtime
# this can return a list of initialized ExpenseForecast objects from ChooseOneSet
# therefore, even if no ChooseOneSets, return the single ExpenseForecast in a list
def initialize_from_excel_file(path_to_excel_file):

    summary_df = pd.read_excel(path_to_excel_file, sheet_name="Summary")

    summary_df = summary_df.T
    summary_df.columns = summary_df.iloc[0, :]
    summary_df.drop(summary_df.index[0], inplace=True)

    summary_df["start_date_YYYYMMDD"] = str(int(summary_df["start_date_YYYYMMDD"]))
    summary_df["end_date_YYYYMMDD"] = str(int(summary_df["end_date_YYYYMMDD"]))
    # summary_df['unique_id'] = str(int(summary_df['unique_id'])).rjust(6,'0')

    account_set_df = pd.read_excel(path_to_excel_file, sheet_name="AccountSet")
    budget_set_df = pd.read_excel(path_to_excel_file, sheet_name="BudgetSet")
    memo_rule_set_df = pd.read_excel(path_to_excel_file, sheet_name="MemoRuleSet")
    choose_one_set_df = pd.read_excel(path_to_excel_file, sheet_name="ChooseOneSet")
    account_milestones_df = pd.read_excel(
        path_to_excel_file, sheet_name="AccountMilestones"
    )
    memo_milestones_df = pd.read_excel(path_to_excel_file, sheet_name="MemoMilestones")
    composite_milestones_df = pd.read_excel(
        path_to_excel_file, sheet_name="CompositeMilestones"
    )

    # These are here to remove the 'might be referenced before assignment' warning
    forecast_df = None
    skipped_df = None
    confirmed_df = None
    deferred_df = None
    milestone_results_df = None

    try:
        forecast_df = pd.read_excel(path_to_excel_file, sheet_name="Forecast")
        skipped_df = pd.read_excel(path_to_excel_file, sheet_name="Skipped")
        confirmed_df = pd.read_excel(path_to_excel_file, sheet_name="Confirmed")
        deferred_df = pd.read_excel(path_to_excel_file, sheet_name="Deferred")
        milestone_results_df = pd.read_excel(
            path_to_excel_file, sheet_name="Milestone Results"
        )
    except Exception as e:
        pass  # if forecast was not run this will happen

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
    interest_balance = None

    for index, row in account_set_df.iterrows():
        if row.Account_Type.lower() == "checking":
            A.createCheckingAccount(
                row.Name,
                row.Balance,
                row.Min_Balance,
                row.Max_Balance,
                row.Primary_Checking_Ind,
            )
            # A.createAccount(row.Name,row.Balance,row.Min_Balance,row.Max_Balance,'checking',None,None,None,None,None,None,None,None)

        if (
            row.Account_Type.lower() == "credit curr stmt bal"
            and not expect_curr_bal_acct
        ):
            current_statement_balance = row.Balance
            expect_prev_bal_acct = True
            continue

        if (
            row.Account_Type.lower() == "credit prev stmt bal"
            and not expect_prev_bal_acct
        ):
            previous_statement_balance = row.Balance
            interest_cadence = row.Interest_Cadence
            minimum_payment = row.Minimum_Payment
            billing_start_date = str(int(row.Billing_Start_Date))
            interest_type = row.Interest_Type
            apr = row.APR

            expect_curr_bal_acct = True
            continue

        if row.Account_Type.lower() == "interest" and not expect_interest_acct:
            interest_balance = row.Balance
            expect_principal_bal_acct = True
            continue

        if (
            row.Account_Type.lower() == "principal balance"
            and not expect_principal_bal_acct
        ):
            principal_balance = row.Balance
            interest_cadence = row.Interest_Cadence
            minimum_payment = row.Minimum_Payment
            billing_start_date = str(int(row.Billing_Start_Date))
            interest_type = row.Interest_Type
            apr = row.APR
            expect_interest_acct = True
            continue

        # todo i was tired when I wrote these likely worth a second look
        if row.Account_Type.lower() == "credit curr stmt bal" and expect_curr_bal_acct:
            A.createAccount(
                name=row.Name.split(":")[0],
                balance=previous_statement_balance + previous_statement_balance,
                min_balance=row.Min_Balance,
                max_balance=row.Max_Balance,
                account_type="credit",
                billing_start_date_YYYYMMDD=billing_start_date,
                interest_type=interest_type,
                apr=apr,
                interest_cadence=interest_cadence,
                minimum_payment=minimum_payment,
                previous_statement_balance=previous_statement_balance,
                current_statement_balance=current_statement_balance,
            )
            expect_curr_bal_acct = False

        if row.Account_Type.lower() == "credit prev stmt bal" and expect_prev_bal_acct:
            A.createAccount(
                name=row.Name.split(":")[0],
                balance=current_statement_balance + row.Balance,
                min_balance=row.Min_Balance,
                max_balance=row.Max_Balance,
                account_type="credit",
                billing_start_date_YYYYMMDD=str(int(row.Billing_Start_Date)),
                interest_type=row.Interest_Type,
                apr=row.APR,
                interest_cadence=row.Interest_Cadence,
                minimum_payment=row.Minimum_Payment,
                previous_statement_balance=row.Balance,
                current_statement_balance=current_statement_balance,
            )
            expect_prev_bal_acct = False

        if row.Account_Type.lower() == "interest" and expect_interest_acct:

            A.createAccount(
                name=row.Name.split(":")[0],
                balance=row.Balance + principal_balance,
                min_balance=row.Min_Balance,
                max_balance=row.Max_Balance,
                account_type="loan",
                billing_start_date_YYYYMMDD=billing_start_date,
                interest_type=interest_type,
                apr=apr,
                interest_cadence=interest_cadence,
                minimum_payment=minimum_payment,
                previous_statement_balance=None,
                current_statement_balance=None,
                principal_balance=principal_balance,
                interest_balance=row.Balance,
            )
            expect_interest_acct = False

        if (
            row.Account_Type.lower() == "principal balance"
            and expect_principal_bal_acct
        ):
            A.createAccount(
                name=row.Name.split(":")[0],
                balance=row.Balance + interest_balance,
                min_balance=row.Min_Balance,
                max_balance=row.Max_Balance,
                account_type="loan",
                billing_start_date_YYYYMMDD=str(int(row.Billing_Start_Date)),
                interest_type=row.Interest_Type,
                apr=row.APR,
                interest_cadence=row.Interest_Cadence,
                minimum_payment=row.Minimum_Payment,
                previous_statement_balance=None,
                current_statement_balance=None,
                principal_balance=row.Balance,
                interest_balance=interest_balance,
            )
            expect_principal_bal_acct = False

    B = BudgetSet.BudgetSet([])
    for index, row in budget_set_df.iterrows():
        B.addBudgetItem(
            row.Start_Date,
            row.End_Date,
            row.Priority,
            row.Cadence,
            row.Amount,
            row.Memo,
            row.Deferrable,
            row.Partial_Payment_Allowed,
        )

    M = MemoRuleSet.MemoRuleSet([])
    for index, row in memo_rule_set_df.iterrows():
        M.addMemoRule(
            row.Memo_Regex, row.Account_From, row.Account_To, row.Transaction_Priority
        )

    am__list = []
    am__dict = {}
    for index, row in account_milestones_df.iterrows():
        AM = AccountMilestone.AccountMilestone(
            row.Milestone_Name, row.Account_Name, row.Min_Balance, row.Max_Balance
        )
        am__list.append(AM)
        am__dict[row.Milestone_Name] = AM

    mm__list = []
    mm__dict = {}
    for index, row in memo_milestones_df.iterrows():
        MM = MemoMilestone.MemoMilestone(row.Milestone_Name, row.Memo_Regex)
        mm__list.append(MM)
        mm__dict[row.Milestone_Name] = MM

    # (self,milestone_name,account_milestones__list, memo_milestones__list)
    cm__list = []
    composite_milestones = {}
    for index, row in composite_milestones_df.iterrows():
        if row.Composite_Milestone_Name not in composite_milestones.keys():
            composite_milestones[row.Composite_Milestone_Name] = {
                "account_milestones": [],
                "memo_milestones": [],
            }

        # todo i think there is an error here
        if row.Milestone_Type == "Account":
            component_account_milestone = am__dict[row.Milestone_Name]
            # print('component_account_milestone:')
            # print(component_account_milestone.to_json())
            composite_milestones[row.Composite_Milestone_Name][
                "account_milestones"
            ].append(component_account_milestone)
        elif row.Milestone_Type == "Memo":
            component_memo_milestone = mm__dict[row.Milestone_Name]
            # print('component_memo_milestone:')
            # print(component_memo_milestone.to_json())
            composite_milestones[row.Composite_Milestone_Name][
                "memo_milestones"
            ].append(component_memo_milestone)

    for key, value in composite_milestones.items():

        # component_account_milestones = []
        # for am_name in value['Account']:
        #     component_account_milestones.append( am__dict[am_name] )
        #
        # component_memo_milestones = []
        # for mm_name in value['Memo']:
        #     component_memo_milestones.append( mm__dict[mm_name] )

        # print('composite_milestones[key][account_milestones]:')
        # print(composite_milestones[key]['account_milestones'])
        # print('composite_milestones[key][memo_milestones]:')
        # print(composite_milestones[key]['memo_milestones'])

        new_composite_milestone = CompositeMilestone.CompositeMilestone(
            key,
            composite_milestones[key]["account_milestones"],
            composite_milestones[key]["memo_milestones"],
        )
        cm__list.append(new_composite_milestone)
        # print('cm__list:')
        # for cm in cm__list:
        #     print(cm.to_json())

    # (self,account_set,budget_set,account_milestones__list,memo_milestones__list,composite_milestones__list)
    MS = MilestoneSet.MilestoneSet(am__list, mm__list, cm__list)

    start_date_YYYYMMDD = summary_df.start_date_YYYYMMDD.iat[0]
    end_date_YYYYMMDD = summary_df.end_date_YYYYMMDD.iat[0]

    E = ExpenseForecast(A, B, M, start_date_YYYYMMDD, end_date_YYYYMMDD, MS)

    # todo
    for index, row in choose_one_set_df.iterrows():
        pass

    if forecast_df is not None:

        E.start_ts = summary_df.start_ts.iat[0]

        E.end_ts = summary_df.end_ts.iat[0]

        E.forecast_df = forecast_df
        E.forecast_df["Date"] = [str(d) for d in E.forecast_df["Date"]]

        E.forecast_df = E.forecast_df.replace(np.NaN, "")

        E.skipped_df = skipped_df
        E.skipped_df["Date"] = [str(d) for d in E.skipped_df["Date"]]

        E.confirmed_df = confirmed_df
        E.confirmed_df["Date"] = [str(d) for d in E.confirmed_df["Date"]]

        E.deferred_df = deferred_df
        E.deferred_df["Date"] = [str(d) for d in E.deferred_df["Date"]]

        E.account_milestone_results = {}
        E.memo_milestone_results = {}
        E.composite_milestone_results = {}
        for index, row in milestone_results_df.iterrows():
            if row.Milestone_Type == "Account":
                E.account_milestone_results[row.Milestone_Name] = str(row.Result_Date)
            elif row.Milestone_Type == "Memo":
                E.memo_milestone_results[row.Milestone_Name] = str(row.Result_Date)
            elif row.Milestone_Type == "Composite":
                E.composite_milestone_results[row.Milestone_Name] = str(row.Result_Date)
            else:
                raise ValueError(
                    "Unknown Milestone result type encountered while reading excel file."
                )

    return E


# whether or not the expense forecast has been run will be determined at runtime
# returns a list of ExpenseForecast objects


def initialize_from_json_file(path_to_json):
    with open(path_to_json) as json_data:
        data = json.load(json_data)
        return initialize_from_dict(data)


def initialize_from_json_string(json_string):
    data = json.loads(json_string)
    return initialize_from_dict(data)


def initialize_from_dict(data):
    initial_account_set = data["initial_account_set"]
    initial_budget_set = data["initial_budget_set"]
    initial_memo_rule_set = data["initial_memo_rule_set"]
    start_date_YYYYMMDD = data["start_date_YYYYMMDD"]
    end_date_YYYYMMDD = data["end_date_YYYYMMDD"]
    milestone_set = data["milestone_set"]

    A = AccountSet.AccountSet([])
    B = BudgetSet.BudgetSet([])
    M = MemoRuleSet.MemoRuleSet([])
    MS = MilestoneSet.MilestoneSet([], [], [])

    # these are here to remove 'might be referenced before assignment' warning
    credit_acct_name = None
    credit_curr_bal = None
    loan_acct_name = None
    loan_balance = None
    loan_billing_start_date = None
    loan_interest_type = None
    loan_apr = None
    loan_interest_cadence = None
    loan_min_payment = None

    for Account__dict in initial_account_set["accounts"]:

        # Account__dict = Account__dict[0] #the dict came in a list
        if Account__dict["account_type"].lower() == "checking":
            A.createCheckingAccount(
                Account__dict["name"],
                Account__dict["balance"],
                Account__dict["min_balance"],
                Account__dict["max_balance"],
                Account__dict["primary_checking_ind"],
            )

        elif Account__dict["account_type"].lower() == "credit curr stmt bal":
            credit_acct_name = Account__dict["name"].split(":")[0]
            credit_curr_bal = Account__dict["balance"]

        elif Account__dict["account_type"].lower() == "credit prev stmt bal":
            # (self,name,current_stmt_bal,prev_stmt_bal,min_balance,max_balance,billing_start_date_YYYYMMDD,apr,minimum_payment):
            A.createCreditCardAccount(
                credit_acct_name,
                credit_curr_bal,
                Account__dict["balance"],
                Account__dict["min_balance"],
                Account__dict["max_balance"],
                Account__dict["billing_start_date_YYYYMMDD"],
                Account__dict["apr"],
                Account__dict["minimum_payment"],
            )

        elif Account__dict["account_type"].lower() == "principal balance":

            loan_acct_name = Account__dict["name"].split(":")[0]
            loan_balance = Account__dict["balance"]
            loan_apr = Account__dict["apr"]
            loan_billing_start_date = Account__dict["billing_start_date_YYYYMMDD"]
            loan_min_payment = Account__dict["minimum_payment"]
            loan_interest_cadence = Account__dict["interest_cadence"]
            loan_interest_type = Account__dict["interest_type"]

        elif Account__dict["account_type"].lower() == "interest":

            # principal balance then interest
            # (self,name,principal_balance,interest_balance,min_balance,max_balance,billing_start_date_YYYYMMDD,apr,minimum_payment):
            A.createLoanAccount(
                loan_acct_name,
                float(loan_balance),
                float(Account__dict["balance"]),
                Account__dict["min_balance"],
                Account__dict["max_balance"],
                loan_billing_start_date,
                loan_apr,
                loan_min_payment,
            )

        else:
            raise ValueError(
                "unrecognized account type in ExpenseForecast::initialize_from_json_file: "
                + str(Account__dict["account_type"])
            )

    for BudgetItem__dict in initial_budget_set["budget_items"]:
        # BudgetItem__dict = BudgetItem__dict[0]
        sd_YYYYMMDD = BudgetItem__dict["start_date_YYYYMMDD"]
        ed_YYYYMMDD = BudgetItem__dict["end_date_YYYYMMDD"]

        B.addBudgetItem(
            start_date_YYYYMMDD=sd_YYYYMMDD,
            end_date_YYYYMMDD=ed_YYYYMMDD,
            priority=BudgetItem__dict["priority"],
            cadence=BudgetItem__dict["cadence"],
            amount=BudgetItem__dict["amount"],
            memo=BudgetItem__dict["memo"],
            deferrable=BudgetItem__dict["deferrable"],
            partial_payment_allowed=BudgetItem__dict["partial_payment_allowed"],
        )

    for MemoRule__dict in initial_memo_rule_set["memo_rules"]:
        # MemoRule__dict = MemoRule__dict[0]
        M.addMemoRule(
            memo_regex=MemoRule__dict["memo_regex"],
            account_from=MemoRule__dict["account_from"],
            account_to=MemoRule__dict["account_to"],
            transaction_priority=MemoRule__dict["transaction_priority"],
        )

    for am in milestone_set["account_milestones"]:
        MS.addAccountMilestone(
            am["milestone_name"],
            am["account_name"],
            am["min_balance"],
            am["max_balance"],
        )

    for mm in milestone_set["memo_milestones"]:
        MS.addMemoMilestone(mm["milestone_name"], mm["memo_regex"])

    # milestone_name,account_milestones__list, memo_milestones__list
    for cm in milestone_set["composite_milestones"]:
        account_milestones__list = []
        for acc_mil in cm["account_milestones"]:
            account_milestones__list.append(
                AccountMilestone.AccountMilestone(
                    acc_mil["milestone_name"],
                    acc_mil["account_name"],
                    acc_mil["min_balance"],
                    acc_mil["max_balance"],
                )
            )

        memo_milestones__list = []
        for memo_mil in cm["memo_milestones"]:
            memo_milestones__list.append(
                MemoMilestone.MemoMilestone(
                    memo_mil["milestone_name"], memo_mil["memo_regex"]
                )
            )

        MS.addCompositeMilestone(
            cm["milestone_name"], account_milestones__list, memo_milestones__list
        )

    E = ExpenseForecast(
        A, B, M, start_date_YYYYMMDD, end_date_YYYYMMDD, MS, print_debug_messages=True
    )
    E.forecast_set_name = data["forecast_set_name"]
    E.forecast_name = data["forecast_name"]

    if not data["start_ts"] is None:
        E.account_milestone_results = data["account_milestone_results"]
        E.memo_milestone_results = data["memo_milestone_results"]
        E.composite_milestone_results = data["composite_milestone_results"]
        E.start_ts = data["start_ts"]
        E.end_ts = data["end_ts"]

        # todo it is so dumb that I have to do this just to interpret string as json
        f = open("./out/forecast_df_" + str(E.unique_id) + ".json", "w")
        f.write(json.dumps(data["forecast_df"], indent=4))
        f.close()

        f = open("./out/skipped_df_" + str(E.unique_id) + ".json", "w")
        f.write(json.dumps(data["skipped_df"], indent=4))
        f.close()

        f = open("./out/confirmed_df_" + str(E.unique_id) + ".json", "w")
        f.write(json.dumps(data["confirmed_df"], indent=4))
        f.close()

        f = open("./out/deferred_df_" + str(E.unique_id) + ".json", "w")
        f.write(json.dumps(data["deferred_df"], indent=4))
        f.close()

        try:
            E.forecast_df = pd.read_json(
                "./out/forecast_df_" + str(E.unique_id) + ".json"
            )
            E.skipped_df = pd.read_json(
                "./out/skipped_df_" + str(E.unique_id) + ".json"
            )
            E.confirmed_df = pd.read_json(
                "./out/confirmed_df_" + str(E.unique_id) + ".json"
            )
            E.deferred_df = pd.read_json(
                "./out/deferred_df_" + str(E.unique_id) + ".json"
            )

            E.forecast_df.Date = [str(d) for d in E.forecast_df.Date]
            if E.skipped_df.shape[0] > 0:
                E.skipped_df.Date = [str(d) for d in E.skipped_df.Date]
            if E.confirmed_df.shape[0] > 0:
                E.confirmed_df.Date = [str(d) for d in E.confirmed_df.Date]
            if E.deferred_df.shape[0] > 0:
                E.deferred_df.Date = [str(d) for d in E.deferred_df.Date]
        except Exception:
            pass  # todo this logic needs to be rethought out

    return E


class ExpenseForecast:

    # Pickle will use these
    # def __getstate__(self):
    #     pass
    #
    # def __setstate__(self, state):
    #     pass

    def update_date_range(self, start_date_YYYYMMDD, end_date_YYYYMMDD):
        if (
            self.start_date_YYYYMMDD != start_date_YYYYMMDD
            or self.end_date_YYYYMMDD != end_date_YYYYMMDD
        ):
            self.start_ts = None
            self.end_ts = None
            self.skipped_df = None
            self.confirmed_df = None
            self.deferred_df = None
            self.forecast_df = None
            self.account_milestone_results = None
            self.memo_milestone_results = None
            self.composite_milestone_results = None

            account_hash = hashlib.sha1(
                self.initial_account_set.getAccounts().to_string().encode("utf-8")
            ).hexdigest()
            budget_hash = hashlib.sha1(
                self.initial_budget_set.getBudgetItems().to_string().encode("utf-8")
            ).hexdigest()
            memo_hash = hashlib.sha1(
                self.initial_memo_rule_set.getMemoRules().to_string().encode("utf-8")
            ).hexdigest()
            start_date_hash = int(start_date_YYYYMMDD)
            end_date_hash = int(end_date_YYYYMMDD)

            self.start_date_YYYYMMDD = start_date_YYYYMMDD
            self.end_date_YYYYMMDD = end_date_YYYYMMDD

            # e.g. 240424_90_1_####_1_A.json
            #      YYMMDD_days_numDistinctPriority_hash_approxFlag
            num_days = (
                datetime.datetime.strptime(end_date_YYYYMMDD, "%Y%m%d")
                - datetime.datetime.strptime(start_date_YYYYMMDD, "%Y%m%d")
            ).days
            num_distinct_priority = len(
                set(self.initial_budget_set.getBudgetItems().Priority)
            )
            self.unique_id = (
                start_date_YYYYMMDD[2:]
                + "_"
                + str(num_days)
                + "_"
                + str(num_distinct_priority)
                + "_"
            )
            self.unique_id += str(
                hash(
                    int(account_hash, 16)
                    + int(budget_hash, 16)
                    + int(memo_hash, 16)
                    + start_date_hash
                    + end_date_hash
                )
                % 1000
            ).rjust(4, "0")
            if self.approximate_flag:
                self.unique_id += "A"

        else:
            return

    def write_to_database(
        self,
        database_hostname,  # localhost
        database_name,  # bsdegjmy_sandbox
        database_username,  # bsdegjmy_humedick
        database_password,  #
        database_port,  # 5432
        username,
        forecast_set_id="",
        overwrite=False,
    ):
        # engine = create_engine('postgresql://bsdegjmy_humedick@localhost:5432/bsdegjmy_sandbox')
        connection = psycopg2.connect(
            host=database_hostname,
            database=database_name,
            user=database_username,
            password=database_password,
            port=database_port,
        )
        connection.autocommit = True
        cursor = connection.cursor()

        # todo implement force

        account_set_table_name = "prod.ef_account_set_" + username
        budget_set_table_name = "prod.ef_budget_item_set_" + username
        memo_rule_set_table_name = "prod.ef_memo_rule_set_" + username
        account_milestone_table_name = "prod.ef_account_milestones_" + username
        memo_milestone_table_name = "prod.ef_memo_milestones_" + username
        composite_milestone_table_name = "prod.ef_composite_milestones_" + username
        budget_item_post_run_category_table_name = (
            "prod." + username + "_budget_item_post_run_category"
        )

        cursor.execute(
            "DELETE FROM "
            + account_set_table_name
            + " WHERE forecast_id = '"
            + str(self.unique_id)
            + "'"
        )
        for index, row in self.initial_account_set.getAccounts().iterrows():
            if row.Billing_Start_Date is None:
                bsd = "Null"
            else:
                bsd = "'" + str(row.Billing_Start_Date) + "'"
            if row.APR is None:
                apr = "Null"
            else:
                apr = "'" + str(row.APR) + "'"
            if row.Minimum_Payment is None:
                min_payment = "Null"
            else:
                min_payment = str(row.Minimum_Payment)

            insert_account_row_q = (
                "INSERT INTO "
                + account_set_table_name
                + " (forecast_id, account_name, balance, min_balance, max_balance, account_type, billing_start_date_yyyymmdd, apr, interest_cadence, minimum_payment, primary_checking_ind) VALUES "
            )
            insert_account_row_q += (
                "('"
                + str(self.unique_id)
                + "', '"
                + str(row.Name)
                + "', "
                + str(row.Balance)
                + ", "
                + str(row.Min_Balance)
                + ", "
                + str(row.Max_Balance)
                + ", '"
                + str(row.Account_Type)
                + "', "
                + str(bsd)
                + ", "
                + apr
                + ", '"
                + str(row.Interest_Cadence)
                + "', "
                + min_payment
                + ", '"
                + str(row.Primary_Checking_Ind)
                + "')"
            )
            # print(insert_account_row_q)
            cursor.execute(insert_account_row_q)

        cursor.execute(
            "DELETE FROM "
            + budget_set_table_name
            + " WHERE forecast_id = '"
            + str(self.unique_id)
            + "'"
        )
        for index, row in self.initial_budget_set.getBudgetItems().iterrows():
            insert_budget_item_row_q = (
                "INSERT INTO "
                + budget_set_table_name
                + ' (forecast_id, memo, priority, start_date, end_date, cadence, amount, "deferrable", partial_payment_allowed) VALUES '
            )
            insert_budget_item_row_q += (
                "('"
                + str(self.unique_id)
                + "','"
                + str(row.Memo)
                + "',"
                + str(row.Priority)
                + ",'"
                + str(row.Start_Date)
                + "','"
                + str(row.End_Date)
                + "','"
                + str(row.Cadence)
                + "',"
                + str(row.Amount)
                + ",'"
                + str(row.Deferrable)
                + "','"
                + str(row.Partial_Payment_Allowed)
                + "')"
            )
            cursor.execute(insert_budget_item_row_q)

        cursor.execute(
            "DELETE FROM "
            + budget_item_post_run_category_table_name
            + " WHERE forecast_id = '"
            + str(self.unique_id)
            + "'"
        )
        if self.confirmed_df is not None:
            for index, row in self.confirmed_df.iterrows():
                insert_confirmed_q = (
                    "INSERT INTO "
                    + budget_item_post_run_category_table_name
                    + ' ( category, forecast_id, "date", priority, amount, memo, "deferrable", partial_payment_allowed) VALUES '
                )
                insert_confirmed_q += (
                    "('Confirmed','" + str(self.unique_id) + "','" + str(row.Date) + "'"
                )
                insert_confirmed_q += (
                    ","
                    + str(row.Priority)
                    + ","
                    + str(row.Amount)
                    + ",'"
                    + str(row.Memo)
                    + "'"
                )
                insert_confirmed_q += (
                    ",'"
                    + str(row.Deferrable)
                    + "','"
                    + str(row.Partial_Payment_Allowed)
                    + "')"
                )
                cursor.execute(insert_confirmed_q)

        if self.deferred_df is not None:
            for index, row in self.deferred_df.iterrows():
                insert_deferred_q = (
                    "INSERT INTO "
                    + budget_item_post_run_category_table_name
                    + ' ( category, forecast_id, "date", priority, amount, memo, "deferrable", partial_payment_allowed) VALUES '
                )
                insert_deferred_q += (
                    "('Deferred','" + str(self.unique_id) + "','" + str(row.Date) + "'"
                )
                insert_deferred_q += (
                    ","
                    + str(row.Priority)
                    + ","
                    + str(row.Amount)
                    + ",'"
                    + str(row.Memo)
                    + "'"
                )
                insert_deferred_q += (
                    ",'"
                    + str(row.Deferrable)
                    + "','"
                    + str(row.Partial_Payment_Allowed)
                    + "')"
                )
                cursor.execute(insert_deferred_q)

        if self.skipped_df is not None:
            for index, row in self.skipped_df.iterrows():
                insert_skipped_q = (
                    "INSERT INTO "
                    + budget_item_post_run_category_table_name
                    + ' ( category, forecast_id, "date", priority, amount, memo, "deferrable", partial_payment_allowed) VALUES '
                )
                insert_skipped_q += (
                    "('Skipped','" + str(self.unique_id) + "','" + str(row.Date) + "'"
                )
                insert_skipped_q += (
                    ","
                    + str(row.Priority)
                    + ","
                    + str(row.Amount)
                    + ",'"
                    + str(row.Memo)
                    + "'"
                )
                insert_skipped_q += (
                    ",'"
                    + str(row.Deferrable)
                    + "','"
                    + str(row.Partial_Payment_Allowed)
                    + "')"
                )
                cursor.execute(insert_skipped_q)

        cursor.execute(
            "DELETE FROM "
            + memo_rule_set_table_name
            + " WHERE forecast_id = '"
            + str(self.unique_id)
            + "'"
        )
        for index, row in self.initial_memo_rule_set.getMemoRules().iterrows():
            insert_memo_rule_row_q = (
                "INSERT INTO "
                + memo_rule_set_table_name
                + " (forecast_id, memo_regex, account_from, account_to, priority ) VALUES "
            )
            insert_memo_rule_row_q += (
                "('"
                + str(self.unique_id)
                + "','"
                + str(row.Memo_Regex)
                + "','"
                + str(row.Account_From)
                + "','"
                + str(row.Account_To)
                + "',"
                + str(row.Transaction_Priority)
                + ")"
            )
            cursor.execute(insert_memo_rule_row_q)

        cursor.execute(
            "DELETE FROM prod.ef_account_milestones_"
            + username
            + " WHERE forecast_id = '"
            + self.unique_id
            + "'"
        )
        for index, row in self.milestone_set.getAccountMilestonesDF().iterrows():
            # forecast_id, milestone_name, account_name, min_balance, max_balance
            am_insert_q = (
                "INSERT INTO prod.ef_account_milestones_"
                + username
                + " SELECT '"
                + self.unique_id
                + "' as forecast_id, "
            )
            am_insert_q += (
                "'"
                + row.milestone_name
                + "' as milestone_name, '"
                + row.account_name
                + "' as account_name, "
            )
            am_insert_q += (
                str(row.min_balance)
                + " as min_balance, "
                + str(row.max_balance)
                + " as max_balance"
            )
            cursor.execute(am_insert_q)

        cursor.execute(
            "DELETE FROM prod.ef_memo_milestones_"
            + username
            + " WHERE forecast_id = '"
            + self.unique_id
            + "'"
        )
        for index, row in self.milestone_set.getMemoMilestonesDF().iterrows():
            mm_insert_q = (
                "INSERT INTO prod.ef_memo_milestones_"
                + username
                + " SELECT '"
                + self.unique_id
                + "' as forecast_id, "
            )
            mm_insert_q += (
                "'"
                + row.milestone_name
                + "' as milestone_name, '"
                + row.memo_regex
                + "' as memo_regex "
            )
            cursor.execute(mm_insert_q)

        cursor.execute(
            "DELETE FROM prod.ef_composite_milestones_"
            + username
            + " WHERE forecast_id = '"
            + self.unique_id
            + "'"
        )
        for index, row in self.milestone_set.getCompositeMilestonesDF().iterrows():
            cm_insert_q = (
                "INSERT INTO prod.ef_memo_milestones_"
                + username
                + " SELECT '"
                + self.unique_id
                + "' as forecast_id, "
            )
            cm_insert_q += (
                "'" + row.composite_milestone_name + "' as composite_milestone_name, "
            )
            cm_insert_q += (
                "'"
                + row.account_milestone_name_list
                + "' as account_milestone_name_list, "
            )
            cm_insert_q += (
                "'" + row.memo_milestone_name_list + "' as memo_milestone_name_list, "
            )
            cursor.execute(cm_insert_q)

        # if hasattr(self,'forecast_df'):
        if self.forecast_df is not None:
            tablename = username + "_Forecast_" + str(self.unique_id)

            if overwrite:
                cursor.execute("drop table if exists prod." + tablename)
                # log_in_color(logger, 'white', 'info', 'drop table if exists prod.'+tablename)
            DDL = "CREATE TABLE prod." + tablename + " (\n"
            # Date	Checking	Credit: Curr Stmt Bal	Credit: Prev Stmt Bal	test loan: Principal Balance	test loan: Interest	Marginal Interest	Net Gain	Net Loss	Net Worth	Loan Total	CC Debt Total	Liquid Total	Memo
            for i in range(0, len(self.forecast_df.columns)):
                column_name = (
                    '"' + self.forecast_df.columns[i] + '"'
                )  # adding quotes to preserve capitalization
                # todo isn't date missing ?
                if column_name == '"Memo"':
                    DDL += '"Memo" text'  # removing last comma. add double quotes just for consistency
                elif column_name == '"Memo Directives"':
                    DDL += '"Memo Directives" text, '  # removing last comma. add double quotes just for consistency
                else:
                    DDL += column_name + " float, "
                DDL += "\n"
            DDL += ")"
            # log_in_color(logger,'white','info',DDL)
            cursor.execute(DDL)

            # Not needed bc will be changed to insert / delete
            grant_q = "grant all privileges on prod." + tablename + " to " + username
            # log_in_color(logger,'white','info',grant_q)
            cursor.execute(grant_q)

            for index, row in self.forecast_df.iterrows():
                insert_q = "INSERT INTO prod." + tablename + " ("
                for i in range(0, len(self.forecast_df.columns)):
                    column_name = (
                        '"' + self.forecast_df.columns[i] + '"'
                    )  # adding quotes to preserve capitalization
                    if column_name == '"Date"':
                        insert_q += '"Date", '
                    elif column_name == '"Memo"':
                        insert_q += '"Memo"'
                        insert_q += " ) VALUES ("
                    elif column_name == '"Memo Directives"':
                        insert_q += '"Memo Directives", '
                    else:
                        insert_q += column_name + ", "

                for i in range(0, len(self.forecast_df.columns)):
                    column_name = (
                        '"' + self.forecast_df.columns[i] + '"'
                    )  # adding quotes to preserve capitalization
                    if column_name == '"Date"':
                        insert_q += "'" + str(row.Date) + "'" + ", "
                    elif column_name == '"Memo Directives"':
                        insert_q += "'" + str(row["Memo Directives"]) + "'" + ", "
                    elif column_name == '"Memo"':
                        insert_q += "'" + str(row.Memo) + "'"
                        insert_q += " )"

                    else:
                        insert_q += str(row[self.forecast_df.columns[i]]) + ", "
                # log_in_color(logger,'white','info',insert_q)
                cursor.execute(insert_q)

            # cursor.execute("TRUNCATE prod.ef_account_set_"+username+"_temporary")
            # cursor.execute("TRUNCATE prod.ef_budget_item_set_" + username+"_temporary")
            # cursor.execute("TRUNCATE prod.ef_memo_rule_set_" + username+"_temporary")
            # cursor.execute("INSERT INTO prod.ef_account_set_"+username+" Select '"+self.unique_id+"', account_name, balance, min_balance, max_balance, account_type, billing_start_date_yyyymmdd, apr, interest_cadence, minimum_payment, primary_checking_ind from prod.ef_account_set_"+username+"_temporary")
            # cursor.execute("INSERT INTO prod.ef_budget_item_set_"+username+" Select '" + self.unique_id + "', memo, priority, start_date, end_date,  cadence, amount, \"deferrable\", partial_payment_allowed from prod.ef_budget_item_set_"+username+"_temporary")
            # cursor.execute("INSERT INTO prod.ef_memo_rule_set_"+username+" Select '" + self.unique_id + "', memo_regex, account_from, account_to, priority from prod.ef_memo_rule_set_"+username+"_temporary")

            if overwrite:
                cursor.execute(
                    "drop table if exists prod."
                    + username
                    + "_milestone_results_"
                    + self.unique_id
                )
                # log_in_color(logger, 'white', 'info', 'drop table if exists prod.'+username+'_milestone_results_'+self.unique_id)

            cursor.execute(
                """CREATE TABLE prod."""
                + username
                + """_milestone_results_"""
                + self.unique_id
                + """ (
            forecast_id text,
            milestone_name text,
            milestone_type text,
            result_date date
            ) """
            )
            cursor.execute(
                "grant all privileges on prod."
                + username
                + "_milestone_results_"
                + self.unique_id
                + " to "
                + username
            )

            # log_in_color(logger, 'white', 'info', 'self.account_milestone_results')
            # log_in_color(logger, 'white', 'info', self.account_milestone_results)
            for k, v in self.account_milestone_results.items():
                if v == "None":
                    v = "null"
                else:
                    v = "'" + v + "'"

                insert_q = (
                    """INSERT INTO prod."""
                    + username
                    + """_milestone_results_"""
                    + self.unique_id
                    + """
                SELECT \'"""
                    + self.unique_id
                    + """\',\'"""
                    + k
                    + """\',\'Account\',"""
                    + v
                    + """
                """
                )
                # log_in_color(logger, 'white', 'info', insert_q)
                cursor.execute(insert_q)

            # log_in_color(logger, 'white', 'info', 'self.memo_milestone_results')
            # log_in_color(logger, 'white', 'info', self.memo_milestone_results)
            for k, v in self.memo_milestone_results.items():

                if v == "None":
                    v = "null"
                else:
                    v = "'" + v + "'"

                insert_q = (
                    """INSERT INTO prod."""
                    + username
                    + """_milestone_results_"""
                    + self.unique_id
                    + """
                                SELECT \'"""
                    + self.unique_id
                    + """\',\'"""
                    + k
                    + """\',\'Memo\',"""
                    + v
                    + """
                                """
                )
                # log_in_color(logger, 'white', 'info', insert_q)
                cursor.execute(insert_q)

            # log_in_color(logger, 'white', 'info', 'self.composite_milestone_results')
            # log_in_color(logger, 'white', 'info', self.composite_milestone_results)
            for k, v in self.composite_milestone_results.items():

                if v == "None":
                    v = "null"
                else:
                    v = "'" + v + "'"

                insert_q = (
                    """INSERT INTO prod."""
                    + username
                    + """_milestone_results_"""
                    + self.unique_id
                    + """
                                SELECT \'"""
                    + self.unique_id
                    + """\',\'"""
                    + k
                    + """\',\'Composite\',"""
                    + v
                    + """
                                """
                )
                # log_in_color(logger, 'white', 'info', insert_q)
                cursor.execute(insert_q)

            # print('self.start_ts:')
            # print(self.start_ts)

            # forecast_set_id, forecast_id, forecast_title, forecast_subtitle, submit_ts, complete_ts, error_flag, _satisfice_failed_flag, insert_ts
            metadata_q = "INSERT INTO prod." + username + "_forecast_run_metadata "
            metadata_q += (
                "Select '"
                + forecast_set_id
                + "' as forecast_set_id, '"
                + str(self.unique_id)
                + "' as forecast_id, "
            )
            metadata_q += "'" + self.forecast_set_name + "' as forecast_title, "
            metadata_q += "'" + self.forecast_name + "' as forecast_subtitle, "
            metadata_q += "'" + str(self.start_ts) + "' as submit_ts, "
            metadata_q += "'" + str(self.end_ts) + "' as complete_ts, "
            metadata_q += (
                "'" + str(0) + "' as error_flag, "
            )  # todo implement error flag
            metadata_q += (
                "'" + str(0) + "' as _satisfice_failed_flag, "
            )  # todo implement _satisfice failed flag
            metadata_q += (
                "'"
                + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                + "' as insert_ts "
            )
            cursor.execute(metadata_q)

    def __str__(self):

        left_margin_width = 5

        return_string = ""
        return_string += "ExpenseForecast object.\n"
        # return_string += self.forecast_title+"\n"
        # return_string +=  self.forecast_title+"\n"

        if self.forecast_df is None:
            return_string += """ This forecast has not yet been run. Use runForecast() to compute this forecast. """
            json_file_name = "FILE NAME UNDEFINED"
        else:
            # (if skipped is empty or min skipped priority is greater than 1) AND ( max forecast date == end date ) #todo check this second clause #https://github.com/hdickie/expense_forecast/issues/17

            return_string += (""" Start timestamp: """ + str(self.start_ts)).rjust(
                left_margin_width, " "
            ) + "\n"
            return_string += (""" End timestamp: """ + str(self.end_ts)).rjust(
                left_margin_width, " "
            ) + "\n"
            if self.end_ts is not None:
                end_dtts = datetime.datetime.strptime(self.end_ts, "%Y-%m-%d %H:%M:%S")
                start_dtts = datetime.datetime.strptime(
                    self.start_ts, "%Y-%m-%d %H:%M:%S"
                )
                seconds_elapsed = (end_dtts - start_dtts).seconds
                if seconds_elapsed >= 3600:
                    time_string = str(seconds_elapsed / (60 * 60)) + " hours"
                elif seconds_elapsed >= 60:
                    time_string = str(seconds_elapsed / 60) + " minutes"
                else:
                    time_string = str(seconds_elapsed) + " seconds"
                return_string += (""" Time Elapsed: """ + time_string).rjust(
                    left_margin_width, " "
                ) + "\n"

            # whether or not this object has ever been written to disk, we know its file name
            json_file_name = (
                "Forecast__" + str(self.unique_id) + "__" + self.start_ts + ".json"
            )

        return_string += (
            """Forecast  #"""
            + str(self.unique_id)
            + """: """
            + self.start_date_YYYYMMDD
            + """ -> """
            + self.end_date_YYYYMMDD
            + "\n"
        )
        return_string += (
            " "
            + (
                str(self.initial_account_set.getAccounts().shape[0])
                + """ accounts, """
                + str(self.initial_budget_set.getBudgetItems().shape[0])
                + """  budget items, """
                + str(self.initial_memo_rule_set.getMemoRules().shape[0])
                + """ memo rules."""
            ).rjust(left_margin_width, " ")
            + "\n"
        )
        return_string += " " + json_file_name + "\n"

        return_string += "\n Account Sets: \n"
        return_string += self.initial_account_set.getAccounts().to_string() + "\n"

        return_string += "\n Budget schedule items: \n"
        return_string += self.initial_budget_set.getBudgetItems().to_string() + "\n"

        return_string += "\n Memo Rules: \n"
        return_string += self.initial_memo_rule_set.getMemoRules().to_string() + "\n"

        return_string += "\n Account Milestones: \n"
        return_string += self.milestone_set.getAccountMilestonesDF().to_string() + "\n"

        return_string += "\n Memo Milestones: \n"
        return_string += self.milestone_set.getMemoMilestonesDF().to_string() + "\n"

        return_string += "\n Composite Milestones: \n"
        return_string += (
            self.milestone_set.getCompositeMilestonesDF().to_string() + "\n"
        )

        if self.forecast_df is not None:
            return_string += "Final Forecast Row:\n"
            return_string += self.forecast_df.tail(1).to_string() + "\n"

            return_string += "\n Account Milestone Results: \n"
            return_string += str(self.account_milestone_results) + "\n"

            return_string += "\n Memo Milestones Results: \n"
            return_string += str(self.memo_milestone_results) + "\n"

            return_string += "\n Composite Milestones Results: \n"
            return_string += str(self.composite_milestone_results) + "\n"

        return return_string

    def __init__(
        self,
        account_set,
        budget_set,
        memo_rule_set,
        start_date_YYYYMMDD,
        end_date_YYYYMMDD,
        milestone_set,
        approximate_flag=False,
        log_directory=".",
        forecast_set_name="",
        forecast_name="",
        print_debug_messages=True,
        raise_exceptions=True,
    ):
        """
        ExpenseForecast one-line description


        :param account_set:
        :param budget_set:
        :param memo_rule_set:
        """

        self.forecast_set_name = str(forecast_set_name)
        self.forecast_name = str(forecast_name)
        self.approximate_flag = approximate_flag
        self.forecast_df = None
        self.skipped_df = None
        self.confirmed_df = None
        self.deferred_df = None
        self.start_ts = None
        self.end_ts = None

        try:
            datetime.datetime.strptime(str(start_date_YYYYMMDD), "%Y%m%d")
            self.start_date_YYYYMMDD = str(start_date_YYYYMMDD)
        except Exception:
            print("value was:" + str(start_date_YYYYMMDD) + "\n")
            raise ValueError(
                "Failed to cast start_date_YYYYMMDD to datetime with format %Y%m%d: "
                + str(start_date_YYYYMMDD)
            )

        try:
            datetime.datetime.strptime(str(end_date_YYYYMMDD), "%Y%m%d")
            self.end_date_YYYYMMDD = str(end_date_YYYYMMDD)
        except Exception:
            raise ValueError(
                "Failed to cast end_date_YYYYMMDD to datetime with format %Y%m%d: "
                + str(end_date_YYYYMMDD)
            )

        if datetime.datetime.strptime(
            str(start_date_YYYYMMDD), "%Y%m%d"
        ) >= datetime.datetime.strptime(str(end_date_YYYYMMDD), "%Y%m%d"):
            raise ValueError(
                str(self.start_date_YYYYMMDD) + " >= " + str(self.end_date_YYYYMMDD)
            )  # start_date must be before end_date

        accounts_df = account_set.getAccounts()
        if accounts_df.shape[0] == 0:
            # if len(account_set) == 0:
            raise ValueError  # There needs to be at least 1 account for ExpenseForecast to do anything.
        # todo more strict checking #https://github.com/hdickie/expense_forecast/issues/18

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
            pd.DataFrame(accounts_df.Name)
            .apply(lambda x: x[0].split(":")[0], axis=1)
            .drop_duplicates()
        ).rename(columns={0: "Name"})
        account_names__from_memo = pd.concat(
            [
                pd.DataFrame(memo_df[["Account_From"]]).rename(
                    columns={"Account_From": "Name"}
                ),
                pd.DataFrame(memo_df[["Account_To"]]).rename(
                    columns={"Account_To": "Name"}
                ),
            ]
        )

        distinct_account_names__from_memo = pd.DataFrame(
            account_names__from_memo.loc[
                account_names__from_memo.Name != "None", "Name"
            ]
            .drop_duplicates()
            .reset_index(drop=True)
        )

        A = None
        B = None
        try:

            A = {""}
            for a in distinct_account_names__from_memo.Name.tolist():
                A = A.union({a})
            A = A - {
                "ALL_LOANS"
            }  # if we have a memo rule for ALL_LOANS, we don't want that to be checked against the list of account names

            A2 = {""}
            for a in distinct_base_account_names__from_acct.Name.tolist():
                A2 = A2.union({a})

            B = A.intersection(A2)

            assert A == B
        except Exception as e:
            error_text = str(e.args) + "\n"
            error_text += "An account name was mentioned in a memo rule that did not exist in the account set\n"
            error_text += "all accounts mentioned in memo rules:\n"
            error_text += distinct_account_names__from_memo.Name.to_string() + "\n"
            error_text += "all defined accounts:\n"
            error_text += distinct_base_account_names__from_acct.Name.to_string() + "\n"
            error_text += "intersection:\n"
            error_text += str(B) + "\n"
            error_text += "Accounts from Memo:\n"
            error_text += str(A) + "\n"
            error_ind = True

        for index, row in budget_df.iterrows():
            memo_rule_set.findMatchingMemoRule(
                row.Memo, row.Priority
            )  # this will throw errors as needed

        if print_debug_messages:
            if error_ind:
                print(error_text)

        if raise_exceptions:
            if error_ind:
                log_in_color(logger, "red", "error", error_text)
                raise ValueError(error_text)

        self.initial_account_set = copy.deepcopy(account_set)
        self.initial_budget_set = copy.deepcopy(budget_set)
        self.initial_memo_rule_set = copy.deepcopy(memo_rule_set)

        self.log_stack_depth = 0

        first_proposed_df = budget_set.getBudgetSchedule()

        lb_sel_vec = [
            datetime.datetime.strptime(self.start_date_YYYYMMDD, "%Y%m%d")
            <= datetime.datetime.strptime(d, "%Y%m%d")
            for d in first_proposed_df.Date
        ]
        rb_sel_vec = [
            datetime.datetime.strptime(d, "%Y%m%d")
            <= datetime.datetime.strptime(self.end_date_YYYYMMDD, "%Y%m%d")
            for d in first_proposed_df.Date
        ]
        date_range_sel_vec = lb_sel_vec and rb_sel_vec

        # todo I don't understand why this is not working
        proposed_df = first_proposed_df[date_range_sel_vec]
        proposed_df.reset_index(drop=True, inplace=True)

        # todo this works instead of the above and I don't know why
        if not proposed_df.empty:
            proposed_df = proposed_df[proposed_df.Date >= self.start_date_YYYYMMDD]
        if not proposed_df.empty:
            proposed_df = proposed_df[proposed_df.Date <= self.end_date_YYYYMMDD]

        # otherwise proposed has no columns
        if proposed_df.empty:
            proposed_df = pd.DataFrame(
                {
                    "Date": [],
                    "Priority": [],
                    "Amount": [],
                    "Memo": [],
                    "Deferrable": [],
                    "Partial_Payment_Allowed": [],
                }
            )

        # take priority 1 items and put them in confirmed
        confirmed_df = proposed_df[proposed_df.Priority == 1]
        confirmed_df.reset_index(drop=True, inplace=True)

        proposed_df = proposed_df[proposed_df.Priority != 1]
        proposed_df.reset_index(drop=True, inplace=True)

        deferred_df = copy.deepcopy(proposed_df.head(0))
        skipped_df = copy.deepcopy(proposed_df.head(0))

        account_hash = hashlib.sha1(
            account_set.getAccounts().to_string().encode("utf-8")
        ).hexdigest()
        budget_hash = hashlib.sha1(
            budget_set.getBudgetItems().to_string().encode("utf-8")
        ).hexdigest()
        memo_hash = hashlib.sha1(
            memo_rule_set.getMemoRules().to_string().encode("utf-8")
        ).hexdigest()
        start_date_hash = int(start_date_YYYYMMDD)
        end_date_hash = int(end_date_YYYYMMDD)

        num_days = (
            datetime.datetime.strptime(end_date_YYYYMMDD, "%Y%m%d")
            - datetime.datetime.strptime(start_date_YYYYMMDD, "%Y%m%d")
        ).days
        num_distinct_priority = len(
            set(self.initial_budget_set.getBudgetItems().Priority)
        )
        self.unique_id = (
            start_date_YYYYMMDD[2:]
            + "_"
            + str(num_days)
            + "_"
            + str(num_distinct_priority)
            + "_"
        )
        self.unique_id += str(
            hash(
                int(account_hash, 16)
                + int(budget_hash, 16)
                + int(memo_hash, 16)
                + start_date_hash
                + end_date_hash
            )
            % 1000
        ).rjust(4, "0")
        if self.approximate_flag:
            self.unique_id += "A"

        single_forecast_run_log_file_name = "Forecast_" + str(self.unique_id) + ".log"
        log_in_color(
            logger,
            "green",
            "debug",
            "Attempting switch log file to: " + single_forecast_run_log_file_name,
        )

        self.initial_proposed_df = proposed_df
        self.initial_deferred_df = deferred_df
        self.initial_skipped_df = skipped_df
        self.initial_confirmed_df = confirmed_df

        self.milestone_set = milestone_set

        self.account_milestone_results = {}
        self.memo_milestone_results = {}
        self.composite_milestone_results = {}

    def _appendSummaryLines(self):

        account_info = self.initial_account_set.getAccounts()

        loan_acct_sel_vec = (account_info.Account_Type == "principal balance") | (
            account_info.Account_Type == "interest"
        )
        cc_acct_sel_vec = (account_info.Account_Type == "credit prev stmt bal") | (
            account_info.Account_Type == "credit curr stmt bal"
        )
        checking_sel_vec = account_info.Account_Type == "checking"

        loan_acct_info = account_info.loc[loan_acct_sel_vec, :]
        credit_acct_info = account_info.loc[cc_acct_sel_vec, :]
        # savings_acct_info = account_info[account_info.Account_Type.lower() == 'savings', :]

        NetWorth = self.forecast_df.Checking
        for loan_account_index, loan_account_row in loan_acct_info.iterrows():
            # loan_acct_col_sel_vec = (self.forecast_df.columns == loan_account_row.Name)
            # print('loan_acct_col_sel_vec')
            # print(loan_acct_col_sel_vec)
            NetWorth = NetWorth - self.forecast_df.loc[:, loan_account_row.Name]

        for credit_account_index, credit_account_row in credit_acct_info.iterrows():
            NetWorth = NetWorth - self.forecast_df.loc[:, credit_account_row.Name]

        # for savings_account_index, savings_account_row in savings_acct_info.iterrows():
        #     NetWorth += self.forecast_df[:,self.forecast_df.columns == savings_account_row.Name]

        LoanTotal = self.forecast_df.Checking - self.forecast_df.Checking
        for loan_account_index, loan_account_row in loan_acct_info.iterrows():
            LoanTotal = LoanTotal + self.forecast_df.loc[:, loan_account_row.Name]

        CCDebtTotal = self.forecast_df.Checking - self.forecast_df.Checking
        for credit_account_index, credit_account_row in credit_acct_info.iterrows():
            CCDebtTotal = CCDebtTotal + self.forecast_df.loc[:, credit_account_row.Name]

        self.forecast_df["Marginal Interest"] = 0
        loan_interest_acct_sel_vec = account_info.Account_Type == "interest"
        cc_curr_stmt_acct_sel_vec = account_info.Account_Type == "credit curr stmt bal"
        cc_prev_stmt_acct_sel_vec = account_info.Account_Type == "credit prev stmt bal"

        loan_interest_acct_info = account_info.loc[loan_interest_acct_sel_vec, :]
        cc_curr_stmt_acct_info = account_info.loc[cc_curr_stmt_acct_sel_vec, :]
        cc_prev_stmt_acct_info = account_info.loc[cc_prev_stmt_acct_sel_vec, :]

        previous_row = None
        for index, row in self.forecast_df.iterrows():
            if index == 0:
                previous_row = row
                continue

            prev_curr_stmt_bal = (
                pd.DataFrame(previous_row).T.iloc[:, cc_curr_stmt_acct_info.index + 1].T
            )
            today_curr_stmt_bal = (
                pd.DataFrame(row).T.iloc[:, cc_curr_stmt_acct_info.index + 1].T
            )
            prev_prev_stmt_bal = (
                pd.DataFrame(previous_row).T.iloc[:, cc_prev_stmt_acct_info.index + 1].T
            )
            today_prev_stmt_bal = (
                pd.DataFrame(row).T.iloc[:, cc_prev_stmt_acct_info.index + 1].T
            )

            prev_interest = (
                pd.DataFrame(previous_row)
                .T.iloc[:, loan_interest_acct_info.index + 1]
                .T
            )
            # print('prev_interest:')
            # print(prev_interest)

            today_interest = (
                pd.DataFrame(row).T.iloc[:, loan_interest_acct_info.index + 1].T
            )
            # print('today_interest:')
            # print(today_interest)

            delta = 0

            # this is needless
            assert prev_curr_stmt_bal.shape[0] == prev_prev_stmt_bal.shape[0]

            # additional loan payment
            # loan min payment
            # memo has cc min payment on days where

            # cc min payment is 1% of balance plus interest. min pay = bal*0.01 + interest
            # therefore interest = min pay - bal*0.01
            if "CC INTEREST" in row["Memo Directives"]:

                memo_directives_line = row["Memo Directives"]
                memo_directives_line_items = memo_directives_line.split(";")
                for memo_directives_line_item in memo_directives_line_items:
                    memo_directives_line_item = memo_directives_line_item.strip()
                    if "CC INTEREST" not in memo_directives_line_item:
                        continue

                    value_match = re.search(
                        r"\(([A-Za-z0-9_ :]*) ([-+]?\$.*)\)$", memo_directives_line_item
                    )
                    line_item_value_string = value_match.group(2)
                    line_item_value_string = (
                        line_item_value_string.replace("(", "")
                        .replace(")", "")
                        .replace("$", "")
                    )
                    line_item_value = float(line_item_value_string)

                    if "CC INTEREST" in memo_directives_line_item:
                        self.forecast_df.loc[index, "Marginal Interest"] += abs(
                            line_item_value
                        )

            if prev_interest.shape[0] > 0:
                delta = 0
                for i in range(0, prev_interest.shape[0]):
                    new_delta = float(today_interest.iloc[i, 0]) - float(
                        prev_interest.iloc[i, 0]
                    )
                    # print(row.Date + ' ' + str(delta) + ' += balance delta (' + str(new_delta) + ') yields: ' + str(round(delta + new_delta,2)))
                    delta = delta + new_delta

                if (
                    "LOAN MIN PAYMENT" in row["Memo Directives"]
                    or "ADDTL LOAN PAYMENT" in row["Memo Directives"]
                ):
                    memo_directives_line = row["Memo Directives"]
                    memo_directives_line_items = memo_directives_line.split(";")
                    for memo_directives_line_item in memo_directives_line_items:
                        memo_directives_line_item = memo_directives_line_item.strip()
                        if memo_directives_line_item == "":
                            continue
                        value_match = re.search(
                            r"\(([A-Za-z0-9_ :]*) ([-+]?\$.*)\)$",
                            memo_directives_line_item,
                        )
                        # print('memo_directives_line_item:'+str(memo_directives_line_item))
                        line_item_account_name = value_match.group(1)
                        if ": Interest" in line_item_account_name:
                            line_item_value_string = value_match.group(2)
                            line_item_value_string = (
                                line_item_value_string.replace("(", "")
                                .replace(")", "")
                                .replace("$", "")
                            )
                            line_item_value = float(line_item_value_string)
                            new_delta = abs(
                                line_item_value
                            )  # this was already subtracted above, so we are putting it back
                            # print(row.Date + ' ' + str(delta) + ' += memo delta ' + str(new_delta) + ' yields: ' + str(round(delta + new_delta,2)))
                            delta = delta + new_delta

                self.forecast_df.loc[index, "Marginal Interest"] += delta
                # print('')

            previous_row = row

        # just memo
        self.forecast_df["Net Gain"] = 0
        self.forecast_df["Net Loss"] = self.forecast_df["Marginal Interest"]
        for index, row in self.forecast_df.iterrows():

            self.forecast_df.loc[index, "Net Loss"] = abs(
                self.forecast_df.loc[index, "Net Loss"]
            )

            memo_line = row.Memo
            memo_line_items = memo_line.split(";")
            for memo_line_item in memo_line_items:
                memo_line_item = memo_line_item.strip()
                if memo_line_item == "":
                    continue

                # handled in memo directive
                # #loss was already taken to account when txn was first made, any paying debts is net 0
                # if 'LOAN MIN PAYMENT' in memo_line_item or 'CC MIN PAYMENT' in memo_line_item or 'ADDTL CC PAYMENT' in memo_line_item:
                #     continue

                try:
                    value_match = re.search(
                        r"\(([A-Za-z0-9_ :]*) ([-+]?\$.*)\)$", memo_line_item
                    )
                    line_item_account_name = value_match.group(1)
                    line_item_value_string = value_match.group(2)

                    if (
                        ": Interest" in line_item_account_name
                        or ": Principal Balance" in line_item_account_name
                    ):
                        continue

                    line_item_value_string = (
                        line_item_value_string.replace("(", "")
                        .replace(")", "")
                        .replace("$", "")
                    )
                except Exception as e:
                    error_text = e.args
                    raise ValueError(str(error_text) + "\nMalformed memo value")

                # Moved to memo directive
                line_item_value = float(line_item_value_string)
                if "income" in memo_line_item.lower():
                    # self.forecast_df.loc[index,'Net Gain'] += abs(line_item_value)
                    pass  # todo income needs to not be in memo. this is a known vulnerability bc of this right here #https://github.com/hdickie/expense_forecast/issues/19
                else:
                    # print(str(self.forecast_df.loc[index, 'Date'])+' Net Loss before update '+str(self.forecast_df.loc[index, 'Net Loss']) )
                    self.forecast_df.loc[index, "Net Loss"] += abs(line_item_value)

                    # print(str(self.forecast_df.loc[index, 'Date'])+' Net Loss += '+str(abs(line_item_value))+' '+str(memo_line_item)+' = '+str(self.forecast_df.loc[index,'Net Loss']))

        # just memo directive
        for index, row in self.forecast_df.iterrows():
            memo_line = row["Memo Directives"]
            memo_line_items = memo_line.split(";")
            for memo_line_item in memo_line_items:
                memo_line_item = memo_line_item.strip()

                if memo_line_item == "":
                    continue

                # loss was already taken to account when txn was first made, any paying debts is net 0
                if (
                    "LOAN MIN PAYMENT" in memo_line_item
                    or "ADDTL CC PAYMENT" in memo_line_item
                    or "CC MIN PAYMENT" in memo_line_item
                    or "ADDTL LOAN PAYMENT" in memo_line_item
                    or "CC INTEREST" in memo_line_item
                ):
                    continue

                try:
                    value_match = re.search(
                        r"\(([A-Za-z0-9_ :]*) ([-+]?\$.*)\)$", memo_line_item
                    )
                    line_item_account_name = value_match.group(1)
                    line_item_value_string = value_match.group(2)

                    if (
                        ": Interest" in line_item_account_name
                        or ": Principal Balance" in line_item_account_name
                    ):
                        continue

                    line_item_value_string = (
                        line_item_value_string.replace("(", "")
                        .replace(")", "")
                        .replace("$", "")
                    )
                except Exception as e:
                    error_text = e.args
                    raise ValueError(str(error_text) + "\nMalformed memo value")

                line_item_value = float(line_item_value_string)
                if "INCOME" in memo_line_item:
                    self.forecast_df.loc[index, "Net Gain"] += abs(line_item_value)
                    # print(str(self.forecast_df.loc[index, 'Date']) + ' Net Gain += ' + str( abs(line_item_value)) + ' ' + str(memo_line_item) + ' = ' + str( self.forecast_df.loc[index, 'Net Gain']))
                else:
                    self.forecast_df.loc[index, "Net Loss"] += abs(line_item_value)
                    # print(str(self.forecast_df.loc[index, 'Date']) + ' Net Loss += ' + str(abs(line_item_value))+' '+str(memo_line_item)+' = '+str(self.forecast_df.loc[index,'Net Loss']))

            if (
                self.forecast_df.loc[index, "Net Loss"] > 0
                and self.forecast_df.loc[index, "Net Gain"] > 0
            ):
                if (
                    self.forecast_df.loc[index, "Net Gain"]
                    > self.forecast_df.loc[index, "Net Loss"]
                ):
                    self.forecast_df.loc[index, "Net Gain"] -= self.forecast_df.loc[
                        index, "Net Loss"
                    ]
                    self.forecast_df.loc[index, "Net Loss"] = 0
                else:
                    self.forecast_df.loc[index, "Net Loss"] -= self.forecast_df.loc[
                        index, "Net Gain"
                    ]
                    self.forecast_df.loc[index, "Net Gain"] = 0

        # Final QC. If we trust the code, we can comment this out
        # checking, credit, loan,
        # loan_acct_sel_vec = loan_acct_sel_vec.append(pd.Series([False])) #this works

        loan_acct_sel_vec = pd.concat(
            [pd.Series([False]), loan_acct_sel_vec, pd.Series([False] * 6)]
        )
        cc_acct_sel_vec = pd.concat(
            [pd.Series([False]), cc_acct_sel_vec, pd.Series([False] * 6)]
        )
        checking_sel_vec = pd.concat(
            [pd.Series([False]), checking_sel_vec, pd.Series([False] * 6)]
        )

        # loan_acct_sel_vec = pd.concat([False],loan_acct_sel_vec,[False] * 5)
        # cc_acct_sel_vec = pd.concat([False], cc_acct_sel_vec, [False] * 5)
        # checking_sel_vec = pd.concat([False], checking_sel_vec, [False] * 5)

        loan_acct_sel_vec = loan_acct_sel_vec.reset_index(drop=True)
        cc_acct_sel_vec = cc_acct_sel_vec.reset_index(drop=True)
        checking_sel_vec = checking_sel_vec.reset_index(drop=True)

        check_row_delta = 0
        cc_row_delta = 0
        loan_row_delta = 0

        log_in_color(
            logger, "magenta", "debug", "Forecast Pre-Validation", self.log_stack_depth
        )
        log_in_color(
            logger,
            "magenta",
            "debug",
            self.forecast_df.to_string(),
            self.log_stack_depth,
        )
        log_in_color(
            logger, "magenta", "debug", "Validation Delta Values", self.log_stack_depth
        )
        log_data_header_string = (
            "Date".rjust(10)
            + " "
            + "Check".rjust(10)
            + " "
            + "CC".rjust(10)
            + " "
            + "Loan".rjust(10)
            + " "
            + "Net +".rjust(10)
            + " "
            + "Net -".rjust(10)
        )
        log_in_color(
            logger, "magenta", "debug", log_data_header_string, self.log_stack_depth
        )

        fail_flag = False
        for f_i, row in self.forecast_df.iterrows():
            loan_acct_sel_vec.index = row.index
            cc_acct_sel_vec.index = row.index
            checking_sel_vec.index = row.index

            if sum(loan_acct_sel_vec) > 0:
                loan_row_total = sum(row[loan_acct_sel_vec])
                # print('loan_row_total:')
                # print(loan_row_total)
            else:
                loan_row_total = 0

            if sum(cc_acct_sel_vec) > 0:
                cc_row_total = sum(row[cc_acct_sel_vec])
                # print('cc_row_total:')
                # print(cc_row_total)
            else:
                cc_row_total = 0

            check_row_total = sum(row[checking_sel_vec])
            # print('check_row_total:')
            # print(check_row_total)

            if f_i == 0:
                previous_check_row_total = check_row_total
                previous_cc_row_total = cc_row_total
                previous_loan_row_total = loan_row_total
                continue

            # check_row_delta = round(check_row_total - previous_check_row_total,2)
            # cc_row_delta = round(cc_row_total - previous_cc_row_total,2)
            # loan_row_delta = round(loan_row_total - previous_loan_row_total,2)

            previous_check_row_total = check_row_total
            previous_cc_row_total = cc_row_total
            previous_loan_row_total = loan_row_total

            row_df = pd.DataFrame(row).T

            # net_gain = round(row_df['Net Gain'].iat[0],2)
            # net_loss = round(row_df['Net Loss'].iat[0],2)

            net_gain = row_df["Net Gain"].iat[0]
            net_loss = row_df["Net Loss"].iat[0]

            memo = row_df["Memo"].iat[0]
            md = row_df["Memo Directives"].iat[0]

            log_string = str(
                row["Date"].rjust(10)
                + " "
                + str(check_row_delta).rjust(10)
                + " "
                + str(cc_row_delta).rjust(10)
                + " "
                + str(loan_row_delta).rjust(10)
                + " "
                + str(net_gain).rjust(10)
                + " "
                + str(net_loss).rjust(10)
            )
            log_in_color(logger, "magenta", "debug", log_string, self.log_stack_depth)
            # if round(check_row_delta - (cc_row_delta + loan_row_delta),2) < 0:
            if check_row_delta - (cc_row_delta + loan_row_delta) < 0:
                try:
                    # assert -1*round(net_loss,2) == round((check_row_delta - (cc_row_delta + loan_row_delta)),2)
                    assert -1 * net_loss == (
                        check_row_delta - (cc_row_delta + loan_row_delta)
                    )
                except Exception as e:
                    # log_in_color(logger, 'red', 'debug', 'Validation FAIL -1*round(net_loss,2) == round((check_row_delta - (cc_row_delta + loan_row_delta)),2) was not TRUE', self.log_stack_depth)
                    log_in_color(
                        logger,
                        "red",
                        "debug",
                        "Validation FAIL -1*net_loss == (check_row_delta - (cc_row_delta + loan_row_delta)) was not TRUE",
                        self.log_stack_depth,
                    )
                    log_in_color(
                        logger,
                        "magenta",
                        "debug",
                        "Memo...........: " + str(memo),
                        self.log_stack_depth,
                    )
                    log_in_color(
                        logger,
                        "magenta",
                        "debug",
                        "Md.............: " + str(md),
                        self.log_stack_depth,
                    )
                    # log_in_color(logger, 'magenta', 'debug', str(-1*net_loss)+' != '+str( round((check_row_delta - (cc_row_delta + loan_row_delta)),2) ) , self.log_stack_depth)
                    log_in_color(
                        logger,
                        "magenta",
                        "debug",
                        str(-1 * net_loss)
                        + " != "
                        + str((check_row_delta - (cc_row_delta + loan_row_delta))),
                        self.log_stack_depth,
                    )
                    log_in_color(logger, "magenta", "debug", "", self.log_stack_depth)

                    fail_flag = True

            # if round(check_row_delta - (cc_row_delta + loan_row_delta),2) > 0:
            if check_row_delta - (cc_row_delta + loan_row_delta) > 0:
                try:
                    # assert round(net_gain,2) == round((check_row_delta - (cc_row_delta + loan_row_delta)),2)
                    assert net_gain == (
                        check_row_delta - (cc_row_delta + loan_row_delta)
                    )
                except Exception as e:
                    # log_in_color(logger, 'red', 'debug', 'Validation FAIL round(net_gain,2) == round((check_row_delta - (cc_row_delta + loan_row_delta)),2) was not TRUE', self.log_stack_depth)
                    log_in_color(
                        logger,
                        "red",
                        "debug",
                        "Validation FAIL net_gain == (check_row_delta - (cc_row_delta + loan_row_delta)) was not TRUE",
                        self.log_stack_depth,
                    )
                    log_in_color(
                        logger,
                        "magenta",
                        "debug",
                        "Memo...........: " + str(memo),
                        self.log_stack_depth,
                    )
                    log_in_color(
                        logger,
                        "magenta",
                        "debug",
                        "Md.............: " + str(md),
                        self.log_stack_depth,
                    )
                    # log_in_color(logger, 'magenta', 'debug', str(net_gain)+' != '+str( round((check_row_delta - (cc_row_delta + loan_row_delta)),2) ) , self.log_stack_depth)
                    log_in_color(
                        logger,
                        "magenta",
                        "debug",
                        str(net_gain)
                        + " != "
                        + str((check_row_delta - (cc_row_delta + loan_row_delta))),
                        self.log_stack_depth,
                    )

                    fail_flag = True

        if fail_flag:
            log_in_color(
                logger, "red", "debug", "Validation FAIL", self.log_stack_depth
            )
        else:
            log_in_color(
                logger, "green", "debug", "Validation SUCCESS", self.log_stack_depth
            )

        LiquidTotal = self.forecast_df.Checking

        self.forecast_df["Net Worth"] = NetWorth
        self.forecast_df["Loan Total"] = LoanTotal
        self.forecast_df["CC Debt Total"] = CCDebtTotal
        self.forecast_df["Liquid Total"] = LiquidTotal

        memo_column = copy.deepcopy(self.forecast_df["Memo"])
        memo_directives_column = copy.deepcopy(self.forecast_df["Memo Directives"])
        next_income_date_column = copy.deepcopy(self.forecast_df["Next Income Date"])
        self.forecast_df = self.forecast_df.drop(
            columns=["Memo", "Memo Directives", "Next Income Date"]
        )
        self.forecast_df["Next Income Date"] = next_income_date_column
        self.forecast_df["Memo Directives"] = memo_directives_column
        self.forecast_df["Memo"] = memo_column

    def _satisficeApproximate(
        self,
        list_of_date_strings,
        confirmed_df,
        account_set,
        memo_rule_set,
        forecast_df,
        raise__satisfice_failed_exception,
        progress_bar=None,
    ):
        # log_in_color(logger, 'cyan', 'debug', 'ENTER _satisficeApproximate()', self.log_stack_depth)
        self.log_stack_depth += 1
        all_days = (
            list_of_date_strings  # just rename it so it's more clear for the context
        )

        for d in all_days:
            if progress_bar is not None:
                progress_bar.update(1)
                progress_bar.refresh()

            if d == self.start_date_YYYYMMDD:
                if not raise__satisfice_failed_exception:
                    # log_in_color(logger, 'white', 'debug', 'Starting Approximate Satisfice.')
                    # log_in_color(logger, 'white', 'debug', self.start_date_YYYYMMDD + ' -> ' + self.end_date_YYYYMMDD)
                    # log_in_color(logger, 'white', 'debug', 'p Date           iteration time elapsed')
                    last_iteration = datetime.datetime.now()
                continue  # first day is considered final
            log_in_color(logger, "magenta", "info", "p1 " + str(d))

            try:
                if not raise__satisfice_failed_exception:
                    last_iteration_time_elapsed = (
                        datetime.datetime.now() - last_iteration
                    )
                    last_iteration = datetime.datetime.now()
                    log_string = (
                        str(1)
                        + " "
                        + datetime.datetime.strptime(d, "%Y%m%d").strftime("%Y-%m-%d")
                    )
                    log_string += "     " + str(last_iteration_time_elapsed)
                    # log_in_color(logger, 'white', 'debug', log_string)

                # print('forecast before eTFD:')
                # print(forecast_df.to_string())
                forecast_df, confirmed_df, deferred_df, skipped_df = (
                    self._executeTransactionsForDayApproximate(
                        account_set=account_set,
                        forecast_df=forecast_df,
                        date_YYYYMMDD=d,
                        memo_set=memo_rule_set,
                        confirmed_df=confirmed_df,
                        proposed_df=confirmed_df.head(
                            0
                        ),  # no proposed txns in _satisfice
                        deferred_df=confirmed_df.head(
                            0
                        ),  # no deferred txns in _satisfice
                        skipped_df=confirmed_df.head(
                            0
                        ),  # no skipped txns in _satisfice
                        priority_level=1,
                    )
                )
                # print('forecast after eTFD:')
                # print(forecast_df.to_string())

                # pre_sync = pd.DataFrame(account_set.getAccounts(),copy=True)
                account_set = self._sync_account_set_w_forecast_day(
                    account_set, forecast_df, d
                )
                # assert pre_sync.to_string() == account_set.getAccounts().to_string() #the program is not reaching a minimum payments day so this check isnt working yet

                forecast_df[forecast_df.Date == d] = (
                    self._calculateLoanInterestAccrualsForDay(
                        account_set, forecast_df[forecast_df.Date == d]
                    )
                )
                account_set = self._sync_account_set_w_forecast_day(
                    account_set, forecast_df, d
                )
                forecast_df[forecast_df.Date == d] = self._executeLoanMinimumPayments(
                    account_set, forecast_df[forecast_df.Date == d]
                )
                account_set = self._sync_account_set_w_forecast_day(
                    account_set, forecast_df, d
                )
                # todo NOTE THAT ADDITIONAL CC PAYMENTS ARE NOT CREDITED BEFORE INTEREST ACCURAL
                forecast_df[forecast_df.Date == d] = (
                    self._executeCreditCardMinimumPayments(
                        forecast_df, account_set, forecast_df[forecast_df.Date == d]
                    )
                )
                account_set = self._sync_account_set_w_forecast_day(
                    account_set, forecast_df, d
                )

                # post_min_payments_row = self.executeMinimumPayments(account_set, forecast_df[forecast_df.Date == d])
                # forecast_df[forecast_df.Date == d] = post_min_payments_row
                # account_set = self._sync_account_set_w_forecast_day(account_set, forecast_df, d)
                # forecast_df[forecast_df.Date == d] = self.calculateInterestAccrualsForDay(account_set, forecast_df[forecast_df.Date == d])  # returns only a forecast row
                #

                # print('about to go to next loop iteration')
            except ValueError as e:
                if (
                    re.search(".*Account boundaries were violated.*", str(e.args))
                    is not None
                ) and not raise__satisfice_failed_exception:
                    self.end_date = datetime.datetime.strptime(
                        d, "%Y%m%d"
                    ) - datetime.timedelta(days=1)

                    log_in_color(
                        logger,
                        "cyan",
                        "error",
                        "State at failure:",
                        self.log_stack_depth,
                    )
                    log_in_color(
                        logger,
                        "cyan",
                        "error",
                        forecast_df.to_string(),
                        self.log_stack_depth,
                    )

                    self.log_stack_depth -= 1
                    # log_in_color(logger, 'cyan', 'debug', 'EXIT _satisfice()', self.log_stack_depth)
                    return forecast_df
                else:
                    raise e

        # log_in_color(logger, 'white', 'info', forecast_df.to_string(), self.log_stack_depth)

        self.log_stack_depth -= 1
        # log_in_color(logger, 'cyan', 'debug', 'EXIT approximateSatisfice()', self.log_stack_depth)
        return forecast_df  # this is the _satisfice_success = true

    def _computeOptimalForecastApproximate(
        self,
        start_date_YYYYMMDD,
        end_date_YYYYMMDD,
        confirmed_df,
        proposed_df,
        deferred_df,
        skipped_df,
        account_set,
        memo_rule_set,
        raise__satisfice_failed_exception=True,
        progress_bar=None,
    ):
        # log_in_color(logger, 'cyan', 'debug', 'ENTER _computeOptimalForecastApproximate()', self.log_stack_depth)
        # log_in_color(logger, 'cyan', 'debug', 'start_date_YYYYMMDD:' + str(start_date_YYYYMMDD), self.log_stack_depth)
        # log_in_color(logger, 'cyan', 'debug', 'end_date_YYYYMMDD:' + str(end_date_YYYYMMDD), self.log_stack_depth)
        self.log_stack_depth += 1

        confirmed_df.reset_index(drop=True, inplace=True)
        proposed_df.reset_index(drop=True, inplace=True)
        deferred_df.reset_index(drop=True, inplace=True)
        skipped_df.reset_index(drop=True, inplace=True)

        # log_in_color(logger, 'cyan', 'debug', 'confirmed_df:', self.log_stack_depth)
        # log_in_color(logger, 'cyan', 'debug', confirmed_df.to_string(), self.log_stack_depth)
        #
        # log_in_color(logger, 'cyan', 'debug', 'proposed_df:', self.log_stack_depth)
        # log_in_color(logger, 'cyan', 'debug', proposed_df.to_string(), self.log_stack_depth)
        #
        # log_in_color(logger, 'cyan', 'debug', 'deferred_df:', self.log_stack_depth)
        # log_in_color(logger, 'cyan', 'debug', deferred_df.to_string(), self.log_stack_depth)
        #
        # log_in_color(logger, 'cyan', 'debug', 'skipped_df:', self.log_stack_depth)
        # log_in_color(logger, 'cyan', 'debug', skipped_df.to_string(), self.log_stack_depth)

        # only one day per month
        no_days = (
            datetime.datetime.strptime(end_date_YYYYMMDD, "%Y%m%d")
            - datetime.datetime.strptime(start_date_YYYYMMDD, "%Y%m%d")
        ).days
        all_days = generate_date_sequence(start_date_YYYYMMDD, no_days, "monthly")

        if datetime.datetime.strptime(
            all_days[len(all_days) - 1], "%Y%m%d"
        ) > datetime.datetime.strptime(end_date_YYYYMMDD, "%Y%m%d"):
            all_days = all_days[0: (len(all_days) - 1)]

        # Schema is: Date, <a column for each account>, Memo
        forecast_df = self._getInitialForecastRow(start_date_YYYYMMDD, account_set)
        # print('_getInitialForecastRow:')
        # print(forecast_df.to_string())

        # the top of mind thing about this method call is the raise__satisfice_failed_exception parameter.
        # This parameter is used to prevent exceptions from stopping the program when testing if a transaction is permitted.
        # The cOF method is only called with this parameter False by the top level of execution.
        # the return value will be forecast_df if successful, and False if not successful and raise__satisfice_failed_exception = False
        # if return value would have been False, but raise__satisfice_failed_exception = True, then an exception will be raised
        # print('before _satisfice')
        _satisfice_df = self._satisficeApproximate(
            all_days,
            confirmed_df,
            account_set,
            memo_rule_set,
            forecast_df,
            raise__satisfice_failed_exception,
            progress_bar,
        )
        # print('after _satisfice')

        _satisfice_success = True
        if _satisfice_df.tail(1).Date.iat[0] != all_days[len(all_days) - 1]:
            _satisfice_success = False

        forecast_df = _satisfice_df

        if _satisfice_success:

            # raise__satisfice_failed_exception is only False at the top level, so this will not print during recursion
            if not raise__satisfice_failed_exception:
                log_in_color(logger, "white", "info", "Satisfice succeeded.")
                log_in_color(logger, "white", "debug", _satisfice_df.to_string())

            # Here, note that confirmed_df, proposed_df, deferred_df, skipped_df are all in the same state as they entered this method
            # but are modified when they come back
            forecast_df, skipped_df, confirmed_df, deferred_df = (
                self._assessPotentialOptimizationsApproximate(
                    forecast_df,
                    account_set,
                    memo_rule_set,
                    confirmed_df,
                    proposed_df,
                    deferred_df,
                    skipped_df,
                    raise__satisfice_failed_exception,
                    progress_bar,
                )
            )
        else:
            if not raise__satisfice_failed_exception:
                log_in_color(logger, "white", "debug", "Satisfice failed.")

            confirmed_df, deferred_df, skipped_df = self._cleanUpAfterFailedSatisfice(
                confirmed_df, proposed_df, deferred_df, skipped_df
            )

        self.log_stack_depth -= 1
        # log_in_color(logger, 'cyan', 'debug', 'EXIT _computeOptimalForecast() C:'+str(confirmed_df.shape[0])+' D:'+str(deferred_df.shape[0])+' S:'+str(skipped_df.shape[0]), self.log_stack_depth)
        return [forecast_df, skipped_df, confirmed_df, deferred_df]

    def _groupTxnsIntoBatchesForApproxForecasts(
        self, budget_schedule_df, start_date_YYYYMMDD, end_date_YYYYMMDD
    ):

        # print('BEFORE')
        # print('budget_schedule_df:')
        # print(budget_schedule_df.to_string())

        no_days = (
            datetime.datetime.strptime(end_date_YYYYMMDD, "%Y%m%d")
            - datetime.datetime.strptime(start_date_YYYYMMDD, "%Y%m%d")
        ).days
        all_days = generate_date_sequence(start_date_YYYYMMDD, no_days, "monthly")
        all_days = all_days[1: len(all_days)]
        if datetime.datetime.strptime(
            all_days[len(all_days) - 1], "%Y%m%d"
        ) > datetime.datetime.strptime(end_date_YYYYMMDD, "%Y%m%d"):
            all_days = all_days[0: (len(all_days) - 1)]

        # print('all_days:')
        # print(all_days)
        # price is right rules
        for index, row in budget_schedule_df.iterrows():

            d_sel_vec = [
                datetime.datetime.strptime(row.Date, "%Y%m%d")
                <= datetime.datetime.strptime(d, "%Y%m%d")
                for d in all_days
            ]
            # print('d_sel_vec: '+str(row.Date)+' '+str(d_sel_vec))
            i = 0
            for i in range(0, len(d_sel_vec)):
                if d_sel_vec[i]:
                    break
            next_batch_date = all_days[i]
            # print(budget_schedule_df.loc[index ,'Date'] + ' -> '+next_batch_date)
            budget_schedule_df.loc[index, "Date"] = next_batch_date

        txn_dict = {}
        for index, row in budget_schedule_df.iterrows():
            key = (
                row.Date,
                row.Priority,
                row.Amount,
                row.Memo,
                row.Deferrable,
                row.Partial_Payment_Allowed,
            )
            if key in txn_dict.keys():
                txn_dict[key] += 1
            else:
                txn_dict[key] = 1

        agg_budget_schedule_df = budget_schedule_df.head(0)
        for key, value in txn_dict.items():

            if value == 1:
                new_row_df = pd.DataFrame(
                    {
                        "Date": [key[0]],
                        "Priority": [key[1]],
                        "Amount": [key[2]],
                        "Memo": [key[3]],
                        "Deferrable": [key[4]],
                        "Partial_Payment_Allowed": [key[5]],
                    }
                )
            else:
                new_row_df = pd.DataFrame(
                    {
                        "Date": [key[0]],
                        "Priority": [key[1]],
                        "Amount": [key[2] * value],
                        "Memo": [key[3] + " x" + str(value)],
                        "Deferrable": [key[4]],
                        "Partial_Payment_Allowed": [key[5]],
                    }
                )

            agg_budget_schedule_df = pd.concat([agg_budget_schedule_df, new_row_df])

        # print('AFTER')
        # print('agg_budget_schedule_df:')
        # print(agg_budget_schedule_df.to_string())

        return agg_budget_schedule_df

    def _adjustBillingDatesForApproxForecasts(
        self, account_set, start_date_YYYYMMDD, end_date_YYYYMMDD
    ):
        no_days = (
            datetime.datetime.strptime(end_date_YYYYMMDD, "%Y%m%d")
            - datetime.datetime.strptime(start_date_YYYYMMDD, "%Y%m%d")
        ).days
        all_days = generate_date_sequence(start_date_YYYYMMDD, no_days, "monthly")
        all_days = all_days[1: len(all_days)]

        for account in account_set.accounts:
            if account.billing_start_date_YYYYMMDD is None:
                continue
            if account.billing_start_date_YYYYMMDD == "None":
                continue
            d_sel_vec = [
                datetime.datetime.strptime(
                    account.billing_start_date_YYYYMMDD, "%Y%m%d"
                )
                <= datetime.datetime.strptime(d, "%Y%m%d")
                for d in all_days
            ]
            # print('d_sel_vec: '+str(row.Date)+' '+str(d_sel_vec))
            for i in range(0, len(d_sel_vec)):
                if d_sel_vec[i]:
                    break
            next_batch_date = all_days[i]
            # print(budget_schedule_df.loc[index ,'Date'] + ' -> '+next_batch_date)
            account.billing_start_date_YYYYMMDD = next_batch_date

        return account_set

    # put all transactions on one day each month, and then only calculate using one day per month
    def runForecastApproximate(self, log_level):
        self.start_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # log_in_color(logger, 'white', 'info', 'Starting Approximate Forecast ' + str(self.unique_id))

        if log_level == "DEBUG":
            loglevel = logging.DEBUG
        elif log_level == "INFO":
            loglevel = logging.INFO
        elif log_level == "WARNING":
            loglevel = logging.WARNING
        elif log_level == "ERROR":
            loglevel = logging.ERROR
        elif log_level == "CRITICAL":
            loglevel = logging.CRITICAL
        else:
            loglevel = logging.WARNING
        logger.setLevel(loglevel)

        sd = datetime.datetime.strptime(self.start_date_YYYYMMDD, "%Y%m%d")
        ed = datetime.datetime.strptime(self.end_date_YYYYMMDD, "%Y%m%d")
        no_days = (
            datetime.datetime.strptime(self.end_date_YYYYMMDD, "%Y%m%d")
            - datetime.datetime.strptime(self.start_date_YYYYMMDD, "%Y%m%d")
        ).days
        all_days = generate_date_sequence(self.start_date_YYYYMMDD, no_days, "monthly")
        predicted__satisfice_runtime_in_simulated_days = len(all_days)

        no_of_p2plus_priority_levels = len(set(self.initial_proposed_df.Priority))
        total_predicted_max_runtime_in_simulated_days = (
            predicted__satisfice_runtime_in_simulated_days
            + predicted__satisfice_runtime_in_simulated_days
            * no_of_p2plus_priority_levels
        )
        progress_bar = tqdm.tqdm(
            range(total_predicted_max_runtime_in_simulated_days),
            total=total_predicted_max_runtime_in_simulated_days,
            desc=self.unique_id,
            disable=True,
        )  # disabled tqdm

        confirmed_df = self._groupTxnsIntoBatchesForApproxForecasts(
            pd.DataFrame(self.initial_confirmed_df, copy=True),
            sd.strftime("%Y%m%d"),
            ed.strftime("%Y%m%d"),
        )
        proposed_df = self._groupTxnsIntoBatchesForApproxForecasts(
            pd.DataFrame(self.initial_proposed_df, copy=True),
            sd.strftime("%Y%m%d"),
            ed.strftime("%Y%m%d"),
        )
        account_set = self._adjustBillingDatesForApproxForecasts(
            self.initial_account_set, sd.strftime("%Y%m%d"), ed.strftime("%Y%m%d")
        )

        forecast_df, skipped_df, confirmed_df, deferred_df = (
            self._computeOptimalForecastApproximate(
                start_date_YYYYMMDD=self.start_date_YYYYMMDD,
                end_date_YYYYMMDD=self.end_date_YYYYMMDD,
                confirmed_df=confirmed_df,
                proposed_df=proposed_df,
                deferred_df=pd.DataFrame(self.initial_deferred_df, copy=True),
                skipped_df=pd.DataFrame(self.initial_skipped_df, copy=True),
                account_set=account_set,
                memo_rule_set=copy.deepcopy(self.initial_memo_rule_set),
                raise__satisfice_failed_exception=False,
                progress_bar=progress_bar,
            )
        )

        self.forecast_df = forecast_df
        self.skipped_df = skipped_df
        self.confirmed_df = confirmed_df
        self.deferred_df = deferred_df

        self.end_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._appendSummaryLines()
        self.evaluateMilestones()

        log_in_color(
            logger,
            "white",
            "info",
            "Finished Approximate Forecast " + str(self.unique_id),
        )

    def _runSingleParallelForecast(self, return_dict):
        self.start_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_in_color(
            logger, "white", "info", "Starting Forecast " + str(self.unique_id)
        )

        sd = datetime.datetime.strptime(self.start_date_YYYYMMDD, "%Y%m%d")
        ed = datetime.datetime.strptime(self.end_date_YYYYMMDD, "%Y%m%d")
        predicted__satisfice_runtime_in_simulated_days = (ed - sd).days

        # On second thought, I would rather deal wit ha stilted progress bar than figuring out how to track progress in recursion
        no_of_p2plus_priority_levels = len(set(self.initial_proposed_df.Priority))
        total_predicted_max_runtime_in_simulated_days = (
            predicted__satisfice_runtime_in_simulated_days
            + predicted__satisfice_runtime_in_simulated_days
            * no_of_p2plus_priority_levels
        )
        # progress_bar = tqdm.tqdm(range(total_predicted_max_runtime_in_simulated_days),total=total_predicted_max_runtime_in_simulated_days, desc=self.unique_id)
        progress_bar = None

        forecast_df, skipped_df, confirmed_df, deferred_df = (
            self._computeOptimalForecast(
                start_date_YYYYMMDD=self.start_date_YYYYMMDD,
                end_date_YYYYMMDD=self.end_date_YYYYMMDD,
                confirmed_df=pd.DataFrame(self.initial_confirmed_df, copy=True),
                proposed_df=pd.DataFrame(self.initial_proposed_df, copy=True),
                deferred_df=pd.DataFrame(self.initial_deferred_df, copy=True),
                skipped_df=pd.DataFrame(self.initial_skipped_df, copy=True),
                account_set=copy.deepcopy(self.initial_account_set),
                memo_rule_set=copy.deepcopy(self.initial_memo_rule_set),
                raise__satisfice_failed_exception=False,
                progress_bar=progress_bar,
            )
        )

        self.forecast_df = forecast_df
        self.skipped_df = skipped_df
        self.confirmed_df = confirmed_df
        self.deferred_df = deferred_df

        self.end_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._appendSummaryLines()
        self.evaluateMilestones()

        log_in_color(
            logger, "white", "info", "Finished Forecast " + str(self.unique_id)
        )
        log_in_color(logger, "white", "info", self.forecast_df.to_string())

        return_dict[self.unique_id] = self

    # @profile
    def runForecast(self, log_level="WARNING", play_notification_sound=False):
        # print('Starting Forecast #'+str(self.unique_id))
        self.start_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if log_level == "DEBUG":
            loglevel = logging.DEBUG
        elif log_level == "INFO":
            loglevel = logging.INFO
        elif log_level == "WARNING":
            loglevel = logging.WARNING
        elif log_level == "ERROR":
            loglevel = logging.ERROR
        elif log_level == "CRITICAL":
            loglevel = logging.CRITICAL
        else:
            loglevel = logging.WARNING
        logger.setLevel(loglevel)

        log_in_color(
            logger, "white", "info", "Starting Forecast " + str(self.unique_id)
        )

        sd = datetime.datetime.strptime(self.start_date_YYYYMMDD, "%Y%m%d")
        ed = datetime.datetime.strptime(self.end_date_YYYYMMDD, "%Y%m%d")
        predicted__satisfice_runtime_in_simulated_days = (ed - sd).days

        # On second thought, I would rather deal wit ha stilted progress bar than figuring out how to track progress in recursion
        no_of_p2plus_priority_levels = len(set(self.initial_proposed_df.Priority))
        total_predicted_max_runtime_in_simulated_days = (
            predicted__satisfice_runtime_in_simulated_days
            + predicted__satisfice_runtime_in_simulated_days
            * no_of_p2plus_priority_levels
        )
        progress_bar = tqdm.tqdm(
            range(total_predicted_max_runtime_in_simulated_days),
            total=total_predicted_max_runtime_in_simulated_days,
            desc=self.unique_id,
            disable=True,
        )  # disabled tqdm

        forecast_df, skipped_df, confirmed_df, deferred_df = (
            self._computeOptimalForecast(
                start_date_YYYYMMDD=self.start_date_YYYYMMDD,
                end_date_YYYYMMDD=self.end_date_YYYYMMDD,
                confirmed_df=pd.DataFrame(self.initial_confirmed_df, copy=True),
                proposed_df=pd.DataFrame(self.initial_proposed_df, copy=True),
                deferred_df=pd.DataFrame(self.initial_deferred_df, copy=True),
                skipped_df=pd.DataFrame(self.initial_skipped_df, copy=True),
                account_set=copy.deepcopy(self.initial_account_set),
                memo_rule_set=copy.deepcopy(self.initial_memo_rule_set),
                raise__satisfice_failed_exception=False,
                progress_bar=progress_bar,
            )
        )

        # Round all values in Memo and Memo Directives
        # (I think I can round other columns as needed w display.precision without changing the data)
        for index, row in forecast_df.iterrows():
            new_memo_lines = []
            for m in row["Memo"].split(";"):
                if m.strip() == "":
                    continue
                try:
                    og_amt = float(re.search(".*\\$(.*)\\)", m).group(1))
                except Exception as e:
                    print("Offending memo: " + str(m))
                    raise e
                new_amount = f"{og_amt:.2f}"
                # log_in_color(logger, 'white', 'debug', '(case 29) _update_memo_amount')
                new_m = self._update_memo_amount(m, new_amount).strip()
                new_memo_lines.append(new_m)

            new_md_lines = []
            for md in row["Memo Directives"].split(";"):
                if md.strip() == "":
                    continue
                try:
                    og_amt = float(re.search(".*\\$(.*)\\)", md).group(1))
                except Exception as e:
                    print("Offending memo directive: " + str(md))
                    raise e
                new_amount = f"{og_amt:.2f}"
                # log_in_color(logger, 'white', 'debug', '(case 30) _update_memo_amount')
                new_md = self._update_memo_amount(md, new_amount).strip()
                new_md_lines.append(new_md)

            forecast_df.loc[index, "Memo"] = "; ".join(new_memo_lines)
            forecast_df.loc[index, "Memo Directives"] = "; ".join(new_md_lines)

        self.forecast_df = forecast_df
        self.skipped_df = skipped_df
        self.confirmed_df = confirmed_df
        self.deferred_df = deferred_df

        self.end_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._appendSummaryLines()
        self.evaluateMilestones()

        # This creates a dependecy on the environment that I don't know how I feel about
        pd.set_option("display.precision", 2)
        log_in_color(
            logger, "white", "info", "Finished Forecast " + str(self.unique_id)
        )
        log_in_color(logger, "white", "info", self.forecast_df.to_string())
        # if play_notification_sound:
        #     notification_sounds.play_notification_sound()

        # self.forecast_df.to_csv('./out//Forecast_' + self.unique_id + '.csv') #this is only the forecast not the whole ExpenseForecast object
        # self.writeToJSONFile() #this is the whole ExpenseForecast object #todo this should accept a path parameter

    # todo this could probably have a better name
    def writeToJSONFile(self, output_dir="./"):

        # self.forecast_df.to_csv('./Forecast__'+run_ts+'.csv')
        log_in_color(
            logger,
            "green",
            "info",
            "Writing to " + str(output_dir) + "/Forecast_" + self.unique_id + ".json",
        )
        print("Writing to " + str(output_dir) + "/Forecast_" + self.unique_id + ".json")
        # self.forecast_df.to_csv('./Forecast__' + run_ts + '.json')

        # self.forecast_df.index = self.forecast_df['Date']
        if hasattr(self, "forecast_df"):
            file_name = "ForecastResult_" + self.unique_id + ".json"
        else:
            file_name = "Forecast_" + self.unique_id + ".json"

        f = open(str(output_dir) + file_name, "w")
        f.write(self.to_json())
        f.close()

        # write all_data.csv  # self.forecast_df.iloc[:,0:(self.forecast_df.shape[1]-1)].to_csv('all_data.csv',index=False)

        # self.forecast_df.to_csv('out.csv', index=False)

    def _getInitialForecastRow(self, start_date_YYYYMMDD, account_set):
        # print('ENTER _getInitialForecastRow')
        min_sched_date = start_date_YYYYMMDD
        account_set_df = account_set.getAccounts()
        # print('account_set_df:')
        # print(account_set_df.to_string())

        date_only_df = pd.DataFrame(["Date", min_sched_date]).T

        accounts_only_df = pd.DataFrame(account_set_df.iloc[:, 0:1]).T
        accounts_only_df.reset_index(inplace=True, drop=True)
        accounts_only_df.columns = accounts_only_df.iloc[0]

        starting_zero_balances_df = pd.DataFrame([0] * account_set_df.shape[0]).T
        starting_zero_balances_df.reset_index(inplace=True, drop=True)
        starting_zero_balances_df.columns = accounts_only_df.iloc[0]

        accounts_only_df = pd.concat([accounts_only_df, starting_zero_balances_df]).T
        accounts_only_df.reset_index(drop=True, inplace=True)
        accounts_only_df.columns = [0, 1]

        next_income_date_only_df = pd.DataFrame(["Next Income Date", ""]).T
        memo_directive_only_df = pd.DataFrame(["Memo Directives", ""]).T
        memo_only_df = pd.DataFrame(["Memo", ""]).T

        initial_forecast_row_df = pd.concat(
            [
                date_only_df,
                accounts_only_df,
                next_income_date_only_df,
                memo_directive_only_df,
                memo_only_df,
            ]
        )

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

    def _addANewDayToTheForecast(self, forecast_df, date_YYYYMMDD):
        # dates_as_datetime_dtype = [datetime.datetime.strptime(d, '%Y%m%d') for d in forecast_df.Date]
        # prev_date_as_datetime_dtype = (datetime.datetime.strptime(date_YYYYMMDD, '%Y%m%d') - datetime.timedelta(days=1))
        # sel_vec = [d == prev_date_as_datetime_dtype for d in dates_as_datetime_dtype]
        # new_row_df = copy.deepcopy(forecast_df.loc[sel_vec])
        new_row_df = copy.deepcopy(forecast_df.tail(1))
        new_row_df.Date = date_YYYYMMDD
        new_row_df["Memo Directives"] = ""
        new_row_df.Memo = ""
        forecast_df = pd.concat([forecast_df, new_row_df])
        forecast_df.reset_index(drop=True, inplace=True)
        return forecast_df

    def _sortTxnsToPreventErrors(self, relevant_confirmed_df, account_set, memo_set):
        # log_in_color(logger, 'white', 'debug', 'ENTER _sortTxnsToPreventErrors', self.log_stack_depth)
        self.log_stack_depth += 1
        # log_in_color(logger, 'white', 'debug', 'input relevant_confirmed_df:', self.log_stack_depth)
        # log_in_color(logger, 'white', 'debug', relevant_confirmed_df.to_string(), self.log_stack_depth)

        # algorithm:
        # sort by priority, for same priority, income, then net loss txns, then debt payment txns

        priority_indices_in_order = list(set(relevant_confirmed_df.Priority))
        priority_indices_in_order.sort()

        sorted_confirmed_df = relevant_confirmed_df.head(0)
        for p in priority_indices_in_order:
            all_txn_of_priority_p = relevant_confirmed_df[
                relevant_confirmed_df.Priority == p
            ]

            p_income = relevant_confirmed_df.head(0)
            p_net_loss = relevant_confirmed_df.head(0)
            p_debt_pay = relevant_confirmed_df.head(0)
            for index, row in all_txn_of_priority_p.iterrows():
                memo_rule = memo_set.findMatchingMemoRule(
                    row.Memo, row.Priority
                ).memo_rules[0]

                # I THINK that these would only be checking and income
                if memo_rule.account_from == "None" and memo_rule.account_to != "None":
                    p_income = pd.concat([p_income, pd.DataFrame(row).T])

                # from should only be checking or credit, so these are always net loss
                elif (
                    memo_rule.account_from != "None" and memo_rule.account_to == "None"
                ):

                    p_net_loss = pd.concat([p_net_loss, pd.DataFrame(row).T])
                else:  # both are not none, and so always debt payments
                    p_debt_pay = pd.concat([p_debt_pay, pd.DataFrame(row).T])

            # log_in_color(logger, 'white', 'debug', 'p_income:', self.log_stack_depth)
            # log_in_color(logger, 'white', 'debug', p_income.to_string(), self.log_stack_depth)
            # log_in_color(logger, 'white', 'debug', 'p_net_loss:', self.log_stack_depth)
            # log_in_color(logger, 'white', 'debug', p_net_loss.to_string(), self.log_stack_depth)
            # log_in_color(logger, 'white', 'debug', 'p_debt_pay:', self.log_stack_depth)
            # log_in_color(logger, 'white', 'debug', p_debt_pay.to_string(), self.log_stack_depth)

            # For stability
            p_income.sort_values(
                by=["Amount", "Memo"], inplace=True, ascending=[False, True]
            )
            p_net_loss.sort_values(
                by=["Amount", "Memo"], inplace=True, ascending=[False, True]
            )
            p_debt_pay.sort_values(
                by=["Amount", "Memo"], inplace=True, ascending=[False, True]
            )

            sorted_confirmed_df = pd.concat(
                [sorted_confirmed_df, p_income, p_net_loss, p_debt_pay]
            )

        # log_in_color(logger, 'white', 'debug', 'sorted_confirmed_df:', self.log_stack_depth)
        # log_in_color(logger, 'white', 'debug', sorted_confirmed_df.to_string(), self.log_stack_depth)
        self.log_stack_depth -= 1
        # log_in_color(logger, 'white', 'debug', 'EXIT _sortTxnsToPreventErrors', self.log_stack_depth)
        return sorted_confirmed_df

    def _checkIfTxnIsIncome(self, confirmed_row):
        m_income = re.search("income", confirmed_row.Memo)
        try:
            m_income.group(0)
            income_flag = True
            # log_in_color(logger,'yellow', 'debug', 'transaction flagged as income: ' + str(m_income.group(0)), 3)
        except Exception as e:
            income_flag = False

        return income_flag

    def _updateBalancesAndMemo(
        self, forecast_df, account_set, confirmed_row, memo_rule_row, date_YYYYMMDD
    ):
        # log_in_color(logger,'white','debug','ENTER _updateBalancesAndMemo',self.log_stack_depth)
        self.log_stack_depth += 1
        # log_in_color(logger, 'white', 'debug', 'memo_rule_row:', self.log_stack_depth)
        # log_in_color(logger, 'white', 'debug', memo_rule_row.to_string(), self.log_stack_depth)

        # Select the row corresponding to the given date
        row_sel_vec = forecast_df["Date"] == date_YYYYMMDD

        # Memo handling when Account_To is not 'ALL_LOANS'
        if memo_rule_row.Account_To != "ALL_LOANS":
            if memo_rule_row.Account_From != "None":
                # Only update the Memo column if Account_To is 'None'
                if memo_rule_row.Account_To == "None":
                    # forecast_df.loc[row_sel_vec, 'Memo'] += f"; {confirmed_row.Memo} ({memo_rule_row.Account_From} -${confirmed_row.Amount:.2f}) "

                    all_basenames = [
                        a.split(":")[0] for a in account_set.getAccounts().Name
                    ]
                    AF_sel_vec = [
                        memo_rule_row.Account_From == bc for bc in all_basenames
                    ]
                    AF_account_rows = account_set.getAccounts()[AF_sel_vec]
                    if AF_account_rows.shape[0] == 1:  # checking
                        # for checking this would be a negative number, but for credit a positive
                        forecast_df.loc[
                            row_sel_vec, "Memo"
                        ] += f"; {confirmed_row.Memo} ({memo_rule_row.Account_From} -${confirmed_row.Amount}) "
                    else:
                        # for checking this would be a negative number, but for credit a positive
                        forecast_df.loc[
                            row_sel_vec, "Memo"
                        ] += f"; {confirmed_row.Memo} ({memo_rule_row.Account_From} +${confirmed_row.Amount}) "
            else:
                # Single account transaction when Account_From is 'None'
                # forecast_df.loc[row_sel_vec, 'Memo'] += f"; {confirmed_row.Memo} ({memo_rule_row.Account_To} +${confirmed_row.Amount:.2f}) "

                # memo always has + bc only single account deposits allowed are to checking
                forecast_df.loc[
                    row_sel_vec, "Memo"
                ] += f"; {confirmed_row.Memo} ({memo_rule_row.Account_To} +${confirmed_row.Amount}) "

        # Iterate over accounts to update balances and directives
        # log_in_color(logger, 'white', 'debug',''.ljust(45) + ' current_balance , new_balance', self.log_stack_depth)
        # print('account_set.getAccounts().shape:')
        # print(account_set.getAccounts().shape)
        for account_index, account_row in account_set.getAccounts().iterrows():
            # if account_index + 1 == account_set.getAccounts().shape[0]:
            #     break
            # for account_index in range(1, (1 + account_set.getAccounts().shape[0])):
            #     account_index = int(account_index)

            col_sel_vec = forecast_df.columns == account_row.Name
            current_balance = forecast_df.loc[row_sel_vec, col_sel_vec].values[0][0]
            relevant_balance = account_row["Balance"]

            # If current balance doesn't match the relevant balance, update the forecast
            # print('current_balance, relevant_balance')
            # print(current_balance, relevant_balance)
            # log_in_color(logger, 'white', 'debug', str(account_row.Name).ljust(45)+': '+str(current_balance).ljust(15)+', '+str(relevant_balance).ljust(11), self.log_stack_depth)
            if current_balance != relevant_balance:
                forecast_df.loc[row_sel_vec, col_sel_vec] = relevant_balance
                # delta = round(current_balance - relevant_balance, 2)
                delta = current_balance - relevant_balance

                # Handle income
                if account_row["Account_Type"] == "checking" and delta < 0:
                    # forecast_df.loc[row_sel_vec, 'Memo Directives'] += f"; INCOME ({memo_rule_row.Account_To} +${-1*delta:.2f}) "
                    forecast_df.loc[
                        row_sel_vec, "Memo Directives"
                    ] += f"; INCOME ({memo_rule_row.Account_To} +${-1 * delta}) "

                # Handle additional loan payments
                if (
                    memo_rule_row.Account_To == "ALL_LOANS"
                    and account_row.Name.split(":")[0] != memo_rule_row.Account_From
                ):

                    if (
                        "Billing Cycle Payment Bal" in account_row.Name
                    ):  # this could be more specific
                        continue
                    # forecast_df.loc[row_sel_vec, 'Memo Directives'] += f"; ADDTL LOAN PAYMENT ({memo_rule_row.Account_From} -${delta:.2f}) "
                    # forecast_df.loc[row_sel_vec, 'Memo Directives'] += f"; ADDTL LOAN PAYMENT ({account_row.Name} -${delta:.2f}) "
                    forecast_df.loc[
                        row_sel_vec, "Memo Directives"
                    ] += f"; ADDTL LOAN PAYMENT ({memo_rule_row.Account_From} -${delta}) "
                    forecast_df.loc[
                        row_sel_vec, "Memo Directives"
                    ] += f"; ADDTL LOAN PAYMENT ({account_row.Name} -${delta}) "

                # Handle additional credit card payments
                if (
                    account_row.Account_Type.lower()
                    in ["credit curr stmt bal", "credit prev stmt bal"]
                    and account_row.Name.split(":")[0] != memo_rule_row.Account_From
                ):
                    # print('Updating MD w/ addtl cc payment')
                    # print(confirmed_row.to_string())

                    if (
                        "Billing Cycle Payment Bal" in account_row.Name
                    ):  # this could be more specific
                        continue
                    # forecast_df.loc[row_sel_vec, 'Memo Directives'] += f"; ADDTL CC PAYMENT ({memo_rule_row.Account_From} -${delta:.2f}) "
                    # forecast_df.loc[row_sel_vec, 'Memo Directives'] += f"; ADDTL CC PAYMENT ({account_row.Name} -${delta:.2f}) "
                    forecast_df.loc[
                        row_sel_vec, "Memo Directives"
                    ] += f"; ADDTL CC PAYMENT ({memo_rule_row.Account_From} -${delta}) "
                    forecast_df.loc[
                        row_sel_vec, "Memo Directives"
                    ] += f"; ADDTL CC PAYMENT ({account_row.Name} -${delta}) "
                # print('Updated Memo Directives: ' + str(forecast_df.loc[row_sel_vec, 'Memo Directives'].iat[0]))

        m_split = [
            " " + m.strip()
            for m in forecast_df.loc[row_sel_vec, "Memo"].iat[0].split(";")
            if m.strip()
        ]
        forecast_df.loc[row_sel_vec, "Memo"] = (";".join(m_split)).strip()

        md_split = [
            md.strip()
            for md in forecast_df.loc[row_sel_vec, "Memo Directives"].iat[0].split(";")
            if md.strip()
        ]
        forecast_df.loc[row_sel_vec, "Memo Directives"] = ("; ".join(md_split)).strip()

        # income (Checking +$100.00); test txn (Checking -$100.00);
        # income (Checking +$100.00); test txn (Checking -$100.00)

        self.log_stack_depth -= 1
        # log_in_color(logger, 'white', 'debug', 'EXIT _updateBalancesAndMemo', self.log_stack_depth)
        return forecast_df

    def _attemptTransactionApproximate(
        self, forecast_df, account_set, memo_set, confirmed_df, proposed_row_df
    ):
        self.log_stack_depth += 1
        try:
            single_proposed_transaction_df = pd.DataFrame(
                copy.deepcopy(proposed_row_df)
            ).T
            not_yet_validated_confirmed_df = copy.deepcopy(
                pd.concat([confirmed_df, single_proposed_transaction_df])
            )
            empty_df = pd.DataFrame(
                {
                    "Date": [],
                    "Priority": [],
                    "Amount": [],
                    "Memo": [],
                    "Deferrable": [],
                    "Partial_Payment_Allowed": [],
                }
            )

            txn_date = proposed_row_df.Date
            d_sel_vec = (
                datetime.datetime.strptime(d, "%Y%m%d")
                <= datetime.datetime.strptime(txn_date, "%Y%m%d")
                for d in forecast_df.Date
            )
            previous_row_df = forecast_df.loc[d_sel_vec, :].tail(2).head(1)

            previous_date = (
                self.start_date_YYYYMMDD
            )  # todo this optimization had to be removed bc of cc prepayment

            hypothetical_future_state_of_forecast_future_rows_only = (
                self._computeOptimalForecastApproximate(
                    start_date_YYYYMMDD=previous_date,
                    end_date_YYYYMMDD=self.end_date_YYYYMMDD,
                    confirmed_df=not_yet_validated_confirmed_df,
                    proposed_df=empty_df,
                    deferred_df=empty_df,
                    skipped_df=empty_df,
                    account_set=copy.deepcopy(
                        self._sync_account_set_w_forecast_day(
                            account_set, forecast_df, previous_date
                        )
                    ),
                    memo_rule_set=memo_set,
                )[0]
            )

            # we started the sub-forecast on the previous date, bc that day is considered final
            # therefore, we can drop it from the concat bc it is not new
            hypothetical_future_state_of_forecast_future_rows_only = (
                hypothetical_future_state_of_forecast_future_rows_only.iloc[1:, :]
            )
            date_array = [
                datetime.datetime.strptime(d, "%Y%m%d") for d in forecast_df.Date
            ]
            row_sel_vec = [
                d < datetime.datetime.strptime(txn_date, "%Y%m%d") for d in date_array
            ]

            past_confirmed_forecast_rows_df = forecast_df[row_sel_vec]

            hypothetical_future_state_of_forecast = pd.concat(
                [
                    past_confirmed_forecast_rows_df,
                    hypothetical_future_state_of_forecast_future_rows_only,
                ]
            )

            self.log_stack_depth -= 1
            return hypothetical_future_state_of_forecast  # transaction is permitted
        except ValueError as e:
            self.log_stack_depth -= (
                5  # several decrements were skipped over by the exception
            )

            log_in_color(logger, "red", "debug", str(e), self.log_stack_depth)

            if (
                re.search(".*Account boundaries were violated.*", str(e.args)) is None
            ):  # this is the only exception where we don't want to stop immediately
                raise e

    # @profile
    def _attemptTransaction(
        self, forecast_df, account_set, memo_set, confirmed_df, proposed_row_df
    ):
        """
        Attempts to execute a proposed transaction and returns the hypothetical future state of the forecast
        if the transaction is permitted.

        Parameters:
        - forecast_df: DataFrame containing the current forecast.
        - account_set: AccountSet object representing the current state of accounts.
        - memo_set: MemoSet object containing memo rules.
        - confirmed_df: DataFrame of confirmed transactions.
        - proposed_row: Series representing the proposed transaction.

        Returns:
        - hypothetical_future_forecast: DataFrame representing the updated forecast if the transaction is permitted.

        Raises:
        - ValueError: If an exception occurs that is not due to account boundary violations.
        """
        log_in_color(
            logger,
            "white",
            "info",
            str(proposed_row_df.Date) + " ENTER _attemptTransaction",
            self.log_stack_depth,
        )
        self.log_stack_depth += 1

        try:
            # Prepare the proposed transaction DataFrame
            single_proposed_transaction_df = proposed_row_df.to_frame().T.copy()

            # Combine the confirmed transactions with the proposed transaction
            updated_confirmed_df = pd.concat(
                [confirmed_df, single_proposed_transaction_df], ignore_index=True
            )

            # log_in_color(logger, 'white', 'info', 'updated_confirmed_df:', self.log_stack_depth)
            # log_in_color(logger, 'white', 'info', updated_confirmed_df.to_string(), self.log_stack_depth)

            # Create an empty DataFrame for proposed, deferred, and skipped transactions
            empty_df = pd.DataFrame(
                columns=[
                    "Date",
                    "Priority",
                    "Amount",
                    "Memo",
                    "Deferrable",
                    "Partial_Payment_Allowed",
                ]
            )

            # Determine the transaction date and previous date
            txn_date = proposed_row_df["Date"]
            txn_datetime = pd.to_datetime(txn_date, format="%Y%m%d")

            # WITH OPTIMIZATION
            previous_date = (txn_datetime - datetime.timedelta(days=1)).strftime(
                "%Y%m%d"
            )

            # # WITHOUT OPTIMIZATION
            # previous_date = self.start_date_YYYYMMDD

            # Synchronize the account set with the forecast on the previous date
            synced_account_set = self._sync_account_set_w_forecast_day(
                account_set, forecast_df, previous_date
            )

            # Compute the hypothetical future forecast starting from the previous date
            hypothetical_future_forecast = self._computeOptimalForecast(
                start_date_YYYYMMDD=previous_date,
                end_date_YYYYMMDD=self.end_date_YYYYMMDD,
                confirmed_df=updated_confirmed_df,
                proposed_df=empty_df,
                deferred_df=empty_df,
                skipped_df=empty_df,
                account_set=synced_account_set,
                memo_rule_set=memo_set,
            )[0]

            # Exclude the first row since it's considered final and not part of the new forecast
            hypothetical_future_forecast = hypothetical_future_forecast.iloc[1:].copy()

            # Extract past forecast rows before the transaction date
            past_forecast = forecast_df[forecast_df["Date"] < txn_date].copy()

            # Combine past forecast with the hypothetical future forecast
            updated_forecast = pd.concat(
                [past_forecast, hypothetical_future_forecast], ignore_index=True
            )

            self.log_stack_depth -= 1
            log_in_color(
                logger,
                "white",
                "info",
                str(proposed_row_df.Date) + " EXIT _attemptTransaction",
                self.log_stack_depth,
            )
            return updated_forecast  # Transaction is permitted

        except ValueError as e:
            # Log the exception
            log_in_color(logger, "red", "debug", str(e), self.log_stack_depth)

            # Reraise the exception if it's not due to account boundary violations
            if "Account boundaries were violated" not in str(e):
                raise e

            self.log_stack_depth -= 1
            log_in_color(
                logger,
                "white",
                "info",
                str(proposed_row_df.Date) + " EXIT _attemptTransaction",
                self.log_stack_depth,
            )

            # Return None to indicate that the transaction is not permitted
            return None

    # @profile
    def _processConfirmedTransactions(
        self, forecast_df, relevant_confirmed_df, memo_set, account_set, date_YYYYMMDD
    ):
        log_in_color(
            logger,
            "white",
            "debug",
            str(date_YYYYMMDD) + " ENTER _processConfirmedTransactions",
            self.log_stack_depth,
        )
        self.log_stack_depth += 1
        # if not relevant_confirmed_df.empty:
        #     log_in_color(logger, 'cyan', 'debug', 'relevant_confirmed_df:', self.log_stack_depth)
        #     log_in_color(logger, 'cyan', 'debug', relevant_confirmed_df.to_string(), self.log_stack_depth)

        for confirmed_index, confirmed_row in relevant_confirmed_df.iterrows():
            # print('    '+str(confirmed_row.Memo)+' '+str(confirmed_row.Amount))
            relevant_memo_rule_set = memo_set.findMatchingMemoRule(
                confirmed_row.Memo, confirmed_row.Priority
            )
            memo_rule_row = relevant_memo_rule_set.getMemoRules().loc[0, :]

            income_flag = self._checkIfTxnIsIncome(confirmed_row)

            try:
                # log_string = str(date_YYYYMMDD) + ' executing txn \''+str(relevant_confirmed_df.Memo.iat[0])
                # log_string += '\' '+str(memo_rule_row.Account_From)+ ' -> '+str(memo_rule_row.Account_To)
                # log_string += ' for $' + str(relevant_confirmed_df.Amount.iat[0])
                # log_in_color(logger, 'white', 'debug', log_string, self.log_stack_depth)
                # log_in_color(logger, 'white', 'debug', str(date_YYYYMMDD) + ' before txn: ', self.log_stack_depth)
                # log_in_color(logger, 'white', 'debug', account_set.getAccounts().to_string(), self.log_stack_depth)
                account_set.executeTransaction(
                    Account_From=memo_rule_row.Account_From,
                    Account_To=memo_rule_row.Account_To,
                    Amount=confirmed_row.Amount,
                    income_flag=income_flag,
                )
                # log_in_color(logger, 'yellow', 'debug', str(date_YYYYMMDD) + ' after txn: ', self.log_stack_depth)
                # log_in_color(logger, 'yellow', 'debug', account_set.getAccounts().to_string(), self.log_stack_depth)
            except Exception as e:
                self.log_stack_depth -= 1
                log_in_color(
                    logger,
                    "white",
                    "debug",
                    str(date_YYYYMMDD) + " EXIT _processConfirmedTransactions",
                    self.log_stack_depth,
                )
                raise e

            forecast_df = self._updateBalancesAndMemo(
                forecast_df, account_set, confirmed_row, memo_rule_row, date_YYYYMMDD
            )

        # log_in_color(logger, 'green', 'debug', forecast_df.to_string(), self.log_stack_depth)
        self.log_stack_depth -= 1
        log_in_color(
            logger,
            "white",
            "debug",
            str(date_YYYYMMDD) + " EXIT _processConfirmedTransactions",
            self.log_stack_depth,
        )
        return forecast_df

    # todo I have seen similar methods so I think that maybe this can be refactored
    def _extract_interest_accrued_amount(self, account_basename, memo_directives):
        interest_amt_found = False
        # print('memo_directives: '+str(memo_directives))
        for md in memo_directives.split(";"):
            # print('md: '+str(md))
            m = re.search("CC INTEREST \\((.*):(.*)\\+\\$(.*)\\)", md)
            try:
                basename_str = m.group(1)

                if account_basename == basename_str.strip():
                    amt_str = m.group(3)
                    # print('amt_str:' + str(amt_str))

                    amt = float(amt_str)
                    interest_amt_found = True
            except Exception as e:
                pass

        if not interest_amt_found:
            raise ValueError(
                "_extract_interest_accrued_amount was not able to extract a value. basename: "
                + str(account_basename)
                + " mds:"
                + str(memo_directives)
            )
        return amt

    # @profile
    def _getTotalPrepaidInCreditCardBillingCycle(
        self, account_name, account_set, forecast_df, date_YYYYMMDD
    ):
        """
        Calculates the total prepaid amount made towards a credit card in the billing cycle up to the given date.

        Parameters:
        - account_name (str): The name of the credit card account.
        - account_set (AccountSet): The account set containing account information.
        - forecast_df (pd.DataFrame): The forecast DataFrame with financial data.
        - date_YYYYMMDD (str): The current date in 'YYYYMMDD' format.

        Returns:
        - float: The total prepaid amount in the current billing cycle.
        """
        log_in_color(
            logger,
            "white",
            "debug",
            str(date_YYYYMMDD) + " ENTER _getTotalPrepaidInCreditCardBillingCycle",
            self.log_stack_depth,
        )
        self.log_stack_depth += 1

        # Extract the base account name (without sub-accounts)
        base_account_name = account_name.split(":")[0]

        # Filter the account row for the given account name and type
        accounts_df = account_set.getAccounts()
        account_row = accounts_df[
            (accounts_df["Name"].str.startswith(base_account_name))
            & (accounts_df["Account_Type"] == "credit prev stmt bal")
        ]

        if account_row.empty:
            self.log_stack_depth -= 1
            raise ValueError(
                f"Account '{account_name}' with type 'credit prev stmt bal' not found in account_set."
            )

        # Get the billing start date
        billing_start_date_str = account_row["Billing_Start_Date"].iloc[0]
        billing_start_date = pd.to_datetime(billing_start_date_str, format="%Y%m%d")

        # Convert the current date to datetime
        current_date = pd.to_datetime(date_YYYYMMDD, format="%Y%m%d")

        # print('billing_start_date_str:' + str(billing_start_date_str))
        # print('billing_start_date:'+str(billing_start_date))
        # print('current_date:' + str(current_date))
        num_days_since_first_billing_date = (current_date - billing_start_date).days
        # print('billing_start_date_str:' + str(billing_start_date_str))
        # print('num_days_since_first_billing_date:'+str(num_days_since_first_billing_date))

        if num_days_since_first_billing_date < 0:
            raise AssertionError  # This method shouldn't have been called if the billing cycle hasn't started yet
        elif num_days_since_first_billing_date > 30:
            billing_dates = generate_date_sequence(
                billing_start_date_str, num_days_since_first_billing_date, "monthly"
            )
        else:  # between 0 and 29
            billing_start_date_str = (
                billing_start_date - datetime.timedelta(days=30)
            ).strftime("%Y%m%d")
            billing_dates = generate_date_sequence(
                billing_start_date_str,
                num_days_since_first_billing_date + 30,
                "monthly",
            )
        # print('billing_dates:'+str(billing_dates))

        lookback_period_start = billing_dates[-2]

        # print('lookback_period_start:'+str(lookback_period_start))

        # Define the time window to search for payments
        lookback_period_end = date_YYYYMMDD

        # Filter forecast_df for the relevant date range
        date_filtered_df = forecast_df[
            (forecast_df["Date"] > lookback_period_start)
            & (forecast_df["Date"] <= lookback_period_end)
        ]

        # print('date_filtered_df:')
        # print(date_filtered_df.to_string())

        # Check for additional credit card payments in the memo directives
        def extract_payment_amount(memo):
            matches = re.findall(
                r"ADDTL CC PAYMENT \((.*?)\$\s*([0-9]*\.[0-9]{1,2})\)", memo
            )
            total = 0.0
            for acc_name, amount_str in matches:
                acc_name = acc_name.replace("-", "").strip()
                if acc_name == account_row["Name"].iloc[0].replace("-", "").strip():
                    try:
                        amount = float(amount_str)
                        total += amount
                    except ValueError:
                        continue
            return total

        # Calculate the total prepaid amount
        total_prepaid_amount = (
            date_filtered_df["Memo Directives"].apply(extract_payment_amount).sum()
        )

        self.log_stack_depth -= 1
        log_in_color(
            logger,
            "white",
            "debug",
            str(date_YYYYMMDD) + " EXIT _getTotalPrepaidInCreditCardBillingCycle",
            self.log_stack_depth,
        )
        return total_prepaid_amount

    # @profile
    def _getFutureMinPaymentAmount(
        self, account_name, account_set, forecast_df, date_YYYYMMDD
    ):
        """
        Calculates the future minimum payment amount for a given credit card account starting from a specific date.

        Parameters:
        - account_name (str): The name of the credit card account.
        - account_set (AccountSet): The account set containing account information.
        - forecast_df (pd.DataFrame): The forecast DataFrame containing financial data.
        - date_YYYYMMDD (str): The date from which to start the calculation, in 'YYYYMMDD' format.

        Returns:
        - float: The minimum payment amount due in the future, or 0.0 if no payment is due.
        """
        log_in_color(
            logger,
            "white",
            "debug",
            str(date_YYYYMMDD) + " ENTER _getFutureMinPaymentAmount",
            self.log_stack_depth,
        )
        self.log_stack_depth += 1

        # Extract the base account name (before any colons)
        base_account_name = account_name.split(":")[0]

        # Get the account row for the specified account name and account type 'credit prev stmt bal'
        accounts_df = account_set.getAccounts()
        account_row = accounts_df[
            (accounts_df["Name"].str.startswith(base_account_name))
            & (accounts_df["Account_Type"] == "credit prev stmt bal")
        ]

        if account_row.empty:
            raise ValueError(
                f"Account '{account_name}' with type 'credit prev stmt bal' not found in account_set."
            )

        # Get the forecast row for the specified date
        current_forecast_row_df = forecast_df[forecast_df["Date"] == date_YYYYMMDD]

        if current_forecast_row_df.empty:
            raise ValueError(f"Date '{date_YYYYMMDD}' not found in forecast DataFrame.")

        # Check if there is a minimum payment on the current date
        memo_directives = current_forecast_row_df["Memo Directives"].iat[0]
        min_payment_amount = self._extract_min_payment_amount(
            memo_directives, base_account_name
        )

        if min_payment_amount > 0:
            self.log_stack_depth -= 1
            log_in_color(
                logger,
                "white",
                "debug",
                str(date_YYYYMMDD) + " EXIT _getFutureMinPaymentAmount",
                self.log_stack_depth,
            )
            return min_payment_amount

        # If no minimum payment on the current date, find the next billing date

        # todo this is wrong
        next_billing_date_str = generate_date_sequence(
            date_YYYYMMDD, 32, cadence="monthly"
        )[-1]
        next_billing_date = datetime.datetime.strptime(next_billing_date_str, "%Y%m%d")

        current_date = datetime.datetime.strptime(date_YYYYMMDD, "%Y%m%d")

        right_check_bound = current_date + datetime.timedelta(days=35)
        forecast_dates = forecast_df["Date"].apply(
            lambda d: datetime.datetime.strptime(d, "%Y%m%d")
        )
        check_region = forecast_df[
            (forecast_dates < right_check_bound) & (forecast_dates >= current_date)
        ]

        future_min_payment_date_sel_vec = check_region["Memo Directives"].str.contains(
            "CC MIN PAYMENT"
        )

        if sum(future_min_payment_date_sel_vec) == 0:
            self.log_stack_depth -= 1
            log_in_color(
                logger,
                "white",
                "debug",
                str(date_YYYYMMDD) + " future min_payment_amount = 0",
                self.log_stack_depth,
            )
            log_in_color(
                logger,
                "white",
                "debug",
                str(date_YYYYMMDD) + " EXIT _getFutureMinPaymentAmount",
                self.log_stack_depth,
            )
            return 0.0

        # Extract minimum payment amount from the memo directives on the next billing date
        memo_directives = check_region.loc[future_min_payment_date_sel_vec][
            "Memo Directives"
        ].iat[0]
        min_payment_amount = self._extract_min_payment_amount(
            memo_directives, base_account_name
        )

        log_in_color(
            logger,
            "white",
            "debug",
            "next_billing_date_str:" + str(next_billing_date_str),
            self.log_stack_depth,
        )
        log_in_color(
            logger,
            "white",
            "debug",
            "next bd memo_directives:" + str(memo_directives),
            self.log_stack_depth,
        )
        log_in_color(
            logger,
            "white",
            "debug",
            "next bd min_payment_amount:" + str(min_payment_amount),
            self.log_stack_depth,
        )

        self.log_stack_depth -= 1
        log_in_color(
            logger,
            "white",
            "debug",
            str(date_YYYYMMDD) + " EXIT _getFutureMinPaymentAmount",
            self.log_stack_depth,
        )
        return min_payment_amount

    # @profile
    def _extract_min_payment_amount(self, memo_directives, base_account_name):
        """
        Helper function to extract the minimum payment amount from memo directives.

        Parameters:
        - memo_directives (str): The memo directives string.
        - base_account_name (str): The base account name.

        Returns:
        - float: The total minimum payment amount found in the memo directives.
        """
        log_in_color(
            logger,
            "white",
            "debug",
            "ENTER _extract_min_payment_amount",
            self.log_stack_depth,
        )
        self.log_stack_depth += 1

        min_payment_amount = 0.0
        memo_items = memo_directives.split(";")
        for memo in memo_items:
            memo = memo.strip()
            if not memo:
                continue
            # Check for minimum payment directives for both previous and current statement balances
            if (
                f"CC MIN PAYMENT ({base_account_name}: Prev Stmt Bal" in memo
                or f"CC MIN PAYMENT ({base_account_name}: Curr Stmt Bal" in memo
            ):

                match = re.search("(.*) \\((.*)[-+]{1}\\$(.*)\\)", memo)
                # match = re.search(r'\(.*-\$(\d+(\.\d{1,2})?)\)', memo)
                if match:
                    amount = float(match.group(3))
                    min_payment_amount += amount
        self.log_stack_depth -= 1
        log_in_color(
            logger,
            "white",
            "debug",
            "EXIT _extract_min_payment_amount",
            self.log_stack_depth,
        )
        return min_payment_amount

    # @profile
    def _processProposedTransactions(
        self,
        account_set,
        forecast_df,
        date_YYYYMMDD,
        memo_set,
        confirmed_df,
        relevant_proposed_df,
        priority_level,
    ):
        """
        Processes proposed transactions by attempting to execute them, handling partial payments, deferrals,
        and updating the forecast accordingly.

        Parameters:
        - account_set: AccountSet object representing the current state of accounts.
        - forecast_df: DataFrame containing the forecasted financial data.
        - date_YYYYMMDD: String representing the current date in 'YYYYMMDD' format.
        - memo_set: MemoSet object containing memo rules.
        - confirmed_df: DataFrame of confirmed transactions.
        - relevant_proposed_df: DataFrame of proposed transactions for the current date.
        - priority_level: Integer representing the priority level.

        Returns:
        - forecast_df: Updated forecast DataFrame.
        - new_confirmed_df: DataFrame of newly confirmed transactions.
        - new_deferred_df: DataFrame of newly deferred transactions.
        - new_skipped_df: DataFrame of newly skipped transactions.
        """
        log_in_color(
            logger,
            "white",
            "debug",
            str(date_YYYYMMDD)
            + " ENTER _processProposedTransactions p == "
            + str(priority_level),
            self.log_stack_depth,
        )
        # Increment the log stack depth
        self.log_stack_depth += 1

        # log_in_color(logger, 'white', 'debug', 'relevant_proposed_df:', self.log_stack_depth)
        # log_in_color(logger, 'white', 'debug',relevant_proposed_df.to_string(), self.log_stack_depth)

        # Initialize DataFrames to hold new deferred, skipped, and confirmed transactions
        new_deferred_df = relevant_proposed_df.iloc[
            0:0
        ].copy()  # Empty DataFrame with the same schema
        new_skipped_df = relevant_proposed_df.iloc[0:0].copy()
        new_confirmed_df = relevant_proposed_df.iloc[0:0].copy()

        # If there are no proposed transactions, return early
        if relevant_proposed_df.empty:
            self.log_stack_depth -= 1
            log_in_color(
                logger,
                "white",
                "debug",
                str(date_YYYYMMDD)
                + " EXIT _processProposedTransactions p == "
                + str(priority_level),
                self.log_stack_depth,
            )
            return forecast_df, new_confirmed_df, new_deferred_df, new_skipped_df

        # log_in_color(logger, 'white', 'debug', 'relevant_proposed_df:', self.log_stack_depth)
        # log_in_color(logger, 'white', 'debug', relevant_proposed_df.to_string(), self.log_stack_depth)

        # Iterate over each proposed transaction
        for proposed_index, proposed_row in relevant_proposed_df.iterrows():
            log_in_color(
                logger,
                "cyan",
                "info",
                str(date_YYYYMMDD)
                + " Considering: "
                + str(proposed_row.Memo)
                + " "
                + str(proposed_row.Amount),
                self.log_stack_depth,
            )

            # log_in_color(logger, 'cyan', 'info','Current State:', self.log_stack_depth)
            # log_in_color(logger, 'cyan', 'info', forecast_df.to_string(), self.log_stack_depth)
            # log_in_color(logger, 'cyan', 'info', account_set.getAccounts().to_string(), self.log_stack_depth)
            # log_in_color(logger, 'cyan', 'info', confirmed_df.to_string(), self.log_stack_depth)

            # Find the matching memo rule for the proposed transaction
            memo_rule_set = memo_set.findMatchingMemoRule(
                proposed_row["Memo"], proposed_row["Priority"]
            )
            memo_rule_row = memo_rule_set.getMemoRules().iloc[0]

            # multiple txns same day same priority p!=1 have not been propagated even if approved
            # editing confirmed_df causes downstream problems, so we have a working copy for the scope of this method
            # local_scope_og_confirmed_df = confirmed_df
            local_scope_confirmed_df = pd.concat([new_confirmed_df, confirmed_df])
            result = self._attemptTransaction(
                forecast_df=forecast_df,
                account_set=copy.deepcopy(account_set),
                memo_set=memo_set,
                confirmed_df=local_scope_confirmed_df,
                proposed_row_df=proposed_row,
            )

            # Check if the transaction is permitted (returns a DataFrame if successful)
            transaction_permitted = isinstance(result, pd.DataFrame)

            if transaction_permitted:
                log_in_color(
                    logger,
                    "green",
                    "info",
                    str(date_YYYYMMDD)
                    + " _attemptTransaction SUCCESS "
                    + str(proposed_row.Memo)
                    + " "
                    + str(proposed_row.Amount),
                    self.log_stack_depth,
                )
                log_in_color(logger, "green", "info", "Result: ", self.log_stack_depth)
                log_in_color(
                    logger, "green", "info", result.to_string(), self.log_stack_depth
                )

                # Transaction is permitted; update the hypothetical future forecast and account set
                hypothetical_forecast = result
                account_set = self._sync_account_set_w_forecast_day(
                    account_set, forecast_df, date_YYYYMMDD
                )
            else:
                log_in_color(
                    logger,
                    "red",
                    "info",
                    str(date_YYYYMMDD)
                    + " _attemptTransaction FAIL "
                    + str(proposed_row.Memo)
                    + " "
                    + str(proposed_row.Amount),
                    self.log_stack_depth,
                )
                hypothetical_forecast = None

            # Handle partial payments if transaction is not permitted and partial payments are allowed
            if not transaction_permitted and proposed_row["Partial_Payment_Allowed"]:

                # Get the minimum future available balances
                min_future_balances = self._getMinimumFutureAvailableBalances(
                    account_set, forecast_df, date_YYYYMMDD
                )
                max_available_funds = min_future_balances.get(
                    memo_rule_row["Account_From"], 0.0
                )

                # Determine the maximum amount that can be transferred to the destination account
                reduced_amount = self._calculate_reduced_amount(
                    account_set=account_set,
                    memo_rule_row=memo_rule_row,
                    max_available_funds=max_available_funds,
                    forecast_df=forecast_df,
                    date_YYYYMMDD=date_YYYYMMDD,
                )

                log_in_color(
                    logger,
                    "cyan",
                    "info",
                    str(date_YYYYMMDD)
                    + " re-attempt at reduced amount: "
                    + str(reduced_amount),
                    self.log_stack_depth,
                )

                # Attempt the transaction with the reduced amount if it's greater than zero
                if reduced_amount > 0:
                    proposed_row["Amount"] = reduced_amount

                    # local_scope_confirmed_df = pd.concat([new_confirmed_df, local_scope_og_confirmed_df])
                    result = self._attemptTransaction(
                        forecast_df=forecast_df,
                        account_set=copy.deepcopy(account_set),
                        memo_set=memo_set,
                        confirmed_df=local_scope_confirmed_df,
                        proposed_row_df=proposed_row,
                    )

                    transaction_permitted = isinstance(result, pd.DataFrame)

                    if transaction_permitted:
                        hypothetical_forecast = result
                        account_set = self._sync_account_set_w_forecast_day(
                            account_set, forecast_df, date_YYYYMMDD
                        )
                    else:
                        hypothetical_forecast = None

            # Handle deferrable transactions if not permitted
            if not transaction_permitted and proposed_row["Deferrable"]:
                # Find the next income date
                # next_income_date = self._find_next_income_date(forecast_df, date_YYYYMMDD)

                # Update the date of the proposed transaction to the next income date
                next_income_date = forecast_df[forecast_df.Date == date_YYYYMMDD][
                    "Next Income Date"
                ].iat[0]
                proposed_row["Date"] = next_income_date

                if next_income_date == "":
                    new_skipped_df = pd.concat(
                        [new_skipped_df, proposed_row.to_frame().T], ignore_index=True
                    )
                else:
                    # Add the transaction to the deferred DataFrame
                    new_deferred_df = pd.concat(
                        [new_deferred_df, proposed_row.to_frame().T], ignore_index=True
                    )

            elif not transaction_permitted and not proposed_row["Deferrable"]:
                # Add the transaction to the skipped DataFrame
                new_skipped_df = pd.concat(
                    [new_skipped_df, proposed_row.to_frame().T], ignore_index=True
                )

            elif transaction_permitted:
                # Transaction is permitted; execute it and update the forecast and account set
                if priority_level > 1:
                    account_set = self._sync_account_set_w_forecast_day(
                        account_set, forecast_df, date_YYYYMMDD
                    )

                account_set.executeTransaction(
                    Account_From=memo_rule_row["Account_From"],
                    Account_To=memo_rule_row["Account_To"],
                    Amount=proposed_row["Amount"],
                    income_flag=False,
                )

                # Add the transaction to the confirmed DataFrame
                new_confirmed_df = pd.concat(
                    [new_confirmed_df, proposed_row.to_frame().T], ignore_index=True
                )

                # Update the forecast DataFrame with the hypothetical future forecast
                forecast_df = self._update_forecast_with_hypothetical(
                    forecast_df=forecast_df,
                    hypothetical_forecast=hypothetical_forecast,
                    date_YYYYMMDD=date_YYYYMMDD,
                )

                # Update the account balances in the forecast DataFrame for the current date
                # this seems redundant here, but chat gpt did this and i dont suspect it for now
                # good method actually, would like to use it in a refactor #todo
                self._update_forecast_balances(
                    forecast_df=forecast_df,
                    account_set=account_set,
                    date_YYYYMMDD=date_YYYYMMDD,
                )

                # log_in_color(logger, 'green', 'info', 'Forecast Post-Update: ', self.log_stack_depth)
                # log_in_color(logger, 'green', 'info', forecast_df.to_string(), self.log_stack_depth)
                # log_in_color(logger, 'green', 'info', 'New Confirmed Txns: ', self.log_stack_depth)
                # log_in_color(logger, 'green', 'info', confirmed_df.to_string(), self.log_stack_depth)
            else:
                # This case should not occur; raise an error
                raise ValueError(
                    "Unexpected case in process_proposed_transactions:\n"
                    f"transaction_permitted: {transaction_permitted}\n"
                    f"Deferrable: {proposed_row['Deferrable']}\n"
                    f"Partial_Payment_Allowed: {proposed_row['Partial_Payment_Allowed']}\n"
                )

        # Decrement the log stack depth
        self.log_stack_depth -= 1
        log_in_color(
            logger,
            "white",
            "debug",
            str(date_YYYYMMDD)
            + " EXIT _processProposedTransactions p == "
            + str(priority_level),
            self.log_stack_depth,
        )
        return forecast_df, new_confirmed_df, new_deferred_df, new_skipped_df

    def _minimum_future_available_balances_as_if_a_cc_payment_did_not_happen(
        self, account_set, memo_rule_row, forecast_df, date_YYYYMMDD
    ):
        log_in_color(
            logger,
            "white",
            "debug",
            str(date_YYYYMMDD)
            + " ENTER _minimum_future_available_balances_as_if_a_cc_payment_did_not_happen ",
            self.log_stack_depth,
        )
        self.log_stack_depth += 1
        # the reason this method exists is that making an advance minimum payment changes the minimum future available balances
        # in order to make the largest payment possible without going over,

        relevant_subset_df = forecast_df[forecast_df.Date >= date_YYYYMMDD]

        left_check_bound = datetime.datetime.strptime(
            date_YYYYMMDD, "%Y%m%d"
        ) + datetime.timedelta(days=1)
        right_check_bound = datetime.datetime.strptime(
            date_YYYYMMDD, "%Y%m%d"
        ) + datetime.timedelta(days=35)
        forecast_dates = forecast_df["Date"].apply(
            lambda d: datetime.datetime.strptime(d, "%Y%m%d")
        )
        check_region = forecast_df[
            (left_check_bound <= forecast_dates) & (forecast_dates <= right_check_bound)
        ]

        print("check_region:")
        print(check_region.to_string())

        credit_basename = str(memo_rule_row.Account_To.split(":")[0])

        # we have to add the curr and prev for the acct in case multiple credit cards were paid the same day
        # CC MIN PAYMENT (Credit: Prev Stmt Bal -$487.99)
        prev_search_substring = (
            "CC MIN PAYMENT \\(" + credit_basename + ": Prev Stmt Bal -\\$(.*)\\)"
        )
        curr_search_substring = (
            "CC MIN PAYMENT \\(" + credit_basename + ": Curr Stmt Bal -\\$(.*)\\)"
        )

        min_cc_payment_found = False
        prev_amt_float = None
        curr_amt_float = None
        next_min_payment_amount = 0
        next_min_payment_date = None
        for index, row in check_region.iterrows():
            for md in row["Memo Directives"].split(";"):
                try:
                    prev_m = re.search(prev_search_substring, md)
                    prev_amt = prev_m.group(1)
                    prev_amt_float = float(prev_amt)
                    next_min_payment_amount += prev_amt_float
                    min_cc_payment_found = True
                    next_min_payment_date = row["Date"]
                except Exception as e:
                    print(e)

                try:
                    curr_m = re.search(curr_search_substring, md)
                    curr_amt = curr_m.group(1)
                    curr_amt_float = float(curr_amt)
                    next_min_payment_amount += curr_amt_float
                    min_cc_payment_found = True
                    next_min_payment_date = row["Date"]
                except Exception as e:
                    print(e)

            if min_cc_payment_found:
                break

        # print('next_min_payment_date:'+str(next_min_payment_date))
        if next_min_payment_date is not None:
            pre_next_payment_df = relevant_subset_df[
                relevant_subset_df.Date < next_min_payment_date
            ]
            post_next_payment_inclusive_df = relevant_subset_df[
                relevant_subset_df.Date >= next_min_payment_date
            ]
            post_next_payment_inclusive_df[
                memo_rule_row.Account_From
            ] += next_min_payment_amount

            log_in_color(
                logger, "white", "debug", "pre_next_payment_df:", self.log_stack_depth
            )
            log_in_color(
                logger,
                "white",
                "debug",
                pre_next_payment_df.to_string(),
                self.log_stack_depth,
            )
            log_in_color(
                logger,
                "white",
                "debug",
                "post_next_payment_inclusive_df:",
                self.log_stack_depth,
            )
            log_in_color(
                logger,
                "white",
                "debug",
                post_next_payment_inclusive_df.to_string(),
                self.log_stack_depth,
            )

            amount_in_question = min(
                min(pre_next_payment_df[memo_rule_row.Account_From]),
                min(post_next_payment_inclusive_df[memo_rule_row.Account_From]),
            )
        else:
            # so lazy lol. This should be refactored #todo
            amount_in_question = self._getMinimumFutureAvailableBalances(
                account_set, forecast_df, date_YYYYMMDD
            )[memo_rule_row.Account_From]

        self.log_stack_depth -= 1
        log_in_color(
            logger,
            "white",
            "debug",
            str(date_YYYYMMDD)
            + " EXIT _minimum_future_available_balances_as_if_a_cc_payment_did_not_happen ",
            self.log_stack_depth,
        )
        return amount_in_question

    # @profile
    def _calculate_reduced_amount(
        self,
        account_set,
        memo_rule_row,
        max_available_funds,
        forecast_df,
        date_YYYYMMDD,
    ):
        """
        Calculates the maximum amount that can be transferred based on available funds and account types.

        Parameters:
        - account_set: AccountSet object representing the current state of accounts.
        - memo_rule_row: Series representing the memo rule for the transaction.
        - max_available_funds: Float representing the maximum available funds from the source account.
        - forecast_df: DataFrame containing the forecasted financial data.
        - date_YYYYMMDD: String representing the current date in 'YYYYMMDD' format.

        Returns:
        - reduced_amount: Float representing the reduced transaction amount.
        """
        log_in_color(
            logger,
            "white",
            "debug",
            str(date_YYYYMMDD) + " ENTER _calculate_reduced_amount",
            self.log_stack_depth,
        )
        self.log_stack_depth += 1

        # Get the account types for the destination account
        account_base_names = account_set.getAccounts()["Name"].apply(
            lambda x: x.split(":")[0]
        )

        not_eopc_or_bcpb_sel_vec = [
            (
                ("Billing Cycle Payment Bal" not in aname)
                and ("End of Prev Cycle Bal" not in aname)
            )
            for aname in account_set.getAccounts()["Name"]
        ]

        from_basename_sel_vec = account_base_names == memo_rule_row["Account_From"]
        to_basename_sel_vec = account_base_names == memo_rule_row["Account_To"]

        from_basename_sel_vec = [
            a & b for a, b in zip(from_basename_sel_vec, not_eopc_or_bcpb_sel_vec)
        ]
        to_basename_sel_vec = [
            a & b for a, b in zip(to_basename_sel_vec, not_eopc_or_bcpb_sel_vec)
        ]

        source_accounts = account_set.getAccounts()[from_basename_sel_vec]
        destination_accounts = account_set.getAccounts()[to_basename_sel_vec]

        # log_in_color(logger, 'white', 'debug', 'source_accounts:', self.log_stack_depth)
        # log_in_color(logger, 'white', 'debug', source_accounts.to_string(), self.log_stack_depth)
        # log_in_color(logger, 'white', 'debug', 'destination_accounts:', self.log_stack_depth)
        # log_in_color(logger, 'white', 'debug', destination_accounts.to_string(), self.log_stack_depth)

        source_account_types = source_accounts["Account_Type"].tolist()
        dest_account_types = destination_accounts["Account_Type"].tolist()

        if (
            "credit curr stmt bal" in source_account_types
            and "credit prev stmt bal" in source_account_types
        ):
            source_account_type = "credit"
        elif (
            "principal balance" in source_account_types
            and "interest" in source_account_types
        ):
            source_account_type = "loan"
        elif len(source_account_types) == 1 and source_account_types[0] == "checking":
            source_account_type = "checking"
        else:
            source_account_type = "none"

        if (
            "credit curr stmt bal" in dest_account_types
            and "credit prev stmt bal" in dest_account_types
        ):
            dest_account_type = "credit"
        elif (
            "principal balance" in dest_account_types
            and "interest" in dest_account_types
        ):
            dest_account_type = "loan"
        elif len(dest_account_types) == 1 and dest_account_types[0] == "checking":
            dest_account_type = "checking"
        else:
            dest_account_type = "none"

        if dest_account_type in ["loan", "credit"]:

            future_min_payment = self._getFutureMinPaymentAmount(
                account_name=memo_rule_row["Account_To"],
                account_set=account_set,
                forecast_df=forecast_df,
                date_YYYYMMDD=date_YYYYMMDD,
            )
        else:
            future_min_payment = 0

        if source_account_type == "credit":
            raise NotImplementedError
            # reduced_amount = min(max_available_funds, total_balance)
        elif source_account_type == "checking":
            # source_bound = max_available_funds # + future_min_payment #min(max_available_funds, total_balance)

            # this would assume that the future min was because of THIS card, which is not always true
            # s owe should look ahead, and pretend like the next payment never happened?
            # therefore, we have to compute max_available_funds in a custom way... refactor this later lol
            source_bound = self._minimum_future_available_balances_as_if_a_cc_payment_did_not_happen(
                account_set, memo_rule_row, forecast_df, date_YYYYMMDD
            )

            # min future + future_min_payment
        elif source_account_type == "loan":
            raise NotImplementedError
        else:
            raise ValueError("Invalid account type in _calculate_reduced_amount")

        # log_in_color(logger, 'magenta', 'debug', 'destination_accounts: ' , self.log_stack_depth)
        # log_in_color(logger, 'magenta', 'debug', str(destination_accounts.to_string()), self.log_stack_depth)

        if dest_account_type == "credit":
            dest_bound = destination_accounts["Balance"].sum()
        elif dest_account_type == "checking":
            raise NotImplementedError
        elif dest_account_type == "loan":
            raise NotImplementedError
        elif dest_account_type == "none":
            dest_bound = float("inf")
        else:
            raise ValueError(
                "Invalid account type in _calculate_reduced_amount: "
                + str(dest_account_type)
            )

        # log_in_color(logger, 'magenta', 'debug', 'forecast_df: ' + str(forecast_df.to_string()), self.log_stack_depth)

        reduced_amount = min(source_bound, dest_bound)
        log_in_color(
            logger,
            "white",
            "debug",
            "source_bound..: " + str(source_bound),
            self.log_stack_depth,
        )
        log_in_color(
            logger,
            "white",
            "debug",
            "dest_bound....: " + str(dest_bound),
            self.log_stack_depth,
        )
        log_in_color(
            logger,
            "white",
            "debug",
            "reduced_amount: " + str(reduced_amount),
            self.log_stack_depth,
        )

        self.log_stack_depth -= 1
        log_in_color(
            logger,
            "white",
            "debug",
            str(date_YYYYMMDD) + " EXIT _calculate_reduced_amount",
            self.log_stack_depth,
        )
        return reduced_amount

    # @profile
    def _find_next_income_date(self, forecast_df, date_YYYYMMDD):
        """
        Finds the next income date after the given date.

        Parameters:
        - forecast_df: DataFrame containing the forecasted financial data.
        - date_YYYYMMDD: String representing the current date in 'YYYYMMDD' format.

        Returns:
        - next_income_date: String representing the next income date in 'YYYYMMDD' format.
        """
        current_date = pd.to_datetime(date_YYYYMMDD, format="%Y%m%d")

        # Filter future dates
        future_dates = forecast_df[forecast_df["Date"] > date_YYYYMMDD]

        # Filter rows where the memo indicates income
        income_rows = future_dates[
            future_dates["Memo"].str.contains("income", case=False, na=False)
        ]

        if not income_rows.empty:
            next_income_date = income_rows["Date"].iloc[0]
        else:
            # If no future income dates, set to one day after the forecast end date
            end_date = pd.to_datetime(self.end_date_YYYYMMDD, format="%Y%m%d")
            next_income_date = (end_date + pd.Timedelta(days=1)).strftime("%Y%m%d")

        return next_income_date

    # @profile
    def _update_forecast_with_hypothetical(
        self, forecast_df, hypothetical_forecast, date_YYYYMMDD
    ):
        """
        Updates the forecast DataFrame with the hypothetical future forecast starting from the given date.

        Parameters:
        - forecast_df: DataFrame containing the current forecast data.
        - hypothetical_forecast: DataFrame containing the hypothetical future forecast.
        - date_YYYYMMDD: String representing the current date in 'YYYYMMDD' format.

        Returns:
        - Updated forecast_df.
        """
        # Split the forecast into past and future
        past_forecast = forecast_df[forecast_df["Date"] < date_YYYYMMDD]
        future_forecast = hypothetical_forecast[
            hypothetical_forecast["Date"] >= date_YYYYMMDD
        ]

        # Concatenate the past and updated future forecasts
        updated_forecast = pd.concat(
            [past_forecast, future_forecast], ignore_index=True
        )

        # Ensure no duplicate dates
        updated_forecast = updated_forecast.drop_duplicates(subset=["Date"])

        return updated_forecast

    # @profile
    def _update_forecast_balances(self, forecast_df, account_set, date_YYYYMMDD):
        """
        Updates the account balances in the forecast DataFrame for the current date based on the account set.

        Parameters:
        - forecast_df: DataFrame containing the forecasted financial data.
        - account_set: AccountSet object representing the current state of accounts.
        - date_YYYYMMDD: String representing the current date in 'YYYYMMDD' format.
        """
        # Update each account balance in the forecast
        for index, account_row in account_set.getAccounts().iterrows():
            account_name = account_row["Name"]
            balance = account_row["Balance"]

            if account_name in forecast_df.columns:
                forecast_df.loc[forecast_df["Date"] == date_YYYYMMDD, account_name] = (
                    balance
                )

    def _processProposedTransactionsApproximate(
        self,
        account_set,
        forecast_df,
        date_YYYYMMDD,
        memo_set,
        confirmed_df,
        relevant_proposed_df,
        priority_level,
    ):
        self.log_stack_depth += 1

        new_deferred_df = relevant_proposed_df.head(0)  # to preserve schema
        new_skipped_df = relevant_proposed_df.head(0)
        new_confirmed_df = relevant_proposed_df.head(0)

        if relevant_proposed_df.shape[0] == 0:
            self.log_stack_depth -= 1
            return forecast_df, new_confirmed_df, new_deferred_df, new_skipped_df

        for proposed_item_index, proposed_row_df in relevant_proposed_df.iterrows():
            # print('proposed txn:'+str(proposed_row_df.Date+' '+str(proposed_row_df.Amount)))
            relevant_memo_rule_set = memo_set.findMatchingMemoRule(
                proposed_row_df.Memo, proposed_row_df.Priority
            )
            memo_rule_row = relevant_memo_rule_set.getMemoRules().loc[0, :]

            result_of_attempt = self._attemptTransactionApproximate(
                forecast_df,
                copy.deepcopy(account_set),
                memo_set,
                confirmed_df,
                proposed_row_df,
            )
            transaction_is_permitted = isinstance(result_of_attempt, pd.DataFrame)

            if transaction_is_permitted:
                hypothetical_future_state_of_forecast = result_of_attempt
                account_set = self._sync_account_set_w_forecast_day(
                    account_set, forecast_df, date_YYYYMMDD
                )
            else:
                hypothetical_future_state_of_forecast = None

            if not transaction_is_permitted and proposed_row_df.Partial_Payment_Allowed:
                min_fut_avl_bals = self._getMinimumFutureAvailableBalances(
                    account_set, forecast_df, date_YYYYMMDD
                )
                af_max = min_fut_avl_bals[memo_rule_row.Account_From]

                account_basenames = [
                    cname.split(":")[0] for cname in account_set.getAccounts().Name
                ]
                at_col_sel_vec = [
                    a == memo_rule_row.Account_To for a in account_basenames
                ]
                at_type_list = list(
                    account_set.getAccounts().loc[at_col_sel_vec, :].Account_Type
                )

                at_type = "none"
                if len(at_type_list) == 2:
                    if (
                        "credit curr stmt bal" in at_type_list
                        and "credit prev stmt bal" in at_type_list
                    ):
                        at_type = "credit"
                    elif (
                        "principal balance" in at_type_list
                        and "interest" in at_type_list
                    ):
                        at_type = "loan"
                elif len(at_type_list) == 1:
                    if "checking" == at_type_list[0]:
                        at_type = "checking"

                # additional credit card payments
                if at_type == "credit":
                    account_base_names = [
                        a.split(":")[0] for a in account_set.getAccounts().Name
                    ]
                    row_sel_vec = [
                        a == memo_rule_row.Account_To for a in account_base_names
                    ]

                    relevant_account_rows_df = account_set.getAccounts()[row_sel_vec]
                    at_max = sum(relevant_account_rows_df.Balance)

                    future_min_payment = self._getFutureMinPaymentAmount(
                        memo_rule_row.Account_To,
                        account_set,
                        forecast_df,
                        date_YYYYMMDD,
                    )
                    if af_max >= future_min_payment and future_min_payment > 0:
                        reduced_amt = min(af_max, at_max)  # + future_min_payment
                    elif future_min_payment == 0:
                        reduced_amt = min(af_max, at_max)
                    else:
                        reduced_amt = min(af_max, at_max)

                elif (
                    at_type == "checking" or at_type == "loan"
                ):  # havent tested this for loan
                    account_base_names = [
                        a.split(":")[0] for a in account_set.getAccounts().Name
                    ]
                    row_sel_vec = [
                        a == memo_rule_row.Account_To for a in account_base_names
                    ]

                    relevant_account_rows_df = account_set.getAccounts()[row_sel_vec]

                    at_max = sum(relevant_account_rows_df.Balance)
                    reduced_amt = min(af_max, at_max)
                elif at_type == "none":
                    reduced_amt = af_max
                else:
                    raise ValueError("at type error in _processProposedTransactions")

                if reduced_amt == 0:
                    pass
                elif reduced_amt > 0:
                    proposed_row_df.Amount = reduced_amt
                    # print(proposed_row_df.Date+' re-attempt at reduced amt: '+str(reduced_amt))
                    result_of_attempt = self._attemptTransactionApproximate(
                        forecast_df,
                        copy.deepcopy(account_set),
                        memo_set,
                        confirmed_df,
                        proposed_row_df,
                    )
                    transaction_is_permitted = isinstance(
                        result_of_attempt, pd.DataFrame
                    )

                    if transaction_is_permitted:
                        hypothetical_future_state_of_forecast = result_of_attempt
                        account_set = self._sync_account_set_w_forecast_day(
                            account_set, forecast_df, date_YYYYMMDD
                        )
                    else:
                        hypothetical_future_state_of_forecast = None

            if not transaction_is_permitted and proposed_row_df.Deferrable:
                # look ahead for next income date
                future_date_sel_vec = [
                    datetime.datetime.strptime(d, "%Y%m%d")
                    > datetime.datetime.strptime(date_YYYYMMDD, "%Y%m%d")
                    for d in forecast_df.Date
                ]
                income_date_sel_vec = ["income" in m for m in forecast_df.Memo]

                sel_vec = []
                for i in range(0, len(future_date_sel_vec)):
                    sel_vec.append(future_date_sel_vec[i] and income_date_sel_vec[i])

                next_income_row_df = forecast_df[sel_vec].head(1)
                if next_income_row_df.shape[0] > 0:
                    next_income_date = next_income_row_df["Date"].iat[0]
                else:
                    next_income_date = (
                        datetime.datetime.strptime(self.end_date_YYYYMMDD, "%Y%m%d")
                        + datetime.timedelta(days=1)
                    ).strftime("%Y%m%d")

                proposed_row_df.Date = next_income_date
                # todo what if there are no future income rows

                new_deferred_df = pd.concat(
                    [new_deferred_df, pd.DataFrame(proposed_row_df).T]
                )

                remaining_unproposed_transactions_df = relevant_proposed_df[
                    ~relevant_proposed_df.index.isin(proposed_row_df.index)
                ]
                proposed_df = remaining_unproposed_transactions_df

            elif not transaction_is_permitted and not proposed_row_df.Deferrable:
                skipped_df = pd.concat(
                    [new_skipped_df, pd.DataFrame(proposed_row_df).T]
                )

                remaining_unproposed_transactions_df = relevant_proposed_df[
                    ~relevant_proposed_df.index.isin(proposed_row_df.index)
                ]
                proposed_df = remaining_unproposed_transactions_df

            elif transaction_is_permitted:
                if priority_level > 1:
                    # print('process proposed case 3 sync')
                    account_set = self._sync_account_set_w_forecast_day(
                        account_set, forecast_df, date_YYYYMMDD
                    )

                account_set.executeTransaction(
                    Account_From=memo_rule_row.Account_From,
                    Account_To=memo_rule_row.Account_To,
                    Amount=proposed_row_df.Amount,
                    income_flag=False,
                )

                new_confirmed_df = pd.concat(
                    [new_confirmed_df, pd.DataFrame(proposed_row_df).T]
                )

                remaining_unproposed_transactions_df = relevant_proposed_df[
                    ~relevant_proposed_df.index.isin(proposed_row_df.index)
                ]
                relevant_proposed_df = remaining_unproposed_transactions_df

                # forecast_df, skipped_df, confirmed_df, deferred_df
                forecast_with_accurately_updated_future_rows = (
                    hypothetical_future_state_of_forecast
                )

                forecast_rows_to_keep_df = forecast_df[
                    [
                        datetime.datetime.strptime(d, "%Y%m%d")
                        < datetime.datetime.strptime(date_YYYYMMDD, "%Y%m%d")
                        for d in forecast_df.Date
                    ]
                ]

                new_forecast_rows_df = forecast_with_accurately_updated_future_rows[
                    [
                        datetime.datetime.strptime(d, "%Y%m%d")
                        >= datetime.datetime.strptime(date_YYYYMMDD, "%Y%m%d")
                        for d in forecast_with_accurately_updated_future_rows.Date
                    ]
                ]

                forecast_df = pd.concat(
                    [forecast_rows_to_keep_df, new_forecast_rows_df]
                )
                assert forecast_df.shape[0] == forecast_df.drop_duplicates().shape[0]
                forecast_df.reset_index(drop=True, inplace=True)

                row_sel_vec = [
                    x
                    for x in (
                        forecast_df.Date
                        == datetime.datetime.strptime(date_YYYYMMDD, "%Y%m%d")
                    )
                ]
                col_sel_vec = forecast_df.columns == "Memo"

                for account_index, account_row in account_set.getAccounts().iterrows():
                    if (account_index + 1) == account_set.getAccounts().shape[1]:
                        break
                    relevant_balance = account_set.getAccounts().iloc[account_index, 1]

                    row_sel_vec = forecast_df.Date == datetime.datetime.strptime(
                        date_YYYYMMDD, "%Y%m%d"
                    )
                    col_sel_vec = forecast_df.columns == account_row.Name
                    forecast_df.iloc[row_sel_vec, col_sel_vec] = relevant_balance

            else:
                raise ValueError(
                    """This is an edge case that should not be possible
                        transaction_is_permitted...............:"""
                    + str(transaction_is_permitted)
                    + """
                        budget_item_row.Deferrable.............:"""
                    + str(proposed_row_df.Deferrable)
                    + """
                        budget_item_row.Partial_Payment_Allowed:"""
                    + str(proposed_row_df.Partial_Payment_Allowed)
                    + """
                        """
                )

        self.log_stack_depth -= 1
        return forecast_df, new_confirmed_df, new_deferred_df, new_skipped_df

    # account_set, forecast_df, date_YYYYMMDD, memo_set,              ,    relevant_deferred_df,             priority_level, allow_partial_payments, allow_skip_and_defer
    def __processDeferredTransactionsApproximate(
        self,
        account_set,
        forecast_df,
        date_YYYYMMDD,
        memo_set,
        relevant_deferred_df,
        priority_level,
        confirmed_df,
    ):
        log_in_color(
            logger,
            "green",
            "debug",
            "ENTER __processDeferredTransactionsApproximate( D:"
            + str(relevant_deferred_df.shape[0])
            + " )",
            self.log_stack_depth,
        )
        self.log_stack_depth += 1

        # new_confirmed_df = pd.DataFrame(
        #    {'Date': [], 'Priority': [], 'Amount': [], 'Memo': [], 'Deferrable': [], 'Partial_Payment_Allowed': []})
        # new_deferred_df = pd.DataFrame(
        #    {'Date': [], 'Priority': [], 'Amount': [], 'Memo': [], 'Deferrable': [], 'Partial_Payment_Allowed': []})
        new_confirmed_df = confirmed_df.head(0)  # to preserve schema
        new_deferred_df = relevant_deferred_df.head(
            0
        )  # to preserve schema. same as above line btw

        if relevant_deferred_df.shape[0] == 0:

            self.log_stack_depth -= 1
            # log_in_color(logger, 'green', 'debug', 'EXIT __processDeferredTransactionsApproximate()', self.log_stack_depth)
            return forecast_df, new_confirmed_df, new_deferred_df

        for deferred_item_index, deferred_row_df in relevant_deferred_df.iterrows():
            if datetime.datetime.strptime(
                deferred_row_df.Date, "%Y%m%d"
            ) > datetime.datetime.strptime(self.end_date_YYYYMMDD, "%Y%m%d"):
                continue

            relevant_memo_rule_set = memo_set.findMatchingMemoRule(
                deferred_row_df.Memo, deferred_row_df.Priority
            )
            memo_rule_row = relevant_memo_rule_set.getMemoRules().loc[0, :]

            hypothetical_future_state_of_forecast = copy.deepcopy(forecast_df.head(0))

            try:

                not_yet_validated_confirmed_df = pd.concat(
                    [confirmed_df, pd.DataFrame(deferred_row_df).T]
                )
                # not_yet_validated_confirmed_df = confirmed_df.append(deferred_row_df)

                empty_df = pd.DataFrame(
                    {
                        "Date": [],
                        "Priority": [],
                        "Amount": [],
                        "Memo": [],
                        "Deferrable": [],
                        "Partial_Payment_Allowed": [],
                    }
                )

                hypothetical_future_state_of_forecast = (
                    self._computeOptimalForecastApproximate(
                        start_date_YYYYMMDD=self.start_date_YYYYMMDD,
                        end_date_YYYYMMDD=self.end_date_YYYYMMDD,
                        confirmed_df=not_yet_validated_confirmed_df,
                        proposed_df=empty_df,
                        deferred_df=empty_df,
                        skipped_df=empty_df,
                        account_set=copy.deepcopy(
                            self._sync_account_set_w_forecast_day(
                                account_set, forecast_df, self.start_date_YYYYMMDD
                            )
                        ),
                        memo_rule_set=memo_set,
                    )[0]
                )

                transaction_is_permitted = True
            except ValueError as e:
                log_in_color(
                    logger,
                    "red",
                    "debug",
                    "EXIT __processDeferredTransactionsApproximate()",
                    self.log_stack_depth,
                )
                if (
                    re.search(".*Account boundaries were violated.*", str(e.args))
                    is None
                ):  # this is the only exception where we don't want to stop immediately
                    raise e

                transaction_is_permitted = False

            if not transaction_is_permitted and deferred_row_df.Deferrable:

                # deferred_row_df.Date = (datetime.datetime.strptime(deferred_row_df.Date, '%Y%m%d') + datetime.timedelta(
                #     days=1)).strftime('%Y%m%d')

                # look ahead for next income date
                future_date_sel_vec = (
                    d > datetime.datetime.strptime(date_YYYYMMDD, "%Y%m%d")
                    for d in forecast_df.Date
                )
                income_date_sel_vec = ("income" in m for m in forecast_df.Memo)
                next_income_date = forecast_df[
                    future_date_sel_vec & income_date_sel_vec
                ].head(1)["Date"]

                deferred_row_df.Date = next_income_date
                # print('new deferred row')
                # print(deferred_row_df.to_string())

                # todo what is no future income date

                new_deferred_df = pd.concat(
                    [new_deferred_df, pd.DataFrame(deferred_row_df).T]
                )

            elif transaction_is_permitted:

                if priority_level > 1:
                    account_set = self._sync_account_set_w_forecast_day(
                        account_set, forecast_df, date_YYYYMMDD
                    )

                account_set.executeTransaction(
                    Account_From=memo_rule_row.Account_From,
                    Account_To=memo_rule_row.Account_To,
                    Amount=deferred_row_df.Amount,
                    income_flag=False,
                )

                new_confirmed_df = pd.concat(
                    [new_confirmed_df, pd.DataFrame(deferred_row_df).T]
                )

                remaining_unproposed_deferred_transactions_df = relevant_deferred_df[
                    ~relevant_deferred_df.index.isin(deferred_row_df.index)
                ]
                relevant_deferred_df = remaining_unproposed_deferred_transactions_df

                # forecast_df, skipped_df, confirmed_df, deferred_df
                forecast_with_accurately_updated_future_rows = (
                    hypothetical_future_state_of_forecast
                )

                row_sel_vec = [
                    datetime.datetime.strptime(d, "%Y%m%d")
                    < datetime.datetime.strptime(date_YYYYMMDD, "%Y%m%d")
                    for d in forecast_df.Date
                ]
                forecast_rows_to_keep_df = forecast_df.loc[row_sel_vec, :]

                row_sel_vec = [
                    datetime.datetime.strptime(d, "%Y%m%d")
                    >= datetime.datetime.strptime(date_YYYYMMDD, "%Y%m%d")
                    for d in forecast_with_accurately_updated_future_rows.Date
                ]
                new_forecast_rows_df = forecast_with_accurately_updated_future_rows.loc[
                    row_sel_vec, :
                ]

                forecast_df = pd.concat(
                    [forecast_rows_to_keep_df, new_forecast_rows_df]
                )
                assert forecast_df.shape[0] == forecast_df.drop_duplicates().shape[0]
                forecast_df.reset_index(drop=True, inplace=True)

                for account_index, account_row in account_set.getAccounts().iterrows():
                    if (account_index + 1) == account_set.getAccounts().shape[1]:
                        break
                    relevant_balance = account_set.getAccounts().iloc[account_index, 1]

                    row_sel_vec = forecast_df.Date == date_YYYYMMDD
                    col_sel_vec = forecast_df.columns == account_row.Name
                    forecast_df.iloc[row_sel_vec, col_sel_vec] = relevant_balance
            else:
                raise ValueError(
                    """This is an edge case that should not be possible
                        transaction_is_permitted...............:"""
                    + str(transaction_is_permitted)
                    + """
                        budget_item_row.Deferrable.............:"""
                    + str(deferred_row_df.Deferrable)
                    + """
                        budget_item_row.Partial_Payment_Allowed:"""
                    + str(deferred_row_df.Partial_Payment_Allowed)
                    + """
                        """
                )

        self.log_stack_depth -= 1
        log_in_color(
            logger,
            "green",
            "debug",
            "EXIT __processDeferredTransactionsApproximate()",
            self.log_stack_depth,
        )
        return forecast_df, new_confirmed_df, new_deferred_df

    # account_set, forecast_df, date_YYYYMMDD, memo_set,              ,    relevant_deferred_df,             priority_level, allow_partial_payments, allow_skip_and_defer
    # @profile
    def _processDeferredTransactions(
        self,
        account_set,
        forecast_df,
        date_YYYYMMDD,
        memo_set,
        relevant_deferred_df,
        priority_level,
        confirmed_df,
    ):
        """
        Processes deferred transactions by attempting to execute them, updating the forecast,
        and handling further deferrals if necessary.

        Parameters:
        - account_set: AccountSet object representing the current state of accounts.
        - forecast_df: DataFrame containing the forecasted financial data.
        - date_YYYYMMDD: String representing the current date in 'YYYYMMDD' format.
        - memo_set: MemoSet object containing memo rules.
        - relevant_deferred_df: DataFrame of deferred transactions relevant to the current date.
        - priority_level: Integer representing the priority level.
        - confirmed_df: DataFrame of confirmed transactions.

        Returns:
        - forecast_df: Updated forecast DataFrame.
        - new_confirmed_df: DataFrame of newly confirmed transactions.
        - new_deferred_df: DataFrame of transactions that remain deferred.
        """
        # Increment log stack depth for logging purposes
        self.log_stack_depth += 1

        # Initialize DataFrames for new confirmed and deferred transactions, preserving the schema
        new_confirmed_df = confirmed_df.iloc[0:0].copy()
        new_deferred_df = relevant_deferred_df.iloc[0:0].copy()

        # Return early if there are no deferred transactions to process
        if relevant_deferred_df.empty:
            self.log_stack_depth -= 1
            return forecast_df, new_confirmed_df, new_deferred_df

        # Iterate over each deferred transaction
        for deferred_index, deferred_row in relevant_deferred_df.iterrows():
            # Skip if the deferred date is beyond the forecast end date
            deferred_date = deferred_row["Date"]
            if datetime.datetime.strptime(
                deferred_date, "%Y%m%d"
            ) > datetime.datetime.strptime(self.end_date_YYYYMMDD, "%Y%m%d"):
                continue

            # Find the matching memo rule for the deferred transaction
            memo_rule_set = memo_set.findMatchingMemoRule(
                deferred_row["Memo"], deferred_row["Priority"]
            )
            memo_rule_row = memo_rule_set.getMemoRules().iloc[0]

            # Initialize an empty forecast DataFrame for the hypothetical future state
            hypothetical_future_forecast = forecast_df.iloc[0:0].copy()

            try:
                # Combine the confirmed transactions with the deferred transaction
                updated_confirmed_df = pd.concat(
                    [confirmed_df, deferred_row.to_frame().T], ignore_index=True
                )

                # Create empty DataFrames for proposed, deferred, and skipped transactions
                empty_df = pd.DataFrame(
                    columns=[
                        "Date",
                        "Priority",
                        "Amount",
                        "Memo",
                        "Deferrable",
                        "Partial_Payment_Allowed",
                    ]
                )

                # Compute the optimal forecast including the deferred transaction
                hypothetical_future_forecast = self._computeOptimalForecast(
                    start_date_YYYYMMDD=self.start_date_YYYYMMDD,
                    end_date_YYYYMMDD=self.end_date_YYYYMMDD,
                    confirmed_df=updated_confirmed_df,
                    proposed_df=empty_df,
                    deferred_df=empty_df,
                    skipped_df=empty_df,
                    account_set=copy.deepcopy(
                        self._sync_account_set_w_forecast_day(
                            account_set, forecast_df, self.start_date_YYYYMMDD
                        )
                    ),
                    memo_rule_set=memo_set,
                )[0]

                transaction_permitted = True
            except ValueError as e:
                # Check if the exception is due to account boundary violations
                if "Account boundaries were violated" not in str(e):
                    # Reraise the exception if it's not expected
                    raise e
                transaction_permitted = False

            if not transaction_permitted and deferred_row["Deferrable"]:
                # Look ahead for the next income date
                future_dates = forecast_df[forecast_df["Date"] > date_YYYYMMDD]
                income_dates = future_dates[
                    future_dates["Memo"].str.contains("income", case=False, na=False)
                ]
                if not income_dates.empty:
                    next_income_date = income_dates["Date"].iloc[0]
                else:
                    # If no future income date, set to one day after forecast end date
                    next_income_date = (
                        datetime.datetime.strptime(self.end_date_YYYYMMDD, "%Y%m%d")
                        + datetime.timedelta(days=1)
                    ).strftime("%Y%m%d")

                # Update the deferred transaction's date
                deferred_row["Date"] = next_income_date

                # Add the deferred transaction to the new deferred DataFrame
                new_deferred_df = pd.concat(
                    [new_deferred_df, deferred_row.to_frame().T], ignore_index=True
                )
            elif transaction_permitted:
                # If priority level is greater than 1, sync the account set with the forecast
                if priority_level > 1:
                    account_set = self._sync_account_set_w_forecast_day(
                        account_set, forecast_df, date_YYYYMMDD
                    )

                # Execute the transaction
                account_set.executeTransaction(
                    Account_From=memo_rule_row["Account_From"],
                    Account_To=memo_rule_row["Account_To"],
                    Amount=deferred_row["Amount"],
                    income_flag=False,
                )

                # Add the transaction to the new confirmed DataFrame
                confirmed_df = pd.concat(
                    [confirmed_df, deferred_row.to_frame().T], ignore_index=True
                )

                # Remove the transaction from relevant deferred transactions
                relevant_deferred_df = relevant_deferred_df.drop(deferred_index)

                # Update the forecast DataFrame with the hypothetical future forecast
                past_forecast = forecast_df[forecast_df["Date"] < date_YYYYMMDD]
                future_forecast = hypothetical_future_forecast[
                    hypothetical_future_forecast["Date"] >= date_YYYYMMDD
                ]
                forecast_df = pd.concat(
                    [past_forecast, future_forecast], ignore_index=True
                )
                forecast_df.drop_duplicates(subset=["Date"], inplace=True)
                forecast_df.reset_index(drop=True, inplace=True)

                # Update the account balances in the forecast DataFrame for the current date
                for account_row in account_set.getAccounts().itertuples():
                    account_name = account_row.Name
                    account_balance = account_row.Balance
                    if account_name in forecast_df.columns:
                        forecast_df.loc[
                            forecast_df["Date"] == date_YYYYMMDD, account_name
                        ] = account_balance
            else:
                # This case should not occur; raise an error
                raise ValueError(
                    f"""This is an edge case that should not be possible
                        transaction_permitted...............: {transaction_permitted}
                        deferred_row.Deferrable.............: {deferred_row['Deferrable']}
                        deferred_row.Partial_Payment_Allowed: {deferred_row['Partial_Payment_Allowed']}
                        """
                )

        # Decrement log stack depth
        self.log_stack_depth -= 1

        # Return the updated forecast and DataFrames
        return forecast_df, confirmed_df, new_deferred_df

    def _executeTransactionsForDayApproximate(
        self,
        account_set,
        forecast_df,
        date_YYYYMMDD,
        memo_set,
        confirmed_df,
        proposed_df,
        deferred_df,
        skipped_df,
        priority_level,
    ):
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

        isP1 = priority_level == 1

        relevant_proposed_df = copy.deepcopy(
            proposed_df[
                (proposed_df.Priority == priority_level)
                & (proposed_df.Date == date_YYYYMMDD)
            ]
        )
        relevant_confirmed_df = copy.deepcopy(
            confirmed_df[
                (confirmed_df.Priority == priority_level)
                & (confirmed_df.Date == date_YYYYMMDD)
            ]
        )
        relevant_deferred_df = copy.deepcopy(
            deferred_df[
                (deferred_df.Priority <= priority_level)
                & (deferred_df.Date == date_YYYYMMDD)
            ]
        )

        F = "F:" + str(forecast_df.shape[0])
        C = "C:" + str(relevant_confirmed_df.shape[0])
        P = "P:" + str(relevant_proposed_df.shape[0])
        D = "D:" + str(relevant_deferred_df.shape[0])
        # log_in_color(logger, 'cyan', 'debug',
        #              'ENTER _executeTransactionsForDayApproximate('+date_YYYYMMDD+' ' + str(priority_level) + ' ' + F + ' ' + C + ' ' + P + ' ' + D + ' ) '+str(date_YYYYMMDD),
        #              self.log_stack_depth)
        self.log_stack_depth += 1
        # log_in_color(logger, 'cyan', 'debug', 'forecast_df:', self.log_stack_depth)
        # log_in_color(logger, 'cyan', 'debug',forecast_df.to_string(),self.log_stack_depth)

        if isP1:
            assert relevant_proposed_df.empty

        thereArePendingConfirmedTransactions = not relevant_confirmed_df.empty

        date_sel_vec = [(d == date_YYYYMMDD) for d in forecast_df.Date]
        noMatchingDayInForecast = forecast_df.loc[date_sel_vec].empty
        notPastEndOfForecast = datetime.datetime.strptime(
            date_YYYYMMDD, "%Y%m%d"
        ) <= datetime.datetime.strptime(self.end_date_YYYYMMDD, "%Y%m%d")

        if isP1 and noMatchingDayInForecast and notPastEndOfForecast:
            forecast_df = self._addANewDayToTheForecast(forecast_df, date_YYYYMMDD)

        if isP1 and thereArePendingConfirmedTransactions:
            relevant_confirmed_df = self._sortTxnsToPreventErrors(
                relevant_confirmed_df, account_set, memo_set
            )

        if priority_level > 1:
            account_set = self._sync_account_set_w_forecast_day(
                account_set, forecast_df, date_YYYYMMDD
            )

        # print('forecast_df:')
        # print(forecast_df.to_string())

        # log_in_color(logger,'green','debug','eTFD :: before processConfirmed',self.log_stack_depth)
        # print('before _processConfirmedTransactions')
        # print(account_set.getAccounts().to_string())
        forecast_df = self._processConfirmedTransactions(
            forecast_df, relevant_confirmed_df, memo_set, account_set, date_YYYYMMDD
        )
        # print('after _processConfirmedTransactions')
        # print(account_set.getAccounts().to_string())
        # log_in_color(logger, 'green', 'debug', 'eTFD :: after processConfirmed', self.log_stack_depth)

        if priority_level > 1:
            # log_in_color(logger, 'green', 'debug', 'eTFD :: before processProposed', self.log_stack_depth)
            forecast_df, new_confirmed_df, new_deferred_df, new_skipped_df = (
                self._processProposedTransactionsApproximate(
                    account_set,
                    forecast_df,
                    date_YYYYMMDD,
                    memo_set,
                    confirmed_df,
                    relevant_proposed_df,
                    priority_level,
                )
            )
            # log_in_color(logger, 'green', 'debug', 'eTFD :: after processProposed', self.log_stack_depth)
            #
            # log_in_color(logger, 'white', 'debug', 'new_confirmed_df:', self.log_stack_depth)
            # log_in_color(logger, 'white', 'debug', new_confirmed_df.to_string(), self.log_stack_depth)
            #
            # log_in_color(logger, 'white', 'debug', 'new_deferred_df:', self.log_stack_depth)
            # log_in_color(logger, 'white', 'debug', new_deferred_df.to_string(), self.log_stack_depth)
            #
            # log_in_color(logger, 'white', 'debug', 'new_skipped_df:', self.log_stack_depth)
            # log_in_color(logger, 'white', 'debug', new_skipped_df.to_string(), self.log_stack_depth)

            confirmed_df = pd.concat([confirmed_df, new_confirmed_df])
            confirmed_df.reset_index(drop=True, inplace=True)

            deferred_df = pd.concat([deferred_df, new_deferred_df])
            deferred_df.reset_index(drop=True, inplace=True)

            skipped_df = pd.concat([skipped_df, new_skipped_df])
            skipped_df.reset_index(drop=True, inplace=True)

            # log_in_color(logger, 'white', 'debug','updated confirmed_df:',self.log_stack_depth)
            # log_in_color(logger, 'white', 'debug',confirmed_df.to_string(),self.log_stack_depth)
            #
            # log_in_color(logger, 'white', 'debug','updated deferred_df:',self.log_stack_depth)
            # log_in_color(logger, 'white', 'debug',deferred_df.to_string(),self.log_stack_depth)
            #
            # log_in_color(logger, 'white', 'debug','updated skipped_df:',self.log_stack_depth)
            # log_in_color(logger, 'white', 'debug',skipped_df.to_string(),self.log_stack_depth)

            if deferred_df.shape[0] > 0:
                relevant_deferred_before_processing = pd.DataFrame(
                    relevant_deferred_df, copy=True
                )  # we need this to remove old txns if they stay deferred

                # log_in_color(logger, 'green', 'debug', 'eTFD :: before processDeferred', self.log_stack_depth)
                forecast_df, new_confirmed_df, new_deferred_df = (
                    self.__processDeferredTransactionsApproximate(
                        account_set,
                        forecast_df,
                        date_YYYYMMDD,
                        memo_set,
                        pd.DataFrame(relevant_deferred_df, copy=True),
                        priority_level,
                        confirmed_df,
                    )
                )
                # log_in_color(logger, 'green', 'debug', 'eTFD :: after processDeferred', self.log_stack_depth)

                confirmed_df = pd.concat([confirmed_df, new_confirmed_df])
                confirmed_df.reset_index(drop=True, inplace=True)

                p_LJ_c = pd.merge(
                    proposed_df, confirmed_df, on=["Date", "Memo", "Priority"]
                )

                # deferred_df = deferred_df - relevant + new. index won't be the same as OG
                # this is the inverse of how we selected the relevant rows
                p_sel_vec = deferred_df.Priority > priority_level
                # d_sel_vec = (deferred_df.Date != date_YYYYMMDD)
                d_sel_vec = [d != date_YYYYMMDD for d in deferred_df.Date]
                sel_vec = p_sel_vec | d_sel_vec
                not_relevant_deferred_df = pd.DataFrame(deferred_df[sel_vec], copy=True)

                deferred_df = pd.concat([not_relevant_deferred_df, new_deferred_df])
                # deferred_df = not_relevant_deferred_df.append(new_deferred_df)
                deferred_df.reset_index(drop=True, inplace=True)

        self.log_stack_depth -= 1
        return [forecast_df, confirmed_df, deferred_df, skipped_df]

    # @profile
    def _executeTransactionsForDay(
        self,
        account_set,
        forecast_df,
        date_YYYYMMDD,
        memo_set,
        confirmed_df,
        proposed_df,
        deferred_df,
        skipped_df,
        priority_level,
    ):
        log_in_color(
            logger,
            "white",
            "debug",
            str(date_YYYYMMDD)
            + " ENTER _executeTransactionsForDay p="
            + str(priority_level),
            self.log_stack_depth,
        )
        self.log_stack_depth += 1

        # log_in_color(logger, 'white', 'debug', 'before forecast_df:', self.log_stack_depth)
        # log_in_color(logger, 'white', 'debug', forecast_df.to_string(), self.log_stack_depth)

        # if not confirmed_df.empty:
        #     log_in_color(logger, 'white', 'debug', 'confirmed_df:', self.log_stack_depth)
        #     log_in_color(logger, 'white', 'debug', confirmed_df.to_string(), self.log_stack_depth)

        isP1 = priority_level == 1

        # Filter transactions relevant to the current day and priority level
        relevant_proposed_df = proposed_df[
            (proposed_df.Priority == priority_level)
            & (proposed_df.Date == date_YYYYMMDD)
        ]
        relevant_confirmed_df = confirmed_df[
            (confirmed_df.Priority == priority_level)
            & (confirmed_df.Date == date_YYYYMMDD)
        ]
        relevant_deferred_df = deferred_df[
            (deferred_df.Priority <= priority_level)
            & (deferred_df.Date == date_YYYYMMDD)
        ]

        # Ensure no proposed transactions exist for priority 1
        if isP1:
            assert relevant_proposed_df.empty

        # Check if there are pending confirmed transactions
        thereArePendingConfirmedTransactions = not relevant_confirmed_df.empty

        # Check if the current day exists in the forecast and if it's within the forecast range
        date_sel_vec = forecast_df["Date"] == date_YYYYMMDD
        noMatchingDayInForecast = forecast_df.loc[date_sel_vec].empty
        notPastEndOfForecast = datetime.datetime.strptime(
            date_YYYYMMDD, "%Y%m%d"
        ) <= datetime.datetime.strptime(self.end_date_YYYYMMDD, "%Y%m%d")

        # Add a new day to the forecast if required
        if isP1 and noMatchingDayInForecast and notPastEndOfForecast:
            forecast_df = self._addANewDayToTheForecast(forecast_df, date_YYYYMMDD)

        # Sort transactions to prioritize income first
        # print('isP1 and thereArePendingConfirmedTransactions:'+str(isP1 and thereArePendingConfirmedTransactions))
        # print('isP1................................:'+str(isP1))
        # print('thereArePendingConfirmedTransactions:' + str(thereArePendingConfirmedTransactions))
        # if thereArePendingConfirmedTransactions:
        #     relevant_confirmed_df = self._sortTxnsToPreventErrors(relevant_confirmed_df, account_set, memo_set)

        # Sync account set with the forecast for non-priority 1 transactions
        if priority_level > 1:
            account_set = self._sync_account_set_w_forecast_day(
                account_set, forecast_df, date_YYYYMMDD
            )

        # if not relevant_confirmed_df.empty:
        #     log_in_color(logger, 'white', 'debug', 'relevant_confirmed_df:', self.log_stack_depth)
        #     log_in_color(logger, 'white', 'debug', relevant_confirmed_df.to_string(), self.log_stack_depth)

        try:
            # Process confirmed transactions
            forecast_df = self._processConfirmedTransactions(
                forecast_df, relevant_confirmed_df, memo_set, account_set, date_YYYYMMDD
            )
        except Exception as e:
            self.log_stack_depth -= 1
            log_in_color(
                logger,
                "white",
                "debug",
                str(date_YYYYMMDD)
                + " EXIT _executeTransactionsForDay p="
                + str(priority_level),
                self.log_stack_depth,
            )
            raise e

        # Process proposed transactions for priority levels greater than 1
        if priority_level > 1:
            forecast_df, new_confirmed_df, new_deferred_df, new_skipped_df = (
                self._processProposedTransactions(
                    account_set,
                    forecast_df,
                    date_YYYYMMDD,
                    memo_set,
                    confirmed_df,
                    relevant_proposed_df,
                    priority_level,
                )
            )

            # Update confirmed, deferred, and skipped DataFrames
            confirmed_df = pd.concat([confirmed_df, new_confirmed_df]).reset_index(
                drop=True
            )

            deferred_df = pd.concat([deferred_df, new_deferred_df]).reset_index(
                drop=True
            )
            skipped_df = pd.concat([skipped_df, new_skipped_df]).reset_index(drop=True)

            # Process deferred transactions if any exist
            if not deferred_df.empty:
                relevant_deferred_before_processing = (
                    relevant_deferred_df.copy()
                )  # Keep original for comparison

                forecast_df, new_confirmed_df, new_deferred_df = (
                    self._processDeferredTransactions(
                        account_set,
                        forecast_df,
                        date_YYYYMMDD,
                        memo_set,
                        relevant_deferred_df.copy(),
                        priority_level,
                        confirmed_df,
                    )
                )

                # Update confirmed DataFrame with newly confirmed transactions
                confirmed_df = pd.concat([confirmed_df, new_confirmed_df]).reset_index(
                    drop=True
                )

                # Adjust deferred DataFrame by removing processed transactions and adding new deferred ones
                not_relevant_deferred_df = deferred_df[
                    (deferred_df.Priority > priority_level)
                    | (deferred_df.Date != date_YYYYMMDD)
                ]
                deferred_df = pd.concat(
                    [not_relevant_deferred_df, new_deferred_df]
                ).reset_index(drop=True)

        # log_in_color(logger, 'white', 'debug', 'after forecast_df:', self.log_stack_depth)
        # log_in_color(logger, 'white', 'debug', forecast_df.to_string(), self.log_stack_depth)

        self.log_stack_depth -= 1
        log_in_color(
            logger,
            "white",
            "debug",
            str(date_YYYYMMDD)
            + " EXIT _executeTransactionsForDay p="
            + str(priority_level),
            self.log_stack_depth,
        )
        return [forecast_df, confirmed_df, deferred_df, skipped_df]

    # @profile
    def _calculateLoanInterestAccrualsForDay(
        self, account_set, current_forecast_row_df
    ):
        """
        Calculates and applies interest accruals for loans on the current day.

        Parameters:
        - account_set: AccountSet object containing account information.
        - current_forecast_row_df: DataFrame containing the forecast row for the current date.

        Returns:
        - Updated current_forecast_row_df with applied interest accruals.
        """
        log_in_color(
            logger,
            "white",
            "debug",
            str(current_forecast_row_df.Date.iat[0])
            + " ENTER _calculateLoanInterestAccrualsForDay",
            self.log_stack_depth,
        )
        # Increment log stack depth for logging purposes
        self.log_stack_depth += 1

        # print('PRE INTEREST ACCRUAL FORECAST ROW')
        # print(current_forecast_row_df.to_string())

        # Extract the current date
        current_date = current_forecast_row_df["Date"].iat[0]

        # Iterate over each account to calculate interest accruals
        for account_index, account_row in account_set.getAccounts().iterrows():
            # log_in_color(logger, 'white', 'debug', 'Might skip '+account_row.Name, self.log_stack_depth)
            # Skip accounts that are not interest-bearing or are previous statement balances
            if account_row["Account_Type"] == "credit prev stmt bal":
                continue

            # Get the interest cadence and type
            if account_row.get("Interest_Cadence", "") is not None:
                interest_cadence = account_row.get("Interest_Cadence", "").lower()
            else:
                continue

            if account_row.get("Interest_Type", "") is not None:
                interest_type = account_row.get("Interest_Type", "").lower()
            else:
                continue

            # log_in_color(logger, 'white', 'debug', 'Did not skip '+account_row.Name, self.log_stack_depth)

            # # Skip if interest cadence or type is not defined
            # if not interest_cadence or interest_cadence == 'none' or not interest_type:
            #     continue

            # Calculate the number of days since the billing start date
            billing_start_date = account_row["Billing_Start_Date"]
            num_days = (
                pd.to_datetime(current_date, format="%Y%m%d")
                - pd.to_datetime(billing_start_date, format="%Y%m%d")
            ).days

            # Skip if current date is before billing start date
            if num_days < 0:
                continue

            # Generate date sequence based on billing start date and interest cadence
            # Assume generate_date_sequence is a function that returns a set of dates
            dseq = generate_date_sequence(
                start_date_YYYYMMDD=billing_start_date,
                num_days=num_days,
                cadence=interest_cadence,
            )

            # Include billing start date if current date matches
            if current_date == billing_start_date:
                dseq.append(current_date)

            # Check if current date is in the interest accrual dates
            if current_date in dseq:
                apr = account_row["APR"]
                balance = account_row["Balance"]

                # Calculate interest based on type and cadence
                if interest_type == "compound":
                    if interest_cadence == "monthly":
                        # Compound interest, monthly accrual
                        interest_accrued = balance * (apr / 12)
                        # Update account balance
                        account_set.accounts[account_index].balance += interest_accrued

                        # # Move current statement balance to previous statement balance for credit accounts
                        # if account_row['Account_Type'] == 'credit curr stmt bal':
                        #     prev_account_index = account_index - 1
                        #     prev_stmt_balance = account_set.accounts[prev_account_index].balance
                        #     account_set.accounts[account_index].balance += prev_stmt_balance
                        #     account_set.accounts[prev_account_index].balance = 0
                    else:
                        # Other compound interest cadences not implemented
                        raise NotImplementedError(
                            f"Compound interest with '{interest_cadence}' cadence is not implemented."
                        )
                elif interest_type == "simple":
                    if interest_cadence == "daily":
                        # Simple interest, daily accrual
                        interest_accrued = balance * (apr / 365.25)

                        # print('current_date, Name, interest '+str(current_date)+' '+str(account_row.Name)+' '+str(round(interest_accrued,2)))

                        # Update interest account balance (assuming it's the next account)
                        interest_account_index = account_index + 1
                        # if interest_account_index < len(account_set.accounts):
                        account_set.accounts[
                            interest_account_index
                        ].balance += interest_accrued
                        # Round small balances to zero
                        # if abs(account_set.accounts[interest_account_index].balance) < 0.01:
                        #     account_set.accounts[interest_account_index].balance = 0.0
                    else:
                        # Other simple interest cadences not implemented
                        raise NotImplementedError(
                            f"Simple interest with '{interest_cadence}' cadence is not implemented."
                        )
                else:
                    raise ValueError(
                        f"Unknown interest type '{interest_type}' for account '{account_row['Name']}'."
                    )

            # print('PRE-UPDATE ACCRUAL FORECAST ROW')
            # print(current_forecast_row_df.to_string())

            # Update the current forecast row with the updated account balances
            for idx, acc_row in account_set.getAccounts().iterrows():
                account_name = acc_row["Name"]
                balance = acc_row["Balance"]
                if account_name in current_forecast_row_df.columns:
                    current_forecast_row_df.iloc[
                        0, current_forecast_row_df.columns == account_name
                    ] = balance
                    pass

            # print('POST-UPDATE ACCRUAL FORECAST ROW')
            # print(current_forecast_row_df.to_string())

        # Decrement log stack depth
        self.log_stack_depth -= 1

        # print('POST INTEREST ACCRUAL FORECAST ROW')
        # print(current_forecast_row_df.to_string())

        log_in_color(
            logger,
            "white",
            "debug",
            str(current_forecast_row_df.Date.iat[0])
            + " EXIT _calculateLoanInterestAccrualsForDay",
            self.log_stack_depth,
        )
        return current_forecast_row_df

    # a design flaw this has is that if a cc min payment is made in advance, but that payment is past the end of the forecast,
    # the payment will show up as extra instead of advance
    # in order to fix this, the executeTransaction function would need to be able to look forward, which is a design weakness
    # i hate more than this "extra instead of advance for last payment in forecast" problem
    # Note that this is not really a problem because the only difference is what the payment is called, not the amount or date
    # .... on second thought ... we may be able to add an explicit check for this
    # BIG WOOPS - this method is only called on P1, before any additional payments.
    # I think this needs to be its own method :(
    # Just Kidding... leaving these comments in case I get stuck in this thought loop again: this code is recursive, all
    # txns are tested in sub forecasts as p1 before they are approved, therefore this logic is fine
    # @profile
    def _executeCreditCardMinimumPayments(
        self, forecast_df, account_set, current_forecast_row_df
    ):
        """
        Executes minimum payments for credit card accounts.

        Parameters:
        - forecast_df: DataFrame containing forecasted financial data.
        - account_set: The current set of accounts.
        - current_forecast_row_df: The forecast row for the current date.

        Returns:
        - Updated current_forecast_row_df after executing credit card minimum payments.
        """
        log_in_color(
            logger,
            "white",
            "debug",
            str(current_forecast_row_df.Date.iat[0])
            + " ENTER _executeCreditCardMinimumPayments ",
            self.log_stack_depth,
        )
        self.log_stack_depth += 1

        # log_in_color(logger, 'white', 'debug','BEFORE forecast_df:', self.log_stack_depth)
        # log_in_color(logger, 'white', 'debug', forecast_df.to_string(), self.log_stack_depth)

        primary_checking_account_name = account_set.getPrimaryCheckingAccountName()

        # Loop through accounts to process credit card minimum payments
        for account_index, account_row in account_set.getAccounts().iterrows():
            if account_row.Account_Type != "credit prev stmt bal":
                continue

            # Skip accounts without a billing start date
            billing_start_date = account_row.Billing_Start_Date
            if pd.isnull(billing_start_date) or billing_start_date == "None":
                continue

            current_date_str = current_forecast_row_df.Date.iloc[0]
            current_date = datetime.datetime.strptime(current_date_str, "%Y%m%d")

            billing_start_datetime = datetime.datetime.strptime(
                billing_start_date, "%Y%m%d"
            )
            num_days = (current_date - billing_start_datetime).days

            # Generate billing days
            if num_days >= 0:
                billing_days = set(
                    generate_date_sequence(billing_start_date, num_days, "monthly")
                )
            else:
                billing_days = set()

            if current_date_str == billing_start_date:
                billing_days.add(current_date_str)

            # print('billing_start_date:'+str(billing_start_date))
            # print('current_date_str:'+str(current_date_str))
            # print('billing_days:'+str(billing_days))
            if current_date_str not in billing_days:
                continue

            # this will be the correct replacement once bcp is tracked properly
            advance_payment_amount = current_forecast_row_df[
                account_row.Name.split(":")[0] + ": Credit Billing Cycle Payment Bal"
            ].iat[0]

            # THIS IS OLD PREPAID LOGIC
            # advance_payment_amount = self._getTotalPrepaidInCreditCardBillingCycle(
            #     account_row.Name, account_set, forecast_df, current_date_str
            # )

            # Determine the earliest billing date within the forecast range
            first_day_of_forecast_str = forecast_df.Date.iloc[0]
            first_day_of_forecast = datetime.datetime.strptime(
                first_day_of_forecast_str, "%Y%m%d"
            )

            relevant_billing_days = [
                d
                for d in billing_days
                if datetime.datetime.strptime(d, "%Y%m%d") > first_day_of_forecast
            ]

            if not relevant_billing_days:
                continue

            # earliest_billing_date_within_forecast_range = min(relevant_billing_days)
            # if current_date_str == earliest_billing_date_within_forecast_range:
            #     # First billing date in forecast range
            #     current_prev_stmt_balance = forecast_df.iloc[0][account_row.Name]
            #     prev_prev_stmt_balance = current_prev_stmt_balance
            #     current_curr_stmt_balance = account_set.getAccounts().iloc[account_index - 1]['Balance']
            # else:
            #     # Get previous billing cycle data
            #     left_check_bound = current_date - datetime.timedelta(days=35)
            #     forecast_dates = forecast_df['Date'].apply(lambda d: datetime.datetime.strptime(d, '%Y%m%d'))
            #     check_region = forecast_df[
            #         (forecast_dates > left_check_bound) & (forecast_dates <= current_date)
            #         ]

            # THIS IS OLD PREV PREV BALANCE LOGIC
            # previous_min_payment_dates = check_region['Memo Directives'].str.contains('CC MIN PAYMENT')
            # if previous_min_payment_dates.any():
            #     prev_prev_stmt_balance = check_region.loc[previous_min_payment_dates, account_row.Name].iat[0]
            # else:
            #     prev_prev_stmt_balance = 0
            prev_prev_aname = (
                account_row.Name.split(":")[0] + ": Credit End of Prev Cycle Bal"
            )
            prev_prev_stmt_bal = current_forecast_row_df[prev_prev_aname].iat[0]

            current_prev_stmt_balance = account_row.Balance
            current_curr_stmt_balance = account_set.getAccounts().iloc[
                account_index - 1
            ]["Balance"]

            # print(str(current_date_str)+' prev_prev_stmt_balance: '+str(prev_prev_stmt_balance))

            # Calculate interest and principal to be charged
            interest_rate_monthly = account_row.APR / 12
            # interest_accrued_this_cycle = round(prev_prev_stmt_balance * interest_rate_monthly, 2)
            interest_accrued_this_cycle = prev_prev_stmt_bal * interest_rate_monthly
            principal_due_this_cycle = (
                prev_prev_stmt_bal * 0.01
            )  # if prev_prev and prev dont match, that implies a payment

            # Update account balances and memo directives
            if interest_accrued_this_cycle > 0:
                account_set.accounts[
                    account_index
                ].balance += interest_accrued_this_cycle
                new_prev_stmt_bal = (
                    current_prev_stmt_balance + interest_accrued_this_cycle
                )
                # interest_md_text = f'CC INTEREST ({account_row.Name} +${interest_accrued_this_cycle:.2f})'
                interest_md_text = (
                    f"CC INTEREST ({account_row.Name} +${interest_accrued_this_cycle})"
                )
                md_split_semicolon = (
                    current_forecast_row_df["Memo Directives"].iat[0].split(";")
                )
                md_split_semicolon = [md for md in md_split_semicolon if md]
                md_split_semicolon.append(interest_md_text)
                current_forecast_row_df["Memo Directives"] = "; ".join(
                    md_split_semicolon
                )
            else:
                new_prev_stmt_bal = current_prev_stmt_balance

            curr_stmt_balance = account_set.accounts[
                account_index - 1
            ].balance  # get curr_stmt_bal
            account_set.accounts[
                account_index
            ].balance += curr_stmt_balance  # add curr to prev
            # account_set.accounts[account_index].balance = round(account_set.accounts[account_index].balance, 2) #round prev
            account_set.accounts[account_index].balance = account_set.accounts[
                account_index
            ].balance
            account_set.accounts[account_index - 1].balance = 0  # set curr to 0
            # current_forecast_row_df[account_row.Name] = round(account_set.accounts[account_index].balance, 2) #update prev on forecast and round
            current_forecast_row_df[account_row.Name] = account_set.accounts[
                account_index
            ].balance
            current_forecast_row_df[account_set.accounts[account_index - 1].name] = (
                0  # set curr on forecast to 0
            )

            cycle_payment_bal_aname = (
                account_row.Name.split(":")[0] + ": Credit Billing Cycle Payment Bal"
            )
            current_forecast_row_df[cycle_payment_bal_aname] = 0

            # print('advance_payment_amount:' + str(advance_payment_amount))
            # print('interest_accrued_this_cycle:' + str(interest_accrued_this_cycle))

            total_owed_before_accrual = account_set.accounts[account_index].balance
            min_payment = AccountSet.determineMinPaymentAmount(
                advance_payment_amount,
                interest_accrued_this_cycle,
                principal_due_this_cycle,
                total_owed_before_accrual,
                account_row.Minimum_Payment,
            )

            # print('min_payment:'+str(min_payment))
            # print('current_forecast_row_df:')
            # print(str(current_forecast_row_df.to_string()))

            total_payment_due = min_payment  # - advance_payment_amount, now accounted for in determineMinPaymentAmount
            if total_payment_due <= 0:
                payment_toward_prev = 0
                payment_toward_curr = 0
            else:
                if current_prev_stmt_balance >= total_payment_due:
                    payment_toward_prev = total_payment_due
                    payment_toward_curr = 0
                else:
                    payment_toward_prev = current_prev_stmt_balance
                    payment_toward_curr = total_payment_due - payment_toward_prev

            total_payment = payment_toward_prev + payment_toward_curr
            if total_payment > 0:
                account_set.executeTransaction(
                    Account_From=primary_checking_account_name,
                    Account_To=account_row.Name.split(":")[0],
                    Amount=total_payment,
                    minimum_payment_flag=True,
                )

                curr_aname = account_row.Name.split(":")[0] + ": Curr Stmt Bal"
                prev_aname = account_row.Name.split(":")[0] + ": Prev Stmt Bal"
                # current_forecast_row_df[curr_aname] = round(account_set.accounts[account_index - 1].balance, 2)
                # current_forecast_row_df[prev_aname] = round(account_set.accounts[account_index].balance, 2)
                current_forecast_row_df[curr_aname] = account_set.accounts[
                    account_index - 1
                ].balance
                current_forecast_row_df[prev_aname] = account_set.accounts[
                    account_index
                ].balance
                check_acct_index = list(account_set.getAccounts().Name).index(
                    primary_checking_account_name
                )
                # current_forecast_row_df[primary_checking_account_name] = round(account_set.accounts[check_acct_index].balance, 2)
                current_forecast_row_df[primary_checking_account_name] = (
                    account_set.accounts[check_acct_index].balance
                )

                memo_parts = []
                if payment_toward_prev > 0:
                    memo_parts.append(
                        # f'CC MIN PAYMENT ({account_row.Name.split(":")[0]}: Prev Stmt Bal -${payment_toward_prev:.2f})'
                        f'CC MIN PAYMENT ({account_row.Name.split(":")[0]}: Prev Stmt Bal -${payment_toward_prev})'
                    )
                if payment_toward_curr > 0:
                    memo_parts.append(
                        # f'CC MIN PAYMENT ({account_row.Name.split(":")[0]}: Curr Stmt Bal -${payment_toward_curr:.2f})'
                        f'CC MIN PAYMENT ({account_row.Name.split(":")[0]}: Curr Stmt Bal -${payment_toward_curr})'
                    )
                if total_payment > 0:
                    memo_parts.append(
                        # f'CC MIN PAYMENT ({primary_checking_account_name} -${total_payment:.2f})'
                        f"CC MIN PAYMENT ({primary_checking_account_name} -${total_payment})"
                    )

                md_split_semicolon = (
                    current_forecast_row_df["Memo Directives"].iat[0].split(";")
                )
                md_split_semicolon = [md for md in md_split_semicolon if md]
                md_split_semicolon += memo_parts
                # md_split_semicolon.append(interest_md_text)
                current_forecast_row_df["Memo Directives"] = "; ".join(
                    md_split_semicolon
                )
            elif (
                "CC MIN PAYMENT" in current_forecast_row_df["Memo Directives"]
                or advance_payment_amount > 0
            ):

                new_prev_memo = f'CC MIN PAYMENT ALREADY MADE ({account_row.Name.split(":")[0]}: Prev Stmt Bal -$0.00)'
                new_check_memo = f"CC MIN PAYMENT ALREADY MADE ({primary_checking_account_name} -$0.00)"
                md_split_semicolon = (
                    current_forecast_row_df["Memo Directives"].iat[0].split(";")
                )
                md_split_semicolon = [md for md in md_split_semicolon if md]
                md_split_semicolon.append(new_prev_memo)
                md_split_semicolon.append(new_check_memo)
                current_forecast_row_df["Memo Directives"] = "; ".join(
                    md_split_semicolon
                )
            # else:  there was no min payment, and one is not necessary now

            # Clean up memo directives
            memo_directives = [
                md.strip()
                for md in current_forecast_row_df["Memo Directives"].iat[0].split(";")
                if md.strip()
            ]
            current_forecast_row_df["Memo Directives"] = "; ".join(memo_directives)

        self.log_stack_depth -= 1
        # print('current_forecast_row_df:')
        # print(current_forecast_row_df.to_string())
        log_in_color(
            logger,
            "white",
            "debug",
            str(current_forecast_row_df.Date.iat[0])
            + " EXIT _executeCreditCardMinimumPayments ",
            self.log_stack_depth,
        )
        return current_forecast_row_df

    # @profile
    def _executeLoanMinimumPayments(self, account_set, current_forecast_row_df):
        log_in_color(
            logger,
            "white",
            "debug",
            str(current_forecast_row_df.Date.iat[0])
            + " ENTER _executeLoanMinimumPayments",
            self.log_stack_depth,
        )
        self.log_stack_depth += 1

        # log_in_color(logger, 'white', 'debug','before current_forecast_row_df:', self.log_stack_depth)
        # log_in_color(logger, 'white', 'debug', current_forecast_row_df.to_string(), self.log_stack_depth)

        primary_checking_account_name = account_set.getPrimaryCheckingAccountName()

        # the branch logic here assumes the sort order of accounts in account list
        for account_index, account_row in account_set.getAccounts().iterrows():

            if account_row.Account_Type == "prev smt bal":
                continue

            # not sure why both of these checks are necessary
            if account_row.Billing_Start_Date == "None":
                continue

            if pd.isnull(account_row.Billing_Start_Date):
                continue

            num_days = (
                datetime.datetime.strptime(
                    current_forecast_row_df.Date.iloc[0], "%Y%m%d"
                )
                - datetime.datetime.strptime(account_row.Billing_Start_Date, "%Y%m%d")
            ).days
            billing_days = set(
                generate_date_sequence(
                    account_row.Billing_Start_Date, num_days, "monthly"
                )
            )

            # if the input date matches the start date, add it to the set (bc range where start = end == null set)
            if current_forecast_row_df.Date.iloc[0] == account_row.Billing_Start_Date:
                billing_days = set(current_forecast_row_df.Date).union(billing_days)

            if current_forecast_row_df.Date.iloc[0] in billing_days:

                if account_row.Account_Type == "principal balance":  # loan min payment

                    minimum_payment_amount = (
                        account_set.getAccounts().loc[account_index, :].Minimum_Payment
                    )

                    # todo I notice that this depends on the order of accounts

                    # new
                    current_pbal_balance = account_row.Balance
                    current_interest_balance = (
                        account_set.getAccounts().loc[account_index + 1, :].Balance
                    )
                    current_debt_balance = (
                        current_pbal_balance + current_interest_balance
                    )

                    payment_toward_interest = min(
                        minimum_payment_amount, current_interest_balance
                    )
                    payment_toward_principal = min(
                        current_pbal_balance,
                        minimum_payment_amount - payment_toward_interest,
                    )

                    loan_payment_amount = min(
                        current_debt_balance, minimum_payment_amount
                    )

                    if loan_payment_amount > 0:
                        # log_in_color(logger, 'white', 'debug','loan_payment_amount:'+str(loan_payment_amount), self.log_stack_depth)
                        account_set.executeTransaction(
                            Account_From=primary_checking_account_name,
                            Account_To=account_row.Name.split(":")[0],
                            # Note that the execute transaction method will split the amount paid between the 2 accounts
                            Amount=loan_payment_amount,
                            minimum_payment_flag=True,
                        )

                        if payment_toward_interest > 0:
                            # current_forecast_row_df['Memo Directives'] += '; LOAN MIN PAYMENT (' + account_row.Name.split(':')[0] + ': Interest -$' + str(f'{payment_toward_interest:.2f}') + ')'
                            current_forecast_row_df["Memo Directives"] += (
                                "; LOAN MIN PAYMENT ("
                                + account_row.Name.split(":")[0]
                                + ": Interest -$"
                                + str(f"{payment_toward_interest}")
                                + ")"
                            )

                        if payment_toward_principal > 0:
                            # current_forecast_row_df['Memo Directives'] += '; LOAN MIN PAYMENT (' + account_row.Name.split(':')[0] + ': Principal Balance -$' + str(f'{payment_toward_principal:.2f}') + ')'
                            current_forecast_row_df["Memo Directives"] += (
                                "; LOAN MIN PAYMENT ("
                                + account_row.Name.split(":")[0]
                                + ": Principal Balance -$"
                                + str(f"{payment_toward_principal}")
                                + ")"
                            )

                        if (payment_toward_interest + payment_toward_principal) > 0:
                            # print('primary_checking_account_name:'+str(primary_checking_account_name))
                            # print('primary_checking_account_name:' + str(payment_toward_interest))
                            # print('primary_checking_account_name:' + str(payment_toward_principal))
                            # current_forecast_row_df['Memo Directives'] += '; LOAN MIN PAYMENT ('+primary_checking_account_name+' -$' + str(f'{( payment_toward_interest + payment_toward_principal ):.2f}') + ')'
                            current_forecast_row_df["Memo Directives"] += (
                                "; LOAN MIN PAYMENT ("
                                + primary_checking_account_name
                                + " -$"
                                + str(
                                    f"{(payment_toward_interest + payment_toward_principal)}"
                                )
                                + ")"
                            )

        md_split = [
            md.strip()
            for md in current_forecast_row_df["Memo Directives"].iat[0].split(";")
            if md.strip()
        ]
        current_forecast_row_df["Memo Directives"] = ("; ".join(md_split)).strip()

        for account_index, account_row in account_set.getAccounts().iterrows():
            relevant_balance = account_set.getAccounts().iloc[account_index, 1]
            col_sel_vec = current_forecast_row_df.columns == account_row.Name
            # current_forecast_row_df.iloc[0, col_sel_vec] = round(relevant_balance,2)
            current_forecast_row_df.iloc[0, col_sel_vec] = relevant_balance

            # account_set.accounts[account_index].balance = round(account_set.accounts[account_index].balance,2)
            account_set.accounts[account_index].balance = account_set.accounts[
                account_index
            ].balance

        # log_in_color(logger, 'white', 'debug', 'after current_forecast_row_df:', self.log_stack_depth)
        # log_in_color(logger, 'white', 'debug', current_forecast_row_df.to_string(), self.log_stack_depth)

        self.log_stack_depth -= 1
        log_in_color(
            logger,
            "white",
            "debug",
            str(current_forecast_row_df.Date.iat[0])
            + " EXIT _executeLoanMinimumPayments",
            self.log_stack_depth,
        )

        return current_forecast_row_df

    # @profile
    def _getMinimumFutureAvailableBalances(
        self, account_set, forecast_df, date_YYYYMMDD
    ):
        """
        Calculates the minimum future available balances for each account starting from the specified date.

        Parameters:
        - account_set: AccountSet object containing account information.
        - forecast_df: DataFrame containing the forecasted financial data.
        - date_YYYYMMDD: String representing the current date in 'YYYYMMDD' format.

        Returns:
        - future_available_balances: Dictionary mapping account names to their minimum future available balances.
        """
        log_in_color(
            logger,
            "cyan",
            "debug",
            str(date_YYYYMMDD) + " ENTER _getMinimumFutureAvailableBalances",
            self.log_stack_depth,
        )
        # Increment log stack depth (if used for logging)
        self.log_stack_depth += 1

        # Convert date string to datetime object for comparison
        current_date = datetime.datetime.strptime(date_YYYYMMDD, "%Y%m%d")

        # Ensure 'Date' column is in datetime format
        # forecast_df['Date_dt'] = pd.to_datetime(forecast_df['Date'], format='%Y%m%d')

        # Filter forecast_df for current and future dates
        current_and_future_forecast_df = forecast_df[
            [
                datetime.datetime.strptime(d, "%Y%m%d") >= current_date
                for d in forecast_df["Date"]
            ]
        ]

        # Get the account information
        accounts_df = account_set.getAccounts()
        future_available_balances = {}

        log_in_color(
            logger,
            "cyan",
            "debug",
            "accounts_df:" + str(accounts_df.to_string()),
            self.log_stack_depth,
        )

        for account_index, account_row in accounts_df.iterrows():
            full_account_name = account_row["Name"]
            account_name = full_account_name.split(":")[0]
            account_type = account_row["Account_Type"].lower()

            if account_type == "checking":
                # Calculate minimum future balance minus minimum required balance
                min_future_balance = current_and_future_forecast_df[account_name].min()
                min_available_balance = min_future_balance - account_row["Min_Balance"]
                future_available_balances[account_name] = min_available_balance

            elif account_type == "credit prev stmt bal":
                # Get indices for previous and current statement balance accounts
                prev_index = account_index
                curr_index = account_index - 1

                # Ensure the current index is valid
                if curr_index < 0:
                    continue

                prev_stmt_account_name = accounts_df.iloc[prev_index]["Name"]
                curr_stmt_account_name = accounts_df.iloc[curr_index]["Name"]

                # Check if both accounts exist in forecast_df columns
                if (
                    prev_stmt_account_name not in forecast_df.columns
                    or curr_stmt_account_name not in forecast_df.columns
                ):
                    continue

                # Sum the balances of previous and current statement balances
                total_credit_balance = (
                    current_and_future_forecast_df[prev_stmt_account_name]
                    + current_and_future_forecast_df[curr_stmt_account_name]
                )

                log_in_color(
                    logger,
                    "cyan",
                    "debug",
                    "total_credit_balance: " + str(total_credit_balance),
                    self.log_stack_depth,
                )

                # Calculate the minimum total credit balance
                min_total_credit_balance = total_credit_balance.min()

                # Calculate available credit
                max_balance = account_row["Max_Balance"]
                min_available_credit = (
                    max_balance - min_total_credit_balance - account_row["Min_Balance"]
                )
                future_available_balances[account_name] = min_available_credit

                log_in_color(
                    logger,
                    "cyan",
                    "debug",
                    "min_available_credit: " + str(min_available_credit),
                    self.log_stack_depth,
                )

        log_in_color(
            logger,
            "cyan",
            "debug",
            "future_available_balances: " + str(future_available_balances),
            self.log_stack_depth,
        )

        # Decrement log stack depth
        self.log_stack_depth -= 1
        log_in_color(
            logger,
            "cyan",
            "debug",
            str(date_YYYYMMDD) + " EXIT _getMinimumFutureAvailableBalances",
            self.log_stack_depth,
        )
        return future_available_balances

    # @profile
    def _sync_account_set_w_forecast_day(self, account_set, forecast_df, date_YYYYMMDD):
        # log_in_color(logger, 'white', 'debug', str(date_YYYYMMDD)+' ENTER _sync_account_set_w_forecast_day', self.log_stack_depth)
        self.log_stack_depth += 1

        # log_in_color(logger, 'cyan', 'debug', 'before account set update:', self.log_stack_depth)
        # log_in_color(logger, 'cyan', 'debug', account_set.getAccounts().to_string(), self.log_stack_depth)

        Accounts_df = account_set.getAccounts()

        # log_in_color(logger, 'cyan', 'debug', 'BEFORE update Accounts_df:', self.log_stack_depth)
        relevant_forecast_day = forecast_df[forecast_df.Date == date_YYYYMMDD]

        # log_in_color(logger, 'cyan', 'debug', 'relevant_forecast_day:', self.log_stack_depth)
        # log_in_color(logger, 'cyan', 'debug', relevant_forecast_day.to_string(), self.log_stack_depth)

        row_sel_vec = forecast_df.Date == date_YYYYMMDD
        try:
            assert sum(row_sel_vec) > 0
        except Exception as e:
            error_msg = "error in _sync_account_set_w_forecast_day\n"
            error_msg += "date_YYYYMMDD: " + date_YYYYMMDD + "\n"
            error_msg += "min date of forecast:" + min(forecast_df.Date) + "\n"
            error_msg += "max date of forecast:" + max(forecast_df.Date) + "\n"
            raise AssertionError(error_msg)

        for account_index in range(1, (1 + Accounts_df.shape[0])):
            account_index = int(account_index)
            # print('account_index: ' + str(account_index))
            relevant_balance = relevant_forecast_day.iat[0, account_index]
            # print('relevant_balance: ' + str(relevant_balance))
            # account_set.accounts[account_index - 1].balance = round(relevant_balance, 2)
            account_set.accounts[account_index - 1].balance = relevant_balance

        # log_in_color(logger, 'cyan', 'debug', 'updated account set:', self.log_stack_depth)
        # log_in_color(logger, 'cyan', 'debug', account_set.getAccounts().to_string(), self.log_stack_depth)

        self.log_stack_depth -= 1
        # log_in_color(logger, 'white', 'debug', str(date_YYYYMMDD)+' EXIT _sync_account_set_w_forecast_day', self.log_stack_depth)
        return account_set

    # @profile
    def _propagate_credit_txn_curr_only(
        self,
        relevant_account_info_df,
        account_deltas_list,
        future_rows_only_df,
        forecast_df,
        account_set_before_p2_plus_txn,
        billing_dates_dict,
        date_string_YYYYMMDD,
        post_txn_row_df,
    ):
        """
        Propagates credit card payments involving only the current statement balance into the future forecast.

        Parameters:
        - relevant_account_info_df: DataFrame with account info for relevant accounts.
        - account_deltas_list: List of account balance changes (deltas).
        - future_rows_only_df: DataFrame with future forecast rows.
        - forecast_df: The original forecast DataFrame.
        - account_set_before_p2_plus_txn: Account set before processing the transaction.
        - billing_dates_dict: Dictionary mapping account names to billing dates.
        - date_string_YYYYMMDD: Current date as a string in 'YYYYMMDD' format.
        - post_txn_row_df: DataFrame with the forecast row after transactions.

        Returns:
        - Updated future_rows_only_df DataFrame.
        """
        log_in_color(
            logger,
            "white",
            "debug",
            "ENTER _propagate_credit_txn_curr_only",
            self.log_stack_depth,
        )
        self.log_stack_depth += 1

        # Extract relevant account names
        checking_account_name = (
            account_set_before_p2_plus_txn.getPrimaryCheckingAccountName()
        )
        curr_stmt_bal_account_name = relevant_account_info_df[
            relevant_account_info_df.Account_Type == "credit curr stmt bal"
        ].Name.iat[0]
        credit_basename = curr_stmt_bal_account_name.split(":")[0]
        prev_stmt_bal_account_name = credit_basename + ": Prev Stmt Bal"
        eopc_account_name = credit_basename + ": Credit End of Prev Cycle Bal"
        # billing_cycle_payment_account_name = relevant_account_info_df[
        #     relevant_account_info_df.Account_Type == 'credit billing cycle payment bal'].Name.iat[0]

        # Get billing dates and next billing date
        cc_billing_dates = billing_dates_dict[prev_stmt_bal_account_name]
        future_billing_dates = [
            int(d) for d in cc_billing_dates if int(d) > int(date_string_YYYYMMDD)
        ]
        if future_billing_dates:
            next_billing_date = str(min(future_billing_dates))
            date_after_next_billing_date_YYYYMMDD = (
                datetime.datetime.strptime(next_billing_date, "%Y%m%d")
                + datetime.timedelta(days=1)
            ).strftime("%Y%m%d")
        else:
            next_billing_date = None
            date_after_next_billing_date_YYYYMMDD = "never match"

        # Get account indices in forecast_df
        checking_account_index = forecast_df.columns.get_loc(checking_account_name)
        curr_stmt_bal_account_index = forecast_df.columns.get_loc(
            curr_stmt_bal_account_name
        )
        prev_stmt_bal_account_index = forecast_df.columns.get_loc(
            prev_stmt_bal_account_name
        )
        eopc_account_index = forecast_df.columns.get_loc(eopc_account_name)

        # Get account deltas
        previous_stmt_delta = 0
        curr_stmt_delta = account_deltas_list[curr_stmt_bal_account_index - 1]
        checking_delta = 0
        eopc_delta = 0

        og_curr_stmt_delta = curr_stmt_delta

        # # Initialize previous previous statement balance (used in future billing dates)
        # previous_prev_stmt_bal = 0

        # Iterate over future forecast rows
        for f_i, f_row in future_rows_only_df.iterrows():
            row_df = pd.DataFrame(f_row).T
            date_iat = f_row["Date"]
            md_to_keep = []
            if date_iat == next_billing_date:
                # Handle next billing date

                # Move current statement delta to previous
                previous_stmt_delta += curr_stmt_delta
                curr_stmt_delta = 0

                # Update memo directives
                # md_to_keep.extend(filter(None, [new_check_memo, new_curr_memo, new_prev_memo, og_interest_memo]))

                #
            elif (
                date_iat == date_after_next_billing_date_YYYYMMDD
            ):  # day after ext billing date
                eopc_delta = og_curr_stmt_delta

            elif date_iat in cc_billing_dates:  # todo update this branch
                # Handle other billing dates

                # Ensure we have a valid previous_prev_stmt_bal
                if f_row[eopc_account_name] == 0:
                    continue  # Skip if we don't have previous balance

                # Initialize memo variables
                og_prev_memo = ""
                og_curr_memo = ""
                og_check_memo = ""
                og_interest_memo = ""
                og_prev_amount = 0.0
                og_curr_amount = 0.0
                og_check_amount = 0.0
                og_interest_amount = 0.0
                og_min_payment_amount = 0.0

                # Parse memo directives
                for md in f_row["Memo Directives"].split(";"):
                    md = md.strip()
                    if not md:
                        continue

                    if f"CC MIN PAYMENT ({prev_stmt_bal_account_name}" in md:
                        og_prev_memo = md
                        og_prev_amount = self._parse_memo_amount(md)
                        og_min_payment_amount += og_prev_amount
                    elif f"CC MIN PAYMENT ({curr_stmt_bal_account_name}" in md:
                        og_curr_memo = md
                        og_curr_amount = self._parse_memo_amount(md)
                        og_min_payment_amount += og_curr_amount
                    elif f"CC MIN PAYMENT ({checking_account_name}" in md:
                        og_check_memo = md
                        og_check_amount = self._parse_memo_amount(md)
                    elif f"CC INTEREST ({prev_stmt_bal_account_name}" in md:
                        og_interest_memo = md
                        og_interest_amount = self._parse_memo_amount(md)
                    else:
                        md_to_keep.append(md)

                # Get account row for APR
                account_row = account_set_before_p2_plus_txn.getAccounts().loc[
                    account_set_before_p2_plus_txn.getAccounts().Name
                    == prev_stmt_bal_account_name
                ]

                # Compute interest and current due
                apr = account_row.APR.iat[0]
                # interest_to_be_charged = round(previous_prev_stmt_bal * (apr / 12), 2)
                interest_to_be_charged = f_row[eopc_account_name] * (apr / 12)
                principal_due = f_row[eopc_account_name] * 0.01
                current_due = principal_due + interest_to_be_charged

                # Adjusted payment amounts
                curr_prev_stmt_bal = f_row[
                    prev_stmt_bal_account_name
                ]  # Should we adjust for interest?

                new_min_payment_amount = max(min(40, current_due), curr_prev_stmt_bal)

                current_prev_stmt_balance = row_df[prev_stmt_bal_account_name].iat[0]
                current_curr_stmt_balance = row_df[curr_stmt_bal_account_name].iat[0]

                # blindly copied from gpt
                new_min_payment_amount = (
                    current_due
                    if current_due > 0
                    and current_due > account_row.Minimum_Payment.iat[0]
                    else (
                        (
                            account_row.Minimum_Payment.iat[0]
                            if (current_prev_stmt_balance + current_curr_stmt_balance)
                            > account_row.Minimum_Payment.iat[0]
                            else (current_prev_stmt_balance + current_curr_stmt_balance)
                        )
                        if current_due > 0
                        else 0
                    )
                )

                # adjusted_payment_amount = round(og_min_payment_amount - new_min_payment_amount, 2)
                adjusted_payment_amount = og_min_payment_amount - new_min_payment_amount
                log_in_color(
                    logger,
                    "cyan",
                    "debug",
                    str(date_iat)
                    + " adjusted_payment_amount: "
                    + str(adjusted_payment_amount),
                    self.log_stack_depth,
                )

                previous_stmt_delta += adjusted_payment_amount
                checking_delta += adjusted_payment_amount
                interest_delta = interest_to_be_charged - og_interest_amount
                # previous_stmt_delta += round(interest_delta, 2)
                previous_stmt_delta += interest_delta
                billing_cycle_payment_delta = 0  # redundant but cant hurt

                # Adjust memos
                log_in_color(logger, "white", "debug", "(case 1) _update_memo_amount")
                new_check_memo = self._update_memo_amount(
                    og_check_memo, og_check_amount - adjusted_payment_amount
                )
                if adjusted_payment_amount >= curr_prev_stmt_bal:
                    # Adjust curr and prev memos
                    if og_curr_amount > 0:
                        log_in_color(
                            logger, "white", "debug", "(case 2) _update_memo_amount"
                        )
                        new_curr_memo = self._update_memo_amount(
                            og_curr_memo, adjusted_payment_amount - curr_prev_stmt_bal
                        )
                    if og_prev_amount > 0:
                        log_in_color(
                            logger, "white", "debug", "(case 3) _update_memo_amount"
                        )
                        new_prev_memo = self._update_memo_amount(
                            og_prev_memo, curr_prev_stmt_bal
                        )
                else:
                    if og_curr_amount > 0:
                        log_in_color(
                            logger, "white", "debug", "(case 4) _update_memo_amount"
                        )
                        new_curr_memo = self._update_memo_amount(og_curr_memo, 0.00)
                    if og_prev_amount > 0:
                        log_in_color(
                            logger, "white", "debug", "(case 5) _update_memo_amount"
                        )
                        new_prev_memo = self._update_memo_amount(
                            og_prev_memo, adjusted_payment_amount
                        )
                log_in_color(logger, "white", "debug", "(case 6) _update_memo_amount")
                new_interest_memo = self._update_memo_amount(
                    og_interest_memo, interest_to_be_charged
                )

                log_in_color(
                    logger,
                    "cyan",
                    "debug",
                    str(date_iat)
                    + " updated check memo: "
                    + str(og_check_memo)
                    + " -> "
                    + str(new_check_memo),
                    self.log_stack_depth,
                )
                log_in_color(
                    logger,
                    "cyan",
                    "debug",
                    str(date_iat)
                    + " updated curr memo: "
                    + str(og_curr_memo)
                    + " -> "
                    + str(new_curr_memo),
                    self.log_stack_depth,
                )
                log_in_color(
                    logger,
                    "cyan",
                    "debug",
                    str(date_iat)
                    + " updated prev memo: "
                    + str(og_prev_memo)
                    + " -> "
                    + str(new_prev_memo),
                    self.log_stack_depth,
                )

                # Update memo directives
                md_to_keep.extend(
                    [new_check_memo, new_curr_memo, new_prev_memo, new_interest_memo]
                )

                # Update previous_prev_stmt_bal
                previous_prev_stmt_bal = (
                    future_rows_only_df.at[f_i, prev_stmt_bal_account_name]
                    + previous_stmt_delta
                )

            elif False:  # day after non-next billing date
                pass  # todo update eopc_delta
            else:
                # No adjustments needed
                pass

            # Update balances
            future_rows_only_df.at[f_i, checking_account_name] += checking_delta
            future_rows_only_df.at[
                f_i, prev_stmt_bal_account_name
            ] += previous_stmt_delta
            future_rows_only_df.at[f_i, curr_stmt_bal_account_name] += curr_stmt_delta
            future_rows_only_df.at[f_i, eopc_account_name] += eopc_delta

            # Clean and update memo directives
            if md_to_keep != []:
                # Clean and update memo directives
                md_to_keep = [" " + md for md in md_to_keep if md]
                future_rows_only_df.at[f_i, "Memo Directives"] = ";".join(
                    md_to_keep
                ).strip()

        self.log_stack_depth -= 1
        log_in_color(
            logger,
            "white",
            "debug",
            "EXIT _propagate_credit_txn_curr_only",
            self.log_stack_depth,
        )
        return future_rows_only_df

    # affects checking as well
    # @profile
    def _propagate_credit_payment_curr_only(
        self,
        relevant_account_info_df,
        account_deltas_list,
        future_rows_only_df,
        forecast_df,
        account_set_before_p2_plus_txn,
        billing_dates_dict,
        date_string_YYYYMMDD,
        post_txn_row_df,
    ):
        """
        Propagates credit card payments involving only the current statement balance into the future forecast.

        Parameters:
        - relevant_account_info_df: DataFrame with account info for relevant accounts.
        - account_deltas_list: List of account balance changes (deltas).
        - future_rows_only_df: DataFrame with future forecast rows.
        - forecast_df: The original forecast DataFrame.
        - account_set_before_p2_plus_txn: Account set before processing the transaction.
        - billing_dates_dict: Dictionary mapping account names to billing dates.
        - date_string_YYYYMMDD: Current date as a string in 'YYYYMMDD' format.
        - post_txn_row_df: DataFrame with the forecast row after transactions.

        Returns:
        - Updated future_rows_only_df DataFrame.
        """
        log_in_color(
            logger,
            "white",
            "debug",
            "ENTER _propagate_credit_payment_curr_only",
            self.log_stack_depth,
        )
        self.log_stack_depth += 1

        # Extract relevant account names
        checking_account_name = relevant_account_info_df[
            relevant_account_info_df.Account_Type == "checking"
        ].Name.iat[0]
        curr_stmt_bal_account_name = relevant_account_info_df[
            relevant_account_info_df.Account_Type == "credit curr stmt bal"
        ].Name.iat[0]
        current_cycle_payment_account_name = relevant_account_info_df[
            relevant_account_info_df.Account_Type == "credit billing cycle payment bal"
        ].Name.iat[0]

        credit_basename = curr_stmt_bal_account_name.split(":")[0]
        prev_stmt_bal_account_name = credit_basename + ": Prev Stmt Bal"
        eopc_account_name = credit_basename + ": Credit End of Prev Cycle Bal"

        # Get billing dates and next billing date
        cc_billing_dates = billing_dates_dict[prev_stmt_bal_account_name]
        future_billing_dates = [
            int(d) for d in cc_billing_dates if int(d) > int(date_string_YYYYMMDD)
        ]
        if future_billing_dates:
            next_billing_date = str(min(future_billing_dates))
        else:
            next_billing_date = None

        day_after_billing_dates = [
            (
                datetime.datetime.strptime(str(d), "%Y%m%d")
                + datetime.timedelta(days=1)
            ).strftime("%Y%m%d")
            for d in future_billing_dates
        ]

        # Get account indices in forecast_df
        checking_account_index = forecast_df.columns.get_loc(checking_account_name)
        prev_stmt_bal_account_index = forecast_df.columns.get_loc(
            prev_stmt_bal_account_name
        )
        curr_stmt_bal_account_index = forecast_df.columns.get_loc(
            curr_stmt_bal_account_name
        )
        billing_cycle_payment_account_index = forecast_df.columns.get_loc(
            current_cycle_payment_account_name
        )
        eopc_account_index = forecast_df.columns.get_loc(eopc_account_name)

        previous_prev_stmt_bal = forecast_df[eopc_account_name]

        # Get account deltas
        curr_stmt_delta = account_deltas_list[curr_stmt_bal_account_index - 1]
        checking_delta = account_deltas_list[checking_account_index - 1]
        billing_cycle_payment_delta = account_deltas_list[
            billing_cycle_payment_account_index - 1
        ]
        prev_stmt_delta = 0
        eopc_delta = 0

        # Iterate over future forecast rows
        for f_i, f_row in future_rows_only_df.iterrows():
            date_iat = f_row["Date"]
            md_to_keep = []

            # We need this value before updating other columns
            future_rows_only_df.at[
                f_i, current_cycle_payment_account_name
            ] += billing_cycle_payment_delta

            if date_iat == next_billing_date:
                # At the next billing date, process memo directives

                if date_string_YYYYMMDD == next_billing_date:
                    pass  # payments day of count toward the next cycle
                else:
                    billing_cycle_payment_delta = 0

                    # Move current statement delta to previous
                    prev_stmt_delta += curr_stmt_delta
                    curr_stmt_delta = 0

            elif date_iat in day_after_billing_dates:
                updated_eopc = future_rows_only_df.at[
                    f_i - 1, prev_stmt_bal_account_name
                ]
                old_eopc = future_rows_only_df.at[f_i, eopc_account_name]
                eopc_delta += updated_eopc - old_eopc

            # todo left off here, copy pasted from prev only method
            elif date_iat in cc_billing_dates and previous_prev_stmt_bal != 0:
                # log_in_color(logger, 'white', 'debug', str(date_iat) + ' (Not Next) Billing Date and previous_prev_stmt_bal != 0', self.log_stack_depth)
                # Handle other billing dates after payment has been made

                # Parse memo directives
                for md in f_row["Memo Directives"].split(";"):
                    md = md.strip()
                    if not md:
                        continue

                    og_min_payment_amount = self._parse_memo_amount(md)

                    # log_in_color(logger, 'white', 'debug',
                    #              str(date_iat) + ' Processing md: '+str(md),
                    #              self.log_stack_depth)

                    if f"CC MIN PAYMENT ({prev_stmt_bal_account_name}" in md:

                        # Calculate interest and current due
                        account_row = account_set_before_p2_plus_txn.getAccounts().loc[
                            account_set_before_p2_plus_txn.getAccounts().Name
                            == prev_stmt_bal_account_name
                        ]
                        apr = account_row["APR"].iat[0]
                        # interest_to_be_charged = round(previous_prev_stmt_bal * (apr / 12), 2)
                        interest_to_be_charged = previous_prev_stmt_bal * (apr / 12)
                        principal_due = previous_prev_stmt_bal * 0.01
                        current_due = principal_due + interest_to_be_charged

                        # new_min_payment_amount = round(current_due, 2)
                        new_min_payment_amount = current_due

                        # log_in_color(logger, 'white', 'debug',
                        #              str(date_iat) + ' og_min_payment_amount: ' + str(og_min_payment_amount),
                        #              self.log_stack_depth)
                        #
                        # log_in_color(logger, 'white', 'debug',
                        #              str(date_iat) + ' new_min_payment_amount: ' + str(new_min_payment_amount),
                        #              self.log_stack_depth)

                        # Adjust deltas
                        prev_stmt_delta += (
                            og_min_payment_amount - new_min_payment_amount
                        )
                        checking_delta += og_min_payment_amount - new_min_payment_amount

                        # Update memo directive
                        log_in_color(
                            logger, "white", "debug", "(case 7) _update_memo_amount"
                        )
                        new_md = self._update_memo_amount(md, new_min_payment_amount)
                        md_to_keep.append(new_md)

                        # log_in_color(logger, 'white', 'debug',
                        #              str(date_iat) + ' new md: ' + str(md),
                        #              self.log_stack_depth)

                    elif f"CC INTEREST ({prev_stmt_bal_account_name}" in md:
                        account_row = account_set_before_p2_plus_txn.getAccounts().loc[
                            account_set_before_p2_plus_txn.getAccounts().Name
                            == prev_stmt_bal_account_name
                        ]
                        apr = account_row["APR"].iat[0]
                        # interest_to_be_charged = round(previous_prev_stmt_bal * (apr / 12), 2)
                        interest_to_be_charged = previous_prev_stmt_bal * (apr / 12)

                        og_interest_amount = self._parse_memo_amount(md)

                        # log_in_color(logger, 'white', 'debug', str(date_iat) + ' og_interest_amount: ' + str(og_interest_amount), self.log_stack_depth)
                        # log_in_color(logger, 'white', 'debug', str(date_iat) + ' NEW interest_to_be_charged: ' + str(interest_to_be_charged), self.log_stack_depth)

                        prev_stmt_delta += interest_to_be_charged - og_interest_amount

                        # Update memo directive
                        log_in_color(
                            logger, "white", "debug", "(case 8) _update_memo_amount"
                        )
                        new_md = self._update_memo_amount(md, interest_to_be_charged)
                        md_to_keep.append(new_md)

                        # Move current statement delta to previous
                        prev_stmt_delta += curr_stmt_delta
                        curr_stmt_delta = 0

                        # log_in_color(logger, 'white', 'debug',
                        #              str(date_iat) + ' new md: ' + str(md),
                        #              self.log_stack_depth)

                    elif f"CC MIN PAYMENT ({checking_account_name}" in md:

                        # Calculate interest and current due
                        account_row = account_set_before_p2_plus_txn.getAccounts().loc[
                            account_set_before_p2_plus_txn.getAccounts().Name
                            == prev_stmt_bal_account_name
                        ]
                        apr = account_row["APR"].iat[0]
                        # interest_to_be_charged = round(previous_prev_stmt_bal * (apr / 12), 2)
                        interest_to_be_charged = previous_prev_stmt_bal * (apr / 12)
                        principal_due = previous_prev_stmt_bal * 0.01
                        current_due = principal_due + interest_to_be_charged

                        # new_min_payment_amount = round(current_due, 2)
                        new_min_payment_amount = current_due
                        # log_in_color(logger, 'white', 'debug',
                        #              str(date_iat) + ' new_min_payment_amount: ' + str(new_min_payment_amount),
                        #              self.log_stack_depth)

                        # Update memo directive
                        log_in_color(
                            logger, "white", "debug", "(case 9) _update_memo_amount"
                        )
                        new_md = self._update_memo_amount(md, new_min_payment_amount)
                        md_to_keep.append(new_md)

                        # log_in_color(logger, 'white', 'debug',
                        #              str(date_iat) + ' new md: ' + str(md),
                        #              self.log_stack_depth)

                    else:
                        md_to_keep.append(md)

            # Update balances
            future_rows_only_df.at[f_i, checking_account_name] += checking_delta
            future_rows_only_df.at[f_i, curr_stmt_bal_account_name] += curr_stmt_delta
            # future_rows_only_df.at[f_i, current_cycle_payment_account_name] += billing_cycle_payment_delta
            future_rows_only_df.at[f_i, prev_stmt_bal_account_name] += prev_stmt_delta
            future_rows_only_df.at[f_i, eopc_account_name] += eopc_delta

            # future_rows_only_df.at[f_i, checking_account_name] = round(future_rows_only_df.at[f_i, checking_account_name],2)
            # future_rows_only_df.at[f_i, curr_stmt_bal_account_name] = round(future_rows_only_df.at[f_i, curr_stmt_bal_account_name],2)
            # future_rows_only_df.at[f_i, current_cycle_payment_account_name] = round(future_rows_only_df.at[f_i, current_cycle_payment_account_name],2)
            # future_rows_only_df.at[f_i, prev_stmt_bal_account_name] = round(future_rows_only_df.at[f_i, prev_stmt_bal_account_name],2)
            # future_rows_only_df.at[f_i, eopc_account_name] = round(future_rows_only_df.at[f_i, eopc_account_name],2)

            # previous_prev_stmt_bal = future_rows_only_df.at[f_i, prev_stmt_bal_account_name]

            # Clean and update memo directives
            md_to_keep = [md for md in md_to_keep if md]
            future_rows_only_df.at[f_i, "Memo Directives"] = ";".join(md_to_keep)

            # # Reset deltas for the next iteration
            # checking_delta = 0.0
            # curr_stmt_delta = 0.0
            # previous_stmt_delta = 0.0

        log_in_color(
            logger,
            "white",
            "debug",
            future_rows_only_df.to_string(),
            self.log_stack_depth,
        )

        self.log_stack_depth -= 1
        log_in_color(
            logger,
            "white",
            "debug",
            "EXIT _propagate_credit_payment_curr_only",
            self.log_stack_depth,
        )
        return future_rows_only_df

    # @profile
    def _propagate_credit_payment_prev_only(
        self,
        relevant_account_info_df,
        account_deltas_list,
        future_rows_only_df,
        forecast_df,
        account_set_before_p2_plus_txn,
        billing_dates_dict,
        date_string_YYYYMMDD,
        post_txn_row_df,
    ):
        """
        Propagates credit card payments involving only the previous statement balance into the future forecast.

        Parameters:
        - relevant_account_info_df: DataFrame with account info for relevant accounts.
        - account_deltas_list: List of account balance changes (deltas).
        - future_rows_only_df: DataFrame with future forecast rows.
        - forecast_df: The original forecast DataFrame.
        - account_set_before_p2_plus_txn: Account set before processing the transaction.
        - billing_dates_dict: Dictionary mapping account names to billing dates.
        - date_string_YYYYMMDD: Current date as a string in 'YYYYMMDD' format.
        - post_txn_row_df: DataFrame with the forecast row after transactions.

        Returns:
        - Updated future_rows_only_df DataFrame.
        """
        log_in_color(
            logger,
            "white",
            "debug",
            str(date_string_YYYYMMDD) + " ENTER _propagate_credit_payment_prev_only",
            self.log_stack_depth,
        )
        self.log_stack_depth += 1

        # Extract relevant account names
        checking_account_name = relevant_account_info_df[
            relevant_account_info_df.Account_Type == "checking"
        ].Name.iat[0]
        prev_stmt_bal_account_name = relevant_account_info_df[
            relevant_account_info_df.Account_Type == "credit prev stmt bal"
        ].Name.iat[0]
        bcp_account_name = relevant_account_info_df[
            relevant_account_info_df.Account_Type == "credit billing cycle payment bal"
        ].Name.iat[0]
        credit_basename = prev_stmt_bal_account_name.split(":")[0]
        eopc_account_name = credit_basename + ": Credit End of Prev Cycle Bal"

        # Get billing dates and next billing date
        cc_billing_dates = billing_dates_dict[prev_stmt_bal_account_name]
        future_billing_dates = [
            int(d) for d in cc_billing_dates if int(d) > int(date_string_YYYYMMDD)
        ]
        if future_billing_dates:
            next_billing_date = str(min(future_billing_dates))
        else:
            next_billing_date = None

        day_after_billing_dates = [
            (
                datetime.datetime.strptime(str(d), "%Y%m%d")
                + datetime.timedelta(days=1)
            ).strftime("%Y%m%d")
            for d in future_billing_dates
        ]

        # Get account indices in forecast_df
        checking_account_index = forecast_df.columns.get_loc(checking_account_name)
        prev_stmt_bal_account_index = forecast_df.columns.get_loc(
            prev_stmt_bal_account_name
        )
        bcp_account_index = forecast_df.columns.get_loc(bcp_account_name)

        # Get account deltas
        previous_stmt_delta = account_deltas_list[prev_stmt_bal_account_index - 1]
        checking_delta = previous_stmt_delta
        billing_cycle_payment_delta = account_deltas_list[bcp_account_index - 1]
        eopc_delta = 0

        log_in_color(
            logger,
            "white",
            "debug",
            "relevant_account_info_df...: ",
            self.log_stack_depth,
        )
        log_in_color(
            logger,
            "white",
            "debug",
            relevant_account_info_df.to_string(),
            self.log_stack_depth,
        )
        # relevant_account_info_df
        log_in_color(
            logger,
            "white",
            "debug",
            "previous_stmt_delta........: " + str(previous_stmt_delta),
            self.log_stack_depth,
        )
        log_in_color(
            logger,
            "white",
            "debug",
            "checking_delta.............: " + str(checking_delta),
            self.log_stack_depth,
        )
        log_in_color(
            logger,
            "white",
            "debug",
            "billing_cycle_payment_delta: " + str(billing_cycle_payment_delta),
            self.log_stack_depth,
        )

        # Initialize previous previous statement balance
        previous_prev_stmt_bal = 0.0

        # Iterate over future forecast rows
        for f_i, f_row in future_rows_only_df.iterrows():
            date_iat = f_row["Date"]
            md_to_keep = []

            # We need this value before updating other columns
            future_rows_only_df.at[f_i, bcp_account_name] += billing_cycle_payment_delta

            if f_i == 0:
                previous_prev_stmt_bal = f_row[prev_stmt_bal_account_name]
            else:
                previous_prev_stmt_bal = future_rows_only_df.iloc[
                    f_i - 1, prev_stmt_bal_account_index
                ]
            # log_in_color(logger, 'white', 'debug', str(date_iat)+' previous_prev_stmt_bal: ' + str(previous_prev_stmt_bal), self.log_stack_depth)

            if date_iat == next_billing_date:
                log_in_color(
                    logger,
                    "white",
                    "debug",
                    str(date_iat) + " Next Billing Date",
                    self.log_stack_depth,
                )
                # Handle next billing date (payment due date)

                # Initialize memo variables
                og_check_memo = ""
                og_prev_memo = ""
                og_min_payment_amount = 0.0

                # Parse memo directives
                for md in f_row["Memo Directives"].split(";"):
                    md = md.strip()
                    if not md:
                        continue

                    if f"CC MIN PAYMENT ({prev_stmt_bal_account_name}" in md:
                        og_prev_memo = md
                    elif f"CC MIN PAYMENT ({checking_account_name}" in md:
                        og_check_memo = md
                    else:
                        md_to_keep.append(md)

                # Get advance payment amount
                # advance_payment_amount = self._getTotalPrepaidInCreditCardBillingCycle(
                #     prev_stmt_bal_account_name,
                #     account_set_before_p2_plus_txn,
                #     forecast_df,
                #     date_iat
                # )
                advance_payment_amount = f_row[bcp_account_name]
                log_in_color(
                    logger,
                    "white",
                    "debug",
                    "advance_payment_amount: " + str(advance_payment_amount),
                    self.log_stack_depth,
                )

                # Get minimum payment amount
                og_min_payment_amount = self._parse_memo_amount(og_check_memo)
                log_in_color(
                    logger,
                    "white",
                    "debug",
                    "og_min_payment_amount: " + str(og_min_payment_amount),
                    self.log_stack_depth,
                )

                # Adjust deltas
                payment_to_apply = min(og_min_payment_amount, advance_payment_amount)
                log_in_color(
                    logger,
                    "white",
                    "debug",
                    "payment_to_apply: " + str(og_min_payment_amount),
                    self.log_stack_depth,
                )

                previous_stmt_delta += payment_to_apply
                checking_delta += payment_to_apply

                if date_string_YYYYMMDD == next_billing_date:
                    pass  # payments day of count toward the next cycle
                else:
                    billing_cycle_payment_delta = 0

                # # Update previous_prev_stmt_bal
                # previous_prev_stmt_bal = round(future_rows_only_df.at[f_i, prev_stmt_bal_account_name] + previous_stmt_delta,2)

                # Adjust memo directives
                if advance_payment_amount >= og_min_payment_amount:

                    og_prev_amount = self._parse_memo_amount(og_prev_memo)

                    new_check_memo = (
                        f"CC MIN PAYMENT ALREADY MADE ({checking_account_name} -$0.00)"
                    )
                    new_prev_memo = (
                        f"CC MIN PAYMENT ALREADY MADE ({prev_stmt_bal_account_name} -$0.00)"
                        if og_prev_amount > 0
                        else ""
                    )
                else:
                    remaining_payment = og_min_payment_amount - advance_payment_amount
                    # log_in_color(logger, 'white', 'debug', 'remaining_payment = og_min_payment_amount - advance_payment_amount', self.log_stack_depth)
                    # log_in_color(logger, 'white', 'debug', str(og_min_payment_amount - advance_payment_amount), self.log_stack_depth)
                    log_in_color(
                        logger, "white", "debug", "(case 12) _update_memo_amount"
                    )
                    new_check_memo = self._update_memo_amount(
                        og_check_memo, remaining_payment
                    )
                    log_in_color(
                        logger, "white", "debug", "(case 13) _update_memo_amount"
                    )
                    new_prev_memo = self._update_memo_amount(
                        og_prev_memo, remaining_payment
                    )

                md_to_keep.extend([new_check_memo, new_prev_memo])

            elif date_iat in day_after_billing_dates:
                # print('DAY AFTER BILLING DATE')
                updated_eopc = future_rows_only_df.at[
                    f_i - 1, prev_stmt_bal_account_name
                ]
                old_eopc = future_rows_only_df.at[f_i, eopc_account_name]
                eopc_delta += updated_eopc - old_eopc

            elif date_iat in cc_billing_dates and previous_prev_stmt_bal != 0:
                # log_in_color(logger, 'white', 'debug', str(date_iat) + ' (Not Next) Billing Date and previous_prev_stmt_bal != 0', self.log_stack_depth)
                # Handle other billing dates after payment has been made

                # Parse memo directives
                for md in f_row["Memo Directives"].split(";"):
                    md = md.strip()
                    if not md:
                        continue

                    og_min_payment_amount = self._parse_memo_amount(md)

                    # log_in_color(logger, 'white', 'debug',
                    #              str(date_iat) + ' Processing md: '+str(md),
                    #              self.log_stack_depth)

                    if f"CC MIN PAYMENT ({prev_stmt_bal_account_name}" in md:

                        # Calculate interest and current due
                        account_row = account_set_before_p2_plus_txn.getAccounts().loc[
                            account_set_before_p2_plus_txn.getAccounts().Name
                            == prev_stmt_bal_account_name
                        ]
                        apr = account_row["APR"].iat[0]
                        # interest_to_be_charged = round(previous_prev_stmt_bal * (apr / 12), 2)
                        interest_to_be_charged = previous_prev_stmt_bal * (apr / 12)
                        principal_due = previous_prev_stmt_bal * 0.01
                        current_due = principal_due + interest_to_be_charged

                        # new_min_payment_amount = round(current_due, 2)
                        new_min_payment_amount = current_due

                        # log_in_color(logger, 'white', 'debug',
                        #              str(date_iat) + ' og_min_payment_amount: ' + str(og_min_payment_amount),
                        #              self.log_stack_depth)
                        #
                        # log_in_color(logger, 'white', 'debug',
                        #              str(date_iat) + ' new_min_payment_amount: ' + str(new_min_payment_amount),
                        #              self.log_stack_depth)

                        # Adjust deltas
                        previous_stmt_delta += (
                            og_min_payment_amount - new_min_payment_amount
                        )
                        checking_delta += og_min_payment_amount - new_min_payment_amount

                        # Update memo directive
                        log_in_color(
                            logger, "white", "debug", "(case 14) _update_memo_amount"
                        )
                        new_md = self._update_memo_amount(md, new_min_payment_amount)
                        md_to_keep.append(new_md)

                        # log_in_color(logger, 'white', 'debug',
                        #              str(date_iat) + ' new md: ' + str(md),
                        #              self.log_stack_depth)

                    elif f"CC INTEREST ({prev_stmt_bal_account_name}" in md:
                        account_row = account_set_before_p2_plus_txn.getAccounts().loc[
                            account_set_before_p2_plus_txn.getAccounts().Name
                            == prev_stmt_bal_account_name
                        ]
                        apr = account_row["APR"].iat[0]
                        # interest_to_be_charged = round(previous_prev_stmt_bal * (apr / 12), 2)
                        interest_to_be_charged = previous_prev_stmt_bal * (apr / 12)

                        og_interest_amount = self._parse_memo_amount(md)

                        # log_in_color(logger, 'white', 'debug', str(date_iat) + ' og_interest_amount: ' + str(og_interest_amount), self.log_stack_depth)
                        # log_in_color(logger, 'white', 'debug', str(date_iat) + ' NEW interest_to_be_charged: ' + str(interest_to_be_charged), self.log_stack_depth)

                        previous_stmt_delta += (
                            interest_to_be_charged - og_interest_amount
                        )

                        # Update memo directive
                        log_in_color(
                            logger, "white", "debug", "(case 15) _update_memo_amount"
                        )
                        new_md = self._update_memo_amount(md, interest_to_be_charged)
                        md_to_keep.append(new_md)

                        # log_in_color(logger, 'white', 'debug',
                        #              str(date_iat) + ' new md: ' + str(md),
                        #              self.log_stack_depth)

                    elif f"CC MIN PAYMENT ({checking_account_name}" in md:

                        # Calculate interest and current due
                        account_row = account_set_before_p2_plus_txn.getAccounts().loc[
                            account_set_before_p2_plus_txn.getAccounts().Name
                            == prev_stmt_bal_account_name
                        ]
                        apr = account_row["APR"].iat[0]
                        # interest_to_be_charged = round(previous_prev_stmt_bal * (apr / 12), 2)
                        interest_to_be_charged = previous_prev_stmt_bal * (apr / 12)
                        principal_due = previous_prev_stmt_bal * 0.01
                        current_due = principal_due + interest_to_be_charged

                        # new_min_payment_amount = round(current_due, 2)
                        new_min_payment_amount = current_due
                        # log_in_color(logger, 'white', 'debug',
                        #              str(date_iat) + ' new_min_payment_amount: ' + str(new_min_payment_amount),
                        #              self.log_stack_depth)

                        # Update memo directive
                        log_in_color(
                            logger, "white", "debug", "(case 16) _update_memo_amount"
                        )
                        new_md = self._update_memo_amount(md, new_min_payment_amount)
                        md_to_keep.append(new_md)

                        # log_in_color(logger, 'white', 'debug',
                        #              str(date_iat) + ' new md: ' + str(md),
                        #              self.log_stack_depth)

                    else:
                        md_to_keep.append(md)

                # # Update previous_prev_stmt_bal
                # previous_prev_stmt_bal = round(future_rows_only_df.at[f_i, prev_stmt_bal_account_name] + previous_stmt_delta,2)

            else:
                # No adjustments needed
                pass

            # log_in_color(logger, 'white', 'debug', str(date_iat)+' '+str(prev_stmt_bal_account_name)+' += '+str(previous_stmt_delta), self.log_stack_depth)

            # Update balances
            future_rows_only_df.at[f_i, checking_account_name] += checking_delta
            future_rows_only_df.at[
                f_i, prev_stmt_bal_account_name
            ] += previous_stmt_delta

            future_rows_only_df.at[f_i, eopc_account_name] += eopc_delta

            # log_in_color(logger, 'cyan', 'debug', str(date_iat) + ' ' + checking_account_name + ' = ' + str(future_rows_only_df.at[f_i, checking_account_name]), self.log_stack_depth)
            # log_in_color(logger, 'cyan', 'debug', str(date_iat) + ' ' + prev_stmt_bal_account_name + ' = ' + str(future_rows_only_df.at[f_i, prev_stmt_bal_account_name]), self.log_stack_depth)

            # else no change is needed?
            if md_to_keep != []:
                # Clean and update memo directives
                md_to_keep = [" " + md for md in md_to_keep if md]
                future_rows_only_df.at[f_i, "Memo Directives"] = ";".join(
                    md_to_keep
                ).strip()

        log_in_color(
            logger, "white", "debug", "future_rows_only_df:", self.log_stack_depth
        )
        log_in_color(
            logger,
            "white",
            "debug",
            future_rows_only_df.to_string(),
            self.log_stack_depth,
        )
        self.log_stack_depth -= 1
        log_in_color(
            logger,
            "white",
            "debug",
            str(date_string_YYYYMMDD) + " EXIT _propagate_credit_payment_prev_only",
            self.log_stack_depth,
        )
        return future_rows_only_df

    # @profile
    def _propagate_loan_payment_interest_only(
        self,
        relevant_account_info_df,
        account_deltas_list,
        future_rows_only_df,
        forecast_df,
        account_set_before_p2_plus_txn,
        billing_dates_dict,
        date_string_YYYYMMDD,
        post_txn_row_df,
    ):
        """
        Propagates loan payments involving only the interest into the future forecast.

        Parameters:
        - relevant_account_info_df: DataFrame with account info for relevant accounts.
        - account_deltas_list: List of account balance changes (deltas).
        - future_rows_only_df: DataFrame with future forecast rows.
        - forecast_df: The original forecast DataFrame.
        - account_set_before_p2_plus_txn: Account set before processing the transaction.
        - billing_dates_dict: Dictionary mapping account names to billing dates.
        - date_string_YYYYMMDD: Current date as a string in 'YYYYMMDD' format.
        - post_txn_row_df: DataFrame with the forecast row after transactions.

        Returns:
        - Updated future_rows_only_df DataFrame.
        """
        log_in_color(
            logger,
            "white",
            "debug",
            "ENTER _propagate_loan_payment_interest_only",
            self.log_stack_depth,
        )
        self.log_stack_depth += 1
        # log_in_color(logger, 'cyan', 'debug', 'BEFORE forecast_df', self.log_stack_depth)
        # log_in_color(logger, 'cyan', 'debug', forecast_df.to_string(), self.log_stack_depth)

        # Extract relevant account names
        checking_account_name = relevant_account_info_df[
            relevant_account_info_df.Account_Type == "checking"
        ].Name.iat[0]
        interest_account_name = relevant_account_info_df[
            relevant_account_info_df.Account_Type == "interest"
        ].Name.iat[0]
        # Construct the principal balance account name based on the interest account name
        pbal_account_name = interest_account_name.split(":")[0] + ": Principal Balance"
        billing_cycle_payment_balance_account_name = (
            interest_account_name.split(":")[0] + ": Loan Billing Cycle Payment Bal"
        )

        # Get the APR for the principal balance account
        pbal_sel = (
            account_set_before_p2_plus_txn.getAccounts()["Name"] == pbal_account_name
        )
        pbal_row_df = account_set_before_p2_plus_txn.getAccounts()[pbal_sel]
        apr = pbal_row_df["APR"].iat[0]

        # Get billing dates and next billing date
        loan_billing_dates = billing_dates_dict[pbal_account_name]
        future_billing_dates = [
            int(d) for d in loan_billing_dates if int(d) > int(date_string_YYYYMMDD)
        ]
        if future_billing_dates:
            next_billing_date = str(min(future_billing_dates))
        else:
            next_billing_date = None

        # Get account indices in forecast_df
        checking_account_index = forecast_df.columns.get_loc(checking_account_name)
        interest_account_index = forecast_df.columns.get_loc(interest_account_name)
        pbal_account_index = forecast_df.columns.get_loc(pbal_account_name)
        billing_cycle_payment_balance_index = forecast_df.columns.get_loc(
            billing_cycle_payment_balance_account_name
        )

        # Get account deltas
        interest_delta = account_deltas_list[interest_account_index - 1]
        checking_delta = interest_delta  # Since only interest is involved
        billing_cycle_payment_delta = -1 * interest_delta

        # print('account_deltas_list: '+str(account_deltas_list))

        # Iterate over future forecast rows
        for f_i, f_row in future_rows_only_df.iterrows():
            date_iat = f_row["Date"]
            md_to_keep = []

            # print('Check to reset cycle payment balance')
            # print('date_string_YYYYMMDD: ' + str(date_string_YYYYMMDD))
            # print('date_iat: ' + str(date_iat))
            # print('next_billing_date: ' + str(next_billing_date))
            if date_iat == next_billing_date:
                # Handle next billing date (payment due date)

                if date_string_YYYYMMDD == next_billing_date:
                    pass  # if the additional payment was made day of, it counts towards the next cycle, so we would not reset it
                else:
                    billing_cycle_payment_delta = 0

                # Initialize amounts
                interest_amount = 0.0

                # Parse memo directives
                for md in f_row["Memo Directives"].split(";"):
                    md = md.strip()
                    if not md:
                        continue

                    if f"LOAN MIN PAYMENT ({interest_account_name}" in md:
                        interest_amount = self._parse_memo_amount(md)
                        interest_delta += interest_amount
                        checking_delta += interest_amount
                    else:
                        md_to_keep.append(md)

                # Remove the checking memo directive
                # checking_memo_to_delete = f'LOAN MIN PAYMENT ({checking_account_name} -${interest_amount:.2f})'
                checking_memo_to_delete = (
                    f"LOAN MIN PAYMENT ({checking_account_name} -${interest_amount})"
                )
                md_to_keep = [md for md in md_to_keep if md != checking_memo_to_delete]

            elif date_iat in loan_billing_dates:
                # Handle other billing dates

                # Initialize variables
                interest_paid_amount = 0.0
                og_interest_md = ""

                # Parse memo directives
                for md in f_row["Memo Directives"].split(";"):
                    md = md.strip()
                    if not md:
                        continue

                    if f"LOAN MIN PAYMENT ({interest_account_name}" in md:
                        interest_paid_amount = self._parse_memo_amount(md)
                        og_interest_md = md
                    else:
                        md_to_keep.append(md)

                # Get interest balance at the time of charge
                interest_balance = future_rows_only_df.at[f_i, interest_account_name]

                # Adjust interest memo
                if interest_balance <= interest_paid_amount:
                    new_interest_amount = interest_balance
                    og_interest_surplus = interest_paid_amount - interest_balance
                    log_in_color(
                        logger, "white", "debug", "(case 17) _update_memo_amount"
                    )
                    new_interest_md = self._update_memo_amount(
                        og_interest_md, new_interest_amount
                    )
                    # new_checking_interest_md = f'LOAN MIN PAYMENT ({checking_account_name} -${new_interest_amount:.2f})'
                    new_checking_interest_md = f"LOAN MIN PAYMENT ({checking_account_name} -${new_interest_amount})"
                else:
                    new_interest_amount = interest_paid_amount
                    og_interest_surplus = 0.0
                    new_interest_md = og_interest_md
                    # new_checking_interest_md = f'LOAN MIN PAYMENT ({checking_account_name} -${new_interest_amount:.2f})'
                    new_checking_interest_md = f"LOAN MIN PAYMENT ({checking_account_name} -${new_interest_amount})"

                # Update memo directives
                md_to_keep.extend([new_interest_md, new_checking_interest_md])

                # Adjust deltas
                checking_delta += og_interest_surplus
                interest_delta += og_interest_surplus
                billing_cycle_payment_delta = 0  # redundant but cant hurt

            else:
                # No adjustments needed for other dates
                pass

            # Apply daily interest accrual
            if int(date_iat) >= int(min(loan_billing_dates)):
                if f_i == 0:
                    # Set interest to the value after the transaction

                    # this is the OG line, but I think this keeps the OG index so this fails
                    # future_rows_only_df.at[f_i, interest_account_name] = post_txn_row_df.at[0, interest_account_name]
                    # instead of reindexing (bc expensive) lets try this:
                    future_rows_only_df.at[f_i, interest_account_name] = (
                        post_txn_row_df.head(1)[interest_account_name].iat[0]
                    )
                else:
                    # Set interest equal to the previous day's interest
                    future_rows_only_df.at[f_i, interest_account_name] = (
                        future_rows_only_df.at[f_i - 1, interest_account_name]
                    )

                # Calculate interest accrued on this day
                pbal_balance = future_rows_only_df.at[f_i, pbal_account_name]
                interest_accrued = pbal_balance * (apr / 365.25)

                future_rows_only_df.at[f_i, interest_account_name] += interest_accrued
                # future_rows_only_df.at[f_i, interest_account_name] = round(future_rows_only_df.at[f_i, interest_account_name],2)
                future_rows_only_df.at[f_i, interest_account_name] = (
                    future_rows_only_df.at[f_i, interest_account_name]
                )

                interest_delta = 0.0  # Reset interest delta to prevent accumulation

            # Update balances
            future_rows_only_df.at[f_i, checking_account_name] += checking_delta

            # print(str(date_iat)+' SET '+str(billing_cycle_payment_balance_account_name)+' += '+str(billing_cycle_payment_delta)+' = '+str(future_rows_only_df.at[f_i, billing_cycle_payment_balance_account_name] + billing_cycle_payment_delta))
            future_rows_only_df.at[
                f_i, billing_cycle_payment_balance_account_name
            ] += billing_cycle_payment_delta

            # Clean and update memo directives
            md_to_keep = [md for md in md_to_keep if md]
            future_rows_only_df.at[f_i, "Memo Directives"] = ";".join(md_to_keep)

        # log_in_color(logger, 'cyan', 'debug', 'future_rows_only_df', self.log_stack_depth)
        # log_in_color(logger, 'cyan', 'debug', future_rows_only_df.to_string(), self.log_stack_depth)
        self.log_stack_depth -= 1
        log_in_color(
            logger,
            "white",
            "debug",
            "EXIT _propagate_loan_payment_interest_only",
            self.log_stack_depth,
        )
        return future_rows_only_df

    # @profile
    def _propagate_loan_payment_pbal_only(
        self,
        relevant_account_info_df,
        account_deltas_list,
        future_rows_only_df,
        forecast_df,
        account_set_before_p2_plus_txn,
        billing_dates_dict,
        date_string_YYYYMMDD,
        post_txn_row_df,
    ):
        """
        Propagates loan payments involving only the principal balance into the future forecast.

        Parameters:
        - relevant_account_info_df: DataFrame with account info for relevant accounts.
        - account_deltas_list: List of account balance changes (deltas).
        - future_rows_only_df: DataFrame with future forecast rows.
        - forecast_df: The original forecast DataFrame.
        - account_set_before_p2_plus_txn: Account set before processing the transaction.
        - billing_dates_dict: Dictionary mapping account names to billing dates.
        - date_string_YYYYMMDD: Current date as a string in 'YYYYMMDD' format.
        - post_txn_row_df: DataFrame with the forecast row after transactions.

        Returns:
        - Updated future_rows_only_df DataFrame.
        """
        log_in_color(
            logger,
            "cyan",
            "debug",
            "ENTER _propagate_loan_payment_pbal_only",
            self.log_stack_depth,
        )
        self.log_stack_depth += 1

        # Extract relevant account names
        checking_account_name = relevant_account_info_df[
            relevant_account_info_df.Account_Type == "checking"
        ].Name.iat[0]
        pbal_account_name = relevant_account_info_df[
            relevant_account_info_df.Account_Type == "principal balance"
        ].Name.iat[0]
        # Construct the interest account name based on the principal balance account name
        interest_account_name = pbal_account_name.split(":")[0] + ": Interest"
        billing_cycle_payment_account_name = (
            pbal_account_name.split(":")[0] + ": Loan Billing Cycle Payment Bal"
        )

        # Get the APR for the principal balance account
        pbal_sel = (
            account_set_before_p2_plus_txn.getAccounts()["Name"] == pbal_account_name
        )
        pbal_row_df = account_set_before_p2_plus_txn.getAccounts()[pbal_sel]
        apr = pbal_row_df["APR"].iat[0]

        # Get billing dates and next billing date
        loan_billing_dates = billing_dates_dict[pbal_account_name]
        future_billing_dates = [
            int(d) for d in loan_billing_dates if int(d) > int(date_string_YYYYMMDD)
        ]
        if future_billing_dates:
            next_billing_date = str(min(future_billing_dates))
        else:
            next_billing_date = None

        # Get account indices in forecast_df
        checking_account_index = forecast_df.columns.get_loc(checking_account_name)
        pbal_account_index = forecast_df.columns.get_loc(pbal_account_name)
        interest_account_index = forecast_df.columns.get_loc(interest_account_name)
        billing_cycle_payment_account_index = forecast_df.columns.get_loc(
            billing_cycle_payment_account_name
        )

        # Get account deltas
        pbal_delta = account_deltas_list[pbal_account_index - 1]
        checking_delta = pbal_delta  # Since only principal balance is involved
        billing_cycle_payment_delta = -1 * pbal_delta

        # Iterate over future forecast rows
        for f_i, f_row in future_rows_only_df.iterrows():
            date_iat = f_row["Date"]
            md_to_keep = []

            if date_iat == next_billing_date:
                # Handle next billing date (payment due date)

                # Initialize amounts
                pbal_amount = 0.0

                if date_string_YYYYMMDD == next_billing_date:
                    pass  # it would count toward next billing cycle
                else:
                    billing_cycle_payment_delta = 0

                # Parse memo directives
                for md in f_row["Memo Directives"].split(";"):
                    md = md.strip()
                    if not md:
                        continue

                    if f"LOAN MIN PAYMENT ({pbal_account_name}" in md:
                        pbal_amount = self._parse_memo_amount(md)
                        pbal_delta += pbal_amount
                        checking_delta += pbal_amount
                    else:
                        md_to_keep.append(md)

                # Remove the checking memo directive
                # checking_memo_to_delete = f'LOAN MIN PAYMENT ({checking_account_name} -${pbal_amount:.2f})'
                checking_memo_to_delete = (
                    f"LOAN MIN PAYMENT ({checking_account_name} -${pbal_amount})"
                )
                md_to_keep = [md for md in md_to_keep if md != checking_memo_to_delete]

            elif date_iat in loan_billing_dates:
                # Handle other billing dates

                # Initialize variables
                pbal_paid_amount = 0.0
                og_pbal_md = ""

                # Parse memo directives
                for md in f_row["Memo Directives"].split(";"):
                    md = md.strip()
                    if not md:
                        continue

                    if f"LOAN MIN PAYMENT ({pbal_account_name}" in md:
                        pbal_paid_amount = self._parse_memo_amount(md)
                        og_pbal_md = md
                    else:
                        md_to_keep.append(md)

                # Get balance at the time of charge
                pbal_balance = future_rows_only_df.at[f_i, pbal_account_name]
                billing_cycle_payment_delta = 0

                # Adjust principal balance memo
                if pbal_balance <= pbal_paid_amount:
                    new_pbal_amount = pbal_balance
                    og_pbal_surplus = pbal_paid_amount - pbal_balance
                    final_recredit_checking = og_pbal_surplus
                    # new_pbal_md = f'LOAN MIN PAYMENT ({pbal_account_name} -${new_pbal_amount:.2f})'
                    new_pbal_md = (
                        f"LOAN MIN PAYMENT ({pbal_account_name} -${new_pbal_amount})"
                    )
                    # new_checking_pbal_md = f'LOAN MIN PAYMENT ({checking_account_name} -${new_pbal_amount:.2f})'
                    new_checking_pbal_md = f"LOAN MIN PAYMENT ({checking_account_name} -${new_pbal_amount})"
                else:
                    new_pbal_amount = pbal_paid_amount
                    og_pbal_surplus = 0.0
                    final_recredit_checking = 0.0
                    new_pbal_md = og_pbal_md
                    # new_checking_pbal_md = f'LOAN MIN PAYMENT ({checking_account_name} -${new_pbal_amount:.2f})'
                    new_checking_pbal_md = f"LOAN MIN PAYMENT ({checking_account_name} -${new_pbal_amount})"

                # Update memo directives
                md_to_keep.extend([new_pbal_md, new_checking_pbal_md])

                # Adjust deltas
                checking_delta += final_recredit_checking
                pbal_delta += og_pbal_surplus

            else:
                # No adjustments needed for other dates
                pass

            # Update balances
            future_rows_only_df.at[f_i, checking_account_name] += checking_delta
            future_rows_only_df.at[f_i, pbal_account_name] += pbal_delta
            future_rows_only_df.at[
                f_i, billing_cycle_payment_account_name
            ] += billing_cycle_payment_delta

            # Apply daily interest accrual
            if int(date_iat) >= int(min(loan_billing_dates)):
                if f_i == 0:
                    # Set interest to the value after the transaction
                    future_rows_only_df.at[f_i, interest_account_name] = (
                        post_txn_row_df.at[0, interest_account_name]
                    )
                else:
                    # Set interest equal to the previous day's interest
                    future_rows_only_df.at[f_i, interest_account_name] = (
                        future_rows_only_df.at[f_i - 1, interest_account_name]
                    )

                # Calculate interest accrued on this day
                pbal_balance = future_rows_only_df.at[f_i, pbal_account_name]
                interest_accrued = pbal_balance * (apr / 365.25)
                future_rows_only_df.at[f_i, interest_account_name] += interest_accrued

            # Clean and update memo directives
            md_to_keep = [md for md in md_to_keep if md]
            future_rows_only_df.at[f_i, "Memo Directives"] = ";".join(md_to_keep)

        self.log_stack_depth -= 1
        log_in_color(
            logger,
            "cyan",
            "debug",
            "EXIT _propagate_loan_payment_pbal_only",
            self.log_stack_depth,
        )
        return future_rows_only_df

    # @profile
    def _propagate_loan_payment_pbal_interest(
        self,
        relevant_account_info_df,
        account_deltas_list,
        future_rows_only_df,
        forecast_df,
        account_set_before_p2_plus_txn,
        billing_dates_dict,
        date_string_YYYYMMDD,
        post_txn_row_df,
    ):
        """
        Propagates loan payments involving principal balance and interest into the future forecast.

        Parameters:
        - relevant_account_info_df: DataFrame with account info for relevant accounts.
        - account_deltas_list: List of account balance changes (deltas).
        - future_rows_only_df: DataFrame with future forecast rows.
        - forecast_df: The original forecast DataFrame.
        - account_set_before_p2_plus_txn: Account set before processing the transaction.
        - billing_dates_dict: Dictionary mapping account names to billing dates.
        - date_string_YYYYMMDD: Current date as a string in 'YYYYMMDD' format.
        - post_txn_row_df: DataFrame with the forecast row after transactions.

        Returns:
        - Updated future_rows_only_df DataFrame.
        """
        log_in_color(
            logger,
            "cyan",
            "debug",
            "ENTER _propagate_loan_payment_pbal_interest",
            self.log_stack_depth,
        )
        self.log_stack_depth += 1

        log_in_color(
            logger, "white", "debug", "future_rows_only_df:", self.log_stack_depth
        )
        log_in_color(
            logger,
            "white",
            "debug",
            future_rows_only_df.to_string(),
            self.log_stack_depth,
        )

        # Extract relevant account names
        checking_account_name = relevant_account_info_df[
            relevant_account_info_df.Account_Type == "checking"
        ].Name.iat[0]
        pbal_account_name = relevant_account_info_df[
            relevant_account_info_df.Account_Type == "principal balance"
        ].Name.iat[0]
        interest_account_name = relevant_account_info_df[
            relevant_account_info_df.Account_Type == "interest"
        ].Name.iat[0]
        billing_cycle_payment_balance_account_name = relevant_account_info_df[
            relevant_account_info_df.Account_Type == "loan billing cycle payment bal"
        ].Name.iat[0]

        # Get the APR for the principal balance account
        pbal_sel = (
            account_set_before_p2_plus_txn.getAccounts()["Name"] == pbal_account_name
        )
        pbal_row_df = account_set_before_p2_plus_txn.getAccounts()[pbal_sel]
        apr = pbal_row_df["APR"].iat[0]

        # Get billing dates and next billing date
        loan_billing_dates = billing_dates_dict[pbal_account_name]
        future_billing_dates = [
            int(d) for d in loan_billing_dates if int(d) > int(date_string_YYYYMMDD)
        ]
        if future_billing_dates:
            next_billing_date = str(min(future_billing_dates))
        else:
            next_billing_date = None

        # Get account indices in forecast_df
        checking_account_index = forecast_df.columns.get_loc(checking_account_name)
        pbal_account_index = forecast_df.columns.get_loc(pbal_account_name)
        interest_account_index = forecast_df.columns.get_loc(interest_account_name)
        billing_cycle_payment_index = forecast_df.columns.get_loc(
            billing_cycle_payment_balance_account_name
        )

        # Get account deltas
        # pbal_delta = round(account_deltas_list[pbal_account_index - 1],2)
        # interest_delta = round(account_deltas_list[interest_account_index - 1],2)
        # checking_delta = round(pbal_delta + interest_delta,2)
        # billing_cycle_payment_delta = round(account_deltas_list[billing_cycle_payment_index - 1],2)

        pbal_delta = account_deltas_list[pbal_account_index - 1]
        interest_delta = account_deltas_list[interest_account_index - 1]

        # if multiple payments were made at the same time, this would cause double dip
        # checking_delta = account_deltas_list[checking_account_index - 1]
        checking_delta = pbal_delta + interest_delta

        billing_cycle_payment_delta = account_deltas_list[
            billing_cycle_payment_index - 1
        ]

        # print('account_deltas_list:'+str(account_deltas_list))

        # print('pbal_delta:' + str(pbal_delta))
        # print('billing_cycle_payment_delta:'+str(billing_cycle_payment_delta))
        # print('forecast_df:')
        # print(forecast_df.to_string())

        # Iterate over future forecast rows
        for f_i, f_row in future_rows_only_df.iterrows():

            print(pd.DataFrame(f_row).T.to_string())

            date_iat = f_row["Date"]
            md_to_keep = []

            if date_iat == next_billing_date:
                # Handle next billing date (payment due date)

                # Initialize amounts
                pbal_amount = 0.0
                interest_amount = 0.0

                # Parse memo directives
                for md in f_row["Memo Directives"].split(";"):
                    md = md.strip()
                    if not md:
                        continue

                    if f"LOAN MIN PAYMENT ({pbal_account_name}" in md:
                        pbal_amount = self._parse_memo_amount(md)
                        pbal_delta += pbal_amount
                        checking_delta += pbal_amount
                    elif f"LOAN MIN PAYMENT ({interest_account_name}" in md:
                        interest_amount = self._parse_memo_amount(md)
                        interest_delta += interest_amount
                        checking_delta += interest_amount
                    else:
                        md_to_keep.append(md)

                if date_string_YYYYMMDD == next_billing_date:
                    pass  # payments day of count toward the next cycle
                else:
                    billing_cycle_payment_delta = 0

                # Remove the checking memo directive
                total_payment = pbal_amount + interest_amount
                # checking_memo_to_delete = f'LOAN MIN PAYMENT ({checking_account_name} -${total_payment:.2f})'
                checking_memo_to_delete = (
                    f"LOAN MIN PAYMENT ({checking_account_name} -${total_payment})"
                )
                md_to_keep = [md for md in md_to_keep if md != checking_memo_to_delete]

            elif date_iat in loan_billing_dates:
                # Handle other billing dates (interest accrual)

                # Initialize variables
                pbal_paid_amount = 0.0
                interest_paid_amount = 0.0
                og_pbal_md = ""
                og_interest_md = ""

                # Parse memo directives
                for md in f_row["Memo Directives"].split(";"):
                    md = md.strip()
                    if not md:
                        continue

                    if f"LOAN MIN PAYMENT ({pbal_account_name}" in md:
                        pbal_paid_amount = self._parse_memo_amount(md)
                        og_pbal_md = md
                    elif f"LOAN MIN PAYMENT ({interest_account_name}" in md:
                        interest_paid_amount = self._parse_memo_amount(md)
                        og_interest_md = md
                    else:
                        md_to_keep.append(md)

                # Get balances at the time of charge
                pbal_balance = future_rows_only_df.at[f_i, pbal_account_name]
                interest_balance = future_rows_only_df.at[f_i, interest_account_name]

                # Adjust interest memo
                if interest_balance <= interest_paid_amount:
                    new_interest_amount = interest_balance
                    og_interest_surplus = interest_paid_amount - interest_balance
                else:
                    new_interest_amount = interest_paid_amount
                    og_interest_surplus = 0.0
                log_in_color(logger, "white", "debug", "(case 18) _update_memo_amount")
                new_interest_md = self._update_memo_amount(
                    og_interest_md, new_interest_amount
                )
                # new_checking_interest_md = f'LOAN MIN PAYMENT ({checking_account_name} -${new_interest_amount:.2f})'
                new_checking_interest_md = f"LOAN MIN PAYMENT ({checking_account_name} -${new_interest_amount})"

                # Adjust principal balance memo
                total_pbal_payment = pbal_paid_amount + og_interest_surplus
                if pbal_balance <= total_pbal_payment:
                    new_pbal_amount = pbal_balance
                    og_pbal_surplus = total_pbal_payment - pbal_balance
                    final_recredit_checking = og_pbal_surplus
                else:
                    new_pbal_amount = total_pbal_payment
                    og_pbal_surplus = 0.0
                    final_recredit_checking = 0.0
                # new_pbal_md = f'LOAN MIN PAYMENT ({pbal_account_name} -${new_pbal_amount:.2f})'
                new_pbal_md = (
                    f"LOAN MIN PAYMENT ({pbal_account_name} -${new_pbal_amount})"
                )
                # new_checking_pbal_md = f'LOAN MIN PAYMENT ({checking_account_name} -${new_pbal_amount:.2f})'
                new_checking_pbal_md = (
                    f"LOAN MIN PAYMENT ({checking_account_name} -${new_pbal_amount})"
                )

                # Update memo directives
                md_to_keep.extend(
                    [
                        new_interest_md,
                        new_pbal_md,
                        new_checking_pbal_md,
                        new_checking_interest_md,
                    ]
                )

                # Adjust deltas
                checking_delta += og_pbal_surplus + og_interest_surplus
                pbal_delta += og_pbal_surplus
                interest_delta += og_interest_surplus
                billing_cycle_payment_delta = 0  # redundant but cant hurt

            else:
                # No adjustments needed for other dates
                pass

            # Update balances
            print(
                str(checking_account_name)
                + " "
                + str(future_rows_only_df.at[f_i, checking_account_name])
                + " += "
                + str(checking_delta)
                + " = "
                + str(
                    future_rows_only_df.at[f_i, checking_account_name] + checking_delta
                )
            )
            future_rows_only_df.at[f_i, checking_account_name] += checking_delta
            future_rows_only_df.at[f_i, pbal_account_name] += pbal_delta
            future_rows_only_df.at[
                f_i, billing_cycle_payment_balance_account_name
            ] += billing_cycle_payment_delta

            # Apply daily interest accrual
            if date_iat >= min(loan_billing_dates):
                if f_i == 0:
                    # Set interest to the value after the transaction
                    # future_rows_only_df.at[f_i, interest_account_name] = post_txn_row_df.at[0, interest_account_name]
                    future_rows_only_df.at[f_i, interest_account_name] = (
                        post_txn_row_df.head(1)[interest_account_name].iat[0]
                    )
                else:
                    # Set interest equal to the previous day's interest
                    future_rows_only_df.at[f_i, interest_account_name] = (
                        future_rows_only_df.at[f_i - 1, interest_account_name]
                    )

                # Calculate interest accrued on this day
                pbal_balance = future_rows_only_df.at[f_i, pbal_account_name]
                interest_accrued = pbal_balance * (apr / 365.25)
                future_rows_only_df.at[f_i, interest_account_name] += interest_accrued
                # future_rows_only_df.at[f_i, interest_account_name] = round(future_rows_only_df.at[f_i, interest_account_name],2)
                interest_delta = 0.0  # Reset interest delta to prevent accumulation

            # Clean and update memo directives
            md_to_keep = [md for md in md_to_keep if md]
            future_rows_only_df.at[f_i, "Memo Directives"] = ";".join(md_to_keep)

        log_in_color(
            logger, "white", "debug", "future_rows_only_df:", self.log_stack_depth
        )
        log_in_color(
            logger,
            "white",
            "debug",
            future_rows_only_df.to_string(),
            self.log_stack_depth,
        )
        self.log_stack_depth -= 1
        log_in_color(
            logger,
            "cyan",
            "debug",
            "EXIT _propagate_loan_payment_pbal_interest",
            self.log_stack_depth,
        )
        return future_rows_only_df

    # @profile
    def _propagate_credit_payment_prev_curr(
        self,
        relevant_account_info_df,
        account_deltas_list,
        future_rows_only_df,
        forecast_df,
        account_set_before_p2_plus_txn,
        billing_dates_dict,
        date_string_YYYYMMDD,
        post_txn_row_df,
    ):
        """
        Propagates credit card payments into the future forecast when both previous and current statement balances are involved.

        Parameters:
        - relevant_account_info_df: DataFrame with account info for relevant accounts.
        - account_deltas_list: List of account balance changes (deltas).
        - future_rows_only_df: DataFrame with future forecast rows.
        - forecast_df: The original forecast DataFrame.
        - account_set_before_p2_plus_txn: Account set before processing the transaction.
        - billing_dates_dict: Dictionary mapping account names to billing dates.
        - date_string_YYYYMMDD: Current date as a string in 'YYYYMMDD' format.
        - post_txn_row_df: DataFrame with the forecast row after transactions.

        Returns:
        - Updated future_rows_only_df DataFrame.
        """
        log_in_color(
            logger,
            "cyan",
            "debug",
            "ENTER _propagate_credit_payment_prev_curr",
            self.log_stack_depth,
        )
        self.log_stack_depth += 1

        # Extract relevant account names
        checking_account_name = relevant_account_info_df[
            relevant_account_info_df.Account_Type == "checking"
        ].Name.iat[0]
        curr_stmt_bal_account_name = relevant_account_info_df[
            relevant_account_info_df.Account_Type == "credit curr stmt bal"
        ].Name.iat[0]
        prev_stmt_bal_account_name = relevant_account_info_df[
            relevant_account_info_df.Account_Type == "credit prev stmt bal"
        ].Name.iat[0]
        billing_cycle_payment_account_name = relevant_account_info_df[
            relevant_account_info_df.Account_Type == "credit billing cycle payment bal"
        ].Name.iat[0]
        credit_basename = prev_stmt_bal_account_name.split(":")[0]
        eopc_account_name = credit_basename + ": Credit End of Prev Cycle Bal"

        # Get billing dates and next billing date
        cc_billing_dates = billing_dates_dict[prev_stmt_bal_account_name]
        future_billing_dates = [
            int(d) for d in cc_billing_dates if int(d) > int(date_string_YYYYMMDD)
        ]
        if future_billing_dates:
            next_billing_date = str(min(future_billing_dates))
        else:
            next_billing_date = None

        day_after_billing_dates = [
            (
                datetime.datetime.strptime(str(d), "%Y%m%d")
                + datetime.timedelta(days=1)
            ).strftime("%Y%m%d")
            for d in future_billing_dates
        ]

        # Get account indices in forecast_df
        checking_account_index = forecast_df.columns.get_loc(checking_account_name)
        prev_stmt_bal_account_index = forecast_df.columns.get_loc(
            prev_stmt_bal_account_name
        )
        curr_stmt_bal_account_index = forecast_df.columns.get_loc(
            curr_stmt_bal_account_name
        )
        billing_cycle_payment_account_index = forecast_df.columns.get_loc(
            billing_cycle_payment_account_name
        )

        # Get account deltas
        previous_stmt_delta = account_deltas_list[prev_stmt_bal_account_index - 1]
        curr_stmt_delta = account_deltas_list[curr_stmt_bal_account_index - 1]
        checking_delta = account_deltas_list[checking_account_index - 1]
        billing_cycle_payment_delta = account_deltas_list[
            billing_cycle_payment_account_index - 1
        ]
        eopc_delta = 0

        # Initialize previous previous statement balance (used in future billing dates)
        previous_prev_stmt_bal = 0

        # Iterate over future forecast rows
        for f_i, f_row in future_rows_only_df.iterrows():
            row_df = pd.DataFrame(f_row).T

            date_iat = f_row["Date"]
            md_to_keep = []

            # We need this value before updating other columns
            future_rows_only_df.at[
                f_i, billing_cycle_payment_account_name
            ] += billing_cycle_payment_delta

            if date_iat == next_billing_date:
                # Handle next billing date

                # Initialize memo variables
                og_prev_memo = ""
                og_curr_memo = ""
                og_check_memo = ""
                og_interest_memo = ""
                og_prev_amount = 0.0
                og_curr_amount = 0.0
                og_check_amount = 0.0

                new_prev_memo = ""
                new_curr_memo = ""
                new_check_memo = ""

                # Parse memo directives
                log_in_color(
                    logger,
                    "cyan",
                    "debug",
                    "Memo Directives: " + str(f_row["Memo Directives"]),
                    self.log_stack_depth,
                )
                for md in f_row["Memo Directives"].split(";"):
                    md = md.strip()
                    if not md:
                        continue

                    if f"CC MIN PAYMENT ({prev_stmt_bal_account_name}" in md:
                        og_prev_memo = md
                        og_prev_amount = self._parse_memo_amount(md)
                    elif f"CC MIN PAYMENT ({curr_stmt_bal_account_name}" in md:
                        og_curr_memo = md
                        og_curr_amount = self._parse_memo_amount(md)
                    elif f"CC MIN PAYMENT ({checking_account_name}" in md:
                        og_check_memo = md
                        og_check_amount = self._parse_memo_amount(md)
                    elif f"CC INTEREST ({prev_stmt_bal_account_name}" in md:
                        og_interest_memo = md
                        og_interest_amount = self._parse_memo_amount(md)
                    else:
                        md_to_keep.append(md)

                # Get advance payment amount
                # advance_payment_amount = self._getTotalPrepaidInCreditCardBillingCycle(
                #     prev_stmt_bal_account_name,
                #     account_set_before_p2_plus_txn,
                #     forecast_df,
                #     date_iat
                # )
                advance_payment_amount = f_row[billing_cycle_payment_account_name]

                min_payment_amount = og_check_amount

                # Adjust deltas
                curr_stmt_delta += og_curr_amount
                previous_stmt_delta += og_prev_amount
                checking_delta += og_prev_amount + og_curr_amount

                if date_string_YYYYMMDD == next_billing_date:
                    pass  # payments day of count toward the next cycle
                else:
                    billing_cycle_payment_delta = 0

                # Apply advance payments
                if advance_payment_amount >= min_payment_amount:
                    # All payments already made
                    new_check_memo = (
                        f"CC MIN PAYMENT ALREADY MADE ({checking_account_name} -$0.00)"
                    )
                    new_prev_memo = (
                        f"CC MIN PAYMENT ALREADY MADE ({prev_stmt_bal_account_name} -$0.00)"
                        if og_prev_amount > 0
                        else ""
                    )
                    new_curr_memo = (
                        f"CC MIN PAYMENT ALREADY MADE ({curr_stmt_bal_account_name} -$0.00)"
                        if og_curr_amount > 0
                        else ""
                    )
                else:
                    remaining_payment = min_payment_amount - advance_payment_amount
                    if advance_payment_amount >= og_prev_amount:
                        # Advance payments cover previous statement balance and some of curr
                        log_in_color(
                            logger, "white", "debug", "(case 19) _update_memo_amount"
                        )
                        new_prev_memo = self._update_memo_amount(
                            og_prev_memo, 0.00
                        )  # todo this is where the error occurred
                        curr_amount_remaining = og_curr_amount - (
                            advance_payment_amount - og_prev_amount
                        )
                        if og_curr_amount > 0:
                            log_in_color(
                                logger,
                                "white",
                                "debug",
                                "(case 20) _update_memo_amount",
                            )
                            new_curr_memo = self._update_memo_amount(
                                og_curr_memo, curr_amount_remaining
                            )
                    else:
                        # Advance payments partially cover previous statement balance and none of curr (which there might not be any)
                        prev_amount_remaining = og_prev_amount - advance_payment_amount
                        log_in_color(
                            logger, "white", "debug", "(case 21) _update_memo_amount"
                        )
                        new_prev_memo = self._update_memo_amount(
                            og_prev_memo, prev_amount_remaining
                        )
                        new_curr_memo = og_curr_memo
                    log_in_color(
                        logger, "white", "debug", "(case 22) _update_memo_amount"
                    )
                    new_check_memo = self._update_memo_amount(
                        og_check_memo, og_check_amount - advance_payment_amount
                    )

                # Move current statement delta to previous
                previous_stmt_delta += curr_stmt_delta
                curr_stmt_delta = 0

                # Update memo directives
                md_to_keep.extend(
                    filter(
                        None,
                        [
                            new_check_memo,
                            new_curr_memo,
                            new_prev_memo,
                            og_interest_memo,
                        ],
                    )
                )

                # Compute previous previous statement balance
                # previous_prev_stmt_bal = round(
                #     future_rows_only_df.at[f_i, prev_stmt_bal_account_name] + previous_stmt_delta, 2
                # )
                previous_prev_stmt_bal = (
                    future_rows_only_df.at[f_i, prev_stmt_bal_account_name]
                    + previous_stmt_delta
                )

            elif date_iat in day_after_billing_dates:
                print("DAY AFTER BILLING DATE")
                updated_eopc = future_rows_only_df.at[
                    f_i - 1, prev_stmt_bal_account_name
                ]
                old_eopc = future_rows_only_df.at[f_i, eopc_account_name]
                print("eopc_delta += " + str(updated_eopc - old_eopc))
                eopc_delta += updated_eopc - old_eopc

            elif date_iat in cc_billing_dates:
                # Handle other billing dates

                # Ensure we have a valid previous_prev_stmt_bal
                if previous_prev_stmt_bal == 0:
                    continue  # Skip if we don't have previous balance

                # Initialize memo variables
                og_prev_memo = ""
                og_curr_memo = ""
                og_check_memo = ""
                og_interest_memo = ""
                og_prev_amount = 0.0
                og_curr_amount = 0.0
                og_check_amount = 0.0
                og_interest_amount = 0.0
                og_min_payment_amount = 0.0

                # Parse memo directives
                for md in f_row["Memo Directives"].split(";"):
                    md = md.strip()
                    if not md:
                        continue

                    if f"CC MIN PAYMENT ({prev_stmt_bal_account_name}" in md:
                        og_prev_memo = md
                        og_prev_amount = self._parse_memo_amount(md)
                        og_min_payment_amount += og_prev_amount
                    elif f"CC MIN PAYMENT ({curr_stmt_bal_account_name}" in md:
                        og_curr_memo = md
                        og_curr_amount = self._parse_memo_amount(md)
                        og_min_payment_amount += og_curr_amount
                    elif f"CC MIN PAYMENT ({checking_account_name}" in md:
                        og_check_memo = md
                        og_check_amount = self._parse_memo_amount(md)
                    elif f"CC INTEREST ({prev_stmt_bal_account_name}" in md:
                        og_interest_memo = md
                        og_interest_amount = self._parse_memo_amount(md)
                    else:
                        md_to_keep.append(md)

                # Get account row for APR
                account_row = account_set_before_p2_plus_txn.getAccounts().loc[
                    account_set_before_p2_plus_txn.getAccounts().Name
                    == prev_stmt_bal_account_name
                ]

                # Compute interest and current due
                apr = account_row.APR.iat[0]
                # interest_to_be_charged = round(previous_prev_stmt_bal * (apr / 12), 2)
                interest_to_be_charged = previous_prev_stmt_bal * (apr / 12)
                principal_due = previous_prev_stmt_bal * 0.01
                current_due = principal_due + interest_to_be_charged

                # Adjusted payment amounts
                curr_prev_stmt_bal = f_row[
                    prev_stmt_bal_account_name
                ]  # Should we adjust for interest?

                new_min_payment_amount = max(min(40, current_due), curr_prev_stmt_bal)

                current_prev_stmt_balance = row_df[prev_stmt_bal_account_name].iat[0]
                current_curr_stmt_balance = row_df[curr_stmt_bal_account_name].iat[0]

                # blindly copied from gpt
                new_min_payment_amount = (
                    current_due
                    if current_due > 0
                    and current_due > account_row.Minimum_Payment.iat[0]
                    else (
                        (
                            account_row.Minimum_Payment.iat[0]
                            if (current_prev_stmt_balance + current_curr_stmt_balance)
                            > account_row.Minimum_Payment.iat[0]
                            else (current_prev_stmt_balance + current_curr_stmt_balance)
                        )
                        if current_due > 0
                        else 0
                    )
                )

                # adjusted_payment_amount = round(og_min_payment_amount - new_min_payment_amount, 2)
                adjusted_payment_amount = og_min_payment_amount - new_min_payment_amount
                log_in_color(
                    logger,
                    "cyan",
                    "debug",
                    str(date_iat)
                    + " adjusted_payment_amount: "
                    + str(adjusted_payment_amount),
                    self.log_stack_depth,
                )

                previous_stmt_delta += adjusted_payment_amount
                checking_delta += adjusted_payment_amount
                interest_delta = interest_to_be_charged - og_interest_amount
                # previous_stmt_delta += round(interest_delta, 2)
                previous_stmt_delta += interest_delta
                billing_cycle_payment_delta = 0  # redundant but cant hurt

                # Adjust memos
                log_in_color(logger, "white", "debug", "(case 23) _update_memo_amount")
                new_check_memo = self._update_memo_amount(
                    og_check_memo, og_check_amount - adjusted_payment_amount
                )
                if adjusted_payment_amount >= curr_prev_stmt_bal:
                    # Adjust curr and prev memos
                    if og_curr_amount > 0:
                        log_in_color(
                            logger, "white", "debug", "(case 24) _update_memo_amount"
                        )
                        new_curr_memo = self._update_memo_amount(
                            og_curr_memo, adjusted_payment_amount - curr_prev_stmt_bal
                        )
                    if og_prev_amount > 0:
                        log_in_color(
                            logger, "white", "debug", "(case 25) _update_memo_amount"
                        )
                        new_prev_memo = self._update_memo_amount(
                            og_prev_memo, curr_prev_stmt_bal
                        )
                else:
                    if og_curr_amount > 0:
                        # this parent logic branch is for cc payments, not cc expenses, therefore
                        # this specific branch should never happen bc adjust payment amount is always less than OG.
                        # if adjusted_payment_amount > curr_prev_stmt_bal, then so was OG, and therefore curr was 0
                        log_in_color(
                            logger, "white", "debug", "(case 26) _update_memo_amount"
                        )
                        new_curr_memo = self._update_memo_amount(og_curr_memo, 0.00)
                    if og_prev_amount > 0:
                        log_in_color(
                            logger, "white", "debug", "(case 27) _update_memo_amount"
                        )
                        new_prev_memo = self._update_memo_amount(
                            og_prev_memo, og_prev_amount - adjusted_payment_amount
                        )
                log_in_color(logger, "white", "debug", "(case 28) _update_memo_amount")
                new_interest_memo = self._update_memo_amount(
                    og_interest_memo, interest_to_be_charged
                )

                log_in_color(
                    logger,
                    "cyan",
                    "debug",
                    str(date_iat)
                    + " updated check memo: "
                    + str(og_check_memo)
                    + " -> "
                    + str(new_check_memo),
                    self.log_stack_depth,
                )
                log_in_color(
                    logger,
                    "cyan",
                    "debug",
                    str(date_iat)
                    + " updated curr memo: "
                    + str(og_curr_memo)
                    + " -> "
                    + str(new_curr_memo),
                    self.log_stack_depth,
                )
                log_in_color(
                    logger,
                    "cyan",
                    "debug",
                    str(date_iat)
                    + " updated prev memo: "
                    + str(og_prev_memo)
                    + " -> "
                    + str(new_prev_memo),
                    self.log_stack_depth,
                )

                # Update memo directives
                md_to_keep.extend(
                    [new_check_memo, new_curr_memo, new_prev_memo, new_interest_memo]
                )

                # Update previous_prev_stmt_bal
                previous_prev_stmt_bal = (
                    future_rows_only_df.at[f_i, prev_stmt_bal_account_name]
                    + previous_stmt_delta
                )

            else:
                # No adjustments needed
                pass

            # Update balances
            future_rows_only_df.at[f_i, checking_account_name] += checking_delta
            future_rows_only_df.at[
                f_i, prev_stmt_bal_account_name
            ] += previous_stmt_delta
            future_rows_only_df.at[f_i, curr_stmt_bal_account_name] += curr_stmt_delta
            # future_rows_only_df.at[f_i, billing_cycle_payment_account_name] += billing_cycle_payment_delta
            future_rows_only_df.at[f_i, eopc_account_name] += eopc_delta

            # future_rows_only_df.at[f_i, checking_account_name] = round(future_rows_only_df.at[f_i, checking_account_name],2)
            # future_rows_only_df.at[f_i, prev_stmt_bal_account_name] = round(future_rows_only_df.at[f_i, prev_stmt_bal_account_name],2)
            # future_rows_only_df.at[f_i, curr_stmt_bal_account_name] = round(future_rows_only_df.at[f_i, curr_stmt_bal_account_name],2)
            # future_rows_only_df.at[f_i, billing_cycle_payment_account_name] = round(future_rows_only_df.at[f_i, billing_cycle_payment_account_name],2)
            # future_rows_only_df.at[f_i, eopc_account_name] = round( future_rows_only_df.at[f_i, eopc_account_name], 2)

            # log_in_color(logger, 'white', 'debug', str(date_iat) + ' ' + str(checking_account_name) + ' += ' + str(checking_delta), self.log_stack_depth)
            # log_in_color(logger, 'white', 'debug', str(date_iat) + ' ' + str(curr_stmt_bal_account_name) + ' += ' + str(curr_stmt_delta), self.log_stack_depth)
            # log_in_color(logger, 'white', 'debug', str(date_iat) + ' ' + str(prev_stmt_bal_account_name) + ' += ' + str(previous_stmt_delta), self.log_stack_depth)
            # log_in_color(logger, 'white', 'debug', str(date_iat) + ' ' + str(billing_cycle_payment_account_name) + ' += ' + str(billing_cycle_payment_delta), self.log_stack_depth)
            log_in_color(
                logger,
                "white",
                "debug",
                str(date_iat) + " " + str(eopc_account_name) + " += " + str(eopc_delta),
                self.log_stack_depth,
            )

            # Clean and update memo directives
            if md_to_keep != []:
                # Clean and update memo directives
                md_to_keep = [" " + md for md in md_to_keep if md]
                future_rows_only_df.at[f_i, "Memo Directives"] = ";".join(
                    md_to_keep
                ).strip()

        self.log_stack_depth -= 1
        log_in_color(
            logger,
            "cyan",
            "debug",
            "EXIT _propagate_credit_payment_prev_curr",
            self.log_stack_depth,
        )
        return future_rows_only_df

    # @profile
    def _parse_memo_amount(self, memo_line):
        """
        Parses a memo line and extracts the amount.
        Returns the amount as a float.
        """
        # log_in_color(logger, 'cyan', 'debug', 'ENTER _parse_memo_amount', self.log_stack_depth)
        self.log_stack_depth += 1

        # log_in_color(logger, 'cyan', 'debug', 'memo_line: '+str(memo_line), self.log_stack_depth)

        matches = re.search("(.*) \\((.*)[-+]{1}\\$(.*)\\)", memo_line)
        memo_amount = matches.group(3)

        # log_in_color(logger, 'cyan', 'debug', 'memo_amount: ' + str(memo_amount), self.log_stack_depth)

        self.log_stack_depth -= 1
        # log_in_color(logger, 'cyan', 'debug', 'EXIT _parse_memo_amount', self.log_stack_depth)
        return float(memo_amount)

    # @profile
    def _update_memo_amount(self, memo_line, new_amount):
        """
        Updates the amount in a memo line with a new amount.
        Returns the updated memo line.
        """
        log_in_color(
            logger, "white", "debug", " ENTER _update_memo_amount", self.log_stack_depth
        )
        self.log_stack_depth += 1

        #  r'(\-$' + f'{new_amount:.2f}' + ')'
        matches = re.search("(.*) \\((.*)[-+]{1}\\$(.*)\\)", memo_line)
        og_amount = matches.group(3)
        # new_memo_line = re.sub(str(og_amount), str(f'{new_amount:.2f}'), str(memo_line))
        new_memo_line = re.sub(str(og_amount), str(f"{new_amount}"), str(memo_line))

        # if memo_line != new_memo_line:
        log_in_color(
            logger,
            "cyan",
            "debug",
            "memo_line: " + str(memo_line),
            self.log_stack_depth,
        )
        log_in_color(
            logger,
            "cyan",
            "debug",
            str(og_amount) + " -> " + str(new_amount),
            self.log_stack_depth,
        )
        log_in_color(
            logger,
            "cyan",
            "debug",
            "new_memo_line: " + str(new_memo_line),
            self.log_stack_depth,
        )

        self.log_stack_depth -= 1
        log_in_color(
            logger, "white", "debug", " EXIT _update_memo_amount", self.log_stack_depth
        )
        return new_memo_line

    # @profile
    def _propagateOptimizationTransactionsIntoTheFuture(
        self, account_set_before_p2_plus_txn, forecast_df, date_string_YYYYMMDD
    ):
        """
        Propagates optimization transactions into the future forecast.

        Parameters:
        - account_set_before_p2_plus_txn: Account set before processing transactions.
        - forecast_df: DataFrame containing the financial forecast.
        - date_string_YYYYMMDD: The current date in 'YYYYMMDD' format.

        Returns:
        - Updated forecast_df with propagated transactions.
        """
        log_in_color(
            logger,
            "white",
            "debug",
            str(date_string_YYYYMMDD)
            + " ENTER _propagateOptimizationTransactionsIntoTheFuture",
            self.log_stack_depth,
        )
        self.log_stack_depth += 1

        account_set_after_p2_plus_txn = self._sync_account_set_w_forecast_day(
            copy.deepcopy(account_set_before_p2_plus_txn),
            forecast_df,
            date_string_YYYYMMDD,
        )

        A_df = account_set_after_p2_plus_txn.getAccounts()
        B_df = account_set_before_p2_plus_txn.getAccounts()

        # Compute account deltas
        account_deltas = A_df["Balance"] - B_df["Balance"]

        # log_in_color(logger, 'cyan', 'debug', 'Before:', self.log_stack_depth)
        # log_in_color(logger, 'cyan', 'debug', B_df.to_string(), self.log_stack_depth)
        #
        # log_in_color(logger, 'cyan', 'debug', 'After:', self.log_stack_depth)
        # log_in_color(logger, 'cyan', 'debug', A_df.to_string(), self.log_stack_depth)
        #
        # log_in_color(logger, 'cyan', 'debug', 'account_deltas:'+str(account_deltas), self.log_stack_depth)

        # Sanity check: For certain account types, deltas should be <= 0
        account_types_to_check = ["checking", "principal balance", "interest"]
        is_account_type = A_df["Account_Type"].isin(account_types_to_check)
        violations = account_deltas[is_account_type] > 0

        if violations.any():
            log_in_color(
                logger,
                "red",
                "error",
                str(account_deltas[violations]),
                self.log_stack_depth,
            )
            raise AssertionError(
                "Account delta positive for checking, principal balance, or interest accounts."
            )

        account_deltas_list = account_deltas.tolist()

        if account_deltas.sum() == 0:
            log_in_color(
                logger,
                "white",
                "debug",
                str(date_string_YYYYMMDD) + " no changes to propagate",
                self.log_stack_depth,
            )
            self.log_stack_depth -= 1
            log_in_color(
                logger,
                "white",
                "debug",
                str(date_string_YYYYMMDD)
                + " EXIT _propagateOptimizationTransactionsIntoTheFuture",
                self.log_stack_depth,
            )
            return forecast_df

        log_in_color(logger, "cyan", "debug", "forecast_df:", self.log_stack_depth)
        log_in_color(
            logger, "cyan", "debug", forecast_df.to_string(), self.log_stack_depth
        )

        # log_in_color(
        #     logger,
        #     'magenta',
        #     'debug',
        #     f'ENTER _propagateOptimizationTransactionsIntoTheFuture({date_string_YYYYMMDD})',
        #     self.log_stack_depth
        # )

        post_txn_row_df = forecast_df[forecast_df["Date"] == date_string_YYYYMMDD]

        future_rows_only_df = forecast_df[
            forecast_df["Date"] > date_string_YYYYMMDD
        ].reset_index(drop=True)

        # Generate interest accrual dates
        interest_accrual_dates__list_of_lists = []
        for _, a_row in A_df.iterrows():
            interest_cadence = a_row["Interest_Cadence"]
            if pd.isnull(interest_cadence) or interest_cadence == "None":
                interest_accrual_dates__list_of_lists.append([])
                continue

            start_date = pd.to_datetime(a_row["Billing_Start_Date"], format="%Y%m%d")
            end_date = pd.to_datetime(self.end_date_YYYYMMDD, format="%Y%m%d")
            num_days = (end_date - start_date).days
            account_specific_iad = generate_date_sequence(
                a_row["Billing_Start_Date"], num_days, interest_cadence
            )
            interest_accrual_dates__list_of_lists.append(account_specific_iad)

        # Generate billing dates
        billing_dates__list_of_lists = []
        billing_dates__dict = {}
        for _, a_row in A_df.iterrows():
            billing_start_date = a_row["Billing_Start_Date"]
            if pd.isnull(billing_start_date) or billing_start_date == "None":
                billing_dates__list_of_lists.append([])
                continue

            start_date = pd.to_datetime(billing_start_date, format="%Y%m%d")
            end_date = pd.to_datetime(self.end_date_YYYYMMDD, format="%Y%m%d")
            num_days = (end_date - start_date).days
            account_specific_bd = generate_date_sequence(
                billing_start_date, num_days, "monthly"
            )
            billing_dates__list_of_lists.append(account_specific_bd)
            billing_dates__dict[a_row["Name"]] = account_specific_bd

        # Mapping of account type combinations to processing functions
        account_type_combinations = {
            frozenset(
                [
                    "checking",
                    "credit prev stmt bal",
                    "credit curr stmt bal",
                    "credit billing cycle payment bal",
                ]
            ): self._propagate_credit_payment_prev_curr,
            frozenset(
                [
                    "checking",
                    "principal balance",
                    "interest",
                    "loan billing cycle payment bal",
                ]
            ): self._propagate_loan_payment_pbal_interest,
            frozenset(
                ["checking", "principal balance", "loan billing cycle payment bal"]
            ): self._propagate_loan_payment_pbal_only,
            frozenset(
                ["checking", "interest", "loan billing cycle payment bal"]
            ): self._propagate_loan_payment_interest_only,
            frozenset(
                ["checking", "credit prev stmt bal", "credit billing cycle payment bal"]
            ): self._propagate_credit_payment_prev_only,
            frozenset(
                ["checking", "credit curr stmt bal", "credit billing cycle payment bal"]
            ): self._propagate_credit_payment_curr_only,
            frozenset(["credit curr stmt bal"]): self._propagate_credit_txn_curr_only,
        }

        # Assume accounts_df is a DataFrame containing account information
        accounts_df = account_set_before_p2_plus_txn.getAccounts().copy()

        # print('BEFORE processing_function branch')
        # print('account_deltas_list: '+str(account_deltas_list))

        # Create a Series for account deltas with the same index as accounts_df
        accounts_df["Delta"] = account_deltas_list

        # Extract base names (before ':') of account names
        accounts_df["Base_Name"] = accounts_df["Name"].str.split(":").str[0]

        # Select accounts with non-zero deltas
        accounts_with_deltas = accounts_df[accounts_df["Delta"] != 0]
        # print('accounts_with_deltas:')
        # print(accounts_with_deltas.to_string())

        # Check if 'checking' account type is involved in the transaction
        checking_in_txn = "checking" in accounts_with_deltas["Account_Type"].unique()

        # Get base names of accounts involved in the transaction
        affected_account_base_names = set(accounts_with_deltas["Base_Name"])

        # Get base names of checking accounts
        checking_base_names = set(
            accounts_df[accounts_df["Account_Type"] == "checking"]["Base_Name"]
        )

        # Base names of affected accounts excluding checking accounts
        affected_account_base_names_sans_checking = (
            affected_account_base_names - checking_base_names
        )

        if checking_in_txn and len(affected_account_base_names_sans_checking) == 0:

            log_in_color(
                logger,
                "yellow",
                "debug",
                str(date_string_YYYYMMDD)
                + " before processing_function (checking case)",
                self.log_stack_depth,
            )
            log_in_color(
                logger, "yellow", "debug", forecast_df.to_string(), self.log_stack_depth
            )

            # Only checking accounts are involved in the transaction
            # Update future balances for the checking accounts
            for idx, row in accounts_with_deltas[
                accounts_with_deltas["Account_Type"] == "checking"
            ].iterrows():
                relevant_checking_account_name = row["Name"]
                checking_delta = row["Delta"]
                future_rows_only_df[relevant_checking_account_name] += checking_delta

        else:
            # Process each affected base account name excluding checking accounts
            for account_base_name in affected_account_base_names_sans_checking:
                # Select accounts with the current base name
                accounts_with_base_name = accounts_df[
                    accounts_df["Base_Name"] == account_base_name
                ]

                # Select accounts with non-zero deltas and the current base name
                accounts_with_base_name_and_delta = accounts_with_base_name[
                    accounts_with_base_name["Delta"] != 0
                ]

                if accounts_with_base_name_and_delta.empty:
                    continue

                # Get the list of account types involved for this base name
                relevant_account_type_list = (
                    accounts_with_base_name_and_delta["Account_Type"].unique().tolist()
                )

                # If checking accounts are involved, include them
                if checking_in_txn:
                    checking_accounts_in_txn = accounts_with_deltas[
                        accounts_with_deltas["Account_Type"] == "checking"
                    ]
                    accounts_with_base_name_and_delta = pd.concat(
                        [accounts_with_base_name_and_delta, checking_accounts_in_txn]
                    )
                    if "checking" not in relevant_account_type_list:
                        relevant_account_type_list.append("checking")

                # Prepare the DataFrame with relevant account information
                relevant_account_info_df = accounts_with_base_name_and_delta

                # Proceed to handle the transaction based on relevant_account_type_list
                # (Implementation depends on specific business logic)

                # Identify the appropriate processing function
                account_types_set = frozenset(relevant_account_type_list)
                processing_function = account_type_combinations.get(account_types_set)

                log_in_color(
                    logger,
                    "cyan",
                    "info",
                    str(date_string_YYYYMMDD)
                    + " processing_function "
                    + str(processing_function),
                    self.log_stack_depth,
                )

                # print('account_types_set:')
                # print(account_types_set)

                if processing_function:

                    log_in_color(
                        logger,
                        "yellow",
                        "debug",
                        str(date_string_YYYYMMDD)
                        + " future_rows_only_df before processing_function",
                        self.log_stack_depth,
                    )
                    log_in_color(
                        logger,
                        "yellow",
                        "debug",
                        future_rows_only_df.to_string(),
                        self.log_stack_depth,
                    )

                    # Call the processing function
                    future_rows_only_df = processing_function(
                        relevant_account_info_df,
                        account_deltas_list,
                        future_rows_only_df,
                        forecast_df,
                        account_set_before_p2_plus_txn,
                        billing_dates__dict,
                        date_string_YYYYMMDD,
                        post_txn_row_df,
                    )

                else:
                    self.log_stack_depth -= 1
                    log_in_color(
                        logger,
                        "white",
                        "debug",
                        str(date_string_YYYYMMDD)
                        + " EXIT _propagateOptimizationTransactionsIntoTheFuture",
                        self.log_stack_depth,
                    )
                    raise ValueError("Undefined case in process_transactions")

        if not future_rows_only_df.empty:

            for idx, row in accounts_with_deltas.iterrows():
                min_balance = row["Min_Balance"]
                max_balance = row["Max_Balance"]
                relevant_account_name = row["Name"]

                min_future_acct_bal = min(future_rows_only_df[relevant_account_name])
                max_future_acct_bal = max(future_rows_only_df[relevant_account_name])

                try:
                    # assert min_balance <= min_future_acct_bal
                    assert (
                        min_balance - min_future_acct_bal
                    ) < ROUNDING_ERROR_TOLERANCE
                except AssertionError:
                    error_msg = (
                        "Failure in _propagateOptimizationTransactionsIntoTheFuture\n"
                    )
                    error_msg += "Account boundaries were violated\n"
                    error_msg += "min_balance <= min_future_acct_bal was not True\n"
                    error_msg += (
                        str(min_balance) + " <= " + str(min_future_acct_bal) + "\n"
                    )
                    error_msg += future_rows_only_df.to_string()
                    self.log_stack_depth -= 1
                    log_in_color(
                        logger,
                        "white",
                        "debug",
                        str(date_string_YYYYMMDD)
                        + " EXIT _propagateOptimizationTransactionsIntoTheFuture",
                        self.log_stack_depth,
                    )
                    raise ValueError(error_msg)

                try:
                    # assert max_balance >= max_future_acct_bal
                    assert (
                        max_balance - max_future_acct_bal
                    ) > ROUNDING_ERROR_TOLERANCE
                except AssertionError:
                    error_msg = (
                        "Failure in _propagateOptimizationTransactionsIntoTheFuture\n"
                    )
                    error_msg += "Account boundaries were violated\n"
                    error_msg += "max_balance >= max_future_acct_bal was not True\n"
                    error_msg += (
                        str(max_balance) + " <= " + str(max_future_acct_bal) + "\n"
                    )
                    error_msg += future_rows_only_df.to_string()
                    self.log_stack_depth -= 1
                    log_in_color(
                        logger,
                        "white",
                        "debug",
                        str(date_string_YYYYMMDD)
                        + " EXIT _propagateOptimizationTransactionsIntoTheFuture",
                        self.log_stack_depth,
                    )
                    raise ValueError(error_msg)

            # If an error occurs here, it is because of systemic error in the algroithm
            # Not a valid rejection of a transactions
            # also check for rounding that caused real deltas to mismatch the memos!!!!
            for f_i, f_row in future_rows_only_df.iterrows():
                log_in_color(
                    logger, "white", "debug", "Date:" + f_row.Date, self.log_stack_depth
                )
                # we don't use index bc it won't be 1 and reindexing is expensive
                current_row = f_row
                current_date_string = f_row.Date
                first_row_date_string = future_rows_only_df.head(1).Date.iat[0]
                if current_date_string == first_row_date_string:
                    previous_row = forecast_df[forecast_df.Date == date_string_YYYYMMDD]
                else:
                    previous_row = future_rows_only_df.loc[f_i - 1, :]

                log_in_color(
                    logger, "white", "debug", "previous_row:", self.log_stack_depth
                )
                if str(type(previous_row)) == "<class 'pandas.core.frame.DataFrame'>":
                    log_in_color(
                        logger,
                        "white",
                        "debug",
                        previous_row.to_string(),
                        self.log_stack_depth,
                    )
                else:
                    # type is pandas.core.series.Series
                    log_in_color(
                        logger,
                        "white",
                        "debug",
                        pd.DataFrame(previous_row).T.to_string(),
                        self.log_stack_depth,
                    )

                log_in_color(
                    logger, "white", "debug", "current_row:", self.log_stack_depth
                )
                if str(type(current_row)) == "<class 'pandas.core.frame.DataFrame'>":
                    log_in_color(
                        logger,
                        "white",
                        "debug",
                        current_row.to_string(),
                        self.log_stack_depth,
                    )
                else:
                    # type is pandas.core.series.Series
                    log_in_color(
                        logger,
                        "white",
                        "debug",
                        pd.DataFrame(current_row).T.to_string(),
                        self.log_stack_depth,
                    )

                reported_acct_deltas = {}
                for md in f_row["Memo Directives"].split(";"):
                    if md.strip() == "":
                        continue
                    if "CC MIN PAYMENT ALREADY MADE" in md:
                        continue
                    log_in_color(
                        logger, "white", "debug", "md:" + str(md), self.log_stack_depth
                    )
                    txn_info = re.search("\\((.*)\\$(.*)\\)", md)
                    acct_name = txn_info.group(1).split(":")[0]
                    acct_name = acct_name.replace("-", "").replace("+", "").strip()
                    memo_balance = float(txn_info.group(2))
                    if acct_name not in reported_acct_deltas.keys():
                        if "Loan" in acct_name:
                            continue  # todo shouldnt need to do this
                        if "-$" in md:
                            memo_balance = -1 * abs(memo_balance)
                        elif "+$" in md:
                            memo_balance = abs(memo_balance)
                        reported_acct_deltas[acct_name] = memo_balance
                        log_in_color(
                            logger,
                            "white",
                            "debug",
                            "reported_acct_deltas["
                            + str(acct_name)
                            + "] = "
                            + str(memo_balance),
                            self.log_stack_depth,
                        )
                    else:
                        if "-$" in md:
                            memo_balance = -1 * abs(memo_balance)
                        elif "+$" in md:
                            memo_balance = abs(memo_balance)
                        reported_acct_deltas[acct_name] += memo_balance
                        log_in_color(
                            logger,
                            "white",
                            "debug",
                            "reported_acct_deltas["
                            + str(acct_name)
                            + "] += "
                            + str(memo_balance)
                            + " = "
                            + str(reported_acct_deltas[acct_name]),
                            self.log_stack_depth,
                        )

                for m in f_row["Memo"].split(";"):
                    if "income" in m or m.strip() == "":
                        # bc otherwise would be double counted. this is a known design weakness
                        # don't bully me i'll cum
                        continue
                    log_in_color(
                        logger, "white", "debug", "m:" + str(m), self.log_stack_depth
                    )
                    txn_info = re.search("\\((.*).*\\$(.*)\\)", m)
                    acct_name = txn_info.group(1)
                    acct_name = acct_name.replace("-", "").replace("+", "").strip()
                    memo_balance = float(txn_info.group(2))
                    if acct_name not in reported_acct_deltas.keys():
                        if "Loan" in acct_name:
                            continue  # todo shouldnt need to do this
                        if (
                            "-$" in m
                        ):  # and 'Checking' not in acct_name: #todo this needs to dynamically check acct type
                            memo_balance = -1 * abs(memo_balance)
                        else:
                            memo_balance = abs(memo_balance)
                        reported_acct_deltas[acct_name] = memo_balance
                        log_in_color(
                            logger,
                            "white",
                            "debug",
                            "reported_acct_deltas["
                            + str(acct_name)
                            + "] = "
                            + str(memo_balance),
                            self.log_stack_depth,
                        )
                    else:
                        if (
                            "-$" in m
                        ):  # and 'Checking' not in acct_name: #todo this needs to dynamically check acct type
                            memo_balance = -1 * abs(memo_balance)
                        else:
                            memo_balance = abs(memo_balance)
                        reported_acct_deltas[acct_name] += memo_balance
                        log_in_color(
                            logger,
                            "white",
                            "debug",
                            "reported_acct_deltas["
                            + str(acct_name)
                            + "] += "
                            + str(memo_balance)
                            + " = "
                            + str(reported_acct_deltas[acct_name]),
                            self.log_stack_depth,
                        )

                observed_acct_deltas = {}
                for cname in forecast_df.columns:
                    if cname in ["Date", "Next Income Date", "Memo Directives", "Memo"]:
                        continue
                    if (
                        "Dad" in cname
                        or "Loan" in cname
                        or "Prev Cycle Bal" in cname
                        or "Billing Cycle Payment Bal" in cname
                    ):
                        # todo consider adding interest accrual to memo directives
                        # Not sure why Loan wasnt sufficient to catch Dad but whatever its temporary anyway
                        continue
                    full_cname = cname
                    cname = cname.split(":")[0]
                    current_delta = float(current_row[full_cname]) - float(
                        previous_row[full_cname]
                    )
                    if cname not in observed_acct_deltas.keys():
                        if abs(current_delta) > ROUNDING_ERROR_TOLERANCE:
                            observed_acct_deltas[cname] = current_delta
                            log_in_color(
                                logger,
                                "white",
                                "debug",
                                "observed_acct_deltas["
                                + str(cname)
                                + "] = "
                                + str(current_delta),
                                self.log_stack_depth,
                            )
                    else:
                        if abs(current_delta) > ROUNDING_ERROR_TOLERANCE:
                            observed_acct_deltas[cname] += current_delta
                            log_in_color(
                                logger,
                                "white",
                                "debug",
                                "observed_acct_deltas["
                                + str(cname)
                                + "] += "
                                + str(current_delta)
                                + " = "
                                + str(observed_acct_deltas[cname]),
                                self.log_stack_depth,
                            )

                observed_acct_deltas_2 = {}
                for k, v in observed_acct_deltas.items():
                    if abs(observed_acct_deltas[k]) > ROUNDING_ERROR_TOLERANCE:
                        # print('observed '+str(k)+' NOT within error tolerance')
                        observed_acct_deltas_2[k] = v
                        # print('observed_acct_deltas_2: '+str(observed_acct_deltas_2))
                    else:
                        # print('observed '+str(k)+' within error tolerance')
                        pass
                observed_acct_deltas = observed_acct_deltas_2
                del observed_acct_deltas_2

                reported_acct_deltas_2 = {}
                for k, v in reported_acct_deltas.items():
                    if abs(reported_acct_deltas[k]) > ROUNDING_ERROR_TOLERANCE:
                        reported_acct_deltas_2[k] = v
                reported_acct_deltas = reported_acct_deltas_2
                del reported_acct_deltas_2

                if set(reported_acct_deltas.keys()) != set(observed_acct_deltas.keys()):
                    log_in_color(
                        logger,
                        "white",
                        "debug",
                        "reported_acct_deltas.keys(): "
                        + str(reported_acct_deltas.keys()),
                        self.log_stack_depth,
                    )
                    log_in_color(
                        logger,
                        "white",
                        "debug",
                        "observed_acct_deltas.keys(): "
                        + str(observed_acct_deltas.keys()),
                        self.log_stack_depth,
                    )
                    # print(pd.DataFrame(previous_row).T.to_string())
                    # print(pd.DataFrame(current_row).T.to_string())
                    if f_i == 0:
                        pass
                    else:
                        log_in_color(
                            logger,
                            "white",
                            "debug",
                            future_rows_only_df.loc[(f_i - 1, f_i), :].to_string(),
                            self.log_stack_depth,
                        )
                    raise ValueError(
                        "Observed delta column set mismatched reported delta column set"
                    )

                for k, v in reported_acct_deltas.items():
                    rounding_error = abs(
                        reported_acct_deltas[k] - observed_acct_deltas[k]
                    )
                    if rounding_error > ROUNDING_ERROR_TOLERANCE:
                        exception_string = (
                            current_date_string
                            + " Memo Lied!!! reported != observed for "
                            + str(k)
                            + "\n"
                        )
                        exception_string += (
                            str(reported_acct_deltas[k])
                            + " != "
                            + str(observed_acct_deltas[k])
                            + "\n"
                        )
                        exception_string += (
                            str(rounding_error)
                            + " > "
                            + str(ROUNDING_ERROR_TOLERANCE)
                            + "\n"
                        )
                        if f_i == 0:
                            log_in_color(
                                logger,
                                "white",
                                "debug",
                                pd.DataFrame(previous_row).to_string(),
                                self.log_stack_depth,
                            )
                            log_in_color(
                                logger,
                                "white",
                                "debug",
                                pd.DataFrame(current_row).T.to_string(),
                                self.log_stack_depth,
                            )
                        else:
                            log_in_color(
                                logger,
                                "white",
                                "debug",
                                future_rows_only_df.loc[(f_i - 1, f_i), :].to_string(),
                                self.log_stack_depth,
                            )
                        raise ValueError(exception_string)

            # todo very slow to do this
            index_of_first_future_day = list(forecast_df.Date).index(
                future_rows_only_df.head(1).Date.iat[0]
            )
            future_rows_only_df.index = (
                future_rows_only_df.index + index_of_first_future_day
            )
            forecast_df.update(future_rows_only_df)

        log_in_color(
            logger,
            "yellow",
            "debug",
            str(date_string_YYYYMMDD) + " after processing_function",
            self.log_stack_depth,
        )
        log_in_color(
            logger, "yellow", "debug", forecast_df.to_string(), self.log_stack_depth
        )

        self.log_stack_depth -= 1
        log_in_color(
            logger,
            "white",
            "debug",
            str(date_string_YYYYMMDD)
            + " EXIT _propagateOptimizationTransactionsIntoTheFuture",
            self.log_stack_depth,
        )
        return forecast_df

    # @profile
    def _updateProposedTransactionsBasedOnOtherSets(
        self, confirmed_df, proposed_df, deferred_df, skipped_df
    ):

        self.log_stack_depth += 1

        p_LJ_c = pd.merge(proposed_df, confirmed_df, on=["Date", "Memo", "Priority"])
        p_LJ_d = pd.merge(proposed_df, deferred_df, on=["Date", "Memo", "Priority"])
        p_LJ_s = pd.merge(proposed_df, skipped_df, on=["Date", "Memo", "Priority"])

        not_confirmed_sel_vec = ~proposed_df.index.isin(p_LJ_c)
        not_deferred_sel_vec = ~proposed_df.index.isin(p_LJ_d)
        not_skipped_sel_vec = ~proposed_df.index.isin(p_LJ_s)
        remaining_unproposed_sel_vec = (
            not_confirmed_sel_vec & not_deferred_sel_vec & not_skipped_sel_vec
        )
        remaining_unproposed_transactions_df = proposed_df[remaining_unproposed_sel_vec]

        self.log_stack_depth -= 1
        # log_in_color(logger, 'cyan', 'debug', 'EXIT _updateProposedTransactionsBasedOnOtherSets',self.log_stack_depth)
        return remaining_unproposed_transactions_df

    def _assessPotentialOptimizationsApproximate(
        self,
        forecast_df,
        account_set,
        memo_rule_set,
        confirmed_df,
        proposed_df,
        deferred_df,
        skipped_df,
        raise__satisfice_failed_exception,
        progress_bar=None,
    ):
        F = "F:" + str(forecast_df.shape[0])
        C = "C:" + str(confirmed_df.shape[0])
        P = "P:" + str(proposed_df.shape[0])
        D = "D:" + str(deferred_df.shape[0])
        S = "S:" + str(skipped_df.shape[0])
        # log_in_color(logger,'magenta','debug','ENTER _assessPotentialOptimizationsApproximate( '+F+' '+C+' '+P+' '+D+' '+S+' )',self.log_stack_depth)
        self.log_stack_depth += 1
        all_days = (
            forecast_df.Date
        )  # todo havent tested this, but forecast_df has been _satisficed so it has all the dates

        # Schema is: Date, Priority, Amount, Memo, Deferrable, Partial_Payment_Allowed
        full_budget_schedule_df = pd.concat(
            [confirmed_df, proposed_df, deferred_df, skipped_df]
        )
        full_budget_schedule_df.reset_index(drop=True, inplace=True)

        unique_priority_indices = full_budget_schedule_df.Priority.unique()
        unique_priority_indices.sort()

        last_iteration_ts = None  # this is here to remove a warning

        if not raise__satisfice_failed_exception:
            log_in_color(logger, "white", "debug", "Beginning Optimization.")
            # log_in_color(logger, 'white', 'debug', self.start_date_YYYYMMDD + ' -> ' + self.end_date_YYYYMMDD)
            # log_in_color(logger, 'white', 'debug', 'Priority Indices: ' + str(unique_priority_indices))
            last_iteration_ts = datetime.datetime.now()

        for priority_index in unique_priority_indices:

            if priority_index == 1:
                continue  # because this was handled by _satisfice

            for date_string_YYYYMMDD in all_days:
                # print('date_string_YYYYMMDD:'+str(date_string_YYYYMMDD))
                if date_string_YYYYMMDD == forecast_df.head(1).Date.iat[0]:
                    # if date_string_YYYYMMDD == self.start_date_YYYYMMDD:
                    continue  # first day is considered final

                if not raise__satisfice_failed_exception:
                    if progress_bar is not None:
                        progress_bar.update(1)
                        progress_bar.refresh()

                    iteration_time_elapsed = datetime.datetime.now() - last_iteration_ts
                    last_iteration_ts = datetime.datetime.now()
                    log_string = (
                        str(priority_index)
                        + " "
                        + datetime.datetime.strptime(
                            date_string_YYYYMMDD, "%Y%m%d"
                        ).strftime("%Y-%m-%d")
                    )
                    log_string += "     " + str(iteration_time_elapsed)
                    # log_in_color(logger, 'white', 'debug', log_string )

                # log_in_color(logger, 'magenta', 'info', 'p' + str(priority_index) + ' ' + str(date_string_YYYYMMDD),self.log_stack_depth)

                remaining_unproposed_transactions_df = (
                    self._updateProposedTransactionsBasedOnOtherSets(
                        confirmed_df, proposed_df, deferred_df, skipped_df
                    )
                )

                # todo idk if this is necessary
                account_set = self._sync_account_set_w_forecast_day(
                    account_set, forecast_df, date_string_YYYYMMDD
                )

                # todo maybe this could be moved down? not sure
                account_set_before_p2_plus_txn = copy.deepcopy(account_set)

                # todo not sure if this is necessary
                account_set = self._sync_account_set_w_forecast_day(
                    account_set, forecast_df, date_string_YYYYMMDD
                )

                # log_in_color(logger, 'yellow', 'debug','proposed_df before eTFD:')
                # log_in_color(logger, 'yellow', 'debug', proposed_df.to_string())

                forecast_df, confirmed_df, deferred_df, skipped_df = (
                    self._executeTransactionsForDayApproximate(
                        account_set=account_set,
                        forecast_df=forecast_df,
                        date_YYYYMMDD=date_string_YYYYMMDD,
                        memo_set=memo_rule_set,
                        confirmed_df=confirmed_df,
                        proposed_df=remaining_unproposed_transactions_df,
                        deferred_df=deferred_df,
                        skipped_df=skipped_df,
                        priority_level=priority_index,
                    )
                )

                # log_in_color(logger, 'yellow', 'debug', 'proposed after eTFD:')
                # log_in_color(logger, 'yellow', 'debug', proposed_df.to_string())

                account_set = self._sync_account_set_w_forecast_day(
                    account_set, forecast_df, date_string_YYYYMMDD
                )

                # this is necessary to make balance deltas propoagate only once
                if raise__satisfice_failed_exception:

                    # regarding why the input params are what they are here:
                    # since the budget schedule does not have Account_From and Account_To, we infer which accounts were
                    # affected by comparing the before and after, hence this method accepts the prior and current state
                    # to modify forecast_df
                    # Furthermore, additional loan payments affect the allocation of future minimum loan payments
                    # so p1 minimumpayments, which aren't even BudgetItems as of 12/31/23.... must be edited
                    # it kind of makes more sense to refactor and have credit card minimum payments and loan minimum
                    # # payments as budget items....
                    #
                    # Doing that though creates a coupling between the AccountSet and BudgetSet classes that I don't like...
                    # I only recently got the full detail of what happens into the Memo field, but I think that that is the answer
                    # There will be information encoded in the Memo column that will not appear anywhere else
                    #
                    # print(forecast_df.to_string())
                    forecast_df = self._propagateOptimizationTransactionsIntoTheFuture(
                        account_set_before_p2_plus_txn,
                        forecast_df,
                        date_string_YYYYMMDD,
                    )
                    # print(forecast_df.to_string())

        self.log_stack_depth -= 1
        # log_in_color(logger, 'magenta', 'debug', 'EXIT _assessPotentialOptimizations() C:'+str(confirmed_df.shape[0])+' D:'+str(deferred_df.shape[0])+' S:'+str(skipped_df.shape[0]),self.log_stack_depth)
        return forecast_df, skipped_df, confirmed_df, deferred_df

    # @profile
    def _assessPotentialOptimizations(
        self,
        forecast_df,
        account_set,
        memo_rule_set,
        confirmed_df,
        proposed_df,
        deferred_df,
        skipped_df,
        raise__satisfice_failed_exception,
        progress_bar=None,
    ):
        log_in_color(
            logger,
            "white",
            "info",
            "ENTER _assessPotentialOptimizations",
            self.log_stack_depth,
        )
        self.log_stack_depth += 1

        log_in_color(
            logger, "white", "info", forecast_df.to_string(), self.log_stack_depth
        )

        all_days = forecast_df.Date

        # Schema is: Date, Priority, Amount, Memo, Deferrable, Partial_Payment_Allowed
        full_budget_schedule_df = pd.concat(
            [confirmed_df, proposed_df, deferred_df, skipped_df]
        )
        full_budget_schedule_df.reset_index(drop=True, inplace=True)

        unique_priority_indices = full_budget_schedule_df.Priority.unique()
        unique_priority_indices.sort()

        last_iteration_ts = None  # this is here to remove a warning

        if not raise__satisfice_failed_exception:
            log_in_color(logger, "white", "info", "Beginning Optimization.")
            # log_in_color(logger, 'white', 'info', forecast_df.to_string())
            last_iteration_ts = datetime.datetime.now()

        # print('Beginning unique_priority_indices:'+str(unique_priority_indices))
        for priority_index in unique_priority_indices:
            if priority_index == 1:
                continue  # because this was handled by _satisfice

            for date_string_YYYYMMDD in all_days:
                if date_string_YYYYMMDD == forecast_df.head(1).Date.iat[0]:
                    # if date_string_YYYYMMDD == self.start_date_YYYYMMDD:
                    continue  # first day is considered final

                if not raise__satisfice_failed_exception:
                    if progress_bar is not None:
                        progress_bar.update(1)
                        progress_bar.refresh()

                    iteration_time_elapsed = datetime.datetime.now() - last_iteration_ts
                    last_iteration_ts = datetime.datetime.now()
                    log_string = (
                        str(priority_index)
                        + " "
                        + datetime.datetime.strptime(
                            date_string_YYYYMMDD, "%Y%m%d"
                        ).strftime("%Y-%m-%d")
                    )
                    log_string += "     " + str(iteration_time_elapsed)
                    # log_in_color(logger, 'white', 'debug', log_string )

                # log_in_color(logger, 'magenta', 'info', 'p' + str(priority_index) + ' ' + str(date_string_YYYYMMDD),self.log_stack_depth)

                remaining_unproposed_transactions_df = (
                    self._updateProposedTransactionsBasedOnOtherSets(
                        confirmed_df, proposed_df, deferred_df, skipped_df
                    )
                )

                # todo idk if this is necessary
                account_set = self._sync_account_set_w_forecast_day(
                    account_set, forecast_df, date_string_YYYYMMDD
                )

                # todo maybe this could be moved down? not sure
                account_set_before_p2_plus_txn = copy.deepcopy(account_set)

                # todo not sure if this is necessary
                account_set = self._sync_account_set_w_forecast_day(
                    account_set, forecast_df, date_string_YYYYMMDD
                )

                try:
                    # print('BEFORE ETFD:')
                    # print(confirmed_df.to_string())
                    forecast_df, confirmed_df, deferred_df, skipped_df = (
                        self._executeTransactionsForDay(
                            account_set=account_set,
                            forecast_df=forecast_df,
                            date_YYYYMMDD=date_string_YYYYMMDD,
                            memo_set=memo_rule_set,
                            confirmed_df=confirmed_df,
                            proposed_df=remaining_unproposed_transactions_df,
                            deferred_df=deferred_df,
                            skipped_df=skipped_df,
                            priority_level=priority_index,
                        )
                    )
                    # print('AFTER ETFD:')
                    # print(confirmed_df.to_string())
                except Exception as e:
                    # log_in_color(logger, 'magenta', 'debug', forecast_df.to_string(), self.log_stack_depth)
                    self.log_stack_depth -= 1
                    log_in_color(
                        logger,
                        "white",
                        "debug",
                        "EXIT _assessPotentialOptimizations",
                        self.log_stack_depth,
                    )
                    raise e

                # log_in_color(logger, 'green', 'info', 'forecast_df after eTFD ('+str(date_string_YYYYMMDD)+'):', self.log_stack_depth)
                # log_in_color(logger, 'green', 'info', forecast_df.to_string(), self.log_stack_depth)

                # print('assess optimizations case 3 sync')
                account_set = self._sync_account_set_w_forecast_day(
                    account_set, forecast_df, date_string_YYYYMMDD
                )

                #
                # log_in_color(logger, 'magenta', 'debug', 'before', self.log_stack_depth)
                # log_in_color(logger, 'magenta', 'debug', account_set_before_p2_plus_txn.getAccounts().to_string(), self.log_stack_depth)
                # log_in_color(logger, 'magenta', 'debug', 'after', self.log_stack_depth)
                # log_in_color(logger, 'magenta', 'debug', account_set.getAccounts().to_string(), self.log_stack_depth)

                # this is necessary to make balance deltas propagate only once
                # print('raise__satisfice_failed_exception:'+str(raise__satisfice_failed_exception))
                if raise__satisfice_failed_exception:

                    # regarding why the input params are what they are here:
                    # since the budget schedule does not have Account_From and Account_To, we infer which accounts were
                    # affected by comparing the before and after, hence this method accepts the prior and current state
                    # to modify forecast_df
                    # Furthermore, additional loan payments affect the allocation of future minimum loan payments
                    # so p1 minimumpayments, which aren't even BudgetItems as of 12/31/23.... must be edited
                    # it kind of makes more sense to refactor and have credit card minimum payments and loan minimum
                    # # payments as budget items....
                    #
                    # Doing that though creates a coupling between the AccountSet and BudgetSet classes that I don't like...
                    # I only recently got the full detail of what happens into the Memo field, but I think that that is the answer
                    # There will be information encoded in the Memo column that will not appear anywhere else
                    #
                    # print('about to _propagateOptimizationTransactionsIntoTheFuture')
                    # print('BEFORE')
                    # print(forecast_df.to_string())
                    forecast_df = self._propagateOptimizationTransactionsIntoTheFuture(
                        account_set_before_p2_plus_txn,
                        forecast_df,
                        date_string_YYYYMMDD,
                    )

                    # print('AFTER')
                    # print(forecast_df.to_string())
        # log_in_color(logger, 'magenta', 'debug', forecast_df.to_string(), self.log_stack_depth)

        self.log_stack_depth -= 1
        log_in_color(
            logger,
            "white",
            "debug",
            "EXIT _assessPotentialOptimizations",
            self.log_stack_depth,
        )
        return forecast_df, skipped_df, confirmed_df, deferred_df

    def _cleanUpAfterFailedSatisfice(
        self, confirmed_df, proposed_df, deferred_df, skipped_df
    ):

        # this logic takes everything that was not executed and adds it to skipped_df
        not_confirmed_sel_vec = [
            (
                datetime.datetime.strptime(d, "%Y%m%d")
                > datetime.datetime.strptime(self.end_date_YYYYMMDD, "%Y%m%d")
            )
            for d in confirmed_df.Date
        ]  # this is using an end date that has been moved forward, so it is > not >=
        not_confirmed_df = confirmed_df.loc[not_confirmed_sel_vec]
        new_deferred_df = proposed_df.loc[[not x for x in proposed_df.Deferrable]]
        skipped_df = pd.concat(
            [skipped_df, not_confirmed_df, new_deferred_df, deferred_df]
        )  # todo I added deferred_df without testing if that was correct

        # if it was confirmed before the date of failure, it stays confirmed
        confirmed_sel_vec = [
            (
                datetime.datetime.strptime(d, "%Y%m%d")
                <= datetime.datetime.strptime(self.end_date_YYYYMMDD, "%Y%m%d")
            )
            for d in confirmed_df.Date
        ]
        confirmed_df = confirmed_df.loc[confirmed_sel_vec]

        # todo if _satisfice fails, should deferred transactions stay deferred?
        deferred_df = proposed_df.loc[proposed_df.Deferrable]

        skipped_df.reset_index(inplace=True, drop=True)
        confirmed_df.reset_index(inplace=True, drop=True)
        deferred_df.reset_index(inplace=True, drop=True)

        return confirmed_df, deferred_df, skipped_df

    def _updateEndOfPrevCycleBal(
        self, forecast_df, account_set, current_forecast_row_df
    ):
        log_in_color(
            logger,
            "white",
            "debug",
            str(current_forecast_row_df.Date.iat[0])
            + " ENTER _updateEndOfPrevCycleBal",
            self.log_stack_depth,
        )
        self.log_stack_depth += 1
        # Naively:
        # if it is the day after a credit card minimum payment,
        # set : Credit End of Prev Cycle Bal = Prev Stmt Bal for the previous day
        # The Nuance:
        # Since additional payments day-of do not count towards minimum payments
        #   they cannot count towards reducing the value this method aims to update either
        #   therefore, the new logic should be:
        #
        # end of prev cycle balance = sum of prev and curr DAY BEFORE billing date
        # since this is called before minimum payments, that logic suffices
        # plus interest from one day ago

        for account_index, account_row in account_set.getAccounts().iterrows():

            if "end of prev cycle bal" not in account_row.Account_Type:
                # print('Skipping '+str(account_row.Name))
                continue
            # print('Processing ' + str(account_row.Name))

            billing_start_date_str = account_row.Billing_Start_Date
            billing_start_datetime = datetime.datetime.strptime(
                billing_start_date_str, "%Y%m%d"
            )

            billing_start_date_plus_1_datetime = (
                billing_start_datetime + datetime.timedelta(days=1)
            )
            billing_start_date_plus_1_str = billing_start_date_plus_1_datetime.strftime(
                "%Y%m%d"
            )

            current_date_str = current_forecast_row_df.Date.iloc[0]
            current_date = datetime.datetime.strptime(current_date_str, "%Y%m%d")

            num_days_since_bsd = (current_date - billing_start_datetime).days
            num_days_since_bsd_plus_1 = (
                current_date - billing_start_date_plus_1_datetime
            ).days

            # we could put some return condition here like, if num_days_since_bsd < 30 then return
            # but month lengths are weird so let's just rely on the more robust check

            # Generate billing days
            # print('num_days_since_bsd_plus_1:'+str(num_days_since_bsd_plus_1))
            if num_days_since_bsd_plus_1 >= 0:
                update_days = set(
                    generate_date_sequence(
                        billing_start_date_plus_1_str,
                        num_days_since_bsd_plus_1,
                        "monthly",
                    )
                )
            else:
                update_days = set()
            # print('update_days:'+str(update_days))

            if current_date_str not in update_days or len(update_days) == 0:
                # print('Skipping ' + str(account_row.Name)+' because current_date_str not in update_days')
                continue

            if len(update_days) == 0:
                # print('Skipping ' + str(account_row.Name)+' len(update_days) == 0')
                continue

            # if this is the first day of the forecast, this method wouldnt be called
            # therefore, here, there will always be a previous day of the forecast

            # current_date_minus_1_day = current_date - datetime.timedelta(days=1)
            # current_date_minus_1_day_str = current_date_minus_1_day.strftime('%Y%m%d')

            prev_date = current_date - datetime.timedelta(days=1)
            prev_date_str = prev_date.strftime("%Y%m%d")

            previous_row_df = forecast_df[forecast_df.Date == prev_date_str]

            # log_in_color(logger, 'cyan', 'debug', 'previous_row_df:', self.log_stack_depth)
            # log_in_color(logger, 'cyan', 'debug', previous_row_df.to_string(), self.log_stack_depth)

            # print('forecast_df:')
            # print(forecast_df.to_string())
            # print('billing_start_datetime_minus_1_day_str: '+str(current_date_minus_1_day_str))

            if account_row.Account_Type == "credit end of prev cycle bal":
                account_basename = account_row.Name.split(":")[0]
                prev_aname = account_basename + ": Prev Stmt Bal"
                # curr_aname = account_basename + ': Curr Stmt Bal'
                eopc_aname = account_basename + ": Credit End of Prev Cycle Bal"

                new_bal = previous_row_df[prev_aname].iat[
                    0
                ]  # + previous_row_df[curr_aname].iat[0]

                # I think that this is no longer necessary bc i changed implementation
                # #subtract interest that was added on the previous day
                # if previous_row_df[eopc_aname].iat[0] > 0: #then there was interest
                #     interest_accrued = self._extract_interest_accrued_amount(account_basename,previous_row_df['Memo Directives'].iat[0])
                # else:
                #     interest_accrued = 0
                #     pass #no interest was accrued that needs to be accounted for
                # new_bal -= interest_accrued

                # log_in_color(logger, 'white', 'debug', 'SET '+str(eopc_aname)+' = '+str(new_bal), self.log_stack_depth)
                current_forecast_row_df[eopc_aname] = new_bal
            elif account_row.Account_Type == "loan end of prev cycle bal":
                pbal_aname = account_row.Name.split(":")[0] + ": Principal Balance"
                # interest_aname = account_row.Name.split(':')[0] + ': Interest'
                eopc_aname = (
                    account_row.Name.split(":")[0] + ": Loan End of Prev Cycle Bal"
                )

                new_bal = previous_row_df[pbal_aname].iat[
                    0
                ]  # + previous_row_df[interest_aname].iat[0]
                # log_in_color(logger, 'white', 'debug', 'SET ' + str(eopc_aname) + ' = ' + str(new_bal), self.log_stack_depth)
                current_forecast_row_df[eopc_aname] = new_bal

        # log_in_color(logger, 'white', 'debug', 'returning this row:', self.log_stack_depth)
        # log_in_color(logger, 'white', 'debug', current_forecast_row_df.to_string(), self.log_stack_depth)

        self.log_stack_depth -= 1
        log_in_color(
            logger,
            "white",
            "debug",
            str(current_forecast_row_df.Date.iat[0]) + " EXIT _updateEndOfPrevCycleBal",
            self.log_stack_depth,
        )
        return current_forecast_row_df

    # @profile
    def _satisfice(
        self,
        list_of_date_strings,
        confirmed_df,
        account_set,
        memo_rule_set,
        forecast_df,
        raise__satisfice_failed_exception,
        progress_bar=None,
    ):
        log_in_color(logger, "white", "info", "ENTER _satisfice", self.log_stack_depth)
        self.log_stack_depth += 1

        all_days = list_of_date_strings  # Rename for clarity

        for date_str in all_days:
            if progress_bar:
                progress_bar.update(1)
                progress_bar.refresh()

            # log_in_color(logger, 'magenta', 'info', str(date_str)+' forecast_df', self.log_stack_depth)
            # log_in_color(logger, 'magenta', 'info', forecast_df.to_string(), self.log_stack_depth)

            # Skip the first day, considered as final
            if date_str == self.start_date_YYYYMMDD:
                continue

            try:
                # Log transaction details if exception handling is not strict
                if not raise__satisfice_failed_exception:
                    log_string = f"1 {datetime.datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')}"

                # if not confirmed_df.empty:
                #     log_in_color(logger, 'white', 'debug', 'confirmed_df:', self.log_stack_depth)
                #     log_in_color(logger, 'white', 'debug', confirmed_df.to_string(), self.log_stack_depth)

                # Execute transactions for the day, priority 1 (non-negotiable)
                forecast_df, confirmed_df, deferred_df, skipped_df = (
                    self._executeTransactionsForDay(
                        account_set=account_set,
                        forecast_df=forecast_df,
                        date_YYYYMMDD=date_str,
                        memo_set=memo_rule_set,
                        confirmed_df=confirmed_df,
                        proposed_df=confirmed_df.head(
                            0
                        ),  # No proposed transactions in _satisfice
                        deferred_df=confirmed_df.head(
                            0
                        ),  # No deferred transactions in _satisfice
                        skipped_df=confirmed_df.head(
                            0
                        ),  # No skipped transactions in _satisfice
                        priority_level=1,
                    )
                )

                # Sync account set after transactions
                account_set = self._sync_account_set_w_forecast_day(
                    account_set, forecast_df, date_str
                )

                # Calculate loan interest accruals for the day
                forecast_df.loc[forecast_df.Date == date_str] = (
                    self._calculateLoanInterestAccrualsForDay(
                        account_set, forecast_df[forecast_df.Date == date_str]
                    )
                )

                # Sync again after interest accruals
                account_set = self._sync_account_set_w_forecast_day(
                    account_set, forecast_df, date_str
                )

                # log_in_color(logger, 'green', 'info', 'BEFORE loan min payment', self.log_stack_depth)
                # log_in_color(logger, 'green', 'info', forecast_df.to_string(), self.log_stack_depth)

                # Execute minimum loan payments
                forecast_df.loc[forecast_df.Date == date_str] = (
                    self._executeLoanMinimumPayments(
                        account_set, forecast_df[forecast_df.Date == date_str]
                    )
                )

                # log_in_color(logger, 'green', 'info', 'AFTER loan min payment', self.log_stack_depth)
                # log_in_color(logger, 'green', 'info', forecast_df.to_string(), self.log_stack_depth)

                # Sync after loan payments
                account_set = self._sync_account_set_w_forecast_day(
                    account_set, forecast_df, date_str
                )

                # log_in_color(logger, 'green', 'info', 'BEFORE cc min payment', self.log_stack_depth)
                # log_in_color(logger, 'green', 'info', forecast_df.to_string(), self.log_stack_depth)

                forecast_df.loc[forecast_df.Date == date_str] = (
                    self._updateEndOfPrevCycleBal(
                        forecast_df,
                        account_set,
                        forecast_df[forecast_df.Date == date_str],
                    )
                )

                account_set = self._sync_account_set_w_forecast_day(
                    account_set, forecast_df, date_str
                )

                # Execute credit card minimum payments
                forecast_df.loc[forecast_df.Date == date_str] = (
                    self._executeCreditCardMinimumPayments(
                        forecast_df,
                        account_set,
                        forecast_df[forecast_df.Date == date_str],
                    )
                )

                # log_in_color(logger, 'green', 'info', 'AFTER cc min payment', self.log_stack_depth)
                # log_in_color(logger, 'green', 'info', forecast_df.to_string(), self.log_stack_depth)

                # Final sync for the day
                account_set = self._sync_account_set_w_forecast_day(
                    account_set, forecast_df, date_str
                )

            except ValueError as e:
                error_message = str(e.args)
                # Handle specific account boundary violations
                if (
                    re.search(".*Account boundaries were violated.*", error_message)
                    and not raise__satisfice_failed_exception
                ):
                    self.end_date = datetime.datetime.strptime(
                        date_str, "%Y%m%d"
                    ) - datetime.timedelta(days=1)

                    log_in_color(
                        logger,
                        "cyan",
                        "error",
                        "Account Boundaries were violated",
                        self.log_stack_depth,
                    )
                    log_in_color(
                        logger, "cyan", "error", error_message, self.log_stack_depth
                    )
                    log_in_color(
                        logger,
                        "cyan",
                        "error",
                        "State at failure:",
                        self.log_stack_depth,
                    )
                    log_in_color(
                        logger,
                        "cyan",
                        "error",
                        forecast_df.to_string(),
                        self.log_stack_depth,
                    )

                    self.log_stack_depth -= 1
                    log_in_color(
                        logger, "white", "info", "EXIT _satisfice", self.log_stack_depth
                    )
                    return forecast_df
                else:
                    raise e

        # now go back and populate next_income_dates
        next_income_date = ""
        for f_i, row in forecast_df.iloc[::-1].iterrows():
            # print(index, row)
            forecast_df.at[f_i, "Next Income Date"] = next_income_date
            if "INCOME" in forecast_df.at[f_i, "Memo Directives"]:
                next_income_date = forecast_df.at[f_i, "Date"]

        log_in_color(
            logger, "white", "info", forecast_df.to_string(), self.log_stack_depth
        )
        self.log_stack_depth -= 1
        log_in_color(logger, "white", "info", "EXIT _satisfice", self.log_stack_depth)
        return forecast_df  # _satisfice_success = True

    # @profile
    def _computeOptimalForecast(
        self,
        start_date_YYYYMMDD,
        end_date_YYYYMMDD,
        confirmed_df,
        proposed_df,
        deferred_df,
        skipped_df,
        account_set,
        memo_rule_set,
        raise__satisfice_failed_exception=True,
        progress_bar=None,
    ):
        log_in_color(
            logger,
            "white",
            "debug",
            "ENTER _computeOptimalForecast "
            + str(start_date_YYYYMMDD)
            + " -> "
            + str(end_date_YYYYMMDD),
            self.log_stack_depth,
        )
        self.log_stack_depth += 1

        # if not confirmed_df.empty:
        #     log_in_color(logger, 'white', 'debug', 'confirmed_df:', self.log_stack_depth)
        #     log_in_color(logger, 'white', 'debug', confirmed_df.to_string(), self.log_stack_depth)
        #
        # if not proposed_df.empty:
        #     log_in_color(logger, 'white', 'debug', 'proposed_df:', self.log_stack_depth)
        #     log_in_color(logger, 'white', 'debug', proposed_df.to_string(), self.log_stack_depth)
        # log_in_color(logger, 'magenta', 'debug', account_set.getAccounts().to_string(), self.log_stack_depth)

        # Reset index for all input DataFrames to ensure clean processing
        for df in [confirmed_df, proposed_df, deferred_df, skipped_df]:
            df.reset_index(drop=True, inplace=True)

        if confirmed_df.shape[0] > 1:
            confirmed_df = self._sortTxnsToPreventErrors(
                confirmed_df, account_set, memo_rule_set
            )

        if proposed_df.shape[0] > 1:
            proposed_df = self._sortTxnsToPreventErrors(
                proposed_df, account_set, memo_rule_set
            )

        # Generate the list of days for the forecast, excluding the first day
        all_days = pd.date_range(
            datetime.datetime.strptime(start_date_YYYYMMDD, "%Y%m%d")
            + datetime.timedelta(days=1),
            datetime.datetime.strptime(end_date_YYYYMMDD, "%Y%m%d"),
        )
        all_days = [d.strftime("%Y%m%d") for d in all_days]

        # Initialize the forecast DataFrame with the first day's account balances
        forecast_df = self._getInitialForecastRow(start_date_YYYYMMDD, account_set)

        # Attempt to _satisfice (execute priority 1 transactions for each day)
        _satisfice_df = self._satisfice(
            all_days,
            confirmed_df,
            account_set,
            memo_rule_set,
            forecast_df,
            raise__satisfice_failed_exception,
            progress_bar,
        )

        # Check if _satisfice succeeded by verifying the last date in the forecast
        _satisfice_success = _satisfice_df.tail(1)["Date"].iat[0] == end_date_YYYYMMDD

        # Update forecast DataFrame with the result of _satisfice
        forecast_df = _satisfice_df

        if _satisfice_success:
            # Log success message when _satisfice completes successfully at the top level
            if not raise__satisfice_failed_exception:
                log_in_color(logger, "white", "debug", "Satisfice succeeded.")
                log_in_color(logger, "white", "debug", _satisfice_df.to_string())

            # Not sure if this try block is needed
            try:

                # Assess potential optimizations across all transaction levels
                forecast_df, skipped_df, confirmed_df, deferred_df = (
                    self._assessPotentialOptimizations(
                        forecast_df,
                        account_set,
                        memo_rule_set,
                        confirmed_df,
                        proposed_df,
                        deferred_df,
                        skipped_df,
                        raise__satisfice_failed_exception,
                        progress_bar,
                    )
                )

            except Exception as e:
                self.log_stack_depth -= 1
                log_in_color(
                    logger,
                    "white",
                    "debug",
                    "EXIT _computeOptimalForecast",
                    self.log_stack_depth,
                )
                raise e
        else:
            # Handle _satisfice failure: clean up unprocessed transactions
            if not raise__satisfice_failed_exception:
                log_in_color(logger, "white", "debug", "Satisfice failed.")

            confirmed_df, deferred_df, skipped_df = self._cleanUpAfterFailedSatisfice(
                confirmed_df, proposed_df, deferred_df, skipped_df
            )

        # Decrement the log stack depth as we exit this method
        self.log_stack_depth -= 1

        # Return the forecast and updated DataFrames
        log_in_color(
            logger,
            "white",
            "debug",
            "EXIT _computeOptimalForecast",
            self.log_stack_depth,
        )
        return [forecast_df, skipped_df, confirmed_df, deferred_df]

    def to_json(self):
        """
        Returns a JSON string representing the ExpenseForecast object.

        #todo ExpenseForecast.to_json() say what the columns are

        :return:
        """

        # return jsonpickle.encode(self, indent=4)

        JSON_string = "{\n"

        unique_id_string = '"unique_id":"' + self.unique_id + '",\n'

        # if self.start_ts is not None:
        # if hasattr(self,'start_ts'):
        if self.start_ts is not None:
            start_ts_string = '"start_ts":"' + str(self.start_ts) + '",\n'
            end_ts_string = '"end_ts":"' + str(self.end_ts) + '",\n'
        else:
            start_ts_string = '"start_ts":"None",\n'
            end_ts_string = '"end_ts":"None",\n'

        start_date_string = '"start_date_YYYYMMDD":' + self.start_date_YYYYMMDD + ",\n"
        end_date_string = '"end_date_YYYYMMDD":' + self.end_date_YYYYMMDD + ",\n"

        memo_rule_set_string = (
            '"initial_memo_rule_set":' + self.initial_memo_rule_set.to_json() + ","
        )
        initial_account_set_string = (
            '"initial_account_set":' + self.initial_account_set.to_json() + ","
        )
        initial_budget_set_string = (
            '"initial_budget_set":' + self.initial_budget_set.to_json() + ","
        )

        if self.start_ts is None:
            forecast_df_string = '"forecast_df":"None",\n'
            skipped_df_string = '"skipped_df":"None",\n'
            confirmed_df_string = '"confirmed_df":"None",\n'
            deferred_df_string = '"deferred_df":"None",\n'
        else:
            tmp__forecast_df = self.forecast_df.copy()
            tmp__skipped_df = self.skipped_df.copy()
            tmp__confirmed_df = self.confirmed_df.copy()
            tmp__deferred_df = self.deferred_df.copy()

            # standardize decimal points

            # todo every value should have a decimal
            for i in range(1, len(tmp__forecast_df.columns) - 2):
                column_name = tmp__forecast_df.columns[i]
                tmp__forecast_df[column_name] = [
                    "{:.2f}".format(v) for v in tmp__forecast_df[column_name]
                ]

            tmp__forecast_df["Date"] = tmp__forecast_df["Date"].astype(str)
            if tmp__skipped_df.shape[0] > 0:
                tmp__skipped_df["Date"] = tmp__skipped_df["Date"].astype(str)
            tmp__confirmed_df["Date"] = tmp__confirmed_df["Date"].astype(str)
            if tmp__deferred_df.shape[0] > 0:
                tmp__deferred_df["Date"] = tmp__deferred_df["Date"].astype(str)

            normalized_forecast_df_JSON_string = tmp__forecast_df.to_json(
                orient="records", date_format="iso"
            )
            normalized_skipped_df_JSON_string = tmp__skipped_df.to_json(
                orient="records", date_format="iso"
            )
            normalized_confirmed_df_JSON_string = tmp__confirmed_df.to_json(
                orient="records", date_format="iso"
            )
            normalized_deferred_df_JSON_string = tmp__deferred_df.to_json(
                orient="records", date_format="iso"
            )

            forecast_df_string = (
                '"forecast_df":' + normalized_forecast_df_JSON_string + ",\n"
            )
            skipped_df_string = (
                '"skipped_df":' + normalized_skipped_df_JSON_string + ",\n"
            )
            confirmed_df_string = (
                '"confirmed_df":' + normalized_confirmed_df_JSON_string + ",\n"
            )
            deferred_df_string = (
                '"deferred_df":' + normalized_deferred_df_JSON_string + ",\n"
            )

        JSON_string += unique_id_string
        JSON_string += '"forecast_set_name":"' + self.forecast_set_name + '",\n'
        JSON_string += '"forecast_name":"' + self.forecast_name + '",\n'

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

        account_milestone_string = jsonpickle.encode(
            self.account_milestone_results, indent=4, unpicklable=False, make_refs=False
        )

        memo_milestone_string = jsonpickle.encode(
            self.memo_milestone_results, indent=4, unpicklable=False, make_refs=False
        )

        composite_milestone_string = jsonpickle.encode(
            self.composite_milestone_results,
            indent=4,
            unpicklable=False,
            make_refs=False,
        )

        JSON_string += '"milestone_set":' + self.milestone_set.to_json()

        JSON_string += ",\n"
        JSON_string += '"account_milestone_results":' + account_milestone_string + ",\n"
        JSON_string += '"memo_milestone_results":' + memo_milestone_string + ",\n"
        JSON_string += '"composite_milestone_results":' + composite_milestone_string

        JSON_string += "}"

        # to pretty print
        JSON_string = json.dumps(json.loads(JSON_string), indent=4)

        return JSON_string

    def to_html(self):
        # todo consider adding commas to long numbers
        # res = ('{:,}'.format(test_num))
        return self.forecast_df.to_html()

    def compute_forecast_difference(
        self,
        forecast_df,
        forecast2_df,
        label="forecast_difference",
        make_plots=False,
        plot_directory=".",
        return_type="dataframe",
        require_matching_columns=False,
        require_matching_date_range=False,
        append_expected_values=False,
        diffs_only=False,
    ):

        forecast_df["Date"] = forecast_df.Date.apply(
            lambda x: datetime.datetime.strptime(x, "%Y%m%d"), 0
        )
        # forecast2_df['Date'] = forecast_df.Date.apply(lambda x: datetime.datetime.strptime(x, '%Y%m%d'), 0)

        forecast_df.reset_index(inplace=True, drop=True)
        forecast2_df.reset_index(inplace=True, drop=True)

        forecast_df = forecast_df.reindex(sorted(forecast_df.columns), axis=1)
        forecast2_df = forecast2_df.reindex(sorted(forecast2_df.columns), axis=1)

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
                print(
                    "ERROR: ATTEMPTED TO TAKE DIFF OF FORECASTS WITH DIFFERENT COLUMNS"
                )
                print("# Check Number of Columns:")
                print("self.forecast_df.shape[1]:" + str(self.forecast_df.shape[1]))
                print("forecast2_df.shape[1]....:" + str(forecast2_df.shape[1]))
                print("")
                print("# Check Column Names:")
                print("In 1 not in 2:")
                print(
                    str(
                        [
                            cname
                            for cname in forecast_df.columns
                            if cname not in forecast2_df.columns
                        ]
                    )
                )
                print("In 2 not in 1:")
                print(
                    str(
                        [
                            cname
                            for cname in forecast2_df.columns
                            if cname not in forecast_df.columns
                        ]
                    )
                )
                print("")
                raise e

        if require_matching_date_range:
            try:
                assert min(forecast_df["Date"]) == min(forecast2_df["Date"])
                assert max(forecast_df["Date"]) == max(forecast2_df["Date"])
            except Exception as e:
                print(
                    "ERROR: ATTEMPTED TO TAKE DIFF OF FORECASTS WITH DIFFERENT DATE RANGE"
                )
                print(
                    "LHS: "
                    + str(min(forecast_df["Date"]))
                    + " - "
                    + str(max(forecast_df["Date"]))
                )
                print(
                    "RHS: "
                    + str(min(forecast2_df["Date"]))
                    + " - "
                    + str(max(forecast2_df["Date"]))
                )
                raise e
        else:
            overlapping_date_range = set(forecast_df["Date"]) & set(
                forecast2_df["Date"]
            )
            LHS_only_dates = set(forecast_df["Date"]) - set(forecast2_df["Date"])
            RHS_only_dates = set(forecast2_df["Date"]) - set(forecast_df["Date"])
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
                if cname == "Date":
                    continue
                elif cname == "Memo":
                    LHS_example_row[cname] = ""
                else:
                    LHS_example_row[cname] = float("nan")

            for dt in RHS_only_dates:
                LHS_zero_row_to_add = LHS_example_row.copy()
                LHS_zero_row_to_add["Date"] = dt
                forecast_df = pd.concat([LHS_zero_row_to_add, forecast_df])
            forecast_df.sort_values(by="Date", inplace=True, ascending=True)

            RHS_example_row = pd.DataFrame(forecast2_df.iloc[0, :]).copy()
            for cname in RHS_example_row.columns:
                if cname == "Date":
                    continue
                elif cname == "Memo":
                    RHS_example_row[cname] = ""
                else:
                    RHS_example_row[cname] = float("nan")

            for dt in LHS_only_dates:
                RHS_zero_row_to_add = RHS_example_row.copy()
                RHS_zero_row_to_add["Date"] = dt
                forecast2_df = pd.concat([RHS_zero_row_to_add, self.forecast_df])
            forecast2_df.sort_values(by="Date", inplace=True, ascending=True)

        if diffs_only:
            return_df = forecast_df[["Date", "Memo"]].copy()
        else:
            return_df = forecast_df.copy()
        return_df.reset_index(inplace=True, drop=True)

        # print(return_df.columns)
        # print('BEFORE return_df:\n' + return_df.to_string())

        relevant_column_names__set = set(forecast_df.columns) - set(
            ["Date", "Next Income Date", "Memo", "Memo Directives"]
        )
        # print('relevant_column_names__set:'+str(relevant_column_names__set))
        assert set(forecast_df.columns) == set(forecast2_df)
        for c in relevant_column_names__set:
            new_column_name = str(c) + " (Diff) "
            # print('new_column_name:'+str(new_column_name))
            res = pd.DataFrame(forecast2_df[c] - forecast_df[c])
            # res = forecast2_df[c].sub(self.forecast_df[c])
            res.reset_index(inplace=True, drop=True)
            # print('res:'+str(res))
            return_df[new_column_name] = res

        if append_expected_values:
            for cname in forecast2_df.columns:
                if cname in ["Memo", "Date", "Memo Directives"]:
                    continue
                return_df[cname + " (Expected)"] = forecast2_df[cname]

        return_df.index = return_df["Date"]

        if make_plots:
            pass  # todo draw plots

        return_df = return_df.reindex(sorted(return_df.columns), axis=1)

        return return_df

    def to_excel(self, output_dir):

        # first page, run parameters
        summary_df = self.getSummaryPageForExcelLandingPageDF()
        account_set_df = self.initial_account_set.getAccounts()
        budget_set_df = self.initial_budget_set.getBudgetItems()
        memo_rule_set_df = self.initial_memo_rule_set.getMemoRules()
        choose_one_set_df = pd.DataFrame()  # todo
        account_milestones_df = self.milestone_set.getAccountMilestonesDF()
        memo_milestones_df = self.milestone_set.getMemoMilestonesDF()
        composite_milestones_df = self.milestone_set.getCompositeMilestonesDF()
        milestone_results_df = self.getMilestoneResultsDF()

        with pd.ExcelWriter(
            output_dir + "/Forecast_" + self.unique_id + ".xlsx", engine="xlsxwriter"
        ) as writer:
            summary_df.to_excel(writer, sheet_name="Summary", index=False)
            for column in summary_df:
                column_length = max(
                    summary_df[column].astype(str).map(len).max(), len(column)
                )
                col_idx = summary_df.columns.get_loc(column)
                writer.sheets["Summary"].set_column(col_idx, col_idx, column_length)

            account_set_df.to_excel(writer, sheet_name="AccountSet", index=False)
            for column in account_set_df:
                column_length = max(
                    account_set_df[column].astype(str).map(len).max(), len(column)
                )
                col_idx = account_set_df.columns.get_loc(column)
                writer.sheets["AccountSet"].set_column(col_idx, col_idx, column_length)

            budget_set_df.to_excel(writer, sheet_name="BudgetSet", index=False)
            for column in budget_set_df:
                column_length = max(
                    budget_set_df[column].astype(str).map(len).max(), len(column)
                )
                col_idx = budget_set_df.columns.get_loc(column)
                writer.sheets["BudgetSet"].set_column(col_idx, col_idx, column_length)

            memo_rule_set_df.to_excel(writer, sheet_name="MemoRuleSet", index=False)
            for column in memo_rule_set_df:
                column_length = max(
                    memo_rule_set_df[column].astype(str).map(len).max(), len(column)
                )
                col_idx = memo_rule_set_df.columns.get_loc(column)
                writer.sheets["MemoRuleSet"].set_column(col_idx, col_idx, column_length)

            choose_one_set_df.to_excel(writer, sheet_name="ChooseOneSet", index=False)
            for column in choose_one_set_df:
                column_length = max(
                    choose_one_set_df[column].astype(str).map(len).max(), len(column)
                )
                col_idx = choose_one_set_df.columns.get_loc(column)
                writer.sheets["ChooseOneSet"].set_column(
                    col_idx, col_idx, column_length
                )

            account_milestones_df.to_excel(
                writer, sheet_name="AccountMilestones", index=False
            )
            for column in account_milestones_df:
                column_length = max(
                    account_milestones_df[column].astype(str).map(len).max(),
                    len(column),
                )
                col_idx = account_milestones_df.columns.get_loc(column)
                writer.sheets["AccountMilestones"].set_column(
                    col_idx, col_idx, column_length
                )

            memo_milestones_df.to_excel(
                writer, sheet_name="MemoMilestones", index=False
            )
            for column in memo_milestones_df:
                column_length = max(
                    memo_milestones_df[column].astype(str).map(len).max(), len(column)
                )
                col_idx = memo_milestones_df.columns.get_loc(column)
                writer.sheets["MemoMilestones"].set_column(
                    col_idx, col_idx, column_length
                )

            composite_milestones_df.to_excel(
                writer, sheet_name="CompositeMilestones", index=False
            )
            for column in composite_milestones_df:
                column_length = max(
                    composite_milestones_df[column].astype(str).map(len).max(),
                    len(column),
                )
                col_idx = composite_milestones_df.columns.get_loc(column)
                writer.sheets["CompositeMilestones"].set_column(
                    col_idx, col_idx, column_length
                )

            if hasattr(self, "forecast_df"):
                self.forecast_df.to_excel(writer, sheet_name="Forecast", index=False)
                for column in self.forecast_df:
                    column_length = max(
                        self.forecast_df[column].astype(str).map(len).max(), len(column)
                    )
                    col_idx = self.forecast_df.columns.get_loc(column)
                    writer.sheets["Forecast"].set_column(
                        col_idx, col_idx, column_length
                    )

                self.skipped_df.to_excel(writer, sheet_name="Skipped", index=False)
                for column in self.skipped_df:
                    column_length = max(
                        self.skipped_df[column].astype(str).map(len).max(), len(column)
                    )
                    col_idx = self.skipped_df.columns.get_loc(column)
                    writer.sheets["Skipped"].set_column(col_idx, col_idx, column_length)

                self.confirmed_df.to_excel(writer, sheet_name="Confirmed", index=False)
                for column in self.confirmed_df:
                    column_length = max(
                        self.confirmed_df[column].astype(str).map(len).max(),
                        len(column),
                    )
                    col_idx = self.confirmed_df.columns.get_loc(column)
                    writer.sheets["Confirmed"].set_column(
                        col_idx, col_idx, column_length
                    )

                self.deferred_df.to_excel(writer, sheet_name="Deferred", index=False)
                for column in self.deferred_df:
                    column_length = max(
                        self.deferred_df[column].astype(str).map(len).max(), len(column)
                    )
                    col_idx = self.deferred_df.columns.get_loc(column)
                    writer.sheets["Deferred"].set_column(
                        col_idx, col_idx, column_length
                    )

                milestone_results_df.to_excel(
                    writer, sheet_name="Milestone Results", index=False
                )
                for column in milestone_results_df:
                    column_length = max(
                        milestone_results_df[column].astype(str).map(len).max(),
                        len(column),
                    )
                    col_idx = milestone_results_df.columns.get_loc(column)
                    writer.sheets["Milestone Results"].set_column(
                        col_idx, col_idx, column_length
                    )

    def getSummaryPageForExcelLandingPageDF(self):

        if hasattr(self, "forecast_df"):
            return_df = pd.DataFrame(
                {
                    "start_date_YYYYMMDD": [self.start_date_YYYYMMDD],
                    "end_date_YYYYMMDD": [self.end_date_YYYYMMDD],
                    "unique_id": [self.unique_id],
                    "start_ts": [self.start_ts],
                    "end_ts": [self.end_ts],
                }
            ).T
        else:
            return_df = pd.DataFrame(
                {
                    "start_date_YYYYMMDD": [self.start_date_YYYYMMDD],
                    "end_date_YYYYMMDD": [self.end_date_YYYYMMDD],
                    "unique_id": [self.unique_id],
                    "start_ts": [None],
                    "end_ts": [None],
                }
            ).T

        return_df.reset_index(inplace=True)
        return_df = return_df.rename(columns={"index": "Field", 0: "Value"})
        return return_df

    def evaluateAccountMilestone(self, account_name, min_balance, max_balance):
        log_in_color(
            logger,
            "yellow",
            "debug",
            "ENTER evaluateAccountMilestone("
            + str(account_name)
            + ","
            + str(min_balance)
            + ","
            + str(max_balance)
            + ")",
            self.log_stack_depth,
        )
        self.log_stack_depth += 1
        account_info = self.initial_account_set.getAccounts()
        account_base_names = [a.split(":")[0] for a in account_info.Name]
        row_sel_vec = [a == account_name for a in account_base_names]

        relevant_account_info_rows_df = account_info[row_sel_vec]
        log_in_color(logger, "yellow", "debug", "relevant_account_info_rows_df:")
        log_in_color(
            logger, "yellow", "debug", relevant_account_info_rows_df.to_string()
        )

        # this df should be either 1 or 2 rows, but have same account type either way
        try:
            assert relevant_account_info_rows_df.Name.unique().shape[0] == 1
        except Exception as e:
            print(e)

        if relevant_account_info_rows_df.shape[0] == 1:  # case for checking and savings
            col_sel_vec = (
                self.forecast_df.columns
                == relevant_account_info_rows_df.head(1)["Name"].iat[0]
            )
            col_sel_vec[0] = True
            relevant_time_series_df = self.forecast_df.iloc[:, col_sel_vec]

            # a valid success date stays valid until the end
            found_a_valid_success_date = False
            success_date = "None"
            for index, row in relevant_time_series_df.iterrows():
                current_value = relevant_time_series_df.iloc[index, 1]
                if (
                    (min_balance <= current_value) & (current_value <= max_balance)
                ) and not found_a_valid_success_date:
                    found_a_valid_success_date = True
                    success_date = row.Date
                    log_in_color(
                        logger,
                        "yellow",
                        "debug",
                        "success_date:" + str(success_date),
                        self.log_stack_depth,
                    )
                elif (min_balance > current_value) | (current_value > max_balance):
                    found_a_valid_success_date = False
                    success_date = "None"
                    log_in_color(
                        logger,
                        "yellow",
                        "debug",
                        "success_date:None",
                        self.log_stack_depth,
                    )

        elif relevant_account_info_rows_df.shape[0] == 2:  # case for credit and loan
            curr_stmt_bal_acct_name = relevant_account_info_rows_df.iloc[0, 0]
            prev_stmt_bal_acct_name = relevant_account_info_rows_df.iloc[1, 0]

            # log_in_color(logger, 'yellow', 'debug', 'curr_stmt_bal_acct_name:')
            # log_in_color(logger, 'yellow', 'debug', curr_stmt_bal_acct_name)
            # log_in_color(logger, 'yellow', 'debug', 'prev_stmt_bal_acct_name:')
            # log_in_color(logger, 'yellow', 'debug', prev_stmt_bal_acct_name)

            col_sel_vec = self.forecast_df.columns == curr_stmt_bal_acct_name
            col_sel_vec = col_sel_vec | (
                self.forecast_df.columns == prev_stmt_bal_acct_name
            )
            col_sel_vec[0] = True  # Date

            # log_in_color(logger, 'yellow', 'debug', 'col_sel_vec:')
            # log_in_color(logger, 'yellow', 'debug', col_sel_vec)

            relevant_time_series_df = self.forecast_df.iloc[:, col_sel_vec]

            # a valid success date stays valid until the end
            found_a_valid_success_date = False
            success_date = "None"
            for index, row in relevant_time_series_df.iterrows():
                current_value = (
                    relevant_time_series_df.iloc[index, 1]
                    + relevant_time_series_df.iloc[index, 2]
                )
                if (
                    (min_balance <= current_value) & (current_value <= max_balance)
                ) and not found_a_valid_success_date:
                    found_a_valid_success_date = True
                    success_date = row.Date
                    log_in_color(
                        logger,
                        "yellow",
                        "debug",
                        "success_date:" + str(success_date),
                        self.log_stack_depth,
                    )
                elif (min_balance > current_value) | (current_value > max_balance):
                    found_a_valid_success_date = False
                    success_date = "None"
                    log_in_color(
                        logger,
                        "yellow",
                        "debug",
                        "success_date:None",
                        self.log_stack_depth,
                    )

        # Summary lines
        elif account_name in (
            "Marginal Interest",
            "Net Gain",
            "Net Loss",
            "Net Worth",
            "Loan Total",
            "CC Debt Total",
            "Liquid Total",
        ):
            col_sel_vec = self.forecast_df.columns == account_name
            col_sel_vec[0] = True
            relevant_time_series_df = self.forecast_df.iloc[:, col_sel_vec]

            # a valid success date stays valid until the end
            found_a_valid_success_date = False
            success_date = "None"
            for index, row in relevant_time_series_df.iterrows():
                current_value = relevant_time_series_df.iloc[index, 1]
                if (
                    (min_balance <= current_value) & (current_value <= max_balance)
                ) and not found_a_valid_success_date:
                    found_a_valid_success_date = True
                    success_date = row.Date
                    log_in_color(
                        logger,
                        "yellow",
                        "debug",
                        "success_date:" + str(success_date),
                        self.log_stack_depth,
                    )
                elif (min_balance > current_value) | (current_value > max_balance):
                    found_a_valid_success_date = False
                    success_date = "None"
                    log_in_color(
                        logger,
                        "yellow",
                        "debug",
                        "success_date:None",
                        self.log_stack_depth,
                    )
        else:
            raise ValueError(
                "undefined edge case in ExpenseForecast::evaulateAccountMilestone" ""
            )

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
        log_in_color(
            logger,
            "yellow",
            "debug",
            "EXIT evaluateAccountMilestone("
            + str(account_name)
            + ","
            + str(min_balance)
            + ","
            + str(max_balance)
            + ") "
            + str(success_date),
            self.log_stack_depth,
        )
        return success_date

    def evaulateMemoMilestone(self, memo_regex):
        log_in_color(
            logger,
            "yellow",
            "debug",
            "ENTER evaluateMemoMilestone(" + str(memo_regex) + ")",
            self.log_stack_depth,
        )
        self.log_stack_depth += 1
        for forecast_index, forecast_row in self.forecast_df.iterrows():
            m = re.search(memo_regex, forecast_row.Memo)
            if m is not None:
                self.log_stack_depth -= 1
                log_in_color(
                    logger,
                    "yellow",
                    "debug",
                    "EXIT evaluateMemoMilestone(" + str(memo_regex) + ")",
                    self.log_stack_depth,
                )
                return forecast_row.Date

        self.log_stack_depth -= 1
        log_in_color(
            logger,
            "yellow",
            "debug",
            "EXIT evaluateMemoMilestone(" + str(memo_regex) + ")",
            self.log_stack_depth,
        )
        return "None"

    def evaluateCompositeMilestone(
        self, list_of_account_milestones, list_of_memo_milestones
    ):
        log_in_color(
            logger,
            "yellow",
            "debug",
            "ENTER evaluateCompositeMilestone()",
            self.log_stack_depth,
        )
        self.log_stack_depth += 1
        # list_of_account_milestones is lists of 3-tuples that are (string,float,float) for parameters

        # todo composite milestones may contain some milestones that arent listed in the composite #https://github.com/hdickie/expense_forecast/issues/22

        num_of_acct_milestones = len(list_of_account_milestones)
        num_of_memo_milestones = len(list_of_memo_milestones)
        account_milestone_dates = []
        memo_milestone_dates = []

        for i in range(0, num_of_acct_milestones):
            account_milestone = list_of_account_milestones[i]
            am_result = self.evaluateAccountMilestone(
                account_milestone.account_name,
                account_milestone.min_balance,
                account_milestone.max_balance,
            )
            if (
                am_result is None
            ):  # disqualified immediately because success requires ALL
                self.log_stack_depth -= 1
                log_in_color(
                    logger,
                    "yellow",
                    "debug",
                    "EXIT evaluateCompositeMilestone() None",
                    self.log_stack_depth,
                )
                return None
            account_milestone_dates.append(am_result)

        for i in range(0, num_of_memo_milestones):
            memo_milestone = list_of_memo_milestones[i]
            mm_result = self.evaulateMemoMilestone(memo_milestone.memo_regex)
            if (
                mm_result is None
            ):  # disqualified immediately because success requires ALL
                self.log_stack_depth -= 1
                log_in_color(
                    logger,
                    "yellow",
                    "debug",
                    "EXIT evaluateCompositeMilestone() None",
                    self.log_stack_depth,
                )
                return None
            memo_milestone_dates.append(mm_result)

        result_date = max(account_milestone_dates + memo_milestone_dates)
        log_in_color(
            logger,
            "yellow",
            "debug",
            "EXIT evaluateCompositeMilestone() " + str(result_date),
            self.log_stack_depth,
        )
        self.log_stack_depth -= 1
        return result_date

    def evaluateMilestones(self):

        account_milestone_results = {}
        for a_m in self.milestone_set.account_milestones:
            res = self.evaluateAccountMilestone(
                a_m.account_name, a_m.min_balance, a_m.max_balance
            )
            account_milestone_results[a_m.milestone_name] = res
        self.account_milestone_results = account_milestone_results

        memo_milestone_results = {}
        for m_m in self.milestone_set.memo_milestones:
            res = self.evaulateMemoMilestone(m_m.memo_regex)
            memo_milestone_results[m_m.milestone_name] = res
        self.memo_milestone_results = memo_milestone_results

        composite_milestone_results = {}
        for c_m in self.milestone_set.composite_milestones:
            res = self.evaluateCompositeMilestone(
                c_m.account_milestones, c_m.memo_milestones
            )
            composite_milestone_results[c_m.milestone_name] = res
        self.composite_milestone_results = composite_milestone_results


# if __name__ == "__main__": import doctest ; doctest.testmod()
if __name__ == "__main__":
    pass


#
#
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_p1_cc_txn_on_billing_date-account_set2-budget_set2-memo_rule_set2-20000101-20000103-milestone_set2-expected_result_df2]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_p2_and_3__expect_defer-account_set7-budget_set7-memo_rule_set7-20000101-20000103-milestone_set7-expected_result_df7]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_p7__additional_loan_payment__amt_560-account_set22-budget_set22-memo_rule_set22-20000101-20000103-milestone_set22-expected_result_df22]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_p7__additional_loan_payment__amt_1900-account_set24-budget_set24-memo_rule_set24-20000101-20000103-milestone_set24-expected_result_df24]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_p7__additional_loan_payment__amt_overpay-account_set25-budget_set25-memo_rule_set25-20000101-20000103-milestone_set25-expected_result_df25]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_cc_advance_minimum_payment_in_1_payment_pay_over_minimum-account_set26-budget_set26-memo_rule_set26-20000110-20000113-milestone_set26-expected_result_df26]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_cc_advance_minimum_payment_in_1_payment_pay_under_minimum-account_set27-budget_set27-memo_rule_set27-20000110-20000113-milestone_set27-expected_result_df27]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_cc_advance_minimum_payment_in_1_payment_pay_exact_minimum-account_set28-budget_set28-memo_rule_set28-20000110-20000113-milestone_set28-expected_result_df28]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_cc_two_additional_payments_on_due_date__curr_only-account_set33-budget_set33-memo_rule_set33-20000111-20000113-milestone_set33-expected_result_df33]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_cc_single_additional_payment_day_before__prev_only-account_set35-budget_set35-memo_rule_set35-20000110-20000113-milestone_set35-expected_result_df35]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_cc_two_additional_payments_day_before__prev_only-account_set36-budget_set36-memo_rule_set36-20000110-20000113-milestone_set36-expected_result_df36]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_cc_single_additional_payment_day_before_OVERPAY__prev_only-account_set37-budget_set37-memo_rule_set37-20000110-20000113-milestone_set37-expected_result_df37]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_cc_two_additional_payments_day_before_OVERPAY__prev_only-account_set38-budget_set38-memo_rule_set38-20000110-20000113-milestone_set38-expected_result_df38]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_cc_single_additional_payment_day_before__curr_only-account_set39-budget_set39-memo_rule_set39-20000110-20000113-milestone_set39-expected_result_df39]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_cc_two_additional_payments_day_before__curr_only-account_set40-budget_set40-memo_rule_set40-20000110-20000113-milestone_set40-expected_result_df40]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_cc_single_additional_payment_day_before_OVERPAY__curr_only-account_set41-budget_set41-memo_rule_set41-20000110-20000113-milestone_set41-expected_result_df41]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_cc_two_additional_payments_day_before_OVERPAY__curr_only-account_set42-budget_set42-memo_rule_set42-20000110-20000113-milestone_set42-expected_result_df42]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_cc_single_additional_payment_day_before__curr_prev-account_set43-budget_set43-memo_rule_set43-20000110-20000113-milestone_set43-expected_result_df43]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_cc_single_additional_payment_day_before_OVERPAY__curr_prev-account_set44-budget_set44-memo_rule_set44-20000110-20000113-milestone_set44-expected_result_df44]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_distal_propagation__prev_only-account_set45-budget_set45-memo_rule_set45-20000110-20000214-milestone_set45-expected_result_df45]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_distal_propagation_multiple__prev_only-account_set46-budget_set46-memo_rule_set46-20000110-20000214-milestone_set46-expected_result_df46]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_distal_propagation__curr_only-account_set47-budget_set47-memo_rule_set47-20000110-20000214-milestone_set47-expected_result_df47]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_distal_propagation_multiple__curr_only-account_set48-budget_set48-memo_rule_set48-20000110-20000214-milestone_set48-expected_result_df48]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_distal_propagation__curr_prev-account_set49-budget_set49-memo_rule_set49-20000110-20000214-milestone_set49-expected_result_df49]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_distal_propagation_multiple__curr_prev-account_set50-budget_set50-memo_rule_set50-20000110-20000214-milestone_set50-expected_result_df50]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_business_case[test_cc_interest_accrued_reaches_0-account_set51-budget_set51-memo_rule_set51-20000110-20000214-milestone_set51-expected_result_df51]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_evaluate_account_milestone[test_account_milestone-account_set0-budget_set0-memo_rule_set0-20000101-20000103-milestone_set0-account_milestone_names0-expected_milestone_dates0]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_evaluate_memo_milestone[test_memo_milestone-account_set0-budget_set0-memo_rule_set0-20000101-20000103-milestone_set0-memo_milestone_names0-expected_milestone_dates0]
# FAILED test_ExpenseForecast__unit_test.py::TestExpenseForecastMethods::test_evaluate_composite_milestone[test composite milestone-account_set0-budget_set0-memo_rule_set0-20000101-20000103-milestone_set0-composite_milestone_names0-expected_milestone_dates0]
# =============================================== 31 failed, 170 passed, 165 warnings in 279.36s (0:04:39) ==========
#
#
#
# Chat GPT had some GREAT advice regarding coverage!!!
# apparently you can end a line with '# pragma: no cover' and it will not get counted in coverage
# also use asserts instead of if branches that are never crossed!!
#
#
# Name                              Stmts   Miss  Cover
# -----------------------------------------------------
# Account.py                           92      6    93%
# AccountMilestone.py                  13      1    92%
# AccountSet.py                       521    119    77%
# BudgetItem.py                        59      3    95%
# BudgetSet.py                         80     19    76%
# CompositeMilestone.py                24      1    96%
# ExpenseForecast.py                 4180   2364    43%
# ForecastHandler.py                 1376   1315     4%
# MemoMilestone.py                     14      1    93%
# MemoRule.py                          51      3    94%
# MemoRuleSet.py                       83     10    88%
# MilestoneSet.py                     224    162    28%
# __init__.py                           0      0   100%
# generate_date_sequence.py            42      1    98%
# log_methods.py                      141     52    63%
# multithread_test.py                  27     20    26%
# test_Account__unit_test.py                      14      0   100%
# test_AccountMilestone__unit_test.py             12      0   100%
# test_AccountSet__unit_test.py                   81     28    65%
# test_BudgetItem__unit_test.py                   13      0   100%
# test_BudgetSet__unit_test.py                    42      0   100%
# test_CompositeMilestone__unit_test.py           20      0   100%
# test_ExpenseForecast__unit_test.py             216     41    81%
# test_ForecastHandler__unit_test.py               0      0   100%
# test_ForecastRunner__unit_test.py                0      0   100%
# test_ForecastSet__unit_test.py                   0      0   100%
# test_MemoMilestone__unit_test.py                10      0   100%
# test_MemoRule.py                     11      0   100%
# test_MemoRuleSet.py                  68      0   100%
# test_MilestoneSet__unit_test.py                  0      0   100%
# test_calculateMinimumPayment__unit_test.py     108    104     4%
# test_ef_cli__unit_test.py                        0      0   100%
# tqdm_test.py                         14      0   100%
# -----------------------------------------------------
# TOTAL                              7536   4250    44%
#

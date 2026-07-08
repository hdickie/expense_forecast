from expense_forecast.AccountSet import AccountBoundaryError, AccountSet
from expense_forecast.BudgetSet import BudgetSet
from expense_forecast.ForecastSetInitialConditions import ForecastSetInitialConditions
from expense_forecast.MemoRuleSet import MemoRuleSet 
from expense_forecast.MilestoneSet import MilestoneSet 
from expense_forecast.ExpenseForecastInitialConditions import ExpenseForecastInitialConditions 
from expense_forecast.ExpenseForecastResult import ExpenseForecastResult 
from expense_forecast.MilestoneTriggeredForecastTransition import MilestoneTriggeredForecastTransition

import hashlib
import hashlib
import json
from datetime import date
from decimal import Decimal
from typing import Any
import datetime
import os
import tempfile
from pathlib import Path
from expense_forecast.log_methods import log_in_color
import logging
import tqdm

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault(
    "MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "expense_forecast_mplconfig")
)
os.environ.setdefault(
    "XDG_CACHE_HOME", os.path.join(tempfile.gettempdir(), "expense_forecast_xdgcache")
)
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["XDG_CACHE_HOME"], exist_ok=True)

import matplotlib
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
import re
import copy 
from expense_forecast.generate_date_sequence import generate_date_sequence
from matplotlib.pyplot import figure

try:
    import plotly.graph_objects as go
except ImportError:
    go = None

matplotlib.rcParams["figure.facecolor"] = "#d1d5db"
matplotlib.rcParams["axes.facecolor"] = "#e5e7eb"
matplotlib.rcParams["savefig.facecolor"] = "#d1d5db"

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s - %(levelname)-8s - %(message)s")
fileHandler = logging.FileHandler(__name__ + ".log", mode="w")
fileHandler.setFormatter(formatter)
streamHandler = logging.StreamHandler()
streamHandler.setFormatter(formatter)
logger.setLevel(logging.DEBUG) 
logger.handlers.clear()
logger.addHandler(fileHandler)
logger.addHandler(streamHandler)
logger.propagate = False

# Show all decimal places in data frames
pd.set_option("display.precision", 2)
ROUNDING_ERROR_TOLERANCE = (
    0.0000000001  # 10 places? overkill but I want to see if it works
)
def _stable_df_payload(df):
    return (
        df.sort_index(axis=1)
        .reset_index(drop=True)
        .to_dict(orient="records")
    )

class ForecastHandler:
    # def __init__(cls):
    #     cls.forecast_set = None
    #     cls.account_set = None
    #     cls.budget_set = None
    #     cls.memo_rule_set = None
    #     cls.milestone_set = None

    # def load_forecast_set(cls, forecast_set: ForecastSet):
    #     cls.forecast_set = forecast_set

    # def load_account_set(cls, account_set: AccountSet):
    #     cls.account_set = account_set

    # def load_budget_set(cls, budget_set: BudgetSet):
    #     cls.budget_set = budget_set

    # def load_memo_rule_set(cls, memo_rule_set: MemoRuleSet):
    #     cls.memo_rule_set = memo_rule_set

    # def load_milestone_set(cls, milestone_set: MilestoneSet):
    #     cls.milestone_set = milestone_set

    @staticmethod
    def _normalize_date_value(value):
        if pd.isnull(value):
            return value
        if isinstance(value, pd.Timestamp):
            return value.date()
        if isinstance(value, datetime.datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            stripped_value = value.strip()
            if stripped_value == "":
                return value
            for date_format in ["%Y%m%d", "%Y-%m-%d"]:
                try:
                    return datetime.datetime.strptime(
                        stripped_value, date_format
                    ).date()
                except ValueError:
                    pass
        return value

    @classmethod
    def _normalize_dataframe_date_column(cls, dataframe):
        if "Date" in dataframe.columns:
            dataframe["Date"] = dataframe["Date"].apply(cls._normalize_date_value)
        return dataframe

    @staticmethod
    def _is_empty_account_endpoint(value):
        return value is None or value == "None"

    @staticmethod
    def _roundForecastOutput(forecast_df, decimals=2):
        forecast_df = forecast_df.copy()
        excluded_columns = {"Date", "Next Income Date", "Memo", "Memo Directives"}

        for column in forecast_df.columns:
            if column in excluded_columns:
                continue

            numeric_values = pd.to_numeric(forecast_df[column], errors="coerce")
            if numeric_values.notna().all():
                forecast_df[column] = numeric_values.round(decimals)

        return forecast_df

    @classmethod
    def runForecast(cls, 
                    IO: ExpenseForecastInitialConditions, 
                    milestone_set: MilestoneSet, 
                    include_debug_columns = False
                    ) -> ExpenseForecastResult:
        # print('Starting Forecast #'+str(cls.unique_id))
        log_stack_depth = 0
        cls.start_ts = datetime.datetime.now()
        cls.initial_account_set = IO.initial_account_set
        cls.initial_budget_set = IO.initial_budget_set
        cls.initial_memo_rule_set = IO.initial_memo_rule_set

        log_in_color(
            logger, "white", "info", "Starting Forecast " + str(IO.unique_id)
        )

        predicted__satisfice_runtime_in_simulated_days = (IO.end_date - IO.start_date).days

        # On second thought, I would rather deal wit ha stilted progress bar than figuring out how to track progress in recursion
        no_of_p2plus_priority_levels = len(set(IO.initial_proposed_df.Priority))
        total_predicted_max_runtime_in_simulated_days = (
            predicted__satisfice_runtime_in_simulated_days
            + predicted__satisfice_runtime_in_simulated_days
            * no_of_p2plus_priority_levels
        )
        progress_bar = tqdm.tqdm(
            range(total_predicted_max_runtime_in_simulated_days),
            total=total_predicted_max_runtime_in_simulated_days,
            desc=IO.unique_id,
            disable=True,
        )  # disabled tqdm

        forecast_df, skipped_df, confirmed_df, deferred_df = (
            cls._computeOptimalForecast(
                start_date=IO.start_date,
                end_date=IO.end_date,
                confirmed_df=pd.DataFrame(IO.initial_confirmed_df, copy=True),
                proposed_df=pd.DataFrame(IO.initial_proposed_df, copy=True),
                deferred_df=pd.DataFrame(IO.initial_deferred_df, copy=True),
                skipped_df=pd.DataFrame(IO.initial_skipped_df, copy=True),
                account_set=copy.deepcopy(IO.initial_account_set), #TODO copy may not be needed here?
                memo_rule_set=copy.deepcopy(IO.initial_memo_rule_set), 
                log_stack_depth=log_stack_depth,
                raise__satisfice_failed_exception=False,
                progress_bar=progress_bar,
                include_debug_columns=include_debug_columns
            )
        )

        # Round all values in Memo and Memo Directives
        # (I think I can round other columns as needed w display.precision without changing the data)
        for index, row in forecast_df.iterrows():
            new_memo_lines = []
            for m in row["Memo"].split(";"):
                if m.strip() == "":
                    continue
                match = re.search(r".*\$(.*)\)", m)
                if match is None:
                    raise ValueError(f"Could not parse amount from memo: {m}")

                og_amt = float(match.group(1))
                new_amount = f"{og_amt:.2f}"
                # log_in_color(logger, 'white', 'debug', '(case 29) _update_memo_amount')
                new_m = cls._update_memo_amount(m, new_amount=new_amount, log_stack_depth=log_stack_depth).strip()
                new_memo_lines.append(new_m)

            new_md_lines = []
            for md in row["Memo Directives"].split(";"):
                if md.strip() == "":
                    continue
                try:
                    match = re.search(r".*\$(.*)\)", md)
                    if match is None:
                        raise ValueError("Regex did not match")
                    og_amt = float(match.group(1))
                except Exception:
                    print("Offending memo directive:", md)
                    raise
                
                new_amount = f"{og_amt:.2f}"
                # log_in_color(logger, 'white', 'debug', '(case 30) _update_memo_amount')
                new_md = cls._update_memo_amount(md, new_amount=new_amount, log_stack_depth=log_stack_depth).strip()
                new_md_lines.append(new_md)

            forecast_df.loc[index, "Memo"] = "; ".join(new_memo_lines)
            forecast_df.loc[index, "Memo Directives"] = "; ".join(new_md_lines)

        cls.forecast_df = forecast_df
        cls.skipped_df = skipped_df
        cls.confirmed_df = confirmed_df
        cls.deferred_df = deferred_df

        cls.end_ts = datetime.datetime.now()
        forecast_df = cls._appendSummaryLines(IO.initial_account_set, forecast_df, log_stack_depth=log_stack_depth)
        forecast_df = cls._roundForecastOutput(forecast_df, decimals=2)
        cls.forecast_df = forecast_df
        milestone_results = cls.evaluateMilestones(forecast_df, milestone_set, log_stack_depth=log_stack_depth)

        result_kwargs = {
            "confirmed_df": confirmed_df,
            "deferred_df": deferred_df,
            "skipped_df": skipped_df,
        }
        if milestone_set:
            result_kwargs["milestone_set"] = milestone_set
            result_kwargs["milestone_results"] = milestone_results

        R = ExpenseForecastResult(IO, forecast_df, **result_kwargs)
        log_in_color(
            logger, "white", "info", "Finished Forecast " + str(IO.unique_id)
        )
        #TODO make this conditional on a --print flag
        # log_in_color(logger, "white", "info", cls.forecast_df.to_string())
        # if play_notification_sound:
        #     notification_sounds.play_notification_sound()

        # cls.forecast_df.to_csv('./out//Forecast_' + cls.unique_id + '.csv') #this is only the forecast not the whole ExpenseForecast object
        # cls.writeToJSONFile() #this is the whole ExpenseForecast object #todo this should accept a path parameter
        return R

    
    

    # todo this could probably have a better name
    # def writeToJSONFile(cls, output_dir="./"):

    #     # cls.forecast_df.to_csv('./Forecast__'+run_ts+'.csv')
    #     log_in_color(
    #         logger,
    #         "green",
    #         "info",
    #         "Writing to " + str(output_dir) + "/Forecast_" + cls.unique_id + ".json",
    #     )
    #     print("Writing to " + str(output_dir) + "/Forecast_" + cls.unique_id + ".json")
    #     # cls.forecast_df.to_csv('./Forecast__' + run_ts + '.json')

    #     # cls.forecast_df.index = cls.forecast_df['Date']
    #     if hasattr(cls, "forecast_df"):
    #         file_name = "ForecastResult_" + cls.unique_id + ".json"
    #     else:
    #         file_name = "Forecast_" + cls.unique_id + ".json"

    #     f = open(str(output_dir) + file_name, "w")
    #     f.write(cls.to_json())
    #     f.close()

    #     # write all_data.csv  # cls.forecast_df.iloc[:,0:(cls.forecast_df.shape[1]-1)].to_csv('all_data.csv',index=False)

    #     # cls.forecast_df.to_csv('out.csv', index=False)

    @classmethod
    def _getInitialForecastRow(cls, start_date, account_set, include_debug_columns=False):
        # print('ENTER _getInitialForecastRow')
        min_sched_date = start_date
        account_balances = account_set.getForecastAccountBalances(
            include_debug_columns=include_debug_columns
        )

        forecast_row_df = pd.DataFrame(
            [
                {
                    "Date": min_sched_date,
                    **account_balances,
                    "Next Income Date": "",
                    "Memo Directives": "",
                    "Memo": "",
                }
            ]
        )
        for column_name in forecast_row_df.columns:
            if column_name in {"Date", "Next Income Date", "Memo Directives", "Memo"}:
                continue
            if pd.api.types.is_numeric_dtype(forecast_row_df[column_name]):
                forecast_row_df[column_name] = forecast_row_df[column_name].astype(float)

        return forecast_row_df

    @classmethod
    def _project_account_set_to_forecast_row(
        cls, forecast_df, account_set, d, include_debug_columns=False
    ):
        row_sel_vec = forecast_df["Date"] == d
        projected_balances = account_set.getForecastAccountBalances(
            include_debug_columns=include_debug_columns
        )

        for column_name, value in projected_balances.items():
            if column_name in forecast_df.columns:
                forecast_df.loc[row_sel_vec, column_name] = value

        return forecast_df

    @classmethod
    def _addANewDayToTheForecast(cls, forecast_df, d):
        # dates_as_datetime_dtype = [datetime.datetime.strptime(d, '%Y%m%d') for d in forecast_df.Date]
        # prev_date_as_datetime_dtype = (datetime.datetime.strptime(date, '%Y%m%d') - datetime.timedelta(days=1))
        # sel_vec = [d == prev_date_as_datetime_dtype for d in dates_as_datetime_dtype]
        # new_row_df = copy.deepcopy(forecast_df.loc[sel_vec])
        new_row_df = copy.deepcopy(forecast_df.tail(1))
        new_row_df.Date = d
        new_row_df["Memo Directives"] = ""
        new_row_df.Memo = ""
        forecast_df = pd.concat([forecast_df, new_row_df])
        forecast_df.reset_index(drop=True, inplace=True)
        return forecast_df

    @classmethod
    def _sortTxnsToPreventErrors(
        cls, relevant_confirmed_df, account_set, memo_set, log_stack_depth
    ):
        log_stack_depth += 1

        # Algorithm:
        # Sort by priority. For same priority:
        # income, then net loss txns, then debt payment txns.

        priority_indices_in_order = sorted(relevant_confirmed_df["Priority"].unique())

        sorted_confirmed_df = relevant_confirmed_df.head(0).copy()

        for p in priority_indices_in_order:
            all_txn_of_priority_p = relevant_confirmed_df[
                relevant_confirmed_df["Priority"] == p
            ].copy()

            p_income_rows = []
            p_net_loss_rows = []
            p_debt_pay_rows = []

            for idx, row in all_txn_of_priority_p.iterrows():
                memo_rule = memo_set.findMatchingMemoRule(row.Memo, row.Priority)

                if cls._is_empty_account_endpoint(
                    memo_rule.account_from
                ) and not cls._is_empty_account_endpoint(memo_rule.account_to):
                    p_income_rows.append(idx)

                elif not cls._is_empty_account_endpoint(
                    memo_rule.account_from
                ) and cls._is_empty_account_endpoint(memo_rule.account_to):
                    p_net_loss_rows.append(idx)

                else:
                    p_debt_pay_rows.append(idx)

            p_income = relevant_confirmed_df.loc[p_income_rows].copy()
            p_net_loss = relevant_confirmed_df.loc[p_net_loss_rows].copy()
            p_debt_pay = relevant_confirmed_df.loc[p_debt_pay_rows].copy()

            p_income = p_income.sort_values(
                by=["Amount", "Memo"], ascending=[False, True]
            )
            p_net_loss = p_net_loss.sort_values(
                by=["Amount", "Memo"], ascending=[False, True]
            )
            p_debt_pay = p_debt_pay.sort_values(
                by=["Amount", "Memo"], ascending=[False, True]
            )

            sorted_confirmed_df = pd.concat(
                [sorted_confirmed_df, p_income, p_net_loss, p_debt_pay]
            )

        log_stack_depth -= 1
        return sorted_confirmed_df

    @classmethod
    def _checkIfTxnIsIncome(cls, confirmed_row, log_stack_depth):
        m_income = re.search(r"income", confirmed_row.Memo)
        income_flag = m_income is not None
        # if m_income is not None:
        #     log_in_color(logger, 'yellow', 'debug',
        #                  'transaction flagged as income: ' + m_income.group(0), 3)

        return income_flag

    @classmethod
    def _updateBalancesAndMemo(
        cls, forecast_df, account_set, confirmed_row, memo_rule, d, log_stack_depth
    ):
        # log_in_color(logger,'white','debug','ENTER _updateBalancesAndMemo',log_stack_depth)
        log_stack_depth += 1
        # log_in_color(logger, 'white', 'debug', 'memo_rule_row:', log_stack_depth)
        # log_in_color(logger, 'white', 'debug', memo_rule_row.to_string(), log_stack_depth)

        # Select the row corresponding to the given date
        row_sel_vec = forecast_df["Date"] == d

        # Memo handling when Account_To is not 'ALL_LOANS'
        if memo_rule.account_to != "ALL_LOANS":
            if not cls._is_empty_account_endpoint(memo_rule.account_from):
                # Only update the Memo column if Account_To is 'None'
                if cls._is_empty_account_endpoint(memo_rule.account_to):
                    # forecast_df.loc[row_sel_vec, 'Memo'] += f"; {confirmed_row.Memo} ({memo_rule_row.Account_From} -${confirmed_row.Amount:.2f}) "

                    all_basenames = [
                        a.split(":")[0] for a in account_set.getAccounts().Name
                    ]
                    AF_sel_vec = [
                        memo_rule.account_from == bc for bc in all_basenames
                    ]
                    AF_account_rows = account_set.getAccounts()[AF_sel_vec]
                    if AF_account_rows.shape[0] == 1:  # checking
                        # for checking this would be a negative number, but for credit a positive
                        forecast_df.loc[
                            row_sel_vec, "Memo"
                        ] += f"; {confirmed_row.Memo} ({memo_rule.account_from} -${confirmed_row.Amount}) "
                    else:
                        # for checking this would be a negative number, but for credit a positive
                        forecast_df.loc[
                            row_sel_vec, "Memo"
                        ] += f"; {confirmed_row.Memo} ({memo_rule.account_from} +${confirmed_row.Amount}) "
            else:
                # Single account transaction when Account_From is 'None'
                # forecast_df.loc[row_sel_vec, 'Memo'] += f"; {confirmed_row.Memo} ({memo_rule_row.Account_To} +${confirmed_row.Amount:.2f}) "

                # memo always has + bc only single account deposits allowed are to checking
                forecast_df.loc[
                    row_sel_vec, "Memo"
                ] += f"; {confirmed_row.Memo} ({memo_rule.account_to} +${confirmed_row.Amount}) "

        # Iterate over accounts to update balances and directives
        # log_in_color(logger, 'white', 'debug',''.ljust(45) + ' current_balance , new_balance', log_stack_depth)
        # print('account_set.getAccounts().shape:')
        # print(account_set.getAccounts().shape)
        for account_index, account_row in account_set.getAccounts().iterrows():
            # if account_index + 1 == account_set.getAccounts().shape[0]:
            #     break
            # for account_index in range(1, (1 + account_set.getAccounts().shape[0])):
            #     account_index = int(account_index)

            col_sel_vec = forecast_df.columns == account_row.Name
            current_balance = forecast_df.loc[row_sel_vec, col_sel_vec].values[0][0]
            relevant_balance = AccountSet._forecast_value(account_row["Balance"])

            # If current balance doesn't match the relevant balance, update the forecast
            # print('current_balance, relevant_balance')
            # print(current_balance, relevant_balance)
            # log_in_color(logger, 'white', 'debug', str(account_row.Name).ljust(45)+': '+str(current_balance).ljust(15)+', '+str(relevant_balance).ljust(11), log_stack_depth)
            if current_balance != relevant_balance:
                forecast_df[account_row.Name] = forecast_df[account_row.Name].astype(
                    float
                )
                forecast_df.loc[row_sel_vec, account_row.Name] = relevant_balance
                # delta = round(current_balance - relevant_balance, 2)
                delta = current_balance - relevant_balance

                # Handle income
                if account_row["Account_Type"] == "checking" and delta < 0:
                    # forecast_df.loc[row_sel_vec, 'Memo Directives'] += f"; INCOME ({memo_rule_row.Account_To} +${-1*delta:.2f}) "
                    forecast_df.loc[
                        row_sel_vec, "Memo Directives"
                    ] += f"; INCOME ({memo_rule.account_to} +${-1 * delta}) "

                # Handle additional loan payments
                if (
                    memo_rule.account_to == "ALL_LOANS"
                    and account_row.Name.split(":")[0] != memo_rule.account_from
                ):

                    if (
                        "Billing Cycle Payment Bal" in account_row.Name
                    ):  # this could be more specific
                        continue
                    # forecast_df.loc[row_sel_vec, 'Memo Directives'] += f"; ADDTL LOAN PAYMENT ({memo_rule_row.Account_From} -${delta:.2f}) "
                    # forecast_df.loc[row_sel_vec, 'Memo Directives'] += f"; ADDTL LOAN PAYMENT ({account_row.Name} -${delta:.2f}) "
                    forecast_df.loc[
                        row_sel_vec, "Memo Directives"
                    ] += f"; ADDTL LOAN PAYMENT ({memo_rule.account_from} -${delta}) "
                    forecast_df.loc[
                        row_sel_vec, "Memo Directives"
                    ] += f"; ADDTL LOAN PAYMENT ({account_row.Name} -${delta}) "

                # Handle additional credit card payments
                if (
                    account_row.Account_Type.lower()
                    in ["credit curr stmt bal", "credit prev stmt bal"]
                    and account_row.Name.split(":")[0] != memo_rule.account_from
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
                    ] += f"; ADDTL CC PAYMENT ({memo_rule.account_from} -${delta}) "
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
        include_debug_columns = any(
            ": Curr Stmt Bal" in column_name
            or ": Prev Stmt Bal" in column_name
            or "Billing Cycle Payment Bal" in column_name
            for column_name in forecast_df.columns
        )
        forecast_df = cls._project_account_set_to_forecast_row(
            forecast_df=forecast_df,
            account_set=account_set,
            d=d,
            include_debug_columns=include_debug_columns,
        )

        # income (Checking +$100.00); test txn (Checking -$100.00);
        # income (Checking +$100.00); test txn (Checking -$100.00)

        log_stack_depth -= 1
        # log_in_color(logger, 'white', 'debug', 'EXIT _updateBalancesAndMemo', log_stack_depth)
        return forecast_df

    @classmethod
    def _annotateAcceptedProposedTransaction(
        cls, forecast_df, proposed_row, memo_rule_row, d, account_set, log_stack_depth
    ):
        row_sel_vec = forecast_df["Date"] == d
        account_info = account_set.getAccounts()
        account_type_by_name = dict(zip(account_info["Name"], account_info["Account_Type"]))
        amount = proposed_row["Amount"]
        account_from = memo_rule_row["Account_From"]
        account_to = memo_rule_row["Account_To"]
        account_to_type = account_type_by_name.get(account_to)

        if account_to_type == "credit":
            forecast_df.loc[
                row_sel_vec, "Memo Directives"
            ] += f"; ADDTL CC PAYMENT ({account_from} -${amount}) "
            forecast_df.loc[
                row_sel_vec, "Memo Directives"
            ] += f"; ADDTL CC PAYMENT ({account_to} -${amount}) "
        elif account_to_type == "loan" or account_to == "ALL_LOANS":
            forecast_df.loc[
                row_sel_vec, "Memo Directives"
            ] += f"; ADDTL LOAN PAYMENT ({account_from} -${amount}) "
            forecast_df.loc[
                row_sel_vec, "Memo Directives"
            ] += f"; ADDTL LOAN PAYMENT ({account_to} -${amount}) "
        else:
            return forecast_df

        md_split = [
            md.strip()
            for md in forecast_df.loc[row_sel_vec, "Memo Directives"].iat[0].split(";")
            if md.strip()
        ]
        forecast_df.loc[row_sel_vec, "Memo Directives"] = ("; ".join(md_split)).strip()
        return forecast_df

    # def _attemptTransactionApproximate(
    #     cls, forecast_df, account_set, memo_set, confirmed_df, proposed_row_df
    # ):
    #     log_stack_depth += 1
    #     try:
    #         single_proposed_transaction_df = pd.DataFrame(
    #             copy.deepcopy(proposed_row_df)
    #         ).T
    #         not_yet_validated_confirmed_df = copy.deepcopy(
    #             pd.concat([confirmed_df, single_proposed_transaction_df])
    #         )
    #         empty_df = pd.DataFrame(
    #             {
    #                 "Date": [],
    #                 "Priority": [],
    #                 "Amount": [],
    #                 "Memo": [],
    #                 "Deferrable": [],
    #                 "Partial_Payment_Allowed": [],
    #             }
    #         )

    #         txn_date = proposed_row_df.Date
    #         d_sel_vec = (
    #             datetime.datetime.strptime(d, "%Y%m%d")
    #             <= datetime.datetime.strptime(txn_date, "%Y%m%d")
    #             for d in forecast_df.Date
    #         )
    #         previous_row_df = forecast_df.loc[d_sel_vec, :].tail(2).head(1)

    #         previous_date = (
    #             cls.start_date
    #         )  # todo this optimization had to be removed bc of cc prepayment

    #         hypothetical_future_state_of_forecast_future_rows_only = (
    #             cls._computeOptimalForecastApproximate(
    #                 start_date=previous_date,
    #                 end_date=cls.end_date,
    #                 confirmed_df=not_yet_validated_confirmed_df,
    #                 proposed_df=empty_df,
    #                 deferred_df=empty_df,
    #                 skipped_df=empty_df,
    #                 account_set=copy.deepcopy(
    #                     cls._sync_account_set_w_forecast_day(
    #                         account_set, forecast_df=forecast_df, d=previous_date
    #)
    #                 ),
    #                 memo_rule_set=memo_set,
    #             )[0]
    #         )

    #         # we started the sub-forecast on the previous date, bc that day is considered final
    #         # therefore, we can drop it from the concat bc it is not new
    #         hypothetical_future_state_of_forecast_future_rows_only = (
    #             hypothetical_future_state_of_forecast_future_rows_only.iloc[1:, :]
    #         )
    #         date_array = [
    #             datetime.datetime.strptime(d, "%Y%m%d") for d in forecast_df.Date
    #         ]
    #         row_sel_vec = [
    #             d < datetime.datetime.strptime(txn_date, "%Y%m%d") for d in date_array
    #         ]

    #         past_confirmed_forecast_rows_df = forecast_df[row_sel_vec]

    #         hypothetical_future_state_of_forecast = pd.concat(
    #             [
    #                 past_confirmed_forecast_rows_df,
    #                 hypothetical_future_state_of_forecast_future_rows_only,
    #             ]
    #         )

    #         log_stack_depth -= 1
    #         return hypothetical_future_state_of_forecast  # transaction is permitted
    #     except ValueError as e:
    #         log_stack_depth -= (
    #             5  # several decrements were skipped over by the exception
    #         )

    #         log_in_color(logger, "red", "debug", str(e), log_stack_depth)

    #         if (
    #             re.search(".*Account boundaries were violated.*", str(e.args)) is None
    #         ):  # this is the only exception where we don't want to stop immediately
    #             raise e

    # @profile
    @classmethod
    def _attemptTransaction(
        cls, end_date, forecast_df, account_set, memo_set, confirmed_df, proposed_row_df, log_stack_depth, include_debug_columns=False
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
            log_stack_depth,
        )
        log_stack_depth += 1

        try:
            # Prepare the proposed transaction DataFrame
            single_proposed_transaction_df = proposed_row_df.to_frame().T.copy()

            # Combine the confirmed transactions with the proposed transaction
            updated_confirmed_df = pd.concat(
                [confirmed_df, single_proposed_transaction_df], ignore_index=True
            )

            # log_in_color(logger, 'white', 'info', 'updated_confirmed_df:', log_stack_depth)
            # log_in_color(logger, 'white', 'info', updated_confirmed_df.to_string(), log_stack_depth)

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

            # WITH OPTIMIZATION
            previous_date = (txn_date - datetime.timedelta(days=1))

            # # WITHOUT OPTIMIZATION
            # previous_date = cls.start_date

            # Synchronize the account set with the forecast on the previous date
            synced_account_set = cls._sync_account_set_w_forecast_day(
                account_set=account_set, forecast_df=forecast_df, d=previous_date, log_stack_depth=log_stack_depth)

            # Compute the hypothetical future forecast starting from the previous date
            hypothetical_future_forecast = cls._computeOptimalForecast(
                start_date=previous_date,
                end_date=end_date,
                confirmed_df=updated_confirmed_df,
                proposed_df=empty_df,
                deferred_df=empty_df,
                skipped_df=empty_df,
                account_set=synced_account_set,
                memo_rule_set=memo_set,
                log_stack_depth=log_stack_depth,
                include_debug_columns=include_debug_columns,
            )[0]

            # Exclude the first row since it's considered final and not part of the new forecast
            hypothetical_future_forecast = hypothetical_future_forecast.iloc[1:].copy()

            # Extract past forecast rows before the transaction date
            past_forecast = forecast_df[forecast_df["Date"] < txn_date].copy()

            # Combine past forecast with the hypothetical future forecast
            updated_forecast = pd.concat(
                [past_forecast, hypothetical_future_forecast], ignore_index=True
            )

            log_stack_depth -= 1
            log_in_color(
                logger,
                "white",
                "info",
                str(proposed_row_df.Date) + " EXIT _attemptTransaction",
                log_stack_depth,
            )
            return updated_forecast  # Transaction is permitted

        except AccountBoundaryError as e:
            # Log the exception
            log_in_color(logger, "red", "debug", str(e), log_stack_depth)

            log_stack_depth -= 1
            log_in_color(
                logger,
                "white",
                "info",
                str(proposed_row_df.Date) + " EXIT _attemptTransaction",
                log_stack_depth,
            )

            # Return None to indicate that the transaction is not permitted
            return None

    # @profile
    @classmethod
    def _processConfirmedTransactions(
        cls, forecast_df, relevant_confirmed_df, memo_set, account_set, d, log_stack_depth
    ):
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     d.strftime('%Y-%m-%d') + " ENTER _processConfirmedTransactions",
        #     log_stack_depth,
        # )
        log_stack_depth += 1
        # if not relevant_confirmed_df.empty:
        #     log_in_color(logger, 'cyan', 'debug', 'relevant_confirmed_df:', log_stack_depth)
        #     log_in_color(logger, 'cyan', 'debug', relevant_confirmed_df.to_string(), log_stack_depth)

        for _, confirmed_row in relevant_confirmed_df.iterrows():
            # print('    '+str(confirmed_row.Memo)+' '+str(confirmed_row.Amount))
            memo_rule = memo_set.findMatchingMemoRule(
                confirmed_row.Memo, confirmed_row.Priority
            )

            income_flag = cls._checkIfTxnIsIncome(confirmed_row=confirmed_row, log_stack_depth=log_stack_depth)

            try:
                log_string = str(d) + ' executing txn \''+str(confirmed_row.Memo)
                log_string += '\' '+str(memo_rule.account_from)+ ' -> '+str(memo_rule.account_to)
                log_string += ' for $' + str(confirmed_row.Amount)
                log_in_color(logger, 'white', 'debug', log_string, log_stack_depth)
                # log_in_color(logger, 'white', 'debug', str(d) + ' before txn: ', log_stack_depth)
                # log_in_color(logger, 'white', 'debug', account_set.getAccounts().to_string(), log_stack_depth)
                account_set.executeTransaction(
                    Account_From=memo_rule.account_from,
                    Account_To=memo_rule.account_to,
                    Amount=confirmed_row.Amount,
                    income_flag=income_flag,
                )
                # log_in_color(logger, 'yellow', 'debug', str(d) + ' after txn: ', log_stack_depth)
                # log_in_color(logger, 'yellow', 'debug', account_set.getAccounts().to_string(), log_stack_depth)
            except Exception as e:
                log_stack_depth -= 1
                log_in_color(
                    logger,
                    "white",
                    "debug",
                    d.strftime('%Y-%m-%d') + " EXIT _processConfirmedTransactions",
                    log_stack_depth,
                )
                raise e

            forecast_df = cls._updateBalancesAndMemo(
                forecast_df=forecast_df, account_set=account_set, confirmed_row=confirmed_row, memo_rule=memo_rule, d=d, log_stack_depth=log_stack_depth)

        # log_in_color(logger, 'green', 'debug', forecast_df.to_string(), log_stack_depth)
        log_stack_depth -= 1
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     str(d) + " EXIT _processConfirmedTransactions",
        #     log_stack_depth,
        # )
        return forecast_df

    # todo I have seen similar methods so I think that maybe this can be refactored
    @classmethod
    def _extract_interest_accrued_amount(cls, account_basename, memo_directives):
        for md in memo_directives.split(";"):
            match = re.search(r"CC INTEREST \((.*):(.*)\+\$(.*)\)", md)
            if match is None:
                continue

            basename_str = match.group(1).strip()

            if account_basename == basename_str:
                return float(match.group(3))

        raise ValueError(
            "_extract_interest_accrued_amount was not able to extract a value. basename: "
            + str(account_basename)
            + " mds:"
            + str(memo_directives)
        )

    # @profile
    @classmethod
    def _getTotalPrepaidInCreditCardBillingCycle(
        cls, account_name, account_set, forecast_df, d, log_stack_depth
    ):
        """
        Calculates the total prepaid amount made towards a credit card in the billing cycle up to the given date.

        Parameters:
        - account_name (str): The name of the credit card account.
        - account_set (AccountSet): The account set containing account information.
        - forecast_df (pd.DataFrame): The forecast DataFrame with financial data.
        - date (str): The current date in 'YYYYMMDD' format.

        Returns:
        - float: The total prepaid amount in the current billing cycle.
        """
        log_in_color(
            logger,
            "white",
            "debug",
            str(d) + " ENTER _getTotalPrepaidInCreditCardBillingCycle",
            log_stack_depth,
        )
        log_stack_depth += 1

        # Extract the base account name (without sub-accounts)
        base_account_name = account_name.split(":")[0]

        # Filter the account row for the given account name and type
        accounts_df = account_set.getAccounts()
        account_row = accounts_df[
            (accounts_df["Name"].str.startswith(base_account_name))
            & (accounts_df["Account_Type"] == "credit prev stmt bal")
        ]

        if account_row.empty:
            log_stack_depth -= 1
            raise ValueError(
                f"Account '{account_name}' with type 'credit prev stmt bal' not found in account_set."
            )

        # Get the billing start date
        billing_start_date = account_row["Billing_Start_Date"].iloc[0]

        current_date = d

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
            billing_start_date = billing_start_date - datetime.timedelta(days=30)
            billing_dates = generate_date_sequence(
                billing_start_date,
                num_days_since_first_billing_date + 30,
                "monthly",
            )
        # print('billing_dates:'+str(billing_dates))

        lookback_period_start = billing_dates[-2]

        # print('lookback_period_start:'+str(lookback_period_start))

        # Define the time window to search for payments
        lookback_period_end = d

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

        log_stack_depth -= 1
        log_in_color(
            logger,
            "white",
            "debug",
            str(d) + " EXIT _getTotalPrepaidInCreditCardBillingCycle",
            log_stack_depth,
        )
        return total_prepaid_amount

    # @profile
    @classmethod
    def _getFutureMinPaymentAmount(
        cls, account_name, account_set, forecast_df, d, log_stack_depth
    ):
        """
        Calculates the future minimum payment amount for a given credit card account starting from a specific date.

        Parameters:
        - account_name (str): The name of the credit card account.
        - account_set (AccountSet): The account set containing account information.
        - forecast_df (pd.DataFrame): The forecast DataFrame containing financial data.
        - date (str): The date from which to start the calculation, in 'YYYYMMDD' format.

        Returns:
        - float: The minimum payment amount due in the future, or 0.0 if no payment is due.
        """
        log_in_color(
            logger,
            "white",
            "debug",
            str(d) + " ENTER _getFutureMinPaymentAmount",
            log_stack_depth,
        )
        log_stack_depth += 1

        # Extract the base account name (before any colons)
        base_account_name = account_name.split(":")[0]

        # Get the account row for the specified account name and account type 'credit prev stmt bal'
        accounts_df = account_set.getAccounts()
        account_row = accounts_df[
            (accounts_df["Name"].str.startswith(base_account_name))
            & (accounts_df["Account_Type"] == "credit prev stmt bal")
        ]

        if account_row.empty and not (
            (accounts_df["Name"] == base_account_name)
            & (accounts_df["Account_Type"].isin(["credit", "loan"]))
        ).any():
            raise ValueError(
                f"Account '{account_name}' with type 'credit prev stmt bal' not found in account_set."
            )

        # Get the forecast row for the specified date
        current_forecast_row_df = forecast_df[forecast_df["Date"] == d]

        if current_forecast_row_df.empty:
            raise ValueError(f"Date '{d}' not found in forecast DataFrame.")

        # Check if there is a minimum payment on the current date
        memo_directives = current_forecast_row_df["Memo Directives"].iat[0]
        min_payment_amount = cls._extract_min_payment_amount(
            memo_directives=memo_directives, base_account_name=base_account_name, log_stack_depth=log_stack_depth)

        if min_payment_amount > 0:
            log_stack_depth -= 1
            log_in_color(
                logger,
                "white",
                "debug",
                str(d) + " EXIT _getFutureMinPaymentAmount",
                log_stack_depth,
            )
            return min_payment_amount

        # If no minimum payment on the current date, find the next billing date

        # todo this is wrong
        next_billing_date = generate_date_sequence(
            d, 32, cadence="monthly"
        ).iloc[-1]

        current_date = d

        right_check_bound = current_date + datetime.timedelta(days=35)
        forecast_dates = forecast_df["Date"]
        check_region = forecast_df[
            (forecast_dates < right_check_bound) & (forecast_dates >= current_date)
        ]

        future_min_payment_date_sel_vec = check_region["Memo Directives"].str.contains(
            "CC MIN PAYMENT"
        )

        if sum(future_min_payment_date_sel_vec) == 0:
            log_stack_depth -= 1
            log_in_color(
                logger,
                "white",
                "debug",
                str(d) + " future min_payment_amount = 0",
                log_stack_depth,
            )
            log_in_color(
                logger,
                "white",
                "debug",
                str(d) + " EXIT _getFutureMinPaymentAmount",
                log_stack_depth,
            )
            return 0.0

        # Extract minimum payment amount from the memo directives on the next billing date
        memo_directives = check_region.loc[future_min_payment_date_sel_vec][
            "Memo Directives"
        ].iat[0]
        min_payment_amount = cls._extract_min_payment_amount(
            memo_directives=memo_directives, base_account_name=base_account_name, log_stack_depth=log_stack_depth)

        log_in_color(
            logger,
            "white",
            "debug",
            "next_billing_date:" + str(next_billing_date),
            log_stack_depth,
        )
        log_in_color(
            logger,
            "white",
            "debug",
            "next bd memo_directives:" + str(memo_directives),
            log_stack_depth,
        )
        log_in_color(
            logger,
            "white",
            "debug",
            "next bd min_payment_amount:" + str(min_payment_amount),
            log_stack_depth,
        )

        log_stack_depth -= 1
        log_in_color(
            logger,
            "white",
            "debug",
            str(d) + " EXIT _getFutureMinPaymentAmount",
            log_stack_depth,
        )
        return min_payment_amount

    # @profile
    @classmethod
    def _extract_min_payment_amount(cls, memo_directives, base_account_name, log_stack_depth):
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
            log_stack_depth,
        )
        log_stack_depth += 1

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
        log_stack_depth -= 1
        log_in_color(
            logger,
            "white",
            "debug",
            "EXIT _extract_min_payment_amount",
            log_stack_depth,
        )
        return min_payment_amount

    # @profile
    @classmethod
    def _processProposedTransactions(
        cls,
        end_date,
        account_set,
        forecast_df,
        d,
        memo_set,
        confirmed_df,
        relevant_proposed_df,
        priority_level,
        log_stack_depth,
        include_debug_columns=False
    ):
        """
        Processes proposed transactions by attempting to execute them, handling partial payments, deferrals,
        and updating the forecast accordingly.

        Parameters:
        - account_set: AccountSet object representing the current state of accounts.
        - forecast_df: DataFrame containing the forecasted financial data.
        - date: String representing the current date in 'YYYYMMDD' format. #TODO old
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
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     str(d)
        #     + " ENTER _processProposedTransactions p == "
        #     + str(priority_level),
        #     log_stack_depth,
        # )
        # Increment the log stack depth
        log_stack_depth += 1

        # log_in_color(logger, 'white', 'debug', 'relevant_proposed_df:', log_stack_depth)
        # log_in_color(logger, 'white', 'debug',relevant_proposed_df.to_string(), log_stack_depth)

        # Initialize DataFrames to hold new deferred, skipped, and confirmed transactions
        new_deferred_df = relevant_proposed_df.iloc[
            0:0
        ].copy()  # Empty DataFrame with the same schema
        new_skipped_df = relevant_proposed_df.iloc[0:0].copy()
        new_confirmed_df = relevant_proposed_df.iloc[0:0].copy()

        # If there are no proposed transactions, return early
        if relevant_proposed_df.empty:
            log_stack_depth -= 1
            # log_in_color(
            #     logger,
            #     "white",
            #     "debug",
            #     str(d)
            #     + " EXIT _processProposedTransactions p == "
            #     + str(priority_level),
            #     log_stack_depth,
            # )
            return forecast_df, new_confirmed_df, new_deferred_df, new_skipped_df

        # log_in_color(logger, 'white', 'debug', 'relevant_proposed_df:', log_stack_depth)
        # log_in_color(logger, 'white', 'debug', relevant_proposed_df.to_string(), log_stack_depth)

        # Iterate over each proposed transaction
        for _, proposed_row in relevant_proposed_df.iterrows():
            log_in_color(
                logger,
                "cyan",
                "info",
                str(d)
                + " Considering: "
                + str(proposed_row.Memo)
                + " "
                + str(proposed_row.Amount),
                log_stack_depth,
            )

            # log_in_color(logger, 'cyan', 'info','Current State:', log_stack_depth)
            # log_in_color(logger, 'cyan', 'info', forecast_df.to_string(), log_stack_depth)
            # log_in_color(logger, 'cyan', 'info', account_set.getAccounts().to_string(), log_stack_depth)
            # log_in_color(logger, 'cyan', 'info', confirmed_df.to_string(), log_stack_depth)

            # Find the matching memo rule for the proposed transaction.
            memo_rule = memo_set.findMatchingMemoRule(
                proposed_row["Memo"], proposed_row["Priority"]
            )
            memo_rule_row = pd.Series(
                {
                    "Account_From": memo_rule.account_from,
                    "Account_To": memo_rule.account_to,
                }
            )

            # multiple txns same day same priority p!=1 have not been propagated even if approved
            # editing confirmed_df causes downstream problems, so we have a working copy for the scope of this method
            # local_scope_og_confirmed_df = confirmed_df
            local_scope_confirmed_df = pd.concat([new_confirmed_df, confirmed_df])
            result = cls._attemptTransaction(end_date=end_date,
                forecast_df=forecast_df,
                account_set=copy.deepcopy(account_set),
                memo_set=memo_set,
                confirmed_df=local_scope_confirmed_df,
                proposed_row_df=proposed_row,
                log_stack_depth=log_stack_depth,
                include_debug_columns=include_debug_columns,
            )

            # Check if the transaction is permitted (returns a DataFrame if successful)
            transaction_permitted = isinstance(result, pd.DataFrame)

            if transaction_permitted:
                log_in_color(
                    logger,
                    "green",
                    "info",
                    str(d)
                    + " _attemptTransaction SUCCESS "
                    + str(proposed_row.Memo)
                    + " "
                    + str(proposed_row.Amount),
                    log_stack_depth,
                )
                log_in_color(logger, "green", "info", "Result: ", log_stack_depth)
                log_in_color(
                    logger, "green", "info", result.to_string(), log_stack_depth
                )

                # Transaction is permitted; update the hypothetical future forecast and account set
                hypothetical_forecast = result
                account_set = cls._sync_account_set_w_forecast_day(
                    account_set=account_set, forecast_df=forecast_df, d=d, log_stack_depth=log_stack_depth)
            else:
                log_in_color(
                    logger,
                    "red",
                    "info",
                    str(d)
                    + " _attemptTransaction FAIL "
                    + str(proposed_row.Memo)
                    + " "
                    + str(proposed_row.Amount),
                    log_stack_depth,
                )
                hypothetical_forecast = None

            # Handle partial payments if transaction is not permitted and partial payments are allowed
            if not transaction_permitted and proposed_row["Partial_Payment_Allowed"]:

                # Get the minimum future available balances
                min_future_balances = cls._getMinimumFutureAvailableBalances(
                    account_set=account_set, forecast_df=forecast_df, d=d, log_stack_depth=log_stack_depth)
                max_available_funds = min_future_balances.get(
                    memo_rule_row["Account_From"], 0.0
                )

                # Determine the maximum amount that can be transferred to the destination account
                reduced_amount = cls._calculate_reduced_amount(
                    account_set=account_set,
                    memo_rule_row=memo_rule_row,
                    max_available_funds=max_available_funds,
                    forecast_df=forecast_df,
                    d=d,
                    log_stack_depth=log_stack_depth,
                )

                log_in_color(
                    logger,
                    "cyan",
                    "info",
                    str(d)
                    + " re-attempt at reduced amount: "
                    + str(reduced_amount),
                    log_stack_depth,
                )

                # Attempt the transaction with the reduced amount if it's greater than zero
                if reduced_amount > 0:
                    proposed_row["Amount"] = reduced_amount

                    # local_scope_confirmed_df = pd.concat([new_confirmed_df, local_scope_og_confirmed_df])
                    result = cls._attemptTransaction(end_date=end_date,
                        forecast_df=forecast_df,
                        account_set=copy.deepcopy(account_set),
                        memo_set=memo_set,
                        confirmed_df=local_scope_confirmed_df,
                        proposed_row_df=proposed_row,
                        log_stack_depth=log_stack_depth,
                        include_debug_columns=include_debug_columns,
                    )

                    transaction_permitted = isinstance(result, pd.DataFrame)

                    if transaction_permitted:
                        hypothetical_forecast = result
                        account_set = cls._sync_account_set_w_forecast_day(
                            account_set=account_set, forecast_df=forecast_df, d=d, log_stack_depth=log_stack_depth)
                    else:
                        hypothetical_forecast = None

            # Handle deferrable transactions if not permitted
            if not transaction_permitted and proposed_row["Deferrable"]:
                # Find the next income date
                # next_income_date = cls._find_next_income_date(forecast_df=forecast_df, d=d)

                # Update the date of the proposed transaction to the next income date
                next_income_date = forecast_df[forecast_df.Date == d][
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
                    account_set = cls._sync_account_set_w_forecast_day(
                        account_set=account_set, forecast_df=forecast_df, d=d, log_stack_depth=log_stack_depth)

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
                forecast_df = cls._update_forecast_with_hypothetical(
                    forecast_df=forecast_df,
                    hypothetical_forecast=hypothetical_forecast,
                    d=d, log_stack_depth=log_stack_depth
                )

                # Update the account balances in the forecast DataFrame for the current date
                # this seems redundant here, but chat gpt did this and i dont suspect it for now
                # good method actually, would like to use it in a refactor #todo
                cls._update_forecast_balances(
                    forecast_df=forecast_df,
                    account_set=account_set,
                    d=d,
                    log_stack_depth=log_stack_depth,
                )
                forecast_df = cls._annotateAcceptedProposedTransaction(
                    forecast_df=forecast_df,
                    proposed_row=proposed_row,
                    memo_rule_row=memo_rule_row,
                    d=d,
                    account_set=account_set,
                    log_stack_depth=log_stack_depth,
                )

                # log_in_color(logger, 'green', 'info', 'Forecast Post-Update: ', log_stack_depth)
                # log_in_color(logger, 'green', 'info', forecast_df.to_string(), log_stack_depth)
                # log_in_color(logger, 'green', 'info', 'New Confirmed Txns: ', log_stack_depth)
                # log_in_color(logger, 'green', 'info', confirmed_df.to_string(), log_stack_depth)
            else:
                # This case should not occur; raise an error
                raise ValueError(
                    "Unexpected case in process_proposed_transactions:\n"
                    f"transaction_permitted: {transaction_permitted}\n"
                    f"Deferrable: {proposed_row['Deferrable']}\n"
                    f"Partial_Payment_Allowed: {proposed_row['Partial_Payment_Allowed']}\n"
                )

        # Decrement the log stack depth
        log_stack_depth -= 1
        log_in_color(
            logger,
            "white",
            "debug",
            str(d)
            + " EXIT _processProposedTransactions p == "
            + str(priority_level),
            log_stack_depth,
        )
        return forecast_df, new_confirmed_df, new_deferred_df, new_skipped_df

    @classmethod
    def _minimum_future_available_balances_as_if_a_cc_payment_did_not_happen(
        cls, account_set, memo_rule_row, forecast_df, d, log_stack_depth
    ):
        log_in_color(
            logger,
            "white",
            "debug",
            str(d)
            + " ENTER _minimum_future_available_balances_as_if_a_cc_payment_did_not_happen ",
            log_stack_depth,
        )
        log_stack_depth += 1
        # the reason this method exists is that making an advance minimum payment changes the minimum future available balances
        # in order to make the largest payment possible without going over,

        relevant_subset_df = forecast_df[forecast_df.Date >= d]

        left_check_bound = d + datetime.timedelta(days=1)
        right_check_bound = d + datetime.timedelta(days=35)
        forecast_dates = forecast_df["Date"]
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
        for _, row in check_region.iterrows():
            for md in row["Memo Directives"].split(";"):
                prev_m = re.search(prev_search_substring, md)
                if prev_m is not None:
                    prev_amt_float = float(prev_m.group(1))
                    next_min_payment_amount += prev_amt_float
                    min_cc_payment_found = True
                    next_min_payment_date = row["Date"]

                curr_m = re.search(curr_search_substring, md)
                if curr_m is not None:
                    curr_amt_float = float(curr_m.group(1))
                    next_min_payment_amount += curr_amt_float
                    min_cc_payment_found = True
                    next_min_payment_date = row["Date"]

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
                logger, "white", "debug", "pre_next_payment_df:", log_stack_depth
            )
            log_in_color(
                logger,
                "white",
                "debug",
                pre_next_payment_df.to_string(),
                log_stack_depth,
            )
            log_in_color(
                logger,
                "white",
                "debug",
                "post_next_payment_inclusive_df:",
                log_stack_depth,
            )
            log_in_color(
                logger,
                "white",
                "debug",
                post_next_payment_inclusive_df.to_string(),
                log_stack_depth,
            )

            amount_in_question = min(
                min(pre_next_payment_df[memo_rule_row.Account_From]),
                min(post_next_payment_inclusive_df[memo_rule_row.Account_From]),
            )
        else:
            # so lazy lol. This should be refactored #todo
            amount_in_question = cls._getMinimumFutureAvailableBalances(
                account_set=account_set, forecast_df=forecast_df, d=d, log_stack_depth=log_stack_depth
            )[memo_rule_row.Account_From]

        log_stack_depth -= 1
        log_in_color(
            logger,
            "white",
            "debug",
            str(d)
            + " EXIT _minimum_future_available_balances_as_if_a_cc_payment_did_not_happen ",
            log_stack_depth,
        )
        return amount_in_question

    # @profile
    @classmethod
    def _calculate_reduced_amount(
        cls,
        account_set,
        memo_rule_row,
        max_available_funds,
        forecast_df,
        d, log_stack_depth
    ):
        """
        Calculates the maximum amount that can be transferred based on available funds and account types.

        Parameters:
        - account_set: AccountSet object representing the current state of accounts.
        - memo_rule_row: Series representing the memo rule for the transaction.
        - max_available_funds: Float representing the maximum available funds from the source account.
        - forecast_df: DataFrame containing the forecasted financial data.
        - date: String representing the current date in 'YYYYMMDD' format.

        Returns:
        - reduced_amount: Float representing the reduced transaction amount.
        """
        log_in_color(
            logger,
            "white",
            "debug",
            str(d) + " ENTER _calculate_reduced_amount",
            log_stack_depth,
        )
        log_stack_depth += 1

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

        # log_in_color(logger, 'white', 'debug', 'source_accounts:', log_stack_depth)
        # log_in_color(logger, 'white', 'debug', source_accounts.to_string(), log_stack_depth)
        # log_in_color(logger, 'white', 'debug', 'destination_accounts:', log_stack_depth)
        # log_in_color(logger, 'white', 'debug', destination_accounts.to_string(), log_stack_depth)

        source_account_types = source_accounts["Account_Type"].tolist()
        dest_account_types = destination_accounts["Account_Type"].tolist()

        if (
            "credit curr stmt bal" in source_account_types
            and "credit prev stmt bal" in source_account_types
        ) or "credit" in source_account_types:
            source_account_type = "credit"
        elif (
            "principal balance" in source_account_types
            and "interest" in source_account_types
        ) or "loan" in source_account_types:
            source_account_type = "loan"
        elif len(source_account_types) == 1 and source_account_types[0] == "checking":
            source_account_type = "checking"
        else:
            source_account_type = "none"

        if (
            "credit curr stmt bal" in dest_account_types
            and "credit prev stmt bal" in dest_account_types
        ) or "credit" in dest_account_types:
            dest_account_type = "credit"
        elif (
            "principal balance" in dest_account_types
            and "interest" in dest_account_types
        ) or "loan" in dest_account_types:
            dest_account_type = "loan"
        elif len(dest_account_types) == 1 and dest_account_types[0] == "checking":
            dest_account_type = "checking"
        else:
            dest_account_type = "none"

        if dest_account_type in ["loan", "credit"]:

            future_min_payment = cls._getFutureMinPaymentAmount(
                account_name=memo_rule_row["Account_To"],
                account_set=account_set,
                forecast_df=forecast_df,
                d=d, log_stack_depth=log_stack_depth
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
            source_bound = cls._minimum_future_available_balances_as_if_a_cc_payment_did_not_happen(
                account_set=account_set, memo_rule_row=memo_rule_row, forecast_df=forecast_df, d=d, log_stack_depth=log_stack_depth
            )

            # min future + future_min_payment
        elif source_account_type == "loan":
            raise NotImplementedError
        else:
            raise ValueError("Invalid account type in _calculate_reduced_amount")

        # log_in_color(logger, 'magenta', 'debug', 'destination_accounts: ' , log_stack_depth)
        # log_in_color(logger, 'magenta', 'debug', str(destination_accounts.to_string()), log_stack_depth)

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

        # log_in_color(logger, 'magenta', 'debug', 'forecast_df: ' + str(forecast_df.to_string()), log_stack_depth)

        reduced_amount = min(source_bound, dest_bound)
        log_in_color(
            logger,
            "white",
            "debug",
            "source_bound..: " + str(source_bound),
            log_stack_depth,
        )
        log_in_color(
            logger,
            "white",
            "debug",
            "dest_bound....: " + str(dest_bound),
            log_stack_depth,
        )
        log_in_color(
            logger,
            "white",
            "debug",
            "reduced_amount: " + str(reduced_amount),
            log_stack_depth,
        )

        log_stack_depth -= 1
        log_in_color(
            logger,
            "white",
            "debug",
            str(d) + " EXIT _calculate_reduced_amount",
            log_stack_depth,
        )
        return reduced_amount

    # @profile
    @classmethod
    def _find_next_income_date(cls, forecast_df, d, log_stack_depth):
        """
        Finds the next income date after the given date.

        Parameters:
        - forecast_df: DataFrame containing the forecasted financial data.
        - date: String representing the current date in 'YYYYMMDD' format.

        Returns:
        - next_income_date: String representing the next income date in 'YYYYMMDD' format.
        """
        current_date = d

        # Filter future dates
        future_dates = forecast_df[forecast_df["Date"] > d]

        # Filter rows where the memo indicates income
        income_rows = future_dates[
            future_dates["Memo"].str.contains("income", case=False, na=False)
        ]

        if not income_rows.empty:
            next_income_date = income_rows["Date"].iloc[0]
        else:
            # If no future income dates, set to one day after the forecast end date
            next_income_date = (cls.end_date + pd.Timedelta(days=1))

        return next_income_date

    # @profile
    @classmethod
    def _update_forecast_with_hypothetical(
        cls, forecast_df, hypothetical_forecast, d, log_stack_depth
    ):
        """
        Updates the forecast DataFrame with the hypothetical future forecast starting from the given date.

        Parameters:
        - forecast_df: DataFrame containing the current forecast data.
        - hypothetical_forecast: DataFrame containing the hypothetical future forecast.
        - date: String representing the current date in 'YYYYMMDD' format.

        Returns:
        - Updated forecast_df.
        """
        # Split the forecast into past and future
        past_forecast = forecast_df[forecast_df["Date"] < d]
        future_forecast = hypothetical_forecast[
            hypothetical_forecast["Date"] >= d
        ]

        # Concatenate the past and updated future forecasts
        updated_forecast = pd.concat(
            [past_forecast, future_forecast], ignore_index=True
        )

        # Ensure no duplicate dates
        updated_forecast = updated_forecast.drop_duplicates(subset=["Date"])

        return updated_forecast

    # @profile
    @classmethod
    def _update_forecast_balances(cls, forecast_df, account_set, d, log_stack_depth):
        """
        Updates the account balances in the forecast DataFrame for the current date based on the account set.

        Parameters:
        - forecast_df: DataFrame containing the forecasted financial data.
        - account_set: AccountSet object representing the current state of accounts.
        - date: String representing the current date in 'YYYYMMDD' format.
        """
        # Update each account balance in the forecast
        for index, account_row in account_set.getAccounts().iterrows():
            account_name = account_row["Name"]
            balance = account_row["Balance"]

            if account_name in forecast_df.columns:
                forecast_df.loc[forecast_df["Date"] == d, account_name] = (
                    balance
                )

    # def _processProposedTransactionsApproximate(
    #     cls,
    #     account_set,
    #     forecast_df,
    #     date,
    #     memo_set,
    #     confirmed_df,
    #     relevant_proposed_df,
    #     priority_level,
    # ):
    #     log_stack_depth += 1

    #     new_deferred_df = relevant_proposed_df.head(0)  # to preserve schema
    #     new_skipped_df = relevant_proposed_df.head(0)
    #     new_confirmed_df = relevant_proposed_df.head(0)

    #     if relevant_proposed_df.shape[0] == 0:
    #         log_stack_depth -= 1
    #         return forecast_df, new_confirmed_df, new_deferred_df, new_skipped_df

    #     for proposed_item_index, proposed_row_df in relevant_proposed_df.iterrows():
    #         # print('proposed txn:'+str(proposed_row_df.Date+' '+str(proposed_row_df.Amount)))
    #         relevant_memo_rule_set = memo_set.findMatchingMemoRule(
    #             proposed_row_df.Memo, proposed_row_df.Priority
    #         )
    #         memo_rule_row = relevant_memo_rule_set.getMemoRules().loc[0, :]

    #         result_of_attempt = cls._attemptTransactionApproximate(
    #             forecast_df,
    #             copy.deepcopy(account_set),
    #             memo_set,
    #             confirmed_df,
    #             proposed_row_df,
    #         )
    #         transaction_is_permitted = isinstance(result_of_attempt, pd.DataFrame)

    #         if transaction_is_permitted:
    #             hypothetical_future_state_of_forecast = result_of_attempt
    #             account_set = cls._sync_account_set_w_forecast_day(
    #                 account_set, forecast_df=forecast_df, d=d
    #)
    #         else:
    #             hypothetical_future_state_of_forecast = None

    #         if not transaction_is_permitted and proposed_row_df.Partial_Payment_Allowed:
    #             min_fut_avl_bals = cls._getMinimumFutureAvailableBalances(
    #                 account_set, forecast_df=forecast_df, d=d
    #)
    #             af_max = min_fut_avl_bals[memo_rule_row.Account_From]

    #             account_basenames = [
    #                 cname.split(":")[0] for cname in account_set.getAccounts().Name
    #             ]
    #             at_col_sel_vec = [
    #                 a == memo_rule_row.Account_To for a in account_basenames
    #             ]
    #             at_type_list = list(
    #                 account_set.getAccounts().loc[at_col_sel_vec, :].Account_Type
    #             )

    #             at_type = "none"
    #             if len(at_type_list) == 2:
    #                 if (
    #                     "credit curr stmt bal" in at_type_list
    #                     and "credit prev stmt bal" in at_type_list
    #                 ):
    #                     at_type = "credit"
    #                 elif (
    #                     "principal balance" in at_type_list
    #                     and "interest" in at_type_list
    #                 ):
    #                     at_type = "loan"
    #             elif len(at_type_list) == 1:
    #                 if "checking" == at_type_list[0]:
    #                     at_type = "checking"

    #             # additional credit card payments
    #             if at_type == "credit":
    #                 account_base_names = [
    #                     a.split(":")[0] for a in account_set.getAccounts().Name
    #                 ]
    #                 row_sel_vec = [
    #                     a == memo_rule_row.Account_To for a in account_base_names
    #                 ]

    #                 relevant_account_rows_df = account_set.getAccounts()[row_sel_vec]
    #                 at_max = sum(relevant_account_rows_df.Balance)

    #                 future_min_payment = cls._getFutureMinPaymentAmount(
    #                     memo_rule_row.Account_To,
    #                     account_set,
    #                     forecast_df,
    #                     date,
    #                 )
    #                 if af_max >= future_min_payment and future_min_payment > 0:
    #                     reduced_amt = min(af_max, at_max)  # + future_min_payment
    #                 elif future_min_payment == 0:
    #                     reduced_amt = min(af_max, at_max)
    #                 else:
    #                     reduced_amt = min(af_max, at_max)

    #             elif (
    #                 at_type == "checking" or at_type == "loan"
    #             ):  # havent tested this for loan
    #                 account_base_names = [
    #                     a.split(":")[0] for a in account_set.getAccounts().Name
    #                 ]
    #                 row_sel_vec = [
    #                     a == memo_rule_row.Account_To for a in account_base_names
    #                 ]

    #                 relevant_account_rows_df = account_set.getAccounts()[row_sel_vec]

    #                 at_max = sum(relevant_account_rows_df.Balance)
    #                 reduced_amt = min(af_max, at_max)
    #             elif at_type == "none":
    #                 reduced_amt = af_max
    #             else:
    #                 raise ValueError("at type error in _processProposedTransactions")

    #             if reduced_amt == 0:
    #                 pass
    #             elif reduced_amt > 0:
    #                 proposed_row_df.Amount = reduced_amt
    #                 # print(proposed_row_df.Date+' re-attempt at reduced amt: '+str(reduced_amt))
    #                 result_of_attempt = cls._attemptTransactionApproximate(
    #                     forecast_df,
    #                     copy.deepcopy(account_set),
    #                     memo_set,
    #                     confirmed_df,
    #                     proposed_row_df,
    #                 )
    #                 transaction_is_permitted = isinstance(
    #                     result_of_attempt, pd.DataFrame
    #                 )

    #                 if transaction_is_permitted:
    #                     hypothetical_future_state_of_forecast = result_of_attempt
    #                     account_set = cls._sync_account_set_w_forecast_day(
    #                         account_set, forecast_df=forecast_df, d=d
    #)
    #                 else:
    #                     hypothetical_future_state_of_forecast = None

    #         if not transaction_is_permitted and proposed_row_df.Deferrable:
    #             # look ahead for next income date
    #             future_date_sel_vec = [
    #                 datetime.datetime.strptime(d, "%Y%m%d")
    #                 > datetime.datetime.strptime(date, "%Y%m%d")
    #                 for d in forecast_df.Date
    #             ]
    #             income_date_sel_vec = ["income" in m for m in forecast_df.Memo]

    #             sel_vec = []
    #             for i in range(0, len(future_date_sel_vec)):
    #                 sel_vec.append(future_date_sel_vec[i] and income_date_sel_vec[i])

    #             next_income_row_df = forecast_df[sel_vec].head(1)
    #             if next_income_row_df.shape[0] > 0:
    #                 next_income_date = next_income_row_df["Date"].iat[0]
    #             else:
    #                 next_income_date = (
    #                     datetime.datetime.strptime(cls.end_date, "%Y%m%d")
    #                     + datetime.timedelta(days=1)
    #                 ).strftime("%Y%m%d")

    #             proposed_row_df.Date = next_income_date
    #             # todo what if there are no future income rows

    #             new_deferred_df = pd.concat(
    #                 [new_deferred_df, pd.DataFrame(proposed_row_df).T]
    #             )

    #             remaining_unproposed_transactions_df = relevant_proposed_df[
    #                 ~relevant_proposed_df.index.isin(proposed_row_df.index)
    #             ]
    #             proposed_df = remaining_unproposed_transactions_df

    #         elif not transaction_is_permitted and not proposed_row_df.Deferrable:
    #             skipped_df = pd.concat(
    #                 [new_skipped_df, pd.DataFrame(proposed_row_df).T]
    #             )

    #             remaining_unproposed_transactions_df = relevant_proposed_df[
    #                 ~relevant_proposed_df.index.isin(proposed_row_df.index)
    #             ]
    #             proposed_df = remaining_unproposed_transactions_df

    #         elif transaction_is_permitted:
    #             if priority_level > 1:
    #                 # print('process proposed case 3 sync')
    #                 account_set = cls._sync_account_set_w_forecast_day(
    #                     account_set, forecast_df=forecast_df, d=d
    #)

    #             account_set.executeTransaction(
    #                 Account_From=memo_rule_row.Account_From,
    #                 Account_To=memo_rule_row.Account_To,
    #                 Amount=proposed_row_df.Amount,
    #                 income_flag=False,
    #             )

    #             new_confirmed_df = pd.concat(
    #                 [new_confirmed_df, pd.DataFrame(proposed_row_df).T]
    #             )

    #             remaining_unproposed_transactions_df = relevant_proposed_df[
    #                 ~relevant_proposed_df.index.isin(proposed_row_df.index)
    #             ]
    #             relevant_proposed_df = remaining_unproposed_transactions_df

    #             # forecast_df, skipped_df, confirmed_df, deferred_df
    #             forecast_with_accurately_updated_future_rows = (
    #                 hypothetical_future_state_of_forecast
    #             )

    #             forecast_rows_to_keep_df = forecast_df[
    #                 [
    #                     datetime.datetime.strptime(d, "%Y%m%d")
    #                     < datetime.datetime.strptime(date, "%Y%m%d")
    #                     for d in forecast_df.Date
    #                 ]
    #             ]

    #             new_forecast_rows_df = forecast_with_accurately_updated_future_rows[
    #                 [
    #                     datetime.datetime.strptime(d, "%Y%m%d")
    #                     >= datetime.datetime.strptime(date, "%Y%m%d")
    #                     for d in forecast_with_accurately_updated_future_rows.Date
    #                 ]
    #             ]

    #             forecast_df = pd.concat(
    #                 [forecast_rows_to_keep_df, new_forecast_rows_df]
    #             )
    #             assert forecast_df.shape[0] == forecast_df.drop_duplicates().shape[0]
    #             forecast_df.reset_index(drop=True, inplace=True)

    #             row_sel_vec = [
    #                 x
    #                 for x in (
    #                     forecast_df.Date
    #                     == datetime.datetime.strptime(date, "%Y%m%d")
    #                 )
    #             ]
    #             col_sel_vec = forecast_df.columns == "Memo"

    #             for account_index, account_row in account_set.getAccounts().iterrows():
    #                 if (account_index + 1) == account_set.getAccounts().shape[1]:
    #                     break
    #                 relevant_balance = account_set.getAccounts().iloc[account_index, 1]

    #                 row_sel_vec = forecast_df.Date == datetime.datetime.strptime(
    #                     date, "%Y%m%d"
    #                 )
    #                 col_sel_vec = forecast_df.columns == account_row.Name
    #                 forecast_df.iloc[row_sel_vec, col_sel_vec] = relevant_balance

    #         else:
    #             raise ValueError(
    #                 """This is an edge case that should not be possible
    #                     transaction_is_permitted...............:"""
    #                 + str(transaction_is_permitted)
    #                 + """
    #                     budget_item_row.Deferrable.............:"""
    #                 + str(proposed_row_df.Deferrable)
    #                 + """
    #                     budget_item_row.Partial_Payment_Allowed:"""
    #                 + str(proposed_row_df.Partial_Payment_Allowed)
    #                 + """
    #                     """
    #             )

    #     log_stack_depth -= 1
    #     return forecast_df, new_confirmed_df, new_deferred_df, new_skipped_df

    # account_set, forecast_df, date, memo_set,              ,    relevant_deferred_df,             priority_level, allow_partial_payments, allow_skip_and_defer
    # def __processDeferredTransactionsApproximate(
    #     cls,
    #     account_set,
    #     forecast_df,
    #     date,
    #     memo_set,
    #     relevant_deferred_df,
    #     priority_level,
    #     confirmed_df,
    # ):
    #     log_in_color(
    #         logger,
    #         "green",
    #         "debug",
    #         "ENTER __processDeferredTransactionsApproximate( D:"
    #         + str(relevant_deferred_df.shape[0])
    #         + " )",
    #         log_stack_depth,
    #     )
    #     log_stack_depth += 1

    #     # new_confirmed_df = pd.DataFrame(
    #     #    {'Date': [], 'Priority': [], 'Amount': [], 'Memo': [], 'Deferrable': [], 'Partial_Payment_Allowed': []})
    #     # new_deferred_df = pd.DataFrame(
    #     #    {'Date': [], 'Priority': [], 'Amount': [], 'Memo': [], 'Deferrable': [], 'Partial_Payment_Allowed': []})
    #     new_confirmed_df = confirmed_df.head(0)  # to preserve schema
    #     new_deferred_df = relevant_deferred_df.head(
    #         0
    #     )  # to preserve schema. same as above line btw

    #     if relevant_deferred_df.shape[0] == 0:

    #         log_stack_depth -= 1
    #         # log_in_color(logger, 'green', 'debug', 'EXIT __processDeferredTransactionsApproximate()', log_stack_depth)
    #         return forecast_df, new_confirmed_df, new_deferred_df

    #     for deferred_item_index, deferred_row_df in relevant_deferred_df.iterrows():
    #         if datetime.datetime.strptime(
    #             deferred_row_df.Date, "%Y%m%d"
    #         ) > datetime.datetime.strptime(cls.end_date, "%Y%m%d"):
    #             continue

    #         relevant_memo_rule_set = memo_set.findMatchingMemoRule(
    #             deferred_row_df.Memo, deferred_row_df.Priority
    #         )
    #         memo_rule_row = relevant_memo_rule_set.getMemoRules().loc[0, :]

    #         hypothetical_future_state_of_forecast = copy.deepcopy(forecast_df.head(0))

    #         try:

    #             not_yet_validated_confirmed_df = pd.concat(
    #                 [confirmed_df, pd.DataFrame(deferred_row_df).T]
    #             )
    #             # not_yet_validated_confirmed_df = confirmed_df.append(deferred_row_df)

    #             empty_df = pd.DataFrame(
    #                 {
    #                     "Date": [],
    #                     "Priority": [],
    #                     "Amount": [],
    #                     "Memo": [],
    #                     "Deferrable": [],
    #                     "Partial_Payment_Allowed": [],
    #                 }
    #             )

    #             hypothetical_future_state_of_forecast = (
    #                 cls._computeOptimalForecastApproximate(
    #                     start_date=cls.start_date,
    #                     end_date=cls.end_date,
    #                     confirmed_df=not_yet_validated_confirmed_df,
    #                     proposed_df=empty_df,
    #                     deferred_df=empty_df,
    #                     skipped_df=empty_df,
    #                     account_set=copy.deepcopy(
    #                         cls._sync_account_set_w_forecast_day(
    #                             account_set, forecast_df=forecast_df, d=cls.start_date
    #)
    #                     ),
    #                     memo_rule_set=memo_set,
    #                 )[0]
    #             )

    #             transaction_is_permitted = True
    #         except ValueError as e:
    #             log_in_color(
    #                 logger,
    #                 "red",
    #                 "debug",
    #                 "EXIT __processDeferredTransactionsApproximate()",
    #                 log_stack_depth,
    #             )
    #             if (
    #                 re.search(".*Account boundaries were violated.*", str(e.args))
    #                 is None
    #             ):  # this is the only exception where we don't want to stop immediately
    #                 raise e

    #             transaction_is_permitted = False

    #         if not transaction_is_permitted and deferred_row_df.Deferrable:

    #             # deferred_row_df.Date = (datetime.datetime.strptime(deferred_row_df.Date, '%Y%m%d') + datetime.timedelta(
    #             #     days=1)).strftime('%Y%m%d')

    #             # look ahead for next income date
    #             future_date_sel_vec = (
    #                 d > datetime.datetime.strptime(date, "%Y%m%d")
    #                 for d in forecast_df.Date
    #             )
    #             income_date_sel_vec = ("income" in m for m in forecast_df.Memo)
    #             next_income_date = forecast_df[
    #                 future_date_sel_vec & income_date_sel_vec
    #             ].head(1)["Date"]

    #             deferred_row_df.Date = next_income_date
    #             # print('new deferred row')
    #             # print(deferred_row_df.to_string())

    #             # todo what is no future income date

    #             new_deferred_df = pd.concat(
    #                 [new_deferred_df, pd.DataFrame(deferred_row_df).T]
    #             )

    #         elif transaction_is_permitted:

    #             if priority_level > 1:
    #                 account_set = cls._sync_account_set_w_forecast_day(
    #                     account_set, forecast_df=forecast_df, d=d
    #)

    #             account_set.executeTransaction(
    #                 Account_From=memo_rule_row.Account_From,
    #                 Account_To=memo_rule_row.Account_To,
    #                 Amount=deferred_row_df.Amount,
    #                 income_flag=False,
    #             )

    #             new_confirmed_df = pd.concat(
    #                 [new_confirmed_df, pd.DataFrame(deferred_row_df).T]
    #             )

    #             remaining_unproposed_deferred_transactions_df = relevant_deferred_df[
    #                 ~relevant_deferred_df.index.isin(deferred_row_df.index)
    #             ]
    #             relevant_deferred_df = remaining_unproposed_deferred_transactions_df

    #             # forecast_df, skipped_df, confirmed_df, deferred_df
    #             forecast_with_accurately_updated_future_rows = (
    #                 hypothetical_future_state_of_forecast
    #             )

    #             row_sel_vec = [
    #                 datetime.datetime.strptime(d, "%Y%m%d")
    #                 < datetime.datetime.strptime(date, "%Y%m%d")
    #                 for d in forecast_df.Date
    #             ]
    #             forecast_rows_to_keep_df = forecast_df.loc[row_sel_vec, :]

    #             row_sel_vec = [
    #                 datetime.datetime.strptime(d, "%Y%m%d")
    #                 >= datetime.datetime.strptime(date, "%Y%m%d")
    #                 for d in forecast_with_accurately_updated_future_rows.Date
    #             ]
    #             new_forecast_rows_df = forecast_with_accurately_updated_future_rows.loc[
    #                 row_sel_vec, :
    #             ]

    #             forecast_df = pd.concat(
    #                 [forecast_rows_to_keep_df, new_forecast_rows_df]
    #             )
    #             assert forecast_df.shape[0] == forecast_df.drop_duplicates().shape[0]
    #             forecast_df.reset_index(drop=True, inplace=True)

    #             for account_index, account_row in account_set.getAccounts().iterrows():
    #                 if (account_index + 1) == account_set.getAccounts().shape[1]:
    #                     break
    #                 relevant_balance = account_set.getAccounts().iloc[account_index, 1]

    #                 row_sel_vec = forecast_df.Date == date
    #                 col_sel_vec = forecast_df.columns == account_row.Name
    #                 forecast_df.iloc[row_sel_vec, col_sel_vec] = relevant_balance
    #         else:
    #             raise ValueError(
    #                 """This is an edge case that should not be possible
    #                     transaction_is_permitted...............:"""
    #                 + str(transaction_is_permitted)
    #                 + """
    #                     budget_item_row.Deferrable.............:"""
    #                 + str(deferred_row_df.Deferrable)
    #                 + """
    #                     budget_item_row.Partial_Payment_Allowed:"""
    #                 + str(deferred_row_df.Partial_Payment_Allowed)
    #                 + """
    #                     """
    #             )

    #     log_stack_depth -= 1
    #     log_in_color(
    #         logger,
    #         "green",
    #         "debug",
    #         "EXIT __processDeferredTransactionsApproximate()",
    #         log_stack_depth,
    #     )
    #     return forecast_df, new_confirmed_df, new_deferred_df

    # account_set, forecast_df, date, memo_set,              ,    relevant_deferred_df,             priority_level, allow_partial_payments, allow_skip_and_defer
    # @profile
    @classmethod
    def _processDeferredTransactions(
        cls,
        start_date,
        end_date,
        account_set,
        forecast_df,
        d,
        memo_set,
        relevant_deferred_df,
        priority_level,
        confirmed_df,
        log_stack_depth
    ):
        """
        Processes deferred transactions by attempting to execute them, updating the forecast,
        and handling further deferrals if necessary.

        Parameters:
        - account_set: AccountSet object representing the current state of accounts.
        - forecast_df: DataFrame containing the forecasted financial data.
        - date: String representing the current date in 'YYYYMMDD' format.
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
        log_stack_depth += 1

        # Initialize DataFrames for new confirmed and deferred transactions, preserving the schema
        new_confirmed_df = confirmed_df.iloc[0:0].copy()
        new_deferred_df = relevant_deferred_df.iloc[0:0].copy()

        # Return early if there are no deferred transactions to process
        if relevant_deferred_df.empty:
            log_stack_depth -= 1
            return forecast_df, new_confirmed_df, new_deferred_df

        # Iterate over each deferred transaction
        for deferred_index, deferred_row in relevant_deferred_df.iterrows():
            # Skip if the deferred date is beyond the forecast end date
            deferred_date = deferred_row["Date"]
            if deferred_date > end_date:
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
                hypothetical_future_forecast = cls._computeOptimalForecast(
                    start_date=start_date,
                    end_date=end_date,
                    confirmed_df=updated_confirmed_df,
                    proposed_df=empty_df,
                    deferred_df=empty_df,
                    skipped_df=empty_df,
                    account_set=copy.deepcopy(
                        cls._sync_account_set_w_forecast_day(
                            account_set=account_set, forecast_df=forecast_df, d=start_date, log_stack_depth=log_stack_depth
                        )
                    ),
                    memo_rule_set=memo_set,
                )[0]

                transaction_permitted = True
            except AccountBoundaryError:
                transaction_permitted = False

            if not transaction_permitted and deferred_row["Deferrable"]:
                # Look ahead for the next income date
                future_dates = forecast_df[forecast_df["Date"] > date]
                income_dates = future_dates[
                    future_dates["Memo"].str.contains("income", case=False, na=False)
                ]
                if not income_dates.empty:
                    next_income_date = income_dates["Date"].iloc[0]
                else:
                    # If no future income date, set to one day after forecast end date
                    next_income_date = end_date + datetime.timedelta(days=1)

                # Update the deferred transaction's date
                deferred_row["Date"] = next_income_date

                # Add the deferred transaction to the new deferred DataFrame
                new_deferred_df = pd.concat(
                    [new_deferred_df, deferred_row.to_frame().T], ignore_index=True
                )
            elif transaction_permitted:
                # If priority level is greater than 1, sync the account set with the forecast
                if priority_level > 1:
                    account_set = cls._sync_account_set_w_forecast_day(
                        account_set=account_set, forecast_df=forecast_df, d=d, log_stack_depth=log_stack_depth
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
                past_forecast = forecast_df[forecast_df["Date"] < d]
                future_forecast = hypothetical_future_forecast[
                    hypothetical_future_forecast["Date"] >= d
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
                            forecast_df["Date"] == d, account_name
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
        log_stack_depth -= 1

        # Return the updated forecast and DataFrames
        return forecast_df, confirmed_df, new_deferred_df

    # def _executeTransactionsForDayApproximate(
    #     cls,
    #     account_set,
    #     forecast_df,
    #     date,
    #     memo_set,
    #     confirmed_df,
    #     proposed_df,
    #     deferred_df,
    #     skipped_df,
    #     priority_level,
    # ):
    #     """

    #     I want this to be as generic as possible, with no memos or priority levels having dard coded behavior.
    #     At least a little of this hard-coding does make implementation simpler though.
    #     Therefore, let all income be priority level one, and be identified by the regex '.*income.*'


    #     """

    #     C0 = confirmed_df.shape[0]
    #     P0 = proposed_df.shape[0]
    #     D0 = deferred_df.shape[0]
    #     S0 = skipped_df.shape[0]
    #     T0 = C0 + P0 + D0 + S0

    #     isP1 = priority_level == 1

    #     relevant_proposed_df = copy.deepcopy(
    #         proposed_df[
    #             (proposed_df.Priority == priority_level)
    #             & (proposed_df.Date == date)
    #         ]
    #     )
    #     relevant_confirmed_df = copy.deepcopy(
    #         confirmed_df[
    #             (confirmed_df.Priority == priority_level)
    #             & (confirmed_df.Date == date)
    #         ]
    #     )
    #     relevant_deferred_df = copy.deepcopy(
    #         deferred_df[
    #             (deferred_df.Priority <= priority_level)
    #             & (deferred_df.Date == date)
    #         ]
    #     )

    #     F = "F:" + str(forecast_df.shape[0])
    #     C = "C:" + str(relevant_confirmed_df.shape[0])
    #     P = "P:" + str(relevant_proposed_df.shape[0])
    #     D = "D:" + str(relevant_deferred_df.shape[0])
    #     # log_in_color(logger, 'cyan', 'debug',
    #     #              'ENTER _executeTransactionsForDayApproximate('+date+' ' + str(priority_level) + ' ' + F + ' ' + C + ' ' + P + ' ' + D + ' ) '+str(d),
    #     #              log_stack_depth)
    #     log_stack_depth += 1
    #     # log_in_color(logger, 'cyan', 'debug', 'forecast_df:', log_stack_depth)
    #     # log_in_color(logger, 'cyan', 'debug',forecast_df.to_string(),log_stack_depth)

    #     if isP1:
    #         assert relevant_proposed_df.empty

    #     thereArePendingConfirmedTransactions = not relevant_confirmed_df.empty

    #     date_sel_vec = [(d == date) for d in forecast_df.Date]
    #     noMatchingDayInForecast = forecast_df.loc[date_sel_vec].empty
    #     notPastEndOfForecast = date <= cls.end_date

    #     if isP1 and noMatchingDayInForecast and notPastEndOfForecast:
    #         forecast_df = cls._addANewDayToTheForecast(forecast_df=forecast_df, d=d)

    #     if isP1 and thereArePendingConfirmedTransactions:
    #         relevant_confirmed_df = cls._sortTxnsToPreventErrors(
    #             relevant_confirmed_df, account_set=account_set, memo_set=memo_set
    #)

    #     if priority_level > 1:
    #         account_set = cls._sync_account_set_w_forecast_day(
    #             account_set, forecast_df=forecast_df, d=d
    #)

    #     # print('forecast_df:')
    #     # print(forecast_df.to_string())

    #     # log_in_color(logger,'green','debug','eTFD :: before processConfirmed',log_stack_depth)
    #     # print('before _processConfirmedTransactions')
    #     # print(account_set.getAccounts().to_string())
    #     forecast_df = cls._processConfirmedTransactions(
    #         forecast_df, relevant_confirmed_df=relevant_confirmed_df, memo_set=memo_set, account_set=account_set, d=d
    #)
    #     # print('after _processConfirmedTransactions')
    #     # print(account_set.getAccounts().to_string())
    #     # log_in_color(logger, 'green', 'debug', 'eTFD :: after processConfirmed', log_stack_depth)

    #     if priority_level > 1:
    #         # log_in_color(logger, 'green', 'debug', 'eTFD :: before processProposed', log_stack_depth)
    #         forecast_df, new_confirmed_df, new_deferred_df, new_skipped_df = (
    #             cls._processProposedTransactionsApproximate(
    #                 account_set,
    #                 forecast_df,
    #                 date,
    #                 memo_set,
    #                 confirmed_df,
    #                 relevant_proposed_df,
    #                 priority_level,
    #             )
    #         )
    #         # log_in_color(logger, 'green', 'debug', 'eTFD :: after processProposed', log_stack_depth)
    #         #
    #         # log_in_color(logger, 'white', 'debug', 'new_confirmed_df:', log_stack_depth)
    #         # log_in_color(logger, 'white', 'debug', new_confirmed_df.to_string(), log_stack_depth)
    #         #
    #         # log_in_color(logger, 'white', 'debug', 'new_deferred_df:', log_stack_depth)
    #         # log_in_color(logger, 'white', 'debug', new_deferred_df.to_string(), log_stack_depth)
    #         #
    #         # log_in_color(logger, 'white', 'debug', 'new_skipped_df:', log_stack_depth)
    #         # log_in_color(logger, 'white', 'debug', new_skipped_df.to_string(), log_stack_depth)

    #         confirmed_df = pd.concat([confirmed_df, new_confirmed_df])
    #         confirmed_df.reset_index(drop=True, inplace=True)

    #         deferred_df = pd.concat([deferred_df, new_deferred_df])
    #         deferred_df.reset_index(drop=True, inplace=True)

    #         skipped_df = pd.concat([skipped_df, new_skipped_df])
    #         skipped_df.reset_index(drop=True, inplace=True)

    #         # log_in_color(logger, 'white', 'debug','updated confirmed_df:',log_stack_depth)
    #         # log_in_color(logger, 'white', 'debug',confirmed_df.to_string(),log_stack_depth)
    #         #
    #         # log_in_color(logger, 'white', 'debug','updated deferred_df:',log_stack_depth)
    #         # log_in_color(logger, 'white', 'debug',deferred_df.to_string(),log_stack_depth)
    #         #
    #         # log_in_color(logger, 'white', 'debug','updated skipped_df:',log_stack_depth)
    #         # log_in_color(logger, 'white', 'debug',skipped_df.to_string(),log_stack_depth)

    #         if deferred_df.shape[0] > 0:
    #             relevant_deferred_before_processing = pd.DataFrame(
    #                 relevant_deferred_df, copy=True
    #             )  # we need this to remove old txns if they stay deferred

    #             # log_in_color(logger, 'green', 'debug', 'eTFD :: before processDeferred', log_stack_depth)
    #             forecast_df, new_confirmed_df, new_deferred_df = (
    #                 cls.__processDeferredTransactionsApproximate(
    #                     account_set,
    #                     forecast_df,
    #                     date,
    #                     memo_set,
    #                     pd.DataFrame(relevant_deferred_df, copy=True),
    #                     priority_level,
    #                     confirmed_df,
    #                 )
    #             )
    #             # log_in_color(logger, 'green', 'debug', 'eTFD :: after processDeferred', log_stack_depth)

    #             confirmed_df = pd.concat([confirmed_df, new_confirmed_df])
    #             confirmed_df.reset_index(drop=True, inplace=True)

    #             p_LJ_c = pd.merge(
    #                 proposed_df, confirmed_df, on=["Date", "Memo", "Priority"]
    #             )

    #             # deferred_df = deferred_df - relevant + new. index won't be the same as OG
    #             # this is the inverse of how we selected the relevant rows
    #             p_sel_vec = deferred_df.Priority > priority_level
    #             # d_sel_vec = (deferred_df.Date != date)
    #             d_sel_vec = [d != date for d in deferred_df.Date]
    #             sel_vec = p_sel_vec | d_sel_vec
    #             not_relevant_deferred_df = pd.DataFrame(deferred_df[sel_vec], copy=True)

    #             deferred_df = pd.concat([not_relevant_deferred_df, new_deferred_df])
    #             # deferred_df = not_relevant_deferred_df.append(new_deferred_df)
    #             deferred_df.reset_index(drop=True, inplace=True)

    #     log_stack_depth -= 1
    #     return [forecast_df, confirmed_df, deferred_df, skipped_df]

    # @profile
    @classmethod
    def _executeTransactionsForDay(
        cls,
        end_date,
        account_set,
        forecast_df,
        d,
        memo_set,
        confirmed_df,
        proposed_df,
        deferred_df,
        skipped_df,
        priority_level,
        log_stack_depth,
        include_debug_columns=False
    ):
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     d.strftime('%Y-%m-%d')
        #     + " ENTER _executeTransactionsForDay p="
        #     + str(priority_level),
        #     log_stack_depth,
        # )
        log_stack_depth += 1

        # log_in_color(logger, 'white', 'debug', 'before forecast_df:', log_stack_depth)
        # log_in_color(logger, 'white', 'debug', forecast_df.to_string(), log_stack_depth)

        # if not confirmed_df.empty:
        #     log_in_color(logger, 'white', 'debug', 'confirmed_df:', log_stack_depth)
        #     log_in_color(logger, 'white', 'debug', confirmed_df.to_string(), log_stack_depth)

        isP1 = priority_level == 1

        # Filter transactions relevant to the current day and priority level
        relevant_proposed_df = proposed_df[
            (proposed_df.Priority == priority_level)
            & (proposed_df.Date == d)
        ]

        # log_in_color(logger, 'green', 'debug', (confirmed_df.Priority == priority_level), log_stack_depth)
        # log_in_color(logger, 'green', 'debug', (confirmed_df.Date == d), log_stack_depth)
        relevant_confirmed_df = confirmed_df[
            (confirmed_df.Priority == priority_level)
            & (confirmed_df.Date == d)
        ]
        relevant_deferred_df = deferred_df[
            (deferred_df.Priority <= priority_level)
            & (deferred_df.Date == d)
        ]

        # Ensure no proposed transactions exist for priority 1
        if isP1:
            assert relevant_proposed_df.empty

        # Check if there are pending confirmed transactions
        thereArePendingConfirmedTransactions = not relevant_confirmed_df.empty


        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     d.strftime('%Y-%m-%d'),
        #     log_stack_depth,
        # )
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     "end_date: "+str(end_date),
        #     log_stack_depth,
        # )

        # Check if the current day exists in the forecast and if it's within the forecast range
        date_sel_vec = forecast_df["Date"] == d
        noMatchingDayInForecast = forecast_df.loc[date_sel_vec].empty
        notPastEndOfForecast = d <= end_date

        # Add a new day to the forecast if required
        if isP1 and noMatchingDayInForecast and notPastEndOfForecast:
            forecast_df = cls._addANewDayToTheForecast(forecast_df=forecast_df, d=d)

        # Sort transactions to prioritize income first
        # print('isP1 and thereArePendingConfirmedTransactions:'+str(isP1 and thereArePendingConfirmedTransactions))
        # print('isP1................................:'+str(isP1))
        # print('thereArePendingConfirmedTransactions:' + str(thereArePendingConfirmedTransactions))
        # if thereArePendingConfirmedTransactions:
        #     relevant_confirmed_df = cls._sortTxnsToPreventErrors(relevant_confirmed_df=relevant_confirmed_df, account_set=account_set, memo_set=memo_set)

        # Sync account set with the forecast for non-priority 1 transactions
        if priority_level > 1:
            account_set = cls._sync_account_set_w_forecast_day(
                account_set=account_set, forecast_df=forecast_df, d=d, log_stack_depth=log_stack_depth
            )

        # if not relevant_confirmed_df.empty:
        #     log_in_color(logger, 'magenta', 'debug', 'relevant_confirmed_df:', log_stack_depth)
        #     log_in_color(logger, 'magenta', 'debug', relevant_confirmed_df.to_string(), log_stack_depth)

        try:
            # Process confirmed transactions
            forecast_df = cls._processConfirmedTransactions(
                forecast_df=forecast_df, relevant_confirmed_df=relevant_confirmed_df, memo_set=memo_set, account_set=account_set, d=d, log_stack_depth=log_stack_depth
            )
        except Exception as e:
            log_stack_depth -= 1
            # log_in_color(
            #     logger,
            #     "white",
            #     "debug",
            #     d.strftime('%Y-%m-%d')
            #     + " EXIT _executeTransactionsForDay p="
            #     + str(priority_level),
            #     log_stack_depth,
            # )
            raise e

        # Process proposed transactions for priority levels greater than 1
        if priority_level > 1:
            forecast_df, new_confirmed_df, new_deferred_df, new_skipped_df = (
                cls._processProposedTransactions(
                    end_date=end_date,
                    account_set=account_set,
                    forecast_df=forecast_df,
                    d=d,
                    memo_set=memo_set,
                    confirmed_df=confirmed_df,
                    relevant_proposed_df=relevant_proposed_df,
                    priority_level=priority_level,
                    log_stack_depth=log_stack_depth,
                    include_debug_columns=include_debug_columns,
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
                    cls._processDeferredTransactions(cls,
                        end_date=end_date,
                        account_set=account_set,
                        forecast_df=forecast_df,
                        d=d,
                        memo_set=memo_set,
                        relevant_deferred_df=relevant_deferred_df.copy(),
                        priority_level=priority_level,
                        confirmed_df=confirmed_df,
                        log_stack_depth=log_stack_depth
                    )
                )

                # Update confirmed DataFrame with newly confirmed transactions
                confirmed_df = pd.concat([confirmed_df, new_confirmed_df]).reset_index(
                    drop=True
                )

                # Adjust deferred DataFrame by removing processed transactions and adding new deferred ones
                not_relevant_deferred_df = deferred_df[
                    (deferred_df.Priority > priority_level)
                    | (deferred_df.Date != d)
                ]
                deferred_df = pd.concat(
                    [not_relevant_deferred_df, new_deferred_df]
                ).reset_index(drop=True)

        # log_in_color(logger, 'white', 'debug', 'after forecast_df:', log_stack_depth)
        # log_in_color(logger, 'white', 'debug', forecast_df.to_string(), log_stack_depth)

        log_stack_depth -= 1
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     str(d)
        #     + " EXIT _executeTransactionsForDay p="
        #     + str(priority_level),
        #     log_stack_depth,
        # )
        return [forecast_df, confirmed_df, deferred_df, skipped_df]

    # @profile
    @classmethod
    def _processCreditCardBillingDayForDay(
        cls,
        account_set,
        current_forecast_row_df,
        log_stack_depth,
    ):
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     str(current_forecast_row_df.Date.iat[0])
        #     + " ENTER _processCreditCardBillingDayForDay",
        #     log_stack_depth,
        # )
        log_stack_depth += 1

        current_date = current_forecast_row_df["Date"].iat[0]
        interest_directives = account_set.processCreditCardBillingDay(current_date)
        account_set.updateCreditCardEndOfPreviousCycleBalances(current_date)

        if interest_directives:
            memo_directives = [
                md.strip()
                for md in current_forecast_row_df["Memo Directives"].iat[0].split(";")
                if md.strip()
            ]
            memo_directives.extend(interest_directives)
            current_forecast_row_df.loc[:, "Memo Directives"] = "; ".join(
                memo_directives
            )

        projected_balances = account_set.getForecastAccountBalances(
            include_debug_columns=True
        )
        for column_name, value in projected_balances.items():
            if column_name in current_forecast_row_df.columns:
                current_forecast_row_df.loc[:, column_name] = value

        log_stack_depth -= 1
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     str(current_forecast_row_df.Date.iat[0])
        #     + " EXIT _processCreditCardBillingDayForDay",
        #     log_stack_depth,
        # )
        return current_forecast_row_df

    # @profile
    @classmethod
    def _calculateLoanInterestAccrualsForDay(
        cls, account_set, current_forecast_row_df, log_stack_depth
    ):
        """
        Calculates and applies interest accruals for loans on the current day.

        Parameters:
        - account_set: AccountSet object containing account information.
        - current_forecast_row_df: DataFrame containing the forecast row for the current date.

        Returns:
        - Updated current_forecast_row_df with applied interest accruals.
        """
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     str(current_forecast_row_df.Date.iat[0])
        #     + " ENTER _calculateLoanInterestAccrualsForDay",
        #     log_stack_depth,
        # )
        # Increment log stack depth for logging purposes
        log_stack_depth += 1

        # print('PRE INTEREST ACCRUAL FORECAST ROW')
        # print(current_forecast_row_df.to_string())

        current_date = current_forecast_row_df["Date"].iat[0]

        for account in account_set.accounts:
            if account.account_type != "loan":
                continue

            billing_state = account.billing_state
            interest_cadence = getattr(billing_state, "interest_cadence", None)
            if interest_cadence is None:
                continue

            billing_start_date = billing_state.billing_cycle_start_date
            if isinstance(billing_start_date, datetime.datetime):
                billing_start_date = billing_start_date.date()
            num_days = (current_date - billing_start_date).days

            if num_days < 0:
                continue

            dseq = generate_date_sequence(
                start_date=billing_start_date,
                num_days=num_days,
                cadence=interest_cadence,
            )
            if current_date == billing_start_date:
                dseq.append(current_date)

            if current_date not in set(dseq):
                continue

            interest_accrued = billing_state.accrue_interest()
            AccountSet._sync_debt_account_from_billing_state(account)
            if interest_accrued > 0:
                md_split_semicolon = (
                    current_forecast_row_df["Memo Directives"].iat[0].split(";")
                )
                md_split_semicolon = [md for md in md_split_semicolon if md]
                md_split_semicolon.append(
                    f"LOAN INTEREST ({account.name}: Interest +${interest_accrued})"
                )
                current_forecast_row_df.loc[:, "Memo Directives"] = "; ".join(
                    md_split_semicolon
                )

        projected_balances = account_set.getForecastAccountBalances(
            include_debug_columns=True
        )
        for column_name, value in projected_balances.items():
            if column_name in current_forecast_row_df.columns:
                current_forecast_row_df.loc[:, column_name] = value

        # Decrement log stack depth
        log_stack_depth -= 1

        # print('POST INTEREST ACCRUAL FORECAST ROW')
        # print(current_forecast_row_df.to_string())

        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     str(current_forecast_row_df.Date.iat[0])
        #     + " EXIT _calculateLoanInterestAccrualsForDay",
        #     log_stack_depth,
        # )
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
    @classmethod
    def _executeCreditCardMinimumPayments(
        cls, forecast_df, account_set, current_forecast_row_df, log_stack_depth
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
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     str(current_forecast_row_df.Date.iat[0])
        #     + " ENTER _executeCreditCardMinimumPayments ",
        #     log_stack_depth,
        # )
        log_stack_depth += 1

        # log_in_color(logger, 'white', 'debug','BEFORE forecast_df:', log_stack_depth)
        # log_in_color(logger, 'white', 'debug', forecast_df.to_string(), log_stack_depth)

        primary_checking_account_name = account_set.getPrimaryCheckingAccountName()

        # Loop through accounts to process credit card minimum payments
        for account_index, account_row in account_set.getAccounts().iterrows():
            if account_row.Account_Type == "credit":
                account = account_set.accounts[account_index]
                current_date = current_forecast_row_df.Date.iloc[0]

                if not AccountSet.is_billing_date(account, current_date):
                    continue

                total_payment_due = account.billing_state.remaining_minimum_payment_due()
                if total_payment_due <= 0:
                    continue

                account_set.executeTransaction(
                    Account_From=primary_checking_account_name,
                    Account_To=account.name,
                    Amount=total_payment_due,
                    minimum_payment_flag=True,
                )

                projected_balances = account_set.getForecastAccountBalances(
                    include_debug_columns=True
                )
                for column_name, value in projected_balances.items():
                    if column_name in current_forecast_row_df.columns:
                        current_forecast_row_df.loc[:, column_name] = value

                memo_parts = [
                    f"CC MIN PAYMENT ({account.name}: Prev Stmt Bal -${total_payment_due})",
                    f"CC MIN PAYMENT ({primary_checking_account_name} -${total_payment_due})",
                ]
                md_split_semicolon = (
                    current_forecast_row_df["Memo Directives"].iat[0].split(";")
                )
                md_split_semicolon = [md for md in md_split_semicolon if md]
                md_split_semicolon += memo_parts
                current_forecast_row_df.loc[:, "Memo Directives"] = "; ".join(
                    md_split_semicolon
                )
                continue

            if account_row.Account_Type != "credit prev stmt bal":
                continue

            # Skip accounts without a billing start date
            billing_start_date = account_row.Billing_Start_Date
            if pd.isnull(billing_start_date) or billing_start_date == "None":
                continue

            current_date = current_forecast_row_df.Date.iloc[0]

            billing_start_datetime = billing_start_date
            num_days = (current_date - billing_start_datetime).days

            # Generate billing days
            if num_days >= 0:
                billing_days = set(
                    generate_date_sequence(billing_start_date, num_days, "monthly")
                )
            else:
                billing_days = set()

            if current_date == billing_start_date:
                billing_days.add(current_date)

            # print('billing_start_date:'+str(billing_start_date))
            # print('current_date_str:'+str(current_date_str))
            # print('billing_days:'+str(billing_days))
            if current_date not in billing_days:
                continue

            # this will be the correct replacement once bcp is tracked properly
            advance_payment_amount = current_forecast_row_df[
                account_row.Name.split(":")[0] + ": Credit Billing Cycle Payment Bal"
            ].iat[0]

            # THIS IS OLD PREPAID LOGIC
            # advance_payment_amount = cls._getTotalPrepaidInCreditCardBillingCycle(
            #     account_row.Name, account_set=account_set, forecast_df=forecast_df, d=current_date_str
            #)

            # Determine the earliest billing date within the forecast range
            first_day_of_forecast = forecast_df.Date.iloc[0]

            relevant_billing_days = [
                d
                for d in billing_days
                if d > first_day_of_forecast
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

        log_stack_depth -= 1
        # print('current_forecast_row_df:')
        # print(current_forecast_row_df.to_string())
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     str(current_forecast_row_df.Date.iat[0])
        #     + " EXIT _executeCreditCardMinimumPayments ",
        #     log_stack_depth,
        # )
        return current_forecast_row_df

    # @profile
    @classmethod
    def _executeLoanMinimumPayments(cls, account_set, current_forecast_row_df, log_stack_depth):
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     str(current_forecast_row_df.Date.iat[0])
        #     + " ENTER _executeLoanMinimumPayments",
        #     log_stack_depth,
        # )
        log_stack_depth += 1

        # log_in_color(logger, 'white', 'debug','before current_forecast_row_df:', log_stack_depth)
        # log_in_color(logger, 'white', 'debug', current_forecast_row_df.to_string(), log_stack_depth)

        primary_checking_account_name = account_set.getPrimaryCheckingAccountName()

        current_date = current_forecast_row_df.Date.iloc[0]
        for account in account_set.accounts:
            if account.account_type != "loan":
                continue

            billing_state = account.billing_state
            billing_start_date = billing_state.billing_cycle_start_date
            if billing_start_date in [None, "None"] or pd.isnull(billing_start_date):
                continue
            if isinstance(billing_start_date, datetime.datetime):
                billing_start_date = billing_start_date.date()

            if not AccountSet.is_billing_date(account, current_date):
                continue

            minimum_payment_amount = min(
                billing_state.remaining_minimum_payment_due(),
                billing_state.balance,
            )
            if minimum_payment_amount <= 0:
                continue

            payment_toward_interest = min(
                minimum_payment_amount,
                billing_state.interest_balance,
            )
            payment_toward_principal = min(
                billing_state.principal_balance,
                minimum_payment_amount - payment_toward_interest,
            )
            loan_payment_amount = payment_toward_interest + payment_toward_principal

            account_set.executeTransaction(
                Account_From=primary_checking_account_name,
                Account_To=account.name,
                Amount=loan_payment_amount,
                minimum_payment_flag=True,
            )

            memo_parts = []
            if payment_toward_interest > 0:
                memo_parts.append(
                    f"LOAN MIN PAYMENT ({account.name}: Interest -${payment_toward_interest})"
                )
            if payment_toward_principal > 0:
                memo_parts.append(
                    f"LOAN MIN PAYMENT ({account.name}: Principal Balance -${payment_toward_principal})"
                )
            if loan_payment_amount > 0:
                memo_parts.append(
                    f"LOAN MIN PAYMENT ({primary_checking_account_name} -${loan_payment_amount})"
                )

            md_split_semicolon = (
                current_forecast_row_df["Memo Directives"].iat[0].split(";")
            )
            md_split_semicolon = [md for md in md_split_semicolon if md]
            md_split_semicolon += memo_parts
            current_forecast_row_df.loc[:, "Memo Directives"] = "; ".join(
                md_split_semicolon
            )

        md_split = [
            md.strip()
            for md in current_forecast_row_df["Memo Directives"].iat[0].split(";")
            if md.strip()
        ]
        current_forecast_row_df.iat[
            0, current_forecast_row_df.columns.get_loc("Memo Directives")
        ] = ("; ".join(md_split)).strip()

        projected_balances = account_set.getForecastAccountBalances(
            include_debug_columns=True
        )
        for column_name, value in projected_balances.items():
            if column_name in current_forecast_row_df.columns:
                current_forecast_row_df.loc[:, column_name] = value

        # log_in_color(logger, 'white', 'debug', 'after current_forecast_row_df:', log_stack_depth)
        # log_in_color(logger, 'white', 'debug', current_forecast_row_df.to_string(), log_stack_depth)

        log_stack_depth -= 1
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     str(current_forecast_row_df.Date.iat[0])
        #     + " EXIT _executeLoanMinimumPayments",
        #     log_stack_depth,
        # )

        return current_forecast_row_df

    # @profile
    @classmethod
    def _getMinimumFutureAvailableBalances(
        cls, account_set, forecast_df, d, log_stack_depth
    ):
        """
        Calculates the minimum future available balances for each account starting from the specified date.

        Parameters:
        - account_set: AccountSet object containing account information.
        - forecast_df: DataFrame containing the forecasted financial data.
        - date: String representing the current date in 'YYYYMMDD' format.

        Returns:
        - future_available_balances: Dictionary mapping account names to their minimum future available balances.
        """
        log_in_color(
            logger,
            "cyan",
            "debug",
            str(d) + " ENTER _getMinimumFutureAvailableBalances",
            log_stack_depth,
        )
        # Increment log stack depth (if used for logging)
        log_stack_depth += 1

        current_date = d

        # Filter forecast_df for current and future dates
        current_and_future_forecast_df = forecast_df[
            [
                d >= current_date
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
            log_stack_depth,
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
                    log_stack_depth,
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
                    log_stack_depth,
                )

        log_in_color(
            logger,
            "cyan",
            "debug",
            "future_available_balances: " + str(future_available_balances),
            log_stack_depth,
        )

        # Decrement log stack depth
        log_stack_depth -= 1
        log_in_color(
            logger,
            "cyan",
            "debug",
            str(d) + " EXIT _getMinimumFutureAvailableBalances",
            log_stack_depth,
        )
        return future_available_balances

    # @profile
    @classmethod
    def _sync_account_set_w_forecast_day(cls, account_set, forecast_df, d, log_stack_depth):
        # log_in_color(logger, 'white', 'debug', str(d)+' ENTER _sync_account_set_w_forecast_day', log_stack_depth)
        log_stack_depth += 1

        # log_in_color(logger, 'cyan', 'debug', 'before account set update:', log_stack_depth)
        # log_in_color(logger, 'cyan', 'debug', account_set.getAccounts().to_string(), log_stack_depth)

        Accounts_df = account_set.getAccounts()

        # log_in_color(logger, 'cyan', 'debug', 'BEFORE update Accounts_df:', log_stack_depth)
        relevant_forecast_day = forecast_df[forecast_df.Date == d]

        # log_in_color(logger, 'cyan', 'debug', 'relevant_forecast_day:', log_stack_depth)
        # log_in_color(logger, 'cyan', 'debug', relevant_forecast_day.to_string(), log_stack_depth)

        row_sel_vec = forecast_df.Date == d
        try:
            assert sum(row_sel_vec) > 0
        except Exception as e:
            error_msg = "error in _sync_account_set_w_forecast_day\n"
            error_msg += "date: " + d.strftime('%Y-%m-%d') + "\n"
            error_msg += "min date of forecast:" + str(min(forecast_df.Date)) + "\n"
            error_msg += "max date of forecast:" + str(max(forecast_df.Date)) + "\n"
            raise AssertionError(error_msg)

        for account_index in range(1, (1 + Accounts_df.shape[0])):
            account_index = int(account_index)
            # print('account_index: ' + str(account_index))
            relevant_balance = relevant_forecast_day.iat[0, account_index]
            # print('relevant_balance: ' + str(relevant_balance))
            # account_set.accounts[account_index - 1].balance = round(relevant_balance, 2)
            account = account_set.accounts[account_index - 1]
            account.balance = relevant_balance

            if account.account_type == "credit":
                billing_state = account.billing_state
                curr_column = f"{account.name}: Curr Stmt Bal"
                prev_column = f"{account.name}: Prev Stmt Bal"
                payment_column = f"{account.name}: Credit Billing Cycle Payment Bal"
                end_of_previous_cycle_column = (
                    f"{account.name}: Credit End of Prev Cycle Bal"
                )

                billing_state_updated = False
                if curr_column in relevant_forecast_day.columns:
                    billing_state.current_statement_balance = Decimal(
                        str(relevant_forecast_day[curr_column].iat[0])
                    )
                    billing_state_updated = True
                if prev_column in relevant_forecast_day.columns:
                    billing_state.previous_statement_balance = Decimal(
                        str(relevant_forecast_day[prev_column].iat[0])
                    )
                    billing_state_updated = True
                if payment_column in relevant_forecast_day.columns:
                    billing_state.billing_cycle_payment_balance = Decimal(
                        str(relevant_forecast_day[payment_column].iat[0])
                    )
                    billing_state_updated = True
                if end_of_previous_cycle_column in relevant_forecast_day.columns:
                    billing_state.end_of_previous_cycle_balance = Decimal(
                        str(relevant_forecast_day[end_of_previous_cycle_column].iat[0])
                    )
                    billing_state_updated = True
                if billing_state_updated:
                    AccountSet._sync_debt_account_from_billing_state(account)
            elif account.account_type == "loan":
                billing_state = account.billing_state
                principal_column = f"{account.name}: Principal Balance"
                interest_column = f"{account.name}: Interest"
                payment_column = f"{account.name}: Loan Billing Cycle Payment Bal"

                billing_state_updated = False
                if principal_column in relevant_forecast_day.columns:
                    billing_state.principal_balance = Decimal(
                        str(relevant_forecast_day[principal_column].iat[0])
                    )
                    billing_state_updated = True
                if interest_column in relevant_forecast_day.columns:
                    billing_state.interest_balance = Decimal(
                        str(relevant_forecast_day[interest_column].iat[0])
                    )
                    billing_state_updated = True
                if payment_column in relevant_forecast_day.columns:
                    billing_state.billing_cycle_payment_balance = Decimal(
                        str(relevant_forecast_day[payment_column].iat[0])
                    )
                    billing_state_updated = True
                if billing_state_updated:
                    AccountSet._sync_debt_account_from_billing_state(account)

        # log_in_color(logger, 'cyan', 'debug', 'updated account set:', log_stack_depth)
        # log_in_color(logger, 'cyan', 'debug', account_set.getAccounts().to_string(), log_stack_depth)

        log_stack_depth -= 1
        # log_in_color(logger, 'white', 'debug', str(d)+' EXIT _sync_account_set_w_forecast_day', log_stack_depth)
        return account_set

    # @profile
    @classmethod
    def _propagate_credit_txn_curr_only(
        cls,
        relevant_account_info_df,
        account_deltas_list,
        future_rows_only_df,
        forecast_df,
        account_set_before_p2_plus_txn,
        billing_dates_dict,
        d,
        post_txn_row_df,
        log_stack_depth
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
        - date_string: Current date as a string in 'YYYYMMDD' format.
        - post_txn_row_df: DataFrame with the forecast row after transactions.

        Returns:
        - Updated future_rows_only_df DataFrame.
        """
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     "ENTER _propagate_credit_txn_curr_only",
        #     log_stack_depth,
        # )
        log_stack_depth += 1

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
            d2 for d2 in cc_billing_dates if d2 > d
        ]
        if future_billing_dates:
            next_billing_date = min(future_billing_dates)
            date_after_next_billing_date = (
                next_billing_date
                + datetime.timedelta(days=1)
            )
        else:
            next_billing_date = None
            date_after_next_billing_date = "never match"

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
                date_iat == date_after_next_billing_date
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
                new_prev_memo = "INITIALIZE"
                new_curr_memo = "INITIALIZE"
                new_check_memo = "INITIALIZE"
                new_interest_memo = "INITIALIZE"
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
                        og_prev_amount = cls._parse_memo_amount(md, log_stack_depth=log_stack_depth)
                        og_min_payment_amount += og_prev_amount
                    elif f"CC MIN PAYMENT ({curr_stmt_bal_account_name}" in md:
                        og_curr_memo = md
                        og_curr_amount = cls._parse_memo_amount(md, log_stack_depth=log_stack_depth)
                        og_min_payment_amount += og_curr_amount
                    elif f"CC MIN PAYMENT ({checking_account_name}" in md:
                        og_check_memo = md
                        og_check_amount = cls._parse_memo_amount(md, log_stack_depth=log_stack_depth)
                    elif f"CC INTEREST ({prev_stmt_bal_account_name}" in md:
                        og_interest_memo = md
                        og_interest_amount = cls._parse_memo_amount(md, log_stack_depth=log_stack_depth)
                    else:
                        md_to_keep.append(md)

                # Get account row for APR
                account_row = account_set_before_p2_plus_txn.getAccounts().loc[
                    account_set_before_p2_plus_txn.getAccounts().Name
                    == credit_basename
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
                    log_stack_depth,
                )

                previous_stmt_delta += adjusted_payment_amount
                checking_delta += adjusted_payment_amount
                interest_delta = interest_to_be_charged - og_interest_amount
                # previous_stmt_delta += round(interest_delta, 2)
                previous_stmt_delta += interest_delta
                billing_cycle_payment_delta = 0  # redundant but cant hurt

                # Adjust memos
                log_in_color(logger, "white", "debug", "(case 1) _update_memo_amount")
                new_check_memo = cls._update_memo_amount(
                    og_check_memo, og_check_amount - adjusted_payment_amount, log_stack_depth=log_stack_depth
                )
                if adjusted_payment_amount >= curr_prev_stmt_bal:
                    # Adjust curr and prev memos
                    if og_curr_amount > 0:
                        log_in_color(
                            logger, "white", "debug", "(case 2) _update_memo_amount"
                        )
                        new_curr_memo = cls._update_memo_amount(
                            og_curr_memo, adjusted_payment_amount - curr_prev_stmt_bal, log_stack_depth=log_stack_depth
                        )
                    if og_prev_amount > 0:
                        log_in_color(
                            logger, "white", "debug", "(case 3) _update_memo_amount"
                        )
                        new_prev_memo = cls._update_memo_amount(
                            og_prev_memo, curr_prev_stmt_bal, log_stack_depth=log_stack_depth
                        )
                else:
                    if og_curr_amount > 0:
                        log_in_color(
                            logger, "white", "debug", "(case 4) _update_memo_amount"
                        )
                        new_curr_memo = cls._update_memo_amount(og_curr_memo, 0.00, log_stack_depth=log_stack_depth)
                    if og_prev_amount > 0:
                        log_in_color(
                            logger, "white", "debug", "(case 5) _update_memo_amount"
                        )
                        new_prev_memo = cls._update_memo_amount(
                            og_prev_memo, adjusted_payment_amount, log_stack_depth=log_stack_depth
                        )
                log_in_color(logger, "white", "debug", "(case 6) _update_memo_amount")
                new_interest_memo = cls._update_memo_amount(
                    og_interest_memo, interest_to_be_charged, log_stack_depth=log_stack_depth
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
                    log_stack_depth,
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
                    log_stack_depth,
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
                    log_stack_depth,
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
            future_rows_only_df.at[f_i, credit_basename] += previous_stmt_delta
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

        log_stack_depth -= 1
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     "EXIT _propagate_credit_txn_curr_only",
        #     log_stack_depth,
        # )
        return future_rows_only_df

    # affects checking as well
    # @profile
    @classmethod
    def _propagate_credit_payment_curr_only(
        cls,
        relevant_account_info_df,
        account_deltas_list,
        future_rows_only_df,
        forecast_df,
        account_set_before_p2_plus_txn,
        billing_dates_dict,
        d,
        post_txn_row_df,
        log_stack_depth
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
        - date_string: Current date as a string in 'YYYYMMDD' format.
        - post_txn_row_df: DataFrame with the forecast row after transactions.

        Returns:
        - Updated future_rows_only_df DataFrame.
        """
        log_in_color(
            logger,
            "white",
            "debug",
            "ENTER _propagate_credit_payment_curr_only",
            log_stack_depth,
        )
        log_stack_depth += 1

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
            d2 for d2 in cc_billing_dates if d2 > d
        ]
        if future_billing_dates:
            next_billing_date = min(future_billing_dates)
        else:
            next_billing_date = None

        day_after_billing_dates = [
            (
                d
                + datetime.timedelta(days=1)
            )
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

                if d == next_billing_date:
                    pass  # payments day of count toward the next cycle
                else:
                    billing_cycle_payment_delta = 0

                    # Move current statement delta to previous
                    prev_stmt_delta += curr_stmt_delta
                    curr_stmt_delta = 0

            elif date_iat in day_after_billing_dates:
                if f_i == 0:
                    updated_eopc = post_txn_row_df[prev_stmt_bal_account_name].iat[0]
                else:
                    updated_eopc = future_rows_only_df.at[
                        f_i - 1, prev_stmt_bal_account_name
                    ]
                old_eopc = future_rows_only_df.at[f_i, eopc_account_name]
                eopc_delta += updated_eopc - old_eopc

            # todo left off here, copy pasted from prev only method
            elif date_iat in cc_billing_dates and previous_prev_stmt_bal != 0:
                # log_in_color(logger, 'white', 'debug', str(date_iat) + ' (Not Next) Billing Date and previous_prev_stmt_bal != 0', log_stack_depth)
                # Handle other billing dates after payment has been made

                # Parse memo directives
                for md in f_row["Memo Directives"].split(";"):
                    md = md.strip()
                    if not md:
                        continue

                    og_min_payment_amount = cls._parse_memo_amount(md, log_stack_depth=log_stack_depth)

                    # log_in_color(logger, 'white', 'debug',
                    #              str(date_iat) + ' Processing md: '+str(md),
                    #              log_stack_depth)

                    if f"CC MIN PAYMENT ({prev_stmt_bal_account_name}" in md:

                        # Calculate interest and current due
                        account_row = account_set_before_p2_plus_txn.getAccounts().loc[
                            account_set_before_p2_plus_txn.getAccounts().Name
                            == credit_basename
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
                        #              log_stack_depth)
                        #
                        # log_in_color(logger, 'white', 'debug',
                        #              str(date_iat) + ' new_min_payment_amount: ' + str(new_min_payment_amount),
                        #              log_stack_depth)

                        # Adjust deltas
                        prev_stmt_delta += (
                            og_min_payment_amount - new_min_payment_amount
                        )
                        checking_delta += og_min_payment_amount - new_min_payment_amount

                        # Update memo directive
                        log_in_color(
                            logger, "white", "debug", "(case 7) _update_memo_amount"
                        )
                        new_md = cls._update_memo_amount(md, new_min_payment_amount, log_stack_depth=log_stack_depth)
                        md_to_keep.append(new_md)

                        # log_in_color(logger, 'white', 'debug',
                        #              str(date_iat) + ' new md: ' + str(md),
                        #              log_stack_depth)

                    elif f"CC INTEREST ({prev_stmt_bal_account_name}" in md:
                        account_row = account_set_before_p2_plus_txn.getAccounts().loc[
                            account_set_before_p2_plus_txn.getAccounts().Name
                            == credit_basename
                        ]
                        apr = account_row["APR"].iat[0]
                        # interest_to_be_charged = round(previous_prev_stmt_bal * (apr / 12), 2)
                        interest_to_be_charged = previous_prev_stmt_bal * (apr / 12)

                        og_interest_amount = cls._parse_memo_amount(md, log_stack_depth=log_stack_depth)

                        # log_in_color(logger, 'white', 'debug', str(date_iat) + ' og_interest_amount: ' + str(og_interest_amount), log_stack_depth)
                        # log_in_color(logger, 'white', 'debug', str(date_iat) + ' NEW interest_to_be_charged: ' + str(interest_to_be_charged), log_stack_depth)

                        prev_stmt_delta += interest_to_be_charged - og_interest_amount

                        # Update memo directive
                        log_in_color(
                            logger, "white", "debug", "(case 8) _update_memo_amount"
                        )
                        new_md = cls._update_memo_amount(md, interest_to_be_charged, log_stack_depth=log_stack_depth)
                        md_to_keep.append(new_md)

                        # Move current statement delta to previous
                        prev_stmt_delta += curr_stmt_delta
                        curr_stmt_delta = 0

                        # log_in_color(logger, 'white', 'debug',
                        #              str(date_iat) + ' new md: ' + str(md),
                        #              log_stack_depth)

                    elif f"CC MIN PAYMENT ({checking_account_name}" in md:

                        # Calculate interest and current due
                        account_row = account_set_before_p2_plus_txn.getAccounts().loc[
                            account_set_before_p2_plus_txn.getAccounts().Name
                            == credit_basename
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
                        #              log_stack_depth)

                        # Update memo directive
                        log_in_color(
                            logger, "white", "debug", "(case 9) _update_memo_amount"
                        )
                        new_md = cls._update_memo_amount(md, new_min_payment_amount, log_stack_depth=log_stack_depth)
                        md_to_keep.append(new_md)

                        # log_in_color(logger, 'white', 'debug',
                        #              str(date_iat) + ' new md: ' + str(md),
                        #              log_stack_depth)

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
            log_stack_depth,
        )

        log_stack_depth -= 1
        log_in_color(
            logger,
            "white",
            "debug",
            "EXIT _propagate_credit_payment_curr_only",
            log_stack_depth,
        )
        return future_rows_only_df

    # @profile
    @classmethod
    def _propagate_credit_payment_prev_only(
        cls,
        relevant_account_info_df,
        account_deltas_list,
        future_rows_only_df,
        forecast_df,
        account_set_before_p2_plus_txn,
        billing_dates_dict,
        d,
        post_txn_row_df,
        log_stack_depth
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
        - date_string: Current date as a string in 'YYYYMMDD' format.
        - post_txn_row_df: DataFrame with the forecast row after transactions.

        Returns:
        - Updated future_rows_only_df DataFrame.
        """
        log_in_color(
            logger,
            "white",
            "debug",
            str(d) + " ENTER _propagate_credit_payment_prev_only",
            log_stack_depth,
        )
        log_stack_depth += 1

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
            d2 for d2 in cc_billing_dates if d2 > d
        ]
        if future_billing_dates:
            next_billing_date = min(future_billing_dates)
        else:
            next_billing_date = None

        day_after_billing_dates = [ d + datetime.timedelta(days=1) for d in future_billing_dates ]

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
            log_stack_depth,
        )
        log_in_color(
            logger,
            "white",
            "debug",
            relevant_account_info_df.to_string(),
            log_stack_depth,
        )
        # relevant_account_info_df
        log_in_color(
            logger,
            "white",
            "debug",
            "previous_stmt_delta........: " + str(previous_stmt_delta),
            log_stack_depth,
        )
        log_in_color(
            logger,
            "white",
            "debug",
            "checking_delta.............: " + str(checking_delta),
            log_stack_depth,
        )
        log_in_color(
            logger,
            "white",
            "debug",
            "billing_cycle_payment_delta: " + str(billing_cycle_payment_delta),
            log_stack_depth,
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
            # log_in_color(logger, 'white', 'debug', str(date_iat)+' previous_prev_stmt_bal: ' + str(previous_prev_stmt_bal), log_stack_depth)

            if date_iat == next_billing_date:
                log_in_color(
                    logger,
                    "white",
                    "debug",
                    str(date_iat) + " Next Billing Date",
                    log_stack_depth,
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
                # advance_payment_amount = cls._getTotalPrepaidInCreditCardBillingCycle(
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
                    log_stack_depth,
                )

                # Get minimum payment amount
                og_min_payment_amount = cls._parse_memo_amount(og_check_memo, log_stack_depth=log_stack_depth)
                log_in_color(
                    logger,
                    "white",
                    "debug",
                    "og_min_payment_amount: " + str(og_min_payment_amount),
                    log_stack_depth,
                )

                # Adjust deltas
                payment_to_apply = min(og_min_payment_amount, advance_payment_amount)
                log_in_color(
                    logger,
                    "white",
                    "debug",
                    "payment_to_apply: " + str(og_min_payment_amount),
                    log_stack_depth,
                )

                previous_stmt_delta += payment_to_apply
                checking_delta += payment_to_apply

                if d == next_billing_date:
                    pass  # payments day of count toward the next cycle
                else:
                    billing_cycle_payment_delta = 0

                # # Update previous_prev_stmt_bal
                # previous_prev_stmt_bal = round(future_rows_only_df.at[f_i, prev_stmt_bal_account_name] + previous_stmt_delta,2)

                # Adjust memo directives
                if advance_payment_amount >= og_min_payment_amount:

                    og_prev_amount = cls._parse_memo_amount(og_prev_memo, log_stack_depth=log_stack_depth)

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
                    # log_in_color(logger, 'white', 'debug', 'remaining_payment = og_min_payment_amount - advance_payment_amount', log_stack_depth)
                    # log_in_color(logger, 'white', 'debug', str(og_min_payment_amount - advance_payment_amount), log_stack_depth)
                    log_in_color(
                        logger, "white", "debug", "(case 12) _update_memo_amount"
                    )
                    new_check_memo = cls._update_memo_amount(
                        og_check_memo, remaining_payment, log_stack_depth=log_stack_depth
                    )
                    log_in_color(
                        logger, "white", "debug", "(case 13) _update_memo_amount"
                    )
                    new_prev_memo = cls._update_memo_amount(
                        og_prev_memo, remaining_payment, log_stack_depth=log_stack_depth
                    )

                md_to_keep.extend([new_check_memo, new_prev_memo])

            elif date_iat in day_after_billing_dates:
                # print('DAY AFTER BILLING DATE')
                if f_i == 0:
                    updated_eopc = post_txn_row_df[prev_stmt_bal_account_name].iat[0]
                else:
                    updated_eopc = future_rows_only_df.at[
                        f_i - 1, prev_stmt_bal_account_name
                    ]
                old_eopc = future_rows_only_df.at[f_i, eopc_account_name]
                eopc_delta += updated_eopc - old_eopc

            elif date_iat in cc_billing_dates and previous_prev_stmt_bal != 0:
                # log_in_color(logger, 'white', 'debug', str(date_iat) + ' (Not Next) Billing Date and previous_prev_stmt_bal != 0', log_stack_depth)
                # Handle other billing dates after payment has been made

                # Parse memo directives
                for md in f_row["Memo Directives"].split(";"):
                    md = md.strip()
                    if not md:
                        continue

                    og_min_payment_amount = cls._parse_memo_amount(md, log_stack_depth=log_stack_depth)

                    # log_in_color(logger, 'white', 'debug',
                    #              str(date_iat) + ' Processing md: '+str(md),
                    #              log_stack_depth)

                    if f"CC MIN PAYMENT ({prev_stmt_bal_account_name}" in md:

                        # Calculate interest and current due
                        account_row = account_set_before_p2_plus_txn.getAccounts().loc[
                            account_set_before_p2_plus_txn.getAccounts().Name
                            == credit_basename
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
                        #              log_stack_depth)
                        #
                        # log_in_color(logger, 'white', 'debug',
                        #              str(date_iat) + ' new_min_payment_amount: ' + str(new_min_payment_amount),
                        #              log_stack_depth)

                        # Adjust deltas
                        previous_stmt_delta += (
                            og_min_payment_amount - new_min_payment_amount
                        )
                        checking_delta += og_min_payment_amount - new_min_payment_amount

                        # Update memo directive
                        log_in_color(
                            logger, "white", "debug", "(case 14) _update_memo_amount"
                        )
                        new_md = cls._update_memo_amount(md, new_min_payment_amount, log_stack_depth=log_stack_depth)
                        md_to_keep.append(new_md)

                        # log_in_color(logger, 'white', 'debug',
                        #              str(date_iat) + ' new md: ' + str(md),
                        #              log_stack_depth)

                    elif f"CC INTEREST ({prev_stmt_bal_account_name}" in md:
                        account_row = account_set_before_p2_plus_txn.getAccounts().loc[
                            account_set_before_p2_plus_txn.getAccounts().Name
                            == credit_basename
                        ]
                        apr = account_row["APR"].iat[0]
                        # interest_to_be_charged = round(previous_prev_stmt_bal * (apr / 12), 2)
                        interest_to_be_charged = previous_prev_stmt_bal * (apr / 12)

                        og_interest_amount = cls._parse_memo_amount(md, log_stack_depth=log_stack_depth)

                        # log_in_color(logger, 'white', 'debug', str(date_iat) + ' og_interest_amount: ' + str(og_interest_amount), log_stack_depth)
                        # log_in_color(logger, 'white', 'debug', str(date_iat) + ' NEW interest_to_be_charged: ' + str(interest_to_be_charged), log_stack_depth)

                        previous_stmt_delta += (
                            interest_to_be_charged - og_interest_amount
                        )

                        # Update memo directive
                        log_in_color(
                            logger, "white", "debug", "(case 15) _update_memo_amount"
                        )
                        new_md = cls._update_memo_amount(md, interest_to_be_charged, log_stack_depth=log_stack_depth)
                        md_to_keep.append(new_md)

                        # log_in_color(logger, 'white', 'debug',
                        #              str(date_iat) + ' new md: ' + str(md),
                        #              log_stack_depth)

                    elif f"CC MIN PAYMENT ({checking_account_name}" in md:

                        # Calculate interest and current due
                        account_row = account_set_before_p2_plus_txn.getAccounts().loc[
                            account_set_before_p2_plus_txn.getAccounts().Name
                            == credit_basename
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
                        #              log_stack_depth)

                        # Update memo directive
                        log_in_color(
                            logger, "white", "debug", "(case 16) _update_memo_amount"
                        )
                        new_md = cls._update_memo_amount(md, new_min_payment_amount, log_stack_depth=log_stack_depth)
                        md_to_keep.append(new_md)

                        # log_in_color(logger, 'white', 'debug',
                        #              str(date_iat) + ' new md: ' + str(md),
                        #              log_stack_depth)

                    else:
                        md_to_keep.append(md)

                # # Update previous_prev_stmt_bal
                # previous_prev_stmt_bal = round(future_rows_only_df.at[f_i, prev_stmt_bal_account_name] + previous_stmt_delta,2)

            else:
                # No adjustments needed
                pass

            # log_in_color(logger, 'white', 'debug', str(date_iat)+' '+str(prev_stmt_bal_account_name)+' += '+str(previous_stmt_delta), log_stack_depth)

            # Update balances
            future_rows_only_df.at[f_i, checking_account_name] += checking_delta
            future_rows_only_df.at[f_i, credit_basename] += previous_stmt_delta
            future_rows_only_df.at[
                f_i, prev_stmt_bal_account_name
            ] += previous_stmt_delta

            future_rows_only_df.at[f_i, eopc_account_name] += eopc_delta

            # log_in_color(logger, 'cyan', 'debug', str(date_iat) + ' ' + checking_account_name + ' = ' + str(future_rows_only_df.at[f_i, checking_account_name]), log_stack_depth)
            # log_in_color(logger, 'cyan', 'debug', str(date_iat) + ' ' + prev_stmt_bal_account_name + ' = ' + str(future_rows_only_df.at[f_i, prev_stmt_bal_account_name]), log_stack_depth)

            # else no change is needed?
            if md_to_keep != []:
                # Clean and update memo directives
                md_to_keep = [" " + md for md in md_to_keep if md]
                future_rows_only_df.at[f_i, "Memo Directives"] = ";".join(
                    md_to_keep
                ).strip()

        log_in_color(
            logger, "white", "debug", "future_rows_only_df:", log_stack_depth
        )
        log_in_color(
            logger,
            "white",
            "debug",
            future_rows_only_df.to_string(),
            log_stack_depth,
        )
        log_stack_depth -= 1
        log_in_color(
            logger,
            "white",
            "debug",
            str(d) + " EXIT _propagate_credit_payment_prev_only",
            log_stack_depth,
        )
        return future_rows_only_df

    # @profile
    @classmethod
    def _propagate_loan_payment_interest_only(
        cls,
        relevant_account_info_df,
        account_deltas_list,
        future_rows_only_df,
        forecast_df,
        account_set_before_p2_plus_txn,
        billing_dates_dict,
        date_string,
        post_txn_row_df,
        log_stack_depth
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
        - date_string: Current date as a string in 'YYYYMMDD' format.
        - post_txn_row_df: DataFrame with the forecast row after transactions.

        Returns:
        - Updated future_rows_only_df DataFrame.
        """
        log_in_color(
            logger,
            "white",
            "debug",
            "ENTER _propagate_loan_payment_interest_only",
            log_stack_depth,
        )
        log_stack_depth += 1
        # log_in_color(logger, 'cyan', 'debug', 'BEFORE forecast_df', log_stack_depth)
        # log_in_color(logger, 'cyan', 'debug', forecast_df.to_string(), log_stack_depth)

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
            int(d) for d in loan_billing_dates if int(d) > int(date_string)
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
            # print('date_string: ' + str(date_string))
            # print('date_iat: ' + str(date_iat))
            # print('next_billing_date: ' + str(next_billing_date))
            if date_iat == next_billing_date:
                # Handle next billing date (payment due date)

                if date_string == next_billing_date:
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
                        interest_amount = cls._parse_memo_amount(md, log_stack_depth=log_stack_depth)
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
                        interest_paid_amount = cls._parse_memo_amount(md, log_stack_depth=log_stack_depth)
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
                    new_interest_md = cls._update_memo_amount(
                        og_interest_md, new_interest_amount, log_stack_depth=log_stack_depth
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

        # log_in_color(logger, 'cyan', 'debug', 'future_rows_only_df', log_stack_depth)
        # log_in_color(logger, 'cyan', 'debug', future_rows_only_df.to_string(), log_stack_depth)
        log_stack_depth -= 1
        log_in_color(
            logger,
            "white",
            "debug",
            "EXIT _propagate_loan_payment_interest_only",
            log_stack_depth,
        )
        return future_rows_only_df

    # @profile
    @classmethod
    def _propagate_loan_payment_pbal_only(
        cls,
        relevant_account_info_df,
        account_deltas_list,
        future_rows_only_df,
        forecast_df,
        account_set_before_p2_plus_txn,
        billing_dates_dict,
        date_string,
        post_txn_row_df,
        log_stack_depth
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
        - date_string: Current date as a string in 'YYYYMMDD' format.
        - post_txn_row_df: DataFrame with the forecast row after transactions.

        Returns:
        - Updated future_rows_only_df DataFrame.
        """
        log_in_color(
            logger,
            "cyan",
            "debug",
            "ENTER _propagate_loan_payment_pbal_only",
            log_stack_depth,
        )
        log_stack_depth += 1

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
            int(d) for d in loan_billing_dates if int(d) > int(date_string)
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

                if date_string == next_billing_date:
                    pass  # it would count toward next billing cycle
                else:
                    billing_cycle_payment_delta = 0

                # Parse memo directives
                for md in f_row["Memo Directives"].split(";"):
                    md = md.strip()
                    if not md:
                        continue

                    if f"LOAN MIN PAYMENT ({pbal_account_name}" in md:
                        pbal_amount = cls._parse_memo_amount(md, log_stack_depth=log_stack_depth)
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
                        pbal_paid_amount = cls._parse_memo_amount(md, log_stack_depth=log_stack_depth)
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

        log_stack_depth -= 1
        log_in_color(
            logger,
            "cyan",
            "debug",
            "EXIT _propagate_loan_payment_pbal_only",
            log_stack_depth,
        )
        return future_rows_only_df

    # @profile
    @classmethod
    def _propagate_loan_payment_pbal_interest(
        cls,
        relevant_account_info_df,
        account_deltas_list,
        future_rows_only_df,
        forecast_df,
        account_set_before_p2_plus_txn,
        billing_dates_dict,
        date_string,
        post_txn_row_df,
        log_stack_depth
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
        - date_string: Current date as a string in 'YYYYMMDD' format.
        - post_txn_row_df: DataFrame with the forecast row after transactions.

        Returns:
        - Updated future_rows_only_df DataFrame.
        """
        log_in_color(
            logger,
            "cyan",
            "debug",
            "ENTER _propagate_loan_payment_pbal_interest",
            log_stack_depth,
        )
        log_stack_depth += 1

        log_in_color(
            logger, "white", "debug", "future_rows_only_df:", log_stack_depth
        )
        log_in_color(
            logger,
            "white",
            "debug",
            future_rows_only_df.to_string(),
            log_stack_depth,
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
            int(d) for d in loan_billing_dates if int(d) > int(date_string)
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
                        pbal_amount = cls._parse_memo_amount(md, log_stack_depth=log_stack_depth)
                        pbal_delta += pbal_amount
                        checking_delta += pbal_amount
                    elif f"LOAN MIN PAYMENT ({interest_account_name}" in md:
                        interest_amount = cls._parse_memo_amount(md, log_stack_depth=log_stack_depth)
                        interest_delta += interest_amount
                        checking_delta += interest_amount
                    else:
                        md_to_keep.append(md)

                if date_string == next_billing_date:
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
                        pbal_paid_amount = cls._parse_memo_amount(md, log_stack_depth=log_stack_depth)
                        og_pbal_md = md
                    elif f"LOAN MIN PAYMENT ({interest_account_name}" in md:
                        interest_paid_amount = cls._parse_memo_amount(md, log_stack_depth=log_stack_depth)
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
                new_interest_md = cls._update_memo_amount(
                    og_interest_md, new_interest_amount, log_stack_depth=log_stack_depth
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
            logger, "white", "debug", "future_rows_only_df:", log_stack_depth
        )
        log_in_color(
            logger,
            "white",
            "debug",
            future_rows_only_df.to_string(),
            log_stack_depth,
        )
        log_stack_depth -= 1
        log_in_color(
            logger,
            "cyan",
            "debug",
            "EXIT _propagate_loan_payment_pbal_interest",
            log_stack_depth,
        )
        return future_rows_only_df

    # @profile
    @classmethod
    def _propagate_credit_payment_prev_curr(
        cls,
        relevant_account_info_df,
        account_deltas_list,
        future_rows_only_df,
        forecast_df,
        account_set_before_p2_plus_txn,
        billing_dates_dict,
        d,
        post_txn_row_df,
        log_stack_depth
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
        - date_string: Current date as a string in 'YYYYMMDD' format.
        - post_txn_row_df: DataFrame with the forecast row after transactions.

        Returns:
        - Updated future_rows_only_df DataFrame.
        """
        log_in_color(
            logger,
            "cyan",
            "debug",
            "ENTER _propagate_credit_payment_prev_curr",
            log_stack_depth,
        )
        log_stack_depth += 1

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
            d2 for d2 in cc_billing_dates if d2 > d
        ]
        if future_billing_dates:
            next_billing_date = min(future_billing_dates)
        else:
            next_billing_date = None

        day_after_billing_dates = [
            (
                d
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
                    log_stack_depth,
                )
                for md in f_row["Memo Directives"].split(";"):
                    md = md.strip()
                    if not md:
                        continue

                    if f"CC MIN PAYMENT ({prev_stmt_bal_account_name}" in md:
                        og_prev_memo = md
                        og_prev_amount = cls._parse_memo_amount(md, log_stack_depth=log_stack_depth)
                    elif f"CC MIN PAYMENT ({curr_stmt_bal_account_name}" in md:
                        og_curr_memo = md
                        og_curr_amount = cls._parse_memo_amount(md, log_stack_depth=log_stack_depth)
                    elif f"CC MIN PAYMENT ({checking_account_name}" in md:
                        og_check_memo = md
                        og_check_amount = cls._parse_memo_amount(md, log_stack_depth=log_stack_depth)
                    elif f"CC INTEREST ({prev_stmt_bal_account_name}" in md:
                        og_interest_memo = md
                        og_interest_amount = cls._parse_memo_amount(md, log_stack_depth=log_stack_depth)
                    else:
                        md_to_keep.append(md)

                # Get advance payment amount
                # advance_payment_amount = cls._getTotalPrepaidInCreditCardBillingCycle(
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

                if d == next_billing_date:
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
                        new_prev_memo = cls._update_memo_amount(
                            og_prev_memo, 0.00, log_stack_depth=log_stack_depth
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
                            new_curr_memo = cls._update_memo_amount(
                                og_curr_memo, curr_amount_remaining, log_stack_depth=log_stack_depth
                            )
                    else:
                        # Advance payments partially cover previous statement balance and none of curr (which there might not be any)
                        prev_amount_remaining = og_prev_amount - advance_payment_amount
                        log_in_color(
                            logger, "white", "debug", "(case 21) _update_memo_amount"
                        )
                        new_prev_memo = cls._update_memo_amount(
                            og_prev_memo, prev_amount_remaining, log_stack_depth=log_stack_depth
                        )
                        new_curr_memo = og_curr_memo
                    log_in_color(
                        logger, "white", "debug", "(case 22) _update_memo_amount"
                    )
                    new_check_memo = cls._update_memo_amount(
                        og_check_memo, og_check_amount - advance_payment_amount, log_stack_depth=log_stack_depth
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
                if f_i == 0:
                    updated_eopc = post_txn_row_df[prev_stmt_bal_account_name].iat[0]
                else:
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
                new_prev_memo = "INITIALIZE"
                new_curr_memo = "INITIALIZE"
                new_check_memo = "INITIALIZE"
                new_interest_memo = "INITIALIZE"
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
                        og_prev_amount = cls._parse_memo_amount(md, log_stack_depth=log_stack_depth)
                        og_min_payment_amount += og_prev_amount
                    elif f"CC MIN PAYMENT ({curr_stmt_bal_account_name}" in md:
                        og_curr_memo = md
                        og_curr_amount = cls._parse_memo_amount(md, log_stack_depth=log_stack_depth)
                        og_min_payment_amount += og_curr_amount
                    elif f"CC MIN PAYMENT ({checking_account_name}" in md:
                        og_check_memo = md
                        og_check_amount = cls._parse_memo_amount(md, log_stack_depth=log_stack_depth)
                    elif f"CC INTEREST ({prev_stmt_bal_account_name}" in md:
                        og_interest_memo = md
                        og_interest_amount = cls._parse_memo_amount(md, log_stack_depth=log_stack_depth)
                    else:
                        md_to_keep.append(md)

                # Get account row for APR
                account_row = account_set_before_p2_plus_txn.getAccounts().loc[
                    account_set_before_p2_plus_txn.getAccounts().Name
                    == credit_basename
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
                    log_stack_depth,
                )

                previous_stmt_delta += adjusted_payment_amount
                checking_delta += adjusted_payment_amount
                interest_delta = interest_to_be_charged - og_interest_amount
                # previous_stmt_delta += round(interest_delta, 2)
                previous_stmt_delta += interest_delta
                billing_cycle_payment_delta = 0  # redundant but cant hurt

                # Adjust memos
                log_in_color(logger, "white", "debug", "(case 23) _update_memo_amount")
                new_check_memo = cls._update_memo_amount(
                    og_check_memo, og_check_amount - adjusted_payment_amount, log_stack_depth=log_stack_depth
                )
                if adjusted_payment_amount >= curr_prev_stmt_bal:
                    # Adjust curr and prev memos
                    if og_curr_amount > 0:
                        log_in_color(
                            logger, "white", "debug", "(case 24) _update_memo_amount"
                        )
                        new_curr_memo = cls._update_memo_amount(
                            og_curr_memo, adjusted_payment_amount - curr_prev_stmt_bal, log_stack_depth=log_stack_depth
                        )
                    if og_prev_amount > 0:
                        log_in_color(
                            logger, "white", "debug", "(case 25) _update_memo_amount"
                        )
                        new_prev_memo = cls._update_memo_amount(
                            og_prev_memo, curr_prev_stmt_bal, log_stack_depth=log_stack_depth
                        )
                else:
                    if og_curr_amount > 0:
                        # this parent logic branch is for cc payments, not cc expenses, therefore
                        # this specific branch should never happen bc adjust payment amount is always less than OG.
                        # if adjusted_payment_amount > curr_prev_stmt_bal, then so was OG, and therefore curr was 0
                        log_in_color(
                            logger, "white", "debug", "(case 26) _update_memo_amount"
                        )
                        new_curr_memo = cls._update_memo_amount(og_curr_memo, 0.00, log_stack_depth=log_stack_depth)
                    if og_prev_amount > 0:
                        log_in_color(
                            logger, "white", "debug", "(case 27) _update_memo_amount"
                        )
                        new_prev_memo = cls._update_memo_amount(
                            og_prev_memo, og_prev_amount - adjusted_payment_amount, log_stack_depth=log_stack_depth
                        )
                log_in_color(logger, "white", "debug", "(case 28) _update_memo_amount")
                new_interest_memo = cls._update_memo_amount(
                    og_interest_memo, interest_to_be_charged, log_stack_depth=log_stack_depth
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
                    log_stack_depth,
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
                    log_stack_depth,
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
                    log_stack_depth,
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
                f_i, credit_basename
            ] += previous_stmt_delta + curr_stmt_delta
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

            # log_in_color(logger, 'white', 'debug', str(date_iat) + ' ' + str(checking_account_name) + ' += ' + str(checking_delta), log_stack_depth)
            # log_in_color(logger, 'white', 'debug', str(date_iat) + ' ' + str(curr_stmt_bal_account_name) + ' += ' + str(curr_stmt_delta), log_stack_depth)
            # log_in_color(logger, 'white', 'debug', str(date_iat) + ' ' + str(prev_stmt_bal_account_name) + ' += ' + str(previous_stmt_delta), log_stack_depth)
            # log_in_color(logger, 'white', 'debug', str(date_iat) + ' ' + str(billing_cycle_payment_account_name) + ' += ' + str(billing_cycle_payment_delta), log_stack_depth)
            log_in_color(
                logger,
                "white",
                "debug",
                str(date_iat) + " " + str(eopc_account_name) + " += " + str(eopc_delta),
                log_stack_depth,
            )

            # Clean and update memo directives
            if md_to_keep != []:
                # Clean and update memo directives
                md_to_keep = [" " + md for md in md_to_keep if md]
                future_rows_only_df.at[f_i, "Memo Directives"] = ";".join(
                    md_to_keep
                ).strip()

        log_stack_depth -= 1
        log_in_color(
            logger,
            "cyan",
            "debug",
            "EXIT _propagate_credit_payment_prev_curr",
            log_stack_depth,
        )
        return future_rows_only_df

    # @profile
    @classmethod
    def _parse_memo_amount(cls, memo_line, log_stack_depth):
        """
        Parses a memo line and extracts the amount.
        Returns the amount as a float.
        """
        log_stack_depth += 1

        matches = re.search(r"(.*) \((.*)[-+]{1}\$(.*)\)", memo_line)
        if matches is None:
            raise ValueError(f"Malformed memo line: {memo_line}")

        memo_amount = matches.group(3)

        log_stack_depth -= 1
        return float(memo_amount)

    # @profile
    @classmethod
    def _update_memo_amount(cls, memo_line, new_amount, log_stack_depth):
        """
        Updates the amount in a memo line with a new amount.
        Returns the updated memo line.
        """
        # log_in_color(
        #     logger, "white", "debug", " ENTER _update_memo_amount", log_stack_depth
        # )
        log_stack_depth += 1

        #  r'(\-$' + f'{new_amount:.2f}' + ')'
        matches = re.search(r"(.*) \((.*)[-+]{1}\$(.*)\)", memo_line)
        if matches is None:
            raise ValueError(f"Malformed memo line: {memo_line}")

        og_amount = matches.group(3)

        # new_memo_line = re.sub(str(og_amount), f"{new_amount:.2f}", str(memo_line))
        new_memo_line = re.sub(str(og_amount), str(new_amount), str(memo_line))

        # if memo_line != new_memo_line:
        # log_in_color(
        #     logger,
        #     "cyan",
        #     "debug",
        #     "memo_line: " + str(memo_line),
        #     log_stack_depth,
        # )
        # log_in_color(
        #     logger,
        #     "cyan",
        #     "debug",
        #     str(og_amount) + " -> " + str(new_amount),
        #     log_stack_depth,
        # )
        # log_in_color(
        #     logger,
        #     "cyan",
        #     "debug",
        #     "new_memo_line: " + str(new_memo_line),
        #     log_stack_depth,
        # )

        log_stack_depth -= 1
        # log_in_color(
        #     logger, "white", "debug", " EXIT _update_memo_amount", log_stack_depth
        # )
        return new_memo_line

    # @profile
    @classmethod
    def _propagateOptimizationTransactionsIntoTheFuture(
        cls, end_date, account_set_before_p2_plus_txn, forecast_df, date_string, log_stack_depth, include_debug_columns=False #TODO unsure if include_debug_columns belongs here
    ):
        """
        Propagates optimization transactions into the future forecast.

        Parameters:
        - account_set_before_p2_plus_txn: Account set before processing transactions.
        - forecast_df: DataFrame containing the financial forecast.
        - date_string: The current date in 'YYYYMMDD' format.

        Returns:
        - Updated forecast_df with propagated transactions.
        """
        log_in_color(
            logger,
            "white",
            "debug",
            str(date_string)
            + " ENTER _propagateOptimizationTransactionsIntoTheFuture",
            log_stack_depth,
        )
        log_stack_depth += 1

        account_set_after_p2_plus_txn = cls._sync_account_set_w_forecast_day(
            copy.deepcopy(account_set_before_p2_plus_txn),
            forecast_df=forecast_df,
            d=date_string, log_stack_depth=log_stack_depth
        )

        A_df = account_set_after_p2_plus_txn.getAccounts()
        B_df = account_set_before_p2_plus_txn.getAccounts()

        # Compute account deltas
        account_deltas = A_df["Balance"] - B_df["Balance"]

        # log_in_color(logger, 'cyan', 'debug', 'Before:', log_stack_depth)
        # log_in_color(logger, 'cyan', 'debug', B_df.to_string(), log_stack_depth)
        #
        # log_in_color(logger, 'cyan', 'debug', 'After:', log_stack_depth)
        # log_in_color(logger, 'cyan', 'debug', A_df.to_string(), log_stack_depth)
        #
        # log_in_color(logger, 'cyan', 'debug', 'account_deltas:'+str(account_deltas), log_stack_depth)

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
                log_stack_depth,
            )
            raise AssertionError(
                "Account delta positive for checking, principal balance, or interest accounts."
            )

        account_deltas_list = account_deltas.tolist()
        account_delta_total = sum(Decimal(str(delta)) for delta in account_deltas_list)

        if account_delta_total == 0:
            log_in_color(
                logger,
                "white",
                "debug",
                str(date_string) + " no changes to propagate",
                log_stack_depth,
            )
            log_stack_depth -= 1
            log_in_color(
                logger,
                "white",
                "debug",
                str(date_string)
                + " EXIT _propagateOptimizationTransactionsIntoTheFuture",
                log_stack_depth,
            )
            return forecast_df

        log_in_color(logger, "cyan", "debug", "forecast_df:", log_stack_depth)
        log_in_color(
            logger, "cyan", "debug", forecast_df.to_string(), log_stack_depth
        )

        # log_in_color(
        #     logger,
        #     'magenta',
        #     'debug',
        #     f'ENTER _propagateOptimizationTransactionsIntoTheFuture({date_string})',
        #     log_stack_depth
        # )

        post_txn_row_df = forecast_df[forecast_df["Date"] == date_string]

        future_rows_only_df = forecast_df[
            forecast_df["Date"] > date_string
        ].reset_index(drop=True)

        # Generate interest accrual dates
        interest_accrual_dates__list_of_lists = []
        for _, a_row in A_df.iterrows():
            interest_cadence = a_row["Interest_Cadence"]
            if pd.isnull(interest_cadence) or interest_cadence == "None":
                interest_accrual_dates__list_of_lists.append([])
                continue

            start_date = a_row["Billing_Start_Date"]
            end_date = end_date
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

            start_date = billing_start_date
            end_date = end_date
            num_days = (end_date - start_date).days
            account_specific_bd = generate_date_sequence(
                billing_start_date, num_days, "monthly"
            )
            billing_dates__list_of_lists.append(account_specific_bd)
            billing_dates__dict[a_row["Name"]] = account_specific_bd

        for account in account_set_before_p2_plus_txn.accounts:
            billing_state = getattr(account, "billing_state", None)
            billing_start_date = getattr(billing_state, "billing_cycle_start_date", None)
            if pd.isnull(billing_start_date) or billing_start_date == "None":
                continue

            num_days = (end_date - billing_start_date).days
            account_specific_bd = generate_date_sequence(
                billing_start_date, num_days, "monthly"
            )
            if account.account_type == "credit":
                billing_dates__dict[f"{account.name}: Curr Stmt Bal"] = account_specific_bd
                billing_dates__dict[f"{account.name}: Prev Stmt Bal"] = account_specific_bd
                billing_dates__dict[
                    f"{account.name}: Credit Billing Cycle Payment Bal"
                ] = account_specific_bd
                billing_dates__dict[
                    f"{account.name}: Credit End of Prev Cycle Bal"
                ] = account_specific_bd
            elif account.account_type == "loan":
                billing_dates__dict[
                    f"{account.name}: Principal Balance"
                ] = account_specific_bd
                billing_dates__dict[f"{account.name}: Interest"] = account_specific_bd
                billing_dates__dict[
                    f"{account.name}: Loan Billing Cycle Payment Bal"
                ] = account_specific_bd

        # Mapping of account type combinations to processing functions
        account_type_combinations = {
            frozenset(
                [
                    "checking",
                    "credit prev stmt bal",
                    "credit curr stmt bal",
                    "credit billing cycle payment bal",
                ]
            ): cls._propagate_credit_payment_prev_curr,
            frozenset(
                [
                    "checking",
                    "principal balance",
                    "interest",
                    "loan billing cycle payment bal",
                ]
            ): cls._propagate_loan_payment_pbal_interest,
            frozenset(
                ["checking", "principal balance", "loan billing cycle payment bal"]
            ): cls._propagate_loan_payment_pbal_only,
            frozenset(
                ["checking", "interest", "loan billing cycle payment bal"]
            ): cls._propagate_loan_payment_interest_only,
            frozenset(
                ["checking", "credit prev stmt bal", "credit billing cycle payment bal"]
            ): cls._propagate_credit_payment_prev_only,
            frozenset(
                ["checking", "credit curr stmt bal", "credit billing cycle payment bal"]
            ): cls._propagate_credit_payment_curr_only,
            frozenset(["credit curr stmt bal"]): cls._propagate_credit_txn_curr_only,
        }

        # Build a delta table aligned with forecast account columns. The
        # propagation helpers index into account_deltas_list using forecast_df
        # column positions, so this must include placeholders for aggregate debt
        # columns when detailed debug columns are present.
        accounts_df = account_set_before_p2_plus_txn.getAccounts().copy()
        if include_debug_columns:
            base_accounts_df = accounts_df.set_index("Name", drop=False)
            before_balances = (
                account_set_before_p2_plus_txn.getForecastAccountBalances(
                    include_debug_columns=True
                )
            )
            post_txn_row = post_txn_row_df.iloc[0]
            account_rows = []
            account_deltas_list = []
            metadata_columns = {"Date", "Next Income Date", "Memo Directives", "Memo"}

            for column_name in forecast_df.columns:
                if column_name in metadata_columns:
                    continue
                base_name = column_name.split(":")[0]
                if base_name not in base_accounts_df.index:
                    continue

                base_row = base_accounts_df.loc[base_name]
                account_type = base_row["Account_Type"]
                if ": Curr Stmt Bal" in column_name:
                    account_type = "credit curr stmt bal"
                elif ": Prev Stmt Bal" in column_name:
                    account_type = "credit prev stmt bal"
                elif ": Credit Billing Cycle Payment Bal" in column_name:
                    account_type = "credit billing cycle payment bal"
                elif ": Credit End of Prev Cycle Bal" in column_name:
                    account_type = "credit end of prev cycle bal"
                elif ": Principal Balance" in column_name:
                    account_type = "principal balance"
                elif ": Interest" in column_name:
                    account_type = "interest"
                elif ": Loan Billing Cycle Payment Bal" in column_name:
                    account_type = "loan billing cycle payment bal"

                before_balance = before_balances.get(column_name, base_row["Balance"])
                after_balance = post_txn_row[column_name]
                delta = after_balance - before_balance
                if ":" not in column_name and account_type in ("credit", "loan"):
                    delta = 0

                account_rows.append(
                    {
                        "Name": column_name,
                        "Balance": before_balance,
                        "Min_Balance": base_row["Min_Balance"],
                        "Max_Balance": base_row["Max_Balance"],
                        "Account_Type": account_type,
                        "Billing_Start_Date": base_row["Billing_Start_Date"],
                        "Interest_Type": base_row["Interest_Type"],
                        "APR": base_row["APR"],
                        "Interest_Cadence": base_row["Interest_Cadence"],
                        "Minimum_Payment": base_row["Minimum_Payment"],
                        "Primary_Checking_Ind": base_row["Primary_Checking_Ind"],
                        "Delta": delta,
                    }
                )
                account_deltas_list.append(delta)

            accounts_df = pd.DataFrame(account_rows)
        else:
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
                str(date_string)
                + " before processing_function (checking case)",
                log_stack_depth,
            )
            log_in_color(
                logger, "yellow", "debug", forecast_df.to_string(), log_stack_depth
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
                    str(date_string)
                    + " processing_function "
                    + str(processing_function),
                    log_stack_depth,
                )

                # print('account_types_set:')
                # print(account_types_set)

                if processing_function:

                    log_in_color(
                        logger,
                        "yellow",
                        "debug",
                        str(date_string)
                        + " future_rows_only_df before processing_function",
                        log_stack_depth,
                    )
                    log_in_color(
                        logger,
                        "yellow",
                        "debug",
                        future_rows_only_df.to_string(),
                        log_stack_depth,
                    )

                    # Call the processing function
                    future_rows_only_df = processing_function(
                        relevant_account_info_df,
                        account_deltas_list,
                        future_rows_only_df,
                        forecast_df,
                        account_set_before_p2_plus_txn,
                        billing_dates__dict,
                        date_string,
                        post_txn_row_df,
                        log_stack_depth,
                    )

                else:
                    log_stack_depth -= 1
                    log_in_color(
                        logger,
                        "white",
                        "debug",
                        str(date_string)
                        + " EXIT _propagateOptimizationTransactionsIntoTheFuture",
                        log_stack_depth,
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
                    log_stack_depth -= 1
                    log_in_color(
                        logger,
                        "white",
                        "debug",
                        str(date_string)
                        + " EXIT _propagateOptimizationTransactionsIntoTheFuture",
                        log_stack_depth,
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
                    log_stack_depth -= 1
                    log_in_color(
                        logger,
                        "white",
                        "debug",
                        str(date_string)
                        + " EXIT _propagateOptimizationTransactionsIntoTheFuture",
                        log_stack_depth,
                    )
                    raise ValueError(error_msg)

            # If an error occurs here, it is because of systemic error in the algroithm
            # Not a valid rejection of a transactions
            # also check for rounding that caused real deltas to mismatch the memos!!!!
            for f_i, f_row in future_rows_only_df.iterrows():
                log_in_color(
                    logger, "white", "debug", "Date:" + str(f_row.Date), log_stack_depth
                )
                # we don't use index bc it won't be 1 and reindexing is expensive
                current_row = f_row
                current_date_string = f_row.Date
                first_row_date_string = future_rows_only_df.head(1).Date.iat[0]
                if current_date_string == first_row_date_string:
                    previous_row = forecast_df[forecast_df.Date == date_string]
                else:
                    previous_row = future_rows_only_df.loc[f_i - 1, :]

                log_in_color(
                    logger, "white", "debug", "previous_row:", log_stack_depth
                )
                if str(type(previous_row)) == "<class 'pandas.core.frame.DataFrame'>":
                    log_in_color(
                        logger,
                        "white",
                        "debug",
                        previous_row.to_string(),
                        log_stack_depth,
                    )
                else:
                    # type is pandas.core.series.Series
                    log_in_color(
                        logger,
                        "white",
                        "debug",
                        pd.DataFrame(previous_row).T.to_string(),
                        log_stack_depth,
                    )

                log_in_color(
                    logger, "white", "debug", "current_row:", log_stack_depth
                )
                if str(type(current_row)) == "<class 'pandas.core.frame.DataFrame'>":
                    log_in_color(
                        logger,
                        "white",
                        "debug",
                        current_row.to_string(),
                        log_stack_depth,
                    )
                else:
                    # type is pandas.core.series.Series
                    log_in_color(
                        logger,
                        "white",
                        "debug",
                        pd.DataFrame(current_row).T.to_string(),
                        log_stack_depth,
                    )

                account_type_by_base_name = dict(
                    zip(
                        account_set_before_p2_plus_txn.getAccounts()["Name"],
                        account_set_before_p2_plus_txn.getAccounts()["Account_Type"],
                    )
                )

                reported_acct_deltas = {}
                for md in f_row["Memo Directives"].split(";"):
                    if md.strip() == "":
                        continue
                    if "CC MIN PAYMENT ALREADY MADE" in md:
                        continue

                    log_in_color(
                        logger, "white", "debug", "md:" + str(md), log_stack_depth
                    )

                    txn_info = re.search(r"\((.*)\$(.*)\)", md)
                    if txn_info is None:
                        raise ValueError(f"Malformed memo directive: {md}")

                    acct_name = txn_info.group(1).split(":")[0]
                    acct_name = acct_name.replace("-", "").replace("+", "").strip()
                    acct_type = account_type_by_base_name.get(acct_name)
                    memo_balance = float(txn_info.group(2))

                    if acct_name not in reported_acct_deltas:
                        if "Loan" in acct_name:
                            continue  # todo shouldn't need to do this

                        if "-$" in md:
                            memo_balance = -abs(memo_balance)
                        elif "+$" in md:
                            memo_balance = abs(memo_balance)
                        if acct_type in ("credit", "loan"):
                            memo_balance *= -1

                        reported_acct_deltas[acct_name] = memo_balance

                        log_in_color(
                            logger,
                            "white",
                            "debug",
                            "reported_acct_deltas["
                            + str(acct_name)
                            + "] = "
                            + str(memo_balance),
                            log_stack_depth,
                        )
                    else:
                        if "-$" in md:
                            memo_balance = -abs(memo_balance)
                        elif "+$" in md:
                            memo_balance = abs(memo_balance)
                        if acct_type in ("credit", "loan"):
                            memo_balance *= -1

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
                            log_stack_depth,
                        )

                for m in f_row["Memo"].split(";"):
                    if "income" in m.lower() or m.strip() == "":
                        # bc otherwise would be double counted. this is a known design weakness
                        # don't bully me i'll cum
                        continue

                    log_in_color(
                        logger, "white", "debug", "m:" + str(m), log_stack_depth
                    )

                    txn_info = re.search(r"\((.*).*\$(.*)\)", m)
                    if txn_info is None:
                        raise ValueError(f"Malformed memo: {m}")

                    acct_name = txn_info.group(1)
                    acct_name = acct_name.replace("-", "").replace("+", "").strip()
                    memo_balance = float(txn_info.group(2))

                    if acct_name not in reported_acct_deltas:
                        if "Loan" in acct_name:
                            continue  # todo shouldn't need to do this

                        if "-$" in m:
                            memo_balance = -abs(memo_balance)
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
                            log_stack_depth,
                        )
                    else:
                        if "-$" in m:
                            memo_balance = -abs(memo_balance)
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
                            log_stack_depth,
                        )

                observed_acct_deltas = {}
                for cname in forecast_df.columns:
                    if cname in ["Date", "Next Income Date", "Memo Directives", "Memo"]:
                        continue
                    full_cname = cname
                    base_cname = cname.split(":")[0]
                    base_account_type = account_type_by_base_name.get(base_cname)
                    if ":" in full_cname and base_account_type in ("credit", "loan"):
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
                    cname = base_cname
                    current_delta = float(current_row[full_cname]) - float(
                        previous_row[full_cname]
                    )
                    if base_account_type in ("credit", "loan"):
                        current_delta *= -1
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
                                log_stack_depth,
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
                                log_stack_depth,
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
                        log_stack_depth,
                    )
                    log_in_color(
                        logger,
                        "white",
                        "debug",
                        "observed_acct_deltas.keys(): "
                        + str(observed_acct_deltas.keys()),
                        log_stack_depth,
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
                            log_stack_depth,
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
                            str(current_date_string)
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
                                log_stack_depth,
                            )
                            log_in_color(
                                logger,
                                "white",
                                "debug",
                                pd.DataFrame(current_row).T.to_string(),
                                log_stack_depth,
                            )
                        else:
                            log_in_color(
                                logger,
                                "white",
                                "debug",
                                future_rows_only_df.loc[(f_i - 1, f_i), :].to_string(),
                                log_stack_depth,
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
            str(date_string) + " after processing_function",
            log_stack_depth,
        )
        log_in_color(
            logger, "yellow", "debug", forecast_df.to_string(), log_stack_depth
        )

        log_stack_depth -= 1
        log_in_color(
            logger,
            "white",
            "debug",
            str(date_string)
            + " EXIT _propagateOptimizationTransactionsIntoTheFuture",
            log_stack_depth,
        )
        return forecast_df

    # @profile
    @classmethod
    def _updateProposedTransactionsBasedOnOtherSets(
        cls, confirmed_df, proposed_df, deferred_df, skipped_df, log_stack_depth
    ):

        log_stack_depth += 1

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

        log_stack_depth -= 1
        # log_in_color(logger, 'cyan', 'debug', 'EXIT _updateProposedTransactionsBasedOnOtherSets',log_stack_depth)
        return remaining_unproposed_transactions_df

    # def _assessPotentialOptimizationsApproximate(
    #     cls,
    #     forecast_df,
    #     account_set,
    #     memo_rule_set,
    #     confirmed_df,
    #     proposed_df,
    #     deferred_df,
    #     skipped_df,
    #     raise__satisfice_failed_exception,
    #     progress_bar=None,
    #     log_stack_depth
    # ):
    #     F = "F:" + str(forecast_df.shape[0])
    #     C = "C:" + str(confirmed_df.shape[0])
    #     P = "P:" + str(proposed_df.shape[0])
    #     D = "D:" + str(deferred_df.shape[0])
    #     S = "S:" + str(skipped_df.shape[0])
    #     # log_in_color(logger,'magenta','debug','ENTER _assessPotentialOptimizationsApproximate( '+F+' '+C+' '+P+' '+D+' '+S+' )',log_stack_depth)
    #     log_stack_depth += 1
    #     all_days = (
    #         forecast_df.Date
    #     )  # todo havent tested this, but forecast_df has been _satisficed so it has all the dates

    #     # Schema is: Date, Priority, Amount, Memo, Deferrable, Partial_Payment_Allowed
    #     full_budget_schedule_df = pd.concat(
    #         [confirmed_df, proposed_df, deferred_df, skipped_df]
    #     )
    #     full_budget_schedule_df.reset_index(drop=True, inplace=True)

    #     unique_priority_indices = full_budget_schedule_df.Priority.unique()
    #     unique_priority_indices.sort()

    #     last_iteration_ts = None  # this is here to remove a warning

    #     if not raise__satisfice_failed_exception:
    #         log_in_color(logger, "white", "debug", "Beginning Optimization.")
    #         # log_in_color(logger, 'white', 'debug', cls.start_date + ' -> ' + cls.end_date)
    #         # log_in_color(logger, 'white', 'debug', 'Priority Indices: ' + str(unique_priority_indices))
    #         last_iteration_ts = datetime.datetime.now()

    #     for priority_index in unique_priority_indices:

    #         if priority_index == 1:
    #             continue  # because this was handled by _satisfice

    #         for date_string in all_days:
    #             # print('date_string:'+str(date_string))
    #             if date_string == forecast_df.head(1).Date.iat[0]:
    #                 # if date_string == cls.start_date:
    #                 continue  # first day is considered final

    #             if not raise__satisfice_failed_exception:
    #                 if progress_bar is not None:
    #                     progress_bar.update(1)
    #                     progress_bar.refresh()

    #                 iteration_time_elapsed = datetime.datetime.now() - last_iteration_ts
    #                 last_iteration_ts = datetime.datetime.now()
    #                 log_string = (
    #                     str(priority_index)
    #                     + " "
    #                     + "PLACEHOLDER 1"
    #                 )
    #                 log_string += "     " + str(iteration_time_elapsed)
    #                 # log_in_color(logger, 'white', 'debug', log_string )

    #             # log_in_color(logger, 'magenta', 'info', 'p' + str(priority_index) + ' ' + str(date_string),log_stack_depth)

    #             remaining_unproposed_transactions_df = (
    #                 cls._updateProposedTransactionsBasedOnOtherSets(
    #                     confirmed_df, proposed_df=proposed_df, deferred_df=deferred_df, skipped_df=skipped_df
    #)
    #             )

    #             # todo idk if this is necessary
    #             account_set = cls._sync_account_set_w_forecast_day(
    #                 account_set, forecast_df=forecast_df, d=d_string
    #)

    #             # todo maybe this could be moved down? not sure
    #             account_set_before_p2_plus_txn = copy.deepcopy(account_set)

    #             # todo not sure if this is necessary
    #             account_set = cls._sync_account_set_w_forecast_day(
    #                 account_set, forecast_df=forecast_df, d=d_string
    #)

    #             # log_in_color(logger, 'yellow', 'debug','proposed_df before eTFD:')
    #             # log_in_color(logger, 'yellow', 'debug', proposed_df.to_string())

    #             forecast_df, confirmed_df, deferred_df, skipped_df = (
    #                 cls._executeTransactionsForDayApproximate(
    #                     account_set=account_set,
    #                     forecast_df=forecast_df,
    #                     d=d_string,
    #                     memo_set=memo_rule_set,
    #                     confirmed_df=confirmed_df,
    #                     proposed_df=remaining_unproposed_transactions_df,
    #                     deferred_df=deferred_df,
    #                     skipped_df=skipped_df,
    #                     priority_level=priority_index,
    #                 )
    #             )

    #             # log_in_color(logger, 'yellow', 'debug', 'proposed after eTFD:')
    #             # log_in_color(logger, 'yellow', 'debug', proposed_df.to_string())

    #             account_set = cls._sync_account_set_w_forecast_day(
    #                 account_set, forecast_df=forecast_df, d=d_string
    #)

    #             # this is necessary to make balance deltas propoagate only once
    #             if raise__satisfice_failed_exception:

    #                 # regarding why the input params are what they are here:
    #                 # since the budget schedule does not have Account_From and Account_To, we infer which accounts were
    #                 # affected by comparing the before and after, hence this method accepts the prior and current state
    #                 # to modify forecast_df
    #                 # Furthermore, additional loan payments affect the allocation of future minimum loan payments
    #                 # so p1 minimumpayments, which aren't even BudgetItems as of 12/31/23.... must be edited
    #                 # it kind of makes more sense to refactor and have credit card minimum payments and loan minimum
    #                 # # payments as budget items....
    #                 #
    #                 # Doing that though creates a coupling between the AccountSet and BudgetSet classes that I don't like...
    #                 # I only recently got the full detail of what happens into the Memo field, but I think that that is the answer
    #                 # There will be information encoded in the Memo column that will not appear anywhere else
    #                 #
    #                 # print(forecast_df.to_string())
    #                 forecast_df = cls._propagateOptimizationTransactionsIntoTheFuture(
    #                     account_set_before_p2_plus_txn,
    #                     forecast_df,
    #                     date_string,
    #                 )
    #                 # print(forecast_df.to_string())

    #     log_stack_depth -= 1
    #     # log_in_color(logger, 'magenta', 'debug', 'EXIT _assessPotentialOptimizations() C:'+str(confirmed_df.shape[0])+' D:'+str(deferred_df.shape[0])+' S:'+str(skipped_df.shape[0]),log_stack_depth)
    #     return forecast_df, skipped_df, confirmed_df, deferred_df

    # @profile
    @classmethod
    def _assessPotentialOptimizations(
        cls,
        end_date,
        forecast_df,
        account_set,
        memo_rule_set,
        confirmed_df,
        proposed_df,
        deferred_df,
        skipped_df,
        raise__satisfice_failed_exception,
        log_stack_depth,
        progress_bar=None,
        include_debug_columns=False
    ):
        # log_in_color(
        #     logger,
        #     "white",
        #     "info",
        #     "ENTER _assessPotentialOptimizations",
        #     log_stack_depth,
        # )
        log_stack_depth += 1

        # log_in_color(
        #     logger, "white", "info", forecast_df.to_string(), log_stack_depth
        # )

        all_days = forecast_df.Date

        # Schema is: Date, Priority, Amount, Memo, Deferrable, Partial_Payment_Allowed
        full_budget_schedule_df = pd.concat(
            [confirmed_df, proposed_df, deferred_df, skipped_df]
        )
        full_budget_schedule_df.reset_index(drop=True, inplace=True)

        unique_priority_indices = list(full_budget_schedule_df["Priority"].unique())
        unique_priority_indices.sort()

        last_iteration_ts = None  # this is here to remove a warning

        if not raise__satisfice_failed_exception:
            log_in_color(logger, "green", "debug", "Beginning Optimization.")
            # log_in_color(logger, 'white', 'info', forecast_df.to_string())
            last_iteration_ts = datetime.datetime.now()

        # print('Beginning unique_priority_indices:'+str(unique_priority_indices))
        for priority_index in unique_priority_indices:
            if priority_index == 1:
                continue  # because this was handled by _satisfice

            for d in all_days:
                if d == forecast_df.head(1).Date.iat[0]:
                    # if date_string == cls.start_date:
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
                        + "PLACEHOLDER 2"
                    )
                    log_string += "     " + str(iteration_time_elapsed)
                    # log_in_color(logger, 'white', 'debug', log_string )

                # log_in_color(logger, 'magenta', 'info', 'p' + str(priority_index) + ' ' + str(date_string),log_stack_depth)

                remaining_unproposed_transactions_df = (
                    cls._updateProposedTransactionsBasedOnOtherSets(
                        confirmed_df=confirmed_df, proposed_df=proposed_df, deferred_df=deferred_df, skipped_df=skipped_df, log_stack_depth=log_stack_depth
                    )
                )

                # todo idk if this is necessary
                account_set = cls._sync_account_set_w_forecast_day(
                    account_set=account_set, forecast_df=forecast_df, d=d, log_stack_depth=log_stack_depth
                )

                # todo maybe this could be moved down? not sure
                account_set_before_p2_plus_txn = copy.deepcopy(account_set)

                # todo not sure if this is necessary
                account_set = cls._sync_account_set_w_forecast_day(
                    account_set=account_set, forecast_df=forecast_df, d=d, log_stack_depth=log_stack_depth
                )

                try:
                    # print('BEFORE ETFD:')
                    # print(confirmed_df.to_string())
                    forecast_df, confirmed_df, deferred_df, skipped_df = (
                        cls._executeTransactionsForDay(
                            end_date=end_date,
                            account_set=account_set,
                            forecast_df=forecast_df,
                            d=d,
                            memo_set=memo_rule_set,
                            confirmed_df=confirmed_df,
                            proposed_df=remaining_unproposed_transactions_df,
                            deferred_df=deferred_df,
                            skipped_df=skipped_df,
                            priority_level=priority_index, 
                            log_stack_depth=log_stack_depth,
                            include_debug_columns=include_debug_columns
                        )
                    )
                    # print('AFTER ETFD:')
                    # print(confirmed_df.to_string())
                except Exception as e:
                    # log_in_color(logger, 'magenta', 'debug', forecast_df.to_string(), log_stack_depth)
                    log_stack_depth -= 1
                    # log_in_color(
                    #     logger,
                    #     "white",
                    #     "debug",
                    #     "EXIT _assessPotentialOptimizations",
                    #     log_stack_depth,
                    # )
                    raise e

                # log_in_color(logger, 'green', 'info', 'forecast_df after eTFD ('+str(date_string)+'):', log_stack_depth)
                # log_in_color(logger, 'green', 'info', forecast_df.to_string(), log_stack_depth)

                # print('assess optimizations case 3 sync')
                account_set = cls._sync_account_set_w_forecast_day(
                    account_set=account_set, forecast_df=forecast_df, d=d, log_stack_depth=log_stack_depth)

                #
                # log_in_color(logger, 'magenta', 'debug', 'before', log_stack_depth)
                # log_in_color(logger, 'magenta', 'debug', account_set_before_p2_plus_txn.getAccounts().to_string(), log_stack_depth)
                # log_in_color(logger, 'magenta', 'debug', 'after', log_stack_depth)
                # log_in_color(logger, 'magenta', 'debug', account_set.getAccounts().to_string(), log_stack_depth)

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
                    forecast_df = cls._propagateOptimizationTransactionsIntoTheFuture(end_date=end_date,
                        account_set_before_p2_plus_txn=account_set_before_p2_plus_txn,
                        forecast_df=forecast_df,
                        date_string=d, 
                        log_stack_depth=log_stack_depth,
                        include_debug_columns=include_debug_columns
                    )

                    # print('AFTER')
                    # print(forecast_df.to_string())
        # log_in_color(logger, 'magenta', 'debug', forecast_df.to_string(), log_stack_depth)

        log_stack_depth -= 1
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     "EXIT _assessPotentialOptimizations",
        #     log_stack_depth,
        # )
        return forecast_df, skipped_df, confirmed_df, deferred_df

    @classmethod
    def _cleanUpAfterFailedSatisfice(
        cls, end_date, confirmed_df, proposed_df, deferred_df, skipped_df, log_stack_depth
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        log_in_color(logger, 'red', 'debug', 'ENTER _cleanUpAfterFailedSatisfice', log_stack_depth)
        # this logic takes everything that was not executed and adds it to skipped_df
        not_confirmed_sel_vec = [
            (
                d
                > end_date
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
                d
                <= end_date
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

    @classmethod
    def _updateEndOfPrevCycleBal(
        cls, forecast_df, account_set, current_forecast_row_df, log_stack_depth
    ):
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     str(current_forecast_row_df.Date.iat[0])
        #     + " ENTER _updateEndOfPrevCycleBal",
        #     log_stack_depth,
        # )
        log_stack_depth += 1
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

            billing_start_datetime = account_row.Billing_Start_Date

            billing_start_date_plus_1= (
                billing_start_datetime + datetime.timedelta(days=1)
            )

            current_date = current_forecast_row_df.Date.iloc[0]

            num_days_since_bsd = (current_date - billing_start_datetime).days
            num_days_since_bsd_plus_1 = (
                current_date - billing_start_date_plus_1
            ).days

            # we could put some return condition here like, if num_days_since_bsd < 30 then return
            # but month lengths are weird so let's just rely on the more robust check

            # Generate billing days
            # print('num_days_since_bsd_plus_1:'+str(num_days_since_bsd_plus_1))
            if num_days_since_bsd_plus_1 >= 0:
                update_days = set(
                    generate_date_sequence(
                        billing_start_date_plus_1,
                        num_days_since_bsd_plus_1,
                        "monthly",
                    )
                )
            else:
                update_days = set()
            # print('update_days:'+str(update_days))

            if current_date not in update_days or len(update_days) == 0:
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

            previous_row_df = forecast_df[forecast_df.Date == prev_date]

            # log_in_color(logger, 'cyan', 'debug', 'previous_row_df:', log_stack_depth)
            # log_in_color(logger, 'cyan', 'debug', previous_row_df.to_string(), log_stack_depth)

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
                #     interest_accrued = cls._extract_interest_accrued_amount(account_basename=account_basename,memo_directives=previous_row_df['Memo Directives'].iat[0])
                # else:
                #     interest_accrued = 0
                #     pass #no interest was accrued that needs to be accounted for
                # new_bal -= interest_accrued

                # log_in_color(logger, 'white', 'debug', 'SET '+str(eopc_aname)+' = '+str(new_bal), log_stack_depth)
                current_forecast_row_df[eopc_aname] = new_bal
        # log_in_color(logger, 'white', 'debug', 'returning this row:', log_stack_depth)
        # log_in_color(logger, 'white', 'debug', current_forecast_row_df.to_string(), log_stack_depth)

        log_stack_depth -= 1
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     str(current_forecast_row_df.Date.iat[0]) + " EXIT _updateEndOfPrevCycleBal",
        #     log_stack_depth,
        # )
        return current_forecast_row_df

    # @profile
    @classmethod
    def _satisfice(
        cls,
        start_date,
        end_date,
        list_of_date_strings,
        confirmed_df,
        account_set,
        memo_rule_set,
        forecast_df,
        raise__satisfice_failed_exception,
        log_stack_depth,
        progress_bar=None,
        include_debug_columns=False
    ):
        # log_in_color(logger, "white", "info", "ENTER _satisfice", log_stack_depth)
        log_stack_depth += 1

        all_days = list_of_date_strings  # Rename for clarity

        for d in all_days:
            if progress_bar:
                progress_bar.update(1)
                progress_bar.refresh()

            # log_in_color(logger, 'magenta', 'info', str(date_str)+' forecast_df', log_stack_depth)
            # log_in_color(logger, 'magenta', 'info', forecast_df.to_string(), log_stack_depth)

            # Skip the first day, considered as final
            if d == start_date:
                continue
            # log_in_color(logger, "white", "info", 'satisfice TOP :: '+d.strftime('%Y-%m-%d'), log_stack_depth)

            try:
                if not (forecast_df.Date == d).any():
                    forecast_df = cls._addANewDayToTheForecast(forecast_df, d)

                # Log transaction details if exception handling is not strict
                if not raise__satisfice_failed_exception:
                    log_string = f"1 {d}"

                if not confirmed_df.empty:
                    pass
                    # log_in_color(logger, 'magenta', 'debug', 'satisfice confirmed_df:', log_stack_depth)
                    # log_in_color(logger, 'magenta', 'debug', confirmed_df.to_string(), log_stack_depth)

                forecast_df.loc[forecast_df.Date == d] = (
                    cls._processCreditCardBillingDayForDay(
                        account_set=account_set,
                        current_forecast_row_df=forecast_df[forecast_df.Date == d],
                        log_stack_depth=log_stack_depth,
                    )
                )

                account_set = cls._sync_account_set_w_forecast_day(
                    account_set=account_set,
                    forecast_df=forecast_df,
                    d=d,
                    log_stack_depth=log_stack_depth,
                )

                # Calculate loan interest accruals before same-day loan payments.
                forecast_df.loc[forecast_df.Date == d] = (
                    cls._calculateLoanInterestAccrualsForDay(
                        account_set=account_set, current_forecast_row_df=forecast_df[forecast_df.Date == d], log_stack_depth=log_stack_depth
                    )
                )

                account_set = cls._sync_account_set_w_forecast_day(
                    account_set=account_set, forecast_df=forecast_df, d=d, log_stack_depth=log_stack_depth
                )

                # Execute loan minimum payments before same-day loan payments.
                forecast_df.loc[forecast_df.Date == d] = (
                    cls._executeLoanMinimumPayments(
                        account_set=account_set, current_forecast_row_df=forecast_df[forecast_df.Date == d], log_stack_depth=log_stack_depth
                    )
                )

                account_set = cls._sync_account_set_w_forecast_day(
                    account_set=account_set, forecast_df=forecast_df, d=d, log_stack_depth=log_stack_depth)

                # Execute transactions for the day, priority 1 (non-negotiable)
                forecast_df, confirmed_df, deferred_df, skipped_df = (
                    cls._executeTransactionsForDay(
                        end_date=end_date,
                        account_set=account_set,
                        forecast_df=forecast_df,
                        d=d,
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
                        priority_level=1, log_stack_depth=log_stack_depth
                    )
                )

                # Sync account set after transactions
                account_set = cls._sync_account_set_w_forecast_day(
                    account_set=account_set, forecast_df=forecast_df, d=d, log_stack_depth=log_stack_depth
                )

                # log_in_color(logger, 'green', 'info', 'BEFORE cc min payment', log_stack_depth)
                # log_in_color(logger, 'green', 'info', forecast_df.to_string(), log_stack_depth)

                forecast_df.loc[forecast_df.Date == d] = (
                    cls._updateEndOfPrevCycleBal(
                        forecast_df=forecast_df,
                        account_set=account_set,
                        current_forecast_row_df=forecast_df[forecast_df.Date == d], log_stack_depth=log_stack_depth
                    )
                )

                account_set = cls._sync_account_set_w_forecast_day(
                    account_set=account_set, forecast_df=forecast_df, d=d, log_stack_depth=log_stack_depth)

                # Execute credit card minimum payments
                forecast_df.loc[forecast_df.Date == d] = (
                    cls._executeCreditCardMinimumPayments(
                        forecast_df=forecast_df,
                        account_set=account_set,
                        current_forecast_row_df=forecast_df[forecast_df.Date == d], log_stack_depth=log_stack_depth
                    )
                )

                # log_in_color(logger, 'green', 'info', 'AFTER cc min payment', log_stack_depth)
                # log_in_color(logger, 'green', 'info', forecast_df.to_string(), log_stack_depth)

                # Final sync for the day
                account_set = cls._sync_account_set_w_forecast_day(
                    account_set=account_set, forecast_df=forecast_df, d=d, log_stack_depth=log_stack_depth)
                
                # log_in_color(logger, "white", "info", 'satisfice BOTTOM :: '+d.strftime('%Y-%m-%d'), log_stack_depth)

            except AccountBoundaryError as e:
                error_message = str(e.args)
                log_in_color(logger, 'red', 'error', error_message, log_stack_depth)
                if not raise__satisfice_failed_exception:
                    cls.end_date = d - datetime.timedelta(days=1)

                    log_in_color(
                        logger,
                        "cyan",
                        "error",
                        "Account Boundaries were violated",
                        log_stack_depth,
                    )
                    log_in_color(
                        logger, "cyan", "error", error_message, log_stack_depth
                    )
                    # log_in_color(
                    #     logger,
                    #     "cyan",
                    #     "error",
                    #     "State at failure:",
                    #     log_stack_depth,
                    # )
                    # log_in_color(
                    #     logger,
                    #     "cyan",
                    #     "error",
                    #     forecast_df.to_string(),
                    #     log_stack_depth,
                    # )

                    log_stack_depth -= 1
                    # log_in_color(
                    #     logger, "white", "info", "EXIT _satisfice", log_stack_depth
                    # )
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

        # log_in_color(
        #     logger, "white", "info", forecast_df.to_string(), log_stack_depth
        # )
        log_stack_depth -= 1
        # log_in_color(logger, "white", "info", "EXIT _satisfice", log_stack_depth)
        return forecast_df  # _satisfice_success = True

    # @profile
    @classmethod
    def _computeOptimalForecast(cls,
        start_date,
        end_date,
        confirmed_df,
        proposed_df,
        deferred_df,
        skipped_df,
        account_set,
        memo_rule_set,
        log_stack_depth,
        raise__satisfice_failed_exception=True,
        progress_bar=None,
        include_debug_columns=False
    ):
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     "ENTER _computeOptimalForecast "
        #     + str(start_date)
        #     + " -> "
        #     + str(end_date),
        #     log_stack_depth,
        # )
        log_stack_depth += 1

        start_date = cls._normalize_date_value(start_date)
        end_date = cls._normalize_date_value(end_date)

        # if not confirmed_df.empty:
        #     log_in_color(logger, 'white', 'debug', 'confirmed_df:', log_stack_depth)
        #     log_in_color(logger, 'white', 'debug', confirmed_df.to_string(), log_stack_depth)
        #
        # if not proposed_df.empty:
        #     log_in_color(logger, 'white', 'debug', 'proposed_df:', log_stack_depth)
        #     log_in_color(logger, 'white', 'debug', proposed_df.to_string(), log_stack_depth)
        # log_in_color(logger, 'magenta', 'debug', account_set.getAccounts().to_string(), log_stack_depth)

        # Reset index for all input DataFrames to ensure clean processing
        for df in [confirmed_df, proposed_df, deferred_df, skipped_df]:
            cls._normalize_dataframe_date_column(df)
            df.reset_index(drop=True, inplace=True)

        if confirmed_df.shape[0] > 1:
            confirmed_df = cls._sortTxnsToPreventErrors(
                confirmed_df, account_set=account_set, memo_set=memo_rule_set, log_stack_depth=log_stack_depth
            )

        if proposed_df.shape[0] > 1:
            proposed_df = cls._sortTxnsToPreventErrors(
                proposed_df, account_set=account_set, memo_set=memo_rule_set, log_stack_depth=log_stack_depth)

        # Generate the list of days for the forecast, excluding the first day
        all_days = generate_date_sequence(start_date, 
                                          (end_date - start_date).days,  
                                          "daily")
        # logger.debug('all_days:')
        # logger.debug(all_days)
        # all_days = [d.strftime("%Y%m%d") for d in all_days]

        # Initialize the forecast DataFrame with the first day's account balances
        forecast_df = cls._getInitialForecastRow(start_date=start_date, account_set=account_set, include_debug_columns=include_debug_columns)

        # Attempt to _satisfice (execute priority 1 transactions for each day)
        # log_in_color(logger, 'magenta', 'debug', confirmed_df.to_string(), log_stack_depth)
        _satisfice_df = cls._satisfice(start_date,
            end_date,
            all_days,
            confirmed_df=confirmed_df,
            account_set=account_set,
            memo_rule_set=memo_rule_set,
            forecast_df=forecast_df,
            raise__satisfice_failed_exception=raise__satisfice_failed_exception,
            progress_bar=progress_bar,
            log_stack_depth=log_stack_depth,
            include_debug_columns=include_debug_columns
        )

        # Check if _satisfice succeeded by verifying the last date in the forecast
        _satisfice_success = _satisfice_df.tail(1)["Date"].iat[0] == end_date

        # Update forecast DataFrame with the result of _satisfice
        forecast_df = _satisfice_df

        if _satisfice_success:
            # Log success message when _satisfice completes successfully at the top level
            if not raise__satisfice_failed_exception:
                pass
                # log_in_color(logger, "white", "debug", "Satisfice succeeded.")
                # log_in_color(logger, "white", "debug", _satisfice_df.to_string())

            # Not sure if this try block is needed
            try:

                # Assess potential optimizations across all transaction levels
                forecast_df, skipped_df, confirmed_df, deferred_df = (
                    cls._assessPotentialOptimizations(
                        end_date=end_date,
                        forecast_df=forecast_df,
                        account_set=account_set,
                        memo_rule_set=memo_rule_set,
                        confirmed_df=confirmed_df,
                        proposed_df=proposed_df,
                        deferred_df=deferred_df,
                        skipped_df=skipped_df,
                        raise__satisfice_failed_exception=raise__satisfice_failed_exception,
                        progress_bar=progress_bar, 
                        log_stack_depth=log_stack_depth,
                        include_debug_columns=include_debug_columns
                    )
                )

            except Exception as e:
                log_stack_depth -= 1
                # log_in_color(
                #     logger,
                #     "white",
                #     "debug",
                #     "EXIT _computeOptimalForecast",
                #     log_stack_depth,
                # )
                raise e
        else:
            # Handle _satisfice failure: clean up unprocessed transactions
            if not raise__satisfice_failed_exception:
                log_in_color(logger, "white", "debug", "Satisfice failed.")

            confirmed_df, deferred_df, skipped_df = cls._cleanUpAfterFailedSatisfice(
                end_date=end_date,
                confirmed_df=confirmed_df, 
                proposed_df=proposed_df,
                deferred_df=deferred_df, 
                skipped_df=skipped_df,
                log_stack_depth=log_stack_depth)

        # Decrement the log stack depth as we exit this method
        log_stack_depth -= 1

        # Return the forecast and updated DataFrames
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     "EXIT _computeOptimalForecast",
        #     log_stack_depth,
        # )
        return [forecast_df, skipped_df, confirmed_df, deferred_df]

    # def to_json(cls):
    #     """
    #     Returns a JSON string representing the ExpenseForecast object.

    #     #todo ExpenseForecast.to_json() say what the columns are

    #     :return:
    #     """

    #     # return jsonpickle.encode(cls, indent=4)

    #     JSON_string = "{\n"

    #     unique_id_string = '"unique_id":"' + cls.unique_id + '",\n'

    #     # if cls.start_ts is not None:
    #     # if hasattr(cls,'start_ts'):
    #     if cls.start_ts is not None:
    #         start_ts_string = '"start_ts":"' + str(cls.start_ts) + '",\n'
    #         end_ts_string = '"end_ts":"' + str(cls.end_ts) + '",\n'
    #     else:
    #         start_ts_string = '"start_ts":"None",\n'
    #         end_ts_string = '"end_ts":"None",\n'

    #     start_date_string = '"start_date":' + cls.start_date + ",\n"
    #     end_date_string = '"end_date":' + cls.end_date + ",\n"

    #     memo_rule_set_string = (
    #         '"initial_memo_rule_set":' + cls.initial_memo_rule_set.to_json() + ","
    #     )
    #     initial_account_set_string = (
    #         '"initial_account_set":' + cls.initial_account_set.to_json() + ","
    #     )
    #     initial_budget_set_string = (
    #         '"initial_budget_set":' + cls.initial_budget_set.to_json() + ","
    #     )

    #     if cls.start_ts is None:
    #         forecast_df_string = '"forecast_df":"None",\n'
    #         skipped_df_string = '"skipped_df":"None",\n'
    #         confirmed_df_string = '"confirmed_df":"None",\n'
    #         deferred_df_string = '"deferred_df":"None",\n'
    #     else:
    #         tmp__forecast_df = cls.forecast_df.copy()
    #         tmp__skipped_df = cls.skipped_df.copy()
    #         tmp__confirmed_df = cls.confirmed_df.copy()
    #         tmp__deferred_df = cls.deferred_df.copy()

    #         # standardize decimal points

    #         # todo every value should have a decimal
    #         for i in range(1, len(tmp__forecast_df.columns) - 2):
    #             column_name = tmp__forecast_df.columns[i]
    #             tmp__forecast_df[column_name] = [
    #                 "{:.2f}".format(v) for v in tmp__forecast_df[column_name]
    #             ]

    #         tmp__forecast_df["Date"] = tmp__forecast_df["Date"].astype(str)
    #         if tmp__skipped_df.shape[0] > 0:
    #             tmp__skipped_df["Date"] = tmp__skipped_df["Date"].astype(str)
    #         tmp__confirmed_df["Date"] = tmp__confirmed_df["Date"].astype(str)
    #         if tmp__deferred_df.shape[0] > 0:
    #             tmp__deferred_df["Date"] = tmp__deferred_df["Date"].astype(str)

    #         normalized_forecast_df_JSON_string = tmp__forecast_df.to_json(
    #             orient="records", date_format="iso"
    #         )
    #         normalized_skipped_df_JSON_string = tmp__skipped_df.to_json(
    #             orient="records", date_format="iso"
    #         )
    #         normalized_confirmed_df_JSON_string = tmp__confirmed_df.to_json(
    #             orient="records", date_format="iso"
    #         )
    #         normalized_deferred_df_JSON_string = tmp__deferred_df.to_json(
    #             orient="records", date_format="iso"
    #         )

    #         forecast_df_string = (
    #             '"forecast_df":' + normalized_forecast_df_JSON_string + ",\n"
    #         )
    #         skipped_df_string = (
    #             '"skipped_df":' + normalized_skipped_df_JSON_string + ",\n"
    #         )
    #         confirmed_df_string = (
    #             '"confirmed_df":' + normalized_confirmed_df_JSON_string + ",\n"
    #         )
    #         deferred_df_string = (
    #             '"deferred_df":' + normalized_deferred_df_JSON_string + ",\n"
    #         )

    #     JSON_string += unique_id_string
    #     JSON_string += '"forecast_set_name":"' + cls.forecast_set_name + '",\n'
    #     JSON_string += '"forecast_name":"' + cls.forecast_name + '",\n'

    #     JSON_string += start_ts_string
    #     JSON_string += end_ts_string

    #     JSON_string += start_date_string
    #     JSON_string += end_date_string
    #     JSON_string += memo_rule_set_string
    #     JSON_string += initial_account_set_string
    #     JSON_string += initial_budget_set_string

    #     JSON_string += forecast_df_string
    #     JSON_string += skipped_df_string
    #     JSON_string += confirmed_df_string
    #     JSON_string += deferred_df_string

    #     account_milestone_string = jsonpickle.encode(
    #         cls.account_milestone_results, indent=4, unpicklable=False, make_refs=False
    #     )

    #     memo_milestone_string = jsonpickle.encode(
    #         cls.memo_milestone_results, indent=4, unpicklable=False, make_refs=False
    #     )

    #     composite_milestone_string = jsonpickle.encode(
    #         cls.composite_milestone_results,
    #         indent=4,
    #         unpicklable=False,
    #         make_refs=False,
    #     )

    #     JSON_string += '"milestone_set":' + cls.milestone_set.to_json()

    #     JSON_string += ",\n"
    #     JSON_string += '"account_milestone_results":' + account_milestone_string + ",\n"
    #     JSON_string += '"memo_milestone_results":' + memo_milestone_string + ",\n"
    #     JSON_string += '"composite_milestone_results":' + composite_milestone_string

    #     JSON_string += "}"

    #     # to pretty print
    #     JSON_string = json.dumps(json.loads(JSON_string), indent=4)

    #     return JSON_string

    # def to_html(cls):
    #     # todo consider adding commas to long numbers
    #     # res = ('{:,}'.format(test_num))
    #     return cls.forecast_df.to_html()

    @classmethod
    def compute_forecast_difference(
        cls,
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

        ### should not be necessary
        # forecast_df["Date"] = forecast_df.Date.apply(
        #     lambda x: datetime.datetime.strptime(x, "%Y%m%d"), 0
        # )
        # forecast2_df['Date'] = forecast_df.Date.apply(lambda x: datetime.datetime.strptime(x, '%Y%m%d'), 0)

        forecast_df.reset_index(inplace=True, drop=True)
        forecast2_df.reset_index(inplace=True, drop=True)
        cls._normalize_dataframe_date_column(forecast_df)
        cls._normalize_dataframe_date_column(forecast2_df)

        forecast_df = forecast_df.reindex(sorted(forecast_df.columns), axis=1)
        forecast2_df = forecast2_df.reindex(sorted(forecast2_df.columns), axis=1)

        # print('compute_forecast_difference()')
        # print('cls.forecast_df:')
        # print(cls.forecast_df.to_string())
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
                print("cls.forecast_df.shape[1]:" + str(cls.forecast_df.shape[1]))
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
                forecast2_df = pd.concat([RHS_zero_row_to_add, cls.forecast_df])
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
            # res = forecast2_df[c].sub(cls.forecast_df[c])
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
# 
    # def to_excel(cls, output_dir):

    #     # first page, run parameters
    #     summary_df = cls.getSummaryPageForExcelLandingPageDF()
    #     account_set_df = cls.initial_account_set.getAccounts()
    #     budget_set_df = cls.initial_budget_set.getBudgetItems()
    #     memo_rule_set_df = cls.initial_memo_rule_set.getMemoRules()
    #     choose_one_set_df = pd.DataFrame()  # todo
    #     account_milestones_df = cls.milestone_set.getAccountMilestonesDF()
    #     memo_milestones_df = cls.milestone_set.getMemoMilestonesDF()
    #     composite_milestones_df = cls.milestone_set.getCompositeMilestonesDF()
    #     milestone_results_df = cls.getMilestoneResultsDF()

    #     with pd.ExcelWriter(
    #         output_dir + "/Forecast_" + cls.unique_id + ".xlsx", engine="xlsxwriter"
    #     ) as writer:
    #         summary_df.to_excel(writer, sheet_name="Summary", index=False)
    #         for column in summary_df:
    #             column_length = max(
    #                 summary_df[column].astype(str).map(len).max(), len(column)
    #             )
    #             col_idx = summary_df.columns.get_loc(column)
    #             writer.sheets["Summary"].set_column(col_idx, col_idx, column_length)

    #         account_set_df.to_excel(writer, sheet_name="AccountSet", index=False)
    #         for column in account_set_df:
    #             column_length = max(
    #                 account_set_df[column].astype(str).map(len).max(), len(column)
    #             )
    #             col_idx = account_set_df.columns.get_loc(column)
    #             writer.sheets["AccountSet"].set_column(col_idx, col_idx, column_length)

    #         budget_set_df.to_excel(writer, sheet_name="BudgetSet", index=False)
    #         for column in budget_set_df:
    #             column_length = max(
    #                 budget_set_df[column].astype(str).map(len).max(), len(column)
    #             )
    #             col_idx = budget_set_df.columns.get_loc(column)
    #             writer.sheets["BudgetSet"].set_column(col_idx, col_idx, column_length)

    #         memo_rule_set_df.to_excel(writer, sheet_name="MemoRuleSet", index=False)
    #         for column in memo_rule_set_df:
    #             column_length = max(
    #                 memo_rule_set_df[column].astype(str).map(len).max(), len(column)
    #             )
    #             col_idx = memo_rule_set_df.columns.get_loc(column)
    #             writer.sheets["MemoRuleSet"].set_column(col_idx, col_idx, column_length)

    #         choose_one_set_df.to_excel(writer, sheet_name="ChooseOneSet", index=False)
    #         for column in choose_one_set_df:
    #             column_length = max(
    #                 choose_one_set_df[column].astype(str).map(len).max(), len(column)
    #             )
    #             col_idx = choose_one_set_df.columns.get_loc(column)
    #             writer.sheets["ChooseOneSet"].set_column(
    #                 col_idx, col_idx, column_length
    #             )

    #         account_milestones_df.to_excel(
    #             writer, sheet_name="AccountMilestones", index=False
    #         )
    #         for column in account_milestones_df:
    #             column_length = max(
    #                 account_milestones_df[column].astype(str).map(len).max(),
    #                 len(column),
    #             )
    #             col_idx = account_milestones_df.columns.get_loc(column)
    #             writer.sheets["AccountMilestones"].set_column(
    #                 col_idx, col_idx, column_length
    #             )

    #         memo_milestones_df.to_excel(
    #             writer, sheet_name="MemoMilestones", index=False
    #         )
    #         for column in memo_milestones_df:
    #             column_length = max(
    #                 memo_milestones_df[column].astype(str).map(len).max(), len(column)
    #             )
    #             col_idx = memo_milestones_df.columns.get_loc(column)
    #             writer.sheets["MemoMilestones"].set_column(
    #                 col_idx, col_idx, column_length
    #             )

    #         composite_milestones_df.to_excel(
    #             writer, sheet_name="CompositeMilestones", index=False
    #         )
    #         for column in composite_milestones_df:
    #             column_length = max(
    #                 composite_milestones_df[column].astype(str).map(len).max(),
    #                 len(column),
    #             )
    #             col_idx = composite_milestones_df.columns.get_loc(column)
    #             writer.sheets["CompositeMilestones"].set_column(
    #                 col_idx, col_idx, column_length
    #             )

    #         if hasattr(cls, "forecast_df"):
    #             cls.forecast_df.to_excel(writer, sheet_name="Forecast", index=False)
    #             for column in cls.forecast_df:
    #                 column_length = max(
    #                     cls.forecast_df[column].astype(str).map(len).max(), len(column)
    #                 )
    #                 col_idx = cls.forecast_df.columns.get_loc(column)
    #                 writer.sheets["Forecast"].set_column(
    #                     col_idx, col_idx, column_length
    #                 )

    #             cls.skipped_df.to_excel(writer, sheet_name="Skipped", index=False)
    #             for column in cls.skipped_df:
    #                 column_length = max(
    #                     cls.skipped_df[column].astype(str).map(len).max(), len(column)
    #                 )
    #                 col_idx = cls.skipped_df.columns.get_loc(column)
    #                 writer.sheets["Skipped"].set_column(col_idx, col_idx, column_length)

    #             cls.confirmed_df.to_excel(writer, sheet_name="Confirmed", index=False)
    #             for column in cls.confirmed_df:
    #                 column_length = max(
    #                     cls.confirmed_df[column].astype(str).map(len).max(),
    #                     len(column),
    #                 )
    #                 col_idx = cls.confirmed_df.columns.get_loc(column)
    #                 writer.sheets["Confirmed"].set_column(
    #                     col_idx, col_idx, column_length
    #                 )

    #             cls.deferred_df.to_excel(writer, sheet_name="Deferred", index=False)
    #             for column in cls.deferred_df:
    #                 column_length = max(
    #                     cls.deferred_df[column].astype(str).map(len).max(), len(column)
    #                 )
    #                 col_idx = cls.deferred_df.columns.get_loc(column)
    #                 writer.sheets["Deferred"].set_column(
    #                     col_idx, col_idx, column_length
    #                 )

    #             milestone_results_df.to_excel(
    #                 writer, sheet_name="Milestone Results", index=False
    #             )
    #             for column in milestone_results_df:
    #                 column_length = max(
    #                     milestone_results_df[column].astype(str).map(len).max(),
    #                     len(column),
    #                 )
    #                 col_idx = milestone_results_df.columns.get_loc(column)
    #                 writer.sheets["Milestone Results"].set_column(
    #                     col_idx, col_idx, column_length
    #                 )

    # def getSummaryPageForExcelLandingPageDF(cls):

    #     if hasattr(cls, "forecast_df"):
    #         return_df = pd.DataFrame(
    #             {
    #                 "start_date": [cls.start_date],
    #                 "end_date": [cls.end_date],
    #                 "unique_id": [cls.unique_id],
    #                 "start_ts": [cls.start_ts],
    #                 "end_ts": [cls.end_ts],
    #             }
    #         ).T
    #     else:
    #         return_df = pd.DataFrame(
    #             {
    #                 "start_date": [cls.start_date],
    #                 "end_date": [cls.end_date],
    #                 "unique_id": [cls.unique_id],
    #                 "start_ts": [None],
    #                 "end_ts": [None],
    #             }
    #         ).T

    #     return_df.reset_index(inplace=True)
    #     return_df = return_df.rename(columns={"index": "Field", 0: "Value"})
    #     return return_df

    @classmethod
    def evaluateAccountMilestone(
        cls, forecast_df, account_name, min_balance, max_balance, log_stack_depth
    ):
        # log_in_color(
        #     logger,
        #     "yellow",
        #     "debug",
        #     "ENTER evaluateAccountMilestone("
        #     + str(account_name)
        #     + ","
        #     + str(min_balance)
        #     + ","
        #     + str(max_balance)
        #     + ")",
        #     log_stack_depth,
        # )
        log_stack_depth += 1
        account_info = cls.initial_account_set.getAccounts()
        account_base_names = [a.split(":")[0] for a in account_info.Name]
        row_sel_vec = [a == account_name for a in account_base_names]

        relevant_account_info_rows_df = account_info[row_sel_vec]
        # log_in_color(logger, "yellow", "debug", "relevant_account_info_rows_df:")
        # log_in_color(
        #     logger, "yellow", "debug", relevant_account_info_rows_df.to_string()
        # )

        # this df should be either 1 or 2 rows, but have same account type either way
        try:
            assert relevant_account_info_rows_df.Name.unique().shape[0] == 1
        except Exception as e:
            print(e)

        if relevant_account_info_rows_df.shape[0] == 1:  # case for checking and savings
            col_sel_vec = (
                forecast_df.columns
                == relevant_account_info_rows_df.head(1)["Name"].iat[0]
            )
            col_sel_vec[0] = True
            relevant_time_series_df = forecast_df.iloc[:, col_sel_vec]

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
                    # log_in_color(
                    #     logger,
                    #     "yellow",
                    #     "debug",
                    #     "success_date:" + str(success_date),
                    #     log_stack_depth,
                    # )
                elif (min_balance > current_value) | (current_value > max_balance):
                    found_a_valid_success_date = False
                    success_date = "None"
                    # log_in_color(
                    #     logger,
                    #     "yellow",
                    #     "debug",
                    #     "success_date:None",
                    #     log_stack_depth,
                    # )

        elif relevant_account_info_rows_df.shape[0] == 2:  # case for credit and loan
            curr_stmt_bal_acct_name = relevant_account_info_rows_df.iloc[0, 0]
            prev_stmt_bal_acct_name = relevant_account_info_rows_df.iloc[1, 0]

            # log_in_color(logger, 'yellow', 'debug', 'curr_stmt_bal_acct_name:')
            # log_in_color(logger, 'yellow', 'debug', curr_stmt_bal_acct_name)
            # log_in_color(logger, 'yellow', 'debug', 'prev_stmt_bal_acct_name:')
            # log_in_color(logger, 'yellow', 'debug', prev_stmt_bal_acct_name)

            col_sel_vec = forecast_df.columns == curr_stmt_bal_acct_name
            col_sel_vec = col_sel_vec | (
                forecast_df.columns == prev_stmt_bal_acct_name
            )
            col_sel_vec[0] = True  # Date

            # log_in_color(logger, 'yellow', 'debug', 'col_sel_vec:')
            # log_in_color(logger, 'yellow', 'debug', col_sel_vec)

            relevant_time_series_df = forecast_df.iloc[:, col_sel_vec]

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
                    # log_in_color(
                    #     logger,
                    #     "yellow",
                    #     "debug",
                    #     "success_date:" + str(success_date),
                    #     log_stack_depth,
                    # )
                elif (min_balance > current_value) | (current_value > max_balance):
                    found_a_valid_success_date = False
                    success_date = "None"
                    # log_in_color(
                    #     logger,
                    #     "yellow",
                    #     "debug",
                    #     "success_date:None",
                    #     log_stack_depth,
                    # )

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
            col_sel_vec = forecast_df.columns == account_name
            col_sel_vec[0] = True
            relevant_time_series_df = forecast_df.iloc[:, col_sel_vec]

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
                    # log_in_color(
                    #     logger,
                    #     "yellow",
                    #     "debug",
                    #     "success_date:" + str(success_date),
                    #     log_stack_depth,
                    # )
                elif (min_balance > current_value) | (current_value > max_balance):
                    found_a_valid_success_date = False
                    success_date = "None"
                    # log_in_color(
                    #     logger,
                    #     "yellow",
                    #     "debug",
                    #     "success_date:None",
                    #     log_stack_depth,
                    # )
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
        log_stack_depth -= 1
        # log_in_color(
        #     logger,
        #     "yellow",
        #     "debug",
        #     "EXIT evaluateAccountMilestone("
        #     + str(account_name)
        #     + ","
        #     + str(min_balance)
        #     + ","
        #     + str(max_balance)
        #     + ") "
        #     + str(success_date),
        #     log_stack_depth,
        # )
        return success_date

    @classmethod
    def evaulateMemoMilestone(cls, forecast_df, memo_regex, log_stack_depth):
        # log_in_color(
        #     logger,
        #     "yellow",
        #     "debug",
        #     "ENTER evaluateMemoMilestone(" + str(memo_regex) + ")",
        #     log_stack_depth,
        # )
        log_stack_depth += 1
        for forecast_index, forecast_row in forecast_df.iterrows():
            m = re.search(memo_regex, forecast_row.Memo)
            if m is not None:
                log_stack_depth -= 1
                # log_in_color(
                #     logger,
                #     "yellow",
                #     "debug",
                #     "EXIT evaluateMemoMilestone(" + str(memo_regex) + ")",
                #     log_stack_depth,
                # )
                return forecast_row.Date

        log_stack_depth -= 1
        # log_in_color(
        #     logger,
        #     "yellow",
        #     "debug",
        #     "EXIT evaluateMemoMilestone(" + str(memo_regex) + ")",
        #     log_stack_depth,
        # )
        return "None"

    @classmethod
    def evaluateCompositeMilestone(
        cls,
        forecast_df,
        list_of_account_milestones,
        list_of_memo_milestones,
        log_stack_depth,
    ):
        # log_in_color(
        #     logger,
        #     "yellow",
        #     "debug",
        #     "ENTER evaluateCompositeMilestone()",
        #     log_stack_depth,
        # )
        log_stack_depth += 1
        # list_of_account_milestones is lists of 3-tuples that are (string,float,float) for parameters

        # todo composite milestones may contain some milestones that arent listed in the composite #https://github.com/hdickie/expense_forecast/issues/22

        if list_of_account_milestones:
            num_of_acct_milestones = len(list_of_account_milestones)
        else:
            num_of_acct_milestones = 0

        if list_of_memo_milestones:
            num_of_memo_milestones = len(list_of_memo_milestones)
        else:
            num_of_memo_milestones = 0
        account_milestone_dates = []
        memo_milestone_dates = []

        for i in range(0, num_of_acct_milestones):
            account_milestone = list_of_account_milestones[i]
            am_result = cls.evaluateAccountMilestone(
                forecast_df,
                account_milestone.account_name,
                account_milestone.min_balance,
                account_milestone.max_balance, log_stack_depth=log_stack_depth
            )
            if (
                am_result is None
            ):  # disqualified immediately because success requires ALL
                log_stack_depth -= 1
                # log_in_color(
                #     logger,
                #     "yellow",
                #     "debug",
                #     "EXIT evaluateCompositeMilestone() None",
                #     log_stack_depth,
                # )
                return None
            account_milestone_dates.append(am_result)

        for i in range(0, num_of_memo_milestones):
            memo_milestone = list_of_memo_milestones[i]
            mm_result = cls.evaulateMemoMilestone(
                forecast_df, memo_milestone.memo_regex, log_stack_depth=log_stack_depth
            )
            if (
                mm_result is None
            ):  # disqualified immediately because success requires ALL
                log_stack_depth -= 1
                # log_in_color(
                #     logger,
                #     "yellow",
                #     "debug",
                #     "EXIT evaluateCompositeMilestone() None",
                #     log_stack_depth,
                # )
                return None
            memo_milestone_dates.append(mm_result)

        result_date = max(account_milestone_dates + memo_milestone_dates)
        # log_in_color(
        #     logger,
        #     "yellow",
        #     "debug",
        #     "EXIT evaluateCompositeMilestone() " + str(result_date),
        #     log_stack_depth,
        # )
        log_stack_depth -= 1
        return result_date

    @classmethod
    def evaluateMilestones(cls, forecast_df, milestone_set, log_stack_depth):

        account_milestone_results = {}
        if milestone_set.account_milestones:
            for a_m in milestone_set.account_milestones:
                res = cls.evaluateAccountMilestone(
                    forecast_df,
                    a_m.account_name,
                    a_m.min_balance,
                    a_m.max_balance,
                    log_stack_depth=log_stack_depth,
                )
                account_milestone_results[a_m.milestone_name] = res
            account_milestone_results = account_milestone_results

        memo_milestone_results = {}
        if milestone_set.memo_milestones:
            for m_m in milestone_set.memo_milestones:
                res = cls.evaulateMemoMilestone(
                    forecast_df, m_m.memo_regex, log_stack_depth=log_stack_depth
                )
                memo_milestone_results[m_m.milestone_name] = res
            memo_milestone_results = memo_milestone_results

        composite_milestone_results = {}
        if milestone_set.composite_milestones:
            for c_m in milestone_set.composite_milestones:
                res = cls.evaluateCompositeMilestone(
                    forecast_df,
                    c_m.account_milestones,
                    c_m.memo_milestones,
                    log_stack_depth=log_stack_depth,
                )
                composite_milestone_results[c_m.milestone_name] = res
            composite_milestone_results = composite_milestone_results
        return [account_milestone_results, memo_milestone_results, composite_milestone_results] #TODO list is not the best type for this


    @classmethod
    def _appendSummaryLines(cls, initial_A, forecast_df, log_stack_depth):

        account_info = initial_A.getAccounts()

        loan_acct_sel_vec = account_info.Account_Type.isin(
            ["loan", "principal balance", "interest"]
        )
        cc_acct_sel_vec = account_info.Account_Type.isin(
            ["credit", "credit prev stmt bal", "credit curr stmt bal"]
        )
        checking_sel_vec = account_info.Account_Type == "checking"

        loan_acct_info = account_info.loc[loan_acct_sel_vec, :]
        credit_acct_info = account_info.loc[cc_acct_sel_vec, :]
        # savings_acct_info = account_info[account_info.Account_Type.lower() == 'savings', :]

        def summary_numeric_series(column_name):
            return pd.to_numeric(forecast_df.loc[:, column_name], errors="coerce").fillna(0.0)

        NetWorth = summary_numeric_series("Checking")
        for loan_account_index, loan_account_row in loan_acct_info.iterrows():
            # loan_acct_col_sel_vec = (cls.forecast_df.columns == loan_account_row.Name)
            # print('loan_acct_col_sel_vec')
            # print(loan_acct_col_sel_vec)
            NetWorth = NetWorth - summary_numeric_series(loan_account_row.Name)

        for credit_account_index, credit_account_row in credit_acct_info.iterrows():
            NetWorth = NetWorth - summary_numeric_series(credit_account_row.Name)

        # for savings_account_index, savings_account_row in savings_acct_info.iterrows():
        #     NetWorth += cls.forecast_df[:,cls.forecast_df.columns == savings_account_row.Name]

        LoanTotal = summary_numeric_series("Checking") - summary_numeric_series("Checking")
        for loan_account_index, loan_account_row in loan_acct_info.iterrows():
            LoanTotal = LoanTotal + summary_numeric_series(loan_account_row.Name)

        CCDebtTotal = summary_numeric_series("Checking") - summary_numeric_series("Checking")
        for credit_account_index, credit_account_row in credit_acct_info.iterrows():
            CCDebtTotal = CCDebtTotal + summary_numeric_series(credit_account_row.Name)

        forecast_df["Marginal Interest"] = 0.0
        loan_interest_acct_sel_vec = account_info.Account_Type == "interest"
        cc_curr_stmt_acct_sel_vec = account_info.Account_Type == "credit curr stmt bal"
        cc_prev_stmt_acct_sel_vec = account_info.Account_Type == "credit prev stmt bal"

        loan_interest_acct_info = account_info.loc[loan_interest_acct_sel_vec, :]
        cc_curr_stmt_acct_info = account_info.loc[cc_curr_stmt_acct_sel_vec, :]
        cc_prev_stmt_acct_info = account_info.loc[cc_prev_stmt_acct_sel_vec, :]

        previous_row = None
        for index, row in forecast_df.iterrows():
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
                        forecast_df.loc[index, "Marginal Interest"] += abs(
                            line_item_value
                        )

            if "LOAN INTEREST" in row["Memo Directives"]:
                memo_directives_line = row["Memo Directives"]
                memo_directives_line_items = memo_directives_line.split(";")
                for memo_directives_line_item in memo_directives_line_items:
                    memo_directives_line_item = memo_directives_line_item.strip()
                    if "LOAN INTEREST" not in memo_directives_line_item:
                        continue

                    value_match = re.search(
                        r"\(([A-Za-z0-9_ :]*) ([-+]?\$.*)\)$",
                        memo_directives_line_item,
                    )
                    if value_match is None:
                        continue
                    line_item_value_string = value_match.group(2)
                    line_item_value_string = (
                        line_item_value_string.replace("(", "")
                        .replace(")", "")
                        .replace("$", "")
                    )
                    line_item_value = float(line_item_value_string)
                    forecast_df.loc[index, "Marginal Interest"] += abs(
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
                        if value_match is None:
                            continue

                        line_item_account_name = value_match.group(1)

                        if ": Interest" in line_item_account_name:
                            line_item_value_string = value_match.group(2)
                            line_item_value_string = (
                                line_item_value_string.replace("(", "")
                                .replace(")", "")
                                .replace("$", "")
                            )
                            line_item_value = float(line_item_value_string)

                            new_delta = abs(line_item_value)
                            delta = delta + new_delta

                forecast_df.loc[index, "Marginal Interest"] += delta
                # print('')

            previous_row = row

        # just memo
        forecast_df["Net Gain"] = 0.0
        forecast_df["Net Loss"] = forecast_df["Marginal Interest"]
        for index, row in forecast_df.iterrows():

            forecast_df.loc[index, "Net Loss"] = abs(
                forecast_df.loc[index, "Net Loss"]
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

                value_match = re.search(
                    r"\(([A-Za-z0-9_ :]*) ([-+]?\$.*)\)$",
                    memo_line_item,
                )

                if value_match is None:
                    raise ValueError(f"Malformed memo value: {memo_line_item}")

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

                # Moved to memo directive
                line_item_value = float(line_item_value_string)
                if "income" in memo_line_item.lower():
                    # cls.forecast_df.loc[index,'Net Gain'] += abs(line_item_value)
                    pass  # todo income needs to not be in memo. this is a known vulnerability bc of this right here #https://github.com/hdickie/expense_forecast/issues/19
                else:
                    # print(str(cls.forecast_df.loc[index, 'Date'])+' Net Loss before update '+str(cls.forecast_df.loc[index, 'Net Loss']) )
                    forecast_df.loc[index, "Net Loss"] += abs(line_item_value)

                    # print(str(cls.forecast_df.loc[index, 'Date'])+' Net Loss += '+str(abs(line_item_value))+' '+str(memo_line_item)+' = '+str(cls.forecast_df.loc[index,'Net Loss']))

        # just memo directive
        for index, row in forecast_df.iterrows():
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
                    or "LOAN INTEREST" in memo_line_item
                ):
                    continue

                value_match = re.search(
                    r"\(([A-Za-z0-9_ :]*) ([-+]?\$.*)\)$",
                    memo_line_item,
                )

                if value_match is None:
                    raise ValueError(f"Malformed memo value: {memo_line_item}")

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

                line_item_value = float(line_item_value_string)
                if "INCOME" in memo_line_item:
                    forecast_df.loc[index, "Net Gain"] += abs(line_item_value)
                    # print(str(cls.forecast_df.loc[index, 'Date']) + ' Net Gain += ' + str( abs(line_item_value)) + ' ' + str(memo_line_item) + ' = ' + str( cls.forecast_df.loc[index, 'Net Gain']))
                else:
                    forecast_df.loc[index, "Net Loss"] += abs(line_item_value)
                    # print(str(cls.forecast_df.loc[index, 'Date']) + ' Net Loss += ' + str(abs(line_item_value))+' '+str(memo_line_item)+' = '+str(cls.forecast_df.loc[index,'Net Loss']))

            if (
                forecast_df.loc[index, "Net Loss"] > 0
                and forecast_df.loc[index, "Net Gain"] > 0
            ):
                if (
                    forecast_df.loc[index, "Net Gain"]
                    > forecast_df.loc[index, "Net Loss"]
                ):
                    forecast_df.loc[index, "Net Gain"] -= forecast_df.loc[
                        index, "Net Loss"
                    ]
                    forecast_df.loc[index, "Net Loss"] = 0
                else:
                    forecast_df.loc[index, "Net Loss"] -= forecast_df.loc[
                        index, "Net Gain"
                    ]
                    forecast_df.loc[index, "Net Gain"] = 0

        # Final QC. If we trust the code, we can comment this out
        # checking, credit, loan,
        # loan_acct_sel_vec = loan_acct_sel_vec.append(pd.Series([False])) #this works

        loan_account_names = set(account_info.loc[loan_acct_sel_vec, "Name"])
        credit_account_names = set(account_info.loc[cc_acct_sel_vec, "Name"])
        checking_account_names = set(account_info.loc[checking_sel_vec, "Name"])

        check_row_delta = 0
        cc_row_delta = 0
        loan_row_delta = 0

        # log_in_color(
        #     logger, "magenta", "debug", "Forecast Pre-Validation", log_stack_depth
        # )
        # log_in_color(
        #     logger,
        #     "magenta",
        #     "debug",
        #     forecast_df.to_string(),
        #     log_stack_depth,
        # )
        # log_in_color(
        #     logger, "magenta", "debug", "Validation Delta Values", log_stack_depth
        # )
        # log_data_header_string = (
        #     "Date".rjust(10)
        #     + " "
        #     + "Check".rjust(10)
        #     + " "
        #     + "CC".rjust(10)
        #     + " "
        #     + "Loan".rjust(10)
        #     + " "
        #     + "Net +".rjust(10)
        #     + " "
        #     + "Net -".rjust(10)
        # )
        # log_in_color(
        #     logger, "magenta", "debug", log_data_header_string, log_stack_depth
        # )

        fail_flag = False
        for f_i, row in forecast_df.iterrows():
            loan_row_sel_vec = row.index.isin(loan_account_names)
            cc_row_sel_vec = row.index.isin(credit_account_names)
            checking_row_sel_vec = row.index.isin(checking_account_names)

            if sum(loan_row_sel_vec) > 0:
                loan_row_total = pd.to_numeric(row[loan_row_sel_vec]).sum()
                # print('loan_row_total:')
                # print(loan_row_total)
            else:
                loan_row_total = 0

            if sum(cc_row_sel_vec) > 0:
                cc_row_total = pd.to_numeric(row[cc_row_sel_vec]).sum()
                # print('cc_row_total:')
                # print(cc_row_total)
            else:
                cc_row_total = 0

            check_row_total = pd.to_numeric(row[checking_row_sel_vec]).sum()
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
                row["Date"].strftime('%Y-%m-%d').rjust(10)
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
            # log_in_color(logger, "magenta", "debug", log_string, log_stack_depth)
            # if round(check_row_delta - (cc_row_delta + loan_row_delta),2) < 0:
            if check_row_delta - (cc_row_delta + loan_row_delta) < 0:
                try:
                    # assert -1*round(net_loss,2) == round((check_row_delta - (cc_row_delta + loan_row_delta)),2)
                    assert -1 * net_loss == (
                        check_row_delta - (cc_row_delta + loan_row_delta)
                    )
                except Exception as e:
                    # log_in_color(logger, 'red', 'debug', 'Validation FAIL -1*round(net_loss,2) == round((check_row_delta - (cc_row_delta + loan_row_delta)),2) was not TRUE', log_stack_depth)
                    log_in_color(
                        logger,
                        "red",
                        "debug",
                        "Validation FAIL -1*net_loss == (check_row_delta - (cc_row_delta + loan_row_delta)) was not TRUE",
                        log_stack_depth,
                    )
                    log_in_color(
                        logger,
                        "magenta",
                        "debug",
                        "Memo...........: " + str(memo),
                        log_stack_depth,
                    )
                    log_in_color(
                        logger,
                        "magenta",
                        "debug",
                        "Md.............: " + str(md),
                        log_stack_depth,
                    )
                    # log_in_color(logger, 'magenta', 'debug', str(-1*net_loss)+' != '+str( round((check_row_delta - (cc_row_delta + loan_row_delta)),2) ) , log_stack_depth)
                    log_in_color(
                        logger,
                        "magenta",
                        "debug",
                        str(-1 * net_loss)
                        + " != "
                        + str((check_row_delta - (cc_row_delta + loan_row_delta))),
                        log_stack_depth,
                    )
                    log_in_color(logger, "magenta", "debug", "", log_stack_depth)

                    fail_flag = True

            # if round(check_row_delta - (cc_row_delta + loan_row_delta),2) > 0:
            if check_row_delta - (cc_row_delta + loan_row_delta) > 0:
                try:
                    # assert round(net_gain,2) == round((check_row_delta - (cc_row_delta + loan_row_delta)),2)
                    assert net_gain == (
                        check_row_delta - (cc_row_delta + loan_row_delta)
                    )
                except Exception as e:
                    # log_in_color(logger, 'red', 'debug', 'Validation FAIL round(net_gain,2) == round((check_row_delta - (cc_row_delta + loan_row_delta)),2) was not TRUE', log_stack_depth)
                    log_in_color(
                        logger,
                        "red",
                        "debug",
                        "Validation FAIL net_gain == (check_row_delta - (cc_row_delta + loan_row_delta)) was not TRUE",
                        log_stack_depth,
                    )
                    log_in_color(
                        logger,
                        "magenta",
                        "debug",
                        "Memo...........: " + str(memo),
                        log_stack_depth,
                    )
                    log_in_color(
                        logger,
                        "magenta",
                        "debug",
                        "Md.............: " + str(md),
                        log_stack_depth,
                    )
                    # log_in_color(logger, 'magenta', 'debug', str(net_gain)+' != '+str( round((check_row_delta - (cc_row_delta + loan_row_delta)),2) ) , log_stack_depth)
                    log_in_color(
                        logger,
                        "magenta",
                        "debug",
                        str(net_gain)
                        + " != "
                        + str((check_row_delta - (cc_row_delta + loan_row_delta))),
                        log_stack_depth,
                    )

                    fail_flag = True

        if fail_flag:
            log_in_color(
                logger, "red", "debug", "Validation FAIL", log_stack_depth
            )
        else:
            log_in_color(
                logger, "green", "debug", "Validation SUCCESS", log_stack_depth
            )

        LiquidTotal = forecast_df.Checking

        forecast_df["Net Worth"] = NetWorth
        forecast_df["Loan Total"] = LoanTotal
        forecast_df["CC Debt Total"] = CCDebtTotal
        forecast_df["Liquid Total"] = LiquidTotal

        memo_column = copy.deepcopy(forecast_df["Memo"])
        memo_directives_column = copy.deepcopy(forecast_df["Memo Directives"])
        next_income_date_column = copy.deepcopy(forecast_df["Next Income Date"])
        forecast_df = forecast_df.drop(
            columns=["Memo", "Memo Directives", "Next Income Date"]
        )
        forecast_df["Next Income Date"] = next_income_date_column
        forecast_df["Memo Directives"] = memo_directives_column
        forecast_df["Memo"] = memo_column

        return forecast_df

    @staticmethod
    def _report_date_to_datetime(value):
        if pd.isnull(value):
            return value
        if isinstance(value, pd.Timestamp):
            return value.to_pydatetime()
        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, date):
            return datetime.datetime.combine(value, datetime.time.min)

        value_string = str(value)
        for date_format in ("%Y%m%d", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.datetime.strptime(value_string, date_format)
            except ValueError:
                pass
        return pd.to_datetime(value).to_pydatetime()

    @staticmethod
    def _report_amount(value):
        return str(f"${float(value):,}")

    def _report_date_label(self, value):
        return self._report_date_to_datetime(value).strftime("%Y-%m-%d")

    def _report_initial_conditions(self, expense_forecast):
        return getattr(expense_forecast, "initial_conditions", expense_forecast)

    def _report_start_date(self, expense_forecast):
        initial_conditions = self._report_initial_conditions(expense_forecast)
        return getattr(
            expense_forecast,
            "start_date_YYYYMMDD",
            getattr(initial_conditions, "start_date", None),
        )

    def _report_end_date(self, expense_forecast):
        initial_conditions = self._report_initial_conditions(expense_forecast)
        return getattr(
            expense_forecast,
            "end_date_YYYYMMDD",
            getattr(initial_conditions, "end_date", None),
        )

    def _report_forecast_name(self, expense_forecast):
        initial_conditions = self._report_initial_conditions(expense_forecast)
        return (
            getattr(expense_forecast, "forecast_name", None)
            or getattr(initial_conditions, "forecast_name", None)
            or f"Forecast {expense_forecast.unique_id}"
        )

    def _report_account_set(self, expense_forecast):
        initial_conditions = self._report_initial_conditions(expense_forecast)
        return getattr(
            expense_forecast,
            "initial_account_set",
            getattr(initial_conditions, "initial_account_set", None),
        )

    def _report_budget_set(self, expense_forecast):
        initial_conditions = self._report_initial_conditions(expense_forecast)
        return getattr(
            expense_forecast,
            "initial_budget_set",
            getattr(initial_conditions, "initial_budget_set", None),
        )

    def _report_memo_rule_set(self, expense_forecast):
        initial_conditions = self._report_initial_conditions(expense_forecast)
        return getattr(
            expense_forecast,
            "initial_memo_rule_set",
            getattr(initial_conditions, "initial_memo_rule_set", None),
        )

    def _report_milestone_set(self, expense_forecast):
        initial_conditions = self._report_initial_conditions(expense_forecast)
        return getattr(
            expense_forecast,
            "milestone_set",
            getattr(initial_conditions, "milestone_set", None),
        )

    @staticmethod
    def _empty_report_df():
        return pd.DataFrame()

    def _report_milestone_table(self, milestone_set, method_name):
        if milestone_set is None or not hasattr(milestone_set, method_name):
            return self._empty_report_df()
        return getattr(milestone_set, method_name)()

    def _report_milestone_results_df(self, expense_forecast, result_type):
        method_name = f"get{result_type}MilestoneResultsDF"
        if hasattr(expense_forecast, method_name):
            return getattr(expense_forecast, method_name)()

        milestone_results = getattr(expense_forecast, "milestone_results", None)
        if isinstance(milestone_results, dict):
            result_data = milestone_results.get(result_type, {})
        elif isinstance(milestone_results, (list, tuple)):
            result_index_by_type = {"Account": 0, "Memo": 1, "Composite": 2}
            result_index = result_index_by_type.get(result_type)
            if result_index is not None and len(milestone_results) > result_index:
                result_data = milestone_results[result_index]
            else:
                result_data = {}
        else:
            result_data = getattr(expense_forecast, f"{result_type.lower()}_milestone_results", {})

        if not result_data:
            return pd.DataFrame(columns=["Milestone", "Date"])

        rows = []
        end_date = self._report_end_date(expense_forecast)
        for milestone_name, milestone_date in result_data.items():
            if milestone_date in (None, "None"):
                milestone_date = end_date
            rows.append(
                {
                    "Milestone": milestone_name,
                    "Date": self._report_date_to_datetime(milestone_date),
                }
            )
        return pd.DataFrame(rows)

    def _report_confirmed_df(self, expense_forecast):
        confirmed_df = getattr(expense_forecast, "confirmed_df", None)
        if confirmed_df is not None:
            return confirmed_df

        initial_conditions = self._report_initial_conditions(expense_forecast)
        confirmed_df = getattr(initial_conditions, "initial_confirmed_df", None)
        if confirmed_df is not None:
            return confirmed_df

        return pd.DataFrame(columns=["Date", "Priority", "Amount", "Memo"])

    def _report_dates_for_plot(self, expense_forecast):
        return [
            self._report_date_to_datetime(d)
            for d in expense_forecast.forecast_df["Date"]
        ]

    def _decorate_report_plot(self, expense_forecast):
        bottom, top = plt.ylim()
        if top == bottom:
            top = top + 1
            bottom = bottom - 1
        if 0 < bottom:
            plt.ylim(0, top)
        elif top < 0:
            plt.ylim(bottom, 0)

        ax = plt.subplot(111)
        box = ax.get_position()
        ax.set_position(
            [box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9]
        )
        ax.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, -0.05),
            fancybox=True,
            shadow=True,
            ncol=4,
        )

        date_as_datetime_type = self._report_dates_for_plot(expense_forecast)
        min_date = min(date_as_datetime_type).strftime("%Y-%m-%d")
        max_date = max(date_as_datetime_type).strftime("%Y-%m-%d")
        plt.title(
            "Forecast #"
            + str(expense_forecast.unique_id)
            + ": "
            + str(min_date)
            + " -> "
            + str(max_date)
        )
        plt.xticks(rotation=90)

    def plotMilestoneDates(
        self, expense_forecast, output_path, plot_colors=["red", "blue", "purple"]
    ):
        assert hasattr(expense_forecast, "forecast_df")
        assert len(plot_colors) >= 3

        milestone_groups = [
            ("account", self._report_milestone_results_df(expense_forecast, "Account")),
            ("memo", self._report_milestone_results_df(expense_forecast, "Memo")),
            ("composite", self._report_milestone_results_df(expense_forecast, "Composite")),
        ]

        data_x = []
        data_y = []
        labels = []
        colors = []
        date_counter = 0
        for group_index, (group_name, milestone_df) in enumerate(milestone_groups):
            if milestone_df is None or milestone_df.empty or "Date" not in milestone_df.columns:
                continue
            name_column = "Milestone" if "Milestone" in milestone_df.columns else milestone_df.columns[0]
            for _, row in milestone_df.iterrows():
                milestone_date = row["Date"]
                if milestone_date in (None, "None"):
                    continue
                data_x.append(self._report_date_to_datetime(milestone_date))
                data_y.append(date_counter)
                labels.append(str(row[name_column]))
                colors.append(plot_colors[group_index])
                date_counter += 1

        figure(figsize=(10, 6), dpi=80)
        fig, ax = plt.subplots()
        fig.subplots_adjust(left=0.25)
        if len(data_x) > 0:
            ax.barh(data_y, data_x, color=colors)
            ax.set_yticks(data_y)
            ax.set_yticklabels(labels, minor=False)
            plt.xlim(
                self._report_date_to_datetime(self._report_start_date(expense_forecast)),
                self._report_date_to_datetime(self._report_end_date(expense_forecast)),
            )
            plt.ylim(-0.5, len(data_y) - 0.5)
            red_patch = mpatches.Patch(color="red", label="account")
            blue_patch = mpatches.Patch(color="blue", label="memo")
            purple_patch = mpatches.Patch(color="purple", label="composite")
            plt.legend(
                handles=[red_patch, blue_patch, purple_patch],
                bbox_to_anchor=(1.15, 1),
                loc="upper right",
            )
            plt.xticks(rotation=90)
            date_as_datetime_type = self._report_dates_for_plot(expense_forecast)
            min_date = min(date_as_datetime_type).strftime("%Y-%m-%d")
            max_date = max(date_as_datetime_type).strftime("%Y-%m-%d")
            plt.title(
                "Forecast #"
                + str(expense_forecast.unique_id)
                + ": "
                + str(min_date)
                + " -> "
                + str(max_date)
            )
        else:
            plt.axis("off")
            plt.text(
                0.5,
                0.5,
                s="There are no milestones to show.",
                horizontalalignment="center",
            )

        plt.savefig(output_path)
        matplotlib.pyplot.close()

    def plotAccountTypeTotals(
        self,
        expense_forecast,
        output_path,
        line_color_cycle_list=["blue", "orange", "green"],
        linestyle="solid",
    ):
        assert hasattr(expense_forecast, "forecast_df")

        figure(figsize=(10, 6), dpi=80)
        plt.gca().set_prop_cycle(plt.cycler(color=line_color_cycle_list))

        relevant_columns = [
            column
            for column in ["Loan Total", "CC Debt Total", "Liquid Total"]
            if column in expense_forecast.forecast_df.columns
        ]
        x_values = self._report_dates_for_plot(expense_forecast)
        for column in relevant_columns:
            plt.plot(
                x_values,
                expense_forecast.forecast_df[column],
                label=column + " " + str(expense_forecast.unique_id),
                linestyle=linestyle,
            )

        self._decorate_report_plot(expense_forecast)
        plt.savefig(output_path)
        matplotlib.pyplot.close()

    def plotNetGainLoss(
        self,
        expense_forecast,
        output_path,
        line_color_cycle_list=["green", "red"],
        linestyle="solid",
    ):
        assert hasattr(expense_forecast, "forecast_df")

        figure(figsize=(10, 6), dpi=80)
        plt.gca().set_prop_cycle(plt.cycler(color=line_color_cycle_list))
        x_values = self._report_dates_for_plot(expense_forecast)
        for column in ["Net Gain", "Net Loss"]:
            if column not in expense_forecast.forecast_df.columns:
                continue
            plt.plot(
                x_values,
                expense_forecast.forecast_df[column],
                label=column + " " + str(expense_forecast.unique_id),
                linestyle=linestyle,
            )

        self._decorate_report_plot(expense_forecast)
        plt.savefig(output_path)
        matplotlib.pyplot.close()

    def plotNetWorth(
        self,
        expense_forecast,
        output_path,
        line_color_cycle_list=["blue"],
        linestyle="solid",
    ):
        assert hasattr(expense_forecast, "forecast_df")

        figure(figsize=(10, 6), dpi=80)
        plt.gca().set_prop_cycle(plt.cycler(color=line_color_cycle_list))
        x_values = self._report_dates_for_plot(expense_forecast)
        plt.plot(
            x_values,
            expense_forecast.forecast_df["Net Worth"],
            label="Net Worth " + str(expense_forecast.unique_id),
            linestyle=linestyle,
        )
        plt.axhline(y=0, color="black", linestyle=":", linewidth=1)

        bottom, top = plt.ylim()
        plt.ylim(bottom, top * 1.1 if top else 1)
        self._decorate_report_plot(expense_forecast)
        plt.savefig(output_path)
        matplotlib.pyplot.close()

    def plotAll(
        self,
        expense_forecast,
        output_path,
    ):
        assert hasattr(expense_forecast, "forecast_df")

        figure(figsize=(10, 6), dpi=80)

        account_set = self._report_account_set(expense_forecast)
        if account_set is not None:
            account_info = account_set.getAccounts()
            account_names = [
                account_name
                for account_name in account_info.Name
                if account_name in expense_forecast.forecast_df.columns
            ]
        else:
            summary_columns = {
                "Date",
                "Net Worth",
                "Loan Total",
                "CC Debt Total",
                "Liquid Total",
                "Net Gain",
                "Net Loss",
                "Marginal Interest",
                "Memo",
                "Memo Directives",
                "Next Income Date",
            }
            account_names = [
                column
                for column in expense_forecast.forecast_df.columns
                if column not in summary_columns and ":" not in column
            ]

        x_values = self._report_dates_for_plot(expense_forecast)
        for account_name in account_names:
            if not pd.api.types.is_numeric_dtype(expense_forecast.forecast_df[account_name]):
                continue
            plt.plot(
                x_values,
                expense_forecast.forecast_df[account_name],
                label=account_name,
            )

        self._decorate_report_plot(expense_forecast)
        plt.savefig(output_path)
        matplotlib.pyplot.close()

    def plotMarginalInterest(self, expense_forecast, output_path, linestyle="solid"):
        assert hasattr(expense_forecast, "forecast_df")

        figure(figsize=(10, 6), dpi=80)
        plt.gca().set_prop_cycle(plt.cycler(color=["blue"]))
        x_values = self._report_dates_for_plot(expense_forecast)
        plt.plot(
            x_values,
            expense_forecast.forecast_df["Marginal Interest"],
            label="Marginal Interest " + str(expense_forecast.unique_id),
            linestyle=linestyle,
        )

        self._decorate_report_plot(expense_forecast)
        plt.savefig(output_path)
        matplotlib.pyplot.close()

    def plotSankeyDiagram(self, expense_forecast, output_path):
        if go is None:
            raise ImportError("plotly is required to generate the Sankey diagram")

        budget_set = self._report_budget_set(expense_forecast)
        memo_rule_set = self._report_memo_rule_set(expense_forecast)
        if budget_set is None or memo_rule_set is None:
            raise ValueError("BudgetSet and MemoRuleSet are required for Sankey report")

        income_memos = []
        expense_memos = []
        for _, row in budget_set.getBudgetItems().iterrows():
            matching_memo_rule_set = memo_rule_set.findMatchingMemoRule(
                row.Memo, row.Priority
            )
            if len(matching_memo_rule_set.memo_rules) == 0:
                continue
            relevant_memo_rule = matching_memo_rule_set.memo_rules[0]
            if (
                relevant_memo_rule.account_from in ("Checking", "Credit")
                and relevant_memo_rule.account_to in (None, "None")
            ):
                expense_memos.append(row.Memo)
            elif (
                relevant_memo_rule.account_from in (None, "None")
                and relevant_memo_rule.account_to == "Checking"
            ):
                income_memos.append(row.Memo)

        total_income = 0
        total_expense = 0
        total_interest = 0
        income_node_dict = {}
        expense_node_dict = {}
        for _, row in expense_forecast.forecast_df.iterrows():
            memo_line_items = str(row.Memo).split(";")
            for memo_line_item in memo_line_items:
                memo_line_item = memo_line_item.strip()
                if memo_line_item == "":
                    continue
                payment_amount_match = re.search("\\(.*-?\\$(.*)\\)", memo_line_item)
                if payment_amount_match is None:
                    continue
                amount = float(payment_amount_match.group(1))
                for income_memo in income_memos:
                    if income_memo in memo_line_item:
                        total_income += amount
                        income_node_dict[income_memo] = (
                            income_node_dict.get(income_memo, 0) + amount
                        )

                for expense_memo in expense_memos:
                    if expense_memo in memo_line_item:
                        total_expense += amount
                        expense_node_dict[expense_memo] = (
                            expense_node_dict.get(expense_memo, 0) + amount
                        )

                if "cc interest" in memo_line_item.lower():
                    total_interest += amount

        total_expense += total_interest
        total_remaining = total_income - total_expense

        labels = []
        source = []
        target = []
        values = []
        colors = []
        income_color = "#42f542"
        expense_color = "#ecf542"

        index = 0
        for key, value in income_node_dict.items():
            labels.append(key)
            source.append(index)
            values.append(value)
            colors.append(income_color)
            index += 1

        total_income_index = index
        labels.append("Total Income")
        index += 1

        total_expense_index = index
        labels.append("Total Expense")
        index += 1

        for income_index in range(len(income_node_dict)):
            target.append(total_income_index)

        source.append(total_income_index)
        target.append(total_expense_index)
        values.append(total_expense)
        colors.append(expense_color)

        remaining_index = index + len(expense_node_dict) + 1
        source.append(total_income_index)
        target.append(remaining_index)
        values.append(max(total_remaining, 0))
        colors.append(income_color)

        for key, value in expense_node_dict.items():
            labels.append(key)
            source.append(total_expense_index)
            target.append(index)
            values.append(value)
            colors.append(expense_color)
            index += 1

        interest_index = index
        labels.append("Total Interest")
        source.append(total_expense_index)
        target.append(interest_index)
        values.append(total_interest)
        colors.append(expense_color)
        index += 1

        labels.append("Remaining")

        fig = go.Figure(
            data=[
                go.Sankey(
                    node=dict(
                        pad=15,
                        thickness=20,
                        line=dict(color="black", width=0.5),
                        label=labels,
                        color="grey",
                    ),
                    link=dict(
                        source=source,
                        target=target,
                        value=values,
                        color=colors,
                    ),
                )
            ],
            layout=go.Layout(height=480, width=800),
        )

        fig.update_layout(title_text=self._report_forecast_name(expense_forecast), font_size=10)
        fig.write_image(output_path)

    def generateHTMLReport(self, E, output_dir="./", parent_report_path=None):
        start_date = self._report_date_label(self._report_start_date(E))
        end_date = self._report_date_label(self._report_end_date(E))

        forecast_failed = (
            self._report_date_to_datetime(E.forecast_df.tail(1).Date.iat[0]).date()
            != self._report_date_to_datetime(self._report_end_date(E)).date()
        )

        report_id = E.unique_id
        output_file_name = "Forecast_" + str(report_id)

        start_ts = getattr(E, "start_ts", None)
        end_ts = getattr(E, "end_ts", None)
        if start_ts is None:
            start_ts__datetime = datetime.datetime.now()
        else:
            start_ts__datetime = self._report_date_to_datetime(start_ts)
        if end_ts is None:
            end_ts__datetime = start_ts__datetime
        else:
            end_ts__datetime = self._report_date_to_datetime(end_ts)
        simulation_time_elapsed = end_ts__datetime - start_ts__datetime

        if parent_report_path is not None:
            parent_report_text = (
                """This report was generated alongside some others. See <a href=\""""
                + parent_report_path
                + """\">this page</a> for information about related forecasts."""
            )
        else:
            parent_report_text = ""

        summary_text = (
            """
        This forecast started at """
            + str(start_ts__datetime)
            + """, took """
            + str(simulation_time_elapsed)
            + """ to complete, and finished at """
            + str(end_ts__datetime)
            + """.
        """
        )

        account_set = self._report_account_set(E)
        budget_set = self._report_budget_set(E)
        memo_rule_set = self._report_memo_rule_set(E)
        milestone_set = self._report_milestone_set(E)

        account_text = (
            """
        The initial conditions and account boundaries are defined as:"""
            + (account_set.getAccounts().to_html() if account_set is not None else "")
            + """
        """
        )

        budget_set_text = (
            """
        These transactions are considered for analysis:"""
            + (budget_set.getBudgetItems().to_html() if budget_set is not None else "")
            + """
        """
        )

        memo_rule_text = (
            """
        These decision rules are used:"""
            + (memo_rule_set.getMemoRules().to_html() if memo_rule_set is not None else "")
            + """
        """
        )

        account_milestone_text = (
            """
        These account milestones are defined:"""
            + self._report_milestone_table(milestone_set, "getAccountMilestonesDF").to_html()
            + """
        """
        )

        memo_milestone_text = (
            """
        These memo milestones are defined:"""
            + self._report_milestone_table(milestone_set, "getMemoMilestonesDF").to_html()
            + """
        """
        )

        composite_milestone_text = (
            """
        These composite milestones are defined:"""
            + self._report_milestone_table(milestone_set, "getCompositeMilestonesDF").to_html()
            + """
        """
        )

        initial_networth = round(E.forecast_df.head(1)["Net Worth"].iat[0], 2)
        final_networth = round(E.forecast_df.tail(1)["Net Worth"].iat[0], 2)
        networth_delta = round(final_networth - initial_networth, 2)
        num_days = E.forecast_df.shape[0]
        avg_networth_change = round(networth_delta / float(num_days), 2)
        rose_or_fell = "rose" if networth_delta >= 0 else "fell"

        networth_text = (
            """
        Net Worth began at """
            + self._report_amount(initial_networth)
            + """ and """
            + rose_or_fell
            + """ to """
            + self._report_amount(final_networth)
            + """ over """
            + str(f"{float(num_days):,.0f}")
            + """ days, averaging """
            + self._report_amount(avg_networth_change)
            + """ per day.
        """
        )

        initial_loan_total = round(E.forecast_df.head(1)["Loan Total"].iat[0], 2)
        final_loan_total = round(E.forecast_df.tail(1)["Loan Total"].iat[0], 2)
        loan_delta = round(final_loan_total - initial_loan_total, 2)
        initial_cc_debt_total = round(E.forecast_df.head(1)["CC Debt Total"].iat[0], 2)
        final_cc_debt_total = round(E.forecast_df.tail(1)["CC Debt Total"].iat[0], 2)
        cc_debt_delta = round(final_cc_debt_total - initial_cc_debt_total, 2)
        initial_liquid_total = round(E.forecast_df.head(1)["Liquid Total"].iat[0], 2)
        final_liquid_total = round(E.forecast_df.tail(1)["Liquid Total"].iat[0], 2)
        liquid_delta = round(final_liquid_total - initial_liquid_total, 2)

        avg_loan_delta = round(loan_delta / num_days, 2)
        avg_cc_debt_delta = round(cc_debt_delta / num_days, 2)
        avg_liquid_delta = round(liquid_delta / num_days, 2)

        account_type_text = (
            """
        Loan debt began at """
            + self._report_amount(initial_loan_total)
            + """ and """
            + ("rose" if avg_loan_delta >= 0 else "fell")
            + """ to """
            + self._report_amount(final_loan_total)
            + """ over """
            + str(f"{float(num_days):,.0f}")
            + """ days, averaging """
            + self._report_amount(avg_loan_delta)
            + """ per day.
        <br><br>
        Credit card debt began at """
            + self._report_amount(initial_cc_debt_total)
            + """ and """
            + ("rose" if avg_cc_debt_delta >= 0 else "fell")
            + """ to """
            + self._report_amount(final_cc_debt_total)
            + """ over """
            + str(f"{float(num_days):,.0f}")
            + """ days, averaging """
            + self._report_amount(avg_cc_debt_delta)
            + """ per day.
        <br><br>
        Liquid cash began at """
            + self._report_amount(initial_liquid_total)
            + """ and """
            + ("rose" if avg_liquid_delta >= 0 else "fell")
            + """ to """
            + self._report_amount(final_liquid_total)
            + """ over """
            + str(f"{float(num_days):,.0f}")
            + """ days, averaging """
            + self._report_amount(avg_liquid_delta)
            + """ per day.
        """
        )

        total_gain = round(sum(E.forecast_df["Net Gain"]), 2)
        avg_daily_gain = round(total_gain / num_days, 2)
        total_loss = round(sum(E.forecast_df["Net Loss"]), 2)
        avg_daily_loss = round(total_loss / num_days, 2)

        net_gain_loss_text = (
            "Total gain was "
            + self._report_amount(total_gain)
            + " over "
            + str(num_days)
            + " days, averaging "
            + self._report_amount(avg_daily_gain)
            + " per day.<br><br>"
        )
        net_gain_loss_text += (
            "Total loss was "
            + str(f"-${float(total_loss):,}")
            + " over "
            + str(num_days)
            + " days, averaging "
            + str(f"-${float(avg_daily_loss):,}")
            + " per day."
        )

        total_interest_accrued = round(sum(E.forecast_df["Marginal Interest"]), 2)
        avg_interest_accrued = round(total_interest_accrued / num_days, 2)

        interest_text = (
            "Total interest accrued was "
            + self._report_amount(total_interest_accrued)
            + " over "
            + str(num_days)
            + " days, averaging "
            + self._report_amount(avg_interest_accrued)
            + " per day.<br>"
        )
        interest_text += "This plot shows the new interest by day, not the total interest at a given time."

        cc_interest_sel_vec = [
            "cc interest" in str(m).lower() for m in E.forecast_df.Memo
        ]
        interest_rows_df = E.forecast_df.loc[cc_interest_sel_vec]
        interest_table_to_display_df = pd.DataFrame(interest_rows_df["Date"])
        interest_table_to_display_df["Total CC Interest"] = 0.0
        for index, row in interest_rows_df.iterrows():
            memo_line = str(row.Memo)
            memo_line_items = memo_line.split(";")
            for memo_line_item in memo_line_items:
                memo_line_item = memo_line_item.strip()
                if "cc interest" not in memo_line_item.lower():
                    continue

                value_match = re.search(
                    "\\(([A-Za-z0-9_ :]*) ([-+]?\\$.*)\\)$", memo_line_item
                )
                if value_match is None:
                    continue
                line_item_value_string = value_match.group(2)
                line_item_value_string = (
                    line_item_value_string.replace("(", "")
                    .replace(")", "")
                    .replace("$", "")
                )
                line_item_value = float(line_item_value_string)
                interest_table_to_display_df.loc[
                    index, "Total CC Interest"
                ] += line_item_value
        interest_table_html = interest_table_to_display_df.to_html()

        am_result_df = self._report_milestone_results_df(E, "Account")
        mm_result_df = self._report_milestone_results_df(E, "Memo")
        cm_result_df = self._report_milestone_results_df(E, "Composite")

        end_date_datetime = self._report_date_to_datetime(self._report_end_date(E))
        achieved_am_count = (
            am_result_df[am_result_df.Date < end_date_datetime].shape[0]
            if "Date" in am_result_df.columns
            else 0
        )
        achieved_mm_count = (
            mm_result_df[mm_result_df.Date < end_date_datetime].shape[0]
            if "Date" in mm_result_df.columns
            else 0
        )
        achieved_cm_count = (
            cm_result_df[cm_result_df.Date < end_date_datetime].shape[0]
            if "Date" in cm_result_df.columns
            else 0
        )
        total_milestone_count = (
            am_result_df.shape[0] + mm_result_df.shape[0] + cm_result_df.shape[0]
        )
        achieved_milestone_count = (
            achieved_am_count + achieved_mm_count + achieved_cm_count
        )

        milestone_text = (
            str(total_milestone_count)
            + " milestones were defined, and "
            + str(achieved_milestone_count)
            + " were achieved before the end of the forecast.<br>"
        )
        milestone_text += "Note that unachieved milestones are displayed on the last day of the forecast."

        transaction_schedule_text = "Transactions are displayed below."
        confirmed_df = self._report_confirmed_df(E)
        if "Priority" in confirmed_df.columns:
            p2_plus_txns_html_table = confirmed_df[confirmed_df.Priority >= 2].to_html()
        else:
            p2_plus_txns_html_table = confirmed_df.to_html()

        payment_rows = []
        account_type_by_name = {}
        if account_set is not None:
            account_type_by_name = dict(
                zip(account_set.getAccounts()["Name"], account_set.getAccounts()["Account_Type"])
            )
        if (
            memo_rule_set is not None
            and "Priority" in confirmed_df.columns
            and "Memo" in confirmed_df.columns
        ):
            for _, confirmed_row in confirmed_df[confirmed_df.Priority >= 2].iterrows():
                memo_rule = memo_rule_set.findMatchingMemoRule(
                    confirmed_row.Memo, confirmed_row.Priority
                )
                account_to_type = account_type_by_name.get(memo_rule.account_to)
                if account_to_type == "credit":
                    payment_rows.append(
                        {
                            "Payment Type": "Credit Card",
                            "Date": confirmed_row.Date,
                            "Memo": confirmed_row.Memo,
                            "Amount": confirmed_row.Amount,
                        }
                    )
                elif account_to_type == "loan" or memo_rule.account_to == "ALL_LOANS":
                    payment_rows.append(
                        {
                            "Payment Type": "Loan",
                            "Date": confirmed_row.Date,
                            "Memo": confirmed_row.Memo,
                            "Amount": confirmed_row.Amount,
                        }
                    )

        for _, row in E.forecast_df.iterrows():
            memo_line_items = str(row.Memo).split(";") + str(row["Memo Directives"]).split(";")
            for memo_line_item in memo_line_items:
                memo_line_item_lower = memo_line_item.lower()
                if (
                    "loan min payment" in memo_line_item_lower
                    or "additional loan payment" in memo_line_item_lower
                    or "addtl loan payment" in memo_line_item_lower
                ):
                    payment_rows.append(
                        {"Payment Type": "Loan", "Date": row.Date, "Memo": memo_line_item}
                    )
                elif (
                    "cc min payment" in memo_line_item_lower
                    or "additional cc payment" in memo_line_item_lower
                    or "addtl cc payment" in memo_line_item_lower
                    or "cc interest" in memo_line_item_lower
                ):
                    payment_rows.append(
                        {"Payment Type": "Credit Card", "Date": row.Date, "Memo": memo_line_item}
                    )

        payments_df = pd.DataFrame(payment_rows)
        cc_payments_html_table = payments_df[
            payments_df.get("Payment Type", pd.Series(dtype=str)) == "Credit Card"
        ].to_html()
        loan_payment_html_table = payments_df[
            payments_df.get("Payment Type", pd.Series(dtype=str)) == "Loan"
        ].to_html()

        all_plot_page_text = ""
        sankey_text = ""

        output_target = Path(output_dir)
        if output_target.suffix:
            html_output_path = output_target
            image_output_dir = output_target.parent
        else:
            image_output_dir = output_target
            html_output_path = image_output_dir / (output_file_name + ".html")

        image_output_dir.mkdir(parents=True, exist_ok=True)
        networth_line_plot_path = report_id + "_networth_line_plot.png"
        net_gain_loss_line_plot_path = report_id + "_net_gain_loss_line_plot.png"
        accounttype_line_plot_path = report_id + "_accounttype_line_plot.png"
        marginal_interest_line_plot_path = (
            report_id + "_marginal_interest_line_plot.png"
        )
        milestone_scatter_plot_path = report_id + "_milestone_scatter_plot.png"
        all_line_plot_path = report_id + "_all_line_plot.png"
        sankey_path = report_id + "_sankey.jpg"

        self.plotAll(E, image_output_dir / all_line_plot_path)
        self.plotNetWorth(E, image_output_dir / networth_line_plot_path)
        self.plotAccountTypeTotals(E, image_output_dir / accounttype_line_plot_path)
        self.plotMarginalInterest(E, image_output_dir / marginal_interest_line_plot_path)
        self.plotNetGainLoss(E, image_output_dir / net_gain_loss_line_plot_path)
        self.plotMilestoneDates(E, image_output_dir / milestone_scatter_plot_path)
        try:
            self.plotSankeyDiagram(E, image_output_dir / sankey_path)
        except Exception as exc:
            sankey_text = "Sankey diagram generation failed: " + str(exc)
            sankey_path = ""

        left_fail_style_tag = ""
        right_fail_style_tag = ""
        fail_message = ""
        if forecast_failed:
            left_fail_style_tag = '<font color ="red">'
            right_fail_style_tag = "</font>"
            fail_message = "This forecast failed to reach the end. The results may not reflect the effect of non-essential transactions accurately."

        html_body = (
            """
        <!DOCTYPE html>
        <html>
        <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Expense Forecast Report #"""
            + str(report_id)
            + """</title>
        <style>
        :root {
          color-scheme: dark;
          --bg: #0b1120;
          --panel: #111827;
          --panel-soft: #172033;
          --panel-strong: #1e293b;
          --border: #334155;
          --border-soft: #243244;
          --text: #e5e7eb;
          --text-muted: #a8b3c7;
          --accent: #38bdf8;
          --accent-strong: #2563eb;
          --accent-soft: #0f3a5c;
          --danger: #fb7185;
        }
        html {
          background: var(--bg);
        }
        body {
          max-width: 1180px;
          margin: 0 auto;
          padding: 40px 32px 64px;
          background: var(--bg);
          color: var(--text);
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          line-height: 1.5;
          text-align: left;
        }
        h1, h3, h4 {
          color: #f8fafc;
        }
        h1 {
          margin-top: 0;
          letter-spacing: 0;
        }
        h3 {
          margin-top: 0;
        }
        p {
          color: var(--text-muted);
        }
        a {
          color: var(--accent);
        }
        .tab {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
          margin-top: 28px;
          padding: 8px;
          border: 1px solid var(--border);
          border-radius: 8px 8px 0 0;
          background-color: var(--panel);
        }
        .tab button {
          background-color: var(--panel-strong);
          color: var(--text-muted);
          border: 1px solid transparent;
          border-radius: 6px;
          outline: none;
          cursor: pointer;
          padding: 12px 14px;
          transition: background-color 0.2s, border-color 0.2s, color 0.2s;
        }
        .tab button:hover {
          background-color: var(--accent-soft);
          border-color: #1d4ed8;
          color: #f8fafc;
        }
        .tab button.active {
          background-color: var(--accent-strong);
          border-color: #60a5fa;
          color: #ffffff;
        }
        .tabcontent {
          display: none;
          padding: 24px;
          border: 1px solid var(--border);
          border-top: none;
          border-radius: 0 0 8px 8px;
          background: var(--panel);
          box-shadow: 0 18px 60px rgba(0, 0, 0, 0.25);
          overflow-x: auto;
        }
        table {
          border-collapse: collapse;
          margin: 14px 0 24px;
          max-width: 100%;
          color: var(--text);
          background: var(--panel-soft);
          font-size: 0.92rem;
        }
        th, td {
          border: 1px solid var(--border-soft);
          padding: 7px 10px;
          white-space: nowrap;
        }
        th {
          background: var(--panel-strong);
          color: #f8fafc;
          font-weight: 600;
        }
        tr:nth-child(even) td {
          background: rgba(148, 163, 184, 0.06);
        }
        img {
          max-width: 100%;
          height: auto;
          margin: 14px 0 24px;
          border: 1px solid var(--border);
          border-radius: 6px;
          background: #f8fafc;
        }
        font[color="red"] {
          color: var(--danger);
        }
        </style>
        </head>
        <body>
        <h1>"""
            + left_fail_style_tag
            + """Expense Forecast Report #"""
            + str(report_id)
            + right_fail_style_tag
            + """</h1>
        <p>"""
            + start_date
            + """ to """
            + end_date
            + " "
            + left_fail_style_tag
            + fail_message
            + right_fail_style_tag
            + " "
            + parent_report_text
            + """</p>

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

        <div id="ForecastParameters" class="tabcontent">
          <h3>Forecast Parameters</h3>
          <p>"""
            + summary_text
            + """</p>
          <h3>Accounts</h3>
          <p>"""
            + account_text
            + """</p>
          <h3>Budget Items</h3>
          <p>"""
            + budget_set_text
            + """</p>
          <h3>Memo Rules</h3>
          <p>"""
            + memo_rule_text
            + """</p>
          <h3>Account Milestones</h3>
          <p>"""
            + account_milestone_text
            + """</p>
          <h3>Memo Milestones</h3>
          <p>"""
            + memo_milestone_text
            + """</p>
          <h3>Composite Milestones</h3>
          <p>"""
            + composite_milestone_text
            + """</p>
        </div>

        <div id="NetWorth" class="tabcontent">
          <h3>Net Worth</h3>
          <p>"""
            + networth_text
            + """</p>
          <img src=\""""
            + networth_line_plot_path
            + """\">
        </div>

        <div id="NetGainLoss" class="tabcontent">
          <h3>Net Gain & Loss</h3>
          <p>"""
            + net_gain_loss_text
            + """</p>
          <img src=\""""
            + net_gain_loss_line_plot_path
            + """\">
        </div>

        <div id="AccountType" class="tabcontent">
          <h3>Account Type</h3>
          <p>"""
            + account_type_text
            + """</p>
          <img src=\""""
            + accounttype_line_plot_path
            + """\">
        </div>

        <div id="Interest" class="tabcontent">
          <h3>Interest</h3>
          <p>"""
            + interest_text
            + """</p>
          <img src=\""""
            + marginal_interest_line_plot_path
            + """\">
          """
            + interest_table_html
            + """
        </div>

        <div id="Milestones" class="tabcontent">
          <h3>Milestones</h3>
          <p>"""
            + milestone_text
            + """</p>
          <img src=\""""
            + milestone_scatter_plot_path
            + """\">
          <h4>Account Milestones</h4>
          """
            + am_result_df.to_html()
            + """ <br>
          <h4>Memo Milestones</h4>
          """
            + mm_result_df.to_html()
            + """ <br>
          <h4>Composite Milestones</h4>
          """
            + cm_result_df.to_html()
            + """ <br>
        </div>

        <div id="All" class="tabcontent">
          <h3>All</h3>
          <p>"""
            + all_plot_page_text
            + """</p>
          <img src=\""""
            + all_line_plot_path
            + """\">
        </div>

        <div id="TransactionSchedule" class="tabcontent">
          <h3>Transaction Schedule</h3>
          <p>"""
            + transaction_schedule_text
            + """</p><br>
          Non-essential transactions: <br>
          <p>"""
            + p2_plus_txns_html_table
            + """</p><br><br>
          Credit Card Payments: <br>
          <p>"""
            + cc_payments_html_table
            + """</p><br><br>
          Loan Payments: <br>
          <p>"""
            + loan_payment_html_table
            + """</p><br><br>
          All Transactions: <br>
          """
            + confirmed_df.to_html()
            + """
        </div>

        <div id="Sankey" class="tabcontent">
          <h3>Sankey</h3>
          <p>"""
            + sankey_text
            + """</p>
          <img src=\""""
            + sankey_path
            + """\">
        </div>

        <div id="Forecast Results" class="tabcontent">
          <h3>Forecast Results</h3>
          <p>"""
            + summary_text
            + """</p>
          <p>The visualized data are below:</p>
          <h4>Forecast #"""
            + str(E.unique_id)
            + """:</h4>
          """
            + E.forecast_df.to_html()
            + """
        </div>

        <br>

        <script>
        function openTab(evt, tabName) {
          var i, tabcontent, tablinks;
          tabcontent = document.getElementsByClassName("tabcontent");
          for (i = 0; i < tabcontent.length; i++) {
            tabcontent[i].style.display = "none";
          }
          tablinks = document.getElementsByClassName("tablinks");
          for (i = 0; i < tablinks.length; i++) {
            tablinks[i].className = tablinks[i].className.replace(" active", "");
          }
          document.getElementById(tabName).style.display = "block";
          evt.currentTarget.className += " active";
        }
        document.getElementById("ForecastParameters").style.display = "block";
        </script>

        </body>
        </html>
        """
        )

        with open(html_output_path, "w") as f:
            f.write(html_body)
        log_in_color(
            logger,
            "green",
            "info",
            "Finished writing single forecast report to " + str(html_output_path),
        )
        return html_output_path

    def show_plan(self, forecast_set: ForecastSetInitialConditions):
        raise NotImplementedError

    @classmethod
    def runForecastWithForks(cls,
                             IO,
                             MS,
                             fork_set: MilestoneTriggeredForecastTransition,
                             include_debug_columns=False,
                             log_stack_depth=0):

        # Order of fork options introduces instability, so fork options are processed in order
        summary_columns = {
            "Marginal Interest",
            "Net Gain",
            "Net Loss",
            "Net Worth",
            "Loan Total",
            "CC Debt Total",
        }

        def strip_summary_columns(forecast_df):
            return forecast_df.drop(
                columns=[
                    column
                    for column in summary_columns
                    if column in forecast_df.columns
                ],
                errors="ignore",
            )

        def flatten_milestone_results(milestone_results):
            flattened_results = {}
            if milestone_results is None:
                return flattened_results

            if isinstance(milestone_results, dict):
                return milestone_results

            for result_group in milestone_results:
                if result_group is None:
                    continue
                flattened_results.update(result_group)
            return flattened_results

        def append_date_slice(destination_df, source_df, start_date, end_date):
            if source_df is None:
                return destination_df

            source_df = strip_summary_columns(source_df)
            if source_df.empty:
                return destination_df

            source_dates = source_df["Date"].apply(cls._normalize_date_value)
            slice_sel_vec = (source_dates >= start_date) & (source_dates <= end_date)
            slice_df = source_df.loc[slice_sel_vec, :].copy()

            if destination_df is None:
                destination_df = source_df.head(0).copy()

            if slice_df.empty:
                return destination_df

            return pd.concat([destination_df, slice_df], ignore_index=True)

        def account_set_at_forecast_row(account_set, forecast_row):
            account_set = copy.deepcopy(account_set)

            for account in account_set.accounts:
                if account.name not in forecast_row.index:
                    continue

                account.balance = AccountSet._money(forecast_row[account.name])

                if account.account_type == "checking":
                    account.billing_state.balance = account.balance
                elif account.account_type == "credit":
                    billing_state = account.billing_state
                    billing_state.current_statement_balance = AccountSet._money(
                        forecast_row[f"{account.name}: Curr Stmt Bal"]
                    )
                    billing_state.previous_statement_balance = AccountSet._money(
                        forecast_row[f"{account.name}: Prev Stmt Bal"]
                    )
                    billing_state.billing_cycle_payment_balance = AccountSet._money(
                        forecast_row[
                            f"{account.name}: Credit Billing Cycle Payment Bal"
                        ]
                    )
                    billing_state.end_of_previous_cycle_balance = AccountSet._money(
                        forecast_row[f"{account.name}: Credit End of Prev Cycle Bal"]
                    )
                    AccountSet._sync_debt_account_from_billing_state(account)
                elif account.account_type == "loan":
                    billing_state = account.billing_state
                    billing_state.principal_balance = AccountSet._money(
                        forecast_row[f"{account.name}: Principal Balance"]
                    )
                    billing_state.interest_balance = AccountSet._money(
                        forecast_row[f"{account.name}: Interest"]
                    )
                    billing_state.billing_cycle_payment_balance = AccountSet._money(
                        forecast_row[f"{account.name}: Loan Billing Cycle Payment Bal"]
                    )
                    AccountSet._sync_debt_account_from_billing_state(account)

            return account_set

        def next_initial_conditions(current_IO, next_start_date, next_account_set, next_budget_set):
            kwargs = {}
            if getattr(current_IO, "forecast_name", None) is not None:
                kwargs["forecast_name"] = current_IO.forecast_name
            if getattr(current_IO, "forecast_set_name", None) is not None:
                kwargs["forecast_set_name"] = current_IO.forecast_set_name

            return ExpenseForecastInitialConditions(
                start_date=next_start_date,
                end_date=current_IO.end_date,
                account_set=next_account_set,
                budget_set=next_budget_set,
                memo_rule_set=current_IO.initial_memo_rule_set,
                log_stack_depth=log_stack_depth,
                **kwargs,
            )

        def assert_no_conflicting_duplicate_dates(forecast_df):
            if forecast_df is None or forecast_df.empty:
                return

            duplicate_date_df = forecast_df[
                forecast_df.duplicated(subset=["Date"], keep=False)
            ]
            if duplicate_date_df.empty:
                return

            for duplicate_date, date_group_df in duplicate_date_df.groupby("Date"):
                unique_rows_df = date_group_df.drop_duplicates()
                if unique_rows_df.shape[0] > 1:
                    raise ValueError(
                        "Conflicting duplicate forecast rows found for date "
                        + str(duplicate_date)
                    )

        original_IO = copy.deepcopy(IO)
        current_IO = copy.deepcopy(IO)

        nth_pass = cls.runForecast(current_IO, MS, include_debug_columns=True)
        forecast_df_slices_to_keep_df = strip_summary_columns(nth_pass.forecast_df).head(0).copy()
        confirmed_to_keep_df = nth_pass.confirmed_df.head(0).copy()
        deferred_to_keep_df = nth_pass.deferred_df.head(0).copy()
        skipped_to_keep_df = nth_pass.skipped_df.head(0).copy()

        slice_start_date = current_IO.start_date
        for fork_milestone_name, swap_sets in fork_set.milestone_name_to_budget_swap_set.items():
            flattened_milestone_results = flatten_milestone_results(
                nth_pass.milestone_results
            )
            milestone_date = flattened_milestone_results.get(fork_milestone_name)
            if milestone_date is None:
                continue

            milestone_date = cls._normalize_date_value(milestone_date)
            if milestone_date < slice_start_date:
                continue

            forecast_df_slices_to_keep_df = append_date_slice(
                forecast_df_slices_to_keep_df,
                nth_pass.forecast_df,
                slice_start_date,
                milestone_date,
            )
            confirmed_to_keep_df = append_date_slice(
                confirmed_to_keep_df,
                nth_pass.confirmed_df,
                slice_start_date,
                milestone_date,
            )
            deferred_to_keep_df = append_date_slice(
                deferred_to_keep_df,
                nth_pass.deferred_df,
                slice_start_date,
                milestone_date,
            )
            skipped_to_keep_df = append_date_slice(
                skipped_to_keep_df,
                nth_pass.skipped_df,
                slice_start_date,
                milestone_date,
            )

            kept_forecast_rows = forecast_df_slices_to_keep_df[
                forecast_df_slices_to_keep_df["Date"].apply(cls._normalize_date_value)
                == milestone_date
            ]
            if kept_forecast_rows.empty:
                raise ValueError(
                    "Could not sync fork state because no forecast row was kept for "
                    + str(milestone_date)
                )

            next_start_date = milestone_date + datetime.timedelta(days=1)
            if next_start_date >= current_IO.end_date:
                slice_start_date = next_start_date
                break

            next_account_set = account_set_at_forecast_row(
                current_IO.initial_account_set,
                kept_forecast_rows.tail(1).iloc[0],
            )
            next_budget_set = current_IO.initial_budget_set - swap_sets[0] + swap_sets[1]
            current_IO = next_initial_conditions(
                current_IO,
                next_start_date,
                next_account_set,
                next_budget_set,
            )
            slice_start_date = current_IO.start_date
            nth_pass = cls.runForecast(current_IO, MS, include_debug_columns=True)

        if slice_start_date <= current_IO.end_date:
            forecast_df_slices_to_keep_df = append_date_slice(
                forecast_df_slices_to_keep_df,
                nth_pass.forecast_df,
                slice_start_date,
                current_IO.end_date,
            )
            confirmed_to_keep_df = append_date_slice(
                confirmed_to_keep_df,
                nth_pass.confirmed_df,
                slice_start_date,
                current_IO.end_date,
            )
            deferred_to_keep_df = append_date_slice(
                deferred_to_keep_df,
                nth_pass.deferred_df,
                slice_start_date,
                current_IO.end_date,
            )
            skipped_to_keep_df = append_date_slice(
                skipped_to_keep_df,
                nth_pass.skipped_df,
                slice_start_date,
                current_IO.end_date,
            )

        forecast_slices_to_keep = forecast_df_slices_to_keep_df.reset_index(drop=True)
        assert_no_conflicting_duplicate_dates(forecast_slices_to_keep)
        forecast_slices_to_keep = forecast_slices_to_keep.drop_duplicates(
            subset=["Date"], keep="first"
        ).reset_index(drop=True)

        result_kwargs = {
            "confirmed_df": confirmed_to_keep_df,
            "deferred_df": deferred_to_keep_df,
            "skipped_df": skipped_to_keep_df,
            "milestone_set": MS,
            "milestone_results": cls.evaluateMilestones(
                forecast_slices_to_keep,
                MS,
                log_stack_depth=log_stack_depth,
            ),
        }


        R = ExpenseForecastResult(original_IO, forecast_slices_to_keep, **result_kwargs)

        # Round all values in Memo and Memo Directives
        # (I think I can round other columns as needed w display.precision without changing the data)
        for index, row in R.forecast_df.iterrows():
            new_memo_lines = []
            for m in row["Memo"].split(";"):
                if m.strip() == "":
                    continue
                match = re.search(r".*\$(.*)\)", m)
                if match is None:
                    raise ValueError(f"Could not parse amount from memo: {m}")

                og_amt = float(match.group(1))
                new_amount = f"{og_amt:.2f}"
                # log_in_color(logger, 'white', 'debug', '(case 29) _update_memo_amount')
                new_m = cls._update_memo_amount(m, new_amount=new_amount, log_stack_depth=log_stack_depth).strip()
                new_memo_lines.append(new_m)

            new_md_lines = []
            for md in row["Memo Directives"].split(";"):
                if md.strip() == "":
                    continue
                try:
                    match = re.search(r".*\$(.*)\)", md)
                    if match is None:
                        raise ValueError("Regex did not match")
                    og_amt = float(match.group(1))
                except Exception:
                    print("Offending memo directive:", md)
                    raise

                new_amount = f"{og_amt:.2f}"
                # log_in_color(logger, 'white', 'debug', '(case 30) _update_memo_amount')
                new_md = cls._update_memo_amount(md, new_amount=new_amount, log_stack_depth=log_stack_depth).strip()
                new_md_lines.append(new_md)

            R.forecast_df.loc[index, "Memo"] = "; ".join(new_memo_lines)
            R.forecast_df.loc[index, "Memo Directives"] = "; ".join(new_md_lines)

        # cls.forecast_df = forecast_df
        # cls.skipped_df = skipped_df
        # cls.confirmed_df = confirmed_df
        # cls.deferred_df = deferred_df

        cls.end_ts = datetime.datetime.now()
        R.forecast_df = cls._appendSummaryLines(IO.initial_account_set, R.forecast_df, log_stack_depth=log_stack_depth)
        R.forecast_df = cls._roundForecastOutput(R.forecast_df, decimals=2)
        R.milestone_results = cls.evaluateMilestones(R.forecast_df, R.milestone_set, log_stack_depth=log_stack_depth)

        return R

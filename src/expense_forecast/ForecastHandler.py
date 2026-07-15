"""
Summary
-------

Description
-----------

Contract
--------

@interface-report: show
"""


from __future__ import annotations

from html import escape
from typing import Any

import pandas as pd



from expense_forecast.AccountSet import (
    AccountBoundaryError,
    AccountSet,
    MONEY_BOUNDARY_TOLERANCE,
)
from expense_forecast.LineItemSet import LineItemSet
# from expense_forecast.ForecastSetInitialConditions import ForecastSetInitialConditions
from expense_forecast.MemoRuleSet import MemoRuleSet
from expense_forecast.MilestoneSet import MilestoneSet
from expense_forecast.ExpenseForecastInitialConditions import ExpenseForecastInitialConditions
from expense_forecast.ExpenseForecastResult import ExpenseForecastResult

import hashlib
import hashlib
import json
from datetime import date
from decimal import Decimal
from typing import Any
import datetime
from time import perf_counter
import os
import tempfile
from pathlib import Path
from dateutil.relativedelta import relativedelta
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
#TODO #Codex-write-doctstring-OK
def _stable_df_payload(df):
    """

    @interface-report: ignore
    """
    return (
        df.sort_index(axis=1)
        .reset_index(drop=True)
        .to_dict(orient="records")
    )

#TODO manual review of ForecastHandler docstring
class ForecastHandler:

    """
    Summary
    -------

    Description
    -----------

    Contract
    --------

    @interface-report: show
    """
    #Codex-write-doctstring-OK
    @staticmethod
    def _normalize_date_value(value):
        """
        
        @interface-report: ignore
        """
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

    #Codex-write-doctstring-OK
    @classmethod
    def _normalize_dataframe_date_column(cls, dataframe):
        """
        @interface-report: ignore
        """
        if "Date" in dataframe.columns:
            dataframe["Date"] = dataframe["Date"].apply(cls._normalize_date_value)
        return dataframe

    #Codex-write-doctstring-OK
    @staticmethod
    def _is_empty_account_endpoint(value):
        """
        @interface-report: ignore
        """
        return value is None or value == "None"

    #Codex-write-doctstring-OK
    @staticmethod
    def _roundForecastOutput(forecast_df, decimals=2):
        """
        @interface-report: show
        """
        forecast_df = forecast_df.copy()
        excluded_columns = {"Date", "Next Income Date", "Memo", "Memo Directives"}

        for column in forecast_df.columns:
            if column in excluded_columns:
                continue

            numeric_values = pd.to_numeric(forecast_df[column], errors="coerce")
            if numeric_values.notna().all():
                forecast_df[column] = numeric_values.round(decimals)

        return forecast_df

    #TODO manual review of ForecastHandler.runForecast docstring
    @classmethod
    def runForecast(cls,
                    IO: ExpenseForecastInitialConditions,
                    milestone_set: MilestoneSet,
                    include_debug_columns = False
                    ) -> ExpenseForecastResult:
        # print('Starting Forecast #'+str(cls.unique_id))
        """
        TODO one-line description of ForecastHandler.runForecast.

        TODO multi-line description of ForecastHandler.runForecast.
        TODO explain how ForecastHandler.runForecast participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        IO : object
            TODO one-line description of ForecastHandler.runForecast.IO.

        milestone_set : object
            TODO one-line description of ForecastHandler.runForecast.milestone_set.

        include_debug_columns : bool
            TODO one-line description of ForecastHandler.runForecast.include_debug_columns.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler.runForecast.

        Contract
        --------
        - #TODO contract lines for ForecastHandler.runForecast.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler.runForecast.

        @interface-report: show
        """
        log_stack_depth = 0
        cls.start_ts = datetime.datetime.now() #TODO does F need start_ts ?
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
                account_set=copy.deepcopy(IO.initial_account_set), #TODO OPTIMIZATION copy may not be needed here?
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
        milestone_results = MilestoneSet.evaluateMilestones(forecast_df, milestone_set, log_stack_depth=log_stack_depth)

        result_kwargs = {
            "confirmed_df": confirmed_df,
            "deferred_df": deferred_df,
            "skipped_df": skipped_df,
        }
        if milestone_set:
            result_kwargs["milestone_set"] = milestone_set
            result_kwargs["milestone_results"] = milestone_results

        R = ExpenseForecastResult(IO, forecast_df,  cls.start_ts, cls.end_ts, **result_kwargs)
        log_in_color(
            logger, "white", "info", "Finished Forecast " + str(IO.unique_id)
        )
        #TODO make this conditional on a --print flag
        # log_in_color(logger, "white", "info", cls.forecast_df.to_string())
        # if play_notification_sound:
        #     notification_sounds.play_notification_sound()

        return R

    @staticmethod
    def _approximate_output_dates(start_date, end_date):
        """Return start/end plus month boundaries without expanding daily rows."""
        dates = [start_date]
        cursor = date(start_date.year, start_date.month, 1)
        if cursor <= start_date:
            cursor = (cursor.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
        while cursor < end_date:
            dates.append(cursor)
            cursor = (cursor.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
        if end_date != dates[-1]:
            dates.append(end_date)
        return dates

    @staticmethod
    def _approximate_memo_line(memo, count, account_from, account_to, amount):
        endpoint = account_from if account_from not in [None, "", "None"] else account_to
        sign = "-" if account_from not in [None, "", "None"] else "+"
        count_text = f" x{count}" if count > 1 else ""
        return f"{memo}{count_text} ({endpoint} {sign}${amount:.2f})"

    @staticmethod
    def _investment_transfer_directive(
        account_set, account_from, account_to, amount
    ):
        if account_to == "ALL_LOANS":
            return None
        account_from_obj = account_set._get_account_by_name(account_from)
        account_to_obj = account_set._get_account_by_name(account_to)
        if account_to_obj is not None and account_to_obj.account_type == "investment":
            return f"INVESTMENT CONTRIBUTION ({account_to_obj.name} +${amount})"
        if (
            account_from_obj is not None
            and account_from_obj.account_type == "investment"
            and account_to_obj is not None
        ):
            return f"INVESTMENT WITHDRAWAL ({account_to_obj.name} +${amount})"
        return None

    @classmethod
    def runForecastApproximate(
        cls,
        IO: ExpenseForecastInitialConditions,
        milestone_set: MilestoneSet,
        include_debug_columns=False,
    ) -> ExpenseForecastResult:
        """Run an event-based, monthly-grain approximation of a forecast.

        Output rows occur only at the forecast endpoints and intervening firsts
        of the month.  Transactions are grouped into those rows, while loan
        interest is calculated over exact elapsed-day spans between meaningful
        events rather than by iterating over every day.
        """
        start_ts = datetime.datetime.now()
        log_in_color(
            logger, "white", "info", "Starting Approximate Forecast " + str(IO.unique_id)
        )
        account_set = copy.deepcopy(IO.initial_account_set)
        memo_rule_set = copy.deepcopy(IO.initial_memo_rule_set)
        output_dates = cls._approximate_output_dates(IO.start_date, IO.end_date)
        schedule = IO.initial_budget_set.getLineItemSchedule().copy()
        if not schedule.empty:
            schedule["Date"] = schedule["Date"].apply(cls._normalize_date_value)

        transaction_columns = list(schedule.columns)
        confirmed_records = []
        skipped_records = []
        pending_deferred_records = []
        if isinstance(IO.initial_deferred_df, pd.DataFrame):
            pending_deferred_records = IO.initial_deferred_df.to_dict(orient="records")
        if isinstance(IO.initial_skipped_df, pd.DataFrame):
            skipped_records = IO.initial_skipped_df.to_dict(orient="records")

        income_dates = (
            sorted(
                set(
                    schedule.loc[
                        schedule["Income_Flag"].astype(bool), "Date"
                    ].tolist()
                )
            )
            if not schedule.empty
            else []
        )

        rows = []
        initial_row = {
            "Date": output_dates[0],
            **account_set.getForecastAccountBalances(include_debug_columns),
            "Next Income Date": "",
            "Memo Directives": "",
            "Memo": "",
        }
        rows.append(initial_row)

        loan_interest_cursor = {}
        investment_return_cursor = {}
        for account in account_set.accounts:
            if account.account_type == "loan":
                loan_interest_cursor[account.name] = max(
                    IO.start_date, account.billing_state.billing_cycle_start_date
                )
            elif account.account_type == "investment":
                investment_return_cursor[account.name] = max(
                    IO.start_date,
                    account.billing_state.billing_cycle_start_date
                    - datetime.timedelta(days=1),
                )

        def sync(account):
            account_set._sync_debt_account_from_billing_state(account)

        def accrue_loan_to(account, event_date, directives):
            cursor = loan_interest_cursor[account.name]
            if event_date <= cursor:
                return
            days = (event_date - cursor).days
            state = account.billing_state
            interest = state.principal_balance * state.apr * Decimal(days) / Decimal("365.25")
            state.interest_balance += interest
            loan_interest_cursor[account.name] = event_date
            sync(account)
            if interest:
                directives.append(
                    f"LOAN INTEREST ({account.name}: Interest +${interest:.2f})"
                )

        def accrue_investment_to(account, event_date, directives):
            cursor = investment_return_cursor[account.name]
            if event_date <= cursor:
                return
            growth = account.billing_state.accrue_return((event_date - cursor).days)
            investment_return_cursor[account.name] = event_date
            account.balance = account.billing_state.balance
            if growth:
                directives.append(
                    f"INVESTMENT RETURN ({account.name} +${growth:.2f})"
                )

        def attempt_transaction(base_account_set, txn, amount):
            """Execute against a copy and return the copy only when valid."""
            candidate_account_set = copy.deepcopy(base_account_set)
            try:
                executed = candidate_account_set.executeTransaction(
                    txn["Account_From"],
                    txn["Account_To"],
                    amount,
                    income_flag=bool(txn["Income_Flag"]),
                )
            except AccountBoundaryError:
                return None, Decimal("0")
            if executed is None:
                executed = Decimal(str(amount))
            return candidate_account_set, Decimal(str(executed))

        def maximum_partial_transaction(base_account_set, txn):
            """Find the largest currently valid amount without mutating state."""
            requested_amount = Decimal(str(txn["Amount"]))
            low = Decimal("0")
            high = requested_amount
            best_account_set = None
            best_executed_amount = Decimal("0")

            for _ in range(60):
                if high - low <= MONEY_BOUNDARY_TOLERANCE:
                    break
                candidate_amount = (low + high) / Decimal("2")
                candidate_account_set, executed_amount = attempt_transaction(
                    base_account_set,
                    txn,
                    candidate_amount,
                )
                if candidate_account_set is None:
                    high = candidate_amount
                    continue
                low = candidate_amount
                best_account_set = candidate_account_set
                best_executed_amount = executed_amount

            return best_account_set, best_executed_amount

        def next_income_date_after(transaction_date):
            return next(
                (
                    income_date
                    for income_date in income_dates
                    if income_date > transaction_date
                ),
                None,
            )

        previous_output_date = output_dates[0]
        for output_index, output_date in enumerate(output_dates[1:], start=1):
            directives = []
            memo_groups = {}
            if output_date.day == 1:
                for account in account_set.accounts:
                    if account.account_type == "loan":
                        account.billing_state.billing_cycle_payment_balance = Decimal("0")
            if schedule.empty:
                interval_transactions = []
            else:
                lower_bound = (
                    schedule["Date"] >= previous_output_date
                    if output_index == 1
                    else schedule["Date"] > previous_output_date
                )
                interval_transactions = schedule.loc[
                    lower_bound & (schedule["Date"] <= output_date)
                ].to_dict(orient="records")

            due_deferred = []
            still_pending = []
            for deferred_transaction in pending_deferred_records:
                deferred_date = cls._normalize_date_value(
                    deferred_transaction["Date"]
                )
                deferred_transaction["Date"] = deferred_date
                if deferred_date <= output_date:
                    due_deferred.append(deferred_transaction)
                else:
                    still_pending.append(deferred_transaction)
            pending_deferred_records = still_pending
            interval_transactions.extend(due_deferred)

            def approximate_transaction_sort_key(transaction):
                return (
                    transaction["Date"],
                    transaction["Priority"],
                    0 if bool(transaction["Income_Flag"]) else 1,
                    -float(transaction["Amount"]),
                    str(transaction["Memo"]),
                )

            while interval_transactions:
                interval_transactions.sort(key=approximate_transaction_sort_key)
                txn = interval_transactions.pop(0)
                rule = memo_rule_set.findMatchingMemoRule(txn["Memo"], txn["Priority"])
                account_from = rule.account_from
                account_to = rule.account_to
                investment_endpoints = {
                    endpoint for endpoint in (account_from, account_to)
                    if endpoint not in [None, "", "None", "ALL_LOANS"]
                }
                for endpoint in investment_endpoints:
                    endpoint_account = account_set._get_account_by_name(endpoint)
                    if endpoint_account.account_type == "investment":
                        accrue_investment_to(
                            endpoint_account, txn["Date"], directives
                        )
                if account_to == "ALL_LOANS":
                    for account in account_set.accounts:
                        if account.account_type == "loan":
                            accrue_loan_to(account, txn["Date"], directives)
                else:
                    debt_target = account_set._get_account_by_name(account_to)
                    if debt_target is not None and debt_target.account_type == "loan":
                        accrue_loan_to(debt_target, txn["Date"], directives)

                executable_txn = {
                    **txn,
                    "Account_From": account_from,
                    "Account_To": account_to,
                }
                candidate_account_set, executed_amount = attempt_transaction(
                    account_set,
                    executable_txn,
                    txn["Amount"],
                )

                if (
                    candidate_account_set is None
                    and bool(txn["Partial_Payment_Allowed"])
                ):
                    candidate_account_set, executed_amount = (
                        maximum_partial_transaction(account_set, executable_txn)
                    )

                transaction_permitted = (
                    candidate_account_set is not None
                    and executed_amount > MONEY_BOUNDARY_TOLERANCE
                )
                if not transaction_permitted:
                    if bool(txn["Deferrable"]):
                        next_income_date = next_income_date_after(txn["Date"])
                        deferred_transaction = {
                            column: txn.get(column) for column in transaction_columns
                        }
                        if next_income_date is None or next_income_date > IO.end_date:
                            skipped_records.append(deferred_transaction)
                        else:
                            deferred_transaction["Date"] = next_income_date
                            if next_income_date <= output_date:
                                interval_transactions.append(deferred_transaction)
                            else:
                                pending_deferred_records.append(deferred_transaction)
                    elif int(txn["Priority"]) > 1:
                        skipped_records.append(
                            {
                                column: txn.get(column)
                                for column in transaction_columns
                            }
                        )
                    else:
                        # Preserve mandatory priority-one behavior and its
                        # detailed AccountBoundaryError message.
                        account_set.executeTransaction(
                            account_from,
                            account_to,
                            txn["Amount"],
                            income_flag=bool(txn["Income_Flag"]),
                        )
                    continue

                account_set = candidate_account_set
                if executed_amount <= MONEY_BOUNDARY_TOLERANCE:
                    continue
                confirmed_transaction = {
                    column: txn.get(column) for column in transaction_columns
                }
                confirmed_transaction["Amount"] = executed_amount
                confirmed_records.append(confirmed_transaction)
                investment_transfer_directive = cls._investment_transfer_directive(
                    account_set, account_from, account_to, executed_amount
                )
                if investment_transfer_directive is not None:
                    directives.append(investment_transfer_directive)
                account_to_obj = (
                    None
                    if account_to == "ALL_LOANS"
                    else account_set._get_account_by_name(account_to)
                )
                if account_to_obj is not None and account_to_obj.account_type == "credit":
                    directives.append(
                        f"ADDTL CC PAYMENT ({account_to} -${executed_amount})"
                    )
                key = (txn["Memo"], account_from, account_to)
                count, total = memo_groups.get(key, (0, Decimal("0")))
                memo_groups[key] = (count + 1, total + executed_amount)

            for account in account_set.accounts:
                if account.account_type == "investment":
                    accrue_investment_to(account, output_date, directives)
                    continue
                billing_start = getattr(account.billing_state, "billing_cycle_start_date", None)
                if account.account_type not in ["loan", "credit"] or output_date < billing_start:
                    continue

                checking = next(
                    a for a in account_set.accounts
                    if a.account_type == "checking" and a.primary_checking_ind
                )
                if account.account_type == "loan":
                    accrue_loan_to(account, output_date, directives)
                    payment = min(
                        account.billing_state.minimum_payment,
                        account.billing_state.balance,
                        checking.balance - checking.min_balance,
                    )
                else:
                    interest = account.billing_state.interest_accrued_this_cycle()
                    if interest:
                        directives.append(
                            f"CC INTEREST ({account.name}: Prev Stmt Bal +${interest:.2f})"
                        )
                    account.billing_state = account.billing_state.roll_cycle(output_date)
                    sync(account)
                    payment = min(
                        account.billing_state.remaining_minimum_payment_due(),
                        account.balance,
                        checking.balance - checking.min_balance,
                    )

                if payment > 0:
                    account_set.executeTransaction(
                        checking.name,
                        account.name,
                        payment,
                        minimum_payment_flag=True,
                    )
                    directives.append(
                        f"MINIMUM PAYMENT ({checking.name} -${payment:.2f})"
                    )
                    directives.append(
                        f"MINIMUM PAYMENT ({account.name} +${payment:.2f})"
                    )

            memo_lines = [
                cls._approximate_memo_line(memo, count, account_from, account_to, total)
                for (memo, account_from, account_to), (count, total) in memo_groups.items()
            ]
            for memo_line in memo_lines:
                log_in_color(
                    logger,
                    "white",
                    "debug",
                    f"{output_date} processing binned memo '{memo_line}'",
                )
            rows.append(
                {
                    "Date": output_date,
                    **account_set.getForecastAccountBalances(include_debug_columns),
                    "Next Income Date": "",
                    "Memo Directives": "; ".join(directives),
                    "Memo": "; ".join(memo_lines),
                }
            )
            previous_output_date = output_date

        forecast_df = pd.DataFrame(rows)
        forecast_df = cls._appendSummaryLines(IO.initial_account_set, forecast_df, log_stack_depth=0)
        forecast_df = cls._roundForecastOutput(forecast_df, decimals=2)
        milestone_results = MilestoneSet.evaluateMilestones(
            forecast_df, milestone_set, log_stack_depth=0
        )
        transaction_result_columns = transaction_columns or [
            "Date",
            "Priority",
            "Amount",
            "Memo",
            "Income_Flag",
            "Deferrable",
            "Partial_Payment_Allowed",
        ]
        confirmed_df = pd.DataFrame(
            confirmed_records,
            columns=transaction_result_columns,
        )
        deferred_df = pd.DataFrame(
            pending_deferred_records,
            columns=transaction_result_columns,
        )
        skipped_df = pd.DataFrame(
            skipped_records,
            columns=transaction_result_columns,
        )
        result_kwargs = {
            "confirmed_df": confirmed_df,
            "deferred_df": deferred_df,
            "skipped_df": skipped_df,
            "approximate_flag": True,
        }
        if milestone_set:
            result_kwargs["milestone_set"] = milestone_set
            result_kwargs["milestone_results"] = milestone_results
        result = ExpenseForecastResult(IO, forecast_df, start_ts, end_ts = datetime.datetime.now(), **result_kwargs)
        log_in_color(
            logger, "white", "info", "Finished Approximate Forecast " + str(IO.unique_id)
        )
        return result




    #Codex-write-doctstring-OK
    @classmethod
    def _getInitialForecastRow(cls, start_date, account_set, include_debug_columns=False):
        # print('ENTER _getInitialForecastRow')
        """
        @interface-report: show
        """
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

    #Codex-write-doctstring-OK
    @classmethod
    def _project_account_set_to_forecast_row(
        cls, forecast_df, account_set, d, include_debug_columns=False
    ):
        """
        @interface-report: show
        """
        row_sel_vec = forecast_df["Date"] == d
        projected_balances = account_set.getForecastAccountBalances(
            include_debug_columns=include_debug_columns
        )

        for column_name, value in projected_balances.items():
            if column_name in forecast_df.columns:
                forecast_df.loc[row_sel_vec, column_name] = value

        return forecast_df

    #Codex-write-doctstring-OK
    @classmethod
    def _addANewDayToTheForecast(cls, forecast_df, d):
        """
        @interface-report: show
        """
        new_row_df = copy.deepcopy(forecast_df.tail(1))
        new_row_df.Date = d
        new_row_df["Memo Directives"] = ""
        new_row_df.Memo = ""
        forecast_df = pd.concat([forecast_df, new_row_df])
        forecast_df.reset_index(drop=True, inplace=True)
        return forecast_df

    #TODO "toPreventErrors" makes me think this shouldnt be a method at all
    # is an inline sort not sufficient ? 
    #TODO manual review of ForecastHandler._sortTxnsToPreventErrors docstring
    @classmethod
    def _sortTxnsToPreventErrors(
        cls, relevant_confirmed_df, account_set, memo_set, log_stack_depth
    ):
        """
        TODO one-line description of ForecastHandler._sortTxnsToPreventErrors.

        TODO multi-line description of ForecastHandler._sortTxnsToPreventErrors.
        TODO explain how ForecastHandler._sortTxnsToPreventErrors participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        relevant_confirmed_df : object
            TODO one-line description of ForecastHandler._sortTxnsToPreventErrors.relevant_confirmed_df.

        account_set : object
            TODO one-line description of ForecastHandler._sortTxnsToPreventErrors.account_set.

        memo_set : object
            TODO one-line description of ForecastHandler._sortTxnsToPreventErrors.memo_set.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._sortTxnsToPreventErrors.log_stack_depth.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._sortTxnsToPreventErrors.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._sortTxnsToPreventErrors.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._sortTxnsToPreventErrors.

        @interface-report: show
        """
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

    # TODO Isn't there a flag for this now?
    #TODO manual review of ForecastHandler._checkIfTxnIsIncome docstring
    @classmethod
    def _checkIfTxnIsIncome(cls, confirmed_row, log_stack_depth):
        """
        TODO DEFER one-line description of ForecastHandler._checkIfTxnIsIncome.

        TODO DEFER  multi-line description of ForecastHandler._checkIfTxnIsIncome.
        TODO DEFER  explain how ForecastHandler._checkIfTxnIsIncome participates in this module.
        TODO DEFER  document important state, validation, or serialization behavior.

        Parameters
        ----------
        confirmed_row : object
            TODO DEFER  one-line description of ForecastHandler._checkIfTxnIsIncome.confirmed_row.

        log_stack_depth : int
            TODO DEFER  one-line description of ForecastHandler._checkIfTxnIsIncome.log_stack_depth.

        Returns
        -------
        object
            TODO DEFER  one-line description of return value of ForecastHandler._checkIfTxnIsIncome.

        Contract
        --------
        - #TODO DEFER  contract lines for ForecastHandler._checkIfTxnIsIncome.
        - #TODO DEFER  document exceptions, mutations, and precision assumptions for ForecastHandler._checkIfTxnIsIncome.

        @interface-report: show
        """
        m_income = re.search(r"income", confirmed_row.Memo)
        income_flag = m_income is not None
        # if m_income is not None:
        #     log_in_color(logger, 'yellow', 'debug',
        #                  'transaction flagged as income: ' + m_income.group(0), 3)

        return income_flag

    #Codex-write-doctstring-OK
    @classmethod
    def _updateBalancesAndMemo(
        cls, forecast_df, account_set, confirmed_row, memo_rule, d, log_stack_depth
    ):
        # log_in_color(logger,'white','debug','ENTER _updateBalancesAndMemo',log_stack_depth)
        """
        TODO one-line description of ForecastHandler._updateBalancesAndMemo.

        TODO multi-line description of ForecastHandler._updateBalancesAndMemo.
        TODO explain how ForecastHandler._updateBalancesAndMemo participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        forecast_df : object
            TODO one-line description of ForecastHandler._updateBalancesAndMemo.forecast_df.

        account_set : object
            TODO one-line description of ForecastHandler._updateBalancesAndMemo.account_set.

        confirmed_row : object
            TODO one-line description of ForecastHandler._updateBalancesAndMemo.confirmed_row.

        memo_rule : object
            TODO one-line description of ForecastHandler._updateBalancesAndMemo.memo_rule.

        d : object
            TODO one-line description of ForecastHandler._updateBalancesAndMemo.d.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._updateBalancesAndMemo.log_stack_depth.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._updateBalancesAndMemo.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._updateBalancesAndMemo.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._updateBalancesAndMemo.

        @interface-report: show
        """
        log_stack_depth += 1
        # log_in_color(logger, 'white', 'debug', 'memo_rule_row:', log_stack_depth)
        # log_in_color(logger, 'white', 'debug', memo_rule_row.to_string(), log_stack_depth)

        # Select the row corresponding to the given date
        row_sel_vec = forecast_df["Date"] == d

        investment_transfer_directive = cls._investment_transfer_directive(
            account_set,
            memo_rule.account_from,
            memo_rule.account_to,
            confirmed_row.Amount,
        )
        if investment_transfer_directive is not None:
            forecast_df.loc[
                row_sel_vec, "Memo"
            ] += f"; {confirmed_row.Memo} ({memo_rule.account_from} -${confirmed_row.Amount}) "
            forecast_df.loc[
                row_sel_vec, "Memo Directives"
            ] += f"; {investment_transfer_directive} "

        # Memo handling when Account_To is not 'ALL_LOANS'
        if (
            memo_rule.account_to != "ALL_LOANS"
            and investment_transfer_directive is None
        ):
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
                if (
                    account_row["Account_Type"] == "checking"
                    and delta < 0
                    and cls._is_empty_account_endpoint(memo_rule.account_from)
                ):
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
                    account_row.Account_Type.lower() == "credit"
                    and account_row.Name.split(":")[0] != memo_rule.account_from
                    and delta > 0
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

    #TODO manual review of ForecastHandler._annotateAcceptedProposedTransaction docstring
    @classmethod
    def _annotateAcceptedProposedTransaction(
        cls, forecast_df, proposed_row, memo_rule_row, d, account_set, log_stack_depth
    ):
        """
        TODO one-line description of ForecastHandler._annotateAcceptedProposedTransaction.

        TODO multi-line description of ForecastHandler._annotateAcceptedProposedTransaction.
        TODO explain how ForecastHandler._annotateAcceptedProposedTransaction participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        forecast_df : object
            TODO one-line description of ForecastHandler._annotateAcceptedProposedTransaction.forecast_df.

        proposed_row : object
            TODO one-line description of ForecastHandler._annotateAcceptedProposedTransaction.proposed_row.

        memo_rule_row : object
            TODO one-line description of ForecastHandler._annotateAcceptedProposedTransaction.memo_rule_row.

        d : object
            TODO one-line description of ForecastHandler._annotateAcceptedProposedTransaction.d.

        account_set : object
            TODO one-line description of ForecastHandler._annotateAcceptedProposedTransaction.account_set.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._annotateAcceptedProposedTransaction.log_stack_depth.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._annotateAcceptedProposedTransaction.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._annotateAcceptedProposedTransaction.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._annotateAcceptedProposedTransaction.

        @interface-report: show
        """
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
    #TODO manual review of ForecastHandler._attemptTransaction docstring
    @classmethod
    def _attemptTransaction(
        cls, end_date, forecast_df, account_set, memo_set, confirmed_df, proposed_row_df, log_stack_depth, include_debug_columns=False
    ):
        """
        TODO one-line description of ForecastHandler._attemptTransaction.

        TODO multi-line description of ForecastHandler._attemptTransaction.
        TODO explain how ForecastHandler._attemptTransaction participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        end_date : date
            TODO one-line description of ForecastHandler._attemptTransaction.end_date.

        forecast_df : object
            TODO one-line description of ForecastHandler._attemptTransaction.forecast_df.

        account_set : object
            TODO one-line description of ForecastHandler._attemptTransaction.account_set.

        memo_set : object
            TODO one-line description of ForecastHandler._attemptTransaction.memo_set.

        confirmed_df : object
            TODO one-line description of ForecastHandler._attemptTransaction.confirmed_df.

        proposed_row_df : object
            TODO one-line description of ForecastHandler._attemptTransaction.proposed_row_df.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._attemptTransaction.log_stack_depth.

        include_debug_columns : bool
            TODO one-line description of ForecastHandler._attemptTransaction.include_debug_columns.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._attemptTransaction.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._attemptTransaction.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._attemptTransaction.

        @interface-report: show
        """
        # log_in_color(
        #     logger,
        #     "white",
        #     "info",
        #     str(proposed_row_df.Date) + " ENTER _attemptTransaction",
        #     log_stack_depth,
        # )
        log_stack_depth += 1
        attempt_started_at = perf_counter()

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
            simulation_elapsed = perf_counter() - attempt_started_at
            # log_in_color(
            #     logger,
            #     "cyan",
            #     "info",
            #     f"{txn_date} _attemptTransaction future forecast updated in "
            #     f"{simulation_elapsed:.2f} seconds",
            #     log_stack_depth,
            # )

            # Exclude the first row since it's considered final and not part of the new forecast
            hypothetical_future_forecast = hypothetical_future_forecast.iloc[1:].copy()

            # Extract past forecast rows before the transaction date
            past_forecast = forecast_df[forecast_df["Date"] < txn_date].copy()

            # Combine past forecast with the hypothetical future forecast
            updated_forecast = pd.concat(
                [past_forecast, hypothetical_future_forecast], ignore_index=True
            )

            log_stack_depth -= 1
            # log_in_color(
            #     logger,
            #     "white",
            #     "info",
            #     str(proposed_row_df.Date) + " EXIT _attemptTransaction",
            #     log_stack_depth,
            # )
            return updated_forecast  # Transaction is permitted

        except AccountBoundaryError as e:
            simulation_elapsed = perf_counter() - attempt_started_at
            log_in_color(
                logger,
                "cyan",
                "info",
                f"{proposed_row_df['Date']} _attemptTransaction simulation "
                f"rejected after {simulation_elapsed:.2f} seconds",
                log_stack_depth,
            )
            # Log the exception
            # log_in_color(logger, "red", "debug", str(e), log_stack_depth)

            log_stack_depth -= 1
            # log_in_color(
            #     logger,
            #     "white",
            #     "info",
            #     str(proposed_row_df.Date) + " EXIT _attemptTransaction",
            #     log_stack_depth,
            # )

            # Return None to indicate that the transaction is not permitted
            return None

    # @profile
    #TODO manual review of ForecastHandler._processConfirmedTransactions docstring
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
        """
        TODO one-line description of ForecastHandler._processConfirmedTransactions.

        TODO multi-line description of ForecastHandler._processConfirmedTransactions.
        TODO explain how ForecastHandler._processConfirmedTransactions participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        forecast_df : object
            TODO one-line description of ForecastHandler._processConfirmedTransactions.forecast_df.

        relevant_confirmed_df : object
            TODO one-line description of ForecastHandler._processConfirmedTransactions.relevant_confirmed_df.

        memo_set : object
            TODO one-line description of ForecastHandler._processConfirmedTransactions.memo_set.

        account_set : object
            TODO one-line description of ForecastHandler._processConfirmedTransactions.account_set.

        d : object
            TODO one-line description of ForecastHandler._processConfirmedTransactions.d.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._processConfirmedTransactions.log_stack_depth.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._processConfirmedTransactions.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._processConfirmedTransactions.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._processConfirmedTransactions.

        @interface-report: show
        """
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
                # log_in_color(
                #     logger,
                #     "white",
                #     "debug",
                #     d.strftime('%Y-%m-%d') + " EXIT _processConfirmedTransactions",
                #     log_stack_depth,
                # )
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

    #Codex-write-doctstring-OK
    @classmethod
    def _extract_interest_accrued_amount(cls, account_basename, memo_directives):
        """
        @interface-report: false
        """
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
    #Codex-write-doctstring-OK
    @classmethod
    def _getTotalPrepaidInCreditCardBillingCycle(
        cls, account_name, account_set, forecast_df, d, log_stack_depth
    ):
        """
        @interface-report: false
        """
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     str(d) + " ENTER _getTotalPrepaidInCreditCardBillingCycle",
        #     log_stack_depth,
        # )
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
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     str(d) + " EXIT _getTotalPrepaidInCreditCardBillingCycle",
        #     log_stack_depth,
        # )
        return total_prepaid_amount

    # TODO look closer at F._getFutureMinPaymentAmount. I think it may be valid 
    # that billing_state is not used,
    # but perhaps next_min_payment_amount could be added to billing_state?
    @classmethod
    def _getFutureMinPaymentAmount(
        cls, account_name, account_set, forecast_df, d, log_stack_depth
    ):
        """
        @interface-report: false
        """
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     str(d) + " ENTER _getFutureMinPaymentAmount",
        #     log_stack_depth,
        # )
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
            # log_in_color(
            #     logger,
            #     "white",
            #     "debug",
            #     str(d) + " EXIT _getFutureMinPaymentAmount",
            #     log_stack_depth,
            # )
            return min_payment_amount

        # If no minimum payment on the current date, find the next billing date

        # todo unclear if this is still wrong ; pylance type warning
        next_billing_date = generate_date_sequence(
            d, 32, interval="monthly"
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
            # log_in_color(
            #     logger,
            #     "white",
            #     "debug",
            #     str(d) + " future min_payment_amount = 0",
            #     log_stack_depth,
            # )
            # log_in_color(
            #     logger,
            #     "white",
            #     "debug",
            #     str(d) + " EXIT _getFutureMinPaymentAmount",
            #     log_stack_depth,
            # )
            return 0.0

        # Extract minimum payment amount from the memo directives on the next billing date
        memo_directives = check_region.loc[future_min_payment_date_sel_vec][
            "Memo Directives"
        ].iat[0]
        min_payment_amount = cls._extract_min_payment_amount(
            memo_directives=memo_directives, base_account_name=base_account_name, log_stack_depth=log_stack_depth)

        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     "next_billing_date:" + str(next_billing_date),
        #     log_stack_depth,
        # )
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     "next bd memo_directives:" + str(memo_directives),
        #     log_stack_depth,
        # )
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     "next bd min_payment_amount:" + str(min_payment_amount),
        #     log_stack_depth,
        # )

        log_stack_depth -= 1
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     str(d) + " EXIT _getFutureMinPaymentAmount",
        #     log_stack_depth,
        # )
        return min_payment_amount

    # @profile
    #Codex-write-doctstring-OK
    @classmethod
    def _extract_min_payment_amount(cls, memo_directives, base_account_name, log_stack_depth):
        """
        TODO one-line description of ForecastHandler._extract_min_payment_amount.

        TODO multi-line description of ForecastHandler._extract_min_payment_amount.
        TODO explain how ForecastHandler._extract_min_payment_amount participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        memo_directives : object
            TODO one-line description of ForecastHandler._extract_min_payment_amount.memo_directives.

        base_account_name : object
            TODO one-line description of ForecastHandler._extract_min_payment_amount.base_account_name.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._extract_min_payment_amount.log_stack_depth.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._extract_min_payment_amount.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._extract_min_payment_amount.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._extract_min_payment_amount.

        @interface-report: show
        """
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     "ENTER _extract_min_payment_amount",
        #     log_stack_depth,
        # )
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
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     "EXIT _extract_min_payment_amount",
        #     log_stack_depth,
        # )
        return min_payment_amount

    # @profile
    #TODO manual review of ForecastHandler._processProposedTransactions docstring
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
        """
        TODO one-line description of ForecastHandler._processProposedTransactions.

        TODO multi-line description of ForecastHandler._processProposedTransactions.
        TODO explain how ForecastHandler._processProposedTransactions participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        end_date : date
            TODO one-line description of ForecastHandler._processProposedTransactions.end_date.

        account_set : object
            TODO one-line description of ForecastHandler._processProposedTransactions.account_set.

        forecast_df : object
            TODO one-line description of ForecastHandler._processProposedTransactions.forecast_df.

        d : object
            TODO one-line description of ForecastHandler._processProposedTransactions.d.

        memo_set : object
            TODO one-line description of ForecastHandler._processProposedTransactions.memo_set.

        confirmed_df : object
            TODO one-line description of ForecastHandler._processProposedTransactions.confirmed_df.

        relevant_proposed_df : object
            TODO one-line description of ForecastHandler._processProposedTransactions.relevant_proposed_df.

        priority_level : object
            TODO one-line description of ForecastHandler._processProposedTransactions.priority_level.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._processProposedTransactions.log_stack_depth.

        include_debug_columns : bool
            TODO one-line description of ForecastHandler._processProposedTransactions.include_debug_columns.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._processProposedTransactions.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._processProposedTransactions.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._processProposedTransactions.

        @interface-report: show
        """
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
                # log_in_color(logger, "green", "info", "Result: ", log_stack_depth)
                # log_in_color(
                #     logger, "green", "info", result.to_string(), log_stack_depth
                # )

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
                        log_in_color(
                            logger,
                            "green",
                            "info",
                            str(d)
                            + " _attemptTransaction REDUCED SUCCESS "
                            + str(proposed_row.Memo)
                            + " "
                            + str(proposed_row.Amount),
                            log_stack_depth,
                        )
                        hypothetical_forecast = result
                        account_set = cls._sync_account_set_w_forecast_day(
                            account_set=account_set, forecast_df=forecast_df, d=d, log_stack_depth=log_stack_depth)
                    else:
                        log_in_color(
                            logger,
                            "red",
                            "info",
                            str(d)
                            + " _attemptTransaction REDUCED FAIL "
                            + str(proposed_row.Memo)
                            + " "
                            + str(proposed_row.Amount),
                            log_stack_depth,
                        )
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

    #TODO manual review of ForecastHandler._minimum_future_available_balances_as_if_a_cc_payment_did_not_happen docstring
    @classmethod
    def _minimum_future_available_balances_as_if_a_cc_payment_did_not_happen(
        cls, account_set, memo_rule_row, forecast_df, d, log_stack_depth
    ):
        """
        TODO one-line description of ForecastHandler._minimum_future_available_balances_as_if_a_cc_payment_did_not_happen.

        TODO multi-line description of ForecastHandler._minimum_future_available_balances_as_if_a_cc_payment_did_not_happen.
        TODO explain how ForecastHandler._minimum_future_available_balances_as_if_a_cc_payment_did_not_happen participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        account_set : object
            TODO one-line description of ForecastHandler._minimum_future_available_balances_as_if_a_cc_payment_did_not_happen.account_set.

        memo_rule_row : object
            TODO one-line description of ForecastHandler._minimum_future_available_balances_as_if_a_cc_payment_did_not_happen.memo_rule_row.

        forecast_df : object
            TODO one-line description of ForecastHandler._minimum_future_available_balances_as_if_a_cc_payment_did_not_happen.forecast_df.

        d : object
            TODO one-line description of ForecastHandler._minimum_future_available_balances_as_if_a_cc_payment_did_not_happen.d.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._minimum_future_available_balances_as_if_a_cc_payment_did_not_happen.log_stack_depth.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._minimum_future_available_balances_as_if_a_cc_payment_did_not_happen.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._minimum_future_available_balances_as_if_a_cc_payment_did_not_happen.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._minimum_future_available_balances_as_if_a_cc_payment_did_not_happen.

        @interface-report: show
        """
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     str(d)
        #     + " ENTER _minimum_future_available_balances_as_if_a_cc_payment_did_not_happen ",
        #     log_stack_depth,
        # )
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

        # print("check_region:")
        # print(check_region.to_string())

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

            # log_in_color(
            #     logger, "white", "debug", "pre_next_payment_df:", log_stack_depth
            # )
            # log_in_color(
            #     logger,
            #     "white",
            #     "debug",
            #     pre_next_payment_df.to_string(),
            #     log_stack_depth,
            # )
            # log_in_color(
            #     logger,
            #     "white",
            #     "debug",
            #     "post_next_payment_inclusive_df:",
            #     log_stack_depth,
            # )
            # log_in_color(
            #     logger,
            #     "white",
            #     "debug",
            #     post_next_payment_inclusive_df.to_string(),
            #     log_stack_depth,
            # )

            amount_in_question = min(
                min(pre_next_payment_df[memo_rule_row.Account_From]),
                min(post_next_payment_inclusive_df[memo_rule_row.Account_From]),
            )
        else:
            amount_in_question = cls._getMinimumFutureAvailableBalances(
                account_set=account_set, forecast_df=forecast_df, d=d, log_stack_depth=log_stack_depth
            )[memo_rule_row.Account_From]

        log_stack_depth -= 1
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     str(d)
        #     + " EXIT _minimum_future_available_balances_as_if_a_cc_payment_did_not_happen ",
        #     log_stack_depth,
        # )
        return amount_in_question

    # TODO make the name of this more clear, and then have codex write the docstring
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
        TODO one-line description of ForecastHandler._calculate_reduced_amount.

        TODO multi-line description of ForecastHandler._calculate_reduced_amount.
        TODO explain how ForecastHandler._calculate_reduced_amount participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        account_set : object
            TODO one-line description of ForecastHandler._calculate_reduced_amount.account_set.

        memo_rule_row : object
            TODO one-line description of ForecastHandler._calculate_reduced_amount.memo_rule_row.

        max_available_funds : object
            TODO one-line description of ForecastHandler._calculate_reduced_amount.max_available_funds.

        forecast_df : object
            TODO one-line description of ForecastHandler._calculate_reduced_amount.forecast_df.

        d : object
            TODO one-line description of ForecastHandler._calculate_reduced_amount.d.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._calculate_reduced_amount.log_stack_depth.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._calculate_reduced_amount.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._calculate_reduced_amount.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._calculate_reduced_amount.

        @interface-report: show
        """
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     str(d) + " ENTER _calculate_reduced_amount",
        #     log_stack_depth,
        # )
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
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     "source_bound..: " + str(source_bound),
        #     log_stack_depth,
        # )
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     "dest_bound....: " + str(dest_bound),
        #     log_stack_depth,
        # )
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     "reduced_amount: " + str(reduced_amount),
        #     log_stack_depth,
        # )

        log_stack_depth -= 1
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     str(d) + " EXIT _calculate_reduced_amount",
        #     log_stack_depth,
        # )
        return reduced_amount

    # @profile
    #Codex-write-doctstring-OK
    @classmethod
    def _find_next_income_date(cls, forecast_df, d, log_stack_depth):
        """
        @interface-report: ignore
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
    #TODO manual review of ForecastHandler._update_forecast_with_hypothetical docstring
    @classmethod
    def _update_forecast_with_hypothetical(
        cls, forecast_df, hypothetical_forecast, d, log_stack_depth
    ):
        # Split the forecast into past and future
        """
        TODO one-line description of ForecastHandler._update_forecast_with_hypothetical.

        TODO multi-line description of ForecastHandler._update_forecast_with_hypothetical.
        TODO explain how ForecastHandler._update_forecast_with_hypothetical participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        forecast_df : object
            TODO one-line description of ForecastHandler._update_forecast_with_hypothetical.forecast_df.

        hypothetical_forecast : object
            TODO one-line description of ForecastHandler._update_forecast_with_hypothetical.hypothetical_forecast.

        d : object
            TODO one-line description of ForecastHandler._update_forecast_with_hypothetical.d.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._update_forecast_with_hypothetical.log_stack_depth.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._update_forecast_with_hypothetical.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._update_forecast_with_hypothetical.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._update_forecast_with_hypothetical.

        @interface-report: show
        """
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

    #Codex-write-doctstring-OK
    @classmethod
    def _update_forecast_balances(cls, forecast_df, account_set, d, log_stack_depth):
        # Update each account balance in the forecast
        """
        @interface-report: ignore
        """
        for index, account_row in account_set.getAccounts().iterrows():
            account_name = account_row["Name"]
            balance = account_row["Balance"]

            if account_name in forecast_df.columns:
                if isinstance(balance, Decimal) and forecast_df[account_name].dtype != object:
                    forecast_df[account_name] = forecast_df[account_name].astype(object)
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
    #TODO manual review of ForecastHandler._processDeferredTransactions docstring
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
        # Increment log stack depth for logging purposes
        """
        TODO one-line description of ForecastHandler._processDeferredTransactions.

        TODO multi-line description of ForecastHandler._processDeferredTransactions.
        TODO explain how ForecastHandler._processDeferredTransactions participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        start_date : date
            TODO one-line description of ForecastHandler._processDeferredTransactions.start_date.

        end_date : date
            TODO one-line description of ForecastHandler._processDeferredTransactions.end_date.

        account_set : object
            TODO one-line description of ForecastHandler._processDeferredTransactions.account_set.

        forecast_df : object
            TODO one-line description of ForecastHandler._processDeferredTransactions.forecast_df.

        d : object
            TODO one-line description of ForecastHandler._processDeferredTransactions.d.

        memo_set : object
            TODO one-line description of ForecastHandler._processDeferredTransactions.memo_set.

        relevant_deferred_df : object
            TODO one-line description of ForecastHandler._processDeferredTransactions.relevant_deferred_df.

        priority_level : object
            TODO one-line description of ForecastHandler._processDeferredTransactions.priority_level.

        confirmed_df : object
            TODO one-line description of ForecastHandler._processDeferredTransactions.confirmed_df.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._processDeferredTransactions.log_stack_depth.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._processDeferredTransactions.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._processDeferredTransactions.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._processDeferredTransactions.

        @interface-report: show
        """
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
    #TODO manual review of ForecastHandler._executeTransactionsForDay docstring
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
        """
        TODO one-line description of ForecastHandler._executeTransactionsForDay.

        TODO multi-line description of ForecastHandler._executeTransactionsForDay.
        TODO explain how ForecastHandler._executeTransactionsForDay participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        end_date : date
            TODO one-line description of ForecastHandler._executeTransactionsForDay.end_date.

        account_set : object
            TODO one-line description of ForecastHandler._executeTransactionsForDay.account_set.

        forecast_df : object
            TODO one-line description of ForecastHandler._executeTransactionsForDay.forecast_df.

        d : object
            TODO one-line description of ForecastHandler._executeTransactionsForDay.d.

        memo_set : object
            TODO one-line description of ForecastHandler._executeTransactionsForDay.memo_set.

        confirmed_df : object
            TODO one-line description of ForecastHandler._executeTransactionsForDay.confirmed_df.

        proposed_df : object
            TODO one-line description of ForecastHandler._executeTransactionsForDay.proposed_df.

        deferred_df : object
            TODO one-line description of ForecastHandler._executeTransactionsForDay.deferred_df.

        skipped_df : object
            TODO one-line description of ForecastHandler._executeTransactionsForDay.skipped_df.

        priority_level : object
            TODO one-line description of ForecastHandler._executeTransactionsForDay.priority_level.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._executeTransactionsForDay.log_stack_depth.

        include_debug_columns : bool
            TODO one-line description of ForecastHandler._executeTransactionsForDay.include_debug_columns.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._executeTransactionsForDay.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._executeTransactionsForDay.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._executeTransactionsForDay.

        @interface-report: show
        """
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
    #TODO manual review of ForecastHandler._processCreditCardBillingDayForDay docstring
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
        """
        TODO one-line description of ForecastHandler._processCreditCardBillingDayForDay.

        TODO multi-line description of ForecastHandler._processCreditCardBillingDayForDay.
        TODO explain how ForecastHandler._processCreditCardBillingDayForDay participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        account_set : object
            TODO one-line description of ForecastHandler._processCreditCardBillingDayForDay.account_set.

        current_forecast_row_df : object
            TODO one-line description of ForecastHandler._processCreditCardBillingDayForDay.current_forecast_row_df.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._processCreditCardBillingDayForDay.log_stack_depth.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._processCreditCardBillingDayForDay.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._processCreditCardBillingDayForDay.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._processCreditCardBillingDayForDay.

        @interface-report: show
        """
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
    #TODO manual review of ForecastHandler._calculateLoanInterestAccrualsForDay docstring
    @classmethod
    def _calculateLoanInterestAccrualsForDay(
        cls, account_set, current_forecast_row_df, log_stack_depth
    ):
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     str(current_forecast_row_df.Date.iat[0])
        #     + " ENTER _calculateLoanInterestAccrualsForDay",
        #     log_stack_depth,
        # )
        # Increment log stack depth for logging purposes
        """
        TODO one-line description of ForecastHandler._calculateLoanInterestAccrualsForDay.

        TODO multi-line description of ForecastHandler._calculateLoanInterestAccrualsForDay.
        TODO explain how ForecastHandler._calculateLoanInterestAccrualsForDay participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        account_set : object
            TODO one-line description of ForecastHandler._calculateLoanInterestAccrualsForDay.account_set.

        current_forecast_row_df : object
            TODO one-line description of ForecastHandler._calculateLoanInterestAccrualsForDay.current_forecast_row_df.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._calculateLoanInterestAccrualsForDay.log_stack_depth.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._calculateLoanInterestAccrualsForDay.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._calculateLoanInterestAccrualsForDay.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._calculateLoanInterestAccrualsForDay.

        @interface-report: show
        """
        log_stack_depth += 1

        # print('PRE INTEREST ACCRUAL FORECAST ROW')
        # print(current_forecast_row_df.to_string())

        current_date = current_forecast_row_df["Date"].iat[0]

        for account in account_set.accounts:
            if account.account_type != "loan":
                continue

            billing_state = account.billing_state
            interest_interval = getattr(billing_state, "interest_interval", None)
            if interest_interval is None:
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
                interval=interest_interval,
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

    @classmethod
    def _calculateInvestmentReturnsForDay(
        cls, account_set, current_forecast_row_df, log_stack_depth
    ):
        """Accrue one day of compound growth for active investments."""
        current_date = current_forecast_row_df["Date"].iat[0]
        directives = [
            item.strip()
            for item in current_forecast_row_df["Memo Directives"].iat[0].split(";")
            if item.strip()
        ]

        for account in account_set.accounts:
            if account.account_type != "investment":
                continue
            billing_start_date = account.billing_state.billing_cycle_start_date
            if isinstance(billing_start_date, datetime.datetime):
                billing_start_date = billing_start_date.date()
            if current_date < billing_start_date:
                continue

            growth = account.billing_state.accrue_return()
            account.balance = account.billing_state.balance
            if growth:
                directives.append(
                    f"INVESTMENT RETURN ({account.name} +${growth})"
                )

        current_forecast_row_df.loc[:, "Memo Directives"] = "; ".join(directives)
        projected_balances = account_set.getForecastAccountBalances(
            include_debug_columns=True
        )
        for column_name, value in projected_balances.items():
            if column_name in current_forecast_row_df.columns:
                current_forecast_row_df.loc[:, column_name] = value
        return current_forecast_row_df

    #TODO forecast_df is not referenced in this method body and idk if it should be
    #TODO manual review of ForecastHandler._executeCreditCardMinimumPayments docstring
    @classmethod
    def _executeCreditCardMinimumPayments(
        cls, forecast_df, account_set, current_forecast_row_df, log_stack_depth
    ):
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     str(current_forecast_row_df.Date.iat[0])
        #     + " ENTER _executeCreditCardMinimumPayments ",
        #     log_stack_depth,
        # )
        """
        TODO one-line description of ForecastHandler._executeCreditCardMinimumPayments.

        TODO multi-line description of ForecastHandler._executeCreditCardMinimumPayments.
        TODO explain how ForecastHandler._executeCreditCardMinimumPayments participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        forecast_df : object
            TODO one-line description of ForecastHandler._executeCreditCardMinimumPayments.forecast_df.

        account_set : object
            TODO one-line description of ForecastHandler._executeCreditCardMinimumPayments.account_set.

        current_forecast_row_df : object
            TODO one-line description of ForecastHandler._executeCreditCardMinimumPayments.current_forecast_row_df.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._executeCreditCardMinimumPayments.log_stack_depth.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._executeCreditCardMinimumPayments.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._executeCreditCardMinimumPayments.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._executeCreditCardMinimumPayments.

        @interface-report: show
        """
        log_stack_depth += 1

        # log_in_color(logger, 'white', 'debug','BEFORE forecast_df:', log_stack_depth)
        # log_in_color(logger, 'white', 'debug', forecast_df.to_string(), log_stack_depth)

        # Loop through real credit accounts; synthetic credit summary rows are
        # projected from CreditCardBillingState and are not payment sources.
        for account in account_set.accounts:
            if account.account_type != "credit":
                continue

            current_date = current_forecast_row_df.Date.iloc[0]
            if not AccountSet.is_billing_date(account, current_date):
                continue

            total_payment_due = account.billing_state.remaining_minimum_payment_due()
            if total_payment_due <= 0:
                continue

            account_set.executeTransaction(
                Account_From=account_set.primary_checking_account_name,
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
                f"CC MIN PAYMENT ({account_set.primary_checking_account_name} -${total_payment_due})",
            ]
            md_split_semicolon = (
                current_forecast_row_df["Memo Directives"].iat[0].split(";")
            )
            md_split_semicolon = [md for md in md_split_semicolon if md]
            md_split_semicolon += memo_parts
            current_forecast_row_df.loc[:, "Memo Directives"] = "; ".join(
                md_split_semicolon
            )

        memo_directives = [
            md.strip()
            for md in current_forecast_row_df["Memo Directives"].iat[0].split(";")
            if md.strip()
        ]
        current_forecast_row_df.loc[:, "Memo Directives"] = "; ".join(
            memo_directives
        )

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
    #TODO manual review of ForecastHandler._executeLoanMinimumPayments docstring
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
        """
        TODO one-line description of ForecastHandler._executeLoanMinimumPayments.

        TODO multi-line description of ForecastHandler._executeLoanMinimumPayments.
        TODO explain how ForecastHandler._executeLoanMinimumPayments participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        account_set : object
            TODO one-line description of ForecastHandler._executeLoanMinimumPayments.account_set.

        current_forecast_row_df : object
            TODO one-line description of ForecastHandler._executeLoanMinimumPayments.current_forecast_row_df.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._executeLoanMinimumPayments.log_stack_depth.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._executeLoanMinimumPayments.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._executeLoanMinimumPayments.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._executeLoanMinimumPayments.

        @interface-report: show
        """
        log_stack_depth += 1

        # log_in_color(logger, 'white', 'debug','before current_forecast_row_df:', log_stack_depth)
        # log_in_color(logger, 'white', 'debug', current_forecast_row_df.to_string(), log_stack_depth)

        primary_checking_account_name = account_set.primary_checking_account_name

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

    #Codex-write-doctstring-OK
    @classmethod
    def _getMinimumFutureAvailableBalances(
        cls, account_set, forecast_df, d, log_stack_depth
    ):
        """
        TODO one-line description of ForecastHandler._getMinimumFutureAvailableBalances.

        TODO multi-line description of ForecastHandler._getMinimumFutureAvailableBalances.
        TODO explain how ForecastHandler._getMinimumFutureAvailableBalances participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        account_set : object
            TODO one-line description of ForecastHandler._getMinimumFutureAvailableBalances.account_set.

        forecast_df : object
            TODO one-line description of ForecastHandler._getMinimumFutureAvailableBalances.forecast_df.

        d : object
            TODO one-line description of ForecastHandler._getMinimumFutureAvailableBalances.d.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._getMinimumFutureAvailableBalances.log_stack_depth.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._getMinimumFutureAvailableBalances.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._getMinimumFutureAvailableBalances.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._getMinimumFutureAvailableBalances.

        @interface-report: show
        """
        # log_in_color(
        #     logger,
        #     "cyan",
        #     "debug",
        #     str(d) + " ENTER _getMinimumFutureAvailableBalances",
        #     log_stack_depth,
        # )
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

        # log_in_color(
        #     logger,
        #     "cyan",
        #     "debug",
        #     "accounts_df:" + str(accounts_df.to_string()),
        #     log_stack_depth,
        # )

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

                # log_in_color(
                #     logger,
                #     "cyan",
                #     "debug",
                #     "total_credit_balance: " + str(total_credit_balance),
                #     log_stack_depth,
                # )

                # Calculate the minimum total credit balance
                min_total_credit_balance = total_credit_balance.min()

                # Calculate available credit
                max_balance = account_row["Max_Balance"]
                min_available_credit = (
                    max_balance - min_total_credit_balance - account_row["Min_Balance"]
                )
                future_available_balances[account_name] = min_available_credit

                # log_in_color(
                #     logger,
                #     "cyan",
                #     "debug",
                #     "min_available_credit: " + str(min_available_credit),
                #     log_stack_depth,
                # )

        # log_in_color(
        #     logger,
        #     "cyan",
        #     "debug",
        #     "future_available_balances: " + str(future_available_balances),
        #     log_stack_depth,
        # )

        # Decrement log stack depth
        log_stack_depth -= 1
        # log_in_color(
        #     logger,
        #     "cyan",
        #     "debug",
        #     str(d) + " EXIT _getMinimumFutureAvailableBalances",
        #     log_stack_depth,
        # )
        return future_available_balances

    # TODO is there a different method with a similar purpose somewhere?
    #TODO manual review of ForecastHandler._sync_account_set_w_forecast_day docstring
    @classmethod
    def _sync_account_set_w_forecast_day(cls, account_set, forecast_df, d, log_stack_depth):
        # log_in_color(logger, 'white', 'debug', str(d)+' ENTER _sync_account_set_w_forecast_day', log_stack_depth)
        """
        TODO one-line description of ForecastHandler._sync_account_set_w_forecast_day.

        TODO multi-line description of ForecastHandler._sync_account_set_w_forecast_day.
        TODO explain how ForecastHandler._sync_account_set_w_forecast_day participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        account_set : object
            TODO one-line description of ForecastHandler._sync_account_set_w_forecast_day.account_set.

        forecast_df : object
            TODO one-line description of ForecastHandler._sync_account_set_w_forecast_day.forecast_df.

        d : object
            TODO one-line description of ForecastHandler._sync_account_set_w_forecast_day.d.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._sync_account_set_w_forecast_day.log_stack_depth.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._sync_account_set_w_forecast_day.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._sync_account_set_w_forecast_day.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._sync_account_set_w_forecast_day.

        @interface-report: show
        """
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

            if account.account_type == "investment":
                account.billing_state.balance = Decimal(str(relevant_balance))
            elif account.account_type == "credit":
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

    #Codex-write-doctstring-OK
    @classmethod
    def _apply_credit_billing_state_delta_to_forecast_row(
        cls,
        forecast_df,
        row_index,
        account_set,
        credit_account_name,
        checking_account_name=None,
        checking_delta=0,
        current_statement_delta=0,
        previous_statement_delta=0,
        billing_cycle_payment_delta=0,
        end_of_previous_cycle_delta=0,
    ):
        """
        TODO one-line description of ForecastHandler._apply_credit_billing_state_delta_to_forecast_row.

        TODO multi-line description of ForecastHandler._apply_credit_billing_state_delta_to_forecast_row.
        TODO explain how ForecastHandler._apply_credit_billing_state_delta_to_forecast_row participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        forecast_df : object
            TODO one-line description of ForecastHandler._apply_credit_billing_state_delta_to_forecast_row.forecast_df.

        row_index : object
            TODO one-line description of ForecastHandler._apply_credit_billing_state_delta_to_forecast_row.row_index.

        account_set : object
            TODO one-line description of ForecastHandler._apply_credit_billing_state_delta_to_forecast_row.account_set.

        credit_account_name : str
            TODO one-line description of ForecastHandler._apply_credit_billing_state_delta_to_forecast_row.credit_account_name.

        checking_account_name : object
            TODO one-line description of ForecastHandler._apply_credit_billing_state_delta_to_forecast_row.checking_account_name.

        checking_delta : float
            TODO one-line description of ForecastHandler._apply_credit_billing_state_delta_to_forecast_row.checking_delta.

        current_statement_delta : float
            TODO one-line description of ForecastHandler._apply_credit_billing_state_delta_to_forecast_row.current_statement_delta.

        previous_statement_delta : float
            TODO one-line description of ForecastHandler._apply_credit_billing_state_delta_to_forecast_row.previous_statement_delta.

        billing_cycle_payment_delta : float
            TODO one-line description of ForecastHandler._apply_credit_billing_state_delta_to_forecast_row.billing_cycle_payment_delta.

        end_of_previous_cycle_delta : float
            TODO one-line description of ForecastHandler._apply_credit_billing_state_delta_to_forecast_row.end_of_previous_cycle_delta.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._apply_credit_billing_state_delta_to_forecast_row.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._apply_credit_billing_state_delta_to_forecast_row.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._apply_credit_billing_state_delta_to_forecast_row.

        @interface-report: show
        """
        credit_account = next(
            account
            for account in account_set.accounts
            if account.name == credit_account_name and account.account_type == "credit"
        )
        billing_state = credit_account.billing_state

        current_statement_column = f"{credit_account.name}: Curr Stmt Bal"
        previous_statement_column = f"{credit_account.name}: Prev Stmt Bal"
        billing_cycle_payment_column = (
            f"{credit_account.name}: Credit Billing Cycle Payment Bal"
        )
        end_of_previous_cycle_column = (
            f"{credit_account.name}: Credit End of Prev Cycle Bal"
        )

        billing_state.current_statement_balance = AccountSet._money(
            forecast_df.at[row_index, current_statement_column]
        ) + AccountSet._money(current_statement_delta)
        billing_state.previous_statement_balance = AccountSet._money(
            forecast_df.at[row_index, previous_statement_column]
        ) + AccountSet._money(previous_statement_delta)
        billing_state.billing_cycle_payment_balance = AccountSet._money(
            forecast_df.at[row_index, billing_cycle_payment_column]
        ) + AccountSet._money(billing_cycle_payment_delta)
        billing_state.end_of_previous_cycle_balance = AccountSet._money(
            forecast_df.at[row_index, end_of_previous_cycle_column]
        ) + AccountSet._money(end_of_previous_cycle_delta)

        AccountSet._sync_debt_account_from_billing_state(credit_account)
        projected_columns = AccountSet.getForecastColumnsForAccount(credit_account)
        for column_name, value in projected_columns.items():
            if column_name in forecast_df.columns:
                forecast_df.at[row_index, column_name] = value

        if checking_account_name is not None:
            checking_account = next(
                account
                for account in account_set.accounts
                if account.name == checking_account_name
            )
            checking_account.balance = AccountSet._money(
                forecast_df.at[row_index, checking_account_name]
            ) + AccountSet._money(checking_delta)
            if getattr(checking_account, "billing_state", None) is not None:
                checking_account.billing_state.balance = checking_account.balance
            forecast_df.at[row_index, checking_account_name] = (
                AccountSet._forecast_value(checking_account.balance)
            )

        return forecast_df

    #Codex-write-doctstring-OK
    @classmethod
    def _apply_loan_billing_state_delta_to_forecast_row(
        cls,
        forecast_df,
        row_index,
        account_set,
        loan_account_name,
        checking_account_name=None,
        checking_delta=0,
        principal_delta=0,
        interest_delta=0,
        billing_cycle_payment_delta=0,
    ):
        """
        TODO one-line description of ForecastHandler._apply_loan_billing_state_delta_to_forecast_row.

        TODO multi-line description of ForecastHandler._apply_loan_billing_state_delta_to_forecast_row.
        TODO explain how ForecastHandler._apply_loan_billing_state_delta_to_forecast_row participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        forecast_df : object
            TODO one-line description of ForecastHandler._apply_loan_billing_state_delta_to_forecast_row.forecast_df.

        row_index : object
            TODO one-line description of ForecastHandler._apply_loan_billing_state_delta_to_forecast_row.row_index.

        account_set : object
            TODO one-line description of ForecastHandler._apply_loan_billing_state_delta_to_forecast_row.account_set.

        loan_account_name : str
            TODO one-line description of ForecastHandler._apply_loan_billing_state_delta_to_forecast_row.loan_account_name.

        checking_account_name : object
            TODO one-line description of ForecastHandler._apply_loan_billing_state_delta_to_forecast_row.checking_account_name.

        checking_delta : float
            TODO one-line description of ForecastHandler._apply_loan_billing_state_delta_to_forecast_row.checking_delta.

        principal_delta : float
            TODO one-line description of ForecastHandler._apply_loan_billing_state_delta_to_forecast_row.principal_delta.

        interest_delta : float
            TODO one-line description of ForecastHandler._apply_loan_billing_state_delta_to_forecast_row.interest_delta.

        billing_cycle_payment_delta : float
            TODO one-line description of ForecastHandler._apply_loan_billing_state_delta_to_forecast_row.billing_cycle_payment_delta.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._apply_loan_billing_state_delta_to_forecast_row.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._apply_loan_billing_state_delta_to_forecast_row.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._apply_loan_billing_state_delta_to_forecast_row.

        @interface-report: show
        """
        loan_account = next(
            account
            for account in account_set.accounts
            if account.name == loan_account_name and account.account_type == "loan"
        )
        billing_state = loan_account.billing_state

        principal_column = f"{loan_account.name}: Principal Balance"
        interest_column = f"{loan_account.name}: Interest"
        billing_cycle_payment_column = (
            f"{loan_account.name}: Loan Billing Cycle Payment Bal"
        )

        billing_state.principal_balance = AccountSet._money(
            forecast_df.at[row_index, principal_column]
        ) + AccountSet._money(principal_delta)
        billing_state.interest_balance = AccountSet._money(
            forecast_df.at[row_index, interest_column]
        ) + AccountSet._money(interest_delta)
        billing_state.billing_cycle_payment_balance = AccountSet._money(
            forecast_df.at[row_index, billing_cycle_payment_column]
        ) + AccountSet._money(billing_cycle_payment_delta)

        AccountSet._sync_debt_account_from_billing_state(loan_account)
        projected_columns = AccountSet.getForecastColumnsForAccount(loan_account)
        for column_name, value in projected_columns.items():
            if column_name in forecast_df.columns:
                forecast_df.at[row_index, column_name] = value

        if checking_account_name is not None:
            checking_account = next(
                account
                for account in account_set.accounts
                if account.name == checking_account_name
            )
            checking_account.balance = AccountSet._money(
                forecast_df.at[row_index, checking_account_name]
            ) + AccountSet._money(checking_delta)
            if getattr(checking_account, "billing_state", None) is not None:
                checking_account.billing_state.balance = checking_account.balance
            forecast_df.at[row_index, checking_account_name] = (
                AccountSet._forecast_value(checking_account.balance)
            )

        return forecast_df

    # @profile
    #Codex-write-doctstring-OK
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
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     "ENTER _propagate_credit_txn_curr_only",
        #     log_stack_depth,
        # )
        """
        TODO one-line description of ForecastHandler._propagate_credit_txn_curr_only.

        TODO multi-line description of ForecastHandler._propagate_credit_txn_curr_only.
        TODO explain how ForecastHandler._propagate_credit_txn_curr_only participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        relevant_account_info_df : object
            TODO one-line description of ForecastHandler._propagate_credit_txn_curr_only.relevant_account_info_df.

        account_deltas_list : object
            TODO one-line description of ForecastHandler._propagate_credit_txn_curr_only.account_deltas_list.

        future_rows_only_df : object
            TODO one-line description of ForecastHandler._propagate_credit_txn_curr_only.future_rows_only_df.

        forecast_df : object
            TODO one-line description of ForecastHandler._propagate_credit_txn_curr_only.forecast_df.

        account_set_before_p2_plus_txn : object
            TODO one-line description of ForecastHandler._propagate_credit_txn_curr_only.account_set_before_p2_plus_txn.

        billing_dates_dict : object
            TODO one-line description of ForecastHandler._propagate_credit_txn_curr_only.billing_dates_dict.

        d : object
            TODO one-line description of ForecastHandler._propagate_credit_txn_curr_only.d.

        post_txn_row_df : object
            TODO one-line description of ForecastHandler._propagate_credit_txn_curr_only.post_txn_row_df.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._propagate_credit_txn_curr_only.log_stack_depth.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._propagate_credit_txn_curr_only.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._propagate_credit_txn_curr_only.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._propagate_credit_txn_curr_only.

        @interface-report: show
        """
        log_stack_depth += 1

        # Extract relevant account names
        checking_account_name = (
            account_set_before_p2_plus_txn.primary_checking_account_name
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

            elif date_iat in cc_billing_dates:
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
                # log_in_color(
                #     logger,
                #     "cyan",
                #     "debug",
                #     str(date_iat)
                #     + " adjusted_payment_amount: "
                #     + str(adjusted_payment_amount),
                #     log_stack_depth,
                # )

                previous_stmt_delta += adjusted_payment_amount
                checking_delta += adjusted_payment_amount
                interest_delta = interest_to_be_charged - og_interest_amount
                # previous_stmt_delta += round(interest_delta, 2)
                previous_stmt_delta += interest_delta
                billing_cycle_payment_delta = 0  # redundant but cant hurt

                # Adjust memos
                # log_in_color(logger, "white", "debug", "(case 1) _update_memo_amount")
                # new_check_memo = cls._update_memo_amount(
                #     og_check_memo, og_check_amount - adjusted_payment_amount, log_stack_depth=log_stack_depth
                # )
                if adjusted_payment_amount >= curr_prev_stmt_bal:
                    # Adjust curr and prev memos
                    if og_curr_amount > 0:
                        # log_in_color(
                        #     logger, "white", "debug", "(case 2) _update_memo_amount"
                        # )
                        new_curr_memo = cls._update_memo_amount(
                            og_curr_memo, adjusted_payment_amount - curr_prev_stmt_bal, log_stack_depth=log_stack_depth
                        )
                    if og_prev_amount > 0:
                        # log_in_color(
                        #     logger, "white", "debug", "(case 3) _update_memo_amount"
                        # )
                        new_prev_memo = cls._update_memo_amount(
                            og_prev_memo, curr_prev_stmt_bal, log_stack_depth=log_stack_depth
                        )
                else:
                    if og_curr_amount > 0:
                        # log_in_color(
                        #     logger, "white", "debug", "(case 4) _update_memo_amount"
                        # )
                        new_curr_memo = cls._update_memo_amount(og_curr_memo, 0.00, log_stack_depth=log_stack_depth)
                    if og_prev_amount > 0:
                        # log_in_color(
                        #     logger, "white", "debug", "(case 5) _update_memo_amount"
                        # )
                        new_prev_memo = cls._update_memo_amount(
                            og_prev_memo, adjusted_payment_amount, log_stack_depth=log_stack_depth
                        )
                # log_in_color(logger, "white", "debug", "(case 6) _update_memo_amount")
                new_interest_memo = cls._update_memo_amount(
                    og_interest_memo, interest_to_be_charged, log_stack_depth=log_stack_depth
                )

                # log_in_color(
                #     logger,
                #     "cyan",
                #     "debug",
                #     str(date_iat)
                #     + " updated check memo: "
                #     + str(og_check_memo)
                #     + " -> "
                #     + str(new_check_memo),
                #     log_stack_depth,
                # )
                # log_in_color(
                #     logger,
                #     "cyan",
                #     "debug",
                #     str(date_iat)
                #     + " updated curr memo: "
                #     + str(og_curr_memo)
                #     + " -> "
                #     + str(new_curr_memo),
                #     log_stack_depth,
                # )
                # log_in_color(
                #     logger,
                #     "cyan",
                #     "debug",
                #     str(date_iat)
                #     + " updated prev memo: "
                #     + str(og_prev_memo)
                #     + " -> "
                #     + str(new_prev_memo),
                #     log_stack_depth,
                # )

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

            cls._apply_credit_billing_state_delta_to_forecast_row(
                forecast_df=future_rows_only_df,
                row_index=f_i,
                account_set=account_set_before_p2_plus_txn,
                credit_account_name=credit_basename,
                checking_account_name=checking_account_name,
                checking_delta=checking_delta,
                current_statement_delta=curr_stmt_delta,
                previous_statement_delta=previous_stmt_delta,
                end_of_previous_cycle_delta=eopc_delta,
            )

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
    #Codex-write-doctstring-OK
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
        TODO one-line description of ForecastHandler._propagate_credit_payment_curr_only.

        TODO multi-line description of ForecastHandler._propagate_credit_payment_curr_only.
        TODO explain how ForecastHandler._propagate_credit_payment_curr_only participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        relevant_account_info_df : object
            TODO one-line description of ForecastHandler._propagate_credit_payment_curr_only.relevant_account_info_df.

        account_deltas_list : object
            TODO one-line description of ForecastHandler._propagate_credit_payment_curr_only.account_deltas_list.

        future_rows_only_df : object
            TODO one-line description of ForecastHandler._propagate_credit_payment_curr_only.future_rows_only_df.

        forecast_df : object
            TODO one-line description of ForecastHandler._propagate_credit_payment_curr_only.forecast_df.

        account_set_before_p2_plus_txn : object
            TODO one-line description of ForecastHandler._propagate_credit_payment_curr_only.account_set_before_p2_plus_txn.

        billing_dates_dict : object
            TODO one-line description of ForecastHandler._propagate_credit_payment_curr_only.billing_dates_dict.

        d : object
            TODO one-line description of ForecastHandler._propagate_credit_payment_curr_only.d.

        post_txn_row_df : object
            TODO one-line description of ForecastHandler._propagate_credit_payment_curr_only.post_txn_row_df.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._propagate_credit_payment_curr_only.log_stack_depth.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._propagate_credit_payment_curr_only.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._propagate_credit_payment_curr_only.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._propagate_credit_payment_curr_only.

        @interface-report: show
        """
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     "ENTER _propagate_credit_payment_curr_only",
        #     log_stack_depth,
        # )
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
            md_to_keep = f_row["Memo Directives"].split(";")

            cls._apply_credit_billing_state_delta_to_forecast_row(
                forecast_df=future_rows_only_df,
                row_index=f_i,
                account_set=account_set_before_p2_plus_txn,
                credit_account_name=credit_basename,
                billing_cycle_payment_delta=billing_cycle_payment_delta,
            )
            f_row = future_rows_only_df.loc[f_i]

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
                # This row starts a new billing cycle.  The propagated delta is
                # relative to each row's original value, so replace the prior
                # cycle's adjustment instead of accumulating it again.
                eopc_delta = updated_eopc - old_eopc

            elif date_iat in cc_billing_dates and previous_prev_stmt_bal != 0:
                # log_in_color(logger, 'white', 'debug', str(date_iat) + ' (Not Next) Billing Date and previous_prev_stmt_bal != 0', log_stack_depth)
                # Handle other billing dates after payment has been made

                # Parse memo directives
                md_to_keep = []
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
                        # log_in_color(
                        #     logger, "white", "debug", "(case 7) _update_memo_amount"
                        # )
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
                        # log_in_color(
                        #     logger, "white", "debug", "(case 8) _update_memo_amount"
                        # )
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
                        # log_in_color(
                        #     logger, "white", "debug", "(case 9) _update_memo_amount"
                        # )
                        new_md = cls._update_memo_amount(md, new_min_payment_amount, log_stack_depth=log_stack_depth)
                        md_to_keep.append(new_md)

                        # log_in_color(logger, 'white', 'debug',
                        #              str(date_iat) + ' new md: ' + str(md),
                        #              log_stack_depth)

                    else:
                        md_to_keep.append(md)

            cls._apply_credit_billing_state_delta_to_forecast_row(
                forecast_df=future_rows_only_df,
                row_index=f_i,
                account_set=account_set_before_p2_plus_txn,
                credit_account_name=credit_basename,
                checking_account_name=checking_account_name,
                checking_delta=checking_delta,
                current_statement_delta=curr_stmt_delta,
                previous_statement_delta=prev_stmt_delta,
                end_of_previous_cycle_delta=eopc_delta,
            )

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

        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     future_rows_only_df.to_string(),
        #     log_stack_depth,
        # )

        # log_stack_depth -= 1
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     "EXIT _propagate_credit_payment_curr_only",
        #     log_stack_depth,
        # )
        return future_rows_only_df

    # @profile
    #Codex-write-doctstring-OK
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
        TODO one-line description of ForecastHandler._propagate_credit_payment_prev_only.

        TODO multi-line description of ForecastHandler._propagate_credit_payment_prev_only.
        TODO explain how ForecastHandler._propagate_credit_payment_prev_only participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        relevant_account_info_df : object
            TODO one-line description of ForecastHandler._propagate_credit_payment_prev_only.relevant_account_info_df.

        account_deltas_list : object
            TODO one-line description of ForecastHandler._propagate_credit_payment_prev_only.account_deltas_list.

        future_rows_only_df : object
            TODO one-line description of ForecastHandler._propagate_credit_payment_prev_only.future_rows_only_df.

        forecast_df : object
            TODO one-line description of ForecastHandler._propagate_credit_payment_prev_only.forecast_df.

        account_set_before_p2_plus_txn : object
            TODO one-line description of ForecastHandler._propagate_credit_payment_prev_only.account_set_before_p2_plus_txn.

        billing_dates_dict : object
            TODO one-line description of ForecastHandler._propagate_credit_payment_prev_only.billing_dates_dict.

        d : object
            TODO one-line description of ForecastHandler._propagate_credit_payment_prev_only.d.

        post_txn_row_df : object
            TODO one-line description of ForecastHandler._propagate_credit_payment_prev_only.post_txn_row_df.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._propagate_credit_payment_prev_only.log_stack_depth.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._propagate_credit_payment_prev_only.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._propagate_credit_payment_prev_only.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._propagate_credit_payment_prev_only.

        @interface-report: show
        """
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     str(d) + " ENTER _propagate_credit_payment_prev_only",
        #     log_stack_depth,
        # )
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

        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     "relevant_account_info_df...: ",
        #     log_stack_depth,
        # )
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     relevant_account_info_df.to_string(),
        #     log_stack_depth,
        # )
        # # relevant_account_info_df
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     "previous_stmt_delta........: " + str(previous_stmt_delta),
        #     log_stack_depth,
        # )
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     "checking_delta.............: " + str(checking_delta),
        #     log_stack_depth,
        # )
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     "billing_cycle_payment_delta: " + str(billing_cycle_payment_delta),
        #     log_stack_depth,
        # )

        # Initialize previous previous statement balance
        previous_prev_stmt_bal = 0.0

        # Iterate over future forecast rows
        for f_i, f_row in future_rows_only_df.iterrows():
            date_iat = f_row["Date"]
            md_to_keep = []

            cls._apply_credit_billing_state_delta_to_forecast_row(
                forecast_df=future_rows_only_df,
                row_index=f_i,
                account_set=account_set_before_p2_plus_txn,
                credit_account_name=credit_basename,
                billing_cycle_payment_delta=billing_cycle_payment_delta,
            )
            f_row = future_rows_only_df.loc[f_i]

            if f_i == 0:
                previous_prev_stmt_bal = f_row[prev_stmt_bal_account_name]
            else:
                previous_prev_stmt_bal = future_rows_only_df.iloc[
                    f_i - 1, prev_stmt_bal_account_index
                ]
            # log_in_color(logger, 'white', 'debug', str(date_iat)+' previous_prev_stmt_bal: ' + str(previous_prev_stmt_bal), log_stack_depth)

            if date_iat == next_billing_date:
                # log_in_color(
                #     logger,
                #     "white",
                #     "debug",
                #     str(date_iat) + " Next Billing Date",
                #     log_stack_depth,
                # )
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
                # log_in_color(
                #     logger,
                #     "white",
                #     "debug",
                #     "advance_payment_amount: " + str(advance_payment_amount),
                #     log_stack_depth,
                # )

                # Get minimum payment amount
                og_min_payment_amount = cls._parse_memo_amount(og_check_memo, log_stack_depth=log_stack_depth)
                # log_in_color(
                #     logger,
                #     "white",
                #     "debug",
                #     "og_min_payment_amount: " + str(og_min_payment_amount),
                #     log_stack_depth,
                # )

                # Adjust deltas
                payment_to_apply = min(og_min_payment_amount, advance_payment_amount)
                # log_in_color(
                #     logger,
                #     "white",
                #     "debug",
                #     "payment_to_apply: " + str(og_min_payment_amount),
                #     log_stack_depth,
                # )

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
                    # log_in_color(
                    #     logger, "white", "debug", "(case 12) _update_memo_amount"
                    # )
                    new_check_memo = cls._update_memo_amount(
                        og_check_memo, remaining_payment, log_stack_depth=log_stack_depth
                    )
                    # log_in_color(
                    #     logger, "white", "debug", "(case 13) _update_memo_amount"
                    # )
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
                # This row starts a new billing cycle.  The propagated delta is
                # relative to each row's original value, so replace the prior
                # cycle's adjustment instead of accumulating it again.
                eopc_delta = updated_eopc - old_eopc

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
                        # log_in_color(
                        #     logger, "white", "debug", "(case 14) _update_memo_amount"
                        # )
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
                        # log_in_color(
                        #     logger, "white", "debug", "(case 15) _update_memo_amount"
                        # )
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
                        # log_in_color(
                        #     logger, "white", "debug", "(case 16) _update_memo_amount"
                        # )
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

            cls._apply_credit_billing_state_delta_to_forecast_row(
                forecast_df=future_rows_only_df,
                row_index=f_i,
                account_set=account_set_before_p2_plus_txn,
                credit_account_name=credit_basename,
                checking_account_name=checking_account_name,
                checking_delta=checking_delta,
                previous_statement_delta=previous_stmt_delta,
                end_of_previous_cycle_delta=eopc_delta,
            )

            # log_in_color(logger, 'cyan', 'debug', str(date_iat) + ' ' + checking_account_name + ' = ' + str(future_rows_only_df.at[f_i, checking_account_name]), log_stack_depth)
            # log_in_color(logger, 'cyan', 'debug', str(date_iat) + ' ' + prev_stmt_bal_account_name + ' = ' + str(future_rows_only_df.at[f_i, prev_stmt_bal_account_name]), log_stack_depth)

            # else no change is needed?
            if md_to_keep != []:
                # Clean and update memo directives
                md_to_keep = [" " + md for md in md_to_keep if md]
                future_rows_only_df.at[f_i, "Memo Directives"] = ";".join(
                    md_to_keep
                ).strip()

        # log_in_color(
        #     logger, "white", "debug", "future_rows_only_df:", log_stack_depth
        # )
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     future_rows_only_df.to_string(),
        #     log_stack_depth,
        # )
        # log_stack_depth -= 1
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     str(d) + " EXIT _propagate_credit_payment_prev_only",
        #     log_stack_depth,
        # )
        return future_rows_only_df

    # @profile
    #Codex-write-doctstring-OK
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
        TODO one-line description of ForecastHandler._propagate_loan_payment_interest_only.

        TODO multi-line description of ForecastHandler._propagate_loan_payment_interest_only.
        TODO explain how ForecastHandler._propagate_loan_payment_interest_only participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        relevant_account_info_df : object
            TODO one-line description of ForecastHandler._propagate_loan_payment_interest_only.relevant_account_info_df.

        account_deltas_list : object
            TODO one-line description of ForecastHandler._propagate_loan_payment_interest_only.account_deltas_list.

        future_rows_only_df : object
            TODO one-line description of ForecastHandler._propagate_loan_payment_interest_only.future_rows_only_df.

        forecast_df : object
            TODO one-line description of ForecastHandler._propagate_loan_payment_interest_only.forecast_df.

        account_set_before_p2_plus_txn : object
            TODO one-line description of ForecastHandler._propagate_loan_payment_interest_only.account_set_before_p2_plus_txn.

        billing_dates_dict : object
            TODO one-line description of ForecastHandler._propagate_loan_payment_interest_only.billing_dates_dict.

        date_string : object
            TODO one-line description of ForecastHandler._propagate_loan_payment_interest_only.date_string.

        post_txn_row_df : object
            TODO one-line description of ForecastHandler._propagate_loan_payment_interest_only.post_txn_row_df.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._propagate_loan_payment_interest_only.log_stack_depth.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._propagate_loan_payment_interest_only.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._propagate_loan_payment_interest_only.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._propagate_loan_payment_interest_only.

        @interface-report: show
        """
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     "ENTER _propagate_loan_payment_interest_only",
        #     log_stack_depth,
        # )
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
        loan_account_name = interest_account_name.split(":")[0]
        # Construct the principal balance account name based on the interest account name
        pbal_account_name = loan_account_name + ": Principal Balance"
        billing_cycle_payment_balance_account_name = (
            loan_account_name + ": Loan Billing Cycle Payment Bal"
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
                    # log_in_color(
                    #     logger, "white", "debug", "(case 17) _update_memo_amount"
                    # )
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

            interest_delta_to_apply = 0
            if int(date_iat) >= int(min(loan_billing_dates)):
                if f_i == 0:
                    base_interest_balance = post_txn_row_df.head(1)[
                        interest_account_name
                    ].iat[0]
                else:
                    base_interest_balance = (
                        future_rows_only_df.at[f_i - 1, interest_account_name]
                    )

                pbal_balance = future_rows_only_df.at[f_i, pbal_account_name]
                interest_accrued = pbal_balance * (apr / 365.25)
                target_interest_balance = base_interest_balance + interest_accrued
                interest_delta_to_apply = (
                    target_interest_balance
                    - future_rows_only_df.at[f_i, interest_account_name]
                )

                interest_delta = 0.0  # Reset interest delta to prevent accumulation

            cls._apply_loan_billing_state_delta_to_forecast_row(
                forecast_df=future_rows_only_df,
                row_index=f_i,
                account_set=account_set_before_p2_plus_txn,
                loan_account_name=loan_account_name,
                checking_account_name=checking_account_name,
                checking_delta=checking_delta,
                interest_delta=interest_delta_to_apply,
                billing_cycle_payment_delta=billing_cycle_payment_delta,
            )

            # Clean and update memo directives
            md_to_keep = [md for md in md_to_keep if md]
            future_rows_only_df.at[f_i, "Memo Directives"] = ";".join(md_to_keep)

        # log_in_color(logger, 'cyan', 'debug', 'future_rows_only_df', log_stack_depth)
        # log_in_color(logger, 'cyan', 'debug', future_rows_only_df.to_string(), log_stack_depth)
        log_stack_depth -= 1
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     "EXIT _propagate_loan_payment_interest_only",
        #     log_stack_depth,
        # )
        return future_rows_only_df

    # @profile
    #Codex-write-doctstring-OK
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
        TODO one-line description of ForecastHandler._propagate_loan_payment_pbal_only.

        TODO multi-line description of ForecastHandler._propagate_loan_payment_pbal_only.
        TODO explain how ForecastHandler._propagate_loan_payment_pbal_only participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        relevant_account_info_df : object
            TODO one-line description of ForecastHandler._propagate_loan_payment_pbal_only.relevant_account_info_df.

        account_deltas_list : object
            TODO one-line description of ForecastHandler._propagate_loan_payment_pbal_only.account_deltas_list.

        future_rows_only_df : object
            TODO one-line description of ForecastHandler._propagate_loan_payment_pbal_only.future_rows_only_df.

        forecast_df : object
            TODO one-line description of ForecastHandler._propagate_loan_payment_pbal_only.forecast_df.

        account_set_before_p2_plus_txn : object
            TODO one-line description of ForecastHandler._propagate_loan_payment_pbal_only.account_set_before_p2_plus_txn.

        billing_dates_dict : object
            TODO one-line description of ForecastHandler._propagate_loan_payment_pbal_only.billing_dates_dict.

        date_string : object
            TODO one-line description of ForecastHandler._propagate_loan_payment_pbal_only.date_string.

        post_txn_row_df : object
            TODO one-line description of ForecastHandler._propagate_loan_payment_pbal_only.post_txn_row_df.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._propagate_loan_payment_pbal_only.log_stack_depth.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._propagate_loan_payment_pbal_only.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._propagate_loan_payment_pbal_only.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._propagate_loan_payment_pbal_only.

        @interface-report: show
        """
        # log_in_color(
        #     logger,
        #     "cyan",
        #     "debug",
        #     "ENTER _propagate_loan_payment_pbal_only",
        #     log_stack_depth,
        # )
        log_stack_depth += 1

        # Extract relevant account names
        checking_account_name = relevant_account_info_df[
            relevant_account_info_df.Account_Type == "checking"
        ].Name.iat[0]
        pbal_account_name = relevant_account_info_df[
            relevant_account_info_df.Account_Type == "principal balance"
        ].Name.iat[0]
        loan_account_name = pbal_account_name.split(":")[0]
        # Construct the interest account name based on the principal balance account name
        interest_account_name = loan_account_name + ": Interest"
        billing_cycle_payment_account_name = (
            loan_account_name + ": Loan Billing Cycle Payment Bal"
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

            interest_delta_to_apply = 0
            if int(date_iat) >= int(min(loan_billing_dates)):
                principal_balance_after_delta = (
                    future_rows_only_df.at[f_i, pbal_account_name] + pbal_delta
                )
                if f_i == 0:
                    base_interest_balance = post_txn_row_df.at[
                        0, interest_account_name
                    ]
                else:
                    base_interest_balance = (
                        future_rows_only_df.at[f_i - 1, interest_account_name]
                    )

                interest_accrued = principal_balance_after_delta * (apr / 365.25)
                target_interest_balance = base_interest_balance + interest_accrued
                interest_delta_to_apply = (
                    target_interest_balance
                    - future_rows_only_df.at[f_i, interest_account_name]
                )

            cls._apply_loan_billing_state_delta_to_forecast_row(
                forecast_df=future_rows_only_df,
                row_index=f_i,
                account_set=account_set_before_p2_plus_txn,
                loan_account_name=loan_account_name,
                checking_account_name=checking_account_name,
                checking_delta=checking_delta,
                principal_delta=pbal_delta,
                interest_delta=interest_delta_to_apply,
                billing_cycle_payment_delta=billing_cycle_payment_delta,
            )

            # Clean and update memo directives
            md_to_keep = [md for md in md_to_keep if md]
            future_rows_only_df.at[f_i, "Memo Directives"] = ";".join(md_to_keep)

        log_stack_depth -= 1
        # log_in_color(
        #     logger,
        #     "cyan",
        #     "debug",
        #     "EXIT _propagate_loan_payment_pbal_only",
        #     log_stack_depth,
        # )
        return future_rows_only_df

    # @profile
    #Codex-write-doctstring-OK
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
        TODO one-line description of ForecastHandler._propagate_loan_payment_pbal_interest.

        TODO multi-line description of ForecastHandler._propagate_loan_payment_pbal_interest.
        TODO explain how ForecastHandler._propagate_loan_payment_pbal_interest participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        relevant_account_info_df : object
            TODO one-line description of ForecastHandler._propagate_loan_payment_pbal_interest.relevant_account_info_df.

        account_deltas_list : object
            TODO one-line description of ForecastHandler._propagate_loan_payment_pbal_interest.account_deltas_list.

        future_rows_only_df : object
            TODO one-line description of ForecastHandler._propagate_loan_payment_pbal_interest.future_rows_only_df.

        forecast_df : object
            TODO one-line description of ForecastHandler._propagate_loan_payment_pbal_interest.forecast_df.

        account_set_before_p2_plus_txn : object
            TODO one-line description of ForecastHandler._propagate_loan_payment_pbal_interest.account_set_before_p2_plus_txn.

        billing_dates_dict : object
            TODO one-line description of ForecastHandler._propagate_loan_payment_pbal_interest.billing_dates_dict.

        date_string : object
            TODO one-line description of ForecastHandler._propagate_loan_payment_pbal_interest.date_string.

        post_txn_row_df : object
            TODO one-line description of ForecastHandler._propagate_loan_payment_pbal_interest.post_txn_row_df.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._propagate_loan_payment_pbal_interest.log_stack_depth.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._propagate_loan_payment_pbal_interest.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._propagate_loan_payment_pbal_interest.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._propagate_loan_payment_pbal_interest.

        @interface-report: show
        """
        # log_in_color(
        #     logger,
        #     "cyan",
        #     "debug",
        #     "ENTER _propagate_loan_payment_pbal_interest",
        #     log_stack_depth,
        # )
        log_stack_depth += 1

        # log_in_color(
        #     logger, "white", "debug", "future_rows_only_df:", log_stack_depth
        # )
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     future_rows_only_df.to_string(),
        #     log_stack_depth,
        # )

        # Extract relevant account names
        checking_account_name = relevant_account_info_df[
            relevant_account_info_df.Account_Type == "checking"
        ].Name.iat[0]
        pbal_account_name = relevant_account_info_df[
            relevant_account_info_df.Account_Type == "principal balance"
        ].Name.iat[0]
        loan_account_name = pbal_account_name.split(":")[0]
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
                # log_in_color(logger, "white", "debug", "(case 18) _update_memo_amount")
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

            interest_delta_to_apply = 0
            if date_iat >= min(loan_billing_dates):
                principal_balance_after_delta = (
                    future_rows_only_df.at[f_i, pbal_account_name] + pbal_delta
                )
                if f_i == 0:
                    base_interest_balance = post_txn_row_df.head(1)[
                        interest_account_name
                    ].iat[0]
                else:
                    base_interest_balance = (
                        future_rows_only_df.at[f_i - 1, interest_account_name]
                    )

                interest_accrued = principal_balance_after_delta * (apr / 365.25)
                target_interest_balance = base_interest_balance + interest_accrued
                interest_delta_to_apply = (
                    target_interest_balance
                    - future_rows_only_df.at[f_i, interest_account_name]
                )
                interest_delta = 0.0  # Reset interest delta to prevent accumulation

            cls._apply_loan_billing_state_delta_to_forecast_row(
                forecast_df=future_rows_only_df,
                row_index=f_i,
                account_set=account_set_before_p2_plus_txn,
                loan_account_name=loan_account_name,
                checking_account_name=checking_account_name,
                checking_delta=checking_delta,
                principal_delta=pbal_delta,
                interest_delta=interest_delta_to_apply,
                billing_cycle_payment_delta=billing_cycle_payment_delta,
            )

            # Clean and update memo directives
            md_to_keep = [md for md in md_to_keep if md]
            future_rows_only_df.at[f_i, "Memo Directives"] = ";".join(md_to_keep)

        # log_in_color(
        #     logger, "white", "debug", "future_rows_only_df:", log_stack_depth
        # )
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     future_rows_only_df.to_string(),
        #     log_stack_depth,
        # )
        log_stack_depth -= 1
        # log_in_color(
        #     logger,
        #     "cyan",
        #     "debug",
        #     "EXIT _propagate_loan_payment_pbal_interest",
        #     log_stack_depth,
        # )
        return future_rows_only_df

    # @profile
    #Codex-write-doctstring-OK
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
        TODO one-line description of ForecastHandler._propagate_credit_payment_prev_curr.

        TODO multi-line description of ForecastHandler._propagate_credit_payment_prev_curr.
        TODO explain how ForecastHandler._propagate_credit_payment_prev_curr participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        relevant_account_info_df : object
            TODO one-line description of ForecastHandler._propagate_credit_payment_prev_curr.relevant_account_info_df.

        account_deltas_list : object
            TODO one-line description of ForecastHandler._propagate_credit_payment_prev_curr.account_deltas_list.

        future_rows_only_df : object
            TODO one-line description of ForecastHandler._propagate_credit_payment_prev_curr.future_rows_only_df.

        forecast_df : object
            TODO one-line description of ForecastHandler._propagate_credit_payment_prev_curr.forecast_df.

        account_set_before_p2_plus_txn : object
            TODO one-line description of ForecastHandler._propagate_credit_payment_prev_curr.account_set_before_p2_plus_txn.

        billing_dates_dict : object
            TODO one-line description of ForecastHandler._propagate_credit_payment_prev_curr.billing_dates_dict.

        d : object
            TODO one-line description of ForecastHandler._propagate_credit_payment_prev_curr.d.

        post_txn_row_df : object
            TODO one-line description of ForecastHandler._propagate_credit_payment_prev_curr.post_txn_row_df.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._propagate_credit_payment_prev_curr.log_stack_depth.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._propagate_credit_payment_prev_curr.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._propagate_credit_payment_prev_curr.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._propagate_credit_payment_prev_curr.

        @interface-report: show
        """
        # log_in_color(
        #     logger,
        #     "cyan",
        #     "debug",
        #     "ENTER _propagate_credit_payment_prev_curr",
        #     log_stack_depth,
        # )
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
            (d + datetime.timedelta(days=1)).strftime("%Y%m%d")
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

            cls._apply_credit_billing_state_delta_to_forecast_row(
                forecast_df=future_rows_only_df,
                row_index=f_i,
                account_set=account_set_before_p2_plus_txn,
                credit_account_name=credit_basename,
                billing_cycle_payment_delta=billing_cycle_payment_delta,
            )
            f_row = future_rows_only_df.loc[f_i]

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
                # log_in_color(
                #     logger,
                #     "cyan",
                #     "debug",
                #     "Memo Directives: " + str(f_row["Memo Directives"]),
                #     log_stack_depth,
                # )
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
                        # log_in_color(
                        #     logger, "white", "debug", "(case 19) _update_memo_amount"
                        # )
                        new_prev_memo = cls._update_memo_amount(
                            og_prev_memo, 0.00, log_stack_depth=log_stack_depth
                        )  # todo this is where the error occurred
                        curr_amount_remaining = og_curr_amount - (
                            advance_payment_amount - og_prev_amount
                        )
                        if og_curr_amount > 0:
                            # log_in_color(
                            #     logger,
                            #     "white",
                            #     "debug",
                            #     "(case 20) _update_memo_amount",
                            # )
                            new_curr_memo = cls._update_memo_amount(
                                og_curr_memo, curr_amount_remaining, log_stack_depth=log_stack_depth
                            )
                    else:
                        # Advance payments partially cover previous statement balance and none of curr (which there might not be any)
                        prev_amount_remaining = og_prev_amount - advance_payment_amount
                        # log_in_color(
                        #     logger, "white", "debug", "(case 21) _update_memo_amount"
                        # )
                        new_prev_memo = cls._update_memo_amount(
                            og_prev_memo, prev_amount_remaining, log_stack_depth=log_stack_depth
                        )
                        new_curr_memo = og_curr_memo
                    # log_in_color(
                    #     logger, "white", "debug", "(case 22) _update_memo_amount"
                    # )
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
                print("eopc_delta = " + str(updated_eopc - old_eopc))
                # This row starts a new billing cycle.  The propagated delta is
                # relative to each row's original value, so replace the prior
                # cycle's adjustment instead of accumulating it again.
                eopc_delta = updated_eopc - old_eopc

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
                # log_in_color(
                #     logger,
                #     "cyan",
                #     "debug",
                #     str(date_iat)
                #     + " adjusted_payment_amount: "
                #     + str(adjusted_payment_amount),
                #     log_stack_depth,
                # )

                previous_stmt_delta += adjusted_payment_amount
                checking_delta += adjusted_payment_amount
                interest_delta = interest_to_be_charged - og_interest_amount
                # previous_stmt_delta += round(interest_delta, 2)
                previous_stmt_delta += interest_delta
                billing_cycle_payment_delta = 0  # redundant but cant hurt

                # Adjust memos
                # log_in_color(logger, "white", "debug", "(case 23) _update_memo_amount")
                new_check_memo = cls._update_memo_amount(
                    og_check_memo, og_check_amount - adjusted_payment_amount, log_stack_depth=log_stack_depth
                )
                if adjusted_payment_amount >= curr_prev_stmt_bal:
                    # Adjust curr and prev memos
                    if og_curr_amount > 0:
                        # log_in_color(
                        #     logger, "white", "debug", "(case 24) _update_memo_amount"
                        # )
                        new_curr_memo = cls._update_memo_amount(
                            og_curr_memo, adjusted_payment_amount - curr_prev_stmt_bal, log_stack_depth=log_stack_depth
                        )
                    if og_prev_amount > 0:
                        # log_in_color(
                        #     logger, "white", "debug", "(case 25) _update_memo_amount"
                        # )
                        new_prev_memo = cls._update_memo_amount(
                            og_prev_memo, curr_prev_stmt_bal, log_stack_depth=log_stack_depth
                        )
                else:
                    if og_curr_amount > 0:
                        # this parent logic branch is for cc payments, not cc expenses, therefore
                        # this specific branch should never happen bc adjust payment amount is always less than OG.
                        # if adjusted_payment_amount > curr_prev_stmt_bal, then so was OG, and therefore curr was 0
                        # log_in_color(
                        #     logger, "white", "debug", "(case 26) _update_memo_amount"
                        # )
                        new_curr_memo = cls._update_memo_amount(og_curr_memo, 0.00, log_stack_depth=log_stack_depth)
                    if og_prev_amount > 0:
                        # log_in_color(
                        #     logger, "white", "debug", "(case 27) _update_memo_amount"
                        # )
                        new_prev_memo = cls._update_memo_amount(
                            og_prev_memo, og_prev_amount - adjusted_payment_amount, log_stack_depth=log_stack_depth
                        )
                # log_in_color(logger, "white", "debug", "(case 28) _update_memo_amount")
                new_interest_memo = cls._update_memo_amount(
                    og_interest_memo, interest_to_be_charged, log_stack_depth=log_stack_depth
                )

                # log_in_color(
                #     logger,
                #     "cyan",
                #     "debug",
                #     str(date_iat)
                #     + " updated check memo: "
                #     + str(og_check_memo)
                #     + " -> "
                #     + str(new_check_memo),
                #     log_stack_depth,
                # )
                # log_in_color(
                #     logger,
                #     "cyan",
                #     "debug",
                #     str(date_iat)
                #     + " updated curr memo: "
                #     + str(og_curr_memo)
                #     + " -> "
                #     + str(new_curr_memo),
                #     log_stack_depth,
                # )
                # log_in_color(
                #     logger,
                #     "cyan",
                #     "debug",
                #     str(date_iat)
                #     + " updated prev memo: "
                #     + str(og_prev_memo)
                #     + " -> "
                #     + str(new_prev_memo),
                #     log_stack_depth,
                # )

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

            cls._apply_credit_billing_state_delta_to_forecast_row(
                forecast_df=future_rows_only_df,
                row_index=f_i,
                account_set=account_set_before_p2_plus_txn,
                credit_account_name=credit_basename,
                checking_account_name=checking_account_name,
                checking_delta=checking_delta,
                current_statement_delta=curr_stmt_delta,
                previous_statement_delta=previous_stmt_delta,
                end_of_previous_cycle_delta=eopc_delta,
            )

            # future_rows_only_df.at[f_i, checking_account_name] = round(future_rows_only_df.at[f_i, checking_account_name],2)
            # future_rows_only_df.at[f_i, prev_stmt_bal_account_name] = round(future_rows_only_df.at[f_i, prev_stmt_bal_account_name],2)
            # future_rows_only_df.at[f_i, curr_stmt_bal_account_name] = round(future_rows_only_df.at[f_i, curr_stmt_bal_account_name],2)
            # future_rows_only_df.at[f_i, billing_cycle_payment_account_name] = round(future_rows_only_df.at[f_i, billing_cycle_payment_account_name],2)
            # future_rows_only_df.at[f_i, eopc_account_name] = round( future_rows_only_df.at[f_i, eopc_account_name], 2)

            # log_in_color(logger, 'white', 'debug', str(date_iat) + ' ' + str(checking_account_name) + ' += ' + str(checking_delta), log_stack_depth)
            # log_in_color(logger, 'white', 'debug', str(date_iat) + ' ' + str(curr_stmt_bal_account_name) + ' += ' + str(curr_stmt_delta), log_stack_depth)
            # log_in_color(logger, 'white', 'debug', str(date_iat) + ' ' + str(prev_stmt_bal_account_name) + ' += ' + str(previous_stmt_delta), log_stack_depth)
            # log_in_color(logger, 'white', 'debug', str(date_iat) + ' ' + str(billing_cycle_payment_account_name) + ' += ' + str(billing_cycle_payment_delta), log_stack_depth)
            # log_in_color(
            #     logger,
            #     "white",
            #     "debug",
            #     str(date_iat) + " " + str(eopc_account_name) + " += " + str(eopc_delta),
            #     log_stack_depth,
            # )

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
        #     "cyan",
        #     "debug",
        #     "EXIT _propagate_credit_payment_prev_curr",
        #     log_stack_depth,
        # )
        return future_rows_only_df

    # @profile
    #Codex-write-doctstring-OK
    @classmethod
    def _parse_memo_amount(cls, memo_line, log_stack_depth):
        """
        TODO one-line description of ForecastHandler._parse_memo_amount.

        TODO multi-line description of ForecastHandler._parse_memo_amount.
        TODO explain how ForecastHandler._parse_memo_amount participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        memo_line : object
            TODO one-line description of ForecastHandler._parse_memo_amount.memo_line.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._parse_memo_amount.log_stack_depth.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._parse_memo_amount.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._parse_memo_amount.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._parse_memo_amount.

        @interface-report: show
        """
        log_stack_depth += 1

        matches = re.search(r"(.*) \((.*)[-+]{1}\$(.*)\)", memo_line)
        if matches is None:
            raise ValueError(f"Malformed memo line: {memo_line}")

        memo_amount = matches.group(3)

        log_stack_depth -= 1
        return float(memo_amount)

    # @profile
    #Codex-write-doctstring-OK
    @classmethod
    def _update_memo_amount(cls, memo_line, new_amount, log_stack_depth):
        # log_in_color(
        #     logger, "white", "debug", " ENTER _update_memo_amount", log_stack_depth
        # )
        """
        TODO one-line description of ForecastHandler._update_memo_amount.

        TODO multi-line description of ForecastHandler._update_memo_amount.
        TODO explain how ForecastHandler._update_memo_amount participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        memo_line : object
            TODO one-line description of ForecastHandler._update_memo_amount.memo_line.

        new_amount : object
            TODO one-line description of ForecastHandler._update_memo_amount.new_amount.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._update_memo_amount.log_stack_depth.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._update_memo_amount.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._update_memo_amount.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._update_memo_amount.

        @interface-report: show
        """
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
    #TODO manual review of ForecastHandler._propagateOptimizationTransactionsIntoTheFuture docstring
    @classmethod
    def _propagateOptimizationTransactionsIntoTheFuture(
        cls, end_date, account_set_before_p2_plus_txn, forecast_df, date_string, log_stack_depth, include_debug_columns=False #TODO unsure if include_debug_columns belongs here
    ):
        """
        TODO one-line description of ForecastHandler._propagateOptimizationTransactionsIntoTheFuture.

        TODO multi-line description of ForecastHandler._propagateOptimizationTransactionsIntoTheFuture.
        TODO explain how ForecastHandler._propagateOptimizationTransactionsIntoTheFuture participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        end_date : date
            TODO one-line description of ForecastHandler._propagateOptimizationTransactionsIntoTheFuture.end_date.

        account_set_before_p2_plus_txn : object
            TODO one-line description of ForecastHandler._propagateOptimizationTransactionsIntoTheFuture.account_set_before_p2_plus_txn.

        forecast_df : object
            TODO one-line description of ForecastHandler._propagateOptimizationTransactionsIntoTheFuture.forecast_df.

        date_string : object
            TODO one-line description of ForecastHandler._propagateOptimizationTransactionsIntoTheFuture.date_string.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._propagateOptimizationTransactionsIntoTheFuture.log_stack_depth.

        include_debug_columns : bool
            TODO one-line description of ForecastHandler._propagateOptimizationTransactionsIntoTheFuture.include_debug_columns.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._propagateOptimizationTransactionsIntoTheFuture.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._propagateOptimizationTransactionsIntoTheFuture.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._propagateOptimizationTransactionsIntoTheFuture.

        @interface-report: show
        """
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     str(date_string)
        #     + " ENTER _propagateOptimizationTransactionsIntoTheFuture",
        #     log_stack_depth,
        # )
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
            log_in_color( #TODO is log error message redundant if an exception is raised immediately after?
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
            # log_in_color(
            #     logger,
            #     "white",
            #     "debug",
            #     str(date_string) + " no changes to propagate",
            #     log_stack_depth,
            # )
            log_stack_depth -= 1
        #     log_in_color(
        #         logger,
        #         "white",
        #         "debug",
        #         str(date_string)
        #         + " EXIT _propagateOptimizationTransactionsIntoTheFuture",
        #         log_stack_depth,
        #     )
        #     return forecast_df

        # log_in_color(logger, "cyan", "debug", "forecast_df:", log_stack_depth)
        # log_in_color(
        #     logger, "cyan", "debug", forecast_df.to_string(), log_stack_depth
        # )

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
            interest_interval = a_row["Interest_interval"]
            if pd.isnull(interest_interval) or interest_interval == "None":
                interest_accrual_dates__list_of_lists.append([])
                continue

            start_date = a_row["Billing_Start_Date"]
            end_date = end_date
            num_days = (end_date - start_date).days
            account_specific_iad = generate_date_sequence(
                a_row["Billing_Start_Date"], num_days, interest_interval
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
                        "Interest_interval": base_row["Interest_interval"],
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

            # log_in_color(
            #     logger,
            #     "yellow",
            #     "debug",
            #     str(date_string)
            #     + " before processing_function (checking case)",
            #     log_stack_depth,
            # )
            # log_in_color(
            #     logger, "yellow", "debug", forecast_df.to_string(), log_stack_depth
            # )

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

                # log_in_color(
                #     logger,
                #     "cyan",
                #     "info",
                #     str(date_string)
                #     + " processing_function "
                #     + str(processing_function),
                #     log_stack_depth,
                # )

                # print('account_types_set:')
                # print(account_types_set)

                if processing_function:

                    # log_in_color(
                    #     logger,
                    #     "yellow",
                    #     "debug",
                    #     str(date_string)
                    #     + " future_rows_only_df before processing_function",
                    #     log_stack_depth,
                    # )
                    # log_in_color(
                    #     logger,
                    #     "yellow",
                    #     "debug",
                    #     future_rows_only_df.to_string(),
                    #     log_stack_depth,
                    # )

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
                    # log_in_color(
                    #     logger,
                    #     "white",
                    #     "debug",
                    #     str(date_string)
                    #     + " EXIT _propagateOptimizationTransactionsIntoTheFuture",
                    #     log_stack_depth,
                    # )
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
                    # log_in_color(
                    #     logger,
                    #     "white",
                    #     "debug",
                    #     str(date_string)
                    #     + " EXIT _propagateOptimizationTransactionsIntoTheFuture",
                    #     log_stack_depth,
                    # )
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
                    # log_in_color(
                    #     logger,
                    #     "white",
                    #     "debug",
                    #     str(date_string)
                    #     + " EXIT _propagateOptimizationTransactionsIntoTheFuture",
                    #     log_stack_depth,
                    # )
                    raise ValueError(error_msg)

            # If an error occurs here, it is because of systemic error in the algroithm
            # Not a valid rejection of a transactions
            # also check for rounding that caused real deltas to mismatch the memos!!!!
            for f_i, f_row in future_rows_only_df.iterrows():
                # log_in_color(
                #     logger, "white", "debug", "Date:" + str(f_row.Date), log_stack_depth
                # )
                # we don't use index bc it won't be 1 and reindexing is expensive
                current_row = f_row
                current_date_string = f_row.Date
                first_row_date_string = future_rows_only_df.head(1).Date.iat[0]
                if current_date_string == first_row_date_string:
                    previous_row = forecast_df[forecast_df.Date == date_string]
                else:
                    previous_row = future_rows_only_df.loc[f_i - 1, :]

                # log_in_color(
                #     logger, "white", "debug", "previous_row:", log_stack_depth
                # )
                # if str(type(previous_row)) == "<class 'pandas.core.frame.DataFrame'>":
                #     log_in_color(
                #         logger,
                #         "white",
                #         "debug",
                #         previous_row.to_string(),
                #         log_stack_depth,
                #     )
                # else:
                #     # type is pandas.core.series.Series
                #     log_in_color(
                #         logger,
                #         "white",
                #         "debug",
                #         pd.DataFrame(previous_row).T.to_string(),
                #         log_stack_depth,
                #     )

                # log_in_color(
                #     logger, "white", "debug", "current_row:", log_stack_depth
                # )
                # if str(type(current_row)) == "<class 'pandas.core.frame.DataFrame'>":
                #     log_in_color(
                #         logger,
                #         "white",
                #         "debug",
                #         current_row.to_string(),
                #         log_stack_depth,
                #     )
                # else:
                #     # type is pandas.core.series.Series
                #     log_in_color(
                #         logger,
                #         "white",
                #         "debug",
                #         pd.DataFrame(current_row).T.to_string(),
                #         log_stack_depth,
                #     )

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

                    # log_in_color(
                    #     logger, "white", "debug", "md:" + str(md), log_stack_depth
                    # )

                    txn_info = re.search(r"\((.*)\$(.*)\)", md)
                    if txn_info is None:
                        raise ValueError(f"Malformed memo directive: {md}")

                    acct_name = txn_info.group(1).split(":")[0]
                    acct_name = acct_name.replace("-", "").replace("+", "").strip()
                    acct_type = account_type_by_base_name.get(acct_name)
                    memo_balance = float(txn_info.group(2))

                    if acct_name not in reported_acct_deltas:
                        if "Loan" in acct_name:
                            continue
                        if "-$" in md:
                            memo_balance = -abs(memo_balance)
                        elif "+$" in md:
                            memo_balance = abs(memo_balance)
                        if acct_type in ("credit", "loan"):
                            memo_balance *= -1

                        reported_acct_deltas[acct_name] = memo_balance

                        # log_in_color(
                        #     logger,
                        #     "white",
                        #     "debug",
                        #     "reported_acct_deltas["
                        #     + str(acct_name)
                        #     + "] = "
                        #     + str(memo_balance),
                        #     log_stack_depth,
                        # )
                    else:
                        if "-$" in md:
                            memo_balance = -abs(memo_balance)
                        elif "+$" in md:
                            memo_balance = abs(memo_balance)
                        if acct_type in ("credit", "loan"):
                            memo_balance *= -1

                        reported_acct_deltas[acct_name] += memo_balance

                        # log_in_color(
                        #     logger,
                        #     "white",
                        #     "debug",
                        #     "reported_acct_deltas["
                        #     + str(acct_name)
                        #     + "] += "
                        #     + str(memo_balance)
                        #     + " = "
                        #     + str(reported_acct_deltas[acct_name]),
                        #     log_stack_depth,
                        # )

                for m in f_row["Memo"].split(";"):
                    if "income" in m.lower() or m.strip() == "":
                        # bc otherwise would be double counted. this is a known design weakness
                        # don't bully me i'll cum
                        continue

                    # log_in_color(
                    #     logger, "white", "debug", "m:" + str(m), log_stack_depth
                    # )

                    txn_info = re.search(r"\((.*).*\$(.*)\)", m)
                    if txn_info is None:
                        raise ValueError(f"Malformed memo: {m}")

                    acct_name = txn_info.group(1)
                    acct_name = acct_name.replace("-", "").replace("+", "").strip()
                    memo_balance = float(txn_info.group(2))

                    if acct_name not in reported_acct_deltas:
                        if "Loan" in acct_name:
                            continue
                        if "-$" in m:
                            memo_balance = -abs(memo_balance)
                        else:
                            memo_balance = abs(memo_balance)

                        reported_acct_deltas[acct_name] = memo_balance

                        # log_in_color(
                        #     logger,
                        #     "white",
                        #     "debug",
                        #     "reported_acct_deltas["
                        #     + str(acct_name)
                        #     + "] = "
                        #     + str(memo_balance),
                        #     log_stack_depth,
                        # )
                    else:
                        if "-$" in m:
                            memo_balance = -abs(memo_balance)
                        else:
                            memo_balance = abs(memo_balance)

                        reported_acct_deltas[acct_name] += memo_balance

                        # log_in_color(
                        #     logger,
                        #     "white",
                        #     "debug",
                        #     "reported_acct_deltas["
                        #     + str(acct_name)
                        #     + "] += "
                        #     + str(memo_balance)
                        #     + " = "
                        #     + str(reported_acct_deltas[acct_name]),
                        #     log_stack_depth,
                        # )

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
                    current_value = current_row[full_cname]
                    previous_value = previous_row[full_cname]
                    if isinstance(current_value, pd.Series):
                        current_value = current_value.iloc[0]
                    if isinstance(previous_value, pd.Series):
                        previous_value = previous_value.iloc[0]
                    current_delta = float(current_value) - float(previous_value)
                    if base_account_type in ("credit", "loan"):
                        current_delta *= -1
                    if cname not in observed_acct_deltas.keys():
                        if abs(current_delta) > ROUNDING_ERROR_TOLERANCE:
                            observed_acct_deltas[cname] = current_delta
                            # log_in_color(
                            #     logger,
                            #     "white",
                            #     "debug",
                            #     "observed_acct_deltas["
                            #     + str(cname)
                            #     + "] = "
                            #     + str(current_delta),
                            #     log_stack_depth,
                            # )
                    else:
                        if abs(current_delta) > ROUNDING_ERROR_TOLERANCE:
                            observed_acct_deltas[cname] += current_delta
                            # log_in_color(
                            #     logger,
                            #     "white",
                            #     "debug",
                            #     "observed_acct_deltas["
                            #     + str(cname)
                            #     + "] += "
                            #     + str(current_delta)
                            #     + " = "
                            #     + str(observed_acct_deltas[cname]),
                            #     log_stack_depth,
                            # )

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
                    # log_in_color(
                    #     logger,
                    #     "white",
                    #     "debug",
                    #     "reported_acct_deltas.keys(): "
                    #     + str(reported_acct_deltas.keys()),
                    #     log_stack_depth,
                    # )
                    # log_in_color(
                    #     logger,
                    #     "white",
                    #     "debug",
                    #     "observed_acct_deltas.keys(): "
                    #     + str(observed_acct_deltas.keys()),
                    #     log_stack_depth,
                    # )
                    # print(pd.DataFrame(previous_row).T.to_string())
                    # print(pd.DataFrame(current_row).T.to_string())
                    # if f_i == 0:
                    #     pass
                    # else:
                        # log_in_color(
                        #     logger,
                        #     "white",
                        #     "debug",
                        #     future_rows_only_df.loc[(f_i - 1, f_i), :].to_string(),
                        #     log_stack_depth,
                        # )
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
                        # if f_i == 0:
                        #     log_in_color(
                        #         logger,
                        #         "white",
                        #         "debug",
                        #         pd.DataFrame(previous_row).to_string(),
                        #         log_stack_depth,
                        #     )
                        #     log_in_color(
                        #         logger,
                        #         "white",
                        #         "debug",
                        #         pd.DataFrame(current_row).T.to_string(),
                        #         log_stack_depth,
                        #     )
                        # else:
                        #     log_in_color(
                        #         logger,
                        #         "white",
                        #         "debug",
                        #         future_rows_only_df.loc[(f_i - 1, f_i), :].to_string(),
                        #         log_stack_depth,
                        #     )
                        raise ValueError(exception_string)

            index_of_first_future_day = list(forecast_df.Date).index(
                future_rows_only_df.head(1).Date.iat[0]
            )
            future_rows_only_df.index = (
                future_rows_only_df.index + index_of_first_future_day
            )

            affected_account_names = set(accounts_with_deltas["Name"])
            pre_update_cycle_payments = {}
            for account in account_set_before_p2_plus_txn.accounts:
                if account.account_type != "credit":
                    continue
                payment_column = (
                    f"{account.name}: Credit Billing Cycle Payment Bal"
                )
                if (
                    payment_column in affected_account_names
                    and payment_column in forecast_df.columns
                ):
                    pre_update_cycle_payments[payment_column] = forecast_df[
                        payment_column
                    ].copy()

            forecast_df.update(future_rows_only_df)

            forecast_dates = pd.to_datetime(forecast_df["Date"])

            # An additional credit payment belongs only to the billing cycle in
            # which it occurs.  The legacy propagation helpers carry its cycle-
            # payment delta through the entire remaining forecast, causing
            # successive monthly payments to accumulate.  Restore the forecast
            # that existed before this transaction beginning with the next
            # billing date.
            for account in account_set_before_p2_plus_txn.accounts:
                if account.account_type != "credit":
                    continue
                payment_column = (
                    f"{account.name}: Credit Billing Cycle Payment Bal"
                )
                if payment_column not in pre_update_cycle_payments:
                    continue
                billing_day = pd.Timestamp(
                    account.billing_state.billing_cycle_start_date
                ).day
                later_billing_dates = forecast_dates[
                    (forecast_dates > pd.Timestamp(date_string))
                    & (forecast_dates.dt.day == billing_day)
                ]
                if later_billing_dates.empty:
                    continue
                restore_from = later_billing_dates.min()
                restore_mask = forecast_dates >= restore_from
                forecast_df.loc[restore_mask, payment_column] = (
                    pre_update_cycle_payments[payment_column].loc[restore_mask]
                )

            # Recompute the derived end-of-previous-cycle balance across the
            # whole forecast.  This must happen after restoring cycle payments,
            # and must include boundaries before the current optimization date
            # so a later transaction cannot reintroduce a stale value.
            for account in account_set_before_p2_plus_txn.accounts:
                if account.account_type != "credit":
                    continue
                prev_column = f"{account.name}: Prev Stmt Bal"
                eopc_column = f"{account.name}: Credit End of Prev Cycle Bal"
                if eopc_column not in forecast_df.columns:
                    continue
                billing_start = account.billing_state.billing_cycle_start_date
                boundary_day = (
                    pd.Timestamp(billing_start) + pd.Timedelta(days=1)
                ).day
                boundaries = sorted(
                    forecast_dates[forecast_dates.dt.day == boundary_day].unique()
                )
                for boundary_index, boundary in enumerate(boundaries):
                    prior_indices = forecast_df.index[forecast_dates < boundary]
                    if len(prior_indices) == 0:
                        continue
                    new_eopc = forecast_df.at[prior_indices[-1], prev_column]
                    cycle_mask = forecast_dates >= boundary
                    if boundary_index + 1 < len(boundaries):
                        cycle_mask &= forecast_dates < boundaries[boundary_index + 1]
                    forecast_df.loc[cycle_mask, eopc_column] = new_eopc

        # log_in_color(
        #     logger,
        #     "yellow",
        #     "debug",
        #     str(date_string) + " after processing_function",
        #     log_stack_depth,
        # )
        # log_in_color(
        #     logger, "yellow", "debug", forecast_df.to_string(), log_stack_depth
        # )

        log_stack_depth -= 1
        # log_in_color(
        #     logger,
        #     "white",
        #     "debug",
        #     str(date_string)
        #     + " EXIT _propagateOptimizationTransactionsIntoTheFuture",
        #     log_stack_depth,
        # )
        return forecast_df

    # TODO potentially rename this. Update? in what way?
    #Codex-write-doctstring-OK
    @classmethod
    def _updateProposedTransactionsBasedOnOtherSets(
        cls, confirmed_df, proposed_df, deferred_df, skipped_df, log_stack_depth
    ):

        """
        TODO one-line description of ForecastHandler._updateProposedTransactionsBasedOnOtherSets.

        TODO multi-line description of ForecastHandler._updateProposedTransactionsBasedOnOtherSets.
        TODO explain how ForecastHandler._updateProposedTransactionsBasedOnOtherSets participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        confirmed_df : object
            TODO one-line description of ForecastHandler._updateProposedTransactionsBasedOnOtherSets.confirmed_df.

        proposed_df : object
            TODO one-line description of ForecastHandler._updateProposedTransactionsBasedOnOtherSets.proposed_df.

        deferred_df : object
            TODO one-line description of ForecastHandler._updateProposedTransactionsBasedOnOtherSets.deferred_df.

        skipped_df : object
            TODO one-line description of ForecastHandler._updateProposedTransactionsBasedOnOtherSets.skipped_df.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._updateProposedTransactionsBasedOnOtherSets.log_stack_depth.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._updateProposedTransactionsBasedOnOtherSets.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._updateProposedTransactionsBasedOnOtherSets.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._updateProposedTransactionsBasedOnOtherSets.

        @interface-report: show
        """
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

    #             account_set = cls._sync_account_set_w_forecast_day(
    #                 account_set, forecast_df=forecast_df, d=d_string
    #)

    #             # todo maybe this could be moved down? not sure
    #             account_set_before_p2_plus_txn = copy.deepcopy(account_set)

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
    #TODO manual review of ForecastHandler._assessPotentialOptimizations docstring
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
        """
        TODO one-line description of ForecastHandler._assessPotentialOptimizations.

        TODO multi-line description of ForecastHandler._assessPotentialOptimizations.
        TODO explain how ForecastHandler._assessPotentialOptimizations participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        end_date : date
            TODO one-line description of ForecastHandler._assessPotentialOptimizations.end_date.

        forecast_df : object
            TODO one-line description of ForecastHandler._assessPotentialOptimizations.forecast_df.

        account_set : object
            TODO one-line description of ForecastHandler._assessPotentialOptimizations.account_set.

        memo_rule_set : object
            TODO one-line description of ForecastHandler._assessPotentialOptimizations.memo_rule_set.

        confirmed_df : object
            TODO one-line description of ForecastHandler._assessPotentialOptimizations.confirmed_df.

        proposed_df : object
            TODO one-line description of ForecastHandler._assessPotentialOptimizations.proposed_df.

        deferred_df : object
            TODO one-line description of ForecastHandler._assessPotentialOptimizations.deferred_df.

        skipped_df : object
            TODO one-line description of ForecastHandler._assessPotentialOptimizations.skipped_df.

        raise__satisfice_failed_exception : object
            TODO one-line description of ForecastHandler._assessPotentialOptimizations.raise__satisfice_failed_exception.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._assessPotentialOptimizations.log_stack_depth.

        progress_bar : object
            TODO one-line description of ForecastHandler._assessPotentialOptimizations.progress_bar.

        include_debug_columns : bool
            TODO one-line description of ForecastHandler._assessPotentialOptimizations.include_debug_columns.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._assessPotentialOptimizations.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._assessPotentialOptimizations.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._assessPotentialOptimizations.

        @interface-report: show
        """
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

                account_set = cls._sync_account_set_w_forecast_day(
                    account_set=account_set, forecast_df=forecast_df, d=d, log_stack_depth=log_stack_depth
                )

                account_set_before_p2_plus_txn = copy.deepcopy(account_set)

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

    #Codex-write-doctstring-OK
    @classmethod
    def _cleanUpAfterFailedSatisfice(
        cls, end_date, confirmed_df, proposed_df, deferred_df, skipped_df, log_stack_depth
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        TODO one-line description of ForecastHandler._cleanUpAfterFailedSatisfice.

        TODO multi-line description of ForecastHandler._cleanUpAfterFailedSatisfice.
        TODO explain how ForecastHandler._cleanUpAfterFailedSatisfice participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        end_date : date
            TODO one-line description of ForecastHandler._cleanUpAfterFailedSatisfice.end_date.

        confirmed_df : object
            TODO one-line description of ForecastHandler._cleanUpAfterFailedSatisfice.confirmed_df.

        proposed_df : object
            TODO one-line description of ForecastHandler._cleanUpAfterFailedSatisfice.proposed_df.

        deferred_df : object
            TODO one-line description of ForecastHandler._cleanUpAfterFailedSatisfice.deferred_df.

        skipped_df : object
            TODO one-line description of ForecastHandler._cleanUpAfterFailedSatisfice.skipped_df.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._cleanUpAfterFailedSatisfice.log_stack_depth.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._cleanUpAfterFailedSatisfice.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._cleanUpAfterFailedSatisfice.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._cleanUpAfterFailedSatisfice.

        @interface-report: show
        """
        # log_in_color(logger, 'red', 'debug', 'ENTER _cleanUpAfterFailedSatisfice', log_stack_depth)
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

    #TODO manual review of ForecastHandler._updateEndOfPrevCycleBal docstring
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
        """
        TODO one-line description of ForecastHandler._updateEndOfPrevCycleBal.

        TODO multi-line description of ForecastHandler._updateEndOfPrevCycleBal.
        TODO explain how ForecastHandler._updateEndOfPrevCycleBal participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        forecast_df : object
            TODO one-line description of ForecastHandler._updateEndOfPrevCycleBal.forecast_df.

        account_set : object
            TODO one-line description of ForecastHandler._updateEndOfPrevCycleBal.account_set.

        current_forecast_row_df : object
            TODO one-line description of ForecastHandler._updateEndOfPrevCycleBal.current_forecast_row_df.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._updateEndOfPrevCycleBal.log_stack_depth.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._updateEndOfPrevCycleBal.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._updateEndOfPrevCycleBal.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._updateEndOfPrevCycleBal.

        @interface-report: show
        """
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
    #TODO manual review of ForecastHandler._satisfice docstring
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
        """
        TODO one-line description of ForecastHandler._satisfice.

        TODO multi-line description of ForecastHandler._satisfice.
        TODO explain how ForecastHandler._satisfice participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        start_date : date
            TODO one-line description of ForecastHandler._satisfice.start_date.

        end_date : date
            TODO one-line description of ForecastHandler._satisfice.end_date.

        list_of_date_strings : object
            TODO one-line description of ForecastHandler._satisfice.list_of_date_strings.

        confirmed_df : object
            TODO one-line description of ForecastHandler._satisfice.confirmed_df.

        account_set : object
            TODO one-line description of ForecastHandler._satisfice.account_set.

        memo_rule_set : object
            TODO one-line description of ForecastHandler._satisfice.memo_rule_set.

        forecast_df : object
            TODO one-line description of ForecastHandler._satisfice.forecast_df.

        raise__satisfice_failed_exception : object
            TODO one-line description of ForecastHandler._satisfice.raise__satisfice_failed_exception.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._satisfice.log_stack_depth.

        progress_bar : object
            TODO one-line description of ForecastHandler._satisfice.progress_bar.

        include_debug_columns : bool
            TODO one-line description of ForecastHandler._satisfice.include_debug_columns.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._satisfice.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._satisfice.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._satisfice.

        @interface-report: show
        """
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

                # Compound active investments before same-day transactions.
                forecast_df.loc[forecast_df.Date == d] = (
                    cls._calculateInvestmentReturnsForDay(
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

                # Execute loan minimum payments before same-day loan payments.
                forecast_df.loc[forecast_df.Date == d] = (
                    cls._executeLoanMinimumPayments(
                        account_set=account_set, current_forecast_row_df=forecast_df[forecast_df.Date == d], log_stack_depth=log_stack_depth
                    )
                )

                account_set = cls._sync_account_set_w_forecast_day(
                    account_set=account_set, forecast_df=forecast_df, d=d, log_stack_depth=log_stack_depth)

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

                # Execute credit card minimum payments before same-day transactions.
                forecast_df.loc[forecast_df.Date == d] = (
                    cls._executeCreditCardMinimumPayments(
                        forecast_df=forecast_df,
                        account_set=account_set,
                        current_forecast_row_df=forecast_df[forecast_df.Date == d], log_stack_depth=log_stack_depth
                    )
                )

                # log_in_color(logger, 'green', 'info', 'AFTER cc min payment', log_stack_depth)
                # log_in_color(logger, 'green', 'info', forecast_df.to_string(), log_stack_depth)

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
    #TODO manual review of ForecastHandler._computeOptimalForecast docstring
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
        """
        TODO one-line description of ForecastHandler._computeOptimalForecast.

        TODO multi-line description of ForecastHandler._computeOptimalForecast.
        TODO explain how ForecastHandler._computeOptimalForecast participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        start_date : date
            TODO one-line description of ForecastHandler._computeOptimalForecast.start_date.

        end_date : date
            TODO one-line description of ForecastHandler._computeOptimalForecast.end_date.

        confirmed_df : object
            TODO one-line description of ForecastHandler._computeOptimalForecast.confirmed_df.

        proposed_df : object
            TODO one-line description of ForecastHandler._computeOptimalForecast.proposed_df.

        deferred_df : object
            TODO one-line description of ForecastHandler._computeOptimalForecast.deferred_df.

        skipped_df : object
            TODO one-line description of ForecastHandler._computeOptimalForecast.skipped_df.

        account_set : object
            TODO one-line description of ForecastHandler._computeOptimalForecast.account_set.

        memo_rule_set : object
            TODO one-line description of ForecastHandler._computeOptimalForecast.memo_rule_set.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._computeOptimalForecast.log_stack_depth.

        raise__satisfice_failed_exception : object
            TODO one-line description of ForecastHandler._computeOptimalForecast.raise__satisfice_failed_exception.

        progress_bar : object
            TODO one-line description of ForecastHandler._computeOptimalForecast.progress_bar.

        include_debug_columns : bool
            TODO one-line description of ForecastHandler._computeOptimalForecast.include_debug_columns.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._computeOptimalForecast.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._computeOptimalForecast.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._computeOptimalForecast.

        @interface-report: show
        """
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

    # TODO compute_forecast_difference needs revision
    #TODO manual review of ForecastHandler.compute_forecast_difference docstring
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

        """
        TODO one-line description of ForecastHandler.compute_forecast_difference.

        TODO multi-line description of ForecastHandler.compute_forecast_difference.
        TODO explain how ForecastHandler.compute_forecast_difference participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        forecast_df : object
            TODO one-line description of ForecastHandler.compute_forecast_difference.forecast_df.

        forecast2_df : object
            TODO one-line description of ForecastHandler.compute_forecast_difference.forecast2_df.

        label : str
            TODO one-line description of ForecastHandler.compute_forecast_difference.label.

        make_plots : object
            TODO one-line description of ForecastHandler.compute_forecast_difference.make_plots.

        plot_directory : object
            TODO one-line description of ForecastHandler.compute_forecast_difference.plot_directory.

        return_type : object
            TODO one-line description of ForecastHandler.compute_forecast_difference.return_type.

        require_matching_columns : object
            TODO one-line description of ForecastHandler.compute_forecast_difference.require_matching_columns.

        require_matching_date_range : object
            TODO one-line description of ForecastHandler.compute_forecast_difference.require_matching_date_range.

        append_expected_values : object
            TODO one-line description of ForecastHandler.compute_forecast_difference.append_expected_values.

        diffs_only : object
            TODO one-line description of ForecastHandler.compute_forecast_difference.diffs_only.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler.compute_forecast_difference.

        Contract
        --------
        - #TODO contract lines for ForecastHandler.compute_forecast_difference.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler.compute_forecast_difference.

        @interface-report: show
        """
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


    #TODO manual review of ForecastHandler._appendSummaryLines docstring
    @classmethod
    def _appendSummaryLines(cls, initial_A, forecast_df, log_stack_depth):

        """
        TODO one-line description of ForecastHandler._appendSummaryLines.

        TODO multi-line description of ForecastHandler._appendSummaryLines.
        TODO explain how ForecastHandler._appendSummaryLines participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        initial_A : object
            TODO one-line description of ForecastHandler._appendSummaryLines.initial_A.

        forecast_df : object
            TODO one-line description of ForecastHandler._appendSummaryLines.forecast_df.

        log_stack_depth : int
            TODO one-line description of ForecastHandler._appendSummaryLines.log_stack_depth.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._appendSummaryLines.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._appendSummaryLines.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._appendSummaryLines.

        @interface-report: show
        """
        account_info = initial_A.getAccounts()

        loan_acct_sel_vec = account_info.Account_Type.isin(
            ["loan", "principal balance", "interest"]
        )
        cc_acct_sel_vec = account_info.Account_Type.isin(
            ["credit", "credit prev stmt bal", "credit curr stmt bal"]
        )
        checking_sel_vec = account_info.Account_Type == "checking"
        investment_sel_vec = account_info.Account_Type == "investment"

        loan_acct_info = account_info.loc[loan_acct_sel_vec, :]
        credit_acct_info = account_info.loc[cc_acct_sel_vec, :]
        investment_acct_info = account_info.loc[investment_sel_vec, :]

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

        for _, investment_account_row in investment_acct_info.iterrows():
            NetWorth = NetWorth + summary_numeric_series(investment_account_row.Name)

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
                if any(
                    directive_type in memo_line_item
                    for directive_type in (
                        "INCOME",
                        "INVESTMENT RETURN",
                        "INVESTMENT CONTRIBUTION",
                        "INVESTMENT WITHDRAWAL",
                    )
                ):
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
                    # log_in_color(
                    #     logger,
                    #     "red",
                    #     "debug",
                    #     "Validation FAIL -1*net_loss == (check_row_delta - (cc_row_delta + loan_row_delta)) was not TRUE",
                    #     log_stack_depth,
                    # )
                    # log_in_color(
                    #     logger,
                    #     "magenta",
                    #     "debug",
                    #     "Memo...........: " + str(memo),
                    #     log_stack_depth,
                    # )
                    # log_in_color(
                    #     logger,
                    #     "magenta",
                    #     "debug",
                    #     "Md.............: " + str(md),
                    #     log_stack_depth,
                    # )
                    # # log_in_color(logger, 'magenta', 'debug', str(-1*net_loss)+' != '+str( round((check_row_delta - (cc_row_delta + loan_row_delta)),2) ) , log_stack_depth)
                    # log_in_color(
                    #     logger,
                    #     "magenta",
                    #     "debug",
                    #     str(-1 * net_loss)
                    #     + " != "
                    #     + str((check_row_delta - (cc_row_delta + loan_row_delta))),
                    #     log_stack_depth,
                    # )
                    # log_in_color(logger, "magenta", "debug", "", log_stack_depth)

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
                    # log_in_color(
                    #     logger,
                    #     "red",
                    #     "debug",
                    #     "Validation FAIL net_gain == (check_row_delta - (cc_row_delta + loan_row_delta)) was not TRUE",
                    #     log_stack_depth,
                    # )
                    # log_in_color(
                    #     logger,
                    #     "magenta",
                    #     "debug",
                    #     "Memo...........: " + str(memo),
                    #     log_stack_depth,
                    # )
                    # log_in_color(
                    #     logger,
                    #     "magenta",
                    #     "debug",
                    #     "Md.............: " + str(md),
                    #     log_stack_depth,
                    # )
                    # # log_in_color(logger, 'magenta', 'debug', str(net_gain)+' != '+str( round((check_row_delta - (cc_row_delta + loan_row_delta)),2) ) , log_stack_depth)
                    # log_in_color(
                    #     logger,
                    #     "magenta",
                    #     "debug",
                    #     str(net_gain)
                    #     + " != "
                    #     + str((check_row_delta - (cc_row_delta + loan_row_delta))),
                    #     log_stack_depth,
                    # )

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

    #TODO manual review of ForecastHandler._report_date_to_datetime docstring
    @staticmethod
    def _report_date_to_datetime(value):
        """
        TODO one-line description of ForecastHandler._report_date_to_datetime.

        TODO multi-line description of ForecastHandler._report_date_to_datetime.
        TODO explain how ForecastHandler._report_date_to_datetime participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        value : object
            TODO one-line description of ForecastHandler._report_date_to_datetime.value.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._report_date_to_datetime.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._report_date_to_datetime.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._report_date_to_datetime.

        @interface-report: show
        """
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

    #TODO manual review of ForecastHandler._report_amount docstring
    @staticmethod
    def _report_amount(value):
        """
        TODO one-line description of ForecastHandler._report_amount.

        TODO multi-line description of ForecastHandler._report_amount.
        TODO explain how ForecastHandler._report_amount participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        value : object
            TODO one-line description of ForecastHandler._report_amount.value.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._report_amount.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._report_amount.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._report_amount.

        @interface-report: show
        """
        return str(f"${float(value):,}")

    @classmethod
    def _report_forecast_duration(cls, start_value, end_value):
        start_datetime = cls._report_date_to_datetime(start_value)
        end_datetime = cls._report_date_to_datetime(end_value)
        total_days = max(0, (end_datetime.date() - start_datetime.date()).days)
        parts = relativedelta(end_datetime.date(), start_datetime.date())

        def label(value, singular):
            return f"{value} {singular if value == 1 else singular + 's'}"

        duration_text = ", ".join(
            [label(parts.years, "year"), label(parts.months, "month"), label(parts.days, "day")]
        )
        return total_days, f"{duration_text} ({total_days:,} days total)"

    #TODO manual review of ForecastHandler._report_date_label docstring
    def _report_date_label(self, value):
        """
        TODO one-line description of ForecastHandler._report_date_label.

        TODO multi-line description of ForecastHandler._report_date_label.
        TODO explain how ForecastHandler._report_date_label participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        value : object
            TODO one-line description of ForecastHandler._report_date_label.value.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._report_date_label.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._report_date_label.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._report_date_label.

        @interface-report: show
        """
        return self._report_date_to_datetime(value).strftime("%Y-%m-%d")

    #TODO manual review of ForecastHandler._report_initial_conditions docstring
    def _report_initial_conditions(self, expense_forecast):
        """
        TODO one-line description of ForecastHandler._report_initial_conditions.

        TODO multi-line description of ForecastHandler._report_initial_conditions.
        TODO explain how ForecastHandler._report_initial_conditions participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            TODO one-line description of ForecastHandler._report_initial_conditions.expense_forecast.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._report_initial_conditions.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._report_initial_conditions.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._report_initial_conditions.

        @interface-report: show
        """
        return getattr(expense_forecast, "initial_conditions", expense_forecast)

    #TODO manual review of ForecastHandler._report_start_date docstring
    def _report_start_date(self, expense_forecast):
        """
        TODO one-line description of ForecastHandler._report_start_date.

        TODO multi-line description of ForecastHandler._report_start_date.
        TODO explain how ForecastHandler._report_start_date participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            TODO one-line description of ForecastHandler._report_start_date.expense_forecast.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._report_start_date.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._report_start_date.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._report_start_date.

        @interface-report: show
        """
        initial_conditions = self._report_initial_conditions(expense_forecast)
        return getattr(
            expense_forecast,
            "start_date_YYYYMMDD",
            getattr(initial_conditions, "start_date", None),
        )

    #TODO manual review of ForecastHandler._report_end_date docstring
    def _report_end_date(self, expense_forecast):
        """
        TODO one-line description of ForecastHandler._report_end_date.

        TODO multi-line description of ForecastHandler._report_end_date.
        TODO explain how ForecastHandler._report_end_date participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            TODO one-line description of ForecastHandler._report_end_date.expense_forecast.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._report_end_date.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._report_end_date.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._report_end_date.

        @interface-report: show
        """
        initial_conditions = self._report_initial_conditions(expense_forecast)
        return getattr(
            expense_forecast,
            "end_date_YYYYMMDD",
            getattr(initial_conditions, "end_date", None),
        )

    #TODO manual review of ForecastHandler._report_forecast_name docstring
    def _report_forecast_name(self, expense_forecast):
        """
        TODO one-line description of ForecastHandler._report_forecast_name.

        TODO multi-line description of ForecastHandler._report_forecast_name.
        TODO explain how ForecastHandler._report_forecast_name participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            TODO one-line description of ForecastHandler._report_forecast_name.expense_forecast.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._report_forecast_name.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._report_forecast_name.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._report_forecast_name.

        @interface-report: show
        """
        initial_conditions = self._report_initial_conditions(expense_forecast)
        return (
            getattr(expense_forecast, "forecast_name", None)
            or getattr(initial_conditions, "forecast_name", None)
            or f"Forecast {expense_forecast.unique_id}"
        )

    #TODO manual review of ForecastHandler._report_account_set docstring
    def _report_account_set(self, expense_forecast):
        """
        TODO one-line description of ForecastHandler._report_account_set.

        TODO multi-line description of ForecastHandler._report_account_set.
        TODO explain how ForecastHandler._report_account_set participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            TODO one-line description of ForecastHandler._report_account_set.expense_forecast.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._report_account_set.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._report_account_set.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._report_account_set.

        @interface-report: show
        """
        initial_conditions = self._report_initial_conditions(expense_forecast)
        return getattr(
            expense_forecast,
            "initial_account_set",
            getattr(initial_conditions, "initial_account_set", None),
        )

    #TODO manual review of ForecastHandler._report_budget_set docstring
    def _report_budget_set(self, expense_forecast):
        """
        TODO one-line description of ForecastHandler._report_budget_set.

        TODO multi-line description of ForecastHandler._report_budget_set.
        TODO explain how ForecastHandler._report_budget_set participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            TODO one-line description of ForecastHandler._report_budget_set.expense_forecast.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._report_budget_set.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._report_budget_set.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._report_budget_set.

        @interface-report: show
        """
        initial_conditions = self._report_initial_conditions(expense_forecast)
        return getattr(
            expense_forecast,
            "initial_budget_set",
            getattr(initial_conditions, "initial_budget_set", None),
        )

    #TODO manual review of ForecastHandler._report_memo_rule_set docstring
    def _report_memo_rule_set(self, expense_forecast):
        """
        TODO one-line description of ForecastHandler._report_memo_rule_set.

        TODO multi-line description of ForecastHandler._report_memo_rule_set.
        TODO explain how ForecastHandler._report_memo_rule_set participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            TODO one-line description of ForecastHandler._report_memo_rule_set.expense_forecast.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._report_memo_rule_set.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._report_memo_rule_set.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._report_memo_rule_set.

        @interface-report: show
        """
        initial_conditions = self._report_initial_conditions(expense_forecast)
        return getattr(
            expense_forecast,
            "initial_memo_rule_set",
            getattr(initial_conditions, "initial_memo_rule_set", None),
        )

    #TODO manual review of ForecastHandler._report_milestone_set docstring
    def _report_milestone_set(self, expense_forecast):
        """
        TODO one-line description of ForecastHandler._report_milestone_set.

        TODO multi-line description of ForecastHandler._report_milestone_set.
        TODO explain how ForecastHandler._report_milestone_set participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            TODO one-line description of ForecastHandler._report_milestone_set.expense_forecast.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._report_milestone_set.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._report_milestone_set.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._report_milestone_set.

        @interface-report: show
        """
        initial_conditions = self._report_initial_conditions(expense_forecast)
        return getattr(
            expense_forecast,
            "milestone_set",
            getattr(initial_conditions, "milestone_set", None),
        )

    #TODO manual review of ForecastHandler._empty_report_df docstring
    @staticmethod
    def _empty_report_df():
        """
        TODO one-line description of ForecastHandler._empty_report_df.

        TODO multi-line description of ForecastHandler._empty_report_df.
        TODO explain how ForecastHandler._empty_report_df participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that ForecastHandler._empty_report_df takes no parameters beyond self/cls.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._empty_report_df.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._empty_report_df.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._empty_report_df.

        @interface-report: show
        """
        return pd.DataFrame()

    #TODO manual review of ForecastHandler._report_milestone_table docstring
    def _report_milestone_table(self, milestone_set, method_name):
        """
        TODO one-line description of ForecastHandler._report_milestone_table.

        TODO multi-line description of ForecastHandler._report_milestone_table.
        TODO explain how ForecastHandler._report_milestone_table participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        milestone_set : object
            TODO one-line description of ForecastHandler._report_milestone_table.milestone_set.

        method_name : object
            TODO one-line description of ForecastHandler._report_milestone_table.method_name.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._report_milestone_table.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._report_milestone_table.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._report_milestone_table.

        @interface-report: show
        """
        if milestone_set is None or not hasattr(milestone_set, method_name):
            return self._empty_report_df()
        return getattr(milestone_set, method_name)()

    #TODO manual review of ForecastHandler._report_milestone_results_df docstring
    def _report_milestone_results_df(self, expense_forecast, result_type):
        """
        TODO one-line description of ForecastHandler._report_milestone_results_df.

        TODO multi-line description of ForecastHandler._report_milestone_results_df.
        TODO explain how ForecastHandler._report_milestone_results_df participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            TODO one-line description of ForecastHandler._report_milestone_results_df.expense_forecast.

        result_type : object
            TODO one-line description of ForecastHandler._report_milestone_results_df.result_type.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._report_milestone_results_df.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._report_milestone_results_df.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._report_milestone_results_df.

        @interface-report: show
        """
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

    #TODO manual review of ForecastHandler._report_confirmed_df docstring
    def _report_confirmed_df(self, expense_forecast):
        """
        TODO one-line description of ForecastHandler._report_confirmed_df.

        TODO multi-line description of ForecastHandler._report_confirmed_df.
        TODO explain how ForecastHandler._report_confirmed_df participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            TODO one-line description of ForecastHandler._report_confirmed_df.expense_forecast.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._report_confirmed_df.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._report_confirmed_df.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._report_confirmed_df.

        @interface-report: show
        """
        confirmed_df = getattr(expense_forecast, "confirmed_df", None)
        if confirmed_df is not None:
            return confirmed_df

        initial_conditions = self._report_initial_conditions(expense_forecast)
        confirmed_df = getattr(initial_conditions, "initial_confirmed_df", None)
        if confirmed_df is not None:
            return confirmed_df

        return pd.DataFrame(columns=["Date", "Priority", "Amount", "Memo"])

    #TODO manual review of ForecastHandler._report_dates_for_plot docstring
    def _report_dates_for_plot(self, expense_forecast):
        """
        TODO one-line description of ForecastHandler._report_dates_for_plot.

        TODO multi-line description of ForecastHandler._report_dates_for_plot.
        TODO explain how ForecastHandler._report_dates_for_plot participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            TODO one-line description of ForecastHandler._report_dates_for_plot.expense_forecast.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._report_dates_for_plot.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._report_dates_for_plot.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._report_dates_for_plot.

        @interface-report: show
        """
        return [
            self._report_date_to_datetime(d)
            for d in expense_forecast.forecast_df["Date"]
        ]

    #TODO manual review of ForecastHandler._decorate_report_plot docstring
    def _decorate_report_plot(self, expense_forecast):
        """
        TODO one-line description of ForecastHandler._decorate_report_plot.

        TODO multi-line description of ForecastHandler._decorate_report_plot.
        TODO explain how ForecastHandler._decorate_report_plot participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            TODO one-line description of ForecastHandler._decorate_report_plot.expense_forecast.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler._decorate_report_plot.

        Contract
        --------
        - #TODO contract lines for ForecastHandler._decorate_report_plot.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler._decorate_report_plot.

        @interface-report: show
        """
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
            [box.x0, box.y0 + box.height * 0.2, box.width, box.height * 0.8]
        )
        ax.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, -0.18),
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

    #TODO manual review of ForecastHandler.plotMilestoneDates docstring
    def plotMilestoneDates(
        self, expense_forecast, output_path, plot_colors=["red", "blue", "purple"]
    ):
        """
        TODO one-line description of ForecastHandler.plotMilestoneDates.

        TODO multi-line description of ForecastHandler.plotMilestoneDates.
        TODO explain how ForecastHandler.plotMilestoneDates participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            TODO one-line description of ForecastHandler.plotMilestoneDates.expense_forecast.

        output_path : object
            TODO one-line description of ForecastHandler.plotMilestoneDates.output_path.

        plot_colors : object
            TODO one-line description of ForecastHandler.plotMilestoneDates.plot_colors.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler.plotMilestoneDates.

        Contract
        --------
        - #TODO contract lines for ForecastHandler.plotMilestoneDates.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler.plotMilestoneDates.

        @interface-report: show
        """
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

    #TODO manual review of ForecastHandler.plotAccountTypeTotals docstring
    def plotAccountTypeTotals(
        self,
        expense_forecast,
        output_path,
        line_color_cycle_list=["blue", "orange", "green", "purple"],
        linestyle="solid",
    ):
        """
        TODO one-line description of ForecastHandler.plotAccountTypeTotals.

        TODO multi-line description of ForecastHandler.plotAccountTypeTotals.
        TODO explain how ForecastHandler.plotAccountTypeTotals participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            TODO one-line description of ForecastHandler.plotAccountTypeTotals.expense_forecast.

        output_path : object
            TODO one-line description of ForecastHandler.plotAccountTypeTotals.output_path.

        line_color_cycle_list : object
            TODO one-line description of ForecastHandler.plotAccountTypeTotals.line_color_cycle_list.

        linestyle : object
            TODO one-line description of ForecastHandler.plotAccountTypeTotals.linestyle.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler.plotAccountTypeTotals.

        Contract
        --------
        - #TODO contract lines for ForecastHandler.plotAccountTypeTotals.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler.plotAccountTypeTotals.

        @interface-report: show
        """
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

        account_set = self._report_account_set(expense_forecast)
        if account_set is not None:
            investment_names = account_set.getAccounts().loc[
                lambda accounts: accounts.Account_Type == "investment", "Name"
            ].tolist()
            investment_names = [
                name for name in investment_names
                if name in expense_forecast.forecast_df.columns
            ]
            if investment_names:
                investment_total = expense_forecast.forecast_df[
                    investment_names
                ].sum(axis=1)
                plt.plot(
                    x_values,
                    investment_total,
                    label="Investment Total " + str(expense_forecast.unique_id),
                    linestyle=linestyle,
                )

        self._decorate_report_plot(expense_forecast)
        plt.savefig(output_path, bbox_inches="tight")
        matplotlib.pyplot.close()

    #TODO manual review of ForecastHandler.plotNetGainLoss docstring
    def plotNetGainLoss(
        self,
        expense_forecast,
        output_path,
        line_color_cycle_list=["green", "red"],
        linestyle="solid",
    ):
        """
        TODO one-line description of ForecastHandler.plotNetGainLoss.

        TODO multi-line description of ForecastHandler.plotNetGainLoss.
        TODO explain how ForecastHandler.plotNetGainLoss participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            TODO one-line description of ForecastHandler.plotNetGainLoss.expense_forecast.

        output_path : object
            TODO one-line description of ForecastHandler.plotNetGainLoss.output_path.

        line_color_cycle_list : object
            TODO one-line description of ForecastHandler.plotNetGainLoss.line_color_cycle_list.

        linestyle : object
            TODO one-line description of ForecastHandler.plotNetGainLoss.linestyle.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler.plotNetGainLoss.

        Contract
        --------
        - #TODO contract lines for ForecastHandler.plotNetGainLoss.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler.plotNetGainLoss.

        @interface-report: show
        """
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
        plt.savefig(output_path, bbox_inches="tight")
        matplotlib.pyplot.close()

    #TODO manual review of ForecastHandler.plotNetWorth docstring
    def plotNetWorth(
        self,
        expense_forecast,
        output_path,
        line_color_cycle_list=["blue"],
        linestyle="solid",
    ):
        """
        TODO one-line description of ForecastHandler.plotNetWorth.

        TODO multi-line description of ForecastHandler.plotNetWorth.
        TODO explain how ForecastHandler.plotNetWorth participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            TODO one-line description of ForecastHandler.plotNetWorth.expense_forecast.

        output_path : object
            TODO one-line description of ForecastHandler.plotNetWorth.output_path.

        line_color_cycle_list : object
            TODO one-line description of ForecastHandler.plotNetWorth.line_color_cycle_list.

        linestyle : object
            TODO one-line description of ForecastHandler.plotNetWorth.linestyle.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler.plotNetWorth.

        Contract
        --------
        - #TODO contract lines for ForecastHandler.plotNetWorth.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler.plotNetWorth.

        @interface-report: show
        """
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
        plt.savefig(output_path, bbox_inches="tight")
        matplotlib.pyplot.close()

    #TODO manual review of ForecastHandler.plotAll docstring
    def plotAll(
        self,
        expense_forecast,
        output_path,
    ):
        """
        TODO one-line description of ForecastHandler.plotAll.

        TODO multi-line description of ForecastHandler.plotAll.
        TODO explain how ForecastHandler.plotAll participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            TODO one-line description of ForecastHandler.plotAll.expense_forecast.

        output_path : object
            TODO one-line description of ForecastHandler.plotAll.output_path.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler.plotAll.

        Contract
        --------
        - #TODO contract lines for ForecastHandler.plotAll.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler.plotAll.

        @interface-report: show
        """
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

    #TODO manual review of ForecastHandler.plotMarginalInterest docstring
    def plotMarginalInterest(self, expense_forecast, output_path, linestyle="solid"):
        """
        TODO one-line description of ForecastHandler.plotMarginalInterest.

        TODO multi-line description of ForecastHandler.plotMarginalInterest.
        TODO explain how ForecastHandler.plotMarginalInterest participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            TODO one-line description of ForecastHandler.plotMarginalInterest.expense_forecast.

        output_path : object
            TODO one-line description of ForecastHandler.plotMarginalInterest.output_path.

        linestyle : object
            TODO one-line description of ForecastHandler.plotMarginalInterest.linestyle.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler.plotMarginalInterest.

        Contract
        --------
        - #TODO contract lines for ForecastHandler.plotMarginalInterest.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler.plotMarginalInterest.

        @interface-report: show
        """
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
        plt.savefig(output_path, bbox_inches="tight")
        matplotlib.pyplot.close()

    #TODO manual review of ForecastHandler.plotSankeyDiagram docstring
    def plotSankeyDiagram(self, expense_forecast, output_path):
        """
        TODO one-line description of ForecastHandler.plotSankeyDiagram.

        TODO multi-line description of ForecastHandler.plotSankeyDiagram.
        TODO explain how ForecastHandler.plotSankeyDiagram participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            TODO one-line description of ForecastHandler.plotSankeyDiagram.expense_forecast.

        output_path : object
            TODO one-line description of ForecastHandler.plotSankeyDiagram.output_path.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler.plotSankeyDiagram.

        Contract
        --------
        - #TODO contract lines for ForecastHandler.plotSankeyDiagram.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler.plotSankeyDiagram.

        @interface-report: show
        """
        if go is None:
            raise ImportError("plotly is required to generate the Sankey diagram")

        budget_set = self._report_budget_set(expense_forecast)
        memo_rule_set = self._report_memo_rule_set(expense_forecast)
        if budget_set is None or memo_rule_set is None:
            raise ValueError("BudgetSet and MemoRuleSet are required for Sankey report")

        income_memos = []
        expense_memos = []
        for _, row in budget_set.getLineItems().iterrows():
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

    #TODO manual review of ForecastHandler.generateHTMLReport docstring
    # def generateHTMLReport(self, E, output_dir="./", parent_report_path=None):
    #     """
    #     TODO one-line description of ForecastHandler.generateHTMLReport.

    #     TODO multi-line description of ForecastHandler.generateHTMLReport.
    #     TODO explain how ForecastHandler.generateHTMLReport participates in this module.
    #     TODO document important state, validation, or serialization behavior.

    #     Parameters
    #     ----------
    #     E : object
    #         TODO one-line description of ForecastHandler.generateHTMLReport.E.

    #     output_dir : object
    #         TODO one-line description of ForecastHandler.generateHTMLReport.output_dir.

    #     parent_report_path : object
    #         TODO one-line description of ForecastHandler.generateHTMLReport.parent_report_path.

    #     Returns
    #     -------
    #     object
    #         TODO one-line description of return value of ForecastHandler.generateHTMLReport.

    #     Contract
    #     --------
    #     - #TODO contract lines for ForecastHandler.generateHTMLReport.
    #     - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler.generateHTMLReport.

    #     @interface-report: show
    #     """
    #     start_date = self._report_date_label(self._report_start_date(E))
    #     end_date = self._report_date_label(self._report_end_date(E))

    #     forecast_failed = (
    #         self._report_date_to_datetime(E.forecast_df.tail(1).Date.iat[0]).date()
    #         != self._report_date_to_datetime(self._report_end_date(E)).date()
    #     )

    #     report_id = E.unique_id
    #     output_file_name = "Forecast_" + str(report_id)

    #     start_ts = getattr(E, "start_ts", None)
    #     end_ts = getattr(E, "end_ts", None)
    #     if start_ts is not None and end_ts is not None:
    #         start_ts__datetime = self._report_date_to_datetime(start_ts)
    #         end_ts__datetime = self._report_date_to_datetime(end_ts)
    #         simulation_seconds = max(
    #             0, (end_ts__datetime - start_ts__datetime).total_seconds()
    #         )
    #         runtime_text = (
    #             "This forecast started at "
    #             + str(start_ts__datetime)
    #             + ", took "
    #             + f"{simulation_seconds:,.3f} seconds"
    #             + " to complete, and finished at "
    #             + str(end_ts__datetime)
    #             + "."
    #         )
    #     else:
    #         runtime_text = "Runtime timing was not recorded for this forecast."

    #     if parent_report_path is not None:
    #         parent_report_text = (
    #             """This report was generated alongside some others. See <a href=\""""
    #             + parent_report_path
    #             + """\">this page</a> for information about related forecasts."""
    #         )
    #     else:
    #         parent_report_text = ""

    #     summary_text = runtime_text

    #     account_set = self._report_account_set(E)
    #     budget_set = self._report_budget_set(E)
    #     memo_rule_set = self._report_memo_rule_set(E)
    #     milestone_set = self._report_milestone_set(E)

    #     accounts_table = account_set.getAccounts().copy() if account_set is not None else None
    #     account_text = (
    #         """
    #     The initial conditions and account boundaries are defined as:"""
    #         + (
    #             accounts_table.to_html(
    #                 formatters={"Balance": lambda value: f"{float(value):,.2f}"}
    #             )
    #             if accounts_table is not None
    #             else ""
    #         )
    #         + """
    #     """
    #     )

    #     budget_set_text = (
    #         """
    #     These transactions are considered for analysis:"""
    #         + (budget_set.getLineItems().to_html() if budget_set is not None else "")
    #         + """
    #     """
    #     )

    #     memo_rules_table = memo_rule_set.getMemoRules().copy() if memo_rule_set is not None else None
    #     if memo_rules_table is not None and "Transaction_Priority" in memo_rules_table:
    #         memo_rules_table["Transaction_Priority"] = (
    #             memo_rules_table["Transaction_Priority"].astype(int)
    #         )
    #     memo_rule_text = (
    #         """
    #     These decision rules are used:"""
    #         + (memo_rules_table.to_html() if memo_rules_table is not None else "")
    #         + """
    #     """
    #     )

    #     account_milestone_text = (
    #         """
    #     These account milestones are defined:"""
    #         + self._report_milestone_table(milestone_set, "getAccountMilestonesDF").to_html()
    #         + """
    #     """
    #     )

    #     memo_milestone_text = (
    #         """
    #     These memo milestones are defined:"""
    #         + self._report_milestone_table(milestone_set, "getMemoMilestonesDF").to_html()
    #         + """
    #     """
    #     )

    #     composite_milestone_text = (
    #         """
    #     These composite milestones are defined:"""
    #         + self._report_milestone_table(milestone_set, "getCompositeMilestonesDF").to_html()
    #         + """
    #     """
    #     )

    #     initial_networth = round(E.forecast_df.head(1)["Net Worth"].iat[0], 2)
    #     final_networth = round(E.forecast_df.tail(1)["Net Worth"].iat[0], 2)
    #     networth_delta = round(final_networth - initial_networth, 2)
    #     num_days, forecast_duration_text = self._report_forecast_duration(
    #         self._report_start_date(E), self._report_end_date(E)
    #     )
    #     averaging_days = max(1, num_days)
    #     avg_networth_change = round(networth_delta / float(averaging_days), 2)
    #     rose_or_fell = "rose" if networth_delta >= 0 else "fell"

    #     networth_text = (
    #         """
    #     Net Worth began at """
    #         + self._report_amount(initial_networth)
    #         + """ and """
    #         + rose_or_fell
    #         + """ to """
    #         + self._report_amount(final_networth)
    #         + """ over """
    #         + forecast_duration_text
    #         + """, averaging """
    #         + self._report_amount(avg_networth_change)
    #         + """ per day.
    #     """
    #     )

    #     initial_loan_total = round(E.forecast_df.head(1)["Loan Total"].iat[0], 2)
    #     final_loan_total = round(E.forecast_df.tail(1)["Loan Total"].iat[0], 2)
    #     loan_delta = round(final_loan_total - initial_loan_total, 2)
    #     initial_cc_debt_total = round(E.forecast_df.head(1)["CC Debt Total"].iat[0], 2)
    #     final_cc_debt_total = round(E.forecast_df.tail(1)["CC Debt Total"].iat[0], 2)
    #     cc_debt_delta = round(final_cc_debt_total - initial_cc_debt_total, 2)
    #     initial_liquid_total = round(E.forecast_df.head(1)["Liquid Total"].iat[0], 2)
    #     final_liquid_total = round(E.forecast_df.tail(1)["Liquid Total"].iat[0], 2)
    #     liquid_delta = round(final_liquid_total - initial_liquid_total, 2)

    #     avg_loan_delta = round(loan_delta / averaging_days, 2)
    #     avg_cc_debt_delta = round(cc_debt_delta / averaging_days, 2)
    #     avg_liquid_delta = round(liquid_delta / averaging_days, 2)

    #     investment_names = []
    #     if accounts_table is not None:
    #         investment_names = accounts_table.loc[
    #             accounts_table.Account_Type == "investment", "Name"
    #         ].tolist()
    #     investment_names = [
    #         name for name in investment_names if name in E.forecast_df.columns
    #     ]
    #     investment_total = (
    #         E.forecast_df[investment_names].sum(axis=1)
    #         if investment_names
    #         else pd.Series(0.0, index=E.forecast_df.index)
    #     )
    #     initial_investment_total = round(investment_total.iloc[0], 2)
    #     final_investment_total = round(investment_total.iloc[-1], 2)
    #     investment_delta = round(
    #         final_investment_total - initial_investment_total, 2
    #     )
    #     avg_investment_delta = round(investment_delta / averaging_days, 2)

    #     account_type_text = (
    #         """
    #     Loan debt began at """
    #         + self._report_amount(initial_loan_total)
    #         + """ and """
    #         + ("rose" if avg_loan_delta >= 0 else "fell")
    #         + """ to """
    #         + self._report_amount(final_loan_total)
    #         + """ over """
    #         + forecast_duration_text
    #         + """, averaging """
    #         + self._report_amount(avg_loan_delta)
    #         + """ per day.
    #     <br><br>
    #     Credit card debt began at """
    #         + self._report_amount(initial_cc_debt_total)
    #         + """ and """
    #         + ("rose" if avg_cc_debt_delta >= 0 else "fell")
    #         + """ to """
    #         + self._report_amount(final_cc_debt_total)
    #         + """ over """
    #         + forecast_duration_text
    #         + """, averaging """
    #         + self._report_amount(avg_cc_debt_delta)
    #         + """ per day.
    #     <br><br>
    #     Liquid cash began at """
    #         + self._report_amount(initial_liquid_total)
    #         + """ and """
    #         + ("rose" if avg_liquid_delta >= 0 else "fell")
    #         + """ to """
    #         + self._report_amount(final_liquid_total)
    #         + """ over """
    #         + forecast_duration_text
    #         + """, averaging """
    #         + self._report_amount(avg_liquid_delta)
    #         + """ per day.
    #     <br><br>
    #     Investments began at """
    #         + self._report_amount(initial_investment_total)
    #         + """ and """
    #         + ("rose" if investment_delta >= 0 else "fell")
    #         + """ to """
    #         + self._report_amount(final_investment_total)
    #         + """ over """
    #         + forecast_duration_text
    #         + """, averaging """
    #         + self._report_amount(avg_investment_delta)
    #         + """ per day.
    #     """
    #     )

    #     total_gain = round(sum(E.forecast_df["Net Gain"]), 2)
    #     avg_daily_gain = round(total_gain / averaging_days, 2)
    #     total_loss = round(sum(E.forecast_df["Net Loss"]), 2)
    #     avg_daily_loss = round(total_loss / averaging_days, 2)

    #     net_gain_loss_text = (
    #         "Total gain was "
    #         + self._report_amount(total_gain)
    #         + " over "
    #         + forecast_duration_text
    #         + ", averaging "
    #         + self._report_amount(avg_daily_gain)
    #         + " per day.<br><br>"
    #     )
    #     net_gain_loss_text += (
    #         "Total loss was "
    #         + str(f"-${float(total_loss):,}")
    #         + " over "
    #         + forecast_duration_text
    #         + ", averaging "
    #         + str(f"-${float(avg_daily_loss):,}")
    #         + " per day."
    #     )

    #     total_interest_accrued = round(sum(E.forecast_df["Marginal Interest"]), 2)
    #     avg_interest_accrued = round(total_interest_accrued / averaging_days, 2)

    #     interest_text = (
    #         "Total interest accrued was "
    #         + self._report_amount(total_interest_accrued)
    #         + " over "
    #         + forecast_duration_text
    #         + ", averaging "
    #         + self._report_amount(avg_interest_accrued)
    #         + " per day.<br>"
    #     )
    #     interest_text += "This plot shows the new interest by day, not the total interest at a given time."

    #     cc_interest_sel_vec = [
    #         "cc interest" in str(m).lower() for m in E.forecast_df.Memo
    #     ]
    #     interest_rows_df = E.forecast_df.loc[cc_interest_sel_vec]
    #     interest_table_to_display_df = pd.DataFrame(interest_rows_df["Date"])
    #     interest_table_to_display_df["Total CC Interest"] = 0.0
    #     for index, row in interest_rows_df.iterrows():
    #         memo_line = str(row.Memo)
    #         memo_line_items = memo_line.split(";")
    #         for memo_line_item in memo_line_items:
    #             memo_line_item = memo_line_item.strip()
    #             if "cc interest" not in memo_line_item.lower():
    #                 continue

    #             value_match = re.search(
    #                 "\\(([A-Za-z0-9_ :]*) ([-+]?\\$.*)\\)$", memo_line_item
    #             )
    #             if value_match is None:
    #                 continue
    #             line_item_value_string = value_match.group(2)
    #             line_item_value_string = (
    #                 line_item_value_string.replace("(", "")
    #                 .replace(")", "")
    #                 .replace("$", "")
    #             )
    #             line_item_value = float(line_item_value_string)
    #             interest_table_to_display_df.loc[
    #                 index, "Total CC Interest"
    #             ] += line_item_value
    #     interest_table_html = interest_table_to_display_df.to_html()

    #     am_result_df = self._report_milestone_results_df(E, "Account")
    #     mm_result_df = self._report_milestone_results_df(E, "Memo")
    #     cm_result_df = self._report_milestone_results_df(E, "Composite")

    #     end_date_datetime = self._report_date_to_datetime(self._report_end_date(E))
    #     achieved_am_count = (
    #         am_result_df[am_result_df.Date < end_date_datetime].shape[0]
    #         if "Date" in am_result_df.columns
    #         else 0
    #     )
    #     achieved_mm_count = (
    #         mm_result_df[mm_result_df.Date < end_date_datetime].shape[0]
    #         if "Date" in mm_result_df.columns
    #         else 0
    #     )
    #     achieved_cm_count = (
    #         cm_result_df[cm_result_df.Date < end_date_datetime].shape[0]
    #         if "Date" in cm_result_df.columns
    #         else 0
    #     )
    #     total_milestone_count = (
    #         am_result_df.shape[0] + mm_result_df.shape[0] + cm_result_df.shape[0]
    #     )
    #     achieved_milestone_count = (
    #         achieved_am_count + achieved_mm_count + achieved_cm_count
    #     )

    #     milestone_text = (
    #         str(total_milestone_count)
    #         + " milestones were defined, and "
    #         + str(achieved_milestone_count)
    #         + " were achieved before the end of the forecast.<br>"
    #     )
    #     milestone_text += "Note that unachieved milestones are displayed on the last day of the forecast."

    #     transaction_schedule_text = "Transactions are displayed below."
    #     confirmed_df = self._report_confirmed_df(E)
    #     if "Priority" in confirmed_df.columns:
    #         p2_plus_txns_html_table = confirmed_df[confirmed_df.Priority >= 2].to_html()
    #     else:
    #         p2_plus_txns_html_table = confirmed_df.to_html()

    #     payment_rows = []
    #     account_type_by_name = {}
    #     if account_set is not None:
    #         account_type_by_name = dict(
    #             zip(account_set.getAccounts()["Name"], account_set.getAccounts()["Account_Type"])
    #         )
    #     if (
    #         memo_rule_set is not None
    #         and "Priority" in confirmed_df.columns
    #         and "Memo" in confirmed_df.columns
    #     ):
    #         for _, confirmed_row in confirmed_df[confirmed_df.Priority >= 2].iterrows():
    #             memo_rule = memo_rule_set.findMatchingMemoRule(
    #                 confirmed_row.Memo, confirmed_row.Priority
    #             )
    #             account_to_type = account_type_by_name.get(memo_rule.account_to)
    #             if account_to_type == "credit":
    #                 payment_rows.append(
    #                     {
    #                         "Payment Type": "Credit Card",
    #                         "Date": confirmed_row.Date,
    #                         "Memo": confirmed_row.Memo,
    #                         "Amount": confirmed_row.Amount,
    #                     }
    #                 )
    #             elif account_to_type == "loan" or memo_rule.account_to == "ALL_LOANS":
    #                 payment_rows.append(
    #                     {
    #                         "Payment Type": "Loan",
    #                         "Date": confirmed_row.Date,
    #                         "Memo": confirmed_row.Memo,
    #                         "Amount": confirmed_row.Amount,
    #                     }
    #                 )

    #     for _, row in E.forecast_df.iterrows():
    #         memo_line_items = str(row.Memo).split(";") + str(row["Memo Directives"]).split(";")
    #         for memo_line_item in memo_line_items:
    #             memo_line_item_lower = memo_line_item.lower()
    #             if (
    #                 "loan min payment" in memo_line_item_lower
    #                 or "additional loan payment" in memo_line_item_lower
    #                 or "addtl loan payment" in memo_line_item_lower
    #             ):
    #                 payment_rows.append(
    #                     {"Payment Type": "Loan", "Date": row.Date, "Memo": memo_line_item}
    #                 )
    #             elif (
    #                 "cc min payment" in memo_line_item_lower
    #                 or "additional cc payment" in memo_line_item_lower
    #                 or "addtl cc payment" in memo_line_item_lower
    #                 or "cc interest" in memo_line_item_lower
    #             ):
    #                 payment_rows.append(
    #                     {"Payment Type": "Credit Card", "Date": row.Date, "Memo": memo_line_item}
    #                 )

    #     payments_df = pd.DataFrame(payment_rows)
    #     cc_payments_html_table = payments_df[
    #         payments_df.get("Payment Type", pd.Series(dtype=str)) == "Credit Card"
    #     ].to_html()
    #     loan_payment_html_table = payments_df[
    #         payments_df.get("Payment Type", pd.Series(dtype=str)) == "Loan"
    #     ].to_html()

    #     all_plot_page_text = ""
    #     sankey_text = ""

    #     output_target = Path(output_dir)
    #     if output_target.suffix:
    #         html_output_path = output_target
    #         image_output_dir = output_target.parent
    #     else:
    #         image_output_dir = output_target
    #         html_output_path = image_output_dir / (output_file_name + ".html")

    #     image_output_dir.mkdir(parents=True, exist_ok=True)
    #     networth_line_plot_path = report_id + "_networth_line_plot.png"
    #     net_gain_loss_line_plot_path = report_id + "_net_gain_loss_line_plot.png"
    #     accounttype_line_plot_path = report_id + "_accounttype_line_plot.png"
    #     marginal_interest_line_plot_path = (
    #         report_id + "_marginal_interest_line_plot.png"
    #     )
    #     milestone_scatter_plot_path = report_id + "_milestone_scatter_plot.png"
    #     all_line_plot_path = report_id + "_all_line_plot.png"
    #     sankey_path = report_id + "_sankey.jpg"

    #     self.plotAll(E, image_output_dir / all_line_plot_path)
    #     self.plotNetWorth(E, image_output_dir / networth_line_plot_path)
    #     self.plotAccountTypeTotals(E, image_output_dir / accounttype_line_plot_path)
    #     self.plotMarginalInterest(E, image_output_dir / marginal_interest_line_plot_path)
    #     self.plotNetGainLoss(E, image_output_dir / net_gain_loss_line_plot_path)
    #     self.plotMilestoneDates(E, image_output_dir / milestone_scatter_plot_path)
    #     try:
    #         self.plotSankeyDiagram(E, image_output_dir / sankey_path)
    #     except Exception as exc:
    #         sankey_text = "Sankey diagram generation failed: " + str(exc)
    #         sankey_path = ""

    #     left_fail_style_tag = ""
    #     right_fail_style_tag = ""
    #     fail_message = ""
    #     if forecast_failed:
    #         left_fail_style_tag = '<font color ="red">'
    #         right_fail_style_tag = "</font>"
    #         fail_message = "This forecast failed to reach the end. The results may not reflect the effect of non-essential transactions accurately."

    #     html_body = (
    #         """
    #     <!DOCTYPE html>
    #     <html>
    #     <head>
    #     <meta name="viewport" content="width=device-width, initial-scale=1">
    #     <title>Expense Forecast Report #"""
    #         + str(report_id)
    #         + """</title>
    #     <style>
    #     :root {
    #       color-scheme: dark;
    #       --bg: #0b1120;
    #       --panel: #111827;
    #       --panel-soft: #172033;
    #       --panel-strong: #1e293b;
    #       --border: #334155;
    #       --border-soft: #243244;
    #       --text: #e5e7eb;
    #       --text-muted: #a8b3c7;
    #       --accent: #38bdf8;
    #       --accent-strong: #2563eb;
    #       --accent-soft: #0f3a5c;
    #       --danger: #fb7185;
    #     }
    #     html {
    #       background: var(--bg);
    #     }
    #     body {
    #       max-width: 1180px;
    #       margin: 0 auto;
    #       padding: 40px 32px 64px;
    #       background: var(--bg);
    #       color: var(--text);
    #       font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    #       line-height: 1.5;
    #       text-align: left;
    #     }
    #     h1, h3, h4 {
    #       color: #f8fafc;
    #     }
    #     h1 {
    #       margin-top: 0;
    #       letter-spacing: 0;
    #     }
    #     h3 {
    #       margin-top: 0;
    #     }
    #     p {
    #       color: var(--text-muted);
    #     }
    #     a {
    #       color: var(--accent);
    #     }
    #     .tab {
    #       display: flex;
    #       flex-wrap: wrap;
    #       gap: 6px;
    #       margin-top: 28px;
    #       padding: 8px;
    #       border: 1px solid var(--border);
    #       border-radius: 8px 8px 0 0;
    #       background-color: var(--panel);
    #     }
    #     .tab button {
    #       background-color: var(--panel-strong);
    #       color: var(--text-muted);
    #       border: 1px solid transparent;
    #       border-radius: 6px;
    #       outline: none;
    #       cursor: pointer;
    #       padding: 12px 14px;
    #       transition: background-color 0.2s, border-color 0.2s, color 0.2s;
    #     }
    #     .tab button:hover {
    #       background-color: var(--accent-soft);
    #       border-color: #1d4ed8;
    #       color: #f8fafc;
    #     }
    #     .tab button.active {
    #       background-color: var(--accent-strong);
    #       border-color: #60a5fa;
    #       color: #ffffff;
    #     }
    #     .tabcontent {
    #       display: none;
    #       padding: 24px;
    #       border: 1px solid var(--border);
    #       border-top: none;
    #       border-radius: 0 0 8px 8px;
    #       background: var(--panel);
    #       box-shadow: 0 18px 60px rgba(0, 0, 0, 0.25);
    #       overflow-x: auto;
    #     }
    #     table {
    #       border-collapse: collapse;
    #       margin: 14px 0 24px;
    #       max-width: 100%;
    #       color: var(--text);
    #       background: var(--panel-soft);
    #       font-size: 0.92rem;
    #     }
    #     th, td {
    #       border: 1px solid var(--border-soft);
    #       padding: 7px 10px;
    #       white-space: nowrap;
    #     }
    #     th {
    #       background: var(--panel-strong);
    #       color: #f8fafc;
    #       font-weight: 600;
    #     }
    #     tr:nth-child(even) td {
    #       background: rgba(148, 163, 184, 0.06);
    #     }
    #     img {
    #       max-width: 100%;
    #       height: auto;
    #       margin: 14px 0 24px;
    #       border: 1px solid var(--border);
    #       border-radius: 6px;
    #       background: #f8fafc;
    #     }
    #     font[color="red"] {
    #       color: var(--danger);
    #     }
    #     </style>
    #     </head>
    #     <body>
    #     <h1>"""
    #         + left_fail_style_tag
    #         + """Expense Forecast Report #"""
    #         + str(report_id)
    #         + right_fail_style_tag
    #         + """</h1>
    #     <p>"""
    #         + start_date
    #         + """ to """
    #         + end_date
    #         + " "
    #         + left_fail_style_tag
    #         + fail_message
    #         + right_fail_style_tag
    #         + " "
    #         + parent_report_text
    #         + """</p>

    #     <div class="tab">
    #       <button class="tablinks active" onclick="openTab(event, 'ForecastParameters')">Forecast Parameters</button>
    #       <button class="tablinks" onclick="openTab(event, 'NetWorth')">Net Worth</button>
    #       <button class="tablinks" onclick="openTab(event, 'NetGainLoss')">Net Gain & Loss</button>
    #       <button class="tablinks" onclick="openTab(event, 'AccountType')">Account Type</button>
    #       <button class="tablinks" onclick="openTab(event, 'Interest')">Interest</button>
    #       <button class="tablinks" onclick="openTab(event, 'Milestones')">Milestones</button>
    #       <button class="tablinks" onclick="openTab(event, 'All')">All</button>
    #       <button class="tablinks" onclick="openTab(event, 'TransactionSchedule')">Transaction Schedule</button>
    #       <button class="tablinks" onclick="openTab(event, 'Sankey')">Sankey</button>
    #       <button class="tablinks" onclick="openTab(event, 'Forecast Results')">Forecast Results</button>
    #     </div>

    #     <div id="ForecastParameters" class="tabcontent">
    #       <h3>Forecast Parameters</h3>
    #       <p>"""
    #         + summary_text
    #         + """</p>
    #       <h3>Accounts</h3>
    #       <p>"""
    #         + account_text
    #         + """</p>
    #       <h3>Budget Items</h3>
    #       <p>"""
    #         + budget_set_text
    #         + """</p>
    #       <h3>Memo Rules</h3>
    #       <p>"""
    #         + memo_rule_text
    #         + """</p>
    #       <h3>Account Milestones</h3>
    #       <p>"""
    #         + account_milestone_text
    #         + """</p>
    #       <h3>Memo Milestones</h3>
    #       <p>"""
    #         + memo_milestone_text
    #         + """</p>
    #       <h3>Composite Milestones</h3>
    #       <p>"""
    #         + composite_milestone_text
    #         + """</p>
    #     </div>

    #     <div id="NetWorth" class="tabcontent">
    #       <h3>Net Worth</h3>
    #       <p>"""
    #         + networth_text
    #         + """</p>
    #       <img src=\""""
    #         + networth_line_plot_path
    #         + """\">
    #     </div>

    #     <div id="NetGainLoss" class="tabcontent">
    #       <h3>Net Gain & Loss</h3>
    #       <p>"""
    #         + net_gain_loss_text
    #         + """</p>
    #       <img src=\""""
    #         + net_gain_loss_line_plot_path
    #         + """\">
    #     </div>

    #     <div id="AccountType" class="tabcontent">
    #       <h3>Account Type</h3>
    #       <p>"""
    #         + account_type_text
    #         + """</p>
    #       <img src=\""""
    #         + accounttype_line_plot_path
    #         + """\">
    #     </div>

    #     <div id="Interest" class="tabcontent">
    #       <h3>Interest</h3>
    #       <p>"""
    #         + interest_text
    #         + """</p>
    #       <img src=\""""
    #         + marginal_interest_line_plot_path
    #         + """\">
    #       """
    #         + interest_table_html
    #         + """
    #     </div>

    #     <div id="Milestones" class="tabcontent">
    #       <h3>Milestones</h3>
    #       <p>"""
    #         + milestone_text
    #         + """</p>
    #       <img src=\""""
    #         + milestone_scatter_plot_path
    #         + """\">
    #       <h4>Account Milestones</h4>
    #       """
    #         + am_result_df.to_html()
    #         + """ <br>
    #       <h4>Memo Milestones</h4>
    #       """
    #         + mm_result_df.to_html()
    #         + """ <br>
    #       <h4>Composite Milestones</h4>
    #       """
    #         + cm_result_df.to_html()
    #         + """ <br>
    #     </div>

    #     <div id="All" class="tabcontent">
    #       <h3>All</h3>
    #       <p>"""
    #         + all_plot_page_text
    #         + """</p>
    #       <img src=\""""
    #         + all_line_plot_path
    #         + """\">
    #     </div>

    #     <div id="TransactionSchedule" class="tabcontent">
    #       <h3>Transaction Schedule</h3>
    #       <p>"""
    #         + transaction_schedule_text
    #         + """</p><br>
    #       Non-essential transactions: <br>
    #       <p>"""
    #         + p2_plus_txns_html_table
    #         + """</p><br><br>
    #       Credit Card Payments: <br>
    #       <p>"""
    #         + cc_payments_html_table
    #         + """</p><br><br>
    #       Loan Payments: <br>
    #       <p>"""
    #         + loan_payment_html_table
    #         + """</p><br><br>
    #       All Transactions: <br>
    #       """
    #         + confirmed_df.to_html()
    #         + """
    #     </div>

    #     <div id="Sankey" class="tabcontent">
    #       <h3>Sankey</h3>
    #       <p>"""
    #         + sankey_text
    #         + """</p>
    #       <img src=\""""
    #         + sankey_path
    #         + """\">
    #     </div>

    #     <div id="Forecast Results" class="tabcontent">
    #       <h3>Forecast Results</h3>
    #       <p>"""
    #         + summary_text
    #         + """</p>
    #       <p>The visualized data are below:</p>
    #       <h4>Forecast #"""
    #         + str(E.unique_id)
    #         + """:</h4>
    #       """
    #         + E.forecast_df.to_html()
    #         + """
    #     </div>

    #     <br>

    #     <script>
    #     function openTab(evt, tabName) {
    #       var i, tabcontent, tablinks;
    #       tabcontent = document.getElementsByClassName("tabcontent");
    #       for (i = 0; i < tabcontent.length; i++) {
    #         tabcontent[i].style.display = "none";
    #       }
    #       tablinks = document.getElementsByClassName("tablinks");
    #       for (i = 0; i < tablinks.length; i++) {
    #         tablinks[i].className = tablinks[i].className.replace(" active", "");
    #       }
    #       document.getElementById(tabName).style.display = "block";
    #       evt.currentTarget.className += " active";
    #     }
    #     document.getElementById("ForecastParameters").style.display = "block";
    #     </script>

    #     </body>
    #     </html>
    #     """
    #     )

    #     with open(html_output_path, "w") as f:
    #         f.write(html_body)
    #     log_in_color(
    #         logger,
    #         "green",
    #         "info",
    #         "Finished writing single forecast report to " + str(html_output_path),
    #     )
    #     return html_output_path

    @staticmethod
    def get_delta_explanation_sentence(column_name: str, delta: Decimal, length_of_forecast_in_days: int) -> str:
        avg = delta / length_of_forecast_in_days
        if delta > 0:
            return f"{column_name} rose by ${delta:,.2f} over {length_of_forecast_in_days} days, averaging ${avg:,.2f} per day."
        elif delta == 0:
            return f"{column_name} did not change."
        else:
            return f"{column_name} fell by ${delta:,.2f} over {length_of_forecast_in_days} days, averaging ${avg:,.2f} per day."

    @staticmethod
    def get_last_row_first_row_delta(df: pd.DataFrame, column_name: str) -> Decimal:
        return Decimal(
            df[column_name].iat[-1]
            - df[column_name].iat[0]
        )

    @staticmethod
    def get_time_elapsed_string(start_ts, end_ts):
        mins = int((end_ts - start_ts).seconds / 60)
        secs = (end_ts - start_ts).seconds % 60
        if mins + secs == 0:
            mic = (end_ts - start_ts).microseconds
            return f"{mic:,} microseconds"
        
        # TODO handle plural of minute(s) and second(s) in get_time_elapsed_string i just don't want to do it rn 
        return f"{mins} minute and {secs} seconds"

    def generateHTMLreport(self, E: ExpenseForecastResult) -> str:
        """
        Generate a self-contained HTML report for one ExpenseForecastResult.

        This method assumes scalar values and pandas DataFrames are available as
        attributes on E. Adapt scalar_value() and dataframe_value() if E exposes
        report data through another interface.
        """

        report_scalars = {}

        report_scalars['scenario_name'] = E.initial_conditions.forecast_name
        report_scalars['unique_id'] = E.unique_id
        report_scalars['date_range'] = str((E.initial_conditions.end_date - E.initial_conditions.start_date).days) + " days : " + E.initial_conditions.start_date.strftime('%Y-%m-%d') + ' to ' + E.initial_conditions.end_date.strftime('%Y-%m-%d')

        length_of_forecast_in_days = (E.initial_conditions.end_date - E.initial_conditions.start_date).days

        net_worth_delta = self.get_last_row_first_row_delta(E.forecast_df, 'Net Worth')

        report_scalars['net_worth_page_text_above_plots']= self.get_delta_explanation_sentence('Net Worth', net_worth_delta, length_of_forecast_in_days)
        report_scalars['net_worth_page_text_below_plots'] = ''

        net_gain_and_loss_page_text_above_plots = '' 
        net_gain_and_loss_page_text_below_plots = ''

        liquid_delta_sent = self.get_delta_explanation_sentence('Liquid Total', net_worth_delta, length_of_forecast_in_days)
        cc_delta_sent = self.get_delta_explanation_sentence('CC Debt Total', net_worth_delta, length_of_forecast_in_days)
        loan_delta_sent = self.get_delta_explanation_sentence('Loan Total', net_worth_delta, length_of_forecast_in_days)
        report_scalars['account_type_page_text_above_plots'] = liquid_delta_sent + '\r\n' + cc_delta_sent + '\r\n' + loan_delta_sent + '\r\n'
        account_type_page_text_below_plots = ''

        interest_page_text_above_plots = '' #TODO for detailed view interest page abobe plot text: in dyanmic sentence, state the average value, dont include start and end values
        interest_page_text_below_plots = ''
        
        sankey_page_text_above_plots = ''
        sankey_page_text_below_plots = ''

        last_day_page_text_above_plots = ''
        last_day_page_text_below_plots = ''

        report_data_frames = {}
        milestone_results = (
            E.milestone_results[0]
            | E.milestone_results[1]
            | E.milestone_results[2]
        )
        forecast_start_date = pd.Timestamp(E.forecast_df["Date"].iloc[0])

        def format_milestone_elapsed_time(date_achieved) -> str:
            elapsed_days = (
                pd.Timestamp(date_achieved).normalize()
                - forecast_start_date.normalize()
            ).days
            if elapsed_days < 365:
                unit = "day" if elapsed_days == 1 else "days"
                return f"{elapsed_days} {unit}"
            elapsed_years = elapsed_days / 365.25
            return f"{elapsed_years:.1f} years"

        report_data_frames["milestone_dates"] = pd.DataFrame(
            [
                {
                    "Time": format_milestone_elapsed_time(date_achieved),
                    "Milestone": milestone_name,
                }
                for milestone_name, date_achieved in sorted(
                    milestone_results.items(),
                    key=lambda item: pd.Timestamp(item[1])
                    if pd.notna(item[1])
                    else pd.Timestamp.max,
                )
                if pd.notna(date_achieved)
            ],
            columns=["Time", "Milestone"],
        )

        initial_conditions = E.initial_conditions
        initial_account_set = initial_conditions.initial_account_set
        initial_budget_set = initial_conditions.initial_budget_set
        initial_memo_rule_set = initial_conditions.initial_memo_rule_set
        milestone_set = E.milestone_set

        report_data_frames["initial_account_set"] = initial_account_set.getAccounts()
        report_data_frames["initial_line_item_set"] = initial_budget_set.getLineItems()
        report_data_frames["initial_memo_rule_set"] = initial_memo_rule_set.getMemoRules()
        report_data_frames["account_milestones"] = milestone_set.getAccountMilestonesDF()
        report_data_frames["memo_milestones"] = milestone_set.getMemoMilestonesDF()
        report_data_frames["composite_milestones"] = milestone_set.getCompositeMilestonesDF()
        report_data_frames["forecast_output"] = E.forecast_df.copy()

        credit_accounts = initial_account_set.getAccounts().loc[
            lambda accounts: accounts["Account_Type"].eq("credit")
        ]
        total_credit_limit = pd.to_numeric(
            credit_accounts["Max_Balance"], errors="coerce"
        ).sum()
        initial_cash_reserve = pd.to_numeric(
            E.forecast_df["Liquid Total"], errors="coerce"
        ).min()
        initial_reserve_credit = total_credit_limit - pd.to_numeric(
            E.forecast_df["CC Debt Total"], errors="coerce"
        ).max()
        final_cash_reserve = float(E.forecast_df["Liquid Total"].iloc[-1])
        final_available_credit = total_credit_limit - float(
            E.forecast_df["CC Debt Total"].iloc[-1]
        )

        def format_report_currency(value) -> str:
            numeric_value = float(value)
            if numeric_value < 0:
                return f"-${abs(numeric_value):,.2f}"
            return f"${numeric_value:,.2f}"

        report_data_frames["margin_metrics"] = pd.DataFrame(
            [
                {
                    "Metric": "Initial Cash Reserve",
                    "Amount": format_report_currency(initial_cash_reserve),
                },
                {
                    "Metric": "Initial Reserve Credit",
                    "Amount": format_report_currency(initial_reserve_credit),
                },
                {
                    "Metric": "Final Cash Reserve",
                    "Amount": format_report_currency(final_cash_reserve),
                },
                {
                    "Metric": "Final Available Credit",
                    "Amount": format_report_currency(final_available_credit),
                },
            ],
            columns=["Metric", "Amount"],
        )

        transaction_schedule = (
            E.confirmed_df.copy()
            if isinstance(E.confirmed_df, pd.DataFrame)
            else initial_budget_set.getLineItemSchedule().iloc[0:0].copy()
        )
        if not transaction_schedule.empty:
            transaction_schedule = transaction_schedule.sort_values(
                ["Date", "Priority", "Memo"],
                kind="stable",
            ).reset_index(drop=True)

        report_data_frames["all_transactions"] = transaction_schedule.copy()
        report_data_frames["non_essential_transactions"] = transaction_schedule.loc[
            transaction_schedule["Priority"].gt(1)
        ].reset_index(drop=True)

        account_types = dict(
            zip(
                initial_account_set.getAccounts()["Name"],
                initial_account_set.getAccounts()["Account_Type"],
            )
        )
        credit_transaction_indices = []
        loan_transaction_indices = []
        for transaction_index, transaction in transaction_schedule.iterrows():
            memo_rule = initial_memo_rule_set.findMatchingMemoRule(
                transaction["Memo"],
                transaction["Priority"],
            )
            destination_type = account_types.get(memo_rule.account_to)
            if destination_type == "credit":
                credit_transaction_indices.append(transaction_index)
            elif (
                destination_type == "loan"
                or memo_rule.account_to == "ALL_LOANS"
            ):
                loan_transaction_indices.append(transaction_index)

        report_data_frames["credit_card_payments"] = transaction_schedule.loc[
            credit_transaction_indices
        ].reset_index(drop=True)
        loan_payment_rows = []
        for transaction_index in loan_transaction_indices:
            transaction = transaction_schedule.loc[transaction_index]
            memo_rule = initial_memo_rule_set.findMatchingMemoRule(
                transaction["Memo"],
                transaction["Priority"],
            )
            loan_payment_rows.append(
                {
                    "Date": transaction["Date"],
                    "Account": memo_rule.account_to,
                    "Payment Type": "Scheduled",
                    "Amount": float(transaction["Amount"]),
                }
            )

        loan_minimum_payment_pattern = re.compile(
            r"^LOAN MIN PAYMENT \("
            r"(?P<Account>[^:]+):\s*"
            r"(?:Interest|Principal Balance)\s*"
            r"-\$(?P<Amount>[\d,]+(?:\.\d+)?)\)$"
        )
        minimum_payment_components = []
        for _, forecast_row in E.forecast_df.iterrows():
            for directive in str(forecast_row["Memo Directives"]).split(";"):
                match = loan_minimum_payment_pattern.match(directive.strip())
                if match is None:
                    continue
                minimum_payment_components.append(
                    {
                        "Date": forecast_row["Date"],
                        "Account": match.group("Account").strip(),
                        "Amount": float(
                            match.group("Amount").replace(",", "")
                        ),
                    }
                )

        if minimum_payment_components:
            minimum_payments = (
                pd.DataFrame(minimum_payment_components)
                .groupby(["Date", "Account"], as_index=False, sort=True)["Amount"]
                .sum()
            )
            minimum_payments["Payment Type"] = "Minimum"
            loan_payment_rows.extend(
                minimum_payments[
                    ["Date", "Account", "Payment Type", "Amount"]
                ].to_dict(orient="records")
            )

        report_data_frames["loan_payments"] = (
            pd.DataFrame(
                loan_payment_rows,
                columns=["Date", "Account", "Payment Type", "Amount"],
            )
            .sort_values(["Date", "Account", "Payment Type"], kind="stable")
            .reset_index(drop=True)
        )

        credit_card_interest_rows = []
        credit_card_interest_pattern = re.compile(
            r"^CC INTEREST \((?P<Account>[^:]+):.*?\+\$(?P<Amount>[\d,]+(?:\.\d+)?)\)$"
        )
        for _, forecast_row in E.forecast_df.iterrows():
            for directive in str(forecast_row["Memo Directives"]).split(";"):
                match = credit_card_interest_pattern.match(directive.strip())
                if match is None:
                    continue
                credit_card_interest_rows.append(
                    {
                        "Date": forecast_row["Date"],
                        "Account": match.group("Account").strip(),
                        "Amount": float(match.group("Amount").replace(",", "")),
                    }
                )

        report_data_frames["credit_card_interest_payments"] = pd.DataFrame(
            credit_card_interest_rows,
            columns=["Date", "Account", "Amount"],
        )
        
        
        forecast_metadata = pd.DataFrame({
            'Start':[E.start_ts], 'End':[E.end_ts], 'Elapsed':[self.get_time_elapsed_string(E.start_ts, E.end_ts)]
        }).T
        forecast_metadata['Stat'] = ['Start', 'End', 'Elapsed']
        forecast_metadata = forecast_metadata.rename(columns={forecast_metadata.columns[0]: "Value"}).loc[:, ["Stat", "Value"]]
        
        report_data_frames['forecast_metadata'] = forecast_metadata

        last_day = E.forecast_df.tail(1).T
        summary_rows = [
            row
            for row in last_day.index
            if not (
                row.startswith("Date")
                or row.startswith("Memo")
                or row.startswith("Memo Directive")
                or row.startswith("Next Income Date")
                or row.startswith("Marginal Interest")
                or row.startswith("Net Gain")
                or row.startswith("Net Loss")
                or ':' in row #TODO change HTML report logic to filter out sub accounts without checking for : in name
            )
        ]
        final_account_balances = (
            last_day
            .loc[summary_rows]
            .reset_index(names="Account")
            .rename(columns={last_day.columns[0]: "Balance"})
        )
        report_data_frames["final_account_balances"] = final_account_balances

        # Build one chart point per achievement date and account-balance value.
        # Milestones sharing both are combined into one tooltip; milestones on
        # the same date with different balances remain separate points.
        account_milestones_by_name = {
            milestone.milestone_name: milestone
            for milestone in (getattr(E.milestone_set, "account_milestones", None) or [])
        }
        account_milestone_results = (
            E.milestone_results[0]
            if isinstance(E.milestone_results, (list, tuple)) and E.milestone_results
            else {}
        )
        forecast_dates = pd.to_datetime(E.forecast_df["Date"]).dt.normalize()
        milestones_by_point: dict[tuple[str, float], list[dict[str, Any]]] = {}

        for milestone_name, achieved_date in account_milestone_results.items():
            if achieved_date in (None, "None"):
                continue

            milestone = account_milestones_by_name.get(milestone_name)
            if milestone is None or milestone.account_name not in E.forecast_df.columns:
                continue

            normalized_date = pd.Timestamp(achieved_date).normalize()
            matching_rows = E.forecast_df.loc[forecast_dates == normalized_date]
            if matching_rows.empty:
                continue

            balance = matching_rows[milestone.account_name].iloc[0]
            if pd.isna(balance):
                continue

            date_key = normalized_date.strftime("%Y-%m-%d")
            balance_value = float(balance)
            milestones_by_point.setdefault((date_key, balance_value), []).append({
                "name": str(milestone_name),
                "account": str(milestone.account_name),
                "balance": balance_value,
            })

        account_milestone_achieved_dates = pd.DataFrame([
            {
                "Date": achieved_date,
                "Amount": balance,
                "Milestones": milestones,
            }
            for (achieved_date, balance), milestones
            in sorted(milestones_by_point.items())
        ], columns=["Date", "Amount", "Milestones"])
        report_data_frames["account_milestone_achieved_dates"] = (
            account_milestone_achieved_dates
        )

        

        def scalar_value(name: str, default: str = "") -> str:
            """
            Return an escaped scalar report value.

            Examples
            --------
            $scenario_name
                scalar_value("scenario_name")

            $net_worth_page_text_above_plots
                scalar_value("net_worth_page_text_above_plots")
            """
            value: Any = report_scalars.get(name, default)

            if value is None:
                return ""

            return escape(str(value))

        def dataframe_value(name: str) -> pd.DataFrame | None:
            """
            Return a DataFrame stored on E, or None when unavailable.
            """
            value: Any = report_data_frames.get(name) #TODO return type should be pd.DataFrame not sure how to express that

            if isinstance(value, pd.DataFrame):
                return value

            return None

        # TODO add an optional parameter to F.render_table to indicate which columns should be money format
        def render_table(
            name: str,
            *,
            empty_message: str = "No data available.",
        ) -> str:
            """
            Render a named DataFrame using the shared report-table CSS classes.
            """
            dataframe = dataframe_value(name)

            if dataframe is None or dataframe.empty:
                return (
                    '<div class="report-table-empty">'
                    f"{escape(empty_message)}"
                    "</div>"
                )

            return dataframe.to_html(
                index=False,
                border=0,
                classes=[
                    "report-table",
                    f"report-table-{name.replace('_', '-')}",
                ],
                justify="left",
                escape=True,
            )

        def render_table_card(
            title: str,
            dataframe_name: str,
            *,
            section_class: str = "",
        ) -> str:
            """
            Render one titled table card.
            """
            additional_class = f" {section_class}" if section_class else ""

            return f"""
                <section class="table-card{additional_class}">
                    <h2 class="table-card-title">{escape(title)}</h2>
                    <div class="table-scroll-container">
                        {render_table(dataframe_name)}
                    </div>
                </section>
            """

        def render_detailed_page(
            page_id: str,
            page_title: str,
            primary_table_name: str | None = None,
            additional_sections: str = "",
            show_plot: bool = True,
        ) -> str:
            """
            Render one detailed-view navbar page.
            """
            active_class = " is-active" if page_id == "parameters" else ""

            primary_table_html = ""

            if primary_table_name is not None:
                primary_table_html = f"""
                    <section class="detailed-primary-table">
                        <div class="table-scroll-container">
                            {render_table(primary_table_name)}
                        </div>
                    </section>
                """

            plot_html = ""
            if show_plot:
                line_chart_html = ""
                if page_id in {
                    "net_worth",
                    "net_gain_and_loss",
                    "account_type",
                    "interest",
                }:
                    line_chart_html = f"""
                        <div class="detail-line-chart-container">
                            <svg
                                id="{escape(page_id)}-chart"
                                class="hero-chart detail-line-chart"
                                role="img"
                                aria-label="{escape(page_title)} line chart"
                            ></svg>
                            <div
                                id="{escape(page_id)}-chart-tooltip"
                                class="hero-chart-tooltip"
                                hidden
                            ></div>
                        </div>
                    """
                plot_html = f"""
                    <div
                        id="{escape(page_id)}-plots"
                        class="detail-page-plots"
                        data-plot-page="{escape(page_id)}"
                    >
                        {line_chart_html}
                    </div>
                """

            return f"""
                <section
                    id="detail-page-{escape(page_id)}"
                    class="detail-page{active_class}"
                    data-detail-page="{escape(page_id)}"
                    aria-labelledby="detail-tab-{escape(page_id)}"
                >
                    <header class="detail-page-header">
                        <h2 class="detail-page-title">
                            {escape(page_title)}
                        </h2>
                    </header>

                    <div class="detail-page-text detail-page-text-above">
                        {scalar_value(f"{page_id}_page_text_above_plots")}
                    </div>

                    {plot_html}

                    <div class="detail-page-text detail-page-text-below">
                        {scalar_value(f"{page_id}_page_text_below_plots")}
                    </div>

                    {primary_table_html}

                    <div class="detailed-additional-sections">
                        {additional_sections}
                    </div>
                </section>
            """

        parameters_sections = "".join(
            [
                render_table_card(
                    "Account Set",
                    "initial_account_set",
                ),
                render_table_card(
                    "Line Items",
                    "initial_line_item_set",
                ),
                render_table_card(
                    "Memo Rules",
                    "initial_memo_rule_set",
                ),
                render_table_card(
                    "Composite Milestones",
                    "composite_milestones",
                ),
                render_table_card(
                    "Account Milestones",
                    "account_milestones",
                ),
                render_table_card(
                    "Memo Milestones",
                    "memo_milestones",
                ),
            ]
        )

        transaction_schedule_sections = "".join(
            [
                render_table_card(
                    "Non-Essential Transactions",
                    "non_essential_transactions",
                ),
                render_table_card(
                    "Credit Card Payments",
                    "credit_card_payments",
                ),
                render_table_card(
                    "Credit Card Interest Payments",
                    "credit_card_interest_payments",
                ),
                render_table_card(
                    "Loan Payments",
                    "loan_payments",
                ),
                render_table_card(
                    "All Transactions",
                    "all_transactions",
                ),
            ]
        )

        detailed_pages = "".join(
            [
                render_detailed_page(
                    "parameters",
                    "Parameters",
                    additional_sections=parameters_sections,
                    show_plot=False,
                ),
                render_detailed_page(
                    "output_data",
                    "Output Data",
                    additional_sections=render_table_card(
                        "Forecast Output",
                        "forecast_output",
                    ),
                    show_plot=False,
                ),
                render_detailed_page(
                    "net_worth",
                    "Net Worth",
                    "net_worth",
                ),
                render_detailed_page(
                    "net_gain_and_loss",
                    "Net Gain & Loss",
                    "net_gain_and_loss",
                ),
                render_detailed_page(
                    "account_type",
                    "Account Type",
                    "account_type",
                ),
                render_detailed_page(
                    "interest",
                    "Interest",
                    "interest",
                ),
                render_detailed_page(
                    "milestones",
                    "Milestones",
                    "milestones",
                ),
                render_detailed_page(
                    "sankey",
                    "Sankey",
                    "sankey",
                ),
                render_detailed_page(
                    "all",
                    "All",
                    "all",
                ),
                render_detailed_page(
                    "transaction_schedule",
                    "Transaction Schedule",
                    additional_sections=transaction_schedule_sections,
                    show_plot=False,
                ),
                render_detailed_page(
                    "last_day",
                    "Last Day",
                    "last_day",
                ),
            ]
        )

        ### JS Plots

        def dataframe_to_chart_records(
            dataframe: pd.DataFrame | None,
            date_column: str = "Date",
        ) -> list[dict[str, Any]]:
            """
            Convert a DataFrame into JSON-safe records for D3.

            Date values are serialized as ISO-formatted strings. Missing values become
            null in the resulting JSON.
            """
            if dataframe is None or dataframe.empty:
                return []

            chart_dataframe = dataframe.copy()

            if date_column in chart_dataframe.columns:
                chart_dataframe[date_column] = pd.to_datetime(
                    chart_dataframe[date_column]
                ).dt.strftime("%Y-%m-%d")

            chart_dataframe = chart_dataframe.astype(object).where(
                pd.notna(chart_dataframe),
                None,
            )

            return chart_dataframe.to_dict(orient="records")

        hero_chart_options = {
            "date_column": "Date",
            "primary_series": "Checking",

            "line_animation_ms": 1800,
            "respect_reduced_motion": False,

            "line_styles": {
                "Checking": {
                    "color": "#2f7d4a",
                    "width": 3.5,
                },
                "Savings": {
                    "color": "#8a8a8f",
                    "width": 2,
                },
                "Credit Card": {
                    "color": "#b65a5a",
                    "width": 2,
                },
            },

            "default_line_color": "#7a7a80",
            "default_line_width": 2,

            "today_color": "#2878d0",
            "transaction_color": "#929298",

            "line_animation_ms": 1800,
            "transaction_delay_ms": 150,
            "transaction_stagger_ms": 130,

            "currency_symbol": "$",
        }


        # hero_chart_dataframe = report_data_frames.get("hero_chart")
        # report_data_frames["hero_chart"] = pd.DataFrame( #example
        
        hero_chart_dataframe = E.forecast_df.loc[:, ["Date", "Checking"]]
        
        # hero_chart_dataframe = pd.DataFrame(
        #     {
        #         "Date": [
        #             "2026-07-01",
        #             "2026-07-15",
        #             "2026-08-01",
        #             "2026-09-01",
        #         ],
        #         "Checking": [
        #             4200,
        #             3800,
        #             5100,
        #             4600,
        #         ],
        #         "Savings": [
        #             9000,
        #             9200,
        #             9400,
        #             9600,
        #         ],
        #     }
        # )


        line_items_dataframe = E.initial_conditions.initial_budget_set.getLineItems()
        once_memos = set(
            line_items_dataframe.loc[
                line_items_dataframe["interval"].eq("once"), "Memo"
            ]
        )
        confirmed_transactions = self._report_confirmed_df(E)
        highlighted_transactions_dataframe = confirmed_transactions.loc[
            confirmed_transactions["Memo"].isin(once_memos)
            | confirmed_transactions["Priority"].gt(1),
            ["Date", "Amount", "Memo"],
        ].reset_index(drop=True)

        date_column = hero_chart_options.get("date_column", "Date")

        hero_chart_payload = {
            "series_data": dataframe_to_chart_records(
                hero_chart_dataframe,
                date_column=date_column,
            ),
            "highlighted_transactions": dataframe_to_chart_records(
                highlighted_transactions_dataframe,
                date_column="Date",
            ),
            "account_milestone_achieved_dates": dataframe_to_chart_records(
                dataframe_value("account_milestone_achieved_dates"),
                date_column="Date",
            ),
            "options": hero_chart_options,
        }

        hero_chart_json = json.dumps(
            hero_chart_payload,
            ensure_ascii=False,
            default=str,
        ).replace("</", "<\\/")

        account_type_columns = [
            column
            for column in ["Liquid Total", "CC Debt Total", "Loan Total"]
            if column in E.forecast_df.columns
        ]
        account_type_dataframe = E.forecast_df.loc[
            :, ["Date", *account_type_columns]
        ].copy()
        investment_names = initial_account_set.getAccounts().loc[
            lambda accounts: accounts["Account_Type"].eq("investment"),
            "Name",
        ].tolist()
        investment_names = [
            name for name in investment_names if name in E.forecast_df.columns
        ]
        if investment_names:
            account_type_dataframe["Investment Total"] = E.forecast_df[
                investment_names
            ].sum(axis=1)

        net_gain_loss_dataframe = E.forecast_df.loc[
            :, ["Date", "Net Gain", "Net Loss"]
        ].copy()
        net_gain_loss_dataframe["Net Loss"] = -net_gain_loss_dataframe[
            "Net Loss"
        ].abs()

        detail_chart_payload = {
            "net_worth": {
                "series_data": dataframe_to_chart_records(
                    E.forecast_df.loc[:, ["Date", "Net Worth"]]
                ),
                "options": {
                    "line_styles": {"Net Worth": {"color": "#2878d0"}},
                },
            },
            "net_gain_and_loss": {
                "series_data": dataframe_to_chart_records(net_gain_loss_dataframe),
                "options": {
                    "symmetric_zero": True,
                    "absolute_tooltip_series": ["Net Loss"],
                    "line_styles": {
                        "Net Gain": {"color": "#268a51"},
                        "Net Loss": {"color": "#c94747"},
                    },
                },
            },
            "account_type": {
                "series_data": dataframe_to_chart_records(account_type_dataframe),
                "options": {
                    "line_styles": {
                        "Liquid Total": {"color": "#2878d0"},
                        "CC Debt Total": {"color": "#c94747"},
                        "Loan Total": {"color": "#a05a9c"},
                        "Investment Total": {"color": "#268a51"},
                    },
                },
            },
            "interest": {
                "series_data": dataframe_to_chart_records(
                    E.forecast_df.loc[:, ["Date", "Marginal Interest"]]
                ),
                "options": {
                    "line_styles": {
                        "Marginal Interest": {"color": "#c47a24"},
                    },
                },
            },
        }
        detail_chart_json = json.dumps(
            detail_chart_payload,
            ensure_ascii=False,
            default=str,
        ).replace("</", "<\\/")

        html = f"""<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">

            <meta
                name="viewport"
                content="width=device-width, initial-scale=1.0"
            >

            <title>
                {scalar_value("scenario_name", "Expense Forecast Report")}
            </title>

            <!--
            ========================================================================
            REPORT DESIGN VARIABLES

            Change these variables to adjust the report's typography, colors,
            spacing, table density, content width, and other repeated design values.
            ========================================================================
            -->
            <style>
                :root {{
                    /* Typography */
                    --report-font-family:
                        Inter,
                        ui-sans-serif,
                        system-ui,
                        -apple-system,
                        BlinkMacSystemFont,
                        "Segoe UI",
                        sans-serif;

                    --report-monospace-font-family:
                        "SFMono-Regular",
                        Consolas,
                        "Liberation Mono",
                        monospace;

                    --report-title-font-size: 2rem;
                    --report-subtitle-font-size: 0.92rem;
                    --report-date-range-font-size: 0.78rem;
                    --report-body-font-size: 0.95rem;
                    --report-small-font-size: 0.78rem;

                    /* Colors */
                    --report-page-background: #f7f7f5;
                    --report-surface-color: #ffffff;
                    --report-text-color: #1d1d1f;
                    --report-muted-text-color: #77777d;
                    --report-border-color: #dedee2;
                    --report-soft-border-color: #ececef;
                    --report-hover-color: #f2f2f3;
                    --report-selected-color: #e8e8eb;
                    --report-accent-color: #315c72;
                    --report-accent-text-color: #ffffff;

                    /* Page layout */
                    --report-page-max-width: 1500px;
                    --report-page-side-padding: clamp(24px, 4vw, 72px);
                    --report-page-top-padding: 42px;
                    --report-section-gap: 34px;

                    /*
                    Header width is deliberately symmetrical.

                    The left scenario block occupies one column. A comparison report
                    can place the second scenario block in the matching right column
                    without shifting the page's visual center.
                    */
                    --report-header-side-column-width: minmax(220px, 1fr);
                    --report-header-center-column-width: minmax(180px, 1.15fr);

                    /* Hero chart */
                    --hero-chart-height: clamp(390px, 47vh, 650px);
                    --hero-chart-max-width: 1240px;
                    --hero-chart-background: transparent;

                    /* Buttons */
                    --view-toggle-height: 38px;
                    --view-toggle-horizontal-padding: 22px;
                    --view-toggle-border-radius: 999px;

                    /* Summary table layout */
                    --summary-table-column-gap: 26px;
                    --summary-table-row-gap: 28px;

                    /*
                    TABLE DENSITY CONTROL

                    Increase these values for a more spacious table.
                    Decrease them for a denser table.
                    */
                    --report-table-cell-padding-vertical: 11px;
                    --report-table-cell-padding-horizontal: 14px;
                    --report-table-row-line-height: 1.4;

                    --report-table-card-padding: 20px;
                    --report-table-card-border-radius: 10px;
                    --report-table-card-min-height: 120px;

                    /* Detailed view */
                    --detail-navbar-height: 48px;
                    --detail-content-max-width: 1240px;
                    --detail-section-spacing: 38px;
                }}

                * {{
                    box-sizing: border-box;
                }}

                html {{
                    background: var(--report-page-background);
                    color: var(--report-text-color);
                    font-family: var(--report-font-family);
                }}

                body {{
                    min-width: 320px;
                    margin: 0;
                    background: var(--report-page-background);
                    color: var(--report-text-color);
                    font-size: var(--report-body-font-size);
                }}

                button,
                input,
                select,
                textarea {{
                    font: inherit;
                }}

                button {{
                    color: inherit;
                }}

                .report-page {{
                    width: min(
                        100%,
                        calc(
                            var(--report-page-max-width) +
                            2 * var(--report-page-side-padding)
                        )
                    );
                    min-height: 100vh;
                    margin: 0 auto;
                    padding:
                        var(--report-page-top-padding)
                        var(--report-page-side-padding)
                        72px;
                }}

                /*
                ====================================================================
                REPORT HEADER
                ====================================================================
                */

                .report-header {{
                    display: grid;
                    grid-template-columns:
                        var(--report-header-side-column-width)
                        var(--report-header-center-column-width)
                        var(--report-header-side-column-width);
                    align-items: start;
                    width: 100%;
                    margin-bottom: 18px;
                }}

                .scenario-identity {{
                    min-width: 0;
                }}

                .scenario-identity-left {{
                    grid-column: 1;
                    justify-self: start;
                    text-align: left;
                }}

                /*
                Reserved for future comparison reports.

                Add a second .scenario-identity element with this class. Because the
                header uses symmetrical side columns, it will mirror the first
                scenario without changing the central page layout.
                */
                .scenario-identity-right {{
                    grid-column: 3;
                    justify-self: end;
                    text-align: right;
                }}

                .scenario-name {{
                    margin: 0;
                    font-size: var(--report-title-font-size);
                    font-weight: 650;
                    line-height: 1.12;
                    letter-spacing: -0.025em;
                }}

                .scenario-unique-id {{
                    margin: 7px 0 0;
                    font-family: var(--report-monospace-font-family);
                    font-size: var(--report-subtitle-font-size);
                    font-weight: 500;
                    line-height: 1.25;
                    letter-spacing: 0.015em;
                    white-space: nowrap;
                }}

                .scenario-date-range {{
                    margin: 6px 0 0;
                    color: var(--report-muted-text-color);
                    font-size: var(--report-date-range-font-size);
                    font-weight: 450;
                    line-height: 1.3;
                }}

                /*
                ====================================================================
                HERO CHART
                ====================================================================
                */

                .hero-section {{
                    width: 100%;
                }}

                .hero-chart-container {{
                    position: relative;
                    display: flex;
                    align-items: stretch;
                    justify-content: center;
                    width: min(100%, var(--hero-chart-max-width));
                    height: var(--hero-chart-height);
                    margin: 0 auto;
                    background: var(--hero-chart-background);
                }}

                .hero-chart {{
                    display: block;
                    width: 100%;
                    height: 100%;
                    overflow: visible;
                }}

                .hero-chart-placeholder {{
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    width: 100%;
                    min-height: 100%;
                    border-bottom: 1px solid var(--report-soft-border-color);
                    color: var(--report-muted-text-color);
                    font-size: var(--report-small-font-size);
                    letter-spacing: 0.04em;
                    text-transform: uppercase;
                }}

                /*
                ====================================================================
                SUMMARY / DETAILED VIEW TOGGLE
                ====================================================================
                */

                .view-toggle-row {{
                    display: flex;
                    justify-content: center;
                    width: 100%;
                    margin: 18px 0 var(--report-section-gap);
                }}

                .view-toggle-button {{
                    min-height: var(--view-toggle-height);
                    padding:
                        0
                        var(--view-toggle-horizontal-padding);
                    border: 1px solid var(--report-border-color);
                    border-radius: var(--view-toggle-border-radius);
                    background: var(--report-surface-color);
                    cursor: pointer;
                    transition:
                        background-color 150ms ease,
                        border-color 150ms ease,
                        transform 150ms ease;
                }}

                .view-toggle-button:hover {{
                    border-color: var(--report-muted-text-color);
                    background: var(--report-hover-color);
                }}

                .view-toggle-button:active {{
                    transform: translateY(1px);
                }}

                .view-toggle-button:focus-visible,
                .detail-nav-button:focus-visible {{
                    outline: 3px solid color-mix(
                        in srgb,
                        var(--report-accent-color) 32%,
                        transparent
                    );
                    outline-offset: 3px;
                }}

                /*
                ====================================================================
                SUMMARY TABLE GRID
                ====================================================================
                */

                .summary-view {{
                    display: block;
                }}

                .summary-view[hidden],
                .detailed-view[hidden] {{
                    display: none;
                }}

                .summary-table-row {{
                    display: grid;
                    align-items: stretch;
                    gap:
                        var(--summary-table-row-gap)
                        var(--summary-table-column-gap);
                    width: 100%;
                }}

                .summary-table-row-primary {{
                    grid-template-columns: repeat(3, minmax(0, 1fr));
                }}

                .summary-table-row-secondary {{
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                    max-width: calc(
                        (
                            2 * (
                                100% - 2 * var(--summary-table-column-gap)
                            )
                        ) / 3 + var(--summary-table-column-gap)
                    );
                    margin-top: var(--summary-table-row-gap);
                }}

                /*
                Each table card stretches to the height of the tallest card in its
                grid row. This creates the requested aligned 1 × 3 rectangle.
                */
                .table-card {{
                    display: flex;
                    flex-direction: column;
                    min-width: 0;
                    min-height: var(--report-table-card-min-height);
                    padding: var(--report-table-card-padding);
                    border: 1px solid var(--report-soft-border-color);
                    border-radius: var(--report-table-card-border-radius);
                    background: var(--report-surface-color);
                }}

                .table-card-title {{
                    margin: 0 0 16px;
                    font-size: 0.94rem;
                    font-weight: 650;
                    line-height: 1.25;
                    letter-spacing: -0.01em;
                }}

                .table-scroll-container {{
                    width: 100%;
                    min-width: 0;
                    overflow-x: auto;
                }}

                /*
                ====================================================================
                SHARED TABLE STYLING
                ====================================================================

                The primary table-density variables are defined in :root:
                    --report-table-cell-padding-vertical
                    --report-table-cell-padding-horizontal
                    --report-table-row-line-height
                */

                .report-table {{
                    width: 100%;
                    border-collapse: collapse;
                    border-spacing: 0;
                    font-size: 0.86rem;
                    line-height: var(--report-table-row-line-height);
                }}

                .report-table thead th {{
                    padding:
                        var(--report-table-cell-padding-vertical)
                        var(--report-table-cell-padding-horizontal);
                    border-bottom: 1px solid var(--report-border-color);
                    color: var(--report-muted-text-color);
                    font-size: 0.74rem;
                    font-weight: 650;
                    letter-spacing: 0.035em;
                    text-align: left;
                    text-transform: uppercase;
                    vertical-align: bottom;
                    white-space: nowrap;
                }}

                .report-table tbody td {{
                    padding:
                        var(--report-table-cell-padding-vertical)
                        var(--report-table-cell-padding-horizontal);
                    border-bottom: 1px solid var(--report-soft-border-color);
                    text-align: left;
                    vertical-align: top;
                }}

                .report-table tbody tr:last-child td {{
                    border-bottom: 0;
                }}

                .report-table tbody tr:hover {{
                    background: var(--report-hover-color);
                }}

                /*
                Keep the raw forecast output compact vertically. The final two
                columns are Memo Directives and Memo, which are intentionally
                wide and horizontally scrollable instead of wrapping.
                */
                .report-table-forecast-output th,
                .report-table-forecast-output td {{
                    white-space: nowrap;
                }}

                .report-table-forecast-output th:nth-last-child(2),
                .report-table-forecast-output td:nth-last-child(2) {{
                    min-width: 1200px;
                }}

                .report-table-forecast-output th:last-child,
                .report-table-forecast-output td:last-child {{
                    min-width: 720px;
                }}

                .report-table-empty {{
                    display: flex;
                    align-items: center;
                    min-height: 58px;
                    color: var(--report-muted-text-color);
                    font-size: var(--report-small-font-size);
                }}

                /*
                ====================================================================
                DETAILED VIEW
                ====================================================================
                */

                .detailed-view {{
                    width: 100%;
                }}

                .detail-navbar-container {{
                    position: sticky;
                    top: 0;
                    z-index: 10;
                    width: 100%;
                    margin-bottom: var(--detail-section-spacing);
                    padding: 8px 0;
                    background:
                        color-mix(
                            in srgb,
                            var(--report-page-background) 94%,
                            transparent
                        );
                    backdrop-filter: blur(10px);
                }}

                .detail-navbar {{
                    display: flex;
                    align-items: center;
                    width: 100%;
                    min-height: var(--detail-navbar-height);
                    overflow-x: auto;
                    border-bottom: 1px solid var(--report-border-color);
                    scrollbar-width: thin;
                    justify-content: center;
                }}

                .detail-nav-button {{
                    flex: 0 0 auto;
                    min-height: var(--detail-navbar-height);
                    padding: 0 15px;
                    border: 0;
                    border-bottom: 2px solid transparent;
                    background: transparent;
                    color: var(--report-muted-text-color);
                    cursor: pointer;
                    font-size: 0.83rem;
                    font-weight: 550;
                    white-space: nowrap;
                }}

                .detail-nav-button:hover {{
                    color: var(--report-text-color);
                    background: var(--report-hover-color);
                }}

                .detail-nav-button.is-active {{
                    border-bottom-color: var(--report-accent-color);
                    color: var(--report-text-color);
                }}

                .detail-content {{
                    width: min(100%, var(--detail-content-max-width));
                    margin: 0 auto;
                }}

                .detail-page {{
                    display: none;
                    width: 100%;
                }}

                .detail-page.is-active {{
                    display: block;
                }}

                .detail-page-header {{
                    margin-bottom: 22px;
                }}

                .detail-page-title {{
                    margin: 0;
                    font-size: 1.55rem;
                    font-weight: 650;
                    letter-spacing: -0.02em;
                }}

                .detail-page-text {{
                    max-width: 940px;
                    line-height: 1.65;
                }}

                .detail-page-text:empty {{
                    display: none;
                }}

                .detail-page-text-above {{
                    margin-bottom: 26px;
                }}

                .detail-page-text-below {{
                    margin-top: 26px;
                }}

                .detail-page-plots {{
                    width: 100%;
                    min-height: 320px;
                    border-bottom: 1px solid var(--report-soft-border-color);
                }}

                .detail-line-chart-container {{
                    position: relative;
                    width: 100%;
                    height: clamp(390px, 47vh, 650px);
                }}

                .detail-line-chart {{
                    width: 100%;
                    height: 100%;
                }}

                .detailed-primary-table {{
                    margin-top: var(--detail-section-spacing);
                }}

                .detailed-additional-sections {{
                    display: grid;
                    grid-template-columns: minmax(0, 1fr);
                    gap: var(--detail-section-spacing);
                    margin-top: var(--detail-section-spacing);
                }}

                .detailed-table-section {{
                    min-width: 0;
                    padding-top: 4px;
                }}

                .detailed-table-section-title {{
                    margin: 0 0 14px;
                    font-size: 1rem;
                    font-weight: 650;
                    letter-spacing: -0.01em;
                }}

                /*
                ====================================================================
                RESPONSIVE LAYOUT
                ====================================================================
                */

                @media (max-width: 1050px) {{
                    .summary-table-row-primary {{
                        grid-template-columns: repeat(2, minmax(0, 1fr));
                    }}

                    .summary-table-row-primary .table-card:last-child {{
                        grid-column: 1 / -1;
                    }}

                    .summary-table-row-secondary {{
                        max-width: none;
                    }}
                }}

                @media (max-width: 760px) {{
                    :root {{
                        --report-page-side-padding: 18px;
                        --report-page-top-padding: 26px;
                        --hero-chart-height: 380px;
                    }}

                    .report-header {{
                        grid-template-columns: 1fr;
                        gap: 20px;
                    }}

                    .scenario-identity-left,
                    .scenario-identity-right {{
                        grid-column: 1;
                        justify-self: start;
                        text-align: left;
                    }}

                    .summary-table-row-primary,
                    .summary-table-row-secondary {{
                        grid-template-columns: minmax(0, 1fr);
                        max-width: none;
                    }}

                    .summary-table-row-primary .table-card:last-child {{
                        grid-column: auto;
                    }}

                    .report-table {{
                        min-width: 540px;
                    }}
                }}

                @media (prefers-reduced-motion: reduce) {{
                    *,
                    *::before,
                    *::after {{
                        scroll-behavior: auto !important;
                        transition-duration: 0.01ms !important;
                        animation-duration: 0.01ms !important;
                        animation-iteration-count: 1 !important;
                    }}
                }}

                /*
                Added for Hero Chart
                */

                .hero-axis {{
                    color: var(--report-muted-text-color);
                    font-family: var(--report-font-family);
                    font-size: 0.76rem;
                }}

                .hero-axis path,
                .hero-axis line {{
                    stroke: var(--report-border-color);
                }}

                .hero-grid line {{
                    stroke: var(--report-soft-border-color);
                    stroke-dasharray: 2 4;
                }}

                .hero-grid path {{
                    display: none;
                }}

                .hero-series-line {{
                    fill: none;
                    stroke-linecap: round;
                    stroke-linejoin: round;
                }}

                .hero-today-guide {{
                    stroke: var(--report-border-color);
                    stroke-width: 1;
                    stroke-dasharray: 3 5;
                }}

                .hero-today-dot {{
                    cursor: pointer;
                    transform-box: fill-box;
                    transform-origin: center;
                    animation: hero-today-pulse 2.8s ease-in-out infinite;
                }}

                .hero-transaction-dot {{
                    cursor: pointer;
                }}

                .hero-milestone-dot {{
                    cursor: pointer;
                }}

                .hero-chart-tooltip {{
                    position: absolute;
                    z-index: 20;
                    min-width: 150px;
                    max-width: 260px;
                    padding: 10px 12px;
                    border: 1px solid var(--report-border-color);
                    border-radius: 8px;
                    background: var(--report-surface-color);
                    box-shadow: 0 8px 24px rgb(0 0 0 / 10%);
                    color: var(--report-text-color);
                    font-size: 0.78rem;
                    line-height: 1.5;
                    pointer-events: none;
                }}

                .hero-chart-tooltip-row {{
                    display: flex;
                    justify-content: space-between;
                    gap: 18px;
                }}

                .hero-chart-tooltip-label {{
                    color: var(--report-muted-text-color);
                }}

                .hero-chart-tooltip-value {{
                    font-weight: 600;
                    text-align: right;
                }}

                @keyframes hero-today-pulse {{
                    0%,
                    100% {{
                        transform: scale(1);
                        opacity: 1;
                    }}

                    50% {{
                        transform: scale(1.45);
                        opacity: 0.62;
                    }}
                }}

                @media (prefers-reduced-motion: reduce) {{
                    .hero-today-dot {{
                        animation: none;
                    }}
                }}
            </style>
        </head>

        <body>
            <main class="report-page">
                <header class="report-header">
                    <section class="scenario-identity scenario-identity-left">
                        <h1 class="scenario-name">
                            {scalar_value("scenario_name", "Unnamed Scenario")}
                        </h1>

                        <p class="scenario-unique-id">
                            {scalar_value("unique_id")}
                        </p>

                        <p class="scenario-date-range">
                            {scalar_value("date_range")}
                        </p>
                    </section>

                    <!--
                    Future comparison-report identity:

                    <section class="scenario-identity scenario-identity-right">
                        <h1 class="scenario-name">
                            comparison scenario name
                        </h1>

                        <p class="scenario-unique-id">
                            comparison unique ID
                        </p>

                        <p class="scenario-date-range">
                            comparison date range
                        </p>
                    </section>
                    -->
                </header>

                <div class="view-toggle-row">
                    <button
                        id="view-toggle-button"
                        class="view-toggle-button"
                        type="button"
                        aria-controls="summary-view detailed-view"
                        aria-expanded="false"
                    >
                        Detailed View
                    </button>
                </div>

                <section class="hero-section">
                    <div
                        id="hero-chart-container"
                        class="hero-chart-container"
                    >
                        
                        <svg
                            id="hero-chart"
                            class="hero-chart"
                            role="img"
                            aria-label="Forecast account balances over time"
                        ></svg>

                        <div
                            id="hero-chart-tooltip"
                            class="hero-chart-tooltip"
                            hidden
                        ></div>

                    </div>
                </section>

                <!--
                ====================================================================
                SUMMARY VIEW
                ====================================================================
                -->

                <section
                    id="summary-view"
                    class="summary-view"
                    aria-label="Forecast summary"
                >
                    <div
                        class="
                            summary-table-row
                            summary-table-row-primary
                        "
                    >
                        {render_table_card(
                            "Final Account Balances",
                            "final_account_balances",
                        )}

                        {render_table_card(
                            "Margin Metrics",
                            "margin_metrics",
                        )}

                        {render_table_card(
                            "Milestones",
                            "milestone_dates",
                        )}

                    </div>

                    <div
                        class="
                            summary-table-row
                            summary-table-row-secondary
                        "
                    >

                        {render_table_card(
                            "Forecast Metadata",
                            "forecast_metadata",
                        )}
                    </div>
                </section>

                <!--
                ====================================================================
                DETAILED VIEW
                ====================================================================
                -->

                <section
                    id="detailed-view"
                    class="detailed-view"
                    aria-label="Detailed forecast report"
                    hidden
                >
                    <div class="detail-navbar-container">
                        <nav
                            class="detail-navbar"
                            aria-label="Detailed report sections"
                            role="tablist"
                        >
                            <button
                                id="detail-tab-parameters"
                                class="detail-nav-button is-active"
                                type="button"
                                role="tab"
                                aria-selected="true"
                                aria-controls="detail-page-parameters"
                                data-detail-target="parameters"
                            >
                                Parameters
                            </button>

                            <button
                                id="detail-tab-output_data"
                                class="detail-nav-button"
                                type="button"
                                role="tab"
                                aria-selected="false"
                                aria-controls="detail-page-output_data"
                                data-detail-target="output_data"
                            >
                                Output Data
                            </button>

                            <button
                                id="detail-tab-net_worth"
                                class="detail-nav-button"
                                type="button"
                                role="tab"
                                aria-selected="false"
                                aria-controls="detail-page-net_worth"
                                data-detail-target="net_worth"
                            >
                                Net Worth
                            </button>

                            <button
                                id="detail-tab-net_gain_and_loss"
                                class="detail-nav-button"
                                type="button"
                                role="tab"
                                aria-selected="false"
                                aria-controls="detail-page-net_gain_and_loss"
                                data-detail-target="net_gain_and_loss"
                            >
                                Net Gain &amp; Loss
                            </button>

                            <button
                                id="detail-tab-account_type"
                                class="detail-nav-button"
                                type="button"
                                role="tab"
                                aria-selected="false"
                                aria-controls="detail-page-account_type"
                                data-detail-target="account_type"
                            >
                                Account Type
                            </button>

                            <button
                                id="detail-tab-interest"
                                class="detail-nav-button"
                                type="button"
                                role="tab"
                                aria-selected="false"
                                aria-controls="detail-page-interest"
                                data-detail-target="interest"
                            >
                                Interest
                            </button>

                            <button
                                id="detail-tab-milestones"
                                class="detail-nav-button"
                                type="button"
                                role="tab"
                                aria-selected="false"
                                aria-controls="detail-page-milestones"
                                data-detail-target="milestones"
                            >
                                Milestones
                            </button>

                            <button
                                id="detail-tab-sankey"
                                class="detail-nav-button"
                                type="button"
                                role="tab"
                                aria-selected="false"
                                aria-controls="detail-page-sankey"
                                data-detail-target="sankey"
                            >
                                Sankey
                            </button>

                            <button
                                id="detail-tab-all"
                                class="detail-nav-button"
                                type="button"
                                role="tab"
                                aria-selected="false"
                                aria-controls="detail-page-all"
                                data-detail-target="all"
                            >
                                All
                            </button>

                            <button
                                id="detail-tab-transaction_schedule"
                                class="detail-nav-button"
                                type="button"
                                role="tab"
                                aria-selected="false"
                                aria-controls="detail-page-transaction_schedule"
                                data-detail-target="transaction_schedule"
                            >
                                Transaction Schedule
                            </button>

                            <button
                                id="detail-tab-last_day"
                                class="detail-nav-button"
                                type="button"
                                role="tab"
                                aria-selected="false"
                                aria-controls="detail-page-last_day"
                                data-detail-target="last_day"
                            >
                                Last Day
                            </button>
                        </nav>
                    </div>

                    <div class="detail-content">
                        {detailed_pages}
                    </div>
                </section>
            </main>

            <script>
                (() => {{
                    "use strict";

                    const heroSection = document.querySelector(".hero-section");

                    const summaryView =
                        document.getElementById("summary-view");

                    const detailedView =
                        document.getElementById("detailed-view");

                    const viewToggleButton =
                        document.getElementById("view-toggle-button");

                    const detailNavButtons = Array.from(
                        document.querySelectorAll(
                            "[data-detail-target]"
                        )
                    );

                    const detailPages = Array.from(
                        document.querySelectorAll(
                            "[data-detail-page]"
                        )
                    );

                    let showingDetailedView = false;

                    

                    function setDetailedViewVisibility(showDetailed) {{
                        showingDetailedView = showDetailed;

                        summaryView.hidden = showDetailed;
                        detailedView.hidden = !showDetailed;

                        setHeroPlotVisible(!showDetailed);

                        viewToggleButton.textContent =
                            showDetailed
                                ? "Show Summary View"
                                : "Show Detailed View";

                        viewToggleButton.setAttribute(
                            "aria-expanded",
                            String(showDetailed)
                        );
                    }}

                    function setHeroPlotVisible(isVisible) {{
                        heroSection.hidden = !isVisible;
                    }}

                    function activateDetailPage(pageName) {{
                        detailNavButtons.forEach((button) => {{
                            const isActive =
                                button.dataset.detailTarget === pageName;

                            button.classList.toggle(
                                "is-active",
                                isActive
                            );

                            button.setAttribute(
                                "aria-selected",
                                String(isActive)
                            );

                            button.tabIndex = isActive ? 0 : -1;
                        }});

                        detailPages.forEach((page) => {{
                            const isActive =
                                page.dataset.detailPage === pageName;

                            page.classList.toggle(
                                "is-active",
                                isActive
                            );
                        }});
                    }}

                    viewToggleButton.addEventListener(
                        "click",
                        () => {{
                            setDetailedViewVisibility(
                                !showingDetailedView
                            );
                        }}
                    );

                    detailNavButtons.forEach((button, index) => {{
                        button.addEventListener("click", () => {{
                            activateDetailPage(
                                button.dataset.detailTarget
                            );
                        }});

                        button.addEventListener(
                            "keydown",
                            (event) => {{
                                if (
                                    event.key !== "ArrowLeft" &&
                                    event.key !== "ArrowRight"
                                ) {{
                                    return;
                                }}

                                event.preventDefault();

                                const direction =
                                    event.key === "ArrowRight"
                                        ? 1
                                        : -1;

                                const nextIndex =
                                    (
                                        index +
                                        direction +
                                        detailNavButtons.length
                                    ) % detailNavButtons.length;

                                const nextButton =
                                    detailNavButtons[nextIndex];

                                activateDetailPage(
                                    nextButton.dataset.detailTarget
                                );

                                nextButton.focus();
                            }}
                        );
                    }});

                    /*
                    Initial page state:
                        - Summary is visible.
                        - Detailed view is hidden.
                        - Parameters is the selected detailed page.
                    */
                    activateDetailPage("parameters");
                    setDetailedViewVisibility(false);
                }})();
            </script>

            <script
                id="hero-chart-data"
                type="application/json"
            >
                {hero_chart_json}
            </script>
            <script
                id="detail-chart-data"
                type="application/json"
            >
                {detail_chart_json}
            </script>
            <script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
            <script src="./hero_chart.js"></script>
            <script src="./detail_charts.js"></script>
        </body>
        </html>
        """

        return html

    # def show_plan(self, forecast_set: ForecastSetInitialConditions):
    #     raise NotImplementedError

    #TODO manual review of ForecastHandler.runForecastWithMilestoneConditionalSwaps docstring
    @classmethod
    def runForecastWithMilestoneConditionalSwaps(cls,
                             IO,
                             MS,
                             include_debug_columns=False,
                             log_stack_depth=0):

        # Order of fork options introduces instability, so fork options are processed in order
        """
        TODO one-line description of ForecastHandler.runForecastWithMilestoneConditionalSwaps.

        TODO multi-line description of ForecastHandler.runForecastWithMilestoneConditionalSwaps.
        TODO explain how ForecastHandler.runForecastWithMilestoneConditionalSwaps participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        IO : object
            TODO one-line description of ForecastHandler.runForecastWithMilestoneConditionalSwaps.IO.

        MS : object
            TODO one-line description of ForecastHandler.runForecastWithMilestoneConditionalSwaps.MS.

        include_debug_columns : bool
            TODO one-line description of ForecastHandler.runForecastWithMilestoneConditionalSwaps.include_debug_columns.

        log_stack_depth : int
            TODO one-line description of ForecastHandler.runForecastWithMilestoneConditionalSwaps.log_stack_depth.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler.runForecastWithMilestoneConditionalSwaps.

        Contract
        --------
        - #TODO contract lines for ForecastHandler.runForecastWithMilestoneConditionalSwaps.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler.runForecastWithMilestoneConditionalSwaps.

        @interface-report: show
        """
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
                elif account.account_type == "investment":
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
            "milestone_results": MilestoneSet.evaluateMilestones(
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
        R.milestone_results = MilestoneSet.evaluateMilestones(R.forecast_df, R.milestone_set, log_stack_depth=log_stack_depth)

        return R

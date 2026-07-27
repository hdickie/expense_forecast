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
    ROUNDING_ERROR_TOLERANCE,
)
from expense_forecast.LineItemSet import LineItemSet
# from expense_forecast.ForecastSetInitialConditions import ForecastSetInitialConditions
from expense_forecast.MemoRuleSet import MemoRuleSet
from expense_forecast.MilestoneSet import MilestoneSet
from expense_forecast.ExpenseForecastInitialConditions import ExpenseForecastInitialConditions
from expense_forecast.ExpenseForecastResult import ExpenseForecastResult
from expense_forecast.ForecastResultSet import ForecastResultSet
from expense_forecast.ForecastPolicySet import ForecastPolicySet
from expense_forecast.MinimumCheckingBalancePolicy import MinimumCheckingBalancePolicy

import hashlib
import hashlib
import json
from pprint import pformat
from datetime import date
from typing import Any
import datetime
import calendar
import math
from contextlib import nullcontext
from time import perf_counter
import os
import tempfile
import shutil
from pathlib import Path
from dateutil.relativedelta import relativedelta
from expense_forecast.log_methods import (
    ForecastProgress,
    log_in_color,
    project_log_file,
    setup_logger,
)
import logging

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
from expense_forecast.SurplusDebtPaymentPolicy import SurplusDebtPaymentPolicy
from expense_forecast.SurplusSavingPolicy import SurplusSavingPolicy
from expense_forecast.CurrentStatementBalancePaymentPolicy import (
    CurrentStatementBalancePaymentPolicy,
)
from expense_forecast.InvestmentPolicies import (
    FixedMonthlyInvestmentPolicy,
    IncomePercentageInvestmentPolicy,
    PeriodicInvestmentContributionCapPolicy,
    SurplusInvestmentPolicy,
)
from expense_forecast.ForecastPolicy import ForecastPolicyError
from expense_forecast.PolicyEventGraph import PolicyEventGraph
from expense_forecast.ScenarioChoice import (
    ScenarioChoice,
    overlay_account_sets,
    extend_account_schema,
    overlay_memo_rule_sets,
    overlay_policy_sets,
    overlay_transition_sets,
)
from matplotlib.pyplot import figure

try:
    import plotly.graph_objects as go
except ImportError:
    go = None

matplotlib.rcParams["figure.facecolor"] = "#d1d5db"
matplotlib.rcParams["axes.facecolor"] = "#e5e7eb"
matplotlib.rcParams["savefig.facecolor"] = "#d1d5db"

logger = setup_logger(__name__, project_log_file(__name__))

# Show all decimal places in data frames
pd.set_option("display.precision", 2)
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

#TODO DOC manual review of ForecastHandler docstring
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
    def _log_interpretation_guide(IO):
        if getattr(IO, "_suppress_log_guide", False):
            return
        guide_lines = (
            "How to read this forecast log:",
            "BLUE starts setup or a new phase.",
            "MAGENTA describes policy discovery and activation.",
            "CYAN means work is active; heartbeats confirm long simulations are progressing.",
            "GREEN marks successful completion.",
            "YELLOW marks skipped/deferred work or a recoverable warning.",
            "RED marks a failure requiring attention.",
            "Discovery and feasibility forecasts are internal safety checks; "
            "the post-activation pass produces the final forecast.",
            "Transaction-level DEBUG detail is written under ./log/.",
        )
        colors = (
            "blue", "blue", "magenta", "cyan", "green",
            "yellow", "red", "white", "white",
        )
        for color, line in zip(colors, guide_lines):
            log_in_color(
                logger, color, "info", line, user_facing=True
            )

    @staticmethod
    def _phase_log(color, message, level="info"):
        log_in_color(
            logger, color, level, message, user_facing=True
        )

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
            if stripped_value.lower() in {"none", "null", "nat"}:
                return None
            for date_format in ["%Y%m%d", "%Y-%m-%d"]:
                try:
                    return datetime.datetime.strptime(
                        stripped_value, date_format
                    ).date()
                except ValueError:
                    pass
            # Approximate forecasts can materialize milestone dates with a
            # time component (for example ``2037-06-01 00:00:00``).  Those
            # values still describe forecast dates and must not remain strings
            # when transition code compares them with DataFrame date cells.
            try:
                return pd.Timestamp(stripped_value).date()
            except (TypeError, ValueError):
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

    @classmethod
    def runForecast(
        cls,
        IO: ExpenseForecastInitialConditions,
        milestone_set: MilestoneSet = None,
        include_debug_columns=False,
        engine="legacy",
        graph_trace=False,
    ) -> ExpenseForecastResult:
        IO = cls._move_start_date_deferrals_after_seed(IO)
        if engine not in {
            "legacy", "graph", "graph v2", "shadow", "shadow v2"
        }:
            raise ValueError(
                "engine must be 'legacy', 'graph', 'graph v2', 'shadow', "
                "or 'shadow v2'"
            )
        if graph_trace and engine not in {"graph v2", "shadow v2"}:
            raise ValueError(
                "graph_trace is supported only with engine='graph v2' "
                "or engine='shadow v2'"
            )
        if engine == "graph v2":
            from expense_forecast.MemoizedDynamicDependencyGraphEngine import (
                ExecutionEngine,
            )

            resolved_milestones = milestone_set or getattr(
                IO, "milestone_set", MilestoneSet()
            )
            return ExecutionEngine.runForecast(
                IO,
                resolved_milestones,
                graph_trace=graph_trace,
            )
        if engine == "shadow v2":
            from expense_forecast.MemoizedDynamicDependencyGraphEngine import (
                ExecutionEngine,
                GraphV2Difference,
                GraphV2ShadowMismatchError,
                compare_v2_result,
            )

            resolved_milestones = milestone_set or getattr(
                IO, "milestone_set", MilestoneSet()
            )
            legacy_result = cls.runForecast(
                IO,
                resolved_milestones,
                include_debug_columns,
                engine="legacy",
            )
            scenario = IO.forecast_name or IO.unique_id
            try:
                graph_output = ExecutionEngine.runForecast(
                    IO,
                    resolved_milestones,
                    graph_trace=graph_trace,
                )
            except Exception as error:
                raise GraphV2ShadowMismatchError(
                    scenario=scenario,
                    differences=[
                        GraphV2Difference(
                            section="execution",
                            variable=type(error).__name__,
                            graph_value=str(error),
                            legacy_value="completed successfully",
                            producer="ExecutionEngine.runForecast",
                        )
                    ],
                ) from error
            compare_v2_result(
                graph_output,
                legacy_result,
                scenario=scenario,
            )
            # Until v2 assembles ExpenseForecastResult, legacy supplies the
            # public return value only after the independently computed v2
            # account state has matched.
            return legacy_result
        if engine in {"graph", "shadow"}:
            from expense_forecast.graph_engine import GraphForecastRunner
            from expense_forecast.graph_engine.comparator import compare_results

            graph_result = GraphForecastRunner(
                IO, milestone_set, approximate=False,
                include_debug_columns=include_debug_columns,
            ).run()
            if engine == "graph":
                return graph_result
            legacy_started = perf_counter()
            legacy_result = cls.runForecast(
                IO, milestone_set, include_debug_columns, engine="legacy"
            )
            graph_result.graph_diagnostics.legacy_shadow_seconds = (
                perf_counter() - legacy_started
            )
            compare_results(graph_result, legacy_result)
            return graph_result
        cls._log_interpretation_guide(IO)
        milestone_set = milestone_set or getattr(IO, "milestone_set", MilestoneSet())
        if getattr(IO, "policy_set", None):
            return cls._runForecastWithPolicies(
                IO, milestone_set, include_debug_columns, approximate=False
            )
        transitions = getattr(IO, "transition_set", None)
        if transitions:
            return cls._runForecastWithScenarioTransitions(
                IO,
                milestone_set,
                transitions,
                include_debug_columns=include_debug_columns,
                approximate=False,
            )
        return cls._runForecastOnce(IO, milestone_set, include_debug_columns)

    #TODO DOC manual review of ForecastHandler.runForecast docstring
    @classmethod
    def _runForecastOnce(cls,
                    IO: ExpenseForecastInitialConditions,
                    milestone_set: MilestoneSet,
                    include_debug_columns = False
                    ) -> ExpenseForecastResult:
        # print('Starting Forecast #'+str(cls.unique_id))
        """
        #TODO DOC one-line description of ForecastHandler.runForecast.

        #TODO DOC multi-line description of ForecastHandler.runForecast.
        #TODO DOC explain how ForecastHandler.runForecast participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        IO : object
            #TODO DOC one-line description of ForecastHandler.runForecast.IO.

        milestone_set : object
            #TODO DOC one-line description of ForecastHandler.runForecast.milestone_set.

        include_debug_columns : bool
            #TODO DOC one-line description of ForecastHandler.runForecast.include_debug_columns.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler.runForecast.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler.runForecast.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler.runForecast.

        @interface-report: show
        """
        log_stack_depth = 0
        cls.start_ts = datetime.datetime.now() #TODO does F need start_ts ?
        cls.initial_account_set = IO.initial_account_set
        cls.initial_line_item_set = IO.initial_line_item_set
        cls.initial_memo_rule_set = IO.initial_memo_rule_set

        cls._phase_log(
            "blue",
            "Starting Forecast: "
            f"name={(getattr(IO, 'forecast_name', None) or 'Unnamed forecast')!r} "
            f"id={IO.unique_id} mode=exact range={IO.start_date} to {IO.end_date}",
        )

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
                progress_bar=None,
                progress_phase=getattr(IO, "_progress_phase", "Exact"),
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
                    logger.exception(
                        "Forecast output normalization failed: malformed memo "
                        "directive=%r forecast_id=%s",
                        md,
                        IO.unique_id,
                    )
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
        cls._phase_log(
            "green",
            "Finished Forecast: "
            f"id={IO.unique_id} mode=exact "
            f"elapsed={(cls.end_ts - cls.start_ts).total_seconds():.2f}s "
            f"confirmed={len(confirmed_df)} deferred={len(deferred_df)} "
            f"skipped={len(skipped_df)} "
            f"final_net_worth=${float(forecast_df['Net Worth'].iloc[-1]):.2f}",
        )

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
        if str(account_to).startswith("ALL_"):
            return None
        account_from_obj = account_set._get_account_by_name(account_from)
        account_to_obj = account_set._get_account_by_name(account_to)
        if str(account_to).startswith("SAVINGS_BELOW:"):
            return f"SAVINGS CONTRIBUTION ({account_to_obj.name} +${amount})"
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
    def runForecastSetApproximate(
        cls,
        initial_conditions_list,
        milestone_set=None,
        include_debug_columns=False,
        engine="graph v2",
        graph_trace=False,
    ) -> ForecastResultSet:
        """Run comparable approximate forecasts in declaration order.

        Scenario materialization remains explicit: this method accepts only
        complete initial conditions and forwards the same execution options to
        each forecast.  Sequential execution keeps log output intelligible and
        avoids introducing concurrency semantics into the first set runner.
        """
        if isinstance(
            initial_conditions_list,
            ExpenseForecastInitialConditions,
        ):
            raise TypeError(
                "initial_conditions_list must be an iterable of "
                "ExpenseForecastInitialConditions"
            )

        try:
            initial_conditions = list(initial_conditions_list)
        except TypeError as error:
            raise TypeError(
                "initial_conditions_list must be an iterable of "
                "ExpenseForecastInitialConditions"
            ) from error

        if not initial_conditions:
            raise ValueError(
                "runForecastSetApproximate requires at least one forecast"
            )
        if any(
            not isinstance(item, ExpenseForecastInitialConditions)
            for item in initial_conditions
        ):
            raise TypeError(
                "initial_conditions_list must contain only "
                "ExpenseForecastInitialConditions"
            )

        results = [
            cls.runForecastApproximate(
                initial_conditions_item,
                milestone_set=milestone_set,
                include_debug_columns=include_debug_columns,
                engine=engine,
                graph_trace=graph_trace,
            )
            for initial_conditions_item in initial_conditions
        ]
        return ForecastResultSet(results)

    @classmethod
    def runForecastApproximate(
        cls,
        IO: ExpenseForecastInitialConditions,
        milestone_set: MilestoneSet = None,
        include_debug_columns=False,
        engine="legacy",
        graph_trace=False,
    ) -> ExpenseForecastResult:
        IO = cls._move_start_date_deferrals_after_seed(IO)
        if engine not in {
            "legacy", "graph", "graph v2", "shadow", "shadow v2"
        }:
            raise ValueError(
                "engine must be 'legacy', 'graph', 'graph v2', 'shadow', "
                "or 'shadow v2'"
            )
        if graph_trace and engine not in {"graph v2", "shadow v2"}:
            raise ValueError(
                "graph_trace is supported only with engine='graph v2' "
                "or engine='shadow v2'"
            )
        if engine in {"graph v2", "shadow v2"}:
            from expense_forecast.MemoizedDynamicDependencyGraphEngine import (
                ExecutionEngine,
                GraphV2Difference,
                GraphV2ShadowMismatchError,
                compare_v2_result,
            )

            resolved_milestones = milestone_set or getattr(
                IO, "milestone_set", MilestoneSet()
            )
            if engine == "graph v2":
                return ExecutionEngine.runForecastApproximate(
                    IO,
                    resolved_milestones,
                    include_debug_columns=include_debug_columns,
                    graph_trace=graph_trace,
                )

            legacy_result = cls.runForecastApproximate(
                IO,
                resolved_milestones,
                include_debug_columns,
                engine="legacy",
            )
            scenario = IO.forecast_name or IO.unique_id
            try:
                graph_result = ExecutionEngine.runForecastApproximate(
                    IO,
                    resolved_milestones,
                    include_debug_columns=include_debug_columns,
                    graph_trace=graph_trace,
                )
            except Exception as error:
                raise GraphV2ShadowMismatchError(
                    scenario=scenario,
                    differences=[
                        GraphV2Difference(
                            section="execution",
                            variable=type(error).__name__,
                            graph_value=str(error),
                            legacy_value="completed successfully",
                            producer=(
                                "ExecutionEngine.runForecastApproximate"
                            ),
                        )
                    ],
                ) from error
            compare_v2_result(
                graph_result,
                legacy_result,
                scenario=scenario,
            )
            return graph_result
        if engine in {"graph", "shadow"}:
            from expense_forecast.graph_engine import GraphForecastRunner
            from expense_forecast.graph_engine.comparator import compare_results

            graph_result = GraphForecastRunner(
                IO, milestone_set, approximate=True,
                include_debug_columns=include_debug_columns,
            ).run()
            if engine == "graph":
                return graph_result
            legacy_started = perf_counter()
            legacy_result = cls.runForecastApproximate(
                IO, milestone_set, include_debug_columns, engine="legacy"
            )
            graph_result.graph_diagnostics.legacy_shadow_seconds = (
                perf_counter() - legacy_started
            )
            compare_results(graph_result, legacy_result)
            return graph_result
        cls._log_interpretation_guide(IO)
        milestone_set = milestone_set or getattr(IO, "milestone_set", MilestoneSet())
        if getattr(IO, "policy_set", None):
            return cls._runForecastWithPolicies(
                IO, milestone_set, include_debug_columns, approximate=True
            )
        transitions = getattr(IO, "transition_set", None)
        if transitions:
            return cls._runForecastWithScenarioTransitions(
                IO,
                milestone_set,
                transitions,
                include_debug_columns=include_debug_columns,
                approximate=True,
            )
        total = max(1, len(cls._approximate_output_dates(IO.start_date, IO.end_date)) - 1)
        progress_phase = getattr(IO, "_progress_phase", "Approximate execution")
        with ForecastProgress(logger, progress_phase, total) as progress:
            IO._forecast_progress = progress
            try:
                return cls._runForecastApproximateOnce(
                    IO, milestone_set, include_debug_columns
                )
            finally:
                if hasattr(IO, "_forecast_progress"):
                    delattr(IO, "_forecast_progress")

    @classmethod
    def _runForecastApproximateOnce(
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
        feasibility_only = getattr(IO, "_feasibility_only", False)
        progress = getattr(IO, "_forecast_progress", None)
        if not feasibility_only:
            cls._phase_log(
                "blue",
                "Starting Approximate Forecast: "
                f"name={(getattr(IO, 'forecast_name', None) or 'Unnamed forecast')!r} "
                f"id={IO.unique_id} range={IO.start_date} to {IO.end_date}",
            )
        account_set = copy.deepcopy(IO.initial_account_set)
        memo_rule_set = copy.deepcopy(IO.initial_memo_rule_set)
        output_dates = cls._approximate_output_dates(IO.start_date, IO.end_date)
        schedule = IO.initial_line_item_set.getLineItemSchedule().copy()
        policy_activation_date = getattr(IO, "_policy_activation_date", None)
        if policy_activation_date is not None and not schedule.empty:
            schedule_dates = schedule["Date"].apply(cls._normalize_date_value)
            schedule = schedule.loc[
                ~(
                    ((schedule["Priority"] == 1) & (schedule_dates <= policy_activation_date))
                    | ((schedule["Priority"] > 1) & (schedule_dates < policy_activation_date))
                )
            ].copy()
        if not schedule.empty:
            schedule["Date"] = schedule["Date"].apply(cls._normalize_date_value)
            exclude_schedule_through = getattr(
                IO, "_exclude_schedule_through", None
            )
            if exclude_schedule_through is not None:
                exclude_schedule_through = cls._normalize_date_value(
                    exclude_schedule_through
                )
                schedule = schedule.loc[
                    schedule["Date"] > exclude_schedule_through
                ].copy()

        if not feasibility_only:
            cls._phase_log(
                "cyan",
                "Approximate forecast prepared: "
                f"accounts={len(account_set.accounts)} "
                f"scheduled_transactions={len(schedule)} output_dates={len(output_dates)}",
            )

        transaction_columns = list(schedule.columns)
        current_statement_policy_cards = {
            str(memo).split(
                "POLICY current_statement_balance_payment:", 1
            )[1].split(" ", 1)[0]
            for memo in schedule.get("Memo", pd.Series(dtype=str)).astype(str)
            if str(memo).startswith(
                "POLICY current_statement_balance_payment:"
            )
        }
        policy_declaration_order = getattr(
            IO,
            "_policy_declaration_order",
            {
                policy.policy_key: index
                for index, policy in enumerate(IO.policy_set.policies)
            },
        )
        policy_event_graph = PolicyEventGraph.from_schedule(schedule, memo_rule_set)

        def policy_order_for_memo(memo):
            memo = str(memo)
            if not memo.startswith("POLICY "):
                return None
            return next(
                (
                    order for key, order in policy_declaration_order.items()
                    if memo.startswith(f"POLICY {key} ")
                ),
                len(policy_declaration_order),
            )
        confirmed_records = []
        skipped_records = []
        safety_decisions = []
        policy_shadow_mode = bool(
            getattr(IO, "_policy_shadow_mode", False)
            or os.environ.get("EXPENSE_FORECAST_POLICY_SHADOW") == "1"
        )
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
            interest = state.principal_balance * state.apr * float(days) / float("365.25")
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
                    f"INVESTMENT RETURN ({account.name} +${growth})"
                )

        def future_lower_priorities_are_feasible(candidate_account_set, txn):
            """Recursively validate a policy candidate against its suffix."""
            memo = str(txn["Memo"])
            if not memo.startswith("POLICY ") or txn["Date"] >= IO.end_date:
                return True, None
            lower_priority_budget = LineItemSet(
                [
                    copy.deepcopy(item)
                    for item in IO.initial_line_item_set.line_items
                    if item.priority < int(txn["Priority"])
                ]
            )
            if not lower_priority_budget.line_items:
                return True, None
            feasibility_io = ExpenseForecastInitialConditions(
                start_date=txn["Date"],
                end_date=IO.end_date,
                account_set=candidate_account_set,
                line_item_set=lower_priority_budget,
                memo_rule_set=IO.initial_memo_rule_set,
                policy_set=ForecastPolicySet(),
            )
            feasibility_io._exclude_schedule_through = txn["Date"]
            feasibility_io._feasibility_only = True
            try:
                cls._runForecastApproximateOnce(
                    feasibility_io, MilestoneSet(), include_debug_columns=True
                )
            except AccountBoundaryError as error:
                return False, error
            return True, None

        def attempt_current_transaction(base_account_set, txn, amount):
            """Execute against a copy without evaluating the future suffix."""
            candidate_account_set = copy.deepcopy(base_account_set)
            try:
                executed = candidate_account_set.executeTransaction(
                    txn["Account_From"],
                    txn["Account_To"],
                    amount,
                    income_flag=bool(txn["Income_Flag"]),
                    enforce_policy_minimum=int(txn["Priority"]) > 1,
                )
            except AccountBoundaryError:
                return None, float("0")
            if executed is None:
                executed = float(str(amount))
            return candidate_account_set, float(str(executed))

        def attempt_transaction(base_account_set, txn, amount):
            """Execute against a copy and recursively validate the suffix."""
            candidate_account_set, executed = attempt_current_transaction(
                base_account_set, txn, amount
            )
            if candidate_account_set is None:
                return None, float("0")
            if executed <= MONEY_BOUNDARY_TOLERANCE:
                return candidate_account_set, float("0")
            feasible, _ = future_lower_priorities_are_feasible(
                candidate_account_set, txn
            )
            if not feasible:
                return None, float("0")
            return candidate_account_set, executed

        def constrained_transaction(base_account_set, txn, amount):
            """Prove a direct checking-account transaction safe analytically."""
            memo = str(txn["Memo"])
            if not memo.startswith("POLICY "):
                return None, None, "ordinary optional transaction"
            source = txn.get("Account_From")
            destination = txn.get("Account_To")
            if source in [None, "", "None"]:
                return None, None, "external source endpoint"
            source_account = base_account_set._get_account_by_name(source)
            destination_account = base_account_set._get_account_by_name(destination)
            if source_account is None or source_account.account_type != "checking":
                return None, None, "non-checking source"
            if destination_account is not None and (
                destination_account.account_type == "loan"
                or destination_account.account_type == "investment"
                or (
                    destination_account.account_type == "credit"
                    and not str(destination).startswith("CURRENT_STATEMENT_BALANCE:")
                )
            ):
                return None, None, "balance-dependent destination"

            source_name = source_account.name
            source_floor = float(str(
                source_account.effective_policy_min_balance
                if int(txn["Priority"]) > 1
                else source_account.min_balance
            ))
            if str(source).startswith("CHECKING_ABOVE:"):
                source_floor = max(
                    source_floor,
                    float(str(source).split(":", 1)[1]),
                )

            maximum_need, binding_date, affected_nodes = (
                policy_event_graph.reserve_requirement(
                    source_name, txn["Date"], txn["Priority"]
                )
            )

            available = (
                float(str(source_account.balance))
                - source_floor
                - maximum_need
            )
            destination_capacity = float("Infinity")
            if str(destination).startswith("ALL_"):
                debt_type = (
                    "loan" if str(destination).startswith("ALL_LOANS") else "credit"
                )
                debt_accounts = [
                    account for account in base_account_set.accounts
                    if account.account_type == debt_type
                ]
                if any(
                    float(str(account.billing_state.apr)) != 0
                    for account in debt_accounts
                ):
                    return None, None, "nonlinear debt ledger"
                future_payments = policy_event_graph.future_incoming(
                    [account.name for account in debt_accounts],
                    txn["Date"], txn["Priority"],
                )
                destination_capacity = max(
                    float("0"),
                    sum(
                        (float(str(account.balance)) for account in debt_accounts),
                        float("0"),
                    ) - future_payments,
                )
            safe_amount = max(
                float("0"),
                min(float(str(amount)), available, destination_capacity),
            )
            return safe_amount, {
                "available_headroom": float(max(float("0"), available)),
                "binding_account": source_name,
                "binding_date": binding_date,
                "binding_constraint": "future mandatory reserve",
                "affected_graph_nodes": affected_nodes,
            }, None

        def maximum_partial_transaction(base_account_set, txn):
            """Find the largest currently valid amount without mutating state."""
            requested_amount = float(str(txn["Amount"]))
            low = float("0")
            high = requested_amount
            best_account_set = None
            best_executed_amount = float("0")

            for _ in range(60):
                # This search determines persisted debt/payment state, not
                # merely whether a displayed cent is meaningful. Stopping at
                # the general half-cent boundary can put graph and legacy on
                # opposite sides of a cent after interest and billing-state
                # rounding. Resolve the executable boundary to sub-cent
                # precision and leave presentation rounding to the result
                # materializer.
                if high - low <= float("0.000001"):
                    break
                candidate_amount = (low + high) / float("2")
                candidate_account_set, executed_amount = attempt_current_transaction(
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

            if best_account_set is None:
                return None, float("0")

            # Preserve recursive future feasibility without performing a full
            # suffix run on every binary-search step. A boundary violation is
            # linear in the policy transfer amount, so reduce by its reported
            # shortfall and recheck the suffix.
            for _ in range(8):
                feasible, error = future_lower_priorities_are_feasible(
                    best_account_set, txn
                )
                if feasible:
                    return best_account_set, best_executed_amount
                reduction = getattr(error, "boundary_shortfall", None)
                if reduction is None or reduction <= MONEY_BOUNDARY_TOLERANCE:
                    return None, float("0")
                revised_amount = max(
                    float("0"), best_executed_amount - float(str(reduction))
                )
                if revised_amount <= MONEY_BOUNDARY_TOLERANCE:
                    return None, float("0")
                best_account_set, best_executed_amount = attempt_current_transaction(
                    base_account_set, txn, revised_amount
                )
                if best_account_set is None:
                    return None, float("0")
            return None, float("0")

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
                        account.billing_state.billing_cycle_payment_balance = float("0")
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
                policy_order = policy_order_for_memo(transaction["Memo"])
                return (
                    transaction["Date"],
                    transaction["Priority"],
                    1 if policy_order is not None else 0,
                    policy_order if policy_order is not None else -1,
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
                    if endpoint not in [None, "", "None"] and not str(endpoint).startswith("ALL_")
                }
                for endpoint in investment_endpoints:
                    endpoint_account = account_set._get_account_by_name(endpoint)
                    if endpoint_account.account_type == "investment":
                        accrue_investment_to(
                            endpoint_account, txn["Date"], directives
                        )
                if str(account_to).startswith("ALL_LOANS"):
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
                resolution_started_at = perf_counter()
                constrained_amount, constraint_detail, fallback_reason = (
                    constrained_transaction(account_set, executable_txn, txn["Amount"])
                )
                resolution_method = "recursive"
                shadow_equivalent = None
                if constrained_amount is not None:
                    resolution_method = "constraint"
                    candidate_account_set, executed_amount = attempt_current_transaction(
                        account_set, executable_txn, constrained_amount
                    )
                    if policy_shadow_mode:
                        oracle_account_set, oracle_executed = attempt_transaction(
                            account_set, executable_txn, txn["Amount"]
                        )
                        if (
                            oracle_account_set is None
                            and bool(txn["Partial_Payment_Allowed"])
                        ):
                            oracle_account_set, oracle_executed = (
                                maximum_partial_transaction(
                                    account_set, executable_txn
                                )
                            )
                        shadow_equivalent = (
                            oracle_account_set is not None
                            and abs(oracle_executed - executed_amount)
                            <= MONEY_BOUNDARY_TOLERANCE
                        )
                        if not shadow_equivalent:
                            raise AssertionError(
                                "Policy compiler shadow mismatch: "
                                f"memo={txn['Memo']!r} compiled={executed_amount} "
                                f"recursive={oracle_executed}"
                            )
                else:
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
                if str(txn["Memo"]).startswith("POLICY "):
                    safety_decisions.append({
                        "date": txn["Date"],
                        "memo": txn["Memo"],
                        "priority": int(txn["Priority"]),
                        "requested": float(txn["Amount"]),
                        "executed": float(executed_amount),
                        "resolution_method": resolution_method,
                        "fallback_reason": fallback_reason,
                        "affected_graph_nodes": [
                            str(account_from), str(account_to),
                            f"schedule-after:{txn['Date']}",
                        ] + list((constraint_detail or {}).get(
                            "affected_graph_nodes", []
                        )),
                        "proof_conditions": (
                            ["source reserve envelope covers higher-priority future flows"]
                            if resolution_method == "constraint" else []
                        ),
                        "recomputed_nodes": len(schedule.loc[
                            schedule["Date"] > txn["Date"]
                        ]),
                        "incremental_seconds": perf_counter() - resolution_started_at,
                        "suffix_forecasts_avoided": int(
                            resolution_method == "constraint"
                        ),
                        "shadow_equivalent": shadow_equivalent,
                        **{
                            key: value for key, value in (constraint_detail or {}).items()
                            if key != "affected_graph_nodes"
                        },
                    })
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
                        try:
                            account_set.executeTransaction(
                                account_from,
                                account_to,
                                txn["Amount"],
                                income_flag=bool(txn["Income_Flag"]),
                            )
                        except AccountBoundaryError as error:
                            contextual_error = AccountBoundaryError(
                                "Approximate mandatory transaction failed "
                                f"during the execution pass: date={txn['Date']}, "
                                f"priority={txn['Priority']}, memo={txn['Memo']!r}, "
                                f"amount={txn['Amount']}, from={account_from!r}, "
                                f"to={account_to!r}.\n{error}"
                            )
                            contextual_error.boundary_shortfall = getattr(
                                error, "boundary_shortfall", None
                            )
                            contextual_error.account_name = getattr(
                                error, "account_name", None
                            )
                            contextual_error.role = getattr(error, "role", None)
                            raise contextual_error from error
                    continue

                account_set = candidate_account_set
                if executed_amount <= MONEY_BOUNDARY_TOLERANCE:
                    continue

                if str(txn["Memo"]).startswith(
                    "POLICY current_statement_balance_payment:"
                ):
                    card_name = str(txn["Memo"]).split(
                        "POLICY current_statement_balance_payment:", 1
                    )[1].split(" ", 1)[0]
                    card = account_set._get_account_by_name(card_name)
                    interest = card.billing_state.interest_accrued_this_cycle()
                    if interest:
                        directives.append(
                            f"CC INTEREST ({card.name}: Prev Stmt Bal +${interest:.2f})"
                        )
                    card.billing_state = card.billing_state.roll_cycle(
                        txn["Date"] + datetime.timedelta(days=1)
                    )
                    sync(card)
                    checking = account_set._get_account_by_name(
                        account_set.primary_checking_account_name
                    )
                    minimum_payment = min(
                        card.billing_state.remaining_minimum_payment_due(),
                        card.balance,
                        float(str(checking.balance))
                        - float(str(checking.min_balance)),
                    )
                    if minimum_payment > 0:
                        account_set.executeTransaction(
                            checking.name,
                            card.name,
                            minimum_payment,
                            minimum_payment_flag=True,
                        )
                        directives.append(
                            f"MINIMUM PAYMENT ({checking.name} -${minimum_payment:.2f})"
                        )
                        directives.append(
                            f"MINIMUM PAYMENT ({card.name} +${minimum_payment:.2f})"
                        )
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
                    if str(account_to).startswith("ALL_")
                    else account_set._get_account_by_name(account_to)
                )
                if account_to_obj is not None and account_to_obj.account_type == "credit":
                    directives.append(
                        f"ADDTL CC PAYMENT ({account_to} -${executed_amount:g})"
                    )
                key = (txn["Memo"], account_from, account_to)
                count, total = memo_groups.get(key, (0, float("0")))
                memo_groups[key] = (count + 1, total + executed_amount)

            for account in account_set.accounts:
                if account.account_type == "investment":
                    accrue_investment_to(account, output_date, directives)
                    continue
                billing_start = getattr(account.billing_state, "billing_cycle_start_date", None)
                if account.account_type not in ["loan", "credit"] or output_date < billing_start:
                    continue
                if (
                    account.account_type == "credit"
                    and account.name in current_statement_policy_cards
                ):
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
                        float(str(checking.balance))
                        - float(str(checking.min_balance)),
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
                        float(str(checking.balance))
                        - float(str(checking.min_balance)),
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
            if not feasibility_only:
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
            if progress is not None:
                progress.update(1, context=output_date)

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
            "safety_decisions": safety_decisions,
        }
        if milestone_set:
            result_kwargs["milestone_set"] = milestone_set
            result_kwargs["milestone_results"] = milestone_results
        result = ExpenseForecastResult(IO, forecast_df, start_ts, end_ts = datetime.datetime.now(), **result_kwargs)
        if not feasibility_only:
            cls._phase_log(
                "green",
                "Finished Approximate Forecast: "
                f"id={IO.unique_id} "
                f"elapsed={(result.end_ts - result.start_ts).total_seconds():.2f}s "
                f"confirmed={len(confirmed_df)} deferred={len(deferred_df)} "
                f"skipped={len(skipped_df)} "
                f"final_net_worth=${float(forecast_df['Net Worth'].iloc[-1]):.2f}",
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
    #TODO DOC manual review of ForecastHandler._sortTxnsToPreventErrors docstring
    @classmethod
    def _sortTxnsToPreventErrors(
        cls, relevant_confirmed_df, account_set, memo_set, log_stack_depth
    ):
        """
        #TODO DOC one-line description of ForecastHandler._sortTxnsToPreventErrors.

        #TODO DOC multi-line description of ForecastHandler._sortTxnsToPreventErrors.
        #TODO DOC explain how ForecastHandler._sortTxnsToPreventErrors participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        relevant_confirmed_df : object
            #TODO DOC one-line description of ForecastHandler._sortTxnsToPreventErrors.relevant_confirmed_df.

        account_set : object
            #TODO DOC one-line description of ForecastHandler._sortTxnsToPreventErrors.account_set.

        memo_set : object
            #TODO DOC one-line description of ForecastHandler._sortTxnsToPreventErrors.memo_set.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._sortTxnsToPreventErrors.log_stack_depth.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._sortTxnsToPreventErrors.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._sortTxnsToPreventErrors.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._sortTxnsToPreventErrors.

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

    #TODO DEFER CODEX-OK Isn't there a flag for this now?
    #TODO DOC manual review of ForecastHandler._checkIfTxnIsIncome docstring
    @classmethod
    def _checkIfTxnIsIncome(cls, confirmed_row, log_stack_depth):
        """
        #TODO DEFER one-line description of ForecastHandler._checkIfTxnIsIncome.

        #TODO DEFER multi-line description of ForecastHandler._checkIfTxnIsIncome.
        #TODO DEFER explain how ForecastHandler._checkIfTxnIsIncome participates in this module.
        #TODO DEFER document important state, validation, or serialization behavior.

        Parameters
        ----------
        confirmed_row : object
            #TODO DEFER one-line description of ForecastHandler._checkIfTxnIsIncome.confirmed_row.

        log_stack_depth : int
            #TODO DEFER one-line description of ForecastHandler._checkIfTxnIsIncome.log_stack_depth.

        Returns
        -------
        object
            #TODO DEFER one-line description of return value of ForecastHandler._checkIfTxnIsIncome.

        Contract
        --------
        - #TODO DEFER contract lines for ForecastHandler._checkIfTxnIsIncome.
        - #TODO DEFER document exceptions, mutations, and precision assumptions for ForecastHandler._checkIfTxnIsIncome.

        @interface-report: show
        """
        # Scheduled transactions carry an explicit flag.  Memo inspection is
        # retained only for legacy callers that construct confirmed rows by
        # hand without the column.
        if "Income_Flag" in confirmed_row.index and not pd.isna(confirmed_row["Income_Flag"]):
            income_flag = bool(confirmed_row["Income_Flag"])
        else:
            m_income = re.search(r"income", str(confirmed_row.Memo), re.IGNORECASE)
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
        #TODO DOC one-line description of ForecastHandler._updateBalancesAndMemo.

        #TODO DOC multi-line description of ForecastHandler._updateBalancesAndMemo.
        #TODO DOC explain how ForecastHandler._updateBalancesAndMemo participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        forecast_df : object
            #TODO DOC one-line description of ForecastHandler._updateBalancesAndMemo.forecast_df.

        account_set : object
            #TODO DOC one-line description of ForecastHandler._updateBalancesAndMemo.account_set.

        confirmed_row : object
            #TODO DOC one-line description of ForecastHandler._updateBalancesAndMemo.confirmed_row.

        memo_rule : object
            #TODO DOC one-line description of ForecastHandler._updateBalancesAndMemo.memo_rule.

        d : object
            #TODO DOC one-line description of ForecastHandler._updateBalancesAndMemo.d.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._updateBalancesAndMemo.log_stack_depth.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._updateBalancesAndMemo.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._updateBalancesAndMemo.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._updateBalancesAndMemo.

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
            not str(memo_rule.account_to).startswith("ALL_")
            and not str(memo_rule.account_to).startswith(
                "CURRENT_STATEMENT_BALANCE:"
            )
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

        if str(memo_rule.account_to).startswith(
            "CURRENT_STATEMENT_BALANCE:"
        ):
            forecast_df.loc[row_sel_vec, "Memo"] += (
                f"; {confirmed_row.Memo} "
                f"({memo_rule.account_from} -${confirmed_row.Amount}) "
            )

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
                    str(memo_rule.account_to).startswith("ALL_LOANS")
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

    #TODO DOC manual review of ForecastHandler._annotateAcceptedProposedTransaction docstring
    @classmethod
    def _annotateAcceptedProposedTransaction(
        cls, forecast_df, proposed_row, memo_rule_row, d, account_set, log_stack_depth
    ):
        """
        #TODO DOC one-line description of ForecastHandler._annotateAcceptedProposedTransaction.

        #TODO DOC multi-line description of ForecastHandler._annotateAcceptedProposedTransaction.
        #TODO DOC explain how ForecastHandler._annotateAcceptedProposedTransaction participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        forecast_df : object
            #TODO DOC one-line description of ForecastHandler._annotateAcceptedProposedTransaction.forecast_df.

        proposed_row : object
            #TODO DOC one-line description of ForecastHandler._annotateAcceptedProposedTransaction.proposed_row.

        memo_rule_row : object
            #TODO DOC one-line description of ForecastHandler._annotateAcceptedProposedTransaction.memo_rule_row.

        d : object
            #TODO DOC one-line description of ForecastHandler._annotateAcceptedProposedTransaction.d.

        account_set : object
            #TODO DOC one-line description of ForecastHandler._annotateAcceptedProposedTransaction.account_set.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._annotateAcceptedProposedTransaction.log_stack_depth.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._annotateAcceptedProposedTransaction.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._annotateAcceptedProposedTransaction.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._annotateAcceptedProposedTransaction.

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
        elif account_to_type == "loan" or str(account_to).startswith("ALL_LOANS"):
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

    # @profile
    #TODO DOC manual review of ForecastHandler._attemptTransaction docstring
    @classmethod
    def _attemptTransaction(
        cls, end_date, forecast_df, account_set, memo_set, confirmed_df, proposed_row_df, log_stack_depth, include_debug_columns=False
    ):
        """
        #TODO DOC one-line description of ForecastHandler._attemptTransaction.

        #TODO DOC multi-line description of ForecastHandler._attemptTransaction.
        #TODO DOC explain how ForecastHandler._attemptTransaction participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        end_date : date
            #TODO DOC one-line description of ForecastHandler._attemptTransaction.end_date.

        forecast_df : object
            #TODO DOC one-line description of ForecastHandler._attemptTransaction.forecast_df.

        account_set : object
            #TODO DOC one-line description of ForecastHandler._attemptTransaction.account_set.

        memo_set : object
            #TODO DOC one-line description of ForecastHandler._attemptTransaction.memo_set.

        confirmed_df : object
            #TODO DOC one-line description of ForecastHandler._attemptTransaction.confirmed_df.

        proposed_row_df : object
            #TODO DOC one-line description of ForecastHandler._attemptTransaction.proposed_row_df.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._attemptTransaction.log_stack_depth.

        include_debug_columns : bool
            #TODO DOC one-line description of ForecastHandler._attemptTransaction.include_debug_columns.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._attemptTransaction.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._attemptTransaction.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._attemptTransaction.

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

            # Preserve the boundary shortfall so partial-payment callers can
            # reduce the candidate and recursively test the suffix again.
            return e

    # @profile
    #TODO DOC manual review of ForecastHandler._processConfirmedTransactions docstring
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
        #TODO DOC one-line description of ForecastHandler._processConfirmedTransactions.

        #TODO DOC multi-line description of ForecastHandler._processConfirmedTransactions.
        #TODO DOC explain how ForecastHandler._processConfirmedTransactions participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        forecast_df : object
            #TODO DOC one-line description of ForecastHandler._processConfirmedTransactions.forecast_df.

        relevant_confirmed_df : object
            #TODO DOC one-line description of ForecastHandler._processConfirmedTransactions.relevant_confirmed_df.

        memo_set : object
            #TODO DOC one-line description of ForecastHandler._processConfirmedTransactions.memo_set.

        account_set : object
            #TODO DOC one-line description of ForecastHandler._processConfirmedTransactions.account_set.

        d : object
            #TODO DOC one-line description of ForecastHandler._processConfirmedTransactions.d.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._processConfirmedTransactions.log_stack_depth.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._processConfirmedTransactions.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._processConfirmedTransactions.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._processConfirmedTransactions.

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

            if str(memo_rule.account_to).startswith(
                "CURRENT_STATEMENT_BALANCE:"
            ):
                card_name = str(memo_rule.account_to).split(":", 1)[1]
                card = account_set._get_account_by_name(card_name)
                checking = account_set._get_account_by_name(
                    memo_rule.account_from
                )
                confirmed_row.Amount = min(
                    AccountSet._money(confirmed_row.Amount),
                    AccountSet._money(
                        card.billing_state.current_statement_balance
                    ),
                    max(
                        float("0"),
                        AccountSet._money(checking.balance)
                        - AccountSet._money(checking.min_balance),
                    ),
                )

            income_flag = cls._checkIfTxnIsIncome(confirmed_row=confirmed_row, log_stack_depth=log_stack_depth)

            try:
                log_string = str(d) + ' executing txn \''+str(confirmed_row.Memo)
                log_string += '\' '+str(memo_rule.account_from)+ ' -> '+str(memo_rule.account_to)
                log_string += ' for $' + str(confirmed_row.Amount)
                log_in_color(logger, 'white', 'debug', log_string, log_stack_depth)
                # log_in_color(logger, 'white', 'debug', str(d) + ' before txn: ', log_stack_depth)
                # log_in_color(logger, 'white', 'debug', account_set.getAccounts().to_string(), log_stack_depth)
                executed_amount = account_set.executeTransaction(
                    Account_From=memo_rule.account_from,
                    Account_To=memo_rule.account_to,
                    Amount=confirmed_row.Amount,
                    income_flag=income_flag,
                    enforce_policy_minimum=int(confirmed_row.Priority) > 1,
                )
                if executed_amount is not None:
                    confirmed_row.Amount = float(executed_amount)
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
        #TODO DOC one-line description of ForecastHandler._extract_min_payment_amount.

        #TODO DOC multi-line description of ForecastHandler._extract_min_payment_amount.
        #TODO DOC explain how ForecastHandler._extract_min_payment_amount participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        memo_directives : object
            #TODO DOC one-line description of ForecastHandler._extract_min_payment_amount.memo_directives.

        base_account_name : object
            #TODO DOC one-line description of ForecastHandler._extract_min_payment_amount.base_account_name.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._extract_min_payment_amount.log_stack_depth.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._extract_min_payment_amount.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._extract_min_payment_amount.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._extract_min_payment_amount.

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
    #TODO DOC manual review of ForecastHandler._processProposedTransactions docstring
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
        #TODO DOC one-line description of ForecastHandler._processProposedTransactions.

        #TODO DOC multi-line description of ForecastHandler._processProposedTransactions.
        #TODO DOC explain how ForecastHandler._processProposedTransactions participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        end_date : date
            #TODO DOC one-line description of ForecastHandler._processProposedTransactions.end_date.

        account_set : object
            #TODO DOC one-line description of ForecastHandler._processProposedTransactions.account_set.

        forecast_df : object
            #TODO DOC one-line description of ForecastHandler._processProposedTransactions.forecast_df.

        d : object
            #TODO DOC one-line description of ForecastHandler._processProposedTransactions.d.

        memo_set : object
            #TODO DOC one-line description of ForecastHandler._processProposedTransactions.memo_set.

        confirmed_df : object
            #TODO DOC one-line description of ForecastHandler._processProposedTransactions.confirmed_df.

        relevant_proposed_df : object
            #TODO DOC one-line description of ForecastHandler._processProposedTransactions.relevant_proposed_df.

        priority_level : object
            #TODO DOC one-line description of ForecastHandler._processProposedTransactions.priority_level.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._processProposedTransactions.log_stack_depth.

        include_debug_columns : bool
            #TODO DOC one-line description of ForecastHandler._processProposedTransactions.include_debug_columns.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._processProposedTransactions.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._processProposedTransactions.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._processProposedTransactions.

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
            source_name = memo_rule_row["Account_From"]
            destination_name = memo_rule_row["Account_To"]
            source_account = account_set._get_account_by_name(source_name)
            destination_account = account_set._get_account_by_name(destination_name)
            destination_column = destination_name

            # Synthetic surplus sources are resolved against the primary
            # checking balance at execution time.  Once that balance has
            # reached the threshold, executing the transaction is a no-op.
            # Do not send that no-op through the recursive safety forecast:
            # a suffix with an unchanged balance is otherwise considered a
            # successful transaction and the original synthetic proposal is
            # incorrectly confirmed and rendered as a $0 memo.
            if str(source_name).startswith("CHECKING_ABOVE:"):
                threshold = float(str(source_name).split(":", 1)[1])
                executable_surplus = max(
                    float("0"),
                    float(str(source_account.balance)) - threshold,
                )
                if executable_surplus <= MONEY_BOUNDARY_TOLERANCE:
                    new_skipped_df = pd.concat(
                        [new_skipped_df, proposed_row.to_frame().T],
                        ignore_index=True,
                    )
                    continue
                proposed_row["Amount"] = min(
                    float(str(proposed_row["Amount"])),
                    executable_surplus,
                )

            # Active minimum-balance policies constrain optional allocations
            # without becoming hard account boundaries. Resolve the immediate
            # headroom here so the recursive suffix cannot call a policy-floor
            # rejection a successful (but skipped) candidate.
            policy_floor = getattr(source_account, "policy_min_balance", None)
            if policy_floor is not None and int(proposed_row["Priority"]) > 1:
                policy_headroom = max(
                    float("0"),
                    float(str(source_account.balance))
                    - float(str(source_account.effective_policy_min_balance)),
                )
                requested = float(str(proposed_row["Amount"]))
                if requested > policy_headroom:
                    if (
                        bool(proposed_row["Partial_Payment_Allowed"])
                        and policy_headroom > MONEY_BOUNDARY_TOLERANCE
                    ):
                        proposed_row["Amount"] = policy_headroom
                    else:
                        new_skipped_df = pd.concat(
                            [new_skipped_df, proposed_row.to_frame().T],
                            ignore_index=True,
                        )
                        continue

            policy_destination_headroom = None
            if str(destination_name).startswith("SAVINGS_BELOW:"):
                _, threshold, savings_name = str(destination_name).split(":", 2)
                destination_account = account_set._get_account_by_name(savings_name)
                destination_column = savings_name
                policy_destination_headroom = max(
                    float("0"),
                    float(str(threshold)) - float(str(destination_account.balance)),
                )
                if policy_destination_headroom <= MONEY_BOUNDARY_TOLERANCE:
                    new_skipped_df = pd.concat(
                        [new_skipped_df, proposed_row.to_frame().T],
                        ignore_index=True,
                    )
                    continue
            deterministic_endpoints = (
                source_account is not None
                and source_account.account_type == "checking"
                and (
                    destination_name in [None, "", "None"]
                    or (
                        destination_account is not None
                        and destination_account.account_type == "checking"
                    )
                )
            )
            result = None
            if deterministic_endpoints and source_name in forecast_df.columns:
                future_mask = forecast_df["Date"] >= d
                source_headroom = float(str(
                    forecast_df.loc[future_mask, source_name].min()
                )) - float(str(source_account.min_balance))
                destination_headroom = float("Infinity")
                if policy_destination_headroom is not None:
                    destination_headroom = policy_destination_headroom
                if destination_account is not None and not math.isinf(
                    float(destination_account.max_balance)
                ):
                    destination_headroom = min(
                        destination_headroom,
                        float(str(destination_account.max_balance)) - float(str(
                            forecast_df.loc[future_mask, destination_column].max()
                        )),
                    )
                safe_amount = max(
                    float("0"),
                    min(
                        float(str(proposed_row["Amount"])),
                        source_headroom,
                        destination_headroom,
                    ),
                )
                requested_amount = float(str(proposed_row["Amount"]))
                if safe_amount >= requested_amount - MONEY_BOUNDARY_TOLERANCE:
                    result = forecast_df.copy()
                    result.loc[future_mask, source_name] = (
                        pd.to_numeric(result.loc[future_mask, source_name])
                        - float(requested_amount)
                    )
                    if destination_account is not None:
                        result.loc[future_mask, destination_column] = (
                            pd.to_numeric(result.loc[future_mask, destination_column])
                            + float(requested_amount)
                        )
                elif bool(proposed_row["Partial_Payment_Allowed"]) and (
                    safe_amount > MONEY_BOUNDARY_TOLERANCE
                ):
                    proposed_row["Amount"] = safe_amount
                    result = forecast_df.copy()
                    result.loc[future_mask, source_name] = (
                        pd.to_numeric(result.loc[future_mask, source_name])
                        - float(safe_amount)
                    )
                    if destination_account is not None:
                        result.loc[future_mask, destination_column] = (
                            pd.to_numeric(result.loc[future_mask, destination_column])
                            + float(safe_amount)
                        )

                if result is not None:
                    amount = float(str(proposed_row["Amount"]))
                    date_mask = result["Date"] == d
                    if str(destination_name).startswith("SAVINGS_BELOW:"):
                        result.loc[date_mask, "Memo"] += (
                            f"; {proposed_row['Memo']} ({source_name} -${amount}) "
                        )
                        result.loc[date_mask, "Memo Directives"] += (
                            f"; SAVINGS CONTRIBUTION "
                            f"({destination_column} +${amount}) "
                        )
                    elif destination_name in [None, "", "None"]:
                        result.loc[date_mask, "Memo"] += (
                            f"; {proposed_row['Memo']} ({source_name} -${amount}) "
                        )

            if result is None:
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

                logger.debug(
                    "Transaction retry: date=%s reduced_amount=%s depth=%s",
                    d,
                    reduced_amount,
                    log_stack_depth,
                )

                # Re-test the recursively forecast suffix after each boundary-
                # informed reduction. This handles constraints on either the
                # source (future cash needs) or destination (future debt
                # payments), rather than relying only on today's balances.
                for _ in range(8):
                    if reduced_amount <= MONEY_BOUNDARY_TOLERANCE:
                        break
                    proposed_row["Amount"] = reduced_amount
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
                        break
                    shortfall = getattr(result, "boundary_shortfall", None)
                    if shortfall is None or shortfall <= MONEY_BOUNDARY_TOLERANCE:
                        break
                    reduced_amount = max(
                        float("0"),
                        float(str(reduced_amount)) - float(str(shortfall)),
                    )
                    logger.info(
                        "%s recursive suffix rejected the partial transaction; "
                        "reducing it by %s to %s.",
                        d, shortfall, reduced_amount,
                    )

                if reduced_amount > 0:

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
                    enforce_policy_minimum=int(proposed_row["Priority"]) > 1,
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

    #TODO DOC manual review of ForecastHandler._minimum_future_available_balances_as_if_a_cc_payment_did_not_happen docstring
    @classmethod
    def _minimum_future_available_balances_as_if_a_cc_payment_did_not_happen(
        cls, account_set, memo_rule_row, forecast_df, d, log_stack_depth
    ):
        """
        #TODO DOC one-line description of ForecastHandler._minimum_future_available_balances_as_if_a_cc_payment_did_not_happen.

        #TODO DOC multi-line description of ForecastHandler._minimum_future_available_balances_as_if_a_cc_payment_did_not_happen.
        #TODO DOC explain how ForecastHandler._minimum_future_available_balances_as_if_a_cc_payment_did_not_happen participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        account_set : object
            #TODO DOC one-line description of ForecastHandler._minimum_future_available_balances_as_if_a_cc_payment_did_not_happen.account_set.

        memo_rule_row : object
            #TODO DOC one-line description of ForecastHandler._minimum_future_available_balances_as_if_a_cc_payment_did_not_happen.memo_rule_row.

        forecast_df : object
            #TODO DOC one-line description of ForecastHandler._minimum_future_available_balances_as_if_a_cc_payment_did_not_happen.forecast_df.

        d : object
            #TODO DOC one-line description of ForecastHandler._minimum_future_available_balances_as_if_a_cc_payment_did_not_happen.d.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._minimum_future_available_balances_as_if_a_cc_payment_did_not_happen.log_stack_depth.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._minimum_future_available_balances_as_if_a_cc_payment_did_not_happen.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._minimum_future_available_balances_as_if_a_cc_payment_did_not_happen.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._minimum_future_available_balances_as_if_a_cc_payment_did_not_happen.

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

    #TODO DOC make the name of this more clear, and then have codex write the docstring
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
        #TODO DOC one-line description of ForecastHandler._calculate_reduced_amount.

        #TODO DOC multi-line description of ForecastHandler._calculate_reduced_amount.
        #TODO DOC explain how ForecastHandler._calculate_reduced_amount participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        account_set : object
            #TODO DOC one-line description of ForecastHandler._calculate_reduced_amount.account_set.

        memo_rule_row : object
            #TODO DOC one-line description of ForecastHandler._calculate_reduced_amount.memo_rule_row.

        max_available_funds : object
            #TODO DOC one-line description of ForecastHandler._calculate_reduced_amount.max_available_funds.

        forecast_df : object
            #TODO DOC one-line description of ForecastHandler._calculate_reduced_amount.forecast_df.

        d : object
            #TODO DOC one-line description of ForecastHandler._calculate_reduced_amount.d.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._calculate_reduced_amount.log_stack_depth.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._calculate_reduced_amount.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._calculate_reduced_amount.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._calculate_reduced_amount.

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

        source_name = memo_rule_row["Account_From"]
        destination_name = memo_rule_row["Account_To"]
        savings_threshold = None
        if str(destination_name).startswith("SAVINGS_BELOW:"):
            _, threshold_text, destination_name = str(destination_name).split(":", 2)
            savings_threshold = float(threshold_text)

        from_basename_sel_vec = account_base_names == source_name
        to_basename_sel_vec = account_base_names == destination_name

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

        def future_debt_capacity(account_name):
            """Return debt that can be paid now without overpaying it later."""
            account = next(
                (a for a in account_set.accounts if a.name == account_name), None
            )
            if account is None or account_name not in forecast_df.columns:
                return float("0")
            future_rows = forecast_df.loc[forecast_df["Date"] >= d, account_name]
            if future_rows.empty:
                future_balance = float(str(account.balance))
            else:
                future_balance = min(
                    float(str(value)) for value in future_rows.dropna().tolist()
                )
            capacity = max(
                float("0"),
                future_balance - float(str(account.min_balance)),
            )
            # Exact forecast balance columns are captured before the billing-
            # cycle minimum payment on some boundary rows. Reserve that known
            # future reduction explicitly so it is not also consumed by an
            # optional payment today.
            if account.account_type == "credit":
                future_minimum = cls._getFutureMinPaymentAmount(
                    account_name=account_name,
                    account_set=account_set,
                    forecast_df=forecast_df,
                    d=d,
                    log_stack_depth=log_stack_depth,
                )
                capacity = max(
                    float("0"), capacity - float(str(future_minimum))
                )
            return capacity

        if savings_threshold is not None:
            destination_account = account_set._get_account_by_name(destination_name)
            dest_bound = max(
                float("0"),
                savings_threshold - float(str(destination_account.balance)),
            )
        elif destination_name in {"ALL_CREDIT_CARDS", "ALL_CREDIT_CARDS_SNOWBALL"}:
            dest_bound = sum(
                (
                    future_debt_capacity(account.name)
                    for account in account_set.accounts
                    if account.account_type == "credit"
                ),
                float("0"),
            )
        elif destination_name in {"ALL_LOANS", "ALL_LOANS_SNOWBALL"}:
            dest_bound = sum(
                (
                    future_debt_capacity(account.name)
                    for account in account_set.accounts
                    if account.account_type == "loan"
                ),
                float("0"),
            )
        elif dest_account_type == "credit":
            dest_bound = future_debt_capacity(destination_name)
        elif dest_account_type == "checking":
            raise NotImplementedError
        elif dest_account_type == "loan":
            dest_bound = future_debt_capacity(destination_name)
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
    #TODO DOC manual review of ForecastHandler._update_forecast_with_hypothetical docstring
    @classmethod
    def _update_forecast_with_hypothetical(
        cls, forecast_df, hypothetical_forecast, d, log_stack_depth
    ):
        # Split the forecast into past and future
        """
        #TODO DOC one-line description of ForecastHandler._update_forecast_with_hypothetical.

        #TODO DOC multi-line description of ForecastHandler._update_forecast_with_hypothetical.
        #TODO DOC explain how ForecastHandler._update_forecast_with_hypothetical participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        forecast_df : object
            #TODO DOC one-line description of ForecastHandler._update_forecast_with_hypothetical.forecast_df.

        hypothetical_forecast : object
            #TODO DOC one-line description of ForecastHandler._update_forecast_with_hypothetical.hypothetical_forecast.

        d : object
            #TODO DOC one-line description of ForecastHandler._update_forecast_with_hypothetical.d.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._update_forecast_with_hypothetical.log_stack_depth.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._update_forecast_with_hypothetical.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._update_forecast_with_hypothetical.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._update_forecast_with_hypothetical.

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
                if isinstance(balance, float) and forecast_df[account_name].dtype != object:
                    forecast_df[account_name] = forecast_df[account_name].astype(object)
                forecast_df.loc[forecast_df["Date"] == d, account_name] = (
                    balance
                )

    # account_set, forecast_df, date, memo_set,              ,    relevant_deferred_df,             priority_level, allow_partial_payments, allow_skip_and_defer
    # @profile
    #TODO DOC manual review of ForecastHandler._processDeferredTransactions docstring
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
        #TODO DOC one-line description of ForecastHandler._processDeferredTransactions.

        #TODO DOC multi-line description of ForecastHandler._processDeferredTransactions.
        #TODO DOC explain how ForecastHandler._processDeferredTransactions participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        start_date : date
            #TODO DOC one-line description of ForecastHandler._processDeferredTransactions.start_date.

        end_date : date
            #TODO DOC one-line description of ForecastHandler._processDeferredTransactions.end_date.

        account_set : object
            #TODO DOC one-line description of ForecastHandler._processDeferredTransactions.account_set.

        forecast_df : object
            #TODO DOC one-line description of ForecastHandler._processDeferredTransactions.forecast_df.

        d : object
            #TODO DOC one-line description of ForecastHandler._processDeferredTransactions.d.

        memo_set : object
            #TODO DOC one-line description of ForecastHandler._processDeferredTransactions.memo_set.

        relevant_deferred_df : object
            #TODO DOC one-line description of ForecastHandler._processDeferredTransactions.relevant_deferred_df.

        priority_level : object
            #TODO DOC one-line description of ForecastHandler._processDeferredTransactions.priority_level.

        confirmed_df : object
            #TODO DOC one-line description of ForecastHandler._processDeferredTransactions.confirmed_df.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._processDeferredTransactions.log_stack_depth.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._processDeferredTransactions.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._processDeferredTransactions.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._processDeferredTransactions.

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
            memo_rule = memo_set.findMatchingMemoRule(
                deferred_row["Memo"], deferred_row["Priority"]
            )

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
                    log_stack_depth=log_stack_depth,
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
                    Account_From=memo_rule.account_from,
                    Account_To=memo_rule.account_to,
                    Amount=deferred_row["Amount"],
                    income_flag=False,
                )

                # Add the transaction to the new confirmed DataFrame
                new_confirmed_df = pd.concat(
                    [new_confirmed_df, deferred_row.to_frame().T],
                    ignore_index=True,
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
                        ] = float(account_balance)
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
        return forecast_df, new_confirmed_df, new_deferred_df

    # @profile
    #TODO DOC manual review of ForecastHandler._executeTransactionsForDay docstring
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
        #TODO DOC one-line description of ForecastHandler._executeTransactionsForDay.

        #TODO DOC multi-line description of ForecastHandler._executeTransactionsForDay.
        #TODO DOC explain how ForecastHandler._executeTransactionsForDay participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        end_date : date
            #TODO DOC one-line description of ForecastHandler._executeTransactionsForDay.end_date.

        account_set : object
            #TODO DOC one-line description of ForecastHandler._executeTransactionsForDay.account_set.

        forecast_df : object
            #TODO DOC one-line description of ForecastHandler._executeTransactionsForDay.forecast_df.

        d : object
            #TODO DOC one-line description of ForecastHandler._executeTransactionsForDay.d.

        memo_set : object
            #TODO DOC one-line description of ForecastHandler._executeTransactionsForDay.memo_set.

        confirmed_df : object
            #TODO DOC one-line description of ForecastHandler._executeTransactionsForDay.confirmed_df.

        proposed_df : object
            #TODO DOC one-line description of ForecastHandler._executeTransactionsForDay.proposed_df.

        deferred_df : object
            #TODO DOC one-line description of ForecastHandler._executeTransactionsForDay.deferred_df.

        skipped_df : object
            #TODO DOC one-line description of ForecastHandler._executeTransactionsForDay.skipped_df.

        priority_level : object
            #TODO DOC one-line description of ForecastHandler._executeTransactionsForDay.priority_level.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._executeTransactionsForDay.log_stack_depth.

        include_debug_columns : bool
            #TODO DOC one-line description of ForecastHandler._executeTransactionsForDay.include_debug_columns.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._executeTransactionsForDay.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._executeTransactionsForDay.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._executeTransactionsForDay.

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
                    cls._processDeferredTransactions(
                        start_date=forecast_df["Date"].min(),
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
    #TODO DOC manual review of ForecastHandler._processCreditCardBillingDayForDay docstring
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
        #TODO DOC one-line description of ForecastHandler._processCreditCardBillingDayForDay.

        #TODO DOC multi-line description of ForecastHandler._processCreditCardBillingDayForDay.
        #TODO DOC explain how ForecastHandler._processCreditCardBillingDayForDay participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        account_set : object
            #TODO DOC one-line description of ForecastHandler._processCreditCardBillingDayForDay.account_set.

        current_forecast_row_df : object
            #TODO DOC one-line description of ForecastHandler._processCreditCardBillingDayForDay.current_forecast_row_df.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._processCreditCardBillingDayForDay.log_stack_depth.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._processCreditCardBillingDayForDay.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._processCreditCardBillingDayForDay.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._processCreditCardBillingDayForDay.

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
    #TODO DOC manual review of ForecastHandler._calculateLoanInterestAccrualsForDay docstring
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
        #TODO DOC one-line description of ForecastHandler._calculateLoanInterestAccrualsForDay.

        #TODO DOC multi-line description of ForecastHandler._calculateLoanInterestAccrualsForDay.
        #TODO DOC explain how ForecastHandler._calculateLoanInterestAccrualsForDay participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        account_set : object
            #TODO DOC one-line description of ForecastHandler._calculateLoanInterestAccrualsForDay.account_set.

        current_forecast_row_df : object
            #TODO DOC one-line description of ForecastHandler._calculateLoanInterestAccrualsForDay.current_forecast_row_df.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._calculateLoanInterestAccrualsForDay.log_stack_depth.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._calculateLoanInterestAccrualsForDay.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._calculateLoanInterestAccrualsForDay.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._calculateLoanInterestAccrualsForDay.

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
    #TODO DOC manual review of ForecastHandler._executeCreditCardMinimumPayments docstring
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
        #TODO DOC one-line description of ForecastHandler._executeCreditCardMinimumPayments.

        #TODO DOC multi-line description of ForecastHandler._executeCreditCardMinimumPayments.
        #TODO DOC explain how ForecastHandler._executeCreditCardMinimumPayments participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        forecast_df : object
            #TODO DOC one-line description of ForecastHandler._executeCreditCardMinimumPayments.forecast_df.

        account_set : object
            #TODO DOC one-line description of ForecastHandler._executeCreditCardMinimumPayments.account_set.

        current_forecast_row_df : object
            #TODO DOC one-line description of ForecastHandler._executeCreditCardMinimumPayments.current_forecast_row_df.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._executeCreditCardMinimumPayments.log_stack_depth.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._executeCreditCardMinimumPayments.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._executeCreditCardMinimumPayments.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._executeCreditCardMinimumPayments.

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
    #TODO DOC manual review of ForecastHandler._executeLoanMinimumPayments docstring
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
        #TODO DOC one-line description of ForecastHandler._executeLoanMinimumPayments.

        #TODO DOC multi-line description of ForecastHandler._executeLoanMinimumPayments.
        #TODO DOC explain how ForecastHandler._executeLoanMinimumPayments participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        account_set : object
            #TODO DOC one-line description of ForecastHandler._executeLoanMinimumPayments.account_set.

        current_forecast_row_df : object
            #TODO DOC one-line description of ForecastHandler._executeLoanMinimumPayments.current_forecast_row_df.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._executeLoanMinimumPayments.log_stack_depth.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._executeLoanMinimumPayments.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._executeLoanMinimumPayments.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._executeLoanMinimumPayments.

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
        #TODO DOC one-line description of ForecastHandler._getMinimumFutureAvailableBalances.

        #TODO DOC multi-line description of ForecastHandler._getMinimumFutureAvailableBalances.
        #TODO DOC explain how ForecastHandler._getMinimumFutureAvailableBalances participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        account_set : object
            #TODO DOC one-line description of ForecastHandler._getMinimumFutureAvailableBalances.account_set.

        forecast_df : object
            #TODO DOC one-line description of ForecastHandler._getMinimumFutureAvailableBalances.forecast_df.

        d : object
            #TODO DOC one-line description of ForecastHandler._getMinimumFutureAvailableBalances.d.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._getMinimumFutureAvailableBalances.log_stack_depth.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._getMinimumFutureAvailableBalances.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._getMinimumFutureAvailableBalances.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._getMinimumFutureAvailableBalances.

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
    #TODO DOC manual review of ForecastHandler._sync_account_set_w_forecast_day docstring
    @classmethod
    def _sync_account_set_w_forecast_day(cls, account_set, forecast_df, d, log_stack_depth):
        # log_in_color(logger, 'white', 'debug', str(d)+' ENTER _sync_account_set_w_forecast_day', log_stack_depth)
        """
        #TODO DOC one-line description of ForecastHandler._sync_account_set_w_forecast_day.

        #TODO DOC multi-line description of ForecastHandler._sync_account_set_w_forecast_day.
        #TODO DOC explain how ForecastHandler._sync_account_set_w_forecast_day participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        account_set : object
            #TODO DOC one-line description of ForecastHandler._sync_account_set_w_forecast_day.account_set.

        forecast_df : object
            #TODO DOC one-line description of ForecastHandler._sync_account_set_w_forecast_day.forecast_df.

        d : object
            #TODO DOC one-line description of ForecastHandler._sync_account_set_w_forecast_day.d.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._sync_account_set_w_forecast_day.log_stack_depth.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._sync_account_set_w_forecast_day.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._sync_account_set_w_forecast_day.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._sync_account_set_w_forecast_day.

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
                account.billing_state.balance = float(str(relevant_balance))
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
                    billing_state.current_statement_balance = float(
                        str(relevant_forecast_day[curr_column].iat[0])
                    )
                    billing_state_updated = True
                if prev_column in relevant_forecast_day.columns:
                    billing_state.previous_statement_balance = float(
                        str(relevant_forecast_day[prev_column].iat[0])
                    )
                    billing_state_updated = True
                if payment_column in relevant_forecast_day.columns:
                    billing_state.billing_cycle_payment_balance = float(
                        str(relevant_forecast_day[payment_column].iat[0])
                    )
                    billing_state_updated = True
                if end_of_previous_cycle_column in relevant_forecast_day.columns:
                    billing_state.end_of_previous_cycle_balance = float(
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
                    billing_state.principal_balance = float(
                        str(relevant_forecast_day[principal_column].iat[0])
                    )
                    billing_state_updated = True
                if interest_column in relevant_forecast_day.columns:
                    billing_state.interest_balance = float(
                        str(relevant_forecast_day[interest_column].iat[0])
                    )
                    billing_state_updated = True
                if payment_column in relevant_forecast_day.columns:
                    billing_state.billing_cycle_payment_balance = float(
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
        #TODO DOC one-line description of ForecastHandler._apply_credit_billing_state_delta_to_forecast_row.

        #TODO DOC multi-line description of ForecastHandler._apply_credit_billing_state_delta_to_forecast_row.
        #TODO DOC explain how ForecastHandler._apply_credit_billing_state_delta_to_forecast_row participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        forecast_df : object
            #TODO DOC one-line description of ForecastHandler._apply_credit_billing_state_delta_to_forecast_row.forecast_df.

        row_index : object
            #TODO DOC one-line description of ForecastHandler._apply_credit_billing_state_delta_to_forecast_row.row_index.

        account_set : object
            #TODO DOC one-line description of ForecastHandler._apply_credit_billing_state_delta_to_forecast_row.account_set.

        credit_account_name : str
            #TODO DOC one-line description of ForecastHandler._apply_credit_billing_state_delta_to_forecast_row.credit_account_name.

        checking_account_name : object
            #TODO DOC one-line description of ForecastHandler._apply_credit_billing_state_delta_to_forecast_row.checking_account_name.

        checking_delta : float
            #TODO DOC one-line description of ForecastHandler._apply_credit_billing_state_delta_to_forecast_row.checking_delta.

        current_statement_delta : float
            #TODO DOC one-line description of ForecastHandler._apply_credit_billing_state_delta_to_forecast_row.current_statement_delta.

        previous_statement_delta : float
            #TODO DOC one-line description of ForecastHandler._apply_credit_billing_state_delta_to_forecast_row.previous_statement_delta.

        billing_cycle_payment_delta : float
            #TODO DOC one-line description of ForecastHandler._apply_credit_billing_state_delta_to_forecast_row.billing_cycle_payment_delta.

        end_of_previous_cycle_delta : float
            #TODO DOC one-line description of ForecastHandler._apply_credit_billing_state_delta_to_forecast_row.end_of_previous_cycle_delta.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._apply_credit_billing_state_delta_to_forecast_row.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._apply_credit_billing_state_delta_to_forecast_row.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._apply_credit_billing_state_delta_to_forecast_row.

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
        #TODO DOC one-line description of ForecastHandler._apply_loan_billing_state_delta_to_forecast_row.

        #TODO DOC multi-line description of ForecastHandler._apply_loan_billing_state_delta_to_forecast_row.
        #TODO DOC explain how ForecastHandler._apply_loan_billing_state_delta_to_forecast_row participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        forecast_df : object
            #TODO DOC one-line description of ForecastHandler._apply_loan_billing_state_delta_to_forecast_row.forecast_df.

        row_index : object
            #TODO DOC one-line description of ForecastHandler._apply_loan_billing_state_delta_to_forecast_row.row_index.

        account_set : object
            #TODO DOC one-line description of ForecastHandler._apply_loan_billing_state_delta_to_forecast_row.account_set.

        loan_account_name : str
            #TODO DOC one-line description of ForecastHandler._apply_loan_billing_state_delta_to_forecast_row.loan_account_name.

        checking_account_name : object
            #TODO DOC one-line description of ForecastHandler._apply_loan_billing_state_delta_to_forecast_row.checking_account_name.

        checking_delta : float
            #TODO DOC one-line description of ForecastHandler._apply_loan_billing_state_delta_to_forecast_row.checking_delta.

        principal_delta : float
            #TODO DOC one-line description of ForecastHandler._apply_loan_billing_state_delta_to_forecast_row.principal_delta.

        interest_delta : float
            #TODO DOC one-line description of ForecastHandler._apply_loan_billing_state_delta_to_forecast_row.interest_delta.

        billing_cycle_payment_delta : float
            #TODO DOC one-line description of ForecastHandler._apply_loan_billing_state_delta_to_forecast_row.billing_cycle_payment_delta.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._apply_loan_billing_state_delta_to_forecast_row.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._apply_loan_billing_state_delta_to_forecast_row.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._apply_loan_billing_state_delta_to_forecast_row.

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
        #TODO DOC one-line description of ForecastHandler._propagate_credit_txn_curr_only.

        #TODO DOC multi-line description of ForecastHandler._propagate_credit_txn_curr_only.
        #TODO DOC explain how ForecastHandler._propagate_credit_txn_curr_only participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        relevant_account_info_df : object
            #TODO DOC one-line description of ForecastHandler._propagate_credit_txn_curr_only.relevant_account_info_df.

        account_deltas_list : object
            #TODO DOC one-line description of ForecastHandler._propagate_credit_txn_curr_only.account_deltas_list.

        future_rows_only_df : object
            #TODO DOC one-line description of ForecastHandler._propagate_credit_txn_curr_only.future_rows_only_df.

        forecast_df : object
            #TODO DOC one-line description of ForecastHandler._propagate_credit_txn_curr_only.forecast_df.

        account_set_before_p2_plus_txn : object
            #TODO DOC one-line description of ForecastHandler._propagate_credit_txn_curr_only.account_set_before_p2_plus_txn.

        billing_dates_dict : object
            #TODO DOC one-line description of ForecastHandler._propagate_credit_txn_curr_only.billing_dates_dict.

        d : object
            #TODO DOC one-line description of ForecastHandler._propagate_credit_txn_curr_only.d.

        post_txn_row_df : object
            #TODO DOC one-line description of ForecastHandler._propagate_credit_txn_curr_only.post_txn_row_df.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._propagate_credit_txn_curr_only.log_stack_depth.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._propagate_credit_txn_curr_only.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._propagate_credit_txn_curr_only.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._propagate_credit_txn_curr_only.

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
        #TODO DOC one-line description of ForecastHandler._propagate_credit_payment_curr_only.

        #TODO DOC multi-line description of ForecastHandler._propagate_credit_payment_curr_only.
        #TODO DOC explain how ForecastHandler._propagate_credit_payment_curr_only participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        relevant_account_info_df : object
            #TODO DOC one-line description of ForecastHandler._propagate_credit_payment_curr_only.relevant_account_info_df.

        account_deltas_list : object
            #TODO DOC one-line description of ForecastHandler._propagate_credit_payment_curr_only.account_deltas_list.

        future_rows_only_df : object
            #TODO DOC one-line description of ForecastHandler._propagate_credit_payment_curr_only.future_rows_only_df.

        forecast_df : object
            #TODO DOC one-line description of ForecastHandler._propagate_credit_payment_curr_only.forecast_df.

        account_set_before_p2_plus_txn : object
            #TODO DOC one-line description of ForecastHandler._propagate_credit_payment_curr_only.account_set_before_p2_plus_txn.

        billing_dates_dict : object
            #TODO DOC one-line description of ForecastHandler._propagate_credit_payment_curr_only.billing_dates_dict.

        d : object
            #TODO DOC one-line description of ForecastHandler._propagate_credit_payment_curr_only.d.

        post_txn_row_df : object
            #TODO DOC one-line description of ForecastHandler._propagate_credit_payment_curr_only.post_txn_row_df.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._propagate_credit_payment_curr_only.log_stack_depth.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._propagate_credit_payment_curr_only.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._propagate_credit_payment_curr_only.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._propagate_credit_payment_curr_only.

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
        #TODO DOC one-line description of ForecastHandler._propagate_credit_payment_prev_only.

        #TODO DOC multi-line description of ForecastHandler._propagate_credit_payment_prev_only.
        #TODO DOC explain how ForecastHandler._propagate_credit_payment_prev_only participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        relevant_account_info_df : object
            #TODO DOC one-line description of ForecastHandler._propagate_credit_payment_prev_only.relevant_account_info_df.

        account_deltas_list : object
            #TODO DOC one-line description of ForecastHandler._propagate_credit_payment_prev_only.account_deltas_list.

        future_rows_only_df : object
            #TODO DOC one-line description of ForecastHandler._propagate_credit_payment_prev_only.future_rows_only_df.

        forecast_df : object
            #TODO DOC one-line description of ForecastHandler._propagate_credit_payment_prev_only.forecast_df.

        account_set_before_p2_plus_txn : object
            #TODO DOC one-line description of ForecastHandler._propagate_credit_payment_prev_only.account_set_before_p2_plus_txn.

        billing_dates_dict : object
            #TODO DOC one-line description of ForecastHandler._propagate_credit_payment_prev_only.billing_dates_dict.

        d : object
            #TODO DOC one-line description of ForecastHandler._propagate_credit_payment_prev_only.d.

        post_txn_row_df : object
            #TODO DOC one-line description of ForecastHandler._propagate_credit_payment_prev_only.post_txn_row_df.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._propagate_credit_payment_prev_only.log_stack_depth.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._propagate_credit_payment_prev_only.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._propagate_credit_payment_prev_only.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._propagate_credit_payment_prev_only.

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
        #TODO DOC one-line description of ForecastHandler._propagate_loan_payment_interest_only.

        #TODO DOC multi-line description of ForecastHandler._propagate_loan_payment_interest_only.
        #TODO DOC explain how ForecastHandler._propagate_loan_payment_interest_only participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        relevant_account_info_df : object
            #TODO DOC one-line description of ForecastHandler._propagate_loan_payment_interest_only.relevant_account_info_df.

        account_deltas_list : object
            #TODO DOC one-line description of ForecastHandler._propagate_loan_payment_interest_only.account_deltas_list.

        future_rows_only_df : object
            #TODO DOC one-line description of ForecastHandler._propagate_loan_payment_interest_only.future_rows_only_df.

        forecast_df : object
            #TODO DOC one-line description of ForecastHandler._propagate_loan_payment_interest_only.forecast_df.

        account_set_before_p2_plus_txn : object
            #TODO DOC one-line description of ForecastHandler._propagate_loan_payment_interest_only.account_set_before_p2_plus_txn.

        billing_dates_dict : object
            #TODO DOC one-line description of ForecastHandler._propagate_loan_payment_interest_only.billing_dates_dict.

        date_string : object
            #TODO DOC one-line description of ForecastHandler._propagate_loan_payment_interest_only.date_string.

        post_txn_row_df : object
            #TODO DOC one-line description of ForecastHandler._propagate_loan_payment_interest_only.post_txn_row_df.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._propagate_loan_payment_interest_only.log_stack_depth.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._propagate_loan_payment_interest_only.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._propagate_loan_payment_interest_only.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._propagate_loan_payment_interest_only.

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
        #TODO DOC one-line description of ForecastHandler._propagate_loan_payment_pbal_only.

        #TODO DOC multi-line description of ForecastHandler._propagate_loan_payment_pbal_only.
        #TODO DOC explain how ForecastHandler._propagate_loan_payment_pbal_only participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        relevant_account_info_df : object
            #TODO DOC one-line description of ForecastHandler._propagate_loan_payment_pbal_only.relevant_account_info_df.

        account_deltas_list : object
            #TODO DOC one-line description of ForecastHandler._propagate_loan_payment_pbal_only.account_deltas_list.

        future_rows_only_df : object
            #TODO DOC one-line description of ForecastHandler._propagate_loan_payment_pbal_only.future_rows_only_df.

        forecast_df : object
            #TODO DOC one-line description of ForecastHandler._propagate_loan_payment_pbal_only.forecast_df.

        account_set_before_p2_plus_txn : object
            #TODO DOC one-line description of ForecastHandler._propagate_loan_payment_pbal_only.account_set_before_p2_plus_txn.

        billing_dates_dict : object
            #TODO DOC one-line description of ForecastHandler._propagate_loan_payment_pbal_only.billing_dates_dict.

        date_string : object
            #TODO DOC one-line description of ForecastHandler._propagate_loan_payment_pbal_only.date_string.

        post_txn_row_df : object
            #TODO DOC one-line description of ForecastHandler._propagate_loan_payment_pbal_only.post_txn_row_df.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._propagate_loan_payment_pbal_only.log_stack_depth.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._propagate_loan_payment_pbal_only.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._propagate_loan_payment_pbal_only.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._propagate_loan_payment_pbal_only.

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
        #TODO DOC one-line description of ForecastHandler._propagate_loan_payment_pbal_interest.

        #TODO DOC multi-line description of ForecastHandler._propagate_loan_payment_pbal_interest.
        #TODO DOC explain how ForecastHandler._propagate_loan_payment_pbal_interest participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        relevant_account_info_df : object
            #TODO DOC one-line description of ForecastHandler._propagate_loan_payment_pbal_interest.relevant_account_info_df.

        account_deltas_list : object
            #TODO DOC one-line description of ForecastHandler._propagate_loan_payment_pbal_interest.account_deltas_list.

        future_rows_only_df : object
            #TODO DOC one-line description of ForecastHandler._propagate_loan_payment_pbal_interest.future_rows_only_df.

        forecast_df : object
            #TODO DOC one-line description of ForecastHandler._propagate_loan_payment_pbal_interest.forecast_df.

        account_set_before_p2_plus_txn : object
            #TODO DOC one-line description of ForecastHandler._propagate_loan_payment_pbal_interest.account_set_before_p2_plus_txn.

        billing_dates_dict : object
            #TODO DOC one-line description of ForecastHandler._propagate_loan_payment_pbal_interest.billing_dates_dict.

        date_string : object
            #TODO DOC one-line description of ForecastHandler._propagate_loan_payment_pbal_interest.date_string.

        post_txn_row_df : object
            #TODO DOC one-line description of ForecastHandler._propagate_loan_payment_pbal_interest.post_txn_row_df.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._propagate_loan_payment_pbal_interest.log_stack_depth.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._propagate_loan_payment_pbal_interest.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._propagate_loan_payment_pbal_interest.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._propagate_loan_payment_pbal_interest.

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

            # print(pd.DataFrame(f_row).T.to_string())

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
        #TODO DOC one-line description of ForecastHandler._propagate_credit_payment_prev_curr.

        #TODO DOC multi-line description of ForecastHandler._propagate_credit_payment_prev_curr.
        #TODO DOC explain how ForecastHandler._propagate_credit_payment_prev_curr participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        relevant_account_info_df : object
            #TODO DOC one-line description of ForecastHandler._propagate_credit_payment_prev_curr.relevant_account_info_df.

        account_deltas_list : object
            #TODO DOC one-line description of ForecastHandler._propagate_credit_payment_prev_curr.account_deltas_list.

        future_rows_only_df : object
            #TODO DOC one-line description of ForecastHandler._propagate_credit_payment_prev_curr.future_rows_only_df.

        forecast_df : object
            #TODO DOC one-line description of ForecastHandler._propagate_credit_payment_prev_curr.forecast_df.

        account_set_before_p2_plus_txn : object
            #TODO DOC one-line description of ForecastHandler._propagate_credit_payment_prev_curr.account_set_before_p2_plus_txn.

        billing_dates_dict : object
            #TODO DOC one-line description of ForecastHandler._propagate_credit_payment_prev_curr.billing_dates_dict.

        d : object
            #TODO DOC one-line description of ForecastHandler._propagate_credit_payment_prev_curr.d.

        post_txn_row_df : object
            #TODO DOC one-line description of ForecastHandler._propagate_credit_payment_prev_curr.post_txn_row_df.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._propagate_credit_payment_prev_curr.log_stack_depth.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._propagate_credit_payment_prev_curr.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._propagate_credit_payment_prev_curr.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._propagate_credit_payment_prev_curr.

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
                # print("DAY AFTER BILLING DATE")
                if f_i == 0:
                    updated_eopc = post_txn_row_df[prev_stmt_bal_account_name].iat[0]
                else:
                    updated_eopc = future_rows_only_df.at[
                        f_i - 1, prev_stmt_bal_account_name
                    ]
                old_eopc = future_rows_only_df.at[f_i, eopc_account_name]
                # print("eopc_delta = " + str(updated_eopc - old_eopc))
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
        #TODO DOC one-line description of ForecastHandler._parse_memo_amount.

        #TODO DOC multi-line description of ForecastHandler._parse_memo_amount.
        #TODO DOC explain how ForecastHandler._parse_memo_amount participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        memo_line : object
            #TODO DOC one-line description of ForecastHandler._parse_memo_amount.memo_line.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._parse_memo_amount.log_stack_depth.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._parse_memo_amount.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._parse_memo_amount.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._parse_memo_amount.

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
        #TODO DOC one-line description of ForecastHandler._update_memo_amount.

        #TODO DOC multi-line description of ForecastHandler._update_memo_amount.
        #TODO DOC explain how ForecastHandler._update_memo_amount participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        memo_line : object
            #TODO DOC one-line description of ForecastHandler._update_memo_amount.memo_line.

        new_amount : object
            #TODO DOC one-line description of ForecastHandler._update_memo_amount.new_amount.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._update_memo_amount.log_stack_depth.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._update_memo_amount.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._update_memo_amount.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._update_memo_amount.

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
    #TODO DOC manual review of ForecastHandler._propagateOptimizationTransactionsIntoTheFuture docstring
    @classmethod
    def _propagateOptimizationTransactionsIntoTheFuture(
        cls, end_date, account_set_before_p2_plus_txn, forecast_df, date_string, log_stack_depth, include_debug_columns=False #TODO unsure if include_debug_columns belongs here
    ):
        """
        #TODO DOC one-line description of ForecastHandler._propagateOptimizationTransactionsIntoTheFuture.

        #TODO DOC multi-line description of ForecastHandler._propagateOptimizationTransactionsIntoTheFuture.
        #TODO DOC explain how ForecastHandler._propagateOptimizationTransactionsIntoTheFuture participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        end_date : date
            #TODO DOC one-line description of ForecastHandler._propagateOptimizationTransactionsIntoTheFuture.end_date.

        account_set_before_p2_plus_txn : object
            #TODO DOC one-line description of ForecastHandler._propagateOptimizationTransactionsIntoTheFuture.account_set_before_p2_plus_txn.

        forecast_df : object
            #TODO DOC one-line description of ForecastHandler._propagateOptimizationTransactionsIntoTheFuture.forecast_df.

        date_string : object
            #TODO DOC one-line description of ForecastHandler._propagateOptimizationTransactionsIntoTheFuture.date_string.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._propagateOptimizationTransactionsIntoTheFuture.log_stack_depth.

        include_debug_columns : bool
            #TODO DOC one-line description of ForecastHandler._propagateOptimizationTransactionsIntoTheFuture.include_debug_columns.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._propagateOptimizationTransactionsIntoTheFuture.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._propagateOptimizationTransactionsIntoTheFuture.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._propagateOptimizationTransactionsIntoTheFuture.

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
        debt_component_types = ["principal balance", "interest"]
        is_debt_component = A_df["Account_Type"].isin(debt_component_types)
        violations = account_deltas[is_debt_component] > 0
        checking_deltas = account_deltas[A_df["Account_Type"].eq("checking")]
        checking_created_value = (
            sum(float(str(delta)) for delta in checking_deltas)
            > MONEY_BOUNDARY_TOLERANCE
        )

        if violations.any() or checking_created_value:
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
        account_delta_total = sum(float(str(delta)) for delta in account_deltas_list)

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
                    # Investment transfers do not alter debt billing state.  The
                    # optimization path can therefore propagate their account
                    # deltas directly; subsequent daily investment-return
                    # processing continues from the adjusted balances.
                    if (
                        account_types_set.issubset({"checking", "investment"})
                        or account_types_set.issubset({"checking", "loan"})
                        or account_types_set.issubset({"checking", "credit"})
                    ):
                        for _, delta_row in accounts_with_base_name_and_delta.iterrows():
                            account_name = delta_row["Name"]
                            delta = delta_row["Delta"]
                            if account_name in future_rows_only_df.columns:
                                future_rows_only_df[account_name] = (
                                    future_rows_only_df[account_name] + float(delta)
                                )
                        continue
                    log_stack_depth -= 1
                    # log_in_color(
                    #     logger,
                    #     "white",
                    #     "debug",
                    #     str(date_string)
                    #     + " EXIT _propagateOptimizationTransactionsIntoTheFuture",
                    #     log_stack_depth,
                    # )
                    raise ValueError(
                        "Undefined account-type combination in transaction propagation: "
                        f"{sorted(account_types_set)}"
                    )

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
        #TODO DOC one-line description of ForecastHandler._updateProposedTransactionsBasedOnOtherSets.

        #TODO DOC multi-line description of ForecastHandler._updateProposedTransactionsBasedOnOtherSets.
        #TODO DOC explain how ForecastHandler._updateProposedTransactionsBasedOnOtherSets participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        confirmed_df : object
            #TODO DOC one-line description of ForecastHandler._updateProposedTransactionsBasedOnOtherSets.confirmed_df.

        proposed_df : object
            #TODO DOC one-line description of ForecastHandler._updateProposedTransactionsBasedOnOtherSets.proposed_df.

        deferred_df : object
            #TODO DOC one-line description of ForecastHandler._updateProposedTransactionsBasedOnOtherSets.deferred_df.

        skipped_df : object
            #TODO DOC one-line description of ForecastHandler._updateProposedTransactionsBasedOnOtherSets.skipped_df.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._updateProposedTransactionsBasedOnOtherSets.log_stack_depth.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._updateProposedTransactionsBasedOnOtherSets.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._updateProposedTransactionsBasedOnOtherSets.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._updateProposedTransactionsBasedOnOtherSets.

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

    # @profile
    #TODO DOC manual review of ForecastHandler._assessPotentialOptimizations docstring
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
        #TODO DOC one-line description of ForecastHandler._assessPotentialOptimizations.

        #TODO DOC multi-line description of ForecastHandler._assessPotentialOptimizations.
        #TODO DOC explain how ForecastHandler._assessPotentialOptimizations participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        end_date : date
            #TODO DOC one-line description of ForecastHandler._assessPotentialOptimizations.end_date.

        forecast_df : object
            #TODO DOC one-line description of ForecastHandler._assessPotentialOptimizations.forecast_df.

        account_set : object
            #TODO DOC one-line description of ForecastHandler._assessPotentialOptimizations.account_set.

        memo_rule_set : object
            #TODO DOC one-line description of ForecastHandler._assessPotentialOptimizations.memo_rule_set.

        confirmed_df : object
            #TODO DOC one-line description of ForecastHandler._assessPotentialOptimizations.confirmed_df.

        proposed_df : object
            #TODO DOC one-line description of ForecastHandler._assessPotentialOptimizations.proposed_df.

        deferred_df : object
            #TODO DOC one-line description of ForecastHandler._assessPotentialOptimizations.deferred_df.

        skipped_df : object
            #TODO DOC one-line description of ForecastHandler._assessPotentialOptimizations.skipped_df.

        raise__satisfice_failed_exception : object
            #TODO DOC one-line description of ForecastHandler._assessPotentialOptimizations.raise__satisfice_failed_exception.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._assessPotentialOptimizations.log_stack_depth.

        progress_bar : object
            #TODO DOC one-line description of ForecastHandler._assessPotentialOptimizations.progress_bar.

        include_debug_columns : bool
            #TODO DOC one-line description of ForecastHandler._assessPotentialOptimizations.include_debug_columns.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._assessPotentialOptimizations.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._assessPotentialOptimizations.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._assessPotentialOptimizations.

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
                        progress_bar.update(1, context=f"P{priority_index} {d}")
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
        #TODO DOC one-line description of ForecastHandler._cleanUpAfterFailedSatisfice.

        #TODO DOC multi-line description of ForecastHandler._cleanUpAfterFailedSatisfice.
        #TODO DOC explain how ForecastHandler._cleanUpAfterFailedSatisfice participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        end_date : date
            #TODO DOC one-line description of ForecastHandler._cleanUpAfterFailedSatisfice.end_date.

        confirmed_df : object
            #TODO DOC one-line description of ForecastHandler._cleanUpAfterFailedSatisfice.confirmed_df.

        proposed_df : object
            #TODO DOC one-line description of ForecastHandler._cleanUpAfterFailedSatisfice.proposed_df.

        deferred_df : object
            #TODO DOC one-line description of ForecastHandler._cleanUpAfterFailedSatisfice.deferred_df.

        skipped_df : object
            #TODO DOC one-line description of ForecastHandler._cleanUpAfterFailedSatisfice.skipped_df.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._cleanUpAfterFailedSatisfice.log_stack_depth.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._cleanUpAfterFailedSatisfice.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._cleanUpAfterFailedSatisfice.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._cleanUpAfterFailedSatisfice.

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

    #TODO DOC manual review of ForecastHandler._updateEndOfPrevCycleBal docstring
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
        #TODO DOC one-line description of ForecastHandler._updateEndOfPrevCycleBal.

        #TODO DOC multi-line description of ForecastHandler._updateEndOfPrevCycleBal.
        #TODO DOC explain how ForecastHandler._updateEndOfPrevCycleBal participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        forecast_df : object
            #TODO DOC one-line description of ForecastHandler._updateEndOfPrevCycleBal.forecast_df.

        account_set : object
            #TODO DOC one-line description of ForecastHandler._updateEndOfPrevCycleBal.account_set.

        current_forecast_row_df : object
            #TODO DOC one-line description of ForecastHandler._updateEndOfPrevCycleBal.current_forecast_row_df.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._updateEndOfPrevCycleBal.log_stack_depth.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._updateEndOfPrevCycleBal.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._updateEndOfPrevCycleBal.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._updateEndOfPrevCycleBal.

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
    #TODO DOC manual review of ForecastHandler._satisfice docstring
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
        #TODO DOC one-line description of ForecastHandler._satisfice.

        #TODO DOC multi-line description of ForecastHandler._satisfice.
        #TODO DOC explain how ForecastHandler._satisfice participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        start_date : date
            #TODO DOC one-line description of ForecastHandler._satisfice.start_date.

        end_date : date
            #TODO DOC one-line description of ForecastHandler._satisfice.end_date.

        list_of_date_strings : object
            #TODO DOC one-line description of ForecastHandler._satisfice.list_of_date_strings.

        confirmed_df : object
            #TODO DOC one-line description of ForecastHandler._satisfice.confirmed_df.

        account_set : object
            #TODO DOC one-line description of ForecastHandler._satisfice.account_set.

        memo_rule_set : object
            #TODO DOC one-line description of ForecastHandler._satisfice.memo_rule_set.

        forecast_df : object
            #TODO DOC one-line description of ForecastHandler._satisfice.forecast_df.

        raise__satisfice_failed_exception : object
            #TODO DOC one-line description of ForecastHandler._satisfice.raise__satisfice_failed_exception.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._satisfice.log_stack_depth.

        progress_bar : object
            #TODO DOC one-line description of ForecastHandler._satisfice.progress_bar.

        include_debug_columns : bool
            #TODO DOC one-line description of ForecastHandler._satisfice.include_debug_columns.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._satisfice.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._satisfice.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._satisfice.

        @interface-report: show
        """
        log_stack_depth += 1

        all_days = list_of_date_strings  # Rename for clarity

        for d in all_days:
            if progress_bar:
                progress_bar.update(1, context=d)
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
    #TODO DOC manual review of ForecastHandler._computeOptimalForecast docstring
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
        progress_phase="Exact",
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
        #TODO DOC one-line description of ForecastHandler._computeOptimalForecast.

        #TODO DOC multi-line description of ForecastHandler._computeOptimalForecast.
        #TODO DOC explain how ForecastHandler._computeOptimalForecast participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        start_date : date
            #TODO DOC one-line description of ForecastHandler._computeOptimalForecast.start_date.

        end_date : date
            #TODO DOC one-line description of ForecastHandler._computeOptimalForecast.end_date.

        confirmed_df : object
            #TODO DOC one-line description of ForecastHandler._computeOptimalForecast.confirmed_df.

        proposed_df : object
            #TODO DOC one-line description of ForecastHandler._computeOptimalForecast.proposed_df.

        deferred_df : object
            #TODO DOC one-line description of ForecastHandler._computeOptimalForecast.deferred_df.

        skipped_df : object
            #TODO DOC one-line description of ForecastHandler._computeOptimalForecast.skipped_df.

        account_set : object
            #TODO DOC one-line description of ForecastHandler._computeOptimalForecast.account_set.

        memo_rule_set : object
            #TODO DOC one-line description of ForecastHandler._computeOptimalForecast.memo_rule_set.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._computeOptimalForecast.log_stack_depth.

        raise__satisfice_failed_exception : object
            #TODO DOC one-line description of ForecastHandler._computeOptimalForecast.raise__satisfice_failed_exception.

        progress_bar : object
            #TODO DOC one-line description of ForecastHandler._computeOptimalForecast.progress_bar.

        include_debug_columns : bool
            #TODO DOC one-line description of ForecastHandler._computeOptimalForecast.include_debug_columns.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._computeOptimalForecast.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._computeOptimalForecast.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._computeOptimalForecast.

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
        mandatory_context = (
            ForecastProgress(
                logger,
                f"{progress_phase} mandatory pass",
                max(1, len(all_days)),
            )
            if not raise__satisfice_failed_exception and progress_bar is None
            else nullcontext(progress_bar)
        )
        with mandatory_context as mandatory_progress:
            _satisfice_df = cls._satisfice(start_date,
                end_date,
                all_days,
                confirmed_df=confirmed_df,
                account_set=account_set,
                memo_rule_set=memo_rule_set,
                forecast_df=forecast_df,
                raise__satisfice_failed_exception=raise__satisfice_failed_exception,
                progress_bar=mandatory_progress,
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
                optimization_started_at = perf_counter()
                if not raise__satisfice_failed_exception:
                    optional_count = int((proposed_df["Priority"] > 1).sum())
                    cls._phase_log(
                        "cyan",
                        "Optimization pass started: "
                        f"optional_transactions={optional_count} days={len(all_days)}. "
                        "Future-safety simulations may hold the percentage while "
                        "the heartbeat continues.",
                    )
                optimization_priorities = max(
                    1,
                    len([
                        priority for priority in full_budget_priorities
                        if priority != 1
                    ]),
                ) if (full_budget_priorities := sorted(set(
                    pd.concat([confirmed_df, proposed_df, deferred_df, skipped_df])[
                        "Priority"
                    ].tolist()
                ))) else 1
                optimization_total = max(1, optimization_priorities * max(1, len(all_days) - 1))
                optimization_context = (
                    ForecastProgress(
                        logger,
                        f"{progress_phase} optimization",
                        optimization_total,
                    )
                    if not raise__satisfice_failed_exception and optional_count > 0
                    else nullcontext(None)
                )
                with optimization_context as optimization_progress:
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
                            progress_bar=optimization_progress,
                            log_stack_depth=log_stack_depth,
                            include_debug_columns=include_debug_columns
                        )
                    )
                if not raise__satisfice_failed_exception:
                    cls._phase_log(
                        "green",
                        "Optimization pass finished: "
                        f"elapsed={perf_counter() - optimization_started_at:.2f}s",
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
    #TODO DOC manual review of ForecastHandler.compute_forecast_difference docstring
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
        #TODO DOC one-line description of ForecastHandler.compute_forecast_difference.

        #TODO DOC multi-line description of ForecastHandler.compute_forecast_difference.
        #TODO DOC explain how ForecastHandler.compute_forecast_difference participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        forecast_df : object
            #TODO DOC one-line description of ForecastHandler.compute_forecast_difference.forecast_df.

        forecast2_df : object
            #TODO DOC one-line description of ForecastHandler.compute_forecast_difference.forecast2_df.

        label : str
            #TODO DOC one-line description of ForecastHandler.compute_forecast_difference.label.

        make_plots : object
            #TODO DOC one-line description of ForecastHandler.compute_forecast_difference.make_plots.

        plot_directory : object
            #TODO DOC one-line description of ForecastHandler.compute_forecast_difference.plot_directory.

        return_type : object
            #TODO DOC one-line description of ForecastHandler.compute_forecast_difference.return_type.

        require_matching_columns : object
            #TODO DOC one-line description of ForecastHandler.compute_forecast_difference.require_matching_columns.

        require_matching_date_range : object
            #TODO DOC one-line description of ForecastHandler.compute_forecast_difference.require_matching_date_range.

        append_expected_values : object
            #TODO DOC one-line description of ForecastHandler.compute_forecast_difference.append_expected_values.

        diffs_only : object
            #TODO DOC one-line description of ForecastHandler.compute_forecast_difference.diffs_only.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler.compute_forecast_difference.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler.compute_forecast_difference.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler.compute_forecast_difference.

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
                #TODO should be a log instead of print
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


    #TODO DOC manual review of ForecastHandler._appendSummaryLines docstring
    @classmethod
    def _appendSummaryLines(cls, initial_A, forecast_df, log_stack_depth=0):

        """
        #TODO DOC one-line description of ForecastHandler._appendSummaryLines.

        #TODO DOC multi-line description of ForecastHandler._appendSummaryLines.
        #TODO DOC explain how ForecastHandler._appendSummaryLines participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        initial_A : object
            #TODO DOC one-line description of ForecastHandler._appendSummaryLines.initial_A.

        forecast_df : object
            #TODO DOC one-line description of ForecastHandler._appendSummaryLines.forecast_df.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler._appendSummaryLines.log_stack_depth.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._appendSummaryLines.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._appendSummaryLines.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._appendSummaryLines.

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
        checking_acct_info = account_info.loc[checking_sel_vec, :]
        investment_acct_info = account_info.loc[investment_sel_vec, :]

        def summary_numeric_series(column_name):
            return pd.to_numeric(forecast_df.loc[:, column_name], errors="coerce").fillna(0.0)

        zero_series = (
            summary_numeric_series("Checking") - summary_numeric_series("Checking")
        )
        NetWorth = zero_series.copy()
        for _, checking_account_row in checking_acct_info.iterrows():
            NetWorth = NetWorth + summary_numeric_series(checking_account_row.Name)
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

        forecast_df["Interest Accrued"] = 0.0
        forecast_df["Investment Returns"] = 0.0
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
                        forecast_df.loc[index, "Interest Accrued"] += abs(
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
                    forecast_df.loc[index, "Interest Accrued"] += abs(
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

                forecast_df.loc[index, "Interest Accrued"] += delta
                # print('')

            previous_row = row

        # just memo
        forecast_df["Net Gain"] = 0.0
        forecast_df["Net Loss"] = forecast_df["Interest Accrued"]
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

                # Policy-driven debt payments move value from checking to a
                # liability account.  The liability-side entry is recorded in
                # Memo Directives, so treating the checking-side entry as an
                # expense would incorrectly report a net loss for a transfer.
                if memo_line_item.startswith(
                    (
                        "POLICY current_statement_balance_payment:",
                        "POLICY surplus_debt_payment:",
                        "POLICY surplus_saving:",
                    )
                ):
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
                    # Approximate forecasts retain scheduled income in Memo
                    # rather than emitting an INCOME memo directive. Exact
                    # forecasts include both, so only use Memo as a fallback.
                    if "INCOME" not in row["Memo Directives"]:
                        forecast_df.loc[index, "Net Gain"] += abs(line_item_value)
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
                if "INVESTMENT RETURN" in memo_line_item:
                    forecast_df.loc[index, "Investment Returns"] += abs(
                        line_item_value
                    )
                # Moving cash from checking to savings changes its location,
                # not the forecast's wealth. Keep the directive for audit and
                # Sankey reporting, but exclude it from both gain and loss.
                if "SAVINGS CONTRIBUTION" in memo_line_item:
                    continue
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

            if "SAVINGS CONTRIBUTION" in md:
                continue

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

        LiquidTotal = zero_series.copy()
        for _, checking_account_row in checking_acct_info.iterrows():
            LiquidTotal = LiquidTotal + summary_numeric_series(checking_account_row.Name)

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

    #TODO DOC manual review of ForecastHandler._report_date_to_datetime docstring
    @staticmethod
    def _report_date_to_datetime(value):
        """
        #TODO DOC one-line description of ForecastHandler._report_date_to_datetime.

        #TODO DOC multi-line description of ForecastHandler._report_date_to_datetime.
        #TODO DOC explain how ForecastHandler._report_date_to_datetime participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        value : object
            #TODO DOC one-line description of ForecastHandler._report_date_to_datetime.value.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._report_date_to_datetime.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._report_date_to_datetime.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._report_date_to_datetime.

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

    #TODO DOC manual review of ForecastHandler._report_amount docstring
    @staticmethod
    def _report_amount(value):
        """
        #TODO DOC one-line description of ForecastHandler._report_amount.

        #TODO DOC multi-line description of ForecastHandler._report_amount.
        #TODO DOC explain how ForecastHandler._report_amount participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        value : object
            #TODO DOC one-line description of ForecastHandler._report_amount.value.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._report_amount.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._report_amount.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._report_amount.

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

    #TODO DOC manual review of ForecastHandler._report_date_label docstring
    def _report_date_label(self, value):
        """
        #TODO DOC one-line description of ForecastHandler._report_date_label.

        #TODO DOC multi-line description of ForecastHandler._report_date_label.
        #TODO DOC explain how ForecastHandler._report_date_label participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        value : object
            #TODO DOC one-line description of ForecastHandler._report_date_label.value.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._report_date_label.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._report_date_label.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._report_date_label.

        @interface-report: show
        """
        return self._report_date_to_datetime(value).strftime("%Y-%m-%d")

    #TODO DOC manual review of ForecastHandler._report_initial_conditions docstring
    def _report_initial_conditions(self, expense_forecast):
        """
        #TODO DOC one-line description of ForecastHandler._report_initial_conditions.

        #TODO DOC multi-line description of ForecastHandler._report_initial_conditions.
        #TODO DOC explain how ForecastHandler._report_initial_conditions participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            #TODO DOC one-line description of ForecastHandler._report_initial_conditions.expense_forecast.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._report_initial_conditions.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._report_initial_conditions.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._report_initial_conditions.

        @interface-report: show
        """
        return getattr(expense_forecast, "initial_conditions", expense_forecast)

    #TODO DOC manual review of ForecastHandler._report_start_date docstring
    def _report_start_date(self, expense_forecast):
        """
        #TODO DOC one-line description of ForecastHandler._report_start_date.

        #TODO DOC multi-line description of ForecastHandler._report_start_date.
        #TODO DOC explain how ForecastHandler._report_start_date participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            #TODO DOC one-line description of ForecastHandler._report_start_date.expense_forecast.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._report_start_date.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._report_start_date.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._report_start_date.

        @interface-report: show
        """
        initial_conditions = self._report_initial_conditions(expense_forecast)
        return getattr(
            expense_forecast,
            "start_date_YYYYMMDD",
            getattr(initial_conditions, "start_date", None),
        )

    #TODO DOC manual review of ForecastHandler._report_end_date docstring
    def _report_end_date(self, expense_forecast):
        """
        #TODO DOC one-line description of ForecastHandler._report_end_date.

        #TODO DOC multi-line description of ForecastHandler._report_end_date.
        #TODO DOC explain how ForecastHandler._report_end_date participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            #TODO DOC one-line description of ForecastHandler._report_end_date.expense_forecast.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._report_end_date.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._report_end_date.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._report_end_date.

        @interface-report: show
        """
        initial_conditions = self._report_initial_conditions(expense_forecast)
        return getattr(
            expense_forecast,
            "end_date_YYYYMMDD",
            getattr(initial_conditions, "end_date", None),
        )

    #TODO DOC manual review of ForecastHandler._report_forecast_name docstring
    def _report_forecast_name(self, expense_forecast):
        """
        #TODO DOC one-line description of ForecastHandler._report_forecast_name.

        #TODO DOC multi-line description of ForecastHandler._report_forecast_name.
        #TODO DOC explain how ForecastHandler._report_forecast_name participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            #TODO DOC one-line description of ForecastHandler._report_forecast_name.expense_forecast.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._report_forecast_name.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._report_forecast_name.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._report_forecast_name.

        @interface-report: show
        """
        initial_conditions = self._report_initial_conditions(expense_forecast)
        return (
            getattr(expense_forecast, "forecast_name", None)
            or getattr(initial_conditions, "forecast_name", None)
            or f"Forecast {expense_forecast.unique_id}"
        )

    #TODO DOC manual review of ForecastHandler._report_account_set docstring
    def _report_account_set(self, expense_forecast):
        """
        #TODO DOC one-line description of ForecastHandler._report_account_set.

        #TODO DOC multi-line description of ForecastHandler._report_account_set.
        #TODO DOC explain how ForecastHandler._report_account_set participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            #TODO DOC one-line description of ForecastHandler._report_account_set.expense_forecast.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._report_account_set.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._report_account_set.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._report_account_set.

        @interface-report: show
        """
        initial_conditions = self._report_initial_conditions(expense_forecast)
        return getattr(
            expense_forecast,
            "initial_account_set",
            getattr(initial_conditions, "initial_account_set", None),
        )

    #TODO DOC manual review of ForecastHandler._report_line_item_set docstring
    def _report_line_item_set(self, expense_forecast):
        """
        #TODO DOC one-line description of ForecastHandler._report_line_item_set.

        #TODO DOC multi-line description of ForecastHandler._report_line_item_set.
        #TODO DOC explain how ForecastHandler._report_line_item_set participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            #TODO DOC one-line description of ForecastHandler._report_line_item_set.expense_forecast.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._report_line_item_set.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._report_line_item_set.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._report_line_item_set.

        @interface-report: show
        """
        initial_conditions = self._report_initial_conditions(expense_forecast)
        return getattr(
            expense_forecast,
            "initial_line_item_set",
            getattr(initial_conditions, "initial_line_item_set", None),
        )

    #TODO DOC manual review of ForecastHandler._report_memo_rule_set docstring
    def _report_memo_rule_set(self, expense_forecast):
        """
        #TODO DOC one-line description of ForecastHandler._report_memo_rule_set.

        #TODO DOC multi-line description of ForecastHandler._report_memo_rule_set.
        #TODO DOC explain how ForecastHandler._report_memo_rule_set participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            #TODO DOC one-line description of ForecastHandler._report_memo_rule_set.expense_forecast.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._report_memo_rule_set.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._report_memo_rule_set.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._report_memo_rule_set.

        @interface-report: show
        """
        initial_conditions = self._report_initial_conditions(expense_forecast)
        return getattr(
            expense_forecast,
            "initial_memo_rule_set",
            getattr(initial_conditions, "initial_memo_rule_set", None),
        )

    #TODO DOC manual review of ForecastHandler._report_milestone_set docstring
    def _report_milestone_set(self, expense_forecast):
        """
        #TODO DOC one-line description of ForecastHandler._report_milestone_set.

        #TODO DOC multi-line description of ForecastHandler._report_milestone_set.
        #TODO DOC explain how ForecastHandler._report_milestone_set participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            #TODO DOC one-line description of ForecastHandler._report_milestone_set.expense_forecast.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._report_milestone_set.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._report_milestone_set.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._report_milestone_set.

        @interface-report: show
        """
        initial_conditions = self._report_initial_conditions(expense_forecast)
        return getattr(
            expense_forecast,
            "milestone_set",
            getattr(initial_conditions, "milestone_set", None),
        )

    #TODO DOC manual review of ForecastHandler._empty_report_df docstring
    @staticmethod
    def _empty_report_df():
        """
        #TODO DOC one-line description of ForecastHandler._empty_report_df.

        #TODO DOC multi-line description of ForecastHandler._empty_report_df.
        #TODO DOC explain how ForecastHandler._empty_report_df participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that ForecastHandler._empty_report_df takes no parameters beyond self/cls.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._empty_report_df.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._empty_report_df.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._empty_report_df.

        @interface-report: show
        """
        return pd.DataFrame()

    #TODO DOC manual review of ForecastHandler._report_milestone_table docstring
    def _report_milestone_table(self, milestone_set, method_name):
        """
        #TODO DOC one-line description of ForecastHandler._report_milestone_table.

        #TODO DOC multi-line description of ForecastHandler._report_milestone_table.
        #TODO DOC explain how ForecastHandler._report_milestone_table participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        milestone_set : object
            #TODO DOC one-line description of ForecastHandler._report_milestone_table.milestone_set.

        method_name : object
            #TODO DOC one-line description of ForecastHandler._report_milestone_table.method_name.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._report_milestone_table.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._report_milestone_table.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._report_milestone_table.

        @interface-report: show
        """
        if milestone_set is None or not hasattr(milestone_set, method_name):
            return self._empty_report_df()
        return getattr(milestone_set, method_name)()

    #TODO DOC manual review of ForecastHandler._report_milestone_results_df docstring
    def _report_milestone_results_df(self, expense_forecast, result_type):
        """
        #TODO DOC one-line description of ForecastHandler._report_milestone_results_df.

        #TODO DOC multi-line description of ForecastHandler._report_milestone_results_df.
        #TODO DOC explain how ForecastHandler._report_milestone_results_df participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            #TODO DOC one-line description of ForecastHandler._report_milestone_results_df.expense_forecast.

        result_type : object
            #TODO DOC one-line description of ForecastHandler._report_milestone_results_df.result_type.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._report_milestone_results_df.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._report_milestone_results_df.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._report_milestone_results_df.

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

    #TODO DOC manual review of ForecastHandler._report_confirmed_df docstring
    def _report_confirmed_df(self, expense_forecast):
        """
        #TODO DOC one-line description of ForecastHandler._report_confirmed_df.

        #TODO DOC multi-line description of ForecastHandler._report_confirmed_df.
        #TODO DOC explain how ForecastHandler._report_confirmed_df participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            #TODO DOC one-line description of ForecastHandler._report_confirmed_df.expense_forecast.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._report_confirmed_df.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._report_confirmed_df.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._report_confirmed_df.

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

    #TODO DOC manual review of ForecastHandler._report_dates_for_plot docstring
    def _report_dates_for_plot(self, expense_forecast):
        """
        #TODO DOC one-line description of ForecastHandler._report_dates_for_plot.

        #TODO DOC multi-line description of ForecastHandler._report_dates_for_plot.
        #TODO DOC explain how ForecastHandler._report_dates_for_plot participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            #TODO DOC one-line description of ForecastHandler._report_dates_for_plot.expense_forecast.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._report_dates_for_plot.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._report_dates_for_plot.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._report_dates_for_plot.

        @interface-report: show
        """
        return [
            self._report_date_to_datetime(d)
            for d in expense_forecast.forecast_df["Date"]
        ]

    #TODO DOC manual review of ForecastHandler._decorate_report_plot docstring
    def _decorate_report_plot(self, expense_forecast):
        """
        #TODO DOC one-line description of ForecastHandler._decorate_report_plot.

        #TODO DOC multi-line description of ForecastHandler._decorate_report_plot.
        #TODO DOC explain how ForecastHandler._decorate_report_plot participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            #TODO DOC one-line description of ForecastHandler._decorate_report_plot.expense_forecast.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler._decorate_report_plot.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler._decorate_report_plot.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler._decorate_report_plot.

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

    #TODO DOC manual review of ForecastHandler.plotMilestoneDates docstring
    def plotMilestoneDates(
        self, expense_forecast, output_path, plot_colors=["red", "blue", "purple"]
    ):
        """
        #TODO DOC one-line description of ForecastHandler.plotMilestoneDates.

        #TODO DOC multi-line description of ForecastHandler.plotMilestoneDates.
        #TODO DOC explain how ForecastHandler.plotMilestoneDates participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            #TODO DOC one-line description of ForecastHandler.plotMilestoneDates.expense_forecast.

        output_path : object
            #TODO DOC one-line description of ForecastHandler.plotMilestoneDates.output_path.

        plot_colors : object
            #TODO DOC one-line description of ForecastHandler.plotMilestoneDates.plot_colors.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler.plotMilestoneDates.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler.plotMilestoneDates.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler.plotMilestoneDates.

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

    #TODO DOC manual review of ForecastHandler.plotAccountTypeTotals docstring
    def plotAccountTypeTotals(
        self,
        expense_forecast,
        output_path,
        line_color_cycle_list=["blue", "orange", "green", "purple"],
        linestyle="solid",
    ):
        """
        #TODO DOC one-line description of ForecastHandler.plotAccountTypeTotals.

        #TODO DOC multi-line description of ForecastHandler.plotAccountTypeTotals.
        #TODO DOC explain how ForecastHandler.plotAccountTypeTotals participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            #TODO DOC one-line description of ForecastHandler.plotAccountTypeTotals.expense_forecast.

        output_path : object
            #TODO DOC one-line description of ForecastHandler.plotAccountTypeTotals.output_path.

        line_color_cycle_list : object
            #TODO DOC one-line description of ForecastHandler.plotAccountTypeTotals.line_color_cycle_list.

        linestyle : object
            #TODO DOC one-line description of ForecastHandler.plotAccountTypeTotals.linestyle.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler.plotAccountTypeTotals.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler.plotAccountTypeTotals.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler.plotAccountTypeTotals.

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

    #TODO DOC manual review of ForecastHandler.plotNetGainLoss docstring
    def plotNetGainLoss(
        self,
        expense_forecast,
        output_path,
        line_color_cycle_list=["green", "red"],
        linestyle="solid",
    ):
        """
        #TODO DOC one-line description of ForecastHandler.plotNetGainLoss.

        #TODO DOC multi-line description of ForecastHandler.plotNetGainLoss.
        #TODO DOC explain how ForecastHandler.plotNetGainLoss participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            #TODO DOC one-line description of ForecastHandler.plotNetGainLoss.expense_forecast.

        output_path : object
            #TODO DOC one-line description of ForecastHandler.plotNetGainLoss.output_path.

        line_color_cycle_list : object
            #TODO DOC one-line description of ForecastHandler.plotNetGainLoss.line_color_cycle_list.

        linestyle : object
            #TODO DOC one-line description of ForecastHandler.plotNetGainLoss.linestyle.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler.plotNetGainLoss.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler.plotNetGainLoss.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler.plotNetGainLoss.

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

    #TODO DOC manual review of ForecastHandler.plotNetWorth docstring
    def plotNetWorth(
        self,
        expense_forecast,
        output_path,
        line_color_cycle_list=["blue"],
        linestyle="solid",
    ):
        """
        #TODO DOC one-line description of ForecastHandler.plotNetWorth.

        #TODO DOC multi-line description of ForecastHandler.plotNetWorth.
        #TODO DOC explain how ForecastHandler.plotNetWorth participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            #TODO DOC one-line description of ForecastHandler.plotNetWorth.expense_forecast.

        output_path : object
            #TODO DOC one-line description of ForecastHandler.plotNetWorth.output_path.

        line_color_cycle_list : object
            #TODO DOC one-line description of ForecastHandler.plotNetWorth.line_color_cycle_list.

        linestyle : object
            #TODO DOC one-line description of ForecastHandler.plotNetWorth.linestyle.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler.plotNetWorth.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler.plotNetWorth.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler.plotNetWorth.

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

    #TODO DOC manual review of ForecastHandler.plotAll docstring
    def plotAll(
        self,
        expense_forecast,
        output_path,
    ):
        """
        #TODO DOC one-line description of ForecastHandler.plotAll.

        #TODO DOC multi-line description of ForecastHandler.plotAll.
        #TODO DOC explain how ForecastHandler.plotAll participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            #TODO DOC one-line description of ForecastHandler.plotAll.expense_forecast.

        output_path : object
            #TODO DOC one-line description of ForecastHandler.plotAll.output_path.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler.plotAll.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler.plotAll.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler.plotAll.

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
                "Interest Accrued",
                "Investment Returns",
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

    #TODO DOC manual review of ForecastHandler.plotInterestAccrued docstring
    def plotInterestAccrued(self, expense_forecast, output_path, linestyle="solid"):
        """
        #TODO DOC one-line description of ForecastHandler.plotInterestAccrued.

        #TODO DOC multi-line description of ForecastHandler.plotInterestAccrued.
        #TODO DOC explain how ForecastHandler.plotInterestAccrued participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            #TODO DOC one-line description of ForecastHandler.plotInterestAccrued.expense_forecast.

        output_path : object
            #TODO DOC one-line description of ForecastHandler.plotInterestAccrued.output_path.

        linestyle : object
            #TODO DOC one-line description of ForecastHandler.plotInterestAccrued.linestyle.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler.plotInterestAccrued.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler.plotInterestAccrued.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler.plotInterestAccrued.

        @interface-report: show
        """
        assert hasattr(expense_forecast, "forecast_df")

        figure(figsize=(10, 6), dpi=80)
        plt.gca().set_prop_cycle(plt.cycler(color=["blue"]))
        x_values = self._report_dates_for_plot(expense_forecast)
        plt.plot(
            x_values,
            expense_forecast.forecast_df["Interest Accrued"],
            label="Interest Accrued " + str(expense_forecast.unique_id),
            linestyle=linestyle,
        )

        self._decorate_report_plot(expense_forecast)
        plt.savefig(output_path, bbox_inches="tight")
        matplotlib.pyplot.close()

    #TODO DOC manual review of ForecastHandler.plotSankeyDiagram docstring
    def plotSankeyDiagram(self, expense_forecast, output_path):
        """
        #TODO DOC one-line description of ForecastHandler.plotSankeyDiagram.

        #TODO DOC multi-line description of ForecastHandler.plotSankeyDiagram.
        #TODO DOC explain how ForecastHandler.plotSankeyDiagram participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        expense_forecast : object
            #TODO DOC one-line description of ForecastHandler.plotSankeyDiagram.expense_forecast.

        output_path : object
            #TODO DOC one-line description of ForecastHandler.plotSankeyDiagram.output_path.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler.plotSankeyDiagram.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler.plotSankeyDiagram.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler.plotSankeyDiagram.

        @interface-report: show
        """
        if go is None:
            raise ImportError("plotly is required to generate the Sankey diagram")

        line_item_set = self._report_line_item_set(expense_forecast)
        memo_rule_set = self._report_memo_rule_set(expense_forecast)
        if line_item_set is None or memo_rule_set is None:
            raise ValueError("BudgetSet and MemoRuleSet are required for Sankey report")

        income_memos = []
        expense_memos = []
        for _, row in line_item_set.getLineItems().iterrows():
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

    @staticmethod
    def get_delta_explanation_sentence(column_name: str, delta: float, length_of_forecast_in_days: int) -> str:
        avg = delta / length_of_forecast_in_days
        if delta > 0:
            return f"{column_name} rose by ${delta:,.2f} over {length_of_forecast_in_days} days, averaging ${avg:,.2f} per day."
        elif delta == 0:
            return f"{column_name} did not change."
        else:
            return f"{column_name} fell by ${delta:,.2f} over {length_of_forecast_in_days} days, averaging ${avg:,.2f} per day."

    @staticmethod
    def get_last_row_first_row_delta(df: pd.DataFrame, column_name: str) -> float:
        # float does not accept NumPy scalar types directly.
        return float(str(
            df[column_name].iat[-1] - df[column_name].iat[0]
        ))

    @staticmethod
    def get_time_elapsed_string(start_ts, end_ts):
        mins = int((end_ts - start_ts).seconds / 60)
        secs = (end_ts - start_ts).seconds % 60
        if mins + secs == 0:
            mic = (end_ts - start_ts).microseconds
            return f"{mic:,} microseconds"
        
        # TODO handle plural of minute(s) and second(s) in get_time_elapsed_string i just don't want to do it rn 
        return f"{mins} minute and {secs} seconds"

    @classmethod
    def generateComparisonReport(
        cls,
        E_1: ExpenseForecastResult,
        E_2: ExpenseForecastResult,
        report_name: str = "Comparison Report",
        output_path=None,
        write_file: bool = True,
    ) -> str:
        """Generate a self-contained comparison report for two forecasts."""
        started_at = perf_counter()

        def normalized_dates(result):
            if "Date" not in result.forecast_df.columns:
                raise ValueError(
                    "Comparison reports require a Date forecast column"
                )
            return [
                cls._normalize_date_value(value)
                for value in result.forecast_df["Date"]
            ]

        dates_1 = normalized_dates(E_1)
        dates_2 = normalized_dates(E_2)
        if dates_1 != dates_2:
            raise ValueError(
                "Comparison reports require matching forecast date ranges "
                "and row dates"
            )

        def account_schema(result):
            account_set = getattr(
                result, "resolved_account_set",
                result.initial_conditions.initial_account_set,
            )
            return [
                (account.name, account.account_type)
                for account in account_set.accounts
            ]

        schema_1 = account_schema(E_1)
        schema_2 = account_schema(E_2)
        for result, schema in ((E_1, schema_1), (E_2, schema_2)):
            missing_columns = [
                name for name, _ in schema
                if name not in result.forecast_df.columns
            ]
            if missing_columns:
                raise ValueError(
                    "Forecast output is missing account column(s): "
                    + ", ".join(repr(name) for name in missing_columns)
                )
        shared_account_names = set(dict(schema_1)) & set(dict(schema_2))
        type_conflicts = {
            name: (dict(schema_1)[name], dict(schema_2)[name])
            for name in shared_account_names
            if dict(schema_1)[name] != dict(schema_2)[name]
        }
        if type_conflicts:
            raise ValueError(
                "Comparison reports require matching types for shared account "
                f"names; conflicts={type_conflicts!r}"
            )
        comparison_schema = list(schema_1)
        observed_accounts = {name for name, _ in comparison_schema}
        comparison_schema.extend(
            (name, account_type)
            for name, account_type in schema_2
            if name not in observed_accounts
        )

        # Validate report accounting only after compatibility checks so an
        # incompatible result produces the comparison-specific error rather
        # than failing while its summaries are being reparsed.
        cls._assert_report_accounting_invariants(E_1)
        cls._assert_report_accounting_invariants(E_2)

        def identity(result):
            initial = result.initial_conditions
            return {
                "name": initial.forecast_name or "Unnamed Forecast",
                "id": result.unique_id,
                "date_range": (
                    f"{initial.start_date:%Y-%m-%d} to "
                    f"{initial.end_date:%Y-%m-%d}"
                ),
            }

        identity_1 = identity(E_1)
        identity_2 = identity(E_2)
        final_1 = E_1.forecast_df.iloc[-1]
        final_2 = E_2.forecast_df.iloc[-1]
        account_deltas = []
        for account_name, account_type in comparison_schema:
            baseline = (
                float(final_1[account_name])
                if account_name in E_1.forecast_df.columns else 0.0
            )
            comparison = (
                float(final_2[account_name])
                if account_name in E_2.forecast_df.columns else 0.0
            )
            account_deltas.append({
                "account": account_name,
                "account_type": account_type,
                "baseline": baseline,
                "comparison": comparison,
                "delta": comparison - baseline,
            })

        def flatten_milestones(result):
            flattened = {}
            for group in result.milestone_results or []:
                if isinstance(group, dict):
                    flattened.update(group)
            return flattened

        def milestone_date(value):
            if value is None or str(value).strip().lower() in {
                "", "none", "nat"
            }:
                return None
            try:
                return pd.Timestamp(value).date()
            except (TypeError, ValueError):
                return None

        milestones_1 = flatten_milestones(E_1)
        milestones_2 = flatten_milestones(E_2)
        milestone_deltas = []
        milestone_statuses = []
        for milestone_name in sorted(set(milestones_1) | set(milestones_2)):
            achieved_1 = milestone_date(milestones_1.get(milestone_name))
            achieved_2 = milestone_date(milestones_2.get(milestone_name))
            if achieved_1 is not None and achieved_2 is not None:
                milestone_deltas.append({
                    "milestone": milestone_name,
                    "baseline_date": achieved_1.isoformat(),
                    "comparison_date": achieved_2.isoformat(),
                    "delta_days": (achieved_2 - achieved_1).days,
                    "achievement_status": "both",
                })
            elif achieved_1 is not None or achieved_2 is not None:
                milestone_deltas.append({
                    "milestone": milestone_name,
                    "baseline_date": (
                        achieved_1.isoformat() if achieved_1 else "Not achieved"
                    ),
                    "comparison_date": (
                        achieved_2.isoformat() if achieved_2 else "Not achieved"
                    ),
                    "delta_days": None,
                    "achievement_status": (
                        "comparison_only" if achieved_2 else "baseline_only"
                    ),
                })
            else:
                milestone_statuses.append({
                    "milestone": milestone_name,
                    "baseline": (
                        achieved_1.isoformat() if achieved_1 else "Not achieved"
                    ),
                    "comparison": (
                        achieved_2.isoformat() if achieved_2 else "Not achieved"
                    ),
                })

        def scenario_metadata(result):
            line_items = (
                result.resolved_line_item_set
                or result.initial_conditions.initial_line_item_set
            )
            timelines = getattr(line_items, "scenario_timelines", {}) or {}
            selections = getattr(line_items, "scenario_selections", {}) or {}
            rows = []
            for dimension_name, timeline in timelines.items():
                for entry in timeline:
                    rows.append({
                        "dimension": dimension_name,
                        "choice": entry.get("choice", ""),
                        "start": str(entry.get("effective_date", "")),
                        "end": str(entry.get("end_date") or "Forecast end"),
                        "transition": entry.get("transition_name"),
                        "milestone": entry.get("trigger_milestone"),
                    })
            dimensions_with_timelines = {
                row["dimension"] for row in rows
            }
            for dimension_name, choice in selections.items():
                if dimension_name not in dimensions_with_timelines:
                    rows.append({
                        "dimension": dimension_name,
                        "choice": choice,
                        "start": identity(result)["date_range"].split(" to ")[0],
                        "end": identity(result)["date_range"].split(" to ")[1],
                        "transition": None,
                        "milestone": None,
                    })
            return rows

        def policy_metadata(result):
            """Pair configured policies with their first activation/execution."""
            rows = []
            resolved_policy_set = getattr(
                result,
                "resolved_policy_set",
                result.initial_conditions.policy_set,
            )
            policies = list(
                getattr(resolved_policy_set, "policies", []) or []
            ) or list(
                getattr(result.initial_conditions.policy_set, "policies", [])
                or []
            )
            for policy in policies:
                policy_result = result.policy_results.get(
                    policy.policy_key, {}
                )
                activation_date = policy_result.get("activation_date")
                if activation_date in (None, "None"):
                    history_dates = [
                        entry.get("effective_date")
                        for entry in policy_result.get(
                            "configuration_history", []
                        )
                        if entry.get("effective_date") is not None
                    ]
                    if history_dates:
                        activation_date = min(
                            cls._normalize_date_value(value)
                            for value in history_dates
                        )

                # Allocation policies do not all expose an explicit activation
                # field yet. Their first confirmed synthetic transaction is
                # the observable date on which they became active.
                if activation_date in (None, "None"):
                    confirmed = result.confirmed_df
                    if (
                        confirmed is not None
                        and not confirmed.empty
                        and {"Date", "Memo"}.issubset(confirmed.columns)
                    ):
                        matching = confirmed.loc[
                            confirmed["Memo"].astype(str).str.startswith(
                                f"POLICY {policy.policy_key}"
                            ),
                            "Date",
                        ]
                        if not matching.empty:
                            activation_date = min(
                                cls._normalize_date_value(value)
                                for value in matching
                            )

                policy_name = str(policy.policy_name).replace("_", " ").title()
                if isinstance(policy, MinimumCheckingBalancePolicy):
                    target = float(str(policy.target))
                    rendered_target = f"{target:.2f}".rstrip("0").rstrip(".")
                    policy_name += f" ${rendered_target}"
                elif isinstance(policy, SurplusDebtPaymentPolicy):
                    policy_name = (
                        "Surplus CC Payment"
                        if policy.debt_type == "credit"
                        else "Surplus Loan Payment"
                    )
                rows.append({
                    "key": policy.policy_key,
                    "name": policy_name,
                    "priority": policy.priority,
                    "status": str(
                        policy_result.get("status", "not evaluated")
                    ).replace("_", " ").title(),
                    "activation_date": (
                        cls._normalize_date_value(activation_date).isoformat()
                        if activation_date not in (None, "None")
                        else None
                    ),
                })
            return rows

        metadata_1 = scenario_metadata(E_1)
        metadata_2 = scenario_metadata(E_2)
        def exclusive_choice_ranges(rows, other_rows, result):
            """Remove only dates where the same choice is active on both sides."""
            forecast_end = result.initial_conditions.end_date
            exclusive = []
            for row in rows:
                start = cls._normalize_date_value(row["start"])
                end = (
                    forecast_end
                    if row["end"] == "Forecast end"
                    else cls._normalize_date_value(row["end"])
                )
                remaining = [(start, end)]
                for other in other_rows:
                    if (
                        other["dimension"] != row["dimension"]
                        or other["choice"] != row["choice"]
                    ):
                        continue
                    other_start = cls._normalize_date_value(other["start"])
                    other_end = (
                        forecast_end
                        if other["end"] == "Forecast end"
                        else cls._normalize_date_value(other["end"])
                    )
                    next_remaining = []
                    for range_start, range_end in remaining:
                        overlap_start = max(range_start, other_start)
                        overlap_end = min(range_end, other_end)
                        if overlap_start > overlap_end:
                            next_remaining.append((range_start, range_end))
                            continue
                        if range_start < overlap_start:
                            next_remaining.append((
                                range_start,
                                overlap_start - datetime.timedelta(days=1),
                            ))
                        if overlap_end < range_end:
                            next_remaining.append((
                                overlap_end + datetime.timedelta(days=1),
                                range_end,
                            ))
                    remaining = next_remaining

                for range_start, range_end in remaining:
                    rendered = dict(row)
                    rendered["start"] = range_start.isoformat()
                    rendered["end"] = (
                        "Forecast end"
                        if range_end == forecast_end
                        else range_end.isoformat()
                    )
                    exclusive.append(rendered)
            return exclusive

        exclusive_metadata_1 = exclusive_choice_ranges(
            metadata_1, metadata_2, E_1
        )
        exclusive_metadata_2 = exclusive_choice_ranges(
            metadata_2, metadata_1, E_2
        )

        baseline_policy_dates = {
            policy["key"]: policy["activation_date"]
            for policy in policy_metadata(E_1)
        }

        def scenario_card(result, side_label, rows, compare_activation=False):
            if not rows:
                body = '<p class="empty-state">No scenario choices recorded.</p>'
            else:
                rendered_rows = []
                for row in rows:
                    transition = ""
                    if row["transition"]:
                        transition = (
                            '<span class="timeline-trigger">'
                            f"via {escape(str(row['transition']))}"
                            + (
                                f" · {escape(str(row['milestone']))}"
                                if row["milestone"] else ""
                            )
                            + "</span>"
                        )
                    rendered_rows.append(
                        '<li><span class="timeline-dimension">'
                        f"{escape(str(row['dimension']))}</span>"
                        '<strong>' + escape(str(row["choice"])) + '</strong>'
                        '<span class="timeline-range">'
                        f"{escape(str(row['start']))} – {escape(str(row['end']))}"
                        "</span>" + transition + "</li>"
                    )
                body = '<ul class="timeline-list">' + "".join(rendered_rows) + "</ul>"
            policies = policy_metadata(result)
            if not policies:
                policy_body = (
                    '<p class="empty-state">No policies configured.</p>'
                )
            else:
                policy_rows = []
                for policy in policies:
                    activation_text = (
                        f"Active from {policy['activation_date']}"
                        if policy["activation_date"]
                        else "No activation recorded"
                    )
                    activation_class = ""
                    baseline_date = baseline_policy_dates.get(policy["key"])
                    if (
                        compare_activation
                        and baseline_date
                        and policy["activation_date"]
                    ):
                        alternate_date = cls._normalize_date_value(
                            policy["activation_date"]
                        )
                        normalized_baseline = cls._normalize_date_value(
                            baseline_date
                        )
                        if alternate_date < normalized_baseline:
                            activation_class = " activation-earlier"
                        elif alternate_date > normalized_baseline:
                            activation_class = " activation-later"
                    policy_rows.append(
                        '<li><span class="timeline-dimension">'
                        f"Priority {escape(str(policy['priority']))}</span>"
                        f"<strong>{escape(policy['name'])}</strong>"
                        '<span class="timeline-range">'
                        f'<span class="policy-activation{activation_class}">'
                        f"{escape(activation_text)}</span> · "
                        f"{escape(policy['status'])}</span></li>"
                    )
                policy_body = (
                    '<ul class="timeline-list">'
                    + "".join(policy_rows)
                    + "</ul>"
                )
            return (
                '<aside class="scenario-card card"><p class="eyebrow">'
                f"{escape(side_label)}</p>{body}"
                '<div class="card-divider"></div>'
                '<p class="eyebrow policy-heading">Policies</p>'
                f"{policy_body}</aside>"
            )

        unmatched_rows = "".join(
            "<tr>"
            f"<td>{escape(str(row['milestone']))}</td>"
            f"<td>{escape(row['baseline'])}</td>"
            f"<td>{escape(row['comparison'])}</td>"
            "</tr>"
            for row in milestone_statuses
        )
        unmatched_section = (
            '<div class="status-table-wrap"><h3>Unachieved Milestones</h3>'
            '<table><thead><tr><th>Milestone</th><th>Baseline</th>'
            '<th>Comparison</th></tr></thead><tbody>'
            f"{unmatched_rows}</tbody></table></div>"
            if milestone_statuses else ""
        )

        comparison_data = json.dumps(
            {
                "accounts": account_deltas,
                "milestones": milestone_deltas,
                "baseline_name": identity_1["name"],
                "comparison_name": identity_2["name"],
            },
            ensure_ascii=False,
        ).replace("<", "\\u003c")
        waterfall_tabs = "".join(
            '<button type="button" class="waterfall-tab'
            + (" is-active" if index == 0 else "")
            + '" data-account="'
            + escape(row["account"], quote=True)
            + '">'
            + escape(row["account"])
            + "</button>"
            for index, row in enumerate(account_deltas)
        )
        initial_waterfall_account = (
            account_deltas[0]["account"] if account_deltas else "Account"
        )
        embedded_reports = json.dumps(
            {
                "baseline": cls.generateHTMLReport(
                    E_1,
                    write_file=False,
                    comparison_return=True,
                ),
                "alternate": cls.generateHTMLReport(
                    E_2,
                    write_file=False,
                    comparison_return=True,
                ),
            },
            ensure_ascii=False,
        ).replace("<", "\\u003c")

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(report_name)}</title>
<style>
:root {{ --bg:#f7f7f5; --surface:#fff; --text:#1d1d1f; --muted:#77777d;
--border:#dedee2; --positive:#2f7d4a; --negative:#b65a5a; --accent:#315c72; }}
* {{ box-sizing:border-box; }} body {{ margin:0; background:var(--bg); color:var(--text);
font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif; }}
.page {{ width:min(1500px,100%); margin:auto; padding:42px clamp(24px,4vw,72px) 72px; }}
.header {{ display:grid; grid-template-columns:1fr 1.15fr 1fr; align-items:start; gap:24px; }}
.identity.right {{ text-align:right; }} .identity h1 {{ margin:0; font-size:1.65rem; }}
.identity p,.subtitle {{ color:var(--muted); margin:7px 0 0; }} .uid {{ font-family:monospace; }}
.identity-link {{ appearance:none; margin:0; padding:0; border:0; background:none; color:inherit;
font:inherit; text-align:inherit; cursor:pointer; }} .identity-link:hover {{ color:var(--accent); text-decoration:underline; }}
.report-title {{ text-align:center; }} .report-title h2 {{ margin:0; font-size:2rem; }}
.comparison-grid {{ display:grid; grid-template-columns:minmax(210px,1fr) minmax(0,3fr) minmax(210px,1fr);
gap:24px; align-items:stretch; margin-top:36px; }}
.card,.chart-card {{ background:var(--surface); border:1px solid var(--border); border-radius:12px;
padding:20px; box-shadow:0 1px 2px rgba(0,0,0,.025); }}
.eyebrow {{ margin:0 0 14px; color:var(--muted); font-size:.75rem; text-transform:uppercase;
letter-spacing:.08em; font-weight:700; }} .timeline-list {{ list-style:none; margin:0; padding:0; }}
.timeline-list li {{ display:grid; gap:4px; padding:12px 0; border-top:1px solid #ececef; }}
.timeline-list li:first-child {{ border-top:0; padding-top:0; }} .timeline-dimension,.timeline-range,
.timeline-trigger,.empty-state {{ color:var(--muted); font-size:.8rem; }}
.policy-activation.activation-earlier {{ color:var(--positive); font-weight:700; }}
.policy-activation.activation-later {{ color:var(--negative); font-weight:700; }}
.scenario-card {{ display:flex; flex-direction:column; }}
.scenario-card .card-divider {{ margin-top:auto; }}
.card-divider {{ height:1px; margin:18px 0; background:#dedee2; }} .policy-heading {{ margin-bottom:14px; }}
.chart-card h2,.section h2 {{ margin:0; font-size:1.2rem; }} .chart-note {{ color:var(--muted); font-size:.82rem; }}
svg {{ display:block; width:100%; height:auto; overflow:visible; }}
.section {{ margin-top:32px; }} .section > .chart-card {{ padding:24px; }}
.status-table-wrap {{ margin-top:22px; }} table {{ width:100%; border-collapse:collapse; }}
th,td {{ padding:10px 12px; text-align:left; border-bottom:1px solid #ececef; }} th {{ color:var(--muted); }}
.placeholder {{ min-height:190px; display:grid; place-items:center; border:1px dashed #bfc0c5;
border-radius:9px; color:var(--muted); background:linear-gradient(135deg,#fafafa,#f1f1ef); }}
.waterfall-nav {{ display:grid; grid-auto-flow:column; grid-auto-columns:minmax(120px,1fr);
overflow-x:auto; margin:18px 0 14px; border:1px solid var(--border); border-radius:9px; }}
.waterfall-tab {{ min-height:42px; border:0; border-left:1px solid var(--border); background:#fafafa;
color:var(--muted); cursor:pointer; font:inherit; }} .waterfall-tab:first-child {{ border-left:0; }}
.waterfall-tab.is-active {{ background:var(--accent); color:#fff; }}
.embedded-report-view {{ position:fixed; inset:0; z-index:20; background:var(--bg); }}
.embedded-report-view[hidden] {{ display:none; }} .embedded-report-frame {{ width:100%; height:100vh; border:0; display:block; }}
.axis {{ stroke:#96969b; stroke-width:1; }} .grid {{ stroke:#ececef; stroke-width:1; }}
.label {{ fill:var(--text); font-size:12px; }} .value {{ fill:var(--muted); font-size:11px; }}
@media(max-width:900px) {{ .header {{ grid-template-columns:1fr; text-align:left; }}
.identity.right,.report-title {{ text-align:left; }} .comparison-grid {{ grid-template-columns:1fr; }}
.chart-card {{ grid-row:1; }} }}
</style>
</head>
<body><main class="page" id="comparison-landing">
<header class="header">
<section class="identity"><h1><button type="button" class="identity-link" data-report-view="baseline">{escape(identity_1['name'])}</button></h1><p><button type="button" class="identity-link uid" data-report-view="baseline">{escape(identity_1['id'])}</button></p></section>
<section class="report-title"><h2>{escape(report_name)}</h2><p class="subtitle">Comparison minus baseline</p><p class="subtitle">{escape(identity_1['date_range'])}</p></section>
<section class="identity right"><h1><button type="button" class="identity-link" data-report-view="alternate">{escape(identity_2['name'])}</button></h1><p><button type="button" class="identity-link uid" data-report-view="alternate">{escape(identity_2['id'])}</button></p></section>
</header>
<section class="comparison-grid">
{scenario_card(E_1, 'Baseline Only Choices', exclusive_metadata_1)}
<div class="chart-card"><h2>Final Account Balance Differences</h2><p class="chart-note">Positive bars mean the comparison balance is higher.</p><svg id="account-chart" viewBox="0 0 900 430" role="img" aria-label="Final account balance deltas"></svg></div>
{scenario_card(E_2, 'Alternate Choices', exclusive_metadata_2, compare_activation=True)}
</section>
<section class="section"><div class="chart-card"><h2>Milestone Timing Differences</h2><p class="chart-note">Days relative to baseline: left is earlier, right is later.</p><svg id="milestone-chart" viewBox="0 0 900 280" role="img" aria-label="Milestone timing deltas"></svg>{unmatched_section}</div></section>
<section class="section"><div class="chart-card"><h2>Waterfall Comparison</h2><nav class="waterfall-nav" aria-label="Waterfall account">{waterfall_tabs}</nav><div class="placeholder" id="waterfall-placeholder"><span><strong id="waterfall-account-name">{escape(initial_waterfall_account)}</strong><br>Waterfall analysis will be added in a future report revision.</span></div></div></section>
</main>
<section class="embedded-report-view" id="embedded-baseline" hidden><iframe class="embedded-report-frame" title="{escape(identity_1['name'], quote=True)} report"></iframe></section>
<section class="embedded-report-view" id="embedded-alternate" hidden><iframe class="embedded-report-frame" title="{escape(identity_2['name'], quote=True)} report"></iframe></section>
<script id="comparison-data" type="application/json">{comparison_data}</script>
<script id="embedded-reports-data" type="application/json">{embedded_reports}</script>
<script>
(() => {{
const data=JSON.parse(document.getElementById('comparison-data').textContent);
const embeddedReports=JSON.parse(document.getElementById('embedded-reports-data').textContent);
const NS='http://www.w3.org/2000/svg';
const add=(svg,tag,attrs,text) => {{ const el=document.createElementNS(NS,tag);
Object.entries(attrs||{{}}).forEach(([k,v])=>el.setAttribute(k,v)); if(text!==undefined)el.textContent=text;
svg.appendChild(el); return el; }};
const money=v=>new Intl.NumberFormat('en-US',{{style:'currency',currency:'USD'}}).format(v);
const accountSvg=document.getElementById('account-chart'), accounts=data.accounts;
const zeroY=210, max=Math.max(1,...accounts.map(d=>Math.abs(d.delta))), scale=155/max;
add(accountSvg,'line',{{x1:55,y1:zeroY,x2:875,y2:zeroY,class:'axis'}});
if(!accounts.length) add(accountSvg,'text',{{x:450,y:215,'text-anchor':'middle',class:'label'}},'No accounts');
accounts.forEach((d,i)=>{{ const slot=820/accounts.length, width=Math.min(76,slot*.62), x=55+i*slot+(slot-width)/2;
const height=Math.abs(d.delta)*scale, y=d.delta>=0?zeroY-height:zeroY;
const bar=add(accountSvg,'rect',{{x,y,width,height:Math.max(2,height),rx:4,fill:d.delta>=0?'#2f7d4a':'#b65a5a'}});
add(bar,'title',{{}},`${{d.account}}\n${{data.baseline_name}}: ${{money(d.baseline)}}\n${{data.comparison_name}}: ${{money(d.comparison)}}\nDelta: ${{money(d.delta)}}`);
add(accountSvg,'text',{{x:x+width/2,y:390,'text-anchor':'middle',class:'label'}},d.account);
add(accountSvg,'text',{{x:x+width/2,y:d.delta>=0?y-8:y+height+16,'text-anchor':'middle',class:'value'}},money(d.delta)); }});
const milestoneSvg=document.getElementById('milestone-chart'), milestones=data.milestones;
const height=Math.max(110,80+milestones.length*46); milestoneSvg.setAttribute('viewBox',`0 0 900 ${{height}}`);
const numericMilestones=milestones.filter(d=>Number.isFinite(d.delta_days));
const zeroX=560, dayMax=Math.max(1,...numericMilestones.map(d=>Math.abs(d.delta_days))), dayScale=280/dayMax;
add(milestoneSvg,'line',{{x1:zeroX,y1:35,x2:zeroX,y2:height-25,class:'axis'}});
if(!milestones.length) add(milestoneSvg,'text',{{x:450,y:height/2+5,'text-anchor':'middle',class:'label'}},'No jointly achieved milestones');
milestones.forEach((d,i)=>{{ const y=58+i*46, oneSided=d.achievement_status!=='both';
const direction=oneSided?(d.achievement_status==='comparison_only'?-1:1):(d.delta_days<0?-1:1);
const width=oneSided?42:Math.abs(d.delta_days)*dayScale, x=direction>=0?zeroX:zeroX-width;
add(milestoneSvg,'text',{{x:8,y:y+5,class:'label'}},d.milestone);
const bar=add(milestoneSvg,'rect',{{x,y:y-13,width:Math.max(2,width),height:24,rx:4,fill:direction<=0?'#2f7d4a':'#b65a5a'}});
const resultText=oneSided?(d.achievement_status==='comparison_only'?'Comparison only':'Baseline only'):`${{d.delta_days}} days`;
add(bar,'title',{{}},`${{d.milestone}}\n${{data.baseline_name}}: ${{d.baseline_date}}\n${{data.comparison_name}}: ${{d.comparison_date}}\n${{resultText}}`);
add(milestoneSvg,'text',{{x:direction>=0?x+width+8:x-8,y:y+5,'text-anchor':direction>=0?'start':'end',class:'value'}},oneSided?resultText:`${{d.delta_days}}d`); }});
document.querySelectorAll('.waterfall-tab').forEach(button => {{
button.addEventListener('click', () => {{
document.querySelectorAll('.waterfall-tab').forEach(candidate => candidate.classList.toggle('is-active',candidate===button));
document.getElementById('waterfall-account-name').textContent=button.dataset.account;
}}); }});
const showComparison=() => {{
document.getElementById('comparison-landing').hidden=false;
document.querySelectorAll('.embedded-report-view').forEach(view=>view.hidden=true);
}};
document.querySelectorAll('[data-report-view]').forEach(button=>{{
button.addEventListener('click',()=>{{
const name=button.dataset.reportView, view=document.getElementById(`embedded-${{name}}`), frame=view.querySelector('iframe');
if(!frame.srcdoc) frame.srcdoc=embeddedReports[name];
document.getElementById('comparison-landing').hidden=true;
document.querySelectorAll('.embedded-report-view').forEach(candidate=>candidate.hidden=candidate!==view);
}}); }});
window.addEventListener('message',event=>{{
if(event.data && event.data.type==='expense-forecast:return-comparison') showComparison();
}});
}})();
</script></body></html>"""

        if not write_file:
            return html
        if output_path is None:
            target_path = Path(
                f"Comparison_{E_1.unique_id}_vs_{E_2.unique_id}.html"
            )
        else:
            target_path = Path(output_path)
            if target_path.suffix.lower() not in {".html", ".htm"}:
                target_path = target_path / (
                    f"Comparison_{E_1.unique_id}_vs_{E_2.unique_id}.html"
                )
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(html)
        cls._phase_log(
            "green",
            "Comparison report completed: "
            f"baseline={E_1.unique_id} comparison={E_2.unique_id} "
            f"destination={target_path} elapsed={perf_counter()-started_at:.2f}s",
        )
        return str(target_path)

    @classmethod
    def generateForecastSetReport(
        cls,
        result_set: ForecastResultSet,
        report_name: str = "Feasibility Report",
        output_path=None,
        write_file: bool = True,
    ) -> str:
        """Generate reports and an interactive index for completed forecasts."""
        if not isinstance(result_set, ForecastResultSet):
            raise TypeError("result_set must be a ForecastResultSet")
        started_at = perf_counter()
        results = list(result_set.results)

        if output_path is None:
            main_path = Path(f"ForecastSet_{result_set.unique_id}.html")
        else:
            main_path = Path(output_path)
            if main_path.suffix.lower() not in {".html", ".htm"}:
                main_path = main_path / f"ForecastSet_{result_set.unique_id}.html"
        report_directory = main_path.with_name(
            f"{main_path.stem}_reports"
        )

        def report_name_for(result):
            return (
                result.initial_conditions.forecast_name
                or f"Forecast {result.unique_id}"
            )

        single_reports = {}
        for result in results:
            filename = f"Forecast_{result.unique_id}.html"
            if write_file:
                target = report_directory / filename
                cls.generateHTMLReport(result, output_path=target)
                single_reports[result.unique_id] = (
                    f"{report_directory.name}/{filename}"
                )
            else:
                single_reports[result.unique_id] = cls.generateHTMLReport(
                    result, write_file=False, comparison_return=True
                )

        comparison_reports = {}
        for baseline_index, baseline in enumerate(results):
            for alternate_index in range(baseline_index + 1, len(results)):
                alternate = results[alternate_index]
                filename = (
                    f"Comparison_{baseline.unique_id}_vs_"
                    f"{alternate.unique_id}.html"
                )
                key = f"{baseline_index}:{alternate_index}"
                if write_file:
                    target = report_directory / filename
                    cls.generateComparisonReport(
                        baseline, alternate, output_path=target
                    )
                    comparison_reports[key] = (
                        f"{report_directory.name}/{filename}"
                    )
                else:
                    comparison_reports[key] = cls.generateComparisonReport(
                        baseline, alternate, write_file=False
                    )

        def append_unique(target, values):
            observed = set(target)
            for value in values:
                if value not in observed:
                    target.append(value)
                    observed.add(value)

        dimensions = []
        choices_by_dimension = {}
        milestones = []
        account_metrics = []
        summary_metrics = [
            "Net Worth", "Liquid Total", "CC Debt Total", "Loan Total",
            "Investment Total",
        ]
        for result in results:
            line_items = (
                result.resolved_line_item_set
                or result.initial_conditions.initial_line_item_set
            )
            append_unique(dimensions, line_items.scenario_dimensions.keys())
            for dimension_name, definitions in (
                line_items.scenario_dimensions.items()
            ):
                choices_by_dimension.setdefault(dimension_name, [])
                append_unique(
                    choices_by_dimension[dimension_name],
                    definitions.keys(),
                )
            append_unique(
                milestones,
                getattr(result.milestone_set, "milestone_names", []),
            )
            for group in result.milestone_results or []:
                if isinstance(group, dict):
                    append_unique(milestones, group.keys())
            resolved_accounts = getattr(
                result,
                "resolved_account_set",
                result.initial_conditions.initial_account_set,
            )
            append_unique(
                account_metrics,
                [account.name for account in resolved_accounts.accounts],
            )
        append_unique(
            account_metrics,
            [
                metric for metric in summary_metrics
                if any(metric in result.forecast_df.columns for result in results)
            ],
        )

        def milestone_value(value):
            if value is None or str(value).strip().lower() in {
                "", "none", "nat", "not achieved",
            }:
                return None
            try:
                return cls._normalize_date_value(value).isoformat()
            except (TypeError, ValueError):
                return None

        report_rows = []
        for index, result in enumerate(results):
            line_items = (
                result.resolved_line_item_set
                or result.initial_conditions.initial_line_item_set
            )
            flattened_milestones = {}
            for group in result.milestone_results or []:
                if isinstance(group, dict):
                    flattened_milestones.update(group)
            final_row = result.forecast_df.iloc[-1]
            values = {
                metric: (
                    float(final_row[metric])
                    if metric in result.forecast_df.columns else 0.0
                )
                for metric in account_metrics
            }
            report_rows.append({
                "index": index,
                "id": result.unique_id,
                "name": report_name_for(result),
                "choices": {
                    dimension: line_items.scenario_selections.get(dimension)
                    for dimension in dimensions
                },
                "milestones": {
                    name: milestone_value(flattened_milestones.get(name))
                    for name in milestones
                },
                "values": values,
                "single_report": (
                    single_reports[result.unique_id] if write_file else "#"
                ),
            })

        matrix_header = "".join(
            f"<th>{escape(report_name_for(result))}</th>"
            for result in results
        )
        matrix_rows = []
        for row_index, row_result in enumerate(results):
            cells = []
            for column_index, column_result in enumerate(results):
                if column_index < row_index:
                    cells.append('<td class="matrix-empty">—</td>')
                elif column_index == row_index:
                    cells.append(
                        '<td><a class="report-link" '
                        f'data-report-kind="single" data-report-key="'
                        f'{escape(row_result.unique_id, quote=True)}" href="'
                        f'{escape(single_reports[row_result.unique_id] if write_file else "#", quote=True)}">'
                        "Single</a></td>"
                    )
                else:
                    key = f"{row_index}:{column_index}"
                    cells.append(
                        '<td><a class="report-link" '
                        f'data-report-kind="comparison" data-report-key="{key}" '
                        f'href="{escape(comparison_reports[key] if write_file else "#", quote=True)}">'
                        "Compare</a></td>"
                    )
            matrix_rows.append(
                f"<tr><th>{escape(report_name_for(row_result))}</th>"
                + "".join(cells) + "</tr>"
            )

        filter_controls = []
        multiple_controls = []
        for dimension in dimensions:
            choice_values = choices_by_dimension.get(dimension, [])
            datalist_id = "choices-" + hashlib.sha256(
                dimension.encode("utf-8")
            ).hexdigest()[:8]
            labels = ["All", *choice_values]
            filter_controls.append(
                '<label class="filter-control"><span>'
                f"{escape(dimension)}</span>"
                f'<input type="range" min="0" max="{len(choice_values)}" '
                f'value="0" step="1" data-single-dimension="'
                f'{escape(dimension, quote=True)}" list="{datalist_id}">'
                f'<output data-single-output="{escape(dimension, quote=True)}">'
                "All</output>"
                f'<datalist id="{datalist_id}">'
                + "".join(
                    f'<option value="{index}" label="{escape(label, quote=True)}">'
                    for index, label in enumerate(labels)
                )
                + "</datalist></label>"
            )
            multiple_controls.append(
                '<label class="filter-control"><span>'
                f"{escape(dimension)}</span>"
                f'<select multiple data-multiple-dimension="'
                f'{escape(dimension, quote=True)}">'
                + "".join(
                    f'<option value="{escape(choice, quote=True)}" selected>'
                    f"{escape(choice)}</option>"
                    for choice in choice_values
                )
                + "</select></label>"
            )

        table_headers = (
            "<th>Report</th>"
            + "".join(f"<th>{escape(value)}</th>" for value in dimensions)
            + "".join(
                f"<th>{escape(value)} Date</th>" for value in milestones
            )
            + "".join(
                f"<th>Final {escape(value)}</th>" for value in account_metrics
            )
        )
        data_payload = json.dumps({
            "results": report_rows,
            "dimensions": dimensions,
            "choices": choices_by_dimension,
            "milestones": milestones,
            "metrics": account_metrics,
            "write_file": write_file,
            "single_reports": single_reports if not write_file else {},
            "comparison_reports": (
                comparison_reports if not write_file else {}
            ),
        }, ensure_ascii=False).replace("<", "\\u003c")

        html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(report_name)}</title>
<style>
:root{{--bg:#f7f7f5;--surface:#fff;--text:#1d1d1f;--muted:#77777d;
--border:#dedee2;--accent:#315c72;--positive:#2f7d4a;--negative:#b65a5a}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--text);
font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}}
.page{{width:min(1800px,100%);margin:auto;padding:40px clamp(20px,3vw,56px) 72px}}
.hero{{text-align:center;margin-bottom:32px}}.hero h1{{margin:0;font-size:2.15rem}}
.hero p{{margin:8px 0 0;color:var(--muted)}} .workspace{{display:grid;
grid-template-columns:minmax(230px,1fr) minmax(460px,3fr) minmax(250px,1.2fr);
gap:22px;align-items:stretch}} .card{{background:var(--surface);border:1px solid var(--border);
border-radius:12px;padding:20px;box-shadow:0 1px 2px rgba(0,0,0,.025)}} h2{{font-size:1.15rem;margin:0 0 14px}}
.mode-nav{{display:grid;grid-template-columns:repeat(3,1fr);border:1px solid var(--border);
border-radius:9px;overflow:hidden;margin-bottom:18px}}.mode-nav button{{border:0;border-left:1px solid var(--border);
padding:10px 5px;background:#fafafa;color:var(--muted);cursor:pointer}}.mode-nav button:first-child{{border-left:0}}
.mode-nav button.active{{background:var(--accent);color:white}}.mode-panel[hidden]{{display:none}}
.filter-control{{display:grid;gap:7px;margin:0 0 17px;font-size:.84rem;font-weight:650}}
.filter-control output{{color:var(--accent);font-weight:700}}select[multiple]{{min-height:90px;border:1px solid var(--border);border-radius:7px}}
#scatter{{width:100%;min-height:520px;display:block}}.legend{{display:flex;flex-wrap:wrap;gap:8px;
max-height:145px;overflow:auto;margin-top:12px}}.legend label{{font-size:.72rem;color:var(--muted);
border:1px solid var(--border);border-radius:999px;padding:5px 8px;background:#fafafa}}
.range-group{{border-top:1px solid #ececef;padding:12px 0}}.range-group:first-child{{border-top:0}}
.range-name{{font-weight:700;font-size:.84rem}}.range-value{{display:block;color:var(--muted);font-size:.8rem;margin-top:3px}}
.section{{margin-top:28px}}.table-scroll{{overflow:auto;max-width:100%}}table{{border-collapse:collapse;width:100%;font-size:.82rem}}
th,td{{padding:10px 12px;border-bottom:1px solid #ececef;text-align:left;white-space:nowrap}}th{{color:var(--muted);background:#fafafa}}
.report-link{{color:var(--accent);font-weight:700;text-decoration:none}}.matrix-empty{{color:#c7c7cc}}
.report-button{{display:inline-block;padding:6px 10px;border-radius:7px;background:var(--accent);
color:#fff;font-weight:700;text-decoration:none}}
.placeholder{{min-height:220px;display:grid;place-items:center;text-align:center;color:var(--muted);
border:1px dashed #bfc0c5;border-radius:9px}}.tooltip{{position:fixed;z-index:10;pointer-events:none;
background:#202124;color:#fff;padding:9px 11px;border-radius:7px;font-size:.75rem;white-space:pre-line;
box-shadow:0 5px 18px rgba(0,0,0,.2)}}.tooltip[hidden]{{display:none}}
.embedded-view{{position:fixed;inset:0;z-index:20;background:var(--bg)}}.embedded-view[hidden]{{display:none}}
.embedded-view iframe{{width:100%;height:100vh;border:0}}
@media(max-width:1050px){{.workspace{{grid-template-columns:1fr}}}}
</style></head><body><main class="page">
<header class="hero"><h1>{escape(report_name)}</h1>
<p>{result_set.start_date:%Y-%m-%d} to {result_set.end_date:%Y-%m-%d}</p></header>
<section class="workspace">
<aside class="card"><nav class="mode-nav">
<button class="active" data-mode="single">SINGLE</button>
<button data-mode="multiple">MULTIPLE</button><button data-mode="range">RANGE</button>
</nav><div class="mode-panel" data-panel="single">{''.join(filter_controls) or '<p>No scenario dimensions.</p>'}</div>
<div class="mode-panel" data-panel="multiple" hidden>{''.join(multiple_controls) or '<p>No scenario dimensions.</p>'}</div>
<div class="mode-panel placeholder" data-panel="range" hidden>Drag-to-select range analysis will be added in a future revision.</div></aside>
<section class="card"><h2>Feasible Region</h2><svg id="scatter" viewBox="0 0 980 560"></svg>
<div class="legend" id="series-legend"></div></section>
<aside class="card"><h2>Visible Ranges</h2><div id="range-panel"></div></aside>
</section>
<section class="card section"><h2>Forecast Outcomes</h2><div class="table-scroll">
<table><thead><tr>{table_headers}</tr></thead><tbody id="forecast-table"></tbody></table></div></section>
<section class="card section"><h2>Comparison Reports</h2>
<p>Rows are baselines; columns are alternates.</p><div class="table-scroll"><table>
<thead><tr><th>Baseline \\ Alternate</th>{matrix_header}</tr></thead>
<tbody>{''.join(matrix_rows)}</tbody></table></div></section>
</main><div class="tooltip" id="tooltip" hidden></div>
<section class="embedded-view" id="embedded-view" hidden><iframe title="Embedded forecast report"></iframe></section>
<script id="forecast-set-data" type="application/json">{data_payload}</script>
<script>
(()=>{{const data=JSON.parse(document.getElementById('forecast-set-data').textContent);
const NS='http://www.w3.org/2000/svg',svg=document.getElementById('scatter'),tooltip=document.getElementById('tooltip');
const money=v=>new Intl.NumberFormat('en-US',{{style:'currency',currency:'USD',maximumFractionDigits:0}}).format(v);
const safe=v=>String(v??'').replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
const dateText=v=>v||'—';let mode='single',hiddenSeries=new Set();
const colors=['#315c72','#2f7d4a','#9b6a3c','#76528f','#b65a5a','#367c83','#8a7a2f','#5a6c9f'];
const series=[];data.milestones.forEach(m=>data.metrics.forEach(metric=>series.push({{key:m+'\\u001f'+metric,milestone:m,metric}})));
function filters(){{const result={{}};if(mode==='single')document.querySelectorAll('[data-single-dimension]').forEach(input=>{{
const choices=data.choices[input.dataset.singleDimension]||[],i=Number(input.value);result[input.dataset.singleDimension]=i?new Set([choices[i-1]]):null;}});
else if(mode==='multiple')document.querySelectorAll('[data-multiple-dimension]').forEach(select=>{{
const selected=new Set([...select.selectedOptions].map(o=>o.value)),all=data.choices[select.dataset.multipleDimension]||[];
result[select.dataset.multipleDimension]=selected.size===all.length?null:selected;}});return result;}}
function visible(){{const f=filters();return data.results.filter(r=>Object.entries(f).every(([d,wanted])=>!wanted||wanted.has(r.choices[d])));}}
function el(tag,attrs,text){{const node=document.createElementNS(NS,tag);Object.entries(attrs||{{}}).forEach(([k,v])=>node.setAttribute(k,v));
if(text!==undefined)node.textContent=text;return node;}}
function renderLegend(){{const root=document.getElementById('series-legend');root.innerHTML='';series.forEach((s,i)=>{{
const label=document.createElement('label'),box=document.createElement('input');box.type='checkbox';box.checked=!hiddenSeries.has(s.key);
box.addEventListener('change',()=>{{box.checked?hiddenSeries.delete(s.key):hiddenSeries.add(s.key);render();}});
label.append(box,document.createTextNode(' '+s.milestone+' × '+s.metric));label.style.borderColor=colors[i%colors.length];root.append(label);}});}}
function renderPlot(rows){{svg.innerHTML='';const points=[];series.forEach((s,si)=>{{if(hiddenSeries.has(s.key))return;
rows.forEach(r=>{{const d=r.milestones[s.milestone];if(d)points.push({{r,s,si,x:new Date(d+'T00:00:00').getTime(),y:r.values[s.metric]}});}});}});
const left=92,right=955,top=25,bottom=505,xValues=points.map(p=>p.x),xMin=xValues.length?Math.min(...xValues):Date.now();
const xMaxRaw=xValues.length?Math.max(...xValues):xMin+86400000,xMax=xMaxRaw===xMin?xMin+86400000:xMaxRaw;
const yMin=Math.min(0,...points.map(p=>p.y)),yMax=Math.max(1,...points.map(p=>p.y));const sx=x=>left+(x-xMin)/(xMax-xMin||1)*(right-left);
const sy=y=>bottom-(y-yMin)/(yMax-yMin||1)*(bottom-top);svg.append(el('line',{{x1:left,y1:bottom,x2:right,y2:bottom,stroke:'#999'}}));
svg.append(el('line',{{x1:left,y1:top,x2:left,y2:bottom,stroke:'#999'}}));if(!points.length)svg.append(el('text',{{x:520,y:270,'text-anchor':'middle',fill:'#777'}},'No achieved milestones for visible forecasts'));
for(let i=0;i<5;i++){{const stamp=xMin+(xMax-xMin)*i/4,x=sx(stamp),label=new Date(stamp).toISOString().slice(0,10);
svg.append(el('line',{{x1:x,y1:bottom,x2:x,y2:bottom+5,stroke:'#999'}}));svg.append(el('text',{{x,y:bottom+20,'text-anchor':'middle',fill:'#777','font-size':11}},label));}}
for(let i=0;i<5;i++){{const value=yMin+(yMax-yMin)*i/4,y=sy(value);svg.append(el('line',{{x1:left,y1:y,x2:right,y2:y,stroke:'#ececef'}}));
svg.append(el('text',{{x:left-8,y:y+4,'text-anchor':'end',fill:'#777','font-size':11}},money(value)));}}
points.forEach(p=>{{const c=el('circle',{{cx:sx(p.x),cy:sy(p.y),r:5,fill:colors[p.si%colors.length],opacity:.72,stroke:'#fff','stroke-width':1}});
c.addEventListener('mouseenter',event=>{{tooltip.hidden=false;tooltip.textContent=p.r.name+'\\n'+p.s.milestone+': '+p.r.milestones[p.s.milestone]+'\\n'+p.s.metric+': '+money(p.y);
tooltip.style.left=(event.clientX+12)+'px';tooltip.style.top=(event.clientY+12)+'px';}});c.addEventListener('mouseleave',()=>tooltip.hidden=true);
c.addEventListener('click',()=>openReport('single',p.r.id,p.r.single_report));svg.append(c);}});
svg.append(el('text',{{x:520,y:550,'text-anchor':'middle',fill:'#777','font-size':12}},'Milestone achievement date'));}}
function renderRanges(rows){{const root=document.getElementById('range-panel');root.innerHTML='';data.metrics.forEach(metric=>{{const values=rows.map(r=>r.values[metric]);
const div=document.createElement('div');div.className='range-group';div.innerHTML='<span class="range-name">'+safe(metric)+'</span><span class="range-value">'+(values.length?money(Math.min(...values))+' – '+money(Math.max(...values)):'—')+'</span>';root.append(div);}});
data.milestones.forEach(m=>{{const dates=rows.map(r=>r.milestones[m]).filter(Boolean).sort(),missing=rows.length-dates.length,div=document.createElement('div');div.className='range-group';
div.innerHTML='<span class="range-name">'+safe(m)+'</span><span class="range-value">'+(dates.length?dates[0]+' – '+dates[dates.length-1]:'Not achieved')+(missing?' · '+missing+' unachieved':'')+'</span>';root.append(div);}});}}
function renderTable(rows){{const body=document.getElementById('forecast-table');body.innerHTML='';rows.forEach(r=>{{const tr=document.createElement('tr');
let html='<td><a class="report-button" href="'+r.single_report+'" data-dynamic-single="'+r.id+'">Open</a></td>';
data.dimensions.forEach(d=>html+='<td>'+safe(r.choices[d]||'—')+'</td>');data.milestones.forEach(m=>html+='<td>'+safe(dateText(r.milestones[m]))+'</td>');
data.metrics.forEach(metric=>html+='<td>'+money(r.values[metric])+'</td>');tr.innerHTML=html;body.append(tr);}});
body.querySelectorAll('[data-dynamic-single]').forEach(a=>a.addEventListener('click',e=>{{if(!data.write_file){{e.preventDefault();openReport('single',a.dataset.dynamicSingle,data.single_reports[a.dataset.dynamicSingle]);}}}}));}}
function render(){{const rows=visible();renderPlot(rows);renderRanges(rows);renderTable(rows);}}
function openReport(kind,key,htmlOrHref){{if(data.write_file){{location.href=htmlOrHref;return;}}const view=document.getElementById('embedded-view'),frame=view.querySelector('iframe');
frame.srcdoc=kind==='single'?data.single_reports[key]:data.comparison_reports[key];view.hidden=false;}}
document.querySelectorAll('[data-mode]').forEach(button=>button.addEventListener('click',()=>{{mode=button.dataset.mode;
document.querySelectorAll('[data-mode]').forEach(b=>b.classList.toggle('active',b===button));document.querySelectorAll('[data-panel]').forEach(p=>p.hidden=p.dataset.panel!==mode);
if(mode!=='range')render();}}));document.querySelectorAll('[data-single-dimension]').forEach(input=>input.addEventListener('input',()=>{{
const choices=data.choices[input.dataset.singleDimension]||[];document.querySelector('[data-single-output="'+CSS.escape(input.dataset.singleDimension)+'"]').value=Number(input.value)?choices[Number(input.value)-1]:'All';render();}}));
document.querySelectorAll('[data-multiple-dimension]').forEach(select=>select.addEventListener('change',render));
document.querySelectorAll('.report-link[data-report-kind]').forEach(a=>a.addEventListener('click',e=>{{if(!data.write_file){{e.preventDefault();openReport(a.dataset.reportKind,a.dataset.reportKey);}}}}));
window.addEventListener('message',event=>{{if(event.data&&event.data.type==='expense-forecast:return-comparison')document.getElementById('embedded-view').hidden=true;}});
renderLegend();render();}})();
</script></body></html>"""

        if not write_file:
            return html
        # Single-forecast reports currently load the project-owned chart
        # renderers as sibling files. Keep the generated bundle portable by
        # placing those renderers beside every child report.
        project_root = Path(__file__).resolve().parents[2]
        report_directory.mkdir(parents=True, exist_ok=True)
        for asset_name in ("hero_chart.js", "detail_charts.js"):
            source = project_root / asset_name
            if source.exists():
                shutil.copy2(source, report_directory / asset_name)
        main_path.parent.mkdir(parents=True, exist_ok=True)
        main_path.write_text(html)
        cls._phase_log(
            "green",
            "Forecast-set report completed: "
            f"forecasts={len(results)} comparisons={len(comparison_reports)} "
            f"destination={main_path} elapsed={perf_counter()-started_at:.2f}s",
        )
        return str(main_path)

    @staticmethod
    def _assert_report_accounting_invariants(
        E: ExpenseForecastResult,
    ) -> None:
        """Fail before rendering when presentation accounting is inconsistent.

        Net Gain and Net Loss are derived from Memo and Memo Directives.  A
        graph node that accidentally appends its presentation text again can
        therefore inflate the report without changing any account balance.
        These checks keep that class of engine bug from becoming a plausible-
        looking HTML report.
        """
        forecast_df = E.forecast_df
        for column in ("Net Gain", "Net Loss"):
            if column not in forecast_df.columns:
                continue
            values = pd.to_numeric(forecast_df[column], errors="coerce")
            assert values.notna().all(), (
                f"Report invariant failed: {column} contains a non-numeric "
                "value."
            )
            assert values.map(math.isfinite).all(), (
                f"Report invariant failed: {column} contains an infinite "
                "value."
            )
            assert (values >= -MONEY_BOUNDARY_TOLERANCE).all(), (
                f"Report invariant failed: {column} contains a negative "
                "value."
            )

        confirmed_df = E.confirmed_df
        required_columns = {"Date", "Amount", "Income_Flag"}
        if (
            confirmed_df is None
            or not required_columns.issubset(confirmed_df.columns)
            or "Memo Directives" not in forecast_df.columns
        ):
            return

        confirmed_income_counts: dict[tuple[date, float], int] = {}
        for _, transaction in confirmed_df.iterrows():
            if not bool(transaction["Income_Flag"]):
                continue
            transaction_date = pd.Timestamp(transaction["Date"]).date()
            amount = round(float(transaction["Amount"]), 2)
            key = (transaction_date, amount)
            confirmed_income_counts[key] = (
                confirmed_income_counts.get(key, 0) + 1
            )

        rendered_income_counts: dict[tuple[date, float], int] = {}
        income_pattern = re.compile(
            r"^INCOME\s*\([^)]*\+\$([0-9,]+(?:\.\d+)?)\)$",
            re.IGNORECASE,
        )
        for row_index, row in forecast_df.iterrows():
            row_date_value = (
                row["Date"] if "Date" in forecast_df.columns else row_index
            )
            row_date = pd.Timestamp(row_date_value).date()
            for raw_directive in str(row["Memo Directives"]).split(";"):
                directive = raw_directive.strip()
                match = income_pattern.match(directive)
                if match is None:
                    continue
                amount = round(
                    float(match.group(1).replace(",", "")), 2
                )
                key = (row_date, amount)
                rendered_income_counts[key] = (
                    rendered_income_counts.get(key, 0) + 1
                )

        for key, rendered_count in rendered_income_counts.items():
            confirmed_count = confirmed_income_counts.get(key, 0)
            assert rendered_count <= confirmed_count, (
                "Report invariant failed: income memo directives exceed "
                "confirmed income transactions for "
                f"date={key[0]} amount=${key[1]:.2f}; "
                f"directives={rendered_count}, confirmed={confirmed_count}. "
                "A computation node may have appended its memo more than once."
            )

        # Rebuild every presentation-accounting column from the account rows,
        # Memo, and Memo Directives. This deliberately starts with a copy of
        # the raw forecast instead of trusting the values the report is about
        # to plot. A mismatch identifies the exact row and derived column.
        report_account_set = getattr(
            E, "resolved_account_set",
            E.initial_conditions.initial_account_set,
        )
        recomputed = ForecastHandler._appendSummaryLines(
            report_account_set,
            forecast_df.copy(deep=True),
        )
        audited_columns = (
            "Net Gain",
            "Net Loss",
            "Interest Accrued",
            "Investment Returns",
            "Liquid Total",
            "Investment Total",
            "CC Debt Total",
            "Loan Total",
            "Net Worth",
        )
        tolerance = float(MONEY_BOUNDARY_TOLERANCE)

        # Graph v2 calculates summaries from full-precision balances and then
        # rounds every public column to cents.  This audit necessarily rebuilds
        # those summaries from the already-rounded account columns.  Each
        # component can therefore contribute half a cent of harmless display
        # error, plus another half cent when the original total was rounded.
        # Use that mathematical bound only for account aggregates; memo-derived
        # gain, loss, interest, and return values retain the stricter tolerance.
        account_info = report_account_set.getAccounts()
        aggregate_component_counts = {
            "Liquid Total": int((account_info.Account_Type == "checking").sum()),
            "Investment Total": int(
                (account_info.Account_Type == "investment").sum()
            ),
            "CC Debt Total": int(
                account_info.Account_Type.isin(
                    ["credit", "credit prev stmt bal", "credit curr stmt bal"]
                ).sum()
            ),
            "Loan Total": int(
                account_info.Account_Type.isin(
                    ["loan", "principal balance", "interest"]
                ).sum()
            ),
        }
        aggregate_component_counts["Net Worth"] = sum(
            aggregate_component_counts.values()
        )

        for column in audited_columns:
            if column not in forecast_df.columns or column not in recomputed:
                continue
            actual_values = pd.to_numeric(
                forecast_df[column], errors="coerce"
            )
            expected_values = pd.to_numeric(
                recomputed[column], errors="coerce"
            )
            allowed_difference = tolerance
            if column in aggregate_component_counts:
                allowed_difference = (
                    aggregate_component_counts[column] + 1
                ) * tolerance
            # Absorb only floating-point representation noise around the
            # float-derived boundary itself.
            allowed_difference += 1e-9
            mismatches = (
                actual_values - expected_values
            ).abs() > allowed_difference
            if not mismatches.any():
                continue
            row_index = mismatches[mismatches].index[0]
            row_date = (
                forecast_df.at[row_index, "Date"]
                if "Date" in forecast_df.columns
                else row_index
            )
            assert False, (
                "Report accounting invariant failed: derived value does not "
                f"match account changes and parsed memo data at date={row_date} "
                f"column={column!r}; actual={actual_values.at[row_index]!r}, "
                f"recomputed={expected_values.at[row_index]!r}."
            )

        # Net worth and its day-to-day change must also reconcile directly to
        # the four account-type totals. This is independent of memo parsing and
        # catches a summary that omits or double-counts an account category.
        total_columns = {
            "Liquid Total",
            "Investment Total",
            "CC Debt Total",
            "Loan Total",
            "Net Worth",
        }
        if total_columns.issubset(forecast_df.columns):
            numeric = {
                column: pd.to_numeric(forecast_df[column], errors="coerce")
                for column in total_columns
            }
            expected_net_worth = (
                numeric["Liquid Total"]
                + numeric["Investment Total"]
                - numeric["CC Debt Total"]
                - numeric["Loan Total"]
            )
            # Five independently rounded public totals participate in this
            # identity: Net Worth and the four account-type summaries.
            net_worth_identity_tolerance = (5 * tolerance) + 1e-9
            net_worth_mismatch = (
                numeric["Net Worth"] - expected_net_worth
            ).abs() > net_worth_identity_tolerance
            assert not net_worth_mismatch.any(), (
                "Report accounting invariant failed: Net Worth does not "
                "equal liquid plus investments minus credit and loan debt."
            )

            actual_change = numeric["Net Worth"].diff().fillna(0)
            expected_change = (
                numeric["Liquid Total"].diff().fillna(0)
                + numeric["Investment Total"].diff().fillna(0)
                - numeric["CC Debt Total"].diff().fillna(0)
                - numeric["Loan Total"].diff().fillna(0)
            )
            # A difference compares two adjacent rounded identities, doubling
            # their maximum presentation error.
            assert (
                (actual_change - expected_change).abs()
                <= (2 * net_worth_identity_tolerance)
            ).all(), (
                "Report accounting invariant failed: a daily Net Worth change "
                "does not reconcile to the account-type balance changes."
            )

    @classmethod
    def generateHTMLReport(
        cls,
        E: ExpenseForecastResult,
        output_path=None,
        write_file=True,
        comparison_return: bool = False,
    ) -> str:
        """
        Generate a self-contained HTML report for one ExpenseForecastResult.

        By default, write the report to output_path (or a forecast-named file
        in the current directory) and return its path. When write_file is
        false, return the generated HTML without writing a file.
        """

        report_started_at = perf_counter()
        cls._assert_report_accounting_invariants(E)
        cls._phase_log(
            "blue",
            "Report generation started: "
            f"forecast={(getattr(E.initial_conditions, 'forecast_name', None) or 'Unnamed forecast')!r} "
            f"id={E.unique_id} output="
            f"{'memory' if not write_file else output_path or 'default HTML path'}",
        )
        report_scalars = {}

        report_scalars['scenario_name'] = E.initial_conditions.forecast_name
        report_scalars['unique_id'] = E.unique_id
        report_scalars['date_range'] = str((E.initial_conditions.end_date - E.initial_conditions.start_date).days) + " days : " + E.initial_conditions.start_date.strftime('%Y-%m-%d') + ' to ' + E.initial_conditions.end_date.strftime('%Y-%m-%d')

        length_of_forecast_in_days = (E.initial_conditions.end_date - E.initial_conditions.start_date).days

        net_worth_delta = cls.get_last_row_first_row_delta(E.forecast_df, 'Net Worth')

        report_scalars['net_worth_page_text_above_plots']= cls.get_delta_explanation_sentence('Net Worth', net_worth_delta, length_of_forecast_in_days)
        report_scalars['net_worth_page_text_below_plots'] = ''

        net_gain_and_loss_page_text_above_plots = '' 
        net_gain_and_loss_page_text_below_plots = ''


        liquid_delta = cls.get_last_row_first_row_delta(E.forecast_df, 'Liquid Total')
        cc_debt_delta = cls.get_last_row_first_row_delta(E.forecast_df, 'CC Debt Total')
        loan_total_delta = cls.get_last_row_first_row_delta(E.forecast_df, 'Loan Total')
        liquid_delta_sent = cls.get_delta_explanation_sentence('Liquid Total', liquid_delta, length_of_forecast_in_days)
        cc_delta_sent = cls.get_delta_explanation_sentence('CC Debt Total', cc_debt_delta, length_of_forecast_in_days)
        loan_delta_sent = cls.get_delta_explanation_sentence('Loan Total', loan_total_delta, length_of_forecast_in_days)
        report_scalars['account_type_page_text_above_plots'] = liquid_delta_sent + '\n' + cc_delta_sent + '\n' + loan_delta_sent
        account_type_page_text_below_plots = ''

        total_interest_accrued = sum(E.forecast_df['Interest Accrued'])
        total_investment_returns = sum(E.forecast_df['Investment Returns'])
        report_scalars['interest_page_text_above_plots'] = (
            f"Interest accrued: ${total_interest_accrued:,.2f}. "
            f"Investment returns: ${total_investment_returns:,.2f}."
        )
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

        def milestone_timestamp(date_achieved):
            if date_achieved is None:
                return None
            if isinstance(date_achieved, str) and date_achieved.strip().lower() in {
                "", "none", "nan", "nat",
            }:
                return None
            timestamp = pd.to_datetime(date_achieved, errors="coerce")
            return None if pd.isna(timestamp) else pd.Timestamp(timestamp)

        milestone_timestamps = {
            milestone_name: milestone_timestamp(date_achieved)
            for milestone_name, date_achieved in milestone_results.items()
        }
        achieved_milestones = [
            (milestone_name, timestamp)
            for milestone_name, timestamp in milestone_timestamps.items()
            if timestamp is not None
        ]

        def format_milestone_elapsed_time(date_achieved: pd.Timestamp) -> str:
            elapsed_days = (
                date_achieved.normalize()
                - forecast_start_date.normalize()
            ).days
            if elapsed_days < 365:
                unit = "day" if elapsed_days == 1 else "days"
                return f"{elapsed_days} {unit}"
            elapsed_years = elapsed_days / 365.25
            return f"{elapsed_years:.1f} years"

        milestone_date_rows = [
                {
                    "Milestone": milestone_name,
                    "Date": date_achieved.date().isoformat(),
                    "Time": format_milestone_elapsed_time(date_achieved),
                }
                for milestone_name, date_achieved in sorted(
                    achieved_milestones,
                    key=lambda item: item[1],
                )
            ]
        milestone_date_rows.extend(
            {
                "Milestone": milestone_name,
                "Date": "Not achieved",
                "Time": "-",
            }
            for milestone_name, timestamp in milestone_timestamps.items()
            if timestamp is None
        )
        report_data_frames["milestone_dates"] = pd.DataFrame(
            milestone_date_rows,
            columns=["Milestone", "Date", "Time"],
        )

        initial_conditions = E.initial_conditions
        initial_account_set = getattr(
            E, "resolved_account_set",
            initial_conditions.initial_account_set,
        )
        initial_line_item_set = initial_conditions.initial_line_item_set
        initial_memo_rule_set = initial_conditions.initial_memo_rule_set
        primary_checking_name = initial_account_set.primary_checking_account_name
        milestone_set = E.milestone_set

        report_data_frames["initial_account_set"] = initial_account_set.getAccounts()
        report_data_frames["initial_line_item_set"] = initial_line_item_set.getLineItems()
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
        investment_account_names = [
            account.name
            for account in initial_account_set.accounts
            if account.account_type == "investment"
            and account.name in E.forecast_df.columns
        ]
        initial_investments = (
            float(E.forecast_df.iloc[0][investment_account_names].sum())
            if investment_account_names else 0.0
        )
        final_investments = (
            float(E.forecast_df.iloc[-1][investment_account_names].sum())
            if investment_account_names else 0.0
        )

        def format_report_currency(value) -> str:
            numeric_value = float(value)
            if numeric_value < 0:
                return f"-${abs(numeric_value):,.2f}"
            return f"${numeric_value:,.2f}"

        def format_policy_label(value) -> str:
            return str(value).replace("_", " ").title()

        def format_policy_percentage(value) -> str:
            return f"{float(value) * 100:g}%"

        policy_results = getattr(E, "policy_results", {}) or {}
        safety_decisions = list(getattr(E, "safety_decisions", []) or [])

        def policy_resolution(policy):
            methods = {
                decision.get("resolution_method")
                for decision in safety_decisions
                if str(decision.get("memo", "")).startswith(
                    f"POLICY {policy.policy_key} "
                )
            }
            methods.discard(None)
            if not methods:
                return "Not evaluated"
            return "Mixed" if len(methods) > 1 else format_policy_label(next(iter(methods)))
        resolved_policies = list(
            getattr(getattr(E, "resolved_policy_set", None), "policies", [])
            or []
        )
        initial_policies = list(
            getattr(initial_conditions.policy_set, "policies", []) or []
        )
        # Older callers sometimes attach policy configuration to the result's
        # initial conditions after constructing the result (notably report
        # fixtures). Prefer the resolved snapshot whenever it contains data,
        # while retaining that harmless compatibility behavior for an empty
        # snapshot.
        configured_policies = resolved_policies or initial_policies
        ordered_policies = [
            policy
            for _, policy in sorted(
                enumerate(configured_policies),
                key=lambda item: (item[1].priority, item[0]),
            )
        ]

        policy_type_specs = [
            (
                MinimumCheckingBalancePolicy,
                "Minimum Checking Balance",
                "minimum_checking_balance_policies",
                [
                    "Priority", "Applies To", "Target", "If Unmet",
                    "Status", "Activation Date",
                ],
            ),
            (
                CurrentStatementBalancePaymentPolicy,
                "Current Statement Balance Payment",
                "current_statement_balance_payment_policies",
                [
                    "Priority", "Account", "Configuration", "If Unmet",
                    "Status", "Requested", "Executed",
                ],
            ),
            (
                SurplusDebtPaymentPolicy,
                "Surplus Debt Payment",
                "surplus_debt_payment_policies",
                [
                    "Priority", "Debt Type", "Strategy", "If Unmet",
                    "Status", "Debt Paid",
                ],
            ),
            (
                FixedMonthlyInvestmentPolicy,
                "Fixed Monthly Investment",
                "fixed_monthly_investment_policies",
                [
                    "Priority", "Account", "Amount", "Day", "If Unmet",
                    "Status", "Requested", "Executed", "Capped", "Missed",
                ],
            ),
            (
                IncomePercentageInvestmentPolicy,
                "Income Percentage Investment",
                "income_percentage_investment_policies",
                [
                    "Priority", "Account", "Percentage", "If Unmet",
                    "Status", "Requested", "Executed", "Capped", "Missed",
                ],
            ),
            (
                SurplusInvestmentPolicy,
                "Surplus Investment",
                "surplus_investment_policies",
                [
                    "Priority", "Account", "Checking Threshold", "If Unmet",
                    "Status", "Executed",
                ],
            ),
            (
                SurplusSavingPolicy,
                "Surplus Saving",
                "surplus_saving_policies",
                [
                    "Priority", "Account", "Saved Minimum Threshold", "If Unmet",
                    "Status", "Executed", "Shortfall",
                ],
            ),
            (
                PeriodicInvestmentContributionCapPolicy,
                "Investment Contribution Cap",
                "investment_contribution_cap_policies",
                [
                    "Priority", "Account", "Limit", "Period", "If Unmet",
                    "Status",
                ],
            ),
        ]

        def policy_presentation(policy):
            if isinstance(policy, MinimumCheckingBalancePolicy):
                account_name = policy.account_name or primary_checking_name
                return (
                    "Minimum Checking Balance",
                    account_name,
                    f"Keep {format_report_currency(policy.target)} available",
                )
            if isinstance(policy, CurrentStatementBalancePaymentPolicy):
                return (
                    "Current Statement Balance Payment",
                    policy.account_name,
                    "Pay current-cycle charges before rollover",
                )
            if isinstance(policy, SurplusDebtPaymentPolicy):
                applies_to = "Credit cards" if policy.debt_type == "credit" else "Loans"
                return (
                    (
                        "Surplus CC Payment"
                        if policy.debt_type == "credit"
                        else "Surplus Loan Payment"
                    ),
                    applies_to,
                    format_policy_label(policy.strategy),
                )
            if isinstance(policy, FixedMonthlyInvestmentPolicy):
                return (
                    "Fixed Monthly Investment",
                    policy.account_name,
                    f"{format_report_currency(policy.amount)} on day {policy.day}",
                )
            if isinstance(policy, IncomePercentageInvestmentPolicy):
                return (
                    "Income Percentage Investment",
                    policy.account_name,
                    f"Invest {format_policy_percentage(policy.percentage)} of income",
                )
            if isinstance(policy, SurplusInvestmentPolicy):
                return (
                    "Surplus Investment",
                    policy.account_name,
                    f"Invest checking above {format_report_currency(policy.checking_threshold)}",
                )
            if isinstance(policy, SurplusSavingPolicy):
                return (
                    "Surplus Saving",
                    policy.account_name,
                    "Save until "
                    f"{format_report_currency(policy.saved_minimum_threshold)}",
                )
            return (
                "Investment Contribution Cap",
                policy.account_name,
                f"{format_report_currency(policy.limit)} / {policy.period}",
            )

        report_data_frames["policies"] = pd.DataFrame(
            [
                {
                    "Priority": policy.priority,
                    "Policy": policy_presentation(policy)[0],
                    "Applies To": policy_presentation(policy)[1],
                    "Configuration": policy_presentation(policy)[2],
                    "If Unmet": format_policy_label(policy.on_unmet),
                    "Safety Resolution": policy_resolution(policy),
                }
                for policy in ordered_policies
            ],
            columns=[
                "Priority", "Policy", "Applies To", "Configuration", "If Unmet",
                "Safety Resolution",
            ],
        )

        report_data_frames["policy_safety_decisions"] = pd.DataFrame(
            [
                {
                    "Date": (
                        decision.get("date").isoformat()
                        if hasattr(decision.get("date"), "isoformat")
                        else decision.get("date", "—")
                    ),
                    "Policy Transaction": decision.get("memo", "—"),
                    "Requested": format_report_currency(decision.get("requested", 0)),
                    "Executed": format_report_currency(decision.get("executed", 0)),
                    "Resolution": format_policy_label(
                        decision.get("resolution_method", "unknown")
                    ),
                    "Available Headroom": (
                        format_report_currency(decision["available_headroom"])
                        if decision.get("available_headroom") is not None else "—"
                    ),
                    "Binding Account": decision.get("binding_account") or "—",
                    "Binding Date": decision.get("binding_date") or "—",
                    "Constraint / Fallback": (
                        decision.get("binding_constraint")
                        or decision.get("fallback_reason")
                        or "—"
                    ),
                }
                for decision in safety_decisions
            ],
            columns=[
                "Date", "Policy Transaction", "Requested", "Executed",
                "Resolution", "Available Headroom", "Binding Account",
                "Binding Date", "Constraint / Fallback",
            ],
        )

        def policy_detail_row(policy):
            result = policy_results.get(policy.policy_key, {}) or {}
            status = format_policy_label(result.get("status", "Not Run"))
            common = {
                "Priority": policy.priority,
                "If Unmet": format_policy_label(policy.on_unmet),
                "Status": status,
            }
            if isinstance(policy, MinimumCheckingBalancePolicy):
                activation_date = result.get("activation_date")
                return {
                    **common,
                    "Applies To": policy.account_name or primary_checking_name,
                    "Target": format_report_currency(policy.target),
                    "Activation Date": (
                        cls._normalize_date_value(activation_date).isoformat()
                        if activation_date not in (None, "None") else "—"
                    ),
                }
            if isinstance(policy, CurrentStatementBalancePaymentPolicy):
                return {
                    **common,
                    "Account": policy.account_name,
                    "Configuration": "Pay current-cycle charges before rollover",
                    "Requested": format_report_currency(result.get("requested", 0)),
                    "Executed": format_report_currency(result.get("executed", 0)),
                }
            if isinstance(policy, SurplusDebtPaymentPolicy):
                return {
                    **common,
                    "Debt Type": "Credit cards" if policy.debt_type == "credit" else "Loans",
                    "Strategy": format_policy_label(policy.strategy),
                    "Debt Paid": format_report_currency(result.get("debt_paid", 0)),
                }
            if isinstance(policy, FixedMonthlyInvestmentPolicy):
                return {
                    **common,
                    "Account": policy.account_name,
                    "Amount": format_report_currency(policy.amount),
                    "Day": policy.day,
                    "Requested": format_report_currency(result.get("requested", 0)),
                    "Executed": format_report_currency(result.get("executed", 0)),
                    "Capped": format_report_currency(result.get("capped", 0)),
                    "Missed": int(result.get("missed", 0)),
                }
            if isinstance(policy, IncomePercentageInvestmentPolicy):
                return {
                    **common,
                    "Account": policy.account_name,
                    "Percentage": format_policy_percentage(policy.percentage),
                    "Requested": format_report_currency(result.get("requested", 0)),
                    "Executed": format_report_currency(result.get("executed", 0)),
                    "Capped": format_report_currency(result.get("capped", 0)),
                    "Missed": int(result.get("missed", 0)),
                }
            if isinstance(policy, SurplusInvestmentPolicy):
                return {
                    **common,
                    "Account": policy.account_name,
                    "Checking Threshold": format_report_currency(policy.checking_threshold),
                    "Executed": format_report_currency(result.get("executed", 0)),
                }
            if isinstance(policy, SurplusSavingPolicy):
                return {
                    **common,
                    "Account": policy.account_name,
                    "Saved Minimum Threshold": format_report_currency(
                        policy.saved_minimum_threshold
                    ),
                    "Executed": format_report_currency(result.get("executed", 0)),
                    "Shortfall": format_report_currency(result.get("shortfall", 0)),
                }
            return {
                **common,
                "Account": policy.account_name,
                "Limit": format_report_currency(policy.limit),
                "Period": format_policy_label(policy.period),
            }

        for policy_type, _, dataframe_name, columns in policy_type_specs:
            report_data_frames[dataframe_name] = pd.DataFrame(
                [
                    policy_detail_row(policy)
                    for policy in ordered_policies
                    if isinstance(policy, policy_type)
                ],
                columns=columns,
            )

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
                    "Metric": "Initial Investments",
                    "Amount": format_report_currency(initial_investments),
                },
                {
                    "Metric": "Final Cash Reserve",
                    "Amount": format_report_currency(final_cash_reserve),
                },
                {
                    "Metric": "Final Available Credit",
                    "Amount": format_report_currency(final_available_credit),
                },
                {
                    "Metric": "Final Investments",
                    "Amount": format_report_currency(final_investments),
                },
            ],
            columns=["Metric", "Amount"],
        )

        transaction_schedule = (
            E.confirmed_df.copy()
            if isinstance(E.confirmed_df, pd.DataFrame)
            else initial_line_item_set.getLineItemSchedule().iloc[0:0].copy()
        )
        if not transaction_schedule.empty:
            transaction_schedule = transaction_schedule.sort_values(
                ["Date", "Priority", "Memo"],
                kind="stable",
            ).reset_index(drop=True)

        report_data_frames["all_transactions"] = transaction_schedule.copy()
        income_mask = (
            transaction_schedule["Income_Flag"].map(
                lambda value: False if pd.isna(value) else bool(value)
            )
            if "Income_Flag" in transaction_schedule.columns
            else pd.Series(False, index=transaction_schedule.index)
        )
        report_data_frames["income_transactions"] = transaction_schedule.loc[
            income_mask
        ].reset_index(drop=True)
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
        policy_loan_transaction_indices = set()
        for transaction_index, transaction in transaction_schedule.iterrows():
            memo = str(transaction["Memo"])
            try:
                memo_rule = initial_memo_rule_set.findMatchingMemoRule(
                    memo,
                    transaction["Priority"],
                )
            except ValueError:
                # Policy transfers are generated internally and therefore do
                # not exist in the caller's original MemoRuleSet. Their stable
                # policy keys still provide unambiguous report classification.
                if memo.startswith("POLICY surplus_debt_payment:credit "):
                    credit_transaction_indices.append(transaction_index)
                    continue
                if memo.startswith("POLICY surplus_debt_payment:loan "):
                    loan_transaction_indices.append(transaction_index)
                    policy_loan_transaction_indices.add(transaction_index)
                    continue
                if memo.startswith("POLICY "):
                    continue
                raise
            destination_type = account_types.get(memo_rule.account_to)
            if destination_type == "credit":
                credit_transaction_indices.append(transaction_index)
            elif (
                destination_type == "loan"
                or str(memo_rule.account_to).startswith("ALL_LOANS")
            ):
                loan_transaction_indices.append(transaction_index)

        report_data_frames["credit_card_payments"] = transaction_schedule.loc[
            credit_transaction_indices
        ].reset_index(drop=True)
        loan_payment_rows = []
        for transaction_index in loan_transaction_indices:
            transaction = transaction_schedule.loc[transaction_index]
            if transaction_index in policy_loan_transaction_indices:
                loan_payment_rows.append(
                    {
                        "Date": transaction["Date"],
                        "Account": "ALL_LOANS",
                        "Payment Type": "Policy",
                        "Amount": float(transaction["Amount"]),
                    }
                )
                continue
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
            'Start':[E.start_ts], 'End':[E.end_ts], 'Elapsed':[cls.get_time_elapsed_string(E.start_ts, E.end_ts)]
        }).T
        forecast_metadata['Stat'] = ['Start', 'End', 'Elapsed']
        forecast_metadata = forecast_metadata.rename(columns={forecast_metadata.columns[0]: "Value"}).loc[:, ["Stat", "Value"]]
        
        report_data_frames['forecast_metadata'] = forecast_metadata

        last_day = E.forecast_df.tail(1).T
        final_row = E.forecast_df.tail(1).copy()
        investment_account_names = [
            account.name
            for account in initial_account_set.accounts
            if account.account_type == "investment"
            and account.name in final_row.columns
        ]
        final_row["Investment Total"] = (
            final_row[investment_account_names].sum(axis=1)
            if investment_account_names
            else 0.0
        )
        account_names = [
            account.name
            for account in initial_account_set.accounts
            if account.name in final_row.columns
        ]
        account_summary_columns = [
            column
            for column in (
                "Liquid Total", "CC Debt Total", "Loan Total",
                "Investment Total", "Net Worth",
            )
            if column in final_row.columns
        ]
        report_data_frames["last_day_account_type_summary"] = final_row.loc[
            :, ["Date", *account_summary_columns]
        ]
        report_data_frames["last_day_accounts"] = final_row.loc[
            :, ["Date", *account_names]
        ]
        final_forecast_row = E.forecast_df.iloc[-1]
        try:
            final_account_set = cls._account_set_from_forecast_row(
                initial_account_set, final_forecast_row
            )
        except KeyError:
            final_account_data = copy.deepcopy(initial_account_set.to_dict())
            for account_row in final_account_data["accounts"]:
                balance = final_forecast_row.get(account_row["Name"], account_row["Balance"])
                account_row["Balance"] = balance
                if account_row["Account_Type"] == "credit":
                    account_row["Current_Statement_Balance"] = 0
                    account_row["Previous_Statement_Balance"] = balance
                    account_row["End_Of_Previous_Cycle_Balance"] = balance
                    account_row["Billing_Cycle_Payment_Balance"] = 0
                elif account_row["Account_Type"] == "loan":
                    account_row["Principal_Balance"] = balance
                    account_row["Interest_Balance"] = 0
                    account_row["Billing_Cycle_Payment_Balance"] = 0
            final_account_set = AccountSet.from_dict(final_account_data)
        final_account_set_data = final_account_set.to_dict()
        final_account_set_data["accounts"] = [
            account
            for account in final_account_set_data["accounts"]
            if not (
                account["Account_Type"] == "loan"
                and abs(float(account["Balance"]))
                <= float(ROUNDING_ERROR_TOLERANCE)
            )
        ]
        final_account_dict_code = pformat(
            final_account_set_data, sort_dicts=False, width=100
        )
        final_account_dict_code = re.sub(
            r"(?<![\w'])inf(?![\w'])", "float('inf')", final_account_dict_code
        )
        final_account_set_code = (
            "AccountSet.from_dict(" + final_account_dict_code + ")"
        )
        summary_rows = [
            row
            for row in last_day.index
            if not (
                row.startswith("Date")
                or row.startswith("Memo")
                or row.startswith("Memo Directive")
                or row.startswith("Next Income Date")
                or row.startswith("Interest Accrued")
                or row.startswith("Investment Returns")
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
            empty_message: str = "No data available.",
        ) -> str:
            """
            Render one titled table card.
            """
            additional_class = f" {section_class}" if section_class else ""

            return f"""
                <section class="table-card{additional_class}">
                    <h2 class="table-card-title">{escape(title)}</h2>
                    <div class="table-scroll-container">
                        {render_table(dataframe_name, empty_message=empty_message)}
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
                    "all",
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
                elif page_id == "sankey":
                    line_chart_html = """
                        <div class="sankey-view-toggle" role="tablist" aria-label="Sankey grouping">
                            <button class="sankey-toggle-button is-active" type="button" data-sankey-mode="transaction">Transaction</button>
                            <button class="sankey-toggle-button" type="button" data-sankey-mode="account">Account</button>
                        </div>
                        <div class="detail-line-chart-container sankey-chart-container">
                            <svg id="sankey-chart" class="hero-chart detail-line-chart" role="img" aria-label="Income flow Sankey diagram"></svg>
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

            return f"""<section
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
                    <div class="detail-page-text detail-page-text-above">{scalar_value(f"{page_id}_page_text_above_plots")}</div>
                    {plot_html}
                    <div class="detail-page-text detail-page-text-below">{scalar_value(f"{page_id}_page_text_below_plots")}</div>
                    {primary_table_html}
                    <div class="detailed-additional-sections">
                        {additional_sections}
                    </div>
                </section>"""

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
            ]
        )

        milestone_sections = "".join(
            [
                render_table_card("Achievement Dates", "milestone_dates"),
                render_table_card("Composite Milestone Definitions", "composite_milestones"),
                render_table_card("Account Milestone Definitions", "account_milestones"),
                render_table_card("Memo Milestone Definitions", "memo_milestones"),
            ]
        )

        last_day_sections = "".join(
            [
                render_table_card(
                    "Account Type Summary",
                    "last_day_account_type_summary",
                    section_class="last-day-table-card last-day-summary-card",
                ),
                render_table_card(
                    "Accounts",
                    "last_day_accounts",
                    section_class="last-day-table-card",
                ),
                (
                    '<section class="table-card last-day-code-card">'
                    '<h2 class="table-card-title">AccountSet Code</h2>'
                    f'<pre><code>{escape(final_account_set_code)}</code></pre>'
                    '</section>'
                ),
            ]
        )

        policy_sections = render_table_card(
            "Safety Decision Audit",
            "policy_safety_decisions",
            empty_message="No optimized policy decisions recorded.",
        ) + "".join(
            render_table_card(
                title,
                dataframe_name,
                empty_message="No policies configured.",
            )
            for _, title, dataframe_name, _ in policy_type_specs
        )

        transaction_schedule_sections = "".join(
            [
                render_table_card(
                    "Income",
                    "income_transactions",
                ),
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
                    "policies",
                    "Policies",
                    additional_sections=policy_sections,
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
                    additional_sections=milestone_sections,
                    show_plot=False,
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
                    additional_sections=last_day_sections,
                    show_plot=False,
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


        line_items_dataframe = E.initial_conditions.initial_line_item_set.getLineItems()
        once_memos = set(
            line_items_dataframe.loc[
                line_items_dataframe["interval"].eq("once"), "Memo"
            ]
        )
        confirmed_transactions = cls()._report_confirmed_df(E)
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

        all_chart_columns = list(dict.fromkeys([
            *account_names,
            "Net Worth",
            *account_summary_columns,
        ]))
        all_chart_columns = [
            column for column in all_chart_columns
            if column != "Date" and column in E.forecast_df.columns
        ]

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
                "series_data": dataframe_to_chart_records(pd.DataFrame({
                    "Date": E.forecast_df["Date"],
                    "Investment Returns": E.forecast_df["Investment Returns"],
                    "Interest Accrued": -E.forecast_df["Interest Accrued"].abs(),
                })),
                "options": {
                    "symmetric_zero": True,
                    "absolute_tooltip_series": ["Interest Accrued"],
                    "line_styles": {
                        "Investment Returns": {"color": "#268a51"},
                        "Interest Accrued": {"color": "#c94747"},
                    },
                },
            },
            "all": {
                "series_data": dataframe_to_chart_records(
                    E.forecast_df.loc[:, ["Date", *all_chart_columns]]
                ),
                "options": {},
            },
        }
        detail_chart_json = json.dumps(
            detail_chart_payload,
            ensure_ascii=False,
            default=str,
        ).replace("</", "<\\/")

        def sankey_payload(group_by_account=False):
            primary_checking_name = initial_account_set.primary_checking_account_name
            if group_by_account:
                account_types_by_name = {
                    account.name: account.account_type
                    for account in initial_account_set.accounts
                }
                edge_totals = {}
                confirmed_debt_totals = {}

                def clean_endpoint(value):
                    if value is None or (not isinstance(value, str) and pd.isna(value)):
                        return None
                    value = str(value).strip()
                    if value.startswith("SAVINGS_BELOW:"):
                        value = value.split(":", 2)[2]
                    return None if value in {"", "None", "nan"} else value

                def policy_endpoints(memo):
                    policy = next(
                        (
                            candidate
                            for candidate in configured_policies
                            if memo.startswith(f"POLICY {candidate.policy_key} ")
                        ),
                        None,
                    )
                    if policy is None:
                        return None, None
                    account_to = getattr(policy, "account_name", None)
                    if account_to is None and isinstance(policy, SurplusDebtPaymentPolicy):
                        account_to = (
                            "ALL_CREDIT" if policy.debt_type == "credit" else "ALL_LOANS"
                        )
                    return primary_checking_name, account_to

                def add_edge(account_from, account_to, amount):
                    amount = float(amount)
                    if amount <= float(ROUNDING_ERROR_TOLERANCE):
                        return
                    source = clean_endpoint(account_from) or "Income"
                    target = clean_endpoint(account_to) or "Spend"
                    if source == target:
                        return
                    key = (source, target)
                    edge_totals[key] = edge_totals.get(key, 0.0) + amount

                for _, transaction in transaction_schedule.iterrows():
                    amount = abs(float(transaction.get("Amount", 0) or 0))
                    if amount <= float(ROUNDING_ERROR_TOLERANCE):
                        continue
                    memo = str(transaction.get("Memo", ""))
                    if memo.startswith("POLICY surplus_saving:"):
                        continue
                    endpoint_columns_present = (
                        "Account_From" in transaction.index
                        and "Account_To" in transaction.index
                    )
                    if endpoint_columns_present:
                        account_from = clean_endpoint(transaction.get("Account_From"))
                        account_to = clean_endpoint(transaction.get("Account_To"))
                    else:
                        account_from = account_to = None
                        try:
                            rule = initial_memo_rule_set.findMatchingMemoRule(
                                memo,
                                transaction.get("Priority", 1),
                            )
                            account_from, account_to = rule.account_from, rule.account_to
                        except ValueError:
                            account_from, account_to = policy_endpoints(memo)
                            if account_from is None and bool(
                                transaction.get("Income_Flag", False)
                            ):
                                account_to = primary_checking_name

                    account_from = clean_endpoint(account_from)
                    account_to = clean_endpoint(account_to)
                    if account_to is not None and account_to.startswith("ALL_"):
                        continue
                    add_edge(account_from, account_to, amount)
                    if account_types_by_name.get(account_to) in {"credit", "loan"}:
                        confirmed_debt_totals[account_to] = (
                            confirmed_debt_totals.get(account_to, 0.0) + amount
                        )

                for policy in configured_policies:
                    if not isinstance(policy, SurplusSavingPolicy):
                        continue
                    executed = float(
                        policy_results.get(policy.policy_key, {}).get("executed", 0)
                    )
                    add_edge(primary_checking_name, policy.account_name, executed)

                minimum_totals = {}
                additional_totals = {}
                debt_names = {
                    name
                    for name, account_type in account_types_by_name.items()
                    if account_type in {"credit", "loan"}
                }

                def directive_debt_name(endpoint_text):
                    endpoint_parts = [
                        part.strip() for part in str(endpoint_text).split(":")
                    ]
                    return next(
                        (part for part in endpoint_parts if part in debt_names),
                        None,
                    )

                for _, forecast_row in E.forecast_df.iterrows():
                    row_date = cls._normalize_date_value(forecast_row["Date"])
                    directives = str(forecast_row.get("Memo Directives", "")).split(";")
                    for directive in (item.strip() for item in directives):
                        match = re.match(
                            r"^(CC|LOAN) MIN PAYMENT \(([^()]+?) -\$([0-9.]+)\)$",
                            directive,
                        )
                        if match:
                            account_name = directive_debt_name(match.group(2))
                            if account_name is not None:
                                key = (row_date, account_name)
                                minimum_totals[key] = (
                                    minimum_totals.get(key, 0.0) + float(match.group(3))
                                )
                            continue

                        match = re.match(
                            r"^MINIMUM PAYMENT \(([^()]+) \+\$([0-9.]+)\)$",
                            directive,
                        )
                        if match and match.group(1).strip() in debt_names:
                            key = (row_date, match.group(1).strip())
                            minimum_totals[key] = (
                                minimum_totals.get(key, 0.0) + float(match.group(2))
                            )
                            continue

                        match = re.match(
                            r"^ADDTL (?:CC|LOAN) PAYMENT \(([^()]+?) -\$([0-9.]+)\)$",
                            directive,
                        )
                        account_name = (
                            directive_debt_name(match.group(1)) if match else None
                        )
                        if account_name is not None:
                            additional_totals[account_name] = (
                                additional_totals.get(account_name, 0.0)
                                + float(match.group(2))
                            )

                for (_, account_name), amount in minimum_totals.items():
                    add_edge(primary_checking_name, account_name, amount)
                for account_name, amount in additional_totals.items():
                    uncovered_amount = max(
                        0.0, amount - confirmed_debt_totals.get(account_name, 0.0)
                    )
                    add_edge(primary_checking_name, account_name, uncovered_amount)

                final_checking_balance = float(
                    E.forecast_df.iloc[-1][primary_checking_name]
                )
                add_edge(
                    primary_checking_name,
                    "Not Spent",
                    max(0.0, final_checking_balance),
                )

                source_totals = {}
                destination_totals = {}
                for (source, target), amount in edge_totals.items():
                    source_totals[source] = source_totals.get(source, 0.0) + amount
                    destination_totals[target] = (
                        destination_totals.get(target, 0.0) + amount
                    )
                return {
                    "left": [
                        {"name": name, "value": amount}
                        for name, amount in sorted(
                            source_totals.items(),
                            key=lambda item: item[1],
                            reverse=True,
                        )
                    ],
                    "right": [
                        {"name": name, "value": amount}
                        for name, amount in sorted(
                            destination_totals.items(),
                            key=lambda item: item[1],
                            reverse=True,
                        )
                    ],
                    "links": [
                        {"source": source, "target": target, "value": amount}
                        for (source, target), amount in edge_totals.items()
                    ],
                }

            income_totals = {}
            destination_totals = {}
            seen_surplus_saving_policies = set()

            def transaction_bin(memo):
                if not memo.startswith("POLICY "):
                    return memo
                policy_key = memo.split(" ", 2)[1].split(":", 1)[0]
                return "Policy: " + format_policy_label(policy_key)

            for _, transaction in transaction_schedule.iterrows():
                amount = abs(float(transaction.get("Amount", 0) or 0))
                if amount <= 0:
                    continue
                memo = str(transaction.get("Memo", "Transaction"))
                if memo.startswith("POLICY surplus_saving:"):
                    policy_key = memo.split(" ", 2)[1]
                    if policy_key in seen_surplus_saving_policies:
                        continue
                    seen_surplus_saving_policies.add(policy_key)
                    amount = float(
                        policy_results.get(policy_key, {}).get("executed", 0)
                    )
                    if amount <= float(ROUNDING_ERROR_TOLERANCE):
                        continue
                is_income = bool(transaction.get("Income_Flag", False))
                if is_income:
                    income_totals[memo] = income_totals.get(memo, 0) + amount
                    continue

                destination = transaction_bin(memo)
                destination_totals[destination] = (
                    destination_totals.get(destination, 0) + amount
                )

            total_income = sum(income_totals.values())
            total_destination = sum(destination_totals.values())
            allocated = min(total_income, total_destination)
            links = []
            if total_income and total_destination:
                for source, source_amount in income_totals.items():
                    for target, target_amount in destination_totals.items():
                        links.append({
                            "source": source,
                            "target": target,
                            "value": allocated * source_amount / total_income
                            * target_amount / total_destination,
                        })
            if total_income > allocated:
                destination_totals["Unallocated Income"] = total_income - allocated
                for source, source_amount in income_totals.items():
                    links.append({
                        "source": source,
                        "target": "Unallocated Income",
                        "value": (total_income - allocated) * source_amount / total_income,
                    })
            return {
                "left": [{"name": key, "value": value} for key, value in income_totals.items()],
                "right": [{"name": key, "value": value} for key, value in destination_totals.items()],
                "links": links,
            }

        sankey_json = json.dumps(
            {
                "transaction": sankey_payload(False),
                "account": sankey_payload(True),
            },
            ensure_ascii=False,
            default=str,
        ).replace("</", "<\\/")

        comparison_return_markup = (
            """
            <button
                type="button"
                class="comparison-return-link"
                onclick="window.parent.postMessage(
                    {type: 'expense-forecast:return-comparison'}, '*'
                )"
            >
                <em>This report was generated as part of a comparison.
                Click here to view.</em>
            </button>
            """
            if comparison_return
            else ""
        )

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

                /*
                The identity metadata stays in the narrow left header column,
                but the primary forecast name may use the full report content
                width. It therefore wraps only when it reaches the page's
                right content edge instead of the first grid-column boundary.
                */
                .scenario-identity-left .scenario-name {{
                    width: min(
                        var(--report-page-max-width),
                        calc(100vw - 2 * var(--report-page-side-padding))
                    );
                    max-width: none;
                    white-space: normal;
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

                .comparison-return-link {{
                    display: block;
                    margin: 8px 0 0;
                    padding: 0;
                    border: 0;
                    background: transparent;
                    color: var(--report-accent-color);
                    font-size: var(--report-date-range-font-size);
                    line-height: 1.35;
                    text-align: left;
                    cursor: pointer;
                }}

                .comparison-return-link:hover {{
                    text-decoration: underline;
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
                    white-space: pre-line;
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

                .last-day-table-card .report-table th,
                .last-day-table-card .report-table td {{
                    text-align: center;
                }}

                .last-day-summary-card .report-table {{
                    table-layout: auto;
                    min-width: max-content;
                    font-size: 1.72rem;
                }}

                .last-day-summary-card .report-table thead th {{
                    font-size: 1.48rem;
                }}

                .last-day-code-card pre {{
                    overflow-x: auto;
                    margin: 16px 0 0;
                    padding: 18px;
                    border: 1px solid var(--report-soft-border-color);
                    border-radius: 8px;
                    background: var(--report-page-background);
                    font-family: var(--report-monospace-font-family);
                    line-height: 1.5;
                }}

                .sankey-view-toggle {{
                    display: flex;
                    justify-content: center;
                    gap: 8px;
                    margin-bottom: 18px;
                }}

                .sankey-toggle-button {{
                    padding: 8px 18px;
                    border: 1px solid var(--report-border-color);
                    border-radius: 999px;
                    background: transparent;
                    cursor: pointer;
                }}

                .sankey-toggle-button.is-active {{
                    border-color: var(--report-accent-color);
                    background: var(--report-accent-color);
                    color: var(--report-accent-text-color);
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

                        {comparison_return_markup}
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
                            "Policies",
                            "policies",
                            empty_message="No policies configured.",
                        )}

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
                                id="detail-tab-policies"
                                class="detail-nav-button"
                                type="button"
                                role="tab"
                                aria-selected="false"
                                aria-controls="detail-page-policies"
                                data-detail-target="policies"
                            >
                                Policies
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
                                Interest &amp; Investment Returns
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
            <script id="sankey-data" type="application/json">{sankey_json}</script>
            <script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
            <script>
                (() => {{
                    const payload = JSON.parse(
                        document.getElementById("sankey-data")?.textContent || "{{}}"
                    );
                    const svg = d3.select("#sankey-chart");
                    const buttons = document.querySelectorAll("[data-sankey-mode]");

                    function renderSankey(mode) {{
                        const data = payload[mode] || {{left: [], right: [], links: []}};
                        const width = 1200;
                        const height = 600;
                        const nodeWidth = 340;
                        const leftX = 30;
                        const rightX = width - nodeWidth - 30;
                        const usableHeight = height - 60;
                        svg.selectAll("*").remove();
                        svg.attr("viewBox", `0 0 ${{width}} ${{height}}`);

                        if (!data.left.length || !data.right.length) {{
                            svg.append("text").attr("x", width / 2).attr("y", height / 2)
                                .attr("text-anchor", "middle").attr("fill", "#77777d")
                                .text("No income flow data available.");
                            return;
                        }}

                        function position(nodes, x) {{
                            const total = d3.sum(nodes, (node) => node.value) || 1;
                            const gap = 12;
                            const available = usableHeight - gap * Math.max(0, nodes.length - 1);
                            let y = 30;
                            return new Map(nodes.map((node) => {{
                                const nodeHeight = Math.max(48, available * node.value / total);
                                const positioned = {{...node, x, y, height: nodeHeight}};
                                y += nodeHeight + gap;
                                return [node.name, positioned];
                            }}));
                        }}

                        const left = position(data.left, leftX);
                        const right = position(
                            [...data.right].sort((a, b) => b.value - a.value),
                            rightX
                        );
                        const maxFlow = d3.max(data.links, (link) => link.value) || 1;
                        const flowWidth = d3.scaleLinear().domain([0, maxFlow]).range([1, 34]);
                        const linkLayer = svg.append("g").attr("fill", "none");
                        data.links.forEach((link) => {{
                            const source = left.get(link.source);
                            const target = right.get(link.target);
                            if (!source || !target) return;
                            const x1 = source.x + nodeWidth;
                            const x2 = target.x;
                            const y1 = source.y + source.height / 2;
                            const y2 = target.y + target.height / 2;
                            linkLayer.append("path")
                                .attr("d", `M${{x1}},${{y1}} C${{width / 2}},${{y1}} ${{width / 2}},${{y2}} ${{x2}},${{y2}}`)
                                .attr("stroke", "#7097aa").attr("stroke-opacity", 0.35)
                                .attr("stroke-width", flowWidth(link.value));
                        }});

                        function drawNodes(nodes, color) {{
                            const groups = svg.append("g").selectAll("g")
                                .data([...nodes.values()]).join("g");
                            groups.append("rect").attr("x", (node) => node.x)
                                .attr("y", (node) => node.y).attr("width", nodeWidth)
                                .attr("height", (node) => node.height).attr("rx", 5)
                                .attr("fill", color);
                            groups.append("foreignObject")
                                .attr("x", (node) => node.x + 10)
                                .attr("y", (node) => node.y + 5)
                                .attr("width", nodeWidth - 20)
                                .attr("height", (node) => Math.max(38, node.height - 10))
                                .append("xhtml:div")
                                .style("color", "white")
                                .style("font-size", "12px")
                                .style("line-height", "1.25")
                                .style("overflow-wrap", "anywhere")
                                .text((node) => `${{node.name}} ($${{d3.format(",.2f")(node.value)}})`);
                        }}
                        drawNodes(left, "#2f7d4a");
                        drawNodes(right, "#315c72");
                    }}

                    buttons.forEach((button) => button.addEventListener("click", () => {{
                        buttons.forEach((candidate) => candidate.classList.toggle(
                            "is-active", candidate === button
                        ));
                        renderSankey(button.dataset.sankeyMode);
                    }}));
                    renderSankey("transaction");
                }})();
            </script>
            <script src="./hero_chart.js"></script>
            <script src="./detail_charts.js"></script>
        </body>
        </html>
        """

        if not write_file:
            cls._phase_log(
                "green",
                "Report generation completed: "
                f"id={E.unique_id} destination=memory "
                f"elapsed={perf_counter() - report_started_at:.2f}s",
            )
            return html

        if output_path is None:
            target_path = Path(f"Forecast_{E.unique_id}.html")
        else:
            target_path = Path(output_path)
            if target_path.suffix.lower() not in {".html", ".htm"}:
                target_path = target_path / f"Forecast_{E.unique_id}.html"
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(html)
        cls._phase_log(
            "green",
            "Report generation completed: "
            f"id={E.unique_id} destination={target_path} "
            f"elapsed={perf_counter() - report_started_at:.2f}s",
        )
        return str(target_path)

    # def show_plan(self, forecast_set: ForecastSetInitialConditions):
    #     raise NotImplementedError

    @staticmethod
    def _flatten_milestone_results(milestone_results):
        if milestone_results is None:
            return {}
        if isinstance(milestone_results, dict):
            return dict(milestone_results)
        flattened = {}
        for result_group in milestone_results:
            if result_group:
                flattened.update(result_group)
        return flattened

    @classmethod
    def _account_set_from_forecast_row(cls, account_set, forecast_row):
        account_set = copy.deepcopy(account_set)
        for account in account_set.accounts:
            if account.name in forecast_row.index:
                account.balance = AccountSet._money(forecast_row[account.name])
            policy_minimum_name = f"{account.name}: Policy Min Balance"
            if policy_minimum_name in forecast_row.index:
                account.policy_min_balance = AccountSet._money(
                    forecast_row[policy_minimum_name]
                )
            if account.account_type in {"checking", "investment"}:
                account.billing_state.balance = account.balance
            elif account.account_type == "credit":
                state = account.billing_state
                state.current_statement_balance = AccountSet._money(
                    forecast_row[f"{account.name}: Curr Stmt Bal"]
                )
                state.previous_statement_balance = AccountSet._money(
                    forecast_row[f"{account.name}: Prev Stmt Bal"]
                )
                state.billing_cycle_payment_balance = AccountSet._money(
                    forecast_row[f"{account.name}: Credit Billing Cycle Payment Bal"]
                )
                state.end_of_previous_cycle_balance = AccountSet._money(
                    forecast_row[f"{account.name}: Credit End of Prev Cycle Bal"]
                )
                AccountSet._sync_debt_account_from_billing_state(account)
            elif account.account_type == "loan":
                state = account.billing_state
                state.principal_balance = AccountSet._money(
                    forecast_row[f"{account.name}: Principal Balance"]
                )
                state.interest_balance = AccountSet._money(
                    forecast_row[f"{account.name}: Interest"]
                )
                state.billing_cycle_payment_balance = AccountSet._money(
                    forecast_row[f"{account.name}: Loan Billing Cycle Payment Bal"]
                )
                AccountSet._sync_debt_account_from_billing_state(account)
        return account_set

    @classmethod
    def _materialize_cash_allocation_policies(cls, IO, approximate=False):
        """Translate executable policies into ordinary prioritized transactions."""
        policies = copy.deepcopy(IO.policy_set)
        budget = copy.deepcopy(IO.initial_line_item_set)
        rules = copy.deepcopy(IO.initial_memo_rule_set)
        schedule = IO.initial_line_item_set.getLineItemSchedule()
        primary_checking = next(
            (
                account for account in IO.initial_account_set.accounts
                if account.account_type == "checking" and account.primary_checking_ind
            ),
            None,
        )
        if primary_checking is None:
            return IO

        generated = False
        surplus_occurrence_dates = (
            cls._approximate_output_dates(IO.start_date, IO.end_date)[1:]
            if approximate
            else generate_date_sequence(
                IO.start_date, (IO.end_date - IO.start_date).days, "daily"
            )
        )
        generated_contributions = []
        caps = [
            policy for policy in policies.policies
            if isinstance(policy, PeriodicInvestmentContributionCapPolicy)
        ]

        def period_key(day, period):
            return (day.year, day.month) if period == "month" else (day.year,)

        explicit_contributions = []
        if not schedule.empty:
            for _, row in schedule.iterrows():
                try:
                    rule = rules.findMatchingMemoRule(row["Memo"], row["Priority"])
                except Exception:
                    continue
                target = rule.account_to
                account = next(
                    (a for a in IO.initial_account_set.accounts if a.name == target),
                    None,
                )
                if (
                    account is not None and account.account_type == "investment"
                    and rule.account_from == primary_checking.name
                ):
                    explicit_contributions.append(
                        (cls._normalize_date_value(row["Date"]), int(row["Priority"]),
                         target, float(row["Amount"]))
                    )

        def add_once(policy, day, amount, account_from, account_to, suffix):
            nonlocal generated
            requested = float(amount)
            policy._requested = getattr(policy, "_requested", 0.0) + requested
            capped = 0.0
            applicable_caps = [
                cap for cap in caps
                if cap.account_name == account_to and cap.priority < policy.priority
            ]
            if applicable_caps:
                allowances = []
                for cap in applicable_caps:
                    key = period_key(day, cap.period)
                    used = sum(
                        value for contribution_day, contribution_priority, target, value
                        in explicit_contributions
                        if target == account_to and contribution_priority < policy.priority
                        and period_key(contribution_day, cap.period) == key
                    ) + sum(
                        value for contribution_day, contribution_priority, target, value
                        in generated_contributions
                        if target == account_to and contribution_priority < policy.priority
                        and period_key(contribution_day, cap.period) == key
                    )
                    allowances.append(max(0.0, float(cap.limit) - used))
                amount = min(requested, min(allowances))
                capped = requested - amount
                policy._capped = getattr(policy, "_capped", 0.0) + capped
            if float(amount) <= 0:
                return
            memo = f"POLICY {policy.policy_key} {suffix} {day.isoformat()}"
            budget.addLineItem(
                start_date=day,
                end_date=day,
                priority=policy.priority,
                interval="once",
                amount=float(amount),
                memo=memo,
                income_flag=False,
                deferrable=False,
                # Priority-one LineItems are rigid in the legacy engine.
                # Policy endpoints perform their own feasible-amount capping.
                partial_payment_allowed=policy.priority != 1,
            )
            rules.addMemoRule(memo, account_from, account_to, policy.priority)
            if account_to and any(
                account.name == account_to and account.account_type == "investment"
                for account in IO.initial_account_set.accounts
            ):
                generated_contributions.append(
                    (day, policy.priority, account_to, float(amount))
                )
            generated = True

        for policy in sorted(policies.policies, key=lambda candidate: candidate.priority):
            if isinstance(policy, CurrentStatementBalancePaymentPolicy):
                card = next(
                    account for account in IO.initial_account_set.accounts
                    if account.name == policy.account_name
                )
                first_billing_date = cls._normalize_date_value(
                    card.billing_state.billing_cycle_start_date
                )
                billing_dates = generate_date_sequence(
                    first_billing_date,
                    max(0, (IO.end_date + datetime.timedelta(days=1) - first_billing_date).days),
                    "monthly",
                )
                for billing_date in billing_dates:
                    close_date = cls._normalize_date_value(billing_date) - datetime.timedelta(days=1)
                    if IO.start_date <= close_date <= IO.end_date:
                        add_once(
                            policy,
                            close_date,
                            10**15,
                            primary_checking.name,
                            f"CURRENT_STATEMENT_BALANCE:{policy.account_name}",
                            "current cycle charges",
                        )
            elif isinstance(policy, FixedMonthlyInvestmentPolicy):
                cursor = date(IO.start_date.year, IO.start_date.month, 1)
                while cursor <= IO.end_date:
                    day_number = min(
                        policy.day,
                        calendar.monthrange(cursor.year, cursor.month)[1],
                    )
                    contribution_date = cursor.replace(day=day_number)
                    if IO.start_date <= contribution_date <= IO.end_date:
                        add_once(
                            policy, contribution_date, policy.amount,
                            primary_checking.name, policy.account_name, "fixed",
                        )
                    cursor = (cursor.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
            elif isinstance(policy, IncomePercentageInvestmentPolicy):
                if schedule.empty:
                    continue
                eligible = schedule.loc[
                    schedule["Income_Flag"].astype(bool)
                    & (schedule["Priority"] < policy.priority)
                ].copy()
                if eligible.empty:
                    continue
                eligible["Date"] = eligible["Date"].apply(cls._normalize_date_value)
                for income_date, rows in eligible.groupby("Date"):
                    add_once(
                        policy,
                        income_date,
                        rows["Amount"].sum() * policy.percentage,
                        primary_checking.name,
                        policy.account_name,
                        "percentage contribution",
                    )
            elif isinstance(policy, SurplusInvestmentPolicy):
                for contribution_date in surplus_occurrence_dates:
                    add_once(
                        policy, contribution_date, 10**15,
                        f"CHECKING_ABOVE:{policy.checking_threshold}",
                        policy.account_name, "surplus",
                    )
            elif isinstance(policy, SurplusSavingPolicy):
                destination = (
                    f"SAVINGS_BELOW:{policy.saved_minimum_threshold}:"
                    f"{policy.account_name}"
                )
                for saving_date in surplus_occurrence_dates:
                    add_once(
                        policy,
                        saving_date,
                        10**15,
                        primary_checking.name,
                        destination,
                        "surplus saving",
                    )
            elif isinstance(policy, SurplusDebtPaymentPolicy):
                destination = (
                    "ALL_LOANS" if policy.debt_type == "loan"
                    else "ALL_CREDIT_CARDS"
                )
                if policy.strategy == "snowball":
                    destination += "_SNOWBALL"
                for payment_date in surplus_occurrence_dates:
                    add_once(
                        policy, payment_date, 10**15,
                        primary_checking.name, destination, "surplus",
                    )

        if not generated:
            return IO
        rebuilt = ExpenseForecastInitialConditions(
            start_date=IO.start_date,
            end_date=IO.end_date,
            account_set=IO.initial_account_set,
            line_item_set=budget,
            memo_rule_set=rules,
            milestone_set=IO.milestone_set,
            transition_set=IO.transition_set,
            policy_set=ForecastPolicySet(),
        )
        rebuilt.policy_set = policies
        rebuilt._policy_declaration_order = {
            policy.policy_key: index
            for index, policy in enumerate(policies.policies)
        }
        rebuilt.unique_id = IO.unique_id
        return rebuilt

    @classmethod
    def _summarize_cash_policy_results(cls, policy_set, result):
        if not getattr(result, "safety_decisions", None):
            result.safety_decisions = []
            for frame, executed in (
                (getattr(result, "confirmed_df", None), True),
                (getattr(result, "skipped_df", None), False),
            ):
                if not isinstance(frame, pd.DataFrame) or frame.empty:
                    continue
                for _, row in frame.iterrows():
                    if not str(row.get("Memo", "")).startswith("POLICY "):
                        continue
                    matching_policy = next((
                        policy for policy in policy_set.policies
                        if str(row.get("Memo", "")).startswith(
                            f"POLICY {policy.policy_key} "
                        )
                    ), None)
                    analytical = isinstance(matching_policy, SurplusSavingPolicy)
                    result.safety_decisions.append({
                        "date": row.get("Date"),
                        "memo": row.get("Memo"),
                        "priority": int(row.get("Priority", 0)),
                        "requested": float(row.get("Amount", 0)),
                        "executed": float(row.get("Amount", 0)) if executed else 0.0,
                        "resolution_method": "constraint" if analytical else "recursive",
                        "available_headroom": None,
                        "binding_account": None,
                        "binding_date": None,
                        "fallback_reason": (
                            None if analytical else "nonlinear or unsupported endpoint"
                        ),
                        "binding_constraint": (
                            "future mandatory reserve" if analytical else None
                        ),
                    })
        summaries = {}
        confirmed = result.confirmed_df
        for policy in policy_set.policies:
            if (
                isinstance(policy, CurrentStatementBalancePaymentPolicy)
                and confirmed is not None
                and not confirmed.empty
            ):
                policy_rows = confirmed["Memo"].astype(str).str.startswith(
                    f"POLICY {policy.policy_key} "
                )
                normalized_forecast_dates = result.forecast_df["Date"].apply(
                    cls._normalize_date_value
                )
                for row_index in confirmed.index[policy_rows]:
                    memo = str(confirmed.at[row_index, "Memo"])
                    transaction_date = cls._normalize_date_value(
                        confirmed.at[row_index, "Date"]
                    )
                    forecast_rows = result.forecast_df.loc[
                        normalized_forecast_dates == transaction_date
                    ]
                    if forecast_rows.empty:
                        continue
                    amount_match = re.search(
                        re.escape(memo) + r" \([^)]* -\$([0-9.]+)\)",
                        str(forecast_rows.iloc[0]["Memo"]),
                    )
                    if amount_match:
                        confirmed.at[row_index, "Amount"] = float(
                            amount_match.group(1)
                        )
            summary = {
                "priority": policy.priority,
                "status": "completed",
                "requested": 0.0,
                "executed": 0.0,
                "capped": 0.0,
                "missed": 0,
                "debt_paid": 0.0,
            }
            summary["requested"] = float(getattr(policy, "_requested", 0.0))
            summary["capped"] = float(getattr(policy, "_capped", 0.0))
            if confirmed is not None and not confirmed.empty:
                matches = confirmed["Memo"].astype(str).str.startswith(
                    f"POLICY {policy.policy_key} "
                )
                executed = pd.to_numeric(
                    confirmed.loc[matches, "Amount"], errors="coerce"
                ).sum()
                summary["executed"] = float(executed)
                if isinstance(policy, SurplusDebtPaymentPolicy):
                    summary["debt_paid"] = float(executed)
            if isinstance(policy, CurrentStatementBalancePaymentPolicy):
                # The requested amount is resolved dynamically from billing
                # state, so materialization's sentinel is not meaningful.
                summary["requested"] = summary["executed"]
            if isinstance(policy, SurplusInvestmentPolicy):
                # Materialization uses a large internal request so the
                # transaction resolver can discover available headroom. The
                # public request is the amount that was actually available,
                # not that sentinel. Also render the real source account in
                # the memo instead of the internal threshold endpoint.
                summary["requested"] = (
                    summary["executed"] + summary["capped"]
                )
                source_token = f"CHECKING_ABOVE:{policy.checking_threshold}"
                source_name = (
                    result.initial_conditions.initial_account_set
                    .primary_checking_account_name
                )
                if "Memo" in result.forecast_df.columns:
                    result.forecast_df["Memo"] = (
                        result.forecast_df["Memo"].astype(str).str.replace(
                            source_token, source_name, regex=False
                        )
                    )
            if isinstance(policy, SurplusSavingPolicy):
                initial_account = next(
                    account
                    for account in result.initial_conditions.initial_account_set.accounts
                    if account.name == policy.account_name
                )
                initial_balance = float(initial_account.balance)
                final_balance = float(result.forecast_df.iloc[-1][policy.account_name])
                target = float(policy.saved_minimum_threshold)
                summary["requested"] = max(0.0, target - initial_balance)
                summary["executed"] = max(0.0, final_balance - initial_balance)
                summary["shortfall"] = max(0.0, target - final_balance)
                if summary["shortfall"] > float(ROUNDING_ERROR_TOLERANCE):
                    summary["status"] = "unmet"
                    summary["missed"] = 1
                    message = (
                        f"Policy {policy.policy_key} was short by "
                        f"${summary['shortfall']:.2f}"
                    )
                    if policy.on_unmet == "fail":
                        raise ForecastPolicyError(message)
                    logger.warning(message)
            expected = max(0.0, summary["requested"] - summary["capped"])
            if isinstance(
                policy, (FixedMonthlyInvestmentPolicy, IncomePercentageInvestmentPolicy)
            ) and summary["executed"] + float(ROUNDING_ERROR_TOLERANCE) < expected:
                shortfall = expected - summary["executed"]
                summary["status"] = "unmet"
                summary["missed"] = 1
                message = (
                    f"Policy {policy.policy_key} was short by ${shortfall:.2f}"
                )
                if policy.on_unmet == "fail":
                    raise ForecastPolicyError(message)
                logger.warning(message)
            elif summary["capped"] > 0:
                summary["status"] = "capped"
            summaries[policy.policy_key] = summary
        return summaries

    @classmethod
    def _runForecastWithPolicies(
        cls, IO, milestone_set, include_debug_columns=False, approximate=False
    ):
        """Apply configured forecast policies without changing public runners."""
        configured_IO = copy.deepcopy(IO)

        def preserve_configured_sets(result):
            """Keep generated policy transactions out of resolved configuration."""
            result.resolved_account_set = copy.deepcopy(
                configured_IO.initial_account_set
            )
            result.resolved_memo_rule_set = copy.deepcopy(
                configured_IO.initial_memo_rule_set
            )
            result.resolved_policy_set = copy.deepcopy(configured_IO.policy_set)
            return result

        IO = cls._materialize_cash_allocation_policies(
            copy.deepcopy(IO), approximate=approximate
        )
        reserve_policies = [
            candidate
            for candidate in IO.policy_set.policies
            if isinstance(candidate, MinimumCheckingBalancePolicy)
        ]

        if not reserve_policies:
            policy_set = copy.deepcopy(IO.policy_set)
            result = run_io = copy.deepcopy(IO)
            run_io.policy_set = ForecastPolicySet()
            runner = cls.runForecastApproximate if approximate else cls.runForecast
            result = runner(
                run_io, milestone_set, include_debug_columns=include_debug_columns
            )
            result.initial_conditions = configured_IO
            result.policy_results = cls._summarize_cash_policy_results(
                policy_set, result
            )
            return preserve_configured_sets(result)

        original_IO = configured_IO
        policy = min(reserve_policies, key=lambda candidate: candidate.priority)

        def resolve_reserve_account(candidate):
            if candidate.account_name is not None:
                return next(
                    account for account in IO.initial_account_set.accounts
                    if account.name == candidate.account_name
                )
            primary_accounts = [
                account for account in IO.initial_account_set.accounts
                if account.account_type == "checking" and account.primary_checking_ind
            ]
            if len(primary_accounts) != 1:
                raise ValueError(
                    "MinimumCheckingBalancePolicy requires exactly one primary "
                    "checking account when account_name is not provided"
                )
            return primary_accounts[0]

        reserve_entries = [
            (candidate, resolve_reserve_account(candidate))
            for candidate in reserve_policies
        ]

        def run_without_policy(io, use_approximate, progress_phase):
            io.policy_set = ForecastPolicySet()
            io._suppress_log_guide = True
            io._progress_phase = progress_phase
            runner = cls.runForecastApproximate if use_approximate else cls.runForecast
            return runner(
                io,
                milestone_set,
                include_debug_columns=True,
            )

        if all(
            account.min_balance >= float(candidate.target)
            for candidate, account in reserve_entries
        ):
            result = run_without_policy(
                copy.deepcopy(IO), approximate, "Reserve-enforced execution"
            )
            result.initial_conditions = original_IO
            result.unique_id = original_IO.unique_id + ("_A" if approximate else "")
            result.policy_results = cls._summarize_cash_policy_results(
                IO.policy_set, result
            )
            result.policy_results.update({candidate.policy_key: {
                    "status": "already_enforced",
                    "account_name": account.name,
                    "target": candidate.target,
                    "activation_date": IO.start_date,
                } for candidate, account in reserve_entries})
            return preserve_configured_sets(result)

        def priority_one_io(source_io):
            result = copy.deepcopy(source_io)
            result.policy_set = ForecastPolicySet()
            policy_order = getattr(source_io, "_policy_declaration_order", {})
            reserve_order = policy_order.get(policy.policy_key, -1)

            def precedes_reserve(priority, memo):
                if int(priority) < policy.priority:
                    return True
                if int(priority) > policy.priority:
                    return False
                memo = str(memo)
                if not memo.startswith("POLICY "):
                    return True
                candidate_order = next(
                    (
                        order for key, order in policy_order.items()
                        if memo.startswith(f"POLICY {key} ")
                    ),
                    len(policy_order),
                )
                return candidate_order < reserve_order

            if not result.initial_proposed_df.empty:
                result.initial_proposed_df = result.initial_proposed_df.loc[
                    result.initial_proposed_df.apply(
                        lambda row: precedes_reserve(
                            row["Priority"], row["Memo"]
                        ),
                        axis=1,
                    )
                ].copy()
            result.initial_deferred_df = result.initial_deferred_df.head(0).copy()
            result.initial_skipped_df = result.initial_skipped_df.head(0).copy()
            result.initial_line_item_set = LineItemSet(
                [
                    copy.deepcopy(item)
                    for item in source_io.initial_line_item_set.line_items
                    if precedes_reserve(item.priority, item.memo)
                ],
                scenario_selections=source_io.initial_line_item_set.scenario_selections,
                scenario_dimensions={
                    dimension_name: {
                        choice_name: ScenarioChoice(
                            line_item_set=LineItemSet([
                                copy.deepcopy(item)
                                for item in choice.line_items
                                if precedes_reserve(item.priority, item.memo)
                            ]),
                            account_set=choice.account_set,
                            memo_rule_set=choice.memo_rule_set,
                            policy_set=choice.policy_set,
                            transition_set=choice.transition_set,
                        )
                        for choice_name, choice in choices.items()
                    }
                    for dimension_name, choices in source_io.initial_line_item_set.scenario_dimensions.items()
                },
            )
            return result

        discovery_started_at = perf_counter()
        reserve_description = ", ".join(
            f"{account.name}=${float(candidate.target):,.2f} at P{candidate.priority}"
            for candidate, account in reserve_entries
        )
        cls._phase_log(
            "magenta",
            "Reserve policy discovery started: "
            f"mode={'approximate' if approximate else 'exact'} "
            f"reserves=[{reserve_description}] execution_gate=P{policy.priority}."
            + (
                " Discovery uses approximate event/binned granularity."
                if approximate
                else " Transaction messages in this phase are daily and unbinned."
            ),
        )
        exact_discovery = run_without_policy(
            priority_one_io(IO), approximate, "Policy discovery"
        )
        cls._phase_log(
            "green",
            "Reserve policy discovery finished: "
            f"elapsed={perf_counter() - discovery_started_at:.2f}s; "
            "evaluating the stable balance crossing.",
        )
        discovery_dates = exact_discovery.forecast_df["Date"].apply(
            cls._normalize_date_value
        )
        qualifying_mask = pd.Series(True, index=exact_discovery.forecast_df.index)
        individual_qualifying_masks = {}
        for candidate, account in reserve_entries:
            balances = pd.to_numeric(
                exact_discovery.forecast_df[account.name], errors="coerce"
            )
            suffix_minimum = balances.iloc[::-1].cummin().iloc[::-1]
            candidate_qualifying = suffix_minimum >= float(candidate.target)
            individual_qualifying_masks[candidate.policy_key] = candidate_qualifying
            qualifying_mask &= candidate_qualifying
        qualifying = exact_discovery.forecast_df.loc[qualifying_mask]

        policy_results = {
            candidate.policy_key: {
                "status": "not_achieved",
                "account_name": account.name,
                "target": candidate.target,
                "activation_date": None,
            }
            for candidate, account in reserve_entries
        }
        proposed = IO.initial_proposed_df.copy()
        if qualifying.empty:
            unattainable_entries = [
                (candidate, account)
                for candidate, account in reserve_entries
                if not individual_qualifying_masks[candidate.policy_key].any()
            ]
            for candidate, account in unattainable_entries:
                logger.warning(
                    "%s never established the requested stable minimum of %s",
                    account.name,
                    float(candidate.target),
                )
                if candidate.on_unmet == "fail":
                    raise ForecastPolicyError(
                        f"Minimum balance policy for {account.name} never "
                        "established its reserve"
                    )
            unattainable_keys = {
                candidate.policy_key for candidate, _ in unattainable_entries
            }
            fallback_IO = copy.deepcopy(original_IO)
            fallback_IO.policy_set = ForecastPolicySet([
                candidate
                for candidate in fallback_IO.policy_set.policies
                if candidate.policy_key not in unattainable_keys
            ])
            fallback_IO._suppress_log_guide = True
            cls._phase_log(
                "yellow",
                "Unattainable warning-only reserve policies will be ignored; "
                "rerunning with the remaining policies: "
                + ", ".join(sorted(unattainable_keys)),
                level="warning",
            )
            fallback_result = cls._runForecastWithPolicies(
                fallback_IO,
                milestone_set,
                include_debug_columns=include_debug_columns,
                approximate=approximate,
            )
            fallback_result.initial_conditions = original_IO
            fallback_result.unique_id = original_IO.unique_id + (
                "_A" if approximate else ""
            )
            fallback_result.policy_results.update({
                key: value
                for key, value in policy_results.items()
                if key in unattainable_keys
            })
            return preserve_configured_sets(fallback_result)

        activation_row = qualifying.iloc[0]
        activation_date = cls._normalize_date_value(activation_row["Date"])
        for policy_result in policy_results.values():
            policy_result.update(status="activated", activation_date=activation_date)
        cls._phase_log(
            "magenta",
            "Reserve policies activated: "
            f"date={activation_date} mode={'approximate' if approximate else 'exact'} "
            f"floors=[{reserve_description}]."
            + (
                " Approximate transaction messages are binned into summary dates."
                if approximate else ""
            ),
        )

        activation_accounts = cls._account_set_from_forecast_row(
            IO.initial_account_set, activation_row
        )
        for candidate, reserve_account in reserve_entries:
            activation_reserve_account = next(
                account
                for account in activation_accounts.accounts
                if account.name == reserve_account.name
            )
            activation_reserve_account.policy_min_balance = float(candidate.target)

        flattened_milestones = cls._flatten_milestone_results(
            exact_discovery.milestone_results
        )
        current_budget = copy.deepcopy(IO.initial_line_item_set)
        remaining_transitions = []
        for transition in IO.transition_set.transitions:
            achieved = flattened_milestones.get(transition.milestone)
            achieved = None if achieved is None else cls._normalize_date_value(achieved)
            if achieved is not None and achieved <= activation_date:
                for dimension_name, choice_name in transition.changes.items():
                    current_budget = current_budget.replace_scenario_choice(
                        dimension_name, choice_name
                    )
            else:
                remaining_transitions.append(copy.deepcopy(transition))

        from expense_forecast.ConditionalScenarioTransitionSet import (
            ConditionalScenarioTransitionSet,
        )

        tail_IO = ExpenseForecastInitialConditions(
            # The optimizer intentionally does not process P2 on its first row
            # because it needs a preceding state for propagation. Seed one
            # internal row and discard it when stitching the public result.
            start_date=activation_date - datetime.timedelta(days=1),
            end_date=IO.end_date,
            account_set=activation_accounts,
            line_item_set=current_budget,
            memo_rule_set=IO.initial_memo_rule_set,
            milestone_set=milestone_set,
            transition_set=ConditionalScenarioTransitionSet(remaining_transitions),
            policy_set=ForecastPolicySet(),
        )
        # Initial-condition normalization rebuilds account objects and keeps
        # only serialized hard boundaries. Reattach active policy floors to
        # the execution accounts so optional policies cannot consume them.
        for candidate, reserve_account in reserve_entries:
            tail_reserve_account = next(
                account for account in tail_IO.initial_account_set.accounts
                if account.name == reserve_account.name
            )
            tail_reserve_account.policy_min_balance = float(candidate.target)
        tail_confirmed_dates = tail_IO.initial_confirmed_df["Date"].apply(
            cls._normalize_date_value
        )
        tail_IO.initial_confirmed_df = tail_IO.initial_confirmed_df.loc[
            tail_confirmed_dates > activation_date
        ].copy()

        proposed_dates = proposed["Date"].apply(cls._normalize_date_value)
        higher_priority = proposed["Priority"] > policy.priority
        earlier = proposed_dates < activation_date
        earlier_deferrable = (
            earlier & higher_priority & proposed["Deferrable"].astype(bool)
        )
        tail_eligible = (
            ((proposed["Priority"] < policy.priority) & (proposed_dates > activation_date))
            | (higher_priority & ~earlier)
            | earlier_deferrable
        )
        tail_proposed = proposed.loc[tail_eligible].copy()
        tail_proposed.loc[earlier_deferrable, "Date"] = activation_date
        tail_IO.initial_proposed_df = tail_proposed
        tail_IO._policy_activation_date = activation_date
        if approximate:
            tail_IO.initial_deferred_df = proposed.loc[earlier_deferrable].copy()
            tail_IO.initial_deferred_df.loc[:, "Date"] = activation_date
        pre_activation_skipped = proposed.loc[
            earlier & higher_priority & ~proposed["Deferrable"].astype(bool)
        ].copy()

        tail_started_at = perf_counter()
        tail_result = run_without_policy(
            tail_IO, approximate, "Post-activation execution"
        )
        cls._phase_log(
            "green",
            "Post-activation forecast finished: "
            f"mode={'approximate' if approximate else 'exact'} "
            f"elapsed={perf_counter() - tail_started_at:.2f}s",
        )
        # Discovery already uses the requested execution mode, so its prefix
        # can be stitched directly without a redundant presentation pass.
        display_discovery = exact_discovery
        summary_columns = {
            "Interest Accrued", "Investment Returns", "Net Gain", "Net Loss", "Net Worth",
            "Loan Total", "CC Debt Total", "Liquid Total", "Investment Total",
        }
        pre_forecast = display_discovery.forecast_df.drop(
            columns=list(summary_columns), errors="ignore"
        )
        pre_forecast = pre_forecast.loc[
            pre_forecast["Date"].apply(cls._normalize_date_value) < activation_date
        ]
        tail_forecast = tail_result.forecast_df.drop(
            columns=list(summary_columns), errors="ignore"
        )
        # The post-activation forecast starts one day early so graph/optimizer
        # propagation has a seed state.  Discard that row when it is outside
        # the requested range or the discovery prefix already owns its date.
        # Approximate discovery can omit that date; in that case it remains a
        # legitimate presentation boundary and must be retained.
        tail_dates = tail_forecast["Date"].apply(cls._normalize_date_value)
        prefix_dates = set(
            pre_forecast["Date"].apply(cls._normalize_date_value)
        )
        tail_forecast = tail_forecast.loc[
            (tail_dates >= IO.start_date)
            & ~(
                (tail_dates < activation_date)
                & tail_dates.isin(prefix_dates)
            )
        ].copy()
        if activation_date > IO.start_date:
            activation_mask = tail_forecast["Date"].apply(
                cls._normalize_date_value
            ) == activation_date
            if activation_mask.any():
                activation_index = tail_forecast.index[activation_mask][0]
                for message_column in ("Memo Directives", "Memo"):
                    discovery_text = str(activation_row.get(message_column, "") or "").strip()
                    tail_text = str(
                        tail_forecast.at[activation_index, message_column] or ""
                    ).strip()
                    tail_forecast.at[activation_index, message_column] = "; ".join(
                        text for text in (discovery_text, tail_text) if text
                    )
        forecast_df = pd.concat([pre_forecast, tail_forecast], ignore_index=True)
        forecast_df = cls._appendSummaryLines(
            original_IO.initial_account_set, forecast_df, log_stack_depth=0
        )
        forecast_df = cls._roundForecastOutput(forecast_df, decimals=2)

        def through(frame, boundary):
            if frame is None or frame.empty:
                return frame
            return frame.loc[
                frame["Date"].apply(cls._normalize_date_value) <= boundary
            ].copy()

        confirmed_parts = [through(exact_discovery.confirmed_df, activation_date)]
        if tail_result.confirmed_df is not None:
            confirmed_parts.append(tail_result.confirmed_df)
        skipped_parts = [pre_activation_skipped]
        if tail_result.skipped_df is not None:
            skipped_parts.append(tail_result.skipped_df)
        result = ExpenseForecastResult(
            original_IO,
            forecast_df,
            exact_discovery.start_ts,
            tail_result.end_ts,
            confirmed_df=pd.concat(confirmed_parts, ignore_index=True),
            deferred_df=tail_result.deferred_df,
            skipped_df=pd.concat(skipped_parts, ignore_index=True),
            milestone_set=milestone_set,
            milestone_results=MilestoneSet.evaluateMilestones(
                forecast_df, milestone_set, log_stack_depth=0
            ),
            approximate_flag=approximate,
            safety_decisions=copy.deepcopy(
                getattr(tail_result, "safety_decisions", [])
            ),
            policy_results={
                **cls._summarize_cash_policy_results(IO.policy_set, tail_result),
                **policy_results,
            },
        )
        if not include_debug_columns:
            debug_columns = set()
            for account in original_IO.initial_account_set.accounts:
                debug_columns.update(
                    set(original_IO.initial_account_set.getForecastColumnsForAccount(account))
                    - {account.name}
                )
            result.forecast_df = result.forecast_df.drop(
                columns=list(debug_columns), errors="ignore"
            )
        return preserve_configured_sets(result)

    @classmethod
    def _runForecastWithScenarioTransitions(
        cls,
        IO,
        milestone_set,
        transitions,
        include_debug_columns=False,
        approximate=False,
    ):
        """Run and stitch forecast segments separated by milestone transitions."""
        transitions.validate(milestone_set, IO.initial_line_item_set)
        original_IO = copy.deepcopy(IO)
        current_IO = copy.deepcopy(IO)
        current_budget = copy.deepcopy(IO.initial_line_item_set)
        resolved_account_set = copy.deepcopy(IO.initial_account_set)
        resolved_memo_rule_set = copy.deepcopy(IO.initial_memo_rule_set)
        resolved_policy_set = copy.deepcopy(IO.policy_set)
        resolved_transition_set = copy.deepcopy(transitions)
        fired_milestones = set()
        forecast_parts = []
        transaction_parts = {name: [] for name in ("confirmed_df", "deferred_df", "skipped_df")}
        boundary_date = None

        summary_columns = {
            "Interest Accrued", "Investment Returns", "Net Gain", "Net Loss", "Net Worth",
            "Loan Total", "CC Debt Total", "Liquid Total", "Investment Total",
        }

        while True:
            runner = (
                cls._runForecastApproximateOnce
                if approximate
                else cls._runForecastOnce
            )
            # Transition boundaries need the full debt billing state even when
            # the caller does not want those columns in the final result.
            segment = runner(current_IO, milestone_set, True)
            milestone_dates = cls._flatten_milestone_results(segment.milestone_results)
            candidates = []
            for declaration_index, transition in enumerate(
                resolved_transition_set.transitions
            ):
                if transition.milestone in fired_milestones:
                    continue
                achieved_date = milestone_dates.get(transition.milestone)
                if achieved_date is None:
                    continue
                achieved_date = cls._normalize_date_value(achieved_date)
                candidates.append((achieved_date, declaration_index, transition))

            segment_forecast = segment.forecast_df.drop(
                columns=[c for c in summary_columns if c in segment.forecast_df.columns],
                errors="ignore",
            ).copy()
            segment_dates = segment_forecast["Date"].apply(cls._normalize_date_value)
            if boundary_date is not None:
                segment_forecast = segment_forecast.loc[segment_dates > boundary_date].copy()
                segment_dates = segment_forecast["Date"].apply(cls._normalize_date_value)

            if not candidates:
                forecast_parts.append(segment_forecast)
                for name in transaction_parts:
                    frame = getattr(segment, name)
                    if frame is not None and not frame.empty:
                        dates = frame["Date"].apply(cls._normalize_date_value)
                        if boundary_date is not None:
                            frame = frame.loc[dates > boundary_date]
                        transaction_parts[name].append(frame.copy())
                break

            next_date = min(candidate[0] for candidate in candidates)
            same_boundary = [
                candidate for candidate in candidates if candidate[0] == next_date
            ]
            same_boundary.sort(key=lambda candidate: candidate[1])
            forecast_parts.append(segment_forecast.loc[segment_dates <= next_date].copy())
            for name in transaction_parts:
                frame = getattr(segment, name)
                if frame is None or frame.empty:
                    continue
                dates = frame["Date"].apply(cls._normalize_date_value)
                lower = dates > boundary_date if boundary_date is not None else True
                transaction_parts[name].append(frame.loc[lower & (dates <= next_date)].copy())

            committed_rows = segment.forecast_df.loc[
                segment.forecast_df["Date"].apply(cls._normalize_date_value) == next_date
            ]
            if committed_rows.empty:
                raise ValueError(
                    f"No forecast row exists for transition boundary {next_date}"
                )

            changed_at_boundary = {}
            for _, _, transition in same_boundary:
                fired_milestones.add(transition.milestone)
                for dimension_name, choice_name in transition.changes.items():
                    previous_write = changed_at_boundary.get(dimension_name)
                    if previous_write is not None and previous_write != choice_name:
                        logger.warning(
                            "Multiple transitions changed ScenarioDimension %r on %s; "
                            "%r was superseded by %r",
                            dimension_name,
                            next_date,
                            previous_write,
                            choice_name,
                        )
                    changed_at_boundary[dimension_name] = choice_name
                current_budget = current_budget.apply_scenario_transition(
                    transition_name=transition.name,
                    trigger_milestone=transition.milestone,
                    trigger_date=next_date,
                    changes=transition.changes,
                    history_start_date=original_IO.start_date,
                )
                for dimension_name, choice_name in transition.changes.items():
                    activated_choice = current_budget.scenario_dimensions[
                        dimension_name
                    ][choice_name]
                    resolved_account_set = overlay_account_sets(
                        resolved_account_set,
                        activated_choice.account_set,
                    )
                    resolved_memo_rule_set = overlay_memo_rule_sets(
                        resolved_memo_rule_set,
                        activated_choice.memo_rule_set,
                    )
                    resolved_policy_set = overlay_policy_sets(
                        resolved_policy_set,
                        activated_choice.policy_set,
                    )
                    previous_transition_names = {
                        candidate.name
                        for candidate in resolved_transition_set.transitions
                    }
                    resolved_transition_set = overlay_transition_sets(
                        resolved_transition_set,
                        activated_choice.transition_set,
                    )
                    newly_activated = [
                        candidate
                        for candidate in resolved_transition_set.transitions
                        if candidate.name not in previous_transition_names
                    ]
                    if newly_activated:
                        ConditionalScenarioTransitionSet(
                            newly_activated
                        ).validate(milestone_set, current_budget)

            if next_date >= current_IO.end_date:
                break
            # The committed trigger row is the seed for every suffix. New
            # choices become effective on the following day, which must be an
            # executable row rather than a second finalized seed.
            next_start = next_date
            next_accounts = cls._account_set_from_forecast_row(
                current_IO.initial_account_set,
                committed_rows.tail(1).iloc[0],
            )
            next_accounts = extend_account_schema(
                next_accounts, resolved_account_set
            )
            io_kwargs = {
                "milestone_set": milestone_set,
                "transition_set": type(transitions)(),
            }
            if getattr(original_IO, "forecast_name", None) is not None:
                io_kwargs["forecast_name"] = original_IO.forecast_name
            if getattr(original_IO, "forecast_set_name", None) is not None:
                io_kwargs["forecast_set_name"] = original_IO.forecast_set_name
            current_IO = ExpenseForecastInitialConditions(
                start_date=next_start,
                end_date=original_IO.end_date,
                account_set=next_accounts,
                line_item_set=current_budget,
                memo_rule_set=resolved_memo_rule_set,
                policy_set=resolved_policy_set,
                **io_kwargs,
            )
            current_IO._exclude_schedule_through = next_date
            for attr in ("initial_confirmed_df", "initial_proposed_df"):
                frame = getattr(current_IO, attr)
                if not frame.empty:
                    setattr(
                        current_IO,
                        attr,
                        frame.loc[
                            frame["Date"].apply(cls._normalize_date_value)
                            > next_date
                        ].copy(),
                    )
            boundary_date = next_date

        forecast_df = pd.concat(forecast_parts, ignore_index=True)
        if forecast_df["Date"].apply(cls._normalize_date_value).duplicated().any():
            raise ValueError("Conditional forecast produced duplicate dates")
        if not include_debug_columns:
            debug_columns = set()
            for account in resolved_account_set.accounts:
                debug_columns.update(
                    set(
                        resolved_account_set
                        .getForecastColumnsForAccount(account)
                    )
                    - {account.name}
                )
            forecast_df = forecast_df.drop(
                columns=[c for c in debug_columns if c in forecast_df.columns],
                errors="ignore",
            )
        for account in resolved_account_set.accounts:
            for column in resolved_account_set.getForecastColumnsForAccount(
                account
            ):
                if column not in forecast_df.columns:
                    forecast_df[column] = 0.0
                else:
                    forecast_df[column] = forecast_df[column].fillna(0.0)
        forecast_df = cls._appendSummaryLines(
            resolved_account_set, forecast_df, log_stack_depth=0
        )
        forecast_df = cls._roundForecastOutput(forecast_df, decimals=2)
        result_frames = {}
        for name, parts in transaction_parts.items():
            result_frames[name] = (
                pd.concat(parts, ignore_index=True)
                if parts
                else pd.DataFrame()
            )
        result = ExpenseForecastResult(
            original_IO,
            forecast_df,
            getattr(cls, "start_ts", datetime.datetime.now()),
            datetime.datetime.now(),
            confirmed_df=result_frames["confirmed_df"],
            deferred_df=result_frames["deferred_df"],
            skipped_df=result_frames["skipped_df"],
            milestone_set=milestone_set,
            milestone_results=MilestoneSet.evaluateMilestones(
                forecast_df, milestone_set, log_stack_depth=0
            ),
            approximate_flag=approximate,
            resolved_line_item_set=current_budget,
            resolved_account_set=resolved_account_set,
            resolved_memo_rule_set=resolved_memo_rule_set,
            resolved_policy_set=resolved_policy_set,
        )
        return result

    #TODO DOC manual review of ForecastHandler.runForecastWithMilestoneConditionalSwaps docstring
    @classmethod
    def runForecastWithMilestoneConditionalSwaps(cls,
                             IO,
                             MS,
                             include_debug_columns=False,
                             log_stack_depth=0):

        logger.warning(
            "runForecastWithMilestoneConditionalSwaps is deprecated; "
            "store ConditionalScenarioTransitionSet on initial conditions and "
            "call runForecast instead"
        )
        return cls.runForecast(IO, MS, include_debug_columns=include_debug_columns)

        # Order of fork options introduces instability, so fork options are processed in order
        """
        #TODO DOC one-line description of ForecastHandler.runForecastWithMilestoneConditionalSwaps.

        #TODO DOC multi-line description of ForecastHandler.runForecastWithMilestoneConditionalSwaps.
        #TODO DOC explain how ForecastHandler.runForecastWithMilestoneConditionalSwaps participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        IO : object
            #TODO DOC one-line description of ForecastHandler.runForecastWithMilestoneConditionalSwaps.IO.

        MS : object
            #TODO DOC one-line description of ForecastHandler.runForecastWithMilestoneConditionalSwaps.MS.

        include_debug_columns : bool
            #TODO DOC one-line description of ForecastHandler.runForecastWithMilestoneConditionalSwaps.include_debug_columns.

        log_stack_depth : int
            #TODO DOC one-line description of ForecastHandler.runForecastWithMilestoneConditionalSwaps.log_stack_depth.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of ForecastHandler.runForecastWithMilestoneConditionalSwaps.

        Contract
        --------
        - #TODO DOC contract lines for ForecastHandler.runForecastWithMilestoneConditionalSwaps.
        - #TODO DOC document exceptions, mutations, and precision assumptions for ForecastHandler.runForecastWithMilestoneConditionalSwaps.

        @interface-report: show
        """
        summary_columns = {
            "Interest Accrued",
            "Investment Returns",
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

        def next_initial_conditions(current_IO, next_start_date, next_account_set, next_line_item_set):
            kwargs = {}
            if getattr(current_IO, "forecast_name", None) is not None:
                kwargs["forecast_name"] = current_IO.forecast_name
            if getattr(current_IO, "forecast_set_name", None) is not None:
                kwargs["forecast_set_name"] = current_IO.forecast_set_name

            return ExpenseForecastInitialConditions(
                start_date=next_start_date,
                end_date=current_IO.end_date,
                account_set=next_account_set,
                line_item_set=next_line_item_set,
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
            next_line_item_set = current_IO.initial_line_item_set - swap_sets[0] + swap_sets[1]
            current_IO = next_initial_conditions(
                current_IO,
                next_start_date,
                next_account_set,
                next_line_item_set,
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
    @classmethod
    def _move_start_date_deferrals_after_seed(cls, IO):
        """Move user-scheduled opening-row deferrals to the first executable day.

        The opening forecast row is a finalized seed state in every engine.
        A deferrable occurrence placed there cannot be attempted consistently,
        so normalize only the runner's private copy to the following day.
        """
        start_date = IO.start_date
        next_date = start_date + datetime.timedelta(days=1)
        affected_items = [
            item
            for item in IO.initial_line_item_set.line_items
            if item.deferrable and item.start_date == start_date
        ]
        if not affected_items:
            return IO

        normalized = copy.deepcopy(IO)
        for item in normalized.initial_line_item_set.line_items:
            if not item.deferrable or item.start_date != start_date:
                continue
            item.start_date = next_date
            if item.interval == "once":
                item.end_date = next_date
            if item.recurrence_anchor == start_date:
                item.recurrence_anchor = next_date

        # Legacy runners consume the preprocessed transaction frames while
        # graph runners expand the LineItemSet. Keep both representations in
        # agreement without changing the caller's initial conditions.
        for frame_name in ("initial_proposed_df", "initial_deferred_df"):
            frame = getattr(normalized, frame_name, None)
            if frame is None or frame.empty:
                continue
            dates = frame["Date"].map(cls._normalize_date_value)
            selection = dates.eq(start_date) & frame["Deferrable"].fillna(
                False
            ).astype(bool)
            frame.loc[selection, "Date"] = next_date

        return normalized

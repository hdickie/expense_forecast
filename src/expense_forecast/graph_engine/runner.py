from __future__ import annotations

import copy
import datetime
import math
from collections import defaultdict
from dataclasses import dataclass, replace
from time import perf_counter

import pandas as pd

from expense_forecast.ExpenseForecastResult import ExpenseForecastResult
from expense_forecast.MilestoneSet import MilestoneSet
from expense_forecast.ForecastPolicySet import ForecastPolicySet
from expense_forecast.MinimumCheckingBalancePolicy import MinimumCheckingBalancePolicy
from expense_forecast.generate_date_sequence import generate_date_sequence

from .errors import UnsupportedGraphBehaviorError
from .graph import ComputationGraph, GraphContext, GraphNode
from .models import ChangeSet, DirtyRange, EvaluationResult, EventKey, VariableKey


SCHEDULE = VariableKey("input", "schedule")
ROUTED = VariableKey("events", "routed")
LEDGER = VariableKey("state", "checking_ledger")
TRANSACTIONS = VariableKey("state", "transaction_results")
RAW_FORECAST = VariableKey("output", "raw_forecast")
FORECAST = VariableKey("output", "forecast")


@dataclass(frozen=True)
class CashEvent:
    key: EventKey
    date: datetime.date
    priority: int
    amount: float
    memo: str
    income_flag: bool
    deferrable: bool
    partial_payment_allowed: bool
    account_from: str | None = None
    account_to: str | None = None

    def transaction_record(self, amount=None, date=None):
        return {
            "Date": date or self.date,
            "Priority": self.priority,
            "Amount": amount if amount is not None else self.amount,
            "Memo": self.memo,
            "Income_Flag": self.income_flag,
            "Deferrable": self.deferrable,
            "Partial_Payment_Allowed": self.partial_payment_allowed,
        }


class ScheduleNode(GraphNode):
    def __init__(self, IO):
        super().__init__("schedule", [VariableKey("config", "line_items")], [SCHEDULE])
        self.IO = IO

    def evaluate(self, context, dirty_range):
        events = []
        occurrence_counts = defaultdict(int)
        for line_item in self.IO.initial_line_item_set.line_items:
            dates = generate_date_sequence(
                line_item.recurrence_anchor,
                (line_item.end_date - line_item.recurrence_anchor).days,
                line_item.interval,
            )
            for event_date in dates:
                if not (
                    self.IO.start_date <= event_date <= self.IO.end_date
                    and line_item.start_date <= event_date <= line_item.end_date
                ):
                    continue
                identity = (
                    f"{line_item.recurrence_key}|{event_date.isoformat()}"
                )
                sequence = occurrence_counts[(event_date, identity)]
                occurrence_counts[(event_date, identity)] += 1
                events.append(CashEvent(
                    EventKey(event_date, identity, sequence),
                    event_date,
                    int(line_item.priority),
                    float(str(line_item.amount)),
                    line_item.memo,
                    bool(line_item.income_flag),
                    bool(line_item.deferrable),
                    bool(line_item.partial_payment_allowed),
                ))
        events.sort(key=lambda item: (
            item.date,
            item.priority,
            1 if str(item.memo).startswith("POLICY ") else 0,
            0 if item.income_flag else 1,
            -item.amount,
            item.memo,
            item.key.sequence,
        ))
        changed = context.write(SCHEDULE, events)
        return EvaluationResult(
            {SCHEDULE} if changed else set(), dirty_range if changed else None,
            events_recomputed=len(events), provenance=["expanded LineItemSet"],
        )


class RoutingNode(GraphNode):
    def __init__(self, memo_rules):
        super().__init__("memo-routing", [SCHEDULE], [ROUTED])
        self.memo_rules = memo_rules

    def evaluate(self, context, dirty_range):
        routed = []
        for event in context.values[SCHEDULE]:
            rule = self.memo_rules.findMatchingMemoRule(event.memo, event.priority)
            routed.append(CashEvent(
                **{
                    **event.__dict__,
                    "account_from": rule.account_from,
                    "account_to": rule.account_to,
                }
            ))
        changed = context.write(ROUTED, routed)
        return EvaluationResult(
            {ROUTED} if changed else set(), dirty_range if changed else None,
            events_recomputed=len(routed), provenance=["resolved MemoRuleSet"],
        )


class CheckingStateNode(GraphNode):
    def __init__(self, IO):
        super().__init__("checking-state", [ROUTED], [LEDGER, TRANSACTIONS])
        self.IO = IO
        self.accounts = {
            account.name: account for account in IO.initial_account_set.accounts
        }

    def _future_reserve(self, events, index, account_name, priority):
        running = float("0")
        maximum = float("0")
        for future in events[index + 1:]:
            if future.priority >= priority:
                continue
            if future.account_from == account_name:
                running += future.amount
            if future.account_to == account_name:
                running -= future.amount
            maximum = max(maximum, running)
        return maximum

    def _capacity(self, balances, event, index, events):
        amount = event.amount
        if event.account_from is not None:
            source = self.accounts[event.account_from]
            reserve = self._future_reserve(
                events, index, event.account_from, event.priority
            ) if event.priority > 1 else float("0")
            amount = min(
                amount,
                balances[event.account_from]
                - float(str(source.min_balance))
                - reserve,
            )
        if event.account_to is not None:
            destination = self.accounts[event.account_to]
            if not math.isinf(float(destination.max_balance)):
                amount = min(
                    amount,
                    float(str(destination.max_balance))
                    - balances[event.account_to],
                )
        return max(float("0"), amount)

    def evaluate(self, context, dirty_range):
        events = list(context.values[ROUTED])
        initial_balances = {
            name: float(str(account.balance)) for name, account in self.accounts.items()
        }
        balances = dict(initial_balances)
        checkpoints = {}
        confirmed, deferred, skipped, executed_events = [], [], [], []
        start_index = 0
        old_ledger = context.values.get(LEDGER)
        old_transactions = context.values.get(TRANSACTIONS)
        if old_ledger is not None:
            prefix = [
                (event, amount) for event, amount in old_ledger["executed"]
                if event.date < dirty_range.start.date
            ]
            if prefix:
                executed_events.extend(prefix)
                last_key = prefix[-1][0].key
                balances = dict(old_ledger["checkpoints"][last_key])
                checkpoints.update({
                    key: value for key, value in old_ledger["checkpoints"].items()
                    if key <= last_key
                })
                start_index = next(
                    (
                        index for index, event in enumerate(events)
                        if event.date >= dirty_range.start.date
                    ),
                    len(events),
                )
                confirmed.extend(
                    event.transaction_record(amount)
                    for event, amount in prefix
                )
                for name, target in (("deferred", deferred), ("skipped", skipped)):
                    target.extend(
                        record for record in old_transactions[name]
                        if record["Date"] < dirty_range.start.date
                    )
        next_income_dates = sorted({
            event.date for event in events if event.income_flag
        })
        queue = list(events)
        index = start_index
        while index < len(queue):
            event = queue[index]
            executable = self._capacity(balances, event, index, queue)
            requested = event.amount
            if executable < requested and event.priority == 1:
                raise ValueError(
                    f"Mandatory graph transaction violates an account boundary: {event.memo!r}"
                )
            if executable < requested and not event.partial_payment_allowed:
                if event.deferrable:
                    next_income = next(
                        (day for day in next_income_dates if day > event.date), None
                    )
                    record = event.transaction_record()
                    if next_income is None:
                        skipped.append(record)
                    else:
                        deferred_event = replace(
                            event,
                            key=EventKey(
                                next_income,
                                event.key.occurrence_id + "|deferred",
                                event.key.sequence,
                            ),
                            date=next_income,
                        )
                        queue.append(deferred_event)
                        queue[index + 1:] = sorted(
                            queue[index + 1:],
                            key=lambda item: (
                                item.date, item.priority,
                                0 if item.income_flag else 1,
                                -item.amount, item.memo,
                            ),
                        )
                else:
                    skipped.append(event.transaction_record())
                index += 1
                continue
            executed = executable if event.partial_payment_allowed else requested
            if executed <= 0:
                skipped.append(event.transaction_record())
                index += 1
                continue
            if event.account_from is not None:
                balances[event.account_from] -= executed
            if event.account_to is not None:
                balances[event.account_to] += executed
            record = event.transaction_record(executed)
            confirmed.append(record)
            executed_events.append((event, executed))
            checkpoints[event.key] = dict(balances)
            index += 1

        ledger = {
            "initial": initial_balances,
            "checkpoints": checkpoints,
            "executed": executed_events,
        }
        transaction_results = {
            "confirmed": confirmed, "deferred": deferred, "skipped": skipped,
        }
        changed_ledger = context.write(LEDGER, ledger)
        changed_transactions = context.write(TRANSACTIONS, transaction_results)
        return EvaluationResult(
            {key for key, changed in (
                (LEDGER, changed_ledger), (TRANSACTIONS, changed_transactions)
            ) if changed},
            dirty_range if changed_ledger or changed_transactions else None,
            events_recomputed=len(events) - start_index,
            checkpoints_reused=start_index,
            provenance=["forward checking state"],
        )


class PresentationNode(GraphNode):
    def __init__(self, IO, approximate):
        super().__init__("presentation", [LEDGER], [RAW_FORECAST])
        self.IO = IO
        self.approximate = approximate

    @staticmethod
    def _approximate_dates(start, end):
        dates = [start]
        cursor = datetime.date(start.year, start.month, 1)
        if cursor <= start:
            cursor = (cursor.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
        while cursor < end:
            dates.append(cursor)
            cursor = (cursor.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
        if dates[-1] != end:
            dates.append(end)
        return dates

    def evaluate(self, context, dirty_range):
        ledger = context.values[LEDGER]
        executed = ledger["executed"]
        dates = (
            self._approximate_dates(self.IO.start_date, self.IO.end_date)
            if self.approximate
            else list(generate_date_sequence(
                self.IO.start_date,
                (self.IO.end_date - self.IO.start_date).days,
                "daily",
            ))
        )
        rows = []
        balances = dict(ledger["initial"])
        cursor = 0
        income_dates = sorted({event.date for event, _ in executed if event.income_flag})
        previous_boundary = None
        for output_date in dates:
            interval = []
            while cursor < len(executed) and executed[cursor][0].date <= output_date:
                event, amount = executed[cursor]
                if previous_boundary is None or event.date > previous_boundary:
                    interval.append((event, amount))
                if event.account_from is not None:
                    balances[event.account_from] -= amount
                if event.account_to is not None:
                    balances[event.account_to] += amount
                cursor += 1
            memo, directives = self._memo(interval)
            next_income = ""
            if not self.approximate:
                next_income = next((day for day in income_dates if day > output_date), "")
            rows.append({
                "Date": output_date,
                **{name: float(value) for name, value in balances.items()},
                "Next Income Date": next_income,
                "Memo Directives": directives,
                "Memo": memo,
            })
            previous_boundary = output_date
        dataframe = pd.DataFrame(rows)
        changed = context.write(RAW_FORECAST, dataframe)
        return EvaluationResult(
            {RAW_FORECAST} if changed else set(), dirty_range if changed else None,
            events_recomputed=len(executed), provenance=["materialized presentation rows"],
        )

    def _memo(self, interval):
        if not interval:
            return "", ""
        if not self.approximate:
            memo_items, directives = [], []
            for event, amount in interval:
                if event.account_from is not None and event.account_to is not None:
                    continue
                endpoint = event.account_from or event.account_to
                sign = "-" if event.account_from is not None else "+"
                memo_items.append(f"{event.memo} ({endpoint} {sign}${float(amount):.2f})")
                if event.income_flag:
                    directives.append(f"INCOME ({endpoint} +${float(amount):.2f})")
            return "; ".join(memo_items), "; ".join(directives)
        groups = {}
        for event, amount in interval:
            key = (event.memo, event.account_from, event.account_to)
            count, total = groups.get(key, (0, float("0")))
            groups[key] = (count + 1, total + amount)
        memo_items = []
        for (memo, account_from, account_to), (count, amount) in groups.items():
            endpoint = account_from or account_to
            sign = "-" if account_from is not None else "+"
            count_text = f" x{count}" if count > 1 else ""
            memo_items.append(
                f"{memo}{count_text} ({endpoint} {sign}${float(amount):.2f})"
            )
        return "; ".join(memo_items), ""


class SummaryNode(GraphNode):
    def __init__(self, IO):
        super().__init__("summary", [RAW_FORECAST], [FORECAST])
        self.IO = IO

    def evaluate(self, context, dirty_range):
        from expense_forecast.ForecastHandler import ForecastHandler

        # Legacy runners round account presentation columns before policy
        # segments are stitched and their summary totals are recomputed. Do
        # the same here so totals are sums of the displayed account values,
        # rather than independently rounded sums of hidden precision.
        presentation = ForecastHandler._roundForecastOutput(
            context.values[RAW_FORECAST].copy(), decimals=2
        )
        dataframe = ForecastHandler._appendSummaryLines(
            self.IO.initial_account_set,
            presentation,
            log_stack_depth=0,
        )
        dataframe = ForecastHandler._roundForecastOutput(dataframe, decimals=2)
        changed = context.write(FORECAST, dataframe)
        return EvaluationResult(
            {FORECAST} if changed else set(), dirty_range if changed else None,
            events_recomputed=len(dataframe), provenance=["derived forecast summaries"],
        )


class GraphForecastRunner:
    def __init__(
        self, IO, milestone_set=None, approximate=False,
        include_debug_columns=False,
    ):
        self.configured_IO = copy.deepcopy(IO)
        self.configured_policy_set = copy.deepcopy(IO.policy_set)
        self.compiled_policy_set = copy.deepcopy(IO.policy_set)
        self.reserve_policies = []
        self.IO = copy.deepcopy(IO)
        self.milestone_set = milestone_set or MilestoneSet()
        self.approximate = approximate
        self.include_debug_columns = include_debug_columns
        self._compile_policies()
        self.validate_supported()
        has_stateful_accounts = any(
            account.account_type != "checking"
            for account in self.IO.initial_account_set.accounts
        ) or bool(self.configured_policy_set)
        if has_stateful_accounts:
            from .domain import AccountStateNode

            self.nodes = [
                ScheduleNode(self.IO),
                RoutingNode(self.IO.initial_memo_rule_set),
                AccountStateNode(
                    self.IO,
                    approximate=approximate,
                    # Stateful summaries require billing subcolumns internally;
                    # public projection drops them below when not requested.
                    include_debug_columns=True,
                    reserve_policies=self.reserve_policies,
                ),
                SummaryNode(self.IO),
            ]
        else:
            self.nodes = [
                ScheduleNode(self.IO),
                RoutingNode(self.IO.initial_memo_rule_set),
                CheckingStateNode(self.IO),
                PresentationNode(self.IO, approximate),
                SummaryNode(self.IO),
            ]
        self.graph = ComputationGraph(self.nodes)
        self.context = GraphContext()

    def _compile_policies(self):
        if not self.IO.policy_set:
            return
        reserve_policies = [
            policy for policy in self.IO.policy_set.policies
            if isinstance(policy, MinimumCheckingBalancePolicy)
        ]
        self.reserve_policies = copy.deepcopy(reserve_policies)
        from expense_forecast.ForecastHandler import ForecastHandler

        self.IO = ForecastHandler._materialize_cash_allocation_policies(
            self.IO, approximate=self.approximate
        )
        self.compiled_policy_set = copy.deepcopy(self.IO.policy_set)
        self.IO.policy_set = ForecastPolicySet()

    def validate_supported(self):
        unsupported = []
        for account in self.IO.initial_account_set.accounts:
            if account.account_type not in {"checking", "credit", "loan", "investment"}:
                unsupported.append(
                    f"account {account.name!r} has type {account.account_type!r}"
                )
        if self.IO.transition_set:
            unsupported.append("conditional scenario transitions")
        account_names = {account.name for account in self.IO.initial_account_set.accounts}
        for rule in self.IO.initial_memo_rule_set.memo_rules:
            for role, endpoint in (
                ("from", rule.account_from), ("to", rule.account_to)
            ):
                is_graph_endpoint = (
                    endpoint in account_names
                    or str(endpoint).startswith("ALL_LOANS")
                    or str(endpoint).startswith("ALL_CREDIT_CARDS")
                    or str(endpoint).startswith("CHECKING_ABOVE:")
                    or str(endpoint).startswith("SAVINGS_BELOW:")
                    or str(endpoint).startswith("CURRENT_STATEMENT_BALANCE:")
                )
                if endpoint not in (None, "", "None") and not is_graph_endpoint:
                    unsupported.append(
                        f"memo endpoint {role}={endpoint!r} is not a checking account"
                    )
        if unsupported:
            raise UnsupportedGraphBehaviorError(unsupported)

    def run(self):
        started = perf_counter()
        start_ts = datetime.datetime.now()
        first_event = EventKey(self.IO.start_date, "forecast-start", 0)
        change = ChangeSet.create(
            [VariableKey("config", "line_items")],
            DirtyRange(first_event),
            "initial graph evaluation",
        )
        self.graph.evaluate(self.context, change)
        if self.approximate:
            output_dates = PresentationNode._approximate_dates(
                self.IO.start_date,
                self.IO.end_date,
            )
            transaction_dates = {
                event.date for event in self.context.values.get(SCHEDULE, ())
            }
            self.context.diagnostics.sparse_calendar_dates = len(
                transaction_dates | set(output_dates)
            )
            self.context.diagnostics.output_bins = len(output_dates)
            # The approximate evaluator advances between sparse events using
            # elapsed spans; it never constructs one carry node per day.
            self.context.diagnostics.daily_carry_nodes = 0
        if self.configured_policy_set:
            self.context.diagnostics.policy_iterations += 1
            self.context.diagnostics.converged_components.append(
                "cash-allocation-policies"
            )
        self.context.diagnostics.wall_seconds = perf_counter() - started
        return self._result(start_ts)

    def update_budget(self, line_item_set, cause="budget update"):
        """Incrementally reevaluate after replacing the in-memory LineItemSet."""
        old_items = {
            self.IO.initial_line_item_set._line_item_key(item)
            for item in self.IO.initial_line_item_set.line_items
        }
        new_items = {
            line_item_set._line_item_key(item) for item in line_item_set.line_items
        }
        changed_keys = old_items ^ new_items
        if not changed_keys:
            self.context.diagnostics.cache_hits += 1
            return self._result(datetime.datetime.now())
        affected_dates = [key[0] for key in changed_keys]
        first_date = max(self.IO.start_date, min(affected_dates))
        self.IO.initial_line_item_set = copy.deepcopy(line_item_set)
        for node in self.nodes:
            if hasattr(node, "IO"):
                node.IO = self.IO
        dirty_event = EventKey(first_date, "budget-change", 0)
        change = ChangeSet.create(
            [VariableKey("config", "line_items")],
            DirtyRange(dirty_event),
            cause,
            provenance=("GraphForecastRunner.update_budget",),
        )
        started = perf_counter()
        self.graph.evaluate(self.context, change)
        self.context.diagnostics.wall_seconds += perf_counter() - started
        return self._result(datetime.datetime.now())

    def _result(self, start_ts):
        forecast = self.context.values[FORECAST]
        transactions = self.context.values[TRANSACTIONS]
        columns = [
            "Date", "Priority", "Amount", "Memo", "Income_Flag",
            "Deferrable", "Partial_Payment_Allowed",
        ]
        frames = {
            name: pd.DataFrame(
                records,
                columns=columns,
            )
            for name, records in transactions.items()
        }
        result = ExpenseForecastResult(
            self.configured_IO,
            forecast,
            start_ts,
            datetime.datetime.now(),
            confirmed_df=frames["confirmed"],
            deferred_df=frames["deferred"],
            skipped_df=frames["skipped"],
            milestone_set=self.milestone_set,
            milestone_results=MilestoneSet.evaluateMilestones(
                forecast, self.milestone_set, log_stack_depth=0
            ),
            approximate_flag=self.approximate,
            # Results are immutable snapshots even when this runner is reused
            # for another candidate evaluation.
            graph_diagnostics=copy.deepcopy(self.context.diagnostics),
        )
        if not self.include_debug_columns:
            debug_columns = set()
            for account in self.configured_IO.initial_account_set.accounts:
                debug_columns.update(
                    set(
                        self.configured_IO.initial_account_set.getForecastColumnsForAccount(
                            account
                        )
                    ) - {account.name}
                )
            result.forecast_df = result.forecast_df.drop(
                columns=list(debug_columns), errors="ignore"
            )
        if self.configured_policy_set:
            from expense_forecast.ForecastHandler import ForecastHandler

            result.policy_results = ForecastHandler._summarize_cash_policy_results(
                self.compiled_policy_set, result
            )
            result.policy_results.update(
                self.context.values.get(LEDGER, {}).get("reserve_results", {})
            )
        return result

from __future__ import annotations

import copy
import datetime
import re

import pandas as pd

from expense_forecast.AccountSet import AccountBoundaryError, AccountSet
from expense_forecast.generate_date_sequence import generate_date_sequence
from expense_forecast.MinimumCheckingBalancePolicy import MinimumCheckingBalancePolicy
from expense_forecast.ForecastPolicy import ForecastPolicyError

from .graph import GraphNode
from .models import EvaluationResult, EventKey, VariableKey


ROUTED = VariableKey("events", "routed")
LEDGER = VariableKey("state", "checking_ledger")
TRANSACTIONS = VariableKey("state", "transaction_results")
RAW_FORECAST = VariableKey("output", "raw_forecast")


class AccountStateNode(GraphNode):
    """Forward account/billing evaluator for debt and investment forecasts.

    The node owns orchestration and checkpoints.  AccountSet and its billing
    states remain the shared source of financial formulas used by both engines.
    """

    def __init__(
        self, IO, approximate=False, include_debug_columns=False,
        reserve_policies=(),
    ):
        super().__init__(
            "account-state",
            [ROUTED],
            [LEDGER, TRANSACTIONS, RAW_FORECAST],
        )
        self.IO = IO
        self.approximate = approximate
        self.include_debug_columns = include_debug_columns
        self.reserve_policies = tuple(copy.deepcopy(reserve_policies))

    def _resolve_reserves(self, context, events, dirty_range):
        if not self.reserve_policies:
            return {}, {}, {}
        gate_priority = min(policy.priority for policy in self.reserve_policies)
        discovery_events = [
            event for event in events
            if event.priority <= gate_priority
            and not str(event.memo).startswith("POLICY minimum_checking_balance")
        ]
        discovery_context = type(context)()
        discovery_context.write(ROUTED, discovery_events)
        discovery_node = AccountStateNode(
            self.IO,
            approximate=self.approximate,
            include_debug_columns=True,
            reserve_policies=(),
        )
        discovery_node.evaluate(discovery_context, dirty_range)
        forecast = discovery_context.values[RAW_FORECAST]
        activations, results, seed_rows = {}, {}, {}
        primary = self.IO.initial_account_set.primary_checking_account_name
        for policy in self.reserve_policies:
            runtime_key = self._reserve_runtime_key(policy)
            account_name = policy.account_name or primary
            window = forecast.loc[
                (forecast["Date"] >= getattr(policy, "_effective_start", self.IO.start_date))
                & (forecast["Date"] <= getattr(policy, "_effective_end", self.IO.end_date))
            ]
            values = pd.to_numeric(window[account_name], errors="coerce")
            qualifying = values.iloc[::-1].cummin().iloc[::-1] >= float(policy.target)
            matching = window.loc[qualifying]
            activation = None if matching.empty else matching.iloc[0]["Date"]
            status = "not_achieved" if activation is None else "activated"
            if activation is None and policy.on_unmet == "fail":
                raise ForecastPolicyError(
                    f"Minimum balance policy for {account_name} never established its reserve"
                )
            activations[runtime_key] = activation
            if activation is not None:
                seed_rows[runtime_key] = matching.iloc[0].to_dict()
            results[policy.policy_key] = {
                "status": status,
                "account_name": account_name,
                "target": policy.target,
                "activation_date": activation,
            }
        return activations, results, seed_rows

    @staticmethod
    def _reserve_runtime_key(policy):
        return (
            f"{policy.policy_key}@"
            f"{getattr(policy, '_effective_start', 'forecast-start')}"
        )

    def _reserve_applies(self, policy, day):
        return (
            getattr(policy, "_effective_start", self.IO.start_date)
            <= day
            <= getattr(policy, "_effective_end", self.IO.end_date)
        )

    @staticmethod
    def _output_dates(start, end, approximate):
        if not approximate:
            return list(generate_date_sequence(start, (end - start).days, "daily"))
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

    def _presentation_dates(self):
        """Dates exposed by this segment's public forecast.

        Keeping this definition beside the event-calendar construction avoids
        a subtle split-brain bug where execution and projection disagree about
        which month boundaries exist.
        """
        return self._output_dates(
            self.IO.start_date,
            self.IO.end_date,
            self.approximate,
        )

    @staticmethod
    def _append_directive(parts, value):
        if value:
            parts.append(str(value))

    @staticmethod
    def _future_source_reserve(events, current, source_name):
        running = float("0")
        maximum = float("0")
        for event in events:
            # Higher-priority events on the current date have already been
            # applied by the queue before this policy is evaluated. Counting
            # them again as future obligations suppresses the final-period
            # residual allocation.
            if event.date <= current.date:
                continue
            if event.priority >= current.priority:
                continue
            if event.account_from == source_name:
                running += event.amount
            if event.account_to == source_name:
                running -= event.amount
            maximum = max(maximum, running)
        return maximum

    def _safe_requested_amount(self, account_set, events, event):
        amount = event.amount
        if event.priority <= 1:
            return amount
        source_name = event.account_from
        threshold = None
        if str(source_name).startswith("CHECKING_ABOVE:"):
            threshold = float(str(source_name).split(":", 1)[1])
            source_name = account_set.primary_checking_account_name
        source = account_set._get_account_by_name(source_name)
        if source is not None and source.account_type == "checking":
            floor = max(
                float(str(
                    source.effective_policy_min_balance
                    if event.priority > 1 else source.min_balance
                )),
                threshold or float("0"),
            )
            # CHECKING_ABOVE encodes the surplus policy's complete reserve
            # rule. Legacy likewise executes the amount above that threshold
            # directly; applying the generic future-flow envelope a second
            # time would incorrectly suppress the investment after a higher-
            # priority saving policy is rejected.
            reserve = (
                float("0")
                if threshold is not None
                else self._future_source_reserve(events, event, source_name)
            )
            amount = min(
                amount, float(str(source.balance)) - floor - reserve
            )
            if amount < event.amount and not event.partial_payment_allowed:
                # Headroom is a feasibility bound, not permission to rewrite a
                # fixed transaction.  Only explicitly partial transactions
                # may be reduced to that bound; otherwise normal execution
                # rejects and classifies the original request.
                amount = event.amount
        destination = str(event.account_to)
        if destination.startswith("ALL_LOANS"):
            debt_type = "loan"
        elif destination.startswith("ALL_CREDIT_CARDS"):
            debt_type = "credit"
        else:
            target = account_set._get_account_by_name(event.account_to)
            debt_type = (
                target.account_type
                if target is not None and target.account_type in {"loan", "credit"}
                else None
            )
        if debt_type is not None:
            applicable_names = {
                account.name for account in account_set.accounts
                if account.account_type == debt_type
            }
            outstanding = sum(
                (float(str(account.balance)) for account in account_set.accounts
                 if account.name in applicable_names),
                float("0"),
            )
            future_claim = sum(
                (
                    future.amount for future in events
                    if future.key != event.key
                    and future.date >= event.date
                    and future.priority < event.priority
                    and (
                        future.account_to in applicable_names
                        or (
                            debt_type == "loan"
                            and str(future.account_to).startswith("ALL_LOANS")
                        )
                        or (
                            debt_type == "credit"
                            and str(future.account_to).startswith("ALL_CREDIT_CARDS")
                        )
                    )
                ),
                float("0"),
            )
            amount = min(amount, outstanding - future_claim)
        return max(
            float("0"),
            amount,
        )

    def _automatic_day(self, account_set, day, directives, investment_returns):
        """Apply billing rollover, accrual, returns, and minimum payments."""
        for value in account_set.processCreditCardBillingDay(day):
            self._append_directive(directives, value)
        account_set.updateCreditCardEndOfPreviousCycleBalances(day)

        for account in account_set.accounts:
            state = account.billing_state
            start = getattr(state, "billing_cycle_start_date", None)
            if isinstance(start, datetime.datetime):
                start = start.date()
            if start is None or day < start:
                continue
            if account.account_type == "loan":
                interval = state.interest_interval
                elapsed = (day - start).days
                dates = set(generate_date_sequence(start, elapsed, interval))
                dates.add(start)
                if day in dates:
                    interest = state.accrue_interest()
                    AccountSet._sync_debt_account_from_billing_state(account)
                    if interest:
                        self._append_directive(
                            directives,
                            f"LOAN INTEREST ({account.name}: Interest +${interest})",
                        )
            elif account.account_type == "investment":
                growth = state.accrue_return()
                account.balance = state.balance
                if growth:
                    investment_returns[account.name] = growth
                    self._append_directive(
                        directives,
                        f"INVESTMENT RETURN ({account.name} +${growth:.2f})",
                    )

        checking_name = account_set.primary_checking_account_name
        for account in account_set.accounts:
            if account.account_type not in {"loan", "credit"}:
                continue
            if not AccountSet.is_billing_date(account, day):
                continue
            state = account.billing_state
            if account.account_type == "loan":
                payment = min(state.remaining_minimum_payment_due(), state.balance)
                interest_part = min(payment, state.interest_balance)
                principal_part = min(state.principal_balance, payment - interest_part)
                if payment > 0:
                    account_set.executeTransaction(
                        checking_name, account.name, payment,
                        minimum_payment_flag=True,
                    )
                    if interest_part:
                        self._append_directive(
                            directives,
                            f"LOAN MIN PAYMENT ({account.name}: Interest -${interest_part})",
                        )
                    if principal_part:
                        self._append_directive(
                            directives,
                            f"LOAN MIN PAYMENT ({account.name}: Principal Balance -${principal_part})",
                        )
                    self._append_directive(
                        directives,
                        f"LOAN MIN PAYMENT ({checking_name} -${payment})",
                    )
            else:
                payment = state.remaining_minimum_payment_due()
                if payment > 0:
                    account_set.executeTransaction(
                        checking_name, account.name, payment,
                        minimum_payment_flag=True,
                    )
                    self._append_directive(
                        directives,
                        f"CC MIN PAYMENT ({account.name}: Prev Stmt Bal -${payment})",
                    )
                    self._append_directive(
                        directives,
                        f"CC MIN PAYMENT ({checking_name} -${payment})",
                    )

    def _memo(self, event, amount):
        if event.account_from is not None and event.account_to is not None:
            if str(event.memo).startswith((
                "POLICY surplus_saving:",
                "POLICY current_statement_balance_payment:",
            )):
                return f"{event.memo} ({event.account_from} -${amount})"
            # Investment transfers carry a checking/investment-side memo so
            # summary accounting can offset the contribution directive.
            accounts = {
                account.name: account.account_type
                for account in self.IO.initial_account_set.accounts
            }
            if "investment" in {
                accounts.get(event.account_from), accounts.get(event.account_to)
            } or self.approximate:
                return f"{event.memo} ({event.account_from} -${amount})"
            return ""
        endpoint = event.account_from or event.account_to
        sign = "-" if event.account_from is not None else "+"
        return f"{event.memo} ({endpoint} {sign}${amount})"

    def _transfer_directives(self, before, after, event, amount):
        directives = []
        if event.income_flag and not self.approximate:
            directives.append(f"INCOME ({event.account_to} +${amount})")
        for name, old in before.items():
            account = after._get_account_by_name(name)
            if account is None:
                continue
            delta = float(str(old)) - float(str(account.balance))
            if account.account_type == "credit" and delta > 0:
                if self.approximate and str(event.account_to).startswith("ALL_"):
                    continue
                current_statement_endpoint = (
                    self.approximate
                    and str(event.account_to).startswith(
                        "CURRENT_STATEMENT_BALANCE:"
                    )
                )
                label = (
                    event.account_to
                    if current_statement_endpoint
                    else name
                )
                directive_amount = amount if current_statement_endpoint else delta
                directives.append(
                    f"ADDTL CC PAYMENT ({label} -${directive_amount})"
                )
            elif (
                account.account_type == "loan"
                and delta > 0
                and str(event.account_to).startswith("ALL_LOANS")
                and not self.approximate
            ):
                directives.append(f"ADDTL LOAN PAYMENT ({name} -${delta})")
        if event.account_to is not None:
            target = after._get_account_by_name(event.account_to)
            if target is not None and target.account_type == "investment":
                directives.append(f"INVESTMENT CONTRIBUTION ({target.name} +${amount})")
            if str(event.account_to).startswith("SAVINGS_BELOW:"):
                savings_name = str(event.account_to).split(":", 2)[2]
                directives.append(
                    f"SAVINGS CONTRIBUTION ({savings_name} +${amount})"
                )
        if event.account_from is not None:
            source = after._get_account_by_name(event.account_from)
            if source is not None and source.account_type == "investment":
                directives.append(
                    f"INVESTMENT WITHDRAWAL ({event.account_to} +${amount})"
                )
        return directives

    def evaluate(self, context, dirty_range):
        events = list(context.values[ROUTED])
        self.current_statement_policy_cards = {
            str(event.account_to).split(":", 1)[1]
            for event in events
            if str(event.account_to).startswith("CURRENT_STATEMENT_BALANCE:")
        }
        reserve_activations, reserve_results, reserve_seed_rows = self._resolve_reserves(
            context, events, dirty_range
        )
        by_day = {}
        for event in events:
            by_day.setdefault(event.date, []).append(event)
        account_set = copy.deepcopy(self.IO.initial_account_set)
        initial = copy.deepcopy(account_set)
        checkpoints = {}
        confirmed, deferred, skipped, executed = [], [], [], []
        daily_rows = []
        evaluation_start = self.IO.start_date
        reused_checkpoints = 0
        old_ledger = context.values.get(LEDGER)
        old_transactions = context.values.get(TRANSACTIONS)
        if old_ledger is not None and dirty_range.start.date > self.IO.start_date:
            prior_day = dirty_range.start.date - datetime.timedelta(days=1)
            prior_key = EventKey(prior_day, "day-end")
            if prior_key in old_ledger["checkpoints"]:
                account_set = copy.deepcopy(old_ledger["checkpoints"][prior_key])
                checkpoints = {
                    key: copy.deepcopy(value)
                    for key, value in old_ledger["checkpoints"].items()
                    if key.date <= prior_day
                }
                daily_rows = copy.deepcopy(old_ledger.get("daily_rows", []))
                daily_rows = [row for row in daily_rows if row["Date"] <= prior_day]
                executed = [
                    value for value in old_ledger["executed"]
                    if value[0].date <= prior_day
                ]
                if old_transactions:
                    confirmed = [
                        value for value in old_transactions["confirmed"]
                        if value["Date"] <= prior_day
                    ]
                    deferred = [
                        value for value in old_transactions["deferred"]
                        if value["Date"] <= prior_day
                    ]
                    skipped = [
                        value for value in old_transactions["skipped"]
                        if value["Date"] <= prior_day
                    ]
                evaluation_start = dirty_range.start.date
                reused_checkpoints = len(checkpoints)
        income_dates = sorted({event.date for event in events if event.income_flag})
        output_dates = set(self._output_dates(
            self.IO.start_date, self.IO.end_date, self.approximate
        ))
        accrual_cursors = {}
        reserve_activates_at_start = any(
            pd.Timestamp(activation).date() == self.IO.start_date
            for activation in reserve_activations.values()
            if activation is not None
        )
        for account in account_set.accounts:
            start = getattr(account.billing_state, "billing_cycle_start_date", None)
            if isinstance(start, datetime.datetime):
                start = start.date()
            if account.account_type == "investment":
                accrual_cursors[account.name] = max(
                    # The opening row is a completed seed boundary. Returns
                    # begin over the following open span, not on that row.
                    evaluation_start,
                    start - datetime.timedelta(days=1),
                )
            elif account.account_type == "loan":
                accrual_cursors[account.name] = max(
                    # Approximate loan accrual measures the open span after
                    # the seed boundary.  The seed date itself is already
                    # represented by the opening balance.
                    evaluation_start,
                    start,
                )

        if self.approximate:
            # Approximate execution is event-time execution.  Account state is
            # visited only when a transaction occurs or a public month-boundary
            # row must be emitted.  Accrual helpers receive the exact elapsed
            # span from their cursors, so omitting quiet calendar days changes
            # work—not financial semantics.
            execution_dates = sorted(
                {
                    day
                    for day in output_dates
                    if evaluation_start <= day <= self.IO.end_date
                }
                | {
                    day
                    for day in by_day
                    if evaluation_start <= day <= self.IO.end_date
                }
            )
        else:
            execution_dates = generate_date_sequence(
                evaluation_start,
                (self.IO.end_date - evaluation_start).days,
                "daily",
            )

        for day in execution_dates:
            directives, memos, investment_returns = [], [], {}
            active_reserves = [
                policy for policy in self.reserve_policies
                if self._reserve_applies(policy, day)
                and reserve_activations.get(self._reserve_runtime_key(policy)) is not None
                and day >= reserve_activations[self._reserve_runtime_key(policy)]
            ]
            for policy in active_reserves:
                name = policy.account_name or account_set.primary_checking_account_name
                account_set._get_account_by_name(name).policy_min_balance = float(
                    policy.target
                )
            if (
                day != self.IO.start_date or reserve_activates_at_start
            ) and not self.approximate:
                self._automatic_day(
                    account_set, day, directives, investment_returns
                )
            queue = list(by_day.get(day, []))
            index = 0
            while index < len(queue):
                event = queue[index]
                blocking_reserves = [
                    policy for policy in self.reserve_policies
                    if self._reserve_applies(policy, day)
                    and reserve_activations.get(self._reserve_runtime_key(policy)) is not None
                    and day < reserve_activations[self._reserve_runtime_key(policy)]
                    and event.priority > policy.priority
                ]
                if blocking_reserves:
                    if event.deferrable:
                        deferred.append(event.transaction_record())
                    else:
                        skipped.append(event.transaction_record())
                    index += 1
                    continue
                if (
                    day == self.IO.start_date
                    and (
                        reserve_activates_at_start
                        or (
                            event.priority > 1
                            and str(event.memo).startswith("POLICY ")
                        )
                    )
                ):
                    # The reserve-activation seed already contains the
                    # opening day's mandatory effects, but those scheduled
                    # transactions remain part of the public confirmed
                    # ledger (matching the discovery prefix stitched by the
                    # legacy runner). Record them without applying them twice.
                    if (
                        reserve_activates_at_start
                        and event.priority == 1
                        and not str(event.memo).startswith("POLICY ")
                    ):
                        confirmed.append(event.transaction_record())
                    index += 1
                    continue
                if self.approximate:
                    for endpoint in (event.account_from, event.account_to):
                        self._accrue_approx_to(
                            account_set, endpoint, day, accrual_cursors,
                            directives, investment_returns,
                        )
                    if str(event.account_to).startswith("ALL_LOANS"):
                        for debt_account in account_set.accounts:
                            if debt_account.account_type == "loan":
                                self._accrue_approx_to(
                                    account_set, debt_account.name, day,
                                    accrual_cursors, directives,
                                    investment_returns,
                                )
                before = {a.name: a.balance for a in account_set.accounts}
                requested_amount = self._safe_requested_amount(
                    account_set, events, event
                )
                try:
                    amount = account_set.executeTransaction(
                        event.account_from,
                        event.account_to,
                        requested_amount,
                        income_flag=event.income_flag,
                        allocation_strategy=(
                            "snowball" if str(event.account_to).endswith("SNOWBALL")
                            else "avalanche"
                        ),
                        enforce_policy_minimum=event.priority > 1,
                    )
                except AccountBoundaryError:
                    amount = float("0")
                amount = float(str(amount or 0))
                if (
                    amount <= 0
                    and (
                        requested_amount > 0
                        or str(event.account_to).startswith(
                            ("ALL_LOANS", "ALL_CREDIT_CARDS")
                        )
                    )
                    and event.partial_payment_allowed
                ):
                    amount = self._maximum_partial(account_set, event)
                if amount <= float("0.005"):
                    record = event.transaction_record()
                    if event.deferrable:
                        next_income = next(
                            (value for value in income_dates if value > day), None
                        )
                        if next_income is not None:
                            by_day.setdefault(next_income, []).append(event)
                        else:
                            skipped.append(record)
                    elif event.priority > 1 or str(event.memo).startswith("POLICY "):
                        # A priority-one policy event can legitimately be a
                        # no-op (for example, a current-statement payment when
                        # the statement is already zero). It is not a failed
                        # mandatory scheduled transaction.
                        skipped.append(record)
                    else:
                        raise AccountBoundaryError(
                            f"Mandatory graph transaction failed: {event.memo!r}"
                        )
                    index += 1
                    continue
                confirmed.append(event.transaction_record(amount, day))
                executed.append((event, amount))
                if str(event.account_to).startswith(
                    "CURRENT_STATEMENT_BALANCE:"
                ):
                    card_name = str(event.account_to).split(":", 1)[1]
                    card = account_set._get_account_by_name(card_name)
                    interest = card.billing_state.interest_accrued_this_cycle()
                    if interest:
                        directives.append(
                            f"CC INTEREST ({card.name}: Prev Stmt Bal +${interest:.2f})"
                        )
                    card.billing_state = card.billing_state.roll_cycle(
                        day + datetime.timedelta(days=1)
                    )
                    AccountSet._sync_debt_account_from_billing_state(card)
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
                        directives.extend([
                            f"MINIMUM PAYMENT ({checking.name} -${minimum_payment:.2f})",
                            f"MINIMUM PAYMENT ({card.name} +${minimum_payment:.2f})",
                        ])
                memo = self._memo(event, amount)
                if memo:
                    memos.append(memo)
                directives.extend(
                    self._transfer_directives(before, account_set, event, amount)
                )
                index += 1

            if (
                self.approximate
                and day in output_dates
                and (day != self.IO.start_date or reserve_activates_at_start)
            ):
                for account in account_set.accounts:
                    if account.account_type == "investment":
                        self._accrue_approx_to(
                            account_set, account.name, day, accrual_cursors,
                            directives, investment_returns,
                        )
                self._approximate_billing_day(
                    account_set, day, directives, accrual_cursors,
                    investment_returns,
                )

            snapshot = copy.deepcopy(account_set)
            checkpoints[EventKey(day, "day-end")] = snapshot
            daily_rows.append({
                "Date": day,
                **account_set.getForecastAccountBalances(
                    include_debug_columns=self.include_debug_columns
                ),
                "Next Income Date": next(
                    (value for value in income_dates if value > day), ""
                ),
                "Memo Directives": "; ".join(directives),
                "Memo": "; ".join(memos),
                "_Investment Returns": investment_returns,
            })

        frame = pd.DataFrame(daily_rows)
        if self.approximate:
            output_dates = self._presentation_dates()
            projected = []
            previous = None
            for output_day in output_dates:
                row = frame.loc[frame["Date"] == output_day].iloc[0].to_dict()
                interval = frame.loc[
                    (frame["Date"] <= output_day)
                    & (True if previous is None else (frame["Date"] > previous))
                ]
                interval_events = [
                    (event, amount)
                    for event, amount in executed
                    if event.date <= output_day
                    and (previous is None or event.date > previous)
                ]
                memo_groups = {}
                for event, amount in interval_events:
                    key = (event.memo, event.account_from, event.account_to)
                    count, total = memo_groups.get(key, (0, float("0")))
                    memo_groups[key] = (count + 1, total + amount)
                memo_parts = []
                for (memo, account_from, account_to), (count, total) in memo_groups.items():
                    endpoint = account_from or account_to
                    sign = "-" if account_from is not None else "+"
                    count_text = f" x{count}" if count > 1 else ""
                    memo_parts.append(
                        f"{memo}{count_text} ({endpoint} {sign}${total:.2f})"
                    )
                row["Memo"] = "; ".join(memo_parts)
                row["Memo Directives"] = "; ".join(
                    value for value in interval["Memo Directives"].astype(str) if value
                )
                row["Next Income Date"] = ""
                projected.append(row)
                previous = output_day
            frame = pd.DataFrame(projected)
        achieved_seeds = [
            (reserve_activations[key], row)
            for key, row in reserve_seed_rows.items()
            if reserve_activations.get(key) is not None
        ]
        if achieved_seeds:
            for activation, raw_seed in sorted(achieved_seeds, key=lambda item: item[0]):
                seed = dict(raw_seed)
                if pd.Timestamp(activation).date() == self.IO.start_date:
                    # Activation at the forecast boundary still needs the
                    # opening account checkpoint, before any start-date
                    # occurrences. Legacy creates that checkpoint by seeding
                    # its post-activation run one day earlier.
                    seed.update(initial.getForecastAccountBalances(
                        include_debug_columns=self.include_debug_columns
                    ))
                seed["Date"] = activation - datetime.timedelta(days=1)
                seed["Memo"] = ""
                seed["Memo Directives"] = ""
                seed["_Investment Returns"] = {}
                # This is an internal propagation checkpoint. Expose it only
                # when it is inside the requested range and its date is not
                # already represented by the discovery projection. Exact
                # output already contains every day; approximate output may
                # need this additional presentation boundary.
                if (
                    seed["Date"] >= self.IO.start_date
                    and seed["Date"] not in set(frame["Date"])
                ):
                    insertion = pd.DataFrame([seed])
                    before = frame.loc[frame["Date"] <= seed["Date"]]
                    same_or_after = frame.loc[frame["Date"] > seed["Date"]]
                    frame = pd.concat(
                        [before, insertion, same_or_after], ignore_index=True
                    )
                frame.loc[
                    frame["Date"] == activation, "Memo"
                ] = ""
                if self.approximate:
                    frame.loc[frame["Date"] == activation, "Memo"] = str(
                        raw_seed.get("Memo", "") or ""
                    )
                else:
                    activation_memos = [
                        self._memo(event, event.amount)
                        for event in events
                        if event.date == activation
                        and not str(event.memo).startswith("POLICY ")
                    ]
                    frame.loc[frame["Date"] == activation, "Memo"] = "; ".join(
                        memo for memo in activation_memos if memo
                    )
        frame = frame.drop(columns=["_Investment Returns"], errors="ignore")

        ledger = {
            "initial_account_set": initial,
            "checkpoints": checkpoints,
            "executed": executed,
            "reserve_results": reserve_results,
            "daily_rows": daily_rows,
        }
        transactions = {"confirmed": confirmed, "deferred": deferred, "skipped": skipped}
        changed_ledger = context.write(LEDGER, ledger)
        changed_transactions = context.write(TRANSACTIONS, transactions)
        changed_frame = context.write(RAW_FORECAST, frame)
        changed_outputs = {
            key for key, changed in (
                (LEDGER, changed_ledger),
                (TRANSACTIONS, changed_transactions),
                (RAW_FORECAST, changed_frame),
            ) if changed
        }
        debt_accounts = sum(
            account.account_type in {"credit", "loan"}
            for account in account_set.accounts
        )
        investment_accounts = sum(
            account.account_type == "investment"
            for account in account_set.accounts
        )
        context.diagnostics.billing_cycles_recomputed += debt_accounts * len(frame)
        context.diagnostics.investment_spans_recomputed += (
            investment_accounts * len(frame)
        )
        return EvaluationResult(
            changed_outputs,
            dirty_range if changed_outputs else None,
            events_recomputed=len(events),
            checkpoints_reused=reused_checkpoints,
            provenance=["forward debt and investment account state"],
        )

    @staticmethod
    def _accrue_approx_to(
        account_set, endpoint, day, cursors, directives, investment_returns,
    ):
        account = account_set._get_account_by_name(endpoint)
        if account is None or account.name not in cursors:
            return
        cursor = cursors[account.name]
        if day <= cursor:
            return
        days = (day - cursor).days
        if account.account_type == "investment":
            growth = account.billing_state.accrue_return(days)
            account.balance = account.billing_state.balance
            if growth:
                investment_returns[account.name] = (
                    investment_returns.get(account.name, float("0")) + growth
                )
                directives.append(
                    f"INVESTMENT RETURN ({account.name} +${growth})"
                )
        elif account.account_type == "loan":
            state = account.billing_state
            interest = state.principal_balance * state.apr * float(days) / float("365.25")
            state.interest_balance += interest
            AccountSet._sync_debt_account_from_billing_state(account)
            if interest:
                directives.append(
                    f"LOAN INTEREST ({account.name}: Interest +${interest:.2f})"
                )
        cursors[account.name] = day

    def _approximate_billing_day(
        self, account_set, day, directives, accrual_cursors=None,
        investment_returns=None,
    ):
        checking_name = account_set.primary_checking_account_name
        for account in account_set.accounts:
            if account.account_type not in {"credit", "loan"}:
                continue
            if (
                account.account_type == "credit"
                and account.name in self.current_statement_policy_cards
            ):
                continue
            if accrual_cursors is not None:
                self._accrue_approx_to(
                    account_set, account.name, day, accrual_cursors,
                    directives, investment_returns or {},
                )
            start = account.billing_state.billing_cycle_start_date
            if day < start:
                continue
            if account.account_type == "credit":
                interest = account.billing_state.interest_accrued_this_cycle()
                if interest:
                    directives.append(
                        f"CC INTEREST ({account.name}: Prev Stmt Bal +${interest:.2f})"
                    )
                account.billing_state = account.billing_state.roll_cycle(day)
                AccountSet._sync_debt_account_from_billing_state(account)
                if account.name in self.current_statement_policy_cards:
                    payment = float("0")
                else:
                    payment = min(
                        account.billing_state.remaining_minimum_payment_due(),
                        account.balance,
                        float(str(account_set._get_account_by_name(checking_name).balance)),
                    )
            else:
                payment = min(
                    account.billing_state.minimum_payment,
                    account.billing_state.balance,
                    float(str(account_set._get_account_by_name(checking_name).balance)),
                )
            if payment > 0:
                account_set.executeTransaction(
                    checking_name, account.name, payment,
                    minimum_payment_flag=True,
                )
                directives.extend([
                    f"MINIMUM PAYMENT ({checking_name} -${payment:.2f})",
                    f"MINIMUM PAYMENT ({account.name} +${payment:.2f})",
                ])

    @staticmethod
    def _bin_investment_returns(directive_text, interval):
        """Match approximate legacy's single full-precision return posting."""
        parts = [part.strip() for part in directive_text.split(";") if part.strip()]
        names = []
        retained = []
        for part in parts:
            match = re.match(r"INVESTMENT RETURN \((.+?) \+\$", part)
            if match:
                if match.group(1) not in names:
                    names.append(match.group(1))
            else:
                retained.append(part)
        for name in names:
            # The row balances retain full precision, so growth over the bin is
            # the end balance less the previous boundary balance. Derive it by
            # summing unrounded daily account deltas from snapshots.
            total = sum(
                (
                    float(str(values.get(name, 0)))
                    for values in interval["_Investment Returns"]
                ),
                float("0"),
            )
            if total:
                retained.append(f"INVESTMENT RETURN ({name} +${total})")
        return "; ".join(retained)

    @staticmethod
    def _maximum_partial(account_set, event):
        low, high = float("0"), event.amount
        best = float("0")
        for _ in range(60):
            middle = (low + high) / float("2")
            candidate = copy.deepcopy(account_set)
            try:
                executed = candidate.executeTransaction(
                    event.account_from, event.account_to, middle,
                    income_flag=event.income_flag,
                    enforce_policy_minimum=event.priority > 1,
                )
            except AccountBoundaryError:
                executed = float("0")
            if float(str(executed or 0)) > 0:
                best, low = middle, middle
            else:
                high = middle
        if best > 0:
            return float(str(account_set.executeTransaction(
                event.account_from, event.account_to, best,
                income_flag=event.income_flag,
                enforce_policy_minimum=event.priority > 1,
            )))
        return float("0")

# Based on this paper: https://csd.cs.cmu.edu/sites/default/files/phd-thesis/CMU-CS-05-129.pdf
from __future__ import annotations
from dataclasses import dataclass, field
from heapq import heappop, heappush
from collections.abc import Hashable
from abc import ABC, abstractmethod

from expense_forecast.AccountSet import AccountSet
from expense_forecast.LineItemSet import LineItemSet
# from expense_forecast.ForecastSetInitialConditions import ForecastSetInitialConditions
from expense_forecast.MemoRuleSet import MemoRuleSet
from expense_forecast.MilestoneSet import MilestoneSet
from expense_forecast.ForecastHandler import ForecastHandler
from expense_forecast.ExpenseForecastInitialConditions import ExpenseForecastInitialConditions
from expense_forecast.ExpenseForecastResult import ExpenseForecastResult
from expense_forecast.ForecastPolicySet import ForecastPolicySet
from expense_forecast.MinimumCheckingBalancePolicy import MinimumCheckingBalancePolicy
from copy import deepcopy
import pandas as pd
from datetime import date
import datetime
from decimal import Decimal
import copy
import logging

logger = logging.getLogger(__name__)

if not logger.handlers:
    logging.basicConfig(
        level=logging.DEBUG,  # INFO when you get tired of the spam
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

def values_equal(left, right) -> bool:
    if pd.isna(left) and pd.isna(right):
        return True

    return left == right

type NodeId = Hashable


@dataclass(frozen=True)
class GraphV2Difference:
    section: str
    event: object = None
    variable: str | None = None
    graph_value: object = None
    legacy_value: object = None
    producer: str | None = None


class GraphV2ShadowMismatchError(AssertionError):
    """All observable differences between one v2 and legacy forecast."""

    def __init__(
        self,
        *,
        scenario: str = "unnamed",
        differences: list[GraphV2Difference] | None = None,
        event=None,
        variable=None,
        graph_value=None,
        legacy_value=None,
        producer=None,
    ):
        if differences is None:
            differences = [
                GraphV2Difference(
                    section="forecast_df",
                    event=event,
                    variable=variable,
                    graph_value=graph_value,
                    legacy_value=legacy_value,
                    producer=producer,
                )
            ]
        self.scenario = scenario
        self.differences = list(differences)
        first = self.differences[0]
        # Compatibility with the original first-cell comparator API.
        self.section = first.section
        self.event = first.event
        self.variable = first.variable
        self.graph_value = first.graph_value
        self.legacy_value = first.legacy_value
        self.producer = first.producer

        shown = self.differences[:20]
        details = "\n".join(
            "  - "
            f"{difference.section}: event={difference.event!r} "
            f"variable={difference.variable!r} "
            f"v2={difference.graph_value!r} "
            f"legacy={difference.legacy_value!r} "
            f"producer={difference.producer!r}"
            for difference in shown
        )
        remaining = len(self.differences) - len(shown)
        if remaining:
            details += f"\n  - ... {remaining} additional differences"
        super().__init__(
            f"Graph v2 shadow mismatch for {scenario!r} "
            f"({len(self.differences)} differences):\n{details}"
        )


def compare_v2_account_balances(
    graph_frame: pd.DataFrame,
    legacy_frame: pd.DataFrame,
    account_names: list[str],
) -> None:
    """Compare the account state currently materialized by graph v2.

    This intentionally does not claim parity for result fields that v2 does
    not produce yet. As those fields are implemented, this comparator should
    be expanded rather than silently borrowing them from legacy.
    """
    graph = graph_frame.loc[:, account_names].copy()
    graph.index = pd.Index(pd.to_datetime(graph.index).date)

    legacy = legacy_frame.loc[:, ["Date", *account_names]].copy()
    legacy.index = pd.Index(pd.to_datetime(legacy.pop("Date")).dt.date)

    if not graph.index.equals(legacy.index):
        raise GraphV2ShadowMismatchError(
            event=None,
            variable="Date",
            graph_value=graph.index.tolist(),
            legacy_value=legacy.index.tolist(),
            producer="event calendar",
        )

    for forecast_date in graph.index:
        for account_name in account_names:
            graph_value = Decimal(
                str(graph.at[forecast_date, account_name])
            ).quantize(Decimal("0.01"))
            legacy_value = Decimal(
                str(legacy.at[forecast_date, account_name])
            ).quantize(Decimal("0.01"))
            if graph_value != legacy_value:
                raise GraphV2ShadowMismatchError(
                    event=forecast_date,
                    variable=account_name,
                    graph_value=graph_value,
                    legacy_value=legacy_value,
                    producer="account-state graph",
                )


def _normalized_shadow_value(value):
    if pd.isna(value):
        return None
    if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
        decimal_value = Decimal(str(value))
        if not decimal_value.is_finite():
            return str(decimal_value)
        return decimal_value.quantize(Decimal("0.01"))
    return str(value)


def _normalized_shadow_frame(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy().reset_index(drop=True)
    sort_columns = [
        column
        for column in ("Date", "Priority", "Memo", "Amount")
        if column in result.columns
    ]
    if sort_columns and not result.empty:
        result = result.sort_values(sort_columns).reset_index(drop=True)
    for column in result.columns:
        result[column] = result[column].map(_normalized_shadow_value)
    # Financial parity is based on normalized values and column shape, not on
    # pandas' inferred dtype for an empty transaction frame.
    return result.astype(object)


def compare_v2_result(
    graph_output,
    legacy_result: ExpenseForecastResult,
    *,
    scenario: str,
) -> None:
    """Compare every observable result currently required for v2 parity."""
    differences: list[GraphV2Difference] = []
    graph_is_result = isinstance(graph_output, ExpenseForecastResult)
    graph_frame = (
        graph_output.forecast_df if graph_is_result else graph_output
    ).copy()
    if "Date" not in graph_frame.columns:
        graph_frame.insert(0, "Date", graph_frame.index)
    graph_frame = graph_frame.reset_index(drop=True)
    legacy_frame = legacy_result.forecast_df.reset_index(drop=True)
    # Deferred-transaction scheduling has not yet been implemented in v2.
    # Keep this legacy projection outside the parity contract until it is.
    graph_frame = graph_frame.drop(
        columns=["Next Income Date"], errors="ignore"
    )
    legacy_frame = legacy_frame.drop(
        columns=["Next Income Date"], errors="ignore"
    )
    internal_bound_suffixes = (
        ": Min Balance",
        ": Max Balance",
        ": Policy Min Balance",
        ": Policy Max Balance",
        ": Prev Stmt Bal Policy Min",
        ": Prev Stmt Bal Policy Max",
    )
    graph_frame = graph_frame.drop(
        columns=[
            column
            for column in graph_frame.columns
            if column.endswith(internal_bound_suffixes)
        ],
        errors="ignore",
    )
    legacy_frame = legacy_frame.drop(
        columns=[
            column
            for column in legacy_frame.columns
            if column.endswith(internal_bound_suffixes)
        ],
        errors="ignore",
    )

    graph_columns = list(graph_frame.columns)
    legacy_columns = list(legacy_frame.columns)
    if graph_columns != legacy_columns:
        differences.append(
            GraphV2Difference(
                section="forecast_df",
                variable="columns",
                graph_value=graph_columns,
                legacy_value=legacy_columns,
                producer="result assembly",
            )
        )

    if len(graph_frame) != len(legacy_frame):
        differences.append(
            GraphV2Difference(
                section="forecast_df",
                variable="row count",
                graph_value=len(graph_frame),
                legacy_value=len(legacy_frame),
                producer="event calendar",
            )
        )

    shared_columns = [
        column for column in legacy_columns if column in graph_columns
    ]
    for row_number in range(min(len(graph_frame), len(legacy_frame))):
        event = legacy_frame.at[row_number, "Date"]
        for column in shared_columns:
            graph_value = _normalized_shadow_value(
                graph_frame.at[row_number, column]
            )
            legacy_value = _normalized_shadow_value(
                legacy_frame.at[row_number, column]
            )
            if graph_value != legacy_value:
                differences.append(
                    GraphV2Difference(
                        section="forecast_df",
                        event=event,
                        variable=column,
                        graph_value=graph_value,
                        legacy_value=legacy_value,
                        producer="forecast materialization",
                    )
                )

    for section in ("confirmed_df", "deferred_df", "skipped_df"):
        if not graph_is_result:
            differences.append(
                GraphV2Difference(
                    section=section,
                    variable="output",
                    graph_value="<missing>",
                    legacy_value=getattr(legacy_result, section),
                    producer="transaction classification",
                )
            )
            continue
        graph_section = getattr(graph_output, section)
        legacy_section = getattr(legacy_result, section)
        if graph_section is None or legacy_section is None:
            if graph_section is not legacy_section:
                differences.append(
                    GraphV2Difference(
                        section=section,
                        variable="output",
                        graph_value=graph_section,
                        legacy_value=legacy_section,
                        producer="transaction classification",
                    )
                )
            continue
        left = _normalized_shadow_frame(graph_section)
        right = _normalized_shadow_frame(legacy_section)
        if not left.equals(right):
            differences.append(
                GraphV2Difference(
                    section=section,
                    variable="rows",
                    graph_value=left.to_dict("records"),
                    legacy_value=right.to_dict("records"),
                    producer="transaction classification",
                )
            )

    for attribute in ("milestone_results", "policy_results"):
        if not graph_is_result:
            differences.append(
                GraphV2Difference(
                    section=attribute,
                    variable="output",
                    graph_value="<missing>",
                    legacy_value=getattr(legacy_result, attribute),
                    producer="result assembly",
                )
            )
        elif getattr(graph_output, attribute) != getattr(
            legacy_result, attribute
        ):
            differences.append(
                GraphV2Difference(
                    section=attribute,
                    variable="value",
                    graph_value=getattr(graph_output, attribute),
                    legacy_value=getattr(legacy_result, attribute),
                    producer="result assembly",
                )
            )

    if differences:
        raise GraphV2ShadowMismatchError(
            scenario=scenario,
            differences=differences,
        )


def balance_column(account_name: str) -> str:
    return account_name


def policy_minimum_column(account_name: str) -> str:
    return f"{account_name}: Policy Min Balance"


def policy_maximum_column(account_name: str) -> str:
    return f"{account_name}: Policy Max Balance"


def credit_current_statement_column(account_name: str) -> str:
    return f"{account_name}: Curr Stmt Bal"


def credit_previous_statement_column(account_name: str) -> str:
    return f"{account_name}: Prev Stmt Bal"


def credit_payment_balance_column(account_name: str) -> str:
    return f"{account_name}: Credit Billing Cycle Payment Bal"


def credit_end_previous_cycle_column(account_name: str) -> str:
    return f"{account_name}: Credit End of Prev Cycle Bal"


def credit_minimum_payment_column(account_name: str) -> str:
    return f"{account_name}: Credit Minimum Payment"


def credit_minimum_payment_credit_column(account_name: str) -> str:
    return f"{account_name}: Credit Minimum Payment Credit"


def previous_statement_policy_minimum_column(account_name: str) -> str:
    return f"{account_name}: Prev Stmt Bal Policy Min"


def previous_statement_policy_maximum_column(account_name: str) -> str:
    return f"{account_name}: Prev Stmt Bal Policy Max"


def loan_principal_column(account_name: str) -> str:
    return f"{account_name}: Principal Balance"


def loan_interest_column(account_name: str) -> str:
    return f"{account_name}: Interest"


def loan_payment_balance_column(account_name: str) -> str:
    return f"{account_name}: Loan Billing Cycle Payment Bal"


def account_initial_cell_values(account) -> dict[str, object]:
    values: dict[str, object] = {
        balance_column(account.name): account.balance,
        policy_minimum_column(account.name): account.min_balance,
        policy_maximum_column(account.name): account.max_balance,
    }
    state = account.billing_state
    if account.account_type == "credit":
        values.update({
            credit_current_statement_column(account.name):
                state.current_statement_balance,
            credit_previous_statement_column(account.name):
                state.previous_statement_balance,
            credit_payment_balance_column(account.name):
                state.billing_cycle_payment_balance,
            credit_end_previous_cycle_column(account.name):
                state.end_of_previous_cycle_balance,
            credit_minimum_payment_column(account.name):
                state.minimum_payment,
            credit_minimum_payment_credit_column(account.name):
                state.minimum_payment_credit_balance,
            previous_statement_policy_minimum_column(account.name):
                Decimal("0"),
            previous_statement_policy_maximum_column(account.name):
                account.max_balance,
        })
    elif account.account_type == "loan":
        values.update({
            loan_principal_column(account.name): state.principal_balance,
            loan_interest_column(account.name): state.interest_balance,
            loan_payment_balance_column(account.name):
                state.billing_cycle_payment_balance,
        })
    return values

@dataclass(order=True)
class Priority:
    day: int
    phase: int
    sequence: int # = field(init=False, default=0)

@dataclass(frozen=True)
class CellId:
    forecast_date: date
    column_name: str

@dataclass
class ExecutionContext:

    initial_conditions: ExpenseForecastInitialConditions
    milestone_set: MilestoneSet
    latest_priority: Priority = field(default_factory=lambda: Priority(0, 0, 0))
    forecast_df: pd.DataFrame = field(init=False)

    readers: dict[CellId, set[NodeId]] = field(default_factory=dict)
    nodes: dict[NodeId, "ComputationNode"] = field(default_factory=dict)
    registration_order: list[NodeId] = field(default_factory=list)
    pending_heap: list[tuple[Priority, NodeId]] = field(default_factory=list)
    pending_ids: set[NodeId] = field(default_factory=set)
    occurrence_counts: dict[tuple[Hashable, ...], int] = field(
        default_factory=dict
    )

    def fork(self) -> "ExecutionContext":
        candidate = object.__new__(ExecutionContext)

        candidate.initial_conditions = self.initial_conditions
        candidate.milestone_set = deepcopy(self.milestone_set)
        candidate.latest_priority = self.latest_priority

        candidate.forecast_df = self.forecast_df.copy(deep=True)

        candidate.readers = {
            cell: set(node_ids)
            for cell, node_ids in self.readers.items()
        }
        candidate.nodes = self.nodes.copy()
        candidate.registration_order = self.registration_order.copy()
        candidate.pending_heap = self.pending_heap.copy()
        candidate.pending_ids = self.pending_ids.copy()
        candidate.occurrence_counts = self.occurrence_counts.copy()

        candidate.name_to_account_type = self.name_to_account_type.copy()
        candidate.name_to_account_min = self.name_to_account_min.copy()
        candidate.name_to_account_max = self.name_to_account_max.copy()
        candidate.confirmed_df = self.confirmed_df.copy()
        candidate.deferred_df = self.deferred_df.copy()
        candidate.skipped_df = self.skipped_df.copy()
        candidate.line_item_set = copy.deepcopy(self.line_item_set)

        return candidate

    # ### Unclear on why I need this
    # # Cell/location -> nodes that read it.
    # readers: dict[CellId, set[NodeId]]

    # nodes: dict[NodeId, "ComputationNode"] = field(default_factory=dict)

    # # Full order of nodes created during the execution.
    # registration_order: list[NodeId] = field(default_factory=list)

    # # Current repair frontier.
    # pending_heap: list[tuple[Priority, NodeId]] = field(default_factory=list)
    # pending_ids: set[NodeId] = field(default_factory=set)

    def register(self, day_index: int, priority_level: int, node: "ComputationNode") -> None:
        logger.info('register '+str(node.__class__)+' '+str(node.node_id))
        if node.node_id in self.nodes:
            raise ValueError(f"Duplicate node ID: {node.node_id!r}")

        sequence = len(self.registration_order) #TODO not sure this is the right way

        node.priority = Priority(
            day_index,
            priority_level,
            sequence
        )

        self.nodes[node.node_id] = node
        self.registration_order.append(node.node_id)

        for location in node.reads:
            self.readers.setdefault(location, set()).add(node.node_id)

    def enqueue(self, node_id: NodeId) -> None:
        if node_id in self.pending_ids:
            return

        node = self.nodes[node_id]
        heappush(self.pending_heap, (node.priority, node_id))
        self.pending_ids.add(node_id)

    def pop_pending(self) -> "ComputationNode":
        _, node_id = heappop(self.pending_heap)
        self.pending_ids.remove(node_id)
        return self.nodes[node_id]
    
    def __post_init__(self) -> None:
        self.name_to_account_type = {}
        self.name_to_account_min = {}
        self.name_to_account_max = {}

        cell_columns: list[str] = []
        for account in self.initial_conditions.initial_account_set.accounts:
            cell_columns.extend(account_initial_cell_values(account))

            # these are here for readability of the code and to prevent
            # repeated lookups
            self.name_to_account_type[account.name] = account.account_type
            self.name_to_account_min[account.name] = account.min_balance
            self.name_to_account_max[account.name] = account.max_balance

        forecast_dates = [ d.date() for d in pd.date_range(
            self.initial_conditions.start_date,
            self.initial_conditions.end_date,
            freq="D",
        ) ]
        initialized_forecast_df = pd.DataFrame(
                index=forecast_dates,
                columns=cell_columns,
                dtype=float,
            )
        initialized_forecast_df['Memo'] = ''
        initialized_forecast_df['Memo Directives'] = ''
        self.forecast_df = initialized_forecast_df

        self.confirmed_df = self.initial_conditions.initial_confirmed_df.copy()
        self.deferred_df = self.initial_conditions.initial_deferred_df.copy()
        self.skipped_df = self.initial_conditions.initial_skipped_df.copy()

        self.line_item_set = copy.deepcopy(self.initial_conditions.initial_line_item_set)

        # used to differentiate between txns w all the same values
        self.occurrence_counts: dict[tuple[Hashable, ...], int] = {}

        

    def read(self, cell: CellId):
        return self.forecast_df.at[
            cell.forecast_date,
            cell.column_name,
        ]

    def write(self, cell: CellId, value) -> bool:
        logger.info('write '+str(cell.forecast_date)+' '+str(cell.column_name).ljust(25,'.')+' '+str(value))
        previous_value = self.forecast_df.at[
            cell.forecast_date,
            cell.column_name,
        ]

        changed = not values_equal(previous_value, value)

        if changed:
            self.forecast_df.at[
                cell.forecast_date,
                cell.column_name,
            ] = value

        return changed

    def payable_balance(self, cell: CellId) -> Decimal:
        if cell.column_name is None:
            return Decimal('Inf')

        # TODO i don't like accessing these related fields by concatenating
        # because it means ':' is illegal in account names
        policy_min_allowed_balance_cell = CellId(cell.forecast_date,
                                          cell.column_name+": Policy Min Balance")
        policy_max_allowed_balance_cell = CellId(cell.forecast_date,
                                          cell.column_name+": Policy Max Balance")
        
        current_balance = Decimal(str(self.read(cell)))
        
        account_type = self.name_to_account_type[cell.column_name]

        if account_type == 'checking' or account_type == 'investment':
            max_allowed_balance = Decimal(self.name_to_account_max[cell.column_name])
            policy_max_allowed_balance = Decimal(str(self.read(policy_max_allowed_balance_cell)))
            return min(max_allowed_balance, policy_max_allowed_balance) - current_balance
        elif account_type == 'credit' or account_type == 'loan':
            min_allowed_balance = Decimal(self.name_to_account_min[cell.column_name])
            policy_min_allowed_balance = Decimal(str(self.read(policy_min_allowed_balance_cell)))
            return current_balance - max(min_allowed_balance, policy_min_allowed_balance)
        else:
            raise NotImplementedError #only payments from to checking, credit, loan and investment are supported

    def available_balance(self, cell: CellId) -> Decimal:
        # CellId.forecast_date, CellId.column_name

        if cell.column_name is None:
            return Decimal('Inf')

        # TODO i don't like accessing these related fields by concatenating
        # because it means ':' is illegal in account names
        policy_min_allowed_balance_cell = CellId(cell.forecast_date,
                                          cell.column_name+": Policy Min Balance")
        policy_max_allowed_balance_cell = CellId(cell.forecast_date,
                                          cell.column_name+": Policy Max Balance")
        
        
        current_balance = Decimal(str(self.read(cell)))
        
        account_type = self.name_to_account_type[cell.column_name]
        if account_type in {'checking', 'investment'}:
            min_allowed_balance = Decimal(self.name_to_account_min[cell.column_name])
            policy_min_allowed_balance = Decimal(str(self.read(policy_min_allowed_balance_cell)))
            return current_balance - max(min_allowed_balance, policy_min_allowed_balance)
        elif account_type == 'credit':
            max_allowed_balance = Decimal(self.name_to_account_max[cell.column_name])
            policy_max_allowed_balance = Decimal(str(self.read(policy_max_allowed_balance_cell)))
            return min(max_allowed_balance, policy_max_allowed_balance) - current_balance
        else:
            raise NotImplementedError #only payments from checking and credit accounts is supported
        
        

@dataclass(kw_only=True)
class ComputationNode(ABC):
    # reads: set[CellId] = field(
    #     init=False,
    #     default_factory=set,
    # )
    # writes: set[CellId] = field(
    #     init=False,
    #     default_factory=set,
    # )
    reads: set[CellId] = field(default_factory=set)
    writes: set[CellId] = field(default_factory=set)

    node_id: NodeId = field(init=False)
    priority: Priority = field(init=False)


    def __post_init__(self) -> None:
        self.node_id = self.semantic_id()

    @abstractmethod
    def semantic_id(self) -> NodeId:
        """Return the stable identity of this logical computation."""
        raise NotImplementedError

    @abstractmethod
    def execute(
        self,
        context: ExecutionContext,
    ) -> set[CellId]:
        """Execute the node and return cells whose values changed."""
        raise NotImplementedError

@dataclass
class WriteValueToOutputCellNode(ComputationNode):
    value: object

    def semantic_id(self) -> NodeId:
        output_cell = next(iter(self.writes))
        return (
            "initialize-cell",
            output_cell.forecast_date,
            output_cell.column_name,
        )

    def execute(
        self,
        context: ExecutionContext,
    ) -> set[CellId]:
        logger.info('execute WriteValueToOutputCellNode')
        output_cell = next(iter(self.writes))
        changed = context.write(output_cell, self.value)

        return {output_cell} if changed else set()
    
@dataclass
class CarryBalanceForwardNode(ComputationNode):

    def semantic_id(self) -> NodeId:
        input_cell = next(iter(self.reads))
        output_cell = next(iter(self.writes))
        return (
            "carry-cell",
            output_cell.column_name,
            input_cell.forecast_date,
            output_cell.forecast_date,
        )

    def execute(
        self,
        context: ExecutionContext,
    ) -> set[CellId]:
        logger.info('execute CarryBalanceForwardNode')
        input_cell = next(iter(self.reads))
        output_cell = next(iter(self.writes))

        value = context.read(input_cell)
        changed = context.write(output_cell, value)

        return {output_cell} if changed else set()
    
@dataclass
class CreditCardRolloverNode(ComputationNode):
    card_name: str
    rollover_date: date
    apr: Decimal
    minimum_payment_floor: Decimal

    def __post_init__(self) -> None:
        self.balance_cell = CellId(
            self.rollover_date, balance_column(self.card_name)
        )
        self.current_statement_cell = CellId(
            self.rollover_date,
            credit_current_statement_column(self.card_name),
        )
        self.previous_statement_cell = CellId(
            self.rollover_date,
            credit_previous_statement_column(self.card_name),
        )
        self.payment_balance_cell = CellId(
            self.rollover_date,
            credit_payment_balance_column(self.card_name),
        )
        self.end_previous_cycle_cell = CellId(
            self.rollover_date,
            credit_end_previous_cycle_column(self.card_name),
        )
        self.minimum_payment_cell = CellId(
            self.rollover_date,
            credit_minimum_payment_column(self.card_name),
        )
        self.minimum_payment_credit_cell = CellId(
            self.rollover_date,
            credit_minimum_payment_credit_column(self.card_name),
        )
        self.memo_directive_cell = CellId(
            self.rollover_date, "Memo Directives"
        )
        state_cells = {
            self.balance_cell,
            self.current_statement_cell,
            self.previous_statement_cell,
            self.payment_balance_cell,
            self.end_previous_cycle_cell,
            self.minimum_payment_cell,
            self.minimum_payment_credit_cell,
        }
        self.reads = state_cells | {
            CellId(
                self.rollover_date,
                previous_statement_policy_minimum_column(self.card_name),
            ),
            CellId(
                self.rollover_date,
                previous_statement_policy_maximum_column(self.card_name),
            ),
            self.memo_directive_cell,
        }
        self.writes = state_cells | {self.memo_directive_cell}
        super().__post_init__()

    def semantic_id(self) -> NodeId:
        return ("credit-rollover", self.card_name, self.rollover_date)

    def execute(self, context: ExecutionContext) -> set[CellId]:
        previous_statement = Decimal(
            str(context.read(self.previous_statement_cell))
        )
        current_statement = Decimal(
            str(context.read(self.current_statement_cell))
        )
        cycle_payments = Decimal(
            str(context.read(self.payment_balance_cell))
        )
        interest = previous_statement * (self.apr / Decimal("12"))
        next_statement = (
            previous_statement + current_statement + interest
        )
        principal_due = previous_statement * Decimal("0.01")
        next_minimum = (
            Decimal("0")
            if interest + principal_due == 0
            else min(
                next_statement,
                max(
                    self.minimum_payment_floor,
                    interest + principal_due,
                ),
            )
        )
        advance_payment_credit = min(cycle_payments, next_minimum)

        updates = {
            self.balance_cell: next_statement,
            self.previous_statement_cell: next_statement,
            self.current_statement_cell: Decimal("0"),
            self.payment_balance_cell: Decimal("0"),
            self.end_previous_cycle_cell: (
                previous_statement + cycle_payments
            ),
            self.minimum_payment_cell: next_minimum,
            self.minimum_payment_credit_cell: advance_payment_credit,
        }
        changed_cells = {
            cell
            for cell, value in updates.items()
            if context.write(cell, value)
        }
        if interest > 0:
            changed_cells.update(
                append_memo_directives(
                    context,
                    self.rollover_date,
                    [
                        "CC INTEREST "
                        f"({self.card_name}: Prev Stmt Bal +${interest})"
                    ],
                )
            )
        return changed_cells


@dataclass
class CreditCardMinimumPaymentNode(ComputationNode):
    source_account_name: str
    card_name: str
    payment_date: date
    minimum_payment: Decimal

    def __post_init__(self) -> None:
        self.source_balance_cell = CellId(
            self.payment_date, balance_column(self.source_account_name)
        )
        self.card_balance_cell = CellId(
            self.payment_date, balance_column(self.card_name)
        )
        self.current_statement_cell = CellId(
            self.payment_date,
            credit_current_statement_column(self.card_name),
        )
        self.previous_statement_cell = CellId(
            self.payment_date,
            credit_previous_statement_column(self.card_name),
        )
        self.minimum_payment_cell = CellId(
            self.payment_date,
            credit_minimum_payment_column(self.card_name),
        )
        self.minimum_payment_credit_cell = CellId(
            self.payment_date,
            credit_minimum_payment_credit_column(self.card_name),
        )
        self.memo_directive_cell = CellId(
            self.payment_date, "Memo Directives"
        )
        card_cells = {
            self.card_balance_cell,
            self.current_statement_cell,
            self.previous_statement_cell,
            self.minimum_payment_cell,
            self.minimum_payment_credit_cell,
        }
        self.reads = card_cells | {
            self.source_balance_cell,
            CellId(
                self.payment_date,
                policy_minimum_column(self.source_account_name),
            ),
            CellId(
                self.payment_date,
                policy_maximum_column(self.source_account_name),
            ),
            CellId(
                self.payment_date,
                previous_statement_policy_minimum_column(self.card_name),
            ),
            CellId(
                self.payment_date,
                previous_statement_policy_maximum_column(self.card_name),
            ),
            self.memo_directive_cell,
        }
        self.writes = card_cells | {
            self.source_balance_cell,
            self.memo_directive_cell,
        }
        super().__post_init__()

    def semantic_id(self) -> NodeId:
        return (
            "credit-minimum-payment",
            self.source_account_name,
            self.card_name,
            self.payment_date,
        )

    def execute(self, context: ExecutionContext) -> set[CellId]:
        minimum_payment = Decimal(
            str(context.read(self.minimum_payment_cell))
        )
        payment_credit = Decimal(
            str(context.read(self.minimum_payment_credit_cell))
        )
        payment_due = max(
            Decimal("0"),
            minimum_payment - payment_credit,
        )
        if payment_due == 0:
            return set()

        source_available = context.available_balance(
            self.source_balance_cell
        )
        if payment_due > source_available:
            raise SpeculativeTransactionRejected(
                node_id=self.node_id,
                requested=payment_due,
                available=source_available,
                reason="Insufficient funds for credit-card minimum payment",
            )

        source_balance = Decimal(
            str(context.read(self.source_balance_cell))
        )
        card_balance = Decimal(str(context.read(self.card_balance_cell)))
        previous_statement = Decimal(
            str(context.read(self.previous_statement_cell))
        )
        current_statement = Decimal(
            str(context.read(self.current_statement_cell))
        )
        payment_due = min(payment_due, card_balance)
        previous_payment = min(payment_due, previous_statement)
        current_payment = payment_due - previous_payment

        updates = {
            self.source_balance_cell: source_balance - payment_due,
            self.card_balance_cell: card_balance - payment_due,
            self.previous_statement_cell: (
                previous_statement - previous_payment
            ),
            self.current_statement_cell: (
                current_statement - current_payment
            ),
        }
        changed_cells = {
            cell
            for cell, value in updates.items()
            if context.write(cell, value)
        }
        changed_cells.update(
            append_memo_directives(
                context,
                self.payment_date,
                    [
                        "CC MIN PAYMENT "
                        f"({self.card_name}: Prev Stmt Bal "
                        f"-${payment_due:.2f})",
                        "CC MIN PAYMENT "
                        f"({self.source_account_name} -${payment_due:.2f})",
                    ],
            )
        )
        return changed_cells


@dataclass
class LoanMinimumPaymentNode(ComputationNode):
    source_account_name: str
    loan_name: str
    payment_date: date
    minimum_payment: Decimal

    def __post_init__(self) -> None:
        self.source_balance_cell = CellId(
            self.payment_date, balance_column(self.source_account_name)
        )
        self.loan_balance_cell = CellId(
            self.payment_date, balance_column(self.loan_name)
        )
        self.principal_cell = CellId(
            self.payment_date, loan_principal_column(self.loan_name)
        )
        self.interest_cell = CellId(
            self.payment_date, loan_interest_column(self.loan_name)
        )
        self.payment_balance_cell = CellId(
            self.payment_date,
            loan_payment_balance_column(self.loan_name),
        )
        self.memo_directive_cell = CellId(
            self.payment_date, "Memo Directives"
        )
        loan_cells = {
            self.loan_balance_cell,
            self.principal_cell,
            self.interest_cell,
            self.payment_balance_cell,
        }
        self.reads = loan_cells | {
            self.source_balance_cell,
            CellId(
                self.payment_date,
                policy_minimum_column(self.source_account_name),
            ),
            CellId(
                self.payment_date,
                policy_maximum_column(self.source_account_name),
            ),
            self.memo_directive_cell,
        }
        self.writes = loan_cells | {
            self.source_balance_cell,
            self.memo_directive_cell,
        }
        super().__post_init__()

    def semantic_id(self) -> NodeId:
        return (
            "loan-minimum-payment",
            self.source_account_name,
            self.loan_name,
            self.payment_date,
        )

    def execute(self, context: ExecutionContext) -> set[CellId]:
        cycle_payments = Decimal(
            str(context.read(self.payment_balance_cell))
        )
        loan_balance = Decimal(str(context.read(self.loan_balance_cell)))
        payment_due = min(
            max(Decimal("0"), self.minimum_payment - cycle_payments),
            loan_balance,
        )
        if payment_due == 0:
            return set()

        source_available = context.available_balance(
            self.source_balance_cell
        )
        if payment_due > source_available:
            raise SpeculativeTransactionRejected(
                node_id=self.node_id,
                requested=payment_due,
                available=source_available,
                reason="Insufficient funds for loan minimum payment",
            )

        source_balance = Decimal(
            str(context.read(self.source_balance_cell))
        )
        interest_balance = Decimal(str(context.read(self.interest_cell)))
        principal_balance = Decimal(str(context.read(self.principal_cell)))
        interest_payment = min(payment_due, interest_balance)
        principal_payment = min(
            payment_due - interest_payment,
            principal_balance,
        )
        executed_payment = interest_payment + principal_payment

        updates = {
            self.source_balance_cell: source_balance - executed_payment,
            self.loan_balance_cell: loan_balance - executed_payment,
            self.interest_cell: interest_balance - interest_payment,
            self.principal_cell: principal_balance - principal_payment,
        }
        changed_cells = {
            cell
            for cell, value in updates.items()
            if context.write(cell, value)
        }
        directives: list[str] = []
        if interest_payment > 0:
            directives.append(
                "LOAN MIN PAYMENT "
                f"({self.loan_name}: Interest -${interest_payment:.2f})"
            )
        if principal_payment > 0:
            directives.append(
                "LOAN MIN PAYMENT "
                f"({self.loan_name}: Principal Balance "
                f"-${principal_payment:.2f})"
            )
        if executed_payment > 0:
            directives.append(
                "LOAN MIN PAYMENT "
                f"({self.source_account_name} -${executed_payment:.2f})"
            )
        changed_cells.update(
            append_memo_directives(
                context,
                self.payment_date,
                directives,
            )
        )
        return changed_cells


@dataclass
class LoanSurplusPaymentNode(ComputationNode):
    source_account_name: str
    loan_name: str
    payment_date: date
    strategy: str
    occurrence_key: Hashable

    def __post_init__(self) -> None:
        source_balance = CellId(
            self.payment_date, balance_column(self.source_account_name)
        )
        loan_cells = {
            CellId(self.payment_date, balance_column(self.loan_name)),
            CellId(
                self.payment_date, loan_principal_column(self.loan_name)
            ),
            CellId(self.payment_date, loan_interest_column(self.loan_name)),
            CellId(
                self.payment_date, loan_payment_balance_column(self.loan_name)
            ),
        }
        self.reads = loan_cells | {
            source_balance,
            CellId(
                self.payment_date,
                policy_minimum_column(self.source_account_name),
            ),
            CellId(
                self.payment_date,
                policy_maximum_column(self.source_account_name),
            ),
        }
        self.writes = loan_cells | {source_balance}
        super().__post_init__()

    def semantic_id(self) -> NodeId:
        return (
            "loan-surplus-payment",
            self.source_account_name,
            self.loan_name,
            self.strategy,
            self.payment_date,
            self.occurrence_key,
        )

    def execute(self, context: ExecutionContext) -> set[CellId]:
        raise NotImplementedError(
            "LoanSurplusPaymentNode execution is not implemented"
        )


@dataclass
class LoanInterestAccrualNode(ComputationNode):
    loan_name: str
    accrual_date: date
    apr: Decimal
    interest_interval: str

    def __post_init__(self) -> None:
        self.principal_cell = CellId(
            self.accrual_date, loan_principal_column(self.loan_name)
        )
        self.interest_cell = CellId(
            self.accrual_date, loan_interest_column(self.loan_name)
        )
        self.balance_cell = CellId(
            self.accrual_date, balance_column(self.loan_name)
        )
        self.memo_directive_cell = CellId(
            self.accrual_date, "Memo Directives"
        )
        self.reads = {
            self.principal_cell,
            self.interest_cell,
            self.balance_cell,
            self.memo_directive_cell,
        }
        self.writes = {
            self.interest_cell,
            self.balance_cell,
            self.memo_directive_cell,
        }
        super().__post_init__()

    def semantic_id(self) -> NodeId:
        return ("loan-interest-accrual", self.loan_name, self.accrual_date)

    def execute(self, context: ExecutionContext) -> set[CellId]:
        divisors = {
            "daily": Decimal("365.25"),
            "monthly": Decimal("12"),
            "quarterly": Decimal("4"),
            "annually": Decimal("1"),
        }
        try:
            divisor = divisors[self.interest_interval]
        except KeyError as error:
            raise ValueError(
                "Unsupported loan interest interval: "
                f"{self.interest_interval!r}"
            ) from error

        principal = Decimal(str(context.read(self.principal_cell)))
        interest_balance = Decimal(str(context.read(self.interest_cell)))
        loan_balance = Decimal(str(context.read(self.balance_cell)))
        interest_accrued = principal * self.apr / divisor

        changed_cells: set[CellId] = set()
        if context.write(
            self.interest_cell,
            interest_balance + interest_accrued,
        ):
            changed_cells.add(self.interest_cell)
        if context.write(
            self.balance_cell,
            loan_balance + interest_accrued,
        ):
            changed_cells.add(self.balance_cell)
        if interest_accrued > 0:
            changed_cells.update(
                append_memo_directives(
                    context,
                    self.accrual_date,
                    [
                        "LOAN INTEREST "
                        f"({self.loan_name}: Interest "
                        f"+${interest_accrued:.2f})"
                    ],
                )
            )
        return changed_cells


@dataclass
class InvestmentAccrualNode(ComputationNode):
    investment_name: str
    accrual_date: date
    apr: Decimal

    def __post_init__(self) -> None:
        self.balance_cell = CellId(
            self.accrual_date, balance_column(self.investment_name)
        )
        self.memo_directive_cell = CellId(
            self.accrual_date, "Memo Directives"
        )
        self.reads = {self.balance_cell, self.memo_directive_cell}
        self.writes = {self.balance_cell, self.memo_directive_cell}
        super().__post_init__()

    def semantic_id(self) -> NodeId:
        return (
            "investment-accrual",
            self.investment_name,
            self.accrual_date,
        )

    def execute(self, context: ExecutionContext) -> set[CellId]:
        # Legacy models deterministic investment growth as daily compound
        # interest. Accrual runs before same-day contributions or withdrawals,
        # so today's return is based on the opening investment balance.
        opening_balance = Decimal(str(context.read(self.balance_cell)))
        daily_growth = opening_balance * self.apr / Decimal("365.25")
        if daily_growth == 0:
            return set()

        changed_cells: set[CellId] = set()
        if context.write(
            self.balance_cell,
            opening_balance + daily_growth,
        ):
            changed_cells.add(self.balance_cell)
        changed_cells.update(
            append_memo_directives(
                context,
                self.accrual_date,
                [
                    "INVESTMENT RETURN "
                    f"({self.investment_name} +${daily_growth:.2f})"
                ],
            )
        )
        return changed_cells

class SpeculativeTransactionRejected(Exception):
    def __init__(
        self,
        *,
        node_id,
        requested,
        available,
        reason,
    ):
        self.node_id = node_id
        self.requested = requested
        self.available = available
        self.reason = reason
        super().__init__(
            f"{node_id!r} rejected: requested={requested}, "
            f"available={available}, reason={reason}"
        )


def append_memo_directives(
    context: ExecutionContext,
    forecast_date: date,
    directives: list[str],
) -> set[CellId]:
    """Append non-empty directives using the legacy ``; `` separator."""
    additions = [directive.strip() for directive in directives if directive.strip()]
    if not additions:
        return set()

    memo_cell = CellId(forecast_date, "Memo Directives")
    existing = [
        directive.strip()
        for directive in str(context.read(memo_cell)).split(";")
        if directive.strip()
    ]
    rendered = "; ".join([*existing, *additions])
    return {memo_cell} if context.write(memo_cell, rendered) else set()


@dataclass
class TransactionNode(ComputationNode):
    amount: Decimal
    account_from: str | None
    account_to: str | None
    priority_level: int
    transaction_date: date
    memo: str
    occurrence_ordinal: int
    deferrable: bool = False
    partial_payment_allowed: bool = False
    income_flag: bool = False

    def __post_init__(self) -> None:
        self.from_cell = (
            CellId(
                forecast_date=self.transaction_date,
                column_name=self.account_from,
            )
            if self.account_from is not None else None
        )
        self.to_cell = (
            CellId(
                forecast_date=self.transaction_date,
                column_name=self.account_to,
            )
            if self.account_to is not None else None
        )
        self.reads = {
            cell for cell in (self.from_cell, self.to_cell)
            if cell is not None
        }
        self.writes = set(self.reads)
        self.memo_cell = CellId(
            forecast_date=self.transaction_date,
            column_name="Memo",
        )
        if self.from_cell is None or self.to_cell is None:
            self.reads.add(self.memo_cell)
            self.writes.add(self.memo_cell)
        self.memo_directive_cell = None
        if self.income_flag:
            self.memo_directive_cell = CellId(
                forecast_date=self.transaction_date,
                column_name="Memo Directives",
            )
            self.reads.add(self.memo_directive_cell)
            self.writes.add(self.memo_directive_cell)
        super().__post_init__()

    def semantic_id(self) -> NodeId:
        occurrence_key = (
            self.memo,
            str(self.amount),
            self.account_from,
            self.account_to,
            self.income_flag,
            self.occurrence_ordinal,
        )
        return (
            "transaction",
            self.transaction_date,
            self.priority_level,
            occurrence_key,
        )

    def execute(self, context: ExecutionContext) -> set[CellId]:
        logger.info('execute TransactionNode')

        changed_cells: set[CellId] = set()

        if self.from_cell is not None: #if the txn is not income

            from_available_balance = context.available_balance(self.from_cell)
            
            # fail
            if self.amount > from_available_balance:
                raise SpeculativeTransactionRejected(node_id=self.node_id, 
                                                     requested=self.amount, 
                                                     available=from_available_balance, 
                                                     reason="Insufficient funds")

        if self.to_cell is not None: #if money is spent
            # print('self.to_cell.column_name')
            # print(self.to_cell.column_name)
            to_payable_balance = context.payable_balance(self.to_cell)
            if self.amount > to_payable_balance:
                raise SpeculativeTransactionRejected(node_id=self.node_id, 
                                                     requested=self.amount, 
                                                     available=to_payable_balance, 
                                                     reason="Debt Overpayment")

        #I believe these potentially unbound errors are erroneous
        if self.from_cell is not None:
            from_balance = Decimal(context.read(self.from_cell))
            if context.write( self.from_cell, from_balance - self.amount):
                changed_cells.add(self.from_cell)

        if self.to_cell is not None:
            to_balance = Decimal(context.read(self.to_cell))
            if context.write( self.to_cell, to_balance + self.amount ):
                changed_cells.add(self.to_cell)

        memo_entry = None
        if self.from_cell is None and self.to_cell is not None:
            memo_entry = (
                f"{self.memo} "
                f"({self.to_cell.column_name} +${self.amount:.2f})"
            )
        elif self.from_cell is not None and self.to_cell is None:
            memo_entry = (
                f"{self.memo} "
                f"({self.from_cell.column_name} -${self.amount:.2f})"
            )

        if memo_entry is not None:
            existing_memo = str(context.read(self.memo_cell)).strip()
            rendered_memo = (
                f"{existing_memo}; {memo_entry}"
                if existing_memo
                else memo_entry
            )
            if context.write(self.memo_cell, rendered_memo):
                changed_cells.add(self.memo_cell)

        # Ordinary spending does not produce memo directives.

        # Income memo directives
        if self.income_flag:
            assert self.memo_directive_cell is not None
            assert self.to_cell is not None
            existing_memo_directive = str(
                context.read(self.memo_directive_cell)
            ).strip()
            income_directive = (
                f"INCOME "
                f"({self.to_cell.column_name} +${self.amount:.2f})"
            )
            rendered_memo_directive = (
                f"{existing_memo_directive}; {income_directive}"
                if existing_memo_directive
                else income_directive
            )
            if context.write(
                self.memo_directive_cell, rendered_memo_directive
            ):
                changed_cells.add(self.memo_directive_cell)

        return changed_cells


@dataclass
class CreditPurchaseNode(TransactionNode):
    """Post a purchase to a card's debt and current statement balances."""

    def __post_init__(self) -> None:
        super().__post_init__()
        assert self.account_from is not None
        self.current_statement_cell = CellId(
            self.transaction_date,
            credit_current_statement_column(self.account_from),
        )
        self.reads.add(self.current_statement_cell)
        self.writes.add(self.current_statement_cell)

    def semantic_id(self) -> NodeId:
        return (
            "credit-purchase",
            self.transaction_date,
            self.priority_level,
            self.memo,
            str(self.amount),
            self.account_from,
            self.occurrence_ordinal,
        )

    def execute(self, context: ExecutionContext) -> set[CellId]:
        assert self.from_cell is not None
        available_credit = context.available_balance(self.from_cell)
        if self.amount > available_credit:
            raise SpeculativeTransactionRejected(
                node_id=self.node_id,
                requested=self.amount,
                available=available_credit,
                reason="Credit limit exceeded",
            )

        changed_cells: set[CellId] = set()
        card_balance = Decimal(str(context.read(self.from_cell)))
        current_statement = Decimal(
            str(context.read(self.current_statement_cell))
        )
        if context.write(self.from_cell, card_balance + self.amount):
            changed_cells.add(self.from_cell)
        if context.write(
            self.current_statement_cell,
            current_statement + self.amount,
        ):
            changed_cells.add(self.current_statement_cell)

        existing_memo = str(context.read(self.memo_cell)).strip()
        memo_entry = (
            f"{self.memo} "
            f"({self.from_cell.column_name} -${self.amount:.2f})"
        )
        rendered_memo = (
            f"{existing_memo}; {memo_entry}"
            if existing_memo
            else memo_entry
        )
        if context.write(self.memo_cell, rendered_memo):
            changed_cells.add(self.memo_cell)
        return changed_cells


@dataclass
class CreditCardSpecifiedAmountPaymentNode(TransactionNode):
    """Pay card debt, allocating to previous statement before current."""

    def __post_init__(self) -> None:
        super().__post_init__()
        assert self.account_to is not None
        self.previous_statement_cell = CellId(
            self.transaction_date,
            credit_previous_statement_column(self.account_to),
        )
        self.current_statement_cell = CellId(
            self.transaction_date,
            credit_current_statement_column(self.account_to),
        )
        self.payment_balance_cell = CellId(
            self.transaction_date,
            credit_payment_balance_column(self.account_to),
        )
        subaccount_cells = {
            self.previous_statement_cell,
            self.current_statement_cell,
            self.payment_balance_cell,
        }
        self.reads.update(subaccount_cells)
        self.writes.update(subaccount_cells)

    def semantic_id(self) -> NodeId:
        return (
            "credit-specified-payment",
            self.transaction_date,
            self.priority_level,
            self.memo,
            str(self.amount),
            self.account_from,
            self.account_to,
            self.occurrence_ordinal,
        )

    def execute(self, context: ExecutionContext) -> set[CellId]:
        assert self.from_cell is not None
        assert self.to_cell is not None
        available_cash = context.available_balance(self.from_cell)
        payable_debt = context.payable_balance(self.to_cell)
        if self.amount > available_cash:
            raise SpeculativeTransactionRejected(
                node_id=self.node_id,
                requested=self.amount,
                available=available_cash,
                reason="Insufficient payment funds",
            )
        if self.amount > payable_debt:
            raise SpeculativeTransactionRejected(
                node_id=self.node_id,
                requested=self.amount,
                available=payable_debt,
                reason="Credit-card overpayment",
            )

        source_balance = Decimal(str(context.read(self.from_cell)))
        card_balance = Decimal(str(context.read(self.to_cell)))
        previous_statement = Decimal(
            str(context.read(self.previous_statement_cell))
        )
        current_statement = Decimal(
            str(context.read(self.current_statement_cell))
        )
        payment_balance = Decimal(
            str(context.read(self.payment_balance_cell))
        )
        previous_payment = min(self.amount, previous_statement)
        current_payment = self.amount - previous_payment

        updates = {
            self.from_cell: source_balance - self.amount,
            self.to_cell: card_balance - self.amount,
            self.previous_statement_cell: (
                previous_statement - previous_payment
            ),
            self.current_statement_cell: current_statement - current_payment,
            self.payment_balance_cell: payment_balance + self.amount,
        }
        changed_cells = {
            cell
            for cell, value in updates.items()
            if context.write(cell, value)
        }
        changed_cells.update(
            append_memo_directives(
                context,
                self.transaction_date,
                [
                    "ADDTL CC PAYMENT "
                    f"({self.account_to} -${self.amount:.2f})"
                ],
            )
        )
        return changed_cells


@dataclass
class LoanSpecifiedAmountPaymentNode(TransactionNode):
    """Pay accrued loan interest first, then reduce principal."""

    def __post_init__(self) -> None:
        super().__post_init__()
        assert self.account_to is not None
        self.principal_cell = CellId(
            self.transaction_date,
            loan_principal_column(self.account_to),
        )
        self.interest_cell = CellId(
            self.transaction_date,
            loan_interest_column(self.account_to),
        )
        self.payment_balance_cell = CellId(
            self.transaction_date,
            loan_payment_balance_column(self.account_to),
        )
        subaccount_cells = {
            self.principal_cell,
            self.interest_cell,
            self.payment_balance_cell,
        }
        self.reads.update(subaccount_cells)
        self.writes.update(subaccount_cells)

    def semantic_id(self) -> NodeId:
        return (
            "loan-specified-payment",
            self.transaction_date,
            self.priority_level,
            self.memo,
            str(self.amount),
            self.account_from,
            self.account_to,
            self.occurrence_ordinal,
        )

    def execute(self, context: ExecutionContext) -> set[CellId]:
        assert self.from_cell is not None
        assert self.to_cell is not None
        available_cash = context.available_balance(self.from_cell)
        payable_debt = context.payable_balance(self.to_cell)
        if self.amount > available_cash:
            raise SpeculativeTransactionRejected(
                node_id=self.node_id,
                requested=self.amount,
                available=available_cash,
                reason="Insufficient payment funds",
            )
        if self.amount > payable_debt:
            raise SpeculativeTransactionRejected(
                node_id=self.node_id,
                requested=self.amount,
                available=payable_debt,
                reason="Loan overpayment",
            )

        source_balance = Decimal(str(context.read(self.from_cell)))
        loan_balance = Decimal(str(context.read(self.to_cell)))
        interest_balance = Decimal(str(context.read(self.interest_cell)))
        principal_balance = Decimal(str(context.read(self.principal_cell)))
        payment_balance = Decimal(
            str(context.read(self.payment_balance_cell))
        )
        interest_payment = min(self.amount, interest_balance)
        principal_payment = self.amount - interest_payment

        remaining_loan_balance = loan_balance - self.amount
        remaining_interest = interest_balance - interest_payment
        remaining_principal = principal_balance - principal_payment
        remaining_payment_balance = payment_balance + self.amount
        if remaining_loan_balance <= Decimal("0.005"):
            remaining_loan_balance = Decimal("0")
            remaining_interest = Decimal("0")
            remaining_principal = Decimal("0")
            remaining_payment_balance = Decimal("0")

        updates = {
            self.from_cell: source_balance - self.amount,
            self.to_cell: remaining_loan_balance,
            self.interest_cell: remaining_interest,
            self.principal_cell: remaining_principal,
            self.payment_balance_cell: remaining_payment_balance,
        }
        return {
            cell
            for cell, value in updates.items()
            if context.write(cell, value)
        }


@dataclass
class InvestmentTransferNode(TransactionNode):
    """Move cash into or out of one investment account.

    TransactionNode already owns the balance-boundary checks and the two
    balance writes. This specialization adds the presentation artifacts that
    distinguish an investment transfer from ordinary checking-to-checking
    movement.
    """

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.account_from is None or self.account_to is None:
            raise ValueError(
                "Investment transfers require two named account endpoints"
            )
        self.memo_cell = CellId(self.transaction_date, "Memo")
        self.memo_directive_cell = CellId(
            self.transaction_date, "Memo Directives"
        )
        self.reads.update({self.memo_cell, self.memo_directive_cell})
        self.writes.update({self.memo_cell, self.memo_directive_cell})

    def semantic_id(self) -> NodeId:
        return (
            "investment-transfer",
            self.transaction_date,
            self.priority_level,
            self.memo,
            str(self.amount),
            self.account_from,
            self.account_to,
            self.occurrence_ordinal,
        )

    def execute(self, context: ExecutionContext) -> set[CellId]:
        changed_cells = super().execute(context)
        assert self.from_cell is not None
        assert self.to_cell is not None

        # Transfers are displayed from the source account's perspective even
        # though both endpoint balances are changed by the graph node.
        existing_memo = str(context.read(self.memo_cell)).strip()
        memo_entry = (
            f"{self.memo} "
            f"({self.account_from} -${self.amount:.2f})"
        )
        rendered_memo = (
            f"{existing_memo}; {memo_entry}"
            if existing_memo
            else memo_entry
        )
        if context.write(self.memo_cell, rendered_memo):
            changed_cells.add(self.memo_cell)

        from_type = context.name_to_account_type[self.account_from]
        to_type = context.name_to_account_type[self.account_to]
        if to_type == "investment":
            directive = (
                "INVESTMENT CONTRIBUTION "
                f"({self.account_to} +${self.amount:.2f})"
            )
        elif from_type == "investment":
            directive = (
                "INVESTMENT WITHDRAWAL "
                f"({self.account_to} +${self.amount:.2f})"
            )
        else:
            raise ValueError(
                "InvestmentTransferNode requires an investment endpoint"
            )
        changed_cells.update(
            append_memo_directives(
                context,
                self.transaction_date,
                [directive],
            )
        )
        return changed_cells


@dataclass
class CarryValueNode(ComputationNode):
    source: CellId
    destination: CellId

    def __post_init__(self) -> None:
        self.reads = {self.source}
        self.writes = {self.destination}
        super().__post_init__()

    def semantic_id(self) -> NodeId:
        return (
            "carry-cell",
            self.destination.column_name,
            self.source.forecast_date,
            self.destination.forecast_date,
        )

    def execute(self, context: ExecutionContext) -> set[CellId]:
        logger.info('execute CarryValueNode')
        value = context.read(self.source)
        changed = context.write(self.destination, value)

        return {self.destination} if changed else set()

class ExecutionEngine:

    @classmethod
    def _carry_accounts_forward(
        cls,
        context: ExecutionContext,
        account_df: pd.DataFrame,
        previous_date: date,
        forecast_date: date,
    ) -> None:
        day_number = (forecast_date - context.initial_conditions.start_date).days

        for sequence, (_, account) in enumerate(account_df.iterrows()):
            account_name = account["Name"]

            source = CellId(
                forecast_date=previous_date,
                column_name=account_name,
            )

            destination = CellId(
                forecast_date=forecast_date,
                column_name=account_name,
            )

            node = CarryValueNode(
                source=source,
                destination=destination,
            )

            context.register(
                day_index=day_number,
                priority_level=0,
                node=node,
            )
            context.enqueue(node.node_id)

    @classmethod
    def build_initial_account_nodes(
        cls,
        context: ExecutionContext,
    ) -> None:
        accounts = context.initial_conditions.initial_account_set.accounts

        for account in accounts:
            for column_name, initial_value in account_initial_cell_values(
                account
            ).items():
                output_cell = CellId(
                    forecast_date=context.initial_conditions.start_date,
                    column_name=column_name,
                )
                node = WriteValueToOutputCellNode(
                    value=initial_value,
                    writes={output_cell},
                )

                context.register(
                    day_index=0,
                    priority_level=0,
                    node=node,
                )
                context.enqueue(node.node_id)

    @classmethod
    def build_balance_carry_nodes_for_day(
        cls,
        context: ExecutionContext,
        day_index: int,
    ) -> None:
        """
        Build carry-forward nodes for each account on the given day.

        Account balances and their active policy bounds persist until another
        node changes them.
        """
        if day_index <= 0:
            raise ValueError("Carry-forward nodes require day_index > 0.")

        current_date = context.forecast_df.index[day_index]
        previous_date = context.forecast_df.index[day_index - 1]

        accounts = context.initial_conditions.initial_account_set.accounts

        for account in accounts:
            # Every cell initialized for an account represents persistent
            # state. This includes subtype ledgers such as credit statements
            # and loan principal/interest—not merely the headline balance.
            # Account-specific event nodes overwrite the relevant destination
            # cells after these carry nodes have established the day's opening
            # state.
            for column_name in account_initial_cell_values(account):
                previous_cell = CellId(
                    forecast_date=previous_date,
                    column_name=column_name,
                )
                current_cell = CellId(
                    forecast_date=current_date,
                    column_name=column_name,
                )
                node = CarryValueNode(
                    source=previous_cell,
                    destination=current_cell,
                )

                context.register(
                    day_index=day_index,
                    priority_level=0,
                    node=node,
                )
                context.enqueue(node.node_id)

    @staticmethod
    def _account_event_dates(
        *,
        first_date: date,
        last_date: date,
        interval: str,
    ) -> list[date]:
        """Generate configured event dates without scanning forecast rows."""
        if first_date > last_date:
            return []

        if interval == "daily":
            return [
                timestamp.date()
                for timestamp in pd.date_range(
                    first_date,
                    last_date,
                    freq="D",
                )
            ]
        if interval == "monthly":
            # Recompute each occurrence from the original anchor day. Adding
            # DateOffset repeatedly would turn Jan 31 -> Feb 28 -> Mar 28,
            # permanently drifting after the first short month.
            dates: list[date] = []
            anchor = pd.Timestamp(first_date)
            month_offset = 0
            while True:
                absolute_month = (
                    anchor.year * 12
                    + anchor.month
                    - 1
                    + month_offset
                )
                year, zero_based_month = divmod(absolute_month, 12)
                month = zero_based_month + 1
                first_of_month = pd.Timestamp(year, month, 1)
                event_timestamp = pd.Timestamp(
                    year,
                    month,
                    min(anchor.day, first_of_month.days_in_month),
                )
                if event_timestamp.date() > last_date:
                    break
                dates.append(event_timestamp.date())
                month_offset += 1
            return dates

        raise ValueError(f"Unsupported graph-v2 event interval: {interval!r}")

    @classmethod
    def build_account_semantic_nodes(
        cls,
        context: ExecutionContext,
    ) -> None:
        """Register account computations only on dates where they can run.

        Registration is grouped in legacy execution order. On a shared date,
        semantic nodes therefore run after opening-state carries and in this
        order: card rollover, loan interest, investment return, loan minimum,
        and card minimum. Scheduled transactions are registered afterward.

        Daily loan/investment behavior still has one event per active day; the
        improvement is that monthly events are generated from their anchors
        and no account-type checks are performed for every forecast row.
        """
        forecast_start = context.initial_conditions.start_date
        forecast_end = context.initial_conditions.end_date
        first_executable_date = forecast_start + datetime.timedelta(days=1)
        primary_checking = (
            context.initial_conditions.initial_account_set
            .primary_checking_account_name
        )
        accounts = (
            context.initial_conditions.initial_account_set.accounts
        )

        def register(node: ComputationNode, event_date: date) -> None:
            day_index = (event_date - forecast_start).days
            context.register(
                day_index=day_index,
                priority_level=0,
                node=node,
            )
            context.enqueue(node.node_id)

        credit_accounts = [
            account for account in accounts
            if account.account_type == "credit"
        ]
        loan_accounts = [
            account for account in accounts
            if account.account_type == "loan"
        ]
        investment_accounts = [
            account for account in accounts
            if account.account_type == "investment"
        ]

        # Credit interest and statement rollover occur at monthly billing
        # boundaries.
        for account in credit_accounts:
            billing_start = account.billing_state.billing_cycle_start_date
            for event_date in cls._account_event_dates(
                first_date=billing_start,
                last_date=forecast_end,
                interval="monthly",
            ):
                if event_date < first_executable_date:
                    continue
                register(
                    CreditCardRolloverNode(
                        card_name=account.name,
                        rollover_date=event_date,
                        apr=Decimal(str(account.billing_state.apr)),
                        minimum_payment_floor=Decimal(
                            str(account.billing_state.minimum_payment_floor)
                        ),
                    ),
                    event_date,
                )

        # Loan interest is accrued before same-day minimum payments and
        # user-authored transactions.
        for account in loan_accounts:
            billing_start = account.billing_state.billing_cycle_start_date
            first_accrual = max(first_executable_date, billing_start)
            for event_date in cls._account_event_dates(
                first_date=first_accrual,
                last_date=forecast_end,
                interval=account.billing_state.interest_interval,
            ):
                register(
                    LoanInterestAccrualNode(
                        loan_name=account.name,
                        accrual_date=event_date,
                        apr=Decimal(str(account.billing_state.apr)),
                        interest_interval=(
                            account.billing_state.interest_interval
                        ),
                    ),
                    event_date,
                )

        # Investments compound daily once their configured accrual period is
        # active.
        for account in investment_accounts:
            billing_start = account.billing_state.billing_cycle_start_date
            first_accrual = max(first_executable_date, billing_start)
            for event_date in cls._account_event_dates(
                first_date=first_accrual,
                last_date=forecast_end,
                interval="daily",
            ):
                register(
                    InvestmentAccrualNode(
                        investment_name=account.name,
                        accrual_date=event_date,
                        apr=Decimal(str(account.billing_state.apr)),
                    ),
                    event_date,
                )

        # Debt minimum payments occur on billing boundaries. Their actual
        # executable amount remains the node's responsibility because prior
        # payments can reduce the amount due.
        for account in loan_accounts:
            billing_start = account.billing_state.billing_cycle_start_date
            for event_date in cls._account_event_dates(
                first_date=billing_start,
                last_date=forecast_end,
                interval="monthly",
            ):
                if event_date < first_executable_date:
                    continue
                register(
                    LoanMinimumPaymentNode(
                        source_account_name=primary_checking,
                        loan_name=account.name,
                        payment_date=event_date,
                        minimum_payment=Decimal(
                            str(account.billing_state.minimum_payment)
                        ),
                    ),
                    event_date,
                )

        for account in credit_accounts:
            billing_start = account.billing_state.billing_cycle_start_date
            for event_date in cls._account_event_dates(
                first_date=billing_start,
                last_date=forecast_end,
                interval="monthly",
            ):
                if event_date < first_executable_date:
                    continue
                register(
                    CreditCardMinimumPaymentNode(
                        source_account_name=primary_checking,
                        card_name=account.name,
                        payment_date=event_date,
                        minimum_payment=Decimal(
                            str(account.billing_state.minimum_payment)
                        ),
                    ),
                    event_date,
                )

    # # this will not be used in practice
    # @classmethod
    # def execute_all(cls, context: ExecutionContext) -> None:
    #     for node_id in context.registration_order:
    #         node = context.nodes[node_id]
    #         node.execute(context)

    @classmethod
    def propagate(cls, context: ExecutionContext) -> None:
        while context.pending_heap:
            node = context.pop_pending()

            logger.debug(
                "Executing %s at %s",
                type(node).__name__,
                node.priority,
            )

            # TODO use memoization
            # simply checks against a set
            # where the keys are - node_id and the input params
            # the payoff of this will be negligible for small operations
            # such as carring the balance forward, however, more expensive
            # operations, such as calculating payments under multiple contraints
            # are worth memoizing
            changed_cells = node.execute(context)

            for cell in changed_cells:
                for dependent_id in context.readers.get(cell, set()):
                    dependent = context.nodes[dependent_id]

                    if dependent.priority <= node.priority:
                        continue

                    context.enqueue(dependent_id)

    @classmethod
    def assemble_transaction_node(
        cls,
        line_item_row: pd.Series,
        context: ExecutionContext,
    ) -> TransactionNode:
        # Line-item and memo-rule data first produce a neutral transaction
        # request. _specialize_transaction_node then chooses the node that
        # understands the affected account's internal ledger. Policy-generated
        # surplus payments remain separate node types because their amount and
        # target selection are not specified by a single scheduled line item.

        priority_level = int(line_item_row["Priority"])
        transaction_date = line_item_row["Date"]

        memo_rule_set = context.initial_conditions.initial_memo_rule_set
        matching_memo_rule = memo_rule_set.findMatchingMemoRule(txn_memo=line_item_row["Memo"],
                                                                            transaction_priority=priority_level)
        occurrence_base: tuple[Hashable, ...] = (
            transaction_date,
            priority_level,
            str(line_item_row["Memo"]),
            str(line_item_row["Amount"]),
            matching_memo_rule.account_from,
            matching_memo_rule.account_to,
            bool(line_item_row["Income_Flag"]),
        )
        occurrence_ordinal = context.occurrence_counts.get(
            occurrence_base, 0
        )
        context.occurrence_counts[occurrence_base] = (
            occurrence_ordinal + 1
        )

        transaction_node = TransactionNode(
            amount=Decimal(str(line_item_row["Amount"])),
            account_from=matching_memo_rule.account_from,
            account_to=matching_memo_rule.account_to,
            transaction_date=transaction_date,
            priority_level=priority_level,
            memo=str(line_item_row["Memo"]),
            deferrable=bool(line_item_row["Deferrable"]),
            partial_payment_allowed=bool(line_item_row["Partial_Payment_Allowed"]),
            income_flag=bool(line_item_row["Income_Flag"]),
            occurrence_ordinal=occurrence_ordinal,
        )

        return cls._specialize_transaction_node(
            transaction_node,
            context,
        )

    @classmethod
    def determine_retry_date_for_deferred_checking_txn(cls, transaction_node: TransactionNode, context: ExecutionContext) -> date:
        # OBSOLETE: retained temporarily as a reference while attemptTransaction
        # moves to the generalized cash suffix-capacity implementation.
        # A retry is plausible only when its amount fits for the entire
        # remaining forecast, not merely on the candidate date. Build suffix
        # minima by sweeping backward over the already-computed accepted
        # forecast. available_balance() and payable_balance() include the hard
        # and policy bounds in force on each date.
        future_capacity: list[tuple[date, Decimal, Decimal]] = []
        minimum_future_available = Decimal("Infinity")
        minimum_future_payable = Decimal("Infinity")

        for forecast_index_value in reversed(context.forecast_df.index):
            candidate_date = (
                forecast_index_value.date()
                if isinstance(forecast_index_value, pd.Timestamp)
                else forecast_index_value
            )
            if candidate_date <= transaction_node.transaction_date:
                break

            available = (
                context.available_balance(
                    CellId(candidate_date, transaction_node.account_from)
                )
                if transaction_node.account_from is not None
                else Decimal("Infinity")
            )
            payable = (
                context.payable_balance(
                    CellId(candidate_date, transaction_node.account_to)
                )
                if transaction_node.account_to is not None
                else Decimal("Infinity")
            )

            minimum_future_available = min(
                minimum_future_available,
                available,
            )
            minimum_future_payable = min(
                minimum_future_payable,
                payable,
            )
            future_capacity.append(
                (
                    candidate_date,
                    minimum_future_available,
                    minimum_future_payable,
                )
            )

        for (
            candidate_date,
            minimum_available,
            minimum_payable,
        ) in reversed(future_capacity):
            if (
                transaction_node.amount <= minimum_available
                and transaction_node.amount <= minimum_payable
            ):
                return candidate_date

        last_index_value = context.forecast_df.index[-1]
        last_forecast_date = (
            last_index_value.date()
            if isinstance(last_index_value, pd.Timestamp)
            else last_index_value
        )
        return last_forecast_date + datetime.timedelta(days=1)
        
            
    @classmethod
    def determine_retry_amount_for_partial(cls, transaction_node: TransactionNode, context: ExecutionContext) -> Decimal:
        # OBSOLETE: retained temporarily as a reference while attemptTransaction
        # moves to the generalized cash suffix-capacity implementation.
        # A partial transaction executes on its original date, so its safe
        # amount is bounded by the smallest source headroom and destination
        # capacity from that date through the end of the accepted forecast.
        minimum_future_available = Decimal("Infinity")
        minimum_future_payable = Decimal("Infinity")

        for forecast_index_value in reversed(context.forecast_df.index):
            candidate_date = (
                forecast_index_value.date()
                if isinstance(forecast_index_value, pd.Timestamp)
                else forecast_index_value
            )
            if candidate_date < transaction_node.transaction_date:
                break

            available = (
                context.available_balance(
                    CellId(candidate_date, transaction_node.account_from)
                )
                if transaction_node.account_from is not None
                else Decimal("Infinity")
            )
            payable = (
                context.payable_balance(
                    CellId(candidate_date, transaction_node.account_to)
                )
                if transaction_node.account_to is not None
                else Decimal("Infinity")
            )
            minimum_future_available = min(
                minimum_future_available,
                available,
            )
            minimum_future_payable = min(
                minimum_future_payable,
                payable,
            )

        safe_amount = min(
            transaction_node.amount,
            minimum_future_available,
            minimum_future_payable,
        )
        return max(Decimal("0"), safe_amount)

    @classmethod
    def _cash_suffix_capacity_by_date(
        cls,
        transaction_node: TransactionNode,
        context: ExecutionContext,
    ) -> dict[date, Decimal]:
        """Return the safe persistent cash delta for each forecast date."""
        capacities: dict[date, Decimal] = {}
        minimum_future_available = Decimal("Infinity")
        minimum_future_payable = Decimal("Infinity")

        for forecast_index_value in reversed(context.forecast_df.index):
            candidate_date = (
                forecast_index_value.date()
                if isinstance(forecast_index_value, pd.Timestamp)
                else forecast_index_value
            )
            if candidate_date < transaction_node.transaction_date:
                break

            available = (
                context.available_balance(
                    CellId(candidate_date, transaction_node.account_from)
                )
                if transaction_node.account_from is not None
                else Decimal("Infinity")
            )
            payable = (
                context.payable_balance(
                    CellId(candidate_date, transaction_node.account_to)
                )
                if transaction_node.account_to is not None
                else Decimal("Infinity")
            )
            minimum_future_available = min(
                minimum_future_available,
                available,
            )
            minimum_future_payable = min(
                minimum_future_payable,
                payable,
            )
            capacities[candidate_date] = max(
                Decimal("0"),
                min(minimum_future_available, minimum_future_payable),
            )

        return capacities

    @staticmethod
    def _transaction_record(
        transaction_node: TransactionNode,
        *,
        transaction_date: date | None = None,
        amount: Decimal | None = None,
    ) -> dict[str, list[object]]:
        return {
            "Date": [transaction_date or transaction_node.transaction_date],
            "Priority": [transaction_node.priority_level],
            "Amount": [
                transaction_node.amount if amount is None else amount
            ],
            "Memo": [transaction_node.memo],
            "Income_Flag": [transaction_node.income_flag],
            "Deferrable": [transaction_node.deferrable],
            "Partial_Payment_Allowed": [
                transaction_node.partial_payment_allowed
            ],
        }

    #it looks like this is used to modify a transaction node
    @staticmethod
    def _transaction_node_with_amount(
        transaction_node: TransactionNode,
        amount: Decimal,
    ) -> TransactionNode:
        return TransactionNode(
            amount=amount,
            account_from=transaction_node.account_from,
            account_to=transaction_node.account_to,
            transaction_date=transaction_node.transaction_date,
            priority_level=transaction_node.priority_level,
            memo=transaction_node.memo,
            occurrence_ordinal=transaction_node.occurrence_ordinal,
            deferrable=transaction_node.deferrable,
            partial_payment_allowed=(
                transaction_node.partial_payment_allowed
            ),
            income_flag=transaction_node.income_flag,
        )

    @staticmethod
    def _transaction_node_with_date(
        transaction_node: TransactionNode,
        transaction_date: date,
    ) -> TransactionNode:
        return TransactionNode(
            amount=transaction_node.amount,
            account_from=transaction_node.account_from,
            account_to=transaction_node.account_to,
            transaction_date=transaction_date,
            priority_level=transaction_node.priority_level,
            memo=transaction_node.memo,
            occurrence_ordinal=transaction_node.occurrence_ordinal,
            deferrable=transaction_node.deferrable,
            partial_payment_allowed=(
                transaction_node.partial_payment_allowed
            ),
            income_flag=transaction_node.income_flag,
        )

    @staticmethod
    def _specialize_transaction_node(
        transaction_node: TransactionNode,
        context: ExecutionContext,
    ) -> TransactionNode:
        """Select the posting node whose writes match the routed accounts.

        TransactionNode is the neutral request assembled from a line item and
        memo rule. This factory converts that request into account-specific
        posting behavior. Keeping the choice here makes attemptTransaction
        responsible for feasibility while each node remains responsible for
        the financial cells it changes.
        """
        account_from_type = (
            context.name_to_account_type[transaction_node.account_from]
            if transaction_node.account_from is not None
            else None
        )
        account_to_type = (
            context.name_to_account_type[transaction_node.account_to]
            if transaction_node.account_to is not None
            else None
        )

        node_type: type[TransactionNode] = TransactionNode
        if account_from_type == "credit" and account_to_type is None:
            node_type = CreditPurchaseNode
        elif (
            account_from_type == "checking"
            and account_to_type == "credit"
        ):
            node_type = CreditCardSpecifiedAmountPaymentNode
        elif (
            account_from_type == "checking"
            and account_to_type == "loan"
        ):
            node_type = LoanSpecifiedAmountPaymentNode
        elif "investment" in {account_from_type, account_to_type}:
            node_type = InvestmentTransferNode

        if isinstance(transaction_node, node_type):
            return transaction_node

        return node_type(
            amount=transaction_node.amount,
            account_from=transaction_node.account_from,
            account_to=transaction_node.account_to,
            transaction_date=transaction_node.transaction_date,
            priority_level=transaction_node.priority_level,
            memo=transaction_node.memo,
            occurrence_ordinal=transaction_node.occurrence_ordinal,
            deferrable=transaction_node.deferrable,
            partial_payment_allowed=(
                transaction_node.partial_payment_allowed
            ),
            income_flag=transaction_node.income_flag,
        )

    @classmethod
    def _reschedule_deferred_transaction(
        cls,
        transaction_node: TransactionNode,
        context: ExecutionContext,
        retry_date: date | None,
    ) -> ExecutionContext:
        if retry_date is None:
            last_index_value = context.forecast_df.index[-1]
            last_forecast_date = (
                last_index_value.date()
                if isinstance(last_index_value, pd.Timestamp)
                else last_index_value
            )
            retry_date = last_forecast_date + datetime.timedelta(days=1)

        transaction_date = transaction_node.transaction_date
        current_occurrence = LineItemSet.from_dict(
            {
                "budget_items": [
                    {
                        "Start_Date": transaction_date,
                        "End_Date": transaction_date,
                        "Priority": transaction_node.priority_level,
                        "interval": "once",
                        "Amount": float(transaction_node.amount),
                        "Memo": transaction_node.memo,
                        "Income_Flag": transaction_node.income_flag,
                        "Deferrable": transaction_node.deferrable,
                        "Partial_Payment_Allowed": (
                            transaction_node.partial_payment_allowed
                        ),
                        "Recurrence_Key": None,
                        "Recurrence_Anchor": transaction_date,
                    }
                ]
            }
        )
        context.line_item_set = context.line_item_set - current_occurrence

        if retry_date > context.forecast_df.index[-1]:
            context.deferred_df = pd.concat(
                [
                    context.deferred_df,
                    pd.DataFrame(
                        cls._transaction_record(
                            transaction_node,
                            transaction_date=retry_date,
                        )
                    ),
                ],
                ignore_index=True,
            )
            return context

        retry_occurrence = LineItemSet.from_dict(
            {
                "budget_items": [
                    {
                        "Start_Date": retry_date,
                        "End_Date": retry_date,
                        "Priority": transaction_node.priority_level,
                        "interval": "once",
                        "Amount": float(transaction_node.amount),
                        "Memo": transaction_node.memo,
                        "Income_Flag": transaction_node.income_flag,
                        "Deferrable": transaction_node.deferrable,
                        "Partial_Payment_Allowed": (
                            transaction_node.partial_payment_allowed
                        ),
                        "Recurrence_Key": None,
                        "Recurrence_Anchor": retry_date,
                    }
                ]
            }
        )
        context.line_item_set = context.line_item_set + retry_occurrence
        return context


    # TODO there are inefficiencies in here
    @classmethod
    def attemptTransaction(cls, transaction_node: TransactionNode, context: ExecutionContext) -> ExecutionContext:

        # Codex: Resolve all previously accepted work before taking the speculative
        # snapshot. Deferral lookup must inspect a complete accepted forecast,
        # not cells that are still waiting in the propagation queue.
        cls.propagate(context)
        # Codex added this, I think it is not necessary but also if the queue is empty it does nothing
        # so it's fine that it is here

        # Callers normally receive an account-specific node from
        # assemble_transaction_node(). Specialize again here deliberately:
        # attemptTransaction is also called directly by focused tests and may
        # later be used by policy expansion. This makes the route dispatch an
        # invariant of transaction execution, rather than an assumption every
        # caller must remember.
        transaction_node = cls._specialize_transaction_node(
            transaction_node,
            context,
        )

        day_index = int(
            context.forecast_df.index.get_indexer(
                pd.Index([transaction_node.transaction_date])
            )[0]
        )

        if day_index < 0:
            raise ValueError(
                f"Transaction date {transaction_node.transaction_date} "
                "is outside the forecast range"
            )
        
        account_from_type = (
            context.name_to_account_type[transaction_node.account_from]
            if transaction_node.account_from is not None
            else None
        )
        account_to_type = (
            context.name_to_account_type[transaction_node.account_to]
            if transaction_node.account_to is not None
            else None
        )


        #Income, never a problem
        if account_from_type is None and account_to_type == "checking":
            context.register(
                day_index=day_index,
                priority_level=transaction_node.priority_level,
                node=transaction_node,
            )
            context.enqueue(transaction_node.node_id)
            cls.propagate(context)
            return context

        simple_cash_route = (
            account_from_type == "checking"
            and account_to_type in {None, "checking"}
        )

        # TODO tighten input validation to prevent this
        # this branch is in principal not correct if there is a non-0 min amount for 
        # a debt account, like "don't pay off more than $1k", which is mathematically
        # possible but not realistic.
        # This optimization takes advantage of these contraints to not resolve the graph 
        # when checking if this transaction is accepted.
        if simple_cash_route:
            capacities = cls._cash_suffix_capacity_by_date(
                transaction_node,
                context,
            )
            safe_amount = capacities.get(
                transaction_node.transaction_date,
                Decimal("0"),
            )

            if transaction_node.amount <= safe_amount:
                accepted_node = transaction_node
                accepted_amount = transaction_node.amount
            elif (
                transaction_node.partial_payment_allowed
                and safe_amount > 0
            ):
                accepted_amount = safe_amount
                accepted_node = cls._transaction_node_with_amount(
                    transaction_node,
                    accepted_amount,
                )
            elif transaction_node.deferrable:
                retry_date = next(
                    (
                        candidate_date
                        for candidate_date in sorted(capacities)
                        if (
                            candidate_date
                            > transaction_node.transaction_date
                            and capacities[candidate_date]
                            >= transaction_node.amount
                        )
                    ),
                    None,
                )
                return cls._reschedule_deferred_transaction(
                    transaction_node,
                    context,
                    retry_date,
                )
            else:
                context.skipped_df = pd.concat(
                    [
                        context.skipped_df,
                        pd.DataFrame(
                            cls._transaction_record(transaction_node)
                        ),
                    ],
                    ignore_index=True,
                )
                return context

            context.register(
                day_index=day_index,
                priority_level=accepted_node.priority_level,
                node=accepted_node,
            )
            context.enqueue(accepted_node.node_id)
            cls.propagate(context)
            context.confirmed_df = pd.concat(
                [
                    context.confirmed_df,
                    pd.DataFrame(
                        cls._transaction_record(
                            transaction_node,
                            amount=accepted_amount,
                        )
                    ),
                ],
                ignore_index=True,
            )
            return context
        elif (
            account_from_type == "credit"
            or account_to_type == "credit"
            or account_to_type == "loan"
            or account_from_type == "investment"
            or account_to_type == "investment"
        ):
            # Debt and investment transactions change future derived state,
            # not merely today's headline balances:
            #
            # * CreditPurchaseNode also increases the current statement.
            # * CreditCardSpecifiedAmountPaymentNode allocates payment between
            #   previous/current statements and records cycle payments.
            # * LoanSpecifiedAmountPaymentNode pays accrued interest before
            #   principal and records the cycle payment.
            # * InvestmentTransferNode changes the base used by every later
            #   daily return calculation.
            #
            # Those changes affect later interest, rollover, and minimum
            # payment computations. Consequently the full amount is tried in a
            # fork and propagated through the graph. If it fails, the same
            # specialized node type is used for each partial/date trial below.
            speculative_context = context.fork()
            try:
                speculative_context.register(
                        day_index=day_index,
                        priority_level=transaction_node.priority_level,
                        node=transaction_node,
                )
                speculative_context.enqueue(transaction_node.node_id)
                ExecutionEngine.propagate(speculative_context)
                
                # transaction accepted
                speculative_context.confirmed_df = pd.concat([ context.confirmed_df, pd.DataFrame({"Date":[transaction_node.transaction_date], 
                                                                                   "Priority":[transaction_node.priority_level], 
                                                                                   "Amount":[transaction_node.amount], 
                                                                                   "Memo":[transaction_node.memo], 
                                                                                   "Income_Flag":[transaction_node.income_flag],
                                                                                   "Deferrable":[transaction_node.deferrable], 
                                                                                   "Partial_Payment_Allowed":[transaction_node.partial_payment_allowed] })])
                return speculative_context
            except SpeculativeTransactionRejected as e:
                if not transaction_node.partial_payment_allowed and not transaction_node.deferrable:
                    context.skipped_df = pd.concat([ context.skipped_df, pd.DataFrame({"Date":[transaction_node.transaction_date], 
                                                                                        "Priority":[transaction_node.priority_level], 
                                                                                        "Amount":[transaction_node.amount], 
                                                                                        "Memo":[transaction_node.memo], 
                                                                                        "Income_Flag":[transaction_node.income_flag],
                                                                                        "Deferrable":[transaction_node.deferrable], 
                                                                                        "Partial_Payment_Allowed":[transaction_node.partial_payment_allowed] })])
                    return context #not speculative context!
                elif transaction_node.partial_payment_allowed:
                    # Search integer cents so termination and the one-cent
                    # optimum are exact. Zero is the known-success lower
                    # bound; the requested amount is the known-failure upper
                    # bound because this branch is entered only after the full
                    # transaction was rejected. Feasibility is assumed to be
                    # monotonic by amount: if X succeeds, every smaller amount
                    # succeeds. Each midpoint runs in an independent fork.
                    # When the bounds become adjacent, highest_success_cents is
                    # the largest legal amount and best_context is the already
                    # resolved graph for that amount.
                    requested_cents = int(
                        transaction_node.amount * Decimal("100")
                    )
                    highest_success_cents = 0
                    lowest_failure_cents = requested_cents
                    best_context: ExecutionContext | None = None

                    while (
                        lowest_failure_cents
                        - highest_success_cents
                        > 1
                    ):
                        trial_cents = (
                            highest_success_cents
                            + lowest_failure_cents
                        ) // 2
                        trial_amount = (
                            Decimal(trial_cents) / Decimal("100")
                        )
                        trial_node = cls._transaction_node_with_amount(
                            transaction_node,
                            trial_amount,
                        )
                        trial_node = cls._specialize_transaction_node(
                            trial_node,
                            context,
                        )
                        binary_search_context = context.fork()
                        binary_search_context.register(
                            day_index=day_index,
                            priority_level=trial_node.priority_level,
                            node=trial_node,
                        )
                        binary_search_context.enqueue(trial_node.node_id)
                        try:
                            cls.propagate(binary_search_context)
                        except SpeculativeTransactionRejected:
                            lowest_failure_cents = trial_cents
                        else:
                            highest_success_cents = trial_cents
                            best_context = binary_search_context

                    if best_context is None:
                        context.skipped_df = pd.concat(
                            [
                                context.skipped_df,
                                pd.DataFrame(
                                    cls._transaction_record(
                                        transaction_node
                                    )
                                ),
                            ],
                            ignore_index=True,
                        )
                        return context

                    accepted_amount = (
                        Decimal(highest_success_cents)
                        / Decimal("100")
                    )
                    best_context.confirmed_df = pd.concat(
                        [
                            context.confirmed_df,
                            pd.DataFrame(
                                cls._transaction_record(
                                    transaction_node,
                                    amount=accepted_amount,
                                )
                            ),
                        ],
                        ignore_index=True,
                    )
                    return best_context
                elif transaction_node.deferrable:
                    # Search only future income dates, ordered chronologically.
                    # The half-open interval
                    # [first_candidate_index, no_candidate_index) contains the
                    # earliest date that may succeed. This assumes feasibility
                    # is monotonic across those dates: rejected dates form a
                    # prefix and acceptable dates form a suffix. A failed
                    # midpoint discards it and every earlier candidate; a
                    # successful midpoint is retained while the search moves
                    # left. The authoritative context is not mutated by trial
                    # forks; only the earliest successful date is rescheduled.
                    schedule = context.line_item_set.getLineItemSchedule()
                    income_mask = (
                        schedule["Income_Flag"]
                        .fillna(False)
                        .map(
                            lambda value: (
                                value
                                if isinstance(value, bool)
                                else str(value).strip().lower() == "true"
                            )
                        )
                    )
                    income_dates = sorted(
                        {
                            income_date
                            for income_date in schedule.loc[
                                income_mask, "Date"
                            ]
                            if (
                                income_date
                                > transaction_node.transaction_date
                            )
                        }
                    )

                    first_candidate_index = 0
                    no_candidate_index = len(income_dates)
                    earliest_successful_date: date | None = None

                    while first_candidate_index < no_candidate_index:
                        trial_index = (
                            first_candidate_index
                            + no_candidate_index
                        ) // 2
                        trial_date = income_dates[trial_index]
                        trial_node = cls._transaction_node_with_date(
                            transaction_node,
                            trial_date,
                        )
                        trial_node = cls._specialize_transaction_node(
                            trial_node,
                            context,
                        )
                        trial_context = context.fork()
                        trial_day_index = int(
                            trial_context.forecast_df.index.get_indexer(
                                pd.Index([trial_date])
                            )[0]
                        )
                        if trial_day_index < 0:
                            no_candidate_index = trial_index
                            continue

                        trial_context.register(
                            day_index=trial_day_index,
                            priority_level=trial_node.priority_level,
                            node=trial_node,
                        )
                        trial_context.enqueue(trial_node.node_id)
                        try:
                            cls.propagate(trial_context)
                        except SpeculativeTransactionRejected:
                            first_candidate_index = trial_index + 1
                        else:
                            earliest_successful_date = trial_date
                            no_candidate_index = trial_index

                    return cls._reschedule_deferred_transaction(
                        transaction_node,
                        context,
                        earliest_successful_date,
                    )
        else:
            raise NotImplementedError(
                "Graph v2 transaction routing is not implemented for "
                f"{account_from_type!r} -> {account_to_type!r} "
                f"({transaction_node.account_from!r} -> "
                f"{transaction_node.account_to!r})"
            )



    @classmethod
    def runForecast(
        cls,
        initial_conditions: ExpenseForecastInitialConditions,
        milestone_set: MilestoneSet
    ) -> ExpenseForecastResult:
        start_ts = datetime.datetime.now()
        context = ExecutionContext(initial_conditions, milestone_set)
        
        # forecast_df has been initialized with 0s and empty strings
        cls.build_initial_account_nodes(context)
        for day_index in range(1, len(context.forecast_df.index)):
            cls.build_balance_carry_nodes_for_day(
                context=context,
                day_index=day_index,
            )
        cls.build_account_semantic_nodes(context)


        #if there are deferrals, this needs to be recomputed (and it will be based on a flag)
        #but most of the time, it is fine to compute this once at the start
        transactions_schedule = context.line_item_set.getLineItemSchedule()

        all_priority_levels = set(context.initial_conditions.initial_line_item_set.getLineItems()["Priority"].unique().flat)
        all_priority_levels.add(1) #to make sure 1 is always in the set
        for priority_level in sorted(list(all_priority_levels)):

            deferrals_exist_at_this_level = bool(
                (
                    (transactions_schedule["Priority"] == priority_level)
                    & transactions_schedule["Deferrable"]
                    .fillna(False)
                    .astype(bool)
                ).any()
            )

            # Most forecast dates contain no scheduled transaction. Walk only
            # the dates present at this priority instead of scanning every
            # forecast row. A deferral can insert a new future occurrence, so
            # refresh the candidate dates after each processed date when this
            # level contains deferrable work.
            processed_through = context.initial_conditions.start_date
            while True:
                if deferrals_exist_at_this_level:
                    transactions_schedule = (
                        context.line_item_set.getLineItemSchedule()
                    )

                dates_at_priority = sorted(
                    {
                        scheduled_date
                        for scheduled_date in transactions_schedule.loc[
                            transactions_schedule["Priority"]
                            == priority_level,
                            "Date",
                        ]
                        if (
                            processed_through < scheduled_date
                            <= context.initial_conditions.end_date
                        )
                    }
                )
                if not dates_at_priority:
                    break

                transaction_date = dates_at_priority[0]
                day_index = int(
                    context.forecast_df.index.get_indexer(
                        pd.Index([transaction_date])
                    )[0]
                )
                if day_index < 0:
                    raise ValueError(
                        f"Scheduled transaction date {transaction_date} "
                        "is outside the forecast calendar"
                    )

                logger.info(str(priority_level)+' '+str(day_index))

                txn_date_selection_mask = (transactions_schedule["Date"] == transaction_date)
                txn_priority_selection_mask = (transactions_schedule["Priority"] == priority_level)
                transactions_for_this_day = transactions_schedule.loc[txn_date_selection_mask & txn_priority_selection_mask]

                for line_item_index, line_item_row in transactions_for_this_day.iterrows():
                    logger.info('    '+str(line_item_index))
                    transaction_node = cls.assemble_transaction_node(line_item_row, context)
                    if priority_level > 1:
                        context = cls.attemptTransaction(transaction_node=transaction_node,
                                            context=context)
                    elif priority_level == 1:
                        context.register(
                            day_index=day_index,
                            priority_level=transaction_node.priority_level,
                            node=transaction_node,
                        )
                        context.enqueue(transaction_node.node_id)
                        cls.propagate(context)
                processed_through = transaction_date
        ExecutionEngine.propagate(context)

        # Account ledgers and active bounds are graph implementation state.
        # Keep only the public account balances and memo columns before
        # applying the same summary materialization used by legacy.
        public_columns = [
            account.name
            for account in (
                initial_conditions.initial_account_set.accounts
            )
        ] + ["Memo Directives", "Memo"]
        context.forecast_df = context.forecast_df.loc[:, public_columns]

        # Graph execution uses dates as its row index. Public forecast output
        # matches legacy: Date is the first column and rows use a RangeIndex.
        context.forecast_df = (
            context.forecast_df
            .rename_axis("Date")
            .reset_index()
        )
        # _appendSummaryLines currently preserves and reorders this legacy
        # presentation column. Its values are not part of v2 parity yet.
        context.forecast_df["Next Income Date"] = "" #TODO delete after parity testing is complete
        context.forecast_df = ForecastHandler._appendSummaryLines(initial_conditions.initial_account_set, context.forecast_df)
        context.forecast_df = ForecastHandler._roundForecastOutput(context.forecast_df, decimals=2)

        result_kwargs = {
            "confirmed_df": context.confirmed_df,
            "deferred_df": context.deferred_df,
            "skipped_df": context.skipped_df,
        }
        if milestone_set:
            result_kwargs["milestone_set"] = milestone_set
            milestone_results = MilestoneSet.evaluateMilestones(context.forecast_df, milestone_set)
            result_kwargs["milestone_results"] = milestone_results

        end_ts = datetime.datetime.now()

        # implemented:
        # allowed_kwargs = ['confirmed_df', 'deferred_df', 'skipped_df', 'milestone_set', 'milestone_results', 
        # TODO not yet implemented:
        # 'approximate_flag', 'policy_results', 'safety_decisions', 'policy_regimes', 'graph_diagnostics']
        R = ExpenseForecastResult(initial_conditions=initial_conditions,
                                  forecast_df=context.forecast_df,
                                  start_ts=start_ts,
                                  end_ts=end_ts,
                                  **result_kwargs
                                  )

        return R

if __name__ == '__main__':

    start_date = date(2020,1,1)
    end_date = date(2020,1,5)
    A = AccountSet()
    L = LineItemSet()
    M = MemoRuleSet()
    MS = MilestoneSet()

    A.createCheckingAccount('Checking',1000,0,10_000,True)
    A.createCheckingAccount('Second Checking',2000,0,10_000,False)
    L.addLineItem(start_date=start_date + datetime.timedelta(days=3),
                  end_date=start_date + datetime.timedelta(days=3),
                  priority=1,
                  interval='once',
                  amount=1,
                  memo='test txn',
                  income_flag=False)
    M.addMemoRule(memo_regex='.*',
                  account_from='Checking',
                  account_to=None,
                  transaction_priority=1)

    initial_conditions = ExpenseForecastInitialConditions(
        start_date,
        end_date,
        A,
        L,
        M
    )

    R = ExecutionEngine.runForecast(initial_conditions, MS)

    print(R.to_string())


### TODOS
# Lots of Decimal casting that could be moved to read

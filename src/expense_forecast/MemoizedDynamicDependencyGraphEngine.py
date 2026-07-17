# Based on this paper: https://csd.cs.cmu.edu/sites/default/files/phd-thesis/CMU-CS-05-129.pdf
from __future__ import annotations
from dataclasses import dataclass, field
from heapq import heappop, heappush
from typing import Hashable
from collections.abc import Hashable
import uuid
type NodeId = Hashable
type Priority = tuple[int, int, int]
from abc import abstractmethod

from expense_forecast.AccountSet import AccountSet
from expense_forecast.LineItemSet import LineItemSet
# from expense_forecast.ForecastSetInitialConditions import ForecastSetInitialConditions
from expense_forecast.MemoRuleSet import MemoRuleSet
from expense_forecast.MilestoneSet import MilestoneSet
from expense_forecast.ExpenseForecastInitialConditions import ExpenseForecastInitialConditions
from expense_forecast.ExpenseForecastResult import ExpenseForecastResult
from expense_forecast.ForecastPolicySet import ForecastPolicySet
from expense_forecast.MinimumCheckingBalancePolicy import MinimumCheckingBalancePolicy

import pandas as pd
from datetime import date

def values_equal(left, right) -> bool:
    if pd.isna(left) and pd.isna(right):
        return True

    return left == right

@dataclass(frozen=True)
class CellId:
    forecast_date: date
    column_name: str

@dataclass
class ExecutionContext:

    initial_conditions: ExpenseForecastInitialConditions
    forecast_df: pd.DataFrame
    milestone_set: MilestoneSet

    ### Unclear on why I need this
    # Cell/location -> nodes that read it.
    readers: dict[CellId, set[NodeId]]

    nodes: dict[NodeId, "ComputationNode"] = field(default_factory=dict)

    # Full order of nodes created during the execution.
    execution_order: list[NodeId] = field(default_factory=list)

    # Current repair frontier.
    pending_heap: list[tuple[Priority, NodeId]] = field(default_factory=list)
    pending_ids: set[NodeId] = field(default_factory=set)

    def register(self, node: "ComputationNode") -> None:
        if node.node_id in self.nodes:
            raise ValueError(f"Duplicate node ID: {node.node_id!r}")

        self.nodes[node.node_id] = node
        self.execution_order.append(node.node_id)

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
    
    def __init__(self, 
                 initial_conditions: ExpenseForecastInitialConditions,
                 milestone_set: MilestoneSet):
        self.initial_conditions = initial_conditions
        self.milestone_set = milestone_set
        account_names = (
            initial_conditions.initial_account_set
            .getAccounts()["Name"]
            .tolist()
        )
        forecast_dates = pd.date_range(
            initial_conditions.start_date,
            initial_conditions.end_date,
            freq="D",
        )
        initialized_forecast_df = pd.DataFrame(
                index=forecast_dates,
                columns=account_names,
                dtype=float,
            )
        initialized_forecast_df['Memo'] = ''
        self.forecast_df = initialized_forecast_df

    def read(self, cell: CellId):
        return self.forecast_df.at[
            cell.forecast_date,
            cell.column_name,
        ]

    def write(self, cell: CellId, value) -> bool:
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



@dataclass
class ComputationNode:
    node_id: NodeId
    priority: Priority
    reads: set[CellId]
    writes: set[CellId]

    @abstractmethod
    def execute(self, context: ExecutionContext) -> set[CellId]:
        """
        Execute the node and return the memory locations whose values changed.
        """
    
    def __init__(self, reads, writes, E: ExecutionContext):
        self.reads = reads
        self.writes = writes
        self.node_id = uuid.uuid4()

        E.register(self)

@dataclass
class WriteValueToOutputCellNode(ComputationNode):
    node_id: NodeId
    priority: Priority
    value: float
    reads: set[CellId]
    writes: set[CellId]

    def execute(self, context: ExecutionContext) -> set[CellId]:
        output_cell = next(iter(self.writes))
        changed = context.write(output_cell, self.value)
        return {output_cell} if changed else set()
    
@dataclass
class CarryValueNode(ComputationNode):
    node_id: NodeId
    priority: Priority
    source: CellId
    destination: CellId
    reads: set[CellId]
    writes: set[CellId]

    def execute(self, context: ExecutionContext) -> set[CellId]:
        value = context.read(self.source)
        changed = context.write(self.destination, value)

        return {self.destination} if changed else set()

class ExecutionEngine:

    @classmethod
    def _initialize_accounts(
        cls,
        context: ExecutionContext,
        account_df: pd.DataFrame,
        forecast_date: date,
    ) -> None:
        for sequence, (_, account) in enumerate(account_df.iterrows()):
            node = WriteValueToOutputCellNode(
                node_id=(
                    "initial_balance",
                    forecast_date,
                    account["Name"],
                ),
                priority=(0, 0, sequence),
                value=account["Balance"],
                reads=set(),
                writes={
                    CellId(
                        forecast_date=forecast_date,
                        column_name=account["Name"],
                    )
                },
            )

            context.register(node)

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
                node_id=(
                    "carry",
                    forecast_date,
                    account_name,
                ),
                priority=(day_number, 0, sequence),
                source=source,
                destination=destination,
                reads={source},
                writes={destination},
            )

            context.register(node)

    @classmethod
    def runForecast(
        cls,
        initial_conditions: ExpenseForecastInitialConditions
    ):
        E = ExecutionContext(initial_conditions, MS)
        # forecast_df has been initialized with 0s and empty strings

    @classmethod
    def propagate(cls, E: ExecutionContext):

        while E.pending_heap:

            node = E.pop_pending()

            changed_cells = node.execute(E)

            for cell in changed_cells:
                for dependent in E.readers.get(cell, []):
                    E.enqueue(dependent)

if __name__ == '__main__':

    start_date = date(2020,1,1)
    end_date = date(2020,4,1)
    A = AccountSet()
    L = LineItemSet()
    M = MemoRuleSet()
    MS = MilestoneSet()

    initial_conditions = ExpenseForecastInitialConditions(
        start_date,
        end_date,
        A,
        L,
        M
    )

    R = ExecutionEngine.runForecast(initial_conditions)
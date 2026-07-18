# Based on this paper: https://csd.cs.cmu.edu/sites/default/files/phd-thesis/CMU-CS-05-129.pdf
from __future__ import annotations
from dataclasses import dataclass, field
from heapq import heappop, heappush
from typing import Hashable
from collections.abc import Hashable
import uuid
from abc import ABC, abstractmethod

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
import datetime

def values_equal(left, right) -> bool:
    if pd.isna(left) and pd.isna(right):
        return True

    return left == right

type NodeId = Hashable

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
    execution_order: list[NodeId] = field(default_factory=list)
    pending_heap: list[tuple[Priority, NodeId]] = field(default_factory=list)
    pending_ids: set[NodeId] = field(default_factory=set)

    

    # ### Unclear on why I need this
    # # Cell/location -> nodes that read it.
    # readers: dict[CellId, set[NodeId]]

    # nodes: dict[NodeId, "ComputationNode"] = field(default_factory=dict)

    # # Full order of nodes created during the execution.
    # execution_order: list[NodeId] = field(default_factory=list)

    # # Current repair frontier.
    # pending_heap: list[tuple[Priority, NodeId]] = field(default_factory=list)
    # pending_ids: set[NodeId] = field(default_factory=set)

    def register(self, day_index: int, phase_index: int, node: "ComputationNode") -> None:
        if node.node_id in self.nodes:
            raise ValueError(f"Duplicate node ID: {node.node_id!r}")

        sequence = len(self.execution_order) #TODO not sure this is the right way

        node.priority = Priority(
            day_index,
            phase_index,
            sequence
        )

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
    
    # def __init__(self, 
    #              initial_conditions: ExpenseForecastInitialConditions,
    #              milestone_set: MilestoneSet):
    def __post_init__(self) -> None:
        
        account_names = (
            initial_conditions.initial_account_set
            .getAccounts()["Name"]
            .tolist()
        )
        forecast_dates = [ d.date() for d in pd.date_range(
            initial_conditions.start_date,
            initial_conditions.end_date,
            freq="D",
        ) ]
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
class ComputationNode(ABC):
    reads: set[CellId]
    writes: set[CellId]

    node_id: NodeId = field(init=False)
    priority: Priority = field(init=False)

    def __post_init__(self) -> None:
        self.node_id = uuid.uuid4()

    @abstractmethod
    def execute(
        self,
        context: ExecutionContext,
    ) -> set[CellId]:
        """Execute the node and return cells whose values changed."""
        raise NotImplementedError

@dataclass
class WriteValueToOutputCellNode(ComputationNode):
    value: float

    def execute(
        self,
        context: ExecutionContext,
    ) -> set[CellId]:
        output_cell = next(iter(self.writes))
        changed = context.write(output_cell, self.value)

        return {output_cell} if changed else set()
    
@dataclass
class CarryBalanceForwardNode(ComputationNode):

    def execute(
        self,
        context: ExecutionContext,
    ) -> set[CellId]:
        input_cell = next(iter(self.reads))
        output_cell = next(iter(self.writes))

        value = context.read(input_cell)
        changed = context.write(output_cell, value)

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
    def build_initial_account_nodes(
        cls,
        context: ExecutionContext,
    ) -> None:
        accounts = context.initial_conditions.initial_account_set.getAccounts()

        # for day_index, forecast_date in enumerate(context.forecast_df.index):
        for _, (_, account) in enumerate(accounts.iterrows()):
            node = WriteValueToOutputCellNode(
                value=account["Balance"],
                reads=set(),
                writes={
                    CellId(
                        forecast_date=context.initial_conditions.start_date,
                        column_name=account["Name"],
                    )
                },
            )

            context.register(
                day_index=0, #first day setup
                phase_index=0, #phase_index == 0 means setup phase
                node=node,
            )



    @classmethod
    def build_balance_carry_nodes_for_day(
        cls,
        context: ExecutionContext,
        day_index: int,
    ) -> None:
        """
        Build one carry-forward node per account for the given day.

        Each node reads the account balance from the previous day and writes
        that balance into the same account column on the current day.
        """
        if day_index <= 0:
            raise ValueError("Carry-forward nodes require day_index > 0.")

        current_date = context.forecast_df.index[day_index]
        previous_date = context.forecast_df.index[day_index - 1]

        accounts = context.initial_conditions.initial_account_set.getAccounts()

        for _, account in accounts.iterrows():
            account_name = account["Name"]

            previous_cell = CellId(
                forecast_date=previous_date,
                column_name=account_name,
            )

            current_cell = CellId(
                forecast_date=current_date,
                column_name=account_name,
            )

            node = CarryBalanceForwardNode(
                reads={previous_cell},
                writes={current_cell},
            )

            context.register(
                day_index=day_index,
                phase_index=0,
                node=node,
            )

    # this will not be used in practice
    @classmethod
    def execute_all(cls, context: ExecutionContext) -> None:
        for node_id in context.execution_order:
            node = context.nodes[node_id]
            node.execute(context)

    @classmethod
    def runForecast(
        cls,
        initial_conditions: ExpenseForecastInitialConditions,
        milestone_set: MilestoneSet
    ):
        context = ExecutionContext(initial_conditions, milestone_set)
        
        # forecast_df has been initialized with 0s and empty strings
        cls.build_initial_account_nodes(context)

        # Carry forward balances
        for day_index in range(1, len(context.forecast_df.index)):
            cls.build_balance_carry_nodes_for_day(
                context=context,
                day_index=day_index,
            )

        cls.execute_all(context)

        return context.forecast_df
        

        # ... continue
        # build_graph(context)
        # execute_initial_trace(context)
        # apply_input_changes(context, changed_cells)
        # propagate(context)

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
    end_date = date(2020,1,5)
    A = AccountSet()
    L = LineItemSet()
    M = MemoRuleSet()
    MS = MilestoneSet()

    A.createCheckingAccount('Checking',1000,0,10_000,True)
    A.createCheckingAccount('Second Checking',2000,0,10_000,False)
    # L.addLineItem(start_date=start_date + datetime.timedelta(days=3),
    #               end_date=start_date + datetime.timedelta(days=3),
    #               priority=1,
    #               interval='once',
    #               amount=1,
    #               memo='test txn',
    #               income_flag=False)
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
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
from decimal import Decimal

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

@dataclass
class ComputationNode(ABC):
    # reads: set[CellId] = field(
    #     init=False,
    #     default_factory=set,
    # )
    # writes: set[CellId] = field(
    #     init=False,
    #     default_factory=set,
    # )
    reads: set[CellId]
    writes: set[CellId]

    node_id: NodeId = field(init=False)
    priority: Priority = field(init=False)


    # TODO instead use a stable semantic id
    # e.g.
    # (
    #     "transaction",
    #     line_item.stable_id,
    #     occurrence_date,
    #     occurrence_sequence,
    # )
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
        logger.info('execute WriteValueToOutputCellNode')
        output_cell = next(iter(self.writes))
        changed = context.write(output_cell, self.value)

        return {output_cell} if changed else set()
    
@dataclass
class CarryBalanceForwardNode(ComputationNode):

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
    
# CreditCardRolloverNode
# CreditCardMinimumPaymentNode
# LoanMinimumPaymentNode
# LoanSurplusPaymentNode
# LoanInterestAccrualNode
# InvestmentAccrualNode

@dataclass
class TransactionNode(ComputationNode):
    amount: Decimal
    account_from: str
    account_to: str
    transaction_date: date

    def __post_init__(self) -> None:
        super().__post_init__()

        self.from_cell = CellId(
            forecast_date=self.transaction_date,
            column_name=self.account_from,
        )
        self.to_cell = CellId(
            forecast_date=self.transaction_date,
            column_name=self.account_to,
        )

        self.reads = {
            self.from_cell,
            self.to_cell,
        }

        self.writes = {
            self.from_cell,
            self.to_cell,
        }

    def execute(self, context: ExecutionContext) -> set[CellId]:
        logger.info('execute TransactionNode')

        changed_cells: set[CellId] = set()

        if self.from_cell.column_name: #if the txn is not income
            from_balance = Decimal(context.read(self.from_cell))
            if context.write(
                self.from_cell,
                from_balance - self.amount,
            ):
                changed_cells.add(self.from_cell)

        if self.to_cell.column_name: #if money is spent
            # print('self.to_cell.column_name')
            # print(self.to_cell.column_name)
            to_balance = Decimal(context.read(self.to_cell))
            if context.write(
                self.to_cell,
                to_balance + self.amount,
            ):
                changed_cells.add(self.to_cell)

        # TODO memo and memo directive

        return changed_cells

@dataclass
class CarryValueNode(ComputationNode):
    node_id: NodeId
    priority: Priority
    source: CellId
    destination: CellId
    reads: set[CellId]
    writes: set[CellId]

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
            context.enqueue(node.node_id)

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
                priority_level=0, #priority_level == 0 means setup phase
                node=node,
            )
            context.enqueue(node.node_id)

            # TODO adding account bounda as columns will allow policies to 
            # move acceptable min and max

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
                priority_level=0,
                node=node,
            )
            context.enqueue(node.node_id)

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
    def runForecast(
        cls,
        initial_conditions: ExpenseForecastInitialConditions,
        milestone_set: MilestoneSet
    ):
        context = ExecutionContext(initial_conditions, milestone_set)
        
        # forecast_df has been initialized with 0s and empty strings
        cls.build_initial_account_nodes(context)

        transactions_schedule = initial_conditions.initial_line_item_set.getLineItemSchedule()
        memo_rule_set = initial_conditions.initial_memo_rule_set

        all_priority_levels = set(context.initial_conditions.initial_line_item_set.getLineItems()["Priority"].unique().flat)
        all_priority_levels.add(1) #to make sure 1 is always in the set
        for priority_level in sorted(list(all_priority_levels)):
            for day_index in range(1, len(context.forecast_df.index)): #TODO does the RHS need a +1 ?

                logger.info(str(priority_level)+' '+str(day_index))

                transaction_date = context.forecast_df.index[day_index]
                txn_date_selection_mask = (transactions_schedule["Date"] == transaction_date)
                txn_priority_selection_mask = (transactions_schedule["Priority"] == priority_level)
                transactions_for_this_day = transactions_schedule.loc[txn_date_selection_mask & txn_priority_selection_mask]

                for line_item_index, line_item_row in transactions_for_this_day.iterrows():
                    logger.info('    '+str(line_item_index))

                    matching_memo_rule = memo_rule_set.findMatchingMemoRule(txn_memo=line_item_row["Memo"],
                                                                            transaction_priority=priority_level)

                    from_cell = CellId(
                        forecast_date=transaction_date,
                        column_name=matching_memo_rule.account_from,
                    )

                    to_cell = CellId(
                        forecast_date=transaction_date,
                        column_name=matching_memo_rule.account_to,
                    )

                    transaction_node = TransactionNode(amount=line_item_row["Amount"],
                                    account_from=matching_memo_rule.account_from,
                                    account_to=matching_memo_rule.account_to,
                                    transaction_date=transaction_date,
                                    reads={from_cell},
                                    writes={to_cell},
                                    )
                    # this is the last place I am sure before hypothetical / candidate
                    # stuff needs to start happening
                    
                    context.register(
                        day_index=day_index,
                        priority_level=priority_level,
                        node=transaction_node,
                    )
                    context.enqueue(transaction_node.node_id)

                    # TODO now the graph needs to resolve completely to determine if the transaction is accepted
                    
            for day_index in range(1, len(context.forecast_df.index)):
                # Carry forward balances. Should be the last thing of the day
                cls.build_balance_carry_nodes_for_day(
                    context=context,
                    day_index=day_index,
                )

        ExecutionEngine.propagate(context)

        return context.forecast_df
        

        # ... continue
        # build_graph(context)
        # execute_initial_trace(context)
        # apply_input_changes(context, changed_cells)
        # propagate(context)

    # @classmethod
    # def propagate(cls, context: ExecutionContext) -> None:
    #     while context.pending_heap:
    #         node = context.pop_pending()
    #         changed_cells = node.execute(context)

    #         for cell in changed_cells:
    #             for dependent_id in context.readers.get(cell, set()):
    #                 dependent = context.nodes[dependent_id]

    #                 if dependent.priority <= node.priority:
    #                     continue

    #                 context.enqueue(dependent_id)

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
                  amount=1500,
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
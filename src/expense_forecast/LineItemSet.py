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
from .LineItem import LineItem
import pandas as pd
import datetime
from . import log_methods
import jsonpickle
from .generate_date_sequence import generate_date_sequence
import logging


# logger = setup_logger('LineItemSet', './log/LineItemSet.log', level=logging.INFO)
logger = logging.getLogger(__name__)


class LineItemSet:
    """
    Represents a collection of LineItems.

    A LineItemSet groups multiple LineItems into a single logical unit that
    can be manipulated, evaluated, serialized, and applied as a whole.
    Individual LineItems describe financial events, while a LineItemSet
    defines the complete collection of events.

    Responsibilities
    ----------------
    - Store and manage a collection of LineItems.
    - Preserve collection invariants.
    - Provide lookup, iteration, and collection operations.
    - Support serialization and deserialization.
    - Define equality and collection semantics.

    Invariants
    ----------
    - Every contained object is a valid LineItem.
    - Collection operations preserve the validity of the set.
    - Serialization preserves the semantic meaning of the collection.
    - Equivalent collections compare as equal regardless of incidental
      implementation details.

    Notes
    -----
    LineItemSet provides collection behavior but does not determine the
    business purpose of its contents. Specialized subclasses or consumers,
    such as BudgetSet and MemoRuleSet, define how the contained LineItems
    are interpreted and used by the forecasting engine.
    """
    #TODO manual review of LineItemSet.__init__ docstring
    def __init__(self, line_items__list=None):
        """
        TODO one-line description of LineItemSet.__init__.

        TODO multi-line description of LineItemSet.__init__.
        TODO explain how LineItemSet.__init__ participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        line_items__list : object
            TODO one-line description of LineItemSet.__init__.line_items__list.

        Returns
        -------
        None
            TODO one-line description of return value of LineItemSet.__init__.

        Contract
        --------
        - #TODO contract lines for LineItemSet.__init__.
        - #TODO document exceptions, mutations, and precision assumptions for LineItemSet.__init__.

        @interface-report: show
        """
        self.line_items__list = []
        self.line_items = []
        self.budget_items__list = self.line_items__list
        self.budget_items = self.line_items

        if line_items__list is None:
            return

        required_attributes = [
            "start_date",
            "end_date",
            "priority",
            "interval",
            "amount",
            "memo",
        ]

        required_methods = [
            "to_dataframe",
            "to_dict",
            "to_json",
        ]

        for line_item in line_items__list:
            for attr in required_attributes:
                if not hasattr(line_item, attr):
                    raise ValueError(
                        f"LineItem is missing required attribute '{attr}'. "
                        f"Found attributes: {[x for x in dir(line_item) if '__' not in x]}"
                    )

            for method in required_methods:
                if not hasattr(line_item, method) or not callable(getattr(line_item, method)):
                    raise ValueError(
                        f"LineItem is missing required method '{method}'."
                    )

            self.line_items__list.append(line_item)
            self.line_items.append(line_item)

    def __str__(self):
        """
        @interface-report: show
        """
        return self.getLineItems().to_string()

    #TODO manual review of LineItemSet.getLineItems docstring
    def getLineItems(self):

        """
        TODO one-line description of LineItemSet.getLineItems.

        TODO multi-line description of LineItemSet.getLineItems.
        TODO explain how LineItemSet.getLineItems participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that LineItemSet.getLineItems takes no parameters beyond self/cls.

        Returns
        -------
        pd.DataFrame
            TODO one-line description of return value of LineItemSet.getLineItems.

        Contract
        --------
        - #TODO contract lines for LineItemSet.getLineItems.
        - #TODO document exceptions, mutations, and precision assumptions for LineItemSet.getLineItems.

        @interface-report: show
        """
        all_line_items_df = pd.DataFrame(
            {
                "Start_Date": [],
                "End_Date": [],
                "Priority": [],
                "interval": [],
                "Amount": [],
                "Memo": [],
                "Income_Flag": [],
                "Deferrable": [],
                "Partial_Payment_Allowed": [],
            }
        )

        for line_item in self.line_items:
            new_line_item_row_df = pd.DataFrame(
                {
                    "Start_Date": [line_item.start_date],
                    "End_Date": [line_item.end_date],
                    "Priority": [line_item.priority],
                    "interval": [line_item.interval],
                    "Amount": [line_item.amount],
                    "Memo": [line_item.memo],
                    "Income_Flag": [line_item.income_flag],
                    "Deferrable": [line_item.deferrable],
                    "Partial_Payment_Allowed": [line_item.partial_payment_allowed],
                }
            )

            if (not all_line_items_df.empty) & (not new_line_item_row_df.empty):
                all_line_items_df = pd.concat(
                    [all_line_items_df, new_line_item_row_df], axis=0
                )

            if (all_line_items_df.empty) & (not new_line_item_row_df.empty):
                all_line_items_df = new_line_item_row_df

        all_line_items_df.reset_index(drop=True, inplace=True)
        return all_line_items_df

    #TODO manual review of LineItemSet.getLineItemSchedule docstring
    def getLineItemSchedule(self):

        """
        TODO one-line description of LineItemSet.getLineItemSchedule.

        TODO multi-line description of LineItemSet.getLineItemSchedule.
        TODO explain how LineItemSet.getLineItemSchedule participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that LineItemSet.getLineItemSchedule takes no parameters beyond self/cls.

        Returns
        -------
        pd.DataFrame
            TODO one-line description of return value of LineItemSet.getLineItemSchedule.

        Contract
        --------
        - #TODO contract lines for LineItemSet.getLineItemSchedule.
        - #TODO document exceptions, mutations, and precision assumptions for LineItemSet.getLineItemSchedule.

        @interface-report: show
        """
        budget_schedule_rows = []
        for line_item in self.line_items:
            relative_num_days = (line_item.end_date - line_item.start_date).days
            relevant_date_sequence = generate_date_sequence(
                line_item.start_date, relative_num_days, line_item.interval
            )

            for scheduled_date in relevant_date_sequence:
                budget_schedule_rows.append(
                    {
                        "Date": scheduled_date,
                        "Priority": line_item.priority,
                        "Amount": line_item.amount,
                        "Memo": line_item.memo,
                        "Income_Flag": line_item.income_flag,
                        "Deferrable": line_item.deferrable,
                        "Partial_Payment_Allowed": line_item.partial_payment_allowed,
                    }
                )

        current_budget_schedule = pd.DataFrame(
            budget_schedule_rows,
            columns=[
                "Date",
                "Priority",
                "Amount",
                "Memo",
                "Income_Flag",
                "Deferrable",
                "Partial_Payment_Allowed",
            ],
        )

        if current_budget_schedule.empty:
            return current_budget_schedule

        current_budget_schedule.sort_values(
            inplace=True,
            axis=0,
            by="Date",
            key=lambda date_column: pd.to_datetime(date_column),
            )
        current_budget_schedule.reset_index(inplace=True, drop=True)

        return current_budget_schedule

    #TODO manual review of LineItemSet.addLineItem docstring
    def addLineItem(self, start_date, end_date, priority, interval, amount, memo, income_flag = False, **kwargs):
        """
        TODO one-line description of LineItemSet.addLineItem.

        TODO multi-line description of LineItemSet.addLineItem.
        TODO explain how LineItemSet.addLineItem participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        start_date : date
            TODO one-line description of LineItemSet.addLineItem.start_date.

        end_date : date
            TODO one-line description of LineItemSet.addLineItem.end_date.

        priority : int
            TODO one-line description of LineItemSet.addLineItem.priority.

        interval : str
            TODO one-line description of LineItemSet.addLineItem.interval.

        amount : float
            TODO one-line description of LineItemSet.addLineItem.amount.

        memo : str
            TODO one-line description of LineItemSet.addLineItem.memo.

        income_flag : bool
            TODO one-line description of LineItemSet.addLineItem.income_flag.

        **kwargs : dict
            TODO one-line description of LineItemSet.addLineItem.kwargs.

        Returns
        -------
        object
            TODO one-line description of return value of LineItemSet.addLineItem.

        Contract
        --------
        - #TODO contract lines for LineItemSet.addLineItem.
        - #TODO document exceptions, mutations, and precision assumptions for LineItemSet.addLineItem.

        @interface-report: show
        """
        line_item = LineItem(
            start_date,
            end_date,
            priority,
            interval,
            amount,
            memo,
            income_flag=income_flag,
            deferrable=kwargs.get('deferrable',None),
            partial_payment_allowed=kwargs.get('partial_payment_allowed',None),
        )

        # Check for duplicates
        all_line_items = self.getLineItems()
        if not all_line_items.empty:
            duplicates = all_line_items[
                (all_line_items["Priority"] == priority)
                & (all_line_items["Memo"] == memo)
            ]
            if not duplicates.empty:
                error_message = f"A line item with priority {priority} and memo '{memo}' already exists."
                raise ValueError(error_message)

        # Append the line item
        self.line_items.append(line_item)

    #TODO manual review of LineItemSet.to_dict docstring
    def to_dict(self):
        """
        TODO one-line description of LineItemSet.to_dict.

        TODO multi-line description of LineItemSet.to_dict.
        TODO explain how LineItemSet.to_dict participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that LineItemSet.to_dict takes no parameters beyond self/cls.

        Returns
        -------
        dict
            TODO one-line description of return value of LineItemSet.to_dict.

        Contract
        --------
        - #TODO contract lines for LineItemSet.to_dict.
        - #TODO document exceptions, mutations, and precision assumptions for LineItemSet.to_dict.

        @interface-report: show
        """
        return {
            "budget_items": [
                {
                    "Start_Date": line_item.start_date.isoformat(),
                    "End_Date": line_item.end_date.isoformat(),
                    "Priority": line_item.priority,
                    "interval": line_item.interval,
                    "Amount": line_item.amount,
                    "Memo": line_item.memo,
                    "Income_Flag": line_item.income_flag,
                    "Deferrable": line_item.deferrable,
                    "Partial_Payment_Allowed": line_item.partial_payment_allowed,
                }
                for line_item in self.line_items
            ]
        }

    def to_json(self):
        """
        @interface-report: show
        """
        return jsonpickle.encode(self, indent=4)

    def __add__(self, other: LineItemSet):
        """
        Set union.

        @interface-report: show
        """
        if not isinstance(other, LineItemSet):
            return NotImplemented

        return LineItemSet(self.line_items + other.line_items)

    #Codex-write-doctstring-OK
    @staticmethod
    def _line_item_key(line_item):
        """
        TODO DEFER one-line description of LineItemSet._line_item_key.

        TODO DEFER multi-line description of LineItemSet._line_item_key.
        TODO DEFER explain how LineItemSet._line_item_key participates in this module.
        TODO DEFER document important state, validation, or serialization behavior.

        Parameters
        ----------
        line_item : object
            TODO DEFER one-line description of LineItemSet._line_item_key.line_item.

        Returns
        -------
        object
            TODO DEFER one-line description of return value of LineItemSet._line_item_key.

        Contract
        --------
        - #TODO DEFER contract lines for LineItemSet._line_item_key.
        - #TODO DEFER document exceptions, mutations, and precision assumptions for LineItemSet._line_item_key.

        @interface-report: ignore
        """
        return (
            line_item.start_date,
            line_item.end_date,
            line_item.priority,
            line_item.interval,
            line_item.amount,
            line_item.memo,
            line_item.income_flag,
            line_item.deferrable,
            line_item.partial_payment_allowed,
        )

    def __sub__(self, other: LineItemSet):
        """
        Set subtraction.

        @interface-report: show
        """
        if not isinstance(other, LineItemSet):
            return NotImplemented

        remaining_items = list(self.line_items)
        for item_to_remove in other.line_items:
            item_to_remove_key = self._line_item_key(item_to_remove)
            for index, candidate_item in enumerate(remaining_items):
                if self._line_item_key(candidate_item) == item_to_remove_key:
                    remaining_items.pop(index)
                    break
            else:
                raise ValueError(
                    "Cannot subtract LineItemSet; item was not present: "
                    + str(item_to_remove)
                )

        return LineItemSet(remaining_items)

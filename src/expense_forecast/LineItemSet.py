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
import copy
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
    #TODO DOC manual review of LineItemSet.__init__ docstring
    def __init__(
        self,
        line_items__list=None,
        scenario_selections=None,
        scenario_dimensions=None,
        scenario_timelines=None,
    ):
        """
        #TODO DOC one-line description of LineItemSet.__init__.

        #TODO DOC multi-line description of LineItemSet.__init__.
        #TODO DOC explain how LineItemSet.__init__ participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        line_items__list : object
            #TODO DOC one-line description of LineItemSet.__init__.line_items__list.

        Returns
        -------
        None
            #TODO DOC one-line description of return value of LineItemSet.__init__.

        Contract
        --------
        - #TODO DOC contract lines for LineItemSet.__init__.
        - #TODO DOC document exceptions, mutations, and precision assumptions for LineItemSet.__init__.

        @interface-report: show
        """
        self.line_items__list = []
        self.line_items = []
        self.budget_items__list = self.line_items__list
        self.budget_items = self.line_items
        self.scenario_selections = dict(scenario_selections or {})
        self.scenario_dimensions = copy.deepcopy(scenario_dimensions or {})
        self.scenario_timelines = copy.deepcopy(scenario_timelines or {})

        if set(self.scenario_selections) - set(self.scenario_dimensions):
            missing = sorted(set(self.scenario_selections) - set(self.scenario_dimensions))
            raise ValueError(
                "Scenario selections are missing dimension definitions: "
                + ", ".join(missing)
            )
        for dimension_name, choice_name in self.scenario_selections.items():
            choices = self.scenario_dimensions[dimension_name]
            if choice_name not in choices:
                raise ValueError(
                    f"Unknown choice {choice_name!r} for ScenarioDimension "
                    f"{dimension_name!r}"
                )

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

    #TODO DOC manual review of LineItemSet.getLineItems docstring
    def getLineItems(self):

        """
        #TODO DOC one-line description of LineItemSet.getLineItems.

        #TODO DOC multi-line description of LineItemSet.getLineItems.
        #TODO DOC explain how LineItemSet.getLineItems participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that LineItemSet.getLineItems takes no parameters beyond self/cls.

        Returns
        -------
        pd.DataFrame
            #TODO DOC one-line description of return value of LineItemSet.getLineItems.

        Contract
        --------
        - #TODO DOC contract lines for LineItemSet.getLineItems.
        - #TODO DOC document exceptions, mutations, and precision assumptions for LineItemSet.getLineItems.

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
                "Recurrence_Key": [],
                "Recurrence_Anchor": [],
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
                    "Recurrence_Key": [line_item.recurrence_key],
                    "Recurrence_Anchor": [line_item.recurrence_anchor],
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

    #TODO DOC manual review of LineItemSet.getLineItemSchedule docstring
    def getLineItemSchedule(self):

        """
        #TODO DOC one-line description of LineItemSet.getLineItemSchedule.

        #TODO DOC multi-line description of LineItemSet.getLineItemSchedule.
        #TODO DOC explain how LineItemSet.getLineItemSchedule participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that LineItemSet.getLineItemSchedule takes no parameters beyond self/cls.

        Returns
        -------
        pd.DataFrame
            #TODO DOC one-line description of return value of LineItemSet.getLineItemSchedule.

        Contract
        --------
        - #TODO DOC contract lines for LineItemSet.getLineItemSchedule.
        - #TODO DOC document exceptions, mutations, and precision assumptions for LineItemSet.getLineItemSchedule.

        @interface-report: show
        """
        budget_schedule_rows = []
        for line_item in self.line_items:
            relative_num_days = (line_item.end_date - line_item.start_date).days
            relevant_date_sequence = generate_date_sequence(
                line_item.recurrence_anchor,
                (line_item.end_date - line_item.recurrence_anchor).days,
                line_item.interval,
            )
            relevant_date_sequence = [
                scheduled_date for scheduled_date in relevant_date_sequence
                if line_item.start_date <= scheduled_date <= line_item.end_date
            ]

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

    def getIncomeExpenseSchedule(self):
        """Return daily scheduled income and expense totals.

        Each scheduled occurrence is classified using its ``Income_Flag``.
        Multiple occurrences on the same date are summed, and dates containing
        only income or only expenses receive zero in the other column.
        """
        schedule = self.getLineItemSchedule()
        result_columns = ["Date", "Expense", "Income"]
        if schedule.empty:
            return pd.DataFrame(columns=result_columns)

        summarized = schedule[["Date", "Amount", "Income_Flag"]].copy()
        income_mask = summarized["Income_Flag"].map(bool)
        summarized["Expense"] = summarized["Amount"].where(~income_mask, 0)
        summarized["Income"] = summarized["Amount"].where(income_mask, 0)
        result = (
            summarized.groupby("Date", as_index=False, sort=True)[
                ["Expense", "Income"]
            ]
            .sum()
            .loc[:, result_columns]
        )
        return result

    def getIncomeExpenseScheduleBinned(self):
        """Return income and expense totals binned to each month's first day."""
        schedule = self.getIncomeExpenseSchedule()
        result_columns = ["Date", "Expense", "Income"]
        if schedule.empty:
            return pd.DataFrame(columns=result_columns)

        binned = schedule.copy()
        binned["Date"] = binned["Date"].map(
            lambda value: datetime.date(value.year, value.month, 1)
        )
        return (
            binned.groupby("Date", as_index=False, sort=True)[
                ["Expense", "Income"]
            ]
            .sum()
            .loc[:, result_columns]
        )

    #TODO DOC manual review of LineItemSet.addLineItem docstring
    def addLineItem(self, start_date, end_date, priority, interval, amount, memo, income_flag = False, **kwargs):
        """
        #TODO DOC one-line description of LineItemSet.addLineItem.

        #TODO DOC multi-line description of LineItemSet.addLineItem.
        #TODO DOC explain how LineItemSet.addLineItem participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        start_date : date
            #TODO DOC one-line description of LineItemSet.addLineItem.start_date.

        end_date : date
            #TODO DOC one-line description of LineItemSet.addLineItem.end_date.

        priority : int
            #TODO DOC one-line description of LineItemSet.addLineItem.priority.

        interval : str
            #TODO DOC one-line description of LineItemSet.addLineItem.interval.

        amount : float
            #TODO DOC one-line description of LineItemSet.addLineItem.amount.

        memo : str
            #TODO DOC one-line description of LineItemSet.addLineItem.memo.

        income_flag : bool
            #TODO DOC one-line description of LineItemSet.addLineItem.income_flag.

        **kwargs : dict
            #TODO DOC one-line description of LineItemSet.addLineItem.kwargs.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of LineItemSet.addLineItem.

        Contract
        --------
        - #TODO DOC contract lines for LineItemSet.addLineItem.
        - #TODO DOC document exceptions, mutations, and precision assumptions for LineItemSet.addLineItem.

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
            recurrence_key=kwargs.get('recurrence_key'),
            recurrence_anchor=kwargs.get('recurrence_anchor'),
        )

        # Check for duplicates
        all_line_items = self.getLineItems()
        if not all_line_items.empty:
            duplicates = all_line_items[
                (all_line_items["Priority"] == priority)
                & (all_line_items["Memo"] == memo)
                & (all_line_items["Start_Date"] <= end_date)
                & (all_line_items["End_Date"] >= start_date)
            ]
            if not duplicates.empty:
                error_message = f"A line item with priority {priority} and memo '{memo}' already exists."
                raise ValueError(error_message)

        # Append the line item
        self.line_items.append(line_item)

    #TODO DOC manual review of LineItemSet.to_dict docstring
    def to_dict(self):
        """
        #TODO DOC one-line description of LineItemSet.to_dict.

        #TODO DOC multi-line description of LineItemSet.to_dict.
        #TODO DOC explain how LineItemSet.to_dict participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that LineItemSet.to_dict takes no parameters beyond self/cls.

        Returns
        -------
        dict
            #TODO DOC one-line description of return value of LineItemSet.to_dict.

        Contract
        --------
        - #TODO DOC contract lines for LineItemSet.to_dict.
        - #TODO DOC document exceptions, mutations, and precision assumptions for LineItemSet.to_dict.

        @interface-report: show
        """
        result = {
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
                    "Recurrence_Key": line_item.recurrence_key,
                    "Recurrence_Anchor": line_item.recurrence_anchor.isoformat(),
                }
                for line_item in self.line_items
            ]
        }
        if self.scenario_selections:
            result["scenario_selections"] = dict(self.scenario_selections)
        if self.scenario_dimensions:
            result["scenario_dimensions"] = {
                dimension_name: {
                    choice_name: choice_set.to_dict()
                    for choice_name, choice_set in choices.items()
                }
                for dimension_name, choices in self.scenario_dimensions.items()
            }
        if self.scenario_timelines:
            result["scenario_timelines"] = {
                dimension_name: [
                    {
                        **entry,
                        "effective_date": entry["effective_date"].isoformat(),
                        "end_date": (
                            entry["end_date"].isoformat()
                            if entry.get("end_date") is not None else None
                        ),
                    }
                    for entry in timeline
                ]
                for dimension_name, timeline in self.scenario_timelines.items()
            }
        return result

    @classmethod
    def from_dict(cls, data):
        """Rebuild a LineItemSet from the structure returned by ``to_dict``."""
        if (
            not isinstance(data, dict)
            or not isinstance(data.get("budget_items"), list)
        ):
            raise TypeError(
                "LineItemSet.from_dict requires a 'budget_items' list"
            )

        def parsed_date(value, *, required=True):
            if value in (None, "None", ""):
                if required:
                    raise ValueError("Required line-item date is missing")
                return None
            if isinstance(value, datetime.datetime):
                return value.date()
            if isinstance(value, datetime.date):
                return value
            rendered = str(value)
            try:
                return datetime.date.fromisoformat(rendered)
            except ValueError:
                return datetime.datetime.strptime(
                    rendered, "%Y%m%d"
                ).date()

        line_items = []
        for row in data["budget_items"]:
            if not isinstance(row, dict):
                raise TypeError("budget_items must contain dictionaries")
            line_items.append(
                LineItem(
                    start_date=parsed_date(row["Start_Date"]),
                    end_date=parsed_date(row["End_Date"]),
                    priority=row["Priority"],
                    interval=row["interval"],
                    amount=row["Amount"],
                    memo=row["Memo"],
                    income_flag=row.get("Income_Flag", False),
                    deferrable=row.get("Deferrable"),
                    partial_payment_allowed=row.get(
                        "Partial_Payment_Allowed"
                    ),
                    recurrence_key=row.get("Recurrence_Key"),
                    recurrence_anchor=parsed_date(
                        row.get("Recurrence_Anchor"),
                        required=False,
                    ),
                )
            )

        scenario_dimensions = {
            dimension_name: {
                choice_name: cls.from_dict(choice_data)
                for choice_name, choice_data in choices_data.items()
            }
            for dimension_name, choices_data in data.get(
                "scenario_dimensions", {}
            ).items()
        }
        scenario_timelines = {
            dimension_name: [
                {
                    **entry,
                    "effective_date": parsed_date(
                        entry["effective_date"]
                    ),
                    "end_date": parsed_date(
                        entry.get("end_date"),
                        required=False,
                    ),
                }
                for entry in timeline
            ]
            for dimension_name, timeline in data.get(
                "scenario_timelines", {}
            ).items()
        }
        return cls(
            line_items,
            scenario_selections=data.get("scenario_selections", {}),
            scenario_dimensions=scenario_dimensions,
            scenario_timelines=scenario_timelines,
        )

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

        merged_selections = dict(self.scenario_selections)
        for dimension_name, choice_name in other.scenario_selections.items():
            existing_choice = merged_selections.get(dimension_name)
            if existing_choice is not None and existing_choice != choice_name:
                raise ValueError(
                    "Cannot combine LineItemSets with conflicting selections for "
                    f"ScenarioDimension {dimension_name!r}: "
                    f"{existing_choice!r} and {choice_name!r}"
                )
            merged_selections[dimension_name] = choice_name

        merged_dimensions = copy.deepcopy(self.scenario_dimensions)
        for dimension_name, choices in other.scenario_dimensions.items():
            if dimension_name in merged_dimensions:
                existing_definition = {
                    name: choice.to_dict()
                    for name, choice in merged_dimensions[dimension_name].items()
                }
                incoming_definition = {
                    name: choice.to_dict() for name, choice in choices.items()
                }
                if existing_definition != incoming_definition:
                    raise ValueError(
                        f"Conflicting definitions for ScenarioDimension {dimension_name!r}"
                    )
            else:
                merged_dimensions[dimension_name] = copy.deepcopy(choices)

        merged_timelines = copy.deepcopy(self.scenario_timelines)
        boundary_adjustments = []
        for dimension_name, timeline in other.scenario_timelines.items():
            combined = merged_timelines.get(dimension_name, []) + copy.deepcopy(timeline)
            combined.sort(key=lambda entry: entry["effective_date"])
            for previous, current in zip(combined, combined[1:]):
                previous_end = previous.get("end_date")
                if previous_end is None:
                    previous["end_date"] = current["effective_date"] - datetime.timedelta(days=1)
                    previous_end = previous["end_date"]
                if previous_end == current["effective_date"]:
                    boundary_adjustments.append((
                        previous_end,
                        set(previous.get("recurrence_keys", [])),
                    ))
                    previous["end_date"] = (
                        current["effective_date"] - datetime.timedelta(days=1)
                    )
                elif previous_end > current["effective_date"]:
                    raise ValueError(
                        f"Overlapping selections for ScenarioDimension {dimension_name!r}"
                    )
            merged_timelines[dimension_name] = combined

        anchors = {}
        for item in list(self.line_items) + list(other.line_items):
            anchors[item.recurrence_key] = min(
                anchors.get(item.recurrence_key, item.recurrence_anchor),
                item.recurrence_anchor,
            )

        merged_items = list(self.line_items)
        observed_keys = {self._line_item_key(item) for item in merged_items}
        for item in other.line_items:
            item_key = self._line_item_key(item)
            if item_key not in observed_keys:
                merged_items.append(item)
                observed_keys.add(item_key)
        merged_items = copy.deepcopy(merged_items)
        for item in merged_items:
            item.recurrence_anchor = anchors[item.recurrence_key]
            for boundary_date, recurrence_keys in boundary_adjustments:
                if (
                    item.end_date == boundary_date
                    and item.recurrence_key in recurrence_keys
                ):
                    item.end_date = boundary_date - datetime.timedelta(days=1)

        return LineItemSet(
            merged_items,
            scenario_selections=merged_selections,
            scenario_dimensions=merged_dimensions,
            scenario_timelines=merged_timelines,
        )

    #Codex-write-doctstring-OK
    @staticmethod
    def _line_item_key(line_item):
        """
        #TODO DEFER one-line description of LineItemSet._line_item_key.

        #TODO DEFER multi-line description of LineItemSet._line_item_key.
        #TODO DEFER explain how LineItemSet._line_item_key participates in this module.
        #TODO DEFER document important state, validation, or serialization behavior.

        Parameters
        ----------
        line_item : object
            #TODO DEFER one-line description of LineItemSet._line_item_key.line_item.

        Returns
        -------
        object
            #TODO DEFER one-line description of return value of LineItemSet._line_item_key.

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
            line_item.recurrence_key,
            line_item.recurrence_anchor,
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

        remaining_selections = dict(self.scenario_selections)
        remaining_dimensions = copy.deepcopy(self.scenario_dimensions)
        for dimension_name, choice_name in other.scenario_selections.items():
            if remaining_selections.get(dimension_name) != choice_name:
                raise ValueError(
                    f"Cannot subtract inactive scenario choice {dimension_name!r}: "
                    f"{choice_name!r}"
                )
            remaining_selections.pop(dimension_name)
            remaining_dimensions.pop(dimension_name, None)

        return LineItemSet(
            remaining_items,
            scenario_selections=remaining_selections,
            scenario_dimensions=remaining_dimensions,
            scenario_timelines=self.scenario_timelines,
        )

    def replace_scenario_choice(self, dimension_name, choice_name):
        """Return a copy with one active scenario choice replaced."""
        if dimension_name not in self.scenario_selections:
            raise ValueError(
                f"ScenarioDimension {dimension_name!r} has no active choice"
            )
        choices = self.scenario_dimensions[dimension_name]
        if choice_name not in choices:
            raise ValueError(
                f"Unknown choice {choice_name!r} for ScenarioDimension "
                f"{dimension_name!r}"
            )
        current_choice = self.scenario_selections[dimension_name]
        if current_choice == choice_name:
            return copy.deepcopy(self)

        current_choice_set = choices[current_choice]
        next_choice_set = choices[choice_name]
        remaining_items = list(self.line_items)
        for item_to_remove in current_choice_set.line_items:
            key = self._line_item_key(item_to_remove)
            for index, candidate in enumerate(remaining_items):
                if self._line_item_key(candidate) == key:
                    remaining_items.pop(index)
                    break
            else:
                raise ValueError(
                    f"Active choice {dimension_name!r}: {current_choice!r} is "
                    "missing one or more of its line items"
                )

        observed_keys = {self._line_item_key(item) for item in remaining_items}
        for item in next_choice_set.line_items:
            key = self._line_item_key(item)
            if key not in observed_keys:
                remaining_items.append(item)
                observed_keys.add(key)

        selections = dict(self.scenario_selections)
        selections[dimension_name] = choice_name
        return LineItemSet(
            remaining_items,
            scenario_selections=selections,
            scenario_dimensions=self.scenario_dimensions,
            scenario_timelines=self.scenario_timelines,
        )

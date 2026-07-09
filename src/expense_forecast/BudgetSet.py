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
from .BudgetItem import BudgetItem
import pandas as pd
import datetime
from . import log_methods
import jsonpickle
from .generate_date_sequence import generate_date_sequence
import logging


# logger = setup_logger('BudgetSet', './log/BudgetSet.log', level=logging.INFO)
logger = logging.getLogger(__name__)

#
# def initialize_from_dataframe(budget_set_df):
#     B = BudgetSet([])
#     try:
#         for index, row in budget_set_df.iterrows():
#             sd = str(row.start_date).replace("-", "")
#             ed = str(row.end_date).replace("-", "")
#             B.addBudgetItem(
#                 sd,
#                 ed,
#                 row.priority,
#                 row.cadence.replace("-", "").lower(),
#                 row.amount,
#                 row.memo,
#                 row.deferrable,
#                 row.partial_payment_allowed,
#             )
#     except Exception as e:
#         print(e.args)
#         raise e
#     return B
#
#
# def initialize_from_json_string(json_string):
#     raise NotImplementedError


#TODO manual review of BudgetSet docstring
class BudgetSet:

    """
    Summary
    -------

    Description
    -----------

    Contract
    --------

    @interface-report: show
    """
    #TODO manual review of BudgetSet.__init__ docstring
    def __init__(self, budget_items__list=None):
        """
        TODO one-line description of BudgetSet.__init__.

        TODO multi-line description of BudgetSet.__init__.
        TODO explain how BudgetSet.__init__ participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        budget_items__list : object
            TODO one-line description of BudgetSet.__init__.budget_items__list.

        Returns
        -------
        None
            TODO one-line description of return value of BudgetSet.__init__.

        Contract
        --------
        - #TODO contract lines for BudgetSet.__init__.
        - #TODO document exceptions, mutations, and precision assumptions for BudgetSet.__init__.

        @interface-report: show
        """
        self.budget_items__list = []
        self.budget_items = []

        if budget_items__list is None:
            return

        required_attributes = [
            "start_date",
            "end_date",
            "priority",
            "cadence",
            "amount",
            "memo",
        ]

        required_methods = [
            "to_dataframe",
            "to_dict",
            "to_json",
        ]

        for budget_item in budget_items__list:
            for attr in required_attributes:
                if not hasattr(budget_item, attr):
                    raise ValueError(
                        f"BudgetItem is missing required attribute '{attr}'. "
                        f"Found attributes: {[x for x in dir(budget_item) if '__' not in x]}"
                    )

            for method in required_methods:
                if not hasattr(budget_item, method) or not callable(getattr(budget_item, method)):
                    raise ValueError(
                        f"BudgetItem is missing required method '{method}'."
                    )

            self.budget_items__list.append(budget_item)
            self.budget_items.append(budget_item)

    #TODO manual review of BudgetSet.__str__ docstring
    def __str__(self):
        """
        TODO one-line description of BudgetSet.__str__.

        TODO multi-line description of BudgetSet.__str__.
        TODO explain how BudgetSet.__str__ participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that BudgetSet.__str__ takes no parameters beyond self/cls.

        Returns
        -------
        str
            TODO one-line description of return value of BudgetSet.__str__.

        Contract
        --------
        - #TODO contract lines for BudgetSet.__str__.
        - #TODO document exceptions, mutations, and precision assumptions for BudgetSet.__str__.

        @interface-report: show
        """
        return self.getBudgetItems().to_string()

    #TODO manual review of BudgetSet.getBudgetItems docstring
    def getBudgetItems(self):

        """
        TODO one-line description of BudgetSet.getBudgetItems.

        TODO multi-line description of BudgetSet.getBudgetItems.
        TODO explain how BudgetSet.getBudgetItems participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that BudgetSet.getBudgetItems takes no parameters beyond self/cls.

        Returns
        -------
        pd.DataFrame
            TODO one-line description of return value of BudgetSet.getBudgetItems.

        Contract
        --------
        - #TODO contract lines for BudgetSet.getBudgetItems.
        - #TODO document exceptions, mutations, and precision assumptions for BudgetSet.getBudgetItems.

        @interface-report: show
        """
        all_budget_items_df = pd.DataFrame(
            {
                "Start_Date": [],
                "End_Date": [],
                "Priority": [],
                "Cadence": [],
                "Amount": [],
                "Memo": [],
                "Income_Flag": [],
                "Deferrable": [],
                "Partial_Payment_Allowed": [],
            }
        )

        for budget_item in self.budget_items:
            new_budget_item_row_df = pd.DataFrame(
                {
                    "Start_Date": [budget_item.start_date],
                    "End_Date": [budget_item.end_date],
                    "Priority": [budget_item.priority],
                    "Cadence": [budget_item.cadence],
                    "Amount": [budget_item.amount],
                    "Memo": [budget_item.memo],
                    "Income_Flag": [budget_item.income_flag],
                    "Deferrable": [budget_item.deferrable],
                    "Partial_Payment_Allowed": [budget_item.partial_payment_allowed],
                }
            )

            if (not all_budget_items_df.empty) & (not new_budget_item_row_df.empty):
                all_budget_items_df = pd.concat(
                    [all_budget_items_df, new_budget_item_row_df], axis=0
                )

            if (all_budget_items_df.empty) & (not new_budget_item_row_df.empty):
                all_budget_items_df = new_budget_item_row_df

        all_budget_items_df.reset_index(drop=True, inplace=True)
        return all_budget_items_df

    #TODO manual review of BudgetSet.getBudgetSchedule docstring
    def getBudgetSchedule(self):

        """
        TODO one-line description of BudgetSet.getBudgetSchedule.

        TODO multi-line description of BudgetSet.getBudgetSchedule.
        TODO explain how BudgetSet.getBudgetSchedule participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that BudgetSet.getBudgetSchedule takes no parameters beyond self/cls.

        Returns
        -------
        pd.DataFrame
            TODO one-line description of return value of BudgetSet.getBudgetSchedule.

        Contract
        --------
        - #TODO contract lines for BudgetSet.getBudgetSchedule.
        - #TODO document exceptions, mutations, and precision assumptions for BudgetSet.getBudgetSchedule.

        @interface-report: show
        """
        budget_schedule_rows = []
        for budget_item in self.budget_items:
            relative_num_days = (budget_item.end_date - budget_item.start_date).days
            relevant_date_sequence = generate_date_sequence(
                budget_item.start_date, relative_num_days, budget_item.cadence
            )

            for scheduled_date in relevant_date_sequence:
                budget_schedule_rows.append(
                    {
                        "Date": scheduled_date,
                        "Priority": budget_item.priority,
                        "Amount": budget_item.amount,
                        "Memo": budget_item.memo,
                        "Income_Flag": budget_item.income_flag,
                        "Deferrable": budget_item.deferrable,
                        "Partial_Payment_Allowed": budget_item.partial_payment_allowed,
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

    #TODO manual review of BudgetSet.addBudgetItem docstring
    def addBudgetItem(self, start_date, end_date, priority, cadence, amount, memo, income_flag = False, **kwargs):
        """
        TODO one-line description of BudgetSet.addBudgetItem.

        TODO multi-line description of BudgetSet.addBudgetItem.
        TODO explain how BudgetSet.addBudgetItem participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        start_date : date
            TODO one-line description of BudgetSet.addBudgetItem.start_date.

        end_date : date
            TODO one-line description of BudgetSet.addBudgetItem.end_date.

        priority : int
            TODO one-line description of BudgetSet.addBudgetItem.priority.

        cadence : str
            TODO one-line description of BudgetSet.addBudgetItem.cadence.

        amount : float
            TODO one-line description of BudgetSet.addBudgetItem.amount.

        memo : str
            TODO one-line description of BudgetSet.addBudgetItem.memo.

        income_flag : bool
            TODO one-line description of BudgetSet.addBudgetItem.income_flag.

        **kwargs : dict
            TODO one-line description of BudgetSet.addBudgetItem.kwargs.

        Returns
        -------
        object
            TODO one-line description of return value of BudgetSet.addBudgetItem.

        Contract
        --------
        - #TODO contract lines for BudgetSet.addBudgetItem.
        - #TODO document exceptions, mutations, and precision assumptions for BudgetSet.addBudgetItem.

        @interface-report: show
        """
        budget_item = BudgetItem(
            start_date,
            end_date,
            priority,
            cadence,
            amount,
            memo,
            income_flag=income_flag,
            deferrable=kwargs.get('deferrable',None),
            partial_payment_allowed=kwargs.get('partial_payment_allowed',None),
        )

        # Check for duplicates
        all_budget_items = self.getBudgetItems()
        if not all_budget_items.empty:
            duplicates = all_budget_items[
                (all_budget_items["Priority"] == priority)
                & (all_budget_items["Memo"] == memo)
            ]
            if not duplicates.empty:
                error_message = f"A budget item with priority {priority} and memo '{memo}' already exists."
                raise ValueError(error_message)

        # Append the budget item
        self.budget_items.append(budget_item)

    #TODO manual review of BudgetSet.to_dict docstring
    def to_dict(self):
        """
        TODO one-line description of BudgetSet.to_dict.

        TODO multi-line description of BudgetSet.to_dict.
        TODO explain how BudgetSet.to_dict participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that BudgetSet.to_dict takes no parameters beyond self/cls.

        Returns
        -------
        dict
            TODO one-line description of return value of BudgetSet.to_dict.

        Contract
        --------
        - #TODO contract lines for BudgetSet.to_dict.
        - #TODO document exceptions, mutations, and precision assumptions for BudgetSet.to_dict.

        @interface-report: show
        """
        return {
            "budget_items": [
                {
                    "Start_Date": budget_item.start_date.isoformat(),
                    "End_Date": budget_item.end_date.isoformat(),
                    "Priority": budget_item.priority,
                    "Cadence": budget_item.cadence,
                    "Amount": budget_item.amount,
                    "Memo": budget_item.memo,
                    "Income_Flag": budget_item.income_flag,
                    "Deferrable": budget_item.deferrable,
                    "Partial_Payment_Allowed": budget_item.partial_payment_allowed,
                }
                for budget_item in self.budget_items
            ]
        }

    #TODO manual review of BudgetSet.to_json docstring
    def to_json(self):
        """
        TODO one-line description of BudgetSet.to_json.

        TODO multi-line description of BudgetSet.to_json.
        TODO explain how BudgetSet.to_json participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that BudgetSet.to_json takes no parameters beyond self/cls.

        Returns
        -------
        str
            TODO one-line description of return value of BudgetSet.to_json.

        Contract
        --------
        - #TODO contract lines for BudgetSet.to_json.
        - #TODO document exceptions, mutations, and precision assumptions for BudgetSet.to_json.

        @interface-report: show
        """
        return jsonpickle.encode(self, indent=4)

    #TODO manual review of BudgetSet.__add__ docstring
    def __add__(self, other: BudgetSet):
        """
        TODO one-line description of BudgetSet.__add__.

        TODO multi-line description of BudgetSet.__add__.
        TODO explain how BudgetSet.__add__ participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        other : object
            TODO one-line description of BudgetSet.__add__.other.

        Returns
        -------
        object
            TODO one-line description of return value of BudgetSet.__add__.

        Contract
        --------
        - #TODO contract lines for BudgetSet.__add__.
        - #TODO document exceptions, mutations, and precision assumptions for BudgetSet.__add__.

        @interface-report: show
        """
        if not isinstance(other, BudgetSet):
            return NotImplemented

        return BudgetSet(self.budget_items + other.budget_items)

    #TODO manual review of BudgetSet._budget_item_key docstring
    @staticmethod
    def _budget_item_key(budget_item):
        """
        TODO one-line description of BudgetSet._budget_item_key.

        TODO multi-line description of BudgetSet._budget_item_key.
        TODO explain how BudgetSet._budget_item_key participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        budget_item : object
            TODO one-line description of BudgetSet._budget_item_key.budget_item.

        Returns
        -------
        object
            TODO one-line description of return value of BudgetSet._budget_item_key.

        Contract
        --------
        - #TODO contract lines for BudgetSet._budget_item_key.
        - #TODO document exceptions, mutations, and precision assumptions for BudgetSet._budget_item_key.

        @interface-report: show
        """
        return (
            budget_item.start_date,
            budget_item.end_date,
            budget_item.priority,
            budget_item.cadence,
            budget_item.amount,
            budget_item.memo,
            budget_item.income_flag,
            budget_item.deferrable,
            budget_item.partial_payment_allowed,
        )

    #TODO manual review of BudgetSet.__sub__ docstring
    def __sub__(self, other: BudgetSet):
        """
        TODO one-line description of BudgetSet.__sub__.

        TODO multi-line description of BudgetSet.__sub__.
        TODO explain how BudgetSet.__sub__ participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        other : object
            TODO one-line description of BudgetSet.__sub__.other.

        Returns
        -------
        object
            TODO one-line description of return value of BudgetSet.__sub__.

        Contract
        --------
        - #TODO contract lines for BudgetSet.__sub__.
        - #TODO document exceptions, mutations, and precision assumptions for BudgetSet.__sub__.

        @interface-report: show
        """
        if not isinstance(other, BudgetSet):
            return NotImplemented

        remaining_items = list(self.budget_items)
        for item_to_remove in other.budget_items:
            item_to_remove_key = self._budget_item_key(item_to_remove)
            for index, candidate_item in enumerate(remaining_items):
                if self._budget_item_key(candidate_item) == item_to_remove_key:
                    remaining_items.pop(index)
                    break
            else:
                raise ValueError(
                    "Cannot subtract BudgetSet; item was not present: "
                    + str(item_to_remove)
                )

        return BudgetSet(remaining_items)

if __name__ == "__main__":
    import doctest

    doctest.testmod()

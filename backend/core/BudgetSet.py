from . import BudgetItem
import pandas as pd
import datetime
# from log_methods import log_in_color
import jsonpickle
from . import generate_date_sequence
import logging
from models.budgetset.params import BudgetItemParams
from typing import Optional, List

logger = logging.getLogger("core.BudgetSet")


def initialize_from_dataframe(budget_set_df):
    B = BudgetSet([])
    try:
        for index, row in budget_set_df.iterrows():
            sd = str(row.start_date).replace("-", "")
            ed = str(row.end_date).replace("-", "")
            B.addBudgetItem(
                sd,
                ed,
                row.priority,
                row.cadence.replace("-", "").lower(),
                row.amount,
                row.memo,
                row.deferrable,
                row.partial_payment_allowed,
            )
    except Exception as e:
        print(e.args)
        raise e
    return B


def initialize_from_json_string(json_string):
    raise NotImplementedError


class BudgetSet:

    def __init__(self, budget_items__list: Optional[List[BudgetItemParams]] = None):
        """
        Add BudgetItemParams to self.budget_items with type checking.
        """
        self.budget_items = []

        if budget_items__list is None:
            return

        for item in budget_items__list:
            if not isinstance(item, BudgetItemParams):
                raise TypeError(f"Expected BudgetItemParams, got {type(item).__name__}")
            self.addBudgetItem(item)

    def __str__(self):
        return self.getBudgetItems().to_string()

    def getBudgetItems(self):
        """
        Returns a DataFrame of BudgetItems.

        :return: DataFrame
        """
        all_budget_items_df = pd.DataFrame(
            {
                "Start_Date": [],
                "End_Date": [],
                "Priority": [],
                "Cadence": [],
                "Amount": [],
                "Memo": [],
                "Deferrable": [],
                "Partial_Payment_Allowed": [],
            }
        )

        for budget_item in self.budget_items:
            new_budget_item_row_df = pd.DataFrame(
                {
                    "Start_Date": [budget_item.start_date_YYYYMMDD],
                    "End_Date": [budget_item.end_date_YYYYMMDD],
                    "Priority": [budget_item.priority],
                    "Cadence": [budget_item.cadence],
                    "Amount": [budget_item.amount],
                    "Memo": [budget_item.memo],
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

    def getBudgetSchedule(self):
        """
        Generate a dataframe of proposed transactions

        :param start_date_YYYYMMDD:
        :param num_days:
        :return:
        """

        current_budget_schedule = pd.DataFrame(
            {
                "Date": [],
                "Priority": [],
                "Amount": [],
                "Memo": [],
                "Deferrable": [],
                "Partial_Payment_Allowed": [],
            }
        )
        for budget_item in self.budget_items:
            relative_num_days = (
                datetime.datetime.strptime(budget_item.end_date_YYYYMMDD, "%Y%m%d")
                - datetime.datetime.strptime(budget_item.start_date_YYYYMMDD, "%Y%m%d")
            ).days
            relevant_date_sequence = generate_date_sequence(
                budget_item.start_date_YYYYMMDD, relative_num_days, budget_item.cadence
            )

            relevant_date_sequence_df = pd.DataFrame(relevant_date_sequence)
            relevant_date_sequence_df = relevant_date_sequence_df.rename(
                columns={0: "Date"}
            )
            current_item_cols_df = pd.DataFrame(
                (
                    budget_item.priority,
                    budget_item.amount,
                    budget_item.memo,
                    budget_item.deferrable,
                    budget_item.partial_payment_allowed,
                )
            ).T

            current_item_cols_df = current_item_cols_df.rename(
                columns={
                    0: "Priority",
                    1: "Amount",
                    2: "Memo",
                    3: "Deferrable",
                    4: "Partial_Payment_Allowed",
                }
            )

            new_budget_schedule_rows_df = relevant_date_sequence_df.merge(
                current_item_cols_df, how="cross"
            )

            current_budget_schedule = pd.concat(
                [current_budget_schedule, new_budget_schedule_rows_df], axis=0
            )

        current_budget_schedule.sort_values(inplace=True, axis=0, by="Date")
        current_budget_schedule.reset_index(inplace=True, drop=True)

        return current_budget_schedule

    # def addBudgetItem(self, params: BudgetItemParams, validate: bool = True) -> None:
    #     budget_item = BudgetItem.BudgetItem(
    #             start_date = params.start_date,
    #             end_date = params.end_date,
    #             priority=params.priority,
    #             cadence=params.cadence,
    #             amount=params.amount,
    #             memo=params.memo,
    #             deferrable=params.deferrable,
    #             partial_payment_allowed=params.partial_payment_allowed
    #         )
        
    #     if validate:
    #         pass #todo validation
    #     self.budget_items.append(budget_item)
    def addBudgetItem(self, item: BudgetItemParams, validate: bool = True) -> None:
        # This is your custom logic – for now we'll just store it.
        if validate:
            pass #todo validation
        self.budget_items.append(item)

    # def addBudgetItem(
    #     self,
    #     start_date_YYYYMMDD,
    #     end_date_YYYYMMDD,
    #     priority,
    #     cadence,
    #     amount,
    #     memo,
    #     deferrable=False,
    #     partial_payment_allowed=False,
    #     print_debug_messages=True,
    #     raise_exceptions=True,
    # ):
    #     """
    #     Add a BudgetItem to the list of budget items.

    #     :param str start_date_YYYYMMDD: Start date in YYYYMMDD format.
    #     :param str end_date_YYYYMMDD: End date in YYYYMMDD format.
    #     :param int priority: Priority level of the budget item.
    #     :param str cadence: Frequency of the budget item.
    #     :param float amount: Amount of the budget item.
    #     :param str memo: Memo for the budget item.
    #     :param bool deferrable: Indicates if the budget item is deferrable.
    #     :param bool partial_payment_allowed: Indicates if partial payments are allowed.
    #     :param bool print_debug_messages: If True, prints debug messages.
    #     :param bool raise_exceptions: If True, raises exceptions on errors.
    #     :raises ValueError: If a budget item with the same priority and memo already exists.
    #     """

    #     try:
    #         budget_item = BudgetItem.BudgetItem(
    #             start_date_YYYYMMDD,
    #             end_date_YYYYMMDD,
    #             priority,
    #             cadence,
    #             amount,
    #             memo,
    #             deferrable,
    #             partial_payment_allowed,
    #             print_debug_messages,
    #             raise_exceptions,
    #         )
    #     except Exception as e:
    #         if print_debug_messages:
    #             log_in_color(
    #                 logger, "red", "error", f"Failed to create BudgetItem: {e}"
    #             )
    #         if raise_exceptions:
    #             raise
    #         else:
    #             return

    #     # Check for duplicates
    #     all_budget_items = self.getBudgetItems()
    #     if not all_budget_items.empty:
    #         duplicates = all_budget_items[
    #             (all_budget_items["Priority"] == priority)
    #             & (all_budget_items["Memo"] == memo)
    #         ]
    #         if not duplicates.empty:
    #             error_message = f"A budget item with priority {priority} and memo '{memo}' already exists."
    #             if print_debug_messages:
    #                 log_in_color(logger, "red", "error", error_message)
    #                 log_in_color(logger, "red", "error", "Existing budget items:")
    #                 log_in_color(logger, "red", "error", duplicates.to_string())
    #             if raise_exceptions:
    #                 raise ValueError(error_message)
    #             else:
    #                 return

    #     # Append the budget item
    #     self.budget_items.append(budget_item)

    def to_json(self):
        """
        Get a JSON <string> representing the <BudgetSet> object.

        """
        return jsonpickle.encode(self, indent=4)


if __name__ == "__main__":
    import doctest

    doctest.testmod()

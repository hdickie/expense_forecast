from . import LineItem
import pandas as pd
import datetime
# from log_methods import log_in_color
import jsonpickle
from . import generate_date_sequence
import logging
from models.lineitem.params import LineItemParams
from typing import Optional, List

import hashlib

logger = logging.getLogger("core.LineItemSet")


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


class LineItemSet:

    def __init__(self, line_items__list: Optional[List[LineItemParams]] = None):
        """
        Add BudgetItemParams to self.budget_items with type checking.
        """
        self.line_items = []

        self.stable_id_cache_is_valid = False

        if line_items__list is None:
            return

        for item in line_items__list:
            if not isinstance(item, LineItemParams):
                raise TypeError(f"Expected LineItemParams, got {type(item).__name__}")
            self.addLineItem(item)

    def __str__(self):
        return self.getLineItems().to_string()

    def getLineItems(self):
        """
        Returns a DataFrame of BudgetItems.

        :return: DataFrame
        """
        all_line_items_df = pd.DataFrame(
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

        for line_item in self.line_items:
            new_line_item_row_df = pd.DataFrame(
                {
                    "Start_Date": [line_item.start_date],
                    "End_Date": [line_item.end_date],
                    "Priority": [line_item.priority],
                    "Cadence": [line_item.cadence],
                    "Amount": [line_item.amount],
                    "Memo": [line_item.memo],
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
    
    def get_stable_id(self):
        # if self.stable_id_cache_is_valid:
        #     return self.stable_id
        m = hashlib.sha256()
        m.update(self.getLineItems().to_string().encode())
        self.stable_id = m.hexdigest()
        self.stable_id_cache_is_valid = True
        return self.stable_id

    def getLineItemSchedule(self) -> pd.DataFrame:
        """
        Generate a DataFrame of proposed transactions.

        :return: DataFrame with columns:
            - Date (datetime.datetime)
            - Priority (int)
            - Amount (float)
            - Memo (str)
            - Deferrable (bool)
            - Partial_Payment_Allowed (bool)
        """
        if len(self.line_items) == 0:
            return pd.DataFrame({
                    "Date": [],
                    "Priority":  [],
                    "Amount":  [],
                    "Memo":  [],
                    "Deferrable":  [],
                    "Partial_Payment_Allowed":  [],
                })
        
        schedule_rows = []

        for item in self.line_items:
            num_days = (item.end_date - item.start_date).days
            dates = generate_date_sequence.generate_date_sequence(
                item.start_date, num_days, item.cadence
            )

            for date in dates:
                schedule_rows.append({
                    "Date": pd.to_datetime(date),  # ensure datetime
                    "Priority": item.priority,
                    "Amount": item.amount,
                    "Memo": item.memo,
                    "Deferrable": item.deferrable,
                    "Partial_Payment_Allowed": item.partial_payment_allowed,
                })

        schedule_df = pd.DataFrame(schedule_rows)

        if not schedule_df.empty:
            schedule_df.sort_values(by="Date", inplace=True)
            schedule_df.reset_index(drop=True, inplace=True)

        return schedule_df


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
    def addLineItem(self, item: LineItemParams, validate: bool = True) -> None:
        # This is your custom logic – for now we'll just store it.
        if validate:
            pass #todo validation
        self.line_items.append(item)

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

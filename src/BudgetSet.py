import BudgetItem
import pandas as pd
import datetime
from log_methods import log_in_color
import jsonpickle
from generate_date_sequence import generate_date_sequence
import logging

from log_methods import setup_logger

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


class BudgetSet:

    def __init__(self, budget_items__list=None):
        self.budget_items__list = []
        if budget_items__list is None:
            return

        required_attributes = [
            "start_date",
            "end_date",
            "priority",
            "cadence",
            "amount",
            "memo",
            "_validate_amount",
            "_validate_memo",
            "_validate_priority",
            "_validate_cadence",
            "_validate_start_and_end_date",
            "to_json"
        ]
        allowed_kwargs = ["deferrable", "partial_payment_allowed","income_flag"]

        self.budget_items = []
        for budget_item in budget_items__list:

            # not perfect but good enough
            non_builtin_attr = [x for x in dir(budget_item) if '__' not in x]
            for attr in non_builtin_attr:
                try:
                    assert attr in required_attributes or attr in allowed_kwargs
                except Exception:
                    raise ValueError('Unrecognized attribute on BudgetItem: '+str(attr))

            for required_attr in required_attributes:
                assert required_attr in non_builtin_attr

            self.budget_items.append(budget_item)

    def __str__(self):
        return self.getBudgetItems().to_string()

    def getBudgetItems(self):

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

    def getBudgetSchedule(self):

        current_budget_schedule = pd.DataFrame(
            {
                "Date": [],
                "Priority": [],
                "Amount": [],
                "Memo": [],
                "Income_Flag": [],
                "Deferrable": [],
                "Partial_Payment_Allowed": [],
            }
        )
        for budget_item in self.budget_items:
            relative_num_days = (budget_item.end_date - budget_item.start_date).days
            relevant_date_sequence = generate_date_sequence(
                budget_item.start_date, relative_num_days, budget_item.cadence
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
                    budget_item.income_flag,
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

    def addBudgetItem(self, start_date, end_date, priority, cadence, amount, memo, income_flag = False, **kwargs):
        budget_item = BudgetItem.BudgetItem(
            start_date,
            end_date,
            priority,
            cadence,
            amount,
            memo,
            income_flag,
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

    def to_json(self):
        return jsonpickle.encode(self, indent=4)


if __name__ == "__main__":
    import doctest

    doctest.testmod()

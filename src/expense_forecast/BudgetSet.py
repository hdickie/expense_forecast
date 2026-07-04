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


class BudgetSet:

    def __init__(self, budget_items__list=None):
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

    def addBudgetItem(self, start_date, end_date, priority, cadence, amount, memo, income_flag = False, **kwargs):
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

    def to_dict(self):
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

    def to_json(self):
        return jsonpickle.encode(self, indent=4)


if __name__ == "__main__":
    import doctest

    doctest.testmod()

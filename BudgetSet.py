import BudgetItem, pandas as pd, datetime
from hd_util import *

class BudgetSet:

    def __init__(self,budget_items__list=[]):
        self.budget_items = []
        for budget_item in budget_items__list:
            print(budget_item)

    def __str__(self):
        return_string = ""
        for budget_item in self.budget_items:
            return_string = str(budget_item.start_date) + " | " + str(budget_item.priority) + " | " + str(budget_item.cadence).ljust(10) + " | "
            return_string += str(budget_item.amount).ljust(10) + " | " + str(budget_item.memo)

        return return_string

    def __repr__(self):
        return str(self)

    def addBudgetItem(self,
                 start_date = '',
                 priority = '',
                 cadence='',
                 amount='',
                 memo=''):

        budget_item = BudgetItem.BudgetItem(start_date,
                 priority,
                 cadence,
                 amount,
                 memo)

        self.budget_items.append(budget_item)

    def getBudgetItems(self):
        all_budget_items_df = pd.DataFrame({'start_date': [], 'priority': [], 'cadence': [], 'amount': [],
                                        'memo': []
                                        })

        for budget_item in self.budget_items:
            new_budget_item_row_df = pd.DataFrame({'start_date': [budget_item.start_date],
                                               'priority': [budget_item.priority],
                                               'cadence': [budget_item.cadence],
                                               'amount': [budget_item.amount],
                                               'memo': [budget_item.memo]
                                               })

            all_budget_items_df = pd.concat([all_budget_items_df, new_budget_item_row_df], axis=0)
            all_budget_items_df.reset_index(drop=True, inplace=True)

        return all_budget_items_df

    def getBudgetSchedule(self,start_date_YYYYMMDD,num_days):

        current_budget_schedule = pd.DataFrame({'Date':[],'Priority':[],'Amount':[],'Memo':[]})

        for budget_item in self.budget_items:
            relevant_date_sequence = generate_date_sequence(start_date_YYYYMMDD,num_days,budget_item.cadence)

            relevant_date_sequence_df = pd.DataFrame(relevant_date_sequence)
            relevant_date_sequence_df = relevant_date_sequence_df.rename(columns={0:"Date"})
            current_item_cols_df = pd.DataFrame((budget_item.priority, budget_item.amount, budget_item.memo)).T

            current_item_cols_df = current_item_cols_df.rename(columns=
                {0: "Priority", 1: "Amount", 2: "Memo"})

            new_budget_schedule_rows_df = relevant_date_sequence_df.merge(current_item_cols_df, how="cross")

            current_budget_schedule = pd.concat([current_budget_schedule,new_budget_schedule_rows_df],axis=0)

            #print(current_budget_schedule.head(1))

        current_budget_schedule.sort_values(inplace=True,axis=0,by="Date")
        current_budget_schedule.reset_index(inplace=True,drop=True)
        return current_budget_schedule

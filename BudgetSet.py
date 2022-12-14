import BudgetItem, pandas as pd, datetime
from project_utilities import *

class BudgetSet:

    def __init__(self,budget_items__list=[]):
        """
        Add a budget_item to self.budget_items. Input validation is performed.

        | Test Cases
        | Expected Successes
        | S1: input an empty list #todo refactor BudgetSet.BudgetSet() doctest S1 to use _S1 label
        | S1: input a list of BudgetItem objects #todo refactor BudgetSet.BudgetSet() doctest S2 to use _S2 label
        |
        | Expected Fails
        | F1 input a list with objects that are not BudgetItem type. Do this without explicitly checking type. #todo refactor BudgetSet.BudgetSet() doctest F1 to use _F1 label
        | F2 input a list with a BudgetItem with a memo that matches a BudgetItem already in self.budget_items

        :param budget_items__list:
        """
        self.budget_items = []
        for budget_item in budget_items__list:
            self.budget_items.append(budget_item)

    def __str__(self):
        return self.getBudgetItems().to_string()

    def __repr__(self):
        return str(self)

    def getBudgetItems(self):
        """
        Returns a DataFrame of BudgetItems.

        :return: DataFrame
        """
        all_budget_items_df = pd.DataFrame({'Start_date': [], 'Priority': [], 'Cadence': [], 'Amount': [],
                                        'Memo': []
                                        })

        for budget_item in self.budget_items:
            new_budget_item_row_df = pd.DataFrame({'Start_date': [budget_item.start_date],
                                               'Priority': [budget_item.priority],
                                               'Cadence': [budget_item.cadence],
                                               'Amount': [budget_item.amount],
                                               'Memo': [budget_item.memo]
                                               })

            all_budget_items_df = pd.concat([all_budget_items_df, new_budget_item_row_df], axis=0)
            all_budget_items_df.reset_index(drop=True, inplace=True)

        return all_budget_items_df


    def getBudgetSchedule(self,start_date_YYYYMMDD,num_days):
        """
        Generate a dataframe of proposed transactions

        #todo write doctests for BudgetSet.getBudgetSchedule()

        :param start_date_YYYYMMDD:
        :param num_days:
        :return:
        """
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

    def addBudgetItem(self,
                 start_date_YYYYMMDD,
                 priority,
                 cadence,
                 amount,
                 deferrable,
                 memo,
                 print_debug_messages = True,
                 raise_exceptions = True):
        """ Add a BudgetItem to list BudgetItem.budget_items.

        | Test Cases
        | Expected Successes
        | S1: Provide no parameters
        | S2: provide valid parameters #todo refactor BudgetSet.addBudgetItem() doctest S2 to use _S2 label
        |
        | Expected Fails
        | F1 Provide incorrect types for all parameters #todo refactor BudgetSet.BudgetSet() doctest F1 to use _F1 label
        | F2 add a BudgetItem where there are 2 BudgetItems with the same memo

        >>> print(BudgetSet().toJSON())
        Empty DataFrame
        Columns: [Start_date, Priority, Cadence, Amount, Memo]
        Index: []

        >>> print(BudgetSet([ BudgetItem.BudgetItem(start_date_YYYYMMDD='20000101',
        ... priority=1,
        ... cadence='once',
        ... amount=0,
        ... deferrable=False,
        ... memo='Income')
        ... ]).toJSON())
        {
        {
        "Start_Date":"2000-01-01 00:00:00",
        "Priority":"1",
        "Cadence":"once",
        "Amount":"0.0",
        "Deferrable":"False",
        "Memo":"Income"
        }
        }

        """
        budget_item = BudgetItem.BudgetItem(start_date_YYYYMMDD,
                 priority,
                 cadence,
                 amount,
                 deferrable,
                 memo,print_debug_messages,raise_exceptions)

        #todo error when duplicate budget item. (user should make memo different its not that hard.)
        #that is, if amount and date are the same, different memos are required. its fine otherwise
        self.budget_items.append(budget_item)

    def toJSON(self):
        """
        Get a JSON <string> representing the <BudgetSet> object.

        """
        JSON_string = "{\n"
        for i in range(0, len(self.budget_items)):
            budget_item = self.budget_items[i]
            JSON_string += budget_item.toJSON()
            if i+1 != len(self.budget_items):
                JSON_string += ","
            JSON_string += '\n'
        JSON_string += '}'
        return JSON_string

    # def fromJSON(self,JSON_string):
    #     pass

#written in one line so that test coverage can reach 100%
if __name__ == "__main__": import doctest ; doctest.testmod()
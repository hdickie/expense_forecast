import BudgetItem, pandas as pd, datetime
from log_methods import log_in_color

from generate_date_sequence import generate_date_sequence
import logging

from log_methods import setup_logger
#logger = setup_logger('BudgetSet', './log/BudgetSet.log', level=logging.INFO)
logger = logging.getLogger(__name__)

import jsonpickle

def initialize_from_dataframe(budget_set_df):
    #print('ENTER BudgetSet initialize_from_dataframe')
    B = BudgetSet([])
    try:
        for index, row in budget_set_df.iterrows():
            sd = str(row.start_date).replace('-','')
            ed = str(row.end_date).replace('-','')
            B.addBudgetItem(sd,
                            ed,
                            row.priority,
                            row.cadence.replace('-','').lower(),
                            row.amount,
                            row.memo,
                            row.deferrable,
                            row.partial_payment_allowed)
    except Exception as e:
        print(e.args)
        raise e
    #print(B.getBudgetItems().to_string())
    #print('EXIT BudgetSet initialize_from_dataframe')
    return B

def initialize_from_json_string(json_string):
    raise NotImplementedError

class BudgetSet:

    def __init__(self,budget_items__list=None):
        """
        Add a budget_item to self.budget_items. Input validation is performed.

        :param budget_items__list:
        """

        if budget_items__list is None:
            budget_items__list = []

        required_attributes = ['start_date_YYYYMMDD', 'end_date_YYYYMMDD',
                               'priority', 'cadence', 'amount',
                               'deferrable',
                               'partial_payment_allowed']

        self.budget_items = []
        for budget_item in budget_items__list:
            if set(required_attributes) & set(dir(budget_item)) != set(required_attributes): raise ValueError("An object in the input list did not have all the attributes a BudgetItem is expected to have.")
            self.addBudgetItem(start_date_YYYYMMDD=budget_item.start_date_YYYYMMDD,
                               end_date_YYYYMMDD=budget_item.end_date_YYYYMMDD,
                               priority=budget_item.priority,
                               cadence=budget_item.cadence,
                               amount=budget_item.amount,
                               memo=budget_item.memo,
                               deferrable=budget_item.deferrable,
                               partial_payment_allowed=budget_item.partial_payment_allowed
                               )

    def __str__(self):
        return self.getBudgetItems().to_string()

    def getBudgetItems(self):
        """
        Returns a DataFrame of BudgetItems.

        :return: DataFrame
        """
        all_budget_items_df = pd.DataFrame({'Start_Date': [], 'End_Date': [], 'Priority': [], 'Cadence': [], 'Amount': [], 'Memo': [],
                                            'Deferrable': [],
                                            'Partial_Payment_Allowed': []
                                        })

        for budget_item in self.budget_items:
            new_budget_item_row_df = pd.DataFrame({'Start_Date': [budget_item.start_date_YYYYMMDD],
                                                   'End_Date': [budget_item.end_date_YYYYMMDD],
                                               'Priority': [budget_item.priority],
                                               'Cadence': [budget_item.cadence],
                                               'Amount': [budget_item.amount],
                                               'Memo': [budget_item.memo],
                                               'Deferrable': [budget_item.deferrable],
                                               'Partial_Payment_Allowed': [budget_item.partial_payment_allowed]
                                               })


            #print('all_budget_items_df:')
            #print(all_budget_items_df.to_string())
            #print('new_budget_item_row_df:')
            #print(new_budget_item_row_df.to_string())

            if (not all_budget_items_df.empty) & (not new_budget_item_row_df.empty):
                all_budget_items_df = pd.concat([all_budget_items_df, new_budget_item_row_df], axis=0)

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
        #log_in_color(logger,'green', 'debug','ENTER getBudgetSchedule(start_date_YYYYMMDD='+str(start_date_YYYYMMDD)+',end_date_YYYYMMDD='+str(end_date_YYYYMMDD)+')', 0)
        # log_in_color(logger,'green', 'debug','self.budget_items:', 0)
        # for b in self.budget_items:
        #    log_in_color(logger,'green', 'debug', '\n'+str(b), 0)
        #
        # log_in_color(logger,'green', 'debug', 'getBudgetSchedule():')
        # log_in_color(logger,'green', 'debug', 'self.budget_items:')
        # log_in_color(logger,'green', 'debug', self.budget_items)

        current_budget_schedule = pd.DataFrame({'Date':[],'Priority':[],'Amount':[],'Memo':[],'Deferrable':[],'Partial_Payment_Allowed':[]})
        for budget_item in self.budget_items:
            relative_num_days = (datetime.datetime.strptime(budget_item.end_date_YYYYMMDD,'%Y%m%d') - datetime.datetime.strptime(budget_item.start_date_YYYYMMDD,'%Y%m%d')).days
            relevant_date_sequence = generate_date_sequence(budget_item.start_date_YYYYMMDD, relative_num_days, budget_item.cadence)

            relevant_date_sequence_df = pd.DataFrame(relevant_date_sequence)
            relevant_date_sequence_df = relevant_date_sequence_df.rename(columns={0:"Date"})
            current_item_cols_df = pd.DataFrame((budget_item.priority, budget_item.amount, budget_item.memo, budget_item.deferrable, budget_item.partial_payment_allowed)).T

            current_item_cols_df = current_item_cols_df.rename(columns=
                {0: "Priority", 1: "Amount", 2: "Memo", 3: "Deferrable", 4: "Partial_Payment_Allowed"})

            new_budget_schedule_rows_df = relevant_date_sequence_df.merge(current_item_cols_df, how="cross")

            current_budget_schedule = pd.concat([current_budget_schedule,new_budget_schedule_rows_df],axis=0)

            #print(current_budget_schedule.head(1))

        current_budget_schedule.sort_values(inplace=True,axis=0,by="Date")
        current_budget_schedule.reset_index(inplace=True,drop=True)

        log_in_color(logger,'green', 'debug', 'current_budget_schedule:')
        log_in_color(logger,'green', 'debug', current_budget_schedule.to_string())
        # log_in_color(logger,'green', 'debug', 'EXIT getBudgetSchedule(start_date_YYYYMMDD=' + str(start_date_YYYYMMDD) + ',end_date_YYYYMMDD=' + str(end_date_YYYYMMDD) + ')', 0)
        return current_budget_schedule

    def addBudgetItem(self,
                      start_date_YYYYMMDD,
                      end_date_YYYYMMDD,
                      priority,
                      cadence,
                      amount,
                      memo,
                      deferrable=False,
                      partial_payment_allowed=False,
                      print_debug_messages=True,
                      raise_exceptions=True):
        """
        Add a BudgetItem to the list of budget items.

        :param str start_date_YYYYMMDD: Start date in YYYYMMDD format.
        :param str end_date_YYYYMMDD: End date in YYYYMMDD format.
        :param int priority: Priority level of the budget item.
        :param str cadence: Frequency of the budget item.
        :param float amount: Amount of the budget item.
        :param str memo: Memo for the budget item.
        :param bool deferrable: Indicates if the budget item is deferrable.
        :param bool partial_payment_allowed: Indicates if partial payments are allowed.
        :param bool print_debug_messages: If True, prints debug messages.
        :param bool raise_exceptions: If True, raises exceptions on errors.
        :raises ValueError: If a budget item with the same priority and memo already exists.
        """
        # Log the addition attempt
        log_message = (f"addBudgetItem(priority={priority}, cadence='{cadence}', memo='{memo}', "
                       f"start_date='{start_date_YYYYMMDD}', end_date='{end_date_YYYYMMDD}')")
        log_in_color(logger, 'green', 'debug', log_message)

        # Create the BudgetItem
        try:
            budget_item = BudgetItem.BudgetItem(start_date_YYYYMMDD,
                                     end_date_YYYYMMDD,
                                     priority,
                                     cadence,
                                     amount,
                                     memo,
                                     deferrable,
                                     partial_payment_allowed,
                                     print_debug_messages,
                                     raise_exceptions)
        except Exception as e:
            if print_debug_messages:
                log_in_color(logger, 'red', 'error', f"Failed to create BudgetItem: {e}")
            if raise_exceptions:
                raise
            else:
                return

        # Check for duplicates
        all_budget_items = self.getBudgetItems()
        if not all_budget_items.empty:
            duplicates = all_budget_items[
                (all_budget_items['Priority'] == priority) & (all_budget_items['Memo'] == memo)
                ]
            if not duplicates.empty:
                error_message = f"A budget item with priority {priority} and memo '{memo}' already exists."
                if print_debug_messages:
                    log_in_color(logger, 'red', 'error', error_message)
                    log_in_color(logger, 'red', 'error', 'Existing budget items:')
                    log_in_color(logger, 'red', 'error', duplicates.to_string())
                if raise_exceptions:
                    raise ValueError(error_message)
                else:
                    return

        # Append the budget item
        self.budget_items.append(budget_item)
        if print_debug_messages:
            log_in_color(logger, 'green', 'info', f"Budget item '{memo}' added successfully.")

    def to_json(self):
        """
        Get a JSON <string> representing the <BudgetSet> object.

        """
        return jsonpickle.encode(self, indent=4)

if __name__ == "__main__": import doctest ; doctest.testmod()

# before gpt  7 passed, 226 deselected in 15.81s
# after gpt 7 passed, 226 deselected in 15.28s
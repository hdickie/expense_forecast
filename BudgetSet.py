import BudgetItem, pandas as pd, datetime


from colorama import init as colorama_init
from colorama import Fore
from colorama import Style
colorama_init()

BEGIN_RED = f"{Fore.RED}"
BEGIN_GREEN = f"{Fore.GREEN}"
BEGIN_YELLOW = f"{Fore.YELLOW}"
BEGIN_BLUE = f"{Fore.BLUE}"
BEGIN_MAGENTA = f"{Fore.MAGENTA}"
BEGIN_WHITE = f"{Fore.WHITE}"
BEGIN_CYAN = f"{Fore.CYAN}"
RESET_COLOR = f"{Style.RESET_ALL}"


def log_in_color(color,level,msg,stack_depth=0):

    if stack_depth == 0:
        left_prefix = ''
    else:
        left_prefix = ' '
    left_prefix = left_prefix.ljust(stack_depth*4,' ') + ' '


    if color.lower() == 'red':
        msg = BEGIN_RED + left_prefix + msg + RESET_COLOR
    elif color.lower() == 'green':
        msg = BEGIN_GREEN + left_prefix + msg + RESET_COLOR
    elif color.lower() == 'yellow':
        msg = BEGIN_YELLOW + left_prefix + msg + RESET_COLOR
    elif color.lower() == 'blue':
        msg = BEGIN_BLUE + left_prefix + msg + RESET_COLOR
    elif color.lower() == 'magenta':
        msg = BEGIN_MAGENTA + left_prefix + msg + RESET_COLOR
    elif color.lower() == 'white':
        msg = BEGIN_WHITE + left_prefix + msg + RESET_COLOR
    elif color.lower() == 'cyan':
        msg = BEGIN_CYAN + left_prefix + msg + RESET_COLOR

    if level == 'debug':
        logger.debug(msg)
    elif level == 'warning':
        logger.warning(msg)
    elif level == 'error':
        logger.error(msg)
    elif level == 'info':
        logger.info(msg)
    elif level == 'critical':
        logger.critical(msg)
    else:
        print(msg)

import logging

format = '%(asctime)s - %(name)-15s - %(levelname)-8s - %(message)s'
formatter = logging.Formatter(format)
ch = logging.StreamHandler()
ch.setFormatter(formatter)
ch.setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)
logger.propagate = False
logger.handlers.clear()
logger.addHandler(ch)

logger.setLevel(logging.DEBUG)


def generate_date_sequence(start_date_YYYYMMDD,num_days,cadence):
    """ A wrapper for pd.date_range intended to make code easier to read.

    #todo write project_utilities.generate_date_sequence() doctests
    """

    start_date = datetime.datetime.strptime(start_date_YYYYMMDD,'%Y%m%d')
    end_date = start_date + datetime.timedelta(days=num_days)

    if cadence.lower() == "once":
        return pd.Series(start_date)
    elif cadence.lower() == "daily":
        return_series = pd.date_range(start_date,end_date,freq='D')
    elif cadence.lower() == "weekly":
        return_series = pd.date_range(start_date,end_date,freq='W')
    elif cadence.lower() == "semiweekly":
        return_series = pd.date_range(start_date,end_date,freq='2W')
    elif cadence.lower() == "monthly":

        day_delta = int(start_date.strftime('%d'))-1
        first_of_each_relevant_month = pd.date_range(start_date,end_date,freq='MS')

        return_series = first_of_each_relevant_month + datetime.timedelta(days=day_delta)
    elif cadence.lower() == "quarterly":
        #todo check if this needs an adjustment like the monthly case did
        return_series = pd.date_range(start_date,end_date,freq='Q')
    elif cadence.lower() == "yearly":
        # todo check if this needs an adjustment like the monthly case did
        return_series = pd.date_range(start_date,end_date,freq='Y')

    return return_series

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
        all_budget_items_df = pd.DataFrame({'Start_Date': [], 'End_Date': [], 'Priority': [], 'Cadence': [], 'Amount': [], 'Deferrable': [],
                                        'Memo': []
                                        })

        for budget_item in self.budget_items:
            new_budget_item_row_df = pd.DataFrame({'Start_Date': [budget_item.start_date],
                                                   'End_Date': [budget_item.end_date],
                                               'Priority': [budget_item.priority],
                                               'Cadence': [budget_item.cadence],
                                               'Amount': [budget_item.amount],
                                                'Deferrable': [budget_item.deferrable],
                                               'Memo': [budget_item.memo]
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


    def getBudgetSchedule(self,start_date_YYYYMMDD,end_date_YYYYMMDD):
        """
        Generate a dataframe of proposed transactions

        #todo write doctests for BudgetSet.getBudgetSchedule()

        :param start_date_YYYYMMDD:
        :param num_days:
        :return:
        """
        # log_in_color('green', 'debug','getBudgetSchedule(start_date_YYYYMMDD='+str(start_date_YYYYMMDD)+',end_date_YYYYMMDD='+str(end_date_YYYYMMDD)+')', 0)
        # log_in_color('green', 'debug','self.budget_items:', 0)
        # for b in self.budget_items:
        #     log_in_color('green', 'debug', '\n'+str(b), 0)

        #print('getBudgetSchedule():')
        #print('self.budget_items:')
        #print(self.budget_items)

        current_budget_schedule = pd.DataFrame({'Date':[],'Priority':[],'Amount':[],'Deferrable':[],'Memo':[]})
        end_date = datetime.datetime.strptime(str(end_date_YYYYMMDD),'%Y%m%d')
        for budget_item in self.budget_items:
            relative_num_days = (end_date - budget_item.start_date).days
            relevant_date_sequence = generate_date_sequence(budget_item.start_date.strftime('%Y%m%d'),relative_num_days,budget_item.cadence)

            relevant_date_sequence_df = pd.DataFrame(relevant_date_sequence)
            relevant_date_sequence_df = relevant_date_sequence_df.rename(columns={0:"Date"})
            current_item_cols_df = pd.DataFrame((budget_item.priority, budget_item.amount, budget_item.deferrable, budget_item.memo)).T

            current_item_cols_df = current_item_cols_df.rename(columns=
                {0: "Priority", 1: "Amount", 2: "Deferrable", 3: "Memo"})

            new_budget_schedule_rows_df = relevant_date_sequence_df.merge(current_item_cols_df, how="cross")

            current_budget_schedule = pd.concat([current_budget_schedule,new_budget_schedule_rows_df],axis=0)

            #print(current_budget_schedule.head(1))


        current_budget_schedule.sort_values(inplace=True,axis=0,by="Date")
        current_budget_schedule.reset_index(inplace=True,drop=True)
        return current_budget_schedule

    def addBudgetItem(self,
                 start_date_YYYYMMDD,
                 end_date_YYYYMMDD,
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

        """
        budget_item = BudgetItem.BudgetItem(start_date_YYYYMMDD,
                                            end_date_YYYYMMDD,
                 priority,
                 cadence,
                 amount,
                 deferrable,
                 memo,print_debug_messages,raise_exceptions)

        all_current_budget_items = self.getBudgetItems()
        memos_w_matching_priority = all_current_budget_items.loc[all_current_budget_items.Priority == priority,'Memo']

        log_in_color('green', 'debug', 'addBudgetItem(priority='+str(priority)+',cadence='+str(cadence)+',memo='+str(memo)+',start_date_YYYYMMDD='+str(start_date_YYYYMMDD)+',end_date_YYYYMMDD='+str(end_date_YYYYMMDD)+')', 0)

        # print('BUDGET SET TEST 1')
        # print(memo)
        # print(str(priority))
        #
        # print('all_current_budget_items:')
        # print(all_current_budget_items)
        # print('memos_w_matching_priority:')
        # print(memos_w_matching_priority)

        if memo in memos_w_matching_priority:
            raise ValueError #A budget item with this priority and memo already exists

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
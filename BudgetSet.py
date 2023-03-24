import BudgetItem, pandas as pd, datetime

from log_methods import log_in_color

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
        all_budget_items_df = pd.DataFrame({'Start_Date': [], 'End_Date': [], 'Priority': [], 'Cadence': [], 'Amount': [], 'Memo': [],
                                            'Deferrable': [],
                                            'Partial_Payment_Allowed': []
                                        })

        for budget_item in self.budget_items:
            new_budget_item_row_df = pd.DataFrame({'Start_Date': [budget_item.start_date],
                                                   'End_Date': [budget_item.end_date],
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

        current_budget_schedule = pd.DataFrame({'Date':[],'Priority':[],'Amount':[],'Memo':[],'Deferrable':[],'Partial_Payment_Allowed':[]})
        end_date = datetime.datetime.strptime(str(end_date_YYYYMMDD),'%Y%m%d')
        for budget_item in self.budget_items:
            relative_num_days = (end_date - budget_item.start_date).days
            relevant_date_sequence = generate_date_sequence(budget_item.start_date.strftime('%Y%m%d'),relative_num_days,budget_item.cadence)

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
        return current_budget_schedule

    def addBudgetItem(self,
                 start_date_YYYYMMDD,
                 end_date_YYYYMMDD,
                 priority,
                 cadence,
                 amount,
                      memo,
                 deferrable,
                 partial_payment_allowed,
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
                 memo,
                 deferrable,
                 partial_payment_allowed,
                 print_debug_messages,raise_exceptions)

        all_current_budget_items = self.getBudgetItems()
        memos_w_matching_priority = all_current_budget_items.loc[all_current_budget_items.Priority == priority,'Memo']

        log_in_color('green', 'info', 'addBudgetItem(priority='+str(priority)+',cadence='+str(cadence)+',memo='+str(memo)+',start_date_YYYYMMDD='+str(start_date_YYYYMMDD)+',end_date_YYYYMMDD='+str(end_date_YYYYMMDD)+')')

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
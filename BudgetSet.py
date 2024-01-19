import BudgetItem, pandas as pd, datetime
from log_methods import log_in_color

from generate_date_sequence import generate_date_sequence
import logging

from log_methods import setup_logger
logger = setup_logger('BudgetSet', './log/BudgetSet.log', level=logging.WARNING)


class BudgetSet:

    def __init__(self,budget_items__list):
        """
        Add a budget_item to self.budget_items. Input validation is performed.

        :param budget_items__list:
        """
        self.budget_items = []
        for budget_item in budget_items__list:

            current_budget_items_df = self.getBudgetItems()
            p_sel_vec = (current_budget_items_df.Priority == budget_item.priority)
            m_sel_vec = (current_budget_items_df.Memo == budget_item.memo)

            sd_sel_vec = (current_budget_items_df.Start_Date == budget_item.start_date_YYYYMMDD)
            ed_sel_vec = (current_budget_items_df.End_Date == budget_item.end_date_YYYYMMDD)
            d_sel_vec = ( sd_sel_vec & ed_sel_vec )

            # print('current_budget_items_df:')
            # print(current_budget_items_df.to_string())
            # print('p_sel_vec:')
            # print(p_sel_vec)
            # print('m_sel_vec:')
            # print(m_sel_vec)

            if not current_budget_items_df[ p_sel_vec & m_sel_vec & d_sel_vec ].empty:
                raise ValueError("A duplicate budget item was detected")


            self.budget_items.append(budget_item)

        #todo do the budgetitem version of this
        #
        # if len(self.accounts) > 0:
        #     required_attributes = ['name', 'balance', 'min_balance', 'max_balance', 'account_type',
        #                            'billing_start_date_YYYYMMDD',
        #                            'interest_type', 'apr', 'interest_cadence', 'minimum_payment']
        #
        #     for obj in self.accounts:
        #         # An object in the input list did not have all the attributes an Account is expected to have.
        #         if set(required_attributes) & set(dir(obj)) != set(required_attributes): raise ValueError("An object in the input list did not have all the attributes an Account is expected to have.")


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


    #todo interesting that start date paramter did not get used here
    def getBudgetSchedule(self,start_date_YYYYMMDD,end_date_YYYYMMDD):
        """
        Generate a dataframe of proposed transactions

        #todo write doctests for BudgetSet.getBudgetSchedule()

        :param start_date_YYYYMMDD:
        :param num_days:
        :return:
        """
        # log_in_color(logger,'green', 'debug','ENTER getBudgetSchedule(start_date_YYYYMMDD='+str(start_date_YYYYMMDD)+',end_date_YYYYMMDD='+str(end_date_YYYYMMDD)+')', 0)
        # log_in_color(logger,'green', 'debug','self.budget_items:', 0)
        # for b in self.budget_items:
        #    log_in_color(logger,'green', 'debug', '\n'+str(b), 0)

        # log_in_color(logger,'green', 'debug', 'getBudgetSchedule():')
        # log_in_color(logger,'green', 'debug', 'self.budget_items:')
        # log_in_color(logger,'green', 'debug', self.budget_items)

        current_budget_schedule = pd.DataFrame({'Date':[],'Priority':[],'Amount':[],'Memo':[],'Deferrable':[],'Partial_Payment_Allowed':[]})
        end_date = datetime.datetime.strptime(str(end_date_YYYYMMDD),'%Y%m%d')
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

        # log_in_color(logger,'green', 'debug', 'current_budget_schedule:')
        # log_in_color(logger,'green', 'debug', current_budget_schedule.to_string())
        # log_in_color(logger,'green', 'debug', 'EXIT getBudgetSchedule(start_date_YYYYMMDD=' + str(start_date_YYYYMMDD) + ',end_date_YYYYMMDD=' + str(end_date_YYYYMMDD) + ')', 0)
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
        memos_w_matching_priority = list(all_current_budget_items.loc[all_current_budget_items.Priority == priority,:].Memo)

        if cadence.lower() == 'once':
            assert start_date_YYYYMMDD == end_date_YYYYMMDD

        log_in_color(logger,'green', 'info', 'addBudgetItem(priority='+str(priority)+',cadence='+str(cadence)+',memo='+str(memo)+',start_date_YYYYMMDD='+str(start_date_YYYYMMDD)+',end_date_YYYYMMDD='+str(end_date_YYYYMMDD)+')')

        if memo in memos_w_matching_priority:
            raise ValueError #A budget item with this priority and memo already exists

        #todo error when duplicate budget item. (user should make memo different its not that hard.)
        #that is, if amount and date are the same, different memos are required. its fine otherwise
        self.budget_items.append(budget_item)


    # def fromExcel(self):
    #     raise NotImplementedError
    #
    # def compareToBudgetSet(self,SecondBudgetSet):
    #     raise NotImplementedError

    def to_json(self):
        """
        Get a JSON <string> representing the <BudgetSet> object.

        """
        JSON_string = "[\n"
        for i in range(0, len(self.budget_items)):
            budget_item = self.budget_items[i]
            JSON_string += budget_item.to_json()
            if i+1 != len(self.budget_items):
                JSON_string += ","
            JSON_string += '\n'
        JSON_string += ']'
        return JSON_string

    # def fromJSON(self,JSON_string):
    #     pass

#written in one line so that test coverage can reach 100%
if __name__ == "__main__": import doctest ; doctest.testmod()
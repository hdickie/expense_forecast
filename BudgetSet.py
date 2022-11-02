import BudgetItem, pandas as pd, datetime

def generate_date_sequence(start_date_YYYYMMDD,num_days,cadence):

    start_date = datetime.datetime.strptime(start_date_YYYYMMDD,'%Y%m%d')
    end_date = start_date + datetime.timedelta(days=num_days)

    if cadence.lower() == "daily":
        return_series = pd.date_range(start_date,end_date,freq='D')
    elif cadence.lower() == "weekly":
        return_series = pd.date_range(start_date,end_date,freq='W')
    elif cadence.lower() == "biweekly":
        return_series = pd.date_range(start_date,end_date,freq='2W')
    elif cadence.lower() == "monthly":
        return_series = pd.date_range(start_date,end_date,freq='M')
    elif cadence.lower() == "quarterly":
        return_series = pd.date_range(start_date,end_date,freq='Q')
    elif cadence.lower() == "yearly":
        return_series = pd.date_range(start_date,end_date,freq='Y')

    return return_series


class BudgetSet:

    def __init__(self,budget_items__list=[]):
        self.budget_items = []
        for budget_item in budget_items__list:
            print(budget_item)


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

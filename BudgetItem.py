import pandas as pd
class BudgetItem:

    def __init__(self,
                 start_date = '',
                 priority = '',
                 cadence='',
                 amount=0,
                 memo=''):

        self.start_date = start_date
        self.priority = priority
        self.cadence = cadence
        self.amount = float(amount)
        self.memo = memo

    def __str__(self):
        single_budget_item_df = pd.DataFrame({
            'start_date': [self.start_date],
            'priority': [self.priority],
            'cadence': [self.cadence],
            'amount': [self.amount],
            'memo': [self.memo]
        })

        return single_budget_item_df.to_string()

    def __repr__(self):
        return str(self)

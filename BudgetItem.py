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

    def toJSON(self):
        """
        Get a string representing the BudgetItem object.
        """
        JSON_string = "{\n"
        JSON_string += "\"Start_Date\":" + "\"" + str(self.start_date) + "\",\n"
        JSON_string += "\"Priority\":" + "\"" + str(self.priority) + "\",\n"
        JSON_string += "\"Cadence\":" + "\"" + str(self.cadence) + "\",\n"
        JSON_string += "\"Amount\":" + "\"" + str(self.amount) + "\",\n"
        JSON_string += "\"Memo\":" + "\"" + str(self.memo) + "\"\n"
        JSON_string += "}"
        return JSON_string

    def fromJSON(self,JSON_string):
        #todo implement BudgetItem.fromJSON()
        pass

if __name__ == "__main__":
    import doctest
    doctest.testmod()
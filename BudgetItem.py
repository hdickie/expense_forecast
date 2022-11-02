
class BudgetItem:

    def __init__(self,
                 start_date = '',
                 priority = '',
                 cadence='',
                 amount='',
                 memo=''):

        self.start_date = start_date
        self.priority = priority
        self.cadence = cadence
        self.amount = amount
        self.memo = memo

    def __str__(self):
        return_string = ""

        return_string += str(self.start_date) +" | "+str(self.priority) + " | " + str(self.cadence).ljust(10) + " | "
        return_string += str(self.amount).ljust(10) + " | " + str(self.memo)

        return return_string

    def __repr__(self):
        pass

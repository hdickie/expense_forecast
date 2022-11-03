

class MemoRule:

    def __init__(self,memo_regex='',account_from='',account_to='',transaction_priority=''):

        self.memo_regex = memo_regex
        self.account_from = account_from
        self.account_to = account_to
        self.transaction_priority = transaction_priority

    def __str__(self):
        return_string = str(self.memo_regex).ljust(10) + " | " + str(self.account_from).ljust(10) + " | "
        return_string += str(self.account_to) + " | " + str(self.transaction_priority)

        return return_string

    def __repr__(self):
        return str(self)


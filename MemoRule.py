

class MemoRule:

    def __init__(self,memo_regex,account_from,account_to,transaction_priority):

        self.memo_regex = memo_regex
        self.account_from = account_from
        self.account_to = account_to
        self.transaction_priority = transaction_priority


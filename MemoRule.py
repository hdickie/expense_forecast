import pandas as pd

class MemoRule:

    def __init__(self,memo_regex='',account_from='',account_to='',transaction_priority=''):

        self.memo_regex = memo_regex
        self.account_from = account_from
        self.account_to = account_to
        self.transaction_priority = transaction_priority

    def __str__(self):
        single_memo_rule_df = pd.DataFrame({
            'Memo_Regex': [self.memo_regex],
            'Account_From': [self.account_from],
            'Account_To': [self.account_to],
            'Transaction_Priority': [self.transaction_priority]
        })

        return single_memo_rule_df.to_string()

    def __repr__(self):
        return str(self)

    def toJSON(self):
        """
        Get a string representing the MemoRule object.
        """
        JSON_string = "{\n"
        JSON_string += "\"Memo_Regex\":" + "\"" + str(self.memo_regex) + "\",\n"
        JSON_string += "\"Account_From\":" + "\"" + str(self.account_from) + "\",\n"
        JSON_string += "\"Account_To\":" + "\"" + str(self.account_to) + "\",\n"
        JSON_string += "\"Transaction_Priority\":" + "\"" + str(self.transaction_priority) + "\"\n"
        JSON_string += "}"
        return JSON_string

    def fromJSON(self,JSON_string):
        #todo implement MemoRule.fromJSON()
        pass

if __name__ == "__main__":
    import doctest
    doctest.testmod()
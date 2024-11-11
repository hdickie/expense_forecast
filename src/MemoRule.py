import pandas as pd
import re
import jsonpickle


class MemoRule:

    def __init__(
        self,
        memo_regex,
        account_from,
        account_to,
        transaction_priority
    ):

        self.memo_regex = memo_regex
        re.compile(self.memo_regex) #will raise error if not valid

        self.account_from = account_from
        assert self.account_from == str(self.account_from)
        assert len(self.account_from.strip()) > 0
        assert ';' not in self.account_from
        assert self.account_from != 'ALL_LOANS' #this can be account_to

        self.account_to = account_to
        assert self.account_to == str(self.account_to)
        assert len(self.account_to.strip()) > 0
        assert ';' not in self.account_to

        assert self.account_from != self.account_to

        self.transaction_priority = transaction_priority
        assert self.transaction_priority == int(self.transaction_priority)
        assert self.transaction_priority >= 1

    def __str__(self):
        single_memo_rule_df = pd.DataFrame(
            {
                "Memo_Regex": [self.memo_regex],
                "Account_From": [self.account_from],
                "Account_To": [self.account_to],
                "Transaction_Priority": [self.transaction_priority],
            }
        )
        return single_memo_rule_df.to_string()

    def to_json(self):
        return jsonpickle.encode(self, indent=4)


# written in one line so that test coverage can reach 100%
if __name__ == "__main__":
    import doctest

    doctest.testmod()

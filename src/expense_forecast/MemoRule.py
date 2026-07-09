"""
Summary
-------

Description
-----------

Contract
--------

@interface-report: show
"""


import pandas as pd
import re
import jsonpickle


#TODO manual review of MemoRule docstring
class MemoRule:

    """
    Summary
    -------

    Description
    -----------

    Contract
    --------

    @interface-report: show
    """
    #TODO manual review of MemoRule.__init__ docstring
    def __init__(
        self,
        memo_regex,
        account_from,
        account_to,
        transaction_priority
    ):

        """
        TODO one-line description of MemoRule.__init__.

        TODO multi-line description of MemoRule.__init__.
        TODO explain how MemoRule.__init__ participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        memo_regex : str
            TODO one-line description of MemoRule.__init__.memo_regex.

        account_from : object
            TODO one-line description of MemoRule.__init__.account_from.

        account_to : object
            TODO one-line description of MemoRule.__init__.account_to.

        transaction_priority : object
            TODO one-line description of MemoRule.__init__.transaction_priority.

        Returns
        -------
        None
            TODO one-line description of return value of MemoRule.__init__.

        Contract
        --------
        - #TODO contract lines for MemoRule.__init__.
        - #TODO document exceptions, mutations, and precision assumptions for MemoRule.__init__.

        @interface-report: show
        """
        self.memo_regex = memo_regex
        re.compile(self.memo_regex) #will raise error if not valid

        self.account_from = account_from
        if self.account_from is not None:
            assert self.account_from == str(self.account_from)
            assert len(self.account_from.strip()) > 0
            assert ';' not in self.account_from
            assert self.account_from != 'ALL_LOANS' #this can be account_to

        self.account_to = account_to
        if self.account_to is not None:
            assert self.account_to == str(self.account_to)
            assert len(self.account_to.strip()) > 0
            assert ';' not in self.account_to

        assert self.account_from != self.account_to
        if self.account_from is None:
            assert self.account_to is not None

        self.transaction_priority = transaction_priority
        assert self.transaction_priority == int(self.transaction_priority)
        assert self.transaction_priority >= 1

    #TODO manual review of MemoRule.__str__ docstring
    def __str__(self):
        """
        TODO one-line description of MemoRule.__str__.

        TODO multi-line description of MemoRule.__str__.
        TODO explain how MemoRule.__str__ participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that MemoRule.__str__ takes no parameters beyond self/cls.

        Returns
        -------
        str
            TODO one-line description of return value of MemoRule.__str__.

        Contract
        --------
        - #TODO contract lines for MemoRule.__str__.
        - #TODO document exceptions, mutations, and precision assumptions for MemoRule.__str__.

        @interface-report: show
        """
        single_memo_rule_df = pd.DataFrame(
            {
                "Memo_Regex": [self.memo_regex],
                "Account_From": [self.account_from],
                "Account_To": [self.account_to],
                "Transaction_Priority": [self.transaction_priority],
            }
        )
        return single_memo_rule_df.to_string()

    #TODO manual review of MemoRule.to_json docstring
    def to_json(self):
        """
        TODO one-line description of MemoRule.to_json.

        TODO multi-line description of MemoRule.to_json.
        TODO explain how MemoRule.to_json participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that MemoRule.to_json takes no parameters beyond self/cls.

        Returns
        -------
        str
            TODO one-line description of return value of MemoRule.to_json.

        Contract
        --------
        - #TODO contract lines for MemoRule.to_json.
        - #TODO document exceptions, mutations, and precision assumptions for MemoRule.to_json.

        @interface-report: show
        """
        return jsonpickle.encode(self, indent=4)


# written in one line so that test coverage can reach 100%
if __name__ == "__main__":
    import doctest

    doctest.testmod()

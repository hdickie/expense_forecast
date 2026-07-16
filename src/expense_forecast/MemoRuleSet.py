"""
Summary
-------

Description
-----------

Contract
--------

@interface-report: show
"""


from .MemoRule import MemoRule
import pandas as pd
import re
from . import log_methods
import logging
import jsonpickle

# logger = setup_logger('MemoRuleSet', './log/MemoRuleSet.log', level=logging.WARNING)
logger = logging.getLogger(__name__)


# def initialize_from_dataframe(memo_set_df):
#     # print('ENTER MemoRuleSet initialize_from_dataframe')
#     M = MemoRuleSet([])
#     try:
#         for index, row in memo_set_df.iterrows():
#             M.addMemoRule(
#                 row.memo_regex, row.account_from, row.account_to, row.priority
#             )
#     except Exception as e:
#         print(e.args)
#         raise e
#     # print(M.getMemoRules().to_string())
#
#     # print('EXIT MemoRuleSet initialize_from_dataframe')
#     return M


#TODO DOC manual review of MemoRuleSet docstring
class MemoRuleSet:

    """
    Summary
    -------

    Description
    -----------

    Contract
    --------

    @interface-report: show
    """
    #TODO DOC manual review of MemoRuleSet.__init__ docstring
    def __init__(self, memo_rules__list=None):
        """
        #TODO DOC one-line description of MemoRuleSet.__init__.

        #TODO DOC multi-line description of MemoRuleSet.__init__.
        #TODO DOC explain how MemoRuleSet.__init__ participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        memo_rules__list : object
            #TODO DOC one-line description of MemoRuleSet.__init__.memo_rules__list.

        Returns
        -------
        None
            #TODO DOC one-line description of return value of MemoRuleSet.__init__.

        Contract
        --------
        - #TODO DOC contract lines for MemoRuleSet.__init__.
        - #TODO DOC document exceptions, mutations, and precision assumptions for MemoRuleSet.__init__.

        @interface-report: show
        """
        self.memo_rules = []
        self.memoized_rule_matches = {} #not possible to input this bc this is a memory optimization
        if memo_rules__list is None:
            return

        required_attributes = ['memo_regex',
                               'account_from',
                               'account_to',
                               'transaction_priority',
                               'to_json']

        for memo_rule in memo_rules__list:

            # not perfect but good enough
            non_builtin_attr = [x for x in dir(memo_rule) if '__' not in x]
            for attr in non_builtin_attr:
                try:
                    assert attr in required_attributes
                except Exception:
                    raise ValueError('Unrecognized attribute on MemoRuleSet: '+str(attr))

            for required_attr in required_attributes:
                assert required_attr in non_builtin_attr
            self.memo_rules.append(memo_rule)

    #TODO DOC manual review of MemoRuleSet.__str__ docstring
    def __str__(self):
        """
        #TODO DOC one-line description of MemoRuleSet.__str__.

        #TODO DOC multi-line description of MemoRuleSet.__str__.
        #TODO DOC explain how MemoRuleSet.__str__ participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that MemoRuleSet.__str__ takes no parameters beyond self/cls.

        Returns
        -------
        str
            #TODO DOC one-line description of return value of MemoRuleSet.__str__.

        Contract
        --------
        - #TODO DOC contract lines for MemoRuleSet.__str__.
        - #TODO DOC document exceptions, mutations, and precision assumptions for MemoRuleSet.__str__.

        @interface-report: show
        """
        return self.getMemoRules().to_string() #TODO implement MemoRuleSet::__str__

    #TODO DOC manual review of MemoRuleSet.__repr__ docstring
    def __repr__(self):
        """
        #TODO DOC one-line description of MemoRuleSet.__repr__.

        #TODO DOC multi-line description of MemoRuleSet.__repr__.
        #TODO DOC explain how MemoRuleSet.__repr__ participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that MemoRuleSet.__repr__ takes no parameters beyond self/cls.

        Returns
        -------
        str
            #TODO DOC one-line description of return value of MemoRuleSet.__repr__.

        Contract
        --------
        - #TODO DOC contract lines for MemoRuleSet.__repr__.
        - #TODO DOC document exceptions, mutations, and precision assumptions for MemoRuleSet.__repr__.

        @interface-report: show
        """
        return str(self) #TODO implement MemoRuleSet::__repr__

    #TODO DOC manual review of MemoRuleSet.findMatchingMemoRule docstring
    def findMatchingMemoRule(self, txn_memo, transaction_priority):
        # log_in_color(logger, "yellow", "debug", "ENTER findMatchingMemoRule")
        """
        #TODO DOC one-line description of MemoRuleSet.findMatchingMemoRule.

        #TODO DOC multi-line description of MemoRuleSet.findMatchingMemoRule.
        #TODO DOC explain how MemoRuleSet.findMatchingMemoRule participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        txn_memo : object
            #TODO DOC one-line description of MemoRuleSet.findMatchingMemoRule.txn_memo.

        transaction_priority : object
            #TODO DOC one-line description of MemoRuleSet.findMatchingMemoRule.transaction_priority.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of MemoRuleSet.findMatchingMemoRule.

        Contract
        --------
        - #TODO DOC contract lines for MemoRuleSet.findMatchingMemoRule.
        - #TODO DOC document exceptions, mutations, and precision assumptions for MemoRuleSet.findMatchingMemoRule.

        @interface-report: show
        """
        if (txn_memo, transaction_priority) in self.memoized_rule_matches:
            return self.memoized_rule_matches[(txn_memo, transaction_priority)]

        memo_df = self.getMemoRules()
        memo_rules_of_matching_priority = memo_df[
            memo_df.Transaction_Priority == transaction_priority
        ]

        match_count = 0
        match_index = None
        for index, memo_row in memo_rules_of_matching_priority.iterrows():
            match = re.search(memo_row.Memo_Regex, txn_memo) #None if False, .group(0) is result if true
            if match is not None:
                match_count += 1
                match_index = index

        if match_count != 1:
            raise ValueError(
                f"Expected exactly one memo rule match for memo {txn_memo!r} "
                f"at priority {transaction_priority}; found {match_count}."
            )

        matching_memo_rule_row = memo_rules_of_matching_priority.loc[match_index]

        relevant_memo_rule = MemoRule(
            matching_memo_rule_row.Memo_Regex,
            matching_memo_rule_row.Account_From,
            matching_memo_rule_row.Account_To,
            matching_memo_rule_row.Transaction_Priority,
        )
        self.memoized_rule_matches[(txn_memo, transaction_priority)] = relevant_memo_rule

        # log_in_color(logger, "yellow", "debug", "Found matching memo rule: " +
        #              str(matching_memo_rule_row.Account_From.iat[0]) + " -> " +
        #              str(matching_memo_rule_row.Account_To.iat[0]),)
        #
        # log_in_color(logger, "yellow", "debug", "EXIT findMatchingMemoRule")
        return self.memoized_rule_matches[(txn_memo, transaction_priority)]

    #TODO DOC manual review of MemoRuleSet.addMemoRule docstring
    def addMemoRule(self, memo_regex, account_from, account_to, transaction_priority):

        """
        #TODO DOC one-line description of MemoRuleSet.addMemoRule.

        #TODO DOC multi-line description of MemoRuleSet.addMemoRule.
        #TODO DOC explain how MemoRuleSet.addMemoRule participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        memo_regex : str
            #TODO DOC one-line description of MemoRuleSet.addMemoRule.memo_regex.

        account_from : object
            #TODO DOC one-line description of MemoRuleSet.addMemoRule.account_from.

        account_to : object
            #TODO DOC one-line description of MemoRuleSet.addMemoRule.account_to.

        transaction_priority : object
            #TODO DOC one-line description of MemoRuleSet.addMemoRule.transaction_priority.

        Returns
        -------
        object
            #TODO DOC one-line description of return value of MemoRuleSet.addMemoRule.

        Contract
        --------
        - #TODO DOC contract lines for MemoRuleSet.addMemoRule.
        - #TODO DOC document exceptions, mutations, and precision assumptions for MemoRuleSet.addMemoRule.

        @interface-report: show
        """
        current_memo_rules_df = self.getMemoRules()
        memo_rules_of_same_priority_df = current_memo_rules_df[
            current_memo_rules_df.Transaction_Priority == transaction_priority
        ]

        for index, row in memo_rules_of_same_priority_df.iterrows():
            if row.Memo_Regex == memo_regex:
                raise ValueError(f"Memo rule already in set. Values were: priority:{transaction_priority}, memo_regex{memo_regex}")  #


        memo_rule = MemoRule(
            memo_regex, account_from, account_to, transaction_priority
        )
        self.memo_rules.append(memo_rule)

    #TODO DOC manual review of MemoRuleSet.getMemoRules docstring
    def getMemoRules(self):
        """
        #TODO DOC one-line description of MemoRuleSet.getMemoRules.

        #TODO DOC multi-line description of MemoRuleSet.getMemoRules.
        #TODO DOC explain how MemoRuleSet.getMemoRules participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that MemoRuleSet.getMemoRules takes no parameters beyond self/cls.

        Returns
        -------
        pd.DataFrame
            #TODO DOC one-line description of return value of MemoRuleSet.getMemoRules.

        Contract
        --------
        - #TODO DOC contract lines for MemoRuleSet.getMemoRules.
        - #TODO DOC document exceptions, mutations, and precision assumptions for MemoRuleSet.getMemoRules.

        @interface-report: show
        """
        all_memo_rules_df = pd.DataFrame(
            {
                "Memo_Regex": [],
                "Account_From": [],
                "Account_To": [],
                "Transaction_Priority": [],
            }
        )

        for memo_rule in self.memo_rules:
            new_memo_rule_df = pd.DataFrame(
                {
                    "Memo_Regex": [memo_rule.memo_regex],
                    "Account_From": [memo_rule.account_from],
                    "Account_To": [memo_rule.account_to],
                    "Transaction_Priority": [memo_rule.transaction_priority],
                }
            )

            all_memo_rules_df = pd.concat([all_memo_rules_df, new_memo_rule_df], axis=0)

        all_memo_rules_df.reset_index(drop=True, inplace=True)
        return all_memo_rules_df

    #TODO DOC manual review of MemoRuleSet.to_dict docstring
    def to_dict(self):
        """
        #TODO DOC one-line description of MemoRuleSet.to_dict.

        #TODO DOC multi-line description of MemoRuleSet.to_dict.
        #TODO DOC explain how MemoRuleSet.to_dict participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that MemoRuleSet.to_dict takes no parameters beyond self/cls.

        Returns
        -------
        dict
            #TODO DOC one-line description of return value of MemoRuleSet.to_dict.

        Contract
        --------
        - #TODO DOC contract lines for MemoRuleSet.to_dict.
        - #TODO DOC document exceptions, mutations, and precision assumptions for MemoRuleSet.to_dict.

        @interface-report: show
        """
        return {
            "memo_rules": [
                {
                    "Memo_Regex": memo_rule.memo_regex,
                    "Account_From": memo_rule.account_from,
                    "Account_To": memo_rule.account_to,
                    "Transaction_Priority": memo_rule.transaction_priority,
                }
                for memo_rule in self.memo_rules
            ]
        }

    #TODO DOC manual review of MemoRuleSet.to_json docstring
    def to_json(self):
        """
        #TODO DOC one-line description of MemoRuleSet.to_json.

        #TODO DOC multi-line description of MemoRuleSet.to_json.
        #TODO DOC explain how MemoRuleSet.to_json participates in this module.
        #TODO DOC document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            #TODO DOC confirm that MemoRuleSet.to_json takes no parameters beyond self/cls.

        Returns
        -------
        str
            #TODO DOC one-line description of return value of MemoRuleSet.to_json.

        Contract
        --------
        - #TODO DOC contract lines for MemoRuleSet.to_json.
        - #TODO DOC document exceptions, mutations, and precision assumptions for MemoRuleSet.to_json.

        @interface-report: show
        """
        return jsonpickle.encode(self, indent=4)


# written in one line so that test coverage can reach 100%
if __name__ == "__main__":
    import doctest

    doctest.testmod()

import MemoRule
import pandas as pd
import re
from log_methods import log_in_color
import logging
import jsonpickle
from log_methods import setup_logger

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


class MemoRuleSet:

    def __init__(self, memo_rules__list=None):
        self.memo_rules = []
        self.memoized_rule_matches = {} #not possible to input this bc this is a memory optimization
        if memo_rules__list is None:
            return

        required_attributes = ['memo_regex', 'account_from', 'account_to', 'transaction_priority']

        for memo_rule in memo_rules__list:

            # not perfect but good enough
            non_builtin_attr = [x for x in dir(memo_rule) if '__' not in x]
            for attr in non_builtin_attr:
                assert attr in required_attributes

            for required_attr in required_attributes:
                assert required_attr in non_builtin_attr
            self.memo_rules.append(memo_rule)

    def __str__(self):
        return self.getMemoRules().to_string()

    def __repr__(self):
        return str(self) #todo

    def findMatchingMemoRule(self, txn_memo, transaction_priority):
        # log_in_color(logger, "yellow", "debug", "ENTER findMatchingMemoRule")
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

        assert match_count == 1

        matching_memo_rule_row = memo_rules_of_matching_priority.loc[match_index]

        relevant_memo_rule = MemoRule.MemoRule(
            matching_memo_rule_row.Memo_Regex.iat[0],
            matching_memo_rule_row.Account_From.iat[0],
            matching_memo_rule_row.Account_To.iat[0],
            matching_memo_rule_row.Transaction_Priority.iat[0],
        )
        self.memoized_rule_matches[(txn_memo, transaction_priority)] = relevant_memo_rule

        # log_in_color(logger, "yellow", "debug", "Found matching memo rule: " +
        #              str(matching_memo_rule_row.Account_From.iat[0]) + " -> " +
        #              str(matching_memo_rule_row.Account_To.iat[0]),)
        #
        # log_in_color(logger, "yellow", "debug", "EXIT findMatchingMemoRule")
        return self.memoized_rule_matches[(txn_memo, transaction_priority)]

    def fromExcel(self):
        raise NotImplementedError #todo

    def addMemoRule(self, memo_regex, account_from, account_to, transaction_priority):

        current_memo_rules_df = self.getMemoRules()
        memo_rules_of_same_priority_df = current_memo_rules_df[
            current_memo_rules_df.Transaction_Priority == transaction_priority
        ]

        for index, row in memo_rules_of_same_priority_df.iterrows():
            if row.Memo_Regex == memo_regex:
                raise ValueError(f"Memo rule already in set. Values were: priority:{transaction_priority}, memo_regex{memo_regex}")  #


        memo_rule = MemoRule.MemoRule(
            memo_regex, account_from, account_to, transaction_priority
        )
        self.memo_rules.append(memo_rule)

    def getMemoRules(self):
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

    def to_json(self):
        return jsonpickle.encode(self, indent=4)


# written in one line so that test coverage can reach 100%
if __name__ == "__main__":
    import doctest

    doctest.testmod()


import MemoRule, pandas as pd
import re
from log_methods import log_in_color
import logging

from log_methods import setup_logger
logger = setup_logger('MemoRuleSet', 'MemoRuleSet.log', level=logging.WARNING)


class MemoRuleSet:

    def __init__(self,memo_rules__list):
        """
        Create a <MemoRuleSet> from a <list> of <MemoRule> objects.

        | Test Cases
        | Expected Successes
        | S1 Provide valid parameters.
        |
        | Expected Fails
        | F1 input a list with objects that are not BudgetItem type. Do this without explicitly checking type. #todo refactor MemoRuleSet.MemoRuleSet() doctest F1 to use _F1 label
        | F2 provide a list of MemoRules with a memo and priority that matches a MemoRule already in self.memo_riles (same from and to) #todo refactor MemoRuleSet.MemoRuleSet() doctest F2 to use _F2 label
        | F3 provide a list of MemoRules with a memo and priority that matches a MemoRule already in self.memo_rules (different from and to) #todo refactor MemoRuleSet.MemoRuleSet() doctest F3 to use _F3 label


        :param memo_rules__list:
        """
        self.memo_rules = []
        for memo_rule in memo_rules__list:
            self.memo_rules.append(memo_rule)

        #todo do the memoruleset version of this
        #
        # if len(self.accounts) > 0:
        #     required_attributes = ['name', 'balance', 'min_balance', 'max_balance', 'account_type',
        #                            'billing_start_date_YYYYMMDD',
        #                            'interest_type', 'apr', 'interest_cadence', 'minimum_payment']
        #
        #     for obj in self.accounts:
        #         # An object in the input list did not have all the attributes an Account is expected to have.
        #         if set(required_attributes) & set(dir(obj)) != set(required_attributes): raise ValueError("An object in the input list did not have all the attributes an Account is expected to have.")


    def __str__(self):
        return self.getMemoRules().to_string()

    def __repr__(self):
        return str(self)

    def findMatchingMemoRule(self, txn_memo,transaction_priority):
        log_in_color(logger,'yellow','debug','ENTER findMatchingMemoRule')

        memo_df = self.getMemoRules()
        memo_rules_of_matching_priority = memo_df[memo_df.Transaction_Priority == transaction_priority]

        match_vec = []
        for memo_index, memo_row in memo_rules_of_matching_priority.iterrows():
            match_vec.append(False)

        for i in range(0, memo_rules_of_matching_priority.shape[0]):
            memo_row = memo_rules_of_matching_priority.iloc[i,:]
            try:
                g = re.search(memo_row.Memo_Regex, txn_memo).group(0)
                match_vec[i] = True
            except Exception as e:
                match_vec[i] = False

        try:
            assert sum(match_vec) != 0  # if error, no matches found
        except Exception as e:
            log_in_color(logger,'yellow', 'error', 'ERROR')
            log_in_color(logger,'yellow', 'error', 'No matches found for memo:'+str(txn_memo))
            log_in_color(logger,'yellow', 'error', 'Memo Set:')
            log_in_color(logger,'yellow', 'error',self)
            raise ValueError

        try:
            assert sum(match_vec) == 1  # if error, multiple matches found
        except Exception as e:
            log_in_color(logger,'yellow', 'error', 'ERROR')
            log_in_color(logger,'yellow', 'error', 'Multiple matches found for memo:'+str(txn_memo))
            log_in_color(logger,'yellow', 'error', 'match vector:')
            log_in_color(logger,'yellow', 'error', match_vec)

            raise ValueError

        matching_memo_rule_row = memo_rules_of_matching_priority[match_vec]

        relevant_memo = MemoRule.MemoRule(matching_memo_rule_row.Memo_Regex.iat[0],
                                 matching_memo_rule_row.Account_From.iat[0],
                                 matching_memo_rule_row.Account_To.iat[0],
                                 matching_memo_rule_row.Transaction_Priority.iat[0])

        log_in_color(logger,'yellow', 'debug', 'Found matching memo rule: '+str(matching_memo_rule_row.Account_From.iat[0])+' -> '+str(matching_memo_rule_row.Account_To.iat[0]))

        log_in_color(logger,'yellow', 'debug', 'EXIT findMatchingMemoRule')
        return MemoRuleSet([relevant_memo])


    # def fromExcel(self):
    #     raise NotImplementedError

    def addMemoRule(self,memo_regex,account_from,account_to,transaction_priority):
        """ Add a <MemoRule> to <list> MemoRuleSet.memo_rules.

        | Test Cases
        | Expected Successes
        | S1 Provide valid parameters.
        |
        | Expected Fails
        | F1 Provide incorrect types for each parameter  #todo refactor MemoRuleSet.addMemoRule() doctest F1 to use _F1 label
        | F2 add a BudgetItem with a memo and priority that matches a BudgetItem already in self.budgetItems (same from and to) #todo refactor MemoRuleSet.addMemoRule() doctest F2 to use _F2 label
        | F3 add a BudgetItem with a memo and priority that matches a BudgetItem already in self.budgetItems (different from and to) #todo refactor MemoRuleSet.addMemoRule() doctest F3 to use _F3 label

        """
        log_in_color(logger,'green','info','addMemoRule(memo_regex='+str(memo_regex)+',account_from='+str(account_from)+',account_to='+str(account_to)+',transaction_priority='+str(transaction_priority)+')')

        current_memo_rules_df = self.getMemoRules()
        memo_rules_of_same_priority_df = current_memo_rules_df.loc[current_memo_rules_df.Transaction_Priority == transaction_priority,:]

        for index, row in memo_rules_of_same_priority_df.iterrows():
            if row.Memo_Regex == memo_regex:
                if row.Account_From == account_from and row.Account_To == account_to:
                    raise ValueError #An attempt was made to add a memo rule to a memo rule set that already existed.
                else:
                    raise ValueError #A MemoRule with the same memo_regex and priority as an existing rule, but with different from or to was added. This creates an ambiguous situation and we cannot continue.

        #Lower-level validation will occur in the MemoRule constructor
        memo_rule = MemoRule.MemoRule(memo_regex, account_from, account_to, transaction_priority)
        self.memo_rules.append(memo_rule)

    def getMemoRules(self):
        """
        Get a <DataFrame> representing the <MemoRuleSet> object.
        """
        all_memo_rules_df = pd.DataFrame({'Memo_Regex': [], 'Account_From': [], 'Account_To': [],
                                             'Transaction_Priority': []})

        for memo_rule in self.memo_rules:
            new_memo_rule_df = pd.DataFrame({'Memo_Regex': [memo_rule.memo_regex],
                                               'Account_From': [memo_rule.account_from],
                                               'Account_To': [memo_rule.account_to],
                                               'Transaction_Priority': [memo_rule.transaction_priority]
                                               })

            all_memo_rules_df = pd.concat([all_memo_rules_df, new_memo_rule_df], axis=0)
            all_memo_rules_df.reset_index(drop=True, inplace=True)

        return all_memo_rules_df

    def to_json(self):
        """
        Get a JSON <string> representing the <MemoRuleSet> object.\
        """
        JSON_string = "[\n"
        for i in range(0, len(self.memo_rules)):
            memo_rule = self.memo_rules[i]
            JSON_string += memo_rule.to_json()
            if i+1 != len(self.memo_rules):
                JSON_string += ","
            JSON_string += '\n'
        JSON_string += ']'

        return JSON_string

    # def fromJSON(self,JSON_string):
    #     pass

#written in one line so that test coverage can reach 100%
if __name__ == "__main__": import doctest ; doctest.testmod()
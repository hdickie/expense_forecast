
import MemoRule, pandas as pd
import re
from log_methods import log_in_color

class MemoRuleSet:

    def __init__(self,memo_rules__list=[]):
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

    def __str__(self):
        return self.getMemoRules().to_string()

    def __repr__(self):
        return str(self)

    def findMatchingMemoRule(self, budget_item_row_df):

        memo_df = self.getMemoRules()
        memo_rules_of_matching_priority = memo_df[memo_df.Transaction_Priority == budget_item_row_df.Priority]

        match_vec = []
        for memo_index, memo_row in memo_rules_of_matching_priority.iterrows():
            match_vec.append(False)

        for i in range(0, memo_rules_of_matching_priority.shape[0]):
            try:
                re.search(memo_row.Memo_Regex, budget_item_row_df.Memo).group(0)
                match_vec[i] = True
            except:
                match_vec[i] = False

        try:
            assert sum(match_vec) > 0  # if error, no matches found
            assert sum(match_vec) == 1  # if error, multiple matches found
        except Exception as e:

            print('Memo Set:')
            print(self.getMemoRules().to_string())
            print('Budget Item:')
            print(pd.DataFrame(budget_item_row_df).T)

            raise e

        matching_memo_rule_row = memo_rules_of_matching_priority[match_vec]

        relevant_memo = MemoRule.MemoRule(matching_memo_rule_row.Memo_Regex.iat[0],
                                 matching_memo_rule_row.Account_From.iat[0],
                                 matching_memo_rule_row.Account_To.iat[0],
                                 matching_memo_rule_row.Transaction_Priority.iat[0])

        return MemoRuleSet([relevant_memo])

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
        log_in_color('green','info','addMemoRule(memo_regex='+str(memo_regex)+',account_from='+str(account_from)+',account_to='+str(account_to)+',transaction_priority='+str(transaction_priority)+')')

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

    def toJSON(self):
        """
        Get a JSON <string> representing the <MemoRuleSet> object.\
        """
        JSON_string = "{\n"
        for i in range(0, len(self.memo_rules)):
            memo_rule = self.memo_rules[i]
            JSON_string += memo_rule.toJSON()
            if i+1 != len(self.memo_rules):
                JSON_string += ","
            JSON_string += '\n'
        JSON_string += '}'

        return JSON_string

    # def fromJSON(self,JSON_string):
    #     pass

#written in one line so that test coverage can reach 100%
if __name__ == "__main__": import doctest ; doctest.testmod()
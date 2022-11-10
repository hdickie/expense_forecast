
import MemoRule, pandas as pd

class MemoRuleSet:

    def __init__(self,memo_rules__list=[]):
        """
        Create a MemoRuleSet from a <list> of <MemoRule> objects.

        #todo MemoRuleSet.MemoRuleSet() doctests

        :param memo_rules__list:
        """
        self.memo_rules = []
        for memo_rule in memo_rules__list:
            self.memo_rules.append(memo_rule)

    def __str__(self):
        return self.getMemoRules().to_string()

    def __repr__(self):
        return str(self)

    def addMemoRule(self,memo_regex='',account_from='',account_to='',transaction_priority=''):
        """ Add a MemoRule to list MemoRuleSet.memo_rules. """
        #todo validation

        #if a memo rule is added that already exists, just ignore it.
        #we could drop duplicates later but it is cheaper to check if it contains an element once
        #than to compare all elements to each other

        memo_rule = MemoRule.MemoRule(memo_regex,account_from,account_to,transaction_priority)
        self.memo_rules.append(memo_rule)

    def getMemoRules(self):
        """
        Get a DataFrame representing the MemoRuleSet object.
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
        Get a string representing the MemoRuleSet object.
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
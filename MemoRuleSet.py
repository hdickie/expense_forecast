import MemoRule, pandas as pd

class MemoRuleSet:

    def __init__(self,memo_rules__list=[]):
        self.memo_rules = []
        for memo_rule in memo_rules__list:
            print(memo_rule)
            self.memo_rules.append(memo_rule)

    def __str__(self):
        return self.getMemoRules().to_string()

    def __repr__(self):
        return str(self)

    def addMemoRule(self,memo_regex='',account_from='',account_to='',transaction_priority=''):
        """ Add a MemoRule to list MemoRuleSet.memo_rules. """
        #todo validation
        memo_rule = MemoRule.MemoRule(memo_regex,account_from,account_to,transaction_priority)
        self.memo_rules.append(memo_rule)

    def getMemoRules(self):
        """
        Get a DataFrame representing the MemoRuleSet object.
        """
        all_memo_rules_df = pd.DataFrame({'memo_regex': [], 'account_from': [], 'account_to': [],
                                             'transaction_priority': []})

        for memo_rule in self.memo_rules:
            new_memo_rule_df = pd.DataFrame({'memo_regex': [memo_rule.memo_regex],
                                               'account_from': [memo_rule.account_from],
                                               'account_to': [memo_rule.account_to],
                                             'transaction_priority': [memo_rule.transaction_priority]
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
        JSON_string += '\n'

        return JSON_string

    def fromJSON(self,JSON_string):
        #todo implement MemoRuleSet.fromJSON()
        pass

if __name__ == "__main__":
    import doctest
    doctest.testmod()
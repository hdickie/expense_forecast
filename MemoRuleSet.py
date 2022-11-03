import MemoRule, pandas as pd

class MemoRuleSet:

    def __init__(self,memo_rules__list=[]):
        self.memo_rules = []
        for memo_rule in memo_rules__list:
            print(memo_rule)
            self.memo_rules.append(memo_rule)

    def __str__(self):
        return_string = ""

        for memo_rule in self.memo_rules:
            return_string += str(memo_rule) + "\n"

        return return_string

    def __repr__(self):
        return str(self)

    def addMemoRule(self,memo_regex='',account_from='',account_to='',transaction_priority=''):
        memo_rule = MemoRule.MemoRule(memo_regex,account_from,account_to,transaction_priority)
        self.memo_rules.append(memo_rule)

    def getMemoRules(self):
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
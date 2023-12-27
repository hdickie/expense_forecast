
import pandas as pd
import re
import MemoMilestone
import CompositeMilestone
import AccountMilestone

class MilestoneSet:

    def __init__(self,account_set,budget_set,account_milestones__list,memo_milestones__list,composite_milestones__list):

        for account_milestone in account_milestones__list:
            all_account_names = set([ a.split(':')[0] for a in account_set.getAccounts().Name ])
            if not account_milestone.account_name in all_account_names:
                raise ValueError("Account Name for Milestone not found in accounts: "+str(account_milestone.account_name))

        self.account_milestones__list = account_milestones__list

        for memo_milestone in memo_milestones__list:
            match_found = False
            for index2, row2 in budget_set.getBudgetItems().iterrows():
                if re.search(memo_milestone.memo_regex,row2.Memo) is not None:
                    match_found = True

            if not match_found:
                raise ValueError("Memo Milestone had no matches in budgetset, so no match during forecast calculation is possible.")

        self.memo_milestones__list = memo_milestones__list

        for cm in composite_milestones__list:
            for account_milestone in cm.account_milestones__list:
                all_account_names = set([ a.split(':')[0] for a in account_set.getAccounts().Name ])
                if not account_milestone.account_name in all_account_names:
                    raise ValueError("Account Name for Milestone in Composite Milestone not found in accounts: "+str(account_milestone.account_name))

            for memo_milestone in memo_milestones__list:
                match_found = False
                for index2, row2 in budget_set.getBudgetItems().iterrows():
                    if re.search(memo_milestone.memo_regex,row2.Memo) is not None:
                        match_found = True

                if not match_found:
                    raise ValueError("Memo Milestone in Composite Milestone had no matches in budgetset, so no match during forecast calculation is possible.")

        self.composite_milestones__list = composite_milestones__list

    def __str__(self):

        return_string = ""

        count_of_milestones = str(len(self.memo_milestones__list)) + str(len(self.account_milestones__list)) + str(len(self.composite_milestones__list))
        return_string += "Total # of Milestones: "+str(count_of_milestones)+"\n"

        return_string += "Memo Milestones:\n"
        for M in self.memo_milestones__list:
            return_string += str(M)+"\n"

        return_string += "Account Milestones:\n"
        for A in self.account_milestones__list:
            return_string += str(A) + "\n"

        return_string += "Composite Milestones:\n"
        for C in self.composite_milestones__list:
            return_string += str(C) + "\n"

        return return_string


    def addMemoMilestone(self,milestone_name,memo_regex_string):
        self.memo_milestones__list += [ MemoMilestone.MemoMilestone(milestone_name,memo_regex_string) ]

    def addAccountMilestone(self,milestone_name,account_name,min_balance,max_balance):
        self.account_milestones__list += [ AccountMilestone.AccountMilestone(milestone_name,account_name,min_balance,max_balance) ]

    def addCompositeMilestone(self,milestone_name,account_milestones__list, memo_milestones__list):
        self.composite_milestones__list += [ CompositeMilestone.CompositeMilestone(milestone_name,account_milestones__list, memo_milestones__list) ]

    def to_json(self):

        json_string = "{"

        account_milestone_index = 0
        account_milestones_json_string = "["
        for a in self.account_milestones__list:
            account_milestones_json_string += a.to_json()

            if account_milestone_index != len(self.account_milestones__list) - 1:
                account_milestones_json_string += ","

            account_milestone_index += 1
        account_milestones_json_string += "]"

        memo_milestone_index = 0
        memo_milestones_json_string = "["
        for m in self.memo_milestones__list:
            memo_milestones_json_string += m.to_json()

            if memo_milestone_index != len(self.memo_milestones__list) - 1:
                memo_milestones_json_string += ","

            memo_milestone_index += 1
        memo_milestones_json_string += "]"

        composite_milestone_index = 0
        composite_milestones_json_string = "["
        for c in self.composite_milestones__list:
            composite_milestones_json_string += c.to_json()

            if composite_milestone_index != len(self.composite_milestones__list) - 1:
                composite_milestones_json_string += ","

            composite_milestone_index += 1
        composite_milestones_json_string += "]"

        json_string += '"' + "account_milestones" + '":' + account_milestones_json_string + ","
        json_string += '"' + "memo_milestones" + '":' + memo_milestones_json_string + ","
        json_string += '"' + "composite_milestones" + '":' + composite_milestones_json_string

        json_string += "}"

        return json_string

    def getAccountMilestonesDF(self):

        account_milestones_df = pd.DataFrame({'Milestone_Name': [],
                                        'Account_Name': [],
                                        'Min_Balance': [],
                                        'Max_Balance': []
                                        })

        for a in self.account_milestones__list:
            account_milestones_df = pd.concat([account_milestones_df,
                          pd.DataFrame({'Milestone_Name': [a.Milestone_Name],
                                        'Account_Name': [a.Account_Name],
                                        'Min_Balance': [a.Min_Balance],
                                        'Max_Balance': [a.Max_Balance]
                                        })])

        return account_milestones_df

    def getMemoMilestonesDF(self):
        memo_milestones_df = pd.DataFrame({'Milestone_Name': [],
                                        'Memo_Regex': []
                                        })

        for m in self.memo_milestones__list:
            memo_milestones_df = pd.concat([memo_milestones_df,
                          pd.DataFrame({'Milestone_Name': [m.Milestone_Name],
                                        'Memo_Regex': [m.Account_Name]
                                        })])
        return memo_milestones_df

    def getCompositeMilestonesDF(self):
        composite_milestones_df = pd.DataFrame({'Milestone_Name': [],
                                        'Milestone1': [],
                                        'Milestone2': [],
                                        'Milestone3': [],
                                        'Milestone4': [],
                                        'Milestone5': []
                                        })

        return composite_milestones_df
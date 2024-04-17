
import pandas as pd
import re
import MemoMilestone
import CompositeMilestone
import AccountMilestone
import jsonpickle

def initialize_from_dataframe(account_milestones_df, memo_milestones_df, composite_milestones_df):

    am__list = []
    mm__list = []
    cm__list = []

    am__dict = {}
    mm__dict = {}

    for index, row in account_milestones_df.iterrows():
        new_AM = AccountMilestone.AccountMilestone(row.milestone_name,row.account_name,row.min_balance,row.max_balance)
        am__list += [ new_AM ]
        am__dict[row.milestone_name] = new_AM

    for index, row in memo_milestones_df.iterrows():
        new_MM = MemoMilestone.MemoMilestone(row.milestone_name,row.memo_regex)
        mm__list += [ new_MM ]
        mm__dict[row.milestone_name] = new_MM

    for index, row in composite_milestones_df.iterrows():
        AM_names = row.account_milestone_name_list.split(';')
        MM_names = row.memo_milestone_name_list.split(';')
        related_AM = []
        related_MM = []
        for AM_name in AM_names:
            related_AM.append(am__dict[AM_name])
        for MM_name in MM_names:
            related_MM.append(mm__dict[MM_name])
        cm__list += [ CompositeMilestone.CompositeMilestone(row.composite_milestone_name,related_AM,related_MM) ]

    return MilestoneSet(am__list,mm__list,cm__list)

class MilestoneSet:

    def __init__(self,account_milestones__list,memo_milestones__list,composite_milestones__list):

        # for account_milestone in account_milestones__list:
        #     all_account_names = set([ a.split(':')[0] for a in account_set.getAccounts().Name ])
        #     if not account_milestone.account_name in all_account_names:
        #         raise ValueError("Account Name for Milestone not found in accounts: "+str(account_milestone.account_name))

        self.account_milestones = account_milestones__list

        # for memo_milestone in memo_milestones__list:
        #     match_found = False
        #     for index2, row2 in budget_set.getBudgetItems().iterrows():
        #         if re.search(memo_milestone.memo_regex,row2.Memo) is not None:
        #             match_found = True
        #
        #     if not match_found:
        #         raise ValueError("Memo Milestone had no matches in budgetset, so no match during forecast calculation is possible.")

        self.memo_milestones = memo_milestones__list

        # for cm in composite_milestones__list:
        #     for account_milestone in cm.account_milestones:
        #         all_account_names = set([ a.split(':')[0] for a in account_set.getAccounts().Name ])
        #         if not account_milestone.account_name in all_account_names:
        #             raise ValueError("Account Name for Milestone in Composite Milestone not found in accounts: "+str(account_milestone.account_name))
        #
        #     for memo_milestone in memo_milestones__list:
        #         match_found = False
        #         for index2, row2 in budget_set.getBudgetItems().iterrows():
        #             if re.search(memo_milestone.memo_regex,row2.Memo) is not None:
        #                 match_found = True
        #
        #         if not match_found:
        #             raise ValueError("Memo Milestone in Composite Milestone had no matches in budgetset, so no match during forecast calculation is possible.")

        self.composite_milestones = composite_milestones__list

    def __str__(self):

        return_string = ""

        count_of_milestones = int(len(self.memo_milestones)) + int(len(self.account_milestones)) + int(len(self.composite_milestones))
        return_string += "Total # of Milestones: "+str(count_of_milestones)+"\n"

        return_string += "Memo Milestones:\n"
        for M in self.memo_milestones:
            return_string += str(M)+"\n"

        return_string += "Account Milestones:\n"
        for A in self.account_milestones:
            return_string += str(A) + "\n"

        return_string += "Composite Milestones:\n"
        for C in self.composite_milestones:
            return_string += str(C) + "\n"

        return return_string


    def addMemoMilestone(self,milestone_name,memo_regex_string):
        self.memo_milestones += [ MemoMilestone.MemoMilestone(milestone_name,memo_regex_string) ]

    def addAccountMilestone(self,milestone_name,account_name,min_balance,max_balance):
        self.account_milestones += [ AccountMilestone.AccountMilestone(milestone_name,account_name,min_balance,max_balance) ]

    def addCompositeMilestone(self,milestone_name,account_milestones__list, memo_milestones__list):
        #todo raise error if input milestones did not already exist
        self.composite_milestones += [ CompositeMilestone.CompositeMilestone(milestone_name,account_milestones__list, memo_milestones__list) ]

    def to_json(self):
        return jsonpickle.encode(self, indent=4, unpicklable=False)

    def getAccountMilestonesDF(self):

        account_milestones_df = pd.DataFrame({'Milestone_Name': [],
                                        'Account_Name': [],
                                        'Min_Balance': [],
                                        'Max_Balance': []
                                        })

        for a in self.account_milestones:
            account_milestones_df = pd.concat([account_milestones_df,
                          pd.DataFrame({'Milestone_Name': [a.milestone_name],
                                        'Account_Name': [a.account_name],
                                        'Min_Balance': [a.min_balance],
                                        'Max_Balance': [a.max_balance]
                                        })])
        account_milestones_df.reset_index(drop=True, inplace=True)
        return account_milestones_df

    def getMemoMilestonesDF(self):
        memo_milestones_df = pd.DataFrame({'Milestone_Name': [],
                                        'Memo_Regex': []
                                        })

        for m in self.memo_milestones:
            memo_milestones_df = pd.concat([memo_milestones_df,
                          pd.DataFrame({'Milestone_Name': [m.milestone_name],
                                        'Memo_Regex': [m.memo_regex]
                                        })])
        memo_milestones_df.reset_index(drop=True,inplace=True)
        return memo_milestones_df

    def getCompositeMilestonesDF(self):
        composite_milestone_df = pd.DataFrame({'Composite_Milestone_Name': [],
                                               'Milestone_Type': [],
                                               'Milestone_Name': []
                                           })

        for cm in self.composite_milestones:
            for am in cm.account_milestones:
                composite_milestone_df = pd.concat([composite_milestone_df, pd.DataFrame({'Composite_Milestone_Name': [cm.milestone_name],
                                               'Milestone_Type': ['Account'],
                                               'Milestone_Name': [am.milestone_name]
                                           }) ])

            for mm in cm.memo_milestones:
                composite_milestone_df = pd.concat([composite_milestone_df,pd.DataFrame({'Composite_Milestone_Name': [cm.milestone_name],
                                               'Milestone_Type': ['Memo'],
                                               'Milestone_Name': [mm.milestone_name]
                                           })])
        composite_milestone_df.reset_index(drop=True, inplace=True)
        return composite_milestone_df

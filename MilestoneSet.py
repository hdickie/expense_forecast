
import pandas as pd
import re
class MilestoneSet:

    def __init__(self,AccountSet,BudgetSet,memo_milestones__list,account_milestones__list,composite_milestones__list):

        # if memo_milestones_df is None:
        #     self.memo_milestones_df = pd.DataFrame({
        #         'Milestone_Name': [''],
        #         'Memo_Regex': ['']
        #     })
        # else:
        #     self.memo_milestones_df = memo_milestones_df
        #
        # if account_milestones_df is None:
        #     self.account_milestones_df = pd.DataFrame({
        #         'Milestone_Name': [''],
        #         'Account_Name': [''],
        #         'Min_Balance': [''],
        #         'Max_Balance': ['']
        #     })
        # else:
        #     self.account_milestones_df = account_milestones_df
        #
        # if composite_milestones_df is None:
        #     self.composite_milestones_df = pd.DataFrame({
        #                 'Milestone_Name': [''],
        #                 'Milestone1': [''],
        #                 'Milestone2': ['']
        #             })
        # else:
        #     self.composite_milestones_df = composite_milestones_df


        for index, row in account_milestones_df.iterrows():
            if not AccountSet.getAccounts().Account_Name.eq(row.Account_Name).any():
                raise ValueError("Account Name for Milestone not found in accounts: "+str(row.Account_Name))

            if row.Max_Balance < row.Min_Balance:
                raise ValueError("Min_Balance greater than Max_Balance for Account Milestone")

        self.account_milestones_df = account_milestones_df

        for index, row in memo_milestones_df.iterrows():
            match_found = False
            for index2, row2 in BudgetSet.getBudgetItems().iterrows():
                if re.search(row.Memo_Regex,row2.Memo) is not None:
                    match_found = True

            if not match_found:
                raise ValueError("Memo Milestone had no matches in budgetset, so no match was possible.")

        self.memo_milestones_df = memo_milestones_df

        # todo input validation
        for index, row in composite_milestones_df.iterrows():
            if row.Milestone1 is not None and not pd.isna(row.Milestone1):
                if not ( memo_milestones_df.Milestone_Name.eq(row.Milestone1).any() or account_milestones_df.Milestone_Name.eq(row.Milestone1).any()):
                    raise ValueError("Milestone 1 was not found in Memo or Account milestones:"+str(row.Milestone1))

            if row.Milestone2 is not None and not pd.isna(row.Milestone2):
                if not ( memo_milestones_df.Milestone_Name.eq(row.Milestone2).any() or account_milestones_df.Milestone_Name.eq(row.Milestone2).any()):
                    raise ValueError("Milestone 2 was not found in Memo or Account milestones:"+str(row.Milestone2))

            if row.Milestone3 is not None and not pd.isna(row.Milestone3):
                if not ( memo_milestones_df.Milestone_Name.eq(row.Milestone3).any() or account_milestones_df.Milestone_Name.eq(row.Milestone3).any()):
                    raise ValueError("Milestone 3 was not found in Memo or Account milestones:"+str(row.Milestone3))

            if row.Milestone4 is not None and not pd.isna(row.Milestone4):
                if not ( memo_milestones_df.Milestone_Name.eq(row.Milestone4).any() or account_milestones_df.Milestone_Name.eq(row.Milestone4).any()):
                    raise ValueError("Milestone 4 was not found in Memo or Account milestones:"+str(row.Milestone4))

            if row.Milestone5 is not None and not pd.isna(row.Milestone5):
                if not ( memo_milestones_df.Milestone_Name.eq(row.Milestone5).any() or account_milestones_df.Milestone_Name.eq(row.Milestone5).any()):
                    raise ValueError("Milestone 5 was not found in Memo or Account milestones:"+str(row.Milestone5))
        self.composite_milestones_df = composite_milestones_df

    def __str__(self):

        return_string = ""

        count_of_milestones = self.memo_milestones_df.shape[0] + self.account_milestones_df.shape[0] + self.composite_milestone_df.shape[0]
        return_string += "Total # of Milestones: "+str(count_of_milestones)+"\n"
        return_string += "Memo Milestones:\n"+ self.memo_milestones_df.to_string()+"\n"
        return_string += "Account Milestones:\n"+ self.account_milestones_df.to_string()+"\n"
        return_string += "Composite Milestones:\n"+ self.composite_milestone_df.to_string()+"\n"

        return return_string


    def addMemoMilestone(self,milestone_name,memo_regex_string):
        raise NotImplementedError

    def addAccountMilestone(self,milestone_name,account_name,min_balance,max_balance):
        raise NotImplementedError

    def addCompositeMilestone(self,milestone_name,*milestone_names):
        raise NotImplementedError
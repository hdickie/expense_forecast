
import pandas as pd
import re
class MilestoneSet:

    def __init__(self,account_set,budget_set,account_milestones__list,memo_milestones__list,composite_milestones__list):

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

        for account_milestone in account_milestones__list:
            all_account_names = set([ a.split(':')[0] for a in account_set.getAccounts().Name ])
            if not account_milestone.account_name in all_account_names:
            #if not all_account_names.eq(account_milestone.account_name).any():
                raise ValueError("Account Name for Milestone not found in accounts: "+str(account_milestone.account_name))

            if account_milestone.max_balance < account_milestone.min_balance:
                raise ValueError("Min_Balance greater than Max_Balance for Account Milestone")

        self.account_milestones__list = account_milestones__list

        for memo_milestone in memo_milestones__list:
            match_found = False
            for index2, row2 in budget_set.getBudgetItems().iterrows():
                if re.search(memo_milestone.memo_regex,row2.Memo) is not None:
                    match_found = True

            if not match_found:
                raise ValueError("Memo Milestone had no matches in budgetset, so no match during forecast calculation is possible.")

        self.memo_milestones__list = memo_milestones__list

        # todo input validation
        for composite_milestone in composite_milestones__list:
            # if composite_milestone.Milestone1 is not None and not pd.isna(row.Milestone1):
            #     if not ( memo_milestones_df.Milestone_Name.eq(composite_milestone.Milestone1).any() or account_milestones_df.Milestone_Name.eq(composite_milestone.Milestone1).any()):
            #         raise ValueError("Milestone 1 was not found in Memo or Account milestones:"+str(composite_milestone.Milestone1))
            pass


        self.composite_milestones__list = composite_milestones__list

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

    def toJSON(self):

        json_string = "{"

        account_milestone_index = 0
        account_milestones_json_string = ""
        for a in self.account_milestones__list:
            account_milestones_json_string = a.toJSON()

            if account_milestone_index != len(self.account_milestones__list):
                account_milestones_json_string += ","

            account_milestone_index += 1

        memo_milestone_index = 0
        memo_milestones_json_string = ""
        for m in self.memo_milestones__list:
            memo_milestones_json_string = m.toJSON()

            if memo_milestone_index != len(self.memo_milestones__list):
                memo_milestones_json_string += ","

            memo_milestone_index += 1

        composite_milestone_index = 0
        composite_milestones_json_string = ""
        for c in self.composite_milestones__list:
            composite_milestones_json_string = c.toJSON()

            if composite_milestone_index != len(self.composite_milestones__list):
                composite_milestones_json_string += ","

            composite_milestone_index += 1

        json_string += '"' + "AccountMilestone" + '":"' + account_milestones_json_string+ '"'
        json_string += '"' + "MemoMilestone" + '":"' + memo_milestones_json_string + '"'
        json_string += '"' + "CompositeMilestone" + '":"' + composite_milestones_json_string + '"'

        json_string += "}"

        return json_string

import MemoMilestone
import AccountMilestone
import pandas as pd

class CompositeMilestone:

    def __init__(self,milestone_name,account_milestones__list, memo_milestones__list):
        self.milestone_name = milestone_name
        self.account_milestones = account_milestones__list
        self.memo_milestones = memo_milestones__list


    def __str__(self):

        return_string = ""

        am_df = pd.DataFrame({ 'Milestone_Name': [],
            'Account_Name': [],
            'Min_Balance': [],
            'Max_Balance': [] })

        for a in self.account_milestones:
            am_df = pd.concat([ am_df, pd.DataFrame({'Milestone_Name': [a.milestone_name], 'Account_Name': [a.account_name], 'Min_Balance': [a.min_balance], 'Max_Balance': [a.max_balance]}) ])

        mm_df = pd.DataFrame({ 'Milestone_Name': [], 'Memo_Regex': []})
        for m in self.memo_milestones:
            mm_df = pd.concat( [ mm_df, pd.DataFrame({'Milestone_Name': [m.milestone_name], 'Milestone_Regex': [m.memo_regex]}) ] )

        return_string += 'Composite Milestone\n'
        return_string += am_df.to_string()
        return_string += '\n'
        return_string += mm_df.to_string()

        return return_string


    def to_json(self):

        return_string = "{"
        for i in range(0,len(self.account_milestones)):
            a = self.account_milestones[i]
            return_string += self.account_milestones[0].to_json()+'\n'
            if i < (len(self.account_milestones)-1):
                return_string += ','

        for i in range(0, len(self.memo_milestones)):
            a = self.memo_milestones[i]
            return_string += self.memo_milestones[0].to_json() + '\n'
            if i < (len(self.memo_milestones) - 1):
                return_string += ','

        return_string += "}"

        return return_string


import MemoMilestone
import AccountMilestone
import pandas as pd

class CompositeMilestone:

    def __init__(self,milestone_name,account_milestones__list, memo_milestones__list, *milestone_names):
        self.milestone_name = milestone_name

        account_milestone_names = [a.milestone_name for a in account_milestones__list]
        memo_milestone_names = [m.milestone_name for m in memo_milestones__list]

        #this needs to explictily record account and memo mielstones, and also not retain any information that is not relevant

        component_milestones__list = []
        #for m_name in milestone_names:
        milestone_names = milestone_names[0] #the input is a table with the input list as the first element. kind of janky...
        for i in range(0,len(milestone_names)):
            m_name = milestone_names[i]

            if pd.isna(m_name):
                continue

            if m_name not in account_milestone_names and m_name not in memo_milestone_names:
                raise ValueError("Milestone \'"+str(m_name)+"\' not found in either account or memo milestones")
            component_milestones__list.append(m_name)

        self.component_milestones__list = component_milestones__list

    def __str__(self):

        return_string = ""

        return_string += "Milestone_Name:"+self.milestone_name+"\n"
        milestone_index = 1
        for component_milestone_name in self.component_milestones__list:
            return_string += "Milestone"+str(milestone_index)+":"+component_milestone_name+"\n"
            milestone_index += 1

        return return_string


    def toJSON(self):

        return_string = "{"

        return_string += '"' + "Milestone_Name:" + '":"' + self.milestone_name + '"' + "\n"
        milestone_index = 1
        for component_milestone_name in self.component_milestones__list:
            return_string += '"' + "Milestone" + str(milestone_index) + '":"' + component_milestone_name + '"' + "\n"
            milestone_index += 1

        return_string += "}"

        return return_string

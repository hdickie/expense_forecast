
import MemoMilestone
import AccountMilestone

class CompositeMilestone:

    def __init__(self,milestone_name,account_milestones__list, memo_milestones__list, *milestone_names):
        self.milestone_name = milestone_name

        self.component_milestones__list = []
        for m_name in milestone_names:
            self.component_milestones__list.append(m_name)

    def __str__(self):

        return_string = ""

        return_string += "Milestone_Name:"+self.milestone_name+"\n"
        milestone_index = 1
        for component_milestone_name in self.component_milestones__list:
            return_string += "Milestone"+str(milestone_index)+":"+component_milestone_name+"\n"
            milestone_index += 1

        return return_string
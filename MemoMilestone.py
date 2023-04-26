
import re
class MemoMilestone:

    def __init__(self,Milestone_Name,Memo_Regex):
        self.milestone_name = Milestone_Name
        self.memo_regex = Memo_Regex

        try:
            re.search(Memo_Regex,'')
        except Exception as e:
            raise e

    def __str__(self):
        return_string = ""

        return_string += "Milestone_Name:" + self.milestone_name + "\n"
        return_string += "Memo_Regex:" + self.memo_regex + "\n"

        return return_string

    def toJSON(self):

        return_string = "{"

        return_string += '"' + "Milestone_Name" + '":"' + self.milestone_name + '"' + "\n"
        return_string += '"' + "Memo_Regex" + '":"' + self.memo_regex + '"' + "\n"

        return_string = "}"

        return return_string
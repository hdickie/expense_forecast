
import re, pandas as pd
class MemoMilestone:

    def __init__(self,Milestone_Name,Memo_Regex):
        self.milestone_name = Milestone_Name
        self.memo_regex = Memo_Regex

        try:
            re.search(Memo_Regex,'')
        except Exception as e:
            raise e

    def __str__(self):
        return pd.DataFrame({
            'Milestone_Name': [self.milestone_name],
            'Memo_Regex': [self.memo_regex]
        }).to_string()

    def to_json(self):

        return_string = "{"

        return_string += '"' + "Milestone_Name" + '":"' + self.milestone_name + '"' + "\n"
        return_string += '"' + "Memo_Regex" + '":"' + self.memo_regex + '"' + "\n"

        return_string = "}"

        return return_string
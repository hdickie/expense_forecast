import re
import pandas as pd
import jsonpickle


class MemoMilestone:

    def __init__(self, Milestone_Name, Memo_Regex):

        self.milestone_name = Milestone_Name
        assert self.milestone_name is not None

        self.memo_regex = Memo_Regex
        assert self.memo_regex is not None

        try:
            re.search(Memo_Regex, "")
        except Exception as e:
            raise e #Not valid regex

    def __str__(self):
        return pd.DataFrame(
            {"Milestone_Name": [self.milestone_name], "Memo_Regex": [self.memo_regex]}
        ).to_string()

    def to_json(self):
        return jsonpickle.encode(self, indent=4)

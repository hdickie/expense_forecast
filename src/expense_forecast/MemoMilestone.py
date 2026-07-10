

import re
import pandas as pd
import jsonpickle


#TODO manual review of MemoMilestone docstring
class MemoMilestone:

    def __init__(self, 
                 Milestone_Name: str, 
                 Memo_Regex: str):

        """
        Initialize a MemoMilestone.

        Construct a milestone by defining the regex to match against the memo line. 
        The date which first returns TRUE for the regex match is the milestone date.
        The supplied arguments completely describe the milestone's evaluation criteria.

        Parameters
        ----------
        Milestone_Name : str

        Memo_Regex : str
            Regex to check against memo line. 

        @interface-report: show
        """
        #TODO DEFER change from AssertionError to ValueError with error message including the illegal values

        self.milestone_name = Milestone_Name
        assert self.milestone_name is not None

        self.memo_regex = Memo_Regex
        assert self.memo_regex is not None

        try:
            re.search(Memo_Regex, "")
        except Exception as e:
            raise e #Not valid regex

    def __str__(self):
        """
        @interface-report: show
        """
        return pd.DataFrame(
            {"Milestone_Name": [self.milestone_name], "Memo_Regex": [self.memo_regex]}
        ).to_string()

    def to_json(self):
        """
        @interface-report: show
        """
        return jsonpickle.encode(self, indent=4)



import re
import pandas as pd
import jsonpickle


#TODO DOC manual review of MemoMilestone docstring
class MemoMilestone:

    def __init__(
        self,
        Milestone_Name: str = None,
        Memo_Regex: str = None,
        *,
        milestone_name: str = None,
        memo_regex: str = None,
    ):

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

        if milestone_name is not None:
            if Milestone_Name is not None:
                raise TypeError("Specify only one milestone name")
            Milestone_Name = milestone_name
        if memo_regex is not None:
            if Memo_Regex is not None:
                raise TypeError("Specify only one memo regex")
            Memo_Regex = memo_regex

        self.milestone_name = Milestone_Name

        self.memo_regex = Memo_Regex
        if self.memo_regex is None:
            raise ValueError("memo_regex cannot be None")

        try:
            re.search(self.memo_regex, "")
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

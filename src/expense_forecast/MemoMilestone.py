"""
Summary
-------

Description
-----------

Contract
--------

@interface-report: show
"""


import re
import pandas as pd
import jsonpickle


#TODO manual review of MemoMilestone docstring
class MemoMilestone:

    """
    Summary
    -------

    Description
    -----------

    Contract
    --------

    @interface-report: show
    """
    #TODO manual review of MemoMilestone.__init__ docstring
    def __init__(self, Milestone_Name, Memo_Regex):

        """
        TODO one-line description of MemoMilestone.__init__.

        TODO multi-line description of MemoMilestone.__init__.
        TODO explain how MemoMilestone.__init__ participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        Milestone_Name : object
            TODO one-line description of MemoMilestone.__init__.Milestone_Name.

        Memo_Regex : object
            TODO one-line description of MemoMilestone.__init__.Memo_Regex.

        Returns
        -------
        None
            TODO one-line description of return value of MemoMilestone.__init__.

        Contract
        --------
        - #TODO contract lines for MemoMilestone.__init__.
        - #TODO document exceptions, mutations, and precision assumptions for MemoMilestone.__init__.

        @interface-report: show
        """
        self.milestone_name = Milestone_Name
        assert self.milestone_name is not None

        self.memo_regex = Memo_Regex
        assert self.memo_regex is not None

        try:
            re.search(Memo_Regex, "")
        except Exception as e:
            raise e #Not valid regex

    #TODO manual review of MemoMilestone.__str__ docstring
    def __str__(self):
        """
        TODO one-line description of MemoMilestone.__str__.

        TODO multi-line description of MemoMilestone.__str__.
        TODO explain how MemoMilestone.__str__ participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that MemoMilestone.__str__ takes no parameters beyond self/cls.

        Returns
        -------
        str
            TODO one-line description of return value of MemoMilestone.__str__.

        Contract
        --------
        - #TODO contract lines for MemoMilestone.__str__.
        - #TODO document exceptions, mutations, and precision assumptions for MemoMilestone.__str__.

        @interface-report: show
        """
        return pd.DataFrame(
            {"Milestone_Name": [self.milestone_name], "Memo_Regex": [self.memo_regex]}
        ).to_string()

    #TODO manual review of MemoMilestone.to_json docstring
    def to_json(self):
        """
        TODO one-line description of MemoMilestone.to_json.

        TODO multi-line description of MemoMilestone.to_json.
        TODO explain how MemoMilestone.to_json participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that MemoMilestone.to_json takes no parameters beyond self/cls.

        Returns
        -------
        str
            TODO one-line description of return value of MemoMilestone.to_json.

        Contract
        --------
        - #TODO contract lines for MemoMilestone.to_json.
        - #TODO document exceptions, mutations, and precision assumptions for MemoMilestone.to_json.

        @interface-report: show
        """
        return jsonpickle.encode(self, indent=4)

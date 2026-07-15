"""
Summary
-------

Description
-----------

Contract
--------

@interface-report: show
"""


import jsonpickle
from .MemoMilestone import MemoMilestone
from .AccountMilestone import AccountMilestone
import pandas as pd


#TODO manual review of CompositeMilestone docstring
class CompositeMilestone:

    """
    Summary
    -------

    Description
    -----------

    Contract
    --------

    @interface-report: show
    """
    #TODO manual review of CompositeMilestone._validate_account_milestones docstring
    @staticmethod
    def _validate_account_milestones(account_milestones):

        """
        TODO one-line description of CompositeMilestone._validate_account_milestones.

        TODO multi-line description of CompositeMilestone._validate_account_milestones.
        TODO explain how CompositeMilestone._validate_account_milestones participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        account_milestones : object
            TODO one-line description of CompositeMilestone._validate_account_milestones.account_milestones.

        Returns
        -------
        None
            TODO one-line description of return value of CompositeMilestone._validate_account_milestones.

        Contract
        --------
        - #TODO contract lines for CompositeMilestone._validate_account_milestones.
        - #TODO document exceptions, mutations, and precision assumptions for CompositeMilestone._validate_account_milestones.

        @interface-report: show
        """
        account_milestone_required_attributes = ['milestone_name',
                                                 'account_name',
                                                 'min_balance',
                                                 'max_balance',
                                                 'to_json']

        for account_milestone in account_milestones:
            for attr in account_milestone_required_attributes:
                if not hasattr(account_milestone, attr):
                    raise TypeError("AccountMilestone did not have expected attribute: " + str(attr))

            non_builtin_attr = [x for x in dir(account_milestone) if '__' not in x]
            for attr in non_builtin_attr:
                assert attr in account_milestone_required_attributes

    #TODO manual review of CompositeMilestone._validate_memo_milestones docstring
    @staticmethod
    def _validate_memo_milestones(memo_milestones):

        """
        TODO one-line description of CompositeMilestone._validate_memo_milestones.

        TODO multi-line description of CompositeMilestone._validate_memo_milestones.
        TODO explain how CompositeMilestone._validate_memo_milestones participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        memo_milestones : object
            TODO one-line description of CompositeMilestone._validate_memo_milestones.memo_milestones.

        Returns
        -------
        None
            TODO one-line description of return value of CompositeMilestone._validate_memo_milestones.

        Contract
        --------
        - #TODO contract lines for CompositeMilestone._validate_memo_milestones.
        - #TODO document exceptions, mutations, and precision assumptions for CompositeMilestone._validate_memo_milestones.

        @interface-report: show
        """
        if not memo_milestones:
            return

        memo_milestone_required_attributes = ['milestone_name', 'memo_regex', 'to_json']

        for memo_milestone in memo_milestones:
            for attr in memo_milestone_required_attributes:
                if not hasattr(memo_milestone, attr):
                    raise TypeError("MemoMilestone did not have expected attribute: " + str(attr))

            non_builtin_attr = [x for x in dir(memo_milestone) if '__' not in x]
            for attr in non_builtin_attr:
                assert attr in memo_milestone_required_attributes


    #TODO manual review of CompositeMilestone.__init__ docstring
    def __init__(self, milestone_name, account_milestones, memo_milestones):
        """
        TODO one-line description of CompositeMilestone.__init__.

        TODO multi-line description of CompositeMilestone.__init__.
        TODO explain how CompositeMilestone.__init__ participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        milestone_name : object
            TODO one-line description of CompositeMilestone.__init__.milestone_name.

        account_milestones : object
            TODO one-line description of CompositeMilestone.__init__.account_milestones.

        memo_milestones : object
            TODO one-line description of CompositeMilestone.__init__.memo_milestones.

        Returns
        -------
        None
            TODO one-line description of return value of CompositeMilestone.__init__.

        Contract
        --------
        - #TODO contract lines for CompositeMilestone.__init__.
        - #TODO document exceptions, mutations, and precision assumptions for CompositeMilestone.__init__.

        @interface-report: show
        """
        if milestone_name is None:
            raise ValueError("Composite Milestone name must not be None")

        if milestone_name.lower().strip() == "":
            raise ValueError("Composite Milestone name must not be empty string")

        self.milestone_name = milestone_name

        self.account_milestones = account_milestones
        CompositeMilestone._validate_account_milestones(self.account_milestones)

        self.memo_milestones = memo_milestones
        CompositeMilestone._validate_memo_milestones(self.memo_milestones)

        #TODO validate unique names and add test









    #TODO manual review of CompositeMilestone.__str__ docstring
    def __str__(self):

        """
        TODO one-line description of CompositeMilestone.__str__.

        TODO multi-line description of CompositeMilestone.__str__.
        TODO explain how CompositeMilestone.__str__ participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that CompositeMilestone.__str__ takes no parameters beyond self/cls.

        Returns
        -------
        str
            TODO one-line description of return value of CompositeMilestone.__str__.

        Contract
        --------
        - #TODO contract lines for CompositeMilestone.__str__.
        - #TODO document exceptions, mutations, and precision assumptions for CompositeMilestone.__str__.

        @interface-report: show
        """
        return_string = ""

        am_df = pd.DataFrame(
            {
                "Milestone_Name": [],
                "Account_Name": [],
                "Min_Balance": [],
                "Max_Balance": [],
            }
        )

        for a in self.account_milestones:
            am_df = pd.concat(
                [
                    am_df,
                    pd.DataFrame(
                        {
                            "Milestone_Name": [a.milestone_name],
                            "Account_Name": [a.account_name],
                            "Min_Balance": [a.min_balance],
                            "Max_Balance": [a.max_balance],
                        }
                    ),
                ]
            )

        mm_df = pd.DataFrame({"Milestone_Name": [], "Memo_Regex": []})
        for m in self.memo_milestones:
            mm_df = pd.concat(
                [
                    mm_df,
                    pd.DataFrame(
                        {
                            "Milestone_Name": [m.milestone_name],
                            "Milestone_Regex": [m.memo_regex],
                        }
                    ),
                ]
            )

        return_string += "Composite Milestone: " + self.milestone_name + "\n"
        return_string += am_df.to_string()
        return_string += "\n"
        return_string += mm_df.to_string()

        return return_string

    #TODO manual review of CompositeMilestone.to_json docstring
    def to_json(self):

        """
        TODO one-line description of CompositeMilestone.to_json.

        TODO multi-line description of CompositeMilestone.to_json.
        TODO explain how CompositeMilestone.to_json participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that CompositeMilestone.to_json takes no parameters beyond self/cls.

        Returns
        -------
        str
            TODO one-line description of return value of CompositeMilestone.to_json.

        Contract
        --------
        - #TODO contract lines for CompositeMilestone.to_json.
        - #TODO document exceptions, mutations, and precision assumptions for CompositeMilestone.to_json.

        @interface-report: show
        """
        return jsonpickle.encode(self, indent=4)

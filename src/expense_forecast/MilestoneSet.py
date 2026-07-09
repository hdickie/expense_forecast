"""
Summary
-------

Description
-----------

Contract
--------

@interface-report: show
"""


import pandas as pd
import re
from .MemoMilestone import MemoMilestone
from .CompositeMilestone import CompositeMilestone
from .AccountMilestone import AccountMilestone
import jsonpickle
import logging
from . import log_methods

logger = log_methods.setup_logger(__name__, "./" + __name__ + ".log", level=logging.DEBUG)


# def initialize_from_dataframe(
#     account_milestones_df, memo_milestones_df, composite_milestones_df
# ):
#
#     am__list = []
#     mm__list = []
#     cm__list = []
#
#     am__dict = {}
#     mm__dict = {}
#
#     for index, row in account_milestones_df.iterrows():
#         new_AM = AccountMilestone(
#             row.milestone_name, row.account_name, row.min_balance, row.max_balance
#         )
#         am__list += [new_AM]
#         am__dict[row.milestone_name] = new_AM
#
#     for index, row in memo_milestones_df.iterrows():
#         new_MM = MemoMilestone(row.milestone_name, row.memo_regex)
#         mm__list += [new_MM]
#         mm__dict[row.milestone_name] = new_MM
#
#     for index, row in composite_milestones_df.iterrows():
#         AM_names = row.account_milestone_name_list.split(";")
#         MM_names = row.memo_milestone_name_list.split(";")
#         related_AM = []
#         related_MM = []
#         for AM_name in AM_names:
#             related_AM.append(am__dict[AM_name])
#         for MM_name in MM_names:
#             related_MM.append(mm__dict[MM_name])
#         cm__list += [
#             CompositeMilestone(
#                 row.composite_milestone_name, related_AM, related_MM
#             )
#         ]
#
#     return MilestoneSet(am__list, mm__list, cm__list)


#TODO manual review of MilestoneSet docstring
class MilestoneSet:

    """
    Summary
    -------

    Description
    -----------

    Contract
    --------

    @interface-report: show
    """
    #TODO manual review of MilestoneSet._validate_unique_account_milestones docstring
    @staticmethod
    def _validate_unique_account_milestones(account_milestones):
        """
        TODO one-line description of MilestoneSet._validate_unique_account_milestones.

        TODO multi-line description of MilestoneSet._validate_unique_account_milestones.
        TODO explain how MilestoneSet._validate_unique_account_milestones participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        account_milestones : object
            TODO one-line description of MilestoneSet._validate_unique_account_milestones.account_milestones.

        Returns
        -------
        None
            TODO one-line description of return value of MilestoneSet._validate_unique_account_milestones.

        Contract
        --------
        - #TODO contract lines for MilestoneSet._validate_unique_account_milestones.
        - #TODO document exceptions, mutations, and precision assumptions for MilestoneSet._validate_unique_account_milestones.

        @interface-report: show
        """
        observed_account_milestones = {}
        if account_milestones is not None:
            for account_milestone in account_milestones:
                am_key = (account_milestone.account_name, account_milestone.min_balance, account_milestone.max_balance)
                if am_key not in observed_account_milestones:
                    observed_account_milestones[am_key] = True
                else:
                    raise ValueError("Duplicate AccountMilestone detected: " + str(am_key))

    #TODO manual review of MilestoneSet._validate_unique_memo_milestones docstring
    @staticmethod
    def _validate_unique_memo_milestones(memo_milestones):
        """
        TODO one-line description of MilestoneSet._validate_unique_memo_milestones.

        TODO multi-line description of MilestoneSet._validate_unique_memo_milestones.
        TODO explain how MilestoneSet._validate_unique_memo_milestones participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        memo_milestones : object
            TODO one-line description of MilestoneSet._validate_unique_memo_milestones.memo_milestones.

        Returns
        -------
        None
            TODO one-line description of return value of MilestoneSet._validate_unique_memo_milestones.

        Contract
        --------
        - #TODO contract lines for MilestoneSet._validate_unique_memo_milestones.
        - #TODO document exceptions, mutations, and precision assumptions for MilestoneSet._validate_unique_memo_milestones.

        @interface-report: show
        """
        observed_memo_milestones = {}
        if memo_milestones is not None:
            for memo_milestone in memo_milestones:
                mm_key = (memo_milestone.milestone_name, memo_milestone.memo_regex)
                if mm_key not in observed_memo_milestones:
                    observed_memo_milestones[mm_key] = True
                else:
                    raise ValueError("Duplicate MemoMilestone detected: " + str(mm_key))

    #TODO manual review of MilestoneSet._validate_unique_composite_milestones docstring
    @staticmethod
    def _validate_unique_composite_milestones(composite_milestones):
        """
        TODO one-line description of MilestoneSet._validate_unique_composite_milestones.

        TODO multi-line description of MilestoneSet._validate_unique_composite_milestones.
        TODO explain how MilestoneSet._validate_unique_composite_milestones participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        composite_milestones : object
            TODO one-line description of MilestoneSet._validate_unique_composite_milestones.composite_milestones.

        Returns
        -------
        None
            TODO one-line description of return value of MilestoneSet._validate_unique_composite_milestones.

        Contract
        --------
        - #TODO contract lines for MilestoneSet._validate_unique_composite_milestones.
        - #TODO document exceptions, mutations, and precision assumptions for MilestoneSet._validate_unique_composite_milestones.

        @interface-report: show
        """
        observed_composite_milestones = {}
        if composite_milestones is not None:
            for composite_milestone in composite_milestones:
                MilestoneSet._validate_unique_account_milestones(composite_milestone.account_milestones)
                MilestoneSet._validate_unique_memo_milestones(composite_milestone.memo_milestones)


                # cm_key = (
                # composite_milestone.account_name, composite_milestone.min_balance, composite_milestone.max_balance)
                # if cm_key not in composite_milestones:
                #     composite_milestones[cm_key] = True
                # else:
                #     raise ValueError("Duplicate CompositeMilestone detected: " + str(cm_key))

    #TODO manual review of MilestoneSet._validate_unique_milestone_names docstring
    @staticmethod
    def _validate_unique_milestone_names(account_milestones, memo_milestones, composite_milestones):
        """
        TODO one-line description of MilestoneSet._validate_unique_milestone_names.

        TODO multi-line description of MilestoneSet._validate_unique_milestone_names.
        TODO explain how MilestoneSet._validate_unique_milestone_names participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        account_milestones : object
            TODO one-line description of MilestoneSet._validate_unique_milestone_names.account_milestones.

        memo_milestones : object
            TODO one-line description of MilestoneSet._validate_unique_milestone_names.memo_milestones.

        composite_milestones : object
            TODO one-line description of MilestoneSet._validate_unique_milestone_names.composite_milestones.

        Returns
        -------
        None
            TODO one-line description of return value of MilestoneSet._validate_unique_milestone_names.

        Contract
        --------
        - #TODO contract lines for MilestoneSet._validate_unique_milestone_names.
        - #TODO document exceptions, mutations, and precision assumptions for MilestoneSet._validate_unique_milestone_names.

        @interface-report: show
        """
        milestone_names = []
        if account_milestones is not None:
            for account_milestone in account_milestones:
                milestone_names.append(account_milestone.milestone_name)

        if memo_milestones is not None:
            for memo_milestone in memo_milestones:
                milestone_names.append(memo_milestone.milestone_name)

        if composite_milestones is not None:
            for composite_milestone in composite_milestones:
                milestone_names.append(composite_milestone.milestone_name)

        if len(milestone_names) != len(set(milestone_names)):
            def find_first_duplicate(lst):
                seen = set()
                for element in lst:
                    if element in seen:
                        return element  # Return as soon as a duplicate is found
                    seen.add(element)
                return None  # Return None if no duplicates are found
            first_offender = find_first_duplicate(milestone_names)
            raise ValueError("Duplicate Milestone Name detected. First Offender: "+str(first_offender))

    #TODO manual review of MilestoneSet.__init__ docstring
    def __init__( self, **kwargs ):

        """
        TODO one-line description of MilestoneSet.__init__.

        TODO multi-line description of MilestoneSet.__init__.
        TODO explain how MilestoneSet.__init__ participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        **kwargs : dict
            TODO one-line description of MilestoneSet.__init__.kwargs.

        Returns
        -------
        None
            TODO one-line description of return value of MilestoneSet.__init__.

        Contract
        --------
        - #TODO contract lines for MilestoneSet.__init__.
        - #TODO document exceptions, mutations, and precision assumptions for MilestoneSet.__init__.

        @interface-report: show
        """
        allowed_kwargs = ['account_milestones', 'memo_milestones', 'composite_milestones']
        for key in kwargs:
            if key not in allowed_kwargs:
                raise TypeError(f"Unexpected keyword argument '{key}'")

        self.account_milestones = kwargs.get('account_milestones',None)
        self.memo_milestones = kwargs.get('memo_milestones', None)
        self.composite_milestones = kwargs.get('composite_milestones', None)

        self._validate_unique_milestone_names(self.account_milestones, self.memo_milestones, self.composite_milestones)
        self._validate_unique_account_milestones(self.account_milestones)
        self._validate_unique_memo_milestones(self.memo_milestones)
        self._validate_unique_composite_milestones(self.composite_milestones)


    #TODO manual review of MilestoneSet.__eq__ docstring
    def __eq__(self, other):
        """
        TODO one-line description of MilestoneSet.__eq__.

        TODO multi-line description of MilestoneSet.__eq__.
        TODO explain how MilestoneSet.__eq__ participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        other : object
            TODO one-line description of MilestoneSet.__eq__.other.

        Returns
        -------
        bool
            TODO one-line description of return value of MilestoneSet.__eq__.

        Contract
        --------
        - #TODO contract lines for MilestoneSet.__eq__.
        - #TODO document exceptions, mutations, and precision assumptions for MilestoneSet.__eq__.

        @interface-report: show
        """
        if not isinstance(other, MilestoneSet):
            return False
        return self.to_json() == other.to_json()


    #TODO manual review of MilestoneSet.__str__ docstring
    def __str__(self):

        """
        TODO one-line description of MilestoneSet.__str__.

        TODO multi-line description of MilestoneSet.__str__.
        TODO explain how MilestoneSet.__str__ participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that MilestoneSet.__str__ takes no parameters beyond self/cls.

        Returns
        -------
        str
            TODO one-line description of return value of MilestoneSet.__str__.

        Contract
        --------
        - #TODO contract lines for MilestoneSet.__str__.
        - #TODO document exceptions, mutations, and precision assumptions for MilestoneSet.__str__.

        @interface-report: show
        """
        return_string = ""

        count_of_milestones = (
            int(len(self.memo_milestones))
            + int(len(self.account_milestones))
            + int(len(self.composite_milestones))
        )
        return_string += "Total # of Milestones: " + str(count_of_milestones) + "\n"

        return_string += "Memo Milestones:\n"
        for M in self.memo_milestones:
            return_string += str(M) + "\n"

        return_string += "Account Milestones:\n"
        for A in self.account_milestones:
            return_string += str(A) + "\n"

        return_string += "Composite Milestones:\n"
        for C in self.composite_milestones:
            return_string += str(C) + "\n"

        return return_string

    #TODO manual review of MilestoneSet.addMemoMilestone docstring
    def addMemoMilestone(self, milestone_name, memo_regex_string):
        """
        TODO one-line description of MilestoneSet.addMemoMilestone.

        TODO multi-line description of MilestoneSet.addMemoMilestone.
        TODO explain how MilestoneSet.addMemoMilestone participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        milestone_name : object
            TODO one-line description of MilestoneSet.addMemoMilestone.milestone_name.

        memo_regex_string : str
            TODO one-line description of MilestoneSet.addMemoMilestone.memo_regex_string.

        Returns
        -------
        object
            TODO one-line description of return value of MilestoneSet.addMemoMilestone.

        Contract
        --------
        - #TODO contract lines for MilestoneSet.addMemoMilestone.
        - #TODO document exceptions, mutations, and precision assumptions for MilestoneSet.addMemoMilestone.

        @interface-report: show
        """
        self.memo_milestones += [
            MemoMilestone(milestone_name, memo_regex_string)
        ]

    #TODO manual review of MilestoneSet.addAccountMilestone docstring
    def addAccountMilestone(
        self, milestone_name, account_name, min_balance, max_balance
    ):
        """
        TODO one-line description of MilestoneSet.addAccountMilestone.

        TODO multi-line description of MilestoneSet.addAccountMilestone.
        TODO explain how MilestoneSet.addAccountMilestone participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        milestone_name : object
            TODO one-line description of MilestoneSet.addAccountMilestone.milestone_name.

        account_name : str
            TODO one-line description of MilestoneSet.addAccountMilestone.account_name.

        min_balance : float
            TODO one-line description of MilestoneSet.addAccountMilestone.min_balance.

        max_balance : float
            TODO one-line description of MilestoneSet.addAccountMilestone.max_balance.

        Returns
        -------
        object
            TODO one-line description of return value of MilestoneSet.addAccountMilestone.

        Contract
        --------
        - #TODO contract lines for MilestoneSet.addAccountMilestone.
        - #TODO document exceptions, mutations, and precision assumptions for MilestoneSet.addAccountMilestone.

        @interface-report: show
        """
        self.account_milestones += [
            AccountMilestone(
                milestone_name, account_name, min_balance, max_balance
            )
        ]

    #TODO manual review of MilestoneSet.addCompositeMilestone docstring
    def addCompositeMilestone(
        self, milestone_name, account_milestones__list, memo_milestones__list
    ):

        """
        TODO one-line description of MilestoneSet.addCompositeMilestone.

        TODO multi-line description of MilestoneSet.addCompositeMilestone.
        TODO explain how MilestoneSet.addCompositeMilestone participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        milestone_name : object
            TODO one-line description of MilestoneSet.addCompositeMilestone.milestone_name.

        account_milestones__list : object
            TODO one-line description of MilestoneSet.addCompositeMilestone.account_milestones__list.

        memo_milestones__list : object
            TODO one-line description of MilestoneSet.addCompositeMilestone.memo_milestones__list.

        Returns
        -------
        object
            TODO one-line description of return value of MilestoneSet.addCompositeMilestone.

        Contract
        --------
        - #TODO contract lines for MilestoneSet.addCompositeMilestone.
        - #TODO document exceptions, mutations, and precision assumptions for MilestoneSet.addCompositeMilestone.

        @interface-report: show
        """
        self.composite_milestones += [
            CompositeMilestone(
                milestone_name, account_milestones__list, memo_milestones__list
            )
        ]

    #TODO manual review of MilestoneSet.to_json docstring
    def to_json(self):
        """
        TODO one-line description of MilestoneSet.to_json.

        TODO multi-line description of MilestoneSet.to_json.
        TODO explain how MilestoneSet.to_json participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that MilestoneSet.to_json takes no parameters beyond self/cls.

        Returns
        -------
        str
            TODO one-line description of return value of MilestoneSet.to_json.

        Contract
        --------
        - #TODO contract lines for MilestoneSet.to_json.
        - #TODO document exceptions, mutations, and precision assumptions for MilestoneSet.to_json.

        @interface-report: show
        """
        return jsonpickle.encode(self, indent=4, unpicklable=False)

    # todo rename?
    #TODO manual review of MilestoneSet.getAccountMilestonesDF docstring
    def getAccountMilestonesDF(self):

        """
        TODO one-line description of MilestoneSet.getAccountMilestonesDF.

        TODO multi-line description of MilestoneSet.getAccountMilestonesDF.
        TODO explain how MilestoneSet.getAccountMilestonesDF participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that MilestoneSet.getAccountMilestonesDF takes no parameters beyond self/cls.

        Returns
        -------
        pd.DataFrame
            TODO one-line description of return value of MilestoneSet.getAccountMilestonesDF.

        Contract
        --------
        - #TODO contract lines for MilestoneSet.getAccountMilestonesDF.
        - #TODO document exceptions, mutations, and precision assumptions for MilestoneSet.getAccountMilestonesDF.

        @interface-report: show
        """
        account_milestones_df = pd.DataFrame(
            {
                "Milestone_Name": [],
                "Account_Name": [],
                "Min_Balance": [],
                "Max_Balance": [],
            }
        )

        if self.account_milestones:
            for a in self.account_milestones:
                account_milestones_df = pd.concat(
                    [
                        account_milestones_df,
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
            account_milestones_df.reset_index(drop=True, inplace=True)
        return account_milestones_df

    #TODO manual review of MilestoneSet.getMemoMilestonesDF docstring
    def getMemoMilestonesDF(self):
        """
        TODO one-line description of MilestoneSet.getMemoMilestonesDF.

        TODO multi-line description of MilestoneSet.getMemoMilestonesDF.
        TODO explain how MilestoneSet.getMemoMilestonesDF participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that MilestoneSet.getMemoMilestonesDF takes no parameters beyond self/cls.

        Returns
        -------
        pd.DataFrame
            TODO one-line description of return value of MilestoneSet.getMemoMilestonesDF.

        Contract
        --------
        - #TODO contract lines for MilestoneSet.getMemoMilestonesDF.
        - #TODO document exceptions, mutations, and precision assumptions for MilestoneSet.getMemoMilestonesDF.

        @interface-report: show
        """
        memo_milestones_df = pd.DataFrame({"Milestone_Name": [], "Memo_Regex": []})

        if self.memo_milestones:
            for m in self.memo_milestones:
                memo_milestones_df = pd.concat(
                    [
                        memo_milestones_df,
                        pd.DataFrame(
                            {
                                "Milestone_Name": [m.milestone_name],
                                "Memo_Regex": [m.memo_regex],
                            }
                        ),
                    ]
                )
            memo_milestones_df.reset_index(drop=True, inplace=True)
        return memo_milestones_df

    #TODO manual review of MilestoneSet.getCompositeMilestonesDF docstring
    def getCompositeMilestonesDF(self):
        """
        TODO one-line description of MilestoneSet.getCompositeMilestonesDF.

        TODO multi-line description of MilestoneSet.getCompositeMilestonesDF.
        TODO explain how MilestoneSet.getCompositeMilestonesDF participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        None
            TODO confirm that MilestoneSet.getCompositeMilestonesDF takes no parameters beyond self/cls.

        Returns
        -------
        pd.DataFrame
            TODO one-line description of return value of MilestoneSet.getCompositeMilestonesDF.

        Contract
        --------
        - #TODO contract lines for MilestoneSet.getCompositeMilestonesDF.
        - #TODO document exceptions, mutations, and precision assumptions for MilestoneSet.getCompositeMilestonesDF.

        @interface-report: show
        """
        composite_milestone_df = pd.DataFrame(
            {"Composite_Milestone_Name": [], "Milestone_Type": [], "Milestone_Name": []}
        )

        if self.composite_milestones:
            for cm in self.composite_milestones:
                if cm.account_milestones:
                    for am in cm.account_milestones:
                        composite_milestone_df = pd.concat(
                            [
                                composite_milestone_df,
                                pd.DataFrame(
                                    {
                                        "Composite_Milestone_Name": [cm.milestone_name],
                                        "Milestone_Type": ["Account"],
                                        "Milestone_Name": [am.milestone_name],
                                    }
                                ),
                            ]
                        )

                if cm.memo_milestones:
                    for mm in cm.memo_milestones:
                        composite_milestone_df = pd.concat(
                            [
                                composite_milestone_df,
                                pd.DataFrame(
                                    {
                                        "Composite_Milestone_Name": [cm.milestone_name],
                                        "Milestone_Type": ["Memo"],
                                        "Milestone_Name": [mm.milestone_name],
                                    }
                                ),
                            ]
                        )
            composite_milestone_df.reset_index(drop=True, inplace=True)
        return composite_milestone_df

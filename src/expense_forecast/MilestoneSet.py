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


class MilestoneSet:

    @staticmethod
    def _validate_unique_account_milestones(account_milestones):
        observed_account_milestones = {}
        if account_milestones is not None:
            for account_milestone in account_milestones:
                am_key = (account_milestone.account_name, account_milestone.min_balance, account_milestone.max_balance)
                if am_key not in observed_account_milestones:
                    observed_account_milestones[am_key] = True
                else:
                    raise ValueError("Duplicate AccountMilestone detected: " + str(am_key))

    @staticmethod
    def _validate_unique_memo_milestones(memo_milestones):
        observed_memo_milestones = {}
        if memo_milestones is not None:
            for memo_milestone in memo_milestones:
                mm_key = (memo_milestone.milestone_name, memo_milestone.memo_regex)
                if mm_key not in observed_memo_milestones:
                    observed_memo_milestones[mm_key] = True
                else:
                    raise ValueError("Duplicate MemoMilestone detected: " + str(mm_key))

    @staticmethod
    def _validate_unique_composite_milestones(composite_milestones):
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

    @staticmethod
    def _validate_unique_milestone_names(account_milestones, memo_milestones, composite_milestones):
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

    def __init__( self, **kwargs ):

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


    def __eq__(self, other):
        if not isinstance(other, MilestoneSet):
            return False
        return self.to_json() == other.to_json()


    def __str__(self):

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

    def addMemoMilestone(self, milestone_name, memo_regex_string):
        self.memo_milestones += [
            MemoMilestone(milestone_name, memo_regex_string)
        ]

    def addAccountMilestone(
        self, milestone_name, account_name, min_balance, max_balance
    ):
        self.account_milestones += [
            AccountMilestone(
                milestone_name, account_name, min_balance, max_balance
            )
        ]

    def addCompositeMilestone(
        self, milestone_name, account_milestones__list, memo_milestones__list
    ):

        self.composite_milestones += [
            CompositeMilestone(
                milestone_name, account_milestones__list, memo_milestones__list
            )
        ]

    def to_json(self):
        return jsonpickle.encode(self, indent=4, unpicklable=False)

    # todo rename?
    def getAccountMilestonesDF(self):

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

    def getMemoMilestonesDF(self):
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

    def getCompositeMilestonesDF(self):
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

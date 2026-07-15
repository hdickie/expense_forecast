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
    @staticmethod
    def _account_milestone_value_series(forecast_df, account_name):
        if account_name in forecast_df.columns:
            return forecast_df[account_name]

        account_component_groups = [
            [
                f"{account_name}: Curr Stmt Bal",
                f"{account_name}: Prev Stmt Bal",
            ],
            [
                f"{account_name}: Principal Balance",
                f"{account_name}: Interest",
            ],
        ]
        for component_columns in account_component_groups:
            if all(column_name in forecast_df.columns for column_name in component_columns):
                return (
                    forecast_df[component_columns]
                    .apply(pd.to_numeric, errors="coerce")
                    .sum(axis=1, min_count=1)
                )

        raise ValueError(
            "Could not find forecast columns for account milestone account_name "
            + repr(account_name)
        )

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
    def __init__(self, milestones=None, **kwargs):

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

        self.account_milestones = list(kwargs.get('account_milestones') or [])
        self.memo_milestones = list(kwargs.get('memo_milestones') or [])
        self.composite_milestones = list(kwargs.get('composite_milestones') or [])

        if milestones is not None:
            if not isinstance(milestones, dict):
                raise TypeError("MilestoneSet positional input must be a mapping")
            for milestone_name, milestone in milestones.items():
                if not isinstance(milestone_name, str) or not milestone_name.strip():
                    raise ValueError("Milestone names must be non-empty strings")
                existing_name = getattr(milestone, "milestone_name", None)
                if existing_name not in (None, milestone_name):
                    raise ValueError(
                        f"Milestone mapping name {milestone_name!r} conflicts with "
                        f"object name {existing_name!r}"
                    )
                milestone.milestone_name = milestone_name
                if isinstance(milestone, AccountMilestone):
                    self.account_milestones.append(milestone)
                elif isinstance(milestone, MemoMilestone):
                    self.memo_milestones.append(milestone)
                elif isinstance(milestone, CompositeMilestone):
                    self.composite_milestones.append(milestone)
                else:
                    raise TypeError(
                        f"Unsupported milestone type: {type(milestone).__name__}"
                    )

        self._validate_unique_milestone_names(self.account_milestones, self.memo_milestones, self.composite_milestones)
        self._validate_unique_account_milestones(self.account_milestones)
        self._validate_unique_memo_milestones(self.memo_milestones)
        self._validate_unique_composite_milestones(self.composite_milestones)

    @property
    def milestone_names(self):
        return {
            milestone.milestone_name
            for milestone in (
                self.account_milestones
                + self.memo_milestones
                + self.composite_milestones
            )
        }


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


    # TODO evaluateAccountMilestone does not seem like it belongs on F
    #TODO manual review of ForecastHandler.evaluateAccountMilestone docstring
    @classmethod
    def evaluateAccountMilestone(
        cls, forecast_df, account_name, min_balance, max_balance, log_stack_depth
    ):
        # log_in_color(
        #     logger,
        #     "yellow",
        #     "debug",
        #     "ENTER evaluateAccountMilestone("
        #     + str(account_name)
        #     + ","
        #     + str(min_balance)
        #     + ","
        #     + str(max_balance)
        #     + ")",
        #     log_stack_depth,
        # )
        """
        TODO one-line description of ForecastHandler.evaluateAccountMilestone.

        TODO multi-line description of ForecastHandler.evaluateAccountMilestone.
        TODO explain how ForecastHandler.evaluateAccountMilestone participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        forecast_df : object
            TODO one-line description of ForecastHandler.evaluateAccountMilestone.forecast_df.

        account_name : str
            TODO one-line description of ForecastHandler.evaluateAccountMilestone.account_name.

        min_balance : float
            TODO one-line description of ForecastHandler.evaluateAccountMilestone.min_balance.

        max_balance : float
            TODO one-line description of ForecastHandler.evaluateAccountMilestone.max_balance.

        log_stack_depth : int
            TODO one-line description of ForecastHandler.evaluateAccountMilestone.log_stack_depth.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler.evaluateAccountMilestone.

        Contract
        --------
        - #TODO contract lines for ForecastHandler.evaluateAccountMilestone.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler.evaluateAccountMilestone.

        @interface-report: show
        """
        log_stack_depth += 1
        value_series = cls._account_milestone_value_series(forecast_df, account_name)

        # A valid success date stays valid until the end.
        found_a_valid_success_date = False
        success_date = "None"
        for row_index, row in forecast_df.iterrows():
            current_value = value_series.loc[row_index]
            if (
                (min_balance <= current_value) & (current_value <= max_balance)
            ) and not found_a_valid_success_date:
                found_a_valid_success_date = True
                success_date = row.Date
                # log_in_color(
                #     logger,
                #     "yellow",
                #     "debug",
                #     "success_date:" + str(success_date),
                #     log_stack_depth,
                # )
            elif (min_balance > current_value) | (current_value > max_balance):
                found_a_valid_success_date = False
                success_date = "None"
                # log_in_color(
                #     logger,
                #     "yellow",
                #     "debug",
                #     "success_date:None",
                #     log_stack_depth,
                # )

        # log_in_color(logger, 'yellow', 'debug', 'relevant_time_series_df:')
        # log_in_color(logger, 'yellow', 'debug', relevant_time_series_df.to_string())
        #
        # log_in_color(logger, 'yellow', 'debug', 'last_value:')
        # log_in_color(logger, 'yellow', 'debug', last_value)

        #
        # #if the last day of the forecast does not satisfy account bounds, then none of the days of the forecast qualify
        # if not (( min_balance <= last_value ) & ( last_value <= max_balance )):
        #     log_in_color(logger,'yellow', 'debug','EXIT evaluateAccountMilestone(' + str(account_name) + ',' + str(min_balance) + ',' + str(max_balance) + ') None')
        #     return None
        #
        # #if the code reaches this point, then the milestone was for sure reached.
        # #We can find the first day that qualifies my reverseing the sequence and returning the day before the first day that doesnt qualify
        # relevant_time_series_df = relevant_time_series_df.loc[::-1]
        # last_qualifying_date = relevant_time_series_df.head(1).Date.iat[0]
        # for index, row in relevant_time_series_df.iterrows():
        #     # print('row:')
        #     # print(row)
        #     # print(row.iloc[1])
        #     if (( min_balance <= row.iloc[1] ) & ( row.iloc[1] <= max_balance )):
        #         last_qualifying_date = row.Date.iat[0]
        #     else:
        #         break
        log_stack_depth -= 1
        # log_in_color(
        #     logger,
        #     "yellow",
        #     "debug",
        #     "EXIT evaluateAccountMilestone("
        #     + str(account_name)
        #     + ","
        #     + str(min_balance)
        #     + ","
        #     + str(max_balance)
        #     + ") "
        #     + str(success_date),
        #     log_stack_depth,
        # )
        return success_date

    #TODO manual review of MilestoneSet.evaulateMemoMilestone docstring
    @classmethod
    def evaulateMemoMilestone(cls, forecast_df, memo_regex, log_stack_depth):
        # log_in_color(
        #     logger,
        #     "yellow",
        #     "debug",
        #     "ENTER evaluateMemoMilestone(" + str(memo_regex) + ")",
        #     log_stack_depth,
        # )
        """
        TODO one-line description of ForecastHandler.evaulateMemoMilestone.

        TODO multi-line description of ForecastHandler.evaulateMemoMilestone.
        TODO explain how ForecastHandler.evaulateMemoMilestone participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        forecast_df : object
            TODO one-line description of ForecastHandler.evaulateMemoMilestone.forecast_df.

        memo_regex : str
            TODO one-line description of ForecastHandler.evaulateMemoMilestone.memo_regex.

        log_stack_depth : int
            TODO one-line description of ForecastHandler.evaulateMemoMilestone.log_stack_depth.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler.evaulateMemoMilestone.

        Contract
        --------
        - #TODO contract lines for ForecastHandler.evaulateMemoMilestone.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler.evaulateMemoMilestone.

        @interface-report: show
        """
        log_stack_depth += 1
        for forecast_index, forecast_row in forecast_df.iterrows():
            m = re.search(memo_regex, forecast_row.Memo)
            if m is not None:
                log_stack_depth -= 1
                # log_in_color(
                #     logger,
                #     "yellow",
                #     "debug",
                #     "EXIT evaluateMemoMilestone(" + str(memo_regex) + ")",
                #     log_stack_depth,
                # )
                return forecast_row.Date

        log_stack_depth -= 1
        # log_in_color(
        #     logger,
        #     "yellow",
        #     "debug",
        #     "EXIT evaluateMemoMilestone(" + str(memo_regex) + ")",
        #     log_stack_depth,
        # )
        return None

    #TODO manual review of MilestoneSet.evaluateCompositeMilestone docstring
    @classmethod
    def evaluateCompositeMilestone(
        cls,
        forecast_df,
        list_of_account_milestones,
        list_of_memo_milestones,
        log_stack_depth,
    ):
        # log_in_color(
        #     logger,
        #     "yellow",
        #     "debug",
        #     "ENTER evaluateCompositeMilestone()",
        #     log_stack_depth,
        # )
        """
        TODO one-line description of ForecastHandler.evaluateCompositeMilestone.

        TODO multi-line description of ForecastHandler.evaluateCompositeMilestone.
        TODO explain how ForecastHandler.evaluateCompositeMilestone participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        forecast_df : object
            TODO one-line description of ForecastHandler.evaluateCompositeMilestone.forecast_df.

        list_of_account_milestones : object
            TODO one-line description of ForecastHandler.evaluateCompositeMilestone.list_of_account_milestones.

        list_of_memo_milestones : object
            TODO one-line description of ForecastHandler.evaluateCompositeMilestone.list_of_memo_milestones.

        log_stack_depth : int
            TODO one-line description of ForecastHandler.evaluateCompositeMilestone.log_stack_depth.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler.evaluateCompositeMilestone.

        Contract
        --------
        - #TODO contract lines for ForecastHandler.evaluateCompositeMilestone.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler.evaluateCompositeMilestone.

        @interface-report: show
        """
        log_stack_depth += 1
        # list_of_account_milestones is lists of 3-tuples that are (string,float,float) for parameters

        # todo composite milestones may contain some milestones that arent listed in the composite #https://github.com/hdickie/expense_forecast/issues/22

        if list_of_account_milestones:
            num_of_acct_milestones = len(list_of_account_milestones)
        else:
            num_of_acct_milestones = 0

        if list_of_memo_milestones:
            num_of_memo_milestones = len(list_of_memo_milestones)
        else:
            num_of_memo_milestones = 0
        account_milestone_dates = []
        memo_milestone_dates = []

        for i in range(0, num_of_acct_milestones):
            account_milestone = list_of_account_milestones[i]
            am_result = cls.evaluateAccountMilestone(
                forecast_df,
                account_milestone.account_name,
                account_milestone.min_balance,
                account_milestone.max_balance, log_stack_depth=log_stack_depth
            )
            if (
                am_result is None
            ):  # disqualified immediately because success requires ALL
                log_stack_depth -= 1
                # log_in_color(
                #     logger,
                #     "yellow",
                #     "debug",
                #     "EXIT evaluateCompositeMilestone() None",
                #     log_stack_depth,
                # )
                return None
            account_milestone_dates.append(am_result)

        for i in range(0, num_of_memo_milestones):
            memo_milestone = list_of_memo_milestones[i]
            mm_result = cls.evaulateMemoMilestone(
                forecast_df, memo_milestone.memo_regex, log_stack_depth=log_stack_depth
            )
            if (
                mm_result is None
            ):  # disqualified immediately because success requires ALL
                log_stack_depth -= 1
                # log_in_color(
                #     logger,
                #     "yellow",
                #     "debug",
                #     "EXIT evaluateCompositeMilestone() None",
                #     log_stack_depth,
                # )
                return None
            memo_milestone_dates.append(mm_result)

        result_date = max(account_milestone_dates + memo_milestone_dates)
        # log_in_color(
        #     logger,
        #     "yellow",
        #     "debug",
        #     "EXIT evaluateCompositeMilestone() " + str(result_date),
        #     log_stack_depth,
        # )
        log_stack_depth -= 1
        return result_date

    #TODO manual review of MilestoneSet.evaluateMilestones docstring
    @classmethod
    def evaluateMilestones(cls, forecast_df, milestone_set, log_stack_depth):

        """
        TODO one-line description of ForecastHandler.evaluateMilestones.

        TODO multi-line description of ForecastHandler.evaluateMilestones.
        TODO explain how ForecastHandler.evaluateMilestones participates in this module.
        TODO document important state, validation, or serialization behavior.

        Parameters
        ----------
        forecast_df : object
            TODO one-line description of ForecastHandler.evaluateMilestones.forecast_df.

        milestone_set : object
            TODO one-line description of ForecastHandler.evaluateMilestones.milestone_set.

        log_stack_depth : int
            TODO one-line description of ForecastHandler.evaluateMilestones.log_stack_depth.

        Returns
        -------
        object
            TODO one-line description of return value of ForecastHandler.evaluateMilestones.

        Contract
        --------
        - #TODO contract lines for ForecastHandler.evaluateMilestones.
        - #TODO document exceptions, mutations, and precision assumptions for ForecastHandler.evaluateMilestones.

        @interface-report: show
        """
        account_milestone_results = {}
        if milestone_set.account_milestones:
            for a_m in milestone_set.account_milestones:
                res = cls.evaluateAccountMilestone(
                    forecast_df,
                    a_m.account_name,
                    a_m.min_balance,
                    a_m.max_balance,
                    log_stack_depth=log_stack_depth,
                )
                account_milestone_results[a_m.milestone_name] = res
            account_milestone_results = account_milestone_results

        memo_milestone_results = {}
        if milestone_set.memo_milestones:
            for m_m in milestone_set.memo_milestones:
                res = cls.evaulateMemoMilestone(
                    forecast_df, m_m.memo_regex, log_stack_depth=log_stack_depth
                )
                memo_milestone_results[m_m.milestone_name] = res
            memo_milestone_results = memo_milestone_results

        composite_milestone_results = {}
        if milestone_set.composite_milestones:
            for c_m in milestone_set.composite_milestones:
                res = cls.evaluateCompositeMilestone(
                    forecast_df,
                    c_m.account_milestones,
                    c_m.memo_milestones,
                    log_stack_depth=log_stack_depth,
                )
                composite_milestone_results[c_m.milestone_name] = res
            composite_milestone_results = composite_milestone_results
        return [account_milestone_results, memo_milestone_results, composite_milestone_results] #TODO list is not the best type for this

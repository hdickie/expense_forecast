import jsonpickle
import MemoMilestone
import AccountMilestone
import pandas as pd


class CompositeMilestone:

    @staticmethod
    def _validate_account_milestones(account_milestones):

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

    @staticmethod
    def _validate_memo_milestones(memo_milestones):
        memo_milestone_required_attributes = ['milestone_name', 'memo_regex', 'to_json']

        for memo_milestone in memo_milestones:
            for attr in memo_milestone_required_attributes:
                if not hasattr(memo_milestone, attr):
                    raise TypeError("MemoMilestone did not have expected attribute: " + str(attr))

            non_builtin_attr = [x for x in dir(memo_milestone) if '__' not in x]
            for attr in non_builtin_attr:
                assert attr in memo_milestone_required_attributes


    def __init__(self, milestone_name, account_milestones, memo_milestones):
        self.milestone_name = milestone_name

        self.account_milestones = account_milestones
        CompositeMilestone._validate_account_milestones(self.account_milestones)

        self.memo_milestones = memo_milestones
        CompositeMilestone._validate_memo_milestones(self.memo_milestones)

        #todo validate unique names









    def __str__(self):

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

    def to_json(self):

        return jsonpickle.encode(self, indent=4)

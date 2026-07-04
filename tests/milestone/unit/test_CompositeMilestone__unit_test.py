import pytest

from expense_forecast.AccountMilestone import AccountMilestone
from expense_forecast.MemoMilestone import MemoMilestone
from expense_forecast.CompositeMilestone import CompositeMilestone


class TestCompositeMilestoneMethods:

    @pytest.mark.unit
    def test_CompositeMilestone_constructor__valid_inputs(self):
        A_1 = AccountMilestone("Milestone_1", "Account_Name1", 0, 100)
        A_2 = AccountMilestone("Milestone_2", "Account_Name2", 0, 100)
        M_1 = MemoMilestone("Milestone_3", "memo_regex1")
        M_2 = MemoMilestone("Milestone_4", "memo_regex2")

        # milestone_name,account_milestones__list, memo_milestones__list
        CompositeMilestone("Milestone Name", [A_1, A_2], [M_1, M_2])

    @pytest.mark.unit
    def test_CompositeMilestone_constructor__invalid_inputs(self):
        valid_account_milestone = AccountMilestone(
            "Milestone_1", "Account_Name1", 0, 100
        )
        valid_memo_milestone = MemoMilestone(
            "Milestone_2", "memo_regex"
        )

        # Invalid milestone name
        with pytest.raises((TypeError, ValueError)):
            CompositeMilestone(None, [valid_account_milestone], [valid_memo_milestone])

        with pytest.raises((TypeError, ValueError)):
            CompositeMilestone("", [valid_account_milestone], [valid_memo_milestone])

        # Invalid AccountMilestone list
        with pytest.raises((TypeError, ValueError)):
            CompositeMilestone(
                "Milestone",
                None,
                [valid_memo_milestone],
            )

        # this is not an expected use case but there is not a problem with it
        # with pytest.raises((TypeError, ValueError)):
        #     CompositeMilestone(
        #         "Milestone",
        #         [],
        #         [valid_memo_milestone],
        #     )

        with pytest.raises((TypeError, ValueError)):
            CompositeMilestone(
                "Milestone",
                [valid_memo_milestone],  # wrong milestone type
                [valid_memo_milestone],
            )

        # this is not an expected use case but there is not a problem with it
        # with pytest.raises((TypeError, ValueError)):
        #     CompositeMilestone(
        #         "Milestone",
        #         [valid_account_milestone],
        #         None,
        #     )

        # this is not an expected use case but there is not a problem with it
        # with pytest.raises((TypeError, ValueError)):
        #     CompositeMilestone(
        #         "Milestone",
        #         [valid_account_milestone],
        #         [],
        #     )

        with pytest.raises((TypeError, ValueError)):
            CompositeMilestone(
                "Milestone",
                [valid_account_milestone],
                [valid_account_milestone],  # wrong milestone type
            )

    @pytest.mark.unit
    def test_str(self):
        A_1 = AccountMilestone("Milestone_1", "Account_Name1", 0, 100)
        A_2 = AccountMilestone("Milestone_2", "Account_Name2", 0, 100)
        M_1 = MemoMilestone("Milestone_3", "memo_regex1")
        M_2 = MemoMilestone("Milestone_4", "memo_regex2")

        # milestone_name,account_milestones__list, memo_milestones__list
        C = CompositeMilestone(
            "Milestone Name", [A_1, A_2], [M_1, M_2]
        )
        str(C)

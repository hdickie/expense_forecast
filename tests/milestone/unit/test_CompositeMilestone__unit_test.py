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
    @pytest.mark.skip(reason="implement")
    def test_CompositeMilestone_constructor__invalid_inputs(self):
        pass

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

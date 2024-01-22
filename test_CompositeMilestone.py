import pytest

import AccountMilestone
import MemoMilestone
import CompositeMilestone

class TestCompositeMilestoneMethods:

    def test_CompositeMilestone_constructor__valid_inputs(self):
        A_1 = AccountMilestone.AccountMilestone('Milestone_1','Account_Name1',0,100)
        A_2 = AccountMilestone.AccountMilestone('Milestone_2', 'Account_Name2', 0, 100)
        M_1 = MemoMilestone.MemoMilestone('Milestone_3', 'memo_regex1')
        M_2 = MemoMilestone.MemoMilestone('Milestone_4', 'memo_regex2')

        #milestone_name,account_milestones__list, memo_milestones__list
        CompositeMilestone.CompositeMilestone('Milestone Name',[A_1,A_2],[M_1,M_2])


    def test_CompositeMilestone_constructor__invalid_inputs(self):
        pass

    def test_str(self):
        A_1 = AccountMilestone.AccountMilestone('Milestone_1', 'Account_Name1', 0, 100)
        A_2 = AccountMilestone.AccountMilestone('Milestone_2', 'Account_Name2', 0, 100)
        M_1 = MemoMilestone.MemoMilestone('Milestone_3', 'memo_regex1')
        M_2 = MemoMilestone.MemoMilestone('Milestone_4', 'memo_regex2')

        # milestone_name,account_milestones__list, memo_milestones__list
        C = CompositeMilestone.CompositeMilestone('Milestone Name', [A_1, A_2], [M_1, M_2])
        str(C)

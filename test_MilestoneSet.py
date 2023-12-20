import pytest
import AccountMilestone
import MemoMilestone
import MilestoneSet
import AccountSet
import BudgetSet
import CompositeMilestone

class TestMilestoneSetMethods:
    def test_MilestoneSet_constructor__valid_inputs(self):

        A = AccountSet.AccountSet([])
        A.createAccount(
            'Account_Name1',
            0,
            0,
            0,
            'checking'
        )
        A.createAccount(
            'Account_Name2',
            0,
            0,
            0,
            'checking'
        )

        B = BudgetSet.BudgetSet([])
        B.addBudgetItem('20000101','20000101',1,'once',10,'memo_regex1',False,False)
        B.addBudgetItem('20000101', '20000101', 1, 'once', 10, 'memo_regex2',False,False)

        A_1 = AccountMilestone.AccountMilestone('Milestone_1', 'Account_Name1', 0, 100)
        A_2 = AccountMilestone.AccountMilestone('Milestone_2', 'Account_Name2', 0, 100)

        M_1 = MemoMilestone.MemoMilestone('Milestone_3', 'memo_regex1')
        M_2 = MemoMilestone.MemoMilestone('Milestone_4', 'memo_regex2')

        C_1 = CompositeMilestone.CompositeMilestone('C1',[],[])
        C_2 = CompositeMilestone.CompositeMilestone('C2',[],[])


        MilestoneSet.MilestoneSet(A,B,
            [A_1,A_2],
            [M_1,M_2],
            [C_1,C_2])


    def test_MilestoneSet_constructor__invalid_inputs(self):
        pass


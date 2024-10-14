# import pytest
# import AccountMilestone
# import MemoMilestone
# import MilestoneSet
# import AccountSet
# import BudgetSet
# import CompositeMilestone
#
# class TestMilestoneSetMethods:
#     def test_MilestoneSet_constructor__valid_inputs(self):
#
#         A = AccountSet.AccountSet([])
#         A.createAccount(
#             'Account_Name1',
#             0,
#             0,
#             0,
#             'checking'
#         )
#         A.createAccount(
#             'Account_Name2',
#             0,
#             0,
#             0,
#             'checking'
#         )
#
#         B = BudgetSet.BudgetSet([])
#         B.addBudgetItem('20000101','20000101',1,'once',10,'memo_regex1',False,False)
#         B.addBudgetItem('20000101', '20000101', 1, 'once', 10, 'memo_regex2',False,False)
#
#         A_1 = AccountMilestone.AccountMilestone('Milestone_1', 'Account_Name1', 0, 100)
#         A_2 = AccountMilestone.AccountMilestone('Milestone_2', 'Account_Name2', 0, 100)
#
#         M_1 = MemoMilestone.MemoMilestone('Milestone_3', 'memo_regex1')
#         M_2 = MemoMilestone.MemoMilestone('Milestone_4', 'memo_regex2')
#
#         C_1 = CompositeMilestone.CompositeMilestone('C1',[],[])
#         C_2 = CompositeMilestone.CompositeMilestone('C2',[],[])
#
#
#         MilestoneSet.MilestoneSet(
#             [A_1,A_2],
#             [M_1,M_2],
#             [C_1,C_2])
#
#
#     # input validation would happen in ExpenseForecast
#     # def test_MilestoneSet_constructor__invalid_inputs(self):
#     #     A = AccountSet.AccountSet([])
#     #     A.createAccount(
#     #         'Account_Name1',
#     #         0,
#     #         0,
#     #         0,
#     #         'checking'
#     #     )
#     #     A.createAccount(
#     #         'Account_Name2',
#     #         0,
#     #         0,
#     #         0,
#     #         'checking'
#     #     )
#     #
#     #     B = BudgetSet.BudgetSet([])
#     #     B.addBudgetItem('20000101', '20000101', 1, 'once', 10, 'memo_regex1', False, False)
#     #     B.addBudgetItem('20000101', '20000101', 1, 'once', 10, 'memo_regex2', False, False)
#     #
#     #     A_1 = AccountMilestone.AccountMilestone('Milestone_1', 'Shmaccount_Name1', 0, 100) #name not found error
#     #     with pytest.raises(ValueError):
#     #         MilestoneSet.MilestoneSet([A_1],
#     #                                   [],
#     #                                   [])
#     #
#     #     A = AccountSet.AccountSet([])
#     #     A.createAccount(
#     #         'Account_Name1',
#     #         0,
#     #         0,
#     #         0,
#     #         'checking'
#     #     )
#     #     A.createAccount(
#     #         'Account_Name2',
#     #         0,
#     #         0,
#     #         0,
#     #         'checking'
#     #     )
#     #
#     #     B = BudgetSet.BudgetSet([])
#     #     B.addBudgetItem('20000101', '20000101', 1, 'once', 10, 'memo_regex1', False, False)
#     #     B.addBudgetItem('20000101', '20000101', 1, 'once', 10, 'memo_regex2', False, False)
#     #
#     #     M_1 = MemoMilestone.MemoMilestone('Milestone_3', 'shmemo_regex1') #no match possible
#     #
#     #     with pytest.raises(ValueError):
#     #         MilestoneSet.MilestoneSet(A, B,
#     #                                   [],
#     #                                   [M_1],
#     #                                   [])
#
#
#     def test_str(self):
#         A = AccountSet.AccountSet([])
#         A.createAccount(
#             'Account_Name1',
#             0,
#             0,
#             0,
#             'checking'
#         )
#         A.createAccount(
#             'Account_Name2',
#             0,
#             0,
#             0,
#             'checking'
#         )
#
#         B = BudgetSet.BudgetSet([])
#         B.addBudgetItem('20000101', '20000101', 1, 'once', 10, 'memo_regex1', False, False)
#         B.addBudgetItem('20000101', '20000101', 1, 'once', 10, 'memo_regex2', False, False)
#
#         A_1 = AccountMilestone.AccountMilestone('Milestone_1', 'Account_Name1', 0, 100)
#         A_2 = AccountMilestone.AccountMilestone('Milestone_2', 'Account_Name2', 0, 100)
#
#         M_1 = MemoMilestone.MemoMilestone('Milestone_3', 'memo_regex1')
#         M_2 = MemoMilestone.MemoMilestone('Milestone_4', 'memo_regex2')
#
#         C_1 = CompositeMilestone.CompositeMilestone('C1', [], [])
#         C_2 = CompositeMilestone.CompositeMilestone('C2', [], [])
#
#         M = MilestoneSet.MilestoneSet([A_1, A_2],
#                                   [M_1, M_2],
#                                   [C_1, C_2])
#         str(M)
#
#     def test_addAccountMilestone(self):
#         A = AccountSet.AccountSet([])
#         A.createAccount(
#             'Account_Name1',
#             0,
#             0,
#             0,
#             'checking'
#         )
#         A.createAccount(
#             'Account_Name2',
#             0,
#             0,
#             0,
#             'checking'
#         )
#
#         B = BudgetSet.BudgetSet([])
#         B.addBudgetItem('20000101', '20000101', 1, 'once', 10, 'memo_regex1', False, False)
#         B.addBudgetItem('20000101', '20000101', 1, 'once', 10, 'memo_regex2', False, False)
#
#         M = MilestoneSet.MilestoneSet([],
#                                       [],
#                                       [])
#         M.addAccountMilestone('Milestone_1', 'Account_Name1', 0, 100)
#
#     def test_addMemoMilestone(self):
#         A = AccountSet.AccountSet([])
#         A.createAccount(
#             'Account_Name1',
#             0,
#             0,
#             0,
#             'checking'
#         )
#         A.createAccount(
#             'Account_Name2',
#             0,
#             0,
#             0,
#             'checking'
#         )
#
#         B = BudgetSet.BudgetSet([])
#         B.addBudgetItem('20000101', '20000101', 1, 'once', 10, 'memo_regex1', False, False)
#         B.addBudgetItem('20000101', '20000101', 1, 'once', 10, 'memo_regex2', False, False)
#
#         M = MilestoneSet.MilestoneSet([],
#                                       [],
#                                       [])
#         M.addMemoMilestone('Milestone_3', 'memo_regex1')
#
#     def test_addCompositeMilestone(self):
#         A = AccountSet.AccountSet([])
#         A.createAccount(
#             'Account_Name1',
#             0,
#             0,
#             0,
#             'checking'
#         )
#         A.createAccount(
#             'Account_Name2',
#             0,
#             0,
#             0,
#             'checking'
#         )
#
#         B = BudgetSet.BudgetSet([])
#         B.addBudgetItem('20000101', '20000101', 1, 'once', 10, 'memo_regex1', False, False)
#         B.addBudgetItem('20000101', '20000101', 1, 'once', 10, 'memo_regex2', False, False)
#
#         A_1 = AccountMilestone.AccountMilestone('Milestone_1', 'Account_Name1', 0, 100)
#         A_2 = AccountMilestone.AccountMilestone('Milestone_2', 'Account_Name2', 0, 100)
#
#         M_1 = MemoMilestone.MemoMilestone('Milestone_3', 'memo_regex1')
#         M_2 = MemoMilestone.MemoMilestone('Milestone_4', 'memo_regex2')
#
#         M = MilestoneSet.MilestoneSet([A_1, A_2],
#                                       [M_1, M_2],
#                                       [])
#         M.addCompositeMilestone('C1', [], [])

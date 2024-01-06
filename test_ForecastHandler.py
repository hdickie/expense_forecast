import pytest

import AccountMilestone
import CompositeMilestone
import ExpenseForecast
import ForecastHandler, AccountSet, BudgetSet, MemoRuleSet
import pandas as pd, numpy as np
import datetime, logging

import MemoMilestone
import MilestoneSet

pd.options.mode.chained_assignment = None #apparently this warning can throw false positives???

from log_methods import log_in_color
from log_methods import setup_logger
logger = setup_logger('test_ForecastHandler', './log/test_ForecastHandler.log', level=logging.DEBUG)

import copy

class TestForecastHandlerMethods:

    def test_ForecastHandler_Constructor(self):
        F = ForecastHandler.ForecastHandler()

    # def test_calculateMultipleChooseOne(self):
    #     raise NotImplementedError
    #
    # def test_generateCompareTwoForecastsHTMLReport(self):
    #     raise NotImplementedError
    #
    # def test_generateHTMLReport(self):
    #
    #     start_date_YYYYMMDD = '20240101'
    #     end_date_YYYYMMDD = '20240201'
    #
    #     A = AccountSet.AccountSet([])
    #     A.createAccount('Checking',2000,0,999999,'checking')
    #     A.createAccount('Credit', 2000, 0, 999999, 'credit','20240107','compound',0.24,'monthly',60,2000)
    #     A.createAccount('Loan A', 2000, 0, 999999, 'loan','20240103','simple',0.05,'daily',20,None,1000,1000)
    #
    #
    #     B = BudgetSet.BudgetSet([])
    #     B.addBudgetItem(start_date_YYYYMMDD,end_date_YYYYMMDD,1,'daily',30,'SPEND food',False,False)
    #     B.addBudgetItem('20240114', '20240114', 2, 'once', 2000, 'big purchase 1', False, False)
    #     B.addBudgetItem('20240114', '20240114', 3, 'once', 2000, 'big purchase 2', False, False)
    #
    #     M = MemoRuleSet.MemoRuleSet([])
    #     M.addMemoRule('.*income.*', None, 'Checking', 1)
    #     M.addMemoRule('SPEND.*','Checking',None,1)
    #     M.addMemoRule('.*', 'Checking', None, 2)
    #     M.addMemoRule('.*', 'Checking', None, 3)
    #
    #     A1 = AccountMilestone.AccountMilestone('Checking 1000','Checking',1000,1000)
    #     A2 = AccountMilestone.AccountMilestone('Credit 1000', 'Credit', 1000, 1000)
    #     A3 = AccountMilestone.AccountMilestone('Loan A', 'Credit', 1000, 1000)
    #
    #     M1 = MemoMilestone.MemoMilestone('big purchase 1','.*big purchase 1.*')
    #     M2 = MemoMilestone.MemoMilestone('big purchase 2', '.*big purchase 2.*')
    #
    #     CM1 = CompositeMilestone.CompositeMilestone('All 1k',[A1,A2,A3],[])
    #     CM2 = CompositeMilestone.CompositeMilestone('both purchases', [], [M1,M2])
    #     CM3 = CompositeMilestone.CompositeMilestone('All 1k and both purchases', [A1, A2, A3], [M1, M2])
    #
    #     MS = MilestoneSet.MilestoneSet(A,B,[A1,A2,A3],[M1,M2],[CM1,CM2,CM3])
    #
    #     E = ExpenseForecast.ExpenseForecast(A,
    #                                         B,
    #                                         M,
    #                                         start_date_YYYYMMDD,
    #                                         end_date_YYYYMMDD,
    #                                         MS)
    #     E.runForecast()
    #
    #     F = ForecastHandler.ForecastHandler()
    #
    #     F.generateHTMLReport(E)
    #
    # def tests_calculateMultipleChooseOne(self):
    #     raise NotImplementedError
    #
    # def test_plotAccountTypeComparison(self):
    #     raise NotImplementedError
    #
    # def test_plotNetWorthComparison(self):
    #     raise NotImplementedError
    #
    # def test_plotAllComparison(self):
    #     raise NotImplementedError
    #
    # def test_plotAccountTypeTotals(self):
    #     raise NotImplementedError
    #
    # def test_plotNetWorth(self):
    #     raise NotImplementedError
    #
    # def test_plotAll(self):
    #     raise NotImplementedError
    #
    # def test_plotMarginalInterest(self):
    #     raise NotImplementedError


# FORECAST HANDLER
#plot networth
#plot account type totals
#plot all
#plot marginal interest


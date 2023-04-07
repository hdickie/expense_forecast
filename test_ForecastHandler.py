import unittest
import ForecastHandler, AccountSet, BudgetSet, MemoRuleSet
import pandas as pd, numpy as np
import datetime, logging
pd.options.mode.chained_assignment = None #apparently this warning can throw false positives???

from log_methods import log_in_color

import copy

class TestForecastHandlerMethods(unittest.TestCase):

    def setUp(self):
        #print('Running setUp')
        self.account_set = AccountSet.AccountSet([])
        self.budget_set = BudgetSet.BudgetSet([])
        self.memo_rule_set = MemoRuleSet.MemoRuleSet([])
        self.start_date_YYYYMMDD = '20000101'
        self.end_date_YYYYMMDD = '20000103'

        self.og_dir = dir()

        #print('exiting setup')

    def tearDown(self):
        #print('Running tearDown')
        pass
        #print('exiting tearDown')

    def test_ForecastHandler_Constructor(self):
        raise NotImplementedError

    def test_calculateMultipleChooseOne(self):

        F = ForecastHandler.ForecastHandler()


        account_set = self.account_set
        memo_rule_set = self.memo_rule_set
        start_date_YYYYMMDD = '20000101'
        end_date_YYYYMMDD = '20000103'

        memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=1)

        account_set.addAccount(name='Checking',
                               balance=1000,
                               min_balance=0,
                               max_balance=float('Inf'),
                               account_type="checking")

        CoreBudgetSet = BudgetSet.BudgetSet([])
        CoreBudgetSet.addBudgetItem('20000102', '20000102', 1, 'once', '1', 'Core', deferrable=False, partial_payment_allowed=False)

        BudgetSetA2 = BudgetSet.BudgetSet([])
        BudgetSetA2.addBudgetItem('20000102', '20000102', 1, 'once', '1', 'A2', deferrable=False, partial_payment_allowed=False)

        BudgetSetB2 = BudgetSet.BudgetSet([])
        BudgetSetB2.addBudgetItem('20000102', '20000102', 1, 'once', '1', 'B2', deferrable=False, partial_payment_allowed=False)

        BudgetSetC3 = BudgetSet.BudgetSet([])
        BudgetSetC3.addBudgetItem('20000102', '20000102', 1, 'once', '1', 'C3', deferrable=False, partial_payment_allowed=False)

        BudgetSetD3 = BudgetSet.BudgetSet([])
        BudgetSetD3.addBudgetItem('20000102', '20000102', 1, 'once', '1', 'D3', deferrable=False, partial_payment_allowed=False)

        BudgetSetE3 = BudgetSet.BudgetSet([])
        BudgetSetE3.addBudgetItem('20000102', '20000102', 1, 'once', '1', 'E3', deferrable=False, partial_payment_allowed=False)

        BudgetSetF4 = BudgetSet.BudgetSet([])
        BudgetSetF4.addBudgetItem('20000102', '20000102', 1, 'once', '1', 'F4', deferrable=False, partial_payment_allowed=False)

        list_of_lists_of_budget_sets = [
            [BudgetSetA2, BudgetSetB2],
            [BudgetSetC3, BudgetSetD3, BudgetSetE3],
            [BudgetSetF4]
        ]

        F.calculateMultipleChooseOne(AccountSet=copy.deepcopy(account_set),
                                     Core_BudgetSet=CoreBudgetSet,
                                     MemoRuleSet=memo_rule_set,
                                     start_date_YYYYMMDD=start_date_YYYYMMDD,
                                     end_date_YYYYMMDD=end_date_YYYYMMDD,
                                     list_of_lists_of_budget_sets=list_of_lists_of_budget_sets)
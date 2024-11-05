import logging
import cProfile

import datetime

import BudgetSet, ExpenseForecast, AccountSet, datetime, pandas as pd, MemoRuleSet, copy
pd.options.mode.chained_assignment = None #apparently this warning can throw false positives???

from log_methods import log_in_color

if __name__ == '__main__':
    account_set = AccountSet.AccountSet([])
    budget_set = BudgetSet.BudgetSet([])
    memo_rule_set = MemoRuleSet.MemoRuleSet([])

    start_date_YYYYMMDD = '20230331'
    end_date_YYYYMMDD = '20231231'

    current_checking_balance = 4224.62
    current_credit_previous_statement_balance = 7351.2
    current_credit_current_statement_balance = 430.27

    #same memo rules for each
    memo_rule_set.addMemoRule(memo_regex='.*income.*', account_from=None, account_to='Checking', transaction_priority=1)

    memo_rule_set.addMemoRule(memo_regex='food', account_from='Credit', account_to=None, transaction_priority=1)
    memo_rule_set.addMemoRule(memo_regex='internet', account_from='Credit', account_to=None, transaction_priority=1)
    memo_rule_set.addMemoRule(memo_regex='phone bill', account_from='Credit', account_to=None, transaction_priority=1)
    memo_rule_set.addMemoRule(memo_regex='car insurance', account_from='Credit', account_to=None, transaction_priority=1)
    memo_rule_set.addMemoRule(memo_regex='health insurance', account_from='Credit', account_to=None, transaction_priority=1)
    memo_rule_set.addMemoRule(memo_regex='gas and bus', account_from='Credit', account_to=None, transaction_priority=1)
    memo_rule_set.addMemoRule(memo_regex='spotify', account_from='Credit', account_to=None, transaction_priority=1)
    memo_rule_set.addMemoRule(memo_regex='gym', account_from='Credit', account_to=None, transaction_priority=1)
    memo_rule_set.addMemoRule(memo_regex='hbo max', account_from='Credit', account_to=None, transaction_priority=1)
    memo_rule_set.addMemoRule(memo_regex='hulu', account_from='Credit', account_to=None, transaction_priority=1)
    memo_rule_set.addMemoRule(memo_regex='.*rent.*', account_from='Checking', account_to=None, transaction_priority=1)
    memo_rule_set.addMemoRule(memo_regex='.*utilities.*', account_from='Checking', account_to=None, transaction_priority=1)

    memo_rule_set.addMemoRule(memo_regex='.*additional cc payment.*', account_from='Checking', account_to='Credit', transaction_priority=1)

    memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=2)
    memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=3)
    memo_rule_set.addMemoRule(memo_regex='.*', account_from='Checking', account_to=None, transaction_priority=4)
    memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=5)
    memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=6)
    memo_rule_set.addMemoRule(memo_regex='.*', account_from='Credit', account_to=None, transaction_priority=7)

    memo_rule_set.addMemoRule(memo_regex='EMT class', account_from='Credit', account_to=None, transaction_priority=1)

    account_set.createAccount(name='Checking',
                              balance=current_checking_balance,
                              min_balance=0,
                              max_balance=float('Inf'),
                              account_type="checking")

    account_set.createAccount(name='Credit',
                              balance=current_credit_current_statement_balance,
                              min_balance=0,
                              max_balance=20000,
                              account_type="credit",
                              billing_start_date_YYYYMMDD='20230103',
                              interest_type='Compound',
                              apr=0.2824,
                              interest_cadence='Monthly',
                              minimum_payment=40,
                              previous_statement_balance=current_credit_previous_statement_balance,
                              principal_balance=None,
                              accrued_interest=None
                              )

    account_set.createAccount(name='Loan A',
                              balance=4746.18,
                              min_balance=0,
                              max_balance=float("inf"),
                              account_type="loan",
                              billing_start_date_YYYYMMDD='20230903',
                              interest_type='simple',
                              apr=0.0466,
                              interest_cadence='daily',
                              minimum_payment=50,
                              previous_statement_balance=None,
                              principal_balance=4746.18,
                              accrued_interest=0
                              )

    account_set.createAccount(name='Loan B',
                              balance=1919.55,
                              min_balance=0,
                              max_balance=float("inf"),
                              account_type="loan",
                              billing_start_date_YYYYMMDD='20230903',
                              interest_type='simple',
                              apr=0.0429,
                              interest_cadence='daily',
                              minimum_payment=50,
                              previous_statement_balance=None,
                              principal_balance=1919.55,
                              accrued_interest=0
                              )

    account_set.createAccount(name='Loan C',
                              balance=4726.68,
                              min_balance=0,
                              max_balance=float("inf"),
                              account_type="loan",
                              billing_start_date_YYYYMMDD='20230903',
                              interest_type='simple',
                              apr=0.0429,
                              interest_cadence='daily',
                              minimum_payment=50,
                              previous_statement_balance=None,
                              principal_balance=4726.68,
                              accrued_interest=0
                              )

    account_set.createAccount(name='Loan D',
                              balance=1823.31,
                              min_balance=0,
                              max_balance=float("inf"),
                              account_type="loan",
                              billing_start_date_YYYYMMDD='20230903',
                              interest_type='simple',
                              apr=0.0376,
                              interest_cadence='daily',
                              minimum_payment=50,
                              previous_statement_balance=None,
                              principal_balance=1823.31,
                              accrued_interest=0
                              )

    account_set.createAccount(name='Loan E',
                              balance=3359.17,
                              min_balance=0,
                              max_balance=float("inf"),
                              account_type="loan",
                              billing_start_date_YYYYMMDD='20230903',
                              interest_type='simple',
                              apr=0.0376,
                              interest_cadence='daily',
                              minimum_payment=50,
                              previous_statement_balance=None,
                              principal_balance=3359.17,
                              accrued_interest=0
                              )

    account_set.createAccount(name='Tax Debt',
                              balance=8000,
                              min_balance=0,
                              max_balance=float("inf"),
                              account_type="loan",
                              billing_start_date_YYYYMMDD='20231015',
                              interest_type='simple',
                              apr=0.06,
                              interest_cadence='daily',
                              minimum_payment=0,
                              previous_statement_balance=None,
                              principal_balance=8000,
                              accrued_interest=0
                              )


    # budget_set.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20241231', priority=4,
    #                          cadence='monthly', amount=20000, memo='additional cc payment',
    #                          deferrable=False,
    #                          partial_payment_allowed=True)

    # budget_set.addBudgetItem(start_date_YYYYMMDD='20230102', end_date_YYYYMMDD='20230731', priority=4,
    #                          cadence='monthly', amount=3611.5, memo='cyclical billing total',
    #                          deferrable=False,
    #                          partial_payment_allowed=False)

    # 1000 + 1918 + 89 + 163 + 100 + 8 + 15 + 33 + 10 + 100 + 175.5 = 3611.5 + 300 ; cyclical billing total

    #these are in all of them
    budget_set.addBudgetItem(start_date_YYYYMMDD=start_date_YYYYMMDD, end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                             cadence='daily', amount=30, memo='food',
                             deferrable=False,
                             partial_payment_allowed=False)

    budget_set.addBudgetItem(start_date_YYYYMMDD='20230217', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                             cadence='monthly', amount=89, memo='car insurance',
                             deferrable=False,
                             partial_payment_allowed=False)

    budget_set.addBudgetItem(start_date_YYYYMMDD='20230331', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                             cadence='monthly', amount=163.09, memo='phone bill',
                             deferrable=False,
                             partial_payment_allowed=False)

    budget_set.addBudgetItem(start_date_YYYYMMDD='20230219', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                             cadence='monthly', amount=8, memo='hulu',
                             deferrable=False,
                             partial_payment_allowed=False)

    budget_set.addBudgetItem(start_date_YYYYMMDD='20230219', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                             cadence='monthly', amount=15, memo='hbo max',
                             deferrable=False,
                             partial_payment_allowed=False)

    budget_set.addBudgetItem(start_date_YYYYMMDD='20230307', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                             cadence='monthly', amount=33, memo='gym',
                             deferrable=False,
                             partial_payment_allowed=False)

    budget_set.addBudgetItem(start_date_YYYYMMDD='20230407', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                             cadence='monthly', amount=10, memo='spotify',
                             deferrable=False,
                             partial_payment_allowed=False)

    budget_set.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                             cadence='monthly', amount=100, memo='gas and bus',
                             deferrable=False,
                             partial_payment_allowed=False)

    budget_set.addBudgetItem(start_date_YYYYMMDD='20230221', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                             cadence='monthly', amount=175.50, memo='health insurance',
                             deferrable=False,
                             partial_payment_allowed=False)




    ### these arent in all of them
    # budget_set.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230615', priority=1,
    #                          cadence='weekly', amount=450, memo='unemployment income',
    #                          deferrable=False,
    #                          partial_payment_allowed=False)
    #
    # budget_set.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230630', priority=1,
    #                          cadence='monthly', amount=1918, memo='rent (june last month at current place)',
    #                          deferrable=False,
    #                          partial_payment_allowed=False)
    #
    # budget_set.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230731', priority=1,
    #                          cadence='monthly', amount=100, memo='internet',
    #                          deferrable=False,
    #                          partial_payment_allowed=False)
    #
    # budget_set.addBudgetItem(start_date_YYYYMMDD='20230427', end_date_YYYYMMDD='20230427', priority=1,
    #                          cadence='once', amount=2900, memo='EMT class',
    #                          deferrable=False,
    #                          partial_payment_allowed=False)
    #
    # budget_set.addBudgetItem(start_date_YYYYMMDD='20230628', end_date_YYYYMMDD='20231215', priority=1,
    #                          cadence='semiweekly', amount=1320, memo='EMT income (work for 6 months)',
    #                          deferrable=False,
    #                          partial_payment_allowed=False)
    #
    # budget_set.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20240228', priority=1,
    #                          cadence='monthly', amount=800, memo='rent (santa cruz 8 months)',
    #                          deferrable=False,
    #                          partial_payment_allowed=False)
    #
    # budget_set.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230731', priority=1,
    #                          cadence='monthly', amount=300, memo='utilities',
    #                          deferrable=False,
    #                          partial_payment_allowed=False)
    #
    #
    # budget_set.addBudgetItem(start_date_YYYYMMDD='20240301', end_date_YYYYMMDD='20241231', priority=1,
    #                          cadence='monthly', amount=3000, memo='income (new tech job at 130k march 2024)',
    #                          deferrable=False,
    #                          partial_payment_allowed=False)
    #
    # budget_set.addBudgetItem(start_date_YYYYMMDD='20240401', end_date_YYYYMMDD='20241231', priority=1,
    #                          cadence='monthly', amount=1200, memo='rent (w james and panda)',
    #                          deferrable=False,
    #                          partial_payment_allowed=False)
    #
    # budget_set.addBudgetItem(start_date_YYYYMMDD='20240401', end_date_YYYYMMDD='20241231', priority=1,
    #                          cadence='monthly', amount=150, memo='utilities (w james and panda)',
    #                          deferrable=False,
    #                          partial_payment_allowed=False)

    budget_set_1 = copy.deepcopy(budget_set)
    budget_set_2 = copy.deepcopy(budget_set)
    budget_set_3 = copy.deepcopy(budget_set)
    budget_set_4 = copy.deepcopy(budget_set)
    budget_set_5 = copy.deepcopy(budget_set)
    budget_set_6 = copy.deepcopy(budget_set)
    budget_set_7 = copy.deepcopy(budget_set)
    budget_set_8 = copy.deepcopy(budget_set)
    budget_set_9 = copy.deepcopy(budget_set)
    budget_set_10 = copy.deepcopy(budget_set)
    budget_set_11 = copy.deepcopy(budget_set)
    budget_set_12 = copy.deepcopy(budget_set)
    budget_set_13 = copy.deepcopy(budget_set)
    budget_set_14 = copy.deepcopy(budget_set)
    budget_set_15 = copy.deepcopy(budget_set)
    budget_set_16 = copy.deepcopy(budget_set)
    budget_set_17 = copy.deepcopy(budget_set)
    budget_set_18 = copy.deepcopy(budget_set)
    budget_set_19 = copy.deepcopy(budget_set)
    budget_set_20 = copy.deepcopy(budget_set)
    budget_set_21 = copy.deepcopy(budget_set)
    budget_set_22 = copy.deepcopy(budget_set)
    budget_set_23 = copy.deepcopy(budget_set)
    budget_set_24 = copy.deepcopy(budget_set)
    budget_set_25 = copy.deepcopy(budget_set)
    budget_set_26 = copy.deepcopy(budget_set)
    budget_set_27 = copy.deepcopy(budget_set)
    budget_set_28 = copy.deepcopy(budget_set)
    budget_set_29 = copy.deepcopy(budget_set)
    budget_set_30 = copy.deepcopy(budget_set)
    budget_set_31 = copy.deepcopy(budget_set)
    budget_set_32 = copy.deepcopy(budget_set)
    budget_set_33 = copy.deepcopy(budget_set)
    budget_set_34 = copy.deepcopy(budget_set)
    budget_set_35 = copy.deepcopy(budget_set)
    budget_set_36 = copy.deepcopy(budget_set)
    budget_set_37 = copy.deepcopy(budget_set)
    budget_set_38 = copy.deepcopy(budget_set)
    budget_set_39 = copy.deepcopy(budget_set)
    budget_set_40 = copy.deepcopy(budget_set)

    ###begin hard coding scenarios.

    # 1. move in w mom June 1, pay 800/mo, start working 62.5/hr tech job May 1
    budget_set_1.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230501', priority=1,
                             cadence='weekly', amount=450, memo='unemployment income',
                             deferrable=False,
                             partial_payment_allowed=False)

    budget_set_1.addBudgetItem(start_date_YYYYMMDD='20230515', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_1.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230531', priority=1,
                             cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                             deferrable=False,
                             partial_payment_allowed=False)

    budget_set_1.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230531', priority=1,
                             cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                             deferrable=False,
                             partial_payment_allowed=False)

    budget_set_1.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230531', priority=1,
                             cadence='monthly', amount=100, memo='internet',
                             deferrable=False,
                             partial_payment_allowed=False)

    budget_set_1.addBudgetItem(start_date_YYYYMMDD='20230601', end_date_YYYYMMDD='20231231', priority=1,
                             cadence='monthly', amount=800, memo='mom rent',
                             deferrable=False,
                             partial_payment_allowed=False)

    budget_set_1.addBudgetItem(start_date_YYYYMMDD='20230601', end_date_YYYYMMDD='20231231', priority=1,
                             cadence='monthly', amount=1000, memo='additional cc payment',
                             deferrable=False,
                             partial_payment_allowed=False)


    # 2. move in w mom June 1, pay 800/mo, start working 62.5/hr tech job June 1
    budget_set_2.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230601', priority=1,
                               cadence='weekly', amount=450, memo='unemployment income',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_2.addBudgetItem(start_date_YYYYMMDD='20230615', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_2.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230531', priority=1,
                               cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_2.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230531', priority=1,
                               cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_2.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230531', priority=1,
                               cadence='monthly', amount=100, memo='internet',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_2.addBudgetItem(start_date_YYYYMMDD='20230601', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=800, memo='mom rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_2.addBudgetItem(start_date_YYYYMMDD='20230601', end_date_YYYYMMDD='20231231', priority=1,
                             cadence='monthly', amount=1000, memo='additional cc payment',
                             deferrable=False,
                             partial_payment_allowed=False)


    # 3. move in w mom June 1, pay 800/mo, start working 62.5/hr tech job June 15
    budget_set_3.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230615', priority=1,
                               cadence='weekly', amount=450, memo='unemployment income',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_3.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_3.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230531', priority=1,
                               cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_3.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230531', priority=1,
                               cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_3.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230531', priority=1,
                               cadence='monthly', amount=100, memo='internet',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_3.addBudgetItem(start_date_YYYYMMDD='20230601', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=800, memo='mom rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_3.addBudgetItem(start_date_YYYYMMDD='20230601', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 4. move in w mom June 1, pay 800/mo, start working EMT job June 15, work there for 3 months, start 62.5/hr tech job Sep 15
    budget_set_4.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230615', priority=1,
                               cadence='weekly', amount=450, memo='unemployment income',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_4.addBudgetItem(start_date_YYYYMMDD='20230628', end_date_YYYYMMDD='20230928', priority=1,
                               cadence='semiweekly', amount=1320, memo='EMT income',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_4.addBudgetItem(start_date_YYYYMMDD='20231001', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_4.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230531', priority=1,
                               cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_4.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230531', priority=1,
                               cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_4.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230531', priority=1,
                               cadence='monthly', amount=100, memo='internet',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_4.addBudgetItem(start_date_YYYYMMDD='20230601', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=800, memo='mom rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_4.addBudgetItem(start_date_YYYYMMDD='20230427', end_date_YYYYMMDD='20230427', priority=1,
                             cadence='once', amount=2900, memo='EMT class',
                             deferrable=False,
                             partial_payment_allowed=False)

    budget_set_4.addBudgetItem(start_date_YYYYMMDD='20230601', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)



    # 5. move in w mom June 1, pay 800/mo, start working EMT job June 15, work there for 6 months, start 62.5/hr tech job Dec 15
    budget_set_5.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230615', priority=1,
                               cadence='weekly', amount=450, memo='unemployment income',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_5.addBudgetItem(start_date_YYYYMMDD='20230628', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='semiweekly', amount=1320, memo='EMT income',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_5.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230531', priority=1,
                               cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_5.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230531', priority=1,
                               cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_5.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230531', priority=1,
                               cadence='monthly', amount=100, memo='internet',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_5.addBudgetItem(start_date_YYYYMMDD='20230601', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=800, memo='mom rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_5.addBudgetItem(start_date_YYYYMMDD='20230427', end_date_YYYYMMDD='20230427', priority=1,
                             cadence='once', amount=2900, memo='EMT class',
                             deferrable=False,
                             partial_payment_allowed=False)

    budget_set_5.addBudgetItem(start_date_YYYYMMDD='20230601', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 6. move in w mom June 1, pay 1000/mo, start working 62.5/hr tech job May 1
    budget_set_6.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230501', priority=1,
                               cadence='weekly', amount=450, memo='unemployment income',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_6.addBudgetItem(start_date_YYYYMMDD='20230515', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_6.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230531', priority=1,
                               cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_6.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230531', priority=1,
                               cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_6.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230531', priority=1,
                               cadence='monthly', amount=100, memo='internet',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_6.addBudgetItem(start_date_YYYYMMDD='20230601', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='mom rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_6.addBudgetItem(start_date_YYYYMMDD='20230601', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 7. move in w mom June 1, pay 1000/mo, start working 62.5/hr tech job June 1
    budget_set_7.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230601', priority=1,
                               cadence='weekly', amount=450, memo='unemployment income',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_7.addBudgetItem(start_date_YYYYMMDD='20230615', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_7.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230531', priority=1,
                               cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_7.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230531', priority=1,
                               cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_7.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230531', priority=1,
                               cadence='monthly', amount=100, memo='internet',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_7.addBudgetItem(start_date_YYYYMMDD='20230601', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='mom rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_7.addBudgetItem(start_date_YYYYMMDD='20230601', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 8. move in w mom June 1, pay 1000/mo, start working 62.5/hr tech job June 15
    budget_set_8.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230615', priority=1,
                               cadence='weekly', amount=450, memo='unemployment income',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_8.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_8.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230531', priority=1,
                               cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_8.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230531', priority=1,
                               cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_8.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230531', priority=1,
                               cadence='monthly', amount=100, memo='internet',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_8.addBudgetItem(start_date_YYYYMMDD='20230601', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='mom rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_8.addBudgetItem(start_date_YYYYMMDD='20230601', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 9. move in w mom June 1, pay 1000/mo, start working EMT job June 15, work there for 3 months, start 62.5/hr tech job Sep 15
    budget_set_9.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230615', priority=1,
                               cadence='weekly', amount=450, memo='unemployment income',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_9.addBudgetItem(start_date_YYYYMMDD='20230628', end_date_YYYYMMDD='20230928', priority=1,
                               cadence='semiweekly', amount=1320, memo='EMT income',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_9.addBudgetItem(start_date_YYYYMMDD='20231001', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_9.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230531', priority=1,
                               cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_9.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230531', priority=1,
                               cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_9.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230531', priority=1,
                               cadence='monthly', amount=100, memo='internet',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_9.addBudgetItem(start_date_YYYYMMDD='20230601', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='mom rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_9.addBudgetItem(start_date_YYYYMMDD='20230427', end_date_YYYYMMDD='20230427', priority=1,
                               cadence='once', amount=2900, memo='EMT class',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_9.addBudgetItem(start_date_YYYYMMDD='20230601', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 10. move in w mom June 1, pay 1000/mo, start working EMT job June 15, work there for 6 months, start 62.5/hr tech job Dec 15
    budget_set_10.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230615', priority=1,
                               cadence='weekly', amount=450, memo='unemployment income',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_10.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230531', priority=1,
                               cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_10.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230531', priority=1,
                               cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_10.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230531', priority=1,
                               cadence='monthly', amount=100, memo='internet',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_10.addBudgetItem(start_date_YYYYMMDD='20230601', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='mom rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_10.addBudgetItem(start_date_YYYYMMDD='20230427', end_date_YYYYMMDD='20230427', priority=1,
                               cadence='once', amount=2900, memo='EMT class',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_10.addBudgetItem(start_date_YYYYMMDD='20230628', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='semiweekly', amount=1320, memo='EMT income',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_10.addBudgetItem(start_date_YYYYMMDD='20230601', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 11. move in w mom July 1, pay 800/mo, start working 62.5/hr tech job May 1
    budget_set_11.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230601', priority=1,
                             cadence='weekly', amount=450, memo='unemployment income',
                             deferrable=False,
                             partial_payment_allowed=False)

    budget_set_11.addBudgetItem(start_date_YYYYMMDD='20230515', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_11.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230630', priority=1,
                             cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                             deferrable=False,
                             partial_payment_allowed=False)

    budget_set_11.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230630', priority=1,
                             cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                             deferrable=False,
                             partial_payment_allowed=False)

    budget_set_11.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230630', priority=1,
                             cadence='monthly', amount=100, memo='internet',
                             deferrable=False,
                             partial_payment_allowed=False)

    budget_set_11.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                             cadence='monthly', amount=800, memo='mom rent',
                             deferrable=False,
                             partial_payment_allowed=False)

    budget_set_11.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 12. move in w mom July 1, pay 800/mo, start working 62.5/hr tech job June 1
    budget_set_12.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230601', priority=1,
                               cadence='weekly', amount=450, memo='unemployment income',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_12.addBudgetItem(start_date_YYYYMMDD='20230615', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_12.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230630', priority=1,
                               cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_12.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230630', priority=1,
                               cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_12.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230630', priority=1,
                               cadence='monthly', amount=100, memo='internet',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_12.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=800, memo='mom rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_12.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 13. move in w mom July 1, pay 800/mo, start working 62.5/hr tech job June 15
    budget_set_13.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230615', priority=1,
                               cadence='weekly', amount=450, memo='unemployment income',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_13.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_13.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230630', priority=1,
                               cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_13.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230630', priority=1,
                               cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_13.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230630', priority=1,
                               cadence='monthly', amount=100, memo='internet',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_13.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=800, memo='mom rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_13.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 14. move in w mom July 1, pay 800/mo, start working EMT job June 15, work there for 3 months, start 62.5/hr tech job Sep 15
    budget_set_14.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230615', priority=1,
                               cadence='weekly', amount=450, memo='unemployment income',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_14.addBudgetItem(start_date_YYYYMMDD='20230628', end_date_YYYYMMDD='20230928', priority=1,
                                cadence='semiweekly', amount=1320, memo='EMT income',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_14.addBudgetItem(start_date_YYYYMMDD='20231001', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_14.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230630', priority=1,
                               cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_14.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230630', priority=1,
                               cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_14.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230630', priority=1,
                               cadence='monthly', amount=100, memo='internet',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_14.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=800, memo='mom rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_14.addBudgetItem(start_date_YYYYMMDD='20230427', end_date_YYYYMMDD='20230427', priority=1,
                             cadence='once', amount=2900, memo='EMT class',
                             deferrable=False,
                             partial_payment_allowed=False)

    budget_set_14.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 15. move in w mom July 1, pay 800/mo, start working EMT job June 15, work there for 6 months, start 62.5/hr tech job Dec 15
    budget_set_15.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230615', priority=1,
                               cadence='weekly', amount=450, memo='unemployment income',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_15.addBudgetItem(start_date_YYYYMMDD='20230628', end_date_YYYYMMDD='20231231', priority=1,
                                cadence='semiweekly', amount=1320, memo='EMT income',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_15.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230630', priority=1,
                               cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_15.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230630', priority=1,
                               cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_15.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230630', priority=1,
                               cadence='monthly', amount=100, memo='internet',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_15.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=800, memo='mom rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_15.addBudgetItem(start_date_YYYYMMDD='20230427', end_date_YYYYMMDD='20230427', priority=1,
                             cadence='once', amount=2900, memo='EMT class',
                             deferrable=False,
                             partial_payment_allowed=False)

    budget_set_15.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 16. move in w mom July 1, pay 1000/mo, start working 62.5/hr tech job May 1
    budget_set_16.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230501', priority=1,
                               cadence='weekly', amount=450, memo='unemployment income',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_16.addBudgetItem(start_date_YYYYMMDD='20230515', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_16.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230630', priority=1,
                               cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_16.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230630', priority=1,
                               cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_16.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230630', priority=1,
                               cadence='monthly', amount=100, memo='internet',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_16.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='mom rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_16.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 17. move in w mom July 1, pay 1000/mo, start working 62.5/hr tech job June 1
    budget_set_17.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230601', priority=1,
                               cadence='weekly', amount=450, memo='unemployment income',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_17.addBudgetItem(start_date_YYYYMMDD='20230615', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_17.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230630', priority=1,
                               cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_17.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230630', priority=1,
                               cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_17.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230630', priority=1,
                               cadence='monthly', amount=100, memo='internet',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_17.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='mom rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_17.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 18. move in w mom July 1, pay 1000/mo, start working 62.5/hr tech job June 15
    budget_set_18.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230615', priority=1,
                               cadence='weekly', amount=450, memo='unemployment income',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_18.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_18.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230630', priority=1,
                               cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_18.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230630', priority=1,
                               cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_18.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230630', priority=1,
                               cadence='monthly', amount=100, memo='internet',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_18.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='mom rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_18.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 19. move in w mom July 1, pay 1000/mo, start working EMT job June 15, work there for 3 months, start 62.5/hr tech job Sep 15
    budget_set_19.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230615', priority=1,
                               cadence='weekly', amount=450, memo='unemployment income',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_19.addBudgetItem(start_date_YYYYMMDD='20230628', end_date_YYYYMMDD='20230928', priority=1,
                                cadence='semiweekly', amount=1320, memo='EMT income',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_19.addBudgetItem(start_date_YYYYMMDD='20231001', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_19.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230630', priority=1,
                               cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_19.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230630', priority=1,
                               cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_19.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230630', priority=1,
                               cadence='monthly', amount=100, memo='internet',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_19.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='mom rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_19.addBudgetItem(start_date_YYYYMMDD='20230427', end_date_YYYYMMDD='20230427', priority=1,
                               cadence='once', amount=2900, memo='EMT class',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_19.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 20. move in w mom July 1, pay 1000/mo, start working EMT job June 15, work there for 6 months, start 62.5/hr tech job Dec 15
    budget_set_20.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230615', priority=1,
                               cadence='weekly', amount=450, memo='unemployment income',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_20.addBudgetItem(start_date_YYYYMMDD='20230628', end_date_YYYYMMDD='20231231', priority=1,
                                cadence='semiweekly', amount=1320, memo='EMT income',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_20.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230630', priority=1,
                               cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_20.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230630', priority=1,
                               cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_20.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230630', priority=1,
                               cadence='monthly', amount=100, memo='internet',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_20.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='mom rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_20.addBudgetItem(start_date_YYYYMMDD='20230427', end_date_YYYYMMDD='20230427', priority=1,
                               cadence='once', amount=2900, memo='EMT class',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_20.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 21. move in w J+P July 1, pay 1500/mo, start working 62.5/hr tech job May 1
    budget_set_21.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230501', priority=1,
                                cadence='weekly', amount=450, memo='unemployment income',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_21.addBudgetItem(start_date_YYYYMMDD='20230515', end_date_YYYYMMDD='20231231', priority=1,
                                cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_21.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230630', priority=1,
                                cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_21.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230630', priority=1,
                                cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_21.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230630', priority=1,
                                cadence='monthly', amount=100, memo='internet',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_21.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                                cadence='monthly', amount=1500, memo='J+P rent',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_21.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 22. move in w J+P July 1, pay 1500/mo, start working 62.5/hr tech job June 1
    budget_set_22.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230601', priority=1,
                                cadence='weekly', amount=450, memo='unemployment income',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_22.addBudgetItem(start_date_YYYYMMDD='20230615', end_date_YYYYMMDD='20231231', priority=1,
                                cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_22.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230630', priority=1,
                                cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_22.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230630', priority=1,
                                cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_22.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230630', priority=1,
                                cadence='monthly', amount=100, memo='internet',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_22.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                                cadence='monthly', amount=1500, memo='J+P rent',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_22.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 23. move in w J+P July 1, pay 1500/mo, start working 62.5/hr tech job June 15
    budget_set_23.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230615', priority=1,
                                cadence='weekly', amount=450, memo='unemployment income',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_23.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                                cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_23.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230630', priority=1,
                                cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_23.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230630', priority=1,
                                cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_23.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230630', priority=1,
                                cadence='monthly', amount=100, memo='internet',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_23.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                                cadence='monthly', amount=1500, memo='J+P rent',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_23.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 24. move in w J+P July 1, pay 1500/mo, start working EMT job June 15, work there for 3 months, start 62.5/hr tech job Sep 15
    budget_set_24.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230615', priority=1,
                                cadence='weekly', amount=450, memo='unemployment income',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_24.addBudgetItem(start_date_YYYYMMDD='20230628', end_date_YYYYMMDD='20230930', priority=1,
                                cadence='semiweekly', amount=1320, memo='EMT income',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_24.addBudgetItem(start_date_YYYYMMDD='20231001', end_date_YYYYMMDD='20231231', priority=1,
                                cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_24.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230630', priority=1,
                                cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_24.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230630', priority=1,
                                cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_24.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230630', priority=1,
                                cadence='monthly', amount=100, memo='internet',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_24.addBudgetItem(start_date_YYYYMMDD='20230427', end_date_YYYYMMDD='20230427', priority=1,
                                cadence='once', amount=2900, memo='EMT class',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_24.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                                cadence='monthly', amount=1500, memo='J+P rent',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_24.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 25. move in w J+P July 1, pay 1500/mo, start working EMT job June 15, work there for 6 months, start 62.5/hr tech job Dec 15
    budget_set_25.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230615', priority=1,
                                cadence='weekly', amount=450, memo='unemployment income',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_25.addBudgetItem(start_date_YYYYMMDD='20230715', end_date_YYYYMMDD='20231231', priority=1,
                                cadence='semiweekly', amount=1320, memo='EMT income',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_25.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230630', priority=1,
                                cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_25.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230630', priority=1,
                                cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_25.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230630', priority=1,
                                cadence='monthly', amount=100, memo='internet',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_25.addBudgetItem(start_date_YYYYMMDD='20230427', end_date_YYYYMMDD='20230427', priority=1,
                                cadence='once', amount=2900, memo='EMT class',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_25.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                                cadence='monthly', amount=1500, memo='J+P rent',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_25.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 26. move in w mom August 1, pay 800/mo, start working 62.5/hr tech job May 1
    budget_set_26.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230501', priority=1,
                               cadence='weekly', amount=450, memo='unemployment income',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_26.addBudgetItem(start_date_YYYYMMDD='20230515', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_26.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230731', priority=1,
                               cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_26.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230731', priority=1,
                               cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_26.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230731', priority=1,
                               cadence='monthly', amount=100, memo='internet',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_26.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=800, memo='mom rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_26.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 27. move in w mom August 1, pay 800/mo, start working 62.5/hr tech job June 1
    budget_set_27.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230601', priority=1,
                               cadence='weekly', amount=450, memo='unemployment income',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_27.addBudgetItem(start_date_YYYYMMDD='20230615', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_27.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230731', priority=1,
                               cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_27.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230731', priority=1,
                               cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_27.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230731', priority=1,
                               cadence='monthly', amount=100, memo='internet',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_27.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=800, memo='mom rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_27.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 28. move in w mom August 1, pay 800/mo, start working 62.5/hr tech job June 15
    budget_set_28.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230615', priority=1,
                               cadence='weekly', amount=450, memo='unemployment income',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_28.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_28.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230731', priority=1,
                               cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_28.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230731', priority=1,
                               cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_28.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230731', priority=1,
                               cadence='monthly', amount=100, memo='internet',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_28.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=800, memo='mom rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_28.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 29. move in w mom August 1, pay 800/mo, start working EMT job June 15, work there for 3 months, start 62.5/hr tech job Sep 15
    budget_set_29.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230615', priority=1,
                               cadence='weekly', amount=450, memo='unemployment income',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_29.addBudgetItem(start_date_YYYYMMDD='20230628', end_date_YYYYMMDD='20230928', priority=1,
                                cadence='semiweekly', amount=1320, memo='EMT income',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_29.addBudgetItem(start_date_YYYYMMDD='20231001', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_29.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230731', priority=1,
                               cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_29.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230731', priority=1,
                               cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_29.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230731', priority=1,
                               cadence='monthly', amount=100, memo='internet',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_29.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=800, memo='mom rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_29.addBudgetItem(start_date_YYYYMMDD='20230427', end_date_YYYYMMDD='20230427', priority=1,
                               cadence='once', amount=2900, memo='EMT class',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_29.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 30. move in w mom August 1, pay 800/mo, start working EMT job June 15, work there for 6 months, start 62.5/hr tech job Dec 15
    budget_set_30.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230615', priority=1,
                               cadence='weekly', amount=450, memo='unemployment income',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_30.addBudgetItem(start_date_YYYYMMDD='20230628', end_date_YYYYMMDD='20231231', priority=1,
                                cadence='semiweekly', amount=1320, memo='EMT income',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_30.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230731', priority=1,
                               cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_30.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230731', priority=1,
                               cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_30.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230731', priority=1,
                               cadence='monthly', amount=100, memo='internet',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_30.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=800, memo='mom rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_30.addBudgetItem(start_date_YYYYMMDD='20230427', end_date_YYYYMMDD='20230427', priority=1,
                               cadence='once', amount=2900, memo='EMT class',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_30.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 31. move in w mom August 1, pay 1000/mo, start working 62.5/hr tech job May 1
    budget_set_31.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230501', priority=1,
                               cadence='weekly', amount=450, memo='unemployment income',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_31.addBudgetItem(start_date_YYYYMMDD='20230515', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_31.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230731', priority=1,
                               cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_31.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230731', priority=1,
                               cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_31.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230731', priority=1,
                               cadence='monthly', amount=100, memo='internet',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_31.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='mom rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_31.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 32. move in w mom August 1, pay 1000/mo, start working 62.5/hr tech job June 1
    budget_set_32.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230601', priority=1,
                               cadence='weekly', amount=450, memo='unemployment income',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_32.addBudgetItem(start_date_YYYYMMDD='20230615', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_32.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230731', priority=1,
                               cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_32.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230731', priority=1,
                               cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_32.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230731', priority=1,
                               cadence='monthly', amount=100, memo='internet',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_32.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='mom rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_32.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 33. move in w mom August 1, pay 1000/mo, start working 62.5/hr tech job June 15
    budget_set_33.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230615', priority=1,
                               cadence='weekly', amount=450, memo='unemployment income',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_33.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_33.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230731', priority=1,
                               cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_33.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230731', priority=1,
                               cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_33.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230731', priority=1,
                               cadence='monthly', amount=100, memo='internet',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_33.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='mom rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_33.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 34. move in w mom August 1, pay 1000/mo, start working EMT job June 15, work there for 3 months, start 62.5/hr tech job Sep 15
    budget_set_34.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230615', priority=1,
                               cadence='weekly', amount=450, memo='unemployment income',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_34.addBudgetItem(start_date_YYYYMMDD='20230628', end_date_YYYYMMDD='20230928', priority=1,
                                cadence='semiweekly', amount=1320, memo='EMT income',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_34.addBudgetItem(start_date_YYYYMMDD='20231001', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_34.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230731', priority=1,
                               cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_34.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230731', priority=1,
                               cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_34.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230731', priority=1,
                               cadence='monthly', amount=100, memo='internet',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_34.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=800, memo='mom rent',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_34.addBudgetItem(start_date_YYYYMMDD='20230427', end_date_YYYYMMDD='20230427', priority=1,
                               cadence='once', amount=2900, memo='EMT class',
                               deferrable=False,
                               partial_payment_allowed=False)

    budget_set_34.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 35. move in w mom August 1, pay 1000/mo, start working EMT job June 15, work there for 6 months, start 62.5/hr tech job Dec 15
    budget_set_35.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230615', priority=1,
                                cadence='weekly', amount=450, memo='unemployment income',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_35.addBudgetItem(start_date_YYYYMMDD='20230628', end_date_YYYYMMDD='20231231', priority=1,
                                cadence='semiweekly', amount=1320, memo='EMT income',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_35.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230731', priority=1,
                                cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_35.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230731', priority=1,
                                cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_35.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230731', priority=1,
                                cadence='monthly', amount=100, memo='internet',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_35.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                                cadence='monthly', amount=1000, memo='mom rent',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_35.addBudgetItem(start_date_YYYYMMDD='20230427', end_date_YYYYMMDD='20230427', priority=1,
                                cadence='once', amount=2900, memo='EMT class',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_35.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 36. move in w J+P August 1, pay 1500/mo, start working 62.5/hr tech job May 1
    budget_set_36.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230501', priority=1,
                                cadence='weekly', amount=450, memo='unemployment income',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_36.addBudgetItem(start_date_YYYYMMDD='20230515', end_date_YYYYMMDD='20231231', priority=1,
                                cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_36.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230731', priority=1,
                                cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_36.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230731', priority=1,
                                cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_36.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230731', priority=1,
                                cadence='monthly', amount=100, memo='internet',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_36.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                                cadence='monthly', amount=1500, memo='J+P rent',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_36.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 37. move in w J+P August 1, pay 1500/mo, start working 62.5/hr tech job June 1
    budget_set_37.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230601', priority=1,
                                cadence='weekly', amount=450, memo='unemployment income',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_37.addBudgetItem(start_date_YYYYMMDD='20230615', end_date_YYYYMMDD='20231231', priority=1,
                                cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_37.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230731', priority=1,
                                cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_37.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230731', priority=1,
                                cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_37.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230731', priority=1,
                                cadence='monthly', amount=100, memo='internet',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_37.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                                cadence='monthly', amount=1500, memo='J+P rent',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_37.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 38. move in w J+P August 1, pay 1500/mo, start working 62.5/hr tech job June 15
    budget_set_38.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230615', priority=1,
                                cadence='weekly', amount=450, memo='unemployment income',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_38.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                                cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_38.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230731', priority=1,
                                cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_38.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230731', priority=1,
                                cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_38.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230731', priority=1,
                                cadence='monthly', amount=100, memo='internet',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_38.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                                cadence='monthly', amount=1500, memo='J+P rent',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_38.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 39. move in w J+P August 1, pay 1500/mo, start working EMT job June 15, work there for 3 months, start 62.5/hr tech job Sep 15
    budget_set_39.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230615', priority=1,
                                cadence='weekly', amount=450, memo='unemployment income',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_39.addBudgetItem(start_date_YYYYMMDD='20230628', end_date_YYYYMMDD='20230928', priority=1,
                                cadence='semiweekly', amount=1320, memo='EMT income',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_39.addBudgetItem(start_date_YYYYMMDD='20231001', end_date_YYYYMMDD='20231231', priority=1,
                                cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_39.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230731', priority=1,
                                cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_39.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230731', priority=1,
                                cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_39.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230731', priority=1,
                                cadence='monthly', amount=100, memo='internet',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_39.addBudgetItem(start_date_YYYYMMDD='20230427', end_date_YYYYMMDD='20230427', priority=1,
                                cadence='once', amount=2900, memo='EMT class',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_39.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                                cadence='monthly', amount=1500, memo='J+P rent',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_39.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    # 40. move in w J+P August 1, pay 1500/mo, start working EMT job June 15, work there for 6 months, start 62.5/hr tech job Dec 15
    budget_set_40.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230615', priority=1,
                                cadence='weekly', amount=450, memo='unemployment income',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_40.addBudgetItem(start_date_YYYYMMDD='20230628', end_date_YYYYMMDD='20231231', priority=1,
                                cadence='semiweekly', amount=1320, memo='EMT income',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_40.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230731', priority=1,
                                cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_40.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230731', priority=1,
                                cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_40.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230731', priority=1,
                                cadence='monthly', amount=100, memo='internet',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_40.addBudgetItem(start_date_YYYYMMDD='20230427', end_date_YYYYMMDD='20230427', priority=1,
                                cadence='once', amount=2900, memo='EMT class',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_40.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                                cadence='monthly', amount=1500, memo='J+P rent',
                                deferrable=False,
                                partial_payment_allowed=False)

    budget_set_40.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    scenario_budget_sets = []
    scenario_budget_sets.append(budget_set_1)
    scenario_budget_sets.append(budget_set_2)
    scenario_budget_sets.append(budget_set_3)
    scenario_budget_sets.append(budget_set_4)
    scenario_budget_sets.append(budget_set_5)
    scenario_budget_sets.append(budget_set_6)
    scenario_budget_sets.append(budget_set_7)
    scenario_budget_sets.append(budget_set_8)
    scenario_budget_sets.append(budget_set_9)
    scenario_budget_sets.append(budget_set_10)
    scenario_budget_sets.append(budget_set_11)
    scenario_budget_sets.append(budget_set_12)
    scenario_budget_sets.append(budget_set_13)
    scenario_budget_sets.append(budget_set_14)
    scenario_budget_sets.append(budget_set_15)
    scenario_budget_sets.append(budget_set_16)
    scenario_budget_sets.append(budget_set_17)
    scenario_budget_sets.append(budget_set_18)
    scenario_budget_sets.append(budget_set_19)
    scenario_budget_sets.append(budget_set_20)
    scenario_budget_sets.append(budget_set_21)
    scenario_budget_sets.append(budget_set_22)
    scenario_budget_sets.append(budget_set_23)
    scenario_budget_sets.append(budget_set_24)
    scenario_budget_sets.append(budget_set_25)
    scenario_budget_sets.append(budget_set_26)
    scenario_budget_sets.append(budget_set_27)
    scenario_budget_sets.append(budget_set_28)
    scenario_budget_sets.append(budget_set_29)
    scenario_budget_sets.append(budget_set_30)
    scenario_budget_sets.append(budget_set_31)
    scenario_budget_sets.append(budget_set_32)
    scenario_budget_sets.append(budget_set_33)
    scenario_budget_sets.append(budget_set_34)
    scenario_budget_sets.append(budget_set_35)
    scenario_budget_sets.append(budget_set_36)
    scenario_budget_sets.append(budget_set_37)
    scenario_budget_sets.append(budget_set_38)
    scenario_budget_sets.append(budget_set_39)
    scenario_budget_sets.append(budget_set_40)

    scenario_index = 7

    print('Starting sim')
    E = ExpenseForecast.ExpenseForecast(copy.deepcopy(account_set),
                                            scenario_budget_sets[scenario_index],
                                            memo_rule_set,
                                            start_date_YYYYMMDD,
                                            end_date_YYYYMMDD)

    E.forecast_df.to_csv('C:/Users/HumeD/PycharmProjects/expense_forecast/Fail_Test.csv')

    # program_start = datetime.datetime.now()
    # scenario_index = 0
    # for b in scenario_budget_sets:
    #
    #     if scenario_index != 7:
    #         scenario_index += 1
    #         continue
    #
    #     try:
    #         loop_start = datetime.datetime.now()
    #         print('Simulating scenario '+str(scenario_index))
    #         E = ExpenseForecast.ExpenseForecast(copy.deepcopy(account_set),
    #                                         scenario_budget_sets[scenario_index],
    #                                         memo_rule_set,
    #                                         start_date_YYYYMMDD,
    #                                         end_date_YYYYMMDD)
    #
    #         E.forecast_df.to_csv('./Forecast__Scenario_'+str(scenario_index)+'.csv')
    #
    #         E.plotOverall('./Scenario_'+str(scenario_index)+'.png')
    #
    #         loop_finish = datetime.datetime.now()
    #
    #         loop_delta = loop_finish - loop_start
    #         time_since_started = loop_finish - program_start
    #
    #         average_time_per_loop = time_since_started.seconds / (scenario_index + 1)
    #         loops_remaining = len(scenario_budget_sets) - (scenario_index + 1)
    #         ETC = loop_finish + datetime.timedelta(seconds=average_time_per_loop*loops_remaining)
    #         progress_string = 'Finished. ETC: '+str(ETC.strftime('%Y-%m-%d %H:%M:%S'))
    #
    #         print(progress_string)
    #
    #     except Exception as e:
    #         print('Failed during forcast #'+str(scenario_index))
    #
    #     scenario_index += 1

    #cProfile.run('re.compile("foo|bar")')

    # cProfile.run("""E = ExpenseForecast.ExpenseForecast(account_set,
    #                                     budget_set,
    #                                     memo_rule_set,
    #                                     start_date_YYYYMMDD,
    #                                     end_date_YYYYMMDD)""")

    # log_in_color('white', 'info', 'Confirmed:')
    # log_in_color('white', 'info', E.confirmed_df.to_string())
    # log_in_color('white', 'info', 'Deferred:')
    # log_in_color('white', 'info', E.deferred_df.to_string())
    # log_in_color('white', 'info', 'Skipped:')
    # log_in_color('white', 'info', E.skipped_df.to_string())
    # log_in_color('white', 'info', 'Forecast:')
    # log_in_color('white', 'info', E.forecast_df.to_string())
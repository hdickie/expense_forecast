import BudgetSet, ExpenseForecast, AccountSet, pandas as pd, MemoRuleSet, copy, ForecastHandler
pd.options.mode.chained_assignment = None #apparently this warning can throw false positives???

from log_methods import log_in_color

if __name__ == '__main__':
    account_set = AccountSet.AccountSet([])
    budget_set = BudgetSet.BudgetSet([])
    memo_rule_set = MemoRuleSet.MemoRuleSet([])

    start_date_YYYYMMDD = '20230402'
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

    account_set.addAccount(name='Checking',
                           balance=current_checking_balance,
                           min_balance=0,
                           max_balance=float('Inf'),
                           account_type="checking")

    account_set.addAccount(name='Credit',
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

    account_set.addAccount(name='Loan A',
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

    account_set.addAccount(name='Loan B',
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

    account_set.addAccount(name='Loan C',
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

    account_set.addAccount(name='Loan D',
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

    account_set.addAccount(name='Loan E',
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

    account_set.addAccount(name='Tax Debt',
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

    F = ForecastHandler.ForecastHandler()

    move_in_w_mom_june_1_pay_800 = BudgetSet.BudgetSet([])
    #move_in_w_mom_june_1_pay_1000 = BudgetSet.BudgetSet([])
    move_in_w_mom_july_1_pay_800 = BudgetSet.BudgetSet([])
    #move_in_w_mom_july_1_pay_1000 = BudgetSet.BudgetSet([])
    move_in_w_jp_july_1_pay_1500 = BudgetSet.BudgetSet([])
    move_in_w_mom_aug_1_pay_800 = BudgetSet.BudgetSet([])
    #move_in_w_mom_aug_1_pay_1000 = BudgetSet.BudgetSet([])
    move_in_w_jp_aug_1_pay_1500 = BudgetSet.BudgetSet([])
    move_in_w_mom_sep_1_pay_800 = BudgetSet.BudgetSet([])
    #move_in_w_mom_sep_1_pay_1000 = BudgetSet.BudgetSet([])
    move_in_w_jp_sep_1_pay_1500 = BudgetSet.BudgetSet([])

    tech_job_may_1 = BudgetSet.BudgetSet([])
    tech_job_june_1 = BudgetSet.BudgetSet([])
    tech_job_july_1 = BudgetSet.BudgetSet([])
    emt_job_july_1__3_months = BudgetSet.BudgetSet([])
    emt_job_july_1__6_months = BudgetSet.BudgetSet([])

    move_in_w_mom_june_1_pay_800.addBudgetItem(start_date_YYYYMMDD='20230601', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    move_in_w_mom_june_1_pay_800.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230531', priority=1,
                                cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                                deferrable=False,
                                partial_payment_allowed=False)

    move_in_w_mom_june_1_pay_800.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230531', priority=1,
                                cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                                deferrable=False,
                                partial_payment_allowed=False)

    move_in_w_mom_june_1_pay_800.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230531', priority=1,
                                cadence='monthly', amount=100, memo='internet',
                                deferrable=False,
                                partial_payment_allowed=False)

    move_in_w_mom_june_1_pay_800.addBudgetItem(start_date_YYYYMMDD='20230601', end_date_YYYYMMDD='20231231', priority=1,
                                cadence='monthly', amount=800, memo='mom rent',
                                deferrable=False,
                                partial_payment_allowed=False)

    
    move_in_w_mom_july_1_pay_800.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                                               cadence='monthly', amount=1000, memo='additional cc payment',
                                               deferrable=False,
                                               partial_payment_allowed=False)

    move_in_w_mom_july_1_pay_800.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230630', priority=1,
                                               cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                                               deferrable=False,
                                               partial_payment_allowed=False)

    move_in_w_mom_july_1_pay_800.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230630', priority=1,
                                               cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                                               deferrable=False,
                                               partial_payment_allowed=False)

    move_in_w_mom_july_1_pay_800.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230630', priority=1,
                                               cadence='monthly', amount=100, memo='internet',
                                               deferrable=False,
                                               partial_payment_allowed=False)

    move_in_w_mom_july_1_pay_800.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                                               cadence='monthly', amount=800, memo='mom rent',
                                               deferrable=False,
                                               partial_payment_allowed=False)


    move_in_w_jp_july_1_pay_1500.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    move_in_w_jp_july_1_pay_1500.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230630', priority=1,
                                               cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                                               deferrable=False,
                                               partial_payment_allowed=False)

    move_in_w_jp_july_1_pay_1500.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230630', priority=1,
                                               cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                                               deferrable=False,
                                               partial_payment_allowed=False)

    move_in_w_jp_july_1_pay_1500.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230630', priority=1,
                                               cadence='monthly', amount=100, memo='internet',
                                               deferrable=False,
                                               partial_payment_allowed=False)

    move_in_w_jp_july_1_pay_1500.addBudgetItem(start_date_YYYYMMDD='20230701', end_date_YYYYMMDD='20231231', priority=1,
                                               cadence='monthly', amount=800, memo='jp rent',
                                               deferrable=False,
                                               partial_payment_allowed=False)



    move_in_w_mom_aug_1_pay_800.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    move_in_w_mom_aug_1_pay_800.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230730', priority=1,
                                               cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                                               deferrable=False,
                                               partial_payment_allowed=False)

    move_in_w_mom_aug_1_pay_800.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230730', priority=1,
                                               cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                                               deferrable=False,
                                               partial_payment_allowed=False)

    move_in_w_mom_aug_1_pay_800.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230730', priority=1,
                                               cadence='monthly', amount=100, memo='internet',
                                               deferrable=False,
                                               partial_payment_allowed=False)

    move_in_w_mom_aug_1_pay_800.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                                               cadence='monthly', amount=800, memo='mom rent',
                                               deferrable=False,
                                               partial_payment_allowed=False)




    move_in_w_jp_aug_1_pay_1500.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    move_in_w_jp_aug_1_pay_1500.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230730', priority=1,
                                              cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                                              deferrable=False,
                                              partial_payment_allowed=False)

    move_in_w_jp_aug_1_pay_1500.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230730', priority=1,
                                              cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                                              deferrable=False,
                                              partial_payment_allowed=False)

    move_in_w_jp_aug_1_pay_1500.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230730', priority=1,
                                              cadence='monthly', amount=100, memo='internet',
                                              deferrable=False,
                                              partial_payment_allowed=False)

    move_in_w_jp_aug_1_pay_1500.addBudgetItem(start_date_YYYYMMDD='20230801', end_date_YYYYMMDD='20231231', priority=1,
                                              cadence='monthly', amount=1500, memo='jp rent',
                                              deferrable=False,
                                              partial_payment_allowed=False)


    move_in_w_mom_sep_1_pay_800.addBudgetItem(start_date_YYYYMMDD='20230901', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    move_in_w_mom_sep_1_pay_800.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230830', priority=1,
                                              cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                                              deferrable=False,
                                              partial_payment_allowed=False)

    move_in_w_mom_sep_1_pay_800.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230830', priority=1,
                                              cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                                              deferrable=False,
                                              partial_payment_allowed=False)

    move_in_w_mom_sep_1_pay_800.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230830', priority=1,
                                              cadence='monthly', amount=100, memo='internet',
                                              deferrable=False,
                                              partial_payment_allowed=False)

    move_in_w_mom_sep_1_pay_800.addBudgetItem(start_date_YYYYMMDD='20230901', end_date_YYYYMMDD='20231231', priority=1,
                                              cadence='monthly', amount=800, memo='mom rent',
                                              deferrable=False,
                                              partial_payment_allowed=False)


    move_in_w_jp_sep_1_pay_1500.addBudgetItem(start_date_YYYYMMDD='20230901', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='monthly', amount=1000, memo='additional cc payment',
                               deferrable=False,
                               partial_payment_allowed=False)

    move_in_w_jp_sep_1_pay_1500.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD='20230830', priority=1,
                                              cadence='monthly', amount=1918, memo='2034 33rd ave rent',
                                              deferrable=False,
                                              partial_payment_allowed=False)

    move_in_w_jp_sep_1_pay_1500.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD='20230830', priority=1,
                                              cadence='monthly', amount=300, memo='2034 33rd ave utilities',
                                              deferrable=False,
                                              partial_payment_allowed=False)

    move_in_w_jp_sep_1_pay_1500.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD='20230830', priority=1,
                                              cadence='monthly', amount=100, memo='internet',
                                              deferrable=False,
                                              partial_payment_allowed=False)

    move_in_w_jp_sep_1_pay_1500.addBudgetItem(start_date_YYYYMMDD='20230901', end_date_YYYYMMDD='20231231', priority=1,
                                              cadence='monthly', amount=1500, memo='jp rent',
                                              deferrable=False,
                                              partial_payment_allowed=False)


    tech_job_may_1.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230501', priority=1,
                   cadence='weekly', amount=450, memo='unemployment income',
                   deferrable=False,
                   partial_payment_allowed=False)
    tech_job_may_1.addBudgetItem(start_date_YYYYMMDD='20230515', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                               deferrable=False,
                               partial_payment_allowed=False)

    tech_job_june_1.addBudgetItem(start_date_YYYYMMDD='20230427', end_date_YYYYMMDD='20230427', priority=1,
                               cadence='once', amount=2900, memo='EMT class',
                               deferrable=False,
                               partial_payment_allowed=False)
    tech_job_june_1.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230601', priority=1,
                                 cadence='weekly', amount=450, memo='unemployment income',
                                 deferrable=False,
                                 partial_payment_allowed=False)
    tech_job_june_1.addBudgetItem(start_date_YYYYMMDD='20230615', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                               deferrable=False,
                               partial_payment_allowed=False)

    tech_job_july_1.addBudgetItem(start_date_YYYYMMDD='20230427', end_date_YYYYMMDD='20230427', priority=1,
                                  cadence='once', amount=2900, memo='EMT class',
                                  deferrable=False,
                                  partial_payment_allowed=False)
    tech_job_july_1.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230701', priority=1,
                                  cadence='weekly', amount=450, memo='unemployment income',
                                  deferrable=False,
                                  partial_payment_allowed=False)
    tech_job_july_1.addBudgetItem(start_date_YYYYMMDD='20230715', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                               deferrable=False,
                               partial_payment_allowed=False)

    emt_job_july_1__3_months.addBudgetItem(start_date_YYYYMMDD='20230427', end_date_YYYYMMDD='20230427', priority=1,
                                  cadence='once', amount=2900, memo='EMT class',
                                  deferrable=False,
                                  partial_payment_allowed=False)
    emt_job_july_1__3_months.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230701', priority=1,
                                 cadence='weekly', amount=450, memo='unemployment income',
                                 deferrable=False,
                                 partial_payment_allowed=False)
    emt_job_july_1__3_months.addBudgetItem(start_date_YYYYMMDD='20230715', end_date_YYYYMMDD='20230928', priority=1,
                               cadence='semiweekly', amount=1320, memo='EMT income',
                               deferrable=False,
                               partial_payment_allowed=False)
    tech_job_july_1.addBudgetItem(start_date_YYYYMMDD='20231001', end_date_YYYYMMDD='20231231', priority=1,
                                  cadence='semiweekly', amount=3360, memo='income full-time 62.5/hr post-taxes',
                                  deferrable=False,
                                  partial_payment_allowed=False)

    emt_job_july_1__6_months.addBudgetItem(start_date_YYYYMMDD='20230427', end_date_YYYYMMDD='20230427', priority=1,
                                           cadence='once', amount=2900, memo='EMT class',
                                           deferrable=False,
                                           partial_payment_allowed=False)
    emt_job_july_1__6_months.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD='20230701', priority=1,
                                           cadence='weekly', amount=450, memo='unemployment income',
                                           deferrable=False,
                                           partial_payment_allowed=False)
    emt_job_july_1__6_months.addBudgetItem(start_date_YYYYMMDD='20230715', end_date_YYYYMMDD='20231231', priority=1,
                               cadence='semiweekly', amount=1320, memo='EMT income',
                               deferrable=False,
                               partial_payment_allowed=False)

    list_of_lists_of_budget_sets = [
        [move_in_w_mom_june_1_pay_800,
        move_in_w_mom_july_1_pay_800,
        move_in_w_jp_july_1_pay_1500,
        move_in_w_mom_aug_1_pay_800,
        move_in_w_jp_aug_1_pay_1500,
        move_in_w_mom_sep_1_pay_800,
        move_in_w_jp_sep_1_pay_1500
         ], #income
        [
            tech_job_may_1,
            tech_job_june_1,
            tech_job_july_1,
            emt_job_july_1__3_months,
            emt_job_july_1__6_months
        ] #living
    ]

    F.calculateMultipleChooseOne(AccountSet=copy.deepcopy(account_set),
                                 Core_BudgetSet=budget_set,
                                 MemoRuleSet=memo_rule_set,
                                 start_date_YYYYMMDD=start_date_YYYYMMDD,
                                 end_date_YYYYMMDD=end_date_YYYYMMDD,
                                 list_of_lists_of_budget_sets=list_of_lists_of_budget_sets)
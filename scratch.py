import logging

import BudgetSet, ExpenseForecast, AccountSet, datetime, pandas as pd, MemoRuleSet, copy
pd.options.mode.chained_assignment = None #apparently this warning can throw false positives???

from log_methods import log_in_color
from log_methods import display_test_result

logger = logging.getLogger()

if __name__ == '__main__':
    log_in_color('green', 'debug', 'START SCRATCH', 0)

    account_set = AccountSet.AccountSet([])
    budget_set = BudgetSet.BudgetSet([])
    memo_rule_set = MemoRuleSet.MemoRuleSet([])
    start_date_YYYYMMDD = '20230313'
    end_date_YYYYMMDD = '20231231'

    current_checking_balance = 2434.18
    current_credit_previous_statement_balance = 7351.23
    current_credit_current_statement_balance = 7456.73 - current_credit_previous_statement_balance




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

    budget_set.addBudgetItem(start_date_YYYYMMDD=start_date_YYYYMMDD, end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                                 cadence='daily', amount=30, memo='food',
                                 deferrable=False)

    budget_set.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                             cadence='monthly', amount=1918, memo='rent',
                             deferrable=False)

    budget_set.addBudgetItem(start_date_YYYYMMDD='20230217', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                             cadence='monthly', amount=89, memo='car insurance',
                             deferrable=False)

    budget_set.addBudgetItem(start_date_YYYYMMDD='20230331', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                             cadence='monthly', amount=163.09, memo='phone bill',
                             deferrable=False)

    budget_set.addBudgetItem(start_date_YYYYMMDD='20230127', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                             cadence='monthly', amount=100, memo='internet',
                             deferrable=False)

    budget_set.addBudgetItem(start_date_YYYYMMDD='20230219', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                             cadence='monthly', amount=8, memo='hulu',
                             deferrable=False)

    budget_set.addBudgetItem(start_date_YYYYMMDD='20230219', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                             cadence='monthly', amount=15, memo='hbo max',
                             deferrable=False)

    budget_set.addBudgetItem(start_date_YYYYMMDD='20230307', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                             cadence='monthly', amount=33, memo='gym',
                             deferrable=False)

    budget_set.addBudgetItem(start_date_YYYYMMDD='20230407', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                             cadence='monthly', amount=10, memo='spotify',
                             deferrable=False)

    budget_set.addBudgetItem(start_date_YYYYMMDD='20230101', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                             cadence='monthly', amount=100, memo='gas and bus',
                             deferrable=False)

    budget_set.addBudgetItem(start_date_YYYYMMDD='20230221', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                             cadence='monthly', amount=175.50, memo='health insurance',
                             deferrable=False)

    budget_set.addBudgetItem(start_date_YYYYMMDD='20230201', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                             cadence='monthly', amount=300, memo='utilities',
                             deferrable=False)

    budget_set.addBudgetItem(start_date_YYYYMMDD='20230102', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=4,
                             cadence='monthly', amount=3611.5, memo='cyclical billing total',
                             deferrable=False)

    budget_set.addBudgetItem(start_date_YYYYMMDD='20230317', end_date_YYYYMMDD=end_date_YYYYMMDD, priority=1,
                             cadence='weekly', amount=450, memo='income',
                             deferrable=False)

    # 1000 + 1918 + 89 + 163 + 100 + 8 + 15 + 33 + 10 + 100 + 175.5 = 3611.5 + 300 ; cyclical billing total

    memo_rule_set.addMemoRule(memo_regex='income', account_from=None, account_to='Checking', transaction_priority=1)

    memo_rule_set.addMemoRule(memo_regex='food', account_from='Credit', account_to=None, transaction_priority=1)
    memo_rule_set.addMemoRule(memo_regex='internet', account_from='Credit', account_to=None, transaction_priority=1)
    memo_rule_set.addMemoRule(memo_regex='phone bill', account_from='Credit', account_to=None, transaction_priority=1)
    memo_rule_set.addMemoRule(memo_regex='car insurance', account_from='Credit', account_to=None, transaction_priority=1)
    memo_rule_set.addMemoRule(memo_regex='health insurance', account_from='Credit', account_to=None,transaction_priority=1)
    memo_rule_set.addMemoRule(memo_regex='gas and bus', account_from='Credit', account_to=None,transaction_priority=1)
    memo_rule_set.addMemoRule(memo_regex='spotify', account_from='Credit', account_to=None,transaction_priority=1)
    memo_rule_set.addMemoRule(memo_regex='gym', account_from='Credit', account_to=None,transaction_priority=1)
    memo_rule_set.addMemoRule(memo_regex='hbo max', account_from='Credit', account_to=None,transaction_priority=1)
    memo_rule_set.addMemoRule(memo_regex='hulu', account_from='Credit', account_to=None,transaction_priority=1)
    memo_rule_set.addMemoRule(memo_regex='rent', account_from='Checking', account_to=None,transaction_priority=1)
    memo_rule_set.addMemoRule(memo_regex='utilities', account_from='Checking', account_to=None, transaction_priority=1)

    #memo_rule_set.addMemoRule(memo_regex='cyclical billing total', account_from='Checking', account_to='Credit', transaction_priority=4)



    E = ExpenseForecast.ExpenseForecast(account_set,
                                        budget_set,
                                        memo_rule_set,
                                        start_date_YYYYMMDD,
                                        end_date_YYYYMMDD)

    print(E.forecast_df.to_string())

    # expected_result_df = pd.DataFrame({
    #     'Date': ['20000101', '20000102', '20000103'],
    #     'Checking': [200, 0, 0],
    #     'Credit: Curr Stmt Bal': [500, 500, 500],
    #     'Credit: Prev Stmt Bal': [500, 300, 300],
    #     'Memo': ['', '', '']
    # })
    # expected_result_df.Date = [datetime.datetime.strptime(x, '%Y%m%d').strftime('%Y-%m-%d') for x in
    #                              expected_result_df.Date]


    #
    # R = E.compute_forecast_difference(expected_result_df,
    #                                                           label='scratch test',
    #                                                           make_plots=False,
    #                                                           diffs_only=True,
    #                                                                 require_matching_columns=True,
    #                                                                 require_matching_date_range=True,
    #                                                                 append_expected_values=False,
    #                                                           return_type='dataframe')
    #
    # print('R:')
    # print(R.to_string())
    # display_test_result('scratch test display_test_result()',R)

    # test_descriptions = []
    # test_descriptions.append('scratch test 1')
    #
    # account_set = AccountSet.AccountSet([])
    # budget_set = BudgetSet.BudgetSet([])
    # memo_rule_set = MemoRuleSet.MemoRuleSet([])
    # start_date_YYYYMMDD = '20000101'
    # end_date_YYYYMMDD = '20000103'
    #
    # account_sets = []
    # budget_sets = []
    # memo_rule_sets = []
    #
    # expected_results = []
    #
    # start_date_YYYYMMDD = start_date_YYYYMMDD
    # end_date_YYYYMMDD = end_date_YYYYMMDD
    #
    # for i in range(0, len(test_descriptions)):
    #     account_sets.append(copy.deepcopy(account_set))
    #     budget_sets.append(copy.deepcopy(budget_set))
    #     memo_rule_sets.append(copy.deepcopy(memo_rule_set))
    #
    # ### BEGIN Test Case 1
    # account_sets[0].addAccount(name='Checking',
    #                            balance=2000,
    #                            min_balance=0,
    #                            max_balance=float('Inf'),
    #                            account_type="checking")
    #
    # account_sets[0].addAccount(name='Credit',
    #                            balance=0,
    #                            min_balance=0,
    #                            max_balance=20000,
    #                            account_type="credit",
    #                            billing_start_date_YYYYMMDD='19991202',
    #                            interest_type='Compound',
    #                            apr=0.05,
    #                            interest_cadence='Monthly',
    #                            minimum_payment=40,
    #                            previous_statement_balance=1000,
    #                            principal_balance=None,
    #                            accrued_interest=None
    #                            )
    #
    # print(account_sets[0].getAvailableBalances())

    # budget_sets[0].addBudgetItem(start_date_YYYYMMDD='20000101', end_date_YYYYMMDD='20000103', priority=1,
    #                              cadence='daily', amount=0, memo='dummy memo',
    #                              deferrable=False)
    #
    # memo_rule_sets[0].addMemoRule(memo_regex='.*', account_from='Checking', account_to='Credit',
    #                               transaction_priority=1)
    #
    # expected_result_0_df = pd.DataFrame({
    #     'Date': ['20000101', '20000102', '20000103'],
    #     'Checking': [0, 0, 0],
    #     'Credit: Curr Stmt Bal': [0, 0, 0],
    #     'Credit: Prev Stmt Bal': [1000, 1004.17, 1004.17],
    #     'Memo': ['', '', '']
    # })
    # expected_result_0_df.Date = [datetime.datetime.strptime(x, '%Y%m%d').strftime('%Y-%m-%d') for x in
    #                              expected_result_0_df.Date]
    # expected_results.append(expected_result_0_df)
    #
    # expense_forecasts = []
    #
    # expense_forecasts.append(ExpenseForecast.ExpenseForecast(account_sets[0],
    #                                                          budget_sets[0],
    #                                                          memo_rule_sets[0],
    #                                                          start_date_YYYYMMDD,
    #                                                          end_date_YYYYMMDD, raise_exceptions=False))
    #
    # print('print(expense_forecasts[0].forecast_df.to_string())')
    # print(expense_forecasts[0].forecast_df.to_string())
    # print('expected_results[0]:')
    # print(expected_results[0])
    #
    # d = expense_forecasts[0].compute_forecast_difference(expected_results[0],
    #                                                      label=test_descriptions[0],
    #                                                      make_plots=True,
    #                                                      diffs_only=True,
    #                                                      require_matching_columns=True,
    #                                                      require_matching_date_range=True,
    #                                                      append_expected_values=True,
    #                                                      return_type='dataframe')
    # d = d.reindex(sorted(d.columns), axis=1)
    #
    #
    # print('print(d.to_string()):')
    # print(d.to_string())
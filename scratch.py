import BudgetSet, ExpenseForecast, AccountSet, datetime, pandas as pd, MemoRuleSet, copy
pd.options.mode.chained_assignment = None #apparently this warning can throw false positives???

if __name__ == '__main__':

    test_descriptions = []
    test_descriptions.append('scratch test 1')

    account_set = AccountSet.AccountSet([])
    budget_set = BudgetSet.BudgetSet([])
    memo_rule_set = MemoRuleSet.MemoRuleSet([])
    start_date_YYYYMMDD = '20000101'
    end_date_YYYYMMDD = '20000103'

    account_sets = []
    budget_sets = []
    memo_rule_sets = []

    expected_results = []

    start_date_YYYYMMDD = start_date_YYYYMMDD
    end_date_YYYYMMDD = end_date_YYYYMMDD

    for i in range(0, len(test_descriptions)):
        account_sets.append(copy.deepcopy(account_set))
        budget_sets.append(copy.deepcopy(budget_set))
        memo_rule_sets.append(copy.deepcopy(memo_rule_set))

    ### BEGIN Test Case 1
    account_sets[0].addAccount(name='Checking',
                               balance=2000,
                               min_balance=0,
                               max_balance=float('Inf'),
                               account_type="checking")

    account_sets[0].addAccount(name='Credit',
                               balance=0,
                               min_balance=0,
                               max_balance=float('Inf'),
                               account_type="credit",
                               billing_start_date_YYYYMMDD='19991202',
                               interest_type='Compound',
                               apr=0.05,
                               interest_cadence='Monthly',
                               minimum_payment=40,
                               previous_statement_balance=1000,
                               principal_balance=None,
                               accrued_interest=None
                               )

    budget_sets[0].addBudgetItem(start_date_YYYYMMDD='20000101', end_date_YYYYMMDD='20000103', priority=1,
                                 cadence='daily', amount=0, memo='dummy memo',
                                 deferrable=False)

    memo_rule_sets[0].addMemoRule(memo_regex='.*', account_from='Checking', account_to='Credit',
                                  transaction_priority=1)

    expected_result_0_df = pd.DataFrame({
        'Date': ['20000101', '20000102', '20000103'],
        'Checking': [0, 0, 0],
        'Credit: Curr Stmt Bal': [0, 0, 0],
        'Credit: Prev Stmt Bal': [1000, 1004.17, 1004.17],
        'Memo': ['', '', '']
    })
    expected_result_0_df.Date = [datetime.datetime.strptime(x, '%Y%m%d').strftime('%Y-%m-%d') for x in
                                 expected_result_0_df.Date]
    expected_results.append(expected_result_0_df)

    expense_forecasts = []

    expense_forecasts.append(ExpenseForecast.ExpenseForecast(account_sets[0],
                                                             budget_sets[0],
                                                             memo_rule_sets[0],
                                                             start_date_YYYYMMDD,
                                                             end_date_YYYYMMDD, raise_exceptions=False))

    print('print(expense_forecasts[0].forecast_df.to_string())')
    print(expense_forecasts[0].forecast_df.to_string())
    print('expected_results[0]:')
    print(expected_results[0])

    d = expense_forecasts[0].compute_forecast_difference(expected_results[0],
                                                         label=test_descriptions[0],
                                                         make_plots=True,
                                                         diffs_only=True,
                                                         require_matching_columns=True,
                                                         require_matching_date_range=True,
                                                         append_expected_values=True,
                                                         return_type='dataframe')
    d = d.reindex(sorted(d.columns), axis=1)


    print('print(d.to_string()):')
    print(d.to_string())
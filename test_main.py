import Account, BudgetItem, BudgetSet, ExpenseForecast, AccountSet, datetime, pandas as pd, MemoRule, MemoRuleSet
pd.options.mode.chained_assignment = None #apparently this warning can throw false positives???

if __name__ == '__main__':

    #Define starting parameters
    start_date_YYYYMMDD = datetime.datetime.now().strftime('%Y%m%d')

    starting_balances = {}
    starting_balances['Checking'] = 0
    starting_balances['Credit'] = 0
    starting_balances['Savings'] = 0

    #Define accounts
    account_set = AccountSet.AccountSet()
    account_set.addAccount(name='Checking',
                           balance=1000,
                           min_balance=0,
                           max_balance=float('inf'),
                           apr=0,
                           interest_cadence='None',
                           interest_type='None',
                           billing_start_date='None',
                           account_type='checking',
                           principal_balance=None,
                           accrued_interest=None)

    account_set.addAccount(name='Credit Card',
                           balance=1001,
                           min_balance=0,
                           max_balance=float('inf'),
                           apr=0.2674,
                           interest_cadence='Monthly',
                           interest_type='Compound',
                           billing_start_date='2000-01-07',
                           account_type='credit',
                           principal_balance=-1,
                           accrued_interest=-1)

    account_set.addAccount(name='Savings',
                           balance=1002,
                           min_balance=0,
                           max_balance=float('inf'),
                           apr=0.01,
                           interest_cadence='Monthly',
                           interest_type='Compound',
                           billing_start_date='2000-01-07',
                           account_type='credit',
                           principal_balance=-1,
                           accrued_interest=-1)

    account_set.addAccount(name='Loan A',
                           balance=1003,
                           min_balance=0,
                           max_balance=float('inf'),
                           apr=0.06,
                           interest_cadence='daily',
                           interest_type='Simple',
                           billing_start_date='2000-01-07',
                           account_type='loan',
                           principal_balance=-1,
                           accrued_interest=-1)

    account_set_df = account_set.getAccounts()

    #Define Budget Items
    budget_set = BudgetSet.BudgetSet()
    budget_set.addBudgetItem(start_date = '2000-01-01',
                 priority = 1,
                 cadence='daily',
                 amount=-30,
                 memo='Food')

    budget_set.addBudgetItem(start_date='2000-01-01',
                                                   priority=1,
                                                   cadence='weekly',
                                                   amount=1200,
                                                   memo='Income')


    budget_schedule_df = budget_set.getBudgetSchedule(start_date_YYYYMMDD,365)

    #Define memo rules
    memo_rule_set = MemoRuleSet.MemoRuleSet()
    memo_rule_set.addMemoRule(
        memo_regex="Food",
        account_from="Credit Card: Credit Current Statement Balance",
        account_to=None,
        transaction_priority=1
    )
    memo_rule_set.addMemoRule(
        memo_regex="Income",
        account_from=None,
        account_to="Checking",
        transaction_priority=1
    )
    memo_rules_df = memo_rule_set.getMemoRules()

    #Begin simulation
    x = ExpenseForecast.ExpenseForecast()
    y = x.satisfice(budget_schedule_df, account_set_df,memo_rules_df)


    #QC output
    print("-------------------------------")
    print(budget_schedule_df.to_string())
    print("-------------------------------")
    print(memo_rules_df.to_string())
    print("-------------------------------")
    print(y[1].to_string())
    print("-------------------------------")
    y[2].to_csv('C:/Users/HumeD/Documents/out.csv',index=False)

    forecast_df = y[2]
    x.plotOutput(forecast_df,'C:/Users/HumeD/Documents/outplot.png')
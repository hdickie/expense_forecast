import Account, BudgetItem, BudgetSet, ExpenseForecast, AccountSet

if __name__ == '__main__':

    starting_balances = {}
    starting_balances['Checking'] = 0
    starting_balances['Credit'] = 0
    starting_balances['Savings'] = 0

    checking_account = Account.Account(name='Checking',
                               balance=0,
                               min_balance=0,
                               max_balance=float('inf'),
                               apr=0,
                               interest_cadence='None',
                               interest_type='None',
                               billing_start_date='None')

    savings_account = Account.Account(name='Savings',
                                       balance=0,
                                       min_balance=0,
                                       max_balance=float('inf'),
                                       apr=0.01,
                                       interest_cadence='Monthly',
                                       interest_type='Compound',
                                       billing_start_date='2000-01-01')

    credit_account = Account.Account(name='Credit Card',
                                      balance=0,
                                      min_balance=0,
                                      max_balance=float('inf'),
                                      apr=0.01,
                                      interest_cadence='Monthly',
                                      interest_type='Compound',
                                      billing_start_date='2000-01-07')

    all_accounts__list = []
    all_accounts__list.append(checking_account)
    all_accounts__list.append(savings_account)
    all_accounts__list.append(credit_account)
    account_set = AccountSet.AccountSet(all_accounts__list)


    all_budget_items__list = []
    daily_food_budget_item = BudgetItem.BudgetItem(start_date = '2000-01-01',
                 priority = 1,
                 cadence='daily',
                 amount=-30,
                 memo='Food')

    weekly_income_budget_item = BudgetItem.BudgetItem(start_date='2000-01-01',
                                                   priority=1,
                                                   cadence='weekly',
                                                   amount=1200,
                                                   memo='Income')

    all_budget_items__list.append(daily_food_budget_item)
    all_budget_items__list.append(weekly_income_budget_item)

    budget_set = BudgetSet.BudgetSet(all_budget_items__list)


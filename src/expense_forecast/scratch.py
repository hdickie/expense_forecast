#scratch.py

from expense_forecast.ExpenseForecastInitialConditions import ExpenseForecastInitialConditions
from expense_forecast.AccountSet import AccountSet
from expense_forecast.BudgetSet import BudgetSet

from expense_forecast.MemoRuleSet import MemoRuleSet
from expense_forecast.ForecastHandler import ForecastHandler
from expense_forecast.MilestoneSet import MilestoneSet

import datetime
from datetime import date

if __name__ == '__main__':

    A = AccountSet()
    B = BudgetSet()
    M = MemoRuleSet()
    F = ForecastHandler()
    
    start_date = date(2026,7,4)
    end_date = start_date + datetime.timedelta(days=365)

    income_start_date = date(2026,8,22)
    paycheck_amount = 22.77 * 80 * 0.75 # assume 25% tax at a minimum

    A.createAccount(name='Checking',balance=5897.80,
                    min_balance=0,max_balance=float('Inf'),
                    account_type='checking',
                    primary_checking_ind=True)
    
    A.createAccount(name='Savings',balance=274.69 + 50.52,
                    min_balance=0,max_balance=float('Inf'),
                    account_type='checking',
                    primary_checking_ind=False)
    
    A.createCreditCardAccount(name='Citi',
                                current_statement_balance=0,
                                previous_statement_balance=3871.98,
                                billing_start_date=date(2026,6,14),
                                minimum_payment=40,
                                end_of_previous_cycle_balance=3871.98,
                                min_balance=0,
                                max_balance=25_000,
                                apr=0.2149)

    A.createCreditCardAccount(name='Chase',
                                current_statement_balance=0,
                                previous_statement_balance=6566.49,
                                billing_start_date=date(2026,6,6),
                                minimum_payment=40,
                                end_of_previous_cycle_balance=6566.49,
                                min_balance=0,
                                max_balance=25_000,
                                apr=0.2724)
    
    A.createLoanAccount(name="Loan A", 
                        principal_balance=3484.34, 
                        interest_balance=124.33, 
                        min_balance=0,
                        max_balance=20_000,
                        billing_start_date=date(2026,6,3),
                        minimum_payment=10, #TODO not sure
                        end_of_previous_cycle_balance=3484.34 + 124.33,
                        apr=0.0466) #TODO end_of_previous_cycle_balance shouldn't exist...
    
    A.createLoanAccount(name="Loan B", 
                        principal_balance=4519.90, 
                        interest_balance=67.01, 
                        min_balance=0,
                        max_balance=20_000,
                        billing_start_date=date(2026,6,3),
                        minimum_payment=10, #TODO not sure
                        end_of_previous_cycle_balance=4519.90 + 67.01,
                        apr=0.0429) #TODO end_of_previous_cycle_balance shouldn't exist...
    
    A.createLoanAccount(name="Loan C", 
                            principal_balance=1969.58, 
                            interest_balance=63.28, 
                            min_balance=0,
                            max_balance=20_000,
                            billing_start_date=date(2026,6,3),
                            minimum_payment=10, #TODO not sure
                            end_of_previous_cycle_balance=1969.58 + 63.28,
                            apr=0.0429) #TODO end_of_previous_cycle_balance shouldn't exist...
    
    A.createLoanAccount(name="Loan D", 
                            principal_balance=4506.0, 
                            interest_balance=52.79, 
                            min_balance=0,
                            max_balance=20_000,
                            billing_start_date=date(2026,6,3),
                            minimum_payment=10, #TODO not sure
                            end_of_previous_cycle_balance=4506.0 + 52.79,
                            apr=0.0376) #TODO end_of_previous_cycle_balance shouldn't exist...
    
    A.createLoanAccount(name="Loan E", 
                            principal_balance=1855.69, 
                            interest_balance=50.18, 
                            min_balance=0,
                            max_balance=20_000,
                            billing_start_date=date(2026,6,3),
                            minimum_payment=10, #TODO not sure
                            end_of_previous_cycle_balance=1855.69 + 50.18,
                            apr=0.0376) #TODO end_of_previous_cycle_balance shouldn't exist...

    B.addBudgetItem(start_date=start_date, end_date=end_date, priority=1,
                    cadence='daily',amount=10,memo='food expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B.addBudgetItem(start_date=start_date, end_date=end_date, priority=1,
                    cadence='semiweekly',amount=80,memo='gas expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B.addBudgetItem(start_date=start_date, end_date=end_date, priority=1,
                    cadence='monthly',amount=287.68,memo='phone expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B.addBudgetItem(start_date=start_date, end_date=end_date, priority=1,
                    cadence='monthly',amount=10,memo='hulu expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B.addBudgetItem(start_date=date(2026,7,2), end_date=end_date, priority=1,
                    cadence='monthly',amount=14,memo='paramount plus expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B.addBudgetItem(start_date=date(2026,6,26), end_date=end_date, priority=1,
                    cadence='monthly',amount=9,memo='netflix expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B.addBudgetItem(start_date=start_date, end_date=end_date, priority=1,
                    cadence='monthly',amount=100,memo='car insurance expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B.addBudgetItem(start_date=date(2026,7,3), end_date=end_date, priority=1,
                    cadence='monthly',amount=149,memo='storage expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    B.addBudgetItem(start_date=date(2026,6,6), end_date=end_date, priority=1,
                    cadence='monthly',amount=129,memo='joyous expense',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    
    B.addBudgetItem(start_date=date(2026,9,1), end_date=date(2026,9,1), priority=1,
                    cadence='once',amount=6621.33,memo='extra cc payment 1',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    
    B.addBudgetItem(start_date=date(2026,10,1), end_date=date(2026,10,1), priority=1,
                    cadence='once',amount=2377.50,memo='extra cc payment 2',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    
    #delete the subtracted penny to cause error
    B.addBudgetItem(start_date=date(2026,11,1), end_date=date(2026,11,1), priority=1,
                    cadence='monthly',amount=1533.47 -0.01,memo='extra cc payment 3',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)

    # 9/1 ADDTL CC PAYMENT (Chase -$6621.33)
    # 10/1 payment $2377.50
    # 11/1 1533.47

    B.addBudgetItem(start_date=income_start_date, end_date=end_date, priority=1,
                    cadence='semiweekly',amount=paycheck_amount,memo='CNA Income',income_flag=True, 
                    deferrable=False, partial_payment_allowed=False)
    M.addMemoRule(memo_regex='.*expense.*',
                  account_from='Chase',
                  account_to=None,
                  transaction_priority=1)
    M.addMemoRule(memo_regex='.*cc payment.*',
                  account_from='Checking',
                  account_to='Chase',
                  transaction_priority=1)
    M.addMemoRule(memo_regex='CNA Income',
                  account_from=None,
                  account_to='Checking',
                  transaction_priority=1)
    M.addMemoRule(memo_regex='extra cc payment',
                  account_from='Checking',
                  account_to='Chase',
                  transaction_priority=2)
    
    MS = MilestoneSet()
    
    IO = ExpenseForecastInitialConditions(start_date, end_date, A,B,M)

    R = F.runForecast(IO, MS, include_debug_columns=True)

    R.writeToJSONFile(str(R.unique_id)+'.json')
    F.generateHTMLReport(R)
    print(R.forecast_df.to_string())

    # TODO rounding error cause this fail


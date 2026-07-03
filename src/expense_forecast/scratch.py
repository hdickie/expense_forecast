#scratch.py

from expense_forecast.ExpenseForecastInitialConditions import ExpenseForecastInitialConditions
from expense_forecast.AccountSet import AccountSet
from expense_forecast.BudgetSet import BudgetSet

from expense_forecast.MemoRuleSet import MemoRuleSet
from expense_forecast.ForecastHandler import ForecastHandler
from expense_forecast.MilestoneSet import MilestoneSet

from datetime import date

if __name__ == '__main__':
    
    start_date = date(2026,6,1)
    end_date = date(2026,6,5)

    A = AccountSet()
    B = BudgetSet()
    M = MemoRuleSet()
    F = ForecastHandler()

    A.createAccount(name="Checking",
                    balance=1000,
                    min_balance=0,
                    max_balance=float('inf'),
                    account_type="checking",
                    primary_checking_ind=True)
    A.createAccount(name="Credit",
                    balance=1000,
                    min_balance=0,
                    max_balance=25_000,
                    account_type="credit",
                    billing_start_date=date(2026,5,3),
                    current_statement_balance=0,
                    previous_statement_balance=1000,
                    minimum_payment=40,
                    apr=0.28,
                    end_of_previous_cycle_balance=1000,
                    interest_cadence="monthly"
                    )
    
    B.addBudgetItem(start_date=start_date, end_date=end_date, priority=1,
                    cadence='daily',amount=10,memo='food',income_flag=False, 
                    deferrable=False, partial_payment_allowed=False)
    M.addMemoRule(memo_regex='.*',
                  account_from='Checking',
                  account_to=None,
                  transaction_priority=1)
    
    MS = MilestoneSet()
    
    IO = ExpenseForecastInitialConditions(start_date, end_date, A,B,M)

    R = F.runForecast(IO, MS, include_debug_columns=True)

    print(R.forecast_df.to_string())


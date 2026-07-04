import pytest
from datetime import date
from expense_forecast.AccountSet import AccountSet
from expense_forecast.BudgetSet import BudgetSet
from expense_forecast.MemoRuleSet import MemoRuleSet
from expense_forecast.MilestoneSet import MilestoneSet
from expense_forecast.ExpenseForecastInitialConditions import ExpenseForecastInitialConditions
from expense_forecast.ForecastHandler import ForecastHandler

class TestForecastHandler:

    @pytest.mark.skip(reason="This example works, but I'm not sure what the success criteria for this test should be.")
    @pytest.mark.integration
    def test_ForecastHandler(self):
        start_date = date(2026,6,1)
        end_date = date(2026,6,30)
        
        A = AccountSet()
        B = BudgetSet()
        M = MemoRuleSet()
        MS = MilestoneSet()

        A.createCheckingAccount(
            name="Checking",
            balance=1000,
            min_balance=0,
            max_balance=float("inf"),
            primary_checking_ind=True,
        )

        B.addBudgetItem(
            start_date=start_date,
            end_date=end_date,
            priority=1,
            cadence="daily",
            amount=10,
            memo="food",
            income_flag=False,
            deferrable=False,
            partial_payment_allowed=False,
        )

        M.addMemoRule(
            memo_regex="food",
            account_from="Checking",
            account_to=None,
            transaction_priority=1,
        )

        MS = MilestoneSet()

        E_IO = ExpenseForecastInitialConditions(
            start_date=start_date,
            end_date=end_date,
            account_set=A,
            budget_set=B,
            memo_rule_set=M,
            milestone_set=MS)
        
        R = ForecastHandler().runForecast(E_IO, MS)

        assert R.forecast_df["Checking"].iat[0] == 700
import pytest
import pandas as pd
from datetime import date

from expense_forecast.AccountSet import AccountSet
from expense_forecast.BudgetSet import BudgetSet
from expense_forecast.ExpenseForecast import ExpenseForecast
from expense_forecast.MemoRuleSet import MemoRuleSet
from expense_forecast.MilestoneSet import MilestoneSet

import subprocess

class TestE2E:

    #this is actually an integration test, but it's proper place is 
    # in a folder structure i havent created yet
    @pytest.mark.integration
    def test_integration_MVP(self):

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

        for _, budget_item in B.getBudgetSchedule().iterrows():
            memo_rule = M.findMatchingMemoRule(
                budget_item.Memo,
                budget_item.Priority,
            )
            A.executeTransaction(
                memo_rule.account_from,
                memo_rule.account_to,
                budget_item.Amount,
                income_flag=budget_item.Income_Flag,
            )

        forecast_df = pd.DataFrame(
            [
                {
                    "Date": end_date,
                    "Checking": A.getBalances()["Checking"],
                }
            ]
        )
        E = ExpenseForecast(
            unique_id="MVP",
            forecast_df=forecast_df,
            milestone_set=MS,
            milestone_results={},
        )

        assert E.forecast_df["Checking"].iat[0] == 700

    @pytest.mark.E2E
    def test_E2E_MVP(self):
        # got id from
        # (at project root) ef stage forecast --source file --filename ./tests/assets/e2e_mvp_forecast.json
        subprocess.run(["ef", "--source", "file", "--id", "TBD"])

    @pytest.mark.E2E
    @pytest.mark.skip(reason="not yet implemented")
    def test_E2E_pay_off_credit_card(self):
        pass
        # raise NotImplementedError

    @pytest.mark.E2E
    @pytest.mark.skip(reason="not yet implemented")
    def test_E2E_optimize_loan_payment(self):
        pass

    @pytest.mark.E2E
    @pytest.mark.skip(reason="not yet implemented")
    def test_E2E_home_ownership(self):
        pass

    @pytest.mark.E2E
    @pytest.mark.skip(reason="not yet implemented")
    def test_E2E_retirement(self):
        pass

    @pytest.mark.E2E
    @pytest.mark.skip(reason="not yet implemented")
    def test_E2E_risk_management(self):
        pass

    @pytest.mark.E2E
    @pytest.mark.skip(reason="not yet implemented")
    def test_E2E_impulse_spending(self):
        pass

    @pytest.mark.E2E
    @pytest.mark.skip(reason="not yet implemented")
    def test_E2E_accruals_and_milestone_tracking(self):
        pass

    @pytest.mark.E2E
    @pytest.mark.skip(reason="not yet implemented")
    def test_E2E_define_rich(self):
        pass

    @pytest.mark.E2E
    @pytest.mark.skip(reason="not yet implemented")
    def test_E2E_communicate(self):
        pass

    @pytest.mark.E2E
    @pytest.mark.skip(reason="not yet implemented")
    def test_E2E_privacy(self):
        pass

    #"from junitparser import JUnitXml;xml = JUnitXml.fromfile('test_results.xml');skipped_tests = len([case for suite in xml for case in suite if case.result and case.result[0].type == 'pytest.skip']);print(str(len(xml.tests)));print(str(len(skipped_tests)))"

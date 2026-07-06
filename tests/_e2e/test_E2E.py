import pytest
import pandas as pd
from datetime import date
import datetime
import json
from pathlib import Path
import tempfile

from expense_forecast.AccountSet import AccountSet
from expense_forecast.BudgetSet import BudgetSet
from expense_forecast.ExpenseForecastInitialConditions import ExpenseForecastInitialConditions
from expense_forecast.SimulationStepper import SimulationStepper
from expense_forecast.ExpenseForecastResult import ExpenseForecastResult
from expense_forecast.MemoRuleSet import MemoRuleSet
from expense_forecast.MilestoneSet import MilestoneSet
from expense_forecast.ForecastHandler import ForecastHandler

import subprocess
import os

def simple_forecast_initial_conditions(path):
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

    E = ExpenseForecastInitialConditions(
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 3),
        account_set=A,
        budget_set=B,
        memo_rule_set=M,
        milestone_set=MS,
    )

    path = Path(path)
    path.write_text(json.dumps(E.to_dict(), indent=4))
    return path

class TestE2E:


    def test_cli_runs_simple_forecast(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            initial_conditions_path = temp_path / "initial_conditions.json"
            forecast_result_path = temp_path / "forecast_result.json"
            config_path = temp_path / "expense_forecast.conf"
            log_dir = temp_path / "log"
            log_dir.mkdir()

            simple_forecast_initial_conditions(initial_conditions_path)
            config_path.write_text("[default]\n")

            result = subprocess.run(
                [
                    "python3",
                    "-m",
                    "expense_forecast.ef_cli",
                    "run",
                    "forecast",
                    "--source",
                    "file",
                    "--ifile",
                    initial_conditions_path,
                    "--ofile",
                    forecast_result_path],
                cwd=temp_path,
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0
            assert forecast_result_path.exists()

    # TODO this could be pared down to a generate-report-only test
    def test_cli_run_forecast_and_generate_report(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            initial_conditions_path = temp_path / "initial_conditions.json"
            forecast_result_path = temp_path / "forecast_result.json"
            forecast_report_path = temp_path / "forecast_report.html"
            config_path = temp_path / "expense_forecast.conf"
            log_dir = temp_path / "log"
            log_dir.mkdir()

            simple_forecast_initial_conditions(initial_conditions_path)
            config_path.write_text("[default]\n")

            #assume working
            subprocess.run(
                [
                    "python3",
                    "-m",
                    "expense_forecast.ef_cli",
                    "run",
                    "forecast",
                    "--source",
                    "file",
                    "--ifile",
                    initial_conditions_path,
                    "--ofile",
                    forecast_result_path],
                cwd=temp_path,
                capture_output=True,
                text=True,
            )

            result = subprocess.run(
                [
                    "python3",
                    "-m",
                    "expense_forecast.ef_cli",
                    "report",
                    "forecast",
                    "--ifile",
                    forecast_result_path,
                    "--ofile",
                    forecast_report_path],
                cwd=temp_path,
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0
            assert forecast_report_path.exists()



    def test_cli_help_runs(self):
        result = subprocess.run(
            ["python3", "-m", "expense_forecast.ef_cli", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "usage" in result.stdout.lower()

    @pytest.mark.skip
    @pytest.mark.E2E
    def test_E2E_MVP(self):
        # got id from
        # (at project root) ef stage forecast --source file --filename ./tests/assets/e2e_mvp_forecast.json
        subprocess.run(["ef", "--source", "file", "--id", "TBD"])

    @pytest.mark.E2E
    def test_IRL(self):

        A = AccountSet()
        B = BudgetSet()
        M = MemoRuleSet()
        F = ForecastHandler()
        
        start_date = date(2026,7,4)
        end_date = date(2026,7,4) + datetime.timedelta(days=90)

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
        
        B.addBudgetItem(start_date=date(2026,9,1), end_date=end_date, priority=2,
                        cadence='monthly',amount=10_000,memo='extra cc payment',income_flag=False, 
                        deferrable=False, partial_payment_allowed=True)
        # phone
        # hulu
        # car insurance
        # storage

        B.addBudgetItem(start_date=income_start_date, end_date=end_date, priority=1,
                        cadence='semiweekly',amount=paycheck_amount,memo='CNA Income',income_flag=True, 
                        deferrable=False, partial_payment_allowed=False)
        M.addMemoRule(memo_regex='.*expense.*',
                    account_from='Chase',
                    account_to=None,
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

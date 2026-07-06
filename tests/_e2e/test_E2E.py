import pytest
import pandas as pd
from datetime import date
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
                    "initial_conditions.json",
                    "--ofile",
                    "forecast_result.json"],
                cwd=temp_path,
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0
            assert forecast_result_path.exists()

    # TODO this could be pared down to a generate-report-only test
    def test_cli_run_forecast_and_generate(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            initial_conditions_path = temp_path / "initial_conditions.json"
            forecast_result_path = temp_path / "forecast_result.json"
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
                    "initial_conditions.json",
                    "--ofile",
                    "forecast_result.json"],
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
                    "forecast_result.json",
                    "--ofile",
                    "forecast_report.json"],
                cwd=temp_path,
                capture_output=True,
                text=True,
            )



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

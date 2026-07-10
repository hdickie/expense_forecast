import pytest
from datetime import date
from expense_forecast.AccountSet import AccountSet
from expense_forecast.LineItemSet import BudgetSet
from expense_forecast.MemoRuleSet import MemoRuleSet
from expense_forecast.MilestoneSet import MilestoneSet
from expense_forecast.ExpenseForecastInitialConditions import ExpenseForecastInitialConditions
from expense_forecast.ExpenseForecastResult import ExpenseForecastResult
from expense_forecast.ForecastHandler import ForecastHandler

import pandas as pd

class TestExpenseForecastIntegration:
    pass
    
    def test_initial_conditions_round_trip_preserves_forecast_result(self):
        start_date = date(2026, 6, 1)
        end_date = date(2026, 6, 5)

        A = AccountSet()
        A.createCheckingAccount(
            name="Checking",
            balance=1000,
            min_balance=0,
            max_balance=float("inf"),
            primary_checking_ind=True,
        )

        B = BudgetSet()
        B.addBudgetItem(
            start_date=date(2026, 6, 2),
            end_date=date(2026, 6, 2),
            priority=1,
            interval="once",
            amount=100,
            memo="test expense",
        )

        M = MemoRuleSet()
        M.addMemoRule(
            memo_regex="test expense",
            account_from="Checking",
            account_to=None,
            transaction_priority=1,
        )

        MS = MilestoneSet()

        original_io = ExpenseForecastInitialConditions(
            start_date=start_date,
            end_date=end_date,
            account_set=A,
            budget_set=B,
            memo_rule_set=M,
            milestone_set=MS,
        )

        rebuilt_io = ExpenseForecastInitialConditions.initialize_from_dict(
            original_io.to_dict()
        )

        original_result = ForecastHandler().runForecast(
            original_io,
            MS,
            include_debug_columns=False,
        )

        rebuilt_result = ForecastHandler().runForecast(
            rebuilt_io,
            MS,
            include_debug_columns=False,
        )

        pd.testing.assert_frame_equal(
            original_result.forecast_df,
            rebuilt_result.forecast_df,
        )

    def test_expense_forecast_result_round_trip_preserves_forecast_result(self):

        start_date = date(2026, 6, 1)
        end_date = date(2026, 6, 5)

        A = AccountSet()
        A.createCheckingAccount(
            name="Checking",
            balance=1000,
            min_balance=0,
            max_balance=float("inf"),
            primary_checking_ind=True,
        )

        B = BudgetSet()
        B.addBudgetItem(
            start_date=date(2026, 6, 2),
            end_date=date(2026, 6, 2),
            priority=1,
            interval="once",
            amount=100,
            memo="test expense",
        )

        M = MemoRuleSet()
        M.addMemoRule(
            memo_regex="test expense",
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
            milestone_set=MS,
        )

        R = ForecastHandler().runForecast(
            E_IO,
            MS,
            include_debug_columns=True,
        )

        json_string = R.to_json_string()
        round_tripped_result = ExpenseForecastResult.initialize_from_json_string(json_string)

        pd.testing.assert_frame_equal(
            R.forecast_df,
            round_tripped_result.forecast_df,
            check_dtype=False,
        )


    ## Recommended interface
    # to_dict()
    # from_dict()

    # to_json()
    # from_json()

    # save_json(path)
    # load_json(path)

    # @pytest.mark.integration
    # @pytest.mark.skip(reason="not yet implemented")
    # def test_ExpenseForecast_to_json(self):
    #     pass

    # @pytest.mark.integration
    # @pytest.mark.skip(reason="not yet implemented")
    # def test_ExpenseForecast_from_json(self):
    #     pass

    # @pytest.mark.integration
    # @pytest.mark.skip(reason="not yet implemented")
    # def test_ExpenseForecast_to_excel(self):
    #     pass

    # @pytest.mark.integration
    # @pytest.mark.skip(reason="not yet implemented")
    # def test_ExpenseForecast_from_excel(self):
    #     pass

    # @pytest.mark.integration
    # @pytest.mark.skip(reason="not yet implemented")
    # def test_ExpenseForecast_to_database(self):
    #     pass

    # @pytest.mark.integration
    # @pytest.mark.skip(reason="not yet implemented")
    # def test_ExpenseForecast_from_database(self):
    #     pass

    # @pytest.mark.integration
    # @pytest.mark.skip(reason="not yet implemented")
    # def test_ExpenseForecast_to_csv(self):
    #     pass

    # @pytest.mark.integration
    # @pytest.mark.skip(reason="not yet implemented")
    # def test_ExpenseForecast_from_csv(self):
    #     pass

    # @pytest.mark.integration
    # @pytest.mark.skip(reason="not yet implemented")
    # def test_ExpenseForecast_log_output(self):
    #     pass

    # @pytest.mark.integration
    # @pytest.mark.skip(reason="not yet implemented")
    # def test_ExpenseForecast_interactions_w_API_Client_object(self):
    #     pass

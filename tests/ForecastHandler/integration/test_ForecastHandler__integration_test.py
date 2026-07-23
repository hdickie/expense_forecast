import pytest
from datetime import date
from expense_forecast.AccountSet import AccountSet
from expense_forecast.LineItemSet import LineItemSet
from expense_forecast.MemoRuleSet import MemoRuleSet
from expense_forecast.MilestoneSet import MilestoneSet
from expense_forecast.ExpenseForecastInitialConditions import ExpenseForecastInitialConditions
from expense_forecast.ExpenseForecastResult import ExpenseForecastResult
from expense_forecast.ForecastHandler import ForecastHandler, logger as forecast_logger
import logging
import datetime

import pandas as pd

class TestForecastHandler:

    # Note that debug true and debug false cases produce the same output and that is correct
    @pytest.mark.integration
    def test_ForecastHandler__debug_t_and_f__checking_only(self):
        start_date = date(2026,6,1)
        end_date = date(2026,6,10)
        
        A = AccountSet()
        B = LineItemSet()
        M = MemoRuleSet()
        MS = MilestoneSet()

        A.createCheckingAccount(
            name="Checking",
            balance=1000,
            min_balance=0,
            max_balance=float("inf"),
            primary_checking_ind=True,
        )

        MS = MilestoneSet()

        E_IO = ExpenseForecastInitialConditions(
            start_date=start_date,
            end_date=end_date,
            account_set=A,
            line_item_set=B,
            memo_rule_set=M,
            milestone_set=MS)
        
        
        
        expected_final = pd.DataFrame(
            {
                "Date": [date(2026,6,10)],
                "Checking": [1000.0],
                "Interest Accrued": [0.0],
                "Investment Returns": [0.0],
                "Net Gain": [0.0],
                "Net Loss": [0.0],
                "Net Worth": [1000.0],
                "Loan Total": [0.0],
                "CC Debt Total": [0.0],  
                "Liquid Total": [1000.0],
                "Next Income Date": [""],
                "Memo Directives": [""],
                "Memo": [""]
            }
        )
        expected_final.index = [9]


        ### Debug True Case
        R__debug_true = ForecastHandler().runForecast(E_IO, MS, include_debug_columns=True)

        assert isinstance(R__debug_true, ExpenseForecastResult)
        assert isinstance(R__debug_true.forecast_df, pd.DataFrame)

        required_columns__debug_true_case = {
            "Date",
            "Checking",
            "Interest Accrued",
            "Investment Returns",
            "Net Gain",
            "Net Loss",
            "Net Worth",
            "Loan Total",
            "CC Debt Total",
            "Liquid Total",
            "Next Income Date",
            "Memo Directives",
            "Memo",
        }

        actual_columns__debug_true_case = set(R__debug_true.forecast_df.columns)

        missing__debug_true_case = required_columns__debug_true_case - actual_columns__debug_true_case
        unexpected__debug_true_case = actual_columns__debug_true_case - required_columns__debug_true_case

        assert actual_columns__debug_true_case == required_columns__debug_true_case, (
            "Forecast dataframe columns did not match.\n"
            f"Missing columns:    {sorted(missing__debug_true_case)}\n"
            f"Unexpected columns: {sorted(unexpected__debug_true_case)}\n"
            f"Actual columns:     {list(R__debug_true.forecast_df.columns)}"
        )

        assert R__debug_true.forecast_df.shape[0] == 10
        assert R__debug_true.forecast_df.shape[1] == 13

        pd.testing.assert_frame_equal(
            R__debug_true.forecast_df.tail(1),
            expected_final,
        )


        ### Debug False Case
        R__debug_false = ForecastHandler().runForecast(E_IO, MS, include_debug_columns=False)

        assert isinstance(R__debug_false, ExpenseForecastResult)
        assert isinstance(R__debug_false.forecast_df, pd.DataFrame)

        required_columns__debug_false_case = {
            "Date",
            "Checking",
            "Interest Accrued",
            "Investment Returns",
            "Net Gain",
            "Net Loss",
            "Net Worth",
            "Loan Total",
            "CC Debt Total",
            "Liquid Total",
            "Next Income Date",
            "Memo Directives",
            "Memo",
        }

        actual_columns__debug_false_case = set(R__debug_false.forecast_df.columns)

        missing__debug_false_case = required_columns__debug_false_case - actual_columns__debug_false_case
        unexpected__debug_false_case = actual_columns__debug_false_case - required_columns__debug_false_case

        assert actual_columns__debug_false_case == required_columns__debug_false_case, (
            "Forecast dataframe columns did not match.\n"
            f"Missing columns:    {sorted(missing__debug_false_case)}\n"
            f"Unexpected columns: {sorted(unexpected__debug_false_case)}\n"
            f"Actual columns:     {list(R__debug_false.forecast_df.columns)}"
        )

        assert R__debug_false.forecast_df.shape[0] == 10
        assert R__debug_false.forecast_df.shape[1] == 13

        pd.testing.assert_frame_equal(
            R__debug_false.forecast_df.tail(1),
            expected_final,
        )

    @pytest.mark.integration
    def test_ForecastHandler__debug_t_and_f__checking_and_credit__no_cc_bal(self):
        start_date = date(2026,6,1)
        end_date = date(2026,6,5)
        
        A = AccountSet()
        B = LineItemSet()
        M = MemoRuleSet()
        MS = MilestoneSet()

        A.createCheckingAccount(
            name="Checking",
            balance=1000,
            min_balance=0,
            max_balance=float("inf"),
            primary_checking_ind=True,
        )

        A.createCreditCardAccount(
            name="Credit",
            current_statement_balance=0, 
            previous_statement_balance=0, 
            min_balance=0, 
            max_balance=25_000,
            billing_start_date=date(2020,1,7), 
            apr=0.28, 
            minimum_payment=40, 
            end_of_previous_cycle_balance=0
        )  

        MS = MilestoneSet()

        E_IO = ExpenseForecastInitialConditions(
            start_date=start_date,
            end_date=end_date,
            account_set=A,
            line_item_set=B,
            memo_rule_set=M,
            milestone_set=MS)
        
        
        ### Debug True Case
        expected_final__debug_true = pd.DataFrame(
            {
                "Date": [date(2026,6,5)],
                "Checking": [1000.0],
                "Credit": [0.0],
                "Credit: Curr Stmt Bal": [0.0],
                "Credit: Prev Stmt Bal": [0.0],
                "Credit: Credit Billing Cycle Payment Bal": [0.0],
                "Credit: Credit End of Prev Cycle Bal": [0.0],
                "Interest Accrued": [0.0],
                "Investment Returns": [0.0],
                "Net Gain": [0.0],
                "Net Loss": [0.0],
                "Net Worth": [1000.0],
                "Loan Total": [0.0],
                "CC Debt Total": [0.0],
                "Liquid Total": [1000.0],
                "Next Income Date": [""],
                "Memo Directives": [""],
                "Memo": [""]
            }
        )
        expected_final__debug_true.index = [4]

        R__debug_true = ForecastHandler().runForecast(E_IO, MS, include_debug_columns=True)

        assert isinstance(R__debug_true, ExpenseForecastResult)
        assert isinstance(R__debug_true.forecast_df, pd.DataFrame)

        required_columns__debug_true_case = {
            "Date",
            "Checking",
            "Credit",
            "Credit: Curr Stmt Bal",
            "Credit: Prev Stmt Bal",
            "Credit: Credit Billing Cycle Payment Bal",
            "Credit: Credit End of Prev Cycle Bal",
            "Interest Accrued",
            "Investment Returns",
            "Net Gain",
            "Net Loss",
            "Net Worth",
            "Loan Total",
            "CC Debt Total",
            "Liquid Total",
            "Next Income Date",
            "Memo Directives",
            "Memo",
        }

        actual_columns__debug_true_case = set(R__debug_true.forecast_df.columns)

        missing__debug_true_case = required_columns__debug_true_case - actual_columns__debug_true_case
        unexpected__debug_true_case = actual_columns__debug_true_case - required_columns__debug_true_case

        assert actual_columns__debug_true_case == required_columns__debug_true_case, (
            "Forecast dataframe columns did not match.\n"
            f"Missing columns:    {sorted(missing__debug_true_case)}\n"
            f"Unexpected columns: {sorted(unexpected__debug_true_case)}\n"
            f"Actual columns:     {list(R__debug_true.forecast_df.columns)}"
        )

        assert R__debug_true.forecast_df.shape[0] == 5
        assert R__debug_true.forecast_df.shape[1] == 18

        pd.testing.assert_frame_equal(
            R__debug_true.forecast_df.tail(1),
            expected_final__debug_true,
        )


        ### Debug False Case
        expected_final__debug_false = pd.DataFrame(
            {
                "Date": [date(2026,6,5)],
                "Checking": [1000.0],
                "Credit": [0.0],
                "Interest Accrued": [0.0],
                "Investment Returns": [0.0],
                "Net Gain": [0.0],
                "Net Loss": [0.0],
                "Net Worth": [1000.0],
                "Loan Total": [0.0],
                "CC Debt Total": [0.0],
                "Liquid Total": [1000.0],
                "Next Income Date": [""],
                "Memo Directives": [""],
                "Memo": [""]
            }
        )
        expected_final__debug_false.index = [4]

        R__debug_false = ForecastHandler().runForecast(E_IO, MS, include_debug_columns=False) #TODO an error here bc debug columns still coming through when they shouldn't

        assert isinstance(R__debug_false, ExpenseForecastResult)
        assert isinstance(R__debug_false.forecast_df, pd.DataFrame)

        required_columns__debug_false_case = {
            "Date",
            "Checking",
            "Credit",
            "Interest Accrued",
            "Investment Returns",
            "Net Gain",
            "Net Loss",
            "Net Worth",
            "Loan Total",
            "CC Debt Total",
            "Liquid Total",
            "Next Income Date",
            "Memo Directives",
            "Memo",
        }

        actual_columns__debug_false_case = set(R__debug_false.forecast_df.columns)

        missing__debug_false_case = required_columns__debug_false_case - actual_columns__debug_false_case
        unexpected__debug_false_case = actual_columns__debug_false_case - required_columns__debug_false_case

        assert actual_columns__debug_false_case == required_columns__debug_false_case, (
            "Forecast dataframe columns did not match.\n"
            f"Missing columns:    {sorted(missing__debug_false_case)}\n"
            f"Unexpected columns: {sorted(unexpected__debug_false_case)}\n"
            f"Actual columns:     {list(R__debug_false.forecast_df.columns)}"
        )

        assert R__debug_false.forecast_df.shape[0] == 5
        assert R__debug_false.forecast_df.shape[1] == 14

        pd.testing.assert_frame_equal(
            R__debug_false.forecast_df.tail(1),
            expected_final__debug_false,
        )

    # No interest accrual occurs because the first billing date for the loan is past the end of the forecast
    @pytest.mark.integration
    def test_ForecastHandler__debug_t_and_f__checking_and_loan__no_loan_interest_accrual(self):
        start_date = date(2026,6,1)
        end_date = date(2026,6,5)
        
        A = AccountSet()
        B = LineItemSet()
        M = MemoRuleSet()
        MS = MilestoneSet()

        A.createCheckingAccount(
            name="Checking",
            balance=1000,
            min_balance=0,
            max_balance=float("inf"),
            primary_checking_ind=True,
        )

        A.createLoanAccount(
            name="Loan", 
            principal_balance=15_000, 
            interest_balance=500, 
            min_balance=0, 
            max_balance=25_000, 
            billing_start_date=date(2030,1,3),
            apr=0.07, 
            minimum_payment=212.00, 
            billing_cycle_payment_balance=0,
        )

        MS = MilestoneSet()

        E_IO = ExpenseForecastInitialConditions(
            start_date=start_date,
            end_date=end_date,
            account_set=A,
            line_item_set=B,
            memo_rule_set=M,
            milestone_set=MS)
        
        
        ### Debug True Case
        expected_final__debug_true = pd.DataFrame(
            {
                "Date": [date(2026,6,5)],
                "Checking": [1000.0],
                "Loan": [15500.0],
                "Loan: Principal Balance": [15000.0],
                "Loan: Interest": [500.0],
                "Loan: Loan Billing Cycle Payment Bal": [0.0],
                "Interest Accrued": [0.0],
                "Investment Returns": [0.0],
                "Net Gain": [0.0],
                "Net Loss": [0.0],
                "Net Worth": [-14500.0],
                "Loan Total": [15500.0],
                "CC Debt Total": [0.0],
                "Liquid Total": [1000.0],
                "Next Income Date": [""],
                "Memo Directives": [""],
                "Memo": [""]
            }
        )
        expected_final__debug_true.index = [4]

        R__debug_true = ForecastHandler().runForecast(E_IO, MS, include_debug_columns=True)

        assert isinstance(R__debug_true, ExpenseForecastResult)
        assert isinstance(R__debug_true.forecast_df, pd.DataFrame)

        required_columns__debug_true_case = {
            "Date",
            "Checking",
            "Loan",
            "Loan: Principal Balance",
            "Loan: Interest",
            "Loan: Loan Billing Cycle Payment Bal",
            "Interest Accrued",
            "Investment Returns",
            "Net Gain",
            "Net Loss",
            "Net Worth",
            "Loan Total",
            "CC Debt Total",
            "Liquid Total",
            "Next Income Date",
            "Memo Directives",
            "Memo",
        }

        actual_columns__debug_true_case = set(R__debug_true.forecast_df.columns)

        missing__debug_true_case = required_columns__debug_true_case - actual_columns__debug_true_case
        unexpected__debug_true_case = actual_columns__debug_true_case - required_columns__debug_true_case

        assert actual_columns__debug_true_case == required_columns__debug_true_case, (
            "Forecast dataframe columns did not match.\n"
            f"Missing columns:    {sorted(missing__debug_true_case)}\n"
            f"Unexpected columns: {sorted(unexpected__debug_true_case)}\n"
            f"Actual columns:     {list(R__debug_true.forecast_df.columns)}"
        )

        assert R__debug_true.forecast_df.shape[0] == 5
        assert R__debug_true.forecast_df.shape[1] == 17

        pd.testing.assert_frame_equal(
            R__debug_true.forecast_df.tail(1),
            expected_final__debug_true,
        )


        ### Debug False Case
        expected_final__debug_false = pd.DataFrame(
            {
                "Date": [date(2026,6,5)],
                "Checking": [1000.0],
                "Loan": [15500.0],
                "Interest Accrued": [0.0],
                "Investment Returns": [0.0],
                "Net Gain": [0.0],
                "Net Loss": [0.0],
                "Net Worth": [-14500.0],
                "Loan Total": [15500.0],
                "CC Debt Total": [0.0],
                "Liquid Total": [1000.0],
                "Next Income Date": [""],
                "Memo Directives": [""],
                "Memo": [""]
            }
        )
        expected_final__debug_false.index = [4]

        R__debug_false = ForecastHandler().runForecast(E_IO, MS, include_debug_columns=False) #TODO an error here bc debug columns still coming through when they shouldn't

        assert isinstance(R__debug_false, ExpenseForecastResult)
        assert isinstance(R__debug_false.forecast_df, pd.DataFrame)

        required_columns__debug_false_case = {
            "Date",
            "Checking",
            "Loan",
            "Interest Accrued",
            "Investment Returns",
            "Net Gain",
            "Net Loss",
            "Net Worth",
            "Loan Total",
            "CC Debt Total",
            "Liquid Total",
            "Next Income Date",
            "Memo Directives",
            "Memo",
        }

        actual_columns__debug_false_case = set(R__debug_false.forecast_df.columns)

        missing__debug_false_case = required_columns__debug_false_case - actual_columns__debug_false_case
        unexpected__debug_false_case = actual_columns__debug_false_case - required_columns__debug_false_case

        assert actual_columns__debug_false_case == required_columns__debug_false_case, (
            "Forecast dataframe columns did not match.\n"
            f"Missing columns:    {sorted(missing__debug_false_case)}\n"
            f"Unexpected columns: {sorted(unexpected__debug_false_case)}\n"
            f"Actual columns:     {list(R__debug_false.forecast_df.columns)}"
        )

        assert R__debug_false.forecast_df.shape[0] == 5
        assert R__debug_false.forecast_df.shape[1] == 14

        pd.testing.assert_frame_equal(
            R__debug_false.forecast_df.tail(1),
            expected_final__debug_false,
        )


    @pytest.mark.integration
    def test_ForecastHandler__checking_and_credit__min_cc_payment(self):
        start_date = date(2026,6,1)
        end_date = date(2026,6,5)
        
        A = AccountSet()
        B = LineItemSet()
        M = MemoRuleSet()
        MS = MilestoneSet()

        A.createCheckingAccount(
            name="Checking",
            balance=1000,
            min_balance=0,
            max_balance=float("inf"),
            primary_checking_ind=True,
        )

        A.createCreditCardAccount(
            name="Credit",
            current_statement_balance=0, 
            previous_statement_balance=1000, 
            min_balance=0, 
            max_balance=25_000,
            billing_start_date=date(2026,6,3), 
            apr=0.28, 
            minimum_payment=40, 
            end_of_previous_cycle_balance=1000
        )  

        MS = MilestoneSet()

        E_IO = ExpenseForecastInitialConditions(
            start_date=start_date,
            end_date=end_date,
            account_set=A,
            line_item_set=B,
            memo_rule_set=M,
            milestone_set=MS)
        
        expected_billing_date_state = pd.DataFrame(
            {
                "Date": [date(2026,6,3)],
                "Checking": [960.0],
                "Credit": [983.33],
                "Credit: Curr Stmt Bal": [0.0],
                "Credit: Prev Stmt Bal": [983.33],
                "Credit: Credit Billing Cycle Payment Bal": [0.0],
                "Credit: Credit End of Prev Cycle Bal": [1000.0], #this doesn't change until the next day, and i think that's correct
                "Interest Accrued": [23.33],
                "Investment Returns": [0.0],
                "Net Gain": [0.0],
                "Net Loss": [23.33],
                "Net Worth": [-23.33],
                "Loan Total": [0.0],
                "CC Debt Total": [983.33],
                "Liquid Total": [960.0],
                "Next Income Date": [""],
                "Memo Directives": ["CC INTEREST (Credit: Prev Stmt Bal +$23.33); CC MIN PAYMENT (Credit: Prev Stmt Bal -$40.00); CC MIN PAYMENT (Checking -$40.00)"],
                "Memo": [""]
            }
        )
        expected_billing_date_state.index = [2]

        expected_final = pd.DataFrame(
            {
                "Date": [date(2026,6,5)],
                "Checking": [960.0],
                "Credit": [983.33],
                "Credit: Curr Stmt Bal": [0.0],
                "Credit: Prev Stmt Bal": [983.33],
                "Credit: Credit Billing Cycle Payment Bal": [0.0],
                "Credit: Credit End of Prev Cycle Bal": [983.33],
                "Interest Accrued": [0.0],
                "Investment Returns": [0.0],
                "Net Gain": [0.0],
                "Net Loss": [0.0],
                "Net Worth": [-23.33],
                "Loan Total": [0.0],
                "CC Debt Total": [983.33],
                "Liquid Total": [960.0],
                "Next Income Date": [""],
                "Memo Directives": [""],
                "Memo": [""]
            }
        )
        expected_final.index = [4]



        R = ForecastHandler().runForecast(E_IO, MS, include_debug_columns=True)

        assert R.forecast_df.shape[0] == 5

        pd.testing.assert_frame_equal(
            R.forecast_df.iloc[[2]], 
            expected_billing_date_state,
        )

        pd.testing.assert_frame_equal(
            R.forecast_df.tail(1),
            expected_final,
        )    

    def _run_checking_and_credit_min_payment_case(
        self,
        expected_billing_date_state,
        expected_final,
        previous_statement_balance=1000.0,
        checking_balance=1000.0,
        payment_date=None,
        payment_amount=None,
        minimum_payment=40.0,
    ):
        start_date = date(2026,6,1)
        end_date = date(2026,6,5)

        A = AccountSet()
        B = LineItemSet()
        M = MemoRuleSet()
        MS = MilestoneSet()

        A.createCheckingAccount(
            name="Checking",
            balance=checking_balance,
            min_balance=0,
            max_balance=float("inf"),
            primary_checking_ind=True,
        )

        A.createCreditCardAccount(
            name="Credit",
            current_statement_balance=0,
            previous_statement_balance=previous_statement_balance,
            min_balance=0,
            max_balance=25_000,
            billing_start_date=date(2026,6,3),
            apr=0.28,
            minimum_payment=minimum_payment,
            end_of_previous_cycle_balance=previous_statement_balance,
        )

        if payment_date is not None:
            B.addLineItem(
                start_date=payment_date,
                end_date=payment_date,
                priority=1,
                interval="once",
                amount=payment_amount,
                memo="credit payment",
                income_flag=False,
                deferrable=False,
                partial_payment_allowed=False,
            )

            M.addMemoRule(
                memo_regex="credit payment",
                account_from="Checking",
                account_to="Credit",
                transaction_priority=1,
            )

        E_IO = ExpenseForecastInitialConditions(
            start_date=start_date,
            end_date=end_date,
            account_set=A,
            line_item_set=B,
            memo_rule_set=M,
            milestone_set=MS,
        )

        R = ForecastHandler().runForecast(E_IO, MS, include_debug_columns=True)

        assert R.forecast_df.shape[0] == 5

        if payment_date == date(2026, 6, 3):
            additional_payment_directives = (
                f"ADDTL CC PAYMENT (Credit -${payment_amount:.2f})"
            )
            existing_directives = expected_billing_date_state.loc[
                expected_billing_date_state.index[0], "Memo Directives"
            ]
            expected_billing_date_state.loc[
                expected_billing_date_state.index[0], "Memo Directives"
            ] = (
                f"{existing_directives}; {additional_payment_directives}"
                if existing_directives
                else additional_payment_directives
            )

        pd.testing.assert_frame_equal(
            R.forecast_df.iloc[[2]],
            expected_billing_date_state,
        )

        pd.testing.assert_frame_equal(
            R.forecast_df.tail(1),
            expected_final,
        )

    def _credit_expected_rows_with_placeholders(self):
        expected_billing_date_state = pd.DataFrame(
            {
                "Date": [date(2026,6,3)],
                "Checking": [None],
                "Credit": [None],
                "Credit: Curr Stmt Bal": [None],
                "Credit: Prev Stmt Bal": [None],
                "Credit: Credit Billing Cycle Payment Bal": [None],
                "Credit: Credit End of Prev Cycle Bal": [None],
                "Interest Accrued": [None],
                "Investment Returns": [0.0],
                "Net Gain": [0.0],
                "Net Loss": [None],
                "Net Worth": [None],
                "Loan Total": [0.0],
                "CC Debt Total": [None],
                "Liquid Total": [None],
                "Next Income Date": [""],
                "Memo Directives": [None],
                "Memo": [""],
            }
        )
        expected_billing_date_state.index = [2]

        expected_final = pd.DataFrame(
            {
                "Date": [date(2026,6,5)],
                "Checking": [None],
                "Credit": [None],
                "Credit: Curr Stmt Bal": [None],
                "Credit: Prev Stmt Bal": [None],
                "Credit: Credit Billing Cycle Payment Bal": [None],
                "Credit: Credit End of Prev Cycle Bal": [None],
                "Interest Accrued": [None],
                "Investment Returns": [0.0],
                "Net Gain": [0.0],
                "Net Loss": [None],
                "Net Worth": [None],
                "Loan Total": [0.0],
                "CC Debt Total": [None],
                "Liquid Total": [None],
                "Next Income Date": [""],
                "Memo Directives": [None],
                "Memo": [""],
            }
        )
        expected_final.index = [4]

        return expected_billing_date_state, expected_final

    def _fill_credit_expected_rows(
        self,
        expected_billing_date_state,
        expected_final,
        checking,
        credit,
        billing_cycle_payment_balance,
        billing_date_end_of_previous_cycle_balance,
        final_end_of_previous_cycle_balance,
        marginal_interest,
        memo_directives,
    ):
        expected_billing_date_state["Checking"] = checking
        expected_billing_date_state["Credit"] = credit
        expected_billing_date_state["Credit: Curr Stmt Bal"] = 0.0
        expected_billing_date_state["Credit: Prev Stmt Bal"] = credit
        expected_billing_date_state["Credit: Credit Billing Cycle Payment Bal"] = (
            billing_cycle_payment_balance
        )
        expected_billing_date_state["Credit: Credit End of Prev Cycle Bal"] = (
            billing_date_end_of_previous_cycle_balance
        )
        expected_billing_date_state["Interest Accrued"] = marginal_interest
        expected_billing_date_state["Investment Returns"] = 0.0
        expected_billing_date_state["Net Gain"] = 0.0
        expected_billing_date_state["Net Loss"] = marginal_interest
        expected_billing_date_state["Net Worth"] = checking - credit
        expected_billing_date_state["Loan Total"] = 0.0
        expected_billing_date_state["CC Debt Total"] = credit
        expected_billing_date_state["Liquid Total"] = checking
        expected_billing_date_state["Memo Directives"] = memo_directives
        expected_billing_date_state["Memo"] = ""

        expected_final["Checking"] = checking
        expected_final["Credit"] = credit
        expected_final["Credit: Curr Stmt Bal"] = 0.0
        expected_final["Credit: Prev Stmt Bal"] = credit
        expected_final["Credit: Credit Billing Cycle Payment Bal"] = (
            billing_cycle_payment_balance
        )
        expected_final["Credit: Credit End of Prev Cycle Bal"] = (
            final_end_of_previous_cycle_balance
        )
        expected_final["Interest Accrued"] = 0.0
        expected_final["Investment Returns"] = 0.0
        expected_final["Net Gain"] = 0.0
        expected_final["Net Loss"] = 0.0
        expected_final["Net Worth"] = checking - credit
        expected_final["Loan Total"] = 0.0
        expected_final["CC Debt Total"] = credit
        expected_final["Liquid Total"] = checking
        expected_final["Memo Directives"] = ""
        expected_final["Memo"] = ""

    def _run_checking_and_loan_min_payment_case(
        self,
        expected_billing_date_state,
        expected_final,
        principal_balance=1000.0,
        checking_balance=1000.0,
        payment_date=None,
        payment_amount=None,
        minimum_payment=40.0,
    ):
        start_date = date(2026,6,1)
        end_date = date(2026,6,5)

        A = AccountSet()
        B = LineItemSet()
        M = MemoRuleSet()
        MS = MilestoneSet()

        A.createCheckingAccount(
            name="Checking",
            balance=checking_balance,
            min_balance=0,
            max_balance=float("inf"),
            primary_checking_ind=True,
        )

        A.createLoanAccount(
            name="Loan",
            principal_balance=principal_balance,
            interest_balance=0.0,
            min_balance=0,
            max_balance=25_000,
            billing_start_date=date(2026,6,3),
            apr=0.07305,
            minimum_payment=minimum_payment,
            billing_cycle_payment_balance=0,
        )

        if payment_date is not None:
            B.addLineItem(
                start_date=payment_date,
                end_date=payment_date,
                priority=1,
                interval="once",
                amount=payment_amount,
                memo="loan payment",
                income_flag=False,
                deferrable=False,
                partial_payment_allowed=False,
            )

            M.addMemoRule(
                memo_regex="loan payment",
                account_from="Checking",
                account_to="Loan",
                transaction_priority=1,
            )

        E_IO = ExpenseForecastInitialConditions(
            start_date=start_date,
            end_date=end_date,
            account_set=A,
            line_item_set=B,
            memo_rule_set=M,
            milestone_set=MS,
        )

        R = ForecastHandler().runForecast(E_IO, MS, include_debug_columns=True)

        assert R.forecast_df.shape[0] == 5

        pd.testing.assert_frame_equal(
            R.forecast_df.iloc[[2]],
            expected_billing_date_state,
        )

        pd.testing.assert_frame_equal(
            R.forecast_df.tail(1),
            expected_final,
        )

    @pytest.mark.integration
    def test_ForecastHandler__all_loans_budget_payment(self):
        start_date = date(2026,6,1)
        end_date = date(2026,6,3)

        A = AccountSet()
        B = LineItemSet()
        M = MemoRuleSet()
        MS = MilestoneSet()

        A.createCheckingAccount(
            name="Checking",
            balance=1000.0,
            min_balance=0,
            max_balance=float("inf"),
            primary_checking_ind=True,
        )
        A.createLoanAccount(
            name="Loan A",
            principal_balance=1000.0,
            interest_balance=10.0,
            min_balance=0,
            max_balance=2000.0,
            billing_start_date=date(2026,6,1),
            apr=0.1,
            minimum_payment=40.0,
            billing_cycle_payment_balance=0,
        )
        A.createLoanAccount(
            name="Loan B",
            principal_balance=1000.0,
            interest_balance=10.0,
            min_balance=0,
            max_balance=2000.0,
            billing_start_date=date(2026,6,1),
            apr=0.05,
            minimum_payment=40.0,
            billing_cycle_payment_balance=0,
        )

        B.addLineItem(
            start_date=date(2026,6,2),
            end_date=date(2026,6,2),
            priority=1,
            interval="once",
            amount=100.0,
            memo="extra loan payment",
            income_flag=False,
            deferrable=False,
            partial_payment_allowed=False,
        )
        M.addMemoRule(
            memo_regex="extra loan payment",
            account_from="Checking",
            account_to="ALL_LOANS",
            transaction_priority=1,
        )

        R = ForecastHandler().runForecast(
            ExpenseForecastInitialConditions(
                start_date=start_date,
                end_date=end_date,
                account_set=A,
                line_item_set=B,
                memo_rule_set=M,
                milestone_set=MS,
            ),
            MS,
            include_debug_columns=True,
        )

        payment_day = R.forecast_df[R.forecast_df.Date == date(2026,6,2)].iloc[0]
        assert payment_day["Checking"] == pytest.approx(900.0)
        assert payment_day["Loan A"] == pytest.approx(910.27, abs=0.01)
        assert payment_day["Loan B"] == pytest.approx(1010.14, abs=0.01)
        assert "ADDTL LOAN PAYMENT (Loan A -$100.00)" in payment_day["Memo Directives"]

    def _loan_expected_rows_with_placeholders(self):
        expected_billing_date_state = pd.DataFrame(
            {
                "Date": [date(2026,6,3)],
                "Checking": [None],
                "Loan": [None],
                "Loan: Principal Balance": [None],
                "Loan: Interest": [None],
                "Loan: Loan Billing Cycle Payment Bal": [None],
                "Interest Accrued": [None],
                "Investment Returns": [0.0],
                "Net Gain": [0.0],
                "Net Loss": [None],
                "Net Worth": [None],
                "Loan Total": [None],
                "CC Debt Total": [0.0],
                "Liquid Total": [None],
                "Next Income Date": [""],
                "Memo Directives": [None],
                "Memo": [""],
            }
        )
        expected_billing_date_state.index = [2]

        expected_final = pd.DataFrame(
            {
                "Date": [date(2026,6,5)],
                "Checking": [None],
                "Loan": [None],
                "Loan: Principal Balance": [None],
                "Loan: Interest": [None],
                "Loan: Loan Billing Cycle Payment Bal": [None],
                "Interest Accrued": [0.0],
                "Investment Returns": [0.0],
                "Net Gain": [0.0],
                "Net Loss": [0.0],
                "Net Worth": [None],
                "Loan Total": [None],
                "CC Debt Total": [0.0],
                "Liquid Total": [None],
                "Next Income Date": [""],
                "Memo Directives": [""],
                "Memo": [""],
            }
        )
        expected_final.index = [4]

        return expected_billing_date_state, expected_final

    def _fill_loan_expected_rows(
        self,
        expected_billing_date_state,
        expected_final,
        checking,
        loan,
        principal_balance,
        interest_balance,
        billing_cycle_payment_balance,
        marginal_interest,
        memo_directives,
        final_loan=None,
        final_principal_balance=None,
        final_interest_balance=None,
        final_marginal_interest=0.0,
        final_net_loss=0.0,
        final_memo_directives="",
    ):
        final_loan = loan if final_loan is None else final_loan
        final_principal_balance = (
            principal_balance
            if final_principal_balance is None
            else final_principal_balance
        )
        final_interest_balance = (
            interest_balance if final_interest_balance is None else final_interest_balance
        )

        expected_billing_date_state["Checking"] = checking
        expected_billing_date_state["Loan"] = loan
        expected_billing_date_state["Loan: Principal Balance"] = principal_balance
        expected_billing_date_state["Loan: Interest"] = interest_balance
        expected_billing_date_state["Loan: Loan Billing Cycle Payment Bal"] = (
            billing_cycle_payment_balance
        )
        expected_billing_date_state["Interest Accrued"] = marginal_interest
        expected_billing_date_state["Investment Returns"] = 0.0
        expected_billing_date_state["Net Gain"] = 0.0
        expected_billing_date_state["Net Loss"] = marginal_interest
        expected_billing_date_state["Net Worth"] = checking - loan
        expected_billing_date_state["Loan Total"] = loan
        expected_billing_date_state["CC Debt Total"] = 0.0
        expected_billing_date_state["Liquid Total"] = checking
        expected_billing_date_state["Memo Directives"] = memo_directives
        expected_billing_date_state["Memo"] = ""

        expected_final["Checking"] = checking
        expected_final["Loan"] = final_loan
        expected_final["Loan: Principal Balance"] = final_principal_balance
        expected_final["Loan: Interest"] = final_interest_balance
        expected_final["Loan: Loan Billing Cycle Payment Bal"] = (
            billing_cycle_payment_balance
        )
        expected_final["Interest Accrued"] = final_marginal_interest
        expected_final["Investment Returns"] = 0.0
        expected_final["Net Gain"] = 0.0
        expected_final["Net Loss"] = final_net_loss
        expected_final["Net Worth"] = checking - final_loan
        expected_final["Loan Total"] = final_loan
        expected_final["CC Debt Total"] = 0.0
        expected_final["Liquid Total"] = checking
        expected_final["Memo Directives"] = final_memo_directives
        expected_final["Memo"] = ""

    @pytest.mark.integration
    def test_ForecastHandler__checking_and_credit__min_cc_payment_gt_default(self):
        expected_billing_date_state, expected_final = self._credit_expected_rows_with_placeholders()
        
        checking = 1000.0
        prev_stmt_bal = 3000.0
        expected_min_payment = 100.0
        expected_interest = 70.0

        expected_billing_date_state["Checking"] = checking - expected_min_payment
        expected_billing_date_state["Credit"] = prev_stmt_bal - expected_min_payment + expected_interest
        expected_billing_date_state["Credit: Curr Stmt Bal"] = 0.0
        expected_billing_date_state["Credit: Prev Stmt Bal"] = prev_stmt_bal - expected_min_payment + expected_interest
        expected_billing_date_state["Credit: Credit Billing Cycle Payment Bal"] = 0.0
        expected_billing_date_state["Credit: Credit End of Prev Cycle Bal"] = prev_stmt_bal #payment is added next day
        expected_billing_date_state["Interest Accrued"] = expected_interest
        expected_billing_date_state["Investment Returns"] = 0.0
        expected_billing_date_state["Net Gain"] = 0.0
        expected_billing_date_state["Net Loss"] = expected_interest
        expected_billing_date_state["Net Worth"] = checking - prev_stmt_bal - expected_interest
        expected_billing_date_state["Loan Total"] = 0.0
        expected_billing_date_state["CC Debt Total"] = prev_stmt_bal - expected_min_payment + expected_interest
        expected_billing_date_state["Liquid Total"] = checking - expected_min_payment
        expected_billing_date_state["Memo Directives"] = "CC INTEREST (Credit: Prev Stmt Bal +$70.00); CC MIN PAYMENT (Credit: Prev Stmt Bal -$100.00); CC MIN PAYMENT (Checking -$100.00)"
        expected_billing_date_state["Memo"] = ""

        expected_final["Checking"] = checking - expected_min_payment
        expected_final["Credit"] = prev_stmt_bal - expected_min_payment + expected_interest
        expected_final["Credit: Curr Stmt Bal"] = 0.0
        expected_final["Credit: Prev Stmt Bal"] = prev_stmt_bal - expected_min_payment + expected_interest
        expected_final["Credit: Credit Billing Cycle Payment Bal"] = 0.0
        expected_final["Credit: Credit End of Prev Cycle Bal"] = prev_stmt_bal - expected_min_payment + expected_interest
        expected_final["Interest Accrued"] = 0.0
        expected_final["Investment Returns"] = 0.0
        expected_final["Net Gain"] = 0.0
        expected_final["Net Loss"] = 0.0
        expected_final["Net Worth"] = checking - prev_stmt_bal - expected_interest
        expected_final["Loan Total"] = 0.0
        expected_final["CC Debt Total"] = prev_stmt_bal - expected_min_payment + expected_interest
        expected_final["Liquid Total"] = checking - expected_min_payment
        expected_final["Memo Directives"] = ""
        expected_final["Memo"] = ""

        # previous_statement_balance=1000,
        # checking_balance=1000,
        # payment_date=None,
        # payment_amount=None,
        # minimum_payment=40,

        self._run_checking_and_credit_min_payment_case(
            expected_billing_date_state=expected_billing_date_state,
            expected_final=expected_final,
            previous_statement_balance=prev_stmt_bal,
            checking_balance=checking,
        )
    
    #TODO manual review
    @pytest.mark.integration
    def test_ForecastHandler__checking_and_credit__min_cc_payment_w_advance_partial_payment(self):
        expected_billing_date_state, expected_final = self._credit_expected_rows_with_placeholders()
        self._fill_credit_expected_rows(
            expected_billing_date_state,
            expected_final,
            checking=960.0,
            credit=982.87,
            billing_cycle_payment_balance=0.0,
            billing_date_end_of_previous_cycle_balance=1000.0,
            final_end_of_previous_cycle_balance=982.87,
            marginal_interest=22.87,
            memo_directives="CC INTEREST (Credit: Prev Stmt Bal +$22.87); CC MIN PAYMENT (Credit: Prev Stmt Bal -$20.00); CC MIN PAYMENT (Checking -$20.00)",
        )
        self._run_checking_and_credit_min_payment_case(
            expected_billing_date_state=expected_billing_date_state,
            expected_final=expected_final,
            payment_date=date(2026,6,2),
            payment_amount=20,
        )
    
    #TODO manual review
    @pytest.mark.integration
    def test_ForecastHandler__checking_and_credit__min_cc_payment_w_advance_exact_payment(self):
        expected_billing_date_state, expected_final = self._credit_expected_rows_with_placeholders()
        self._fill_credit_expected_rows(
            expected_billing_date_state,
            expected_final,
            checking=960.0,
            credit=982.4,
            billing_cycle_payment_balance=0.0,
            billing_date_end_of_previous_cycle_balance=1000.0,
            final_end_of_previous_cycle_balance=982.4,
            marginal_interest=22.4,
            memo_directives="CC INTEREST (Credit: Prev Stmt Bal +$22.40)",
        )
        self._run_checking_and_credit_min_payment_case(
            expected_billing_date_state=expected_billing_date_state,
            expected_final=expected_final,
            payment_date=date(2026,6,2),
            payment_amount=40,
        )
    
    #TODO manual review
    @pytest.mark.integration
    def test_ForecastHandler__checking_and_credit__min_cc_payment_w_advance_surplus_payment(self):
        expected_billing_date_state, expected_final = self._credit_expected_rows_with_placeholders()
        self._fill_credit_expected_rows(
            expected_billing_date_state,
            expected_final,
            checking=940.0,
            credit=961.93,
            billing_cycle_payment_balance=0.0,
            billing_date_end_of_previous_cycle_balance=1000.0,
            final_end_of_previous_cycle_balance=961.93,
            marginal_interest=21.93,
            memo_directives="CC INTEREST (Credit: Prev Stmt Bal +$21.93)",
        )
        self._run_checking_and_credit_min_payment_case(
            expected_billing_date_state=expected_billing_date_state,
            expected_final=expected_final,
            payment_date=date(2026,6,2),
            payment_amount=60,
        )

    #TODO manual review
    @pytest.mark.integration
    def test_ForecastHandler__checking_and_credit__min_cc_payment_w_same_day_partial_payment(self):
        expected_billing_date_state, expected_final = self._credit_expected_rows_with_placeholders()
        self._fill_credit_expected_rows(
            expected_billing_date_state,
            expected_final,
            checking=940.0,
            credit=963.33,
            billing_cycle_payment_balance=20.0,
            billing_date_end_of_previous_cycle_balance=1000.0,
            final_end_of_previous_cycle_balance=983.33,
            marginal_interest=23.33,
            memo_directives="CC INTEREST (Credit: Prev Stmt Bal +$23.33); CC MIN PAYMENT (Credit: Prev Stmt Bal -$40.00); CC MIN PAYMENT (Checking -$40.00)",
        )
        self._run_checking_and_credit_min_payment_case(
            expected_billing_date_state=expected_billing_date_state,
            expected_final=expected_final,
            payment_date=date(2026,6,3),
            payment_amount=20,
        )
    
    #TODO manual review
    @pytest.mark.integration
    def test_ForecastHandler__checking_and_credit__min_cc_payment_w_same_day_exact_payment(self):
        expected_billing_date_state, expected_final = self._credit_expected_rows_with_placeholders()
        self._fill_credit_expected_rows(
            expected_billing_date_state,
            expected_final,
            checking=920.0,
            credit=943.33,
            billing_cycle_payment_balance=40.0,
            billing_date_end_of_previous_cycle_balance=1000.0,
            final_end_of_previous_cycle_balance=983.33,
            marginal_interest=23.33,
            memo_directives="CC INTEREST (Credit: Prev Stmt Bal +$23.33); CC MIN PAYMENT (Credit: Prev Stmt Bal -$40.00); CC MIN PAYMENT (Checking -$40.00)",
        )
        self._run_checking_and_credit_min_payment_case(
            expected_billing_date_state=expected_billing_date_state,
            expected_final=expected_final,
            payment_date=date(2026,6,3),
            payment_amount=40,
        )
    
    #TODO manual review
    @pytest.mark.integration
    def test_ForecastHandler__checking_and_credit__min_cc_payment_w_same_day_surplus_payment(self):
        expected_billing_date_state, expected_final = self._credit_expected_rows_with_placeholders()
        self._fill_credit_expected_rows(
            expected_billing_date_state,
            expected_final,
            checking=900.0,
            credit=923.33,
            billing_cycle_payment_balance=60.0,
            billing_date_end_of_previous_cycle_balance=1000.0,
            final_end_of_previous_cycle_balance=983.33,
            marginal_interest=23.33,
            memo_directives="CC INTEREST (Credit: Prev Stmt Bal +$23.33); CC MIN PAYMENT (Credit: Prev Stmt Bal -$40.00); CC MIN PAYMENT (Checking -$40.00)",
        )
        self._run_checking_and_credit_min_payment_case(
            expected_billing_date_state=expected_billing_date_state,
            expected_final=expected_final,
            payment_date=date(2026,6,3),
            payment_amount=60,
        )

    #TODO manual review
    @pytest.mark.integration
    def test_ForecastHandler__checking_and_credit__min_cc_payment_gt_default_w_advance_partial_payment(self):
        expected_billing_date_state, expected_final = self._credit_expected_rows_with_placeholders()
        self._fill_credit_expected_rows(
            expected_billing_date_state,
            expected_final,
            checking=19670.0,
            credit=9901.0,
            billing_cycle_payment_balance=0.0,
            billing_date_end_of_previous_cycle_balance=10000.0,
            final_end_of_previous_cycle_balance=9901.0,
            marginal_interest=231.0,
            memo_directives="CC INTEREST (Credit: Prev Stmt Bal +$231.00); CC MIN PAYMENT (Credit: Prev Stmt Bal -$230.00); CC MIN PAYMENT (Checking -$230.00)",
        )
        self._run_checking_and_credit_min_payment_case(
            expected_billing_date_state=expected_billing_date_state,
            expected_final=expected_final,
            previous_statement_balance=10000,
            checking_balance=20000,
            payment_date=date(2026,6,2),
            payment_amount=100,
        )
    
    #TODO manual review
    @pytest.mark.integration
    def test_ForecastHandler__checking_and_credit__min_cc_payment_gt_default_w_advance_exact_payment(self):
        expected_billing_date_state, expected_final = self._credit_expected_rows_with_placeholders()
        self._fill_credit_expected_rows(
            expected_billing_date_state,
            expected_final,
            checking=19666.67,
            credit=9892.23,
            billing_cycle_payment_balance=0.0,
            billing_date_end_of_previous_cycle_balance=10000.0,
            final_end_of_previous_cycle_balance=9892.23,
            marginal_interest=225.56,
            memo_directives="CC INTEREST (Credit: Prev Stmt Bal +$225.56)",
        )
        self._run_checking_and_credit_min_payment_case(
            expected_billing_date_state=expected_billing_date_state,
            expected_final=expected_final,
            previous_statement_balance=10000,
            checking_balance=20000,
            payment_date=date(2026,6,2),
            payment_amount=333.33,
        )
    
    #TODO manual review
    @pytest.mark.integration
    def test_ForecastHandler__checking_and_credit__min_cc_payment_gt_default_w_advance_surplus_payment(self):
        expected_billing_date_state, expected_final = self._credit_expected_rows_with_placeholders()
        self._fill_credit_expected_rows(
            expected_billing_date_state,
            expected_final,
            checking=19600.0,
            credit=9824.0,
            billing_cycle_payment_balance=0.0,
            billing_date_end_of_previous_cycle_balance=10000.0,
            final_end_of_previous_cycle_balance=9824.0,
            marginal_interest=224.0,
            memo_directives="CC INTEREST (Credit: Prev Stmt Bal +$224.00)",
        )
        self._run_checking_and_credit_min_payment_case(
            expected_billing_date_state=expected_billing_date_state,
            expected_final=expected_final,
            previous_statement_balance=10000,
            checking_balance=20000,
            payment_date=date(2026,6,2),
            payment_amount=400,
        )

    #TODO manual review
    @pytest.mark.integration
    def test_ForecastHandler__checking_and_credit__min_cc_payment_gt_default_w_same_day_partial_payment(self):
        expected_billing_date_state, expected_final = self._credit_expected_rows_with_placeholders()
        self._fill_credit_expected_rows(
            expected_billing_date_state,
            expected_final,
            checking=19566.67,
            credit=9800.0,
            billing_cycle_payment_balance=100.0,
            billing_date_end_of_previous_cycle_balance=10000.0,
            final_end_of_previous_cycle_balance=9900.0,
            marginal_interest=233.33,
            memo_directives="CC INTEREST (Credit: Prev Stmt Bal +$233.33); CC MIN PAYMENT (Credit: Prev Stmt Bal -$333.33); CC MIN PAYMENT (Checking -$333.33)",
        )
        self._run_checking_and_credit_min_payment_case(
            expected_billing_date_state=expected_billing_date_state,
            expected_final=expected_final,
            previous_statement_balance=10000,
            checking_balance=20000,
            payment_date=date(2026,6,3),
            payment_amount=100,
        )
    
    #TODO manual review
    @pytest.mark.integration
    def test_ForecastHandler__checking_and_credit__min_cc_payment_gt_default_w_same_day_exact_payment(self):
        expected_billing_date_state, expected_final = self._credit_expected_rows_with_placeholders()
        self._fill_credit_expected_rows(
            expected_billing_date_state,
            expected_final,
            checking=19333.34,
            credit=9566.67,
            billing_cycle_payment_balance=333.33,
            billing_date_end_of_previous_cycle_balance=10000.0,
            final_end_of_previous_cycle_balance=9900.0,
            marginal_interest=233.33,
            memo_directives="CC INTEREST (Credit: Prev Stmt Bal +$233.33); CC MIN PAYMENT (Credit: Prev Stmt Bal -$333.33); CC MIN PAYMENT (Checking -$333.33)",
        )
        self._run_checking_and_credit_min_payment_case(
            expected_billing_date_state=expected_billing_date_state,
            expected_final=expected_final,
            previous_statement_balance=10000,
            checking_balance=20000,
            payment_date=date(2026,6,3),
            payment_amount=333.33,
        )
    
    #TODO manual review
    @pytest.mark.integration
    def test_ForecastHandler__checking_and_credit__min_cc_payment_gt_default_w_same_day_surplus_payment(self):
        expected_billing_date_state, expected_final = self._credit_expected_rows_with_placeholders()
        self._fill_credit_expected_rows(
            expected_billing_date_state,
            expected_final,
            checking=19266.67,
            credit=9500.0,
            billing_cycle_payment_balance=400.0,
            billing_date_end_of_previous_cycle_balance=10000.0,
            final_end_of_previous_cycle_balance=9900.0,
            marginal_interest=233.33,
            memo_directives="CC INTEREST (Credit: Prev Stmt Bal +$233.33); CC MIN PAYMENT (Credit: Prev Stmt Bal -$333.33); CC MIN PAYMENT (Checking -$333.33)",
        )
        self._run_checking_and_credit_min_payment_case(
            expected_billing_date_state=expected_billing_date_state,
            expected_final=expected_final,
            previous_statement_balance=10000,
            checking_balance=20000,
            payment_date=date(2026,6,3),
            payment_amount=400,
        )

    #TODO manual review
    @pytest.mark.integration
    def test_ForecastHandler__checking_and_loan__min_loan_payment(self):
        expected_billing_date_state, expected_final = self._loan_expected_rows_with_placeholders()
        self._fill_loan_expected_rows(
            expected_billing_date_state,
            expected_final,
            checking=960.0,
            loan=960.2,
            principal_balance=960.2,
            interest_balance=0.0,
            billing_cycle_payment_balance=0.0,
            marginal_interest=0.2,
            memo_directives="LOAN INTEREST (Loan: Interest +$0.20); LOAN MIN PAYMENT (Loan: Interest -$0.20); LOAN MIN PAYMENT (Loan: Principal Balance -$39.80); LOAN MIN PAYMENT (Checking -$40.00)",
            final_loan=960.58,
            final_principal_balance=960.2,
            final_interest_balance=0.38,
            final_marginal_interest=0.19,
            final_net_loss=0.19,
            final_memo_directives="LOAN INTEREST (Loan: Interest +$0.19)",
        )
        self._run_checking_and_loan_min_payment_case(
            expected_billing_date_state=expected_billing_date_state,
            expected_final=expected_final,
        )

    @pytest.mark.integration
    def test_ForecastHandler__checking_and_loan__daily_interest_accrues_after_billing_start(self):
        start_date = date(2026,6,1)
        end_date = date(2026,6,2)

        A = AccountSet()
        B = LineItemSet()
        M = MemoRuleSet()
        MS = MilestoneSet()

        A.createCheckingAccount(
            name="Checking",
            balance=1000,
            min_balance=0,
            max_balance=float("inf"),
            primary_checking_ind=True,
        )
        A.createLoanAccount(
            name="Loan",
            principal_balance=1000,
            interest_balance=0,
            min_balance=0,
            max_balance=25_000,
            billing_start_date=date(2026,6,1),
            apr=0.36525,
            minimum_payment=0,
            billing_cycle_payment_balance=0,
        )

        result = ForecastHandler().runForecast(
            ExpenseForecastInitialConditions(
                start_date=start_date,
                end_date=end_date,
                account_set=A,
                line_item_set=B,
                memo_rule_set=M,
                milestone_set=MS,
            ),
            MS,
            include_debug_columns=True,
        )

        expected_final = pd.DataFrame(
            {
                "Date": [date(2026,6,2)],
                "Checking": [1000.0],
                "Loan": [1001.0],
                "Loan: Principal Balance": [1000.0],
                "Loan: Interest": [1.0],
                "Loan: Loan Billing Cycle Payment Bal": [0.0],
                "Interest Accrued": [1.0],
                "Investment Returns": [0.0],
                "Net Gain": [0.0],
                "Net Loss": [1.0],
                "Net Worth": [-1.0],
                "Loan Total": [1001.0],
                "CC Debt Total": [0.0],
                "Liquid Total": [1000.0],
                "Next Income Date": [""],
                "Memo Directives": ["LOAN INTEREST (Loan: Interest +$1.00)"],
                "Memo": [""],
            },
            index=[1],
        )

        pd.testing.assert_frame_equal(result.forecast_df.tail(1), expected_final)
    
    #TODO manual review
    @pytest.mark.integration
    def test_ForecastHandler__checking_and_loan__min_loan_payment_w_advance_partial_payment(self):
        expected_billing_date_state, expected_final = self._loan_expected_rows_with_placeholders()
        self._fill_loan_expected_rows(
            expected_billing_date_state,
            expected_final,
            checking=960.0,
            loan=960.2,
            principal_balance=960.2,
            interest_balance=0.0,
            billing_cycle_payment_balance=20.0,
            marginal_interest=0.2,
            memo_directives="LOAN INTEREST (Loan: Interest +$0.20); LOAN MIN PAYMENT (Loan: Interest -$0.20); LOAN MIN PAYMENT (Loan: Principal Balance -$19.80); LOAN MIN PAYMENT (Checking -$20.00)",
            final_loan=960.58,
            final_principal_balance=960.2,
            final_interest_balance=0.38,
            final_marginal_interest=0.19,
            final_net_loss=0.19,
            final_memo_directives="LOAN INTEREST (Loan: Interest +$0.19)",
        )
        self._run_checking_and_loan_min_payment_case(
            expected_billing_date_state=expected_billing_date_state,
            expected_final=expected_final,
            payment_date=date(2026,6,2),
            payment_amount=20,
        )
    
    #TODO manual review
    @pytest.mark.integration
    def test_ForecastHandler__checking_and_loan__min_loan_payment_w_advance_exact_payment(self):
        expected_billing_date_state, expected_final = self._loan_expected_rows_with_placeholders()
        self._fill_loan_expected_rows(
            expected_billing_date_state,
            expected_final,
            checking=960.0,
            loan=960.19,
            principal_balance=960.0,
            interest_balance=0.19,
            billing_cycle_payment_balance=40.0,
            marginal_interest=0.19,
            memo_directives="LOAN INTEREST (Loan: Interest +$0.19)",
            final_loan=960.58,
            final_principal_balance=960.0,
            final_interest_balance=0.58,
            final_marginal_interest=0.19,
            final_net_loss=0.19,
            final_memo_directives="LOAN INTEREST (Loan: Interest +$0.19)",
        )
        self._run_checking_and_loan_min_payment_case(
            expected_billing_date_state=expected_billing_date_state,
            expected_final=expected_final,
            payment_date=date(2026,6,2),
            payment_amount=40,
        )
    
    #TODO manual review
    @pytest.mark.integration
    def test_ForecastHandler__checking_and_loan__min_loan_payment_w_advance_surplus_payment(self):
        expected_billing_date_state, expected_final = self._loan_expected_rows_with_placeholders()
        self._fill_loan_expected_rows(
            expected_billing_date_state,
            expected_final,
            checking=940.0,
            loan=940.19,
            principal_balance=940.0,
            interest_balance=0.19,
            billing_cycle_payment_balance=60.0,
            marginal_interest=0.19,
            memo_directives="LOAN INTEREST (Loan: Interest +$0.19)",
            final_loan=940.56,
            final_principal_balance=940.0,
            final_interest_balance=0.56,
            final_marginal_interest=0.19,
            final_net_loss=0.19,
            final_memo_directives="LOAN INTEREST (Loan: Interest +$0.19)",
        )
        self._run_checking_and_loan_min_payment_case(
            expected_billing_date_state=expected_billing_date_state,
            expected_final=expected_final,
            payment_date=date(2026,6,2),
            payment_amount=60,
        )

    #TODO manual review
    @pytest.mark.integration
    def test_ForecastHandler__checking_and_loan__min_loan_payment_w_same_day_partial_payment(self):
        expected_billing_date_state, expected_final = self._loan_expected_rows_with_placeholders()
        self._fill_loan_expected_rows(
            expected_billing_date_state,
            expected_final,
            checking=940.0,
            loan=940.2,
            principal_balance=940.2,
            interest_balance=0.0,
            billing_cycle_payment_balance=20.0,
            marginal_interest=0.2,
            memo_directives="LOAN INTEREST (Loan: Interest +$0.20); LOAN MIN PAYMENT (Loan: Interest -$0.20); LOAN MIN PAYMENT (Loan: Principal Balance -$39.80); LOAN MIN PAYMENT (Checking -$40.00)",
            final_loan=940.58,
            final_principal_balance=940.2,
            final_interest_balance=0.38,
            final_marginal_interest=0.19,
            final_net_loss=0.19,
            final_memo_directives="LOAN INTEREST (Loan: Interest +$0.19)",
        )
        self._run_checking_and_loan_min_payment_case(
            expected_billing_date_state=expected_billing_date_state,
            expected_final=expected_final,
            payment_date=date(2026,6,3),
            payment_amount=20,
        )
    
    #TODO manual review
    @pytest.mark.integration
    def test_ForecastHandler__checking_and_loan__min_loan_payment_w_same_day_exact_payment(self):
        expected_billing_date_state, expected_final = self._loan_expected_rows_with_placeholders()
        self._fill_loan_expected_rows(
            expected_billing_date_state,
            expected_final,
            checking=920.0,
            loan=920.2,
            principal_balance=920.2,
            interest_balance=0.0,
            billing_cycle_payment_balance=40.0,
            marginal_interest=0.2,
            memo_directives="LOAN INTEREST (Loan: Interest +$0.20); LOAN MIN PAYMENT (Loan: Interest -$0.20); LOAN MIN PAYMENT (Loan: Principal Balance -$39.80); LOAN MIN PAYMENT (Checking -$40.00)",
            final_loan=920.57,
            final_principal_balance=920.2,
            final_interest_balance=0.37,
            final_marginal_interest=0.18,
            final_net_loss=0.18,
            final_memo_directives="LOAN INTEREST (Loan: Interest +$0.18)",
        )
        self._run_checking_and_loan_min_payment_case(
            expected_billing_date_state=expected_billing_date_state,
            expected_final=expected_final,
            payment_date=date(2026,6,3),
            payment_amount=40,
        )
    
    #TODO manual review
    @pytest.mark.integration
    def test_ForecastHandler__checking_and_loan__min_loan_payment_w_same_day_surplus_payment(self):
        expected_billing_date_state, expected_final = self._loan_expected_rows_with_placeholders()
        self._fill_loan_expected_rows(
            expected_billing_date_state,
            expected_final,
            checking=900.0,
            loan=900.2,
            principal_balance=900.2,
            interest_balance=0.0,
            billing_cycle_payment_balance=60.0,
            marginal_interest=0.2,
            memo_directives="LOAN INTEREST (Loan: Interest +$0.20); LOAN MIN PAYMENT (Loan: Interest -$0.20); LOAN MIN PAYMENT (Loan: Principal Balance -$39.80); LOAN MIN PAYMENT (Checking -$40.00)",
            final_loan=900.56,
            final_principal_balance=900.2,
            final_interest_balance=0.36,
            final_marginal_interest=0.18,
            final_net_loss=0.18,
            final_memo_directives="LOAN INTEREST (Loan: Interest +$0.18)",
        )
        self._run_checking_and_loan_min_payment_case(
            expected_billing_date_state=expected_billing_date_state,
            expected_final=expected_final,
            payment_date=date(2026,6,3),
            payment_amount=60,
        )



    # @pytest.mark.skip(reason="A combination of multiple cases, not sure if this is useful")
    # @pytest.mark.integration
    # def test_ForecastHandler__all_account_types(self):
    #     start_date = date(2026,6,1)
    #     end_date = date(2026,6,10)
        
    #     A = AccountSet()
    #     B = LineItemSet()
    #     M = MemoRuleSet()
    #     MS = MilestoneSet()

    #     A.createCheckingAccount(
    #         name="Checking",
    #         balance=1000,
    #         min_balance=0,
    #         max_balance=float("inf"),
    #         primary_checking_ind=True,
    #     )

    #     A.createCreditCardAccount(
    #         name="Credit",
    #         current_statement_balance=100, 
    #         previous_statement_balance=100, 
    #         min_balance=0, 
    #         max_balance=25_000,
    #         billing_start_date=date(2020,1,7), 
    #         apr=0.28, 
    #         minimum_payment=40, 
    #         end_of_previous_cycle_balance=100
    #     )  

    #     A.createLoanAccount(
    #         name="Loan", 
    #         principal_balance=15_000, 
    #         interest_balance=500, 
    #         min_balance=0, 
    #         max_balance=25_000, 
    #         billing_start_date=date(2020,1,3),
    #         apr=0.07, 
    #         minimum_payment=212.00, 
    #         end_of_previous_cycle_balance=15_000
    #     )

    #     # TODO Savings / Investment Account

    #     B.addLineItem(
    #         start_date=start_date,
    #         end_date=end_date,
    #         priority=1,
    #         interval="daily",
    #         amount=10,
    #         memo="food",
    #         income_flag=False,
    #         deferrable=False,
    #         partial_payment_allowed=False,
    #     )

    #     M.addMemoRule(
    #         memo_regex="food",
    #         account_from="Checking",
    #         account_to=None,
    #         transaction_priority=1,
    #     )

    #     MS = MilestoneSet()

    #     E_IO = ExpenseForecastInitialConditions(
    #         start_date=start_date,
    #         end_date=end_date,
    #         account_set=A,
    #         line_item_set=B,
    #         memo_rule_set=M,
    #         milestone_set=MS)
        
    #     R__debug_true = ForecastHandler().runForecast(E_IO, MS, include_debug_columns=True)

    #     assert isinstance(R__debug_true, ExpenseForecastResult)
    #     assert isinstance(R__debug_true.forecast_df, pd.DataFrame)

    #     required_columns__debug_true_case = {
    #         "Date",
    #         "Checking",
    #         "Credit",
    #         "Credit: Curr Stmt Bal",
    #         "Credit: Prev Stmt Bal",
    #         "Credit: Credit Billing Cycle Payment Bal",
    #         "Credit: Credit End of Prev Cycle Bal",

    #         "Loan",     #Something fishy with this
    #         "Loan: Principal Balance",
    #         "Loan: Interest",
    #         "Loan: Loan Billing Cycle Payment Bal",

    #         "Interest Accrued",
    #         "Net Gain",
    #         "Net Loss",
    #         "Net Worth",
    #         "Loan Total",
    #         "CC Debt Total",
    #         "Liquid Total",
    #         "Next Income Date",
    #         "Memo Directives",
    #         "Memo",
            
    #     }

    #     actual_columns__debug_true_case = set(R__debug_true.forecast_df.columns)

    #     missing__debug_true_case = required_columns__debug_true_case - actual_columns__debug_true_case
    #     unexpected__debug_true_case = actual_columns__debug_true_case - required_columns__debug_true_case

    #     assert actual_columns__debug_true_case == required_columns__debug_true_case, (
    #         "Forecast dataframe columns did not match.\n"
    #         f"Missing columns:    {sorted(missing__debug_true_case)}\n"
    #         f"Unexpected columns: {sorted(unexpected__debug_true_case)}\n"
    #         f"Actual columns:     {list(R__debug_true.forecast_df.columns)}"
    #     )

    #     R__debug_false = ForecastHandler().runForecast(E_IO, MS, include_debug_columns=False)

    #     assert isinstance(R__debug_false, ExpenseForecastResult)
    #     assert isinstance(R__debug_false.forecast_df, pd.DataFrame)

    #     required_columns__debug_false_case = {
    #         "Date",
    #         "Checking",
    #         "Credit",
    #         "Loan",
    #         "Next Income Date",
    #         "Memo Directives",
    #         "Memo",
    #         "CC Debt Total",
    #         "Liquid Total",
    #         "Net Loss"
    #     }

    #     actual_columns__debug_false_case = set(R__debug_false.forecast_df.columns)

    #     missing__debug_false_case = required_columns__debug_false_case - actual_columns__debug_false_case
    #     unexpected__debug_false_case = actual_columns__debug_false_case - required_columns__debug_false_case

    #     assert actual_columns__debug_false_case == required_columns__debug_false_case, (
    #         "Forecast dataframe columns did not match.\n"
    #         f"Missing columns:    {sorted(missing__debug_false_case)}\n"
    #         f"Unexpected columns: {sorted(unexpected__debug_false_case)}\n"
    #         f"Actual columns:     {list(R__debug_false.forecast_df.columns)}"
    #     )

    #     # TODO assert final values, and shape of final data frames





# Tests to write (some of these may belong in stubs up above)
# multiple cc / overlap cases
# multiple loans / overlap cases
# overlap of cc and loan

# Test names I moved from test_ExpenseForecast. I deleted those methods, but they still exist in history if you want to look at them.
# test_p1_only_no_budget_items
# test_p1_only__income_and_payment_on_same_day
# test_p1_cc_txn_on_billing_date
# test_cc_payment__satisfice__curr_bal_25__expect_0
# test_cc_payment__satisfice__prev_bal_1000__expect_40
# test_cc_payment__satisfice__prev_bal_3000__expect_60
# test_p2_and_3__expect_defer
# test_p2_and_3__p3_item_deferred_bc_p2
# test_execute_defer_after_receiving_income_2_days_later
# test_p2_and_3__expect_skip
# test_p2_and_3__p3_item_skipped_bc_p2
# test_p4__cc_payment__no_prev_balance__pay_100__no_funds__expect_skip
# test_p4__cc_payment__no_prev_balance__pay_100__expect_skip
# test_transactions_executed_at_p1_and_p2
# test_transactions_executed_at_p1_and_p2_and_p3
# test_p4__cc_payment__pay_all_of_prev_part_of_curr__expect_800
# test_p4__cc_payment__pay_part_of_prev_balance__expect_200
# test_p4__cc_payment__non_0_prev_balance_but_no_funds__expect_0
# test_p4__cc_payment__partial_of_indicated_amount
# test_execute_at_reduced_amount_bc_later_higher_priority_txn
# test_cc_advance_minimum_payment_in_1_payment_pay_over_minimum
# test_cc_advance_minimum_payment_in_1_payment_pay_under_minimum
# test_cc_advance_minimum_payment_in_1_payment_pay_exact_minimum
# test_cc_single_additional_payment_on_due_date
# test_eopc_bal_500eocp_0prev_0curr
# test_cc_two_additional_payments_on_due_date__prev_only
# test_cc_single_additional_payment_on_due_date_OVERPAY
# test_cc_two_additional_payments_on_due_date__curr_only
# test_cc_two_additional_payments_on_due_date_OVERPAY
# test_cc_single_additional_payment_day_before__prev_only
# test_cc_two_additional_payments_day_before__prev_only
# test_cc_single_additional_payment_day_before_OVERPAY__prev_only
# test_cc_two_additional_payments_day_before_OVERPAY__prev_only
# test_cc_single_additional_payment_day_before__curr_only
# test_cc_two_additional_payments_day_before__curr_only
# test_cc_single_additional_payment_day_before_OVERPAY__curr_only
# test_cc_two_additional_payments_day_before_OVERPAY__curr_only
# test_cc_single_additional_payment_day_before__curr_prev
# test_cc_single_additional_payment_day_before_OVERPAY__curr_prev
# test_distal_propagation__prev_only
# test_distal_propagation_multiple__prev_only
# test_distal_propagation__curr_only
# test_distal_propagation_multiple__curr_only
# test_distal_propagation__curr_prev
# test_distal_propagation_multiple__curr_prev
# test_p7__additional_loan_payment__amt_10
# test_p7__additional_loan_payment__amt_110
# test_p7__additional_loan_payment__amt_560
# test_p7__additional_loan_payment__amt_610
# test_p7__additional_loan_payment__amt_1900
# test_p7__additional_loan_payment__amt_overpay





    """Copy-pasted approximate forecast templates retained for historical context.

    # without an interval, have the forecast be each day at the first of the month
    def test_ForecastHandler__runApproximate__no_activity__less_than_1_month__not_include_1st(self):
        start_date = date(2026,6,5)
        end_date = date(2026,6,10)

        A = AccountSet()
        B = LineItemSet()
        M = MemoRuleSet()
        MS = MilestoneSet()

        checking_balance = 1000

        expected_billing_date_state = None #TODO
        expected_final = None #TODO

        A.createCheckingAccount(
            name="Checking",
            balance=checking_balance,
            min_balance=0,
            max_balance=float("inf"),
            primary_checking_ind=True,
        )

        E_IO = ExpenseForecastInitialConditions(
            start_date=start_date,
            end_date=end_date,
            account_set=A,
            line_item_set=B,
            memo_rule_set=M,
            milestone_set=MS,
        )

        R = ForecastHandler().runForecastApproximate(E_IO, MS, include_debug_columns=True)

        assert R.forecast_df.shape[0] == 5

        pd.testing.assert_frame_equal(
            R.forecast_df.iloc[[2]],
            expected_billing_date_state,
        )

        pd.testing.assert_frame_equal(
            R.forecast_df.tail(1),
            expected_final,
        )

    def test_ForecastHandler__runApproximate__no_activity__less_than_1_month__include_1st(self):
            start_date = date(2026,5,30)
            end_date = date(2026,6,2)

            A = AccountSet()
            B = LineItemSet()
            M = MemoRuleSet()
            MS = MilestoneSet()

            checking_balance = 1000

            expected_billing_date_state = None #TODO
            expected_final = None #TODO

            A.createCheckingAccount(
                name="Checking",
                balance=checking_balance,
                min_balance=0,
                max_balance=float("inf"),
                primary_checking_ind=True,
            )

            E_IO = ExpenseForecastInitialConditions(
                start_date=start_date,
                end_date=end_date,
                account_set=A,
                line_item_set=B,
                memo_rule_set=M,
                milestone_set=MS,
            )

            R = ForecastHandler().runForecastApproximate(E_IO, MS, include_debug_columns=True)

            assert R.forecast_df.shape[0] == 5

            pd.testing.assert_frame_equal(
                R.forecast_df.iloc[[2]],
                expected_billing_date_state,
            )

            pd.testing.assert_frame_equal(
                R.forecast_df.tail(1),
                expected_final,
            )

    def test_ForecastHandler__runApproximate__no_activity__6_weeks(self):
            start_date = date(2026,6,1)
            end_date = date(2026,7,15)

            A = AccountSet()
            B = LineItemSet()
            M = MemoRuleSet()
            MS = MilestoneSet()

            checking_balance = 1000

            expected_billing_date_state = None #TODO
            expected_final = None #TODO

            A.createCheckingAccount(
                name="Checking",
                balance=checking_balance,
                min_balance=0,
                max_balance=float("inf"),
                primary_checking_ind=True,
            )

            E_IO = ExpenseForecastInitialConditions(
                start_date=start_date,
                end_date=end_date,
                account_set=A,
                line_item_set=B,
                memo_rule_set=M,
                milestone_set=MS,
            )

            R = ForecastHandler().runForecastApproximate(E_IO, MS, include_debug_columns=True)

            assert R.forecast_df.shape[0] == 5

            pd.testing.assert_frame_equal(
                R.forecast_df.iloc[[2]],
                expected_billing_date_state,
            )

            pd.testing.assert_frame_equal(
                R.forecast_df.tail(1),
                expected_final,
            )

    def test_ForecastHandler__runApproximate__no_activity__6_months(self):
            start_date = date(2026,6,1)
            end_date = start_date + datetime.timedelta(days=180)

            A = AccountSet()
            B = LineItemSet()
            M = MemoRuleSet()
            MS = MilestoneSet()

            checking_balance = 1000

            expected_billing_date_state = None #TODO
            expected_final = None #TODO

            A.createCheckingAccount(
                name="Checking",
                balance=checking_balance,
                min_balance=0,
                max_balance=float("inf"),
                primary_checking_ind=True,
            )

            E_IO = ExpenseForecastInitialConditions(
                start_date=start_date,
                end_date=end_date,
                account_set=A,
                line_item_set=B,
                memo_rule_set=M,
                milestone_set=MS,
            )

            R = ForecastHandler().runForecastApproximate(E_IO, MS, include_debug_columns=True)

            assert R.forecast_df.shape[0] == 5

            pd.testing.assert_frame_equal(
                R.forecast_df.iloc[[2]],
                expected_billing_date_state,
            )

            pd.testing.assert_frame_equal(
                R.forecast_df.tail(1),
                expected_final,
            )


    # TODO test_ForecastHandler__runApproximate__min_cc_payments__90_days
    def test_ForecastHandler__runApproximate__min_cc_payments__90_days(self):
            start_date = date(2026,6,1)
            end_date = start_date + datetime.timedelta(days=90)

            A = AccountSet()
            B = LineItemSet()
            M = MemoRuleSet()
            MS = MilestoneSet()

            checking_balance = 1000
            principal_balance = 1000
            minimum_payment = 40

            # payment_date, payment_amount
            # expected_billing_date_state, expected_final

            A.createCheckingAccount(
                name="Checking",
                balance=checking_balance,
                min_balance=0,
                max_balance=float("inf"),
                primary_checking_ind=True,
            )

            A.createLoanAccount(
                name="Loan",
                principal_balance=principal_balance,
                interest_balance=0.0,
                min_balance=0,
                max_balance=25_000,
                billing_start_date=date(2026,6,3),
                apr=0.07305,
                minimum_payment=minimum_payment,
                billing_cycle_payment_balance=0,
            )

            if payment_date is not None:
                B.addLineItem(
                    start_date=payment_date,
                    end_date=payment_date,
                    priority=1,
                    interval="once",
                    amount=payment_amount,
                    memo="loan payment",
                    income_flag=False,
                    deferrable=False,
                    partial_payment_allowed=False,
                )

                M.addMemoRule(
                    memo_regex="loan payment",
                    account_from="Checking",
                    account_to="Loan",
                    transaction_priority=1,
                )

            E_IO = ExpenseForecastInitialConditions(
                start_date=start_date,
                end_date=end_date,
                account_set=A,
                line_item_set=B,
                memo_rule_set=M,
                milestone_set=MS,
            )

            R = ForecastHandler().runForecast(E_IO, MS, include_debug_columns=True)

            assert R.forecast_df.shape[0] == 5

            pd.testing.assert_frame_equal(
                R.forecast_df.iloc[[2]],
                expected_billing_date_state,
            )

            pd.testing.assert_frame_equal(
                R.forecast_df.tail(1),
                expected_final,
            )

    # TODO test_ForecastHandler__runApproximate__min_loan_payments__90_days
    def test_ForecastHandler__runApproximate__min_loan_payments__90_days(self):
            start_date = date(2026,6,1)
            end_date = start_date + datetime.timedelta(days=90)

            A = AccountSet()
            B = LineItemSet()
            M = MemoRuleSet()
            MS = MilestoneSet()

            checking_balance = 1000
            principal_balance = 1000
            minimum_payment = 40

            # payment_date, payment_amount
            # expected_billing_date_state, expected_final

            A.createCheckingAccount(
                name="Checking",
                balance=checking_balance,
                min_balance=0,
                max_balance=float("inf"),
                primary_checking_ind=True,
            )

            A.createLoanAccount(
                name="Loan",
                principal_balance=principal_balance,
                interest_balance=0.0,
                min_balance=0,
                max_balance=25_000,
                billing_start_date=date(2026,6,3),
                apr=0.07305,
                minimum_payment=minimum_payment,
                billing_cycle_payment_balance=0,
            )

            if payment_date is not None:
                B.addLineItem(
                    start_date=payment_date,
                    end_date=payment_date,
                    priority=1,
                    interval="once",
                    amount=payment_amount,
                    memo="loan payment",
                    income_flag=False,
                    deferrable=False,
                    partial_payment_allowed=False,
                )

                M.addMemoRule(
                    memo_regex="loan payment",
                    account_from="Checking",
                    account_to="Loan",
                    transaction_priority=1,
                )

            E_IO = ExpenseForecastInitialConditions(
                start_date=start_date,
                end_date=end_date,
                account_set=A,
                line_item_set=B,
                memo_rule_set=M,
                milestone_set=MS,
            )

            R = ForecastHandler().runForecast(E_IO, MS, include_debug_columns=True)

            assert R.forecast_df.shape[0] == 5

            pd.testing.assert_frame_equal(
                R.forecast_df.iloc[[2]],
                expected_billing_date_state,
            )

            pd.testing.assert_frame_equal(
                R.forecast_df.tail(1),
                expected_final,
            )

    # TODO test_ForecastHandler__runApproximate__min_loan_and_cc_payments__90_days
    def test_ForecastHandler__runApproximate__min_loan_and_cc_payments__90_days(self):
            start_date = date(2026,6,1)
            end_date = start_date + datetime.timedelta(days=90)

            A = AccountSet()
            B = LineItemSet()
            M = MemoRuleSet()
            MS = MilestoneSet()

            checking_balance = 1000
            principal_balance = 1000
            minimum_payment = 40

            # payment_date, payment_amount
            # expected_billing_date_state, expected_final

            A.createCheckingAccount(
                name="Checking",
                balance=checking_balance,
                min_balance=0,
                max_balance=float("inf"),
                primary_checking_ind=True,
            )

            A.createLoanAccount(
                name="Loan",
                principal_balance=principal_balance,
                interest_balance=0.0,
                min_balance=0,
                max_balance=25_000,
                billing_start_date=date(2026,6,3),
                apr=0.07305,
                minimum_payment=minimum_payment,
                billing_cycle_payment_balance=0,
            )

            if payment_date is not None:
                B.addLineItem(
                    start_date=payment_date,
                    end_date=payment_date,
                    priority=1,
                    interval="once",
                    amount=payment_amount,
                    memo="loan payment",
                    income_flag=False,
                    deferrable=False,
                    partial_payment_allowed=False,
                )

                M.addMemoRule(
                    memo_regex="loan payment",
                    account_from="Checking",
                    account_to="Loan",
                    transaction_priority=1,
                )

            E_IO = ExpenseForecastInitialConditions(
                start_date=start_date,
                end_date=end_date,
                account_set=A,
                line_item_set=B,
                memo_rule_set=M,
                milestone_set=MS,
            )

            R = ForecastHandler().runForecast(E_IO, MS, include_debug_columns=True)

            assert R.forecast_df.shape[0] == 5

            pd.testing.assert_frame_equal(
                R.forecast_df.iloc[[2]],
                expected_billing_date_state,
            )

            pd.testing.assert_frame_equal(
                R.forecast_df.tail(1),
                expected_final,
            )

    # TODO test_ForecastHandler__runApproximate__advance_loan_payments__90_days
    def test_ForecastHandler__runApproximate__advance_loan_payments__90_days(self):
            start_date = date(2026,6,1)
            end_date = start_date + datetime.timedelta(days=90)

            A = AccountSet()
            B = LineItemSet()
            M = MemoRuleSet()
            MS = MilestoneSet()

            checking_balance = 1000
            principal_balance = 1000
            minimum_payment = 40

            # payment_date, payment_amount
            # expected_billing_date_state, expected_final

            A.createCheckingAccount(
                name="Checking",
                balance=checking_balance,
                min_balance=0,
                max_balance=float("inf"),
                primary_checking_ind=True,
            )

            A.createLoanAccount(
                name="Loan",
                principal_balance=principal_balance,
                interest_balance=0.0,
                min_balance=0,
                max_balance=25_000,
                billing_start_date=date(2026,6,3),
                apr=0.07305,
                minimum_payment=minimum_payment,
                billing_cycle_payment_balance=0,
            )

            if payment_date is not None:
                B.addLineItem(
                    start_date=payment_date,
                    end_date=payment_date,
                    priority=1,
                    interval="once",
                    amount=payment_amount,
                    memo="loan payment",
                    income_flag=False,
                    deferrable=False,
                    partial_payment_allowed=False,
                )

                M.addMemoRule(
                    memo_regex="loan payment",
                    account_from="Checking",
                    account_to="Loan",
                    transaction_priority=1,
                )

            E_IO = ExpenseForecastInitialConditions(
                start_date=start_date,
                end_date=end_date,
                account_set=A,
                line_item_set=B,
                memo_rule_set=M,
                milestone_set=MS,
            )

            R = ForecastHandler().runForecast(E_IO, MS, include_debug_columns=True)

            assert R.forecast_df.shape[0] == 5

            pd.testing.assert_frame_equal(
                R.forecast_df.iloc[[2]],
                expected_billing_date_state,
            )

            pd.testing.assert_frame_equal(
                R.forecast_df.tail(1),
                expected_final,
            )

    # TODO test_ForecastHandler__runApproximate__advance_cc_payments__90_days
    def test_ForecastHandler__runApproximate__advance_cc_payments__90_days(self):
            start_date = date(2026,6,1)
            end_date = start_date + datetime.timedelta(days=90)

            A = AccountSet()
            B = LineItemSet()
            M = MemoRuleSet()
            MS = MilestoneSet()

            checking_balance = 1000
            principal_balance = 1000
            minimum_payment = 40

            # payment_date, payment_amount
            # expected_billing_date_state, expected_final

            A.createCheckingAccount(
                name="Checking",
                balance=checking_balance,
                min_balance=0,
                max_balance=float("inf"),
                primary_checking_ind=True,
            )

            A.createLoanAccount(
                name="Loan",
                principal_balance=principal_balance,
                interest_balance=0.0,
                min_balance=0,
                max_balance=25_000,
                billing_start_date=date(2026,6,3),
                apr=0.07305,
                minimum_payment=minimum_payment,
                billing_cycle_payment_balance=0,
            )

            if payment_date is not None:
                B.addLineItem(
                    start_date=payment_date,
                    end_date=payment_date,
                    priority=1,
                    interval="once",
                    amount=payment_amount,
                    memo="loan payment",
                    income_flag=False,
                    deferrable=False,
                    partial_payment_allowed=False,
                )

                M.addMemoRule(
                    memo_regex="loan payment",
                    account_from="Checking",
                    account_to="Loan",
                    transaction_priority=1,
                )

            E_IO = ExpenseForecastInitialConditions(
                start_date=start_date,
                end_date=end_date,
                account_set=A,
                line_item_set=B,
                memo_rule_set=M,
                milestone_set=MS,
            )

            R = ForecastHandler().runForecast(E_IO, MS, include_debug_columns=True)

            assert R.forecast_df.shape[0] == 5

            pd.testing.assert_frame_equal(
                R.forecast_df.iloc[[2]],
                expected_billing_date_state,
            )

            pd.testing.assert_frame_equal(
                R.forecast_df.tail(1),
                expected_final,
            )

    # TODO test_ForecastHandler__runApproximate__p2_transactions
    def test_ForecastHandler__runApproximate__p2_transactions(self):
            start_date = date(2026,6,1)
            end_date = start_date + datetime.timedelta(days=90)

            A = AccountSet()
            B = LineItemSet()
            M = MemoRuleSet()
            MS = MilestoneSet()

            checking_balance = 1000
            principal_balance = 1000
            minimum_payment = 40

            # payment_date, payment_amount
            # expected_billing_date_state, expected_final

            A.createCheckingAccount(
                name="Checking",
                balance=checking_balance,
                min_balance=0,
                max_balance=float("inf"),
                primary_checking_ind=True,
            )

            A.createLoanAccount(
                name="Loan",
                principal_balance=principal_balance,
                interest_balance=0.0,
                min_balance=0,
                max_balance=25_000,
                billing_start_date=date(2026,6,3),
                apr=0.07305,
                minimum_payment=minimum_payment,
                billing_cycle_payment_balance=0,
            )

            if payment_date is not None:
                B.addLineItem(
                    start_date=payment_date,
                    end_date=payment_date,
                    priority=1,
                    interval="once",
                    amount=payment_amount,
                    memo="loan payment",
                    income_flag=False,
                    deferrable=False,
                    partial_payment_allowed=False,
                )

                M.addMemoRule(
                    memo_regex="loan payment",
                    account_from="Checking",
                    account_to="Loan",
                    transaction_priority=1,
                )

            E_IO = ExpenseForecastInitialConditions(
                start_date=start_date,
                end_date=end_date,
                account_set=A,
                line_item_set=B,
                memo_rule_set=M,
                milestone_set=MS,
            )

            R = ForecastHandler().runForecast(E_IO, MS, include_debug_columns=True)

            assert R.forecast_df.shape[0] == 5

            pd.testing.assert_frame_equal(
                R.forecast_df.iloc[[2]],
                expected_billing_date_state,
            )

            pd.testing.assert_frame_equal(
                R.forecast_df.tail(1),
                expected_final,
            )



    """

    @staticmethod
    def _approximate_io(start_date, end_date, accounts, budget=None, memo_rules=None):
        return ExpenseForecastInitialConditions(
            start_date=start_date,
            end_date=end_date,
            account_set=accounts,
            line_item_set=budget or LineItemSet(),
            memo_rule_set=memo_rules or MemoRuleSet(),
            milestone_set=MilestoneSet(),
        )

    @staticmethod
    def _approximate_checking(balance=1000):
        accounts = AccountSet()
        accounts.createCheckingAccount(
            name="Checking", balance=balance, min_balance=0,
            max_balance=float("inf"), primary_checking_ind=True,
        )
        return accounts

    def _run_approximate(self, start_date, end_date, accounts, budget=None, memo_rules=None):
        result = ForecastHandler().runForecastApproximate(
            self._approximate_io(start_date, end_date, accounts, budget, memo_rules),
            MilestoneSet(),
            include_debug_columns=True,
        )
        assert isinstance(result, ExpenseForecastResult)
        assert isinstance(result.forecast_df, pd.DataFrame)
        return result

    @staticmethod
    def _add_approximate_credit_card(accounts):
        accounts.createCreditCardAccount(
            name="Credit", current_statement_balance=0,
            previous_statement_balance=1000, min_balance=0, max_balance=25_000,
            billing_start_date=date(2026, 6, 3), apr=0.25, minimum_payment=40,
            end_of_previous_cycle_balance=1000,
        )

    @staticmethod
    def _add_approximate_loan(accounts):
        accounts.createLoanAccount(
            name="Loan", principal_balance=1000, interest_balance=0,
            min_balance=0, max_balance=25_000,
            billing_start_date=date(2026, 6, 3), apr=0.1, minimum_payment=40,
            billing_cycle_payment_balance=0,
        )

    @staticmethod
    def _add_approximate_payment(budget, memo_rules, account_to, memo):
        budget.addLineItem(
            start_date=date(2026, 6, 15), end_date=date(2026, 6, 15),
            priority=1, interval="once", amount=100, memo=memo,
            income_flag=False, deferrable=False, partial_payment_allowed=False,
        )
        memo_rules.addMemoRule(
            memo_regex=memo, account_from="Checking", account_to=account_to,
            transaction_priority=1,
        )

    @pytest.mark.integration
    def test_ForecastHandler__runApproximate__no_activity__less_than_1_month__not_include_1st(self):
        start_date, end_date = date(2026, 6, 5), date(2026, 6, 10)
        result = self._run_approximate(start_date, end_date, self._approximate_checking())
        assert result.forecast_df["Date"].tolist() == [start_date, end_date]
        assert result.forecast_df["Checking"].tolist() == [1000.0, 1000.0]

    @pytest.mark.integration
    def test_ForecastHandler__runApproximate__no_activity__less_than_1_month__include_1st(self):
        start_date, end_date = date(2026, 5, 30), date(2026, 6, 2)
        result = self._run_approximate(
            start_date, end_date, self._approximate_checking()
        )
        assert result.forecast_df["Date"].tolist() == [start_date, date(2026, 6, 1), end_date]
        assert result.forecast_df["Checking"].tolist() == [1000.0, 1000.0, 1000.0]

    @pytest.mark.integration
    def test_ForecastHandler__runApproximate__no_activity__6_weeks(self):
        start_date, end_date = date(2026, 5, 30), date(2026, 7, 15)
        result = self._run_approximate(
            start_date, end_date, self._approximate_checking()
        )
        assert result.forecast_df["Date"].tolist() == [start_date, date(2026, 6, 1), date(2026, 7, 1), end_date]
        assert result.forecast_df["Checking"].tolist() == [1000.0, 1000.0, 1000.0, 1000.0]





    # Expected Data:
    # Date      Checking        Prev
    # 5/30      1000            1000
    # 6/1       1000            1000
    # 7/1       960             960 + interest from 1st payment
    # 8/1       920             920 + interest from 1st payment + interest from 2nd payment
    # 8/28      880             880 + interest from 1st payment + interest from 2nd payment + interest from 3rd payment
    @pytest.mark.integration
    def test_ForecastHandler__runApproximate__min_cc_payments__90_days(self):
        start_date = date(2026, 5, 30)
        end_date = start_date + datetime.timedelta(days=90)
        accounts = self._approximate_checking()
        self._add_approximate_credit_card(accounts)
        result = self._run_approximate(start_date, end_date, accounts)
        assert result.forecast_df["Date"].tolist() == [
            start_date, date(2026, 6, 1), date(2026, 7, 1),
            date(2026, 8, 1), end_date,
        ]
        directives = result.forecast_df["Memo Directives"].tolist()
        assert sum("Credit" in directive for directive in directives) == 3
        assert result.forecast_df.iloc[-1]["Checking"] == 1000 - (40 * 3)
        balance = float("1000")
        for _ in range(3):
            balance += balance * float("0.25") / float("12")
            balance -= float("40")
        assert result.forecast_df.iloc[-1]["Credit"] == round(float(balance), 2)

    # Expected Data:
    # (column names are different i forget what to call them atm)
    # Date      Checking        Loan Principal      Loan Interest
    # 5/30      1000            1000                0
    # 6/1       1000            1000                0
    # 7/1       960             960
    # 8/1       920             920
    # 8/28      880             880

    # The first billing date is 6/3, but the next approximate forecast date is 7/1
    # Start at the current forecast date.
    # Accrue interest for the number of days until the billing/payment date.
    #    Note that in this case, the first billing date was 6/3, not 6/1, so this check should account for this.
    #    However, for the following payment on 8/1, the full previous month should count toward interest accrual.
    #    Furthermore, months are not all the same length, and this should be accounted for.
    # Apply the payment to interest first, then principal.
    #
    # I think the cleanest rule is: monthly grain controls output dates, not necessarily every internal state-change date.
    # You do not need to simulate every day. You can advance directly 
    # between a small number of meaningful dates using interval arithmetic:

    @pytest.mark.integration
    def test_ForecastHandler__runApproximate__min_loan_payments__90_days(self):
        start_date = date(2026, 5, 30)
        end_date = start_date + datetime.timedelta(days=90)
        accounts = self._approximate_checking()
        self._add_approximate_loan(accounts)
        result = self._run_approximate(start_date, end_date, accounts)
        assert result.forecast_df["Date"].tolist() == [
            start_date, date(2026, 6, 1), date(2026, 7, 1),
            date(2026, 8, 1), end_date,
        ]
        directives = result.forecast_df["Memo Directives"].tolist()
        assert sum("Loan" in directive for directive in directives) == 3
        assert result.forecast_df.iloc[-1]["Checking"] == 1000 - (40 * 3)
        principal, interest = float("1000"), float("0")
        for elapsed_days in (28, 31, 27):
            interest += principal * float("0.1") * elapsed_days / float("365.25")
            payment = float("40")
            interest_payment = min(payment, interest)
            interest -= interest_payment
            principal -= payment - interest_payment
        assert result.forecast_df.iloc[-1]["Loan: Principal Balance"] == round(float(principal), 2)
        assert result.forecast_df.iloc[-1]["Loan: Interest"] == round(float(interest), 2)

    #dates should be: start_date, 6/1, 7/1, 8/1, end_date
    # the values from this should be the same as the previous cases, but both are present in this output
    # with Checking being accordingly lower
    @pytest.mark.integration
    def test_ForecastHandler__runApproximate__min_loan_and_cc_payments__90_days(self):
        start_date = date(2026, 5, 30)
        end_date = start_date + datetime.timedelta(days=90)

        accounts = self._approximate_checking()
        self._add_approximate_loan(accounts)
        self._add_approximate_credit_card(accounts)
        result = self._run_approximate(start_date, end_date, accounts)
        assert result.forecast_df["Date"].tolist() == [
            start_date, date(2026, 6, 1), date(2026, 7, 1),
            date(2026, 8, 1), end_date,
        ]
        directives = result.forecast_df["Memo Directives"].tolist()
        assert sum("Loan" in directive for directive in directives) == 3
        assert sum("Credit" in directive for directive in directives) == 3
        assert result.forecast_df.iloc[-1]["Checking"] == 1000 - ((40 * 3) * 2)
        credit_balance = float("1000")
        for _ in range(3):
            credit_balance += credit_balance * float("0.25") / float("12")
            credit_balance -= float("40")
        loan_principal, loan_interest = float("1000"), float("0")
        for elapsed_days in (28, 31, 27):
            loan_interest += loan_principal * float("0.1") * elapsed_days / float("365.25")
            interest_payment = min(float("40"), loan_interest)
            loan_interest -= interest_payment
            loan_principal -= float("40") - interest_payment
        assert result.forecast_df.iloc[-1]["Credit"] == round(float(credit_balance), 2)
        assert result.forecast_df.iloc[-1]["Loan: Principal Balance"] == round(float(loan_principal), 2)
        assert result.forecast_df.iloc[-1]["Loan: Interest"] == round(float(loan_interest), 2)




    # Expected Data:
    # (column names are different i forget what to call them atm)
    # Date      Checking        Loan Principal      Loan Interest
    # 5/30      1000            1000                0
    # 6/1       1000            1000                0
    # 7/1       960             960
    # 8/1       920             920
    # 8/28      880             880
    #
    # Note that the advance payment takes place on 6/15 for 100
    # In order for this test case to pass, an additional intervals in the interest calculation
    # must be added. It may be necessary to splti this test into 3 separate cases:
    # 1. the current interest is not completely paid by the additional payment
    # 2. the current interest is exactly paid by the additional payment
    # 3. the current interest is overpaid by the additional payment, and thus reduces
    #    reduces the principal as well
    @pytest.mark.integration
    def test_ForecastHandler__runApproximate__advance_loan_payments__90_days(self):
        start_date = date(2026, 5, 30)
        end_date = start_date + datetime.timedelta(days=90)

        accounts = self._approximate_checking()
        self._add_approximate_loan(accounts) #billing start date is 6/3
        budget, memo_rules = LineItemSet(), MemoRuleSet()
        self._add_approximate_payment(budget, memo_rules, "Loan", "extra loan payment") #payment date is 6/15
        result = self._run_approximate(
            start_date, end_date, accounts, budget, memo_rules
        )
        assert result.forecast_df["Date"].tolist() == [
            start_date, date(2026, 6, 1), date(2026, 7, 1),
            date(2026, 8, 1), end_date,
        ]
        july_memo = result.forecast_df.loc[result.forecast_df.Date == date(2026, 7, 1), "Memo"].iat[0]
        assert "extra loan payment (Checking -$100.00)" in july_memo
        principal, interest = float("1000"), float("0")
        interest += principal * float("0.1") * float("12") / float("365.25")
        interest_payment = min(float("100"), interest)
        interest -= interest_payment
        principal -= float("100") - interest_payment
        for elapsed_days in (16, 31, 27):
            interest += principal * float("0.1") * elapsed_days / float("365.25")
            interest_payment = min(float("40"), interest)
            interest -= interest_payment
            principal -= float("40") - interest_payment
        assert result.forecast_df.iloc[-1]["Loan: Principal Balance"] == round(float(principal), 2)
        assert result.forecast_df.iloc[-1]["Loan: Interest"] == round(float(interest), 2)

    @pytest.mark.integration
    def test_ForecastHandler__runApproximate__all_loans_payment(self):
        start_date = date(2026, 5, 30)
        end_date = date(2026, 6, 20)
        accounts = self._approximate_checking()
        for name, apr in (("High APR Loan", 0.2), ("Low APR Loan", 0.1)):
            accounts.createLoanAccount(
                name=name,
                principal_balance=1000,
                interest_balance=0,
                min_balance=0,
                max_balance=25_000,
                billing_start_date=date(2026, 6, 3),
                apr=apr,
                minimum_payment=0,
                billing_cycle_payment_balance=0,
            )

        budget, memo_rules = LineItemSet(), MemoRuleSet()
        self._add_approximate_payment(
            budget, memo_rules, "ALL_LOANS", "extra loan payment"
        )

        result = self._run_approximate(
            start_date, end_date, accounts, budget, memo_rules
        )

        payment_row = result.forecast_df.iloc[-1]
        high_interest = float("1000") * float("0.2") * float("12") / float("365.25")
        high_principal = float("900") + high_interest
        post_payment_high_interest = (
            high_principal * float("0.2") * float("5") / float("365.25")
        )
        low_interest = float("1000") * float("0.1") * float("17") / float("365.25")
        assert payment_row["Checking"] == 900
        assert payment_row["High APR Loan: Principal Balance"] == round(
            float(high_principal), 2
        )
        assert payment_row["High APR Loan: Interest"] == round(
            float(post_payment_high_interest), 2
        )
        assert payment_row["Low APR Loan: Principal Balance"] == 1000
        assert payment_row["Low APR Loan: Interest"] == round(float(low_interest), 2)

    @pytest.mark.integration
    def test_ForecastHandler__runApproximate__all_loans_uses_executed_amount_after_payoff(self):
        start_date, end_date = date(2026, 6, 1), date(2026, 6, 20)
        accounts = self._approximate_checking()
        accounts.createLoanAccount(
            name="Small Loan",
            principal_balance=100,
            interest_balance=0,
            min_balance=0,
            max_balance=1000,
            billing_start_date=start_date,
            apr=0,
            minimum_payment=0,
            billing_cycle_payment_balance=0,
        )
        budget, memo_rules = LineItemSet(), MemoRuleSet()
        budget.addLineItem(
            start_date=date(2026, 6, 15), end_date=date(2026, 6, 16),
            priority=1, interval="daily", amount=4200,
            memo="all loan payment", income_flag=False,
            deferrable=False, partial_payment_allowed=False,
        )
        memo_rules.addMemoRule(
            memo_regex="all loan payment", account_from="Checking",
            account_to="ALL_LOANS", transaction_priority=1,
        )

        result = self._run_approximate(
            start_date, end_date, accounts, budget, memo_rules
        )
        final_row = result.forecast_df.iloc[-1]

        assert final_row["Checking"] == 900
        assert final_row["Small Loan"] == 0
        assert final_row["Small Loan: Loan Billing Cycle Payment Bal"] == 0
        assert final_row["Memo"] == "all loan payment (Checking -$100.00)"

    @pytest.mark.integration
    def test_ForecastHandler__runApproximate__loan_cycle_payments_reset_monthly(self):
        start_date, end_date = date(2026, 5, 30), date(2026, 7, 1)
        accounts = self._approximate_checking(balance=20_000)
        for name, apr in (("Loan A", 0.2), ("Loan B", 0.1)):
            accounts.createLoanAccount(
                name=name,
                principal_balance=10_000,
                interest_balance=0,
                min_balance=0,
                max_balance=20_000,
                billing_start_date=start_date,
                apr=apr,
                minimum_payment=0,
                billing_cycle_payment_balance=0,
            )
        budget, memo_rules = LineItemSet(), MemoRuleSet()
        budget.addLineItem(
            start_date=date(2026, 6, 1), end_date=end_date,
            priority=1, interval="monthly", amount=4200,
            memo="all loan payment", income_flag=False,
            deferrable=False, partial_payment_allowed=False,
        )
        memo_rules.addMemoRule(
            memo_regex="all loan payment", account_from="Checking",
            account_to="ALL_LOANS", transaction_priority=1,
        )

        result = self._run_approximate(
            start_date, end_date, accounts, budget, memo_rules
        )
        cycle_columns = [
            column for column in result.forecast_df.columns
            if "Loan Billing Cycle Payment Bal" in column
        ]
        june_row = result.forecast_df.loc[
            result.forecast_df.Date == date(2026, 6, 1)
        ].iloc[0]
        july_row = result.forecast_df.loc[
            result.forecast_df.Date == date(2026, 7, 1)
        ].iloc[0]

        assert june_row[cycle_columns].sum() == pytest.approx(4200)
        assert july_row[cycle_columns].sum() == pytest.approx(4200)

    @pytest.mark.integration
    def test_ForecastHandler__runApproximate__unknown_account_still_raises(self):
        start_date, end_date = date(2026, 6, 1), date(2026, 6, 20)
        accounts = self._approximate_checking()
        budget, memo_rules = LineItemSet(), MemoRuleSet()
        self._add_approximate_payment(
            budget, memo_rules, "NOT_AN_ACCOUNT", "invalid payment"
        )

        with pytest.raises(ValueError):
            self._run_approximate(
                start_date, end_date, accounts, budget, memo_rules
            )

    @pytest.mark.integration
    def test_ForecastHandler__runApproximate__logs_processing(self, caplog, monkeypatch):
        start_date, end_date = date(2026, 6, 1), date(2026, 6, 20)
        accounts = self._approximate_checking()
        budget, memo_rules = LineItemSet(), MemoRuleSet()
        budget.addLineItem(
            start_date=date(2026, 6, 15), end_date=date(2026, 6, 16),
            priority=1, interval="daily", amount=100, memo="logged expense",
            income_flag=False, deferrable=False, partial_payment_allowed=False,
        )
        memo_rules.addMemoRule(
            memo_regex="logged expense", account_from="Checking", account_to=None,
            transaction_priority=1,
        )

        monkeypatch.setattr(forecast_logger, "propagate", True)
        with caplog.at_level(logging.DEBUG, logger=forecast_logger.name):
            io = self._approximate_io(
                start_date, end_date, accounts, budget, memo_rules
            )
            ForecastHandler().runForecastApproximate(
                io, MilestoneSet(), include_debug_columns=True
            )

        log_output = "\n".join(record.getMessage() for record in caplog.records)
        assert "Starting Approximate Forecast" in log_output
        assert (
            "2026-06-20 processing binned memo "
            "'logged expense x2 (Checking -$200.00)'"
            in log_output
        )
        assert "executing txn" not in log_output
        assert "Finished Approximate Forecast" in log_output

    @pytest.mark.integration
    def test_ForecastHandler__runApproximate__uses_reduced_partial_payment(self):
        start_date, end_date = date(2026, 6, 1), date(2026, 6, 20)
        accounts = self._approximate_checking(balance=100)
        budget, memo_rules = LineItemSet(), MemoRuleSet()
        budget.addLineItem(
            start_date=date(2026, 6, 2), end_date=date(2026, 6, 2),
            priority=2, interval="once", amount=150, memo="optional expense",
            income_flag=False, deferrable=False, partial_payment_allowed=True,
        )
        memo_rules.addMemoRule(
            memo_regex="optional expense", account_from="Checking", account_to=None,
            transaction_priority=2,
        )

        result = self._run_approximate(
            start_date, end_date, accounts, budget, memo_rules
        )

        assert result.forecast_df.iloc[-1]["Checking"] == 0
        assert len(result.confirmed_df) == 1
        assert 99.99 <= float(result.confirmed_df.iloc[0]["Amount"]) <= 100.01
        assert result.skipped_df.empty

    @pytest.mark.integration
    def test_ForecastHandler__runApproximate__defers_until_next_income(self):
        start_date, end_date = date(2026, 6, 1), date(2026, 6, 20)
        accounts = self._approximate_checking(balance=0)
        budget, memo_rules = LineItemSet(), MemoRuleSet()
        budget.addLineItem(
            start_date=date(2026, 6, 2), end_date=date(2026, 6, 2),
            priority=2, interval="once", amount=50, memo="deferrable expense",
            income_flag=False, deferrable=True, partial_payment_allowed=False,
        )
        budget.addLineItem(
            start_date=date(2026, 6, 10), end_date=date(2026, 6, 10),
            priority=1, interval="once", amount=100, memo="paycheck income",
            income_flag=True, deferrable=False, partial_payment_allowed=False,
        )
        memo_rules.addMemoRule(
            memo_regex="deferrable expense", account_from="Checking", account_to=None,
            transaction_priority=2,
        )
        memo_rules.addMemoRule(
            memo_regex="paycheck income", account_from=None, account_to="Checking",
            transaction_priority=1,
        )

        result = self._run_approximate(
            start_date, end_date, accounts, budget, memo_rules
        )

        assert result.forecast_df.iloc[-1]["Checking"] == 50
        deferred_expense = result.confirmed_df.loc[
            result.confirmed_df["Memo"].eq("deferrable expense")
        ].iloc[0]
        assert deferred_expense["Date"] == date(2026, 6, 10)
        assert result.deferred_df.empty
        assert result.skipped_df.empty

    @pytest.mark.integration
    def test_ForecastHandler__runApproximate__skips_when_no_income_remains(self):
        start_date, end_date = date(2026, 6, 1), date(2026, 6, 20)
        accounts = self._approximate_checking(balance=0)
        budget, memo_rules = LineItemSet(), MemoRuleSet()
        budget.addLineItem(
            start_date=date(2026, 6, 2), end_date=date(2026, 6, 2),
            priority=2, interval="once", amount=50, memo="unfunded expense",
            income_flag=False, deferrable=True, partial_payment_allowed=False,
        )
        memo_rules.addMemoRule(
            memo_regex="unfunded expense", account_from="Checking", account_to=None,
            transaction_priority=2,
        )

        result = self._run_approximate(
            start_date, end_date, accounts, budget, memo_rules
        )

        assert result.confirmed_df.empty
        assert result.deferred_df.empty
        assert result.skipped_df["Memo"].tolist() == ["unfunded expense"]

    @pytest.mark.integration
    def test_ForecastHandler__investment_returns__exact_and_approximate(self):
        start_date, end_date = date(2026, 6, 1), date(2026, 6, 5)
        accounts = self._approximate_checking()
        accounts.createInvestmentAccount(
            name="Brokerage",
            balance=1000,
            billing_start_date=date(2026, 6, 2),
            apr=0.1,
        )
        io = self._approximate_io(start_date, end_date, accounts)

        exact = ForecastHandler().runForecast(
            io, MilestoneSet(), include_debug_columns=True
        )
        approximate = ForecastHandler().runForecastApproximate(
            io, MilestoneSet(), include_debug_columns=True
        )

        expected_balance = float("1000") * (
            float("1") + float("0.1") / float("365.25")
        ) ** 4
        expected_rounded = round(float(expected_balance), 2)
        assert exact.forecast_df.iloc[-1]["Brokerage"] == expected_rounded
        assert approximate.forecast_df.iloc[-1]["Brokerage"] == expected_rounded
        assert exact.forecast_df.iloc[-1]["Net Worth"] == 1000 + expected_rounded
        assert approximate.forecast_df.iloc[-1]["Net Worth"] == 1000 + expected_rounded
        for result in (exact, approximate):
            assert result.forecast_df["Investment Returns"].sum() == pytest.approx(
                expected_rounded - 1000,
                # Approximate output bins accrue with full precision but its
                # memo directives retain cent-denominated daily postings.
                abs=0.03,
            )
        assert sum(
            "INVESTMENT RETURN" in directives
            for directives in exact.forecast_df["Memo Directives"]
        ) == 4
        assert sum(
            "INVESTMENT RETURN" in directives
            for directives in approximate.forecast_df["Memo Directives"]
        ) == 1

    @pytest.mark.integration
    def test_ForecastHandler__investment_contribution_preserves_exact_approximate_parity(self):
        start_date, end_date = date(2026, 6, 1), date(2026, 6, 5)
        accounts = self._approximate_checking()
        accounts.createInvestmentAccount(
            name="Brokerage",
            balance=1000,
            billing_start_date=start_date,
            apr=0.1,
        )
        budget, memo_rules = LineItemSet(), MemoRuleSet()
        budget.addLineItem(
            start_date=date(2026, 6, 3), end_date=date(2026, 6, 3),
            priority=1, interval="once", amount=100, memo="invest",
            income_flag=False, deferrable=False, partial_payment_allowed=False,
        )
        memo_rules.addMemoRule(
            memo_regex="invest", account_from="Checking", account_to="Brokerage",
            transaction_priority=1,
        )
        io = self._approximate_io(
            start_date, end_date, accounts, budget, memo_rules
        )

        exact = ForecastHandler().runForecast(
            io, MilestoneSet(), include_debug_columns=True
        )
        approximate = ForecastHandler().runForecastApproximate(
            io, MilestoneSet(), include_debug_columns=True
        )

        daily_factor = float("1") + float("0.1") / float("365.25")
        expected_balance = (
            float("1000") * daily_factor ** 2 + float("100")
        ) * daily_factor ** 2
        assert exact.forecast_df.iloc[-1]["Checking"] == 900
        assert approximate.forecast_df.iloc[-1]["Checking"] == 900
        assert exact.forecast_df.iloc[-1]["Brokerage"] == round(
            float(expected_balance), 2
        )
        assert approximate.forecast_df.iloc[-1]["Brokerage"] == round(
            float(expected_balance), 2
        )
        for result in (exact, approximate):
            assert result.forecast_df["Net Loss"].sum() == 0
            assert result.forecast_df["Net Gain"].sum() > 0
            assert any(
                "INVESTMENT CONTRIBUTION (Brokerage +$100" in directives
                for directives in result.forecast_df["Memo Directives"]
            )

    @pytest.mark.integration
    def test_ForecastHandler__investment_withdrawal_is_net_neutral(self):
        start_date, end_date = date(2026, 6, 1), date(2026, 6, 3)
        accounts = self._approximate_checking()
        accounts.createInvestmentAccount(
            name="Brokerage", balance=1000,
            billing_start_date=start_date, apr=0,
        )
        budget, memo_rules = LineItemSet(), MemoRuleSet()
        budget.addLineItem(
            start_date=date(2026, 6, 2), end_date=date(2026, 6, 2),
            priority=1, interval="once", amount=100, memo="withdraw",
            income_flag=False, deferrable=False, partial_payment_allowed=False,
        )
        memo_rules.addMemoRule(
            memo_regex="withdraw", account_from="Brokerage", account_to="Checking",
            transaction_priority=1,
        )
        io = self._approximate_io(
            start_date, end_date, accounts, budget, memo_rules
        )

        exact = ForecastHandler().runForecast(
            io, MilestoneSet(), include_debug_columns=True
        )
        approximate = ForecastHandler().runForecastApproximate(
            io, MilestoneSet(), include_debug_columns=True
        )

        for result in (exact, approximate):
            final_row = result.forecast_df.iloc[-1]
            assert final_row["Checking"] == 1100
            assert final_row["Brokerage"] == 900
            assert result.forecast_df["Net Gain"].sum() == 0
            assert result.forecast_df["Net Loss"].sum() == 0
            assert any(
                "INVESTMENT WITHDRAWAL (Checking +$100" in directives
                for directives in result.forecast_df["Memo Directives"]
            )

    # dates should be: start_date, 6/1, 7/1, 8/1, end_date
    # this test is similar but simpler than the loan case, since (I am pretty sure )
    # interest should not be reduced by advance payment within 1 month
    # and hence the monthly grain should sufficiently expose the change in balance
    # for the calculation
    @pytest.mark.integration
    def test_ForecastHandler__runApproximate__advance_cc_payments__90_days(self):
        start_date = date(2026, 5, 30)
        end_date = start_date + datetime.timedelta(days=90)

        accounts = self._approximate_checking()
        self._add_approximate_credit_card(accounts)
        budget, memo_rules = LineItemSet(), MemoRuleSet()
        self._add_approximate_payment(budget, memo_rules, "Credit", "extra credit payment")
        result = self._run_approximate(
            start_date, end_date, accounts, budget, memo_rules
        )
        assert result.forecast_df["Date"].tolist() == [
            start_date, date(2026, 6, 1), date(2026, 7, 1),
            date(2026, 8, 1), end_date,
        ]
        july_memo = result.forecast_df.loc[result.forecast_df.Date == date(2026, 7, 1), "Memo"].iat[0]
        assert "extra credit payment (Checking -$100.00)" in july_memo
        july_directives = result.forecast_df.loc[
            result.forecast_df.Date == date(2026, 7, 1), "Memo Directives"
        ].iat[0]
        assert "ADDTL CC PAYMENT (Credit -$100)" in july_directives
        assert "ADDTL CC PAYMENT (Checking" not in july_directives
        # The advance payment lowers the statement balance used for interest and
        # satisfies the first approximate minimum payment through payment credit.
        credit_balance = float("1000") - float("100")
        credit_balance += credit_balance * float("0.25") / float("12")
        for _ in range(2):
            credit_balance += credit_balance * float("0.25") / float("12")
            credit_balance -= float("40")
        assert result.forecast_df.iloc[-1]["Credit"] == round(float(credit_balance), 2)

    @pytest.mark.integration
    def test_ForecastHandler__p1_credit_payment_adds_directives(self):
        start_date, end_date = date(2026, 6, 1), date(2026, 6, 2)
        accounts = self._approximate_checking()
        accounts.createCreditCardAccount(
            name="Credit", current_statement_balance=0,
            previous_statement_balance=500, min_balance=0, max_balance=5000,
            billing_start_date=date(2026, 7, 1), apr=0.2,
            minimum_payment=40, end_of_previous_cycle_balance=500,
        )
        budget, memo_rules = LineItemSet(), MemoRuleSet()
        budget.addLineItem(
            start_date=end_date, end_date=end_date, priority=1,
            interval="once", amount=100, memo="credit payment",
            income_flag=False, deferrable=False, partial_payment_allowed=False,
        )
        memo_rules.addMemoRule(
            memo_regex="credit payment", account_from="Checking",
            account_to="Credit", transaction_priority=1,
        )

        result = ForecastHandler().runForecast(
            self._approximate_io(
                start_date, end_date, accounts, budget, memo_rules
            ),
            MilestoneSet(),
            include_debug_columns=True,
        )
        directives = result.forecast_df.iloc[-1]["Memo Directives"]
        assert "ADDTL CC PAYMENT (Credit -$100" in directives
        assert "ADDTL CC PAYMENT (Checking" not in directives

    @pytest.mark.integration
    def test_ForecastHandler__p2_partial_credit_payment_uses_reduced_amount(self):
        start_date, end_date = date(2026, 6, 1), date(2026, 6, 2)
        accounts = self._approximate_checking(balance=300)
        accounts.createCreditCardAccount(
            name="Credit", current_statement_balance=0,
            previous_statement_balance=1000, min_balance=0, max_balance=5000,
            billing_start_date=date(2026, 7, 1), apr=0.2,
            minimum_payment=40, end_of_previous_cycle_balance=1000,
        )
        budget, memo_rules = LineItemSet(), MemoRuleSet()
        budget.addLineItem(
            start_date=end_date, end_date=end_date, priority=2,
            interval="once", amount=500, memo="extra credit payment",
            income_flag=False, deferrable=False, partial_payment_allowed=True,
        )
        memo_rules.addMemoRule(
            memo_regex="extra credit payment", account_from="Checking",
            account_to="Credit", transaction_priority=2,
        )

        result = ForecastHandler().runForecast(
            self._approximate_io(
                start_date, end_date, accounts, budget, memo_rules
            ),
            MilestoneSet(),
            include_debug_columns=True,
        )

        final_row = result.forecast_df.iloc[-1]
        assert final_row["Checking"] == 0
        assert final_row["Credit"] == 700
        assert result.confirmed_df.iloc[-1]["Amount"] == pytest.approx(300)
        assert "ADDTL CC PAYMENT (Credit -$300" in final_row["Memo Directives"]
        assert "ADDTL CC PAYMENT (Checking" not in final_row["Memo Directives"]

    # dates should be: start_date, 6/1, 7/1, 8/1, end_date
    # this test should include 1 p2 transactions at each grain: daily, weekly, semiweekly, monthly
    # and test that the memo is binned xN appropriately
    @pytest.mark.integration
    def test_ForecastHandler__runApproximate__p2_transactions(self):
        start_date = date(2026, 5, 30)
        end_date = start_date + datetime.timedelta(days=90)
        
        start_date, end_date = date(2026, 6, 1), date(2026, 7, 1)
        budget, memo_rules = LineItemSet(), MemoRuleSet()
        budget.addLineItem(
            start_date=start_date, end_date=end_date, priority=2,
            interval="daily", amount=10, memo="food", income_flag=False,
            deferrable=False, partial_payment_allowed=False,
        )
        memo_rules.addMemoRule(
            memo_regex="food", account_from="Checking", account_to=None,
            transaction_priority=2,
        )
        result = self._run_approximate(
            start_date, end_date, self._approximate_checking(), budget, memo_rules
        )
        assert result.forecast_df["Date"].tolist() == [start_date, end_date]
        assert result.forecast_df.iloc[-1]["Checking"] == 690.0
        assert result.forecast_df.iloc[-1]["Memo"] == "food x31 (Checking -$310.00)"

    # @pytest.mark.skip
    # def test_forecast_longer_than_satisfice(self):
    #     # if satisfice fails on the second day of the forecast, there is weirdness

    #     start_date = "20000101"
    #     end_date = "20000104"

    #     account_set = AccountSet([])
    #     line_item_set = LineItemSet([])
    #     memo_rule_set = MemoRuleSet([])

    #     account_set.createAccount(
    #         name="Checking",
    #         balance=100,
    #         min_balance=0,
    #         max_balance=float("Inf"),
    #         account_type="checking",
    #         primary_checking_ind=True,
    #     )

    #     line_item_set.addLineItem(
    #         start_date="20000101",
    #         end_date="20000104",
    #         priority=1,
    #         interval="daily",
    #         amount=50,
    #         memo="dummy memo",
    #     )

    #     memo_rule_set.addMemoRule(
    #         memo_regex=".*",
    #         account_from="Checking",
    #         account_to=None,
    #         transaction_priority=1,
    #     )

    #     milestone_set = MilestoneSet([], [], [])

    #     # expected_result_df = pd.DataFrame({
    #     #     'Date': ['20000101', '20000102', '20000103'],
    #     #     'Checking': [0, 0, 0],
    #     #     'Credit: Curr Stmt Bal': [0, 0, 0],
    #     #     'Credit: Prev Stmt Bal': [0, 0, 0],
    #     #     'Memo': ['', '', '']
    #     # })
    #     # expected_result_df.Date = [datetime.datetime.strptime(x, '%Y%m%d') for x in
    #     #                            expected_result_df.Date]
    #     #
    #     # E = self.compute_forecast_and_actual_vs_expected(account_set,
    #     #                                                  line_item_set,
    #     #                                                  memo_rule_set,
    #     #                                                  start_date,
    #     #                                                  end_date,
    #     #                                                  expected_result_df,
    #     #                                                  test_description)

    #     E = ExpenseForecastInitialConditions(
    #         datetime.datetime.strptime(start_date, "%Y%m%d").date(),
    #         datetime.datetime.strptime(end_date, "%Y%m%d").date(),
    #         account_set,
    #         line_item_set,
    #         memo_rule_set,
    #     )

    # @pytest.mark.skip
    # @pytest.mark.unit
    # @pytest.mark.parametrize(
    #     "test_description,account_set,line_item_set,memo_rule_set,start_date,end_date,milestone_set,account_milestone_names,expected_milestone_dates",
    #     [
    #         (
    #             "test_account_milestone",
    #             AccountSet(
    #                 checking_acct_list(10) + credit_acct_list(0, 0, 0.05)
    #             ),
    #             LineItemSet(
    #                 [
    #                     LineItem(
    #                         datetime.datetime.strptime("20000102",'%Y%m%d'),
    #                         datetime.datetime.strptime("20000102",'%Y%m%d'),
    #                         1, "once", 10, "test txn"
    #                     )
    #                 ]
    #             ),
    #             MemoRuleSet([MemoRule(".*", "Checking", None, 1)]),
    #             "20000101",
    #             "20000103",
    #             MilestoneSet(
    #                 account_milestones=[
    #                     AccountMilestone(
    #                         "test account milestone", "Checking", 0, 0
    #                     )
    #                 ],
    #             ),
    #             ["test account milestone"],
    #             ["20000102"],
    #         ),
    #     ],
    # )
    # def test_evaluate_account_milestone(
    #     self,
    #     test_description,
    #     account_set,
    #     line_item_set,
    #     memo_rule_set,
    #     start_date,
    #     end_date,
    #     milestone_set,
    #     account_milestone_names,
    #     expected_milestone_dates,
    # ):
    #     E = ExpenseForecastInitialConditions(
    #         datetime.datetime.strptime(start_date, "%Y%m%d").date(),
    #         datetime.datetime.strptime(end_date, "%Y%m%d").date(),
    #         account_set,
    #         line_item_set,
    #         memo_rule_set,
    #     )
    #     E = ForecastHandler().runForecast(E, milestone_set)
    #     assert len(account_milestone_names) == len(expected_milestone_dates)

    #     for i in range(0, len(account_milestone_names)):
    #         try:
    #             am_name = account_milestone_names[i]
    #             assert (
    #                 E.account_milestone_results[am_name] == expected_milestone_dates[i]
    #             )
    #         except Exception as e:
    #             print(
    #                 str(account_milestone_names[i])
    #                 + " did not match expected milestone date"
    #             )
    #             print("Received: " + str(E.account_milestone_results[am_name]))
    #             print("Expected: " + str(expected_milestone_dates[i]))
    #             raise e

    # @pytest.mark.skip
    # @pytest.mark.unit
    # @pytest.mark.parametrize(
    #     "test_description,account_set,line_item_set,memo_rule_set,start_date,end_date,milestone_set,memo_milestone_names,expected_milestone_dates",
    #     [
    #         (
    #             "test_memo_milestone",
    #             AccountSet(
    #                 checking_acct_list(10) + credit_acct_list(0, 0, 0.05)
    #             ),
    #             LineItemSet(
    #                 [
    #                     LineItem(
    #                         datetime.datetime.strptime("20000102",'%Y%m%d'), datetime.datetime.strptime("20000102",'%Y%m%d'), 1, "once", 10, "memo milestone"
    #                     )
    #                 ]
    #             ),
    #             MemoRuleSet([MemoRule(".*", "Checking", None, 1)]),
    #             "20000101",
    #             "20000103",
    #             MilestoneSet(
    #                 memo_milestones=[
    #                     MemoMilestone(
    #                         "test memo milestone", "memo milestone"
    #                     )
    #                 ],
    #             ),
    #             ["test memo milestone"],
    #             [datetime.datetime.strptime("20000102",'%Y%m%d')],
    #         ),
    #     ],
    # )
    # def test_evaluate_memo_milestone(
    #     self,
    #     test_description,
    #     account_set,
    #     line_item_set,
    #     memo_rule_set,
    #     start_date,
    #     end_date,
    #     milestone_set,
    #     memo_milestone_names,
    #     expected_milestone_dates,
    # ):
    #     E = ExpenseForecastInitialConditions(
    #         datetime.datetime.strptime(start_date, "%Y%m%d").date(),
    #         datetime.datetime.strptime(end_date, "%Y%m%d").date(),
    #         account_set,
    #         line_item_set,
    #         memo_rule_set,
    #     )
    #     E = ForecastHandler().runForecast(E, milestone_set)

    #     assert len(memo_milestone_names) == len(expected_milestone_dates)

    #     for i in range(0, len(memo_milestone_names)):
    #         try:
    #             mm_name = memo_milestone_names[i]
    #             assert E.memo_milestone_results[mm_name] == expected_milestone_dates[i]
    #         except Exception as e:
    #             print(
    #                 str(memo_milestone_names[i])
    #                 + " did not match expected milestone date"
    #             )
    #             print("Received: " + str(E.memo_milestone_results[mm_name]))
    #             print("Expected: " + str(expected_milestone_dates[i]))
    #             raise e

    # @pytest.mark.skip
    # @pytest.mark.unit
    # @pytest.mark.parametrize(
    #     "test_description,account_set,line_item_set,memo_rule_set,start_date,end_date,milestone_set,composite_milestone_names,expected_milestone_dates",
    #     [
    #         (
    #             "test composite milestone",
    #             AccountSet(
    #                 checking_acct_list(10) + credit_acct_list(0, 0, 0.05)
    #             ),
    #             LineItemSet(
    #                 [
    #                     LineItem(
    #                         datetime.datetime.strptime("20000102",'%Y%m%d'), datetime.datetime.strptime("20000102",'%Y%m%d'), 1, "once", 10, "memo milestone"
    #                     )
    #                 ]
    #             ),
    #             MemoRuleSet([MemoRule(".*", "Checking", None, 1)]),
    #             "20000101",
    #             "20000103",
    #             MilestoneSet(
    #                 account_milestones=[
    #                     AccountMilestone(
    #                         "test account milestone", "Checking", 0, 0
    #                     )
    #                 ],
    #                 memo_milestones=[
    #                     MemoMilestone(
    #                         "test memo milestone", "memo milestone"
    #                     )
    #                 ],
    #                 composite_milestones=[
    #                     CompositeMilestone(
    #                         "test composite milestone",
    #                         [
    #                             AccountMilestone(
    #                                 "test account milestone", "Checking", 0, 0
    #                             )
    #                         ],
    #                         [
    #                             MemoMilestone(
    #                                 "test memo milestone", "memo milestone"
    #                             )
    #                         ],
    #                     )
    #                 ],
    #             ),
    #             ["test composite milestone"],
    #             [datetime.datetime.strptime("20000102",'%Y%m%d')],
    #         ),
    #     ],
    # )
    # def test_evaluate_composite_milestone(
    #     self,
    #     test_description,
    #     account_set,
    #     line_item_set,
    #     memo_rule_set,
    #     start_date,
    #     end_date,
    #     milestone_set,
    #     composite_milestone_names,
    #     expected_milestone_dates,
    # ):

    #     E = ExpenseForecastInitialConditions(
    #         datetime.datetime.strptime(start_date, "%Y%m%d").date(),
    #         datetime.datetime.strptime(end_date, "%Y%m%d").date(),
    #         account_set,
    #         line_item_set,
    #         memo_rule_set,
    #     )
    #     E = ForecastHandler().runForecast(E, milestone_set)
    #     assert len(composite_milestone_names) == len(expected_milestone_dates)

    #     for i in range(0, len(composite_milestone_names)):
    #         cm_name = composite_milestone_names[i]

    #         try:
    #             assert E.composite_milestone_results[cm_name] == expected_milestone_dates[i]
    #         except Exception:
    #             print(f"{cm_name} did not match expected milestone date")
    #             print("Received: " + str(E.composite_milestone_results[cm_name]))
    #             print("Expected: " + str(expected_milestone_dates[i]))
    #             raise


    #     # todo what should we do here?

    #     # with pytest.raises(ValueError):
    #     #     E.runForecast()

    #     # log_in_color(logger,'white', 'debug', 'Confirmed:')
    #     # log_in_color(logger,'white', 'debug', E.confirmed_df.to_string())
    #     # log_in_color(logger,'white', 'debug', 'Deferred:')
    #     # log_in_color(logger,'white', 'debug', E.deferred_df.to_string())
    #     # log_in_color(logger,'white', 'debug', 'Skipped:')
    #     # log_in_color(logger,'white', 'debug', E.skipped_df.to_string())
    #     # log_in_color(logger,'white', 'debug', 'Forecast:')
    #     # log_in_color(logger,'white', 'debug', E.forecast_df.to_string())

    # @pytest.mark.skip
    # @pytest.mark.unit
    # @pytest.mark.parametrize(
    #     "test_description,account_set,line_item_set,memo_rule_set,start_date,end_date,milestone_set,expected_result_df",
    #     [
    #         (
    #             "test_next_income_date",
    #             AccountSet(checking_acct_list(1000)),
    #             LineItemSet(
    #                 [
    #                     LineItem(datetime.datetime.strptime("20000102","%Y%m%d"),datetime.datetime.strptime("20000102","%Y%m%d"),
    #                         1,
    #                         "once",
    #                         100,
    #                         "income 1",

    #                     ),
    #                     LineItem(datetime.datetime.strptime("20000104","%Y%m%d"),datetime.datetime.strptime("20000104","%Y%m%d"),
    #                         1,
    #                         "once",
    #                         100,
    #                         "income 2",

    #                     ),
    #                 ]
    #             ),
    #             MemoRuleSet([MemoRule(".*", None, "Checking", 1)]),
    #             "20000101",
    #             datetime.datetime.strptime("20000105","%Y%m%d"),
    #             MilestoneSet(),
    #             pd.DataFrame(
    #                 {
    #                     "Date": [
    #                         "20000101",
    #                         "20000102",
    #                         "20000103",
    #                         "20000104",
    #                         "20000105",
    #                     ],
    #                     "Checking": [1000, 1100, 1100, 1200, 1200],
    #                     "Interest Accrued": [0, 0, 0, 0, 0],
    #                     "Net Gain": [0, 100, 0, 100, 0],
    #                     "Net Loss": [0, 0, 0, 0, 0],
    #                     "Net Worth": [1000, 1100, 1100, 1200, 1200],
    #                     "Loan Total": [0, 0, 0, 0, 0],
    #                     "CC Debt Total": [0, 0, 0, 0, 0],
    #                     "Liquid Total": [1000, 1100, 1100, 1200, 1200],
    #                     "Next Income Date": [
    #                         "20000102",
    #                         "20000104",
    #                         "20000104",
    #                         "",
    #                         "",
    #                     ],
    #                     "Memo Directives": [
    #                         "",
    #                         "INCOME (Checking +$100.00)",
    #                         "",
    #                         "INCOME (Checking +$100.00)",
    #                         "",
    #                     ],
    #                     "Memo": [
    #                         "",
    #                         "income 1 (Checking +$100.00)",
    #                         "",
    #                         "income 2 (Checking +$100.00)",
    #                         "",
    #                     ],
    #                 }
    #             ),
    #         ),
    #     ],
    # )
    # def test_next_income_date(
    #     self,
    #     test_description,
    #     account_set,
    #     line_item_set,
    #     memo_rule_set,
    #     start_date,
    #     end_date,
    #     milestone_set,
    #     expected_result_df,
    # ):
    #     expected_result_df.Date = [
    #         datetime.datetime.strptime(x, "%Y%m%d") for x in expected_result_df.Date
    #     ]

    #     E = self.compute_forecast_and_actual_vs_expected(
    #         account_set,
    #         line_item_set,
    #         memo_rule_set,
    #         start_date,
    #         end_date,
    #         milestone_set,
    #         expected_result_df,
    #         test_description,
    #     )

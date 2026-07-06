import pytest
from datetime import date
from expense_forecast.AccountSet import AccountSet
from expense_forecast.BudgetSet import BudgetSet
from expense_forecast.MemoRuleSet import MemoRuleSet
from expense_forecast.MilestoneSet import MilestoneSet
from expense_forecast.ExpenseForecastInitialConditions import ExpenseForecastInitialConditions
from expense_forecast.ExpenseForecastResult import ExpenseForecastResult
from expense_forecast.ForecastHandler import ForecastHandler

import pandas as pd

class TestForecastHandler:

    # Note that debug true and debug false cases produce the same output and that is correct
    @pytest.mark.integration
    def test_ForecastHandler__debug_t_and_f__checking_only(self):
        start_date = date(2026,6,1)
        end_date = date(2026,6,10)
        
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

        MS = MilestoneSet()

        E_IO = ExpenseForecastInitialConditions(
            start_date=start_date,
            end_date=end_date,
            account_set=A,
            budget_set=B,
            memo_rule_set=M,
            milestone_set=MS)
        
        
        
        expected_final = pd.DataFrame(
            {
                "Date": [date(2026,6,10)],
                "Checking": [1000.0],
                "Marginal Interest": [0.0],
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
            "Marginal Interest",
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
        assert R__debug_true.forecast_df.shape[1] == 12

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
            "Marginal Interest",
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
        assert R__debug_false.forecast_df.shape[1] == 12

        pd.testing.assert_frame_equal(
            R__debug_false.forecast_df.tail(1),
            expected_final,
        )

    @pytest.mark.integration
    def test_ForecastHandler__debug_t_and_f__checking_and_credit__no_cc_bal(self):
        start_date = date(2026,6,1)
        end_date = date(2026,6,5)
        
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
            budget_set=B,
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
                "Marginal Interest": [0.0],
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
            "Marginal Interest",
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
                "Credit": [0.0],
                "Marginal Interest": [0.0],
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
            "Marginal Interest",
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
        assert R__debug_false.forecast_df.shape[1] == 13

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

        A.createLoanAccount(
            name="Loan", 
            principal_balance=15_000, 
            interest_balance=500, 
            min_balance=0, 
            max_balance=25_000, 
            billing_start_date=date(2030,1,3),
            apr=0.07, 
            minimum_payment=212.00, 
            end_of_previous_cycle_balance=15_000
        )

        MS = MilestoneSet()

        E_IO = ExpenseForecastInitialConditions(
            start_date=start_date,
            end_date=end_date,
            account_set=A,
            budget_set=B,
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
                "Loan: Loan End of Prev Cycle Bal": [15000.0],
                "Marginal Interest": [0.0],
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
            "Loan: Loan End of Prev Cycle Bal",
            "Marginal Interest",
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
                "Marginal Interest": [0.0],
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
            "Marginal Interest",
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
        assert R__debug_false.forecast_df.shape[1] == 13

        pd.testing.assert_frame_equal(
            R__debug_false.forecast_df.tail(1),
            expected_final__debug_false,
        )


    @pytest.mark.integration
    def test_ForecastHandler__checking_and_credit__min_cc_payment(self):
        start_date = date(2026,6,1)
        end_date = date(2026,6,5)
        
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
            budget_set=B,
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
                "Marginal Interest": [23.33],
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
                "Marginal Interest": [0.0],
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
        B = BudgetSet()
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
            B.addBudgetItem(
                start_date=payment_date,
                end_date=payment_date,
                priority=1,
                cadence="once",
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
            budget_set=B,
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
                "Marginal Interest": [None],
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
                "Marginal Interest": [None],
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
        expected_billing_date_state["Marginal Interest"] = marginal_interest
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
        expected_final["Marginal Interest"] = 0.0
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
        B = BudgetSet()
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
            end_of_previous_cycle_balance=principal_balance,
        )

        if payment_date is not None:
            B.addBudgetItem(
                start_date=payment_date,
                end_date=payment_date,
                priority=1,
                cadence="once",
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
            budget_set=B,
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

    def _loan_expected_rows_with_placeholders(self):
        expected_billing_date_state = pd.DataFrame(
            {
                "Date": [date(2026,6,3)],
                "Checking": [None],
                "Loan": [None],
                "Loan: Principal Balance": [None],
                "Loan: Interest": [None],
                "Loan: Loan Billing Cycle Payment Bal": [None],
                "Loan: Loan End of Prev Cycle Bal": [None],
                "Marginal Interest": [None],
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
                "Loan: Loan End of Prev Cycle Bal": [None],
                "Marginal Interest": [0.0],
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
        loan_end_of_previous_cycle_balance,
        marginal_interest,
        memo_directives,
    ):
        expected_billing_date_state["Checking"] = checking
        expected_billing_date_state["Loan"] = loan
        expected_billing_date_state["Loan: Principal Balance"] = principal_balance
        expected_billing_date_state["Loan: Interest"] = interest_balance
        expected_billing_date_state["Loan: Loan Billing Cycle Payment Bal"] = (
            billing_cycle_payment_balance
        )
        expected_billing_date_state["Loan: Loan End of Prev Cycle Bal"] = (
            loan_end_of_previous_cycle_balance
        )
        expected_billing_date_state["Marginal Interest"] = marginal_interest
        expected_billing_date_state["Net Gain"] = 0.0
        expected_billing_date_state["Net Loss"] = marginal_interest
        expected_billing_date_state["Net Worth"] = checking - loan
        expected_billing_date_state["Loan Total"] = loan
        expected_billing_date_state["CC Debt Total"] = 0.0
        expected_billing_date_state["Liquid Total"] = checking
        expected_billing_date_state["Memo Directives"] = memo_directives
        expected_billing_date_state["Memo"] = ""

        expected_final["Checking"] = checking
        expected_final["Loan"] = loan
        expected_final["Loan: Principal Balance"] = principal_balance
        expected_final["Loan: Interest"] = interest_balance
        expected_final["Loan: Loan Billing Cycle Payment Bal"] = (
            billing_cycle_payment_balance
        )
        expected_final["Loan: Loan End of Prev Cycle Bal"] = (
            loan_end_of_previous_cycle_balance
        )
        expected_final["Marginal Interest"] = 0.0
        expected_final["Net Gain"] = 0.0
        expected_final["Net Loss"] = 0.0
        expected_final["Net Worth"] = checking - loan
        expected_final["Loan Total"] = loan
        expected_final["CC Debt Total"] = 0.0
        expected_final["Liquid Total"] = checking
        expected_final["Memo Directives"] = ""
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
        expected_billing_date_state["Marginal Interest"] = expected_interest
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
        expected_final["Marginal Interest"] = 0.0
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
            loan_end_of_previous_cycle_balance=960.2,
            marginal_interest=0.2,
            memo_directives="LOAN INTEREST (Loan: Interest +$0.20); LOAN MIN PAYMENT (Loan: Interest -$0.20); LOAN MIN PAYMENT (Loan: Principal Balance -$39.80); LOAN MIN PAYMENT (Checking -$40.00)",
        )
        self._run_checking_and_loan_min_payment_case(
            expected_billing_date_state=expected_billing_date_state,
            expected_final=expected_final,
        )
    
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
            loan_end_of_previous_cycle_balance=960.2,
            marginal_interest=0.2,
            memo_directives="LOAN INTEREST (Loan: Interest +$0.20); LOAN MIN PAYMENT (Loan: Interest -$0.20); LOAN MIN PAYMENT (Loan: Principal Balance -$19.80); LOAN MIN PAYMENT (Checking -$20.00)",
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
            loan_end_of_previous_cycle_balance=960.0,
            marginal_interest=0.19,
            memo_directives="LOAN INTEREST (Loan: Interest +$0.19)",
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
            loan_end_of_previous_cycle_balance=940.0,
            marginal_interest=0.19,
            memo_directives="LOAN INTEREST (Loan: Interest +$0.19)",
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
            loan_end_of_previous_cycle_balance=940.2,
            marginal_interest=0.2,
            memo_directives="LOAN INTEREST (Loan: Interest +$0.20); LOAN MIN PAYMENT (Loan: Interest -$0.20); LOAN MIN PAYMENT (Loan: Principal Balance -$39.80); LOAN MIN PAYMENT (Checking -$40.00)",
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
            loan_end_of_previous_cycle_balance=920.2,
            marginal_interest=0.2,
            memo_directives="LOAN INTEREST (Loan: Interest +$0.20); LOAN MIN PAYMENT (Loan: Interest -$0.20); LOAN MIN PAYMENT (Loan: Principal Balance -$39.80); LOAN MIN PAYMENT (Checking -$40.00)",
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
            loan_end_of_previous_cycle_balance=900.2,
            marginal_interest=0.2,
            memo_directives="LOAN INTEREST (Loan: Interest +$0.20); LOAN MIN PAYMENT (Loan: Interest -$0.20); LOAN MIN PAYMENT (Loan: Principal Balance -$39.80); LOAN MIN PAYMENT (Checking -$40.00)",
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
    #     B = BudgetSet()
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

    #     B.addBudgetItem(
    #         start_date=start_date,
    #         end_date=end_date,
    #         priority=1,
    #         cadence="daily",
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
    #         budget_set=B,
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

    #         "Marginal Interest",
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
            cadence="once",
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
            cadence="once",
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










    # @pytest.mark.skip
    # def test_forecast_longer_than_satisfice(self):
    #     # if satisfice fails on the second day of the forecast, there is weirdness

    #     start_date = "20000101"
    #     end_date = "20000104"

    #     account_set = AccountSet([])
    #     budget_set = BudgetSet([])
    #     memo_rule_set = MemoRuleSet([])

    #     account_set.createAccount(
    #         name="Checking",
    #         balance=100,
    #         min_balance=0,
    #         max_balance=float("Inf"),
    #         account_type="checking",
    #         primary_checking_ind=True,
    #     )

    #     budget_set.addBudgetItem(
    #         start_date="20000101",
    #         end_date="20000104",
    #         priority=1,
    #         cadence="daily",
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
    #     #                                                  budget_set,
    #     #                                                  memo_rule_set,
    #     #                                                  start_date,
    #     #                                                  end_date,
    #     #                                                  expected_result_df,
    #     #                                                  test_description)

    #     E = ExpenseForecastInitialConditions(
    #         datetime.datetime.strptime(start_date, "%Y%m%d").date(),
    #         datetime.datetime.strptime(end_date, "%Y%m%d").date(),
    #         account_set,
    #         budget_set,
    #         memo_rule_set,
    #     )

    # @pytest.mark.skip
    # @pytest.mark.unit
    # @pytest.mark.parametrize(
    #     "test_description,account_set,budget_set,memo_rule_set,start_date,end_date,milestone_set,account_milestone_names,expected_milestone_dates",
    #     [
    #         (
    #             "test_account_milestone",
    #             AccountSet(
    #                 checking_acct_list(10) + credit_acct_list(0, 0, 0.05)
    #             ),
    #             BudgetSet(
    #                 [
    #                     BudgetItem(
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
    #     budget_set,
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
    #         budget_set,
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
    #     "test_description,account_set,budget_set,memo_rule_set,start_date,end_date,milestone_set,memo_milestone_names,expected_milestone_dates",
    #     [
    #         (
    #             "test_memo_milestone",
    #             AccountSet(
    #                 checking_acct_list(10) + credit_acct_list(0, 0, 0.05)
    #             ),
    #             BudgetSet(
    #                 [
    #                     BudgetItem(
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
    #     budget_set,
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
    #         budget_set,
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
    #     "test_description,account_set,budget_set,memo_rule_set,start_date,end_date,milestone_set,composite_milestone_names,expected_milestone_dates",
    #     [
    #         (
    #             "test composite milestone",
    #             AccountSet(
    #                 checking_acct_list(10) + credit_acct_list(0, 0, 0.05)
    #             ),
    #             BudgetSet(
    #                 [
    #                     BudgetItem(
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
    #     budget_set,
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
    #         budget_set,
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
    #     "test_description,account_set,budget_set,memo_rule_set,start_date,end_date,milestone_set,expected_result_df",
    #     [
    #         (
    #             "test_next_income_date",
    #             AccountSet(checking_acct_list(1000)),
    #             BudgetSet(
    #                 [
    #                     BudgetItem(datetime.datetime.strptime("20000102","%Y%m%d"),datetime.datetime.strptime("20000102","%Y%m%d"),
    #                         1,
    #                         "once",
    #                         100,
    #                         "income 1",

    #                     ),
    #                     BudgetItem(datetime.datetime.strptime("20000104","%Y%m%d"),datetime.datetime.strptime("20000104","%Y%m%d"),
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
    #                     "Marginal Interest": [0, 0, 0, 0, 0],
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
    #     budget_set,
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
    #         budget_set,
    #         memo_rule_set,
    #         start_date,
    #         end_date,
    #         milestone_set,
    #         expected_result_df,
    #         test_description,
    #     )

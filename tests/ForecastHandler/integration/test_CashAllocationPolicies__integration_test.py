from datetime import date

import pytest

from expense_forecast.AccountSet import AccountSet
from expense_forecast.ExpenseForecastInitialConditions import ExpenseForecastInitialConditions
from expense_forecast.FixedMonthlyInvestmentPolicy import FixedMonthlyInvestmentPolicy
from expense_forecast.ForecastHandler import ForecastHandler
from expense_forecast.ForecastPolicySet import ForecastPolicySet
from expense_forecast.IncomePercentageInvestmentPolicy import IncomePercentageInvestmentPolicy
from expense_forecast.LineItemSet import LineItemSet
from expense_forecast.MemoRuleSet import MemoRuleSet
from expense_forecast.PeriodicInvestmentContributionCapPolicy import PeriodicInvestmentContributionCapPolicy
from expense_forecast.SurplusDebtPaymentPolicy import SurplusDebtPaymentPolicy
from expense_forecast.CurrentStatementBalancePaymentPolicy import (
    CurrentStatementBalancePaymentPolicy,
)


def _base(accounts, budget, rules, *policies):
    return ExpenseForecastInitialConditions(
        date(2026, 2, 1), date(2026, 2, 4), accounts, budget, rules,
        policy_set=ForecastPolicySet(*policies),
    )


def _checking_and_investment():
    accounts = AccountSet()
    accounts.createCheckingAccount("Checking", 1000, 0, float("inf"), True)
    accounts.createInvestmentAccount("Brokerage", 0, date(2026, 2, 1), 0)
    return accounts


def test_fixed_monthly_investment_executes_at_policy_priority():
    result = ForecastHandler.runForecast(
        _base(
            _checking_and_investment(), LineItemSet(), MemoRuleSet(),
            FixedMonthlyInvestmentPolicy("Brokerage", 250, priority=2, day=2),
        )
    )

    assert result.forecast_df.iloc[-1]["Checking"] == 750
    assert result.forecast_df.iloc[-1]["Brokerage"] == 250
    assert result.policy_results["fixed_monthly_investment:Brokerage"]["executed"] == 250


def test_income_percentage_investment_uses_lower_priority_income():
    accounts = _checking_and_investment()
    budget, rules = LineItemSet(), MemoRuleSet()
    budget.addLineItem(
        date(2026, 2, 2), date(2026, 2, 2), 1, "once", 500, "income",
        income_flag=True,
    )
    rules.addMemoRule("income", None, "Checking", 1)

    result = ForecastHandler.runForecast(
        _base(
            accounts, budget, rules,
            IncomePercentageInvestmentPolicy("Brokerage", 0.10, priority=2),
        )
    )

    assert result.forecast_df.iloc[-1]["Checking"] == 1450
    assert result.forecast_df.iloc[-1]["Brokerage"] == 50
    html = ForecastHandler.generateHTMLreport(result)
    income_section = html.split(">Income</h2>", 1)[1].split(">Non-Essential Transactions</h2>", 1)[0]
    assert "income" in income_section


def test_surplus_loan_policy_uses_snowball():
    accounts = AccountSet()
    accounts.createCheckingAccount("Checking", 1000, 500, float("inf"), True)
    accounts.createLoanAccount(
        name="Large", principal_balance=900, interest_balance=0,
        min_balance=0, max_balance=2000,
        billing_start_date=date(2026, 1, 1), minimum_payment=40,
        billing_cycle_payment_balance=0, apr=0.10,
    )
    accounts.createLoanAccount(
        name="Small", principal_balance=300, interest_balance=0,
        min_balance=0, max_balance=2000,
        billing_start_date=date(2026, 1, 1), minimum_payment=40,
        billing_cycle_payment_balance=0, apr=0.05,
    )

    result = ForecastHandler.runForecast(
        _base(
            accounts, LineItemSet(), MemoRuleSet(),
            SurplusDebtPaymentPolicy("loan", "snowball", priority=2),
        )
    )

    assert result.forecast_df.iloc[-1]["Checking"] == 500
    assert result.forecast_df.iloc[-1]["Small"] == 0
    assert result.forecast_df.iloc[-1]["Large"] == pytest.approx(700.86)
    html = ForecastHandler.generateHTMLreport(result)
    loan_section = html.split(">Loan Payments</h2>", 1)[1].split(">All Transactions</h2>", 1)[0]
    assert "ALL_LOANS" in loan_section
    assert "Policy" in loan_section


def test_periodic_cap_limits_later_policy_contribution():
    result = ForecastHandler.runForecast(
        _base(
            _checking_and_investment(), LineItemSet(), MemoRuleSet(),
            PeriodicInvestmentContributionCapPolicy(
                "Brokerage", 100, "month", priority=2
            ),
            FixedMonthlyInvestmentPolicy("Brokerage", 250, priority=3, day=2),
        )
    )

    assert result.forecast_df.iloc[-1]["Brokerage"] == 100
    fixed = result.policy_results["fixed_monthly_investment:Brokerage"]
    assert fixed["requested"] == 250
    assert fixed["executed"] == 100
    assert fixed["capped"] == 150
    assert fixed["status"] == "capped"


def test_credit_card_surplus_allocation_supports_avalanche_and_snowball():
    accounts = AccountSet()
    accounts.createCheckingAccount("Checking", 2_000, 500, float("inf"), True)
    accounts.createCreditCardAccount(
        name="High APR", current_statement_balance=0,
        previous_statement_balance=1_000,
        billing_start_date=date(2026, 1, 1), minimum_payment=40,
        end_of_previous_cycle_balance=1_000,
        min_balance=0, max_balance=5_000, apr=0.25,
    )
    accounts.createCreditCardAccount(
        name="Small Balance", current_statement_balance=0,
        previous_statement_balance=200,
        billing_start_date=date(2026, 1, 1), minimum_payment=40,
        end_of_previous_cycle_balance=200,
        min_balance=0, max_balance=5_000, apr=0.10,
    )

    avalanche = accounts.allocate_additional_credit_card_payments(
        300, strategy="avalanche"
    )
    snowball = accounts.allocate_additional_credit_card_payments(
        300, strategy="snowball"
    )

    assert avalanche[0][1] == "High APR"
    assert snowball[0][1] == "Small Balance"
    assert snowball[0][2] == 200


def test_approximate_surplus_policy_occurs_only_on_output_boundaries():
    accounts = AccountSet()
    accounts.createCheckingAccount("Checking", 1_000, 500, float("inf"), True)
    accounts.createLoanAccount(
        name="Loan", principal_balance=1_000, interest_balance=0,
        min_balance=0, max_balance=2_000,
        billing_start_date=date(2026, 1, 1), minimum_payment=0,
        billing_cycle_payment_balance=0, apr=0,
    )
    conditions = ExpenseForecastInitialConditions(
        date(2026, 2, 1), date(2026, 4, 4), accounts,
        LineItemSet(), MemoRuleSet(),
        policy_set=ForecastPolicySet(
            SurplusDebtPaymentPolicy("loan", "avalanche", priority=2)
        ),
    )

    result = ForecastHandler.runForecastApproximate(conditions)
    policy_rows = result.confirmed_df.loc[
        result.confirmed_df["Memo"].str.startswith("POLICY surplus_debt_payment")
    ]

    assert set(policy_rows["Date"]) <= {date(2026, 3, 1), date(2026, 4, 1), date(2026, 4, 4)}


def test_approximate_current_statement_policy_pays_current_cycle_charges():
    accounts = AccountSet()
    accounts.createCheckingAccount("Checking", 5_000, 0, float("inf"), True)
    accounts.createCreditCardAccount(
        name="Card", current_statement_balance=100,
        previous_statement_balance=1_000,
        billing_start_date=date(2026, 3, 1), minimum_payment=0,
        end_of_previous_cycle_balance=1_000,
        min_balance=0, max_balance=10_000, apr=0,
    )
    budget, rules = LineItemSet(), MemoRuleSet()
    budget.addLineItem(
        date(2026, 2, 10), date(2026, 2, 10), 1, "once", 200,
        "cycle purchase", income_flag=False,
    )
    rules.addMemoRule("cycle purchase", "Card", None, 1)
    conditions = ExpenseForecastInitialConditions(
        date(2026, 2, 1), date(2026, 3, 2), accounts, budget, rules,
        policy_set=ForecastPolicySet(
            CurrentStatementBalancePaymentPolicy("Card", priority=1)
        ),
    )

    result = ForecastHandler.runForecastApproximate(conditions)
    policy_rows = result.confirmed_df.loc[
        result.confirmed_df["Memo"].str.startswith(
            "POLICY current_statement_balance_payment:Card"
        )
    ]

    assert policy_rows["Date"].tolist() == [date(2026, 2, 28)]
    assert policy_rows["Amount"].sum() == pytest.approx(300)


@pytest.mark.parametrize("approximate", [False, True])
def test_surplus_debt_policy_preserves_future_mandatory_payment(approximate):
    """A surplus payment must be sized by recursively forecasting its suffix."""
    accounts = AccountSet()
    accounts.createCheckingAccount("Checking", 2_000, 500, float("inf"), True)
    accounts.createLoanAccount(
        name="Debt", principal_balance=1_000, interest_balance=0,
        min_balance=0, max_balance=5_000,
        billing_start_date=date(2026, 6, 15), minimum_payment=0,
        billing_cycle_payment_balance=0, apr=0,
    )
    budget, rules = LineItemSet(), MemoRuleSet()
    if approximate:
        start_date, payment_date, end_date = (
            date(2026, 1, 1), date(2026, 3, 1), date(2026, 3, 1)
        )
    else:
        start_date, payment_date, end_date = (
            date(2026, 2, 1), date(2026, 2, 3), date(2026, 2, 3)
        )
    budget.addLineItem(
        payment_date, payment_date, 1, "once", 600,
        "scheduled debt payment", partial_payment_allowed=False,
    )
    rules.addMemoRule("scheduled debt payment", "Checking", "Debt", 1)
    conditions = ExpenseForecastInitialConditions(
        start_date, end_date, accounts, budget, rules,
        policy_set=ForecastPolicySet(
            SurplusDebtPaymentPolicy("loan", "avalanche", priority=2)
        ),
    )

    runner = (
        ForecastHandler.runForecastApproximate
        if approximate else ForecastHandler.runForecast
    )
    result = runner(conditions)
    scheduled = result.confirmed_df.loc[
        result.confirmed_df["Memo"] == "scheduled debt payment"
    ]
    policy_rows = result.confirmed_df.loc[
        result.confirmed_df["Memo"].str.startswith("POLICY surplus_debt_payment")
    ]

    assert scheduled["Amount"].sum() == pytest.approx(600)
    if approximate:
        assert policy_rows["Amount"].sum() == pytest.approx(400, abs=0.01)
    else:
        assert policy_rows["Amount"].sum() <= 400.01
    expected_final_debt = 0 if approximate else 400
    assert result.forecast_df.iloc[-1]["Debt"] == pytest.approx(
        expected_final_debt, abs=0.01
    )

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

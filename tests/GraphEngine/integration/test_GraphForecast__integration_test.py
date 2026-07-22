from datetime import date

import pytest

from expense_forecast.AccountSet import AccountSet
from expense_forecast.ExpenseForecastInitialConditions import ExpenseForecastInitialConditions
from expense_forecast.ForecastHandler import ForecastHandler
from expense_forecast.ForecastPolicySet import ForecastPolicySet
from expense_forecast.LineItemSet import LineItemSet
from expense_forecast.MemoRuleSet import MemoRuleSet
from expense_forecast.SurplusSavingPolicy import SurplusSavingPolicy
from expense_forecast.graph_engine import GraphForecastRunner
from expense_forecast.InvestmentPolicies import FixedMonthlyInvestmentPolicy
from expense_forecast.MinimumCheckingBalancePolicy import MinimumCheckingBalancePolicy


def cash_conditions(*, second_account=False):
    accounts = AccountSet()
    accounts.createCheckingAccount("Checking", 500, 0, float("inf"), True)
    if second_account:
        accounts.createCheckingAccount("Savings", 0, 0, float("inf"), False)
    return accounts, LineItemSet(), MemoRuleSet()


@pytest.mark.parametrize("approximate", [False, True])
def test_income_and_spending_match_legacy_in_shadow_mode(approximate):
    accounts, budget, rules = cash_conditions()
    budget.addLineItem(date(2026, 1, 2), date(2026, 1, 2), 1, "once", 100, "food")
    budget.addLineItem(
        date(2026, 1, 3), date(2026, 1, 3), 1, "once", 1000, "paycheck",
        income_flag=True,
    )
    rules.addMemoRule("food", "Checking", None, 1)
    rules.addMemoRule("paycheck", None, "Checking", 1)
    conditions = ExpenseForecastInitialConditions(
        date(2026, 1, 1), date(2026, 1, 3), accounts, budget, rules
    )
    runner = ForecastHandler.runForecastApproximate if approximate else ForecastHandler.runForecast

    result = runner(conditions, engine="shadow")

    assert result.forecast_df.iloc[-1]["Checking"] == 1400
    assert result.graph_diagnostics.legacy_shadow_seconds is not None


@pytest.mark.parametrize("approximate", [False, True])
def test_checking_transfer_matches_legacy_in_shadow_mode(approximate):
    accounts, budget, rules = cash_conditions(second_account=True)
    budget.addLineItem(date(2026, 1, 2), date(2026, 1, 2), 1, "once", 200, "save")
    rules.addMemoRule("save", "Checking", "Savings", 1)
    conditions = ExpenseForecastInitialConditions(
        date(2026, 1, 1), date(2026, 1, 2), accounts, budget, rules
    )
    runner = ForecastHandler.runForecastApproximate if approximate else ForecastHandler.runForecast

    result = runner(conditions, engine="shadow")

    assert result.forecast_df.iloc[-1]["Savings"] == 200


@pytest.mark.parametrize("approximate", [False, True])
def test_empty_schedule_matches_legacy_in_shadow_mode(approximate):
    accounts, budget, rules = cash_conditions()
    conditions = ExpenseForecastInitialConditions(
        date(2026, 1, 1), date(2026, 1, 3), accounts, budget, rules
    )
    runner = ForecastHandler.runForecastApproximate if approximate else ForecastHandler.runForecast

    result = runner(conditions, engine="shadow")

    assert result.confirmed_df.empty
    assert result.forecast_df.iloc[-1]["Checking"] == 500


def test_same_day_transactions_follow_priority_order():
    accounts, budget, rules = cash_conditions()
    budget.addLineItem(date(2026, 1, 2), date(2026, 1, 2), 2, "once", 450, "optional")
    budget.addLineItem(date(2026, 1, 2), date(2026, 1, 2), 1, "once", 100, "mandatory")
    rules.addMemoRule("optional", "Checking", None, 2)
    rules.addMemoRule("mandatory", "Checking", None, 1)
    conditions = ExpenseForecastInitialConditions(
        date(2026, 1, 1), date(2026, 1, 2), accounts, budget, rules
    )

    result = ForecastHandler.runForecast(conditions, engine="shadow")

    assert result.confirmed_df["Memo"].tolist() == ["mandatory"]
    assert result.skipped_df["Memo"].tolist() == ["optional"]


def test_late_budget_change_reuses_checkpoints_and_matches_clean_graph():
    accounts, budget, rules = cash_conditions()
    budget.addLineItem(date(2026, 1, 2), date(2026, 1, 2), 1, "once", 50, "first")
    budget.addLineItem(date(2026, 1, 5), date(2026, 1, 5), 1, "once", 50, "late")
    rules.addMemoRule("first", "Checking", None, 1)
    rules.addMemoRule("late", "Checking", None, 1)
    conditions = ExpenseForecastInitialConditions(
        date(2026, 1, 1), date(2026, 1, 6), accounts, budget, rules
    )
    incremental = GraphForecastRunner(conditions)
    incremental.run()
    changed = LineItemSet([item for item in budget.line_items])
    changed.line_items[-1].amount = 75

    updated = incremental.update_budget(changed)
    clean_conditions = ExpenseForecastInitialConditions(
        date(2026, 1, 1), date(2026, 1, 6), accounts, changed, rules
    )
    clean = GraphForecastRunner(clean_conditions).run()

    assert updated.forecast_df.equals(clean.forecast_df)
    assert updated.graph_diagnostics.checkpoints_reused > 0


def test_partial_optional_payment_preserves_future_mandatory_cash():
    accounts, budget, rules = cash_conditions()
    accounts.accounts[0].min_balance = 100
    budget.addLineItem(
        date(2026, 1, 2), date(2026, 1, 2), 2, "once", 300, "optional",
        partial_payment_allowed=True,
    )
    budget.addLineItem(
        date(2026, 1, 3), date(2026, 1, 3), 1, "once", 300, "mandatory"
    )
    rules.addMemoRule("optional", "Checking", None, 2)
    rules.addMemoRule("mandatory", "Checking", None, 1)
    conditions = ExpenseForecastInitialConditions(
        date(2026, 1, 1), date(2026, 1, 3), accounts, budget, rules
    )
    result = ForecastHandler.runForecast(conditions, engine="shadow")

    optional = result.confirmed_df.loc[result.confirmed_df["Memo"] == "optional"]
    assert float(optional["Amount"].sum()) == 100


def test_approximate_deferrable_transaction_retries_on_next_income():
    accounts, budget, rules = cash_conditions()
    accounts.accounts[0].balance = 100
    budget.addLineItem(
        date(2026, 1, 2), date(2026, 1, 2), 2, "once", 200, "optional",
        deferrable=True,
    )
    budget.addLineItem(
        date(2026, 1, 3), date(2026, 1, 3), 1, "once", 500, "income",
        income_flag=True,
    )
    rules.addMemoRule("optional", "Checking", None, 2)
    rules.addMemoRule("income", None, "Checking", 1)
    conditions = ExpenseForecastInitialConditions(
        date(2026, 1, 1), date(2026, 1, 3), accounts, budget, rules
    )

    result = ForecastHandler.runForecastApproximate(conditions, engine="shadow")

    optional = result.confirmed_df.loc[result.confirmed_df["Memo"] == "optional"]
    assert optional["Date"].tolist() == [date(2026, 1, 3)]


def test_graph_mode_supports_cash_allocation_policy():
    accounts, budget, rules = cash_conditions(second_account=True)
    conditions = ExpenseForecastInitialConditions(
        date(2026, 1, 1), date(2026, 1, 2), accounts, budget, rules,
        policy_set=ForecastPolicySet(
            SurplusSavingPolicy("Savings", 100, priority=2)
        ),
    )

    result = ForecastHandler.runForecast(conditions, engine="shadow")

    assert result.forecast_df.iloc[-1]["Savings"] == 100
    assert result.policy_results["surplus_saving:Savings"]["executed"] == 100


@pytest.mark.parametrize("approximate", [False, True])
@pytest.mark.parametrize("debt_type", ["credit", "loan"])
def test_debt_payment_and_billing_state_match_shadow(approximate, debt_type):
    accounts, budget, rules = cash_conditions()
    accounts.accounts[0].balance = 2000
    if debt_type == "credit":
        accounts.createCreditCardAccount(
            "Debt", 0, 1000, 0, 25_000, date(2026, 6, 3), .25, 40, 1000
        )
    else:
        accounts.createLoanAccount(
            "Debt", 1000, 0, 0, 25_000, date(2026, 6, 3), .1, 40, 0
        )
    budget.addLineItem(date(2026, 6, 3), date(2026, 6, 3), 1, "once", 100, "pay")
    rules.addMemoRule("pay", "Checking", "Debt", 1)
    conditions = ExpenseForecastInitialConditions(
        date(2026, 6, 1), date(2026, 6, 5), accounts, budget, rules
    )
    runner = ForecastHandler.runForecastApproximate if approximate else ForecastHandler.runForecast

    result = runner(conditions, include_debug_columns=True, engine="shadow")

    assert result.graph_diagnostics.billing_cycles_recomputed > 0


@pytest.mark.parametrize("approximate", [False, True])
def test_investment_contribution_and_returns_match_shadow(approximate):
    accounts, budget, rules = cash_conditions()
    accounts.accounts[0].balance = 2000
    accounts.createInvestmentAccount("Brokerage", 1000, date(2026, 6, 2), .1)
    budget.addLineItem(date(2026, 6, 3), date(2026, 6, 3), 1, "once", 100, "invest")
    rules.addMemoRule("invest", "Checking", "Brokerage", 1)
    conditions = ExpenseForecastInitialConditions(
        date(2026, 6, 1), date(2026, 6, 5), accounts, budget, rules
    )
    runner = ForecastHandler.runForecastApproximate if approximate else ForecastHandler.runForecast

    result = runner(conditions, include_debug_columns=True, engine="shadow")

    assert result.forecast_df.iloc[-1]["Brokerage"] > 1100
    assert result.graph_diagnostics.investment_spans_recomputed > 0


def test_late_investment_change_reuses_account_checkpoints():
    accounts, budget, rules = cash_conditions()
    accounts.accounts[0].balance = 2000
    accounts.createInvestmentAccount("Brokerage", 1000, date(2026, 6, 1), .1)
    budget.addLineItem(date(2026, 6, 2), date(2026, 6, 2), 1, "once", 50, "early")
    budget.addLineItem(date(2026, 6, 9), date(2026, 6, 9), 1, "once", 50, "late")
    rules.addMemoRule("early", "Checking", "Brokerage", 1)
    rules.addMemoRule("late", "Checking", "Brokerage", 1)
    conditions = ExpenseForecastInitialConditions(
        date(2026, 6, 1), date(2026, 6, 10), accounts, budget, rules
    )
    runner = GraphForecastRunner(conditions)
    runner.run()
    changed = LineItemSet([item for item in budget.line_items])
    changed.line_items[-1].amount = 75

    updated = runner.update_budget(changed)
    clean_conditions = ExpenseForecastInitialConditions(
        date(2026, 6, 1), date(2026, 6, 10), accounts, changed, rules
    )
    clean = GraphForecastRunner(clean_conditions).run()

    assert updated.forecast_df.equals(clean.forecast_df)
    assert updated.graph_diagnostics.checkpoints_reused >= 8


@pytest.mark.parametrize("approximate", [False, True])
def test_fixed_investment_policy_matches_shadow(approximate):
    accounts, budget, rules = cash_conditions()
    accounts.accounts[0].balance = 1000
    accounts.createInvestmentAccount("Brokerage", 0, date(2026, 6, 1), 0)
    conditions = ExpenseForecastInitialConditions(
        date(2026, 6, 1), date(2026, 6, 5), accounts, budget, rules,
        policy_set=ForecastPolicySet(
            FixedMonthlyInvestmentPolicy("Brokerage", 100, priority=2, day=2)
        ),
    )
    runner = ForecastHandler.runForecastApproximate if approximate else ForecastHandler.runForecast

    result = runner(conditions, include_debug_columns=True, engine="shadow")

    assert result.policy_results["fixed_monthly_investment:Brokerage"]["executed"] == 100
    assert result.graph_diagnostics.policy_iterations == 1


@pytest.mark.parametrize("approximate", [False, True])
def test_minimum_checking_activation_matches_shadow(approximate):
    accounts, budget, rules = cash_conditions()
    accounts.accounts[0].balance = 100
    budget.addLineItem(
        date(2026, 1, 2), date(2026, 1, 2), 1, "once", 500, "income",
        income_flag=True,
    )
    budget.addLineItem(
        date(2026, 1, 2), date(2026, 1, 2), 3, "once", 200, "optional"
    )
    rules.addMemoRule("income", None, "Checking", 1)
    rules.addMemoRule("optional", "Checking", None, 3)
    conditions = ExpenseForecastInitialConditions(
        date(2026, 1, 1), date(2026, 1, 3), accounts, budget, rules,
        policy_set=ForecastPolicySet(MinimumCheckingBalancePolicy(400, priority=2)),
    )
    runner = ForecastHandler.runForecastApproximate if approximate else ForecastHandler.runForecast

    result = runner(conditions, engine="shadow")

    assert result.policy_results["minimum_checking_balance"]["status"] == "activated"


def test_invalid_engine_name_is_rejected():
    accounts, budget, rules = cash_conditions()
    conditions = ExpenseForecastInitialConditions(
        date(2026, 1, 1), date(2026, 1, 2), accounts, budget, rules
    )
    with pytest.raises(ValueError, match="engine"):
        ForecastHandler.runForecast(conditions, engine="missing")

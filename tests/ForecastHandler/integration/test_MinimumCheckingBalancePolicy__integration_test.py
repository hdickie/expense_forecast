from datetime import date
import logging
from unittest.mock import patch

import pytest

from expense_forecast.AccountSet import AccountSet
from expense_forecast.ExpenseForecastInitialConditions import ExpenseForecastInitialConditions
from expense_forecast.ExpenseForecastResult import ExpenseForecastResult
from expense_forecast.ForecastHandler import ForecastHandler
from expense_forecast.ForecastPolicySet import ForecastPolicySet
from expense_forecast.LineItemSet import LineItemSet
from expense_forecast.MemoRuleSet import MemoRuleSet
from expense_forecast.MinimumCheckingBalancePolicy import MinimumCheckingBalancePolicy
from expense_forecast.SurplusDebtPaymentPolicy import SurplusDebtPaymentPolicy


def _conditions(target, transactions, *, balance=0, min_balance=0):
    accounts = AccountSet()
    accounts.createCheckingAccount(
        "Checking", balance, min_balance, float("inf"), primary_checking_ind=True
    )
    budget = LineItemSet()
    rules = MemoRuleSet()
    for day, amount, memo, income, priority, deferrable, reducible in transactions:
        budget.addLineItem(
            start_date=day,
            end_date=day,
            priority=priority,
            interval="once",
            amount=amount,
            memo=memo,
            income_flag=income,
            deferrable=deferrable,
            partial_payment_allowed=reducible,
        )
        rules.addMemoRule(
            memo,
            None if income else "Checking",
            "Checking" if income else None,
            priority,
        )
    return ExpenseForecastInitialConditions(
        date(2026, 7, 1),
        date(2026, 7, 5),
        accounts,
        budget,
        rules,
        policy_set=ForecastPolicySet(MinimumCheckingBalancePolicy(target, priority=2)),
    )


@pytest.mark.integration
def test_policy_uses_earliest_stable_crossing_and_enforces_floor():
    conditions = _conditions(
        500,
        [
            (date(2026, 7, 2), 1000, "first income", True, 1, False, False),
            (date(2026, 7, 3), 800, "required expense", False, 1, False, False),
            (date(2026, 7, 4), 1000, "second income", True, 1, False, False),
            (date(2026, 7, 4), 600, "optional expense", False, 3, False, False),
        ],
    )

    result = ForecastHandler.runForecast(conditions)

    policy_result = result.policy_results["minimum_checking_balance"]
    assert policy_result["status"] == "activated"
    assert policy_result["activation_date"] == date(2026, 7, 4)
    assert result.forecast_df["Checking"].min() >= 0
    assert float(result.forecast_df.iloc[-1]["Checking"]) == 600
    assert result.confirmed_df["Memo"].eq("optional expense").any()


@pytest.mark.integration
def test_pre_activation_p2_is_deferred_or_skipped():
    conditions = _conditions(
        500,
        [
            (date(2026, 7, 1), 100, "rigid optional", False, 3, False, False),
            (date(2026, 7, 1), 100, "deferred optional", False, 3, True, False),
            (date(2026, 7, 2), 1000, "income", True, 1, False, False),
        ],
    )

    result = ForecastHandler.runForecast(conditions)

    assert result.skipped_df["Memo"].eq("rigid optional").any()
    assert result.confirmed_df["Memo"].eq("deferred optional").any()


@pytest.mark.integration
def test_never_achieved_warns_and_runs_without_the_policy():
    conditions = _conditions(
        2000,
        [
            (date(2026, 7, 2), 1000, "income", True, 1, False, False),
            (date(2026, 7, 3), 100, "rigid optional", False, 3, False, False),
            (date(2026, 7, 3), 100, "deferred optional", False, 3, True, False),
        ],
    )

    with patch("expense_forecast.ForecastHandler.logger.warning") as warning:
        result = ForecastHandler.runForecast(conditions)

    assert result.policy_results["minimum_checking_balance"]["status"] == "not_achieved"
    assert float(result.forecast_df.iloc[-1]["Checking"]) == 800
    assert result.confirmed_df["Memo"].eq("rigid optional").any()
    assert result.confirmed_df["Memo"].eq("deferred optional").any()
    warning.assert_called_once()
    assert "never established" in warning.call_args.args[0]


@pytest.mark.integration
def test_policy_runs_in_approximate_mode():
    conditions = _conditions(
        500,
        [
            (date(2026, 7, 2), 1000, "income", True, 1, False, False),
            (date(2026, 7, 3), 400, "optional", False, 3, False, False),
        ],
    )

    result = ForecastHandler.runForecastApproximate(conditions)

    assert result.approximate_flag is True
    # Approximate reserve discovery activates at the emitted event/bin boundary,
    # not at the exact underlying transaction date.
    assert result.policy_results["minimum_checking_balance"]["activation_date"] == date(2026, 7, 5)
    assert float(result.forecast_df.iloc[-1]["Checking"]) == 1000
    assert result.skipped_df["Memo"].tolist() == ["optional"]


def test_policy_forecast_prints_log_guide_once(caplog, monkeypatch):
    conditions = _conditions(
        500,
        [(date(2026, 7, 2), 1000, "income", True, 1, False, False)],
    )
    forecast_logger = logging.getLogger("expense_forecast.ForecastHandler")
    monkeypatch.setattr(forecast_logger, "propagate", True)

    with caplog.at_level(logging.INFO, logger=forecast_logger.name):
        ForecastHandler.runForecastApproximate(conditions)

    assert sum(
        "How to read this forecast log:" in record.getMessage()
        for record in caplog.records
    ) == 1


@pytest.mark.integration
def test_already_enforced_policy_is_a_no_op():
    conditions = _conditions(
        500,
        [(date(2026, 7, 2), 600, "optional", False, 3, False, False)],
        balance=1000,
        min_balance=500,
    )

    result = ForecastHandler.runForecast(conditions)

    assert result.policy_results["minimum_checking_balance"]["status"] == "already_enforced"
    assert float(result.forecast_df.iloc[-1]["Checking"]) == 1000
    assert result.skipped_df["Memo"].eq("optional").any()


@pytest.mark.integration
def test_result_policy_metadata_round_trips():
    conditions = _conditions(
        500,
        [(date(2026, 7, 2), 1000, "income", True, 1, False, False)],
    )
    result = ForecastHandler.runForecast(conditions)

    rebuilt = ExpenseForecastResult.initialize_from_json_string(
        result.to_json_string()
    )

    policy_result = rebuilt.policy_results["minimum_checking_balance"]
    assert policy_result["status"] == "activated"
    assert policy_result["activation_date"] == date(2026, 7, 2)


def test_policy_round_trip_and_forecast_identity():
    conditions = _conditions(500, [])

    rebuilt = ExpenseForecastInitialConditions.initialize_from_dict(conditions.to_dict())

    policy = rebuilt.policy_set.get(MinimumCheckingBalancePolicy)
    assert policy.target == 500
    assert rebuilt.unique_id == conditions.unique_id
    assert conditions.unique_id != _conditions(1000, []).unique_id


@pytest.mark.integration
def test_policy_can_protect_named_savings_account():
    accounts = AccountSet()
    accounts.createCheckingAccount(
        "Checking", 1000, 0, float("inf"), primary_checking_ind=True
    )
    accounts.createCheckingAccount(
        "Emergency Fund", 500, 0, float("inf"), primary_checking_ind=False
    )
    budget = LineItemSet()
    budget.addLineItem(
        date(2026, 7, 2), date(2026, 7, 2), 3, "once", 100,
        "optional emergency withdrawal", deferrable=False,
        partial_payment_allowed=False,
    )
    rules = MemoRuleSet()
    rules.addMemoRule(
        "optional emergency withdrawal", "Emergency Fund", None, 3
    )
    conditions = ExpenseForecastInitialConditions(
        date(2026, 7, 1),
        date(2026, 7, 5),
        accounts,
        budget,
        rules,
        policy_set=ForecastPolicySet(
            MinimumCheckingBalancePolicy(500, priority=2),
            MinimumCheckingBalancePolicy(
                500, priority=3, account_name="Emergency Fund"
            )
        ),
    )

    result = ForecastHandler.runForecast(conditions)

    assert result.policy_results["minimum_checking_balance"] == {
        "status": "activated",
        "account_name": "Checking",
        "target": 500,
        "activation_date": date(2026, 7, 1),
    }
    assert result.policy_results[
        "minimum_checking_balance:Emergency Fund"
    ] == {
        "status": "activated",
        "account_name": "Emergency Fund",
        "target": 500,
        "activation_date": date(2026, 7, 1),
    }
    assert result.forecast_df.iloc[-1]["Emergency Fund"] == 500
    assert result.skipped_df["Memo"].eq("optional emergency withdrawal").any()


@pytest.mark.integration
def test_unattainable_savings_reserve_does_not_suppress_surplus_debt_policy():
    accounts = AccountSet()
    accounts.createCheckingAccount(
        "Checking", 2000, 500, float("inf"), primary_checking_ind=True
    )
    accounts.createCheckingAccount(
        "Savings", 0, 0, float("inf"), primary_checking_ind=False
    )
    accounts.createLoanAccount(
        name="Loan",
        principal_balance=1000,
        interest_balance=0,
        min_balance=0,
        max_balance=5000,
        billing_start_date=date(2026, 1, 1),
        minimum_payment=40,
        billing_cycle_payment_balance=0,
        apr=0.05,
    )
    conditions = ExpenseForecastInitialConditions(
        date(2026, 7, 1),
        date(2026, 7, 5),
        accounts,
        LineItemSet(),
        MemoRuleSet(),
        policy_set=ForecastPolicySet(
            MinimumCheckingBalancePolicy(500, priority=2),
            SurplusDebtPaymentPolicy("loan", "avalanche", priority=3),
            MinimumCheckingBalancePolicy(
                20_000, priority=5, account_name="Savings", on_unmet="warn"
            ),
        ),
    )

    result = ForecastHandler.runForecastApproximate(conditions)

    assert result.policy_results[
        "minimum_checking_balance:Savings"
    ]["status"] == "not_achieved"
    assert result.policy_results["surplus_debt_payment:loan"]["debt_paid"] > 0
    assert result.forecast_df.iloc[-1]["Loan"] < 1000
    assert any(
        decision["memo"].startswith("POLICY surplus_debt_payment:loan ")
        for decision in result.safety_decisions
    )


def test_named_policy_round_trip():
    conditions = _conditions(500, [])
    conditions.policy_set.policies[0].account_name = "Checking"

    rebuilt = ExpenseForecastInitialConditions.initialize_from_dict(
        conditions.to_dict()
    )

    assert rebuilt.policy_set.get(MinimumCheckingBalancePolicy).account_name == "Checking"


def test_policy_rejects_unknown_or_non_liquid_named_account():
    accounts = AccountSet()
    accounts.createCheckingAccount(
        "Checking", 1000, 0, float("inf"), primary_checking_ind=True
    )
    accounts.createInvestmentAccount("Brokerage", 1000, date(2026, 1, 1), 0.05)

    with pytest.raises(ValueError, match="checking-type account"):
        ExpenseForecastInitialConditions(
            date(2026, 7, 1), date(2026, 7, 5), accounts,
            LineItemSet(), MemoRuleSet(),
            policy_set=ForecastPolicySet(
                MinimumCheckingBalancePolicy(
                    500, priority=2, account_name="Brokerage"
                )
            ),
        )


@pytest.mark.parametrize("target", [-1, float("inf"), float("nan")])
def test_policy_rejects_invalid_target(target):
    with pytest.raises(ValueError, match="finite, non-negative"):
        MinimumCheckingBalancePolicy(target, priority=2)


def test_policy_set_rejects_duplicate_policy_types():
    with pytest.raises(ValueError, match="Duplicate forecast policy"):
        ForecastPolicySet(
            MinimumCheckingBalancePolicy(500, priority=2),
            MinimumCheckingBalancePolicy(1000, priority=3),
        )


def test_policy_requires_primary_checking_account():
    conditions = _conditions(500, [])
    conditions.initial_account_set.accounts[0].primary_checking_ind = False

    with pytest.raises(ValueError, match="exactly one primary checking"):
        ForecastHandler.runForecast(conditions)

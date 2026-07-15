from datetime import date
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
def test_never_achieved_returns_p1_result_and_warns():
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
    assert float(result.forecast_df.iloc[-1]["Checking"]) == 1000
    assert result.skipped_df["Memo"].eq("rigid optional").any()
    assert result.deferred_df["Memo"].eq("deferred optional").any()
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
    assert result.policy_results["minimum_checking_balance"]["activation_date"] == date(2026, 7, 2)
    assert float(result.forecast_df.iloc[-1]["Checking"]) == 600


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

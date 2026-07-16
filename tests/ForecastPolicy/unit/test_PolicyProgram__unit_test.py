from datetime import date

import pytest

from expense_forecast.AccountSet import AccountSet
from expense_forecast.DatedPolicyChange import DatedPolicyChange
from expense_forecast.ExpenseForecastInitialConditions import ExpenseForecastInitialConditions
from expense_forecast.ExpenseForecastResult import ExpenseForecastResult
from expense_forecast.ForecastHandler import ForecastHandler
from expense_forecast.ForecastPolicySet import ForecastPolicySet
from expense_forecast.LineItemSet import LineItemSet
from expense_forecast.MemoRuleSet import MemoRuleSet
from expense_forecast.PolicyProgram import PolicyProgram
from expense_forecast.SurplusSavingPolicy import SurplusSavingPolicy


def saving(target):
    return SurplusSavingPolicy("Savings", target, priority=2)


def test_dated_add_replace_remove_resolves_persistently():
    program = PolicyProgram(
        ForecastPolicySet(),
        [
            DatedPolicyChange(date(2026, 2, 1), add=[saving(500)]),
            DatedPolicyChange(date(2026, 3, 1), replace=[saving(1000)]),
            DatedPolicyChange(
                date(2026, 4, 1), remove=["surplus_saving:Savings"]
            ),
        ],
    )

    assert not program.resolve(date(2026, 1, 31))
    assert program.resolve(date(2026, 2, 1)).policies[0].saved_minimum_threshold == 500
    assert program.resolve(date(2026, 3, 15)).policies[0].saved_minimum_threshold == 1000
    assert not program.resolve(date(2026, 4, 1))


def test_invalid_dated_operation_is_rejected_at_construction():
    with pytest.raises(ValueError, match="inactive"):
        PolicyProgram(
            ForecastPolicySet(),
            [DatedPolicyChange(date(2026, 1, 1), replace=[saving(500)])],
        )


def test_bounded_change_restores_prior_policy():
    program = PolicyProgram(
        ForecastPolicySet(saving(500)),
        [DatedPolicyChange.bounded(
            date(2026, 2, 1), date(2026, 3, 1), replace=[saving(1000)]
        )],
    )

    assert program.resolve(date(2026, 2, 15)).policies[0].saved_minimum_threshold == 1000
    assert program.resolve(date(2026, 3, 1)).policies[0].saved_minimum_threshold == 500


def test_dated_program_executes_phases_and_round_trips():
    accounts = AccountSet()
    accounts.createCheckingAccount("Checking", 2000, 0, float("inf"), True)
    accounts.createCheckingAccount("Savings", 0, 0, float("inf"), False)
    program = PolicyProgram(
        ForecastPolicySet(saving(500)),
        [DatedPolicyChange(date(2026, 1, 3), replace=[saving(1000)])],
    )
    conditions = ExpenseForecastInitialConditions(
        date(2026, 1, 1), date(2026, 1, 4), accounts,
        LineItemSet(), MemoRuleSet(), policy_program=program,
    )

    result = ForecastHandler.runForecastApproximate(conditions)

    assert result.forecast_df.iloc[-1]["Savings"] == 1000
    assert len(result.policy_regimes) == 2
    rebuilt = ExpenseForecastResult.initialize_from_json_string(
        result.to_json_string()
    )
    assert rebuilt.initial_conditions.policy_program.resolve(
        date(2026, 1, 3)
    ).policies[0].saved_minimum_threshold == 1000
    assert len(rebuilt.policy_regimes) == 2

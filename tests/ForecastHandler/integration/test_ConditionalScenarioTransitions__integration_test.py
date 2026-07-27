from datetime import date

import pytest

from expense_forecast.AccountSet import AccountSet
from expense_forecast.ConditionalScenarioTransition import ConditionalScenarioTransition
from expense_forecast.ConditionalScenarioTransitionSet import ConditionalScenarioTransitionSet
from expense_forecast.ExpenseForecastInitialConditions import ExpenseForecastInitialConditions
from expense_forecast.ForecastHandler import ForecastHandler
from expense_forecast.LineItemSet import LineItemSet
from expense_forecast.MemoMilestone import MemoMilestone
from expense_forecast.MemoRuleSet import MemoRuleSet
from expense_forecast.MilestoneSet import MilestoneSet
from expense_forecast.ForecastPolicySet import ForecastPolicySet
from expense_forecast.MinimumCheckingBalancePolicy import MinimumCheckingBalancePolicy
from expense_forecast.ScenarioDimension import ScenarioDimension
from expense_forecast.ScenarioChoice import ScenarioChoice
from expense_forecast.ScenarioSpace import ScenarioSpace
from expense_forecast.AccountMilestone import AccountMilestone


def _line_item_set(day, amount, memo, income=False):
    result = LineItemSet()
    result.addLineItem(
        start_date=day,
        end_date=day,
        priority=1,
        interval="once",
        amount=amount,
        memo=memo,
        income_flag=income,
        deferrable=False,
        partial_payment_allowed=False,
    )
    return result


def _initial_conditions(approximate=False, reserve_target=None):
    start = date(2026, 7, 1)
    trigger_day = date(2026, 7, 15) if approximate else date(2026, 7, 2)
    expense_day = date(2026, 8, 15) if approximate else date(2026, 7, 4)
    end = date(2026, 9, 1) if approximate else date(2026, 7, 6)

    accounts = AccountSet()
    accounts.createCheckingAccount(
        "Checking", 100, 0, float("inf"), primary_checking_ind=True
    )
    trigger = _line_item_set(trigger_day, 100, "RN Year 1 Income", income=True)
    food = ScenarioDimension(
        "Food",
        {
            "Very Low": _line_item_set(expense_day, 10, "Very Low Food"),
            "Average": _line_item_set(expense_day, 20, "Average Food"),
        },
    )
    budget = trigger + food.select("Very Low")
    rules = MemoRuleSet()
    rules.addMemoRule("RN Year 1 Income", None, "Checking", 1)
    rules.addMemoRule(".* Food", "Checking", None, 1)
    milestones = MilestoneSet(
        {"Get job as RN": MemoMilestone(memo_regex="RN Year 1 Income")}
    )
    transitions = ConditionalScenarioTransitionSet(
        ConditionalScenarioTransition(
            "Start average food budget",
            "Get job as RN",
            {"Food": "Average"},
        )
    )
    kwargs = {}
    if reserve_target is not None:
        kwargs["policy_set"] = ForecastPolicySet(
            MinimumCheckingBalancePolicy(reserve_target, priority=2)
        )
    return ExpenseForecastInitialConditions(
        start,
        end,
        accounts,
        budget,
        rules,
        milestone_set=milestones,
        transition_set=transitions,
        **kwargs,
    )


@pytest.mark.integration
def test_exact_transition_applies_new_choice_after_milestone():
    result = ForecastHandler.runForecast(_initial_conditions())

    assert float(result.forecast_df.iloc[-1]["Checking"]) == 180.0
    assert "Average Food" in "; ".join(result.confirmed_df["Memo"])
    assert "Very Low Food" not in "; ".join(result.confirmed_df["Memo"])


@pytest.mark.integration
def test_approximate_transition_applies_new_choice_to_following_bin():
    result = ForecastHandler.runForecastApproximate(_initial_conditions(True))

    assert float(result.forecast_df.iloc[-1]["Checking"]) == 180.0
    assert all(day.day == 1 for day in result.forecast_df["Date"])
    assert "Average Food" in "; ".join(result.confirmed_df["Memo"])


@pytest.mark.integration
def test_graph_v2_approximate_transition_normalizes_timestamp_strings():
    result = ForecastHandler.runForecastApproximate(
        _initial_conditions(True),
        engine="graph v2",
    )

    assert float(result.forecast_df.iloc[-1]["Checking"]) == 180.0
    assert "Average Food" in "; ".join(result.confirmed_df["Memo"])
    assert result.transition_results["Start average food budget"][
        "status"
    ] == "triggered"


@pytest.mark.integration
def test_graph_v2_approximate_ignores_unachieved_transition_milestone():
    initial_conditions = _initial_conditions(True)
    initial_conditions.milestone_set = MilestoneSet({
        "Get job as RN": AccountMilestone(
            "Get job as RN",
            "Checking",
            10_000,
            float("inf"),
        )
    })

    result = ForecastHandler.runForecastApproximate(
        initial_conditions,
        engine="graph v2",
    )

    assert result.transition_results["Start average food budget"][
        "status"
    ] == "untriggered"
    assert "Very Low Food" in "; ".join(result.confirmed_df["Memo"])
    assert "Average Food" not in "; ".join(result.confirmed_df["Memo"])


@pytest.mark.integration
def test_transition_initial_conditions_round_trip_preserves_scenario_metadata():
    original = _initial_conditions()

    rebuilt = ExpenseForecastInitialConditions.initialize_from_dict(
        original.to_dict()
    )

    assert rebuilt.initial_line_item_set.scenario_selections == {"Food": "Very Low"}
    assert rebuilt.transition_set.transitions[0].milestone == "Get job as RN"
    assert float(ForecastHandler.runForecast(rebuilt).forecast_df.iloc[-1]["Checking"]) == 180.0


@pytest.mark.integration
def test_minimum_checking_policy_composes_with_scenario_transition():
    result = ForecastHandler.runForecast(
        _initial_conditions(reserve_target=150)
    )

    assert result.policy_results["minimum_checking_balance"]["status"] == "activated"
    assert "Average Food" in "; ".join(result.confirmed_df["Memo"])
    assert float(result.forecast_df.iloc[-1]["Checking"]) >= 150


@pytest.mark.integration
def test_transition_choice_adds_account_and_memo_routing_on_following_day():
    start = date(2026, 7, 1)
    end = date(2026, 7, 5)
    accounts = AccountSet()
    accounts.createCheckingAccount(
        "Checking", 100, 0, float("inf"), primary_checking_ind=True
    )
    added_accounts = AccountSet()
    added_accounts.createCheckingAccount(
        "Savings", 50, 0, float("inf"), primary_checking_ind=False
    )
    transfer = LineItemSet()
    transfer.addLineItem(
        start_date=start,
        end_date=end,
        priority=1,
        interval="daily",
        amount=10,
        memo="emergency fund transfer",
        income_flag=False,
    )
    added_rules = MemoRuleSet()
    added_rules.addMemoRule(
        "emergency fund transfer", "Checking", "Savings", 1
    )
    trigger = _line_item_set(
        date(2026, 7, 2), 1, "transition trigger", income=True
    )
    rules = MemoRuleSet()
    rules.addMemoRule("transition trigger", None, "Checking", 1)
    milestones = MilestoneSet({
        "Trigger": MemoMilestone(memo_regex="transition trigger"),
        "Savings exists": AccountMilestone(
            "Savings exists", "Savings", 50, float("inf")
        ),
    })
    living = ScenarioDimension(
        "Living",
        {
            "Before": ScenarioChoice(
                transition_set=ConditionalScenarioTransitionSet(
                    ConditionalScenarioTransition(
                        "Add savings", "Trigger", {"Living": "After"}
                    )
                )
            ),
            "After": ScenarioChoice(
                line_item_set=transfer,
                account_set=added_accounts,
                memo_rule_set=added_rules,
            ),
        },
    )
    scenario = ScenarioSpace(
        trigger, {"Living": living}, rules
    ).from_choice_keys({"Living": "Before"})
    initial_conditions = scenario.to_initial_conditions(
        start, end, accounts, rules, milestone_set=milestones
    )

    result = ForecastHandler.runForecast(
        initial_conditions, engine="graph v2"
    )

    trigger_row = result.forecast_df.loc[
        result.forecast_df["Date"].eq(date(2026, 7, 2))
    ].iloc[0]
    assert trigger_row["Savings"] == 0
    assert result.forecast_df.iloc[-1]["Savings"] == 80
    assert "Savings" in {
        account.name for account in result.resolved_account_set.accounts
    }
    assert result.milestone_results[0]["Savings exists"] == date(2026, 7, 3)


def test_unknown_account_milestone_fails_initial_condition_validation():
    start = date(2026, 7, 1)
    accounts = AccountSet()
    accounts.createCheckingAccount(
        "Checking", 100, 0, float("inf"), primary_checking_ind=True
    )
    milestones = MilestoneSet({
        "Unknown target": AccountMilestone(
            "Unknown target", "Never Added", 0, float("inf")
        )
    })

    with pytest.raises(
        ValueError,
        match="Unknown target.*Never Added",
    ):
        ExpenseForecastInitialConditions(
            start,
            date(2026, 7, 3),
            accounts,
            LineItemSet(),
            MemoRuleSet(),
            milestone_set=milestones,
        )

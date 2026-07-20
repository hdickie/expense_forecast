"""Behavioral parity backlog for the memoized dependency graph engine.

These tests intentionally use ordinary assertions.  A red test is an
unimplemented or divergent graph-v2 behavior, not an expected failure.
"""

from datetime import date

import pandas as pd
import pytest

from expense_forecast.AccountSet import AccountSet
from expense_forecast.ConditionalScenarioTransition import (
    ConditionalScenarioTransition,
)
from expense_forecast.ConditionalScenarioTransitionSet import (
    ConditionalScenarioTransitionSet,
)
from expense_forecast.CurrentStatementBalancePaymentPolicy import (
    CurrentStatementBalancePaymentPolicy,
)
from expense_forecast.ExpenseForecastInitialConditions import (
    ExpenseForecastInitialConditions,
)
from expense_forecast.FixedMonthlyInvestmentPolicy import (
    FixedMonthlyInvestmentPolicy,
)
from expense_forecast.ForecastHandler import ForecastHandler
from expense_forecast.ForecastPolicySet import ForecastPolicySet
from expense_forecast.IncomePercentageInvestmentPolicy import (
    IncomePercentageInvestmentPolicy,
)
from expense_forecast.LineItemSet import LineItemSet
from expense_forecast.MemoMilestone import MemoMilestone
from expense_forecast.MemoRuleSet import MemoRuleSet
from expense_forecast.MilestoneSet import MilestoneSet
from expense_forecast.MinimumCheckingBalancePolicy import (
    MinimumCheckingBalancePolicy,
)
from expense_forecast.MemoizedDynamicDependencyGraphEngine import (
    ExecutionEngine,
    GraphV2ShadowMismatchError,
    compare_v2_result,
)
from expense_forecast.PeriodicInvestmentContributionCapPolicy import (
    PeriodicInvestmentContributionCapPolicy,
)
from expense_forecast.PolicyProgram import DatedPolicyChange, PolicyProgram
from expense_forecast.ScenarioDimension import ScenarioDimension
from expense_forecast.SurplusDebtPaymentPolicy import (
    SurplusDebtPaymentPolicy,
)
from expense_forecast.SurplusInvestmentPolicy import SurplusInvestmentPolicy
from expense_forecast.SurplusSavingPolicy import SurplusSavingPolicy


START = date(2026, 1, 1)


def _accounts(*, checking=1_000, savings=False):
    result = AccountSet()
    result.createCheckingAccount(
        "Checking", checking, 0, float("inf"), True
    )
    if savings:
        result.createCheckingAccount(
            "Savings", 100, 0, float("inf"), False
        )
    return result


def _conditions(
    name,
    accounts,
    line_items=None,
    rules=None,
    *,
    start=START,
    end=date(2026, 1, 10),
    **kwargs,
):
    return ExpenseForecastInitialConditions(
        start,
        end,
        accounts,
        line_items or LineItemSet(),
        rules or MemoRuleSet(),
        forecast_name=name,
        **kwargs,
    )


def _item(
    line_items,
    memo,
    amount,
    *,
    start=date(2026, 1, 2),
    end=None,
    priority=1,
    interval="once",
    income=False,
    deferrable=False,
    partial=False,
    recurrence_key=None,
):
    line_items.addLineItem(
        start,
        end or start,
        priority,
        interval,
        amount,
        memo,
        income_flag=income,
        deferrable=deferrable,
        partial_payment_allowed=partial,
        recurrence_key=recurrence_key,
    )


def _cash_case(name, transactions, *, savings=False, end=date(2026, 1, 10)):
    accounts = _accounts(savings=savings)
    line_items = LineItemSet()
    rules = MemoRuleSet()
    for transaction in transactions:
        transaction = dict(transaction)
        account_from = transaction.pop("account_from", "Checking")
        account_to = transaction.pop("account_to", None)
        memo = transaction["memo"]
        priority = transaction.get("priority", 1)
        _item(line_items, **transaction)
        rules.addMemoRule(memo, account_from, account_to, priority)
    return _conditions(name, accounts, line_items, rules, end=end)


def _assert_shadow_parity(conditions):
    # Shadow v2 owns the comparison; reaching a result means every observable
    # section currently required by the parity contract matched legacy.
    result = ForecastHandler.runForecast(conditions, engine="shadow v2")
    assert result.forecast_df["Date"].tolist()
    return result


@pytest.mark.parametrize(
    "conditions",
    [
        pytest.param(
            _cash_case("empty", []),
            id="empty-forecast",
        ),
        pytest.param(
            _cash_case(
                "first-day-income",
                [{
                    "memo": "income",
                    "amount": 100,
                    "start": START,
                    "income": True,
                    "account_from": None,
                    "account_to": "Checking",
                }],
            ),
            id="transaction-on-first-day",
        ),
        pytest.param(
            _cash_case(
                "last-day-spend",
                [{
                    "memo": "spend",
                    "amount": 100,
                    "start": date(2026, 1, 10),
                }],
            ),
            id="transaction-on-last-day",
        ),
        pytest.param(
            _cash_case(
                "income-and-spend",
                [
                    {
                        "memo": "income",
                        "amount": 500,
                        "income": True,
                        "account_from": None,
                        "account_to": "Checking",
                    },
                    {
                        "memo": "spend",
                        "amount": 125,
                        "start": date(2026, 1, 3),
                    },
                ],
            ),
            id="income-and-spending",
        ),
        pytest.param(
            _cash_case(
                "checking-transfer",
                [{
                    "memo": "save",
                    "amount": 200,
                    "account_to": "Savings",
                }],
                savings=True,
            ),
            id="checking-to-checking-transfer",
        ),
        pytest.param(
            _cash_case(
                "multiple-same-day",
                [
                    {"memo": "coffee", "amount": 5},
                    {"memo": "snack", "amount": 5},
                ],
            ),
            id="multiple-same-day-occurrences",
        ),
        *[
            pytest.param(
                _cash_case(
                    f"{interval}-recurrence",
                    [{
                        "memo": f"{interval} expense",
                        "amount": 10,
                        "interval": interval,
                        "end": end,
                    }],
                    end=end,
                ),
                id=f"{interval}-recurrence",
            )
            for interval, end in (
                ("daily", date(2026, 1, 5)),
                ("weekly", date(2026, 1, 20)),
                ("semiweekly", date(2026, 2, 5)),
                ("monthly", date(2026, 3, 5)),
            )
        ],
    ],
)
def test_shadow_v2_cash_schedule_and_routing_parity(conditions):
    _assert_shadow_parity(conditions)


def _resolution_case(kind):
    accounts = _accounts(
        checking=500, savings=kind == "hard-maximum"
    )
    line_items = LineItemSet()
    rules = MemoRuleSet()
    if kind == "priority-order":
        _item(line_items, "mandatory", 100, priority=1)
        _item(line_items, "optional", 450, priority=2)
        rules.addMemoRule("mandatory", "Checking", None, 1)
        rules.addMemoRule("optional", "Checking", None, 2)
    elif kind == "optional-accepted":
        _item(line_items, "optional", 100, priority=2)
        rules.addMemoRule("optional", "Checking", None, 2)
    elif kind == "optional-rejected":
        _item(line_items, "optional", 600, priority=2)
        rules.addMemoRule("optional", "Checking", None, 2)
    elif kind == "partial":
        _item(line_items, "partial", 600, priority=2, partial=True)
        rules.addMemoRule("partial", "Checking", None, 2)
    elif kind == "deferred":
        _item(
            line_items, "deferred", 600, priority=2, deferrable=True
        )
        _item(
            line_items,
            "later income",
            500,
            start=date(2026, 1, 4),
            income=True,
        )
        rules.addMemoRule("deferred", "Checking", None, 2)
        rules.addMemoRule("later income", None, "Checking", 1)
    elif kind == "hard-minimum":
        accounts.accounts[0].min_balance = 400
        _item(line_items, "bounded", 200, priority=2)
        rules.addMemoRule("bounded", "Checking", None, 2)
    elif kind == "hard-maximum":
        accounts.accounts[1].max_balance = 150
        _item(line_items, "bounded transfer", 100, priority=2)
        rules.addMemoRule(
            "bounded transfer", "Checking", "Savings", 2
        )
    return _conditions(kind, accounts, line_items, rules)


@pytest.mark.parametrize(
    "kind",
    [
        "priority-order",
        "optional-accepted",
        "optional-rejected",
        "partial",
        "deferred",
        "hard-minimum",
        "hard-maximum",
    ],
)
def test_shadow_v2_transaction_resolution_parity(kind):
    _assert_shadow_parity(_resolution_case(kind))


def test_graph_v2_deferral_beyond_forecast_remains_deferred():
    accounts = _accounts(checking=500)
    line_items = LineItemSet()
    rules = MemoRuleSet()
    _item(line_items, "deferred", 600, priority=2, deferrable=True)
    rules.addMemoRule("deferred", "Checking", None, 2)
    conditions = _conditions(
        "deferred-beyond-forecast",
        accounts,
        line_items,
        rules,
    )

    result = ExecutionEngine.runForecast(conditions, MilestoneSet())

    assert result.confirmed_df.empty
    assert result.skipped_df.empty
    assert result.deferred_df[["Date", "Memo", "Amount"]].to_dict(
        orient="records"
    ) == [
        {
            "Date": date(2026, 1, 11),
            "Memo": "deferred",
            "Amount": 600,
        }
    ]


def test_graph_v2_deferral_ignores_temporary_income_headroom():
    accounts = _accounts(checking=500)
    line_items = LineItemSet()
    rules = MemoRuleSet()
    _item(line_items, "deferred", 600, priority=2, deferrable=True)
    _item(
        line_items,
        "temporary income",
        500,
        start=date(2026, 1, 4),
        income=True,
    )
    _item(
        line_items,
        "mandatory spend",
        1_000,
        start=date(2026, 1, 5),
    )
    rules.addMemoRule("deferred", "Checking", None, 2)
    rules.addMemoRule("temporary income", None, "Checking", 1)
    rules.addMemoRule("mandatory spend", "Checking", None, 1)
    conditions = _conditions(
        "deferred-temporary-headroom",
        accounts,
        line_items,
        rules,
    )

    result = ExecutionEngine.runForecast(conditions, MilestoneSet())

    assert result.forecast_df.iloc[-1]["Checking"] == 0
    assert result.deferred_df[["Date", "Memo", "Amount"]].to_dict(
        orient="records"
    ) == [
        {
            "Date": date(2026, 1, 11),
            "Memo": "deferred",
            "Amount": 600,
        }
    ]


def test_graph_v2_credit_partial_purchase_uses_largest_passing_cent():
    accounts = _accounts(checking=500)
    accounts.createCreditCardAccount(
        "Card",
        current_statement_balance=200,
        previous_statement_balance=500,
        min_balance=0,
        max_balance=750,
        billing_start_date=date(2026, 1, 1),
        apr=0.24,
        minimum_payment=40,
        end_of_previous_cycle_balance=500,
    )
    line_items = LineItemSet()
    rules = MemoRuleSet()
    _item(
        line_items,
        "partial card purchase",
        100,
        priority=2,
        partial=True,
    )
    rules.addMemoRule("partial card purchase", "Card", None, 2)
    conditions = _conditions(
        "partial-credit-purchase",
        accounts,
        line_items,
        rules,
    )

    result = ExecutionEngine.runForecast(conditions, MilestoneSet())

    assert result.confirmed_df[["Memo", "Amount"]].to_dict(
        orient="records"
    ) == [
        {
            "Memo": "partial card purchase",
            "Amount": 50,
        }
    ]


def _debt_case(kind):
    accounts = _accounts(checking=3_000)
    line_items = LineItemSet()
    rules = MemoRuleSet()
    start = date(2026, 1, 30)
    end = date(2026, 2, 5)
    if kind.startswith("credit"):
        accounts.createCreditCardAccount(
            "Card",
            current_statement_balance=200,
            previous_statement_balance=500,
            min_balance=0,
            max_balance=10_000,
            billing_start_date=date(2026, 1, 1),
            apr=0.24,
            minimum_payment=40,
            end_of_previous_cycle_balance=500,
        )
        if kind == "credit-purchase":
            _item(
                line_items,
                "card purchase",
                100,
                start=date(2026, 1, 31),
            )
            rules.addMemoRule("card purchase", "Card", None, 1)
        elif kind in {"credit-payment", "credit-rollover-with-payment"}:
            payment_date = (
                date(2026, 2, 1)
                if kind == "credit-rollover-with-payment"
                else date(2026, 1, 31)
            )
            _item(
                line_items,
                "card payment",
                300,
                start=payment_date,
            )
            rules.addMemoRule("card payment", "Checking", "Card", 1)
    else:
        accounts.createLoanAccount(
            "Loan",
            principal_balance=1_000,
            interest_balance=25,
            min_balance=0,
            max_balance=25_000,
            billing_start_date=date(2026, 1, 1),
            apr=0.12,
            minimum_payment=100,
        )
        if kind in {"loan-payment", "loan-payoff"}:
            amount = (
                200
                if kind == "loan-payment"
                else 1025.3285420944558
            )
            _item(
                line_items,
                kind,
                amount,
                start=date(2026, 1, 31),
            )
            rules.addMemoRule(kind, "Checking", "Loan", 1)
    return _conditions(
        kind,
        accounts,
        line_items,
        rules,
        start=start,
        end=end,
    )


@pytest.mark.parametrize(
    "kind",
    [
        "credit-purchase",
        "credit-payment",
        "credit-rollover-interest-and-minimum",
        "credit-rollover-with-payment",
        "loan-interest-and-minimum",
        "loan-payment",
        "loan-payoff",
    ],
)
def test_shadow_v2_debt_parity(kind):
    result = _assert_shadow_parity(_debt_case(kind))
    final_row = result.forecast_df.iloc[-1]
    expected_final_balances = {
        "credit-purchase": {"Checking": 2_960, "Card": 770},
        "credit-payment": {"Checking": 2_700, "Card": 404},
        "credit-rollover-interest-and-minimum": {
            "Checking": 2_960,
            "Card": 670,
        },
        "credit-rollover-with-payment": {
            "Checking": 2_660,
            "Card": 370,
        },
        "loan-interest-and-minimum": {
            "Checking": 2_900,
            "Loan": 926.87,
        },
        "loan-payment": {"Checking": 2_800, "Loan": 826.68},
        "loan-payoff": {"Checking": 1_974.67, "Loan": 0},
    }
    for account_name, expected_balance in expected_final_balances[kind].items():
        assert final_row[account_name] == expected_balance

    if kind == "credit-rollover-with-payment":
        rollover_directives = result.forecast_df.loc[
            result.forecast_df["Date"] == date(2026, 2, 1),
            "Memo Directives",
        ].iat[0]
        assert rollover_directives.index("CC MIN PAYMENT") < (
            rollover_directives.index("ADDTL CC PAYMENT")
        )
    if kind == "loan-payoff":
        assert not result.forecast_df.loc[
            result.forecast_df["Date"] > date(2026, 1, 31),
            "Memo Directives",
        ].str.contains("LOAN INTEREST").any()


def _investment_case(kind):
    accounts = _accounts(checking=3_000)
    accounts.createInvestmentAccount(
        "Brokerage", 1_000, date(2026, 1, 1), 0.10
    )
    line_items = LineItemSet()
    rules = MemoRuleSet()
    if kind == "contribution":
        _item(line_items, "invest", 200)
        rules.addMemoRule("invest", "Checking", "Brokerage", 1)
    elif kind == "withdrawal":
        _item(line_items, "withdraw", 200)
        rules.addMemoRule("withdraw", "Brokerage", "Checking", 1)
    elif kind == "multiple-accounts":
        accounts.createInvestmentAccount(
            "IRA", 500, date(2026, 1, 1), 0.05
        )
        _item(line_items, "ira contribution", 100)
        rules.addMemoRule(
            "ira contribution", "Checking", "IRA", 1
        )
    return _conditions(
        kind,
        accounts,
        line_items,
        rules,
        end=date(2026, 1, 15),
    )


@pytest.mark.parametrize(
    "kind",
    ["contribution", "withdrawal", "returns", "multiple-accounts"],
)
def test_shadow_v2_investment_parity(kind):
    _assert_shadow_parity(_investment_case(kind))


def _policy_case(kind):
    accounts = _accounts(checking=5_000, savings=kind == "surplus-saving")
    line_items = LineItemSet()
    rules = MemoRuleSet()
    policies = []
    if kind == "minimum-checking":
        policies = [MinimumCheckingBalancePolicy(2_000, priority=2)]
        _item(line_items, "optional", 4_000, priority=3)
        rules.addMemoRule("optional", "Checking", None, 3)
    elif kind == "minimum-checking-unmet-warn":
        policies = [
            MinimumCheckingBalancePolicy(
                6_000, priority=2, on_unmet="warn"
            )
        ]
    elif kind == "surplus-saving":
        policies = [SurplusSavingPolicy("Savings", 1_000, priority=2)]
    elif kind in {
        "fixed-investment",
        "income-percentage",
        "surplus-investment",
        "contribution-cap",
    }:
        accounts.createInvestmentAccount(
            "Brokerage", 0, date(2026, 1, 1), 0
        )
        if kind == "fixed-investment":
            policies = [
                FixedMonthlyInvestmentPolicy(
                    "Brokerage", 500, priority=2, day=2
                )
            ]
        elif kind == "income-percentage":
            _item(
                line_items,
                "paycheck",
                1_000,
                income=True,
            )
            rules.addMemoRule("paycheck", None, "Checking", 1)
            policies = [
                IncomePercentageInvestmentPolicy(
                    "Brokerage", 0.10, priority=2
                )
            ]
        elif kind == "surplus-investment":
            policies = [
                SurplusInvestmentPolicy(
                    "Brokerage", checking_threshold=1_000, priority=2
                )
            ]
        else:
            policies = [
                FixedMonthlyInvestmentPolicy(
                    "Brokerage", 700, priority=2, day=2
                ),
                PeriodicInvestmentContributionCapPolicy(
                    "Brokerage", 500, "month", priority=3
                ),
            ]
    elif kind in {"surplus-credit", "current-statement"}:
        accounts.createCreditCardAccount(
            "Card", 200, 500, 0, 10_000,
            date(2026, 1, 1), 0.20, 40, 500,
        )
        policies = [
            SurplusDebtPaymentPolicy("credit", "avalanche", priority=2)
            if kind == "surplus-credit"
            else CurrentStatementBalancePaymentPolicy("Card", priority=2)
        ]
    elif kind == "surplus-loan":
        accounts.createLoanAccount(
            "Loan", 1_000, 0, 0, 25_000,
            date(2026, 1, 1), 0.10, 100,
        )
        policies = [
            SurplusDebtPaymentPolicy("loan", "snowball", priority=2)
        ]
    return _conditions(
        kind,
        accounts,
        line_items,
        rules,
        end=date(2026, 1, 5),
        policy_set=ForecastPolicySet(*policies),
    )


@pytest.mark.parametrize(
    "kind",
    [
        "minimum-checking",
        "minimum-checking-unmet-warn",
        "surplus-saving",
        "fixed-investment",
        "income-percentage",
        "surplus-investment",
        "contribution-cap",
        "surplus-credit",
        "surplus-loan",
        "current-statement",
    ],
)
def test_shadow_v2_policy_parity(kind):
    _assert_shadow_parity(_policy_case(kind))


def _policy_program_case(operation):
    accounts = _accounts(checking=3_000)
    accounts.createInvestmentAccount(
        "Brokerage", 0, date(2026, 1, 1), 0
    )
    original = FixedMonthlyInvestmentPolicy(
        "Brokerage", 100, priority=2, day=2
    )
    replacement = FixedMonthlyInvestmentPolicy(
        "Brokerage", 200, priority=2, day=2
    )
    if operation == "add":
        program = PolicyProgram(
            ForecastPolicySet(),
            [DatedPolicyChange(date(2026, 2, 1), add=[original])],
        )
    elif operation == "replace":
        program = PolicyProgram(
            ForecastPolicySet(original),
            [DatedPolicyChange(date(2026, 2, 1), replace=[replacement])],
        )
    elif operation == "remove":
        program = PolicyProgram(
            ForecastPolicySet(original),
            [
                DatedPolicyChange(
                    date(2026, 2, 1), remove=[original.policy_key]
                )
            ],
        )
    else:
        program = PolicyProgram(
            ForecastPolicySet(),
            [
                DatedPolicyChange.bounded(
                    date(2026, 2, 1),
                    date(2026, 3, 1),
                    add=[original],
                )
            ],
        )
    return _conditions(
        f"dated-policy-{operation}",
        accounts,
        start=date(2026, 1, 25),
        end=date(2026, 3, 3),
        policy_program=program,
    )


@pytest.mark.parametrize("operation", ["add", "replace", "remove", "bounded"])
def test_shadow_v2_dated_policy_program_parity(operation):
    _assert_shadow_parity(_policy_program_case(operation))


def _scenario_transition_case():
    accounts = _accounts(checking=500)
    trigger = LineItemSet()
    _item(trigger, "new job", 100, income=True)
    low = LineItemSet()
    _item(low, "low food", 10, start=date(2026, 1, 4))
    standard = LineItemSet()
    _item(standard, "standard food", 20, start=date(2026, 1, 4))
    food = ScenarioDimension(
        "Food", {"Low": low, "Standard": standard}
    )
    line_items = trigger + food.select("Low")
    rules = MemoRuleSet()
    rules.addMemoRule("new job", None, "Checking", 1)
    rules.addMemoRule(".* food", "Checking", None, 1)
    milestones = MilestoneSet(
        {"Employed": MemoMilestone(memo_regex="new job")}
    )
    transitions = ConditionalScenarioTransitionSet(
        ConditionalScenarioTransition(
            "Employed", {"Food": "Standard"}
        )
    )
    return _conditions(
        "milestone-transition",
        accounts,
        line_items,
        rules,
        milestone_set=milestones,
        transitions=transitions,
    )


def test_shadow_v2_milestone_and_scenario_transition_parity():
    _assert_shadow_parity(_scenario_transition_case())


def test_shadow_v2_dated_scenario_recurrence_continuity_parity():
    accounts = _accounts(checking=500)
    first = LineItemSet()
    _item(
        first,
        "paycheck",
        100,
        start=date(2020, 1, 1),
        end=date(2020, 12, 31),
        interval="semiweekly",
        income=True,
    )
    second = LineItemSet()
    _item(
        second,
        "paycheck",
        125,
        start=date(2020, 1, 1),
        end=date(2020, 12, 31),
        interval="semiweekly",
        income=True,
    )
    income = ScenarioDimension(
        "Income", {"Year 1": first, "Year 2": second}
    )
    line_items = income.choice_for_date_range(
        "Year 1", date(2026, 1, 1), date(2026, 1, 20)
    ) + income.choice_for_date_range(
        "Year 2", date(2026, 1, 20), date(2026, 2, 10)
    )
    rules = MemoRuleSet()
    rules.addMemoRule("paycheck", None, "Checking", 1)
    conditions = _conditions(
        "dated-scenario-recurrence",
        accounts,
        line_items,
        rules,
        end=date(2026, 2, 10),
    )

    _assert_shadow_parity(conditions)


def test_v2_comparator_reports_all_controlled_differences():
    accounts = _accounts(checking=500)
    conditions = _conditions("comparator-control", accounts)
    legacy = ForecastHandler.runForecast(conditions, engine="legacy")
    graph = legacy.forecast_df.copy()
    graph.loc[1, "Checking"] = 400
    graph.loc[2, "Checking"] = 300

    with pytest.raises(GraphV2ShadowMismatchError) as error:
        compare_v2_result(graph, legacy, scenario="comparator-control")

    cell_differences = [
        difference
        for difference in error.value.differences
        if difference.variable == "Checking"
    ]
    assert [difference.event for difference in cell_differences] == [
        legacy.forecast_df.loc[1, "Date"],
        legacy.forecast_df.loc[2, "Date"],
    ]
    assert all(
        difference.graph_value != difference.legacy_value
        for difference in cell_differences
    )


def test_shadow_v2_remains_exact_only():
    conditions = _conditions("exact-only", _accounts())
    with pytest.raises(ValueError, match="engine must be"):
        ForecastHandler.runForecastApproximate(
            conditions, engine="shadow v2"
        )

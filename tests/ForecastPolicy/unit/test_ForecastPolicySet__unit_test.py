import pytest

from expense_forecast.FixedMonthlyInvestmentPolicy import FixedMonthlyInvestmentPolicy
from expense_forecast.ForecastPolicySet import ForecastPolicySet
from expense_forecast.IncomePercentageInvestmentPolicy import IncomePercentageInvestmentPolicy
from expense_forecast.MinimumCheckingBalancePolicy import MinimumCheckingBalancePolicy
from expense_forecast.PeriodicInvestmentContributionCapPolicy import PeriodicInvestmentContributionCapPolicy
from expense_forecast.SurplusDebtPaymentPolicy import SurplusDebtPaymentPolicy
from expense_forecast.SurplusInvestmentPolicy import SurplusInvestmentPolicy
from expense_forecast.CurrentStatementBalancePaymentPolicy import (
    CurrentStatementBalancePaymentPolicy,
)


def test_policy_set_preserves_priority_order_and_distinct_targets():
    policies = ForecastPolicySet(
        FixedMonthlyInvestmentPolicy("Brokerage", 100, priority=5),
        FixedMonthlyInvestmentPolicy("IRA", 100, priority=6),
    )

    assert [policy.priority for policy in policies.policies] == [5, 6]


def test_policy_set_allows_duplicate_priority_in_declaration_order():
    policies = ForecastPolicySet(
        MinimumCheckingBalancePolicy(500, priority=2),
        SurplusDebtPaymentPolicy("loan", "avalanche", priority=2),
    )

    assert [type(policy) for policy in policies.policies] == [
        MinimumCheckingBalancePolicy,
        SurplusDebtPaymentPolicy,
    ]


@pytest.mark.parametrize(
    "factory",
    [
        lambda: MinimumCheckingBalancePolicy(500, priority=0),
        lambda: SurplusDebtPaymentPolicy("mortgage", "avalanche", priority=2),
        lambda: SurplusDebtPaymentPolicy("loan", "random", priority=2),
        lambda: FixedMonthlyInvestmentPolicy("Brokerage", 100, priority=2, day=32),
        lambda: IncomePercentageInvestmentPolicy("Brokerage", 1.1, priority=2),
        lambda: SurplusInvestmentPolicy("Brokerage", -1, priority=2),
        lambda: PeriodicInvestmentContributionCapPolicy(
            "Brokerage", 100, "week", priority=2
        ),
        lambda: MinimumCheckingBalancePolicy(
            500, priority=2, on_unmet="ignore"
        ),
        lambda: CurrentStatementBalancePaymentPolicy("", priority=1),
    ],
)
def test_policy_validation(factory):
    with pytest.raises((TypeError, ValueError)):
        factory()


def test_current_statement_policy_allows_priority_one():
    policy = CurrentStatementBalancePaymentPolicy("Chase", priority=1)

    assert policy.policy_key == "current_statement_balance_payment:Chase"

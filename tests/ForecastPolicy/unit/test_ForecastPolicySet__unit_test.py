import pytest

from expense_forecast.FixedMonthlyInvestmentPolicy import FixedMonthlyInvestmentPolicy
from expense_forecast.ForecastPolicySet import ForecastPolicySet
from expense_forecast.IncomePercentageInvestmentPolicy import IncomePercentageInvestmentPolicy
from expense_forecast.MinimumCheckingBalancePolicy import MinimumCheckingBalancePolicy
from expense_forecast.PeriodicInvestmentContributionCapPolicy import PeriodicInvestmentContributionCapPolicy
from expense_forecast.SurplusDebtPaymentPolicy import SurplusDebtPaymentPolicy
from expense_forecast.SurplusInvestmentPolicy import SurplusInvestmentPolicy


def test_policy_set_preserves_priority_order_and_distinct_targets():
    policies = ForecastPolicySet(
        FixedMonthlyInvestmentPolicy("Brokerage", 100, priority=5),
        FixedMonthlyInvestmentPolicy("IRA", 100, priority=6),
    )

    assert [policy.priority for policy in policies.policies] == [5, 6]


def test_policy_set_rejects_duplicate_priority():
    with pytest.raises(ValueError, match="Duplicate forecast policy priority"):
        ForecastPolicySet(
            MinimumCheckingBalancePolicy(500, priority=2),
            SurplusDebtPaymentPolicy("loan", "avalanche", priority=2),
        )


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
    ],
)
def test_policy_validation(factory):
    with pytest.raises((TypeError, ValueError)):
        factory()


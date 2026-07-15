"""Ordered forecast policy collection."""

from expense_forecast.MinimumCheckingBalancePolicy import (
    MinimumCheckingBalancePolicy,
)
from expense_forecast.SurplusDebtPaymentPolicy import SurplusDebtPaymentPolicy
from expense_forecast.CurrentStatementBalancePaymentPolicy import (
    CurrentStatementBalancePaymentPolicy,
)
from expense_forecast.InvestmentPolicies import (
    FixedMonthlyInvestmentPolicy,
    IncomePercentageInvestmentPolicy,
    PeriodicInvestmentContributionCapPolicy,
    SurplusInvestmentPolicy,
)


class ForecastPolicySet:
    """Store one policy of each supported type in declaration order."""

    supported_types = (
        MinimumCheckingBalancePolicy,
        SurplusDebtPaymentPolicy,
        FixedMonthlyInvestmentPolicy,
        IncomePercentageInvestmentPolicy,
        SurplusInvestmentPolicy,
        PeriodicInvestmentContributionCapPolicy,
        CurrentStatementBalancePaymentPolicy,
    )

    def __init__(self, *policies):
        if len(policies) == 1 and isinstance(policies[0], (list, tuple)):
            policies = tuple(policies[0])
        self.policies = []
        observed_keys = set()
        for policy in policies:
            if not isinstance(policy, self.supported_types):
                raise TypeError(f"Unsupported forecast policy: {type(policy).__name__}")
            if policy.policy_key in observed_keys:
                raise ValueError(f"Duplicate forecast policy key: {policy.policy_key}")
            observed_keys.add(policy.policy_key)
            self.policies.append(policy)

    def __bool__(self):
        return bool(self.policies)

    def get(self, policy_type):
        return next(
            (policy for policy in self.policies if isinstance(policy, policy_type)),
            None,
        )

    def validate(self, account_set, budget_set):
        accounts_by_name = {account.name: account for account in account_set.accounts}
        reserve = self.get(MinimumCheckingBalancePolicy)
        for policy in self.policies:
            if isinstance(policy, CurrentStatementBalancePaymentPolicy):
                account = accounts_by_name.get(policy.account_name)
                if account is None or account.account_type != "credit":
                    raise ValueError(
                        f"Policy {policy.policy_key!r} requires credit-card account "
                        f"{policy.account_name!r}"
                    )
                continue
            account_name = getattr(policy, "account_name", None)
            if account_name is not None:
                account = accounts_by_name.get(account_name)
                if account is None or account.account_type != "investment":
                    raise ValueError(
                        f"Policy {policy.policy_key!r} requires investment account "
                        f"{account_name!r}"
                    )
            if isinstance(policy, SurplusInvestmentPolicy) and reserve is not None:
                if policy.checking_threshold < reserve.target:
                    raise ValueError(
                        "Surplus investment threshold must be at least the checking reserve"
                    )

"""Ordered forecast policy collection."""

from expense_forecast.MinimumCheckingBalancePolicy import (
    MinimumCheckingBalancePolicy,
)
from expense_forecast.SurplusDebtPaymentPolicy import SurplusDebtPaymentPolicy
from expense_forecast.CurrentStatementBalancePaymentPolicy import (
    CurrentStatementBalancePaymentPolicy,
)
from expense_forecast.SurplusSavingPolicy import SurplusSavingPolicy
from expense_forecast.InvestmentPolicies import (
    FixedMonthlyInvestmentPolicy,
    IncomePercentageInvestmentPolicy,
    PeriodicInvestmentContributionCapPolicy,
    SurplusInvestmentPolicy,
)


class ForecastPolicySet:
    """Store supported policies in declaration order with unique policy keys."""

    supported_types = (
        MinimumCheckingBalancePolicy,
        SurplusDebtPaymentPolicy,
        FixedMonthlyInvestmentPolicy,
        IncomePercentageInvestmentPolicy,
        SurplusInvestmentPolicy,
        PeriodicInvestmentContributionCapPolicy,
        CurrentStatementBalancePaymentPolicy,
        SurplusSavingPolicy,
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

    def get_priority_n_policies(self, priority):
        """Return policies at ``priority`` in declaration order.

        Declaration order is significant when policies share a priority, so
        this intentionally filters the existing list rather than regrouping it
        through a set or dictionary.
        """
        return [
            policy
            for policy in self.policies
            if policy.priority == priority
        ]

    def validate(self, account_set, line_item_set):
        accounts_by_name = {account.name: account for account in account_set.accounts}
        primary_checking_name = account_set.primary_checking_account_name
        reserves = [
            policy for policy in self.policies
            if isinstance(policy, MinimumCheckingBalancePolicy)
        ]
        reserve_accounts = [
            policy.account_name or primary_checking_name for policy in reserves
        ]
        if len(reserve_accounts) != len(set(reserve_accounts)):
            raise ValueError(
                "Only one MinimumCheckingBalancePolicy may target each account"
            )
        for policy in self.policies:
            if isinstance(policy, MinimumCheckingBalancePolicy):
                if policy.account_name is not None:
                    account = accounts_by_name.get(policy.account_name)
                    if account is None or account.account_type != "checking":
                        raise ValueError(
                            f"Policy {policy.policy_key!r} requires checking-type "
                            f"account {policy.account_name!r}"
                        )
                continue
            if isinstance(policy, SurplusSavingPolicy):
                account = accounts_by_name.get(policy.account_name)
                if account is None or account.account_type != "checking":
                    raise ValueError(
                        f"Policy {policy.policy_key!r} requires checking-type "
                        f"account {policy.account_name!r}"
                    )
                if policy.account_name == primary_checking_name:
                    raise ValueError(
                        "SurplusSavingPolicy destination cannot be primary checking"
                    )
                continue
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
            if (
                isinstance(policy, SurplusInvestmentPolicy)
                and any(
                    reserve.account_name in {None, primary_checking_name}
                    for reserve in reserves
                )
            ):
                checking_reserve = next(
                    reserve for reserve in reserves
                    if reserve.account_name in {None, primary_checking_name}
                )
                if policy.checking_threshold < checking_reserve.target:
                    raise ValueError(
                        "Surplus investment threshold must be at least the checking reserve"
                    )

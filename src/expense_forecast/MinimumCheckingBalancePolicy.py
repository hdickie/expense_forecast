"""Policy for establishing and preserving a primary-checking reserve."""

from expense_forecast.ForecastPolicy import ForecastPolicy


class MinimumCheckingBalancePolicy(ForecastPolicy):
    """Delay optional spending until a stable liquid-account reserve is established.

    ``account_name`` defaults to the primary checking account for backward
    compatibility. It may name another checking-type account, such as savings.
    """

    policy_name = "minimum_checking_balance"

    def __init__(self, target, priority, on_unmet="warn", account_name=None):
        super().__init__(priority, on_unmet)
        self.validate_amount(target, "target")
        if account_name is not None and (
            not isinstance(account_name, str) or not account_name.strip()
        ):
            raise ValueError("account_name must be a non-empty string or None")
        self.target = target
        self.account_name = account_name.strip() if account_name is not None else None

    @property
    def policy_key(self):
        if self.account_name is None:
            return self.policy_name
        return f"{self.policy_name}:{self.account_name}"

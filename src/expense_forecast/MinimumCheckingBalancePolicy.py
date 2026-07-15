"""Policy for establishing and preserving a primary-checking reserve."""

from expense_forecast.ForecastPolicy import ForecastPolicy


class MinimumCheckingBalancePolicy(ForecastPolicy):
    """Delay optional spending until a stable checking reserve is established."""

    policy_name = "minimum_checking_balance"

    def __init__(self, target, priority, on_unmet="warn"):
        super().__init__(priority, on_unmet)
        self.validate_amount(target, "target")
        self.target = target

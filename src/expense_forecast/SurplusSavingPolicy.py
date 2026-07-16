"""Policy for directing available checking cash into a savings reserve."""

from expense_forecast.ForecastPolicy import ForecastPolicy


class SurplusSavingPolicy(ForecastPolicy):
    """Transfer checking surplus until a named savings account reaches a target."""

    policy_name = "surplus_saving"

    def __init__(
        self,
        account_name,
        saved_minimum_threshold,
        priority,
        on_unmet="warn",
    ):
        super().__init__(priority, on_unmet)
        if not isinstance(account_name, str) or not account_name.strip():
            raise ValueError("account_name must be a non-empty string")
        self.validate_amount(saved_minimum_threshold, "saved_minimum_threshold")
        self.account_name = account_name.strip()
        self.saved_minimum_threshold = saved_minimum_threshold

    @property
    def policy_key(self):
        return f"{self.policy_name}:{self.account_name}"

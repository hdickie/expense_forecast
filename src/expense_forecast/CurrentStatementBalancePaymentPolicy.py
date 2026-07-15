from expense_forecast.ForecastPolicy import ForecastPolicy


class CurrentStatementBalancePaymentPolicy(ForecastPolicy):
    """Pay a named card's current-cycle charges before billing rollover."""

    policy_name = "current_statement_balance_payment"

    def __init__(self, account_name, priority, on_unmet="warn"):
        super().__init__(priority, on_unmet)
        if not isinstance(account_name, str) or not account_name.strip():
            raise ValueError("account_name must be a non-empty string")
        self.account_name = account_name.strip()

    @property
    def policy_key(self):
        return f"{self.policy_name}:{self.account_name}"


__all__ = ["CurrentStatementBalancePaymentPolicy"]

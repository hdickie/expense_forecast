from expense_forecast.ForecastPolicy import ForecastPolicy


class SurplusDebtPaymentPolicy(ForecastPolicy):
    policy_name = "surplus_debt_payment"

    def __init__(self, debt_type, strategy, priority, on_unmet="warn"):
        super().__init__(priority, on_unmet)
        if debt_type not in {"credit", "loan"}:
            raise ValueError("debt_type must be 'credit' or 'loan'")
        if strategy not in {"avalanche", "snowball"}:
            raise ValueError("strategy must be 'avalanche' or 'snowball'")
        self.debt_type = debt_type
        self.strategy = strategy

    @property
    def policy_key(self):
        return f"{self.policy_name}:{self.debt_type}"


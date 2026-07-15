from expense_forecast.ForecastPolicy import ForecastPolicy


class _InvestmentPolicy(ForecastPolicy):
    def __init__(self, account_name, priority, on_unmet="warn"):
        super().__init__(priority, on_unmet)
        if not isinstance(account_name, str) or not account_name.strip():
            raise ValueError("account_name must be a non-empty string")
        self.account_name = account_name.strip()

    @property
    def policy_key(self):
        return f"{self.policy_name}:{self.account_name}"


class FixedMonthlyInvestmentPolicy(_InvestmentPolicy):
    policy_name = "fixed_monthly_investment"

    def __init__(self, account_name, amount, priority, day=1, on_unmet="warn"):
        super().__init__(account_name, priority, on_unmet)
        self.validate_amount(amount, "amount")
        if isinstance(day, bool) or not isinstance(day, int) or not 1 <= day <= 31:
            raise ValueError("day must be an integer from 1 through 31")
        self.amount = amount
        self.day = day


class IncomePercentageInvestmentPolicy(_InvestmentPolicy):
    policy_name = "income_percentage_investment"

    def __init__(self, account_name, percentage, priority, on_unmet="warn"):
        super().__init__(account_name, priority, on_unmet)
        self.validate_amount(percentage, "percentage")
        if percentage > 1:
            raise ValueError("percentage must be between 0 and 1")
        self.percentage = percentage


class SurplusInvestmentPolicy(_InvestmentPolicy):
    policy_name = "surplus_investment"

    def __init__(self, account_name, checking_threshold, priority, on_unmet="warn"):
        super().__init__(account_name, priority, on_unmet)
        self.validate_amount(checking_threshold, "checking_threshold")
        self.checking_threshold = checking_threshold


class PeriodicInvestmentContributionCapPolicy(_InvestmentPolicy):
    policy_name = "periodic_investment_contribution_cap"

    def __init__(self, account_name, limit, period, priority, on_unmet="warn"):
        super().__init__(account_name, priority, on_unmet)
        self.validate_amount(limit, "limit")
        if period not in {"month", "year"}:
            raise ValueError("period must be 'month' or 'year'")
        self.limit = limit
        self.period = period

    @property
    def policy_key(self):
        return f"{self.policy_name}:{self.account_name}:{self.period}"

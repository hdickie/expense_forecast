from dataclasses import dataclass
from datetime import date


@dataclass
class InvestmentBillingState:

    def __init__(self, 
                balance: float,
                billing_start_date: date, 
                expected_apr: float
                ):
        """
        Represents the billing state for an investment account.

        Stores the current balance and investment parameters required to
        calculate expected growth over a billing cycle. This model uses a
        deterministic expected annual percentage return (APR) rather than
        attempting to simulate market volatility.

        Parameters
        ----------
        balance : float
            Current account balance at the beginning of the billing cycle.

        billing_cycle_start_date : date
            Date on which the current billing or accrual cycle begins.

        expected_apr : float
            Expected annual percentage return expressed as a decimal fraction.
            For example, use ``float("0.07")`` for an expected annual return
            of 7%.


        @interface-report: show
        """
        self.billing_cycle_start_date = billing_start_date
        
        balance = float(str(balance))
        expected_apr = float(str(expected_apr))

        assert balance >= 0
        self.balance = balance

        assert expected_apr >= 0
        self.apr = expected_apr

    def accrue_return(self, days=1) -> float:
        """Compound the balance daily for ``days`` and return the growth."""
        if days < 0:
            raise ValueError("Investment accrual days cannot be negative")
        starting_balance = self.balance
        daily_growth_factor = float("1") + self.apr / float("365.25")
        self.balance *= daily_growth_factor ** days
        return self.balance - starting_balance

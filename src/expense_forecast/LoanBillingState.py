

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class LoanBillingState:
    billing_cycle_start_date: date
    principal_balance: Decimal
    interest_balance: Decimal
    billing_cycle_payment_balance: Decimal
    minimum_payment: Decimal

    def __init__(self, billing_cycle_start_date: date,
                  minimum_payment: Decimal,
                  interest_type: str,
                  interest_cadence: str,
                  apr: Decimal,
                  principal_balance: Decimal = None,
                  interest_balance: Decimal = None,
                  billing_cycle_payment_balance: Decimal = Decimal("0"),
                  previous_statement_balance: Decimal = None,
                  current_statement_balance: Decimal = None,
                  ):
        self.billing_cycle_start_date = billing_cycle_start_date

        if principal_balance is None:
            principal_balance = previous_statement_balance
        if interest_balance is None and current_statement_balance is not None:
            interest_balance = current_statement_balance - principal_balance

        assert principal_balance >= 0
        self.principal_balance = principal_balance
        assert interest_balance >= 0
        self.interest_balance = interest_balance
        assert billing_cycle_payment_balance >= 0
        self.billing_cycle_payment_balance = billing_cycle_payment_balance
        assert minimum_payment >= 0
        self.minimum_payment = minimum_payment

        assert interest_type == "simple"
        assert interest_cadence in ["daily", "monthly", "quarterly", "annually"]
        self.interest_type = interest_type
        self.interest_cadence = interest_cadence

        assert apr >= 0
        self.apr = apr

    @property
    def balance(self) -> Decimal:
        return self.principal_balance + self.interest_balance

    @property
    def previous_statement_balance(self) -> Decimal:
        return self.principal_balance

    @previous_statement_balance.setter
    def previous_statement_balance(self, value: Decimal):
        assert value >= 0
        self.principal_balance = value

    @property
    def current_statement_balance(self) -> Decimal:
        return self.balance

    @current_statement_balance.setter
    def current_statement_balance(self, value: Decimal):
        assert value >= 0
        self.interest_balance = value - self.principal_balance
        assert self.interest_balance >= 0

    def interest_accrued_for_period(self) -> Decimal:
        if self.interest_cadence == "daily":
            return self.principal_balance * self.apr / Decimal("365.25")
        if self.interest_cadence == "monthly":
            return self.principal_balance * self.apr / Decimal("12")
        if self.interest_cadence == "quarterly":
            return self.principal_balance * self.apr / Decimal("4")
        if self.interest_cadence == "annually":
            return self.principal_balance * self.apr
        raise ValueError(f"Unsupported loan interest cadence: {self.interest_cadence}")

    def accrue_interest(self) -> Decimal:
        interest_accrued = self.interest_accrued_for_period()
        self.interest_balance += interest_accrued
        return interest_accrued

    def remaining_minimum_payment_due(self) -> Decimal:
        return max(
            Decimal("0"),
            self.minimum_payment - self.billing_cycle_payment_balance
        )

    def apply_payment(self, amount: Decimal) -> tuple[Decimal, Decimal]:
        payment_remaining = amount

        interest_payment = min(payment_remaining, self.interest_balance)
        self.interest_balance -= interest_payment
        payment_remaining -= interest_payment

        principal_payment = min(payment_remaining, self.principal_balance)
        self.principal_balance -= principal_payment
        payment_remaining -= principal_payment

        return interest_payment, principal_payment

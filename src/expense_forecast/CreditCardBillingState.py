

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class CreditCardBillingState:
    billing_cycle_start_date: date
    previous_statement_balance: Decimal
    current_statement_balance: Decimal
    billing_cycle_payment_balance: Decimal
    minimum_payment: Decimal

    def __init__(self, billing_cycle_start_date: date, previous_statement_balance: Decimal,
                  current_statement_balance: Decimal, billing_cycle_payment_balance: Decimal, 
                  minimum_payment: Decimal,
                  interest_type: str,
                  interest_cadence: str,
                  apr: Decimal
                  ):
        self.billing_cycle_start_date = billing_cycle_start_date
        assert previous_statement_balance >= 0
        self.previous_statement_balance = previous_statement_balance
        assert current_statement_balance >= 0
        self.current_statement_balance = current_statement_balance
        assert billing_cycle_payment_balance >= 0
        self.billing_cycle_payment_balance = billing_cycle_payment_balance
        assert minimum_payment >= 0
        self.minimum_payment = minimum_payment

        assert interest_type in ["simple", "compound"]
        assert interest_cadence in ["daily", "monthly", "quarterly", "annually"]
        self.interest_type = interest_type
        self.interest_cadence = interest_cadence

        assert apr >= 0
        self.apr = apr

    def calculate_next_minimum_payment(self) -> Decimal:
        raise NotImplementedError

    def remaining_minimum_payment_due(self) -> Decimal:
        return max(
            Decimal("0"),
            self.minimum_payment - self.billing_cycle_payment_balance
        )

    def remaining_statement_balance(self) -> Decimal:
        return max(
            Decimal("0"),
            self.previous_statement_balance - self.billing_cycle_payment_balance
        )

    def roll_cycle(self, new_cycle_start_date: date) -> "CreditCardBillingState":
        return CreditCardBillingState(
            billing_cycle_start_date=new_cycle_start_date,
            previous_statement_balance=self.current_statement_balance,
            current_statement_balance=self.current_statement_balance,
            billing_cycle_payment_balance=Decimal("0"),
            minimum_payment=self.calculate_next_minimum_payment(),
            interest_type=self.interest_type,
            interest_cadence=self.interest_cadence,
            apr=self.apr
        )



from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class CreditCardBillingState:
    billing_cycle_start_date: date
    previous_statement_balance: Decimal
    current_statement_balance: Decimal
    billing_cycle_payment_balance: Decimal
    end_of_previous_cycle_balance: Decimal
    minimum_payment: Decimal
    minimum_payment_floor: Decimal
    minimum_payment_credit_balance: Decimal

    def __init__(self, billing_cycle_start_date: date, previous_statement_balance: Decimal,
                  current_statement_balance: Decimal, billing_cycle_payment_balance: Decimal, 
                  minimum_payment: Decimal,
                  interest_type: str,
                  interest_cadence: str,
                  apr: Decimal,
                  end_of_previous_cycle_balance: Decimal = None,
                  minimum_payment_floor: Decimal = None,
                  minimum_payment_credit_balance: Decimal = Decimal("0"),
                  ):
        self.billing_cycle_start_date = billing_cycle_start_date
        previous_statement_balance = Decimal(str(previous_statement_balance))
        current_statement_balance = Decimal(str(current_statement_balance))
        billing_cycle_payment_balance = Decimal(str(billing_cycle_payment_balance))
        minimum_payment = Decimal(str(minimum_payment))
        if minimum_payment_floor is None:
            minimum_payment_floor = minimum_payment
        minimum_payment_floor = Decimal(str(minimum_payment_floor))
        minimum_payment_credit_balance = Decimal(str(minimum_payment_credit_balance))
        apr = Decimal(str(apr))
        if end_of_previous_cycle_balance is None:
            end_of_previous_cycle_balance = (
                previous_statement_balance + billing_cycle_payment_balance
            )
        end_of_previous_cycle_balance = Decimal(str(end_of_previous_cycle_balance))

        assert previous_statement_balance >= 0
        self.previous_statement_balance = previous_statement_balance
        assert current_statement_balance >= 0
        self.current_statement_balance = current_statement_balance
        assert billing_cycle_payment_balance >= 0
        self.billing_cycle_payment_balance = billing_cycle_payment_balance
        assert end_of_previous_cycle_balance >= 0
        self.end_of_previous_cycle_balance = end_of_previous_cycle_balance
        assert minimum_payment >= 0
        self.minimum_payment = minimum_payment
        assert minimum_payment_floor >= 0
        self.minimum_payment_floor = minimum_payment_floor
        assert minimum_payment_credit_balance >= 0
        self.minimum_payment_credit_balance = minimum_payment_credit_balance

        assert interest_type in ["simple", "compound"]
        assert interest_cadence in ["daily", "monthly", "quarterly", "annually"]
        self.interest_type = interest_type
        self.interest_cadence = interest_cadence

        assert apr >= 0
        self.apr = apr

    def calculate_next_minimum_payment(self) -> Decimal:
        interest_accrued_this_cycle = self.interest_accrued_this_cycle()
        principal_due_this_cycle = self.previous_statement_balance * Decimal("0.01")
        total_balance = (
            self.previous_statement_balance
            + self.current_statement_balance
            + interest_accrued_this_cycle
        )

        if interest_accrued_this_cycle + principal_due_this_cycle == 0:
            return Decimal("0")

        return min(
            total_balance,
            max(
                self.minimum_payment_floor,
                interest_accrued_this_cycle + principal_due_this_cycle,
            ),
        )

    def interest_accrued_this_cycle(self) -> Decimal:
        if self.interest_cadence != "monthly":
            raise NotImplementedError(
                f"Credit card interest cadence '{self.interest_cadence}' is not implemented."
            )
        if self.interest_type != "compound":
            raise NotImplementedError(
                f"Credit card interest type '{self.interest_type}' is not implemented."
            )
        return self.previous_statement_balance * (self.apr / Decimal("12"))

    def remaining_minimum_payment_due(self) -> Decimal:
        return max(
            Decimal("0"),
            self.minimum_payment - self.minimum_payment_credit_balance
        )

    def remaining_statement_balance(self) -> Decimal:
        return max(
            Decimal("0"),
            self.previous_statement_balance - self.billing_cycle_payment_balance
        )

    def roll_cycle(self, new_cycle_start_date: date) -> "CreditCardBillingState":
        interest_accrued_this_cycle = self.interest_accrued_this_cycle()
        end_of_previous_cycle_balance = (
            self.previous_statement_balance
            + self.billing_cycle_payment_balance
        )
        next_statement_balance = (
            self.previous_statement_balance
            + self.current_statement_balance
            + interest_accrued_this_cycle
        )
        next_minimum_payment = self.calculate_next_minimum_payment()
        advance_payment_credit = min(
            self.billing_cycle_payment_balance,
            next_minimum_payment,
        )

        return CreditCardBillingState(
            billing_cycle_start_date=new_cycle_start_date,
            previous_statement_balance=next_statement_balance,
            current_statement_balance=Decimal("0"),
            billing_cycle_payment_balance=Decimal("0"),
            end_of_previous_cycle_balance=end_of_previous_cycle_balance,
            minimum_payment=next_minimum_payment,
            interest_type=self.interest_type,
            interest_cadence=self.interest_cadence,
            apr=self.apr,
            minimum_payment_floor=self.minimum_payment_floor,
            minimum_payment_credit_balance=advance_payment_credit,
        )
